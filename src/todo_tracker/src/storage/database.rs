#![allow(dead_code)]

use anyhow::Result;
use rusqlite::Connection;
use std::path::Path;

use crate::model::TodoItem;

/// SQLite-backed storage for TODO lifecycle tracking.
pub struct Database {
    /// SQLite connection handle.
    conn: Connection,
}

impl Database {
    /// Open or create the database at the given path.
    pub fn open(path: &Path) -> Result<Self> {
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        let conn = Connection::open(path)?;
        let db = Self { conn };
        db.initialize_schema()?;
        Ok(db)
    }

    /// Open an in-memory database (for testing).
    pub fn open_in_memory() -> Result<Self> {
        let conn = Connection::open_in_memory()?;
        let db = Self { conn };
        db.initialize_schema()?;
        Ok(db)
    }

    /// Create tables and indexes if they do not already exist.
    fn initialize_schema(&self) -> Result<()> {
        self.conn.execute_batch(
            "
            CREATE TABLE IF NOT EXISTS scans (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at  TEXT NOT NULL,
                finished_at TEXT,
                commit_hash TEXT,
                total_files INTEGER,
                total_todos INTEGER
            );

            CREATE TABLE IF NOT EXISTS todos (
                id          TEXT PRIMARY KEY,
                tag         TEXT NOT NULL,
                file_path   TEXT NOT NULL,
                line        INTEGER NOT NULL,
                column_num  INTEGER NOT NULL,
                message     TEXT NOT NULL,
                author      TEXT,
                priority    TEXT,
                tickets     TEXT,
                first_seen  INTEGER NOT NULL,
                last_seen   INTEGER NOT NULL,
                resolved_at INTEGER
            );

            CREATE TABLE IF NOT EXISTS file_cache (
                path        TEXT PRIMARY KEY,
                mtime_secs  INTEGER NOT NULL,
                size        INTEGER NOT NULL,
                scan_id     INTEGER NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_todos_tag ON todos(tag);
            CREATE INDEX IF NOT EXISTS idx_todos_file ON todos(file_path);
            CREATE INDEX IF NOT EXISTS idx_todos_resolved ON todos(resolved_at);
            ",
        )?;
        Ok(())
    }

    /// Record the start of a new scan. Returns the scan ID.
    pub fn start_scan(&self, commit_hash: Option<&str>) -> Result<i64> {
        self.conn.execute(
            "INSERT INTO scans (started_at, commit_hash) VALUES (datetime('now'), ?1)",
            rusqlite::params![commit_hash],
        )?;
        Ok(self.conn.last_insert_rowid())
    }

    /// Record the end of a scan with totals.
    pub fn finish_scan(&self, scan_id: i64, total_files: u32, total_todos: u32) -> Result<()> {
        self.conn.execute(
            "UPDATE scans SET finished_at = datetime('now'), total_files = ?1, total_todos = ?2 WHERE id = ?3",
            rusqlite::params![total_files, total_todos, scan_id],
        )?;
        Ok(())
    }

    /// Upsert TODO items from a scan.
    /// New items get first_seen = scan_id. Existing items get last_seen updated.
    pub fn upsert_todos(&self, items: &[TodoItem], scan_id: i64) -> Result<()> {
        let tx = self.conn.unchecked_transaction()?;

        for item in items {
            let tickets_json = serde_json::to_string(&item.metadata.tickets)?;
            let priority_str = item.metadata.priority.map(|p| p.as_str().to_string());

            tx.execute(
                "INSERT INTO todos (id, tag, file_path, line, column_num, message, author, priority, tickets, first_seen, last_seen)
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?10)
                 ON CONFLICT(id) DO UPDATE SET
                    line = excluded.line,
                    column_num = excluded.column_num,
                    last_seen = excluded.last_seen,
                    resolved_at = NULL",
                rusqlite::params![
                    item.id,
                    item.tag.as_str(),
                    item.file.to_string_lossy(),
                    item.line,
                    item.column,
                    item.message,
                    item.metadata.author,
                    priority_str,
                    tickets_json,
                    scan_id,
                ],
            )?;
        }

        tx.commit()?;
        Ok(())
    }

    /// Mark items not seen in this scan as resolved.
    pub fn mark_resolved(&self, scan_id: i64) -> Result<u64> {
        let count = self.conn.execute(
            "UPDATE todos SET resolved_at = ?1 WHERE last_seen < ?1 AND resolved_at IS NULL",
            rusqlite::params![scan_id],
        )?;
        Ok(count as u64)
    }

    /// Get the total count of active (unresolved) TODOs.
    pub fn active_count(&self) -> Result<u64> {
        let count: u64 = self.conn.query_row(
            "SELECT COUNT(*) FROM todos WHERE resolved_at IS NULL",
            [],
            |row| row.get(0),
        )?;
        Ok(count)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::model::todo::{TodoMetadata, TodoTag};
    use std::path::PathBuf;

    fn make_item(id: &str, tag: TodoTag, file: &str, line: u32, message: &str) -> TodoItem {
        TodoItem {
            id: id.to_string(),
            tag,
            file: PathBuf::from(file),
            line,
            column: 0,
            message: message.to_string(),
            metadata: TodoMetadata::default(),
        }
    }

    #[test]
    fn create_and_query() {
        let db = Database::open_in_memory().unwrap();
        let scan_id = db.start_scan(None).unwrap();

        let items = vec![
            make_item("a1", TodoTag::Todo, "src/main.rs", 10, "fix this"),
            make_item("a2", TodoTag::Fixme, "src/lib.rs", 20, "broken"),
        ];
        db.upsert_todos(&items, scan_id).unwrap();
        db.finish_scan(scan_id, 2, 2).unwrap();

        assert_eq!(db.active_count().unwrap(), 2);
    }

    #[test]
    fn resolves_missing_items() {
        let db = Database::open_in_memory().unwrap();

        // Scan 1: two items
        let scan1 = db.start_scan(None).unwrap();
        let items = vec![
            make_item("a1", TodoTag::Todo, "src/main.rs", 10, "fix this"),
            make_item("a2", TodoTag::Fixme, "src/lib.rs", 20, "broken"),
        ];
        db.upsert_todos(&items, scan1).unwrap();
        db.finish_scan(scan1, 2, 2).unwrap();

        // Scan 2: only one item remains
        let scan2 = db.start_scan(None).unwrap();
        let items = vec![make_item(
            "a1",
            TodoTag::Todo,
            "src/main.rs",
            10,
            "fix this",
        )];
        db.upsert_todos(&items, scan2).unwrap();
        let resolved = db.mark_resolved(scan2).unwrap();
        db.finish_scan(scan2, 1, 1).unwrap();

        assert_eq!(resolved, 1);
        assert_eq!(db.active_count().unwrap(), 1);
    }
}
