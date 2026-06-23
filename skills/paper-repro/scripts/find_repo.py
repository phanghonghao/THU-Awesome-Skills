"""Find candidate code repositories for a paper.

Pipeline:
  1. resolve an arXiv id (if a URL/id given) and fetch the paper title from arXiv
  2. search GitHub by TITLE keywords (much better recall than searching the bare id)
Note: PapersWithCode's public API was deprecated (returns HTML now), so we no
longer query it; GitHub + arXiv cover the common case.

Network layer mirrors /web-search-fallback: requests -> curl -> warn.

Usage:
    python find_repo.py "1706.03762"
    python find_repo.py "https://arxiv.org/abs/1706.03762" --top 8
    python find_repo.py "Attention Is All You Need" --json
"""
import argparse
import json
import re
import sys
import urllib.parse

UA = "paper-repro/0.1 (+local skill)"


def http_get(url, timeout=25):
    """requests -> curl fallback. Returns text or raises RuntimeError."""
    try:
        import requests
        r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception:
        pass
    import subprocess
    try:
        out = subprocess.run(
            ["curl", "-sL", "--max-time", str(timeout), "-A", UA, url],
            capture_output=True, text=True, check=False,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout
    except Exception:
        pass
    raise RuntimeError(f"network failed: {url}")


def extract_arxiv_id(raw):
    m = re.search(r"(\d{4}\.\d{4,5})", raw)
    return m.group(1) if m else None


def fetch_arxiv_title(arxiv_id):
    """Return the paper title for an arXiv id, or '' on failure."""
    import xml.etree.ElementTree as ET
    try:
        xml = http_get(f"http://export.arxiv.org/api/query?id_list={arxiv_id}", timeout=20)
        root = ET.fromstring(xml)
        ns = {"a": "http://www.w3.org/2005/Atom"}
        e = root.find("a:entry", ns)
        if e is not None:
            t = e.find("a:title", ns)
            if t is not None and t.text:
                return " ".join(t.text.split())
    except Exception as e:
        sys.stderr.write(f"[WARN] arxiv title fetch failed: {e}\n")
    return ""


def query_github(q):
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode({
        "q": q, "sort": "stars", "order": "desc", "per_page": 10,
    })
    try:
        data = json.loads(http_get(url))
    except Exception as e:
        sys.stderr.write(f"[WARN] github search failed: {e}\n")
        return []
    out = []
    for r in data.get("items", []):
        out.append({
            "full_name": r.get("full_name"),
            "url": r.get("html_url"),
            "stars": r.get("stargazers_count", 0) or 0,
            "description": (r.get("description") or "")[:140],
            "language": r.get("language"),
        })
    return out


def search_query_from_title(title):
    """Trim a title into good GitHub search keywords."""
    # drop filler words, keep meaningful tokens
    stop = {"a", "an", "the", "of", "for", "and", "to", "in", "on", "with", "is", "are"}
    toks = [t for t in re.split(r"[^A-Za-z0-9]+", title.lower()) if t and t not in stop]
    return " ".join(toks[:8]) if toks else title


def main():
    ap = argparse.ArgumentParser(description="Find code repos for a paper.")
    ap.add_argument("query", help="arXiv id / arXiv URL / paper title")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--json", action="store_true", help="emit JSON instead of table")
    args = ap.parse_args()

    arxiv_id = extract_arxiv_id(args.query)
    title = ""
    if arxiv_id:
        title = fetch_arxiv_title(arxiv_id)
        print(f"[find_repo] arxiv {arxiv_id} -> \"{title}\"")
    gh_q = search_query_from_title(title or args.query)

    results = query_github(gh_q)
    # dedupe by url, sort by stars
    seen, dedup = set(), []
    for r in results:
        if r["url"] and r["url"] not in seen:
            seen.add(r["url"]); dedup.append(r)
    dedup.sort(key=lambda r: r["stars"], reverse=True)
    dedup = dedup[: args.top]

    if not dedup:
        print(f"[find_repo] no candidates for GitHub query: {gh_q!r}")
        return

    if args.json:
        print(json.dumps(dedup, indent=2, ensure_ascii=False))
        return

    print(f"[find_repo] GitHub search: {gh_q!r}\n")
    for i, r in enumerate(dedup, 1):
        lang = f"  [{r['language']}]" if r["language"] else ""
        print(f"  {i:>2}. {r['stars']:>6}* | {r['full_name']}{lang}")
        if r["description"]:
            print(f"         {r['description']}")
        print(f"         {r['url']}")
    print()


if __name__ == "__main__":
    main()
