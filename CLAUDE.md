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
  discards future vanilla additions to it. Two standing violations: the `Artifact 3`–`8`
  replacements, and the `<removetable>` chain in `Armor 7C/7R/8C/8R` that severs tier cascade.
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
- **Never:** file I/O outside the mod's own directory, network access of any kind, telemetry,
  reading player files or environment, shelling out, or loading external assemblies.
- **No Harmony.** Freehold recommend it as a last resort; it also breaks on arm64 macOS
  (`../design-docs/API_VERIFICATION.md` §1). Every hook these designs need exists as a `MinEvent`.
- **No reflection into game internals.** Public events and documented extension points only.
- The current `mod/Scripting/` is 36 one-line `ModImprovedMutationBase<T>` subclasses — no I/O, no
  reflection, no state. **That inertness is the ceiling**, not a starting point. Any C# that
  wants more must justify itself explicitly.

### 6. Configurable — players choose what they take

Nobody should have to swallow the whole mod to get one part of it. Opinionated changes ship
**off by default**; content ships on.

Qud ships a real mod-options menu and it is the primary mechanism. Two halves, verified against
the mods installed on this machine (`~/Library/Application Support/Steam/steamapps/workshop/
content/333640/`):

- **Declaring options is pure XML.** A file with `Option` in its name, root `<options>`, one
  `<option ID= DisplayText= Category="Mods" Type="Checkbox|Slider|Combo|BigCombo|Button"
  Default= SearchKeywords=>` each, with a `<helptext>` child. `Category="Mods"` is what files it
  into the in-game menu. No code needed to make an option *appear*.
- **Reading an option requires C#** — `[OptionFlag]` on a field in a `[HasOptionFlagUpdate]`
  class, with an `[OptionFlagUpdate]` method to react to changes. Empirically firm: of the 12
  installed mods shipping an `Options.xml`, **all 12 also ship at least one `.cs`**.

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

### Modularity is the complement, not the substitute

Splitting still earns its place — for keeping an optional system's C# out of the core mod
entirely, and because each piece can then be updated or break without taking the rest down.
Mura already worked this way: Grand Bazaar and Experience Curve Beta ship as separate sub-mods
(both present at `../qud-expanded-bazaar` and `../qud-expanded-experience`), and
`../design-docs/DESIGN_difficulty.md` §1 argues the same case independently.

Use **options** for choices within a system, and **a split** when a whole system is a separate
opinion. Cross-mod dependencies use `LoadBefore` / `LoadAfter` in `manifest.json` — `LoadOrder`
is deprecated as of build 210.

Note this rule spends a little of rule 5's budget: gating content means more C#, not less. The
mod already ships `mod/Scripting/`, so the subscriber approval prompt is **already paid for**, and
option-reading plus table adjustment stays well inside rule 5's limits — no I/O, no network, no
reflection. It licenses nothing beyond that.

## Immediate priorities

These are the things blocking a first release, in order. **The mod loads and plays on current
Qud** — none of this is about getting it to run.

1. **`mod/workshop.json` still has `"WorkshopId": 1134036260`** — Mura's item. This fork releases
   *separately*, so that field must be cleared or the uploader targets their page. `Description`
   also holds Mura's pre-handoff text (which asks that the mod *not* be forked); `Title` and
   `ImagePath` need updating too. Upload blocker and a charter-rule-3 obligation at once.
2. **`Artifact 3`–`Artifact 8` are full table replacements, not merges.** The mod's worst
   compatibility defect: conflicts with any other mod touching those tables, and silently
   discards future vanilla additions to them. Charter rule 1 makes this the highest-value fix in
   the codebase. See `docs/FEATURES.md` §7.3. Same class of problem, smaller: the `<removetable>`
   chain in `Armor 7C/7R/8C/8R`.
3. **`mod/Skills.xml` is not well-formed** — line 10 has a duplicate `Tile` attribute on Berserk!.
   It is the only file in the mod that fails a strict XML parse. Since the mod otherwise plays
   fine, Qud's loader is either tolerating it or dropping this one file silently; Qud loads files
   independently, so both are consistent with what we see. **Determine which before fixing** —
   check `Player.log` for a load error, and test in-game whether an Agility-primary character can
   actually buy Axe → Cleave. That answer tells you whether §4's skill changes have ever shipped.
4. **72 of 144 psionic chips can't drop.** `Raven_Chips Tier 1/2/3` only list the first chip of
   each family plus its chipset (24 entries where 48 are needed). Chips B and C of all 12
   families are in no table and have no `TinkerItem`. See `docs/FEATURES.md` §3.3.
5. **Nine armor pieces are unobtainable** — the four nanoweave, four flexi, and the mutating mask
   have no drop entry and no tinker recipe. Plus `Raven_Iron Maceth`. See §7.2.

Lower-priority items (value typos, tier typos, the `<stag>` bug, the Akimbo class collision) are
in `docs/FEATURES.md` §10, severity-ranked with file and line.

## Conventions to preserve

Mura was consistent. Match these when adding anything.

- **Blueprint prefix `Raven_`** on every new object. Merges into vanilla objects use the vanilla
  name with `Load="Merge"` and no prefix. (A handful of new objects break this — `SteelFist`,
  `Programmable Recoiler`, the `Projectile*` objects — but the prefix is the rule.)
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
- **Prefer `Load="Merge"`** over redeclaring a vanilla object. The Artifact tables are the one
  place this was violated, and it's the mod's worst compatibility problem — don't add more.

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
  would affect the entire world at once.

## Repo state

Under git as of 2026-08-15, with a deliberate two-commit baseline:

| Commit | Contents |
|---|---|
| `971d97e` — tag **`upstream-2.2`** | Pristine upstream 2.2, 76 files, unmodified |
| `da753b7` | This fork's docs — `FEATURES.md`, `PERMISSION.md`, `CLAUDE.md`, `.gitignore` (later moved to `docs/`) |

So `git diff upstream-2.2` shows exactly what the fork has changed, forever. Keep that true:
never amend or rewrite the baseline commit. No remote is configured yet.

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
  Example: `fix(tables): merge Artifact 3-8 instead of replacing (closes #4)`.
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
- Run the validation script before every commit. It is the only automated gate that exists.

> ⚠️ **Bootstrapping gap: there is no remote and no issue tracker yet.** "Issues first" cannot
> start until a GitHub repo exists. Creating it is the first chore.

## Lessons learned

Operational traps hit during this fork, kept so nobody pays for them twice. Add to this whenever
something bites — the reasoning is the durable artifact, not the fix.

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
