#!/usr/bin/env python3
"""
Test script for manager cache functionality.

This script tests the manager cache system implemented in the LDAP batch processor:
- Manager cache data structures (single cache with multi-key storage)
- Cache storage and retrieval strategy
- Cache statistics tracking
- Cache management utilities
"""

import os
import sys
import tempfile

from processing_utils.ldap_batch_processor import LDAPBatchProcessor  # type: ignore[import-not-found]

# Add parent directory to path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_manager_cache_initialization() -> None:
    """Test that cache data structures are properly initialized."""
    print("Testing cache initialization...")

    # Create a temporary password file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test_password")
        password_file = f.name

    try:
        processor = LDAPBatchProcessor(
            ldap_server="ldaps://test.example.com:636",
            ldap_username="testuser",
            ldap_base_dn="dc=example,dc=com",
            password_file=password_file,
            verbose=True,
        )

        # Verify cache structure is initialized (single manager_cache)
        assert hasattr(processor, "manager_cache")
        assert isinstance(processor.manager_cache, dict)

        # Verify cache starts empty
        assert len(processor.manager_cache) == 0

        # Verify statistics are initialized
        assert hasattr(processor, "cache_hits")
        assert hasattr(processor, "cache_misses")

        assert processor.cache_hits == 0
        assert processor.cache_misses == 0

        print("  ✓ Cache structures initialized correctly")

    finally:
        os.unlink(password_file)


def test_cache_storage_strategy() -> None:
    """Test the cache storage strategy."""
    print("\\nTesting cache storage strategy...")

    # Create a test processor instance
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test_password")
        password_file = f.name

    try:
        processor = LDAPBatchProcessor(
            ldap_server="ldaps://test.example.com:636",
            ldap_username="testuser",
            ldap_base_dn="dc=example,dc=com",
            password_file=password_file,
            verbose=True,
        )

        # Test person info with both username and display name
        complete_person_info = {
            "name": "John Smith",
            "display_name": "John Smith",
            "displayName": "John Smith",
            "cn": "John Smith",
            "username": "john.smith",
            "sAMAccountName": "john.smith",
            "title": "Software Engineer",
            "department": "Engineering",
            "email": "john.smith@example.com",
            "manager_name": "Jane Doe",
        }

        # Store the person info
        processor._store_in_cache("john.smith", complete_person_info)

        # Verify it's stored in cache
        cache_sizes = processor.get_cache_sizes()

        print(f"  Cache sizes after storage: {cache_sizes}")

        # Check that the entry can be retrieved by different keys
        username_key = "john.smith"
        display_name_key = processor._normalize_cache_key("John Smith")

        username_stored = username_key in processor.manager_cache
        displayname_stored = display_name_key in processor.manager_cache

        print(f"  ✓ Manager cache contains '{username_key}': {username_stored}")
        print(f"  ✓ Manager cache contains '{display_name_key}': {displayname_stored}")

        # Should be stored under at least one key
        assert username_stored or displayname_stored

    finally:
        os.unlink(password_file)


def test_cache_retrieval_priority() -> None:
    """Test the cache retrieval strategy."""
    print("\\nTesting cache retrieval...")

    # Create a test processor instance
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test_password")
        password_file = f.name

    try:
        processor = LDAPBatchProcessor(
            ldap_server="ldaps://test.example.com:636",
            ldap_username="testuser",
            ldap_base_dn="dc=example,dc=com",
            password_file=password_file,
            verbose=True,
        )

        # Create test data
        person_info = {
            "name": "Jane Doe",
            "username": "jane.doe",
            "title": "Manager",
        }

        # Store in cache
        processor._store_in_cache("jane.doe", person_info)

        # Reset statistics to track retrieval behavior
        processor.cache_hits = 0
        processor.cache_misses = 0

        # Test 1: Retrieve using username
        result1 = processor._get_from_cache("jane.doe")

        print(f"  Username lookup - Cache hits: {processor.cache_hits}")

        # Test 2: Retrieve using display name
        result2 = processor._get_from_cache("Jane Doe")

        print(f"  Display name lookup - Cache hits: {processor.cache_hits}")

        # Verify results - both should work due to multi-key storage
        username_worked = result1 is not None
        display_name_worked = result2 is not None

        print(f"  ✓ Username retrieval worked: {username_worked}")
        print(f"  ✓ Display name retrieval worked: {display_name_worked}")

        assert username_worked and display_name_worked

    finally:
        os.unlink(password_file)


def test_cache_miss_scenarios() -> None:
    """Test cache miss scenarios and statistics tracking."""
    print("\\nTesting cache miss scenarios...")

    # Create a test processor instance
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test_password")
        password_file = f.name

    try:
        processor = LDAPBatchProcessor(
            ldap_server="ldaps://test.example.com:636",
            ldap_username="testuser",
            ldap_base_dn="dc=example,dc=com",
            password_file=password_file,
            verbose=True,
        )

        # Test cache miss
        result = processor._get_from_cache("nonexistent.user")

        # Verify cache miss was recorded
        cache_miss_recorded = result is None and processor.cache_misses == 1

        print(f"  Cache misses: {processor.cache_misses}")
        print(f"  ✓ Cache miss properly recorded: {cache_miss_recorded}")

        assert cache_miss_recorded

    finally:
        os.unlink(password_file)


def test_not_found_caching() -> None:
    """Test caching of 'not found' results."""
    print("\\nTesting 'not found' result caching...")

    # Create a test processor instance
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test_password")
        password_file = f.name

    try:
        processor = LDAPBatchProcessor(
            ldap_server="ldaps://test.example.com:636",
            ldap_username="testuser",
            ldap_base_dn="dc=example,dc=com",
            password_file=password_file,
            verbose=True,
        )

        # Store "not found" result (empty dict)
        processor._store_in_cache("missing.user", {})

        # Try to retrieve it
        result = processor._get_from_cache("missing.user")

        # Verify "not found" is cached and retrievable
        not_found_cached = result == {} and processor.cache_hits == 1

        print(f"  Cache hits for 'not found': {processor.cache_hits}")
        print(f"  Retrieved result: {result}")
        print(f"  ✓ 'Not found' properly cached and retrieved: {not_found_cached}")

        assert not_found_cached

    finally:
        os.unlink(password_file)


def test_cache_management_utilities() -> None:
    """Test cache management utility methods."""
    print("\\nTesting cache management utilities...")

    # Create a test processor instance
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test_password")
        password_file = f.name

    try:
        processor = LDAPBatchProcessor(
            ldap_server="ldaps://test.example.com:636",
            ldap_username="testuser",
            ldap_base_dn="dc=example,dc=com",
            password_file=password_file,
            verbose=True,
        )

        # Add some test data to cache
        test_info = {"name": "Test User", "username": "test.user"}
        processor._store_in_cache("test.user", test_info)

        # Check cache sizes
        sizes_before = processor.get_cache_sizes()
        print(f"  Cache sizes before clear: {sizes_before}")

        # Clear all caches
        processor.clear_all_caches()

        # Check cache sizes after clear
        sizes_after = processor.get_cache_sizes()
        print(f"  Cache sizes after clear: {sizes_after}")

        # Verify everything was cleared
        all_cleared = len(processor.manager_cache) == 0 and processor.cache_hits == 0 and processor.cache_misses == 0

        print(f"  ✓ All caches and statistics cleared: {all_cleared}")

        assert all_cleared

    finally:
        os.unlink(password_file)


def test_statistics() -> None:
    """Test statistics functionality."""
    print("\\nTesting statistics...")

    # Create a test processor instance
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test_password")
        password_file = f.name

    try:
        processor = LDAPBatchProcessor(
            ldap_server="ldaps://test.example.com:636",
            ldap_username="testuser",
            ldap_base_dn="dc=example,dc=com",
            password_file=password_file,
            verbose=True,
        )

        # Generate some cache activity
        test_info = {"name": "Test User", "username": "test.user"}
        processor._store_in_cache("test.user", test_info)

        # Generate cache hits and misses
        processor._get_from_cache("test.user")  # Should hit cache
        processor._get_from_cache("Test User")  # Should hit cache
        processor._get_from_cache("nonexistent")  # Should be cache miss

        # Get statistics
        stats = processor.get_statistics()

        print("  Statistics:")
        for key, value in stats.items():
            print(f"    {key}: {value}")

        # Verify basic fields are present
        basic_fields = ["cache_hits", "cache_misses", "manager_cache_entries"]

        has_basic_fields = all(field in stats for field in basic_fields)

        print(f"  ✓ Basic statistics fields present: {has_basic_fields}")

        assert has_basic_fields

    finally:
        os.unlink(password_file)


def main() -> bool:
    """Run all manager cache tests."""
    print("Testing Manager Cache Functionality")
    print("=" * 50)

    try:
        # Run all tests
        test_manager_cache_initialization()
        test_cache_storage_strategy()
        test_cache_retrieval_priority()
        test_cache_miss_scenarios()
        test_not_found_caching()
        test_cache_management_utilities()
        test_statistics()

        # Summary - all tests passed if we reach here
        print("\\n" + "=" * 50)
        print("Manager Cache Test Results: All tests passed!")

        print("✓ All manager cache functionality working correctly!")
        print("\\nKey functionality verified:")
        print("- Manager cache system with multi-key storage")
        print("- Cache retrieval with key normalization")
        print("- Cache statistics and monitoring")
        print("- Cache key normalization")
        print("- Cache management utilities")
        print("\\nNext steps:")
        print("- Integration layer updates")
        print("- Performance benchmarking with real workloads")
        print("- Integration with asset management core")

        return True

    except Exception as e:
        print(f"\\n{'=' * 50}")
        print(f"Test failed with error: {e}")
        print("✗ Some tests failed. Please review implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
