//! Storage backends for TODO data persistence.

/// File fingerprint cache for incremental scanning.
pub mod cache;
/// SQLite database for TODO lifecycle tracking.
pub mod database;
