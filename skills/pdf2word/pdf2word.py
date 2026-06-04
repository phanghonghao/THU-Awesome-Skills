"""
pdf2word.py — Convert PDF to Word (.docx) preserving layout.

Usage:
    python pdf2word.py <input.pdf> [output.docx] [--start 0] [--end 5] [--pages 0,1,2]
"""

import sys
import os
import argparse

try:
    from pdf2docx import Converter
except ImportError:
    print("ERROR: pdf2docx not installed. Run: python -m pip install pdf2docx")
    sys.exit(1)


def convert(pdf_path, docx_path=None, start=0, end=None, pages=None):
    """Convert PDF to Word document."""
    if docx_path is None:
        base = os.path.splitext(pdf_path)[0]
        docx_path = base + ".docx"

    cv = Converter(pdf_path)

    kwargs = {"output": docx_path}
    if pages is not None:
        kwargs["pages"] = pages
    else:
        if start > 0 or end is not None:
            kwargs["start"] = start
            if end is not None:
                kwargs["end"] = end

    print(f"Converting: {pdf_path}")
    print(f"Output:     {docx_path}")
    if pages:
        print(f"Pages:      {pages}")
    elif start > 0 or end:
        print(f"Range:      {start}-{end or 'end'}")

    cv.convert(**kwargs)
    cv.close()
    print(f"Done! Saved to: {docx_path}")
    return docx_path


def main():
    parser = argparse.ArgumentParser(description="Convert PDF to Word (.docx)")
    parser.add_argument("input", help="Input PDF file path")
    parser.add_argument("output", nargs="?", default=None, help="Output Word file path")
    parser.add_argument("--start", type=int, default=0, help="Start page (0-indexed)")
    parser.add_argument("--end", type=int, default=None, help="End page (exclusive)")
    parser.add_argument("--pages", type=str, default=None, help="Specific pages (comma-separated)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: File not found: {args.input}")
        sys.exit(1)

    pages = None
    if args.pages:
        pages = [int(p.strip()) for p in args.pages.split(",")]

    convert(args.input, args.output, args.start, args.end, pages)


if __name__ == "__main__":
    main()
