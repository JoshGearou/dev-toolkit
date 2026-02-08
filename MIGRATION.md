# Migration from dev-rerickso

This document provides a complete mapping of what was preserved from the original dev-rerickso repository and what was removed to create this general-purpose dev-toolkit.

## Philosophy

**Kept**: Platform-agnostic tools, utilities, documentation, and research that work in any development environment.

**Removed**: LinkedIn-specific infrastructure tools, internal APIs, corporate authentication systems, and company-specific workflows.

## Directory Mapping

### ✅ KEPT (General-Purpose)

#### Documentation & Research
```
iam/                        → iam/                  (IAM patterns and research)
designs/okta/               → designs/okta/         (Okta AD integration patterns)
k8s/                        → k8s/                  (Kubernetes architecture docs)
nist_policy_machine/        → nist_policy_machine/  (Policy engine documentation)
bash/common/                → bash/common/          (Shared bash utilities)
git/                        → git/                  (Git configuration and scripts)
```

#### Development Tools
```
src/claude-cli/             → src/claude-cli/       (Claude CLI tools)
src/codex-cli/              → src/codex-cli/        (GitHub Codex integration)
src/copilot/                → src/copilot/          (GitHub Copilot utilities)
src/cursor-cli/             → src/cursor-cli/       (Cursor editor CLI)
src/gemini-cli/             → src/gemini-cli/       (Google Gemini CLI)
src/docker/                 → src/docker/           (Docker setup guides)
src/iterm2/                 → src/iterm2/           (iTerm2 utilities)
src/node_diagnostics/       → src/node_diagnostics/ (Node.js diagnostics)
src/tmux_bench/             → src/tmux_bench/       (Tmux benchmarking)
src/vm-setup/               → src/vm-setup/         (Azure VM setup)
```

#### Code Quality & Analysis
```
src/lint/                   → src/lint/             (Python linting automation)
src/rust_coverage_exclusions/ → src/rust_coverage_exclusions/ (Rust coverage demos)
src/todo_tracker/           → src/todo_tracker/     (Source code TODO tracker)
```

#### Utilities
```
src/expand_date_ranges/     → src/expand_date_ranges/ (Date utilities)
src/url_shortener/          → src/url_shortener/    (URL shortening service)
src/linkify/                → src/linkify/          (Google Docs link tools)
src/git_submodules/         → src/git_submodules/   (Git submodule utilities)
src/deny-file/              → src/deny-file/        (File access control)
src/macos_app_remover/      → src/macos_app_remover/ (macOS app removal)
src/jwt/                    → src/jwt/              (JWT utilities)
src/mcp/github/             → src/mcp/github/       (MCP GitHub server setup)
```

#### Language Examples
```
src/grpc-sample/            → src/grpc-sample/      (Rust gRPC examples)
src/dispatch_demo/          → src/dispatch_demo/    (Rust dispatch patterns)
```

#### Shared Libraries (Partial)
```
src/shared_libs/common/     → src/shared_libs/common/     (Logging, error handling)
src/shared_libs/io_utils/   → src/shared_libs/io_utils/   (CSV, file I/O)
src/shared_libs/cmd_utils/  → src/shared_libs/cmd_utils/  (Subprocess utilities)
src/shared_libs/file_utils/ → src/shared_libs/file_utils/ (File categorization)
src/shared_libs/github_utils/ → src/shared_libs/github_utils/ (GitHub API client)
src/shared_libs/processing_utils/ → src/shared_libs/processing_utils/ (Batch processing)
src/shared_libs/templates/  → src/shared_libs/templates/  (Project templates)
src/shared_libs/tests/      → src/shared_libs/tests/      (Test suites)
```

#### Configuration
```
.gitignore                  → .gitignore (Updated)
.gitattributes              → .gitattributes
Cargo.toml                  → Cargo.toml (Updated workspace members)
```

### ❌ REMOVED (LinkedIn-Specific)

#### LinkedIn Infrastructure Tools
```
src/acl-tool/               ❌ LinkedIn ACL management (uses acl-tool CLI)
src/asset_management/       ❌ LinkedIn Crew/asset APIs (engx.corp.linkedin.com)
src/get_scheduler/          ❌ LinkedIn scheduler detection (go-status CLI)
src/grpcurli/               ❌ LinkedIn gRPC testing (DataVault auth)
src/scm-checker/            ❌ LinkedIn SCM policy enforcement
src/omkhar/                 ❌ Cloudflare analytics (omkhar.net domain)
rdev/                       ❌ LinkedIn rdev tool wrappers
```

#### LinkedIn-Specific Libraries
```
src/shared_libs/linkedin_utils/ ❌ LinkedIn LDAP/AD authentication
src/shared_libs/processing_utils/ldap_batch_processor.py ❌ LinkedIn LDAP batch processing
```

#### LinkedIn-Specific Analysis Tools
```
src/log_parser/             ❌ VDS (Virtual Directory Service) log analysis
src/glean/                  ❌ Glean integration (LinkedIn search)
```

#### LinkedIn Documentation
```
.windsurf/rules/captain.md  ❌ LinkedIn MCP (Captain) tool documentation
onboarding/                 ❌ LinkedIn onboarding documentation
reviews/                    ❌ LinkedIn code/design reviews
rigor/                      ❌ LinkedIn engineering rigor documentation
runbooks/                   ❌ LinkedIn operational runbooks
```

#### LinkedIn-Specific Output/Artifacts
```
output/                     ❌ Generated LinkedIn-specific reports
repositories/               ❌ LinkedIn repository metadata
updates/                    ❌ LinkedIn update tracking
expense/                    ❌ Expense tracking (context unclear)
observe/                    ❌ Observability tools (context unclear)
lucidchart/                 ❌ Lucidchart diagrams (context unclear)
```

#### Test/Temporary Files
```
TEST_FIX_SUMMARY.md         ❌ Test fix documentation from original repo
claude-dotfiles/            ❌ Personal dotfiles (not general-purpose)
.github/                    ❌ GitHub workflows (not general-purpose)
```

## Dependency Changes

### Removed Python Dependencies
```python
# LinkedIn-specific dependencies removed:
# - linkedin-ldap-client (LinkedIn LDAP)
# - linkedin-directory-api (LinkedIn internal API)
# - Any internal LinkedIn packages
```

### Updated Python Import Paths
No changes needed - `linkedin_utils` was fully isolated and unused by other modules.

### Rust Workspace Updates
```toml
# Cargo.toml updated to reflect new directory structure
# Removed: projects/ prefix from excluded members
# All Rust projects now under src/ with consistent structure
```

## Key Differences

### 1. No LinkedIn CLI Tool Dependencies
**Removed**: acl-tool, rdev, rexec, mint, go-status, lid-client, kafka-tool, curli, kubectl (LinkedIn extensions)

**Impact**: Tools that depended on these were removed entirely.

### 2. No LinkedIn Authentication
**Removed**: LinkedIn LDAP, Active Directory, DataVault authentication

**Impact**: `src/shared_libs/linkedin_utils/` removed, no other code depended on it.

### 3. No LinkedIn API Access
**Removed**:
- LinkedIn Crew/Asset APIs
- LinkedIn EngX/Product APIs
- LinkedIn Multiproduct Backend
- LinkedIn go-status service

**Impact**: `src/asset_management/` and `src/get_scheduler/` removed entirely.

### 4. No LinkedIn Infrastructure References
**Removed**:
- Fabric names (ei-lca1, corp-lca1, prod-*, azureprod)
- LinkedIn URN formats (urn:li:restli:..., urn:li:kafkaClusterTopic:...)
- LinkedIn go/ links (go/acl-tool, go/policy/scm, etc.)
- LinkedIn internal domains (*.corp.linkedin.com, *.linkedin.biz)

**Impact**: Documentation examples updated or removed where necessary.

### 5. Documentation Focused on General Patterns
**Changed**:
- README emphasizes platform-agnostic development
- Removed references to LinkedIn-specific workflows (mint build, Captain tools)
- Focused on universal concepts (DDD, code quality, testing patterns)

## Usage Changes

### Before (dev-rerickso)
```bash
# LinkedIn-specific workflows
mint build                          # LinkedIn build tool
rdev create my-dev                  # LinkedIn dev environment
acl-tool acl evaluate ...           # LinkedIn ACL evaluation
captain_context_search "query"      # LinkedIn codebase search
```

### After (dev-toolkit)
```bash
# General-purpose workflows
cargo build                         # Standard Rust build
python -m pytest tests/             # Standard Python testing
./flake8_report.sh --summary-only   # Code quality check
git s                               # Custom git alias (pull + rebase)
```

## File Count Summary

**Original dev-rerickso**: ~150+ tools/directories
**New dev-toolkit**: ~35 tools/directories

**Reduction**: ~75% smaller, focusing on general-purpose utilities

## Migration Validation

To verify the migration was successful:

```bash
# 1. No LinkedIn-specific tool dependencies
! grep -r "acl-tool\|rdev\|omkhar" src/ 2>/dev/null

# 2. No LinkedIn authentication code
! test -d src/shared_libs/linkedin_utils

# 3. No LinkedIn API references (except in test data)
! grep -r "corp\.linkedin\|linkedin\.biz" src/*/README.md 2>/dev/null

# 4. All Python code is importable
python -c "import sys; sys.path.insert(0, 'src/shared_libs'); from common import *"

# 5. Rust workspace builds
cargo check --workspace
```

## Next Steps After Migration

1. **Update Import Paths**: If you had custom scripts importing from `linkedin_utils`, update them to use alternative authentication methods.

2. **Replace LinkedIn CLI Tools**: If you relied on LinkedIn infrastructure tools:
   - **ACL management** → Use native cloud provider IAM (AWS IAM, Azure RBAC, GCP IAM)
   - **Service discovery** → Use Kubernetes service discovery or Consul
   - **Build tools** → Use standard tools (cargo, npm, make, bazel)

3. **Authentication**: Replace LinkedIn LDAP/AD with:
   - OAuth 2.0 / OIDC providers (Okta, Auth0, etc.)
   - SAML 2.0 for enterprise
   - Cloud provider IAM

4. **Git Configuration**: Install git aliases:
   ```bash
   cd git/scripts
   ./install_gitconfig.sh
   ```

5. **Python Development**: Set up linting:
   ```bash
   cd src/lint
   ./import_autofix.sh --configure-workspace
   ```

## Questions?

If you find LinkedIn-specific references that should have been removed, please check:
- Test files (may contain example data with LinkedIn domains)
- Comments and documentation (may reference LinkedIn as examples)
- Historical investigation notes (not active code)

These are generally safe to ignore or update as needed.
