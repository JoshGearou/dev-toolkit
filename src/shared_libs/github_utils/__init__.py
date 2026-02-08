"""
GitHub utilities for interacting with the GitHub CLI.

Provides URL parsing and a robust gh CLI client with rate limit handling.

Example:
    from shared_libs.github_utils import GHClient, parse_repo_url

    # Parse a GitHub URL
    owner, repo, pr_number = parse_repo_url("https://github.com/linkedin/rest.li/pull/123")

    # Use the GHClient for GitHub operations
    client = GHClient()
    prs = client.list_prs(owner, repo, limit=10, state="open")

    # Search repos with exclusion status
    repos_with_status = client.search_repos_with_exclusion_status(
        "myorg", "^prod-", exclude_patterns=["sandbox", "test"]
    )
"""

from .gh_client import (
    GHClient,
    GHClientConfig,
    create_gh_client,
)
from .url_parser import (
    extract_owner_from_url,
    parse_repo_url,
)

__all__ = [
    # Client
    "GHClient",
    "GHClientConfig",
    "create_gh_client",
    # URL parsing
    "extract_owner_from_url",
    "parse_repo_url",
]
