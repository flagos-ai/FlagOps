# Post Benchmark Report Action

A reusable GitHub Action that uploads a benchmark test metric file to a backend HTTP service via multipart form POST.

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `backend_url` | **yes** | — | Full URL of the backend metrics endpoint |
| `results_file` | **yes** | — | Path to the benchmark test metric file |
| `api_token` | no | `""` | Bearer token for authentication |
| `file_format` | no | `json` | File format identifier |
| `file_type` | no | `benchmark` | File type identifier |
| `is_zipped` | no | `false` | Whether the file is zipped |
| `git_project_name` | no | `${{ github.repository }}` | Project name |
| `workflow_name` | no | `${{ github.workflow }}` | Workflow name |
| `job_name` | no | `${{ github.job }}` | Job name |
| `pr_id` | no | auto-detected | PR number (auto-detected from PR events) |
| `fail_on_error` | no | `true` | Whether to fail the step on upload error |

## Outputs

| Output | Description |
|---|---|
| `status` | HTTP status code from the upload request |

## Usage

### Basic (in a benchmark workflow)

```yaml
steps:
  - name: Run benchmark tests
    id: benchmark_test
    run: |
      bash run_tests.sh --task benchmark --model qwen3 --list tp2_pp2

  - name: Upload benchmark data
    if: steps.benchmark_test.outcome == 'success'
    uses: flagos-ai/FlagOps/actions/post-benchmark-report@main
    with:
      backend_url: 'http://10.1.4.167:30180/flagcicd-backend/metrics/'
      results_file: 'tests/functional_tests/benchmark/qwen3/test_results/tp2_pp2/metrics.json'
```

`workflow_name`, `job_name`, `pr_id`, and `git_project_name` are auto-detected from the GitHub context.

### With authentication and custom settings

```yaml
  - uses: flagos-ai/FlagOps/actions/post-benchmark-report@main
    with:
      backend_url: 'http://10.1.4.167:30180/flagcicd-backend/metrics/'
      results_file: 'benchmark_results.tar.gz'
      is_zipped: 'true'
      api_token: ${{ secrets.BACKEND_TOKEN }}
      job_name: 'benchmark_qwen3_tp2_pp2'
      fail_on_error: 'false'
```

### Non-PR context (push to main)

When running outside a PR context, `pr_id` is simply omitted from the request unless you explicitly set it:

```yaml
  - uses: flagos-ai/FlagOps/actions/post-benchmark-report@main
    with:
      backend_url: 'http://10.1.4.167:30180/flagcicd-backend/metrics/'
      results_file: 'metrics.json'
      pr_id: '0'  # optional explicit override
```

## Behavior

- **Auto-packaging**: If `is_zipped` is `false` (default), the file is automatically compressed into a `tar.gz` archive before uploading. If `is_zipped` is `true`, the file is uploaded as-is.
- **Auto-detection**: `git_project_name`, `workflow_name`, `job_name`, and `pr_id` are auto-populated from GitHub context variables. Any of them can be overridden by setting the input explicitly.
- **Optional pr_id**: If no PR context is available and `pr_id` is not set, the field is omitted from the request entirely.
- **Error handling**: Controlled by `fail_on_error`. When `true` (default), a failed upload or missing results file fails the workflow step. When `false`, a warning is logged and the step succeeds.
