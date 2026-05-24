#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
warnings.filterwarnings("ignore", message="urllib3 .* doesn't match a supported version!", category=Warning)
import requests
from requests.exceptions import RequestsDependencyWarning
from yt_dlp import YoutubeDL


TIMESTAMP_RE = re.compile(r"(?m)^[ \t\u00a0]*((?:\d{1,2}:)?\d{1,2}:\d{2})\s+(.+?)\s*$")
warnings.simplefilter("ignore", RequestsDependencyWarning)

TOPIC_RULES: dict[str, dict[str, Any]] = {
    "VLA": {
        "slug": "vla",
        "keywords": [
            "vla",
            "vision-language-action",
            "vision language action",
            "openvla",
            "smolvla",
            "rt-2",
            "rt2",
            "pi0",
            "pi 0",
            "robot transformer",
        ],
    },
    "WM": {
        "slug": "wm",
        "keywords": [
            "world model",
            "world action model",
            "wam",
            "dreamerv3",
            "unisim",
            "cosmos",
            "gigabrain",
            "world-model-action",
        ],
    },
    "GR00T": {
        "slug": "gr00t",
        "keywords": ["gr00t", "groot", "isaac gr00t", "humanoid", "n1"],
    },
    "ALOHA": {
        "slug": "aloha",
        "keywords": [
            "aloha",
            "mobile aloha",
            "action chunking",
            "action chunking transformer",
            "遥操作",
            "teleoperation",
        ],
    },
    "DiffusionPolicy": {
        "slug": "diffusion-policy",
        "keywords": ["diffusion policy", "扩散策略", "flow matching", "diffusion"],
    },
    "RL": {
        "slug": "rl",
        "keywords": ["reinforcement learning", "强化学习", "recap", "policy optimization"],
    },
}


@dataclass
class Chapter:
    timecode: str
    seconds: int
    title: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect Bilibili metadata, screenshots, and a markdown draft for embodied-AI topic notes."
    )
    parser.add_argument("url", help="Bilibili video URL")
    parser.add_argument(
        "--output-root",
        default="outputs/embodied-ai-daily",
        help="Directory that will contain generated reports",
    )
    parser.add_argument(
        "--report-date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Date prefix for the output folder",
    )
    parser.add_argument(
        "--frame-format",
        default="30016",
        help="yt-dlp format id for the lightweight video-only download used for screenshots",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=16,
        help="Maximum chapter frames to extract",
    )
    parser.add_argument(
        "--keep-video",
        action="store_true",
        help="Keep the downloaded video artifact after frame extraction",
    )
    parser.add_argument(
        "--for-feishu",
        action="store_true",
        help="Generate Feishu-safe markdown without local relative image embeds",
    )
    return parser.parse_args()


def sanitize_slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "video"


def parse_timecode(timecode: str) -> int:
    parts = [int(part) for part in timecode.split(":")]
    if len(parts) == 2:
        minutes, seconds = parts
        return minutes * 60 + seconds
    hours, minutes, seconds = parts
    return hours * 3600 + minutes * 60 + seconds


def format_timecode(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def count_keyword(haystack: str, keyword: str) -> int:
    keyword = keyword.lower().strip()
    if not keyword:
        return 0
    variants = {keyword}
    if "-" in keyword:
        variants.add(keyword.replace("-", " "))
    if " " in keyword:
        variants.add(keyword.replace(" ", "-"))

    total = 0
    for variant in variants:
        if any(ord(char) > 127 for char in variant):
            total += haystack.count(variant)
            continue
        pattern = rf"(?<![a-z0-9]){re.escape(variant)}(?![a-z0-9])"
        total += len(re.findall(pattern, haystack))
    return total


def parse_chapters(description: str, duration: float | None) -> list[Chapter]:
    chapters: list[Chapter] = []
    seen: set[int] = set()
    for match in TIMESTAMP_RE.finditer(description or ""):
        timecode = match.group(1)
        seconds = parse_timecode(timecode)
        if seconds in seen:
            continue
        seen.add(seconds)
        chapters.append(Chapter(timecode=timecode, seconds=seconds, title=match.group(2).strip()))

    if chapters:
        return chapters

    total = int(duration or 0)
    if total <= 0:
        return []

    fallback_points = [0.1, 0.25, 0.4, 0.55, 0.7, 0.85]
    generated: list[Chapter] = []
    for index, ratio in enumerate(fallback_points, start=1):
        seconds = min(max(int(total * ratio), 0), max(total - 1, 0))
        generated.append(
            Chapter(
                timecode=format_timecode(seconds),
                seconds=seconds,
                title=f"Auto checkpoint {index}",
            )
        )
    return generated


def fetch_metadata(url: str) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--dump-single-json",
        "--skip-download",
        url,
    ]
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return json.loads(result.stdout)


def download_thumbnail(thumbnail_url: str | None, target: Path) -> Path | None:
    if not thumbnail_url:
        return None
    response = requests.get(thumbnail_url, timeout=60)
    response.raise_for_status()
    target.write_bytes(response.content)
    return target


def download_video(url: str, target: Path, format_id: str) -> Path:
    opts = {
        "format": format_id,
        "outtmpl": str(target),
        "quiet": True,
        "no_warnings": True,
    }
    with YoutubeDL(opts) as ydl:
        ydl.download([url])
    return target


def select_frame_chapters(chapters: list[Chapter], max_frames: int) -> list[Chapter]:
    if len(chapters) <= max_frames:
        return chapters

    stride = max(len(chapters) / max_frames, 1)
    chosen: list[Chapter] = []
    index = 0.0
    while len(chosen) < max_frames and int(index) < len(chapters):
        chosen.append(chapters[int(index)])
        index += stride

    if chapters[-1] not in chosen:
        chosen[-1] = chapters[-1]
    return chosen


def extract_frames(video_path: Path, chapters: list[Chapter], frames_dir: Path) -> list[dict[str, Any]]:
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    results: list[dict[str, Any]] = []
    try:
        for index, chapter in enumerate(chapters, start=1):
            capture.set(cv2.CAP_PROP_POS_MSEC, chapter.seconds * 1000)
            ok, frame = capture.read()
            if not ok:
                continue
            filename = f"{index:02d}_{sanitize_slug(chapter.title)[:50] or 'frame'}.jpg"
            output_path = frames_dir / filename
            cv2.imwrite(str(output_path), frame)
            results.append(
                {
                    "title": chapter.title,
                    "timecode": chapter.timecode,
                    "seconds": chapter.seconds,
                    "path": output_path,
                }
            )
    finally:
        capture.release()
    return results


def build_output_dir(root: Path, report_date: str, video_id: str, title: str) -> Path:
    slug = sanitize_slug(title)[:60]
    return root / f"{report_date}_{video_id}_{slug}"


def infer_topics(metadata: dict[str, Any], chapters: list[Chapter]) -> tuple[str, list[str], dict[str, int]]:
    fields = [
        metadata.get("title", ""),
        metadata.get("description", ""),
        " ".join(metadata.get("tags") or []),
        " ".join(chapter.title for chapter in chapters),
    ]
    haystack = "\n".join(fields).lower()
    scores: dict[str, int] = {}
    for topic, rule in TOPIC_RULES.items():
        score = 0
        for keyword in rule["keywords"]:
            score += count_keyword(haystack, keyword)
        if score > 0:
            scores[topic] = score

    if not scores:
        return "General", [], {}

    ordered = [topic for topic, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))]
    return ordered[0], ordered[1:], scores


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def first_paragraph(text: str) -> str:
    paragraphs = [chunk.strip() for chunk in (text or "").split("\n\n") if chunk.strip()]
    return paragraphs[0] if paragraphs else ""


def write_markdown(
    path: Path,
    metadata: dict[str, Any],
    chapters: list[Chapter],
    frames: list[dict[str, Any]],
    report_dir: Path,
    primary_topic: str,
    secondary_topics: list[str],
    for_feishu: bool,
) -> None:
    title = metadata.get("title", "Untitled")
    description = metadata.get("description", "")
    thesis = first_paragraph(description)
    tags = metadata.get("tags") or []
    uploader = metadata.get("uploader", "Unknown")
    upload_date = metadata.get("upload_date", "")
    readable_upload_date = (
        datetime.strptime(upload_date, "%Y%m%d").strftime("%Y-%m-%d") if upload_date else "Unknown"
    )
    duration = metadata.get("duration_string", "Unknown")
    video_url = metadata.get("webpage_url", metadata.get("original_url", ""))

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append("## 课题归类")
    lines.append("")
    lines.append(f"- 主课题：`{primary_topic}`")
    if secondary_topics:
        lines.append(f"- 相关课题：{', '.join(f'`{topic}`' for topic in secondary_topics)}")
    else:
        lines.append("- 相关课题：")
    lines.append("")
    lines.append("## 核心判断")
    lines.append("")
    if thesis:
        lines.append(thesis)
    else:
        lines.append("这一部分需要在看完视频截图后补成一句话判断。")
    lines.append("")
    lines.append("## 内容主线")
    lines.append("")
    lines.append("- 这期视频主要在讲什么：")
    lines.append("- 它回答了哪些关键技术问题：")
    lines.append("- 对 Embodied AI 研究或产品有什么启发：")
    lines.append("")
    lines.append("## 章节脉络")
    lines.append("")
    for chapter in chapters:
        lines.append(f"- `{chapter.timecode}` {chapter.title}")
    lines.append("")
    lines.append("## 截图证据")
    lines.append("")
    for frame in frames:
        relative_path = frame["path"].relative_to(report_dir).as_posix()
        lines.append(f"### {frame['timecode']} {frame['title']}")
        lines.append("")
        if for_feishu:
            lines.append(f"> 截图文件：`{relative_path}`")
            lines.append(">")
            lines.append("> 推送到飞书前，请先上传该图片并替换为飞书图片素材。")
            lines.append("")
        else:
            lines.append(f"![{frame['title']}]({relative_path})")
            lines.append("")
        lines.append("- 画面信息：")
        lines.append("- 对应观点：")
        lines.append("- 为什么重要：")
        lines.append("")
    lines.append("## 可拆分 Wiki 主题")
    lines.append("")
    lines.append("- 主题 1：")
    lines.append("- 主题 2：")
    lines.append("- 主题 3：")
    lines.append("")
    lines.append("## 延伸研究")
    lines.append("")
    lines.append("- 相关论文：")
    lines.append("- 相关项目：")
    lines.append("- 建议继续跟进的问题：")
    lines.append("")
    lines.append("## 参考与署名")
    lines.append("")
    lines.append(f"- 视频：{video_url}")
    lines.append(f"- 标题：{title}")
    lines.append(f"- UP主：{uploader}")
    lines.append(f"- 发布时间：{readable_upload_date}")
    lines.append(f"- 时长：{duration}")
    lines.append(f"- 视频 ID：{metadata.get('id', 'Unknown')}")
    if tags:
        lines.append(f"- 标签：{', '.join(tags)}")
    lines.append("- 说明：本次抓取优先使用 Bilibili 原始信息；若官方字幕不可用，则退化为“视频简介时间线 + 章节截图 + 公开项目资料”。")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    metadata = fetch_metadata(args.url)
    chapters = parse_chapters(metadata.get("description", ""), metadata.get("duration"))
    primary_topic, secondary_topics, topic_scores = infer_topics(metadata, chapters)
    topic_slug = TOPIC_RULES.get(primary_topic, {}).get("slug", sanitize_slug(primary_topic))
    report_dir = build_output_dir(
        output_root / "topics" / topic_slug / "videos",
        args.report_date,
        metadata.get("id", "unknown"),
        metadata.get("title", "video"),
    )
    assets_dir = report_dir / "assets"
    frames_dir = assets_dir / "frames"
    assets_dir.mkdir(parents=True, exist_ok=True)
    selected_chapters = select_frame_chapters(chapters, args.max_frames)

    thumbnail_path = download_thumbnail(metadata.get("thumbnail"), assets_dir / "cover.jpg")
    video_path = download_video(args.url, assets_dir / "video.mp4", args.frame_format)
    frames = extract_frames(video_path, selected_chapters, frames_dir)

    metadata_payload = dict(metadata)
    metadata_payload["extracted_chapters"] = [
        {"timecode": chapter.timecode, "seconds": chapter.seconds, "title": chapter.title}
        for chapter in chapters
    ]
    metadata_payload["frame_chapters"] = [
        {"timecode": chapter.timecode, "seconds": chapter.seconds, "title": chapter.title}
        for chapter in selected_chapters
    ]
    metadata_payload["topic_routing"] = {
        "primary_topic": primary_topic,
        "secondary_topics": secondary_topics,
        "scores": topic_scores,
    }
    if thumbnail_path:
        metadata_payload["cover_path"] = str(thumbnail_path)

    write_json(report_dir / "metadata.json", metadata_payload)
    write_markdown(
        report_dir / "report.md",
        metadata,
        selected_chapters,
        frames,
        report_dir,
        primary_topic,
        secondary_topics,
        args.for_feishu,
    )

    if not args.keep_video and video_path.exists():
        video_path.unlink()

    manifest = {
        "report_dir": str(report_dir),
        "report_markdown": str(report_dir / "report.md"),
        "metadata_json": str(report_dir / "metadata.json"),
        "frame_count": len(frames),
        "primary_topic": primary_topic,
        "secondary_topics": secondary_topics,
    }
    write_json(report_dir / "manifest.json", manifest)

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
