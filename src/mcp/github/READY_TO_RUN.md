# ?? Ready to Run: Dual-Config Security Fix

**Created**: 2025-10-30  
**Status**: ? All scripts updated and ready

---

## ?? Executive Summary

Your GitHub token `gho_7WMPsiVW5Hv2w...` is exposed in **TWO** locations:
1. `~/.cursor/mcp.json` (Cursor)
2. `~/Library/Application Support/Code/User/mcp.json` (VS Code)

**Good news**: One script fixes both files automatically. ??

---

## ? Quick Start (5 minutes)

```bash
# Navigate to scripts directory
cd ~/src/sandbox/dev-rerickso/src/mcp/github

# Run the fix (handles BOTH Cursor and VS Code)
./secure_mcp_config_update.sh
```

The script will:
1. ? Find and backup both config files
2. ? Replace hardcoded GitHub token with secure method
3. ? Preserve your Glean MCP config (VS Code only)
4. ? Set secure file permissions (600)
5. ? Verify no tokens remain in configs

---

## ?? What's Been Updated

### Scripts Updated

| Script | Location | What Changed |
|--------|----------|--------------|
| **Fix Script** | `src/mcp/github/secure_mcp_config_update.sh` | Now handles both Cursor & VS Code configs |
| **Health Check** | `~/bin/cursor-mcp-health-check.sh` | Scans both config files for issues |

### Documentation Updated

| Document | What Changed |
|----------|--------------|
| **QUICK_START.md** | Added dual-config instructions |
| **README.md** | Updated security warnings for both files |
| **UPDATE_SUMMARY.md** | Complete changelog (new) |
| **READY_TO_RUN.md** | This file - your execution guide (new) |

---

## ?? Files Affected

### Current State (BEFORE running script) ?

**Cursor Config** (`~/.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "github": {
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "gho_7WMPsiVW5Hv2w..." ?
      }
    }
  }
}
```

**VS Code Config** (`~/Library/Application Support/Code/User/mcp.json`):
```json
{
  "servers": {
    "glean-mcp": { ... },
    "github": {
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "gho_7WMPsiVW5Hv2w..." ?
      }
    }
  }
}
```

### After Running Script ?

**Both Configs** (secure method):
```json
{
  "command": "sh",
  "args": ["-c", "GITHUB_PERSONAL_ACCESS_TOKEN=$(gh auth token) docker run ..."]
}
```

**Key**: Token retrieved dynamically from GitHub CLI keychain, never stored in plaintext.

---

## ?? Step-by-Step Execution

### Step 1: Run the Fix Script

```bash
cd ~/src/sandbox/dev-rerickso/src/mcp/github
./secure_mcp_config_update.sh
```

**Expected Output**:
```
??????????????????????????????????????????????????????????
?  Secure MCP Configuration Update                       ?
?  Cursor + VS Code: Rotating to secure token method    ?
??????????????????????????????????????????????????????????

[INFO] Checking prerequisites...
[SUCCESS] GitHub CLI found
[SUCCESS] GitHub CLI authenticated
[SUCCESS] Docker is running
[SUCCESS] jq found
[INFO] Scanning for MCP configuration files...
[SUCCESS] Found Cursor config: /Users/rerickso/.cursor/mcp.json
[SUCCESS] Found VS Code config: /Users/rerickso/Library/Application Support/Code/User/mcp.json

[WARNING] Scanning for exposed tokens...
[ERROR] SECURITY ISSUE: GitHub token detected in .cursor/mcp.json
  Found token: gho_7WMPsiVW5H...
[ERROR] SECURITY ISSUE: GitHub token detected in Code/User/mcp.json
  Found token: gho_7WMPsiVW5H...
[WARNING] Glean API token detected in Code/User/mcp.json
  (Glean token will be preserved in config)

Update configurations to use GitHub CLI token? (yes/no): yes

[INFO] Creating backups...
[SUCCESS] Backup: ~/.cursor/mcp.json.backup.20251030_143000
[SUCCESS] Backup: ~/Library/Application Support/Code/User/mcp.json.backup.20251030_143000

[INFO] Testing GitHub CLI token access...
[SUCCESS] GitHub CLI token accessible

[INFO] Testing GitHub API access...
[SUCCESS] GitHub API access confirmed (user: {gh-username})

[INFO] Updating Cursor configuration...
[SUCCESS] Cursor configuration updated

[INFO] Updating VS Code configuration...
[INFO] Preserving Glean MCP configuration...
[SUCCESS] Preserved Glean MCP configuration
[SUCCESS] VS Code configuration updated

[INFO] Setting secure file permissions...
[SUCCESS] mcp.json: permissions set to 600
[SUCCESS] mcp.json: permissions set to 600

[INFO] Verifying secure configurations...
[SUCCESS] mcp.json: No hardcoded GitHub tokens
[SUCCESS] mcp.json: No hardcoded GitHub tokens

[INFO] Testing new MCP configuration...
[SUCCESS] MCP server test successful

??????????????????????????????????????????????????????????
?  Configuration Updated Successfully!                   ?
??????????????????????????????????????????????????????????

[SUCCESS] Secure configurations applied
[SUCCESS] Backups saved with timestamp: 20251030_143000
  ? /Users/rerickso/.cursor/mcp.json.backup.20251030_143000
  ? /Users/rerickso/Library/Application Support/Code/User/mcp.json.backup.20251030_143000

IMPORTANT NEXT STEPS:

1. Revoke the old exposed token:
   ? Visit: https://github.com/settings/tokens
   ? Find token starting with: gho_7WMPsiVW5Hv2w...
   ? Click 'Delete' or 'Revoke'

2. Restart applications to apply changes:
   Cursor:
   ? Quit completely (Cmd+Q or killall Cursor)
   ? Reopen Cursor
   
   VS Code:
   ? Quit completely (Cmd+Q or killall 'Visual Studio Code')
   ? Reopen VS Code

3. Verify MCP functionality:
   In Cursor:
   ? Open Settings ? MCP Servers
   ? Check 'github' shows as 'Connected'
   ? Test: @github list my repositories
   
   In VS Code:
   ? Open Command Palette (Cmd+Shift+P)
   ? Type 'MCP' and check server status

4. Run health check (after restarting apps):
   ? ~/bin/cursor-mcp-health-check.sh

[WARNING] Your old token is still active until you revoke it!
[WARNING] Complete step 1 immediately to secure your account.

Open GitHub tokens page now? (yes/no): 
```

### Step 2: Revoke Old Token

```bash
# Open GitHub tokens page
open https://github.com/settings/tokens
```

**Actions**:
1. Find token starting with `gho_7WMPsiVW5Hv2w...`
2. Click on the token name
3. Scroll to bottom
4. Click "Delete" or "Revoke"
5. Confirm deletion

### Step 3: Restart Both Applications

```bash
# Quit Cursor
killall Cursor

# Quit VS Code
killall "Visual Studio Code"

# Wait 5 seconds
sleep 5

# Reopen both (manually or via command)
open -a Cursor
open -a "Visual Studio Code"
```

### Step 4: Verify in Cursor

1. Open Cursor
2. Go to **Settings** (Cmd+,)
3. Navigate to **MCP Servers**
4. Verify `github` shows status: **Connected** ?
5. Open Cursor Chat
6. Type: `@github list my repositories`
7. Confirm it returns your repositories

### Step 5: Verify in VS Code

1. Open VS Code
2. Open **Command Palette** (Cmd+Shift+P)
3. Type: `MCP`
4. Check MCP server status
5. Verify both `github` and `glean-mcp` are connected

### Step 6: Run Health Check

```bash
~/bin/cursor-mcp-health-check.sh
```

**Expected Result**: All checks pass ?

```
???????????????????????????????????????????????????????
      Cursor MCP Health Check
???????????????????????????????????????????????????????
Date: Thu Oct 30 14:30:00 PDT 2025

1. GitHub CLI Authentication
   ? GitHub CLI installed
   ? Authenticated
   ? User: {gh-username}
   ? Token accessible

2. Docker Status
   ? Docker installed
   ? Docker daemon running
   ? MCP image present

3. GitHub API Access
   ? API accessible
   ? Rate limit: 4999/5000 requests remaining

4. GitHub MCP Server
   ? MCP server functional
   ? Version: GitHub MCP Server Version: v0.17.1

5. Configuration Security
   ? Cursor config exists
   ? Cursor permissions: 600 (secure)
   ? Cursor: No hardcoded tokens
   ? Cursor: Using secure GitHub CLI method
   ? VS Code config exists
   ? VS Code permissions: 600 (secure)
   ? VS Code: No hardcoded GitHub tokens
   ? VS Code: Using secure GitHub CLI method
   ? VS Code: Contains Glean API token (acceptable if intended)

???????????????????????????????????????????????????????
? All Checks Passed (18 passed, 0 failed)

Your Cursor MCP is configured correctly!

Next steps:
  ? Open Cursor and verify MCP in Settings ? MCP Servers
  ? Test in chat: @github list my repositories
```

---

## ? Verification Checklist

After completing all steps:

- [ ] Script ran successfully without errors
- [ ] Two backup files created (check timestamps match)
- [ ] Old GitHub token revoked at https://github.com/settings/tokens
- [ ] Cursor restarted
- [ ] VS Code restarted
- [ ] Cursor MCP shows "Connected" in settings
- [ ] VS Code GitHub MCP connected (Command Palette check)
- [ ] VS Code Glean MCP still working (if you use it)
- [ ] Tested `@github` in Cursor chat - works ?
- [ ] Health check passes all tests ?
- [ ] No hardcoded tokens in Cursor: `grep -E "gho_|ghp_" ~/.cursor/mcp.json` returns nothing
- [ ] No hardcoded tokens in VS Code: `grep -E "gho_|ghp_" ~/Library/Application\ Support/Code/User/mcp.json` returns nothing

---

## ?? Security Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Plaintext Tokens** | 2 locations | 0 locations | -100% ? |
| **Manual Rotation** | Edit 2 files | `gh auth refresh` | Automated ? |
| **Backup Exposure** | High risk | No tokens in backups | Eliminated ? |
| **Version Control Risk** | If committed | Safe | Eliminated ? |
| **Token Storage** | Config files | macOS Keychain | Secure ? |

---

## ?? Troubleshooting

### Issue: Script says "gh not authenticated"

**Solution**:
```bash
gh auth login
# Follow browser authentication flow
```

### Issue: Script says "Docker not running"

**Solution**:
```bash
open -a Docker
# Wait for Docker Desktop to start
```

### Issue: Script says "jq not installed"

**Solution**:
```bash
brew install jq
```

### Issue: MCP not working after restart

**Cursor**:
```bash
# Check Cursor logs
tail -f ~/Library/Logs/Cursor/main.log
```

**VS Code**:
```bash
# Check Output panel in VS Code
# View ? Output ? Select "MCP" from dropdown
```

### Issue: Glean MCP stopped working in VS Code

**Check**:
```bash
# Verify Glean config is still present
jq '.servers."glean-mcp"' ~/Library/Application\ Support/Code/User/mcp.json
```

If missing, restore from backup:
```bash
# Find your backup
ls -la ~/Library/Application\ Support/Code/User/mcp.json.backup.*

# Restore (using latest backup timestamp)
cp ~/Library/Application\ Support/Code/User/mcp.json.backup.YYYYMMDD_HHMMSS \
   ~/Library/Application\ Support/Code/User/mcp.json

# Re-run the fix script
cd ~/src/sandbox/dev-rerickso/src/mcp/github
./secure_mcp_config_update.sh
```

---

## ?? Additional Resources

| Document | Purpose |
|----------|---------|
| [QUICK_START.md](./QUICK_START.md) | Fast 5-minute guide |
| [README.md](./README.md) | Main documentation hub |
| [UPDATE_SUMMARY.md](./UPDATE_SUMMARY.md) | Complete changelog |
| [secure_token_rotation_runbook.md](./secure_token_rotation_runbook.md) | Comprehensive security guide |

---

## ?? You're Ready!

Everything is prepared. Just run:

```bash
cd ~/src/sandbox/dev-rerickso/src/mcp/github
./secure_mcp_config_update.sh
```

Then follow the on-screen instructions. The script handles everything automatically! ??

---

**Questions?** Check [UPDATE_SUMMARY.md](./UPDATE_SUMMARY.md) for detailed Q&A.
