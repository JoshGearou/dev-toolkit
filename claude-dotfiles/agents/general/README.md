# General Profile Agents

General-purpose agents usable in any context. This is the default profile.

## Directory Structure

```
general/
├── code/             # Code fixers and reviewers
├── communication/    # Human communication
├── docs/             # Documentation writers and reviewers
├── experts/          # Language and domain experts
├── meta/             # Agents about agents
│   └── guides/       # Meta agent reference docs (inlined during deploy)
├── ssdlc/            # Security lifecycle (writers and reviewers)
└── tools/            # Utility agents
```

## Categories

| Category | Description | Agent Count |
|----------|-------------|-------------|
| [code/](code/) | Code fixers and reviewers | 3 |
| [communication/](communication/) | Human communication | 1 |
| [docs/](docs/) | Documentation writers and reviewers | 2 |
| [experts/](experts/) | Language and domain experts | 15 |
| [meta/](meta/) | Agents about agents | 2 |
| [ssdlc/](ssdlc/) | Secure Software Development Lifecycle | 3 |
| [tools/](tools/) | Utility agents | 1 |

**Total: 27 agents**

## Agent Details

### code/ (3 agents)

| Agent | Purpose |
|-------|---------|
| **code-reviewer** | Comprehensive code review (performance, security, concurrency, errors, resources, APIs, tests, types) |
| **python-fixer** | Fixes mypy type errors and flake8 violations |
| **rust-fixer** | Fixes cargo check errors and clippy warnings |

### docs/ (2 agents)

| Agent | Purpose |
|-------|---------|
| **doc-reviewer** | Comprehensive doc review (accuracy, structure, completeness, grammar, audience, consistency, actionability) |
| **tech-writer** | Creates READMEs, ADRs, runbooks, API references |

### ssdlc/ (3 agents)

| Agent | Purpose |
|-------|---------|
| **security-reviewer** | Reviews code for security (authorization, secrets, privacy, blast radius, telemetry, threat models, designs, requirements) |
| **security-writer** | Creates threat models, security designs, requirements documents |
| **threat-model-reviewer** | Reviews code against existing threat models |

### experts/ (15 agents)

**Languages:** bash, golang, java, python, rust

**Platforms:** docker, kubernetes, linux, macos

**Tools:** grafana, kql, mermaid, n8n, rootly

**Security:** auth-token (JWT/JWKS)

### communication/ (1 agent)

| Agent | Purpose |
|-------|---------|
| **communication** | Writes and reviews workplace communications (negotiations, Slack posts) using tactical empathy |

### meta/ (2 agents)

| Agent | Purpose |
|-------|---------|
| **sub-agent-writer** | Creates new agents following rules |
| **sub-agent-reviewer** | Reviews agent definitions |

### tools/ (1 agent)

| Agent | Purpose |
|-------|---------|
| **pdf-to-markdown** | Converts PDF files to markdown |

## Deploying

```bash
# Deploy general profile (default)
../deploy_agents.sh

# Clean deploy (remove old agents first)
../deploy_agents.sh --clean

# Preview deployment
../deploy_agents.sh --dry-run
```

## Quick Reference

| Need | Agent |
|------|-------|
| Review code quality | code-reviewer |
| Fix Python lint/types | python-fixer |
| Fix Rust build/lint | rust-fixer |
| Write docs | tech-writer |
| Review docs | doc-reviewer |
| Security code review | security-reviewer |
| Create threat model | security-writer |
| Write negotiation email | communication |
| Create new agent | sub-agent-writer |
