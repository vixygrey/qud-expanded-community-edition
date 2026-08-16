# Mod options — design doc

**Status:** spec. No code written. Written before a first release, deliberately.
**Target:** Caves of Qud 2.0.211.x
**Premise:** nobody should have to swallow the whole mod to get one part of it.

This is charter rule 6 made concrete. It is also the first work in this fork that adds *behaviour*
rather than fixing defects, so it is the first time rule 2 (causality) applies at the design bar
rather than the defect bar.

---

## 0. The decision that comes first

Charter rule 6 currently reads:

> Opinionated changes ship **off by default**; content ships on.

Applied literally to the features below, someone installs *Qud Expanded* and gets a mod that
mostly does not do anything. The skill retunes are off, the mutation points are vanilla, the
starting reputations are vanilla. That is not configurability, it is a mod that fails to arrive.

**Proposed amendment:**

> **Defaults reproduce the mod's established behaviour. Options let players opt out.**
> "Off by default" applies to genuinely *new* opinions this fork introduces — not to what the mod
> already is.

The reasoning is that this is a **fork continuing an existing mod**, not a new one. Someone
subscribing to *Qud Expanded Community Edition* is asking for Caves of Qud Expanded. Shipping it
inert would be a surprising reading of "players choose".

This needs settling before anything is built, because it decides every `Default=` value below.
**Nothing else in this document is blocked on it**, but every option's default is.

---

## 1. What can actually be gated

Three mechanisms, and picking the wrong one wastes the work. Verification status is stated for
each because two of the three are proven and one is not.

| Feature | Mechanism | When it applies | Verified? |
|---|---|---|---|
| Loot participation (chips, new weapons and armor in tables) | `PopulationManager.Populations` mutated at runtime | Live | ✅ Proven — installed mods do this (`1756765609/fishvendorhotloader.cs`) |
| Psionic Adept genotype | Chargen | Before starting a character | ⚠️ Hook exists, mechanism unproven |
| Mutation points | Chargen | Before starting a character | ⚠️ Unproven |
| Starting reputation | Chargen | Before starting a character | ⚠️ Unproven |
| Skill tree changes | Unknown | ? | ❌ No worked example anywhere |
| Joppa house | Zone generation | New game only | ⚠️ Unproven |
| Chip Interface anatomy slot | Baked into every creature at creation | **Not gateable** | ✅ Known |

"Before starting a character" is not a defect. It is how every chargen-affecting option in Qud
works, and `<helptext>` is where it gets said.

### 1.1 The one that cannot be gated

The Chip Interface slot is merged into base `Humanoid`, so it is written into every humanoid's
body when that creature is created. **There is no toggle for it**, and there never will be without
removing the feature entirely.

That is acceptable: an empty, abstract, position-ignoring slot costs nothing to a player who never
uses a chip. But it means "disable everything" still leaves one trace, and the helptext should not
pretend otherwise.

---

## 2. API surface — what the game actually documents

The game ships **its own API documentation** at
`CoQ.app/Contents/Resources/Data/Managed/Assembly-CSharp.xml` — 898 documented members with
summaries. This is a better source than metadata analysis and was not being used.

### 2.1 Declaring options — pure XML, no code

A file with `Option` in its name, root `<options>`:

```xml
<option ID="OptionQudExpandedMutationPoints"
        DisplayText="Qud Expanded: mutation points for Mutated Humans"
        Category="Mods" Type="Slider" Default="16" Min="6" Max="24" Increment="1"
        SearchKeywords="qud expanded mutation points mutant">
  <helptext>
    How many mutation points a Mutated Human starts with.
    Vanilla is 12. This mod's default is 16.
    Set before creating a character; changing it has no effect on an existing one.
  </helptext>
</option>
```

`Category="Mods"` is what files it into the in-game menu. Types: `Checkbox`, `Slider`, `Combo`,
`BigCombo`, `Button`.

### 2.2 Reading options — requires C#

`[OptionFlag]` on a field in a `[HasOptionFlagUpdate]` class, with `[OptionFlagUpdate]` to react to
changes. Empirically firm: of the 12 installed mods shipping an `Options.xml`, **all 12 also ship
at least one `.cs`**.

### 2.3 The chargen seam — documented and in use

```
XRL.CharacterBuilds.AbstractEmbarkBuilderModule      "Abstract base class for all EmbarkBuilder modules"
XRL.CharacterBuilds.AbstractQudEmbarkBuilderModule   "Abstract base class for Qud EmbarkBuilder modules"
XRL.CharacterBuilds.QudEmbarkBuilderModule`1         "...with a specific data type"
XRL.CharacterBuilds.AbstractEmbarkBuilderModule.GetRequiredMod
    "Return the name of your mod if you want to have a notice about required mods"
XRL.CharacterBuilds.EmbarkInfo
```

Used in practice by `ChooseYourFighter` (`3032410975/Scripts/PlayerModel.cs`), which subclasses
`AbstractEmbarkBuilderModuleData`.

### 2.4 The boot lifecycle — 28 named, documented hooks

`XRL.CharacterBuilds.Qud.QudGameBootModule.BOOTEVENT_*`. The ones that matter here:

| Event | Documented as |
|---|---|
| `BOOTEVENT_BEGINBOOT` | "fires before anything else happens during game bootup" |
| `BOOTEVENT_AFTERCACHERESET` | "caches are now reset" |
| `BOOTEVENT_INITIALIZESYSTEMS` | "typically used to use game.AddSystem(...)" |
| `BOOTEVENT_BOOTPLAYEROBJECTBLUEPRINT` | "element is a string that will be the player's blueprint" |
| `BOOTEVENT_AFTERBOOTPLAYEROBJECT` | "the player's GameObject has been created" |
| `BOOTEVENT_GAMESTARTING` | "the last event before [the game starts]" |

`BOOTEVENT_AFTERBOOTPLAYEROBJECT` is the interesting one for reputation: the player object exists
and can be adjusted before play begins.

### 2.5 What is *not* documented

**`GenotypeFactory`, `SkillFactory`, and anything named `MutationPoints` do not appear in the API
documentation at all**, and **no installed mod manipulates them**. Zero worked examples across 87
mods.

This is the single largest risk in the document, and it is why §3 exists.

---

## 3. Build the spike before the design

> **Prove one option end-to-end before designing eight.**

**The spike: the mutation point slider.**

It is the best first target for four reasons:

1. It is the most valuable item on the list on its own merits — a slider is a better design than
   any fixed number, including Mura's 16.
2. It **changes a value** rather than removing a record. Removing a genotype from a list is a
   harder unknown; overwriting an integer is the smallest possible test of the same seam.
3. It has an obvious success criterion: start a Mutated Human, count the points.
4. If it fails, it fails cheaply and tells us the chargen seam is closed for data of this kind —
   which redirects the whole design toward splitting into sub-mods instead.

**Definition of done:** an `Options.xml` slider, an `[OptionFlag]` field, and a Mutated Human
starting with the number the slider says. Nothing else.

Only after that lands should the rest be designed against a proven mechanism.

---

## 4. The features, individually

### 4.1 Mutation points — `Slider`

Vanilla 12, this mod 16. Slider 6–24, default 16 (see §0).

Worth deciding: does the slider also cover **True Kin** stat points and the Psionic Adept's 34?
Recommendation: **no, not initially.** One number, one option, proven first. A second slider is
cheap to add later; an over-scoped first option is not.

### 4.2 Skill tree changes — `Checkbox`, **highest risk**

Six retuned trees (`docs/FEATURES.md` §4). No known mechanism, and skill trees are read both at
chargen and during play.

**Do not design this until §3 lands.** If the chargen seam turns out not to reach skills, the
honest answer is a **separate sub-mod** rather than a contorted runtime patch — which is exactly
what charter rule 6's "modularity is the complement" clause is for.

### 4.3 Psionic Adept genotype — `Checkbox`

Turning it off means removing a genotype from the chargen list. Unproven.

**Interaction worth deciding now:** with the genotype off, the **chips still work** — the Chip
Interface is on base `Humanoid`, so every genotype has a slot. That is coherent and probably
desirable: the chip system is the mod's best idea and does not depend on the genotype existing.

The 18 subtypes and their `StartingGear_*` tables become dead data. Harmless.

### 4.4 Starting reputation — `Checkbox`

Mutated Human +300 Joppa, Psionic Adept +300 Mechanimist. The most clearly "opinionated" item on
the list, and the best candidate for defaulting **off** even under §0's amendment — it is a
straightforward power grant with no content attached.

`BOOTEVENT_AFTERBOOTPLAYEROBJECT` looks like the right hook.

### 4.5 The Joppa house — `Checkbox`, new game only

A `Load="Merge"` map patch, applied when the Joppa zone is first generated. Once generated, it is
in the save.

Two candidate approaches, both unproven:

1. Read the option at world generation and skip the patch.
2. Ship the map patch as a **separate sub-mod**, which sidesteps the problem entirely.

Given it is a single 76-cell file with no dependencies on the rest of the mod, **option 2 is
probably correct** and is the cheapest thing on this list to split.

### 4.6 Loot participation — `Checkbox`, fully live

The one thing that is proven and works mid-game: adding and removing entries in
`PopulationManager.Populations`.

Candidate options: chips in the loot pool, new weapons and armor in the loot pool. Both live,
both reversible, both safe.

---

## 5. Keep the menu small

Thirty toggles is its own kind of unusable. Target **six to eight**:

| Option | Type | Default (pending §0) |
|---|---|---|
| Mutation points | Slider | 16 |
| Skill tree changes | Checkbox | on |
| Psionic Adept genotype | Checkbox | on |
| Starting reputation bonuses | Checkbox | **off** |
| Joppa house | Checkbox | on |
| New items in loot tables | Checkbox | on |
| Psionic chips in loot tables | Checkbox | on |

Every `<helptext>` states whether the option is live, chargen-scoped, or new-game-scoped. That is
not boilerplate — it is the difference between an option that works and a bug report.

---

## 6. What this costs against the charter

**Rule 5 (safety).** The mod already ships `mod/Scripting/`, so the subscriber approval prompt is
already paid for and this adds no new trust cost in that sense. But it moves the C# from **36
inert one-line subclasses to real logic with state**, and rule 5 currently names that inertness as
"the ceiling". That ceiling is being raised deliberately, and the charter should say so rather
than have it happen by drift.

The limits themselves do not move: no file I/O, no network, no reflection into internals, no
Harmony. Reading options and mutating already-loaded game data stays well inside them.

**Rule 6 (configurable).** Needs the §0 amendment.

**Rule 2 (causality).** This is the first work here that meets the *design* bar rather than the
defect bar. The justification is not "it would be nice" — it is that the mod bundles a genotype,
a balance opinion, a world edit and an item catalogue into one subscription, and players
reasonably want some of those without the others.

---

## 7. Edge cases to handle before release

- [ ] **Option changed mid-game.** Every option must either apply live or state that it does not.
      Silent no-ops are worse than a disabled control.
- [ ] **Existing saves.** A chargen option cannot retroactively change a made character. Say so.
- [ ] **Loot options toggled after world generation.** Containers already generated keep their
      contents. Acceptable; document it.
- [ ] **Everything off.** The mod must still load cleanly and not error. The Chip Interface slot
      remains (§1.1).
- [ ] **Psionic Adept off, existing Psionic Adept character.** Do not break the save — the
      genotype data must still resolve for a character already using it.
- [ ] **Interaction with the sub-mods** (Grand Bazaar, Experience Curve) if they are ever revived.

---

## 8. Build order

1. **The spike (§3)** — mutation point slider, proven end to end. Nothing else.
2. Loot participation options — the proven mechanism, immediate value, low risk.
3. Starting reputation — small, and the clearest opt-out win.
4. Psionic Adept genotype toggle.
5. Joppa house — **decide split versus toggle first**, do not build both.
6. Skill tree changes — last, because it is the least understood and the most likely to end as a
   sub-mod.

Steps 1–3 are a plausible first release with options. Steps 4–6 can follow.

---

## 9. Open questions

- Can a genotype be removed from the chargen list at runtime? No worked example exists.
- Can `MutationPoints` be overridden from an embark builder module, or does it need to be read
  from the genotype record before chargen builds its UI?
- Are skill tree definitions mutable after load at all?
- Does the Joppa map patch have any hook at zone generation, or is splitting the only option?
- Does `GetRequiredMod` matter here — is there value in the chargen UI knowing this mod is
  required for a build code?

Every one of these is answerable with a small spike against a running game. None should be
answered by assumption.

---

## Sources

- `CoQ.app/Contents/Resources/Data/Managed/Assembly-CSharp.xml` — the game's own API
  documentation, 898 documented members
- Installed Workshop mods under `steamapps/workshop/content/333640/` — 87 mods, 12 with
  `Options.xml`, all 12 shipping C#
- `CLAUDE.md` — charter rules 2, 5 and 6
- `../design-docs/DESIGN_difficulty.md` §1 and §5 — the same split-versus-options argument, reached
  independently
