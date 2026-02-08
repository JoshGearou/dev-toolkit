# Tool Agents

Utility agents for file conversion and processing tasks.

## Overview

These agents perform specific utility tasks like file format conversion. They execute scripts and tools to transform content.

## Agents

| Agent | Purpose |
|-------|---------|
| [pdf-to-markdown](pdf-to-markdown.md) | Converts PDF files to clean markdown |

## Scripts

| Script | Purpose |
|--------|---------|
| [scripts/pdf_to_markdown.py](scripts/pdf_to_markdown.py) | Python script using pymupdf4llm for PDF conversion |

## PDF to Markdown

### When to Use

- Converting PDF documents to markdown format
- Extracting text from PDFs for editing
- Batch conversion of PDF directories

### Workflow

1. **Convert** - Run pymupdf4llm on PDF file
2. **Read** - Check generated markdown
3. **Reformat** - Clean up spacing, headers, lists
4. **Write** - Save cleaned markdown

### Formatting Applied

- Maximum 2 consecutive blank lines
- Proper header hierarchy
- Consistent list formatting
- Code block fencing
- Trailing whitespace removal

### Example

```bash
# Convert single PDF
.venv/bin/python tools/scripts/pdf_to_markdown.py /path/to/document.pdf

# Output: /path/to/document.md
```

## Adding New Tools

Tool agents should:
1. Wrap existing scripts or binaries
2. Handle errors gracefully
3. Report clear status on completion
4. Support both single items and batches where applicable

## Related

- See [docs/](../docs/) for documentation agents
- See [experts/](../experts/) for domain-specific help
