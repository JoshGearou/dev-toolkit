#!/usr/bin/env python3
"""
Simplified Flake8 Reporter

A streamlined tool to run flake8 and generate both human-readable summaries
and structured JSON reports suitable for LLM consumption.

Follows project's Domain Driven Design principles with simple, focused design.
"""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class Issue:
    """Simple representation of a flake8 issue."""

    path: str
    line: int
    col: int
    code: str
    msg: str


@dataclass
class FileReport:
    """Issues for a single file."""

    path: str
    issues: List[Issue]

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    @property
    def is_clean(self) -> bool:
        return self.issue_count == 0


def run_flake8(paths: List[str]) -> List[str]:
    """Run flake8 and return output lines."""
    cmd = [
        sys.executable,
        "-m",
        "flake8",
        "--exclude=.venv,venv,__pycache__,.git,target,build,dist,.tox,.pytest_cache",
    ] + paths
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        return []


def parse_flake8_output(lines: List[str], repo_root: Path) -> List[Issue]:
    """Parse flake8 output into Issue objects."""
    issues: List[Issue] = []
    pattern = re.compile(r"^([^:]+):(\d+):(\d+):\s+([A-Z]\d+)\s+(.+)$")

    for line in lines:
        if not line.strip():
            continue

        match = pattern.match(line.strip())
        if not match:
            continue

        file_path, line_num, col_num, error_code, message = match.groups()

        # Convert to relative path
        try:
            abs_path = Path(file_path).resolve()
            rel_path = str(abs_path.relative_to(repo_root))
        except (ValueError, OSError):
            rel_path = file_path

        issues.append(
            Issue(
                path=rel_path,
                line=int(line_num),
                col=int(col_num),
                code=error_code,
                msg=message,
            )
        )

    return issues


def find_python_files(repo_root: Path) -> List[str]:
    """Find all Python files in the repository."""
    exclude_patterns = {
        ".venv",
        "venv",
        "__pycache__",
        ".git",
        "target",
        "build",
        "dist",
        ".tox",
        ".pytest_cache",
    }
    python_files: List[str] = []

    for py_file in repo_root.rglob("*.py"):
        # Skip if any parent directory matches exclude patterns
        rel_path_parts = py_file.relative_to(repo_root).parts
        if any(pattern in rel_path_parts for pattern in exclude_patterns):
            continue
        # Also skip any path containing "venv" anywhere (e.g., myproject/.venv,
        # .venv, project_venv)
        if any("venv" in part.lower() for part in rel_path_parts):
            continue
        try:
            rel_path = str(py_file.relative_to(repo_root))
            python_files.append(rel_path)
        except ValueError:
            continue

    return sorted(python_files)


def generate_json_report(issues: List[Issue], repo_root: Path, timestamp: str) -> Dict[str, Any]:
    """Generate LLM-friendly JSON report."""
    # Group issues by file
    files_with_issues: Dict[str, List[Dict[str, Any]]] = {}
    for issue in issues:
        if issue.path not in files_with_issues:
            files_with_issues[issue.path] = []
        files_with_issues[issue.path].append(
            {
                "line": issue.line,
                "col": issue.col,
                "code": issue.code,
                "msg": issue.msg,
            }
        )

    # Count error types
    error_counts = Counter(issue.code for issue in issues)

    # Get all Python files for clean/total counts
    all_python_files = find_python_files(repo_root)
    files_with_issues_count = len(files_with_issues)
    clean_files_count = len(all_python_files) - files_with_issues_count

    return {
        "timestamp": timestamp,
        "summary": {
            "total_files": len(all_python_files),
            "clean_files": clean_files_count,
            "files_with_issues": files_with_issues_count,
            "total_issues": len(issues),
        },
        "files": [{"path": path, "issues": file_issues} for path, file_issues in sorted(files_with_issues.items())],
        "error_summary": dict(error_counts.most_common()),
    }


def generate_human_summary(json_report: Dict[str, Any]) -> str:
    """Generate human-readable summary from JSON report."""
    summary = json_report["summary"]
    files = json_report["files"]
    errors = json_report["error_summary"]

    # Calculate percentages
    total_files = summary["total_files"]
    clean_pct = (summary["clean_files"] / total_files * 100) if total_files > 0 else 100

    # Build summary text
    lines = [
        f"Flake8 Report Summary - {json_report['timestamp']}",
        "",
        "📊 OVERVIEW",
        f"  Total Files: {total_files} Python files checked",
        f"  Clean Files: {summary['clean_files']} ({clean_pct:.1f}% - {'Good!' if clean_pct >= 70 else 'Needs work'})",  # noqa: E501
        f"  Files with Issues: {summary['files_with_issues']} ({100 - clean_pct:.1f}%)",
        f"  Total Issues: {summary['total_issues']}",
        "",
    ]

    # Top issues
    if errors:
        lines.extend(
            [
                "🔥 TOP ISSUES",
                *[
                    f"  {i + 1}. {code}: {count} occurrences"
                    for i, (code, count) in enumerate(list(errors.items())[:5])
                ],
            ]
        )
        lines.append("")

    # Worst files
    if files:
        worst_files = sorted(files, key=lambda f: len(f["issues"]), reverse=True)[:5]
        lines.extend(
            [
                "📁 WORST FILES",
                *[f"  {i + 1}. {f['path']}: {len(f['issues'])} issues" for i, f in enumerate(worst_files)],
            ]
        )
        lines.append("")

    # Recommendations
    lines.extend(
        [
            "💡 RECOMMENDATIONS",
            "  - Run `./flake8_autofix.sh --safe` to fix formatting issues automatically",  # noqa: E501
        ]
    )

    if "F401" in errors:
        lines.append("  - Focus manual review on F401 (unused imports)")

    lines.extend(
        [
            "  - Consider adding flake8 to pre-commit hooks",
            "",
            f"Full details in: {
                json_report['timestamp'].replace(
                    ':',
                    '')}_flake8_report.json",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate flake8 reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Report on current directory
  %(prog)s --json-only                  # Generate only JSON report (LLM-friendly)
  %(prog)s --summary-only               # Generate only human summary
  %(prog)s src/ tests/                  # Report on specific directories
  %(prog)s --verbose                    # Detailed output during execution
        """,
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Paths to check (default: current directory)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./reports"),
        help="Output directory (default: ./reports)",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Generate only JSON report (no human summary)",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Generate only human summary (no JSON)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output during execution",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be reported without creating files",
    )

    args = parser.parse_args()

    # Validate mutually exclusive options
    if args.json_only and args.summary_only:
        print(
            "Error: --json-only and --summary-only are mutually exclusive",
            file=sys.stderr,
        )
        return 1

    # Find repo root
    repo_root = Path.cwd()
    while repo_root.parent != repo_root:
        if (repo_root / ".git").exists() or (repo_root / "Cargo.toml").exists():
            break
        repo_root = repo_root.parent

    if args.verbose:
        print(f"Repository root: {repo_root}")
        print(f"Checking paths: {args.paths}")

    # Run flake8
    flake8_output = run_flake8(args.paths)
    issues = parse_flake8_output(flake8_output, repo_root)

    if args.verbose:
        print(f"Found {len(issues)} flake8 issues")

    # Generate reports
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    json_report = generate_json_report(issues, repo_root, timestamp)
    human_summary = generate_human_summary(json_report)

    # Handle dry-run mode
    if args.dry_run:
        print("DRY RUN - No files will be created")
        print("\nWould generate:")
        if not args.summary_only:
            print(f"  JSON: {timestamp.replace(':', '')}_flake8_report.json")
        if not args.json_only:
            print(f"  Summary: {timestamp.replace(':', '')}_flake8_summary.txt")
        print("\nReport content:")
        print(human_summary)
        return 1 if issues else 0

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    generated_files: List[str] = []

    # Write JSON report (LLM-friendly) unless summary-only
    if not args.summary_only:
        json_filename = f"{timestamp.replace(':', '')}_flake8_report.json"
        json_path = args.output_dir / json_filename
        with open(json_path, "w") as f:
            json.dump(json_report, f, indent=2)
        generated_files.append(f"JSON: {json_path}")
        if args.verbose:
            print(f"Generated JSON report: {json_path}")

    # Write human summary unless json-only
    if not args.json_only:
        summary_filename = f"{timestamp.replace(':', '')}_flake8_summary.txt"
        summary_path = args.output_dir / summary_filename
        with open(summary_path, "w") as f:
            f.write(human_summary)
        generated_files.append(f"Summary: {summary_path}")
        if args.verbose:
            print(f"Generated summary report: {summary_path}")

    # Print to console (unless json-only mode)
    if not args.json_only:
        print(human_summary)

    # Show generated files
    if generated_files:
        print("\nReports saved:")
        for file_info in generated_files:
            print(f"  {file_info}")

    # Exit with error code if issues found
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
