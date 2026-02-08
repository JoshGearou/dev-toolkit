"""
Tests for GitHub URL parsing utilities.
"""

import os
import sys

import pytest

# Add src directory to path so shared_libs is importable as a package
src_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, src_root)

from shared_libs.github_utils import extract_owner_from_url, parse_repo_url


class TestExtractOwnerFromUrl:
    """Tests for extract_owner_from_url function."""

    def test_full_https_url(self) -> None:
        """Extract owner from full HTTPS URL."""
        assert extract_owner_from_url("https://github.com/linkedin/rest.li") == "linkedin"

    def test_full_http_url(self) -> None:
        """Extract owner from HTTP URL."""
        assert extract_owner_from_url("http://github.com/linkedin/rest.li") == "linkedin"

    def test_url_without_protocol(self) -> None:
        """Extract owner from URL without protocol."""
        assert extract_owner_from_url("github.com/linkedin/rest.li") == "linkedin"

    def test_owner_repo_format(self) -> None:
        """Extract owner from owner/repo format."""
        assert extract_owner_from_url("linkedin/rest.li") == "linkedin"

    def test_just_owner(self) -> None:
        """Return owner when just owner name provided."""
        assert extract_owner_from_url("linkedin") == "linkedin"

    def test_trailing_slash(self) -> None:
        """Handle trailing slashes."""
        assert extract_owner_from_url("https://github.com/linkedin/") == "linkedin"
        assert extract_owner_from_url("linkedin/rest.li/") == "linkedin"

    def test_github_enterprise(self) -> None:
        """Handle GitHub Enterprise URLs."""
        assert extract_owner_from_url("https://github.mycompany.com/team/project") == "team"

    def test_pr_url(self) -> None:
        """Extract owner from PR URL."""
        assert extract_owner_from_url("https://github.com/linkedin/rest.li/pull/123") == "linkedin"


class TestParseRepoUrl:
    """Tests for parse_repo_url function."""

    def test_full_https_url(self) -> None:
        """Parse full HTTPS repo URL."""
        owner, repo, pr = parse_repo_url("https://github.com/linkedin/rest.li")
        assert owner == "linkedin"
        assert repo == "rest.li"
        assert pr is None

    def test_full_http_url(self) -> None:
        """Parse HTTP repo URL."""
        owner, repo, pr = parse_repo_url("http://github.com/linkedin/rest.li")
        assert owner == "linkedin"
        assert repo == "rest.li"
        assert pr is None

    def test_url_with_git_suffix(self) -> None:
        """Parse URL with .git suffix."""
        owner, repo, pr = parse_repo_url("https://github.com/linkedin/rest.li.git")
        assert owner == "linkedin"
        assert repo == "rest.li"
        assert pr is None

    def test_pr_url(self) -> None:
        """Parse PR URL and extract PR number."""
        owner, repo, pr = parse_repo_url("https://github.com/linkedin/rest.li/pull/123")
        assert owner == "linkedin"
        assert repo == "rest.li"
        assert pr == 123

    def test_pr_url_with_trailing_slash(self) -> None:
        """Parse PR URL with trailing slash."""
        owner, repo, pr = parse_repo_url("https://github.com/linkedin/rest.li/pull/456/")
        assert owner == "linkedin"
        assert repo == "rest.li"
        assert pr == 456

    def test_owner_repo_format(self) -> None:
        """Parse owner/repo format."""
        owner, repo, pr = parse_repo_url("linkedin/rest.li")
        assert owner == "linkedin"
        assert repo == "rest.li"
        assert pr is None

    def test_github_enterprise(self) -> None:
        """Parse GitHub Enterprise URL."""
        owner, repo, pr = parse_repo_url("https://github.mycompany.com/team/project")
        assert owner == "team"
        assert repo == "project"
        assert pr is None

    def test_github_enterprise_pr(self) -> None:
        """Parse GitHub Enterprise PR URL."""
        owner, repo, pr = parse_repo_url("https://github.mycompany.com/team/project/pull/42")
        assert owner == "team"
        assert repo == "project"
        assert pr == 42

    def test_invalid_url_raises(self) -> None:
        """Invalid URL raises ValueError."""
        with pytest.raises(ValueError, match="Cannot parse URL"):
            parse_repo_url("invalid-url")

    def test_just_domain_raises(self) -> None:
        """Just domain raises ValueError."""
        with pytest.raises(ValueError, match="Cannot parse URL"):
            parse_repo_url("github.com")

    def test_trailing_slash(self) -> None:
        """Handle trailing slashes properly."""
        owner, repo, pr = parse_repo_url("https://github.com/linkedin/rest.li/")
        assert owner == "linkedin"
        assert repo == "rest.li"
        assert pr is None
