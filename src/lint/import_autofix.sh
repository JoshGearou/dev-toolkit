#!/bin/bash
set -euo pipefail

# Simple wrapper for import_autofix.py following project patterns

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Venv setup (minimal) - AST-based import analysis uses only standard library
VENV_DIR="$SCRIPT_DIR/.venv"
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Setting up Python environment..."
    python3 -m venv "$VENV_DIR"
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    # No additional dependencies needed - uses Python standard library AST module
else
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
fi

# Execute Python script with all arguments
exec python3 "$SCRIPT_DIR/import_autofix.py" "$@"