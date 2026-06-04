"""
word2pdf.py — Convert Word (.doc / .docx) to PDF.

Auto-detects format via magic bytes:
  - .doc  (OLE2 Compound Binary) → COM / LibreOffice
  - .docx (ZIP / Office Open XML) → COM / LibreOffice

Usage:
    python word2pdf.py <input.doc|input.docx> [output.pdf]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Magic bytes for format detection
# ---------------------------------------------------------------------------
OLE2_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # .doc .xls .ppt
ZIP_MAGIC = b"PK\x03\x04"  # .docx .xlsx .pptx (ZIP archive)


def detect_format(filepath: str) -> str:
    """Return 'doc' or 'docx' based on magic bytes, fall back to extension."""
    with open(filepath, "rb") as f:
        header = f.read(8)

    if header.startswith(OLE2_MAGIC):
        return "doc"
    if header.startswith(ZIP_MAGIC):
        return "docx"

    # Fallback: guess from extension
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".doc":
        return "doc"
    if ext == ".docx":
        return "docx"

    raise ValueError(
        f"Cannot determine Word format: {filepath}\n"
        f"  Header hex: {header[:8].hex(' ')}\n"
        f"  Extension : {ext or '(none)'}"
    )


# ---------------------------------------------------------------------------
# Method 1: Microsoft Word COM (pywin32) — Windows only, best fidelity
# ---------------------------------------------------------------------------

def convert_via_com(filepath: str, output: str) -> tuple[bool, str]:
    """Try Microsoft Word COM automation. Returns (success, message)."""
    try:
        import win32com.client  # type: ignore
    except ImportError:
        return False, "pywin32 not installed"

    filepath_abs = os.path.abspath(filepath)
    output_abs = os.path.abspath(output)

    word = None
    doc = None
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        word.DisplayAlerts = False  # suppress dialogs
        doc = word.Documents.Open(filepath_abs)
        # wdFormatPDF = 17
        doc.SaveAs(output_abs, FileFormat=17)
        return True, "Microsoft Word COM"
    except Exception as exc:
        return False, str(exc)
    finally:
        try:
            if doc:
                doc.Close(False)
        except Exception:
            pass
        try:
            if word:
                word.Quit()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Method 2: LibreOffice headless — cross-platform fallback
# ---------------------------------------------------------------------------

def find_libreoffice() -> str | None:
    """Find LibreOffice / OpenOffice executable."""
    candidates = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    # Check PATH
    which = shutil.which("soffice")
    if which:
        candidates.insert(0, which)

    for p in candidates:
        if p and os.path.exists(p):
            return p
    return None


def convert_via_libreoffice(filepath: str, output: str) -> tuple[bool, str]:
    """Try LibreOffice headless conversion. Returns (success, message)."""
    lo = find_libreoffice()
    if not lo:
        return False, "LibreOffice not found"

    filepath_abs = os.path.abspath(filepath)
    output_dir = os.path.dirname(os.path.abspath(output))

    cmd = [
        lo,
        "--headless",
        "--convert-to", "pdf",
        "--outdir", output_dir,
        filepath_abs,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        return False, result.stderr.strip() or f"exit code {result.returncode}"

    # LibreOffice names output after input stem
    expected = os.path.join(output_dir, Path(filepath).stem + ".pdf")
    if os.path.exists(expected):
        target = os.path.abspath(output)
        if os.path.abspath(expected) != target:
            os.replace(expected, target)
        return True, "LibreOffice headless"

    return False, "Output PDF not found after conversion"


# ---------------------------------------------------------------------------
# PDF helpers
# ---------------------------------------------------------------------------

def count_pages(pdf_path: str) -> int | None:
    """Return page count of PDF, or None if PyPDF2 unavailable."""
    try:
        from PyPDF2 import PdfReader  # type: ignore
        return len(PdfReader(pdf_path).pages)
    except Exception:
        return None


def file_size_mb(path: str) -> str:
    size = os.path.getsize(path)
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def convert(filepath: str, output: str | None = None) -> str:
    """Convert Word to PDF. Returns output path."""
    # 1. Detect format
    fmt = detect_format(filepath)
    fmt_label = ".doc (OLE2 Binary)" if fmt == "doc" else ".docx (Office Open XML)"
    print(f"Format:   {fmt_label}")

    # 2. Default output path
    if output is None:
        output = os.path.splitext(filepath)[0] + ".pdf"
    outdir = os.path.dirname(os.path.abspath(output))
    if outdir:
        os.makedirs(outdir, exist_ok=True)

    print(f"Input:    {os.path.abspath(filepath)}")
    print(f"Output:   {os.path.abspath(output)}")

    # 3. Try conversion methods
    methods = [convert_via_com, convert_via_libreoffice]
    for method in methods:
        name = method.__name__
        print(f"Trying {name} ...")
        ok, msg = method(filepath, output)
        if ok:
            print(f"Method:   {msg}")
            break
        print(f"  {name} failed: {msg}")
    else:
        print("\nERROR: All conversion methods failed.", file=sys.stderr)
        print("Please install one of:", file=sys.stderr)
        print("  - Microsoft Word + pywin32 (pip install pywin32)", file=sys.stderr)
        print("  - LibreOffice (https://www.libreoffice.org/)", file=sys.stderr)
        sys.exit(1)

    # 4. Report results
    print(f"Size:     {file_size_mb(output)}")
    pages = count_pages(output)
    if pages is not None:
        print(f"Pages:    {pages}")
    print(f"\nDone! -> {os.path.abspath(output)}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert Word (.doc/.docx) to PDF with auto format detection."
    )
    parser.add_argument("input", help="Input Word file (.doc or .docx)")
    parser.add_argument("output", nargs="?", default=None, help="Output PDF path")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: File not found: {args.input}", file=sys.stderr)
        return 1

    convert(args.input, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
