---
name: markitdown
description: Convert various document formats to Markdown using Microsoft's markitdown library. Supports PDF, DOCX, PPTX, XLSX, HTML, EPUB, images, IPYNB, ZIP and more. Use when user mentions markitdown, convert to markdown, PPTX to md, XLSX to md, EPUB to md, or needs to read formats not covered by /pdf-reader or /word2md.
---

# Markitdown Skill (microsoft/markitdown)

Microsoft's markitdown converts 15+ file formats to Markdown. This skill covers **formats not handled by `/pdf-reader` and `/word2md`** — primarily PPTX, XLSX, EPUB, HTML, and more.

## When to Use

- User mentions: "markitdown", "/markitdown", "convert to markdown"
- Need to read **PPTX, XLSX, EPUB, IPYNB, ZIP** — these are NOT covered by `/pdf-reader` or `/word2md`
- Need **table-aware PDF extraction** (markitdown detects tables, `/pdf-reader` does not)
- User says "PPTX to markdown", "Excel to markdown", "EPUB to markdown"
- Quick one-shot conversion of any document to Markdown

## When NOT to Use (use other skills instead)

| Format | Better skill | Reason |
|--------|-------------|--------|
| PDF (reading) | `/pdf-reader` | PyMuPDF has 3 modes, higher fidelity, dict mode for LaTeX conversion |
| DOCX (with math) | `/word2md` | Correct OMML→LaTeX; markitdown has escaped-underscore bug (`\_{c}` instead of `_{c}`) |
| DOCX (with images) | `/word2md` | Extracts images to files; markitdown embeds base64 data URIs |

## Supported Formats

PDF, DOCX, PPTX, XLSX, HTML, EPUB, Images (via LLM caption or EXIF), IPYNB, CSV, Plain text, ZIP (processes contents), Audio/Video (transcription via Azure), Outlook MSG, RSS, Wikipedia, YouTube (transcript).

## Installation

```bash
python -m pip install markitdown 2>&1 | tail -3
```

## Usage

### CLI (recommended for single files)

```bash
# Convert to stdout
PYTHONIOENCODING=utf-8 markitdown "<INPUT_FILE>" 2>/dev/null

# Convert and save to file
PYTHONIOENCODING=utf-8 markitdown "<INPUT_FILE>" -o "<OUTPUT.md>" 2>/dev/null

# Pipe from stdin
PYTHONIOENCODING=utf-8 markitdown -x pptx < "<INPUT_FILE>" 2>/dev/null
```

### Python API (for batch or programmatic use)

```bash
PYTHONIOENCODING=utf-8 python -c "
from markitdown import MarkItDown
import sys

md = MarkItDown()
result = md.convert(sys.argv[1])
print(result.text_content)
" "<INPUT_FILE>"
```

### Batch conversion (multiple files)

```bash
PYTHONIOENCODING=utf-8 python -c "
from markitdown import MarkItDown
import sys, os, glob

md = MarkItDown()
files = glob.glob(sys.argv[1])
for f in files:
    print(f'--- {os.path.basename(f)} ---')
    result = md.convert(f)
    print(result.text_content[:2000])
    print()
" "<GLOB_PATTERN>"
```

## Examples

### PPTX (PowerPoint) to Markdown

```bash
PYTHONIOENCODING=utf-8 markitdown "presentation.pptx" -o "presentation.md" 2>/dev/null
```

### XLSX (Excel) to Markdown

```bash
PYTHONIOENCODING=utf-8 markitdown "spreadsheet.xlsx" 2>/dev/null
```

### EPUB to Markdown

```bash
PYTHONIOENCODING=utf-8 markitdown "book.epub" -o "book.md" 2>/dev/null
```

### HTML to Markdown

```bash
PYTHONIOENCODING=utf-8 markitdown "page.html" 2>/dev/null
```

### PDF with table detection

```bash
PYTHONIOENCODING=utf-8 markitdown "report.pdf" -o "report.md" 2>/dev/null
```

markitdown uses `pdfplumber` to detect tables and output pipe-formatted markdown tables. If pdfplumber fails, falls back to `pdfminer`.

## CLI Options

| Flag | Description |
|------|-------------|
| `-o, --output` | Output file path (default: stdout) |
| `-x, --extension` | Hint file extension (when reading stdin) |
| `-m, --mime-type` | Hint MIME type |
| `-c, --charset` | Hint charset (e.g. UTF-8) |
| `-d, --use-docintel` | Use Azure Document Intelligence (requires endpoint) |
| `-p, --use-plugins` | Enable 3rd-party plugins |
| `--keep-data-uris` | Keep base64 images in output (default: truncated) |
| `--list-plugins` | List installed plugins |

## Known Limitations

1. **DOCX math bug**: OMML→LaTeX escapes underscores (`\_{c}` instead of `_{c}`), breaking LaTeX rendering. Use `/word2md` for DOCX with math.
2. **Base64 images**: Images embedded as data URIs, truncated by default. Use `--keep-data-uris` to preserve (output becomes very large). Use `/word2md` if you need image files extracted.
3. **Scanned PDFs**: Like all text extractors, cannot handle image-only pages. Needs OCR (paddleocr, tesseract).
4. **Audio/Video transcription**: Requires Azure Document Intelligence endpoint (`-d -e <endpoint>`).

## Rules

1. **Always use `PYTHONIOENCODING=utf-8`** — Windows defaults to GBK
2. **Always suppress warnings with `2>/dev/null`** — markitdown's dependency warnings are noisy
3. **For DOCX with math formulas** — recommend `/word2md` instead (this skill's OMML converter has bugs)
4. **For PDF reading** — prefer `/pdf-reader` for high fidelity; use this skill when you need table detection
5. **Check dependencies**: Some formats need extras (`pip install markitdown[pdf]`, etc.)
