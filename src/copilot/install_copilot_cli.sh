#!/bin/bash
set -u  # Required per repo guidelines

# GitHub Copilot CLI Installation Script
# Supports both GitHub CLI extension and npm installation methods

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../../bash/common/repo_lib.sh"

# Initialize logging
log_file="${SCRIPT_DIR}/$(basename "$0" .sh).log"

install_via_gh_extension() {
    log_message "Installing GitHub Copilot CLI via GitHub CLI extension..."
    
    # Check if GitHub CLI is available
    check_dependency "gh" "Install GitHub CLI: brew install gh or visit https://cli.github.com/"
    
    # Check if already installed
    if gh extension list | grep -q "github/gh-copilot"; then
        local current_version
        current_version=$(get_installed_version "gh copilot --version")
        log_message "GitHub Copilot CLI already installed via gh extension: $current_version"
        return 0
    fi
    
    # Install via GitHub CLI extension
    run_command_with_retry "gh extension install github/gh-copilot"
    
    # Verify installation
    local installed_version
    installed_version=$(get_installed_version "gh copilot --version")
    if [[ "$installed_version" == "not installed" ]]; then
        log_message "Error: GitHub CLI extension installation failed"
        return 1
    fi
    
    log_message "✓ GitHub Copilot CLI installed via gh extension: $installed_version"
    return 0
}

install_via_npm() {
    log_message "Installing GitHub Copilot CLI via npm..."
    
    # Check Node.js and npm requirements
    check_volta_and_node
    
    # Check if already installed
    local current_version
    current_version=$(get_installed_version "gh copilot --version")
    if [[ "$current_version" != "not installed" ]]; then
        log_message "GitHub Copilot CLI already installed: $current_version"
        return 0
    fi
    
    # Install via npm
    run_command_with_retry "npm install -g @github/copilot"
    
    # Verify installation
    local installed_version
    installed_version=$(get_installed_version "gh copilot --version")
    if [[ "$installed_version" == "not installed" ]]; then
        log_message "Error: npm installation failed"
        return 1
    fi
    
    log_message "✓ GitHub Copilot CLI installed via npm: $installed_version"
    return 0
}

show_next_steps() {
    log_message "Installation completed successfully!"
    log_message ""
    log_message "Next steps:"
    log_message "1. Authenticate with GitHub:"
    log_message "   gh auth login  # if not already authenticated"
    log_message "   gh copilot auth  # authenticate Copilot specifically"
    log_message ""
    log_message "2. Test the installation:"
    log_message "   gh copilot suggest \"list files in current directory\""
    log_message "   gh copilot explain \"ls -la\""
    log_message ""
    log_message "3. Get help:"
    log_message "   gh copilot --help"
}

main() {
    log_message "Starting GitHub Copilot CLI installation..."
    
    # Check platform compatibility
    local platform
    platform=$(detect_platform)
    if [[ "$platform" == "unsupported" ]]; then
        log_message "Error: Unsupported platform $(uname -s)"
        log_message "This script supports macOS and Linux only"
        exit 1
    fi
    log_message "Platform detected: $platform"
    
    # Try GitHub CLI extension first (preferred method)
    if command -v gh >/dev/null 2>&1; then
        log_message "GitHub CLI detected, attempting installation via extension..."
        if install_via_gh_extension; then
            show_next_steps
            return 0
        fi
        log_message "GitHub CLI extension installation failed, trying npm method..."
    else
        log_message "GitHub CLI not found, using npm installation method..."
    fi
    
    # Fallback to npm installation
    if install_via_npm; then
        show_next_steps
        return 0
    fi
    
    log_message "Error: All installation methods failed"
    log_message "Please install GitHub CLI or Node.js/npm manually and try again"
    exit 1
}

main "$@"