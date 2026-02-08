"""
CSV Manager for LDAP batch processing operations.

This module provides CSV reading and writing functionality specifically designed
for the find_manager.sh batch processing workflow, handling name inputs and
manager hierarchy results.
"""

import csv
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Union


class CSVManager:
    """
    CSV manager for LDAP batch processing operations.

    Handles reading employee names from input CSV files and writing
    manager hierarchy results to output CSV files with proper escaping
    and validation.
    """

    def __init__(self, encoding: str = "utf-8"):
        """
        Initialize CSV Manager.

        Args:
            encoding: File encoding (default: utf-8)
        """
        self.encoding = encoding

    def read_manager_data_from_csv(self, file_path: Union[str, Path]) -> List[Tuple[str, str]]:
        """
        Read CSV file with Manager and ManagerUserName columns.

        Extracts both Manager (display name) and ManagerUserName columns
        for username-based LDAP searches. Falls back to display name only
        if ManagerUserName column is not available.

        Args:
            file_path: Path to input CSV file

        Returns:
            List of tuples (manager_display_name, manager_username)
            If username not available, username will be empty string

        Raises:
            FileNotFoundError: If input file doesn't exist
            PermissionError: If input file isn't readable
            ValueError: If no valid data found in file
        """
        file_path = Path(file_path)

        # Validate file exists and is readable
        if not file_path.exists():
            raise FileNotFoundError(f"Input file does not exist: {file_path}")

        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"Input file is not readable: {file_path}")

        manager_data = []

        with open(file_path, "r", encoding=self.encoding, newline="") as csvfile:
            # Use csv.Sniffer to detect dialect
            try:
                sample = csvfile.read(1024)
                csvfile.seek(0)
                dialect = csv.Sniffer().sniff(sample)
                reader = csv.DictReader(csvfile, dialect=dialect)
            except csv.Error:
                # Fallback to default dialect
                csvfile.seek(0)
                reader = csv.DictReader(csvfile)

            # Check if required columns exist
            if reader.fieldnames:
                has_manager = any(col.lower().strip() in ["manager"] for col in reader.fieldnames)
                any(col.lower().strip() in ["managerusername"] for col in reader.fieldnames)

                if not has_manager:
                    raise ValueError("CSV file must contain 'Manager' column")

                # Find actual column names (case-insensitive)
                manager_col = None
                username_col = None

                for col in reader.fieldnames:
                    if col.lower().strip() == "manager":
                        manager_col = col
                    elif col.lower().strip() == "managerusername":
                        username_col = col

                # Process rows
                for row in reader:
                    if not row:  # Skip empty rows
                        continue

                    manager_name = row.get(manager_col, "").strip() if manager_col else ""
                    manager_username = row.get(username_col, "").strip() if username_col else ""

                    # Skip rows with empty manager name
                    if not manager_name:
                        continue

                    manager_data.append((manager_name, manager_username))
            else:
                raise ValueError("Could not parse CSV headers")

        if not manager_data:
            raise ValueError(f"No valid manager data found in input file: {file_path}")

        return manager_data

    def write_manager_results_csv(
        self,
        file_path: Union[str, Path],
        results: Dict[Tuple[str, str], Tuple[str, str]],
        input_order: List[Tuple[str, str]],
    ) -> None:
        """
        Write CSV output with 4 columns as specified in username_plan.md.

        Output format: Manager,ManagerUserName,ResultManager,ResultManagerUserName

        Args:
            file_path: Path to output CSV file
            results: Dictionary mapping input (manager_name, manager_username) tuples
                    to result (result_manager_name, result_manager_username) tuples
            input_order: List maintaining original input order

        Raises:
            PermissionError: If output file cannot be written
        """
        file_path = Path(file_path)

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Validate we can write to the file location
        try:
            with open(file_path, "w", encoding=self.encoding, newline="") as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)

                # Write header as specified in username_plan.md
                writer.writerow(
                    [
                        "Manager",
                        "ManagerUserName",
                        "ResultManager",
                        "ResultManagerUserName",
                    ]
                )

                # Write results in input order
                for input_manager, input_username in input_order:
                    result = results.get((input_manager, input_username), ("ERROR", ""))
                    result_manager, result_username = result

                    writer.writerow(
                        [
                            input_manager,  # Manager (input display name)
                            input_username,  # ManagerUserName (input username)
                            result_manager,
                            # ResultManager (found manager display name)
                            result_username,
                            # ResultManagerUserName (found manager username)
                        ]
                    )

        except PermissionError:
            raise PermissionError(f"Cannot write to output file: {file_path}")

    def csv_escape(self, field: str) -> str:
        """
        Escape CSV field if necessary.

        Fields containing commas, double quotes, or newlines are wrapped
        in quotes with internal quotes doubled according to CSV standard.

        Args:
            field: String field to potentially escape

        Returns:
            Escaped field string ready for CSV output
        """
        # Check if field needs escaping
        if "," in field or '"' in field or "\n" in field or "\r" in field:
            # Escape internal double quotes by doubling them
            escaped_field = field.replace('"', '""')
            return f'"{escaped_field}"'

        return field

    def detect_header(self, first_line: str) -> bool:
        """
        Detect if first line appears to be a CSV header.

        Uses pattern matching to identify common header formats
        for employee name columns.

        Args:
            first_line: First line of CSV file

        Returns:
            True if line appears to be a header, False otherwise
        """
        # Split by comma and get first field
        first_field = first_line.split(",")[0].strip().strip('"').lower()

        header_patterns = [
            r"^name$",
            r"^employee.*name$",
            r"^full.*name$",
            r"^person.*name$",
            r"^input$",
            r"^employee$",
            r"^first.*name$",
            r"^display.*name$",
            r"^manager$",
        ]

        return any(re.match(pattern, first_field) for pattern in header_patterns)

    def validate_csv_format(self, file_path: Union[str, Path]) -> Tuple[bool, str]:
        """
        Validate CSV file format and readability.

        Performs basic validation checks on CSV structure and content.

        Args:
            file_path: Path to CSV file to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        file_path = Path(file_path)

        try:
            # Check file exists and is readable
            if not file_path.exists():
                return False, f"File does not exist: {file_path}"

            if not os.access(file_path, os.R_OK):
                return False, f"File is not readable: {file_path}"

            # Check file size (warn if empty or very large)
            file_size = file_path.stat().st_size
            if file_size == 0:
                return False, "File is empty"

            if file_size > 50 * 1024 * 1024:  # 50MB limit
                return (
                    False,
                    f"File too large ({
                        file_size /
                        1024 /
                        1024:.1f}MB). Maximum 50MB supported.",
                )

            # Try to read a few lines to validate CSV format
            with open(file_path, "r", encoding=self.encoding) as file:
                try:
                    reader = csv.reader(file)
                    lines_read = 0
                    for row in reader:
                        lines_read += 1
                        if lines_read >= 5:  # Sample first 5 lines
                            break

                        # Check if row has at least one field
                        if not row:
                            continue

                except csv.Error as e:
                    return False, f"CSV format error: {e}"

            return True, "Valid CSV format"

        except UnicodeDecodeError:
            return False, f"File encoding error. Expected {self.encoding} encoding."
        except Exception as e:
            return False, f"Validation error: {e}"

    def get_file_stats(self, file_path: Union[str, Path]) -> Dict[str, Union[int, float, str, bool]]:
        """
        Get basic statistics about CSV file.

        Provides information about file size, line count, and estimated
        processing time for batch operations.

        Args:
            file_path: Path to CSV file

        Returns:
            Dictionary with file statistics

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File does not exist: {file_path}")

        stats: Dict[str, Union[int, float, str, bool]] = {
            "file_size_bytes": file_path.stat().st_size,
            "file_size_mb": round(file_path.stat().st_size / 1024 / 1024, 2),
            "line_count": 0,
            "estimated_names": 0,
            "has_header": False,
        }

        # Count lines and detect header
        with open(file_path, "r", encoding=self.encoding) as file:
            first_line = True
            for line_num, line in enumerate(file, 1):
                if line.strip():  # Only count non-empty lines
                    if first_line:
                        stats["has_header"] = self.detect_header(line)
                        first_line = False
                    stats["line_count"] = line_num

            # Estimate number of names (subtract 1 for header if detected)
            line_count = stats["line_count"]
            has_header = stats["has_header"]
            assert isinstance(line_count, int)
            assert isinstance(has_header, bool)
            stats["estimated_names"] = max(0, line_count - (1 if has_header else 0))

        # Estimate processing time (rough approximation: 1-2 seconds per name)
        estimated_names = stats["estimated_names"]
        assert isinstance(estimated_names, int)
        if estimated_names > 0:
            min_time = estimated_names * 1
            max_time = estimated_names * 2
            stats["estimated_processing_time"] = f"{min_time}-{max_time} seconds"
        else:
            stats["estimated_processing_time"] = "0 seconds"

        return stats
