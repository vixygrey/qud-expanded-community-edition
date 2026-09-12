# Contributing

Use the project records as the source of truth for every behavior change.

Read `CONVENTIONS.md` before you change code.

## Start a feature

1. Read `specs/development-workflow.md`.
2. Read `specs/definition-of-ready.md`.
3. Update `specs/active-feature.yaml`.
4. Record the impact analysis and design.
5. Add an ADR when an architecture decision changes.
6. Map every acceptance criterion to a test or manual check.

## Test-driven development

Run `specs/run-feature-tests.sh --red` before implementation when automated tests apply.

Implement the smallest complete change.

Run `specs/run-feature-tests.sh --green` after implementation.

Record test results and red evidence in `specs/active-feature.yaml`.

Use the fixture convention in `specs/test-strategy.md`.

## Verification

Run `specs/validate-context.sh` during development.

Run `specs/validate-context.sh --strict` before archive.

Run the formatter, linter, build, type checks, and project test commands when they exist.

Run `specs/archive-feature.sh` only after the feature reaches `complete`.

## Git and pull requests

Keep each commit atomic.

Use Conventional Commits for every commit.

Use a Conventional Commit-style PR title with an optional scope.

Describe observable behavior and verification evidence in the PR body.

Enable the generated hook with:

```bash
git config core.hooksPath .githooks
```

## Versioning and changelog

Use Semantic Versioning in `VERSION`.

Keep `CHANGELOG.md` in the Keep a Changelog format.

Add user-visible changes under `Unreleased` before release.

Move entries to a versioned section when you release.
