# Release Specification

## Status

- Status: Active
- Source: [`docs/RELEASING.md`](../docs/RELEASING.md)

## Scope

This specification defines the release process for GitHub, Steam Workshop, GOG, and itch distribution.

## Observable Behavior

Every release has one version and one player-facing change note.

The release version matches the newest released heading in `CHANGELOG.md`, `manifest.json`, and both version references in `workshop.json`.

The GitHub release contains the source tag and release notes.

The Workshop upload contains the mod directory and its change note.

The release asset contains the tagged mod snapshot.

The project board moves released work from Staging to Done only after publication.

## Prerequisites

Choose the version according to the Semantic Versioning rules in [`docs/STYLEGUIDE.md`](../docs/STYLEGUIDE.md).

Run `python3 tools/validate_mod.py` before rolling the release.

Prepare Markdown release notes and their BBCode change-note equivalent.

## Safety Rules

WARNING: Do not publish a release with mismatched version fields. Subscribers can receive inconsistent metadata.

WARNING: Do not run publish or tag commands from a dirty worktree. The release tools reject or package unintended files.

Do not edit [`docs/2.2-changelog.txt`](../docs/2.2-changelog.txt).

Do not mark work Done after merging alone. A release must reach the required distribution channels.

## Failure Behavior

Stop when validation, version comparison, Workshop publication, GitHub release creation, or asset generation fails.

Correct the source metadata and rerun the relevant check before continuing.

Leave the board item in Staging when publication is incomplete.

## Related Files

- [`docs/RELEASING.md`](../docs/RELEASING.md)
- [`docs/STYLEGUIDE.md`](../docs/STYLEGUIDE.md)
- [`CHANGELOG.md`](../CHANGELOG.md)
- [`mod/manifest.json`](../mod/manifest.json)
- [`mod/workshop.json`](../mod/workshop.json)
- [`tools/sync_mod.py`](../tools/sync_mod.py)
