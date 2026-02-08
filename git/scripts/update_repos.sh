#!/bin/bash
set -u

print_help() {
    cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --gc                         Run garbage collection on each repository.
  -g, --generate-config [FILE] Generate a configuration file with repository information.
                               Default output file is 'git_repos_config.csv' in the script directory.
  -l, --list-repos             Print the list of repositories from the configuration file to stdout.
  -a, --add-repos [FILE]       Clone repositories listed in [FILE]. Defaults to configuration file if not provided.
  -h, --help                   Display this help message and exit.

Description:
  This script updates Git repositories in the specified search directory, optionally
  generating a configuration file with repository details, running garbage collection,
  listing repositories from the configuration file, or cloning repositories that haven't
  been cloned yet.
EOF
    exit 0
}

source_required_file() {
    local filepath="$1"
    local prefix
    prefix="$(date '+%Y.%m.%d:%H:%M:%S') - "

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

list_repos() {
    if [[ ! -f "$config_file" ]]; then
        echo "Error: Configuration file '$config_file' not found." >&2
        exit 1
    fi

    echo "List of repositories from configuration file:"
    tail -n +2 "$config_file" | while IFS=',' read -r dir repo_name remote_url; do
        echo "Directory: ${dir//\"/}, Repo Name: ${repo_name//\"/}, Remote URL: ${remote_url//\"/}"
    done
    exit 0
}

process_repo() {
    local dir="$1"
    log_message "${SEPARATOR_LONG}"
    log_message "Updating repository: $dir"
    log_message "${SEPARATOR_LONG}"

    cd "$dir" || return
    REMOTE_URL=$(git config --get remote.origin.url || echo "no remote")
    log_message "${dir} :: remote: ${REMOTE_URL}"

    if [[ "$GENERATE_CONFIG" != true ]]; then
        CURRENT_BRANCH=$(git symbolic-ref --short HEAD || echo "detached")
        log_message "${dir} :: branch: ${CURRENT_BRANCH}"
        run_command_with_retry "git fetch --all --prune" false true

        if git ls-remote --exit-code --heads origin "${CURRENT_BRANCH}" >/dev/null 2>&1; then
            run_command_with_retry "git pull --rebase" false true
        else
            log_message "${dir} :: no remote branch found for: '${CURRENT_BRANCH}', skipping pull."
        fi
    fi

    if [[ "$GENERATE_CONFIG" == true ]]; then
        if [[ "$REMOTE_URL" == "no remote" ]]; then
            log_message "Skipping repository $dir as no remote is configured."
        else
            # Normalize the directory by stripping $HOME and prepending '~'
            normalized_dir="~${dir#$HOME}"
            # Extract repository name from the remote URL
            repo_name=$(basename "$REMOTE_URL")
            repo_name="${repo_name%.git}"
            csv_data+=("\"$normalized_dir\",\"$repo_name\",\"$REMOTE_URL\"")
        fi
    fi

    if [[ "$RUN_GC" == true ]]; then
        run_command_with_retry "git gc" false true
    fi

    cd - > /dev/null
}

main() {
    # Define variables
    script_dir=$(dirname "$(realpath "${BASH_SOURCE[0]}")")
    script_name=$(basename "$(realpath "${BASH_SOURCE[0]}")")
    log_file="${script_dir}/${script_name}.log"
    config_file="${script_dir}/git_repos_config.csv"
    RUN_GC=false
    GENERATE_CONFIG=false
    ADD_REPOS=false
    repos_file=""
    
    # Declare CSV data array explicitly
    declare -a csv_data=()

    # Option parsing
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --gc)
                RUN_GC=true
                shift
                ;;
            --generate-config|-g)
                GENERATE_CONFIG=true
                shift
                if [[ -n "${1:-}" && "${1:0:1}" != "-" ]]; then
                    config_file="$1"
                    shift
                fi
                ;;
            --list-repos|-l)
                list_repos
                ;;
            --add-repos|-a)
                ADD_REPOS=true
                shift
                if [[ -n "${1:-}" && "${1:0:1}" != "-" ]]; then
                    repos_file="$1"
                    shift
                else
                    repos_file="$config_file"
                fi
                ;;
            --help|-h)
                print_help
                ;;
            *)
                echo "Unknown parameter: $1" >&2
                print_help
                ;;
        esac
    done

    run_command_with_retry "git --version"

    if [[ -z "${SEARCH_DIR:-}" ]]; then
        REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
        if [[ -n "$REPO_ROOT" ]]; then
            SEARCH_DIR=$(dirname "$(dirname "$REPO_ROOT")")
        else
            log_message "Not in a Git repository, and no directory provided."
            exit 1
        fi
    fi

    # If not in add-repos mode, update repositories in the search directory
    if [[ "$ADD_REPOS" != true ]]; then
        for dir in "$SEARCH_DIR"/*; do
            if [[ -d "$dir/.git" ]]; then
                process_repo "$dir"
            elif [[ -d "$dir" ]]; then
                for subdir in "$dir"/*; do
                    if [[ -d "$subdir/.git" ]]; then
                        process_repo "$subdir"
                    fi
                done
            fi
        done
    fi

    # If --add-repos is enabled, process additional repositories from the file.
    # Only clone repositories that are not already present; do not update existing ones.
    if [[ "$ADD_REPOS" == true ]]; then
        if [[ ! -f "$repos_file" ]]; then
            log_message "Repository file '$repos_file' not found." >&2
            exit 1
        fi

        echo "Processing additional repositories from configuration file: $repos_file" >&2
        tail -n +2 "$repos_file" | while IFS=',' read -r dir repo_name remote_url; do
            # Remove quotes from fields
            dir="${dir//\"/}"
            repo_name="${repo_name//\"/}"
            remote_url="${remote_url//\"/}"
            expanded_dir="${dir/#\~/$HOME}"
            if [[ -d "$expanded_dir" ]]; then
                log_message "Repository already cloned: $dir; skipping clone."
            else
                log_message "Repository not found: $dir. Attempting mint clone."
                if ! mint clone "$repo_name" --destination "$expanded_dir"; then
                    log_message "mint clone failed for $dir, trying git clone."
                    git clone "$remote_url" "$expanded_dir" || log_message "git clone failed for $dir"
                fi
            fi
        done
    fi

    # If generating the config, write out the CSV file with a single header definition
    if [[ "$GENERATE_CONFIG" == true ]]; then
        local header="\"directory\",\"repo_name\",\"remote_url\""
        new_entries=$(printf "%s\n" "${csv_data[@]}")
        if [[ -f "$config_file" ]]; then
            merged_entries=$( { printf "%s\n" "$new_entries"; tail -n +2 "$config_file"; } | sort -t',' -k1,1 -u )
        else
            merged_entries=$(printf "%s\n" "$new_entries" | sort -t',' -k1,1 -u )
        fi
        {
            echo "$header"
            printf "%s\n" "$merged_entries"
        } > "$config_file"
        log_message "Configuration file updated at: $config_file"
    fi

    log_message "All repositories have been processed."
}

# Determine project root and source required environment file
project_root="$(dirname "$(dirname "$(realpath "${BASH_SOURCE[0]}")")")"
project_env_sh="${project_root}/scripts/common/com_env.sh"
source_required_file "${project_env_sh}"

main "$@"
