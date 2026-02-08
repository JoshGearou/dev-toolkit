"""
Flexible structured log writer for any data objects.

This module provides a generalized log writer that can format any data objects
into human-readable log format with consistent field alignment and timestamps.
"""

import datetime
import os
from typing import Any, Callable, Dict, List, Optional, Protocol, TextIO, Union


class LogSerializable(Protocol):
    """Protocol for objects that can be serialized to structured logs."""

    def to_log_dict(self) -> Dict[str, Any]:
        """Convert object to log-compatible dictionary."""
        ...


class LogWriter:
    """
    Generic structured log output formatter for various data types.

    Creates human-readable log format with consistent field alignment
    and timestamps. Can handle dictionaries, objects with attributes,
    or custom serializable objects.
    """

    def __init__(
        self,
        output_file: str,
        console_output: bool = False,
        encoding: str = "utf-8",
        title: Optional[str] = None,
    ):
        """
        Initialize log writer.

        Args:
            output_file: Path to output log file
            console_output: Also output to console
            encoding: File encoding (default: utf-8)
            title: Custom title for log header (default: auto-generated)
        """
        self.output_file = output_file
        self.console_output = console_output
        self.encoding = encoding
        self.title = title

    def write_data(
        self,
        data: List[Union[Dict[str, Any], LogSerializable, Any]],
        field_mapper: Optional[Callable[[Any], Dict[str, Any]]] = None,
        primary_field: str = "item",
    ) -> None:
        """
        Write data to log file with atomic operation.

        Args:
            data: List of data objects to write
            field_mapper: Optional function to convert objects to dictionaries
            primary_field: Name of the primary field for display (default: "item")
        """
        if not data:
            print("No data to write to log")
            return

        # Convert data to log-compatible format
        log_data = self._prepare_data(data, field_mapper)

        if not log_data:
            print("No valid data after conversion")
            return

        # Use temporary file for atomic writes
        temp_file = f"{self.output_file}.tmp"

        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(self.output_file)), exist_ok=True)

            with open(temp_file, "w", encoding=self.encoding) as logfile:
                # Write header
                self._write_header(logfile, len(log_data))

                # Write individual data entries
                for i, entry in enumerate(log_data, 1):
                    self._write_entry(logfile, entry, i, primary_field)

            # Atomic move - replace original file
            os.replace(temp_file, self.output_file)

            success_msg = f"✅ Log data written to: {self.output_file} ({len(log_data)} entries)"
            print(success_msg)

            # Optional console output
            if self.console_output:
                self._write_console_log(log_data, primary_field)

        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass
            raise Exception(f"Failed to write log file: {e}")

    def _prepare_data(
        self,
        data: List[Union[Dict[str, Any], LogSerializable, Any]],
        field_mapper: Optional[Callable[[Any], Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Convert various data types to log-compatible dictionaries."""
        log_data = []

        for item in data:
            try:
                if field_mapper:
                    # Use custom field mapper function
                    entry_dict = field_mapper(item)
                elif isinstance(item, dict):
                    # Already a dictionary
                    entry_dict = item
                elif hasattr(item, "to_log_dict"):
                    # Implements LogSerializable protocol
                    entry_dict = item.to_log_dict()
                elif hasattr(item, "__dict__"):
                    # Object with attributes - use as dictionary
                    entry_dict = {k: v for k, v in item.__dict__.items()}
                elif hasattr(item, "_asdict"):
                    # NamedTuple
                    entry_dict = dict(item._asdict())
                else:
                    # Try to convert to string representation
                    entry_dict = {"value": str(item)}

                log_data.append(entry_dict)

            except Exception as e:
                print(f"Warning: Could not convert data item to log format: {e}")
                continue

        return log_data

    def _write_header(self, logfile: TextIO, entry_count: int) -> None:
        """Write log file header."""
        title = self.title or "DATA PROCESSING RESULTS"

        logfile.write("=" * 80 + "\n")
        logfile.write(f"{title}\n")
        logfile.write(f"Generated: {datetime.datetime.now().isoformat()}\n")
        logfile.write(f"Total Entries: {entry_count}\n")
        logfile.write("=" * 80 + "\n\n")

    def _write_entry(self, logfile: TextIO, entry: Dict[str, Any], index: int, primary_field: str) -> None:
        """Write a single entry to the log file."""
        # Determine primary identifier for this entry
        primary_value = entry.get(primary_field, entry.get("id", entry.get("name", f"entry_{index}")))

        logfile.write(f"[{index:3d}] {primary_field.upper()}: {primary_value}\n")

        # Write all fields with consistent formatting
        for key, value in entry.items():
            if key != primary_field:  # Skip primary field as it's already shown
                # Format the key with proper spacing
                formatted_key = f"{key.replace('_', ' ').title()}:"
                logfile.write(f"     {formatted_key:<20} {value}\n")

        logfile.write("\n")  # Add blank line between entries

    def _write_console_log(self, log_data: List[Dict[str, Any]], primary_field: str) -> None:
        """Write log data to console for debugging/verification."""
        print("\n" + "=" * 60)
        print("Log Data Preview (console output):")
        print("=" * 60)

        # Show first few entries
        for i, entry in enumerate(log_data[:5], 1):  # Limit to 5 entries
            primary_value = entry.get(primary_field, entry.get("id", entry.get("name", f"entry_{i}")))
            print(f"[{i}] {primary_field.title()}: {primary_value}")

            # Show a few key fields
            shown_fields = 0
            for key, value in entry.items():
                if key != primary_field and shown_fields < 3:
                    formatted_key = key.replace("_", " ").title()
                    value_str = str(value)[:40] + "..." if len(str(value)) > 40 else str(value)
                    print(f"    {formatted_key}: {value_str}")
                    shown_fields += 1
            print()

        if len(log_data) > 5:
            print(f"... and {len(log_data) - 5} more entries")
        print("=" * 60 + "\n")

    def append_data(
        self,
        data: List[Union[Dict[str, Any], LogSerializable, Any]],
        field_mapper: Optional[Callable[[Any], Dict[str, Any]]] = None,
        primary_field: str = "item",
    ) -> None:
        """
        Append data to existing log file.

        Args:
            data: List of data objects to append
            field_mapper: Optional function to convert objects to dictionaries
            primary_field: Name of the primary field for display
        """
        if not data:
            return

        log_data = self._prepare_data(data, field_mapper)

        if not log_data:
            return

        # If file doesn't exist, write normally
        if not os.path.exists(self.output_file):
            self.write_data(data, field_mapper, primary_field)
            return

        # Append to existing file
        try:
            with open(self.output_file, "a", encoding=self.encoding) as logfile:
                logfile.write("\n" + "-" * 80 + "\n")
                logfile.write(f"APPENDED: {datetime.datetime.now().isoformat()}\n")
                logfile.write("-" * 80 + "\n\n")

                # Start numbering from existing count (approximate)
                start_index = self._estimate_existing_entries() + 1

                for i, entry in enumerate(log_data, start_index):
                    self._write_entry(logfile, entry, i, primary_field)

            print(f"✅ Appended {len(log_data)} entries to: {self.output_file}")

        except Exception as e:
            raise Exception(f"Failed to append to log file: {e}")

    def _estimate_existing_entries(self) -> int:
        """Estimate number of existing entries in log file."""
        try:
            with open(self.output_file, "r", encoding=self.encoding) as f:
                content = f.read()
                # Count entry markers (lines starting with [nnn])
                import re

                matches = re.findall(r"^\[\s*\d+\]", content, re.MULTILINE)
                return len(matches)
        except BaseException:
            return 0


def create_log_writer(output_file: str, title: Optional[str] = None, console_output: bool = False) -> LogWriter:
    """
    Create a log writer with specified configuration.

    Args:
        output_file: Path to output log file
        title: Custom title for log header
        console_output: Whether to also output to console

    Returns:
        Configured LogWriter instance
    """
    return LogWriter(output_file=output_file, console_output=console_output, title=title)
