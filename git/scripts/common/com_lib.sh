#!/bin/bash
set -u

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

# Function to get the Git repository root
get_git_root() {
    local repo_root
    if ! repo_root=$(git rev-parse --is-inside-work-tree &>/dev/null); then
        echo "Error: Not inside a Git repository." >&2
        exit 1
    fi
    git rev-parse --show-toplevel
}

repo_root=$(get_git_root)
repo_lib_sh="${repo_root}/bash/common/repo_lib.sh"
source_required_file "${repo_lib_sh}"

# Local variables
script_dir=$(dirname "$(realpath "${BASH_SOURCE[0]}")")
script_name=$(basename "$(realpath "${BASH_SOURCE[0]}")")
log_file="${script_dir}/${script_name}.log"