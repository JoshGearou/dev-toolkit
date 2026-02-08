#!/bin/bash
set -u

# validate.sh - Run the full CI pipeline for todo_tracker.
#
# Order follows Rust best practices:
#   1. fmt        Format check (fast, catches style before anything compiles)
#   2. clippy     Lint (catches bugs before tests run)
#   3. build      Compile release binary
#   4. test       Unit + integration tests
#   5. doc        Build documentation
#   6. deny       Dependency audit (if cargo-deny and deny.toml are present)
#   7. coverage   Code coverage report (slow, opt-in via --coverage)
#
# Usage:
#   ./validate.sh              # Run steps 1-6
#   ./validate.sh --coverage   # Run steps 1-7
#   ./validate.sh --fix        # Auto-fix fmt and clippy where possible
#   ./validate.sh --quick      # Run only fmt + clippy + test (no release build, no docs)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}" || exit 1

# ── Options ──────────────────────────────────────────────────────────────────

RUN_COVERAGE=false
AUTO_FIX=false
QUICK=false

for arg in "$@"; do
    case "${arg}" in
        --coverage) RUN_COVERAGE=true ;;
        --fix)      AUTO_FIX=true ;;
        --quick)    QUICK=true ;;
        --help|-h)
            echo "Usage: ./validate.sh [--fix] [--quick] [--coverage]"
            echo ""
            echo "  --fix        Auto-fix formatting and clippy warnings"
            echo "  --quick      Only run fmt + clippy + test (skip release build, docs, deny)"
            echo "  --coverage   Run code coverage report after all other steps"
            exit 0
            ;;
        *)
            echo "Unknown option: ${arg}"
            exit 1
            ;;
    esac
done

# ── Helpers ──────────────────────────────────────────────────────────────────

PASS=0
FAIL=0
SKIP=0

step() {
    local name="$1"
    shift
    echo ""
    echo "━━━ ${name} ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if "$@"; then
        echo "  ✓ ${name}"
        PASS=$((PASS + 1))
    else
        echo "  ✗ ${name} FAILED (exit $?)"
        FAIL=$((FAIL + 1))
        return 1
    fi
}

skip() {
    local name="$1"
    echo ""
    echo "━━━ ${name} ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  - ${name} skipped"
    SKIP=$((SKIP + 1))
}

export RUSTFLAGS="-D warnings"

# ── 1. Format ────────────────────────────────────────────────────────────────

if [ "${AUTO_FIX}" = true ]; then
    step "fmt (auto-fix)" cargo fmt --all
else
    step "fmt (check)" cargo fmt --all -- --check
fi

# Fail fast: if formatting is wrong, nothing else matters.
if [ "${FAIL}" -gt 0 ] && [ "${AUTO_FIX}" = false ]; then
    echo ""
    echo "Formatting check failed. Run with --fix or 'cargo fmt --all' to fix."
    exit 1
fi

# ── 2. Clippy ────────────────────────────────────────────────────────────────

CLIPPY_ARGS=(
    --all-targets
    --all-features
    --message-format=human
    --
    -D warnings
    -D clippy::missing_docs_in_private_items
)

if [ "${AUTO_FIX}" = true ]; then
    step "clippy (auto-fix)" cargo clippy --fix --allow-dirty --allow-staged "${CLIPPY_ARGS[@]}"
else
    # cargo check first for faster feedback on compilation errors
    step "check" cargo check --all-targets --all-features
    if [ "${FAIL}" -gt 0 ]; then
        echo ""
        echo "Compilation failed. Fix errors before clippy can run."
        exit 1
    fi
    step "clippy" cargo clippy "${CLIPPY_ARGS[@]}"
fi

# Fail fast: clippy failures likely mean tests will fail too.
if [ "${FAIL}" -gt 0 ]; then
    echo ""
    echo "Clippy failed. Fix lint issues before proceeding."
    exit 1
fi

# ── 3. Build (release) ──────────────────────────────────────────────────────

if [ "${QUICK}" = true ]; then
    skip "build (release)"
else
    step "build (release)" cargo build --release
fi

# ── 4. Test ──────────────────────────────────────────────────────────────────

step "test" cargo test --all-features

# ── 5. Examples ──────────────────────────────────────────────────────────────

if [ -d "examples" ] && [ -n "$(ls examples/*.rs 2>/dev/null)" ]; then
    step "examples" bash -c '
        for f in examples/*.rs; do
            base="${f##*/}"
            echo "  Running example: ${base%.rs}"
            cargo run --example "${base%.rs}" || exit 1
        done
    '
else
    skip "examples (none found)"
fi

# ── 6. Documentation ────────────────────────────────────────────────────────

if [ "${QUICK}" = true ]; then
    skip "doc"
else
    step "doc" cargo doc --no-deps --document-private-items

    # Create redirect index for browsing
    if [ -d "target/doc" ]; then
        echo '<meta http-equiv="refresh" content="0; url=todo_tracker">' > target/doc/index.html
    fi
fi

# ── 7. Dependency audit ─────────────────────────────────────────────────────

if [ "${QUICK}" = true ]; then
    skip "deny"
elif command -v cargo-deny &>/dev/null && [ -f "deny.toml" ]; then
    step "deny" cargo deny check --config deny.toml --show-stats
else
    skip "deny (cargo-deny not installed or deny.toml not found)"
fi

# ── 8. Coverage (opt-in) ────────────────────────────────────────────────────

if [ "${RUN_COVERAGE}" = true ]; then
    if ! command -v cargo-tarpaulin &>/dev/null; then
        echo "Installing cargo-tarpaulin..."
        cargo install cargo-tarpaulin
    fi
    step "coverage" cargo tarpaulin \
        --no-default-features \
        --exclude-files "benches/*" \
        --exclude-files "examples/*" \
        --out Html \
        --output-dir coverage

    if [ -f "coverage/tarpaulin-report.html" ]; then
        echo "  Coverage report: coverage/tarpaulin-report.html"
    fi
else
    skip "coverage (use --coverage to enable)"
fi

# ── Summary ──────────────────────────────────────────────────────────────────

echo ""
echo "━━━ Summary ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  passed:  ${PASS}"
echo "  failed:  ${FAIL}"
echo "  skipped: ${SKIP}"
echo ""

if [ "${FAIL}" -gt 0 ]; then
    echo "FAILED"
    exit 1
else
    echo "ALL PASSED"
    exit 0
fi
