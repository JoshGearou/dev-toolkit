#!/bin/bash
set -u  # Required per repo guidelines

# Google Gemini CLI Update Script
# Updates Google Cloud SDK components including Gemini CLI

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../../bash/common/repo_lib.sh"

# Initialize logging
log_file="${SCRIPT_DIR}/$(basename "$0" .sh).log"

is_gemini_available() {
    # Check if gcloud gemini command exists
    if gcloud gemini --help >/dev/null 2>&1; then
        return 0
    fi
    
    return 1
}

get_gcloud_version() {
    local version
    version=$(gcloud version --format="value(Google Cloud SDK)" 2>/dev/null || echo "unknown")
    echo "$version"
}

check_gcp_authentication() {
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" >/dev/null 2>&1; then
        log_message "Warning: No active Google Cloud authentication"
        log_message "Authenticate with: gcloud auth login"
        return 1
    fi
    
    local active_account
    active_account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1)
    log_message "✓ Authenticated as: $active_account"
    return 0
}

update_gcloud_components() {
    log_message "Updating Google Cloud SDK components..."
    
    local current_version
    current_version=$(get_gcloud_version)
    log_message "Current Google Cloud SDK version: $current_version"
    
    # Update all components
    run_command_with_retry "gcloud components update"
    
    # Get new version
    local new_version
    new_version=$(get_gcloud_version)
    
    if [[ "$current_version" == "$new_version" ]]; then
        log_message "✓ Google Cloud SDK is already up to date: $current_version"
    else
        log_message "✓ Google Cloud SDK updated from $current_version to $new_version"
    fi
    
    return 0
}

show_whats_new() {
    log_message ""
    log_message "Google Cloud SDK update completed!"
    log_message ""
    log_message "What's new:"
    log_message "• Check release notes: gcloud info --show-log"
    log_message "• View all components: gcloud components list"
    log_message "• Documentation: https://cloud.google.com/sdk/docs/release-notes"
    log_message ""
    log_message "Test Gemini CLI functionality:"
    log_message "  gcloud gemini --help"
    log_message "  gcloud version"
    log_message ""
    
    # Check authentication status
    if ! check_gcp_authentication; then
        log_message "Remember to authenticate if needed:"
        log_message "  gcloud auth login"
        log_message "  gcloud config set project YOUR_PROJECT_ID"
    fi
    
    # Check if gemini is available after update
    if is_gemini_available; then
        log_message "✓ Gemini CLI is available and ready to use"
    else
        log_message "Note: Gemini CLI may not be available in your current configuration"
        log_message "Check: gcloud components list | grep gemini"
    fi
}

main() {
    log_message "Starting Google Cloud SDK / Gemini CLI update..."
    
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
    check_dependency "gcloud" "Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    
    # Check if Gemini CLI was previously available
    if ! is_gemini_available; then
        log_message "Warning: Gemini CLI not currently available"
        log_message "This may be normal if Gemini CLI is not yet available in your region/project"
        log_message "Continuing with Google Cloud SDK update..."
    else
        log_message "Gemini CLI detected, proceeding with update"
    fi
    
    # Check authentication (warning only)
    check_gcp_authentication
    
    # Perform update
    if update_gcloud_components; then
        show_whats_new
        log_message "Update completed successfully!"
    else
        log_message "Error: Update failed"
        log_message ""
        log_message "Troubleshooting steps:"
        log_message "1. Check internet connectivity"
        log_message "2. Verify authentication: gcloud auth list"
        log_message "3. Try manual update: gcloud components update"
        log_message "4. Check disk space and permissions"
        log_message "5. Visit: https://cloud.google.com/sdk/docs/troubleshooting"
        exit 1
    fi
}

main "$@"