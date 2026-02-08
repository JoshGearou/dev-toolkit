# Repository Guidelines

This file provides guidance for AI agents (like Claude Code) working with the dev-toolkit codebase.

## Project Structure & Module Organization

- **`src/`** - Self-contained tools and projects
  - Rust crates: `src/dispatch_demo`, `src/grpc-sample`, `src/todo_tracker`, etc.
  - Python projects: Most follow bash wrapper + Python script pattern
  - Shared Python libraries: `src/shared_libs/` with reusable utilities
- **`bash/common/`** - Reusable shell utilities (import via `source bash/common/repo_lib.sh`)
- **`designs/`** - Architecture specs and diagrams (Okta integration patterns)
- **`iam/`** - Identity and Access Management research documentation
- **`k8s/`** - Kubernetes architecture deep-dives
- **`git/`** - Git configuration, aliases, and repository management scripts
- **`target/`** - Rust builds (not committed to git)

## Build, Test, and Development Commands

### Rust
```bash
cargo fmt --all                                    # Format before review
cargo clippy --workspace --all-targets -D warnings # Lint (must pass)
cargo test --workspace                             # Run all tests
cargo build --workspace                            # Build all members

# Individual projects
cd src/dispatch_demo
cargo test
bash build_and_test.sh                             # CI smoke test
```

### Python
```bash
# Setup (use virtualenv)
python -m pip install -r src/shared_libs/requirements.txt

# Testing
python -m pytest src/shared_libs/tests -v

# Code quality (REQUIRED)
mypy --strict <file>.py                            # Must pass
flake8 <file>.py                                   # Must pass

# Automated linting
cd src/lint
./flake8_report.sh --summary-only                  # Generate report
./import_autofix.sh --dry-run                      # Preview fixes
./flake8_autofix.sh --backup                       # Apply fixes
```

### Node.js
```bash
cd src/url_shortener
npm install
npm test
```

## Coding Style & Naming Conventions

### Rust
- Follow Rust 2021 edition idioms
- Keep module boundaries aligned with bounded contexts
- Document invariants in `mod.rs`
- Use `cargo clippy` - all warnings must be fixed
- Prefer explicit error handling over unwrap/expect

### Python
- **4-space indentation** (not tabs)
- **Full type hints** on all function signatures
- **`mypy --strict` must pass** (no exceptions)
- **`flake8` must pass** (no exceptions)
- Prefer dataclasses and composition over inheritance
- Use descriptive, intention-revealing names

### Shell/Bash
- Enable strict mode: `set -u` (undefined variable check required)
- Reuse helpers from `bash/common/repo_lib.sh`
- Keep scripts idempotent (safe to rerun)
- Use comprehensive retry logic for network operations
- Prefer simple bash for orchestration, Python for complex logic

## Domain Driven Design Principles

Follow Eric Evans' DDD conventions:

- **Ubiquitous Language** - Use domain terms consistently
- **Bounded Contexts** - Keep related functionality grouped
- **Intention-Revealing Names** - Code should be self-documenting
- **Entities and Value Objects** - Model domain concepts properly
- **Services** - For operations that don't belong to entities
- **Repositories** - Abstract data access patterns

Avoid clever or abbreviated names. Prefer clarity over brevity.

## Testing Guidelines

- **Name tests after domain behavior**, not implementation details
  - Good: `test_username_lookup_handles_unknown_user`
  - Bad: `test_function_returns_none`
- **Collocate fixtures** inside each project's `tests/` directory
- **Avoid cross-project imports** that break test isolation
- **Update tests alongside behavior changes**
- **Document coverage exclusions** inline with comments explaining why
- Use descriptive assertions with clear failure messages

### Test Organization
```
src/project_name/
├── project_name.py
├── tests/
│   ├── __init__.py
│   ├── test_feature_a.py
│   ├── test_feature_b.py
│   └── fixtures/
│       └── sample_data.json
```

## Commit & Pull Request Guidelines

### Commit Messages
Follow [Arlo's Commit Notation](https://github.com/RefactoringCombos/ArlosCommitNotation):
- One intent per commit
- Leading keyword: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
- Reference issues/RFCs in body
- Explain domain impact and reasoning

**Examples:**
```
feat: Add JWT validation with RS256 support

Implement RS256 signature verification for JWT tokens using PyJWT.
Includes comprehensive error handling for expired/malformed tokens.

Refs: IAM research in iam/jwt_issuance.md
```

```
refactor: Extract CSV writing to io_utils module

Move CSV generation logic from individual tools to shared_libs/io_utils
for reuse across projects. No behavior changes.
```

### Pull Requests
- **List validation steps**: Commands run, tests passed
- **Call out security implications** if applicable
- **Note breaking changes** clearly
- **Include screenshots** for UI changes
- Prefer short-lived branches
- Rebase instead of merge commits (keep history linear)

## Python Project Pattern

Most Python tools follow this pattern:

```
src/tool_name/
├── tool_name.sh          # Bash wrapper (handles venv, args)
├── tool_name.py          # Python implementation (business logic)
├── requirements.txt      # Dependencies
└── tests/
    └── test_tool_name.py
```

**Bash wrapper responsibilities:**
- Virtual environment setup
- Dependency installation
- Argument forwarding to Python script
- Error handling and exit codes

**Python script responsibilities:**
- Business logic implementation
- Must be `mypy --strict` and `flake8` clean
- Type hints on all functions
- Use dataclasses for domain objects

**Usage:** Always run the bash wrapper, not the Python script directly.

## Common Pitfalls

1. **Virtual environments**: Use bash wrapper scripts which handle venv automatically
2. **Python imports**: Use `import_autofix.sh --configure-workspace` for path setup
3. **Rust toolchains**: Some projects override toolchains (check with `rustup show`)
4. **Bash strict mode**: Always use `set -u` in scripts
5. **Type checking**: All Python must pass `mypy --strict` before committing
6. **LinkedIn references**: This is a general-purpose toolkit - avoid company-specific patterns

## Documentation Standards

- Use **Mermaid diagrams** for architecture visualization
- Include **sequence diagrams** for authentication flows
- Create **graph diagrams** for policy relationships
- Write for **domain experts**, not just developers
- Keep examples **platform-agnostic**

### Google Docs Compatibility
Markdown files may be converted to Google Docs:
- Use headings (`#`, `##`) or **bold headers** followed by blank lines
- Avoid indentation-based formatting
- Use blank lines between sections
- Prefer tables for structured data
- Add two trailing spaces for hard line breaks within paragraphs

## Key Tools and Their Purpose

| Tool | Purpose | Language | Entry Point |
|------|---------|----------|-------------|
| `lint/` | Python linting automation | Python | `flake8_report.sh` |
| `todo_tracker/` | Source code TODO scanner | Rust | `run.sh` |
| `node_diagnostics/` | Node.js environment debugging | Python | `diagnose_node_env.sh` |
| `expand_date_ranges/` | Date utility with holidays | Python | `expand_date_ranges.sh` |
| `url_shortener/` | URL shortening service | TypeScript | `npm start` |
| `jwt/` | JWT examples | Python | `jwt_example.sh` |
| `mcp/github/` | MCP GitHub server setup | Shell | See README |

## AI Agent Guidelines

When working with this codebase:

1. **Read before modifying** - Always read existing code first
2. **Maintain quality standards** - Run mypy/flake8/clippy before committing
3. **Follow DDD principles** - Use domain language consistently
4. **Keep tools self-contained** - Avoid creating dependencies between tools
5. **Document patterns** - Update READMEs when adding features
6. **Prefer platform-agnostic solutions** - No company-specific dependencies
7. **Test thoroughly** - Write tests for new functionality

## Getting Help

- **Code quality**: `src/lint/README.md`
- **IAM patterns**: `iam/` directory
- **Rust workspace**: `Cargo.toml` and project READMEs
- **Git utilities**: `git/scripts/`
- **Migration notes**: `MIGRATION.md`
- **Claude Code guidance**: `CLAUDE.md`

## Repository Philosophy

This toolkit emphasizes:
- **Platform-agnostic** solutions over company-specific tools
- **Code quality** through strict type checking and linting
- **Domain-driven design** with clear, intention-revealing names
- **Self-contained tools** that are easy to understand and modify
- **Comprehensive documentation** for IAM and security patterns
- **Reusable patterns** that can be adapted to any environment

Think of this as a **research and development workspace**, not a production framework.
