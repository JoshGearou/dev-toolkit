#!/usr/bin/env python3
"""
PR Quality Check - Fetch and analyze GitHub PRs for quality assessment.

This script fetches merged PRs for a given GitHub user within a date range
and performs comprehensive quality checks including:
- Description quality and structure
- Testing evidence and test coverage
- PR size and reviewability
- Review coverage and approval status
- Traceability (JIRA references, labels)
- Post-merge CI/CD status and failures

The script also counts total PRs merged and reviewed by the user.
Output is human-readable summary by default, or JSON for agent consumption.

Defaults:
    Repository: ALL accessible repositories (use --repo to filter)
    Date Range: Current Microsoft fiscal year (FY26 = 2025-07-01 to 2026-06-30)
    Format: Human-readable summary (use --format json for machine parsing)

Usage:
    python3 pr_quality_check.py <github_username> [--repo REPO] [--start DATE] [--end DATE] [--format FORMAT] [--verbose]

Examples:
    python3 pr_quality_check.py {gh-username}
    python3 pr_quality_check.py {gh-username} --repo {gh-org-name}/{repo-name}
    python3 pr_quality_check.py {gh-username} --start 2025-01-01 --end 2025-12-31
    python3 pr_quality_check.py {gh-username} --format json
    python3 pr_quality_check.py {gh-username} --verbose  # Show all issues with PR links
"""

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

try:
    from scm_policy_rules import (
        CheckResult as SCMCheckResult,
        PRInfo as SCMPRInfo,
        run_all_checks as run_scm_checks,
    )
    _HAS_SCM_RULES = True
except ImportError:
    _HAS_SCM_RULES = False


@dataclass
class PRQualityCheck:
    """Quality check results for a single PR."""

    pr_number: int
    title: str
    url: str
    merged_at: str
    additions: int
    deletions: int
    changed_files: int

    # Quality checks (True = passes, False = fails)
    has_description: bool = False
    description_length: int = 0
    has_testing_section: bool = False
    has_jira_reference: bool = False
    has_tests_in_diff: bool = False
    code_to_test_ratio: float = 0.0

    # Size metrics
    total_changes: int = 0
    size_category: str = "unknown"  # small, medium, large, xlarge

    # Review metrics
    review_count: int = 0
    has_approval: bool = False
    is_self_merged: bool = False

    # Post-merge metrics
    post_merge_ci_status: str = "unknown"  # success, failure, pending, unknown, no_ci
    post_merge_failed_checks: list[str] = field(default_factory=list)
    post_merge_failed_check_urls: list[str] = field(default_factory=list)
    has_post_merge_failure: bool = False
    has_build_check: bool = False
    has_test_check: bool = False
    has_no_ci: bool = False
    ci_check_names: list[str] = field(default_factory=list)
    build_evidence: str = ""  # Where build was detected (job or step)
    test_evidence: str = ""  # Where test was detected (job or step)

    # Metadata
    labels: list[str] = field(default_factory=list)
    author: str = ""

    # SCM Policy metrics
    scm_checks_passed: int = 0
    scm_checks_total: int = 0
    scm_check_details: list[str] = field(default_factory=list)
    scm_policy_score: int = 0

    # Quality scores by category (0-100 each)
    description_score: int = 0
    testing_score: int = 0
    size_score: int = 0
    review_score: int = 0
    traceability_score: int = 0
    post_merge_score: int = 0

    # Overall quality score (0-100)
    quality_score: int = 0
    grade: str = "F"  # A, B, C, D, F
    issues: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)


@dataclass
class DimensionScore:
    """Scoring and grading for a single quality dimension."""

    average_score: float
    grade: str
    grade_distribution: dict[str, int] = field(default_factory=dict)


@dataclass
class PRQualityReport:
    """Complete quality report for a user's PRs."""

    github_username: str
    repository: str
    date_range: str
    total_prs_merged: int  # Total PRs merged by the user
    total_prs_reviewed: int  # Total PRs reviewed by the user
    prs_analyzed: int
    average_quality_score: float
    prs_below_threshold: int
    prs_with_post_merge_failures: int  # PRs that failed CI/CD after merge
    quality_threshold: int
    prs: list[PRQualityCheck] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    dimension_scores: dict[str, DimensionScore] = field(default_factory=dict)


def run_gh_command(args: list[str], max_retries: int = 20) -> tuple[bool, str]:
    """Run a gh CLI command with exponential backoff retry on rate limits.

    Retries up to 1 hour total wait time with exponential backoff capped at 5 minutes.

    Args:
        args: Command arguments to pass to gh
        max_retries: Maximum number of retries for rate limit errors (default: 20)

    Returns:
        Tuple of (success, output/error)
    """
    try:
        total_wait = 0
        max_wait_per_retry = 300  # Cap at 5 minutes per retry

        for attempt in range(max_retries):
            result = subprocess.run(["gh"] + args, capture_output=True, text=True, timeout=60, check=False)

            if result.returncode == 0:
                return True, result.stdout.strip()

            stderr = result.stderr.strip()

            # Detect rate limit errors
            if "rate limit" in stderr.lower():
                if attempt < max_retries - 1:
                    # Exponential backoff capped at 5 minutes
                    wait_time = min(2 ** (attempt + 1), max_wait_per_retry)
                    total_wait += wait_time

                    mins = wait_time // 60
                    secs = wait_time % 60
                    wait_str = f"{mins}m{secs}s" if mins > 0 else f"{secs}s"

                    print(
                        f"⚠ Rate limit hit, waiting {wait_str} (total waited: {total_wait//60}m{total_wait%60}s) - retry {attempt + 2}/{max_retries}..."
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    mins = total_wait // 60
                    return (
                        False,
                        f"{stderr}\n\n⚠ Rate limit exceeded after {max_retries} retries (waited total: {mins}m).\n   GitHub rate limits reset after 1 hour.\n   Check remaining quota: gh api rate_limit",
                    )

            # Non-rate-limit error - don't retry
            return False, stderr

        return False, "Max retries exceeded"
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except FileNotFoundError:
        return False, "gh CLI not found. Install with: brew install gh"


def get_user_prs(username: str, repo: str | None, start_date: str, end_date: str) -> list[dict[str, Any]]:
    """Fetch merged PRs for a user in the given date range.

    Args:
        username: GitHub username to search for
        repo: Repository to search (owner/repo format), or None to search all repos
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        List of PR dictionaries with metadata
    """
    prs: list[dict[str, Any]] = []

    if repo:
        # Search specific repository using gh pr list
        success, output = run_gh_command(
            [
                "pr",
                "list",
                "--repo",
                repo,
                "--author",
                username,
                "--state",
                "merged",
                "--limit",
                "100",
                "--json",
                "number,title,url,mergedAt,additions,deletions,changedFiles,labels,body,reviews,commits,author,mergedBy",
            ]
        )

        if not success:
            print(f"Error fetching PRs: {output}", file=sys.stderr)
            return []

        try:
            all_prs = json.loads(output)
        except json.JSONDecodeError as e:
            print(f"Error parsing PR list: {e}", file=sys.stderr)
            return []

        # Filter by date range
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)

        for pr in all_prs:
            if not pr.get("mergedAt"):
                continue
            merged_at = datetime.fromisoformat(pr["mergedAt"].replace("Z", "+00:00"))
            if start_dt <= merged_at.replace(tzinfo=None) <= end_dt:
                prs.append(pr)
    else:
        # Search across all repositories using gh search (gets basic PR info)
        success, output = run_gh_command(
            [
                "search",
                "prs",
                "--author",
                username,
                "--merged",
                f"merged:{start_date}..{end_date}",
                "--limit",
                "1000",
                "--json",
                "number,repository,url",
            ]
        )

        if not success:
            print(f"Error fetching PRs: {output}", file=sys.stderr)
            return []

        try:
            search_results = json.loads(output)
        except json.JSONDecodeError as e:
            print(f"Error parsing PR search results: {e}", file=sys.stderr)
            return []

        # Fetch full details for each PR
        print(f"Found {len(search_results)} PRs, fetching details...", file=sys.stderr)
        for pr_data in search_results:
            pr_number = pr_data.get("number")
            repo_info = pr_data.get("repository", {})
            repo_name = repo_info.get("nameWithOwner", "unknown")

            if not pr_number or not repo_name:
                continue

            # Fetch full PR details
            success, pr_output = run_gh_command(
                [
                    "pr",
                    "view",
                    str(pr_number),
                    "--repo",
                    repo_name,
                    "--json",
                    "number,title,url,mergedAt,additions,deletions,changedFiles,labels,body,reviews,commits,author,mergedBy",
                ]
            )

            if success:
                try:
                    pr_details = json.loads(pr_output)
                    pr_details["repo_name"] = repo_name
                    prs.append(pr_details)
                except json.JSONDecodeError:
                    continue

    return prs


def get_pr_diff_stats(repo: str, pr_number: int) -> dict[str, Any]:
    """Get diff statistics for a PR to check for test files."""
    success, output = run_gh_command(["pr", "diff", str(pr_number), "--repo", repo, "--name-only"])

    if not success:
        return {"test_files": 0, "code_files": 0, "files": []}

    files = output.strip().split("\n") if output.strip() else []
    test_files = [f for f in files if "test" in f.lower() or "spec" in f.lower() or "__tests__" in f.lower()]
    code_files = [
        f
        for f in files
        if f.endswith((".py", ".java", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go")) and f not in test_files
    ]

    return {"test_files": len(test_files), "code_files": len(code_files), "files": files}


def get_prs_reviewed_by_user(username: str, repo: str | None, start_date: str, end_date: str) -> int:
    """Count PRs reviewed by the user in the given date range.

    Excludes PRs authored by the user (only counts reviews on others' PRs).

    Args:
        username: GitHub username
        repo: Repository to search (owner/repo format), or None to search all repos
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Count of PRs reviewed by the user (excluding self-authored PRs)
    """
    # Search for PRs reviewed by the user using gh search
    cmd = [
        "search",
        "prs",
        "--reviewed-by",
        username,
        "--merged",
        f"merged:{start_date}..{end_date}",
        "--limit",
        "1000",
        "--json",
        "number,author",  # Include author to filter out self-authored PRs
    ]

    # Add repo filter only if specified
    if repo:
        cmd.extend(["--repo", repo])

    success, output = run_gh_command(cmd)

    if not success:
        print(f"Warning: Could not fetch reviewed PRs: {output}", file=sys.stderr)
        return 0

    try:
        reviewed_prs = json.loads(output)
        # Filter out PRs authored by the user
        other_prs = [pr for pr in reviewed_prs if pr.get("author", {}).get("login") != username]
        return len(other_prs)
    except json.JSONDecodeError as e:
        print(f"Error parsing reviewed PRs: {e}", file=sys.stderr)
        return 0


@dataclass
class CICheckResult:
    """Result of CI check analysis."""

    status: str  # success, failure, pending, unknown, no_ci
    failed_checks: list[str] = field(default_factory=list)
    failed_check_urls: list[str] = field(default_factory=list)
    check_names: list[str] = field(default_factory=list)
    has_build_check: bool = False
    has_test_check: bool = False
    build_evidence: str = ""  # Where build was detected (job name or step name)
    test_evidence: str = ""  # Where test was detected (job name or step name)


# Patterns to identify build checks (case-insensitive)
BUILD_CHECK_PATTERNS = [
    "build",
    "compile",
    "make",
    "gradle",
    "maven",
    "cargo",
    "npm run build",
    "yarn build",
    "webpack",
    "tsc",
    "javac",
    "gcc",
    "cmake",
    "bazel",
]

# Patterns to identify test checks (case-insensitive)
TEST_CHECK_PATTERNS = [
    "test",
    "spec",
    "jest",
    "pytest",
    "junit",
    "mocha",
    "karma",
    "cypress",
    "selenium",
    "unittest",
    "rspec",
    "minitest",
    "coverage",
    "e2e",
]


def get_job_steps(repo: str, job_id: int) -> list[str]:
    """Fetch step names for a specific job.

    Args:
        repo: Repository in owner/repo format
        job_id: GitHub Actions job ID

    Returns:
        List of step names for the job
    """
    success, output = run_gh_command(
        [
            "api",
            f"repos/{repo}/actions/jobs/{job_id}",
            "--jq",
            ".steps[].name",
        ]
    )

    if not success:
        return []

    return [line.strip() for line in output.strip().split("\n") if line.strip()]


def check_steps_for_build_test(repo: str, job_id: int) -> tuple[bool, bool, str, str]:
    """Check job steps for build/test patterns.

    Args:
        repo: Repository in owner/repo format
        job_id: GitHub Actions job ID

    Returns:
        Tuple of (has_build, has_test, build_evidence, test_evidence)
    """
    steps = get_job_steps(repo, job_id)
    has_build = False
    has_test = False
    build_evidence = ""
    test_evidence = ""

    for step_name in steps:
        step_lower = step_name.lower()

        if not has_build and any(p in step_lower for p in BUILD_CHECK_PATTERNS):
            has_build = True
            build_evidence = f"step: {step_name}"

        if not has_test and any(p in step_lower for p in TEST_CHECK_PATTERNS):
            has_test = True
            test_evidence = f"step: {step_name}"

        if has_build and has_test:
            break

    return has_build, has_test, build_evidence, test_evidence


def check_post_merge_ci_status(repo: str, pr_number: int) -> CICheckResult:
    """Check CI/CD status after PR merge.

    Returns:
        CICheckResult with status, failed checks, and check type detection.
        Status is one of:
        - "success": All checks passed
        - "failure": One or more checks failed
        - "pending": Checks still running
        - "no_ci": No CI checks found (this is a problem!)
        - "unknown": Could not determine status (API error)
    """
    # Get PR details to find the merge commit
    success, output = run_gh_command(
        [
            "pr",
            "view",
            str(pr_number),
            "--repo",
            repo,
            "--json",
            "mergeCommit",
        ]
    )

    if not success:
        return CICheckResult(status="unknown")

    try:
        pr_data = json.loads(output)
        merge_commit = pr_data.get("mergeCommit", {})
        if not merge_commit or "oid" not in merge_commit:
            return CICheckResult(status="unknown")

        commit_sha = merge_commit["oid"]
    except (json.JSONDecodeError, KeyError):
        return CICheckResult(status="unknown")

    # Get check runs for the merge commit (include id for step lookup)
    success, output = run_gh_command(
        [
            "api",
            f"repos/{repo}/commits/{commit_sha}/check-runs",
            "--jq",
            ".check_runs[] | {id, name, conclusion, status, html_url}",
        ]
    )

    if not success:
        return CICheckResult(status="unknown")

    # Parse check runs
    failed_checks: list[str] = []
    failed_check_urls: list[str] = []
    check_names: list[str] = []
    job_ids: list[int] = []  # Track job IDs for step lookup
    has_pending = False
    has_checks = False
    has_build_check = False
    has_test_check = False
    build_evidence = ""
    test_evidence = ""

    for line in output.strip().split("\n"):
        if not line:
            continue
        try:
            check = json.loads(line)
            has_checks = True
            check_name = check.get("name", "unknown check")
            check_id = check.get("id")
            check_names.append(check_name)
            check_name_lower = check_name.lower()

            if check_id:
                job_ids.append(check_id)

            # Detect build checks from job name
            if not has_build_check and any(pattern in check_name_lower for pattern in BUILD_CHECK_PATTERNS):
                has_build_check = True
                build_evidence = f"job: {check_name}"

            # Detect test checks from job name
            if not has_test_check and any(pattern in check_name_lower for pattern in TEST_CHECK_PATTERNS):
                has_test_check = True
                test_evidence = f"job: {check_name}"

            # Check if still pending
            if check.get("status") != "completed":
                has_pending = True
                continue

            # Check for failures
            conclusion = check.get("conclusion", "")
            if conclusion in ("failure", "cancelled", "timed_out", "action_required"):
                failed_checks.append(check_name)
                failed_check_urls.append(check.get("html_url", ""))
        except json.JSONDecodeError:
            continue

    if not has_checks:
        return CICheckResult(status="no_ci")

    # If build or test not found in job names, check step names within jobs
    if (not has_build_check or not has_test_check) and job_ids:
        # Limit to first 5 jobs to avoid too many API calls
        for job_id in job_ids[:5]:
            if has_build_check and has_test_check:
                break

            step_build, step_test, step_build_ev, step_test_ev = check_steps_for_build_test(repo, job_id)

            if not has_build_check and step_build:
                has_build_check = True
                build_evidence = step_build_ev

            if not has_test_check and step_test:
                has_test_check = True
                test_evidence = step_test_ev

    if has_pending:
        return CICheckResult(
            status="pending",
            check_names=check_names,
            has_build_check=has_build_check,
            has_test_check=has_test_check,
            build_evidence=build_evidence,
            test_evidence=test_evidence,
        )

    if failed_checks:
        return CICheckResult(
            status="failure",
            failed_checks=failed_checks,
            failed_check_urls=failed_check_urls,
            check_names=check_names,
            has_build_check=has_build_check,
            has_test_check=has_test_check,
            build_evidence=build_evidence,
            test_evidence=test_evidence,
        )

    return CICheckResult(
        status="success",
        check_names=check_names,
        has_build_check=has_build_check,
        has_test_check=has_test_check,
        build_evidence=build_evidence,
        test_evidence=test_evidence,
    )


def get_msft_fiscal_year_dates() -> tuple[str, str, str]:
    """Calculate current Microsoft fiscal year dates.

    MSFT fiscal years run from July 1st to June 30th and are named FY{Year+1}.
    Example: FY26 runs from July 1, 2025 to June 30, 2026.

    Returns:
        Tuple of (fiscal_year_name, start_date, end_date) in YYYY-MM-DD format.
    """
    today = datetime.now()
    current_year = today.year
    current_month = today.month

    # If we're in July or later, we're in FY{current_year + 1}
    # If we're before July, we're in FY{current_year}
    if current_month >= 7:
        fiscal_year = current_year + 1
        start_year = current_year
        end_year = current_year + 1
    else:
        fiscal_year = current_year
        start_year = current_year - 1
        end_year = current_year

    fiscal_year_name = f"FY{fiscal_year % 100}"  # FY26, FY27, etc.
    start_date = f"{start_year}-07-01"
    end_date = f"{end_year}-06-30"

    return fiscal_year_name, start_date, end_date


def categorize_pr_size(additions: int, deletions: int, changed_files: int) -> str:
    """Categorize PR size based on changes."""
    total = additions + deletions
    if total <= 50 and changed_files <= 3:
        return "small"
    elif total <= 200 and changed_files <= 10:
        return "medium"
    elif total <= 500 and changed_files <= 20:
        return "large"
    else:
        return "xlarge"


def calculate_grade(score: int) -> str:
    """Convert numeric score to letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def analyze_pr_quality(pr: dict[str, Any], repo: str | None) -> PRQualityCheck:
    """Analyze a single PR for quality metrics using structured rules.

    Args:
        pr: PR data dictionary
        repo: Repository in owner/repo format, or None to extract from PR data

    Returns:
        PRQualityCheck with quality metrics and scores
    """
    body = pr.get("body", "") or ""
    labels = [label.get("name", "") for label in pr.get("labels", [])]
    reviews = pr.get("reviews", [])
    author = pr.get("author", {}).get("login", "") if pr.get("author") else ""
    additions = pr.get("additions", 0)
    deletions = pr.get("deletions", 0)
    changed_files = pr.get("changedFiles", 0)

    # Determine repo name (from parameter or PR data in all-repos mode)
    pr_repo = repo if repo else pr.get("repo_name", "unknown")

    # Get diff stats
    diff_stats = get_pr_diff_stats(pr_repo, pr["number"])

    # Size metrics
    total_changes = additions + deletions
    size_category = categorize_pr_size(additions, deletions, changed_files)

    # Review metrics
    has_approval = any(r.get("state") == "APPROVED" for r in reviews)
    # Check if merged by author (self-merge)
    merger = pr.get("mergedBy", {}).get("login", "") if pr.get("mergedBy") else ""
    is_self_merged = merger == author and len(reviews) == 0

    issues: list[str] = []
    strengths: list[str] = []

    # ========================================
    # RULE 1: Description Quality (25 points)
    # ========================================
    description_score = 100
    has_description = len(body.strip()) > 20
    description_length = len(body.strip())

    if not has_description or description_length == 0:
        description_score = 0
        issues.append("CRITICAL: Empty or missing description")
    elif description_length < 50:
        description_score = 30
        issues.append("Description too brief (< 50 chars)")
    elif description_length < 100:
        description_score = 60
        issues.append("Description minimal (< 100 chars)")
    elif description_length < 200:
        description_score = 80
    else:
        strengths.append("Detailed description provided")

    # Check for structured description (headers, bullet points)
    if "##" in body or "- " in body or "* " in body:
        description_score = min(100, description_score + 10)
        strengths.append("Well-structured description format")

    # ========================================
    # RULE 2: Testing Evidence (25 points)
    # ========================================
    testing_score = 100

    # Check for testing section in description
    testing_patterns = [
        "## test",
        "## testing",
        "### test",
        "### testing",
        "test plan",
        "how was this tested",
        "tested by",
        "unit test",
        "integration test",
        "manual test",
        "verified by",
        "tested with",
        "test coverage",
    ]
    has_testing_section = any(pattern in body.lower() for pattern in testing_patterns)

    # Check if PR has test files in diff
    has_tests_in_diff = diff_stats["test_files"] > 0

    # Code to test ratio
    total_code = diff_stats["code_files"]
    total_tests = diff_stats["test_files"]
    code_to_test_ratio = total_tests / total_code if total_code > 0 else 0.0

    # Scoring logic
    if diff_stats["code_files"] > 0:  # Only score testing for code PRs
        if not has_testing_section and not has_tests_in_diff:
            testing_score = 0
            issues.append("CRITICAL: No testing evidence (no tests in diff, no testing section)")
        elif not has_testing_section:
            testing_score = 60
            issues.append("No testing section in description")
        elif not has_tests_in_diff:
            testing_score = 70
            issues.append("No test files in PR (but testing section exists)")
        else:
            strengths.append("Tests included with code changes")
            if code_to_test_ratio >= 0.5:
                strengths.append(f"Good test coverage ratio ({code_to_test_ratio:.1f})")
    else:
        # Non-code PRs (docs, config) - testing less critical
        testing_score = 100 if has_testing_section else 80

    # ========================================
    # RULE 3: PR Size (20 points)
    # ========================================
    size_score = 100

    if size_category == "small":
        strengths.append("Appropriately sized PR (easy to review)")
    elif size_category == "medium":
        size_score = 90
    elif size_category == "large":
        size_score = 70
        issues.append(f"Large PR ({total_changes} changes, {changed_files} files)")
    else:  # xlarge
        size_score = 40
        issues.append(f"Very large PR ({total_changes} changes, {changed_files} files) - consider splitting")

    # ========================================
    # RULE 4: Review Coverage (20 points)
    # ========================================
    review_score = 100

    if is_self_merged:
        review_score = 0
        issues.append("CRITICAL: Self-merged without review")
    elif len(reviews) == 0:
        review_score = 30
        issues.append("No reviews on PR")
    elif not has_approval:
        review_score = 60
        issues.append("PR merged without explicit approval")
    else:
        strengths.append("Peer reviewed and approved")
        if len(reviews) >= 2:
            strengths.append("Multiple reviewers")

    # ========================================
    # RULE 5: Traceability (10 points)
    # ========================================
    traceability_score = 100

    # Check for JIRA reference
    jira_pattern = r"[A-Z]+-\d+"
    has_jira_in_body = bool(re.search(jira_pattern, body))
    has_jira_in_title = bool(re.search(jira_pattern, pr.get("title", "")))
    has_jira_reference = has_jira_in_body or has_jira_in_title or "jira" in body.lower()

    if not has_jira_reference:
        traceability_score = 50
        issues.append("No JIRA ticket reference")
    else:
        strengths.append("JIRA ticket referenced")

    # Check for labels (optional - no penalty if missing)
    if labels:
        strengths.append(f"Labeled: {', '.join(labels[:3])}")

    # ========================================
    # RULE 6: Post-Merge CI/CD Build & Test
    # ========================================
    # Check post-merge CI for build/test presence and results
    ci_result = check_post_merge_ci_status(pr_repo, pr["number"])
    post_merge_status = ci_result.status
    failed_checks = ci_result.failed_checks
    failed_check_urls = ci_result.failed_check_urls
    has_post_merge_failure = ci_result.status == "failure"
    has_build_check = ci_result.has_build_check
    has_test_check = ci_result.has_test_check
    has_no_ci = ci_result.status == "no_ci"
    ci_check_names = ci_result.check_names
    build_evidence = ci_result.build_evidence
    test_evidence = ci_result.test_evidence

    # Post-merge score (0-100)
    post_merge_score = 100

    # Critical: No CI at all
    if has_no_ci:
        issues.append("CRITICAL: No CI checks found on merge commit")
        testing_score = int(testing_score * 0.3)
        post_merge_score = 0
    # Critical: CI failure
    elif has_post_merge_failure:
        issues.append(f"CRITICAL: Post-merge CI/CD failure ({len(failed_checks)} checks failed)")
        testing_score = int(testing_score * 0.5)
        post_merge_score = 20
    elif post_merge_status == "success":
        strengths.append("All post-merge CI/CD checks passed")
    elif post_merge_status == "pending":
        post_merge_score = 70
    elif post_merge_status == "unknown":
        post_merge_score = 50

    # Check for missing build check (only if CI exists)
    if not has_no_ci and post_merge_status != "unknown":
        if not has_build_check:
            issues.append("Missing build check in CI pipeline")
            testing_score = int(testing_score * 0.8)
            post_merge_score = int(post_merge_score * 0.7)
        else:
            strengths.append("Build check present in CI")

        if not has_test_check:
            issues.append("Missing test check in CI pipeline")
            testing_score = int(testing_score * 0.8)
            post_merge_score = int(post_merge_score * 0.7)
        else:
            strengths.append("Test check present in CI")

    # ========================================
    # RULE 7: SCM Policy Compliance
    # ========================================
    scm_checks_passed = 0
    scm_checks_total = 0
    scm_check_details: list[str] = []
    scm_policy_score = 100  # Default: neutral when module unavailable

    if _HAS_SCM_RULES:
        # Extract reviewers and approvers from reviews
        scm_reviewers: list[str] = []
        scm_approvers: list[str] = []
        for review in reviews:
            reviewer_login = review.get("author", {}).get("login", "")
            if reviewer_login:
                scm_reviewers.append(reviewer_login)
                if review.get("state") == "APPROVED":
                    scm_approvers.append(reviewer_login)
        scm_reviewers = list(set(scm_reviewers))
        scm_approvers = list(set(scm_approvers))

        # Extract commits
        scm_commits: list[dict[str, str]] = []
        for commit in pr.get("commits", []):
            scm_commits.append(
                {
                    "sha": commit.get("oid", "")[:7],
                    "author": commit.get("authors", [{}])[0].get("login", "unknown") if commit.get("authors") else "unknown",
                    "message": commit.get("messageHeadline", ""),
                }
            )

        scm_pr_info = SCMPRInfo(
            number=pr["number"],
            author=author,
            title=pr.get("title", ""),
            state="MERGED",
            reviewers=scm_reviewers,
            approvers=scm_approvers,
            commits=scm_commits,
            files_changed=diff_stats["files"],
            files_by_category={},
            url=pr.get("url", ""),
        )

        scm_results = run_scm_checks(scm_pr_info)
        scm_checks_total = len(scm_results)
        scm_checks_passed = sum(1 for r in scm_results if r.passed)

        for r in scm_results:
            if not r.passed:
                scm_check_details.append(f"SCM Policy: {r.name} failed")
                issues.append(f"SCM Policy: {r.name} failed")

        if scm_checks_total > 0:
            scm_policy_score = int((scm_checks_passed / scm_checks_total) * 100)
        else:
            scm_policy_score = 100

    # ========================================
    # Calculate Overall Score (weighted average)
    # ========================================
    # Weights: Description 18%, Testing 18%, Size 12%, Review 18%, Traceability 9%, Post-merge 15%, SCM Policy 10%
    overall_score = int(
        description_score * 0.18
        + testing_score * 0.18
        + size_score * 0.12
        + review_score * 0.18
        + traceability_score * 0.09
        + post_merge_score * 0.15
        + scm_policy_score * 0.10
    )

    return PRQualityCheck(
        pr_number=pr["number"],
        title=pr["title"],
        url=pr["url"],
        merged_at=pr.get("mergedAt", ""),
        additions=additions,
        deletions=deletions,
        changed_files=changed_files,
        has_description=has_description,
        description_length=description_length,
        has_testing_section=has_testing_section,
        has_jira_reference=has_jira_reference,
        has_tests_in_diff=has_tests_in_diff,
        code_to_test_ratio=code_to_test_ratio,
        total_changes=total_changes,
        size_category=size_category,
        review_count=len(reviews),
        has_approval=has_approval,
        is_self_merged=is_self_merged,
        post_merge_ci_status=post_merge_status,
        post_merge_failed_checks=failed_checks,
        post_merge_failed_check_urls=failed_check_urls,
        has_post_merge_failure=has_post_merge_failure,
        has_build_check=has_build_check,
        has_test_check=has_test_check,
        has_no_ci=has_no_ci,
        ci_check_names=ci_check_names,
        build_evidence=build_evidence,
        test_evidence=test_evidence,
        labels=labels,
        author=author,
        scm_checks_passed=scm_checks_passed,
        scm_checks_total=scm_checks_total,
        scm_check_details=scm_check_details,
        scm_policy_score=scm_policy_score,
        description_score=description_score,
        testing_score=testing_score,
        size_score=size_score,
        review_score=review_score,
        traceability_score=traceability_score,
        post_merge_score=post_merge_score,
        quality_score=overall_score,
        grade=calculate_grade(overall_score),
        issues=issues,
        strengths=strengths,
    )


def normalize_issue_for_frequency(issue: str) -> str:
    """Normalize issue strings for frequency counting.

    Groups similar issues together by removing dynamic details like counts.
    Individual PRs keep the detailed issue strings.

    Args:
        issue: Original issue string with specific details

    Returns:
        Normalized issue string for grouping
    """
    # Normalize CI/CD failure messages (remove specific check counts)
    if "Post-merge CI/CD failure" in issue:
        return "CRITICAL: Post-merge CI/CD failure"

    # Normalize large PR messages (remove specific file/change counts)
    if "Large PR" in issue and "consider splitting" not in issue:
        return "Large PR - consider splitting"
    if "Very large PR" in issue:
        return "Very large PR - consider splitting"

    # Keep other issues as-is
    return issue


def calculate_dimension_score(
    prs: list[PRQualityCheck], dimension_name: str, score_attribute: str
) -> DimensionScore:
    """Calculate score and grade distribution for a single dimension.

    Args:
        prs: List of analyzed PRs
        dimension_name: Name of the dimension (for display)
        score_attribute: Name of the score attribute on PRQualityCheck

    Returns:
        DimensionScore with average score, grade, and grade distribution
    """
    if not prs:
        return DimensionScore(average_score=0.0, grade="F", grade_distribution={})

    scores = [getattr(pr, score_attribute) for pr in prs]
    average_score = sum(scores) / len(scores)

    # Calculate grade distribution
    grade_dist = {
        "A (90-100)": sum(1 for s in scores if s >= 90),
        "B (80-89)": sum(1 for s in scores if 80 <= s < 90),
        "C (70-79)": sum(1 for s in scores if 70 <= s < 80),
        "D (60-69)": sum(1 for s in scores if 60 <= s < 70),
        "F (<60)": sum(1 for s in scores if s < 60),
    }

    return DimensionScore(
        average_score=round(average_score, 1),
        grade=calculate_grade(int(average_score)),
        grade_distribution=grade_dist,
    )


def generate_report(
    username: str,
    repo: str | None,
    start_date: str,
    end_date: str,
    quality_threshold: int = 70,
) -> PRQualityReport:
    """Generate a complete quality report for a user's PRs.

    Args:
        username: GitHub username to analyze
        repo: Repository to search (owner/repo format), or None to search all repos
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        quality_threshold: Minimum quality score threshold (default: 70)

    Returns:
        PRQualityReport with comprehensive quality analysis
    """
    prs = get_user_prs(username, repo, start_date, end_date)

    # Get count of PRs reviewed by the user
    total_reviewed = get_prs_reviewed_by_user(username, repo, start_date, end_date)

    analyzed_prs: list[PRQualityCheck] = []
    for pr in prs:
        quality = analyze_pr_quality(pr, repo)
        analyzed_prs.append(quality)

    # Sort by quality score (worst first for review)
    analyzed_prs.sort(key=lambda x: x.quality_score)

    # Calculate summary stats
    total_score = sum(pr.quality_score for pr in analyzed_prs)
    avg_score = total_score / len(analyzed_prs) if analyzed_prs else 0
    below_threshold = sum(1 for pr in analyzed_prs if pr.quality_score < quality_threshold)
    post_merge_failures = sum(1 for pr in analyzed_prs if pr.has_post_merge_failure)

    # Issue frequency (normalize issues for grouping)
    issue_counts: dict[str, int] = {}
    for pr in analyzed_prs:
        for issue in pr.issues:
            normalized_issue = normalize_issue_for_frequency(issue)
            issue_counts[normalized_issue] = issue_counts.get(normalized_issue, 0) + 1

    # Calculate dimension scores and grades
    dimension_scores = {
        "description": calculate_dimension_score(analyzed_prs, "description", "description_score"),
        "testing": calculate_dimension_score(analyzed_prs, "testing", "testing_score"),
        "size": calculate_dimension_score(analyzed_prs, "size", "size_score"),
        "review": calculate_dimension_score(analyzed_prs, "review", "review_score"),
        "traceability": calculate_dimension_score(analyzed_prs, "traceability", "traceability_score"),
        "post_merge": calculate_dimension_score(analyzed_prs, "post_merge", "post_merge_score"),
        "scm_policy": calculate_dimension_score(analyzed_prs, "scm_policy", "scm_policy_score"),
    }

    return PRQualityReport(
        github_username=username,
        repository=repo if repo else "All repositories",
        date_range=f"{start_date} to {end_date}",
        total_prs_merged=len(prs),
        total_prs_reviewed=total_reviewed,
        prs_analyzed=len(analyzed_prs),
        average_quality_score=round(avg_score, 1),
        prs_below_threshold=below_threshold,
        prs_with_post_merge_failures=post_merge_failures,
        quality_threshold=quality_threshold,
        prs=analyzed_prs,
        dimension_scores=dimension_scores,
        summary={
            "issue_frequency": issue_counts,
            "grade_distribution": {
                "A (90-100)": sum(1 for pr in analyzed_prs if pr.grade == "A"),
                "B (80-89)": sum(1 for pr in analyzed_prs if pr.grade == "B"),
                "C (70-79)": sum(1 for pr in analyzed_prs if pr.grade == "C"),
                "D (60-69)": sum(1 for pr in analyzed_prs if pr.grade == "D"),
                "F (<60)": sum(1 for pr in analyzed_prs if pr.grade == "F"),
            },
            "category_averages": {
                "description": (
                    round(sum(pr.description_score for pr in analyzed_prs) / len(analyzed_prs), 1)
                    if analyzed_prs
                    else 0
                ),
                "testing": (
                    round(sum(pr.testing_score for pr in analyzed_prs) / len(analyzed_prs), 1) if analyzed_prs else 0
                ),
                "size": round(sum(pr.size_score for pr in analyzed_prs) / len(analyzed_prs), 1) if analyzed_prs else 0,
                "review": (
                    round(sum(pr.review_score for pr in analyzed_prs) / len(analyzed_prs), 1) if analyzed_prs else 0
                ),
                "traceability": (
                    round(sum(pr.traceability_score for pr in analyzed_prs) / len(analyzed_prs), 1)
                    if analyzed_prs
                    else 0
                ),
                "post_merge": (
                    round(sum(pr.post_merge_score for pr in analyzed_prs) / len(analyzed_prs), 1)
                    if analyzed_prs
                    else 0
                ),
                "scm_policy": (
                    round(sum(pr.scm_policy_score for pr in analyzed_prs) / len(analyzed_prs), 1)
                    if analyzed_prs
                    else 0
                ),
            },
            "critical_issues": sum(1 for pr in analyzed_prs if any("CRITICAL" in issue for issue in pr.issues)),
            "post_merge_ci_status": {
                "success": sum(1 for pr in analyzed_prs if pr.post_merge_ci_status == "success"),
                "failure": post_merge_failures,
                "pending": sum(1 for pr in analyzed_prs if pr.post_merge_ci_status == "pending"),
                "no_ci": sum(1 for pr in analyzed_prs if pr.post_merge_ci_status == "no_ci"),
                "unknown": sum(1 for pr in analyzed_prs if pr.post_merge_ci_status == "unknown"),
            },
            "ci_coverage": {
                "has_build_check": sum(1 for pr in analyzed_prs if pr.has_build_check),
                "missing_build_check": sum(
                    1
                    for pr in analyzed_prs
                    if not pr.has_build_check and not pr.has_no_ci and pr.post_merge_ci_status != "unknown"
                ),
                "has_test_check": sum(1 for pr in analyzed_prs if pr.has_test_check),
                "missing_test_check": sum(
                    1
                    for pr in analyzed_prs
                    if not pr.has_test_check and not pr.has_no_ci and pr.post_merge_ci_status != "unknown"
                ),
                "no_ci_at_all": sum(1 for pr in analyzed_prs if pr.has_no_ci),
            },
        },
    )


def main() -> None:
    """Main entry point."""
    # Calculate current MSFT fiscal year dates
    fiscal_year_name, default_start, default_end = get_msft_fiscal_year_dates()

    parser = argparse.ArgumentParser(description="Fetch and analyze GitHub PRs for quality assessment")
    parser.add_argument("username", help="GitHub username to analyze")
    parser.add_argument(
        "--repo",
        default=None,
        help="Repository to search in owner/repo format (default: search all accessible repositories)",
    )
    parser.add_argument(
        "--start",
        default=default_start,
        help=f"Start date for PR search (YYYY-MM-DD, default: current fiscal year {fiscal_year_name} = {default_start})",
    )
    parser.add_argument(
        "--end",
        default=default_end,
        help=f"End date for PR search (YYYY-MM-DD, default: current fiscal year {fiscal_year_name} = {default_end})",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=70,
        help="Quality score threshold (default: 70)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "summary", "markdown"],
        default="summary",
        help="Output format (default: summary)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed evidence with PR links for all issues",
    )

    args = parser.parse_args()

    report = generate_report(
        username=args.username,
        repo=args.repo,
        start_date=args.start,
        end_date=args.end,
        quality_threshold=args.threshold,
    )

    # Set up output destination (file or stdout)
    import sys
    from contextlib import redirect_stdout

    output_file = open(args.output, "w") if args.output else sys.stdout

    try:
        with redirect_stdout(output_file):
            # Generate output (all print statements go to output_file or stdout)
            _generate_output(args, report)
    finally:
        if args.output:
            output_file.close()


def _simplify_check_name(check_name: str) -> str:
    """Simplify a CI check name to its essential part.

    Args:
        check_name: Full check name like "Post-merge / Build / (Dry run) Build on linux"

    Returns:
        Simplified name like "Build"
    """
    # Common patterns to extract
    if "/" in check_name:
        # Split by / and find the key part
        parts = [p.strip() for p in check_name.split("/")]
        # Skip generic parts
        for part in parts:
            if part.lower() not in ("post-merge", "pre-merge", "(dry run)", ""):
                # Further simplify by taking first word
                words = part.split()
                for word in words:
                    if word.lower() not in ("on", "linux", "windows", "macos", "unvarianted"):
                        return word
                return part
    return check_name.split()[0] if check_name else "Check"


def _format_dimension_cell(score: int, has_issue: bool, issue_text: str | None) -> str:
    """Format a table cell for a dimension with grade and optional issue text.

    Args:
        score: Dimension score (0-100)
        has_issue: Whether this dimension has an issue
        issue_text: Optional text describing the issue

    Returns:
        Formatted cell string with emoji and grade/issue
    """
    grade = calculate_grade(score)
    if score >= 90:
        icon = "✓"
    elif score >= 60:
        icon = "⚠"
    else:
        icon = "✗"

    if has_issue and issue_text:
        return f"{icon} {grade} {issue_text}"
    else:
        return f"{icon} {grade}"


def _generate_appendix_markdown() -> None:
    """Generate appendix explaining quality dimensions and scoring methodology."""
    print("## Appendix: Quality Scoring Methodology")
    print()
    print("This report evaluates PR quality across seven dimensions. Each dimension is scored 0-100, ")
    print("then combined into an overall score using weighted averages. Letter grades are assigned as: ")
    print("A (90-100), B (80-89), C (70-79), D (60-69), F (<60).")
    print()

    print("### Overall Score Calculation")
    print()
    print("The overall quality score is a weighted average of all dimensions:")
    print()
    print("- **Description Quality: 18%**")
    print("- **Testing Evidence: 18%**")
    print("- **PR Size: 12%**")
    print("- **Review Coverage: 18%**")
    print("- **Traceability: 9%**")
    print("- **Post-Merge CI/CD: 15%**")
    print("- **SCM Policy Compliance: 10%**")
    print()

    print("### 1. Description Quality (18% weight)")
    print()
    print("**What it measures:** Completeness and structure of the PR description.")
    print()
    print("**Scoring criteria:**")
    print("- **0 points:** Empty or missing description")
    print("- **30 points:** Very brief description (<50 characters)")
    print("- **60 points:** Minimal description (50-99 characters)")
    print("- **80 points:** Moderate description (100-199 characters)")
    print("- **100 points:** Detailed description (200+ characters)")
    print("- **+10 bonus:** Structured format (headers, bullet points)")
    print()
    print("**Why it matters:** Good descriptions help reviewers understand context, decisions, and impact.")
    print()

    print("### 2. Testing Evidence (18% weight)")
    print()
    print("**What it measures:** Presence of tests and testing documentation.")
    print()
    print("**Scoring criteria (for code PRs):**")
    print("- **0 points:** No test files in diff AND no testing section in description")
    print("- **60 points:** Testing section present but no test files in diff")
    print("- **70 points:** Test files present but no testing section")
    print("- **100 points:** Both test files and testing section present")
    print()
    print("**Additional factors:**")
    print("- Code-to-test ratio of 0.5+ earns recognition as good coverage")
    print("- Non-code PRs (docs, config) receive 100 points with testing section, 80 without")
    print()
    print("**Impact of CI results:** Testing score is reduced by 70% if no CI checks exist, ")
    print("50% if CI fails post-merge, and 20% if build or test checks are missing from CI.")
    print()
    print("**Why it matters:** Tests prevent regressions and document expected behavior.")
    print()

    print("### 3. PR Size (12% weight)")
    print()
    print("**What it measures:** Reviewability based on total changes and files modified.")
    print()
    print("**Size categories:**")
    print("- **Small:** ≤50 changes, ≤3 files (100 points)")
    print("- **Medium:** ≤200 changes, ≤10 files (90 points)")
    print("- **Large:** ≤500 changes, ≤20 files (70 points)")
    print("- **XLarge:** >500 changes or >20 files (40 points)")
    print()
    print("**Why it matters:** Smaller PRs are easier to review thoroughly, reducing bug risk.")
    print()

    print("### 4. Review Coverage (18% weight)")
    print()
    print("**What it measures:** Peer review participation and approval status.")
    print()
    print("**Scoring criteria:**")
    print("- **0 points:** Self-merged without any reviews (CRITICAL issue)")
    print("- **30 points:** No reviews on PR")
    print("- **60 points:** Reviews present but merged without explicit approval")
    print("- **100 points:** Peer reviewed with explicit approval")
    print()
    print("**Why it matters:** Peer review catches bugs, improves design, and shares knowledge.")
    print()

    print("### 5. Traceability (9% weight)")
    print()
    print("**What it measures:** Linkage to project tracking systems.")
    print()
    print("**Scoring criteria:**")
    print("- **50 points:** No JIRA ticket reference found")
    print("- **100 points:** JIRA ticket referenced in title or description")
    print()
    print("**Detection:** Looks for patterns like \"PROJ-123\" or mentions of \"jira\".")
    print()
    print("**Why it matters:** Traceability connects code changes to requirements and planning.")
    print()

    print("### 6. Post-Merge CI/CD (15% weight)")
    print()
    print("**What it measures:** CI/CD pipeline execution and health after merge.")
    print()
    print("**Scoring criteria:**")
    print("- **0 points:** No CI checks found on merge commit (CRITICAL)")
    print("- **20 points:** CI checks failed post-merge (CRITICAL)")
    print("- **50 points:** CI status unknown")
    print("- **70 points:** CI checks pending")
    print("- **100 points:** All CI checks passed")
    print()
    print("**Additional penalties:**")
    print("- **-30% penalty:** Missing build check in CI pipeline")
    print("- **-30% penalty:** Missing test check in CI pipeline")
    print()
    print("**Build detection:** Patterns include \"build\", \"compile\", \"gradle\", \"maven\", \"cargo\", etc.")
    print()
    print("**Test detection:** Patterns include \"test\", \"jest\", \"pytest\", \"junit\", \"coverage\", etc.")
    print()
    print("**Why it matters:** CI failures indicate broken builds or failing tests that impact other developers.")
    print()

    print("### 7. SCM Policy Compliance (10% weight)")
    print()
    print("**What it measures:** Adherence to source control management policies (when available).")
    print()
    print("**Scoring criteria:**")
    print("- Score = (passed_checks / total_checks) × 100")
    print("- **100 points:** All SCM policy checks passed or module not available")
    print()
    print("**Why it matters:** SCM policies enforce organizational best practices and security requirements.")
    print()


def _generate_appendix_summary() -> None:
    """Generate appendix explaining quality dimensions in text format."""
    print("\n" + "=" * 60)
    print("APPENDIX: QUALITY SCORING METHODOLOGY")
    print("=" * 60)
    print()
    print("This report evaluates PR quality across seven dimensions.")
    print("Each dimension is scored 0-100, then combined using weighted")
    print("averages. Letter grades: A (90-100), B (80-89), C (70-79),")
    print("D (60-69), F (<60).")
    print()
    print("-" * 60)
    print("OVERALL SCORE CALCULATION")
    print("-" * 60)
    print("Weighted average of all dimensions:")
    print("  Description Quality:    18%")
    print("  Testing Evidence:       18%")
    print("  PR Size:                12%")
    print("  Review Coverage:        18%")
    print("  Traceability:            9%")
    print("  Post-Merge CI/CD:       15%")
    print("  SCM Policy Compliance:  10%")
    print()
    print("-" * 60)
    print("1. DESCRIPTION QUALITY (18% weight)")
    print("-" * 60)
    print("Measures: Completeness and structure of PR description")
    print()
    print("Scoring:")
    print("   0 pts: Empty or missing description")
    print("  30 pts: Very brief (<50 chars)")
    print("  60 pts: Minimal (50-99 chars)")
    print("  80 pts: Moderate (100-199 chars)")
    print(" 100 pts: Detailed (200+ chars)")
    print(" +10 pts: Structured format (headers, bullets)")
    print()
    print("Why: Good descriptions provide context for reviewers.")
    print()
    print("-" * 60)
    print("2. TESTING EVIDENCE (18% weight)")
    print("-" * 60)
    print("Measures: Presence of tests and testing documentation")
    print()
    print("Scoring (for code PRs):")
    print("   0 pts: No test files AND no testing section")
    print("  60 pts: Testing section but no test files")
    print("  70 pts: Test files but no testing section")
    print(" 100 pts: Both test files and testing section")
    print()
    print("Additional factors:")
    print("  - Code-to-test ratio 0.5+ recognized as good coverage")
    print("  - Non-code PRs: 100 pts with testing section, 80 without")
    print()
    print("CI impact on testing score:")
    print("  - Reduced 70% if no CI checks exist")
    print("  - Reduced 50% if CI fails post-merge")
    print("  - Reduced 20% if build/test checks missing from CI")
    print()
    print("Why: Tests prevent regressions and document behavior.")
    print()
    print("-" * 60)
    print("3. PR SIZE (12% weight)")
    print("-" * 60)
    print("Measures: Reviewability based on changes and files")
    print()
    print("Size categories:")
    print("  Small:   ≤50 changes, ≤3 files    (100 pts)")
    print("  Medium:  ≤200 changes, ≤10 files  (90 pts)")
    print("  Large:   ≤500 changes, ≤20 files  (70 pts)")
    print("  XLarge:  >500 changes or >20 files (40 pts)")
    print()
    print("Why: Smaller PRs enable thorough review, reducing bugs.")
    print()
    print("-" * 60)
    print("4. REVIEW COVERAGE (18% weight)")
    print("-" * 60)
    print("Measures: Peer review participation and approval")
    print()
    print("Scoring:")
    print("   0 pts: Self-merged without reviews (CRITICAL)")
    print("  30 pts: No reviews on PR")
    print("  60 pts: Reviews but no explicit approval")
    print(" 100 pts: Peer reviewed with approval")
    print()
    print("Why: Peer review catches bugs and shares knowledge.")
    print()
    print("-" * 60)
    print("5. TRACEABILITY (9% weight)")
    print("-" * 60)
    print("Measures: Linkage to project tracking systems")
    print()
    print("Scoring:")
    print("  50 pts: No JIRA reference found")
    print(" 100 pts: JIRA ticket referenced (e.g., PROJ-123)")
    print()
    print("Why: Connects code changes to requirements.")
    print()
    print("-" * 60)
    print("6. POST-MERGE CI/CD (15% weight)")
    print("-" * 60)
    print("Measures: CI/CD pipeline execution after merge")
    print()
    print("Scoring:")
    print("   0 pts: No CI checks found (CRITICAL)")
    print("  20 pts: CI checks failed (CRITICAL)")
    print("  50 pts: CI status unknown")
    print("  70 pts: CI checks pending")
    print(" 100 pts: All CI checks passed")
    print()
    print("Additional penalties:")
    print("  -30%: Missing build check in CI")
    print("  -30%: Missing test check in CI")
    print()
    print("Build detection: 'build', 'compile', 'gradle', etc.")
    print("Test detection: 'test', 'jest', 'pytest', etc.")
    print()
    print("Why: CI failures break builds for other developers.")
    print()
    print("-" * 60)
    print("7. SCM POLICY COMPLIANCE (10% weight)")
    print("-" * 60)
    print("Measures: Adherence to SCM policies (when available)")
    print()
    print("Scoring:")
    print("  Score = (passed_checks / total_checks) × 100")
    print("  100 pts: All checks passed or module unavailable")
    print()
    print("Why: Enforces organizational best practices.")
    print()


def _generate_output(args: argparse.Namespace, report: PRQualityReport) -> None:
    """Generate formatted output based on args.format.

    Args:
        args: Parsed command line arguments
        report: Generated quality report
    """
    if args.format == "json":
        # Convert dataclasses to dict for JSON output
        output = {
            "github_username": report.github_username,
            "repository": report.repository,
            "date_range": report.date_range,
            "total_prs_merged": report.total_prs_merged,
            "total_prs_reviewed": report.total_prs_reviewed,
            "prs_analyzed": report.prs_analyzed,
            "average_quality_score": report.average_quality_score,
            "prs_below_threshold": report.prs_below_threshold,
            "prs_with_post_merge_failures": report.prs_with_post_merge_failures,
            "quality_threshold": report.quality_threshold,
            "dimension_scores": {
                dimension: asdict(score) for dimension, score in report.dimension_scores.items()
            },
            "summary": report.summary,
            "prs": [asdict(pr) for pr in report.prs],
        }
        print(json.dumps(output, indent=2))
    elif args.format == "markdown":
        # Markdown format
        print(f"# PR Quality Report: {report.github_username}")
        print()
        print(f"**Repository:** {report.repository}  ")
        print(f"**Date Range:** {report.date_range}  ")

        # Add GitHub search link for all merged PRs
        # Parse date range to build search URL
        if " to " in report.date_range:
            start_date, end_date = report.date_range.split(" to ")
            date_filter = f"+merged:{start_date.strip()}..{end_date.strip()}"
        else:
            date_filter = ""
        github_search_url = f"https://github.com/search?q=is:pr+author:{report.github_username}+is:merged{date_filter}"
        print(f"**All Merged PRs:** [View on GitHub]({github_search_url})  ")
        print()

        print("## Activity Stats")
        print()
        print(f"- **Total PRs Merged:** {report.total_prs_merged}")
        print(f"- **Total PRs Reviewed:** {report.total_prs_reviewed}")
        print(f"- **PRs Analyzed:** {report.prs_analyzed}")
        print()

        print("## Quality Metrics")
        print()
        print(f"- **Average Quality Score:** {report.average_quality_score}/100")
        print(f"- **PRs Below Threshold ({report.quality_threshold}):** {report.prs_below_threshold}")
        print(f"- **Critical Issues Found:** {report.summary['critical_issues']}")
        print(f"- **Post-Merge CI Failures:** {report.prs_with_post_merge_failures}")
        print()

        print("## Grade Distribution")
        print()
        print("| Grade | Count |")
        print("|-------|-------|")
        for grade, count in report.summary["grade_distribution"].items():
            print(f"| {grade} | {count} |")
        print()

        print("## Dimension Scores & Grades")
        print()
        print("| Dimension | Score | Grade | A | B | C | D | F |")
        print("|-----------|-------|-------|---|---|---|---|---|")
        for dimension in ["description", "testing", "size", "review", "traceability", "post_merge", "scm_policy"]:
            dim_score = report.dimension_scores[dimension]
            dist = dim_score.grade_distribution
            display_name = "SCM Policy" if dimension == "scm_policy" else dimension.capitalize().replace("_", " ")
            print(
                f"| {display_name} | {dim_score.average_score}/100 | {dim_score.grade} | "
                f"{dist.get('A (90-100)', 0)} | {dist.get('B (80-89)', 0)} | "
                f"{dist.get('C (70-79)', 0)} | {dist.get('D (60-69)', 0)} | {dist.get('F (<60)', 0)} |"
            )
        print()

        print("## Most Common Issues")
        print()
        for issue, count in sorted(report.summary["issue_frequency"].items(), key=lambda x: -x[1])[:8]:
            if "CRITICAL" in issue:
                print(f"- ⚠️ **CRITICAL:** {issue.replace('CRITICAL: ', '')}: **{count}**")
            else:
                print(f"- {issue}: **{count}**")
        print()

        # Show all PRs with issues in a compact table (replaces separate sections)
        prs_with_issues = [pr for pr in report.prs if pr.issues]
        if prs_with_issues:
            print(f"## All Issues by PR ({len(prs_with_issues)} PRs)")
            print()
            print("| PR | Title | Overall | Description | Testing | Size | Review | Traceability | Post-Merge | SCM Policy |")
            print("|----|-------|---------|-------------|---------|------|--------|--------------|------------|------------|")

            for pr in sorted(prs_with_issues, key=lambda x: x.quality_score):
                # Format each dimension with grade and key issues
                desc_cell = _format_dimension_cell(pr.description_score, pr.description_length == 0, "Empty")

                # Testing cell - check for various test issues
                test_issues = []
                if not pr.has_tests_in_diff and pr.code_to_test_ratio == 0:
                    test_issues.append("No tests")
                test_cell = _format_dimension_cell(pr.testing_score, len(test_issues) > 0, ", ".join(test_issues) if test_issues else None)

                # Size cell
                size_issues = []
                if pr.size_category == "xlarge":
                    size_issues.append(f"XL ({pr.total_changes})")
                elif pr.size_category == "large":
                    size_issues.append(f"L ({pr.total_changes})")
                size_cell = _format_dimension_cell(pr.size_score, len(size_issues) > 0, ", ".join(size_issues) if size_issues else None)

                # Review cell
                review_issues = []
                if pr.is_self_merged:
                    review_issues.append("Self-merge")
                elif not pr.has_approval:
                    review_issues.append("No approval")
                review_cell = _format_dimension_cell(pr.review_score, len(review_issues) > 0, ", ".join(review_issues) if review_issues else None)

                # Traceability cell
                trace_issues = []
                if not pr.has_jira_reference:
                    trace_issues.append("No JIRA")
                trace_cell = _format_dimension_cell(pr.traceability_score, len(trace_issues) > 0, ", ".join(trace_issues) if trace_issues else None)

                # Post-merge cell - show links to failing checks
                if pr.has_no_ci:
                    post_cell = _format_dimension_cell(pr.post_merge_score, True, "No CI")
                elif pr.has_post_merge_failure and pr.post_merge_failed_checks:
                    # Show links to failed checks with simplified names
                    failed_links = []
                    for check_name, check_url in zip(pr.post_merge_failed_checks, pr.post_merge_failed_check_urls):
                        # Simplify check name (e.g., "Post-merge / Build / ..." -> "Build")
                        simplified = _simplify_check_name(check_name)
                        if check_url:
                            failed_links.append(f"[{simplified}]({check_url})")
                        else:
                            failed_links.append(simplified)
                    # Show only first 3 failures to avoid clutter
                    links_str = " ".join(failed_links[:3])
                    if len(failed_links) > 3:
                        links_str += f" +{len(failed_links) - 3}"
                    post_cell = _format_dimension_cell(pr.post_merge_score, True, links_str)
                elif not pr.has_build_check:
                    post_cell = _format_dimension_cell(pr.post_merge_score, True, "No build")
                elif not pr.has_test_check:
                    post_cell = _format_dimension_cell(pr.post_merge_score, True, "No test")
                else:
                    post_cell = _format_dimension_cell(pr.post_merge_score, False, None)

                # Overall score cell
                overall_icon = "✗" if pr.grade == "F" else "⚠" if pr.grade in ("D", "C") else "✓"
                overall_cell = f"{overall_icon} {pr.grade} ({pr.quality_score})"

                # PR link with owner/repo - extract from URL like "https://github.com/owner/repo/pull/123"
                url_parts = pr.url.rstrip('/').split('/')
                owner = url_parts[-4]
                repo = url_parts[-3]
                pr_link = f"[{owner}/{repo}#{pr.pr_number}]({pr.url})"

                # Title cell
                title_cell = pr.title

                # SCM Policy cell
                scm_issues = []
                for detail in pr.scm_check_details:
                    scm_issues.append(detail.replace("SCM Policy: ", "").replace(" failed", ""))
                scm_cell = _format_dimension_cell(pr.scm_policy_score, len(scm_issues) > 0, ", ".join(scm_issues[:2]) if scm_issues else None)

                print(f"| {pr_link} | {title_cell} | {overall_cell} | {desc_cell} | {test_cell} | {size_cell} | {review_cell} | {trace_cell} | {post_cell} | {scm_cell} |")
            print()

        # Verbose mode: detailed findings
        if args.verbose:
            print("## Detailed Findings With Evidence")
            print()

            # Group PRs by normalized issue
            issues_to_prs: dict[str, list[PRQualityCheck]] = {}
            for pr in report.prs:
                for issue in pr.issues:
                    normalized = normalize_issue_for_frequency(issue)
                    if normalized not in issues_to_prs:
                        issues_to_prs[normalized] = []
                    issues_to_prs[normalized].append(pr)

            # Sort by frequency
            sorted_issues = sorted(issues_to_prs.items(), key=lambda x: -len(x[1]))

            for issue, prs_with_issue in sorted_issues:
                print(f"### {issue} ({len(prs_with_issue)} PRs)")
                print()
                for pr in prs_with_issue:
                    print(f"- [#{pr.pr_number} [{pr.grade}]]({pr.url})")
                print()

            # Show PRs by grade
            print("### All PRs By Grade")
            print()
            for grade in ["A", "B", "C", "D", "F"]:
                grade_prs = [pr for pr in report.prs if pr.grade == grade]
                if grade_prs:
                    print(f"**Grade {grade} ({len(grade_prs)} PRs):**")
                    print()
                    for pr in grade_prs:
                        print(f"- [#{pr.pr_number} (score: {pr.quality_score})]({pr.url})")
                    print()

        # Add appendix for markdown format
        print()
        _generate_appendix_markdown()
    else:
        # Summary format
        print("=" * 60)
        print(f"PR QUALITY REPORT: {report.github_username}")
        print("=" * 60)
        print(f"Repository: {report.repository}")
        print(f"Date Range: {report.date_range}")
        print()
        print("ACTIVITY STATS:")
        print(f"  Total PRs Merged: {report.total_prs_merged}")
        print(f"  Total PRs Reviewed: {report.total_prs_reviewed}")
        print(f"  PRs Analyzed: {report.prs_analyzed}")
        print()
        print("QUALITY METRICS:")
        print(f"  Average Quality Score: {report.average_quality_score}/100")
        print(f"  PRs Below Threshold ({report.quality_threshold}): {report.prs_below_threshold}")
        print(f"  Critical Issues Found: {report.summary['critical_issues']}")
        print(f"  Post-Merge CI Failures: {report.prs_with_post_merge_failures}")

        print("\n" + "-" * 40)
        print("GRADE DISTRIBUTION")
        print("-" * 40)
        for grade, count in report.summary["grade_distribution"].items():
            bar = "█" * count
            print(f"  {grade}: {count:2d} {bar}")

        print("\n" + "-" * 40)
        print("POST-MERGE CI/CD STATUS")
        print("-" * 40)
        ci_stats = report.summary["post_merge_ci_status"]
        print(f"  ✓ Success: {ci_stats['success']}")
        print(f"  ✗ Failure: {ci_stats['failure']}")
        print(f"  ⏳ Pending: {ci_stats['pending']}")
        print(f"  ⚠ No CI:   {ci_stats['no_ci']}")
        print(f"  ? Unknown: {ci_stats['unknown']}")

        print("\n" + "-" * 40)
        print("CI BUILD & TEST COVERAGE")
        print("-" * 40)
        ci_coverage = report.summary["ci_coverage"]
        print(f"  Build check present: {ci_coverage['has_build_check']}")
        print(f"  Build check missing: {ci_coverage['missing_build_check']}")
        print(f"  Test check present:  {ci_coverage['has_test_check']}")
        print(f"  Test check missing:  {ci_coverage['missing_test_check']}")
        print(f"  No CI at all:        {ci_coverage['no_ci_at_all']}")

        # Show evidence of where build/test was detected (verbose mode)
        if args.verbose:
            prs_with_build = [pr for pr in report.prs if pr.has_build_check and pr.build_evidence]
            prs_with_test = [pr for pr in report.prs if pr.has_test_check and pr.test_evidence]

            if prs_with_build or prs_with_test:
                print("\n  Detection evidence (sample):")
                # Show unique evidence patterns
                build_patterns: set[str] = set()
                test_patterns: set[str] = set()
                for pr in prs_with_build[:5]:
                    build_patterns.add(pr.build_evidence)
                for pr in prs_with_test[:5]:
                    test_patterns.add(pr.test_evidence)

                for pattern in sorted(build_patterns):
                    print(f"    Build: {pattern}")
                for pattern in sorted(test_patterns):
                    print(f"    Test:  {pattern}")

        print("\n" + "-" * 40)
        print("DIMENSION SCORES & GRADES")
        print("-" * 40)
        for dimension in ["description", "testing", "size", "review", "traceability", "post_merge", "scm_policy"]:
            dim_score = report.dimension_scores[dimension]
            bar_len = int(dim_score.average_score / 10)
            bar = "█" * bar_len + "░" * (10 - bar_len)
            print(f"  {dimension:15s}: {dim_score.average_score:5.1f}/100 [{dim_score.grade}] {bar}")
            # Show grade distribution
            dist = dim_score.grade_distribution
            dist_str = f"  A:{dist.get('A (90-100)', 0)} B:{dist.get('B (80-89)', 0)} C:{dist.get('C (70-79)', 0)} D:{dist.get('D (60-69)', 0)} F:{dist.get('F (<60)', 0)}"
            print(f"    {dist_str}")

        print("\n" + "-" * 40)
        print("MOST COMMON ISSUES")
        print("-" * 40)
        for issue, count in sorted(report.summary["issue_frequency"].items(), key=lambda x: -x[1])[:8]:
            prefix = "⚠️ " if "CRITICAL" in issue else "   "
            print(f"{prefix}{issue}: {count}")

        # Always show critical issues with evidence (CI failures, self-merges)
        prs_with_ci_failures = [pr for pr in report.prs if pr.has_post_merge_failure]
        prs_with_self_merge = [pr for pr in report.prs if pr.is_self_merged]

        if prs_with_ci_failures:
            print("\n" + "-" * 40)
            print(f"POST-MERGE CI FAILURES ({len(prs_with_ci_failures)})")
            print("-" * 40)
            for pr in prs_with_ci_failures:
                print(f"\n  #{pr.pr_number}: {pr.title[:60]}")
                print(f"  PR: {pr.url}")
                if pr.post_merge_failed_checks:
                    print("  Failed checks:")
                    for check_name, check_url in zip(pr.post_merge_failed_checks, pr.post_merge_failed_check_urls):
                        if check_url:
                            print(f"    - {check_name}: {check_url}")
                        else:
                            print(f"    - {check_name}")

        if prs_with_self_merge:
            print("\n" + "-" * 40)
            print(f"SELF-MERGED WITHOUT REVIEW ({len(prs_with_self_merge)})")
            print("-" * 40)
            for pr in prs_with_self_merge:
                print(f"  #{pr.pr_number}: {pr.url}")

        # Show PRs with no CI at all
        prs_with_no_ci = [pr for pr in report.prs if pr.has_no_ci]
        if prs_with_no_ci:
            print("\n" + "-" * 40)
            print(f"NO CI CHECKS FOUND ({len(prs_with_no_ci)})")
            print("-" * 40)
            for pr in prs_with_no_ci:
                print(f"  #{pr.pr_number}: {pr.url}")

        # Show PRs missing build check (but have some CI)
        prs_missing_build = [
            pr
            for pr in report.prs
            if not pr.has_build_check and not pr.has_no_ci and pr.post_merge_ci_status != "unknown"
        ]
        if prs_missing_build:
            print("\n" + "-" * 40)
            print(f"MISSING BUILD CHECK ({len(prs_missing_build)})")
            print("-" * 40)
            for pr in prs_missing_build:
                checks_str = ", ".join(pr.ci_check_names[:5]) if pr.ci_check_names else "none detected"
                print(f"  #{pr.pr_number}: {pr.url}")
                print(f"    CI checks found: {checks_str}")

        # Show PRs missing test check (but have some CI)
        prs_missing_test = [
            pr
            for pr in report.prs
            if not pr.has_test_check and not pr.has_no_ci and pr.post_merge_ci_status != "unknown"
        ]
        if prs_missing_test:
            print("\n" + "-" * 40)
            print(f"MISSING TEST CHECK ({len(prs_missing_test)})")
            print("-" * 40)
            for pr in prs_missing_test:
                checks_str = ", ".join(pr.ci_check_names[:5]) if pr.ci_check_names else "none detected"
                print(f"  #{pr.pr_number}: {pr.url}")
                print(f"    CI checks found: {checks_str}")

        # Verbose mode: show all issues grouped by category with PR links
        if args.verbose:
            print("\n" + "=" * 60)
            print("DETAILED FINDINGS WITH EVIDENCE")
            print("=" * 60)

            # Group PRs by normalized issue
            issues_to_prs: dict[str, list[PRQualityCheck]] = {}
            for pr in report.prs:
                for issue in pr.issues:
                    normalized = normalize_issue_for_frequency(issue)
                    if normalized not in issues_to_prs:
                        issues_to_prs[normalized] = []
                    issues_to_prs[normalized].append(pr)

            # Sort by frequency (most common first)
            sorted_issues = sorted(issues_to_prs.items(), key=lambda x: -len(x[1]))

            for issue, prs_with_issue in sorted_issues:
                print(f"\n{issue} ({len(prs_with_issue)} PRs)")
                print("-" * 40)
                for pr in prs_with_issue:
                    print(f"  #{pr.pr_number} [{pr.grade}]: {pr.url}")

            # Show PRs by grade
            print("\n" + "-" * 40)
            print("ALL PRs BY GRADE")
            print("-" * 40)
            for grade in ["A", "B", "C", "D", "F"]:
                grade_prs = [pr for pr in report.prs if pr.grade == grade]
                if grade_prs:
                    print(f"\n  Grade {grade} ({len(grade_prs)} PRs):")
                    for pr in grade_prs:
                        print(f"    #{pr.pr_number} (score: {pr.quality_score}): {pr.url}")

        # Show PRs below threshold (non-verbose mode shows this, verbose already has details)
        elif report.prs_below_threshold > 0:
            print("\n" + "-" * 40)
            print(f"PRs BELOW THRESHOLD (< {report.quality_threshold})")
            print("-" * 40)
            for pr in report.prs:
                if pr.quality_score < report.quality_threshold:
                    print(f"\n  #{pr.pr_number} [{pr.grade}] (score: {pr.quality_score})")
                    print(f"  Title: {pr.title[:50]}...")
                    print(f"  URL: {pr.url}")
                    if pr.has_post_merge_failure:
                        print(f"  ⚠️  Post-merge CI failed: {', '.join(pr.post_merge_failed_checks)}")
                        if pr.post_merge_failed_check_urls:
                            print("  Failed check URLs:")
                            for check_name, check_url in zip(
                                pr.post_merge_failed_checks, pr.post_merge_failed_check_urls
                            ):
                                if check_url:
                                    print(f"    - {check_name}: {check_url}")
                    print("  Issues:")
                    for issue in pr.issues:
                        print(f"    - {issue}")

        # Add appendix for summary format
        _generate_appendix_summary()


if __name__ == "__main__":
    main()
