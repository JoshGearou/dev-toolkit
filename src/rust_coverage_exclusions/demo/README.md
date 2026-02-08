# Coverage Demo

This demo project illustrates different coverage scenarios in Rust:

## Functions Demonstrated

1. **`covered_function`** - A function that is tested and should show good coverage
2. **`uncovered_function`** - A function that is NOT tested and should show 0% coverage
3. **`excluded_nightly_function`** - A function excluded using `#[coverage(off)]` (nightly only)
4. **`excluded_stable_function`** - A function excluded using feature flags (stable Rust)

## Running the Demo

```bash
./run_demo.sh
```

This script will:
1. Set up nightly Rust
2. Run `./coverage-nightly.sh` (tests without coverage feature)
3. Generate coverage reports showing nightly exclusion behavior
4. Switch to stable Rust
5. Run `./coverage.sh` (tests with `--features coverage` flag)
6. Generate coverage reports showing stable exclusion behavior
7. **Automatically open both reports in your browser**
8. Restore stable toolchain as default

The coverage scripts use `cargo test` and `static-analysis-tools coverage` to generate HTML reports in `build/reports/`. The demo will automatically open the reports for easy comparison.

## Expected Results

### Nightly Coverage Report
- ✅ `covered_function`: Should show good coverage (100%)
- ❌ `uncovered_function`: Should show 0% coverage  
- 🚫 `excluded_nightly_function`: Should NOT appear in report (excluded by `#[coverage(off)]`)
- ✅ `call_excluded_stable_function`: Should show coverage

### Stable Coverage Report  
- ✅ `covered_function`: Should show good coverage (100%)
- ❌ `uncovered_function`: Should show 0% coverage
- ✅ `excluded_nightly_function`: Will appear (no `#[coverage(off)]` support)
- 🚫 `excluded_stable_function`: Should NOT be compiled (excluded by feature flag)
- ✅ `call_excluded_stable_function`: Should show coverage

## Manual Commands

If you prefer to run commands manually:

### Nightly with #[coverage(off)]
```bash
rustup override set nightly
./coverage-nightly.sh
```

### Stable with feature flags
```bash
rustup override set stable  
./coverage.sh
```

Both scripts will generate HTML coverage reports in `build/reports/` and automatically open them in your browser for easy viewing and comparison.
