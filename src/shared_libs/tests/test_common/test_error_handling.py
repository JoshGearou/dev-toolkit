"""
Tests for ErrorPatternDetector class.
"""

import os
import sys
from typing import Any

# Add src directory to path so shared_libs is importable as a package
src_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, src_root)

from shared_libs.common.error_handling import (
    ErrorInfo,
    ErrorPatternDetector,
    ErrorPatternSet,
    create_simple_detector,
)


class TestErrorInfo:
    """Tests for ErrorInfo dataclass."""

    def test_create_error_info(self) -> None:
        """ErrorInfo captures all fields correctly."""
        info = ErrorInfo(
            error_type="test-error",
            is_error=True,
            message="Test error message",
            suggestion="Try again",
            recoverable=True,
        )
        assert info.error_type == "test-error"
        assert info.is_error is True
        assert info.message == "Test error message"
        assert info.suggestion == "Try again"
        assert info.recoverable is True

    def test_success_error_info(self) -> None:
        """ErrorInfo can represent success."""
        info = ErrorInfo(
            error_type="success",
            is_error=False,
            message="OK",
            suggestion="",
            recoverable=True,
        )
        assert info.is_error is False
        assert info.error_type == "success"


class TestErrorPatternSet:
    """Tests for ErrorPatternSet class."""

    def test_create_pattern_set(self) -> None:
        """ErrorPatternSet stores all configuration."""
        pattern_set = ErrorPatternSet(
            name="test-set",
            patterns=[r"error.*pattern", r"another.*error"],
            error_type="test-error",
            message="Test error",
            suggestion="Fix it",
            recoverable=False,
        )
        assert pattern_set.name == "test-set"
        assert len(pattern_set.patterns) == 2
        assert pattern_set.error_type == "test-error"
        assert pattern_set.recoverable is False

    def test_default_recoverable(self) -> None:
        """ErrorPatternSet defaults to recoverable=True."""
        pattern_set = ErrorPatternSet(
            name="test",
            patterns=["test"],
            error_type="test",
            message="test",
            suggestion="test",
        )
        assert pattern_set.recoverable is True


class TestErrorPatternDetectorDefaultPatterns:
    """Tests for ErrorPatternDetector default pattern detection."""

    def test_detect_sso_required(self) -> None:
        """Detect SSO authentication required."""
        detector = ErrorPatternDetector()

        result = detector.detect_error_patterns("To sign in, use a web browser", return_code=1)

        assert result.is_error is True
        assert result.error_type == "sso-required"
        assert "SSO" in result.message
        assert result.recoverable is True

    def test_detect_az_login_required(self) -> None:
        """Detect Azure login required."""
        detector = ErrorPatternDetector()

        result = detector.detect_error_patterns("please run az login to authenticate", return_code=1)

        assert result.is_error is True
        assert result.error_type == "sso-required"

    def test_detect_tls_cert_error(self) -> None:
        """Detect TLS certificate errors."""
        detector = ErrorPatternDetector()

        result = detector.detect_error_patterns(
            "tls: failed to verify certificate: x509: certificate signed by unknown authority",
            return_code=1,
        )

        assert result.is_error is True
        assert result.error_type == "tls-error"
        assert "certificate" in result.message.lower()

    def test_detect_network_error(self) -> None:
        """Detect network connectivity errors."""
        detector = ErrorPatternDetector()

        result = detector.detect_error_patterns("dial tcp 10.0.0.1:443: connection refused", return_code=1)

        assert result.is_error is True
        assert result.error_type == "network-error"

    def test_detect_timeout(self) -> None:
        """Detect timeout from output text."""
        detector = ErrorPatternDetector()

        result = detector.detect_error_patterns("Connection timed out after 30 seconds", return_code=1)

        assert result.is_error is True
        assert result.error_type == "network-error"  # "timeout" in default patterns

    def test_detect_permission_error(self) -> None:
        """Detect permission denied errors."""
        detector = ErrorPatternDetector()

        result = detector.detect_error_patterns("Error: forbidden - user does not have access", return_code=1)

        assert result.is_error is True
        assert result.error_type == "permission-error"
        assert result.recoverable is False


class TestErrorPatternDetectorReturnCodes:
    """Tests for ErrorPatternDetector return code handling."""

    def test_command_not_found_return_code(self) -> None:
        """Detect command not found from return code 127."""
        detector = ErrorPatternDetector()

        result = detector.detect_error_patterns("", return_code=127, command="nonexistent")

        assert result.is_error is True
        assert result.error_type == "command-not-found"
        assert "nonexistent" in result.message
        assert result.recoverable is False

    def test_command_not_found_output(self) -> None:
        """Detect command not found from output text."""
        detector = ErrorPatternDetector()

        result = detector.detect_error_patterns("bash: foobar: command not found", return_code=127)

        assert result.is_error is True
        assert result.error_type == "command-not-found"

    def test_timeout_return_code(self) -> None:
        """Detect timeout from return code 124."""
        detector = ErrorPatternDetector(timeout=60)

        result = detector.detect_error_patterns("", return_code=124)

        assert result.is_error is True
        assert result.error_type == "timeout"
        assert "60" in result.message  # Should show configured timeout

    def test_generic_error(self) -> None:
        """Generic error for unknown non-zero return codes."""
        detector = ErrorPatternDetector()

        result = detector.detect_error_patterns("Some unknown error", return_code=42)

        assert result.is_error is True
        assert result.error_type == "generic-error"
        assert "42" in result.message

    def test_success(self) -> None:
        """Success for return code 0."""
        detector = ErrorPatternDetector()

        result = detector.detect_error_patterns("All good!", return_code=0)

        assert result.is_error is False
        assert result.error_type == "success"


class TestErrorPatternDetectorCustomPatterns:
    """Tests for ErrorPatternDetector custom pattern handling."""

    def test_add_pattern_set(self) -> None:
        """Add custom pattern set."""
        detector = ErrorPatternDetector()

        custom_set = ErrorPatternSet(
            name="my-custom",
            patterns=[r"CUSTOM_ERROR_\d+"],
            error_type="custom-error",
            message="Custom error detected",
            suggestion="Check custom logs",
            recoverable=True,
        )
        detector.add_pattern_set(custom_set)

        result = detector.detect_error_patterns("CUSTOM_ERROR_123", return_code=1)

        assert result.is_error is True
        assert result.error_type == "custom-error"
        assert result.message == "Custom error detected"

    def test_add_simple_pattern(self) -> None:
        """Add simple single-pattern rule."""
        detector = ErrorPatternDetector()

        detector.add_simple_pattern(
            pattern=r"MY_APP_ERROR",
            error_type="my-app-error",
            message="Application error",
            suggestion="Restart the app",
            recoverable=True,
        )

        result = detector.detect_error_patterns("MY_APP_ERROR occurred", return_code=1)

        assert result.is_error is True
        assert result.error_type == "my-app-error"

    def test_custom_patterns_take_precedence(self) -> None:
        """Custom patterns are checked before default patterns."""
        detector = ErrorPatternDetector()

        # Add custom pattern that would also match default network pattern
        detector.add_simple_pattern(
            pattern=r"connection refused",
            error_type="my-network-error",
            message="Custom network error",
            suggestion="Custom suggestion",
        )

        result = detector.detect_error_patterns("connection refused", return_code=1)

        # Custom pattern should match first
        assert result.error_type == "my-network-error"
        assert result.message == "Custom network error"

    def test_get_pattern_sets(self) -> None:
        """Get all pattern sets for inspection."""
        detector = ErrorPatternDetector()

        detector.add_simple_pattern(
            pattern="custom",
            error_type="custom",
            message="Custom",
        )

        pattern_sets = detector.get_pattern_sets()

        # Should have default patterns plus custom
        names = [name for name, _ in pattern_sets]
        assert "sso-auth" in names
        assert "tls-cert" in names
        assert "network" in names
        assert "permission" in names
        assert "custom-custom" in names  # Simple pattern name format


class TestErrorPatternDetectorCaseInsensitive:
    """Tests for case-insensitive pattern matching."""

    def test_case_insensitive_sso(self) -> None:
        """SSO pattern matches case-insensitively."""
        detector = ErrorPatternDetector()

        result = detector.detect_error_patterns("AUTHENTICATION REQUIRED", return_code=1)

        assert result.error_type == "sso-required"

    def test_case_insensitive_tls(self) -> None:
        """TLS pattern matches case-insensitively."""
        detector = ErrorPatternDetector()

        result = detector.detect_error_patterns("CERTIFICATE VERIFY FAILED", return_code=1)

        assert result.error_type == "tls-error"


class TestCreateSimpleDetector:
    """Tests for create_simple_detector factory function."""

    def test_default_config(self) -> None:
        """Factory creates detector with default config."""
        detector = create_simple_detector()
        assert isinstance(detector, ErrorPatternDetector)
        assert detector.timeout == 30

    def test_custom_timeout(self) -> None:
        """Factory creates detector with custom timeout."""
        detector = create_simple_detector(timeout=60)
        assert detector.timeout == 60

        # Verify timeout is used in messages
        result = detector.detect_error_patterns("", return_code=124)
        assert "60" in result.message

    def test_with_additional_patterns(self) -> None:
        """Factory creates detector with additional patterns."""
        patterns = {
            r"SPECIAL_ERROR": {
                "error_type": "special",
                "message": "Special error detected",
                "suggestion": "Special fix",
                "recoverable": False,
            }
        }
        detector = create_simple_detector(additional_patterns=patterns)

        result = detector.detect_error_patterns("SPECIAL_ERROR occurred", return_code=1)

        assert result.error_type == "special"
        assert result.message == "Special error detected"
        assert result.recoverable is False

    def test_additional_patterns_use_defaults(self) -> None:
        """Additional patterns use default values if not specified."""
        patterns: dict[str, dict[str, Any]] = {r"MINIMAL": {}}  # No config specified
        detector = create_simple_detector(additional_patterns=patterns)

        result = detector.detect_error_patterns("MINIMAL error", return_code=1)

        assert result.error_type == "custom"  # default error_type
        assert result.message == "Custom error detected"  # default message
        assert result.recoverable is True  # default recoverable
