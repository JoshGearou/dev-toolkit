#!/bin/bash
set -u  # Required per repo guidelines

# Google Gemini CLI Installation Script
# Installs Google's Gemini Code Assist CLI via gcloud components

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../../bash/common/repo_lib.sh"

# Initialize logging
log_file="${SCRIPT_DIR}/$(basename "$0" .sh).log"

check_gcp_setup() {
    log_message "Checking Google Cloud Platform setup..."
    
    # Check if user is authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" >/dev/null 2>&1; then
        log_message "Warning: No active Google Cloud authentication found"
        log_message "You'll need to authenticate before using Gemini CLI"
        log_message ""
        log_message "To authenticate:"
        log_message "  gcloud auth login"
        log_message "  gcloud config set project YOUR_PROJECT_ID"
        return 1
    fi
    
    local active_account
    active_account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1)
    log_message "✓ Active Google Cloud account: $active_account"
    
    # Check if a project is set
    local current_project
    current_project=$(gcloud config get-value project 2>/dev/null)
    if [[ -n "$current_project" && "$current_project" != "(unset)" ]]; then
        log_message "✓ Current project: $current_project"
    else
        log_message "Warning: No default project set"
        log_message "Set a project with: gcloud config set project YOUR_PROJECT_ID"
        return 1
    fi
    
    return 0
}

check_gemini_api_enabled() {
    log_message "Checking if Generative AI API is enabled..."
    
    local current_project
    current_project=$(gcloud config get-value project 2>/dev/null)
    
    if [[ -z "$current_project" || "$current_project" == "(unset)" ]]; then
        log_message "Warning: Cannot check API status - no project set"
        return 1
    fi
    
    # Check if Generative AI API is enabled
    if gcloud services list --enabled --filter="name:generativeai.googleapis.com" --format="value(name)" | grep -q "generativeai.googleapis.com"; then
        log_message "✓ Generative AI API is enabled for project: $current_project"
        return 0
    else
        log_message "Warning: Generative AI API not enabled for project: $current_project"
        log_message "Enable with: gcloud services enable generativeai.googleapis.com"
        return 1
    fi
}

is_gemini_installed() {
    # Check if gcloud gemini command exists
    if gcloud gemini --help >/dev/null 2>&1; then
        return 0
    fi
    
    # Also check components list
    if gcloud components list --filter="id:gemini" --format="value(state)" 2>/dev/null | grep -q "Installed"; then
        return 0
    fi
    
    return 1
}

install_gemini_cli() {
    log_message "Installing Google Gemini CLI via gcloud components..."
    
    # Check if already installed
    if is_gemini_installed; then
        local version_info
        version_info=$(gcloud version --format="value(Google Cloud SDK)" 2>/dev/null || echo "unknown")
        log_message "Google Gemini CLI already available in Google Cloud SDK: $version_info"
        log_message "Run './update_gemini_cli.sh' to update gcloud components"
        return 0
    fi
    
    # Note: As of 2024, Gemini CLI might be part of core gcloud or require enabling
    # First, try to see if it's already available
    if gcloud gemini --help >/dev/null 2>&1; then
        log_message "✓ Google Gemini CLI is already available in your gcloud installation"
        return 0
    fi
    
    # Try to install/enable gemini component if it exists as a separate component
    log_message "Attempting to install Gemini component..."
    if gcloud components install gemini 2>/dev/null; then
        log_message "✓ Gemini component installed successfully"
    else
        log_message "Info: Gemini may be part of core gcloud SDK"
        log_message "Checking if gemini commands are available..."
        
        # Test if gemini commands work
        if gcloud gemini --help >/dev/null 2>&1; then
            log_message "✓ Google Gemini CLI is available through gcloud"
        else
            log_message "Warning: Gemini CLI not found"
            log_message "This may require a newer version of Google Cloud SDK"
            log_message "Or Gemini CLI may not be available in your region/project"
            return 1
        fi
    fi
    
    return 0
}

show_next_steps() {
    log_message "Installation completed successfully!"
    log_message ""
    
    local auth_status=0
    check_gcp_setup || auth_status=1
    
    if [[ $auth_status -ne 0 ]]; then
        log_message "Next steps:"
        log_message ""
        log_message "1. Authenticate with Google Cloud (REQUIRED):"
        log_message "   gcloud auth login"
        log_message "   gcloud config set project YOUR_PROJECT_ID"
        log_message ""
        log_message "2. Enable Generative AI API:"
        log_message "   gcloud services enable generativeai.googleapis.com"
        log_message ""
        log_message "3. Test the installation (after setup):"
    else
        log_message "Next steps:"
        log_message ""
        local api_status=0
        check_gemini_api_enabled || api_status=1
        
        if [[ $api_status -ne 0 ]]; then
            log_message "1. Enable Generative AI API:"
            log_message "   gcloud services enable generativeai.googleapis.com"
            log_message ""
            log_message "2. Test the installation:"
        else
            log_message "1. Test the installation:"
        fi
    fi
    
    log_message "   gcloud gemini --help"
    log_message "   gcloud version"
    log_message ""
    log_message "4. Example usage:"
    log_message "   # Code suggestions (if available)"
    log_message "   gcloud gemini code-assist suggest --help"
    log_message "   # Code explanations (if available)"
    log_message "   gcloud gemini code-assist explain --help"
    log_message ""
    log_message "5. Documentation:"
    log_message "   • Google Cloud Console: https://console.cloud.google.com/"
    log_message "   • Gemini API docs: https://cloud.google.com/gemini/docs/"
    
    if [[ $auth_status -ne 0 ]]; then
        log_message ""
        log_message "⚠️  Setup required: Authenticate and configure project before using Gemini CLI"
    fi
}

main() {
    log_message "Starting Google Gemini CLI installation..."
    
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
    
    # Check Google Cloud SDK version
    local gcloud_version
    gcloud_version=$(gcloud version --format="value(Google Cloud SDK)" 2>/dev/null || echo "unknown")
    log_message "Google Cloud SDK version: $gcloud_version"
    
    # Check GCP authentication and project setup
    check_gcp_setup
    
    # Check if Generative AI API is enabled
    check_gemini_api_enabled
    
    # Install Gemini CLI
    if install_gemini_cli; then
        show_next_steps
    else
        log_message "Error: Google Gemini CLI installation failed"
        log_message ""
        log_message "Troubleshooting steps:"
        log_message "1. Update Google Cloud SDK: gcloud components update"
        log_message "2. Check available components: gcloud components list"
        log_message "3. Verify authentication: gcloud auth list"
        log_message "4. Check project access: gcloud projects list"
        log_message "5. Visit Google Cloud Console: https://console.cloud.google.com/"
        log_message ""
        log_message "Note: Gemini CLI availability may depend on:"
        log_message "• Your Google Cloud project settings"
        log_message "• Regional availability"
        log_message "• API access permissions"
        exit 1
    fi
}

main "$@"