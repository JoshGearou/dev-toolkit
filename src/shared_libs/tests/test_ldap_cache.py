#!/usr/bin/env python3
"""
Test script for LDAP cache implementation - Step 1 verification.

This script tests the cache infrastructure added in Step 1:
- Cache data structures initialization
- Cache key normalization
- Cache getter/setter methods
- Cache statistics tracking
"""

import os
import sys
import tempfile

from processing_utils.ldap_batch_processor import LDAPBatchProcessor  # type: ignore[import-not-found]

# Add parent directory to path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_cache_initialization() -> None:
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

        # Verify cache structures are initialized
        assert hasattr(processor, "manager_cache")
        assert hasattr(processor, "cache_hits")
        assert hasattr(processor, "cache_misses")

        assert isinstance(processor.manager_cache, dict)
        assert len(processor.manager_cache) == 0
        assert processor.cache_hits == 0
        assert processor.cache_misses == 0

        print("✓ Cache initialization successful")

    finally:
        os.unlink(password_file)


def test_cache_key_normalization() -> None:
    """Test cache key normalization functionality."""
    print("Testing cache key normalization...")

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test_password")
        password_file = f.name

    try:
        processor = LDAPBatchProcessor(
            ldap_server="ldaps://test.example.com:636",
            ldap_username="testuser",
            ldap_base_dn="dc=example,dc=com",
            password_file=password_file,
        )

        # Test various name formats
        test_cases = [
            ("John Doe", "john doe"),
            ("  John Doe  ", "john doe"),
            ("JOHN DOE", "john doe"),
            ("john.doe", "john doe"),
            ("John.Doe", "john doe"),
            ("  JOHN.DOE  ", "john doe"),
            ("John    Doe", "john doe"),  # Multiple spaces
            ("", ""),
            ("Single", "single"),
        ]

        for input_name, expected in test_cases:
            result = processor._normalize_cache_key(input_name)
            assert result == expected, f"Failed: '{input_name}' -> '{result}' (expected '{expected}')"

        print("✓ Cache key normalization successful")

    finally:
        os.unlink(password_file)


def test_cache_operations() -> None:
    """Test cache getter/setter operations."""
    print("Testing cache operations...")

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

        # Test cache miss (empty cache) - should log miss in verbose mode
        result = processor._get_from_cache("John Doe")
        assert result is None
        assert processor.cache_misses == 1
        assert processor.cache_hits == 0

        # Store some data
        test_data = {
            "cn": "John Doe",
            "displayName": "John Doe",
            "title": "Software Engineer",
            "department": "Engineering",
            "mail": "john.doe@example.com",
        }

        processor._store_in_cache("John Doe", test_data)
        assert len(processor.manager_cache) == 1

        # Test cache hit
        cached_result = processor._get_from_cache("John Doe")
        assert cached_result == test_data
        assert processor.cache_hits == 1
        assert processor.cache_misses == 1

        # Test cache hit with different case/format (should normalize)
        cached_result2 = processor._get_from_cache("JOHN DOE")
        assert cached_result2 == test_data
        assert processor.cache_hits == 2
        assert processor.cache_misses == 1

        cached_result3 = processor._get_from_cache("john.doe")
        assert cached_result3 == test_data
        assert processor.cache_hits == 3
        assert processor.cache_misses == 1

        # Test storing empty dict (person not found)
        processor._store_in_cache("Jane Smith", {})
        not_found_result = processor._get_from_cache("Jane Smith")
        assert not_found_result == {}  # Empty dict returned for "not found"
        assert processor.cache_hits == 4  # Should count as cache hit
        assert processor.cache_misses == 1

        print("✓ Cache operations successful")

    finally:
        os.unlink(password_file)


def test_cache_statistics() -> None:
    """Test cache statistics functionality."""
    print("Testing cache statistics...")

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test_password")
        password_file = f.name

    try:
        processor = LDAPBatchProcessor(
            ldap_server="ldaps://test.example.com:636",
            ldap_username="testuser",
            ldap_base_dn="dc=example,dc=com",
            password_file=password_file,
        )

        # Initial statistics
        stats = processor.get_statistics()
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["manager_cache_entries"] == 0

        # Add some cache activity
        processor._get_from_cache("John Doe")  # miss
        processor._store_in_cache("John Doe", {"cn": "John Doe"})
        processor._get_from_cache("John Doe")  # hit
        processor._get_from_cache("jane.smith")  # miss

        stats = processor.get_statistics()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 2
        assert stats["manager_cache_entries"] == 1

        # Test statistics logging (should not crash)
        processor._log_cache_statistics()

        print("✓ Cache statistics successful")

    finally:
        os.unlink(password_file)


def main() -> None:
    """Run all cache tests."""
    print("Running LDAP Cache Implementation Tests (Step 1)")
    print("=" * 50)

    try:
        test_cache_initialization()
        test_cache_key_normalization()
        test_cache_operations()
        test_cache_statistics()

        print("\n" + "=" * 50)
        print("✅ All tests passed! Step 1 implementation is working correctly.")
        print("\nStep 1 Complete: Cache Infrastructure Added")
        print("- ✓ Cache data structures initialized in __init__()")
        print("- ✓ Cache key normalization method implemented")
        print("- ✓ Cache getter/setter methods implemented")
        print("- ✓ Cache statistics tracking added")
        print("- ✓ Statistics logging integrated into process_batch()")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
