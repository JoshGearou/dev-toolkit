#!/usr/bin/env bash
#
# Run tests for expand_date_ranges.py
#
# Usage:
#   ./run_tests.sh              # Run all tests (normal output)
#   ./run_tests.sh -v           # Run with verbose output
#   ./run_tests.sh -q           # Run with quiet output
#   ./run_tests.sh -h           # Show help
#   ./run_tests.sh <TestClass>  # Run specific test class
#
# Examples:
#   ./run_tests.sh -v
#   ./run_tests.sh TestEdgeCases
#   ./run_tests.sh TestMarkdownParsing -v

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to script directory
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_status() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to show help
show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] [TEST_CLASS]

Run unit tests for expand_date_ranges.py

OPTIONS:
    -v, --verbose       Run tests with verbose output
    -q, --quiet         Run tests with quiet output (minimal)
    -c, --coverage      Run tests with coverage report
    -h, --help          Show this help message

TEST_CLASS:
    Run specific test class (e.g., TestEdgeCases, TestMarkdownParsing)
    If not specified, all tests will be run.

EXAMPLES:
    $(basename "$0")                          # Run all tests
    $(basename "$0") -v                       # Run all tests verbosely
    $(basename "$0") -q                       # Run all tests quietly
    $(basename "$0") TestEdgeCases            # Run only edge case tests
    $(basename "$0") TestEdgeCases -v         # Run edge case tests verbosely

AVAILABLE TEST CLASSES:
    TestMarkdownParsing       (3 tests)  - Multi-table markdown parsing
    TestDateRangeParsing      (5 tests)  - Date range parsing
    TestDateNormalization     (4 tests)  - Date format normalization
    TestDeduplication         (3 tests)  - Duplicate removal
    TestDateRangeExpansion    (2 tests)  - Range expansion
    TestEdgeCases             (6 tests)  - Edge cases and real-world scenarios
    TestSorting               (1 test)   - Chronological sorting
    TestIntegration           (1 test)   - End-to-end integration

Total: 25 tests
EOF
}

# Parse command line arguments
VERBOSE=""
QUIET=""
COVERAGE=""
TEST_CLASS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        -q|--quiet)
            QUIET="--quiet"
            shift
            ;;
        -c|--coverage)
            COVERAGE="yes"
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        Test*)
            TEST_CLASS="test_expand_date_ranges.$1"
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
done

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "python3 is not installed or not in PATH"
    exit 1
fi

# Determine test target
if [[ -n "$TEST_CLASS" ]]; then
    TEST_TARGET="$TEST_CLASS"
    print_status "Running test class: ${TEST_CLASS#test_expand_date_ranges.}"
else
    TEST_TARGET="test_expand_date_ranges"
    print_status "Running all tests"
fi

# Build the command
CMD="python3 -m unittest $TEST_TARGET"

# Add verbosity flags
if [[ -n "$VERBOSE" ]]; then
    CMD="$CMD $VERBOSE"
elif [[ -n "$QUIET" ]]; then
    CMD="$CMD $QUIET"
fi

# Run the tests
echo ""
print_status "Command: $CMD"
echo ""

if $CMD; then
    echo ""
    print_success "All tests passed!"
    
    # Show test count
    if [[ -n "$QUIET" ]]; then
        # In quiet mode, extract and show the summary
        TEST_COUNT=$(python3 -m unittest $TEST_TARGET --quiet 2>&1 | grep "^Ran" | awk '{print $2}')
        if [[ -n "$TEST_COUNT" ]]; then
            print_status "$TEST_COUNT tests passed"
        fi
    fi
    
    exit 0
else
    echo ""
    print_error "Tests failed!"
    exit 1
fi
