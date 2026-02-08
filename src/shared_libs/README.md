# Shared Python Libraries for dev-rerickso/src

A collection of reusable Python utilities extracted from the `get_scheduler` library and designed to be shared across all Python projects in the `src/` directory.

## Overview

This shared library provides consistent, well-tested utilities for common operations across Python projects in the workspace. All utilities follow the workspace philosophy of simple bash wrappers with Python implementations and maintain zero external dependencies.

## Quick Start

### 🚀 New Projects
Use the complete project template:
```bash
cp -r src/shared_libs/templates/python_project/ src/your_new_project/
# See ../SHARED_LIBS_MIGRATION_GUIDE.md for complete setup guide
```

### 🔧 Existing Projects  
Add shared_libs imports:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  # Adjust path to src/

# Use shared utilities:
from shared_libs.common import setup_logging
from shared_libs.io_utils import CSVWriter
from shared_libs.cmd_utils import SubprocessClient
```

### 📚 Complete Documentation
See [`../SHARED_LIBS_MIGRATION_GUIDE.md`](../SHARED_LIBS_MIGRATION_GUIDE.md) for:
- ✅ **Complete migration guide** with real examples
- ✅ **Project template usage** for new tools
- ✅ **acl-tool success story** - full working example  
- ✅ **Migration patterns** by project type
- ✅ **Testing and validation** approaches

### Bash Wrapper Integration

For projects following the workspace pattern with bash wrappers:

```bash
# In your .sh script:
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export PYTHONPATH="${REPO_ROOT}/src/shared_libs:${PYTHONPATH}"

# Then your Python script can import directly:
# from shared_libs.common import setup_logging
```

## Available Modules

### `shared_libs.common` - Core Utilities

**Logging Setup**
```python
from shared_libs.common import setup_logging

logger = setup_logging(verbose=True, log_file="./my_tool.log")
logger.info("Standardized logging across all tools")
```

**Error Pattern Detection** 
```python  
from shared_libs.common import ErrorPatternDetector

detector = ErrorPatternDetector(timeout=30)
error_info = detector.classify_error(command_output)
if error_info:
    print(f"Detected {error_info.category}: {error_info.message}")
```

**Progress Tracking**
```python
from shared_libs.common import ProgressTracker

tracker = ProgressTracker(total_items=100)
for item in items:
    # ... process item ...
    tracker.update(1)
    if tracker.should_report():
        print(f"Progress: {tracker.get_status()}")
```

### `shared_libs.io_utils` - I/O Operations

**CSV Writing**
```python
from shared_libs.io_utils import CSVWriter

writer = CSVWriter("results.csv", console_output=True)
writer.write_results([
    {"service": "myapp", "status": "healthy", "scheduler": "kubernetes"},
    {"service": "webapp", "status": "degraded", "scheduler": "yarn"}
])
```

**Output Management**
```python
from shared_libs.io_utils import OutputManager

manager = OutputManager(
    csv_file="results.csv",
    log_file="details.log", 
    console_output=True
)
manager.write_result(service_result)
manager.finalize()
```

### `shared_libs.cmd_utils` - Command Execution

**Subprocess Execution**
```python
from shared_libs.cmd_utils import SubprocessClient

client = SubprocessClient(timeout=30, verbose=True)
result = client.run_command(["acl-tool", "rule", "list", resource_urn])

if result.success:
    print(f"Output: {result.output}")
else:
    print(f"Error: {result.error_info}")
```

**Specialized Command Wrappers**
```python
from shared_libs.cmd_utils import GoStatusClient, KubectlClient

# For go-status operations:
go_client = GoStatusClient(timeout=30)
service_info = go_client.query_service("my-service")

# For kubectl operations:
kubectl_client = KubectlClient(timeout=30)
pods = kubectl_client.get_pods("my-service", context="prod")
```

## Integration Examples

### Upgrading acl-tool Project

**Before:**
```python
# acl-tool/acl_tool_lib.py
def log(message: str) -> None:
    print(f"[{datetime.now()}] {message}")

def run_command(cmd: List[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, **kwargs)
```

**After:**
```python  
# acl-tool/acl_tool_lib.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared_libs'))

from shared_libs.common import setup_logging
from shared_libs.cmd_utils import SubprocessClient

logger = setup_logging(verbose=True, log_file="acl_tool.log")
cmd_client = SubprocessClient(timeout=30, verbose=True)

def run_acl_command(cmd: List[str]) -> Dict[str, Any]:
    result = cmd_client.run_command(cmd)
    if result.success:
        logger.info(f"ACL command succeeded: {' '.join(cmd)}")
        return {"success": True, "output": result.output}
    else:
        logger.error(f"ACL command failed: {result.error_info}")
        return {"success": False, "error": result.error_info}
```

### Upgrading asset_management Project

**Before:**
```python
# asset_management/lib/utils.py
def log(msg):
    print(f"{datetime.now().strftime('%Y.%m.%d:%H:%M:%S')} - {msg}")

def write_csv(filename, rows, fieldnames):
    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
```

**After:**
```python
# asset_management/lib/utils.py  
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared_libs'))

from shared_libs.common import setup_logging
from shared_libs.io_utils import CSVWriter

logger = setup_logging(verbose=False, log_file="asset_management.log") 

def log(msg):
    logger.info(msg)

def write_csv(filename, rows, fieldnames):
    writer = CSVWriter(filename, console_output=False)
    writer.fieldnames = fieldnames
    writer.write_results(rows)
```

## Design Principles

### Zero External Dependencies
All shared libraries use only Python standard library modules:
- `subprocess`, `logging`, `csv`, `datetime`, `os`, `re`, `sys`
- No third-party dependencies to avoid version conflicts
- Easy to use across different Python environments

### Workspace Pattern Compliance
- Follows bash wrapper + Python implementation pattern
- Integrates with existing `bash/common/repo_lib.sh` utilities
- Maintains consistency with workspace coding standards

### Robust Error Handling
- Comprehensive timeout management for all operations
- Pattern-based error detection and classification  
- Graceful degradation and informative error messages
- Signal handling for clean shutdown

### Type Safety and Documentation
- Full type hints on all public interfaces
- Dataclasses for structured data with validation
- Comprehensive docstrings with usage examples
- Clean, discoverable APIs

## Testing

Run the test suite:

```bash
cd /path/to/src/shared_libs
python -m pytest tests/
```

For specific test categories:
```bash
python -m pytest tests/test_common/      # Test common utilities
python -m pytest tests/test_io_utils/    # Test I/O operations  
python -m pytest tests/test_cmd_utils/   # Test command execution
```

## Migration Guide

### Step 1: Update Import Path
Add shared library path to your Python imports:
```python
sys.path.insert(0, '../shared_libs')  # Adjust path as needed
```

### Step 2: Replace Utility Functions
- Replace basic `log()` functions with `setup_logging()`
- Replace `subprocess.run()` calls with `SubprocessClient`
- Replace simple CSV writing with `CSVWriter` class

### Step 3: Add Error Handling
- Use `ErrorPatternDetector` for robust error classification
- Add progress tracking for long-running operations
- Implement graceful shutdown with `SignalHandler`

### Step 4: Test Integration
- Verify existing functionality works unchanged
- Add tests using shared library test utilities
- Validate performance and error handling

## Contributing

When adding new shared utilities:

1. **Maintain Zero Dependencies**: Only use Python standard library
2. **Add Comprehensive Tests**: Include unit tests and integration tests
3. **Document Thoroughly**: Add docstrings and usage examples
4. **Follow Type Hints**: Use proper type annotations
5. **Consider Reusability**: Design for multiple use cases across projects

## Architecture

```
src/shared_libs/
├── __init__.py                  # Main package exports and documentation
├── README.md                    # This file
├── requirements.txt             # Dependencies (currently empty - standard lib only)
│
├── common/                      # Core utilities
│   ├── __init__.py
│   ├── logging_utils.py         # Standardized logging setup  
│   ├── error_handling.py        # Error pattern detection and classification
│   ├── progress_tracking.py     # Progress reporting and time estimation
│   └── signal_handling.py       # Graceful shutdown handling
│
├── io_utils/                    # I/O operations
│   ├── __init__.py
│   ├── csv_writer.py           # Robust CSV output with escaping
│   ├── log_writer.py           # Structured log file output
│   ├── output_manager.py       # Multi-format output coordination
│   └── file_validator.py       # File validation and disk space checking
│
├── cmd_utils/                   # Command execution
│   ├── __init__.py  
│   ├── subprocess_client.py     # Robust subprocess execution
│   ├── timeout_manager.py      # Timeout and retry logic
│   └── command_wrappers.py     # Specialized tool wrappers (go-status, kubectl, etc.)
│
└── tests/                       # Comprehensive test suite
    ├── __init__.py
    ├── test_common/            # Tests for common utilities
    ├── test_io_utils/          # Tests for I/O operations
    └── test_cmd_utils/         # Tests for command execution
```

## Version History

- **1.0.0**: Initial implementation extracted from get_scheduler library
  - Core logging, I/O, and command execution utilities
  - Zero external dependencies
  - Full test coverage and documentation