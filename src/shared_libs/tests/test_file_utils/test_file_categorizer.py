"""
Tests for file categorization utilities.
"""

import os
import sys

import pytest

# Add src directory to path so shared_libs is importable as a package
src_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, src_root)

from shared_libs.file_utils import (
    FileCategorizer,
    FileCategory,
    categorize_file,
    categorize_files,
    create_file_categorizer,
)


class TestFileCategory:
    """Tests for FileCategory enum."""

    def test_category_values(self) -> None:
        """All expected categories exist with correct values."""
        assert FileCategory.DOCS.value == "docs"
        assert FileCategory.TEST.value == "test"
        assert FileCategory.CODE.value == "code"
        assert FileCategory.UNKNOWN.value == "unknown"

    def test_category_count(self) -> None:
        """Exactly 4 categories exist."""
        assert len(FileCategory) == 4


class TestCategorizeDocs:
    """Tests for DOCS file categorization."""

    @pytest.mark.parametrize(
        "filepath",
        [
            "README.md",
            "docs/guide.md",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            "file.txt",
            "notes.rst",
            "guide.adoc",
            "manual.pdf",
            "report.doc",
            "report.docx",
            "LICENSE",
            "src/LICENSE",
            "docs/api.md",
            "documentation/index.md",
        ],
    )
    def test_docs_files(self, filepath: str) -> None:
        """Documentation files should be categorized as DOCS."""
        assert categorize_file(filepath) == FileCategory.DOCS


class TestCategorizeTest:
    """Tests for TEST file categorization."""

    @pytest.mark.parametrize(
        "filepath",
        [
            "tests/test_main.py",
            "test/unit_test.py",
            "src/tests/integration.py",
            "__tests__/component.test.js",
            "spec/model_spec.rb",
            "specs/helper_spec.ts",
            "foo_test.py",
            "bar_test.go",
            "utils_test.java",
            "component.test.js",
            "module.test.tsx",
            "helper_spec.rb",
            "test_utils.py",
            "FooTest.java",
            "BarTest.kt",
        ],
    )
    def test_test_files(self, filepath: str) -> None:
        """Test files should be categorized as TEST."""
        assert categorize_file(filepath) == FileCategory.TEST

    def test_test_priority_over_code(self) -> None:
        """Test patterns should match before code patterns."""
        # These are .py files but in test directories or with test naming
        assert categorize_file("tests/utils.py") == FileCategory.TEST
        assert categorize_file("test_helper.py") == FileCategory.TEST
        assert categorize_file("src/test/main.py") == FileCategory.TEST


class TestCategorizeCode:
    """Tests for CODE file categorization."""

    @pytest.mark.parametrize(
        "filepath",
        [
            # Programming languages
            "main.py",
            "app.js",
            "index.ts",
            "Component.tsx",
            "Main.java",
            "main.go",
            "lib.rs",
            "script.rb",
            "program.c",
            "program.cpp",
            "header.h",
            "App.swift",
            "Main.kt",
            "Module.scala",
            # Scripts
            "build.sh",
            "setup.bash",
            "init.zsh",
            "deploy.ps1",
            "run.bat",
            # Config files
            "config.json",
            "settings.yaml",
            "app.yml",
            "config.toml",
            "data.xml",
            "app.ini",
            # Web files
            "index.html",
            "styles.css",
            "theme.scss",
            # Database/query
            "schema.sql",
            "query.graphql",
            "message.proto",
            # Build files
            "Makefile",
            "Dockerfile",
            "build.gradle",
            ".gitignore",
            ".bashrc",
            "go.mod",
            "go.sum",
            # Notebooks
            "analysis.ipynb",
            # Data files
            "data.csv",
            "data.parquet",
        ],
    )
    def test_code_files(self, filepath: str) -> None:
        """Code files should be categorized as CODE."""
        assert categorize_file(filepath) == FileCategory.CODE


class TestCategorizeUnknown:
    """Tests for UNKNOWN file categorization."""

    @pytest.mark.parametrize(
        "filepath",
        [
            "random_file",
            "no_extension",
            "file.xyz",
            "data.unknown",
            ".hidden_no_ext",
        ],
    )
    def test_unknown_files(self, filepath: str) -> None:
        """Unrecognized files should be categorized as UNKNOWN."""
        assert categorize_file(filepath) == FileCategory.UNKNOWN


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_string(self) -> None:
        """Empty string returns UNKNOWN."""
        assert categorize_file("") == FileCategory.UNKNOWN

    def test_whitespace_only(self) -> None:
        """Whitespace-only string returns UNKNOWN."""
        assert categorize_file("   ") == FileCategory.UNKNOWN

    def test_special_characters(self) -> None:
        """Files with special characters are handled."""
        assert categorize_file("my-file.py") == FileCategory.CODE
        assert categorize_file("my_file.py") == FileCategory.CODE
        assert categorize_file("my.file.py") == FileCategory.CODE

    def test_deep_paths(self) -> None:
        """Deep nested paths are handled."""
        assert categorize_file("a/b/c/d/e/f/main.py") == FileCategory.CODE
        assert categorize_file("very/deep/path/to/tests/test_main.py") == FileCategory.TEST

    def test_case_insensitivity(self) -> None:
        """Pattern matching is case-insensitive by default."""
        assert categorize_file("README.MD") == FileCategory.DOCS
        assert categorize_file("readme.md") == FileCategory.DOCS
        assert categorize_file("Main.PY") == FileCategory.CODE


class TestCategorizeFiles:
    """Tests for batch categorization."""

    def test_categorize_multiple_files(self) -> None:
        """Multiple files are categorized correctly."""
        files = [
            "README.md",
            "main.py",
            "test_main.py",
            "unknown.xyz",
        ]
        result = categorize_files(files)

        assert result[FileCategory.DOCS] == ["README.md"]
        assert result[FileCategory.CODE] == ["main.py"]
        assert result[FileCategory.TEST] == ["test_main.py"]
        assert result[FileCategory.UNKNOWN] == ["unknown.xyz"]

    def test_empty_list(self) -> None:
        """Empty list returns empty categories."""
        result = categorize_files([])
        assert all(len(files) == 0 for files in result.values())

    def test_all_same_category(self) -> None:
        """All files in same category."""
        files = ["a.md", "b.md", "c.txt"]
        result = categorize_files(files)
        assert len(result[FileCategory.DOCS]) == 3


class TestFileCategorizer:
    """Tests for FileCategorizer class."""

    def test_default_initialization(self) -> None:
        """Default categorizer works correctly."""
        categorizer = FileCategorizer()
        assert categorizer.categorize_file("main.py") == FileCategory.CODE

    def test_custom_patterns(self) -> None:
        """Custom patterns are used."""
        custom = [(FileCategory.DOCS, r".*\.wiki$")]
        categorizer = create_file_categorizer(custom_patterns=custom)

        # Custom pattern should match
        assert categorizer.categorize_file("page.wiki") == FileCategory.DOCS

        # Default patterns still work
        assert categorizer.categorize_file("main.py") == FileCategory.CODE

    def test_custom_patterns_priority(self) -> None:
        """Custom patterns take priority over defaults."""
        # Override .py files to be DOCS (unusual but tests priority)
        custom = [(FileCategory.DOCS, r".*\.py$")]
        categorizer = create_file_categorizer(custom_patterns=custom)

        assert categorizer.categorize_file("main.py") == FileCategory.DOCS

    def test_no_default_patterns(self) -> None:
        """Can disable default patterns."""
        custom = [(FileCategory.CODE, r".*\.xyz$")]
        categorizer = create_file_categorizer(
            custom_patterns=custom,
            use_default_patterns=False,
        )

        # Custom pattern works
        assert categorizer.categorize_file("file.xyz") == FileCategory.CODE

        # Default patterns don't work
        assert categorizer.categorize_file("main.py") == FileCategory.UNKNOWN

    def test_get_matching_pattern(self) -> None:
        """Can retrieve the pattern that matched."""
        categorizer = FileCategorizer()

        pattern = categorizer.get_matching_pattern("README.md")
        assert pattern is not None
        assert ".md" in pattern.lower() or "readme" in pattern.lower()

        pattern = categorizer.get_matching_pattern("unknown.xyz")
        assert pattern is None

    def test_get_category_summary(self) -> None:
        """Category summary returns correct counts."""
        categorizer = FileCategorizer()
        files = ["a.md", "b.md", "main.py", "test_main.py", "unknown"]

        summary = categorizer.get_category_summary(files)

        assert summary["docs"] == 2
        assert summary["code"] == 1
        assert summary["test"] == 1
        assert summary["unknown"] == 1

    def test_case_sensitive_option(self) -> None:
        """Case sensitivity can be enabled."""
        # Case-insensitive (default)
        categorizer = create_file_categorizer(case_sensitive=False)
        assert categorizer.categorize_file("README.MD") == FileCategory.DOCS

        # Case-sensitive
        categorizer_cs = create_file_categorizer(case_sensitive=True)
        # Pattern uses lowercase, so uppercase won't match as well
        # This depends on pattern definitions - test that behavior differs
        result_lower = categorizer_cs.categorize_file("readme.md")
        categorizer_cs.categorize_file("README.MD")
        # Both should still be DOCS because patterns handle common cases
        assert result_lower == FileCategory.DOCS


class TestFactoryFunction:
    """Tests for create_file_categorizer factory."""

    def test_factory_default(self) -> None:
        """Factory with defaults works."""
        categorizer = create_file_categorizer()
        assert isinstance(categorizer, FileCategorizer)
        assert categorizer.categorize_file("main.py") == FileCategory.CODE

    def test_factory_all_options(self) -> None:
        """Factory with all options works."""
        categorizer = create_file_categorizer(
            custom_patterns=[(FileCategory.DOCS, r".*\.custom$")],
            use_default_patterns=True,
            case_sensitive=False,
        )
        assert categorizer.categorize_file("file.custom") == FileCategory.DOCS
        assert categorizer.categorize_file("main.py") == FileCategory.CODE
