use anyhow::Result;
use ignore::WalkBuilder;
use std::path::{Path, PathBuf};
use std::sync::Mutex;

use crate::config::Config;

/// Walk the file tree from `root`, respecting .gitignore and config exclusions.
/// Returns a list of file paths to scan.
pub fn walk_files(root: &Path, config: &Config) -> Result<Vec<PathBuf>> {
    let files: Mutex<Vec<PathBuf>> = Mutex::new(Vec::new());

    let walker = WalkBuilder::new(root)
        .hidden(true)
        .git_ignore(true)
        .git_global(true)
        .git_exclude(true)
        .threads(num_cpus())
        .build_parallel();

    walker.run(|| {
        Box::new(|entry| {
            let entry = match entry {
                Ok(e) => e,
                Err(_) => return ignore::WalkState::Continue,
            };

            if !entry.file_type().is_some_and(|ft| ft.is_file()) {
                return ignore::WalkState::Continue;
            }

            let path = entry.path();
            if !should_scan(path, config) {
                return ignore::WalkState::Continue;
            }

            if let Ok(mut locked) = files.lock() {
                locked.push(path.to_path_buf());
            }

            ignore::WalkState::Continue
        })
    });

    let result = files
        .into_inner()
        .map_err(|e| anyhow::anyhow!("lock poisoned: {e}"))?;
    Ok(result)
}

/// Check if a file should be scanned based on config exclude/include patterns.
fn should_scan(path: &Path, config: &Config) -> bool {
    let path_str = path.to_string_lossy();

    // Check excludes
    for pattern in &config.exclude {
        if glob_match(pattern, &path_str) {
            return false;
        }
    }

    // If include patterns are set, file must match at least one
    if let Some(ref includes) = config.include {
        if !includes.is_empty() {
            return includes.iter().any(|p| glob_match(p, &path_str));
        }
    }

    true
}

/// Simple glob matching. For production use, consider the `glob` crate.
fn glob_match(pattern: &str, path: &str) -> bool {
    // Handle ** and * patterns
    if pattern.contains("**") {
        let parts: Vec<&str> = pattern.split("**").collect();
        if parts.len() == 2 {
            let prefix = parts[0].trim_end_matches('/');
            let suffix = parts[1].trim_start_matches('/');
            if prefix.is_empty() && suffix.is_empty() {
                return true;
            }
            if !prefix.is_empty() && !path.contains(prefix) {
                return false;
            }
            if !suffix.is_empty() && !path.ends_with(suffix) {
                return false;
            }
            return true;
        }
    }

    // Simple wildcard: *.ext
    if let Some(ext) = pattern.strip_prefix("*.") {
        return path.ends_with(&format!(".{ext}"));
    }

    // Direct substring match as fallback
    path.contains(pattern)
}

/// Return available CPU count for parallel walking, defaulting to 4.
fn num_cpus() -> usize {
    std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(4)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn glob_match_extension() {
        assert!(glob_match("*.min.js", "dist/bundle.min.js"));
        assert!(!glob_match("*.min.js", "src/app.js"));
    }

    #[test]
    fn glob_match_double_star() {
        assert!(glob_match("vendor/**", "/repo/vendor/lib/foo.rs"));
        assert!(!glob_match("vendor/**", "/repo/src/main.rs"));
    }
}
