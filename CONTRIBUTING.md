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

The [**Qud Expanded CE project board**](https://github.com/users/vixygrey/projects/1) is the live
view of the same work, and it's public. Check it before starting: it shows what's already in
progress, and every issue carries a **Track** — Ammo, Content, Systems, Sub-mod merges, Upstream,
Tooling & docs — which is how the work is grouped in practice. If you file something, I'll add it to
the board and set its track; you don't have to.

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

### Your PR merging isn't the end of it

An item only reaches **Done** on the board once the change is live on the Steam Workshop *and* a
release has been cut for everyone else — GOG, itch, and Linux players outside Steam install from
the release zip, and a change that exists only in `main` hasn't reached them.

**QA** is everything between "the code is written" and that: being tested in game, or merged and
waiting on a release. The validators can prove an object is well-formed and reachable; only playing
can prove it does what it says, so an item can sit in QA while its pull request is still open.

So if your change merges and the board doesn't move to Done, nothing is wrong — it's being tested
or waiting on a release, and you'll see it in the changelog when one is cut.

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

Ten checks run on every pull request and all ten must pass. Run
`python3 tools/validate_mod.py` before you commit — locally it costs you seconds instead of a round
trip.

### If you touch `mod/Scripting/`

**Nothing in CI compiles the C#, and nothing can.** Compiling it needs the game's own
`Assembly-CSharp.dll`, which is proprietary and cannot be committed or fetched on a runner. The
validator lints those files, but a linter is not a compiler. Two local checks cover the gap, and both
skip rather than fail if you don't have the game — so neither can block you, and neither is
CI-enforced. That makes running them a courtesy you owe the next person.

**[`tools/compile_scripting.py`](tools/compile_scripting.py) actually compiles it**, in about half a
second, against four DLLs from your Qud install. It runs automatically as a `pre-commit` hook when you
touch `mod/Scripting/`, so usually you'll just see it pass. To run it directly:

```bash
python3 tools/compile_scripting.py
```

It needs a .NET SDK (`brew install dotnet`) and finds one on its own; set `QUD_MANAGED_DIR` or
`QUD_CSC` if your install isn't where it looks. Two things worth knowing: the language version is
pinned to C# 9 on purpose, because the SDK's compiler is newer than the one Unity embeds and would
otherwise accept syntax the game rejects; and the reference set is deliberately narrow, so a file that
starts using a new namespace fails here while compiling fine in game. That is a false *failure* — it
names the missing reference, and the fix is to add it to `REFERENCES`.

**[`tools/check_build_log.py`](tools/check_build_log.py) reads back what the game actually did.** Qud
compiles every enabled mod at launch and records the outcome in `build_log.txt`; this reads that
verdict and refuses it unless it demonstrably describes your working tree — the `identical` check
compares your source against the copy the game compiled, and the `fresh` check rejects a verdict
written before that copy. Launch the game once with the mod enabled, then:

```bash
pre-commit run --hook-stage manual check-build-log
```

That one is manual rather than automatic because mid-work you'll often have edited C# without
relaunching. Set `QUD_SAVE_DIR` if your save directory isn't in the macOS default location.

If you changed C# and couldn't run either, say so in the pull request and I'll run them.

## Two things that will save you pain

**Anything you put in `mod/` ships to subscribers.** That directory is uploaded verbatim; 8 of the
87 mods installed on my machine accidentally ship a `README.md`. Development tooling lives at the
repo root, outside `mod/`.

**Merge, never replace.** `Load="Merge"` on every touch of a vanilla object or table. A full
redeclaration conflicts with any other mod touching the same record *and* silently discards whatever
future Qud patches add to it. `merge-discipline` in the validator will catch you, but it's easier to
write it right the first time.

## The wiki: it explains, `docs/FEATURES.md` specifies

The wiki is for the things a reference document is bad at — what a build actually plays like, how the
chip families interact, which combinations are worth building toward, what a system is *for* in the
game's fiction, how to open a run as a Psionic Adept. [`docs/FEATURES.md`](docs/FEATURES.md) keeps
every figure: tiers, weights, prices, drop rates, stat modifiers, option defaults and their scopes.

| The wiki | `docs/FEATURES.md` |
|---|---|
| What an affinity plays like | The subtype's stat modifiers and resistances |
| How the chip families interact, and what to build toward | Every chip, with its tier, grade and mutation level |
| Why a build works; opening strategy | Starting gear tables, drop rates, the value curve |
| What the Chip Interface is for, in the fiction | Which anatomies carry the slot, and how it merges |
| What an option changes about a run | The option table, defaults, and live/restart/new-character scopes (§13) |

**The rule that falls out of it: link to `docs/FEATURES.md` for figures instead of repeating them.** A
tier, a weight, a price, a drop rate or an option default typed into a wiki page is a copy that nothing
will ever check. Where a number genuinely has to appear inline for a page to read, say where it came
from, so a later reader knows which one wins.

That is a stronger rule for the wiki than for anything in this repository, because **the wiki is a
separate git repository and not one of the ten checks reaches it.** No `typos`, no prettier, no
`tools/validate_mod.py`, no changelog requirement, no review, and no `merge-discipline` or
`unreachable` check standing behind its numbers. It is prose with *fewer* guardrails than the documents
that have now gone quietly stale four times (#93, #96, #106, #139) *with* guardrails — which makes it
the highest-risk place in this project to write a number down.

One practical trap: a wiki page **cannot** use a relative link to a file in this repository, because it
is a different repository. Figures need a full `https://github.com/…/blob/main/docs/FEATURES.md` URL.
That extra friction is exactly what tempts people to paste the number instead. Pay it.

If you're creating or reorganising wiki pages, the home page should link to this section rather than
restate it — same reason: one owner per rule.

## Licensing your contribution

Contributions are offered under the same terms as the project — Apache-2.0 for code, CC BY 4.0 for
content — so it stays consistently licensed. You keep your copyright; you're granting a licence, not
signing anything away. [`COPYING.md`](COPYING.md) has the details, including which parts of this
repository aren't mine to license and why.

## Conduct

[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) — the Contributor Covenant, and the standard I hold
myself to as much as anyone else. If I fall short of it, say so.

## Security

If you find something that could be abused before subscribers can update, please report it
privately rather than opening an issue — [`SECURITY.md`](SECURITY.md) has the details and the
reasoning. This mod ships C# that Qud runs with full process privileges, which is why it has a
policy at all.

## If something here is wrong

Say so — file an issue. The documentation has gone quietly stale four separate times now (#93, #96,
#106, #139) because not one of the ten checks reads a sentence and asks whether it's still true. The
fourth was caused by the two checks that closed #134: they made "the C# has no compile gate" false in
four documents at once, and nothing noticed. A contributor noticing is still the only mechanism that
exists.
