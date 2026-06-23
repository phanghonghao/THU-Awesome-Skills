"""Analyze a GitHub repo for reproduction feasibility (no full clone needed).

Uses the GitHub tree API to list files, then fetches the most relevant ones
(README, dependency files, training entry, configs) as raw text and greps for
resource signals (n_gpu, deepspeed, batch_size, epochs, dataset paths...).
Emits a JSON feasibility report for the agent to plan a minimal reproduction.

Usage:
    python analyze_repo.py "https://github.com/jadore801120/attention-is-all-you-need-pytorch"
    python analyze_repo.py "owner/repo" --json
"""
import argparse
import json
import re
import sys
import urllib.parse

UA = "paper-repro/0.1 (+local skill)"
API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"

# files we care about (lowercase substrings to match against paths)
README_RE = re.compile(r"(^|/)readme(\.|$)", re.I)
DEP_NAMES = ["requirements", "environment.yml", "environment.yaml", "setup.py",
             "setup.cfg", "pyproject.toml", "Pipfile", "conda.yml"]
ENTRY_RE = re.compile(r"(^|/)(train|main|run|finetune|pretrain)\.(py|sh)$", re.I)
CONFIG_RE = re.compile(r"\.(ya?ml|json|cfg|ini)$", re.I)

KNOWN_LIBS = {"torch", "pytorch", "tensorflow", "jax", "flax", "transformers",
              "accelerate", "deepspeed", "torchtext", "spacy", "numpy", "flash-attn",
              "hydra", "wandb", "datasets", "torchvision"}

# resource signals -> regex
SIGNALS = {
    "n_gpu": r"(?:n_?gpu|num_gpus|world_size|nproc|num_processes)\D{0,3}(\d+)",
    "batch_size": r"batch_?size\D{0,3}(\d+)",
    "epochs": r"(?:epoch[s]?)\D{0,6}(\d{2,4})",
    "deepspeed": r"deepspeed",
    "accelerate": r"accelerate",
    "distributed": r"torch\.distributed|DistributedDataParallel|ddp",
}
HARDWARE_HINTS = re.compile(r"\b(H100|A100|V100|TPU|GPU)s?\b", re.I)
DATASET_HINTS = re.compile(r"(?:data[_-]?(?:set|dir|path)|/data/|download)\s*[=:]\s*([^\s\"'`]+)", re.I)


def http_get(url, timeout=25, headers=None):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    try:
        import requests
        r = requests.get(url, headers=h, timeout=timeout)
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


def parse_owner_repo(s):
    m = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:[./]|$)", s)
    if m:
        return m.group(1)
    if s.count("/") == 1 and " " not in s:
        return s
    raise SystemExit(f"[analyze_repo] cannot parse owner/repo from: {s}")


def get_default_branch(owner_repo):
    try:
        data = json.loads(http_get(f"{API}/repos/{owner_repo}"))
        return data.get("default_branch") or "main"
    except Exception:
        return "main"


def list_tree(owner_repo, branch):
    try:
        data = json.loads(http_get(f"{API}/repos/{owner_repo}/git/trees/{branch}?recursive=1"))
        return [t["path"] for t in data.get("tree", []) if t.get("type") == "blob"]
    except Exception as e:
        sys.stderr.write(f"[WARN] tree fetch failed: {e}\n")
        return []


def classify(paths):
    readme = [p for p in paths if README_RE.search(p)][:1]
    deps, entries, configs = [], [], []
    for p in paths:
        low = p.lower()
        if any(d in low for d in DEP_NAMES) and len(deps) < 4:
            deps.append(p)
        if ENTRY_RE.search(p) and len(entries) < 6:
            entries.append(p)
        if CONFIG_RE.search(p) and "node_modules" not in p and len(configs) < 4:
            configs.append(p)
    # prefer top-level (shortest path) variants
    deps.sort(key=lambda p: (p.count("/"), len(p)))
    entries.sort(key=lambda p: (p.count("/"), len(p)))
    return readme, deps, entries, configs


def fetch_raw(owner_repo, branch, path, max_bytes=200_000):
    try:
        txt = http_get(f"{RAW}/{owner_repo}/{branch}/{path}")
        return txt[:max_bytes]
    except Exception:
        return ""


def grep_signals(texts):
    blob = "\n".join(texts)
    found = {}
    for key, pat in SIGNALS.items():
        m = re.search(pat, blob, re.I)
        if m:
            found[key] = m.group(1) if m.lastindex else True
    hw = sorted(set(h.upper() for h in HARDWARE_HINTS.findall(blob)))
    if hw:
        found["hardware_mentioned"] = hw
    datasets = []
    for line in blob.splitlines():
        m = DATASET_HINTS.search(line)
        if not m or len(datasets) >= 6:
            continue
        cap = m.group(1).strip("'\"`,")[:60]
        # reject markdown borders / pure-punctuation / placeholder captures
        if not re.search(r"[A-Za-z]", cap):
            continue
        if re.fullmatch(r"[=\-|#~_/\s.]+", cap):
            continue
        datasets.append(cap)
    if datasets:
        found["dataset_deps"] = datasets
    return found


def parse_deps(dep_texts):
    deps = set()
    for t in dep_texts:
        for line in t.splitlines():
            line = line.split("#")[0].strip(" =<>~!")
            line = re.sub(r"\[.*\]", "", line)
            if not line or line.startswith("-") or line.startswith("git+"):
                continue
            name = line.split("=")[0].split(":")[0].strip().lower()
            if not name:
                continue
            # collect known-lib hits: literal name first, then sub-tokens
            if name in KNOWN_LIBS:
                deps.add(name)
                continue
            tokens = set(re.split(r"[-_.]", name))
            deps |= (tokens & KNOWN_LIBS)
    return sorted(deps)


def main():
    ap = argparse.ArgumentParser(description="Analyze a repo for repro feasibility.")
    ap.add_argument("repo", help="github URL or owner/repo")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    owner_repo = parse_owner_repo(args.repo)
    branch = get_default_branch(owner_repo)
    paths = list_tree(owner_repo, branch)
    if not paths:
        print(json.dumps({"error": "could not list repo tree", "repo": owner_repo}, indent=2))
        return

    readme, deps_files, entries, configs = classify(paths)
    # fetch the most useful files (cap to stay light)
    to_fetch = readme + deps_files[:2] + entries[:2] + configs[:2]
    contents = {}
    for p in dict.fromkeys(to_fetch):  # dedupe, preserve order
        contents[p] = fetch_raw(owner_repo, branch, p)

    signals = grep_signals(list(contents.values()))
    dep_libs = parse_deps([contents[p] for p in deps_files if contents.get(p)])

    n_gpu = int(signals.get("n_gpu", 1) or 1) if isinstance(signals.get("n_gpu"), str) else 1
    bs = int(signals.get("batch_size", 0) or 0) if isinstance(signals.get("batch_size"), str) else 0
    epochs = int(signals.get("epochs", 0) or 0) if isinstance(signals.get("epochs"), str) else 0

    blockers = []
    if "torchtext" in dep_libs:
        blockers.append("torchtext is deprecated (may not install on Python 3.12+)")
    if signals.get("dataset_deps"):
        blockers.append(f"needs dataset(s): {', '.join(signals['dataset_deps'])}")
    if n_gpu and n_gpu > 1:
        blockers.append(f"configured for {n_gpu} GPUs (multi-GPU)")

    report = {
        "repo": owner_repo,
        "url": f"https://github.com/{owner_repo}",
        "branch": branch,
        "readme": readme[0] if readme else None,
        "readme_excerpt": (contents[readme[0]][:600] if readme and contents.get(readme[0]) else ""),
        "deps_files": deps_files,
        "detected_libraries": dep_libs,
        "entry_candidates": entries,
        "config_candidates": configs,
        "resource_signals": signals,
        "gpu_demand": {"n_gpu": n_gpu},
        "blockers": blockers,
        "suggested_minimal_overrides": {
            "n_gpu": 1,
            "batch_size": max(1, min(bs, 8)) if bs else 8,
            "epochs": min(epochs, 50) if epochs else 50,
            "deepspeed": False,
            "accelerate": False,
        },
    }

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"[analyze_repo] {owner_repo} @ {branch}")
        print(f"  entry candidates : {entries[:4]}")
        print(f"  detected libs    : {dep_libs or '(none parsed)'}")
        print(f"  resource signals : {signals}")
        print(f"  blockers         : {blockers or '(none obvious)'}")
        print(f"  -> suggested minimal overrides: {report['suggested_minimal_overrides']}")
        print(f"  (full JSON: re-run with --json)")


if __name__ == "__main__":
    main()
