# GitHub MCP Security - Secure Token Management

**Status**: ?? **ACTION REQUIRED** - Exposed tokens detected  
**Solution**: One automated script fixes everything

---

## ? Quick Fix (5 Minutes)

### The Problem

Your GitHub token `gho_7WMPsiVW5Hv2w...` is **exposed in plaintext** in:
```
~/.cursor/mcp.json
~/Library/Application Support/Code/User/mcp.json
```

### The Solution

**Run this:**

```bash
./secure_mcp_config_update.sh
```

**Then:**
1. Revoke old token: https://github.com/settings/tokens
2. Restart: `killall Cursor && killall "Visual Studio Code"`
3. Verify: `~/bin/cursor-mcp-health-check.sh`

---

## ?? Documentation

| File | Purpose |
|------|---------|
| **[READY_TO_RUN.md](./READY_TO_RUN.md)** | ?? **START HERE** - Complete step-by-step guide |
| **[secure_token_rotation_runbook.md](./secure_token_rotation_runbook.md)** | Comprehensive reference documentation |

---

## ?? What the Script Does

```bash
./secure_mcp_config_update.sh
```

? Updates **both** Cursor and VS Code configs  
? Replaces hardcoded tokens with `$(gh auth token)`  
? Preserves Glean MCP (VS Code)  
? Creates timestamped backups  
? Sets secure permissions (600)  
? Validates security  
? Tests connectivity  

---

## ?? Before vs After

**Before** ?
```json
{
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "gho_7WMP..." ?
  }
}
```
Hardcoded token in 2 config files

**After** ?
```json
{
  "command": "sh",
  "args": ["-c", "GITHUB_PERSONAL_ACCESS_TOKEN=$(gh auth token) docker run ..."]
}
```
Token retrieved dynamically from keychain

---

## ?? Troubleshooting

**Script says "gh not authenticated"**
```bash
gh auth login
```

**Script says "Docker not running"**
```bash
open -a Docker
```

**Check current status**
```bash
~/bin/cursor-mcp-health-check.sh
```

---

## ?? Ready?

Read **[READY_TO_RUN.md](./READY_TO_RUN.md)** for detailed instructions, then:

```bash
./secure_mcp_config_update.sh
```

---

**One script. One secure method. That's it.** ??
