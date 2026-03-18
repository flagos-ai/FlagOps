#!/usr/bin/env python3
"""Generate user-perspective test case template.

Usage:
    # FlagScale training test
    python create_test_template.py --repo flagscale --type train --model llama2 --name tp2_pp1

    # Generic test
    python create_test_template.py --repo flaggems --name my_operator_test
"""

import argparse
import json
import os
import sys
from pathlib import Path

import yaml


VALID_REPOS = [
    "flagscale", "flaggems", "flagcx", "flagtree",
    "vllm-fl", "vllm-plugin-fl", "te-fl", "megatron-lm-fl",
]


def create_flagscale_test_case(task_type: str, model: str, name: str) -> dict:
    """Generate a FlagScale user-perspective test case YAML."""
    return {
        "meta": {
            "repo": "flagscale",
            "task": task_type,
            "model": model,
            "case": name,
            "description": "TODO: describe what this test validates",
        },
        "resources": {
            "gpu": "A100-80GB",
            "gpu_count": 8,
        },
        "env": {
            "CUDA_VISIBLE_DEVICES": "0,1,2,3,4,5,6,7",
            "CUDA_DEVICE_MAX_CONNECTIONS": "1",
        },
        "setup": [
            "pip install flagscale",
        ],
        "run": [
            f"flagscale {task_type} {model} --config ./conf/{name}.yaml",
        ],
        "verify": {
            "log_path": f"tests/functional_tests/{task_type}/{model}/test_results/{name}/logs/details/host_0_localhost/*/default_*/attempt_0/*/stdout.log",
            "gold_values_path": f"./gold_values/{name}.json",
            "rtol": 1e-5,
            "atol": 0,
        },
    }


def create_flagscale_experiment_config(model: str, name: str, task_type: str) -> dict:
    """Generate Hydra experiment config for flagscale CLI."""
    return {
        "defaults": ["_self_", {task_type: name}],
        "experiment": {
            "exp_name": name,
            "exp_dir": f"tests/functional_tests/{task_type}/{model}/test_results/{name}",
            "task": {
                "type": task_type,
                "backend": "megatron",
                "entrypoint": "flagscale/train/megatron/train_gpt.py",
            },
            "runner": {"ssh_port": None},
            "envs": {
                "CUDA_VISIBLE_DEVICES": "0,1,2,3,4,5,6,7",
                "CUDA_DEVICE_MAX_CONNECTIONS": "1",
            },
        },
        "action": "run",
        "hydra": {"run": {"dir": "${experiment.exp_dir}/hydra"}},
    }


def create_flagscale_train_params() -> dict:
    """Generate training params sub-config."""
    return {
        "defaults": ["data"],
        "system": {
            "tensor_model_parallel_size": 2,
            "pipeline_model_parallel_size": 1,
            "sequence_parallel": True,
            "use_distributed_optimizer": True,
            "precision": {"bf16": True},
            "logging": {"log_interval": 1},
            "checkpoint": {"no_save_optim": True, "no_save_rng": True, "save_interval": 100000},
        },
        "model": {
            "num_layers": 2,
            "hidden_size": 4096,
            "num_attention_heads": 32,
            "seq_length": 2048,
        },
    }


def create_generic_test_case(repo: str, name: str) -> dict:
    """Generate a generic user-perspective test case YAML."""
    return {
        "meta": {
            "repo": repo,
            "case": name,
            "description": "TODO: describe what this test validates",
        },
        "resources": {},
        "setup": [
            f"pip install {repo.replace('-', '_')}",
        ],
        "run": [
            "pytest -v",
        ],
    }


def create_readme(repo: str, task_type: str, model: str, name: str) -> str:
    if repo == "flagscale":
        return f"""# {name}

## Description

TODO: Describe what this test case validates.

## Environment

- GPU: 8x A100 80GB
- CUDA: 12.1+
- Python: 3.10

## How to Run

```bash
pip install flagscale
flagscale {task_type} {model} --config ./conf/{name}.yaml
```

## Gold Values

TODO: Describe expected values and tolerance.
"""
    return f"""# {name}

## Description

TODO: Describe what this test case validates.

## Environment

- Python: 3.10

## How to Run

```bash
pip install {repo}
pytest -v
```
"""


def dump_yaml(data: dict, path: Path):
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def main():
    parser = argparse.ArgumentParser(description="Generate test case template")
    parser.add_argument("--repo", required=True, choices=VALID_REPOS)
    parser.add_argument("--type", default="train")
    parser.add_argument("--model", default="")
    parser.add_argument("--name", required=True)
    parser.add_argument("--output", default=".")
    args = parser.parse_args()

    root = Path(args.output)

    if args.repo == "flagscale":
        if not args.model:
            print("FlagScale test cases require --model"); sys.exit(1)

        case_dir = root / "tests" / args.repo / args.type / args.model / args.name

        # Main test case YAML (user-perspective)
        tc = create_flagscale_test_case(args.type, args.model, args.name)
        dump_yaml(tc, case_dir / f"{args.name}.yaml")

        # Hydra experiment config
        ec = create_flagscale_experiment_config(args.model, args.name, args.type)
        dump_yaml(ec, case_dir / "conf" / f"{args.name}.yaml")

        # Training params sub-config
        tp = create_flagscale_train_params()
        dump_yaml(tp, case_dir / "conf" / "train" / f"{args.name}.yaml")

        # Gold values
        gold = {"lm loss:": {"values": [0.0] * 10}}
        gold_path = case_dir / "gold_values" / f"{args.name}.json"
        os.makedirs(gold_path.parent, exist_ok=True)
        with open(gold_path, "w") as f:
            json.dump(gold, f, indent=2)

        # README
        readme = create_readme(args.repo, args.type, args.model, args.name)
        with open(case_dir / "README.md", "w") as f:
            f.write(readme)

        print(f"Created FlagScale test case at: {case_dir}")
        print(f"  {args.name}.yaml          — test case (setup/run/verify)")
        print(f"  conf/{args.name}.yaml     — FlagScale experiment config")
        print(f"  conf/train/{args.name}.yaml — training parameters")
        print(f"  gold_values/{args.name}.json — expected metrics")
        print(f"  README.md")
    else:
        case_dir = root / "tests" / args.repo / args.name
        tc = create_generic_test_case(args.repo, args.name)
        dump_yaml(tc, case_dir / f"{args.name}.yaml")

        readme = create_readme(args.repo, "", "", args.name)
        with open(case_dir / "README.md", "w") as f:
            f.write(readme)

        print(f"Created test case at: {case_dir}")


if __name__ == "__main__":
    main()
