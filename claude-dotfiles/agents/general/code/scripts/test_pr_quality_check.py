#!/usr/bin/env python3
"""Unit tests for pr_quality_check.py."""

import json
from unittest.mock import MagicMock, patch

import pytest
from pr_quality_check import (
    CICheckResult,
    DimensionScore,
    PRQualityCheck,
    PRQualityReport,
    analyze_pr_quality,
    calculate_dimension_score,
    calculate_grade,
    categorize_pr_size,
    check_post_merge_ci_status,
    generate_report,
    get_msft_fiscal_year_dates,
    get_pr_diff_stats,
    get_prs_reviewed_by_user,
    get_user_prs,
    normalize_issue_for_frequency,
    run_gh_command,
)


class TestHelperFunctions:
    """Test helper/utility functions."""

    def test_calculate_grade_a(self) -> None:
        """Test grade calculation for A range."""
        assert calculate_grade(100) == "A"
        assert calculate_grade(95) == "A"
        assert calculate_grade(90) == "A"

    def test_calculate_grade_b(self) -> None:
        """Test grade calculation for B range."""
        assert calculate_grade(89) == "B"
        assert calculate_grade(85) == "B"
        assert calculate_grade(80) == "B"

    def test_calculate_grade_c(self) -> None:
        """Test grade calculation for C range."""
        assert calculate_grade(79) == "C"
        assert calculate_grade(75) == "C"
        assert calculate_grade(70) == "C"

    def test_calculate_grade_d(self) -> None:
        """Test grade calculation for D range."""
        assert calculate_grade(69) == "D"
        assert calculate_grade(65) == "D"
        assert calculate_grade(60) == "D"

    def test_calculate_grade_f(self) -> None:
        """Test grade calculation for F range."""
        assert calculate_grade(59) == "F"
        assert calculate_grade(30) == "F"
        assert calculate_grade(0) == "F"

    def test_categorize_pr_size_small(self) -> None:
        """Test PR size categorization for small PRs."""
        assert categorize_pr_size(30, 20, 2) == "small"
        assert categorize_pr_size(50, 0, 3) == "small"
        assert categorize_pr_size(25, 25, 1) == "small"

    def test_categorize_pr_size_medium(self) -> None:
        """Test PR size categorization for medium PRs."""
        assert categorize_pr_size(100, 50, 5) == "medium"
        assert categorize_pr_size(150, 50, 10) == "medium"
        assert categorize_pr_size(51, 0, 4) == "medium"

    def test_categorize_pr_size_large(self) -> None:
        """Test PR size categorization for large PRs."""
        assert categorize_pr_size(300, 100, 15) == "large"
        assert categorize_pr_size(400, 100, 20) == "large"
        assert categorize_pr_size(201, 0, 5) == "large"

    def test_categorize_pr_size_xlarge(self) -> None:
        """Test PR size categorization for extra large PRs."""
        assert categorize_pr_size(600, 100, 25) == "xlarge"
        assert categorize_pr_size(1000, 500, 50) == "xlarge"
        assert categorize_pr_size(501, 0, 21) == "xlarge"

    def test_get_msft_fiscal_year_dates(self) -> None:
        """Test Microsoft fiscal year calculation."""
        fy_name, start, end = get_msft_fiscal_year_dates()

        # Verify format
        assert fy_name.startswith("FY")
        assert len(fy_name) == 4  # FY26, FY27, etc.
        assert start.count("-") == 2  # YYYY-MM-DD
        assert end.count("-") == 2

        # Verify fiscal year runs July-June
        assert start.endswith("-07-01")
        assert end.endswith("-06-30")

        # Verify dates are sequential
        start_year = int(start.split("-")[0])
        end_year = int(end.split("-")[0])
        assert end_year == start_year + 1

    def test_normalize_issue_for_frequency_ci_failures(self) -> None:
        """Test normalization of CI/CD failure messages."""
        # Different check counts should normalize to same string
        assert (
            normalize_issue_for_frequency("CRITICAL: Post-merge CI/CD failure (2 checks failed)")
            == "CRITICAL: Post-merge CI/CD failure"
        )
        assert (
            normalize_issue_for_frequency("CRITICAL: Post-merge CI/CD failure (4 checks failed)")
            == "CRITICAL: Post-merge CI/CD failure"
        )
        assert (
            normalize_issue_for_frequency("CRITICAL: Post-merge CI/CD failure (10 checks failed)")
            == "CRITICAL: Post-merge CI/CD failure"
        )

    def test_normalize_issue_for_frequency_large_prs(self) -> None:
        """Test normalization of large PR messages."""
        # Different sizes should normalize to same string
        assert normalize_issue_for_frequency("Large PR (448 changes, 4 files)") == "Large PR - consider splitting"
        assert (
            normalize_issue_for_frequency("Very large PR (678 changes, 2 files) - consider splitting")
            == "Very large PR - consider splitting"
        )
        assert (
            normalize_issue_for_frequency("Very large PR (1064 changes, 7 files) - consider splitting")
            == "Very large PR - consider splitting"
        )

    def test_normalize_issue_for_frequency_unchanged(self) -> None:
        """Test that other issues remain unchanged."""
        # Issues without dynamic content stay the same
        assert normalize_issue_for_frequency("No JIRA ticket reference") == "No JIRA ticket reference"
        assert normalize_issue_for_frequency("No labels on PR") == "No labels on PR"
        assert (
            normalize_issue_for_frequency("CRITICAL: Empty or missing description")
            == "CRITICAL: Empty or missing description"
        )
        assert (
            normalize_issue_for_frequency("Description too brief (< 50 chars)") == "Description too brief (< 50 chars)"
        )


class TestGitHubCommands:
    """Test GitHub CLI command execution."""

    @patch("pr_quality_check.subprocess.run")
    def test_run_gh_command_success(self, mock_run: MagicMock) -> None:
        """Test successful gh command execution."""
        mock_run.return_value = MagicMock(returncode=0, stdout="success output", stderr="")

        success, output = run_gh_command(["pr", "list"])

        assert success is True
        assert output == "success output"
        mock_run.assert_called_once()

    @patch("pr_quality_check.subprocess.run")
    def test_run_gh_command_failure(self, mock_run: MagicMock) -> None:
        """Test failed gh command execution."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error message")

        success, output = run_gh_command(["pr", "list"])

        assert success is False
        assert output == "error message"

    @patch("pr_quality_check.subprocess.run")
    @patch("pr_quality_check.time.sleep")
    def test_run_gh_command_rate_limit_retry(self, mock_sleep: MagicMock, mock_run: MagicMock) -> None:
        """Test rate limit retry with exponential backoff."""
        # First call fails with rate limit, second succeeds
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="rate limit exceeded"),
            MagicMock(returncode=0, stdout="success", stderr=""),
        ]

        success, output = run_gh_command(["pr", "list"])

        assert success is True
        assert output == "success"
        assert mock_run.call_count == 2
        mock_sleep.assert_called_once()

    @patch("pr_quality_check.subprocess.run")
    def test_run_gh_command_timeout(self, mock_run: MagicMock) -> None:
        """Test gh command timeout handling."""
        from subprocess import TimeoutExpired

        mock_run.side_effect = TimeoutExpired(cmd=["gh", "pr", "list"], timeout=60)

        success, output = run_gh_command(["pr", "list"])

        assert success is False
        assert "timed out" in output.lower()


class TestPRDataFetching:
    """Test PR data fetching functions."""

    @patch("pr_quality_check.run_gh_command")
    def test_get_user_prs_specific_repo(self, mock_gh: MagicMock) -> None:
        """Test fetching PRs for specific repository."""
        mock_prs = [
            {
                "number": 123,
                "title": "Test PR",
                "mergedAt": "2025-08-01T12:00:00Z",
                "url": "https://github.com/test/repo/pull/123",
            }
        ]
        mock_gh.return_value = (True, json.dumps(mock_prs))

        prs = get_user_prs("testuser", "test/repo", "2025-07-01", "2026-06-30")

        assert len(prs) == 1
        assert prs[0]["number"] == 123

    @patch("pr_quality_check.run_gh_command")
    def test_get_user_prs_all_repos(self, mock_gh: MagicMock) -> None:
        """Test fetching PRs across all repositories."""
        # Mock search results
        search_results = [
            {
                "number": 456,
                "repository": {"nameWithOwner": "org/repo1"},
                "url": "https://github.com/org/repo1/pull/456",
            }
        ]

        pr_details = {
            "number": 456,
            "title": "Test PR",
            "mergedAt": "2025-08-01T12:00:00Z",
            "url": "https://github.com/org/repo1/pull/456",
        }

        # First call returns search results, second returns PR details
        mock_gh.side_effect = [
            (True, json.dumps(search_results)),
            (True, json.dumps(pr_details)),
        ]

        prs = get_user_prs("testuser", None, "2025-07-01", "2026-06-30")

        assert len(prs) == 1
        assert prs[0]["number"] == 456
        assert prs[0]["repo_name"] == "org/repo1"

    @patch("pr_quality_check.run_gh_command")
    def test_get_pr_diff_stats_with_tests(self, mock_gh: MagicMock) -> None:
        """Test diff stats extraction with test files."""
        files = "src/main.py\ntests/test_main.py\nREADME.md"
        mock_gh.return_value = (True, files)

        stats = get_pr_diff_stats("test/repo", 123)

        assert stats["test_files"] == 1
        assert stats["code_files"] == 1
        assert len(stats["files"]) == 3

    @patch("pr_quality_check.run_gh_command")
    def test_get_pr_diff_stats_no_tests(self, mock_gh: MagicMock) -> None:
        """Test diff stats extraction without test files."""
        files = "src/main.py\nsrc/utils.py\nREADME.md"
        mock_gh.return_value = (True, files)

        stats = get_pr_diff_stats("test/repo", 123)

        assert stats["test_files"] == 0
        assert stats["code_files"] == 2

    @patch("pr_quality_check.run_gh_command")
    def test_get_prs_reviewed_by_user(self, mock_gh: MagicMock) -> None:
        """Test counting PRs reviewed by user (excluding self-authored)."""
        # Mock response includes PRs authored by testuser and others
        mock_prs = [
            {"number": 1, "author": {"login": "otheruser"}},
            {"number": 2, "author": {"login": "testuser"}},  # Self-authored, should be excluded
            {"number": 3, "author": {"login": "anotheruser"}},
        ]
        mock_gh.return_value = (True, json.dumps(mock_prs))

        count = get_prs_reviewed_by_user("testuser", None, "2025-07-01", "2026-06-30")

        # Should count only 2 PRs (excluding the self-authored one)
        assert count == 2


class TestPostMergeCIStatus:
    """Test post-merge CI/CD status checking."""

    @patch("pr_quality_check.run_gh_command")
    def test_check_post_merge_ci_success(self, mock_gh: MagicMock) -> None:
        """Test successful CI/CD checks."""
        # Mock merge commit response
        merge_commit = {"mergeCommit": {"oid": "abc123"}}

        # Mock check runs response
        check_runs = "\n".join(
            [
                json.dumps(
                    {
                        "id": 1,
                        "name": "test",
                        "status": "completed",
                        "conclusion": "success",
                        "html_url": "https://example.com/1",
                    }
                ),
                json.dumps(
                    {
                        "id": 2,
                        "name": "lint",
                        "status": "completed",
                        "conclusion": "success",
                        "html_url": "https://example.com/2",
                    }
                ),
            ]
        )

        mock_gh.side_effect = [
            (True, json.dumps(merge_commit)),
            (True, check_runs),
        ]

        result = check_post_merge_ci_status("test/repo", 123)

        assert result.status == "success"
        assert len(result.failed_checks) == 0
        assert len(result.failed_check_urls) == 0
        assert result.has_test_check is True

    @patch("pr_quality_check.run_gh_command")
    def test_check_post_merge_ci_failure(self, mock_gh: MagicMock) -> None:
        """Test failed CI/CD checks."""
        merge_commit = {"mergeCommit": {"oid": "abc123"}}

        check_runs = "\n".join(
            [
                json.dumps(
                    {
                        "id": 1,
                        "name": "test",
                        "status": "completed",
                        "conclusion": "failure",
                        "html_url": "https://example.com/failed",
                    }
                ),
                json.dumps(
                    {
                        "id": 2,
                        "name": "lint",
                        "status": "completed",
                        "conclusion": "success",
                        "html_url": "https://example.com/success",
                    }
                ),
            ]
        )

        mock_gh.side_effect = [
            (True, json.dumps(merge_commit)),
            (True, check_runs),
        ]

        result = check_post_merge_ci_status("test/repo", 123)

        assert result.status == "failure"
        assert len(result.failed_checks) == 1
        assert "test" in result.failed_checks
        assert len(result.failed_check_urls) == 1
        assert result.failed_check_urls[0] == "https://example.com/failed"

    @patch("pr_quality_check.run_gh_command")
    def test_check_post_merge_ci_pending(self, mock_gh: MagicMock) -> None:
        """Test pending CI/CD checks."""
        merge_commit = {"mergeCommit": {"oid": "abc123"}}

        check_runs = "\n".join(
            [
                json.dumps(
                    {
                        "id": 1,
                        "name": "test",
                        "status": "in_progress",
                        "conclusion": None,
                        "html_url": "https://example.com/pending",
                    }
                ),
            ]
        )

        mock_gh.side_effect = [
            (True, json.dumps(merge_commit)),
            (True, check_runs),
        ]

        result = check_post_merge_ci_status("test/repo", 123)

        assert result.status == "pending"
        assert len(result.failed_checks) == 0

    @patch("pr_quality_check.run_gh_command")
    def test_check_post_merge_ci_unknown(self, mock_gh: MagicMock) -> None:
        """Test unknown CI/CD status."""
        mock_gh.return_value = (False, "error")

        result = check_post_merge_ci_status("test/repo", 123)

        assert result.status == "unknown"
        assert len(result.failed_checks) == 0
        assert len(result.failed_check_urls) == 0


class TestPRQualityAnalysis:
    """Test PR quality analysis logic."""

    def _create_mock_pr(
        self,
        body: str = "",
        additions: int = 50,
        deletions: int = 20,
        changed_files: int = 3,
        reviews: list[dict[str, str]] | None = None,
        labels: list[dict[str, str]] | None = None,
    ) -> dict[str, any]:
        """Create mock PR data for testing."""
        return {
            "number": 123,
            "title": "Test PR",
            "url": "https://github.com/test/repo/pull/123",
            "mergedAt": "2025-08-01T12:00:00Z",
            "body": body,
            "additions": additions,
            "deletions": deletions,
            "changedFiles": changed_files,
            "reviews": reviews or [],
            "labels": labels or [],
            "author": {"login": "testuser"},
            "mergedBy": {"login": "reviewer"},
        }

    @patch("pr_quality_check.get_pr_diff_stats")
    @patch("pr_quality_check.check_post_merge_ci_status")
    def test_analyze_pr_quality_high_quality(self, mock_ci: MagicMock, mock_diff: MagicMock) -> None:
        """Test analysis of high-quality PR."""
        pr = self._create_mock_pr(
            body="## Summary\nDetailed description with multiple sections.\n\n## Testing\nTested thoroughly.\n\nJIRA: PROJ-123",
            additions=30,
            deletions=10,
            changed_files=2,
            reviews=[{"state": "APPROVED"}],
            labels=[{"name": "feature"}],
        )

        mock_diff.return_value = {"test_files": 1, "code_files": 1, "files": []}
        mock_ci.return_value = CICheckResult(
            status="success",
            has_build_check=True,
            has_test_check=True,
        )

        result = analyze_pr_quality(pr, "test/repo")

        assert result.quality_score >= 80
        assert result.grade in ("A", "B")
        assert result.has_description is True
        assert result.has_testing_section is True
        assert result.has_jira_reference is True
        assert result.has_approval is True

    @patch("pr_quality_check.get_pr_diff_stats")
    @patch("pr_quality_check.check_post_merge_ci_status")
    def test_analyze_pr_quality_low_quality(self, mock_ci: MagicMock, mock_diff: MagicMock) -> None:
        """Test analysis of low-quality PR."""
        pr = self._create_mock_pr(
            body="",  # No description
            additions=600,
            deletions=400,
            changed_files=30,
            reviews=[],  # No reviews
            labels=[],  # No labels
        )

        mock_diff.return_value = {"test_files": 0, "code_files": 10, "files": []}
        mock_ci.return_value = CICheckResult(
            status="failure",
            failed_checks=["test"],
            failed_check_urls=["https://example.com/fail"],
        )

        result = analyze_pr_quality(pr, "test/repo")

        assert result.quality_score < 60
        assert result.grade == "F"
        assert result.has_description is False
        assert result.has_testing_section is False
        assert result.has_jira_reference is False
        assert result.has_approval is False
        assert result.has_post_merge_failure is True
        assert "CRITICAL" in " ".join(result.issues)

    @patch("pr_quality_check.get_pr_diff_stats")
    @patch("pr_quality_check.check_post_merge_ci_status")
    def test_analyze_pr_quality_medium_quality(self, mock_ci: MagicMock, mock_diff: MagicMock) -> None:
        """Test analysis of medium-quality PR."""
        pr = self._create_mock_pr(
            body="Brief description that is over 50 chars but under 100. ## Testing\nManually tested the changes.",
            additions=150,
            deletions=50,
            changed_files=8,
            reviews=[{"state": "APPROVED"}],
        )

        mock_diff.return_value = {"test_files": 0, "code_files": 5, "files": []}
        mock_ci.return_value = CICheckResult(
            status="success",
            has_build_check=True,
            has_test_check=True,
        )

        result = analyze_pr_quality(pr, "test/repo")

        # With testing section but no test files: testing_score = 70
        # description: 60, testing: 70, size: 90, review: 100, traceability: 30
        # Overall: 60*0.25 + 70*0.25 + 90*0.20 + 100*0.20 + 30*0.10 = 15 + 17.5 + 18 + 20 + 3 = 73.5
        assert 70 <= result.quality_score < 80
        assert result.grade == "C"

    @patch("pr_quality_check.get_pr_diff_stats")
    @patch("pr_quality_check.check_post_merge_ci_status")
    def test_analyze_pr_quality_self_merged(self, mock_ci: MagicMock, mock_diff: MagicMock) -> None:
        """Test analysis of self-merged PR without review."""
        pr = self._create_mock_pr(
            body="Good description with testing info",
        )
        pr["mergedBy"] = {"login": "testuser"}  # Same as author
        pr["reviews"] = []  # No reviews

        mock_diff.return_value = {"test_files": 1, "code_files": 1, "files": []}
        mock_ci.return_value = CICheckResult(
            status="success",
            has_build_check=True,
            has_test_check=True,
        )

        result = analyze_pr_quality(pr, "test/repo")

        assert result.is_self_merged is True
        assert "Self-merged without review" in " ".join(result.issues)
        assert result.review_score == 0


class TestReportGeneration:
    """Test report generation."""

    @patch("pr_quality_check.get_prs_reviewed_by_user")
    @patch("pr_quality_check.get_user_prs")
    @patch("pr_quality_check.analyze_pr_quality")
    def test_generate_report_basic(
        self,
        mock_analyze: MagicMock,
        mock_get_prs: MagicMock,
        mock_reviewed: MagicMock,
    ) -> None:
        """Test basic report generation."""
        # Mock PR data
        mock_prs = [
            {"number": 1, "title": "PR 1"},
            {"number": 2, "title": "PR 2"},
        ]
        mock_get_prs.return_value = mock_prs
        mock_reviewed.return_value = 10

        # Mock quality checks
        mock_analyze.side_effect = [
            PRQualityCheck(
                pr_number=1,
                title="PR 1",
                url="https://github.com/test/repo/pull/1",
                merged_at="2025-08-01T12:00:00Z",
                additions=50,
                deletions=20,
                changed_files=3,
                quality_score=85,
                grade="B",
                issues=[],
                strengths=["Good PR"],
            ),
            PRQualityCheck(
                pr_number=2,
                title="PR 2",
                url="https://github.com/test/repo/pull/2",
                merged_at="2025-08-02T12:00:00Z",
                additions=30,
                deletions=10,
                changed_files=2,
                quality_score=55,
                grade="F",
                issues=["Bad PR"],
                strengths=[],
                has_post_merge_failure=True,
            ),
        ]

        report = generate_report(
            username="testuser",
            repo="test/repo",
            start_date="2025-07-01",
            end_date="2026-06-30",
        )

        assert report.github_username == "testuser"
        assert report.total_prs_merged == 2
        assert report.total_prs_reviewed == 10
        assert report.prs_analyzed == 2
        assert report.average_quality_score == 70.0
        assert report.prs_below_threshold == 1
        assert report.prs_with_post_merge_failures == 1

    @patch("pr_quality_check.get_prs_reviewed_by_user")
    @patch("pr_quality_check.get_user_prs")
    def test_generate_report_empty(self, mock_get_prs: MagicMock, mock_reviewed: MagicMock) -> None:
        """Test report generation with no PRs."""
        mock_get_prs.return_value = []
        mock_reviewed.return_value = 0

        report = generate_report(
            username="testuser",
            repo=None,
            start_date="2025-07-01",
            end_date="2026-06-30",
        )

        assert report.total_prs_merged == 0
        assert report.prs_analyzed == 0
        assert report.average_quality_score == 0


class TestDataClasses:
    """Test dataclass structures."""

    def test_pr_quality_check_defaults(self) -> None:
        """Test PRQualityCheck default values."""
        pr = PRQualityCheck(
            pr_number=123,
            title="Test",
            url="https://github.com/test/repo/pull/123",
            merged_at="2025-08-01T12:00:00Z",
            additions=50,
            deletions=20,
            changed_files=3,
        )

        assert pr.pr_number == 123
        assert pr.has_description is False
        assert pr.quality_score == 0
        assert pr.grade == "F"
        assert len(pr.issues) == 0
        assert len(pr.post_merge_failed_checks) == 0
        assert len(pr.post_merge_failed_check_urls) == 0

    def test_pr_quality_report_structure(self) -> None:
        """Test PRQualityReport structure."""
        report = PRQualityReport(
            github_username="testuser",
            repository="test/repo",
            date_range="2025-07-01 to 2026-06-30",
            total_prs_merged=5,
            total_prs_reviewed=15,
            prs_analyzed=5,
            average_quality_score=75.0,
            prs_below_threshold=2,
            prs_with_post_merge_failures=1,
            quality_threshold=70,
        )

        assert report.github_username == "testuser"
        assert report.total_prs_merged == 5
        assert report.total_prs_reviewed == 15
        assert len(report.prs) == 0
        assert isinstance(report.summary, dict)
        assert isinstance(report.dimension_scores, dict)

    def test_dimension_score_structure(self) -> None:
        """Test DimensionScore structure."""
        dim_score = DimensionScore(
            average_score=85.5,
            grade="B",
            grade_distribution={
                "A (90-100)": 2,
                "B (80-89)": 5,
                "C (70-79)": 3,
                "D (60-69)": 1,
                "F (<60)": 0,
            },
        )

        assert dim_score.average_score == 85.5
        assert dim_score.grade == "B"
        assert dim_score.grade_distribution["B (80-89)"] == 5
        assert sum(dim_score.grade_distribution.values()) == 11


class TestDimensionScoring:
    """Test dimension scoring functionality."""

    def _create_mock_pr_check(self, scores: dict[str, int]) -> PRQualityCheck:
        """Create a mock PRQualityCheck with specified dimension scores."""
        return PRQualityCheck(
            pr_number=1,
            title="Test",
            url="https://github.com/test/repo/pull/1",
            merged_at="2025-08-01T12:00:00Z",
            additions=50,
            deletions=20,
            changed_files=3,
            description_score=scores.get("description", 0),
            testing_score=scores.get("testing", 0),
            size_score=scores.get("size", 0),
            review_score=scores.get("review", 0),
            traceability_score=scores.get("traceability", 0),
            post_merge_score=scores.get("post_merge", 0),
        )

    def test_calculate_dimension_score_empty_list(self) -> None:
        """Test dimension score calculation with empty PR list."""
        result = calculate_dimension_score([], "description", "description_score")

        assert result.average_score == 0.0
        assert result.grade == "F"
        assert len(result.grade_distribution) == 0

    def test_calculate_dimension_score_all_a(self) -> None:
        """Test dimension score calculation with all A grades."""
        prs = [
            self._create_mock_pr_check({"description": 95}),
            self._create_mock_pr_check({"description": 92}),
            self._create_mock_pr_check({"description": 90}),
        ]

        result = calculate_dimension_score(prs, "description", "description_score")

        assert result.average_score == 92.3
        assert result.grade == "A"
        assert result.grade_distribution["A (90-100)"] == 3
        assert result.grade_distribution["B (80-89)"] == 0
        assert result.grade_distribution["F (<60)"] == 0

    def test_calculate_dimension_score_mixed_grades(self) -> None:
        """Test dimension score calculation with mixed grades."""
        prs = [
            self._create_mock_pr_check({"testing": 95}),  # A
            self._create_mock_pr_check({"testing": 85}),  # B
            self._create_mock_pr_check({"testing": 75}),  # C
            self._create_mock_pr_check({"testing": 65}),  # D
            self._create_mock_pr_check({"testing": 45}),  # F
        ]

        result = calculate_dimension_score(prs, "testing", "testing_score")

        # Average: (95 + 85 + 75 + 65 + 45) / 5 = 73
        assert result.average_score == 73.0
        assert result.grade == "C"
        assert result.grade_distribution["A (90-100)"] == 1
        assert result.grade_distribution["B (80-89)"] == 1
        assert result.grade_distribution["C (70-79)"] == 1
        assert result.grade_distribution["D (60-69)"] == 1
        assert result.grade_distribution["F (<60)"] == 1

    def test_calculate_dimension_score_boundary_cases(self) -> None:
        """Test dimension score calculation at grade boundaries."""
        prs = [
            self._create_mock_pr_check({"size": 90}),  # A (at boundary)
            self._create_mock_pr_check({"size": 89}),  # B (just below A)
            self._create_mock_pr_check({"size": 80}),  # B (at boundary)
            self._create_mock_pr_check({"size": 79}),  # C (just below B)
            self._create_mock_pr_check({"size": 70}),  # C (at boundary)
            self._create_mock_pr_check({"size": 69}),  # D (just below C)
            self._create_mock_pr_check({"size": 60}),  # D (at boundary)
            self._create_mock_pr_check({"size": 59}),  # F (just below D)
        ]

        result = calculate_dimension_score(prs, "size", "size_score")

        # Average: (90 + 89 + 80 + 79 + 70 + 69 + 60 + 59) / 8 = 74.5
        assert result.average_score == 74.5
        assert result.grade == "C"
        assert result.grade_distribution["A (90-100)"] == 1
        assert result.grade_distribution["B (80-89)"] == 2
        assert result.grade_distribution["C (70-79)"] == 2
        assert result.grade_distribution["D (60-69)"] == 2
        assert result.grade_distribution["F (<60)"] == 1

    @patch("pr_quality_check.get_prs_reviewed_by_user")
    @patch("pr_quality_check.get_user_prs")
    @patch("pr_quality_check.analyze_pr_quality")
    def test_generate_report_includes_dimension_scores(
        self,
        mock_analyze: MagicMock,
        mock_get_prs: MagicMock,
        mock_reviewed: MagicMock,
    ) -> None:
        """Test that generate_report includes dimension scores."""
        mock_prs = [{"number": 1, "title": "PR 1"}]
        mock_get_prs.return_value = mock_prs
        mock_reviewed.return_value = 5

        mock_analyze.return_value = PRQualityCheck(
            pr_number=1,
            title="PR 1",
            url="https://github.com/test/repo/pull/1",
            merged_at="2025-08-01T12:00:00Z",
            additions=50,
            deletions=20,
            changed_files=3,
            description_score=80,
            testing_score=75,
            size_score=90,
            review_score=85,
            traceability_score=70,
            post_merge_score=100,
            quality_score=80,
            grade="B",
        )

        report = generate_report(
            username="testuser",
            repo="test/repo",
            start_date="2025-07-01",
            end_date="2026-06-30",
        )

        # Verify dimension_scores exists and has all 6 dimensions
        assert "dimension_scores" in report.__dict__
        assert len(report.dimension_scores) == 6
        assert "description" in report.dimension_scores
        assert "testing" in report.dimension_scores
        assert "size" in report.dimension_scores
        assert "review" in report.dimension_scores
        assert "traceability" in report.dimension_scores
        assert "post_merge" in report.dimension_scores

        # Verify each dimension has correct structure
        for dimension_name, dimension_score in report.dimension_scores.items():
            assert isinstance(dimension_score, DimensionScore)
            assert isinstance(dimension_score.average_score, float)
            assert dimension_score.grade in ("A", "B", "C", "D", "F")
            assert isinstance(dimension_score.grade_distribution, dict)


class TestOutputFormats:
    """Test different output format options."""

    @patch("pr_quality_check.get_prs_reviewed_by_user")
    @patch("pr_quality_check.get_user_prs")
    @patch("pr_quality_check.analyze_pr_quality")
    @patch("builtins.print")
    def test_markdown_format_output(
        self,
        mock_print: MagicMock,
        mock_analyze: MagicMock,
        mock_get_prs: MagicMock,
        mock_reviewed: MagicMock,
    ) -> None:
        """Test markdown format output generation."""
        from pr_quality_check import main
        from unittest.mock import patch
        import sys

        # Mock PR data
        mock_prs = [{"number": 1, "title": "Test PR"}]
        mock_get_prs.return_value = mock_prs
        mock_reviewed.return_value = 5

        mock_analyze.return_value = PRQualityCheck(
            pr_number=1,
            title="Test PR",
            url="https://github.com/test/repo/pull/1",
            merged_at="2025-08-01T12:00:00Z",
            additions=50,
            deletions=20,
            changed_files=3,
            description_score=80,
            testing_score=75,
            size_score=90,
            review_score=85,
            traceability_score=70,
            post_merge_score=100,
            quality_score=80,
            grade="B",
        )

        # Mock command line arguments
        test_args = [
            "pr_quality_check.py",
            "testuser",
            "--repo",
            "test/repo",
            "--format",
            "markdown",
            "--start",
            "2025-07-01",
            "--end",
            "2026-06-30",
        ]

        with patch.object(sys, "argv", test_args):
            main()

        # Verify markdown output was generated
        printed_output = "\n".join(str(call[0][0]) for call in mock_print.call_args_list)

        # Check for key markdown elements
        assert "# PR Quality Report:" in printed_output
        assert "## Activity Stats" in printed_output
        assert "## Quality Metrics" in printed_output
        assert "## Grade Distribution" in printed_output
        assert "## Dimension Scores & Grades" in printed_output
        assert "| Dimension | Score | Grade |" in printed_output
        assert "## Post-Merge CI/CD Status" in printed_output
        assert "## Most Common Issues" in printed_output

        # Check for proper markdown formatting
        assert "**Repository:**" in printed_output
        assert "**Date Range:**" in printed_output
        assert "|-------|" in printed_output  # Table separator

    @patch("pr_quality_check.get_prs_reviewed_by_user")
    @patch("pr_quality_check.get_user_prs")
    @patch("pr_quality_check.analyze_pr_quality")
    @patch("builtins.print")
    def test_json_format_output(
        self,
        mock_print: MagicMock,
        mock_analyze: MagicMock,
        mock_get_prs: MagicMock,
        mock_reviewed: MagicMock,
    ) -> None:
        """Test JSON format output generation."""
        from pr_quality_check import main
        from unittest.mock import patch
        import sys

        # Mock PR data
        mock_prs = [{"number": 1, "title": "Test PR"}]
        mock_get_prs.return_value = mock_prs
        mock_reviewed.return_value = 5

        mock_analyze.return_value = PRQualityCheck(
            pr_number=1,
            title="Test PR",
            url="https://github.com/test/repo/pull/1",
            merged_at="2025-08-01T12:00:00Z",
            additions=50,
            deletions=20,
            changed_files=3,
            description_score=80,
            testing_score=75,
            size_score=90,
            review_score=85,
            traceability_score=70,
            post_merge_score=100,
            quality_score=80,
            grade="B",
        )

        # Mock command line arguments
        test_args = [
            "pr_quality_check.py",
            "testuser",
            "--repo",
            "test/repo",
            "--format",
            "json",
            "--start",
            "2025-07-01",
            "--end",
            "2026-06-30",
        ]

        with patch.object(sys, "argv", test_args):
            main()

        # Verify JSON output was generated
        printed_output = "\n".join(str(call[0][0]) for call in mock_print.call_args_list)

        # Check that it looks like JSON
        assert "{" in printed_output
        assert '"github_username"' in printed_output or "'github_username'" in printed_output
        assert '"dimension_scores"' in printed_output or "'dimension_scores'" in printed_output


class TestOutputFile:
    """Test output file functionality."""

    @patch("pr_quality_check.get_prs_reviewed_by_user")
    @patch("pr_quality_check.get_user_prs")
    @patch("pr_quality_check.analyze_pr_quality")
    def test_output_to_file(
        self,
        mock_analyze: MagicMock,
        mock_get_prs: MagicMock,
        mock_reviewed: MagicMock,
    ) -> None:
        """Test writing output to a file."""
        import tempfile
        import os
        from pr_quality_check import main
        from unittest.mock import patch
        import sys

        # Mock PR data
        mock_prs = [{"number": 1, "title": "Test PR"}]
        mock_get_prs.return_value = mock_prs
        mock_reviewed.return_value = 5

        mock_analyze.return_value = PRQualityCheck(
            pr_number=1,
            title="Test PR",
            url="https://github.com/test/repo/pull/1",
            merged_at="2025-08-01T12:00:00Z",
            additions=50,
            deletions=20,
            changed_files=3,
            description_score=80,
            testing_score=75,
            size_score=90,
            review_score=85,
            traceability_score=70,
            post_merge_score=100,
            quality_score=80,
            grade="B",
        )

        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
            output_file = tmp.name

        try:
            # Mock command line arguments with output file
            test_args = [
                "pr_quality_check.py",
                "testuser",
                "--repo",
                "test/repo",
                "--format",
                "summary",
                "--output",
                output_file,
                "--start",
                "2025-07-01",
                "--end",
                "2026-06-30",
            ]

            with patch.object(sys, "argv", test_args):
                main()

            # Verify file was created and contains output
            assert os.path.exists(output_file)
            with open(output_file, "r") as f:
                content = f.read()

            # Check for key output elements
            assert "PR QUALITY REPORT: testuser" in content
            assert "ACTIVITY STATS:" in content
            assert "QUALITY METRICS:" in content
            assert "DIMENSION SCORES & GRADES" in content

        finally:
            # Clean up temporary file
            if os.path.exists(output_file):
                os.remove(output_file)

    @patch("pr_quality_check.get_prs_reviewed_by_user")
    @patch("pr_quality_check.get_user_prs")
    @patch("pr_quality_check.analyze_pr_quality")
    def test_json_output_to_file(
        self,
        mock_analyze: MagicMock,
        mock_get_prs: MagicMock,
        mock_reviewed: MagicMock,
    ) -> None:
        """Test writing JSON output to a file."""
        import tempfile
        import os
        from pr_quality_check import main
        from unittest.mock import patch
        import sys

        # Mock PR data
        mock_prs = [{"number": 1, "title": "Test PR"}]
        mock_get_prs.return_value = mock_prs
        mock_reviewed.return_value = 5

        mock_analyze.return_value = PRQualityCheck(
            pr_number=1,
            title="Test PR",
            url="https://github.com/test/repo/pull/1",
            merged_at="2025-08-01T12:00:00Z",
            additions=50,
            deletions=20,
            changed_files=3,
            description_score=80,
            testing_score=75,
            size_score=90,
            review_score=85,
            traceability_score=70,
            post_merge_score=100,
            quality_score=80,
            grade="B",
        )

        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as tmp:
            output_file = tmp.name

        try:
            # Mock command line arguments with output file
            test_args = [
                "pr_quality_check.py",
                "testuser",
                "--repo",
                "test/repo",
                "--format",
                "json",
                "--output",
                output_file,
                "--start",
                "2025-07-01",
                "--end",
                "2026-06-30",
            ]

            with patch.object(sys, "argv", test_args):
                main()

            # Verify file was created and contains valid JSON
            assert os.path.exists(output_file)
            with open(output_file, "r") as f:
                content = f.read()
                data = json.loads(content)

            # Check JSON structure
            assert data["github_username"] == "testuser"
            assert "dimension_scores" in data
            assert "post_merge" in data["dimension_scores"]

        finally:
            # Clean up temporary file
            if os.path.exists(output_file):
                os.remove(output_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
