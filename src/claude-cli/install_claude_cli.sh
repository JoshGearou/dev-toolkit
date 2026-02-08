#!/bin/bash
set -u  # Required per repo guidelines

# Claude Code CLI Installation Script
# Installs Anthropic's Claude AI CLI tool via npm

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../../bash/common/repo_lib.sh"

# Initialize logging
log_file="${SCRIPT_DIR}/$(basename "$0" .sh).log"

check_api_key_setup() {
    log_message "Checking Anthropic API key configuration..."
    
    if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
        log_message "✓ ANTHROPIC_API_KEY environment variable is set"
        return 0
    fi
    
    log_message "Warning: ANTHROPIC_API_KEY environment variable not set"
    log_message "Claude Code CLI requires an Anthropic API key to function"
    log_message ""
    log_message "To set up your API key:"
    log_message "1. Get an API key from https://console.anthropic.com/"
    log_message "2. Add to your shell profile (~/.zshrc or ~/.bashrc):"
    log_message "   export ANTHROPIC_API_KEY='your-api-key-here'"
    log_message "3. Reload your shell: source ~/.zshrc"
    log_message ""
    log_message "Installation will continue, but authentication setup will be needed before use"
}

install_claude_cli() {
    log_message "Installing Claude Code CLI via npm..."
    
    # Check if already installed
    local current_version
    current_version=$(get_installed_version "claude --version")
    if [[ "$current_version" != "not installed" ]]; then
        log_message "Claude Code CLI already installed: $current_version"
        log_message "Run './update_claude_cli.sh' to upgrade to latest version"
        return 0
    fi
    
    # Install via npm
    run_command_with_retry "npm install -g @anthropic-ai/claude-code"
    
    # Verify installation
    local installed_version
    installed_version=$(get_installed_version "claude --version")
    if [[ "$installed_version" == "not installed" ]]; then
        log_message "Error: npm installation failed"
        log_message "Check that Node.js and npm are properly configured"
        return 1
    fi
    
    log_message "✓ Claude Code CLI installed successfully: $installed_version"
    return 0
}

show_next_steps() {
    log_message "Installation completed successfully!"
    log_message ""
    log_message "Next steps:"
    log_message ""
    
    if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
        log_message "1. Set up your Anthropic API key (REQUIRED):"
        log_message "   • Get API key: https://console.anthropic.com/"
        log_message "   • Add to ~/.zshrc: export ANTHROPIC_API_KEY='your-key'"
        log_message "   • Reload shell: source ~/.zshrc"
        log_message ""
        log_message "2. Test the installation (after API key setup):"
    else
        log_message "1. Test the installation:"
    fi
    
    log_message "   claude --help"
    log_message "   claude --version"
    log_message ""
    log_message "3. Start using Claude Code CLI:"
    log_message "   claude  # Interactive mode"
    log_message ""
    log_message "4. Get help and documentation:"
    log_message "   • CLI help: claude --help"
    log_message "   • Documentation: https://docs.anthropic.com/claude/docs/claude-code"
    log_message ""
    
    if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
        log_message "⚠️  Remember: Set ANTHROPIC_API_KEY before using Claude Code CLI"
    else
        log_message "✓ API key configured - Claude Code CLI is ready to use!"
    fi
}

main() {
    log_message "Starting Claude Code CLI installation..."
    
    # Check platform compatibility
    local platform
    platform=$(detect_platform)
    if [[ "$platform" == "unsupported" ]]; then
        log_message "Error: Unsupported platform $(uname -s)"
        log_message "This script supports macOS and Linux only"
        exit 1
    fi
    log_message "Platform detected: $platform"
    
    # Check Node.js and npm requirements (essential for Claude CLI)
    check_volta_and_node
    
    # Check API key setup (warning only, doesn't block installation)
    check_api_key_setup
    
    # Install Claude Code CLI
    if install_claude_cli; then
        show_next_steps
    else
        log_message "Error: Claude Code CLI installation failed"
        log_message ""
        log_message "Troubleshooting steps:"
        log_message "1. Verify Node.js version: node --version (should be 18+)"
        log_message "2. Check npm access: npm --version"
        log_message "3. Try manual installation: npm install -g @anthropic-ai/claude-code"
        log_message "4. Check network connectivity and npm registry access"
        exit 1
    fi
}

main "$@"