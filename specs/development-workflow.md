# Spec- and Test-Driven Development Workflow

Use this workflow for every feature that changes shipped mod behavior, tooling behavior,
validation behavior, or contributor workflow.

## 1. Discovery

Read `specs/system-architecture.yaml` and `specs/context-map.yaml`.

Read the relevant specifications in `specs/`, including `charter.md` and `style-guide.md`
when the change affects shipped content.

Read the affected files and nearby tests.

Identify the affected paths, identifiers, interfaces, dependencies, risks, and verification needs.

Set `state.yaml.milestone.phase_id` to `discovery`.

## 2. Specification

Create or update `active-feature.yaml`.

Give the feature a stable `feature_id` and a clear title.

Write acceptance criteria with stable IDs such as `AC-001`.

Describe observable behavior in each acceptance criterion.

Record compatibility impact for save-backed identifiers, Qud references, merge targets,
Workshop metadata, and optional directories when applicable.

Set the feature status to `specified` after the criteria are complete.

Set `state.yaml.milestone.phase_id` to `specification`.

## 3. Design

Fill the `design` section in `active-feature.yaml`.

Record constraints, affected interfaces, data flow, and rejected alternatives.

Record the affected repository paths and the required project tools.

Set `state.yaml.milestone.phase_id` to `design`.
Set the feature status to `designed`.

## 4. Test design

Add an automated test or manual check for every acceptance criterion.

Use `tools/test_*.py` for Python tool tests.

Use `python3 tools/validate_mod.py --all` for mod structure and compatibility checks.

Use `python3 tools/check_docs.py` for documentation checks.

Use Prettier, Ruff, basedpyright, and the applicable pre-commit hooks for static checks.

Give every test and manual check a stable ID.

Record the test file and test name when an automated test applies.

Set the feature status to `test_designed`.

Set `state.yaml.milestone.phase_id` to `test_design`.

## 5. Red phase

Run each new automated test before you implement the behavior.

Run `specs/run-feature-tests.sh --red`.

Record the failing result in the test `red_evidence` field.

Use a manual verification record when automation cannot observe the behavior.

## 6. Green phase

Implement the smallest complete change that satisfies the specification.

Keep development files outside `mod/`.

Preserve established identifiers, merge targets, attribution, and metadata fields.

Run `specs/run-feature-tests.sh --green`.

Run the mapped checks after implementation.

Record each test result and verification result in `active-feature.yaml`.

Set the feature status to `implementing` during code changes.

Set `state.yaml.milestone.phase_id` to `implementation`.

## 7. Verification

Run the checks that cover the changed paths:

- `python3 tools/validate_mod.py --all`
- `python3 tools/check_docs.py`
- `python3 -m unittest discover -s tools -v`
- `ruff check tools/`
- `ruff format --check tools/`
- `basedpyright tools/`
- `npx prettier --check "mod/**/*.xml" "mod/**/*.rpm"`

Run `pre-commit run --all-files` before delivery.

Run the manual game checks when the change affects C# scripts, textures, or runtime behavior.

Review every acceptance criterion against its evidence.

Set `verification.status` to `passed` only after the required checks pass.

Set the feature status to `verifying` during final review.

Set `state.yaml.milestone.phase_id` to `verification`.

## 8. Completion

Set the feature status to `complete` only after the validator passes.

Update `state.yaml` with the completed tasks and final check results.

Set `state.yaml.milestone.phase_id` to `complete`.

Run `specs/validate-context.sh --strict` before you archive a completed feature.

Run `specs/archive-feature.sh` before you start another feature.

## Required records

Use `acceptance_criteria[].id` and `acceptance_criteria[].statement`.

Use `test_plan.tests[].id`, `file`, `name`, `command`, `result`, and `red_evidence`.

Use `test_plan.manual_checks[].id`, `description`, and `result`.

Map every criterion to IDs in `verification.tests` or `verification.manual_checks`.

## Test-driven design exceptions

Use manual checks when the game runtime, installed assemblies, or Workshop surface cannot
be observed by an automated test.

Use parser and validator checks for metadata and configuration changes.

Use link, format, and example checks for documentation changes.

Record the reason in `test_plan.reason` when automated TDD does not apply.

## Completion gate

A feature is complete only when its acceptance criteria, design record, test evidence,
verification status, and project state agree.

## Versioning and changelog

Use Semantic Versioning in `VERSION`.

Keep `CHANGELOG.md` in the Keep a Changelog format.

Record user-visible changes under `Unreleased` before release.
