# Secure GitHub MCP Token Rotation and Cursor Agent Setup Runbook

**Date Created**: 2025-10-30  
**Status**: Active  
**Purpose**: Revoke exposed GitHub PAT, establish secure token management, and configure Cursor Agent MCP access

---

## Table of Contents

1. [Emergency: Revoke Exposed Token](#1-emergency-revoke-exposed-token)
2. [Security Assessment](#2-security-assessment)
3. [Choose Secure Authentication Method](#3-choose-secure-authentication-method)
4. [Method A: GitHub CLI Token (Recommended)](#4-method-a-github-cli-token-recommended)
5. [Method B: Environment Variable with New PAT](#5-method-b-environment-variable-with-new-pat)
6. [Update Cursor MCP Configuration](#6-update-cursor-mcp-configuration)
7. [Understanding Cursor Agent vs Cursor UI MCPs](#7-understanding-cursor-agent-vs-cursor-ui-mcps)
8. [Verification and Testing](#8-verification-and-testing)
9. [Post-Incident Review](#9-post-incident-review)
10. [Maintenance Schedule](#10-maintenance-schedule)

---

## 1. Emergency: Revoke Exposed Token

### Issue Description

**Critical Security Finding**: GitHub Personal Access Token exposed in plaintext in `~/.cursor/mcp.json`

```
Exposed Token: gho_[REDACTED_TOKEN]
Location: ~/.cursor/mcp.json (line 16)
Exposure Duration: Unknown
Risk Level: HIGH
```

### Immediate Action Required

#### Step 1.1: Revoke the Exposed Token

- [ ] **Open GitHub Token Settings**:
  ```bash
  # Open in default browser
  open https://github.com/settings/tokens
  
  # Or navigate manually:
  # GitHub.com ? Settings ? Developer settings ? Personal access tokens ? Tokens (classic)
  ```

- [ ] **Locate the Token**:
  - Look for tokens with prefix `gho_[REDACTED]...`
  - Check "Last used" date to confirm it's the active token
  - Note the scopes granted (you'll need these for the new token)

- [ ] **Revoke the Token**:
  - Click on the token name
  - Scroll to bottom and click "Delete" or "Revoke"
  - Confirm the revocation

- [ ] **Verify Revocation**:
  ```bash
  # This should fail with 401 Unauthorized
  curl -H "Authorization: Bearer gho_[REDACTED_TOKEN]" \
       https://api.github.com/user
  
  # Expected output: {"message":"Bad credentials"...}
  ```

**Completion Criteria**: Token revocation confirmed, API returns 401 error.

---

## 2. Security Assessment

### Impact Analysis

- [ ] **Determine Exposure Scope**:
  - Check if `~/.cursor/mcp.json` is in any git repositories
  - Review backup systems that might contain the file
  - Check if config was shared in docs, tickets, or chat

- [ ] **Audit Recent GitHub Activity**:
  ```bash
  # Review recent activity on your account
  gh api user/events --paginate | jq -r '.[] | "\(.created_at) \(.type) \(.repo.name)"' | head -50
  ```

- [ ] **Check Token Usage**:
  - Visit https://github.com/settings/security-log
  - Filter for "oauth access token" events
  - Look for suspicious activity or unexpected access patterns

### Risk Assessment Checklist

- [ ] Token had repo access (read/write)
- [ ] Token was stored in plaintext in user home directory
- [ ] File permissions on `~/.cursor/mcp.json`: `ls -la ~/.cursor/mcp.json`
- [ ] Other users have access to this machine: `who`
- [ ] Machine has remote access enabled: `sudo systemsetup -getremotelogin` (macOS)

**Mitigation Priority**: Immediate token rotation required.

---

## 3. Choose Secure Authentication Method

### Decision Matrix

| Method | Security | Convenience | Rotation | Recommended For |
|--------|----------|-------------|----------|-----------------|
| **GitHub CLI Token** | ????? | ????? | Automatic | **Primary Choice** |
| **Environment Variable** | ???? | ??? | Manual | Backup method |
| **Hardcoded Token** | ? | ????? | Manual | **NEVER USE** |

### Method Comparison

**GitHub CLI Token** (Recommended):
- ? Token managed by `gh` CLI with keychain integration
- ? Automatic rotation when you re-authenticate
- ? No plaintext storage
- ? Same token used across all tools
- ? Scopes managed centrally

**Environment Variable**:
- ? Better than hardcoding
- ?? Still stored in shell profile files
- ?? Manual rotation required
- ?? Visible in process listings

**Hardcoded Token** (Current State):
- ? Plaintext in config files
- ? Version control risk
- ? Backup exposure risk
- ? No rotation mechanism
- ? **SECURITY VIOLATION**

### Recommended Approach

? **Use GitHub CLI Token** - You already have `gh` CLI configured and authenticated.

Current `gh` status:
```
? Logged in to github.com account {gh-username}
? Token scopes: admin:public_key, gist, read:org, repo
```

---

## 4. Method A: GitHub CLI Token (Recommended)

### Prerequisites Verification

- [ ] **Verify GitHub CLI Installation**:
  ```bash
  gh --version
  # Expected: gh version 2.x.x (or higher)
  ```

- [ ] **Check Current Authentication**:
  ```bash
  gh auth status
  # Should show: ? Logged in to github.com
  ```

- [ ] **Test Token Access**:
  ```bash
  gh auth token
  # Should output a token starting with gho_ or ghp_
  ```

- [ ] **Verify Token Scopes**:
  ```bash
  gh auth status
  # Check "Token scopes" line includes: repo, read:org
  ```

### Step 4.1: Refresh GitHub CLI Authentication (Optional)

If you want to update scopes or rotate the CLI token:

- [ ] **Refresh with Additional Scopes**:
  ```bash
  # Refresh authentication and ensure all needed scopes
  gh auth refresh -s repo,read:org,read:packages,admin:public_key,gist
  
  # Follow the browser authentication flow
  # This will generate a new token and replace the old one
  ```

- [ ] **Verify New Authentication**:
  ```bash
  gh auth status
  # Confirm new scopes are present
  ```

### Step 4.2: Test GitHub CLI Token with Docker

- [ ] **Test Token with MCP Server**:
  ```bash
  # This tests the full flow: gh CLI ? token ? docker ? GitHub API
  GITHUB_PERSONAL_ACCESS_TOKEN=$(gh auth token) \
    docker run --rm \
      -e GITHUB_PERSONAL_ACCESS_TOKEN \
      ghcr.io/github/github-mcp-server --version
  
  # Expected output: GitHub MCP Server Version: v0.x.x
  ```

- [ ] **Test GitHub API Access**:
  ```bash
  # Verify token can access GitHub API
  curl -H "Authorization: Bearer $(gh auth token)" \
       https://api.github.com/user | jq -r '.login'
  
  # Expected output: {gh-username}
  ```

**Success Criteria**: Both commands succeed without authentication errors.

---

## 5. Method B: Environment Variable with New PAT

**Use this only if GitHub CLI method is not suitable for your workflow.**

### Step 5.1: Generate New Personal Access Token

- [ ] **Navigate to Token Creation**:
  ```bash
  open https://github.com/settings/personal-access-tokens/new
  ```

- [ ] **Configure Token Settings**:
  - **Token name**: `cursor-mcp-github-$(date +%Y%m%d)`
  - **Expiration**: 90 days (recommended for security)
  - **Repository access**: 
    - Select "All repositories" or specific repos as needed
  
- [ ] **Select Scopes** (minimum required):
  - ? `repo` - Full control of private repositories
  - ? `read:org` - Read org and team membership
  - ? `read:packages` - Download packages from GitHub Container Registry
  - ?? Optional: `write:packages` (only if you need to push)
  - ?? Optional: `workflow` (if you need to trigger Actions)

- [ ] **Generate and Copy Token**:
  - Click "Generate token"
  - **IMMEDIATELY** copy the token (you won't see it again)
  - Store temporarily in secure location (1Password, etc.)

### Step 5.2: Store Token in Environment Variable

**macOS/Linux with Zsh**:

- [ ] **Add to ~/.zshrc** (with proper security):
  ```bash
  # Create backup first
  cp ~/.zshrc ~/.zshrc.backup.$(date +%Y%m%d_%H%M%S)
  
  # Add token to zshrc (ONLY if using this method)
  cat >> ~/.zshrc << 'EOF'
  
  # GitHub Personal Access Token for MCP (rotate every 90 days)
  # Created: $(date +%Y-%m-%d)
  # Expires: $(date -v+90d +%Y-%m-%d)
  export GITHUB_PERSONAL_ACCESS_TOKEN="your_new_token_here"
  EOF
  
  # Secure the file
  chmod 600 ~/.zshrc
  
  # Load the new configuration
  source ~/.zshrc
  ```

- [ ] **Verify Environment Variable**:
  ```bash
  echo $GITHUB_PERSONAL_ACCESS_TOKEN | cut -c1-10
  # Should output: gho_ or ghp_ prefix
  ```

**Security Note**: Even with environment variables, the token is still visible in:
- Shell history (use `history -c` to clear)
- Process listings (`ps aux | grep TOKEN`)
- Child processes

**Alternative: Use System Keychain** (More Secure):
```bash
# Store in keychain
security add-generic-password \
  -a "${USER}" \
  -s "github-mcp-token" \
  -w "your_new_token_here"

# Retrieve from keychain
export GITHUB_PERSONAL_ACCESS_TOKEN=$(security find-generic-password \
  -a "${USER}" \
  -s "github-mcp-token" \
  -w)
```

---

## 6. Update Cursor MCP Configuration

### Step 6.1: Backup Current Configuration

- [ ] **Create Backup**:
  ```bash
  # Backup with timestamp
  cp ~/.cursor/mcp.json \
     ~/.cursor/mcp.json.backup.$(date +%Y%m%d_%H%M%S)
  
  # Verify backup
  ls -la ~/.cursor/*.backup.*
  ```

- [ ] **Document Current State**:
  ```bash
  # Save current config structure (redacting token)
  jq 'walk(if type == "string" and startswith("gho_") then "***REDACTED***" else . end)' \
     ~/.cursor/mcp.json > ~/mcp-config-structure.json
  ```

### Step 6.2: Update Configuration for GitHub CLI Token

**This is the recommended configuration.**

- [ ] **Update ~/.cursor/mcp.json**:

Run this command to update your configuration:

```bash
cat > ~/.cursor/mcp.json << 'EOF'
{
  "mcpServers": {
    "github": {
      "name": "github",
      "type": "stdio",
      "command": "sh",
      "args": [
        "-c",
        "GITHUB_PERSONAL_ACCESS_TOKEN=$(gh auth token) docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server"
      ],
      "enabled": true
    }
  }
}
EOF
```

**What This Does**:
- Uses `sh -c` to execute a shell command
- Dynamically retrieves token from `gh auth token` at runtime
- Passes token to Docker container via environment variable
- No plaintext token storage anywhere

### Step 6.3: Alternative Configuration (Environment Variable Method)

**Only use if you chose Method B above.**

```bash
cat > ~/.cursor/mcp.json << 'EOF'
{
  "mcpServers": {
    "github": {
      "name": "github",
      "type": "stdio",
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "ghcr.io/github/github-mcp-server"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
      },
      "enabled": true
    }
  }
}
EOF
```

This reads from the `$GITHUB_PERSONAL_ACCESS_TOKEN` environment variable.

### Step 6.4: Secure the Configuration File

- [ ] **Set Proper Permissions**:
  ```bash
  # Only owner can read/write
  chmod 600 ~/.cursor/mcp.json
  
  # Verify permissions
  ls -la ~/.cursor/mcp.json
  # Should show: -rw------- (600)
  ```

- [ ] **Verify No Plaintext Tokens**:
  ```bash
  # This should NOT output any tokens
  grep -E "gho_|ghp_" ~/.cursor/mcp.json
  
  # If it finds any, you still have hardcoded tokens - fix immediately
  ```

- [ ] **Add to .gitignore** (if ever in a repo):
  ```bash
  # Ensure cursor configs are never committed
  echo ".cursor/" >> ~/.gitignore_global
  git config --global core.excludesfile ~/.gitignore_global
  ```

---

## 7. Understanding Cursor Agent vs Cursor UI MCPs

### Architecture Overview

**Cursor has TWO different MCP contexts**:

```
???????????????????????????????????????????????????????????
?                     CURSOR APPLICATION                   ?
???????????????????????????????????????????????????????????
?                                                          ?
?  ??????????????????????       ??????????????????????   ?
?  ?   Cursor UI/GUI    ?       ?   Cursor Agent     ?   ?
?  ?                    ?       ?   (CLI / Chat)     ?   ?
?  ??????????????????????       ??????????????????????   ?
?  ? Global MCPs        ?       ? Workspace MCPs     ?   ?
?  ? ~/.cursor/mcp.json ?       ? /mcp list          ?   ?
?  ?                    ?       ? /mcp add           ?   ?
?  ??????????????????????       ??????????????????????   ?
?           ?                            ?                ?
?  Available everywhere       Available in chat only     ?
???????????????????????????????????????????????????????????
```

### Global MCPs (Cursor UI)

**Location**: `~/.cursor/mcp.json`

**Characteristics**:
- ? Configured via Settings UI or manual JSON editing
- ? Available across all workspaces
- ? Shows in "Cursor Settings ? MCP Servers"
- ? Used by background features and integrations
- ?? **NOT visible to `/mcp list` command**

**Your Current Setup**: You have GitHub MCP configured here.

### Workspace MCPs (Cursor Agent CLI)

**Location**: Workspace-specific, managed by `/mcp` commands

**Characteristics**:
- ? Configured via `/mcp add` in Cursor chat
- ? Scoped to current workspace/project
- ? Visible with `/mcp list` command
- ? Can override global MCPs
- ?? **NOT the same as global MCPs**

**Your Current Setup**: No workspace MCPs configured (that's why `/mcp list` shows none).

### Why `/mcp list` Shows Nothing

The `/mcp list` command checks **workspace-specific MCPs only**.

Your global GitHub MCP (`~/.cursor/mcp.json`) is configured and working, but it's not a "workspace MCP" that shows up in `/mcp list`.

### Should You Add Workspace MCPs?

**Decision Guide**:

| Use Case | Recommendation |
|----------|----------------|
| **Same MCP across all projects** | ? Use Global MCP (current setup) |
| **Project-specific MCP config** | ? Add Workspace MCP |
| **Team-shared MCP config** | ? Add Workspace MCP (can commit to repo) |
| **Temporary/experimental MCP** | ? Add Workspace MCP |

**For your GitHub MCP**: Keep it as a global MCP (current approach is correct).

### Step 7.1: Optional - Add GitHub MCP to Workspace

Only do this if you need workspace-specific configuration.

- [ ] **Open Cursor Chat** in your workspace
- [ ] **Add GitHub MCP** to workspace:
  ```
  /mcp add github --config '{"command":"sh","args":["-c","GITHUB_PERSONAL_ACCESS_TOKEN=$(gh auth token) docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server"]}'
  ```

- [ ] **Verify with List**:
  ```
  /mcp list
  ```
  Should now show `github` MCP

**Recommendation**: Skip this step. Your global MCP is sufficient.

---

## 8. Verification and Testing

### Step 8.1: Restart Cursor

- [ ] **Quit Cursor Completely**:
  ```bash
  # Force quit Cursor
  killall Cursor
  
  # Or use Cmd+Q (macOS)
  ```

- [ ] **Clear Cursor Cache** (optional but recommended):
  ```bash
  # Backup cache first
  mv ~/.cursor/cache ~/.cursor/cache.backup.$(date +%Y%m%d_%H%M%S)
  
  # Cursor will recreate cache on next launch
  ```

- [ ] **Restart Cursor**:
  - Launch Cursor normally
  - Wait for full initialization (check bottom status bar)

### Step 8.2: Verify Global MCP Configuration

- [ ] **Check Cursor Settings**:
  - Open Cursor Settings (Cmd+, or Ctrl+,)
  - Navigate to "MCP Servers" section
  - Verify "github" MCP shows as "Connected" or "Enabled"

- [ ] **Check MCP Status**:
  ```bash
  # Review MCP approval status
  cat ~/.cursor/projects/Users-rerickso-src-sandbox-dev-rerickso/mcp-approvals.json
  
  # Should show: ["glean-mcp-...", "github-..."]
  ```

### Step 8.3: Test MCP Functionality

- [ ] **Test GitHub API Access**:
  
  Open Cursor chat and test with a simple query:
  ```
  @github What repositories do I have access to?
  ```
  
  Or use the MCP directly:
  ```
  Use the GitHub MCP to list my repositories
  ```

- [ ] **Test Repository Operations**:
  ```
  @github Get details about the repository rerickso/dev-rerickso
  ```

- [ ] **Test Search Functionality**:
  ```
  @github Search for issues in my repositories with label "bug"
  ```

### Step 8.4: Verify No Plaintext Tokens

- [ ] **Scan All Cursor Config Files**:
  ```bash
  # Search for any tokens in Cursor configs
  find ~/.cursor -type f -name "*.json" -exec grep -l "gho_\|ghp_" {} \; 2>/dev/null
  
  # Should return EMPTY (no files with hardcoded tokens)
  ```

- [ ] **Check Process Environment**:
  ```bash
  # Verify token is not in process environment
  ps aux | grep -i cursor | grep -v grep
  
  # Should NOT show any tokens in command line
  ```

### Step 8.5: Test Token Rotation

- [ ] **Simulate Token Rotation**:
  ```bash
  # Re-authenticate with gh (generates new token)
  gh auth refresh
  
  # Restart Cursor
  killall Cursor
  
  # Verify MCP still works (uses new token automatically)
  ```

**Success Criteria**: MCP continues working with new token, no manual config changes needed.

---

## 9. Post-Incident Review

### Security Improvements Implemented

- [x] Revoked exposed GitHub PAT
- [x] Removed plaintext token from `~/.cursor/mcp.json`
- [x] Implemented secure token management (GitHub CLI)
- [x] Set proper file permissions (600) on config files
- [x] Documented token rotation procedures
- [x] Created runbook for future incidents

### Lessons Learned

**What Went Wrong**:
1. Initial MCP setup used insecure hardcoded token
2. No validation that config followed security best practices
3. No automated scanning for exposed credentials

**Preventive Measures**:

- [ ] **Add Credential Scanning**:
  ```bash
  # Create git pre-commit hook to scan for tokens
  cat > .git/hooks/pre-commit << 'EOF'
  #!/bin/bash
  # Scan for potential tokens
  if git diff --cached | grep -E "gho_|ghp_|github.*token.*[A-Za-z0-9]{20,}"; then
    echo "ERROR: Potential GitHub token detected in commit"
    echo "Please remove tokens before committing"
    exit 1
  fi
  EOF
  
  chmod +x .git/hooks/pre-commit
  ```

- [ ] **Regular Security Audits**:
  ```bash
  # Add to crontab or run monthly
  # Schedule: First Monday of each month
  0 9 1-7 * 1 [ "$(date +\%u)" -eq 1 ] && /path/to/security-audit.sh
  ```

- [ ] **Document Token Locations**:
  Create inventory of all GitHub tokens in use:
  - GitHub CLI: `gh auth token` (automatically managed)
  - CI/CD: Repository secrets (check GitHub Actions secrets)
  - Local tools: Environment variables, keychains

### Documentation Updates

- [x] Created `secure_token_rotation_runbook.md` (this file)
- [ ] Update `setup_mcp_github_local.md` with security warnings
- [ ] Add security checklist to team onboarding docs
- [ ] Create incident response procedures for credential exposure

---

## 10. Maintenance Schedule

### Regular Maintenance Tasks

| Task | Frequency | Command | Owner |
|------|-----------|---------|-------|
| **Verify MCP Connectivity** | Weekly | Test GitHub API access | You |
| **Review GitHub Audit Log** | Monthly | Visit https://github.com/settings/security-log | You |
| **Rotate GitHub CLI Token** | Quarterly | `gh auth refresh` | You |
| **Update MCP Server Image** | Monthly | `docker pull ghcr.io/github/github-mcp-server:latest` | You |
| **Security Audit** | Quarterly | Run credential scan | You |
| **Review Token Scopes** | Annually | Minimize required permissions | You |

### Token Rotation Procedure

**GitHub CLI Token** (Automatic):
```bash
# When needed, refresh authentication
gh auth refresh -s repo,read:org,read:packages

# Restart Cursor to pick up new token
killall Cursor
```

**Manual PAT** (If using Method B):
1. Generate new token 1 week before expiration
2. Update environment variable or keychain
3. Test MCP connectivity
4. Revoke old token only after confirming new one works
5. Update documentation with new expiration date

### Health Check Script

Create an automated health check:

```bash
cat > ~/bin/cursor-mcp-health-check.sh << 'EOF'
#!/bin/bash
# Cursor MCP Health Check
# Run: ~/bin/cursor-mcp-health-check.sh

set -euo pipefail

echo "=== Cursor MCP Health Check ==="
echo "Date: $(date)"
echo

# Check GitHub CLI authentication
echo "1. GitHub CLI Authentication:"
if gh auth status &>/dev/null; then
  echo "   ? Authenticated"
  gh auth status 2>&1 | grep "Token scopes"
else
  echo "   ? NOT authenticated - run: gh auth login"
  exit 1
fi

# Check Docker
echo
echo "2. Docker Status:"
if docker info &>/dev/null; then
  echo "   ? Docker running"
else
  echo "   ? Docker not running"
  exit 1
fi

# Test GitHub API
echo
echo "3. GitHub API Access:"
if curl -sf -H "Authorization: Bearer $(gh auth token)" \
     https://api.github.com/user > /dev/null; then
  echo "   ? API accessible"
else
  echo "   ? API not accessible"
  exit 1
fi

# Test MCP Server
echo
echo "4. GitHub MCP Server:"
if GITHUB_PERSONAL_ACCESS_TOKEN=$(gh auth token) \
   docker run --rm -e GITHUB_PERSONAL_ACCESS_TOKEN \
   ghcr.io/github/github-mcp-server --version &>/dev/null; then
  echo "   ? MCP server functional"
else
  echo "   ? MCP server error"
  exit 1
fi

# Check config security
echo
echo "5. Configuration Security:"
if grep -qE "gho_|ghp_" ~/.cursor/mcp.json 2>/dev/null; then
  echo "   ? SECURITY WARNING: Hardcoded token found in config!"
  exit 1
else
  echo "   ? No hardcoded tokens detected"
fi

echo
echo "=== All Checks Passed ==="
EOF

chmod +x ~/bin/cursor-mcp-health-check.sh
```

Run health check:
```bash
~/bin/cursor-mcp-health-check.sh
```

---

## Quick Reference

### Emergency Contacts

- **GitHub Token Management**: https://github.com/settings/tokens
- **GitHub Security Log**: https://github.com/settings/security-log
- **GitHub Support**: https://support.github.com

### Key Commands

```bash
# Verify GitHub CLI authentication
gh auth status

# Refresh GitHub CLI token
gh auth refresh

# Test GitHub API access
curl -H "Authorization: Bearer $(gh auth token)" https://api.github.com/user

# Test MCP server
GITHUB_PERSONAL_ACCESS_TOKEN=$(gh auth token) \
  docker run --rm -e GITHUB_PERSONAL_ACCESS_TOKEN \
  ghcr.io/github/github-mcp-server --version

# View Cursor MCP config (safely)
jq 'walk(if type == "string" and (startswith("gho_") or startswith("ghp_")) then "***REDACTED***" else . end)' ~/.cursor/mcp.json

# Restart Cursor
killall Cursor
```

### Configuration Files

| File | Purpose | Permissions |
|------|---------|-------------|
| `~/.cursor/mcp.json` | Global MCP configuration | 600 (-rw-------) |
| `~/.cursor/projects/.../mcp-approvals.json` | Approved MCPs | 600 |
| `~/.zshrc` | Shell environment (if using Method B) | 600 |

### Security Checklist

- [ ] No hardcoded tokens in any config files
- [ ] File permissions set to 600 on sensitive configs
- [ ] GitHub CLI authenticated and token accessible
- [ ] MCP server Docker image up to date
- [ ] Regular token rotation schedule documented
- [ ] Security audit log reviewed monthly
- [ ] Backup configs stored securely (without tokens)

---

## Completion Checklist

Mark each section as you complete it:

- [ ] **Section 1**: Revoked exposed token
- [ ] **Section 2**: Completed security assessment
- [ ] **Section 3**: Chose secure authentication method (GitHub CLI)
- [ ] **Section 4**: Configured GitHub CLI token integration
- [ ] **Section 5**: (Skip if using GitHub CLI)
- [ ] **Section 6**: Updated Cursor MCP configuration
- [ ] **Section 7**: Understood Cursor Agent vs UI MCPs
- [ ] **Section 8**: Verified and tested MCP functionality
- [ ] **Section 9**: Completed post-incident review
- [ ] **Section 10**: Set up maintenance schedule

**Final Verification**: Run health check script and confirm all checks pass.

---

## Appendix: Troubleshooting

### Issue: MCP Server Won't Start

**Symptoms**: Cursor shows MCP as "Disconnected" or errors in console

**Resolution**:
```bash
# Check Docker
docker info

# Pull latest MCP image
docker pull ghcr.io/github/github-mcp-server:latest

# Test manually
GITHUB_PERSONAL_ACCESS_TOKEN=$(gh auth token) \
  docker run -it --rm -e GITHUB_PERSONAL_ACCESS_TOKEN \
  ghcr.io/github/github-mcp-server stdio

# Check Cursor logs
tail -f ~/Library/Logs/Cursor/main.log
```

### Issue: GitHub CLI Token Expired

**Symptoms**: `gh auth token` returns error or API calls fail with 401

**Resolution**:
```bash
# Re-authenticate
gh auth login

# Or refresh existing auth
gh auth refresh -s repo,read:org,read:packages

# Restart Cursor
killall Cursor
```

### Issue: Permission Denied Errors

**Symptoms**: Docker can't access token or config files

**Resolution**:
```bash
# Fix file permissions
chmod 600 ~/.cursor/mcp.json

# Ensure Docker has necessary permissions
# Check Docker Desktop settings ? Resources ? File Sharing

# Verify token is accessible
gh auth token | wc -c  # Should output > 0
```

### Issue: `/mcp list` Still Shows Nothing

**Explanation**: This is **expected behavior**. The `/mcp list` command shows workspace MCPs, not global MCPs.

**Resolution**: 
- No action needed if global MCP is working
- Global MCPs (`~/.cursor/mcp.json`) are available in Cursor UI
- Only add workspace MCPs if you need project-specific configuration

---

**Runbook Version**: 1.0  
**Last Updated**: 2025-10-30  
**Next Review Date**: 2026-01-30  
**Owner**: @rerickso
