"""
Flexible output manager for multiple data formats.

This module provides a factory pattern for managing different output formats
and can be used across all Python projects in the workspace.
"""

from typing import Any, Callable, Dict, List, Optional, Union

from .csv_writer import CSVWriter
from .log_writer import LogWriter


class OutputManager:
    """
    Factory class for managing different output formats.

    Supports:
    - CSV output with flexible field mapping
    - Structured log output with customizable formatting
    - Console output for debugging and progress display
    - Multiple simultaneous output formats
    """

    @staticmethod
    def create_writer(
        output_format: str,
        output_file: str,
        console_output: bool = False,
        **kwargs: Any,
    ) -> Union[CSVWriter, LogWriter]:
        """
        Create appropriate writer based on format.

        Args:
            output_format: 'csv' or 'log'
            output_file: Path to output file
            console_output: Whether to also output to console
            **kwargs: Additional format-specific options

        Returns:
            Writer instance (CSVWriter or LogWriter)

        Raises:
            ValueError: If output format is not supported
        """
        format_lower = output_format.lower()

        if format_lower == "csv":
            return CSVWriter(
                output_file=output_file,
                console_output=console_output,
                fieldnames=kwargs.get("fieldnames"),
                encoding=kwargs.get("encoding", "utf-8"),
            )
        elif format_lower == "log":
            return LogWriter(
                output_file=output_file,
                console_output=console_output,
                encoding=kwargs.get("encoding", "utf-8"),
                title=kwargs.get("title"),
            )
        else:
            raise ValueError(f"Unsupported output format: {output_format}. Supported: csv, log")

    @staticmethod
    def create_multi_writer(
        formats: List[str],
        base_filename: str,
        console_output: bool = False,
        **kwargs: Any,
    ) -> "MultiFormatWriter":
        """
        Create a writer that outputs to multiple formats simultaneously.

        Args:
            formats: List of formats (e.g., ['csv', 'log'])
            base_filename: Base filename (extensions will be added automatically)
            console_output: Whether to also output to console
            **kwargs: Format-specific options

        Returns:
            MultiFormatWriter instance
        """
        return MultiFormatWriter(formats, base_filename, console_output, **kwargs)

    @staticmethod
    def get_console_writer(title: Optional[str] = None) -> "ConsoleWriter":
        """Get console writer for progress display and debugging."""
        return ConsoleWriter(title)


class MultiFormatWriter:
    """
    Writer that outputs data to multiple formats simultaneously.
    """

    def __init__(
        self,
        formats: List[str],
        base_filename: str,
        console_output: bool = False,
        **kwargs: Any,
    ):
        """
        Initialize multi-format writer.

        Args:
            formats: List of output formats
            base_filename: Base filename without extension
            console_output: Whether to show console output
            **kwargs: Format-specific configuration
        """
        self.formats = formats
        self.base_filename = base_filename
        self.console_output = console_output
        self.writers: Dict[str, Union[CSVWriter, LogWriter]] = {}

        # Create writers for each format
        for fmt in formats:
            output_file = f"{base_filename}.{fmt}"
            self.writers[fmt] = OutputManager.create_writer(
                output_format=fmt,
                output_file=output_file,
                console_output=False,  # Only show console output once
                **kwargs,
            )

    def write_data(
        self,
        data: List[Any],
        field_mapper: Optional[Callable[[Any], Dict[str, Any]]] = None,
        primary_field: str = "item",
    ) -> None:
        """
        Write data to all configured formats.

        Args:
            data: List of data objects to write
            field_mapper: Optional function to convert objects to dictionaries
            primary_field: Primary field name for log format
        """
        if not data:
            print("No data to write")
            return

        # Write to each format
        for fmt, writer in self.writers.items():
            try:
                if isinstance(writer, CSVWriter):
                    writer.write_data(data, field_mapper)
                elif isinstance(writer, LogWriter):
                    writer.write_data(data, field_mapper, primary_field)

            except Exception as e:
                print(f"Warning: Failed to write {fmt} format: {e}")

        # Show console output once if requested
        if self.console_output and data:
            console_writer = ConsoleWriter()
            console_writer.display_summary(data, field_mapper, primary_field)

    def get_output_files(self) -> List[str]:
        """Get list of all output file paths."""
        return [f"{self.base_filename}.{fmt}" for fmt in self.formats]


class ConsoleWriter:
    """
    Console output for debugging, progress display, and data summaries.
    """

    def __init__(self, title: Optional[str] = None):
        """
        Initialize console writer.

        Args:
            title: Optional title for console output
        """
        self.title = title or "Data Processing Results"

    def display_summary(
        self,
        data: List[Any],
        field_mapper: Optional[Callable[[Any], Dict[str, Any]]] = None,
        primary_field: str = "item",
    ) -> None:
        """
        Display a summary of data to console.

        Args:
            data: List of data objects
            field_mapper: Optional function to convert objects to dictionaries
            primary_field: Primary field name for identification
        """
        if not data:
            print("No data to display")
            return

        print("\n" + "=" * 60)
        print(f"{self.title}")
        print(f"Total Items: {len(data)}")
        print("=" * 60)

        # Convert first few items for preview
        preview_data = self._prepare_preview_data(data[:5], field_mapper)

        for i, entry in enumerate(preview_data, 1):
            primary_value = entry.get(primary_field, entry.get("id", entry.get("name", f"item_{i}")))
            print(f"[{i}] {primary_field.title()}: {primary_value}")

            # Show key fields (limit to avoid clutter)
            shown = 0
            for key, value in entry.items():
                if key != primary_field and shown < 3:
                    value_str = str(value)
                    if len(value_str) > 50:
                        value_str = value_str[:47] + "..."
                    print(f"    {key.replace('_', ' ').title()}: {value_str}")
                    shown += 1
            print()

        if len(data) > 5:
            print(f"... and {len(data) - 5} more items")

        print("=" * 60 + "\n")

    def display_progress(self, current: int, total: int, item_name: str = "item") -> None:
        """
        Display progress information.

        Args:
            current: Current item number
            total: Total number of items
            item_name: Name of items being processed
        """
        percentage = (current / total) * 100 if total > 0 else 0
        bar_length = 40
        filled = int(bar_length * current / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)

        print(
            f"\rProgress: [{bar}] {percentage:5.1f}% ({current}/{total} {item_name}s)",
            end="",
            flush=True,
        )

        if current >= total:
            print()  # New line when complete

    def display_error_summary(self, errors: List[str]) -> None:
        """
        Display error summary.

        Args:
            errors: List of error messages
        """
        if not errors:
            print("✅ No errors detected")
            return

        print(f"\n⚠️  {len(errors)} error(s) detected:")
        for i, error in enumerate(errors[:10], 1):  # Limit to 10 errors
            print(f"  {i}. {error}")

        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
        print()

    def _prepare_preview_data(
        self,
        data: List[Any],
        field_mapper: Optional[Callable[[Any], Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Prepare data for console preview display."""
        preview_data = []

        for item in data:
            try:
                if field_mapper:
                    entry_dict = field_mapper(item)
                elif isinstance(item, dict):
                    entry_dict = item
                elif hasattr(item, "to_log_dict"):
                    entry_dict = item.to_log_dict()
                elif hasattr(item, "__dict__"):
                    entry_dict = {k: v for k, v in item.__dict__.items()}
                else:
                    entry_dict = {"value": str(item)}

                preview_data.append(entry_dict)

            except Exception as e:
                preview_data.append({"error": f"Could not display: {e}"})

        return preview_data


def create_output_manager(
    output_format: str, output_file: str, console_output: bool = False, **kwargs: Any
) -> Union[CSVWriter, LogWriter]:
    """
    Convenience function to create an output writer.

    Args:
        output_format: Format type ('csv' or 'log')
        output_file: Output file path
        console_output: Whether to also show console output
        **kwargs: Additional format-specific options

    Returns:
        Configured writer instance
    """
    return OutputManager.create_writer(
        output_format=output_format,
        output_file=output_file,
        console_output=console_output,
        **kwargs,
    )
