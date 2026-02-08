"""
Shared logging utilities for all projects in the workspace.

This module provides standardized logging setup and configuration that can be
used across all Python projects in the dev-rerickso/src directory.

Features:
- Dual logging (file + console) with configurable levels
- Consistent formatting and timestamps
- Graceful shutdown signal handling
- Configurable log file paths and logger names
"""

import logging
import os
import signal
import sys
from types import FrameType
from typing import Optional


class LoggingConfig:
    """Configuration constants for logging setup."""

    DEFAULT_LOG_FILE = "./application.log"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    verbose: bool = False,
    log_file: Optional[str] = None,
    logger_name: str = "application",
) -> logging.Logger:
    """
    Setup dual logging (file + console) with appropriate levels.

    Args:
        verbose: Enable DEBUG level for console output
        log_file: Path to log file (default: ./application.log)
        logger_name: Name for the logger instance (default: "application")

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    logger.handlers.clear()

    # File handler - always DEBUG level
    file_path = log_file or LoggingConfig.DEFAULT_LOG_FILE

    # Ensure log directory exists
    log_dir = os.path.dirname(os.path.abspath(file_path))
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    file_handler = logging.FileHandler(file_path)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LoggingConfig.LOG_FORMAT, datefmt=LoggingConfig.DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler - DEBUG if verbose, INFO otherwise
    console_handler = logging.StreamHandler()
    console_level = logging.DEBUG if verbose else logging.INFO
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter(LoggingConfig.LOG_FORMAT, datefmt=LoggingConfig.DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Prevent duplicate logs from root logger
    logger.propagate = False

    logger.info(f"Logging initialized - File: {file_path}, Console level: {console_level}")
    return logger


class SignalHandler:
    """Handles graceful shutdown on SIGINT/SIGTERM."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, frame: Optional[FrameType]) -> None:
        """Handle graceful shutdown signal."""
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        self.logger.info(f"Received {signal_name} signal. Finishing current operation...")
        sys.exit(0)


def create_project_logger(project_name: str, verbose: bool = False, log_dir: Optional[str] = None) -> logging.Logger:
    """
    Create a standardized logger for a specific project.

    This is a convenience function that sets up logging with project-specific
    defaults, following workspace conventions.

    Args:
        project_name: Name of the project (used for logger name and log file)
        verbose: Enable DEBUG level for console output
        log_dir: Directory for log files (default: ./output)

    Returns:
        Configured logger instance
    """
    if log_dir:
        log_file = os.path.join(log_dir, f"{project_name}.log")
    else:
        log_file = f"./output/{project_name}.log"

    return setup_logging(verbose=verbose, log_file=log_file, logger_name=project_name)
