---
name: word2html
description: Convert Word (.docx) files to standalone HTML with tables, images, and math formulas. Handles merged cells (colspan/rowspan), embedded images, bold/italic/underline, and OMML math via MathJax.
---

# Word to HTML Converter

Convert Word (.docx) files to a self-contained HTML page with proper table rendering, images, and math formulas.

## When to Use

- User says "word2html", "docx转html", "word to html"
- User needs to view/docx content in a browser-friendly format
- User wants to preserve tables with merged cells and embedded images

## How to Use

```bash
python ~/.claude/skills/word2html/word2html.py "<input.docx>" ["<output.html>"]
```

- **input.docx** (required): Path to the Word file
- **output.html** (optional): Output file path. Defaults to same name with `.html` extension

### Examples

```bash
# Convert (output = input_name.html)
python ~/.claude/skills/word2html/word2html.py "document.docx"

# Convert with specific output path
python ~/.claude/skills/word2html/word2html.py "document.docx" "output.html"
```

## Features

| Feature | Details |
|---------|---------|
| Tables | Full support including merged cells (colspan/rowspan) |
| Images | Extracted to `images/` folder, embedded as `<img>` tags |
| Math | OMML formulas converted to LaTeX, rendered via MathJax CDN |
| Formatting | Bold, italic, underline, strikethrough |
| Styling | Built-in CSS with Chinese fonts, responsive layout |

## Dependencies

- `python-docx` must be installed: `python -m pip install python-docx`
- MathJax loads from CDN (requires internet for math rendering)
