"""
Python Wrapper Utilities for bash script integration.

This module provides utilities for bash scripts that delegate to Python implementations,
including environment setup, argument handling, and process management.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple


class WrapperError(Exception):
    """Custom exception for wrapper operations."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


class PythonWrapperManager:
    """
    Manager for bash-to-Python wrapper scripts.

    Handles Python environment setup, validation, and delegation patterns
    common in LinkedIn's bash-wrapper + Python-core architecture.
    """

    def __init__(
        self,
        script_dir: str,
        project_name: str,
        repo_root: Optional[str] = None,
        verbose: bool = False,
    ):
        """
        Initialize wrapper manager.

        Args:
            script_dir: Directory containing the wrapper script
            project_name: Name of the project (for Python script naming)
            repo_root: Repository root (auto-detected if None)
            verbose: Enable verbose logging
        """
        self.script_dir = Path(script_dir)
        self.project_name = project_name
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

        # Auto-detect repo root if not provided
        if repo_root:
            self.repo_root = Path(repo_root)
        else:
            self.repo_root = self._find_repo_root()

        # Derived paths
        self.python_script = self.script_dir / f"{project_name}.py"
        self.venv_dir = self.script_dir / ".venv"
        self.shared_libs_path = self.repo_root / "src" / "shared_libs"

    def validate_python_script(self) -> None:
        """
        Validate that the Python script exists.

        Raises:
            WrapperError: If Python script is not found
        """
        if not self.python_script.is_file():
            raise WrapperError(
                f"Python script not found at {
                    self.python_script}. " f"Please ensure {
                    self.project_name}.py exists in the same directory as the wrapper script.",
                exit_code=1,
            )

    def setup_python_environment(self) -> None:
        """
        Set up Python virtual environment with shared_libs access.

        Creates venv if needed, activates it, and ensures shared_libs is in PYTHONPATH.

        Raises:
            WrapperError: If environment setup fails
        """
        try:
            # Create virtual environment if it doesn't exist
            if not self.venv_dir.is_dir():
                if self.verbose:
                    print(f"Creating Python virtual environment at {self.venv_dir}")

                subprocess.run(
                    [sys.executable, "-m", "venv", str(self.venv_dir)],
                    check=True,
                    capture_output=not self.verbose,
                )

            # Add shared_libs to Python path
            current_pythonpath = os.environ.get("PYTHONPATH", "")
            if current_pythonpath:
                pythonpath = f"{self.shared_libs_path}:{current_pythonpath}"
            else:
                pythonpath = str(self.shared_libs_path)
            os.environ["PYTHONPATH"] = pythonpath

            # Install/upgrade required packages if needed
            packages_marker = self.venv_dir / ".packages_installed"
            if not packages_marker.exists():
                if self.verbose:
                    print("Setting up Python environment...")

                # Get pip path in venv
                pip_path = self.venv_dir / "bin" / "pip"
                if not pip_path.exists():
                    pip_path = self.venv_dir / "Scripts" / "pip.exe"  # Windows

                if pip_path.exists():
                    # Upgrade pip (suppress output unless verbose)
                    subprocess.run(
                        [str(pip_path), "install", "--upgrade", "pip"],
                        capture_output=not self.verbose,
                        check=True,
                    )

                # Create marker file
                packages_marker.touch()

        except subprocess.CalledProcessError as e:
            raise WrapperError(f"Failed to set up Python environment: {e}", exit_code=1)
        except Exception as e:
            raise WrapperError(f"Environment setup error: {e}", exit_code=1)

    def get_python_executable(self) -> str:
        """
        Get the Python executable path for the virtual environment.

        Returns:
            Path to Python executable in the venv
        """
        python_path = self.venv_dir / "bin" / "python3"
        if not python_path.exists():
            python_path = self.venv_dir / "Scripts" / "python.exe"  # Windows

        if python_path.exists():
            return str(python_path)
        else:
            # Fallback to system Python if venv not found
            return sys.executable

    def execute_python_script(self, args: List[str]) -> None:
        """
        Execute the Python script with given arguments.

        Args:
            args: Command line arguments to pass to Python script

        Raises:
            WrapperError: If execution fails
        """
        try:
            python_exe = self.get_python_executable()
            cmd = [python_exe, str(self.python_script)] + args

            if self.verbose:
                self.logger.debug(f"Executing: {' '.join(cmd)}")

            # Use exec-like behavior - replace current process
            os.execv(python_exe, [python_exe, str(self.python_script)] + args)

        except OSError as e:
            raise WrapperError(f"Failed to execute Python script: {e}", exit_code=1)
        except Exception as e:
            raise WrapperError(f"Execution error: {e}", exit_code=1)

    def _find_repo_root(self) -> Path:
        """
        Find repository root by looking for common indicators.

        Returns:
            Path to repository root

        Raises:
            WrapperError: If repo root cannot be determined
        """
        current = self.script_dir

        # Look for common repo root indicators
        indicators = [".git", "Cargo.toml", "pyproject.toml", "README.md"]

        for _ in range(10):  # Limit search depth
            for indicator in indicators:
                if (current / indicator).exists():
                    return current

            parent = current.parent
            if parent == current:  # Reached filesystem root
                break
            current = parent

        # Fallback: assume script_dir/../.. is repo root (common pattern)
        fallback = self.script_dir.parent.parent
        if fallback.is_dir():
            return fallback

        raise WrapperError(f"Could not determine repository root from {self.script_dir}", exit_code=1)


def create_thin_wrapper(
    script_dir: str,
    project_name: str,
    args: List[str],
    repo_root: Optional[str] = None,
    verbose: bool = False,
) -> None:
    """
    Main function for thin wrapper scripts.

    Handles the complete wrapper workflow: validation, environment setup,
    and delegation to Python implementation.

    Args:
        script_dir: Directory containing the wrapper script
        project_name: Name of the project
        args: Command line arguments to forward
        repo_root: Repository root (auto-detected if None)
        verbose: Enable verbose logging

    Raises:
        WrapperError: If any step fails
    """
    try:
        # Create wrapper manager
        wrapper = PythonWrapperManager(
            script_dir=script_dir,
            project_name=project_name,
            repo_root=repo_root,
            verbose=verbose,
        )

        # Validate Python script exists
        wrapper.validate_python_script()

        # Set up Python environment
        wrapper.setup_python_environment()

        # Execute Python implementation (this replaces current process)
        wrapper.execute_python_script(args)

    except WrapperError:
        # Re-raise wrapper errors as-is
        raise
    except Exception as e:
        raise WrapperError(f"Wrapper execution failed: {e}", exit_code=1)


def setup_bash_environment_integration() -> Tuple[str, Optional[str], str]:
    """
    Set up environment variables for bash script integration.

    Returns:
        Tuple of (script_dir, repo_root, project_name) derived from environment
    """
    # These would typically be set by the bash script
    script_dir = os.environ.get("SCRIPT_DIR", os.path.dirname(os.path.abspath(__file__)))
    repo_root = os.environ.get("REPO_ROOT")

    # Project name typically derived from script name
    script_name = os.path.basename(sys.argv[0]) if sys.argv else "unknown"
    if script_name.endswith(".py"):
        project_name = script_name[:-3]  # Remove .py extension
    else:
        project_name = script_name

    return script_dir, repo_root, project_name
