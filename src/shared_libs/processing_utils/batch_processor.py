"""
Generic batch processing utilities using ThreadPoolExecutor.

Provides reusable patterns for concurrent processing extracted from
asset_management and log_parser projects.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, List, Optional, Protocol, TypeVar

T = TypeVar("T")
R = TypeVar("R")
T_contra = TypeVar("T_contra", contravariant=True)
R_co = TypeVar("R_co", covariant=True)


@dataclass
class ProcessingStats:
    """Statistics for tracking batch processing performance."""

    total_items: int = 0
    processed_items: int = 0
    failed_items: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    cache_stats: Dict[str, int] = field(default_factory=dict)

    def start(self) -> None:
        """Start timing the processing."""
        self.start_time = time.time()

    def finish(self) -> None:
        """Finish timing the processing."""
        self.end_time = time.time()

    @property
    def duration(self) -> Optional[float]:
        """Get processing duration in seconds."""
        if self.start_time is not None and self.end_time is not None:
            return self.end_time - self.start_time
        return None

    @property
    def success_rate(self) -> float:
        """Get success rate as a percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100.0


class ProcessingFunction(Protocol, Generic[T_contra, R_co]):
    """Protocol for processing functions used by BatchProcessor."""

    def __call__(self, item: T_contra, *args: Any, **kwargs: Any) -> Optional[R_co]:
        """Process a single item and return result or None if filtered."""
        ...


class BatchProcessor(Generic[T, R]):
    """
    Generic batch processor using ThreadPoolExecutor.

    Provides concurrent processing of items with error handling,
    progress tracking, and statistics collection.

    Example:
        def process_item(item: str) -> str:
            return item.upper()

        processor = BatchProcessor(process_item, max_workers=5)
        results = processor.process_batch(["a", "b", "c"])
    """

    def __init__(
        self,
        process_func: ProcessingFunction[T, R],
        max_workers: int = 10,
        enable_stats: bool = True,
    ) -> None:
        """
        Initialize batch processor.

        Args:
            process_func: Function to process each item
            max_workers: Maximum number of worker threads
            enable_stats: Whether to collect processing statistics
        """
        self.process_func = process_func
        self.max_workers = max_workers
        self.enable_stats = enable_stats
        self.stats = ProcessingStats() if enable_stats else None

    def process_batch(
        self,
        items: List[T],
        *args: Any,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        **kwargs: Any,
    ) -> List[R]:
        """
        Process a batch of items concurrently.

        Args:
            items: List of items to process
            *args: Additional arguments passed to process_func
            progress_callback: Optional callback for progress updates
            **kwargs: Additional keyword arguments passed to process_func

        Returns:
            List of successful processing results
        """
        if self.stats:
            self.stats.total_items = len(items)
            self.stats.start()

        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_item = {executor.submit(self.process_func, item, *args, **kwargs): item for item in items}

            # Collect results as they complete
            for i, future in enumerate(as_completed(future_to_item), 1):
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                        if self.stats:
                            self.stats.processed_items += 1
                except Exception as e:
                    item = future_to_item[future]
                    print(f"Error processing item {item}: {e}")
                    if self.stats:
                        self.stats.failed_items += 1

                # Call progress callback if provided
                if progress_callback:
                    progress_callback(i, len(items))

        if self.stats:
            self.stats.finish()

        return results

    def get_stats(self) -> Optional[ProcessingStats]:
        """Get processing statistics if enabled."""
        return self.stats


class ConcurrentProcessor:
    """
    Utility class for concurrent processing with shared caches and locks.

    Provides the pattern used in asset_management for processing with
    thread-safe caches and statistics collection.
    """

    def __init__(self, max_workers: int = 10):
        """Initialize concurrent processor with specified worker count."""
        self.max_workers = max_workers
        self.caches: Dict[str, Dict[Any, Any]] = {}
        self.lock = threading.Lock()

    def create_cache(self, name: str) -> Dict[Any, Any]:
        """Create a new shared cache."""
        self.caches[name] = {}
        return self.caches[name]

    def get_cache(self, name: str) -> Dict[Any, Any]:
        """Get an existing cache by name."""
        return self.caches.get(name, {})

    def process_with_cache(
        self,
        items: List[T],
        process_func: Callable[[T, Dict[str, Dict[Any, Any]], threading.Lock], Optional[R]],
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[R]:
        """
        Process items with shared caches and thread safety.

        Args:
            items: Items to process
            process_func: Function that takes (item, caches, lock) and returns result
            progress_callback: Optional callback for logging progress

        Returns:
            List of successful results
        """
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(process_func, item, self.caches, self.lock) for item in items]

            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    if progress_callback:
                        progress_callback(f"Error processing item: {e}")

        return results

    def get_cache_stats(self) -> Dict[str, int]:
        """Get statistics about cache usage."""
        return {name: len(cache) for name, cache in self.caches.items()}


def create_batch_processor(process_func: ProcessingFunction[T, R], max_workers: int = 10) -> BatchProcessor[T, R]:
    """
    Convenience function to create a BatchProcessor.

    Args:
        process_func: Function to process each item
        max_workers: Maximum number of worker threads

    Returns:
        Configured BatchProcessor instance
    """
    return BatchProcessor(process_func, max_workers)


def create_concurrent_processor(max_workers: int = 10) -> ConcurrentProcessor:
    """
    Convenience function to create a ConcurrentProcessor.

    Args:
        max_workers: Maximum number of worker threads

    Returns:
        Configured ConcurrentProcessor instance
    """
    return ConcurrentProcessor(max_workers)
