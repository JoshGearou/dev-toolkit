#!/bin/bash
#
# setup_azure_vm.sh - Set up an Azure Linux VM with SSH keys and clone dev repo
#
# Usage: ./setup_azure_vm.sh [options] [vm-name-or-ip]
#   If vm-name-or-ip not provided, prompts interactively
#
# Steps:
#   1. Copy SSH keys from local machine to VM
#   2. Create ~/src/sandbox directory on VM
#   3. Clone dev-rerickso repository
#

set -u  # Exit on undefined variables
set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
GITHUB_ORG="org-132020694@github.com:linkedin-sandbox"
REPO_NAME="dev-rerickso"
REMOTE_DIR="~/src/sandbox"

# SSH ControlMaster settings
CONTROL_PATH=""
CONTROL_PERSIST="5m"

usage() {
    cat << EOF
Usage: $(basename "$0") [options] [vm-name-or-ip]

Set up an Azure Linux VM with SSH keys and clone the dev repository.

Arguments:
  vm-name-or-ip    VM hostname (e.g., ${USER}-ld1) or IP address (e.g., 10.x.x.x)
                   If not provided, prompts interactively.
                   Hostnames are auto-appended with .linkedin.biz if needed.

Options:
  -h, --help       Show this help message and exit

Examples:
  $(basename "$0")                        # Interactive mode, prompts for VM
  $(basename "$0") ${USER}-ld1           # Connect by hostname
  $(basename "$0") 10.195.32.45           # Connect by IP address
  $(basename "$0") ${USER}@10.195.32.45  # Connect by user@IP

Steps performed:
  1. Establish SSH connection (password entered once, then cached)
  2. Copy SSH keys (~/.ssh/\$USER*, id_*, custom keys) to VM
  3. Update system packages (tdnf update)
  4. Install Docker (moby-engine, moby-cli, etc.)
  5. Install tmux (for long-running builds)
  6. Install Claude Code CLI (AI-powered coding assistant)
  7. Create ~/src/sandbox directory on VM
  8. Verify GitHub SSH access
  9. Clone dev-rerickso repository

Prerequisites:
  - VPN or corp network connection
  - VM provisioned at go/azureworkstation
  - SSH keys generated locally (ssh-keygen -t ed25519)

Check VM status: go/myvm or go/my-azureworkstation
EOF
    exit 0
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if input contains an IP address (with or without user@)
contains_ip_address() {
    local input="$1"
    # Match IPv4 pattern, optionally preceded by user@
    if [[ "$input" =~ ^([^@]+@)?[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        return 0
    fi
    return 1
}

# Get VM name/IP from argument or prompt
get_vm_target() {
    local vm_target="${1:-}"

    if [[ -z "$vm_target" ]]; then
        echo -n "Enter VM name (e.g., ${USER}-ld1) or IP address (user@ip or ip): "
        read -r vm_target
    fi

    # If it contains an IP address (user@ip or just ip), use as-is
    if contains_ip_address "$vm_target"; then
        echo "$vm_target"
        return
    fi

    # For hostnames: append .linkedin.biz if not already present
    # Handle user@hostname format
    if [[ "$vm_target" == *"@"* ]]; then
        local user_part="${vm_target%@*}"
        local host_part="${vm_target#*@}"
        if [[ "$host_part" != *".linkedin.biz" ]]; then
            host_part="${host_part}.linkedin.biz"
        fi
        vm_target="${user_part}@${host_part}"
    else
        if [[ "$vm_target" != *".linkedin.biz" ]]; then
            vm_target="${vm_target}.linkedin.biz"
        fi
    fi

    echo "$vm_target"
}

# SSH wrapper that uses ControlMaster
ssh_cmd() {
    ssh -o ControlPath="$CONTROL_PATH" "$@"
}

# SSH wrapper with TTY for sudo commands
ssh_sudo() {
    ssh -t -o ControlPath="$CONTROL_PATH" "$@"
}

# SCP wrapper that uses ControlMaster
scp_cmd() {
    scp -o ControlPath="$CONTROL_PATH" "$@"
}

# Start SSH ControlMaster connection
start_control_master() {
    local vm_target="$1"

    # Create control socket path
    CONTROL_PATH="/tmp/ssh-control-$$-$(date +%s)"

    log_info "Establishing SSH connection to ${vm_target}..."
    log_info "You will be prompted for your password once."
    echo

    # Start master connection in background
    if ! ssh -o ControlMaster=yes \
            -o ControlPath="$CONTROL_PATH" \
            -o ControlPersist="$CONTROL_PERSIST" \
            -o ConnectTimeout=30 \
            "$vm_target" "echo 'Connection established'"; then
        log_error "Cannot connect to ${vm_target}"
        log_info "Make sure:"
        log_info "  1. You are on VPN or corp network"
        log_info "  2. The VM is provisioned and running (check go/myvm)"
        log_info "  3. Your credentials are correct"
        return 1
    fi

    log_info "SSH connection cached (will reuse for all commands)"
    return 0
}

# Stop SSH ControlMaster connection
stop_control_master() {
    if [[ -n "$CONTROL_PATH" ]] && [[ -S "$CONTROL_PATH" ]]; then
        ssh -o ControlPath="$CONTROL_PATH" -O exit "" 2>/dev/null || true
    fi
}

# Cleanup on exit
cleanup() {
    stop_control_master
}

# Copy SSH keys to VM
# Uses pattern from Envoy dev setup: scp $HOME/.ssh/$USER* <vm>:/home/$USER/.ssh
copy_ssh_keys() {
    local vm_target="$1"
    local ssh_dir="$HOME/.ssh"

    log_info "Copying SSH keys to ${vm_target}..."

    # Create .ssh directory on remote if it doesn't exist
    ssh_cmd "$vm_target" "mkdir -p ~/.ssh && chmod 700 ~/.ssh"

    # Copy all user-specific SSH files (pattern from Envoy setup guide)
    # This captures: ${USER}_at_linkedin.com_ssh_key, id_rsa, id_ed25519, etc.
    local user_keys
    user_keys=$(ls -1 "${ssh_dir}/${USER}"* 2>/dev/null || true)
    if [[ -n "$user_keys" ]]; then
        log_info "Copying user-specific keys (${USER}*)..."
        scp_cmd "${ssh_dir}/${USER}"* "${vm_target}:~/.ssh/" 2>/dev/null || true
    fi

    # Copy standard SSH keys (id_rsa, id_ed25519)
    for key_type in id_rsa id_ed25519; do
        if [[ -f "${ssh_dir}/${key_type}" ]]; then
            log_info "Copying ${key_type}..."
            scp_cmd "${ssh_dir}/${key_type}" "${vm_target}:~/.ssh/${key_type}"
            if [[ -f "${ssh_dir}/${key_type}.pub" ]]; then
                scp_cmd "${ssh_dir}/${key_type}.pub" "${vm_target}:~/.ssh/${key_type}.pub"
            fi
        fi
    done

    # Copy any custom keys referenced in SSH config (IdentityFile directives)
    if [[ -f "${ssh_dir}/config" ]]; then
        log_info "Scanning SSH config for custom IdentityFile entries..."
        while IFS= read -r key_path; do
            # Expand ~ to home directory
            key_path="${key_path/#\~/$HOME}"
            if [[ -f "$key_path" ]]; then
                local key_name
                key_name=$(basename "$key_path")
                # Skip if already copied via $USER* pattern
                if [[ "$key_name" != "${USER}"* ]]; then
                    log_info "Copying custom key: ${key_name}..."
                    scp_cmd "$key_path" "${vm_target}:~/.ssh/${key_name}"
                    if [[ -f "${key_path}.pub" ]]; then
                        scp_cmd "${key_path}.pub" "${vm_target}:~/.ssh/${key_name}.pub"
                    fi
                fi
            fi
        done < <(grep -i '^\s*IdentityFile' "${ssh_dir}/config" | awk '{print $2}' | sort -u)
    fi

    # Copy SSH config (filtering out macOS-specific options)
    if [[ -f "${ssh_dir}/config" ]]; then
        log_info "Copying SSH config (filtering macOS-specific options)..."
        # Filter out macOS-only options: UseKeychain, AddKeysToAgent yes
        grep -viE '^\s*(UseKeychain|AddKeysToAgent\s+yes)' "${ssh_dir}/config" > "/tmp/ssh_config_linux_$$" || true
        scp_cmd "/tmp/ssh_config_linux_$$" "${vm_target}:~/.ssh/config"
        rm -f "/tmp/ssh_config_linux_$$"
    fi

    # Copy known_hosts (for GitHub, etc.)
    if [[ -f "${ssh_dir}/known_hosts" ]]; then
        log_info "Copying known_hosts..."
        scp_cmd "${ssh_dir}/known_hosts" "${vm_target}:~/.ssh/known_hosts"
    fi

    # Set proper permissions on all SSH files
    log_info "Setting SSH file permissions..."
    ssh_cmd "$vm_target" "chmod 700 ~/.ssh && chmod 600 ~/.ssh/* 2>/dev/null; chmod 644 ~/.ssh/*.pub 2>/dev/null || true"

    # Add public key to authorized_keys for passwordless SSH
    for key_type in id_ed25519 id_rsa; do
        if [[ -f "${ssh_dir}/${key_type}.pub" ]]; then
            log_info "Adding ${key_type}.pub to authorized_keys..."
            local pub_key
            pub_key=$(cat "${ssh_dir}/${key_type}.pub")
            ssh_cmd "$vm_target" "grep -qxF '${pub_key}' ~/.ssh/authorized_keys 2>/dev/null || echo '${pub_key}' >> ~/.ssh/authorized_keys"
            ssh_cmd "$vm_target" "chmod 600 ~/.ssh/authorized_keys"
            break
        fi
    done

    log_info "SSH keys copied successfully"

    # Set up persistent ssh-agent via systemd (survives across sessions)
    log_info "Configuring persistent ssh-agent via systemd..."

    # Create systemd user directory
    ssh_cmd "$vm_target" "mkdir -p ~/.config/systemd/user"

    # Create ssh-agent service
    ssh_cmd "$vm_target" "cat > ~/.config/systemd/user/ssh-agent.service << 'SVCEOF'
[Unit]
Description=SSH Agent

[Service]
Type=simple
Environment=SSH_AUTH_SOCK=%t/ssh-agent.socket
ExecStart=/usr/bin/ssh-agent -D -a \$SSH_AUTH_SOCK

[Install]
WantedBy=default.target
SVCEOF"

    # Enable lingering so user services run without being logged in
    ssh_sudo "$vm_target" "sudo loginctl enable-linger \$USER" || true

    # Enable and start the ssh-agent service
    ssh_cmd "$vm_target" "systemctl --user daemon-reload"
    ssh_cmd "$vm_target" "systemctl --user enable ssh-agent.service"
    ssh_cmd "$vm_target" "systemctl --user start ssh-agent.service"

    # Add SSH_AUTH_SOCK to bashrc
    ssh_cmd "$vm_target" "grep -q 'SSH_AUTH_SOCK.*ssh-agent.socket' ~/.bashrc 2>/dev/null || cat >> ~/.bashrc << 'BASHEOF'

# Use persistent ssh-agent socket
export SSH_AUTH_SOCK=\"\$XDG_RUNTIME_DIR/ssh-agent.socket\"
BASHEOF"

    log_info "Persistent ssh-agent configured"
    log_info "Enter passphrase once after VM reboot, then it's cached until next reboot"
    return 0
}

# Create sandbox directory on VM
create_sandbox_dir() {
    local vm_target="$1"

    log_info "Creating ${REMOTE_DIR} on ${vm_target}..."

    ssh_cmd "$vm_target" "mkdir -p ${REMOTE_DIR}"

    log_info "Directory created"
    return 0
}

# Update system packages on VM (Azure Linux / Mariner)
update_system() {
    local vm_target="$1"

    log_info "Updating system packages..."

    # Update using tdnf (Azure Linux / Mariner package manager)
    ssh_sudo "$vm_target" "sudo tdnf update -y" || true

    # Note: patchtool --patch-now requires interactive auth, skipping
    # Run manually if needed: patchtool --patch-now

    log_info "System update complete"
    return 0
}

# Install Docker on VM (Azure Linux / Mariner)
install_docker() {
    local vm_target="$1"

    log_info "Installing Docker..."

    # Check if Docker is already installed and running
    if ssh_cmd "$vm_target" "command -v docker &>/dev/null && systemctl is-active docker &>/dev/null"; then
        log_info "Docker already installed and running, skipping"
        return 0
    fi

    # Install Docker packages (Azure Linux / Mariner uses tdnf)
    log_info "Installing Docker packages..."
    ssh_sudo "$vm_target" "sudo tdnf install -y moby-engine moby-cli moby-compose ca-certificates moby-buildx"

    # Add user to docker group
    log_info "Adding user to docker group..."
    ssh_sudo "$vm_target" "sudo usermod -aG docker \$USER"

    # Enable and start Docker service
    log_info "Enabling Docker service..."
    ssh_sudo "$vm_target" "sudo systemctl enable docker.service"
    ssh_sudo "$vm_target" "sudo systemctl start docker.service"

    # Configure Docker network to avoid routing conflicts
    log_info "Configuring Docker network..."
    ssh_sudo "$vm_target" "sudo mkdir -p /etc/docker"
    ssh_sudo "$vm_target" "cat << 'DOCKEREOF' | sudo tee /etc/docker/daemon.json > /dev/null
{
  \"bip\": \"192.168.254.1/24\",
  \"default-address-pools\": [
    {\"base\": \"192.168.0.0/16\", \"size\": 24},
    {\"base\": \"192.169.0.0/16\", \"size\": 24}
  ]
}
DOCKEREOF"

    # Restart Docker to apply network config
    ssh_sudo "$vm_target" "sudo systemctl restart docker"

    log_info "Docker installed successfully"
    log_warn "Note: Log out and back in for docker group membership to take effect"
    return 0
}

# Install tmux on VM (useful for long-running builds)
install_tmux() {
    local vm_target="$1"

    log_info "Installing tmux..."

    # Check if tmux is already installed
    if ssh_cmd "$vm_target" "command -v tmux &>/dev/null"; then
        log_info "tmux already installed, skipping"
        return 0
    fi

    # Install tmux
    ssh_sudo "$vm_target" "sudo tdnf install -y tmux"

    log_info "tmux installed successfully"
    log_info "Usage: 'tmux' to start, 'tmux attach' to reattach after disconnect"
    return 0
}

# Install Claude Code CLI on VM
install_claude_code() {
    local vm_target="$1"

    log_info "Installing Claude Code CLI..."

    # Check if claude is already installed and in PATH
    if ssh_cmd "$vm_target" "command -v claude &>/dev/null"; then
        log_info "Claude Code CLI already installed, skipping"
        return 0
    fi

    # Install Claude Code CLI
    ssh_cmd "$vm_target" "curl -fsSL https://claude.ai/install.sh | bash"

    # Ensure ~/.local/bin is in PATH (installer puts binary there)
    log_info "Ensuring ~/.local/bin is in PATH..."
    ssh_cmd "$vm_target" "grep -q 'export PATH=\"\$HOME/.local/bin:\$PATH\"' ~/.bashrc 2>/dev/null || echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"

    # Verify installation with updated PATH
    if ssh_cmd "$vm_target" "export PATH=\"\$HOME/.local/bin:\$PATH\" && command -v claude &>/dev/null"; then
        log_info "Claude Code CLI installed successfully"
        log_info "Usage: 'claude' to start interactive mode"
    else
        log_warn "Claude Code CLI installation may require shell restart"
        log_info "After login, run: source ~/.bashrc && claude"
    fi

    return 0
}

# Verify GitHub SSH access
verify_github_access() {
    local vm_target="$1"

    log_info "Verifying GitHub SSH access..."

    # Test SSH connection to GitHub
    local github_output
    if github_output=$(ssh_cmd "$vm_target" "ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -T git@github.com 2>&1"); then
        # This won't actually succeed (exit 1) but output should contain "successfully authenticated"
        :
    fi

    if echo "$github_output" | grep -q "successfully authenticated"; then
        log_info "GitHub SSH access verified"
        return 0
    else
        log_error "GitHub SSH access failed"
        log_info "Output: $github_output"
        log_info ""
        log_info "To fix, ensure your SSH key is added to GitHub:"
        log_info "  1. Copy public key: cat ~/.ssh/*_at_linkedin.com_ssh_key.pub"
        log_info "  2. Add to GitHub: https://github.com/settings/keys"
        log_info "  3. Configure SSO for linkedin-multiproduct org"
        return 1
    fi
}

# Clone repository on VM
clone_repository() {
    local vm_target="$1"

    log_info "Cloning ${REPO_NAME} repository on ${vm_target}..."

    # Check if repo already exists - skip for idempotency
    if ssh_cmd "$vm_target" "test -d ${REMOTE_DIR}/${REPO_NAME}"; then
        log_info "Repository already exists at ${REMOTE_DIR}/${REPO_NAME}, skipping"
        return 0
    fi

    # Clone the repository
    ssh_cmd "$vm_target" "cd ${REMOTE_DIR} && git clone ${GITHUB_ORG}/${REPO_NAME}.git"

    log_info "Repository cloned successfully"
    return 0
}

# Main function
main() {
    local vm_target

    # Set up cleanup trap
    trap cleanup EXIT

    # Parse options
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                usage
                ;;
            -*)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
            *)
                break
                ;;
        esac
        shift
    done

    echo "========================================"
    echo "  Azure Linux VM Setup Script"
    echo "========================================"
    echo

    # Get VM name or IP
    vm_target=$(get_vm_target "${1:-}")

    log_info "Setting up VM: ${vm_target}"
    echo

    # Step 1: Establish SSH connection with ControlMaster (password once)
    if ! start_control_master "$vm_target"; then
        exit 1
    fi
    echo

    # Step 2: Copy SSH keys
    if ! copy_ssh_keys "$vm_target"; then
        exit 1
    fi
    echo

    # Step 3: Update system packages
    if ! update_system "$vm_target"; then
        log_warn "System update failed, continuing..."
    fi
    echo

    # Step 4: Install Docker
    if ! install_docker "$vm_target"; then
        log_warn "Docker installation failed, continuing..."
    fi
    echo

    # Step 5: Install tmux
    if ! install_tmux "$vm_target"; then
        log_warn "tmux installation failed, continuing..."
    fi
    echo

    # Step 6: Install Claude Code CLI
    if ! install_claude_code "$vm_target"; then
        log_warn "Claude Code CLI installation failed, continuing..."
    fi
    echo

    # Step 7: Create sandbox directory
    if ! create_sandbox_dir "$vm_target"; then
        exit 1
    fi
    echo

    # Step 8: Verify GitHub SSH access before cloning
    if ! verify_github_access "$vm_target"; then
        log_warn "Skipping clone due to GitHub access issue"
        log_info "Fix GitHub SSH access and re-run this script"
    else
        echo
        # Step 9: Clone repository
        if ! clone_repository "$vm_target"; then
            exit 1
        fi
    fi
    echo

    log_info "========================================"
    log_info "  VM Setup Complete!"
    log_info "========================================"
    log_info ""
    log_info "Next steps:"
    log_info "  1. SSH to your VM: ssh ${vm_target}"
    log_info "  2. Navigate to repo: cd ${REMOTE_DIR}/${REPO_NAME}"
    log_info "  3. Start tmux session: tmux (reattach with: tmux attach)"
    log_info "  4. Test Docker: docker run hello-world"
    log_info "  5. Start Claude Code: claude"
    log_info ""
    log_info "Note: Log out and back in for docker group membership to take effect"
    log_info ""
}

main "$@"
