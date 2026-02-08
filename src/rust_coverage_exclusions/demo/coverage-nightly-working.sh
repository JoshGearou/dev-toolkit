#!/bin/bash
set -e

echo "Running nightly coverage with #[coverage(off)] exclusions..."

# Check if llvm-tools component is installed
if ! rustup component list --installed | grep -q "llvm-tools"; then
    echo "Installing llvm-tools-preview component..."
    rustup component add llvm-tools-preview
fi

# Clean up previous coverage data
rm -rf build/coverage
rm -rf build/reports/nightly
mkdir -p build/coverage
mkdir -p build/reports/nightly

# Set nightly toolchain
rustup override set nightly

# Force a clean build to ensure we get the right binary
cargo clean

# Run tests with coverage instrumentation and nightly feature
RUSTFLAGS="-C instrument-coverage" \
LLVM_PROFILE_FILE="build/coverage/nightly_%m_%p.profraw" \
cargo test --features nightly

# Find llvm tools
LLVM_PROFDATA="$HOME/.rustup/toolchains/nightly-aarch64-apple-darwin/lib/rustlib/aarch64-apple-darwin/bin/llvm-profdata"
LLVM_COV="$HOME/.rustup/toolchains/nightly-aarch64-apple-darwin/lib/rustlib/aarch64-apple-darwin/bin/llvm-cov"

# Merge coverage data
"$LLVM_PROFDATA" merge -sparse build/coverage/*.profraw -o build/coverage/nightly-merged.profdata

# Find the test binary (most recent one)
TEST_BINARY=$(find target/debug/deps -name "coverage_demo-*" -perm +111 -exec ls -t {} + | head -1)

if [ -n "$TEST_BINARY" ]; then
    echo "Generating nightly coverage report..."
    
    # Generate text report
    echo "=== Nightly Coverage Summary ==="
    "$LLVM_COV" report "$TEST_BINARY" -instr-profile=build/coverage/nightly-merged.profdata
    
    # Generate HTML report
    "$LLVM_COV" show "$TEST_BINARY" \
        -instr-profile=build/coverage/nightly-merged.profdata \
        --format=html \
        --output-dir=build/reports/nightly
        
    echo "Nightly HTML report generated at: build/reports/nightly/index.html"
else
    echo "Error: Could not find test binary"
fi

# Restore stable toolchain
rustup override set stable
