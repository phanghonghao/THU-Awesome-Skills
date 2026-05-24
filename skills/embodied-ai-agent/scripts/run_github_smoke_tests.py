#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run smoke tests for the GitHub research pipeline.")
    parser.add_argument(
        "--output-root",
        default="outputs/smoke-tests/github",
        help="Directory that will contain generated smoke-test outputs",
    )
    parser.add_argument(
        "--keywords",
        nargs="*",
        default=["World Model", "World Action Model"],
        help="Keywords to test",
    )
    return parser.parse_args()


def run_case(python_exe: str, script_path: Path, output_root: Path, keyword: str) -> dict:
    command = [
        python_exe,
        str(script_path),
        keyword,
        "--output-root",
        str(output_root),
        "--for-feishu",
        "--limit",
        "8",
    ]
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(f"Smoke test failed for {keyword}:\n{result.stderr or result.stdout}")
    return json.loads(result.stdout)


def main() -> int:
    args = parse_args()
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    script_path = Path(__file__).resolve().with_name("github_repo_research_pipeline.py")

    results = []
    for keyword in args.keywords:
        results.append(run_case(sys.executable, script_path, output_root, keyword))

    summary = {
        "output_root": str(output_root),
        "cases": results,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
