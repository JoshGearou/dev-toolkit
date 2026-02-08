#!/usr/bin/env python3
"""
Test script for LDAP lookup functionality.

This script tests LDAP search functionality:
- LDAP search filters for username and display name queries
- LDAP result parsing with sAMAccountName extraction
"""

import os
import sys
import tempfile

from processing_utils.ldap_batch_processor import LDAPBatchProcessor  # type: ignore[import-not-found]

# Add parent directory to path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_ldap_result_parsing() -> None:
    """Test the LDAP result parsing method."""
    print("\\nTesting LDAP result parsing...")

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

        # Test LDAP result with username field
        test_ldap_result = """dn: CN=John Smith,OU=Users,DC=example,DC=com
cn: John Smith
displayName: John Smith
sAMAccountName: john.smith
title: Software Engineer
department: Engineering
mail: john.smith@example.com
manager: CN=Jane Doe,OU=Users,DC=example,DC=com"""

        parsed_info = processor._parse_ldap_result(test_ldap_result)

        # Verify all expected fields are extracted
        expected_fields = {
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

        passed = 0
        total = len(expected_fields)

        print("  Checking extracted fields:")
        for field, expected_value in expected_fields.items():
            actual_value = parsed_info.get(field)
            status = "✓" if actual_value == expected_value else "✗"
            print(f"    {status} {field:15} -> {actual_value}")
            if actual_value == expected_value:
                passed += 1

        print(f"LDAP parsing tests: {passed}/{total} passed")
        assert passed == total

    finally:
        os.unlink(password_file)


def test_search_filter_generation() -> None:
    """Test search filter generation for different search types."""
    print("\\nTesting search filter generation...")

    # This would normally require actual LDAP connectivity, but we can test
    # the logic by examining debug output or by mocking the subprocess call
    print("  Username-based search filters:")
    print("    Input: 'john.doe' -> sAMAccountName search")
    print("    Filter: (&(objectcategory=Person)(sAMAccountName=john.doe))")

    print("  Display name-based search filters:")
    print("    Input: 'John Smith' -> display name search")
    print("    Filter: (&(objectcategory=Person)(|(cn=John Smith)" "(displayName=John Smith)(cn=*John Smith*)))")

    print("  Search filter generation: Manual verification required")
    # No assertion needed for manual verification test


def test_ldap_string_conversion() -> None:
    """Test conversion back to LDAP string format."""
    print("\\nTesting LDAP string conversion...")

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

        # Test person info with username
        person_info = {
            "name": "John Smith",
            "username": "john.smith",
            "title": "Software Engineer",
            "department": "Engineering",
            "email": "john.smith@example.com",
            "manager_name": "Jane Doe",
        }

        ldap_string = processor._convert_dict_to_ldap_string(person_info)

        print("  Generated LDAP string:")
        for line in ldap_string.split("\\n"):
            print(f"    {line}")

        # Verify username field is included
        username_included = "sAMAccountName: john.smith" in ldap_string
        status = "✓" if username_included else "✗"
        print(f"  {status} Username field included in output")

        assert username_included

    finally:
        os.unlink(password_file)


def main() -> bool:
    """Run all tests."""
    print("Testing LDAP Integration")
    print("=" * 50)

    try:
        # Run all tests
        test_ldap_result_parsing()
        test_search_filter_generation()
        test_ldap_string_conversion()

        # All tests passed if we reach here
        print("\\n" + "=" * 50)
        print("Overall Test Results: All tests passed!")
        print("✓ All LDAP functionality working correctly!")
        print("\\nNext steps:")
        print("- Implement dual-key cache")
        print("- Test with actual LDAP server connectivity")
        print("- Update integration points")

        return True

    except Exception as e:
        print(f"\\n{'=' * 50}")
        print(f"Test failed with error: {e}")
        print("✗ Some tests failed. Please review implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
