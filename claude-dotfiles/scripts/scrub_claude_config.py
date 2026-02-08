#!/usr/bin/env python3
"""
Scrub secrets and PII from .claude.json config file.

Removes:
- API tokens and keys
- User UUIDs and identifiers
- Email addresses and personal names
- Organization identifiers
- File paths that may contain sensitive info
- Referral codes and links
- Session identifiers
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict


def scrub_value(value_type: str, key: str) -> str:
    """
    Replace value with consistent searchable format: <SCRUBBED:type:key>

    Args:
        value_type: Type of secret (uuid, email, token, pii, path, code)
        key: The JSON key name for context

    Returns:
        Scrubbed string in consistent format
    """
    return f"<SCRUBBED:{value_type}:{key}>"


def scrub_path(value: str) -> str:
    """Replace username in file paths only."""
    if not value or not isinstance(value, str):
        return value
    # Replace username in path only
    return re.sub(r'/Users/[^/]+', '/Users/<SCRUBBED:username>', value)


def scrub_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively scrub sensitive data from dictionary."""
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        # Scrub based on key patterns
        if key == 'GLEAN_API_TOKEN':
            result[key] = scrub_value('token', key) if value else value
        elif key == 'GITHUB_PERSONAL_ACCESS_TOKEN':
            result[key] = scrub_value('token', key) if value else value
        elif key == 'userID':
            result[key] = scrub_value('uuid', key) if value else value
        elif key == 'accountUuid':
            result[key] = scrub_value('uuid', key) if value else value
        elif key == 'organizationUuid':
            result[key] = scrub_value('uuid', key) if value else value
        elif key in ('emailAddress', 'email'):
            result[key] = scrub_value('email', key) if value else value
        elif key == 'displayName':
            result[key] = scrub_value('pii', key) if value else value
        elif key == 'organizationName':
            result[key] = scrub_value('pii', key) if value else value
        elif key in ('referral_code', 'code'):
            result[key] = scrub_value('code', key) if value else value
        elif key in ('referral_link',):
            result[key] = scrub_value('url', key) if value else value
        elif key in ('iterm2BackupPath',) or 'Path' in key:
            result[key] = scrub_path(value) if isinstance(value, str) else value
        elif key == 'approved' and isinstance(value, list):
            # API key hashes
            result[key] = [scrub_value('token', f'{key}[{i}]') for i in range(len(value))]
        elif key == 'projects' and isinstance(value, dict):
            # Scrub project paths
            result[key] = {scrub_path(k): scrub_dict(v) for k, v in value.items()}
        elif key == 'githubRepoPaths' and isinstance(value, dict):
            # Scrub repo paths but keep structure
            result[key] = {k: [scrub_path(p) for p in v] for k, v in value.items()}
        elif key == 'exampleFiles' and isinstance(value, list):
            # Keep example filenames, they're not sensitive
            result[key] = value
        elif key in ('s1mAccessCache', 's1mNonSubscriberAccessCache',
                     'groveConfigCache', 'passesEligibilityCache'):
            # Replace cache keys (UUIDs) with searchable placeholders
            if isinstance(value, dict):
                scrubbed_cache = {}
                for i, (cache_key, cache_val) in enumerate(value.items()):
                    new_key = scrub_value('uuid', f'{key}_key_{i}')
                    scrubbed_cache[new_key] = scrub_dict(cache_val) if isinstance(cache_val, dict) else cache_val
                result[key] = scrubbed_cache
            else:
                result[key] = value
        elif key == 'hasShownOpus45Notice' and isinstance(value, dict):
            # Replace UUIDs in dict keys
            result[key] = {scrub_value('uuid', f'{key}_key_{i}'): v for i, (k, v) in enumerate(value.items())}
        elif isinstance(value, dict):
            result[key] = scrub_dict(value)
        elif isinstance(value, list):
            result[key] = [scrub_dict(item) if isinstance(item, dict) else item for item in value]
        else:
            result[key] = value

    return result


def main():
    """Main function."""
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    else:
        input_file = Path.home() / ".claude.json"

    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    else:
        output_file = Path(__file__).parent.parent / "config" / "claude.json"

    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    # Read original config
    with open(input_file, 'r') as f:
        config = json.load(f)

    # Scrub sensitive data
    scrubbed = scrub_dict(config)

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write scrubbed config
    with open(output_file, 'w') as f:
        json.dump(scrubbed, f, indent=2)

    print(f"Scrubbed config written to: {output_file}")
    print("\nScrubbed sensitive data using format: <SCRUBBED:type:key>")
    print("  - API tokens and keys      → <SCRUBBED:token:...>")
    print("  - User UUIDs               → <SCRUBBED:uuid:...>")
    print("  - Email addresses          → <SCRUBBED:email:...>")
    print("  - Personal info            → <SCRUBBED:pii:...>")
    print("  - Referral codes           → <SCRUBBED:code:...>")
    print("  - File paths               → /Users/<SCRUBBED:username>/...")
    print("\nSearch for scrubbed values: grep '<SCRUBBED:' config/claude.json")


if __name__ == "__main__":
    main()
