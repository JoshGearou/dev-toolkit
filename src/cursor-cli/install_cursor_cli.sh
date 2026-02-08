#!/bin/bash
set -u  # Required per repo guidelines

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../../bash/common/repo_lib.sh"

# Initialize logging
log_file="${SCRIPT_DIR}/$(basename "$0" .sh).log"

# Cursor CLI installation configuration
CURSOR_APP_NAME="Cursor.app"
CURSOR_DOWNLOAD_URL="https://download.cursor.sh/mac"
CURSOR_SYMLINK_PATH="/usr/local/bin/cursor"

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Install Cursor IDE and CLI command for macOS.

OPTIONS:
    -h, --help          Show this help message
    -f, --force         Force reinstallation if already installed
    --skip-symlink      Install IDE only, skip CLI symlink setup

DESCRIPTION:
    This script downloads and installs Cursor IDE, then sets up the 'cursor'
    command in your PATH for opening files and projects from the terminal.

    The installation process:
    1. Downloads Cursor IDE from the official website
    2. Installs to /Applications/Cursor.app
    3. Creates symlink at /usr/local/bin/cursor for CLI access
    4. Verifies the installation

EXAMPLES:
    $0                    # Standard installation
    $0 --force            # Reinstall even if already present
    $0 --skip-symlink     # Install IDE only

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

download_and_install_cursor() {
    log_message "Starting Cursor IDE download and installation..."
    
    # Create temporary directory for download
    local temp_dir
    temp_dir=$(mktemp -d)
    local dmg_file="${temp_dir}/Cursor.dmg"
    
    log_message "Downloading Cursor IDE from $CURSOR_DOWNLOAD_URL..."
    
    # Download Cursor DMG
    if ! run_command_with_retry "curl -L -o '$dmg_file' '$CURSOR_DOWNLOAD_URL'"; then
        log_message "Error: Failed to download Cursor IDE"
        rm -rf "$temp_dir"
        return 1
    fi
    
    log_message "Download completed. Installing Cursor IDE..."
    
    # Mount the DMG
    local mount_point
    mount_point=$(hdiutil attach "$dmg_file" -nobrowse -noautoopen | awk '/\/Volumes\//{print $NF}')
    
    if [[ -z "$mount_point" ]]; then
        log_message "Error: Failed to mount Cursor DMG"
        rm -rf "$temp_dir"
        return 1
    fi
    
    # Copy application to /Applications
    if [[ -d "${mount_point}/${CURSOR_APP_NAME}" ]]; then
        log_message "Copying Cursor to /Applications..."
        
        # Remove existing installation if present
        if [[ -d "/Applications/${CURSOR_APP_NAME}" ]]; then
            rm -rf "/Applications/${CURSOR_APP_NAME}"
        fi
        
        if cp -R "${mount_point}/${CURSOR_APP_NAME}" /Applications/; then
            log_message "✓ Cursor IDE installed successfully"
        else
            log_message "Error: Failed to copy Cursor to /Applications"
            hdiutil detach "$mount_point" >/dev/null 2>&1
            rm -rf "$temp_dir"
            return 1
        fi
    else
        log_message "Error: Cursor.app not found in DMG"
        hdiutil detach "$mount_point" >/dev/null 2>&1
        rm -rf "$temp_dir"
        return 1
    fi
    
    # Unmount DMG and cleanup
    hdiutil detach "$mount_point" >/dev/null 2>&1
    rm -rf "$temp_dir"
    
    return 0
}

setup_cursor_cli() {
    log_message "Setting up cursor CLI command..."
    
    local cursor_binary="/Applications/${CURSOR_APP_NAME}/Contents/Resources/app/bin/cursor"
    
    # Check if the cursor binary exists
    if [[ ! -f "$cursor_binary" ]]; then
        log_message "Error: Cursor CLI binary not found at $cursor_binary"
        log_message "This may be a different version of Cursor. Trying alternative path..."
        
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
        log_message "✓ Created cursor CLI symlink at $CURSOR_SYMLINK_PATH"
    else
        log_message "Error: Failed to create cursor CLI symlink"
        log_message "You may need to run with sudo or create the symlink manually:"
        log_message "  sudo ln -s '$cursor_binary' '$CURSOR_SYMLINK_PATH'"
        return 1
    fi
    
    return 0
}

verify_installation() {
    log_message "Verifying Cursor installation..."
    
    local installation_status
    installation_status=$(check_cursor_installation)
    
    case "$installation_status" in
        "fully_installed")
            local version
            version=$(get_cursor_version)
            log_message "✓ Cursor IDE and CLI successfully installed"
            log_message "  Version: $version"
            log_message "  IDE: /Applications/${CURSOR_APP_NAME}"
            log_message "  CLI: $CURSOR_SYMLINK_PATH"
            return 0
            ;;
        "ide_only")
            log_message "⚠ Cursor IDE installed but CLI setup failed"
            return 1
            ;;
        "not_installed")
            log_message "✗ Cursor installation failed"
            return 1
            ;;
    esac
}

install_cursor() {
    local force_install=false
    local skip_symlink=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -f|--force)
                force_install=true
                shift
                ;;
            --skip-symlink)
                skip_symlink=true
                shift
                ;;
            *)
                log_message "Error: Unknown option $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    log_message "Starting Cursor CLI installation process..."
    
    # Check platform compatibility
    local platform
    platform=$(detect_platform)
    if [[ "$platform" != "macos" ]]; then
        log_message "Error: This script only supports macOS"
        log_message "Platform detected: $(uname -s)"
        exit 1
    fi
    
    log_message "✓ Platform compatibility confirmed: macOS"
    
    # Check current installation status
    local current_status
    current_status=$(check_cursor_installation)
    
    if [[ "$current_status" == "fully_installed" ]] && [[ "$force_install" != true ]]; then
        local version
        version=$(get_cursor_version)
        log_message "Cursor is already installed (version: $version)"
        log_message "Use --force to reinstall or run update script to upgrade"
        exit 0
    fi
    
    if [[ "$current_status" == "ide_only" ]] && [[ "$skip_symlink" != true ]]; then
        log_message "Cursor IDE found but CLI not set up. Setting up CLI..."
        if setup_cursor_cli; then
            verify_installation
            exit $?
        else
            log_message "Failed to set up CLI. You may need to run with sudo:"
            log_message "  sudo $0"
            exit 1
        fi
    fi
    
    # Download and install Cursor IDE
    if ! download_and_install_cursor; then
        log_message "Error: Failed to install Cursor IDE"
        exit 1
    fi
    
    # Set up CLI command (unless skipped)
    if [[ "$skip_symlink" != true ]]; then
        if ! setup_cursor_cli; then
            log_message "Warning: Cursor IDE installed but CLI setup failed"
            log_message "You can set up the CLI manually or run with sudo:"
            log_message "  sudo $0 --skip-symlink"
            log_message "Then create symlink: sudo ln -s '/Applications/${CURSOR_APP_NAME}/Contents/Resources/app/bin/cursor' '$CURSOR_SYMLINK_PATH'"
        fi
    fi
    
    # Verify final installation
    if verify_installation; then
        log_message ""
        log_message "🎉 Cursor installation completed successfully!"
        log_message ""
        log_message "Next steps:"
        log_message "  1. Open Cursor IDE: open -a Cursor"
        log_message "  2. Open a file with CLI: cursor myfile.txt"
        log_message "  3. Open a project: cursor /path/to/project"
        log_message ""
        log_message "For help: cursor --help"
    else
        log_message "Installation completed with warnings. Check the log above."
        exit 1
    fi
}

# Main execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    install_cursor "$@"
fi