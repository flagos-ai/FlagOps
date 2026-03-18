# Getting Started

## Overview

`flagos-user-tests` manages **user-perspective** test cases for FlagOS repositories. Each test case defines its own setup, run, and verification commands — exactly as a real user would operate.

## Quick Start

### 1. Generate a template

```bash
# FlagScale training test
python tools/generators/create_test_template.py \
    --repo flagscale --type train --model llama2 --name tp2_pp1

# Generic test
python tools/generators/create_test_template.py \
    --repo flaggems --name my_operator_test
```

### 2. Edit the generated files

The test case YAML defines the user workflow:

```yaml
# tests/flagscale/train/llama2/tp2_pp1/tp2_pp1.yaml
meta:
  repo: flagscale
  task: train
  model: llama2
  case: tp2_pp1
  description: "LLaMA2 training with TP=2, PP=1"

resources:
  gpu: A100-80GB
  gpu_count: 8

setup:
  - pip install flagscale                    # user installs the package

run:
  - flagscale train llama2 --config ./conf/tp2_pp1.yaml   # user runs training

verify:
  log_path: ".../stdout.log"                 # where to find output
  gold_values_path: ./gold_values/tp2_pp1.json   # expected metrics
```

Also edit the FlagScale config files (`conf/*.yaml`) and fill in gold values from a verified run.

### 3. Validate locally

```bash
python tools/validators/validate_config.py
python tools/validators/validate_gold_values.py
python tools/validators/lint_test_case.py --strict
```

### 4. Run locally (optional)

```bash
python tools/run_user_tests.py \
    --case tests/flagscale/train/llama2/tp2_pp1/tp2_pp1.yaml
```

### 5. Submit a PR

CI will automatically:
1. Validate format (PR Validation workflow)
2. Run your test case on real hardware (Test Dispatch workflow)

## How the Runner Works

`run_user_tests.py` is a **generic executor**:

```
┌─────────────┐     ┌──────────────────────────────────────┐
│  Test Case   │ ──▶ │ 1. cd <test_case_dir>                │
│  YAML        │     │ 2. Execute setup commands             │
│              │     │ 3. Execute run commands                │
│              │     │ 4. Find log file (glob pattern)        │
│              │     │ 5. Extract metrics from log            │
│              │     │ 6. Compare against gold values          │
└─────────────┘     └──────────────────────────────────────┘
```

It does **not** call any internal repo scripts. Users have full control over:
- What to install (`setup`)
- How to run (`run`)
- What to verify (`verify`)
- Machine requirements (`resources`) — mapped to runner labels via `resource_map.yaml`

## CI Workflows

| Workflow | Trigger | Description |
|---|---|---|
| PR Validation | Pull Request | Format/lint/gold-values checks |
| Test Dispatch | Push to main / PR | Runs user-defined setup → run → verify |
| Nightly | Daily 02:00 UTC | All test cases across all repos |
