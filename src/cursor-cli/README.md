# Cursor CLI Installation

## Overview

Cursor is a modern AI-powered code editor built on VS Code, designed for pair programming with AI. This directory contains scripts to install, update, and manage Cursor IDE and its command-line interface on macOS.

Cursor provides:
- AI-powered code completion and editing
- Natural language code generation
- Intelligent refactoring suggestions
- Built on VS Code with full extension compatibility
- Command-line interface for opening files and projects

## Official Installation Page

Canonical CLI page: https://cursor.com/cli

The official instructions rely on the IDE's command palette to install the shell command. This script automates the DMG download, application install, and symlink creation with verification and logging.

## Prerequisites

### Platform Requirements
- **macOS** (Darwin) - Primary support
- Intel or Apple Silicon Mac
- macOS 10.14 (Mojave) or later

### System Dependencies
- **curl** - For downloading Cursor IDE
- **hdiutil** - For mounting DMG files (built into macOS)
- **plutil** - For reading version information (built into macOS)

### Permissions
- Write access to `/Applications` directory (for IDE installation)
- Write access to `/usr/local/bin` (for CLI symlink) - may require `sudo`

## Installation

### Quick Install

```bash
./install_cursor_cli.sh
```

This will:
1. Download the latest Cursor IDE from the official website
2. Install it to `/Applications/Cursor.app`
3. Create a CLI symlink at `/usr/local/bin/cursor`
4. Verify the installation

### Installation Options

```bash
# Standard installation
./install_cursor_cli.sh

# Force reinstallation (overwrite existing)
./install_cursor_cli.sh --force

# Install IDE only, skip CLI setup
./install_cursor_cli.sh --skip-symlink

# Show help
./install_cursor_cli.sh --help
```

### Manual CLI Setup

If the automatic CLI setup fails (usually due to permissions), you can create the symlink manually:

```bash
# Create the symlink with sudo
sudo ln -s /Applications/Cursor.app/Contents/Resources/app/bin/cursor /usr/local/bin/cursor

# Alternative path (if the above doesn't work)
sudo ln -s /Applications/Cursor.app/Contents/MacOS/Cursor /usr/local/bin/cursor
```

## Usage

### Launching Cursor

```bash
# Open Cursor IDE
open -a Cursor

# Or use the CLI (if set up)
cursor
```

### Command Line Interface

Once the CLI symlink is set up, you can use the `cursor` command:

```bash
# Open a file
cursor myfile.py

# Open a project directory
cursor /path/to/project

# Open current directory
cursor .

# Create and open a new file
cursor new-file.js

# Show CLI help
cursor --help
```

### Common Use Cases

```bash
# Start a new project
mkdir my-project && cd my-project
cursor .

# Edit configuration files
cursor ~/.zshrc

# Open multiple files
cursor file1.py file2.py file3.py

# Work with git repositories
cd my-repo
cursor README.md
```

## Authentication & Setup

### First Launch
1. Open Cursor for the first time
2. Sign in with your GitHub, Google, or email account
3. Cursor may prompt you to migrate settings from VS Code
4. Install any desired extensions through the Extensions panel

### AI Features Setup
Cursor's AI features work out of the box with their built-in models. For enhanced functionality:
1. Sign up for Cursor Pro (optional)
2. Configure AI model preferences in Settings
3. Set up custom AI prompts and templates

### VS Code Extension Compatibility
Cursor is compatible with VS Code extensions:
1. Open Command Palette (`Cmd+Shift+P`)
2. Run "Extensions: Install Extensions"
3. Search and install extensions as you would in VS Code

## Updates

### Automatic Updates (Default)
Cursor has built-in auto-update enabled by default. It will:
- Check for updates when launching
- Download and install updates in the background
- Prompt to restart when updates are ready

### Manual Update Check

```bash
# Check for and install updates
./update_cursor_cli.sh

# Check only (don't install)
./update_cursor_cli.sh --check-only

# Force update check even with auto-update enabled
./update_cursor_cli.sh --force
```

### Update Methods

The update script handles:
1. **Auto-update enabled**: Guides you to manual update checking in Cursor
2. **Auto-update disabled**: Downloads and reinstalls the latest version
3. **CLI fixes**: Repairs broken CLI symlinks during updates

### Disabling Auto-Update

To prefer manual updates:
1. Open Cursor
2. Go to Preferences → Settings (`Cmd+,`)
3. Search for "update.mode"
4. Change from "default" to "manual" or "none"

## Uninstallation

### Complete Removal

```bash
# Remove everything with confirmation
./uninstall_cursor_cli.sh

# Remove everything without prompts
./uninstall_cursor_cli.sh -y
```

### Selective Removal Options

```bash
# Keep configuration files
./uninstall_cursor_cli.sh --keep-config

# Remove only CLI, keep IDE
./uninstall_cursor_cli.sh --keep-ide

# Remove only configuration files
./uninstall_cursor_cli.sh --config-only

# Show help
./uninstall_cursor_cli.sh --help
```

### What Gets Removed

**Full uninstall removes:**
- Cursor IDE (`/Applications/Cursor.app`)
- CLI command (`/usr/local/bin/cursor`)
- User configuration (`~/Library/Application Support/Cursor`)
- User preferences (`~/Library/Preferences/com.todesktop.*.plist`)
- Caches and logs (`~/Library/Caches/Cursor`, `~/Library/Logs/Cursor`)

**Configuration locations:**
- `~/.cursor` - User settings (if exists)
- `~/Library/Application Support/Cursor` - Main configuration
- `~/Library/Preferences/com.todesktop.230313mzl4w4u92.plist` - macOS preferences
- `~/Library/Caches/Cursor` - Application caches
- `~/Library/Logs/Cursor` - Application logs

## Troubleshooting

### Installation Issues

**Problem**: Download fails or times out
```bash
# Check internet connection
curl -I https://download.cursor.sh/mac

# Try installation with force flag
./install_cursor_cli.sh --force
```

**Problem**: Permission denied during CLI setup
```bash
# Create CLI symlink manually with sudo
sudo ./install_cursor_cli.sh --skip-symlink
sudo ln -s /Applications/Cursor.app/Contents/Resources/app/bin/cursor /usr/local/bin/cursor
```

**Problem**: DMG mounting fails
```bash
# Check available disk space
df -h

# Clear temporary files and retry
rm -rf /tmp/cursor* && ./install_cursor_cli.sh
```

### CLI Issues

**Problem**: `cursor` command not found
```bash
# Check if symlink exists
ls -la /usr/local/bin/cursor

# Verify PATH includes /usr/local/bin
echo $PATH

# Fix CLI symlink
./update_cursor_cli.sh

# Or create manually
sudo ln -s /Applications/Cursor.app/Contents/Resources/app/bin/cursor /usr/local/bin/cursor
```

**Problem**: CLI points to wrong binary
```bash
# Check what the symlink points to
readlink /usr/local/bin/cursor

# Remove and recreate
sudo rm /usr/local/bin/cursor
sudo ln -s /Applications/Cursor.app/Contents/Resources/app/bin/cursor /usr/local/bin/cursor
```

### Runtime Issues

**Problem**: Cursor won't start or crashes
```bash
# Check system logs
log show --predicate 'process == "Cursor"' --info --last 1h

# Reset configuration
./uninstall_cursor_cli.sh --config-only
./install_cursor_cli.sh
```

**Problem**: AI features not working
1. Check internet connection
2. Verify account authentication in Cursor settings
3. Try signing out and back in
4. Check Cursor service status at their website

**Problem**: Extensions not working
1. Open Command Palette (`Cmd+Shift+P`)
2. Run "Extensions: Show Installed Extensions"
3. Disable and re-enable problematic extensions
4. Check extension compatibility with current Cursor version

### Version Issues

**Problem**: Can't determine Cursor version
```bash
# Check manually
plutil -p /Applications/Cursor.app/Contents/Info.plist | grep -i version

# Reinstall if corrupted
./install_cursor_cli.sh --force
```

**Problem**: Update script reports wrong status
```bash
# Force update check
./update_cursor_cli.sh --force

# Or manually reinstall
./install_cursor_cli.sh --force
```

## Advanced Configuration

### Custom CLI Location

To install the CLI command to a different location:

```bash
# Install IDE without CLI
./install_cursor_cli.sh --skip-symlink

# Create custom symlink location
mkdir -p ~/bin
ln -s /Applications/Cursor.app/Contents/Resources/app/bin/cursor ~/bin/cursor

# Add to your PATH in ~/.zshrc or ~/.bash_profile
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
```

### Network Configuration

For corporate environments with proxies:

```bash
# Set proxy for downloads
export https_proxy=http://proxy.company.com:8080
export http_proxy=http://proxy.company.com:8080

# Then run installation
./install_cursor_cli.sh
```

### Integration with Other Tools

```bash
# Add Cursor to your shell aliases
echo 'alias c="cursor"' >> ~/.zshrc
echo 'alias edit="cursor"' >> ~/.zshrc

# Git integration - edit with Cursor
git config --global core.editor "cursor --wait"
```

## Script Details

### File Locations

```
cursor-cli/
├── install_cursor_cli.sh      # Main installation script
├── update_cursor_cli.sh       # Update and maintenance script  
├── uninstall_cursor_cli.sh    # Removal script
├── README.md                  # This documentation
└── *.log                      # Generated log files
```

### Logging

All scripts create detailed log files:
- `install_cursor_cli.log` - Installation process log
- `update_cursor_cli.log` - Update process log
- `uninstall_cursor_cli.log` - Uninstallation process log

Log files include:
- Timestamps for all operations
- Success/failure status
- Error messages and debugging information
- System environment details

### Dependencies

Scripts use utilities from `../../bash/common/repo_lib.sh`:
- `log_message()` - Timestamped logging
- `run_command_with_retry()` - Retry logic for network operations
- Error handling and cleanup functions

## Differences from VS Code

### Key Advantages of Cursor
- **AI-First Design**: Built-in AI assistance for coding
- **Natural Language Editing**: Write code using plain English
- **Intelligent Suggestions**: Context-aware code completion
- **Refactoring AI**: Automated code improvements
- **Compatibility**: Full VS Code extension support

### Migration from VS Code
1. Cursor can import VS Code settings automatically
2. Extensions work without modification
3. Keybindings are identical by default
4. Workspaces and projects transfer seamlessly

## Alternatives and Related Tools

If Cursor doesn't meet your needs, consider:

- **VS Code with GitHub Copilot**: Traditional VS Code with AI extension
- **JetBrains IDEs**: IntelliJ, PyCharm with AI assistant
- **Vim/Neovim**: With AI plugins like codeium.vim
- **Emacs**: With AI packages like copilot.el

## References

### Official Documentation
- **Cursor Website**: https://cursor.com
- **Cursor Documentation**: https://cursor.com/docs
- **Download Page**: https://download.cursor.sh/mac
- **GitHub Repository**: https://github.com/getcursor/cursor

### Community Resources  
- **Discord Community**: Available through Cursor website
- **Feature Requests**: Submit through Cursor IDE
- **Bug Reports**: Use Help → Report Issue in Cursor

### Related Tools in This Repository
- **GitHub Copilot CLI**: `../copilot/` - GitHub's AI CLI tools
- **Claude CLI**: `../claude-cli/` - Anthropic's Claude AI CLI
- **Gemini CLI**: `../gemini-cli/` - Google's Gemini AI CLI

---

**Last Updated**: October 30, 2025  
**Cursor Version Tested**: Latest available  
**Script Version**: 1.0  
**Platform**: macOS (Darwin)