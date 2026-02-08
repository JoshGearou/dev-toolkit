#![allow(dead_code)]

use anyhow::Result;
use std::path::{Path, PathBuf};
use std::time::SystemTime;

/// Fingerprint of a file for cache invalidation.
/// If mtime and size match, assume content is unchanged.
#[derive(Debug, Clone)]
pub struct FileFingerprint {
    /// Absolute path to the file.
    pub path: PathBuf,
    /// Last modification time when fingerprint was taken.
    pub mtime: SystemTime,
    /// File size in bytes when fingerprint was taken.
    pub size: u64,
}

impl FileFingerprint {
    /// Create a fingerprint from a file path by reading its metadata.
    pub fn from_path(path: &Path) -> Result<Self> {
        let metadata = std::fs::metadata(path)?;
        Ok(Self {
            path: path.to_path_buf(),
            mtime: metadata.modified()?,
            size: metadata.len(),
        })
    }

    /// Check if the file has changed since this fingerprint was taken.
    pub fn is_stale(&self) -> Result<bool> {
        let current = Self::from_path(&self.path)?;
        Ok(self.mtime != current.mtime || self.size != current.size)
    }
}

/// Cache manager for incremental scanning.
/// Stores file fingerprints to skip unchanged files on subsequent scans.
pub struct ScanCache {
    /// Directory where cache files are stored.
    cache_dir: PathBuf,
}

impl ScanCache {
    /// Create a new cache rooted at the given directory.
    pub fn new(cache_dir: &Path) -> Result<Self> {
        std::fs::create_dir_all(cache_dir)?;
        Ok(Self {
            cache_dir: cache_dir.to_path_buf(),
        })
    }

    /// Returns the cache directory path.
    pub fn cache_dir(&self) -> &Path {
        &self.cache_dir
    }

    /// Check if a file needs re-scanning based on cached fingerprint.
    /// Returns true if the file is new or has changed.
    pub fn needs_rescan(&self, _path: &Path) -> bool {
        // Placeholder: always rescan in v1.
        // Future: compare against stored fingerprints in SQLite.
        true
    }
}
