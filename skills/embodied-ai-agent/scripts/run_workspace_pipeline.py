#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Locate the current workspace Embodied-Ai-agent pipeline and run it in Feishu-safe mode."
    )
    parser.add_argument("video_url", help="Bilibili video URL")
    parser.add_argument(
        "--workspace",
        help="Optional workspace root; defaults to current working directory and its parents",
    )
    parser.add_argument("--python", default=sys.executable, help="Python executable for the workspace pipeline")
    return parser.parse_args()


def locate_workspace(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "scripts" / "bilibili_embodied_ai_pipeline.py").exists():
            return candidate
    raise FileNotFoundError(
        "Could not find scripts/bilibili_embodied_ai_pipeline.py from the current directory upward."
    )


def main() -> int:
    args = parse_args()
    start = Path(args.workspace).resolve() if args.workspace else Path.cwd().resolve()
    workspace = locate_workspace(start)
    script_path = workspace / "scripts" / "bilibili_embodied_ai_pipeline.py"
    command = [args.python, str(script_path), args.video_url, "--for-feishu"]
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
        # Surface stderr first; it usually contains the real failure reason.
        message = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"Workspace pipeline failed (exit={result.returncode}).\n{message}")

    stdout = (result.stdout or "").strip()
    try:
        manifest = json.loads(stdout)
    except json.JSONDecodeError:
        # Some environments print warnings to stdout; salvage the JSON block.
        start = stdout.find("{")
        end = stdout.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        manifest = json.loads(stdout[start : end + 1])
    manifest["workspace"] = str(workspace)
    manifest["command"] = command
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
