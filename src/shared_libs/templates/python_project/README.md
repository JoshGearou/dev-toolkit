# Python Project Template for dev-rerickso/src

This template provides a standardized structure for Python projects in the dev-rerickso workspace that use shared_libs utilities.

## Template Structure

```
project_name/
├── project_name.sh              # Bash wrapper (follows repo patterns)
├── project_name.py              # Main Python script
├── lib/                         # Domain-specific logic (if needed)
│   ├── __init__.py
│   └── project_specific.py      # Project-specific utilities
├── requirements.txt             # External dependencies (if any)
├── .venv/                       # Virtual environment (created by .sh)
└── README.md                    # Project documentation
```

## Usage

1. Copy this template to your new project directory
2. Rename files to match your project name  
3. Update imports and customize functionality
4. Follow the established patterns for bash wrappers and Python implementation

## Key Patterns

### Bash Wrapper Pattern
```bash
#!/bin/bash

# Source common repository functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$REPO_ROOT/bash/common/repo_lib.sh"

# Set up Python environment and shared libraries
setup_python_environment() {
    local venv_dir="$SCRIPT_DIR/.venv"
    
    if [[ ! -d "$venv_dir" ]]; then
        log_message "Creating Python virtual environment"
        python3 -m venv "$venv_dir"
    fi
    
    source "$venv_dir/bin/activate"
    
    # Add shared_libs to PYTHONPATH
    export PYTHONPATH="$REPO_ROOT/src/shared_libs:${PYTHONPATH:-}"
}

# Main execution
main() {
    log_message "Starting project_name"
    setup_python_environment
    
    # Forward all arguments to Python script
    exec python3 "$SCRIPT_DIR/project_name.py" "$@"
}

# Run main function
main "$@"
```

### Python Implementation Pattern
```python
#!/usr/bin/env python3
"""
Project Name - Description of what this tool does

Usage:
    project_name.py [options]
    
Example:
    project_name.py --input file.csv --output results.csv
"""

import argparse
import sys
from pathlib import Path

# Add shared_libs to path (in case PYTHONPATH not set)
sys.path.insert(0, str(Path(__file__).parent.parent / "shared_libs"))

# Import shared utilities
from shared_libs.common.logging_utils import setup_logging, create_project_logger
from shared_libs.io_utils.csv_writer import CSVWriter
from shared_libs.cmd_utils.subprocess_client import SubprocessClient

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Project description")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose logging")
    parser.add_argument("--output-file", "-o", 
                       help="Output file path")
    
    args = parser.parse_args()
    
    # Set up logging using shared utilities
    logger = setup_logging(
        log_file="project_name.log",
        logger_name="project_name",
        verbose=args.verbose
    )
    
    logger.info("Starting project_name processing")
    
    try:
        # Use shared utilities for common operations
        subprocess_client = SubprocessClient()
        csv_writer = CSVWriter()
        
        # Your project-specific logic here
        process_data(logger, subprocess_client, csv_writer, args)
        
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        sys.exit(1)
    
    logger.info("Processing completed successfully")

def process_data(logger, subprocess_client, csv_writer, args):
    """Project-specific data processing logic"""
    # Example usage of shared utilities:
    
    # Execute external commands
    result = subprocess_client.execute_command(
        ["echo", "Hello World"],
        timeout=10
    )
    
    if result.success:
        logger.info(f"Command output: {result.stdout}")
    
    # Write CSV output
    if args.output_file:
        data = [{"message": "Hello", "timestamp": "2025-10-10"}]
        csv_writer.write_csv(args.output_file, data, fieldnames=["message", "timestamp"])

if __name__ == "__main__":
    main()
```

## Integration with shared_libs

This template demonstrates proper usage of shared libraries:

### Logging
```python
from shared_libs.common.logging_utils import setup_logging, create_project_logger

# Set up structured logging
logger = setup_logging(
    log_file="project.log",
    logger_name="project_name",
    verbose=True
)
```

### CSV Output  
```python
from shared_libs.io_utils.csv_writer import CSVWriter

csv_writer = CSVWriter()
csv_writer.write_csv("output.csv", data, fieldnames=["col1", "col2"])
```

### Command Execution
```python
from shared_libs.cmd_utils.subprocess_client import SubprocessClient

client = SubprocessClient()
result = client.execute_command(["ls", "-la"], timeout=30)
if result.success:
    print(result.stdout)
```

### Error Handling
```python
from shared_libs.common.error_handling import ErrorPatternDetector

detector = ErrorPatternDetector()
errors = detector.detect_errors(command_output)
if errors:
    logger.warning(f"Detected {len(errors)} potential issues")
```

## Migration from Existing Projects

When migrating existing projects to use shared_libs:

1. **Replace basic logging**: Replace simple `print()` or basic `log()` functions with shared_libs logging
2. **Upgrade subprocess calls**: Replace direct `subprocess.run()` with SubprocessClient for better error handling
3. **Standardize CSV output**: Replace basic CSV writing with CSVWriter for consistent formatting
4. **Add error detection**: Use ErrorPatternDetector for command output analysis
5. **Update imports**: Follow the import patterns shown above

## Benefits

- **Consistent error handling** across all projects
- **Standardized logging** with unified format and file output
- **Robust subprocess execution** with timeout and retry logic
- **Professional CSV output** with proper escaping and headers
- **Type safety** with comprehensive type hints
- **Easy maintenance** through shared code reduction