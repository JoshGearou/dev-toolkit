# Config Directory

This directory contains Claude Code configuration files for backup and deployment.

## Files

### `settings.json`
- **Source**: `~/.claude/settings.json`
- **Deployed**: ✅ YES - Copied to `~/.claude/settings.json` during deployment
- **Purpose**: Claude Code UI and feature settings
- **Safe to commit**: ✅ Yes - Contains no secrets

### `claude.json`
- **Source**: `~/.claude.json` (scrubbed via `scripts/scrub_claude_config.py`)
- **Deployed**: ❌ **NEVER** - This is a backup only
- **Purpose**: Scrubbed backup of main Claude config for version control
- **Safe to commit**: ✅ Yes - Secrets replaced with `<SCRUBBED:type:key>` format
- **⚠️ WARNING**: This file should NEVER overwrite `~/.claude.json` as it contains no real secrets

## Import Process

When you run `./deploy.sh --import`, the script:

1. Copies `~/.claude/settings.json` → `config/settings.json` (as-is)
2. Scrubs `~/.claude.json` → `config/claude.json` (secrets removed)

All sensitive data in `claude.json` is replaced with the format: `<SCRUBBED:type:key>`

Search for scrubbed values:
```bash
grep '<SCRUBBED:' config/claude.json
```

## Scrubbed Data Types

- `<SCRUBBED:token:*>` - API tokens and keys
- `<SCRUBBED:uuid:*>` - User and organization UUIDs
- `<SCRUBBED:email:*>` - Email addresses
- `<SCRUBBED:pii:*>` - Personal identifiable information
- `<SCRUBBED:code:*>` - Referral codes
- `<SCRUBBED:url:*>` - URLs with sensitive data
- `/Users/<SCRUBBED:username>/` - File paths with usernames

## Deploy Safety

The `deploy.sh` script explicitly:
- ✅ Deploys `config/settings.json` to `~/.claude/settings.json`
- ❌ **NEVER** deploys `config/claude.json` anywhere
- Shows `[SKIP]` message if `claude.json` exists during deployment

This ensures your real secrets in `~/.claude.json` are never overwritten.
