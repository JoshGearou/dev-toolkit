#!/bin/bash
set -u

# deny_file.sh - Add files to Claude Code's deny list
#
# Adds Read() deny rules to .claude/settings.local.json to prevent
# Claude Code from accessing specified files.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GIT_ROOT="$(cd "$SCRIPT_DIR" && git rev-parse --show-toplevel 2>/dev/null)"
SETTINGS_FILE="$GIT_ROOT/.claude/settings.local.json"
BACKUP_DIR="$GIT_ROOT/claude"

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS] <file_path> [file_path...]

Add files to Claude Code's deny list in .claude/settings.local.json

Arguments:
    file_path       Path to file(s) to deny (absolute or relative)

Options:
    -h, --help      Show this help message
    -l, --list      List currently denied files
    -r, --remove    Remove file(s) from deny list instead of adding

Path Handling:
    - Absolute paths are converted to repo-relative paths automatically
    - Relative paths are used as-is (prefixed with ./ if needed)

Wildcard Support:
    Glob-style wildcards are supported in paths:

    *           Match any characters in a filename
    **          Match directories recursively

Examples:
    # Deny a specific file
    $(basename "$0") repositories/designs/secret.md

    # Deny using absolute path (auto-converted to relative)
    $(basename "$0") /Users/you/repo/secrets/api_keys.json

    # Deny all files in a directory recursively
    $(basename "$0") "./secrets/**"

    # Deny all .env files
    $(basename "$0") "./.env.*"

    # Deny all JSON files in config directory
    $(basename "$0") "./config/*.json"

    # List currently denied files
    $(basename "$0") --list

    # Remove a file from deny list
    $(basename "$0") --remove ./secrets/old_file.md

EOF
    exit 0
}

list_denied() {
    if [[ ! -f "$SETTINGS_FILE" ]]; then
        echo "No settings file found at: $SETTINGS_FILE"
        exit 1
    fi

    echo "Currently denied files:"
    jq -r '.permissions.deny[]' "$SETTINGS_FILE" 2>/dev/null | while read -r rule; do
        echo "  $rule"
    done
}

# Backup settings file before modification
backup_settings() {
    mkdir -p "$BACKUP_DIR"
    local backup_file="$BACKUP_DIR/settings.local.json"
    cp "$SETTINGS_FILE" "$backup_file"
}

# Convert absolute path to repo-relative path
to_relative_path() {
    local path="$1"

    # If it's an absolute path starting with the git root, make it relative
    if [[ "$path" == "$GIT_ROOT"/* ]]; then
        path=".${path#$GIT_ROOT}"
    fi

    # Ensure path starts with ./
    if [[ "$path" != ./* ]]; then
        path="./$path"
    fi

    echo "$path"
}

add_deny_rule() {
    local path="$1"
    local relative_path
    relative_path=$(to_relative_path "$path")
    local rule="Read($relative_path)"

    # Check if rule already exists
    if jq -e ".permissions.deny | index(\"$rule\")" "$SETTINGS_FILE" >/dev/null 2>&1; then
        echo "Already denied: $rule"
        return 0
    fi

    # Add the rule
    local tmp_file
    tmp_file=$(mktemp)
    jq ".permissions.deny += [\"$rule\"]" "$SETTINGS_FILE" > "$tmp_file" && mv "$tmp_file" "$SETTINGS_FILE"
    echo "Added: $rule"
}

remove_deny_rule() {
    local path="$1"
    local relative_path
    relative_path=$(to_relative_path "$path")
    local rule="Read($relative_path)"

    # Check if rule exists
    if ! jq -e ".permissions.deny | index(\"$rule\")" "$SETTINGS_FILE" >/dev/null 2>&1; then
        echo "Not found in deny list: $rule"
        return 1
    fi

    # Remove the rule
    local tmp_file
    tmp_file=$(mktemp)
    jq ".permissions.deny -= [\"$rule\"]" "$SETTINGS_FILE" > "$tmp_file" && mv "$tmp_file" "$SETTINGS_FILE"
    echo "Removed: $rule"
}

# Parse arguments
REMOVE_MODE=false
FILES=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            ;;
        -l|--list)
            list_denied
            exit 0
            ;;
        -r|--remove)
            REMOVE_MODE=true
            shift
            ;;
        -*)
            echo "Unknown option: $1" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
        *)
            FILES+=("$1")
            shift
            ;;
    esac
done

# Validate
if [[ ${#FILES[@]} -eq 0 ]]; then
    echo "Error: No files specified" >&2
    echo "Use --help for usage information" >&2
    exit 1
fi

if [[ ! -f "$SETTINGS_FILE" ]]; then
    echo "Error: Settings file not found: $SETTINGS_FILE" >&2
    echo "Create it first or run Claude Code to generate it." >&2
    exit 1
fi

# Check for jq
if ! command -v jq &>/dev/null; then
    echo "Error: jq is required but not installed" >&2
    echo "Install with: brew install jq" >&2
    exit 1
fi

# Process files
for file in "${FILES[@]}"; do
    if [[ "$REMOVE_MODE" == true ]]; then
        remove_deny_rule "$file"
    else
        add_deny_rule "$file"
    fi
done

# Copy to git-tracked location after changes
backup_settings
