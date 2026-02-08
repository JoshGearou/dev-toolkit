# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this general-purpose development toolkit.

## Repository Overview

General-purpose, multi-language development toolkit focused on security infrastructure research, identity/access management (IAM), and developer productivity. Emphasizes code quality, Domain Driven Design principles, and platform-agnostic solutions.

**Origin**: Extracted from a LinkedIn-focused workspace (dev-rerickso) with all LinkedIn-specific infrastructure dependencies removed.

## Key Development Commands

### Python Quality Tools

**Lint entire codebase:**
```bash
cd src/lint
./flake8_report.sh --summary-only    # Generate flake8 report
```

**Auto-fix Python issues:**
```bash
cd src/lint
# Full workflow: imports → style → verify
./import_autofix.sh --dry-run        # Preview import cleanup (AST-based)
./import_autofix.sh --verbose        # Apply import fixes
./flake8_autofix.sh --dry-run        # Preview style fixes
./flake8_autofix.sh --backup         # Apply with backups
./flake8_report.sh --summary-only    # Verify improvements
```

**Type checking:**
```bash
mypy --strict <file.py>              # All Python must be mypy --strict clean
```

### Rust Development

**Build workspace:**
```bash
cargo build --workspace              # Build all workspace members
```

**Test and lint:**
```bash
cargo test --workspace               # Run all tests
cargo clippy --workspace --all-targets -D warnings  # Lint (must pass)
```

**Run specific project:**
```bash
cd src/grpc-sample/rust/client       # Navigate to project
cargo run                            # Run specific member
```

**Note**: Some projects may override toolchains locally. Check with `rustup show` in project directory.

### Testing

**Python tests:**
```bash
# From project root or specific src/ subdirectory
python -m pytest tests/              # Run all tests in directory
python -m pytest tests/test_*.py -v  # Run specific test with verbose output
```

**Rust tests:**
```bash
cargo test --workspace               # All tests
cargo test --test <name>             # Specific test
```

## Architecture Overview

### Directory Structure

- **`src/`**: Individual project directories (Python or Rust), typically self-contained
- **`designs/`**: Architecture documents and patterns (IAM, Okta, authentication flows)
- **`iam/`**: Identity and access management research with Mermaid diagrams
- **`k8s/`**: Kubernetes architecture documentation
- **`bash/common/`**: Shared shell utilities with robust error handling
- **`git/`**: Git configuration, aliases, and repository management

### Rust Workspace Pattern

Cargo workspace with members defined in root `Cargo.toml`:
- Members: `src/todo_tracker/`
- Excluded (standalone projects): `src/dispatch_demo/`, `src/grpc-sample/`, `src/rust_coverage_exclusions/demo/`
- Navigate to specific directories to work on excluded projects

### Python Project Pattern

Many Python projects follow a **bash wrapper + Python script** pattern:

**Bash wrapper** (e.g., `diagnose_node_env.sh`):
- Handles virtual environment setup automatically
- Installs dependencies as needed
- Forwards arguments to Python script
- Provides consistent error handling

**Python script** (e.g., `diagnose_node_env.py`):
- Contains actual business logic
- Must be `mypy --strict` and `flake8` clean
- Uses type hints for all function signatures
- Typically uses dataclasses or Pydantic for domain objects

**To run**: Always use the bash wrapper script, not the Python script directly.

### Bash Scripting Patterns

All bash scripts source shared utilities from `bash/common/repo_lib.sh`:

**Key functions:**
- `source_required_file()` - Strict sourcing with debug logging
- `log_message()` - Timestamped logging to stdout and file
- `run_command_with_retry()` - Fibonacci backoff retry logic for network operations
- `get_git_root()` - Find repository root
- Kubernetes helpers: `cluster_exists()`, `wait_for_pod_ready()`, etc.

**Standard pattern:**
```bash
#!/bin/bash
set -u  # Undefined variable check (required)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../../bash/common/repo_lib.sh"
```

## Design Principles

### Domain Driven Design (DDD)

Follow Eric Evans' Domain Driven Design conventions:

- **Ubiquitous Language**: Use domain terms consistently across code, docs, conversations
- **Bounded Contexts**: Keep related functionality grouped with clear boundaries
- **Entities and Value Objects**: Model concepts as entities (with identity) or value objects (immutable)
- **Services**: Use domain services for operations that don't belong to entities/value objects
- **Repositories**: Abstract data access behind repository interfaces
- **Intention-Revealing Names**: Choose names that express what code does in domain terms
- Prefer simple, straightforward names over clever or abbreviated ones

### Code Quality Standards

**Python (Strictly Enforced):**
- Must pass `mypy --strict` (no exceptions)
- Must pass `flake8` (no exceptions)
- Use type hints for all function signatures and complex data structures
- Prefer composition over inheritance
- Use dataclasses or Pydantic models for domain objects

**Rust:**
- Follow standard Rust conventions and idioms
- Use `cargo clippy` for linting (must pass with no warnings)
- Maintain clear module boundaries aligned with domain concepts

**Bash:**
- Use `set -u` for undefined variable checking (required)
- Source utilities from `bash/common/repo_lib.sh`
- Use comprehensive retry logic for network operations
- Prefer simple bash for basic tasks, transition to Python for complex logic

### Scripting Philosophy

Know when to use bash vs Python:

**Simple Bash** - Use for:
- Environment setup
- Argument parsing and forwarding
- Basic file operations
- Calling external tools
- Virtual environment management

**Python + Bash Wrapper** - Use for:
- Complex data processing
- Analysis and algorithms
- API interactions
- Business logic

Pattern: Bash handles venv setup and argument forwarding; Python does the work.

## Domain-Specific Knowledge

### Identity & Access Management (IAM)

This toolkit contains extensive IAM research in the `iam/` directory:

- **Cedar Policy Engine**: Policy decision point (PDP) implementations
- **SPIRE/SPIFFE**: Workload identity with TPM attestation
- **Zanzibar**: Google's relationship-based access control model
- **NIST Policy Machine**: Kubernetes-native access control

Reference Mermaid diagrams in `iam/` when working on authentication/authorization features.

### Kubernetes Patterns

The `k8s/` directory contains deep-dive documentation on:
- Control plane architecture
- Data plane components
- Extension points and customization
- Communication patterns and lifecycles

Use these as reference when designing Kubernetes-native applications.

## Git Workflow

### Custom Aliases (from `git/config/.gitconfig`)

Install with: `cd git/scripts && ./install_gitconfig.sh`

- `git s` - Fetch all + rebase pull
- `git lg` - Colorized graph log with relative dates
- `git bclean` - Delete merged branches (keeps main/dev)

### Commit Notation

Follow [Arlo's Commit Notation](https://github.com/RefactoringCombos/ArlosCommitNotation) for semantic commit messages.

## Testing Patterns

- Organize tests by domain concepts, not technical layers
- Use descriptive test names that express business scenarios
- Separate test categories clearly with `tests/` directories
- Many projects include test-specific README files
- Document coverage exclusions with working examples

## Common Pitfalls

1. **Virtual environments**: Many projects have local `.venv` or `venv` directories. Use the bash wrapper scripts which handle venv setup automatically. Don't activate venvs manually.

2. **Python imports**: For projects in `src/`, custom modules from `src/shared_libs/` may need path configuration. Use `import_autofix.sh --configure-workspace` to set up VS Code Python paths.

3. **Rust toolchains**: Projects may override toolchains locally. Check with `rustup show` in project directory. Some demos require nightly, others use stable.

4. **Bash strict mode**: Always use `set -u` in bash scripts. Source from `bash/common/repo_lib.sh` for consistent error handling.

5. **Type checking**: All Python code must pass `mypy --strict`. No exceptions. Run mypy before committing.

6. **Removed LinkedIn dependencies**: This toolkit was extracted from a LinkedIn-focused workspace. Don't add back LinkedIn-specific tools (acl-tool, rdev, mint) or assume access to LinkedIn infrastructure.

## Documentation Standards

- Use Mermaid diagrams for architecture visualization
- Include sequence diagrams for authentication flows
- Create graph diagrams for policy relationships
- Write documentation that domain experts can understand
- Focus on universal patterns, not company-specific implementations

### Google Docs Markdown Compatibility

Markdown files in this repository may be converted to Google Docs. **Always format markdown for Google Docs compatibility.**

**Structure for Google Docs:**
- Use markdown headings (`#`, `##`, `###`) or **bold headers** followed by blank lines
- Avoid indentation-based formatting (Google Docs ignores leading spaces)
- Use blank lines between sections
- Prefer numbered/bulleted lists over indented blocks

**Line breaks within a paragraph:** Add two trailing spaces at the end of lines where you need a hard line break.

**Tables:** Markdown tables convert well to Google Docs tables - use them for structured data.

**Links:** Use standard markdown links `[text](url)` - these convert to clickable links.

## Tool-Specific Guidance

### MCP (Model Context Protocol)
The `src/mcp/github/` directory contains:
- Secure MCP server configuration for GitHub API access
- Token rotation runbooks
- Best practices for credential management

Use these patterns when setting up MCP servers for any API.

### AI CLI Tools
The repository includes installation and management scripts for:
- Claude CLI (`src/claude-cli/`)
- GitHub Codex (`src/codex-cli/`)
- Cursor (`src/cursor-cli/`)
- Google Gemini (`src/gemini-cli/`)
- GitHub Copilot (`src/copilot/`)

Each includes install, update, and uninstall scripts.

### Code Quality Automation
The `src/lint/` directory provides:
- Automated flake8 linting with reports
- AST-based import cleanup (safer than regex)
- Auto-fix workflows with dry-run capability
- Integration with CI/CD pipelines

## What This Repository Is NOT

- **Not LinkedIn-specific**: All LinkedIn infrastructure tools have been removed
- **Not a production framework**: This is a research and development toolkit
- **Not a library**: Projects are self-contained, not designed for packaging
- **Not company-specific**: Patterns and tools are platform-agnostic

## Getting Help

For questions about:
- **Code quality**: See `src/lint/README.md`
- **IAM patterns**: See `iam/` directory documentation
- **Rust workspace**: See `Cargo.toml` and project-specific READMEs
- **Git utilities**: See `git/scripts/`
- **Migration from dev-rerickso**: See `MIGRATION.md`

## Development Loop

Standard workflow for making changes:

1. **Read existing code** first before suggesting modifications
2. **Run quality checks** before committing:
   ```bash
   # Python
   mypy --strict <file>.py
   flake8 <file>.py
   python -m pytest tests/

   # Rust
   cargo clippy
   cargo test
   ```
3. **Follow commit notation** (Arlo's Commit Notation)
4. **Update tests** when changing behavior
5. **Document patterns** in README files when adding new tools

## Key Takeaway

This is a **general-purpose development toolkit** focused on security research, IAM patterns, and code quality. When working with this codebase:
- Prefer platform-agnostic solutions
- Maintain strict code quality standards
- Follow Domain Driven Design principles
- Document patterns and trade-offs
- Keep tools self-contained and reusable
