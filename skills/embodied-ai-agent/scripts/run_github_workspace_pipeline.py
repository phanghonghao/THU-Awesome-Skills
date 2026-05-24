#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Locate the current workspace GitHub research pipeline and run it in Feishu-safe mode."
    )
    parser.add_argument("target", help="GitHub repository URL, owner/repo, or keyword")
    parser.add_argument("--workspace", help="Optional workspace root; defaults to current working directory and parents")
    parser.add_argument("--python", default=sys.executable, help="Python executable for the workspace pipeline")
    parser.add_argument("--limit", type=int, default=8, help="Maximum candidate repositories for keyword mode")
    parser.add_argument("--output-root", help="Optional output root passed through to the workspace pipeline")
    return parser.parse_args()


def locate_workspace(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "scripts" / "github_repo_research_pipeline.py").exists():
            return candidate
    raise FileNotFoundError(
        "Could not find scripts/github_repo_research_pipeline.py from the current directory upward."
    )


def main() -> int:
    args = parse_args()
    start = Path(args.workspace).resolve() if args.workspace else Path.cwd().resolve()
    workspace = locate_workspace(start)
    script_path = workspace / "scripts" / "github_repo_research_pipeline.py"
    command = [args.python, str(script_path), args.target, "--for-feishu", "--limit", str(args.limit)]
    if args.output_root:
        command.extend(["--output-root", args.output_root])
    result = subprocess.run(
        command,
        cwd=workspace,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"Workspace pipeline failed (exit={result.returncode}).\n{message}")

    stdout = (result.stdout or "").strip()
    try:
        manifest = json.loads(stdout)
    except json.JSONDecodeError:
        start_idx = stdout.find("{")
        end_idx = stdout.rfind("}")
        if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
            raise
        manifest = json.loads(stdout[start_idx : end_idx + 1])
    manifest["workspace"] = str(workspace)
    manifest["command"] = command
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
