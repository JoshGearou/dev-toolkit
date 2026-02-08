#!/bin/bash
set -e

echo "Running stable coverage with feature flag exclusions..."

# Check if llvm-tools component is installed
if ! rustup component list --installed | grep -q "llvm-tools"; then
    echo "Installing llvm-tools-preview component..."
    rustup component add llvm-tools-preview
fi

# Clean up previous coverage data
rm -rf build/coverage
rm -rf build/reports/stable
mkdir -p build/coverage
mkdir -p build/reports/stable

# Set stable toolchain
rustup override set stable

# Run tests with coverage instrumentation and coverage feature
RUSTFLAGS="-C instrument-coverage" \
LLVM_PROFILE_FILE="build/coverage/stable_%m_%p.profraw" \
cargo test --features coverage

# Find llvm tools
LLVM_PROFDATA="$HOME/.rustup/toolchains/stable-aarch64-apple-darwin/lib/rustlib/aarch64-apple-darwin/bin/llvm-profdata"
LLVM_COV="$HOME/.rustup/toolchains/stable-aarch64-apple-darwin/lib/rustlib/aarch64-apple-darwin/bin/llvm-cov"

# Merge coverage data
"$LLVM_PROFDATA" merge -sparse build/coverage/*.profraw -o build/coverage/stable-merged.profdata

# Find the test binary
TEST_BINARY=$(find target/debug/deps -name "coverage_demo-*" -perm +111 | head -1)

if [ -n "$TEST_BINARY" ]; then
    echo "Generating stable coverage report..."
    
    # Generate text report
    echo "=== Stable Coverage Summary ==="
    "$LLVM_COV" report "$TEST_BINARY" -instr-profile=build/coverage/stable-merged.profdata
    
    # Generate HTML report
    "$LLVM_COV" show "$TEST_BINARY" \
        -instr-profile=build/coverage/stable-merged.profdata \
        --format=html \
        --output-dir=build/reports/stable
        
    echo "Stable HTML report generated at: build/reports/stable/index.html"
else
    echo "Error: Could not find test binary"
fi
