#!/bin/bash

# Working demo script using direct llvm-cov commands

echo "=== Rust Coverage Demo (Working Version) ==="
echo

# Ensure we're in the demo directory
cd "$(dirname "$0")"

echo "1. Running nightly coverage with #[coverage(off)] exclusions..."
./coverage-nightly-working.sh

echo
echo "2. Running stable coverage with feature flag exclusions..."
./coverage-stable-working.sh

echo
echo "=== Demo Complete ==="
echo
echo "Key observations:"
echo "- covered_function: Should show good coverage (tested)"
echo "- uncovered_function: Should show 0% coverage (not tested)"  
echo "- excluded_nightly_function: Should NOT appear in nightly report (excluded with #[coverage(off)])"
echo "- excluded_stable_function: Should NOT appear in stable report (excluded with feature flag)"
echo
echo "=== Generated Coverage Reports ==="
echo "🎯 Nightly Coverage Report (with #[coverage(off)] exclusions):"
echo "   📊 file:///Users/rerickso/src/sandbox/dev-rerickso/projects/rust_coverage_exclusions/demo/build/reports/nightly/index.html"
echo
echo "🎯 Stable Coverage Report (with feature flag exclusions):"
echo "   📊 file:///Users/rerickso/src/sandbox/dev-rerickso/projects/rust_coverage_exclusions/demo/build/reports/stable/index.html"
echo
echo "🌐 Opening coverage reports in your browser..."

# Open the reports in the default browser
if command -v open >/dev/null 2>&1; then
    open "file:///Users/rerickso/src/sandbox/dev-rerickso/projects/rust_coverage_exclusions/demo/build/reports/nightly/index.html"
    sleep 1
    open "file:///Users/rerickso/src/sandbox/dev-rerickso/projects/rust_coverage_exclusions/demo/build/reports/stable/index.html"
    echo "✅ Coverage reports opened in browser!"
else
    echo "⚠️  Could not auto-open browser. Please manually open the file:// URLs above."
fi

echo
echo "🔍 Compare the two reports to see the difference between:"
echo "   • Nightly: excluded_nightly_function should be completely absent"
echo "   • Stable: excluded_stable_function should be completely absent"
echo
echo "Expected differences:"
echo "  • Nightly: excluded_nightly_function should be completely absent from the report"
echo "  • Stable: excluded_stable_function should be completely absent from the report"
echo

echo "3. Restoring stable toolchain as default..."
rustup override set stable
echo "✅ Stable toolchain restored as default for this project."
