use serde::{Deserialize, Serialize};

/// Priority level for a TODO item.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum Priority {
    /// P0 level priority.
    Critical, // P0
    /// P1 level priority.
    High, // P1
    /// P2 level priority.
    Medium, // P2
    /// P3 level priority.
    Low, // P3
}

impl Priority {
    /// Parse priority from common notations: P0, P1, critical, high, etc.
    pub fn parse(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "p0" | "critical" | "urgent" | "blocker" => Some(Self::Critical),
            "p1" | "high" => Some(Self::High),
            "p2" | "medium" => Some(Self::Medium),
            "p3" | "low" => Some(Self::Low),
            _ => None,
        }
    }

    /// Return the priority as a lowercase string.
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Critical => "critical",
            Self::High => "high",
            Self::Medium => "medium",
            Self::Low => "low",
        }
    }
}

impl std::fmt::Display for Priority {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(self.as_str())
    }
}
