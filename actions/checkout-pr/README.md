# checkout-pr

A reusable GitHub Action that installs the `gh` CLI (if not already present) and checks out a PR branch by number. Needed for `issue_comment`-triggered workflows where the default checkout does not land on the PR branch.

Contains only bash steps — no local `./` action references — so it works from containerized runners via a fully-qualified `@main` ref.

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `pull` | **yes** | — | PR number to check out |
| `github-token` | **yes** | — | Token used by `gh` to check out the PR |
| `gh-version` | no | `2.95.0` | `gh` CLI version to install if not already available |
| `gh-mirror-url` | no | `https://resource.flagos.net/...` | Base URL of the `gh` release mirror |

## Usage

```yaml
# In an issue_comment-triggered workflow:
steps:
  - uses: actions/checkout@v4
    continue-on-error: true

  - uses: flagos-ai/FlagOps/actions/checkout-retry@main

  - uses: flagos-ai/FlagOps/actions/checkout-pr@main
    with:
      pull: ${{ github.event.issue.number }}
      github-token: ${{ secrets.GITHUB_TOKEN }}
```

### Overriding the gh download mirror

By default, `gh` is downloaded from the internal FlagOS CDN. To use GitHub's official releases or your own mirror:

```yaml
  - uses: flagos-ai/FlagOps/actions/checkout-pr@main
    with:
      pull: ${{ github.event.issue.number }}
      github-token: ${{ secrets.GITHUB_TOKEN }}
      gh-mirror-url: "https://github.com/cli/cli/releases/download/v2.95.0"
```

> **Note:** The mirror URL must serve archives in the format
> `gh_<version>_linux_<arch>.tar.gz` with the binary at
> `gh_<version>_linux_<arch>/bin/gh` inside the archive — matching the
> standard GitHub CLI release layout.

## Behavior

- Detects CPU architecture (`x86_64` → `amd64`, `aarch64`/`arm64` → `arm64`).
- Checks if `gh` is already installed and functional before downloading.
- Caches the downloaded binary in `$HOME/.local/bin` and adds it to `$GITHUB_PATH`.
- Fails immediately if the architecture is unsupported.
