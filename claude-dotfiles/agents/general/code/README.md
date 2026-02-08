# Code Agents

Code review and fixing agents for comprehensive code quality analysis.

## Overview

This directory contains agents for code quality review and automated fixing. The consolidated code-reviewer covers multiple quality dimensions, while language-specific fixers handle automated repairs.

## Agents

| Agent | Type | Purpose |
|-------|------|---------|
| [code-reviewer](code-reviewer.md) | Reviewer | Comprehensive code review across 8 quality dimensions |
| [python-fixer](python-fixer.md) | Fixer | Fixes mypy type errors and flake8 violations |
| [rust-fixer](rust-fixer.md) | Fixer | Fixes cargo check errors and clippy warnings |

## Code Reviewer Dimensions

The consolidated code-reviewer covers:

| Dimension | Focus |
|-----------|-------|
| **Performance** | N+1 queries, O(n²) loops, hot path optimization |
| **Security** | OWASP Top 10, injection, XSS, auth issues |
| **Concurrency** | Race conditions, deadlocks, thread safety |
| **Error Handling** | Empty catches, error propagation, logging |
| **Resources** | File/connection leaks, cleanup patterns |
| **API Contracts** | Breaking changes, backward compatibility |
| **Test Coverage** | Untested paths, edge cases, test quality |
| **Type Safety** | Missing annotations, unsafe casts, null handling |

## Code Fixers

Fixers modify code to resolve issues:

### Python Fixer
- Runs `mypy --strict` and fixes type errors
- Runs `flake8` and fixes style violations
- Applies import sorting and cleanup

### Rust Fixer
- Runs `cargo check` and fixes compilation errors
- Runs `cargo clippy` and fixes lint warnings
- Applies suggested fixes automatically

## Workflow

### Code Review
```
1. Run code-reviewer on PR
2. Review findings by severity
3. Address critical/high issues
4. Use fixers for automated repairs
```

### Fix Workflow
```
1. Run python-fixer or rust-fixer
2. Review changes
3. Run tests to verify fixes
4. Commit when satisfied
```

## Severity Levels

All agents use consistent severity:

- **Critical** - Block PR: Security issues, data loss risk
- **High** - Request changes: Bugs, missing error handling
- **Medium** - Comment: Code quality, missing tests
- **Low** - Informational: Best practices, optimization

## Related

- See [ssdlc/](../ssdlc/) for security-focused review
- See [docs/](../docs/) for documentation review
- See [experts/](../experts/) for language-specific guidance
