use crate::config::Config;
use crate::model::todo::{TodoItem, TodoTag};

/// Result of a CI policy check.
pub struct CheckResult {
    /// Whether all policy checks passed.
    pub passed: bool,
    /// List of policy violations found.
    pub violations: Vec<Violation>,
}

/// A single policy violation found during CI check.
#[derive(Debug)]
pub struct Violation {
    /// The rule name that was violated.
    #[allow(dead_code)]
    pub rule: String,
    /// Human-readable description of the violation.
    pub message: String,
    /// File path where violation occurred, if applicable.
    pub file: Option<String>,
    /// Line number where violation occurred, if applicable.
    pub line: Option<u32>,
}

impl std::fmt::Display for Violation {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        if let (Some(file), Some(line)) = (&self.file, self.line) {
            write!(f, " FAIL  {file}:{line}\n       {}", self.message)
        } else {
            write!(f, " FAIL  {}", self.message)
        }
    }
}

/// Run CI policy checks against a set of TODO items.
pub fn check(items: &[TodoItem], config: &Config) -> CheckResult {
    let mut violations = Vec::new();

    // Check: fail on FIXMEs
    if config.ci.fail_on_fixme {
        for item in items {
            if item.tag == TodoTag::Fixme {
                violations.push(Violation {
                    rule: "fail_on_fixme".to_string(),
                    message: format!("FIXME found: {}", item.message),
                    file: Some(item.file.to_string_lossy().to_string()),
                    line: Some(item.line),
                });
            }
        }
    }

    // Check: max total TODOs
    if config.ci.max_todos > 0 && items.len() as u32 > config.ci.max_todos {
        violations.push(Violation {
            rule: "max_todos".to_string(),
            message: format!(
                "Total TODOs ({}) exceeds limit ({})",
                items.len(),
                config.ci.max_todos
            ),
            file: None,
            line: None,
        });
    }

    let passed = violations.is_empty();
    CheckResult { passed, violations }
}

/// Format check results for terminal output.
pub fn format_check_result(result: &CheckResult) -> String {
    if result.passed {
        return "All checks passed.".to_string();
    }

    let mut output = String::new();
    for violation in &result.violations {
        output.push_str(&format!("{violation}\n\n"));
    }
    output.push_str(&format!(
        "{} violation(s) found.\n",
        result.violations.len()
    ));
    output
}
