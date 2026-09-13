# Contributing

This is a community fork, and community contributions are welcome.

**You will be credited by name** in the README and the Workshop description in the pull request
that merges your work. You do not need to ask. This follows charter rule 3, the condition Mura
attached to opening this mod. I treat that condition as permanent.

**Use the house writing style in project documentation.** Keep prose clear, composed, warm, and direct.
Use the stricter rules for documentation, specifications, changelogs, release notes, CLI output, error
messages, and UI copy. Use the looser rules for issues, pull requests, comments, and chat.

## Start here

- [`docs/CHARTER.md`](docs/CHARTER.md) covers the six rules that maintain this fork and explains them.
  The rules are constraints, and most are mechanically enforced.
- [`docs/STYLEGUIDE.md`](docs/STYLEGUIDE.md) covers naming, layout, and formatting.
  **Read §1 before renaming anything.** Several conventions are load-bearing identifiers.
  Breaking one can fail without an error.
- [`docs/LESSONS.md`](docs/LESSONS.md) collects traps from Qud and prior maintenance work.
  Read it before a first change.
- [`docs/FEATURES.md`](docs/FEATURES.md) records the mod's behavior.
  §10 contains the severity-ranked backlog with a file and line for every open row.

The mod has no build step.
Qud loads the XML in `mod/` directly, so contributors need no toolchain.
`README.md` covers the validators and optional local hooks.

## The workflow

Trunk-based: issue first, short-lived branch, small PR, squash merge.

### Issue first

File an issue before starting code work.
Use [`docs/FEATURES.md`](docs/FEATURES.md) §10 as a backlog source.
Each backlog row has a scope, file, and line.

The [**Qud Expanded CE project board**](https://github.com/users/vixygrey/projects/1) shows active work.
Check it before starting.
Each issue has a **Track** for Ammo, Content, Systems, Sub-mod merges, Upstream, or Tooling & docs.
The maintainer adds filed issues to the board and assigns their tracks.

Labels: `bug` · `feature` · `chore` · `docs` · `tech-debt` · `balance` · `compat` ·
`upstream-defect` · `upstream-qud` · `security` · `dependencies`.

Four of those are less obvious than they look:

- **`compat`** earns its own label because charter rule 1 makes cross-mod and future-patch
  compatibility a distinct class of work rather than a flavour of `bug`.
- **`upstream-defect`** means a bug inherited from Mura's 2.2. **`upstream-qud`** means a bug in
  Caves of Qud itself. The distinction matters, because one is ours to fix and the other is ours to
  work around.
- **`security`** covers charter rule 5: the mod ships C# that runs with full process privileges.
- **`balance`** means the change moves a number a player feels: damage, weight, a release duration,
  a drop weight. It is orthogonal to `bug` rather than a softer version of it: a value can be plainly
  wrong *and* correcting it can change how the mod plays, and the second half wants deciding against
  the value curves in [`docs/STYLEGUIDE.md`](docs/STYLEGUIDE.md) §3.2 rather than riding along with
  the fix.

### Branches and commits

- **Use short-lived branches off `main`** with names such as `type/kebab-case-description`.
  Never commit to `main`.
  A server-side ruleset and a local hook enforce this rule.
- **Make atomic commits.** Keep one logical change in each commit.
  Do not mix a defect fix with a design change.
  A population-table edit and a blueprint edit can look similar in a diff and have different risks.
- **Use Conventional Commits** with scopes that match this repository:
  `tables` (`mod/Core/PopulationTables.xml`) · `chips` · `armor` · `melee` · `ranged` · `skills` ·
  `genotypes` · `bodies` · `workshop` · `scripting` · `docs`.

  Example: `fix(tables): merge Artifact 3-8 instead of replacing (closes #3)`.

- **State the cause in the commit body.** Cite the relevant convention or in-world reason.
  A one-line commit body violates charter rule 2.

### A merged PR still needs a release

An item reaches **Done** after the change is live on the Steam Workshop and a release is available.
GOG, itch, and Linux players outside Steam install the release zip.
A change that exists only on `main` has not reached those players.

**QA** identifies code that needs play testing.
Validators prove that an object is well-formed and reachable.
Only gameplay proves the stated behavior.
**Staging** identifies all work merged since the last release.

A merged change remains in Staging until release.
The changelog records it when the release is cut.

**An issue closed without shipping goes straight to Done.**
#364 records the first such issue.
Its premise did not hold, so the issue will not appear in a release.
The close reason distinguishes `completed` from `not planned`.

The maintainer cuts releases.
[`docs/RELEASING.md`](docs/RELEASING.md) describes the process and the waiting points.

### Pull requests

- **Use a Conventional Commit as the title.** The title becomes the squash commit message.
  CI checks it.
- **State the compatibility impact.** Name each vanilla record that the change touches.
  State whether the edit is additive.
  Identify any commonly edited population table.
- **Update [`CHANGELOG.md`](CHANGELOG.md).** Use [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
  categories: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, and `Security`.
  Place entries under `[Unreleased]` until release.
  Mark entries that do not affect the shipped mod as **(internal)**.

A pull request without a changelog entry is incomplete.
The changelog carries charter rule 2's causality to players.
CI enforces this requirement.
Apply the `skip-changelog` label only when the change records nothing for subscribers.

Mura's `docs/2.2-changelog.txt` is upstream history and is never edited.

Ten checks run here and all ten must pass.
Run `python3 tools/validate_mod.py` before committing.

### If you touch `mod/Scripting/`

**CI does not compile the C#.** Compilation needs the proprietary
`Assembly-CSharp.dll`, which cannot be committed or fetched on a runner.
The validator lints these files, but a linter is not a compiler.
Two local checks cover this gap.
Both checks skip when the game is unavailable.

**[`tools/compile_scripting.py`](tools/compile_scripting.py) compiles the C#.**
It uses four DLLs from the Qud installation.
The `pre-commit` hook runs it when a change touches `mod/Scripting/`.
Run it directly with:

```bash
python3 tools/compile_scripting.py
```

The command needs a .NET SDK.
It finds the SDK automatically.
Set `QUD_MANAGED_DIR` or `QUD_CSC` when the installation uses another path.
The compiler uses C# 9 because Unity embeds an older compiler.
The reference set is narrow, so a new namespace can fail here while succeeding in the game.
Add the missing reference to `REFERENCES` when that failure occurs.

**[`tools/check_build_log.py`](tools/check_build_log.py) reads the game build log.**
Qud compiles each enabled mod at launch and records the result in `build_log.txt`.
This tool compares that result with the working tree.
The `identical` check compares source with the compiled copy.
The `fresh` check rejects a verdict from before that copy.
Launch the game with the mod enabled before running:

```bash
pre-commit run --hook-stage manual check-build-log
```

Run this check manually after each C# change.
Set `QUD_SAVE_DIR` when the save directory is not in the macOS default location.
Report the result in the pull request when local compilation is unavailable.

### After a Qud update

**[`tools/snapshot_qud_api.py`](tools/snapshot_qud_api.py) records names that Qud exposes.**
`tools/validate_mod.py` uses those names to check part names, blueprint names, and part attributes
on a runner without a game installation.
The answers are committed to `tools/qud-api.json`.
The validator reads that file and runs everywhere.

**Regenerate the snapshot after every game update.**
Run it with `tools/check_vanilla_drift.py`:

```bash
python3 tools/snapshot_qud_api.py --assembly
```

The `--assembly` option is required.
The committed snapshot uses it.
A run without it drops 656 part names and the generator refuses that result (#244).

The `snapshot-check` pre-commit hook runs `--check` on every commit.
It uses `always_run` instead of a file pattern because a Qud update can affect any file.
The hook skips when the game, .NET SDK, or `ilspycmd` is absent.
The `--require` option changes that skip into a failure.

Install the .NET SDK and `ilspycmd` to run the check:

```bash
dotnet tool install -g ilspycmd
export PATH="$PATH:$HOME/.dotnet/tools"
```

The `export` command remains required after installation.
The .NET installer writes the literal string `~/.dotnet/tools` to `/etc/paths.d/dotnet-cli-tools`.
`path_helper` copies that string without expanding `~`.
The path therefore points to a directory named `~` and matches no binaries.
Use `$HOME` in the shell profile:

```bash
export PATH="$HOME/.dotnet/tools:$PATH"
```

The hook skips until the profile contains the corrected path.

### Checking the wiki's links into this repository

The [wiki](https://github.com/vixygrey/qud-expanded-community-edition/wiki) links to repository figures.
It contains 89 anchor links across 27 pages, mostly into `docs/FEATURES.md`.
GitHub derives anchors from heading text.
**Renaming a heading silently breaks every wiki link to it.**
The server can still return HTTP 200 for a broken fragment.
The links use 67 distinct headings.

```bash
python3 tools/check_docs.py --wiki
```

This command clones the public wiki and checks every anchor.
Pass `--wiki-path PATH` to check an existing clone.
The command runs outside the normal checks because it needs another repository and network access.
**Run it after renaming or removing a heading cited by the wiki.**

The command checks link targets, not page accuracy.
Search the wiki for affected claims after a change lands.
The wiki is a separate repository, so contributors must clone it before searching.

### Seeing what a `DynamicObjectsTable:` tag distributes

A `DynamicObjectsTable:` tag distributes a blueprint, but the tag site does not show its destinations.
The validator checks `Blueprint="…"` references and new blueprint reachability.
It does not resolve distribution tags.
Tags inherit, so the tagged blueprint is often not the distributed blueprint.

```bash
python3 tools/report_dynamic_tables.py
```

The report separates fork declarations from vanilla inheritance.
Only fork declarations represent decisions in this repository.
For example, `DynamicObjectsTable:Items` reaches 325 fork blueprints through vanilla distribution.

**The `--check` option fails on membership drift.**
`tools/dynamic-pools.json` pins pool membership.
The `pre-commit` hook compares current membership with that file.
Use `--snapshot` when an intended change adds or removes a blueprint:

```bash
python3 tools/report_dynamic_tables.py --check     # the hook
python3 tools/report_dynamic_tables.py --snapshot  # an intended change
```

The report needs the game because `BaseArrow` is vanilla.
A mod-only run would miss the important tag.
The command skips without the game.
The `--require` option turns that skip into a failure.

## Two rules that prevent common errors

**Anything under `mod/` ships to subscribers.** The directory is uploaded verbatim.
Development tooling belongs at the repository root.

**Merge, never replace.** Use `Load="Merge"` for every change to a vanilla object or table.
A full redeclaration conflicts with other mods and discards future Qud patches.
The `merge-discipline` validator check catches violations.

## The wiki: it explains, `docs/FEATURES.md` specifies

The wiki explains play patterns, chip combinations, opening strategy, system purpose, and fiction.
[`docs/FEATURES.md`](docs/FEATURES.md) specifies tiers, weights, prices, drop rates, stat modifiers,
option defaults, and option scopes.

| The wiki | `docs/FEATURES.md` |
|---|---|
| What an affinity plays like | The subtype's stat modifiers and resistances |
| How the chip families interact, and what to build toward | Every chip, with its tier, grade and mutation level |
| Why a build works and its opening strategy | Starting gear tables, drop rates, and the value curve |
| What the Chip Interface does in the fiction | Anatomies that carry the slot and its merge behavior |
| What an option changes about a run | The option table, defaults, and live, restart, or new-character scopes (§13) |

**Link to `docs/FEATURES.md` for figures instead of repeating them.**
A wiki number has no repository check.
State the source when a number must appear inline.

The wiki is a separate repository.
It is separate, and not one of the ten checks reaches it.
It has no Typos, Prettier, `tools/validate_mod.py`, changelog requirement, or merge-discipline check.
Search the wiki for affected claims after each change.

Clone the wiki anonymously:

```bash
git clone https://github.com/vixygrey/qud-expanded-community-edition.wiki.git
```

Do not use a relative link from the wiki to this repository.
Use a full URL such as `https://github.com/…/blob/main/docs/FEATURES.md`.

Link the wiki home page to this section instead of repeating its rules.

## Licensing your contribution

Contributions use the project licenses:
Apache-2.0 for code and CC BY 4.0 for content and documentation.
You retain your copyright and grant the project a license.
[`COPYING.md`](COPYING.md) describes reuse rights and inherited work.

## Conduct

[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) contains the Contributor Covenant.
It applies to every contributor, including the maintainer.
Report a concern when conduct falls below that standard.

## Security

Report a vulnerability privately before opening an issue.
[`SECURITY.md`](SECURITY.md) describes the process and its reason.
This mod runs C# with full process privileges, so the policy is necessary.

## Report documentation errors

File an issue when this documentation is wrong.
Four stale-documentation incidents (#93, #96, #106, and #139) showed that static checks do not assess truth.
A contributor report remains the only check for claims that tools cannot measure.
