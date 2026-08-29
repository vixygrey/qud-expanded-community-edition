# Creature Variants — design doc

**Status:** v0.2 built and validated. **Pure XML — no C#, no script-approval prompt.**
**Target:** Caves of Qud 2.0.211.x
**Last verified against:** shipped `ObjectBlueprints/Creatures.xml` (1,379 blueprints)

---

## 1. How spawning actually works

Creatures self-register into spawn tables with a tag. `PopulationTables.xml` is never
touched.

```xml
<object Name="Dog" Inherits="BaseDog">
  <part Name="Render" DisplayName="feral dog" Tile="creatures/sw_dog.bmp"
        RenderString="d" ColorString="&amp;y" />
  <tag Name="DynamicObjectsTable:DesertCanyon_Creatures" />
  <tag Name="DynamicObjectsTable:Hills_Creatures" />
  <tag Name="DynamicObjectsTable:Mountains_Creatures" />
  <tag Name="DynamicObjectsTable:Flowerfields_Creatures" />
</object>
```

### 1.1 Rarity IS controllable — this was the blocking open question in v0.1

A paired `:Weight` tag sets how often the entry is drawn:

```xml
<tag Name="DynamicObjectsTable:Hills_Creatures" />
<tag Name="DynamicObjectsTable:Hills_Creatures:Weight" Value="0.5" />
```

Measured across `Creatures.xml`: **191 creature-table tags, of which only 10 (5%) carry an
explicit `:Weight`.** Vanilla values seen: `0.05, 0.1, 0.2, 0.3, 3`. The other 95% omit it,
so the implicit default is the baseline (1).

Confirmed examples:

| Blueprint | Tag | Weight |
|---|---|---|
| Issachari Raider | `Saltdunes_Creatures` | 3 |
| Astral Tabby | `BaroqueRuins_Creatures` | 0.2 |
| Ixlthyxl | `LakeHinnom_Creatures` | 0.1 |

This is what makes "some coats rarer than others" expressible, and it is also what keeps
variants from swamping a table — see §3.

### 1.2 Related tag forms

- `DynamicObjectsTable:<Table>:Number` — `Value="1-2"`, group size (Snapjaws uses it)
- `DynamicObjectsTable:<Table>` with `Value="{{{remove}}}"` — **removes** an inherited table
  entry. `Quartz Baboon` uses this to drop out of the Baboons troupe. Use this if a variant
  should replace its parent rather than join it.

### 1.3 The table-name gotcha

Most tables are `<Biome>_Creatures`. **Some are not.** Troupe tables have no suffix:

```
DynamicObjectsTable:Baboons        <- 4 entries, referenced 6x from PopulationTables.xml
DynamicObjectsTable:Snapjaws       <- 8 entries
DynamicObjectsTable:Goatfolk       <- 5 entries
```

Emitting `Baboons_Creatures` silently creates a **new table nothing draws from**, and the
variant never spawns. There is no error — it just never appears. `build_creatures.py`
now validates every emitted table name against the set vanilla actually defines.

---

## 2. Vanilla table sizes — measured

These are small, which is the whole reason weights matter.

| Table | Entries | | Table | Entries |
|---|---|---|---|---|
| Ruins | 25 | | Saltmarsh | 8 |
| Jungle | 24 | | LakeHinnom | 8 |
| DesertCanyon | 19 | | Water | 6 |
| Hills | 17 | | Saltdunes | 6 |
| PalladiumReef | 15 | | Mountains | **5** |
| BaroqueRuins | 14 | | Goatfolk | 5 |
| Flowerfields | 13 | | Baboons | 4 |
| MoonStair | 11 | | | |
| DeepJungle | 11 | | | |

**Mountains has five entries.** Adding four unweighted dog variants there would nearly
double the table. At weight 0.25 each they add 1.0 — one extra vanilla-weight slot.

---

## 3. v0.2 — what shipped

32 variants across 13 base creatures. Rarity tiers:

| Tier | Weight | Count | Rationale |
|---|---|---|---|
| common | 0.5 | 14 | ordinary coats — brindle, dun, russet, mottled |
| uncommon | 0.25 | 13 | piebald, silverback, banded |
| rare | 0.08 | 5 | albino and melanistic — pale boar, black goat, pale croc |

Spawn-table pressure, capped at 20% of the vanilla entry count:

```
Mountains        5  +3  +0.83   17%
Saltmarsh        8  +3  +1.08   14%
Hills           17  +6  +2.25   13%
DesertCanyon    19  +6  +2.08   11%
Flowerfields    13  +3  +1.25   10%
Water            6  +3  +0.41    7%
Jungle          24  +3  +1.50    6%
Baboons          4  +1  +0.25    6%
Saltdunes        6  +1  +0.25    4%
Ruins           25  +2  +0.50    2%
BaroqueRuins    14  +1  +0.25    2%
```

### 3.1 Regional theming is semantic, not budget-driven

v0.1 assigned one biome per variant to cap table inflation. That was an accounting decision
dressed up as a design one. v0.2 assigns by **what that coat would be doing in that terrain**:

- **feral dog** — brindle in hills, rangy in the desert canyon, ash-coated in mountains,
  pied in flowerfields, and a rare **marsh dog** in the saltmarsh
- **goat** — cragged on mountains, dun in hills, rare black goat on mountains
- **croc** — silt croc in the marsh, rare pale croc in open water
- **salamander** — marbled in jungle, ashen in the desert canyon
- **chameleon** — mottled in jungle, sand in the desert canyon

Weights now do the load-limiting, so theming is free to mean something.

### 3.2 Naming register — 55 / 35 / 10

Vanilla's base dog is already **"feral dog"**, not "dog", so plain-modifier + plain-noun is
an established pattern being extended, not fought.

- **Plain descriptive** — brindle, pied, dun, russet, mottled, banded, marbled, silverback
- **Condition / behaviour** — mangy, rangy, scarred, bristleback
- **Qud-ish** — salt-crusted, verdigris, ash-coated, rust-furred, ember, glass

The failure mode is making every variant exotic. If all of them are "chrome / glass-eyed /
salt-crusted", exotic becomes the baseline and stops signifying.

### 3.3 Roaches reuse vanilla art

`MiddenRoach`, `RustRoach`, `SaltRoach` inherit `Giant Beetle` and reuse
`Creatures/sw_beetle.bmp`. No new tile. Note the parent is **level 10 with 15 HP**, so these
read as goat-sized roaches, not vermin — named accordingly rather than calling one
"cockroach" and having it hit like a tenth-level insect.

---

## 4. The one rule that keeps this cosmetic

> **A variant may differ in name, colour and flavour text. It must not differ in stats.**

The moment "vampire bat" drains life, this stops being a texture mod and becomes a balance
mod, and every variant needs testing at every tier it spawns in. It also breaks player
expectation unfairly: two identically-sized glyphs behaving differently with nothing but
colour to warn you reads as a bug when it kills you.

`build_creatures.py` enforces this — it fails the build if any variant carries a `<stat>`.

---

## 5. Colour palette

Real hex from `StreamingAssets/Base/Display.txt`:

| Code | Hex | | Code | Hex |
|---|---|---|---|---|
| `r` | a64a2e rust | | `w` | 98875f brown |
| `R` | d74200 red | | `W` | cfc041 gold |
| `g` | 009403 green | | `k` | 0f3b3a near-black |
| `G` | 00c420 bright green | | `K` | 155352 dark teal |
| `b` | 0048bd dark blue | | `y` | b1c9c3 pale grey |
| `B` | 0096ff azure | | `Y` | FFFFFF white |
| `c` | 40a4b9 teal | | `o` | f15f22 orange |
| `C` | 77bfcf cyan | | `O` | e99f10 amber |
| `m` | b154cf purple | | | |
| `M` | da5bd6 magenta | | | |

Camera background is `0F252B` — preview renders should use it, since a colour that reads on
white can vanish against the game's dark field.

**Watch `&g`.** At 009403 it is a saturated green that reads as alien on a mammal — the marsh
dog was changed to `&K`. It looks right on the croc and chameleon.

`ColorString` sets the glyph, `TileColor` the sprite body, `DetailColor` the sprite's second
colour. Vanilla also colours the display name: `DisplayName="{{K|black jell}}"`.

---

## 6. Validation the build script performs

- XML parses; no duplicate blueprint names
- Every `Inherits` target exists in `Creatures.xml`
- **Every emitted table name exists in vanilla** (the Baboons gotcha)
- Exactly one spawn tag + one matching `:Weight` tag per variant
- Valid colour codes on `ColorString`, `TileColor`, `DetailColor`
- Zero `<stat>` elements
- Per-biome weight pressure within the 20% cap

---

## 7. File layout

```
qud-creature-variants/
├── build_creatures.py          # generator + validator
└── QudCreatureVariants/
    ├── manifest.json
    └── ObjectBlueprints.xml    # root <objects>, one <object> per variant
```

No scripts directory in the mod itself, therefore **no mod-approval prompt**.

---

## 8. Still open

- **Live weight semantics.** Weights are read from vanilla usage and the 5%/95% split; the
  exact normalisation (does weight 0.5 mean half as likely as an unweighted entry, or half a
  share of some total?) is inferred, not verified. Install and walk Joppa → hills → mountains
  and see whether variants feel roughly one-in-three of their base.
- Whether `DynamicObjectsTable` membership can be conditioned on zone tier.
- Whether corpse blueprints should be per-variant (probably not — inherit).
