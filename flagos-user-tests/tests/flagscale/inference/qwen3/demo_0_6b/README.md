# demo_0_6b

## Description

FlagScale inference demo using Qwen3-0.6B model with vLLM backend.
Runs 4 prompts with greedy decoding (temperature=0, max_tokens=10) and verifies output text against gold values.

## Environment

- GPU: 1x A100 40GB
- CUDA: 12.1+
- Python: 3.12
- vLLM: 0.10.1.dev

## How to Run

```bash
git clone https://github.com/flagos-ai/FlagScale.git && cd FlagScale && pip install .
flagscale inference qwen3 --config ./conf/demo_0_6b.yaml
```

## Gold Values

Uses text-type gold values to verify inference output.
Greedy decoding (temperature=0) produces deterministic output, so text comparison is exact match.
