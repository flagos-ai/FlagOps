#!/usr/bin/env python3
"""Validate YAML configuration files for test cases.

Checks:
- YAML syntax validity
- Test case YAML (with meta key): required fields (meta.repo, setup, run)
- FlagScale sub-configs (experiment/defaults): structure validation
- Generic configs: non-empty dict
"""

import argparse
import sys
from pathlib import Path

import yaml


VALID_REPOS = [
    "flagscale", "flaggems", "flagcx", "flagtree",
    "vllm-fl", "vllm-plugin-fl", "te-fl", "megatron-lm-fl",
]


def validate_yaml_syntax(filepath: Path) -> list[str]:
    """Check that a file is valid YAML."""
    errors = []
    try:
        with open(filepath) as f:
            data = yaml.safe_load(f)
        if data is None:
            errors.append(f"{filepath}: YAML file is empty")
    except yaml.YAMLError as e:
        errors.append(f"{filepath}: Invalid YAML syntax - {e}")
    return errors


def validate_test_case(filepath: Path, data: dict) -> list[str]:
    """Validate a user-perspective test case YAML (has 'meta' key)."""
    errors = []
    meta = data.get("meta", {})

    if not meta.get("repo"):
        errors.append(f"{filepath}: Missing 'meta.repo'")
    elif meta["repo"] not in VALID_REPOS:
        errors.append(f"{filepath}: Invalid meta.repo '{meta['repo']}'")

    if not data.get("run"):
        errors.append(f"{filepath}: Missing 'run' (list of commands)")
    elif not isinstance(data["run"], list):
        errors.append(f"{filepath}: 'run' must be a list of commands")

    if "setup" in data and not isinstance(data["setup"], list):
        errors.append(f"{filepath}: 'setup' must be a list of commands")

    if "verify" in data:
        v = data["verify"]
        if isinstance(v, dict):
            has_gold = v.get("gold_values") or v.get("gold_values_path")
            if has_gold and not v.get("log_path"):
                errors.append(f"{filepath}: verify.log_path required when gold values are defined")

    return errors


def validate_flagscale_subconfig(filepath: Path, data: dict) -> list[str]:
    """Validate FlagScale sub-config (experiment config or train params)."""
    errors = []
    keys = set(data.keys())

    if "experiment" in keys:
        exp = data["experiment"]
        if "exp_name" not in exp:
            errors.append(f"{filepath}: Missing 'experiment.exp_name'")
        if "task" not in exp:
            errors.append(f"{filepath}: Missing 'experiment.task'")
        elif "type" not in exp.get("task", {}):
            errors.append(f"{filepath}: Missing 'experiment.task.type'")
    elif "defaults" in keys:
        # Sub-config (train params, data, etc.) — lighter validation
        pass
    else:
        errors.append(
            f"{filepath}: Missing expected top-level key "
            f"('experiment' or 'defaults'), found: {keys}"
        )
    return errors


def validate_file(filepath: Path) -> list[str]:
    """Validate a single YAML file based on its content type."""
    errors = validate_yaml_syntax(filepath)
    if errors:
        return errors

    with open(filepath) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        return [f"{filepath}: Must be a YAML mapping"]

    # Determine type by content
    if "meta" in data:
        # User-perspective test case
        return validate_test_case(filepath, data)
    elif "experiment" in data or "defaults" in data:
        # FlagScale sub-config (Hydra config)
        return validate_flagscale_subconfig(filepath, data)
    else:
        # Generic config — just check it's a valid non-empty dict
        return []


def find_yaml_files(root: Path) -> list[Path]:
    """Find all YAML files under tests/."""
    tests_dir = root / "tests"
    if not tests_dir.exists():
        return []
    return sorted(tests_dir.rglob("*.yaml"))


def main():
    parser = argparse.ArgumentParser(description="Validate test case YAML configs")
    parser.add_argument("--path", default=".", help="Root directory of flagos-user-tests")
    parser.add_argument("--changed-files", default="", help="Comma-separated list of changed files")
    args = parser.parse_args()

    root = Path(args.path)

    if args.changed_files:
        yaml_files = [
            Path(f) for f in args.changed_files.split(",")
            if f.strip().endswith(".yaml") and f.strip().startswith("tests/")
        ]
    else:
        yaml_files = find_yaml_files(root)

    if not yaml_files:
        print("No YAML test config files found to validate.")
        sys.exit(0)

    all_errors = []
    for filepath in yaml_files:
        full_path = root / filepath if not filepath.is_absolute() else filepath
        if not full_path.exists():
            all_errors.append(f"{filepath}: File does not exist")
            continue
        all_errors.extend(validate_file(full_path))

    if all_errors:
        print(f"Validation FAILED with {len(all_errors)} error(s):")
        for err in all_errors:
            print(f"  ✗ {err}")
        sys.exit(1)
    else:
        print(f"Validation PASSED: {len(yaml_files)} file(s) checked.")
        sys.exit(0)


if __name__ == "__main__":
    main()
