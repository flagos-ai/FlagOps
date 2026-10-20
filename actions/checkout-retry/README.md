# checkout-retry

A reusable GitHub Action that wraps `actions/checkout` with up to 3 attempts, sleeping 30 seconds between failures. Useful for runners on flaky networks where a single checkout attempt occasionally fails.

> For more severe network instability (hung fetches, SSH/HTTPS rotation), use [`robust-checkout`](../robust-checkout/) instead.

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `ref` | no | `${{ github.ref }}` | Git ref to checkout |
| `submodules` | no | `false` | Whether to checkout submodules |
| `fetch-depth` | no | `1` | Fetch depth for checkout |

## Usage

```yaml
steps:
  - uses: actions/checkout@v4
    continue-on-error: true

  - uses: flagos-ai/FlagOps/actions/checkout-retry@main

  # From a containerized runner (must use fully-qualified ref):
  - uses: flagos-ai/FlagOps/actions/checkout-retry@main
    with:
      ref: ${{ github.event.pull_request.head.sha }}
```

## Behavior

- Attempts `actions/checkout` up to 3 times.
- Sleeps 30 seconds between attempts.
- Fails the step only if all 3 attempts fail.
- The first `actions/checkout` before this action (with `continue-on-error: true`) is a common pattern that pre-warms git config; the retry handles the case where that initial checkout failed.
