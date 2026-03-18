#!/usr/bin/env python3
"""Collect all test cases and output a JSON report for post-benchmark-report action.

Output format:
    [
      {
        "case_id": "tests/flagscale/inference/qwen3/demo_0_6b/demo_0_6b.yaml",
        "case_name": "flagscale-inference-qwen3-demo_0_6b",
        "repo": "flagscale",
        "updated_at": "2026-03-18T15:02:29+08:00"
      },
      ...
    ]

Usage:
    python tools/collect_test_cases.py --root . --output report.json
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


def get_file_updated_time(filepath: Path) -> str:
    """Get the last commit time of a file via git, fallback to mtime."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%aI", str(filepath)],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback to file modification time
    mtime = filepath.stat().st_mtime
    return datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y/%m/%d %H:%M:%S")


def make_case_id(meta: dict) -> str:
    """Generate a case ID from meta fields: <repo>-<task>-<model>-<case>."""
    parts = [
        meta.get("repo", "unknown"),
        meta.get("task", ""),
        meta.get("model", ""),
        meta.get("case", ""),
    ]
    return "-".join(p for p in parts if p)


def collect_test_cases(root: Path) -> list:
    """Discover all test cases and return report list."""
    tests_dir = root / "tests"
    report = []

    for yaml_path in sorted(tests_dir.rglob("*.yaml")):
        if yaml_path.name.startswith("_") or yaml_path.name == "data.yaml":
            continue

        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict) or "meta" not in data:
                continue

            meta = data["meta"]
            report.append({
                "case_id": str(yaml_path.relative_to(root)),
                "case_name": make_case_id(meta),
                "repo": meta.get("repo", "unknown"),
                "updated_at": get_file_updated_time(yaml_path),
            })
        except (yaml.YAMLError, KeyError):
            continue

    return report


def main():
    parser = argparse.ArgumentParser(description="Collect test cases for reporting")
    parser.add_argument("--root", default=".", help="Root directory of flagos-user-tests")
    parser.add_argument("--output", default="test_cases_report.json", help="Output JSON file")
    args = parser.parse_args()

    root = Path(args.root)
    report = collect_test_cases(root)

    with open(args.output, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Collected {len(report)} test case(s) -> {args.output}")
    sys.exit(0)


if __name__ == "__main__":
    main()
