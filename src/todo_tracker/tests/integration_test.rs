use std::path::Path;

/// Integration test: scan the test fixtures directory and verify extraction.
#[test]
fn scan_fixtures_directory() {
    let fixtures_dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures");
    assert!(fixtures_dir.exists(), "fixtures directory must exist");

    let config = todo_tracker::config::Config {
        repo_root: Some(fixtures_dir.clone()),
        ..Default::default()
    };

    let items = todo_tracker::scanner::scan_repository(&fixtures_dir, &config).unwrap();

    // We should find TODOs across all fixture files
    assert!(!items.is_empty(), "should find TODOs in fixtures");

    // Check that multiple tags are found
    let tags: std::collections::HashSet<_> = items.iter().map(|i| i.tag).collect();
    assert!(tags.len() > 1, "should find multiple tag types");

    // Verify items are sorted by file then line
    for window in items.windows(2) {
        assert!(
            (window[0].file.clone(), window[0].line) <= (window[1].file.clone(), window[1].line),
            "items should be sorted by file then line"
        );
    }
}

/// Integration test: verify JSON output is valid.
#[test]
fn json_output_is_valid() {
    let fixtures_dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures");
    let config = todo_tracker::config::Config {
        repo_root: Some(fixtures_dir.clone()),
        ..Default::default()
    };

    let items = todo_tracker::scanner::scan_repository(&fixtures_dir, &config).unwrap();
    let json = todo_tracker::output::format_items(&items, todo_tracker::config::OutputFormat::Json)
        .unwrap();

    // Should parse as valid JSON
    let parsed: Vec<serde_json::Value> = serde_json::from_str(&json).unwrap();
    assert_eq!(parsed.len(), items.len());
}

/// Integration test: verify CSV output has correct columns.
#[test]
fn csv_output_has_header() {
    let fixtures_dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures");
    let config = todo_tracker::config::Config {
        repo_root: Some(fixtures_dir.clone()),
        ..Default::default()
    };

    let items = todo_tracker::scanner::scan_repository(&fixtures_dir, &config).unwrap();
    let csv_output =
        todo_tracker::output::format_items(&items, todo_tracker::config::OutputFormat::Csv)
            .unwrap();

    let first_line = csv_output.lines().next().unwrap();
    assert!(first_line.contains("file"));
    assert!(first_line.contains("line"));
    assert!(first_line.contains("tag"));
    assert!(first_line.contains("message"));
}
