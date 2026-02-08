"""
File categorization utilities.

Provides pattern-based file categorization into DOCS, TEST, CODE, or UNKNOWN.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .patterns import DEFAULT_FILE_PATTERNS, FileCategory


@dataclass
class FileCategorizerConfig:
    """Configuration for file categorization."""

    custom_patterns: Optional[List[Tuple[FileCategory, str]]] = None
    use_default_patterns: bool = True
    case_sensitive: bool = False


class FileCategorizer:
    """
    Categorize files based on regex patterns.

    Patterns are evaluated in order - first match wins.

    Example:
        categorizer = FileCategorizer()
        category = categorizer.categorize_file("src/test_utils.py")
        # Returns FileCategory.TEST

        results = categorizer.categorize_files(["README.md", "main.py"])
        # Returns {FileCategory.DOCS: ["README.md"], FileCategory.CODE: ["main.py"], ...}
    """

    def __init__(self, config: Optional[FileCategorizerConfig] = None) -> None:
        """
        Initialize file categorizer.

        Args:
            config: Configuration options. If None, uses defaults.
        """
        self.config = config or FileCategorizerConfig()
        self._patterns: List[Tuple[FileCategory, re.Pattern[str]]] = []
        self._raw_patterns: List[Tuple[FileCategory, str]] = []
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficient matching."""
        patterns_to_use: List[Tuple[FileCategory, str]] = []

        # Add custom patterns first (higher priority)
        if self.config.custom_patterns:
            patterns_to_use.extend(self.config.custom_patterns)

        # Add default patterns
        if self.config.use_default_patterns:
            patterns_to_use.extend(DEFAULT_FILE_PATTERNS)

        # Store raw patterns for get_matching_pattern()
        self._raw_patterns = patterns_to_use

        # Compile patterns
        flags = 0 if self.config.case_sensitive else re.IGNORECASE
        for category, pattern in patterns_to_use:
            try:
                compiled = re.compile(pattern, flags)
                self._patterns.append((category, compiled))
            except re.error as e:
                # Skip invalid patterns but log warning
                print(f"Warning: Invalid regex pattern '{pattern}': {e}")

    def categorize_file(self, filepath: str) -> FileCategory:
        """
        Categorize a single file based on its path.

        First matching pattern wins.

        Args:
            filepath: File path to categorize

        Returns:
            FileCategory enum value
        """
        if not filepath:
            return FileCategory.UNKNOWN

        for category, pattern in self._patterns:
            if pattern.search(filepath):
                return category

        return FileCategory.UNKNOWN

    def categorize_files(self, files: List[str]) -> Dict[FileCategory, List[str]]:
        """
        Categorize multiple files into buckets.

        Args:
            files: List of file paths to categorize

        Returns:
            Dictionary mapping FileCategory to list of matching files
        """
        result: Dict[FileCategory, List[str]] = {cat: [] for cat in FileCategory}

        for filepath in files:
            category = self.categorize_file(filepath)
            result[category].append(filepath)

        return result

    def get_matching_pattern(self, filepath: str) -> Optional[str]:
        """
        Get the pattern string that matched a file.

        Useful for debugging why a file was categorized a certain way.

        Args:
            filepath: File path to check

        Returns:
            The pattern string that matched, or None if no match
        """
        if not filepath:
            return None

        flags = 0 if self.config.case_sensitive else re.IGNORECASE

        for category, pattern_str in self._raw_patterns:
            if re.search(pattern_str, filepath, flags):
                return pattern_str

        return None

    def get_category_summary(self, files: List[str]) -> Dict[str, int]:
        """
        Get a summary count of files by category.

        Args:
            files: List of file paths

        Returns:
            Dictionary mapping category name to count
        """
        categorized = self.categorize_files(files)
        return {cat.value: len(files_list) for cat, files_list in categorized.items()}


def create_file_categorizer(
    custom_patterns: Optional[List[Tuple[FileCategory, str]]] = None,
    use_default_patterns: bool = True,
    case_sensitive: bool = False,
) -> FileCategorizer:
    """
    Create a file categorizer with the specified configuration.

    Args:
        custom_patterns: Additional patterns to use (evaluated first)
        use_default_patterns: Whether to include default patterns
        case_sensitive: Whether pattern matching is case-sensitive

    Returns:
        Configured FileCategorizer instance
    """
    config = FileCategorizerConfig(
        custom_patterns=custom_patterns,
        use_default_patterns=use_default_patterns,
        case_sensitive=case_sensitive,
    )
    return FileCategorizer(config)


# Convenience functions for simple usage
def categorize_file(filepath: str) -> FileCategory:
    """
    Categorize a single file using default patterns.

    Args:
        filepath: File path to categorize

    Returns:
        FileCategory enum value
    """
    return _default_categorizer.categorize_file(filepath)


def categorize_files(files: List[str]) -> Dict[FileCategory, List[str]]:
    """
    Categorize multiple files using default patterns.

    Args:
        files: List of file paths

    Returns:
        Dictionary mapping FileCategory to list of files
    """
    return _default_categorizer.categorize_files(files)


# Module-level default categorizer (lazy initialization)
_default_categorizer = FileCategorizer()
