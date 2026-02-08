"""
Authentication utilities for interactive auth flows.

This module provides utilities for handling device authentication flows
commonly used with cloud services (Azure, AWS, etc.).
"""

import re
import sys


def check_for_device_auth(output: str) -> bool:
    """
    Check if output contains device authentication prompts.

    Returns True if device auth is detected (e.g., OAuth device flow prompts).

    Args:
        output: Command output text to check for auth patterns

    Returns:
        True if device authentication is detected, False otherwise
    """
    auth_patterns = [
        r"use a web browser to open.*devicelogin",
        r"enter the code [A-Z0-9]{6,}",
        r"https://microsoft\.com/devicelogin",
        r"To sign in.*authenticate",
        r"device code:",
        r"user code:",
    ]

    output_lower = output.lower()
    for pattern in auth_patterns:
        if re.search(pattern, output_lower):
            return True
    return False


def display_auth_prompt(output: str) -> None:
    """
    Display authentication prompts to the user.

    Args:
        output: Authentication message to display
    """
    print("\n" + "=" * 60)
    print("⚠️  AUTHENTICATION REQUIRED")
    print("=" * 60)
    print(output)
    print("=" * 60)
    print("\nPlease complete authentication in your browser, " "then press Enter to continue...")
    print("(The script will wait for authentication to complete)")
    print("=" * 60 + "\n")
    sys.stdout.flush()
