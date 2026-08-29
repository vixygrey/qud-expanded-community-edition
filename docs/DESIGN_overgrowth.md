# Overgrowth Overhaul — design doc

**Status:** spec, no code written
**Target:** Caves of Qud 2.0.211.x
**Scope discipline:** decoration and theming **only**. No new mechanics.

---

## 0. What this is, and what it deliberately is not

The Workshop [Overgrowth](https://steamcommunity.com/sharedfiles/filedetails/?id=3596464527)
mod bundles atmosphere with systems — biomorphosis cocoons that reshape your cells, sap
farming, metaembryos granting permanent HP, poison humus, clearing thickets for skill points.
The atmosphere is the good part. The systems are opinions.

This mod is a **clean-room rebuild of the atmosphere alone**, written from scratch. No code,
assets or data are taken from that mod, which also settles the licensing question — it states
no licence, so a stripped-down republish of it wouldn't be ours to ship.

**The rule that keeps this mod honest:**

> If a change would alter a number the player can act on, it does not belong here.

No HP, no skill points, no resources, no status effects, no new hostiles. Overgrowth may
block movement — that is unavoidable for a physical object — but it grants nothing and costs
nothing beyond a turn spent clearing it.

---

## 1. How decoration actually gets into a zone

Verified against `Assembly-CSharp.dll` and `Worlds.xml`.

### The builder contract is tiny

```csharp
public class MyBuilder            // XRL.World.ZoneBuilders convention
{
    public bool BuildZone(Zone Z);                  // the whole contract
    public void Save(SerializationWriter Writer);   // builders are serialised
    public void Load(SerializationReader Reader);
}
```

`XRL.World.ZoneBuilders.Watervine` is the closest vanilla analogue and the right template —
a noise-driven vegetation scatterer:

```
Watervine
  fields:  WatervineNoise · int MaxWidth · int MaxHeight · bool Underground
  method:  bool BuildZone(Zone Z)
```

Public fields on a builder are settable **as XML attributes** — `Underground="true"` in
`Worlds.xml` sets the `Underground` field. So tuning knobs are free.

### `ZoneBuilderSandbox` gives you the hard parts

```
sampleSimplexNoise      ← organic patch shapes, not uniform scatter
EnsureCellReachable     ← THE critical one, see §3
GetTerrainObject / GetTerrain
PopulationOr
GetSeedValue            ← deterministic per-zone RNG
```

### Two ways to attach a builder — take the second

**Declarative.** `Worlds.xml` (root `<worlds>`) nests
`<cell ApplyTo="TerrainX"> → <zone Level=… Name=…> → <builder Class="Watervine" .../>`.
A mod could merge in additional `<builder>` entries.

**Programmatic — recommended.** `XRL.World.ZoneManager` exposes:

```
AddZoneBuilder            (six overloads)
AddZonePreBuilder
AddZoneBuilderOverride
ZoneHasBuilder
GetBuildersFor / CountBuildersFor
```

Register overgrowth at game start and inject it into zones **matching criteria you evaluate
yourself**, without editing `Worlds.xml` at all.

Why this is better for this mod specifically:

- **No XML merge conflict** with any other worldgen mod. The single most common way
  environment mods break each other is both editing the same cell blocks.
- **`ZoneHasBuilder` lets you detect theme from what's already there.** A zone that already
  ran `Mountains` or `JungleRuins` tells you what it is more reliably than string-matching a
  zone name.
- Trivially toggleable behind a mod option, because it's one registration call.

Vanilla vegetation builders worth reading first: `Watervine`, `Stillvine`, `Flowerfields`,
`FungalJungle`, `JungleRuins`, `FractiPlanter`.

---

## 2. The overlap bug, and why it happens

Your complaint — wood drawing over overgrowth in the same tile — is a **render layer**
collision. `XRL.World.Parts.Render` carries:

```
int    RenderLayer          ← draw order within a cell
int    Flags
int    RENDER_FLAG_OCCLUDING
string Tile · TileColor · DetailColor · ColorString · RenderString
```

Two objects in one cell both draw; the one with the higher `RenderLayer` wins, and if either
sets `RENDER_FLAG_OCCLUDING` it suppresses what's beneath.

Three fixes, in order of preference:

1. **Don't co-occupy.** When placing, skip cells that already hold a solid object. Cheapest,
   and usually correct — a thicket growing *through* a log is not what you wanted anyway.
2. **Assign an explicit `RenderLayer`** below structural objects so overgrowth reads as
   ground cover and never hides a wall, door or item.
3. **Combined blueprints** for cases where you *do* want both — one object whose tile depicts
   overgrown wood, rather than two objects stacked.

Pick one convention and apply it to every blueprint in the mod. Mixed conventions are how
this bug reappears later.

---

## 3. The failure mode to design against

Decoration mods brick runs by **sealing cells**. Overgrowth is a physical object; scatter
enough of it with noise and you will eventually generate a zone where the stairs, a quest
NPC, or the only exit sits behind an impassable clump — and the player may not be carrying
anything that clears it.

Non-negotiable guards:

- [ ] Call `EnsureCellReachable` (or verify connectivity yourself) **after** placement, and
      carve back if a required cell became unreachable.
- [ ] Never place on stairs, doors, or a cell holding an item or creature.
- [ ] Hard cap coverage per zone — suggest **≤ 25%** of open floor.
- [ ] Skip zones flagged as settlements, historic sites, or anything with a `MapBuilder`
      preset. Handcrafted maps should stay handcrafted.
- [ ] Make it always clearable by the most basic means available, with no tool requirement.

That checklist is most of the QA for this mod.

---

## 4. Theming

The world map's biome vocabulary, taken from `QudHistoryFactory`'s worldmap constants:

`Saltdunes · Saltmarsh · DesertCanyon · Jungle · DeepJungle · Hills · Water · BananaGrove ·
Fungal · LakeHinnom · PalladiumReef · Mountains · Flowerfields · Ruins · BaroqueRuins ·
MoonStair`

Theming means **each biome gets its own overgrowth vocabulary**, not one green sprite tinted
differently. Rough starting assignment:

| Biome | Overgrowth reads as | Palette |
|---|---|---|
| Jungle / DeepJungle | dense vine curtains, buttress roots | deep greens, wet browns |
| Hills / Mountains | scrub, lichen, creeper on rock | greys, sage, ochre |
| Saltmarsh | reeds, brackish weed | pale green, salt white |
| Saltdunes | almost none — dead stalks only | bleached tan |
| Fungal | mycelial mats, shelf growth | violet, sickly yellow |
| Ruins / BaroqueRuins | ivy over masonry, root-split floors | green over grey |
| BananaGrove | broad leaves, fallen fronds | bright green, yellow |
| Flowerfields | flowering creeper | saturated mixed |

**Salt dunes getting almost nothing is a deliberate design statement.** Restraint in the
hostile biomes is what makes the jungle feel dense by contrast, and it costs no work.

---

## 5. Sprites

Every tile is 16×24, black / white / transparent — the same constraint as the CYF work, and
the same pipeline applies. `qud_cyf_sprites_PARKED.zip` contains a grid editor that authors
sprites as ASCII and validates dimensions and palette on build; point it at a new set and it
works unchanged.

Two things carry over directly:

- **Detached pixels read as noise.** Vegetation is the exact case where this bites — scattered
  single pixels look like dirt on the screen, not leaves. Keep strands connected.
- **Vegetation is naturally a lattice.** The strand finding from the beastkin work applies
  here even more cleanly than it did to animals: vines, reeds and creepers *are* thin
  connected structures. Target an edge-to-area ratio near 1.5 and they'll read as organic
  rather than blobby. The measurement harness is in `build7.py`.

Estimate ~4–6 tiles per biome family, ~20–30 total for full coverage. Fewer if biomes share.

---

## 6. File layout

```
QudOvergrowth/
├── manifest.json
├── OvergrowthOptions.xml           # density, per-biome toggles, master off
├── ObjectBlueprints.xml            # the overgrowth objects; explicit RenderLayer on each
├── Textures/                       # 16x24 tiles
└── Scripts/
    ├── OvergrowthBuilder.cs        # BuildZone + Save/Load, noise-driven placement
    ├── OvergrowthRegistrar.cs      # ZoneManager.AddZoneBuilder at game start
    ├── BiomeTheme.cs               # biome -> blueprint set + palette
    └── Options.cs                  # [OptionFlag] fields
```

No Harmony. Confirmed Tier 2 at worst — a C# builder plus XML data — so it is fully
developable and testable on macOS (`recon-findings.md` §Q0).

---

## 7. Build order

1. **One biome, one sprite, hardcoded placement.** Jungle, one vine tile, fixed 10% density.
   Prove the builder registers and draws.
2. **Add the reachability guard (§3) immediately** — before adding any more content. It will
   change how placement works, so retrofitting it later means redoing the placement code.
3. Swap fixed density for `sampleSimplexNoise` patches.
4. Resolve the render-layer convention (§2) and apply it to every blueprint.
5. Expand to the biome table, one family at a time.
6. Mod options: master toggle, global density slider, per-biome checkboxes.

Steps 1–2 are the real spike. If a jungle zone generates with vines and you can still always
reach the stairs, everything after that is content.

---

## 8. Open questions

- Whether `AddZoneBuilder` can be called usefully at game start for zones not yet generated,
  or whether registration must happen per-zone via `BeforeZoneBuiltEvent`. Both exist;
  **`BeforeZoneBuiltEvent` is the safer assumption** and is a plain `MinEvent`.
- How `MapBuilder` preset zones report themselves, for the skip rule in §3.
- Whether `EnsureCellReachable` operates on the whole zone or a supplied cell pair.

All three are answerable by reading `Watervine.BuildZone` and one `ZoneManager.AddZoneBuilder`
overload in ILSpy — the same decompile pass that's already outstanding for `lore-expansion`, a
private sibling project of mine.

---

## Sources

- `Assembly-CSharp.dll` metadata, read with my own tooling in `lore-expansion` (a private sibling
  project, not in this repository)
- `StreamingAssets/Base/Worlds.xml`, `ZoneTemplates.xml`
- [Overgrowth on the Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3596464527)
  — referenced for scope contrast only; nothing derived from it
