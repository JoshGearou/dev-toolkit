"""
Common utilities module for shared libraries.

This module contains core utilities that are commonly needed across projects:
- Logging setup and configuration
- Error pattern detection and classification
- Progress tracking with time estimation
- Signal handling for graceful shutdown

These utilities are extracted from the get_scheduler library and generalized
for use across all Python projects in the workspace.
"""

# Error handling utilities - implemented
from .error_handling import (
    ErrorInfo,
    ErrorPatternDetector,
    ErrorPatternSet,
    create_simple_detector,
)

# Logging utilities - implemented
from .logging_utils import (
    LoggingConfig,
    SignalHandler,
    create_project_logger,
    setup_logging,
)

# Future imports will be added as modules are implemented:
# from .progress_tracking import ProgressTracker, ProcessingStats

__all__ = [
    # Logging utilities
    "setup_logging",
    "LoggingConfig",
    "SignalHandler",
    "create_project_logger",
    # Error handling utilities
    "ErrorPatternDetector",
    "ErrorInfo",
    "ErrorPatternSet",
    "create_simple_detector",
    # Will be populated as modules are implemented
]
