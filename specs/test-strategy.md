# Test Strategy

Use the smallest test level that proves the observable behavior.

## Test levels

- Use Python `unittest` for isolated tooling logic and boundary behavior.
- Use `python3 tools/validate_mod.py --all` for mod structure, reference reachability,
  merge discipline, and scripting policy.
- Use `python3 tools/check_docs.py` for documentation links, counts, preserved files,
  and CI metadata.
- Use `npx prettier --check "mod/**/*.xml" "mod/**/*.rpm"` for shipped XML and map formatting.
- Use `ruff check tools/`, `ruff format --check tools/`, and `basedpyright tools/`
  for Python tooling quality.
- Use a game launch and the manual `check-build-log` hook for runtime C# behavior.
- Use manual checks for Workshop metadata, player-facing behavior, and surfaces that
  automation cannot observe.

## Test location

Keep Python tests beside their tools under `tools/` and name them `test_*.py`.

Keep reusable static fixtures under `tools/` only when the fixture represents repository
data and does not contain production data, credentials, personal data, or network state.

Create temporary directories inside tests for generated save, build-log, and metadata inputs.

Do not add development fixtures under `mod/`. The `mod/` directory contains shipped content.

## Feature test runner

Run `specs/run-feature-tests.sh --red` before implementation.

Run `specs/run-feature-tests.sh --green` after implementation.

The runner reads commands only from the trusted test records in `specs/active-feature.yaml`.

The runner records command output and exit status under `specs/.test-results/` and updates
each test result.

Run commands only from trusted project-controlled feature records.

## Test record requirements

Record a stable test ID, test file, test name, executable command, result, and red evidence.

Record a stable manual-check ID, description, and result when automation cannot observe behavior.

Map every test and manual check to one or more acceptance criteria.
