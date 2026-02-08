#!/usr/bin/env python3
"""
Test cases for expand_date_ranges.py
Tests multi-table markdown parsing, date normalization, and deduplication.

Run tests:
    python3 -m unittest test_expand_date_ranges -v      # verbose
    python3 -m unittest test_expand_date_ranges         # normal
    python3 -m unittest test_expand_date_ranges -q      # quiet

Test Coverage (25 tests):
    1. Multi-table markdown parsing (TestMarkdownParsing - 3 tests)
       - Single table parsing
       - Multiple tables in one file
       - Table at end of file without trailing newline

    2. Date range parsing (TestDateRangeParsing - 5 tests)
       - Cross-month ranges with/without commas
       - Same-month ranges (abbreviated and full month names)
       - Single dates (not ranges)

    3. Date normalization (TestDateNormalization - 4 tests)
       - Dates with commas vs. without
       - Abbreviated vs. full month names
       - Proper chronological sorting

    4. Deduplication (TestDeduplication - 3 tests)
       - Duplicate dates with different format strings
       - Different holidays on same date (both kept)
       - Deduplication across multiple tables

    5. Date range expansion (TestDateRangeExpansion - 2 tests)
       - Range expansion to individual dates
       - Overlapping ranges with deduplication

    6. Edge cases (TestEdgeCases - 6 tests)
       - Same holiday name on different dates
       - Cross-year date handling
       - En-dash vs hyphen in date ranges
       - Date ranges with no spaces around dash
       - Multiple consecutive entries with same holiday name
       - Mixed date formats within same table

    7. Sorting (TestSorting - 1 test)
       - Output sorted in chronological order

    8. Integration (TestIntegration - 1 test)
       - Realistic multi-region holiday data
       - All features working together
"""

import os
import tempfile
import unittest

from expand_date_ranges import (
    expand_csv_dates,
    parse_date_for_sorting,
    parse_date_range,
    parse_markdown_table,
)


class TestMarkdownParsing(unittest.TestCase):
    """Test parsing of multiple markdown tables."""

    def test_single_table(self) -> None:
        """Test parsing a single markdown table."""
        content = """
# United States

| Holiday | Date | Day of the Week |
|---------|------|-----------------|
| New Year | January 1, 2025 | Wednesday |
| MLK Day | January 20, 2025 | Monday |
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_file = f.name

        try:
            header, rows = parse_markdown_table(temp_file)
            self.assertEqual(header, ["Region", "Holiday", "Date", "Day of the Week"])
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0][0], "United States")  # Region
            self.assertEqual(rows[0][1], "New Year")  # Holiday
            self.assertEqual(rows[1][0], "United States")  # Region
            self.assertEqual(rows[1][1], "MLK Day")  # Holiday
        finally:
            os.unlink(temp_file)

    def test_multiple_tables(self) -> None:
        """Test parsing multiple markdown tables from one file."""
        content = """
# USA Holidays

| Holiday | Date | Day of the Week |
|---------|------|-----------------|
| New Year | January 1, 2025 | Wednesday |
| MLK Day | January 20, 2025 | Monday |

Some text between tables.

# India Holidays

| Holiday | Date | Day of the Week |
|---------|------|-----------------|
| Diwali | October 20, 2025 | Monday |
| Gandhi Jayanthi | October 2, 2025 | Thursday |
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_file = f.name

        try:
            header, rows = parse_markdown_table(temp_file)
            self.assertEqual(header, ["Region", "Holiday", "Date", "Day of the Week"])
            # Should have all 4 rows from both tables
            self.assertEqual(len(rows), 4)
            # Check regions
            regions = [row[0] for row in rows]
            self.assertEqual(regions.count("USA Holidays"), 2)
            self.assertEqual(regions.count("India Holidays"), 2)
            # Check holiday names (now in column 1)
            holiday_names = [row[1] for row in rows]
            self.assertIn("New Year", holiday_names)
            self.assertIn("MLK Day", holiday_names)
            self.assertIn("Diwali", holiday_names)
            self.assertIn("Gandhi Jayanthi", holiday_names)
        finally:
            os.unlink(temp_file)

    def test_table_at_end_of_file(self) -> None:
        """Test parsing when table is at the end of file (no newline after)."""
        content = """
# Holidays

| Holiday | Date | Day of the Week |
|---------|------|-----------------|
| New Year | January 1, 2025 | Wednesday |"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_file = f.name

        try:
            header, rows = parse_markdown_table(temp_file)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][0], "Holidays")  # Region
            self.assertEqual(rows[0][1], "New Year")  # Holiday
        finally:
            os.unlink(temp_file)


class TestDateRangeParsing(unittest.TestCase):
    """Test parsing of date ranges in various formats."""

    def test_cross_month_range_with_comma(self) -> None:
        """Test parsing cross-month range like 'Jun 30 – Jul 3, 2025'."""
        result = parse_date_range("Jun 30 – Jul 3, 2025")
        self.assertIsNotNone(result)
        start, end = result
        self.assertEqual(start.month, 6)
        self.assertEqual(start.day, 30)
        self.assertEqual(end.month, 7)
        self.assertEqual(end.day, 3)
        self.assertEqual(start.year, 2025)

    def test_cross_month_range_without_comma(self) -> None:
        """Test parsing cross-month range like 'Jun 30 – Jul 3 2025'."""
        result = parse_date_range("Jun 30 – Jul 3 2025")
        self.assertIsNotNone(result)
        start, end = result
        self.assertEqual(start.month, 6)
        self.assertEqual(end.month, 7)

    def test_same_month_range_abbreviated(self) -> None:
        """Test parsing same-month range like 'Dec 28-31 2026'."""
        result = parse_date_range("Dec 28-31 2026")
        self.assertIsNotNone(result)
        start, end = result
        self.assertEqual(start.month, 12)
        self.assertEqual(start.day, 28)
        self.assertEqual(end.month, 12)
        self.assertEqual(end.day, 31)

    def test_same_month_range_full_name(self) -> None:
        """Test parsing same-month range like 'July 6-10 2026'."""
        result = parse_date_range("July 6-10 2026")
        self.assertIsNotNone(result)
        start, end = result
        self.assertEqual(start.month, 7)
        self.assertEqual(start.day, 6)
        self.assertEqual(end.day, 10)

    def test_single_date_not_a_range(self) -> None:
        """Test that single dates are not parsed as ranges."""
        result = parse_date_range("January 1, 2025")
        self.assertIsNone(result)

        result = parse_date_range("Dec 25 2025")
        self.assertIsNone(result)


class TestDateNormalization(unittest.TestCase):
    """Test date parsing and normalization."""

    def test_parse_date_with_comma(self) -> None:
        """Test parsing dates with commas like 'January 1, 2025'."""
        result = parse_date_for_sorting("January 1, 2025")
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 1)

    def test_parse_date_without_comma(self) -> None:
        """Test parsing dates without commas like 'January 1 2025'."""
        result = parse_date_for_sorting("January 1 2025")
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 1)

    def test_parse_abbreviated_month(self) -> None:
        """Test parsing abbreviated month like 'Dec 25 2025'."""
        result = parse_date_for_sorting("Dec 25 2025")
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 12)
        self.assertEqual(result.day, 25)

    def test_dates_sort_correctly(self) -> None:
        """Test that dates sort in chronological order."""
        dates = [
            "December 31, 2025",
            "January 1, 2025",
            "July 4 2025",
            "March 15, 2025",
        ]
        sorted_dates = sorted(dates, key=parse_date_for_sorting)
        self.assertEqual(sorted_dates[0], "January 1, 2025")
        self.assertEqual(sorted_dates[1], "March 15, 2025")
        self.assertEqual(sorted_dates[2], "July 4 2025")
        self.assertEqual(sorted_dates[3], "December 31, 2025")


class TestDeduplication(unittest.TestCase):
    """Test deduplication with normalized dates."""

    def test_duplicate_dates_with_different_formats(self) -> None:
        """Test that duplicate dates with different formats are deduplicated."""
        content = """
# Holidays

| Holiday | Date | Day of the Week |
|---------|------|-----------------|
| New Year | January 1, 2025 | Wednesday |
| New Year | January 1 2025 | Wednesday |
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_file = f.name

        output_file = temp_file.replace(".md", ".csv")

        try:
            expand_csv_dates(temp_file, output_file)

            # Read the output
            with open(output_file, "r") as f:
                lines = f.readlines()

            # Should have header + 1 data row (duplicate removed)
            self.assertEqual(len(lines), 2)
            self.assertIn("New Year", lines[1])
        finally:
            os.unlink(temp_file)
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_keep_different_holidays_same_date(self) -> None:
        """Test that different holidays on the same date are both kept."""
        content = """
# Holidays

| Holiday | Date | Day of the Week |
|---------|------|-----------------|
| Christmas | December 25, 2025 | Thursday |
| Company Shutdown | December 25 2025 | Thursday |
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_file = f.name

        output_file = temp_file.replace(".md", ".csv")

        try:
            expand_csv_dates(temp_file, output_file)

            # Read the output
            with open(output_file, "r") as f:
                lines = f.readlines()

            # Should have header + 2 data rows (both kept)
            self.assertEqual(len(lines), 3)
            content = "".join(lines)
            self.assertIn("Christmas", content)
            self.assertIn("Company Shutdown", content)
        finally:
            os.unlink(temp_file)
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_deduplication_across_tables(self) -> None:
        """Test deduplication works across multiple tables."""
        content = """
# USA Holidays

| Holiday | Date | Day of the Week |
|---------|------|-----------------|
| Independence Day | July 4, 2025 | Friday |
| Shutdown | December 26, 2025 | Friday |

# India Holidays

| Holiday | Date | Day of the Week |
|---------|------|-----------------|
| Independence Day | August 15, 2025 | Friday |
| Shutdown | December 26 2025 | Friday |
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_file = f.name

        output_file = temp_file.replace(".md", ".csv")

        try:
            expand_csv_dates(temp_file, output_file)

            # Read the output
            with open(output_file, "r") as f:
                lines = f.readlines()

            # Should have header + 4 rows (with Region column, different regions are kept):
            # - Independence Day (July 4) from USA
            # - Independence Day (August 15) from India
            # - Shutdown (Dec 26) from USA
            # - Shutdown (Dec 26) from India (both kept, different regions)
            self.assertEqual(len(lines), 5)

            # Check content
            content = "".join(lines)
            self.assertIn("July 4", content)
            self.assertIn("August 15", content)
            # Should have TWO December 26 entries (one per region)
            december_count = content.count("December 26")
            self.assertEqual(december_count, 2)
        finally:
            os.unlink(temp_file)
            if os.path.exists(output_file):
                os.unlink(output_file)


class TestDateRangeExpansion(unittest.TestCase):
    """Test expansion of date ranges."""

    def test_expand_date_range(self) -> None:
        """Test that date ranges are expanded to individual dates."""
        content = """
# Holidays

| Holiday | Date | Day of the Week |
|---------|------|-----------------|
| July 4th Break | Jun 30 – Jul 3, 2025 | Mon to Thu |
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_file = f.name

        output_file = temp_file.replace(".md", ".csv")

        try:
            expand_csv_dates(temp_file, output_file)

            # Read the output
            with open(output_file, "r") as f:
                lines = f.readlines()

            # Should have header + 4 data rows (June 30, July 1, 2, 3)
            self.assertEqual(len(lines), 5)
            content = "".join(lines)
            self.assertIn("June 30", content)
            self.assertIn("July 1", content)
            self.assertIn("July 2", content)
            self.assertIn("July 3", content)
        finally:
            os.unlink(temp_file)
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_expand_and_deduplicate_range_with_overlap(self) -> None:
        """Test that overlapping date ranges are properly deduplicated."""
        content = """
# Holidays

| Holiday | Date | Day of the Week |
|---------|------|-----------------|
| Shutdown | December 25, 2025 | Thursday |
| Shutdown | December 26, 2025 | Friday |
| Shutdown | Dec 25–31, 2025 | Thu–Wed |
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_file = f.name

        output_file = temp_file.replace(".md", ".csv")

        try:
            expand_csv_dates(temp_file, output_file)

            # Read the output
            with open(output_file, "r") as f:
                lines = f.readlines()

            # Should have header + 7 rows (Dec 25-31, no duplicates)
            self.assertEqual(len(lines), 8)

            # Verify all dates from 25-31 are present
            content = "".join(lines)
            for day in range(25, 32):
                self.assertIn(f"December {day}", content)

            # Count occurrences - each date should appear exactly once
            for day in range(25, 32):
                count = content.count(f"December {day}")
                self.assertEqual(count, 1, f"December {day} should appear exactly once")
        finally:
            os.unlink(temp_file)
            if os.path.exists(output_file):
                os.unlink(output_file)


class TestSorting(unittest.TestCase):
    """Test that output is sorted by date."""

    def test_output_sorted_by_date(self) -> None:
        """Test that final output is sorted in chronological order."""
        content = """
# Holidays

| Holiday | Date | Day of the Week |
|---------|------|-----------------|
| Christmas | December 25, 2025 | Thursday |
| New Year | January 1, 2025 | Wednesday |
| July 4th | July 4, 2025 | Friday |
| MLK Day | January 20, 2025 | Monday |
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_file = f.name

        output_file = temp_file.replace(".md", ".csv")

        try:
            expand_csv_dates(temp_file, output_file)

            # Read the output
            with open(output_file, "r") as f:
                lines = f.readlines()[1:]  # Skip header

            # Extract dates and verify they're in order
            dates = []
            for line in lines:
                # Extract date (second column)
                parts = line.split(",")
                date_str = parts[1].strip().strip('"')
                dates.append(parse_date_for_sorting(date_str))

            # Verify dates are in ascending order
            for i in range(len(dates) - 1):
                self.assertLessEqual(dates[i], dates[i + 1], f"Dates not in order at position {i}")
        finally:
            os.unlink(temp_file)
            if os.path.exists(output_file):
                os.unlink(output_file)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios."""

    def test_same_holiday_different_dates(self) -> None:
        """Test same holiday name on different dates (both kept)."""
        content = """
# Holidays

| Holiday | Date | Day of the Week |
|---------|------|-----------------|
| Independence Day | July 4, 2025 | Friday |
| Independence Day | August 15, 2025 | Friday |
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_file = f.name

        output_file = temp_file.replace(".md", ".csv")

        try:
            expand_csv_dates(temp_file, output_file)

            # Read the output
            with open(output_file, "r") as f:
                lines = f.readlines()

            # Should have header + 2 rows (both Independence Days kept)
            self.assertEqual(len(lines), 3)
            content = "".join(lines)
            self.assertIn("July 4", content)
            self.assertIn("August 15", content)
            # Count occurrences of Independence Day
            independence_count = content.count("Independence Day")
            self.assertEqual(independence_count, 2)
        finally:
            os.unlink(temp_file)
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_cross_year_dates(self) -> None:
        """Test handling dates that cross calendar years."""
        content = """
# Holidays

| Holiday | Date | Day of the Week |
|---------|------|-----------------|
| New Year's Day | January 1, 2025 | Wednesday |
| Christmas | December 25, 2025 | Thursday |
| New Year's Day | January 1, 2026 | Thursday |
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_file = f.name

        output_file = temp_file.replace(".md", ".csv")

        try:
            expand_csv_dates(temp_file, output_file)

            # Read the output
            with open(output_file, "r") as f:
                lines = f.readlines()

            # Should have header + 3 rows, sorted chronologically
            self.assertEqual(len(lines), 4)
            # First data row should be Jan 1, 2025
            self.assertIn("January 1 2025", lines[1])
            # Second should be Dec 25, 2025
            self.assertIn("December 25 2025", lines[2])
            # Third should be Jan 1, 2026
            self.assertIn("January 1 2026", lines[3])
        finally:
            os.unlink(temp_file)
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_en_dash_vs_hyphen_ranges(self) -> None:
        """Test date ranges with en-dash (–) vs hyphen (-)."""
        content = """
# Holidays

| Holiday | Date | Day of the Week |
|---------|------|-----------------|
| Break A | Jun 30 – Jul 3, 2025 | Mon to Thu |
| Break B | Dec 25-31, 2025 | Thu-Wed |
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_file = f.name

        output_file = temp_file.replace(".md", ".csv")

        try:
            expand_csv_dates(temp_file, output_file)

            # Read the output
            with open(output_file, "r") as f:
                lines = f.readlines()

            # Should expand both ranges: 4 (Jun 30-Jul 3) + 7 (Dec 25-31) = 11 + header
            self.assertEqual(len(lines), 12)
            content = "".join(lines)
            # Verify both ranges expanded
            self.assertIn("June 30", content)
            self.assertIn("July 3", content)
            self.assertIn("December 25", content)
            self.assertIn("December 31", content)
        finally:
            os.unlink(temp_file)
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_multiple_consecutive_same_holiday(self) -> None:
        """Test multiple consecutive entries with same holiday name."""
        content = """
# Holidays

| Holiday | Date | Day of the Week |
|---------|------|-----------------|
| Company Shutdown | December 26, 2025 | Friday |
| Company Shutdown | December 27, 2025 | Saturday |
| Company Shutdown | December 28, 2025 | Sunday |
| Company Shutdown | December 29, 2025 | Monday |
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_file = f.name

        output_file = temp_file.replace(".md", ".csv")

        try:
            expand_csv_dates(temp_file, output_file)

            # Read the output
            with open(output_file, "r") as f:
                lines = f.readlines()

            # Should have header + 4 rows (all kept, no deduplication)
            self.assertEqual(len(lines), 5)
            content = "".join(lines)
            # All should be Company Shutdown
            shutdown_count = content.count("Company Shutdown")
            self.assertEqual(shutdown_count, 4)
        finally:
            os.unlink(temp_file)
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_mixed_date_formats_in_table(self) -> None:
        """Test table with mixed date formats (full month, abbreviated, with/without commas)."""
        content = """
# Holidays

| Holiday | Date | Day of the Week |
|---------|------|-----------------|
| Holiday A | January 1, 2025 | Wednesday |
| Holiday B | Feb 14 2025 | Friday |
| Holiday C | March 17, 2025 | Monday |
| Holiday D | Apr 1 2025 | Tuesday |
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_file = f.name

        output_file = temp_file.replace(".md", ".csv")

        try:
            expand_csv_dates(temp_file, output_file)

            # Read the output
            with open(output_file, "r") as f:
                lines = f.readlines()

            # Should have header + 4 rows, all normalized to same format
            self.assertEqual(len(lines), 5)

            # All dates should be normalized (no commas in output)
            content = "".join(lines)
            self.assertIn("January 1 2025", content)
            self.assertIn("February 14 2025", content)  # Expanded from "Feb"
            self.assertIn("March 17 2025", content)
            self.assertIn("April 1 2025", content)  # Expanded from "Apr"

            # Verify chronological order by checking line order
            jan_line = next(i for i, line in enumerate(lines) if "January" in line)
            feb_line = next(i for i, line in enumerate(lines) if "February" in line)
            mar_line = next(i for i, line in enumerate(lines) if "March" in line)
            apr_line = next(i for i, line in enumerate(lines) if "April" in line)

            self.assertLess(jan_line, feb_line)
            self.assertLess(feb_line, mar_line)
            self.assertLess(mar_line, apr_line)
        finally:
            os.unlink(temp_file)
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_date_range_no_spaces_around_dash(self) -> None:
        """Test date range with no spaces around dash: 'December 25–31, 2025'."""
        result = parse_date_range("December 25–31, 2025")
        self.assertIsNotNone(result)
        start, end = result
        self.assertEqual(start.month, 12)
        self.assertEqual(start.day, 25)
        self.assertEqual(end.month, 12)
        self.assertEqual(end.day, 31)
        self.assertEqual(start.year, 2025)


class TestIntegration(unittest.TestCase):
    """Integration tests with realistic data."""

    def test_realistic_multi_region_holidays(self) -> None:
        """Test with realistic multi-region holiday data."""
        content = """
# United States

| Holiday | Date | Day of the Week |
|---------|------|-----------------|
| New Year's Day | January 1, 2025 | Wednesday |
| July 4th Break | Jun 30 – Jul 3, 2025 | Mon to Thu |
| Independence Day | July 4, 2025 | Friday |
| Christmas Day | December 25, 2025 | Thursday |
| Company Shutdown | December 26, 2025 | Friday |
| Company Shutdown | December 29, 2025 | Monday |

# India

| Holiday | Date | Day of the Week |
|---------|------|-----------------|
| Independence Day | August 15, 2025 | Friday |
| Diwali | October 20, 2025 | Monday |
| Company Shutdown | December 25–31, 2025 | Thursday–Wednesday |
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_file = f.name

        output_file = temp_file.replace(".md", ".csv")

        try:
            expand_csv_dates(temp_file, output_file)

            # Read the output
            with open(output_file, "r") as f:
                lines = f.readlines()

            # Verify we have expected number of rows (with Region column):
            # USA: 1 (New Year) + 4 (July Break) + 1 (July 4) + 1 (Christmas) + 1 (Dec 26) + 1 (Dec 29) = 9
            # India: 1 (Aug 15) + 1 (Diwali) + 7 (Dec 25-31) = 9
            # With regions, different regions are NOT duplicates
            # Both USA and India have Company Shutdown on Dec 26, 29
            # So total: 9 + 9 = 18 data rows + header = 19 lines
            self.assertEqual(len(lines), 19)

            content = "".join(lines)

            # Verify key holidays are present
            self.assertIn("New Year's Day", content)
            self.assertIn("July 4th Break", content)
            self.assertIn("Diwali", content)

            # Verify (region, holiday, date) combinations are unique
            combinations: set[tuple[str, str, str]] = set()
            for line in lines[1:]:  # Skip header
                parts = line.split(",")
                region = parts[0].strip().strip('"')
                holiday = parts[1].strip().strip('"')
                date_str = parts[2].strip().strip('"')
                combo = (region, holiday, date_str)
                # Each (region, holiday, date) combo should be unique
                self.assertNotIn(combo, combinations, f"Duplicate: {combo}")
                combinations.add(combo)
        finally:
            os.unlink(temp_file)
            if os.path.exists(output_file):
                os.unlink(output_file)


if __name__ == "__main__":
    unittest.main()
