#!/usr/bin/env python3
"""
Project Name - Template for Python projects using shared_libs

This template demonstrates proper usage of shared_libs utilities and follows
the dev-rerickso repository patterns for Python project structure.

Usage:
    project_name.py [options]

Example:
    project_name.py --verbose --output-file results.csv --input data.csv

Features:
    - Structured logging using shared_libs
    - Robust CSV output with proper escaping
    - External command execution with timeout/retry
    - Error pattern detection
    - Type safety with comprehensive hints
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from shared_libs.cmd_utils.subprocess_client import CommandConfig, SubprocessClient
from shared_libs.common.error_handling import ErrorPatternDetector
from shared_libs.common.logging_utils import setup_logging
from shared_libs.io_utils.csv_writer import CSVSerializable, CSVWriter
from shared_libs.io_utils.file_validator import FileValidator

# Ensure shared_libs is available (fallback if PYTHONPATH not set)
# For the template in templates/python_project, need to go up to src/ level
# Ensure shared_libs is available (fallback if PYTHONPATH not set)
# Navigate from templates/python_project/ up to src/ directory
src_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(src_dir))


# Import shared utilities


class ProjectConfig:
    """Configuration for the project"""

    def __init__(self) -> None:
        self.input_file: Optional[str] = None
        self.output_file: str = "output.csv"
        self.verbose: bool = False
        self.timeout: int = 30


class DataItem(CSVSerializable):
    """Example data structure that can be serialized to CSV"""

    def __init__(self, name: str, value: int, status: str):
        self.name = name
        self.value = value
        self.status = status

    def to_csv_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV output"""
        return {
            "name": self.name,
            "value": self.value,
            "status": self.status,
            "timestamp": "2025-10-10T12:00:00Z",  # Example computed field
        }


def parse_arguments() -> ProjectConfig:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Template Python project using shared_libs utilities",
        epilog="Example: %(prog)s --verbose --output-file results.csv",
    )

    parser.add_argument("--input-file", "-i", help="Input file to process")

    parser.add_argument(
        "--output-file",
        "-o",
        default="output.csv",
        help="Output CSV file (default: output.csv)",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=30,
        help="Command timeout in seconds (default: 30)",
    )

    args = parser.parse_args()

    config = ProjectConfig()
    config.input_file = args.input_file
    config.output_file = args.output_file
    config.verbose = args.verbose
    config.timeout = args.timeout

    return config


def validate_inputs(config: ProjectConfig, logger: logging.Logger) -> bool:
    """Validate input parameters using shared utilities"""
    validator = FileValidator()

    # Validate input file if provided
    if config.input_file:
        if not os.path.exists(config.input_file):
            logger.error(f"Input file not found: {config.input_file}")
            return False

        if not os.access(config.input_file, os.R_OK):
            logger.error(f"Input file not readable: {config.input_file}")
            return False

    # Validate output file path using shared utilities
    try:
        validator.validate_output_file(config.output_file)
        logger.debug(f"Output file path validated: {config.output_file}")
    except Exception as e:
        logger.error(f"Output file validation failed: {e}")
        return False

    return True


def execute_external_commands(config: ProjectConfig, logger: logging.Logger) -> List[str]:
    """Example of external command execution using shared utilities"""
    logger.info("Executing external commands for data gathering")

    # Create subprocess client with configuration
    command_config = CommandConfig(timeout=config.timeout, retries=3, retry_delay=1.0)

    subprocess_client = SubprocessClient(command_config)

    # Create error detector for command output
    error_detector = ErrorPatternDetector()

    results = []

    # Example commands (customize for your project)
    commands = [
        ["echo", "Processing data..."],
        ["date", "+%Y-%m-%d %H:%M:%S"],
        ["whoami"],
        ["pwd"],
    ]

    for cmd in commands:
        logger.debug(f"Executing command: {' '.join(cmd)}")

        result = subprocess_client.execute_command(cmd)

        if result.success:
            logger.debug(f"Command succeeded: {result.output.strip()}")
            results.append(result.output.strip())

            # Check for error patterns in output
            error_info = error_detector.detect_error_patterns(result.output, result.return_code, " ".join(cmd))
            if error_info.is_error:
                logger.warning(f"Detected potential issue: {error_info.message}")
        else:
            logger.error(f"Command failed: {' '.join(cmd)}")
            logger.error(f"Error: {result.error_output}")

    return results


def process_data(config: ProjectConfig, logger: logging.Logger, command_results: List[str]) -> List[DataItem]:
    """Process data and create output structures"""
    logger.info("Processing collected data")

    data_items = []

    # Example data processing (customize for your project)
    for i, result in enumerate(command_results):
        item = DataItem(name=f"item_{i}", value=len(result), status="processed")  # Example: length of command output
        data_items.append(item)
        logger.debug(f"Created data item: {item.name} with value {item.value}")

    # Add some synthetic data for demonstration
    synthetic_items = [
        DataItem("synthetic_1", 42, "generated"),
        DataItem("synthetic_2", 100, "generated"),
        DataItem("error_case", -1, "failed"),
    ]

    data_items.extend(synthetic_items)

    logger.info(f"Generated {len(data_items)} data items for output")
    return data_items


def write_output(config: ProjectConfig, logger: logging.Logger, data_items: List[DataItem]) -> None:
    """Write results to CSV using shared utilities"""
    logger.info(f"Writing {len(data_items)} items to {config.output_file}")

    # Define output fields
    fieldnames = ["name", "value", "status", "timestamp"]

    # Create CSV writer with output file
    csv_writer = CSVWriter(output_file=config.output_file, fieldnames=fieldnames)

    # Write CSV file
    csv_writer.write_data(cast(List[Any], data_items))

    logger.info(f"Successfully wrote output to {config.output_file}")


def main() -> None:
    """Main entry point"""
    config = parse_arguments()

    # Set up logging using shared utilities
    logger = setup_logging(log_file="project_name.log", logger_name="project_name", verbose=config.verbose)

    logger.info("Starting project_name processing")
    logger.debug(
        f"Configuration: input={config.input_file}, output={config.output_file}, "
        f"verbose={config.verbose}, timeout={config.timeout}"
    )

    try:
        # Validate inputs
        if not validate_inputs(config, logger):
            logger.error("Input validation failed")
            sys.exit(1)

        # Execute external commands
        command_results = execute_external_commands(config, logger)

        # Process the data
        data_items = process_data(config, logger, command_results)

        # Write output
        write_output(config, logger, data_items)

        logger.info("Processing completed successfully")

    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Error during processing: {e}")
        if config.verbose:
            logger.exception("Full traceback:")
        sys.exit(1)


if __name__ == "__main__":
    main()
