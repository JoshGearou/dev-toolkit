# PR Quality Check Scripts

Comprehensive PR quality assessment tool for GitHub pull requests with intelligent retry logic and fiscal year-aware defaults.

## Overview

The PR Quality Check tool analyzes merged pull requests to assess code review quality across multiple dimensions:

- **Description Quality** (25%) - Detailed PR descriptions with structure
- **Testing Evidence** (25%) - Test files in diff and testing documentation
- **PR Size** (20%) - Appropriate sizing for reviewability
- **Review Coverage** (20%) - Peer review and approval status
- **Traceability** (10%) - JIRA references and labels
- **Post-Merge CI/CD** - Build/test status after merge

## Quick Start

```bash
# Analyze all PRs across all repositories (default: summary format)
./pr_quality_check.sh {gh-username}

# Analyze PRs in a specific repository
./pr_quality_check.sh {gh-username} --repo {gh-org-name}/{repo-name}

# Custom date range
./pr_quality_check.sh {gh-username} --start 2025-01-01 --end 2025-12-31

# JSON output for automation/parsing
./pr_quality_check.sh username --format json > results.json
```

## Features

### Automatic Fiscal Year Defaults

By default, the tool analyzes PRs from the current Microsoft fiscal year:
- **FY26**: July 1, 2025 to June 30, 2026
- **FY27**: July 1, 2026 to June 30, 2027

The fiscal year is automatically calculated based on the current date.

### Exponential Backoff Retry

Handles GitHub API rate limits gracefully:
- **Max retries**: 20 attempts
- **Exponential backoff**: Doubles wait time each retry (2^n seconds)
- **Cap per retry**: Maximum 5 minutes per wait
- **Total wait time**: Up to ~1 hour before giving up
- **Progress updates**: Real-time wait time notifications

Example retry output:
```
⚠ Rate limit hit, waiting 2m30s (total waited: 5m15s) - retry 8/20...
```

### Multi-Repository Support

**Default Behavior**: Searches across ALL accessible repositories
```bash
./pr_quality_check.sh username
# Searches all repos the user has access to
```

**Single Repository**: Use `--repo` to filter to specific repository
```bash
./pr_quality_check.sh username --repo owner/repo-name
# Only searches the specified repository
```

## Installation

### Prerequisites

```bash
# Install GitHub CLI
brew install gh

# Authenticate with GitHub
gh auth login

# Verify Python 3 is installed
python3 --version
```

### Setup

The bash wrapper script automatically:
1. Creates a Python virtual environment (`.venv`)
2. Installs dependencies (none required - uses Python stdlib only)
3. Activates the environment and runs the script

## Usage

### Command Line Arguments

```bash
pr_quality_check.sh <username> [OPTIONS]

Required:
  username              GitHub username to analyze

Optional:
  --repo REPO          Repository in owner/repo format
                       (default: search all accessible repositories)

  --start DATE         Start date in YYYY-MM-DD format
                       (default: current fiscal year start)

  --end DATE           End date in YYYY-MM-DD format
                       (default: current fiscal year end)

  --threshold N        Quality score threshold (default: 70)

  --format FORMAT      Output format: json or summary (default: summary)
```

### Output Formats

#### Summary Format (default)

Human-readable report with visual indicators - perfect for quick reviews and terminal output:

```
============================================================
PR QUALITY REPORT: {gh-username}
============================================================
Repository: All repositories
Date Range: 2025-07-01 to 2026-06-30

ACTIVITY STATS:
  Total PRs Merged: 17
  Total PRs Reviewed: 52
  PRs Analyzed: 17

QUALITY METRICS:
  Average Quality Score: 89.1/100
  PRs Below Threshold (70): 0
  Critical Issues Found: 2
  Post-Merge CI Failures: 2

----------------------------------------
GRADE DISTRIBUTION
----------------------------------------
  A (90-100): 13 █████████████
  B (80-89):  2 ██
  C (70-79):  2 ██
  D (60-69):  0
  F (<60):  0

----------------------------------------
CATEGORY SCORES (Average)
----------------------------------------
  description    : 100.0/100 ██████████
  testing        :  93.2/100 █████████░
  size           :  89.4/100 ████████░░
  review         : 100.0/100 ██████████
  traceability   :  30.0/100 ███░░░░░░░
```

#### JSON Format

Machine-readable JSON with complete analysis - use `--format json` for automation:

```json
{
  "github_username": "{gh-username}",
  "repository": "All repositories",
  "date_range": "2025-07-01 to 2026-06-30",
  "total_prs_merged": 17,
  "total_prs_reviewed": 52,
  "prs_analyzed": 17,
  "average_quality_score": 89.1,
  "prs_below_threshold": 0,
  "prs_with_post_merge_failures": 2,
  "quality_threshold": 70,
  "summary": {
    "issue_frequency": { "No JIRA ticket reference": 17 },
    "grade_distribution": { "A (90-100)": 13, "B (80-89)": 2 },
    "category_averages": { "description": 100.0, "testing": 93.2 },
    "post_merge_ci_status": { "success": 15, "failure": 2 }
  },
  "prs": [ ... ]
}
```

## Quality Scoring

### Scoring Categories

Each PR receives a score (0-100) based on weighted categories:

| Category | Weight | Criteria |
|----------|--------|----------|
| Description | 25% | Length, structure, clarity |
| Testing | 25% | Test files, testing documentation |
| Size | 20% | Lines changed, files modified |
| Review | 20% | Peer review, approvals |
| Traceability | 10% | JIRA references, labels |

### Letter Grades

- **A (90-100)**: Excellent - Best practices followed
- **B (80-89)**: Good - Minor improvements needed
- **C (70-79)**: Acceptable - Some issues present
- **D (60-69)**: Below threshold - Multiple issues
- **F (<60)**: Failing - Significant quality concerns

### Critical Issues

Issues marked as CRITICAL include:
- Empty or missing PR description
- No testing evidence (no tests, no testing section)
- Self-merged without review
- Post-merge CI/CD failures

## Testing

### Running Tests

The project includes comprehensive unit tests covering all major functionality:

```bash
# Run all tests with verbose output
source .venv/bin/activate
python -m pytest test_pr_quality_check.py -v

# Run specific test class
python -m pytest test_pr_quality_check.py::TestHelperFunctions -v

# Run with coverage report
python -m pytest test_pr_quality_check.py --cov=pr_quality_check --cov-report=html
```

### Test Coverage

The test suite covers:
- **Helper functions** - Grade calculation, PR size categorization, fiscal year dates
- **GitHub commands** - API calls, retry logic, rate limit handling
- **PR data fetching** - Repository queries, diff analysis, review counting
- **Post-merge CI/CD** - Status checking, failure detection, URL generation
- **Quality analysis** - Scoring logic for all quality categories
- **Report generation** - Summary statistics, grade distribution, issue frequency
- **Data structures** - Dataclass defaults and validation

31 tests ensure reliability of the quality assessment logic.

## Files

- **`pr_quality_check.py`** - Main Python script with quality analysis logic
- **`pr_quality_check.sh`** - Bash wrapper with venv management
- **`test_pr_quality_check.py`** - Comprehensive unit tests (31 tests)
- **`requirements.txt`** - Python dependencies (pytest for testing)
- **`README.md`** - This file

## Technical Details

### Dependencies

The tool uses only Python standard library:
- `argparse` - Command-line argument parsing
- `json` - JSON data handling
- `subprocess` - GitHub CLI invocation
- `datetime` - Date calculations
- `time` - Retry delays
- `dataclasses` - Data structure definitions
- `re` - Regular expression matching

### GitHub API Usage

Uses GitHub CLI (`gh`) for API access:
- `gh pr list` - List PRs in specific repository
- `gh search prs` - Search PRs across all repositories
- `gh pr view` - Fetch detailed PR information
- `gh pr diff` - Get file changes for test detection
- `gh api` - Check post-merge CI/CD status

### Rate Limiting

GitHub API has rate limits:
- **Authenticated**: 5,000 requests/hour
- **Search API**: 30 requests/minute

The retry logic handles rate limit errors automatically with exponential backoff.

Check your rate limit status:
```bash
gh api rate_limit
```

## Examples

### Promotion Assessment

Analyze PR quality for promotion review:

```bash
# Get comprehensive JSON report
./pr_quality_check.sh {gh-username} --format json > candidate_prs.json

# Get human-readable summary
./pr_quality_check.sh {gh-username} --format summary
```

### Team Quality Analysis

Analyze multiple team members:

```bash
for user in user1 user2 user3; do
  echo "Analyzing ${user}..."
  ./pr_quality_check.sh "${gh-user}" --format json > "reports/${user}.json"
done
```

### Specific Repository Analysis

Focus on a single repository:

```bash
./pr_quality_check.sh username --repo org/repo-name --format summary
```

### Historical Analysis

Analyze PRs from a specific time period:

```bash
# Calendar year 2025
./pr_quality_check.sh username --start 2025-01-01 --end 2025-12-31

# Q1 2026
./pr_quality_check.sh username --start 2026-01-01 --end 2026-03-31

# Previous fiscal year (FY25)
./pr_quality_check.sh username --start 2024-07-01 --end 2025-06-30
```

## Troubleshooting

### GitHub CLI Not Found

```bash
# Install GitHub CLI
brew install gh

# Or download from: https://cli.github.com/
```

### Not Authenticated

```bash
# Authenticate with GitHub
gh auth login

# Verify authentication
gh auth status
```

### Rate Limit Exceeded

If you hit rate limits:
1. Wait for the script to retry automatically (up to 1 hour)
2. Check remaining quota: `gh api rate_limit`
3. Rate limits reset every hour
4. Consider reducing the number of PRs analyzed with date range filters

### Virtual Environment Issues

```bash
# Remove and recreate virtual environment
rm -rf .venv
./pr_quality_check.sh username
```

### No PRs Found

If the script reports 0 PRs:
1. Verify the username is correct
2. Check the date range covers when PRs were merged
3. Verify repository access (if using `--repo`)
4. Try searching all repos without `--repo` flag

## Best Practices

### For Individual Assessment

```bash
# Use all repos to get complete picture
./pr_quality_check.sh username --format summary

# Focus on current fiscal year (default)
./pr_quality_check.sh username
```

### For Automation

```bash
# Use JSON format for parsing
./pr_quality_check.sh username --format json | jq '.average_quality_score'

# Save results for later analysis
./pr_quality_check.sh username --format json > "reports/$(date +%Y%m%d)_username.json"
```

### For Large Result Sets

When analyzing users with many PRs:
1. Start with a smaller date range to test
2. Use `--format json` to avoid large terminal output
3. Let the retry logic handle rate limits automatically
4. Consider running overnight for very large datasets

## Contributing

When modifying the scripts:
1. Maintain backward compatibility
2. Follow the Python `mypy --strict` and `flake8` standards
3. Test both JSON and summary output formats
4. Verify retry logic with rate limit scenarios
5. Update this README with any new features or changes

## See Also

- [GitHub CLI Documentation](https://cli.github.com/manual/)
- [Microsoft Fiscal Year Calendar](https://www.microsoft.com/en-us/Investor/fiscal-year-calendar.aspx)
