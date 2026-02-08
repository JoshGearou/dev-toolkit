#!/bin/bash
set -u  # Required per repo guidelines

# GitHub Copilot CLI Update Script
# Detects installation method and updates accordingly

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../../bash/common/repo_lib.sh"

# Initialize logging
log_file="${SCRIPT_DIR}/$(basename "$0" .sh).log"

detect_installation_method() {
    # Check if installed via GitHub CLI extension
    if command -v gh >/dev/null 2>&1 && gh extension list 2>/dev/null | grep -q "github/gh-copilot"; then
        echo "gh_extension"
        return 0
    fi
    
    # Check if installed via npm
    if command -v npm >/dev/null 2>&1 && npm list -g @github/copilot >/dev/null 2>&1; then
        echo "npm"
        return 0
    fi
    
    # Not installed
    echo "not_installed"
    return 1
}

get_current_version() {
    local method="$1"
    local version
    
    case "$method" in
        "gh_extension")
            version=$(get_installed_version "gh copilot --version")
            ;;
        "npm")
            version=$(npm list -g @github/copilot --depth=0 2>/dev/null | grep "@github/copilot" | sed 's/.*@github\/copilot@//' | sed 's/ .*//')
            if [[ -z "$version" ]]; then
                version="unknown"
            fi
            ;;
        *)
            version="not installed"
            ;;
    esac
    
    echo "$version"
}

update_via_gh_extension() {
    log_message "Updating GitHub Copilot CLI via GitHub CLI extension..."
    
    local current_version
    current_version=$(get_current_version "gh_extension")
    log_message "Current version: $current_version"
    
    # Update the extension
    run_command_with_retry "gh extension upgrade gh-copilot"
    
    # Get new version
    local new_version
    new_version=$(get_current_version "gh_extension")
    
    if [[ "$current_version" == "$new_version" ]]; then
        log_message "✓ GitHub Copilot CLI is already up to date: $current_version"
    else
        log_message "✓ GitHub Copilot CLI updated from $current_version to $new_version"
    fi
}

update_via_npm() {
    log_message "Updating GitHub Copilot CLI via npm..."
    
    # Check Node.js and npm requirements
    check_volta_and_node
    
    local current_version
    current_version=$(get_current_version "npm")
    log_message "Current version: $current_version"
    
    # Update the package
    run_command_with_retry "npm update -g @github/copilot"
    
    # Get new version
    local new_version
    new_version=$(get_current_version "npm")
    
    if [[ "$current_version" == "$new_version" ]]; then
        log_message "✓ GitHub Copilot CLI is already up to date: $current_version"
    else
        log_message "✓ GitHub Copilot CLI updated from $current_version to $new_version"
    fi
}

show_whats_new() {
    log_message ""
    log_message "What's new in GitHub Copilot CLI:"
    log_message "• Visit https://github.com/github/gh-copilot/releases for changelog"
    log_message "• Try new features with 'gh copilot --help'"
    log_message ""
    log_message "Test the updated installation:"
    log_message "  gh copilot suggest \"create a hello world script\""
    log_message "  gh copilot explain \"git rebase -i HEAD~3\""
}

main() {
    log_message "Starting GitHub Copilot CLI update..."
    
    # Check platform compatibility
    local platform
    platform=$(detect_platform)
    if [[ "$platform" == "unsupported" ]]; then
        log_message "Error: Unsupported platform $(uname -s)"
        log_message "This script supports macOS and Linux only"
        exit 1
    fi
    log_message "Platform detected: $platform"
    
    # Detect installation method
    log_message "Detecting GitHub Copilot CLI installation method..."
    local install_method
    install_method=$(detect_installation_method)
    
    case "$install_method" in
        "gh_extension")
            log_message "Found GitHub Copilot CLI installed via GitHub CLI extension"
            update_via_gh_extension
            ;;
        "npm")
            log_message "Found GitHub Copilot CLI installed via npm"
            update_via_npm
            ;;
        "not_installed")
            log_message "Error: GitHub Copilot CLI is not installed"
            log_message "Run './install_copilot_cli.sh' to install it first"
            exit 1
            ;;
        *)
            log_message "Error: Unknown installation method"
            exit 1
            ;;
    esac
    
    show_whats_new
    log_message "Update completed successfully!"
}

main "$@"