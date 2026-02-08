"""
I/O utilities module for shared libraries.

This module handles various input/output operations:
- CSV writing with proper escaping and formatting
- Structured log file output
- Output management with multiple format support
- File validation and disk space checking

These utilities provide robust, consistent I/O operations across all projects.
"""

# I/O utilities - implemented
from .csv_writer import CSVSerializable, CSVWriter, create_csv_writer
from .file_validator import FileValidator, validate_file_operations
from .log_writer import LogSerializable, LogWriter, create_log_writer
from .output_manager import (
    ConsoleWriter,
    MultiFormatWriter,
    OutputManager,
    create_output_manager,
)

__all__ = [
    # CSV utilities
    "CSVWriter",
    "CSVSerializable",
    "create_csv_writer",
    # Log utilities
    "LogWriter",
    "LogSerializable",
    "create_log_writer",
    # Output management
    "OutputManager",
    "MultiFormatWriter",
    "ConsoleWriter",
    "create_output_manager",
    # File validation utilities
    "FileValidator",
    "validate_file_operations",
]
