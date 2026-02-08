"""
URL parsing utilities for GitHub repositories.

Provides functions to extract owner, repo, and PR information from various URL formats.
"""

from typing import Optional, Tuple


def extract_owner_from_url(url: str) -> str:
    """
    Extract just the owner/org name from a URL or owner/repo string.

    Args:
        url: GitHub URL, owner/repo string, or just an owner name

    Returns:
        The owner/organization name

    Examples:
        >>> extract_owner_from_url("https://github.com/linkedin/rest.li")
        'linkedin'
        >>> extract_owner_from_url("linkedin/rest.li")
        'linkedin'
        >>> extract_owner_from_url("linkedin")
        'linkedin'
    """
    url = url.rstrip("/")

    # Handle GitHub URLs like github.com/owner or github.com/owner/repo
    if "github.com" in url or "github" in url:
        parts = url.replace("https://", "").replace("http://", "").split("/")
        # Find github.com or ghe.com
        for i, part in enumerate(parts):
            if "github" in part.lower():
                if i + 1 < len(parts):
                    return parts[i + 1]
                break

    # Handle owner/repo format (e.g., "linkedin/rest.li")
    # Check it looks like owner/repo: has exactly one slash and doesn't look like a domain
    if "/" in url and url.count("/") == 1 and not url.startswith("http"):
        return url.split("/")[0]

    # Assume it's just an owner name
    return url


def parse_repo_url(url: str) -> Tuple[str, str, Optional[int]]:
    """
    Parse repo URL and extract owner, repo, and optional PR number.

    Args:
        url: GitHub URL in various formats

    Returns:
        Tuple of (owner, repo, pr_number) where pr_number is None if not a PR URL

    Raises:
        ValueError: If the URL cannot be parsed

    Examples:
        >>> parse_repo_url("https://github.com/linkedin/rest.li/pull/123")
        ('linkedin', 'rest.li', 123)
        >>> parse_repo_url("https://github.com/linkedin/rest.li")
        ('linkedin', 'rest.li', None)
        >>> parse_repo_url("linkedin/rest.li")
        ('linkedin', 'rest.li', None)
    """
    url = url.rstrip("/")

    # Handle PR URLs like github.com/owner/repo/pull/123
    if "/pull/" in url:
        parts = url.split("/")
        pr_idx = parts.index("pull")
        owner = parts[pr_idx - 2]
        repo = parts[pr_idx - 1]
        pr_number = int(parts[pr_idx + 1])
        return owner, repo, pr_number

    # Handle repo URLs like github.com/owner/repo
    if "github.com" in url or "github" in url:
        parts = url.replace("https://", "").replace("http://", "").split("/")
        # Find github.com or ghe.com
        for i, part in enumerate(parts):
            if "github" in part.lower():
                if i + 2 < len(parts):
                    return parts[i + 1], parts[i + 2].replace(".git", ""), None
                break

    # Handle owner/repo format (e.g., "linkedin/rest.li")
    # Check it looks like owner/repo: has exactly one slash and doesn't look like a domain
    if "/" in url and url.count("/") == 1 and not url.startswith("http"):
        parts = url.split("/")
        return parts[0], parts[1], None

    raise ValueError(f"Cannot parse URL: {url}")
