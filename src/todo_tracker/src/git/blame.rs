use anyhow::Result;
use std::path::Path;

use crate::model::todo::{BlameInfo, TodoItem};

/// Enrich TODO items with git blame information.
///
/// This is expensive: runs blame per file. Only call on demand
/// (e.g., `todo blame` subcommand), never during the default scan.
pub fn enrich_with_blame(items: &mut [TodoItem], repo_root: &Path) -> Result<()> {
    // Group indices by file to minimize blame invocations
    let mut by_file: std::collections::HashMap<std::path::PathBuf, Vec<usize>> =
        std::collections::HashMap::new();
    for (idx, item) in items.iter().enumerate() {
        by_file.entry(item.file.clone()).or_default().push(idx);
    }

    for (file, indices) in by_file {
        let full_path = repo_root.join(&file);
        match blame_file(&full_path) {
            Ok(blame_lines) => {
                for idx in indices {
                    let line = items[idx].line as usize;
                    if let Some(info) = blame_lines.get(line.saturating_sub(1)) {
                        items[idx].metadata.blame = Some(info.clone());
                        // Backfill author from blame if not set from comment metadata
                        if items[idx].metadata.author.is_none() {
                            items[idx].metadata.author = Some(info.author.clone());
                        }
                    }
                }
            }
            Err(_) => {
                // Skip files that can't be blamed (new files, not in git, etc.)
                continue;
            }
        }
    }

    Ok(())
}

/// Run git blame on a single file and return per-line BlameInfo.
///
/// Uses `git blame --porcelain` via process invocation.
/// Future: replace with gix for pure-Rust implementation.
fn blame_file(path: &Path) -> Result<Vec<BlameInfo>> {
    let output = std::process::Command::new("git")
        .args(["blame", "--porcelain"])
        .arg(path)
        .output()?;

    if !output.status.success() {
        anyhow::bail!(
            "git blame failed for {}: {}",
            path.display(),
            String::from_utf8_lossy(&output.stderr)
        );
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    parse_porcelain_blame(&stdout)
}

/// Parse `git blame --porcelain` output into per-line BlameInfo.
fn parse_porcelain_blame(output: &str) -> Result<Vec<BlameInfo>> {
    let mut results: Vec<BlameInfo> = Vec::new();
    let mut current_commit = String::new();
    let mut current_author = String::new();
    let mut current_email = String::new();
    let mut current_timestamp: i64 = 0;

    for line in output.lines() {
        if line.len() >= 40 && line.chars().take(40).all(|c| c.is_ascii_hexdigit()) {
            // Commit line: <sha> <orig_line> <final_line> [<num_lines>]
            let parts: Vec<&str> = line.split_whitespace().collect();
            if !parts.is_empty() {
                current_commit = parts[0].to_string();
            }
        } else if let Some(author) = line.strip_prefix("author ") {
            current_author = author.to_string();
        } else if let Some(email) = line.strip_prefix("author-mail ") {
            current_email = email.trim_matches(|c| c == '<' || c == '>').to_string();
        } else if let Some(time) = line.strip_prefix("author-time ") {
            current_timestamp = time.parse().unwrap_or(0);
        } else if line.starts_with('\t') {
            // Content line signals end of a blame entry
            let date = chrono::DateTime::from_timestamp(current_timestamp, 0).unwrap_or_default();
            results.push(BlameInfo {
                author: current_author.clone(),
                email: current_email.clone(),
                commit: current_commit.clone(),
                date,
            });
        }
    }

    Ok(results)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_empty_blame() {
        let results = parse_porcelain_blame("").unwrap();
        assert!(results.is_empty());
    }
}
