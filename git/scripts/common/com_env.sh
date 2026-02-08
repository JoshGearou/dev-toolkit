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
project_root="$(dirname "$(dirname "$(dirname "$(realpath "${BASH_SOURCE[0]}")")")")"
project_lib_sh="${project_root}/scripts/common/com_lib.sh"
source_required_file "${project_lib_sh}"

# Source global functions and variables
REPO_ROOT=$(get_git_root)
repo_env_sh="${repo_root}/bash/common/repo_env.sh"
source_required_file $repo_env_sh

# Local variables
script_dir=$(dirname "$(realpath "${BASH_SOURCE[0]}")")
script_name=$(basename "$(realpath "${BASH_SOURCE[0]}")")
log_file="${script_dir}/${script_name}.log"
