# robust-checkout

A reusable GitHub Action that provides a network-resilient git checkout by rotating between SSH and HTTPS links, using hard-kill probes to detect hung fetches, and judging transfer health on throughput rather than elapsed time.

Designed for runners where `git fetch` can **hang** (not just fail) — a problem that git's own timeouts cannot solve because no bytes flow during a connect-stage stall.

> For simple retry without SSH/HTTPS rotation, use [`checkout-retry`](../checkout-retry/) instead.

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `fetch-depth` | no | `1` | git fetch depth (use `0` for full history) |
| `ssh-key` | no | `""` | SSH private key (deploy key); leave empty to disable SSH (e.g. fork PRs) |
| `ref` | no | PR head SHA or `github.sha` | Ref/SHA to fetch and checkout |
| `base-ref` | no | `""` | Extra ref to fetch (e.g. PR base SHA for `base...head` diffs) |
| `connect-seconds` | no | `10` | Hard kill timeout for the connect probe (`git ls-remote`) |
| `probe-seconds` | no | `20` | Low-speed window: aborts if transfer stays below ~20 KiB/s for this long |
| `transfer-seconds` | no | `180` | Catch-all hard kill for the full fetch (last resort) |
| `rounds` | no | `3` | Number of SSH→HTTP rotation cycles before failing |

## Usage

### Basic (HTTPS only, no SSH key)

```yaml
steps:
  - uses: flagos-ai/FlagOps/actions/robust-checkout@main
```

### With SSH deploy key (faster, more reliable on flaky networks)

```yaml
steps:
  - uses: flagos-ai/FlagOps/actions/robust-checkout@main
    with:
      ssh-key: ${{ secrets.DEPLOY_KEY }}
      fetch-depth: 0       # full history for git diffs
      base-ref: ${{ github.event.pull_request.base.sha }}
```

### Fork PRs (SSH unavailable)

For PRs from forks, deploy keys don't have access. Pass an empty `ssh-key` to skip SSH and use HTTPS only:

```yaml
steps:
  - uses: flagos-ai/FlagOps/actions/robust-checkout@main
    with:
      ssh-key: ""          # explicitly empty — fork PRs have no deploy key access
      ref: ${{ github.event.pull_request.head.sha }}
```

## How it works

1. **Connect probe**: runs `git ls-remote` under a short `SIGKILL` window. A link that can't advertise refs in `connect-seconds` is considered wedged and rotated.
2. **Throughput-based transfer**: the real fetch is killed only if it stays below ~20 KiB/s for `probe-seconds` — a slow-but-moving runner isn't cut off by the clock.
3. **SSH → HTTP rotation**: tries SSH first (if a key is provided), then HTTP. Repeats for `rounds` cycles.
4. **Credential scrub**: SSH key file is removed and the remote URL is reset to a public HTTPS URL regardless of outcome.
5. **Clean workspace**: wipes `.git` each run to prevent stale index state from reused runner workspaces from hiding tracked files.
