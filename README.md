# FlagOS DevOps Central

This repository is the single source of truth for CI/CD logic across the **FlagOS AI** organization. It contains unified GitHub Actions (individual steps) and Reusable Workflows (entire pipelines) to ensure consistency, security, and speed across all our projects.

## 📁 Repository Structure

```text
flagos-ai/FlagOps/
├── .github/
│   └── workflows/                       # Reusable Workflows & CI tests
│       ├── ci-shared.yml
│       ├── test-post-pytest-report.yml
│       └── test-post-benchmark-report.yml
├── actions/                             # Shared Actions ("Individual Steps")
│   │
│   ├── # ── Checkout ─────────────────────────────────────────────────────
│   ├── checkout-retry/                  # Retry checkout up to 3x (simple flakiness)
│   │   ├── action.yml
│   │   └── README.md
│   ├── checkout-pr/                     # Check out a PR branch by number (issue_comment workflows)
│   │   ├── action.yml
│   │   └── README.md
│   ├── robust-checkout/                 # SSH→HTTP rotation, hard-kill probes (severe flakiness)
│   │   ├── action.yml
│   │   └── README.md
│   │
│   ├── # ── Setup ────────────────────────────────────────────────────────
│   ├── setup-project/                   # Run setup script + optional vllm + GPU check
│   │   ├── action.yml
│   │   └── README.md
│   ├── setup-poetry/                    # Set up Poetry environment
│   │   └── action.yml
│   │
│   ├── # ── Testing ──────────────────────────────────────────────────────
│   ├── run-ondemand-test/               # Run test, upload artifact, post PR comment
│   │   ├── action.yml
│   │   └── README.md
│   │
│   ├── # ── Reporting ────────────────────────────────────────────────────
│   ├── post-pytest-report/              # Upload pytest JSON reports to backend
│   │   ├── action.yml
│   │   └── README.md
│   ├── post-benchmark-report/           # Upload benchmark data with custom table columns
│   │   ├── action.yml
│   │   └── README.md
│   │
│   └── # ── Notifications ────────────────────────────────────────────────
│       └── notify-slack/                # Send Slack notifications
│           └── action.yml
└── README.md
```

---

## 🚀 How to use Shared Workflows

Reusable workflows allow you to standardize entire CI pipelines (e.g., testing, linting, and deploying) with just a few lines of code.

### Usage Example

In your application repository (e.g., `flagos-ai/model-api`), create a file at `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  run-standard-ci:
    uses: flagos-ai/FlagOps/.github/workflows/ci-python.yml@main
    with:
      python-version: "3.11"
    secrets:
      HF_TOKEN: ${{ secrets.HF_TOKEN }}
```

---

## 🛠 How to use Shared Actions

Custom actions are discrete tasks used within your own existing jobs.

### Usage Example

In any workflow file within the organization:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Using a shared action from this repo
      - name: Setup Environment
        uses: flagos-ai/FlagOps/actions/setup-poetry@main
        with:
          install-dev-deps: "true"
```

### Available Actions

#### Checkout

| Action | Description |
|---|---|
| [`checkout-retry`](actions/checkout-retry/) | Wraps `actions/checkout` with up to 3 attempts and 30s sleep between failures. Use for transient network errors. |
| [`checkout-pr`](actions/checkout-pr/) | Installs `gh` CLI and checks out a PR branch by number. Required for `issue_comment`-triggered workflows. |
| [`robust-checkout`](actions/robust-checkout/) | SSH→HTTPS rotation with hard-kill probes and throughput-based transfer judging. Use when fetches can hang. |

#### Setup

| Action | Description |
|---|---|
| [`setup-project`](actions/setup-project/) | Runs a setup script for a given backend, optionally installs vllm with layer-1 integrity protection, exports `AVAILABLE_GPUS`. |
| [`setup-poetry`](actions/setup-poetry/) | Set up Poetry environment |

#### Testing

| Action | Description |
|---|---|
| [`run-ondemand-test`](actions/run-ondemand-test/) | Runs an arbitrary test command, uploads results as an artifact, and posts/updates a PR comment with the report. |

#### Reporting

| Action | Description |
|---|---|
| [`post-pytest-report`](actions/post-pytest-report/) | Upload pytest JSON reports to backend |
| [`post-benchmark-report`](actions/post-benchmark-report/) | Upload benchmark data with custom table columns |

#### Notifications

| Action | Description |
|---|---|
| [`notify-slack`](actions/notify-slack/) | Send Slack notifications |

---

## 🔄 Choosing the right checkout action

```
Network is fine most of the time?
    └─ yes → checkout-retry         (simple, 3 retries, 30s sleep)
    └─ no, fetches can hang/stall
           ├─ have a deploy key?    → robust-checkout with ssh-key
           └─ no key (fork PRs)?   → robust-checkout (HTTPS only)

Triggered by issue_comment and need to land on the PR branch?
    └─ yes → checkout-retry (or robust-checkout) + checkout-pr
```

---

## 📌 Best Practices

### 1. Versioning

For production-critical repositories, avoid using `@main`. Instead, reference a specific version tag or commit SHA to prevent breaking changes:

```yaml
uses: flagos-ai/FlagOps/actions/setup-project@v1.0.0
uses: flagos-ai/FlagOps/actions/robust-checkout@v1.0.0
```

### 2. Contributions

1. Create a new branch for your changes.
2. Add your action or workflow following the folder structure above.
3. Document required `inputs` and `outputs` in a `README.md` alongside `action.yml`.
4. Open a Pull Request for the DevOps team to review.

### 3. Containerized runners

Actions used inside Docker containers (e.g. `container:` jobs) cannot resolve local `./` action refs. Always use fully-qualified refs for these jobs:

```yaml
# ✅ works in container jobs
- uses: flagos-ai/FlagOps/actions/checkout-pr@main

# ❌ fails in container jobs
- uses: ./.github/actions/checkout-pr
```

---

## 📞 Support

For questions regarding CI/CD standards or help with these actions, please contact the Infrastructure team or open an issue in this repository.
