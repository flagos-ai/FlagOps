# FlagOS User Tests

User-perspective test cases for FlagOS repositories. Each test case defines its own setup, run, and verification — exactly as a real user would operate.

## How It Works

```
User submits test case YAML:
  setup: [pip install flagscale]
  run:   [flagscale train mixtral --config ./conf/xxx.yaml]
  verify: {log_path: ..., gold_values_path: ...}

CI runner:
  1. cd <test_case_dir>
  2. Execute setup commands
  3. Execute run commands
  4. Extract metrics from log
  5. Compare against gold values → PASS/FAIL
```

Users have full control — the runner does NOT call internal repo scripts.

## Quick Start

```bash
# Generate template
python tools/generators/create_test_template.py \
    --repo flagscale --type train --model llama2 --name tp2_pp1

# Validate
python tools/validators/validate_config.py
python tools/validators/validate_gold_values.py
python tools/validators/lint_test_case.py --strict

# Run locally
python tools/run_user_tests.py \
    --case tests/flagscale/train/llama2/tp2_pp1/tp2_pp1.yaml
```

See [docs/getting_started.md](docs/getting_started.md) for the full guide.

## Test Case Structure (FlagScale Example)

```
tests/flagscale/train/mixtral/tp2_pp1_ep2/
├── tp2_pp1_ep2.yaml           # Test case: setup → run → verify
├── conf/                      # FlagScale configs (user provides)
│   ├── tp2_pp1_ep2.yaml
│   └── train/tp2_pp1_ep2.yaml
├── gold_values/               # Expected metrics
│   └── tp2_pp1_ep2.json
└── README.md
```

## Supported Repositories

FlagScale, FlagGems, FlagCX, FlagTree, vLLM-FL, vLLM-plugin-FL, TE-FL, Megatron-LM-FL

## CI Workflows (in `../.github/workflows/`)

| Workflow | Trigger | Description |
|---|---|---|
| PR Validation | Pull Request | Format, lint, gold values checks |
| Test Dispatch | Push/PR | Run user-defined setup → run → verify |
| Nightly | Daily 02:00 UTC | All test cases |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
