# Charter


The rules I maintain this fork under, and why. `docs/STYLEGUIDE.md` is the mechanical layer beneath
this one: given these rules, what does a file get called and how is it formatted. Where the two
touch, this document wins.

---

## What this is

A community fork of **Caves of Qud Expanded** (Steam Workshop `1134036260`), originally by
**Mura** (`@mura_raven`). The fork permission is public and explicit. See `docs/PERMISSION.md`.

**`mod/` is the mod.** There is no build step: Qud loads those XML files directly, and `mod/` is
what gets packaged and uploaded to the Workshop. **Anything you put in `mod/` ships to
subscribers.** 8 of the 87 mods installed on my machine accidentally ship a `README.md`, 5 a
`LICENSE`, 4 a `.csproj`. Development tooling lives at the repo root, outside `mod/`, so it never
reaches players. Point the Workshop uploader at `mod/`, not the repo root.

```
mod/     the shipped mod          docs/    reference documentation
tools/   validation and helpers   .github/ CI
```

**Read `docs/FEATURES.md` before changing shipped content.**
It is the complete feature reference.
It covers every system, every item, 527 new blueprints, and 284 vanilla merges.
Section 10 contains the bug and fork checklist.
Read **`docs/STYLEGUIDE.md`** for naming, formatting, and Workshop requirements.
Read §1 before renaming anything.
Several conventions are load-bearing identifiers.

---

## The six rules

These rules define the fork.
Existing violations are maintenance debt, not precedent.

### 1. Compatibility is a hard constraint

Compatible with vanilla, future Qud patches, and other mods.

- **Merge, never replace.** Use `Load="Merge"` for every change to a vanilla object or table.
  A full redeclaration conflicts with other mods and discards future vanilla additions.
  The `Artifact 3`–`8` replacements (#3, fixed in #34) and the `<removetable>` chain in
  `Armor 7C/7R/8C/8R` (#4, fixed in #85) remain recorded as resolved violations.
  Do not reintroduce either pattern.
- **Prefer additive changes.** Add entries instead of removing them.
  Adjust weights instead of stripping tables.
- **State the blast radius.** The `Chip Interface` merge into base `Humanoid` reaches every
  humanoid in the game.
  State and review changes at that level.
- ✅ **Verified 2026-08-15: 2.2 loads and plays on current Qud** on a Legion Go 2 S.
  Compatibility work covers other mods and future patches.

### 2. Causality, and nothing arbitrary

Every change needs a stated reason.
Put that reason in the commit message and the player-facing changelog.

- **Defect fixes** need a contradiction with the mod's own convention.
  Examples include tier-3 `Flawless Crysteel Boots`, value-5 `Raven_Carbideweave Cloak`, and `<stag>` mix-ups.
  The convention tables in `docs/STYLEGUIDE.md` provide the justification.
- **Design changes** need a reason grounded in Qud's fiction, existing systems, or an existing asymmetry.
  “It felt weak” is not a reason.
  Ask whether the world explains the change and whether it changes a player decision.

Ask a third question after #596: **Did the player earn it?**
Faction standing must follow player actions, such as shared water, kills, and carried relics.
It must not follow from an item the player chooses to wear.
An insignia that changes faction standing turns a relationship into inventory management.
The world can explain an insignia without making the standing earned.

This rule does not block an object that records existing standing.

Derive new content from established tiers and value curves.
That derivation preserves Mura's conventions.

### 3. Credit, permanently

Credit is a permanent condition of the fork permission.

- Keep the `docs/PERMISSION.md` §4 credit list in the Workshop description, README, and release notes.
  Name **Noble Lark** explicitly.
- **Keep the `Raven_` blueprint prefix.** It preserves Mura's attribution in the namespace.
- **Credit every outside contribution by name** in the README and Workshop description in the pull request
  that merges the contribution.
  Keep those credits separate from the `docs/PERMISSION.md` §4 list.

### 4. Friendly but rigorous DX

- **Fix causes instead of adding workarounds.** Record an out-of-scope fix as an issue.
- **Keep the direct load path.** The game loads `mod/` without a build step.
- **Keep validation in the script.** Run `python3 tools/validate_mod.py`.
  Add new checks to the script instead of relying on prose.
- Use issue, branch, small PR, and squash merge in that order.

### 5. Safety

Qud mods run with **full process privileges**.
The game asks each subscriber to approve a mod with a `mod/Scripting/` directory.
Treat scripting as privileged code.

**This rule contains a hard boundary and a design preference.**
The following list defines the boundary.
The later guidance explains the preference.

**Use data when the game already provides the mechanism.**
Blueprints, tags, and population tables are Freehold's maintained mechanisms.
Equivalent C# becomes the fork's maintenance burden.
Issue #498 removed an `IGameSystem` because `manifest.json` already gated the directory.

**Use C# when a feature genuinely needs C#.**
Do not choose an inferior XML route to satisfy an artificial budget.
The hard limits concern privilege, not code volume.
Issue #589 records why this distinction matters.

**The hard limits are:**

- Do not use file I/O outside the mod directory.
- Do not use network access or telemetry.
- Do not read player files or the environment.
- Do not run shell commands or load external assemblies.
- **Do not use Harmony.** Freehold recommends it only as a last resort.
  It also fails on arm64 macOS.
  Every hook that this mod needs exists as a `MinEvent`.
- **Do not use reflection into game internals.** Use public members and documented extension points.

**What the mod's C# does.**
The original ceiling named 36 one-line `ModImprovedMutationBase<T>` subclasses.
The current code also:

- reads options and writes public fields on loaded records
  (`GenotypeEntry.MutationPoints`, `.Skills`, `.Reputations`, `NameElement.Weight`,
  `NameScope.Chance`, `Gender.EnableSelection`)
- registers an `AbstractEmbarkBuilderModule` in `mod/Core/EmbarkModules.xml`
  to replace the generated player name during character creation
- declares a `BaseDefaultEquipmentMutation` in `mod/Core/Mutations.xml`
  to grow a natural weapon and track its rank

**The ceiling changed three times by deliberate decision.**
Issue #46 allowed C# to hold state and adjust loaded data after a player choice.
The embark module required separate review because it runs during character creation.
It stays within the hard limits.
`AbstractEmbarkBuilderModule` declares no abstract members.
The subclass overrides one public virtual method.
The game instantiates it from a class name in XML.
It declares no module data because `AbstractEmbarkBuilderModuleData` is `[Serializable]`
and travels in build codes.

Harmony was not an alternative because rule 5 forbids it.
The question was whether the feature justified a new C# form.

**The third change was the mutation class (#589).**
Every `<mutation>` node names a `Class` that the game resolves as
`"XRL.World.Parts.Mutation." + Class`.
The mutation cannot be declared in data.
The issue assumed that `Class` could point to vanilla's `Horns`.
That choice would collide with vanilla's entry for every player.
Two entries sharing a class collide, and the entry with the first display name wins.
The correct choice was a new mutation class or no mutation.
The 36 existing subclasses only improve vanilla mutations.

The mutation class passed the same safety test as the embark module.
The game instantiates it from a class name in XML.
It declares no instance fields, so it adds no save data.
It inherits a base that Freehold designed for extension.
`docs/LESSONS.md` records why `Horns` cannot be extended.

**The ceiling also came down once.**
Issue #498 removed a `[Serializable]` `IGameSystem` that handled a zone event and created or
destroyed objects in one zone.
`manifest.json` already gates the directory on the option.
The system and its extra ceiling were removed.

**CodeQL does not cover the C#.**
Every non-`System` dependency is `XRL.*` in Freehold's proprietary 12 MB `Assembly-CSharp.dll`.
The assembly is absent from NuGet and CI runners.
With build-mode `none`, call-target resolution reached 82% against an 85% threshold.
The `autobuild` and `manual` modes both need a build target.
The repository has no `.csproj` under rule 4.
CodeQL still runs for `actions` and `python`.
The project checks enforce the policy directly.

**State creates two obligations:**

- **`[Serializable]` data enters player saves.**
  Its field layout is a save-compatible identifier under `docs/STYLEGUIDE.md` §1.
  Treat the shape of a shipped part or effect as frozen unless a save break is intended.
  `serializable-shape` checks every such type.
- **Loaded game data must be idempotent and reversible.**
  Option handlers can run repeatedly and in any order.
  Make data match the option value instead of applying a one-way edit.
  Document an irreversible case, such as the Chip Interface slot, in `<helptext>`.

### 6. Configurable, so players choose what they take

Nobody should have to swallow the whole mod to get one part of it.

> **Defaults reproduce the mod's established behaviour. Options let players opt out.**
> "Off by default" applies to genuinely *new* opinions this fork introduces, not to what the mod
> already is.

**An option must earn its place.**
Define the default first.
Then ask whether the option should exist.

> **Would anybody actually turn this off?**

An option earns its place where a reasonable player could want the mod *without that part*: changes
to numbers, difficulty, loot, character creation, or an opinionated system somebody might disagree
with. Flavour and immersion that changes no mechanic does not need one. A clay pot being brown
rather than grey is not a part anybody needs to refuse, and neither is a gate that shuts itself.

The cost of getting this wrong is not neutral. Every option is a line in a menu a player has to read
past to find the one they want, a `<helptext>` to keep true, an entry in the wiring check, and a
branch to carry in the code forever. Adding one to a change nobody would disable spends all of that
and buys nothing.

Two cases where the answer is yes despite the change being small: it takes something *away* that a
player might want back, or it turns off cleanly and somebody has said they want it off. The
give-artifact filter is the first, because the mark it respects is the player's, and a player who would
rather hand over a marked item should be able to.

Settled in #663, after two flavour features in one day were each given an option nobody would use.

This fork **continues** an existing mod rather than starting one. Someone subscribing to Qud
Expanded Community Edition is asking for Caves of Qud Expanded, so shipping it inert would be a
surprising reading of "players choose", because a mod that fails to arrive is not a configurable mod.

A change that grants power without content remains off by default.
The starting reputation bonus is the current example.
Ask whether the option gives the player something to use or only something to have.

Settled in #45. Every `Default=` value follows from it.

Qud provides a mod-options menu as the primary mechanism.
Verify both halves against the installed mods at
`~/Library/Application Support/Steam/steamapps/workshop/content/333640/`.

- **Declaring options is pure XML.** A file with `Option` in its name, root `<options>`, one
  `<option ID= DisplayText= Category="Mods" Type="Checkbox|Slider|Combo|BigCombo|Button"
  Default= SearchKeywords=>` each, with a `<helptext>` child. `Category="Mods"` is what files it
  into the in-game menu. No code needed to make an option *appear*.
- **Acting on an option usually requires C#.** Of the 12 installed mods shipping an `Options.xml`,
  **all 12 also ship at least one `.cs`**. The exception is gating a whole directory, which
  `manifest.json` does on its own (#498). See rule 5, where that discovery took a system out of
  this mod's C# entirely. The working pattern is `[HasOptionFlagUpdate]` on the class,
  `[OptionFlagUpdate]` on a `static void` method, and `XRL.UI.Options.GetOption(ID, default)`
  inside it, and **every option value is a string**, sliders included, so numbers need parsing.
  `[OptionFlag]` field binding also exists and is sometimes recommended over `GetOption`, but
  **zero of the 87 installed mods use it and 17 use `GetOption`**. Prefer the pattern with evidence
  behind it.

**Content is gateable too.**

Blueprints and tables load from XML.
The loaded result remains mutable.
`PopulationManager.Populations` is a live `Dictionary<string, PopulationInfo>`.
Installed mods add and remove entries at runtime.
Parts can also change through events.
The XML defines content, and C# gates drops, spawns, recipes, and behavior at runtime.

What resists a *live* toggle is the narrower set of things consumed once, at a moment that has
already passed by the time the player flips the switch:

| Gate this | How |
|---|---|
| Loot/spawn participation, formulas, abilities, item behaviour | Option read at runtime. Fully live. |
| Genotypes, subtypes, skill-tree edits | Read at chargen. Set the option **before starting a character** and state that requirement in `<helptext>`. |
| Anatomy (the `Chip Interface` slot), the Joppa map patch | Baked into save state on creation. Use restart or new-character scope. |

The design consequence: **prefer designs whose off-switch is a runtime decision** rather than a
load-time one. A chip family that can be dropped from the loot tables is more configurable than
one welded into chargen, and that should influence how new content gets built.

### One mod, not a constellation

**This mod stays self-contained.**
It carries this fork's features, including new features.
The target player experience is one subscription instead of eighty separate Workshop items.

That makes **options the mechanism**, and splitting a last resort rather than a peer choice.
Where a feature cannot be option-gated, the answer is to ship it on with that stated in the
description, not to exile it to a sub-mod.

A split is justified when a system is a different mod.
Valid reasons include a different audience, maintenance cadence, or dependency.
Mura's Grand Bazaar and Experience Curve Beta use separate subscriptions for now.
The fork permission allows later absorption when that better serves players.

Cross-mod dependencies, if ever needed, use `LoadBefore` / `LoadAfter` in `manifest.json`.
`LoadOrder` is deprecated as of build 210.

### The obligation that comes with staying self-contained

A growing single mod becomes take-it-or-leave-it unless the off-switches keep pace. So:

> **Every new feature ships with its option in the same PR.**

Do not defer options without a reason.
Retrofitting a toggle after release forces a new default on players with existing expectations.
This fork paid down that debt during its first release.

This rule pulls against rule 5's preference rather than against its limits: gating content means
more C#, not less. That is fine, and worth being explicit about, because the two rules would
otherwise look as though they disagree. The mod already ships `mod/Scripting/`, so the subscriber
approval prompt is **already paid for**, and option-reading plus table adjustment stays well inside
rule 5's hard boundary: no I/O, no network, no reflection. It licenses nothing beyond that.

---

## Release blockers, all five cleared

I identified five items at the start of the fork as blocking a first release. **All five are now
closed.** I keep the list as a record rather than a queue, because each was a real upstream defect
and the shape of each is worth not reintroducing. **The mod loads and plays on current Qud**, and none
of this was ever about getting it to run.

| What it was | Where it landed |
|---|---|
| `mod/workshop.json` carried `"WorkshopId": 1134036260`, Mura's item, and its pre-handoff description | Clear `WorkshopId` so the fork publishes as a **new** item. Update `Title`, `Description`, `ImagePath`, and the `docs/PERMISSION.md` §4 credits (#2). The placeholder `0` blocked the first upload and remains a defect (#163). |
| `Artifact 3`–`8` were full table replacements, not merges | Merge all six. Each contributes one `Raven_Chips Tier N` entry (#3, fixed in #34). See `docs/FEATURES.md` §7.3. |
| `mod/Core/Skills.xml` failed a strict XML parse on a duplicate `Tile` attribute on Berserk! | Qud tolerated the duplicate, so §4's skill changes shipped. Remove the attribute (#5). |
| 72 of 144 psionic chips could not drop | `Raven_Chips Tier 1/2/3` now hold 48 entries each (#6, fixed in #36). |
| Nine armor pieces and `Raven_Iron Maceth` were unobtainable without a drop entry or tinker recipe | All are reachable. `tools/validate_mod.py` reports **0** known inherited defects (#7, fixed in #38). |

Remaining work lives in the issue tracker. `docs/FEATURES.md` §10 is still the severity-ranked
backlog, with a file and line on every open row.

---

## Things not to break

- **Credit is the one condition of the fork permission.** Mura named **Noble Lark** explicitly for
  the subtype sprites. Keep the credits list in `docs/PERMISSION.md` §4 intact in the Workshop
  description and any README.
- `mod/ObjectBlueprints/Ammo.xml` is **entirely commented out** (62 objects, "removed temporarily").
  Do not delete it.
  It is the largest block of ready-made content available, including vibro bullets, vibro shells, and a reworked shotgun shell.
  Reviving it is an early win.
- Four vibro weapons are commented out in `mod/ObjectBlueprints/MeleeWeapons.xml` with "rework these
  or remove them".
- The `Chip Interface` slot is merged into the base `Humanoid` anatomy, so **every humanoid NPC
  in the game has one**. Nothing populates it today. Be deliberate if you ever change that, because it
  would affect the entire world at once. Option-gated as of #81, and note `Humanoid` is shared by
  NPCs *and* by a Mutated Human player (vanilla's genotype is `BodyObject="Humanoid"`), so the two
  cannot be separated by editing that anatomy alone. That is why `Raven_ChipSlotPlayerMutator`
  exists: since #353 it takes the shared slot back off the player at chargen, because a genotype
  that can mutate is not what chips are for.

---

## Repo state

Under git as of 2026-08-15, with a deliberate two-commit baseline:

| Commit | Contents |
|---|---|
| `971d97e`, tag **`upstream-2.2`** | Pristine upstream 2.2, 76 files, unmodified |
| `da753b7` | This fork's docs: `FEATURES.md`, `PERMISSION.md`, and `.gitignore` (later moved to `docs/`) |

So `git diff upstream-2.2` shows exactly what this fork has changed, forever. Keep that true:
never amend or rewrite the baseline commit.

The remote is [`vixygrey/qud-expanded-community-edition`](https://github.com/vixygrey/qud-expanded-community-edition),
with issues and CI both in use.

---

## Source documents

| File | What it is |
|---|---|
| `docs/FEATURES.md` | Complete feature reference and bug checklist. It is authoritative for this fork. |
| `docs/LESSONS.md` | Operational traps from Qud, Git, GitHub, and tooling. |
| `docs/DESIGN_options.md` | Historical design work for mod options (#45). The shipped result is in `docs/FEATURES.md` §13. |
| `docs/DESIGN_balance.md` | Balance work against vanilla (#315), verified combat mechanics, open questions, and rationale. |
| `docs/PERMISSION.md` | Fork permission, provenance, credit obligations, pre-upload actions. |
| `docs/STYLEGUIDE.md` | Naming, layout, XML/C# formatting, Workshop requirements. Read §1 before renaming anything. |
| `docs/permission-mura-workshop-comment.png` | Screenshot evidence of the grant. |
| `docs/mura-feature-notes-wip.txt` | Mura's oldest partial list. Joppa section is stale. |
| `docs/2.2-changelog.txt` | The 2.1.1 → 2.2 delta. Only source for the physical-vs-mental chip scaling split. |

Mura also kept a pinned "Partial Feature List" discussion on the Workshop page, newest of the
three writeups, and the best source for the energy-cell mod formulas. Its content is folded into
`docs/FEATURES.md` §6.6 and §10. Where any of Mura's docs disagree with the XML, **the XML is what
ships**. `docs/FEATURES.md` §10 has a table of the known disagreements.
