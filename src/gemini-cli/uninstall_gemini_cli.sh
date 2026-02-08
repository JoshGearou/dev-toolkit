#!/bin/bash
set -u  # Required per repo guidelines

# Google Gemini CLI Uninstall Script
# Manages Google Cloud SDK and Gemini CLI removal

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../../bash/common/repo_lib.sh"

# Initialize logging
log_file="${SCRIPT_DIR}/$(basename "$0" .sh).log"

# Command line options
SKIP_CONFIRMATION=false
PRESERVE_CONFIG=false
REMOVE_GCLOUD=false

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -y, --yes              Skip confirmation prompts"
    echo "  -p, --preserve-config  Preserve Google Cloud configuration files"
    echo "  -g, --remove-gcloud    Remove entire Google Cloud SDK (WARNING: affects all gcloud tools)"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                     Interactive removal (Gemini component only)"
    echo "  $0 -y                  Remove Gemini without confirmation"
    echo "  $0 -y -g               Remove entire Google Cloud SDK"
    echo "  $0 -p                  Remove Gemini but keep all config"
    echo ""
    echo "Note: By default, this only removes Gemini CLI components, not the entire Google Cloud SDK"
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
            -g|--remove-gcloud)
                REMOVE_GCLOUD=true
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

is_gcloud_installed() {
    command -v gcloud >/dev/null 2>&1
}

is_gemini_available() {
    if ! is_gcloud_installed; then
        return 1
    fi
    
    # Check if gcloud gemini command exists
    if gcloud gemini --help >/dev/null 2>&1; then
        return 0
    fi
    
    return 1
}

confirm_uninstall() {
    if [[ "$SKIP_CONFIRMATION" == "true" ]]; then
        return 0
    fi
    
    echo ""
    if [[ "$REMOVE_GCLOUD" == "true" ]]; then
        echo "⚠️  WARNING: This will remove the ENTIRE Google Cloud SDK!"
        echo "This affects ALL gcloud commands and tools, not just Gemini CLI."
        echo ""
        echo "Affected tools include:"
        echo "• gcloud CLI • kubectl • gsutil • bq • Cloud SQL Proxy"
        echo "• All other Google Cloud SDK components"
        echo ""
    else
        echo "This will attempt to remove Gemini CLI components from Google Cloud SDK."
        echo "The main Google Cloud SDK will be preserved."
    fi
    
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

remove_gemini_component() {
    log_message "Attempting to remove Gemini CLI component..."
    
    # Check if gemini exists as a separate component
    if gcloud components list --filter="id:gemini" --format="value(state)" 2>/dev/null | grep -q "Installed"; then
        log_message "Removing Gemini component..."
        run_command_with_retry "gcloud components remove gemini"
        log_message "✓ Gemini component removed"
        return 0
    else
        log_message "Info: Gemini CLI appears to be part of core gcloud SDK"
        log_message "Cannot remove Gemini without removing entire Google Cloud SDK"
        
        if [[ "$REMOVE_GCLOUD" != "true" ]]; then
            log_message "Use --remove-gcloud option to remove entire Google Cloud SDK"
            log_message "Or manually disable Gemini API access in Google Cloud Console"
            return 1
        fi
    fi
    
    return 0
}

remove_gcloud_sdk() {
    log_message "Removing Google Cloud SDK..."
    
    # Detect installation method and remove accordingly
    local gcloud_path
    gcloud_path=$(command -v gcloud)
    
    if [[ "$gcloud_path" == *"/snap/"* ]]; then
        log_message "Detected snap installation"
        run_command_with_retry "sudo snap remove google-cloud-sdk"
    elif [[ "$gcloud_path" == *"/usr/local/"* ]] || [[ "$gcloud_path" == *"/opt/"* ]]; then
        log_message "Detected system installation"
        log_message "Manual removal required - check your system's package manager"
        log_message "Common removal commands:"
        log_message "• Ubuntu/Debian: sudo apt remove google-cloud-sdk"
        log_message "• macOS Homebrew: brew uninstall google-cloud-sdk"
        log_message "• Manual: rm -rf /usr/local/google-cloud-sdk"
        return 1
    elif [[ "$gcloud_path" == *"/homebrew/"* ]] || [[ "$gcloud_path" == *"/brew/"* ]]; then
        log_message "Detected Homebrew installation"
        run_command_with_retry "brew uninstall google-cloud-sdk"
    else
        log_message "Detected user installation"
        local install_dir
        install_dir=$(dirname "$(dirname "$gcloud_path")")
        log_message "Removing installation directory: $install_dir"
        run_command_with_retry "rm -rf \"$install_dir\""
    fi
    
    log_message "✓ Google Cloud SDK removal completed"
    return 0
}

cleanup_config_files() {
    if [[ "$PRESERVE_CONFIG" == "true" ]]; then
        log_message "Preserving configuration files as requested"
        return 0
    fi
    
    log_message "Cleaning up Google Cloud configuration files..."
    
    local config_locations=(
        "$HOME/.config/gcloud"
        "$HOME/.gcloud"
        "$HOME/Library/Application Support/gcloud"  # macOS
    )
    
    local found_configs=false
    
    for config_dir in "${config_locations[@]}"; do
        if [[ -d "$config_dir" ]]; then
            log_message "Removing config directory: $config_dir"
            run_command_with_retry "rm -rf \"$config_dir\""
            found_configs=true
        fi
    done
    
    # Remove gcloud from shell profiles
    local shell_profiles=(
        "$HOME/.bashrc"
        "$HOME/.zshrc"
        "$HOME/.bash_profile"
        "$HOME/.profile"
    )
    
    for profile in "${shell_profiles[@]}"; do
        if [[ -f "$profile" ]] && grep -q "gcloud\|google-cloud-sdk" "$profile" 2>/dev/null; then
            log_message "Found gcloud references in $profile"
            log_message "Manual cleanup recommended for shell profile: $profile"
        fi
    done
    
    if [[ "$found_configs" == "true" ]]; then
        log_message "✓ Configuration files cleaned up"
    else
        log_message "No configuration files found to remove"
    fi
}

show_cleanup_summary() {
    log_message ""
    log_message "Uninstall completed!"
    log_message ""
    log_message "Summary:"
    
    if [[ "$REMOVE_GCLOUD" == "true" ]]; then
        log_message "• Google Cloud SDK has been removed from your system"
        log_message "• All gcloud commands are no longer available"
    else
        log_message "• Gemini CLI components have been addressed"
        log_message "• Google Cloud SDK core functionality preserved"
    fi
    
    if [[ "$PRESERVE_CONFIG" == "true" ]]; then
        log_message "• Configuration files were preserved"
    else
        log_message "• Configuration files were cleaned up"
    fi
    
    log_message ""
    
    if [[ "$REMOVE_GCLOUD" == "true" ]]; then
        log_message "If you want to reinstall Google Cloud SDK later:"
        log_message "  Visit: https://cloud.google.com/sdk/docs/install"
        log_message ""
        log_message "To verify complete removal:"
        log_message "  gcloud --version  # Should show 'command not found'"
    else
        log_message "To verify Gemini CLI removal:"
        log_message "  gcloud gemini --help  # May show 'command not found' or help"
        log_message "  gcloud components list | grep gemini"
        log_message ""
        log_message "If you want to reinstall Gemini CLI later:"
        log_message "  ./install_gemini_cli.sh"
    fi
    
    log_message ""
    log_message "Note: You may need to restart your terminal for PATH changes to take effect"
}

main() {
    parse_args "$@"
    
    log_message "Starting Google Gemini CLI uninstall..."
    
    # Check platform compatibility
    local platform
    platform=$(detect_platform)
    if [[ "$platform" == "unsupported" ]]; then
        log_message "Error: Unsupported platform $(uname -s)"
        log_message "This script supports macOS and Linux only"
        exit 1
    fi
    log_message "Platform detected: $platform"
    
    # Check if Google Cloud SDK is installed
    if ! is_gcloud_installed; then
        log_message "Google Cloud SDK is not installed"
        log_message "Nothing to uninstall"
        exit 0
    fi
    
    log_message "Google Cloud SDK installation detected"
    
    # Show what will be removed
    if [[ "$REMOVE_GCLOUD" == "true" ]]; then
        log_message "Mode: Full Google Cloud SDK removal"
    else
        log_message "Mode: Gemini CLI component removal only"
        
        if ! is_gemini_available; then
            log_message "Gemini CLI does not appear to be available"
            log_message "This may be normal - proceeding with cleanup anyway"
        fi
    fi
    
    # Confirm uninstall
    confirm_uninstall
    
    # Perform removal
    if [[ "$REMOVE_GCLOUD" == "true" ]]; then
        if ! remove_gcloud_sdk; then
            log_message "Error: Failed to remove Google Cloud SDK"
            log_message "Manual removal may be required"
            exit 1
        fi
    else
        if ! remove_gemini_component; then
            log_message "Warning: Could not remove Gemini CLI component"
            log_message "This may be expected if Gemini is part of core gcloud"
        fi
    fi
    
    # Clean up configuration files
    cleanup_config_files
    
    # Show summary
    show_cleanup_summary
}

main "$@"