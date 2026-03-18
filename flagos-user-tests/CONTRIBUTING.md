# Contributing to FlagOS User Tests

Thank you for contributing test cases to the FlagOS ecosystem!

## How to Submit a Test Case

### Step 1: Generate a Template

Use the built-in generator to create a properly structured test case:

```bash
# FlagScale training test case
python tools/generators/create_test_template.py \
    --repo flagscale \
    --type train \
    --model <model_name> \
    --name <test_case_name>

# Other repositories
python tools/generators/create_test_template.py \
    --repo <repo_name> \
    --name <test_case_name>
```

### Step 2: Complete the Test Case

1. **Edit the YAML config** with your actual test parameters
2. **Add gold values** from a verified local run (JSON format)
3. **Complete the README.md** with:
   - Description of what the test validates
   - Environment requirements (GPU, CUDA, Python)
   - Manual execution instructions

### Step 3: Validate Locally

```bash
python tools/validators/validate_config.py
python tools/validators/validate_gold_values.py
python tools/validators/lint_test_case.py --strict
```

### Step 4: Submit a Pull Request

1. Fork this repository
2. Create a feature branch: `git checkout -b add-test/<repo>/<name>`
3. Add your test case files
4. Commit and push
5. Open a Pull Request using the provided template

## Test Case Requirements

- Each test case must be in its own directory
- Each directory must contain:
  - At least one `.yaml` configuration file
  - A `README.md` with test documentation
  - Gold values JSON file (for regression tests)
- No sensitive data (tokens, passwords, private paths) in any files
- YAML must pass schema validation
- Gold values must contain numeric arrays

## Code Review

- PRs are reviewed by the respective team CODEOWNERS
- CI must pass before merge
- At least one approval from a maintainer is required

## Experimental Test Cases

If your test case covers a new or unstable feature:
- Place it under `tests/experimental/`
- It will only run in nightly integration tests
- It will not block PR merges

## Questions?

Open an issue using the "New Test Case" template or contact the DevOps team.
