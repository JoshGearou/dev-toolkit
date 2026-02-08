#!/usr/bin/env bash
set -euo pipefail

# Node.js Environment Diagnostic Tool - Bash wrapper
#
# Handles virtual environment setup and forwards to Python diagnostic script.
# Uses workspace standard pattern with shared_libs integration.
#
# Usage:
#   ./diagnose_node_env.sh [--verbose]
#

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/diagnose_node_env.py"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Check if Python script exists
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT"
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is required but not found"
    echo "Install: brew install python3  # macOS"
    echo "Install: apt-get install python3  # Ubuntu/Debian"
    exit 1
fi

# Setup Python environment
VENV_DIR="$SCRIPT_DIR/.venv"

# Create virtual environment if it doesn't exist
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# Install/upgrade required packages if needed
if [[ ! -f "$VENV_DIR/.packages_installed" ]]; then
    echo "Installing required Python packages..."
    python3 -m pip install --upgrade pip > /dev/null 2>&1
    # Add any required packages here if there's a requirements.txt
    if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
        python3 -m pip install -r "$SCRIPT_DIR/requirements.txt" > /dev/null 2>&1
    fi
    touch "$VENV_DIR/.packages_installed"
fi

# Set PYTHONPATH for shared_libs access
export PYTHONPATH="${REPO_ROOT}/src:${PYTHONPATH:-}"

# Forward all arguments to the Python script
exec python3 "$PYTHON_SCRIPT" "$@"
