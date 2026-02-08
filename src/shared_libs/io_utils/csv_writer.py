"""
Flexible CSV writer for any data structures.

This module provides a generalized CSV writer that can handle any data objects,
not just scheduler-specific ServiceResult objects.
"""

import csv
import os
from typing import Any, Callable, Dict, List, Optional, Protocol, Union


class CSVSerializable(Protocol):
    """Protocol for objects that can be serialized to CSV."""

    def to_csv_dict(self) -> Dict[str, Any]:
        """Convert object to CSV-compatible dictionary."""
        ...


class CSVWriter:
    """
    Generic CSV output formatter that can handle various data types.

    Supports:
    - Dictionary objects directly
    - Objects implementing CSVSerializable protocol
    - Objects with dataclass fields
    - Custom field mapping functions
    """

    def __init__(
        self,
        output_file: str,
        fieldnames: Optional[List[str]] = None,
        console_output: bool = False,
        encoding: str = "utf-8",
    ):
        """
        Initialize CSV writer.

        Args:
            output_file: Path to output CSV file
            fieldnames: List of column names (auto-detected if None)
            console_output: Also output to console
            encoding: File encoding (default: utf-8)
        """
        self.output_file = output_file
        self.fieldnames = fieldnames
        self.console_output = console_output
        self.encoding = encoding
        self._auto_detected_fields = False

    def write_data(
        self,
        data: List[Union[Dict[str, Any], CSVSerializable, Any]],
        field_mapper: Optional[Callable[[Any], Dict[str, Any]]] = None,
    ) -> None:
        """
        Write data to CSV file with atomic operation.

        Args:
            data: List of data objects to write
            field_mapper: Optional function to convert objects to dictionaries
        """
        if not data:
            print("No data to write to CSV")
            return

        # Convert data to dictionaries
        csv_data = self._prepare_data(data, field_mapper)

        if not csv_data:
            print("No valid data after conversion")
            return

        # Auto-detect fieldnames if not provided
        if self.fieldnames is None:
            self.fieldnames = list(csv_data[0].keys())
            self._auto_detected_fields = True

        # Use temporary file for atomic writes
        temp_file = f"{self.output_file}.tmp"

        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(self.output_file)), exist_ok=True)

            with open(temp_file, "w", newline="", encoding=self.encoding) as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)

                # Write header
                writer.writeheader()

                # Write data rows
                for row_data in csv_data:
                    # Only write fields that are in fieldnames
                    filtered_row = {field: row_data.get(field, "") for field in self.fieldnames}
                    writer.writerow(filtered_row)

            # Atomic move - replace original file
            os.replace(temp_file, self.output_file)

            success_msg = f"✅ CSV data written to: {self.output_file} " f"({len(csv_data)} records)"
            print(success_msg)

            # Optional console output
            if self.console_output:
                self._write_console_csv(csv_data)

        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass
            raise Exception(f"Failed to write CSV file: {e}")

    def _prepare_data(
        self,
        data: List[Union[Dict[str, Any], CSVSerializable, Any]],
        field_mapper: Optional[Callable[[Any], Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Convert various data types to CSV-compatible dictionaries."""
        csv_data = []

        for item in data:
            try:
                if field_mapper:
                    # Use custom field mapper function
                    row_dict = field_mapper(item)
                elif isinstance(item, dict):
                    # Already a dictionary
                    row_dict = item
                elif hasattr(item, "to_csv_dict"):
                    # Implements CSVSerializable protocol
                    row_dict = item.to_csv_dict()
                elif hasattr(item, "__dict__"):
                    # Object with attributes - use as dictionary
                    row_dict = {k: str(v) for k, v in item.__dict__.items()}
                elif hasattr(item, "_asdict"):
                    # NamedTuple
                    row_dict = item._asdict()
                else:
                    # Try to convert to string representation
                    row_dict = {"value": str(item)}

                # Ensure all values are strings for CSV compatibility
                csv_data.append({k: str(v) if v is not None else "" for k, v in row_dict.items()})

            except Exception as e:
                print(f"Warning: Could not convert data item to CSV: {e}")
                continue

        return csv_data

    def _write_console_csv(self, csv_data: List[Dict[str, Any]]) -> None:
        """Write CSV data to console for debugging/verification."""
        print("\n" + "=" * 60)
        print("CSV Data Preview (console output):")
        print("=" * 60)

        # Show header
        if self.fieldnames:
            print(" | ".join(f"{field[:15]:15}" for field in self.fieldnames[:5]))
            print("-" * 80)

        # Show first few rows
        for i, row in enumerate(csv_data[:10]):  # Limit to 10 rows
            values = []
            fields_to_show = list(self.fieldnames or row.keys())[:5]  # Limit to 5 columns
            for field in fields_to_show:
                value = str(row.get(field, ""))[:15]  # Truncate long values
                values.append(f"{value:15}")
            print(" | ".join(values))

        if len(csv_data) > 10:
            print(f"... and {len(csv_data) - 10} more rows")
        print("=" * 60 + "\n")

    def append_data(
        self,
        data: List[Union[Dict[str, Any], CSVSerializable, Any]],
        field_mapper: Optional[Callable[[Any], Dict[str, Any]]] = None,
    ) -> None:
        """
        Append data to existing CSV file.

        Args:
            data: List of data objects to append
            field_mapper: Optional function to convert objects to dictionaries
        """
        if not data:
            return

        csv_data = self._prepare_data(data, field_mapper)

        if not csv_data:
            return

        # If file doesn't exist, write normally
        if not os.path.exists(self.output_file):
            self.write_data(data, field_mapper)
            return

        # Append to existing file
        try:
            with open(self.output_file, "a", newline="", encoding=self.encoding) as csvfile:
                # Use existing fieldnames or auto-detect
                if self.fieldnames is None:
                    self.fieldnames = list(csv_data[0].keys())

                writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)

                # Write data rows (no header for append)
                for row_data in csv_data:
                    filtered_row = {field: row_data.get(field, "") for field in self.fieldnames}
                    writer.writerow(filtered_row)

            print(f"✅ Appended {len(csv_data)} records to: {self.output_file}")

        except Exception as e:
            raise Exception(f"Failed to append to CSV file: {e}")


def create_csv_writer(
    output_file: str,
    data_sample: Optional[Any] = None,
    custom_fields: Optional[List[str]] = None,
    console_output: bool = False,
) -> CSVWriter:
    """
    Create a CSV writer with auto-detected or custom field configuration.

    Args:
        output_file: Path to output CSV file
        data_sample: Sample data object to auto-detect fields from
        custom_fields: Explicit list of field names
        console_output: Whether to also output to console

    Returns:
        Configured CSVWriter instance
    """
    fieldnames = None

    if custom_fields:
        fieldnames = custom_fields
    elif data_sample:
        # Try to auto-detect fields from sample
        if isinstance(data_sample, dict):
            fieldnames = list(data_sample.keys())
        elif hasattr(data_sample, "to_csv_dict"):
            fieldnames = list(data_sample.to_csv_dict().keys())
        elif hasattr(data_sample, "__dict__"):
            fieldnames = list(data_sample.__dict__.keys())
        elif hasattr(data_sample, "_asdict"):
            fieldnames = list(data_sample._asdict().keys())

    return CSVWriter(output_file=output_file, fieldnames=fieldnames, console_output=console_output)
