# Color System for Sub-Agents

All agents must be assigned a color category for visual organization and machine-readable classification.

## Color Taxonomy

| Color | Category | Type | Examples |
|-------|----------|------|----------|
| purple | Requirements & Design | code-review | requirement-reviewer, design-reviewer |
| red | SSDLC Security | code-review | threat-model, secret-management, authz-pattern |
| blue | Code Quality | code-review | security-vulnerability, error-handling, type-safety |
| yellow | Testing | code-review | test-coverage-analyzer |
| orange | Performance | code-review | performance-reviewer |
| teal | Documentation | doc-review/content-creator | tech-writer, grammar-reviewer, documentation-reviewer |
| green | Code Fixers | code-fixer | flake8-fixer, mypy-fixer, clippy-fixer |

## Detailed Category Descriptions

### Purple - Requirements & Design
- **Focus**: Requirements validation, implementation correctness
- **Type**: code-review (read-only)
- **Examples**: requirement-reviewer, design-reviewer
- **Use when**: Validating PR requirements and design compliance

### Red - SSDLC Security
- **Focus**: Secure software development lifecycle, hyperscale security
- **Type**: code-review (read-only)
- **Examples**: threat-model, secret-management, authz-pattern
- **Use when**: Security-critical reviews, compliance, threat analysis

### Blue - Code Quality
- **Focus**: General code correctness, safety, maintainability
- **Type**: code-review (read-only)
- **Examples**: security-vulnerability, error-handling, type-safety
- **Use when**: General code quality reviews

### Yellow - Testing
- **Focus**: Test coverage, quality assurance
- **Type**: code-review (read-only)
- **Examples**: test-coverage-analyzer
- **Use when**: Analyzing test completeness

### Orange - Performance
- **Focus**: Performance optimization, anti-patterns
- **Type**: code-review (read-only)
- **Examples**: performance-reviewer
- **Use when**: Analyzing performance

### Teal - Documentation
- **Focus**: Documentation completeness, clarity, technical writing
- **Type**: doc-review (read-only) or content-creator (writes)
- **Examples**: tech-writer, grammar-reviewer, documentation-reviewer
- **Use when**: Checking docs, writing technical content

### Green - Code Fixers
- **Focus**: Automated code modification
- **Type**: code-fixer (modifies code)
- **Examples**: flake8-fixer, mypy-fixer, clippy-fixer, cargo-check-fixer
- **Use when**: Applying fixes after review

## Usage in Agent Definitions

The `color` field is required in the YAML frontmatter for all agents in this repository:

```yaml
---
name: example-agent
description: |
  When to use this agent...
tools: Read, Grep
model: sonnet
color: blue  # Required - must match a color from this taxonomy
---
```

## Validation Rules

1. **Color must be lowercase**: `blue` not `Blue`
2. **Color must match taxonomy**: Only values from the table above
3. **Color should match agent purpose**: A security reviewer should be `red`, not `green`
4. **Fixers are always green**: Any agent that modifies code is `green`
5. **Reviewers match their domain**: Use the category that best fits the review focus
