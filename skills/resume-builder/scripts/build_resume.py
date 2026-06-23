#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_resume.py —— 简历数据(YAML/JSON) → 填充 HTML 模板 → resume.html

用法:
    python build_resume.py <数据文件.yaml|json> [--template classic_single] [--out resume.html]

模板 token 契约 (templates/classic_single.html):
    <!--HEADER--> <!--EDUCATION--> <!--PROJECTS--> <!--LAB-->
    <!--CLUBS_COMPETITIONS--> <!--SKILLS--> <!--SOCIAL-->
本脚本逐板块生成 HTML 片段并替换对应 token；无数据的板块自动消失。
"""

from __future__ import annotations

import argparse
import json
import sys
from html import escape
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_DIR / "templates"


# ---------- 工具 ----------
def esc(s) -> str:
    """HTML 转义，None/数字安全处理。"""
    if s is None:
        return ""
    return escape(str(s), quote=False)


def date_range(start, end) -> str:
    """'2023.09 – 至今'；只有一边时只显示那一边。"""
    s = esc(start)
    e = esc(end)
    if s and e:
        return f"{s} – {e}"
    return s or e


def render_entry_head(title: str, date: str) -> str:
    return (
        f'<div class="r-entry-head">'
        f'<span class="r-title">{esc(title)}</span>'
        f'<span class="r-date">{esc(date)}</span>'
        f"</div>"
    )


def section(title: str, body: str) -> str:
    if not body.strip():
        return ""
    return (
        f'<section class="r-section">'
        f'<h2 class="r-section-title">{title}</h2>'
        f'<div class="r-entries">{body}</div>'
        f"</section>"
    )


# ---------- 各板块 ----------
def render_header(p: dict) -> str:
    if not p:
        return ""
    name = esc(p.get("name_cn", ""))
    if not name:
        return ""
    name_html = f'<h1 class="r-name">{name}'
    en = p.get("name_en", "")
    if en and str(en).strip():
        name_html += f'<span class="en">{esc(en)}</span>'
    name_html += "</h1>"

    bits = []
    if p.get("phone"):
        bits.append(f"电话: {esc(p['phone'])}")
    if p.get("email"):
        bits.append(f"邮箱: {esc(p['email'])}")
    contact = f'<div class="r-contact">{"&nbsp;&nbsp;".join(bits)}</div>' if bits else ""

    address = ""
    if p.get("address"):
        address = f'<div class="r-address">地址: {esc(p["address"])}</div>'

    target = ""
    if p.get("target"):
        target = f'<div class="r-target"><strong>求职意向：</strong>{esc(p["target"])}</div>'

    return f'<header class="r-header">{name_html}{contact}{address}{target}</header>'


def render_education(items) -> str:
    if not items:
        return ""
    out = []
    for e in items:
        if not isinstance(e, dict) or e.get("optional"):
            continue
        school = e.get("school", "")
        if not school:
            continue
        head = render_entry_head(school, date_range(e.get("start"), e.get("end")))

        major = esc(e.get("major", ""))
        sub = f'<div class="r-sub"><span>{major}</span>'
        if e.get("city"):
            sub += f'<span class="city">{esc(e["city"])}</span>'
        sub += "</div>"

        detail_bits = []
        if e.get("gpa"):
            detail_bits.append(esc(e["gpa"]))
        if e.get("courses"):
            detail_bits.append(esc(e["courses"]))
        detail = f'<div class="r-detail">{"&nbsp;&nbsp;".join(detail_bits)}</div>' if detail_bits else ""

        out.append(f'<div class="r-entry">{head}{sub}{detail}</div>')
    if not out:
        return ""
    return section("教育背景", "\n".join(out))


def render_bullets(item) -> str:
    """把 item['bullets'] 列表渲染成项目符号 <ul>；无则空串。"""
    bullets = item.get("bullets") if isinstance(item, dict) else None
    if not isinstance(bullets, list) or not bullets:
        return ""
    items_html = "".join(
        f"<li>{esc(str(b).strip())}</li>" for b in bullets if str(b).strip()
    )
    return f'<ul class="r-bullets">{items_html}</ul>' if items_html else ""


def render_projects(items) -> str:
    if not items:
        return ""
    out = []
    for p in items:
        if not isinstance(p, dict):
            continue
        name = p.get("name", "")
        if not name:
            continue
        head = render_entry_head(name, date_range(p.get("start"), p.get("end")))

        role = ""
        if str(p.get("role", "")).strip():
            role = f'<div class="r-role">{esc(p["role"])}</div>'

        # 描述行：desc：tech。details。（沿用原 .tex 的中文标点风格；任一为空自动省略）
        desc = str(p.get("desc", "")).strip()
        tech = str(p.get("tech", "")).strip()
        details = str(p.get("details", "")).strip()
        text = desc
        if tech:
            text = f"{text}：{tech}" if text else tech
        if details:
            text = f"{text}。{details}" if text else details
        detail = f'<div class="r-detail">{esc(text)}</div>' if text else ""

        # 项目符号要点列表（可选；与 desc 互不冲突，有则追加）
        bullets = render_bullets(p)

        out.append(f'<div class="r-entry">{head}{role}{detail}{bullets}</div>')
    if not out:
        return ""
    return section("核心科研与项目经历", "\n".join(out))


def render_lab(items) -> str:
    if not items:
        return ""
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        name = it.get("name", "")
        if not name:
            continue
        head = render_entry_head(name, date_range(it.get("start"), it.get("end")))
        desc = ""
        if str(it.get("desc", "")).strip():
            desc = f'<div class="r-detail">{esc(it["desc"])}</div>'
        bullets = render_bullets(it)
        out.append(f'<div class="r-entry">{head}{desc}{bullets}</div>')
    if not out:
        return ""
    return section("实验室经历", "\n".join(out))


def render_clubs_competitions(clubs, comps) -> str:
    out = []
    for c in clubs or []:
        if not isinstance(c, dict):
            continue
        name = c.get("name", "")
        if not name:
            continue
        head = render_entry_head(name, date_range(c.get("start"), c.get("end")))
        role = ""
        if str(c.get("role", "")).strip():
            role = f'<div class="r-role">{esc(c["role"])}</div>'
        desc = ""
        if str(c.get("desc", "")).strip():
            desc = f'<div class="r-detail">{esc(c["desc"])}</div>'
        bullets = render_bullets(c)
        out.append(f'<div class="r-entry">{head}{role}{desc}{bullets}</div>')

    for c in comps or []:
        if not isinstance(c, dict):
            continue
        name = c.get("name", "")
        if not name:
            continue
        head = render_entry_head(name, esc(c.get("date", "")))
        desc = ""
        if str(c.get("desc", "")).strip():
            desc = f'<div class="r-detail">{esc(c["desc"])}</div>'
        bullets = render_bullets(c)
        out.append(f'<div class="r-entry">{head}{desc}{bullets}</div>')

    if not out:
        return ""
    return section("社团与竞赛经历", "\n".join(out))


SKILL_LABELS = {
    "software": "专业软件",
    "languages": "编程语言",
    "hardware": "硬件平台",
    "languages_spoken": "语言",
    "eda_tools": "EDA 工具",
    "professional": "专业能力",
    "ai_tools": "AI 工具",
    "tools": "工具",
    "frameworks": "框架",
    "certificates": "证书",
}


def _humanize_label(key: str) -> str:
    return key.replace("_", " ").capitalize()


def render_skills(sk) -> str:
    if not sk or not isinstance(sk, dict):
        return ""
    out = []
    for key, val in sk.items():  # 保留 YAML 中的书写顺序
        v = str(val).strip() if val else ""
        if not v:
            continue
        label = SKILL_LABELS.get(key) or _humanize_label(key)
        out.append(f'<div class="r-skill-row"><span class="label">{esc(label)}：</span>{esc(v)}</div>')
    if not out:
        return ""
    return section("技能储备", "\n".join(out))


def render_social(sp) -> str:
    if not sp:
        return ""
    org = str(sp.get("org", "")).strip()
    desc = str(sp.get("desc", "")).strip()
    if not (org or desc):
        return ""
    body = ""
    if org:
        body += f'<div class="r-title">{esc(org)}</div>'
    if desc:
        body += f'<div class="r-detail" style="margin-top:2px">{esc(desc)}</div>'
    return section("社会实践", body)


# ---------- 数据加载 ----------
def load_data(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".json":
        return json.loads(text)
    # yaml/yml 或其它：优先 yaml，无 PyYAML 则尝试 json
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except ImportError:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            sys.exit(
                "无法解析数据文件：未安装 PyYAML 且内容不是合法 JSON。\n"
                "解决：pip install pyyaml，或把数据另存为 .json。"
            )


# ---------- 主流程 ----------
def parse_args():
    ap = argparse.ArgumentParser(description="简历数据(YAML/JSON) → HTML + PDF（一条命令，无需 LaTeX）。")
    ap.add_argument("data", help="数据文件路径 (.yaml/.yml/.json)")
    ap.add_argument("--template", default="classic_single", help="模板名(templates 目录下)或绝对路径")
    ap.add_argument("--out", default="resume.html", help="输出 HTML 路径")
    ap.add_argument("--pdf", default=None, help="输出 PDF 路径（默认与 HTML 同名 .pdf）")
    ap.add_argument("--no-pdf", action="store_true", help="只生成 HTML，不自动出 PDF")
    return ap.parse_args()


def resolve_template(name: str) -> Path:
    p = Path(name)
    if p.is_absolute() or p.exists():
        return p
    candidate = TEMPLATES_DIR / (name if name.endswith(".html") else f"{name}.html")
    if candidate.exists():
        return candidate
    sys.exit(f"找不到模板: {name}（在 {TEMPLATES_DIR} 下也没找到）")


def render_pdf_for(html_path: Path, pdf_arg) -> None:
    """best-effort 自动 HTML→PDF。失败不影响已生成的 HTML。"""
    pdf_path = Path(pdf_arg) if pdf_arg else html_path.with_suffix(".pdf")
    try:
        from render_pdf import count_pages, detect_browser, print_to_pdf
    except Exception as e:  # 模块加载失败
        print(f"⚠️ 无法加载渲染模块 render_pdf：{e}", file=sys.stderr)
        return
    try:
        browser = detect_browser(None)
        print_to_pdf(browser, html_path, pdf_path)
        pages = count_pages(pdf_path)
        print(f"PDF 已生成: {pdf_path.resolve()}")
        if pages is not None:
            print(f"页数: {pages}")
    except FileNotFoundError as e:
        print(f"⚠️ 未生成 PDF（找不到 Chrome/Edge）：{e}", file=sys.stderr)
        print("   可在浏览器打开 HTML 后「打印 → 另存为 PDF」。", file=sys.stderr)
    except Exception as e:
        print(f"⚠️ PDF 生成失败：{e}", file=sys.stderr)
        print("   HTML 已生成，可手动打印为 PDF。", file=sys.stderr)


def main() -> int:
    args = parse_args()
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"数据文件不存在: {data_path}", file=sys.stderr)
        return 1

    data = load_data(data_path)

    html = resolve_template(args.template).read_text(encoding="utf-8")

    replacements = {
        "<!--HEADER-->": render_header(data.get("personal", {})),
        "<!--EDUCATION-->": render_education(data.get("education")),
        "<!--PROJECTS-->": render_projects(data.get("projects")),
        "<!--LAB-->": render_lab(data.get("lab_experience")),
        "<!--CLUBS_COMPETITIONS-->": render_clubs_competitions(
            data.get("clubs"), data.get("competitions")
        ),
        "<!--SKILLS-->": render_skills(data.get("skills")),
        "<!--SOCIAL-->": render_social(data.get("social_practice")),
    }
    for token, value in replacements.items():
        html = html.replace(token, value)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"HTML 已生成: {out_path.resolve()}")
    print(f"模板: {args.template}")

    # 一条命令自动出 PDF（开箱即用）；--no-pdf 可跳过
    if not args.no_pdf:
        render_pdf_for(out_path, args.pdf)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
