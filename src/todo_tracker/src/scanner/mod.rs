/// Comment syntax definitions per language.
pub mod comment;
/// TODO extraction logic from file contents.
pub mod extractor;
/// File system walking with gitignore support.
pub mod walker;

use anyhow::Result;
use std::path::Path;

use crate::config::Config;
use crate::model::TodoItem;

/// Scan a repository for TODO comments.
/// Orchestrates walking, filtering, and extraction.
pub fn scan_repository(root: &Path, config: &Config) -> Result<Vec<TodoItem>> {
    let files = walker::walk_files(root, config)?;
    let items = extractor::extract_from_files(&files, config)?;
    Ok(items)
}
