# Meta Agents

Agents for creating and reviewing other agents.

## Overview

Meta agents help maintain and extend the agent library itself. They ensure new agents follow conventions and best practices.

## Agents

| Agent | Type | Purpose |
|-------|------|---------|
| [sub-agent-writer](sub-agent-writer.md) | Content Creator | Creates new agent definitions |
| [sub-agent-reviewer](sub-agent-reviewer.md) | Reviewer | Reviews agent definitions for quality |

## Guides

| Guide | Purpose |
|-------|---------|
| [guides/sub-agent-creation-rules.md](guides/sub-agent-creation-rules.md) | Complete rules for creating agents |
| [guides/color-system.md](guides/color-system.md) | Agent color taxonomy |

## Workflow

### Creating a New Agent

1. **Plan** - Identify the gap in existing agents
2. **Check existing** - Review similar agents for patterns
3. **Write** - Use sub-agent-writer to create definition
4. **Review** - Use sub-agent-reviewer to validate
5. **Place** - Put in appropriate category folder

### Required Agent Structure

```markdown
---
name: {kebab-case-name}
description: |
  # When to Invoke the {Agent Name}
  ## Automatic Triggers (Always Use Agent)
  ...
  ## Do NOT Use Agent When
  ...
  **Summary**: {one-line summary}
tools: {Tool1, Tool2}
model: {sonnet|haiku|opus}
color: {color}
---

# {Agent Name}

**Category**: {Category}
**Type**: {code-review|code-fixer|content-creator|doc-review}

You are a specialized agent that {primary action verb} {domain}.

## Your Mission
...

## Your Constraints
...

## Output Format
...
```

## Agent Categories & Colors

| Category | Color | Folder | Purpose |
|----------|-------|--------|---------|
| Requirements & Design | Purple | ssdlc/ | Validate requirements |
| SSDLC Security | Red | ssdlc/ | Security lifecycle |
| Code Quality | Blue | code/ | Code analysis |
| Testing | Yellow | code/ | Test coverage |
| Performance | Orange | code/ | Performance analysis |
| Documentation | Teal | docs/ | Documentation |
| Experts | Blue | experts/ | Domain expertise |
| Communication | Purple | communication/ | Human communication |
| Meta | Teal | meta/ | Agent tooling |
| Tools | Teal | tools/ | Utilities |

## Core Principles

1. **Single Responsibility** - One agent does one thing well
2. **Action-Oriented** - Agents do, not just report
3. **Clear Triggers** - Description explains WHEN to invoke
4. **Safety Boundaries** - Distinguish safe vs unsafe operations
5. **Generic** - Portable across projects

## Related

- See [sub-agent-creation-rules.md](guides/sub-agent-creation-rules.md) for complete guidelines
- See other category folders for example agents
