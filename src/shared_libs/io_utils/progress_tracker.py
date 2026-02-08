"""
Progress tracking and time estimation utilities.

This module provides utilities for displaying progress bars and estimating
remaining time for batch processing operations.
"""


class ProgressTracker:
    """
    Progress tracking and time estimation utilities for batch operations.
    """

    @staticmethod
    def display_progress_bar(current: int, total: int, width: int = 50) -> str:
        """
        Generate a simple text-based progress bar.

        Args:
            current: Current progress count
            total: Total items to process
            width: Width of progress bar in characters

        Returns:
            Formatted progress bar string
        """
        if total == 0:
            return "[" + "=" * width + "] 100%"  # noqa: E501

        percentage = current / total
        filled_width = int(width * percentage)

        bar = "=" * filled_width + "-" * (width - filled_width)
        percent_text = f"{percentage * 100:.1f}%"

        return f"[{bar}] {percent_text}"

    @staticmethod
    def estimate_remaining_time(current: int, total: int, elapsed_time: float) -> str:
        """
        Estimate remaining processing time.

        Args:
            current: Current progress count
            total: Total items to process
            elapsed_time: Time elapsed so far in seconds

        Returns:
            Formatted time estimate string
        """
        if current == 0:
            return "estimating..."

        avg_time_per_item = elapsed_time / current
        remaining_items = total - current
        remaining_seconds = avg_time_per_item * remaining_items

        if remaining_seconds < 60:
            return f"{remaining_seconds:.0f}s remaining"
        elif remaining_seconds < 3600:
            minutes = remaining_seconds / 60
            return f"{minutes:.1f}m remaining"
        else:
            hours = remaining_seconds / 3600
            return f"{hours:.1f}h remaining"
