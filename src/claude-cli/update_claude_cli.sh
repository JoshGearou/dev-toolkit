#!/bin/bash
set -u  # Required per repo guidelines

# Claude Code CLI Update Script
# Updates Anthropic's Claude AI CLI tool via npm

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../../bash/common/repo_lib.sh"

# Initialize logging
log_file="${SCRIPT_DIR}/$(basename "$0" .sh).log"

is_claude_installed() {
    # Check if Claude CLI is installed
    if command -v claude >/dev/null 2>&1; then
        return 0
    fi
    
    # Also check npm global packages
    if command -v npm >/dev/null 2>&1 && npm list -g @anthropic-ai/claude-code >/dev/null 2>&1; then
        return 0
    fi
    
    return 1
}

get_current_version() {
    local version
    
    # Try to get version from claude command
    if command -v claude >/dev/null 2>&1; then
        version=$(claude --version 2>/dev/null || echo "unknown")
    else
        # Fallback to npm package version
        version=$(npm list -g @anthropic-ai/claude-code --depth=0 2>/dev/null | grep "@anthropic-ai/claude-code" | sed 's/.*@anthropic-ai\/claude-code@//' | sed 's/ .*//')
        if [[ -z "$version" ]]; then
            version="unknown"
        fi
    fi
    
    echo "$version"
}

check_api_key() {
    if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
        log_message "Warning: ANTHROPIC_API_KEY environment variable not set"
        log_message "Make sure to configure your API key before using Claude Code CLI"
        log_message "Visit: https://console.anthropic.com/"
        return 1
    fi
    
    log_message "✓ ANTHROPIC_API_KEY environment variable is configured"
    return 0
}

update_claude_cli() {
    log_message "Updating Claude Code CLI via npm..."
    
    # Check Node.js and npm requirements
    check_volta_and_node
    
    local current_version
    current_version=$(get_current_version)
    log_message "Current version: $current_version"
    
    # Update the package
    run_command_with_retry "npm update -g @anthropic-ai/claude-code"
    
    # Get new version
    local new_version
    new_version=$(get_current_version)
    
    if [[ "$current_version" == "$new_version" ]]; then
        log_message "✓ Claude Code CLI is already up to date: $current_version"
    else
        log_message "✓ Claude Code CLI updated from $current_version to $new_version"
    fi
    
    return 0
}

show_whats_new() {
    log_message ""
    log_message "What's new in Claude Code CLI:"
    log_message "• Visit https://docs.anthropic.com/claude/docs/claude-code for latest features"
    log_message "• Check release notes: https://www.npmjs.com/package/@anthropic-ai/claude-code"
    log_message ""
    log_message "Test the updated installation:"
    log_message "  claude --version"
    log_message "  claude --help"
    log_message ""
    
    # Check API key and provide reminder if needed
    if ! check_api_key; then
        log_message "Remember to set up your API key before testing:"
        log_message "  export ANTHROPIC_API_KEY='your-api-key'"
        log_message "  source ~/.zshrc"
    else
        log_message "Ready to test Claude Code CLI:"
        log_message "  claude  # Start interactive session"
    fi
}

main() {
    log_message "Starting Claude Code CLI update..."
    
    # Check platform compatibility
    local platform
    platform=$(detect_platform)
    if [[ "$platform" == "unsupported" ]]; then
        log_message "Error: Unsupported platform $(uname -s)"
        log_message "This script supports macOS and Linux only"
        exit 1
    fi
    log_message "Platform detected: $platform"
    
    # Check if Claude CLI is installed
    if ! is_claude_installed; then
        log_message "Error: Claude Code CLI is not installed"
        log_message "Run './install_claude_cli.sh' to install it first"
        exit 1
    fi
    
    log_message "Claude Code CLI installation detected"
    
    # Perform update
    if update_claude_cli; then
        show_whats_new
        log_message "Update completed successfully!"
    else
        log_message "Error: Update failed"
        log_message ""
        log_message "Troubleshooting steps:"
        log_message "1. Check network connectivity"
        log_message "2. Verify npm registry access: npm ping"
        log_message "3. Try manual update: npm update -g @anthropic-ai/claude-code"
        log_message "4. Check Node.js version: node --version (should be 18+)"
        exit 1
    fi
}

main "$@"