#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------------------------
# run_bench.sh – bootstrap a Rust project in bench_proj/, build it, then
#              measure in 4 modes: plain, plain_pinned, tmux, tmux_pinned
#              write results as CSV into the current directory
# Supports Linux (CPU pinning via taskset) and macOS (skips pinned tests)
# ------------------------------------------------------------------------------

# Trap to clean up tmux sessions on exit
cleanup() {
    echo "Cleaning up tmux sessions..."
    tmux_sessions=$(tmux ls -F "#{session_name}" 2>/dev/null | grep "^bench_" || true)
    if [ -n "$tmux_sessions" ]; then
        echo "$tmux_sessions" | xargs -I {} tmux kill-session -t {} 2>/dev/null || true
        echo "Cleaned up tmux sessions"
    fi
    echo "Cleanup complete"
}
trap cleanup EXIT

# Configurable defaults
CORE=${CORE:-2}
# Define OS first since we use it below
OS=$(uname)
# Convert relative path to absolute path to avoid issues
PROJ_DIR=${PROJ_DIR:-bench_proj}
# Use a cross-platform way to get absolute path
if [[ "$OS" = "Darwin" ]]; then
    PROJ_DIR=$(mkdir -p "$PROJ_DIR" && cd "$PROJ_DIR" && pwd)
else
    PROJ_DIR=$(realpath "$PROJ_DIR")
fi
ITERATIONS=${1:-5000000}

# Ensure project directory exists 
mkdir -p "$PROJ_DIR"

# Make sure results directory exists and is writable
RESULTS=${RESULTS:-"${PROJ_DIR}/bench_results.csv"}
# Use a cross-platform way to get absolute path for results
RESULTS_DIR=$(dirname "$RESULTS")
mkdir -p "$RESULTS_DIR"
if [[ "$OS" = "Darwin" ]]; then
    RESULTS=$(cd "$RESULTS_DIR" && pwd)/$(basename "$RESULTS")
else
    RESULTS=$(realpath "$RESULTS")
fi

echo "Using project dir: $PROJ_DIR"
echo "Results will be written to: $RESULTS"

# Helper flags
IS_LINUX=false
IS_MAC=false
HAS_TASKSET=false
HAS_TMUX=false

[[ "$OS" = "Linux" ]] && IS_LINUX=true
[[ "$OS" = "Darwin" ]] && IS_MAC=true
command -v taskset >/dev/null 2>&1 && HAS_TASKSET=true || HAS_TASKSET=false
command -v tmux    >/dev/null 2>&1 && HAS_TMUX=true    || HAS_TMUX=false

# 1) Fresh Cargo project
rm -rf "$PROJ_DIR"
cargo new "$PROJ_DIR" --bin

# 2) Write benchmark source
cat > "$PROJ_DIR/src/main.rs" << 'EOF'
// bench_proj/src/main.rs
fn main() {
    let n = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(10_000_000);
    let mut acc: u64 = 0;
    for i in 0..n {
        acc = acc.wrapping_add((i as u64).wrapping_mul(31).wrapping_add(17));
    }
    println!("Result: {}", acc);
}

/// The calculation function that will be used for both main and benchmarks
pub fn calculate(n: u64) -> u64 {
    let mut acc: u64 = 0;
    for i in 0..n {
        acc = acc.wrapping_add((i as u64).wrapping_mul(31).wrapping_add(17));
    }
    acc
}
EOF

# Add criterion dependency to Cargo.toml
cat >> "$PROJ_DIR/Cargo.toml" << 'EOF'

[dev-dependencies]
criterion = "0.5"

[[bench]]
name = "simple_bench"
harness = false
EOF

# Create benchmark directory
mkdir -p "$PROJ_DIR/benches"

# Create benchmark file
cat > "$PROJ_DIR/benches/simple_bench.rs" << 'EOF'
use criterion::{black_box, criterion_group, criterion_main, Criterion};

// Define the calculation function directly in the benchmark
fn calculate(n: u64) -> u64 {
    let mut acc: u64 = 0;
    for i in 0..n {
        acc = acc.wrapping_add((i as u64).wrapping_mul(31).wrapping_add(17));
    }
    acc
}

fn bench_calculate(c: &mut Criterion) {
    c.bench_function("calculate", |b| {
        b.iter(|| {
            calculate(black_box(50000))
        })
    });
}

criterion_group!(benches, bench_calculate);
criterion_main!(benches);
EOF

# 3) Build in release mode
pushd "$PROJ_DIR" >/dev/null
echo "Building release binary for $(basename "$PROJ_DIR")..."
cargo build --release --bin "$(basename "$PROJ_DIR")"
echo "Building benchmarks..."
cargo build --benches
popd >/dev/null

# Find the binary - it could be in a workspace target directory or in the local target directory
BIN="$PROJ_DIR/target/release/$(basename "$PROJ_DIR")"
WORKSPACE_BIN="$(dirname "$PROJ_DIR")/target/release/$(basename "$PROJ_DIR")"
ROOT_BIN="$(cd "$PROJ_DIR" && cargo metadata --format-version=1 | grep -o '"workspace_root":"[^"]*"' | sed 's/"workspace_root":"\([^"]*\)"/\1/' 2>/dev/null)/target/release/$(basename "$PROJ_DIR")"

echo "Checking for binary in standard location: $BIN"
if [ ! -f "$BIN" ]; then
    echo "Binary not found in standard location, checking workspace location: $WORKSPACE_BIN"
    if [ -f "$WORKSPACE_BIN" ]; then
        BIN="$WORKSPACE_BIN"
        echo "Using workspace binary: $BIN"
    else
        echo "Checking root workspace location: $ROOT_BIN" 
        if [ -f "$ROOT_BIN" ]; then
            BIN="$ROOT_BIN"
            echo "Using root workspace binary: $BIN"
        else
            echo "Binary not found in expected locations. Searching for it..."
            FOUND_BIN=$(find "$(dirname "$PROJ_DIR")" -name "$(basename "$PROJ_DIR")" -type f -executable | grep -v "\.d$" | head -1 || true)
            
            if [ -n "$FOUND_BIN" ]; then
                BIN="$FOUND_BIN"
                echo "Found binary at: $BIN"
            else
                echo "Error: Binary not found in any location"
                echo "Available binaries in project target:"
                find "$PROJ_DIR/target" -type f -executable 2>/dev/null | grep -v "\.d$" | sort || echo "No binaries found in project target"
                echo "Available binaries in parent target:"
                find "$(dirname "$PROJ_DIR")/target" -type f -executable 2>/dev/null | grep -v "\.d$" | sort || echo "No binaries found in parent target"
                exit 1
            fi
        fi
    fi
fi

echo "Using binary: $BIN"
# Quick check to make sure the binary is executable
if [ ! -x "$BIN" ]; then
    echo "Warning: Binary $BIN is not executable, attempting to fix permissions"
    chmod +x "$BIN" || { echo "Failed to make binary executable"; exit 1; }
fi

# 4) Start CSV
echo "variant,µs,log" > "$RESULTS"

# 5) Measurement functions
measure() {
    tag=$1; shift
    echo "Running command: $*"
    start=$(date +%s%N 2>/dev/null || date +%s)
    if ! "$@" > "${PROJ_DIR}/${tag}.log" 2>&1; then
        echo "Warning: Command failed: $*"
        echo "See log: ${PROJ_DIR}/${tag}.log"
        # Cat out the log to see the error
        cat "${PROJ_DIR}/${tag}.log"
        # Don't exit due to failure, just record the failure
        elapsed=$(( ( $(date +%s%N 2>/dev/null || date +%s) - start ) / 1000 ))
        echo "${tag},ERROR-${elapsed},${PROJ_DIR}/${tag}.log" >> "$RESULTS"
        return 0  # Don't propagate the error to honor set -e
    else
        elapsed=$(( ( $(date +%s%N 2>/dev/null || date +%s) - start ) / 1000 ))
        echo "${tag},${elapsed},${PROJ_DIR}/${tag}.log" >> "$RESULTS"
    fi
}

measure_tmux() {
    tag=$1; shift
    session=bench_${tag}_$$
    echo "Running tmux command: $*"
    if ! tmux new-session -d -s "$session"; then
        echo "Warning: Failed to create tmux session: $session"
        echo "${tag},ERROR,${PROJ_DIR}/${tag}.log" >> "$RESULTS"
        return 0
    fi
    tmux set-option -t "$session" status off
    tmux set-option -t "$session" escape-time 0
    tmux pipe-pane -t "$session" -o 'cat >/dev/null'

    start=$(date +%s%N 2>/dev/null || date +%s)
    tmux send-keys -t "$session" "$* > ${PROJ_DIR}/${tag}.log 2>&1" C-m
    tmux send-keys -t "$session" "exit" C-m
    
    # Wait for session to end with a timeout
    local timeout=60  # 60 seconds timeout
    local waited=0
    while tmux has-session -t "$session" 2>/dev/null; do 
        sleep 0.05
        waited=$((waited+1))
        if [ $waited -gt $((timeout*20)) ]; then  # 20 iterations per second
            echo "Warning: Tmux session $session timed out after ${timeout}s"
            tmux kill-session -t "$session" 2>/dev/null || true
            break
        fi
    done
    
    elapsed=$(( ( $(date +%s%N 2>/dev/null || date +%s) - start ) / 1000 ))
    echo "${tag},${elapsed},${PROJ_DIR}/${tag}.log" >> "$RESULTS"
    return 0
}

measure_tmux_detached() {
    tag=$1; shift
    session=bench_${tag}_$$
    
    # Create a detached session with a command that will run directly in the first window
    # and exit the session when done
    if ! tmux new-session -d -s "$session" "bash -c '$* > ${PROJ_DIR}/${tag}.log 2>&1; exit'"; then
        echo "Warning: Failed to create tmux session: $session"
        echo "${tag},ERROR,${PROJ_DIR}/${tag}.log" >> "$RESULTS"
        return 0
    fi
    
    tmux set-option -t "$session" status off 2>/dev/null || true
    tmux set-option -t "$session" escape-time 0 2>/dev/null || true

    start=$(date +%s%N 2>/dev/null || date +%s)
    # Wait for the session to end naturally when the command completes with timeout
    local timeout=60  # 60 seconds timeout
    local waited=0
    while tmux has-session -t "$session" 2>/dev/null; do 
        sleep 0.05
        waited=$((waited+1))
        if [ $waited -gt $((timeout*20)) ]; then  # 20 iterations per second
            echo "Warning: Tmux session $session timed out after ${timeout}s"
            tmux kill-session -t "$session" 2>/dev/null || true
            break
        fi
    done
    
    elapsed=$(( ( $(date +%s%N 2>/dev/null || date +%s) - start ) / 1000 ))
    echo "${tag},${elapsed},${PROJ_DIR}/${tag}.log" >> "$RESULTS"
    return 0
}

measure_cargo_bench() {
    tag=$1; shift
    pushd "$PROJ_DIR" >/dev/null
    echo "Running cargo bench command: cargo bench $*"
    start=$(date +%s%N 2>/dev/null || date +%s)
    if ! cargo bench "$@" > "${tag}.log" 2>&1; then
        echo "Warning: Cargo bench command failed: cargo bench $*"
        echo "See log: ${PROJ_DIR}/${tag}.log"
        # Cat out the first few lines of the log to see the error
        head -20 "${tag}.log"
        # Don't exit due to failure, just record the failure
        elapsed=$(( ( $(date +%s%N 2>/dev/null || date +%s) - start ) / 1000 ))
        echo "${tag},ERROR-${elapsed},${PROJ_DIR}/${tag}.log" >> "$RESULTS"
    else
        elapsed=$(( ( $(date +%s%N 2>/dev/null || date +%s) - start ) / 1000 ))
        echo "${tag},${elapsed},${PROJ_DIR}/${tag}.log" >> "$RESULTS"
    fi
    popd >/dev/null
    return 0  # Don't propagate the error to honor set -e
}

measure_cargo_bench_tmux() {
    tag=$1; shift
    session=bench_${tag}_$$
    tmux new-session -d -s "$session"
    tmux set-option -t "$session" status off
    tmux set-option -t "$session" escape-time 0
    tmux pipe-pane -t "$session" -o 'cat >/dev/null'
    
    # Change to project directory inside tmux
    tmux send-keys -t "$session" "cd $PROJ_DIR" C-m
    
    start=$(date +%s%N 2>/dev/null || date +%s)
    tmux send-keys -t "$session" "cargo bench $* > ${tag}.log 2>&1" C-m
    tmux send-keys -t "$session" "exit" C-m
    while tmux has-session -t "$session" 2>/dev/null; do sleep 0.05; done
    elapsed=$(( ( $(date +%s%N 2>/dev/null || date +%s) - start ) / 1000 ))
    echo "${tag},${elapsed},${PROJ_DIR}/${tag}.log" >> "$RESULTS"
}

measure_cargo_bench_tmux_detached() {
    tag=$1; shift
    session=bench_${tag}_$$
    
    # Create a detached session with a command that will run directly and exit when done
    if ! tmux new-session -d -s "$session" "cd $PROJ_DIR && cargo bench $* > ${tag}.log 2>&1; exit"; then
        echo "Warning: Failed to create tmux session: $session"
        echo "${tag},ERROR,${PROJ_DIR}/${tag}.log" >> "$RESULTS"
        return 0
    fi
    
    tmux set-option -t "$session" status off 2>/dev/null || true
    tmux set-option -t "$session" escape-time 0 2>/dev/null || true
    
    start=$(date +%s%N 2>/dev/null || date +%s)
    # Wait for the session to end with timeout
    local timeout=180  # 180 seconds timeout (cargo bench can take a while)
    local waited=0
    while tmux has-session -t "$session" 2>/dev/null; do 
        sleep 0.05
        waited=$((waited+1))
        if [ $waited -gt $((timeout*20)) ]; then  # 20 iterations per second
            echo "Warning: Tmux session $session timed out after ${timeout}s"
            tmux kill-session -t "$session" 2>/dev/null || true
            break
        fi
    done
    
    elapsed=$(( ( $(date +%s%N 2>/dev/null || date +%s) - start ) / 1000 ))
    echo "${tag},${elapsed},${PROJ_DIR}/${tag}.log" >> "$RESULTS"
    return 0
}

# 6) Run benchmarks

# Plain
echo "Running plain..."
BIN_NAME=$(basename "$BIN")
echo "Executing binary: $BIN ($BIN_NAME) with iterations: $ITERATIONS"
measure plain "$BIN" "$ITERATIONS"

# tmux
echo "Running tmux..."
if $HAS_TMUX; then
    measure_tmux tmux "$BIN" "$ITERATIONS"
else
    echo "tmux,NA,${PROJ_DIR}/tmux.log" >> "$RESULTS"
fi

# tmux detached (without terminal emulation overhead)
echo "Running tmux_detached..."
if $HAS_TMUX; then
    measure_tmux_detached tmux_detached "$BIN" "$ITERATIONS"
else
    echo "tmux_detached,NA,${PROJ_DIR}/tmux_detached.log" >> "$RESULTS"
fi

# tmux + pinned tests removed

# Cargo bench tests
echo "Running cargo_bench..."
measure_cargo_bench cargo_bench

# Cargo bench with taskset (Linux only) removed

# Cargo bench with tmux
echo "Running cargo_bench_tmux..."
if $HAS_TMUX; then
    measure_cargo_bench_tmux cargo_bench_tmux
else
    echo "cargo_bench_tmux,NA,${PROJ_DIR}/cargo_bench_tmux.log" >> "$RESULTS"
fi

# Cargo bench with tmux detached
echo "Running cargo_bench_tmux_detached..."
if $HAS_TMUX; then
    measure_cargo_bench_tmux_detached cargo_bench_tmux_detached
else
    echo "cargo_bench_tmux_detached,NA,${PROJ_DIR}/cargo_bench_tmux_detached.log" >> "$RESULTS"
fi

# Cargo bench with tmux and taskset (Linux only) removed

# 7) Analysis of results
echo -e "\n=== Performance Analysis ==="

# Extract times from results
PLAIN_TIME=$(grep "^plain," "$RESULTS" | cut -d',' -f2)
TMUX_TIME=$(grep "^tmux," "$RESULTS" | cut -d',' -f2)
TMUX_DETACHED_TIME=$(grep "^tmux_detached," "$RESULTS" | cut -d',' -f2)

# Check if we have valid times for plain and tmux
if [[ "$PLAIN_TIME" != "NA" && "$TMUX_TIME" != "NA" ]]; then
    RATIO=$(echo "scale=2; $TMUX_TIME / $PLAIN_TIME" | bc -l)
    PERCENT_SLOWER=$(echo "scale=2; ($TMUX_TIME - $PLAIN_TIME) * 100 / $PLAIN_TIME" | bc -l)
    echo -e "\nSimple Program Execution:"
    echo "  Plain:  $PLAIN_TIME µs"
    echo "  tmux:   $TMUX_TIME µs"
    echo "  Impact: tmux is ${RATIO}x slower (${PERCENT_SLOWER}% overhead)"
    
    if [[ "$TMUX_DETACHED_TIME" != "NA" ]]; then
        DETACHED_RATIO=$(echo "scale=2; $TMUX_DETACHED_TIME / $PLAIN_TIME" | bc -l)
        DETACHED_PERCENT=$(echo "scale=2; ($TMUX_DETACHED_TIME - $PLAIN_TIME) * 100 / $PLAIN_TIME" | bc -l)
        echo "  tmux detached: $TMUX_DETACHED_TIME µs"
        echo "  Detached Impact: tmux_detached is ${DETACHED_RATIO}x slower (${DETACHED_PERCENT}% overhead)"
        
        # Compare detached vs regular tmux
        TMUX_VS_DETACHED=$(echo "scale=2; $TMUX_TIME / $TMUX_DETACHED_TIME" | bc -l)
        TMUX_VS_DETACHED_PERCENT=$(echo "scale=2; ($TMUX_TIME - $TMUX_DETACHED_TIME) * 100 / $TMUX_DETACHED_TIME" | bc -l)
        echo "  tmux vs detached: Regular tmux is ${TMUX_VS_DETACHED}x $(if (( $(echo "$TMUX_VS_DETACHED < 1" | bc -l) )); then echo "faster"; else echo "slower"; fi) than detached mode"
    fi
else
    echo "Cannot calculate plain vs tmux impact: missing data"
fi

# Extract Criterion benchmark times
CARGO_TIME=$(grep "^cargo_bench," "$RESULTS" | cut -d',' -f2)
CARGO_TMUX_TIME=$(grep "^cargo_bench_tmux," "$RESULTS" | cut -d',' -f2)
CARGO_TMUX_DETACHED_TIME=$(grep "^cargo_bench_tmux_detached," "$RESULTS" | cut -d',' -f2)

if [[ "$CARGO_TIME" != "NA" && "$CARGO_TMUX_TIME" != "NA" ]]; then
    CARGO_RATIO=$(echo "scale=2; $CARGO_TMUX_TIME / $CARGO_TIME" | bc -l)
    CARGO_PERCENT=$(echo "scale=2; ($CARGO_TMUX_TIME - $CARGO_TIME) * 100 / $CARGO_TIME" | bc -l)
    
    echo -e "\nCargo Bench Execution (Wall clock):"
    echo "  Plain:      $CARGO_TIME µs"
    echo "  tmux:       $CARGO_TMUX_TIME µs"
    echo "  Impact:     tmux is ${CARGO_RATIO}x $(if (( $(echo "$CARGO_RATIO < 1" | bc -l) )); then echo "faster"; else echo "slower"; fi) ($(if (( $(echo "$CARGO_PERCENT < 0" | bc -l) )); then echo "-"; else echo "+"; fi)${CARGO_PERCENT#-}% difference)"
    
    if [[ "$CARGO_TMUX_DETACHED_TIME" != "NA" ]]; then
        CARGO_DETACHED_RATIO=$(echo "scale=2; $CARGO_TMUX_DETACHED_TIME / $CARGO_TIME" | bc -l)
        CARGO_DETACHED_PERCENT=$(echo "scale=2; ($CARGO_TMUX_DETACHED_TIME - $CARGO_TIME) * 100 / $CARGO_TIME" | bc -l)
        echo "  tmux detached: $CARGO_TMUX_DETACHED_TIME µs"
        echo "  Detached Impact: tmux_detached is ${CARGO_DETACHED_RATIO}x $(if (( $(echo "$CARGO_DETACHED_RATIO < 1" | bc -l) )); then echo "faster"; else echo "slower"; fi) ($(if (( $(echo "$CARGO_DETACHED_PERCENT < 0" | bc -l) )); then echo "-"; else echo "+"; fi)${CARGO_DETACHED_PERCENT#-}% difference)"
        
        # Compare detached vs regular tmux
        CARGO_TMUX_VS_DETACHED=$(echo "scale=2; $CARGO_TMUX_TIME / $CARGO_TMUX_DETACHED_TIME" | bc -l)
        CARGO_TMUX_VS_DETACHED_PERCENT=$(echo "scale=2; ($CARGO_TMUX_TIME - $CARGO_TMUX_DETACHED_TIME) * 100 / $CARGO_TMUX_DETACHED_TIME" | bc -l)
        echo "  tmux vs detached: Regular tmux is ${CARGO_TMUX_VS_DETACHED}x $(if (( $(echo "$CARGO_TMUX_VS_DETACHED < 1" | bc -l) )); then echo "faster"; else echo "slower"; fi) than detached mode"
    fi
else
    echo "Cannot calculate cargo bench vs cargo bench tmux impact: missing data"
fi

# Extract the actual benchmark results from the logs - use middle value (median)
echo -e "\nMicrobenchmark Results (From Criterion):"

if [[ -f "${PROJ_DIR}/cargo_bench.log" && -f "${PROJ_DIR}/cargo_bench_tmux.log" ]]; then
    # Extract median times (middle value) with a simpler, more robust method
    BENCH_LINE=$(grep -A3 "calculate.*time:" "${PROJ_DIR}/cargo_bench.log" 2>/dev/null | head -1 || echo "No calculate time found")
    BENCH_TMUX_LINE=$(grep -A3 "calculate.*time:" "${PROJ_DIR}/cargo_bench_tmux.log" 2>/dev/null | head -1 || echo "No calculate time found")
    
    echo "Extracted bench line: $BENCH_LINE"
    echo "Extracted tmux bench line: $BENCH_TMUX_LINE"

    # Use sed to extract just the middle time value (assumes format "[num1 ps num2 ps num3 ps]")
    # Be defensive and provide default values if extraction fails
    BENCH_RESULT=$(echo "$BENCH_LINE" | sed -E 's/.*\[([0-9.]+) ps ([0-9.]+) ps ([0-9.]+) ps\].*/\2/' 2>/dev/null || echo "NA")
    BENCH_TMUX_RESULT=$(echo "$BENCH_TMUX_LINE" | sed -E 's/.*\[([0-9.]+) ps ([0-9.]+) ps ([0-9.]+) ps\].*/\2/' 2>/dev/null || echo "NA")
    
    # Continue only if we successfully extracted values
    if [[ "$BENCH_RESULT" =~ ^[0-9.]+$ ]] && [[ "$BENCH_TMUX_RESULT" =~ ^[0-9.]+$ ]]; then
        # Calculate ratio and percentage difference
        BENCH_RATIO=$(echo "scale=4; $BENCH_TMUX_RESULT / $BENCH_RESULT" | bc)
        BENCH_PERCENT=$(echo "scale=2; ($BENCH_TMUX_RESULT - $BENCH_RESULT) * 100 / $BENCH_RESULT" | bc)
        
        # Display results
        echo "  Plain:  $BENCH_RESULT ps"
        echo "  tmux:   $BENCH_TMUX_RESULT ps"
        
        # Determine if tmux is faster or slower
        if (( $(echo "$BENCH_TMUX_RESULT < $BENCH_RESULT" | bc -l) )); then
            echo "  Impact: tmux is ${BENCH_RATIO}x faster (${BENCH_PERCENT#-}% improvement)"
        else
            echo "  Impact: tmux is ${BENCH_RATIO}x slower (${BENCH_PERCENT}% overhead)"
        fi
        
        # Extract statistical significance information
        CHANGE_LINE=$(grep "change:" "${PROJ_DIR}/cargo_bench_tmux.log")
        if [[ -n "$CHANGE_LINE" ]]; then
            if echo "$CHANGE_LINE" | grep -q "No change in performance detected"; then
                echo "  Statistical Analysis: No statistically significant difference detected"
            elif echo "$CHANGE_LINE" | grep -q "Performance has regressed"; then
                echo "  Statistical Analysis: Performance has regressed (statistically significant)"
            elif echo "$CHANGE_LINE" | grep -q "Performance has improved"; then
                echo "  Statistical Analysis: Performance has improved (statistically significant)"
            elif echo "$CHANGE_LINE" | grep -q "Change within noise threshold"; then
                echo "  Statistical Analysis: Change within noise threshold (not significant)"
            else
                echo "  Statistical Analysis: Change detected in measurements"
            fi
        else
            echo "  Statistical Analysis: No change data available"
        fi
    else
        echo "  Error extracting benchmark values from logs"
        echo "  Plain log line: $BENCH_LINE" 
        echo "  tmux log line: $BENCH_TMUX_LINE"
    fi
else
    echo "  Benchmark log files not found"
fi

echo -e "\nSummary:"
# Generate process startup overhead conclusion based on simple program execution results
if [[ "$PLAIN_TIME" != "NA" && "$TMUX_TIME" != "NA" ]]; then
    if (( $(echo "$RATIO > 2" | bc -l) )); then
        echo "  1. Process startup overhead: tmux introduces significant overhead (${RATIO}x slower) for short-running tasks"
    elif (( $(echo "$RATIO > 1" | bc -l) )); then
        echo "  1. Process startup overhead: tmux introduces moderate overhead (${RATIO}x slower) for short-running tasks"
    else 
        echo "  1. Process startup overhead: tmux does not introduce significant overhead for short-running tasks"
    fi
else
    echo "  1. Process startup overhead: Could not determine (insufficient data)"
fi

# Generate computation performance conclusion based on microbenchmark results
if [[ "$BENCH_RESULT" =~ ^[0-9.]+$ ]] && [[ "$BENCH_TMUX_RESULT" =~ ^[0-9.]+$ ]]; then
    if (( $(echo "($BENCH_TMUX_RESULT - $BENCH_RESULT) / $BENCH_RESULT * 100 < 5 && ($BENCH_TMUX_RESULT - $BENCH_RESULT) / $BENCH_RESULT * 100 > -5" | bc -l) )); then
        echo "  2. Computation performance: tmux has minimal impact (${BENCH_PERCENT}%) on pure computational workloads"
    elif (( $(echo "$BENCH_TMUX_RESULT < $BENCH_RESULT" | bc -l) )); then
        echo "  2. Computation performance: tmux shows improved performance (${BENCH_PERCENT#-}% faster) on computational workloads"
    else
        echo "  2. Computation performance: tmux shows decreased performance (${BENCH_PERCENT}% slower) on computational workloads"
    fi
else
    echo "  2. Computation performance: Could not determine (insufficient data)"
fi

# Generate detached mode conclusion
if [[ "$TMUX_DETACHED_TIME" != "NA" && "$TMUX_TIME" != "NA" ]]; then
    if (( $(echo "$TMUX_VS_DETACHED > 10" | bc -l) )); then
        echo "  3. Detached mode: Regular tmux is dramatically slower (${TMUX_VS_DETACHED}x) than detached mode for short tasks"
    elif (( $(echo "$TMUX_VS_DETACHED > 1.5" | bc -l) )); then
        echo "  3. Detached mode: Regular tmux is significantly slower (${TMUX_VS_DETACHED}x) than detached mode"
    elif (( $(echo "$TMUX_VS_DETACHED < 0.9" | bc -l) )); then
        echo "  3. Detached mode: Regular tmux is actually faster than detached mode for this workload"
    else
        echo "  3. Detached mode: Regular tmux and detached mode perform similarly for this workload"
    fi
else
    echo "  3. Detached mode: Could not determine (insufficient data)"
fi

# Generate recommendation based on results
if [[ "$PLAIN_TIME" != "NA" && "$TMUX_TIME" != "NA" && "$BENCH_RESULT" =~ ^[0-9.]+$ && "$BENCH_TMUX_RESULT" =~ ^[0-9.]+$ ]]; then
    echo "  4. Recommendation:"
    
    # For short-lived processes
    if (( $(echo "$RATIO > 1.2" | bc -l) )); then
        echo "     - Avoid using tmux for benchmarking short-lived processes (${PERCENT_SLOWER}% overhead)"
    else
        echo "     - Tmux has minimal impact on short-lived processes in this environment"
    fi
    
    # For computational workloads
    if (( $(echo "($BENCH_TMUX_RESULT - $BENCH_RESULT) / $BENCH_RESULT * 100 < 5 && ($BENCH_TMUX_RESULT - $BENCH_RESULT) / $BENCH_RESULT * 100 > -5" | bc -l) )); then
        echo "     - Tmux is acceptable for long-running computational tasks (${BENCH_PERCENT}% difference)"
    elif (( $(echo "$BENCH_TMUX_RESULT < $BENCH_RESULT" | bc -l) )); then
        echo "     - Tmux may actually improve performance for certain computational workloads"
    else
        echo "     - Consider the impact of tmux (${BENCH_PERCENT}% overhead) even for computational workloads"
    fi
    
    # For detached mode
    if [[ "$TMUX_DETACHED_TIME" != "NA" ]]; then
        if (( $(echo "$TMUX_VS_DETACHED > 1.2" | bc -l) )); then
            echo "     - Detached tmux mode is recommended if tmux must be used (${TMUX_VS_DETACHED}x better performance)"
        fi
    fi
else
    echo "  4. Recommendation: Could not determine (insufficient data)"
fi

echo -e "\nResults written to $(realpath "${RESULTS}")"
