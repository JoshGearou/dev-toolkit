#!/bin/bash
set -u

print_help() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --user <username>      Specify the username to search for authored or co-authored commits."
    echo "  --directory <path>     Specify the root directory to search for Git repositories."
    echo "  --full-message         Include the full commit message in the output."
    echo "  --show-diff            Show the diff for each commit."
    echo "  --limit <N>            Limit the output to the latest N commits matching the user."
    echo "  -h                     Display this help message and exit."
    echo
    exit 0
}

get_commits_by_user() {
    local username="$1"
    local git_dir="$2"
    local full_message="${3:-false}"
    local show_diff="${4:-false}"
    local limit="${5:-0}"

    if [[ -z "$username" || -z "$git_dir" ]]; then
        echo "Error: Both username and git directory must be specified." >&2
        exit 1
    fi

    # Ensure the path is a valid Git repository
    if ! git -C "$git_dir" rev-parse --is-inside-work-tree > /dev/null 2>&1; then
        echo "Error: $git_dir is not a valid Git repository." >&2
        exit 1
    fi

    # Adjust format string based on full-message flag
    local format
    if [[ "$full_message" == "true" ]]; then
        format="%H"
    else
        format="%H - %ae, %ar : %s"
    fi

    # Counter to enforce the limit
    local count=0

    # Extract commits matching the username
    git -C "$git_dir" --no-pager log --pretty=format:"$format" | while IFS= read -r line; do
        commit_hash=$(echo "$line" | awk '{print $1}')
        if [[ "$commit_hash" =~ ^[a-f0-9]+$ ]]; then
            # Check for matching username in the commit
            commit_details=$(git -C "$git_dir" --no-pager show -s --format="%ae %ce" "$commit_hash")
            if echo "$commit_details" | grep -qi "$username"; then
                if [[ "$limit" -gt 0 && "$count" -ge "$limit" ]]; then
                    break
                fi

                if [[ "$full_message" == "true" ]]; then
                    # Show full commit message
                    git -C "$git_dir" --no-pager show -s --format="Commit: %H%nAuthor: %an <%ae>%nDate: %ad%n%n%s%n%b" "$commit_hash"
                else
                    # Show short message
                    echo "$line"
                fi

                # Show diff if enabled
                if [[ "$show_diff" == "true" ]]; then
                    git -C "$git_dir" --no-pager show --stat --patch "$commit_hash"
                fi

                echo "---"

                # Increment the counter
                count=$((count + 1))
            fi
        fi
    done
}

user=""
search_dir="."
full_message="false"
show_diff="false"
limit="0"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --user|-u)
            if [[ -n "${2:-}" && ! "$2" =~ ^- ]]; then
                user="$2"
                shift 2
            else
                echo "Error: --user requires a username argument." >&2
                exit 1
            fi
            ;;
        --directory|-d)
            if [[ -n "${2:-}" && ! "$2" =~ ^- ]]; then
                search_dir="$2"
                shift 2
            else
                echo "Error: --directory requires a directory argument." >&2
                exit 1
            fi
            ;;
        --full-message|-f)
            full_message="true"
            shift
            ;;
        --show-diff|-s)
            show_diff="true"
            shift
            ;;
        --limit|-l)
            if [[ -n "${2:-}" && "$2" =~ ^[0-9]+$ ]]; then
                limit="$2"
                shift 2
            else
                echo "Error: --limit requires a numeric argument." >&2
                exit 1
            fi
            ;;
        -h|--help)
            print_help
            ;;
        *)
            echo "Unknown option: $1" >&2
            print_help
            ;;
    esac
done

if [[ -n "$user" ]]; then
    get_commits_by_user "$user" "$search_dir" "$full_message" "$show_diff" "$limit"
else
    echo "Error: --user <username> is required." >&2
    print_help
fi
