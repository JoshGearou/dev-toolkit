# Claude Code Sub-Agents

This directory contains custom sub-agent definitions for Claude Code, organized by profile and category.

## Directory Structure

```
agents/
├── <profile>/            # Profile directory (e.g., general)
│   ├── <category>/       # Category directory (e.g., code, docs, experts)
│   │   ├── agent.md      # Agent definition
│   │   ├── scripts/      # Agent-specific scripts and tools
│   │   └── guides/       # Reference docs (inlined during deploy)
│   └── README.md         # Profile-specific documentation
└── README.md             # This file
```

## Profiles

Agents are organized into **profiles** (top-level directories). Each profile contains categories of related agents. See individual profile READMEs for details:

- [`general/`](general/) - General-purpose agents usable anywhere (default profile)

## Available Agent Categories

### Code Quality & Review
- **code-reviewer** - Reviews code for quality, patterns, and best practices
- **pr-quality-reviewer** - Analyzes GitHub PR quality and completeness
- **python-fixer** - Fixes Python code quality issues (mypy, flake8)
- **rust-fixer** - Fixes Rust code issues (clippy, formatting)

### Security (SSDLC)
- **security-reviewer** - Reviews code for security vulnerabilities
- **security-writer** - Writes secure code following best practices
- **threat-model-reviewer** - Reviews threat models for completeness

### Documentation
- **doc-reviewer** - Reviews technical documentation for clarity
- **tech-writer** - Writes clear, comprehensive technical documentation

### Language Experts
- **python-expert** - Deep Python expertise
- **rust-expert** - Deep Rust expertise
- **bash-expert** - Shell scripting expertise
- **golang-expert** - Go language expertise
- **java-expert** - Java expertise
- **kubernetes-expert** - Kubernetes expertise
- **docker-expert** - Docker and containerization
- **linux-expert** - Linux systems expertise
- **macos-expert** - macOS systems expertise
- **mermaid-expert** - Mermaid diagram creation
- And more...

### Meta Agents
- **sub-agent-writer** - Creates new Claude sub-agents
- **sub-agent-reviewer** - Reviews sub-agent definitions

### Tools
- **pdf-to-markdown** - Converts PDF files to markdown

### Communication
- **communication** - Helps with professional communication

## Deploying Agents

```bash
# Preview deployment (default: general profile)
./deploy.sh --dry-run

# Deploy general profile agents
./deploy.sh

# Clean and deploy fresh
./deploy.sh --clean

# Deploy specific category within profile
./deploy.sh --category code
./deploy.sh --category experts

# Import current settings from ~/.claude
./deploy.sh --import
```

**Note:** Claude Code requires flat structure. The deployment script automatically adds profile and category prefixes (e.g., `general-code-code-reviewer.md`, `general-experts-python-expert.md`).

## Creating New Agents

Use the **sub-agent-writer** agent (`/sub-agent-writer` in Claude Code) or follow `general/meta/guides/sub-agent-creation-rules.md`:

### Key Principles
1. **Single responsibility** - One clear purpose per agent
2. **Action-oriented** - DO, not just report
3. **Clear triggers** - When to invoke vs when not to
4. **Safety boundaries** - Safe vs unsafe operations
5. **Pragmatic** - Include fallbacks and escape hatches

### Agent Structure
```markdown
---
name: agent-name
description: Brief one-line description
trigger: model_decision
---

# Agent Name

Brief overview of what this agent does.

## When to Use This Agent

Clear triggers for when this agent should be invoked.

## When NOT to Use This Agent

Explicit anti-patterns or situations to avoid.

## Core Capabilities

What this agent can do.

## Guidelines

How this agent should approach tasks.

## Examples

Concrete examples of agent usage.
```

## Agent Naming Convention

Agents are deployed with prefixed names:
- Format: `{profile}-{category}-{agent-name}`
- Example: `general-code-code-reviewer.md`
- Invocation in Claude: `/code-reviewer` (prefix stripped in UI)

## Testing Agents

After deploying:
1. Open Claude Code CLI or Web
2. Type `/` to see available agents
3. Test with: `/agent-name "test description"`
4. Verify agent behavior matches expectations

## Best Practices

- **Keep agents focused** - Single responsibility
- **Make triggers explicit** - Clear when to use/not use
- **Include examples** - Show concrete usage
- **Document limitations** - What agent cannot do
- **Test thoroughly** - Validate in real scenarios
- **Version control** - Track changes, use meaningful commits

## Guides and References

Agents can reference guide files that get inlined during deployment:
- Place guides in `{category}/guides/` directory
- Reference in agent frontmatter: `references: [guides/example.md]`
- Guides are automatically included in deployed agent

## Scripts and Tools

Agents can include executable scripts:
- Place scripts in `{category}/scripts/` directory
- Scripts are deployed to `~/.claude/scripts/`
- Agents can invoke scripts via bash commands
- Include `requirements.txt` for Python dependencies

## Troubleshooting

**Agents not appearing:**
- Run `./deploy.sh --dry-run` to preview
- Check `~/.claude/agents/` for deployed files
- Restart Claude Code after deployment

**Agent errors:**
- Check agent syntax and frontmatter
- Verify script paths and permissions
- Review Claude Code logs for details

**Import/export issues:**
- Use `./deploy.sh --import` to pull from `~/.claude/`
- Use `./deploy.sh` to push to `~/.claude/`
- Never manually edit `~/.claude.json` (use scrub script)

## Related Documentation

- `../config/README.md` - Claude Code configuration
- `../scripts/README.md` - Utility scripts
- `../rules/README.md` - Global rules and guidelines
- `general/meta/guides/sub-agent-creation-rules.md` - Agent creation guide
