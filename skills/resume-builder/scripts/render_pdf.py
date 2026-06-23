#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_pdf.py —— resume.html → resume.pdf（Chrome/Edge 无头打印，无需 LaTeX）

用法:
    python render_pdf.py <输入.html> [输出.pdf] [--browser PATH]

纸张(A4)与边距由 HTML 模板里的 @page CSS 决定，本脚本只负责调用浏览器打印。
浏览器探测逻辑抄自同机已验证可用的 html2pdf skill，保证本 skill 自包含。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

BROWSER_CANDIDATES = [
    # Windows
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    # macOS
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
    # Linux
    Path("/usr/bin/google-chrome"),
    Path("/usr/bin/google-chrome-stable"),
    Path("/usr/bin/chromium"),
    Path("/usr/bin/chromium-browser"),
    Path("/usr/bin/microsoft-edge"),
]


def detect_browser(explicit):
    if explicit:
        p = Path(explicit)
        if p.exists():
            return p
        raise FileNotFoundError(f"指定的浏览器不存在: {p}")
    for c in BROWSER_CANDIDATES:
        if c.exists():
            return c
    raise FileNotFoundError(
        "未找到 Chrome 或 Edge。请安装其一，或用 --browser 指定可执行文件路径。"
    )


def file_url(path: Path) -> str:
    resolved = str(path.resolve()).replace("\\", "/")
    return "file:///" + quote(resolved, safe="/:._-")


def count_pages(pdf_path: Path):
    try:
        from PyPDF2 import PdfReader  # type: ignore
        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        return None


def print_to_pdf(browser: Path, html_path: Path, pdf_path: Path) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    # Chrome headless 对相对输出路径的解析不以继承 CWD 为准，必须用绝对路径，
    # 否则会静默 exit 0 却不落盘。
    abs_pdf = pdf_path.resolve()
    common_args = [
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={abs_pdf}",
        file_url(html_path),
    ]
    # 优先新版无头；旧版 Chrome/部分 Edge 仅支持 --headless(老)，失败则回退
    for headless_flag in ("--headless=new", "--headless"):
        cmd = [str(browser), headless_flag] + common_args
        try:
            subprocess.run(cmd, check=True)
            return
        except subprocess.CalledProcessError:
            continue
    raise RuntimeError("浏览器打印失败，请检查 Chrome/Edge 是否可用。")


def main() -> int:
    ap = argparse.ArgumentParser(description="HTML 简历 → PDF（无头浏览器，无需 LaTeX）。")
    ap.add_argument("input_html", help="输入 HTML 路径")
    ap.add_argument("output_pdf", nargs="?", help="输出 PDF 路径（默认同名 .pdf）")
    ap.add_argument("--browser", help="显式指定浏览器可执行文件路径")
    args = ap.parse_args()

    html_path = Path(args.input_html)
    if not html_path.exists():
        print(f"输入 HTML 不存在: {html_path}", file=sys.stderr)
        return 1

    pdf_path = Path(args.output_pdf) if args.output_pdf else html_path.with_suffix(".pdf")

    try:
        browser = detect_browser(args.browser)
        print_to_pdf(browser, html_path, pdf_path)
    except Exception as exc:
        print(f"PDF 生成失败: {exc}", file=sys.stderr)
        return 1

    pages = count_pages(pdf_path)
    print(f"PDF 已生成: {pdf_path.resolve()}")
    print(f"使用浏览器: {browser.name}")
    if pages is not None:
        print(f"页数: {pages}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
