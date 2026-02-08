# dev-toolkit

A general-purpose, multi-language development toolkit focused on security infrastructure research, identity management, and developer productivity tools. This repository provides platform-agnostic utilities, comprehensive IAM research documentation, and best-practice development patterns.

## Origin

This repository is derived from dev-rerickso, a LinkedIn-focused development workspace. All LinkedIn-specific tooling, APIs, and internal infrastructure dependencies have been removed to create a standalone, general-purpose toolkit suitable for any development environment.

## Repository Structure

### Identity & Access Management Research (`iam/`, `designs/`, `k8s/`)
Comprehensive documentation and architectural patterns for modern IAM systems:
- **Cedar Policy Engine** - Policy decision point (PDP) implementations
- **SPIRE/SPIFFE** - Workload identity with TPM attestation patterns
- **Zanzibar** - Relationship-based access control architectures
- **NIST Policy Machine** - Kubernetes-native policy frameworks
- **Okta Integration** - Enterprise identity federation patterns
- **Kubernetes Auth** - K8s authentication and authorization deep-dives

### Development Tools (`src/`)
Self-contained projects organized by domain:

**AI/Editor Integration**
- `claude-cli/` - Claude CLI tools and utilities
- `codex-cli/` - GitHub Codex integration
- `cursor-cli/` - Cursor editor CLI tools
- `gemini-cli/` - Google Gemini CLI integration
- `copilot/` - GitHub Copilot utilities

**Infrastructure & DevOps**
- `docker/` - Docker setup guides (Linux/macOS)
- `vm-setup/` - Azure VM provisioning scripts
- `node_diagnostics/` - Node.js environment troubleshooting
- `iterm2/` - iTerm2 backup and restore utilities
- `tmux_bench/` - Tmux performance benchmarking

**Security & Identity**
- `jwt/` - JWT generation and validation examples
- `mcp/` - Model Context Protocol (MCP) tools for secure API access
  - GitHub MCP server setup and token rotation
  - Secure configuration management patterns

**Code Quality & Analysis**
- `lint/` - Python linting automation (flake8, import fixes)
  - AST-based import cleanup
  - Auto-fix workflows with dry-run support
- `rust_coverage_exclusions/` - Rust code coverage patterns and demos
- `todo_tracker/` - Source code TODO tracker (Rust)

**General Utilities**
- `expand_date_ranges/` - Date range expansion with holiday calendars
- `url_shortener/` - Self-hosted URL shortening service (Node.js/TypeScript)
- `linkify/` - Google Apps Script for document link enhancement
- `git_submodules/` - Git submodule management utilities
- `deny-file/` - File access control utilities
- `macos_app_remover/` - Safe macOS application removal

**Language Examples**
- `grpc-sample/` - Rust gRPC client/server examples
- `dispatch_demo/` - Rust async dispatch patterns

### Shared Libraries (`src/shared_libs/`)
Reusable Python utilities with strict type safety (`mypy --strict` compliant):
- `common/` - Logging, error handling, progress tracking
- `io_utils/` - CSV, file I/O with validation
- `cmd_utils/` - Subprocess execution with retry logic
- `file_utils/` - File categorization and pattern matching
- `github_utils/` - GitHub API client with rate limiting
- `processing_utils/` - Batch processing frameworks
- `templates/` - Project scaffolding templates

### Scripts & Configuration
- `bash/common/` - Shared bash utilities with sophisticated error handling
- `git/` - Git configuration, aliases, and repository management scripts

## Design Principles

### Domain Driven Design
Follow Eric Evans' DDD conventions for simple, maintainable code:
- **Ubiquitous Language** - Use domain terms consistently
- **Bounded Contexts** - Clear separation of concerns
- **Intention-Revealing Names** - Self-documenting code
- **Entities and Value Objects** - Proper domain modeling

### Code Quality Standards

**Python (Strictly Enforced)**
```bash
mypy --strict <file.py>    # All code must pass
flake8 <file.py>            # All code must pass
```
- Full type hints on all function signatures
- Prefer composition over inheritance
- Use dataclasses or Pydantic for domain objects

**Rust**
```bash
cargo clippy                # Lint all workspace members
cargo test                  # Run test suites
```
- Follow standard Rust idioms
- Clear module boundaries aligned with domain concepts

**Bash**
- Always use `set -u` for undefined variable checking
- Source shared utilities from `bash/common/repo_lib.sh`
- Comprehensive retry logic for network operations

### Python Project Pattern
Many tools follow a **bash wrapper + Python implementation** pattern:
- Bash handles virtual environment setup and argument forwarding
- Python contains business logic (must be mypy/flake8 clean)
- Automatic dependency installation on first run

Example structure:
```
project/
├── project_name.sh      # Bash wrapper (venv setup)
├── project_name.py      # Python implementation
└── requirements.txt     # Dependencies
```

## Quick Start

### Python Tools
```bash
cd src/lint
./flake8_report.sh --summary-only    # Lint codebase
./import_autofix.sh --dry-run        # Preview import fixes
./flake8_autofix.sh --backup         # Apply style fixes
```

### Rust Workspace
```bash
cargo build              # Build all workspace members
cargo test               # Run tests
cargo clippy             # Lint

cd src/todo_tracker      # Navigate to specific project
cargo run                # Run individual tool
```

### Node.js Diagnostics
```bash
cd src/node_diagnostics
./diagnose_node_env.sh   # Diagnose Node.js, npm, Volta issues
```

## Git Workflow

### Custom Aliases (from `git/config/.gitconfig`)
- `git s` - Fetch all + rebase pull
- `git lg` - Colorized graph log with relative dates
- `git bclean` - Delete merged branches (keeps main/dev)

### Commit Notation
Follow [Arlo's Commit Notation](https://github.com/RefactoringCombos/ArlosCommitNotation) for semantic commit messages.

## Documentation Standards
- Use Mermaid diagrams for architecture visualization
- Include sequence diagrams for authentication flows
- Create graph diagrams for policy relationships
- Write documentation that domain experts can understand

## Testing
- Organize tests by domain concepts, not technical layers
- Use descriptive test names expressing business scenarios
- Separate test categories in dedicated `tests/` directories

## What Was Removed

This toolkit was extracted from a LinkedIn-focused development workspace. The following LinkedIn-specific components were removed:
- ACL management tools (LinkedIn ACL infrastructure)
- Asset management APIs (LinkedIn Crews/Products)
- Scheduler detection tools (go-status, RAIN scheduler)
- gRPC testing tools (LinkedIn DataVault authentication)
- SCM policy enforcement (LinkedIn-specific compliance)
- LDAP/directory utilities (LinkedIn Active Directory)
- Development environment tools (rdev, mint, lid-client)
- VDS log analysis (LinkedIn Virtual Directory Service)
- Internal documentation and runbooks

For the complete list of what was kept vs. removed, see `MIGRATION.md`.

## Contributing

Contributions should maintain the same quality standards:
1. All Python code must pass `mypy --strict` and `flake8`
2. All Rust code must pass `cargo clippy`
3. Follow Domain Driven Design principles
4. Include tests for new functionality
5. Use Arlo's Commit Notation

## License

This is a personal development toolkit. Individual tools may have their own licensing requirements - check specific subdirectories for details.
