# Coding Conventions

This document defines language-agnostic conventions for project code and supporting files.
Language-specific rules can add detail when they follow the rules in this document.

## Core Principles

- Prefer clear code over clever code.
- Keep each module focused on one responsibility.
- Make data flow and side effects visible.
- Preserve simple interfaces.
- Choose predictable behavior over hidden behavior.
- Remove code that no longer serves the current design.

## Formatting

- Follow `.editorconfig`.
- Use the formatter that the project defines.
- Keep line breaks, indentation, and quoting consistent with nearby files.
- Do not reformat unrelated code.
- Keep comments short and explain decisions, constraints, or risks.

## Naming

- Use names that describe purpose.
- Use one term for one concept across the project.
- Match the naming style of the language and existing code.
- Avoid unexplained abbreviations.
- Name boolean values as conditions when the language supports that style.

## Structure

- Keep public interfaces small.
- Keep functions and methods focused.
- Separate parsing, validation, transformation, storage, and presentation.
- Keep configuration separate from executable logic.
- Place tests near the code or in the project test structure.
- Prefer existing directories and file patterns.

## Errors and Validation

- Validate external input at the system boundary.
- Return or raise errors that identify the failed operation.
- Preserve useful error context.
- Do not catch errors without handling or rethrowing them.
- Do not use broad fallback behavior to hide failures.
- Use explicit defaults for missing or invalid configuration.

## Tests and Verification

- Test observable behavior.
- Cover normal behavior, boundaries, invalid input, and important state changes.
- Keep tests deterministic and isolated.
- Use the project test command and test naming pattern.
- Remove tests that only assert implementation details.
- Document manual verification when automation cannot cover the behavior.

## Git and Change Management

- Keep every commit atomic. Each commit must represent one coherent change.
- Use Conventional Commits for every commit.
- Use Conventional PRs for every pull request.
- Use a Conventional Commit-style title with an optional scope for every pull request.

## Best Practices

- Always use established best practices for the language, framework, and project.
- Choose the first correct design instead of a temporary workaround.
- Do not add hacks, bypasses, hidden exceptions, or symptom suppression.
- Fix root causes instead of masking failures.
- Prefer a complete solution over a partial solution.
- Keep quality gates enabled.

## Versioning and Changelog

- Use Semantic Versioning for every release.
- Record the current version in `VERSION`.
- Keep `CHANGELOG.md` in the Keep a Changelog format.
- Record user-visible changes under `Unreleased` before release.

## Dependencies and Configuration

- Use the project package manager and lockfile.
- Keep dependency versions reproducible.
- Add a dependency only when existing project code cannot provide the required behavior.
- Keep environment-specific values outside committed source when appropriate.
- Do not commit secrets or credentials.

## Security

- Treat files, network responses, commands, and user input as untrusted.
- Apply least privilege to file, network, and process access.
- Use secure parsers and disable unnecessary external resource resolution.
- Avoid shell interpolation with untrusted values.
- Log enough context for diagnosis without logging sensitive data.
- Review changes that affect authentication, authorization, cryptography, or data handling.

## Documentation and Changes

- Update documentation when a public behavior or workflow changes.
- Keep examples valid and current.
- Use the project terminology consistently.
- Keep commits focused on one coherent change.
- Include verification results in change descriptions.
