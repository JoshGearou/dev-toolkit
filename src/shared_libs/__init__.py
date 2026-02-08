"""
Shared Libraries for dev-rerickso/src Projects

A collection of reusable Python utilities extracted from the get_scheduler library
and designed to be shared across all Python projects in the src/ directory.

Main Components:
- common: Core utilities (logging, error handling, progress tracking)
- io_utils: I/O operations (CSV writing, log formatting, output management)
- cmd_utils: Command execution (subprocess wrappers, timeout handling)
- processing_utils: Batch processing (concurrent execution, pagination)

Usage:
    import sys
    sys.path.insert(0, '../shared_libs')

    from shared_libs.common import setup_logging
    from shared_libs.io_utils import CSVWriter
    from shared_libs.cmd_utils import SubprocessClient
    from shared_libs.processing_utils import BatchProcessor, PaginationManager

Philosophy:
- Zero external dependencies (standard library only)
- Clean, well-documented interfaces
- Robust error handling and timeout management
- Type hints and dataclass usage for better maintainability
- Follows workspace patterns: bash wrappers + Python implementation
"""

__version__ = "1.0.0"
__author__ = "Refactored from get_scheduler library"

# Import key components for easy access at package level

# Command execution utilities
from .cmd_utils import (
    CommandConfig,
    CommandResult,
    CustomCommandWrapper,
    DockerCommandWrapper,
    GitCommandWrapper,
    KubernetesCommandWrapper,
    SubprocessClient,
    SystemCommandWrapper,
    create_command_wrapper,
    create_subprocess_client,
)

# Core utilities from common module
from .common import (
    ErrorInfo,
    ErrorPatternDetector,
    ErrorPatternSet,
    LoggingConfig,
    SignalHandler,
    create_project_logger,
    create_simple_detector,
    setup_logging,
)

# I/O utilities
from .io_utils import (
    ConsoleWriter,
    CSVWriter,
    FileValidator,
    LogWriter,
    MultiFormatWriter,
    OutputManager,
    create_csv_writer,
    create_log_writer,
    create_output_manager,
    validate_file_operations,
)

__all__ = [
    # Common utilities
    "setup_logging",
    "LoggingConfig",
    "SignalHandler",
    "create_project_logger",
    "ErrorPatternDetector",
    "ErrorInfo",
    "ErrorPatternSet",
    "create_simple_detector",
    # I/O utilities
    "CSVWriter",
    "LogWriter",
    "OutputManager",
    "MultiFormatWriter",
    "ConsoleWriter",
    "FileValidator",
    "create_csv_writer",
    "create_log_writer",
    "create_output_manager",
    "validate_file_operations",
    # Command utilities
    "SubprocessClient",
    "CommandConfig",
    "CommandResult",
    "GitCommandWrapper",
    "DockerCommandWrapper",
    "KubernetesCommandWrapper",
    "SystemCommandWrapper",
    "CustomCommandWrapper",
    "create_subprocess_client",
    "create_command_wrapper",
]
