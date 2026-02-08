use chrono::{DateTime, NaiveDate, Utc};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

use super::priority::Priority;

/// A single TODO comment found in the codebase.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TodoItem {
    /// Stable identifier: hash of (file_path + content + tag + occurrence_index).
    /// Line numbers are not part of identity because they shift on edits.
    pub id: String,

    /// The tag type (TODO, FIXME, HACK, etc.)
    pub tag: TodoTag,

    /// File path relative to repository root
    pub file: PathBuf,

    /// Line number (1-indexed), for display only
    pub line: u32,

    /// Column where the tag starts (0-indexed)
    pub column: u32,

    /// The comment text after the tag and separator
    pub message: String,

    /// Structured metadata extracted from the comment
    pub metadata: TodoMetadata,
}

/// The tag type for a TODO comment.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum TodoTag {
    /// Standard TODO marker.
    Todo,
    /// Fix me marker for bugs.
    Fixme,
    /// Hack marker for temporary workarounds.
    Hack,
    /// XXX marker for attention needed.
    Xxx,
    /// Bug marker for known issues.
    Bug,
    /// Note marker for informational comments.
    Note,
    /// Optimize marker for performance improvements.
    Optimize,
    /// Safety marker for unsafe code concerns.
    Safety,
}

impl TodoTag {
    /// Parse a tag string into a TodoTag variant.
    /// Returns None for unrecognized tags.
    pub fn parse(s: &str) -> Option<Self> {
        match s.to_uppercase().as_str() {
            "TODO" => Some(Self::Todo),
            "FIXME" => Some(Self::Fixme),
            "HACK" => Some(Self::Hack),
            "XXX" => Some(Self::Xxx),
            "BUG" => Some(Self::Bug),
            "NOTE" => Some(Self::Note),
            "OPTIMIZE" => Some(Self::Optimize),
            "SAFETY" => Some(Self::Safety),
            _ => None,
        }
    }

    /// Return the tag as an uppercase string.
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Todo => "TODO",
            Self::Fixme => "FIXME",
            Self::Hack => "HACK",
            Self::Xxx => "XXX",
            Self::Bug => "BUG",
            Self::Note => "NOTE",
            Self::Optimize => "OPTIMIZE",
            Self::Safety => "SAFETY",
        }
    }

    /// Severity rank for sorting. Lower number = higher severity.
    #[allow(dead_code)]
    pub fn severity_rank(&self) -> u8 {
        match self {
            Self::Fixme => 0,
            Self::Bug => 1,
            Self::Safety => 2,
            Self::Hack => 3,
            Self::Todo => 4,
            Self::Optimize => 5,
            Self::Xxx => 6,
            Self::Note => 7,
        }
    }
}

impl std::fmt::Display for TodoTag {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(self.as_str())
    }
}

/// Metadata extracted from or attached to a TODO item.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct TodoMetadata {
    /// Author extracted from TODO(author) or git blame
    pub author: Option<String>,

    /// Date from comment text or git blame
    pub date: Option<NaiveDate>,

    /// Ticket references: JIRA-123, GH-456, etc.
    pub tickets: Vec<String>,

    /// Priority if specified: TODO(P0), TODO(high)
    pub priority: Option<Priority>,

    /// Git blame information (populated on demand, not during scan)
    pub blame: Option<BlameInfo>,
}

/// Git blame information for a TODO item.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BlameInfo {
    /// Author name from git.
    pub author: String,
    /// Author email from git.
    pub email: String,
    /// Commit SHA where this line was last changed.
    pub commit: String,
    /// Date of the commit.
    pub date: DateTime<Utc>,
}

impl TodoItem {
    /// Generate a stable ID from file path, content, tag, and occurrence index.
    pub fn generate_id(
        file: &std::path::Path,
        tag: &TodoTag,
        message: &str,
        occurrence: u32,
    ) -> String {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};

        let mut hasher = DefaultHasher::new();
        file.hash(&mut hasher);
        tag.as_str().hash(&mut hasher);
        message.hash(&mut hasher);
        occurrence.hash(&mut hasher);
        format!("{:016x}", hasher.finish())
    }
}
