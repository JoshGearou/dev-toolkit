"""
Tests for retry strategy implementations.
"""

import os
import sys

# Add src directory to path so shared_libs is importable as a package
src_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, src_root)

from shared_libs.cmd_utils.subprocess_client import (
    ConstantDelayStrategy,
    ExponentialBackoffStrategy,
)


class TestConstantDelayStrategy:
    """Tests for ConstantDelayStrategy."""

    def test_constant_delay(self) -> None:
        """Delay is constant regardless of attempt number."""
        strategy = ConstantDelayStrategy(delay=5.0)

        assert strategy.get_delay(0) == 5.0
        assert strategy.get_delay(1) == 5.0
        assert strategy.get_delay(10) == 5.0

    def test_default_delay(self) -> None:
        """Default delay is 1.0 seconds."""
        strategy = ConstantDelayStrategy()
        assert strategy.get_delay(0) == 1.0

    def test_always_retries(self) -> None:
        """ConstantDelayStrategy always returns True for should_retry."""
        strategy = ConstantDelayStrategy()

        assert strategy.should_retry("any error", 1)
        assert strategy.should_retry("", 0)
        assert strategy.should_retry("rate limit exceeded", 429)


class TestExponentialBackoffStrategy:
    """Tests for ExponentialBackoffStrategy."""

    def test_exponential_growth(self) -> None:
        """Delay grows exponentially with attempt number."""
        strategy = ExponentialBackoffStrategy(
            initial_delay=2.0,
            max_delay=300.0,
            jitter=0.0,  # Disable jitter for predictable testing
        )

        assert strategy.get_delay(0) == 2.0  # 2 * 2^0 = 2
        assert strategy.get_delay(1) == 4.0  # 2 * 2^1 = 4
        assert strategy.get_delay(2) == 8.0  # 2 * 2^2 = 8
        assert strategy.get_delay(3) == 16.0  # 2 * 2^3 = 16

    def test_max_delay_cap(self) -> None:
        """Delay is capped at max_delay."""
        strategy = ExponentialBackoffStrategy(
            initial_delay=2.0,
            max_delay=50.0,
            jitter=0.0,
        )

        # 2 * 2^5 = 64, but capped at 50
        assert strategy.get_delay(5) == 50.0
        # Higher attempts still capped
        assert strategy.get_delay(10) == 50.0

    def test_jitter_range(self) -> None:
        """Jitter produces values within expected range."""
        strategy = ExponentialBackoffStrategy(
            initial_delay=10.0,
            max_delay=300.0,
            jitter=0.1,  # ±10%
        )

        # With 10% jitter on base delay of 10.0, values should be 9.0-11.0
        delays = [strategy.get_delay(0) for _ in range(100)]

        assert all(9.0 <= d <= 11.0 for d in delays), f"Delays out of range: {delays}"
        # Check there's actual variation (not all the same)
        assert len(set(delays)) > 1, "Jitter should produce variation"

    def test_jitter_prevents_exact_values(self) -> None:
        """With jitter enabled, delays vary between calls."""
        strategy = ExponentialBackoffStrategy(
            initial_delay=10.0,
            jitter=0.2,  # ±20%
        )

        # Get multiple delays for same attempt
        delays = {strategy.get_delay(0) for _ in range(50)}

        # Should have multiple unique values due to jitter
        assert len(delays) > 1, "Jitter should cause variation in delays"

    def test_no_jitter_produces_exact_values(self) -> None:
        """With jitter=0, delays are exact."""
        strategy = ExponentialBackoffStrategy(
            initial_delay=5.0,
            jitter=0.0,
        )

        # Get multiple delays for same attempt
        delays = {strategy.get_delay(0) for _ in range(10)}

        # All should be identical
        assert len(delays) == 1
        assert delays == {5.0}

    def test_should_retry_no_patterns(self) -> None:
        """Without patterns, always returns True."""
        strategy = ExponentialBackoffStrategy(retry_patterns=[])

        assert strategy.should_retry("any error", 1)
        assert strategy.should_retry("", 0)
        assert strategy.should_retry("something else", 500)

    def test_should_retry_with_patterns(self) -> None:
        """With patterns, only retries when pattern matches."""
        strategy = ExponentialBackoffStrategy(retry_patterns=["rate limit", "429", "try again"])

        # Should retry - patterns match
        assert strategy.should_retry("Error: rate limit exceeded", 429)
        assert strategy.should_retry("HTTP 429 Too Many Requests", 429)
        assert strategy.should_retry("Please try again later", 500)

        # Should NOT retry - no pattern match
        assert not strategy.should_retry("Connection refused", 1)
        assert not strategy.should_retry("File not found", 1)
        assert not strategy.should_retry("", 1)

    def test_should_retry_case_insensitive(self) -> None:
        """Pattern matching is case-insensitive."""
        strategy = ExponentialBackoffStrategy(retry_patterns=["Rate Limit"])

        assert strategy.should_retry("RATE LIMIT exceeded", 429)
        assert strategy.should_retry("rate limit exceeded", 429)
        assert strategy.should_retry("Rate Limit exceeded", 429)

    def test_default_values(self) -> None:
        """Default values are reasonable."""
        strategy = ExponentialBackoffStrategy()

        assert strategy.initial_delay == 2.0
        assert strategy.max_delay == 300.0
        assert strategy.jitter == 0.1
        assert strategy.retry_patterns == []

    def test_delay_never_negative(self) -> None:
        """Delay is never negative even with large jitter."""
        strategy = ExponentialBackoffStrategy(
            initial_delay=0.1,
            jitter=0.9,  # ±90% - extreme case
        )

        delays = [strategy.get_delay(0) for _ in range(100)]
        assert all(d >= 0.0 for d in delays), "Delays should never be negative"
