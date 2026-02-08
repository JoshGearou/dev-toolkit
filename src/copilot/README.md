# GitHub Copilot CLI Installation

## Overview

GitHub Copilot CLI is an AI-powered command-line assistant that helps you discover, learn, and run commands. It provides intelligent suggestions and explanations for shell commands, making it easier to work with unfamiliar tools and complex command-line operations.

This directory contains installation, update, and uninstall scripts that follow repository conventions and support multiple installation methods.

## Official Installation Page

For authoritative installation and product details, see: https://github.com/features/copilot/cli

The scripts here wrap the official methods (GitHub CLI extension and npm package) with logging, retry logic, and environment validation.

## Prerequisites

### Platform Requirements
- **macOS** (Darwin) - Primary support
- **Linux** - Full support
- **Windows** - Not supported by these scripts

### Dependencies

**Method 1: GitHub CLI Extension (Recommended)**
- [GitHub CLI](https://cli.github.com/) (`gh`) - Install via `brew install gh` or visit https://cli.github.com/
- GitHub account with authentication: `gh auth login`

**Method 2: npm Package (Alternative)**
- **Node.js 18+** - Managed automatically via [Volta](https://volta.sh/) if available
- **npm** - Included with Node.js
- GitHub account for authentication

### Account Requirements
- **GitHub account** with Copilot access
- **GitHub Copilot subscription** (individual or organization)

## Installation

### Quick Install
```bash
./install_copilot_cli.sh
```

The install script automatically:
1. Detects your platform (macOS/Linux)
2. Tries GitHub CLI extension method first (if `gh` is available)
3. Falls back to npm installation if needed
4. Validates Node.js 18+ for npm method
5. Provides clear next steps for authentication

### Manual Installation

**Option 1: GitHub CLI Extension (Recommended)**
```bash
# Install GitHub CLI first
brew install gh  # macOS
# or visit https://cli.github.com/

# Install Copilot extension
gh extension install github/gh-copilot
```

**Option 2: npm Package**
```bash
# Ensure Node.js 18+ (via Volta recommended)
volta install node@18

# Install globally
npm install -g @github/copilot
```

### Installation Methods Comparison

| Method | Pros | Cons |
|--------|------|------|
| **GitHub CLI Extension** | • Integrated with GitHub CLI<br>• Automatic updates via `gh`<br>• No Node.js dependency | • Requires GitHub CLI<br>• Tied to GitHub ecosystem |
| **npm Package** | • Standard npm workflow<br>• Version pinning available<br>• Works with Node.js toolchain | • Requires Node.js 18+<br>• Manual npm management |

## Usage

### Authentication

**First-time setup:**
```bash
# Authenticate with GitHub (if not already done)
gh auth login

# Authenticate Copilot specifically
gh copilot auth
```

### Common Commands

**Get command suggestions:**
```bash
gh copilot suggest "list all files in current directory"
gh copilot suggest "find large files over 100MB"
gh copilot suggest "compress folder to zip archive"
```

**Explain complex commands:**
```bash
gh copilot explain "find . -type f -name '*.js' -exec grep -l 'TODO' {} +"
gh copilot explain "docker run -it --rm -v $(pwd):/workspace ubuntu:latest"
gh copilot explain "awk '{print $2}' file.txt | sort | uniq -c"
```

**Interactive mode:**
```bash
gh copilot suggest   # Opens interactive suggestion mode
gh copilot explain   # Opens interactive explanation mode
```

### Advanced Usage

**Command options:**
```bash
gh copilot suggest --help     # Show all suggestion options
gh copilot explain --help     # Show all explanation options
gh copilot --version         # Show version information
```

## Updates

### Quick Update
```bash
./update_copilot_cli.sh
```

The update script:
- Automatically detects installation method (GitHub CLI extension vs npm)
- Updates using the appropriate package manager
- Shows version changes and what's new
- Provides testing commands to verify the update

### Manual Updates

**GitHub CLI Extension:**
```bash
gh extension upgrade gh-copilot
```

**npm Package:**
```bash
npm update -g @github/copilot
```

## Uninstallation

### Quick Uninstall
```bash
./uninstall_copilot_cli.sh
```

### Uninstall Options
```bash
./uninstall_copilot_cli.sh -y              # Skip confirmation prompts
./uninstall_copilot_cli.sh -p              # Preserve configuration files
./uninstall_copilot_cli.sh -y -p           # Skip prompts and keep config
./uninstall_copilot_cli.sh --help          # Show all options
```

### Manual Uninstall

**GitHub CLI Extension:**
```bash
gh extension remove gh-copilot
```

**npm Package:**
```bash
npm uninstall -g @github/copilot
```

**Clean up configuration (optional):**
```bash
# Remove configuration directories
rm -rf ~/.config/github-copilot
rm -rf ~/.github-copilot
rm -rf ~/Library/Application\ Support/github-copilot  # macOS only
```

## Troubleshooting

### Common Issues

**Issue**: "gh: command not found" during installation
```bash
# Solution: Install GitHub CLI first
brew install gh              # macOS
# or visit https://cli.github.com/ for other platforms
```

**Issue**: "Node.js 18+ required" error with npm method
```bash
# Solution 1: Install Volta and Node.js 18
curl https://get.volta.sh | bash
source ~/.zshrc              # Restart shell
volta install node@18

# Solution 2: Manual Node.js installation  
# Visit https://nodejs.org/ and install Node.js 18+
```

**Issue**: "gh copilot: command not found" after installation
```bash
# Check installation method and reinstall
gh extension list | grep copilot    # Should show github/gh-copilot
# or
npm list -g @github/copilot         # Should show package version

# If missing, run the install script again
./install_copilot_cli.sh
```

**Issue**: Authentication failures
```bash
# Re-authenticate with GitHub
gh auth login
gh copilot auth

# Verify authentication
gh auth status
```

**Issue**: Permission errors with npm on macOS
```bash
# Solution: Use Volta (recommended) or fix npm permissions
volta install node@18  # Volta handles permissions correctly

# Alternative: Fix npm permissions (not recommended)
sudo chown -R $(whoami) $(npm config get prefix)/{lib/node_modules,bin,share}
```

**Issue**: Multiple Node.js installations causing conflicts
```bash
# Solution: Clean up and use Volta exclusively
brew uninstall node         # Remove Homebrew version if present
volta install node@18       # Install via Volta
which node                  # Should show Volta-managed path
```

### Debugging

**Enable detailed logging:**
```bash
# Set DEBUG=true for verbose output
DEBUG=true ./install_copilot_cli.sh
DEBUG=true ./update_copilot_cli.sh
```

**Check log files:**
```bash
# View recent installation logs
tail -f install_copilot_cli.log
tail -f update_copilot_cli.log
tail -f uninstall_copilot_cli.log
```

**Verify installation:**
```bash
# Check version and basic functionality
gh copilot --version
gh copilot suggest "echo hello world"
```

## Configuration

### Environment Variables

**ANTHROPIC_API_KEY** (not needed for GitHub Copilot)
- GitHub Copilot uses GitHub authentication, not API keys

**GitHub Token**
- Managed automatically via `gh auth login`
- No manual token configuration needed

### Configuration Files

GitHub Copilot CLI stores configuration in:
- **macOS**: `~/Library/Application Support/github-copilot/`
- **Linux**: `~/.config/github-copilot/`

Configuration includes:
- Authentication tokens
- User preferences
- Usage analytics settings (opt-out available)

## Integration with Development Workflow

### Shell Aliases (Optional)

Add these to your shell profile for convenience:
```bash
# Add to ~/.zshrc or ~/.bashrc
alias cop-suggest="gh copilot suggest"
alias cop-explain="gh copilot explain" 
alias cop-auth="gh copilot auth"

# Usage examples after reload:
cop-suggest "deploy app to kubernetes"
cop-explain "kubectl apply -f deployment.yaml"
```

### Editor Integration

GitHub Copilot CLI complements:
- **VS Code**: GitHub Copilot extension for inline suggestions
- **Vim/Neovim**: GitHub Copilot plugins available
- **JetBrains IDEs**: GitHub Copilot plugins available

### CI/CD Integration

Note: GitHub Copilot CLI is designed for interactive use. For automated environments, consider:
- Using the GitHub CLI directly for repository operations
- Integrating with GitHub Actions for automated workflows

## References

### Official Documentation
- **GitHub Copilot CLI**: https://docs.github.com/en/copilot/github-copilot-in-the-cli
- **GitHub CLI**: https://cli.github.com/
- **GitHub Copilot**: https://github.com/features/copilot

### Installation Resources
- **Node.js**: https://nodejs.org/
- **Volta**: https://volta.sh/
- **npm**: https://docs.npmjs.com/

### Repository Guidelines
- **Coding Standards**: See `../../AGENTS.md`
- **Node.js Management**: See `../../bash/common/NODE_VERSION_MANAGEMENT.md`

## Changelog

### Version 2.0 (2024-10-30)
- Enhanced install script with dual installation method support
- Added comprehensive update and uninstall scripts
- Integrated with repository `repo_lib.sh` utilities
- Added Volta/Node.js 18+ validation for npm method
- Comprehensive error handling and logging
- Added platform detection and compatibility checks

### Version 1.0 (Previous)
- Basic npm-only installation script
- Minimal error handling
- No repository convention integration

## License & Support

This tooling follows the repository license. For GitHub Copilot CLI issues:
- **Installation problems**: Check this README's troubleshooting section
- **GitHub Copilot CLI bugs**: Report to https://github.com/github/gh-copilot
- **Account/billing issues**: Contact GitHub Support