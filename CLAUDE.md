# Working notes

Whatever is left here is what applies to me rather than to the project. It becomes untracked in the
last step of #115; until then it is still in version control, so nothing private belongs in it yet.

The project's own documents are:

- `docs/CHARTER.md` — the six rules I maintain this fork under, and why
- `docs/LESSONS.md` — operational traps, Qud internals, git and GitHub
- `docs/STYLEGUIDE.md` — naming, layout, formatting
- `docs/FEATURES.md` — the complete feature reference

@docs/CHARTER.md
@docs/LESSONS.md

What stays here is what applies to me rather than to the project.

# Caves of Qud Expanded — fork working notes

## Validating changes

There is no test suite. The minimum bar before any commit — this would have caught the
`mod/Skills.xml` bug:

```bash
python3 - <<'EOF'
import xml.etree.ElementTree as ET, glob, sys
bad = 0
for f in glob.glob('mod/*.xml') + glob.glob('mod/ObjectBlueprints/*.xml') + glob.glob('mod/*.rpm'):
    try:
        ET.parse(f)
    except Exception as e:
        print(f'FAIL {f}: {e}'); bad = 1
print('all XML parses' if not bad else 'PARSE ERRORS ABOVE')
sys.exit(bad)
EOF
```

Useful follow-up checks, all scriptable against the XML:

- Every `Blueprint="..."` in `mod/PopulationTables.xml` resolves to a real object.
- Every new blueprint is reachable — appears in a population table **or** has a `TinkerItem` part.
  (This is the check that surfaces the 72 chips and 9 armor pieces.)
- Every `Raven_Mod*` part referenced by a chip has a matching class in `mod/Scripting/`.
  (Currently clean: 36 referenced, 36 defined.)
- Tier tags are internally consistent with the value curve.

In-game, `wish` is the fastest way to spawn a blueprint by name and eyeball it.

## Workflow

Trunk-based, per the global rules, with these project specifics:

- **Issue first, always.** Nothing gets coded before it's filed. `docs/FEATURES.md` §10 is the backlog
  to seed from — each row is already scoped, severity-ranked, and carries a file and line.
  Labels: `bug`, `feature`, `chore`, `docs`, `tech-debt`, `compat`, `upstream-defect`.
  `compat` earns its own label because charter rule 1 makes it a distinct class of work.
- **Short-lived branches off `main`**, squash-merged, deleted after. Never commit to `main`.
- **Atomic commits** — one logical change each. This matters more than usual here: a
  population-table edit and a blueprint edit can look identical in a diff and have completely
  different blast radii. Never mix a defect fix with a design change in one commit.
- **Conventional commits**, with scopes that match this repo's structure:
  `tables` (`mod/PopulationTables.xml`) · `chips` · `armor` · `melee` · `ranged` · `skills` ·
  `genotypes` · `bodies` · `workshop` · `scripting` · `docs`.
  Example: `fix(tables): merge Artifact 3-8 instead of replacing (closes #3)`.
- **The body carries the causality.** Charter rule 2 lives or dies here — say *why*, and cite the
  convention or the in-world reason. A one-line commit body is a rule-2 violation.
- **Every PR states its compatibility impact** — which vanilla records it touches and whether the
  edit is additive. If it touches a table other mods commonly touch, say so.
- **Every PR updates `CHANGELOG.md`.** [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
  format — `Added` / `Changed` / `Deprecated` / `Removed` / `Fixed` / `Security`, newest first,
  under `[Unreleased]` until a release cuts it. Entries that don't affect the shipped mod are
  marked **(internal)**, because the changelog serves subscribers first and contributors second.
  A PR without a changelog entry is incomplete, not merely untidy: the changelog is where charter
  rule 2's causality reaches players, who never read commit messages.
  Mura's `docs/2.2-changelog.txt` is upstream history and is never edited.
- Run `python3 tools/validate_mod.py` before every commit. CI runs it too, alongside prettier for
  XML formatting, `typos`, ruff, gitleaks, CodeQL, and a PR-conventions job that checks the title
  and the changelog — but locally is where it costs you seconds instead of a round trip.

## Voice — write as me

This applies to **my** writing and to anything written on my behalf: documentation, GitHub issues,
pull request bodies, changelog entries, commit messages. It is not a rule for contributors, and
`docs/STYLEGUIDE.md` §8 says so explicitly — anyone else writes however comes naturally to them.

- **First person singular.** "I checked this against the DLL rather than assuming it", not "the
  caveat was checked". I decided these things; the prose should say so rather than reporting
  conclusions as though they arrived on their own.
- **Never "we".** There is one of me. The repository used "we" and "our" nowhere before this rule
  existed, so it describes what was already true rather than adding a constraint.
- **"You" is the reader** — the register `README.md` already used.
- **She/her**, in the rare place a third-person reference to me survives the switch to first person.
- **Warmth comes from directness and from explaining reasoning**, not from padding. No hedging for
  its own sake, no softening of a real problem, no exclamation marks. Never reach for stereotyped
  markers of a "feminine" register; they would make the writing worse and condescend at the same
  time.

**This continues Mura's voice rather than replacing it.** `docs/2.2-changelog.txt` is already
written this way — *"Decreased base SP gain to 95, I felt they were a little too overtuned in that
regard"*. A fork whose third charter rule is about carrying someone's work forward should carry
their voice too. It also serves rule 2: "I decided X because Y" holds a reason in a way "X was
decided" does not.

**The AI disclosure is what makes this honest.** `README.md` and the Workshop description both state
plainly that I use AI for development and documentation, and the `Co-Authored-By:` trailer stays on
commits with the "Generated with Claude Code" footer on pull requests. Writing in my voice is
ghostwriting with the ghost declared — remove the disclosure and it stops being that, so the
disclosure is the condition under which this section is acceptable at all, not decoration.

**A voice rewrite must prove it changed nothing else.** Prose has already gone quietly untrue three
times here (#93, #96, #106), no gate noticed, and a voice pass touches every sentence at once. So
extract every number, inline-code identifier, file path, link target and issue reference before and
after, and diff the two sets: a voice change moves **zero** of them. Anything that moves is either a
mistake or a deliberate fix, and the pull request says which.

> **None of these gates reads prose.** Every one inspects a machine-readable property, so a
> document asserting something no longer true passes all of them. See *Stale prose rots silently*
> below, and grep the docs for a defect's name in the PR that closes it.

## Lessons learned — mine only

The shared ones live in `docs/LESSONS.md`, which this file imports. Two stay here because they
are about my own setup rather than about Qud or this repository.

### The sibling design docs are not verified sources

`../design-docs/` was written before this project had a metadata reader or the installed-mod
corpus to check against. `DESIGN_sleep.md` §7 recommends reading options with `[OptionFlag]`,
calling `Options.GetOption` "legacy". Measured: **zero of 87 installed mods use `[OptionFlag]`
field binding; 17 use `GetOption`.**

Treat those docs as design thinking, not as an API reference. Anything they assert about the game
gets checked against the DLL metadata or the installed mods before code is written against it.

### When the only test environment is someone else's machine, batch the experiments

Every hypothesis here costs a full round-trip through the maintainer: copy the mod, launch Qud,
reproduce, report. That is the dominant cost, not the thinking.

So: prepare the **whole bisect set at once** — one variant per suspected cause, numbered in
descending order of suspicion — rather than one change per exchange. And compare against working
examples on *value ranges*, not just structure: every installed slider uses `Min` of 0 or 1, and
this mod's used 6, which no amount of checking that the attributes were "present and correct"
would have surfaced.

