#!/bin/bash
set -e

# Check if llvm-tools component is installed (platform-agnostic check)
if ! rustup component list --installed | grep -q "llvm-tools"; then
    echo "Error: llvm-tools component not found. Please run 'mint setup' to install required tools."
    exit 1
fi

rm -rf build/coverage
rm -rf build/reports

# Override any existing RUSTFLAGS from mint to avoid conflicts
RUSTFLAGS="-C instrument-coverage" LLVM_PROFILE_FILE=build/coverage/default_%m_%p.profraw cargo test --features coverage

# Use static-analysis-tools coverage with explicit profraw file
PROFRAW_FILE=$(find build/coverage -name "*.profraw" | head -1)
if [ -n "$PROFRAW_FILE" ]; then
    echo "Using profraw file: $PROFRAW_FILE"
    
    # Run static-analysis-tools from the repository root to include all projects
    cd ../../../
    static-analysis-tools coverage -r "$(realpath "projects/rust_coverage_exclusions/demo/$PROFRAW_FILE")"
    cd projects/rust_coverage_exclusions/demo
    
    # Copy the generated report to our local build directory for easy access
    if [ -d "../../../build/reports/coverage/overall/html" ]; then
        mkdir -p build/reports/stable
        cp -r ../../../build/reports/coverage/overall/html/* build/reports/stable/
        echo "Coverage report copied to: build/reports/stable/index.html"
        
        echo "Opening coverage report in browser..."
        open build/reports/stable/index.html
    fi
else
    echo "Error: No profraw files found in build/coverage"
    exit 1
fi
