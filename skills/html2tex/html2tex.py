"""
html2tex.py - HTML to LaTeX + PDF converter (XeLaTeX + ctex)

Parses HTML produced by word2html: tables with colspan/rowspan,
images, formatted text, MathJax formulas.

Usage:
    python html2tex.py <input.html> [--output-dir DIR] [--no-compile]

Output:
    <input>.tex  - LaTeX source (XeLaTeX + ctex)
    <input>.pdf  - Compiled PDF (via xelatex)
"""

import sys
import os
import re
import subprocess
import argparse
from pathlib import Path
from html.parser import HTMLParser
from html import unescape


# ============================================================
# Lightweight DOM
# ============================================================

class _Node:
    __slots__ = ('tag', 'attrs', 'children', 'text')

    def __init__(self, tag, attrs=None):
        self.tag = tag
        self.attrs = dict(attrs) if attrs else {}
        self.children = []
        self.text = None  # only set for text nodes

    def get_attr(self, name, default=None):
        return self.attrs.get(name, default)

    def get_int_attr(self, name, default=1):
        try:
            return int(self.attrs.get(name, default))
        except (ValueError, TypeError):
            return default


# ============================================================
# HTML -> DOM tree builder
# ============================================================

_VOID_ELEMENTS = frozenset([
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
    'link', 'meta', 'param', 'source', 'track', 'wbr',
])

_SKIP_TAGS = frozenset(['head', 'style', 'script', 'meta', 'title', 'link'])


class _HtmlTreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = _Node('root')
        self._stack = [self.root]
        self._skip_depth = 0  # depth counter for skipped subtrees

    # -- helpers --

    def _current(self):
        return self._stack[-1]

    def _push(self, node):
        self._current().children.append(node)
        self._stack.append(node)

    def _pop(self, tag):
        # Pop back to matching tag
        for i in range(len(self._stack) - 1, 0, -1):
            if self._stack[i].tag == tag:
                self._stack = self._stack[:i]
                return

    # -- parser callbacks --

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in _SKIP_TAGS:
            if tag not in _VOID_ELEMENTS:
                self._skip_depth += 1
            return
        if self._skip_depth > 0:
            return

        node = _Node(tag, attrs)

        if tag in _VOID_ELEMENTS:
            self._current().children.append(node)
            # don't push — self-closing
        else:
            self._push(node)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in _SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth > 0:
            return
        if tag in _VOID_ELEMENTS:
            return
        self._pop(tag)

    def handle_data(self, data):
        if self._skip_depth > 0:
            return
        node = _Node('TEXT')
        node.text = data
        self._current().children.append(node)

    def handle_entityref(self, name):
        if self._skip_depth > 0:
            return
        ch = unescape(f'&{name};')
        node = _Node('TEXT')
        node.text = ch
        self._current().children.append(node)

    def handle_charref(self, name):
        if self._skip_depth > 0:
            return
        ch = unescape(f'&#{name};')
        node = _Node('TEXT')
        node.text = ch
        self._current().children.append(node)


def _build_tree(html_text):
    builder = _HtmlTreeBuilder()
    builder.feed(html_text)
    builder.close()
    return builder.root


# ============================================================
# LaTeX special-character escaping
# ============================================================

_LATEX_SPECIAL = str.maketrans({
    '&': r'\&', '%': r'\%', '#': r'\#',
    '_': r'\_', '{': r'\{', '}': r'\}',
})

# Greek Unicode → LaTeX (for text outside math mode)
_GREEK_TO_LATEX = {
    'α': r'$\alpha$', 'β': r'$\beta$', 'γ': r'$\gamma$', 'δ': r'$\delta$',
    'ε': r'$\varepsilon$', 'ζ': r'$\zeta$', 'η': r'$\eta$', 'θ': r'$\theta$',
    'ι': r'$\iota$', 'κ': r'$\kappa$', 'λ': r'$\lambda$', 'μ': r'$\mu$',
    'ν': r'$\nu$', 'ξ': r'$\xi$', 'π': r'$\pi$', 'ρ': r'$\rho$',
    'σ': r'$\sigma$', 'τ': r'$\tau$', 'υ': r'$\upsilon$', 'φ': r'$\varphi$',
    'χ': r'$\chi$', 'ψ': r'$\psi$', 'ω': r'$\omega$',
    'Γ': r'$\Gamma$', 'Δ': r'$\Delta$', 'Θ': r'$\Theta$', 'Λ': r'$\Lambda$',
    'Ξ': r'$\Xi$', 'Π': r'$\Pi$', 'Σ': r'$\Sigma$', 'Φ': r'$\Phi$',
    'Ψ': r'$\Psi$', 'Ω': r'$\Omega$',
}
_MATH_SYMBOLS = {
    '≥': r'$\geq$', '≤': r'$\leq$', '≈': r'$\approx$', '≠': r'$\neq$',
    '⋅': r'$\cdot$', '×': r'$\times$', '→': r'$\to$', '∈': r'$\in$',
    '±': r'$\pm$', '∓': r'$\mp$', '∘': r'$^\circ$',
}


def _escape_latex(text):
    """Escape LaTeX special characters, preserving backslash-commands."""
    # Protect existing LaTeX commands (\textbf, \textit, etc.)
    parts = re.split(r'(\\[a-zA-Z]+(?:\{[^}]*\})*)', text)
    result = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            # This is a LaTeX command — keep as-is
            result.append(part)
        else:
            result.append(part.translate(_LATEX_SPECIAL))
    return ''.join(result)


def _replace_unicode_math(text):
    """Replace Greek and math Unicode chars with LaTeX equivalents."""
    for ch, cmd in _GREEK_TO_LATEX.items():
        text = text.replace(ch, cmd)
    for ch, cmd in _MATH_SYMBOLS.items():
        text = text.replace(ch, cmd)
    return text


# ============================================================
# Core converter
# ============================================================

class Html2TexConverter:
    def __init__(self, html_path, output_dir=None):
        self.html_path = os.path.abspath(html_path)
        self.html_dir = os.path.dirname(self.html_path)
        self.html_name = Path(html_path).stem
        self.output_dir = os.path.abspath(output_dir) if output_dir else self.html_dir

        with open(self.html_path, 'r', encoding='utf-8') as f:
            self.html_text = f.read()

        self.images = []      # (rel_path, full_path)
        self.has_table = False
        self.has_math = False

    # -- public API --

    def convert(self):
        tree = _build_tree(self.html_text)
        body_parts = []
        for child in tree.children:
            latex = self._convert_node(child)
            if latex:
                body_parts.append(latex)
        return self._assemble_document(body_parts)

    # -- node dispatch --

    def _convert_node(self, node, in_table=False):
        if node.tag == 'TEXT':
            return self._convert_text(node, in_table)

        tag = node.tag.lower()

        # Structural — recurse into children
        if tag in ('root', 'html', 'body', 'div', 'section', 'article',
                    'main', 'span', 'header', 'footer', 'nav'):
            parts = [self._convert_node(c, in_table) for c in node.children]
            return ''.join(p for p in parts if p)

        # Headings
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            return self._convert_heading(node)

        # Paragraphs
        if tag == 'p':
            return self._convert_paragraph(node, in_table)

        # Tables
        if tag == 'table':
            return self._convert_table(node)

        # Images
        if tag == 'img':
            return self._convert_image(node, in_table)

        # Line break
        if tag == 'br':
            return ' \\\\ ' if in_table else '\\newline '

        # Bold
        if tag == 'b' or tag == 'strong':
            inner = self._collect_inline(node, in_table)
            return f'\\textbf{{{inner}}}'

        # Italic
        if tag == 'i' or tag == 'em':
            inner = self._collect_inline(node, in_table)
            return f'\\textit{{{inner}}}'

        # Underline
        if tag == 'u':
            inner = self._collect_inline(node, in_table)
            return f'\\underline{{{inner}}}'

        # Strikethrough
        if tag in ('s', 'strike', 'del'):
            inner = self._collect_inline(node, in_table)
            return f'\\sout{{{inner}}}'

        # Fallback: recurse
        parts = [self._convert_node(c, in_table) for c in node.children]
        return ''.join(p for p in parts if p)

    # -- text & inline --

    def _convert_text(self, node, in_table=False):
        text = node.text
        if text is None:
            return ''
        # &nbsp; -> ~
        text = text.replace('\u00a0', '~')
        # Replace Greek / math Unicode with LaTeX
        text = _replace_unicode_math(text)
        # Pass through math delimiters: \(...\), $$...$$
        # Check for math content before escaping
        if '\\(' in text or '$$' in text:
            self.has_math = True
            # Split around math regions and only escape non-math parts
            return self._protect_math_in_text(text)
        # Escape LaTeX special chars in plain text
        return _escape_latex(text)

    def _protect_math_in_text(self, text):
        """Escape text while preserving \\(...\\) and $$...$$ math regions."""
        # Split on \(...\) and $$...$$
        parts = re.split(r'(\\\\\\(.*?\\\\\\)|\\$\\$.*?\\$\\$)', text, flags=re.DOTALL)
        result = []
        for part in parts:
            if part.startswith('\\(') or part.startswith('$$'):
                self.has_math = True
                result.append(part)
            else:
                result.append(_escape_latex(part))
        return ''.join(result)

    def _collect_inline(self, node, in_table=False):
        """Collect inline content from children into a single string."""
        parts = []
        for child in node.children:
            latex = self._convert_node(child, in_table)
            if latex:
                parts.append(latex)
        return ''.join(parts)

    # -- headings --

    def _convert_heading(self, node):
        level = int(node.tag[1])
        commands = {1: 'section', 2: 'subsection', 3: 'subsubsection',
                    4: 'paragraph', 5: 'subparagraph', 6: 'subparagraph'}
        cmd = commands.get(level, 'paragraph')
        title = self._collect_inline(node)
        # Clean escaped characters that are fine in headings
        return f'\\{cmd}{{{title}}}\n\n'

    # -- paragraphs --

    def _convert_paragraph(self, node, in_table=False):
        if in_table:
            # Inside table cells, just collect inline content
            return self._collect_inline(node, True)

        inner = self._collect_inline(node)
        if not inner.strip():
            return ''

        # Check if paragraph contains only images
        has_only_images = all(
            c.tag == 'img' or (c.tag == 'TEXT' and (c.text or '').strip() == '')
            for c in node.children
        )
        img_children = [c for c in node.children if c.tag == 'img']

        if img_children and has_only_images:
            # Multiple images in one paragraph — output as figures
            parts = []
            for img_node in img_children:
                parts.append(self._convert_image(img_node, in_table=False))
            return ''.join(parts) + '\n'

        return inner + '\n\n'

    # -- images --

    def _convert_image(self, node, in_table=False):
        src = node.get_attr('src', '')
        if not src:
            return ''

        # Resolve path
        if os.path.isabs(src):
            full_path = src
        else:
            full_path = os.path.normpath(os.path.join(self.html_dir, src))

        # Relative path from output_dir
        try:
            rel_path = os.path.relpath(full_path, self.output_dir)
        except ValueError:
            rel_path = src
        rel_path = rel_path.replace('\\', '/')

        self.images.append((rel_path, full_path))

        if in_table:
            return f'\\includegraphics[width=0.3\\textwidth]{{{rel_path}}}'
        else:
            return (f'\\begin{{figure}}[htbp]\n'
                    f'  \\centering\n'
                    f'  \\includegraphics[width=0.6\\textwidth]{{{rel_path}}}\n'
                    f'\\end{{figure}}\n')

    # -- tables (the hard part) --

    def _convert_table(self, node):
        rows = self._collect_table_rows(node)
        if not rows:
            return ''

        self.has_table = True

        # Phase 1: Build cell grid with colspan/rowspan info
        grid = []  # grid[row] = list of (content_latex, colspan, rowspan)
        for tr in rows:
            cells = []
            for child in tr.children:
                if child.tag in ('td', 'th'):
                    content = self._collect_inline(child, in_table=True)
                    colspan = child.get_int_attr('colspan', 1)
                    rowspan = child.get_int_attr('rowspan', 1)
                    cells.append((content, colspan, rowspan))
            grid.append(cells)

        if not grid:
            return ''

        # Phase 2: Determine actual column count via occupied-grid simulation
        num_rows = len(grid)
        # occupied[r][c] = True if already filled by a rowspan from above
        occupied = [[False] * 200 for _ in range(num_rows)]  # generous width
        actual_cols = 0

        for ri, row in enumerate(grid):
            ci = 0  # logical column index
            for content, colspan, rowspan in row:
                # Skip occupied cells
                while ci < 200 and occupied[ri][ci]:
                    ci += 1
                if ci >= 200:
                    break
                # Mark this cell + colspan
                actual_cols = max(actual_cols, ci + colspan)
                # Mark occupied for rowspan
                for dr in range(rowspan):
                    for dc in range(colspan):
                        rr = ri + dr
                        if rr < num_rows and ci + dc < 200:
                            occupied[rr][ci + dc] = True
                ci += colspan

        if actual_cols == 0:
            return ''

        # Phase 3: Re-simulate to build LaTeX rows
        # Reset occupied grid
        occupied = [[False] * actual_cols for _ in range(num_rows)]

        latex_rows = []
        for ri, row in enumerate(grid):
            latex_cells = []
            ci = 0
            for content, colspan, rowspan in row:
                # Emit empty cells for positions occupied by multirow from above
                while ci < actual_cols and occupied[ri][ci]:
                    latex_cells.append('')
                    ci += 1
                if ci >= actual_cols:
                    break

                # Mark occupied
                for dr in range(rowspan):
                    for dc in range(colspan):
                        rr = ri + dr
                        if rr < num_rows and ci + dc < actual_cols:
                            occupied[rr][ci + dc] = True

                cell_tex = content if content.strip() else ' '

                # Wrap multi-line content in \shortstack for tabular compatibility
                if '\\\\' in cell_tex:
                    cell_tex = f'\\shortstack{{{cell_tex}}}'

                if colspan > 1 and rowspan > 1:
                    cell_tex = (f'\\multicolumn{{{colspan}}}{{|c|}}{{'
                                f'\\multirow{{{rowspan}}}{{*}}{{{cell_tex}}}}}')
                elif colspan > 1:
                    cell_tex = f'\\multicolumn{{{colspan}}}{{|c|}}{{{cell_tex}}}'
                elif rowspan > 1:
                    cell_tex = f'\\multirow{{{rowspan}}}{{*}}{{{cell_tex}}}'

                latex_cells.append(cell_tex)
                ci += colspan

            # Handle trailing occupied cells
            while ci < actual_cols and occupied[ri][ci]:
                latex_cells.append('')
                ci += 1

            if latex_cells:
                latex_rows.append(' & '.join(latex_cells) + ' \\\\')

        if not latex_rows:
            return ''

        # Column spec
        col_spec = '|' + '|'.join(['c'] * actual_cols) + '|'

        # Build tabular
        tab_lines = [f'\\begin{{tabular}}{{{col_spec}}}']
        tab_lines.append('\\hline')
        for row_tex in latex_rows:
            tab_lines.append(row_tex)
            tab_lines.append('\\hline')
        tab_lines.append('\\end{tabular}')

        tab_tex = '\n'.join(tab_lines)

        # Always wrap in resizebox to prevent overflow
        tab_tex = ('\\begin{center}\n'
                   '\\resizebox{\\textwidth}{!}{%\n'
                   + tab_tex + '}\n'
                   '\\end{center}\n')

        return tab_tex + '\n'

    def _collect_table_rows(self, node):
        """Collect <tr> nodes from table, including from nested <tbody>/<thead>/<tfoot>."""
        rows = []
        for child in node.children:
            if child.tag == 'tr':
                rows.append(child)
            elif child.tag in ('tbody', 'thead', 'tfoot'):
                for sub in child.children:
                    if sub.tag == 'tr':
                        rows.append(sub)
        return rows

    # -- document assembly --

    def _assemble_document(self, body_parts):
        body = '\n'.join(body_parts)

        packages = [
            r'\usepackage[UTF8]{ctex}',
            r'\usepackage{graphicx}',
            r'\usepackage{amsmath}',
            r'\usepackage{amssymb}',
            r'\usepackage{array}',
            r'\usepackage{longtable}',
            r'\usepackage{multirow}',
            r'\usepackage[normalem]{ulem}',
            r'\usepackage[margin=2.5cm]{geometry}',
            r'\usepackage{hyperref}',
        ]

        # Image search paths
        img_dirs = set()
        for rel, full in self.images:
            d = os.path.dirname(rel)
            if d:
                img_dirs.add(d)
        if img_dirs:
            paths_str = ', '.join(f'{{{p}}}' for p in sorted(img_dirs))
            packages.append(f'\\graphicspath{{{paths_str}}}')

        preamble = '\n'.join(packages)

        tex = (
            f'\\documentclass[a4paper,12pt]{{article}}\n\n'
            f'{preamble}\n\n'
            f'\\title{{{_escape_latex(self.html_name)}}}\n'
            f'\\author{{}}\n'
            f'\\date{{\\today}}\n\n'
            f'\\begin{{document}}\n'
            f'\\maketitle\n\n'
            f'{body}\n'
            f'\\end{{document}}\n'
        )
        return tex


# ============================================================
# XeLaTeX compilation (reused from md2tex)
# ============================================================

def compile_tex(tex_path, runs=2):
    """Compile .tex to .pdf using XeLaTeX."""
    tex_dir = os.path.dirname(os.path.abspath(tex_path))
    tex_name = os.path.basename(tex_path)

    for run in range(runs):
        print(f"XeLaTeX 编译第 {run+1} 遍...")
        result = subprocess.run(
            ['xelatex', '-interaction=nonstopmode', '-halt-on-error', tex_name],
            cwd=tex_dir,
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=120
        )
        if result.returncode != 0:
            errors = [l for l in result.stdout.split('\n') if l.startswith('!')]
            if errors:
                print(f"编译错误: {errors[0]}")
            else:
                print(f"编译失败 (返回码 {result.returncode})")
            return False

    return True


# ============================================================
# CLI entry point
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='HTML to LaTeX + PDF converter')
    parser.add_argument('input', help='Input HTML file')
    parser.add_argument('--output-dir', help='Output directory (default: same as input)')
    parser.add_argument('--no-compile', action='store_true',
                        help='Only generate .tex, skip PDF compilation')
    args = parser.parse_args()

    html_path = args.input
    if not os.path.exists(html_path):
        print(f"ERROR: File not found: {html_path}")
        sys.exit(1)

    # Convert
    converter = Html2TexConverter(html_path, args.output_dir)
    tex_content = converter.convert()

    # Write .tex
    output_dir = args.output_dir or os.path.dirname(os.path.abspath(html_path))
    os.makedirs(output_dir, exist_ok=True)

    tex_path = os.path.join(output_dir, f'{converter.html_name}.tex')
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(tex_content)
    print(f"LaTeX 已生成: {tex_path}")

    # Compile
    if not args.no_compile:
        pdf_path = os.path.join(output_dir, f'{converter.html_name}.pdf')
        success = compile_tex(tex_path)
        if success and os.path.exists(pdf_path):
            print(f"PDF 已生成: {pdf_path}")
        else:
            print("PDF 编译失败，请检查 .tex 文件")

    # Clean auxiliary files
    for ext in ['.aux', '.log', '.out', '.toc']:
        aux = os.path.join(output_dir, f'{converter.html_name}{ext}')
        if os.path.exists(aux):
            os.remove(aux)


if __name__ == '__main__':
    main()
