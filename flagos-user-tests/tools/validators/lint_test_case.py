#!/usr/bin/env python3
"""Lint test case directories for completeness and correctness.

Checks:
- Each test case directory has a README.md
- Each test case has at least one YAML config
- README contains required sections (Description, Environment, etc.)
- No sensitive data patterns (tokens, passwords, private paths)
"""

import argparse
import re
import sys
from pathlib import Path

import yaml


VALID_REPOS = [
    "flagscale", "flaggems", "flagcx", "flagtree",
    "vllm-fl", "vllm-plugin-fl", "te-fl", "megatron-lm-fl",
]

# Patterns that might indicate sensitive data in configs
SENSITIVE_PATTERNS = [
    re.compile(r"(password|passwd|secret|token|api_key)\s*[:=]", re.IGNORECASE),
    re.compile(r"/home/[a-zA-Z0-9_]+/", re.IGNORECASE),  # Private user paths
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),  # API keys
]

README_REQUIRED_SECTIONS = ["description", "environment"]


def find_test_case_dirs(root: Path) -> list[Path]:
    """Find directories that contain a user-perspective test case YAML (has 'meta' key)."""
    tests_dir = root / "tests"
    if not tests_dir.exists():
        return []

    test_dirs = set()
    for yaml_file in tests_dir.rglob("*.yaml"):
        try:
            data = yaml.safe_load(yaml_file.read_text())
            if isinstance(data, dict) and "meta" in data:
                test_dirs.add(yaml_file.parent)
        except (yaml.YAMLError, OSError):
            continue

    return sorted(test_dirs)


def lint_readme(readme_path: Path, strict: bool = False) -> list[str]:
    """Check README.md for required content."""
    errors = []
    if not readme_path.exists():
        return [f"{readme_path.parent}: Missing README.md"]

    content = readme_path.read_text().lower()

    if strict:
        for section in README_REQUIRED_SECTIONS:
            if section not in content:
                errors.append(
                    f"{readme_path}: Missing required section '{section}'"
                )

    if len(content.strip()) < 20:
        errors.append(f"{readme_path}: README is too short (less than 20 characters)")

    return errors


def lint_sensitive_data(filepath: Path) -> list[str]:
    """Check for sensitive data patterns in config files."""
    errors = []
    content = filepath.read_text()
    for pattern in SENSITIVE_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            errors.append(
                f"{filepath}: Possible sensitive data detected: {matches[:3]}"
            )
    return errors


def lint_yaml_configs(test_dir: Path) -> list[str]:
    """Lint YAML config files in a test directory."""
    errors = []
    yaml_files = list(test_dir.glob("*.yaml"))
    if not yaml_files:
        return []

    for yf in yaml_files:
        try:
            with open(yf) as f:
                data = yaml.safe_load(f)
            if data is None:
                errors.append(f"{yf}: Empty YAML file")
        except yaml.YAMLError as e:
            errors.append(f"{yf}: Invalid YAML - {e}")
            continue

        # Check for sensitive data
        errors.extend(lint_sensitive_data(yf))

    return errors


def main():
    parser = argparse.ArgumentParser(description="Lint test case directories")
    parser.add_argument(
        "--path", default=".",
        help="Root directory of flagos-user-tests"
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Enable strict checks (README sections, etc.)"
    )
    args = parser.parse_args()

    root = Path(args.path)
    all_errors = []
    warnings = []

    test_dirs = find_test_case_dirs(root)
    if not test_dirs:
        print("No test case directories found.")
        sys.exit(0)

    for test_dir in test_dirs:
        # Check README
        readme_errors = lint_readme(test_dir / "README.md", strict=args.strict)
        if args.strict:
            all_errors.extend(readme_errors)
        else:
            warnings.extend(readme_errors)

        # Lint YAML configs
        all_errors.extend(lint_yaml_configs(test_dir))

    if warnings:
        print(f"Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"  ⚠ {w}")

    if all_errors:
        print(f"Lint FAILED with {len(all_errors)} error(s):")
        for err in all_errors:
            print(f"  ✗ {err}")
        sys.exit(1)
    else:
        print(f"Lint PASSED: {len(test_dirs)} test directory(ies) checked.")
        sys.exit(0)


if __name__ == "__main__":
    main()
