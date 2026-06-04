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
        self.image_counter = 0
        self.has_table = False
        self.has_math = False
        self.has_code = False
        self.has_color = False
        self.has_wrapfig = False


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

            # 列表（支持缩进子项）
            if re.match(r'^\s*[-*]\s+', line):
                list_block, i = self._parse_list(lines, i)
                body_parts.append(list_block)
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
        # 固定比例列宽，避免长文本导致 Overfull
        if num_cols == 4:
            col_spec = r'|p{0.10\textwidth}|p{0.10\textwidth}|p{0.30\textwidth}|p{0.40\textwidth}|'
        elif num_cols == 3:
            col_spec = r'|p{0.16\textwidth}|p{0.24\textwidth}|p{0.52\textwidth}|'
        else:
            each = 0.88 / max(num_cols, 1)
            col_spec = '|' + '|'.join([f'p{{{each:.3f}\\textwidth}}' for _ in range(num_cols)]) + '|'

        tex_lines = [r'\setlength{\tabcolsep}{4pt}', r'\renewcommand{\arraystretch}{1.15}', f'\\begin{{tabular}}{{{col_spec}}}']
        tex_lines.append('\\hline')

        for ri, row in enumerate(table_lines):
            # 补齐列数
            while len(row) < num_cols:
                row.append('')
            # 单元格也按行内规则处理（支持 $...$、【红】...【/红】）
            escaped = [self._convert_inline(c) for c in row]
            tex_lines.append(' & '.join(escaped) + ' \\\\')
            tex_lines.append('\\hline')

        tex_lines.append('\\end{tabular}')

        # 包裹在 center 环境中
        result = '\\begin{center}\n\\small\n' + '\n'.join(tex_lines) + '\n\\normalsize\n\\end{center}\n'
        return result, i

    def _parse_paragraph(self, lines, start):
        para_lines = []
        i = start
        while i < len(lines):
            line = lines[i]
            if line.strip() == '' or line.strip().startswith('|') or line.strip().startswith('#') or \
               line.strip().startswith('```') or line.strip().startswith('$$') or \
               line.strip().startswith('![') or line.strip().startswith('---') or \
               re.match(r'^\s*[-*]\s+', line):
                break
            para_lines.append(line)
            i += 1

        text = ' '.join(para_lines).strip()
        if not text:
            return '', i

        # 处理行内格式
        text = self._convert_inline(text)
        return f'{text}\n\n', i

    def _parse_list(self, lines, start):
        out = []
        out.append('\\begin{itemize}')
        i = start
        in_sub = False
        seen_top_item = False

        while i < len(lines):
            line = lines[i]
            if line.strip() == '':
                i += 1
                continue
            m = re.match(r'^(\s*)[-*]\s+(.+)$', line)
            if not m:
                break
            indent = len(m.group(1).replace('\t', '    '))
            item_text = self._convert_inline(m.group(2).strip())

            # 如果列表块开头就是缩进子项（常见于图片/段落打断后），降级为顶层项
            if indent >= 2 and not seen_top_item:
                indent = 0

            if indent >= 2 and not in_sub:
                out.append('\\begin{itemize}')
                in_sub = True
            if indent < 2 and in_sub:
                out.append('\\end{itemize}')
                in_sub = False

            out.append(f'\\item {item_text}')
            if indent < 2:
                seen_top_item = True
            i += 1

        if in_sub:
            out.append('\\end{itemize}')
        out.append('\\end{itemize}')
        return '\n'.join(out) + '\n', i

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
        # 处理相对路径并复制到 ASCII 目录，避免 LaTeX 对中文路径报错
        full_path = path if os.path.isabs(path) else os.path.join(self.md_dir, path)
        assets_dir = os.path.join(self.output_dir, 'md2tex_assets')
        os.makedirs(assets_dir, exist_ok=True)
        ext = os.path.splitext(full_path)[1].lower() or '.png'
        self.image_counter += 1
        new_name = f'img_{self.image_counter:03d}{ext}'
        dst_path = os.path.join(assets_dir, new_name)
        try:
            shutil.copy2(full_path, dst_path)
            rel_path = os.path.relpath(dst_path, self.output_dir).replace('\\', '/')
        except Exception:
            rel_path = (path if path else full_path).replace('\\', '/')

        self.images.append((alt, rel_path, full_path))
        alt_escaped = self._escape_latex(alt)
        self.has_wrapfig = True
        # 优先使用右侧环绕图，尽量利用空白区域；由 LaTeX 自动避免遮挡正文
        return (f'\\begin{{wrapfigure}}{{r}}{{0.42\\textwidth}}\n'
                f'  \\vspace{{-0.6em}}\n'
                f'  \\centering\n'
                f'  \\includegraphics[width=0.4\\textwidth]{{{rel_path}}}\n'
                f'  \\caption{{{alt_escaped}}}\n'
                f'  \\vspace{{-0.8em}}\n'
                f'\\end{{wrapfigure}}\n')

    def _convert_inline(self, text):
        # 红色关键公式标记：默认按数学公式处理
        def red_repl(m):
            self.has_color = True
            content = m.group(1).strip()
            # 兼容两种写法：
            # 1) 【红】a+b【/红】
            # 2) 【红】$a+b$【/红】
            if content.startswith('$') and content.endswith('$') and len(content) >= 2:
                content = content[1:-1].strip()
            return f'\\textcolor{{red}}{{${content}$}}'
        text = re.sub(r'【红】(.*?)【/红】', red_repl, text)

        # 保护代码段，避免被 * 强调误伤
        code_spans = []
        def hold_code(m):
            code_spans.append(m.group(1))
            return f'__CODE{len(code_spans)-1}__'
        text = re.sub(r'`([^`]+)`', hold_code, text)

        # 行内数学 $...$
        def math_repl(m):
            self.has_math = True
            return f'${m.group(1)}$'
        text = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', math_repl, text)

        # 加粗 **...**
        text = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', text)
        # 斜体 *...*
        text = re.sub(r'(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)', r'\\textit{\1}', text)

        # 转义特殊字符（但保留已转换的命令）
        text = self._escape_latex_partial(text)

        # 恢复代码段
        for idx, code in enumerate(code_spans):
            code_esc = self._escape_latex(code)
            text = text.replace(f'__CODE{idx}__', f'\\texttt{{{code_esc}}}')

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
        """部分转义：不破坏已生成的 LaTeX 结构"""
        for old, new in [('&', '\\&'), ('%', '\\%'), ('#', '\\#'),
                         ('~', '\\textasciitilde{}'), ('^', '\\textasciicircum{}')]:
            text = text.replace(old, new)
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
        if self.has_color:
            packages.append(r'\usepackage{xcolor}')

        if self.has_code:
            packages.append(r'\usepackage{listings}')
            packages.append(r'\lstset{basicstyle=\ttfamily\small, breaklines=true, frame=single}')
        if self.has_wrapfig:
            packages.append(r'\usepackage{wrapfig}')

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

