# run-ondemand-test

A reusable GitHub Action that runs an arbitrary test command, uploads results as a GitHub Actions artifact, and posts (or updates) a PR comment with the markdown report.

Generalized from FlagGems' `ondemand-test` action for org-wide reuse. Contains only bash and remote-action steps — no local `./` references — so it works from containerized runners via a fully-qualified `@main` ref.

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `test-command` | **yes** | — | Shell command or multi-line script to run. Must produce `report-path` and files at `artifact-path`. |
| `report-path` | no | `report.md` | Path to the markdown report file produced by `test-command` |
| `artifact-name` | **yes** | — | Name for the uploaded results artifact |
| `artifact-path` | no | `results/` | Path to upload as the results artifact |
| `comment-message-id` | **yes** | — | Stable ID for the PR comment (same ID updates the comment on subsequent runs) |
| `github-token` | **yes** | — | Token used to post the PR comment on failure |

## Usage

```yaml
steps:
  - uses: flagos-ai/FlagOps/actions/run-ondemand-test@main
    with:
      test-command: |
        source .venv/bin/activate
        python tools/run_tests.py --ops my_op --gpus "${AVAILABLE_GPUS}" \
          --dump-output --output-dir results/
        python tools/generate_report.py results/ --output report.md
      artifact-name: my_op-nvidia
      comment-message-id: my_op-h20
      github-token: ${{ secrets.GITHUB_TOKEN }}
```

### With compare mode (new vs. baseline)

```yaml
steps:
  - uses: flagos-ai/FlagOps/actions/run-ondemand-test@main
    with:
      test-command: |
        source .venv/bin/activate
        # Run tests on new code
        python tools/run_tests.py --ops ${{ inputs.op }} --output-dir results_new/
        # Fetch baseline from main
        git fetch origin main
        git checkout origin/main -- tests/
        python tools/run_tests.py --ops ${{ inputs.op }} --output-dir results_old/
        # Generate comparison report
        mkdir -p results/
        mv results_old/ results/before && mv results_new/ results/after
        python tools/compare_report.py results/ --output report.md
      artifact-name: ${{ inputs.op }}-${{ inputs.backend }}
      comment-message-id: ${{ inputs.op }}-${{ inputs.runner }}
      github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Behavior

- **test-command**: executed as a bash script. On failure, the `failure-report` step posts a failure notice to the PR.
- **Artifact upload**: uses `continue-on-error: true` so a transient upload failure doesn't block the PR comment.
- **Artifact link**: if upload succeeds, appends a download link to the report before posting it as a comment.
- **PR comment**: uses [`mshick/add-pr-comment`](https://github.com/mshick/add-pr-comment) with `message-id` to update-in-place on repeated runs.

## Migrating from FlagGems `ondemand-test`

The FlagGems-specific `op`, `backend`, `runner`, and `existing` inputs are replaced by a single `test-command` string:

```yaml
# Before (FlagGems-specific)
- uses: ./.github/actions/ondemand-test
  with:
    op: ${{ needs.preprocess.outputs.op }}
    backend: ${{ needs.preprocess.outputs.backend }}
    runner: ${{ needs.preprocess.outputs.runner }}
    existing: ${{ needs.preprocess.outputs.existing }}
    github-token: ${{ secrets.GITHUB_TOKEN }}

# After (org-wide)
- uses: flagos-ai/FlagOps/actions/run-ondemand-test@main
  with:
    test-command: |
      source .venv/bin/activate
      tools/run_tests.py --ops ${{ needs.preprocess.outputs.op }} \
        --gpus "${AVAILABLE_GPUS}" --dump-output --output-dir results_new

      if [ "${{ needs.preprocess.outputs.existing }}" == "0" ]; then
        tools/psum_text --format markdown --output report.md --single results_new
        mv results_new results
      else
        git checkout master
        tools/run_tests.py --ops ${{ needs.preprocess.outputs.op }} \
          --gpus "${AVAILABLE_GPUS}" --dump-output --output-dir results_old
        mkdir results
        mv results_old results/before
        mv results_new results/after
        tools/psum_text --format markdown --single --compare --output report.md results
      fi
    artifact-name: ${{ needs.preprocess.outputs.op }}-${{ needs.preprocess.outputs.backend }}
    comment-message-id: ${{ needs.preprocess.outputs.op }}-${{ needs.preprocess.outputs.runner }}
    github-token: ${{ secrets.GITHUB_TOKEN }}
```
