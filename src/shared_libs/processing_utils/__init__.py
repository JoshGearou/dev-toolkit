"""
Shared processing utilities for batch operations, pagination, and concurrent processing.

This module provides reusable patterns extracted from asset_management and log_parser
projects that are applicable to any batch data processing tasks.

Available modules:
- batch_processor: ThreadPoolExecutor-based concurrent processing
- pagination_manager: Generic pagination logic for APIs and large datasets
"""

from .batch_processor import BatchProcessor, ConcurrentProcessor, ProcessingStats
from .pagination_manager import PageConfig, PaginationManager, PaginationResult

__all__ = [
    "BatchProcessor",
    "ConcurrentProcessor",
    "ProcessingStats",
    "PaginationManager",
    "PageConfig",
    "PaginationResult",
]
