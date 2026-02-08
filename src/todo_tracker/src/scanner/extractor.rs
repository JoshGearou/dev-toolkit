use anyhow::Result;
use once_cell::sync::Lazy;
use rayon::prelude::*;
use regex::Regex;
use std::collections::HashMap;
use std::path::{Path, PathBuf};

use crate::config::Config;
use crate::model::priority::Priority;
use crate::model::todo::{TodoItem, TodoMetadata, TodoTag};

use super::comment::CommentSyntax;

/// Regex for matching TODO-style tags with optional metadata.
///
/// Matches patterns like:
///   TODO: message
///   TODO(author): message
///   FIXME(JIRA-1234): message
///   HACK(P0, rerickso): message
static TODO_PATTERN: Lazy<Regex> = Lazy::new(|| {
    Regex::new(
        r"(?x)
        \b(?P<tag>TODO|FIXME|HACK|XXX|BUG|NOTE|OPTIMIZE|SAFETY)\b
        (?:\((?P<meta>[^)]*)\))?   # optional parenthesized metadata
        (?:\[(?P<ref>[^\]]*)\])?   # optional bracketed reference
        \s*[:>\-]?\s*              # optional separator
        (?P<message>.+?)           # the message (non-greedy)
        \s*$                       # trailing whitespace
    ",
    )
    .expect("TODO_PATTERN regex must compile")
});

/// Regex for extracting ticket references (e.g., JIRA-123, GH-456).
static TICKET_PATTERN: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"(?P<ticket>[A-Z]{2,10}-\d+)").expect("TICKET_PATTERN regex must compile")
});

/// Extract TODO items from a list of files in parallel.
pub fn extract_from_files(files: &[PathBuf], config: &Config) -> Result<Vec<TodoItem>> {
    let results: Vec<Vec<TodoItem>> = files
        .par_iter()
        .filter_map(|path| match extract_from_file(path, config) {
            Ok(items) if !items.is_empty() => Some(items),
            Ok(_) => None,
            Err(_) => None, // skip unreadable files silently
        })
        .collect();

    let mut items: Vec<TodoItem> = results.into_iter().flatten().collect();
    items.sort_by(|a, b| a.file.cmp(&b.file).then(a.line.cmp(&b.line)));
    Ok(items)
}

/// Extract TODO items from a single file.
fn extract_from_file(path: &Path, config: &Config) -> Result<Vec<TodoItem>> {
    let content = read_file_contents(path)?;
    let ext = path.extension().and_then(|e| e.to_str()).unwrap_or("");
    let syntax = CommentSyntax::for_extension(ext);

    let repo_root = config.repo_root.as_deref().unwrap_or(Path::new("."));
    let relative_path = path.strip_prefix(repo_root).unwrap_or(path);

    extract_todos(relative_path, &content, &syntax)
}

/// Read file contents, skipping binary files.
fn read_file_contents(path: &Path) -> Result<String> {
    let bytes = std::fs::read(path)?;

    // Binary check: look for null bytes in first 8KB
    let check_len = bytes.len().min(8192);
    if bytes[..check_len].contains(&0) {
        return Ok(String::new());
    }

    Ok(String::from_utf8_lossy(&bytes).into_owned())
}

/// Extract TODO items from file content using regex matching.
fn extract_todos(
    relative_path: &Path,
    content: &str,
    _syntax: &CommentSyntax,
) -> Result<Vec<TodoItem>> {
    let mut items = Vec::new();
    // Track occurrences per (tag, message) for stable ID generation
    let mut occurrence_counts: HashMap<(String, String), u32> = HashMap::new();

    for (line_idx, line) in content.lines().enumerate() {
        if let Some(caps) = TODO_PATTERN.captures(line) {
            let tag_str = caps.name("tag").map(|m| m.as_str()).unwrap_or("TODO");
            let tag = match TodoTag::parse(tag_str) {
                Some(t) => t,
                None => continue,
            };

            let message = caps
                .name("message")
                .map(|m| m.as_str().to_string())
                .unwrap_or_default();

            let meta = caps.name("meta").map(|m| m.as_str()).unwrap_or("");
            let bracket_ref = caps.name("ref").map(|m| m.as_str()).unwrap_or("");

            let metadata = parse_metadata(meta, bracket_ref, &message);

            let column = caps.name("tag").map(|m| m.start() as u32).unwrap_or(0);

            // Compute occurrence index for stable ID
            let key = (tag_str.to_string(), message.clone());
            let occurrence = occurrence_counts.entry(key).or_insert(0);
            let id = TodoItem::generate_id(relative_path, &tag, &message, *occurrence);
            *occurrence += 1;

            items.push(TodoItem {
                id,
                tag,
                file: relative_path.to_path_buf(),
                line: (line_idx + 1) as u32,
                column,
                message,
                metadata,
            });
        }
    }

    Ok(items)
}

/// Parse metadata from the parenthesized and bracketed portions of a TODO comment.
fn parse_metadata(meta: &str, bracket_ref: &str, message: &str) -> TodoMetadata {
    let mut metadata = TodoMetadata::default();

    // Extract tickets from all available text
    let combined = format!("{meta} {bracket_ref} {message}");
    metadata.tickets = TICKET_PATTERN
        .captures_iter(&combined)
        .map(|c| c["ticket"].to_string())
        .collect();

    // Parse parenthesized metadata: could be author, priority, ticket, or combination
    if !meta.is_empty() {
        for part in meta.split(',').map(|s| s.trim()) {
            if let Some(priority) = Priority::parse(part) {
                metadata.priority = Some(priority);
            } else if TICKET_PATTERN.is_match(part) {
                // Already captured above
            } else if part.starts_with('@') {
                metadata.author = Some(part.trim_start_matches('@').to_string());
            } else if !part.is_empty() {
                // Assume it is an author name if no other match
                if metadata.author.is_none() {
                    metadata.author = Some(part.to_string());
                }
            }
        }
    }

    // Bracket ref as a ticket
    if !bracket_ref.is_empty() && TICKET_PATTERN.is_match(bracket_ref) {
        // Already captured in combined extraction
    }

    metadata
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn extracts_simple_todo() {
        let content = "// TODO: fix this bug\n";
        let syntax = CommentSyntax::for_extension("rs");
        let items = extract_todos(Path::new("test.rs"), content, &syntax).unwrap();
        assert_eq!(items.len(), 1);
        assert_eq!(items[0].tag, TodoTag::Todo);
        assert_eq!(items[0].message, "fix this bug");
        assert_eq!(items[0].line, 1);
    }

    #[test]
    fn extracts_todo_with_author() {
        let content = "# TODO(rerickso): refactor this\n";
        let syntax = CommentSyntax::for_extension("py");
        let items = extract_todos(Path::new("test.py"), content, &syntax).unwrap();
        assert_eq!(items.len(), 1);
        assert_eq!(items[0].metadata.author.as_deref(), Some("rerickso"));
    }

    #[test]
    fn extracts_todo_with_ticket() {
        let content = "// FIXME(JIRA-1234): null pointer on empty list\n";
        let syntax = CommentSyntax::for_extension("rs");
        let items = extract_todos(Path::new("test.rs"), content, &syntax).unwrap();
        assert_eq!(items.len(), 1);
        assert_eq!(items[0].tag, TodoTag::Fixme);
        assert!(items[0].metadata.tickets.contains(&"JIRA-1234".to_string()));
    }

    #[test]
    fn extracts_multiple_tags() {
        let content = "// TODO: first\n// FIXME: second\n// HACK: third\n";
        let syntax = CommentSyntax::for_extension("rs");
        let items = extract_todos(Path::new("test.rs"), content, &syntax).unwrap();
        assert_eq!(items.len(), 3);
        assert_eq!(items[0].tag, TodoTag::Todo);
        assert_eq!(items[1].tag, TodoTag::Fixme);
        assert_eq!(items[2].tag, TodoTag::Hack);
    }

    #[test]
    fn skips_lines_without_tags() {
        let content = "fn main() {\n    println!(\"hello\");\n}\n";
        let syntax = CommentSyntax::for_extension("rs");
        let items = extract_todos(Path::new("test.rs"), content, &syntax).unwrap();
        assert!(items.is_empty());
    }

    #[test]
    fn extracts_priority() {
        let content = "// TODO(P0, rerickso): critical fix needed\n";
        let syntax = CommentSyntax::for_extension("rs");
        let items = extract_todos(Path::new("test.rs"), content, &syntax).unwrap();
        assert_eq!(items.len(), 1);
        assert_eq!(items[0].metadata.priority, Some(Priority::Critical));
        assert_eq!(items[0].metadata.author.as_deref(), Some("rerickso"));
    }
}
