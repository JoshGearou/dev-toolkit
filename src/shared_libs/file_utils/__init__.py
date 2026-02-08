r"""
File utilities for categorizing and analyzing files.

Provides pattern-based file categorization into DOCS, TEST, CODE, or UNKNOWN.

Example:
    from shared_libs.file_utils import categorize_file, FileCategory

    category = categorize_file("src/test_utils.py")
    if category == FileCategory.TEST:
        print("This is a test file")

    # Or use the class for more control:
    from shared_libs.file_utils import FileCategorizer, create_file_categorizer

    categorizer = create_file_categorizer(
        custom_patterns=[(FileCategory.DOCS, r".*\.wiki$")],
    )
    results = categorizer.categorize_files(file_list)
"""

from .file_categorizer import (
    FileCategorizer,
    FileCategorizerConfig,
    categorize_file,
    categorize_files,
    create_file_categorizer,
)
from .patterns import DEFAULT_FILE_PATTERNS, FileCategory

__all__ = [
    # Enum
    "FileCategory",
    # Classes
    "FileCategorizer",
    "FileCategorizerConfig",
    # Functions
    "categorize_file",
    "categorize_files",
    "create_file_categorizer",
    # Constants
    "DEFAULT_FILE_PATTERNS",
]
