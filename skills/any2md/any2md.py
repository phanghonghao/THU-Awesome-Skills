# -*- coding: utf-8 -*-
"""Universal document-to-Markdown converter.

Routes to the best backend per format:
  - DOCX with math -> word2md (OMML->LaTeX, no escaping bugs)
  - DOCX without math / PPTX / XLSX / HTML / EPUB / etc -> markitdown
  - PDF -> markitdown (table-aware) or PyMuPDF (high fidelity)
  - Post-processes to fix markdownify math-escaping bugs
"""
import sys
import io
import re
import os
import subprocess

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ─── Post-processing: fix math escaping ───────────────────────────

def fix_math_escaping(text):
    """Fix markdownify's incorrect escaping inside $...$ math blocks.

    markdownify treats underscores as emphasis markers and escapes them
    inside math delimiters, producing $v\\_{c}$ instead of $v_{c}$.
    """
    # Fix display math $$...$$ first (may be multiline)
    def fix_display(m):
        inner = m.group(1)
        inner = inner.replace(r'\_', '_').replace(r'\*', '*')
        return '$$' + inner + '$$'
    text = re.sub(r'\$\$(.*?)\$\$', fix_display, text, flags=re.DOTALL)

    # Fix inline math $...$
    def fix_inline(m):
        inner = m.group(1)
        inner = inner.replace(r'\_', '_').replace(r'\*', '*')
        return '$' + inner + '$'
    text = re.sub(r'\$([^$\n]+?)\$', fix_inline, text)

    return text


# ─── Format detection ─────────────────────────────────────────────

def get_ext(path):
    """Get lowercase file extension without dot."""
    _, ext = os.path.splitext(path)
    return ext.lstrip('.').lower()


def docx_has_math(path):
    """Quick check: does this DOCX contain Office Math (OMML) elements?"""
    import zipfile
    try:
        with zipfile.ZipFile(path) as zf:
            with zf.open('word/document.xml') as f:
                content = f.read().decode('utf-8')
                return 'oMath' in content
    except (KeyError, zipfile.BadZipFile):
        return False


# ─── Backends ──────────────────────────────────────────────────────

SKILLS_DIR = os.path.dirname(os.path.abspath(__file__))
WORD2MD = os.path.join(os.path.dirname(SKILLS_DIR), 'word2md', 'word2md.py')


def convert_word2md(input_path, output_path=None):
    """Use word2md.py for DOCX with math formulas."""
    cmd = [sys.executable, WORD2MD, input_path]
    if output_path:
        cmd.append(output_path)

    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding='utf-8', errors='replace')
    if result.returncode != 0:
        print(f'word2md error: {result.stderr}', file=sys.stderr)
        return None

    if output_path:
        with io.open(output_path, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = result.stdout

    return text


def convert_markitdown(input_path, output_path=None):
    """Use markitdown for general formats. Returns markdown text."""
    from markitdown import MarkItDown
    md = MarkItDown()
    result = md.convert(input_path)
    text = result.text_content

    # Post-process: fix math escaping from markdownify
    text = fix_math_escaping(text)

    if output_path:
        with io.open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'Written to {output_path}')

    return text


def convert_pymupdf(input_path, output_path=None):
    """Use PyMuPDF for high-fidelity PDF extraction."""
    import fitz
    doc = fitz.open(input_path)
    parts = []
    for page in doc:
        parts.append(page.get_text())
    doc.close()
    text = '\n\n'.join(parts)

    if output_path:
        with io.open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'Written to {output_path}')

    return text


# ─── Route logic ──────────────────────────────────────────────────

def convert(input_path, output_path=None, math=None, pdf_backend=None):
    """Convert a document to Markdown.

    Args:
        input_path: Path to input file.
        output_path: Path to output .md file (optional, prints to stdout if None).
        math: 'auto' (default), 'yes', 'no' — whether file contains math.
        pdf_backend: 'markitdown' (default) or 'pymupdf' — PDF backend.
    """
    ext = get_ext(input_path)
    if not os.path.isfile(input_path):
        print(f'Error: file not found: {input_path}', file=sys.stderr)
        sys.exit(1)

    # ── DOCX routing ──
    if ext == 'docx':
        has_math = False
        if math == 'yes':
            has_math = True
        elif math == 'auto':
            has_math = docx_has_math(input_path)

        if has_math:
            print(f'[any2md] DOCX with math -> word2md', file=sys.stderr)
            text = convert_word2md(input_path, output_path)
        else:
            print(f'[any2md] DOCX without math -> markitdown', file=sys.stderr)
            text = convert_markitdown(input_path, output_path)

        if not output_path and text:
            print(text)
        return

    # ── PDF routing ──
    if ext == 'pdf':
        backend = pdf_backend or 'markitdown'
        if backend == 'pymupdf':
            print(f'[any2md] PDF (high fidelity) -> PyMuPDF', file=sys.stderr)
            text = convert_pymupdf(input_path, output_path)
        else:
            print(f'[any2md] PDF (table-aware) -> markitdown', file=sys.stderr)
            text = convert_markitdown(input_path, output_path)

        if not output_path and text:
            print(text)
        return

    # ── All other formats: markitdown ──
    print(f'[any2md] {ext.upper()} -> markitdown', file=sys.stderr)
    text = convert_markitdown(input_path, output_path)
    if not output_path and text:
        print(text)


# ─── CLI ───────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Universal document to Markdown converter')
    parser.add_argument('input', help='Input file path')
    parser.add_argument('output', nargs='?', default=None,
                        help='Output .md file path (default: stdout)')
    parser.add_argument('--math', choices=['auto', 'yes', 'no'], default='auto',
                        help='Whether file contains math formulas (default: auto-detect)')
    parser.add_argument('--pdf-backend', choices=['markitdown', 'pymupdf'],
                        default='markitdown',
                        help='PDF backend: markitdown (table-aware) or pymupdf (high fidelity)')
    args = parser.parse_args()

    convert(args.input, args.output, math=args.math,
            pdf_backend=args.pdf_backend)


if __name__ == '__main__':
    main()
