# Caves of Qud Expanded — fork working notes

## What this is

A community fork of **Caves of Qud Expanded** (Steam Workshop `1134036260`), originally by
**Mura** (`@mura_raven`). Fork permission is public and explicit — see `docs/PERMISSION.md`.

**`mod/` is the mod.** There is no build step: Qud loads those XML files directly, and `mod/` is
what gets packaged and uploaded to the Workshop. **Anything you put in `mod/` ships to
subscribers** — 8 of the 87 mods installed locally accidentally ship a `README.md`, 5 a `LICENSE`,
4 a `.csproj`. Development tooling lives at the repo root, outside `mod/`, so it never reaches
players. Point the Workshop uploader at `mod/`, not the repo root.

```
mod/     the shipped mod          docs/    reference documentation
tools/   validation and helpers   .github/ CI
```

**Read `docs/FEATURES.md` before touching anything.** It's the complete reference for what the mod
does — every system, every item, all 350 new blueprints and 209 vanilla merges, reconstructed
from the source because no complete list ever existed. Section 10 is the bug/fork checklist.
**`docs/STYLEGUIDE.md`** covers naming, formatting, and Workshop requirements — read §1 before
renaming anything, because several conventions that look like mess are load-bearing identifiers.

## Fork charter

Six rules, set by the maintainer at the start of the fork. They are constraints, not
aspirations — where existing content violates one, that's debt to pay down, not precedent.

### 1. Compatibility is a hard constraint

Compatible with vanilla, with future Qud patches, and with other mods. In practice:

- **Merge, never replace.** `Load="Merge"` on every touch of a vanilla object or table. A full
  redeclaration both conflicts with any other mod touching the same record *and* silently
  discards future vanilla additions to it. **The two inherited violations are now paid off** —
  the `Artifact 3`–`8` replacements (#3, fixed in #34) and the `<removetable>` chain in
  `Armor 7C/7R/8C/8R` that severed the tier cascade (#4, fixed in #85). They are recorded here
  because they were debt, not precedent: both were deliberate upstream choices made for
  convenience, and both cost more than they bought. Don't reintroduce either shape.
- **Additive over destructive.** Add entries rather than removing them; adjust weights rather
  than stripping tables.
- **Know the blast radius.** The `Chip Interface` merge into base `Humanoid` reaches every
  humanoid in the game at once. Changes at that level need to be deliberate and stated.
- ✅ **Verified 2026-08-15: 2.2 loads and plays on current Qud** (maintainer, Legion Go 2 S).
  Compatibility work here is about *other mods* and *future patches* — not about booting.

### 2. Causality — nothing arbitrary

Every change carries a stated reason, and the reason goes in the commit message and the
player-facing changelog, not just someone's head. Two different bars:

- **Defect fixes** need only "this contradicts the mod's own stated convention" — the
  tier-3 `Flawless Crysteel Boots`, the value-5 `Raven_Carbideweave Cloak`, the `<stag>` typos.
  The convention tables below *are* the justification.
- **Design changes** need a reason grounded in Qud — its fiction, its existing systems, or an
  asymmetry the game already created. "It felt weak" is not a reason. Borrow the test from
  `../design-docs/DESIGN_difficulty_systems.md` §0: does the world explain it, and does it
  change a decision the player makes?

New content is *derived*, not invented: a new tier-4 halberd's stats fall out of the tier and
value curves below. That derivability is the whole reason Mura's conventions are worth keeping.

### 3. Credit, permanently

Credit is the one condition attached to the fork permission, so it is non-negotiable.

- The `docs/PERMISSION.md` §4 credit list stays intact in the Workshop description, the README, and
  release notes — **Noble Lark named explicitly**, as Mura asked.
- **Keep the `Raven_` blueprint prefix.** It's Mura's signature in the namespace. Renaming it
  would erase attribution from the one place every future contributor actually reads.
- **Every outside contribution is credited by name**, in the README and the Workshop description,
  in the same pull request that merges it. Not "later" — a contributor who has to ask has already
  been let down, and the Workshop description is the only place most players will ever look.
  Their own section, kept separate from the `docs/PERMISSION.md` §4 list, which stays intact.

### 4. Friendly but rigorous DX

- **No workarounds, no bandaids.** Fix causes. If a correct fix is out of scope right now,
  write the issue and leave the defect — don't paper it.
- **No build step.** `mod/` is loaded directly by the game. Keep it that way; it's why anyone
  can contribute without a toolchain.
- **Validation is one command, and it fails loudly.** Grow the checks under "Validating changes"
  into a real script rather than a heredoc pasted out of a doc — the `mod/Skills.xml` bug survived
  years precisely because nothing ran automatically.
- Issue → branch → small PR → squash merge, per the global workflow rules.

### 5. Safety

Qud mods run with **full process privileges**, and any `mod/Scripting/` directory triggers a
mod-approval prompt for every subscriber. That is a trust relationship; treat it as one.

- **Prefer XML to C#.** Every feature achievable in data should be data. Less code is both safer
  and more patch-durable.

**Never — these do not move:**

- file I/O outside the mod's own directory
- network access of any kind, or telemetry
- reading player files or the environment
- shelling out, or loading external assemblies
- **Harmony.** Freehold recommend it as a last resort; it also breaks on arm64 macOS
  (`../design-docs/API_VERIFICATION.md` §1). Every hook these designs need exists as a `MinEvent`.
- **reflection into game internals.** Public members and documented extension points only.

**What the mod's C# does, as of 2.3.0.** The rule used to name 36 one-line
`ModImprovedMutationBase<T>` subclasses as the ceiling — no I/O, no reflection, no state. It now
also:

- reads its own options and writes public fields on records the game has already loaded
  (`GenotypeEntry.MutationPoints`, `.Skills`, `.Reputations`)
- registers a `[Serializable]` `IGameSystem` that handles a zone event and creates and destroys
  objects within one zone

**That ceiling was raised deliberately in #46, not crossed by drift** — which is the failure this
rule exists to prevent. The hard limits above are unchanged; what changed is that C# may now hold
state and adjust already-loaded data in response to a player's choice.

**Both limits above are now checked, not just written down.** `tools/validate_mod.py` runs
`scripting-policy` (every banned API in rule 5's list, with the clause each pattern enforces) and
`serializable-shape` (any instance field on a `[Serializable]` type, which is what makes a class's
layout part of every save). Comments are stripped first, since the scripts legitimately name these
APIs; string literals are not, because `Type.GetType("System.IO.File")` is how a token scan gets
sidestepped.

**CodeQL does not cover the C#, and cannot.** Every non-`System` dependency is `XRL.*`, which
lives only in Freehold's 12 MB `Assembly-CSharp.dll` — proprietary, absent from NuGet and from CI
runners — so with build-mode `none` call-target resolution sat at 82% against an 85% threshold,
permanently. `autobuild` and `manual` both need something to build, and there is deliberately no
`.csproj` (rule 4). C# was removed from the repo's CodeQL languages; `actions` and `python` still
run. This is not a downgrade: CodeQL's generic queries could never express "no Harmony, no
reflection, no shelling out" — that is a project policy, and the two checks above enforce it
directly.

**Two obligations that come with holding state:**

- **Anything `[Serializable]` is written into player saves.** Its field layout is an identifier in
  the sense of `docs/STYLEGUIDE.md` §1 — renaming or removing a field can break saves that already
  exist. Treat a shipped system's shape as frozen unless you mean to break it.
- **Anything that mutates loaded game data must be idempotent and reversible.** Option handlers run
  repeatedly and in any order, so make the data *match* the option's value rather than performing a
  one-way edit. Where that is impossible — the Joppa building, which cannot be rebuilt once
  removed — say so in the option's `<helptext>` rather than letting the player discover it.

### 6. Configurable — players choose what they take

Nobody should have to swallow the whole mod to get one part of it.

> **Defaults reproduce the mod's established behaviour. Options let players opt out.**
> "Off by default" applies to genuinely *new* opinions this fork introduces — not to what the mod
> already is.

This fork **continues** an existing mod rather than starting one. Someone subscribing to Qud
Expanded Community Edition is asking for Caves of Qud Expanded, so shipping it inert would be a
surprising reading of "players choose" — a mod that fails to arrive is not a configurable mod.

The exception is a change that **grants power with no content attached**. Those stay off by
default even though they predate the fork; the starting reputation bonuses are the current
example. The test is whether turning the option on gives the player something to *use* or merely
something to *have*.

Settled in #45. Every `Default=` value follows from this.

Qud ships a real mod-options menu and it is the primary mechanism. Two halves, verified against
the mods installed on this machine (`~/Library/Application Support/Steam/steamapps/workshop/
content/333640/`):

- **Declaring options is pure XML.** A file with `Option` in its name, root `<options>`, one
  `<option ID= DisplayText= Category="Mods" Type="Checkbox|Slider|Combo|BigCombo|Button"
  Default= SearchKeywords=>` each, with a `<helptext>` child. `Category="Mods"` is what files it
  into the in-game menu. No code needed to make an option *appear*.
- **Reading an option requires C#.** Of the 12 installed mods shipping an `Options.xml`, **all 12
  also ship at least one `.cs`**. The working pattern is `[HasOptionFlagUpdate]` on the class,
  `[OptionFlagUpdate]` on a `static void` method, and `XRL.UI.Options.GetOption(ID, default)`
  inside it — **every option value is a string**, sliders included, so numbers need parsing.
  `[OptionFlag]` field binding also exists, and `../design-docs/DESIGN_sleep.md` §7 recommends it
  over `GetOption` — but **zero of the 87 installed mods use it and 17 use `GetOption`**. Prefer
  the pattern with evidence behind it.

**Content is gateable too.**

Blueprints and tables are read from XML at load, but the **loaded result stays mutable**.
`PopulationManager.Populations` is a live `Dictionary<string, PopulationInfo>`; installed mods
add and remove entries in it at runtime (see `1756765609/fishvendorhotloader.cs`). Parts can
likewise be added and removed from objects through events. So an option can gate drops, spawns,
recipes, and behaviour — the XML defines the content, and C# decides at runtime whether it
participates.

What resists a *live* toggle is the narrower set of things consumed once, at a moment that has
already passed by the time the player flips the switch:

| Gate this | How |
|---|---|
| Loot/spawn participation, formulas, abilities, item behaviour | Option read at runtime. Fully live. |
| Genotypes, subtypes, skill-tree edits | Read at chargen. Option must be set **before starting a character**; say so in the `<helptext>`. |
| Anatomy (the `Chip Interface` slot), the Joppa map patch | Baked into save state on creation. Realistically restart- or new-game-scoped. |

Design consequence: **prefer designs whose off-switch is a runtime decision** rather than a
load-time one. A chip family that can be dropped from the loot tables is more configurable than
one welded into chargen, and that should influence how new content is built.

### One mod, not a constellation

**This mod stays self-contained.** It is the vehicle for this fork's features, including new ones,
and the player experience it targets is *one subscription* — not assembling the intended game from
eighty separate Workshop items.

That makes **options the mechanism**, and splitting a last resort rather than a peer choice.
Where a feature cannot be option-gated, the answer is to ship it on with that stated in the
description — not to exile it to a sub-mod.

A split is justified only when a system is genuinely a different mod: a different audience, a
different maintenance cadence, or a dependency the core should not carry. Mura's Grand Bazaar and
Experience Curve Beta were split that way and remain separate for now (`../qud-expanded-bazaar`,
`../qud-expanded-experience`); the fork permission explicitly covers them, so absorbing them later
is allowed if it ever serves players better than a separate subscription.

Cross-mod dependencies, if ever needed, use `LoadBefore` / `LoadAfter` in `manifest.json` —
`LoadOrder` is deprecated as of build 210.

### The obligation that comes with staying self-contained

A growing single mod becomes take-it-or-leave-it unless the off-switches keep pace. So:

> **Every new feature ships with its option in the same PR.**

Not "options later". Retrofitting a toggle onto a shipped feature means deciding its default after
players already have expectations, and it is the exact debt this fork spent its first release
paying down.

Note this rule spends a little of rule 5's budget: gating content means more C#, not less. The
mod already ships `mod/Scripting/`, so the subscriber approval prompt is **already paid for**, and
option-reading plus table adjustment stays well inside rule 5's limits — no I/O, no network, no
reflection. It licenses nothing beyond that.

## Release blockers — all five cleared

Five items were identified at the start of the fork as blocking a first release. **All five are
now closed.** The list is kept as a record rather than a queue, because each was a real upstream
defect and the shape of each is worth not reintroducing. **The mod loads and plays on current
Qud** — none of this was ever about getting it to run.

| What it was | Where it landed |
|---|---|
| `mod/workshop.json` carried `"WorkshopId": 1134036260` — Mura's item — plus their pre-handoff description asking that the mod not be forked | `WorkshopId` cleared to `0` so the uploader creates a **new** item; `Title`, `Description` and `ImagePath` now describe this fork and carry the `docs/PERMISSION.md` §4 credits (#2) |
| `Artifact 3`–`8` were full table replacements, not merges | All six merge, each contributing one `Raven_Chips Tier N` entry (#3, fixed in #34). See `docs/FEATURES.md` §7.3 |
| `mod/Skills.xml` failed a strict XML parse — a duplicate `Tile` attribute on Berserk! | Cosmetic, and settled before the fix: Qud's loader tolerated it, so §4's skill changes had been shipping all along. Attribute removed (#5) |
| 72 of 144 psionic chips could not drop | `Raven_Chips Tier 1/2/3` now hold 48 entries each (#6, fixed in #36) |
| Nine armor pieces and `Raven_Iron Maceth` were unobtainable — no drop entry, no tinker recipe | All reachable; `tools/validate_mod.py` reports **0** known inherited defects (#7, fixed in #38) |

Remaining work lives in the issue tracker. `docs/FEATURES.md` §10 is still the severity-ranked
backlog, with a file and line on every open row.

## Conventions to preserve

Mura was consistent. Match these when adding anything.

- **Blueprint prefix `Raven_`** on every new object. Merges into vanilla objects use the vanilla
  name with `Load="Merge"` and no prefix. **No exceptions remain:** `SteelFist` and the 18
  `Projectile*` objects were the last, renamed in #66 before the save window closed; the
  Recoilers turned out to be vanilla objects the mod was replacing, fixed in #29. The only
  unprefixed new objects left are `TrueKin` and `PsionicAdept`, which are body objects following
  vanilla's own `BodyObject` convention (#13).
- **Tier → material:** 0 bronze · 1 iron · 2 steel · 3 carbide · 4 folded carbide · 5 fullerite ·
  6 crysteel · 7 flawless crysteel · 8 zetachrome.
- **Value curve doubles per tier:** 5 · 10 · 20 · 40 · 80 · 160 · 320 · 640 · 1280. Body armor
  runs 8→2048; vambraces run 4→1024 (half curve, partial slot).
- **Two-handed variants** get `PenBonus="1"` and a damage bump over the one-handed version, plus
  `UsesTwoSlots="true"`.
- **Agility-scaling martials** are a deliberate theme: vinereapers, halberds, rapiers, katanas,
  war hammers all use `Stat="Agility"` while keeping their tree's skill.
- **Vibro weapons:** tier 5, value 300, `ChargeUse="100"`, bits `0015`,
  `Mods="AxeMods,BladeMods,WeaponMods,CommonMods,ElectronicsMods"`.
- **Prefer `Load="Merge"`** over redeclaring a vanilla object. The Artifact tables were the one
  place this was violated; they were converted to merges in #34, and `tools/validate_mod.py`'s
  `merge-discipline` check now holds the line. Don't add new violations for it to catch.

## Naming decision — settled

The slot is **"Chip Interface"**, and the anatomy/body object is **`PsionicAdept`** (#13).

The original shipped a slot called `Chipset Interface` while all of Mura's player-facing
documentation called it the "Psionic Interface". Neither was accurate: the slot takes 108 chips
against 36 chipsets, and 13 of the 36 mutations the chips grant are *physical* rather than mental.
"Chip Interface" is true of the whole catalogue, matches the technological fiction in the chips'
own description, and doesn't imply the slot belongs to the Psionic Adept genotype — it is merged
into base `Humanoid`, so every humanoid has one.

`PsionicAdept` follows the convention `Genotypes.xml` already sets: the True Kin genotype
("True Kin") points at a body object and anatomy named `TrueKin` — the display name with spaces
removed.

**Use these names in all new player-facing text.** Mura's original docs in `docs/` predate the
decision and are left as historical record.

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

## Things not to break

- **Credit is the one condition of the fork permission.** Mura named **Noble Lark** explicitly for
  the subtype sprites. Keep the credits list in `docs/PERMISSION.md` §4 intact in the Workshop
  description and any README.
- `mod/ObjectBlueprints/Ammo.xml` is **entirely commented out** (62 objects, "removed temporarily"). Don't delete it —
  it's the largest block of ready-made content available, including vibro bullets/shells and a
  reworked shotgun shell. Reviving it is a good early win.
- Four vibro weapons are commented out in `mod/ObjectBlueprints/MeleeWeapons.xml` with "rework these or remove them".
- The `Chip Interface` slot is merged into the base `Humanoid` anatomy, so **every humanoid NPC
  in the game has one**. Nothing populates it today. Be deliberate if you ever change that — it
  would affect the entire world at once. Option-gated as of #81 — and note `Humanoid` is shared by
  NPCs *and* by a Mutated Human player (vanilla's genotype is `BodyObject="Humanoid"`), so the two
  cannot be separated by editing that anatomy alone. `Raven_ChipSlotPlayerMutator` exists solely to
  correct the player when the two options disagree.

## Repo state

Under git as of 2026-08-15, with a deliberate two-commit baseline:

| Commit | Contents |
|---|---|
| `971d97e` — tag **`upstream-2.2`** | Pristine upstream 2.2, 76 files, unmodified |
| `da753b7` | This fork's docs — `FEATURES.md`, `PERMISSION.md`, `CLAUDE.md`, `.gitignore` (later moved to `docs/`) |

So `git diff upstream-2.2` shows exactly what the fork has changed, forever. Keep that true:
never amend or rewrite the baseline commit.

The remote is [`vixygrey/qud-expanded-community-edition`](https://github.com/vixygrey/qud-expanded-community-edition),
with issues and CI both in use.

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

## Lessons learned

Operational traps hit during this fork, kept so nobody pays for them twice. Add to this whenever
something bites — the reasoning is the durable artifact, not the fix.

### Read the crash *type* before forming a hypothesis

A Qud crash report's exception type narrows the search enormously, and it is free:

- `EXC_BAD_ACCESS` in the **Stack Guard** region with `RECURSION LEVEL n` markers is a **stack
  overflow** — unbounded recursion inside the game, not an exception thrown by mod code. A
  handler that calls two functions and returns cannot produce it.
- A managed exception appears in `game_log.txt` with a stack trace instead, and names the type.

The options-menu crash was chased through two wrong hypotheses before the report was read
properly. The recursion markers pointed at the game's own UI, which immediately made "my C# threw
something" the wrong tree.

Note the crash report lives in macOS's crash reporter, **not** in Qud's own logs — `game_log.txt`
had four lines because the process died before logging started.

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

### Stacked PRs do not survive a squash merge of their base

Squash-merging PR A **and deleting its branch** does not retarget PR B stacked on it — GitHub
**auto-closes B**. After B's branch is rebased, `gh pr reopen` then fails outright
(*"Could not open the pull request"*) and `--base` cannot be changed on a closed PR. The only
recovery is a fresh PR.

The cause is that a squash merge creates a commit that is not an ancestor of B, so B's history no
longer descends from `main`.

**Do instead:** retarget the child to `main` *before* merging the base, or merge the base without
deleting its branch. Recover with
`git rebase --onto origin/main <old-base-tip> <child-branch>` — and capture `<old-base-tip>`
*before* merging, because it is painful to find afterwards. Better still, avoid stacking when the
base will merge soon.

### Squash merging invalidates blame-ignore SHAs

`.git-blame-ignore-revs` must list the **squash commit on `main`**, not the commit from the
feature branch — squash merging replaces the branch SHA, so an entry written before merge points
at a commit that does not exist in history and is silently ignored.

Consequence: **an entry can only be added after its PR merges**, in a follow-up. And because the
squash collapses a whole PR into one commit, a PR containing a mechanical change plus anything
else produces a squash commit that is not purely mechanical. If a change is meant to be
blame-ignored, give it its own PR.

Verify with `git merge-base --is-ancestor <sha> HEAD` — a listed SHA that fails this check is
doing nothing.

### Normalisation rules need explicit exemptions for preserved documents

`* text=auto eol=lf` in `.gitattributes` reaches Mura's original documents too, which are a
provenance record meant to stay byte-for-byte. They need `-text` to opt out of EOL conversion
entirely. Check with `git ls-files --eol` and `git add --renormalize`, not by reading the
attribute file — `git check-attr` reports an inherited `eol` value even where it does not apply.

### The game ships its own API documentation

`CoQ.app/Contents/Resources/Data/Managed/Assembly-CSharp.xml` — **898 documented members** with
summaries, including the full `QudGameBootModule.BOOTEVENT_*` lifecycle and the
`AbstractEmbarkBuilderModule` chargen surface. This is better than metadata analysis and was not
being used; `../design-docs/API_VERIFICATION.md` was written without it.

Equally useful is what it *omits*: `GenotypeFactory`, `SkillFactory` and `MutationPoints` are
absent, which is a real signal about what is and is not a supported extension point.

### For "does this API exist", read the DLL metadata, not the XML docs

`Assembly-CSharp.xml` documents **some** members. `GenotypeFactory`, `SkillFactory` and
`MutationPoints` appear in none of it — and all three exist, public, in the assembly. Absence from
the documentation was briefly mistaken for absence from the API, which nearly redirected an entire
design toward sub-mod splits it did not need.

The metadata reader is `../lore-expansion/tools/metadata/cli_meta.py`; point its `DLL` constant at
`CoQ.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll` (it ships with a path from another
machine). 7,837 types, with field and method names, signatures and visibility flags.

### The vanilla game data is readable — check it

`~/Library/Application Support/Steam/steamapps/common/Caves of Qud/CoQ.app/Contents/Resources/Data/StreamingAssets/Base`

30 XML files plus `ObjectBlueprints/`. **Not** `CoQ_Data/StreamingAssets`, which holds only DLC —
that wrong turn caused several questions to be reported as unanswerable when they weren't.

Two gotchas when reading it:

- **Five vanilla files are not well-formed XML.** `Items.xml`, `Creatures.xml`, `Furniture.xml`,
  `Books.xml` and `Manual.xml` embed control characters as numeric references (`&#11;`, `&#15;`,
  `&#27;`, `&#x7;`) which Qud accepts and XML 1.0 forbids. A strict parser rejects them.
- **Never swallow those failures.** Skipping `Items.xml` silently makes every object it defines
  look absent — which surfaced as *208 phantom "orphaned merge" defects* before the parse errors
  were surfaced. `tools/check_vanilla_drift.py` strips the invalid refs and reports anything it
  still cannot read.

### Verify Qud's behaviour against installed mods, not from memory

Several confident-sounding assumptions about Qud were wrong and were caught only by checking the
~87 mods installed under `~/Library/Application Support/Steam/steamapps/workshop/content/333640/`:

- Mod options **can** gate content. `PopulationManager.Populations` stays mutable at runtime, so
  drops and behaviour are option-gateable; only chargen- and save-baked definitions are not.
- The loader dispatches on **root element**, not filename — so XML filenames are free.
- Dev files **do** ship to subscribers.

That directory is the cheapest ground truth available. Use it before asserting how Qud behaves.

### Distinguish "frozen by saves" from "frozen by vanilla identity"

They look alike and behave completely differently. Renaming a vanilla blueprint or population
table doesn't break a save — it silently orphans the `Load="Merge"` so the edit stops applying,
with **no error anywhere**. See `docs/STYLEGUIDE.md` §1.

### A generator must never read the file it writes

`tools/build_preview.sh` was first written to read `mod/preview.png`, composite the fork's marks
onto it, and write back to the same path. That is correct exactly once. `mod/preview.png` is now
the *composited* result, so the second run would have layered `- CE` and `& VixyGrey` on top of
marks that were already there.

The fix: keep the pristine input as its own committed file — `tools/preview-base.png`, Mura's
original, verified byte-identical to `git show upstream-2.2:preview.png` — and generate from that.

Two things make this worth remembering rather than filing under "obvious":

- **It fails plausibly, not loudly.** A double-composited image isn't corrupt and doesn't error.
  It renders, and a binary diff tells you nothing. Same silent-failure class as an orphaned
  `Load="Merge"`.
- **The general form is broader than images.** Any generator whose output overwrites its own input
  has stopped being idempotent — it applies to anything that appends, wraps, or composites. The
  same reasoning is why charter rule 5 requires option handlers to make data *match* the option's
  value rather than performing a one-way edit.

Two habits that catch it: make the check `regenerate → diff against the committed artefact` part
of finishing the work (`tools/build_preview.sh` reproduces `mod/preview.png` byte-for-byte, and a
second run proves it), and **guard the input's identity** rather than trusting it — the script
refuses to run unless the base is 418×312, because every offset is measured against that logo and
a swapped base would misplace the marks instead of erroring.

### A gate is only evidence about the property it checks

Reformatting the XML in #78 produced output that `tools/validate_mod.py`,
`tools/check_vanilla_drift.py` **and** `npx prettier --check` all passed — while prettier had
reflowed the text inside `<helptext>` in `Options.xml`, inserting a newline mid-sentence into a
string Qud renders in its options menu.

None of those three gates was broken. None of them looks at whether text *content* survived, so all
three were honestly green and collectively meaningless for that question. Three passing checks felt
like three pieces of evidence and were zero.

It surfaced by comparing the **parsed element tree** of every file before and after — tags,
attributes, stripped text — which found 18 of 19 files identical and one not. That is exactly the
ratio that gets waved through on a 2,500-line diff.

This is the general form of two things already recorded below in their specific cases: an orphaned
`Load="Merge"` applies nothing with no error, and a renamed vanilla blueprint breaks no save while
silently ceasing to merge. Stated generally:

> **Before trusting a green run, ask which property each check actually inspects.** A change that
> rewrites content wholesale needs a comparison of a *parsed* representation — the AST for Python,
> the element tree for XML — not a reading of the diff and not the checks that happen to exist.

The same trap catches *manual* verification, where there is no green run to be suspicious of. The
repo's wiki was disabled in #102 after confirming it had never been created — a true answer,
correctly obtained, to the wrong question. **"Never used" is evidence about the past, not about
intent**, and an unwanted feature and a not-yet-wanted one are identical from the API; the wiki was
wanted, for documenting the mod's mechanics, and had to be turned back on (#106). Before acting on a
check, confirm it answers the question you are actually deciding — and where the real question is
intent, no command answers it. Ask.

It is also why `serializable-shape` and `subtype-tile` were written: each exists because nothing
else was looking at that property, and "nothing was looking" is not the same as "nothing is wrong".

### `git checkout <file>` restores from the index, not from HEAD

While testing a new check in #80, `git checkout mod/Subtypes.xml` — used to undo a deliberately
broken probe — also silently reverted the real fix in that file, because the fix had never been
staged. The validator caught it moments later, but the command itself gave no sign it had discarded
work.

Stage before using checkout to undo scratch edits in a file you are also legitimately changing, or
keep the probe in a different file entirely.

### Discovery attributes fail by doing nothing

`[PlayerMutator]` is the marker Qud scans for. A class implementing `IPlayerMutator` **without** it
compiles, ships, and is simply never called — no exception, no log line, just a feature that does
not happen. Measured: 11 of the installed mods implementing that interface carry the attribute.

Generalises to every attribute-driven extension point in the game, `[HasOptionFlagUpdate]` and
`[OptionFlagUpdate]` included. **The failure mode for a missing registration marker is silence**, so
check the marker against a working installed mod rather than assuming the interface is sufficient.

### A public field is not a supported setter if something caches what it derives

`PowerEntry.Attribute` and `.Minimum` are public and writable, so retuning a skill requirement at
runtime looks trivial. It is not. `MeetsAttributeMinimum` gates on a **cached** `_requirements`
list; `InitRequirements()` opens by returning early when that cache already exists; and the cache is
private, so reaching it would need reflection, which charter rule 5 forbids outright. Once anything
has rendered or checked that power, writing the field is **inert, with no error**.

What saved the feature is that `HandleXMLNode` never primes the cache — it is null after load, so
the value written at boot is the one the cache is eventually built from. That makes the
`Restart="true"` option in #91 correct and honest. It would not have supported a live one, and
shipping it as live would have produced an option that silently did nothing for anyone who happened
to open the skills screen first.

> **Before designing an option around writing a public field, find who *reads* it.** If a cache sits
> between the field and the behaviour, the option's scope is set by the cache's lifetime, not by how
> live the field looks.

This is why #91 became two options rather than one. `Cost` is a plain int that `Render` and purchase
read directly, so costs are genuinely live; requirements are not, and one toggle covering both would
have had to describe itself dishonestly. **The scopes are a property of the game, not a design
choice** — `docs/FEATURES.md` §13.2 tabulates all three (live / restart / new character).

Same silent-failure family as an orphaned `Load="Merge"` and a missing `[PlayerMutator]`.

### Read the IL when the metadata and the XML docs run out

The two lessons above say to check `Assembly-CSharp.xml` for documentation and the metadata reader
for structure. Neither can answer *"does this method rebuild, append, or return early"* — and that
question decided the design above. Method bodies can answer it, and reading them needs **no
decompiler**: the metadata reader already yields each method's RVA.

- Header: `b & 3 == 2` means tiny format, one byte, code length `b >> 2`. Otherwise fat — 12-byte
  header with the code size at offset 4.
- Then scan opcodes. Token-bearing ones (`ldfld` `0x7b`, `stfld` `0x7d`, `call` `0x28`,
  `newobj` `0x73`) carry a 4-byte metadata token whose high byte is the table and low three the RID,
  so a field or method name can be resolved straight out of the tables.

**Do not scan for tokens alone.** A token-only pass over `InitRequirements` showed `ldfld` → `newobj`
→ `stfld` and read as a clean rebuild — exactly backwards, because it had dropped the branch between
them. The opening bytes settled it: `02 7b … 3a d4 00 00 00` is `ldarg.0; ldfld _requirements;
brtrue → ret`, a guard rather than a rebuild.

Worth the twenty minutes because the wrong answer ships a silently inert option, and because the
alternative was a round trip through the maintainer's machine.

### GitHub does not re-run pull request checks on a retitle

`on: pull_request` with no `types:` means `opened`, `synchronize`, `reopened`. A job reading
`github.event.pull_request.title` therefore **cannot be satisfied by retitling**: the edit does not
re-trigger it, and a manual re-run replays the *original* event payload, so it still sees the old
title. The check stays red until an unrelated commit is pushed.

`.github/workflows/ci.yml` now lists `edited` explicitly. The general form: **a check that reads the
event payload must listen for the event that changes that payload**, or it is unfixable by the very
action it demands — which teaches contributors that a red check can be ignored.

### Stale prose rots silently, and the emphatic passages rot worst

Every gate this repo has inspects a *machine-readable* property. `validate_mod.py` checks XML and C#
structure, prettier checks formatting, `typos` checks spelling, CodeQL checks the Python. **Not one
of them reads a sentence and asks whether it is still true.** So documentation decays with no signal
at all — the same silent-failure shape as an orphaned `Load="Merge"`, but across every file a
contributor reads *first*.

Measured at the point the option toggles landed (#93): **all five** of the items in *Release
blockers* above were closed while that section was still titled "Immediate priorities" and written
as a queue, `docs/FEATURES.md` §7.3 still called a defect fixed months earlier in #34 the
"🔴 Biggest compatibility hazard in the mod", and §3.4's drop-rate arithmetic still read `10 / 100`,
which was only correct under the table *replacement* that #34 had removed. One of those is a wrong
number that would have been repeated as fact by anyone who trusted the doc.

**The emphasis is the tell.** A 🔴 callout, a "highest-value fix in the codebase", a numbered
priority list — these get written when a defect is freshest and most irritating, and that same
emphasis is what stops them being revisited. They read as settled background rather than as claims
under review, so the strongest statements in the repo become the least trustworthy ones. Two harms,
both charter-relevant: they point the next contributor at work already done, and they advertise a
resolved hazard in the one dimension charter rule 1 makes the fork's headline claim.

Stale **cross-references** are the same class. `CLAUDE.md`'s own commit-message example read
`closes #4` for work that actually closed #3, and nothing checks issue numbers in prose either.

> **When a PR closes a defect, grep the docs for it in the same PR.** `rg -i 'artifact 3|removetable'`
> costs seconds. The fix and the prose describing the defect are one change, not two — and the
> second half is the one no gate will ever remind you about.

## Source documents

| File | What it is |
|---|---|
| `docs/FEATURES.md` | Complete feature reference + bug checklist. Written for this fork; the authoritative doc. |
| `docs/PERMISSION.md` | Fork permission, provenance, credit obligations, pre-upload actions. |
| `docs/STYLEGUIDE.md` | Naming, layout, XML/C# formatting, Workshop requirements. Read §1 before renaming anything. |
| `docs/permission-mura-workshop-comment.png` | Screenshot evidence of the grant. |
| `docs/mura-feature-notes-wip.txt` | Mura's oldest partial list. Joppa section is stale. |
| `docs/2.2-changelog.txt` | The 2.1.1 → 2.2 delta. Only source for the physical-vs-mental chip scaling split. |

Mura also kept a pinned "Partial Feature List" discussion on the Workshop page — newest of the
three writeups, best source for the energy-cell mod formulas. Its content is folded into
`docs/FEATURES.md` §6.6 and §10. Where any of Mura's docs disagree with the XML, **the XML is what
ships** — `docs/FEATURES.md` §10 has a table of the known disagreements.
