# Style Guide Specification

## Status

- Status: Active
- Source: [`docs/STYLEGUIDE.md`](../docs/STYLEGUIDE.md)
- Precedence: [`docs/CHARTER.md`](../docs/CHARTER.md) overrides this specification when rules overlap

## Scope

This specification defines the current repository layout, identifiers, filenames, formatting, source style, attribution, Workshop metadata, and enforcement.

## Repository Layout

Keep the shipped mod in `mod/`. Qud loads its XML directly, and the Workshop upload points to this directory.

Keep development files outside `mod/`.

Use these repository areas for their stated purpose:

- `mod/`: shipped XML, map patches, C# scripts, textures, metadata, and preview image
- `docs/`: reference, design, provenance, and release documentation
- `spec/`: active project specifications and the specification template
- `tools/`: validation, reporting, API snapshot, build-log, and asset tools
- `.github/`: workflows, issue templates, pull request templates, and repository automation
- root files: contributor guidance, licenses, configuration, and project metadata

Keep `README.md` as the project entry point.

## Delivery and Versioning

Keep each commit atomic and limited to one logical change.

Use Conventional Commits for commit messages, with a valid type and a repository-specific scope.

Use Conventional PRs. Give each pull request a conventional title, a clear summary, its scope, compatibility impact, and verification details.

Require a `CHANGELOG.md` entry for every pull request. Apply the `skip-changelog` label only when the change records nothing.

Write `CHANGELOG.md` in [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

Place unreleased entries under `## [Unreleased]` and use `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, or `Security` categories.

Mark changes that do not affect the shipped mod as `(internal)`.

Use Semantic Versioning for release versions.

Choose patch releases for defect fixes, minor releases for new content or rebalancing, and major releases for save-breaking changes or removed content.

Keep the `CHANGELOG.md` version, `mod/manifest.json` version, and release tag consistent.

## Observable Behavior

Use established identifiers exactly when Qud, a save, another mod, or a tool resolves them.

Treat vanilla blueprint names, population table names, `.rpm` basenames, and required metadata filenames as frozen.

Treat shipped body part strings, anatomy names, fork blueprint names, and shader names as save-compatible identifiers after release.

Rename coupled artifacts together:

- C# filename, class name, and XML `Name` reference
- texture filename and XML `Tile` reference

Use `Raven_` for inherited CoQE content and retain it as attribution.

Use `Vixy_` for new fork content.

Use vanilla names with `Load="Merge"` for vanilla records.

Use PascalCase XML filenames and directories inside `mod/`.

Use `PascalCase.cs`, one public class per file, and matching filenames for C#.

Use `camelCase.png` with the established affinity and role pattern for textures.

Use lowercase kebab-case for specification filenames.

Use kebab-case or snake_case for tooling scripts, according to the language's norm.

Use `SCREAMING_CASE.md` for root standards and `Title-Case.md` for other root documentation.

Use `type/kebab-case-description` for branches.

Do not use spaces in filenames.

Format XML as UTF-8 with LF endings, two-space indentation, double-quoted attributes, inline self-closing elements, and one blank line between logical object groups.

Write `<object>` attributes in `Name`, `Inherits`, `Load` order.

Write `<part>` with `Name` first, then the order used by vanilla for that part.

Preserve Qud color entities such as `&amp;y` during formatting.

Use `<tag>` or `<stag>` according to the form that vanilla and its consumer require.

Give every new book a fork-owned `ID`. Do not use `Load` on `<book>`.

Write section comments that identify groups. Explain why and when commented-out content remains.

Format C# with PascalCase types and members, `_camelCase` private fields, four-space indentation, `[Serializable]` parts, and lean event handlers.

Format Python in `tools/` with the repository Ruff configuration.

Format JSON, YAML, TOML, XML, C#, Python, and Markdown according to [`.editorconfig`](../.editorconfig).

Use the XML-specific settings in [`.prettierrc.json`](../.prettierrc.json) for `mod/**/*.xml` and `mod/**/*.rpm`.

Keep Markdown prose free of em dashes.
Use clear, composed, warm, and direct language.
Use active voice, complete sentences, and one consistent term for each concept.
Apply the stricter house rules to specifications, technical documentation, changelogs, release notes,
CLI output, error messages, and UI copy.
Apply the looser rules to issues, comments, and chat.
Preserve code, identifiers, paths, quoted errors, proper nouns, legal text, and protected historical text.

## Workshop Requirements

Keep `mod/manifest.json` with the required identity fields, `previewImage`, and `Directories` entries.

Declare optional directories with their controlling option in `manifest.json`.

Keep `manifest.json` `id` stable after publication.

Set `manifest.json` `author` to include Mura and the current maintainer.

Keep `mod/workshop.json` with the assigned Workshop ID, title, BBCode description, tags, visibility, and `preview.png` path.

Never use `"WorkshopId": 0` as a placeholder. Omit the key before Steam assigns an ID.

Keep `preview.png` as an original square PNG under 1 MB. Declare it in both metadata files.

Keep the Workshop description under Steam's 8000-character limit and include the fork statement, original item link, and complete credit list.

## Attribution

Keep the `Raven_` prefix.

Keep Mura's credit list from [`docs/PERMISSION.md`](../docs/PERMISSION.md) in the README, manifest, Workshop description, and release notes where required.

Name Noble Lark explicitly for the subtype sprite contribution.

Credit each outside contribution by name in the README and Workshop description in the pull request that merges it.

## Safety Rules

Never replace vanilla data when an additive merge is possible.

Do not use `<removetable>` to remove vanilla population entries.

Do not rename save-backed identifiers without an explicit compatibility plan.

Do not change escaped Qud color entities during formatting.

Do not add file I/O outside the mod directory, network access, telemetry, shell execution, external assembly loading, Harmony, or reflection into game internals.

Do not add development files to `mod/`.

Do not edit [`docs/2.2-changelog.txt`](../docs/2.2-changelog.txt) or [`docs/mura-feature-notes-wip.txt`](../docs/mura-feature-notes-wip.txt).

## Failure Behavior

Reject a change when an identifier, `Load="Merge"` target, inherited blueprint, table entry, tile, book reference, class reference, or metadata field cannot be resolved.

Treat a missing tile as a runtime defect. Confirm tile names against the installed game or add a valid asset under `mod/Textures/`.

Treat a changed save-backed identifier as a compatibility failure.

Treat a Workshop description over 8000 characters as a release failure.
Reject a pull request that lacks a changelog entry or an approved `skip-changelog` exception.

Reject a commit or pull request that combines unrelated logical changes.

Reject a non-Conventional commit message or pull request title.

Reject a release when its Semantic Versioning, changelog, manifest, or tag values disagree.

Run `python3 tools/validate_mod.py` for mod structure, data, reachability, merge discipline, and scripting policy.

Run `python3 tools/check_docs.py` for documentation links, sections, claims, preserved files, counts, and CI metadata.

Run Prettier for shipped XML and map files, Ruff for `tools/`, Typos for spelling, and Gitleaks for secrets.

Treat runtime behavior and design rationale as acceptance evidence, not as properties that static style checks can prove.

## Verification and Enforcement

Keep the required-check registry synchronized with the CI workflow and pre-commit configuration.

Keep tool versions consistent wherever CI and local hooks pin the same tool.

Use [`.gitattributes`](../.gitattributes) to enforce LF text endings and binary handling.

Install the hooks with `pre-commit install` and run them with `pre-commit run --all-files`.

## Related Files

- [`docs/STYLEGUIDE.md`](../docs/STYLEGUIDE.md)
- [`docs/CHARTER.md`](../docs/CHARTER.md)
- [`docs/PERMISSION.md`](../docs/PERMISSION.md)
- [`mod/manifest.json`](../mod/manifest.json)
- [`mod/workshop.json`](../mod/workshop.json)
- [`mod/`](../mod/)
- [`docs/`](../docs/)
- [`spec/`](./)
- [`tools/validate_mod.py`](../tools/validate_mod.py)
- [`tools/check_docs.py`](../tools/check_docs.py)
- [`.editorconfig`](../.editorconfig)
- [`.gitattributes`](../.gitattributes)
- [`.prettierrc.json`](../.prettierrc.json)
- [`.pre-commit-config.yaml`](../.pre-commit-config.yaml)
