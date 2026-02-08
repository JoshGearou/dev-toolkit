#!/bin/bash
set -u

# run.sh - Run the todo tracker on the current repository.
#
# This script builds and runs the todo tracker against the parent repository
# (dev-rerickso) to demonstrate the tool in action.
#
# Usage examples:
#   ./run.sh                       # List all TODOs in table format
#   ./run.sh stats                 # Show summary statistics
#   ./run.sh list --severity TODO  # Filter by severity
#   ./run.sh blame --stale 90      # Show stale TODOs with git blame
#   ./run.sh check                 # Run CI policy checks
#   ./run.sh --format json         # Output as JSON (global flag before subcommand)
#   ./run.sh --help                # Show full CLI help
#
# Note: Subcommands (stats, blame, check, etc.) have no dashes.
#       Global flags (--format, --quiet, etc.) have dashes and go before the subcommand.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}" || exit 1

# The repository root is two levels up from the todo_tracker project
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Binary is in the workspace target directory, not the package target
BINARY="${REPO_ROOT}/target/release/todo"

# Build if the binary doesn't exist or if source files are newer
if [ ! -f "${BINARY}" ] || [ "src/" -nt "${BINARY}" ]; then
    echo "Building todo tracker..." >&2
    cargo build --release --quiet
    echo "" >&2
fi

# Run the tool on the parent repo
cd "${REPO_ROOT}" || exit 1
exec "${BINARY}" "$@"
