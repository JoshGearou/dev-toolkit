# Domain Expert Agents

Specialized agents providing deep expertise in specific languages, platforms, and tools.

## Overview

These agents serve as domain experts for specific technologies. They provide guidance, answer questions, debug issues, and recommend best practices within their area of expertise.

## Agents by Category

### Programming Languages (5)

| Agent | Expertise |
|-------|-----------|
| [python-expert](python-expert.md) | Type hints, async, pytest, mypy, Pythonic patterns |
| [golang-expert](golang-expert.md) | Goroutines, channels, interfaces, Go idioms |
| [rust-expert](rust-expert.md) | Ownership, borrowing, lifetimes, cargo |
| [java-expert](java-expert.md) | JVM, Spring, Maven/Gradle, enterprise patterns |
| [bash-expert](bash-expert.md) | Shell scripting, text processing, pipelines |

### Platforms & Operating Systems (4)

| Agent | Expertise |
|-------|-----------|
| [linux-expert](linux-expert.md) | System administration, systemd, troubleshooting |
| [macos-expert](macos-expert.md) | macOS configuration, launchd, development setup |
| [kubernetes-expert](kubernetes-expert.md) | Workloads, control plane, manifests, Helm, troubleshooting |
| [docker-expert](docker-expert.md) | Dockerfile optimization, compose, container debugging |

### Tools & Technologies (5)

| Agent | Expertise |
|-------|-----------|
| [grafana-expert](grafana-expert.md) | Dashboard design, transformations, visualizations |
| [kql-expert](kql-expert.md) | Kusto Query Language, log analysis, time series |
| [mermaid-expert](mermaid-expert.md) | Diagram generation, Lucidchart compatibility |
| [n8n-expert](n8n-expert.md) | Workflow automation, node configuration |
| [rootly-expert](rootly-expert.md) | Incident management, Slack integration |

### Security (1)

| Agent | Expertise |
|-------|-----------|
| [auth-token-expert](auth-token-expert.md) | JWT structure, claims, JWKS, key rotation, IdP integration |

## When to Use

**Use domain experts when:**
- Asking language-specific questions
- Debugging technology-specific issues
- Making architecture decisions within a domain
- Learning best practices for a tool
- Troubleshooting platform issues

**Do NOT use when:**
- Simple syntax lookup (use documentation)
- Generic programming questions (use general-purpose agent)
- Questions outside the expert's domain

## Expert Capabilities

All domain experts can:
- Answer conceptual questions
- Debug issues specific to their domain
- Recommend best practices
- Provide code examples with proper patterns
- Reference official documentation
- Search web for current information

## Example Usage

```
User: "How do I use goroutines and channels safely?"
→ Use golang-expert

User: "My Kubernetes pod is stuck in Pending"
→ Use kubernetes-expert

User: "How should I structure my Python project for mypy --strict?"
→ Use python-expert

User: "Create a sequence diagram for this API flow"
→ Use mermaid-expert

User: "How do I validate JWT claims and handle key rotation?"
→ Use auth-token-expert
```

## Related

- See [code/](../code/) for code review and fixing agents
- See [docs/](../docs/) for documentation agents
