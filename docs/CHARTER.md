# Charter

The rules I maintain this fork under, and why. `docs/STYLEGUIDE.md` is the mechanical layer beneath
this one — given these rules, what does a file get called and how is it formatted. Where the two
touch, this document wins.

---

## What this is

A community fork of **Caves of Qud Expanded** (Steam Workshop `1134036260`), originally by
**Mura** (`@mura_raven`). The fork permission is public and explicit — see `docs/PERMISSION.md`.

**`mod/` is the mod.** There is no build step: Qud loads those XML files directly, and `mod/` is
what gets packaged and uploaded to the Workshop. **Anything you put in `mod/` ships to
subscribers** — 8 of the 87 mods installed on my machine accidentally ship a `README.md`, 5 a
`LICENSE`, 4 a `.csproj`. Development tooling lives at the repo root, outside `mod/`, so it never
reaches players. Point the Workshop uploader at `mod/`, not the repo root.

```
mod/     the shipped mod          docs/    reference documentation
tools/   validation and helpers   .github/ CI
```

**Read `docs/FEATURES.md` before touching anything.** It's the complete reference for what the mod
does — every system, every item, all 472 new blueprints and 228 vanilla merges, which I
reconstructed from the source because no complete list had ever existed. Section 10 is the bug and
fork checklist. **`docs/STYLEGUIDE.md`** covers naming, formatting, and Workshop requirements — read
§1 before renaming anything, because several conventions that look like mess are load-bearing
identifiers.

---

## The six rules

I set these at the start of the fork. They're constraints rather than aspirations — where existing
content violates one, that's debt to pay down, not precedent.

### 1. Compatibility is a hard constraint

Compatible with vanilla, with future Qud patches, and with other mods. In practice:

- **Merge, never replace.** `Load="Merge"` on every touch of a vanilla object or table. A full
  redeclaration both conflicts with any other mod touching the same record *and* silently
  discards future vanilla additions to it. **The two inherited violations are now paid off** —
  the `Artifact 3`–`8` replacements (#3, fixed in #34) and the `<removetable>` chain in
  `Armor 7C/7R/8C/8R` that severed the tier cascade (#4, fixed in #85). I keep them recorded here
  because they were debt, not precedent: both were deliberate upstream choices made for
  convenience, and both cost more than they bought. Don't reintroduce either shape.
- **Additive over destructive.** Add entries rather than removing them; adjust weights rather
  than stripping tables.
- **Know the blast radius.** The `Chip Interface` merge into base `Humanoid` reaches every
  humanoid in the game at once. Changes at that level need to be deliberate and stated.
- ✅ **Verified 2026-08-15: 2.2 loads and plays on current Qud** — me, on my Legion Go 2 S.
  Compatibility work here is about *other mods* and *future patches*, not about booting.

### 2. Causality — nothing arbitrary

Every change carries a stated reason, and that reason goes in the commit message and the
player-facing changelog rather than staying in my head. Two different bars:

- **Defect fixes** need only "this contradicts the mod's own stated convention" — the
  tier-3 `Flawless Crysteel Boots`, the value-5 `Raven_Carbideweave Cloak`, the `<stag>` mix-ups.
  The convention tables in `docs/STYLEGUIDE.md` *are* the justification.
- **Design changes** need a reason grounded in Qud — its fiction, its existing systems, or an
  asymmetry the game already created. "It felt weak" is not a reason. The test I use: does the
  world explain it, and does it change a decision the player makes?

New content is *derived*, not invented: a new tier-4 halberd's stats fall out of the tier and
value curves. That derivability is the whole reason Mura's conventions are worth keeping.

### 3. Credit, permanently

Credit is the one condition attached to the fork permission, so it isn't negotiable.

- The `docs/PERMISSION.md` §4 credit list stays intact in the Workshop description, the README, and
  release notes — **Noble Lark named explicitly**, as Mura asked.
- **Keep the `Raven_` blueprint prefix.** It's Mura's signature in the namespace. Renaming it
  would erase attribution from the one place every future contributor actually reads.
- **Every outside contribution is credited by name**, in the README and the Workshop description,
  in the same pull request that merges it. Not "later" — a contributor who has to ask has already
  been let down, and the Workshop description is the only place most players will ever look.
  They get their own section, kept separate from the `docs/PERMISSION.md` §4 list, which stays
  intact.

### 4. Friendly but rigorous DX

- **No workarounds, no bandaids.** Fix causes. If a correct fix is out of scope right now,
  write the issue and leave the defect — don't paper over it.
- **No build step.** `mod/` is loaded directly by the game. Keep it that way; it's why anyone
  can contribute without a toolchain.
- **Validation is one command, and it fails loudly.** `python3 tools/validate_mod.py`, which grew
  out of a heredoc pasted into a document — the `mod/Core/Skills.xml` bug survived years precisely
  because nothing ran automatically. Keep new checks in the script rather than in prose.
- Issue → branch → small PR → squash merge.

### 5. Safety

Qud mods run with **full process privileges**, and any `mod/Scripting/` directory triggers a
mod-approval prompt for every subscriber. That's a trust relationship, and I treat it as one.

**Two different things live in this rule, and they are not the same weight.** The list below is a
hard boundary. What follows it is a preference with a reason, and the reason is not restraint.

**Where the game already does a thing in data, use the data.** Not because C# is suspect — it is a
normal way to build a feature here, and three of this mod's have needed it — but because a
blueprint, a tag or a population table is *Freehold's* mechanism, maintained by them across
patches, where equivalent C# is mine to keep working. #498 is the case: a whole `IGameSystem` went
away because `manifest.json` already gated a directory, and the result was less to break, not less
code for its own sake.

**The corollary matters as much and is easier to lose.** Where a feature genuinely needs C#, write
the C#. Looking for a worse XML route to stay under a budget is not what this rule asks for, and
there is no budget — the constraints are the list below, and they are about privilege, not volume.
#589 is why this is spelled out: "it needs no new C#" got written into an issue as the reason to
build that feature *first*, which is this preference deciding a roadmap it has no business
deciding, on a claim that turned out to be false.

**Never — these do not move:**

- file I/O outside the mod's own directory
- network access of any kind, or telemetry
- reading player files or the environment
- shelling out, or loading external assemblies
- **Harmony.** Freehold recommend it as a last resort, and it also breaks on arm64 macOS. Every
  hook this mod needs exists as a `MinEvent`.
- **reflection into game internals.** Public members and documented extension points only.

**What the mod's C# does.** The rule used to name 36 one-line
`ModImprovedMutationBase<T>` subclasses as the ceiling — no I/O, no reflection, no state. It now
also:

- reads its own options and writes public fields on records the game has already loaded
  (`GenotypeEntry.MutationPoints`, `.Skills`, `.Reputations`, `NameElement.Weight`,
  `NameScope.Chance`, `Gender.EnableSelection`)
- **registers a character-creation module** — an `AbstractEmbarkBuilderModule` subclass, declared
  by class name in `mod/Core/EmbarkModules.xml`, which handles one boot event and replaces the string
  the game generated for the player's name
- **declares a mutation** — a `BaseDefaultEquipmentMutation` subclass, named by `Class` in
  `mod/Core/Mutations.xml`, which grows a natural weapon onto a body part and keeps its rank in step

**I raised that ceiling three times, deliberately, and none of them was drift** — drift is the failure
this rule exists to prevent. #46 was the first: C# may hold state and adjust already-loaded data in
response to a player's choice. The second is the embark module, and it is worth saying why it
needed asking for rather than just doing.

It participates in character creation, which is a part of the game the mod had never touched, and
"the mod runs code while you are making your character" is a bigger sentence than any diff shows.
What made it acceptable is that none of the hard limits above move. `AbstractEmbarkBuilderModule`
declares **no abstract members**, so the subclass overrides one public virtual method; the game
instantiates it from a class name in XML exactly as it instantiates a part from a blueprint, so the
reflection is the game's rather than the mod's; and it declares no module data, because
`AbstractEmbarkBuilderModuleData` is `[Serializable]` and travels in build codes — a module holding
state would put this mod's shape into other people's saved characters.

The alternative was Harmony, which rule 5 refuses and which breaks on arm64 macOS anyway. The
question was never "patch or module", it was whether the feature was worth a new kind of C# at all.

**The third is the mutation class (#589), and it is the one this rule's own phrasing nearly
prevented.** Every `<mutation>` node names a `Class` the game resolves as
`"XRL.World.Parts.Mutation." + Class`, so a mutation cannot be declared in data — and the issue was
filed on the theory that it could be, by pointing `Class` at vanilla's `Horns`. That would have
broken vanilla's own entry for every player, because two entries sharing a class collide and the one
sorting first by display name wins. So the choice was never "XML or C#": it was a new mutation
class, or no mutation. The 36 existing subclasses only *improve* vanilla mutations; none of them is
one.

What kept it inside the limits above is the same test the embark module passed. The game
instantiates it from a class name in XML exactly as it instantiates a part from a blueprint, so the
reflection is the game's; it declares no instance fields, so the mod still adds nothing to save
shape; and it inherits a base Freehold wrote to be extended rather than reaching into one that was
not — which is a distinction `docs/LESSONS.md` now records, because `Horns` turned out to be
unextendable and reading its access modifiers is what said so.

**It has come down once, too.** A third bullet stood here until #498: a `[Serializable]`
`IGameSystem` that handled a zone event and created and destroyed objects within one zone, which is
how the Joppa building used to be removed when its option was off. `manifest.json` gates the whole
directory on that option instead, so the system went and the ceiling went back down with it. Worth
recording, because a ceiling that only ever rises is one nobody is reading — and because the
replacement was not a smaller version of the same idea but the discovery that the game already did
it, which is the outcome this rule's preference is pointing at.

**Both limits above are checked now, not just written down.** `tools/validate_mod.py` runs
`scripting-policy` (every banned API in rule 5's list, with the clause each pattern enforces) and
`serializable-shape` (any instance field on a `[Serializable]` type, which is what makes a class's
layout part of every save). Comments are stripped first, since the scripts legitimately name these
APIs; string literals are not, because `Type.GetType("System.IO.File")` is how a token scan gets
sidestepped.

**CodeQL does not cover the C#, and cannot.** Every non-`System` dependency is `XRL.*`, which
lives only in Freehold's 12 MB `Assembly-CSharp.dll` — proprietary, absent from NuGet and from CI
runners — so with build-mode `none`, call-target resolution sat at 82% against an 85% threshold,
permanently. `autobuild` and `manual` both need something to build, and there is deliberately no
`.csproj` (rule 4). I removed C# from the repo's CodeQL languages; `actions` and `python` still
run. That isn't a downgrade: CodeQL's generic queries could never express "no Harmony, no
reflection, no shelling out" — that's a project policy, and the two checks above enforce it
directly.

**Two obligations that come with holding state:**

- **Anything `[Serializable]` is written into player saves.** Its field layout is an identifier in
  the sense of `docs/STYLEGUIDE.md` §1 — renaming or removing a field can break saves that already
  exist. Treat a shipped part's or effect's shape as frozen unless you mean to break it — nearly
  every script here carries the attribute, and `serializable-shape` checks all of them.
- **Anything that mutates loaded game data must be idempotent and reversible.** Option handlers run
  repeatedly and in any order, so make the data *match* the option's value rather than performing a
  one-way edit. Where that's impossible — the Chip Interface slot, which a body built without one
  never gains — say so in the option's `<helptext>` rather than letting the player discover it.

### 6. Configurable — players choose what they take

Nobody should have to swallow the whole mod to get one part of it.

> **Defaults reproduce the mod's established behaviour. Options let players opt out.**
> "Off by default" applies to genuinely *new* opinions this fork introduces — not to what the mod
> already is.

**And an option has to earn its place.** The rule above says what a default should be; it never
asked whether the option should exist, and reading it as *"everything gets one"* is how the menu got
to twenty-five entries. The question comes first:

> **Would anybody actually turn this off?**

An option earns its place where a reasonable player could want the mod *without that part* — changes
to numbers, difficulty, loot, character creation, or an opinionated system somebody might disagree
with. Flavour and immersion that changes no mechanic does not need one. A clay pot being brown
rather than grey is not a part anybody needs to refuse, and neither is a gate that shuts itself.

The cost of getting this wrong is not neutral. Every option is a line in a menu a player has to read
past to find the one they want, a `<helptext>` to keep true, an entry in the wiring check, and a
branch to carry in the code forever. Adding one to a change nobody would disable spends all of that
and buys nothing.

Two cases where the answer is yes despite the change being small: it takes something *away* that a
player might want back, or it turns off cleanly and somebody has said they want it off. The
give-artifact filter is the first — the mark it respects is the player's, and a player who would
rather hand over a marked item should be able to.

Settled in #663, after two flavour features in one day were each given an option nobody would use.

This fork **continues** an existing mod rather than starting one. Someone subscribing to Qud
Expanded Community Edition is asking for Caves of Qud Expanded, so shipping it inert would be a
surprising reading of "players choose" — a mod that fails to arrive is not a configurable mod.

The exception is a change that **grants power with no content attached**. Those stay off by
default even though they predate the fork; the starting reputation bonus is the current
example. The test is whether turning the option on gives the player something to *use* or merely
something to *have*.

Settled in #45. Every `Default=` value follows from it.

Qud ships a real mod-options menu and it's the primary mechanism. Two halves, both verified against
the mods installed on my machine (`~/Library/Application Support/Steam/steamapps/workshop/
content/333640/`):

- **Declaring options is pure XML.** A file with `Option` in its name, root `<options>`, one
  `<option ID= DisplayText= Category="Mods" Type="Checkbox|Slider|Combo|BigCombo|Button"
  Default= SearchKeywords=>` each, with a `<helptext>` child. `Category="Mods"` is what files it
  into the in-game menu. No code needed to make an option *appear*.
- **Acting on an option usually requires C#.** Of the 12 installed mods shipping an `Options.xml`,
  **all 12 also ship at least one `.cs`**. The exception is gating a whole directory, which
  `manifest.json` does on its own (#498) — see rule 5, where that discovery took a system out of
  this mod's C# entirely. The working pattern is `[HasOptionFlagUpdate]` on the class,
  `[OptionFlagUpdate]` on a `static void` method, and `XRL.UI.Options.GetOption(ID, default)`
  inside it — **every option value is a string**, sliders included, so numbers need parsing.
  `[OptionFlag]` field binding also exists and is sometimes recommended over `GetOption`, but
  **zero of the 87 installed mods use it and 17 use `GetOption`**. Prefer the pattern with evidence
  behind it.

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

The design consequence: **prefer designs whose off-switch is a runtime decision** rather than a
load-time one. A chip family that can be dropped from the loot tables is more configurable than
one welded into chargen, and that should influence how new content gets built.

### One mod, not a constellation

**This mod stays self-contained.** It's the vehicle for this fork's features, including new ones,
and the player experience I'm aiming at is *one subscription* — not assembling the intended game
from eighty separate Workshop items.

That makes **options the mechanism**, and splitting a last resort rather than a peer choice.
Where a feature cannot be option-gated, the answer is to ship it on with that stated in the
description — not to exile it to a sub-mod.

A split is justified only when a system is genuinely a different mod: a different audience, a
different maintenance cadence, or a dependency the core shouldn't carry. Mura's Grand Bazaar and
Experience Curve Beta were split that way and stay separate for now; the fork permission explicitly
covers them, so absorbing them later is allowed if it ever serves players better than a separate
subscription.

Cross-mod dependencies, if ever needed, use `LoadBefore` / `LoadAfter` in `manifest.json` —
`LoadOrder` is deprecated as of build 210.

### The obligation that comes with staying self-contained

A growing single mod becomes take-it-or-leave-it unless the off-switches keep pace. So:

> **Every new feature ships with its option in the same PR.**

Not "options later". Retrofitting a toggle onto a shipped feature means deciding its default after
players already have expectations, and it's the exact debt this fork spent its first release
paying down.

This rule pulls against rule 5's preference rather than against its limits: gating content means
more C#, not less. That is fine, and worth being explicit about, because the two rules would
otherwise look as though they disagree. The mod already ships `mod/Scripting/`, so the subscriber
approval prompt is **already paid for**, and option-reading plus table adjustment stays well inside
rule 5's hard boundary — no I/O, no network, no reflection. It licenses nothing beyond that.

---

## Release blockers — all five cleared

I identified five items at the start of the fork as blocking a first release. **All five are now
closed.** I keep the list as a record rather than a queue, because each was a real upstream defect
and the shape of each is worth not reintroducing. **The mod loads and plays on current Qud** — none
of this was ever about getting it to run.

| What it was | Where it landed |
|---|---|
| `mod/workshop.json` carried `"WorkshopId": 1134036260` — Mura's item — plus their pre-handoff description asking that the mod not be forked | `WorkshopId` cleared so the fork publishes as a **new** item; `Title`, `Description` and `ImagePath` now describe this fork and carry the `docs/PERMISSION.md` §4 credits (#2). The placeholder `0` it was cleared to blocked the first upload and is a defect in its own right (#163) |
| `Artifact 3`–`8` were full table replacements, not merges | All six merge, each contributing one `Raven_Chips Tier N` entry (#3, fixed in #34). See `docs/FEATURES.md` §7.3 |
| `mod/Core/Skills.xml` failed a strict XML parse — a duplicate `Tile` attribute on Berserk! | Cosmetic, and settled before the fix: Qud's loader tolerated it, so §4's skill changes had been shipping all along. Attribute removed (#5) |
| 72 of 144 psionic chips could not drop | `Raven_Chips Tier 1/2/3` now hold 48 entries each (#6, fixed in #36) |
| Nine armor pieces and `Raven_Iron Maceth` were unobtainable — no drop entry, no tinker recipe | All reachable; `tools/validate_mod.py` reports **0** known inherited defects (#7, fixed in #38) |

Remaining work lives in the issue tracker. `docs/FEATURES.md` §10 is still the severity-ranked
backlog, with a file and line on every open row.

---

## Things not to break

- **Credit is the one condition of the fork permission.** Mura named **Noble Lark** explicitly for
  the subtype sprites. Keep the credits list in `docs/PERMISSION.md` §4 intact in the Workshop
  description and any README.
- `mod/ObjectBlueprints/Ammo.xml` is **entirely commented out** (62 objects, "removed temporarily").
  Don't delete it — it's the largest block of ready-made content available, including vibro
  bullets/shells and a reworked shotgun shell. Reviving it is a good early win.
- Four vibro weapons are commented out in `mod/ObjectBlueprints/MeleeWeapons.xml` with "rework these
  or remove them".
- The `Chip Interface` slot is merged into the base `Humanoid` anatomy, so **every humanoid NPC
  in the game has one**. Nothing populates it today. Be deliberate if you ever change that — it
  would affect the entire world at once. Option-gated as of #81 — and note `Humanoid` is shared by
  NPCs *and* by a Mutated Human player (vanilla's genotype is `BodyObject="Humanoid"`), so the two
  cannot be separated by editing that anatomy alone. That is why `Raven_ChipSlotPlayerMutator`
  exists: since #353 it takes the shared slot back off the player at chargen, because a genotype
  that can mutate is not what chips are for.

---

## Repo state

Under git as of 2026-08-15, with a deliberate two-commit baseline:

| Commit | Contents |
|---|---|
| `971d97e` — tag **`upstream-2.2`** | Pristine upstream 2.2, 76 files, unmodified |
| `da753b7` | This fork's docs — `FEATURES.md`, `PERMISSION.md`, `CLAUDE.md`, `.gitignore` (later moved to `docs/`) |

So `git diff upstream-2.2` shows exactly what this fork has changed, forever. Keep that true:
never amend or rewrite the baseline commit.

The remote is [`vixygrey/qud-expanded-community-edition`](https://github.com/vixygrey/qud-expanded-community-edition),
with issues and CI both in use.

---

## Source documents

| File | What it is |
|---|---|
| `docs/FEATURES.md` | Complete feature reference + bug checklist. Written for this fork; the authoritative doc. |
| `docs/LESSONS.md` | Operational traps I hit maintaining this fork — Qud internals, git and GitHub, tooling. |
| `docs/DESIGN_options.md` | The design work behind the mod options (#45). Historical — the shipped result is in `docs/FEATURES.md` §13. |
| `docs/DESIGN_balance.md` | The balance sweep against vanilla (#315) — verified combat mechanics, the four open questions, and the reasoning behind each. |
| `docs/PERMISSION.md` | Fork permission, provenance, credit obligations, pre-upload actions. |
| `docs/STYLEGUIDE.md` | Naming, layout, XML/C# formatting, Workshop requirements. Read §1 before renaming anything. |
| `docs/permission-mura-workshop-comment.png` | Screenshot evidence of the grant. |
| `docs/mura-feature-notes-wip.txt` | Mura's oldest partial list. Joppa section is stale. |
| `docs/2.2-changelog.txt` | The 2.1.1 → 2.2 delta. Only source for the physical-vs-mental chip scaling split. |

Mura also kept a pinned "Partial Feature List" discussion on the Workshop page — newest of the
three writeups, and the best source for the energy-cell mod formulas. Its content is folded into
`docs/FEATURES.md` §6.6 and §10. Where any of Mura's docs disagree with the XML, **the XML is what
ships** — `docs/FEATURES.md` §10 has a table of the known disagreements.
