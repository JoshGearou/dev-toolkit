#!/bin/bash
set -u

# Function to check if a specified file exists and source it
source_required_file() {
    local filepath="$1"
    local prefix="$(date '+%Y.%m.%d:%H:%M:%S') - "

    if [[ "${DEBUG:-false}" == "true" ]]; then
        prefix+="${0}: ${BASH_SOURCE[1]}::${FUNCNAME[1]}::${BASH_LINENO[1]} - ${BASH_SOURCE[0]}::${FUNCNAME[0]}::${BASH_LINENO[0]} ->"
    fi

    echo "${prefix}sourcing ${filepath}" >&2

    if [[ -f "$filepath" ]]; then
        source "$filepath"
    else
        echo "${prefix} error: Required file $filepath not found." >&2
        exit 1
    fi
}

# Source project functions and variables
script_dir=$(dirname "$(realpath "${BASH_SOURCE[0]}")")
repo_lib_sh="${script_dir}/repo_lib.sh"
source_required_file "${repo_lib_sh}"

# Local variables
script_dir=$(dirname "$(realpath "${BASH_SOURCE[0]}")")
script_name=$(basename "$(realpath "${BASH_SOURCE[0]}")")
log_file="${script_dir}/${script_name}.log"

# Global variables
SEPARATOR_LONG=$(printf '=%.0s' {1..80})
REPO_ROOT=$(get_git_root)