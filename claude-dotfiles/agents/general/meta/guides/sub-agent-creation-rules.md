# Sub Agent Creation Rules

**Official Documentation**: [Claude Code Sub-Agents](https://code.claude.com/docs/en/sub-agents.md)

This document extends the official Claude Code documentation with additional conventions and best practices specific to this repository.

## Quick Reference

### Minimal Valid Agent (Claude Code Official)
```markdown
---
name: code-reviewer
description: Expert code review specialist. Use after writing code.
---

You are a code reviewer that ensures quality and security.
Review the code and provide actionable feedback.
```

### Complete Agent (This Repository Style)
```markdown
---
name: mypy-fixer
description: |
  Use when: 3+ mypy violations or explicit request.
  Do NOT use: Single trivial violation.
tools: Bash, Read, Edit
model: sonnet
color: blue
---

# Mypy Resolution Agent

You are a specialized agent that resolves mypy violations.

## Your Mission
Make code pass mypy --strict checks.

## Resolution Priority
1. Auto-add obvious type hints
2. Safe refactoring
3. Suppressions when needed

## Your Constraints
- You ONLY fix type errors
- You do NOT change business logic
```

### Invalid Agent (Missing Frontmatter - WON'T LOAD!)
```markdown
# Requirement Reviewer Agent

**Category**: Requirements & Design
**Color**: purple

You are a specialized agent that reviews requirements.
```

**Critical Error:** No YAML frontmatter = Claude Code won't recognize this as an agent!

## Token Budget & Consolidation-First Principle

### System Token Budget

**CRITICAL: All agent descriptions share a 15,000 token budget at Claude Code startup.**

Exceeding this budget causes performance warnings and degraded context. Every new agent consumes shared resources.

### Line Limits (Enforced)

| Section | Target | Maximum |
|---------|--------|---------|
| Description (frontmatter) | 15-25 lines | 40 lines |
| Agent body | 60-100 lines | 150 lines |
| **Total file** | 100-150 lines | **200 lines** |

### Consolidation-First Approach

**Before creating a new agent, ALWAYS check:**

1. **Search existing agents** - Does one already cover this domain?
2. **Consider extending** - Can this be a new dimension of an existing agent?
3. **Evaluate overlap** - Will this duplicate functionality?

**Prefer extending over creating:**
- Add a review dimension to `code-reviewer` instead of new `xyz-reviewer`
- Add expertise to `kubernetes-expert` instead of new `k8s-networking-expert`
- Add document type to `security-writer` instead of new `xyz-writer`

**Only create new agent when:**
- Truly distinct domain with no overlap
- Different workflow/methodology than existing agents
- Consolidation would make existing agent too broad

### What NOT to Include (Models Know This)

Models are trained on CLI tools, programming languages, and frameworks. Don't duplicate:

- ❌ kubectl, docker, git, cargo, npm command references
- ❌ Flag documentation or man pages
- ❌ Example command outputs
- ❌ Programming language syntax
- ❌ Framework API documentation

**Red flag sections:** "CLI Tools and Commands", "Command Reference", "Usage Examples"

---

## Agent Management & Resources

### Resource Consumption

**Definition Phase:**
- Agent definitions (.md files) are loaded into context at session start
- Each agent adds ~100-500 tokens (minimal cost)
- Having 10-20+ agent definitions has negligible impact

**Invocation Phase:**
- Agents run in separate contexts with clean slate
- Each invocation is a separate API call with its own token usage
- Slight latency as agent "spins up" and gathers context
- Results are returned to main conversation

**Key Insight:** Inactive agents barely consume resources. You only pay (in tokens/latency) when invoking them.

### How Many Agents Should You Create?

**No practical limit** - Create as many as make your workflow clear:
- ✅ 20+ focused agents (each invoked only when needed)
- ❌ 3 bloated multipurpose agents (constantly active)

**The cost is in delegation, not definitions.** Having 50 agent files doesn't hurt; each agent invocation does use tokens.

**Trade-off:** Agents help preserve main context for longer sessions, but each delegation adds latency and uses tokens for that specific invocation.

### Personal vs Project Agents

**Project Agents** (`agents/` in this repository)
- This repository uses `agents/` directory at the repo root
- Scoped to current project
- Version-controlled with codebase
- Shared with team members
- Highest priority when names conflict
- Use for: domain-specific knowledge, team workflows, codebase-specific automation

**Standard Claude Code Location** (`.claude/agents/`)
- Default location per Claude Code documentation
- Can be used alongside repo-specific `agents/` directory

**Personal/User Agents** (`~/.claude/agents/`)
- Available across all projects
- Personal workflow automation
- Lower priority than project agents
- Use for: general workflow patterns, personal preferences, cross-project utilities

**Example Split:**
```
Project:  agents/iam-policy-reviewer.md             # Domain-specific (this repo)
Personal: ~/.claude/agents/commit-message-writer.md # General workflow
```

### Managing Agents

**Interactive Command:**
```bash
/agents
```
Use this to view, create, edit, and delete agents through a guided interface.

**File-Based Management:**
Create `.md` files directly in `.claude/agents/` (project) or `~/.claude/agents/` (personal).

### Required File Format

**IMPORTANT:** All agent definition files MUST follow this exact structure:

```markdown
---
name: agent-name
description: |
  # When to Invoke the [Agent Name]

  ## Automatic Triggers (Always Use Agent)

  1. **[Trigger condition 1]**
     - [Specific scenario]
     - [Example user request]

  2. **[Trigger condition 2]**
     - [Specific scenario]
     - [Example user request]

  ## Do NOT Use Agent When

  ❌ **[Exclusion case 1]**
     - [When not to use]
     - [Alternative approach]

  **Summary**: [One-line summary of when to use this agent]
tools: Bash, Read, Edit, Glob, Grep  # Optional - omit to inherit all tools from parent
model: sonnet                         # Optional - sonnet/opus/haiku or 'inherit'
color: blue                           # Required - see Color Taxonomy section
---

# [Agent Name]

You are a specialized agent that [primary action verb] [domain].

## Your Mission
[One sentence goal. What does success look like?]

## [Resolution/Action] Priority
1. **[Safest action]** (apply immediately)
   - Bullet list of specific operations

2. **[Medium risk action]** (apply with confidence)
   - Bullet list of specific operations

3. **[High risk action]** (WARN FIRST)
   - Bullet list of specific operations

## Your Constraints
- You ONLY [do X] - nothing else
- You do NOT [common scope creep items]
- You [behavioral guideline]

## Output Format
Report:
- [Key metric 1]
- [Key metric 2]
- [Actions taken]
- [Final status]
```

### Frontmatter Fields Explained

#### Required Fields (Claude Code Official)

1. **`name`** (REQUIRED): Unique identifier using lowercase letters and hyphens
   - Format: kebab-case (e.g., `mypy-fixer`, `requirement-reviewer`, `code-reviewer`)
   - Must be unique across all agents in the workspace

2. **`description`** (REQUIRED): Natural language description of the agent's purpose
   - Tells Claude Code WHEN to invoke this agent
   - Should clearly indicate trigger conditions
   - Use phrases like "use PROACTIVELY" or "MUST BE USED" for autonomous invocation
   - Can be single-line or multi-line (use `|` for multi-line YAML)
   - This is shown to the main assistant, not the agent itself

#### Optional Fields (Claude Code Official)

3. **`tools`** (OPTIONAL): Comma-separated list of allowed tools
   - Examples: `Bash, Read, Edit, Glob, Grep`
   - If omitted, inherits all tools from parent/main thread
   - Restrict tools for security and focus

4. **`model`** (OPTIONAL): Model to use for this agent
   - Values: `sonnet`, `opus`, `haiku`, or `inherit`
   - Prefer `haiku` for quick, straightforward tasks to minimize cost
   - If omitted, defaults to configured subagent model
   - Use `inherit` to use the main conversation's model

#### Repository-Specific Fields (Not Claude Code Standard)

5. **`color`** (REPOSITORY CONVENTION): Category color for visual organization
   - **Note**: This is NOT part of official Claude Code specification
   - Used in this repository for agent categorization
   - Must match one from Color Taxonomy section
   - Examples: `blue`, `red`, `purple`, `green`, `orange`, `yellow`, `teal`
   - Optional in general, but required for agents in this repository

6. **`references`** (REPOSITORY CONVENTION): List of files to inline during deployment
   - **Note**: This is NOT part of official Claude Code specification
   - Used by `deploy_agents.sh` to inline reference documents into agents
   - Files are appended to the end of the deployed agent under "# Inlined Reference Materials"
   - The `references:` field is stripped from the deployed frontmatter
   - Paths are relative to the `agents/` directory
   - Example:
     ```yaml
     references:
       - agents/meta/guides/sub-agent-creation-rules.md
       - agents/talent/guides/FY26_Mid-Year_Reviews_Guide.md
     ```
   - Reference files should be placed in a `guides/` subdirectory of the agent's category

### Critical: Two-Part Structure

Agent definition files have TWO distinct sections with different audiences:

**Part 1: YAML Frontmatter (between `---` delimiters)**
- **Audience:** Main Claude Code assistant
- **Purpose:** Decides WHEN to invoke this agent
- **Content:** The `description` field contains invocation rules, trigger conditions, and usage examples
- **Format:** Multi-line YAML string with markdown formatting
- **Key point:** This is NOT shown to the agent itself - it's for autonomous invocation decisions

**Part 2: Agent Prompt Body (after closing `---`)**
- **Audience:** The agent subprocess itself
- **Purpose:** Instructions for HOW the agent should operate once invoked
- **Content:** Mission statement, action priorities, constraints, output format
- **Format:** Standard markdown with clear sections
- **Key point:** This is what the agent receives as its system prompt

**Example of the distinction:**

**Approach 1: Simple natural language (official docs style)**
```markdown
---
name: code-reviewer
description: Expert code review specialist. Use PROACTIVELY after writing significant code changes.
tools: Read, Grep, Bash
---

You are a senior code reviewer ensuring high standards...
[This tells the AGENT what to do once invoked]
```

**Approach 2: Structured markdown (extended style used in this repo)**
```markdown
---
name: mypy-fixer
description: |
  # When to Invoke the Mypy Fixer

  ## Automatic Triggers (Always Use Agent)
  1. User explicitly requests mypy work
  2. Multiple mypy violations detected (3+)

  ## Do NOT Use Agent When
  ❌ Single trivial violation - fix directly

  **Summary**: Use for batch resolution of type errors
tools: Bash, Read, Edit
color: blue
---

# Mypy Resolution Agent

You are a specialized agent that resolves mypy violations...
[This tells the AGENT what to do once invoked]
```

**Both approaches work** - the key is that the description helps the main assistant decide WHEN to invoke, and the prompt body tells the agent HOW to operate.

**Common Mistake:** Putting agent instructions in the frontmatter or invocation rules in the body. These are separate and serve different purposes.

**Priority Resolution:** Project agents override personal agents when names match.

**Tool Access:** Grant only necessary tools for security and focus. Omit `tools` field to inherit all tools.

## Google Docs Compatibility

**All documentation-producing agents must format markdown for Google Docs compatibility.** Documents are frequently converted to Google Docs.

**Key rules:**
- Use markdown headings (`#`, `##`) or **bold headers** followed by blank line, then description
- Avoid indentation-based formatting (Google Docs ignores leading spaces)
- Use blank lines between sections (not indentation)
- Prefer numbered/bulleted lists over indented blocks

**Applies to:** tech-writer, threat-model-writer, security-design-writer, functional-nonfunctional-requirements-writer, security-requirements-writer, negotiation-writer, and any agent that produces markdown documents.

## Core Principles

  1. **Single Responsibility**
     - Agent does ONE thing extremely well
     - No feature creep or scope expansion
     - Clearly name what the agent resolves/handles

  2. **Action-Oriented**
     - Agents should DO, not just report
     - Prioritize fixes/resolutions over analysis
     - Default to making changes, not suggesting them

  3. **Pragmatic Decision-Making**
     - Provide clear priority ordering for decisions
     - Embrace practical solutions (like suppressions)
     - Balance purity with getting things done

  4. **Safety Boundaries**
     - Distinguish safe vs unsafe operations explicitly
     - Auto-apply safe operations
     - WARN before unsafe operations (don't block, just warn)
     - Define what "safe" means for the domain

  5. **Generic Over Specific**
     - Avoid repo-specific paths or tooling
     - Work with standard tools/conventions
     - Portable across projects/contexts

  6. **Clear Constraints**
     - List what agent does NOT do
     - Prevent scope creep
     - Keep agent focused on mission

  ## Color Coding (Agent Categories)

All agents must be assigned a color category. See `agents/meta/guides/color-system.md` for the complete color taxonomy and validation rules.

  ## Prompt Structure

  ```markdown
  # [Tool/Domain] [Action] Agent

  **Category**: [Category Name]
  **Color**: [color]
  **Type**: [code-review | code-fixer]

  You are a specialized agent that [primary action verb] [domain].

  ## Your Mission
  [One sentence goal. What does success look like?]

  ## [Resolution/Action] Priority
  1. **[Safest action]** (apply immediately)
     - Bullet list of specific operations

  2. **[Medium risk action]** (apply with confidence)
     - Bullet list of specific operations

  3. **[High risk action]** (WARN FIRST)
     - Bullet list of specific operations

  4. **[Fallback/exception handling]**
     - When and how to handle edge cases

  ## Your Constraints
  - You ONLY [do X] - nothing else
  - You do NOT [common scope creep items]
  - You [behavioral guideline]

  ## Output Format
  Report:
  - [Key metric 1]
  - [Key metric 2]
  - [Actions taken]
  - [Final status]

  ## Post-Completion Review (Optional)
  [For writer/fixer agents that benefit from quality checks]

  After completing [action], invoke **[critic-agent-name]** for feedback.

  **Review workflow:**
  1. Complete the [artifact] draft
  2. Invoke [critic-agent-name]
  3. Review critic feedback against rules R1-RN
  4. Update [artifact] based on valid concerns
  5. You have final say - dismiss feedback that conflicts with user requirements

  **When responding to critic:**
  - Accept feedback about [valid concern types]
  - Dismiss feedback that [invalid concern types]
  - Note any dismissed feedback and reasoning in final output
  ```

  ## Post-Completion Review Pattern (Advanced)

  For agents that produce artifacts (writers, fixers), consider adding a Post-Completion Review section that invokes a paired reviewer agent. This creates a writer→reviewer workflow that improves quality.

  ### When to Use This Pattern

  - **Writer agents** that produce documents (threat models, communications, designs)
  - **Fixer agents** that make significant code changes
  - When automated quality feedback improves the output

  ### Pattern Structure

  Add this section after "Output Format" in the agent prompt body:

  ```markdown
  ## Post-Completion Review

  After completing [the artifact], invoke **[reviewer-agent-name]** for feedback.

  **Review workflow:**
  1. Complete the [artifact] draft
  2. Invoke [reviewer-agent-name]
  3. Review critic feedback against rules R1-RN (list specific rules)
  4. Update [artifact] based on valid concerns
  5. You have final say - dismiss feedback that conflicts with user requirements or scope

  **When responding to critic:**
  - Accept feedback about [specific valid concerns]
  - Accept feedback about [another valid concern type]
  - Dismiss feedback that [over-complicates / expands scope / conflicts with user style]
  - Note any dismissed feedback and reasoning in final output
  ```

  ### Key Principles

  1. **Agent Autonomy**: The writer/fixer has final say, not the reviewer
  2. **Selective Acceptance**: Define which feedback types to accept vs dismiss
  3. **Transparency**: Document dismissed feedback and reasoning
  4. **Scope Protection**: Dismiss feedback that expands beyond original request

  ### Example Pairings

  | Writer/Fixer Agent | Paired Reviewer |
  |-------------------|-----------------|
  | threat-model-writer | threat-model-doc-reviewer |
  | negotiation-writer | negotiation-reviewer |
  | flake8-fixer | error-handling-reviewer (if exception handling changed) |
  | security-design-writer | security-design-doc-reviewer |

  ## File Format Validation Checklist

  Before finalizing an agent definition file, verify:

  ### Structural Requirements ✅ (Claude Code Official)
  - [ ] File has YAML frontmatter delimited by `---` at start and end
  - [ ] `name` field present in frontmatter (kebab-case, unique)
  - [ ] `description` field present in frontmatter (explains WHEN to invoke)
  - [ ] Agent prompt body exists AFTER closing `---`
  - [ ] Frontmatter and body serve different purposes (invocation vs operation)

  ### Repository-Specific Requirements ✅ (This Repo)
  - [ ] `color` field present in frontmatter (matches Color Taxonomy)
  - [ ] Description uses structured markdown format (extended style)

  ### Description Field (Invocation Rules) ✅
  - [ ] Contains "When to Invoke" or similar section
  - [ ] Lists automatic trigger conditions (numbered list)
  - [ ] Lists exclusion cases ("Do NOT Use When")
  - [ ] Includes usage examples or decision tree
  - [ ] Has one-line summary at the end
  - [ ] Uses markdown formatting (headers, lists, code blocks)

  ### Agent Prompt Body ✅
  - [ ] Starts with "You are a specialized agent that..."
  - [ ] Has clear Mission section (one sentence goal)
  - [ ] Has numbered Priority/Resolution section
  - [ ] Has Constraints section with 3+ "do NOT" items
  - [ ] Has Output Format section
  - [ ] Safe operations are auto-applied
  - [ ] Unsafe operations trigger warnings (not blocks)
  - [ ] (Optional) Post-Completion Review section for writer/fixer agents

  ### Content Quality ✅
  - [ ] Agent has single, clear purpose
  - [ ] No repo-specific paths or tools
  - [ ] Priorities are numbered and clear
  - [ ] Agent is action-oriented (fixes/applies, not just suggests)
  - [ ] Pragmatic fallbacks exist (suppressions, workarounds)

  ### Common Validation Errors ❌

  **CRITICAL ERRORS (Agent Won't Load):**
  - ❌ **Missing frontmatter entirely** - File starts with `#` instead of `---`
    - Example: `# Requirement Reviewer Agent` at line 1
    - **This is the #1 most common error** - Claude Code won't recognize the file
  - ❌ **No `name` field** in frontmatter
  - ❌ **No `description` field** in frontmatter
  - ❌ **Unclosed frontmatter** - Missing closing `---`

  **Configuration Errors (Agent Won't Work Correctly):**
  - ⚠️ **Invocation rules in body instead of `description` field**
    - The body should contain agent instructions, not invocation rules
  - ⚠️ **Agent instructions in `description` instead of body**
    - The description should explain WHEN to invoke, not HOW to operate
  - ⚠️ **Single-line `description` for complex agents**
    - Use `|` for multi-line YAML strings when needed

  **Repository-Specific Errors (This Repo):**
  - ⚠️ **No `color` field** in frontmatter (required for this repo's organization)
  - ⚠️ **Invalid color value** - Must match Color Taxonomy section

  Anti-Patterns to Avoid

  ❌ Too broad: "You handle code quality"✅ Focused: "You resolve flake8 violations"

  ❌ Analysis-focused: "You identify and report issues"✅ Action-focused: "You fix issues and make code pass checks"

  ❌ Vague safety: "Be careful with changes"✅ Explicit safety: "Auto-fix whitespace. WARN before changing logic."

  ❌ Repo-specific: "Use ./scripts/lint.sh"✅ Generic: "Use flake8 with project configuration"

  ❌ No escape hatch: "Fix all violations"✅ Pragmatic: "Fix or suppress violations to achieve clean status"

  Example Agent Ideas

  - Import Resolution Agent: Fixes missing/unused imports, organizes import blocks
  - Type Annotation Agent: Adds/fixes type hints for mypy compliance
  - Test Coverage Agent: Identifies untested code, generates test stubs
  - Dependency Update Agent: Updates dependencies, tests for breakage
  - Documentation Agent: Generates/fixes docstrings for functions/classes
  - Security Fix Agent: Resolves security scanner violations (Bandit, etc.)