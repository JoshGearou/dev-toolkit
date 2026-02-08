"""
Tests for CSVWriter class.
"""

import os
import sys
import tempfile
from typing import Any, Dict, NamedTuple
from unittest.mock import patch

import pytest

# Add src directory to path so shared_libs is importable as a package
src_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, src_root)

from shared_libs.io_utils.csv_writer import CSVWriter, create_csv_writer


class TestCSVWriterInit:
    """Tests for CSVWriter initialization."""

    def test_default_values(self) -> None:
        """Default configuration values are set correctly."""
        writer = CSVWriter("/tmp/test.csv")
        assert writer.output_file == "/tmp/test.csv"
        assert writer.fieldnames is None
        assert writer.console_output is False
        assert writer.encoding == "utf-8"

    def test_custom_values(self) -> None:
        """Custom configuration values are respected."""
        writer = CSVWriter(
            output_file="/tmp/custom.csv",
            fieldnames=["col1", "col2"],
            console_output=True,
            encoding="latin-1",
        )
        assert writer.output_file == "/tmp/custom.csv"
        assert writer.fieldnames == ["col1", "col2"]
        assert writer.console_output is True
        assert writer.encoding == "latin-1"


class TestCSVWriterWriteData:
    """Tests for CSVWriter.write_data method."""

    def test_write_dict_data(self) -> None:
        """Write dictionary data to CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.csv")
            writer = CSVWriter(output_file)

            data = [
                {"name": "Alice", "age": "30"},
                {"name": "Bob", "age": "25"},
            ]
            writer.write_data(data)

            assert os.path.exists(output_file)
            with open(output_file, "r") as f:
                content = f.read()
            assert "name,age" in content
            assert "Alice,30" in content
            assert "Bob,25" in content

    def test_write_with_custom_fieldnames(self) -> None:
        """Write data with custom fieldnames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.csv")
            writer = CSVWriter(output_file, fieldnames=["name", "age"])

            data = [
                {"name": "Alice", "age": "30", "extra": "ignored"},
            ]
            writer.write_data(data)

            with open(output_file, "r") as f:
                content = f.read()
            assert "name,age" in content
            assert "Alice,30" in content
            assert "extra" not in content
            assert "ignored" not in content

    def test_write_empty_data(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Writing empty data prints message and returns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.csv")
            writer = CSVWriter(output_file)

            writer.write_data([])

            captured = capsys.readouterr()
            assert "No data to write" in captured.out
            assert not os.path.exists(output_file)

    def test_write_with_field_mapper(self) -> None:
        """Write data using custom field mapper function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.csv")
            writer = CSVWriter(output_file)

            data = [("Alice", 30), ("Bob", 25)]

            def mapper(item: tuple) -> Dict[str, Any]:
                return {"name": item[0], "age": str(item[1])}

            writer.write_data(data, field_mapper=mapper)

            with open(output_file, "r") as f:
                content = f.read()
            assert "name,age" in content
            assert "Alice,30" in content

    def test_atomic_write_on_error(self) -> None:
        """Temporary file is cleaned up on error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.csv")
            writer = CSVWriter(output_file)

            with patch("builtins.open", side_effect=IOError("Disk full")):
                with pytest.raises(Exception, match="Failed to write CSV"):
                    writer.write_data([{"name": "Alice"}])

            # Ensure temp file is not left behind
            temp_file = f"{output_file}.tmp"
            assert not os.path.exists(temp_file)

    def test_creates_output_directory(self) -> None:
        """Output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "subdir", "nested", "output.csv")
            writer = CSVWriter(output_file)

            writer.write_data([{"name": "Alice"}])

            assert os.path.exists(output_file)


class TestCSVWriterPrepareData:
    """Tests for CSVWriter._prepare_data method."""

    def test_prepare_dict_data(self) -> None:
        """Dictionaries are passed through."""
        writer = CSVWriter("/tmp/test.csv")
        data = [{"name": "Alice", "age": 30}]

        result = writer._prepare_data(data)

        assert len(result) == 1
        assert result[0]["name"] == "Alice"
        assert result[0]["age"] == "30"  # Converted to string

    def test_prepare_object_with_to_csv_dict(self) -> None:
        """Objects with to_csv_dict method are converted."""

        class MyData:
            def to_csv_dict(self) -> Dict[str, Any]:
                return {"field1": "value1"}

        writer = CSVWriter("/tmp/test.csv")
        data = [MyData()]

        result = writer._prepare_data(data)

        assert len(result) == 1
        assert result[0]["field1"] == "value1"

    def test_prepare_object_with_dict(self) -> None:
        """Objects with __dict__ are converted."""

        class SimpleObject:
            def __init__(self) -> None:
                self.name = "test"
                self.value = 123

        writer = CSVWriter("/tmp/test.csv")
        data = [SimpleObject()]

        result = writer._prepare_data(data)

        assert len(result) == 1
        assert result[0]["name"] == "test"
        assert result[0]["value"] == "123"

    def test_prepare_named_tuple(self) -> None:
        """NamedTuples are converted via _asdict."""

        class Record(NamedTuple):
            name: str
            value: int

        writer = CSVWriter("/tmp/test.csv")
        data = [Record("test", 100)]

        result = writer._prepare_data(data)

        assert len(result) == 1
        assert result[0]["name"] == "test"
        assert result[0]["value"] == "100"

    def test_prepare_primitive_value(self) -> None:
        """Primitive values are wrapped in 'value' key."""
        writer = CSVWriter("/tmp/test.csv")
        data = ["simple string"]

        result = writer._prepare_data(data)

        assert len(result) == 1
        assert result[0]["value"] == "simple string"

    def test_prepare_none_values(self) -> None:
        """None values are converted to empty string."""
        writer = CSVWriter("/tmp/test.csv")
        data = [{"name": None, "value": "test"}]

        result = writer._prepare_data(data)

        assert result[0]["name"] == ""
        assert result[0]["value"] == "test"

    def test_prepare_with_field_mapper(self) -> None:
        """Field mapper takes precedence."""
        writer = CSVWriter("/tmp/test.csv")
        data = [{"original": "data"}]

        def mapper(item: Dict[str, Any]) -> Dict[str, Any]:
            return {"mapped": item["original"]}

        result = writer._prepare_data(data, field_mapper=mapper)

        assert "mapped" in result[0]
        assert result[0]["mapped"] == "data"


class TestCSVWriterAppendData:
    """Tests for CSVWriter.append_data method."""

    def test_append_to_existing_file(self) -> None:
        """Append data to existing CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.csv")
            writer = CSVWriter(output_file, fieldnames=["name", "age"])

            # Write initial data
            writer.write_data([{"name": "Alice", "age": "30"}])

            # Append more data
            writer.append_data([{"name": "Bob", "age": "25"}])

            with open(output_file, "r") as f:
                lines = f.readlines()
            assert len(lines) == 3  # header + 2 rows
            assert "Alice" in lines[1]
            assert "Bob" in lines[2]

    def test_append_to_nonexistent_file(self) -> None:
        """Appending to nonexistent file creates it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "new_output.csv")
            writer = CSVWriter(output_file)

            writer.append_data([{"name": "Alice"}])

            assert os.path.exists(output_file)
            with open(output_file, "r") as f:
                content = f.read()
            assert "Alice" in content

    def test_append_empty_data(self) -> None:
        """Appending empty data does nothing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.csv")
            writer = CSVWriter(output_file)
            writer.write_data([{"name": "Alice"}])

            writer.append_data([])

            with open(output_file, "r") as f:
                lines = f.readlines()
            assert len(lines) == 2  # header + 1 row


class TestCSVWriterConsoleOutput:
    """Tests for CSVWriter console output feature."""

    def test_console_output_enabled(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Console output is shown when enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.csv")
            writer = CSVWriter(output_file, console_output=True)

            writer.write_data([{"name": "Alice", "age": "30"}])

            captured = capsys.readouterr()
            assert "CSV Data Preview" in captured.out

    def test_console_output_disabled(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Console output is not shown when disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.csv")
            writer = CSVWriter(output_file, console_output=False)

            writer.write_data([{"name": "Alice", "age": "30"}])

            captured = capsys.readouterr()
            assert "CSV Data Preview" not in captured.out


class TestCreateCsvWriter:
    """Tests for create_csv_writer factory function."""

    def test_default_config(self) -> None:
        """Factory creates writer with default config."""
        writer = create_csv_writer("/tmp/test.csv")
        assert isinstance(writer, CSVWriter)
        assert writer.fieldnames is None
        assert writer.console_output is False

    def test_with_custom_fields(self) -> None:
        """Factory creates writer with custom fields."""
        writer = create_csv_writer("/tmp/test.csv", custom_fields=["col1", "col2"])
        assert writer.fieldnames == ["col1", "col2"]

    def test_with_dict_sample(self) -> None:
        """Factory auto-detects fields from dict sample."""
        sample = {"name": "test", "value": 123}
        writer = create_csv_writer("/tmp/test.csv", data_sample=sample)
        assert writer.fieldnames == ["name", "value"]

    def test_with_object_sample(self) -> None:
        """Factory auto-detects fields from object sample."""

        class Sample:
            def __init__(self) -> None:
                self.field1 = "test"
                self.field2 = 123

        sample = Sample()
        writer = create_csv_writer("/tmp/test.csv", data_sample=sample)
        assert "field1" in writer.fieldnames
        assert "field2" in writer.fieldnames

    def test_with_to_csv_dict_sample(self) -> None:
        """Factory auto-detects fields from to_csv_dict sample."""

        class Sample:
            def to_csv_dict(self) -> Dict[str, Any]:
                return {"csv_field": "value"}

        sample = Sample()
        writer = create_csv_writer("/tmp/test.csv", data_sample=sample)
        assert writer.fieldnames == ["csv_field"]

    def test_with_namedtuple_sample(self) -> None:
        """Factory auto-detects fields from NamedTuple sample."""

        class Sample(NamedTuple):
            field_a: str
            field_b: int

        sample = Sample("test", 123)
        writer = create_csv_writer("/tmp/test.csv", data_sample=sample)
        assert writer.fieldnames == ["field_a", "field_b"]

    def test_with_console_output(self) -> None:
        """Factory sets console_output option."""
        writer = create_csv_writer("/tmp/test.csv", console_output=True)
        assert writer.console_output is True
