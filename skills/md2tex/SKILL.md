---
name: md2tex
description: >-
  Markdown to LaTeX + PDF converter. Converts .md to .tex (XeLaTeX + ctex) and compiles to .pdf.
  Supports Chinese, tables, images, math formulas, code blocks.
---

# md2tex — Markdown → LaTeX + PDF

将 Markdown 文件转换为 LaTeX 文档 (.tex)，并用 MiKTeX 的 XeLaTeX 编译为 PDF。

## When to Use

- User says "md2tex", "md转tex", "转latex", "生成pdf", "转pdf"
- User has a Markdown file and wants LaTeX source + compiled PDF
- User needs a document/report (NOT presentation — use latex-beamer for that)

## How to Use

```bash
# Convert MD → TEX + PDF
python ~/.claude/skills/md2tex/md2tex.py "<input.md>"

# Specify output directory
python ~/.claude/skills/md2tex/md2tex.py "<input.md>" --output-dir <dir>

# Only generate .tex, skip PDF compilation
python ~/.claude/skills/md2tex/md2tex.py "<input.md>" --no-compile
```

## Features

| Feature | Support |
|---------|---------|
| Chinese text | ctex package (XeLaTeX) |
| Headings (#, ##, ###) | \section, \subsection, \subsubsection |
| Tables | tabular with \hline |
| Images ![](path) | \includegraphics with figure |
| Math (inline $...$, display $$...$$) | amsmath |
| Code blocks (```) | listings package |
| Bold/Italic | \textbf, \textit |
| Horizontal rule (---) | \rule |

## Output

For input `report.md`:
- `report.tex` — LaTeX source (fully compilable with XeLaTeX)
- `report.pdf` — Compiled PDF

## Dependencies

- **MiKTeX** with XeLaTeX: `C:\MiKTeX\miktex\bin\x64\xelatex.exe`
- **Python 3** (no extra packages needed for basic usage)

## Differences from latex-beamer

| | md2tex | latex-beamer |
|--|--------|-------------|
| Document type | Article/Report | Presentation slides |
| Class | `\documentclass{article}` | `\documentclass{beamer}` |
| Output | .tex + .pdf | .tex + .pdf + .pptx |
| Complexity | Simple conversion | Full sync + incremental updates |
