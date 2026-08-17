# Contributing

I'd be glad of the help. This is a community fork and it's meant to act like one.

**You'll be credited by name**, in the README and the Workshop description, in the same pull request
that merges your work — not later, and you shouldn't have to ask. That's charter rule 3, and it's
the one condition Mura attached to opening this mod up, so I treat it as permanent.

**Write however comes naturally to you.** The documents here are in my voice, first person and all,
because I wrote them. That's a description of how I write, not a house style. Your issues, pull
requests and comments are yours — I'd rather have your contribution than a stylistic match.

## Start here

- [`docs/CHARTER.md`](docs/CHARTER.md) — the six rules I maintain this fork under, and why. They're
  constraints rather than aspirations, and most are mechanically enforced.
- [`docs/STYLEGUIDE.md`](docs/STYLEGUIDE.md) — naming, layout, formatting. **Read §1 before renaming
  anything**: several conventions look like mess and are load-bearing identifiers, and breaking one
  fails silently with no error anywhere.
- [`docs/LESSONS.md`](docs/LESSONS.md) — traps I've already hit, mostly about Qud itself. Worth a
  skim; it'll save you an afternoon at some point.
- [`docs/FEATURES.md`](docs/FEATURES.md) — what the mod actually does. §10 is the severity-ranked
  backlog, with a file and line on every open row, and it's a good place to find a first change.

There's **no build step**. Qud loads the XML in `mod/` directly, so you need no toolchain to
contribute. `README.md` covers running the validators and the optional local hooks.

## The workflow

Trunk-based: issue first, short-lived branch, small PR, squash merge.

### Issue first

Nothing gets coded before it's filed. `docs/FEATURES.md` §10 is the backlog to seed from — each row
is already scoped and carries a file and line.

Labels: `bug` · `feature` · `chore` · `docs` · `tech-debt` · `compat` · `upstream-defect` ·
`upstream-qud` · `security` · `dependencies`.

Three of those are less obvious than they look:

- **`compat`** earns its own label because charter rule 1 makes cross-mod and future-patch
  compatibility a distinct class of work rather than a flavour of `bug`.
- **`upstream-defect`** means a bug inherited from Mura's 2.2. **`upstream-qud`** means a bug in
  Caves of Qud itself — the distinction matters, because one is ours to fix and the other is ours to
  work around.
- **`security`** covers charter rule 5: the mod ships C# that runs with full process privileges.

### Branches and commits

- **Short-lived branches off `main`**, named `type/kebab-case-description`. Never commit to `main`;
  a ruleset enforces it server-side and a local hook fails first.
- **Atomic commits** — one logical change each. This matters more here than in most repositories: a
  population-table edit and a blueprint edit can look identical in a diff and have completely
  different blast radii. Never mix a defect fix with a design change in one commit.
- **Conventional commits**, with scopes matching this repo's structure:
  `tables` (`mod/PopulationTables.xml`) · `chips` · `armor` · `melee` · `ranged` · `skills` ·
  `genotypes` · `bodies` · `workshop` · `scripting` · `docs`.

  Example: `fix(tables): merge Artifact 3-8 instead of replacing (closes #3)`.

- **The body carries the causality.** Charter rule 2 lives or dies here — say *why*, and cite the
  convention or the in-world reason. A one-line commit body is a rule-2 violation. This is the rule
  I care most about and the one most easily skipped.

### Pull requests

- **The title must be a conventional commit too.** It becomes the squash commit message, and CI
  checks it.
- **State the compatibility impact** — which vanilla records the change touches, and whether the
  edit is additive. If it touches a table other mods commonly touch, say so.
- **Update [`CHANGELOG.md`](CHANGELOG.md).** [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
  format — `Added` / `Changed` / `Deprecated` / `Removed` / `Fixed` / `Security`, newest first,
  under `[Unreleased]` until a release cuts it. Entries that don't affect the shipped mod are marked
  **(internal)**, because the changelog serves subscribers first and contributors second.

  A PR without a changelog entry is incomplete rather than untidy: the changelog is where charter
  rule 2's causality reaches players, who never read commit messages. CI enforces this; apply the
  `skip-changelog` label if a change genuinely records nothing.

  Mura's `docs/2.2-changelog.txt` is upstream history and is never edited.

Nine checks run on every pull request and all nine must pass. Run
`python3 tools/validate_mod.py` before you commit — locally it costs you seconds instead of a round
trip.

## Two things that will save you pain

**Anything you put in `mod/` ships to subscribers.** That directory is uploaded verbatim; 8 of the
87 mods installed on my machine accidentally ship a `README.md`. Development tooling lives at the
repo root, outside `mod/`.

**Merge, never replace.** `Load="Merge"` on every touch of a vanilla object or table. A full
redeclaration conflicts with any other mod touching the same record *and* silently discards whatever
future Qud patches add to it. `merge-discipline` in the validator will catch you, but it's easier to
write it right the first time.

## Security

If you find something that could be abused before subscribers can update, please report it
privately rather than opening an issue — [`SECURITY.md`](SECURITY.md) has the details and the
reasoning. This mod ships C# that Qud runs with full process privileges, which is why it has a
policy at all.

## If something here is wrong

Say so — file an issue. The documentation has gone quietly stale three separate times (#93, #96,
#106) because none of the nine checks reads a sentence and asks whether it's still true. A
contributor noticing is currently the only mechanism that exists.
