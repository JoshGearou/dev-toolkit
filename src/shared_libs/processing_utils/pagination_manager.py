"""
Generic pagination utilities for APIs and large datasets.

Provides reusable patterns for pagination extracted from asset_management
and log_parser projects.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, List, Optional, Protocol, TypeVar

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


@dataclass
class PageConfig:
    """Configuration for pagination parameters."""

    page_size: int = 100
    start_offset: int = 0
    max_items: Optional[int] = None

    def get_page_limit(self, current_count: int) -> int:
        """Get the limit for the current page based on max_items."""
        if self.max_items is None:
            return self.page_size
        return min(self.page_size, self.max_items - current_count)

    def should_continue(self, current_count: int) -> bool:
        """Check if pagination should continue."""
        if self.max_items is None:
            return True
        return current_count < self.max_items


@dataclass
class PaginationResult(Generic[T]):
    """Result of a paginated operation."""

    items: List[T]
    total_retrieved: int
    pages_processed: int
    has_more: bool = False


class DataFetcher(Protocol, Generic[T_co]):
    """Protocol for functions that fetch paginated data."""

    def __call__(self, start: int, count: int) -> Dict[str, Any]:
        """Fetch data starting at offset with count limit."""
        ...


class PaginationManager(Generic[T]):
    """
    Generic pagination manager for APIs and large datasets.

    Handles the common pattern of fetching data in pages with configurable
    page sizes, limits, and continuation logic.

    Example:
        def fetch_data(start: int, count: int) -> Dict[str, Any]:
            # API call returning {"elements": [...], "total": N}
            return api_client.get_items(start=start, count=count)

        paginator = PaginationManager(fetch_data)
        result = paginator.paginate(PageConfig(page_size=50, max_items=200))
    """

    def __init__(
        self,
        fetch_func: DataFetcher[T],
        elements_key: str = "elements",
        progress_callback: Optional[Callable[[int, int, int], None]] = None,
    ):
        """
        Initialize pagination manager.

        Args:
            fetch_func: Function to fetch data pages
            elements_key: Key in response dict containing the items list
            progress_callback: Optional callback for progress updates (page_num, items_in_page, total_items)
        """
        self.fetch_func = fetch_func
        self.elements_key = elements_key
        self.progress_callback = progress_callback

    def paginate(self, config: PageConfig) -> PaginationResult[T]:
        """
        Paginate through all available data.

        Args:
            config: Pagination configuration

        Returns:
            PaginationResult with all retrieved items and metadata
        """
        all_items: List[T] = []
        current_offset = config.start_offset
        page_num = 1

        while config.should_continue(len(all_items)):
            page_limit = config.get_page_limit(len(all_items))
            if page_limit <= 0:
                break

            # Fetch this page
            response = self.fetch_func(current_offset, page_limit)
            elements = response.get(self.elements_key, [])

            # No more data available
            if not elements:
                break

            all_items.extend(elements)

            # Progress callback
            if self.progress_callback:
                self.progress_callback(page_num, len(elements), len(all_items))

            # Check if this was a partial page (indicates end of data)
            if len(elements) < page_limit:
                break

            # Move to next page
            current_offset += config.page_size
            page_num += 1

        return PaginationResult(
            items=all_items,
            total_retrieved=len(all_items),
            pages_processed=page_num,
            has_more=config.should_continue(len(all_items)) and len(all_items) > 0,
        )

    def paginate_with_processor(self, config: PageConfig, process_func: Callable[[List[T]], List[Any]]) -> List[Any]:
        """
        Paginate and process each page immediately.

        Useful for memory-efficient processing of large datasets where
        you don't need to keep all items in memory at once.

        Args:
            config: Pagination configuration
            process_func: Function to process each page of items

        Returns:
            Combined results from processing all pages
        """
        all_results: List[T] = []
        current_offset = config.start_offset
        page_num = 1

        while config.should_continue(len(all_results)):
            page_limit = config.get_page_limit(len(all_results))
            if page_limit <= 0:
                break

            # Fetch this page
            response = self.fetch_func(current_offset, page_limit)
            elements = response.get(self.elements_key, [])

            if not elements:
                break

            # Process this page immediately
            page_results = process_func(elements)
            all_results.extend(page_results)

            # Progress callback
            if self.progress_callback:
                self.progress_callback(page_num, len(elements), len(all_results))

            # Check if this was a partial page
            if len(elements) < page_limit:
                break

            current_offset += config.page_size
            page_num += 1

        return all_results


def create_pagination_manager(fetch_func: DataFetcher[T], elements_key: str = "elements") -> PaginationManager[T]:
    """
    Convenience function to create a PaginationManager.

    Args:
        fetch_func: Function to fetch data pages
        elements_key: Key in response containing items list

    Returns:
        Configured PaginationManager instance
    """
    return PaginationManager(fetch_func, elements_key)


def create_page_config(page_size: int = 100, max_items: Optional[int] = None, start_offset: int = 0) -> PageConfig:
    """
    Convenience function to create PageConfig.

    Args:
        page_size: Number of items per page
        max_items: Maximum total items to retrieve
        start_offset: Starting offset for pagination

    Returns:
        Configured PageConfig instance
    """
    return PageConfig(page_size=page_size, max_items=max_items, start_offset=start_offset)
