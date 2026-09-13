# Project Conventions

## Engineering Principles

Follow established best practices.

Do not use workarounds or hacks.

Implement the correct solution, even when it requires more work.

Prefer maintainable solutions over quick solutions.

Resolve root causes instead of hiding symptoms.

Treat high security as a requirement for every feature.

## Delivery and Versioning

Keep each commit atomic and limited to one logical change.

Use Conventional Commits for commit messages.

Use Conventional PRs with a clear summary, scope, and verification details.

Keep `CHANGELOG.md` for every user-visible change.

Follow the Keep a Changelog format.

Use Semantic Versioning for release versions.

Run the pre-commit hooks before each commit.

Use a trunk-based Git strategy.

Create or identify an issue before starting code work.

Always squash-merge pull requests.

## Specifications

Store specifications in [`specs/`](specs/).

Read [`specs/README.md`](specs/README.md) before writing a specification.

Start new specifications from [`specs/template.md`](specs/template.md).

Use these specifications as the concise requirement layer:

- [`specs/charter.md`](specs/charter.md)
- [`specs/style-guide.md`](specs/style-guide.md)
- [`specs/maintenance-lessons.md`](specs/maintenance-lessons.md)
- [`specs/releasing.md`](specs/releasing.md)
- [`specs/project-conventions.md`](specs/project-conventions.md)

Name files with lowercase kebab-case.

Describe observable behavior, prerequisites, safety rules, and failure behavior.

Use MUST for required behavior and MAY for optional behavior.

Link related scripts and configuration files with repository-relative paths.

## Documentation

Use concise headings and short paragraphs.

Use code blocks for commands and identifiers.

Document destructive or irreversible actions with a clear warning before the action.

Keep examples safe to copy and run.

## House Writing Style

Write polished, composed, warm, and direct prose.

Use clear American English, active voice, and one consistent term for each concept.

Write instructions in the imperative. Put required conditions before commands.

Keep one topic per paragraph and one instruction per sentence.

Keep descriptive sentences to 25 words or fewer and procedural sentences to 20 words or fewer.

Use complete sentences with articles. Do not use contractions.

Do not use em dashes, semicolons, filler words, Latin abbreviations, or unexplained jargon.

Put a clear command before the risk in warnings and cautions.

Keep code, identifiers, file paths, quoted errors, proper nouns, legal text, and preserved historical text unchanged.
Preserve intentional voice in design philosophy and historical rationale when that voice carries design meaning.

Use the house style for specifications, technical documentation, changelogs, release notes, error messages, CLI output, and UI copy.

Use a looser version for issues, comments, and chat. Keep those passages clear and free of filler.
