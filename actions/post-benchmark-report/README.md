# Post Benchmark Report Action

A reusable GitHub Action that uploads benchmark data to a backend service, configures list headers, and queries list data with pagination and sorting.

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `backend_url` | **yes** | — | Backend base URL (e.g. `http://host:port`) |
| `report_path` | **yes** | — | Path to the benchmark JSON report file |
| `api_token` | no | `""` | Bearer token for authentication |
| `list_code` | **yes** | — | List code identifier |
| `list_name` | no | `list_code` value | List display name (defaults to `list_code` if empty) |
| `header_config` | **yes** | — | JSON array of header config for custom table columns |
| `repository_name` | no | `${{ github.repository }}` | Repository name |
| `workflow_id` | no | `${{ github.run_id }}` | Workflow run ID |
| `commit_id` | no | `${{ github.sha }}` | GitHub commit SHA |
| `run_id` | no | `${{ github.run_id }}` | GitHub Actions run ID |
| `page_size` | no | `10` | Number of items per page for query |
| `page` | no | `1` | Page number for query |
| `sort` | no | `created_at` | Sort field for query |
| `order` | no | `desc` | Sort direction (`asc` or `desc`) |
| `fail_on_error` | no | `true` | Whether to fail the step on error |

## Outputs

| Output | Description |
|---|---|
| `header_status` | HTTP status code from the header config request |
| `upload_status` | HTTP status code from the data upload request |
| `query_status` | HTTP status code from the data query request |
| `query_result` | JSON response from the data query request |

## Usage

### Basic (in a benchmark workflow)

```yaml
steps:
  - name: Run benchmark
    id: benchmark
    run: |
      python run_benchmark.py --output benchmark_metrics.json

  - name: Upload benchmark report
    if: steps.benchmark.outcome == 'success'
    uses: flagos-ai/FlagOps/actions/post-benchmark-report@main
    with:
      backend_url: 'http://10.1.4.167:30180'
      report_path: 'benchmark_metrics.json'
      list_code: 'benchmark-list'
      list_name: 'Benchmark Results'
      header_config: |
        [{"field":"metric","name":"Metric","required":true,"sortable":true,"type":"string"},
         {"field":"value","name":"Value","required":true,"sortable":true,"type":"number"}]
```

`repository_name`, `workflow_id`, `commit_id`, and `run_id` are auto-detected from the GitHub context.

### With authentication and query options

```yaml
  - uses: flagos-ai/FlagOps/actions/post-benchmark-report@main
    with:
      backend_url: 'http://10.1.4.167:30180'
      report_path: 'benchmark_metrics.json'
      list_code: 'perf-test'
      header_config: |
        [{"field":"metric","name":"Metric","required":true,"sortable":true,"type":"string"},
         {"field":"value","name":"Value","required":true,"sortable":true,"type":"number"}]
      api_token: ${{ secrets.BACKEND_TOKEN }}
      page_size: '20'
      sort: 'updated_at'
      order: 'asc'
      fail_on_error: 'false'
```

### With object-valued metrics (sub-field extraction)

```yaml
steps:
  - name: Upload benchmark report
    uses: flagos-ai/FlagOps/actions/post-benchmark-report@main
    with:
      backend_url: 'http://10.1.4.167:30180'
      report_path: 'benchmark_metrics.json'
      list_code: 'latency-benchmark'
      list_name: 'Latency Benchmark'
      header_config: |
        [{"field":"metric","name":"Metric","required":true,"sortable":true,"type":"string"},
         {"field":"p50","name":"P50","required":true,"sortable":true,"type":"number"},
         {"field":"p99","name":"P99","required":true,"sortable":true,"type":"number"},
         {"field":"mean","name":"Mean","required":true,"sortable":true,"type":"number"}]
```

Where `benchmark_metrics.json` contains:

```json
{
  "latency": {"p50": 1.2, "p99": 3.4, "mean": 2.0},
  "throughput": {"p50": 100, "p99": 80, "mean": 95}
}
```

## Report File Format

The benchmark JSON report file should be a key-value object where each key is a metric name. The value supports two formats:

### Format 1: Array / Primitive value

Each value is an array (or string/number). All `header_config` fields beyond the first receive the entire value.

```json
{
  "elapsed time per iteration (ms):": [8572.3, 766.4, 308.1, 306.5, 306.5],
  "throughput per GPU (TFLOP/s/GPU):": [1.4, 16.2, 39.9, 39.5, 40.4]
}
```

With `header_config`:

```json
[
  {"field": "metric", "name": "Metric", "type": "string", ...},
  {"field": "values", "name": "Values", "type": "number", ...}
]
```

Transformed payload:

```json
{
  "items": [
    {"metric": "elapsed time per iteration (ms):", "values": [8572.3, 766.4, 308.1, 306.5, 306.5], "commit_id": "...", "repository_name": "...", "workflow_id": "...", "run_id": "..."},
    {"metric": "throughput per GPU (TFLOP/s/GPU):", "values": [1.4, 16.2, 39.9, 39.5, 40.4], "commit_id": "...", "repository_name": "...", "workflow_id": "...", "run_id": "..."}
  ]
}
```

### Format 2: Object value (sub-field extraction)

Each value is an object with named sub-fields. `header_config` fields beyond the first each extract the matching sub-field by `field` name.

```json
{
  "latency": {"p50": 1.2, "p99": 3.4, "mean": 2.0},
  "throughput": {"p50": 100, "p99": 80, "mean": 95}
}
```

With `header_config`:

```json
[
  {"field": "metric", "name": "Metric", "type": "string", ...},
  {"field": "p50",    "name": "P50",    "type": "number", ...},
  {"field": "p99",    "name": "P99",    "type": "number", ...},
  {"field": "mean",   "name": "Mean",   "type": "number", ...}
]
```

Transformed payload:

```json
{
  "items": [
    {"metric": "latency", "p50": 1.2, "p99": 3.4, "mean": 2.0, "commit_id": "...", ...},
    {"metric": "throughput", "p50": 100, "p99": 80, "mean": 95, "commit_id": "...", ...}
  ]
}
```

### Transform rules

- `header_config[0].field` → always mapped to each entry's **key** (metric name)
- `header_config[1+].field` → if value is an **object**, extracts `value[field]`; otherwise uses the **entire value**

## `header_config` Format

`header_config` is a JSON array describing the columns of the report list. Each item has the following fields:

| Field | Type | Description |
|---|---|---|
| `field` | string | Column field key |
| `name` | string | Column display name |
| `required` | boolean | Whether the column is required |
| `sortable` | boolean | Whether the column is sortable |
| `type` | string | Data type (`string`, `number`, etc.) |

Example:

```json
[
  {
    "field": "username",
    "name": "用户名",
    "required": true,
    "sortable": true,
    "type": "string"
  }
]
```

## Behavior

1. **Resolve inputs**: Defaults are populated from GitHub context (`github.repository`, `github.run_id`, `github.sha`). `run_id` also defaults to `github.run_id`. If `list_name` is empty, it defaults to `list_code`.
2. **Post header config**: Sends the header configuration to `{backend_url}/flagcicd-backend/list/header`. If the list code already exists, the step is treated as a no-op.
3. **Upload data**: Reads the report file and transforms entries using `header_config`. The first header field receives the metric key; subsequent fields receive sub-fields from the value (if it's an object) or the entire value (if it's an array/primitive). POSTs to `{backend_url}/flagcicd-backend/list/data/{list_code}`. Each item includes `commit_id`, `repository_name`, `workflow_id`, and `run_id`.
4. **Query data**: After a successful upload, queries the list data with pagination and sorting from `{backend_url}/flagcicd-backend/list/data/{list_code}`.
5. **Error handling**: Controlled by `fail_on_error`. When `true` (default), a failed request or missing report file fails the workflow step. When `false`, a warning is logged and the step succeeds.
