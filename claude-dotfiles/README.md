# Claude Code Configuration and Sub-Agents

This directory contains a comprehensive Claude Code setup including custom sub-agents, configuration, scripts, and rules for enhancing your Claude Code workflow.

## What's Included

### 🤖 Sub-Agents (`agents/`)
**39 custom Claude Code agents** organized into categories:

- **Code Quality** - Code reviewers, Python/Rust fixers, PR quality analysis
- **Security** - Security reviewers, threat model analysis, secure code writers
- **Documentation** - Technical writers, doc reviewers
- **Language Experts** - Python, Rust, Bash, Go, Java, Kubernetes, Docker, Linux, macOS, and more
- **Meta Agents** - Tools to create and review other sub-agents
- **Tools** - PDF to Markdown converter
- **Communication** - Professional communication assistance

### ⚙️ Configuration (`config/`)
- `settings.json` - Claude Code settings template
- Example configurations for your environment

### 📜 Rules (`rules/`)
- `writing-style.md` - Writing style guidelines for documentation

### 🔧 Scripts (`scripts/`)
Utility scripts for Claude Code management:
- `scrub_claude_config.py` - Safely scrub secrets from config before committing
- `refresh-github-mcp.sh` - Refresh GitHub MCP server token
- `README.md` - Script documentation

### 📚 Guides (`guides/`)
Reference materials and documentation (inlined into agents during deployment)

## Quick Start

### 1. Deploy Agents to Claude Code

```bash
cd claude-dotfiles

# Preview what will be deployed
./deploy.sh --dry-run

# Deploy all general-purpose agents
./deploy.sh

# Deploy specific category
./deploy.sh --category code        # Code quality agents only
./deploy.sh --category experts     # Language expert agents only
./deploy.sh --category ssdlc       # Security agents only
```

### 2. Verify Deployment

```bash
# Check deployed agents
ls ~/.claude/agents/

# Test in Claude Code
claude code
# Type / to see available agents
# Try: /code-reviewer
```

### 3. Customize Configuration (Optional)

```bash
# Import your current Claude settings
./deploy.sh --import

# Edit as needed
vi config/settings.json

# Deploy updated settings
./deploy.sh
```

## Available Agents

### Code Quality & Review
- `/code-reviewer` - Comprehensive code quality review
- `/pr-quality-reviewer` - Analyze GitHub PR completeness
- `/python-fixer` - Fix Python mypy/flake8 issues
- `/rust-fixer` - Fix Rust clippy/formatting issues

### Security (SSDLC)
- `/security-reviewer` - Security vulnerability analysis
- `/security-writer` - Write secure code
- `/threat-model-reviewer` - Review threat models

### Documentation
- `/doc-reviewer` - Review technical docs
- `/tech-writer` - Write clear documentation

### Language Experts
- `/python-expert` - Deep Python expertise
- `/rust-expert` - Rust best practices
- `/bash-expert` - Shell scripting
- `/golang-expert` - Go programming
- `/java-expert` - Java development
- `/kubernetes-expert` - K8s administration
- `/docker-expert` - Container expertise
- `/linux-expert` - Linux systems
- `/macos-expert` - macOS systems
- `/mermaid-expert` - Diagram creation
- And 10+ more specialized experts...

### Meta Agents
- `/sub-agent-writer` - Create new sub-agents
- `/sub-agent-reviewer` - Review sub-agent quality

### Tools
- `/pdf-to-markdown` - Convert PDFs to markdown

## Directory Structure

```
claude-dotfiles/
├── README.md              # This file
├── deploy.sh              # Main deployment script
├── agents/                # Sub-agent definitions
│   ├── README.md          # Agent documentation
│   └── general/           # General-purpose agents
│       ├── code/          # Code quality agents
│       ├── docs/          # Documentation agents
│       ├── experts/       # Language experts
│       ├── meta/          # Meta agents
│       ├── ssdlc/         # Security agents
│       ├── tools/         # Tool agents
│       └── communication/ # Communication helpers
├── config/                # Claude Code configuration
│   ├── README.md
│   └── settings.json      # Settings template
├── rules/                 # Global rules
│   └── writing-style.md   # Documentation style guide
├── scripts/               # Utility scripts
│   ├── README.md
│   ├── scrub_claude_config.py
│   └── refresh-github-mcp.sh
└── guides/                # Reference documentation
```

## Usage Examples

### Reviewing Code Quality
```bash
claude code
> /code-reviewer "Review src/main.rs for quality issues"
```

### Fixing Python Code
```bash
claude code
> /python-fixer "Fix mypy and flake8 issues in src/parser.py"
```

### Security Review
```bash
claude code
> /security-reviewer "Review authentication flow in auth.py"
```

### Creating Documentation
```bash
claude code
> /tech-writer "Document the API authentication flow"
```

### Getting Language-Specific Help
```bash
claude code
> /rust-expert "How should I structure error handling for this parser?"
> /kubernetes-expert "How do I configure horizontal pod autoscaling?"
```

### Creating New Agents
```bash
claude code
> /sub-agent-writer "Create an agent that reviews Terraform code"
```

## Deployment Options

### Basic Deployment
```bash
./deploy.sh                    # Deploy everything
./deploy.sh --dry-run          # Preview changes
./deploy.sh --clean            # Clean ~/.claude and redeploy
```

### Category-Specific
```bash
./deploy.sh --category code    # Code agents only
./deploy.sh --category experts # Expert agents only
./deploy.sh --category ssdlc   # Security agents only
./deploy.sh --category docs    # Documentation agents only
```

### Configuration Management
```bash
./deploy.sh --import           # Import current settings from ~/.claude
./deploy.sh                    # Deploy settings and agents
```

## Creating Custom Agents

### Using the Sub-Agent Writer
```bash
claude code
> /sub-agent-writer "Create an agent that analyzes database schemas"
```

### Manual Creation
1. Create new file in appropriate category: `agents/general/{category}/{agent-name}.md`
2. Follow agent template structure (see `agents/README.md`)
3. Deploy: `./deploy.sh --category {category}`
4. Test: `/agent-name` in Claude Code

### Agent Template
```markdown
---
name: my-custom-agent
description: Brief one-line description
trigger: model_decision
---

# My Custom Agent

## When to Use This Agent
[Clear triggers]

## When NOT to Use This Agent
[Anti-patterns]

## Core Capabilities
[What it can do]

## Guidelines
[How it works]

## Examples
[Concrete examples]
```

## Best Practices

### Agent Usage
- **Invoke explicitly** - Use `/agent-name` for specific tasks
- **Chain agents** - Use multiple agents for complex workflows
- **Provide context** - Give agents clear, specific instructions
- **Review outputs** - Agents are assistants, not replacements for judgment

### Agent Development
- **Single responsibility** - One clear purpose per agent
- **Clear triggers** - Explicit when to use/not use
- **Include examples** - Show concrete usage patterns
- **Test thoroughly** - Validate behavior in real scenarios
- **Document limitations** - Be clear about what agent can't do

### Configuration Management
- **Version control** - Keep agents and config in git
- **Scrub secrets** - Use `scrub_claude_config.py` before committing
- **Import regularly** - Keep repo in sync with `~/.claude/`
- **Test before deploying** - Use `--dry-run` first

## Troubleshooting

### Agents Not Appearing
```bash
# Check deployment
./deploy.sh --dry-run

# Verify files
ls ~/.claude/agents/

# Redeploy
./deploy.sh --clean

# Restart Claude Code
```

### Agent Errors
- Check agent syntax (YAML frontmatter)
- Verify script paths in `agents/{category}/scripts/`
- Review Claude Code logs
- Test with `--dry-run` first

### Script Issues
```bash
# Verify script permissions
chmod +x scripts/*.sh

# Check Python dependencies
pip install -r agents/general/code/scripts/requirements.txt

# Test scripts standalone
python3 scripts/scrub_claude_config.py --help
```

## Integration with dev-toolkit

These agents work seamlessly with the dev-toolkit repository:

- **Code quality agents** work with the `src/lint/` tools
- **Language experts** understand the repository structure
- **Security agents** complement IAM research in `iam/`
- **Documentation agents** follow the style guides in this repo

## Updating Agents

### Pull Latest Changes
```bash
cd dev-toolkit
git pull origin main
cd claude-dotfiles
./deploy.sh
```

### Import Your Changes
```bash
# After modifying agents in ~/.claude/
./deploy.sh --import

# Review changes
git diff

# Commit
git add -A
git commit -m "Update agents: [description]"
```

## Related Documentation

- [Agent Creation Guide](agents/general/meta/guides/sub-agent-creation-rules.md)
- [Agent README](agents/README.md)
- [Scripts README](scripts/README.md)
- [Config README](config/README.md)
- [Writing Style Guide](rules/writing-style.md)

## Support

For questions about:
- **Agent usage** - See examples in `agents/README.md`
- **Deployment** - Run `./deploy.sh --help`
- **Creating agents** - Use `/sub-agent-writer` or see creation guide
- **Configuration** - See `config/README.md`
- **Scripts** - See `scripts/README.md`

## Contributing

To contribute new agents:
1. Create agent in `agents/general/{category}/`
2. Follow agent creation guidelines
3. Test deployment: `./deploy.sh --dry-run`
4. Validate functionality
5. Submit PR with examples

## License

These agents and configurations are part of the dev-toolkit repository. See main repository LICENSE for details.

---

**Quick Start TL;DR:**
```bash
cd claude-dotfiles
./deploy.sh --dry-run  # Preview
./deploy.sh            # Deploy all agents
# Then in Claude Code: type / to see agents
```
