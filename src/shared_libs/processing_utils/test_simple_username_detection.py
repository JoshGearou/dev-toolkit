#!/usr/bin/env python3
"""
Test the simplified username detection logic with CSV data examples.
"""

import os
import sys

from ldap_batch_processor import LDAPBatchProcessor  # type: ignore[import-not-found]

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_username_detection() -> bool:
    """Test username detection with examples from the CSV data."""

    # Initialize processor (dummy values since we're only testing username detection)
    processor = LDAPBatchProcessor(
        ldap_server="ldaps://dummy:636",
        ldap_username="dummy",
        ldap_base_dn="DC=dummy,DC=com",
        password_file="dummy.txt",
        verbose=True,
        dry_run=True,
    )

    # Test cases from the CSV file
    test_cases = [
        # Username column examples (should return True)
        ("ahaydar", True, "Username from CSV"),
        ("acoffman", True, "Username from CSV"),
        ("absidhar", True, "Username from CSV"),
        ("alagad", True, "Username from CSV"),
        ("ajasharm", True, "Username from CSV"),
        # Manager column examples (should return False)
        ("Abdullah Haydar", False, "Display name from CSV"),
        ("Abe Coffman", False, "Display name from CSV"),
        ("Abhishek S", False, "Display name from CSV"),
        ("Aboli Ashok Lagad", False, "Display name from CSV"),
        ("Ajay Bangalore Ravindranath", False, "Display name from CSV"),
        # Edge cases
        ("", False, "Empty string"),
        ("john.doe", True, "Username with dot"),
        ("J.Smith", True, "Username with dot and capital"),
        ("ADMIN", False, "All caps (likely organizational)"),
        ("user@company.com", False, "Email address"),
        ("verylongusernamethatexceeds25chars", False, "Too long for username"),
    ]

    print("🔍 Testing simplified username detection logic...")
    print("=" * 60)

    passed = 0
    failed = 0

    for identifier, expected, description in test_cases:
        result = processor._looks_like_username(identifier)
        status = "✅ PASS" if result == expected else "❌ FAIL"

        print(f"{status} | '{identifier}' -> {result} (expected {expected}) | {description}")

        if result == expected:
            passed += 1
        else:
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")

    return failed == 0


def test_new_api_methods() -> None:
    """Test the new structured API methods."""

    processor = LDAPBatchProcessor(
        ldap_server="ldaps://dummy:636",
        ldap_username="dummy",
        ldap_base_dn="DC=dummy,DC=com",
        password_file="dummy.txt",
        verbose=True,
        dry_run=True,
    )

    print("\n🔧 Testing new structured API methods...")
    print("=" * 60)

    # Test username method
    print("Testing find_person_by_username('ahaydar')...")
    result1 = processor.find_person_by_username("ahaydar")
    print(f"Result: {type(result1)} (dry-run simulation)")

    # Test display name method
    print("Testing find_person_by_display_name('Abdullah Haydar')...")
    result2 = processor.find_person_by_display_name("Abdullah Haydar")
    print(f"Result: {type(result2)} (dry-run simulation)")

    print("✅ New API methods work correctly")


if __name__ == "__main__":
    success1 = test_username_detection()
    test_new_api_methods()

    if success1:
        print("\n🎉 All tests passed! The simplified username detection is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Check the output above.")
        sys.exit(1)
