#!/bin/bash
set -u

# macOS Application Removal Tool
# Thoroughly removes applications and all associated files from macOS

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/../../bash/common/repo_lib.sh"

# Configuration
DRY_RUN=false
VERBOSE=false
SKIP_CONFIRM=false
APP_NAME=""
BUNDLE_ID=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

usage() {
    cat << EOF
Usage: $0 [OPTIONS] APP_NAME

Thoroughly remove a macOS application and all associated files.

OPTIONS:
    -n, --dry-run       Show what would be removed without actually removing
    -v, --verbose       Show detailed output
    -y, --yes           Skip confirmation prompts
    -b, --bundle-id ID  Specify bundle ID (e.g., com.company.app)
    -h, --help          Show this help message

EXAMPLES:
    $0 "Slack"                          # Remove Slack app
    $0 --dry-run "Docker"               # Preview what would be removed
    $0 -b com.docker.docker "Docker"    # Remove with specific bundle ID
    $0 -y "Zoom"                        # Remove without confirmation

EOF
    exit 1
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

confirm() {
    if [[ "$SKIP_CONFIRM" == "true" ]]; then
        return 0
    fi

    local prompt="$1"
    echo -ne "${YELLOW}${prompt} [y/N]:${NC} "
    read -r response
    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

is_cloud_storage_path() {
    local path="$1"

    # Common cloud storage locations
    local cloud_paths=(
        "${HOME}/Library/Mobile Documents/com~apple~CloudDocs"  # iCloud Drive
        "${HOME}/iCloud Drive"
        "${HOME}/Google Drive"
        "${HOME}/GoogleDrive"
        "${HOME}/OneDrive"
        "${HOME}/Dropbox"
        "${HOME}/Box"
        "${HOME}/Box Sync"
        "${HOME}/Library/CloudStorage"  # macOS cloud storage root
    )

    for cloud_path in "${cloud_paths[@]}"; do
        # Check if path is within a cloud storage directory
        if [[ "$path" == "$cloud_path"* ]]; then
            return 0  # true - is cloud storage
        fi
    done

    return 1  # false - not cloud storage
}

remove_path() {
    local path="$1"
    local skip_confirm="${2:-false}"  # Optional parameter to skip confirmation

    if [[ ! -e "$path" ]]; then
        return 0
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        # Check if path is in cloud storage (in dry-run mode)
        if is_cloud_storage_path "$path"; then
            echo "  [DRY-RUN] Would move to Trash (WARNING - CLOUD STORAGE): $path"
        else
            echo "  [DRY-RUN] Would move to Trash: $path"
        fi
        return 0
    fi

    # Check if path is in cloud storage and warn user
    local cloud_warning=false
    if is_cloud_storage_path "$path"; then
        echo ""
        log_error "⚠️  CLOUD STORAGE WARNING ⚠️"
        log_error "Path: $path"
        log_error "This is in cloud storage (iCloud, Google Drive, OneDrive, Dropbox, Box, etc.)"
        log_error "Removing this could DELETE files from your cloud!"
        echo ""
        cloud_warning=true
    fi

    # Prompt for each path individually (with extra warning for cloud storage)
    if [[ "$skip_confirm" != "true" ]]; then
        if [[ "$cloud_warning" == "true" ]]; then
            log_warning "Are you ABSOLUTELY SURE you want to remove this cloud storage path?"
            if ! confirm "Move to Trash (CLOUD STORAGE): $path?"; then
                log_info "Skipped cloud storage path: $path"
                return 1
            fi
        else
            if ! confirm "Move to Trash: $path?"; then
                log_info "Skipped: $path"
                return 1
            fi
        fi
    fi

    if [[ "$VERBOSE" == "true" ]]; then
        log_info "Moving to Trash: $path"
    fi

    # Generate unique name for trash to avoid conflicts
    local basename_path=$(basename "$path")
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local trash_name="${basename_path}_${timestamp}"
    local trash_path="${HOME}/.Trash/${trash_name}"

    # Try moving to Trash without sudo first
    if mv "$path" "$trash_path" 2>/dev/null; then
        # Verify move succeeded
        if [[ ! -e "$path" && -e "$trash_path" ]]; then
            log_success "Moved to Trash: $path"
            return 0
        fi
    fi

    # Failed - prompt before trying with sudo
    log_warning "Failed to move to Trash without sudo: $path"
    echo ""
    log_warning "This file requires elevated privileges (sudo) to remove."

    if ! confirm "Use sudo to move to Trash: $path?"; then
        log_error "Cannot remove: $path (permission denied, sudo declined)"
        log_error "Removal failed. Exiting script."
        exit 1
    fi

    log_info "Attempting to move to Trash with sudo..."

    if sudo mv "$path" "$trash_path" 2>/dev/null; then
        # Verify move succeeded
        if [[ ! -e "$path" && -e "$trash_path" ]]; then
            log_success "Moved to Trash with sudo: $path"
            # Fix ownership so user can empty trash
            sudo chown -R "$(whoami)" "$trash_path" 2>/dev/null
            return 0
        fi
    fi

    # Still exists - move failed, try permanent deletion as last resort
    log_warning "Could not move to Trash. Attempting permanent deletion..."

    if sudo rm -rf "$path" 2>/dev/null; then
        if [[ ! -e "$path" ]]; then
            log_success "Permanently deleted: $path"
            return 0
        fi
    fi

    # Still exists - removal failed
    if [[ -e "$path" ]]; then
        log_error "FAILED to remove: $path"
        log_error "Removal failed even with sudo. Exiting script."
        exit 1
    fi

    return 0
}

find_and_list_files() {
    local search_pattern="$1"
    local search_dir="$2"
    local description="$3"
    local found_files=()

    log_info "Searching for ${description}..."

    # Use more specific patterns to avoid false positives
    # Only match files/dirs that start with the pattern or have it as a complete word
    while IFS= read -r file; do
        # Skip cloud storage files
        if is_cloud_storage_path "$file"; then
            continue
        fi

        local basename_file=$(basename "$file")
        # Check if pattern matches at word boundaries to avoid false positives
        # For "Box", match "Box", "Box.app", "Box Helper" but not "Mailbox", "Xbox", "Sandbox"
        if [[ "$basename_file" =~ ^${search_pattern}[^a-z] ]] || \
           [[ "$basename_file" =~ ^${search_pattern}$ ]] || \
           [[ "$basename_file" =~ [^a-zA-Z]${search_pattern}[^a-z] ]] || \
           [[ "$basename_file" =~ [^a-zA-Z]${search_pattern}$ ]]; then
            found_files+=("$file")
            echo "  - $file"
        fi
    done < <(find "$search_dir" -iname "*${search_pattern}*" 2>/dev/null)

    return "${#found_files[@]}"
}

is_system_process() {
    local proc_name="$1"

    # System processes to exclude (common macOS system processes)
    local system_procs=(
        "sandboxd"
        "kernel_task"
        "launchd"
        "syslogd"
        "cfprefsd"
        "loginwindow"
        "WindowServer"
        "systemstats"
    )

    for sys_proc in "${system_procs[@]}"; do
        if [[ "$proc_name" == "$sys_proc" ]]; then
            return 0  # true - is system process
        fi
    done

    return 1  # false - not system process
}

quit_application() {
    local app_name="$1"
    local bundle_id="$2"

    log_info "Checking for running processes..."

    # Find all related processes using multiple methods
    # Use bash 3.2 compatible arrays (no associative arrays)
    local process_list=()  # Array of "PID|process_name|full_command"
    local parent_pids=()

    # Method 1: Search by app name (catches "Box", "Box Helper", "Box Finder Extension")
    # Use exact word matching or starts-with to avoid false positives like "sandboxd"
    while IFS= read -r line; do
        local pid=$(echo "$line" | awk '{print $1}')
        local proc_name=$(echo "$line" | awk '{$1=""; print $0}' | xargs)

        # Filter out system processes and processes that don't really match
        if [[ -n "$pid" && -n "$proc_name" ]]; then
            # Check if it's a real match (starts with app name or is exact word)
            if [[ "$proc_name" =~ ^${app_name} ]] || [[ "$proc_name" =~ [[:space:]]${app_name}[[:space:]] ]] || [[ "$proc_name" == "$app_name" ]]; then
                # Exclude system processes
                if ! is_system_process "$proc_name"; then
                    local full_cmd=$(ps -p "$pid" -o command= 2>/dev/null | head -c 100)
                    process_list+=("$pid|$proc_name|$full_cmd")
                    parent_pids+=("$pid")
                fi
            fi
        fi
    done < <(pgrep -l -i "$app_name" 2>/dev/null)

    # Method 2: Search by bundle ID (more specific)
    if [[ -n "$bundle_id" ]]; then
        while IFS= read -r line; do
            local pid=$(echo "$line" | awk '{print $1}')
            local proc_name=$(echo "$line" | awk '{$1=""; print $0}' | xargs)
            if [[ -n "$pid" && -n "$proc_name" ]]; then
                # Check if already in list
                local already_added=false
                for existing in "${process_list[@]}"; do
                    local existing_pid=$(echo "$existing" | cut -d'|' -f1)
                    if [[ "$existing_pid" == "$pid" ]]; then
                        already_added=true
                        break
                    fi
                done

                if [[ "$already_added" == "false" ]]; then
                    local full_cmd=$(ps -p "$pid" -o command= 2>/dev/null | head -c 100)
                    process_list+=("$pid|$proc_name|$full_cmd")
                    parent_pids+=("$pid")
                fi
            fi
        done < <(pgrep -l -i "$bundle_id" 2>/dev/null)
    fi

    # Method 3: Find child processes of any parent we found
    # Only proceed if we have parent processes
    if [[ ${#parent_pids[@]} -gt 0 ]]; then
        local found_children=true
        while [[ "$found_children" == "true" ]]; do
            found_children=false
            # Iterate safely over array
            local i
            for i in "${!parent_pids[@]}"; do
                local parent_pid="${parent_pids[$i]}"
                # Find children of this parent
                while IFS= read -r child_pid; do
                    if [[ -n "$child_pid" ]]; then
                        # Check if already in list
                        local already_added=false
                        if [[ ${#process_list[@]} -gt 0 ]]; then
                            for existing in "${process_list[@]}"; do
                                local existing_pid=$(echo "$existing" | cut -d'|' -f1)
                                if [[ "$existing_pid" == "$child_pid" ]]; then
                                    already_added=true
                                    break
                                fi
                            done
                        fi

                        if [[ "$already_added" == "false" ]]; then
                            local proc_name=$(ps -p "$child_pid" -o comm= 2>/dev/null)
                            local full_cmd=$(ps -p "$child_pid" -o command= 2>/dev/null | head -c 100)
                            if [[ -n "$proc_name" ]]; then
                                process_list+=("$child_pid|$proc_name|$full_cmd")
                                parent_pids+=("$child_pid")
                                found_children=true
                            fi
                        fi
                    fi
                done < <(pgrep -P "$parent_pid" 2>/dev/null)
            done
        done
    fi

    if [[ ${#process_list[@]} -eq 0 ]]; then
        log_info "No running processes found"
        return 0
    fi

    # List all found processes with details
    log_warning "Found ${#process_list[@]} running process(es):"
    if [[ ${#process_list[@]} -gt 0 ]]; then
        for proc_info in "${process_list[@]}"; do
            local pid=$(echo "$proc_info" | cut -d'|' -f1)
            local proc_name=$(echo "$proc_info" | cut -d'|' -f2)
            local proc_cmd=$(echo "$proc_info" | cut -d'|' -f3)
            echo "  [PID $pid] $proc_name"
            if [[ "$VERBOSE" == "true" && -n "$proc_cmd" ]]; then
                echo "      Command: $proc_cmd"
            fi
        done
    fi
    echo ""

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "  [DRY-RUN] Would prompt to quit ${#process_list[@]} process(es)"
        return 0
    fi

    # Kill each process with individual prompts
    local killed=0
    local skipped=0
    if [[ ${#process_list[@]} -gt 0 ]]; then
        for proc_info in "${process_list[@]}"; do
            local pid=$(echo "$proc_info" | cut -d'|' -f1)
            local proc_name=$(echo "$proc_info" | cut -d'|' -f2)

            # Prompt for each process individually
            if ! confirm "Terminate [PID $pid] $proc_name?"; then
                log_info "Skipped [PID $pid] $proc_name"
                ((skipped++))
                continue
            fi

            log_info "Terminating [PID $pid] $proc_name..."

            # Try graceful termination first (SIGTERM)
            if kill -TERM "$pid" 2>/dev/null; then
                # Wait up to 3 seconds for process to exit
                local wait_count=0
                while [[ $wait_count -lt 6 ]]; do
                    if ! kill -0 "$pid" 2>/dev/null; then
                        log_success "Terminated [PID $pid] $proc_name"
                        ((killed++))
                        break
                    fi
                    sleep 0.5
                    ((wait_count++))
                done

                # Force kill if still running
                if kill -0 "$pid" 2>/dev/null; then
                    log_warning "Process still running. Force kill [PID $pid] $proc_name?"
                    if confirm "Force kill (SIGKILL)?"; then
                        if kill -9 "$pid" 2>/dev/null; then
                            sleep 0.5
                            if ! kill -0 "$pid" 2>/dev/null; then
                                log_success "Force killed [PID $pid] $proc_name"
                                ((killed++))
                            else
                                log_error "Failed to kill [PID $pid] $proc_name"
                            fi
                        fi
                    else
                        log_warning "Process [PID $pid] left running"
                        ((skipped++))
                    fi
                fi
            else
                log_warning "Process [PID $pid] already terminated or permission denied"
            fi
        done
    fi

    if [[ $killed -gt 0 ]]; then
        log_success "Terminated $killed process(es)"
    fi
    if [[ $skipped -gt 0 ]]; then
        log_warning "Skipped $skipped process(es) - may need manual cleanup"
    fi
}

remove_main_application() {
    local app_name="$1"
    local removed=0
    local paths_to_remove=()

    # Check standard locations
    for app_path in "/Applications/${app_name}.app" "${HOME}/Applications/${app_name}.app"; do
        if [[ -e "$app_path" ]]; then
            paths_to_remove+=("$app_path")
        fi
    done

    if [[ ${#paths_to_remove[@]} -eq 0 ]]; then
        log_info "No main application found"
        return 0
    fi

    log_info "Removing main application (${#paths_to_remove[@]} location(s))..."
    echo ""

    for path in "${paths_to_remove[@]}"; do
        remove_path "$path" && ((removed++))
    done

    if [[ $removed -gt 0 ]]; then
        echo ""
        log_success "Removed main application ($removed location(s))"
    fi
}

remove_support_files() {
    local app_name="$1"
    local bundle_id="$2"
    local paths_to_remove=()

    # Collect all paths
    # Application Support
    [[ -e "${HOME}/Library/Application Support/${app_name}" ]] && \
        paths_to_remove+=("${HOME}/Library/Application Support/${app_name}")
    [[ -e "/Library/Application Support/${app_name}" ]] && \
        paths_to_remove+=("/Library/Application Support/${app_name}")

    # Preferences
    if [[ -n "$bundle_id" ]]; then
        [[ -e "${HOME}/Library/Preferences/${bundle_id}.plist" ]] && \
            paths_to_remove+=("${HOME}/Library/Preferences/${bundle_id}.plist")
        for pref in "${HOME}/Library/Preferences/${bundle_id}".*; do
            [[ -e "$pref" ]] && paths_to_remove+=("$pref")
        done
    fi
    [[ -e "${HOME}/Library/Preferences/${app_name}.plist" ]] && \
        paths_to_remove+=("${HOME}/Library/Preferences/${app_name}.plist")

    # Caches
    if [[ -n "$bundle_id" ]]; then
        [[ -e "${HOME}/Library/Caches/${bundle_id}" ]] && \
            paths_to_remove+=("${HOME}/Library/Caches/${bundle_id}")
    fi
    [[ -e "${HOME}/Library/Caches/${app_name}" ]] && \
        paths_to_remove+=("${HOME}/Library/Caches/${app_name}")

    # Saved Application State
    if [[ -n "$bundle_id" ]]; then
        [[ -e "${HOME}/Library/Saved Application State/${bundle_id}.savedState" ]] && \
            paths_to_remove+=("${HOME}/Library/Saved Application State/${bundle_id}.savedState")
    fi

    # Containers (sandboxed apps)
    if [[ -n "$bundle_id" ]]; then
        [[ -e "${HOME}/Library/Containers/${bundle_id}" ]] && \
            paths_to_remove+=("${HOME}/Library/Containers/${bundle_id}")
        for container in "${HOME}/Library/Containers/${bundle_id}".*; do
            [[ -e "$container" ]] && paths_to_remove+=("$container")
        done
        for group_container in "${HOME}/Library/Group Containers/${bundle_id}"*; do
            [[ -e "$group_container" ]] && paths_to_remove+=("$group_container")
        done
    fi

    # Application Scripts
    if [[ -n "$bundle_id" ]]; then
        for script_dir in "${HOME}/Library/Application Scripts/${bundle_id}"*; do
            [[ -e "$script_dir" ]] && paths_to_remove+=("$script_dir")
        done
    fi

    # Logs
    [[ -e "${HOME}/Library/Logs/${app_name}" ]] && \
        paths_to_remove+=("${HOME}/Library/Logs/${app_name}")
    [[ -e "/Library/Logs/${app_name}" ]] && \
        paths_to_remove+=("/Library/Logs/${app_name}")

    if [[ ${#paths_to_remove[@]} -eq 0 ]]; then
        log_info "No support files found"
        return 0
    fi

    log_info "Removing support files (${#paths_to_remove[@]} items)..."
    echo ""

    local removed=0
    for path in "${paths_to_remove[@]}"; do
        remove_path "$path" && ((removed++))
    done

    if [[ $removed -gt 0 ]]; then
        echo ""
        log_success "Removed $removed support file(s)"
    fi
}

unload_launch_agents() {
    local app_name="$1"
    local bundle_id="$2"

    log_info "Unloading launch agents to prevent auto-restart..."

    local patterns=("$app_name")
    [[ -n "$bundle_id" ]] && patterns+=("$bundle_id")

    local unloaded=0

    # Unload user launch agents
    for pattern in "${patterns[@]}"; do
        for agent in "${HOME}/Library/LaunchAgents/"*"${pattern}"*; do
            if [[ -e "$agent" ]]; then
                local agent_name=$(basename "$agent" .plist)
                if [[ "$DRY_RUN" == "true" ]]; then
                    echo "  [DRY-RUN] Would unload: $agent_name"
                else
                    if launchctl unload "$agent" 2>/dev/null; then
                        log_info "Unloaded: $agent_name"
                        ((unloaded++))
                    else
                        # Try without path
                        launchctl remove "$agent_name" 2>/dev/null || true
                    fi
                fi
            fi
        done
    done

    # Unload system launch agents/daemons (requires sudo)
    for pattern in "${patterns[@]}"; do
        for daemon in /Library/LaunchDaemons/*"${pattern}"* /Library/LaunchAgents/*"${pattern}"*; do
            if [[ -e "$daemon" ]]; then
                local daemon_name=$(basename "$daemon" .plist)
                if [[ "$DRY_RUN" == "true" ]]; then
                    echo "  [DRY-RUN] Would unload (with sudo): $daemon_name"
                else
                    log_info "Unloading system daemon: $daemon_name (may require sudo)"
                    sudo launchctl unload "$daemon" 2>/dev/null || \
                    sudo launchctl remove "$daemon_name" 2>/dev/null || true
                    ((unloaded++))
                fi
            fi
        done
    done

    if [[ $unloaded -gt 0 ]]; then
        log_success "Unloaded $unloaded launch agent(s)/daemon(s)"
        sleep 1  # Give system time to stop services
    else
        log_info "No launch agents to unload"
    fi
}

remove_launch_agents() {
    local app_name="$1"
    local bundle_id="$2"
    local agents_to_remove=()
    local system_daemons=()

    local patterns=("$app_name")
    [[ -n "$bundle_id" ]] && patterns+=("$bundle_id")

    # Collect user launch agents
    for pattern in "${patterns[@]}"; do
        for agent in "${HOME}/Library/LaunchAgents/"*"${pattern}"*; do
            if [[ -e "$agent" ]]; then
                agents_to_remove+=("$agent")
            fi
        done
    done

    # Collect system launch agents/daemons
    for pattern in "${patterns[@]}"; do
        for daemon in /Library/LaunchDaemons/*"${pattern}"* /Library/LaunchAgents/*"${pattern}"*; do
            if [[ -e "$daemon" ]]; then
                system_daemons+=("$daemon")
            fi
        done
    done

    # Handle user launch agents
    if [[ ${#agents_to_remove[@]} -gt 0 ]]; then
        log_info "Removing launch agent files (${#agents_to_remove[@]} items)..."
        echo ""

        local removed=0
        for agent in "${agents_to_remove[@]}"; do
            remove_path "$agent" && ((removed++))
        done
        if [[ $removed -gt 0 ]]; then
            echo ""
            log_success "Removed $removed launch agent file(s)"
        fi
    else
        log_info "No user launch agent files found"
    fi

    # Handle system daemons
    if [[ ${#system_daemons[@]} -gt 0 ]]; then
        log_info "Removing system daemon files (${#system_daemons[@]} items)..."
        echo ""

        local removed=0
        for daemon in "${system_daemons[@]}"; do
            remove_path "$daemon" && ((removed++))
        done
        if [[ $removed -gt 0 ]]; then
            echo ""
            log_success "Removed $removed system daemon file(s)"
        fi
    fi
}

remove_receipts() {
    local app_name="$1"
    local bundle_id="$2"

    log_info "Checking package receipts..."

    local patterns=("$app_name")
    [[ -n "$bundle_id" ]] && patterns+=("$bundle_id")

    local found_receipts=false
    for pattern in "${patterns[@]}"; do
        while IFS= read -r pkg; do
            found_receipts=true
            echo "  - $pkg"

            if [[ "$DRY_RUN" != "true" ]]; then
                if confirm "Remove receipt: $pkg?"; then
                    sudo pkgutil --forget "$pkg" 2>/dev/null && log_success "Removed receipt: $pkg"
                fi
            else
                echo "  [DRY-RUN] Would remove receipt: $pkg"
            fi
        done < <(pkgutil --pkgs 2>/dev/null | grep -i "$pattern")
    done

    if [[ "$found_receipts" == "false" ]]; then
        log_info "No package receipts found"
    fi
}

search_remaining_files() {
    local app_name="$1"
    local bundle_id="$2"

    log_info "Searching for remaining files..."

    local patterns=("$app_name")
    [[ -n "$bundle_id" ]] && patterns+=("$bundle_id")

    local remaining_files=()

    # Collect all remaining files
    for pattern in "${patterns[@]}"; do
        while IFS= read -r file; do
            # Skip cloud storage files
            if is_cloud_storage_path "$file"; then
                continue
            fi

            local basename_file=$(basename "$file")
            # Check if pattern matches at word boundaries to avoid false positives
            if [[ "$basename_file" =~ ^${pattern}[^a-z] ]] || \
               [[ "$basename_file" =~ ^${pattern}$ ]] || \
               [[ "$basename_file" =~ [^a-zA-Z]${pattern}[^a-z] ]] || \
               [[ "$basename_file" =~ [^a-zA-Z]${pattern}$ ]]; then
                remaining_files+=("$file")
            fi
        done < <(find "$HOME/Library" -iname "*${pattern}*" 2>/dev/null)
    done

    if [[ ${#remaining_files[@]} -eq 0 ]]; then
        log_success "No remaining files found"
        return 0
    fi

    log_warning "Found ${#remaining_files[@]} remaining file(s):"
    if [[ ${#remaining_files[@]} -gt 0 ]]; then
        for file in "${remaining_files[@]}"; do
            echo "  - $file"
        done
    fi
    echo ""

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Run without --dry-run to review and remove these files individually"
        return 0
    fi

    # Prompt to handle remaining files
    log_info "These files may be related to the application."
    if ! confirm "Do you want to review these files for removal?"; then
        log_info "Skipped remaining files"
        return 0
    fi

    # Prompt for each file individually
    local removed=0
    local skipped=0
    echo ""
    if [[ ${#remaining_files[@]} -gt 0 ]]; then
        for file in "${remaining_files[@]}"; do
            remove_path "$file" && ((removed++)) || ((skipped++))
        done
    fi

    echo ""
    if [[ $removed -gt 0 ]]; then
        log_success "Removed $removed remaining file(s)"
    fi
    if [[ $skipped -gt 0 ]]; then
        log_info "Skipped $skipped remaining file(s)"
    fi
}

detect_bundle_id() {
    local app_name="$1"

    for app_path in "/Applications/${app_name}.app" "${HOME}/Applications/${app_name}.app"; do
        if [[ -e "$app_path" ]]; then
            local detected_id=$(defaults read "${app_path}/Contents/Info.plist" CFBundleIdentifier 2>/dev/null)
            if [[ -n "$detected_id" ]]; then
                echo "$detected_id"
                return 0
            fi
        fi
    done

    return 1
}

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -y|--yes)
                SKIP_CONFIRM=true
                shift
                ;;
            -b|--bundle-id)
                BUNDLE_ID="$2"
                shift 2
                ;;
            -h|--help)
                usage
                ;;
            *)
                APP_NAME="$1"
                shift
                ;;
        esac
    done

    if [[ -z "$APP_NAME" ]]; then
        log_error "Application name is required"
        usage
    fi

    # Header
    echo ""
    echo "=========================================="
    echo "  macOS Application Removal Tool"
    echo "=========================================="
    echo ""
    echo "Application: $APP_NAME"
    [[ "$DRY_RUN" == "true" ]] && echo "Mode: DRY RUN (no files will be removed)"
    echo ""

    # Try to detect bundle ID if not provided
    if [[ -z "$BUNDLE_ID" ]]; then
        log_info "Attempting to detect bundle ID..."
        if BUNDLE_ID=$(detect_bundle_id "$APP_NAME"); then
            log_success "Detected bundle ID: $BUNDLE_ID"
        else
            log_warning "Could not detect bundle ID. Removal may be incomplete."
        fi
    fi

    # For non-dry-run, show preview first
    if [[ "$DRY_RUN" != "true" ]]; then
        echo ""
        log_info "Scanning for files to remove..."
        echo ""

        # Show what will be removed
        echo "The following will be removed:"
        echo ""

        local item_count=0

        # Check main app
        for app_path in "/Applications/${APP_NAME}.app" "${HOME}/Applications/${APP_NAME}.app"; do
            if [[ -e "$app_path" ]]; then
                echo "  [APP] $app_path"
                ((item_count++))
            fi
        done

        # Check support files
        if [[ -e "${HOME}/Library/Application Support/${APP_NAME}" ]]; then
            echo "  [SUPPORT] ${HOME}/Library/Application Support/${APP_NAME}"
            ((item_count++))
        fi
        if [[ -e "/Library/Application Support/${APP_NAME}" ]]; then
            echo "  [SUPPORT] /Library/Application Support/${APP_NAME}"
            ((item_count++))
        fi

        # Check preferences
        if [[ -n "$BUNDLE_ID" ]]; then
            for pref in "${HOME}/Library/Preferences/${BUNDLE_ID}"*; do
                if [[ -e "$pref" ]]; then
                    echo "  [PREFS] $pref"
                    ((item_count++))
                fi
            done
        fi
        for pref in "${HOME}/Library/Preferences/${APP_NAME}"*; do
            if [[ -e "$pref" ]]; then
                echo "  [PREFS] $pref"
                ((item_count++))
            fi
        done

        # Check caches
        if [[ -e "${HOME}/Library/Caches/${APP_NAME}" ]]; then
            echo "  [CACHE] ${HOME}/Library/Caches/${APP_NAME}"
            ((item_count++))
        fi
        if [[ -n "$BUNDLE_ID" ]]; then
            if [[ -e "${HOME}/Library/Caches/${BUNDLE_ID}" ]]; then
                echo "  [CACHE] ${HOME}/Library/Caches/${BUNDLE_ID}"
                ((item_count++))
            fi
        fi

        # Check saved application state
        if [[ -n "$BUNDLE_ID" ]]; then
            if [[ -e "${HOME}/Library/Saved Application State/${BUNDLE_ID}.savedState" ]]; then
                echo "  [STATE] ${HOME}/Library/Saved Application State/${BUNDLE_ID}.savedState"
                ((item_count++))
            fi
        fi

        # Check containers
        if [[ -n "$BUNDLE_ID" ]]; then
            if [[ -e "${HOME}/Library/Containers/${BUNDLE_ID}" ]]; then
                echo "  [CONTAINER] ${HOME}/Library/Containers/${BUNDLE_ID}"
                ((item_count++))
            fi
            for container in "${HOME}/Library/Containers/${BUNDLE_ID}".*; do
                if [[ -e "$container" ]]; then
                    echo "  [CONTAINER] $container"
                    ((item_count++))
                fi
            done
            for group_container in "${HOME}/Library/Group Containers/${BUNDLE_ID}"*; do
                if [[ -e "$group_container" ]]; then
                    echo "  [GROUP CONTAINER] $group_container"
                    ((item_count++))
                fi
            done
        fi

        # Check application scripts
        if [[ -n "$BUNDLE_ID" ]]; then
            for script_dir in "${HOME}/Library/Application Scripts/${BUNDLE_ID}"*; do
                if [[ -e "$script_dir" ]]; then
                    echo "  [SCRIPT] $script_dir"
                    ((item_count++))
                fi
            done
        fi

        # Check logs
        if [[ -e "${HOME}/Library/Logs/${APP_NAME}" ]]; then
            echo "  [LOGS] ${HOME}/Library/Logs/${APP_NAME}"
            ((item_count++))
        fi
        if [[ -e "/Library/Logs/${APP_NAME}" ]]; then
            echo "  [LOGS] /Library/Logs/${APP_NAME}"
            ((item_count++))
        fi

        # Check launch agents (user)
        for agent in "${HOME}/Library/LaunchAgents/"*"${APP_NAME}"*; do
            if [[ -e "$agent" ]]; then
                echo "  [LAUNCH AGENT] $agent"
                ((item_count++))
            fi
        done
        if [[ -n "$BUNDLE_ID" ]]; then
            for agent in "${HOME}/Library/LaunchAgents/"*"${BUNDLE_ID}"*; do
                if [[ -e "$agent" ]]; then
                    echo "  [LAUNCH AGENT] $agent"
                    ((item_count++))
                fi
            done
        fi

        # Check system launch agents/daemons (won't be removed without sudo)
        local system_daemon_count=0
        for daemon in /Library/LaunchDaemons/*"${APP_NAME}"* /Library/LaunchAgents/*"${APP_NAME}"*; do
            if [[ -e "$daemon" ]]; then
                echo "  [SYSTEM DAEMON - requires sudo] $daemon"
                ((system_daemon_count++))
            fi
        done
        if [[ -n "$BUNDLE_ID" ]]; then
            for daemon in /Library/LaunchDaemons/*"${BUNDLE_ID}"* /Library/LaunchAgents/*"${BUNDLE_ID}"*; do
                if [[ -e "$daemon" ]]; then
                    echo "  [SYSTEM DAEMON - requires sudo] $daemon"
                    ((system_daemon_count++))
                fi
            done
        fi

        # Check package receipts
        local receipt_count=0
        while IFS= read -r pkg; do
            ((receipt_count++))
        done < <(pkgutil --pkgs 2>/dev/null | grep -i "${APP_NAME}")
        if [[ -n "$BUNDLE_ID" ]]; then
            while IFS= read -r pkg; do
                ((receipt_count++))
            done < <(pkgutil --pkgs 2>/dev/null | grep -i "${BUNDLE_ID}")
        fi
        if [[ $receipt_count -gt 0 ]]; then
            echo "  [RECEIPTS] $receipt_count package receipt(s) - will prompt individually"
            ((item_count++))
        fi

        echo ""
        if [[ $system_daemon_count -gt 0 ]]; then
            log_warning "Note: System daemons require 'sudo' to remove"
        fi
        log_warning "Total items to remove: $item_count"
        log_warning "This action cannot be undone!"
        echo ""

        # Confirm before proceeding
        if ! confirm "Do you want to proceed with removal?"; then
            log_info "Cancelled by user"
            exit 0
        fi
    fi

    echo ""

    # Execute removal steps in correct order:
    # 1. Unload launch agents first to prevent auto-restart
    # 2. Kill running processes (they won't restart now)
    # 3. Remove application and files
    # 4. Remove launch agent files
    # 5. Remove package receipts

    unload_launch_agents "$APP_NAME" "$BUNDLE_ID"
    echo ""

    quit_application "$APP_NAME" "$BUNDLE_ID"
    echo ""

    remove_main_application "$APP_NAME"
    echo ""

    remove_support_files "$APP_NAME" "$BUNDLE_ID"
    echo ""

    remove_launch_agents "$APP_NAME" "$BUNDLE_ID"
    echo ""

    remove_receipts "$APP_NAME" "$BUNDLE_ID"
    echo ""

    search_remaining_files "$APP_NAME" "$BUNDLE_ID"
    echo ""

    # Summary
    echo "=========================================="
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry run complete. Run without --dry-run to remove files."
    else
        log_success "Application removal complete!"
        echo ""
        log_info "Files have been moved to Trash (~/.Trash/)"
        log_info "To permanently delete:"
        echo "  1. Open Finder"
        echo "  2. Empty Trash (Cmd+Shift+Delete)"
        echo ""
        log_info "Or restore files from Trash if you change your mind!"
        echo ""
        log_info "You may want to restart your Mac after emptying Trash."
    fi
    echo "=========================================="
    echo ""
}

main "$@"
