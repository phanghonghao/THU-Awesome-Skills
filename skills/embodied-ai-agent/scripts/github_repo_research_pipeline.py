#!/usr/bin/env python
from __future__ import annotations

import argparse
import base64
import json
import math
import re
import warnings
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

warnings.filterwarnings("ignore", message="urllib3 .* doesn't match a supported version!", category=Warning)
import requests
from requests.exceptions import RequestsDependencyWarning


API_ROOT = "https://api.github.com"
warnings.simplefilter("ignore", RequestsDependencyWarning)
REPO_URL_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/#?]+)")
OWNER_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

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
            "robot transformer",
            "robot foundation model",
        ],
    },
    "WM": {
        "slug": "wm",
        "keywords": [
            "world model",
            "world-model",
            "world action model",
            "world-action-model",
            "dreamer",
            "dreamerv3",
            "genie",
            "unisim",
            "cosmos",
            "latent dynamics",
        ],
    },
    "GR00T": {
        "slug": "gr00t",
        "keywords": ["gr00t", "groot", "isaac gr00t", "humanoid", "humanoid robot"],
    },
    "ALOHA": {
        "slug": "aloha",
        "keywords": [
            "aloha",
            "mobile aloha",
            "action chunking",
            "action chunking transformer",
            "teleoperation",
            "bimanual",
        ],
    },
    "DiffusionPolicy": {
        "slug": "diffusion-policy",
        "keywords": ["diffusion policy", "flow matching", "diffusion", "rectified flow"],
    },
    "RL": {
        "slug": "rl",
        "keywords": ["reinforcement learning", "offline rl", "ppo", "sac", "policy optimization"],
    },
}


@dataclass
class RepoCandidate:
    full_name: str
    html_url: str
    description: str
    stars: int
    forks: int
    language: str
    topics: list[str]
    created_at: str
    updated_at: str
    homepage: str
    score: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect GitHub repository metadata and turn it into a Chinese wiki draft."
    )
    parser.add_argument("target", help="GitHub URL, owner/repo, or keyword")
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
    parser.add_argument("--limit", type=int, default=8, help="Maximum related repositories in keyword mode")
    parser.add_argument(
        "--for-feishu",
        action="store_true",
        help="Generate Feishu-safe markdown without local relative SVG embeds",
    )
    return parser.parse_args()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "item"


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


def github_get(path: str, params: dict[str, Any] | None = None) -> Any:
    headers = {
        "accept": "application/vnd.github+json",
        "user-agent": "multi-source-research-agent",
    }
    response = requests.get(f"{API_ROOT}{path}", params=params, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def parse_repo_target(target: str) -> str | None:
    target = target.strip()
    url_match = REPO_URL_RE.match(target)
    if url_match:
        owner = url_match.group(1)
        repo = url_match.group(2).removesuffix(".git")
        return f"{owner}/{repo}"
    if OWNER_REPO_RE.match(target):
        return target
    return None


def keyword_tokens(keyword: str) -> list[str]:
    return [token for token in re.split(r"[^a-zA-Z0-9]+", keyword.lower()) if len(token) >= 2]


def score_candidate(item: dict[str, Any], keyword: str) -> float:
    haystack = " ".join(
        [
            item.get("name", "") or "",
            item.get("full_name", "") or "",
            item.get("description", "") or "",
            " ".join(item.get("topics", []) or []),
        ]
    ).lower()
    keyword_lower = keyword.lower().strip()
    score = 0.0
    if keyword_lower and keyword_lower in haystack:
        score += 80.0
    for token in keyword_tokens(keyword):
        score += haystack.count(token) * 8.0
    score += min(math.log10(max(item.get("stargazers_count", 0), 1)) * 12.0, 60.0)
    return score


def normalize_candidate(item: dict[str, Any], keyword: str) -> RepoCandidate:
    return RepoCandidate(
        full_name=item.get("full_name", ""),
        html_url=item.get("html_url", ""),
        description=item.get("description", "") or "",
        stars=item.get("stargazers_count", 0),
        forks=item.get("forks_count", 0),
        language=item.get("language", "") or "",
        topics=item.get("topics", []) or [],
        created_at=item.get("created_at", ""),
        updated_at=item.get("updated_at", ""),
        homepage=item.get("homepage", "") or "",
        score=score_candidate(item, keyword),
    )


def search_repositories(keyword: str, limit: int) -> list[RepoCandidate]:
    payload = github_get(
        "/search/repositories",
        params={
            "q": keyword,
            "sort": "stars",
            "order": "desc",
            "per_page": max(1, min(limit, 20)),
        },
    )
    return [normalize_candidate(item, keyword) for item in payload.get("items", [])[:limit]]


def fetch_repo(repo_full_name: str) -> dict[str, Any]:
    return github_get(f"/repos/{repo_full_name}")


def fetch_releases(repo_full_name: str) -> list[dict[str, Any]]:
    releases = github_get(f"/repos/{repo_full_name}/releases", params={"per_page": 5})
    return releases if isinstance(releases, list) else []


def fetch_readme(repo_full_name: str) -> str:
    try:
        payload = github_get(f"/repos/{repo_full_name}/readme")
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return ""
        raise
    content = payload.get("content", "")
    encoding = payload.get("encoding", "")
    if encoding == "base64" and content:
        return base64.b64decode(content).decode("utf-8", errors="replace")
    return ""


def infer_topics(repo: dict[str, Any], readme_text: str, keyword: str) -> tuple[str, list[str], dict[str, int]]:
    fields = [
        keyword,
        repo.get("name", "") or "",
        repo.get("full_name", "") or "",
        repo.get("description", "") or "",
        " ".join(repo.get("topics", []) or []),
        readme_text[:12000],
    ]
    haystack = "\n".join(fields).lower()
    scores: dict[str, int] = {}
    for topic, rule in TOPIC_RULES.items():
        score = 0
        for topic_keyword in rule["keywords"]:
            score += count_keyword(haystack, topic_keyword)
        if score > 0:
            scores[topic] = score
    if not scores:
        return "General", [], {}
    ordered = [topic for topic, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))]
    return ordered[0], ordered[1:], scores


def format_date(value: str) -> str:
    return value[:10] if value else ""


def first_meaningful_paragraph(text: str) -> str:
    for paragraph in re.split(r"\n\s*\n", text):
        clean = paragraph.strip()
        if not clean or clean.startswith("#") or clean.startswith("!"):
            continue
        clean = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", clean)
        clean = re.sub(r"`{1,3}", "", clean)
        clean = re.sub(r"\s+", " ", clean)
        if len(clean) >= 30:
            return clean
    return ""


def extract_headings(readme_text: str, limit: int = 6) -> list[str]:
    headings: list[str] = []
    for line in readme_text.splitlines():
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
            if heading:
                headings.append(heading)
        if len(headings) >= limit:
            break
    return headings


def make_related_candidates(candidates: list[RepoCandidate], selected_repo: str) -> list[RepoCandidate]:
    related = [candidate for candidate in candidates if candidate.full_name != selected_repo]
    return sorted(related, key=lambda item: (-item.score, -item.stars, item.full_name))


def build_output_dir(root: Path, topic_slug: str, report_date: str, repo_full_name: str) -> Path:
    owner, repo = repo_full_name.split("/", 1)
    return root / "topics" / topic_slug / "github" / f"{report_date}_{slugify(owner)}_{slugify(repo)}"


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def star_text(value: int) -> str:
    return f"{value / 1000:.1f}k" if value >= 1000 else str(value)


def ensure_svg(report_dir: Path, repo: dict[str, Any], primary_topic: str, related: list[RepoCandidate]) -> Path:
    diagram_dir = report_dir / "assets" / "diagrams"
    diagram_dir.mkdir(parents=True, exist_ok=True)
    output = diagram_dir / "github-topic-map.svg"
    repo_name = repo.get("full_name", "unknown/repo")
    language = repo.get("language", "Unknown") or "Unknown"
    stats = f"Stars {star_text(repo.get('stargazers_count', 0))} | Forks {star_text(repo.get('forks_count', 0))}"
    related_names = [candidate.full_name for candidate in related[:4]] or ["No related repos"]
    related_lines = "".join(
        f'<text x="430" y="{170 + index * 38}" font-size="18" fill="#19313d">{escape(name)}</text>'
        for index, name in enumerate(related_names)
    )
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <rect width="1280" height="720" fill="#f6f2e9"/>
  <rect x="56" y="48" width="1168" height="624" rx="28" fill="#fffdf8" stroke="#d9cfbf" stroke-width="2"/>
  <text x="90" y="112" font-size="34" font-weight="700" fill="#173243">GitHub Research Map</text>
  <text x="90" y="152" font-size="20" fill="#5f6f79">{escape(repo_name)}</text>
  <rect x="90" y="198" width="300" height="240" rx="24" fill="#dff1ea" stroke="#7ab89f" stroke-width="2"/>
  <text x="118" y="248" font-size="24" font-weight="700" fill="#0b6e4f">Primary Topic</text>
  <text x="118" y="294" font-size="36" font-weight="700" fill="#12394a">{escape(primary_topic)}</text>
  <text x="118" y="340" font-size="20" fill="#385260">{escape(language)}</text>
  <text x="118" y="378" font-size="18" fill="#385260">{escape(stats)}</text>
  <rect x="420" y="198" width="724" height="240" rx="24" fill="#f1f6fb" stroke="#b9ccd9" stroke-width="2"/>
  <text x="448" y="248" font-size="24" font-weight="700" fill="#173243">Related Repositories</text>
  {related_lines}
  <rect x="90" y="478" width="1054" height="132" rx="24" fill="#fff4ee" stroke="#e3c0af" stroke-width="2"/>
  <text x="118" y="528" font-size="24" font-weight="700" fill="#b4582b">Interpretation</text>
  <text x="118" y="568" font-size="20" fill="#4e5b63">This repo is routed into the topic knowledge base first, then expanded into Chinese wiki pages and related topic notes.</text>
</svg>
"""
    output.write_text(svg, encoding="utf-8")
    return output


def write_report(
    path: Path,
    report_dir: Path,
    repo: dict[str, Any],
    keyword: str,
    readme_text: str,
    releases: list[dict[str, Any]],
    primary_topic: str,
    secondary_topics: list[str],
    related: list[RepoCandidate],
    diagram_path: Path,
    for_feishu: bool,
) -> None:
    summary = first_meaningful_paragraph(readme_text) or (repo.get("description", "") or "这一部分需要后续补充判断。")
    headings = extract_headings(readme_text)
    relative_diagram = diagram_path.relative_to(report_dir).as_posix()
    lines: list[str] = []
    lines.append(f"# {repo.get('full_name', 'unknown/repo')}")
    lines.append("")
    lines.append("## 课题归类")
    lines.append("")
    lines.append(f"- 主课题：`{primary_topic}`")
    lines.append(f"- 相关课题：{', '.join(f'`{item}`' for item in secondary_topics) if secondary_topics else ''}")
    lines.append(f"- 检索入口：`{keyword}`")
    lines.append("")
    lines.append("## 核心判断")
    lines.append("")
    lines.append(summary)
    lines.append("")
    lines.append("## 仓库概况")
    lines.append("")
    lines.append(f"- 仓库：{repo.get('html_url', '')}")
    lines.append(f"- Stars：{repo.get('stargazers_count', 0)}")
    lines.append(f"- Forks：{repo.get('forks_count', 0)}")
    lines.append(f"- Language：{repo.get('language', '') or 'Unknown'}")
    lines.append(f"- 创建时间：{format_date(repo.get('created_at', ''))}")
    lines.append(f"- 最近更新：{format_date(repo.get('updated_at', ''))}")
    if repo.get("homepage"):
        lines.append(f"- Homepage：{repo.get('homepage')}")
    if repo.get("topics"):
        lines.append(f"- Topics：{', '.join(repo.get('topics', []))}")
    lines.append("")
    lines.append("## README 主线")
    lines.append("")
    if headings:
        for heading in headings:
            lines.append(f"- {heading}")
    else:
        lines.append("- 当前 README 标题结构较少，建议补看源码与 issues。")
    lines.append("")
    lines.append("## 版本与活跃度")
    lines.append("")
    if releases:
        for release in releases[:5]:
            lines.append(f"- `{release.get('tag_name', '')}` | {format_date(release.get('published_at', ''))} | {release.get('name', '')}")
    else:
        lines.append("- 当前未发现正式 release，可重点关注提交历史与 issues。")
    lines.append("")
    lines.append("## 技术地图")
    lines.append("")
    if for_feishu:
        lines.append(f"> 图文件：`{relative_diagram}`")
        lines.append(">")
        lines.append("> 推送到飞书前，请先把 SVG 渲染成 PNG，再上传为飞书图片素材。")
    else:
        lines.append(f"![github topic map]({relative_diagram})")
    lines.append("")
    lines.append("## 相关仓库")
    lines.append("")
    for candidate in related[:5]:
        lines.append(
            f"- [{candidate.full_name}]({candidate.html_url}) | Stars {candidate.stars} | {candidate.language or 'Unknown'} | {candidate.description}"
        )
    if not related:
        lines.append("- 当前没有可直接并列的相关仓库候选。")
    lines.append("")
    lines.append("## 可拆分 Wiki 主题")
    lines.append("")
    lines.append(f"- {primary_topic} 方法总览")
    lines.append(f"- {repo.get('name', 'repo')} 仓库拆解")
    lines.append("- 数据、训练与评测路径")
    lines.append("")
    lines.append("## 延伸研究")
    lines.append("")
    lines.append("- 推荐继续查 README、论文、项目主页和 issues 中的路线图。")
    lines.append("- 如果是世界模型相关仓库，建议补看规划、动作条件建模和仿真闭环。")
    lines.append("")
    lines.append("## 参考与署名")
    lines.append("")
    lines.append("- 来源类型：GitHub 仓库调研")
    lines.append(f"- 检索关键词：{keyword}")
    lines.append(f"- 仓库链接：{repo.get('html_url', '')}")
    lines.append(f"- 仓库名：{repo.get('full_name', '')}")
    lines.append(f"- 作者 / 组织：{repo.get('owner', {}).get('login', '')}")
    lines.append(f"- 创建时间：{format_date(repo.get('created_at', ''))}")
    lines.append(f"- 最近更新：{format_date(repo.get('updated_at', ''))}")
    lines.append("- 说明：本次整理基于 GitHub 仓库元信息、README、release 与相关候选仓库。")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_wiki_draft(
    path: Path,
    repo: dict[str, Any],
    keyword: str,
    readme_text: str,
    primary_topic: str,
    related: list[RepoCandidate],
) -> None:
    summary = first_meaningful_paragraph(readme_text) or (repo.get("description", "") or "待补充")
    lines: list[str] = []
    lines.append(f"# {primary_topic}：{repo.get('name', 'repo')} 仓库研究草稿")
    lines.append("")
    lines.append("> 这是一份从 GitHub 仓库进入中文 Wiki 的专题草稿，优先回答“这个仓库为什么值得放进该课题板块”。")
    lines.append("")
    lines.append("## 背景与目标")
    lines.append("")
    lines.append(f"围绕关键词 `{keyword}` 检索 GitHub 后，当前优先沉淀 `{repo.get('full_name', '')}`，并将其路由到 `{primary_topic}` 板块。")
    lines.append("")
    lines.append("## 核心判断")
    lines.append("")
    lines.append(f"- {summary}")
    if repo.get("stargazers_count", 0) >= 100:
        lines.append("- 仓库具备一定社区影响力，适合纳入持续追踪清单。")
    else:
        lines.append("- 仓库影响力仍需结合提交活跃度和外部引用进一步判断。")
    lines.append("")
    lines.append("## 技术抓手")
    lines.append("")
    lines.append("- 仓库解决的问题：")
    lines.append("- 输入 / 状态如何表示：")
    lines.append("- 输出对象是动作、规划还是世界状态：")
    lines.append("- 与现有 WM / VLA / RL 方案的差异：")
    lines.append("")
    lines.append("## 仓库调研")
    lines.append("")
    lines.append(f"- 仓库：[{repo.get('full_name', '')}]({repo.get('html_url', '')})")
    lines.append(f"- Stars / Forks：{repo.get('stargazers_count', 0)} / {repo.get('forks_count', 0)}")
    lines.append(f"- 语言：{repo.get('language', '') or 'Unknown'}")
    lines.append(f"- Topics：{', '.join(repo.get('topics', [])) if repo.get('topics') else '待补充'}")
    lines.append("")
    lines.append("## 相关仓库")
    lines.append("")
    for candidate in related[:5]:
        lines.append(f"- [{candidate.full_name}]({candidate.html_url})：{candidate.description}")
    if not related:
        lines.append("- 待继续补充同类仓库。")
    lines.append("")
    lines.append("## 待补充材料")
    lines.append("")
    lines.append("- 论文与项目主页")
    lines.append("- 训练数据与 benchmark")
    lines.append("- 与 World Action Model 的边界")
    lines.append("- 是否能映射到飞书现有 WM 子板块")
    lines.append("")
    lines.append("## 参考与署名")
    lines.append("")
    lines.append("- 来源类型：GitHub 仓库调研")
    lines.append(f"- 检索关键词：{keyword}")
    lines.append(f"- 仓库链接：{repo.get('html_url', '')}")
    lines.append(f"- 仓库名：{repo.get('full_name', '')}")
    lines.append("- 说明：本稿基于 GitHub API 抓取结果自动整理，后续应补人工判断。")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_topic_notes(report_dir: Path, repo: dict[str, Any], primary_topic: str, related: list[RepoCandidate]) -> list[str]:
    topic_dir = report_dir / "topics"
    topic_dir.mkdir(parents=True, exist_ok=True)

    repo_note = topic_dir / f"{slugify(repo.get('name', 'repo'))}-repo-note.md"
    repo_note.write_text(
        "\n".join(
            [
                f"# {repo.get('full_name', '')} 仓库拆解",
                "",
                "## 建议关注",
                "",
                f"- 主课题：`{primary_topic}`",
                f"- Stars：{repo.get('stargazers_count', 0)}",
                f"- Forks：{repo.get('forks_count', 0)}",
                f"- 描述：{repo.get('description', '') or '待补充'}",
                "",
                "## 后续检查项",
                "",
                "- 核心模块与目录结构",
                "- 训练入口与评测脚本",
                "- 是否有论文或项目主页",
                "",
            ]
        ),
        encoding="utf-8",
    )

    landscape_note = topic_dir / f"{slugify(primary_topic)}-landscape.md"
    landscape_lines = [
        f"# {primary_topic} 相关仓库横向观察",
        "",
        "## 当前候选",
        "",
    ]
    for candidate in related[:6]:
        landscape_lines.append(f"- [{candidate.full_name}]({candidate.html_url}) | Stars {candidate.stars} | {candidate.description}")
    if not related:
        landscape_lines.append("- 暂无并列候选。")
    landscape_lines += [
        "",
        "## 建议补充维度",
        "",
        "- 数据来源与闭环方式",
        "- 是否包含动作条件建模",
        "- 是否提供可复现实验配置",
        "",
    ]
    landscape_note.write_text("\n".join(landscape_lines), encoding="utf-8")
    return [str(repo_note), str(landscape_note)]


def prepare_repo(target: str, limit: int) -> tuple[str, dict[str, Any], list[RepoCandidate]]:
    repo_full_name = parse_repo_target(target)
    if repo_full_name:
        repo = fetch_repo(repo_full_name)
        keyword = repo_full_name
        candidates = [normalize_candidate(repo, keyword)]
        return keyword, repo, candidates

    keyword = target.strip()
    candidates = search_repositories(keyword, limit)
    if not candidates:
        raise RuntimeError(f"No GitHub repositories found for keyword: {keyword}")
    selected = sorted(candidates, key=lambda item: (-item.score, -item.stars, item.full_name))[0]
    repo = fetch_repo(selected.full_name)
    return keyword, repo, candidates


def main() -> int:
    args = parse_args()
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    keyword, repo, candidates = prepare_repo(args.target, args.limit)
    releases = fetch_releases(repo["full_name"])
    readme_text = fetch_readme(repo["full_name"])
    primary_topic, secondary_topics, topic_scores = infer_topics(repo, readme_text, keyword)
    topic_slug = TOPIC_RULES.get(primary_topic, {}).get("slug", slugify(primary_topic))
    report_dir = build_output_dir(output_root, topic_slug, args.report_date, repo["full_name"])
    report_dir.mkdir(parents=True, exist_ok=True)

    related = make_related_candidates(candidates, repo["full_name"])
    diagram_path = ensure_svg(report_dir, repo, primary_topic, related)

    metadata_payload = dict(repo)
    metadata_payload["search_keyword"] = keyword
    metadata_payload["related_candidates"] = [asdict(candidate) for candidate in related]
    metadata_payload["release_summary"] = releases[:5]
    metadata_payload["readme_headings"] = extract_headings(readme_text)
    metadata_payload["topic_routing"] = {
        "primary_topic": primary_topic,
        "secondary_topics": secondary_topics,
        "scores": topic_scores,
    }
    metadata_payload["diagram_path"] = str(diagram_path)
    write_json(report_dir / "metadata.json", metadata_payload)

    write_report(
        report_dir / "report.md",
        report_dir,
        repo,
        keyword,
        readme_text,
        releases,
        primary_topic,
        secondary_topics,
        related,
        diagram_path,
        args.for_feishu,
    )
    write_wiki_draft(report_dir / "wiki-draft.md", repo, keyword, readme_text, primary_topic, related)
    topic_notes = write_topic_notes(report_dir, repo, primary_topic, related)

    manifest = {
        "report_dir": str(report_dir),
        "report_markdown": str(report_dir / "report.md"),
        "wiki_draft": str(report_dir / "wiki-draft.md"),
        "metadata_json": str(report_dir / "metadata.json"),
        "topic_notes": topic_notes,
        "diagram_svg": str(diagram_path),
        "selected_repo": repo["full_name"],
        "search_keyword": keyword,
        "primary_topic": primary_topic,
        "secondary_topics": secondary_topics,
        "related_count": len(related),
    }
    write_json(report_dir / "manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
