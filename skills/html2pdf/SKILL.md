---
name: html2pdf
description: Convert HTML, especially slide-style HTML presentations, into paginated PDF using Chrome or Edge headless printing. Use when the user mentions `html2pdf`, wants to export HTML to PDF, or needs each slide/page in a presentation HTML to become a separate PDF page instead of one long page.
---

# html2pdf

Convert local HTML files to PDF with browser-grade rendering.

This skill is designed for two cases:
- ordinary HTML pages that should print to PDF as-is
- presentation-style HTML with fixed-size `.slide` pages that need to become multi-page PDF output

## Run

From this skill directory, run:

```bash
python html2pdf.py <input.html> [output.pdf]
```

## What It Does

For presentation HTML, the script can:
- detect slide-style layouts such as `.presentation` and `.slide`
- inject print CSS into a temporary copy
- make all slides visible during print
- force each slide to become one PDF page
- hide navigation bars during export

For ordinary HTML, it prints the page directly without altering the source file.

## Workflow

1. Confirm the input HTML exists.
2. Run `html2pdf.py`.
3. If the HTML looks like a presentation, let the script auto-inject print pagination CSS.
4. Export with Chrome or Edge headless.
5. If available, verify the resulting PDF page count and report the output path.

## Examples

```bash
# Default output: same basename as input
python html2pdf.py "slides.html"

# Explicit output path
python html2pdf.py "slides.html" "slides_10pages.pdf"
```

## Dependencies

Require one of:
- Google Chrome
- Microsoft Edge

Optional:
- `PyPDF2` for PDF page-count verification

## Notes

- The script does not overwrite the source HTML. It writes a temporary print-ready copy when needed.
- If the HTML already has correct `@media print` pagination rules, the script can still print it directly.
- Prefer reporting the generated PDF path and page count instead of dumping command output.
