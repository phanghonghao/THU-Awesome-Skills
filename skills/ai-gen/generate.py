#!/usr/bin/env python3
"""AI 文生图/文生视频生成工具 — 多模型组合版 (纯 stdlib，零外部依赖).

支持预设:
  doubao  — 文生图: GLM-CogView3-Flash | 文生视频: Doubao-Seedance-1.0-Pro  (p001 族)
  glm     — 文生图: GLM-CogView3-Flash | 文生视频: Doubao-Seedance-1.0-Pro  (p001 族)
  minimax — 文生图: GLM-CogView3-Flash | 文生视频: MiniMax-T2V-01-Directo   (p004 族)

CLI:
  python generate.py --list-presets
  python generate.py --mode image --prompt "..." --provider doubao
  python generate.py --mode video --prompt "..." --provider minimax
  python generate.py --mode video --prompt "..." --model MiniMax-T2V-01-Directo
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
DEFAULT_OUTPUT_DIR = Path("ai_gen_output")

DEFAULT_BASE_URL = "https://llmapi.paratera.com/v1"

VIDEO_POLL_INTERVAL = 10
VIDEO_MAX_WAIT = 600

# ── 预设定义 ──────────────────────────────────────────────────────────

PRESETS = {
    "doubao": {
        "label": "豆包 (Doubao)",
        "image_model": "GLM-CogView3-Flash",
        "video_model": "Doubao-Seedance-1.0-Pro",
        "video_engine": "doubao",   # p001 族
    },
    "glm": {
        "label": "GLM",
        "image_model": "GLM-CogView3-Flash",
        "video_model": "Doubao-Seedance-1.0-Pro",
        "video_engine": "doubao",   # GLM 无视频，用豆包补
    },
    "minimax": {
        "label": "MiniMax",
        "image_model": "GLM-CogView3-Flash",
        "video_model": "MiniMax-T2V-01-Directo",
        "video_engine": "minimax",  # p004 族
    },
}


def _load_config():
    """Load config.json, return dict with api_keys list and base_url."""
    if not CONFIG_PATH.exists():
        print(f"[ERROR] config not found: {CONFIG_PATH}", file=sys.stderr)
        print("Copy config.example.json -> config.json and fill in your API keys.", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


class KeyPool:
    """Round-robin API key pool."""

    def __init__(self, keys):
        self._keys = list(keys)
        self._idx = 0

    def next(self):
        if not self._keys:
            raise RuntimeError("No API keys available")
        key = self._keys[self._idx % len(self._keys)]
        self._idx += 1
        return key


def _urlopen_with_retry(url, headers, data=None, method="POST", timeout=180, retries=3):
    """urlopen with simple retry on transient errors."""
    req = urllib.request.Request(url, headers=headers, data=data, method=method)
    last_err = None
    for attempt in range(retries):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.URLError as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    raise last_err


def _resolve_base_url(config):
    """Get base_url from config or use default."""
    return config.get("base_url", DEFAULT_BASE_URL)


# ── 文生图 (统一 OpenAI 兼容) ─────────────────────────────────────────

def text_to_image(prompt, output_path, api_key, base_url, model="GLM-CogView3-Flash", size="1024x1024"):
    """Call text-to-image API (synchronous, OpenAI-compatible)."""
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": size,
    }).encode("utf-8")

    url = base_url.rstrip("/") + "/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    print(f"[image] Model: {model}")
    print(f"[image] Generating: {prompt[:80]}...")
    resp = _urlopen_with_retry(url, headers, data=payload, method="POST", timeout=180)
    data = json.loads(resp.read().decode("utf-8"))

    items = data.get("data") or [{}]
    item = items[0]
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if item.get("b64_json"):
        out.write_bytes(base64.b64decode(item["b64_json"]))
    elif item.get("url"):
        img_resp = urllib.request.urlopen(item["url"], timeout=180)
        out.write_bytes(img_resp.read())
    else:
        raise RuntimeError(f"No image data in response: {data}")

    print(f"[image] Saved: {out} ({out.stat().st_size // 1024} KB)")
    return str(out)


# ── 文生视频 — 豆包 Doubao (p001 族) ─────────────────────────────────

def _submit_doubao_video(prompt, api_key, base_url, model="Doubao-Seedance-1.0-Pro", ratio="16:9", dur=None):
    """Submit async video task to Doubao p001 endpoint, return task_id."""
    text_parts = f"{prompt} --ratio {ratio}"
    if dur is not None:
        text_parts += f" --dur {dur}"

    payload = json.dumps({
        "model": model,
        "content": [{"type": "text", "text": text_parts}],
    }).encode("utf-8")

    url = base_url.rstrip("/") + "/p001/contents/generations/tasks"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    print(f"[video/doubao] Submitting task: {prompt[:80]}...")
    resp = _urlopen_with_retry(url, headers, data=payload, method="POST", timeout=30)
    result = json.loads(resp.read().decode("utf-8"))
    task_id = result.get("id")
    if not task_id:
        raise RuntimeError(f"No task id in submit response: {result}")
    print(f"[video/doubao] Task submitted: {task_id}")
    return task_id


def _poll_doubao_video(task_id, api_key, base_url):
    """Poll Doubao p001 task until complete, return video download URL."""
    url = base_url.rstrip("/") + "/p001/contents/generations/tasks"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"filter": json.dumps({"task_ids": [task_id]})}

    elapsed = 0
    while elapsed < VIDEO_MAX_WAIT:
        full_url = url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(full_url, headers=headers, method="GET")
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read().decode("utf-8"))

        tasks = result.get("data") or []
        if tasks:
            task = tasks[0]
            status = task.get("status", "")
            if status == "succeeded":
                video_url = (task.get("result") or {}).get("s3_url", "")
                if not video_url:
                    raise RuntimeError(f"Task succeeded but no video URL: {task}")
                return video_url
            elif status == "failed":
                raise RuntimeError(f"Task failed: {task}")
            print(f"[video/doubao] Status: {status} ... ({elapsed}s elapsed)")
        else:
            print(f"[video/doubao] Waiting for task info ... ({elapsed}s elapsed)")

        time.sleep(VIDEO_POLL_INTERVAL)
        elapsed += VIDEO_POLL_INTERVAL

    raise TimeoutError(f"Video generation timed out after {VIDEO_MAX_WAIT}s")


# ── 文生视频 — MiniMax (p004 族) ──────────────────────────────────────

def _submit_minimax_video(prompt, api_key, base_url, model="MiniMax-T2V-01-Directo"):
    """Submit async video task to MiniMax p004 endpoint, return task_id."""
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
    }).encode("utf-8")

    url = base_url.rstrip("/") + "/p004/video_generation"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    print(f"[video/minimax] Submitting task: {prompt[:80]}...")
    resp = _urlopen_with_retry(url, headers, data=payload, method="POST", timeout=30)
    result = json.loads(resp.read().decode("utf-8"))
    task_id = result.get("task_id") or result.get("id")
    if not task_id:
        raise RuntimeError(f"No task id in MiniMax submit response: {result}")
    print(f"[video/minimax] Task submitted: {task_id}")
    return task_id


def _poll_minimax_video(task_id, api_key, base_url):
    """Poll MiniMax p004 task until complete, return file_id."""
    url = base_url.rstrip("/") + "/p004/query/video_generation"
    headers = {"Authorization": f"Bearer {api_key}"}

    elapsed = 0
    while elapsed < VIDEO_MAX_WAIT:
        full_url = url + "?" + urllib.parse.urlencode({"task_id": task_id})
        req = urllib.request.Request(full_url, headers=headers, method="GET")
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read().decode("utf-8"))

        status = result.get("status", "")
        if status == "Success":
            file_id = result.get("file_id", "")
            if not file_id:
                raise RuntimeError(f"MiniMax task succeeded but no file_id: {result}")
            return file_id
        elif status == "Fail":
            raise RuntimeError(f"MiniMax task failed: {result}")
        # Preparing / Queueing / Processing
        print(f"[video/minimax] Status: {status} ... ({elapsed}s elapsed)")

        time.sleep(VIDEO_POLL_INTERVAL)
        elapsed += VIDEO_POLL_INTERVAL

    raise TimeoutError(f"MiniMax video generation timed out after {VIDEO_MAX_WAIT}s")


def _fetch_minimax_video(file_id, api_key, base_url):
    """Fetch download URL for completed MiniMax video by file_id."""
    url = base_url.rstrip("/") + "/p004/files/retrieve"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"file_id": file_id}

    full_url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(full_url, headers=headers, method="GET")
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read().decode("utf-8"))

    download_url = (result.get("file") or {}).get("download_url", "")
    if not download_url:
        raise RuntimeError(f"No download_url in MiniMax file response: {result}")
    return download_url


# ── 通用下载 ──────────────────────────────────────────────────────────

def _download_file(url, output_path):
    """Download file from URL to local path."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    resp = urllib.request.urlopen(url, timeout=300)
    out.write_bytes(resp.read())
    return str(out)


# ── 统一视频入口 ──────────────────────────────────────────────────────

def text_to_video(prompt, output_path, api_key, base_url, provider="doubao",
                  model=None, ratio="16:9", dur=None):
    """Call text-to-video API — dispatches to correct engine based on provider."""
    preset = PRESETS[provider]
    engine = preset["video_engine"]
    video_model = model or preset["video_model"]

    if engine == "doubao":
        task_id = _submit_doubao_video(prompt, api_key, base_url,
                                       model=video_model, ratio=ratio, dur=dur)
        video_url = _poll_doubao_video(task_id, api_key, base_url)
    elif engine == "minimax":
        task_id = _submit_minimax_video(prompt, api_key, base_url, model=video_model)
        file_id = _poll_minimax_video(task_id, api_key, base_url)
        video_url = _fetch_minimax_video(file_id, api_key, base_url)
    else:
        raise ValueError(f"Unknown video engine: {engine}")

    print(f"[video] Downloading: {video_url[:80]}...")
    result = _download_file(video_url, output_path)
    out = Path(result)
    print(f"[video] Saved: {out} ({out.stat().st_size // 1024 // 1024} MB)")
    return result


# ── 列出预设 ──────────────────────────────────────────────────────────

def list_presets():
    """Print available presets."""
    print("Available presets:\n")
    print(f"{'Preset':<10} {'Label':<18} {'Image Model':<25} {'Video Model':<30}")
    print("-" * 85)
    for name, p in PRESETS.items():
        print(f"{name:<10} {p['label']:<18} {p['image_model']:<25} {p['video_model']:<30}")
    print()
    print("Image model is always GLM-CogView3-Flash (the only working image model).")
    print("Choose preset based on your preferred video engine.")


# ── CLI 入口 ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI 文生图/文生视频 — 多模型组合版")
    parser.add_argument("--list-presets", action="store_true",
                        help="List available presets and exit")
    parser.add_argument("--mode", choices=["image", "video"],
                        help="Generation mode: image or video")
    parser.add_argument("--prompt", help="Text prompt for generation")
    parser.add_argument("--output", default=None,
                        help="Output file path (default: ai_gen_output/NNN.ext)")
    parser.add_argument("--provider", default="doubao",
                        choices=list(PRESETS.keys()),
                        help="Preset to use (default: doubao)")
    parser.add_argument("--model", default=None,
                        help="Override model name (advanced usage)")
    parser.add_argument("--size", default="1024x1024",
                        help="Image size (image mode only, default: 1024x1024)")
    parser.add_argument("--ratio", default="16:9",
                        help="Video aspect ratio (video mode only, default: 16:9)")
    parser.add_argument("--dur", type=int, default=None,
                        help="Video duration in seconds (video mode only)")
    parser.add_argument("--api-key", default=None,
                        help="API key (overrides config.json key pool)")

    args = parser.parse_args()

    # --list-presets
    if args.list_presets:
        list_presets()
        return

    # Validate required args
    if not args.mode or not args.prompt:
        parser.error("--mode and --prompt are required (unless using --list-presets)")

    # Resolve API key & base_url
    if args.api_key:
        key = args.api_key
        base_url = DEFAULT_BASE_URL
    else:
        config = _load_config()
        keys = config.get("api_keys", [])
        if not keys:
            print("[ERROR] No api_keys in config.json", file=sys.stderr)
            sys.exit(1)
        pool = KeyPool(keys)
        key = pool.next()
        base_url = _resolve_base_url(config)

    preset = PRESETS[args.provider]

    # Resolve model
    if args.model:
        model = args.model
    elif args.mode == "image":
        model = preset["image_model"]
    else:
        model = preset["video_model"]

    # Resolve output path
    ext = ".png" if args.mode == "image" else ".mp4"
    if args.output:
        output = args.output
    else:
        DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        existing = sorted(DEFAULT_OUTPUT_DIR.glob(f"*{ext}"))
        idx = len(existing) + 1
        output = str(DEFAULT_OUTPUT_DIR / f"{idx:03d}_{args.mode}{ext}")

    # Execute
    try:
        if args.mode == "image":
            text_to_image(args.prompt, output, key, base_url, model=model, size=args.size)
        else:
            text_to_video(args.prompt, output, key, base_url,
                          provider=args.provider, model=model,
                          ratio=args.ratio, dur=args.dur)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
