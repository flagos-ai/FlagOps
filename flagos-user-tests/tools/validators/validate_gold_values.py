#!/usr/bin/env python3

# Copyright 2026 FlagOS Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Validate gold values JSON files for test cases.

Checks:
- Valid JSON syntax
- Expected structure: keys map to objects with "values" arrays
- At least one value is present
- Numeric entries (default): all values are int/float
- Text entries (type: "text"): all values are strings, "pattern" field is present
"""

import argparse
import json
import sys
from pathlib import Path


def validate_gold_values_file(filepath: Path) -> list[str]:
    """Validate a single gold values JSON file."""
    errors = []

    try:
        with open(filepath) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"{filepath}: Invalid JSON - {e}"]

    if not isinstance(data, dict):
        return [f"{filepath}: Gold values must be a JSON object, got {type(data).__name__}"]

    if not data:
        return [f"{filepath}: Gold values file is empty"]

    for key, value in data.items():
        if not isinstance(value, dict):
            errors.append(f"{filepath}: Key '{key}' must map to an object, got {type(value).__name__}")
            continue

        if "values" not in value:
            errors.append(f"{filepath}: Key '{key}' missing 'values' field")
            continue

        values = value["values"]
        if not isinstance(values, list):
            errors.append(f"{filepath}: Key '{key}'.values must be an array")
            continue

        if len(values) == 0:
            errors.append(f"{filepath}: Key '{key}'.values is empty")
            continue

        entry_type = value.get("type", "numeric")

        if entry_type == "text":
            # Text entries require a 'pattern' field for extraction
            if "pattern" not in value:
                errors.append(f"{filepath}: Key '{key}' has type 'text' but missing 'pattern' field")
            for i, v in enumerate(values):
                if not isinstance(v, str):
                    errors.append(
                        f"{filepath}: Key '{key}'.values[{i}] is not a string: {v!r}"
                    )
        elif entry_type == "numeric":
            for i, v in enumerate(values):
                if not isinstance(v, (int, float)):
                    errors.append(
                        f"{filepath}: Key '{key}'.values[{i}] is not numeric: {v!r}"
                    )
        else:
            errors.append(f"{filepath}: Key '{key}' has unknown type: {entry_type!r}")

    return errors


def find_gold_values_files(root: Path) -> list[Path]:
    """Find all gold values JSON files under tests/.

    Supports both conventions:
    - FlagScale: tests/<repo>/<task>/<model>/gold_values/<case>.json
    - Flat: tests/<repo>/<case>/<case>_gold_values.json
    """
    tests_dir = root / "tests"
    if not tests_dir.exists():
        return []
    # Match files inside gold_values/ directories
    gold_dir_files = list(tests_dir.rglob("gold_values/*.json"))
    # Match files with _gold_values in name (legacy flat layout)
    gold_name_files = list(tests_dir.rglob("*_gold_values.json"))
    return list(set(gold_dir_files + gold_name_files))


def main():
    parser = argparse.ArgumentParser(description="Validate gold values JSON files")
    parser.add_argument(
        "--path", default=".",
        help="Root directory of flagos-user-tests"
    )
    args = parser.parse_args()

    root = Path(args.path)
    all_errors = []

    gold_files = find_gold_values_files(root)

    if not gold_files:
        print("No gold values files found. Skipping validation.")
        sys.exit(0)

    for filepath in gold_files:
        all_errors.extend(validate_gold_values_file(filepath))

    if all_errors:
        print(f"Gold values validation FAILED with {len(all_errors)} error(s):")
        for err in all_errors:
            print(f"  ✗ {err}")
        sys.exit(1)
    else:
        print(f"Gold values validation PASSED: {len(gold_files)} file(s) checked.")
        sys.exit(0)


if __name__ == "__main__":
    main()
