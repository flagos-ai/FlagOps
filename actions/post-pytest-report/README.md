# Post Pytest Report Action

A reusable GitHub Action that uploads a pytest JSON report to a backend HTTP service via multipart form POST.

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `backend_url` | **yes** | — | Full URL of the backend metrics endpoint |
| `report_path` | **yes** | — | Path to the pytest JSON report file |
| `user_id` | **yes** | — | User ID sent as `x-user-id` header (use a GitHub secret) |
| `api_token` | no | `""` | Bearer token for authentication |
| `file_format` | no | `json` | File format identifier |
| `file_type` | no | `pytest` | File type identifier |
| `is_zipped` | no | `false` | Whether the file is zipped |
| `git_project_name` | no | `${{ github.repository }}` | Project name |
| `workflow_name` | no | `${{ github.workflow }}` | Workflow name |
| `job_name` | no | `${{ github.job }}` | Job name |
| `run_id` | no | `${{ github.run_id }}` | GitHub Actions run ID |
| `pr_id` | no | auto-detected | PR number (auto-detected from PR events) |
| `fail_on_error` | no | `true` | Whether to fail the step on upload error |

## Outputs

| Output | Description |
|---|---|
| `status` | HTTP status code from the upload request |

## Usage

### Basic (on a PR workflow)

```yaml
steps:
  - uses: actions/checkout@v4

  - name: Run tests
    run: pytest --json-report --json-report-file=report.json

  - uses: flagos-ai/FlagOps/actions/post-pytest-report@v1
    with:
      backend_url: 'http://10.1.4.167:30180/flagcicd-backend/metrics/'
      report_path: 'report.json'
      user_id: ${{ secrets.FLAGOPS_USER_ID }}
```

`workflow_name`, `job_name`, `pr_id`, `run_id`, and `git_project_name` are auto-detected from the GitHub context.

### With authentication and custom settings

```yaml
  - uses: flagos-ai/FlagOps/actions/post-pytest-report@v1
    with:
      backend_url: 'http://10.1.4.167:30180/flagcicd-backend/metrics/'
      report_path: 'report.json'
      user_id: ${{ secrets.FLAGOPS_USER_ID }}
      api_token: ${{ secrets.BACKEND_TOKEN }}
      git_project_name: 'baai.ac/FlagCICD'
      fail_on_error: 'false'
```

### Non-PR context (push to main)

When running outside a PR context, `pr_id` is simply omitted from the request unless you explicitly set it:

```yaml
  - uses: flagos-ai/FlagOps/actions/post-pytest-report@v1
    with:
      backend_url: 'http://10.1.4.167:30180/flagcicd-backend/metrics/'
      report_path: 'report.json'
      user_id: ${{ secrets.FLAGOPS_USER_ID }}
      pr_id: '0'  # optional explicit override
```

## Behavior

- **Auto-detection**: `git_project_name`, `workflow_name`, `job_name`, `run_id`, and `pr_id` are auto-populated from GitHub context variables. Any of them can be overridden by setting the input explicitly.
- **User identification**: `user_id` is sent on every request as the `x-user-id` HTTP header. Pass it via a GitHub secret — the action will fail immediately if the value is empty.
- **Optional pr_id**: If no PR context is available and `pr_id` is not set, the field is omitted from the request entirely.
- **Error handling**: Controlled by `fail_on_error`. When `true` (default), a failed upload or missing report file fails the workflow step. When `false`, a warning is logged and the step succeeds.
