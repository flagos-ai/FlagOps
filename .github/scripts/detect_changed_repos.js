// Detect which repos have changed test cases.
//
// Outputs (via core.setOutput):
//   changed_cases      — JSON array of case paths (manual single-case dispatch)
//   changed_repos      — JSON object {repo, task, model} (manual repo dispatch or _none_)
//   changed_repos_list — JSON array of repo names (auto-detected from PR/push)
//
// Called from workflow via:
//   uses: actions/github-script@v7
//   with:
//     script: |
//       const run = require('./.github/scripts/detect_changed_repos.js');
//       await run({ github, context, core });

module.exports = async ({ github, context, core }) => {
  const inputCase = process.env.INPUT_CASE || '';
  const inputRepo = process.env.INPUT_REPO || '';
  const inputTask = process.env.INPUT_TASK || '';
  const inputModel = process.env.INPUT_MODEL || '';

  // Manual dispatch — single case
  if (inputCase) {
    core.setOutput('changed_cases', JSON.stringify([inputCase]));
    return;
  }

  // Manual dispatch — by repo
  if (inputRepo) {
    core.setOutput('changed_repos', JSON.stringify({
      repo: inputRepo,
      task: inputTask,
      model: inputModel,
    }));
    return;
  }

  // Auto-detect from changed files
  let files = [];
  if (context.eventName === 'pull_request') {
    const resp = await github.paginate(
      github.rest.pulls.listFiles,
      { owner: context.repo.owner, repo: context.repo.repo, pull_number: context.issue.number }
    );
    files = resp.map(f => f.filename);
  } else {
    const resp = await github.rest.repos.compareCommits({
      owner: context.repo.owner, repo: context.repo.repo,
      base: context.payload.before, head: context.payload.after,
    });
    files = resp.data.files.map(f => f.filename);
  }

  // Extract unique repos from changed paths
  const repos = new Set();
  for (const f of files) {
    const m = f.match(/^flagos-user-tests\/tests\/([^/]+)\//);
    if (m && m[1] !== 'experimental') repos.add(m[1]);
  }

  if (repos.size === 0) {
    core.setOutput('changed_repos', JSON.stringify({ repo: '_none_' }));
  } else {
    core.setOutput('changed_repos_list', JSON.stringify([...repos]));
  }
};
