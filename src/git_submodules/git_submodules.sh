#!/usr/bin/env bash
#
# git_submodules.sh - Manage git submodules with ease
#
# Usage:
#   ./git_submodules.sh list
#   ./git_submodules.sh add <url> <path>
#   ./git_submodules.sh remove <path>
#   ./git_submodules.sh update [--recursive] [path]
#   ./git_submodules.sh status
#   ./git_submodules.sh init [path]
#   ./git_submodules.sh sync

set -euo pipefail

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Script metadata
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
readonly SCRIPT_NAME

# Preset base paths for common repositories
declare -A PRESET_PATHS=(
    [designs]="/Users/rerickso/Library/CloudStorage/GoogleDrive-rerickson@linkedin.com/My Drive/Designs"
    [talent]="/Users/rerickso/Library/CloudStorage/GoogleDrive-rerickson@linkedin.com/My Drive/Talent"
)

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# Check if we're in a git repository
ensure_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not a git repository. Please run this script from within a git repository."
        exit 1
    fi
}

# Display usage information
usage() {
    cat << EOF
Usage: $SCRIPT_NAME <command> [options]

Manage git submodules with ease.

Commands:
    list                        List all submodules with their status
    add <url> <path> [branch]   Add a new submodule at the specified path
    add --preset <name> [branch]
                                Add entire preset repo as submodule (defaults to main)
    remove <path>               Remove a submodule (preserves working directory)
    update [--recursive] [path] Update submodule(s) to latest commit
    status                      Show detailed status of all submodules
    init [path]                 Initialize submodule(s)
    sync                        Sync submodule URLs from .gitmodules to .git/config
    help                        Show this help message

Presets (auto-destination: repositories/<preset>, default branch: main):
    designs                     /Users/.../Google Drive/Designs
    talent                      /Users/.../Google Drive/Talent

Examples:
    $SCRIPT_NAME list
    $SCRIPT_NAME add https://github.com/user/repo.git libs/mylib
    $SCRIPT_NAME add https://github.com/user/repo.git libs/mylib main
    $SCRIPT_NAME add --preset designs
    $SCRIPT_NAME add --preset talent develop
    $SCRIPT_NAME remove repositories/designs
    $SCRIPT_NAME update --recursive
    $SCRIPT_NAME update libs/mylib
    $SCRIPT_NAME status

EOF
}

# List all submodules
cmd_list() {
    ensure_git_repo
    
    if ! git config --file .gitmodules --get-regexp path > /dev/null 2>&1; then
        log_warning "No submodules found in this repository."
        return 0
    fi
    
    log_info "Submodules in this repository:"
    echo ""
    
    git config --file .gitmodules --get-regexp path | while read -r key path; do
        local url
        url=$(git config --file .gitmodules --get "submodule.${path}.url" || echo "Unknown")
        
        local branch
        branch=$(git config --file .gitmodules --get "submodule.${path}.branch" 2>/dev/null || echo "default")
        
        local status="Not initialized"
        if [[ -d "$path/.git" ]] || [[ -f "$path/.git" ]]; then
            status="${GREEN}Initialized${NC}"
        fi
        
        echo -e "  ${BLUE}Path:${NC}   $path"
        echo -e "  ${BLUE}URL:${NC}    $url"
        echo -e "  ${BLUE}Branch:${NC} $branch"
        echo -e "  ${BLUE}Status:${NC} $status"
        echo ""
    done
}

# Add a new submodule
cmd_add() {
    ensure_git_repo
    
    # Check for preset option
    if [[ $# -gt 0 && "$1" == "--preset" ]]; then
        if [[ $# -lt 2 ]]; then
            log_error "Usage: $SCRIPT_NAME add --preset <name> [branch]"
            log_error "Available presets: ${!PRESET_PATHS[*]}"
            exit 1
        fi
        
        local preset_name="$2"
        local branch="${3:-main}"
        
        # Validate preset exists
        if [[ -z "${PRESET_PATHS[$preset_name]:-}" ]]; then
            log_error "Unknown preset: $preset_name"
            log_error "Available presets: ${!PRESET_PATHS[*]}"
            exit 1
        fi
        
        local url="${PRESET_PATHS[$preset_name]}"
        local path="repositories/${preset_name}"
        
        # Check if source directory exists and is a git repo
        if [[ ! -d "$url" ]]; then
            log_error "Directory not found: $url"
            exit 1
        fi
        
        if [[ ! -d "${url}/.git" ]]; then
            log_error "Not a git repository: $url"
            log_error "The directory must be a git repository to add as a submodule."
            exit 1
        fi
        
        log_info "Adding submodule from preset '$preset_name'..."
        log_info "  Source: $url"
        log_info "  Destination: $path"
        log_info "  Branch: $branch"
    else
        # Standard URL-based add
        if [[ $# -lt 2 ]]; then
            log_error "Usage: $SCRIPT_NAME add <url> <path> [branch]"
            log_error "   Or: $SCRIPT_NAME add --preset <name> [branch]"
            exit 1
        fi
        
        local url="$1"
        local path="$2"
        local branch="${3:-}"
        
        log_info "Adding submodule..."
        log_info "  URL:  $url"
        log_info "  Path: $path"
        [[ -n "$branch" ]] && log_info "  Branch: $branch"
    fi
    
    # Check if path already exists
    if [[ -d "$path" ]]; then
        log_error "Path '$path' already exists. Please choose a different path or remove the existing directory."
        exit 1
    fi
    
    # Check if submodule already registered
    if git config --file .gitmodules --get "submodule.${path}.url" > /dev/null 2>&1; then
        log_error "Submodule at path '$path' is already registered."
        exit 1
    fi
    
    # Add the submodule
    if [[ -n "$branch" ]]; then
        if git submodule add -b "$branch" "$url" "$path"; then
            log_success "Submodule added successfully!"
            log_info "Don't forget to commit the changes: git commit -m 'Add submodule $path'"
        else
            log_error "Failed to add submodule."
            exit 1
        fi
    else
        if git submodule add "$url" "$path"; then
            log_success "Submodule added successfully!"
            log_info "Don't forget to commit the changes: git commit -m 'Add submodule $path'"
        else
            log_error "Failed to add submodule."
            exit 1
        fi
    fi
}

# Remove a submodule
cmd_remove() {
    ensure_git_repo
    
    if [[ $# -lt 1 ]]; then
        log_error "Usage: $SCRIPT_NAME remove <path>"
        exit 1
    fi
    
    local path="$1"
    
    # Check if submodule exists
    if ! git config --file .gitmodules --get "submodule.${path}.url" > /dev/null 2>&1; then
        log_error "Submodule at path '$path' not found."
        exit 1
    fi
    
    log_warning "This will remove the submodule '$path' from git tracking."
    log_info "The working directory will be preserved as '$path.backup'."
    read -p "Continue? (y/N) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Aborted."
        exit 0
    fi
    
    log_info "Removing submodule '$path'..."
    
    # Backup the working directory if it exists
    if [[ -d "$path" ]]; then
        mv "$path" "${path}.backup"
        log_info "Working directory backed up to '${path}.backup'"
    fi
    
    # Deinitialize the submodule
    git submodule deinit -f "$path" 2>/dev/null || true
    
    # Remove from .git/modules
    rm -rf ".git/modules/$path"
    
    # Remove the submodule entry from .git/config
    git config --remove-section "submodule.${path}" 2>/dev/null || true
    
    # Remove from index and .gitmodules
    git rm -f "$path"
    
    log_success "Submodule removed successfully!"
    log_info "Backup directory: ${path}.backup"
    log_info "Don't forget to commit the changes: git commit -m 'Remove submodule $path'"
}

# Update submodules
cmd_update() {
    ensure_git_repo
    
    local recursive=""
    local path=""
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --recursive|-r)
                recursive="--recursive"
                shift
                ;;
            *)
                path="$1"
                shift
                ;;
        esac
    done
    
    if [[ -n "$path" ]]; then
        log_info "Updating submodule '$path'..."
        if git submodule update --remote $recursive "$path"; then
            log_success "Submodule updated successfully!"
        else
            log_error "Failed to update submodule."
            exit 1
        fi
    else
        log_info "Updating all submodules..."
        if git submodule update --remote $recursive; then
            log_success "All submodules updated successfully!"
        else
            log_error "Failed to update submodules."
            exit 1
        fi
    fi
}

# Show submodule status
cmd_status() {
    ensure_git_repo
    
    if ! git config --file .gitmodules --get-regexp path > /dev/null 2>&1; then
        log_warning "No submodules found in this repository."
        return 0
    fi
    
    log_info "Submodule status:"
    echo ""
    git submodule status --recursive
}

# Initialize submodules
cmd_init() {
    ensure_git_repo
    
    local path="${1:-}"
    
    if [[ -n "$path" ]]; then
        log_info "Initializing submodule '$path'..."
        if git submodule init "$path"; then
            log_success "Submodule initialized!"
            log_info "Run 'git submodule update' to checkout the code."
        else
            log_error "Failed to initialize submodule."
            exit 1
        fi
    else
        log_info "Initializing all submodules..."
        if git submodule init; then
            log_success "All submodules initialized!"
            log_info "Run 'git submodule update' to checkout the code."
        else
            log_error "Failed to initialize submodules."
            exit 1
        fi
    fi
}

# Sync submodule URLs
cmd_sync() {
    ensure_git_repo
    
    if ! git config --file .gitmodules --get-regexp path > /dev/null 2>&1; then
        log_warning "No submodules found in this repository."
        return 0
    fi
    
    log_info "Syncing submodule URLs from .gitmodules to .git/config..."
    if git submodule sync --recursive; then
        log_success "Submodule URLs synced successfully!"
    else
        log_error "Failed to sync submodule URLs."
        exit 1
    fi
}

# Main command dispatcher
main() {
    if [[ $# -eq 0 ]]; then
        usage
        exit 0
    fi
    
    local command="$1"
    shift
    
    case "$command" in
        list|ls)
            cmd_list "$@"
            ;;
        add|create)
            cmd_add "$@"
            ;;
        remove|rm|delete)
            cmd_remove "$@"
            ;;
        update|up)
            cmd_update "$@"
            ;;
        status|st)
            cmd_status "$@"
            ;;
        init)
            cmd_init "$@"
            ;;
        sync)
            cmd_sync "$@"
            ;;
        help|--help|-h)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown command: $command"
            echo ""
            usage
            exit 1
            ;;
    esac
}

main "$@"
