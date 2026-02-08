"""
Tests for OutputManager class.
"""

import os
import sys
import tempfile

import pytest

# Add src directory to path so shared_libs is importable as a package
src_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, src_root)

from shared_libs.io_utils.csv_writer import CSVWriter
from shared_libs.io_utils.log_writer import LogWriter
from shared_libs.io_utils.output_manager import (
    ConsoleWriter,
    MultiFormatWriter,
    OutputManager,
    create_output_manager,
)


class TestOutputManagerCreateWriter:
    """Tests for OutputManager.create_writer method."""

    def test_create_csv_writer(self) -> None:
        """Create CSV writer."""
        writer = OutputManager.create_writer("csv", "/tmp/test.csv")
        assert isinstance(writer, CSVWriter)
        assert writer.output_file == "/tmp/test.csv"

    def test_create_log_writer(self) -> None:
        """Create log writer."""
        writer = OutputManager.create_writer("log", "/tmp/test.log")
        assert isinstance(writer, LogWriter)
        assert writer.output_file == "/tmp/test.log"

    def test_case_insensitive_format(self) -> None:
        """Format is case-insensitive."""
        writer1 = OutputManager.create_writer("CSV", "/tmp/test.csv")
        writer2 = OutputManager.create_writer("Log", "/tmp/test.log")
        assert isinstance(writer1, CSVWriter)
        assert isinstance(writer2, LogWriter)

    def test_unsupported_format_raises(self) -> None:
        """Unsupported format raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported output format"):
            OutputManager.create_writer("xml", "/tmp/test.xml")

    def test_passes_console_output(self) -> None:
        """Console output option is passed through."""
        writer = OutputManager.create_writer("csv", "/tmp/test.csv", console_output=True)
        assert writer.console_output is True

    def test_passes_csv_kwargs(self) -> None:
        """CSV-specific kwargs are passed through."""
        writer = OutputManager.create_writer("csv", "/tmp/test.csv", fieldnames=["col1", "col2"])
        assert isinstance(writer, CSVWriter)
        assert writer.fieldnames == ["col1", "col2"]

    def test_passes_log_kwargs(self) -> None:
        """Log-specific kwargs are passed through."""
        writer = OutputManager.create_writer("log", "/tmp/test.log", title="My Report")
        assert isinstance(writer, LogWriter)
        assert writer.title == "My Report"


class TestOutputManagerCreateMultiWriter:
    """Tests for OutputManager.create_multi_writer method."""

    def test_creates_multi_format_writer(self) -> None:
        """Creates MultiFormatWriter instance."""
        writer = OutputManager.create_multi_writer(formats=["csv", "log"], base_filename="/tmp/test")
        assert isinstance(writer, MultiFormatWriter)

    def test_multi_writer_has_correct_formats(self) -> None:
        """Multi writer has all requested formats."""
        writer = OutputManager.create_multi_writer(formats=["csv", "log"], base_filename="/tmp/test")
        assert "csv" in writer.writers
        assert "log" in writer.writers


class TestMultiFormatWriter:
    """Tests for MultiFormatWriter class."""

    def test_initialization(self) -> None:
        """MultiFormatWriter initializes correctly."""
        writer = MultiFormatWriter(
            formats=["csv", "log"],
            base_filename="/tmp/test",
            console_output=True,
        )
        assert writer.formats == ["csv", "log"]
        assert writer.base_filename == "/tmp/test"
        assert writer.console_output is True

    def test_creates_writers_for_each_format(self) -> None:
        """Creates a writer for each format."""
        writer = MultiFormatWriter(formats=["csv", "log"], base_filename="/tmp/test")
        assert isinstance(writer.writers["csv"], CSVWriter)
        assert isinstance(writer.writers["log"], LogWriter)

    def test_write_data_to_multiple_formats(self) -> None:
        """Write data to all formats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = os.path.join(tmpdir, "output")
            writer = MultiFormatWriter(formats=["csv", "log"], base_filename=base)

            data = [{"name": "Alice", "value": "123"}]
            writer.write_data(data, primary_field="name")

            assert os.path.exists(f"{base}.csv")
            assert os.path.exists(f"{base}.log")

    def test_get_output_files(self) -> None:
        """get_output_files returns all output paths."""
        writer = MultiFormatWriter(formats=["csv", "log"], base_filename="/tmp/test")
        files = writer.get_output_files()
        assert "/tmp/test.csv" in files
        assert "/tmp/test.log" in files

    def test_write_empty_data(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Writing empty data prints message."""
        writer = MultiFormatWriter(formats=["csv"], base_filename="/tmp/test")
        writer.write_data([])
        captured = capsys.readouterr()
        assert "No data to write" in captured.out


class TestConsoleWriter:
    """Tests for ConsoleWriter class."""

    def test_initialization_default(self) -> None:
        """Default title is set."""
        writer = ConsoleWriter()
        assert writer.title == "Data Processing Results"

    def test_initialization_custom_title(self) -> None:
        """Custom title is respected."""
        writer = ConsoleWriter(title="My Report")
        assert writer.title == "My Report"

    def test_display_summary(self, capsys: pytest.CaptureFixture[str]) -> None:
        """display_summary shows data preview."""
        writer = ConsoleWriter(title="Test Output")
        data = [{"name": "Alice", "value": "123"}]

        writer.display_summary(data, primary_field="name")

        captured = capsys.readouterr()
        assert "Test Output" in captured.out
        assert "Alice" in captured.out
        assert "Total Items: 1" in captured.out

    def test_display_summary_empty(self, capsys: pytest.CaptureFixture[str]) -> None:
        """display_summary handles empty data."""
        writer = ConsoleWriter()
        writer.display_summary([])

        captured = capsys.readouterr()
        assert "No data to display" in captured.out

    def test_display_progress(self, capsys: pytest.CaptureFixture[str]) -> None:
        """display_progress shows progress bar."""
        writer = ConsoleWriter()
        writer.display_progress(5, 10, item_name="file")

        captured = capsys.readouterr()
        assert "50.0%" in captured.out
        assert "5/10" in captured.out

    def test_display_error_summary_no_errors(self, capsys: pytest.CaptureFixture[str]) -> None:
        """display_error_summary shows success when no errors."""
        writer = ConsoleWriter()
        writer.display_error_summary([])

        captured = capsys.readouterr()
        assert "No errors detected" in captured.out

    def test_display_error_summary_with_errors(self, capsys: pytest.CaptureFixture[str]) -> None:
        """display_error_summary shows error list."""
        writer = ConsoleWriter()
        errors = ["Error 1", "Error 2"]
        writer.display_error_summary(errors)

        captured = capsys.readouterr()
        assert "2 error(s) detected" in captured.out
        assert "Error 1" in captured.out
        assert "Error 2" in captured.out


class TestCreateOutputManager:
    """Tests for create_output_manager factory function."""

    def test_creates_csv_writer(self) -> None:
        """Factory creates CSV writer."""
        writer = create_output_manager("csv", "/tmp/test.csv")
        assert isinstance(writer, CSVWriter)

    def test_creates_log_writer(self) -> None:
        """Factory creates log writer."""
        writer = create_output_manager("log", "/tmp/test.log")
        assert isinstance(writer, LogWriter)

    def test_passes_options(self) -> None:
        """Factory passes options through."""
        writer = create_output_manager("csv", "/tmp/test.csv", console_output=True)
        assert writer.console_output is True
