#!/bin/bash

# Project Name Script - Bash wrapper for project_name Python implementation
#
# This script follows the dev-rerickso repository patterns:
# - Sources common repository functions
# - Sets up Python virtual environment 
# - Configures shared_libs access
# - Forwards arguments to Python implementation
#
# Usage:
#   ./project_name.sh [python_args...]
#
# Example:
#   ./project_name.sh --verbose --output-file results.csv

set -euo pipefail

# Source common repository functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source repository library functions
source_required_file() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        echo "❌ Required file not found: $file" >&2
        exit 1
    fi
    # shellcheck disable=SC1091
    source "$file"
}

source_required_file "$REPO_ROOT/bash/common/repo_lib.sh"

# Project configuration
readonly PROJECT_NAME="project_name"
readonly PYTHON_SCRIPT="$SCRIPT_DIR/${PROJECT_NAME}.py"
readonly VENV_DIR="$SCRIPT_DIR/.venv"
readonly REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"

setup_python_environment() {
    """Set up Python virtual environment and shared libraries access"""
    log_message "Setting up Python environment for $PROJECT_NAME"
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "$VENV_DIR" ]]; then
        log_message "Creating Python virtual environment"
        python3 -m venv "$VENV_DIR"
        
        # Install requirements if they exist
        if [[ -f "$REQUIREMENTS_FILE" ]]; then
            log_message "Installing requirements"
            "$VENV_DIR/bin/pip" install -r "$REQUIREMENTS_FILE"
        fi
    fi
    
    # Activate virtual environment
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    
    # Add shared_libs to PYTHONPATH for shared utilities access
    export PYTHONPATH="$REPO_ROOT/src/shared_libs:${PYTHONPATH:-}"
    
    log_message "Python environment ready"
}

validate_environment() {
    """Validate that required files exist"""
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        log_message "❌ Python script not found: $PYTHON_SCRIPT"
        exit 1
    fi
    
    # Validate shared_libs is accessible
    if [[ ! -d "$REPO_ROOT/src/shared_libs" ]]; then
        log_message "❌ shared_libs not found: $REPO_ROOT/src/shared_libs"
        exit 1
    fi
}

main() {
    """Main execution function"""
    log_message "Starting $PROJECT_NAME"
    
    validate_environment
    setup_python_environment
    
    # Execute Python script with all provided arguments
    log_message "Executing: python3 $PYTHON_SCRIPT $*"
    exec python3 "$PYTHON_SCRIPT" "$@"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi