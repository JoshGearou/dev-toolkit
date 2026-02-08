#!/bin/bash
set -u  # Required per repo guidelines

# GitHub Copilot CLI Uninstall Script
# Safely removes GitHub Copilot CLI and optionally cleans up configuration

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
    echo "  -p, --preserve-config  Preserve GitHub Copilot configuration files"
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

confirm_uninstall() {
    if [[ "$SKIP_CONFIRMATION" == "true" ]]; then
        return 0
    fi
    
    echo ""
    echo "This will remove GitHub Copilot CLI from your system."
    if [[ "$PRESERVE_CONFIG" == "false" ]]; then
        echo "Configuration files will also be removed."
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

uninstall_via_gh_extension() {
    log_message "Removing GitHub Copilot CLI via GitHub CLI extension..."
    
    # Remove the extension
    run_command_with_retry "gh extension remove gh-copilot"
    
    # Verify removal
    if gh extension list 2>/dev/null | grep -q "github/gh-copilot"; then
        log_message "Error: Failed to remove GitHub CLI extension"
        return 1
    fi
    
    log_message "✓ GitHub Copilot CLI extension removed successfully"
    return 0
}

uninstall_via_npm() {
    log_message "Removing GitHub Copilot CLI via npm..."
    
    # Check Node.js and npm requirements for uninstall
    if ! command -v npm >/dev/null 2>&1; then
        log_message "Warning: npm not found, cannot remove npm package"
        log_message "You may need to remove @github/copilot manually"
        return 1
    fi
    
    # Remove the package
    run_command_with_retry "npm uninstall -g @github/copilot"
    
    # Verify removal
    if npm list -g @github/copilot >/dev/null 2>&1; then
        log_message "Error: Failed to remove npm package"
        return 1
    fi
    
    log_message "✓ GitHub Copilot CLI npm package removed successfully"
    return 0
}

cleanup_config_files() {
    if [[ "$PRESERVE_CONFIG" == "true" ]]; then
        log_message "Preserving configuration files as requested"
        return 0
    fi
    
    log_message "Cleaning up GitHub Copilot configuration files..."
    
    local config_locations=(
        "$HOME/.config/github-copilot"
        "$HOME/.github-copilot"
        "$HOME/Library/Application Support/github-copilot"  # macOS
    )
    
    local found_configs=false
    
    for config_dir in "${config_locations[@]}"; do
        if [[ -d "$config_dir" ]]; then
            log_message "Removing config directory: $config_dir"
            run_command_with_retry "rm -rf \"$config_dir\""
            found_configs=true
        fi
    done
    
    # Check for copilot-related files in .gitconfig
    if [[ -f "$HOME/.gitconfig" ]] && grep -q "copilot" "$HOME/.gitconfig" 2>/dev/null; then
        log_message "Warning: Found copilot-related entries in ~/.gitconfig"
        log_message "You may want to review and remove them manually"
    fi
    
    if [[ "$found_configs" == "true" ]]; then
        log_message "✓ Configuration files cleaned up"
    else
        log_message "No configuration files found to remove"
    fi
}

show_cleanup_summary() {
    log_message ""
    log_message "Uninstall completed successfully!"
    log_message ""
    log_message "Summary:"
    log_message "• GitHub Copilot CLI has been removed from your system"
    
    if [[ "$PRESERVE_CONFIG" == "true" ]]; then
        log_message "• Configuration files were preserved"
    else
        log_message "• Configuration files were cleaned up"
    fi
    
    log_message ""
    log_message "If you want to reinstall GitHub Copilot CLI later:"
    log_message "  ./install_copilot_cli.sh"
    log_message ""
    log_message "To verify removal:"
    log_message "  gh copilot --version  # Should show 'command not found'"
}

main() {
    parse_args "$@"
    
    log_message "Starting GitHub Copilot CLI uninstall..."
    
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
        "not_installed")
            log_message "GitHub Copilot CLI is not installed"
            log_message "Nothing to uninstall"
            exit 0
            ;;
        "gh_extension")
            log_message "Found GitHub Copilot CLI installed via GitHub CLI extension"
            ;;
        "npm")
            log_message "Found GitHub Copilot CLI installed via npm"
            ;;
        *)
            log_message "Error: Unknown installation method"
            exit 1
            ;;
    esac
    
    # Confirm uninstall
    confirm_uninstall
    
    # Perform uninstall based on method
    case "$install_method" in
        "gh_extension")
            if ! uninstall_via_gh_extension; then
                exit 1
            fi
            ;;
        "npm")
            if ! uninstall_via_npm; then
                exit 1
            fi
            ;;
    esac
    
    # Clean up configuration files
    cleanup_config_files
    
    # Show summary
    show_cleanup_summary
}

main "$@"