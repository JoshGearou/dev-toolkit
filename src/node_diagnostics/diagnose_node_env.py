#!/usr/bin/env python3
"""
Node.js Environment Diagnostic Tool

Comprehensive diagnostics for Node.js, npm, and Volta installations.
Identifies issues, conflicts, and provides actionable recommendations.

Usage:
    python3 diagnose_node_env.py [--verbose]
    ./diagnose_node_env.sh [--verbose]  # With bash wrapper

Exit codes:
    0 - Environment healthy
    1 - Critical issues found
    2 - Warnings but functional
"""

import argparse
import json
import os
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# Import shared libraries
from shared_libs.cmd_utils.subprocess_client import CommandConfig, SubprocessClient
from shared_libs.common.logging_utils import setup_logging


@dataclass
class Command:
    """Represents a command to check."""

    name: str
    cmd: list[str]
    required: bool = True
    version_key: str = "version"


@dataclass
class DiagnosticResult:
    """Results from diagnostic checks."""

    command: str
    found: bool
    version: Optional[str] = None
    path: Optional[str] = None
    error: Optional[str] = None
    all_paths: list[str] = field(default_factory=list)


@dataclass
class Issue:
    """Represents an identified issue."""

    severity: str  # "critical", "warning", "info"
    message: str
    recommendation: str
    commands: list[str] = field(default_factory=list)


class NodeDiagnostics:
    """Diagnose Node.js environment."""

    def __init__(self, verbose: bool = False, logger: Optional[Any] = None) -> None:
        """Initialize diagnostics."""
        self.verbose = verbose
        self.logger = logger
        self.results: dict[str, DiagnosticResult] = {}
        self.issues: list[Issue] = []
        self.system_info = self._get_system_info()

        # Setup subprocess client
        config = CommandConfig(
            timeout=10,
            retries=0,
            verbose=verbose,
            check_return_code=False,  # We handle errors manually
        )
        self.subprocess_client = SubprocessClient(config)

    def _get_system_info(self) -> dict[str, str]:
        """Get system information."""
        return {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
        }

    def _find_all_instances(self, command: str) -> list[str]:
        """Find all instances of a command in PATH."""
        if platform.system() == "Windows":
            # Windows uses 'where' command
            result = self.subprocess_client.execute_command(["where", command])
        else:
            # Unix-like systems use 'which -a'
            result = self.subprocess_client.execute_command(["which", "-a", command])

        if result.success:
            paths = [p.strip() for p in result.output.strip().split("\n") if p.strip()]
            return paths
        return []

    def check_command(self, cmd: Command) -> DiagnosticResult:
        """Check if command exists and get version."""
        # Check if command exists
        result = self.subprocess_client.execute_command(["which", cmd.name])

        if not result.success:
            return DiagnosticResult(
                command=cmd.name,
                found=False,
                error=f"{cmd.name} not found in PATH",
            )

        which_path = result.output.strip()

        # Get all instances
        all_paths = self._find_all_instances(cmd.name)

        # Get version
        version_result = self.subprocess_client.execute_command(cmd.cmd)
        version = None
        if version_result.success:
            version = version_result.output.strip()

        return DiagnosticResult(
            command=cmd.name,
            found=True,
            version=version,
            path=which_path,
            all_paths=all_paths,
        )

    def check_path_config(self) -> dict[str, Any]:
        """Check PATH configuration."""
        path_env = os.environ.get("PATH", "")
        path_entries = path_env.split(os.pathsep)

        volta_in_path = any("volta" in entry.lower() for entry in path_entries)
        npm_global_in_path = any(".npm-global" in entry or "npm/bin" in entry for entry in path_entries)

        return {
            "volta_in_path": volta_in_path,
            "npm_global_in_path": npm_global_in_path,
            "path_entries": path_entries if self.verbose else len(path_entries),
        }

    def check_volta_home(self) -> Optional[Path]:
        """Check VOLTA_HOME environment variable."""
        volta_home = os.environ.get("VOLTA_HOME")
        if volta_home:
            path = Path(volta_home)
            return path if path.exists() else None
        return None

    def check_node_version_requirement(self, version_str: Optional[str]) -> tuple[bool, int]:
        """Check if Node.js meets minimum version requirement (18+)."""
        if not version_str:
            return False, 0

        # Extract version number (handle "v22.11.0" or "22.11.0")
        version_str = version_str.strip().lstrip("v")
        try:
            major = int(version_str.split(".")[0])
            return major >= 18, major
        except (ValueError, IndexError):
            return False, 0

    def check_npm_global_packages(self) -> dict[str, Any]:
        """Check installed npm global packages."""
        result = self.subprocess_client.execute_command(["npm", "list", "-g", "--depth=0", "--json"])
        if not result.success:
            return {"error": "Failed to list npm packages"}

        try:
            data = json.loads(result.output)
            dependencies = data.get("dependencies", {})
            return {
                "count": len(dependencies),
                "packages": list(dependencies.keys()) if self.verbose else None,
                "location": data.get("path"),
            }
        except json.JSONDecodeError:
            return {"error": "Failed to parse npm list output"}

    def analyze_issues(self) -> None:
        """Analyze results and identify issues."""
        # Check Node.js installation
        node_result = self.results.get("node")
        if not node_result or not node_result.found:
            self.issues.append(
                Issue(
                    severity="critical",
                    message="Node.js is not installed",
                    recommendation="Install Node.js 22 LTS (recommended)",
                    commands=[
                        "# With Volta (recommended):",
                        "curl https://get.volta.sh | bash",
                        "source ~/.zshrc  # or ~/.bashrc",
                        "volta install node@22",
                        "",
                        "# Or download directly:",
                        "# Visit: https://nodejs.org/",
                    ],
                )
            )
        else:
            # Check version
            meets_req, major_version = self.check_node_version_requirement(node_result.version)
            if not meets_req:
                self.issues.append(
                    Issue(
                        severity="critical",
                        message=f"Node.js version too old: {node_result.version}",
                        recommendation="Upgrade to Node.js 18+ (22 LTS recommended)",
                        commands=[
                            "volta install node@22  # Recommended",
                            "# Or: volta install node@18  # Minimum",
                        ],
                    )
                )
            elif major_version < 22:
                self.issues.append(
                    Issue(
                        severity="info",
                        message=f"Node.js {node_result.version} meets minimum requirements",
                        recommendation="Consider upgrading to Node.js 22 LTS for improved performance",
                        commands=["volta install node@22"],
                    )
                )

            # Check for multiple Node.js installations
            if len(node_result.all_paths) > 1:
                self.issues.append(
                    Issue(
                        severity="warning",
                        message=f"Multiple Node.js installations detected: {len(node_result.all_paths)}",
                        recommendation="Consider using Volta exclusively to avoid version conflicts",
                        commands=[
                            "# Remove Homebrew Node.js:",
                            "brew uninstall node",
                            "brew uninstall node@18",
                            "brew uninstall node@20",
                            "",
                            "# Verify Volta-managed Node.js:",
                            "which node",
                            "volta list",
                        ],
                    )
                )

        # Check npm
        npm_result = self.results.get("npm")
        if not npm_result or not npm_result.found:
            self.issues.append(
                Issue(
                    severity="critical",
                    message="npm is not installed",
                    recommendation="Reinstall Node.js (npm is bundled with Node.js)",
                    commands=["volta install node@22"],
                )
            )

        # Check Volta
        volta_result = self.results.get("volta")
        if not volta_result or not volta_result.found:
            self.issues.append(
                Issue(
                    severity="info",
                    message="Volta is not installed (optional but recommended)",
                    recommendation="Install Volta for better Node.js version management",
                    commands=[
                        "curl https://get.volta.sh | bash",
                        "source ~/.zshrc  # or ~/.bashrc",
                        "volta install node@22",
                    ],
                )
            )
        else:
            # Check if Node.js is managed by Volta
            if node_result and node_result.path:
                if "volta" not in node_result.path.lower():
                    self.issues.append(
                        Issue(
                            severity="warning",
                            message="Volta installed but Node.js not managed by Volta",
                            recommendation="Use Volta to install Node.js",
                            commands=[
                                "volta install node@22",
                                "which node  # Should show .volta/bin/node",
                            ],
                        )
                    )

    def print_header(self, text: str) -> None:
        """Print section header."""
        print(f"\n{'=' * 60}")
        print(f"  {text}")
        print(f"{'=' * 60}")

    def print_result(self, result: DiagnosticResult) -> None:
        """Print diagnostic result."""
        status = "✓" if result.found else "✗"
        print(f"{status} {result.command:10}", end="")

        if result.found:
            print(f" {result.version or 'installed'}")
            if self.verbose and result.path:
                print(f"   Path: {result.path}")
            if self.verbose and len(result.all_paths) > 1:
                print(f"   Warning: {len(result.all_paths)} installations found:")
                for path in result.all_paths:
                    print(f"     - {path}")
        else:
            print(" NOT FOUND")
            if result.error:
                print(f"   Error: {result.error}")

    def print_issues(self) -> None:
        """Print identified issues."""
        if not self.issues:
            self.print_header("DIAGNOSIS: HEALTHY ✓")
            print("\nNo issues detected. Your Node.js environment is properly configured.")
            return

        # Group by severity
        critical = [i for i in self.issues if i.severity == "critical"]
        warnings = [i for i in self.issues if i.severity == "warning"]
        info = [i for i in self.issues if i.severity == "info"]

        if critical:
            self.print_header("CRITICAL ISSUES")
            for idx, issue in enumerate(critical, 1):
                print(f"\n{idx}. {issue.message}")
                print(f"   → {issue.recommendation}")
                if issue.commands:
                    print("   Commands:")
                    for cmd in issue.commands:
                        print(f"     {cmd}")

        if warnings:
            self.print_header("WARNINGS")
            for idx, issue in enumerate(warnings, 1):
                print(f"\n{idx}. {issue.message}")
                print(f"   → {issue.recommendation}")
                if issue.commands:
                    print("   Commands:")
                    for cmd in issue.commands:
                        print(f"     {cmd}")

        if info:
            self.print_header("RECOMMENDATIONS")
            for idx, issue in enumerate(info, 1):
                print(f"\n{idx}. {issue.message}")
                print(f"   → {issue.recommendation}")
                if issue.commands:
                    print("   Commands:")
                    for cmd in issue.commands:
                        print(f"     {cmd}")

    def run(self) -> int:
        """Run all diagnostics and return exit code."""
        print("Node.js Environment Diagnostics")
        print(f"Platform: {self.system_info['platform']} {self.system_info['platform_release']}")

        # Check commands
        self.print_header("INSTALLED TOOLS")
        commands = [
            Command("node", ["node", "--version"]),
            Command("npm", ["npm", "--version"]),
            Command("volta", ["volta", "--version"], required=False),
        ]

        for cmd in commands:
            result = self.check_command(cmd)
            self.results[cmd.name] = result
            self.print_result(result)

        # Check PATH configuration
        if self.verbose:
            self.print_header("PATH CONFIGURATION")
            path_config = self.check_path_config()
            print(f"Volta in PATH: {path_config['volta_in_path']}")
            print(f"npm global in PATH: {path_config['npm_global_in_path']}")

            volta_home = self.check_volta_home()
            if volta_home:
                print(f"VOLTA_HOME: {volta_home}")
            else:
                print("VOLTA_HOME: Not set or invalid")

        # Check npm packages
        if self.results.get("npm", DiagnosticResult("npm", False)).found:
            if self.verbose:
                self.print_header("NPM GLOBAL PACKAGES")
                pkg_info = self.check_npm_global_packages()
                if "error" not in pkg_info:
                    print(f"Count: {pkg_info['count']}")
                    print(f"Location: {pkg_info.get('location', 'unknown')}")
                    if pkg_info.get("packages"):
                        print("\nPackages:")
                        for pkg in sorted(pkg_info["packages"]):
                            print(f"  - {pkg}")
                else:
                    print(f"Error: {pkg_info['error']}")

        # Analyze and print issues
        self.analyze_issues()
        self.print_issues()

        # Determine exit code
        critical_count = sum(1 for i in self.issues if i.severity == "critical")
        warning_count = sum(1 for i in self.issues if i.severity == "warning")

        print("\n" + "=" * 60)
        if critical_count > 0:
            print(f"EXIT: CRITICAL ({critical_count} critical issues)")
            return 1
        elif warning_count > 0:
            print(f"EXIT: WARNING ({warning_count} warnings)")
            return 2
        else:
            print("EXIT: HEALTHY")
            return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Diagnose Node.js environment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
  0 - Environment healthy
  1 - Critical issues found
  2 - Warnings but functional

Examples:
  %(prog)s              # Basic check
  %(prog)s --verbose    # Detailed analysis
        """,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output with detailed diagnostics",
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(
        verbose=args.verbose,
        log_file="./diagnose_node_env.log",
        logger_name="node_diagnostics",
    )

    if args.verbose:
        logger.info("Starting Node.js environment diagnostics")
        logger.info(f"Platform: {platform.system()} {platform.release()}")

    diagnostics = NodeDiagnostics(verbose=args.verbose, logger=logger)
    exit_code = diagnostics.run()

    if args.verbose:
        logger.info(f"Diagnostics completed with exit code: {exit_code}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
