#!/usr/bin/env python3
"""
Expand date ranges in holiday CSV/Markdown files to one row per day.

Usage: python3 expand_date_ranges.py <input_file> [output_csv]
       python3 expand_date_ranges.py --all [directory]

Input can be:
  - CSV file (*.csv)
  - Markdown file with table (*.md)

Output is always CSV format, with:
  - All tables processed (for markdown files)
  - Date ranges expanded to individual days
  - Dates normalized to consistent format
  - Duplicates removed (same holiday + date)
  - Results sorted chronologically

Testing:
  Run tests with: ./run_tests.sh
  See test_expand_date_ranges.py for 25 comprehensive tests
"""

import csv
import sys
from datetime import datetime, timedelta
from pathlib import Path


def parse_date_range(date_str):  # type: ignore[no-untyped-def]
    """
    Parse date ranges like:
    - "Jun 30 – Jul 3 2025" (cross-month range)
    - "Jun 30 – Jul 3, 2025" (cross-month range with comma)
    - "July 6–10 2026" (same month range)
    - "Dec 28–31 2026" (same month range, abbreviated)
    Returns (start_date, end_date) as datetime objects, or None if not a range
    """
    # Remove commas from date string for easier parsing
    date_str = date_str.replace(",", "")

    # Check if it's a date range
    if "–" not in date_str and " - " not in date_str and "-" not in date_str:
        return None

    # Normalize separators (replace en-dash with hyphen)
    date_str = date_str.replace("–", "-").replace(" - ", "-")

    # Split on the dash
    parts = date_str.split("-")
    if len(parts) != 2:
        return None

    start_part = parts[0].strip()
    end_part = parts[1].strip()

    # Case 1: "July 6-10 2026" or "Dec 28-31 2026" (same month, day range)
    # start_part will be like "July 6" or "Dec 28"
    # end_part will be like "10 2026" or "31 2026"
    start_words = start_part.split()
    end_words = end_part.split()

    if len(start_words) == 2 and len(end_words) == 2:
        # Format: "Month Day-Day Year"
        month = start_words[0]
        start_day = start_words[1]
        end_day = end_words[0]
        year = end_words[1]

        # Try abbreviated month format
        try:
            start_date = datetime.strptime(f"{month} {start_day} {year}", "%b %d %Y")
            end_date = datetime.strptime(f"{month} {end_day} {year}", "%b %d %Y")
            return (start_date, end_date)
        except ValueError:
            pass

        # Try full month format
        try:
            start_date = datetime.strptime(f"{month} {start_day} {year}", "%B %d %Y")
            end_date = datetime.strptime(f"{month} {end_day} {year}", "%B %d %Y")
            return (start_date, end_date)
        except ValueError:
            pass

    # Case 2: "Jun 30 - Jul 3 2025" (cross-month range)
    # end_part should have at least 3 words: "Jul 3 2025"
    if len(end_words) >= 3:
        year = end_words[-1]

        # Build full date strings
        start_full = f"{start_part} {year}"
        end_full = end_part

        # Try abbreviated month format
        try:
            start_date = datetime.strptime(start_full, "%b %d %Y")
            end_date = datetime.strptime(end_full, "%b %d %Y")
            return (start_date, end_date)
        except ValueError:
            pass

        # Try full month format
        try:
            start_date = datetime.strptime(start_full, "%B %d %Y")
            end_date = datetime.strptime(end_full, "%B %d %Y")
            return (start_date, end_date)
        except ValueError:
            pass

    return None


def parse_markdown_table(file_path):  # type: ignore[no-untyped-def]
    """
    Parse all markdown tables and return header and combined rows with region.
    Extracts region from H1 heading (# Region Name) preceding each table.
    Expected format:
    # Region Name

    | Holiday | Date | Day of the Week |
    |---------|------|-----------------|
    | ...     | ...  | ...             |
    """
    with open(file_path, "r") as f:
        lines = f.readlines()

    # Find all tables with their regions
    all_rows = []
    header = None
    table_lines = []
    in_table = False
    current_region = "Unknown"

    for line in lines:
        stripped = line.strip()

        # Check for H1 heading (region)
        if stripped.startswith("# ") and not stripped.startswith("##"):
            current_region = stripped[2:].strip()
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            if not in_table:
                in_table = True
            table_lines.append(stripped)
        elif in_table and not stripped.startswith("|"):
            # End of current table, process it
            if len(table_lines) >= 2:
                # Parse header (first line) if we haven't yet
                if header is None:
                    header_line = table_lines[0]
                    header = [cell.strip() for cell in header_line.split("|")[1:-1]]

                # Parse data rows (skip header and separator)
                for table_line in table_lines[2:]:
                    cells = [cell.strip() for cell in table_line.split("|")[1:-1]]
                    if cells and any(cell for cell in cells):
                        # Add region as first column
                        all_rows.append([current_region] + cells)

            # Reset for next table
            table_lines = []
            in_table = False

    # Process last table if file ends with a table
    if in_table and len(table_lines) >= 2:
        if header is None:
            header_line = table_lines[0]
            header = [cell.strip() for cell in header_line.split("|")[1:-1]]

        for table_line in table_lines[2:]:
            cells = [cell.strip() for cell in table_line.split("|")[1:-1]]
            if cells and any(cell for cell in cells):
                # Add region as first column
                all_rows.append([current_region] + cells)

    if not header or not all_rows:
        raise ValueError("No valid markdown table found in file")

    # Add Region as first column in header
    header = ["Region"] + header

    return header, all_rows


def read_input_file(input_file):  # type: ignore[no-untyped-def]
    """
    Read input file (CSV or Markdown) and return header and rows.
    """
    file_path = Path(input_file)

    if file_path.suffix.lower() == ".md":
        return parse_markdown_table(input_file)
    else:
        # Assume CSV
        with open(input_file, "r") as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)
        return header, rows


def parse_date_for_sorting(date_str):  # type: ignore[no-untyped-def]
    """
    Parse a date string to datetime object for sorting.
    Handles various formats like "January 1, 2025", "January 1 2025", etc.
    """
    # Remove commas
    date_str_clean = date_str.replace(",", "").strip()

    # Try different date formats
    formats = [
        "%B %d %Y",  # "January 1 2025"
        "%b %d %Y",  # "Jan 1 2025"
        "%B %-d %Y",  # "January 1 2025" (no leading zero)
        "%b %-d %Y",  # "Jan 1 2025" (no leading zero)
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str_clean, fmt)
        except ValueError:
            continue

    # If all else fails, return a far future date so it sorts last
    return datetime(9999, 12, 31)


def expand_csv_dates(input_file, output_file=None):  # type: ignore[no-untyped-def]
    """
    Expand date ranges in CSV/Markdown to individual rows.
    Always outputs CSV format, sorted by date ascending.
    """
    if output_file is None:
        # Generate output filename based on input
        input_path = Path(input_file)
        if input_path.suffix.lower() == ".md":
            output_file = input_path.with_suffix(".csv")
        else:
            output_file = input_file

    # Read input file (CSV or Markdown)
    header, rows = read_input_file(input_file)

    # Process rows
    expanded_rows = []

    for row in rows:
        if not row or len(row) < 3:  # Need at least Region, Holiday, Date
            continue

        region = row[0]
        holiday = row[1]
        date_str = row[2]
        row[3] if len(row) > 3 else ""

        # Try to parse as date range
        date_range = parse_date_range(date_str)

        if date_range:
            start_date, end_date = date_range

            # Expand the range
            current_date = start_date
            while current_date <= end_date:
                # Format: "January 1 2025" without leading zero
                formatted_date = current_date.strftime("%B %-d %Y")
                day_name = current_date.strftime("%A")
                expanded_rows.append([region, holiday, formatted_date, day_name])
                current_date += timedelta(days=1)
        else:
            # Not a range - parse and reformat to normalize
            parsed_date = parse_date_for_sorting(date_str)
            if parsed_date.year != 9999:  # Valid date
                formatted_date = parsed_date.strftime("%B %-d %Y")
                day_name = parsed_date.strftime("%A")
                expanded_rows.append([region, holiday, formatted_date, day_name])
            else:
                # Couldn't parse, keep original
                expanded_rows.append(row)

    # Remove duplicates based on (region, holiday, normalized_date) combination
    # Normalize dates to a standard format for comparison
    seen = set()
    unique_rows = []
    for row in expanded_rows:
        region = row[0]
        holiday = row[1]
        date_str = row[2]

        # Parse and normalize the date to YYYY-MM-DD for comparison
        parsed_date = parse_date_for_sorting(date_str)
        if parsed_date.year != 9999:  # Valid date
            normalized_date = parsed_date.strftime("%Y-%m-%d")
        else:
            normalized_date = date_str  # Couldn't parse, use as-is

        key = (region, holiday, normalized_date)  # (region, holiday, normalized_date)
        if key not in seen:
            seen.add(key)
            unique_rows.append(row)

    # Sort by date (column index 2)
    unique_rows.sort(key=lambda row: parse_date_for_sorting(row[2]))

    # Write output CSV
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(unique_rows)

    print(f"✓ Processed {input_file}")
    print(f"  Input rows: {len(rows)}")
    print(f"  Expanded rows: {len(expanded_rows)}")
    print(f"  Output rows (after deduplication): {len(unique_rows)}")
    if output_file == input_file:
        print(f"  File updated in place")
    else:
        print(f"  Output written to: {output_file}")


def process_directory(directory: str) -> None:
    """
    Process all *.csv and *.md files in the specified directory.
    """
    target_dir = Path(directory)
    if not target_dir.is_dir():
        print(f"Error: Directory '{directory}' not found")
        sys.exit(1)

    # Find all matching files
    csv_files = list(target_dir.glob("*.csv"))
    md_files = list(target_dir.glob("*.md"))
    all_files = csv_files + md_files

    if not all_files:
        print(f"No *.csv or *.md files found in {directory}")
        sys.exit(1)

    print(f"Processing all CSV and MD files in {directory}...")
    for file_path in all_files:
        print(f"\n✓ Processing: {file_path}")
        try:
            expand_csv_dates(str(file_path))
        except Exception as e:
            print(f"  Error processing {file_path}: {e}")
            import traceback

            traceback.print_exc()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 expand_date_ranges.py <input_file> [output_csv]")
        print("       python3 expand_date_ranges.py --all [directory]")
        print("\nInput formats:")
        print("  - CSV file (*.csv)")
        print("  - Markdown file with table (*.md)")
        print("\nOutput is always CSV format.")
        print("\nExamples:")
        print("  python3 expand_date_ranges.py 2025_holidays_usa.csv")
        print("  python3 expand_date_ranges.py 2025_holidays.md")
        print("  python3 expand_date_ranges.py 2025_holidays.md 2025_holidays_expanded.csv")
        print("  python3 expand_date_ranges.py --all")
        print("  python3 expand_date_ranges.py --all ./holidays/")
        sys.exit(1)

    # Check for --all flag
    if sys.argv[1] == "--all":
        directory = sys.argv[2] if len(sys.argv) > 2 else "."
        process_directory(directory)
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        expand_csv_dates(input_file, output_file)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
