use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

/// Top-level configuration.
/// Loaded from .todo-tracker.toml, with defaults for all fields.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(default)]
pub struct Config {
    /// Tags to scan for (case-insensitive)
    pub tags: Vec<String>,

    /// Additional custom tags beyond built-in set
    pub custom_tags: Vec<String>,

    /// Path patterns to exclude (in addition to .gitignore)
    pub exclude: Vec<String>,

    /// If set, only scan paths matching these patterns
    pub include: Option<Vec<String>>,

    /// Days before a TODO is considered stale
    pub stale_days: u32,

    /// Regex for extracting ticket references
    pub ticket_pattern: String,

    /// Output configuration
    pub output: OutputConfig,

    /// Storage configuration
    pub storage: StorageConfig,

    /// CI mode configuration
    pub ci: CiConfig,

    /// Repository root (set at runtime, not from config file)
    #[serde(skip)]
    pub repo_root: Option<PathBuf>,
}

/// Output formatting configuration.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(default)]
pub struct OutputConfig {
    /// Default output format
    pub format: OutputFormat,

    /// Color mode
    pub color: ColorMode,

    /// Lines of context around each TODO
    pub context_lines: u32,

    /// Include git blame info (slower)
    pub show_blame: bool,

    /// Use paths relative to repo root
    pub relative_paths: bool,
}

/// Available output formats for displaying TODO items.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum OutputFormat {
    /// Table format.
    Table,
    /// JSON format.
    Json,
    /// CSV format.
    Csv,
    /// Markdown format.
    Markdown,
    /// SARIF format.
    Sarif,
    /// Count only.
    Count,
}

/// Color output mode for terminal display.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ColorMode {
    /// Auto-detect TTY support.
    Auto,
    /// Always output colors.
    Always,
    /// Never output colors.
    Never,
}

/// Storage backend configuration for persistence and caching.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(default)]
pub struct StorageConfig {
    /// Path to SQLite database
    pub db_path: String,

    /// Path to cache directory
    pub cache_path: String,
}

/// CI policy configuration for automated checks.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[serde(default)]
pub struct CiConfig {
    /// Fail if any stale TODOs exist
    pub fail_on_stale: bool,

    /// Fail if any FIXMEs exist
    pub fail_on_fixme: bool,

    /// Maximum total TODOs allowed (0 = no limit)
    pub max_todos: u32,

    /// Maximum stale TODOs allowed (0 = no limit)
    pub max_stale: u32,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            tags: vec![
                "TODO".into(),
                "FIXME".into(),
                "HACK".into(),
                "XXX".into(),
                "BUG".into(),
            ],
            custom_tags: vec![],
            exclude: vec![
                "vendor/**".into(),
                "node_modules/**".into(),
                "*.generated.*".into(),
                "*.pb.go".into(),
                "*.min.js".into(),
            ],
            include: None,
            stale_days: 90,
            ticket_pattern: r"[A-Z]{2,10}-\d+".into(),
            output: OutputConfig::default(),
            storage: StorageConfig::default(),
            ci: CiConfig::default(),
            repo_root: None,
        }
    }
}

impl Default for OutputConfig {
    fn default() -> Self {
        Self {
            format: OutputFormat::Table,
            color: ColorMode::Auto,
            context_lines: 0,
            show_blame: false,
            relative_paths: true,
        }
    }
}

impl Default for StorageConfig {
    fn default() -> Self {
        Self {
            db_path: ".todo-cache/todos.db".into(),
            cache_path: ".todo-cache/".into(),
        }
    }
}

impl Config {
    /// Load configuration with layered precedence:
    /// 1. Compiled defaults
    /// 2. User-level config (~/.config/todo-tracker/config.toml)
    /// 3. Project-level config (.todo-tracker.toml in repo root)
    pub fn load(repo_root: &Path) -> Result<Self> {
        let mut config = Self {
            repo_root: Some(repo_root.to_path_buf()),
            ..Default::default()
        };

        // User-level config
        if let Some(user_config_path) = user_config_path() {
            if user_config_path.exists() {
                let user_config = Self::load_from_file(&user_config_path)?;
                config.merge(user_config);
            }
        }

        // Project-level config
        let project_config_path = repo_root.join(".todo-tracker.toml");
        if project_config_path.exists() {
            let project_config = Self::load_from_file(&project_config_path)?;
            config.merge(project_config);
        }

        Ok(config)
    }

    /// Load config from a TOML file.
    fn load_from_file(path: &Path) -> Result<Self> {
        let content = std::fs::read_to_string(path)?;
        let config: Config = toml::from_str(&content)?;
        Ok(config)
    }

    /// Merge another config into this one (other takes precedence for non-default values).
    fn merge(&mut self, other: Config) {
        if other.tags != Self::default().tags {
            self.tags = other.tags;
        }
        if !other.custom_tags.is_empty() {
            self.custom_tags.extend(other.custom_tags);
        }
        if other.exclude != Self::default().exclude {
            self.exclude = other.exclude;
        }
        if other.include.is_some() {
            self.include = other.include;
        }
        if other.stale_days != Self::default().stale_days {
            self.stale_days = other.stale_days;
        }
    }
}

/// Returns the user-level config path: ~/.config/todo-tracker/config.toml
fn user_config_path() -> Option<PathBuf> {
    dirs_path().map(|d| d.join("todo-tracker").join("config.toml"))
}

/// XDG config directory or ~/.config
fn dirs_path() -> Option<PathBuf> {
    std::env::var_os("XDG_CONFIG_HOME")
        .map(PathBuf::from)
        .or_else(|| std::env::var_os("HOME").map(|h| PathBuf::from(h).join(".config")))
}
