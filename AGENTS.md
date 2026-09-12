# Agent Instructions

These instructions define the default workflow for agents that work in this project.
Project-specific instructions can add constraints. They must not weaken safety requirements.

## Scope

Apply this file to the project root and all child paths unless a nearer `AGENTS.md` provides more specific instructions.

## Before You Change Files

1. Read the relevant source files and nearby tests.
2. Read the project specifications in `specs/` when they exist.
3. Identify every affected caller before changing an exported symbol.
4. Keep the existing architecture unless the task requires a design change.
5. Record the active task in the project state files when the project uses them.

## Implementation Rules

- Make the smallest complete change that satisfies the task.
- Reuse existing project patterns before adding a new pattern.
- Keep names clear and consistent with nearby code.
- Preserve public behavior unless the task changes the contract.
- Remove obsolete code after a clean migration.
- Do not add placeholders, stubs, silent fallbacks, or disabled checks.
- Do not add dependencies without a clear need and an update to project records.
- Do not expose secrets, tokens, personal data, or private paths in source or logs.
- Treat external input as untrusted.
- Avoid destructive commands unless the task requires them and the risk is clear.

## Verification

- Run the narrowest relevant formatter, linter, type check, or test after each change.
- Exercise the changed behavior through the real project surface when practical.
- Add a regression test when a plausible failure can recur.
- Report checks that ran and checks that did not run.
- Do not report a check as passing unless the check ran successfully.

## File and Repository Safety

- Do not overwrite user changes.
- Stop when an unexpected file change affects the task.
- Do not modify generated files when the project provides a source generator.
- Review file permissions when a change creates a file.
- Review rollback steps before any operation that can discard work.

## Completion

Before you finish, confirm that all affected callers, tests, and documentation are consistent.
Summarize the changed files, behavior, and verification results.
State known limitations and follow-up work when they remain.
