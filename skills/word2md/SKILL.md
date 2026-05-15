---
name: word2md
description: Convert Word (.docx) files with Office Math formulas to clean Markdown with LaTeX. Handles OMML to LaTeX conversion, Greek letters, subscripts, superscripts, fractions, and display/inline math.
---

# Word to Markdown Converter

Convert Word (.docx) files containing Office Math (OMML) formulas to clean Markdown with LaTeX math.

## When to Use

- User says "convert docx to md", "word to markdown", "word2md"
- User provides a `.docx` file and wants it in Markdown format
- User needs to extract math formulas from Word documents

## How to Use

```bash
PYTHONIOENCODING=utf-8 python ~/.claude/skills/word2md/word2md.py "<input.docx>" ["<output.md>"]
```

- **input.docx** (required): Path to the Word file
- **output.md** (optional): Output file path. If omitted, prints to stdout

### Examples

```bash
# Convert and print to stdout
PYTHONIOENCODING=utf-8 python ~/.claude/skills/word2md/word2md.py "document.docx"

# Convert and save to file
PYTHONIOENCODING=utf-8 python ~/.claude/skills/word2md/word2md.py "document.docx" "output.md"
```

## Features

- **OMML to LaTeX**: Converts Office Math XML elements (subscripts, superscripts, fractions, square roots, delimiters, sums/integrals, accents, limits, functions)
- **Unicode to LaTeX**: Greek letters (alpha, beta, sigma...) and math symbols (geq, times, circ...)
- **Display vs inline math**: `oMathPara` produces `$$...$$`, `oMath` produces `$...$`
- **Post-processing**: Cleans up delimiter issues, fixes command spacing, bold headers

## Dependencies

- `python-docx` must be installed: `python -m pip install python-docx`
