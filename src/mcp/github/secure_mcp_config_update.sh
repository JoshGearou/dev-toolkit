#!/bin/bash
# Secure Cursor MCP Configuration Update Script
# Purpose: Safely update ~/.cursor/mcp.json to use GitHub CLI token
# Author: Generated for rerickso
# Date: 2025-10-30

set -euo pipefail

# Configuration file paths
CURSOR_CONFIG="${HOME}/.cursor/mcp.json"
VSCODE_CONFIG="${HOME}/Library/Application Support/Code/User/mcp.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo -e "${BLUE}??????????????????????????????????????????????????????????${NC}"
echo -e "${BLUE}?  Secure Cursor MCP Configuration Update               ?${NC}"
echo -e "${BLUE}?  Rotating exposed GitHub token to secure method       ?${NC}"
echo -e "${BLUE}??????????????????????????????????????????????????????????${NC}"
echo

# Check prerequisites
log_info "Checking prerequisites..."

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    log_error "GitHub CLI (gh) is not installed"
    echo "Install with: brew install gh"
    exit 1
fi
log_success "GitHub CLI found"

# Check if gh is authenticated
if ! gh auth status &> /dev/null; then
    log_error "GitHub CLI is not authenticated"
    echo "Authenticate with: gh auth login"
    exit 1
fi
log_success "GitHub CLI authenticated"

# Check if Docker is running
if ! docker info &> /dev/null; then
    log_error "Docker is not running"
    echo "Please start Docker Desktop"
    exit 1
fi
log_success "Docker is running"

# Check which config files exist
CONFIG_FILES=()
if [ -f "$CURSOR_CONFIG" ]; then
    CONFIG_FILES+=("$CURSOR_CONFIG")
    log_success "Found Cursor config: $CURSOR_CONFIG"
fi
if [ -f "$VSCODE_CONFIG" ]; then
    CONFIG_FILES+=("$VSCODE_CONFIG")
    log_success "Found VS Code config: $VSCODE_CONFIG"
fi

if [ ${#CONFIG_FILES[@]} -eq 0 ]; then
    log_error "No MCP configuration files found"
    exit 1
fi

echo

# Display current configuration (with token redacted)
log_info "Current configuration (tokens redacted):"
jq 'walk(if type == "string" and (startswith("gho_") or startswith("ghp_")) then "***REDACTED***" else . end)' ~/.cursor/mcp.json
echo

# Check for hardcoded tokens
log_warning "Scanning for exposed tokens..."
if grep -qE "gho_|ghp_" ~/.cursor/mcp.json; then
    log_error "SECURITY ISSUE: Hardcoded token detected in config!"
    
    # Extract the token prefix for confirmation (don't show full token)
    TOKEN_PREFIX=$(grep -oE "gho_[A-Za-z0-9]{10}" ~/.cursor/mcp.json | head -1)
    echo
    echo "Found token starting with: ${TOKEN_PREFIX}..."
    echo
    log_warning "This token should be revoked immediately at:"
    echo "https://github.com/settings/tokens"
    echo
else
    log_success "No hardcoded tokens found"
fi

# Confirm action
echo
read -p "Do you want to update the configuration to use GitHub CLI token? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    log_info "Operation cancelled by user"
    exit 0
fi
echo

# Create backups
log_info "Creating backups..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
for CONFIG_FILE in "${CONFIG_FILES[@]}"; do
    BACKUP_FILE="${CONFIG_FILE}.backup.${TIMESTAMP}"
    cp "$CONFIG_FILE" "$BACKUP_FILE"
    log_success "Backup: $BACKUP_FILE"
done

echo

# Test GitHub CLI token access
log_info "Testing GitHub CLI token access..."
if gh auth token &> /dev/null; then
    log_success "GitHub CLI token accessible"
else
    log_error "Cannot access GitHub CLI token"
    exit 1
fi

# Test GitHub API with the token
log_info "Testing GitHub API access..."
if curl -sf -H "Authorization: Bearer $(gh auth token)" https://api.github.com/user > /dev/null; then
    USERNAME=$(curl -sf -H "Authorization: Bearer $(gh auth token)" https://api.github.com/user | jq -r '.login')
    log_success "GitHub API access confirmed (user: $USERNAME)"
else
    log_error "GitHub API access failed"
    exit 1
fi

echo

# Update Cursor configuration
if [ -f "$CURSOR_CONFIG" ]; then
    log_info "Updating Cursor configuration..."
    cat > "$CURSOR_CONFIG" << 'EOF'
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
    chmod 600 "$CURSOR_CONFIG"
    log_success "Cursor configuration updated"
fi

# Update VS Code configuration (preserving Glean MCP if present)
if [ -f "$VSCODE_CONFIG" ]; then
    log_info "Updating VS Code configuration..."
    
    # Check if Glean MCP exists in current config
    if jq -e '.servers."glean-mcp"' "$VSCODE_CONFIG" > /dev/null 2>&1; then
        log_info "Preserving Glean MCP configuration..."
        GLEAN_CONFIG=$(jq '.servers."glean-mcp"' "$VSCODE_CONFIG")
        
        # Create new config with both GitHub (secure) and Glean (preserved)
        cat > "$VSCODE_CONFIG" << EOF
{
  "servers": {
    "glean-mcp": ${GLEAN_CONFIG},
    "github": {
      "name": "github",
      "type": "stdio",
      "command": "sh",
      "args": [
        "-c",
        "GITHUB_PERSONAL_ACCESS_TOKEN=\$(gh auth token) docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server"
      ],
      "enabled": true
    }
  }
}
EOF
        log_success "Preserved Glean MCP configuration"
    else
        # Just update GitHub MCP
        cat > "$VSCODE_CONFIG" << 'EOF'
{
  "servers": {
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
    fi
    
    chmod 600 "$VSCODE_CONFIG"
    log_success "VS Code configuration updated"
fi

# Set secure permissions on all configs
log_info "Setting secure file permissions..."
for CONFIG_FILE in "${CONFIG_FILES[@]}"; do
    chmod 600 "$CONFIG_FILE"
    PERMS=$(stat -f "%Lp" "$CONFIG_FILE" 2>/dev/null || stat -c "%a" "$CONFIG_FILE" 2>/dev/null)
    if [ "$PERMS" = "600" ]; then
        log_success "$(basename "$CONFIG_FILE"): permissions set to 600"
    else
        log_warning "$(basename "$CONFIG_FILE"): permissions $PERMS (expected 600)"
    fi
done

echo

# Verify no plaintext GitHub tokens in new configs
log_info "Verifying secure configurations..."
VERIFICATION_FAILED=0
for CONFIG_FILE in "${CONFIG_FILES[@]}"; do
    if grep -qE "gho_|ghp_" "$CONFIG_FILE"; then
        log_error "$(basename "$CONFIG_FILE") still contains hardcoded GitHub token!"
        VERIFICATION_FAILED=1
    else
        log_success "$(basename "$CONFIG_FILE"): No hardcoded GitHub tokens"
    fi
done

if [ $VERIFICATION_FAILED -eq 1 ]; then
    log_error "Verification failed! Restoring backups..."
    for CONFIG_FILE in "${CONFIG_FILES[@]}"; do
        BACKUP_FILE="${CONFIG_FILE}.backup.${TIMESTAMP}"
        cp "$BACKUP_FILE" "$CONFIG_FILE"
    done
    exit 1
fi

# Test the new configuration
log_info "Testing new MCP configuration..."
if GITHUB_PERSONAL_ACCESS_TOKEN=$(gh auth token) docker run --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server --version &> /dev/null; then
    log_success "MCP server test successful"
else
    log_error "MCP server test failed"
    log_warning "Restoring backup..."
    cp "$BACKUP_FILE" ~/.cursor/mcp.json
    exit 1
fi

# Display new configurations
echo
log_info "New secure configurations:"
for CONFIG_FILE in "${CONFIG_FILES[@]}"; do
    echo
    echo "$(basename $(dirname "$CONFIG_FILE"))/$(basename "$CONFIG_FILE"):"
    cat "$CONFIG_FILE"
done
echo

# Success summary
echo
echo -e "${GREEN}??????????????????????????????????????????????????????????${NC}"
echo -e "${GREEN}?  Configuration Updated Successfully!                   ?${NC}"
echo -e "${GREEN}??????????????????????????????????????????????????????????${NC}"
echo

log_success "Secure configurations applied"
log_success "Backups saved with timestamp: ${TIMESTAMP}"
for CONFIG_FILE in "${CONFIG_FILES[@]}"; do
    echo "  ? ${CONFIG_FILE}.backup.${TIMESTAMP}"
done
echo

# Next steps
log_info "IMPORTANT NEXT STEPS:"
echo
echo "1. Revoke the old exposed token:"
echo "   ? Visit: https://github.com/settings/tokens"
echo "   ? Find token starting with: gho_7WMPsiVW5Hv2w..."
echo "   ? Click 'Delete' or 'Revoke'"
echo
echo "2. Restart applications to apply changes:"
echo "   Cursor:"
echo "   ? Quit completely (Cmd+Q or killall Cursor)"
echo "   ? Reopen Cursor"
echo ""
echo "   VS Code:"
echo "   ? Quit completely (Cmd+Q or killall 'Visual Studio Code')"
echo "   ? Reopen VS Code"
echo
echo "3. Verify MCP functionality:"
echo "   In Cursor:"
echo "   ? Open Settings ? MCP Servers"
echo "   ? Check 'github' shows as 'Connected'"
echo "   ? Test: @github list my repositories"
echo ""
echo "   In VS Code:"
echo "   ? Open Command Palette (Cmd+Shift+P)"
echo "   ? Type 'MCP' and check server status"
echo
echo "4. Run health check (after restarting apps):"
echo "   ? ~/bin/cursor-mcp-health-check.sh"
echo

log_warning "Your old token is still active until you revoke it!"
log_warning "Complete step 1 immediately to secure your account."
echo

# Optional: Show token revocation URL
read -p "Open GitHub tokens page now? (yes/no): " OPEN_TOKENS
if [ "$OPEN_TOKENS" = "yes" ]; then
    open https://github.com/settings/tokens
    log_info "Opening GitHub tokens page in browser..."
fi

echo
log_success "Script completed successfully!"
