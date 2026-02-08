#!/bin/bash
set -u

SELF_SCRIPT=$(realpath "$0")
SOURCE_SCRIPT=~/src/sandbox/dev-rerickso/git/scripts/run_update_repos.sh
TARGET_SCRIPT=~/src/sandbox/dev-rerickso/git/scripts/update_repos.sh

if [ "${RUN_UPDATE_REPOS_UPDATED:-false}" != "true" ]; then
    export RUN_UPDATE_REPOS_UPDATED=true
    if [ "$SELF_SCRIPT" != "$SOURCE_SCRIPT" ]; then
        if [ -f "$SOURCE_SCRIPT" ]; then
            echo "Updating $SELF_SCRIPT from $SOURCE_SCRIPT..."
            cp "$SOURCE_SCRIPT" "$SELF_SCRIPT"
            echo "Update complete. Restarting script..."
            exec bash "$SELF_SCRIPT" "$@"
        else
            echo "Error: Source script not found at $SOURCE_SCRIPT"
            exit 1
        fi
    fi
fi

if [ ! -f "$TARGET_SCRIPT" ]; then
    echo "Error: Target script not found at $TARGET_SCRIPT"
    exit 1
fi

TARGET_DIR=$(dirname "$TARGET_SCRIPT")
cd "$TARGET_DIR"

bash "$(basename "$TARGET_SCRIPT")"
