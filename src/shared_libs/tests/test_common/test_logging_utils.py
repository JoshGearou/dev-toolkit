"""
Tests for logging utilities.
"""

import logging
import os
import sys
import tempfile

# Add src directory to path so shared_libs is importable as a package
src_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, src_root)

from shared_libs.common.logging_utils import (
    LoggingConfig,
    SignalHandler,
    create_project_logger,
    setup_logging,
)


class TestLoggingConfig:
    """Tests for LoggingConfig constants."""

    def test_default_log_file(self) -> None:
        """Default log file is set."""
        assert LoggingConfig.DEFAULT_LOG_FILE == "./application.log"

    def test_log_format(self) -> None:
        """Log format contains expected placeholders."""
        assert "%(asctime)s" in LoggingConfig.LOG_FORMAT
        assert "%(levelname)s" in LoggingConfig.LOG_FORMAT
        assert "%(message)s" in LoggingConfig.LOG_FORMAT

    def test_date_format(self) -> None:
        """Date format is ISO-like."""
        assert "%Y-%m-%d" in LoggingConfig.DATE_FORMAT
        assert "%H:%M:%S" in LoggingConfig.DATE_FORMAT


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_returns_logger(self) -> None:
        """setup_logging returns a Logger instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(log_file=log_file, logger_name="test_logger_1")

            assert isinstance(logger, logging.Logger)
            assert logger.name == "test_logger_1"

    def test_creates_log_file(self) -> None:
        """setup_logging creates the log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(log_file=log_file, logger_name="test_logger_2")

            logger.info("Test message")

            assert os.path.exists(log_file)

    def test_creates_log_directory(self) -> None:
        """setup_logging creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "subdir", "nested", "test.log")
            logger = setup_logging(log_file=log_file, logger_name="test_logger_3")

            logger.info("Test message")

            assert os.path.exists(log_file)

    def test_verbose_mode(self) -> None:
        """Verbose mode sets console handler to DEBUG."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(verbose=True, log_file=log_file, logger_name="test_logger_4")

            # Find console handler
            console_handler = None
            for handler in logger.handlers:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    console_handler = handler
                    break

            assert console_handler is not None
            assert console_handler.level == logging.DEBUG

    def test_non_verbose_mode(self) -> None:
        """Non-verbose mode sets console handler to INFO."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(verbose=False, log_file=log_file, logger_name="test_logger_5")

            # Find console handler
            console_handler = None
            for handler in logger.handlers:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    console_handler = handler
                    break

            assert console_handler is not None
            assert console_handler.level == logging.INFO

    def test_has_file_and_console_handlers(self) -> None:
        """Logger has both file and console handlers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(log_file=log_file, logger_name="test_logger_6")

            handler_types = [type(h).__name__ for h in logger.handlers]

            assert "FileHandler" in handler_types
            assert "StreamHandler" in handler_types

    def test_propagate_disabled(self) -> None:
        """Logger propagate is disabled to prevent duplicate logs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(log_file=log_file, logger_name="test_logger_7")

            assert logger.propagate is False

    def test_clears_existing_handlers(self) -> None:
        """Calling setup_logging twice doesn't duplicate handlers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")

            # Setup twice
            setup_logging(log_file=log_file, logger_name="test_logger_8")
            logger = setup_logging(log_file=log_file, logger_name="test_logger_8")

            # Should have exactly 2 handlers (file + console)
            assert len(logger.handlers) == 2


class TestCreateProjectLogger:
    """Tests for create_project_logger function."""

    def test_creates_logger_with_project_name(self) -> None:
        """Logger is named after the project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = create_project_logger("my_project", log_dir=tmpdir)

            assert logger.name == "my_project"

    def test_creates_log_file_with_project_name(self) -> None:
        """Log file is named after the project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = create_project_logger("my_project", log_dir=tmpdir)
            logger.info("Test")

            expected_file = os.path.join(tmpdir, "my_project.log")
            assert os.path.exists(expected_file)

    def test_default_log_directory(self) -> None:
        """Default log directory is ./output."""
        # Just verify the logger is created (can't easily test default dir)
        logger = create_project_logger("temp_project_test")
        assert logger.name == "temp_project_test"

        # Cleanup
        if os.path.exists("./output/temp_project_test.log"):
            os.remove("./output/temp_project_test.log")

    def test_verbose_option(self) -> None:
        """Verbose option is passed through."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = create_project_logger("verbose_project", verbose=True, log_dir=tmpdir)

            # Find console handler
            console_handler = None
            for handler in logger.handlers:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    console_handler = handler
                    break

            assert console_handler is not None
            assert console_handler.level == logging.DEBUG


class TestSignalHandler:
    """Tests for SignalHandler class."""

    def test_initialization(self) -> None:
        """SignalHandler initializes with logger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(log_file=log_file, logger_name="signal_test")

            handler = SignalHandler(logger)

            assert handler.logger is logger
