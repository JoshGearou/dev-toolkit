#!/bin/bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"
PYTHON_SCRIPT="${SCRIPT_DIR}/pr_quality_check.py"
REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    log_error "python3 not found. Please install Python 3."
    exit 1
fi

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    log_error "gh CLI not found. Install with: brew install gh"
    exit 1
fi

# Check if gh is authenticated
if ! gh auth status &> /dev/null; then
    log_error "gh CLI not authenticated. Run: gh auth login"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [[ ! -d "${VENV_DIR}" ]]; then
    log_info "Creating virtual environment..."
    python3 -m venv "${VENV_DIR}"
    if [[ $? -ne 0 ]]; then
        log_error "Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source "${VENV_DIR}/bin/activate"

# Install/upgrade dependencies if requirements.txt exists
if [[ -f "${REQUIREMENTS_FILE}" ]]; then
    log_info "Installing dependencies from ${REQUIREMENTS_FILE}..."
    pip install --quiet --upgrade pip
    pip install --quiet -r "${REQUIREMENTS_FILE}"
    if [[ $? -ne 0 ]]; then
        log_error "Failed to install dependencies"
        deactivate
        exit 1
    fi
fi

# Run the Python script with all arguments forwarded
log_info "Running PR quality check..."
python3 "${PYTHON_SCRIPT}" "$@"
exit_code=$?

# Deactivate virtual environment
deactivate

exit $exit_code
