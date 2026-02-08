"""
Common command execution patterns and wrappers.

This module provides convenient wrappers for common types of commands
that are used across multiple projects in the workspace.
"""

from typing import Any, Dict, List, Optional

from .subprocess_client import CommandConfig, CommandResult, SubprocessClient


class GitCommandWrapper:
    """Wrapper for common git operations."""

    def __init__(self, client: Optional[SubprocessClient] = None):
        self.client = client or SubprocessClient()

    def get_current_branch(self) -> Optional[str]:
        """Get the current git branch name."""
        result = self.client.execute_simple(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        return result.output.strip() if result.success else None

    def get_commit_hash(self, short: bool = True) -> Optional[str]:
        """Get the current commit hash."""
        cmd = ["git", "rev-parse"]
        if short:
            cmd.append("--short")
        cmd.append("HEAD")

        result = self.client.execute_simple(cmd)
        return result.output.strip() if result.success else None

    def is_clean_working_tree(self) -> bool:
        """Check if the working tree is clean (no uncommitted changes)."""
        result = self.client.execute_simple(["git", "status", "--porcelain"])
        return result.success and len(result.output.strip()) == 0


class DockerCommandWrapper:
    """Wrapper for common docker operations."""

    def __init__(self, client: Optional[SubprocessClient] = None):
        self.client = client or SubprocessClient()

    def is_running(self) -> bool:
        """Check if Docker daemon is running."""
        result = self.client.execute_simple(["docker", "version"], timeout=10)
        return result.success

    def list_containers(self, all_containers: bool = False) -> List[str]:
        """List container IDs."""
        cmd = ["docker", "ps", "-q"]
        if all_containers:
            cmd.append("-a")

        result = self.client.execute_simple(cmd)
        if result.success:
            return [line.strip() for line in result.output.split("\n") if line.strip()]
        return []

    def get_image_tags(self, image_name: str) -> List[str]:
        """Get available tags for an image."""
        # This is a simplified version - real implementation would query registry
        result = self.client.execute_simple(["docker", "images", image_name, "--format", "{{.Tag}}"])
        if result.success:
            return [line.strip() for line in result.output.split("\n") if line.strip()]
        return []


class KubernetesCommandWrapper:
    """Wrapper for kubectl operations with context management."""

    def __init__(self, client: Optional[SubprocessClient] = None, skip_tls_verify: bool = False):
        self.client = client or SubprocessClient()
        self.skip_tls_verify = skip_tls_verify
        self._setup_done = False

    def _get_base_cmd(self) -> List[str]:
        """Get base kubectl command with common flags."""
        cmd = ["kubectl"]
        if self.skip_tls_verify:
            cmd.extend(["--insecure-skip-tls-verify"])
        return cmd

    def setup_kubectl(self) -> CommandResult:
        """Run kubectl setup command if needed."""
        if self._setup_done:
            return CommandResult(
                success=True,
                output="Setup already completed",
                error_output="",
                return_code=0,
                command="kubectl setup (cached)",
                execution_time=0.0,
            )

        cmd = self._get_base_cmd() + ["in", "setup"]
        result = self.client.execute_simple(cmd, timeout=30)
        self._setup_done = True  # Mark as done regardless of success
        return result

    def get_contexts(self) -> List[str]:
        """Get available kubectl contexts."""
        cmd = self._get_base_cmd() + ["config", "get-contexts", "-o", "name"]
        result = self.client.execute_simple(cmd)
        if result.success:
            return [line.strip() for line in result.output.split("\n") if line.strip()]
        return []

    def get_current_context(self) -> Optional[str]:
        """Get current kubectl context."""
        cmd = self._get_base_cmd() + ["config", "current-context"]
        result = self.client.execute_simple(cmd)
        return result.output.strip() if result.success else None

    def set_context(self, context: str) -> CommandResult:
        """Set kubectl context."""
        cmd = self._get_base_cmd() + ["config", "use-context", context]
        return self.client.execute_simple(cmd)

    def get_pods(self, context: Optional[str] = None, namespace: str = "default") -> CommandResult:
        """Get pods in specified context and namespace."""
        # Setup kubectl if needed
        self.setup_kubectl()

        cmd = self._get_base_cmd()
        if context:
            cmd.extend(["--context", context])
        cmd.extend(["get", "pods", "-n", namespace, "-o", "wide"])

        return self.client.execute_command(cmd)


class SystemCommandWrapper:
    """Wrapper for common system operations."""

    def __init__(self, client: Optional[SubprocessClient] = None):
        self.client = client or SubprocessClient()

    def get_disk_usage(self, path: str = ".") -> Dict[str, str]:
        """Get disk usage information for a path."""
        result = self.client.execute_simple(["df", "-h", path])
        if result.success:
            lines = result.output.strip().split("\n")
            if len(lines) >= 2:
                # Parse df output
                header = lines[0].split()
                data = lines[1].split()
                return dict(zip(header, data))
        return {}

    def get_memory_info(self) -> Dict[str, str]:
        """Get system memory information."""
        result = self.client.execute_simple(["free", "-h"])
        if result.success:
            lines = result.output.strip().split("\n")
            if len(lines) >= 2:
                # Parse free output
                mem_line = lines[1].split()
                return {
                    "total": mem_line[1] if len(mem_line) > 1 else "unknown",
                    "used": mem_line[2] if len(mem_line) > 2 else "unknown",
                    "available": mem_line[6] if len(mem_line) > 6 else "unknown",
                }
        return {}

    def check_port_open(self, host: str, port: int, timeout: int = 5) -> bool:
        """Check if a network port is open."""
        import socket

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                result = sock.connect_ex((host, port))
                return result == 0
        except BaseException:
            return False

    def get_process_info(self, process_name: str) -> List[Dict[str, str]]:
        """Get information about running processes matching name."""
        result = self.client.execute_simple(["pgrep", "-l", process_name])
        processes = []
        if result.success:
            for line in result.output.strip().split("\n"):
                if line.strip():
                    parts = line.strip().split(" ", 1)
                    if len(parts) >= 2:
                        processes.append({"pid": parts[0], "name": parts[1]})
        return processes


class CustomCommandWrapper:
    """
    Base class for creating custom command wrappers for specific tools.

    This provides a pattern for wrapping domain-specific command line tools
    with consistent error handling and configuration.
    """

    def __init__(
        self,
        command_name: str,
        client: Optional[SubprocessClient] = None,
        default_args: Optional[List[str]] = None,
        custom_patterns: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        """
        Initialize custom command wrapper.

        Args:
            command_name: Base command name (e.g., 'go-status', 'myapp')
            client: SubprocessClient instance
            default_args: Default arguments to always include
            custom_patterns: Custom error patterns for this tool
        """
        self.command_name = command_name
        self.default_args = default_args or []

        # Create client with custom patterns if provided
        if custom_patterns and client is None:
            config = CommandConfig(custom_error_patterns=custom_patterns)
            self.client = SubprocessClient(config)
        else:
            self.client = client or SubprocessClient()

    def execute(self, args: List[str], timeout: Optional[int] = None, retries: int = 0) -> CommandResult:
        """
        Execute the command with specified arguments.

        Args:
            args: Command arguments
            timeout: Override default timeout
            retries: Number of retry attempts

        Returns:
            CommandResult
        """
        full_command = [self.command_name] + self.default_args + args

        if timeout is not None or retries > 0:
            config = CommandConfig(
                timeout=timeout or 30,
                retries=retries,
                verbose=self.client.config.verbose,
            )
            return self.client.execute_command(full_command, override_config=config)
        else:
            return self.client.execute_command(full_command)

    def is_available(self) -> bool:
        """Check if the command is available."""
        return self.client.test_command_available(self.command_name)

    def get_version(self) -> Optional[str]:
        """Get command version."""
        return self.client.get_command_version(self.command_name)


def create_command_wrapper(
    command_name: str,
    default_args: Optional[List[str]] = None,
    custom_patterns: Optional[Dict[str, Dict[str, Any]]] = None,
    timeout: int = 30,
    verbose: bool = False,
) -> CustomCommandWrapper:
    """
    Create a custom command wrapper with specified configuration.

    Args:
        command_name: Base command name
        default_args: Default arguments
        custom_patterns: Custom error patterns
        timeout: Default timeout
        verbose: Enable verbose output

    Returns:
        Configured CustomCommandWrapper
    """
    config = CommandConfig(timeout=timeout, verbose=verbose, custom_error_patterns=custom_patterns)
    client = SubprocessClient(config)

    return CustomCommandWrapper(
        command_name=command_name,
        client=client,
        default_args=default_args,
        custom_patterns=custom_patterns,
    )
