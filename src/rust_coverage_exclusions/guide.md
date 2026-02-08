````markdown
# Guide: Excluding Specific Functions from Rust Code Coverage

This guide walks through how to **exclude specific functions** (like `test_mock_foo`) from coverage reports using Rust's `-C instrument-coverage` and `llvm-cov`. It covers both nightly and stable methods and explains how to avoid common pitfalls.

---

## ✅ Recommended: Use `#[coverage(off)]` (Nightly Only)

### 1. Switch to nightly
```bash
rustup override set nightly
````

### 2. Enable the unstable attribute in crate root

```rust
#![feature(coverage_attribute)]
```

### 3. Exclude your function

```rust
#[coverage(off)]
fn test_mock_foo() {
    // This will not be instrumented or appear in reports
}
```

### 4. Run tests with instrumentation

```bash
RUSTFLAGS="-C instrument-coverage" \
LLVM_PROFILE_FILE="build/coverage/%p-%m.profraw" \
cargo test
```

### 5. Generate report

```bash
llvm-profdata merge -sparse build/coverage/*.profraw -o build/coverage/merged.profdata
llvm-cov show \
  target/debug/<your_binary> \
  -instr-profile=build/coverage/merged.profdata \
  --show-line-counts-or-regions
```

> ✅ `test_mock_foo` will be excluded entirely.

---

## ✅ Alternative: Use Feature Flags (Stable Rust)

### 1. Define the feature in `Cargo.toml`

```toml
[features]
coverage = []
```

### 2. Wrap your function in a `#[cfg(not(feature = "coverage"))]`

```rust
#[cfg(not(feature = "coverage"))]
fn test_mock_foo() {
    // This function will not be compiled when the "coverage" feature is enabled
}
```

### 3. Run tests with the coverage feature enabled

```bash
RUSTFLAGS="-C instrument-coverage" \
LLVM_PROFILE_FILE="build/coverage/%p-%m.profraw" \
cargo test --features coverage
```

> ✅ `test_mock_foo` will not be compiled or instrumented.

---

## 🧪 Sanity Checks

### A. Ensure the feature is active

```bash
cargo rustc --features coverage -- --print cfg | grep coverage
```

You should see:

```
feature="coverage"
```

### B. Add a compile-time check to verify gating works

```rust
#[cfg(feature = "coverage")]
compile_error!("coverage feature is ON");
```

---

## 🧠 Common Pitfalls

| Issue                                            | Explanation                                  | Fix                                                |
| ------------------------------------------------ | -------------------------------------------- | -------------------------------------------------- |
| `foo` still shows in report                      | Feature wasn't propagated to the crate       | Use `-p your_crate` or update `[dev-dependencies]` |
| `foo` called from other code                     | Call sites may force function to be retained | Guard both function and its uses                   |
| Mixed `--cfg coverage` and `--features coverage` | These are **not** the same                   | Use one method only                                |
| Function inlined                                 | Optimizer retains inlined function           | Add `-C opt-level=0 -C inline-threshold=0`         |

---

## 🔧 Integration Test Gotchas

If your function is in a crate that’s used as a dev-dependency (e.g. in `tests/`), Cargo won’t apply `--features coverage` unless you declare:

```toml
[dev-dependencies.your_crate]
path = "../your_crate"
features = ["coverage"]
```

Or run:

```bash
cargo test -p your_crate --features coverage
```

---

## 🧹 (Optional) Filter from Report Output

If a function is still present but you want to hide it from the report:

```bash
llvm-cov show \
  -instr-profile=build/coverage/merged.profdata \
  -object=target/debug/<your_binary> \
  -name-regex='^(?!.*test_mock_foo).*$'
```

> 🚫 This does not stop instrumentation — only filters output.

---

## ✅ Summary

| Method                       | Instrumented? | In Report? | Notes                 |
| ---------------------------- | ------------- | ---------- | --------------------- |
| `#[coverage(off)]`           | ❌             | ❌          | ✅ Best (nightly only) |
| `#[cfg(not(feature = ...))]` | ❌             | ❌          | ✅ Stable & reliable   |
| `#[ignore]` only             | ✅             | ✅          | ⚠️ Still instrumented |
| `--name-regex` filter        | ✅             | ❌          | ⚠️ Cosmetic only      |

---

## 🚀 Recommendation

* Use `#[coverage(off)]` on nightly Rust.
* Use `#[cfg(not(feature = "coverage"))]` and run with `--features coverage` on stable Rust.
* Never rely on `#[ignore]` alone — the function is still compiled and instrumented.
* Always verify feature propagation and optimization flags when debugging.

---

```
```
