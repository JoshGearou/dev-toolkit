# Claude Code CLI Installation

## Overview

Claude Code CLI is Anthropic's AI-powered command-line assistant that provides intelligent code suggestions, explanations, and interactive programming support. It leverages Claude AI to help developers with coding tasks, debugging, and learning new programming concepts.

This directory contains installation, update, and uninstall scripts that follow repository conventions and provide robust error handling and logging.

## Official Installation Page

Authoritative quickstart and usage guide: https://docs.claude.com/en/docs/claude-code/quickstart

The repository scripts add idempotent automation, environment validation (Node.js 18+), and enhanced troubleshooting over the base instructions.

## Prerequisites

### Platform Requirements
- **macOS** (Darwin) - Primary support
- **Linux** - Full support  
- **Windows** - Not supported by these scripts

### Dependencies

**Node.js and npm Requirements:**
- **Node.js 18+** - Automatically managed via [Volta](https://volta.sh/) if available
- **npm** - Included with Node.js
- Internet connection for npm package installation

### Account Requirements
- **Anthropic account** - Sign up at https://console.anthropic.com/
- **API key** - Required for Claude Code CLI to function
- **API usage credits** - Claude Code CLI consumes API tokens for requests

## Installation

### Quick Install
```bash
./install_claude_cli.sh
```

The install script automatically:
1. Detects your platform (macOS/Linux)
2. Validates Node.js 18+ and npm availability (using Volta if present)
3. Installs `@anthropic-ai/claude-code` via npm
4. Checks for ANTHROPIC_API_KEY environment variable
5. Provides setup instructions for API key if not configured

### Manual Installation

```bash
# Ensure Node.js 18+ (via Volta recommended)
volta install node@18

# Install Claude Code CLI globally
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version
```

### API Key Setup (Required)

Claude Code CLI requires an Anthropic API key to function:

1. **Get API Key:**
   - Visit https://console.anthropic.com/
   - Sign up or log in to your account
   - Navigate to API Keys section
   - Generate a new API key

2. **Configure Environment Variable:**
   ```bash
   # Add to your shell profile (~/.zshrc or ~/.bashrc)
   echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.zshrc
   
   # Reload shell configuration
   source ~/.zshrc
   
   # Verify setup
   echo $ANTHROPIC_API_KEY
   ```

3. **Test Authentication:**
   ```bash
   claude --version  # Should work without errors
   ```

## Usage

### Basic Commands

**Interactive Mode:**
```bash
claude                    # Start interactive session
claude --help            # Show all available options
claude --version         # Display version information
```

### Interactive Features

When you run `claude`, you enter an interactive session where you can:

- **Ask coding questions:** "How do I implement a binary search in Python?"
- **Request code reviews:** Paste your code and ask for feedback
- **Debug issues:** Describe errors and get debugging assistance
- **Learn concepts:** "Explain how async/await works in JavaScript"
- **Generate code:** "Create a REST API endpoint for user authentication"

### Usage Examples

**Code Generation:**
```bash
# Start interactive session
claude

# Then in the session:
> Generate a Python function to validate email addresses using regex
> Create a React component for a todo list
> Write a bash script to backup a database
```

**Code Explanation:**
```bash
# In claude interactive session:
> Explain this code: [paste your code here]
> What does this SQL query do: SELECT * FROM users WHERE created_at > NOW() - INTERVAL 1 DAY
```

**Debugging Help:**
```bash
# In claude interactive session:
> I'm getting this error: TypeError: Cannot read property 'length' of undefined
> My Python script fails with ImportError, here's the code: [paste code]
```

## Updates

### Quick Update
```bash
./update_claude_cli.sh
```

The update script:
- Detects Claude Code CLI installation via npm
- Shows current version before updating  
- Updates to latest version via `npm update`
- Displays version changes and testing instructions
- Reminds about API key configuration if needed

### Manual Update

```bash
npm update -g @anthropic-ai/claude-code
```

## Uninstallation

### Quick Uninstall
```bash
./uninstall_claude_cli.sh
```

### Uninstall Options
```bash
./uninstall_claude_cli.sh -y              # Skip confirmation prompts
./uninstall_claude_cli.sh -p              # Preserve configuration files
./uninstall_claude_cli.sh -y -p           # Skip prompts and keep config
./uninstall_claude_cli.sh --help          # Show all options
```

### Manual Uninstall

```bash
# Remove npm package
npm uninstall -g @anthropic-ai/claude-code

# Remove configuration (optional)
rm -rf ~/.config/claude-code
rm -rf ~/.claude-code

# Remove API key from shell profile (optional)
# Edit ~/.zshrc or ~/.bashrc and remove:
# export ANTHROPIC_API_KEY='...'
```

## Troubleshooting

### Common Issues

**Issue**: "claude: command not found" after installation
```bash
# Solution 1: Check npm global bin path
npm config get prefix
echo $PATH | grep $(npm config get prefix)

# Solution 2: Reinstall with correct Node.js version
volta install node@18
npm install -g @anthropic-ai/claude-code

# Solution 3: Manual PATH fix
export PATH="$(npm config get prefix)/bin:$PATH"
```

**Issue**: "API key not found" or authentication errors
```bash
# Solution: Verify API key setup
echo $ANTHROPIC_API_KEY              # Should show your key
grep ANTHROPIC_API_KEY ~/.zshrc      # Should show export line

# If missing, add API key:
echo 'export ANTHROPIC_API_KEY="your-key"' >> ~/.zshrc
source ~/.zshrc
```

**Issue**: "Node.js 18+ required" error
```bash
# Solution 1: Install via Volta (recommended)
curl https://get.volta.sh | bash
source ~/.zshrc
volta install node@18

# Solution 2: Manual Node.js installation
# Visit https://nodejs.org/ and download Node.js 18+

# Verify version
node --version  # Should show 18.x.x or higher
```

**Issue**: npm permission errors
```bash
# Solution: Use Volta (recommended) or fix npm permissions
volta install node@18  # Volta handles permissions correctly

# Alternative: Fix npm permissions (not recommended)
sudo chown -R $(whoami) $(npm config get prefix)/{lib/node_modules,bin,share}
```

**Issue**: Network or installation errors
```bash
# Check npm registry connectivity
npm ping

# Clear npm cache
npm cache clean --force

# Try alternative registry
npm install -g @anthropic-ai/claude-code --registry https://registry.npmjs.org/

# Check proxy settings if behind corporate firewall
npm config get proxy
npm config get https-proxy
```

**Issue**: "Rate limit exceeded" or API quota errors
```bash
# Check API usage at https://console.anthropic.com/
# Consider upgrading API plan or reducing usage frequency
# API errors are from Anthropic's service, not the CLI tool
```

### Debugging

**Enable verbose logging:**
```bash
DEBUG=true ./install_claude_cli.sh
DEBUG=true ./update_claude_cli.sh
```

**Check installation status:**
```bash
# Verify npm package
npm list -g @anthropic-ai/claude-code

# Check command availability  
which claude
claude --version

# Test API connectivity (requires API key)
claude --help
```

**View log files:**
```bash
tail -f install_claude_cli.log
tail -f update_claude_cli.log  
tail -f uninstall_claude_cli.log
```

## Configuration

### Environment Variables

**ANTHROPIC_API_KEY** (Required)
- Your Anthropic API key for authentication
- Get from: https://console.anthropic.com/
- Example: `export ANTHROPIC_API_KEY="sk-ant-api03-..."`

### Configuration Files

Claude Code CLI may store configuration in:
- **macOS**: `~/Library/Application Support/claude-code/`
- **Linux**: `~/.config/claude-code/`

Configuration typically includes:
- User preferences and settings
- Command history (if enabled)
- Cached responses (temporary)

## API Usage and Billing

### Understanding Costs
- **Token-based billing**: Each interaction consumes API tokens
- **Model usage**: Claude Code CLI uses Claude AI models (pricing varies by model)
- **Rate limits**: API calls are subject to Anthropic's rate limiting

### Best Practices
- **Batch questions**: Ask multiple related questions in one session
- **Be specific**: Clear questions get better answers with fewer follow-ups  
- **Monitor usage**: Check API consumption at https://console.anthropic.com/
- **Use efficiently**: Claude Code CLI is best for complex coding assistance

### Cost Management
- **Set usage alerts**: Configure billing alerts in Anthropic console
- **Review bills**: Monitor API usage patterns  
- **Optimize queries**: Write clear, specific questions to minimize back-and-forth

## Integration with Development Workflow

### Editor Integration
Claude Code CLI complements but doesn't replace:
- **VS Code**: Use alongside Claude extensions for VS Code
- **Terminal workflow**: Great for command-line focused development
- **Code review**: Excellent for understanding unfamiliar codebases

### Development Patterns
```bash
# Code review workflow
git diff HEAD~1 | claude  # Review recent changes

# Learning new frameworks  
claude  # Ask: "Explain React hooks with examples"

# Debugging session
claude  # Paste error + code for assistance
```

### Team Usage
- **Shared API key**: Consider team API accounts for collaborative use
- **Documentation**: Use Claude to explain complex code for team members
- **Onboarding**: Help new developers understand existing codebases

## Security Considerations

### API Key Protection
- **Never commit API keys** to version control
- **Use environment variables** for API key storage
- **Rotate keys regularly** for security best practices
- **Restrict access** to API keys in team environments

### Code Privacy
- **Be cautious with proprietary code**: Claude Code CLI sends code to Anthropic's servers
- **Review terms of service**: Understand data handling policies
- **Use for learning/debugging**: Great for educational and debugging purposes
- **Consider alternatives** for highly sensitive codebases

## References

### Official Documentation
- **Claude Code CLI**: https://docs.anthropic.com/claude/docs/claude-code
- **Anthropic API**: https://docs.anthropic.com/claude/reference/
- **Anthropic Console**: https://console.anthropic.com/

### Installation Resources
- **Node.js**: https://nodejs.org/
- **Volta**: https://volta.sh/
- **npm**: https://docs.npmjs.com/

### Repository Guidelines
- **Coding Standards**: See `../../AGENTS.md`
- **Node.js Management**: See `../../bash/common/NODE_VERSION_MANAGEMENT.md`

## Changelog

### Version 1.0 (2024-10-30)
- Initial Claude Code CLI installation scripts
- Complete install/update/uninstall workflow
- Integration with repository `repo_lib.sh` utilities
- Volta/Node.js 18+ validation and setup
- Comprehensive error handling and logging  
- API key configuration guidance
- Platform detection and compatibility checks
- Detailed troubleshooting documentation

## License & Support

This tooling follows the repository license. For Claude Code CLI issues:
- **Installation problems**: Check this README's troubleshooting section
- **API/billing issues**: Contact Anthropic support via console
- **Claude Code CLI bugs**: Report to Anthropic via official channels
- **Usage questions**: Consult official Anthropic documentation

---

**Note**: Claude Code CLI requires an active Anthropic API subscription and consumes API tokens for each interaction. Monitor your usage and billing through the Anthropic console.