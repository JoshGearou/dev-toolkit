// Enable coverage attribute only on nightly Rust
#![cfg_attr(feature = "nightly", feature(coverage_attribute))]

/// A function that will be covered by tests
pub fn covered_function(x: i32) -> i32 {
    if x > 0 {
        x * 2
    } else {
        0
    }
}

/// A function that will NOT be covered by tests
pub fn uncovered_function(x: i32) -> i32 {
    if x > 10 {
        x * 3
    } else {
        x + 1
    }
}

/// A function excluded from coverage using nightly #[coverage(off)]
#[cfg_attr(feature = "nightly", coverage(off))]
pub fn excluded_nightly_function(x: i32) -> i32 {
    // This function will not be instrumented for coverage
    // even if called by tests
    x * 100
}

/// A function excluded from coverage using stable feature flags
#[cfg(not(feature = "coverage"))]
pub fn excluded_stable_function(x: i32) -> i32 {
    // This function will not be compiled when coverage feature is enabled
    x * 200
}

/// A wrapper function that's always available for the stable exclusion demo
pub fn call_excluded_stable_function(x: i32) -> i32 {
    #[cfg(not(feature = "coverage"))]
    {
        excluded_stable_function(x)
    }
    #[cfg(feature = "coverage")]
    {
        // Provide a mock implementation when coverage is enabled
        x * 200 // Same behavior for demonstration
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_covered_function() {
        assert_eq!(covered_function(5), 10);
        assert_eq!(covered_function(-1), 0);
        assert_eq!(covered_function(0), 0);
    }

    #[test]
    fn test_excluded_nightly_function() {
        // This test calls the excluded function, but it won't be instrumented
        assert_eq!(excluded_nightly_function(5), 500);
    }

    #[test]
    fn test_excluded_stable_function() {
        // This test calls the wrapper which handles the exclusion logic
        assert_eq!(call_excluded_stable_function(5), 1000);
    }

    // Note: uncovered_function is intentionally not tested
    // to demonstrate uncovered code in the report
}
