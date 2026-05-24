#!/usr/bin/env python
from __future__ import annotations

import argparse
import html
import json
import re
import warnings
from datetime import datetime
from typing import Any
from urllib.parse import quote

warnings.filterwarnings("ignore", message="urllib3 .* doesn't match a supported version!", category=Warning)
import requests
from requests.exceptions import RequestsDependencyWarning


API_URL = "https://api.bilibili.com/x/web-interface/search/all/v2"
TAG_RE = re.compile(r"<[^>]+>")
warnings.simplefilter("ignore", RequestsDependencyWarning)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search Bilibili videos by keyword.")
    parser.add_argument("keyword", help="Chinese keyword string for Bilibili video search")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of candidates to print")
    return parser.parse_args()


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = TAG_RE.sub("", value)
    return re.sub(r"\s+", " ", value).strip()


def format_timestamp(value: int | str | None) -> str:
    if value in (None, ""):
        return ""
    return datetime.fromtimestamp(int(value)).strftime("%Y-%m-%d")


def fetch_candidates(keyword: str, limit: int) -> list[dict[str, Any]]:
    headers = {
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36"
        ),
        "referer": f"https://search.bilibili.com/all?keyword={quote(keyword)}",
    }
    params = {"keyword": keyword, "page": 1}
    response = requests.get(API_URL, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    payload = response.json()
    result_groups = payload.get("data", {}).get("result", [])
    video_group = next((item for item in result_groups if item.get("result_type") == "video"), {})
    results = video_group.get("data", [])[:limit]
    normalized: list[dict[str, Any]] = []
    for item in results:
        bvid = item.get("bvid", "")
        normalized.append(
            {
                "title": clean_text(item.get("title", "")),
                "bvid": bvid,
                "url": f"https://www.bilibili.com/video/{bvid}/" if bvid else item.get("arcurl", ""),
                "uploader": item.get("author", ""),
                "duration": item.get("duration", ""),
                "publish_date": format_timestamp(item.get("pubdate")),
                "play": item.get("play", ""),
                "description": clean_text(item.get("description", "")),
                "tag": clean_text(item.get("tag", "")),
            }
        )
    return normalized


def main() -> int:
    args = parse_args()
    candidates = fetch_candidates(args.keyword, args.limit)
    print(json.dumps({"keyword": args.keyword, "candidates": candidates}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
