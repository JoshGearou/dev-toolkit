"""
Tests for command wrapper classes.
"""

import os
import sys
from unittest.mock import MagicMock

# Add src directory to path so shared_libs is importable as a package
src_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, src_root)

from shared_libs.cmd_utils.command_wrappers import (
    CustomCommandWrapper,
    DockerCommandWrapper,
    GitCommandWrapper,
    KubernetesCommandWrapper,
    SystemCommandWrapper,
    create_command_wrapper,
)
from shared_libs.cmd_utils.subprocess_client import CommandResult, SubprocessClient


def make_result(
    success: bool = True,
    output: str = "",
    return_code: int = 0,
) -> CommandResult:
    """Helper to create CommandResult."""
    return CommandResult(
        success=success,
        output=output,
        error_output="",
        return_code=return_code,
        command="test",
        execution_time=0.1,
    )


class TestGitCommandWrapper:
    """Tests for GitCommandWrapper class."""

    def test_get_current_branch(self) -> None:
        """get_current_branch returns branch name."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.execute_simple.return_value = make_result(output="main\n")

        wrapper = GitCommandWrapper(client=mock_client)
        result = wrapper.get_current_branch()

        assert result == "main"

    def test_get_current_branch_failure(self) -> None:
        """get_current_branch returns None on failure."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.execute_simple.return_value = make_result(success=False)

        wrapper = GitCommandWrapper(client=mock_client)
        result = wrapper.get_current_branch()

        assert result is None

    def test_get_commit_hash_short(self) -> None:
        """get_commit_hash returns short hash by default."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.execute_simple.return_value = make_result(output="abc1234\n")

        wrapper = GitCommandWrapper(client=mock_client)
        result = wrapper.get_commit_hash()

        assert result == "abc1234"
        call_args = mock_client.execute_simple.call_args[0][0]
        assert "--short" in call_args

    def test_get_commit_hash_full(self) -> None:
        """get_commit_hash returns full hash when requested."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.execute_simple.return_value = make_result(output="abc1234567890abcdef\n")

        wrapper = GitCommandWrapper(client=mock_client)
        result = wrapper.get_commit_hash(short=False)

        assert result == "abc1234567890abcdef"

    def test_is_clean_working_tree_clean(self) -> None:
        """is_clean_working_tree returns True for clean tree."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.execute_simple.return_value = make_result(output="")

        wrapper = GitCommandWrapper(client=mock_client)
        result = wrapper.is_clean_working_tree()

        assert result is True

    def test_is_clean_working_tree_dirty(self) -> None:
        """is_clean_working_tree returns False for dirty tree."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.execute_simple.return_value = make_result(output=" M modified_file.py\n")

        wrapper = GitCommandWrapper(client=mock_client)
        result = wrapper.is_clean_working_tree()

        assert result is False


class TestDockerCommandWrapper:
    """Tests for DockerCommandWrapper class."""

    def test_is_running_true(self) -> None:
        """is_running returns True when Docker is available."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.execute_simple.return_value = make_result(success=True)

        wrapper = DockerCommandWrapper(client=mock_client)
        result = wrapper.is_running()

        assert result is True

    def test_is_running_false(self) -> None:
        """is_running returns False when Docker is not available."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.execute_simple.return_value = make_result(success=False)

        wrapper = DockerCommandWrapper(client=mock_client)
        result = wrapper.is_running()

        assert result is False

    def test_list_containers(self) -> None:
        """list_containers returns container IDs."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.execute_simple.return_value = make_result(output="abc123\ndef456\n")

        wrapper = DockerCommandWrapper(client=mock_client)
        result = wrapper.list_containers()

        assert result == ["abc123", "def456"]

    def test_list_containers_all(self) -> None:
        """list_containers with all=True includes -a flag."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.execute_simple.return_value = make_result(output="")

        wrapper = DockerCommandWrapper(client=mock_client)
        wrapper.list_containers(all_containers=True)

        call_args = mock_client.execute_simple.call_args[0][0]
        assert "-a" in call_args

    def test_get_image_tags(self) -> None:
        """get_image_tags returns tags."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.execute_simple.return_value = make_result(output="latest\nv1.0\nv2.0\n")

        wrapper = DockerCommandWrapper(client=mock_client)
        result = wrapper.get_image_tags("myimage")

        assert result == ["latest", "v1.0", "v2.0"]


class TestKubernetesCommandWrapper:
    """Tests for KubernetesCommandWrapper class."""

    def test_skip_tls_verify_flag(self) -> None:
        """skip_tls_verify adds insecure flag."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.execute_simple.return_value = make_result(output="")

        wrapper = KubernetesCommandWrapper(client=mock_client, skip_tls_verify=True)
        wrapper.get_contexts()

        call_args = mock_client.execute_simple.call_args[0][0]
        assert "--insecure-skip-tls-verify" in call_args

    def test_get_contexts(self) -> None:
        """get_contexts returns context list."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.execute_simple.return_value = make_result(output="context1\ncontext2\n")

        wrapper = KubernetesCommandWrapper(client=mock_client)
        result = wrapper.get_contexts()

        assert result == ["context1", "context2"]

    def test_get_current_context(self) -> None:
        """get_current_context returns context name."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.execute_simple.return_value = make_result(output="my-context\n")

        wrapper = KubernetesCommandWrapper(client=mock_client)
        result = wrapper.get_current_context()

        assert result == "my-context"

    def test_set_context(self) -> None:
        """set_context calls kubectl with context."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.execute_simple.return_value = make_result()

        wrapper = KubernetesCommandWrapper(client=mock_client)
        wrapper.set_context("new-context")

        call_args = mock_client.execute_simple.call_args[0][0]
        assert "use-context" in call_args
        assert "new-context" in call_args

    def test_setup_kubectl_caches(self) -> None:
        """setup_kubectl caches result."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.execute_simple.return_value = make_result()

        wrapper = KubernetesCommandWrapper(client=mock_client)
        wrapper.setup_kubectl()
        wrapper.setup_kubectl()  # Second call

        # Should only call execute_simple once
        assert mock_client.execute_simple.call_count == 1


class TestSystemCommandWrapper:
    """Tests for SystemCommandWrapper class."""

    def test_get_disk_usage(self) -> None:
        """get_disk_usage returns disk info."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.execute_simple.return_value = make_result(
            output="Filesystem Size Used Avail Use% Mounted\n/dev/sda1 100G 50G 50G 50% /\n"
        )

        wrapper = SystemCommandWrapper(client=mock_client)
        result = wrapper.get_disk_usage()

        assert "Size" in result or "Filesystem" in result

    def test_check_port_open(self) -> None:
        """check_port_open uses socket."""
        wrapper = SystemCommandWrapper()
        # Test against a port that should be closed
        result = wrapper.check_port_open("127.0.0.1", 59999, timeout=1)
        assert isinstance(result, bool)

    def test_get_process_info(self) -> None:
        """get_process_info returns process list."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.execute_simple.return_value = make_result(output="123 python\n456 python3\n")

        wrapper = SystemCommandWrapper(client=mock_client)
        result = wrapper.get_process_info("python")

        assert len(result) == 2
        assert result[0]["pid"] == "123"


class TestCustomCommandWrapper:
    """Tests for CustomCommandWrapper class."""

    def test_execute_basic(self) -> None:
        """execute runs command with arguments."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.execute_command.return_value = make_result(output="success")
        mock_client.config = MagicMock(verbose=False)

        wrapper = CustomCommandWrapper("myapp", client=mock_client)
        result = wrapper.execute(["--version"])

        assert result.output == "success"
        call_args = mock_client.execute_command.call_args[0][0]
        assert call_args == ["myapp", "--version"]

    def test_execute_with_default_args(self) -> None:
        """execute includes default arguments."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.execute_command.return_value = make_result()
        mock_client.config = MagicMock(verbose=False)

        wrapper = CustomCommandWrapper("myapp", client=mock_client, default_args=["--verbose"])
        wrapper.execute(["action"])

        call_args = mock_client.execute_command.call_args[0][0]
        assert call_args == ["myapp", "--verbose", "action"]

    def test_is_available(self) -> None:
        """is_available checks command availability."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.test_command_available.return_value = True

        wrapper = CustomCommandWrapper("myapp", client=mock_client)
        result = wrapper.is_available()

        assert result is True
        mock_client.test_command_available.assert_called_with("myapp")

    def test_get_version(self) -> None:
        """get_version returns version string."""
        mock_client = MagicMock(spec=SubprocessClient)
        mock_client.get_command_version.return_value = "1.0.0"

        wrapper = CustomCommandWrapper("myapp", client=mock_client)
        result = wrapper.get_version()

        assert result == "1.0.0"


class TestCreateCommandWrapper:
    """Tests for create_command_wrapper factory function."""

    def test_creates_wrapper(self) -> None:
        """Factory creates CustomCommandWrapper."""
        wrapper = create_command_wrapper("myapp")
        assert isinstance(wrapper, CustomCommandWrapper)
        assert wrapper.command_name == "myapp"

    def test_with_default_args(self) -> None:
        """Factory sets default_args."""
        wrapper = create_command_wrapper("myapp", default_args=["--debug"])
        assert wrapper.default_args == ["--debug"]

    def test_with_timeout(self) -> None:
        """Factory sets timeout in client config."""
        wrapper = create_command_wrapper("myapp", timeout=60)
        assert wrapper.client.config.timeout == 60

    def test_with_verbose(self) -> None:
        """Factory sets verbose in client config."""
        wrapper = create_command_wrapper("myapp", verbose=True)
        assert wrapper.client.config.verbose is True
