---
name: any2md
description: Universal document to Markdown converter with automatic format routing. Auto-detects DOCX math and routes to word2md; uses markitdown for PPTX/XLSX/HTML/EPUB/etc; supports PyMuPDF for high-fidelity PDF. Fixes markdownify math-escaping bugs.
---

# any2md — Universal Document to Markdown

Automatically routes to the best backend based on file format and content:

| Format | Backend | Why |
|--------|---------|-----|
| DOCX with math | `/word2md` | Correct OMML→LaTeX, no escaping bugs |
| DOCX no math | markitdown | General-purpose conversion |
| PDF | markitdown | Table-aware extraction |
| PDF (high fidelity) | PyMuPDF | `--pdf-backend pymupdf` |
| PPTX / XLSX / HTML / EPUB / etc | markitdown | Broad format support |

## When to Use

- User mentions: "any2md", "/any2md", "convert to md", "转 markdown", "万能转 md"
- User has a document of unknown type and wants Markdown output
- User wants one command that handles any format

## How to Use

```bash
PYTHONIOENCODING=utf-8 python ~/.claude/skills/any2md/any2md.py "<INPUT_FILE>" ["<OUTPUT.md>"]
```

### Arguments

| Arg | Required | Description |
|-----|----------|-------------|
| `input` | Yes | Input file path |
| `output` | No | Output .md path (default: stdout) |
| `--math` | No | `auto` (default) / `yes` / `no` — math detection |
| `--pdf-backend` | No | `markitdown` (default) / `pymupdf` |

### Examples

```bash
# Auto-detect format, print to stdout
PYTHONIOENCODING=utf-8 python ~/.claude/skills/any2md/any2md.py "document.docx"

# Convert and save
PYTHONIOENCODING=utf-8 python ~/.claude/skills/any2md/any2md.py "slides.pptx" "slides.md"

# Force math mode for DOCX
PYTHONIOENCODING=utf-8 python ~/.claude/skills/any2md/any2md.py "report.docx" "report.md" --math yes

# PDF with PyMuPDF (high fidelity, no tables)
PYTHONIOENCODING=utf-8 python ~/.claude/skills/any2md/any2md.py "paper.pdf" "paper.md" --pdf-backend pymupdf
```

## Key Features

1. **Auto math detection**: Scans DOCX for `oMath` elements; routes to `word2md` if found
2. **Math escaping fix**: Post-processes markitdown output to fix `\_` → `_` inside `$...$`
3. **Image extraction**: DOCX with math → word2md extracts images to `images/` folder
4. **PDF backends**: Choose between table-aware (markitdown) or high-fidelity text (PyMuPDF)

## Dependencies

- `markitdown` — `pip install markitdown`
- `python-docx` — for word2md backend (auto-detected)
- `PyMuPDF` (optional) — for `--pdf-backend pymupdf`

## Rules

1. **Always use `PYTHONIOENCODING=utf-8`** on Windows
2. **For DOCX with math**, this skill auto-routes to word2md — no need to call `/word2md` separately
3. **For pure PDF reading** (no conversion needed), prefer `/pdf-reader` which has 3 extraction modes
4. **For DOCX to HTML** (not Markdown), use `/word2html` instead
