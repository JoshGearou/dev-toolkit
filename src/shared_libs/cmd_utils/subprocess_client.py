"""
Generic subprocess client with timeout, retry logic, and configurable error handling.

This module provides a robust foundation for executing external commands across
all Python projects in the workspace.
"""

import os
import random
import subprocess

# Import error handling from the common module
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from ..common.error_handling import ErrorInfo, ErrorPatternDetector

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class RetryStrategy(ABC):
    """
    Abstract base class for retry strategies.

    Implement this to customize retry behavior including delay calculation
    and retry decision logic based on error output.
    """

    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay before the next retry attempt.

        Args:
            attempt: Zero-based attempt number (0 = first retry after initial failure)

        Returns:
            Delay in seconds before the next attempt
        """

    @abstractmethod
    def should_retry(self, error_output: str, return_code: int) -> bool:
        """
        Determine if a retry should be attempted based on the error.

        Args:
            error_output: Combined stdout/stderr from the failed command
            return_code: Process return code

        Returns:
            True if retry should be attempted, False otherwise
        """


@dataclass
class ConstantDelayStrategy(RetryStrategy):
    """Simple retry strategy with constant delay between attempts."""

    delay: float = 1.0

    def get_delay(self, attempt: int) -> float:
        """Return constant delay regardless of attempt number."""
        return self.delay

    def should_retry(self, error_output: str, return_code: int) -> bool:
        """Always retry (let max retries handle termination)."""
        return True


@dataclass
class ExponentialBackoffStrategy(RetryStrategy):
    """
    Retry strategy with exponential backoff and jitter.

    Implements exponential delay growth with optional jitter to prevent
    thundering herd problems when multiple clients retry simultaneously.

    Example:
        strategy = ExponentialBackoffStrategy(
            initial_delay=2.0,
            max_delay=300.0,
            jitter=0.1,  # ±10% randomization
            retry_patterns=["rate limit", "429", "try again"]
        )
    """

    initial_delay: float = 2.0
    max_delay: float = 300.0
    jitter: float = 0.1  # ±10% randomization to prevent thundering herd
    retry_patterns: List[str] = field(default_factory=list)

    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay with exponential backoff and jitter.

        Delay grows as: initial_delay * 2^attempt, capped at max_delay.
        Jitter adds random variation of ±jitter% to prevent synchronized retries.

        Args:
            attempt: Zero-based attempt number

        Returns:
            Delay in seconds with jitter applied
        """
        base_delay: float = min(self.initial_delay * (2**attempt), self.max_delay)

        # Add jitter: random value between -jitter% and +jitter%
        if self.jitter > 0:
            jitter_range: float = base_delay * self.jitter
            jitter_value: float = random.uniform(-jitter_range, jitter_range)
            return float(max(0.0, base_delay + jitter_value))

        return float(base_delay)

    def should_retry(self, error_output: str, return_code: int) -> bool:
        """
        Determine if retry is appropriate based on error patterns.

        If retry_patterns is empty, always returns True.
        Otherwise, returns True only if any pattern matches the error output.

        Args:
            error_output: Combined stdout/stderr from the failed command
            return_code: Process return code

        Returns:
            True if retry patterns match or no patterns configured
        """
        if not self.retry_patterns:
            return True

        error_lower = error_output.lower()
        return any(pattern.lower() in error_lower for pattern in self.retry_patterns)


@dataclass
class CommandResult:
    """Result of a command execution."""

    success: bool
    output: str
    error_output: str
    return_code: int
    command: str
    execution_time: float
    error_info: Optional[ErrorInfo] = None


@dataclass
class CommandConfig:
    """Configuration for command execution."""

    timeout: int = 30
    retries: int = 0
    retry_delay: float = 1.0  # Used when retry_strategy is None (backward compat)
    combine_output: bool = True
    check_return_code: bool = True
    verbose: bool = False
    custom_error_patterns: Optional[Dict[str, Dict[str, Any]]] = None
    retry_strategy: Optional[RetryStrategy] = None  # Overrides retry_delay when set


class SubprocessClient:
    """
    Generic client for robust subprocess execution with error handling.

    Features:
    - Configurable timeout and retry logic
    - Integrated error pattern detection
    - Flexible command building
    - Consistent result format
    - Verbose debugging support
    """

    def __init__(self, config: Optional[CommandConfig] = None):
        """
        Initialize subprocess client.

        Args:
            config: Command configuration (uses defaults if None)
        """
        self.config = config or CommandConfig()

        # Setup error detector with custom patterns if provided
        self.error_detector = ErrorPatternDetector(timeout=self.config.timeout)
        if self.config.custom_error_patterns:
            for pattern, pattern_config in self.config.custom_error_patterns.items():
                self.error_detector.add_simple_pattern(
                    pattern=pattern,
                    error_type=pattern_config.get("error_type", "custom"),
                    message=pattern_config.get("message", "Custom error detected"),
                    suggestion=pattern_config.get("suggestion", ""),
                    recoverable=pattern_config.get("recoverable", True),
                )

    def execute_command(
        self,
        command: Union[str, List[str]],
        override_config: Optional[CommandConfig] = None,
        env: Optional[Dict[str, str]] = None,
        working_dir: Optional[str] = None,
    ) -> CommandResult:
        """
        Execute a command with robust error handling and retry logic.

        Args:
            command: Command to execute (string or list of arguments)
            override_config: Override default configuration for this command
            env: Environment variables for the command
            working_dir: Working directory for command execution

        Returns:
            CommandResult with execution details
        """
        # Use override config if provided, otherwise use instance config
        config = override_config or self.config

        # Convert command to list format if needed
        cmd_list = command.split() if isinstance(command, str) else command
        cmd_string = " ".join(cmd_list)

        if config.verbose:
            print(f"Executing command: {cmd_string}")
            if working_dir:
                print(f"Working directory: {working_dir}")

        # Attempt execution with retries
        last_result = None
        start_time = time.time()

        for attempt in range(config.retries + 1):
            if attempt > 0:
                # Calculate delay using strategy or fallback to fixed delay
                if config.retry_strategy:
                    delay = config.retry_strategy.get_delay(attempt - 1)
                else:
                    delay = config.retry_delay

                if config.verbose:
                    print(f"Retry attempt {attempt}/{config.retries} (delay: {delay:.2f}s)")
                time.sleep(delay)

            try:
                # Execute the command
                process_result = subprocess.run(
                    cmd_list,
                    capture_output=True,
                    text=True,
                    timeout=config.timeout,
                    check=False,  # We handle return codes ourselves
                    env=env,
                    cwd=working_dir,
                )

                execution_time = time.time() - start_time

                # Prepare output
                stdout = process_result.stdout or ""
                stderr = process_result.stderr or ""

                if config.combine_output:
                    combined_output = stdout + stderr
                    output = combined_output
                    error_output = stderr
                else:
                    output = stdout
                    error_output = stderr

                if config.verbose:
                    print(f"Command return code: {process_result.returncode}")
                    print(f"Output length: {len(output)} characters")

                # Detect error patterns
                error_info = self.error_detector.detect_error_patterns(output, process_result.returncode, cmd_string)

                # Determine success
                success = process_result.returncode == 0 and (not config.check_return_code or not error_info.is_error)

                last_result = CommandResult(
                    success=success,
                    output=output,
                    error_output=error_output,
                    return_code=process_result.returncode,
                    command=cmd_string,
                    execution_time=execution_time,
                    error_info=error_info,
                )

                # If successful or error is not recoverable, break retry loop
                if success or not error_info.recoverable:
                    break

                # Check if retry strategy says we should retry
                if config.retry_strategy:
                    if not config.retry_strategy.should_retry(output, process_result.returncode):
                        if config.verbose:
                            print("Retry strategy indicates no retry for this error")
                        break

                if config.verbose and error_info.is_error:
                    print(f"Attempt {attempt + 1} failed: {error_info.message}")
                    if error_info.recoverable and attempt < config.retries:
                        # Calculate next delay for verbose output
                        if config.retry_strategy:
                            next_delay = config.retry_strategy.get_delay(attempt)
                        else:
                            next_delay = config.retry_delay
                        print(f"Will retry in {next_delay:.2f} seconds...")

            except subprocess.TimeoutExpired:
                execution_time = time.time() - start_time
                timeout_error = ErrorInfo(
                    error_type="timeout",
                    is_error=True,
                    message=f"Command timed out after {config.timeout} seconds",
                    suggestion="Try increasing timeout or check for hanging processes",
                    recoverable=True,
                )

                last_result = CommandResult(
                    success=False,
                    output=f"Command timed out after {config.timeout} seconds",
                    error_output="",
                    return_code=124,  # Standard timeout return code
                    command=cmd_string,
                    execution_time=execution_time,
                    error_info=timeout_error,
                )

                if config.verbose:
                    print(f"Command timed out after {config.timeout} seconds")

                # Retry on timeout if configured
                if attempt < config.retries:
                    continue
                else:
                    break

            except FileNotFoundError:
                execution_time = time.time() - start_time
                cmd_name = cmd_list[0] if cmd_list else "unknown"
                not_found_error = ErrorInfo(
                    error_type="command-not-found",
                    is_error=True,
                    message=f"Command not found: {cmd_name}",
                    suggestion="Ensure the command is installed and in PATH",
                    recoverable=False,
                )

                last_result = CommandResult(
                    success=False,
                    output=f"Command not found: {cmd_name}",
                    error_output="",
                    return_code=127,  # Standard command not found return code
                    command=cmd_string,
                    execution_time=execution_time,
                    error_info=not_found_error,
                )

                if config.verbose:
                    print(f"Command not found: {cmd_name}")

                # Don't retry for command not found
                break

            except Exception as e:
                execution_time = time.time() - start_time
                exception_error = ErrorInfo(
                    error_type="execution-error",
                    is_error=True,
                    message=f"Command execution failed: {str(e)}",
                    suggestion="Check command syntax and system resources",
                    recoverable=True,
                )

                last_result = CommandResult(
                    success=False,
                    output=f"Execution error: {str(e)}",
                    error_output="",
                    return_code=1,
                    command=cmd_string,
                    execution_time=execution_time,
                    error_info=exception_error,
                )

                if config.verbose:
                    print(f"Command execution failed: {str(e)}")

                # Retry on general exceptions if configured
                if attempt < config.retries:
                    continue
                else:
                    break

        return last_result or CommandResult(
            success=False,
            output="No execution attempted",
            error_output="",
            return_code=1,
            command=cmd_string,
            execution_time=0.0,
            error_info=ErrorInfo("no-execution", True, "No execution attempted", "", False),
        )

    def execute_simple(self, command: Union[str, List[str]], timeout: int = 30, verbose: bool = False) -> CommandResult:
        """
        Simple command execution with minimal configuration.

        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            verbose: Enable verbose output

        Returns:
            CommandResult
        """
        simple_config = CommandConfig(timeout=timeout, verbose=verbose, retries=0)
        return self.execute_command(command, override_config=simple_config)

    def test_command_available(self, command: str) -> bool:
        """
        Test if a command is available in the system PATH.

        Args:
            command: Command name to test

        Returns:
            True if command is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["which", command] if os.name != "nt" else ["where", command],
                capture_output=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0
        except BaseException:
            return False

    def get_command_version(self, command: str, version_arg: str = "--version") -> Optional[str]:
        """
        Get version information for a command.

        Args:
            command: Command name
            version_arg: Version argument (default: --version)

        Returns:
            Version string if successful, None otherwise
        """
        try:
            result = self.execute_simple([command, version_arg], timeout=10)
            if result.success:
                # Return first line of output, cleaned up
                return result.output.split("\n")[0].strip()
            return None
        except BaseException:
            return None


def create_subprocess_client(
    timeout: int = 30,
    retries: int = 0,
    verbose: bool = False,
    custom_patterns: Optional[Dict[str, Dict[str, Any]]] = None,
) -> SubprocessClient:
    """
    Create a subprocess client with common configuration.

    Args:
        timeout: Default command timeout
        retries: Number of retry attempts
        verbose: Enable verbose output
        custom_patterns: Custom error patterns for detection

    Returns:
        Configured SubprocessClient
    """
    config = CommandConfig(
        timeout=timeout,
        retries=retries,
        verbose=verbose,
        custom_error_patterns=custom_patterns,
    )
    return SubprocessClient(config)
