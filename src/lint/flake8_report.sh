#!/bin/bash
set -euo pipefail

# Simple wrapper for flake8_report.py following project patterns

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Venv setup (minimal)
VENV_DIR="$SCRIPT_DIR/.venv"
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Setting up Python environment..."
    python3 -m venv "$VENV_DIR"
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    pip install --quiet flake8
else
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
fi

# Execute Python script with all arguments
exec python3 "$SCRIPT_DIR/flake8_report.py" "$@"