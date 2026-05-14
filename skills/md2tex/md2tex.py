"""
md2tex.py — Markdown to LaTeX + PDF converter (XeLaTeX + ctex)

Usage:
    python md2tex.py <input.md> [--output-dir DIR] [--no-compile]

Output:
    <input>.tex  — LaTeX source (XeLaTeX + ctex)
    <input>.pdf  — Compiled PDF (via xelatex)
"""

import sys
import os
import re
import shutil
import subprocess
import argparse
from pathlib import Path


# ============================================================
# Markdown → LaTeX 转换器
# ============================================================

class Md2TexConverter:
    def __init__(self, md_path, output_dir=None):
        self.md_path = os.path.abspath(md_path)
        self.md_dir = os.path.dirname(self.md_path)
        self.md_name = Path(md_path).stem
        self.output_dir = os.path.abspath(output_dir) if output_dir else self.md_dir

        with open(self.md_path, 'r', encoding='utf-8') as f:
            self.md_text = f.read()

        self.images = []       # 收集所有图片引用
        self.has_table = False
        self.has_math = False
        self.has_code = False

    def convert(self):
        """主转换流程"""
        lines = self.md_text.split('\n')
        body_parts = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # 空行
            if line.strip() == '':
                i += 1
                continue

            # 代码块 ```
            if line.strip().startswith('```'):
                code_lines, i = self._parse_code_block(lines, i)
                body_parts.append(code_lines)
                continue

            # 数学块 $$...$$
            if line.strip().startswith('$$'):
                math_lines, i = self._parse_math_block(lines, i)
                body_parts.append(math_lines)
                continue

            # 表格
            if line.strip().startswith('|') and '|' in line.strip()[1:]:
                table_lines, i = self._parse_table(lines, i)
                body_parts.append(table_lines)
                continue

            # 图片
            img_match = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', line.strip())
            if img_match:
                body_parts.append(self._convert_image(img_match.group(1), img_match.group(2)))
                i += 1
                continue

            # 标题
            heading_match = re.match(r'^(#{1,4})\s+(.+)', line)
            if heading_match:
                level = len(heading_match.group(1))
                title = self._escape_latex(heading_match.group(2).strip())
                # 清理加粗标记
                title = title.replace('\\textbf{', '').replace('}', '')
                body_parts.append(self._convert_heading(level, title))
                i += 1
                continue

            # 水平线
            if re.match(r'^---+$', line.strip()):
                body_parts.append('\n\\vspace{0.5em}\\noindent\\rule{\\textwidth}{0.4pt}\\vspace{0.5em}\n')
                i += 1
                continue

            # 普通段落
            para_lines, i = self._parse_paragraph(lines, i)
            body_parts.append(para_lines)
            continue

        return self._assemble_document(body_parts)

    # --- 解析器 ---

    def _parse_code_block(self, lines, start):
        lang = lines[start].strip()[3:].strip()
        code_lines = []
        i = start + 1
        while i < len(lines) and not lines[i].strip().startswith('```'):
            code_lines.append(lines[i])
            i += 1
        i += 1  # skip closing ```

        self.has_code = True
        code = '\n'.join(code_lines)
        code = self._escape_latex(code)
        lang_cmd = f'[language={lang}]' if lang else ''
        return f'\\begin{{lstlisting}}{lang_cmd}\n{code}\n\\end{{lstlisting}}\n', i

    def _parse_math_block(self, lines, start):
        # 单行 $$ 或多行 $$
        line = lines[start].strip()
        if line == '$$':
            # 多行模式
            math_lines = []
            i = start + 1
            while i < len(lines) and lines[i].strip() != '$$':
                math_lines.append(lines[i])
                i += 1
            i += 1  # skip closing $$
            math_content = '\n'.join(math_lines)
        else:
            # 单行 $$...$$
            math_content = line[2:]
            if math_content.endswith('$$'):
                math_content = math_content[:-2]
            i = start + 1

        self.has_math = True
        return f'\\[\n{math_content.strip()}\n\\]\n', i

    def _parse_table(self, lines, start):
        # 收集所有连续的表格行
        table_lines = []
        i = start
        while i < len(lines) and lines[i].strip().startswith('|'):
            row = lines[i].strip()
            cells = [c.strip() for c in row.split('|')[1:-1]]
            # 跳过分隔行
            if all(re.match(r'^[-:]+$', c) for c in cells):
                i += 1
                continue
            table_lines.append(cells)
            i += 1

        if len(table_lines) < 1:
            return '', i

        self.has_table = True
        num_cols = max(len(row) for row in table_lines)
        col_spec = '|' + '|'.join(['c'] * num_cols) + '|'

        tex_lines = [f'\\begin{{tabular}}{{{col_spec}}}']
        tex_lines.append('\\hline')

        for ri, row in enumerate(table_lines):
            # 补齐列数
            while len(row) < num_cols:
                row.append('')
            # 转义每个单元格
            escaped = [self._escape_latex(c) for c in row]
            tex_lines.append(' & '.join(escaped) + ' \\\\')
            tex_lines.append('\\hline')

        tex_lines.append('\\end{tabular}')

        # 包裹在 center 环境中
        result = '\\begin{center}\n' + '\n'.join(tex_lines) + '\n\\end{center}\n'
        return result, i

    def _parse_paragraph(self, lines, start):
        para_lines = []
        i = start
        while i < len(lines):
            line = lines[i]
            if line.strip() == '' or line.strip().startswith('|') or line.strip().startswith('#') or \
               line.strip().startswith('```') or line.strip().startswith('$$') or \
               line.strip().startswith('![') or line.strip().startswith('---'):
                break
            para_lines.append(line)
            i += 1

        text = ' '.join(para_lines).strip()
        if not text:
            return '', i

        # 处理行内格式
        text = self._convert_inline(text)
        return f'{text}\n\n', i

    # --- 转换器 ---

    def _convert_heading(self, level, title):
        # 清理标题中的特殊字符
        title = re.sub(r'\*\*(.+?)\*\*', r'\1', title)
        title = re.sub(r'\*(.+?)\*', r'\1', title)

        if level == 1:
            return f'\\section{{{title}}}\n'
        elif level == 2:
            return f'\\subsection{{{title}}}\n'
        elif level == 3:
            return f'\\subsubsection{{{title}}}\n'
        else:
            return f'\\paragraph{{{title}}}\n'

    def _convert_image(self, alt, path):
        # 处理相对路径
        full_path = os.path.join(self.md_dir, path)
        if not os.path.isabs(path):
            # 使用相对于 output_dir 的路径
            try:
                rel_path = os.path.relpath(full_path, self.output_dir)
            except ValueError:
                rel_path = path
        else:
            rel_path = path

        # 统一使用正斜杠 (LaTeX 要求)
        rel_path = rel_path.replace('\\', '/')

        self.images.append((alt, rel_path, full_path))
        alt_escaped = self._escape_latex(alt)
        return (f'\\begin{{figure}}[htbp]\n'
                f'  \\centering\n'
                f'  \\includegraphics[width=0.85\\textwidth]{{{rel_path}}}\n'
                f'  \\caption{{{alt_escaped}}}\n'
                f'\\end{{figure}}\n')

    def _convert_inline(self, text):
        # 行内数学 $...$
        def math_repl(m):
            self.has_math = True
            return f'${m.group(1)}$'
        text = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', math_repl, text)

        # 加粗 **...**
        text = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', text)
        # 斜体 *...*
        text = re.sub(r'\*(.+?)\*', r'\\textit{\1}', text)
        # 行内代码 `...`
        text = re.sub(r'`([^`]+)`', r'\\texttt{\1}', text)

        # 转义特殊字符（但保留已转换的命令）
        text = self._escape_latex_partial(text)

        return text

    def _escape_latex(self, text):
        """完全转义 LaTeX 特殊字符"""
        text = text.replace('\\', '\\textbackslash{}')
        for old, new in [('&', '\\&'), ('%', '\\%'), ('$', '\\$'),
                         ('#', '\\#'), ('_', '\\_'), ('{', '\\{'),
                         ('}', '\\}'), ('~', '\\textasciitilde{}'),
                         ('^', '\\textasciicircum{}')]:
            text = text.replace(old, new)
        return text

    def _escape_latex_partial(self, text):
        """部分转义：保留已生成的 LaTeX 命令"""
        # 先标记已有的 LaTeX 命令
        commands = []
        def save_cmd(m):
            commands.append(m.group(0))
            return f'__CMD{len(commands)-1}__'
        text = re.sub(r'\\(?:textbf|textit|texttt|textbackslash|textasciitilde|textasciicircum)\{[^}]*\}', save_cmd, text)
        text = re.sub(r'\\\$', save_cmd, text)
        text = re.sub(r'\$[^$]+\$', save_cmd, text)

        # 转义剩余的
        for old, new in [('&', '\\&'), ('%', '\\%'), ('#', '\\#'),
                         ('~', '\\textasciitilde{}'), ('^', '\\textasciicircum{}')]:
            text = text.replace(old, new)

        # 恢复命令
        for idx, cmd in enumerate(commands):
            text = text.replace(f'__CMD{idx}__', cmd)

        return text

    # --- 文档组装 ---

    def _assemble_document(self, body_parts):
        body = '\n'.join(body_parts)

        # preamble
        packages = []
        packages.append(r'\usepackage[UTF8]{ctex}')
        packages.append(r'\usepackage{graphicx}')
        packages.append(r'\usepackage{booktabs}')
        packages.append(r'\usepackage{amsmath}')
        packages.append(r'\usepackage{amssymb}')
        packages.append(r'\usepackage[margin=2.5cm]{geometry}')
        packages.append(r'\usepackage{hyperref}')

        if self.has_code:
            packages.append(r'\usepackage{listings}')
            packages.append(r'\lstset{basicstyle=\ttfamily\small, breaklines=true, frame=single}')

        if self.has_table:
            packages.append(r'\usepackage{array}')
            packages.append(r'\usepackage{longtable}')

        # 图片搜索路径
        img_paths = set()
        for alt, rel, full in self.images:
            img_dir = os.path.dirname(rel)
            if img_dir:
                img_paths.add(img_dir)
        if img_paths:
            paths_str = ', '.join(f'{{{p}}}' for p in img_paths)
            packages.append(f'\\graphicspath{{{paths_str}}}')

        preamble = '\n'.join(packages)

        tex = (
            f'\\documentclass[a4paper,12pt]{{article}}\n\n'
            f'{preamble}\n\n'
            f'\\title{{{{{self._escape_latex(self.md_name)}}}}}\n'
            f'\\author{{}}\n'
            f'\\date{{\\today}}\n\n'
            f'\\begin{{document}}\n'
            f'\\maketitle\n\n'
            f'{body}\n'
            f'\\end{{document}}\n'
        )
        return tex


# ============================================================
# XeLaTeX 编译
# ============================================================

def compile_tex(tex_path, runs=2):
    """用 XeLaTeX 编译 .tex 文件"""
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
            # 提取错误信息
            errors = [l for l in result.stdout.split('\n') if l.startswith('!')]
            if errors:
                print(f"编译错误: {errors[0]}")
            else:
                print(f"编译失败 (返回码 {result.returncode})")
            return False

    return True


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='Markdown to LaTeX + PDF converter')
    parser.add_argument('input', help='Input Markdown file')
    parser.add_argument('--output-dir', help='Output directory (default: same as input)')
    parser.add_argument('--no-compile', action='store_true', help='Only generate .tex, skip PDF compilation')
    args = parser.parse_args()

    md_path = args.input
    if not os.path.exists(md_path):
        print(f"ERROR: File not found: {md_path}")
        sys.exit(1)

    # 转换
    converter = Md2TexConverter(md_path, args.output_dir)
    tex_content = converter.convert()

    # 输出路径
    output_dir = args.output_dir or os.path.dirname(os.path.abspath(md_path))
    os.makedirs(output_dir, exist_ok=True)

    tex_path = os.path.join(output_dir, f'{converter.md_name}.tex')
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(tex_content)
    print(f"LaTeX 已生成: {tex_path}")

    # 编译
    if not args.no_compile:
        pdf_path = os.path.join(output_dir, f'{converter.md_name}.pdf')
        success = compile_tex(tex_path)
        if success and os.path.exists(pdf_path):
            print(f"PDF 已生成: {pdf_path}")
        else:
            print("PDF 编译失败，请检查 .tex 文件")

    # 清理辅助文件
    for ext in ['.aux', '.log', '.out', '.toc']:
        aux = os.path.join(output_dir, f'{converter.md_name}{ext}')
        if os.path.exists(aux):
            os.remove(aux)


if __name__ == '__main__':
    main()
