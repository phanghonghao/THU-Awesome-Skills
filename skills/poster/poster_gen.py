#!/usr/bin/env python3
"""从沙龙 Markdown 生成 A4 海报 (Playwright + HTML/CSS + Jinja2).

用法:
  python poster_gen.py input.md                       # 生成 .html
  python poster_gen.py input.md --pdf                  # 生成 .html + .pdf
  python poster_gen.py input.md -o poster.html --pdf   # 指定输出路径

输入 MD 格式:
  【标题】
  日期：...
  时间：...
  分享人：
  1. 姓名 主题描述
  ...
  logo：![alt text](path/to/logo.jpg)
  姓名：![alt text](path/to/photo.jpg)
"""

import argparse
import re
import sys
from pathlib import Path

from jinja2 import Template


# ── MD 解析 (与 LaTeX 版相同逻辑) ────────────────────────────────────

def parse_md(md_text, md_dir):
    """Parse salon MD file into structured dict."""
    data = {
        "title": "",
        "club": "",
        "date": "",
        "time": "",
        "format": "",
        "speakers": [],
        "logo": "",
        "meeting_link": "",
        "meeting_id": "",
        "team_name": "",
        "vision": "",
        "tracks": "",
        "recruitment": "",
        "highlight": "",
        "github": "",
        "feishu": "",
        "huggingface": "",
    }

    lines = md_text.strip().split("\n")
    photo_map = {}

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        m = re.match(r'^【(.+?)】', line_stripped)
        if m:
            data["title"] = m.group(1)
            continue

        m = re.match(r'^社团[：:]\s*(.+)', line_stripped)
        if m:
            data["club"] = m.group(1).strip()
            continue

        m = re.match(r'^日期[：:]\s*(.+)', line_stripped)
        if m:
            data["date"] = m.group(1).strip()
            continue

        m = re.match(r'^时间[：:]\s*(.+)', line_stripped)
        if m:
            data["time"] = m.group(1).strip()
            continue

        m = re.match(r'^形式[：:]\s*(.+)', line_stripped)
        if m:
            data["format"] = m.group(1).strip()
            continue

        m = re.match(r'^https?://\S+', line_stripped)
        if m:
            data["meeting_link"] = m.group(0)
            continue

        m = re.match(r'^#?腾讯会议[：:]\s*(.+)', line_stripped)
        if m:
            data["meeting_id"] = m.group(1).strip()
            continue

        m = re.match(r'^团队[：:]\s*(.+)', line_stripped)
        if m:
            data["team_name"] = m.group(1).strip()
            continue

        m = re.match(r'^愿景[：:]\s*(.+)', line_stripped)
        if m:
            data["vision"] = m.group(1).strip()
            continue

        m = re.match(r'^赛道[：:]\s*(.+)', line_stripped)
        if m:
            data["tracks"] = m.group(1).strip()
            continue

        m = re.match(r'^招新[：:]\s*(.+)', line_stripped)
        if m:
            data["recruitment"] = m.group(1).strip()
            continue

        m = re.match(r'^亮点[：:]\s*(.+)', line_stripped)
        if m:
            data["highlight"] = m.group(1).strip()
            continue

        for key, label in [("github", "GitHub"), ("feishu", "飞书"), ("huggingface", "HuggingFace")]:
            m = re.match(r'^' + label + r'[：:]\s*(.+)', line_stripped)
            if m:
                val = m.group(1).strip()
                if " | " in val:
                    name, url = val.split(" | ", 1)
                    data[key] = url.strip()
                    data[key + "_name"] = name.strip()
                else:
                    data[key] = val
                continue

        m = re.match(r'^\d+\.\s+(.+)', line_stripped)
        if m:
            content = m.group(1).strip()
            # Extract class info in parentheses: 潘洪浩（机械34）topic
            class_name = ""
            cm = re.match(r'^(.+?)[（(](.+?)[）)]\s*(.*)', content)
            if cm:
                name = cm.group(1).strip()
                class_name = cm.group(2).strip()
                topic = cm.group(3).strip()
            elif ',' in content or '，' in content:
                parts = re.split(r'[，,]\s*', content, maxsplit=1)
                name = parts[0].strip()
                topic = parts[1].strip() if len(parts) > 1 else ""
            elif ' ' in content:
                parts = content.split(' ', 1)
                name = parts[0].strip()
                topic = parts[1].strip() if len(parts) > 1 else ""
            else:
                name = content
                topic = ""
            data["speakers"].append({"name": name, "class": class_name, "topic": topic, "photo": ""})
            continue

        m = re.match(r'^(.+?)[：:]\s*!\[.*?\]\((.+?)\)', line_stripped)
        if m:
            key = m.group(1).strip().lower()
            img_path = m.group(2).strip()
            if key == "logo":
                data["logo"] = img_path
            else:
                photo_map[key] = img_path
            continue

    for speaker in data["speakers"]:
        name_lower = speaker["name"].lower()
        for photo_name, photo_path in photo_map.items():
            if name_lower in photo_name or photo_name in name_lower:
                speaker["photo"] = photo_path
                break

    # Resolve relative paths to absolute file:// URLs
    for sp in data["speakers"]:
        if sp.get("photo"):
            sp["photo"] = _to_file_url(md_dir, sp["photo"])
    if data.get("logo"):
        data["logo"] = _to_file_url(md_dir, data["logo"])

    return data


def _to_file_url(base_dir, rel_path):
    """Convert relative path to file:// URL with forward slashes."""
    abs_path = (Path(base_dir) / rel_path).resolve()
    return abs_path.as_uri()


# ── HTML/CSS 模板 (Jinja2) ───────────────────────────────────────────

HTML_TEMPLATE = Template(r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{{ title }}</title>
<style>
  @page {
    size: A4;
    margin: 0;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    width: 210mm; height: 297mm;
    font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans SC", sans-serif;
    background: #f8fafb;
    overflow: hidden;
    position: relative;
  }

  /* ── Header ───────────────────────────── */
  .header {
    background: linear-gradient(135deg, #0d7377 0%, #0f4c75 50%, #1b262c 100%);
    height: 80mm;
    padding: 8mm 12mm;
    position: relative;
    overflow: hidden;
  }
  .header::before {
    content: '';
    position: absolute;
    top: -30mm; right: -20mm;
    width: 100mm; height: 100mm;
    border-radius: 50%;
    background: rgba(255,255,255,0.04);
  }
  .header::after {
    content: '';
    position: absolute;
    bottom: -40mm; left: -10mm;
    width: 80mm; height: 80mm;
    border-radius: 50%;
    background: rgba(255,255,255,0.03);
  }

  .logo {
    width: 20mm; height: 20mm;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid rgba(255,255,255,0.5);
  }

  .header .dept {
    display: flex;
    align-items: center;
    gap: 3mm;
    margin-bottom: 4mm;
  }
  .header .dept .dept-badge {
    background: rgba(255,255,255,0.15);
    color: rgba(255,255,255,0.95);
    font-size: 9pt;
    font-weight: 700;
    padding: 1mm 4mm;
    border-radius: 2mm;
    letter-spacing: 0.5pt;
  }
  .header .dept .dept-en {
    color: rgba(255,255,255,0.55);
    font-size: 7.5pt;
    font-weight: 400;
    letter-spacing: 0.3pt;
  }

  .header .club-row {
    display: flex;
    align-items: center;
    gap: 4mm;
    margin-bottom: 4mm;
  }
  .header .club-text {
    display: flex;
    flex-direction: column;
    gap: 0.5mm;
  }
  .header .club-text .club-cn {
    color: rgba(255,255,255,0.95);
    font-size: 10pt;
    font-weight: 700;
  }
  .header .club-text .club-en {
    color: rgba(255,255,255,0.65);
    font-size: 8pt;
    font-weight: 400;
    letter-spacing: 0.3pt;
  }

  .header h1 {
    color: #fff;
    font-size: 28pt;
    font-weight: 700;
    letter-spacing: 1pt;
    margin-bottom: 4mm;
  }

  .header .meta {
    color: rgba(255,255,255,0.85);
    font-size: 10pt;
    display: flex;
    flex-wrap: wrap;
    gap: 4mm 8mm;
  }
  .header .meta span {
    display: flex;
    align-items: center;
    gap: 2mm;
  }
  .header .meta .icon {
    display: inline-block;
    width: 10px; height: 10px;
    background: rgba(255,255,255,0.5);
    border-radius: 50%;
    flex-shrink: 0;
  }
  .header .meta .link-text {
    font-size: 8pt;
    color: rgba(255,255,255,0.65);
    word-break: break-all;
  }
  .header .meta a {
    color: rgba(255,255,255,0.85);
    text-decoration: none;
    font-size: 9pt;
  }
  .header .meta a:hover {
    text-decoration: underline;
  }

  /* ── Content ──────────────────────────── */
  .content {
    padding: 6mm 12mm;
  }

  .section-title {
    text-align: center;
    margin-bottom: 5mm;
    position: relative;
  }
  .section-title span {
    font-size: 14pt;
    font-weight: 700;
    color: #0d7377;
    background: #f8fafb;
    padding: 0 4mm;
    position: relative;
    z-index: 1;
  }
  .section-title::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, #0d737744, transparent);
  }

  /* ── Speaker Cards ────────────────────── */
  .speakers {
    display: grid;
    grid-template-columns: repeat({{ speaker_cols }}, 1fr);
    gap: 4mm;
  }

  .card {
    border-radius: 4mm;
    padding: 5mm;
    display: flex;
    align-items: center;
    gap: 4mm;
    box-shadow: 0 1mm 3mm rgba(0,0,0,0.06);
    transition: transform 0.2s;
  }
  .card:nth-child(1) { background: #e8f6f3; border-left: 3px solid #0d7377; }
  .card:nth-child(2) { background: #eaf0f9; border-left: 3px solid #1a5276; }
  .card:nth-child(3) { background: #f5eef8; border-left: 3px solid #6c3483; }
  .card:nth-child(4) { background: #fef5e7; border-left: 3px solid #ca6f1e; }
  .card:nth-child(5) { background: #e8f0fe; border-left: 3px solid #1a73e8; }
  .card:nth-child(6) { background: #fce4ec; border-left: 3px solid #c62828; }

  .card .avatar {
    width: 18mm; height: 18mm;
    border-radius: 50%;
    object-fit: cover;
    flex-shrink: 0;
    border: 2px solid rgba(0,0,0,0.08);
  }
  .card .avatar-placeholder {
    width: 18mm; height: 18mm;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22pt;
    font-weight: 700;
    color: #fff;
    flex-shrink: 0;
  }
  .card:nth-child(1) .avatar-placeholder { background: #0d7377; }
  .card:nth-child(2) .avatar-placeholder { background: #1a5276; }
  .card:nth-child(3) .avatar-placeholder { background: #6c3483; }
  .card:nth-child(4) .avatar-placeholder { background: #ca6f1e; }
  .card:nth-child(5) .avatar-placeholder { background: #1a73e8; }
  .card:nth-child(6) .avatar-placeholder { background: #c62828; }

  .card .info { flex: 1; min-width: 0; }
  .card .info .name-row {
    display: flex;
    align-items: baseline;
    gap: 2mm;
    margin-bottom: 1.5mm;
  }
  .card .info .name {
    font-size: 12pt;
    font-weight: 700;
  }
  .card .info .class-info {
    font-size: 7.5pt;
    color: #888;
    font-weight: 400;
  }
  .card:nth-child(1) .info .name { color: #0d7377; }
  .card:nth-child(2) .info .name { color: #1a5276; }
  .card:nth-child(3) .info .name { color: #6c3483; }
  .card:nth-child(4) .info .name { color: #ca6f1e; }
  .card:nth-child(5) .info .name { color: #1a73e8; }
  .card:nth-child(6) .info .name { color: #c62828; }

  .card .info .topic {
    font-size: 8.5pt;
    color: #555;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  /* ── Illustration Grid ────────────────── */
  .illustrations {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 3mm;
    margin-top: 4mm;
  }
  .illustrations img {
    width: 100%;
    height: 28mm;
    object-fit: cover;
    border-radius: 3mm;
    box-shadow: 0 1mm 2mm rgba(0,0,0,0.08);
  }

  /* ── Team Intro ────────────────────────── */
  .team-section {
    margin-top: 3mm;
    background: linear-gradient(135deg, #0d737708, #0f4c7508);
    border: 1px solid #0d737722;
    border-radius: 4mm;
    padding: 3mm 6mm;
  }
  .team-section .team-header {
    display: flex;
    align-items: center;
    gap: 3mm;
    margin-bottom: 3mm;
  }
  .team-section .team-header .team-badge {
    background: linear-gradient(135deg, #0d7377, #0f4c75);
    color: #fff;
    font-size: 9pt;
    font-weight: 700;
    padding: 1.5mm 4mm;
    border-radius: 2mm;
    letter-spacing: 0.5pt;
  }
  .team-section .team-header .vision {
    font-size: 9pt;
    color: #0d7377;
    font-weight: 600;
  }
  .team-section .tracks {
    font-size: 8pt;
    color: #555;
    line-height: 1.5;
    margin-bottom: 3mm;
  }
  .team-section .tracks .tag {
    display: inline-block;
    background: #e8f6f3;
    color: #0d7377;
    font-size: 7.5pt;
    padding: 1mm 3mm;
    border-radius: 1.5mm;
    margin-right: 2mm;
    font-weight: 600;
  }
  .team-section .recruit {
    text-align: center;
    font-size: 10pt;
    font-weight: 700;
    color: #0d7377;
    padding: 2.5mm 0;
    background: linear-gradient(90deg, transparent, #0d737712, transparent);
    border-radius: 2mm;
    letter-spacing: 0.5pt;
  }
  .team-section .highlight {
    text-align: center;
    font-size: 8.5pt;
    color: #555;
    font-style: italic;
    margin-top: 2mm;
    line-height: 1.4;
  }
  .team-section .links {
    display: flex;
    justify-content: center;
    gap: 6mm;
    margin-top: 3mm;
  }
  .team-section .qr-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.5mm;
  }
  .team-section .qr-item a {
    display: block;
    line-height: 0;
  }
  .team-section .qr-item img {
    width: 22mm;
    height: 22mm;
    border-radius: 2mm;
    border: 1px solid #ddd;
  }
  .team-section .qr-item span {
    font-size: 7pt;
    color: #555;
    font-weight: 600;
  }

  /* ── Footer ───────────────────────────── */
  .footer {
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 18mm;
    background: #e8f6f3;
    padding: 0 12mm;
    display: flex;
    align-items: center;
    gap: 5mm;
    border-top: 1px solid #b2dfdb;
  }
  .footer .label {
    font-size: 9pt;
    font-weight: 700;
    color: #0d7377;
  }
  .footer .meeting-id {
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11pt;
    color: #0d7377;
  }
  .footer .link {
    font-size: 7.5pt;
    color: #888;
  }
  .footer .qr-code {
    margin-left: auto;
    width: 12mm;
    height: 12mm;
  }
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div class="dept">
    <span class="dept-badge">开源社区部</span>
    <span class="dept-en">Open Source Department</span>
  </div>
  <div class="club-row">
    {% if logo %}
    <img class="logo" src="{{ logo }}" alt="Logo">
    {% endif %}
    <div class="club-text">
      <span class="club-cn">清华大学未来智能机器人兴趣团队</span>
      <span class="club-en">Future Robotics Club, FuRoC</span>
    </div>
  </div>
  <h1>{{ title }}</h1>
  <div class="meta">
    <span><i class="icon"></i> 日期：{{ date }}</span>
    <span><i class="icon"></i> 时间：{{ time }}</span>
    {% if format %}
    <span><i class="icon"></i> 形式：{{ format }}</span>
    {% endif %}
    {% if meeting_id %}
    <span><i class="icon"></i> 会议：{{ meeting_id }}</span>
    {% endif %}
    {% if meeting_link %}
    <span><i class="icon"></i> 链接：<a href="{{ meeting_link }}">{{ meeting_link }}</a></span>
    {% endif %}
  </div>
</div>

<!-- Content -->
<div class="content">

  <div class="section-title"><span>分享人</span></div>

  <div class="speakers">
    {% for sp in speakers %}
    <div class="card">
      {% if sp.photo %}
      <img class="avatar" src="{{ sp.photo }}" alt="{{ sp.name }}">
      {% else %}
      <div class="avatar-placeholder">{{ sp.name[0] }}</div>
      {% endif %}
      <div class="info">
        <div class="name-row">
          <span class="name">{{ sp.name }}</span>
          {% if sp.class %}
          <span class="class-info">{{ sp.class }}</span>
          {% endif %}
        </div>
        <div class="topic">{{ sp.topic }}</div>
      </div>
    </div>
    {% endfor %}
  </div>

  {% if illustrations %}
  <div class="illustrations">
    {% for img in illustrations %}
    <img src="{{ img }}" alt="illustration">
    {% endfor %}
  </div>
  {% endif %}

  {% if team_name %}
  <div class="team-section">
    <div class="team-header">
      <span class="team-badge">{{ team_name }}</span>
      {% if vision %}
      <span class="vision">{{ vision }}</span>
      {% endif %}
    </div>
    {% if tracks %}
    <div class="tracks">
      <span class="tag">赛道1</span> Awesome Repo 导向（新人入门）
      <span class="tag">赛道2</span> 立项 Contribute（进阶贡献）
    </div>
    {% endif %}
    {% if recruitment %}
    <div class="recruit">{{ recruitment }}</div>
    {% endif %}
    {% if highlight %}
    <div class="highlight">{{ highlight }}</div>
    {% endif %}
    {% if github or feishu or huggingface %}
    <div class="links">
      {% if github %}
      <div class="qr-item">
        <a href="{{ github }}"><img src="{{ github_qr }}" alt="GitHub QR"></a>
        <span>GitHub: {{ github_name }}</span>
      </div>
      {% endif %}
      {% if feishu %}
      <div class="qr-item">
        <a href="{{ feishu }}"><img src="{{ feishu_qr }}" alt="飞书 QR"></a>
        <span>飞书: {{ feishu_name }}</span>
      </div>
      {% endif %}
      {% if huggingface %}
      <div class="qr-item">
        <a href="{{ huggingface }}"><img src="{{ huggingface_qr }}" alt="HuggingFace QR"></a>
        <span>HuggingFace: {{ huggingface_name }}</span>
      </div>
      {% endif %}
    </div>
    {% endif %}
  </div>
  {% endif %}

</div>

<!-- Footer -->
<div class="footer">
  <span class="label">腾讯会议</span>
  <span class="meeting-id">{{ meeting_id }}</span>
  {% if meeting_link %}
  <span class="link">{{ meeting_link }}</span>
  {% endif %}
  {% if meeting_qr %}
  <img class="qr-code" src="{{ meeting_qr }}" alt="扫码入会">
  {% endif %}
</div>

</body>
</html>
""")


# ── 生成 & 编译 ──────────────────────────────────────────────────────

def generate_qr_base64(url, box_size=5, border=2):
    """Generate QR code as base64 PNG data URI."""
    import qrcode, base64
    from io import BytesIO
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M,
                        box_size=box_size, border=border)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"


def _call_llm_shorten(speaker_lines):
    """Call LLM API to semantically shorten speaker topics."""
    import os
    try:
        import requests
    except ImportError:
        return None

    token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "")
    model = os.environ.get("ANTHROPIC_MODEL", "glm-5.1")

    if not token or not base_url:
        return None

    prompt = (
        "精简以下每位分享人的主题描述，每条控制在15字以内。"
        "保留关键技术词和项目名，去掉进度类描述(已完成、接下来计划等)。"
        "每行格式: • 姓名（班级）精简主题\n\n"
        + "\n".join(speaker_lines)
    )

    try:
        resp = requests.post(
            f"{base_url}/v1/messages",
            headers={
                "x-api-key": token,
                "content-type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": model,
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=15,
        )
        resp.raise_for_status()
        result = resp.json()
        return result["content"][0]["text"].strip()
    except Exception as e:
        print(f"[WARN] LLM shortening failed: {e}", file=sys.stderr)
        return None


def generate_quotes(data):
    """Generate concise promotional text, using LLM to shorten topics."""
    lines = []

    title = data.get("title", "")
    if title:
        lines.append(f"【FuRoC 开源社区部 · {title}】")
    else:
        lines.append("【FuRoC 开源社区部 · 微沙龙】")
    lines.append("")

    speakers = data.get("speakers", [])
    if speakers:
        lines.append("🚀 分享阵容")

        # Try LLM shortening
        speaker_raw = []
        for sp in speakers:
            cls = f"（{sp['class']}）" if sp.get("class") else ""
            speaker_raw.append(f"{sp['name']}{cls} | {sp['topic']}")

        shortened = _call_llm_shorten(speaker_raw)
        if shortened:
            for line in shortened.split("\n"):
                line = line.strip()
                if line:
                    if not line.startswith("•") and not line.startswith("-"):
                        line = "• " + line
                    lines.append(line)
        else:
            # Fallback to raw output
            for sp in speakers:
                cls = f"（{sp['class']}）" if sp.get("class") else ""
                lines.append(f"• {sp['name']}{cls} {sp['topic']}")
        lines.append("")

    date = data.get("date", "")
    time = data.get("time", "")
    if date or time:
        lines.append(f"⏰ {date} {time}".strip())

    mid = data.get("meeting_id", "")
    if mid:
        lines.append(f"📍 腾讯会议 {mid}")

    link = data.get("meeting_link", "")
    if link:
        lines.append(f"🔗 {link}")

    return "\n".join(lines)


def generate_html(data, illustrations=None):
    """Render HTML from parsed data using Jinja2 template."""
    # Generate QR code data URIs
    github_qr = generate_qr_base64(data["github"]) if data.get("github") else ""
    feishu_qr = generate_qr_base64(data["feishu"]) if data.get("feishu") else ""
    huggingface_qr = generate_qr_base64(data["huggingface"]) if data.get("huggingface") else ""
    meeting_qr = generate_qr_base64(data["meeting_link"]) if data.get("meeting_link") else ""

    speaker_count = len(data.get("speakers", []))
    speaker_cols = 3 if speaker_count > 4 else 2

    return HTML_TEMPLATE.render(
        title=data.get("title", ""),
        club=data.get("club", ""),
        date=data.get("date", ""),
        time=data.get("time", ""),
        format=data.get("format", ""),
        speakers=data.get("speakers", []),
        speaker_cols=speaker_cols,
        logo=data.get("logo", ""),
        meeting_id=data.get("meeting_id", ""),
        meeting_link=data.get("meeting_link", ""),
        illustrations=illustrations or [],
        team_name=data.get("team_name", ""),
        vision=data.get("vision", ""),
        tracks=data.get("tracks", ""),
        recruitment=data.get("recruitment", ""),
        highlight=data.get("highlight", ""),
        github=data.get("github", ""),
        github_name=data.get("github_name", ""),
        feishu=data.get("feishu", ""),
        feishu_name=data.get("feishu_name", ""),
        huggingface=data.get("huggingface", ""),
        huggingface_name=data.get("huggingface_name", ""),
        github_qr=github_qr,
        feishu_qr=feishu_qr,
        huggingface_qr=huggingface_qr,
        meeting_qr=meeting_qr,
    )


def html_to_pdf(html_path, pdf_path):
    """Convert HTML to PDF using Playwright (forced single page)."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # Set viewport to A4 at 96dpi so CSS mm units render correctly
        page.set_viewport_size({"width": 794, "height": 1123})
        # Use screen media so overflow:hidden is respected (no pagination)
        page.emulate_media(media="screen")
        page.goto(html_path.as_uri())

        # Overflow detection: measure content vs available space
        overflow = page.evaluate("""() => {
            const body = document.body;
            const header = document.querySelector('.header');
            const footer = document.querySelector('.footer');
            const content = document.querySelector('.content');
            if (!header || !footer || !content) return { ok: true };
            const bodyH = body.getBoundingClientRect().height;
            const headerH = header.getBoundingClientRect().height;
            const footerH = footer.getBoundingClientRect().height;
            const contentH = content.getBoundingClientRect().height;
            const available = bodyH - headerH - footerH;
            const scale = 297 / bodyH;  // px -> mm
            return {
                ok: contentH <= available,
                content_mm: (contentH * scale).toFixed(1),
                available_mm: (available * scale).toFixed(1),
                header_mm: (headerH * scale).toFixed(1),
                footer_mm: (footerH * scale).toFixed(1),
            };
        }""")
        if not overflow.get('ok', True):
            print(f"[WARN] Content overflow: content {overflow['content_mm']}mm "
                  f"> available {overflow['available_mm']}mm "
                  f"(header {overflow['header_mm']}mm + footer {overflow['footer_mm']}mm)",
                  file=sys.stderr)

        page.pdf(
            path=str(pdf_path),
            width="210mm",
            height="297mm",
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        )
        browser.close()


def pdf_to_png(pdf_path, png_path, dpi=300):
    """Convert PDF to PNG using pdf2image (poppler)."""
    from pdf2image import convert_from_path
    images = convert_from_path(str(pdf_path), dpi=dpi)
    images[0].save(str(png_path), "PNG")


def main():
    parser = argparse.ArgumentParser(description="从沙龙 MD 生成 A4 海报 (Playwright)")
    parser.add_argument("input", help="输入 MD 文件路径")
    parser.add_argument("-o", "--output", default=None,
                        help="输出 .html 文件路径 (默认: 同目录下同名.html)")
    parser.add_argument("--pdf", action="store_true",
                        help="生成后自动转 PDF (需要 playwright + chromium)")
    parser.add_argument("--png", action="store_true",
                        help="生成后自动转 PNG (需要 playwright + chromium)")
    parser.add_argument("--illustrations", nargs="*", default=None,
                        help="海报插画图片路径 (可选, 最多4张)")
    parser.add_argument("--copy", action="store_true",
                        help="生成推广文案并输出到 stdout")
    args = parser.parse_args()

    md_path = Path(args.input).resolve()
    md_dir = str(md_path.parent)

    if not md_path.exists():
        print(f"[ERROR] File not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    # Parse MD
    md_text = md_path.read_text(encoding="utf-8")
    data = parse_md(md_text, md_dir)

    # --copy: generate promotional text and exit
    if args.copy:
        sys.stdout.buffer.write(generate_quotes(data).encode("utf-8"))
        sys.stdout.buffer.write(b"\n")
        return

    # Resolve illustration paths
    illustrations = []
    if args.illustrations:
        for img_path in args.illustrations:
            p = Path(img_path).resolve()
            if p.exists():
                illustrations.append(p.as_uri())
            else:
                print(f"[WARN] Illustration not found: {img_path}", file=sys.stderr)

    # Output path
    html_path = Path(args.output) if args.output else md_path.with_suffix(".html")

    # Generate HTML
    html_source = generate_html(data, illustrations)
    html_path.write_text(html_source, encoding="utf-8")
    print(f"[OK] Generated: {html_path}")

    # Convert to PDF
    if args.pdf:
        pdf_path = html_path.with_suffix(".pdf")
        print("[...] Converting to PDF with Playwright...")
        html_to_pdf(html_path, pdf_path)
        print(f"[OK] PDF: {pdf_path}")

    # Convert to PNG
    if args.png:
        pdf_path = html_path.with_suffix(".pdf")
        if not pdf_path.exists():
            print("[...] Generating PDF first for PNG conversion...")
            html_to_pdf(html_path, pdf_path)
            print(f"[OK] PDF: {pdf_path}")
        png_path = html_path.with_suffix(".png")
        print("[...] Converting PDF to PNG...")
        pdf_to_png(pdf_path, png_path)
        print(f"[OK] PNG: {png_path}")


if __name__ == "__main__":
    main()
