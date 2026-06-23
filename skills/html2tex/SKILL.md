---
name: html2tex
description: >-
  Convert HTML, especially HTML generated from Word or `word2html`, into LaTeX
  and optionally PDF via XeLaTeX. Use when the user mentions `html2tex`, wants
  to convert HTML to LaTeX or PDF, or needs support for merged tables, embedded
  images, inline formatting, or MathJax formulas.
---

# html2tex

Convert HTML files to LaTeX and PDF with the bundled `html2tex.py` script.

## Run

From this skill directory, run:

```bash
python html2tex.py <input.html> [--output-dir DIR] [--no-compile]
```

## Inputs

Assume the input HTML may contain:
- tables with `colspan` and `rowspan`
- embedded images
- bold, italic, underline, and strikethrough
- MathJax-style formulas

Use this skill especially for HTML produced by a Word-to-HTML workflow.

## Outputs

Produce:
- `<input>.tex`
- `<input>.pdf` when compilation is enabled

If `--output-dir` is omitted, write output next to the input file.

## Workflow

1. Confirm the input file exists.
2. Run `html2tex.py`.
3. If the user asked for PDF and compilation succeeds, report both `.tex` and `.pdf`.
4. If XeLaTeX is missing or compilation fails, rerun with `--no-compile` only when needed and report that only `.tex` was generated.

## Dependencies

Require:
- Python 3
- XeLaTeX for PDF compilation

If XeLaTeX is unavailable, do not pretend PDF generation succeeded.

## Notes

- Preserve tables and images where possible.
- Prefer reporting the generated file paths instead of pasting LaTeX output into the response.
- If the HTML appears broken, mention that the converter can only preserve structure that exists in the source HTML.