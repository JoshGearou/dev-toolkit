"""
File validation and disk space checking utilities.

This module provides file validation, permission checking, and disk space
validation that can be used across all projects in the workspace.
"""

import os
import shutil
from typing import Optional


class FileValidator:
    """
    File validation and disk space checking utilities.

    Provides comprehensive file system validation including:
    - Path validation and directory creation
    - Permission checking for read/write operations
    - Disk space validation with configurable thresholds
    - Safe write testing with temporary files
    """

    @staticmethod
    def validate_output_file(output_file: str, min_space_mb: int = 10) -> None:
        """
        Validate output file path and permissions.

        Args:
            output_file: Path to output file
            min_space_mb: Minimum required free space in MB

        Raises:
            Exception: If file path is invalid or not writable
        """
        try:
            # Check if parent directory exists and is writable
            parent_dir = os.path.dirname(os.path.abspath(output_file))

            # Create parent directory if it doesn't exist
            if not os.path.exists(parent_dir):
                try:
                    os.makedirs(parent_dir, exist_ok=True)
                except PermissionError:
                    raise Exception(f"Permission denied: Cannot create directory {parent_dir}")
                except OSError as e:
                    raise Exception(f"Cannot create directory {parent_dir}: {e}")

            # Check if directory is writable
            if not os.access(parent_dir, os.W_OK):
                raise Exception(f"Permission denied: Directory {parent_dir} is not writable")

            # Check if file exists and is writable
            if os.path.exists(output_file):
                if not os.access(output_file, os.W_OK):
                    raise Exception(f"Permission denied: File {output_file} is not writable")

            # Check available disk space
            try:
                free_space = shutil.disk_usage(parent_dir).free
                min_space_bytes = min_space_mb * 1024 * 1024
                if free_space < min_space_bytes:
                    raise Exception(f"Insufficient disk space: {
                            free_space // (
                                1024 * 1024)}MB available, need at least {min_space_mb}MB")
            except (AttributeError, OSError):
                # shutil.disk_usage might not be available on all systems
                pass

            # Test write access with a temporary file
            temp_test_file = f"{output_file}.writetest"
            try:
                with open(temp_test_file, "w", encoding="utf-8") as f:
                    f.write("test")
                os.remove(temp_test_file)
            except Exception as e:
                raise Exception(f"Cannot write to output location: {e}")

        except Exception as e:
            raise Exception(f"Output file validation failed: {e}")

    @staticmethod
    def check_file_space_before_write(output_file: str, estimated_size: int = 0, buffer_mb: int = 5) -> None:
        """
        Check if there's enough space before writing.

        Args:
            output_file: Path to output file
            estimated_size: Estimated size in bytes (0 for basic check)
            buffer_mb: Buffer space to add in MB

        Raises:
            Exception: If insufficient disk space
        """
        try:
            parent_dir = os.path.dirname(os.path.abspath(output_file))
            free_space = shutil.disk_usage(parent_dir).free

            # Add buffer space (buffer_mb + estimated size)
            buffer_bytes = buffer_mb * 1024 * 1024
            required_space = max(buffer_bytes, estimated_size + buffer_bytes)

            if free_space < required_space:
                raise Exception(f"Insufficient disk space for write: {
                        free_space //
                        (
                            1024 *
                            1024)}MB available, need {
                        required_space //
                        (
                            1024 *
                            1024)}MB")
        except (AttributeError, OSError):
            # Ignore if we can't check disk space - system may not support it
            pass

    @staticmethod
    def validate_input_file(input_file: str) -> None:
        """
        Validate input file exists and is readable.

        Args:
            input_file: Path to input file

        Raises:
            Exception: If file doesn't exist or isn't readable
        """
        if not os.path.exists(input_file):
            raise Exception(f"Input file does not exist: {input_file}")

        if not os.path.isfile(input_file):
            raise Exception(f"Path is not a file: {input_file}")

        if not os.access(input_file, os.R_OK):
            raise Exception(f"Permission denied: File {input_file} is not readable")

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        Get file size in bytes.

        Args:
            file_path: Path to file

        Returns:
            File size in bytes

        Raises:
            Exception: If file doesn't exist or can't be accessed
        """
        try:
            return os.path.getsize(file_path)
        except OSError as e:
            raise Exception(f"Cannot get size of file {file_path}: {e}")

    @staticmethod
    def get_disk_usage(path: str) -> tuple[int, int, int]:
        """
        Get disk usage for a path.

        Args:
            path: Directory path to check

        Returns:
            Tuple of (total, used, free) in bytes

        Raises:
            Exception: If path doesn't exist or can't be accessed
        """
        try:
            usage = shutil.disk_usage(path)
            return usage.total, usage.used, usage.free
        except OSError as e:
            raise Exception(f"Cannot get disk usage for {path}: {e}")

    @staticmethod
    def ensure_directory_exists(directory: str, mode: int = 0o755) -> None:
        """
        Ensure directory exists, creating it if necessary.

        Args:
            directory: Directory path
            mode: Directory permissions (default: 0o755)

        Raises:
            Exception: If directory cannot be created
        """
        try:
            if not os.path.exists(directory):
                os.makedirs(directory, mode=mode, exist_ok=True)
            elif not os.path.isdir(directory):
                raise Exception(f"Path exists but is not a directory: {directory}")
        except OSError as e:
            raise Exception(f"Cannot create directory {directory}: {e}")

    @staticmethod
    def is_safe_path(base_path: str, target_path: str) -> bool:
        """
        Check if target_path is safe (within base_path, no path traversal).

        Args:
            base_path: Base directory path
            target_path: Target file/directory path

        Returns:
            True if path is safe, False otherwise
        """
        try:
            base = os.path.abspath(base_path)
            target = os.path.abspath(target_path)
            return target.startswith(base + os.sep) or target == base
        except (OSError, ValueError):
            return False


def validate_file_operations(
    input_files: Optional[list[str]] = None,
    output_file: Optional[str] = None,
    min_space_mb: int = 10,
) -> None:
    """
    Convenience function to validate multiple file operations.

    Args:
        input_files: List of input files to validate (optional)
        output_file: Output file to validate (optional)
        min_space_mb: Minimum required free space in MB

    Raises:
        Exception: If any validation fails
    """
    validator = FileValidator()

    if input_files:
        for input_file in input_files:
            validator.validate_input_file(input_file)

    if output_file:
        validator.validate_output_file(output_file, min_space_mb)
