# Style Guide

How this repository is organised, named, and formatted.

`CHARTER.md` holds the **charter** — the six rules I maintain this fork under, and why. This
document is the mechanical layer beneath it: given those rules, what does a file get called, how
is it indented, and what is safe to change. Where the two touch, the charter wins.

Everything here is either an industry-standard convention, a Steam Workshop requirement, or a
constraint imposed by Qud's own loader. Where a rule exists only because Qud forces it, that is
stated — those are the ones that look arbitrary and are not.

---

## 1. The rule that comes before all the others

> **Some names are identifiers, not labels. Renaming them orphans data, breaks other mods, or
> breaks the mod itself — silently, with no error.**

Sort them into three groups before touching any of them: permanently frozen (§1.1), frozen since
this fork released (§1.1b), and free (§1.3). Conflating the first two is how a fork either
paralyses itself or breaks its own merges.

Qud resolves modded XML by **root element, not by filename**. Verified across the 87 mods
installed locally: `ObjectBlueprints.xml`, `Objectblueprints.xml`, and
`ShadowsOfTheSultans_PopulationTables.xml` all load correctly, because the loader reads the root
element (`<objects>`, `<populations>`) and ignores what the file is called.

That makes **filenames free** and makes several other things **frozen**. Know which is which
before renaming anything.

### 1.0b `<removetable>` — the tool this mod deliberately does not use

Qud can remove a table reference from a population group:

```xml
<group Name="Items" Load="Merge">
  <removetable Name="Armor 6C" />
</group>
```

The syntax is **Arendeth's**, worked out for this mod when an earlier attempt was malformed. It is
recorded here because it is genuinely hard to find, and because the code it was written for is
gone.

**Do not reach for it.** Charter rule 1 makes edits additive, and removing a vanilla table
reference is destructive twice over: it discards whatever a future Qud patch adds behind that
reference, and it makes any other mod's additions invisible too. It was used on
`Armor 7C/7R/8C/8R` to sever the tier cascade, and the effect was far larger than intended — a
tier-8 armor roll went from vanilla's 8.6% chance of a zetachrome piece to 100%, and vanilla items
reachable only through the cascade stopped dropping at all. Removed in #4.

**What to do instead: weight your own entries.** Weight is entirely within your own records, needs
no merge trickery, survives vanilla patches, and coexists with other mods. If your new items are
not showing up often enough, they are underweighted — the vanilla cascade is not the problem.

### 1.0c Skills merge per power, by name

`mod/Core/Skills.xml` touches eight vanilla skills — Axe, Cooking and Gathering, Cudgel, Long
Blade, Multiweapon Fighting, Short Blade, Tinkering, Wayfaring — and edits individual powers inside
them without restating the rest.

**The loader merges at the level of the individual power, keyed by its `Name`, and keeps every
attribute the mod does not restate.** That is why an entry like

```xml
<power Name="Multiweapon Expertise" Minimum="21|21" Tile="..." Foreground="y" Detail="M" />
```

works despite carrying no `Class=` and no `Cost=`: it is editing vanilla's entry, not replacing it.
Here that single change is the whole point — the mod's contribution to that tree is a requirement
cut, `23|23` down to `21|21`.

The evidence is the mod itself. **24** of the powers it declares omit `Class=`. If redeclaring a
skill replaced it, all 24 would be left with no implementation — Cleave, Berserk!, Tinker I/II/III,
Disassemble and the rest — and the mod would be obviously broken rather than subtly wrong. It has
played correctly for years. Replacement would also have silently deleted **34** vanilla powers,
including Tinkering's Repair and Scavenger and Long Blade's Lunge and Swipe.

The four exceptions declare `Class=` because they are new powers rather than edits to vanilla ones:
the Finesse power on each of the four melee trees.

> 🗒️ Both figures were exact when this section was written against six skills (#87), and one of
> them stopped being so without anyone noticing. Adding Short Blade for its Finesse power (#146)
> left `23` correct by coincidence — a power carrying `Class=` does not count toward it — while
> quietly taking the deletion count from 18 to 25, because the mod names only one of Short Blade's
> seven. Wayfaring (#470) then moved both. `check_docs.py` does not recount either one, which is
> why they drifted where the option and blueprint counts beside them could not.

**Write `Load="Merge"` on the skill anyway** (#87). The mod did not, for years, and was saved by the
loader's default rather than by intent — which is precisely the arrangement charter rule 1 exists to
prevent. Explicit is also durable: it states what is meant, survives a change to the loader's
default, and matches every other merge in the mod.

### 1.1 Permanently frozen — never rename

These are frozen by vanilla identity or engine requirement. **No release schedule or save policy
changes them.**

| Thing | Why |
|---|---|
| **Vanilla blueprint names** (`Cudgel3`, `Battle Axe3th`, `Iron Vinereaper`) | Vanilla identity. Renaming doesn't break a save — it silently orphans the `Load="Merge"`, and the edit simply stops applying. No error. |
| **Population table names** (`Artifact 6R`, `Melee Weapons 3C`) | Same: the merge target must match vanilla exactly. |
| **`.rpm` map basenames** (`Joppa.rpm`) | The basename *is* the zone the patch applies to. |
| **`workshop.json`, `manifest.json`, `preview.png`** | Required names — the Workshop uploader and Qud's mod loader look for exactly these. |
| **Options filename pattern** | Qud only treats a file as mod options if the filename **contains `Option`**. `ModOptions.xml` and `Options.xml` both work; `Settings.xml` does not. |
| **The `Raven_` prefix** | Charter rule 3 — policy, not technology. Mura's signature in the namespace, and the attribution future contributors actually read. |

### 1.1b Frozen since first release

These are frozen by **save compatibility**, and that freeze is now in force.

**The window closed on 2026-08-17, when `v2.3.0` shipped** as this fork's first release. Until
then these were genuinely free — the fork publishes as a new Workshop item and its notes require a
new character, so nothing carried over from Mura's original and there were no saves of its own to
protect. That is no longer true. There are players with saves now, and #24, which tracked the
window, is closed.

| Thing | Note |
|---|---|
| **Body part type strings** (`Chip Interface`) | Written into save state on every character that has one. Settled in #13: `Chipset Interface` → **`Chip Interface`**. |
| **Anatomy and body-object names** (`PsionicAdept`) | Settled in #13: `Yttrian` → **`PsionicAdept`**, matching the `TrueKin` convention. |
| **CoQE-original blueprint names** (`Raven_Iron Maceth`) | Was *"verified free"* before release, on the evidence that no installed mod references a `Raven_` blueprint — true, and no longer the point. Saves reference them now. The `Raven_` prefix itself stays regardless — see §1.1. |
| **Markup shader names** (`lesbian`, `agender`) | `ItemNaming.NameItem` calls `ColorUtility.ApplyColor`, which stores the literal string `{{lesbian|Whatever}}` as the item's proper name — so the shader name is *inside* the save. Rename one and every item already named with it renders differently, in saves already written. Added in #577; `validate_mod.py`'s `shader-collision` check guards the vanilla half. |

**What breaking this actually does, which is the reason it reads as a rule rather than a
preference.** Renaming or removing a blueprint that shipped does not crash and does not error where
anyone will see it. `GameObject.GetBlueprint` looks the name up, misses, logs through
`MetricsManager` and returns the generic `Object` blueprint:

```csharp
if (_BlueprintCache != null || GameObjectFactory.Factory.Blueprints.TryGetValue(Blueprint, out _BlueprintCache))
    return _BlueprintCache;
...
MetricsManager.LogError(new Exception("GameObject::GetBlueprint() Unknown Blueprint " + Blueprint));
return GameObjectFactory.Factory.Blueprints["Object"];
```

The player's object survives — its parts are serialised on the object itself, so a weapon still
swings and an arrow still fires — but every blueprint-level lookup (`GetTag`, `HasTagOrProperty`,
`IsWall`) silently answers as `Object` instead. Degraded, not broken, and invisible to whoever
caused it. The same silent-failure family as an orphaned `Load="Merge"`.

**If a shipped name genuinely has to go**, do what #201 did rather than renaming in place: comment
the old blueprint out with a note saying why and what would restore it, and give the replacement a
**new** name. Existing copies degrade rather than vanish, nothing new spawns, and the old
definition stays in the file for whoever revives it. Weigh that degradation against how long the
name has been out and how common the object is — #201 judged one day of exposure on a weight-2 drop
acceptable, which is not a general licence.

### 1.2 Coupled — renameable, but only in lockstep

Independent of release state: these travel in pairs, always.

| Thing | Update alongside |
|---|---|
| **C# class names** (`Raven_ModKindle`) | Referenced by `Name=` on `<part>` elements in the XML. Rename both or neither. |
| **Texture files** (`Textures/Subtypes/forcePsionic.png`) | Referenced from `Subtypes.xml` as `Tile="Subtypes/forcePsionic.bmp"` — note the **`.bmp` extension in XML against a `.png` on disk**. That mismatch is normal Qud convention, not a bug: the engine resolves `.bmp` tile paths against `.png` assets. |
| **C# filenames** | Keep filename == class name (standard .NET). Renaming the file means renaming the class, which means updating every `<part Name="…">` that references it. |

### 1.3 Free — rename freely

- XML filenames (`Melee Weapons.xml` → `melee-weapons.xml`)
- Directory names, except as constrained above
- Documentation filenames
- Tooling and CI filenames

### 1.4 Settled naming decisions

The slot is **"Chip Interface"** and the anatomy and body object are **`PsionicAdept`** (#13). Both
were decided rather than inherited, so here is the reasoning.

The original shipped a slot called `Chipset Interface` while all of Mura's player-facing
documentation called it the "Psionic Interface". Neither was accurate: the slot takes 108 chips
against 36 chipsets, and 13 of the 36 mutations the chips grant are *physical* rather than mental.
"Chip Interface" is true of the whole catalogue, it matches the technological fiction in the chips'
own description, and it doesn't imply the slot belongs to the Psionic Adept genotype — it's merged
into base `Humanoid`, so every humanoid has one.

`PsionicAdept` follows the convention `Genotypes.xml` already sets: the True Kin genotype
("True Kin") points at a body object and anatomy named `TrueKin`, the display name with spaces
removed.

**Use these names in all new player-facing text.** Mura's original documents in `docs/` predate the
decision and I leave them as a historical record.

---

## 2. Repository layout

The mod folder is **uploaded verbatim** to the Workshop, so anything sitting beside the mod
content reaches every subscriber. This is not theoretical — of the mods installed locally, 8 ship
a `README.md`, 5 a `LICENSE`, 4 a `.csproj`, and 2 a `.gitignore`. Nobody meant to.

Development tooling therefore lives **outside** the uploaded directory:

```
qud-expanded-community-edition/
├── mod/                          # the ONLY thing uploaded to the Workshop
│   ├── ObjectBlueprints/
│   ├── Scripting/
│   ├── Textures/Subtypes/
│   ├── *.xml
│   ├── Joppa.rpm
│   ├── manifest.json
│   ├── workshop.json
│   └── preview.png
├── docs/                         # CHARTER, FEATURES, LESSONS, PERMISSION, STYLEGUIDE, upstream notes
├── tools/                        # validation script, helpers
├── .github/workflows/            # CI
├── .pre-commit-config.yaml
├── README.md
├── CONTRIBUTING.md
└── CLAUDE.md                     # my local working notes; untracked
```

This matches the layout already used by the sibling Qud projects in this workspace
(`qud-creature-variants`, `lore-expansion`), so the whole set stays consistent.

**Rule:** if a file exists to help develop the mod rather than to run it, it does not belong in
`mod/`.

---

## 3. Naming conventions

Qud's own data files are `PascalCase.xml` (`PopulationTables.xml`, `ObjectBlueprints.xml`), and
matching vanilla makes modded files instantly legible to anyone who knows the game. **Inside
`mod/`, match vanilla. Outside `mod/`, use standard open-source conventions.**

| Artifact | Convention | Example |
|---|---|---|
| Mod XML files | `PascalCase.xml`, matching the vanilla file they correspond to | `PopulationTables.xml`, `Bodies.xml` |
| Mod XML files with no vanilla counterpart | `PascalCase.xml`, no spaces | `MeleeWeapons.xml`, `PsionicChips.xml` |
| Mod directories | `PascalCase` | `ObjectBlueprints/`, `Textures/` |
| C# files | `PascalCase.cs`, one public class per file, filename == class name | `Raven_ModKindle.cs` |
| C# classes for this fork | `Raven_` prefix retained — see §6 | `Raven_ModFrostWebs` |
| Textures | `camelCase.png`, `<affinity><Role>` | `forcePsionic.png`, `lightGuardian.png` |
| Repo-root docs | `SCREAMING_CASE.md` for top-level standards, `Title-Case.md` otherwise | `README.md`, `STYLEGUIDE.md` |
| Tooling scripts | `kebab-case` or `snake_case.py`, matching the language's norm | `validate-mod.py` |
| Branches | `type/kebab-case-description` | `fix/artifact-table-merge` |

**No filename contains a space.** The four that did — `Melee Weapons.xml`, `Other Equipment.xml`,
`Psionic Chips.xml`, `Ranged Weapons.xml` — were renamed in #23, because spaces require quoting in
every script, hook and CI step that touches them. Do not reintroduce any.

### 3.1 Blueprint naming (for new content)

New blueprints follow Mura's existing scheme, which the charter requires preserving:

- **A prefix on every new object**, and which one is a question of credit rather than of
  namespacing — see §6. `Raven_` is Mura's, and stays on everything inherited from CoQE; content
  added to this fork takes **`Vixy_`**. Never re-prefix an existing `Raven_` object: that would
  both break the attribution and spend the identifier-rename window described in §1.1b.
- `tools/validate_mod.py` enforces both through `MOD_PREFIXES`, and treats any other name as a
  vanilla record. A third prefix means updating that constant, or four of its six checks stop
  guarding in silence (#224).
- Vanilla merges use the **vanilla name** with `Load="Merge"` and **no prefix**.
- Display names are lowercase (`basic kindle chip`), matching Qud's convention.
- Tier suffixes follow vanilla's pattern where extending a vanilla family (`Battle Axe3th`), and
  read naturally where creating a new one (`Raven_Folded Carbide Halberd`).

### 3.2 Content conventions

Mura was consistent, and these tables are what make charter rule 2's "derived, not invented"
possible in practice. Match them when adding anything.

- **Blueprint prefix `Raven_` or `Vixy_`** on every new object, per §3.1 — `Raven_` on Mura's,
  `Vixy_` on this fork's. Merges into vanilla objects use the vanilla
  name with `Load="Merge"` and no prefix. **No exceptions remain:** `SteelFist` and the 18
  `Projectile*` objects were the last, renamed in #66 before the save window closed; the
  Recoilers turned out to be vanilla objects the mod was replacing, fixed in #29. The only
  unprefixed new objects left are `TrueKin` and `PsionicAdept`, which are body objects following
  vanilla's own `BodyObject` convention (#13).
- **Tier → material:** 0 bronze · 1 iron · 2 steel · 3 carbide · 4 folded carbide · 5 fullerite ·
  6 crysteel · 7 flawless crysteel · 8 zetachrome.
- **Value curve doubles per tier:** 5 · 10 · 20 · 40 · 80 · 160 · 320 · 640 · 1280. Body armor
  runs 8→2048; vambraces run 4→1024 (half curve, partial slot).
- **Chips run a quarter of that curve: `1.25 × 2^tier`** — 20 · 40 · 80 · 160 · 320 across tiers
  4–8. They are not equipment: their slot competes with nothing, and they **cannot be bought**,
  because they live in `Artifact 3`–`8` and village tinkers stock `Artifact NR`. So price only sets
  what an unwanted chip sells for, and **rarity is the access dial, not price.**
  `docs/DESIGN_balance.md` §5.3.
- **The chip system controls access and price. Vanilla controls what a mutation is worth.** A
  chip's price and its drop weight are this fork's to set; the number of ranks a grade grants is
  not. Every mutation behind a chip is a vanilla mutation Freehold already balanced, so re-tuning
  one through the chip ladder is second-guessing Qud's own mutation design by proxy.
  `docs/DESIGN_balance.md` §5.2.
- **But a cost vanilla wrote is not always a cost vanilla weighed**, and the two want opposite
  treatment. The rule above protects Freehold's *balancing*; where there is none to protect it has
  nothing to say. `HiddenMutations.xml` ships 48 mutations that are `Hidden` and `ExcludeFromPool`,
  and **nothing has ever paid one of their costs** — not a player, not a random mutant — so those
  numbers are starting figures rather than judgements. Thirty of the forty-two physical entries are
  `Cost="1"`, which is the tell.

  **The test is whether anything has ever paid it.** `Hidden`, `ExcludeFromPool` or the wiki's
  `npconly` all mean no, and a mutation this fork exposes is then costed by §10.2's two-neighbours
  method like any new content. `Heightened Smell` is the worked case: vanilla says 2, its radius is
  `5 + 4L` against `Heightened Hearing`'s `3 + 2L` at the same price, and it ships at 3 (#593).
  Whether a hidden mutation may be exposed at all is a separate two-part test in
  `docs/DESIGN_balance.md` §10.4.
- **A subtype starts with its own affinity, whatever that affinity contains** — never a *generic*
  chipset carrying someone else's steep passive. A Light Psionic opening with `PhotosyntheticSkin`
  is its affinity expressing itself and stays; a shared chipset that hands every Guardian
  `HeightenedSpeed` is an accident of kit-building. `docs/DESIGN_balance.md` §5.9.
- **Two-handed variants** get `PenBonus="1"` and a damage bump over the one-handed version, plus
  `UsesTwoSlots="true"`.
- **Two-handed hammer `Physics` weight is the one-handed weight plus 3** — inventory pounds, not a
  population table's draw weight — and the one-handed line sits below vanilla's throughout. Every
  war hammer follows it: bronze 4→7, iron 3→6, steel 3→6, carbide 5→8, folded carbide 4→7,
  fullerite 6→9, crysteel 3→6, flawless crysteel 3→6, zetachrome 3→6.
  Read the greathammers on their own and the curve looks like it wobbles: it climbs to fullerite,
  then falls to the lightest weapon in the family at the top tier. That shape is vanilla's own
  one-handed curve, compressed and carried across with a constant added, so the wobble is
  inherited rather than introduced and there is no monotonic curve here to restore. Nothing checks
  this, so check it by hand when you add a tier — #248 read the two-handed half in isolation and
  proposed bringing fullerite down from 9, which was the one value the rule required.

  **The mace family follows the same +3, and the mace line sits one pound below the war hammer line
  at every tier.** That offset is not decoration: it is the finesse tell. The mace ladder is the
  Cudgel tree's finesse pick and the war hammers are the Strength pick, and a finesse weapon is light
  for its class — so the lighter of the two families is the one carrying the tag. Maces run
  3·2·2·4·3·5·2·2·2 against war hammers at 4·3·3·5·4·6·3·3·3, and mauls 6·5·5·7·6·8·5·5·5 against
  greathammers at 7·6·6·8·7·9·6·6·6.

  Before #342 the offset pointed the other way, and the mace family broke the +3 rule at two tiers —
  fullerite was +4 and zetachrome +2. Flipping it repaired both. Every weight moved **downward**,
  which matters: `check_weight_curve` lets a merge lighten a vanilla item and never make one heavier,
  and `Mace2`, `Steel Hammer`, `Cudgel6`, `Cudgel7` and `Cudgel5th` are all vanilla.
- **`MeleeWeapon.Stat` is `Strength` on every new weapon, and a merge never changes vanilla's.**
  `Stat=` names the *penetration* stat, and the damage die is rolled once per penetration, so it
  multiplies a weapon's whole output rather than adding to it — while Agility already supplies
  melee to-hit and DV on every weapon with no exemption. Vanilla declares `MeleeWeapon` 402 times:
  191 `Strength`, 208 unset (which is Strength), 3 `Ego`, and **`Agility` never**. A weapon meant
  to reward Agility carries `<tag Name="Finesse" />` instead, and the crossover is then bought as a
  power in that weapon's own tree — never granted by the blueprint. All four melee trees sell it:
  Short Blades, Long Blades, Axe and Cudgel. `docs/DESIGN_balance.md` §3.9 has the reasoning and the
  tabletop precedent, and §3.3 has why the Axe and Cudgel powers were added later than the other two.
  The 61 blueprints that once violated this were reverted in
  [#321](https://github.com/vixygrey/qud-expanded-community-edition/issues/321); **no live
  declaration breaks it now.** Two `Stat="Agility"` vibro war hammers survive inside a commented-out
  block in `MeleeWeapons.xml` — inert, invisible to `stat-discipline`, which parses rather than
  greps, and not precedent.
- **A finesse weapon is light for its class**, and that is the whole test — not the hand count. A
  one-handed finesse weapon sits below one-handed norms for its tier, a two-handed one below
  two-handed norms. This is why the mace ladder sits a pound below the war hammers, and it is what
  licenses two-handed finesse weapons at all; Pathfinder's elven branched spear and elven curve blade
  are both two-handed and both finesse. An earlier version of this rule said finesse never coexists
  with two-handed, which was 5e's rule mistaken for the genre's. `docs/DESIGN_balance.md` §3.3.
- **A `Finesse` tag needs a matching `RulesDescription`**, and text needs a matching tag. The tag has
  no player-facing surface of its own, so a weapon carrying it and a weapon where the feature is
  silently broken look identical — which is how #366 survived a play session. `finesse-visible` in
  `tools/validate_mod.py` checks both directions.
- **Vibro weapons:** tier 5, value 300, `ChargeUse="100"`, bits `0015`,
  `Mods="AxeMods,BladeMods,WeaponMods,CommonMods,ElectronicsMods"`.
- **A tool is found at low tiers and built at high ones.** Where a line is an implement rather than a
  weapon, it stops appearing in the loot tables above the tier vanilla itself stopped at, and takes a
  `TinkerItem` instead. Nobody forges a farming tool out of crysteel, but a tinker with odd
  priorities can. The vinereaper is the case: vanilla ships it at iron and steel only, so tiers 0–2
  stay in the tables and 3–8 are tinker-only.

  **This is not a way around `unreachable`.** That check accepts "in a population table, *or*
  tinkerable", and the second half is real: `TinkerData.TinkerRecipes` scans every blueprint carrying
  a `TinkerItem`, and `DataDisk` draws from that list filtered by tier, so the recipes turn up on
  found disks gated by Tinkering rank. **Bits are `000` plus the item's own tier** — three scrap bits
  and one of its tier — which is vanilla's commonest shape at four of the six tiers this covers.

  **Never delete the high-tier blueprints instead.** §1.1b freezes them, and a save holding one
  would silently degrade to the generic `Object`.
- **Prefer `Load="Merge"`** over redeclaring a vanilla object. The Artifact tables were the one
  place this was violated; they became merges in #34, and `tools/validate_mod.py`'s
  `merge-discipline` check holds the line now. Don't add new violations for it to catch.

The tier and value curves are checked by `item-curve` in `tools/validate_mod.py`, so a mispriced or
mistagged item fails CI rather than sitting in the loot pool at the wrong rarity.

**The value curve is this fork's convention, not vanilla's.** `item-curve` prices only `Raven_` and
`Vixy_` objects, because vanilla sets its own values — and vanilla's are nowhere near a curve.
So the test for whether the curve describes a category is whether *this mod* has ever followed it
there. Measured across everything priced: melee weapons **63 of 73** on the curve and armour **50 of
62**, against **0 of 5** ranged weapons, **0 of 4** energy cells and 0 of 1 trinket. Those three are
exempt (#373) — a rule nothing has ever followed is not a rule being broken.

Exemptions are decided by **part composition** rather than a word in the name, since a name match is
the failure #354 removed from tier detection. A `MissileWeapon`, an `EnergyCell`, a `Backpack` or a
`Trinket` tag exempts; so does an `Armor` part granting **no AV**, which is a slot occupier rather
than armour. A `Food` or `PreparedCookingIngredient` part exempts too. Anything else with a price is
held to the curve.

**Food is the one exemption I declared before the category existed**, and it is worth saying why.
Every other one was written after measuring what this fork already shipped — 0 of 5 ranged weapons,
0 of 4 cells. This fork ships no priced food at all, so that test reads 0 of 0 and settles nothing.
Vanilla settles it instead: of its **32** edibles carrying both a `Tier` tag and a price, **none**
sits on the curve, at ratios from 0.006 (mopango corpse, 2 against a curve of 320) to 6.25 (black
puma haunch, 250 against 40). A thousandfold spread is the absence of a curve, not drift from one —
a saltwurm corpse and a crystal of Eve share tier 8 and nothing else. Food is priced by what eating
it does. Declaring the exemption up front is what stops the first edible this fork adds from being
silently priced against a rule that has never described anything here (#177).

**A merge keeps vanilla's value, unless it also changes the item's tier.** The curve describes this
fork's own items; imposing it on a vanilla blueprint is the same shape as the `MeleeWeapon.Stat`
swaps #321 reverted, and it reached far further — **142 of the 213 merges** carried a price the fork
had rewritten, moving the merged economy 44,476 → 33,459, about 25% cheaper. #380 reverted 80 of
them and kept the 12 where the merge re-tiers the item, because there the price follows a derived
tier rather than replacing a decision vanilla made. The remaining 50 belong to
[#334](https://github.com/vixygrey/qud-expanded-community-edition/issues/334) and
[#335](https://github.com/vixygrey/qud-expanded-community-edition/issues/335), which own the grenade
and cybernetics economies.

The measurement that settled it: vanilla's own prices are **not** the mess the exemption note above
suggests once you hold the slot fixed. Body armour runs a 1.1x spread at tier 5, 1.5x at tiers 6 and
7, and **1.1x at tier 8** — Zetachrome Lune at 6,000 sits beside the Flange from the Great Machine
at 6,666. Vanilla is coherent at the top; this fork's curve is simply a different slope, above
vanilla at tier 1 and a third of it at tier 8. There was no inconsistency to tidy.

**What that costs, stated because it is visible in play.** A family holding both new and merged
items no longer steps evenly: four pairs run a higher tier at no more price, and ten tiers hold a
fork item and a vanilla one at different prices — tier-5 boots are 160 new and 195 merged. Two of
those four are vanilla's own flat step reproduced faithfully. That unevenness is accepted; it is
what "vanilla sets its own values" looks like when the two catalogues sit in one table.

Resistances follow the same rule and have no curve at all, so a merge never states them. The two
that did — `Zetachrome Gloves` at 5/5/5/5 against vanilla's 6, `Zetachrome Lune` at 10/10/10/10
against 11 — were reverted in #380.

**An item's tier is its `Tier` tag**, and the material word in its name is only a fallback for the
objects that predate the tag. That order used to be reversed, which meant anything not named after
a metal was skipped before its price was ever compared — 144 psionic chips and 22 other items, all
carrying an explicit tier the check declined to read (#354). If you add an item whose name carries
no material, tag its tier and the curve will hold it.

#### 3.2.1 The curves: AV, damage, weight and table share

Derived from the installed game in #340, after the balance sweep found that **every number that
drifted is one this section did not mention**. The value curve and the tier→material table held
perfectly, because `item-curve` fails CI when they do not. These four had nothing holding them.

Read them as **ceilings**, not targets. Vanilla prices an item against its neighbours, not against a
grid, so an item well under a ceiling is fine and an item over one needs a reason.

**AV per slot.** No item may exceed vanilla's best *ordinary* item in its slot:

| Body | Head | Hands | Feet | Back | Arm | Face | Floating Nearby |
| ---: | ---: | ----: | ---: | ---: | --: | ---: | --------------: |
|    8 |    4 |     4 |    4 |    2 |   1 |    2 |               1 |

**Shields are the exception, and they need a ceiling per tier.** Vanilla's shield line is
AV = tier + 1 up to tier 3 and AV = tier from tier 5 — not one formula — so the ceiling is vanilla's
own value where vanilla ships a shield, extended to **8 at tier 8** because vanilla ships none there
and 5·6·7 at tiers 5·6·7 points nowhere else. **A greatshield sits one above the shield at its
tier**, which it pays for in about 3 lb and a flat −3 DV.

| tier | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
| ------------- | -: | -: | -: | -: | -: | -: | -: | -: | -: |
| shield | 2 | 2 | 3 | 4 | 5 | 5 | 6 | 7 | 8 |
| **greatshield** | 3 | 3 | 4 | 5 | 6 | 6 | 7 | 8 | **9** |

A single number for the slot would let a tier-2 greatshield pass at the tier-8 ceiling, which is why
`armor-curve` reads this table rather than one value.

Named artefacts break vanilla's own ceiling on purpose — `Flange from the Great Machine` at AV 10,
`Gear from the Great Machine` at 10, `Gigantic Chassis Plate` at 6 — and are not a benchmark this
fork may match.

**Shields carry their AV on a `Shield` part rather than an `Armor` one**, so any survey filtered on
`Armor` misses them entirely — which is how the first version of this table shipped without a Shield
column at all. They also carry the largest single AV of any ordinary item: `Flawless Crysteel Shield`
at 7 beats every body armour but one, and the tier-8 extension puts a greatshield at 9, one below
`Gear from the Great Machine`.

**Shield AV is conditional, so it is not the same currency.** It applies only to an attack the
shield blocks, and `Combat.HandleEvent(GetDefenderHitDiceEvent)` puts that at `25 * (1 +
ImprovedBlock)` percent, plus 25 for `Shield_Block` and 25 for `Shield_DeftBlocking` — 25% bare,
75% fully skilled, 100% under Shield Wall. Compare a shield against other shields, and treat any
best-in-slot total that adds it to armour AV as an upper bound rather than a figure.

**Count the slot, not the item.** A humanoid has **two** Arm slots, so Arm AV counts twice toward a
loadout. That is why Arm is the tightest cap in the table, and why vanilla puts bracelets there
rather than armour. `Bodies.xml` is the authority: Body, Head, Hands, Feet, Back and Face are one
each; Arm and Hand are two.

**Back is the one deliberate stretch.** Vanilla's ordinary cloaks are AV 1 and only the
`Sail from the Great Machine` reaches 2. This fork allows 2 at the top tiers so the weave-cloak line
has somewhere to go. Measured against vanilla's best full loadout it costs **+1 AV and nothing
else** — 26 becomes 27. That is the whole price of keeping the line, and it is why the concession
stops at cloaks: extending the same courtesy to vambraces would cost 4 more, because the slot is
worn twice.

**The Arm slot carries no DV penalty and weighs a pound.** Vanilla puts 28 armour items in that
slot and **not one** of them has negative DV — the values are 0, 1 and 2, and the median weight is 1.
The vambrace line broke both: seven of its nine imposed a penalty the slot has never had, running
−1, 0, −2, −1, 0, −3, −2, −1, 0, and they weighed 2 to 6 lb. Both columns were chosen per item, which
the weight rule above forbids in as many words. #381 flattened them to DV 0 and 1 lb. There is no Arm
row in the factor table because vanilla has nothing armoured there to derive a factor from; the slot's
own numbers are the anchor instead.

That leaves nine items separated only by price, and **that is accepted rather than owed**. The Arm
slot is for utility artifacts; the vambraces are flavour, and flavour that imposes no penalty vanilla
would not is the honest version of flavour. Vanilla ships duplicates of its own — `Steel Dagger`,
`Steel Kukri`, `Steel Utility Knife` — though at one tier rather than nine.

**A wristblade is worth about 60% of the dagger at its tier.** It attacks from the Arm slot, and
`BodyPart.ScanForWeapon` walks every part, so two arms and two hands is four attempts a round; the
Arm slot's alternative is a utility artifact, which is no contest. Vanilla is no guide here and says
so clearly: `ArmDagger4` **is** `Dagger4` — same `1d8`, same 75 water, same penetration — because
vanilla ships exactly one wristblade at one tier and never enabled the build. Nine of them is a
build, so this fork prices the attack that vanilla never had to. Means by tier: 1.0, 1.5, 1.5, 2.0,
2.5, 3.5, 4.0, 4.5, 5.0, a deficit of a third to a half at every tier the dice can express one — 0
and 1 cannot, because 40% off `1d2` has nowhere to go. #324.

**Note what that does *not* rest on.** #380's rule that a merge keeps vanilla's value is about price
and resistances, where `merged_records` can prove what vanilla said. Damage is held to a per-family
ceiling instead, deliberately, so `ArmDagger4` at `1d4` against vanilla's `1d8` is allowed by the
rules as they stand rather than in tension with them. It is the one place this fork overrides a
vanilla weapon's damage, and it is here because leaving it at parity would make the merged item 80%
better than its own tier-mates.

**Penetration bonus is 1, and vanilla has no second value for it.** Across the 28 weapons vanilla
ships that a player can equip and that carry a `PenBonus`, **every one is 1** — including `Gimeleth`
at 12,000 water and `Fist of the Ape God`, its legendary cudgels. The high numbers in the game's data
(6, 8, 10) are on creature limbs — cherubic claws, astral tabby bites — not on equipment. This fork's
own 84 declarations are all 1 as well. `Rhinox-Skull Maul` at **2** was the only exception in either
catalogue, and #333 brought it back: a named artifact may be distinctive, but not above a ceiling the
game's own legendaries respect.

**Shots per action stops at 10.** Vanilla's ceiling across 65 missile weapons is the `Swarm Rack` at
10, and its two shotguns fire 8. `Raven_Drum Shotgun` fired **24** — three times the best shotgun in
the game, at the same tier, for less money. It is 10 now, at 2 ammo, which keeps the drum's actual
trade (five shots a shell against vanilla's eight) without exceeding a ceiling vanilla sets. Note
`ShotsPerAnimation` follows `ShotsPerAction` on every vanilla burst weapon except the chaingun.

**A merge may re-tier a vanilla item when the material table says so, and the price follows the
tier.** Fourteen do. `Ironweave Cloak` is the one that demotes rather than extends — tier 4 to 1,
because iron is tier 1 — which puts a mid-game vanilla item in the opening zones so the
bronzeweave-through-zetachromeweave family has room. That is accepted (#333) and it is the exception
that #380's value rule was already written around: a merge keeps vanilla's value *unless it also
re-tiers*, and this is what that clause is for.

**An energy cell's capacity sets its rarity and its entry tier, and the two ladders run separately.**
Vanilla states the rule plainly once entry tier is read against charge: chem 10,000 enters Ammo 4 at
weight 25, nuclear 100,000 enters Ammo 6 at 5, antimatter 200,000 enters Ammo 7 at 1. Recharging
cells run their own ladder beside it, anchored by the solar cell at 2,500 and weight 10. **Nothing
with more charge may be commoner than something with less**, within either ladder. #326 found the
advanced chem cell at weight 20 — four times commoner than a nuclear cell holding twice as much.

**A solar cell recharges at 10 a turn, because that is the only rate vanilla states.** `SolarArray`
defaults to 10 and vanilla ships exactly one cell using it, so any other figure is invented. The rate
is not a free parameter: it is measured against what a shot costs. Vanilla's own ratio is a laser
pistol at 100 charge against 10 a turn — **ten turns of sunlight per shot**. #323 found the solar
nexus at 50 a turn against a psionic pistol at 50 a shot, which is one shot per turn, outdoors, for
ever. Capacity is what separates this fork's solar cells now, as it separates every vanilla cell.

**Vanilla's portable charge ceiling is 200,000.** The only 500,000 cell it ships is the mech power
core, at **70 lb**. A cell may hold more than an antimatter cell only by taking that weight — the
dark matter cell keeps its 500,000 and carries the 70 (#323), which makes it a power source you
install rather than one you pocket.

**A subtype's starting skills are capped at vanilla's most generous caste**, which is 7 skills and
**700 skill points** — `Priest of All Suns`. Vanilla's median is 5 and 450. A subtype may exceed the
ceiling only by what its own Intelligence penalty pays back: `Leveler.RollSP` is
`(Intelligence − 10) × 4` per level, so −6 Intelligence costs 24 a level and about 720 across a run.
That is the whole of #330's derivation — `Temporal, Support Battalion` granted 22 skills and 2,075 SP
against a stated trade of *"massively lowered Intelligence in exchange for so many skills"*, and now
grants 15 and **1,400**, which is 700 plus the 720 it pays. `Mental, Guides of the Lost` came to the
ceiling exactly at 10 and 700.

**An option offers a choice between two things somebody meant.** Where a change is documented intent
it can be optional; where it is drift, it is a defect and the option has no business carrying it. The
skill-requirements option kept three of each until #331: the Axe and Cudgel regating, `En Garde!` and
the Multiweapon thresholds are in Mura's notes and stay optional, while the Tinkering gates
(19/23/29 cut to 17/21/25), `Disassemble` made free, and `Long Blade`'s `Dueling Stance` cut from
Int 17 to 15 had no record anywhere and now track vanilla whichever way the option is set.

**A cybernetic implant is priced against vanilla's, and most of them stack.** `CyberneticsOneOnly`
is the only gate on duplicates and it is **per-blueprint** — vanilla tags 17 items with it, and the
dermal platings and insulations are not among them. `Slots="Body,Head,Back"` names three distinct
body parts, and `ImplantedEvent` does `GetStat(key).BaseValue += value` once per implant with no cap.
So any multi-slot implant's real value is **three times its printed one**, and that is the number to
price against. #335 found the fork's line at 3 x +4 AV = +12 against vanilla's 3 x +1 = +3, and
three high-grade insulations at +60 to each element against vanilla's +27.

Resistance matters more than the AV, because it is applied as `(100 - resistance) / 100` — at 100 it
multiplies to zero. A Full Psionic caster's +40 plus three insulations at +20 reached **exactly
100**. Vanilla's ceiling by the same route is 42, and the fork now sits at 47.

Two rules follow. **A merge does not change a vanilla implant's cost or effect** — the same rule
§3.2 states for value, for the same reason, and a merge left restating vanilla's numbers should be
deleted rather than kept. And **a new implant is priced on its stacked total**, not its printed one:
the fork's plating line runs +1 / +2 / +3 so the best three slots give +6, twice vanilla's ceiling
rather than four times it.

**No caste grants cybernetics license points.** Vanilla's genotype is the only source — zero
declarations across every vanilla subtype — and the nine Full Psionics granting +1 each was part of
how the resistance ceiling reached 100 (#332).

**There is no AV curve, only a ceiling.** Vanilla's tier-4 body armour runs AV 0 to 5. Two tighter
rules were tested against all 224 vanilla armour pieces and **rejected**: `AV + DV` capped per tier
is not monotone, and `AV + DV >= 0` is broken by 14 secondary-slot pieces. Do not reintroduce
either; they produce false failures.

**Damage per family, tier and handedness.** Highest **mean** damage vanilla ships, ordinary weapons
only. Mean, not the die string: `2d6+1` is 8.0.

| family         |   0 |   1 |   2 |   3 |   4 |   5 |   6 |    7 |    8 |
| -------------- | --: | --: | --: | --: | --: | --: | --: | ---: | ---: |
| Short blade 1H | 1.5 | 2.0 | 3.5 | 4.5 | 4.5 | 5.5 | 6.5 |  7.5 |  8.5 |
| Long blade 1H  | 2.0 | 2.5 | 3.5 | 4.5 | 5.5 | 6.5 | 7.0 |  8.0 |  9.0 |
| Long blade 2H  | 3.5 | 4.5 | 5.5 | 6.5 | 7.0 | 8.0 | 9.0 | 11.0 | 13.0 |
| Axe 1H         | 1.5 | 2.0 | 3.0 | 3.5 | 4.5 | 5.5 | 6.5 |  7.5 |  8.5 |
| Axe 2H         |   — |   — | 4.5 | 5.5 | 6.5 | 7.5 | 8.5 |  9.5 | 10.5 |
| Cudgel 1H      | 2.0 | 2.0 | 3.0 | 4.0 | 5.0 | 6.0 | 7.0 |  7.5 |  8.5 |
| Cudgel 2H      |   — |   — | 5.0 | 6.0 | 7.0 | 9.0 | 8.5 | 10.5 | 14.0 |

**`MaxStrengthBonus` is the tier plus one.** True of 83 of vanilla's 87 ordinary melee weapons; the
four exceptions are `Battle Axe2`, `Dagger2`, `TutorialBattleAxe` and `Obsidian Kris`. Vibro weapons
are 0 by design — `Math.Min(Bonus, MaxBonus)` means no stat bonus reaches them at all — and fists
are unbounded.

**Weight is a constant factor per slot**, applied to vanilla's own value rather than chosen per
item. Measured across the 119 merged items that carry a weight on both sides:

| slot | factor | | slot | factor |
| ---------- | ----: | --- | ----------- | ----: |
| Body | **0.44** | | melee 1H | 0.60–0.75 |
| Feet | 0.47 | | melee 2H | 0.62–0.67 |
| Hands | 0.50 | | short blades | **1.00** — see below |
| Head | 0.57 | | | |

**Two rules bind absolutely.** Every factor is below 1, so **no item may be heavier than vanilla's**
— that holds whatever the magnitudes are, and it is what the `weight-curve` check enforces. And the
factor belongs to the **slot**, not the item.

**Body armour is held to 0.44 exactly**, because it is the one slot where weight *is* the balance.
`Fullerite Plate Mail` is 160 lb in vanilla against a Strength-16 carry budget of 240 — two thirds
of everything a character can lift, and precisely what its AV 6 is priced against. It had been cut
to 36 lb, a factor of 0.23, which made the AV free. #320.

**The other slots are held to the rule rather than the number.** Their medians sit close enough that
re-deriving every weight would be churn against a convention the content mostly follows already;
what matters is that nothing gets heavier and nothing is chosen per item. The short blades were the
exception that proved it — a median of 1.00 is no compression at all, and five of them had gone
*up*, leaving a line that ran 1, 1, 2, 2, 3, 1, 1, 1 by tier against vanilla's 1, 1, 1, 1, 1, 2, 2, 2.

**Burden makes this matter more, not differently.** [#176](https://github.com/vixygrey/qud-expanded-community-edition/issues/176)
ships graded burden **off by default**, so the experience these factors are tuned against is still
vanilla's binary `Overburdened` cliff — where only the extremes count. With the gradient on, every
pound moves you toward a real penalty, which is an argument for the factors being defensible rather
than generous.

**Mod share of a vanilla loot table stops at half.** A mod entry never outweighs a comparable
vanilla entry — that already holds, and one table's entries are deliberately lighter — so share
drifted on **count** rather than weight: completing every family and both handednesses puts more
mod entries in a tier band than vanilla stocks. Where completeness tips a table past half, the fix
is a lower per-item weight on this fork's entries, never less content.

Unlike the three above, **half is a chosen number, not a derived one.** Vanilla offers no anchor for
how much of its loot pool may be someone else's, so this is a texture decision: at the low tiers
most of what a player finds should still be the game they bought.

The ceiling does not apply to a table this fork defines itself — `Raven_Chips Tier 1` through `3`
have no vanilla entry to be half of.

**One ceiling, two measures, because vanilla writes entries two ways.** A `pickone` group selects
exactly one child, weighted by `Weight`; everything else rolls each child independently at its
`Chance`, producing `Number` of it. Vanilla never mixes them — across its 4,860 pickone children
every one carries `Weight` and none carries `Chance`, and its pickeach children are the reverse — so
which measure applies is decided by the entry itself:

| entry style | measured as | check |
|---|---|---|
| carries `Weight` | summed weight | `table-share` |
| carries no `Weight` | expected quantity, `Chance ÷ 100 × Number` | `scatter-share` |

**`scatter-share` exists because the weight measure silently governed nothing for half the tables
here** (#474). Biome globals scatter, so both sides summed to zero and the check could not fail
however much was added: six merge blocks sat in it, every creature variant among them, and
`HillsZoneGlobals-Reachable` computed 0 against 100 and would have gone on passing at fifty more
entries.

**Do not try to unify the two into one number.** I tried, and it fails on the tables that already
worked: a `Load="Merge"` block carries no `Style`, because the group it merges into already has one,
so a merged entry cannot be resolved to its parent's style from this fork's XML alone. Reading every
merged entry as a scatter entry reported `Melee Weapons 5C` at 75.2% where the true share is 42.6%,
and did the same to twelve more. Splitting by "does this entry carry a `Weight`" needs no resolution
at all, because vanilla's disjointness above makes that question equivalent.

**A sub-table this fork writes is measured; one vanilla wrote is not** (#544). `<table>` references
are normally not followed — a shared sub-table belongs to whoever wrote it. But vanilla's own
overgrowth idiom *is* a sub-table (`BrightshroomPatches`, pulled into eight cave tiers by one line),
so a `Vixy_` copy of that shape would carry its entire footprint past the measure. Resolution
follows a reference only into a table this fork defines, and is opt-in so that vanilla's side of
every ratio — and the snapshot digest with it — does not move. A `Style="pickone"` group is
over-counted, since one child fires and all are summed; that pushes a share toward the ceiling
rather than under it.

#### Every scattered blueprint reads as its own thing

Two *different* blueprints sharing a display name print as one thing twice —
`You pass by a wild overgrowth and a wild overgrowth` — and `placement-hint` cannot see it, because
the engine is right that they are distinct objects. `name-collision` compares the name with colour
markup taken off, so `{{g|ivy}}` and `{{y|ivy}}` count as the collision they are. It covers
**scattered** blueprints only: projectiles, chip grades and each arrow beside its projectile share
names legitimately and are never in a cell you walk into.

#### Every scattered plant carries its own `Hint`

Share is not the only thing a scatter entry has to get right. **Whether the game refuses to put two
of the same object in one cell is decided per biome, in `ZoneTemplates.xml`** — a file this fork
never edits:

```xml
<population Table="HillsZoneGlobals" Hint="Any"></population>   <!-- deduplicates -->
<population Table="JungleZoneGlobals"></population>             <!-- does not -->
```

`ZTPopulatonNode` hands that attribute to `PlacePopulationInRegion` as its `DefaultHint`, and only a
hinted placement runs `Points.RemoveAll(l => … || l.HasObject(Blueprint))`. **The hint follows a
`<table>` reference down** — `Population.Generate(Result, Vars, Hint ?? DefaultHint)` — so a nested
table inherits from whatever named it, and a table reached by two routes is only safe if both carry
one. Without one, placement
falls back to a path filtered on `Cell.IsEmpty()` — which returns false only above `RenderLayer` 5,
and `Plant` ships at 3. The guard cannot see the plant already standing there.

> **Write `Hint="Any"` on every scattered plant, including in the biomes whose template already
> supplies it.** Three of the six harvestables were exposed and three were not, and nothing in this
> fork's own XML said which. `placement-hint` enforces it; `docs/LESSONS.md` has the full trace.

Creatures are exempt and must stay exempt: `PlaceObjectInArea` already refuses to co-locate combat
objects, and `Any` would *harm* them by dropping the fallback's `IsReachable()` test.

#### A third route, which nobody writes

`table-share` and `scatter-share` both govern entries **someone typed**. There is a third way
content reaches a player, and it has no entry at all: the game fabricates
`DynamicInheritsTable:<Base>` from every blueprint descending from `<Base>`, weights it by tier, and
a population table draws from it. **Joining is a consequence of `Inherits=`.** No tag, no table
entry, nothing in the diff.

**Measure a slice, not a pool, and weigh it rather than counting it.** Both halves of that were
wrong when the check was first written, and #494 fixed them together:

- A request names a slice — `DynamicInheritsTable:BaseShield:Tier1` and `:Tier8` are different
  tables. Vanilla asks for every tier from 1 to 8 by name, for `Tier{zonetier}` in thirty-six
  places, for three ranges like `Tier4-7`, and for three pools with no tier at all. **A substituted
  spec reaches tiers 1-8, not 0-8**: a zone is never tier 0, and an offset is clamped by
  `Tier.Constrain`. Only `{ownertier}` reaches tier 0, because it is a blueprint's tier and this
  fork's bronze line is tier 0 (#533, #537).
- **A slice holds every member of its pool**, not the ones at its own tier. What the tier changes is
  the weight: a blueprint at the requested tier weighs 10⁸ and each step away divides by ten, then
  `Role` multiplies, then a `:Weight` tag does — 200 blueprints carry one, 167 of them vanilla's. So
  the nearest tier dominates, and counting members answers a question the game never asks.

Getting this wrong understated `MeleeWeapon:Tier8` by more than thirty points, and reported two
slices as clean that were the most dominated in the pool.

**There is no ceiling here, and the level is reported rather than judged.** On the other two routes
a share is a number someone chose and can lower. Here it is a consequence of what this fork is
*for*: completing a weapon or armour family across every tier necessarily takes most of that
family's pool. `BaseShield` is nine of ten slices above half and `BaseAxe` eight of nine — a rule
that failed the build on the mod's own premise would be the wrong rule, and a ledger of forty-odd
permanent exemptions would be worse, which is the failure mode `tools/validation-baseline.json`
exists to avoid.

**A threshold was tried and retired (#529).** It sat at half, and the distribution it was drawn
across has no break in it anywhere: the shares run smoothly from 0% to 93% with the largest bucket
at the bottom. Worse, `BaseLongBlade` is **21 of 42 members** — headcount parity to the blueprint —
so where its members weigh alike the share is exactly **50.00000%**, and four sibling slices sit
within a fiftieth of a point of it. Whether those were "in breach" came down to the fourth decimal.

**And a pool's share is not one number.** The tier decides the weights, so the same content reads
very differently depending which slice is asked for:

| pool | share range across its own slices |
|---|---|
| `BaseGlove` | 2.9% – 84.3% |
| `BaseShield` | 30.7% – 93.4% |
| `BaseCloak` | 4.6% – 70.0% |

So "N of 185 slices are over half" counted tier requests while reading as a count of breaches. What
the report prints instead is a ranking — the ten most dominated slices, and **every pool at its own
worst slice**, so no pool hides behind its good tiers.

**What fails instead is drift.** `tools/inherited-pools.json` pins two things per pool, because two
different things move and they want telling apart:

- **which of this fork's blueprints the pool reaches**, which changes when an `Inherits=` changes —
  the thing no diff shows;
- **this fork's share of each slice**, rounded to whole percent, which also moves when *vanilla's*
  content moves. A Qud update adding tier-8 weapons lowers my share of that slice without a line of
  mine changing, and that is worth being told.

*(Two earlier derivations here are void and worth recording as such. The first justified a floor on
the pool's **total** size by a gap between 9 and 16 in the size distribution; there is no such gap —
it was measured over the already-over-half cells only. The second put the floor on vanilla's count
**at that tier**, and rested on "no cell has vanilla holding four, five or six" out of thirty-four
cells. Both counted members. Once slices are weighed rather than counted there are a hundred and
eighty-five of them, not thirty-four, and neither derivation survives contact with the real numbers. The
floor that remains — five vanilla blueprints in the pool — binds on nothing today and is kept only
so that a pool where vanilla ships almost nothing cannot produce a percentage that reads as
dominance.)*

#### The two levers, and which one to reach for

**`:Weight` is the fine one, and it is the one to reach for.** A
`<tag Name="<resolved table name>:Weight" Value="0.1" />` multiplies a blueprint's weight **inside
one slice and nowhere else**, after the tier delta and `Role`. Vanilla ships **167 blueprints**
carrying one, at values from 0.05 to 0.3 — `Holographic Banana Tree` is 0.2 of
`DynamicObjectsTable:BananaGrove_Plants`, a cosmetic oddity damped in the one pool where it would
otherwise crowd.

**It works on both fabricators, which is not obvious and I had it wrong once.** A pool requested
with a tier is built by `FabricateMultitierDynamicPopulationTable`, base 10⁸, where any fraction
bites. A pool requested with no tier is built by `FabricateDynamicObjectsTable`, base **1**, and
there only one case rounds away:

| on the flat path | result |
|---|---|
| no `Role`, `Value="0.2"` | `ceil(0.2)` = **1** — the one case that does nothing |
| no `Role`, `Value="3"` | 3 — commoner |
| `Role="Minion"` (×4), `Value="0.25"` | `ceil(4 × 0.25)` = 1 — a fourfold cut |
| any `Role`, **`Value="0"`** | 0 → `continue` — **excluded from that pool alone** |

The zero case is worth knowing about on its own: it is a **per-pool exclusion**, and the only one
there is. `ExcludeFromDynamicEncounters` cannot be aimed at a single pool.

Two things follow from how the game builds the key, and both cost tags:

- The key is the table name **as requested**, and `TryResolvePopulation` substitutes `{zonetier}`
  *before* `RequireTable` sees it — so `DynamicInheritsTable:BaseAnimal:Tier1:Weight` weights that
  slice and no other. Damping a pool costs **one tag per tier** you mean to damp.
- The value is a multiplier, applied last and ceilinged, so it can only ever thin a blueprint's
  weight. **`Value="0"` is not a small weight but an exclusion**: the game does
  `if (value == 0) continue`, dropping the blueprint from that one slice entirely.

The creature variants are the worked example (#524): 78 tags at `0.1` across tiers 0–2 took
`BaseAnimal` from 69.6% to 18.6% and `BaseReptile` from 65.1% to 15.7%, while leaving membership,
the explicit biome entries and the `DynamicObjectsTable:<Biome>_Creatures` village route all
untouched. Verified in game — the report says 18.6% and a hundred rolls said 21%.

**`ExcludeFromDynamicEncounters` is the coarse one, and it is sequential.** It removes a blueprint
from **every** dynamic pool at once, `DynamicObjectsTable:` included, because
`FabricateDynamicObjectsTable` and `FabricateDynamicInheritsTable` share the
`IsEligibleForDynamicEncounters` predicate. So it is only usable on content that is reachable
another way:

> **A blueprint may be excluded from the generic pools only once it has a home someone chose.**
> Excluding an item that has no explicit population entry does not lower a share, it deletes the
> item.

`Raven_Base Psionic Chip` is the worked example (#481): 144 chips, every one placed by hand in
`Raven_Chips Tier 1`–`3`, so one tag on the base took `BaseArmor:Tier8` from 96% to 0% and cost
nothing. Reach for this when a blueprint should leave the generic pools altogether; reach for
`:Weight` when it should stay and weigh less.


### 3.3 Two ways to distribute an item, and which to reach for

A new item can reach the world by an explicit entry in `mod/Core/PopulationTables.xml`, or by carrying a
`DynamicObjectsTable:X` tag. They do different jobs and this fork uses both.

**Reach for an explicit entry when you want a chosen weight in a named table.** That is what the
other 56 merged tables are, it is reviewable as a number in a diff, and `validate_mod.py` checks the
blueprint resolves. **Every new item should have one** — the tags below are additions on top, not
substitutes, and every tagged *item* in this fork also has an explicit entry.

**Creature spawning does not work this way at all, and it cost a shipped feature to learn.** The
`DynamicObjectsTable:<Biome>_Creatures` tables look like the route — 123 vanilla creature blueprints
tag themselves into sixteen of them — and they do not put a creature in a zone. Biome creatures come
from ordinary hand-written populations instead: `HillsZoneGlobals-Reachable` lists `Goat`, `Dog`,
`Boar`, `Salamander` and the rest as explicit `<object Blueprint=>` entries. **So a new creature
reaches a zone the same way a new item does: an explicit entry in `mod/Core/PopulationTables.xml`.** See
#171.

**They are not unread, though, and this section said they were.** Every biome-keyed pool is rolled
by procedural village generation — `VillageBase.cs:167` for creatures, and the `_Plants`,
`_Ingredients` and `_FarmablePlants` families beside it — deciding who lives in a village rather than
what walks a hillside. So the tag is for villagers, and the original design was expecting
wilderness. #489 later used the `_Ingredients` half deliberately, which is the same route working as
intended once pointed at the right question.

**The two things that made the wrong answer look proven are worth more than the answer** (#490).
Neither was a careless step; both are the normal way to check.

- **Grepping the data.** `Hills_Creatures` really does appear in exactly one file. The names are
  built by string concatenation at runtime — `"DynamicObjectsTable:" + region + "_Creatures"` — so
  no search of the XML can find the consumer, and the search coming back clean reads as proof.
- **Checking at runtime with the wrong wish.** `population:findblueprint` enumerates
  `PopulationManager.Populations`, which holds tables *already fabricated*. The session used to
  confirm this had generated hills, canyon and saltmarsh zones and no village, so no `*_Creatures`
  table had been built and none was listed. Absence of a table that nothing had asked for read as
  absence of a consumer.

  `population:generate:<table>#<amount>` names the table instead, which sends it through
  `RequireTable` and fabricates it on demand. **Use that one when the question is about a table.**
  `docs/LESSONS.md` carries both failures, and the second one's own trap: a misspelt pool name
  builds an empty table and reports nothing, which looks identical to a tag that did not take.

**Reach for a tag when you want the item in vanilla's specialist pool for its category** — the hatter
stocking your helmets, the legendary gunsmith stocking your guns. Six of vanilla's seventy-nine
declared pools correspond to gear this fork adds, and all six are named directly in
`PopulationTables.xml`: `Ammo`, `Guns`, `Headwear`, `EnergyCells`, `Daggers`, `Trinkets`.

There is **no declared pool at all** for boots, gloves, body armour, shields or cloaks, so for those
an explicit entry is the only route and no decision arises. `MeleeWeapons` is the exception worth
knowing: it *is* declared, and it is one of only three pools in the whole game that nothing rolls —
`HumanoidCorpses` and `Mushrooms` are the others. Tagging into it would do nothing today and might do
something after a Qud patch, which is a reason to leave it alone and a reason to know it is there.

*(An earlier draft said "only nineteen of seventy-nine are consumed anywhere". Nineteen is how many
are named in the game's XML; **seventy-six of the seventy-nine are consumed**, the other fifty-seven
from code — the biome families above, plus `AjiConch`, `FarmablePlants` and `Jungle_Creatures` as
literals. The word was "anywhere" and only the data had been searched, which is the same mistake as
the paragraph above it and was made in the same sitting. #491.)*

**A tag cannot be replaced by an explicit entry where the consumer is tiered.** Every one of these
pools is consumed in the `:Tier{n}` form — `DynamicObjectsTable:Guns:Tier{zonetier+1}` and the like —
and `PopulationManager.RequireTable` returns early when a table of that name already exists, so
declaring one replaces vanilla's whole fabricated pool instead of joining it. The tag is the only
additive way into tier-appropriate distribution.

`EnergyCells` is the one that is genuinely load-bearing rather than flavour: `EnergyCellSocket`
reads that pool, so it is what lets a cell this fork adds be found already installed in a machine.
Nothing written in `PopulationTables.xml` can express that. **Do not tidy it away.**

**An item entered in more than one tier of a table family must be anchored at its own tier at one
end of the run, and its weight must move toward that anchor.** Spanning tiers is not itself a
defect — vanilla does it freely, and `Missile 4` carries vanilla's own `Hypertractor` at tier 6.
But every span in this fork is one of two shapes, and a new one should be too:

- **A consumable anchors at its own tier and tails upward at flat weight.** `Raven_Solar Cell Array`
  (tier 4) runs `Ammo 4`–`Ammo 8` at weight 10 throughout, and `Raven_Advanced Chem Cell` (tier 5)
  runs `Ammo 5`–`Ammo 8` at 20. A cell stays useful past its tier, so finding one late is a weak
  result rather than a strong one, and flat weight says exactly that.
- **An artifact ramps upward toward its own tier.** `Raven_Advanced Hoversled` (tier 6) runs
  `Artifact 3R`–`6R` at 1, 1, 5, 10, and `Raven_Large Sphere of Negative Weight` (tier 8) runs the
  same four at 5, 10, 15, 15. The ramp is what makes an early find rare rather than impossible;
  without it a tier-8 artifact turns up at tier 3 as readily as at tier 6.

Both shapes are deliberate and neither is a defect to be tidied away. An audit that reads only the
entries furthest from their table will re-flag them, because the anchor is the entry that looks
unremarkable.

**A single entry off its own tier is vanilla's idiom rather than this fork's, and needs vanilla's
rarity with it.** `Raven_Fine-Tuned Handgun` (tier 6) sits only in `Missile 4` — no run, so no
anchor. Vanilla's `Hypertractor` does the same and carries weight 2 against neighbours at 5 and 10,
which is *allowed but rare*. The handgun matches that weight for that reason (#284, #286). Write a
span with no run and it should be the rarest thing in its table.

Nothing checks any of this.

**Whichever you use, `tools/report_dynamic_tables.py --check` runs on every commit.** A tag
inherits, so the blueprint carrying it is usually not the blueprint being distributed. `BaseArrow`
is vanilla and *did* put six of this fork's arrows in the ammunition pool, and two psionic *base*
blueprints put all eighteen psionic firearms into legendary gunsmith stock. Both were invisible
until that tool existed, #223 described the first while missing the second on the same page, and
both were corrected in #261 and #262.

Membership is now pinned in `tools/dynamic-pools.json`, so a blueprint arriving in a pool fails a
commit rather than waiting to be noticed. Run the tool without `--check` to see the route, and
`--snapshot` to accept a change deliberately. It needs the game and skips loudly without it — the
tags that decide this live on vanilla blueprints, so nothing in CI can check it (#303).

---

## 4. XML conventions

### 4.0b `<tag>` and `<stag>` are different tags

They look like a spelling variation and they are not. `XRL.World.GameObjectFactory` loads both into
the same dictionary and **renames one**:

```csharp
if (item8.Value.NodeName == "stag") { text = "Semantic" + text; ... }
gameObjectBlueprint.Tags.Add(text, value);
```

So `<stag Name="Plank" Value="thatch" />` produces the tag **`SemanticPlank`**, and
`<tag Name="Plank" Value="thatch" />` produces `Plank`. A consumer looks for exactly one of them,
and the wrong choice leaves the tag sitting on a key nothing reads — the object loads, the tag
exists, nothing happens.

**Which form is correct depends on what reads the tag, and that lives in the assembly rather than
the data.** So the rule is vanilla's own usage: write a tag the way vanilla writes that name.
`tag-form` checks it against the snapshot's `tag_forms`, and `snapshot-coverage` checks that every
name this fork writes is accounted for at all — 41 names, 38 with a recorded form and 3 cited in
`tag_forms_absent`. Four names vanilla writes both ways — `Fiber`, `Furniture`, `LightSource`,
`Scrap` — carry no opinion, and a name vanilla never uses has nothing to copy, since nothing outside
this mod can say what is right for `Vixy_CreatureVariant`.

Vanilla leans hard: 8,203 `<tag>` against 961 `<stag>`, and the `<stag>` names are categorisation —
`Contemporary`, `Historical`, `Power`, `Plank`, `Crafts`.

**Two different consumers read a `Semantic*` key, and an `<stag>` written for one reaches the other
as well** (#501).

- **Grammar.** `XRL.Language.Semantics` resolves these into the words the game writes about an
  object. `Plank`, `Fiber` and `FiberMaterial` are what a village wall's description is made of, and
  that is what the three harvestable plants carry them for.
- **Distribution.** `GameObjectFactory.FabricateDynamicSemanticTable` takes the categories out of a
  requested table name, prefixes each with `Semantic`, and builds a **population table** from every
  blueprint carrying them. `DynamicSemanticTable:` is named in vanilla's `PopulationTables.xml` and
  rolled by five zone builders — `Village`, `VillageCoda`, `VillageOutskirts`, `SultanDungeon` and
  `GirshLairMakerBase`.

So **an `<stag>` added for a grammar reason can put the object into a spawn pool**, with nothing in
the diff to show it. Before adding one, check whether the category is consumed.

**Checking that is harder than reading a list, and the list is the wrong instinct.** 24 categories
are named literally in vanilla's population tables, but six sites build the name at runtime from
village and dungeon template data — `"DynamicSemanticTable:" + text + "::" + villageTechTier` and
similar — so **the live set has no fixed size**. Treat a category vanilla uses as consumed unless
you have checked otherwise.

This fork writes five: `Fiber`, `FiberMaterial`, `Plank`, `Floating`, `Trinket`. None is among the
24 and none matches the runtime shapes, so nothing here is enrolled in a pool by accident — checked,
rather than assumed.

### 4.1 Line endings — LF

**LF everywhere**, enforced by `.gitattributes` (`* text=auto eol=lf`) so contributor platform
cannot reintroduce CRLF.

Upstream 2.2 was uniformly CRLF because Mura worked on Windows. This fork normalised it: LF is
what Qud mods actually use — a sample of the installed Workshop mods turned up no CRLF at all —
and .NET's XML parser is indifferent either way.

The obvious objection is that normalising rewrites every line and ruins the diff against the
`upstream-2.2` baseline. It doesn't, because git can suppress the noise:

```bash
git diff --ignore-cr-at-eol upstream-2.2
```

The conversion also landed as a single mechanical commit listed in `.git-blame-ignore-revs`, so
`git blame` skips it. Enable that once per clone:

```bash
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

GitHub applies the file automatically in its own blame view.

### 4.2 Formatting

| Rule | Value |
|---|---|
| Indentation | 2 spaces, **never tabs** — `Skills.xml` (4 lines) and `Throwables.xml` (12 lines) currently violate this |
| Declaration | `<?xml version="1.0" encoding="utf-8" ?>` on line 1 |
| Encoding | UTF-8 |
| Attribute quoting | Double quotes, always |
| Self-closing | Elements with no children close inline: `<part Name="Render" … />` |
| Blank lines | One blank line between logical groups of objects; none within an object |
| Line length | No hard limit — attribute-dense blueprint lines are normal and wrapping them hurts readability |

### 4.3 Attribute order

Consistent ordering makes diffs readable and scanning fast. On `<object>`:

1. `Name`
2. `Inherits`
3. `Load`

On `<part>`: `Name` first, then the rest in the order vanilla uses for that part type.

### 4.4 Escaped entities — do not touch

Qud colour codes appear as XML entities: `ColorString="&amp;y"`, `DisplayName="&amp;cvibro &amp;ybullet"`.
These must survive formatting unaltered. Any formatter or bulk edit is verified against this
before adoption.

### 4.5 Comments

- Section comments mark groups within a file: `<!-- Feet -->`
- Commented-out content **states why and when**. `ObjectBlueprints/Ammo.xml` is a ~500-line
  comment reading only "removed temporarily", with no date and no reason — see #14. Do not add
  more of these.

---

## 5. C# conventions

The `Scripting/` directory currently holds 36 one-line classes and nothing else. Standard .NET
conventions apply, plus two constraints from the charter:

- **PascalCase** types and members, `_camelCase` private fields, 4-space indent, one public class
  per file, filename == class name.
- **Parts inherit `IPart` and carry `[Serializable]`.** Keep `WantEvent` lean — it runs on every
  event fired.
- **Charter rule 5 (safety) is a hard boundary.** No file I/O outside the mod directory, no
  network, no reflection into game internals, no Harmony, no loading external assemblies. Qud mods
  run with full process privileges and `Scripting/` triggers an approval prompt for every
  subscriber — that is a trust relationship, and those limits do not move.
- **What the C# is allowed to *do* is a separate question, and it is not fixed.** The 36 inert
  `ModImprovedMutationBase<T>` subclasses used to be the ceiling; option handling, a
  character-creation module and a mutation class have each raised it since, and #498 lowered it
  again. Read rule 5 rather than assuming a limit — this line has been out of date before.
- **Where the game already does a thing in data, use the data** — a blueprint or a tag is
  Freehold's mechanism to maintain across patches, where equivalent C# is ours. **This is not a
  budget.** Where a feature needs C#, write the C#; going looking for a worse XML route to avoid it
  is not what the rule asks.

---

## 6. Attribution in the source

Charter rule 3 makes credit the one non-negotiable condition of the fork. Two mechanical
consequences:

- **The `Raven_` blueprint and class prefix stays.** It is Mura's signature in the namespace, and
  it is the attribution that every future contributor actually reads. Renaming it to something
  fork-specific would erase authorship from the code itself.
- **`manifest.json` `author` and the Workshop description both carry the full credit list** from
  `PERMISSION.md` §4, with **Noble Lark named explicitly** for the subtype sprites, as Mura asked.

---

## 7. Steam Workshop requirements

### 7.1 `workshop.json`

Uploader metadata. Observed schema across all 40 installed mods that ship one — every field below
appears in all of them:

| Field | Notes |
|---|---|
| `WorkshopId` | The published item ID. **Omit the key entirely until Steam has assigned one** — see below. A value targets *that* item, which is how a fork can accidentally publish over the original (#2). |
| `Title` | Item title |
| `Description` | **Steam BBCode**, not Markdown — `[h1]`, `[i]`, `[b]`, `[url]`, `[list]` |
| `Tags` | Comma-separated, from Qud's published tag set |
| `Visibility` | `0` public · `1` friends · `2` private |
| `ImagePath` | Relative path to the preview, normally `preview.png` |

**Before the first upload, `workshop.json` should not exist at all.** The uploader writes it: you
select the mod in *Modding Utilities → Steam Workshop Uploader*, click **Create Workshop Id for
Mod…**, and it creates the item and writes the file, containing nothing but the new id. Only then
does **Upload Content…** have somewhere to publish to.

**Never write `"WorkshopId": 0` as a placeholder.** `0` is not "no item" to the uploader — it is a
lookup for item zero, which fails as *Item not found*, with the path and id fields blank and no
offer to create anything. That cost this fork its first upload attempt (#163). Two of the installed
mods ship a `workshop.json` with **no `WorkshopId` key at all**, which is what an unpublished file
actually looks like; none of the 72 carries a zero. `workshop-target` in `tools/validate_mod.py`
rejects a placeholder now, so the trap cannot be laid again.

Once Steam has assigned an id, keep it. It is how every later upload finds the same item, and
`Title`, `Description`, `Tags`, `Visibility` and `ImagePath` are merged back in beside it.

### 7.2 `manifest.json`

Mod identity and load behaviour — present in 64 of 87 installed mods, and currently **missing
here** (#21). Lowercase keys:

```json
{
  "id": "…",
  "title": "…",
  "version": "…",
  "author": "…",
  "description": "…",
  "tags": "…",
  "previewImage": "preview.png"
}
```

`loadorder` is **deprecated as of build 210**. Use `LoadBefore` / `LoadAfter` when ordering
against another mod is genuinely required.

**`id` is effectively permanent.** It is what other mods name in their `LoadBefore` / `LoadAfter`
declarations, so changing it breaks their ordering against this mod. It is
`QudExpandedCommunityEdition` and should stay that way.

**`author` must name Mura.** Charter rule 3 in machine-readable form; the validator enforces it.

### 7.2.1 Versioning

Semantic versioning, **continuing Mura's lineage rather than resetting**. Upstream's last release
was 2.2, so this fork's first release is **2.3.0**. Restarting at 1.0.0 would present the fork as a
new mod rather than a continuation, which is both less accurate and a quieter form of taking
credit for the eleven releases that came before.

- **Patch** — defect fixes that change no player-facing behaviour beyond correcting it
- **Minor** — new content, new tables, rebalancing
- **Major** — reserved for a change that breaks saves or removes content

"Removes content" means content that *goes away*, not content that is **replaced in function**.
Settled by 2.4.0, which disabled the quill arrow and shipped the hulk honey arrow in its place:
saves still load, the shipped blueprint is commented out rather than deleted so existing copies
keep working (§1.1b), and the release adds four shells besides — so content net-grows and nothing
a player owns stops functioning. That is **minor**. Reserve major for a release that genuinely
takes something away and leaves a hole, or that breaks saves outright.

Note that "requires a new character" applies to the **first** release regardless, because
save-baked identifiers changed during the fork.

### 7.3 `preview.png`

- PNG, **under 1 MB** (Steam limit). The current file is 512×512 and 35 KB.
- **Square, and readable as a thumbnail.** Freehold recommend 512×512; the mod manager displays it
  at 128×128 and Steam's front page at up to 435×435, so it has to survive reduction. Design for the
  small view first — `tools/build_preview.py` writes a 128px proof beside the output for exactly
  that reason.
- Path declared in `workshop.json` `ImagePath` and `manifest.json` `previewImage`.
- **Original work, not Mura's logo.** Until #500 the preview composited the fork's marks onto
  `tools/preview-base.png`, which was Mura's artwork. It is now an original design in Caves of Qud's
  own eighteen fixed colours, and Mura is credited *in the image*, alongside me, in the same face and
  weight. Charter rule 3 obliges credit, not the reuse of someone else's artwork — and a fork wearing
  its own identity while naming its origin honours that better than a borrowed logo with a suffix.
- Reasoning behind the design lives in [`PREVIEW_DESIGN.md`](PREVIEW_DESIGN.md), so a later change
  inherits the intent rather than guessing at it.

### 7.4 Description content

- Lead with what the mod does, not with history.
- Carry the `PERMISSION.md` §4 credit list, Noble Lark named explicitly.
- State clearly that this is a **community fork** and link the original item (`1134036260`).
- Never carry text written by the original author as though it were the fork's own — the current
  description is Mura's pre-handoff notice asking that the mod *not* be forked (#2).
- **8000 characters, hard.** That is Steam's own limit on a published item's description, and the
  installed mods confirm where the wall is: of the 72 shipping a `workshop.json`, the longest is
  Caves of Qud Expanded's own at 7943. Nothing local complains — the JSON stays valid, Qud still
  loads the mod, and the overflow is cut on Steam's side at upload — so `workshop-description` in
  `tools/validate_mod.py` fails the build instead.
- **Leave headroom.** The description grows with every release, and BBCode markup costs characters
  a reader never sees. Keep it summary-shaped and let `CHANGELOG.md` carry the reasoning: the page
  says what changed, the repository says why.

---

## 8. Documentation

- **Markdown, LF line endings**, one sentence per line not required but lines wrapped at ~100.
- `README.md` is the entry point: what it is, credits, install, contributing.
- `FEATURES.md` is the feature reference and is expected to stay exhaustive.
- `PERMISSION.md` is a provenance record — **append, never rewrite**.
- Reference issues as `#N`, files as clickable relative paths.
- `2.2-changelog.txt` and `mura-feature-notes-wip.txt` are Mura's, kept byte-for-byte as a
  provenance record — **never edited**, not even for typos or line endings.

> **On the first person.** The documents here are written in my voice, so they say "I decided" and
> "I checked" rather than reporting decisions as though they made themselves. That is a description
> of how *I* write, not a rule for you. **Write your issues, pull requests and comments however
> comes naturally** — in your own voice, in whatever person you like. I'd rather have your
> contribution than a stylistic match, and I'll keep the docs consistent myself.

---

## 9. Commits, branches, and PRs

Defined in `CONTRIBUTING.md` — trunk-based, issue-first, atomic commits, conventional commit
messages with repo-specific scopes (`tables`, `chips`, `armor`, `melee`, `ranged`, `skills`,
`genotypes`, `bodies`, `workshop`, `scripting`, `docs`). Not duplicated here.

The one point worth repeating, because it is the most commonly skipped: **the commit body carries
the causality.** Charter rule 2 lives or dies in commit messages.

---

## 10. What enforces what

A style rule nobody checks is a preference. Everything below is enforced today — **ten checks are
required on every pull request**, and `pre-commit` runs the same ones locally so they fail in
seconds rather than after a round trip.

| Rule | Enforced by |
|---|---|
| XML and map-file well-formedness | `wellformed` in `tools/validate_mod.py` |
| `manifest.json` / `workshop.json` validity, and the upload target | `json`, `manifest`, `workshop-target` |
| The Workshop description fitting inside Steam's 8000-character limit | `workshop-description` |
| Figures and the version quoted by the Workshop description, which ships with a release | `workshop-figure`, `workshop-version` |
| Vanilla creatures swept into an `AggregateWith` slot by inheritance | `aggregate-sweep` |
| **`Load="Merge"` on vanilla records** | `merge-discipline` |
| Markup shader names not colliding with vanilla's | `shader-collision` |
| Blueprint reachability, and table entries resolving | `unreachable`, `dangling-blueprint` |
| Part names resolving to a real class in `XRL.World.Parts` | `unknown-part`, against `tools/qud-api.json` |
| Blueprint-valued part attributes naming a blueprint that exists | `dangling-blueprint-ref`, same snapshot |
| Part attributes naming a settable member of the part class | `part-attribute`, against the snapshot's `members` map |
| `<part Builder="…">` naming a class in `XRL.World.PartBuilders` | `part-builder`, against the snapshot's `part_builders` list |
| Figures the documents quote **from vanilla** | `vanilla-figure` in `tools/check_docs.py`, against the snapshot's `figures` map |
| Tier and value curve consistency | `item-curve` |
| AV against §3.2.1's ceiling, per slot and for shields | `armor-curve` |
| `MeleeWeapon.Stat` on new weapons and on merges | `stat-discipline` |
| A `Finesse` tag and its rules text implying each other | `finesse-visible` |
| Damage against §3.2.1's per-family ceiling | `damage-ceiling`, against the snapshot's `merged_records` |
| A merge never making a vanilla item heavier | `weight-curve`, same source |
| A merge keeping vanilla's value and resistances | `merge-value`, same source |
| A chip grading a mutation that cannot level | `dead-chip-grade`, against the snapshot's `non_leveling_mutations` |
| This fork's share of a vanilla loot table | `table-share`, against the snapshot's `table_weights` |
| This fork's share of a vanilla table's *scattered* content | `scatter-share`, against the snapshot's `scatter_quantities` |
| A scattered plant carrying its own placement `Hint` | `placement-hint`, against the snapshot's `template_hints` |
| No two scattered blueprints reading as the same thing | `name-collision` |
| An implant's loot table matching the licence points it costs | `implant-table-cost` |
| A skill value this fork changes being one its options restore | `skill-option-coverage`, against the snapshot's `skill_powers` |
| Every claim pattern matching something, so a reworded sentence cannot silence its check | `claim-coverage` |
| Figures quoted by the wiki, which has no version selector | `wiki-figure`, under `--wiki` only |
| Subtype tiles existing and named for their affinity | `subtype-tile` |
| C# parts referenced by XML having a class | `missing-script`, `class-filename` |
| A mutation's `Class` existing, and never being a vanilla one | `mutation-class`, `missing-script` |
| A mutation reached by name from C# existing at all | `mutation-name`, against the snapshot's `mutation_names` |
| Mutation equipment counting as reachable, since the variant picker is its route | `unreachable`, following `MutationEquipment` up `Inherits` |
| Charter rule 5's banned APIs in `mod/Scripting/` | `scripting-policy` |
| Instance fields on `[Serializable]` types, which enter every save | `serializable-shape` |
| A file under `mod/` no declared path loads | `directory-coverage`, against `manifest.json`'s `Directories` |
| A `.rpm` map patch whose identity is its file path | `map-id` |
| A subtype's starting gear table not resolving | `subtype-gear` |
| A tag name or merged table the snapshot has never seen | `snapshot-coverage`, against `tag_forms` + `tag_forms_absent` and the table sections |
| A creature variant splitting its parent's share of a table, not adding to it | `variant-density`, against the snapshot's `variant_parent_quantities` |
| Option wiring — declared but unread, or read but undeclared | `option-wiring` |
| Slider `Min` above 1, which crashes Qud's options menu (#51) | `option-slider` |
| Filenames without spaces | `filename-space` |
| Line endings | `.gitattributes` |
| XML formatting | `prettier` with `@prettier/plugin-xml`, checked in CI |
| Python lint and format for `tools/` | `ruff`, pinned to the same version `pre-commit` runs |
| Spelling | `typos`, with a Qud vocabulary allowlist |
| No committed secrets | `gitleaks` over full history, plus GitHub push protection |
| Conventional PR title, and a changelog entry | The `conventions` job in `.github/workflows/ci.yml` |
| No direct commits to `main`, linear history, squash-only merges | GitHub ruleset, plus a local `pre-commit` hook that fails first |
| Every CI job being required or deliberately not, and this section's count | `required-checks` in `tools/check_docs.py`, against `tools/required-checks.json` |

The `merge-discipline` check is the important one: it turns this fork's headline compatibility rule
into something mechanically enforced rather than remembered, and it would have caught #3 on the
commit that introduced it.

**What none of them do is read a sentence and ask whether it's still true.** Every check above
inspects a machine-readable property, which is why the documentation here has gone quietly stale
three times (#93, #96, #106) with everything green. See `docs/LESSONS.md`.

The count in this section is itself the fourth instance, and the one that shows the shape most
clearly. It said **ten** while **nine** were enforced — `Tests` ran and passed on every pull
request and was simply not in the ruleset, so a failing test suite could have merged. Six
documents carried the number and nothing counted it, because a number in prose is prose. It is
checked now (#152), and the fix has a sting worth remembering: when `Tests` was made required, the
obvious next move was to update the documented count — which would have turned a correct ten into
an incorrect eleven. The documents were only right again *because* of the fix.

### 10.1 Every check name

The table above maps **rules to enforcers**, so a check guarding something other than a style rule has
no row in it. This one is the registry: **every name any script in `tools/` can report**, so a name
you meet in a failure has somewhere to be looked up.

`check-names` holds it complete **in both directions** — a document calling something a check that no
script emits, and a script emitting a name this table does not list, are both findings. It only
checked the first until #402, so a new check could ship unlisted in silence, and fifteen had.

| Check | Emitted by | What it holds |
|---|---|---|
| `appendix-b` | `check_docs.py` | every row of FEATURES' chip appendix, against the blueprint it describes |
| `armor-curve` | `validate_mod.py` | AV against §3.2.1's ceiling, per slot and for shields |
| `bit-letters` | `validate_mod.py` | a `TinkerItem Bits` letter, which pins one bit where a digit names a level |
| `built` | `check_build_log.py` | the game's own build log says the C# compiled |
| `changelog-sections` | `check_docs.py` | no duplicate `### Added` / `### Changed` heading inside one release |
| `heading-order` | `check_docs.py` | numbered headings being unique and ascending, so a cross-reference has one reading |
| `check-names` | `check_docs.py` | this one — a documented check name exists, and an emitted one is documented |
| `class-filename` | `validate_mod.py` | a C# class living in a file named for it |
| `map-id` | `validate_mod.py` | a `.rpm` carrying an explicit `ID`, so its identity is not its path |
| `layout` | `validate_mod.py` | the named files the checks read being where they expect, so a move cannot silently disable them |
| `directory-coverage` | `validate_mod.py` | every file under `mod/` being reachable from exactly one path `manifest.json` declares, matching case |
| `conflict-markers` | `check_docs.py` | no tracked file carrying a leftover conflict marker, the diff3 `\|\|\|\|\|\|\|` included |
| `count` | `check_build_log.py` | the log covering every script the mod ships |
| `counts` | `check_docs.py` | the file and blueprint counts the documents quote |
| `damage-ceiling` | `validate_mod.py` | damage against §3.2.1's per-family ceiling |
| `dangling-blueprint` | `validate_mod.py` | a population entry naming a blueprint that exists |
| `claim-coverage` | `check_docs.py` | every claim pattern matching something, or being registered as idle |
| `dangling-blueprint-ref` | `validate_mod.py` | a blueprint-valued part attribute naming one that exists |
| `dead-chip-grade` | `validate_mod.py` | a chip grading a mutation that cannot level |
| `deployed` | `check_build_log.py` | the log belonging to the copy the game actually compiled |
| `duplicate-child` | `validate_mod.py` | one `<object>` never naming two children the same, which Qud merges rather than keeps |
| `filename-space` | `validate_mod.py` | filenames without spaces |
| `finesse-visible` | `validate_mod.py` | a `Finesse` tag and its rules text implying each other |
| `fresh` | `check_build_log.py` | the log post-dating that copy |
| `identical` | `check_build_log.py` | the working tree matching what was compiled |
| `implant-table-cost` | `validate_mod.py` | an implant's loot table matching its licence cost |
| `item-curve` | `validate_mod.py` | tier and value curve consistency |
| `item-tables` | `check_docs.py` | every figure in FEATURES' item tables, against its blueprint |
| `file-rows` | `check_docs.py` | every row of FEATURES §6.1, against a recount of the file it names |
| `json` | `validate_mod.py` | `manifest.json` and `workshop.json` parsing |
| `links` | `check_docs.py` | every relative link in the documents resolving |
| `loaded` | `check_build_log.py` | the game loading the mod rather than skipping it |
| `manifest` | `validate_mod.py` | `manifest.json` validity, and its version against the changelog |
| `merge-discipline` | `validate_mod.py` | `Load="Merge"` on vanilla records |
| `shader-collision` | `validate_mod.py` | A `<shader>`/`<solidcolor>` name that vanilla already owns, or that this fork declares twice. `Colors.xml` has no `Load` attribute — merge is the only behaviour — so `merge-discipline` cannot see it |
| `merge-value` | `validate_mod.py` | a merge keeping vanilla's value and resistances |
| `missing-script` | `validate_mod.py` | a C# part referenced by XML having a class |
| `variant-density` | `validate_mod.py` | a creature variant splitting its parent's share of a table rather than adding a second roll |
| `mutation-class` | `validate_mod.py` | a `<mutation Class=>` naming a vanilla class, which collides with vanilla's own entry |
| `mutation-name` | `validate_mod.py` | a mutation name passed to `GetMutationEntryByName` that resolves to nothing |
| `naming-amounts` | `validate_mod.py` | a new namestyle stating `Format` and every pool `Amount`, which default to silence |
| `naming-ascii` | `validate_mod.py` | syllables staying ASCII, as all 3,074 of vanilla's are |
| `naming-merge-discipline` | `validate_mod.py` | `Load="Merge"` on vanilla namestyles, and mod-prefixed names on scopes added to them |
| `naming-option-coverage` | `validate_mod.py` | the syllables the option can switch off being exactly the ones the XML adds |
| `naming-priority` | `validate_mod.py` | a combining scope sitting above 0 and below 100 |
| `option-default` | `validate_mod.py` | a Checkbox `Default` of `Yes` or `No`, and a Combo `Default` among its own `Values` |
| `option-slider` | `validate_mod.py` | slider `Min` above 1, which crashes Qud's options menu (#51) |
| `option-wiring` | `validate_mod.py` | an option declared but unread, or read but undeclared |
| `part-attribute` | `validate_mod.py` | a part attribute naming a settable member |
| `part-builder` | `validate_mod.py` | `<part Builder="…">` naming a real class |
| `preserved` | `check_docs.py` | Mura's preserved documents unedited since the fork |
| `qud-api-snapshot` | `validate_mod.py` | the API snapshot being present and carrying what a check needs |
| `required-checks` | `check_docs.py` | the documented count of required checks matching the ruleset copy |
| `scripting-policy` | `validate_mod.py` | charter rule 5's banned APIs in `mod/Scripting/` |
| `sections` | `check_docs.py` | the section headings the documents cross-reference |
| `serializable-shape` | `validate_mod.py` | instance fields on `[Serializable]` types, which enter every save |
| `snapshot-coverage` | `validate_mod.py` | everything this fork writes being something `tools/qud-api.json` has an opinion about, so a snapshot the mod has outrun fails without needing the game |
| `subtype-gear` | `validate_mod.py` | a subtype's `Gear` naming a table this fork actually defines |
| `stat-discipline` | `validate_mod.py` | `MeleeWeapon.Stat` on new weapons and on merges |
| `skill-option-coverage` | `validate_mod.py` | a skill value this fork changes being one its options restore |
| `subtype-tile` | `validate_mod.py` | subtype tiles existing and named for their affinity |
| `tag-form` | `validate_mod.py` | `<tag>` vs `<stag>` against vanilla's usage of that tag name |
| `role-form` | `validate_mod.py` | `Role` declared as a `<tag>`, the way vanilla declares it and never otherwise |
| `tinker-only` | `validate_mod.py` | a blueprint whose only route to a player is tinkering, so its drop rate was never chosen |
| `table-share` | `validate_mod.py` | this fork's share of a vanilla loot table |
| `scatter-share` | `validate_mod.py` | this fork's share of a vanilla table's scattered content |
| `placement-hint` | `validate_mod.py` | a scattered plant carrying its own `Hint`, so two cannot share a cell |
| `name-collision` | `validate_mod.py` | two scattered blueprints that read as the same thing |
| `inherits-share` | `report_dynamic_tables.py` | this fork's share of an inherited pool, per tier (needs the game) |
| `unknown-mutation` | `validate_mod.py` | `ModImprovedMutationBase<T>` naming a mutation the game grants |
| `unknown-part` | `validate_mod.py` | part names resolving to a real class |
| `unreachable` | `validate_mod.py` | blueprint reachability |
| `vanilla-figure` | `check_docs.py` | figures the documents quote from vanilla |
| `weight-curve` | `validate_mod.py` | a merge never making a vanilla item heavier |
| `wellformed` | `validate_mod.py` | XML and map-file well-formedness |
| `wiki-figure` | `check_docs.py` | every figure the wiki quotes, against the mod it describes |
| `wiki-link` | `check_docs.py` | the wiki anchors the documents point at |
| `aggregate-sweep` | `validate_mod.py` | vanilla descendants folded into an `AggregateWith` slot this fork merges |
| `workshop-description` | `validate_mod.py` | the Workshop description fitting Steam's 8000-character limit |
| `workshop-figure` | `check_docs.py` | every figure the Workshop description quotes, against the mod it describes |
| `workshop-version` | `check_docs.py` | the version in the Workshop description, against `manifest.json` |
| `workshop-target` | `validate_mod.py` | the upload target |

`qud-api-snapshot` is the odd one out: several checks emit it when `tools/qud-api.json` is missing or
has lost a list they need, so it is a shared failure mode rather than a check of its own. It is listed
anyway, because a contributor who meets it still needs somewhere to look it up.

### 10.2 Where checking stops

Worth stating, so the boundary is not rediscovered by someone building the wrong tool.

**Checkable, and now checked:** figures quoted from the game. A number copied out of Freehold's
data is mechanical, and `vanilla-figure` holds every one of them to its source (#159).

**Not checkable:** claims about how the game *behaves*. "Resistance does not apply on this branch."
"Only `TurretTinker` and `PlaceTurretGoal` raise that event." Both were wrong in #147, both were
about control flow, and both were caught by deploying a turret and looking. Grepping decompiled
source for a pattern would produce a check harder to trust than the sentence it guards. **Do not
build that.**

**Should not be checked:** design rationale. "Cold has no gradient, so halving moderates nothing"
is a judgment, not a fact. Mechanising it would pad the check until it stops meaning anything —
the failure `.typos.toml`'s own policy warns about.

What actually catches the second and third kinds is an acceptance criterion that requires
**running the game**. #144 carried one and it earned its place twice: once finding the cryo arrow
too weak, once finding that turrets deploy empty. That habit is the lever. The tooling above is
worth having because quoted numbers are genuinely mechanical — not because it closes the gap.
