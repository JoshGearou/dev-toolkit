#!/usr/bin/env python3
"""
Simplified Flake8 Auto-fixer

A streamlined tool to automatically fix flake8 issues using black, isort, and autopep8.
Provides safe and aggressive modes with dry-run capabilities.

Follows project's Domain Driven Design principles with simple, focused design.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List


def check_tool_available(tool_name: str) -> bool:
    """Check if a formatting tool is available."""
    return shutil.which(tool_name) is not None or tool_importable(tool_name)


def tool_importable(tool_name: str) -> bool:
    """Check if a tool can be imported as a Python module."""
    try:
        subprocess.run(
            [sys.executable, "-c", f"import {tool_name}"],
            capture_output=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def run_formatter(
    tool: str,
    args: List[str],
    files: List[str],
    dry_run: bool = False,
    verbose: bool = False,
) -> bool:
    """Run a formatting tool on files."""
    cmd = [sys.executable, "-m", tool] + args + files

    if verbose:
        print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if dry_run and result.stdout:
            print(f"\n{tool.upper()} changes:")
            print(result.stdout)

        if verbose and result.stderr:
            print(f"{tool} stderr:", result.stderr)

        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        if verbose:
            print(f"Error running {tool}: {e}")
        return False


def apply_black(
    files: List[str],
    aggressive: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> bool:
    """Apply black formatting."""
    args = ["--target-version=py38"]

    # Configure line length based on mode
    if aggressive:
        args.append("--line-length=88")  # Black's default
    else:
        args.append("--line-length=120")  # More conservative

    if dry_run:
        args.append("--diff")

    return run_formatter("black", args, files, dry_run, verbose)


def apply_isort(
    files: List[str],
    aggressive: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> bool:
    """Apply isort import organization."""
    args = [
        "--profile=black",  # Compatible with black
        "--multi-line=3",
        "--trailing-comma",
        "--force-grid-wrap=0",
        "--combine-as",
    ]

    # Configure line width based on mode
    if aggressive:
        args.append("--line-width=88")
    else:
        args.append("--line-width=120")

    if dry_run:
        args.append("--diff")

    return run_formatter("isort", args, files, dry_run, verbose)


def apply_autoflake(files: List[str], dry_run: bool = False, verbose: bool = False) -> bool:
    """Apply autoflake to remove unused imports and variables."""
    args = [
        "--remove-all-unused-imports",
        "--remove-unused-variables",
        "--remove-duplicate-keys",
        "--expand-star-imports",
    ]

    if dry_run:
        args.append("--stdout")
        # For dry run, process files one by one to show changes
        success = True
        for file_path in files:
            if verbose:
                print(f"\nChecking {file_path} with autoflake...")
            single_success = run_formatter("autoflake", args + [file_path], [], dry_run, verbose)
            success = success and single_success
        return success
    else:
        args.append("--in-place")
        return run_formatter("autoflake", args, files, dry_run, verbose)


def apply_autopep8(files: List[str], dry_run: bool = False, verbose: bool = False) -> bool:
    """Apply autopep8 for more aggressive fixes."""
    args = [
        "--aggressive",
        "--aggressive",
        "--max-line-length=88",
    ]  # Double aggressive for more fixes

    if dry_run:
        args.append("--diff")
    else:
        args.append("--in-place")

    return run_formatter("autopep8", args, files, dry_run, verbose)


def create_backups(files: List[str], verbose: bool = False) -> None:
    """Create backup files."""
    for file_path in files:
        backup_path = f"{file_path}.bak"
        shutil.copy2(file_path, backup_path)
        if verbose:
            print(f"Created backup: {backup_path}")


def verify_syntax(files: List[str], verbose: bool = False) -> bool:
    """Verify Python syntax of files."""
    errors: List[str] = []

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                compile(f.read(), file_path, "exec")
            if verbose:
                print(f"✅ Syntax OK: {file_path}")
        except SyntaxError as e:
            error_msg = f"{file_path}:{e.lineno}: {e.msg}"
            errors.append(error_msg)
            print(f"❌ Syntax error: {error_msg}")
        except Exception as e:
            error_msg = f"{file_path}: {e}"
            errors.append(error_msg)
            print(f"❌ Error checking: {error_msg}")

    if errors:
        print(f"\n💥 SYNTAX VERIFICATION FAILED - {len(errors)} files with errors")
        return False
    else:
        print(f"✅ SYNTAX VERIFICATION PASSED - All {len(files)} files are valid")
        return True


def find_python_files(paths: List[str]) -> List[str]:
    """Find Python files in given paths."""
    python_files: List[str] = []
    exclude_patterns = {
        ".venv",
        "venv",
        "__pycache__",
        ".git",
        "target",
        "build",
        "dist",
    }

    for path_str in paths:
        path = Path(path_str)
        if path.is_file() and path.suffix == ".py":
            python_files.append(str(path))
        elif path.is_dir():
            for py_file in path.rglob("*.py"):
                # Skip excluded directories
                if any(pattern in py_file.parts for pattern in exclude_patterns):
                    continue
                python_files.append(str(py_file))

    return sorted(python_files)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Auto-fix flake8 issues using autoflake, black, isort, and autopep8",  # noqa: E501
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Safe fixes on current directory
  %(prog)s --aggressive                 # Aggressive fixes with shorter lines
  %(prog)s --dry-run                    # Preview changes without applying
  %(prog)s --backup src/                # Fix src/ with backups
  %(prog)s --safe --no-syntax-check     # Skip syntax verification (not recommended)
        """,
    )

    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Paths to fix (default: current directory)",
    )
    parser.add_argument(
        "--safe",
        action="store_true",
        default=True,
        help="Apply safe fixes only (default)",
    )
    parser.add_argument(
        "--aggressive",
        action="store_true",
        help="Apply aggressive fixes (shorter lines, more changes)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without applying them",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create .bak files before making changes",
    )
    parser.add_argument(
        "--no-syntax-check",
        action="store_true",
        help="Skip syntax verification (not recommended)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Determine mode
    aggressive_mode = args.aggressive
    if aggressive_mode:
        args.safe = False

    if args.verbose:
        mode = "AGGRESSIVE" if aggressive_mode else "SAFE"
        print(f"Mode: {mode}")
        print(f"Paths: {args.paths}")
        print(f"Dry run: {args.dry_run}")
        print(f"Backup: {args.backup}")
        print(f"Syntax check: {not args.no_syntax_check}")

    # Find Python files
    python_files = find_python_files(args.paths)
    if not python_files:
        print("No Python files found to process")
        return 0

    print(f"Processing {len(python_files)} Python files...")

    # Check tool availability
    tools_available = {
        "autoflake": check_tool_available("autoflake"),
        "black": check_tool_available("black"),
        "isort": check_tool_available("isort"),
        "autopep8": (check_tool_available("autopep8") if aggressive_mode else True),
    }

    missing_tools = [tool for tool, available in tools_available.items() if not available]
    if missing_tools:
        print(f"Missing tools: {', '.join(missing_tools)}")
        print("Install with: pip install " + " ".join(missing_tools))
        return 1

    # Create backups if requested
    if args.backup and not args.dry_run:
        create_backups(python_files, args.verbose)

    # Apply formatting (order matters: autoflake first, then formatting)
    success = True

    # Apply autoflake first to remove unused imports/variables
    if tools_available["autoflake"]:
        if args.verbose:
            print("\n🧹 Removing unused imports and variables...")
        if not apply_autoflake(python_files, args.dry_run, args.verbose):
            print("Autoflake cleanup failed")
            success = False

    # Apply black
    if success:
        if args.verbose:
            print("\n🖤 Applying black formatting...")
        if not apply_black(python_files, aggressive_mode, args.dry_run, args.verbose):
            print("Black formatting failed")
            success = False

    # Apply isort
    if success and tools_available["isort"]:
        if args.verbose:
            print("\n📦 Organizing imports...")
        if not apply_isort(python_files, aggressive_mode, args.dry_run, args.verbose):
            print("Import organization failed")
            success = False

    # Apply autopep8 in aggressive mode for additional PEP8 fixes
    if success and aggressive_mode and tools_available["autopep8"]:
        if args.verbose:
            print("\n🔧 Applying autopep8 aggressive fixes...")
        if not apply_autopep8(python_files, args.dry_run, args.verbose):
            print("Autopep8 failed")
            success = False

    # Verify syntax after changes
    if success and not args.dry_run and not args.no_syntax_check:
        print("\n🔍 Verifying syntax...")
        if not verify_syntax(python_files, args.verbose):
            success = False

    # Summary
    if args.dry_run:
        print(f"\nDRY RUN complete - No changes made to {len(python_files)} files")
    elif success:
        print(f"✅ Auto-fix complete - {len(python_files)} files processed successfully")
        mode_desc = "aggressive" if aggressive_mode else "safe"
        print(f"Applied {mode_desc} fixes using:", end="")
        if tools_available["autoflake"]:
            print(" autoflake", end="")
        if tools_available["black"]:
            print(" black", end="")
        if tools_available["isort"]:
            print(" isort", end="")
        if aggressive_mode and tools_available["autopep8"]:
            print(" autopep8", end="")
        print()
    else:
        print("⚠️ Auto-fix completed with issues - Check output above")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
