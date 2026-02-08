# Node.js Environment Diagnostics

Comprehensive diagnostic tool for identifying and resolving Node.js, npm, and Volta environment issues.

## Quick Start

```bash
cd src/node_diagnostics
./diagnose_node_env.sh              # Basic check
./diagnose_node_env.sh --verbose    # Detailed analysis
```

## Features

- ✅ Checks Node.js installation and version (requires 18+, recommends 22 LTS)
- ✅ Validates npm installation
- ✅ Detects Volta installation and configuration
- ✅ Identifies multiple Node.js installations causing conflicts
- ✅ Verifies PATH configuration
- ✅ Lists npm global packages
- ✅ Provides copy-paste fix commands for each issue
- ✅ Categorizes issues by severity (critical/warning/info)

## Exit Codes

- `0` - Environment healthy (no issues)
- `1` - Critical issues found (must fix)
- `2` - Warnings (functional but suboptimal)

## Usage

### Basic Diagnostics

```bash
./diagnose_node_env.sh
```

Output example:
```
Node.js Environment Diagnostics
Platform: Darwin 25.2.0

============================================================
  INSTALLED TOOLS
============================================================
✓ node       v22.16.0
✓ npm        10.9.2
✓ volta      1.1.1

============================================================
  DIAGNOSIS: HEALTHY ✓
============================================================
No issues detected. Your Node.js environment is properly configured.
```

### Verbose Mode

```bash
./diagnose_node_env.sh --verbose
```

Provides additional information:
- All Node.js installation paths (detects conflicts)
- PATH configuration details
- VOLTA_HOME settings
- npm global packages list with locations
- Command execution details (logged to `diagnose_node_env.log`)

### Integration with Scripts

Use in CI/CD or installation scripts:

```bash
#!/bin/bash
set -e

# Run diagnostics
if ! ./src/node_diagnostics/diagnose_node_env.sh; then
    echo "Environment check failed. Fix issues above."
    exit 1
fi

# Proceed with installation
npm install -g @anthropic-ai/claude-code
```

## Architecture

### Files

- `diagnose_node_env.py` - Python implementation using shared_libs
- `diagnose_node_env.sh` - Bash wrapper with venv management
- `NODE_DIAGNOSTICS.md` - Complete diagnosis runbook
- `README.md` - This file

### Dependencies

Uses workspace shared libraries from `src/shared_libs`:
- `shared_libs.cmd_utils.subprocess_client` - Robust command execution
- `shared_libs.common.logging_utils` - Standardized logging

Zero external dependencies - uses only Python standard library + shared_libs.

## Common Issues Detected

### Critical Issues
- Node.js not installed
- Node.js version < 18
- npm not installed

### Warnings
- Multiple Node.js installations detected
- Volta installed but not managing Node.js
- Version conflicts in PATH

### Recommendations
- Volta not installed (optional but recommended)
- Node.js < 22 (upgrade to LTS)

## Output

The tool provides:
1. System information
2. Installed tools status
3. Issues grouped by severity
4. Copy-paste commands to fix each issue
5. Exit code indicating overall health

Example with issues:
```
============================================================
  CRITICAL ISSUES
============================================================

1. Node.js version too old: v16.20.0
   → Upgrade to Node.js 18+ (22 LTS recommended)
   Commands:
     volta install node@22  # Recommended
     # Or: volta install node@18  # Minimum
```

## Development

### Testing

```bash
# Test basic functionality
./diagnose_node_env.sh

# Test verbose mode
./diagnose_node_env.sh --verbose

# Check exit code
./diagnose_node_env.sh
echo $?  # 0=healthy, 1=critical, 2=warnings
```

### Logging

Verbose mode creates `diagnose_node_env.log` with detailed execution information:
```bash
./diagnose_node_env.sh --verbose
cat diagnose_node_env.log
```

## Complete Documentation

See [`runbooks/node-environment-diagnostics.md`](../../runbooks/node-environment-diagnostics.md) for:
- Complete symptom-based troubleshooting guide
- Manual diagnostic procedures
- Integration with repository bash helpers
- Expected output examples for all scenarios

## Related Tools

- `bash/common/repo_lib.sh` - Contains `check_volta_and_node()` function for scripts
- AI tool installation scripts use this for environment validation

## Requirements

- Python 3.7+
- Bash 3.0+
- Standard Unix utilities (which, grep, etc.)
