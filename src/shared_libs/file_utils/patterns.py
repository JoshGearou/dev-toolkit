"""
Default file categorization patterns.

Provides regex patterns for categorizing files into DOCS, TEST, CODE, or UNKNOWN.
Patterns are evaluated in order - first match wins.
"""

from enum import Enum
from typing import List, Tuple


class FileCategory(Enum):
    """Categories for classifying files."""

    DOCS = "docs"
    TEST = "test"
    CODE = "code"
    UNKNOWN = "unknown"


# Default patterns for file categorization
# Order matters: first match wins
DEFAULT_FILE_PATTERNS: List[Tuple[FileCategory, str]] = [
    # Documentation files
    (FileCategory.DOCS, r".*\.md$"),
    (FileCategory.DOCS, r".*\.txt$"),
    (FileCategory.DOCS, r".*\.rst$"),
    (FileCategory.DOCS, r".*\.adoc$"),
    (FileCategory.DOCS, r".*\.(doc|docx|pdf|pptx)$"),
    (FileCategory.DOCS, r".*\.tex$"),
    (FileCategory.DOCS, r"^(README|CHANGELOG|CONTRIBUTING|AUTHORS)"),
    (FileCategory.DOCS, r"(^|.*/)LICENSE$"),
    (FileCategory.DOCS, r"(^|.*/)NOTICE$"),
    (FileCategory.DOCS, r"^docs/"),
    (FileCategory.DOCS, r"^documentation/"),
    # Test files (check before code - path or name contains "test")
    (FileCategory.TEST, r".*[/]?test[s]?[/].*"),
    (FileCategory.TEST, r".*[/]?__tests__[/].*"),
    (FileCategory.TEST, r".*[/]?spec[s]?[/].*"),
    (FileCategory.TEST, r".*_test\.(py|js|ts|go|java)$"),
    (FileCategory.TEST, r".*\.test\.(py|js|ts|tsx|jsx)$"),
    (FileCategory.TEST, r".*_spec\.(rb|js|ts)$"),
    (FileCategory.TEST, r"^test_.*\.(py|js|ts)$"),
    (FileCategory.TEST, r".*Test\.(java|kt)$"),
    # Code files (scripts and programming languages)
    (
        FileCategory.CODE,
        r".*\.(py|js|ts|tsx|jsx|java|go|rs|rb|c|cc|cpp|h|hpp|cs|swift|kt|scala)$",
    ),
    (FileCategory.CODE, r".*\.(swiftinterface|swiftdoc)$"),
    (FileCategory.CODE, r".*\.class$"),
    (FileCategory.CODE, r".*\.(pyc|pyo|pyd)$"),
    (FileCategory.CODE, r".*\.(sh|bash|zsh|fish|ps1|bat|cmd)$"),
    (FileCategory.CODE, r".*\.(json|yaml|yml|toml|xml|ini|cfg|conf|acl)$"),
    (FileCategory.CODE, r".*\.(cmake|plist|prefs|iml|project)$"),
    (FileCategory.CODE, r".*\.(jinja|jinja2|j2|hbs|tmpl)$"),
    (FileCategory.CODE, r".*\.(html|css|scss|sass|less)$"),
    (FileCategory.CODE, r".*\.(sql|graphql|proto|kql|hql)$"),
    (FileCategory.CODE, r".*\.(libsonnet|flow|dsl)$"),
    (FileCategory.CODE, r".*\.(pls|plsql|plb)$"),
    (FileCategory.CODE, r".*\.(VW|CST|IDX|TBL)$"),
    (FileCategory.CODE, r".*\.definition$"),
    (FileCategory.CODE, r".*\.(ipynb|swb)$"),
    (FileCategory.CODE, r".*\.(fbs|thrift|avsc|avro|orc)$"),
    (FileCategory.CODE, r".*\.(properties|env\.example|ldt)$"),
    (FileCategory.CODE, r".*\.(gradle|gradle\.kts)$"),
    (FileCategory.CODE, r".*\.(csv|jsonl)$"),
    (FileCategory.CODE, r".*\.(svg|png|jpg|jpeg|gif|webp|ico)$"),
    (FileCategory.CODE, r".*\.(jar|war|ear)$"),
    (FileCategory.CODE, r".*\.(lock|sum)$"),
    (FileCategory.CODE, r".*\.(groovy|gvy|gy|gsh)$"),
    (FileCategory.CODE, r".*\.(R|r)$"),
    (FileCategory.CODE, r".*\.(parquet|dat|db|sqlite)$"),
    (FileCategory.CODE, r".*\.(ispac|dtsx|rdl)$"),
    (FileCategory.CODE, r".*\.(bazel|bzl)$"),
    (FileCategory.CODE, r".*\.(pt|pth|ckpt)$"),
    (FileCategory.CODE, r".*\.(csproj|vbproj|fsproj|sln)$"),
    (FileCategory.CODE, r".*\.(dot|gv)$"),
    (FileCategory.CODE, r".*\.textproto$"),
    (FileCategory.CODE, r".*\.(service|socket|timer)$"),
    (FileCategory.CODE, r".*\.(example|sample)$"),
    (FileCategory.CODE, r".*\.code-workspace$"),
    (FileCategory.CODE, r".*\.so(\.\d+)*$"),
    (FileCategory.CODE, r".*\.(zip|tar|gz|bz2|xz|7z)$"),
    (FileCategory.CODE, r".*\.(bin|exe|dll)$"),
    (FileCategory.CODE, r".*\.DS_Store$"),
    (FileCategory.CODE, r".*/dist-info/(WHEEL|METADATA|RECORD|INSTALLER|REQUESTED)$"),
    (FileCategory.CODE, r".*/CODEOWNERS$"),
    (FileCategory.CODE, r"^Makefile$"),
    (FileCategory.CODE, r"^Dockerfile"),
    (FileCategory.CODE, r".*\.dockerfile$"),
    (FileCategory.CODE, r".*\.Dockerfile$"),
    (FileCategory.CODE, r"^\..*rc$"),
    (FileCategory.CODE, r"^\.gitignore$"),
    (FileCategory.CODE, r".*/\.gitignore$"),
    (FileCategory.CODE, r"^\.gitkeep$"),
    (FileCategory.CODE, r".*/\.gitkeep$"),
    (FileCategory.CODE, r"^\.gitmodules$"),
    (FileCategory.CODE, r".*/\.gitmodules$"),
    (FileCategory.CODE, r"^WORKSPACE$"),
    (FileCategory.CODE, r".*/WORKSPACE$"),
    (FileCategory.CODE, r"^\.env$"),
    (FileCategory.CODE, r".*/\.env$"),
    (FileCategory.CODE, r"(^|.*/)(go\.mod|go\.sum)$"),
    (FileCategory.CODE, r".*gradlew$"),
    (FileCategory.CODE, r".*/settings\.gradle$"),
    (FileCategory.CODE, r".*/build\.gradle$"),
    (FileCategory.CODE, r".*/MANIFEST\.in$"),
    (FileCategory.CODE, r".*/routes$"),
    (FileCategory.CODE, r".*/PKG-INFO$"),
    (FileCategory.CODE, r".*\.(map|backup|bak|orig|patch|link)$"),
    (FileCategory.CODE, r".*\.pem$"),
    (FileCategory.CODE, r".*\.(mdc|mdx)$"),
    (FileCategory.CODE, r".*\.(bicep|tf|tfvars)$"),
    (FileCategory.CODE, r".*\.(cypher|cql)$"),
    (FileCategory.CODE, r".*\.(spec|podspec)$"),
    (FileCategory.CODE, r".*\.(cron|crontab)$"),
    (FileCategory.CODE, r".*\.(ctl|am|in)$"),
    (FileCategory.CODE, r".*\.template$"),
    (FileCategory.CODE, r".*\.kdbx$"),
]
