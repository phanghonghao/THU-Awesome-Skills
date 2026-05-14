---
name: pdf-reader
description: Use PyMuPDF (fitz) to read and extract text from PDF files, instead of the native Read tool. Use this skill when user mentions "read PDF", "读取PDF", "PDF内容", "提取PDF", "PDF text", "open PDF", "打开PDF", or when you need to read any .pdf file. Always prefer this over the native Read tool for PDF files.
---

# PDF Reader Skill (PyMuPDF)

Use PyMuPDF (`import fitz`) to read PDF files. This handles Chinese text, multi-page PDFs, and image-based PDFs better than the native Read tool.

## When to Use

- **Any time you need to read a .pdf file** — always use this instead of the native Read tool
- User mentions: "read PDF", "读取PDF", "PDF内容", "提取PDF", "PDF text", "open PDF"
- User provides a file path ending in `.pdf`
- Any task requiring PDF content extraction

## Implementation

### Step 1: Check PyMuPDF Installation

Before reading, verify PyMuPDF is installed. If not, install it:

```bash
python -m pip install PyMuPDF 2>&1 | tail -3
```

### Step 2: Extract PDF Text

Use the following Python script pattern. **Always set `PYTHONIOENCODING=utf-8`** to avoid GBK encoding issues on Windows.

**Basic extraction (all pages):**

```bash
PYTHONIOENCODING=utf-8 python -c "
import fitz
import sys

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

**Extract specific page range:**

```bash
PYTHONIOENCODING=utf-8 python -c "
import fitz
import sys

pdf_path = sys.argv[1]
start = int(sys.argv[2]) - 1  # 1-indexed to 0-indexed
end = int(sys.argv[3])        # exclusive, so pass the last page + 1

doc = fitz.open(pdf_path)
print(f'Total pages: {len(doc)}, extracting pages {start+1}-{end}')
for page_num in range(start, min(end, len(doc))):
    page = doc[page_num]
    text = page.get_text()
    if text.strip():
        print(f'--- Page {page_num + 1} ---')
        print(text)
    else:
        print(f'--- Page {page_num + 1}: [empty/image-only] ---')
doc.close()
" "<PDF_PATH>" "<START_PAGE>" "<END_PAGE>"
```

### Step 3: Handle Image-Only PDFs

If text extraction returns empty/pages show `[empty/image-only]`, the PDF is likely a scanned document. Inform the user:

> This PDF appears to be an image-based (scanned) document. Text extraction returned empty. To extract content, you would need OCR tools like `pytesseract` + `pdf2image`, or `paddleocr`.

## Rules

1. **Always use `PYTHONIOENCODING=utf-8`** — Windows defaults to GBK which fails on Unicode characters
2. **Always use `python -m pip install`** (not bare `pip`) — ensures installation into the correct venv
3. **Use `python -c`** with the script inline — no need to create temporary .py files
4. **Pass PDF path as sys.argv[1]** — avoids shell quoting issues with paths containing spaces or Chinese characters
5. **Do NOT use the native Read tool for PDF files** — this skill replaces it entirely
