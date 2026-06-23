---
name: pdf-reader
description: Use PyMuPDF (fitz) to read and extract text from PDF files, instead of the native Read tool. Use this skill when user mentions "read PDF", "读取PDF", "PDF内容", "提取PDF", "PDF text", "open PDF", "打开PDF", or when you need to read any .pdf file. Always prefer this over the native Read tool for PDF files.
---

# PDF Reader Skill (PyMuPDF)

Use PyMuPDF (`import fitz`) to read PDF files. Supports **3 extraction modes** with increasing fidelity. Handles Chinese text, multi-page PDFs, and image-based PDFs.

## When to Use

- **Any time you need to read a .pdf file** — always use this instead of the native Read tool
- User mentions: "read PDF", "读取PDF", "PDF内容", "提取PDF", "PDF text", "open PDF"
- User provides a file path ending in `.pdf`
- Any task requiring PDF content extraction

## Extraction Modes

Choose the mode based on the downstream task:

| Mode | Method | Output | Best for |
|------|--------|--------|----------|
| **text** (default) | `get_text()` | Plain text | Simple reading, summarization |
| **html** | `get_text("html")` | HTML with CSS formatting | High-fidelity intermediate format, preserving bold/italic/font size/color |
| **dict** | `get_text("dict")` | Structured JSON-like dict | Maximum fidelity — font name, size, color, position, flags; ideal for PDF → .tex conversion |

**Mode selection guide:**
- Just need to read content? → `text`
- Need to preserve formatting (bold, italic, headings, tables)? → `html`
- Converting PDF to .tex/.docx and need font size / layout info? → `dict`
- Not sure? → Use `dict` (most complete, can derive everything else)

## Implementation

### Step 1: Check PyMuPDF Installation

```bash
python -m pip install PyMuPDF 2>&1 | tail -3
```

### Step 2: Extract PDF Content

**Always set `PYTHONIOENCODING=utf-8`** to avoid GBK encoding issues on Windows.

---

#### Mode: text (default — plain text extraction)

```bash
PYTHONIOENCODING=utf-8 python -c "
import fitz, sys
pdf_path = sys.argv[1]
doc = fitz.open(pdf_path)
print(f'Total pages: {len(doc)}')
for page in doc:
    text = page.get_text()
    if text.strip():
        print(f'--- Page {page.number + 1} ---')
        print(text)
    else:
        print(f'--- Page {page.number + 1}: [empty/image-only] ---')
doc.close()
" "<PDF_PATH>"
```

With page range:

```bash
PYTHONIOENCODING=utf-8 python -c "
import fitz, sys
pdf_path = sys.argv[1]
start, end = int(sys.argv[2]) - 1, int(sys.argv[3])
doc = fitz.open(pdf_path)
print(f'Total pages: {len(doc)}, extracting pages {start+1}-{end}')
for i in range(start, min(end, len(doc))):
    text = doc[i].get_text()
    if text.strip():
        print(f'--- Page {i + 1} ---')
        print(text)
    else:
        print(f'--- Page {i + 1}: [empty/image-only] ---')
doc.close()
" "<PDF_PATH>" "<START>" "<END>"
```

---

#### Mode: html (high-fidelity HTML with CSS formatting)

Outputs HTML preserving **bold, italic, font family, font size, text color, and paragraph structure**. Ideal as an intermediate format before converting to .tex or .docx.

```bash
PYTHONIOENCODING=utf-8 python -c "
import fitz, sys
pdf_path = sys.argv[1]
out_path = sys.argv[2] if len(sys.argv) > 2 else pdf_path.rsplit('.', 1)[0] + '.html'
doc = fitz.open(pdf_path)
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('<html><head><meta charset=\"utf-8\"><style>body{font-family:sans-serif;}</style></head><body>\n')
    for page in doc:
        html = page.get_text('html')
        f.write(html + '\n')
    f.write('</body></html>')
print(f'Exported HTML: {out_path} ({len(doc)} pages)')
doc.close()
" "<PDF_PATH>" "<OUTPUT_HTML_PATH>"
```

`<OUTPUT_HTML_PATH>` is optional — defaults to same name as PDF with `.html` extension.

To page range:

```bash
PYTHONIOENCODING=utf-8 python -c "
import fitz, sys
pdf_path = sys.argv[1]
start, end = int(sys.argv[2]) - 1, int(sys.argv[3])
out_path = sys.argv[4] if len(sys.argv) > 4 else pdf_path.rsplit('.', 1)[0] + '.html'
doc = fitz.open(pdf_path)
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('<html><head><meta charset=\"utf-8\"><style>body{font-family:sans-serif;}</style></head><body>\n')
    for i in range(start, min(end, len(doc))):
        f.write(doc[i].get_text('html') + '\n')
    f.write('</body></html>')
print(f'Exported HTML: {out_path} (pages {start+1}-{min(end, len(doc))})')
doc.close()
" "<PDF_PATH>" "<START>" "<END>" "<OUTPUT_HTML_PATH>"
```

---

#### Mode: dict (maximum fidelity — structured data with font metadata)

Outputs a structured summary of every text span, including **font name, font size (pt), text color, bold/italic flags, and position (x, y)**. This is the best mode for PDF → LaTeX conversion because font sizes can be mapped to heading levels.

```bash
PYTHONIOENCODING=utf-8 python -c "
import fitz, json, sys
pdf_path = sys.argv[1]
start = int(sys.argv[2]) - 1 if len(sys.argv) > 2 else 0
end = int(sys.argv[3]) if len(sys.argv) > 3 else 999999

doc = fitz.open(pdf_path)
total = len(doc)
end = min(end, total)
print(f'Total pages: {total}, extracting pages {start+1}-{end} (dict mode)')
print('=' * 60)

for i in range(start, end):
    page = doc[i]
    data = page.get_text('dict')
    print(f'\n--- Page {i + 1} (size: {page.rect.width:.0f} x {page.rect.height:.0f} pt) ---')
    for block in data['blocks']:
        if block['type'] == 0:  # text block
            for line in block['lines']:
                for span in line['spans']:
                    flags = span['flags']
                    bold = bool(flags & (1 << 4))
                    italic = bool(flags & (1 << 1))
                    size = span['size']
                    font = span['font']
                    color = span['color']
                    text = span['text'].strip()
                    if not text:
                        continue
                    origin = span['origin']
                    # Print with metadata annotations
                    attrs = []
                    if bold: attrs.append('bold')
                    if italic: attrs.append('italic')
                    if size > 14: attrs.append(f'HEADING?({size:.1f}pt)')
                    elif size > 12: attrs.append(f'subtitle?({size:.1f}pt)')
                    attr_str = f' [{\" \".join(attrs)}]' if attrs else ''
                    print(f'  L{origin[1]:6.1f} {size:5.1f}pt {font:20s} {text}{attr_str}')
        elif block['type'] == 1:  # image block
            print(f'  [IMAGE {block[\"width\"]}x{block[\"height\"]} at ({block[\"bbox\"][0]:.0f},{block[\"bbox\"][1]:.0f})]')
doc.close()
" "<PDF_PATH>" "<START>" "<END>"
```

This prints a compact, human-readable summary like:

```
--- Page 1 (size: 595 x 842 pt) ---
  L  56.0 24.0pt SimHei              第一章 绪论 [bold HEADING?(24.0pt)]
  L  82.0 12.0pt SimSun              本文研究了...
  L  98.0 12.0pt TimesNewRoman       E = mc^2 [italic]
  [IMAGE 400x300 at (100,200)]
```

**To save full dict as JSON file** (for programmatic downstream use):

```bash
PYTHONIOENCODING=utf-8 python -c "
import fitz, json, sys
pdf_path = sys.argv[1]
out_path = sys.argv[2] if len(sys.argv) > 2 else pdf_path.rsplit('.', 1)[0] + '.dict.json'

doc = fitz.open(pdf_path)
result = {'pages': [], 'total_pages': len(doc)}
for page in doc:
    data = page.get_text('dict')
    result['pages'].append(data)
doc.close()

with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f'Saved dict JSON: {out_path} ({len(result[\"pages\"])} pages)')
" "<PDF_PATH>" "<OUTPUT_JSON_PATH>"
```

---

### Step 3: Handle Image-Only PDFs

If text extraction returns empty/pages show `[empty/image-only]`, the PDF is likely a scanned document:

> This PDF appears to be an image-based (scanned) document. Text extraction returned empty. To extract content, you would need OCR tools like `pytesseract` + `pdf2image`, or `paddleocr`.

## Rules

1. **Always use `PYTHONIOENCODING=utf-8`** — Windows defaults to GBK which fails on Unicode characters
2. **Always use `python -m pip install`** (not bare `pip`) — ensures installation into the correct venv
3. **Use `python -c`** with the script inline — no need to create temporary .py files
4. **Pass PDF path as sys.argv[1]** — avoids shell quoting issues with paths containing spaces or Chinese characters
5. **Do NOT use the native Read tool for PDF files** — this skill replaces it entirely
6. **Default to `dict` mode** when the user needs high fidelity, format preservation, or PDF → LaTeX conversion
7. **`html` mode writes to file** (not stdout) — HTML output is too large for terminal display; always save to `.html` file
8. **`dict` mode** prints a compact summary to stdout by default; use the JSON variant to save full structured data to `.dict.json` file
