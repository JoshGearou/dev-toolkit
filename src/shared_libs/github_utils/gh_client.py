"""
GitHub CLI client with rate limit handling and retry logic.

Provides a robust wrapper around the gh CLI with exponential backoff,
jitter, and parallel processing support.
"""

import base64
import json
import random
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, cast


@dataclass
class GHClientConfig:
    """Configuration for GHClient."""

    max_retries: int = 25
    initial_delay: float = 2.0
    max_delay: float = 300.0  # 5 minutes
    jitter: float = 0.1  # ±10% randomization
    verbose: bool = False


class GHClient:
    """
    GitHub CLI client with rate limit handling and retry logic.

    Provides methods to interact with GitHub via the gh CLI tool,
    with automatic retry on rate limits using exponential backoff with jitter.

    Example:
        client = GHClient()
        success, output = client.run_command(["repo", "list", "linkedin"])
        if success:
            repos = json.loads(output)
    """

    def __init__(self, config: Optional[GHClientConfig] = None) -> None:
        """
        Initialize GHClient.

        Args:
            config: Client configuration. Uses defaults if None.
        """
        self.config = config or GHClientConfig()

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        base_delay = min(self.config.initial_delay * (2**attempt), self.config.max_delay)

        # Add jitter: random value between -jitter% and +jitter%
        if self.config.jitter > 0:
            jitter_range: float = base_delay * self.config.jitter
            jitter_value: float = random.uniform(-jitter_range, jitter_range)
            return float(max(0.0, base_delay + jitter_value))

        return float(base_delay)

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format seconds into a human-readable duration string.

        Returns XXmYYs for durations under 1 hour, XhXXmYYs for longer.
        """
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours}h{mins:02d}m{secs:02d}s"
        return f"{mins:02d}m{secs:02d}s"

    def _retry_with_backoff(
        self,
        cmd: List[str],
        max_retries: Optional[int] = None,
        label: str = "",
        check_stdout_for_rate_limit: bool = False,
        return_stdout_on_error: bool = False,
        rate_limit_exhausted_output: str = "",
    ) -> Tuple[bool, str]:
        """
        Run a gh CLI command with exponential backoff retry on rate limits.

        Shared retry logic used by both run_command and run_graphql.

        Args:
            cmd: Full command to run (including 'gh' prefix)
            max_retries: Override default max retries
            label: Label for log messages (e.g. "GraphQL")
            check_stdout_for_rate_limit: Also check stdout for rate limit
                indicators (needed for GraphQL where gh writes JSON errors
                to stdout)
            return_stdout_on_error: When True, return stdout (not stderr)
                on non-rate-limit errors. Needed for GraphQL where partial
                results are in stdout even on non-zero exit.
            rate_limit_exhausted_output: String to return when rate limit
                retries are exhausted. run_command returns an error message;
                run_graphql returns "" so callers skip REST fallback.

        Returns:
            Tuple of (success, output)
        """
        retries = max_retries if max_retries is not None else self.config.max_retries
        label_prefix = f"{label} " if label else ""

        try:
            total_wait = 0.0

            for attempt in range(retries):
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)

                stdout = result.stdout.strip()
                stderr = result.stderr.strip()

                if result.returncode == 0:
                    return True, stdout

                # Detect rate limit errors
                is_rate_limited = "rate limit" in stderr.lower()
                if check_stdout_for_rate_limit:
                    is_rate_limited = is_rate_limited or "rate_limit" in stdout.lower()

                if is_rate_limited:
                    if attempt < retries - 1:
                        wait_time = self._calculate_delay(attempt)
                        total_wait += wait_time

                        if self.config.verbose:
                            wait_str = self._format_duration(wait_time)
                            total_str = self._format_duration(total_wait)
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            retry_str = f"{attempt + 2:>2}/{retries}"
                            print(
                                f"[{timestamp}] \u26a0 {label_prefix}Rate limit hit,"
                                f" waiting {wait_str:>9} "
                                f"(total waited: {total_str:>9}) - "
                                f"retry {retry_str}...",
                                file=sys.stderr,
                            )

                        time.sleep(wait_time)
                        continue
                    else:
                        # Retries exhausted
                        total_str = self._format_duration(total_wait)
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        if rate_limit_exhausted_output:
                            return False, rate_limit_exhausted_output
                        return False, (
                            f"{stderr}\n\n"
                            f"[{timestamp}] \u26a0 {label_prefix}Rate limit exceeded"
                            f" after {retries} retries "
                            f"(waited total: {total_str}).\n"
                            f"   GitHub rate limits reset after 1 hour.\n"
                            f"   Check remaining quota: gh api rate_limit\n"
                            f"   Or reduce parallelism and try again"
                        )

                # Non-rate-limit error: don't retry
                if return_stdout_on_error:
                    return False, stdout
                return False, stderr

            return False, "Max retries exceeded"

        except FileNotFoundError:
            if return_stdout_on_error:
                return False, ""
            return False, "gh CLI not found. Install with: brew install gh"

    def run_command(self, args: List[str], max_retries: Optional[int] = None) -> Tuple[bool, str]:
        """
        Run a gh CLI command with exponential backoff retry on rate limits.

        Retries up to configured max retries with exponential backoff
        capped at max_delay, with jitter to prevent thundering herd.

        Args:
            args: Command arguments to pass to gh
            max_retries: Override default max retries

        Returns:
            Tuple of (success, output/error)
        """
        return self._retry_with_backoff(
            cmd=["gh"] + args,
            max_retries=max_retries,
        )

    def run_graphql(self, query: str, max_retries: Optional[int] = None) -> Tuple[bool, str]:
        """
        Run a GraphQL query via gh api graphql with rate limit retry.

        Unlike run_command, this always returns stdout (not stderr) because
        gh api graphql writes JSON to stdout even on non-zero exit codes
        (e.g. when some repos in a batch are inaccessible). Rate limit
        detection checks both stderr and stdout JSON error responses.

        Args:
            query: GraphQL query string
            max_retries: Override default max retries

        Returns:
            Tuple of (success, stdout_output). On rate limit exhaustion,
            returns (False, "") so callers know not to fall back to REST.
        """
        return self._retry_with_backoff(
            cmd=["gh", "api", "graphql", "-f", f"query={query}"],
            max_retries=max_retries,
            label="GraphQL",
            check_stdout_for_rate_limit=True,
            return_stdout_on_error=True,
            rate_limit_exhausted_output="",
        )

    def get_default_branch(self, owner: str, repo: str) -> str:
        """
        Get the default branch for a repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Default branch name (defaults to 'main' if unable to determine)
        """
        success, output = self.run_command(
            [
                "repo",
                "view",
                f"{owner}/{repo}",
                "--json",
                "defaultBranchRef",
            ]
        )

        if not success:
            if self.config.verbose:
                print(
                    "Warning: Could not determine default branch, assuming 'main'",
                    file=sys.stderr,
                )
            return "main"

        data = json.loads(output)
        return cast(str, data.get("defaultBranchRef", {}).get("name", "main"))

    def list_prs(self, owner: str, repo: str, limit: int = 5, state: str = "open") -> List[int]:
        """
        Get PR numbers for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            limit: Maximum number of PRs to return (0 for no limit)
            state: PR state filter - 'open', 'closed', 'merged', or 'all'

        Returns:
            List of PR numbers
        """
        cmd = [
            "pr",
            "list",
            "--repo",
            f"{owner}/{repo}",
            "--state",
            state,
            "--json",
            "number",
        ]
        if limit > 0:
            cmd.extend(["--limit", str(limit)])

        success, output = self.run_command(cmd)
        if not success:
            if self.config.verbose:
                print(f"Error listing PRs: {output}", file=sys.stderr)
            return []

        data = json.loads(output)
        return [pr["number"] for pr in data]

    def search_repos(
        self,
        owner: str,
        pattern: str,
        max_matches: int = 100,
        exclude_patterns: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Search for repositories matching a regex pattern.

        Fetches a batch of repos then filters by pattern.

        Args:
            owner: Repository owner/organization
            pattern: Regex pattern to match repository names (anchored to start)
            max_matches: Maximum number of matching repos to return (0 = unlimited)
            exclude_patterns: List of regex patterns to exclude (matches anywhere)

        Returns:
            List of repository names matching the pattern
        """
        # Compile include regex pattern
        try:
            include_regex = re.compile(pattern)
        except re.error as e:
            if self.config.verbose:
                print(f"Invalid regex pattern '{pattern}': {e}", file=sys.stderr)
            return []

        # Compile exclude patterns into a single combined regex for performance
        exclude_regex: Optional[re.Pattern[str]] = None
        if exclude_patterns:
            try:
                combined_pattern = "(" + "|".join(f"(?:{p})" for p in exclude_patterns) + ")"
                exclude_regex = re.compile(combined_pattern)
            except re.error as e:
                if self.config.verbose:
                    print(f"Invalid exclude pattern combination: {e}", file=sys.stderr)

        # Fetch repos - use high limit to get most repos
        if max_matches == 0:
            fetch_limit = 100000
        else:
            fetch_limit = max(max_matches * 10, 1000)

        success, output = self.run_command(["repo", "list", owner, "--limit", str(fetch_limit), "--json", "name"])

        if not success:
            if self.config.verbose:
                print(f"Error listing repositories: {output}", file=sys.stderr)
            return []

        data = json.loads(output)
        repo_names = [r["name"] for r in data]

        # Filter by include pattern
        matching = [name for name in repo_names if include_regex.match(name)]

        # Filter out excluded repos
        if exclude_regex:
            excluded_count = 0
            filtered = []
            for name in matching:
                if exclude_regex.search(name):
                    excluded_count += 1
                else:
                    filtered.append(name)
            matching = filtered

            if excluded_count > 0 and self.config.verbose:
                print(
                    f"Excluded {excluded_count} repo(s) matching exclude patterns",
                    file=sys.stderr,
                )

        # Sort alphabetically for consistent output
        matching.sort()

        # Return up to max_matches (or all if max_matches is 0)
        if max_matches == 0:
            return matching
        return matching[:max_matches]

    def search_repos_with_exclusion_status(
        self,
        owner: str,
        pattern: str,
        max_matches: int = 100,
        exclude_patterns: Optional[List[str]] = None,
    ) -> List[Tuple[str, bool]]:
        """
        Search for repositories with exclusion status for each.

        Returns ALL matching repos with a flag indicating if they're excluded.
        Useful for listing/auditing purposes where you want to see the complete picture.

        Args:
            owner: Repository owner/organization
            pattern: Regex pattern to match repository names (anchored to start)
            max_matches: Maximum number of matching repos to return (0 = unlimited)
            exclude_patterns: List of regex patterns to exclude (matches anywhere)

        Returns:
            List of (repo_name, is_excluded) tuples for all matching repos
        """
        # Compile include regex pattern
        try:
            include_regex = re.compile(pattern)
        except re.error as e:
            if self.config.verbose:
                print(f"Invalid regex pattern '{pattern}': {e}", file=sys.stderr)
            return []

        # Compile exclude patterns into a single combined regex
        exclude_regex: Optional[re.Pattern[str]] = None
        if exclude_patterns:
            try:
                combined_pattern = "(" + "|".join(f"(?:{p})" for p in exclude_patterns) + ")"
                exclude_regex = re.compile(combined_pattern)
            except re.error as e:
                if self.config.verbose:
                    print(f"Invalid exclude pattern combination: {e}", file=sys.stderr)

        # Fetch repos
        if max_matches == 0:
            fetch_limit = 100000
        else:
            fetch_limit = max(max_matches * 10, 1000)

        success, output = self.run_command(["repo", "list", owner, "--limit", str(fetch_limit), "--json", "name"])

        if not success:
            if self.config.verbose:
                print(f"Error listing repositories: {output}", file=sys.stderr)
            return []

        data = json.loads(output)
        repo_names = [r["name"] for r in data]

        # Filter by include pattern and mark exclusion status
        matching_with_status: List[Tuple[str, bool]] = []
        for name in repo_names:
            if include_regex.match(name):
                is_excluded = bool(exclude_regex and exclude_regex.search(name))
                matching_with_status.append((name, is_excluded))

        # Sort alphabetically by repo name
        matching_with_status.sort(key=lambda x: x[0])

        # Return up to max_matches (or all if max_matches is 0)
        if max_matches == 0:
            return matching_with_status
        return matching_with_status[:max_matches]

    def get_pr_info(self, owner: str, repo: str, pr_number: int) -> Optional[Dict[str, Any]]:
        """
        Fetch PR information using gh CLI.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number

        Returns:
            Dictionary with PR info or None if fetch failed
        """
        repo_path = f"{owner}/{repo}"

        success, output = self.run_command(
            [
                "pr",
                "view",
                str(pr_number),
                "--repo",
                repo_path,
                "--json",
                "number,author,title,state,reviews,commits,files,url",
            ]
        )

        if not success:
            if self.config.verbose:
                print(f"Error fetching PR: {output}", file=sys.stderr)
            return None

        return cast(Dict[str, Any], json.loads(output))

    def get_file_contents(self, owner: str, repo: str, path: str) -> Optional[str]:
        """
        Fetch file contents from a repository at HEAD.

        Uses the GitHub Contents API to retrieve a file. Returns the
        decoded content as a string, or None if the file does not exist.

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path within the repository

        Returns:
            Decoded file content as string, or None if not found
        """
        success, output = self.run_command(["api", f"repos/{owner}/{repo}/contents/{path}"])

        if not success:
            return None

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            return None

        content_b64 = data.get("content")
        if not content_b64 or data.get("type") != "file":
            return None

        try:
            return base64.b64decode(content_b64).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return None

    def check_direct_commits(
        self, owner: str, repo: str, branch: str, limit: int = 50, max_workers: int = 5
    ) -> List[Dict[str, str]]:
        """
        Check for commits pushed directly to branch without PRs.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch to check
            limit: Maximum number of commits to check
            max_workers: Maximum parallel workers for PR checks

        Returns:
            List of commits without associated PRs
        """
        # Get recent commits on the branch
        success, output = self.run_command(
            [
                "api",
                f"repos/{owner}/{repo}/commits",
                "-f",
                f"sha={branch}",
                "-f",
                f"per_page={limit}",
                "--jq",
                ".[] | {sha: .sha, message: .commit.message, " "author: .author.login, date: .commit.author.date}",
            ]
        )

        if not success:
            if self.config.verbose:
                print(f"Error fetching commits: {output}", file=sys.stderr)
            return []

        # Parse the newline-delimited JSON
        commits: List[Dict[str, str]] = []
        for line in output.strip().split("\n"):
            if line:
                try:
                    commits.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        # Check each commit for associated PR
        def has_pr(commit: Dict[str, str]) -> bool:
            """Check if commit has associated PR."""
            sha = commit.get("sha", "")
            if not sha:
                return True  # Skip malformed commits

            success, pr_output = self.run_command(
                ["api", f"repos/{owner}/{repo}/commits/{sha}/pulls", "--jq", "length"]
            )
            return not (success and pr_output.strip() == "0")

        # Parallel check for PR associations
        direct_commits: List[Dict[str, str]] = []
        workers = min(max_workers, len(commits))

        if workers > 0:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_commit = {executor.submit(has_pr, commit): commit for commit in commits}

                for future in as_completed(future_to_commit):
                    commit = future_to_commit[future]
                    if not future.result():  # No PR found
                        direct_commits.append(commit)

        return direct_commits


def create_gh_client(
    max_retries: int = 25,
    initial_delay: float = 2.0,
    max_delay: float = 300.0,
    jitter: float = 0.1,
    verbose: bool = False,
) -> GHClient:
    """
    Create a GHClient with the specified configuration.

    Args:
        max_retries: Maximum number of retries for rate limit errors
        initial_delay: Initial delay in seconds for exponential backoff
        max_delay: Maximum delay cap in seconds
        jitter: Jitter factor (+-percentage) to prevent thundering herd
        verbose: Enable verbose output

    Returns:
        Configured GHClient instance
    """
    config = GHClientConfig(
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=max_delay,
        jitter=jitter,
        verbose=verbose,
    )
    return GHClient(config)
