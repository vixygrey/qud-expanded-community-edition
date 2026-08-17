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

## Source documents

| File | What it is |
|---|---|
| `docs/FEATURES.md` | Complete feature reference + bug checklist. Written for this fork; the authoritative doc. |
| `docs/LESSONS.md` | Operational traps I hit maintaining this fork — Qud internals, git and GitHub, tooling. Imported by this file. |
| `docs/PERMISSION.md` | Fork permission, provenance, credit obligations, pre-upload actions. |
| `docs/STYLEGUIDE.md` | Naming, layout, XML/C# formatting, Workshop requirements. Read §1 before renaming anything. |
| `docs/permission-mura-workshop-comment.png` | Screenshot evidence of the grant. |
| `docs/mura-feature-notes-wip.txt` | Mura's oldest partial list. Joppa section is stale. |
| `docs/2.2-changelog.txt` | The 2.1.1 → 2.2 delta. Only source for the physical-vs-mental chip scaling split. |

Mura also kept a pinned "Partial Feature List" discussion on the Workshop page — newest of the
three writeups, best source for the energy-cell mod formulas. Its content is folded into
`docs/FEATURES.md` §6.6 and §10. Where any of Mura's docs disagree with the XML, **the XML is what
ships** — `docs/FEATURES.md` §10 has a table of the known disagreements.
