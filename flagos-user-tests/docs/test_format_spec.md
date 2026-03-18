# Test Format Specification

## Core Concept: User-Perspective Test Cases

Every test case is a **self-contained YAML file** that defines the complete workflow from a **user's perspective**:

```yaml
meta:       # What is this test?
resources:  # Hardware requirements (platform, device, device_count)
setup:      # How to install? (user's commands)
run:        # How to run?    (user's commands)
verify:     # How to check?  (gold values comparison)
```

The runner (`run_user_tests.py`) simply executes these user-defined commands. It does NOT call any internal repo scripts — giving users full control and matching real usage scenarios.

## Test Case YAML Format

### Complete Example (FlagScale)

```yaml
meta:
  repo: flagscale
  task: train
  model: mixtral
  case: tp2_pp1_ep2
  description: "Mixtral MoE training with TP=2, PP=1, EP=2"

resources:
  platform: cuda
  device: A100-80GB
  device_count: 8

env:
  CUDA_VISIBLE_DEVICES: "0,1,2,3,4,5,6,7"

setup:
  - pip install flagscale

run:
  - flagscale train mixtral --config ./conf/tp2_pp1_ep2.yaml

verify:
  log_path: "tests/functional_tests/train/mixtral/test_results/tp2_pp1_ep2/logs/details/host_0_localhost/*/default_*/attempt_0/*/stdout.log"
  gold_values_path: ./gold_values/tp2_pp1_ep2.json
  rtol: 1e-5
  atol: 0
```

### Complete Example (Generic)

```yaml
meta:
  repo: flaggems
  case: my_operator_test
  description: "Test custom operator correctness"

setup:
  - pip install flaggems

run:
  - pytest -v tests/test_my_operator.py

# No verify step — pytest exit code determines pass/fail
```

### Field Reference

| Field | Type | Required | Description |
|---|---|---|---|
| `meta.repo` | string | Yes | Target FlagOS repository name |
| `meta.task` | string | No | Task type (train/inference/hetero_train) |
| `meta.model` | string | No | Model name |
| `meta.case` | string | No | Case name (for filtering) |
| `meta.description` | string | Yes | What this test validates |
| `resources` | object | No | Hardware requirements |
| `resources.platform` | string | No | Chip platform: `cuda`, `metax`, `ascend` (default: `cuda`) |
| `resources.device` | string | No | Device type (e.g. `A100-40GB`, `C500`, `Ascend910B`) |
| `resources.device_count` | int | No | Number of devices required |
| `env` | object | No | Environment variables |

### Resource Resolution

The `resources` field drives CI decisions via `resource_map.yaml` (platform-based):

1. **Runner selection**: `resources.platform` + `resources.device` -> platform-specific runner labels
2. **Container image**: `resources.platform` + `meta.repo/task` -> platform-specific Docker image
3. **Container options**: `resources.platform` -> device passthrough flags (`--gpus all`, `--device /dev/davinci_all`, etc.)

Supported platforms:

| Platform | Vendor | Devices | Status |
|---|---|---|---|
| `cuda` | NVIDIA | A100, H100, H800 | Active |
| `metax` | MetaX (Muxi) | C500 | Planned |
| `ascend` | Huawei | Ascend910B, Ascend910C | Planned |

The test job runs inside the platform-resolved Docker container with device access.

### Field Reference (continued)

| Field | Type | Required | Description |
|---|---|---|---|
| `setup` | list[str] | No | Shell commands for environment setup |
| `run` | list[str] | Yes | Shell commands to execute the test |
| `verify.log_path` | string | No | Path to output log (supports glob patterns) |
| `verify.gold_values_path` | string | No | Path to gold values JSON file |
| `verify.gold_values` | object | No | Inline gold values (alternative to file) |
| `verify.rtol` | float | No | Relative tolerance (default: 1e-5) |
| `verify.atol` | float | No | Absolute tolerance (default: 0) |

### Working Directory

All commands execute with the **test case directory** as the working directory. So `./conf/tp2_pp1_ep2.yaml` resolves relative to where the test case YAML lives.

## Gold Values Format

### Numeric (default)

```json
{
  "lm loss:": {
    "values": [11.17587, 11.16908, 10.41927]
  }
}
```

- Keys are metric names extracted from log files
- Values are numeric arrays
- Comparison uses `rtol` / `atol` similar to `numpy.allclose`
- `log_path` supports glob patterns for timestamp directories

### Text

```json
{
  "inference_output": {
    "type": "text",
    "pattern": "output\\.outputs\\[0\\]\\.text=(?:\"(.+?)\"$|'(.+?)'$)",
    "values": [
      " Lina. I'm a 22-year",
      " the same as the president of the United Nations."
    ]
  }
}
```

- Set `"type": "text"` to enable text comparison
- `"pattern"` is a regex with capture group(s) to extract text from log lines
  - If multiple groups (e.g. alternation), the first non-None group is used
- Values are compared with exact string match

## FlagScale Test Case Directory Structure

```
tests/flagscale/train/mixtral/tp2_pp1_ep2/
├── tp2_pp1_ep2.yaml              # Test case definition (setup/run/verify)
├── conf/
│   ├── tp2_pp1_ep2.yaml          # FlagScale experiment config (Hydra)
│   └── train/
│       └── tp2_pp1_ep2.yaml      # Training parameters
├── gold_values/
│   └── tp2_pp1_ep2.json          # Expected metrics
└── README.md
```

The user runs: `pip install flagscale && flagscale train mixtral --config ./conf/tp2_pp1_ep2.yaml`

## README Requirements

Each test case directory must have a `README.md` with:
1. **Description** section
2. **Environment** section

## Experimental Test Cases

Place under `tests/experimental/` for gray-stage tests (nightly only, non-blocking).
