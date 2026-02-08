#!/bin/bash
set -u  # Required per repo guidelines

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../../bash/common/repo_lib.sh"

# Initialize logging
log_file="${SCRIPT_DIR}/$(basename "$0" .sh).log"

# Cursor CLI uninstall configuration
CURSOR_APP_NAME="Cursor.app"
CURSOR_SYMLINK_PATH="/usr/local/bin/cursor"

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Uninstall Cursor IDE and CLI command.

OPTIONS:
    -h, --help              Show this help message
    -y, --yes               Skip confirmation prompts
    --keep-config           Keep user configuration and settings
    --keep-ide              Only remove CLI symlink, keep IDE
    --config-only           Only remove configuration, keep IDE and CLI

DESCRIPTION:
    This script removes Cursor IDE and associated CLI command from your system.
    By default, it will also remove user configuration and settings.

    Default removal includes:
    - Cursor IDE application (/Applications/Cursor.app)
    - CLI symlink (/usr/local/bin/cursor)
    - User configuration (~/.cursor, ~/Library/Application Support/Cursor)
    - User caches and logs

EXAMPLES:
    $0                      # Full uninstall with confirmation
    $0 -y                   # Full uninstall without confirmation
    $0 --keep-config        # Remove app but keep settings
    $0 --keep-ide           # Only remove CLI symlink
    $0 --config-only        # Only remove configuration files

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
    elif [[ "$cursor_cli_available" == true ]]; then
        echo "cli_only"
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

find_cursor_config_locations() {
    local config_paths=()
    
    # Common Cursor configuration directories
    local potential_paths=(
        "$HOME/.cursor"
        "$HOME/Library/Application Support/Cursor"
        "$HOME/Library/Preferences/com.todesktop.230313mzl4w4u92.plist"
        "$HOME/Library/Caches/Cursor"
        "$HOME/Library/Logs/Cursor"
        "$HOME/Library/Saved Application State/com.todesktop.230313mzl4w4u92.savedState"
    )
    
    for path in "${potential_paths[@]}"; do
        if [[ -e "$path" ]]; then
            config_paths+=("$path")
        fi
    done
    
    printf '%s\n' "${config_paths[@]}"
}

confirm_action() {
    local message="$1"
    local default_yes="${2:-false}"
    
    if [[ "$default_yes" == true ]]; then
        return 0
    fi
    
    echo
    read -p "$message (y/N): " -r response
    case "$response" in
        [yY]|[yY][eE][sS])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

remove_cursor_ide() {
    local cursor_app_path="/Applications/${CURSOR_APP_NAME}"
    
    if [[ -d "$cursor_app_path" ]]; then
        log_message "Removing Cursor IDE from $cursor_app_path..."
        
        # Force quit Cursor if running
        if pgrep -x "Cursor" >/dev/null; then
            log_message "Terminating running Cursor processes..."
            pkill -x "Cursor" || true
            sleep 2
        fi
        
        if rm -rf "$cursor_app_path"; then
            log_message "✓ Cursor IDE removed successfully"
            return 0
        else
            log_message "Error: Failed to remove Cursor IDE"
            return 1
        fi
    else
        log_message "Cursor IDE not found at $cursor_app_path"
        return 0
    fi
}

remove_cursor_cli() {
    if [[ -L "$CURSOR_SYMLINK_PATH" ]]; then
        log_message "Removing cursor CLI symlink from $CURSOR_SYMLINK_PATH..."
        
        if rm "$CURSOR_SYMLINK_PATH"; then
            log_message "✓ Cursor CLI symlink removed successfully"
            return 0
        else
            log_message "Error: Failed to remove cursor CLI symlink"
            log_message "You may need to run with sudo: sudo rm '$CURSOR_SYMLINK_PATH'"
            return 1
        fi
    elif [[ -f "$CURSOR_SYMLINK_PATH" ]]; then
        log_message "Removing cursor CLI binary from $CURSOR_SYMLINK_PATH..."
        
        if rm "$CURSOR_SYMLINK_PATH"; then
            log_message "✓ Cursor CLI binary removed successfully"
            return 0
        else
            log_message "Error: Failed to remove cursor CLI binary"
            return 1
        fi
    else
        log_message "Cursor CLI not found at $CURSOR_SYMLINK_PATH"
        return 0
    fi
}

remove_cursor_config() {
    log_message "Finding Cursor configuration files..."
    
    local config_paths
    mapfile -t config_paths < <(find_cursor_config_locations)
    
    if [[ ${#config_paths[@]} -eq 0 ]]; then
        log_message "No Cursor configuration files found"
        return 0
    fi
    
    log_message "Found ${#config_paths[@]} configuration location(s):"
    for path in "${config_paths[@]}"; do
        log_message "  - $path"
    done
    
    local removed_count=0
    for path in "${config_paths[@]}"; do
        log_message "Removing: $path"
        
        if rm -rf "$path"; then
            log_message "✓ Removed: $path"
            ((removed_count++))
        else
            log_message "✗ Failed to remove: $path"
        fi
    done
    
    if [[ $removed_count -eq ${#config_paths[@]} ]]; then
        log_message "✓ All Cursor configuration files removed successfully"
        return 0
    elif [[ $removed_count -gt 0 ]]; then
        log_message "⚠ Partially removed configuration files ($removed_count/${#config_paths[@]})"
        return 1
    else
        log_message "✗ Failed to remove configuration files"
        return 1
    fi
}

show_removal_summary() {
    local will_remove_ide="$1"
    local will_remove_cli="$2"
    local will_remove_config="$3"
    
    echo
    echo "=== Cursor Uninstall Summary ==="
    echo
    
    if [[ "$will_remove_ide" == true ]]; then
        echo "Will remove:"
        echo "  ✓ Cursor IDE (/Applications/${CURSOR_APP_NAME})"
    fi
    
    if [[ "$will_remove_cli" == true ]]; then
        echo "  ✓ Cursor CLI command ($CURSOR_SYMLINK_PATH)"
    fi
    
    if [[ "$will_remove_config" == true ]]; then
        echo "  ✓ User configuration and settings"
        local config_paths
        mapfile -t config_paths < <(find_cursor_config_locations)
        for path in "${config_paths[@]}"; do
            echo "    - $path"
        done
    fi
    
    if [[ "$will_remove_ide" == false ]] && [[ "$will_remove_cli" == false ]] && [[ "$will_remove_config" == false ]]; then
        echo "Nothing to remove - Cursor is not installed"
        return
    fi
    
    echo
    echo "Will keep:"
    if [[ "$will_remove_ide" == false ]] && [[ -d "/Applications/${CURSOR_APP_NAME}" ]]; then
        echo "  ✓ Cursor IDE (/Applications/${CURSOR_APP_NAME})"
    fi
    
    if [[ "$will_remove_cli" == false ]] && [[ -e "$CURSOR_SYMLINK_PATH" ]]; then
        echo "  ✓ Cursor CLI command ($CURSOR_SYMLINK_PATH)"
    fi
    
    if [[ "$will_remove_config" == false ]]; then
        local config_paths
        mapfile -t config_paths < <(find_cursor_config_locations)
        if [[ ${#config_paths[@]} -gt 0 ]]; then
            echo "  ✓ User configuration and settings"
        fi
    fi
    
    echo
}

uninstall_cursor() {
    local skip_confirmation=false
    local keep_config=false
    local keep_ide=false
    local config_only=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -y|--yes)
                skip_confirmation=true
                shift
                ;;
            --keep-config)
                keep_config=true
                shift
                ;;
            --keep-ide)
                keep_ide=true
                shift
                ;;
            --config-only)
                config_only=true
                shift
                ;;
            *)
                log_message "Error: Unknown option $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    log_message "Starting Cursor uninstall process..."
    
    # Check platform compatibility
    local platform
    platform=$(detect_platform)
    if [[ "$platform" != "macos" ]]; then
        log_message "Error: This script only supports macOS"
        log_message "Platform detected: $(uname -s)"
        exit 1
    fi
    
    # Check current installation status
    local installation_status
    installation_status=$(check_cursor_installation)
    
    if [[ "$installation_status" == "not_installed" ]]; then
        log_message "Cursor is not installed"
        
        # Still check for configuration files
        local config_paths
        mapfile -t config_paths < <(find_cursor_config_locations)
        
        if [[ ${#config_paths[@]} -gt 0 ]]; then
            log_message "Found configuration files to clean up:"
            for path in "${config_paths[@]}"; do
                log_message "  - $path"
            done
            
            if confirm_action "Remove configuration files?" "$skip_confirmation"; then
                remove_cursor_config
            fi
        fi
        
        exit 0
    fi
    
    # Get current version for logging
    local current_version
    current_version=$(get_cursor_version)
    log_message "Found Cursor version: $current_version"
    
    # Determine what to remove based on options
    local will_remove_ide=true
    local will_remove_cli=true
    local will_remove_config=true
    
    if [[ "$keep_ide" == true ]]; then
        will_remove_ide=false
    fi
    
    if [[ "$keep_config" == true ]]; then
        will_remove_config=false
    fi
    
    if [[ "$config_only" == true ]]; then
        will_remove_ide=false
        will_remove_cli=false
        will_remove_config=true
    fi
    
    # Don't remove CLI if IDE is being kept and CLI symlink points to IDE
    if [[ "$will_remove_ide" == false ]] && [[ "$will_remove_cli" == true ]]; then
        local cursor_binary="/Applications/${CURSOR_APP_NAME}/Contents/Resources/app/bin/cursor"
        if [[ -L "$CURSOR_SYMLINK_PATH" ]] && [[ "$(readlink "$CURSOR_SYMLINK_PATH")" == "$cursor_binary" ]]; then
            log_message "Keeping CLI symlink since IDE is being preserved"
            will_remove_cli=false
        fi
    fi
    
    # Show summary and get confirmation
    show_removal_summary "$will_remove_ide" "$will_remove_cli" "$will_remove_config"
    
    if ! confirm_action "Proceed with uninstallation?" "$skip_confirmation"; then
        log_message "Uninstallation cancelled by user"
        exit 0
    fi
    
    # Perform removals
    local success=true
    
    if [[ "$will_remove_cli" == true ]]; then
        if ! remove_cursor_cli; then
            success=false
        fi
    fi
    
    if [[ "$will_remove_ide" == true ]]; then
        if ! remove_cursor_ide; then
            success=false
        fi
    fi
    
    if [[ "$will_remove_config" == true ]]; then
        if ! remove_cursor_config; then
            success=false
        fi
    fi
    
    # Final verification
    local final_status
    final_status=$(check_cursor_installation)
    
    echo
    if [[ "$success" == true ]]; then
        if [[ "$final_status" == "not_installed" ]] || [[ "$config_only" == true ]]; then
            log_message "🎉 Cursor uninstallation completed successfully!"
        else
            log_message "✓ Cursor uninstallation completed (partial removal as requested)"
        fi
    else
        log_message "⚠ Cursor uninstallation completed with some warnings"
        log_message "Check the log above for any failed operations"
    fi
    
    echo
    log_message "Summary:"
    log_message "  IDE status: $(check_cursor_installation)"
    log_message "  Configuration: $(find_cursor_config_locations | wc -l | tr -d ' ') files remaining"
    
    if [[ "$will_remove_ide" == true ]] && [[ -d "/Applications/${CURSOR_APP_NAME}" ]]; then
        echo
        log_message "Note: If you want to reinstall Cursor later:"
        log_message "  Run: ${SCRIPT_DIR}/install_cursor_cli.sh"
    fi
}

# Main execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    uninstall_cursor "$@"
fi