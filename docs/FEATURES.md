# Caves of Qud Expanded — Complete Feature Reference

*I reconstructed this by reading the whole mod source — every XML blueprint, population table,
skill, genotype, subtype, body, C# script, and the Joppa map patch. No complete list of what this
mod does had ever existed, including for Mura, and I needed one before I could safely change
anything. Where this document and the XML disagree, **the XML is what ships**; §10 tabulates the
disagreements I know about.*

**Original author:** Mura (`@mura_raven`) — with contributions from Noble Lark (subtype sprites),
Arendeth (table fixes), Tyrir (bug reports), and Scrolldier/Parzival (mentorship).
**Workshop ID:** 1134036260 · **Last upstream release:** 2.2 (built for Qud 1.0)
**Steam tags:** Stable, Armor, Artifact, Cybernetic, Item, Item Mod, Weapon, Genotype, Subtype, Mutation, Skill, Balance, Lore

---

## 0. At a glance

| Area | What the mod does |
|---|---|
| **New item blueprints** | **368** brand-new objects across 8 blueprint files |
| **Modified vanilla blueprints** | **214** `Load="Merge"` edits to existing objects |
| **New genotype** | Psionic Adept, with 18 subtypes |
| **New body system** | "Chip Interface" slots — 1 for all humanoids, 2 for True Kin, 4 for Psionic Adepts |
| **New equipment system** | 144 psionic chips/chipsets granting real mutations to any genotype |
| **New weapon classes** | Katana, rapier, halberd, greataxe, greatsword, vinereaper (extended), wristblade, two-handed mace, war hammer, greathammer |
| **New armor classes** | Greatshield, vambrace (arm armor), weave cloaks at every tier, nanoweave/flexi gear |
| **New ranged weapons** | 18 psionic pistols/rifles + 6 conventional guns |
| **Skill tree edits** | 6 skill trees retuned (Akimbo was added to Multiweapon Fighting upstream; removed in this fork — §4) |
| **Loot tables** | **56** vanilla tables merged — none replaced — plus 18 new starting-gear tables, 3 new chip tables + 1 helper |
| **World edits** | New amenity building in Joppa (76 map cells) |
| **Economy** | Price curve flattened on high-tier gear; all 51 grenades repriced |

> **This document specifies; the [wiki](https://github.com/vixygrey/qud-expanded-community-edition/wiki)
> explains.** Every figure below — tier, weight, price, drop rate, stat modifier, option default and
> scope — is authoritative here, and the wiki links back to it rather than repeating it. What a build
> plays like, how the chip families interact and how to open a run belong there instead. The boundary,
> and why it is stricter for the wiki than for anything in this repository, is in
> [`CONTRIBUTING.md`](../CONTRIBUTING.md#the-wiki-it-explains-docsfeaturesmd-specifies).

---

## 1. Genotypes

All three genotypes are defined/merged in `Genotypes.xml`.

### 1.1 Changes shared by all genotypes

Every genotype gains these starting skills:

- **Staunch Wounds** (`Physic_StaunchWounds`)
- **Cooking and Gathering** (`CookingAndGathering`)
- **Meal Preparation** (`CookingAndGathering_MealPreparation`) — the base skill is required for this to function, which is why both are granted

Every humanoid also gains **one Chip Interface slot** (see §3).

### 1.2 Mutated Human

| Field | Vanilla | CoQE |
|---|---|---|
| Mutation points | 12 | **16** |
| Skill points / level (`BaseSPGain`) | 50 | **65** |
| HP gain / level (`BaseHPGain`) | 1-4 | **1-5** |
| MP gain / level (`BaseMPGain`) | 1 | **1-2** |
| Joppa reputation | 0 | **+300** |
| Extra starting skill | — | **Menacing Stare** (`Persuasion_MenacingStare`) |

> ℹ️ **`BaseHPGain` was `2-3` through 2.2; this fork corrected it to `1-5` in #90.** All three of
> Mura's writeups (`2.2 changelog.txt`, `What Does the Mod Do (WIP).txt`, and the pinned Workshop
> feature list) state 1-5, and the XML was the odd one out.
>
> Three things settled it. `2-3` is uniform over {2,3}, so it carries **vanilla's own 2.5 average**
> — the headline mutant HP change moved nothing. It inverts the changelog's stated design, which
> gives mutants "variability but potential for greater numbers" against True Kin's 2-4 "for a
> little more consistency, leaning the opposite from Mutants"; at 2-3 mutants are *more* consistent
> than True Kin and strictly dominated by them, same floor of 2 against a ceiling of 3 rather than
> 4. And every other HP claim in the docs matches its XML — True Kin's 2-4 and the Adept's 1-4 both
> check out, leaving this the single disagreement.
>
> The WIP notes' sentence is the source of the long-standing confusion: *"Narrowed health gain from
> 1-4 to 1-5 for more flavor and a chance at more HP"* contradicts itself, since the verb says
> narrow while the numbers and the rationale say widen. The newer changelog carries the reasoning
> and resolves it.
>
> Players who preferred the shipped 2-3 can select it — see §13.

**How HP gain actually works**, verified against `Assembly-CSharp.dll` metadata rather than
inferred: `XRL.GenotypeEntry.BaseHPGain` is a **public string**, and `XRL.World.Parts.Leveler`
calls `RollHP(string BaseHPGain)` on every level-up via `GetEntryDice`. Rolls run through
`Stat.RandomLevelUpChoice` on a dedicated seeded level-up RNG stream. The range is a uniform
inclusive `min-max`, re-read **fresh at each level** — nothing is baked at chargen, which is why
the option over it takes effect mid-save from the next level onward. `BaseSPGain` and `BaseMPGain`
work identically, through `RollSP` and `RollMP`.

### 1.3 True Kin

| Field | Vanilla | CoQE |
|---|---|---|
| Skill points / level | 70 | **85** |
| HP gain / level | 1-4 | **2-4** |
| Cybernetics license points | 2 | **4** |
| Body object | `Humanoid` | **`TrueKin`** (custom anatomy — 2 Chip Interface slots) |
| Extra starting skills | — | Staunch Wounds, Cooking and Gathering, Meal Preparation |

### 1.4 Psionic Adept (new)

Named `Psionic Adept` internally and in display, matching vanilla's convention that a genotype's
`Name` and `DisplayName` agree (`Mutated Human`, `True Kin`). It was internally `Psionic` until
this fork renamed it (#24).

Earlier versions called the genotype "Yttrian"; the anatomy and body object kept that name until
this fork renamed them to `PsionicAdept` (#13) — that follows the *other* convention the same
file sets, where a body object is the display name with spaces removed (`True Kin` → `TrueKin`).

| Field | Value |
|---|---|
| Mutation points | 0 (`AllowedMutationCategories=""` — no mutation access at all) |
| Stat points to allocate | **34** (True Kin: 38, Mutant: 44) |
| Base stat floor | 12 in every stat (identical to True Kin), then heavily modified by affinity |
| Stat range | 12–24 per stat |
| HP gain / level | **1-4** |
| Skill points / level | **95** (+10 over True Kin, +25 over vanilla mutant) |
| MP gain / level | 0 |
| Cybernetics license points | **2** |
| Chip Interface slots | **4** |
| Species / flags | `human`, `IsTrueKin="True"` |
| Mechanimist reputation | **+300** |
| Random-weight in chargen | 10 (same as the other two) |
| Tile | `creatures/sw_nomad.bmp`, detail color `M`, code `r` |

Starting skills: Run (`Tactics_Run`), Camp (`Survival_Camp`), Staunch Wounds, Cooking and
Gathering, Meal Preparation, and **Gadget Inspector** (`Tinkering_GadgetInspector`) in place of
the Rebuke Robot / Menacing Stare the other genotypes get.

Because `IsTrueKin="True"` and cybernetics points are granted, Psionic Adepts can use the
becoming nook and all cybernetics — they are mechanically a third "tech" genotype, not a mutant.

> ⚠️ The genotype's chargen blurb reads `{{C|30}} bonus skill points each level`. The actual
> delta versus vanilla True Kin is +25 (95 vs 70) or +10 vs the mod's own True Kin (95 vs 85).
> The "30" is left over from an earlier tuning pass.

---

## 2. Psionic Adept subtypes (`Subtypes.xml`)

18 subtypes in one class (`Affinities`, chargen title "choose expertise", singular "affinity"),
split into two categories:

- **The Lore Seekers of the Grand Library** (`Full Psionic`) — 9 caster subtypes. Each grants
  **+1 cybernetics license point** on top of the genotype's 2.
- **The Immovable Wall of the Yttria** (`Half Psionic`) — 9 martial "Guardian" subtypes. No
  bonus cybernetics points.

Design rule stated in the source comments: each subtype nets **+2 to +3 stat points** after
subtracting penalties (True Kin net +3 to +4, Mutants net +2). Subtypes with elemental
resistances take a penalty resist equal to **half** their bonus.

### 2.1 Full Psionic — The Lore Seekers of the Grand Library

| Subtype | STR | AGI | TOU | INT | WIL | EGO | Resistances | Bonus skills |
|---|---|---|---|---|---|---|---|---|
| Force, Watchers of the World | -2 | -2 | -2 | +4 | +2 | +2 | — | Short Blades Expertise, Rifles, Tinkering (+Disassemble, Reverse Engineer, Tinker I) |
| Fire, Defenders of the Core | +1 | -2 | -2 | +2 | +2 | +2 | Heat +40 / Cold -20 | Short Blades Expertise, Axe, Heavy Weapons (+Tank, Sweep) |
| Ice, Bulwark of the Throne | -2 | -2 | +1 | +2 | +2 | +2 | Cold +40 / Heat -20 | Short Blades Expertise, Rifles, Kickback, Endurance (+Swimming) |
| Lightning, Hunters of the Defilers | -2 | +1 | -2 | +2 | +2 | +2 | Electric +40 / Acid -20 | Short Blades (+Bloodletter, Jab, Hobble), Pistol |
| Light, Seekers of the Path | -2 | +1 | -2 | +2 | +2 | +2 | Heat +20, Electric +20 / Cold -10, Acid -10 | Short Blades Expertise, Pistol (+Akimbo, Weak Spotter, Sling and Run) |
| Corrosive, Builders of the Wall | -2 | -2 | -2 | +2 | +2 | +4 | Acid +40 / Electric -20 | Short Blades Expertise, Rifles, Persuasion (+Intimidate, Berate, Snake Oiler) |
| Blood, Lurkers of the Unknown | -2 | +1 | -2 | +2 | +2 | +2 | *+4 save vs Bleeding* | Short Blades, Pistol, Multiweapon Fighting (+Proficiency, Expertise) |
| Mental, Guides of the Lost | -2 | -2 | -2 | +4 | +2 | +2 | — | Short Blades Expertise, Rifles, Customs (+Trash Divining), Survival + **all 7 terrain survival skills** |
| Temporal, Keepers of the Records | -2 | -2 | -2 | +2 | +4 | +2 | — | Short Blades Expertise, Rifles, Discipline (+Fasting Way, Iron Mind, Lionheart, Conatus, Mind over Body) |

*Light also carries an `extrainfo`: "Guaranteed one Solar Cell."*

### 2.2 Half Psionic — The Immovable Wall of the Yttria

| Subtype | STR | AGI | TOU | INT | WIL | EGO | Resistances | Bonus skills |
|---|---|---|---|---|---|---|---|---|
| Force, Main Battalion | +3 | +3 | +1 | — | -2 | -2 | — | Long Blades (+Dueling Stance), Shield (+Deft Blocking, Swift Blocking) |
| Fire, Berserker Battalion | +4 | +2 | +2 | -2 | -2 | -2 | Heat +20 / Cold -10 | Axe (+Cleave, Dismember, Hook and Drag), Cudgel Charging Strike |
| Ice, Assault Battalion | +4 | +2 | +2 | -2 | -2 | -2 | Cold +20 / Heat -10 | Cudgel (+Bludgeon, Charging Strike, Conk, Backswing) |
| Lightning, Skirmish Battalion | +2 | +4 | +2 | -2 | -2 | -2 | Electric +20 / Acid -10 | Tactics (+Throwing, Juke), Acrobatics (+Dodge, Tumble) |
| Light, Ranged Battalion | +2 | +4 | +2 | -2 | -2 | -2 | Heat +10, Electric +10 / Cold -5, Acid -5 | Rifles (+Kickback, Suppressive Fire, Wounding Fire, Sure Fire) |
| Corrosive, Flank Battalion | +2 | +2 | +4 | -2 | -2 | -2 | Acid +20 / Electric -10 | Long Blades Proficiency, Endurance (+Swimming, Poison Tolerance, Weathered, Juicer) |
| Blood, Assassin Battalion | +1 | +4 | +2 | -2 | -2 | -2 | *+2 save vs Bleeding* | Axe (+Dismember), Short Blades (+Bloodletter), Multiweapon Fighting (+Proficiency) |
| Mental, Technical Battalion | +1 | +3 | +1 | — | -2 | — | — | Persuasion (+Inspiring Presence), Tinkering (+Disassemble, Deploy Turret, Lay Mine) |
| Temporal, Support Battalion | +2 | +2 | +2 | **-6** | +1 | +1 | — | **19 skill trees at once** — see below |

*Light Guardian also carries "Guaranteed one Solar Cell."*

**Temporal, Support Battalion** is the outlier build: it trades a crippling **-6 Intelligence**
for base access to Acrobatics, Axe, Rifles, Cooking and Gathering, Cudgel, Customs, Discipline,
Multiweapon Fighting, Endurance, Physic, Heavy Weapons, Long Blades, Persuasion, Pistol, Shield,
Short Blades, Survival, Tactics, and Tinkering (plus Tinker I, Disassemble, Scavenger). Its own
`extrainfo` says: *"Starts with massively lowered Intelligence in exchange for so many skills."*

### 2.3 Subtype sprites

18 custom tiles by **Noble Lark** live in `Textures/Subtypes/` — `{force,fire,ice,lightning,light,corrosive,blood,mental,temporal}{Psionic,Guardian}.png`.

One naming quirk:
`Subtypes.xml` references the tiles as **`.bmp`** (`Subtypes/forcePsionic.bmp`) while the shipped
files are `.png`. The latter is normal Qud convention — the engine resolves `.bmp` tile paths
against `.png` assets — but worth knowing if you ever rename them.

---

## 3. The Chip Interface & psionic chips

This is the mod's headline system, and the reason I picked the fork up: **equipment that grants real, working mutations to genotypes
that cannot mutate.**

### 3.1 Body slots (`Bodies.xml`)

A new abstract, integral, position-ignoring body part type — **Chip Interface** — is defined
and then attached to anatomies:

| Anatomy | Chip Interface slots | Notes |
|---|---|---|
| `Humanoid` (merged) | **1** | Applies to every humanoid in the game, NPCs included |
| `TrueKin` (new) | **2** | Full custom anatomy; True Kin genotype points at this |
| `PsionicAdept` (new) | **4** | Psionic Adept anatomy |

> ✅ **Resolved in this fork (#13).** The original shipped a slot called **"Chipset Interface"**
> while every piece of Mura's player-facing documentation called it the **"Psionic Interface"**.
> Neither was accurate: the slot takes 108 chips against 36 chipsets, and 13 of the 36 mutations
> the chips grant are *physical* rather than mental. It is now **"Chip Interface"** — true of the
> whole catalogue, and consistent with the technological fiction in the chips' own description.

The `TrueKin` and `PsionicAdept` anatomies are otherwise identical to vanilla Humanoid (Head/Face,
Back, two Arms with Hands, two Missile Weapon slots, Hands, Feet). Two matching creature
blueprints (`TrueKin`, `PsionicAdept`) in `ObjectBlueprints/Creatures.xml` inherit from `Humanoid`
and swap the anatomy.

### 3.2 How chips work

`Raven_Base Psionic Chip` inherits `BaseArmor`, sits in the Chip Interface slot with 0 AV /
0 DV and 0 weight, and uses the `UnknownArmor` examiner alternate (so it needs identifying).
Its description explains the fiction: the chip integrates with your flesh and grants lost
knowledge — remove it and you lose the ability.

Each chip carries one or more custom parts named `Raven_Mod<Mutation>`. Every one of those is a
one-line C# class in `Scripting/`:

```csharp
public class Raven_ModDisintegration : ModImprovedMutationBase<Disintegration> { }
```

36 such scripts exist, one per mutation. The part's `Tier` attribute is the mutation level granted.

**Physical vs mental scaling (2.2 change):** mental mutations keep scaling with Ego even when
granted by a chip; physical mutations do not scale at all. To compensate, chips granting
*physical* mutations give **3 / 6 / 10** levels instead of the **2 / 4 / 6** that mental chips give.
Chipsets follow the same split: **1 / 2 / 3** for mental, **2 / 4 / 6** for physical.

### 3.3 The 12 affinity families

Each family has 3 single-mutation chips and 1 chipset, each at 3 grades
(**basic** → **upgraded** → **perfected**) = 12 items per family, **144 chips total** (plus the base blueprint).

| Family | Mutation A | Mutation B | Mutation C |
|---|---|---|---|
| **Force** | Disintegration | Stunning Force | Force Bubble |
| **Fire** | Kindle | Flaming Ray *(physical)* | Pyrokinesis |
| **Ice** | Frost Webs *(physical)* | Freezing Ray *(physical)* | Cryokinesis |
| **Lightning** | Electromagnetic Pulse *(physical)* | Electrical Generation *(physical)* | Phasing *(physical)* |
| **Light** | Photosynthetic Skin *(physical)* | Light Manipulation | Teleportation |
| **Acid** | Corrosive Gas Generation *(physical)* | Confusion | Acid Slime Glands *(physical)* |
| **Blood** | Syphon Vim | Adrenal Control *(physical)* | Regeneration *(physical)* |
| **Mental** | Sunder Mind | Domination | Mass Mind |
| **Temporal** | Space-Time Vortex | Time Dilation | Temporal Fugue |
| **Neutral Mind** | Mental Mirror | Teleport Other | Force Wall |
| **Neutral Body** | Heightened Quickness *(physical)* | Ego Projection (`Raven_ModWillForce`) | Heightened Hearing *(physical)* |
| **Neutral Spirit** | Clairvoyance | Psychometry | Precognition |

Item tiers and prices are uniform across all families:

| Grade | Single chip: item tier / value / mutation level | Chipset: item tier / value / mutation levels |
|---|---|---|
| basic (`Simple`) | Tier 4 · 20 · **2** (mental) or **3** (physical) | Tier 6 · 20 · **1** / **2** |
| upgraded (`Improved`) | Tier 6 · 40 · **4** / **6** | Tier 7 · 40 · **2** / **4** |
| perfected (`Advanced`) | Tier 8 · 60 · **6** / **10** | Tier 8 · 60 · **3** / **6** |

> ✅ **All 144 chips can drop.** Upstream 2.2 shipped only *the first chip of each family* plus that
> family's chipset in `Raven_Chips Tier 1/2/3` — 24 entries where 48 were needed — so chips B and C
> of all 12 families appeared nowhere in `PopulationTables.xml`. Since no chip carries a
> `TinkerItem` part, they could not be built either, leaving **half the flagship catalogue
> wish-only**. Each tier table now holds **48** entries (#6, fixed in #36).
>
> The 18 `StartingGear_*` tables still hand out only first-of-family chips and chipsets, which is
> deliberate — a Psionic Adept's opening kit is meant to be the entry point of its affinity, not a
> sample of the whole catalogue.
>
> Chips remain **drop-only by design**: no `TinkerItem` anywhere in `PsionicChips.xml`. That is what
> lets the *psionic chips in loot* option close the supply completely rather than leaving tinkering
> as a way in — see §13.

### 3.4 Chip drop rates

Chips enter the loot pool through the **Artifact** tables (see §7.3):

| Table | Chip table used | Weight |
|---|---|---|
| Artifact 3, 4, 5 | `Raven_Chips Tier 1` | 10 / 110 |
| Artifact 6, 7 | `Raven_Chips Tier 2` | 10 / 110 |
| Artifact 8 | `Raven_Chips Tier 3` | 10 / 110 |

The denominator is **110**, not 100, because the entry is *added* to vanilla's pool rather than
carved out of it. Vanilla's `Artifact N` group is a uniform 95 common / 5 rare across all six
tables — read from the game's own `PopulationTables.xml` — so the merged pool totals 110 and a
chip lands **9.09%** of the time. Under the pre-#34 replacement it was a flat 10%; see §7.3.

Within a chip table, single chips are weight 3 and chipsets weight 1 — so a chipset is a 1-in-4
result among that family, and each family is equally likely.

---

## 4. Skills (`Skills.xml`)

Six trees are edited. Nothing is removed; requirements and costs are retuned and one power is added.

Both halves are optional, under two separate toggles — **eased skill requirements** and **retuned
skill point costs**. They are split because their scopes differ: costs apply immediately, while
requirements need a restart. See §13.

| Tree | Change |
|---|---|
| **Axe** | Every power (Cleave, Charging Strike, Dismember, Hook and Drag, Decapitate, Berserk!) now accepts **Strength *or* Agility** for its attribute minimum. Thresholds unchanged: 19/19/21/23/25/29. |
| **Cudgel** | Same treatment — Bludgeon 17, Charging Strike 19, Conk 21, Backswing 23, Slam 25, Demolish 29, each **Strength or Agility**. |
| **Long Blade** | *Dueling Stance* Intelligence requirement **17 → 15**. *En Garde!* no longer needs both stats: it was Strength 29 **and** Agility 23 (either order); now it is **29 in Strength or Agility**. |
| **Multiweapon Fighting** | *Multiweapon Expertise* **23 → 21**, *Multiweapon Mastery* **27 → 25**. Upstream 2.2 also added **Akimbo** here; this fork removed it — see below. |
| **Cooking and Gathering** | *Butchery* and *Spicer* cost **50 → 100** each, offsetting the free Cooking and Gathering + Meal Preparation every genotype now starts with. |
| **Tinkering** | *Disassemble* cost **→ 0** (free with the tree). *Reverse Engineer* cost **100 → 200**. *Tinker I* Int **19 → 17**, *Tinker II* **23 → 21**, *Tinker III* **29 → 25**. |

> ✅ **Akimbo was removed from Multiweapon Fighting in #88** (closing #11), and the story is worth
> keeping because it is this repo's clearest demonstration that **`Class=` is an identifier**.
>
> Upstream 2.2 added Akimbo to Multiweapon Fighting under `Class="Pistol_Akimbo"` — the *same*
> implementation class as the Pistol tree's Akimbo. `SkillFactory.PowersByClass` holds one entry
> per class, and vanilla grants powers **by class**: the Gunslinger calling is
> `<skill Name="Pistol_Akimbo" />`. So the mod's power was served wherever the game asked for
> vanilla's, and Gunslingers silently got the wrong one.
>
> None of it was visible for years, because both powers were named "Akimbo" and rendered
> identically. It surfaced only when this fork renamed one of them while working on something else.
> Giving the mod's copy a distinct class fixed the Gunslinger but left a character who bought both
> holding the ability twice, with a skills screen that would not close — so the power was removed
> rather than shipped with a known way to spoil a run.
>
> Nothing is lost that cannot be had elsewhere: Akimbo is unchanged in the Pistol tree, where it has
> always lived, and Multiweapon Fighting keeps this mod's reduced requirements above.
> `docs/STYLEGUIDE.md` §1.0c carries the general rule.

> ℹ️ The 2.2 changelog notes that vanilla itself adopted Strength-or-Agility for Multiweapon
> Fighting, so only the **requirement reduction** there is still a mod change. The
> Strength-or-Agility rewrite is a genuine mod feature for **Axe** and **Cudgel**.

---

## 5. Item mods (`Mods.xml`)

One line, big consequence:

```xml
<mod Part="ModGigantic" Load="Merge" TinkerAllowed="true" />
```

**Gigantic becomes a tinkerable item mod.** You can now apply Gigantic to equipment yourself
rather than only finding it. Combined with the energy-cell notes below, Gigantic on a cell
doubles max charge and stacks with High Capacity.

---

## 6. Items

### 6.1 Counts by file

| File | New objects | Merged vanilla objects |
|---|---|---|
| `MeleeWeapons.xml` | 71 | 79 |
| `Armor.xml` | 61 | 38 |
| `RangedWeapons.xml` | 49 | 8 |
| `PsionicChips.xml` | 145 | 0 |
| `Cybernetics.xml` | 9 | 16 |
| `OtherEquipment.xml` | 7 | 16 |
| `Throwables.xml` | 0 | 51 |
| `Furniture.xml` | 4 | 0 |
| `Creatures.xml` | 2 | 1 |
| `Food.xml` | 0 | 2 |
| `Ammo.xml` | 20 (20 disabled) | 1 |
| **Total** | **368 active** | **214** |

### 6.2 Melee weapons

The mod's core structural change: **vanilla weapon families are completed across all 9 tiers
(0–8) and split into one-handed / two-handed variants with consistent stat rules.**

Conventions the mod follows:

- Two-handed variants get **+1 penetration** and a damage bump; one-handed variants keep vanilla pen.
- Tiers map to materials: **0 bronze · 1 iron · 2 steel · 3 carbide · 4 folded carbide · 5 fullerite · 6 crysteel · 7 flawless crysteel · 8 zetachrome**.
- Value doubles per tier: 5 / 10 / 20 / 40 / 80 / 160 / 320 / 640 / 1280.
- **Agility-scaling martial weapons** are a deliberate theme: vinereapers, halberds, rapiers, katanas and war hammers all use `Stat="Agility"` while keeping their tree's skill (Axe, Long Blades, Cudgel respectively).
- Vibro variants sit at tier 5, cost 300, take an energy cell, use 100 charge per swing, and set penetration equal to the defender's AV.


#### Greataxes (Axe, two-handed, Strength) — **new family**

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Bronze Greataxe | new | 0 | 1d2+1 | +1 | 1 | Strength | 5 | 6 | yes |
| Iron Greataxe | new | 1 | 1d3+1 | +1 | 2 | Strength | 10 | 5 | yes |
| Vibro Greataxe | new | 5 | 1d6+3 | +0 | 0 | (inh) | 300 | 6 | yes |
| Crysteel Greataxe | new | 6 | 1d8+5 | +1 | 7 | (inh) | 320 | 5 | yes |
| Flawless Crysteel Greataxe | new | 7 | 1d9+5 | +1 | 8 | (inh) | 640 | 5 | yes |
| Zetachrome Greataxe | new | 8 | 1d10+6 | +1 | 9 | (inh) | 1200 | 4 | yes |

#### Halberds (Axe, two-handed, Agility) — **new family**

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Bronze Halberd | new | 0 | 1d2+1 | +1 | 1 | Agility | 5 | 7 | yes |
| Iron Halberd | new | 1 | 1d3+1 | +1 | 2 | Agility | 10 | 6 | yes |
| Steel Halberd | new | 2 | 1d4+2 | +1 | 3 | Agility | 20 | 6 | yes |
| Carbide Halberd | new | 3 | 1d5+2 | +1 | 4 | Agility | 40 | 8 | yes |
| Folded Carbide Halberd | new | 4 | 1d6+3 | +1 | 5 | Agility | 80 | 7 | yes |
| Fullerite Halberd | new | 5 | 1d7+3 | +1 | 6 | Agility | 160 | 9 | yes |
| Vibro Halberd | new | 5 | 1d6+3 | +0 | 0 | Agility | 300 | 7 | yes |

#### Vinereapers (Axe, one-handed, Agility) — vanilla family, completed to all tiers

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Bronze Vinereaper | new | 0 | 1d2 | +0 | 1 | Agility | 5 | 3 |  |
| Iron Vinereaper | merge | 1 | 1d3 | +0 | 2 | Agility | 10 | 2 |  |
| Steel Vinereaper | merge | 2 | 1d4 | +0 | 3 | Agility | 20 | 2 |  |
| Carbide Vinereaper | new | 3 | 1d5 | +0 | 4 | Agility | 40 | 4 |  |
| Folded Carbide Vinereaper | new | 4 | 1d6+1 | +0 | 5 | Agility | 80 | 3 |  |
| Fullerite Vinereaper | new | 5 | 1d7+1 | +0 | 6 | Agility | 160 | 5 |  |
| Vibro Vinereaper | new | 5 | 1d6+1 | +0 | 0 | Agility | 300 | 3 |  |
| Crysteel Vinereaper | new | 6 | 1d8+2 | +0 | 7 | Agility | 320 | 3 |  |
| Flawless Crysteel Vinereaper | new | 7 | 1d9+2 | +0 | 8 | Agility | 640 | 3 |  |
| Zetachrome Vinereaper | new | 8 | 1d10+3 | +0 | 9 | Agility | 1280 | 2 |  |

#### Katanas (Long Blades, two-handed, Agility) — **new family**

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Bronze Katana | new | 0 | 1d6 | +1 | 1 | Agility | 5 | 6 | yes |
| Iron Katana | new | 1 | 1d8 | +1 | 2 | Agility | 10 | 5 | yes |
| Steel Katana | new | 2 | 1d10 | +1 | 3 | Agility | 20 | 5 | yes |
| Carbide Katana | new | 3 | 1d12 | +1 | 4 | Agility | 40 | 7 | yes |
| Folded Carbide Katana | new | 4 | 2d6+1 | +1 | 5 | Agility | 80 | 6 | yes |
| Fullerite Katana | new | 5 | 2d8+1 | +1 | 6 | Agility | 160 | 9 | yes |
| Vibro Katana | new | 5 | 2d8 | +0 | 0 | Agility | 300 | 6 | yes |
| Crysteel Katana | new | 6 | 2d8+2 | +1 | 7 | Agility | 320 | 4 | yes |
| Flawless Crysteel Katana | new | 7 | 2d10+1 | +1 | 8 | Agility | 640 | 4 | yes |
| Zetachrome Katana | new | 8 | 2d12+1 | +1 | 9 | Agility | 1280 | 3 | yes |

#### Rapiers (Long Blades, one-handed, Agility) — **new family**

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Bronze Rapier | new | 0 | 1d3 | +0 | 1 | Agility | 5 | 3 |  |
| Iron Rapier | new | 1 | 1d4 | +0 | 2 | Agility | 10 | 3 |  |
| Steel Rapier | new | 2 | 1d6 | +0 | 3 | Agility | 20 | 3 |  |
| Carbide Rapier | new | 3 | 1d8 | +0 | 4 | Agility | 40 | 4 |  |
| Folded Carbide Rapier | new | 4 | 1d10 | +0 | 5 | Agility | 80 | 3 |  |
| Fullerite Rapier | new | 5 | 1d12 | +0 | 6 | Agility | 160 | 4 |  |
| Vibro Rapier | new | 5 | 1d10 | +0 | 0 | Agility | 300 | 3 |  |
| Crysteel Rapier | new | 6 | 2d6+1 | +0 | 7 | Agility | 320 | 2 |  |
| Flawless Crysteel Rapier | new | 7 | 2d8+1 | +0 | 8 | Agility | 640 | 2 |  |
| Zetachrome Rapier | new | 8 | 2d8+2 | +0 | 9 | Agility | 1280 | 2 |  |

#### Wristblades / arm daggers (Short Blades) — **new family**

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Bronze Wristblade | new | 0 | 1 | +0 | 1 | (inh) | 15 | 1 |  |
| Iron Wristblade | new | 1 | 1d2 | +0 | 2 | (inh) | 25 | 1 |  |
| Steel Wristblade | new | 2 | 1d3 | +0 | 3 | (inh) | 35 | 1 |  |
| Carbide Wristblade | new | 3 | 2d2 | +0 | 4 | (inh) | 55 | 2 |  |
| Fullerite Wristblade | new | 5 | 2d3+1 | +0 | 6 | (inh) | 105 | 3 |  |
| Vibro Wristblade | new | 5 | 1d4+1 | +0 | 0 | (inh) | 300 | 1 |  |
| Crysteel Wristblade | new | 6 | 2d4 | +0 | 7 | (inh) | 320 | 1 |  |
| Flawless Crysteel Wristblade | new | 7 | 2d4+1 | +0 | 8 | (inh) | 640 | 1 |  |
| Zetachrome Wristblade | new | 8 | 2d6 | +0 | 9 | (inh) | 1200 | 1 |  |

#### Maces, one-handed (Cudgel, Strength)

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Mace2 | merge | 0 | 1d3 | +0 | 1 | (inh) | 5 | 5 |  |
| Iron Mace | new | 1 | 1d4 | +0 | 2 | (inh) | 10 | 4 |  |
| Carbide Mace | new | 3 | 2d4 | +0 | 4 | (inh) | 40 | 6 |  |
| Folded Carbide Mace | new | 4 | 2d4+1 | +0 | 5 | (inh) | 80 | 5 |  |
| Fullerite Mace | new | 5 | 2d6 | +0 | 6 | (inh) | 160 | 7 |  |
| Zetachrome Mace | new | 8 | 3d6+2 | +0 | 9 | (inh) | 1280 | 3 |  |

#### Maces, two-handed (Cudgel, Strength) — **new family**

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Bronze Maceth | new | 0 | 2d2 | +1 | 1 | (inh) | 5 | 8 | yes |
| Iron Maceth | new | 1 | 2d2+1 | +1 | 2 | (inh) | 10 | 7 | yes |
| Steel Maceth | new | 2 | 3d2 | +1 | 3 | (inh) | 20 | 7 | yes |
| Carbide Maceth | new | 3 | 3d4 | +1 | 4 | (inh) | 40 | 9 | yes |
| Folded Carbide Maceth | new | 4 | 3d4+1 | +1 | 5 | (inh) | 80 | 8 | yes |
| Crysteel Maceth | new | 6 | 3d6+1 | +1 | 7 | (inh) | 320 | 6 | yes |
| Flawless Crysteel Maceth | new | 7 | 5d4+2 | +1 | 8 | (inh) | 640 | 6 | yes |
| Zetachrome Maceth | new | 8 | 5d6+2 | +1 | 9 | (inh) | 1280 | 5 | yes |

#### War hammers (Cudgel, Agility)

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Bronze War Hammer | new | 0 | 1d3 | +0 | 1 | Agility | 5 | 4 |  |
| Bronze War Hammerth | new | 0 | 2d2 | +1 | 1 | Agility | 5 | 7 | yes |
| Iron War Hammerth | new | 1 | 2d2+1 | +1 | 2 | Agility | 10 | 6 | yes |
| Steel War Hammer | merge | 2 | 2d2 | +0 | 3 | Agility | 20 | 3 |  |
| Steel War Hammerth | merge | 2 | 3d2 | +1 | 3 | Agility | 20 | 6 |  |
| Crysteel War Hammer | new | 6 | 2d6+1 | +0 | 7 | Agility | 320 | 3 |  |
| Flawless Crysteel War Hammer | new | 7 | 3d4+2 | +0 | 8 | Agility | 640 | 3 |  |

#### Greathammers (Cudgel, Agility)

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Fullerite Greathammer | new | 5 | 3d6 | +1 | 6 | Agility | 160 | 9 |  |

#### Greatswords (Long Blades)

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Vibro Greatsword | new | 5 | 2d8 | +0 | 0 | (inh) | 300 | 6 | yes |

#### Other new melee weapons

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Vibro Battle Axe | new | 5 | 1d6+1 | +0 | 0 | (inh) | 300 | 4 | |

The full vibro set added by the mod is: **vibro battle axe, vibro greataxe, vibro vinereaper,
vibro halberd, vibro greatsword, vibro rapier, vibro katana, vibro wristblade** (8 weapons,
all tier 5, all 300 value, all `ChargeUse=100`, all tinkerable at bits `0015`, all with
`Mods="AxeMods,BladeMods,WeaponMods,CommonMods,ElectronicsMods"`). None of them appear in any
population table — they are tinker-only.

#### Rebalanced vanilla melee lines (merge-only, no new blueprint)

The mod also retunes the vanilla **Long Sword**, **Dagger/Short Blade**, **Battle Axe**, and
**Cudgel** progressions — mostly weight, value, and damage-die smoothing so the new families
line up with them. Notable base-object edits: `BaseAxe` weight → 3, `BaseLongBlade` weight → 2,
`BaseDagger` weight → 1 (and `Stat="Agility"` on the dagger bases and both relic-dagger bases).

Two-handed vanilla long swords received a substantial damage lift (e.g. Long Sword2th 1d8,
Steel Long Swordth 1d10, Long Sword3th 1d12, Long Sword8th 2d12+1).

> ⚠️ **Likely typo:** `Cudgel6th` (tier 6 two-handed war hammer) has `MaxStrengthBonus="11"`.
> Every other tier-6 weapon in the mod uses 7. This lets it scale off ~4 extra Strength.

> 🗒️ **Dormant content:** four blueprints are commented out in `MeleeWeapons.xml` (two blocks,
> both headed *"rework these or remove them"*): `Raven_Vibro Mace`, `Raven_Two-Handed Vibro Mace`
> ("vibro flail"), `Raven_Vibro War Hammer`, and `Raven_Two-Handed Vibro War Hammer`
> ("vibro greathammer").

### 6.3 Armor

New concepts introduced:

- **Vambraces** — a full tier 0–8 line of `Arm`-slot armor built on vanilla's `BaseArmlet`. Vanilla only puts bucklers in that slot, so this is the first real armor line for arms.
- **Greatshields** — a full tier 0–8 line of two-handed-feel `Hand` shields with the highest AV in the game (3 → 10) at a DV cost.
- **Weave cloaks** at every tier (bronzeweave → zetachromeweave), filling out the vanilla ironweave cloak.
- **Nanoweave** and **Flexi** gear — a tier 5–6 "light armor" alternative that trades AV for **positive DV**, which vanilla metal armor never gives.
- **Bio-scanner mask** and **mutating mask** — two `Face`-slot artifacts.
- **Reinforced suspension** — `Tread`-slot accessory for the mechanical-legs build.


#### Feet

| Blueprint | New? | Tier | Slot | AV | DV | Resists (H/C/A/E) | Value | Weight |
|---|---|---|---|---|---|---|---|---|
| Bronze Boots | new | 0 | Feet | 2 | -2 | — | 5 | 8 |
| Iron Boots | new | 1 | Feet | 2 | -1 | — | 10 | 7 |
| Chain Boots | merge | 2 | Feet | 2 | -2 | — | 20 | 6 |
| Steel Boots | merge | 2 | Feet | 3 | -3 | — | 20 | 7 |
| Carbide Boots | merge | 3 | Feet | 3 | -2 | — | 40 | 9 |
| Flawless Crysteel Boots | merge | 3 | Feet | 4 | 0 | 5/5/5/5 | 640 | 6 |
| Folded Carbide Boots | new | 4 | Feet | 3 | -1 | — | 80 | 8 |
| Fullerite Boots | merge | 5 | Feet | 4 | -4 | — | 160 | 10 |
| Flexiboots | new | 5 | Feet | 1 | 3 | — | 75 | 2 |
| Crysteel Boots | merge | 6 | Feet | 4 | -2 | 5/5/5/5 | 320 | 6 |
| Nanoweave Boots | new | 6 | Feet | 3 | 1 | — | 300 | 3 |
| Zetachrome Pumps | merge | 8 | Feet | 6 | 0 | 6/6/6/6 | 1280 | 5 |

#### Hands

| Blueprint | New? | Tier | Slot | AV | DV | Resists (H/C/A/E) | Value | Weight |
|---|---|---|---|---|---|---|---|---|
| Bronze Gauntlets | new | 0 | Hands | 2 | -2 | — | 5 | 8 |
| Iron Gauntlets | new | 1 | Hands | 2 | -1 | — | 10 | 7 |
| Steel Gauntlets | merge | 2 | Hands | 3 | -3 | — | 20 | 7 |
| Carbide Gauntlets | merge | 3 | Hands | 3 | -2 | — | 40 | 9 |
| Folded Carbide Gauntlets | new | 4 | Hands | 3 | -1 | — | 80 | 8 |
| Fullerite Gauntlets | merge | 5 | Hands | 4 | -4 | — | 160 | 10 |
| Flexigloves | new | 5 | Hands | 1 | 2 | — | 125 | 2 |
| Crysteel Gauntlets | merge | 6 | Hands | 4 | -2 | 5/5/5/5 | 320 | 6 |
| Nanoweave Gloves | new | 6 | Hands | 2 | 1 | — | 300 | 3 |
| Flawless Crysteel Gauntlets | merge | 7 | Hands | 4 | 0 | 5/5/5/5 | 640 | 6 |
| Zetachrome Gloves | merge | 8 | Hands | 6 | 0 | 5/5/5/5 | 1280 | 5 |
| Chain Gauntlets | merge | - | Hands | 2 | -1 | — | - | 6 |

#### Head

| Blueprint | New? | Tier | Slot | AV | DV | Resists (H/C/A/E) | Value | Weight |
|---|---|---|---|---|---|---|---|---|
| Bronze Helmet | new | 0 | Head | 2 | -2 | — | 5 | 10 |
| Iron Helmet | new | 1 | Head | 2 | -1 | — | 10 | 9 |
| Chain Coif | merge | 2 | Head | 2 | -1 | — | 20 | 6 |
| Steel Helmet | merge | 2 | Head | 3 | -3 | — | 20 | 9 |
| Carbide Helmet | new | 3 | Head | 3 | -2 | — | 40 | 11 |
| Folded Carbide Helmet | new | 4 | Head | 3 | -1 | — | 80 | 10 |
| Fullerite Armet | merge | 5 | Head | 4 | -4 | — | 160 | 12 |
| Flexihelmet | new | 5 | Head | 1 | 2 | — | 125 | 2 |
| Crysteel Coronet | merge | 6 | Head | 4 | -2 | 5/5/5/5 | 320 | 8 |
| Nanoweave Helmet | new | 6 | Head | 2 | 1 | — | 300 | 3 |
| Flawless Crysteel Coronet | merge | 7 | Head | 4 | 0 | 5/5/5/5 | 640 | 8 |
| Zetachrome Apex | merge | 8 | Head | 6 | 0 | 6/6/6/6 | 1280 | 7 |

#### Body

| Blueprint | New? | Tier | Slot | AV | DV | Resists (H/C/A/E) | Value | Weight |
|---|---|---|---|---|---|---|---|---|
| Bronze Plate Armor | new | 0 | Body | 3 | -3 | — | 8 | 24 |
| Iron Plate Armor | new | 1 | Body | 3 | -1 | — | 16 | 21 |
| Chain Mail | merge | 2 | (inh) | - | - | — | 32 | 18 |
| Steel Plate Mail | merge | 2 | Body | 4 | -4 | — | 32 | 21 |
| Carbide Plate Armor | merge | 3 | Body | 4 | -2 | — | 64 | 27 |
| Folded Carbide Plate Armor | new | 4 | Body | 6 | -4 | — | 128 | 24 |
| Fullerite Flake Armor | merge | 5 | Body | 4 | -2 | 12/12/3/3 | 256 | 30 |
| Fullerite Plate Mail | merge | 5 | Body | 6 | -2 | — | 256 | 36 |
| Crysteel Shardmail | merge | 6 | Body | 8 | -4 | — | 512 | 18 |
| Flawless Crysteel Shardmail | merge | 7 | Body | 8 | -2 | 9/9/9/9 | 1024 | 18 |
| Zetachrome Lune | merge | 8 | Body | 10 | -2 | 10/10/10/10 | 2048 | 15 |

#### Back (cloaks)

| Blueprint | New? | Tier | Slot | AV | DV | Resists (H/C/A/E) | Value | Weight |
|---|---|---|---|---|---|---|---|---|
| Bronzeweave Cloak | new | 0 | Back | 1 | -1 | — | 5 | 4 |
| Ironweave Cloak | merge | 1 | Back | 1 | 0 | — | 10 | 3 |
| Steelweave Cloak | new | 2 | Back | 2 | -2 | — | 20 | 3 |
| Carbideweave Cloak | new | 3 | Back | 2 | -1 | — | 5 | 6 |
| Folded Carbideweave Cloak | new | 4 | Back | 2 | 0 | — | 80 | 5 |
| Flexicloak | new | 5 | Back | 1 | 2 | — | 125 | 2 |
| Fulleriteweave Cloak | new | 5 | Back | 3 | -2 | — | 160 | 6 |
| Crysteelweave Cloak | new | 6 | Back | 3 | -3 | 6/6/6/6 | 320 | 3 |
| Nanoweave Cloak | new | 6 | Back | 2 | 1 | — | 300 | 3 |
| Flawless Crysteelweave Cloak | new | 7 | Back | 3 | -1 | 6/6/6/6 | 640 | 3 |
| Zetachromeweave Cloak | new | 8 | Back | 3 | 0 | 6/6/6/6 | 1280 | 2 |
| Portable Beehive | merge | - | Back | 0 | 1 | — | - | - |

#### Arm (vambraces — new slot usage)

| Blueprint | New? | Tier | Slot | AV | DV | Resists (H/C/A/E) | Value | Weight |
|---|---|---|---|---|---|---|---|---|
| Bronze Vambrace | new | 0 | Arm | 1 | -1 | — | 4 | 4 |
| Iron Vambrace | new | 1 | Arm | 1 | 0 | — | 8 | 3 |
| Steel Vambrace | new | 2 | Arm | 2 | -2 | — | 16 | 3 |
| Carbide Vambrace | new | 3 | Arm | 2 | -1 | — | 32 | 5 |
| Folded Carbide Vambrace | new | 4 | Arm | 2 | 0 | — | 64 | 4 |
| Fullerite Vambrace | new | 5 | Arm | 3 | -3 | — | 128 | 6 |
| Crysteel Vambrace | new | 6 | Arm | 3 | -2 | 5/5/5/5 | 256 | 3 |
| Flawless Crysteel Vambrace | new | 7 | Arm | 3 | -1 | 5/5/5/5 | 512 | 3 |
| Zetachrome Vambrace | new | 8 | Arm | 3 | 0 | 6/6/6/6 | 1024 | 2 |

#### Face

| Blueprint | New? | Tier | Slot | AV | DV | Resists (H/C/A/E) | Value | Weight |
|---|---|---|---|---|---|---|---|---|
| Bio Scanner Mask | new | 5 | Face | 0 | 0 | — | 60 | 5 |
| Mutating Mask | new | 8 | Face | 1 | 1 | — | 1000 | 5 |
| VISAGE | merge | - | (inh) | - | - | — | - | - |

#### Tread

| Blueprint | New? | Tier | Slot | AV | DV | Resists (H/C/A/E) | Value | Weight |
|---|---|---|---|---|---|---|---|---|
| Reinforced Suspension | new | 3 | Tread | 0 | 2 | — | 25 | 5 |

#### Bucklers (Arm slot)

| Blueprint | New? | Tier | Slot | AV | DV | Value | Weight |
|---|---|---|---|---|---|---|---|
| Bronze Buckler | new | 0 | Arm | 1 | -1 | 5 | 4 |
| Iron Buckler | merge | 1 | Arm | 1 | 0 | 10 | 3 |
| Steel Buckler | merge | 2 | Arm | 2 | -1 | 20 | 3 |
| Carbide Buckler | new | 3 | Arm | 2 | 0 | 40 | 5 |
| Folded Carbide Buckler | new | 4 | Arm | 3 | -2 | 80 | 4 |
| Fullerite Buckler | new | 5 | Arm | 3 | -1 | 160 | 6 |
| Crysteel Buckler | new | 6 | Arm | 3 | 0 | 320 | 3 |
| Flawless Crysteel Buckler | new | 7 | Arm | 4 | -3 | 640 | 3 |
| Zetachrome Buckler | new | 8 | Arm | 4 | -1 | 1280 | 2 |

#### Shields (Hand slot)

| Blueprint | New? | Tier | Slot | AV | DV | Value | Weight |
|---|---|---|---|---|---|---|---|
| Bronze Shield | new | 0 | Hand | 2 | -2 | 5 | 8 |
| Iron Shield | new | 1 | Hand | 2 | -1 | 10 | 7 |
| Steel Shield | merge | 2 | (inh) | - | - | 20 | 7 |
| Carbide Shield | merge | 3 | Hand | 4 | -2 | 40 | 10 |
| Folded Carbide Shield | new | 4 | Hand | 5 | -3 | 80 | 9 |
| Fullerite Shield | merge | 5 | Hand | 5 | -2 | 160 | 12 |
| Crysteel Shield | merge | 6 | Hand | 6 | -2 | 320 | 6 |
| Flawless Crysteel Shield | merge | 7 | Hand | 7 | -2 | 640 | 6 |
| Zetachrome Shield | new | 8 | Hand | 8 | -1 | 1280 | 5 |

#### Greatshields — **new family** (Hand slot)

| Blueprint | New? | Tier | Slot | AV | DV | Value | Weight |
|---|---|---|---|---|---|---|---|
| Bronze Greatshield | new | 0 | Hand | 3 | -3 | 5 | 11 |
| Iron Greatshield | new | 1 | Hand | 3 | -2 | 10 | 10 |
| Steel Greatshield | new | 2 | Hand | 4 | -3 | 20 | 10 |
| Carbide Greatshield | new | 3 | Hand | 5 | -3 | 40 | 13 |
| Folded Carbide Greatshield | new | 4 | Hand | 6 | -3 | 80 | 12 |
| Fullerite Greatshield | new | 5 | Hand | 7 | -3 | 160 | 15 |
| Crysteel Greatshield | new | 6 | Hand | 8 | -3 | 320 | 9 |
| Flawless Crysteel Greatshield | new | 7 | Hand | 9 | -3 | 640 | 9 |
| Zetachrome Greatshield | new | 8 | Hand | 10 | -2 | 1280 | 7 |

#### Notable armor artifacts

**Bio-scanner mask** (tier 5, 60 value, Face) — energy-cell powered visor that sets the
`BioScannerEquipped` property, giving creature readouts. 5-turn boot sequence, complexity 5,
tinkerable (bits `0005`), accepts a Solar Cell by default.

**Mutating mask** (tier 8, 1000 value, Face, AV 1 / DV 1) — a `GasMask` with Power 10 that also
grants **+100 reputation with 50 factions simultaneously** (Antelopes through Worms — effectively
every faction in the game including Joppa, Kyakukya, Barathrumites, Mechanimists, Templar, Girsh,
Consortium and Mamon). Flavor: the visage takes the appearance of whoever looks at you.

**Reinforced suspension** (tier 3, `Tread`) — +2 DV, -15 carry weight penalty, `Role="Uncommon"`, tinkerable.

> ⚠️ **Two data bugs found in `Armor.xml`:**
> - `Flawless Crysteel Boots` has `<tag Name="Tier" Value="3" />`. It should be 7 (vanilla value, and its price is 640 = tier-7 price). As shipped it will roll on tier-3 loot pools and gets tier-3 mod capacity.
> - `Raven_Carbideweave Cloak` has `Commerce Value="5"`. The weave-cloak curve is 5/10/20/**40**/80/160/320/640/1280 — carbideweave should be 40.

### 6.4 Ranged weapons

#### Psionic pistols & rifles — new family (18 weapons)

Two new base blueprints, `Raven_Base Psionic Pistol` and `Raven_Base Psionic Rifle`, both tier 3,
energy-cell powered, tinkerable (bits `0003`), complexity 3, with `UnknownPistol`/`UnknownRifle`
examiner alternates.

| | Pistol | Rifle |
|---|---|---|
| Skill | Pistol | Rifle |
| Charge per shot | 50 | 100 |
| Value | 60 | 120 |
| Weight | 4 | 10 (two-slot) |
| Fire sound | `pistol_laser` | `laser_medium_1` |

Nine elemental variants of each:

| Variant | Display name | Pistol pen / dmg | Rifle pen / dmg | Special |
|---|---|---|---|---|
| Disintegration | disintegrating psionic … | 5 / 1d6 | 7 / 1d6 | `Disintegrate`, penetrates creatures |
| Perception | mindflaying psionic … | 5 / 1d6 | 7 / 1d6 | `Mental Psionic` damage |
| Ice | hyperborean psionic … | 4 / 1d8 | 6 / 1d8 | `Cold`, -3d20 (pistol) / -3d40 (rifle) temperature |
| Fire | conflagrating psionic … | 4 / 1d8 | 6 / 1d8 | +3d20 / +3d40 temperature. Pistol is `Heat Fire`; **rifle is `Heat` only** — likely an oversight |
| Lightning | fulminating psionic … | 4 / 1d8 | 6 / 1d8 | `Electric` |
| Acid | corrosive psionic … | 4 / 1d8 | 6 / 1d8 | `Acid` |
| Blood | sanguine psionic … | 3 / 1d10 | 5 / 1d10 | `Exsanguination` + **vampiric** (80–100% of damage healed, `Reduction=1d3-1`, cap 1d10+10, living targets only, reality-distortion based) |
| Light | refulgent psionic … | 3 / 1d10 | 5 / 1d10 | `Light` |
| Temporal | astral psionic … | 5 / 1d6 | 7 / 1d6 | `Cosmic` + **omniphase** (hits phased targets) |

> ⚠️ Both psionic bases carry `Mods="…RifleMods,ElectronicsMods,BeamWeaponMods"`. The **pistol**
> base inherits `BaseRifle` and lists `RifleMods` rather than `PistolMods` — likely an oversight
> that blocks pistol-specific mods on the psionic pistols.

#### Conventional guns — new (6 weapons)

| Blueprint | Tier | Skill | Shots/action | Ammo | Accuracy | Range inc. | Value | Notes |
|---|---|---|---|---|---|---|---|---|
| Fine-tuned handgun | 6 | Pistol | 2 (2 ammo) | 10 slugs | **1** (near-perfect) | 1 | 600 | Projectile pen 8 / 1d8. Turret name "miniature burstfire turret" |
| Modified handcannon | 5 | Pistol | 8 (1 ammo) | 4 shotgun shells | 30 | 12 | 400 | Fires shotgun shells from a handcannon; pellets pen 4 / 1d2 |
| Drum shotgun | 3 | Rifle | 24 (4 ammo, 6/anim) | 20 shells | 36 | 6 | 75 | `NoWildfire`, two-slot, weight 16 |
| Compact flamethrower | (inherits) | Heavy | — | 16 dram liquid | — | — | — | Occupies **both Missile Weapon slots** instead of hands |
| Cryocannon | 5 | Heavy Weapons | 1 | energy cell, 2000 charge | 0 | — | 750 | 1d8 `Cold NonPenetrating`, **-300 temperature** on hit and on entering |
| Net gun | 5 | Rifle | 1 | energy cell, 1000 charge | — | 12 | 130 | 1d4 `Electric NonPenetrating` + deploys a **Stasisfield** (radius 1, duration 1d3+3). Also a radius-8 light source while charged |

#### Merged vanilla ranged weapons

| Blueprint | Change |
|---|---|
| Musket | Weight → 12, now two-slot |
| Nullray Pistol | Charge use → 500; projectile → **1d12+4 Vorpal** |
| Borderlands Revolver | Value → 25 |
| Ruin of House Isner | Mods now include `MagazineMods` |
| Chain Pistol | Value → 100 |
| Laser Pistol | Value → 250 |
| Laser Rifle | Value → 550 |

### 6.5 Cybernetics

#### New implants

| Implant | Cost | Slots | Effect | Weight |
|---|---|---|---|---|
| **Air filtration system** | 3 | Body | `GasMask` Power 100 — **immune to gas attacks** | 2 |
| **Steel dermal plating** | 1 | Body, Head, Back | +1 AV | 6 |
| **Crysteel dermal plating** | 3 | Body, Head, Back | +3 AV | 12 |
| **Zetachrome dermal plating** | 4 | Body, Head, Back | +4 AV | 16 |
| **Omni pass** | 2 | Hands, Feet, Body, Back, Face, Arm, Head | **Walk through forcefields and unlock any door** (`DoorUnlocker:1` + `CyberneticsForcefieldNullifier`). Tagged `StartingCybernetic:General` | 0 |
| **Steel hand bones** | 1 | Hands | Fists deal **1d5** (`Raven_SteelFist`, tier 3) | 10 |
| **Zetachrome hand bones** | 8 | Hands | Fists deal **3d6** (`Raven_ZetachromeFist`, tier 8, `Zetachrome` part) | 10 |

Plus the two supporting fist weapons (`Raven_SteelFist`, `Raven_ZetachromeFist`), both `MaxStrengthBonus="999"`.

#### Merged vanilla implants

| Implant | Change |
|---|---|
| Carbide dermal plating (`DermalPlating`) | Renamed to **carbide** dermal plating, cost **2**, +2 AV (was the generic 1-point/+1) |
| Crysteel hand bones | Now cost **6**, value 360, complexity 6, weight 10, **3d4** fist damage |
| Fullerite hand bones / fist | **2d5** fist damage |
| Beautiful Visage / Cherubic Visage | **+2 Ego** each (stat modifier added) |
| Dopamine Synth | **+2 Willpower** |
| Dermal Insulation | +10 to all four elemental resistances |
| High-grade Dermal Insulation | Cost **4**, **+20** to all four resistances, complexity 5, value 240, slots Body/Head/Back |
| Hyper-elastic ankle tendons | +10 movespeed |
| Ultra-elastic ankle tendons | +20 movespeed |
| Motorized treads | `SaveModifier` +6 vs Move, Knockdown, Knockback, Restraint, Drag (EMP-sensitive, tech-scannable) |
| Optical multiscanner | Cost **4**, complexity 5, value 240 |
| Air current microsensor, Nocturnal apex, Rapid release finger flexors | New custom tiles and color strings |

### 6.6 Other equipment

#### Energy cells — new

| Cell | Tier | Max charge | Recharge | Value | Tinker bits |
|---|---|---|---|---|---|
| **Advanced chem cell** | 5 | 50,000 | — | 300 | `0014` |
| **Dark matter cell** | 8 | **500,000** | — | 300 | `0047` |
| **Solar cell array** | 4 | 10,000 | 25/turn in sunlight | 150 | `0023` |
| **Solar cell nexus** | 7 | 50,000 | 50/turn in sunlight | 225 | `0025` |

For reference, the mod's own notes record the vanilla baseline: chem cell 10,000 (T1);
fidget 2,500 (T1, 2/20 per turn out of/in combat); solar 2,500 (T2, 10/turn); nuclear 100,000 (T7);
antimatter 200,000 (T8); and the liquid-fuelled cells — lead-acid 4,000 (500/dram), combustion
6,000 (750/dram), thermoelectric 40,000 (5,000/dram), biodynamic 60,000 (7,500/dram).

So the solar array is 4× capacity / 2.5× recharge of a basic solar cell; the nexus is 20× / 5×
(or 5× / 2× versus the array). The advanced chem cell is 5× a chem cell, half a nuclear cell. The
dark matter cell is 10× the advanced chem cell, 5× a nuclear cell, 2.5× an antimatter cell.

**How cell mods interact** (from Mura's pinned feature list — useful context for retuning these):

| Mod | Effect |
|---|---|
| **Radio Powered** | Recharges (10 × Tier) per turn, up to (1 + Tier) max depth. Does **not** stack with Fidget/Solar recharge — only the highest rate applies. |
| **High Capacity** | Max charge × (14 + Tier) / 10. A tier-1 cell gets 1.5×, each tier adds 0.1, capping at **2.2× at tier 8**. |
| **Gigantic** | Doubles max charge, and **stacks** with High Capacity. (Mura never confirmed whether the stack is additive or multiplicative — worth testing, and note §5: this mod is what makes Gigantic tinkerable in the first place.) |

> ⚠️ The dark matter cell (500,000 charge) and the advanced chem cell (50,000 charge) are both
> priced at **300**. Given the mod's own doubling curve, the dark matter cell is drastically
> underpriced.

#### Other new items

| Item | Tier | Effect | Value |
|---|---|---|---|
| **Advanced hoversled** | 6 | `Backpack` **-100 carry weight**, worn "Floating Nearby", tinkerable (`00345`) | 400 |
| **Cybernetics credit pass** | — | `CyberneticsCreditWedge` worth **10 credits** | 1550 |
| **Large sphere of negative weight** | 8 | `Suspensor` at **200% force**, **0 charge use**, complexity 7, tinkerable (`00008`), trinket, `DisplayFullNameAsReward` | 100 |

#### Merged vanilla equipment

| Item | Change |
|---|---|
| `BaseRecoiler` | Renamed "basic recoiler"; now **programmable and reprogrammable**, 10,000 charge per use — every vanilla recoiler inherits this |
| `Programmable Recoiler` | **Vanilla object.** Charge use 10,000 → **5,000**, and `Reprogrammable` false → **true**, so the cheaper recoiler can now be re-imprinted. Custom description. *(Listed as a new object in earlier drafts of this file — it is not; see #29.)* |
| `Reprogrammable Recoiler` | **Vanilla object.** Charge use 30,000 → **2,500**. Custom description. |
| All 7 location recoilers (Joppa, Grit Gate, Six Day Stilt, Kyakukya, Golgotha, Bethesda Susa, Ezra) | Given `NameElide` values so their names render correctly under the new programmable system |
| Force bracelet | Charge use → 250 |
| Bottle | Weight 5, value 10, **1000 HP**, 100 in all four resistances, `Inorganic`, `ThermalInsulation` 1000, non-solid, immune to freezing/burning |
| Scrap | Weight → 0 |
| Strength exo | `Backpack` -60 carry weight |
| Waterskin / Oilskin | Recolored display names |
| Yuckwheat stem, Witchwood bark (`Food.xml`) | Weight → 0 |
| Chute crab claw (`Creatures.xml`) | Damage **1d3-1** (can now roll 0), Cudgel skill, Strength, Hand slot |

#### Throwables — pure price rebalance

All **51** grenade blueprints (sleep gas, poison gas, stun gas, acid gas, flashbang, heat, cold,
HE, EMP, normality gas, stasis, sunder, defoliant, fungicide, fire support, time dilation,
glitter — grades 1/2/3 each) are repriced to a flat **10 / 20 / 30** by grade. Nothing else about
them changes.

#### Furniture — new

| Blueprint | Inherits | Notes |
|---|---|---|
| `Raven_Empty Weapon Rack` | Chest | "on"-preposition container, tier 2, `HangingSupport`, `NoSparkingQuest` |
| `Raven_Empty Gun Rack` | ↑ | Recolored |
| `Raven_Empty Armor Rack` | Weapon Rack | Recolored |
| `Raven_Rusted Door` | Metal Door | Non-occluding, renders in dark |

### 6.7 Ammo — arrows and shells live, bullets still disabled

`ObjectBlueprints/Ammo.xml` was 524 lines with **every one of its 62 objects inside a single XML
comment** marked only *"removed temporarily"*. Mura pulled the file when a Qud change broke the
effects and the ammo degraded to plain ammo. #144 revived the arrows and #145 the shells; the
**20 bullet objects remain commented** for #146, which is a much larger reachability claim — 12
vanilla weapons plus 7 relic bases.

**The six effect arrows.** All are `Commerce Value="0.20"`, carry **no `TinkerItem`**, inherit
`BaseArrow`, and pair with a `BaseArrowProjectile` at `StrengthPenetration="1"` over `1d2` damage.
Those figures are vanilla's `Boomrose Arrow`, the only effect arrow the game ships.

| Displayed as | Blueprint | Payload | Shape | Its grenade |
|---|---|---|---|---|
| blaze arrow | `Raven_Blaze Arrow` | `TemperatureOnHit 250` | single target | thermal mk I is `ThermalGrenade 500`, **area** |
| cryo arrow | `Raven_Cryo Arrow` | `TemperatureOnHit -50` | single target | freeze mk I is `ThermalGrenade -400`, **area** |
| dream dew arrow | `Raven_Dream Dew Arrow` | `GasGrenade Density=20 GasObject=SleepGas` | area | sleep gas mk I is 40 |
| hulk honey arrow | `Raven_Hulk Honey Arrow` | `StickyOnHit Duration=6 SaveTarget=17` | single target | `CastNet` is 12 / 20 |
| starshell arrow | `Raven_Starshell Arrow` | `FlashbangGrenade Radius=1 Duration=1d3` | area | flashbang mk I is R2, 1d4+4 |
| stinger arrow | `Raven_Stinger Arrow` | `GasGrenade Density=20 GasObject=PoisonGas` | area | poison gas mk I is 40 |

Payloads sit at roughly half their mk I grenade, which is the ratio Boomrose keeps against a high
explosive grenade mk I (force 1,200 against 2,000; 1d6 against 4d6). `HEGrenade` takes no radius
attribute anywhere in the game, so Boomrose's lower force buys a smaller blast as well as weaker
damage — it is the same area part as the grenade, dialled down, which is what makes it a like-for-
like anchor for the gas and flashbang arrows.

**Blaze and cryo are asymmetric on purpose, because Qud implements heat and cold differently.**
Their grenades are `HeatGrenade1` at `TemperatureDelta="500"` and `ColdGrenade1` at `-400`, both
tier 1, and Mura's original ±400 matched them almost exactly. A creature starts at 25, freezes at
0, goes brittle at −100 and ignites at 350.

**Heat takes the honest half, 250.** Burning is threshold-gated *and* self-extinguishing: the
effect removes itself as soon as temperature falls back under `FlameTemperature`, and
`Burning.GetBurningAmount` keys damage to how far *above* that line the target sits.

| Degrees above 350 | Damage/turn |
|---|---|
| 0–100 | 1 |
| 101–300 | 1–2 |
| 301–500 | 2–3 |
| 501–700 | 3–4 |
| 701–900 | 4–5 |
| 901+ | 5–6 |

So the size of the hit sets the tick *and* the duration, and a small one is penalised twice —
barely igniting something is worth about 2 damage in total. At 250, two arrows put a target near
520 for roughly 20 turns, which is what one thermal grenade does to a single target.

**Cold takes −50, far below half,** because freezing has no damage tier — crossing −100 is a
binary immobilise. Halving the grenade moderates nothing: from 25, anything deeper than about
−125 is a one-shot disable, so −200 lands in the same place as −400.

−50 freezes on the third consecutive hit, and the arithmetic matters because the first attempt at
this number did not survive play-testing. `Physics.IsFrozen()` is `Temperature <= BrittleTemperature`
with no save and no roll, so it is pure accounting — but temperature returns to ambient by
`Math.Max(5, |diff| × 0.02)` every turn, and at these magnitudes the `0.02` term never reaches 5,
making it a flat **5 a turn**. Each hit nets −45 rather than −50, and every miss hands 5 back:

| After hit | Temp |
|---|---|
| 1 | −20 |
| 2 | −65 |
| 3 | **−115 → frozen** |

The original −35 needed four *consecutive* hits and measured at four to five in play, which is why
it moved. A single hit reaches −20, nowhere near the −100 line, so it stays clear of a one-shot
disable by a wide margin.

One caveat for both temperature arrows: `TemperatureOnHit` passes `Radiant: false`, and on that
branch resistance still applies — cold whenever the result lands below 25, heat whenever it lands
above 50. The glowpad these were tested against has `ColdResistance` 0 and `HeatResistance` 25, so
blaze igniting it in two hits is a figure measured against a *resistant* target.

Both stay on `TemperatureOnHit` rather than `ThermalGrenade`, single-target by design. Fire
already spreads through the game's own mechanics, so the blaze arrow reaches beyond what it hits
without an area part, and the cryo arrow is meant to be single-target. `ThermalGrenade` also
appears on six objects in the game and every one inherits `Grenade` — no projectile precedent,
unlike `HEGrenade`, `GasGrenade`, `FlashbangGrenade`, `SunderGrenade` and `DeploymentGrenade` —
so its failure mode on a projectile would be silent.

**None of them is craftable, and that follows a rule far wider than arrows.** Qud has exactly one
crafting system, and Tinkering is the **artifact** skill — it builds recovered old-world technology
and nothing else. No arrow is craftable, but neither is a dagger, a long sword, a battle axe, a
steel suit, a short bow or a compound bow:

| Craftable | Not craftable |
|---|---|
| Semi-Automatic Pistol, Combat Shotgun | Dagger, Steel Long Sword, Steel Battle Axe |
| Lead Slug, Shotgun Shell | every arrow, including `Boomrose Arrow` |
| Chem Cell, every grenade | Short Bow, Compound Bow, Steel Suit |
| **Turbow** | |

The Turbow is the tell: the only craftable bow in the game, and the only one with an `Examiner`
part — *"servos click on the wheeling groves and a miniature air turbine exaggerates the pull of
the bowstring."* An artifact that happens to be bow-shaped. Slugs and shells are craftable because
they are cartridges serving firearms, which are recovered tech in their own right.

Giving these arrows a recipe would not have filled a gap Freehold left; it would have put a stick
into the artifact system, which vanilla declines to do for every wooden and forged object it ships.
An earlier revision did exactly that, and also merged a `TinkerItem` onto vanilla's `Boomrose
Arrow`; both were reverted before release. Whether this fork should add a *mundane* crafting system
of its own — fletching, smithing, leatherwork — is #154.

**Reachability is therefore entirely the drop tables.** Each arrow is weight 2 in `Ammo 2`,
`Ammo 3` and `Ammo 4`, at Boomrose's own quantities (1, then 1d4, then 1d4) — so the set of six is
worth roughly what Boomrose alone is worth in those pools rather than six times as much. They stay
out of `Ammo 1`, where vanilla keeps Boomrose at weight 1 against wooden arrows' 100. Those tables
also feed merchant stock through `Tier1Wares`, `Tier2Wares` and `YurlWares`, so buying is a
reliable route rather than waiting on floor drops. See §7.

**Three of the nine were cut**: the vibro arrow (`Vorpal`, which vanilla grants only to the tier-7
Linear Cannon), the sunder arrow (flat `BasePenetration="10"`, above every vanilla arrow), and the
stasis arrow (omitted `IsRealityDistortionBased`, so normality would not have suppressed it).

**A fourth was replaced after release.** The quill arrow shipped in 2.3.0 **doing nothing**:
`BleedingOnHit` registers `WeaponHit` and `WieldedWeaponHit`, both raised on the melee path, and
`MissileWeapon` raises `ProjectileHit` instead. It flew, hit, dealt its `1d2`, and never bled
anything — with no error anywhere, which is why it survived a release. Found while working #145,
whose razor shell had the identical defect.

Bleeding is melee-only **by design**, not oversight: vanilla puts `BleedingOnHit` on exactly two
objects, `Lamprey Bite` and `Sharpened Polyp`, both natural melee weapons. So #201 changed the
payload rather than adding the mechanic in C#; whether the mod should own a bleeding-at-range part
is #210, and it needs charter rule 2's argument rather than arriving inside a bug fix.

The replacement is the **hulk honey arrow**, and `StickyOnHit` is the one payload for which being a
single projectile is an *advantage* — it was rejected for the takedown shell precisely because eight
pellets applied eight separate `Stuck` effects. It is also the only arrow that reaches every
anatomy: `Stuck` has no limb requirement, so it holds oozes and insects that `Prone` cannot touch,
and `Stuck.Apply` calls `Flight.Fall`, so it grounds fliers too.

Named for Qud's own sticky substance, which the game already models — `LiquidHoney` sets
`StickyWhenWet`, `StickyDuration = 12` and `StickySaveVs = "Honey Stuck Restraint"` — so the
substance on the tip explains the mechanic rather than decorating it, which is the naming rule
above. `Duration="6" SaveTarget="17"` is half the hold of `CastNet` and hulk honey itself (both 12 /
20), with the save midway between vanilla's light restraint (freezing liquid, 5 / 15) and its heavy
one. An arrow fires at bow range from a stack; a net must be closed with and thrown once.

Measured: an oddly-hued glowpad held for **~4.3 turns against the cap of 6**. Its Strength is 6, so
its modifier is −5 and `d20 − 5 ≥ 17` is unreachable — only a natural 20 frees it, and `Duration`
becomes the binding constraint. `CastNet` would hold the same target the full 12, so the arrow is
half a net in practice as well as on paper. `SaveTarget` governs the other end instead: a
Strength-16 target escapes in about two attempts.

**`Raven_Quill Arrow` is commented out rather than deleted**, so #210 can restore it verbatim — the
quillipede barb is the right fiction for bleeding and the wrong one for anything else, so the
replacement took a new blueprint instead of the name. Commenting out a blueprint that shipped is not
free: `GameObject.GetBlueprint` falls back to the generic `Object` blueprint and logs an error, so
anyone still holding one keeps a working arrow (its parts are serialised on the object) whose
blueprint-level tag lookups answer as `Object`. One day of release exposure on a weight-2 drop,
against leaving an arrow in the tables that does nothing.

**None of them can end up in a turret the game stocked** — all six carry `ExcludeFromTurretStock`,
and vanilla's `Boomrose Arrow` gains it by merge. `MagazineAmmoLoader.GetAmmoBlueprints` is
**opt-out**: every blueprint with the matching ammo part is a candidate unless tagged, and an
untagged one gets one entry in the pool while a `TurretStockWeight="N"` gets N.

**Which turrets, exactly.** Auto-stocking runs off a `GenerateIntegratedHostInitialAmmo` event, and
only two things raise it: `TurretTinker`, for wild turrets, and `PlaceTurretGoal`, for an AI placing
one. **`Tinkering_DeployTurret` does not** — a turret you deploy yourself arrives *empty* and you
load it from your own pack. Confirmed in game. So this is about turrets nobody chose the ammunition
for, not about your own.

**And it was a guaranteed share, not a chance.** Short Bow and Compound Bow both carry
`MagazineAmmoLoader MaxAmmo="1" AmmoPart="AmmoArrow"`. `GetDesiredAmmoCount` asks for
`AmmoPerAction × 50` = 50 arrows, and the fill is `(desired ÷ entries)` of **every** entry rather
than a weighted pick:

| | Pool entries | What a wild bow turret carried |
|---|---|---|
| Before | 25 | 2 of each → **12 effect arrows and a boomrose**, plus 18 steel |
| After | 18 | 18 steel, 6 carbide, 4 folded carbide, 2 of each end-game arrow |

The Turbow is unaffected either way — it uses `EnergyAmmoLoader`, so a Turbow turret stocks no
arrows at all.

Two reasons, covering different arrows. **Three of the six burst** — dream dew, starshell and
stinger carry area payloads — and a turret stocked by the game is one nobody picked the ammunition
for, so a target closing to point blank puts the cloud or the flash on the turret and on anything
beside it. Boomrose is the vanilla case of the same problem. Blaze, cryo and hulk honey are
single-target and that argument does not reach them.

**What reaches all six is that they are hand-made.** A waxed bulb of honey, a
hollowed stinger with the sac still in it, a scored gas bulb, a phial, a wax shell — none of that
survives being cycled through a magazine and a feed mechanism. A vanilla arrow is a shaft and a
metal head, which does.

Only the blast case is merged into vanilla. Fullerite, crysteel, flawless crysteel and zetachrome
arrows are also untagged and therefore also stocked, at one entry each — but they are better
sticks, not hazards, and where Freehold draws its value ceiling is their economy to set. See #147.

#### The four effect shells

**Why they never worked, and it was not Mura's doing.** A shotgun never asks its ammunition what
to fire. `MagazineAmmoLoader.HandleEvent(LoadAmmoEvent)` reads the *weapon*:

```csharp
if (ProjectileObject.IsNullOrEmpty())
    E.Projectile = GetProjectileObjectEvent.GetFor(E.LoadedAmmo, ParentObject);
else
    E.Projectile = GameObject.Create(ProjectileObject, ...);
```

and all four weapons that take a shell hardcoded a pellet — `ProjectileShotgunPellet` on the Pump
Shotgun, `ProjectileCombatShotgunPellet` on the Combat Shotgun, and this mod's own two. Every
shell's `AmmoShotgunShell ProjectileObject` was discarded and the payload never existed. That is
the *"degraded to plain ammo"* symptom #14 recorded, and it is structural rather than a bug.

**The fix is vanilla's own.** An empty `ProjectileObject` means "fire whatever is loaded", and it
appears exactly three times in the game — the **Grenade Launcher** and the **Dart Gun**, both
weapons whose ammunition carries the payload. #145 merges that blank onto both vanilla shotguns
and sets it on this mod's two. Plain `Shotgun Shell` is unaffected: `ProjectileShotgunShell` and
the two pellet blueprints are the same object three times over — `BasePenetration` 4 over `1d2`,
all inheriting `BaseShotgunProjectile`.

The cost is stated rather than hidden: if Freehold ever differentiates the combat shotgun's pellet
from the pump's, this merge discards it. That is charter rule 1's own failure mode, accepted
because the alternative is a category of ammunition that cannot exist.

**The payload is per pellet, and that governs every number.** `MissileWeapon.Fire` raises
`LoadAmmoEvent` `AmmoPerAction` times, then `DeepCopy`s the result up to `ShotsPerAction` — so one
shell becomes **eight** projectiles, each with its own spread roll and its own copy of the payload.

| Displayed as | Blueprint | Payload |
|---|---|---|
| incendiary shell | `Raven_Incendiary Shell` | `TemperatureOnHit 125`, `Max="true" MaxTemp="400"` |
| cryo shell | `Raven_Cryo Shell` | `TemperatureOnHit -25`, `Max="true" MaxTemp="-110"` |
| flechette shell | `Raven_Flechette Shell` | pen 6 over flat `1` damage |
| takedown shell | `Raven_Takedown Shell` | `GroundOnHit` + `ProneOnHit`, both `Chance="12"` |

**The temperature figures came out of play-testing, and the first two attempts were wrong in ways
worth recording**, because both traps generalise and #146 meets them again with a chaingun.

Parity per action is the right *target* — a shell and an arrow each cost one piece of ammunition
per action — but ÷8 is the wrong way to reach it, twice over. `MissileWeapon.Fire` rolls
`Stat.Random(-WeaponAccuracy, WeaponAccuracy)` per pellet, and at the Pump Shotgun's
`WeaponAccuracy="45"` only about **two of eight** connect, ranging from 1.8 to 4.4 across
measured runs. And ambient regression is a **flat 5 a turn** — a floor, not a curve — so −6 a
pellet with a couple connecting was erased about as fast as it landed. Eight shells into a 500 HP
target never got it cold.

So the divisor is the pellets that *land*: −50 and +250 over two gives **−25** and **+125**, which
is three shots to freeze and two to ignite — the arrows' own figures, reached the way a shotgun
reaches them. Measured: 3 shots, ~4 turns frozen, against the arrow's 3 hits and ~3 turns.

**`Max`/`MaxTemp` bound the duration**, which no `Amount` can. Overshoot past −100 *is* the freeze
duration at 5 a turn, and it scales with however many pellets happen to connect — two point-blank
shots once reached −185 and held for ~17 turns. The cap stops the payload applying once the target
is past the line. Its value has a trap: it must sit **beyond** the threshold. `MaxTemp="-90"` would
stop the cold at about −95, above the brittle line, and the target would never freeze at all.
Vanilla writes `Max="true" MaxTemp="400"` on four objects, all heat; the cold side has no
precedent.

**Heat and cold are asymmetric by nature, not by tuning.** `Physics.Temperature` is clamped to
±10,000, and the thresholds are not mirror images:

| | trigger | what happens |
|---|---|---|
| `Frozen` | ≤ −100 | *"Can't take physical actions."* — and **nothing** below it, all the way to the −10,000 floor |
| `Burning` | ≥ 350 | damage per turn, scaling with distance above |
| `Vaporized` | ≥ 10,000 | `ParentObject.Die(…, "You were vaporized.")` |

So heat is a damage type with a runaway top end and a kill line; cold is a control effect that
plateaus, where every point past −100 buys only duration. That is why the two shells' numbers are
not mirror images, and why #144 could cut the arrow's cold from −400 to −50 without losing anything
— there was no deeper tier to buy.

**Six of Mura's ten were cut, and the mechanism did the sorting.**

*Area payloads cannot be scaled down*, because eight pellets multiply the geometry rather than the
magnitude. `GasGrenade.DoDetonate` fills the impact cell **and all eight adjacent cells** at the
full `Density`, and density is per cell — so dividing it thins the gas without shrinking anything.
Eight pellets across a `WeaponAccuracy="45"` cone reach up to **72 gas cells** from one shell.
`FlashbangGrenade` bottoms out at radius 1 / duration 1 per pellet. `HEGrenade` is worst: `Explode`
deals `Force / 250` and propagates only while `(Force − dealt) / 8 > 100`, so Boomrose's 1,200
divided by eight is **150 — zero damage and no propagation at all**. And `IGrenade` detonates on
the projectile's *death* (`BeforeDeathRemovalEvent`, when `Primed`), so a pellet that hits nothing
still goes off where it lands. Cut: explosive, flash, poison gas, sleep gas.

*Bleeding is not available to a projectile at all.* `BleedingOnHit` registers `WeaponHit` and
`WieldedWeaponHit`; `WeaponHit` is raised in `Combat.cs` on the melee path, and `MissileWeapon`
raises `ProjectileHit` instead. The razor shell would have fired and done nothing — **and so does
the quill arrow shipped in 2.3.0**, replaced in #201. Cut: razor.

*Vibro, sunder and stasis* go for the reasons #144 cut their arrows, each worse on eight pellets
from a tier-3 gun: `Vorpal` exists on three objects in the game and the nearest is a tier-7 heavy
weapon; `BasePenetration="10"` is above every vanilla firearm projectile including the sniper
rifle's 7; and the stasis shell omitted `IsRealityDistortionBased`, which all three vanilla stasis
grenades set.

What survives is what a shotgun already is — many small hits — so the payload rides the hit.

**Armour stops the damage, not the temperature.** `ProjectileHit` fires even when a pellet fails to
penetrate (the `Penetrations = 0` branch raises it too) and `TemperatureOnHit` never checks
penetration. It is also why the cryo shell answers everything the takedown shell cannot touch:
`Physics.IsFrozen()` is nothing but `Temperature <= -100` and `Frozen.Apply` has no conditions
whatsoever, so an ooze, a slug or a worm freezes exactly as well as a humanoid.

**The flechette shell is new, because a real slug shell is not expressible.** Shot count belongs to
the gun — `num9` is read straight off `MissileWeapon.ShotsPerAction` with no event between, and
`GetMissileWeaponPerformanceEvent`, the one event ammunition can reach, carries penetration and
damage but no count. That is filed upstream as #200. So the anti-armour round reaches its role
through penetration instead: eight steel darts rather than one slug. Pen 6 over flat 1 damage came
from simulating `Stat.RollDamagePenetrations` directly:

| Mean damage per pellet | AV 0 | AV 4 | AV 8 | AV 10 | **AV 12** |
|---|---|---|---|---|---|
| standard pellet — pen 4 / `1d2` | 5.34 | 2.34 | 1.22 | 0.73 | **0.33** |
| flechette — pen 6 / `1` | 4.56 | 2.56 | 1.11 | 0.82 | **0.49** |

Within 10% of standard shot everywhere below AV 10 and **48% ahead at AV 12**, which is the most
populous declared AV in the game — 70 blueprints, all cherubim, plus Rodanis Y. Pen 7 and `1d2`
damage were both tried and both beat standard shot nearly everywhere, making them upgrades rather
than trades.

**Every penetration figure above is the raw XML value, which is not what the game shows.** Qud adds
`RuleSettings.VISUAL_PENETRATION_BONUS`, a flat **+4**, to every penetration it displays anywhere —
melee, thrown, arrows, mutations and missiles alike:

```csharp
stringBuilder.Append(Math.Max(E.Penetration + RuleSettings.VISUAL_PENETRATION_BONUS, 1));
```

| | XML | on screen |
|---|---|---|
| vanilla shotgun pellet | 4 | →8 |
| **flechette shell** | **6** | **→10** |
| sniper rifle, vanilla's firearm ceiling | 7 | →11 |

The offset is not arbitrary and the manual explains the result without naming it: *"Each weapon has
a penetration value (→4, for example). This value represents the armor value (AV) that your weapon
will usually penetrate with ease."* The penetration die is `Random(1, 10) - 2`, which averages
**3.89** — so folding 4 into the display makes `displayed penetration > target AV` the comparison a
player can make by eye. The flechette reads as *usually penetrates AV 10*, which is where it was
aimed, arrived at independently from the cherub arithmetic above.

Worth remembering when reading this document against a screenshot: everything here is XML values,
and the game is always four higher.

**The takedown shell carries two parts because neither can stack.** `Prone.Apply` opens with a
`HasEffect<Prone>` guard and `GroundOnHit` extends a `Grounded` duration rather than adding a
second, so pellets buy reliability and never magnitude — which is what makes `Chance` an honest
dial. Both sit at `Chance="40"`, sized against the ~2 pellets that land rather than the 8 fired;
`Chance="12"` shipped first and gave a shell a 22% chance of doing anything at all.

**Three things about it that play-testing corrected, all of which a player will also meet.**

*`Prone` promises more than Qud delivers.* Its own summary is `-6 Agility, -5 DV, -80 move speed,
must spend a turn to stand up`, at `Duration = 1`. It does **not** stop the target attacking — a
prone creature adjacent to you still bites — and it neither stacks nor refreshes, so a second shell
into a downed target is wasted. It buys a window and an action.

*The anatomy exclusion is wider than "no legs".* `LimbSupportsProneness` wants a `Feet` or `Roots`
part with `Mobility` above zero, and **`Legs` — the variant every insect, spider and crab is built
from — is `VariantOf="Feet"` with `Mobility="0"`.** A fire ant queen has six legs in its anatomy and
cannot be knocked off any of them. The `Mobility` clause excludes as much as the missing-limb one.

*Grounding is silent unless the target is airborne.* `Grounded.Apply` prints nothing; the *"falls to
the ground"* line comes from `Flight.Fall`, which only fires on a live `Flying` effect. Three
play-tests read as failures before examining a target showed the `Grounded` status had been there
all along. The reason is worth knowing when testing: **a wished creature is not flying** —
`Flight.StartFlying` is only reached from the `Wings` mutation's `CommandEvent` handler, so flight
is an activated ability rather than a spawn state, and a fresh gamma moth is standing on the ground.

Measured on a moth that had taken off: grounded on the shell, **~20 turns unable to fly** against
the configured `Duration="20-30"`, with the *"falls to the ground"* message appearing as expected.
`Grounded` refuses `CanChangeMovementModeEvent` for `"Flying"` throughout, so the target spends that
window trying to take off and failing.

`GroundOnHit` also needs `SaveTarget="40"`, not `ProneOnHit`'s 25, because `FlyingLevelAidsSave`
subtracts the target's flying level first — and nearly every flier in the game carries `Wings` at
level 10. At 25 that is a save against 15, which is why six point-blank shells failed to ground a
gamma moth. Vanilla's only user of the part writes 40 for exactly this reason.

`StickyOnHit` was the obvious alternative and fails the same test the gas shells did: it reaches
every anatomy and grounds fliers by itself, but it has no `Chance` field, `Stuck` has no anti-stack
guard, and `GameObject.ApplyEffect` does not deduplicate — so one shell applies **eight separate
`Stuck` effects** and escaping rolls a save against each. No dial, so no shell.

`GroundOnHit` needs `ChargeUse="0"` written out: it is an `IPoweredPart` whose constructor sets
`ChargeUse` 100, so on a projectile with no power source `IsReady` fails and the part does nothing,
silently. Vanilla's only user, `ProjectileNaserCannon`, writes the same zero.

**Unlike the arrows these are craftable, and that is the same rule read the other way.** Tinkering
is the artifact skill, and a cartridge serves a firearm, which is recovered technology — vanilla
agrees, giving `Shotgun Shell` and `Lead Slug` recipes while no arrow in the game has one.

Cost and availability are set separately. `TinkerItem.LoadBlueprint` reads the recipe tier from
`BuildTier`, defaulting to the highest bit level in the cost, and `DataDisk.GetRequiredSkill` needs
Tinker 2 past tier 3:

| Shell | Bits | `BuildTier` | Recipe tier | Skill |
|---|---|---|---|---|
| incendiary, cryo, flechette | `003` | **4** | 4 | **Tinker 2** |
| takedown | `003` | — | 3 | Tinker 1 |

All four cost two scrap metal and one pure alloy for three shells, which sits between vanilla's two
anchors — a grenade mk I is two bits for one, plain shot is one bit for five. `BuildTier` is a real
public field on `TinkerItem` that vanilla never writes; using it keeps the materials cheap while
putting burning, freezing and armour-defeating behind the second skill. The less-lethal round is the
one anybody who can build the gun can also load. The wider inconsistency in vanilla's own recipe
tiers is #202.

**All four carry `ExcludeFromTurretStock`, and the case is stronger than it was for arrows.**
`Shotgun Shell` is the *only* blueprint in the game with `AmmoShotgunShell` and carries no exclusive
tag, so the shell pool is a single entry — untagged, these four would be four fifths of every
shotgun turret's ammunition. `TurretTinker` also falls back to `"Pump Shotgun"` twice, which makes
shotgun turrets the game's default. The scope is the same narrow one as for arrows: only
`TurretTinker` and `PlaceTurretGoal` raise `GenerateIntegratedHostInitialAmmo`, so a turret you
deploy yourself still arrives empty.

**Reachability is both routes.** Weight 2 apiece in `Ammo 2` through `Ammo 8`, at Boomrose's
quantities (1 at tier 2, `1d4` above). Unlike the arrows they run the full range, because shells
have no tier ladder — Boomrose stops at 4 because fullerite, crysteel and zetachrome arrows take
over, and there is no better shell to replace these. Vanilla keeps plain `Shotgun Shell` at weight
25 in every pool from `Ammo 2` to `Ammo 8`.

---

## 7. Population / loot tables (`PopulationTables.xml`)

78 table definitions: **56 merged** into vanilla, **22 declared fresh**. The 48/28 split this
line used to give was from before #34 converted `Artifact 3`–`8` from replacements to merges; §0
was corrected in #95 and this line was missed. `Ammo 2` and `Ammo 3` were added in #144 to give
the effect arrows a drop route alongside the cells already merged into `Ammo 4`–`8`.

### 7.1 Starting gear (18 new tables)

One `StartingGear_*` table per Psionic Adept subtype. Common pattern:

**Lore Seekers (casters)** — `StartingGear_Common`, their affinity's psionic pistol or rifle,
cloth robe, sandals, 3 half-full waterskins, 1d3 salve tonic, a dagger, **their affinity's basic
chipset**, a **basic mental mirror chip**, a **basic clairvoyance chip**, 1d3 injectors,
2d4 scrap, 1d3 cells, 1d3 from Artifact 1, 1d3 from Artifact 2.

Per-subtype deviations:

| Subtype | Deviation |
|---|---|
| Force | Also a **basic toolkit**; 3d4 scrap instead of 2d4 |
| Ice | **Iron plate armor** instead of cloth robe |
| Lightning | Steel dagger instead of Dagger2 |
| Fire | Dagger + **Battle Axe2** |
| Light | Guaranteed **Solar Cell**, only 1d2 from the Cells table |
| Corrosive | **4** waterskins, 1d3+1 salve tonic |
| Blood | **Two** blood psionic pistols, **two** daggers |
| Mental | **2d3** injectors instead of 1d3 |
| Temporal | Only 2 waterskins, but **2d3** rolls on Artifact 1 and Artifact 2 |

**Immovable Wall (Guardians)** — `StartingGear_Common`, a themed weapon, a **full iron armor
set** (Raven_Iron Plate Armor, Boots, Gauntlets, Helmet), 3 half-full waterskins, 1d3 salve
tonic, one themed single chip, a **basic neutral body chipset**, a **basic mental mirror chip**,
1d3 injectors, 1d3 cells. Three Guardians break the armor-set pattern entirely.

| Guardian | Weapon(s) | Armor | Chip | Other deviations |
|---|---|---|---|---|
| Force | Long Sword2 + **Iron Greatshield** | iron set | Disintegration | — |
| Fire | **Steel Halberd** | iron set | Kindle | — |
| Ice | **Steel War Hammerth** (2H) | iron set | Frost Webs | — |
| Lightning | Long Sword2 + **Iron Buckler** + **Lightning Psionic Rifle** | iron set | EMP | **2d3** injectors |
| Light | **Compound Bow + 100 Wooden Arrows** + **Light Psionic Rifle** + Dagger2 | iron set | Photosynthetic Skin | Guaranteed **Solar Cell**, only 1d2 cells |
| Corrosive | **Steel Long Swordth** (2H) | iron set | Corrosive Gas | — |
| Blood | 2× Dagger2 | **Vine-Weave Tunic, Elastyne Slippers / Gloves / Skull Cap** — no iron set | Syphon Vim | 1d2 cells |
| Mental | **Battle Axe3** | iron set | Sunder Mind | 2 full + 2 empty waterskins, **Basic Toolkit**, 2d4 scrap, **1** cell |
| Temporal | **2× Temporal Psionic Pistol** | **Cloth Robe + Sandals** — no iron set | Space-Time Vortex | **1** salve tonic, **Basic Toolkit**, **1** injector, 1d4 scrap, **1** cell |

### 7.2 Equipment tables (merged)

- **Melee Weapons 1C–8C / 1R–8R** — new melee blueprints are slotted into their tier's Common
  (one-handed) and Rare (two-handed) tables, mostly at weight 20. Tier-1 tables seed bronze gear
  at weight 20 and iron at weight 10; `Raven_Bronze Wristblade` is weight 5 in Melee Weapons 1C.
  **Nine new melee blueprints appear in no table at all:** the eight vibro weapons
  (battle axe, greataxe, vinereaper, halberd, greatsword, rapier, katana, wristblade — all
  tinkerable, so still reachable) and `Raven_Iron Maceth`, which is neither dropped nor tinkerable.
- **Armor 1C–8C / 1R–8R** — all new armor is reachable. Upstream 2.2 left **ten pieces in no
  table** — the four nanoweave pieces, the four flexi pieces, the bio-scanner mask and the mutating
  mask — and since only the bio-scanner mask is tinkerable, nine of them were unobtainable in play.
  All now have drop entries (#7, fixed in #38), and `validate_mod.py`'s `unreachable` check keeps
  it that way.
  Armor 7C/7R/8C/8R each used to carry a `<removetable>` stripping the tier-below reference,
  severing vanilla's tier cascade — `Armor 8C` weights that cascade **900** against 85 of actual
  zetachrome, so a tier-8 roll is meant to be a rare jackpot rather than a guarantee. Removed in
  #4; the mod's own entries carry the weight instead, giving 25% top-tier at tier 8 against
  vanilla's 8.6%.
- **Missile 2** — all 9 psionic pistols, weight 1 each.
- **Missile 3** — all 9 psionic rifles, weight 1 each.
- **Missile 4** — compact flamethrower (10), cryocannon (10), net gun (5), fine-tuned handgun (5), modified handcannon (5), drum shotgun (5).
- **Ammo 4–8** — solar cell array from tier 4; advanced chem cell from tier 5; solar cell nexus from tier 7; dark matter cell via a nested chance table at tier 8.
- **Implants_1and2Pointers** — steel dermal plating, omni pass, steel hand bones.
- **Implants_3Pointers** — air filtration system, crysteel dermal plating.
- **Implants_4PlusPointers** — crysteel hand bones, zetachrome dermal plating, zetachrome hand bones.

### 7.3 Artifact tables (merged)

`Artifact 3, 4, 5, 6, 7, 8` each merge a single psionic-chip entry into vanilla's `Items` group
and touch nothing else:

```xml
<population Name="Artifact 3" Load="Merge">
  <group Name="Items" Load="Merge">
    <table Weight="10" Number="1" Name="Raven_Chips Tier 1" />
  </group>
</population>
```

`Artifact 3R/4R/5R/6R/8R` are likewise merged, adding:

| Table | Additions |
|---|---|
| Artifact 3R | Large sphere of negative weight (w5), advanced hoversled (w1) |
| Artifact 4R | Sphere (w10), hoversled (w1) |
| Artifact 5R | Sphere (w15), hoversled (w5) |
| Artifact 6R | Sphere (w15), hoversled (w10) |
| Artifact 8R | **Cybernetics credit pass** (w5), **dark matter cell** (w1) |

These six were declared **without** `Load="Merge"` through 2.2, overwriting vanilla's tables
outright. A source comment shows it was deliberate — *"Overwrite instead of merge to neatly add
chips in"* — convenience bought at the price of conflicting with any other mod touching those
tables and silently discarding whatever a future Qud patch adds to them. It was the mod's worst
compatibility defect; converted to merges in **#34**.

Vanilla's weights are a uniform 95 common / 5 rare across all six tables, so the distribution
moved by well under a percentage point:

| | common | rare | chips |
|---|---|---|---|
| vanilla, unmodded | 95.00% | 5.00% | — |
| before (replacement) | 85.00% | 5.00% | 10.00% |
| **after (merge)** | **86.36%** | **4.55%** | **9.09%** |

Chips drop marginally less often because the entry is added to the pool rather than carved out of
it, which also dilutes rares by half a point. Reproducing the old numbers exactly would mean
overriding vanilla's common weight to 85 — reintroducing a hardcoded assumption about a value the
game is free to change, which is the problem the fix existed to remove. Charter rule 1 prefers
additive.

### 7.4 The dark matter cell chance table

```
Ammo 8  →  weight 1  →  Raven_Dark Matter Cell Chance
                         ├─ weight 1 → reroll on Ammo 8
                         └─ weight 1 → Raven_Dark Matter Cell
```

So on Ammo 8, hitting the weight-1 slot gives a 50/50 between the cell and a reroll. On
Artifact 8R it is a flat weight-1 entry with no second roll. (This nesting was added in 2.2
after the cell was corrected from tier 7 to tier 8.)

---

## 8. World changes — Joppa (`Joppa.rpm`)

A `Load="Merge"` map patch adding **76 cells** in the region X 16–27, Y 13–21 — a walled
building near Argyve's workshop (the changelog describes it as "the building in red"). It was
rebuilt as a separate structure in 2.2 specifically to stop it colliding with the Spring Molting
update's new Joppa furniture and with the Saving Joppa sub-mod.

Contents:

| Object | Count |
|---|---|
| DirtPath | 45 |
| RustedMetalWall | 27 |
| Torchpost | 2 |
| CyberneticsStationRack (becoming nook rack) | 1 |
| CyberneticsTerminal2 (becoming nook) | 1 |
| `Raven_Empty Gun Rack` | 1 |
| `Raven_Empty Weapon Rack` | 1 |
| `Raven_Rusted Door` | 1 |
| Bookshelf, Bed, Dresser, Low Table, Floor Cushion, Vase, Oven, Woven Basket, Chest | 1 each |

> 🗒️ The `What Does the Mod Do (WIP).txt` in this folder describes this as "two chests, a bedroll,
> a becoming nook, and an empty cybernetics rack." That text predates the 2.2 rebuild — the shipped
> map actually has **one** chest, a **bed** (not a bedroll), and a good deal more besides. Mura's
> later pinned feature list drops the itemisation and just calls it "a new building into Joppa that
> can be used as a sort of home base for the player," which matches what's in the file.

Net effect: a free bed, storage, an oven, and — most importantly — **a becoming nook and
cybernetics rack available in Joppa from turn one**, which matters a great deal now that
Psionic Adepts and (buffed) True Kin both want early cybernetics.

---

## 9. Economy & value curve

The mod deliberately flattens the top of the price curve so high-tier gear is attainable:

- Standard tier progression for weapons/armor: **5 · 10 · 20 · 40 · 80 · 160 · 320 · 640 · 1280**.
- Body armor runs a parallel curve at 8/16/32/64/128/256/512/1024/2048.
- Vambraces run at 4/8/16/32/64/128/256/512/1024 (half the standard curve — they're a partial slot).
- Several tier-8 items are pulled *below* curve: zetachrome greataxe 1200, zetachrome wristblade 1200, Cudgel8/Cudgel8th 1200.
- Vibro weapons are flat 300 across the board.
- Laser pistol 250, laser rifle 550, chain pistol 100, borderlands revolver 25.
- All grenades flattened to 10/20/30.

---

## 10. Known issues & fork checklist

Ordered roughly by impact. Rows marked ✅ are done and stay here as a record — each was a real
defect, and the shape of it is worth not reintroducing. I'd sooner keep a closed row than have
someone rediscover the problem from scratch.

| # | Severity | Issue | Where |
|---|---|---|---|
| 0 | ✅ Fixed | **`Skills.xml` had a duplicate `Tile` attribute** on Berserk!, making it the only file in the mod that failed a strict parse. The open question was whether Qud's loader was tolerating it or dropping the file silently — which would have meant §4's skill changes had never shipped. It was tolerating it: the changes had been live all along, so the defect was cosmetic. Attribute removed (#5). | `Skills.xml` |
| 0b | ✅ Fixed | **`workshop.json` pointed at Mura's Workshop page.** `"WorkshopId": 1134036260` is the *original* mod's ID, so uploading would have published over their item rather than creating this fork's. Cleared for the fork's own upload; `Title`, `Description` and `ImagePath` now describe this fork and carry the `docs/PERMISSION.md` §4 credits (#2). `tools/validate_mod.py` has a `workshop-target` check so the upstream ID cannot come back. The field held `0` until the first upload, which turned out to be its own defect — the uploader reads a zero as a lookup for item zero, not as "no item yet" (#163). It now carries the fork's real id, `3785441196`. | `workshop.json` |
| 1 | ✅ Fixed | **72 of 144 psionic chips had no drop-table entry and no tinker recipe** — half the flagship system was unobtainable. `Raven_Chips Tier 1/2/3` listed only the first chip of each family plus its chipset, 24 entries where 48 were needed. Each tier table now holds **48** (#6, fixed in #36). | `PopulationTables.xml` → `Raven_Chips Tier 1/2/3` |
| 2 | ✅ Fixed | **Artifact 3–8 were full table replacements**, not merges — guaranteeing conflicts with any other mod touching them and silently discarding future vanilla additions. A source comment shows the overwrite was deliberate ("to neatly add chips in"), which made it convenience bought against charter rule 1. All six now merge a single `Raven_Chips Tier N` entry into vanilla's `Items` group (#3, fixed in #34); chip drop rate moved 10% → 9.09%. See §7.3. | `PopulationTables.xml` |
| 2b | ✅ Fixed | **Nine new armor pieces were unobtainable** — the four nanoweave and four flexi pieces plus the mutating mask had no drop-table entry and no `TinkerItem`, and `Raven_Iron Maceth` had the same problem. All are reachable (#7, fixed in #38); the Maceth's entry is at `PopulationTables.xml:431`. `tools/validate_mod.py`'s `unreachable` check now reports **0** unreachable blueprints, so this class of defect fails CI rather than accumulating. | `Armor.xml`, `MeleeWeapons.xml`, `PopulationTables.xml` |
| 3 | 🟠 Part | **All of `Ammo.xml` (62 objects) was commented out** — "removed temporarily". Mura pulled it when a Qud change broke the effects and the ammo degraded to plain ammo. The six effect **arrows** are live as of #144 and the four effect **shells** as of #145, both retuned and renamed, with three of nine arrows and six of ten shells cut rather than revived. #145 also established *why* the shells were dead: every shell-firing weapon hardcoded its pellet, so the ammunition's projectile was discarded — fixed by deferring the weapon to its ammo, as vanilla's own grenade launcher does. The **20 bullet objects are still disabled**, pending #146 (slugs), which must run the same test first. | `ObjectBlueprints/Ammo.xml` |
| 4 | ✅ Fixed | **Mutant HP gain was `2-3`** in XML against `1-5` in every one of Mura's writeups. `2-3` has vanilla's own 2.5 average, so the mod's headline HP change did nothing to the mean, and it left mutants strictly dominated by True Kin's 2-4. Corrected to `1-5` in #90, with a Combo option offering `2-3` and vanilla's `1-4`. | `Genotypes.xml` |
| 5 | ✅ Fixed | **`Flawless Crysteel Boots` was tagged Tier 3** by the mod's merge, overriding vanilla's 7. Override removed (#9). (should be 7) — wrong loot pool and mod capacity | `ObjectBlueprints/Armor.xml` |
| 6 | 🟠 Med | **`<stag>` used instead of `<tag>`** twice — the advanced hoversled's `Floating` tag and the sphere of negative weight's `Trinket` tag are almost certainly not being applied | `ObjectBlueprints/OtherEquipment.xml` lines 95, 196 |
| 7 | ✅ Fixed | **Akimbo reused `Class="Pistol_Akimbo"`** across the Pistol and Multiweapon trees. `SkillFactory.PowersByClass` holds one entry per class and vanilla grants powers by class — the Gunslinger calling is `<skill Name="Pistol_Akimbo" />` — so the mod's entry was served in place of vanilla's. Removed from Multiweapon Fighting in #11 after a distinct class proved to duplicate the ability and lock the skills screen. | `Skills.xml` |
| 8 | ✅ Fixed | **`Cudgel6th` had `MaxStrengthBonus="11"`** where every tier-6 peer uses 7 | `ObjectBlueprints/MeleeWeapons.xml` |
| 9 | ✅ Fixed | **`Raven_Carbideweave Cloak` was valued at 5** instead of 40 | `ObjectBlueprints/Armor.xml` |
| 10 | ✅ Fixed | **Dark matter cell (500k charge) priced same as advanced chem cell (50k)** — both 300 | `ObjectBlueprints/OtherEquipment.xml` |
| 11 | ✅ Fixed | **Psionic pistols listed `RifleMods`, not `PistolMods`** (the pistol base inherits `BaseRifle`) | `ObjectBlueprints/RangedWeapons.xml` |
| 12 | 🟡 Low | **Psionic Adept chargen text says "+30 bonus skill points"** — actual delta is +25 vs vanilla / +10 vs the mod's True Kin | `Genotypes.xml` |
| 13 | 🟡 Low | **Four vibro weapons commented out** with "rework these or remove them" (vibro mace, two-handed vibro mace/flail, vibro war hammer, two-handed vibro war hammer/greathammer) | `ObjectBlueprints/MeleeWeapons.xml` |
| 13b | ✅ Fixed | **`Raven_ProjectileFireRifle` used `Attributes="Heat"`** while its pistol counterpart uses `"Heat Fire"` — the rifle likely won't set things alight | `ObjectBlueprints/RangedWeapons.xml` |
| 14 | ✅ Fixed | Subtype sprite files used the prefix `corrosion*` while the subtype is named "Corrosive". Renamed to `corrosive*` in this fork (#24), and `tools/validate_mod.py` now checks every subtype tile against its affinity. | `Textures/Subtypes/` |
| 15 | ✅ Fixed | The `Yttrian` anatomy/body-object name survived the genotype's rename to "Psionic Adept". Renamed to `PsionicAdept` in this fork (#13). | `Bodies.xml`, `Genotypes.xml` |
| 16 | ⚪ Note | The Chip Interface is merged into the base `Humanoid` anatomy, so **every humanoid NPC in the game gains a chip slot**. Currently nothing equips chips to NPCs, but any mod or future change that populates that slot would affect the whole world | `Bodies.xml` |

### Things the changelog references that are **not** in this folder

The 2.2 changelog mentions fixes to **Experience Curve Beta**, the **Grand Bazaar**, and
**Saving Joppa**. The first two are separate sub-mods by the same author — no `.cs` or map files
for them exist in this directory, and carrying them forward means pulling them separately
(#174, #175). The only C# here is the 36 one-line mutation-mod classes.

**Saving Joppa is the exception, and it is partly here already.** Mura's standalone listing says
so outright — *"there's no point in installing both as it is already incorporated into the base
mod"* — and the shared parts check out: `Raven_Empty Weapon Rack`, `Raven_Empty Gun Rack`,
`Raven_Empty Armor Rack` and `Raven_Rusted Door` are declared in `Furniture.xml` **identically** to
the standalone's own copies, attribute for attribute.

What did *not* come across is the part the sub-mod is named for: `TerrainJoppaRuins` and the
96 KB `JoppaRuins.rpm` map are in the standalone and absent here. So "incorporated" describes the
furniture rather than the ruins, and anyone planning around that should verify the claim against
the current standalone rather than the sentence. It is also the fork's own precedent for #174 and
#175: absorbing a sub-mod is something this mod's author has already done.

### Mura's three partial feature lists — and how far to trust them

Three overlapping writeups of the mod exist. None is complete; all three are explicitly labelled
as partial by their author. Where they disagree with the XML, **the XML is what ships**.

| Source | Where | Scope | Reliability |
|---|---|---|---|
| `What Does the Mod Do (WIP).txt` | In this folder | Genotypes, skills, "other", energy cells. Header says *"THIS LIST IS NOT COMPLETE, IT IS A WORK IN PROGRESS (Need to add equipment)"* | Oldest. Joppa section is stale (describes the pre-2.2 building) |
| **Pinned Workshop discussion**, "Partial Feature List" | Workshop page, Mura, Nov 9 2024 | Near-identical to the above, but with a rewritten Joppa line and a much fuller energy-cell/item-mod explanation | Newest of the three. Best source for the cell-mod formulas |
| `2.2 changelog.txt` | In this folder | Only the 2.1.1 → 2.2 delta | Accurate for what it covers; the only source documenting the physical-vs-mental chip scaling split |

Mura's own framing of the pinned list: *"this is NOT a feature-complete list. In particular, I
don't have all the new equipment or psionic chips listed, nor the changes to armor/weapon stats
and trade values, among other things."* That gap is precisely what §6 and Appendices A–B of this
document fill in.

**Known points where the docs and the XML disagree** (all covered in detail above):

| Claim in Mura's docs | Reality in the XML |
|---|---|
| Mutants get 1-5 HP/level | Was `BaseHPGain="2-3"`; the docs were right and the XML was the regression. Now `1-5` (§1.2) |
| Psionic Adept "+30 bonus skill points" | +25 vs vanilla, +10 vs the mod's True Kin (§1.4) |
| "Psionic Interface" slot | Was `Chipset Interface`; now **`Chip Interface`** in this fork (§3.1) |
| Joppa gets "two chests, a bedroll…" | One chest, a bed, and considerably more (§8) |
| Multiweapon Fighting Str-or-Agi is a mod feature | Vanilla adopted it; only the requirement cut is the mod's (§4) |


---

## 11. File map

```
mod/                            # the only directory uploaded to the Workshop
├── Mods.xml                    # makes Gigantic tinkerable
├── Genotypes.xml               # Mutant + True Kin merges, Psionic Adept (new)
├── Subtypes.xml                # 18 affinities in 2 categories
├── Skills.xml                  # 6 tree edits
├── Bodies.xml                  # Chip Interface part; TrueKin + PsionicAdept anatomies
├── Options.xml                 # 11 options (§13)
├── PopulationTables.xml        # 78 tables (56 merge / 22 new)
├── Joppa.rpm                   # 76-cell amenity building
├── manifest.json               # id, version, author — the credit field is enforced
├── workshop.json               # Steam metadata + description
├── preview.png
├── ObjectBlueprints/
│   ├── MeleeWeapons.xml        # 71 new / 79 merged
│   ├── Armor.xml               # 61 new / 38 merged
│   ├── RangedWeapons.xml       # 49 new / 10 merged
│   ├── PsionicChips.xml        # 145 new (1 base + 144 chips)
│   ├── Cybernetics.xml         # 9 new / 16 merged
│   ├── OtherEquipment.xml      # 7 new / 16 merged
│   ├── Throwables.xml          # 51 merged (prices only)
│   ├── Ammo.xml                # 20 new + 1 merge; 20 bullets still disabled
│   ├── Furniture.xml           # 4 new
│   ├── Creatures.xml           # 2 new bodies + 1 merge
│   └── Food.xml                # 2 merges
├── Scripting/                  # 40 classes: 36 mutation stubs, plus options,
│                               # the Joppa system, and the chip-slot mutator
└── Textures/Subtypes/          # 18 sprites by Noble Lark

Mura's original documents are NOT in mod/ — they live in docs/, outside what ships.
```

---

## 12. Credits (carry these forward)

- **Mura** (`@mura_raven`) — creator; years of work on the original mod
- **Noble Lark** — all 18 psionic subtype sprites (credited in the Workshop description)
- **Scrolldier / Parzival** — taught Mura to mod Caves of Qud (credited in the Workshop description)
- **Arendeth** — population-table fixes (credited in `2.2 changelog.txt`)
- **Tyrir** — found the 2.2 typo batch and the invalid blueprint in Other Equipment (credited in `2.2 changelog.txt`)
- **Crow** — helped with bug fixes on the original (credited on the Workshop page)

> 📌 **Fork permission — granted publicly.** The live Workshop description now reads:
> *"Despite my original apprehension, I've decided to make the mod open to the community to
> update, fork, and generally do with as they please, all I ask is that you give credit where due,
> which includes Noble Lark for the subclass sprites."* Mura reiterated it in the discussions
> (*"It is indeed open for anyone to update, use, and fork as they want"*) and replied directly to
> this fork's request: *"@VixyGrey13 it's open to the community now, so feel free to do so, feel
> free to DM me if you have any questions."*
>
> **The one condition is credit** — and Noble Lark is named explicitly. Keep the list above intact
> in your Workshop description and in-repo.

---

## 13. Options (`Options.xml`)

Eleven options, all under **Category="Mods"** in Qud's own options menu. Declaring one is pure XML;
reading one requires C# — `mod/Scripting/Raven_Options.cs` holds all of them except the Joppa
building, which `Raven_JoppaBuildingSystem` reads because the building is map data rather than a
field on a loaded record.

Per charter rule 6, **defaults reproduce the mod's established behaviour**. The single exception is
the starting reputation bonus, which grants power with no content attached and so must be asked
for rather than opted out of.

> ✅ **Verified 2026-08-16: all eleven options work in game** (maintainer). Still the only evidence
> that they *behave* correctly, and worth stating rather than assuming. Since #136 the C# is compiled
> locally against the game's own assemblies, and #135 reads Qud's own build log back — but a compiler
> proves the code builds, not that an option does the right thing to a run. CodeQL cannot cover the C#
> either (see `docs/CHARTER.md` rule 5). What each option actually does is checked by playing it.

### 13.1 What each option does

| Option | Type | Default | Governs |
|---|---|---|---|
| Mutated Human mutation points | Slider 0–24 | **16** | `MutationPoints`. Vanilla gives 12. |
| Mutated Human hit points per level | Combo | **1-5** | `BaseHPGain`. `2-3` is what 2.2 shipped, `1-4` is vanilla. See §1.2. |
| extra skill points per level | Checkbox | **Yes** | `BaseSPGain` — 65 for mutants against vanilla's 50, 85 for True Kin against 70. |
| extra starting skills | Checkbox | **Yes** | Staunch Wounds, Cooking and Gathering, Meal Preparation; Menacing Stare for mutants. |
| eased skill requirements | Checkbox | **Yes** | The twenty retuned attribute requirements in §4. |
| retuned skill point costs | Checkbox | **Yes** | The four retuned prices in §4. |
| starting reputation bonus | Checkbox | **No** | +300 Joppa for mutants. §1.2. |
| psionic chips in loot | Checkbox | **Yes** | The six `Raven_Chips Tier N` references in Artifact 3–8. §7.3. |
| home base building in Joppa | Checkbox | **Yes** | The map patch in §8. |
| your own Chip Interface slots | Checkbox | **Yes** | The player's slots — 1 mutant, 2 True Kin. §3.1. |
| Chip Interface slots on other humanoids | Checkbox | **Yes** | The `Humanoid` anatomy merge, which reaches every humanoid NPC. §3.1. |

The Psionic Adept is deliberately outside every one of these. Its skills, reputation, four chip
slots and 95 skill points are the genotype rather than additions to a vanilla one, so there is no
vanilla value to restore and turning them off would leave a genotype with nothing.

### 13.2 When an option takes effect — three scopes

This is the distinction that decides how an option must be written and what its `<helptext>` has to
warn about. The charter's guidance to *prefer designs whose off-switch is a runtime decision* is
about moving features up this table.

| Scope | Options | Why |
|---|---|---|
| **Live** — applies immediately | chips in loot, retuned skill point costs, and — from your next level — hit points and skill points per level | Population tables stay mutable after load, `Cost` is a plain int with no cache, and `Leveler` re-reads `BaseHPGain`/`BaseSPGain` at every level-up. |
| **Restart** | eased skill requirements | `PowerEntry` caches its requirement list on first use and `InitRequirements()` returns early rather than rebuilding. The cache is private, and reaching it would need reflection, which rule 5 forbids. Declared `Restart="true"` — the attribute vanilla uses for `OptionEnableMods`. |
| **New character** | mutation points, starting skills, starting reputation, both Chip Interface options, Joppa building | Consumed once at chargen or baked into save state when a body or a zone is created. The Joppa building additionally **cannot be rebuilt** once removed from a save. |

### 13.3 Two constraints worth knowing before adding another option

- **A slider's `Min` must be 0 or 1.** Anything higher sends Qud's options menu into unbounded
  recursion and crashes the game with a stack overflow the moment the menu opens — a bug in the
  game, not the mod, which is why the crash points nowhere near its cause. Verified by bisection
  and by every slider across the 87 mods installed locally. `tools/validate_mod.py` refuses to let
  it back in. See issue #51.
- **Both directions of the wiring fail silently.** A declared option that nothing reads appears in
  the menu and does nothing; an option read but never declared makes `GetOption` return its
  fallback forever, so the feature is stuck at its default. Neither raises an error, and
  `validate_mod.py` checks both.

Anything that mutates loaded game data must also be **idempotent and reversible**: handlers run
repeatedly and in any order, so each one makes the data *match* the option rather than performing a
one-way edit. That is why every toggle here stores the vanilla value it replaced — the mod's XML
overwrote it at load, and the original is gone from memory by the time an option is read.

---

## Appendix A — every merged vanilla melee weapon

Full listing of the 79 `Load="Merge"` edits in `MeleeWeapons.xml`. Blank cells mean the mod did
not touch that field (the vanilla value is inherited).

| Blueprint | Tier | Damage | Pen | Max STR | Stat | Value | Weight |
|---|---|---|---|---|---|---|---|
| BaseAxe |  |  |  |  |  |  | 3 |
| Battle Axe | 0 |  |  |  |  | 5 | 4 |
| Battle Axe2 | 1 | 1d3 |  | 2 |  | 10 | 3 |
| Steel Battle Axe | 2 | 1d4 |  | 3 |  | 20 | 3 |
| Steel Battle Axeth | 2 | 1d4+2 | 1 | 3 |  | 20 | 5 |
| Battle Axe3 | 3 | 1d5 |  | 4 |  | 40 | 5 |
| Battle Axe3th | 3 | 1d5+2 | 1 | 4 |  | 40 | 8 |
| Battle Axe4 | 4 | 1d6+1 |  | 5 |  | 80 | 4 |
| Battle Axe4th | 4 | 1d6+3 | 1 | 5 |  | 80 | 6 |
| Battle Axe5 | 5 | 1d7+1 |  | 6 |  | 160 | 6 |
| Battle Axe5th | 5 | 1d7+3 | 1 | 6 |  | 160 | 9 |
| Battle Axe6 | 6 | 1d8+2 |  | 7 |  | 320 | 3 |
| Battle Axe7 | 7 | 1d9+2 |  | 8 |  | 640 | 3 |
| Battle Axe8 | 8 | 1d10+3 |  | 9 |  | 1280 | 2 |
| Iron Vinereaper | 1 | 1d3 |  | 2 | Agility | 10 | 2 |
| Steel Vinereaper | 2 | 1d4 |  | 3 | Agility | 20 | 2 |
| Battle Axe6th | 6 | 1d8+5 | 1 | 7 | Agility | 320 | 6 |
| Battle Axe7th | 7 | 1d9+5 | 1 | 8 | Agility | 640 | 6 |
| Battle Axe8th | 8 | 1d10+6 | 1 | 9 | Agility | 1280 | 5 |
| BaseLongBlade |  |  |  |  |  |  | 2 |
| Long Sword | 0 | 1d3 |  | 1 |  | 5 | 4 |
| Two-Handed Sword | 0 | 1d6 | 1 | 1 |  | 5 | 6 |
| Long Sword2 | 1 | 1d4 |  | 2 |  | 10 | 3 |
| Long Sword2th | 1 | 1d8 | 1 | 2 |  | 10 | 5 |
| Steel Long Sword | 2 | 1d6 |  | 3 |  | 20 | 3 |
| Steel Long Swordth | 2 | 1d10 | 1 | 3 |  | 20 | 5 |
| Long Sword3 | 3 | 1d8 |  | 4 |  | 40 | 5 |
| Long Sword3th | 3 | 1d12 | 1 | 4 |  | 40 | 7 |
| Long Sword4 | 4 | 1d10 |  | 5 |  | 80 | 4 |
| Long Sword4th | 4 | 2d6+1 | 1 | 5 |  | 80 | 6 |
| Long Sword5 | 5 | 1d12 |  | 6 |  | 160 | 6 |
| Long Sword5th | 5 | 2d8+1 | 1 | 6 |  | 160 | 9 |
| Long Sword6 | 6 | 2d6+1 |  | 7 |  | 320 | 3 |
| Long Sword6th | 6 | 2d8+2 |  | 7 |  | 320 | 5 |
| Long Sword7 | 7 | 2d8+1 |  | 8 |  | 640 | 3 |
| Long Sword7th | 7 | 2d10+1 | 1 | 8 |  | 640 | 5 |
| Long Sword8 | 8 | 2d8+2 |  | 9 |  | 1280 | 2 |
| Long Sword8th | 8 | 2d12+1 | 1 | 9 |  | 1280 | 4 |
| Vibro Blade | 5 | 1d10 |  | 0 |  | 300 | 4 |
| BaseDagger |  |  |  |  | Agility |  | 1 |
| BaseRelicDagger1 |  |  |  |  | Agility |  |  |
| BaseRelicDagger2 |  |  |  |  | Agility |  |  |
| Dagger | 0 | 1d2 |  | 1 |  | 5 | 1 |
| Dagger2 | 1 | 1d3 |  | 2 |  | 10 | 1 |
| Desert Kris | 1 | 1d3 |  | 2 |  | 10 | 1 |
| Steel Kukri | 2 | 1d4 |  | 3 |  | 20 | 1 |
| Steel Dagger | 2 | 1d4 |  | 3 |  | 20 | 1 |
| Steel Utility Knife | 2 | 1d4 |  | 3 |  | 20 | 1 |
| Steel Potter's Knife | 2 | 1d4 |  | 3 |  | 20 | 1 |
| Steel Butcher Knife | 2 | 1d4 |  | 3 |  | 20 | 1 |
| Dagger3 | 3 | 1d6 |  | 4 |  | 40 | 2 |
| Dagger4 | 4 | 1d8 |  | 5 |  | 80 | 2 |
| Obsidian Kris | 4 | 1d8 |  | 5 |  | 80 | 2 |
| Dagger5 | 5 | 1d10 |  | 6 |  | 160 | 3 |
| Dagger6 | 6 | 1d12 |  | 7 |  | 320 | 1 |
| Dagger7 | 7 | 2d6+1 |  | 8 |  | 640 | 1 |
| Dagger8 | 8 | 2d6+2 |  | 9 |  | 1280 | 1 |
| Vibro Dagger | 5 | 2d4 |  | 0 |  | 300 | 1 |
| ArmDagger4 | 4 | 2d3 |  | 5 |  | 75 | 2 |
| BaseCudgel |  |  |  |  |  |  | 3 |
| Club | 0 |  |  |  |  | 2 | 3 |
| Mace2 | 0 | 1d3 |  | 1 |  | 5 | 5 |
| Steel Hammer | 2 | 2d2 |  | 3 |  | 20 | 4 |
| Cudgel5th | 5 | 3d6 | 1 | 6 |  | 160 | 11 |
| Cudgel6 | 6 | 2d6+1 |  | 7 |  | 320 | 3 |
| Cudgel7 | 7 | 3d4+2 |  | 8 |  | 640 | 3 |
| Rhinox-Skull Maul | 6 | 3d4+1 | 2 | 7 |  | 480 | 10 |
| Warhammer2 | 1 | 1d4 |  | 2 | Agility | 10 | 3 |
| Steel War Hammer | 2 | 2d2 |  | 3 | Agility | 20 | 3 |
| Steel War Hammerth | 2 | 3d2 | 1 | 3 | Agility | 20 | 6 |
| Cudgel3 | 3 | 2d4 |  | 4 | Agility | 40 | 5 |
| Cudgel3th | 3 | 3d4 | 1 | 4 | Agility | 40 | 8 |
| Cudgel4 | 4 | 2d4+1 |  | 5 | Agility | 80 | 4 |
| Cudgel4th | 4 | 3d4+1 | 1 | 5 | Agility | 80 | 7 |
| Cudgel5 | 5 | 2d6 |  | 6 | Agility | 160 | 6 |
| Cudgel6th | 6 | 3d6+1 | 1 | 11 | Agility | 320 | 6 |
| Cudgel7th | 7 | 5d4+2 | 1 | 8 | Agility | 640 | 6 |
| Cudgel8 | 8 | 3d6+2 |  | 9 | Agility | 1200 | 3 |
| Cudgel8th | 8 | 5d6+2 | 1 | 9 | Agility | 1200 | 5 |

---

## Appendix B — every psionic chip

144 chips. `Mut. level` is the level of the granted mutation(s).

| Chip | Item tier | Value | Grants (mutation @ level) |
|---|---|---|---|
| basic disintegration chip | 4 | 20 | Disintegration @ 2 |
| upgraded disintegration chip | 6 | 40 | Disintegration @ 4 |
| perfected disintegration chip | 8 | 60 | Disintegration @ 6 |
| basic stunning force chip | 4 | 20 | StunningForce @ 2 |
| upgraded stunning force chip | 6 | 40 | StunningForce @ 4 |
| perfected stunning force chip | 8 | 60 | StunningForce @ 6 |
| basic force bubble chip | 4 | 20 | ForceBubble @ 2 |
| upgraded force bubble chip | 6 | 40 | ForceBubble @ 4 |
| perfected force bubble chip | 8 | 60 | ForceBubble @ 6 |
| basic force chipset | 6 | 20 | Disintegration @ 1, StunningForce @ 1, ForceBubble @ 1 |
| upgraded force chipset | 7 | 40 | Disintegration @ 2, StunningForce @ 2, ForceBubble @ 2 |
| perfected force chipset | 8 | 60 | Disintegration @ 3, StunningForce @ 3, ForceBubble @ 3 |
| basic kindle chip | 4 | 20 | Kindle @ 2 |
| upgraded kindle chip | 6 | 40 | Kindle @ 4 |
| perfected kindle chip | 8 | 60 | Kindle @ 6 |
| basic flaming ray chip | 4 | 20 | FlamingRay @ 3 |
| upgraded flaming ray chip | 6 | 40 | FlamingRay @ 6 |
| perfected flaming ray chip | 8 | 60 | FlamingRay @ 10 |
| basic pyrokinesis chip | 4 | 20 | Pyrokinesis @ 2 |
| upgraded pyrokinesis chip | 6 | 40 | Pyrokinesis @ 4 |
| perfected pyrokinesis chip | 8 | 60 | Pyrokinesis @ 6 |
| basic fire chipset | 6 | 20 | Kindle @ 1, FlamingRay @ 2, Pyrokinesis @ 1 |
| upgraded fire chipset | 7 | 40 | Kindle @ 2, FlamingRay @ 4, Pyrokinesis @ 2 |
| perfected fire chipset | 8 | 60 | Kindle @ 3, FlamingRay @ 6, Pyrokinesis @ 3 |
| basic frost webs chip | 4 | 20 | FrostWebs @ 3 |
| upgraded frost webs chip | 6 | 40 | FrostWebs @ 6 |
| perfected frost webs chip | 8 | 60 | FrostWebs @ 10 |
| basic freezing ray chip | 4 | 20 | FreezingRay @ 3 |
| upgraded freezing ray chip | 6 | 40 | FreezingRay @ 6 |
| perfected freezing ray chip | 8 | 60 | FreezingRay @ 10 |
| basic cryokinesis chip | 4 | 20 | Cryokinesis @ 2 |
| upgraded cryokinesis chip | 6 | 40 | Cryokinesis @ 4 |
| perfected cryokinesis chip | 8 | 60 | Cryokinesis @ 6 |
| basic ice chipset | 6 | 20 | FrostWebs @ 2, FreezingRay @ 2, Cryokinesis @ 1 |
| upgraded ice chipset | 7 | 40 | FrostWebs @ 4, FreezingRay @ 4, Cryokinesis @ 2 |
| perfected ice chipset | 8 | 60 | FrostWebs @ 6, FreezingRay @ 6, Cryokinesis @ 3 |
| basic EMP chip | 4 | 20 | ElectromagneticPulse @ 3 |
| upgraded EMP chip | 6 | 40 | ElectromagneticPulse @ 6 |
| perfected EMP chip | 8 | 60 | ElectromagneticPulse @ 10 |
| basic electrical generation chip | 4 | 20 | ElectricalGeneration @ 3 |
| upgraded electrical generation chip | 6 | 40 | ElectricalGeneration @ 6 |
| perfected electrical generation chip | 8 | 60 | ElectricalGeneration @ 10 |
| basic phasing chip | 4 | 20 | Phasing @ 3 |
| upgraded phasing chip | 6 | 40 | Phasing @ 6 |
| perfected phasing chip | 8 | 60 | Phasing @ 10 |
| basic lightning chipset | 6 | 20 | ElectromagneticPulse @ 2, ElectricalGeneration @ 2, Phasing @ 2 |
| upgraded lightning chipset | 7 | 40 | ElectromagneticPulse @ 4, ElectricalGeneration @ 4, Phasing @ 4 |
| perfected lightning chipset | 8 | 60 | ElectromagneticPulse @ 6, ElectricalGeneration @ 6, Phasing @ 6 |
| basic photosynthetic skin chip | 4 | 20 | PhotosyntheticSkin @ 3 |
| upgraded photosynthetic skin chip | 6 | 40 | PhotosyntheticSkin @ 6 |
| perfected photosynthetic skin chip | 8 | 60 | PhotosyntheticSkin @ 10 |
| basic light manipulation chip | 4 | 20 | LightManipulation @ 2 |
| upgraded light manipulation chip | 6 | 40 | LightManipulation @ 4 |
| perfected light manipulation chip | 8 | 60 | LightManipulation @ 6 |
| basic teleportation chip | 4 | 20 | Teleportation @ 2 |
| upgraded teleportation chip | 6 | 40 | Teleportation @ 4 |
| perfected teleportation chip | 8 | 60 | Teleportation @ 6 |
| basic light chipset | 6 | 20 | PhotosyntheticSkin @ 2, LightManipulation @ 1, Teleportation @ 1 |
| upgraded light chipset | 7 | 40 | PhotosyntheticSkin @ 4, LightManipulation @ 2, Teleportation @ 2 |
| perfected light chipset | 8 | 60 | PhotosyntheticSkin @ 6, LightManipulation @ 3, Teleportation @ 3 |
| basic corrosive gas chip | 4 | 20 | GasGeneration @ 3 |
| upgraded corrosive gas chip | 6 | 40 | GasGeneration @ 6 |
| perfected corrosive gas chip | 8 | 60 | GasGeneration @ 10 |
| basic confusion chip | 4 | 20 | Confusion @ 2 |
| upgraded confusion chip | 6 | 40 | Confusion @ 4 |
| perfected confusion chip | 8 | 60 | Confusion @ 6 |
| basic acid slime glands chip | 4 | 20 | AcidSlimeGlands @ 3 |
| upgraded acid slime glands chip | 6 | 40 | AcidSlimeGlands @ 6 |
| perfected acid slime glands chip | 8 | 60 | AcidSlimeGlands @ 10 |
| basic acid chipset | 6 | 20 | GasGeneration @ 2, Confusion @ 1, AcidSlimeGlands @ 2 |
| upgraded acid chipset | 7 | 40 | GasGeneration @ 4, Confusion @ 2, AcidSlimeGlands @ 4 |
| perfected acid chipset | 8 | 60 | GasGeneration @ 6, Confusion @ 3, AcidSlimeGlands @ 6 |
| basic syphon vim chip | 4 | 20 | LifeDrain @ 2 |
| upgraded syphon vim chip | 6 | 40 | LifeDrain @ 4 |
| perfected syphon vim chip | 8 | 60 | LifeDrain @ 6 |
| basic adrenal control chip | 4 | 20 | AdrenalControl2 @ 3 |
| upgraded adrenal control chip | 6 | 40 | AdrenalControl2 @ 6 |
| perfected adrenal control chip | 8 | 60 | AdrenalControl2 @ 10 |
| basic regeneration chip | 4 | 20 | Regeneration @ 3 |
| upgraded regeneration chip | 6 | 40 | Regeneration @ 6 |
| perfected regeneration chip | 8 | 60 | Regeneration @ 10 |
| basic blood chipset | 6 | 20 | LifeDrain @ 1, AdrenalControl2 @ 2, Regeneration @ 2 |
| upgraded blood chipset | 7 | 40 | LifeDrain @ 2, AdrenalControl2 @ 4, Regeneration @ 4 |
| perfected blood chipset | 8 | 60 | LifeDrain @ 3, AdrenalControl2 @ 6, Regeneration @ 6 |
| basic sunder mind chip | 4 | 20 | SunderMind @ 2 |
| upgraded sunder mind chip | 6 | 40 | SunderMind @ 4 |
| perfected sunder mind chip | 8 | 60 | SunderMind @ 6 |
| basic domination chip | 4 | 20 | Domination @ 2 |
| upgraded domination chip | 6 | 40 | Domination @ 4 |
| perfected domination chip | 8 | 60 | Domination @ 6 |
| basic mass mind chip | 4 | 20 | MassMind @ 2 |
| upgraded mass mind chip | 6 | 40 | MassMind @ 4 |
| perfected mass mind chip | 8 | 60 | MassMind @ 6 |
| basic mental chipset | 6 | 20 | SunderMind @ 1, Domination @ 1, MassMind @ 1 |
| upgraded mental chipset | 7 | 40 | SunderMind @ 2, Domination @ 2, MassMind @ 2 |
| perfected mental chipset | 8 | 60 | SunderMind @ 3, Domination @ 3, MassMind @ 3 |
| basic space-time vortex chip | 4 | 20 | SpacetimeVortex @ 2 |
| upgraded space-time vortex chip | 6 | 40 | SpacetimeVortex @ 4 |
| perfected space-time vortex chip | 8 | 60 | SpacetimeVortex @ 6 |
| basic time dilation chip | 4 | 20 | TimeDilation @ 2 |
| upgraded time dilation chip | 6 | 40 | TimeDilation @ 4 |
| perfected time dilation chip | 8 | 60 | TimeDilation @ 6 |
| basic temporal fugue chip | 4 | 20 | TemporalFugue @ 2 |
| upgraded temporal fugue chip | 6 | 40 | TemporalFugue @ 4 |
| perfected temporal fugue chip | 8 | 60 | TemporalFugue @ 6 |
| basic temporal chipset | 6 | 20 | SpacetimeVortex @ 1, TimeDilation @ 1, TemporalFugue @ 1 |
| upgraded temporal chipset | 7 | 40 | SpacetimeVortex @ 2, TimeDilation @ 2, TemporalFugue @ 2 |
| perfected temporal chipset | 8 | 60 | SpacetimeVortex @ 3, TimeDilation @ 3, TemporalFugue @ 3 |
| basic mental mirror chip | 4 | 20 | MentalMirror @ 2 |
| upgraded mental mirror chip | 6 | 40 | MentalMirror @ 4 |
| perfected mental mirror chip | 8 | 60 | MentalMirror @ 6 |
| basic teleport other chip | 4 | 20 | TeleportOther @ 2 |
| upgraded teleport other chip | 6 | 40 | TeleportOther @ 4 |
| perfected teleport other chip | 8 | 60 | TeleportOther @ 6 |
| basic force wall chip | 4 | 20 | ForceWall @ 2 |
| upgraded force wall chip | 6 | 40 | ForceWall @ 4 |
| perfected force wall chip | 8 | 60 | ForceWall @ 6 |
| basic neutral mind chipset | 6 | 20 | MentalMirror @ 1, TeleportOther @ 1, ForceWall @ 1 |
| upgraded neutral mind chipset | 7 | 40 | MentalMirror @ 2, TeleportOther @ 2, ForceWall @ 2 |
| perfected neutral mind chipset | 8 | 60 | MentalMirror @ 3, TeleportOther @ 3, ForceWall @ 3 |
| basic heightened quickness chip | 4 | 20 | HeightenedSpeed @ 3 |
| upgraded heightened quickness chip | 6 | 40 | HeightenedSpeed @ 6 |
| perfected heightened quickness chip | 8 | 60 | HeightenedSpeed @ 10 |
| basic ego projection chip | 4 | 20 | WillForce @ 2 |
| upgraded ego projection chip | 6 | 40 | WillForce @ 4 |
| perfected ego projection chip | 8 | 60 | WillForce @ 6 |
| basic heightened hearing chip | 4 | 20 | HeightenedHearing @ 3 |
| upgraded heightened hearing chip | 6 | 40 | HeightenedHearing @ 6 |
| perfected heightened hearing chip | 8 | 60 | HeightenedHearing @ 10 |
| basic neutral body chipset | 6 | 20 | HeightenedSpeed @ 2, WillForce @ 1, HeightenedHearing @ 2 |
| upgraded neutral body chipset | 7 | 40 | HeightenedSpeed @ 4, WillForce @ 2, HeightenedHearing @ 4 |
| perfected neutral body chipset | 8 | 60 | HeightenedSpeed @ 6, WillForce @ 3, HeightenedHearing @ 6 |
| basic clairvoyance chip | 4 | 20 | Clairvoyance @ 2 |
| upgraded clairvoyance chip | 6 | 40 | Clairvoyance @ 4 |
| perfected clairvoyance chip | 8 | 60 | Clairvoyance @ 6 |
| basic psychometry chip | 4 | 20 | Psychometry @ 2 |
| upgraded psychometry chip | 6 | 40 | Psychometry @ 4 |
| perfected psychometry chip | 8 | 60 | Psychometry @ 6 |
| basic precognition chip | 4 | 20 | Precognition @ 2 |
| upgraded precognition chip | 6 | 40 | Precognition @ 4 |
| perfected precognition chip | 8 | 60 | Precognition @ 6 |
| basic neutral spirit chipset | 6 | 20 | Clairvoyance @ 1, Psychometry @ 1, Precognition @ 1 |
| upgraded neutral spirit chipset | 7 | 40 | Clairvoyance @ 2, Psychometry @ 2, Precognition @ 2 |
| perfected neutral spirit chipset | 8 | 60 | Clairvoyance @ 3, Psychometry @ 3, Precognition @ 3 |
