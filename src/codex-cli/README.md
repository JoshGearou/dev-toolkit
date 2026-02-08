# OpenAI Codex CLI - Deprecated

## Current Status

**OpenAI Codex CLI**: As of October 2025, OpenAI has **deprecated** the standalone Codex CLI tool in favor of integrating code generation capabilities into GPT-4 and other models. The original Codex API and dedicated CLI tools are no longer actively maintained or recommended by OpenAI.

## Historical Installation Page (Reference Only)

Original Codex CLI reference (now deprecated): https://developers.openai.com/codex/cli/

Retained here for historical context. New development should use one of the actively maintained official tools listed below.

## Official Alternative AI Coding Tools

Instead of using deprecated community alternatives, we recommend these **official AI coding tools** from major technology companies that are actively maintained and supported:

### 1. GitHub Copilot CLI (Microsoft/GitHub)
- **Status**: ✅ **Official** - Actively maintained by Microsoft/GitHub
- **Installation**: See [`../copilot/README.md`](../copilot/README.md)
- **Features**:
  - Command suggestions and explanations
  - Integrated with GitHub ecosystem
  - No additional API key needed (uses GitHub auth)
  - Enterprise support available

### 2. Claude Code CLI (Anthropic)
- **Status**: ✅ **Official** - Actively maintained by Anthropic
- **Installation**: See [`../claude-cli/README.md`](../claude-cli/README.md)
- **Features**:
  - Anthropic's Claude AI for coding tasks
  - Interactive coding sessions
  - Advanced reasoning capabilities
  - Enterprise-grade AI model

### 3. Google Gemini CLI (Google)
- **Status**: ✅ **Official** - Part of Google Cloud SDK
- **Installation**: See [`../gemini-cli/README.md`](../gemini-cli/README.md)
- **Features**:
  - Google's latest AI technology
  - Integrated with Google Cloud Platform
  - Multi-modal capabilities
  - Enterprise support via Google Cloud

### 4. Cursor CLI (Cursor)
- **Status**: ✅ **Official** - Part of Cursor IDE
- **Installation**: See [`../cursor-cli/README.md`](../cursor-cli/README.md)
- **Features**:
  - Full IDE with AI integration
  - Advanced code completion
  - AI-powered refactoring
  - Professional development environment

## Installation

All official AI coding tools are implemented in this repository with automated installation scripts:

```bash
# GitHub Copilot CLI (recommended for most users)
cd ../copilot && ./install_copilot_cli.sh

# Claude Code CLI (excellent for complex reasoning)
cd ../claude-cli && ./install_claude_cli.sh

# Google Gemini CLI (Google ecosystem integration)
cd ../gemini-cli && ./install_gemini_cli.sh

# Cursor CLI (full IDE experience)
cd ../cursor-cli && ./install_cursor_cli.sh
```

## API Key Requirements

The official AI coding tools have different authentication requirements:

### GitHub Copilot CLI ✅ **No API key needed**
```bash
# Uses GitHub authentication
gh auth login
gh copilot auth
```

### Claude Code CLI
```bash
# Get key from: https://console.anthropic.com/
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.zshrc
```

### Google Gemini CLI
```bash
# Uses Google Cloud authentication
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Cursor CLI ✅ **No API key needed**
```bash
# Built into Cursor IDE - no separate authentication required
```

## Usage Examples

### GitHub Copilot CLI
```bash
# Get command suggestions
gh copilot suggest "list all files in current directory"

# Explain existing commands
gh copilot explain "tar -xzf archive.tar.gz"
```

### Claude Code CLI
```bash
# Interactive coding session
claude

# Get help
claude --help
```

### Google Gemini CLI
```bash
# Code suggestions (via gcloud)
gcloud gemini code-assist suggest --help
```

### Cursor CLI
```bash
# Open files in Cursor IDE
cursor myfile.py
cursor /path/to/project
```

## Comparison of Official AI Coding Tools

| Feature | GitHub Copilot CLI | Claude Code CLI | Google Gemini CLI | Cursor CLI |
|---------|-------------------|-----------------|-------------------|------------|
| **Company** | Microsoft/GitHub | Anthropic | Google | Cursor |
| **API Key Required** | ❌ | ✅ | ✅ (GCP) | ❌ |
| **Code Generation** | ✅ | ✅ | ✅ | ✅ |
| **Command Explanation** | ✅ | ✅ | ✅ | ✅ |
| **Interactive Mode** | ❌ | ✅ | ✅ | ✅ (IDE) |
| **Multi-language** | ✅ | ✅ | ✅ | ✅ |
| **Enterprise Support** | ✅ | ✅ | ✅ | ✅ |
| **Offline Capability** | ❌ | ❌ | ❌ | Partial |
| **Best For** | GitHub integration | Complex reasoning | Google ecosystem | Full IDE experience |

## Recommended Choice by Use Case

1. **Beginners & GitHub Users**: **GitHub Copilot CLI** - No API key needed, excellent integration
2. **Advanced Reasoning & Analysis**: **Claude Code CLI** - Best AI reasoning capabilities  
3. **Google Cloud Users**: **Google Gemini CLI** - Seamless GCP integration
4. **Full Development Environment**: **Cursor CLI** - Complete IDE with AI features

## Migration from Codex

If you were previously using OpenAI Codex CLI, here are the official migration paths:

### Old Codex Workflow:
```bash
codex generate "python function to sort dictionary"
```

### New Workflow with GitHub Copilot:
```bash
gh copilot suggest "create python function to sort dictionary"
```

### New Workflow with Claude:
```bash
claude
# Interactive: "create a python function to sort dictionary"
```

### New Workflow with Cursor:
```bash
cursor myfile.py
# Use AI features within the IDE
```

## Why Official Tools Only?

We focus on **official AI coding tools** from major technology companies because they offer:

- ✅ **Enterprise Support** - Professional support and SLAs
- ✅ **Active Maintenance** - Regular updates and security patches  
- ✅ **Integration Quality** - Seamless integration with existing workflows
- ✅ **Reliability** - Backed by major technology companies
- ✅ **Security** - Enterprise-grade security and compliance
- ✅ **Longevity** - Less likely to be discontinued or abandoned

## Official Documentation

- **GitHub Copilot CLI**: https://docs.github.com/en/copilot/github-copilot-in-the-cli
- **Claude Code CLI**: https://docs.anthropic.com/claude/docs/claude-code
- **Google Gemini CLI**: https://cloud.google.com/gemini/docs/codeassist
- **Cursor IDE**: https://cursor.com/
- **Anthropic Console**: https://console.anthropic.com/
- **Google Cloud Console**: https://console.cloud.google.com/

---

**Note**: This document explains why OpenAI Codex CLI was deprecated and provides official alternatives from major technology companies. We focus exclusively on official tools that are actively maintained and supported by their respective companies.

**Last Updated**: October 30, 2025