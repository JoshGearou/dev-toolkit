"""
Shared error handling utilities for command output analysis.

This module provides configurable error pattern detection and classification
that can be used across all Python projects in the workspace.

Features:
- Configurable error pattern sets
- Extensible error classification
- Custom error detection rules
- Structured error information
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ErrorInfo:
    """
    Detailed error information for troubleshooting and recovery.
    """

    error_type: str
    is_error: bool
    message: str
    suggestion: str
    recoverable: bool


class ErrorPatternSet:
    """Represents a set of error patterns with metadata."""

    def __init__(
        self,
        name: str,
        patterns: List[str],
        error_type: str,
        message: str,
        suggestion: str,
        recoverable: bool = True,
    ):
        self.name = name
        self.patterns = patterns
        self.error_type = error_type
        self.message = message
        self.suggestion = suggestion
        self.recoverable = recoverable


class ErrorPatternDetector:
    """
    Configurable error pattern detection and classification.

    This class allows for customizable error detection patterns that can be
    adapted for different types of commands and applications.
    """

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._pattern_sets = self._get_default_patterns()
        self._custom_patterns: List[ErrorPatternSet] = []

    def _get_default_patterns(self) -> List[ErrorPatternSet]:
        """Get the default set of error patterns commonly needed across projects."""
        return [
            ErrorPatternSet(
                name="sso-auth",
                patterns=[
                    r"To sign in, use a web browser",
                    r"please run az login",
                    r"authentication required",
                    r"login required",
                    r"Please re-run azure login",
                    r"interactive authentication is needed",
                    r"https://microsoft\.com/devicelogin",
                    r"enter the code .* to authenticate",
                    r"authentication via web browser.*required",
                ],
                error_type="sso-required",
                message="SSO authentication required",
                suggestion="Please complete SSO authentication in your web browser and retry",
                recoverable=True,
            ),
            ErrorPatternSet(
                name="tls-cert",
                patterns=[
                    r"tls: failed to verify certificate",
                    r"certificate verify failed",
                    r"x509: certificate",
                    r"certificate signed by unknown authority",
                    r"certificate has expired",
                    r"certificate is not valid",
                    r"ssl certificate problem",
                ],
                error_type="tls-error",
                message="TLS certificate verification failed",
                suggestion="Use --skip-tls-verify flag (INSECURE) or contact your administrator to fix certificate issues",
                recoverable=True,
            ),
            ErrorPatternSet(
                name="network",
                patterns=[
                    r"connection refused",
                    r"network is unreachable",
                    r"timeout",
                    r"connection timed out",
                    r"dial tcp.*timeout",
                    r"no route to host",
                    r"temporary failure in name resolution",
                ],
                error_type="network-error",
                message="Network connectivity issue",
                suggestion="Check network connectivity and endpoint configuration",
                recoverable=True,
            ),
            ErrorPatternSet(
                name="permission",
                patterns=[
                    r"forbidden",
                    r"unauthorized",
                    r"access denied",
                    r"permission denied",
                    r"user.*cannot.*get",
                    r"RBAC.*denied",
                ],
                error_type="permission-error",
                message="Permission denied or insufficient permissions",
                suggestion="Contact your administrator to check permissions",
                recoverable=False,
            ),
            ErrorPatternSet(
                name="service-not-found",
                patterns=[
                    r"service not found",
                    r"no records found",
                    r"service.*does not exist",
                    r"could not find.*service",
                ],
                error_type="service-not-found",
                message="Service not found in system",
                suggestion="Verify the service name and check if it exists in the target environment",
                recoverable=False,
            ),
        ]

    def add_pattern_set(self, pattern_set: ErrorPatternSet) -> None:
        """Add a custom error pattern set."""
        self._custom_patterns.append(pattern_set)

    def add_simple_pattern(
        self,
        pattern: str,
        error_type: str,
        message: str,
        suggestion: str = "",
        recoverable: bool = True,
    ) -> None:
        """Add a simple single-pattern error detection rule."""
        pattern_set = ErrorPatternSet(
            name=f"custom-{error_type}",
            patterns=[pattern],
            error_type=error_type,
            message=message,
            suggestion=suggestion,
            recoverable=recoverable,
        )
        self.add_pattern_set(pattern_set)

    def detect_error_patterns(self, output: str, return_code: int, command: str = "") -> ErrorInfo:
        """
        Detect and classify error patterns from command output.

        Args:
            output: Command output text
            return_code: Command return code
            command: Command that was executed (optional)

        Returns:
            ErrorInfo with classification and details
        """
        # Check custom patterns first (higher priority)
        for pattern_set in self._custom_patterns:
            if self._matches_pattern_set(output, pattern_set):
                return ErrorInfo(
                    error_type=pattern_set.error_type,
                    is_error=True,
                    message=pattern_set.message,
                    suggestion=pattern_set.suggestion,
                    recoverable=pattern_set.recoverable,
                )

        # Check default patterns
        for pattern_set in self._pattern_sets:
            if self._matches_pattern_set(output, pattern_set):
                return ErrorInfo(
                    error_type=pattern_set.error_type,
                    is_error=True,
                    message=pattern_set.message,
                    suggestion=pattern_set.suggestion,
                    recoverable=pattern_set.recoverable,
                )

        # Check for common return codes
        if return_code == 127 or "command not found" in output.lower():
            cmd_name = command.split()[0] if command else "unknown"
            return ErrorInfo(
                error_type="command-not-found",
                is_error=True,
                message=f"Command not found: {cmd_name}",
                suggestion="Ensure the required command is installed and in PATH",
                recoverable=False,
            )

        # Timeout errors (return code 124 or timeout in output)
        if return_code == 124 or re.search(r"timeout|timed out", output, re.IGNORECASE):
            return ErrorInfo(
                error_type="timeout",
                is_error=True,
                message=f"Command timed out after {self.timeout} seconds",
                suggestion="Try increasing timeout or check for hanging processes",
                recoverable=True,
            )

        # Generic non-zero return code
        if return_code != 0:
            return ErrorInfo(
                error_type="generic-error",
                is_error=True,
                message=f"Command failed with return code {return_code}",
                suggestion="Check command output for details",
                recoverable=True,
            )

        # No error detected
        return ErrorInfo(
            error_type="success",
            is_error=False,
            message="Command completed successfully",
            suggestion="",
            recoverable=True,
        )

    def _matches_pattern_set(self, output: str, pattern_set: ErrorPatternSet) -> bool:
        """Check if output matches any pattern in the set."""
        for pattern in pattern_set.patterns:
            if re.search(pattern, output, re.IGNORECASE):
                return True
        return False

    def get_pattern_sets(self) -> List[Tuple[str, List[str]]]:
        """Get list of all pattern sets for debugging/inspection."""
        all_sets = []
        for pattern_set in self._pattern_sets + self._custom_patterns:
            all_sets.append((pattern_set.name, pattern_set.patterns))
        return all_sets


def create_simple_detector(
    timeout: int = 30, additional_patterns: Optional[Dict[str, Dict[str, Any]]] = None
) -> ErrorPatternDetector:
    """
    Create a simple error detector with optional additional patterns.

    Args:
        timeout: Command timeout in seconds
        additional_patterns: Dict of {pattern: {error_type, message, suggestion, recoverable}}

    Returns:
        Configured ErrorPatternDetector
    """
    detector = ErrorPatternDetector(timeout=timeout)

    if additional_patterns:
        for pattern, config in additional_patterns.items():
            detector.add_simple_pattern(
                pattern=pattern,
                error_type=config.get("error_type", "custom"),
                message=config.get("message", "Custom error detected"),
                suggestion=config.get("suggestion", ""),
                recoverable=config.get("recoverable", True),
            )

    return detector
