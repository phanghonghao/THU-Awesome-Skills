#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def remove_images(md: str) -> str:
    return re.sub(r"!\[(.*?)\]\((.*?)\)", "", md)


def extract_title(path: Path, text: str) -> str:
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            return s.lstrip("#").strip()
        return re.sub(r"[_\-]+", " ", path.stem).strip()
    return re.sub(r"[_\-]+", " ", path.stem).strip()


def extract_numbered_sections(text: str):
    """Extract sections matching '## N. title' or 'N. title' patterns."""
    sections = []
    current = None
    for line in text.splitlines():
        s = line.rstrip()
        # Match "## N. title" (markdown header) or plain "N. title"
        m = re.match(r"^\s*##\s*(\d+)\.\s+(.+)$", s) or re.match(r"^\s*(\d+)\.\s+(.+)$", s)
        if m:
            if current:
                sections.append(current)
            current = {"title": clean_text(m.group(2)), "items": []}
            continue
        if current and s.strip() and not s.strip().startswith("#"):
            current["items"].append(clean_text(s))
    if current:
        sections.append(current)
    return sections


def extract_key_takeaways(text: str, limit=5):
    out = []
    for sec in extract_numbered_sections(text):
        body = " ".join(sec["items"])
        merged = clean_text(f"{sec['title']} {body}")
        if merged:
            out.append(merged[:180])
        if len(out) >= limit:
            break
    if out:
        return out

    paras = [clean_text(x) for x in text.split("\n\n") if clean_text(x)]
    return paras[:limit]


def extract_technical_highlights(text: str, limit=6):
    lines = [clean_text(x) for x in text.splitlines() if clean_text(x)]
    patterns = [
        r"\b1050\b", r"\b552\b", r"\b12\b", r"\bPPO\b", r"\bPD\b", r"\bAMP\b",
        r"\bK-Action\b", r"\bKP\b", r"\bKD\b", r"\b0\.25\b", r"\b0\.3\b", r"\b0\.4\b",
        r"\b200 Hz\b", r"\b0\.02s\b", r"\b0\.8 秒\b", r"\b0\.4 秒\b"
    ]
    out = []
    for line in lines:
        if any(re.search(p, line, re.I) for p in patterns):
            out.append(line[:180])
        if len(out) >= limit:
            break
    return out


def extract_summary_line(text: str) -> str:
    paras = [clean_text(x) for x in text.split("\n\n") if clean_text(x)]
    for p in reversed(paras):
        if len(p) >= 20:
            return p[:200]
    return "把个人反思整理成一张适合分享的小红书单页图。"


def build_payload(path: Path):
    raw = read_markdown(path)
    text = remove_images(raw)
    title = extract_title(path, text)
    takeaways = extract_key_takeaways(text, limit=5)
    technical = extract_technical_highlights(text, limit=6)
    summary = extract_summary_line(text)
    subtitle = takeaways[0] if takeaways else "个人论文读后感整理"
    return {
        "title": title,
        "subtitle": subtitle,
        "takeaways": takeaways,
        "technical_highlights": technical,
        "summary": summary,
        "source": str(path),
    }


def build_prompt(payload: dict) -> str:
    bullets = "\n".join(f"- {x}" for x in payload["takeaways"])
    tech = "\n".join(f"- {x}" for x in payload["technical_highlights"])
    return f"""Design a single-page A4 vertical educational study-note poster in Chinese.

Content source type: personal reflection markdown.

Title: {payload['title']}
Subtitle: {payload['subtitle']}

Main takeaways:
{bullets}

Technical highlights:
{tech}

Bottom summary:
{payload['summary']}

Layout requirements:
- A4 vertical poster, content must fill the entire page evenly
- polished study-note aesthetic
- warm ivory background, editorial cards, modern Chinese typography
- information-dense but readable
- no browser UI, no fake screenshots, no watermark, no brand logos
- emphasize title, structured cards, key bullets, and technical numbers
- make it look like a shareable one-page poster for social media
- cards must use flex:1 to auto-stretch and distribute evenly across columns
- no large white space at bottom; content should balance to fill the page
- use two-column grid layout with align-items:stretch for balanced fill
"""


def maybe_generate_image(prompt: str, out_dir: Path, model: str):
    try:
        from openai import OpenAI
        import base64
    except Exception as exc:
        raise RuntimeError("Missing dependencies: install openai") from exc

    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI()
    result = client.images.generate(
        model=model,
        prompt=prompt,
        size="1024x1536",
    )
    image_b64 = result.data[0].b64_json
    out_path = out_dir / "poster.png"
    out_path.write_bytes(base64.b64decode(image_b64))
    return out_path


def copy_latest_codex_generated_image(out_dir: Path, codex_dir: Path | None = None):
    root = codex_dir or (Path.home() / ".codex" / "generated_images")
    if not root.exists():
        raise RuntimeError(f"Codex generated image cache not found: {root}")

    candidates = sorted(root.rglob("*.png"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        raise RuntimeError(f"No generated PNG found under: {root}")

    src = candidates[-1]
    dst = out_dir / "poster.png"
    shutil.copy2(src, dst)
    return dst


def main():
    ap = argparse.ArgumentParser(description="Convert reflection markdown into Xiaohongshu poster prompt/image.")
    ap.add_argument("--input", required=True, help="Path to reflection markdown file")
    ap.add_argument("--out-dir", help="Output directory; default is source file directory / <stem>_xhs")
    ap.add_argument("--generate", action="store_true", help="Call OpenAI image API to generate poster.png")
    ap.add_argument("--copy-latest-codex-image", action="store_true", help="Copy the latest PNG from ~/.codex/generated_images into out_dir/poster.png")
    ap.add_argument("--codex-generated-dir", help="Override Codex generated image cache directory")
    ap.add_argument("--model", default="gpt-image-1", help="Image model; default gpt-image-1")
    args = ap.parse_args()

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"Not found: {src}")
    if src.suffix.lower() not in {".md", ".markdown"}:
        raise SystemExit(f"Only Markdown input is supported: {src}")

    out_dir = Path(args.out_dir).expanduser().resolve() if args.out_dir else src.parent / f"{src.stem}_xhs"
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = build_payload(src)
    prompt = build_prompt(payload)

    (out_dir / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "prompt.txt").write_text(prompt, encoding="utf-8")

    print(f"[OK] summary: {out_dir / 'summary.json'}")
    print(f"[OK] prompt: {out_dir / 'prompt.txt'}")

    if args.generate:
        image_path = maybe_generate_image(prompt, out_dir, args.model)
        print(f"[OK] poster: {image_path}")
    elif args.copy_latest_codex_image:
        codex_dir = Path(args.codex_generated_dir).expanduser().resolve() if args.codex_generated_dir else None
        image_path = copy_latest_codex_generated_image(out_dir, codex_dir)
        print(f"[OK] poster: {image_path}")


if __name__ == "__main__":
    main()
