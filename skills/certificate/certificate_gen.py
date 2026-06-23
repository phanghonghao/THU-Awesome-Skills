"""
certificate_gen.py — 从沙龙海报自动生成电子证书 (PNG)

输入:
  --image  海报图片路径 (PNG/JPG)  → 用 GLM-4V 提取信息
  --html   海报 HTML 路径          → 解析 HTML 提取信息
  --json   直接传入 JSON 数据      → 跳过提取, 直接生成

输出:
  PNG 文件, 保存在海报同级的 certificates/ 子目录下

JSON 格式 (供 --json 或被 Claude 直接传入):
{
  "salon_title": "第X期微沙龙",
  "salon_n": "X",               # 中文数字
  "date": "2025.5.10",
  "speakers": [
    {"name": "张三", "topic": "主题描述"},
    ...
  ]
}
"""
import argparse, json, os, re, subprocess, sys, tempfile
from pathlib import Path
from html.parser import HTMLParser

# ── 路径常量 ──────────────────────────────────────────────
SKILL_DIR  = Path(__file__).parent
TEMPLATE   = SKILL_DIR / "certificate_template.html"
LOGO       = SKILL_DIR / "Profile_FuRoC.jpg"
VISION_API = Path(r"C:\Users\20174\.claude\skills\img-reader\vision_api.py")
CHROME     = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# ── 签名 (固定) ──────────────────────────────────────────
SIG_LEFT_NAME  = "刘思彤"
SIG_LEFT_ROLE  = "FuRoC 科技活动中心负责人"
SIG_RIGHT_NAME = "潘洪浩"
SIG_RIGHT_ROLE = "开源社区部 负责人"


# ══════════════════════════════════════════════════════════
#  提取方式 1: 图片 → GLM-4V
# ══════════════════════════════════════════════════════════
def extract_from_image(image_path: str) -> dict:
    prompt = (
        "请从这张沙龙海报中提取以下信息, 严格按 JSON 格式返回, 不要任何多余文字:\n"
        "```json\n"
        '{\n'
        '  "salon_title": "第X期微沙龙",\n'
        '  "salon_n": "X",\n'
        '  "date": "2025.M.DD",\n'
        '  "speakers": [\n'
        '    {"name": "分享人姓名", "topic": "分享主题"},\n'
        '    ...\n'
        '  ]\n'
        '}\n'
        "```\n"
        "注意:\n"
        "- salon_n 用中文数字 (一, 二, 三...)\n"
        "- date 格式为 YYYY.M.DD\n"
        "- 提取所有分享人的姓名和完整主题\n"
    )
    import subprocess as sp
    result = sp.run(
        [sys.executable, str(VISION_API), image_path, prompt],
        capture_output=True, timeout=60
    )
    raw = result.stdout.decode("utf-8", errors="replace")
    # 从输出中提取 JSON
    m = re.search(r'\{[\s\S]+\}', raw)
    if not m:
        raise RuntimeError(f"GLM-4V 返回无法解析, 原始输出:\n{raw[:500]}")
    outer = json.loads(m.group())

    # 如果外层是 vision_api.py 的包装 {"success":true,"result":"...","provider":"..."}
    if isinstance(outer, dict) and "speakers" not in outer and "result" in outer:
        inner_raw = outer["result"]
        # 去掉 markdown code block 包裹
        inner_raw = re.sub(r'^```\w*\n?', '', inner_raw.strip())
        inner_raw = re.sub(r'\n?```$', '', inner_raw.strip())
        data = json.loads(inner_raw)
    else:
        data = outer

    if not isinstance(data, dict) or "speakers" not in data:
        raise RuntimeError(f"提取结果缺少 speakers, 原始输出:\n{raw[:500]}")
    return data


# ══════════════════════════════════════════════════════════
#  提取方式 2: HTML → 正则解析
# ══════════════════════════════════════════════════════════
def extract_from_html(html_path: str) -> dict:
    text = Path(html_path).read_text(encoding="utf-8")

    # 标题: <h1>第X次微沙龙</h1> 或 <h1>第一次微沙龙</h1>
    m_title = re.search(r'<h1[^>]*>(.*?)</h1>', text)
    salon_title = m_title.group(1).strip() if m_title else "微沙龙"
    # 提取中文数字
    m_n = re.search(r'第([一二三四五六七八九十\d]+)[次期]', salon_title)
    salon_n = m_n.group(1) if m_n else "一"

    # 日期: 日期：5.10  或 5.30（周六）
    m_date = re.search(r'日期[：:]\s*([\d.]+)', text)
    date_str = m_date.group(1).strip() if m_date else ""

    # 分享人卡片: .name 和 .topic
    names = re.findall(r'<span class="name"[^>]*>(.*?)</span>', text)
    topics = re.findall(r'<div class="topic"[^>]*>(.*?)</div>', text)

    speakers = []
    for i in range(min(len(names), len(topics))):
        speakers.append({
            "name": re.sub(r'<[^>]+>', '', names[i]).strip(),
            "topic": re.sub(r'<[^>]+>', '', topics[i]).strip(),
        })

    return {
        "salon_title": salon_title,
        "salon_n": salon_n,
        "date": date_str,
        "speakers": speakers,
    }


# ══════════════════════════════════════════════════════════
#  生成证书
# ══════════════════════════════════════════════════════════
def fill_template(data: dict, speaker: dict) -> str:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    # 解析日期
    parts = data.get("date", "").split(".")
    yyyy = parts[0] if len(parts) > 0 else "2025"
    mm   = parts[1] if len(parts) > 1 else "1"
    dd   = parts[2] if len(parts) > 2 else "1"

    return (
        tpl
        .replace("{{姓名}}",   speaker["name"])
        .replace("{{N}}",      data.get("salon_n", "一"))
        .replace("{{分享主题}}", speaker["topic"])
        .replace("{{活动日期}}", data.get("date", ""))
        .replace("{{YYYY}}",   yyyy)
        .replace("{{MM}}",     mm)
        .replace("{{DD}}",     dd)
    )


def html_to_png(html_path: str, png_path: str) -> bool:
    # Ensure absolute paths; skip resolve if already a file:// URI
    if not html_path.startswith("file://"):
        html_path = str(Path(html_path).resolve())
    png_path  = str(Path(png_path).resolve())
    r = subprocess.run([
        CHROME, "--headless", "--disable-gpu", "--no-sandbox",
        f"--screenshot={png_path}",
        "--window-size=794,1123",
        "--force-device-scale-factor=3",
        html_path,
    ], capture_output=True, timeout=60)
    ok = os.path.exists(png_path)
    if not ok:
        sys.stderr.write(f"Chrome stderr: {r.stderr.decode('utf-8','replace')[-300:]}\n")
    return ok


def generate_certificates(data: dict, output_dir: str):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    speakers = data.get("speakers", [])
    if not speakers:
        print("[ERROR] 未提取到分享人数据")
        return

    print(f"沙龙: {data.get('salon_title', '?')} | 日期: {data.get('date', '?')} | 分享人: {len(speakers)} 人")
    print("-" * 50)

    for sp in speakers:
        html_content = fill_template(data, sp)
        safe = sp["name"].replace(" ", "_")
        html_path = out / f"{safe}.html"
        png_path  = out / f"{safe}.png"
        html_path.write_text(html_content, encoding="utf-8")
        ok = html_to_png(str(html_path.resolve()), str(png_path))
        # 清理临时 HTML
        html_path.unlink(missing_ok=True)
        if ok:
            print(f"  OK {png_path.name}")
        else:
            print(f"  FAIL {png_path.name}")

    print(f"\nDone. {len(speakers)} certificates → {out}")


# ══════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser(description="从沙龙海报生成电子证书")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--image", help="海报图片路径 (PNG/JPG)")
    group.add_argument("--html",  help="海报 HTML 路径")
    group.add_argument("--json",  help="直接传入 JSON 数据字符串")
    p.add_argument("-o", "--output", help="输出目录 (默认: 海报同级 certificates/)")

    args = p.parse_args()

    # 提取数据
    if args.image:
        print(f"[1/2] 从图片提取: {args.image}")
        data = extract_from_image(args.image)
    elif args.html:
        print(f"[1/2] 从 HTML 提取: {args.html}")
        data = extract_from_html(args.html)
    else:
        data = json.loads(args.json)

    print(f"[提取结果] {json.dumps(data, ensure_ascii=False, indent=2)}")

    # 输出目录
    if args.output:
        out_dir = args.output
    else:
        src = Path(args.image or args.html or ".")
        out_dir = str(src.parent / "certificates")

    print(f"\n[2/2] 生成证书 → {out_dir}")
    generate_certificates(data, out_dir)


if __name__ == "__main__":
    main()
