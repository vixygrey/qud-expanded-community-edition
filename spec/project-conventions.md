# Project Conventions Specification

## Status

- Status: Active
- Source: [`CONVENTIONS.md`](../CONVENTIONS.md)

## Scope

This specification defines engineering, delivery, versioning, specification, and documentation rules.

## Observable Behavior

Contributors use maintainable root-cause fixes instead of hacks or symptom suppression.

Each logical change has one atomic commit with a Conventional Commit message.

Each pull request has a Conventional PR title and a body with summary, scope, and verification details.

Each user-visible change has a `CHANGELOG.md` entry in Keep a Changelog format.

Release versions use Semantic Versioning.

Contributors run the pre-commit hooks before each commit.

Work follows an issue-first, trunk-based workflow with squash-merged pull requests.

Project documentation uses clear, composed, warm, and direct language.

Technical documentation uses active voice, complete sentences, and one consistent term for each concept.

Protected legal, quoted, identifier, and historical text remains unchanged.

## Prerequisites

Create or identify an issue before starting code work.

Store specifications in `spec/` and use lowercase kebab-case filenames.

## Safety Rules

Treat security as a requirement for every feature.

Document destructive or irreversible actions before the action.

Keep examples safe to copy and run.

Link scripts and configuration files with repository-relative paths.

## Failure Behavior

Reject work that uses a workaround when a root-cause fix is available.

Reject a release that lacks a changelog entry or uses a non-Semantic Version.

Reject a commit that combines unrelated logical changes.

## Related Files

- [`CONVENTIONS.md`](../CONVENTIONS.md)
- [`CONTRIBUTING.md`](../CONTRIBUTING.md)
- [`CHANGELOG.md`](../CHANGELOG.md)
- [`spec/template.md`](template.md)
