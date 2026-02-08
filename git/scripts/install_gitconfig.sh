#!/bin/bash
set -u

# Script to install git configuration with platform-specific editor settings
# Mac: Uses VS Code
# Linux: Uses nano (headless-friendly)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/../config/.gitconfig"
TARGET_FILE="${HOME}/.gitconfig"
BACKUP_FILE="${HOME}/.gitconfig.backup"

# Detect platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="mac"
    EDITOR_CMD="code --wait"
    MERGE_TOOL="vscode"
    DIFF_TOOL="vscode"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
    EDITOR_CMD="nano"
    MERGE_TOOL="vimdiff"
    DIFF_TOOL="vimdiff"
else
    echo "Warning: Unknown platform '$OSTYPE', defaulting to Linux settings"
    PLATFORM="linux"
    EDITOR_CMD="nano"
    MERGE_TOOL="vimdiff"
    DIFF_TOOL="vimdiff"
fi

echo "Detected platform: $PLATFORM"
echo "Will use editor: $EDITOR_CMD"

# Backup existing config if it exists
if [[ -f "$TARGET_FILE" ]]; then
    echo "Backing up existing config to $BACKUP_FILE"
    cp "$TARGET_FILE" "$BACKUP_FILE"
fi

# Copy config file
echo "Copying $CONFIG_FILE to $TARGET_FILE"
cp "$CONFIG_FILE" "$TARGET_FILE"

# Mutate for Linux
if [[ "$PLATFORM" == "linux" ]]; then
    echo "Adjusting editor and merge/diff tools for Linux..."

    # Replace editor
    sed -i "s|editor = code --wait|editor = $EDITOR_CMD|g" "$TARGET_FILE"

    # Replace merge tool
    sed -i "s|tool = vscode|tool = $MERGE_TOOL|g" "$TARGET_FILE"

    # Remove VS Code-specific mergetool section (exactly 3 lines)
    sed -i '/^\[mergetool "vscode"\]$/,+2d' "$TARGET_FILE"

    # Remove VS Code-specific difftool section (exactly 2 lines)
    sed -i '/^\[difftool "vscode"\]$/,+1d' "$TARGET_FILE"

    # Fix signing key path (macOS /Users -> Linux /home)
    echo "Adjusting SSH signing key path for Linux..."
    sed -i "s|/Users/|/home/|g" "$TARGET_FILE"
fi

echo ""
echo "Git config installed successfully!"
echo ""
echo "Verify settings:"
echo "  git config --global --get core.editor"
echo "  git config --global --get merge.tool"
echo ""
echo "View full config:"
echo "  git config --global --list"
