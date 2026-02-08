"""
Tests for SubprocessClient class.
"""

import os
import sys
from unittest.mock import MagicMock, patch

# Add src directory to path so shared_libs is importable as a package
src_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, src_root)

from shared_libs.cmd_utils.subprocess_client import (
    CommandConfig,
    CommandResult,
    ConstantDelayStrategy,
    ExponentialBackoffStrategy,
    SubprocessClient,
    create_subprocess_client,
)


class TestCommandConfig:
    """Tests for CommandConfig dataclass."""

    def test_default_values(self) -> None:
        """Default configuration values are set correctly."""
        config = CommandConfig()
        assert config.timeout == 30
        assert config.retries == 0
        assert config.retry_delay == 1.0
        assert config.combine_output is True
        assert config.check_return_code is True
        assert config.verbose is False
        assert config.custom_error_patterns is None
        assert config.retry_strategy is None

    def test_custom_values(self) -> None:
        """Custom configuration values are respected."""
        strategy = ConstantDelayStrategy(delay=5.0)
        config = CommandConfig(
            timeout=60,
            retries=3,
            retry_delay=2.0,
            combine_output=False,
            check_return_code=False,
            verbose=True,
            retry_strategy=strategy,
        )
        assert config.timeout == 60
        assert config.retries == 3
        assert config.retry_delay == 2.0
        assert config.combine_output is False
        assert config.check_return_code is False
        assert config.verbose is True
        assert config.retry_strategy is strategy


class TestCommandResult:
    """Tests for CommandResult dataclass."""

    def test_success_result(self) -> None:
        """CommandResult captures success correctly."""
        result = CommandResult(
            success=True,
            output="hello world",
            error_output="",
            return_code=0,
            command="echo hello world",
            execution_time=0.1,
        )
        assert result.success is True
        assert result.output == "hello world"
        assert result.return_code == 0

    def test_failure_result(self) -> None:
        """CommandResult captures failure correctly."""
        result = CommandResult(
            success=False,
            output="",
            error_output="command not found",
            return_code=127,
            command="nonexistent",
            execution_time=0.05,
        )
        assert result.success is False
        assert result.return_code == 127


class TestSubprocessClientExecuteCommand:
    """Tests for SubprocessClient.execute_command method."""

    @patch("subprocess.run")
    def test_successful_command(self, mock_run: MagicMock) -> None:
        """Successful command execution returns correct result."""
        mock_run.return_value = MagicMock(returncode=0, stdout="hello world\n", stderr="")

        client = SubprocessClient()
        result = client.execute_command(["echo", "hello", "world"])

        assert result.success is True
        assert "hello world" in result.output
        assert result.return_code == 0
        assert result.command == "echo hello world"

    @patch("subprocess.run")
    def test_command_as_string(self, mock_run: MagicMock) -> None:
        """Command can be provided as string."""
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")

        client = SubprocessClient()
        result = client.execute_command("echo hello")

        assert result.success is True
        mock_run.assert_called_once()
        # Command should be split into list
        call_args = mock_run.call_args
        assert call_args[0][0] == ["echo", "hello"]

    @patch("subprocess.run")
    def test_command_failure(self, mock_run: MagicMock) -> None:
        """Failed command returns correct result."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error occurred")

        client = SubprocessClient()
        result = client.execute_command(["false"])

        assert result.success is False
        assert result.return_code == 1
        assert "error occurred" in result.error_output

    @patch("subprocess.run")
    def test_command_not_found(self, mock_run: MagicMock) -> None:
        """FileNotFoundError is handled correctly."""
        mock_run.side_effect = FileNotFoundError()

        client = SubprocessClient()
        result = client.execute_command(["nonexistent_command"])

        assert result.success is False
        assert result.return_code == 127
        assert "Command not found" in result.output
        assert result.error_info is not None
        assert result.error_info.error_type == "command-not-found"
        assert result.error_info.recoverable is False

    @patch("subprocess.run")
    def test_command_timeout(self, mock_run: MagicMock) -> None:
        """Timeout is handled correctly."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="sleep", timeout=5)

        config = CommandConfig(timeout=5)
        client = SubprocessClient(config)
        result = client.execute_command(["sleep", "100"])

        assert result.success is False
        assert result.return_code == 124
        assert "timed out" in result.output.lower()
        assert result.error_info is not None
        assert result.error_info.error_type == "timeout"

    @patch("subprocess.run")
    def test_working_directory(self, mock_run: MagicMock) -> None:
        """Working directory is passed to subprocess."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        client = SubprocessClient()
        client.execute_command(["pwd"], working_dir="/tmp")

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["cwd"] == "/tmp"

    @patch("subprocess.run")
    def test_environment_variables(self, mock_run: MagicMock) -> None:
        """Environment variables are passed to subprocess."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        client = SubprocessClient()
        env = {"MY_VAR": "my_value"}
        client.execute_command(["env"], env=env)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["env"] == env

    @patch("subprocess.run")
    def test_combine_output_true(self, mock_run: MagicMock) -> None:
        """Combined output includes both stdout and stderr."""
        mock_run.return_value = MagicMock(returncode=0, stdout="stdout content", stderr="stderr content")

        config = CommandConfig(combine_output=True)
        client = SubprocessClient(config)
        result = client.execute_command(["cmd"])

        assert "stdout content" in result.output
        assert "stderr content" in result.output

    @patch("subprocess.run")
    def test_combine_output_false(self, mock_run: MagicMock) -> None:
        """Separate output keeps stdout and stderr apart."""
        mock_run.return_value = MagicMock(returncode=0, stdout="stdout only", stderr="stderr only")

        config = CommandConfig(combine_output=False)
        client = SubprocessClient(config)
        result = client.execute_command(["cmd"])

        assert result.output == "stdout only"
        assert result.error_output == "stderr only"

    @patch("subprocess.run")
    def test_override_config(self, mock_run: MagicMock) -> None:
        """Override config takes precedence."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        config = CommandConfig(timeout=30)
        override = CommandConfig(timeout=60)
        client = SubprocessClient(config)
        client.execute_command(["cmd"], override_config=override)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["timeout"] == 60


class TestSubprocessClientRetry:
    """Tests for SubprocessClient retry logic."""

    @patch("subprocess.run")
    @patch("time.sleep")
    def test_retry_on_failure(self, mock_sleep: MagicMock, mock_run: MagicMock) -> None:
        """Command is retried on failure."""
        # First call fails, second succeeds
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="temporary error"),
            MagicMock(returncode=0, stdout="success", stderr=""),
        ]

        config = CommandConfig(retries=2, retry_delay=1.0)
        client = SubprocessClient(config)
        result = client.execute_command(["cmd"])

        assert result.success is True
        assert mock_run.call_count == 2
        mock_sleep.assert_called_once_with(1.0)

    @patch("subprocess.run")
    @patch("time.sleep")
    def test_retry_with_strategy(self, mock_sleep: MagicMock, mock_run: MagicMock) -> None:
        """Retry uses strategy for delay calculation."""
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="error"),
            MagicMock(returncode=1, stdout="", stderr="error"),
            MagicMock(returncode=0, stdout="success", stderr=""),
        ]

        strategy = ExponentialBackoffStrategy(initial_delay=2.0, max_delay=100.0, jitter=0.0)
        config = CommandConfig(retries=3, retry_strategy=strategy)
        client = SubprocessClient(config)
        result = client.execute_command(["cmd"])

        assert result.success is True
        assert mock_run.call_count == 3
        # First retry: 2.0s, second retry: 4.0s
        assert mock_sleep.call_count == 2
        delays = [call[0][0] for call in mock_sleep.call_args_list]
        assert delays[0] == 2.0
        assert delays[1] == 4.0

    @patch("subprocess.run")
    @patch("time.sleep")
    def test_max_retries_exhausted(self, mock_sleep: MagicMock, mock_run: MagicMock) -> None:
        """Retries stop after max attempts."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="persistent error")

        config = CommandConfig(retries=2)
        client = SubprocessClient(config)
        result = client.execute_command(["cmd"])

        assert result.success is False
        assert mock_run.call_count == 3  # Initial + 2 retries

    @patch("subprocess.run")
    def test_no_retry_on_command_not_found(self, mock_run: MagicMock) -> None:
        """Command not found does not retry."""
        mock_run.side_effect = FileNotFoundError()

        config = CommandConfig(retries=3)
        client = SubprocessClient(config)
        result = client.execute_command(["nonexistent"])

        assert result.success is False
        assert mock_run.call_count == 1  # No retries


class TestSubprocessClientUtilities:
    """Tests for SubprocessClient utility methods."""

    @patch("subprocess.run")
    def test_execute_simple(self, mock_run: MagicMock) -> None:
        """execute_simple provides simplified interface."""
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")

        client = SubprocessClient()
        result = client.execute_simple("echo test", timeout=10)

        assert result.success is True
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["timeout"] == 10

    @patch("subprocess.run")
    def test_test_command_available_true(self, mock_run: MagicMock) -> None:
        """test_command_available returns True for available commands."""
        mock_run.return_value = MagicMock(returncode=0)

        client = SubprocessClient()
        assert client.test_command_available("echo") is True

    @patch("subprocess.run")
    def test_test_command_available_false(self, mock_run: MagicMock) -> None:
        """test_command_available returns False for unavailable commands."""
        mock_run.return_value = MagicMock(returncode=1)

        client = SubprocessClient()
        assert client.test_command_available("nonexistent_cmd_12345") is False

    @patch.object(SubprocessClient, "execute_simple")
    def test_get_command_version(self, mock_execute: MagicMock) -> None:
        """get_command_version extracts version string."""
        mock_execute.return_value = CommandResult(
            success=True,
            output="Python 3.11.0\nmore info",
            error_output="",
            return_code=0,
            command="python --version",
            execution_time=0.1,
        )

        client = SubprocessClient()
        version = client.get_command_version("python")

        assert version == "Python 3.11.0"

    @patch.object(SubprocessClient, "execute_simple")
    def test_get_command_version_failure(self, mock_execute: MagicMock) -> None:
        """get_command_version returns None on failure."""
        mock_execute.return_value = CommandResult(
            success=False,
            output="",
            error_output="error",
            return_code=1,
            command="nonexistent --version",
            execution_time=0.1,
        )

        client = SubprocessClient()
        version = client.get_command_version("nonexistent")

        assert version is None


class TestCreateSubprocessClient:
    """Tests for create_subprocess_client factory function."""

    def test_default_config(self) -> None:
        """Factory creates client with default config."""
        client = create_subprocess_client()
        assert isinstance(client, SubprocessClient)
        assert client.config.timeout == 30
        assert client.config.retries == 0

    def test_custom_config(self) -> None:
        """Factory creates client with custom config."""
        client = create_subprocess_client(
            timeout=60,
            retries=3,
            verbose=True,
        )
        assert client.config.timeout == 60
        assert client.config.retries == 3
        assert client.config.verbose is True

    def test_custom_error_patterns(self) -> None:
        """Factory accepts custom error patterns."""
        patterns = {
            "my error": {
                "error_type": "custom",
                "message": "Custom error detected",
                "suggestion": "Try something else",
                "recoverable": False,
            }
        }
        client = create_subprocess_client(custom_patterns=patterns)

        # Verify pattern was added to detector
        pattern_sets = client.error_detector.get_pattern_sets()
        pattern_names = [name for name, _ in pattern_sets]
        assert any("custom" in name for name in pattern_names)
