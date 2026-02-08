# Claude Code Scripts

Utility scripts for managing Claude Code configuration, MCP servers, and customization.

## Scripts Overview

| Script | Description |
|--------|-------------|
| `statusline-command.sh` | Custom rainbow statusline for Claude Code |
| `deploy-statusline.sh` | Deploy/backup statusline to `~/.claude/` |
| `debug-statusline.sh` | Debug statusline with sample JSON input |
| `refresh-github-mcp.sh` | Refresh GitHub MCP server token |
| `scrub_claude_config.py` | Remove secrets from `.claude.json` for safe sharing |

---

## GitHub MCP Token Refresh

Refreshes the GitHub MCP server authentication when your token expires or rotates.

### Usage

```bash
# Refresh with default scope (local)
./refresh-github-mcp.sh

# Specify scope
./refresh-github-mcp.sh --scope user
./refresh-github-mcp.sh -s project
```

### Prerequisites

- `gh` CLI installed and authenticated (`gh auth login`)
- Docker running
- Claude Code CLI (`claude`) available

### What It Does

1. Verifies prerequisites (gh, docker, auth status)
2. Gets fresh token from `gh auth token`
3. Removes existing GitHub MCP config
4. Re-adds with fresh token using `claude mcp add`
5. Verifies connection

### When to Run

- After GitHub token rotation
- When GitHub MCP shows as disconnected in `/mcp`
- After `gh auth refresh`

---

## Config Scrubber

Removes secrets and PII from `.claude.json` for safe version control or sharing.

### Usage

```bash
# Default: reads ~/.claude.json, writes to ../config/claude.json
./scrub_claude_config.py

# Specify input/output files
./scrub_claude_config.py /path/to/input.json /path/to/output.json
```

### What Gets Scrubbed

| Type | Example Keys | Replacement Format |
|------|--------------|-------------------|
| Tokens | `GITHUB_PERSONAL_ACCESS_TOKEN`, `GLEAN_API_TOKEN` | `<SCRUBBED:token:key>` |
| UUIDs | `userID`, `accountUuid`, `organizationUuid` | `<SCRUBBED:uuid:key>` |
| Email | `emailAddress`, `email` | `<SCRUBBED:email:key>` |
| PII | `displayName`, `organizationName` | `<SCRUBBED:pii:key>` |
| Paths | `/Users/username/...` | `/Users/<SCRUBBED:username>/...` |

### Finding Scrubbed Values

```bash
grep '<SCRUBBED:' config/claude.json
```

---

## Custom Statusline

A colorful, rainbow-themed statusline for Claude Code that dynamically displays model information, context usage, Git status, and system information.

### Features

- **Dynamic Model Detection**: Automatically displays the current Claude model being used (e.g., Opus, Sonnet, Haiku)
- **Context Usage Visualization**: Shows percentage of context window used with color-coded thresholds
- **Git Integration**: Displays current branch, file change counts (modified/added/deleted), and unpushed commits
- **SSH Indicator**: Shows lightning bolt (⚡) when connected via SSH
- **Python Virtual Environment**: Displays active venv name with snake emoji (🐍)
- **Kubernetes Context**: Shows current k8s context with helm symbol (⎈), truncated for long names
- **System Information**: Shows hostname and current directory (truncated for long paths)
- **Rainbow Color Scheme**: Uses ANSI 256-color codes for a vibrant terminal display
- **Last Exit Status**: Shows success (✔) or failure (✘) with exit code

### Installation

#### Quick Install with Deploy Script

```bash
cd /Users/rerickso/src/sandbox/dev-rerickso/claude-dotfiles
./deploy.sh   # Deploys everything including statusline
```

#### Manual Installation

1. Copy the statusline script to your `~/.claude/` directory:
```bash
cp statusline-command.sh ~/.claude/
chmod +x ~/.claude/statusline-command.sh
```

2. Configure Claude Code to use the custom statusline by adding to `~/.claude/settings.json`:
```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline-command.sh",
    "padding": 0
  }
}
```

Alternatively, you can set it up interactively using the `/statusline` command within Claude Code.

### How It Works

Claude Code passes session context as JSON via stdin to the statusline script (see [official documentation](https://code.claude.com/docs/en/statusline#status-line-configuration)). The script:

1. Reads JSON data from stdin containing:
   - Model information (`display_name` and `id`)
   - Context window metrics (`max_tokens`, `used_percentage`)
   - Workspace details and session statistics

2. Extracts and formats the information:
   - Model name from `display_name` (e.g., "Opus") or falls back to `id`
   - Context size converted to thousands (e.g., "200k")
   - Percentage used with color coding

3. Displays a single-line status with ANSI rainbow colors

### Display Format

```
[ssh] [status] [hostname] [directory] [git branch/status/unpushed] [venv] [k8s] [model] [context] [usage%]
```

Example output:
```
⚡ ✔ macbook ~/projects master ~3+2 ↑1 🐍venv ⎈minikube Opus 200k 35%
```

Segments only appear when relevant:
- SSH indicator (⚡) only when connected remotely
- Unpushed count (↑n) only when commits exist ahead of upstream
- Venv (🐍name) only when a Python virtual environment is active
- K8s (⎈context) only when kubectl has a current context configured

### Color Scheme

#### Context Usage Display

- **XX%** - Context usage percentage
  - 🟢 Green: < 50% used
  - 🟡 Yellow: 50-75% used
  - 🟠 Orange: 75-90% used
  - 🔴 Red: > 90% used
- **90+** - 🔴 Red warning when `exceeds_200k_tokens` is true
- **0%** - Displays when percentage data is not yet available

#### Rainbow Elements
- SSH indicator: Yellow ⚡
- Status: Green ✔ for success, Red ✘ with exit code for errors
- Hostname: Orange
- Directory: Green
- Git branch: Blue
- Git changes: Purple
- Unpushed commits: Cyan ↑n
- Python venv: Green 🐍
- K8s context: Cyan ⎈
- Model: Magenta
- Context size: Blue

### Deploy Script Usage

The `deploy-statusline.sh` script helps manage statusline deployment:

```bash
# Deploy to ~/.claude/
./deploy-statusline.sh --deploy

# Backup changes from ~/.claude/ back to repo
./deploy-statusline.sh --backup

# Show current deployment status
./deploy-statusline.sh --status

# Show help
./deploy-statusline.sh --help
```

### Testing

You can test the statusline script standalone:

```bash
# Test without input (uses defaults)
~/.claude/statusline-command.sh

# Test with sample JSON input
echo '{"model":{"display_name":"Opus"},"max_tokens":200000,"used_percentage":35.5}' | ~/.claude/statusline-command.sh
```

### Customization

To modify the statusline:

1. Edit `statusline-command.sh` (or `~/.claude/statusline-command.sh` if already deployed)
2. Adjust colors by modifying the ANSI color codes at the top of the script
3. Change the display format in the final `echo` statement
4. Add or remove information segments as needed
5. Use `./deploy-statusline.sh --backup` to save changes back to the repo

#### Available JSON Fields from Claude Code

You can extract additional fields from the JSON input:
- `current_dir`: Current working directory
- `project_dir`: Project root directory
- `total_input_tokens`: Input tokens used
- `total_output_tokens`: Output tokens generated
- `cost`: Session cost information
- `duration`: Session duration

### Troubleshooting

#### Statusline Not Appearing
- Verify `~/.claude/settings.json` has the correct configuration
- Check that the script has execute permissions: `chmod +x ~/.claude/statusline-command.sh`
- Ensure the script outputs only one line to stdout

#### Colors Not Displaying
- Verify your terminal supports ANSI 256-color codes
- Check that color codes aren't being stripped by terminal settings

#### Model Shows as "claude"
- This is the default fallback when no model information is available
- Occurs when testing the script without JSON input
- In Claude Code, the actual model name should display automatically

#### Context Shows 0%
- Displays when Claude Code hasn't yet provided context usage data
- Normal at the start of a session before the first response
- The "90+" warning appears when `exceeds_200k_tokens` is true

---

## Related Documentation

- [MCP Troubleshooting Guide](../guides/mcp_troubleshooting_summary.md) - Comprehensive guide for MCP server configuration issues
- [Claude Code MCP Documentation](https://code.claude.com/docs/en/mcp)
- [Claude Code Statusline Documentation](https://code.claude.com/docs/en/statusline#status-line-configuration)
- [GitHub MCP Server](https://github.com/github/github-mcp-server)
- [ANSI Color Codes Reference](https://en.wikipedia.org/wiki/ANSI_escape_code#8-bit)