#!/bin/bash
set -u  # Required per repo guidelines

# Claude Code CLI Uninstall Script
# Safely removes Anthropic's Claude AI CLI tool

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../../bash/common/repo_lib.sh"

# Initialize logging
log_file="${SCRIPT_DIR}/$(basename "$0" .sh).log"

# Command line options
SKIP_CONFIRMATION=false
PRESERVE_CONFIG=false

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -y, --yes              Skip confirmation prompts"
    echo "  -p, --preserve-config  Preserve Claude Code CLI configuration files"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                     Interactive uninstall with prompts"
    echo "  $0 -y                  Uninstall without confirmation"
    echo "  $0 -y -p               Uninstall without confirmation, keep config"
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -y|--yes)
                SKIP_CONFIRMATION=true
                shift
                ;;
            -p|--preserve-config)
                PRESERVE_CONFIG=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log_message "Error: Unknown option $1"
                usage
                exit 1
                ;;
        esac
    done
}

is_claude_installed() {
    # Check if Claude Code CLI is installed via npm
    if command -v npm >/dev/null 2>&1 && npm list -g @anthropic-ai/claude-code >/dev/null 2>&1; then
        return 0
    fi
    
    # Also check if command is available (in case installed differently)
    if command -v claude >/dev/null 2>&1; then
        return 0
    fi
    
    return 1
}

confirm_uninstall() {
    if [[ "$SKIP_CONFIRMATION" == "true" ]]; then
        return 0
    fi
    
    echo ""
    echo "This will remove Claude Code CLI from your system."
    if [[ "$PRESERVE_CONFIG" == "false" ]]; then
        echo "Configuration files will also be removed."
        echo "Note: ANTHROPIC_API_KEY environment variable will NOT be removed."
    else
        echo "Configuration files will be preserved."
    fi
    echo ""
    read -p "Are you sure you want to continue? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_message "Uninstall cancelled by user"
        exit 0
    fi
}

uninstall_claude_cli() {
    log_message "Removing Claude Code CLI via npm..."
    
    # Check if npm is available
    if ! command -v npm >/dev/null 2>&1; then
        log_message "Warning: npm not found, cannot remove npm package"
        log_message "You may need to remove @anthropic-ai/claude-code manually"
        return 1
    fi
    
    # Remove the package
    run_command_with_retry "npm uninstall -g @anthropic-ai/claude-code"
    
    # Verify removal
    if npm list -g @anthropic-ai/claude-code >/dev/null 2>&1; then
        log_message "Error: Failed to remove npm package"
        return 1
    fi
    
    log_message "✓ Claude Code CLI npm package removed successfully"
    
    # Check if command is still available (shouldn't be)
    if command -v claude >/dev/null 2>&1; then
        log_message "Warning: claude command still available"
        log_message "May have been installed via a different method"
        log_message "Path: $(command -v claude)"
    fi
    
    return 0
}

cleanup_config_files() {
    if [[ "$PRESERVE_CONFIG" == "true" ]]; then
        log_message "Preserving configuration files as requested"
        return 0
    fi
    
    log_message "Cleaning up Claude Code CLI configuration files..."
    
    local config_locations=(
        "$HOME/.config/claude-code"
        "$HOME/.claude-code"
        "$HOME/Library/Application Support/claude-code"  # macOS
        "$HOME/.anthropic"
        "$HOME/.config/anthropic"
    )
    
    local found_configs=false
    
    for config_dir in "${config_locations[@]}"; do
        if [[ -d "$config_dir" ]]; then
            log_message "Removing config directory: $config_dir"
            run_command_with_retry "rm -rf \"$config_dir\""
            found_configs=true
        fi
    done
    
    # Check for claude-related cache files
    local cache_locations=(
        "$HOME/.cache/claude-code"
        "$HOME/Library/Caches/claude-code"  # macOS
    )
    
    for cache_dir in "${cache_locations[@]}"; do
        if [[ -d "$cache_dir" ]]; then
            log_message "Removing cache directory: $cache_dir"
            run_command_with_retry "rm -rf \"$cache_dir\""
            found_configs=true
        fi
    done
    
    if [[ "$found_configs" == "true" ]]; then
        log_message "✓ Configuration files cleaned up"
    else
        log_message "No configuration files found to remove"
    fi
    
    # Note about API key
    log_message ""
    log_message "Note: ANTHROPIC_API_KEY environment variable not removed"
    log_message "Remove manually from ~/.zshrc or ~/.bashrc if desired"
}

show_cleanup_summary() {
    log_message ""
    log_message "Uninstall completed successfully!"
    log_message ""
    log_message "Summary:"
    log_message "• Claude Code CLI has been removed from your system"
    
    if [[ "$PRESERVE_CONFIG" == "true" ]]; then
        log_message "• Configuration files were preserved"
    else
        log_message "• Configuration files were cleaned up"
    fi
    
    log_message "• ANTHROPIC_API_KEY environment variable was preserved"
    log_message ""
    log_message "If you want to reinstall Claude Code CLI later:"
    log_message "  ./install_claude_cli.sh"
    log_message ""
    log_message "To verify removal:"
    log_message "  claude --version  # Should show 'command not found'"
    log_message "  npm list -g @anthropic-ai/claude-code  # Should show 'empty'"
    log_message ""
    log_message "To completely remove API key (optional):"
    log_message "  # Edit ~/.zshrc or ~/.bashrc and remove:"
    log_message "  # export ANTHROPIC_API_KEY='...'"
}

main() {
    parse_args "$@"
    
    log_message "Starting Claude Code CLI uninstall..."
    
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
        log_message "Claude Code CLI is not installed"
        log_message "Nothing to uninstall"
        exit 0
    fi
    
    log_message "Claude Code CLI installation detected"
    
    # Confirm uninstall
    confirm_uninstall
    
    # Perform uninstall
    if ! uninstall_claude_cli; then
        log_message "Error: Failed to uninstall Claude Code CLI"
        log_message "You may need to remove it manually:"
        log_message "  npm uninstall -g @anthropic-ai/claude-code"
        exit 1
    fi
    
    # Clean up configuration files
    cleanup_config_files
    
    # Show summary
    show_cleanup_summary
}

main "$@"