#!/bin/bash
set -u  # Required per repo guidelines

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../../bash/common/repo_lib.sh"

# Initialize logging
log_file="${SCRIPT_DIR}/$(basename "$0" .sh).log"

# Cursor CLI update configuration
CURSOR_APP_NAME="Cursor.app"
CURSOR_SYMLINK_PATH="/usr/local/bin/cursor"

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Update Cursor IDE and CLI command.

OPTIONS:
    -h, --help          Show this help message
    -f, --force         Force update check even if auto-update is enabled
    --check-only        Only check for updates, don't install

DESCRIPTION:
    This script checks for and installs Cursor IDE updates. Cursor typically
    has built-in auto-update functionality, but this script provides manual
    update checking and installation.

EXAMPLES:
    $0                   # Check and install updates
    $0 --check-only      # Only check for updates
    $0 --force           # Force update check

EOF
}

detect_platform() {
    case "$(uname -s)" in
        Darwin*)    echo "macos" ;;
        *)          echo "unsupported" ;;
    esac
}

check_cursor_installation() {
    local cursor_app_path="/Applications/${CURSOR_APP_NAME}"
    local cursor_cli_available=false
    
    # Check if Cursor IDE is installed
    if [[ -d "$cursor_app_path" ]]; then
        log_message "✓ Found Cursor IDE at $cursor_app_path"
        
        # Check if CLI symlink exists and works
        if [[ -L "$CURSOR_SYMLINK_PATH" ]] && command -v cursor >/dev/null 2>&1; then
            cursor_cli_available=true
            log_message "✓ Found cursor CLI command at $CURSOR_SYMLINK_PATH"
        fi
    fi
    
    if [[ -d "$cursor_app_path" ]] && [[ "$cursor_cli_available" == true ]]; then
        echo "fully_installed"
    elif [[ -d "$cursor_app_path" ]]; then
        echo "ide_only"
    else
        echo "not_installed"
    fi
}

get_cursor_version() {
    local cursor_app_path="/Applications/${CURSOR_APP_NAME}"
    
    if [[ -d "$cursor_app_path" ]]; then
        # Try to get version from Info.plist
        local version
        version=$(plutil -p "${cursor_app_path}/Contents/Info.plist" 2>/dev/null | grep -E 'CFBundleShortVersionString|CFBundleVersion' | head -1 | awk -F'"' '{print $4}')
        
        if [[ -n "$version" ]]; then
            echo "$version"
        else
            echo "unknown"
        fi
    else
        echo "not installed"
    fi
}

check_auto_update_status() {
    log_message "Checking Cursor auto-update configuration..."
    
    # Cursor typically stores preferences in ~/Library/Application Support/Cursor
    local cursor_config_dir="$HOME/Library/Application Support/Cursor"
    local user_settings="${cursor_config_dir}/User/settings.json"
    
    if [[ -f "$user_settings" ]]; then
        # Check if auto-update is disabled
        if grep -q '"update.mode".*"none"' "$user_settings" 2>/dev/null; then
            log_message "Auto-update is disabled in Cursor settings"
            return 1
        elif grep -q '"update.mode".*"manual"' "$user_settings" 2>/dev/null; then
            log_message "Auto-update is set to manual mode"
            return 1
        else
            log_message "Auto-update appears to be enabled (default)"
            return 0
        fi
    else
        log_message "Cursor settings not found, assuming default auto-update behavior"
        return 0
    fi
}

trigger_cursor_update_check() {
    log_message "Triggering Cursor update check..."
    
    # Check if Cursor is currently running
    if pgrep -x "Cursor" >/dev/null; then
        log_message "Cursor is currently running"
        log_message "Cursor typically checks for updates automatically when running"
        log_message "You can also check manually: Help → Check for Updates"
        return 0
    else
        log_message "Starting Cursor to trigger update check..."
        
        # Launch Cursor briefly to trigger update check
        if open -a Cursor; then
            log_message "Cursor launched. It will check for updates automatically"
            log_message "You can close Cursor after it finishes loading"
            return 0
        else
            log_message "Error: Failed to launch Cursor"
            return 1
        fi
    fi
}

reinstall_cursor() {
    log_message "Reinstalling Cursor using install script..."
    
    local install_script="${SCRIPT_DIR}/install_cursor_cli.sh"
    
    if [[ -f "$install_script" ]]; then
        log_message "Running: $install_script --force"
        if "$install_script" --force; then
            log_message "✓ Cursor reinstallation completed"
            return 0
        else
            log_message "Error: Cursor reinstallation failed"
            return 1
        fi
    else
        log_message "Error: Install script not found at $install_script"
        log_message "Please run the install script manually to update Cursor"
        return 1
    fi
}

fix_cursor_cli() {
    log_message "Fixing Cursor CLI symlink..."
    
    local cursor_binary="/Applications/${CURSOR_APP_NAME}/Contents/Resources/app/bin/cursor"
    
    # Check if the cursor binary exists
    if [[ ! -f "$cursor_binary" ]]; then
        # Try alternative path
        cursor_binary="/Applications/${CURSOR_APP_NAME}/Contents/MacOS/Cursor"
        if [[ ! -f "$cursor_binary" ]]; then
            log_message "Error: Could not locate Cursor CLI binary"
            return 1
        fi
    fi
    
    # Create /usr/local/bin if it doesn't exist
    if [[ ! -d "/usr/local/bin" ]]; then
        log_message "Creating /usr/local/bin directory..."
        mkdir -p "/usr/local/bin"
    fi
    
    # Remove existing symlink if present
    if [[ -L "$CURSOR_SYMLINK_PATH" ]]; then
        rm "$CURSOR_SYMLINK_PATH"
    fi
    
    # Create symlink
    if ln -s "$cursor_binary" "$CURSOR_SYMLINK_PATH"; then
        log_message "✓ Fixed cursor CLI symlink at $CURSOR_SYMLINK_PATH"
        return 0
    else
        log_message "Error: Failed to create cursor CLI symlink"
        log_message "You may need to run with sudo:"
        log_message "  sudo ln -s '$cursor_binary' '$CURSOR_SYMLINK_PATH'"
        return 1
    fi
}

update_cursor() {
    local force_update=false
    local check_only=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -f|--force)
                force_update=true
                shift
                ;;
            --check-only)
                check_only=true
                shift
                ;;
            *)
                log_message "Error: Unknown option $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    log_message "Starting Cursor update process..."
    
    # Check platform compatibility
    local platform
    platform=$(detect_platform)
    if [[ "$platform" != "macos" ]]; then
        log_message "Error: This script only supports macOS"
        log_message "Platform detected: $(uname -s)"
        exit 1
    fi
    
    # Check if Cursor is installed
    local installation_status
    installation_status=$(check_cursor_installation)
    
    if [[ "$installation_status" == "not_installed" ]]; then
        log_message "Error: Cursor is not installed"
        log_message "Run the install script first: ${SCRIPT_DIR}/install_cursor_cli.sh"
        exit 1
    fi
    
    # Get current version
    local current_version
    current_version=$(get_cursor_version)
    log_message "Current Cursor version: $current_version"
    
    # Fix CLI if needed
    if [[ "$installation_status" == "ide_only" ]]; then
        log_message "CLI symlink missing, attempting to fix..."
        if ! fix_cursor_cli; then
            log_message "Warning: Could not fix CLI symlink. You may need to run with sudo"
        fi
    fi
    
    # Check auto-update status
    local auto_update_enabled=true
    if ! check_auto_update_status; then
        auto_update_enabled=false
    fi
    
    if [[ "$auto_update_enabled" == true ]] && [[ "$force_update" != true ]]; then
        log_message ""
        log_message "ℹ️  Cursor has auto-update enabled (default behavior)"
        log_message "It will automatically check for and install updates"
        log_message ""
        
        if [[ "$check_only" == true ]]; then
            log_message "To check for updates manually:"
            log_message "  1. Open Cursor"
            log_message "  2. Go to Help → Check for Updates"
        else
            log_message "Triggering update check..."
            trigger_cursor_update_check
        fi
        
        log_message ""
        log_message "If you prefer manual updates, you can disable auto-update:"
        log_message "  1. Open Cursor"
        log_message "  2. Go to Preferences → Settings"
        log_message "  3. Search for 'update.mode'"
        log_message "  4. Set to 'manual' or 'none'"
        log_message ""
        log_message "Use --force to bypass auto-update check"
        
        exit 0
    fi
    
    log_message "Auto-update is disabled or --force specified"
    
    if [[ "$check_only" == true ]]; then
        log_message ""
        log_message "To check for updates manually:"
        log_message "  1. Open Cursor"
        log_message "  2. Go to Help → Check for Updates"
        log_message ""
        log_message "Or use this script without --check-only to reinstall latest version"
        exit 0
    fi
    
    # Perform manual update by reinstalling
    log_message ""
    log_message "Performing manual update by reinstalling latest version..."
    
    if reinstall_cursor; then
        local new_version
        new_version=$(get_cursor_version)
        
        log_message ""
        log_message "🎉 Cursor update completed!"
        log_message "  Previous version: $current_version"
        log_message "  Current version: $new_version"
        log_message ""
        
        if [[ "$current_version" == "$new_version" ]] && [[ "$current_version" != "unknown" ]]; then
            log_message "ℹ️  Version unchanged - you may already have the latest version"
        fi
    else
        log_message "Error: Update failed"
        exit 1
    fi
}

# Main execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    update_cursor "$@"
fi