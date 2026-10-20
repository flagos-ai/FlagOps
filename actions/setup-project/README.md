# setup-project

A reusable GitHub Action that runs a project setup script for a given backend, optionally installs vllm with layer-1 package integrity protection, and exports available GPU IDs to `AVAILABLE_GPUS`.

Generalized from FlagGems' `setup-flaggems` action for org-wide reuse across any project that follows a similar `setup.sh <backend>` pattern.

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `backend` | **yes** | — | Backend label passed to the setup script (e.g. `nvidia-cuda133`, `ascend-cann900`) |
| `setup-script` | no | `./setup.sh` | Path to the setup script |
| `vllm-version` | no | `""` | vllm version to install (e.g. `0.21.0`). Empty = skip |
| `vllm-backend-prefix` | no | `nvidia` | Only install vllm when `backend` starts with this prefix. Empty = always install |
| `vllm-safe-deps-script` | no | `tools/vllm_safe_deps.py` | Script that prints safe vllm transitive deps. Empty = skip safe-deps filtering |
| `layer1-packages-pattern` | no | `^(torch\|triton\|flag)` | Regex to identify layer-1 packages; used to detect unintended downgrades |
| `gpu-check-script` | no | `""` | Path to GPU availability check script. Parses `Available GPUs: <ids>` and sets `AVAILABLE_GPUS` |

## Usage

### Basic

```yaml
steps:
  - uses: flagos-ai/FlagOps/actions/setup-project@main
    with:
      backend: nvidia-cuda133
```

### With vllm install

```yaml
steps:
  - uses: flagos-ai/FlagOps/actions/setup-project@main
    with:
      backend: nvidia-cuda133
      vllm-version: '0.21.0'
      gpu-check-script: tools/gpu_check.sh
```

### Non-nvidia backend with vllm (override prefix)

```yaml
  - uses: flagos-ai/FlagOps/actions/setup-project@main
    with:
      backend: custom-backend
      vllm-version: '0.21.0'
      vllm-backend-prefix: ''    # install vllm for any backend
```

### Custom setup script and layer-1 pattern

```yaml
  - uses: flagos-ai/FlagOps/actions/setup-project@main
    with:
      backend: ascend-cann900
      setup-script: ./scripts/bootstrap.sh
      layer1-packages-pattern: "^(torch|torchvision)"
```

## Behavior

- **Setup script**: always runs `<setup-script> <backend>`.
- **vllm install**: skipped when `vllm-version` is empty, or when `backend` does not start with `vllm-backend-prefix` (and `vllm-backend-prefix` is non-empty).
- **Layer-1 integrity check**: takes a snapshot of layer-1 packages before vllm install; fails the step if any package is modified after install.
- **Safe deps filtering**: if `vllm-safe-deps-script` is set and exists, runs it to generate a filtered dependency list and installs only those packages (both with `--no-deps`).
- **GPU check**: if `gpu-check-script` is set, runs the script and parses its `Available GPUs:` output line to set `AVAILABLE_GPUS` in `$GITHUB_ENV`.

## Migrating from FlagGems `setup-flaggems`

```yaml
# Before (FlagGems-specific)
- uses: ./.github/actions/setup-flaggems
  with:
    backend: ${{ matrix.backend }}
    gpu_check_script: tools/gpu_check.sh

# After (org-wide)
- uses: flagos-ai/FlagOps/actions/setup-project@main
  with:
    backend: ${{ matrix.backend }}
    vllm-version: '0.21.0'        # was hardcoded in the action
    gpu-check-script: tools/gpu_check.sh   # note: kebab-case
```
