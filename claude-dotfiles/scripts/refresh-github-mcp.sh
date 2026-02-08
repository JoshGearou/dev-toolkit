#!/bin/bash
# Refresh GitHub MCP server authentication for Claude Code
#
# This script removes and re-adds the GitHub MCP server with a fresh token
# from the gh CLI. Run this when your GitHub token expires or rotates.
#
# Usage: ./refresh-github-mcp.sh [--scope local|project|user]
#
# Scopes:
#   local   - Current project only (default)
#   project - Shared via .mcp.json file
#   user    - Available across all projects

set -euo pipefail

SCRIPT_NAME=$(basename "$0")
SCOPE="local"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --scope|-s)
            SCOPE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $SCRIPT_NAME [--scope local|project|user]"
            echo ""
            echo "Refresh GitHub MCP server with a fresh token from gh CLI."
            echo ""
            echo "Options:"
            echo "  --scope, -s   MCP scope (local, project, user). Default: local"
            echo "  --help, -h    Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run '$SCRIPT_NAME --help' for usage"
            exit 1
            ;;
    esac
done

# Validate scope
if [[ ! "$SCOPE" =~ ^(local|project|user)$ ]]; then
    echo "Error: Invalid scope '$SCOPE'. Must be: local, project, or user"
    exit 1
fi

echo "Refreshing GitHub MCP server (scope: $SCOPE)..."

# Check prerequisites
if ! command -v gh &> /dev/null; then
    echo "Error: gh CLI not found. Install with: brew install gh"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "Error: docker not found. Install Docker Desktop."
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub. Run: gh auth login"
    exit 1
fi

if ! docker info &> /dev/null 2>&1; then
    echo "Error: Docker is not running. Start Docker Desktop."
    exit 1
fi

# Get fresh token
echo "Getting fresh GitHub token..."
GITHUB_TOKEN=$(gh auth token)
if [[ -z "$GITHUB_TOKEN" ]]; then
    echo "Error: Failed to get GitHub token"
    exit 1
fi
echo "Token retrieved: ${GITHUB_TOKEN:0:10}..."

# Remove existing config (ignore errors if not exists)
echo "Removing existing GitHub MCP server..."
claude mcp remove github -s "$SCOPE" 2>/dev/null || true

# Add with fresh token
echo "Adding GitHub MCP server with fresh token..."
claude mcp add github -s "$SCOPE" \
    -e GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_TOKEN" \
    -- docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server

# Verify
echo ""
echo "Verifying connection..."
claude mcp get github

echo ""
echo "GitHub MCP server refreshed successfully."
echo "Restart Claude Code to use the updated configuration."
