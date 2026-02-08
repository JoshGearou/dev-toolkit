//! Todo tracker CLI for scanning and managing TODO comments in codebases.

/// CI policy checking for TODO comments.
mod ci;
/// Command line interface structures and argument parsing.
mod cli;
/// Configuration loading and merging from files.
mod config;
/// Git integration for blame and diff support.
mod git;
/// Domain model types for TODO items and metadata.
mod model;
/// Output formatters for different display formats.
mod output;
/// File walking and TODO extraction logic.
mod scanner;
/// Storage backends for caching and persistence.
mod storage;

use anyhow::Result;
use clap::Parser;
use std::path::{Path, PathBuf};
use std::process;

use cli::{Cli, Command};
use config::{Config, OutputFormat};

fn main() {
    if let Err(e) = run() {
        eprintln!("error: {e:#}");
        process::exit(1);
    }
}

/// Main entry point for the application logic.
fn run() -> Result<()> {
    let cli = Cli::parse();

    let repo_root = find_repo_root()?;
    let mut config = Config::load(&repo_root)?;

    // Apply CLI overrides
    if let Some(fmt) = cli.format {
        config.output.format = fmt.into();
    }
    if cli.porcelain {
        config.output.format = OutputFormat::Json;
    }
    if cli.no_color {
        config.output.color = config::ColorMode::Never;
    }
    if cli.color {
        config.output.color = config::ColorMode::Always;
    }

    // Determine color behavior
    apply_color_mode(&config);

    match cli.command {
        None => cmd_list(&cli, &config, &repo_root, &[], &None),
        Some(Command::List {
            ref severity,
            ref author,
            ..
        }) => cmd_list(&cli, &config, &repo_root, severity, author),
        Some(Command::Stats { .. }) => cmd_stats(&config, &repo_root),
        Some(Command::Blame { stale, author }) => cmd_blame(&config, &repo_root, stale, author),
        Some(Command::Check { staged, diff }) => cmd_check(&config, &repo_root, staged, diff),
        Some(Command::Init { force }) => cmd_init(&repo_root, force),
    }
}

/// Execute the list command to display TODO items with optional filters.
fn cmd_list(
    cli: &Cli,
    config: &Config,
    repo_root: &Path,
    severity: &[String],
    author: &Option<String>,
) -> Result<()> {
    let mut items = scanner::scan_repository(repo_root, config)?;

    // Filter by severity/tag
    if !severity.is_empty() {
        let tags_upper: Vec<String> = severity.iter().map(|s| s.to_uppercase()).collect();
        items.retain(|item| tags_upper.contains(&item.tag.as_str().to_string()));
    }

    // Filter by author
    if let Some(ref author_filter) = author {
        items.retain(|item| {
            item.metadata
                .author
                .as_ref()
                .map(|a| a.contains(author_filter.as_str()))
                .unwrap_or(false)
        });
    }

    if cli.quiet {
        println!("{}", items.len());
        return Ok(());
    }

    let output = output::format_items(&items, config.output.format)?;
    println!("{output}");
    Ok(())
}

/// Execute the stats command to show summary counts by tag and author.
fn cmd_stats(config: &Config, repo_root: &Path) -> Result<()> {
    let items = scanner::scan_repository(repo_root, config)?;

    // Tag counts
    let mut tag_counts: std::collections::BTreeMap<&str, usize> = std::collections::BTreeMap::new();
    for item in &items {
        *tag_counts.entry(item.tag.as_str()).or_default() += 1;
    }

    println!("\n Severity    Count");
    println!(" ─────────────────");
    for (tag, count) in &tag_counts {
        println!(" {:<11} {:>5}", tag, count);
    }
    println!(" ─────────────────");
    println!(" Total       {:>5}", items.len());

    // Author counts
    let mut author_counts: std::collections::BTreeMap<String, usize> =
        std::collections::BTreeMap::new();
    for item in &items {
        let author = item
            .metadata
            .author
            .as_deref()
            .unwrap_or("unknown")
            .to_string();
        *author_counts.entry(author).or_default() += 1;
    }

    if !author_counts.is_empty() {
        println!("\n By Author");
        println!(" ─────────────────");
        for (author, count) in &author_counts {
            println!(" {:<15} {:>5}", author, count);
        }
    }

    println!();
    Ok(())
}

/// Execute the blame command to show git blame info for TODOs.
fn cmd_blame(
    config: &Config,
    repo_root: &Path,
    stale: Option<u32>,
    author: Option<String>,
) -> Result<()> {
    let mut items = scanner::scan_repository(repo_root, config)?;

    // Enrich with blame data
    git::blame::enrich_with_blame(&mut items, repo_root)?;

    // Filter by author if specified
    if let Some(ref author_filter) = author {
        items.retain(|item| {
            item.metadata
                .author
                .as_ref()
                .map(|a| a.contains(author_filter.as_str()))
                .unwrap_or(false)
        });
    }

    // Filter by stale threshold if specified
    if let Some(stale_days) = stale {
        let now = chrono::Utc::now();
        items.retain(|item| {
            item.metadata
                .blame
                .as_ref()
                .map(|b| {
                    let age = now.signed_duration_since(b.date).num_days();
                    age > stale_days as i64
                })
                .unwrap_or(false)
        });
    }

    let output = output::format_items(&items, config.output.format)?;
    println!("{output}");
    Ok(())
}

/// Execute the check command to validate TODOs against CI policies.
fn cmd_check(
    config: &Config,
    repo_root: &Path,
    _staged: bool,
    _diff: Option<String>,
) -> Result<()> {
    let items = scanner::scan_repository(repo_root, config)?;
    let result = ci::check(&items, config);

    let output = ci::format_check_result(&result);
    println!("{output}");

    if !result.passed {
        process::exit(1);
    }
    Ok(())
}

/// Execute the init command to create a default config file.
fn cmd_init(repo_root: &Path, force: bool) -> Result<()> {
    let config_path = repo_root.join(".todo-tracker.toml");
    if config_path.exists() && !force {
        anyhow::bail!(".todo-tracker.toml already exists. Use --force to overwrite.");
    }

    let default_config = include_str!("../default_config.toml");
    std::fs::write(&config_path, default_config)?;
    println!("Created {}", config_path.display());
    Ok(())
}

/// Find the repository root by checking git or falling back to current directory.
fn find_repo_root() -> Result<PathBuf> {
    // Try git root first
    let output = std::process::Command::new("git")
        .args(["rev-parse", "--show-toplevel"])
        .output();

    if let Ok(output) = output {
        if output.status.success() {
            let root = String::from_utf8_lossy(&output.stdout).trim().to_string();
            return Ok(PathBuf::from(root));
        }
    }

    // Fall back to current directory
    Ok(std::env::current_dir()?)
}

/// Apply color mode settings from config to the colored crate.
fn apply_color_mode(config: &Config) {
    match config.output.color {
        config::ColorMode::Always => colored::control::set_override(true),
        config::ColorMode::Never => colored::control::set_override(false),
        config::ColorMode::Auto => {} // colored crate auto-detects TTY
    }
}
