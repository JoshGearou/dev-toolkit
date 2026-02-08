use clap::{Parser, Subcommand, ValueEnum};
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(
    name = "todo",
    about = "Track TODO comments across your codebase",
    version,
    after_help = "Examples:\n  \
        todo                        List all TODOs\n  \
        todo list --severity FIXME  Show only FIXMEs\n  \
        todo stats                  Summary counts\n  \
        todo check                  CI policy check (exit non-zero on violations)\n  \
        todo blame --stale 60       Show blame for stale TODOs"
)]
/// Top-level CLI structure with global flags and subcommands.
pub struct Cli {
    /// Subcommand to execute (defaults to list if not provided).
    #[command(subcommand)]
    pub command: Option<Command>,

    /// Paths to scan (defaults to current directory)
    #[arg(global = true)]
    pub paths: Vec<PathBuf>,

    /// Output format
    #[arg(short, long, global = true, value_enum)]
    pub format: Option<Format>,

    /// Disable color output
    #[arg(long, global = true)]
    pub no_color: bool,

    /// Force color output
    #[arg(long, global = true)]
    pub color: bool,

    /// Machine-readable output (stable format for scripts)
    #[arg(long, global = true)]
    pub porcelain: bool,

    /// Suppress output, exit code only
    #[arg(short, long, global = true)]
    pub quiet: bool,
}

#[derive(Subcommand, Debug)]
pub enum Command {
    /// List TODO comments (default when no subcommand given)
    List {
        /// Filter by tag severity
        #[arg(short, long)]
        severity: Vec<String>,

        /// Filter by author (from comment metadata or git blame)
        #[arg(short, long)]
        author: Option<String>,

        /// Filter by file glob pattern
        #[arg(short = 'F', long)]
        file: Option<String>,

        /// Filter by language (file extension)
        #[arg(long)]
        lang: Option<String>,

        /// Show only TODOs older than N days
        #[arg(long)]
        stale: Option<u32>,

        /// Show only TODOs introduced since this git ref
        #[arg(long)]
        since: Option<String>,

        /// Show only TODOs added in diff against this ref
        #[arg(long)]
        diff: Option<String>,

        /// Show only TODOs on current branch vs main
        #[arg(long)]
        branch: bool,

        /// Show only your TODOs (uses git config user.name)
        #[arg(long)]
        mine: bool,
    },

    /// Show summary statistics
    Stats {
        /// Compare against a git ref
        #[arg(long)]
        compare: Option<String>,

        /// Show only TODOs in diff against this ref
        #[arg(long)]
        diff: Option<String>,
    },

    /// Show git blame information for TODOs
    Blame {
        /// Show only TODOs older than N days
        #[arg(long)]
        stale: Option<u32>,

        /// Filter by author
        #[arg(short, long)]
        author: Option<String>,
    },

    /// Run CI policy checks (exit non-zero on violations)
    Check {
        /// Only check staged files
        #[arg(long)]
        staged: bool,

        /// Only check TODOs in diff against this ref
        #[arg(long)]
        diff: Option<String>,
    },

    /// Initialize a .todo-tracker.toml config file
    Init {
        /// Overwrite existing config
        #[arg(long)]
        force: bool,
    },
}

/// Output format options for displaying TODO items.
#[derive(Debug, Clone, Copy, ValueEnum)]
pub enum Format {
    /// Human-readable table format.
    Table,
    /// JSON format for machine parsing.
    Json,
    /// CSV format for spreadsheet import.
    Csv,
    /// Markdown format for documentation.
    Markdown,
    /// SARIF format for CI integration.
    Sarif,
    /// Simple count of items.
    Count,
}

impl From<Format> for crate::config::OutputFormat {
    fn from(f: Format) -> Self {
        match f {
            Format::Table => Self::Table,
            Format::Json => Self::Json,
            Format::Csv => Self::Csv,
            Format::Markdown => Self::Markdown,
            Format::Sarif => Self::Sarif,
            Format::Count => Self::Count,
        }
    }
}
