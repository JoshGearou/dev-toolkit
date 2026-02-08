"""
Tests for LogWriter class.
"""

import os
import sys
import tempfile
from typing import Any, Dict, NamedTuple

import pytest

# Add src directory to path so shared_libs is importable as a package
src_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, src_root)

from shared_libs.io_utils.log_writer import LogWriter, create_log_writer


class TestLogWriterInit:
    """Tests for LogWriter initialization."""

    def test_default_values(self) -> None:
        """Default configuration values are set correctly."""
        writer = LogWriter("/tmp/test.log")
        assert writer.output_file == "/tmp/test.log"
        assert writer.console_output is False
        assert writer.encoding == "utf-8"
        assert writer.title is None

    def test_custom_values(self) -> None:
        """Custom configuration values are respected."""
        writer = LogWriter(
            output_file="/tmp/custom.log",
            console_output=True,
            encoding="latin-1",
            title="Custom Title",
        )
        assert writer.output_file == "/tmp/custom.log"
        assert writer.console_output is True
        assert writer.encoding == "latin-1"
        assert writer.title == "Custom Title"


class TestLogWriterWriteData:
    """Tests for LogWriter.write_data method."""

    def test_write_dict_data(self) -> None:
        """Write dictionary data to log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.log")
            writer = LogWriter(output_file)

            data = [
                {"name": "Alice", "status": "active"},
                {"name": "Bob", "status": "inactive"},
            ]
            writer.write_data(data, primary_field="name")

            assert os.path.exists(output_file)
            with open(output_file, "r") as f:
                content = f.read()
            assert "Alice" in content
            assert "Bob" in content
            assert "Status:" in content

    def test_write_with_custom_title(self) -> None:
        """Write data with custom title."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.log")
            writer = LogWriter(output_file, title="My Custom Report")

            data = [{"item": "test"}]
            writer.write_data(data)

            with open(output_file, "r") as f:
                content = f.read()
            assert "My Custom Report" in content

    def test_write_empty_data(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Writing empty data prints message and returns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.log")
            writer = LogWriter(output_file)

            writer.write_data([])

            captured = capsys.readouterr()
            assert "No data to write" in captured.out
            assert not os.path.exists(output_file)

    def test_header_contains_metadata(self) -> None:
        """Header contains timestamp and entry count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.log")
            writer = LogWriter(output_file)

            data = [{"a": "1"}, {"a": "2"}, {"a": "3"}]
            writer.write_data(data)

            with open(output_file, "r") as f:
                content = f.read()
            assert "Generated:" in content
            assert "Total Entries: 3" in content

    def test_creates_output_directory(self) -> None:
        """Output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "subdir", "nested", "output.log")
            writer = LogWriter(output_file)

            writer.write_data([{"item": "test"}])

            assert os.path.exists(output_file)


class TestLogWriterPrepareData:
    """Tests for LogWriter._prepare_data method."""

    def test_prepare_dict_data(self) -> None:
        """Dictionaries are passed through."""
        writer = LogWriter("/tmp/test.log")
        data = [{"name": "Alice", "age": 30}]

        result = writer._prepare_data(data)

        assert len(result) == 1
        assert result[0]["name"] == "Alice"
        assert result[0]["age"] == 30

    def test_prepare_object_with_to_log_dict(self):  # type: ignore[no-untyped-def]
        """Objects with to_log_dict method are converted."""

        class MyData:
            def to_log_dict(self) -> Dict[str, Any]:
                return {"field1": "value1"}

        writer = LogWriter("/tmp/test.log")
        data = [MyData()]

        result = writer._prepare_data(data)

        assert len(result) == 1
        assert result[0]["field1"] == "value1"

    def test_prepare_named_tuple(self) -> None:
        """NamedTuples are converted via _asdict."""

        class Record(NamedTuple):
            name: str
            value: int

        writer = LogWriter("/tmp/test.log")
        data = [Record("test", 100)]

        result = writer._prepare_data(data)

        assert len(result) == 1
        assert result[0]["name"] == "test"
        assert result[0]["value"] == 100


class TestLogWriterAppendData:
    """Tests for LogWriter.append_data method."""

    def test_append_to_existing_file(self) -> None:
        """Append data to existing log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.log")
            writer = LogWriter(output_file)

            # Write initial data
            writer.write_data([{"name": "Alice"}], primary_field="name")

            # Append more data
            writer.append_data([{"name": "Bob"}], primary_field="name")

            with open(output_file, "r") as f:
                content = f.read()
            assert "Alice" in content
            assert "Bob" in content
            assert "APPENDED:" in content

    def test_append_to_nonexistent_file(self) -> None:
        """Appending to nonexistent file creates it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "new_output.log")
            writer = LogWriter(output_file)

            writer.append_data([{"name": "Alice"}])

            assert os.path.exists(output_file)


class TestLogWriterConsoleOutput:
    """Tests for LogWriter console output feature."""

    def test_console_output_enabled(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Console output is shown when enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.log")
            writer = LogWriter(output_file, console_output=True)

            writer.write_data([{"name": "Alice"}], primary_field="name")

            captured = capsys.readouterr()
            assert "Log Data Preview" in captured.out


class TestCreateLogWriter:
    """Tests for create_log_writer factory function."""

    def test_default_config(self) -> None:
        """Factory creates writer with default config."""
        writer = create_log_writer("/tmp/test.log")
        assert isinstance(writer, LogWriter)
        assert writer.title is None
        assert writer.console_output is False

    def test_with_title(self) -> None:
        """Factory creates writer with custom title."""
        writer = create_log_writer("/tmp/test.log", title="My Report")
        assert writer.title == "My Report"

    def test_with_console_output(self) -> None:
        """Factory sets console_output option."""
        writer = create_log_writer("/tmp/test.log", console_output=True)
        assert writer.console_output is True
