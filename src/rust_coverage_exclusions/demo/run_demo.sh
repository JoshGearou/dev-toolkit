#!/bin/bash

# Demo script to show different coverage scenarios

echo "=== Rust Coverage Demo ==="
echo

# Ensure we're in the demo directory
cd "$(dirname "$0")"

echo "1. Setting up nightly Rust..."
rustup override set nightly

echo
echo "2. Running nightly coverage with #[coverage(off)] exclusions..."
echo "   (Note: excluded_nightly_function should not appear even though it's tested)"
echo "   (Note: uncovered_function should appear with 0% coverage)"
echo "   (Note: covered_function should show good coverage)"
echo

./coverage-nightly.sh

echo
echo "=== Nightly Coverage Report Generated and Opened ==="

echo "3. Now testing with stable Rust + feature flag..."
echo

./coverage.sh

echo
echo "=== Stable Coverage Report Generated and Opened ==="

echo
echo "=== Demo Complete ==="
echo "Key observations:"
echo "- covered_function: Should show good coverage (tested)"
echo "- uncovered_function: Should show 0% coverage (not tested)"  
echo "- excluded_nightly_function: Should NOT appear in nightly report (excluded with #[coverage(off)])"
echo "- excluded_stable_function: Should NOT appear in stable report (excluded with feature flag)"
echo
echo "📊 Coverage reports have been opened in your browser automatically!"
echo "🔍 Compare the two reports to see the difference between nightly and stable exclusion methods."
