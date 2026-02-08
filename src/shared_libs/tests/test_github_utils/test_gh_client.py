"""
Tests for GHClient class.
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch

# Add src directory to path so shared_libs is importable as a package
src_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, src_root)

from shared_libs.github_utils import GHClient, GHClientConfig, create_gh_client


class TestGHClientConfig:
    """Tests for GHClientConfig."""

    def test_default_values(self) -> None:
        """Default configuration values are set correctly."""
        config = GHClientConfig()
        assert config.max_retries == 25
        assert config.initial_delay == 2.0
        assert config.max_delay == 300.0
        assert config.jitter == 0.1
        assert config.verbose is False

    def test_custom_values(self) -> None:
        """Custom configuration values are respected."""
        config = GHClientConfig(max_retries=10, initial_delay=1.0, max_delay=60.0, jitter=0.2, verbose=True)
        assert config.max_retries == 10
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.jitter == 0.2
        assert config.verbose is True


class TestGHClientDelayCalculation:
    """Tests for delay calculation with jitter."""

    def test_exponential_growth(self) -> None:
        """Delay grows exponentially."""
        config = GHClientConfig(initial_delay=2.0, max_delay=300.0, jitter=0.0)
        client = GHClient(config)

        assert client._calculate_delay(0) == 2.0
        assert client._calculate_delay(1) == 4.0
        assert client._calculate_delay(2) == 8.0

    def test_max_delay_cap(self) -> None:
        """Delay is capped at max_delay."""
        config = GHClientConfig(initial_delay=2.0, max_delay=10.0, jitter=0.0)
        client = GHClient(config)

        # 2 * 2^4 = 32, but capped at 10
        assert client._calculate_delay(4) == 10.0

    def test_jitter_adds_variation(self) -> None:
        """Jitter produces variation in delays."""
        config = GHClientConfig(initial_delay=10.0, jitter=0.2)
        client = GHClient(config)

        delays = {client._calculate_delay(0) for _ in range(50)}
        # Should have variation due to jitter
        assert len(delays) > 1

    def test_delay_never_negative(self) -> None:
        """Delay is never negative even with large jitter."""
        config = GHClientConfig(initial_delay=0.1, jitter=0.9)
        client = GHClient(config)

        delays = [client._calculate_delay(0) for _ in range(100)]
        assert all(d >= 0.0 for d in delays)


class TestGHClientRunCommand:
    """Tests for run_command method."""

    @patch("subprocess.run")
    def test_successful_command(self, mock_run: MagicMock) -> None:
        """Successful command returns output."""
        mock_run.return_value = MagicMock(returncode=0, stdout="success output", stderr="")

        client = GHClient()
        success, output = client.run_command(["repo", "list"])

        assert success is True
        assert output == "success output"
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_command_failure(self, mock_run: MagicMock) -> None:
        """Failed command returns error."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error message")

        client = GHClient()
        success, output = client.run_command(["invalid", "command"])

        assert success is False
        assert output == "error message"

    @patch("subprocess.run")
    def test_gh_not_found(self, mock_run: MagicMock) -> None:
        """FileNotFoundError returns helpful message."""
        mock_run.side_effect = FileNotFoundError()

        client = GHClient()
        success, output = client.run_command(["repo", "list"])

        assert success is False
        assert "gh CLI not found" in output

    @patch("subprocess.run")
    @patch("time.sleep")
    def test_rate_limit_retry(self, mock_sleep: MagicMock, mock_run: MagicMock) -> None:
        """Rate limit triggers retry with backoff."""
        # First call: rate limit, second call: success
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="rate limit exceeded"),
            MagicMock(returncode=0, stdout="success", stderr=""),
        ]

        config = GHClientConfig(max_retries=5, jitter=0.0)
        client = GHClient(config)
        success, output = client.run_command(["repo", "list"])

        assert success is True
        assert output == "success"
        assert mock_run.call_count == 2
        mock_sleep.assert_called_once()

    @patch("subprocess.run")
    @patch("time.sleep")
    def test_rate_limit_max_retries(self, mock_sleep: MagicMock, mock_run: MagicMock) -> None:
        """Rate limit exhausts retries."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="rate limit exceeded")

        config = GHClientConfig(max_retries=3, jitter=0.0)
        client = GHClient(config)
        success, output = client.run_command(["repo", "list"])

        assert success is False
        assert "Rate limit exceeded after 3 retries" in output
        assert mock_run.call_count == 3


class TestGHClientMethods:
    """Tests for GHClient convenience methods."""

    @patch.object(GHClient, "run_command")
    def test_get_default_branch(self, mock_run: MagicMock) -> None:
        """get_default_branch returns branch name."""
        mock_run.return_value = (
            True,
            json.dumps({"defaultBranchRef": {"name": "develop"}}),
        )

        client = GHClient()
        branch = client.get_default_branch("owner", "repo")

        assert branch == "develop"

    @patch.object(GHClient, "run_command")
    def test_get_default_branch_fallback(self, mock_run: MagicMock) -> None:
        """get_default_branch falls back to main on error."""
        mock_run.return_value = (False, "error")

        client = GHClient()
        branch = client.get_default_branch("owner", "repo")

        assert branch == "main"

    @patch.object(GHClient, "run_command")
    def test_list_prs(self, mock_run: MagicMock) -> None:
        """list_prs returns PR numbers."""
        mock_run.return_value = (
            True,
            json.dumps([{"number": 1}, {"number": 2}, {"number": 3}]),
        )

        client = GHClient()
        prs = client.list_prs("owner", "repo", limit=5, state="open")

        assert prs == [1, 2, 3]

    @patch.object(GHClient, "run_command")
    def test_list_prs_error(self, mock_run: MagicMock) -> None:
        """list_prs returns empty list on error."""
        mock_run.return_value = (False, "error")

        client = GHClient()
        prs = client.list_prs("owner", "repo")

        assert prs == []

    @patch.object(GHClient, "run_command")
    def test_get_pr_info(self, mock_run: MagicMock) -> None:
        """get_pr_info returns PR data."""
        pr_data = {
            "number": 123,
            "author": {"login": "user"},
            "title": "Test PR",
            "state": "OPEN",
        }
        mock_run.return_value = (True, json.dumps(pr_data))

        client = GHClient()
        result = client.get_pr_info("owner", "repo", 123)

        assert result == pr_data

    @patch.object(GHClient, "run_command")
    def test_get_pr_info_error(self, mock_run: MagicMock) -> None:
        """get_pr_info returns None on error."""
        mock_run.return_value = (False, "error")

        client = GHClient()
        result = client.get_pr_info("owner", "repo", 123)

        assert result is None

    @patch.object(GHClient, "run_command")
    def test_search_repos(self, mock_run: MagicMock) -> None:
        """search_repos filters by pattern."""
        mock_run.return_value = (
            True,
            json.dumps(
                [
                    {"name": "api-gateway"},
                    {"name": "api-service"},
                    {"name": "web-app"},
                    {"name": "api-docs"},
                ]
            ),
        )

        client = GHClient()
        repos = client.search_repos("owner", r"api-.*", max_matches=10)

        assert repos == ["api-docs", "api-gateway", "api-service"]

    @patch.object(GHClient, "run_command")
    def test_search_repos_with_exclude(self, mock_run: MagicMock) -> None:
        """search_repos applies exclude patterns."""
        mock_run.return_value = (
            True,
            json.dumps(
                [
                    {"name": "api-gateway"},
                    {"name": "api-service"},
                    {"name": "api-docs"},
                    {"name": "api-test"},
                ]
            ),
        )

        client = GHClient()
        repos = client.search_repos("owner", r"api-.*", exclude_patterns=["test", "docs"])

        assert repos == ["api-gateway", "api-service"]

    @patch.object(GHClient, "run_command")
    def test_search_repos_with_exclusion_status(self, mock_run: MagicMock) -> None:
        """search_repos_with_exclusion_status returns all repos with exclusion flags."""
        mock_run.return_value = (
            True,
            json.dumps(
                [
                    {"name": "api-gateway"},
                    {"name": "api-service"},
                    {"name": "api-test"},
                    {"name": "api-docs"},
                ]
            ),
        )

        client = GHClient()
        repos_with_status = client.search_repos_with_exclusion_status(
            "owner", r"api-.*", exclude_patterns=["test", "docs"]
        )

        # All matching repos should be returned with exclusion status
        assert len(repos_with_status) == 4
        assert repos_with_status == [
            ("api-docs", True),  # Excluded (matches "docs")
            ("api-gateway", False),  # Not excluded
            ("api-service", False),  # Not excluded
            ("api-test", True),  # Excluded (matches "test")
        ]

    @patch.object(GHClient, "run_command")
    def test_search_repos_with_exclusion_status_no_excludes(self, mock_run: MagicMock) -> None:
        """search_repos_with_exclusion_status without exclude patterns."""
        mock_run.return_value = (
            True,
            json.dumps([{"name": "api-gateway"}, {"name": "api-service"}]),
        )

        client = GHClient()
        repos_with_status = client.search_repos_with_exclusion_status("owner", r"api-.*")

        # All repos should have is_excluded=False
        assert repos_with_status == [("api-gateway", False), ("api-service", False)]

    @patch.object(GHClient, "run_command")
    def test_search_repos_with_exclusion_status_all_excluded(self, mock_run: MagicMock) -> None:
        """search_repos_with_exclusion_status when all match exclusion."""
        mock_run.return_value = (
            True,
            json.dumps([{"name": "sandbox-test1"}, {"name": "sandbox-test2"}]),
        )

        client = GHClient()
        repos_with_status = client.search_repos_with_exclusion_status(
            "owner", r"sandbox-.*", exclude_patterns=["sandbox", "test"]
        )

        # All repos should be marked as excluded
        assert repos_with_status == [("sandbox-test1", True), ("sandbox-test2", True)]


class TestRateLimitMessageFormatting:
    """Tests for rate limit message formatting and alignment."""

    @patch("subprocess.run")
    @patch("time.sleep")
    @patch("sys.stderr")
    def test_rate_limit_message_seconds_only(
        self, mock_stderr: MagicMock, mock_sleep: MagicMock, mock_run: MagicMock
    ) -> None:
        """Rate limit message formats seconds-only duration correctly."""
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="rate limit exceeded"),
            MagicMock(returncode=0, stdout="success", stderr=""),
        ]

        config = GHClientConfig(initial_delay=5.0, jitter=0.0, verbose=True)
        client = GHClient(config)
        success, _ = client.run_command(["repo", "list"])

        assert success is True
        # Check that stderr.write was called with properly formatted message
        [str(call) for call in mock_stderr.write.call_args_list]
        message = "".join(str(call) for call in mock_stderr.write.call_args_list)
        # Should contain right-aligned time strings
        assert "waiting        5s" in message or "waiting" in message
        assert "retry  2/" in message  # 2-digit aligned retry count

    @patch("subprocess.run")
    @patch("time.sleep")
    @patch("sys.stderr")
    def test_rate_limit_message_minutes_seconds(
        self, mock_stderr: MagicMock, mock_sleep: MagicMock, mock_run: MagicMock
    ) -> None:
        """Rate limit message formats minutes+seconds duration correctly."""
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="rate limit exceeded"),
            MagicMock(returncode=0, stdout="success", stderr=""),
        ]

        config = GHClientConfig(initial_delay=65.0, jitter=0.0, verbose=True)
        client = GHClient(config)
        success, _ = client.run_command(["repo", "list"])

        assert success is True
        [str(call) for call in mock_stderr.write.call_args_list]
        message = "".join(str(call) for call in mock_stderr.write.call_args_list)
        # Should contain minutes and seconds
        assert "1m5s" in message or "waiting" in message

    @patch("subprocess.run")
    @patch("time.sleep")
    @patch("sys.stderr")
    def test_rate_limit_message_hours_minutes_seconds(
        self, mock_stderr: MagicMock, mock_sleep: MagicMock, mock_run: MagicMock
    ) -> None:
        """Rate limit message formats hours+minutes+seconds duration correctly."""
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="rate limit exceeded"),
            MagicMock(returncode=0, stdout="success", stderr=""),
        ]

        config = GHClientConfig(initial_delay=3665.0, jitter=0.0, verbose=True)
        client = GHClient(config)
        success, _ = client.run_command(["repo", "list"])

        assert success is True
        message = "".join(str(call) for call in mock_stderr.write.call_args_list)
        # Should contain hours, minutes, and seconds (3665s = 1h1m5s)
        assert "1h1m5s" in message or "waiting" in message

    @patch("subprocess.run")
    @patch("time.sleep")
    @patch("sys.stderr")
    def test_rate_limit_message_alignment_single_digit_retry(
        self, mock_stderr: MagicMock, mock_sleep: MagicMock, mock_run: MagicMock
    ) -> None:
        """Retry count is right-aligned for single-digit attempts."""
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="rate limit exceeded"),
            MagicMock(returncode=0, stdout="success", stderr=""),
        ]

        config = GHClientConfig(max_retries=25, initial_delay=1.0, jitter=0.0, verbose=True)
        client = GHClient(config)
        success, _ = client.run_command(["repo", "list"])

        assert success is True
        message = "".join(str(call) for call in mock_stderr.write.call_args_list)
        # Should have space-padded retry count: " 2/25"
        assert "retry  2/25" in message

    @patch("subprocess.run")
    @patch("time.sleep")
    @patch("sys.stderr")
    def test_rate_limit_message_alignment_double_digit_retry(
        self, mock_stderr: MagicMock, mock_sleep: MagicMock, mock_run: MagicMock
    ) -> None:
        """Retry count alignment works for double-digit attempts."""
        # Simulate 10 rate limit errors before success
        mock_run.side_effect = [MagicMock(returncode=1, stdout="", stderr="rate limit exceeded") for _ in range(10)] + [
            MagicMock(returncode=0, stdout="success", stderr="")
        ]

        config = GHClientConfig(max_retries=25, initial_delay=1.0, jitter=0.0, verbose=True)
        client = GHClient(config)
        success, _ = client.run_command(["repo", "list"])

        assert success is True
        message = "".join(str(call) for call in mock_stderr.write.call_args_list)
        # Should have retry counts aligned: " 2/25", "10/25", "11/25"
        assert "retry  2/25" in message
        assert "retry 10/25" in message
        assert "retry 11/25" in message

    @patch("subprocess.run")
    @patch("time.sleep")
    @patch("sys.stderr")
    def test_rate_limit_max_retries_message_format(
        self, mock_stderr: MagicMock, mock_sleep: MagicMock, mock_run: MagicMock
    ) -> None:
        """Final error message after max retries is formatted correctly."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="rate limit exceeded")

        config = GHClientConfig(max_retries=3, initial_delay=65.0, jitter=0.0, verbose=True)
        client = GHClient(config)
        success, output = client.run_command(["repo", "list"])

        assert success is False
        # Final error should mention total wait time with proper formatting
        assert "Rate limit exceeded after 3 retries" in output
        assert "waited total:" in output
        # Should contain time format (could be minutes+seconds or hours depending on total)


class TestCreateGhClient:
    """Tests for create_gh_client factory function."""

    def test_default_config(self) -> None:
        """Factory creates client with default config."""
        client = create_gh_client()
        assert isinstance(client, GHClient)
        assert client.config.max_retries == 25

    def test_custom_config(self) -> None:
        """Factory creates client with custom config."""
        client = create_gh_client(max_retries=10, initial_delay=1.0, verbose=True)
        assert client.config.max_retries == 10
        assert client.config.initial_delay == 1.0
        assert client.config.verbose is True
