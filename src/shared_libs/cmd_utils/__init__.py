"""
Command utilities module for shared libraries.

This module provides robust command execution utilities:
- Subprocess execution with timeout and retry logic
- External command wrappers (go-status, kubectl, acl-tool, etc.)
- Timeout management and error handling
- Command result parsing and validation

These utilities standardize external command execution across all projects.
"""

from .command_wrappers import (
    CustomCommandWrapper,
    DockerCommandWrapper,
    GitCommandWrapper,
    KubernetesCommandWrapper,
    SystemCommandWrapper,
    create_command_wrapper,
)

# Command utilities - implemented
from .subprocess_client import (
    CommandConfig,
    CommandResult,
    ConstantDelayStrategy,
    ExponentialBackoffStrategy,
    RetryStrategy,
    SubprocessClient,
    create_subprocess_client,
)
from .wrapper_manager import (
    PythonWrapperManager,
    WrapperError,
    create_thin_wrapper,
    setup_bash_environment_integration,
)

# Future imports will be added as modules are implemented:
# from .timeout_manager import TimeoutManager

__all__ = [
    # Core subprocess utilities
    "SubprocessClient",
    "CommandConfig",
    "CommandResult",
    "create_subprocess_client",
    # Retry strategies
    "RetryStrategy",
    "ConstantDelayStrategy",
    "ExponentialBackoffStrategy",
    # Command wrappers
    "GitCommandWrapper",
    "DockerCommandWrapper",
    "KubernetesCommandWrapper",
    "SystemCommandWrapper",
    "CustomCommandWrapper",
    "create_command_wrapper",
    # Wrapper utilities
    "PythonWrapperManager",
    "WrapperError",
    "create_thin_wrapper",
    "setup_bash_environment_integration",
]
