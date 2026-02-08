#!/bin/zsh
#
# Shell wrapper for expand_date_ranges.py
# Expands date ranges in holiday CSV/Markdown files to one row per day
#
# Usage:
#   ./expand_date_ranges.sh <input_file> [output_csv]
#   ./expand_date_ranges.sh --help
#   ./expand_date_ranges.sh --all     # Process all CSV/MD files in current directory
#

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="${0:A:h}"
PYTHON_SCRIPT="${SCRIPT_DIR}/expand_date_ranges.py"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print usage
usage() {
    echo "Usage: $0 <input_file> [output_csv]"
    echo "       $0 --all [directory]"
    echo "       $0 --help"
    echo ""
    echo "Options:"
    echo "  <input_file>      Input CSV or Markdown file with date ranges"
    echo "  [output_csv]      Optional output CSV file"
    echo "                    (default: updates CSV in place or creates .csv from .md)"
    echo "  --all [directory] Process all *.csv and *.md files in specified directory"
    echo "                    (default: current directory)"
    echo "  --help            Show this help message"
    echo ""
    echo "Input formats:"
    echo "  - CSV files (*.csv)"
    echo "  - Markdown files with tables (*.md)"
    echo ""
    echo "Output is always CSV format."
    echo ""
    echo "Examples:"
    echo "  $0 2025_holidays_usa.csv"
    echo "  $0 2025_holidays.md"
    echo "  $0 2025_holidays.md 2025_holidays_expanded.csv"
    echo "  $0 --all"
    echo "  $0 --all ./holidays/"
    exit 0
}

# Check if Python script exists
if [[ ! -f "${PYTHON_SCRIPT}" ]]; then
    echo "${RED}Error: Python script not found at ${PYTHON_SCRIPT}${NC}" >&2
    exit 1
fi

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "${RED}Error: python3 is not installed or not in PATH${NC}" >&2
    exit 1
fi

# Parse arguments
if [[ $# -eq 0 ]]; then
    usage
fi

case "$1" in
    --help|-h)
        usage
        ;;
    --all)
        # Process all CSV and MD files in specified or current directory
        TARGET_DIR="${2:-.}"
        
        if [[ ! -d "${TARGET_DIR}" ]]; then
            echo "${RED}Error: Directory '${TARGET_DIR}' not found${NC}" >&2
            exit 1
        fi
        
        echo "${YELLOW}Processing all CSV and MD files in ${TARGET_DIR}...${NC}"
        found_files=false
        
        # Process CSV files
        for file in "${TARGET_DIR}"/*.csv(N); do
            if [[ -f "$file" ]]; then
                found_files=true
                echo ""
                echo "${GREEN}Processing: $file${NC}"
                python3 "${PYTHON_SCRIPT}" "$file"
            fi
        done
        
        # Process MD files
        for file in "${TARGET_DIR}"/*.md(N); do
            if [[ -f "$file" ]]; then
                found_files=true
                echo ""
                echo "${GREEN}Processing: $file${NC}"
                python3 "${PYTHON_SCRIPT}" "$file"
            fi
        done
        
        if [[ "$found_files" = false ]]; then
            echo "${YELLOW}No *.csv or *.md files found in ${TARGET_DIR}${NC}"
            exit 1
        fi
        ;;
    *)
        # Process single file or with output file
        INPUT_FILE="$1"
        OUTPUT_FILE="${2:-}"
        
        if [[ ! -f "${INPUT_FILE}" ]]; then
            echo "${RED}Error: Input file '${INPUT_FILE}' not found${NC}" >&2
            exit 1
        fi
        
        if [[ -n "${OUTPUT_FILE}" ]]; then
            python3 "${PYTHON_SCRIPT}" "${INPUT_FILE}" "${OUTPUT_FILE}"
        else
            python3 "${PYTHON_SCRIPT}" "${INPUT_FILE}"
        fi
        ;;
esac

echo ""
echo "${GREEN}✓ Done!${NC}"
