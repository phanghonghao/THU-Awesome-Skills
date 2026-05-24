#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import math
import re
import warnings
from typing import Any

warnings.filterwarnings("ignore", message="urllib3 .* doesn't match a supported version!", category=Warning)
import requests
from requests.exceptions import RequestsDependencyWarning


API_URL = "https://api.github.com/search/repositories"
warnings.simplefilter("ignore", RequestsDependencyWarning)


def keyword_tokens(keyword: str) -> list[str]:
    return [token for token in re.split(r"[^a-zA-Z0-9]+", keyword.lower()) if len(token) >= 2]


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


def score_repo(item: dict[str, Any], keyword: str) -> float:
    haystack = " ".join(
        [
            item.get("name", "") or "",
            item.get("full_name", "") or "",
            item.get("description", "") or "",
            " ".join(item.get("topics", []) or []),
        ]
    ).lower()
    score = count_keyword(haystack, keyword) * 50.0
    for token in keyword_tokens(keyword):
        score += count_keyword(haystack, token) * 8.0
    score += min(math.log10(max(item.get("stargazers_count", 0), 1)) * 12.0, 60.0)
    return score


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search GitHub repositories by keyword.")
    parser.add_argument("keyword", help="Keyword string for GitHub repository search")
    parser.add_argument("--limit", type=int, default=8, help="Maximum number of candidates to print")
    parser.add_argument(
        "--sort",
        default="stars",
        choices=["stars", "updated"],
        help="GitHub API sort field",
    )
    return parser.parse_args()


def normalize_repo(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "full_name": item.get("full_name", ""),
        "name": item.get("name", ""),
        "url": item.get("html_url", ""),
        "description": item.get("description", "") or "",
        "stars": item.get("stargazers_count", 0),
        "forks": item.get("forks_count", 0),
        "language": item.get("language", "") or "",
        "topics": item.get("topics", []) or [],
        "created_at": item.get("created_at", ""),
        "updated_at": item.get("updated_at", ""),
        "homepage": item.get("homepage", "") or "",
        "score": item.get("score", 0),
    }


def fetch_one_query(query: str, limit: int, sort: str) -> list[dict[str, Any]]:
    headers = {
        "accept": "application/vnd.github+json",
        "user-agent": "multi-source-research-agent",
    }
    params = {
        "q": query,
        "sort": sort,
        "order": "desc",
        "per_page": max(1, min(limit, 20)),
    }
    response = requests.get(API_URL, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json().get("items", [])


def fetch_candidates(keyword: str, limit: int, sort: str) -> dict[str, Any]:
    raw_items: list[dict[str, Any]] = []
    queries = [f"\"{keyword}\"", keyword] if " " in keyword.strip() else [keyword]
    seen: set[str] = set()
    for query in queries:
        for item in fetch_one_query(query, max(limit * 2, 10), sort):
            full_name = item.get("full_name", "")
            if not full_name or full_name in seen:
                continue
            seen.add(full_name)
            item["score"] = score_repo(item, keyword)
            raw_items.append(item)
    ranked = sorted(raw_items, key=lambda item: (-item.get("score", 0), -item.get("stargazers_count", 0), item.get("full_name", "")))
    return {
        "keyword": keyword,
        "total_count": len(raw_items),
        "candidates": [normalize_repo(item) for item in ranked[:limit]],
    }


def main() -> int:
    args = parse_args()
    print(json.dumps(fetch_candidates(args.keyword, args.limit, args.sort), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
