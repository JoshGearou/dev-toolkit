# Documentation Agents

Agents for creating and reviewing technical documentation.

## Overview

These agents cover the documentation lifecycle - writing technical content and reviewing it across multiple quality dimensions.

## Agents

| Agent | Type | Purpose |
|-------|------|---------|
| [tech-writer](tech-writer.md) | Writer | Creates READMEs, ADRs, runbooks, API references |
| [doc-reviewer](doc-reviewer.md) | Reviewer | Comprehensive review across 7 quality dimensions |

## Doc Reviewer Dimensions

The consolidated doc-reviewer covers:

| Dimension | Focus |
|-----------|-------|
| **Accuracy** | Documentation matches code behavior |
| **Structure** | Organization, headings, scannability |
| **Completeness** | Missing sections, documentation gaps |
| **Grammar** | Spelling, punctuation, mechanics |
| **Audience** | Reader knowledge level assumptions |
| **Consistency** | Terminology and style uniformity |
| **Actionability** | Instructions are followable with expected outputs |

## Document Types

Tech-writer creates:

- **README** - Project quick start and overview
- **ADR** - Architecture Decision Records
- **Runbook** - Operational procedures with verification steps
- **API Reference** - Endpoint documentation with examples
- **Setup Guide** - Installation and configuration steps

## Workflow

### Writing Documentation
```
1. Use tech-writer to create initial draft
2. Run doc-reviewer for comprehensive feedback
3. Address findings by priority
4. Iterate until quality threshold met
```

### Reviewing Documentation
```
1. Run doc-reviewer with specific focus areas
2. Review by dimension (accuracy first, then structure, etc.)
3. Provide feedback or request changes
```

## Google Docs Compatibility

All agents follow Google Docs markdown guidelines:

- Use headings (`#`, `##`) or **bold headers** with blank lines
- Avoid indentation-based formatting
- Prefer lists over indented blocks
- Use tables for structured data

## Related

- See [code/](../code/) for code review agents
- See [ssdlc/](../ssdlc/) for security documentation
- See [experts/](../experts/) for domain expertise
