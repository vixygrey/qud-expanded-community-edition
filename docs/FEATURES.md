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
| **New item blueprints** | **464** brand-new objects across 8 blueprint files |
| **Modified vanilla blueprints** | **211** `Load="Merge"` edits to existing objects |
| **New genotype** | Psionic Adept, with 18 subtypes |
| **New body system** | "Chip Interface" slots — 1 for humanoid NPCs, 2 for True Kin, 4 for Psionic Adepts; a Mutated Human has none (#353) |
| **New equipment system** | 144 psionic chips/chipsets granting real mutations to any genotype |
| **New weapon classes** | Katana, rapier, halberd, greataxe, greatsword, vinereaper (extended), wristblade, two-handed mace, war hammer, greathammer |
| **New armor classes** | Greatshield and vambrace (arm armor); the weave cloak, nanoweave and flexi lines completed from the one piece vanilla ships of each |
| **New ranged weapons** | 18 psionic pistols/rifles + 6 conventional guns |
| **Skill tree edits** | 6 skill trees retuned (Akimbo was added to Multiweapon Fighting upstream; removed in this fork — §4) |
| **Loot tables** | **77** vanilla tables merged — none replaced — plus 18 new starting-gear tables, 3 new chip tables + 1 helper |
| **World edits** | New amenity building in Joppa (76 map cells) |
| **Economy** | Vanilla's own prices on every merged item, including all 51 grenades (#334, #380) |

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

Every humanoid **NPC** also gains one Chip Interface slot (see §3). A Mutated Human player does
not, though vanilla's genotype shares that anatomy — see §3.1.

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

**What it is for.** A True Kin plans; an Adept adapts. A True Kin's power is a shopping list —
credits cost 150 water each, implants are chosen, and you install exactly what you saved for at a
becoming nook. An Adept's power is whatever the world hands it: **psionic chips cannot be bought and
cannot be built.** They carry no `TinkerItem` and no `DynamicObjectsTable` tag, and the only tables
naming them are `Artifact 3` through `8` — which is what `ChestBuilders` uses to fill a chest. So
they come out of chests, tier-scaled, and from nowhere else.

Chargen fills three of its four slots from its affinity's own kit, and everything after that is a
find. It is the one genotype whose build you cannot decide in advance, which is what its fiction
already says: a chip is *"knowledge lost eons ago"* that integrates with your flesh. **You become
what you find.**

The **95 skill points a level** — the highest in the game — are the counterweight. The Adept has no
innate power at all: no mutations, the fewest stat points of the three at 34, and the lowest hit
points. What it has instead is the broadest skill access in the game and a mutation kit assembled
from loot. **Skills and scavenging** is the fantasy.

> ⚪ **Its power curve is the opposite shape to a mutant's**, and that is deliberate rather than a
> defect to fix. A chip's rank is capped at its grade, so an Adept is at its strongest relative to
> the others around **character level 18** — where the rank cap reaches 10 and a perfected chip is
> finally worth its full value — and falls behind after 30, when a mutant's mutation-point income
> keeps climbing and the chips do not. Front-loaded breadth that plateaus. The working is in
> [`docs/DESIGN_balance.md`](DESIGN_balance.md) §5.8, and #350 records the one route past the
> plateau: chip levels sum, so two of the same mutation are worth twice the grade, at the cost of
> half your breadth.

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

> 🗒️ The chargen blurb reads `{{C|95}} skill points each level`, which is the Adept's
> `BaseSPGain` and is true under every option. It used to read *30 bonus*, and a note here called
> that stale — wrongly. **30 was the delta against this fork's own Mutated Human** (95 vs 65), which
> is the genotype most players arrive from. What made it wrong was not the number but the baseline:
> the Mutant's 65 is itself an option, so switching skill points off moved the real delta to 45
> while the panel still said 30. An absolute figure needs no baseline and cannot drift (#275).

---

## 2. Psionic Adept subtypes (`Subtypes.xml`)

18 subtypes in one class (`Affinities`, chargen title "choose expertise", singular "affinity"),
split into two categories:

- **The Lore Seekers of the Grand Library** (`Full Psionic`) — 9 caster subtypes.
- **The Immovable Wall of the Yttria** (`Half Psionic`) — 9 martial "Guardian" subtypes.

**Neither grants cybernetics license points.** The casters granted +1 each until #332: no vanilla
caste grants any, the genotype is the only source in the base game, and stacked with the implant
changes it was part of how elemental resistance reached 100.

Design rule stated in the source comments: each subtype nets **+2 to +3 stat points** after
subtracting penalties (True Kin net +3 to +4, Mutants net +2). Subtypes with elemental
resistances take a penalty resist equal to **half** their bonus.

**The two halves now use one resistance scale**, 20 against a −10 counterpart, which is what the
Guardians always used. The casters ran 40 / −20 until #332 — vanilla's castes are **always exactly
15 and never negative**, so 40 was 2.7x a number vanilla only ever states once.

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
| Mental, Guides of the Lost | -2 | -2 | -2 | +4 | +2 | +2 | — | Short Blades Expertise, Customs (+Trash Divining), Survival + **6 terrain survival skills** |
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
| Temporal, Support Battalion | +2 | +2 | +2 | **-6** | +1 | +1 | — | **the most skills in the game** — see below |

*Light Guardian also carries "Guaranteed one Solar Cell."*

**Temporal, Support Battalion** is the most generous subtype in the game: it trades a crippling
**-6 Intelligence** for base access to Axe, Bow and Rifle, Cooking and Gathering, Cudgel, Customs,
Discipline, Endurance, Persuasion, Physic, Survival, Tactics and Tinkering (plus Tinker I,
Disassemble and Scavenger) — **15 skills, 1,400 skill points**. Its own `extrainfo` says:
*"Starts with massively lowered Intelligence in exchange for so many skills."*

> ⚪ **That trade is now arithmetic rather than a claim (#330).** It granted **22 skills / 2,075 SP**
> against vanilla's most generous caste at 7 / 700 and its median at 5 / 450 — and it opened *every*
> base weapon tree, which is why it had no weapon identity of its own. `Leveler.RollSP` is
> `(Intelligence − 10) × 4` per level, so -6 Intelligence costs **24 SP a level**, about 720 over a
> full run. Vanilla's ceiling of 700 **plus** the 720 it pays is ≈1,400, which is what it grants now:
> the most skills in the game, and it pays for them exactly.
>
> The specialist weapon trees went — Multiweapon Fighting, Heavy Weapon, Long Blade, Pistol, Shield,
> Short Blade and Acrobatics — and the whole support kit stayed. A support unit keeps a sidearm and
> a long arm, not mastery of every weapon in the battalion.
>
> **`Mental, Guides of the Lost` came down with it**, from 12 skills / 825 SP to **10 / 700**, which
> is vanilla's ceiling exactly. It loses the firearm tree, which a guide has no call for, and the one
> terrain lore vanilla itself prices below the rest.

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
| `Humanoid` (merged) | **1** | Every humanoid NPC. A Mutated Human player shares this anatomy and has the slot taken off at chargen — see below |
| `TrueKin` (new) | **2** | Full custom anatomy; True Kin genotype points at this |
| `PsionicAdept` (new) | **4** | Psionic Adept anatomy |

> ✅ **Resolved in this fork (#13).** The original shipped a slot called **"Chipset Interface"**
> while every piece of Mura's player-facing documentation called it the **"Psionic Interface"**.
> Neither was accurate: the slot takes 108 chips against 36 chipsets, and 13 of the 36 mutations
> the chips grant are *physical* rather than mental. It is now **"Chip Interface"** — true of the
> whole catalogue, and consistent with the technological fiction in the chips' own description.

> ⚪ **A Mutated Human gets no slot (#353).** Vanilla's Mutated Human is `BodyObject="Humanoid"`, so
> the merge that gives every humanoid *NPC* a slot gave the mutant player one as a side-effect.
> Nobody chose that, and #352 found it made the mutant the **strongest chip user in the game**: a
> chip's level is a tracker that sums with a mutation's inherent `BaseLevel` before the rank cap, so
> one slot on a genotype that already mutates outperforms four on the genotype the chips were built
> for. It also contradicts §3's own statement of what chips are for — *"genotypes that cannot
> mutate"*. So `Raven_ChipSlotPlayerMutator` removes it at character creation. The anatomy is
> unchanged, because NPCs still get theirs and the type string has to stay live for the other two.
>
> **Existing characters keep it.** `IPlayerMutator.mutate` runs at chargen only, so a Mutated Human
> already in a save keeps the slot and anything in it. Nothing is orphaned.

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

**Two of them need a variant, and the stock base class does not supply one (#411).** `FlamingRay`
and `FreezingRay` derive the body part they fire from out of a chosen variant, and
`ModImprovedMutationBase` passes `null` for it — so `BodyPartType` stayed null and activating the
ability failed with *"Your  is too damaged to do that!"*, an empty body-part name printed straight
into the sentence. Both now inherit `Raven_ModVariantMutationBase`, which passes the variant
(`Ghostly Flames` and `Icy Vapor`, each the only one its mutation has) and then rebuilds the body's
default equipment so the slot is actually registered. Vanilla never meets this: its only three items
using that base class grant Confusion and Temporal Fugue, neither of which has variants.

**Physical vs mental scaling (2.2 change):** mental mutations keep scaling with Ego even when
granted by a chip; physical mutations do not scale at all. To compensate, chips granting
*physical* mutations give **3 / 6 / 10** levels instead of the **2 / 4 / 6** that mental chips give.
Chipsets follow the same split: **1 / 2 / 3** for mental, **2 / 4 / 6** for physical.

**Two mutations ignore their level, so their chips have no grades (#347).** `Kindle` and
`FrostWebs` both override `CanLevel()` to `false` and read their level nowhere — Kindle's cooldown
and range are constants, and Frost Webs sets its range and area as literals. They are the only two
of the 36 that do this. So all three Kindle chips are one item, all three Frost Webs chips are one
item, and each line is now named, priced and levelled as that one item: **one display name, 20
water at every tier, and the same granted level on all three**. The three blueprints stay, because
a shipped blueprint name is frozen (`docs/STYLEGUIDE.md` §1.1b) and anyone holding one in a save
would lose it. The item tier still differs, since that is what puts each in its own loot pool. The
Fire and Ice chipsets carry the same dead component and now state its true level too; their prices
are unchanged, because the other two mutations in each still scale.

**Chip levels sum on a mutation you already have (#350).** `ModImprovedMutationBase` adds a
tracker rather than setting a value, and `BaseMutation.CalcLevel` sums every tracker before
clamping — so two chips of one mutation are worth twice the grade, and a chip stacks on an inherent
mutation the same way. **This is vanilla's own behaviour, not something the fork added**: the Enigma
Cone and the Enigma Cap each carry `ModImprovedConfusion` at Tier 3, on the Body and Head slots, so
vanilla ships a deliberate stacking pair of its own. What limits it is the rank cap,
`level / 2 + 1`, which applies to the total from every source: two perfected chips reach tracker 20
and that cap does not reach 20 until **character level 38**, so a third copy is worth nothing before
then. Doubling up is also strictly worse below level 18, where the cap binds at 10 either way — it
buys depth after that, at the cost of half your breadth.

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
| basic (`Simple`) | Tier 4 · 20 · **2** (mental) or **3** (physical) | Tier 6 · 80 · **1** / **2** |
| upgraded (`Improved`) | Tier 6 · 80 · **4** / **6** | Tier 7 · 160 · **2** / **4** |
| perfected (`Advanced`) | Tier 8 · 320 · **6** / **10** | Tier 8 · 320 · **3** / **6** |

Values are the chip curve, `1.25 × 2^tier`, set in #338 — this table said 20 / 40 / 60 until #347
noticed it had not been updated with the blueprints. The Kindle and Frost Webs lines are the two
exceptions: every grade of each is 20, for the reason in §3.2.

> ✅ **All 144 chips can drop.** Upstream 2.2 shipped only *the first chip of each family* plus that
> family's chipset in `Raven_Chips Tier 1/2/3` — 24 entries where 48 were needed — so chips B and C
> of all 12 families appeared nowhere in `PopulationTables.xml`. Since no chip carries a
> `TinkerItem` part, they could not be built either, leaving **half the flagship catalogue
> wish-only**. Each tier table now holds **48** entries (#6, fixed in #36).
>
> The 18 `Vixy_StartingGear_*` tables still hand out only first-of-family chips and chipsets, which is
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

**That is the only route, and it was not until #481.** `Raven_Base Psionic Chip` inherits
`BaseArmor`, so all 144 chips descended from it and every pool the game fabricates from that base
picked them up — `DynamicInheritsTable:BaseArmor` ran **80% to 96% this fork's at tiers 4 and
above**, and it was chips the whole way down rather than armour.
`DynamicObjectsTable:Items` took them too, because `FabricateDynamicObjectsTable` filters on the
same `EncountersAPI.IsEligibleForDynamicEncounters` predicate that the inherits fabricator does.

Neither was a decision anyone made. Membership follows from `Inherits=`, so there was no line in
any diff to notice, and it quietly worked against §3.2's rule that **rarity is the access dial** for
chips rather than price. One `<tag Name="ExcludeFromDynamicEncounters" />` on the base fixes both,
because tags inherit — `BaseArmor:Tier8` goes 96% → 0%, and `Armor` tiers 4, 6 and 8 fall from
61–69% to 16–19%.

Nothing became harder to find: every chip is placed by hand, 48 apiece in `Raven_Chips Tier 1`–`3`
and three apiece across the eighteen `Vixy_StartingGear_` tables. What changed is that the hand-written
rates above are now the whole story.

`tools/dynamic-pools.json` pins the result, so a chip re-entering `DynamicObjectsTable:Items` fails
a commit rather than waiting to be noticed.

---

### 3.5 A follower can wear one, and it works

**Hand a psionic chip to a humanoid follower and they will equip it and gain the mutation — and use
it.** Verified in game (#417): a wished-up humanoid companion equipped a
`Raven_Simple Disintegration Chip` unprompted, gained Disintegration, and killed a snapjaw with it.

This is a real capability of the chip system and nothing described it until now. It follows from
chips being **worn armour rather than implants** — `Raven_Base Psionic Chip` inherits `BaseArmor`
and sits in the slot with `WornOn="Chip Interface"`, which puts it on the ordinary AI equip path,
and the grant fires on `EquippedEvent` targeting `E.Actor` — whoever wore it, not whoever is the
player. §13.1's callout traces every gate on that path.

Two things are worth knowing before you try it.

**The option gates it, and it gates it at creation.** *Chip Interface slots on other humanoids* adds
the slot to the `Humanoid` **anatomy**, which is the template a body is built from. A follower you
already have was built with whatever the anatomy said at the time and will never gain the slot
afterwards — switching the option on reaches only humanoids generated after it. That is not a defect;
it is what §13.2 means by an option read once, applied to a creature rather than to you.

**Nothing in this mod ever puts a chip on an NPC.** Chips reach the world through the artifact tables
that fill containers (#410), never through creature inventories, so this only ever happens because a
player chose to hand one over. That is the sense in which §13.1's original line was half right: no
creature is *generated* carrying one.

## 4. Skills (`Skills.xml`)

Seven trees are edited. Nothing is removed; requirements and costs are retuned, and **Finesse** is
sold by all four melee trees.

Both halves are optional, under two separate toggles — **eased skill requirements** and **retuned
skill point costs**. They are split because their scopes differ: costs apply immediately, while
requirements need a restart. See §13.

| Tree | Change |
|---|---|
| **Axe** | Every power (Cleave, Charging Strike, Dismember, Hook and Drag, Decapitate, Berserk!) now accepts **Strength *or* Agility** for its attribute minimum. Thresholds unchanged: 19/19/21/23/25/29. |
| **Cudgel** | Same treatment — Bludgeon 17, Charging Strike 19, Conk 21, Backswing 23, Slam 25, Demolish 29, each **Strength or Agility**. |
| **Long Blade** | *En Garde!* no longer needs both stats: it was Strength 29 **and** Agility 23 (either order); now it is **29 in Strength or Agility**. Adds **Finesse** (250, Agility 19). *Dueling Stance* is vanilla's again (#331). |
| **Short Blade** | Adds **Finesse** (250, Agility 19). The tree is otherwise untouched. |
| **Multiweapon Fighting** | *Multiweapon Expertise* **23 → 21**, *Multiweapon Mastery* **27 → 25**. Upstream 2.2 also added **Akimbo** here; this fork removed it — see below. |
| **Cooking and Gathering** | *Butchery* and *Spicer* cost **50 → 100** each, offsetting the free Cooking and Gathering + Meal Preparation every genotype now starts with. |
| **Tinkering** | *Reverse Engineer* cost **100 → 200**, the other half of the Cooking offset. Everything else is vanilla's: *Disassemble* costs 100 again, and *Tinker I / II / III* need Int **19 / 23 / 29** (#331). |

> ⚔️ **Finesse** is how an Agility character gets damage out of a blade.
>
> `MeleeWeapon.Stat` names the stat a weapon rolls **penetration** against, and the damage die is
> rolled once per penetration — so it multiplies a weapon's whole output. Vanilla uses Strength for
> it on every melee weapon in the game, which leaves an Agility build paying for to-hit and DV and
> getting no damage scaling at all.
>
> Finesse fixes that without handing it out free. A weapon tagged `Finesse` rolls penetration
> against your **Agility** modifier instead, whenever Agility is the higher of the two. Each finesse
> weapon says so in its own rules description.
>
> | tree | tagged weapons |
> |---|---|
> | **Short Blade** | daggers, knives, wristblades, spears |
> | **Long Blade** | rapiers, katanas |
> | **Axe** | vinereapers, glaives |
> | **Cudgel** | maces, quarterstaves |
>
> **The halberd and the war hammer are deliberately not on it.** #321 called them the two most
> genre-inverted assignments in the mod and that still holds — what #342 changed was the reading of
> the *trees*, not of those two weapons. Vanilla describes the vinereaper as a crescent for scything,
> which is a sickle, and Pathfinder's sickle carries finesse; its finesse bludgeon is likewise a
> mace-family weapon and never the warhammer. Both trees had a genre-legitimate finesse weapon all
> along. It was simply not the one the mod had picked.
>
> It applies only to weapons that roll against **Strength** in the first place. Vanilla has three
> that do not, and one of them — the crystalline jile, at `Stat="Ego"` — is a dagger, so it would
> otherwise have been converted into an Agility weapon by a power that never meant to touch it
> (#366). The vibro blades are excluded too: their `MaxStrengthBonus` is 0, so no penetration bonus
> of any kind reaches them.
>
> It costs 250 skill points and Agility 19, one purchase per tree. That price is the point: Agility
> already buys melee to-hit and DV, so letting it buy penetration for free would make every other
> melee stat pointless — the "Dex is the god stat" problem 5e is known for. Pathfinder charges a
> feat for the same crossover, and this is that trade in Qud's own currency.
>
> The reasoning is in [`docs/DESIGN_balance.md`](DESIGN_balance.md) §3.

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
<mod Part="ModGigantic" Load="Merge" TinkerAllowed="true" TinkerTier="7" />
```

**Gigantic becomes a tinkerable item mod.** You can now apply Gigantic to equipment yourself rather
than only finding it. Combined with the energy-cell notes below, Gigantic on a cell doubles max
charge and stacks with High Capacity.

**Tier 7 is the price of that**, added in #317. It puts the recipe alongside `ModNanon` and
`ModSuspensor` — the top of what vanilla lets anyone build. Without the attribute `ModEntry` defaults
`TinkerTier` to **1**, which is what shipped until now, and nothing vanilla allows at tier 1 is in
the same company: `ModGigantic.ApplyModification` calls `AdjustDamage(3)` on a melee weapon, and
damage is rolled **once per penetration**, so it is +3 *per penetration* rather than +3 flat.

> ⚖️ **What Gigantic costs the player is real, and easy to miss from the blueprint.**
> `GetSlotsRequiredEvent` does `E.Increases++`, so a gigantic item takes **one more equipment slot**
> unless the wielder is a gigantic creature — a gigantic one-handed sword needs both hands, and a
> gigantic shield does too. `GetAddedWeight()` is the blueprint's weight **× 4**, floored at 4, so a
> 6 lb greataxe becomes 30 lb. Those two are why the capability is worth keeping rather than
> reverting.
>
> One thing it does *not* do, contrary to how #317 first read it: the `× 3.333` value multiplier in
> `GetIntrinsicValueEvent` is gated on `GetIntProperty("Currency") > 0`, so it multiplies gigantic
> *currency* rather than gigantic weapons. An ordinary item gets the entry's `Value="1.5"`, in line
> with every tinkerable vanilla mod.

---

## 6. Items

### 6.1 Counts by file

| File | New objects | Merged vanilla objects |
|---|---|---|
| `MeleeWeapons.xml` | 101 (4 dormant) | 77 |
| `Armor.xml` | 61 | 38 |
| `RangedWeapons.xml` | 49 | 11 |
| `PsionicChips.xml` | 145 | 0 |
| `Cybernetics.xml` | 9 | 14 |
| `OtherEquipment.xml` | 7 | 16 |
| `Throwables.xml` | 0 | 51 |
| `Furniture.xml` | 4 | 0 |
| `Creatures.xml` | 46 | 1 |
| `Food.xml` | 12 | 2 |
| `Plants.xml` | 8 | 0 |
| `Ammo.xml` | 22 (22 dormant) | 1 |
| **Total** | **464 active** | **211** |

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
| Crysteel Greataxe | new | 6 | 1d8+4 | +1 | 7 | (inh) | 320 | 5 | yes |
| Flawless Crysteel Greataxe | new | 7 | 1d8+5 | +1 | 8 | (inh) | 640 | 5 | yes |
| Zetachrome Greataxe | new | 8 | 1d8+6 | +1 | 9 | (inh) | 1280 | 4 | yes |

#### Glaives (Axe, two-handed, Finesse) — **new family**

The Axe tree's two-handed finesse weapon, added in #342. Of Pathfinder's three polearms it is the one
whose identity survives translation: the halberd's traits are **reach** and **versatile**, and Qud has
neither, while the glaive's are flavour rather than mechanism. *"A long, single-edged blade on the end
of a 7-foot pole."*

Damage is **the greataxe's die one tier behind**, the same way the quarterstaff pays the maul — which
gives it a memorable property: **a glaive at tier N hits exactly as hard as a one-handed battle axe at
tier N+1.** Weight is the greataxe line minus one, per §3.2's light-for-its-class rule.

Neither the glaive nor a plain spear carries `finesse` in Pathfinder — the two-handed finesse
precedents are both elven weapons. This is a fork decision resting on the light-for-its-class rule
rather than an imported trait, recorded plainly so nobody later reads it as genre canon.

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Bronze Glaive | new | 0 | 1d3 | +1 | 1 | (inh) | 5 | 5 | yes |
| Iron Glaive | new | 1 | 1d2+1 | +1 | 2 | (inh) | 10 | 4 | yes |
| Steel Glaive | new | 2 | 1d3+1 | +1 | 3 | (inh) | 20 | 4 | yes |
| Carbide Glaive | new | 3 | 1d4+2 | +1 | 4 | (inh) | 40 | 7 | yes |
| Folded Carbide Glaive | new | 4 | 1d5+2 | +1 | 5 | (inh) | 80 | 5 | yes |
| Fullerite Glaive | new | 5 | 1d6+3 | +1 | 6 | (inh) | 160 | 8 | yes |
| Crysteel Glaive | new | 6 | 1d7+3 | +1 | 7 | (inh) | 320 | 4 | yes |
| Flawless Crysteel Glaive | new | 7 | 1d8+4 | +1 | 8 | (inh) | 640 | 4 | yes |
| Zetachrome Glaive | new | 8 | 1d8+5 | +1 | 9 | (inh) | 1280 | 3 | yes |

`Vixy_Vibro Glaive` follows the vibro convention — tier 5, value 300, `ChargeUse="100"`, bits `0015`.

The tile is this fork's own art, `mod/Textures/items/Vixy_Glaive.png` — a broad single-edged blade
with a back-spur at the socket, so it reads as a chopping weapon rather than the spear's thrusting
point. One 16×24 sprite recoloured across all nine tiers by `ColorString`.

#### Halberds (Axe, two-handed, Strength) — **new family**

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Bronze Halberd | new | 0 | 1d2+1 | +1 | 1 |  | 5 | 7 | yes |
| Iron Halberd | new | 1 | 1d3+1 | +1 | 2 |  | 10 | 6 | yes |
| Steel Halberd | new | 2 | 1d4+2 | +1 | 3 |  | 20 | 6 | yes |
| Carbide Halberd | new | 3 | 1d5+2 | +1 | 4 |  | 40 | 8 | yes |
| Folded Carbide Halberd | new | 4 | 1d6+3 | +1 | 5 |  | 80 | 7 | yes |
| Fullerite Halberd | new | 5 | 1d7+3 | +1 | 6 |  | 160 | 9 | yes |
| Vibro Halberd | new | 5 | 1d6+3 | +0 | 0 |  | 300 | 7 | yes |

#### Vinereapers (Axe, one-handed, Finesse) — vanilla family, completed to all tiers

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Bronze Vinereaper | new | 0 | 1d2 | +0 | 1 |  | 5 | 3 |  |
| Iron Vinereaper | merge | 1 | 1d3 | +0 | 2 |  | 5 | 2 |  |
| Steel Vinereaper | merge | 2 | 1d4 | +0 | 3 |  | 35 | 2 |  |
| Carbide Vinereaper | new | 3 | 1d5 | +0 | 4 |  | 40 | 4 |  |
| Folded Carbide Vinereaper | new | 4 | 1d6+1 | +0 | 5 |  | 80 | 3 |  |
| Fullerite Vinereaper | new | 5 | 1d7+1 | +0 | 6 |  | 160 | 5 |  |
| Vibro Vinereaper | new | 5 | 1d6+1 | +0 | 0 |  | 300 | 3 |  |
| Crysteel Vinereaper | new | 6 | 1d8+2 | +0 | 7 |  | 320 | 3 |  |
| Flawless Crysteel Vinereaper | new | 7 | 1d9+2 | +0 | 8 |  | 640 | 3 |  |
| Zetachrome Vinereaper | new | 8 | 1d10+3 | +0 | 9 |  | 1280 | 2 |  |

#### Katanas (Long Blades, two-handed, Finesse) — **new family**

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Bronze Katana | new | 0 | 1d6 | +1 | 1 |  | 5 | 6 | yes |
| Iron Katana | new | 1 | 1d8 | +1 | 2 |  | 10 | 5 | yes |
| Steel Katana | new | 2 | 1d10 | +1 | 3 |  | 20 | 5 | yes |
| Carbide Katana | new | 3 | 1d12 | +1 | 4 |  | 40 | 7 | yes |
| Folded Carbide Katana | new | 4 | 2d6 | +1 | 5 |  | 80 | 6 | yes |
| Fullerite Katana | new | 5 | 2d6+1 | +1 | 6 |  | 160 | 9 | yes |
| Vibro Katana | new | 5 | 2d8 | +0 | 0 |  | 300 | 6 | yes |
| Crysteel Katana | new | 6 | 2d8 | +1 | 7 |  | 320 | 4 | yes |
| Flawless Crysteel Katana | new | 7 | 2d10 | +1 | 8 |  | 640 | 4 | yes |
| Zetachrome Katana | new | 8 | 2d12 | +1 | 9 |  | 1280 | 3 | yes |

#### Rapiers (Long Blades, one-handed, Finesse) — **new family**

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Bronze Rapier | new | 0 | 1d3 | +0 | 1 |  | 5 | 3 |  |
| Iron Rapier | new | 1 | 1d4 | +0 | 2 |  | 10 | 3 |  |
| Steel Rapier | new | 2 | 1d6 | +0 | 3 |  | 20 | 3 |  |
| Carbide Rapier | new | 3 | 1d8 | +0 | 4 |  | 40 | 4 |  |
| Folded Carbide Rapier | new | 4 | 1d10 | +0 | 5 |  | 80 | 3 |  |
| Fullerite Rapier | new | 5 | 1d12 | +0 | 6 |  | 160 | 4 |  |
| Vibro Rapier | new | 5 | 1d10 | +0 | 0 |  | 300 | 3 |  |
| Crysteel Rapier | new | 6 | 2d6 | +0 | 7 |  | 320 | 2 |  |
| Flawless Crysteel Rapier | new | 7 | 2d6+1 | +0 | 8 |  | 640 | 2 |  |
| Zetachrome Rapier | new | 8 | 2d8 | +0 | 9 |  | 1280 | 2 |  |

#### Spears (Short Blades, two-handed, Finesse) — **new family**

**The only two-handed weapon in the Short Blades tree**, added in #342. That gap was the reason for
it: Single Weapon Fighting zeroes every non-primary intrinsic attack, so a two-handed weapon has
already paid its cost — and a short-blade specialist was the one build that could never take the
skill cheaply. Pathfinder's elven branched spear is the precedent for a two-handed finesse weapon.

Damage sits at the **midpoint between the dagger line and the two-handed long sword line** at each
tier — above its own tree's one-handed line, below the two-handed line of the tree above. The Short Blades tree
is already the finesse tree, so unlike the quarterstaff the spear does not pay for finesse twice.
Weight is the katana line minus one, keeping §3.2's light-for-its-class rule.

Deliberately **not** throwable, though PF2e's spear is and the whole dagger line carries
`ThrownWeapon`: the two-handed spear exists to fill a build gap, not to do a second job.

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Bronze Spear | new | 0 | 1d4 | +1 | 1 | (inh) | 5 | 5 | yes |
| Iron Spear | new | 1 | 1d5 | +1 | 2 | (inh) | 10 | 4 | yes |
| Steel Spear | new | 2 | 1d7 | +1 | 3 | (inh) | 20 | 4 | yes |
| Carbide Spear | new | 3 | 1d9 | +1 | 4 | (inh) | 40 | 6 | yes |
| Folded Carbide Spear | new | 4 | 2d5 | +1 | 5 | (inh) | 80 | 5 | yes |
| Fullerite Spear | new | 5 | 2d6 | +1 | 6 | (inh) | 160 | 8 | yes |
| Crysteel Spear | new | 6 | 2d7 | +1 | 7 | (inh) | 320 | 3 | yes |
| Flawless Crysteel Spear | new | 7 | 2d8 | +1 | 8 | (inh) | 640 | 3 | yes |
| Zetachrome Spear | new | 8 | 2d10 | +1 | 9 | (inh) | 1280 | 2 | yes |

`Vixy_Vibro Spear` follows the vibro convention — tier 5, value 300, `ChargeUse="100"`, bits `0015`.

The tile is this fork's own art, `mod/Textures/items/Vixy_Spear.png` — one 16×24 drawing recoloured
across all nine tiers by `ColorString`, with the head and butt-ferrule taking the tier colour and the
haft taking `DetailColor`.

#### Wristblades / arm daggers (Short Blades) — **new family**

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Bronze Wristblade | new | 0 | 1 | +0 | 1 | (inh) | 5 | 1 |  |
| Iron Wristblade | new | 1 | 1d2 | +0 | 2 | (inh) | 10 | 1 |  |
| Steel Wristblade | new | 2 | 1d2 | +0 | 3 | (inh) | 20 | 1 |  |
| Carbide Wristblade | new | 3 | 1d3 | +0 | 4 | (inh) | 40 | 2 |  |
| ArmDagger4 | merge | 4 | 1d4 |  | 5 |  | 75 | 1 |  |
| Fullerite Wristblade | new | 5 | 1d6 | +0 | 6 | (inh) | 160 | 3 |  |
| Vibro Wristblade | new | 5 | 1d4+1 | +0 | 0 | (inh) | 300 | 1 |  |
| Crysteel Wristblade | new | 6 | 2d3 | +0 | 7 | (inh) | 320 | 1 |  |
| Flawless Crysteel Wristblade | new | 7 | 1d8 | +0 | 8 | (inh) | 640 | 1 |  |
| Zetachrome Wristblade | new | 8 | 2d4 | +0 | 9 | (inh) | 1280 | 1 |  |

**Two things worth knowing before building around these.**

**They attack from the Arm slot**, and `BodyPart.ScanForWeapon` walks every body part, so two arms
plus two hands is **four attack attempts a round**. That is vanilla's mechanic, not this fork's —
what the fork changed is availability: vanilla ships exactly one wristblade, `ArmDagger4` at tier 4,
and one item at one tier is a find rather than a build. The damage is priced against that extra
attack at roughly 60% of the dagger of the same tier (#324, and `docs/STYLEGUIDE.md` §3.2.1). Vanilla
prices its own at full parity — `ArmDagger4` **is** `Dagger4` — because it never had to price a build.

**Single Weapon Fighting turns them off, and it defaults to on.** While that ability is toggled on,
`SingleWeaponFighting_Ability` multiplies the attack chance of every non-primary body part by zero,
and the combat loop marks only the first part primary — so your wristblades make **no attacks at
all**. The skill's own bonuses need the toggle on, so the two are alternatives you switch between
rather than combine. This is vanilla's behaviour and applies to your off-hand weapon just the same,
but it is worth stating here, because a new character who buys Single Weapon Fighting and then
straps on wristblades will see nothing happen and have no obvious reason why.

#### Maces, one-handed (Cudgel, Finesse)

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Mace2 | merge | 0 | 1d3 | +0 | 1 | (inh) | 10 | 3 |  |
| Iron Mace | new | 1 | 2 | +0 | 2 | (inh) | 10 | 2 |  |
| Carbide Mace | new | 3 | 2d3 | +0 | 4 | (inh) | 40 | 4 |  |
| Folded Carbide Mace | new | 4 | 2d4 | +0 | 5 | (inh) | 80 | 3 |  |
| Fullerite Mace | new | 5 | 2d4+1 | +0 | 6 | (inh) | 160 | 5 |  |
| Zetachrome Mace | new | 8 | 3d4+1 | +0 | 9 | (inh) | 1280 | 2 |  |

#### Maces, two-handed (Cudgel, Strength) — **new family**

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Bronze Maceth | new | 0 | 2d2 | +1 | 1 | (inh) | 5 | 6 | yes |
| Iron Maceth | new | 1 | 2d2+1 | +1 | 2 | (inh) | 10 | 5 | yes |
| Steel Maceth | new | 2 | 3d2 | +1 | 3 | (inh) | 20 | 5 | yes |
| Carbide Maceth | new | 3 | 2d4+1 | +1 | 4 | (inh) | 40 | 7 | yes |
| Folded Carbide Maceth | new | 4 | 2d6 | +1 | 5 | (inh) | 80 | 6 | yes |
| Crysteel Maceth | new | 6 | 3d4+1 | +1 | 7 | (inh) | 320 | 5 | yes |
| Flawless Crysteel Maceth | new | 7 | 3d6 | +1 | 8 | (inh) | 640 | 5 | yes |
| Zetachrome Maceth | new | 8 | 4d6 | +1 | 9 | (inh) | 1280 | 5 | yes |

#### Quarterstaves (Cudgel, two-handed, Finesse) — **new family**

The Cudgel tree's two-handed finesse weapon, added in #342. Pathfinder files both the staff and the
bo staff in the **club** group and tags each `monk` — the trait that has always meant Dexterity in
both systems — so the staff is where a finesse two-handed cudgel comes from. It is the lightest of
the three two-handed cudgel lines at every tier, per §3.2's rule that a finesse weapon is light for
its class, and it deals **the maul's die one tier behind**, which is what the finesse costs.

Wood rather than metal, so no `Metal` part — matching vanilla's own `Staff` and `Club`. The tier
material is the ferrule, not the shaft, which is what a shod quarterstaff actually is.

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Bronze Quarterstaff | new | 0 | 1d3 | +1 | 1 | (inh) | 5 | 5 | yes |
| Iron Quarterstaff | new | 1 | 2d2 | +1 | 2 | (inh) | 10 | 4 | yes |
| Steel Quarterstaff | new | 2 | 2d2+1 | +1 | 3 | (inh) | 20 | 4 | yes |
| Carbide Quarterstaff | new | 3 | 3d2 | +1 | 4 | (inh) | 40 | 6 | yes |
| Folded Carbide Quarterstaff | new | 4 | 2d4+1 | +1 | 5 | (inh) | 80 | 5 | yes |
| Fullerite Quarterstaff | new | 5 | 2d6 | +1 | 6 | (inh) | 160 | 7 | yes |
| Crysteel Quarterstaff | new | 6 | 3d4 | +1 | 7 | (inh) | 320 | 4 | yes |
| Flawless Crysteel Quarterstaff | new | 7 | 3d4+1 | +1 | 8 | (inh) | 640 | 4 | yes |
| Zetachrome Quarterstaff | new | 8 | 3d6 | +1 | 9 | (inh) | 1280 | 4 | yes |

`Vixy_Vibro Quarterstaff` follows the vibro convention — tier 5, value 300, `ChargeUse="100"`,
bits `0015`.

#### War hammers (Cudgel, Strength)

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Bronze War Hammer | new | 0 | 1d3 | +0 | 1 |  | 5 | 4 |  |
| Bronze War Hammerth | new | 0 | 2d2 | +1 | 1 |  | 5 | 7 | yes |
| Iron War Hammerth | new | 1 | 2d2+1 | +1 | 2 |  | 10 | 6 | yes |
| Steel War Hammer | merge | 2 | 2d2 | +0 | 3 |  | 20 | 3 |  |
| Steel War Hammerth | merge | 2 | 3d2 | +1 | 3 |  | 20 | 6 |  |
| Crysteel War Hammer | new | 6 | 2d6 | +0 | 7 |  | 320 | 3 |  |
| Flawless Crysteel War Hammer | new | 7 | 3d4 | +0 | 8 |  | 640 | 3 |  |

#### Greathammers (Cudgel, Strength)

| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |
|---|---|---|---|---|---|---|---|---|---|
| Fullerite Greathammer | new | 5 | 6d2 | +1 | 6 |  | 160 | 9 |  |

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

- **Vambraces** — a full tier 0–8 line of `Arm`-slot armor built on vanilla's `BaseArmlet`. Vanilla fills that slot with bracelets and gadgets and never with armor: no arm item in the game grants more than a single point of AV, and across all 28 of them **not one carries a negative DV**. So the line is held to the slot rather than allowed to reshape it — AV 1, DV 0 and a pound at every tier, matching vanilla's own numbers (#318, #381). What separates the nine is price, which makes them flavour rather than a progression, and that is deliberate: the Arm slot is for utility artifacts, and a vambrace is what you wear until you find one.
- **Greatshields** — a full tier 0–8 line of two-handed-feel `Hand` shields with the highest AV in the game (3 → 10) at a DV cost.
- **Bio-scanner mask** and **mutating mask** — two `Face`-slot artifacts.
- **Reinforced suspension** — `Tread`-slot accessory for the mechanical-legs build.

Vanilla families completed:

- **Weave cloaks** at every tier (bronzeweave → zetachromeweave), filling out the vanilla ironweave cloak.
- **Nanoweave** and **Flexi** sets — vanilla ships the vest of each and nothing to go with it; helmet, gloves, boots and cloak complete both lines. They trade AV for **positive DV**, which vanilla's metal armor never gives.


#### Feet

| Blueprint | New? | Tier | Slot | AV | DV | Resists (H/C/A/E) | Value | Weight |
|---|---|---|---|---|---|---|---|---|
| Bronze Boots | new | 0 | Feet | 2 | -2 | — | 5 | 8 |
| Iron Boots | new | 1 | Feet | 2 | -1 | — | 10 | 7 |
| Chain Boots | merge | 2 | Feet | 2 | -2 | — | 20 | 6 |
| Steel Boots | merge | 2 | Feet | 3 | -3 | — | 20 | 7 |
| Carbide Boots | merge | 3 | Feet | 3 | -2 | — | 40 | 9 |
| Flawless Crysteel Boots | merge | 7 | Feet | 4 | 0 | 5/5/5/5 | 650 | 6 |
| Folded Carbide Boots | new | 4 | Feet | 3 | -1 | — | 80 | 8 |
| Fullerite Boots | merge | 5 | Feet | 4 | -4 | — | 195 | 10 |
| Flexiboots | new | 5 | Feet | 1 | 3 | — | 160 | 2 |
| Crysteel Boots | merge | 6 | Feet | 4 | -2 | 5/5/5/5 | 400 | 6 |
| Nanoweave Boots | new | 6 | Feet | 3 | 1 | — | 300 | 3 |
| Zetachrome Pumps | merge | 8 | Feet | 4 | 0 | 6/6/6/6 | 1500 | 5 |

#### Hands

| Blueprint | New? | Tier | Slot | AV | DV | Resists (H/C/A/E) | Value | Weight |
|---|---|---|---|---|---|---|---|---|
| Bronze Gauntlets | new | 0 | Hands | 2 | -2 | — | 5 | 8 |
| Iron Gauntlets | new | 1 | Hands | 2 | -1 | — | 10 | 7 |
| Steel Gauntlets | merge | 2 | Hands | 3 | -3 | — | 20 | 7 |
| Carbide Gauntlets | merge | 3 | Hands | 3 | -2 | — | 40 | 9 |
| Folded Carbide Gauntlets | new | 4 | Hands | 3 | -1 | — | 80 | 8 |
| Fullerite Gauntlets | merge | 5 | Hands | 4 | -4 | — | 195 | 10 |
| Flexigloves | new | 5 | Hands | 1 | 2 | — | 160 | 2 |
| Crysteel Gauntlets | merge | 6 | Hands | 4 | -2 | 5/5/5/5 | 400 | 6 |
| Nanoweave Gloves | new | 6 | Hands | 2 | 1 | — | 300 | 3 |
| Flawless Crysteel Gauntlets | merge | 7 | Hands | 4 | 0 | 5/5/5/5 | 650 | 6 |
| Zetachrome Gloves | merge | 8 | Hands | 4 | 0 | 5/5/5/5 | 1500 | 5 |
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
| Fullerite Armet | merge | 5 | Head | 4 | -4 | — | 95 | 12 |
| Flexihelmet | new | 5 | Head | 1 | 2 | — | 160 | 2 |
| Crysteel Coronet | merge | 6 | Head | 4 | -2 | 5/5/5/5 | 400 | 8 |
| Nanoweave Helmet | new | 6 | Head | 2 | 1 | — | 300 | 3 |
| Flawless Crysteel Coronet | merge | 7 | Head | 4 | 0 | 5/5/5/5 | 650 | 8 |
| Zetachrome Apex | merge | 8 | Head | 4 | 0 | 6/6/6/6 | 1500 | 7 |

#### Body

| Blueprint | New? | Tier | Slot | AV | DV | Resists (H/C/A/E) | Value | Weight |
|---|---|---|---|---|---|---|---|---|
| Bronze Plate Armor | new | 0 | Body | 3 | -3 | — | 8 | 24 |
| Iron Plate Armor | new | 1 | Body | 3 | -1 | — | 16 | 21 |
| Chain Mail | merge | 2 | (inh) | - | - | — | 25 | 15 |
| Steel Plate Mail | merge | 2 | Body | 4 | -4 | — | 32 | 26 |
| Carbide Plate Armor | merge | 3 | Body | 4 | -2 | — | 64 | 20 |
| Folded Carbide Plate Armor | new | 4 | Body | 6 | -4 | — | 128 | 24 |
| Fullerite Flake Armor | merge | 5 | Body | 4 | -2 | 12/12/3/3 | 320 | 40 |
| Fullerite Plate Mail | merge | 5 | Body | 6 | -2 | — | 345 | 70 |
| Crysteel Shardmail | merge | 6 | Body | 8 | -4 | — | 1200 | 18 |
| Flawless Crysteel Shardmail | merge | 7 | Body | 8 | -2 | 9/9/9/9 | 1900 | 18 |
| Zetachrome Lune | merge | 8 | Body | 8 | -2 | 10/10/10/10 | 6000 | 15 |

#### Back (cloaks)

| Blueprint | New? | Tier | Slot | AV | DV | Resists (H/C/A/E) | Value | Weight |
|---|---|---|---|---|---|---|---|---|
| Bronzeweave Cloak | new | 0 | Back | 1 | -1 | — | 5 | 4 |
| Ironweave Cloak | merge | 1 | Back | 1 | 0 | — | 10 | 3 |
| Steelweave Cloak | new | 2 | Back | 2 | -2 | — | 20 | 3 |
| Carbideweave Cloak | new | 3 | Back | 2 | -1 | — | 40 | 6 |
| Folded Carbideweave Cloak | new | 4 | Back | 2 | 0 | — | 80 | 5 |
| Flexicloak | new | 5 | Back | 1 | 2 | — | 160 | 2 |
| Fulleriteweave Cloak | new | 5 | Back | 2 | -2 | — | 160 | 6 |
| Crysteelweave Cloak | new | 6 | Back | 2 | -3 | 6/6/6/6 | 320 | 3 |
| Nanoweave Cloak | new | 6 | Back | 2 | 1 | — | 300 | 3 |
| Flawless Crysteelweave Cloak | new | 7 | Back | 2 | -1 | 6/6/6/6 | 640 | 3 |
| Zetachromeweave Cloak | new | 8 | Back | 2 | 0 | 6/6/6/6 | 1280 | 2 |
| Portable Beehive | merge | - | Back | 0 | 1 | — | - | - |

#### Arm (vambraces — new slot usage)

| Blueprint | New? | Tier | Slot | AV | DV | Resists (H/C/A/E) | Value | Weight |
|---|---|---|---|---|---|---|---|---|
| Bronze Vambrace | new | 0 | Arm | 1 | 0 | — | 4 | 1 |
| Iron Vambrace | new | 1 | Arm | 1 | 0 | — | 8 | 1 |
| Steel Vambrace | new | 2 | Arm | 1 | 0 | — | 16 | 1 |
| Carbide Vambrace | new | 3 | Arm | 1 | 0 | — | 32 | 1 |
| Folded Carbide Vambrace | new | 4 | Arm | 1 | 0 | — | 64 | 1 |
| Fullerite Vambrace | new | 5 | Arm | 1 | 0 | — | 128 | 1 |
| Crysteel Vambrace | new | 6 | Arm | 1 | 0 | 5/5/5/5 | 256 | 1 |
| Flawless Crysteel Vambrace | new | 7 | Arm | 1 | 0 | 5/5/5/5 | 512 | 1 |
| Zetachrome Vambrace | new | 8 | Arm | 1 | 0 | 6/6/6/6 | 1024 | 1 |

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
| Steel Buckler | merge | 2 | Arm | 2 | -1 | 50 | 3 |
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
| Steel Shield | merge | 2 | (inh) | - | - | 50 | 7 |
| Carbide Shield | merge | 3 | Hand | 4 | -2 | 50 | 10 |
| Folded Carbide Shield | new | 4 | Hand | 5 | -3 | 80 | 9 |
| Fullerite Shield | merge | 5 | Hand | 5 | -2 | 200 | 12 |
| Crysteel Shield | merge | 6 | Hand | 6 | -2 | 300 | 6 |
| Flawless Crysteel Shield | merge | 7 | Hand | 7 | -2 | 450 | 6 |
| Zetachrome Shield | new | 8 | Hand | 8 | -1 | 1280 | 5 |

#### Greatshields — **new family** (Hand slot)

| Blueprint | New? | Tier | Slot | AV | DV | Value | Weight |
|---|---|---|---|---|---|---|---|
| Bronze Greatshield | new | 0 | Hand | 3 | -3 | 5 | 11 |
| Iron Greatshield | new | 1 | Hand | 3 | -2 | 10 | 10 |
| Steel Greatshield | new | 2 | Hand | 4 | -3 | 20 | 10 |
| Carbide Greatshield | new | 3 | Hand | 5 | -3 | 40 | 13 |
| Folded Carbide Greatshield | new | 4 | Hand | 6 | -3 | 80 | 12 |
| Fullerite Greatshield | new | 5 | Hand | 6 | -3 | 160 | 15 |
| Crysteel Greatshield | new | 6 | Hand | 7 | -3 | 320 | 9 |
| Flawless Crysteel Greatshield | new | 7 | Hand | 8 | -3 | 640 | 9 |
| Zetachrome Greatshield | new | 8 | Hand | 9 | -2 | 1280 | 7 |

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
| Fine-tuned handgun | 6 | Pistol | 2 (2 ammo) | 10 slugs | **1** (near-perfect) | 1 | 750 | Projectile pen 8 / 1d8. Turret name "miniature burstfire turret" |
| Modified handcannon | 5 | Pistol | 8 (1 ammo) | 4 shotgun shells | 30 | 12 | 400 | Fires shotgun shells from a handcannon; pellets pen 4 / 1d2 |
| Drum shotgun | 3 | Rifle | 10 (2 ammo, 10/anim) | 20 shells | 36 | 6 | 125 | `NoWildfire`, two-slot, weight 16 |
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
| **Steel dermal plating** | 1 | Body | +1 AV | 6 |
| **Crysteel dermal plating** | 6 | Body, Head, Back | +2 AV | 12 |
| **Zetachrome dermal plating** | 9 | Body, Head, Back | +3 AV | 16 |
| **Omni pass** | 2 | Hands, Feet, Body, Back, Face, Arm, Head | **Walk through forcefields and unlock any door** (`DoorUnlocker:1` + `CyberneticsForcefieldNullifier`). Tagged `StartingCybernetic:General` | 0 |
| **Steel hand bones** | 1 | Hands | Fists deal **1d5** (`Raven_SteelFist`, tier 3) | 10 |
| **Zetachrome hand bones** | 8 | Hands | Fists deal **3d6** (`Raven_ZetachromeFist`, tier 8, `Zetachrome` part) | 10 |

Plus the two supporting fist weapons (`Raven_SteelFist`, `Raven_ZetachromeFist`), both `MaxStrengthBonus="999"`.

#### Merged vanilla implants

| Implant | Change |
|---|---|
| Carbide dermal plating (`DermalPlating`) | Renamed to **carbide** dermal plating. Cost and effect are vanilla's — 3 points, +1 AV |
| Crysteel hand bones | Weight 10 and a custom tile; cost, value and **3d4** fist damage are vanilla's |
| Fullerite hand bones / fist | Vanilla's **2d4+1** |
| Motorized treads | `SaveModifier` +6 vs Move, Knockdown, Knockback, Restraint, Drag (EMP-sensitive, tech-scannable) |
| Air current microsensor, Nocturnal apex, Rapid release finger flexors | New custom tiles and color strings |

> ⚪ **The buffs that used to be in this table were reverted in #335.** Eight implants had been made
> cheaper, stronger, or both — `DermalPlating` at 2 points for +2 AV against vanilla's 3 for +1,
> both insulations at +10 and +20 against +6 and +9, the ankle tendons doubled, `CherubicVisage` at
> +2 Ego, `OpticalMultiscanner` at 4 points and 240 water against 8 and 600.
>
> **What made it matter is that most of them stack.** `CyberneticsOneOnly` is the only gate on
> duplicate implants and it is per-blueprint; vanilla tags 17 items with it and the platings and
> insulations are not among them. `Slots="Body,Head,Back"` is three distinct body parts, and
> `ImplantedEvent` adds the stat once per implant with no cap — so three high-grade insulations were
> **+60 to each of the four elemental resistances**. Resistance applies as `(100 - resistance) / 100`,
> so a Full Psionic caster's +40 on top of that reached **exactly 100**, which multiplies those paths
> to zero. Vanilla's ceiling by the same route is 42. It is now 47.
>
> `DermalInsulation` and `HighGradeDermalInsulation` no longer appear in `mod/` at all: once their
> numbers are vanilla's, the merge changes nothing by definition, and deleting it is cleaner than
> restating it.

> ⚪ **The plating line is priced on vanilla's own rate (#418).** Restoring carbide to 3 points for
> +1 AV in #335 was right on its own and left it **dominated by two of this fork's rungs** — steel
> gave the same +1 AV for a third of the licence cost, and crysteel gave twice the AV for the same
> 3 points. Vanilla ships exactly one plating, so there is exactly one data point for what AV costs:
> **3 licence points each**. The fork's rungs now sit on that rate.
>
> | plating | source | licence | water | AV | across 3 slots |
> |---|---|---:|---:|---:|---:|
> | steel | fork | 1 | 60 | +1 | **+1** — Body only |
> | carbide | vanilla | 3 | 180 | +1 | +3 |
> | crysteel | fork | 6 | 360 | +2 | +6 |
> | zetachrome | fork | 9 | 800 | +3 | +9 |
>
> **So the fork's platings buy slot density rather than power.** One zetachrome is +3 AV for 9 points
> in one slot; three carbides are +3 AV for 9 points in three. You pay vanilla's price for the armour
> and buy back two slots for insulations, and that is the whole reason to want the expensive one.
>
> Steel keeps its cheap entry price but is **Body only**, so it cannot ladder to +3 the way it could
> when it undercut carbide in every slot. `Slots` governs installation rather than what is already
> installed, so a save with steel plating in a Head or Back slot keeps it.
>
> Crysteel moved from `Implants_3Pointers` to `Implants_4PlusPointers` to match — those table names
> are literal about licence cost, and `implant-table-cost` in `tools/validate_mod.py` now holds that.

### 6.6 Other equipment

#### Energy cells — new

| Blueprint | Tier | Max charge | Recharge | Weight | Value | Drop weight | Tinker bits |
|---|---|---|---|---|---|---|---|
| **Advanced chem cell** | 5 | 50,000 | — | 1 | 300 | 10 | `0014` |
| **Dark matter cell** | 8 | **500,000** | — | 70 | 1200 | 1 | `0047` |
| **Solar cell array** | 4 | 10,000 | 10/turn in sunlight | 1 | 150 | 5 | `0023` |
| **Solar cell nexus** | 7 | 50,000 | 10/turn in sunlight | 1 | 225 | 1 | `0025` |

For reference, the mod's own notes record the vanilla baseline: chem cell 10,000 (T1);
fidget 2,500 (T1, 2/20 per turn out of/in combat); solar 2,500 (T2, 10/turn); nuclear 100,000 (T7);
antimatter 200,000 (T8); and the liquid-fuelled cells — lead-acid 4,000 (500/dram), combustion
6,000 (750/dram), thermoelectric 40,000 (5,000/dram), biodynamic 60,000 (7,500/dram).

So the solar array is 4× the capacity of a basic solar cell and the nexus 20×, at vanilla's own
recharge rate. The advanced chem cell is 5× a chem cell and half a nuclear cell. The dark matter cell
matches the **mech power core**, which is the only other 500,000 cell in the game.

> ⚪ **Three of those figures moved in #326 and #323**, and the reasons are worth keeping.
>
> **Recharge was 25 and 50 per turn.** Vanilla ships exactly one solar cell and its rate is **10**, so
> 25 and 50 were invented. The nexus at 50 mattered more than it looks: a psionic pistol costs 50
> charge a shot, so the nexus paid for **one shot per turn, indefinitely**, outdoors in daylight.
> Vanilla's own ratio is a laser pistol at 100 a shot against a solar cell making 10 — **ten turns of
> sun per shot**. Both fork cells are now 10 as well, which leaves capacity as the thing that
> separates them, exactly as it separates every vanilla cell.
>
> **The dark matter cell weighed a pound.** Vanilla's portable ceiling is the antimatter cell at
> 200,000; the only 500,000 cell it ships is the mech power core, at **70 lb**. Keeping the capacity
> and taking the weight is the honest version of that trade — it is a power source you install
> somewhere, not one you pocket.
>
> **And the drop weights were inverted.** See below.

#### Energy cells — rarity

Vanilla's rule is visible once entry tier is read against capacity: **more charge, rarer, and later**.

| cell | charge | enters | drop weight |
|---|---:|---|---:|
| Chem (vanilla) | 10,000 | Ammo 4 | 25 |
| **Advanced chem** | 50,000 | Ammo 5 | **10** |
| Nuclear (vanilla) | 100,000 | Ammo 6 | 5 |
| Antimatter (vanilla) | 200,000 | Ammo 7 | 1 |

and the recharging cells run their own ladder alongside it:

| cell | charge | enters | drop weight |
|---|---:|---|---:|
| Solar (vanilla) | 2,500 | Ammo 4 | 10 |
| **Solar array** | 10,000 | Ammo 4 | **5** |
| **Solar nexus** | 50,000 | Ammo 7 | **1** |

Both ladders are monotone: nothing with more charge is commoner than something with less. They were
not, before #326 — the advanced chem cell sat at weight **20**, four times commoner than the nuclear
cell at twice its capacity and twenty times commoner than antimatter.

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
| **Cybernetics credit pass** | — | `CyberneticsCreditWedge` worth **3 credits** | 450 |
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

### 6.7 Ammo — arrows, shells and one slug live, bullets cut

`ObjectBlueprints/Ammo.xml` was 524 lines with **every one of its 62 objects inside a single XML
comment** marked only *"removed temporarily"*. Mura pulled the file when a Qud change broke the
effects and the ammo degraded to plain ammo. #144 revived the arrows and #145 the shells. #146 was
the largest reachability claim of the three — 12 vanilla weapons plus 7 relic bases consume slugs —
and it resolved by **cutting all 20 bullet objects** and adding one new round in their place, the
scour slug. Those 20 stay commented as a record of what was tried, with `Raven_Quill Arrow` and its
projectile. See *The scour slug* below for the measurement that decided it.

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

The **part** is melee-only; the **mechanic** is not. `BleedingOnHit` sits on exactly two vanilla
objects, `Lamprey Bite` and `Sharpened Polyp` — and only the first is a natural weapon, the second
being a wieldable `LongBlades` item. Bleeding itself reaches much further:
`XRL.World.Parts.Skill.ShortBlades`, the tree's *root* class, bleeds on every critical hit with no
power purchased, and `Rifle_WoundingFire` applies `Bleeding` at range from `MissileWeapon.cs`. This
section previously said the opposite; corrected in #219.

So #201 changed the payload because `BleedingOnHit` cannot fire from a projectile — which remains
true — not because Qud declines to bleed things at range. Whether the mod should own a
bleeding-at-range part is #210, and charter rule 2's question there is not whether to invent a
mechanic but whether ammunition should deliver one that vanilla gates behind 250 skill points and a
marking turn.

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
| incendiary, cryo, flechette | `001` | **4** | 4 | **Tinker 2** |
| takedown | `001` | — | 1 | Tinker 1 |

All four cost two scrap metal and one phasic power systems for three shells — **exactly what vanilla
charges for a gas, flashbang, thermal, freeze or high explosive grenade mk III**, which are the
payloads these shells carry dialled down. The material bracket matches the thing being imitated.

They cost `003` until #146, a **pure alloy**: a level-3 bit vanilla reserves for its exotic grenades
— plasma, gravity, time dilation — and never asks for on a payload of this kind. The rarity was
doing gating work `BuildTier` already does, and it read as a tax on the line rather than a decision
about any shell.

`BuildTier` is a real public field on `TinkerItem` that vanilla never writes; using it keeps the
materials cheap while putting burning, freezing and armour-defeating behind the second skill. The
less-lethal round is the one anybody who can build the gun can also load. Since the bits no longer
reach tier 3 on their own, the gate is now entirely `BuildTier`'s. The wider inconsistency in
vanilla's own recipe tiers is #202.

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

#### The scour slug

Mura's ten effect bullets are **cut**, decided in #146. Six had already been cut from the arrows and
the shells for reasons that did not change, and the razor bullet — the one worth arguing about —
failed the test this whole line is built on. **813 of 904 creature blueprints bleed**, robots
included, so it had no dead matchup: a straight upgrade over a plain slug rather than a trade.

What replaced it is one round, `Vixy_Scour Slug`, carrying `RustOnHit` at `Chance="5"`.

| | |
|---|---|
| What it does | takes **one random item** from the target's equipment or inventory and applies `Rusted` |
| Dead to | creatures carrying nothing — `GetRandomItemFrom` returns `null`, silently |
| Dead to | creatures whose gear is all **natural** — see below, and this is the big one |
| Dead to | anything carrying only non-metal — `Rusted.Apply` opens on `!HasPart<Metal>` |
| Costs you | `Rusted` drops an item to **1%** of its value, and a second one destroys it outright |

**This is a narrow round, and that is the trade it is priced on.** 728 of 904 creature blueprints
are dead to `RustOnHit` — but that number alone describes a round that does nothing, and the useful
half is the other one: **134 of 340 humanoid creature blueprints have a rustable item**, against
202 that do not. It is a round for the armed and the armoured and dead weight against beasts, and
those are the two figures that say so. Both are recomputed from the game by
`tools/snapshot_qud_api.py`, so neither can quietly stop being true.

Worth knowing that it is narrower still in play than in the bestiary. Restricting the count to
creatures a vanilla population table can actually spawn moves the rustable share from 18.8% to
17.4%, and weighting by how many table entries name each one takes it to 13.6%. And a blueprint
census is a *floor* in the other direction — a creature arms itself from what is lying around, so
what a blueprint declares is the least it can be carrying.

##### Natural gear is invisible to it

The largest dead category is not creatures carrying nothing. It is **351 of 904 creature blueprints
carry only natural gear**, and they are immune however armed they look — a temple mecha holding a
`MachinedEdge` that *has* `<part Name="Metal" />` cannot be rusted at all.

`NaturalWeapon` sets `<intproperty Name="Natural" Value="1">`. `BodyPart.DoEquip` opens with
`GameObject.EquipAsDefaultBehavior()`, which is true for anything `IsNatural()`, and that branch
assigns `bodyPart.DefaultBehavior` rather than `bodyPart._Equipped`. `GetEquippedObjects` collects
`Equipped` only. So the pool `GetRandomItemFrom` draws from is empty, it returns `null`, and
`?.ApplyEffect` does nothing without a message. Armour is unaffected — `EquipAsDefaultBehavior`
refuses anything with an `Armor` part — so armoured creatures stay rustable.

It fills a real gap: **Bow and Rifle is the only tree with status-inflicting shots** — Wounding,
Suppressive, Flattening, Sure, Beacon, Disorienting and Ultra Fire — while Pistol (30 weapons) and
Heavy Weapon (16, including the Chaingun and Linear Cannon) have none. Slugs are eaten across all
three, so ammunition is the only vehicle that reaches the two empty ones.

**It does not need to penetrate.** `MissileWeapon` raises `ProjectileHit` inside the
failed-to-penetrate branch as well, with `Penetrations` 0, and `RustOnHit` checks penetration
nowhere — so this answers a target you cannot hurt. Deliberate, and the reason the chance is a third
of vanilla's default.

**Rust is repairable**, at a premium: `Tinkering_Repair` branches to `RustedRepairCost`, forcing the
item's highest bit and including 75% of the rest against 50% for ordinary repair. So the round is an
expensive setback rather than annihilation — except on an artifact, where `IActivePart.IsRustSensitive`
defaults true and `IsReady` returns `ActivePartStatus.Rusted`, so a rusted laser rifle simply stops
firing.

#### Getting a payload past a weapon that hardcodes its projectile

The mechanism that made the slug possible at all, and the reason #145's fix could not be reused.

All 19 slug consumers — 12 weapons, 7 relic bases — name their projectile on `MagazineAmmoLoader`,
which only consults the round's own `ProjectileObject` when that field is blank. That is why every
effect bullet Mura wrote was loaded, fired, and had its payload discarded.

For shotguns, blanking the field was free: both pellet projectiles are 1d2/pen 4, identical to
`ProjectileShotgunShell`. For slugs that field is **where the weapon's ballistics live** — 1d6/pen 3
for the Borderlands Revolver, 1d8/pen 7 for the Sniper Rifle, 2d12 `Vorpal` for the Linear Cannon —
and blanking all 19 would flatten every one to `ProjectileLeadSlug`'s 1d6/pen 3.

So `Vixy_AmmoPayload` merges the round's payload **into** the weapon's projectile instead. One part,
merged onto `BaseFirearm`, which reaches all 19 plus both Masterwork variants and any firearm a
future Qud release adds — one vanilla name on the compatibility surface rather than nineteen, adding
a part and replacing no attribute.

It needs two events, because one is not available:

| Event | Order | Why |
|---|---|---|
| `LoadAmmoEvent` | **before** `MagazineAmmoLoader` | reads `loader.Ammo`, the stack about to be drawn from, while `RemoveOne()` has not yet run |
| `ProjectileSetup` | after the projectile exists | fired by `MissileWeapon.SetupProjectile` once per projectile — a separate dispatch, so part order stops mattering |

Running *after* the loader in one dispatch is not purchasable at any price: `ObjectBlueprintLoader.Bake`
inherits a parent's parts before the object's own, and `AddPartInternals` orders `PartsList` by
`IPart.Priority`, which can only move a part **earlier**. Running early is what makes the read valid.

---

## 7. Population / loot tables (`PopulationTables.xml`)

101 table definitions: **77 merged** into vanilla, **24 declared fresh**. The 48/28 split this
line used to give was from before #34 converted `Artifact 3`–`8` from replacements to merges; §0
was corrected in #95 and this line was missed. `Ammo 2` and `Ammo 3` were added in #144 to give
the effect arrows a drop route alongside the cells already merged into `Ammo 4`–`8`.

### 7.1 Starting gear (18 new tables)

One `Vixy_StartingGear_*` table per Psionic Adept subtype. Common pattern:

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
tonic, one themed single chip, a **basic neutral mind chipset**, a **basic precognition chip**,
1d3 injectors, 1d3 cells. Three Guardians break the armor-set pattern entirely.

> The chipset used to be **neutral body**, and the third chip **mental mirror**. Both changed in
> #338. Neutral body carries `HeightenedSpeed`, which is one of the four steep permanent passives —
> so every one of the nine Guardians opened the game at +15 Quickness from a *generic* chipset that
> is nobody's affinity. `docs/DESIGN_balance.md` §5.9 states the rule it broke: **a subtype starts
> with its own affinity, not a generic chipset carrying someone else's steep passive.** Neutral mind
> is reflect-block-displace, which is closer to what a Guardian is anyway.
>
> Mental mirror moved to precognition for a second reason: the neutral mind chipset already grants
> `MentalMirror`, and **duplicate chips stack** (#350), which should not be baked into starting
> gear. Still three chips and five mutations, with no duplicate and no steep passive.
>
> The affinity cases stay. A Light Psionic opening with `PhotosyntheticSkin` is its affinity
> expressing itself, and so is the Light Guardian's own affinity chip.

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
  **Eight new melee blueprints appear in no table at all:** the vibro weapons
  (battle axe, greataxe, vinereaper, halberd, greatsword, rapier, katana, wristblade) — all
  tinkerable, so still reachable.
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
- **Missile 4** — compact flamethrower (10), cryocannon (10), net gun (5), fine-tuned handgun (2), modified handcannon (5), drum shotgun (5).
- **Ammo 4–8** — solar cell array from tier 4; advanced chem cell from tier 5; solar cell nexus from tier 7; dark matter cell via a nested chance table at tier 8.
- **Implants_1and2Pointers** — steel dermal plating, omni pass, steel hand bones.
- **Implants_3Pointers** — air filtration system.
- **Implants_4PlusPointers** — crysteel hand bones, crysteel dermal plating, zetachrome dermal
  plating, zetachrome hand bones.

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
- Two tier-8 items are pulled *below* curve: Cudgel8 and Cudgel8th, both 1200. The zetachrome greataxe and wristblade were also 1200 until #86 put them on the curve at 1280.
- Vibro weapons are flat 300 across the board.
- Laser pistol 250, laser rifle 550, chain pistol 100, borderlands revolver 25.
- All grenades carry vanilla's own prices again (#334). They had been flattened to 10/20/30, which
  erased vanilla's three ladders: 20/30/40 for the common lines, 20/20/20 for the four that do not
  scale by grade, and 30/40/50 for fire support and time dilation.

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
| 3 | ✅ Fixed | **All of `Ammo.xml` (62 objects) was commented out** — "removed temporarily". Mura pulled it when a Qud change broke the effects and the ammo degraded to plain ammo. All three families have now been through: six effect **arrows** revived in #144, four effect **shells** in #145, and one **slug** — the scour slug — designed and shipped in #146. #145 also established *why* the shells were dead: every shell-firing weapon hardcoded its pellet, so the ammunition's projectile was discarded, fixed by deferring the weapon to its ammo as vanilla's own grenade launcher does. The rest were **cut rather than revived**, on measurement rather than neglect — #146 worked out what rate of fire does to area and status effects and cut all ten bullets, keeping one slug with a payload that survives being fired in volume. The 22 objects those decisions covered — the ten bullets with their projectiles, and `Raven_Quill Arrow` with its — stay commented in the file as a record of what was tried, per the note above this table. 23 objects are live. | `ObjectBlueprints/Ammo.xml` |
| 4 | ✅ Fixed | **Mutant HP gain was `2-3`** in XML against `1-5` in every one of Mura's writeups. `2-3` has vanilla's own 2.5 average, so the mod's headline HP change did nothing to the mean, and it left mutants strictly dominated by True Kin's 2-4. Corrected to `1-5` in #90, with a Combo option offering `2-3` and vanilla's `1-4`. | `Genotypes.xml` |
| 5 | ✅ Fixed | **`Flawless Crysteel Boots` was tagged Tier 3** by the mod's merge, overriding vanilla's 7. Override removed (#9). (should be 7) — wrong loot pool and mod capacity | `ObjectBlueprints/Armor.xml` |
| 6 | ✅ Fixed | **`<stag>` changed to `<tag>` twice, and it should not have been** — the advanced hoversled's `Floating` and the sphere of negative weight's `Trinket`. #50 (#10) made the change on the reading that `<stag>` is not an element Qud reads. It is: `XRL.World.GameObjectFactory` loads `tag` and `stag` into the same dictionary and **prefixes the second**, so `<stag Name="Floating" />` produces the tag `SemanticFloating`. Vanilla writes both of these names as `<stag>` and nothing else, so #50 made these two the only objects in the game carrying the unprefixed names. **Reverted in #478**; both read `<stag>` again, at `OtherEquipment.xml:141` and `:278`, and `curve_exempt` learned both forms in the same change — it recognised a trinket only by `<tag>`, so correcting the blueprint alone would have silently repriced the sphere at 100 against a curve of 1280. `tag-form` in `tools/validate_mod.py` now compares every tag against vanilla's usage of that name, and `docs/STYLEGUIDE.md` §4.0b carries the mechanism. This row sat at 🟠 Med for the whole time it was "fixed", which is what #291 is about. | `ObjectBlueprints/OtherEquipment.xml` lines 140, 277 |
| 7 | ✅ Fixed | **Akimbo reused `Class="Pistol_Akimbo"`** across the Pistol and Multiweapon trees. `SkillFactory.PowersByClass` holds one entry per class and vanilla grants powers by class — the Gunslinger calling is `<skill Name="Pistol_Akimbo" />` — so the mod's entry was served in place of vanilla's. Removed from Multiweapon Fighting in #11 after a distinct class proved to duplicate the ability and lock the skills screen. | `Skills.xml` |
| 8 | ✅ Fixed | **`Cudgel6th` had `MaxStrengthBonus="11"`** where every tier-6 peer uses 7 | `ObjectBlueprints/MeleeWeapons.xml` |
| 9 | ✅ Fixed | **`Raven_Carbideweave Cloak` was valued at 5** instead of 40 | `ObjectBlueprints/Armor.xml` |
| 10 | ✅ Fixed | **Dark matter cell (500k charge) priced same as advanced chem cell (50k)** — both 300 | `ObjectBlueprints/OtherEquipment.xml` |
| 11 | ✅ Fixed | **Psionic pistols listed `RifleMods`, not `PistolMods`** (the pistol base inherits `BaseRifle`) | `ObjectBlueprints/RangedWeapons.xml` |
| 12 | ✅ Fixed | **Psionic Adept chargen text said "+30 bonus skill points"** — a bonus the genotype did not grant, against an actual delta of +25 on vanilla's True Kin and +10 on this fork's. Corrected in #276 (#275): the panel now reads `{{C|95}} skill points each level`, the absolute figure `BaseSPGain="95"` gives, which cannot drift out of step with a comparison the way a delta can. | `Genotypes.xml` |
| 13 | 🟡 Low | **Four vibro weapons commented out** with "rework these or remove them" (vibro mace, two-handed vibro mace/flail, vibro war hammer, two-handed vibro war hammer/greathammer) | `ObjectBlueprints/MeleeWeapons.xml` |
| 13b | ✅ Fixed | **`Raven_ProjectileFireRifle` used `Attributes="Heat"`** while its pistol counterpart uses `"Heat Fire"` — the rifle likely won't set things alight | `ObjectBlueprints/RangedWeapons.xml` |
| 14 | ✅ Fixed | Subtype sprite files used the prefix `corrosion*` while the subtype is named "Corrosive". Renamed to `corrosive*` in this fork (#24), and `tools/validate_mod.py` now checks every subtype tile against its affinity. | `Textures/Subtypes/` |
| 15 | ✅ Fixed | The `Yttrian` anatomy/body-object name survived the genotype's rename to "Psionic Adept". Renamed to `PsionicAdept` in this fork (#13). | `Bodies.xml`, `Genotypes.xml` |
| 16 | ⚪ Note | The Chip Interface is merged into the base `Humanoid` anatomy, so **every humanoid NPC in the game gains a chip slot**. Currently nothing equips chips to NPCs, but any mod or future change that populates that slot would affect the whole world. The player-side half of that blast radius is settled: vanilla's Mutated Human shares the anatomy, so the merge gave the mutant player a slot as a side-effect, and #353 takes it back off at chargen (§3.1). | `Bodies.xml` |

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
├── manifest.json               # id, version, author, and the Directories array below
├── workshop.json               # Steam metadata + description
├── preview.png
│
├── Core/                       # always loaded
│   ├── Mods.xml                # makes Gigantic tinkerable
│   ├── Genotypes.xml           # Mutant + True Kin merges, Psionic Adept (new)
│   ├── Subtypes.xml            # 18 affinities in 2 categories
│   ├── Skills.xml              # 7 tree edits
│   ├── Bodies.xml              # Chip Interface part; TrueKin + PsionicAdept anatomies
│   ├── Options.xml             # 18 options (§13)
│   ├── Naming.xml              # widened Qudish pools + 2 new namestyles (§15)
│   ├── EmbarkModules.xml       # declares the name-flavour chargen module (§15.4)
│   ├── Genders.xml             # 8 new genders + 1 unhidden (§16)
│   └── PopulationTables.xml    # 101 tables (77 merge / 24 new)
│
├── Optional/
│   └── JoppaBuilding/          # loaded only while its option is Yes
│       └── Joppa.rpm           # 76-cell amenity building
│
├── ObjectBlueprints/
│   ├── MeleeWeapons.xml        # 101 new / 77 merged
│   ├── Armor.xml               # 61 new / 38 merged
│   ├── RangedWeapons.xml       # 49 new / 11 merged
│   ├── PsionicChips.xml        # 145 new (1 base + 144 chips)
│   ├── Cybernetics.xml         # 9 new / 14 merged
│   ├── OtherEquipment.xml      # 7 new / 16 merged
│   ├── Throwables.xml          # 51 merged (prices only)
│   ├── Ammo.xml                # 20 new + 1 merge; 20 bullets still disabled
│   ├── Furniture.xml           # 4 new
│   ├── Creatures.xml           # 2 new bodies + 1 merge
│   └── Food.xml                # 2 merges
├── Scripting/                  # 50 classes: 36 mutation stubs, plus options,
│                               # the chip-slot mutator, burden, the save-format
│                               # guard, and four Finesse powers
└── Textures/Subtypes/          # 18 sprites by Noble Lark

manifest.json's `Directories` array names the four always-loaded paths and gates
Optional/JoppaBuilding on its option. It must never name mod/ itself: the loader keeps
only one of two overlapping entries, so a root entry would load the gated directory
unconditionally. `directory-coverage` enforces that, and that every file here is
reachable from exactly one declared path.

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

Eighteen options, all under **Category="Mods"** in Qud's own options menu. Declaring one is pure XML;
reading one requires C# — `mod/Scripting/Raven_Options.cs` holds all of them except the Joppa
building, which `Raven_JoppaBuildingSystem` reads because the building is map data rather than a
field on a loaded record.

Per charter rule 6, **defaults reproduce the mod's established behaviour**. Two exceptions: the
starting reputation bonus, which grants power with no content attached and so must be asked for
rather than opted out of; and graded burden, which is a genuinely new opinion this fork introduces
rather than anything the mod already was.

> ✅ **Verified in game by the maintainer: eleven options on 2026-08-16, graded burden on
> 2026-08-23.** ⚠️ **The Chip Interface option is due a re-check**: #353 narrowed it to True Kin
> only, so the 2026-08-16 pass no longer covers what it does. Still the only evidence
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
| eased skill requirements | Checkbox | **Yes** | The fifteen retuned attribute requirements in §4. |
| retuned skill point costs | Checkbox | **Yes** | The four retuned prices in §4. |
| starting reputation bonus | Checkbox | **No** | +300 Joppa for mutants. §1.2. |
| psionic chips in loot | Checkbox | **Yes** | The six `Raven_Chips Tier N` references in Artifact 3–8. §7.3. |
| home base building in Joppa | Checkbox | **Yes** | The map patch in §8. |
| graded burden | Checkbox | **No** | Four load bands under vanilla's carry cliff. §14. |
| True Kin Chip Interface slots | Checkbox | **Yes** | A True Kin's 2 slots. A Mutated Human has none either way (#353); the Adept's 4 are the genotype. §3.1. |
| Chip Interface slots on other humanoids | Checkbox | **Yes** | The `Humanoid` anatomy merge, which reaches every humanoid NPC. §3.1. Nothing in this mod ever *places* a chip in one — but a player can, by handing a chip to a follower. See the callout below (#417). |
| wider name pools | Checkbox | **Yes** | The syllables added to Qudish. Off restores vanilla's 29/20/24 exactly. §15.1. |
| gendered name endings | Checkbox | **Yes** | Whether a generated name reflects the gender the game already rolled. Off makes naming gender-blind, as vanilla is. §15.2. |
| how your own random name sounds | Combo | **Random** | Which pool the player's own generated name is drawn from. §15.4. |
| choose your gender at character creation | Checkbox | **Yes** | `Gender.EnableSelection`. Adds the Gender row, offering 13. §16. |
| choose your pronouns at character creation | Checkbox | **Yes** | `PronounSet.EnableSelection`. Adds the Pronoun Set row, offering 14. §16. |

The Psionic Adept is deliberately outside every one of these. Its skills, reputation, four chip
slots and 95 skill points are the genotype rather than additions to a vanilla one, so there is no
vanilla value to restore and turning them off would leave a genotype with nothing.

> ⚠️ **An NPC's chip slot is reachable, and the documentation used to say it was not (#417).**
> **Confirmed in game**: a humanoid follower equipped a chip unprompted, gained the mutation, and
> killed a snapjaw with it. What follows was a code reading first and is now a result — see §3.5. This
> row read *"nothing here ever fills those slots, so the reason to turn it off is to stop another mod
> — or a later version of this one — being able to."* The first clause is true of the **mod**: no
> creature is generated carrying a chip, and chips reach the world only through the artifact tables
> that fill containers. The conclusion drawn from it is not, because a player is not another mod.
>
> **Chips are worn armour, not implants.** `Raven_Base Psionic Chip` inherits `BaseArmor` and sits in
> the slot with `WornOn="Chip Interface"`, which puts it on the ordinary AI equip path. Every gate on
> that path was traced:
>
> | step | result |
> |---|---|
> | `Body.GetParts()` | returns every part with no filter, so the abstract slot is enumerated |
> | `Armor.HandleEvent(QueryEquippableListEvent)` | adds the chip whenever `WornOn` matches the queried slot, and **never reads `RequireDesirable`** — 0 AV / 0 DV does not disqualify it |
> | `NoAIEquip`, `CannotEquip`, `NoEquip`, `Food`, `Shield` | none of the 144 chips carries any of them |
> | `Brain.CompareGear(chip, null)` | returns `-1` for an empty slot, so `IsNewGearBetter` is true |
> | the grant | fires on `EquippedEvent` and targets `E.Actor` — whoever wore it, not whoever is the player |
>
> The `_stock` guard in `PerformEquip` keeps merchants from wearing their own inventory, so this
> needs a player to choose it: hand a chip to a humanoid follower.
>
> **This is a code reading, not a result.** Every step is accounted for and none of them blocks, but
> nobody has watched a follower do it. #417 holds the in-game test. If it works, the mod has a
> capability no document describes; if it does not, whatever stops it belongs in `docs/LESSONS.md`,
> because the trace above says it should.

### 13.2 When an option takes effect — three scopes

This is the distinction that decides how an option must be written and what its `<helptext>` has to
warn about. The charter's guidance to *prefer designs whose off-switch is a runtime decision* is
about moving features up this table.

| Scope | Options | Why |
|---|---|---|
| **Live** — applies immediately | graded burden, chips in loot, retuned skill point costs, and — from your next level — hit points and skill points per level | Burden derives its band from carried weight every turn and stores nothing. Population tables stay mutable after load, `Cost` is a plain int with no cache, and `Leveler` re-reads `BaseHPGain`/`BaseSPGain` at every level-up. |
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

## 14. Graded burden (`Vixy_Burden`)

**Off by default** — a genuinely new opinion this fork introduces, which is what charter rule 6
reserves that default for.

Vanilla has one weight threshold and nothing underneath it. Carry capacity is `15 × Strength`;
exceed it and `Overburdened` applies, which makes you unable to move at all. Below it, nothing
happens. So the optimal play is to sit at 99% of capacity forever and never think about weight
again — a threshold that produces no decision.

Four bands fill that space:

| band | load | effect |
| ------------------- | ------: | -------------------------------------------- |
| unburdened | < 50% | none |
| lightly burdened | 50–75% | −1 DV |
| encumbered | 75–90% | −2 DV, −1 Quickness per 10% above 75 |
| heavily burdened | 90–100% | −4 DV, −10 Quickness, cannot run |
| *(vanilla)* | > 100% | `Overburdened` — unable to move, untouched |

**Vanilla's cliff is deliberately left where it is.** Moving it to 125%, as the original spec
proposed, is only possible by intercepting `GetMaxCarriedWeightEvent` — and that figure is read by
seven UI surfaces and by the **Pack Rat** mutation, which forces a character to stay above 90% of
whatever capacity reports. Inflating it would pin a Pack Rat permanently in the worst band. Leaving
the cliff alone costs one band and has no blast radius at all.

**Player only**, matching vanilla exactly: `GameObject.IsOverburdened()` opens with
`if (!IsPlayerControlled()) return false;`, so no NPC is ever burdened at any load.

**Safe to toggle mid-run.** The band is derived from carried weight on every turn and the effect
stores nothing, so the option takes hold on the next tick and adds nothing to the save.

> ✅ **Played and confirmed on 2026-08-23** (maintainer). All five behaviours the pull request left
> open: the band appears by name at each threshold, DV and Quickness move, running is refused in the
> heavy band, the option takes hold on the next turn in both directions, and — the case with no
> compile-time proof — **an existing save picks the part up on load**, not just a fresh character.
> That last one is the whole reason `Vixy_BurdenAttach` carries two hooks rather than one.

### 14.1 Two spec items that could not be built

Neither is a shortcut; Qud has nowhere to put them.

- **A stealth penalty.** There is no stealth system in Caves of Qud — the word does not appear
  anywhere in the game assembly.
- **"Movement costs double."** There is no movement-cost hook. Movement is charged at fixed energy
  and Quickness governs how fast it is earned back, so this would have to be spent through
  Quickness — which is the penalty the band already applies. Listing both would double-count one
  mechanism.

A third, a fatigue rider on the heavy band, waits on the sleep work in
[#179](https://github.com/vixygrey/qud-expanded-community-edition/issues/179).

### 14.2 One implementation note worth keeping

The heavy band's run block vetoes the **`ApplyRunning`** event, not
`CanChangeMovementModeEvent`. Refusing the latter is how vanilla's own `Overburdened` blocks
flight, so it looks like the obvious model — but that event's `To` carries the movement *message
name*, which is `"sprinting"` by default and configurable per `Run` part. Matching on `"Running"`
would never fire, and the restriction would have shipped silently inert.

---

## 15. Name pools (`Naming.xml`)

Procedurally generated humans stopped sounding alike, and the half of them who are women stopped
sounding like men.

### 15.1 What a player was actually noticing

Vanilla's Qudish namestyle has **29 prefixes, 20 infixes and 24 postfixes**, drawn as prefix=1,
infix=0–2, postfix=1 — about **93,500 distinct names**. So exact repeats are *not* what anyone was
seeing: roughly 0.2% across 20 rolls.

**Repeated syllables are.** There is a 50% chance of a repeated *opening* after 6.3 draws. That
inverts the obvious fix: widen prefixes and postfixes, and leave the infix pool alone, because the
infix is not where the collision is.

| pool | vanilla | now | 50% repeat at | expected repeats in 20 names |
| ---------- | ------: | --: | ------------: | ---------------------------: |
| prefixes | 29 | 68 | 7 → 11 draws | 6.6 → 2.8 |
| infixes | 20 | 28 | *unchanged by design* | — |
| postfixes | 24 | 36 | 7 → 11 draws | 7.9 → 2.6 |

Widening halves perceived repetition. It cannot do much better than that: the effect scales with the
square root of the pool, so reaching "you would never notice" needs roughly ten times the syllables.

### 15.2 The ending carries the gendered read

Qud's name generation is very nearly gender-blind — exactly **one** namestyle in the whole vanilla
file uses a `Gender` attribute, and it is a Warden honorific. What reads as male-coded is a phonetic
property of the postfix pool: **23 of vanilla's 24 endings are hard stops** (`-q -t -m -r -s`), with
`la` the only open, vowel-final one.

That matters more than it sounds, because the game already knows each character's gender.
**117 of the 126 blueprints that resolve to Qudish inherit `RandomGender="male,female"` from
`BaseHuman`** — a coin flip rolled at creation, before the name is generated, and passed to the
generator. So half of every generated human in Qud already *was* female, drawing from a pool of hard
stops.

Two namestyles use it:

| namestyle | scoped to | ending pool |
| ------------------------ | ---------------------------------------- | ------------------------------------ |
| `Vixy_Qudish Feminine` | `Species="human"`, `Gender="female"` | 36 open + 5 hard |
| `Vixy_Qudish Neutral` | `Species="human"`, the non-binary genders | 18 open + 18 hard |

The hard endings in the feminine pool are deliberate. It is a lean, not a rule — about one draw in
five takes one, so a name never states the gender outright.

`Vixy_Qudish Neutral` carries one scope per gender, because `NameScope.Gender` is a single
exact-match string rather than a list: `neuterperson`, `nonspecific`, and `elverson`. The last is
inert today — vanilla hides that gender behind `Generic="false"` — and inert is the right state for
it until something makes the gender reachable.

**`hartind` is deliberately absent.** Its person terms are `hartind` / `faun`, which makes it the
hindren third gender rather than a general one, and hindren have their own namestyle.

### 15.3 Three attributes doing more work than they look like

- **`Load="Merge"` sits once on `<naming>`** and cascades — `LoadNamingNode` reads it and every level
  below inherits it. Without it, `LoadNameStyleNode` removes the namestyle from `_NameStyleList`,
  builds a replacement and **never adds it back to the list**, which `Generate` iterates. Qudish
  would leave name generation entirely and every procedurally named human would be called
  `NameGenFail1`, `NameGenFail2`, and so on.
- **`Species="human"`** bounds both new namestyles. A scope carrying only `Gender` matches every
  female creature in the game, and female bears would draw Qudish names.
- **`Priority="50"`** is under a hard ceiling of 100. Exclusion is `other.priority > scope.priority`,
  and the faction namestyles that must keep winning — Templar, Barathrumite, Mechanimist, Snapjaw —
  sit at exactly 100 with `Combine="false"`. At 100 these would displace them.

All three are held by `tools/validate_mod.py`, and `tools/naming_harness.py` resolves the whole file
against vanilla without launching the game.

### 15.4 The player's own name, which needed a different mechanism entirely

Everything above scopes on a creature's gender and species. **None of it can reach the player**, and
the reason is worth stating because it looks like an oversight and is not.

`XRLCore.GenerateRandomPlayerName` calls `NameMaker.MakeName(null, null, Type)`. `For` is **null** —
there is no GameObject, because the name is generated at `BOOTEVENT_GENERATERANDOMPLAYERNAME`, before
the player object is built. `NameStyles.Generate` only populates `Gender`, `Species` and `Tag` from a
live GameObject, so the player's random name is drawn gender-blind from `Qudish` however the
namestyles above are scoped. There is nothing to hang a `NamingTag` property on.

What there *is*, is the boot event itself. It fires through `EmbarkInfo.fireBootEvent` with the
default name as its element and takes back whatever the modules return. So
`mod/Scripting/Vixy_NameFlavourModule.cs` replaces it, reading a `Combo` option:

| choice | drawn from | resolves to |
| --- | --- | --- |
| `Random` *(default)* | all three pools, evenly | 33% / 33% / 33% |
| `Masc` | the widened Qudish pool | `Qudish` |
| `Femme` | the open, vowel-final endings | `Vixy_Qudish Feminine` |

There is no `Neutral` choice. It existed briefly and was cut: it drew from the mixed pool every
time, which for a single name is indistinguishable from `Random` drawing that pool one time in
three. Both mean *"I am not specifying"*, and offering two ways to say it is a wart rather than a
capability. `Random` still reaches the mixed pool, so nothing was lost — `Vixy_Qudish Neutral` keeps
its `Vixy_Random` scope and its gender scopes, which is how it serves non-binary NPCs.

`NameMaker.MakeName` takes `Tag` as an ordinary parameter, so reaching a tag-scoped namestyle needs
no GameObject — just the argument. `GameObject.Validate(ref null)` returns false, so `Generate` skips
the block that would overwrite `Tag` and the passed one survives.

**It is a module rather than an `EmbarkEvent` handler for one reason.** `fireBootEvent` iterates
`enabledModules` regardless of `game`, while `EmbarkEvent.Send` dispatches through
`Game?.HandleEvent` — and character creation's own *"roll me another name"* passes `game: null`. An
event handler would have changed the final name and not the one previewed while choosing it.

The `Tag` scopes sit at `Priority="200"` with `Combine="false"`, because an explicit choice should win
outright. `Vixy_Random` is the exception: `Priority="50"` and combining, carried at the same priority
by all three namestyles, so the weighted draw splits evenly. Random is the absence of a preference
rather than a fourth pool.

**The re-roll works, and it takes one line to explain why it nearly did not.** `EmbarkBuilder` fills
`EmbarkInfo._modules` with `embarkInfo.modules.AddRange(...)` at the very *end* of character
creation. Until then the list is empty — so the Name row's re-roll, which calls
`builder.info.fireBootEvent(...)`, consulted nobody and handed back a name drawn the old way. The
module therefore adds *itself* to that list in `Init()`. `EmbarkInfo.modules` is a public property,
so this is a public member rather than a patch, and if Freehold ever changes it the mod stops
compiling and `tools/compile_scripting.py` says so on the next Qud update.

The cost is that the module is in the list twice once `EmbarkBuilder` adds it too, so
`handleBootEvent` fires twice per boot event. Checked rather than assumed: build codes never see it
(`generateCode()` reads the *builder's* list, and `IncludeInBuildCodes()` returns `getData() != null`,
which is null here), `embarkInfo._data` gains nothing for the same reason, and both handlers are
idempotent.

Whichever name you were shown is the one you keep: the preview writes `data.name`, and
`BEFOREBOOTPLAYEROBJECT` restores it over anything the boot-time roll produced. Leave the row on
`<random>` and the boot-time roll is what you get, flavoured the same way.

**It follows the character afterwards.** Renaming yourself in game goes through
`GameObject.GiveProperName`, which calls `NameMaker.MakeName(this, …)` — a valid `For`, so `Generate`
reads `Gender`, `Species` and `Tag` off the object and an option is invisible to it. The module
therefore writes the chosen tag onto the player as a `NamingTag` property at
`AFTERBOOTPLAYEROBJECT`, and `Raven_Options` rewrites it whenever the option changes, so the property
matches the option's current value rather than being a one-way edit. Without that, character creation
followed the option and every rename afterwards followed your gender instead.

Typing a name in bypasses all of this, which is always the surest way to get the one you want.

### 15.5 What this does not touch

- **Hand-authored NPCs.** Mehmet, Argyve, Barathrum and about 60 others carry their name on the
  blueprint and never call the generator.
- **Non-human creatures.** Snapjaws, robots, animals, plants, reptiles, Templars and Mechanimists all
  have their own syllable pools, reached by their own scopes.
- **Village and site names.** `Qudish Site` is a separate namestyle with its own 23 prefixes, and
  scope matching gates on `Type` with exact equality, so a person-name scope can never be reached by
  a site call.
- **The player's own random name**, by any of the gender scoping above — see §15.4, which reaches
  it a different way.

## 16. Gender and pronouns (`Genders.xml`)

Qud has a complete gender and pronoun system and ships every part of it switched off. This turns it
on and widens it.

### 16.1 What vanilla already has, and cannot reach

`Genders.xml` and `PronounSets.xml` are both vanilla files. Between them they define **13 genders**
with full grammar tables — subjective, objective, possessive, substantive possessive, reflexive, plus
six person terms — a separate pronoun-set system, automatic replication of genders into pronoun sets,
procedural gender generation, and a selection UI rendered down to its screen coordinates and click
regions. **141 vanilla creature blueprints declare a `Gender` tag.**

All of it is unreachable. Both files carry `EnableSelection="false"` on their root element, and
`QudCustomizeCharacterModuleWindow.GetSelections()` yields the **Gender:** row only
`if (Gender.EnableSelection)` and the **Pronoun Set:** row only `if (PronounSet.EnableSelection)`.
Both false means neither row is emitted, so character creation offers Name / Pet / World Seed and the
handler that would run the choosers can never be reached. Absent a choice, the player is assigned
`Gender.GetAnyGenericPersonalSingular()` — a random draw from `male`, `female`, `neuterperson`,
`nonspecific`.

The same gate sits on the in-game customization screen, where *"buy a new **random** gender for 4
MP"* renders unconditionally but the line that lets you **choose** one does not.

### 16.2 Turning it on is C#, not XML, and that is deliberate

`Gender.EnableSelection` and `PronounSet.EnableSelection` are public static fields, set from the root
attribute of their XML files. A mod could ship a four-line `mod/Core/Genders.xml` with
`EnableSelection="true"` and it would work — the loader reads the attribute off whatever `<genders>`
root it is handed, base sorts before mods, and it is a plain static assignment, so last write wins.

**That version cannot be switched off.** XML loads unconditionally, and charter rule 6 wants this to
be the player's choice. So `Raven_Options.cs` sets the two fields from two options instead. That is
the only reason C# is involved.

**And setting them once is not enough.** `QudCustomizeCharacterModule.Init()` calls
`PronounSet.Reinit()`, which clears every pronoun set and re-reads `PronounSets.xml` — whose root
carries `EnableSelection="false"`. Character creation therefore undoes the pronoun half of this *as
it opens*. `Gender` has no equivalent `Reinit`, so it survives, and the symptom was one row
appearing and the other not.

`Vixy_NameFlavourModule.Init()` reapplies both afterwards. `EmbarkBuilder` calls `Init()` on every
module in load order and `DataFile.CompareTo` sorts base files before mod files unconditionally, so
a mod module's `Init` always runs after a base module's.

This was found by launching the game. The harness models how a name resolves, not the lifecycle of a
character-creation module, so nothing short of opening the screen would have caught it.

### 16.3 The gender row goes from four to thirteen

| | gender | pronouns |
| --- | --- | --- |
| *vanilla* | `male` | he / him / his / his / himself |
| *vanilla* | `female` | she / her / her / hers / herself |
| *vanilla* | `neuterperson` | it / it / its / its / itself |
| *vanilla* | `nonspecific` | they / them / their / theirs / themself |
| **unhidden** | `elverson` | ey / em / eir / eirs / emself |
| **promoted** | `xe` | xe / xem / xyr / xyrs / xemself |
| **promoted** | `ze` | ze / zir / zir / zirs / zirself |
| **promoted** | `sie` | sie / hir / hir / hirs / hirself |
| **new** | `fae` | fae / faer / faer / faers / faerself |
| **new** | `spivak` | e / em / eir / eirs / emself |
| **new** | `ve` | ve / ver / vis / vis / verself |
| **new** | `per` | per / per / pers / pers / perself |
| **new** | `ne` | ne / nem / nir / nirs / nemself |

**Unhidden** means vanilla already ships it, complete, behind `Generic="false"` — the one attribute
that keeps it out of `GetAllGenericPersonalSingular`. **Promoted** means vanilla ships it as a pronoun
*set* but not as a gender, so it appeared in one row and never the other.

Every addition uses vanilla's own person terms for a generic non-binary gender, taken from
`elverson`: `person / child / friend / child / sibling / parent`. The game already answered that
question, so this derives rather than invents.

The Pronoun Set row goes from **8 to 14**.

### 16.4 `hartind` stays hidden, on purpose

It is the other gender behind `Generic="false"`, and it stays there. Its person terms are `hartind` /
**`faun`**, which makes it the hindren third gender rather than a general one, and its pronouns
duplicate `nonspecific` exactly. Offering it would put a hindren cultural gender in a human's list
while changing nothing about the grammar.

### 16.5 The duplicate that `DoNotReplicateAsPronounSet` prevents

`ReplicateGenders="true"` mirrors every gender into a pronoun set — but a pronoun set is **named by
all eleven of its forms, person terms included**, and replication is skipped only when a set of that
exact name already exists.

Vanilla's hand-written `xe`, `ze` and `sie` sets carry the field defaults, `human / child / friend /
child / sib / progenitor`. The promoted genders carry elverson's. The names therefore differ, the
replica is **not** skipped, and each would appear twice in the Pronoun Set row — identical pronouns,
differing only in whether a stranger calls you `person` or `human`.

`DoNotReplicateAsPronounSet="true"` on the three promoted genders prevents it. The genders mode of
`tools/naming_harness.py` demonstrates both the duplicate and the fix.

One consequence worth knowing: the **gender** `xe` carries `person / sibling / parent` while vanilla's
hand-written **pronoun set** `xe/xem/…` keeps `human / sib / progenitor`. A player who leaves the
Pronoun Set row on its `<from gender>` default — which is what it defaults to — never meets the
difference.

### 16.6 What this does not do

- **No vanilla gender is removed or altered**, apart from `elverson`'s one `Generic` attribute.
  `<removegender>` exists and this file deliberately does not use it, for the reason §1.0b of
  `docs/STYLEGUIDE.md` gives about `<removetable>`.
- **`EnableGeneration` stays off.** It is a third switch on both files, and it invents genders at
  runtime — pronouns assembled from a syllable kit, a generated name, generated person terms. Roughly
  half of what it produces reads as a plausible neopronoun and half does not, and a bad roll is
  visible for a whole run. Investigated and declined in #435.
- **NPC naming is unaffected.** §15's namestyles scope on gender, so a gender added here will reach
  them, but nothing in this file changes how anyone is named.

### 16.7 It also widened what the world generates, which was not the intent

Adding nine genders changes more than the character-creation list, and I did not think of this when
I argued for it.

`Gender.CheckSpecial` resolves a set of keywords a blueprint can use in place of a gender name —
`genericpersonalsingular`, `personalsingular`, `any`, `generic` and others — and they resolve through
the same `GetAllGenericPersonalSingular()` the chargen row uses. **That list went from 4 to 13.**

Nine vanilla creature blueprints use one of those keywords in their `RandomGender` tag. Those
creatures now turn up as `fae`, `xe`, `spivak`, `ve`, `per`, `ne`, `ze`, `sie` or `elverson` where
before they could only be `male`, `female`, `neuterperson` or `nonspecific`.

`male` and `female` are untouched — `CheckSpecial` passes an ordinary gender name straight through
(`_ => Name`), so `RandomGender="male,female"`, which 117 of the 126 human blueprints inherit from
`BaseHuman`, is still the same coin flip it always was. Only the blueprints that deliberately asked
for "any generic personal singular gender" see a wider one.

I think this is right — a blueprint asking for any generic gender should get any generic gender, and
narrowing it would mean the fork adding genders and then hiding them from the world it added them
to. But it is a change to what the world generates rather than to what a player can pick, it was not
argued for, and it should not have been discovered by someone noticing a village full of women and
asking whether something had skewed. Recorded here so the next person meets it as a decision rather
than a surprise.

## 17. Creature variants (`ObjectBlueprints/Creatures.xml`)

**44 cosmetic colour and name variants of nineteen common creatures** (#171). Option-gated by
`OptionQudExpandedCECreatureVariants`, default **on**.

### 17.1 The one rule that keeps this cosmetic

> **A variant may differ in name, colour and flavour text. It must not differ in stats.**

Two identically-sized glyphs behaving differently, with only colour to warn you, reads as a bug when
it kills you. Nothing below declares a `<stat>` or any part other than `Render` and `Description`.

### 17.2 How they reach the world, and the attempt that did not

Distribution is by **explicit entry in `mod/Core/PopulationTables.xml`**, merged into the vanilla table a
zone template actually draws from. That is how every other piece of this fork's content is
distributed, and `docs/STYLEGUIDE.md` §3.3 says so.

The first attempt used `DynamicObjectsTable:<Biome>_Creatures` tags, on the reading that a creature
self-registers into a spawn table. **Those tables do not put a creature in a zone.** No population
table references one and no zone builder requires one. All 32 shipped, and none ever spawned.

They are not inert, though — I said they were, and that was wrong. Every biome-keyed pool is rolled
by **procedural village generation** (`VillageBase.cs:167` for creatures), which decides who lives in
a village rather than what walks a hillside. So the tags were pointed at villagers while the design
was about wilderness. `docs/LESSONS.md` carries the full account and the correction.

So every target table here was checked for a consumer **before** a line was written, and the dun goat
shipped alone and was walked in a running game before the other 31 followed.

### 17.3 Weights are derived, not chosen

**A variant takes its parent's `Chance` in that same table, and about half its `Number`.** So you
meet a variant roughly as often as you meet the animal it is a variant of, but there are fewer of
them when you do — the ordinary animal stays the common one by *count*, not by how rarely it turns
up. In `pickone` groups the currency is `Weight` and the same rule applies.

That is the second version of this curve. The first put each variant one step below its parent on
vanilla's chance ladder, which reads sensibly in the hills where vanilla sits at 25–50, and fails
everywhere vanilla is already low: in the desert canyon and the jungle it pushed thirteen variants
to a 5% floor, needing about 58 zones of the right biome apiece to meet one. Playtesting found them
essentially invisible. Deriving from the parent's own frequency instead is what fixes it, and it can
never make a variant likelier than the animal it varies.

**Six are still uncommon, and deliberately so**: the jungle boar, salamander and chameleon and the
ruins beetles and glowmoth sit at vanilla's own 5% in those tables. Their variants match, which means
you will meet a russet boar about as often as a plain jungle boar — rarely, because vanilla makes
boars rare in the jungle.

The black goat and the rust-furred baboon are held one step below their parents rather than matching,
which is the rarity the roster always wanted and the first attempt could not express at all.

**Where the parent's `Number` is already 1 there is nothing to halve, so the `Chance` or `Weight`
halves instead.** Without that a variant of a single-spawn animal would be purely additive at the
parent's own rate — a black bear at the cave tables' `Bear` weight of 5 would mean a bear *and* a
black bear drawn as readily as each other.

### 17.3a Three of them lived in a table vanilla had switched off

The black bear, chalk centipede and hoary bat were merged into
`LowerTremblingDunesZoneGlobals`, whose contents **Freehold commented out** — along with
`TrembleRocky` and `TremblingDunesSurfaceZoneGlobals`, all three inside one `<!-- -->` block. The
zone template still names the table and `Worlds.xml` still builds the zone, so the merge *created*
the table rather than landing nowhere: a running game reported the chalk centipede at 45%, exactly
the `Chance` declared.

Which meant this fork's three were **100% of that zone's global population**, in a place a player
walks into — and it re-enabled something vanilla had deliberately emptied. Both are things §3.2.1
and charter rule 2 exist to prevent, and nothing caught either, because `table-share` skipped a
table absent from the snapshot in silence. `scatter-share` (#474) reports it instead, which is how
this surfaced at all (#476).

**Redrock was the wrong answer, and measuring is what showed it.** The first rehoming sent them to
Redrock, on the reasoning that it is desert canyon country and holds all three parents. But Redrock
is one world-map cell — `x="0-2" y="0-2"`, `Mutable="false"` — and is reached by **1 of the game's
87 zonetemplates**. That is exactly as narrow as the place they came from: it would have fixed the
share and left the content just as hard to meet. Every named landmark is the same shape; the
Rustwells are also 1.

**Breadth is measurable, so measure it.** Follow each zonetemplate's `<population Table=>` through
nested `<table>` references and count which templates reach a given table. These three now sit in
the broadest table holding each parent that does not already carry a variant of it:

| variant | table | zonetemplates reaching it |
|---|---|---:|
| hoary bat | `Tier3CavePopulation` | 14 of 87 |
| black bear | `Tier3CavePopulation` | 14 of 87 |
| chalk centipede | `Shale Cave Critters 2` | 8 of 87 |

The centipede does not go to `Tier2CaveCreatures`, which reaches 14, because
`Vixy_SlateCentipede` is already there and two variants of one parent in one table is not what
§17.3's curve describes.

**The derivation was done against commented-out data.** The original weights carry notes reading
`Giant Centipede 45/1-2` and `Bat 90/1-3` — figures taken from inside the comment block, which is
why they looked authoritative. A commented-out record is not a record.

### 17.3b Which creatures can take a variant

Two rules, both learned the hard way:

**The parent must have a live population entry.** Not a `DynamicObjectsTable` tag — those distribute
into pools nothing reads. Grep for the blueprint name outside the file that declares it; if every hit
is a declaration, there is no route.

**Its colour must not be doing mechanical work.** This is what rules out the svardym, whose hatchling
green, scrounge red, eld blue and jut bright-green encode *rank* rather than coat. A variant there
would read as a different tier of enemy, which is the "two identical glyphs behaving differently"
failure §17.1 exists to prevent. Named uniques and vanilla's own variants are out for the same family
of reason — `Sultan Croc`, `Astral Tabby`, `Two-Headed Boar`.

### 17.4 One restoration and two additions

**`Baboon` is added to the desert canyon.** Vanilla's own tags say baboons belong there and the
mechanism that would have delivered them is dead, so this is authored intent being restored rather
than a placement invented.

**Two placements have no vanilla backing and are deliberate new content:** the **marsh dog** and the
**salt beetle**. Nothing in vanilla, live or dead, puts a dog in the saltmarsh or a beetle on the
dunes. Both are marked in the XML. The marsh dog stands without a plain dog beside it on purpose —
it is a marsh-adapted animal, not a coat on something that already lives there.

### 17.5 Naming

Names follow what vanilla does to its own creatures: keep the word carrying species identity, swap
the word carrying the distinction. `giant beetle` becomes `clockwork beetle` in vanilla, which is why
the beetles here drop "giant"; `horned chameleon` keeps "horned", because horns are anatomy. Across
all 1,072 vanilla creature display names, no vanilla variant replaces its parent's species noun.

### 17.6 The catalogue

✦ marks a variant carrying its own description, because the inherited one names a colour it does not
have — both salamanders inherit "ovoid spots, crimson and coral and citrine", and the beetles inherit
"shining black elytra".

| Variant | Parent | Table | Entry |
|---|---|---|---|
| ash-coated dog | `Dog` | `MountainsZoneGlobals-Reachable` | Chance=25 Number=1d2 |
| ashen salamander ✦ | `Salamander` | `DesertCanyonZoneGlobals-Reachable` | Chance=10 Number=1d4 |
| ashwing glowmoth | `Glowmoth` | `RuinsZoneGlobals-Creatures` | Chance=5 Number=1 |
| banded honey skunk | `Honey Skunk` | `HillsZoneGlobals-Reachable` | Chance=50 Number=1 |
| black bear ✦ | `Bear` | `Tier3CavePopulation` | Weight=2 Number=1 |
| black goat | `Goat` | `MountainsZoneGlobals-Reachable` | Chance=25 Number=1d3 |
| brindle dog | `Dog` | `HillsZoneGlobals-Reachable` | Chance=25 Number=1d2 |
| bristleback boar | `Boar` | `HillsZoneGlobals-Reachable` | Chance=25 Number=1d2 |
| chalk centipede | `Giant Centipede` | `Shale Cave Critters 2` | Chance=25 Number=1-2 |
| cinder glowcrow ✦ | `Glowcrow` | `DesertCanyonZoneGlobals-Reachable` | Chance=10 Number=1d6 |
| cinnamon bear | `Bear` | `Tier2CaveCreatures` | Weight=2 Number=1 |
| copper dragonfly | `GiantDragonfly` | `FlowerFieldsPopulation` | Chance=25 Number=1d6 |
| cragged goat | `Goat` | `MountainsZoneGlobals-Reachable` | Chance=50 Number=1d6 |
| dun goat ✦ | `Goat` | `HillsZoneGlobals-Reachable` | Chance=50 Number=1d3 |
| ember dragonfly | `GiantDragonfly` | `DesertCanyonZoneGlobals` | Chance=25 Number=1d6 |
| glass dragonfly | `GiantDragonfly` | `WaterCreatures` | Weight=5 Number=1 |
| hoary bat | `Bat` | `Tier3CavePopulation` | Weight=2 Number=1 |
| lantern glowcrow | `Glowcrow` | `FlowerFieldsPopulation` | Chance=10 Number=1d6 |
| mangy baboon | `Baboon` | `DesertCanyonZoneGlobals-Reachable` | Chance=10 Number=1d2 |
| marbled salamander ✦ | `Salamander` | `JungleZoneGlobals` | Chance=5 Number=1-2 |
| marsh dog | `Dog` | `SaltMarshZoneGlobals` | Chance=25 Number=1d2 |
| meadow salthopper ✦ | `Salthopper` | `FlowerFieldsPopulation` | Chance=5 Number=1 |
| midden beetle ✦ | `Giant Beetle` | `RuinsZoneGlobals-Creatures` | Chance=5 Number=2-3 |
| mossbacked tortoise | `IrritableTortoise` | `FlowerFieldsPopulation` | Chance=10 Number=1d2 |
| mottled horned chameleon | `Horned Chameleon` | `JungleZoneGlobals` | Chance=5 Number=1 |
| ochre salthopper ✦ | `Salthopper` | `DesertCanyonZoneGlobals-Reachable` | Chance=5 Number=1 |
| pale boar | `Boar` | `DesertCanyonZoneGlobals-Reachable` | Chance=10 Number=1 |
| pale croc | `Croc` | `WaterCreatures` | Weight=5 Number=1 |
| pale glowfish | `Glowfish` | `WaterCreatures` | Weight=5 Number=1 |
| piebald equimax | `Equimax` | `FlowerFieldsPopulation` | Chance=30 Number=1d6 |
| pied dog | `Dog` | `FlowerFieldsPopulation` | Chance=10 Number=1d2 |
| rangy dog | `Dog` | `DesertCanyonZoneGlobals-Reachable` | Chance=10 Number=1d2 |
| rufous bat | `Bat` | `Tier2CaveCreatures` | Weight=2 Number=1 |
| russet boar | `Boar` | `JungleZoneGlobals` | Chance=5 Number=1 |
| rust beetle ✦ | `Giant Beetle` | `RuinsZoneGlobals-Creatures` | Chance=5 Number=2-3 |
| rust-furred baboon | `Baboon` | `BaboonParty` | Chance=50 Number=1 |
| salt beetle ✦ | `Giant Beetle` | `SaltDuneCreatures` | Number=1-2 |
| sand horned chameleon | `Horned Chameleon` | `DesertCanyonZoneGlobals-Reachable` | Chance=10 Number=1 |
| scarred tortoise | `IrritableTortoise` | `HillsZoneGlobals-Reachable` | Chance=25 Number=1d2 |
| silt croc | `Croc` | `SaltMarshZoneGlobals` | Chance=50 Number=1 |
| silverback baboon | `Baboon` | `BaboonParty` | Chance=90 Number=1-2 |
| slate centipede | `Giant Centipede` | `Tier2CaveCreatures` | Weight=10 Number=1-2 |
| sorrel equimax | `Equimax` | `DesertCanyonZoneGlobals-Reachable` | Chance=10 Number=1d6 |
| verdigris glowfish | `Glowfish` | `SaltMarshZoneGlobals` | Chance=75 Number=1d4 |

### 17.7 The option

`OptionQudExpandedCECreatureVariants`, default on, read by `Raven_Options.ApplyCreatureVariants`. It
walks `PopulationManager.Populations` and detaches every entry whose blueprint carries the
`Vixy_CreatureVariant` tag, remembering where each came from so the toggle is reversible — the same
shape as the psionic chip option in §13.

The tag matters: a `Vixy_` prefix match would also catch 32 glaives, spears and quarterstaves and
quietly empty three weapon families out of the loot tables.

The first attempt gated this with `ExcludeFromDynamicEncountersOption`, which costs no C# at all —
but that tag is read only by the dynamic table fabricators, so on this route it gated nothing.

## 18. Harvestable plants (`ObjectBlueprints/Plants.xml`)

**Six harvestable plants, one each for Mountains, Saltmarsh, BananaGrove, Hills, DesertCanyon and
Jungle** (#177, #540), with a yield and a preserved cooking ingredient apiece. Everything here is
data — no scripting, so no charter rule 5 budget spent.

### 18.1 How thin vanilla actually is

Resolving every biome's population tables transitively — following `<table>` references as well as
`<object>` entries — no biome in the game reaches more than three harvestable plants:

| Harvestables reachable | Biomes |
|---:|---|
| 0 | RainbowWood, SaltDesert, SecretRuins |
| 1 | BananaGrove, Jungle, Ruins, LakeHinnom, PalladiumReef, Golgotha, GritGate |
| 2 | Hills, Mountains, DesertCanyon, DeepJungle, BaroqueRuins, Rivers, MoonStair |
| 3 | Saltmarsh — the richest biome in the game |

`Starapple Tree` appears in nearly all of them, so the real variety is closer to **one distinctive
plant per biome**. The cooking-ingredient pools tell the same story from the other end:
`BananaGrove_Ingredients` holds one entry and `Mountains_Ingredients` three.

Wave one took the thinnest three of those with unambiguous theming. **Wave two took the three that
shared an identical list**: counting distinct species rather than blueprints, `Hills`, `DesertCanyon`
and `Jungle` each offered starapple, its Barathrumite variant and witchwood — two species, and the
same two, across the biomes a player crosses most.

`Water` and `Ruins` report no harvestables at all, and are deliberately left alone: their `_Plants`
pools hold mangroves and star palms, which is a village-building tree list rather than a foraging
gap.

### 18.2 The chain, and that all of it is data

```
plant (Harvestable) ──▶ yield (Snack) ──PreservableItem──▶ ingredient (PreparedCookingIngredient)
```

`Harvestable` is an attribute-only part — `OnSuccess`, `OnSuccessAmount`, `StartRipeChance`,
`DestroyOnHarvest`, and the ripe/unripe colour and tile fields. Every link is a vanilla part used
the way vanilla uses it.

**No new cooking effect is introduced.** `regenLowtier`, `plantMinor` and `starch` are all carried
by vanilla plants today, so the cooking system gains ingredients rather than behaviour. That was the
point of starting here: a new reagent with no consumer is inventory clutter.

Tiles are vanilla's, recoloured — the same route the creature variants took in §17, and the reason
these cost no art.

### 18.3 Ripeness is derived, not chosen

The number that matters is not `StartRipeChance` on its own but **how many ripe plants a zone
actually holds**, which is `Chance × Number ÷ StartRipeChance` across the population entry. Vanilla's
band runs 0.07 (witchwood tree) to 8.1 (watervine), and it is dense between 0.6 and 1.0:

| vanilla plant | ripe per zone | | this fork | ripe per zone |
|---|---:|---|---|---:|
| watervine | 8.10 | | brinereed | 1.50 |
| yuckwheat | 6.67 | | broadglove | 0.92 |
| noisegrass | 3.20 | | sweetfrond | 0.88 |
| urberry bush | 1.04 | | rimeburr | 0.73 |
| dreadroot | 0.84 | | cragwort | 0.72 |
| banana tree | 0.81 | | shadetooth | 0.63 |
| witchwood tree | 0.07 | | | |

All six land in the dense part of vanilla's band, and the highest is brinereed — whose yield is
also the cheapest of the six. Cheap staples sitting commoner than valuable ones is vanilla's own
shape. The lowest is shadetooth, in the biome with the least of everything.

**Three files hold the inputs**, so changing a `Number` in `PopulationTables.xml` without
recomputing against `StartRipeChance` moves a figure this section states. Nothing checks it.

### 18.4 Prices are anchored to a neighbour, not to the value curve

The value curve does not describe food, and **`item-curve` now exempts it** — of vanilla's 32
edibles carrying both a `Tier` tag and a price, none sits on the curve, at ratios from 0.006 to
6.25. `docs/STYLEGUIDE.md` §3.2 carries the reasoning and the measurement.

So each price is anchored to a named vanilla neighbour instead:

| item | value | anchored to |
|---|---:|---|
| cragwort sprig | 4 | witchwood bark, 4 — also a mountain harvest |
| dried cragwort | 4 | freeze-dried hoarshrooms and pickled mushrooms, both 4 |
| brinereed shoot | 2 | dried lah petals and pickles, both 2 |
| salted brinereed | 2 | pickles, 2 |
| sweetfrond heart | 8 | the banana, 8 — from the same grove |
| candied sweetfrond | 8 | sun-dried banana, 8 — likewise |

### 18.4b A plant you cannot see is a plant that is not there

Cragwort shipped in `&K` — the darkest grey Qud has — on a `&K` tile, both taken from noisegrass
along with its sprite. Noisegrass lives in fungal and underground zones where near-black reads
fine. On an open mountain surface it was the least visible thing on screen, next to dogthorn at
`&G` and witchwood at `&W`.

A playtest crossed several parasangs of mountains and found **no cragwort at all, while finding
witchwood** — which rolls from the same table at `Chance=25` against cragwort's `40`. A thing that
should be commoner turning up never, beside a thing that is rarer and white, is what a contrast
failure looks like from the player's side.

It is now brown-olive, `&w` on `&w` with a `y` detail, which keeps the ochre-on-rock intent inside
the visible half of the palette.

**Ripeness is a hue change, not a brightness bump.** Vanilla always signals it that way — witchwood
`&W` → `&r`, starapple `&g` → `&R`, noisegrass `&K` → `&M`. Cragwort's old values left the tile
`&K` in both states and moved a single detail pixel, so even a ripe one looked the same from a
distance. Ripe now lifts the whole tile.

Brinereed (`&g`) and sweetfrond (`&G`) were already in the visible range and are unchanged.

### 18.5 Three tags that came with the base, and had to be corrected

Inheriting from vanilla's `Plant` carries `Fiber="strip"`, `FiberMaterial="bark"` and
`Plank="plank"`. Nothing in this fork wrote them, and a playtest found all three in the semantic
tables — a reed yielding **bark**, mountain scrub yielding **planks**.

Vanilla does not accept its own defaults either: **17 of its plants override at least one**. So each
of these takes a named neighbour rather than a guess, and only where the default is wrong:

| plant | Fiber | FiberMaterial | Plank | taken from |
|---|---|---|---|---|
| cragwort | twine | thatch | thatch | slime grass — the same grass idiom |
| brinereed | rope | fibre | bundle | brinestalk, the saltmarsh's own reed |
| sweetfrond | *(inherited `strip`)* | fibre | frond | `frond` is Yempuris's word |

`stag` rather than `tag`, which is what vanilla uses for all three: 26 of 26 for `Plank`, 14 of 14
for `FiberMaterial`.

This is the charter's "know the blast radius" in miniature. The blast radius of `Inherits="Plant"`
is three tags nobody wrote, and **only the game showed them** — every static check passed. Nothing
checks these values.

### 18.6 The catalogue

| plant | biome | yield | preserved into | cooking effect |
|---|---|---|---|---|
| cragwort | Mountains | cragwort sprig | dried cragwort | `regenLowtier` |
| brinereed | Saltmarsh | brinereed shoot | salted brinereed | `plantMinor` |
| sweetfrond | BananaGrove | sweetfrond heart | candied sweetfrond | `starch` |

### 18.6b They can be a village's plant, which needed a tag

Each plant carries `DynamicObjectsTable:<Biome>_Plants`. That pool is rolled by procedural village
generation — `VillageBase.cs:1430` picks a region's plant, and §18.5's `Plank`, `Fiber` and
`FiberMaterial` words are what name it in the wall description. Without the tag these three could
only ever be picked by already standing in the zone the village was built in, never through the pool
vanilla uses.

**Wild flora carries `_Plants` alone.** Brinestalk is the model, with `Saltmarsh_Plants` and nothing
else. `_FarmablePlants` is deliberately absent: that pool is for crops villagers *grow*, which
witchwood and yuckwheat are and these are not.

| plant | pool | vanilla entries before | after |
|---|---|---:|---:|
| cragwort | `Mountains_Plants` | 4 | 5 |
| brinereed | `Saltmarsh_Plants` | 2 | 3 |
| sweetfrond | `BananaGrove_Plants` | 2 | 3 |

`tools/dynamic-pools.json` pins all three, so a fourth arriving unnoticed fails a commit.

### 18.7 The ingredient pools are village pools, not loot pools

`DynamicObjectsTable:<Biome>_Ingredients` looks like the obvious way to distribute a preserved
ingredient — 73 vanilla blueprints tag themselves into twelve of these pools, and **no population
table references one**. The only dynamic pools `PopulationTables.xml` ever names are `Ammo`,
`AnimatableFurniture`, `Baboons`, `Chests`, `Corpses`, `EnergyCells`, `Goatfolk`, `Grenades`, `Guns`,
`Headwear`, `Items`, `Naphtaali`, `SecurityCards`, `Snapjaws`, `TechTurrets`, `Tonics_NonRare`,
`TradeGoods` and `Trinkets` — all flat.

**I first wrote that this meant nothing rolls them, and that was wrong.** `VillageBase.cs:2586` rolls
`"DynamicObjectsTable:" + region + "_Ingredients"` when it stocks a village, and every other
biome-keyed family has an equivalent line. The names are built by string concatenation at runtime, so
no amount of grepping the data will find them — which is exactly why the data grep looked conclusive.

That sentence did more work than it should have. **A preserved ingredient placed *only* in that pool
would turn up in villages rather than in the wild, which is not what the plants are for** — and that
is still true, which is why the plants themselves reach the world through explicit population
entries. What it does not settle is whether the *preserves* should also be there, and I read it as
though it did.

They should, and now are (#489). The distinction is that the plants and their preserves are
different objects with different lives: a plant is found, a preserve is made. The three preserves
have **no explicit population entry at all** and were never going to have one — you get them by
harvesting and preserving. So the tag adds a route rather than replacing one, and the route it adds
is the one vanilla uses for exactly this kind of object.

| preserve | pool | pool held |
|---|---|---|
| `Vixy_Dried Cragwort` | `Mountains_Ingredients` | 3, all jerky |
| `Vixy_Salted Brinereed` | `Saltmarsh_Ingredients` | 3 |
| `Vixy_Candied Sweetfrond` | `BananaGrove_Ingredients` | **1** |

**24 of vanilla's 40 preserved cooking ingredients carry one of these tags, and the split is the
argument.** Every regional plant preserve is in — Starapple Preserves, Fermented Yondercane, Dried
Lah Petals, Vinewafer Sheaf, Fermented Yuckwheat Stem. What is out is mostly manufactured or
placeless: Food Cube, Canned Have-It-All, Crusty Loaf, Mirror Dust. These three are the first kind.
Raw snacks are out too, on both sides — Starapple and Yondercane carry no tag, only what has been put
up for keeping does.

`BananaGrove_Ingredients` deserves its own note, because this fork becomes **half** of it. That is
over the line §3.2.1 draws for the routes where a share is chosen, and it is the right call anyway:
a signature dish asks for one to three *distinct* ingredients and retries 25 times to avoid a
repeat, so a pool holding one member cannot serve a dish that wants two. Adding the second is closer
to repairing the mechanic than to crowding it.

The rest of the original correction stands: the reason those pools looked empty was "wrong
consumer", not "no consumer". `docs/LESSONS.md` carries it and the reason the original search
failed.

**The six new food objects do sit in `DynamicObjectsTable:Items`**, which *is* consumed. That comes
from vanilla's `Item` base by inheritance, and every vanilla food is in it on the same route —
`Bundle of Noisegrass`, `Vinewafer Sheaf` and `Urberry` included. It is recorded in
`tools/dynamic-pools.json` rather than stripped with `*delete`, because matching vanilla is the
correct behaviour here rather than something to tidy away.

## 19. Ruins overgrowth (`ObjectBlueprints/Plants.xml`)

**Two decorative plants for Ruins and BaroqueRuins** (#173): **slabmoss** on the floor and
**pallvine** against the walls. They are the first blueprints in this fork that give a player
nothing — no yield, no ingredient, no stat. That is the whole scope: a ruin should look like
something has been growing in it for a thousand years, and nothing a player can act on should move.

### 19.1 Vanilla's own patch idiom, which is better than a zone builder

The design this came from assumed a C# zone builder registered through `ZoneManager.AddZoneBuilder`,
with hand-written noise for patch shapes and a hand-written reachability guard. None of that is
needed. `BrightshroomPatches` and `GraveMossPatches` are the same table twice, and they are a
complete overgrowth system in data:

```xml
<group Name="Types" Style="pickone">
  <group Name="Small" Style="pickeach" Weight="95">   <!-- the usual zone -->
    <object Chance="100" Blueprint="Grave Moss" Number="12-20" Hint="Adjacent:90" />
  <group Name="Large" Style="pickeach" Weight="5">    <!-- the one that has gone under -->
```

Each line is one clump: the first object lands anywhere, and `Adjacent:N` grows the rest of that
line's `Number` outward from it. A `pickone` between a common Small arm and a rare Large one gives
the occasional zone that is properly overgrown. Vanilla pulls the whole thing in with one
low-chance reference — eight cave tiers at 30, the crypts at 60, the Moon Stair at 10.

So the mod spends **no rule 5 budget** here and ships no C# at all.

### 19.2 The hint is load-bearing twice

Every line carries one, and each does two jobs:

| plant | hint | places it | and |
|---|---|---|---|
| slabmoss | `Adjacent:90` | grows each clump outward from its first tile | runs the same-blueprint check |
| pallvine | `AlongWall` | in floor cells that touch masonry | runs the same-blueprint check |

**`LivesOnWalls` was the obvious hint for the vine and is not used.** It puts an object *in* the
wall cell, which is the stronger image — but it is one of four hints that set `flag3` in
`PlaceObjectInArea` and skip `Points.RemoveAll(… || l.HasObject(Blueprint))`. That is the check
whose absence produced `You pass by a brinereed and a brinereed` in #542, and taking it off again
for a nicer silhouette is not a trade worth making. `OnWall`, `Aquatic` and every `StackWith*` skip
it too, and in all four cases that is deliberate: co-locating is what those hints are *for*.

### 19.3 Why teal, and why not brighter

Every plant already growing in a ruin is green — swarmshade `&g`, ziv bough `&g`, star palm `&G`,
starapple `&g`. A fourth green reads as more canopy rather than as something on the floor, so
slabmoss is `&c` with a `C` detail: verdigris on old fulcrete, and the only value in the scene that
separates from the tree line. Pallvine stays `&g`, because a ruin's vegetation *is* green and the
shape carries the difference — vertical strands against the moss mat's speckle.

`RenderIfDark` is deliberately absent, though Grave Moss carries it. Seeing terrain in an unlit room
is information, and vanilla's own ruins vegetation does without it.

### 19.4 No new art, and two tilesets that were not taken

| plant | tile | variants | vanilla owner |
|---|---|---:|---|
| slabmoss | `Creatures/sw_moss_*.bmp` | 5 | Grave Moss |
| pallvine | `Terrain/sw_wheat_*.bmp` | 3 | Yuckwheat |

The atlas holds better art for this than either — `extrasolar-vine`, `finger-root`, `ring-moss` and
`star-orchid-lily` are literal vines, roots, moss rings and creepers, and **no population table
places any of them**. They belong to North Sheva's sacred plants, set by hand in the Star Orchid
Temple and the Starfarers' Quay. Reusing those silhouettes for common ground cover would turn a
named thing into wallpaper.

The same objection retired a third species. A root break splitting a ruin floor is the obvious
third, and the only real root-tendril tile is `sw_arsplice_hyphae_*` — **arsplice** being a
meaningful and dangerous thing in Qud, whose silhouette in a ruin would read as an infection rather
than as decoration. The near misses all belong to something too: `sw_tree_circle` is the sunflower,
`sw_tree_curly` the nachash tree, `sw_mushroom_terrain` the Rainbow Wood. Two species with honest
tiles beat three with one borrowed wrong.

### 19.5 Share

| table | vanilla | this fork | share |
|---|---:|---:|---:|
| `RuinsZoneGlobals-Vegetation` | 213.6 | 124.0 | 36.7% |
| `BaroqueRuinsZoneGlobals-Vegetation` | 707.0 | 124.0 | 14.9% |

Each reference is `Chance="60"`, so **84% of ruins zones carry one plant or the other** and about one
in thirty rolls the Large arm and has gone properly under. That figure is taken from the crypts,
which pull `GraveMossPatches` at 60-70, rather than from the caves at 30 or the Moon Stair at 10 —
grave moss is that frequent because being mossy is part of what a crypt is, and "overgrown" is the
same kind of claim about a ruin. This first shipped at 20, where five ruins in nine had neither
plant, which states the opposite of what the issue is for.

Both measured through the `<table>` reference, which `scatter-share` could not previously see
(#544). The measure over-counts a `pickone` group — one arm fires and both are summed — so the true
share is lower than either figure, in the direction that fails loud.

`RuinsZoneGlobals-Vegetation` is drawn by both the surface and the underground templates, so one
merge reaches either.

## Appendix A — every merged vanilla melee weapon

Full listing of the 79 `Load="Merge"` edits in `MeleeWeapons.xml`. Blank cells mean the mod did
not touch that field (the vanilla value is inherited).

| Blueprint | Tier | Damage | Pen | Max STR | Stat | Value | Weight |
|---|---|---|---|---|---|---|---|
| BaseAxe |  |  |  |  |  |  | 3 |
| Battle Axe | 0 |  |  |  |  | 3 | 4 |
| Battle Axe2 | 1 | 1d3 |  | 2 |  | 10 | 3 |
| Steel Battle Axe | 2 | 1d4 |  | 3 |  | 25 | 3 |
| Steel Battle Axeth | 2 | 1d4+2 | 1 | 3 |  | 25 | 5 |
| Battle Axe3 | 3 | 1d5 |  | 4 |  | 55 | 5 |
| Battle Axe3th | 3 | 1d5+2 | 1 | 4 |  | 55 | 8 |
| Battle Axe4 | 4 | 1d6+1 |  | 5 |  | 95 | 4 |
| Battle Axe4th | 4 | 1d6+3 | 1 | 5 |  | 95 | 6 |
| Battle Axe5 | 5 | 1d7+1 |  | 6 |  | 185 | 6 |
| Battle Axe5th | 5 | 1d7+3 | 1 | 6 |  | 195 | 9 |
| Battle Axe6 | 6 | 1d8+2 |  | 7 |  | 390 | 3 |
| Battle Axe7 | 7 | 1d9+2 |  | 8 |  | 720 | 3 |
| Battle Axe8 | 8 | 1d10+3 |  | 9 |  | 1500 | 2 |
| Iron Vinereaper | 1 | 1d3 |  | 2 |  | 5 | 2 |
| Steel Vinereaper | 2 | 1d4 |  | 3 |  | 35 | 2 |
| Battle Axe6th | 6 | 1d8+4 | 1 | 7 |  | 390 | 6 |
| Battle Axe7th | 7 | 1d8+5 | 1 | 8 |  | 720 | 6 |
| Battle Axe8th | 8 | 1d8+6 | 1 | 9 |  | 1500 | 5 |
| BaseLongBlade |  |  |  |  |  |  | 2 |
| Long Sword | 0 | 1d3 |  | 1 |  | 15 | 4 |
| Two-Handed Sword | 0 | 1d6 | 1 | 1 |  | 20 | 6 |
| Long Sword2 | 1 | 1d4 |  | 2 |  | 25 | 3 |
| Long Sword2th | 1 | 1d8 | 1 | 2 |  | 25 | 5 |
| Steel Long Sword | 2 | 1d6 |  | 3 |  | 30 | 3 |
| Steel Long Swordth | 2 | 1d10 | 1 | 3 |  | 30 | 5 |
| Long Sword3 | 3 | 1d8 |  | 4 |  | 55 | 5 |
| Long Sword3th | 3 | 1d12 | 1 | 4 |  | 55 | 7 |
| Long Sword4 | 4 | 1d10 |  | 5 |  | 95 | 4 |
| Long Sword4th | 4 | 2d6 | 1 | 5 |  | 95 | 6 |
| Long Sword5 | 5 | 1d12 |  | 6 |  | 195 | 6 |
| Long Sword5th | 5 | 2d6+1 | 1 | 6 |  | 195 | 9 |
| Long Sword6 | 6 | 2d6 |  | 7 |  | 390 | 3 |
| Long Sword6th | 6 | 2d8 |  | 7 |  | 390 | 5 |
| Long Sword7 | 7 | 2d6+1 |  | 8 |  | 720 | 3 |
| Long Sword7th | 7 | 2d10 | 1 | 8 |  | 720 | 5 |
| Long Sword8 | 8 | 2d8 |  | 9 |  | 1500 | 2 |
| Long Sword8th | 8 | 2d12 | 1 | 9 |  | 1500 | 4 |
| Vibro Blade | 5 | 1d10 |  | 0 |  | 300 | 2 |
| BaseDagger |  |  |  |  |  |  | 1 |
| Dagger | 0 | 1d2 |  | 1 |  | 5 | 1 |
| Dagger2 | 1 | 1d3 |  | 2 |  | 10 | 1 |
| Desert Kris | 1 | 1d3 |  | 2 |  | 15 | 1 |
| Steel Kukri | 2 | 1d4 |  | 3 |  | 20 | 1 |
| Steel Dagger | 2 | 1d4 |  | 3 |  | 20 | 1 |
| Steel Utility Knife | 2 | 1d4 |  | 3 |  | 20 | 1 |
| Steel Potter's Knife | 2 | 1d4 |  | 3 |  | 28 | 1 |
| Steel Butcher Knife | 2 | 1d4 |  | 3 |  | 28 | 1 |
| Dagger3 | 3 | 1d6 |  | 4 |  | 40 | 1 |
| Dagger4 | 4 | 1d8 |  | 5 |  | 75 | 1 |
| Obsidian Kris | 4 | 1d8 |  | 5 |  | 80 | 1 |
| Dagger5 | 5 | 1d10 |  | 6 |  | 150 | 2 |
| Dagger6 | 6 | 1d12 |  | 7 |  | 310 | 1 |
| Dagger7 | 7 | 1d12+1 |  | 8 |  | 690 | 1 |
| Dagger8 | 8 | 1d12+2 |  | 9 |  | 1390 | 1 |
| Vibro Dagger | 5 | 2d4 |  | 0 |  | 300 | 1 |
| ArmDagger4 | 4 | 1d4 |  | 5 |  | 75 | 1 |
| BaseCudgel |  |  |  |  |  |  | 3 |
| Club | 0 |  |  |  |  | 2 | 3 |
| Mace2 | 0 | 1d3 |  | 1 |  | 10 | 3 |
| Steel Hammer | 2 | 2d2 |  | 3 |  | 20 | 2 |
| Cudgel5th | 5 | 3d4 | 1 | 6 |  | 160 | 8 |
| Cudgel6 | 6 | 2d6 |  | 7 |  | 390 | 2 |
| Cudgel7 | 7 | 3d4 |  | 8 |  | 720 | 2 |
| Rhinox-Skull Maul | 6 | 3d4+1 | 1 | 7 |  | 320 | 10 |
| Warhammer2 | 1 | 2 |  | 2 |  | 10 | 3 |
| Steel War Hammer | 2 | 2d2 |  | 3 |  | 20 | 3 |
| Steel War Hammerth | 2 | 3d2 | 1 | 3 |  | 20 | 6 |
| Cudgel3 | 3 | 2d3 |  | 4 |  | 40 | 5 |
| Cudgel3th | 3 | 2d4+1 | 1 | 4 |  | 40 | 8 |
| Cudgel4 | 4 | 2d4 |  | 5 |  | 80 | 4 |
| Cudgel4th | 4 | 2d6 | 1 | 5 |  | 80 | 7 |
| Cudgel5 | 5 | 2d4+1 |  | 6 |  | 160 | 6 |
| Cudgel6th | 6 | 3d4+1 | 1 | 11 |  | 390 | 6 |
| Cudgel7th | 7 | 3d6 | 1 | 8 |  | 720 | 6 |
| Cudgel8 | 8 | 3d4+1 |  | 9 |  | 1500 | 3 |
| Cudgel8th | 8 | 4d6 | 1 | 9 |  | 1500 | 6 |

---

## Appendix B — every psionic chip

144 chips. `Mut. level` is the level of the granted mutation(s).

> 🗒️ **These are the ranks each chip grants, not necessarily the rank you will see.** Qud caps a
> mutation's effective rank at `level / 2 + 1` — `BaseMutation.GetMutationCapForLevel`, applying to
> every mutation from every source. So a perfected chip's rank 10 reads as rank 1 on a level-1
> character and is fully yours at level 18. Your character sheet shows the arithmetic per mutation,
> equipment bonus and cap both.

| Chip | Item tier | Value | Grants (mutation @ level) |
|---|---|---|---|
| basic disintegration chip | 4 | 20 | Disintegration @ 2 |
| upgraded disintegration chip | 6 | 80 | Disintegration @ 4 |
| perfected disintegration chip | 8 | 320 | Disintegration @ 6 |
| basic stunning force chip | 4 | 20 | StunningForce @ 2 |
| upgraded stunning force chip | 6 | 80 | StunningForce @ 4 |
| perfected stunning force chip | 8 | 320 | StunningForce @ 6 |
| basic force bubble chip | 4 | 20 | ForceBubble @ 2 |
| upgraded force bubble chip | 6 | 80 | ForceBubble @ 4 |
| perfected force bubble chip | 8 | 320 | ForceBubble @ 6 |
| basic force chipset | 6 | 80 | Disintegration @ 1, StunningForce @ 1, ForceBubble @ 1 |
| upgraded force chipset | 7 | 160 | Disintegration @ 2, StunningForce @ 2, ForceBubble @ 2 |
| perfected force chipset | 8 | 320 | Disintegration @ 3, StunningForce @ 3, ForceBubble @ 3 |
| kindle chip | 4 | 20 | Kindle @ 2 |
| kindle chip | 6 | 20 | Kindle @ 2 |
| kindle chip | 8 | 20 | Kindle @ 2 |
| basic flaming ray chip | 4 | 20 | FlamingRay @ 3 |
| upgraded flaming ray chip | 6 | 80 | FlamingRay @ 6 |
| perfected flaming ray chip | 8 | 320 | FlamingRay @ 10 |
| basic pyrokinesis chip | 4 | 20 | Pyrokinesis @ 2 |
| upgraded pyrokinesis chip | 6 | 80 | Pyrokinesis @ 4 |
| perfected pyrokinesis chip | 8 | 320 | Pyrokinesis @ 6 |
| basic fire chipset | 6 | 80 | Kindle @ 1, FlamingRay @ 2, Pyrokinesis @ 1 |
| upgraded fire chipset | 7 | 160 | Kindle @ 1, FlamingRay @ 4, Pyrokinesis @ 2 |
| perfected fire chipset | 8 | 320 | Kindle @ 1, FlamingRay @ 6, Pyrokinesis @ 3 |
| frost webs chip | 4 | 20 | FrostWebs @ 3 |
| frost webs chip | 6 | 20 | FrostWebs @ 3 |
| frost webs chip | 8 | 20 | FrostWebs @ 3 |
| basic freezing ray chip | 4 | 20 | FreezingRay @ 3 |
| upgraded freezing ray chip | 6 | 80 | FreezingRay @ 6 |
| perfected freezing ray chip | 8 | 320 | FreezingRay @ 10 |
| basic cryokinesis chip | 4 | 20 | Cryokinesis @ 2 |
| upgraded cryokinesis chip | 6 | 80 | Cryokinesis @ 4 |
| perfected cryokinesis chip | 8 | 320 | Cryokinesis @ 6 |
| basic ice chipset | 6 | 80 | FrostWebs @ 2, FreezingRay @ 2, Cryokinesis @ 1 |
| upgraded ice chipset | 7 | 160 | FrostWebs @ 2, FreezingRay @ 4, Cryokinesis @ 2 |
| perfected ice chipset | 8 | 320 | FrostWebs @ 2, FreezingRay @ 6, Cryokinesis @ 3 |
| basic EMP chip | 4 | 20 | ElectromagneticPulse @ 3 |
| upgraded EMP chip | 6 | 80 | ElectromagneticPulse @ 6 |
| perfected EMP chip | 8 | 320 | ElectromagneticPulse @ 10 |
| basic electrical generation chip | 4 | 20 | ElectricalGeneration @ 3 |
| upgraded electrical generation chip | 6 | 80 | ElectricalGeneration @ 6 |
| perfected electrical generation chip | 8 | 320 | ElectricalGeneration @ 10 |
| basic phasing chip | 4 | 20 | Phasing @ 3 |
| upgraded phasing chip | 6 | 80 | Phasing @ 6 |
| perfected phasing chip | 8 | 320 | Phasing @ 10 |
| basic lightning chipset | 6 | 80 | ElectromagneticPulse @ 2, ElectricalGeneration @ 2, Phasing @ 2 |
| upgraded lightning chipset | 7 | 160 | ElectromagneticPulse @ 4, ElectricalGeneration @ 4, Phasing @ 4 |
| perfected lightning chipset | 8 | 320 | ElectromagneticPulse @ 6, ElectricalGeneration @ 6, Phasing @ 6 |
| basic photosynthetic skin chip | 4 | 20 | PhotosyntheticSkin @ 3 |
| upgraded photosynthetic skin chip | 6 | 80 | PhotosyntheticSkin @ 6 |
| perfected photosynthetic skin chip | 8 | 320 | PhotosyntheticSkin @ 10 |
| basic light manipulation chip | 4 | 20 | LightManipulation @ 2 |
| upgraded light manipulation chip | 6 | 80 | LightManipulation @ 4 |
| perfected light manipulation chip | 8 | 320 | LightManipulation @ 6 |
| basic teleportation chip | 4 | 20 | Teleportation @ 2 |
| upgraded teleportation chip | 6 | 80 | Teleportation @ 4 |
| perfected teleportation chip | 8 | 320 | Teleportation @ 6 |
| basic light chipset | 6 | 80 | PhotosyntheticSkin @ 2, LightManipulation @ 1, Teleportation @ 1 |
| upgraded light chipset | 7 | 160 | PhotosyntheticSkin @ 4, LightManipulation @ 2, Teleportation @ 2 |
| perfected light chipset | 8 | 320 | PhotosyntheticSkin @ 6, LightManipulation @ 3, Teleportation @ 3 |
| basic corrosive gas chip | 4 | 20 | CorrosiveGasGeneration @ 3 |
| upgraded corrosive gas chip | 6 | 80 | CorrosiveGasGeneration @ 6 |
| perfected corrosive gas chip | 8 | 320 | CorrosiveGasGeneration @ 10 |
| basic confusion chip | 4 | 20 | Confusion @ 2 |
| upgraded confusion chip | 6 | 80 | Confusion @ 4 |
| perfected confusion chip | 8 | 320 | Confusion @ 6 |
| basic acid slime glands chip | 4 | 20 | AcidSlimeGlands @ 3 |
| upgraded acid slime glands chip | 6 | 80 | AcidSlimeGlands @ 6 |
| perfected acid slime glands chip | 8 | 320 | AcidSlimeGlands @ 10 |
| basic acid chipset | 6 | 80 | CorrosiveGasGeneration @ 2, Confusion @ 1, AcidSlimeGlands @ 2 |
| upgraded acid chipset | 7 | 160 | CorrosiveGasGeneration @ 4, Confusion @ 2, AcidSlimeGlands @ 4 |
| perfected acid chipset | 8 | 320 | CorrosiveGasGeneration @ 6, Confusion @ 3, AcidSlimeGlands @ 6 |
| basic syphon vim chip | 4 | 20 | LifeDrain @ 2 |
| upgraded syphon vim chip | 6 | 80 | LifeDrain @ 4 |
| perfected syphon vim chip | 8 | 320 | LifeDrain @ 6 |
| basic adrenal control chip | 4 | 20 | AdrenalControl2 @ 3 |
| upgraded adrenal control chip | 6 | 80 | AdrenalControl2 @ 6 |
| perfected adrenal control chip | 8 | 320 | AdrenalControl2 @ 10 |
| basic regeneration chip | 4 | 20 | Regeneration @ 3 |
| upgraded regeneration chip | 6 | 80 | Regeneration @ 6 |
| perfected regeneration chip | 8 | 320 | Regeneration @ 10 |
| basic blood chipset | 6 | 80 | LifeDrain @ 1, AdrenalControl2 @ 2, Regeneration @ 2 |
| upgraded blood chipset | 7 | 160 | LifeDrain @ 2, AdrenalControl2 @ 4, Regeneration @ 4 |
| perfected blood chipset | 8 | 320 | LifeDrain @ 3, AdrenalControl2 @ 6, Regeneration @ 6 |
| basic sunder mind chip | 4 | 20 | SunderMind @ 2 |
| upgraded sunder mind chip | 6 | 80 | SunderMind @ 4 |
| perfected sunder mind chip | 8 | 320 | SunderMind @ 6 |
| basic domination chip | 4 | 20 | Domination @ 2 |
| upgraded domination chip | 6 | 80 | Domination @ 4 |
| perfected domination chip | 8 | 320 | Domination @ 6 |
| basic mass mind chip | 4 | 20 | MassMind @ 2 |
| upgraded mass mind chip | 6 | 80 | MassMind @ 4 |
| perfected mass mind chip | 8 | 320 | MassMind @ 6 |
| basic mental chipset | 6 | 80 | SunderMind @ 1, Domination @ 1, MassMind @ 1 |
| upgraded mental chipset | 7 | 160 | SunderMind @ 2, Domination @ 2, MassMind @ 2 |
| perfected mental chipset | 8 | 320 | SunderMind @ 3, Domination @ 3, MassMind @ 3 |
| basic space-time vortex chip | 4 | 20 | SpacetimeVortex @ 2 |
| upgraded space-time vortex chip | 6 | 80 | SpacetimeVortex @ 4 |
| perfected space-time vortex chip | 8 | 320 | SpacetimeVortex @ 6 |
| basic time dilation chip | 4 | 20 | TimeDilation @ 2 |
| upgraded time dilation chip | 6 | 80 | TimeDilation @ 4 |
| perfected time dilation chip | 8 | 320 | TimeDilation @ 6 |
| basic temporal fugue chip | 4 | 20 | TemporalFugue @ 2 |
| upgraded temporal fugue chip | 6 | 80 | TemporalFugue @ 4 |
| perfected temporal fugue chip | 8 | 320 | TemporalFugue @ 6 |
| basic temporal chipset | 6 | 80 | SpacetimeVortex @ 1, TimeDilation @ 1, TemporalFugue @ 1 |
| upgraded temporal chipset | 7 | 160 | SpacetimeVortex @ 2, TimeDilation @ 2, TemporalFugue @ 2 |
| perfected temporal chipset | 8 | 320 | SpacetimeVortex @ 3, TimeDilation @ 3, TemporalFugue @ 3 |
| basic mental mirror chip | 4 | 20 | MentalMirror @ 2 |
| upgraded mental mirror chip | 6 | 80 | MentalMirror @ 4 |
| perfected mental mirror chip | 8 | 320 | MentalMirror @ 6 |
| basic teleport other chip | 4 | 20 | TeleportOther @ 2 |
| upgraded teleport other chip | 6 | 80 | TeleportOther @ 4 |
| perfected teleport other chip | 8 | 320 | TeleportOther @ 6 |
| basic force wall chip | 4 | 20 | ForceWall @ 2 |
| upgraded force wall chip | 6 | 80 | ForceWall @ 4 |
| perfected force wall chip | 8 | 320 | ForceWall @ 6 |
| basic neutral mind chipset | 6 | 80 | MentalMirror @ 1, TeleportOther @ 1, ForceWall @ 1 |
| upgraded neutral mind chipset | 7 | 160 | MentalMirror @ 2, TeleportOther @ 2, ForceWall @ 2 |
| perfected neutral mind chipset | 8 | 320 | MentalMirror @ 3, TeleportOther @ 3, ForceWall @ 3 |
| basic heightened quickness chip | 4 | 20 | HeightenedSpeed @ 3 |
| upgraded heightened quickness chip | 6 | 80 | HeightenedSpeed @ 6 |
| perfected heightened quickness chip | 8 | 320 | HeightenedSpeed @ 10 |
| basic ego projection chip | 4 | 20 | WillForce @ 2 |
| upgraded ego projection chip | 6 | 80 | WillForce @ 4 |
| perfected ego projection chip | 8 | 320 | WillForce @ 6 |
| basic heightened hearing chip | 4 | 20 | HeightenedHearing @ 3 |
| upgraded heightened hearing chip | 6 | 80 | HeightenedHearing @ 6 |
| perfected heightened hearing chip | 8 | 320 | HeightenedHearing @ 10 |
| basic neutral body chipset | 6 | 80 | HeightenedSpeed @ 2, WillForce @ 1, HeightenedHearing @ 2 |
| upgraded neutral body chipset | 7 | 160 | HeightenedSpeed @ 4, WillForce @ 2, HeightenedHearing @ 4 |
| perfected neutral body chipset | 8 | 320 | HeightenedSpeed @ 6, WillForce @ 3, HeightenedHearing @ 6 |
| basic clairvoyance chip | 4 | 20 | Clairvoyance @ 2 |
| upgraded clairvoyance chip | 6 | 80 | Clairvoyance @ 4 |
| perfected clairvoyance chip | 8 | 320 | Clairvoyance @ 6 |
| basic psychometry chip | 4 | 20 | Psychometry @ 2 |
| upgraded psychometry chip | 6 | 80 | Psychometry @ 4 |
| perfected psychometry chip | 8 | 320 | Psychometry @ 6 |
| basic precognition chip | 4 | 20 | Precognition @ 2 |
| upgraded precognition chip | 6 | 80 | Precognition @ 4 |
| perfected precognition chip | 8 | 320 | Precognition @ 6 |
| basic neutral spirit chipset | 6 | 80 | Clairvoyance @ 1, Psychometry @ 1, Precognition @ 1 |
| upgraded neutral spirit chipset | 7 | 160 | Clairvoyance @ 2, Psychometry @ 2, Precognition @ 2 |
| perfected neutral spirit chipset | 8 | 320 | Clairvoyance @ 3, Psychometry @ 3, Precognition @ 3 |
