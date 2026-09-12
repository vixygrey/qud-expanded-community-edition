# The official modding wiki, indexed

Every question that this fork re-derives from game files has an official wiki page.
This index lists the 53 pages in the modding navbox.
It states what each page settles and identifies corrections that this repository already made.

**This index does not reproduce wiki content.**
The wiki uses CC BY-NC-SA.
Its non-commercial clause does not align with this repository's licenses.
See `COPYING.md`.
This file contains links, page titles, section names, and one-line descriptions.
Read each source page at its link.

The wiki is a secondary source.
The decompiled assembly takes precedence when the sources disagree.
[`docs/LESSONS.md`](LESSONS.md) records those disagreements.
The wiki often provides the fastest route to the relevant type.

## Where to look first

| Question | Page |
|---|---|
| Why did my `Load="Merge"` not merge? | [XML](https://wiki.cavesofqud.com/wiki/Modding:XML): load strategies |
| What puts an object into the world? | [Populations](https://wiki.cavesofqud.com/wiki/Modding:Populations): read *Dynamic Tables* twice |
| Does the engine read this tag? | [Objects](https://wiki.cavesofqud.com/wiki/Modding:Objects): supported tags |
| What is `<stag>` for? | [Grammar](https://wiki.cavesofqud.com/wiki/Modding:Grammar): semantic terms |
| Which random function can I call? | [Randomness](https://wiki.cavesofqud.com/wiki/Modding:Randomness): never `Random.Next()` |
| Will this option be read? | [Options](https://wiki.cavesofqud.com/wiki/Modding:Options): both directions fail silently |
| Why did my save stop loading? | [Serialization](<https://wiki.cavesofqud.com/wiki/Modding:Serialization_(Saving/Loading)>): migration section |
| How do I avoid breaking other mods? | [Compatibility](https://wiki.cavesofqud.com/wiki/Modding:Compatibility): prefixing, merging, named arguments |
| Where does a zone's content come from? | [Zone Builders](https://wiki.cavesofqud.com/wiki/Modding:Zone_Builders) |
| What color codes exist? | [Colors & Object Rendering](https://wiki.cavesofqud.com/wiki/Modding:Colors_%26_Object_Rendering) |
| Where else can a tag come from? | [Objects](https://wiki.cavesofqud.com/wiki/Modding:Objects): `<mixin>`, which `Inherits=` alone cannot find (#526) |
| How do I test this without playing? | [Wishes](https://wiki.cavesofqud.com/wiki/Modding:Wishes): full player-facing list |

## Core Concepts

| Page | What it settles |
|---|---|
| [Overview](https://wiki.cavesofqud.com/wiki/Modding:Overview) | File structure, what a mod may do, the incompatible-mod flag |
| [XML](https://wiki.cavesofqud.com/wiki/Modding:XML) | Syntax, how data loads, **load strategies**, debugging |
| [Objects](https://wiki.cavesofqud.com/wiki/Modding:Objects) | Blueprint definitions, the component system, supported tags, the part catalogue, and **`<mixin>` with `Include` / `Exclude` / `Priority` / `Load="Fill"`** |
| [Parts](https://wiki.cavesofqud.com/wiki/Modding:Parts) | What a part is and the kinds there are |
| [Active Parts](https://wiki.cavesofqud.com/wiki/Modding:Active_Parts) | `IActivePart` statuses, `IsReady()`, `IPoweredPart`, and XML configuration points |
| [Events](https://wiki.cavesofqud.com/wiki/Modding:Events) | String events and MinEvents, including listening, firing, handling, and cascading |
| [Effects](https://wiki.cavesofqud.com/wiki/Modding:Effects) | `GetEffectType()` as a bit vector, and the masking that follows from it |
| [Populations](https://wiki.cavesofqud.com/wiki/Modding:Populations) | Encounter vs population tables, **`DynamicObjectsTable` / `DynamicInheritsTable` / `DynamicSemanticTable`**, excluding objects, debugging |
| [Grammar](https://wiki.cavesofqud.com/wiki/Modding:Grammar) | Term format, pronouns, and verbs. The semantic layer receives `<stag>` terms. |
| [Turns, Segments, and Actions](https://wiki.cavesofqud.com/wiki/Modding:Turns,_Segments,_and_Actions) | `ActionManager.RunSegment`, the action queue, action cost |
| [Scripting](https://wiki.cavesofqud.com/wiki/Modding:Scripting) | C# 9, runtime compilation, getting the source, dev environment |
| [Wishes](https://wiki.cavesofqud.com/wiki/Modding:Wishes) | Declaring your own commands with `[WishCommand]` and `[HasWishCommand]` |
| [Polish](https://wiki.cavesofqud.com/wiki/Modding:Polish) | The pre-publish checklist: articles, zoom levels, both UIs |

## Creatures and Objects

| Page | What it settles |
|---|---|
| [Creature AI](https://wiki.cavesofqud.com/wiki/Modding:Creature_AI) | What `Brain` exposes to XML alone, the AI part catalogue, goal handlers, opinions and allegiances |
| [Mutations](https://wiki.cavesofqud.com/wiki/Modding:Mutations) | `Mutations.xml` parameters, including cost, `MaxSelected`, exclusions, and `BearerDescription` |
| [Activated Abilities](https://wiki.cavesofqud.com/wiki/Modding:Activated_Abilities) | Registering and activating, from any part |
| [Bodies](https://wiki.cavesofqud.com/wiki/Modding:Bodies) | `Bodies.xml`, part types and variants, anatomies |
| [StatShifter](https://wiki.cavesofqud.com/wiki/Modding:StatShifter) | The bookkeeping API for temporary stat changes |
| [Conversations](https://wiki.cavesofqud.com/wiki/Modding:Conversations) | The XML tree, merging, inheritance, delegates, parts and events |
| [Giving Creatures Inventory Items](https://wiki.cavesofqud.com/wiki/Modding:Giving_Creatures_Inventory_Items) | Preset vs random inventory, and the legacy forms |
| [Inventory Actions](https://wiki.cavesofqud.com/wiki/Modding:Inventory_Actions) | Adding a verb to the twiddle menu |
| [Missile Weapons](https://wiki.cavesofqud.com/wiki/Modding:Missile_Weapons) | `AmmoGeneric`, specialised ammo under one generic, scripted impact effects |
| [Tiles](https://wiki.cavesofqud.com/wiki/Modding:Tiles) | Formats, the palette, the 4th colour, painted tiles, `PaintWith`, filepath construction |
| [Pets](https://wiki.cavesofqud.com/wiki/Modding:Pets) | A custom pet in XML alone |
| [Vehicles](https://wiki.cavesofqud.com/wiki/Modding:Vehicles) | A redirect into *Interior Zones* |

## Zones and Worlds

| Page | What it settles |
|---|---|
| [Intro - Zones and Worlds](https://wiki.cavesofqud.com/wiki/Modding:Intro_-_Zones_and_Worlds) | The vocabulary. Start here before the other four pages. |
| [Zone Builders](https://wiki.cavesofqud.com/wiki/Modding:Zone_Builders) | The pre-existing builders, `ZoneBuilderSandbox`, `PlacePopulationInRegion`, pathfinding |
| [Zone Procedural Generation](https://wiki.cavesofqud.com/wiki/Modding:Zone_Procedural_Generation) | FastNoise, NoiseMap, wave function collapse |
| [Interior Zones](https://wiki.cavesofqud.com/wiki/Modding:Interior_Zones) | Zones attached to objects, vehicles, interior weights, and the limits |
| [Maps](https://wiki.cavesofqud.com/wiki/Modding:Maps) | `.rpm` format, patching a shipped map, and the map editor. It also explains `mod/Optional/JoppaBuilding/Joppa.rpm`. |
| [Worlds](https://wiki.cavesofqud.com/wiki/Modding:Worlds) | `JoppaWorldBuilderExtension`, worldgen patterns, building a world of your own |

## Miscellanea

| Page | What it settles |
|---|---|
| [Options](https://wiki.cavesofqud.com/wiki/Modding:Options) | The XML structure, option types, `[OptionFlag]`, `Options.GetOption`, requirement specs, **enabling and disabling XML from an option** |
| [Randomness](https://wiki.cavesofqud.com/wiki/Modding:Randomness) | The `Stat.cs` generators and their uses: `Rnd`, `SeededRandom`, `GaussianRandom`, and `RandomCosmetic` |
| [Serialization (Saving/Loading)](<https://wiki.cavesofqud.com/wiki/Modding:Serialization_(Saving/Loading)>) | How Qud saves, custom serialization, and **migrating between mod versions** |
| [Adding Code at Startup](https://wiki.cavesofqud.com/wiki/Modding:Adding_Code_at_Startup) | The four cache points and their timing |
| [Adding Code to the Player](https://wiki.cavesofqud.com/wiki/Modding:Adding_Code_to_the_Player) | `[PlayerMutator]` / `IPlayerMutator`, on new game and on load |
| [Genotypes and Subtypes](https://wiki.cavesofqud.com/wiki/Modding:Genotypes_and_Subtypes) | A genotype in XML. The worked snapjaw example covers all four files. |
| [Quests](https://wiki.cavesofqud.com/wiki/Modding:Quests) | `Quests.xml`, `IQuestSystem`, giving and completing steps in XML or script |
| [Liquids](https://wiki.cavesofqud.com/wiki/Modding:Liquids) | `BaseLiquid` plus the `IsLiquid` attribute |
| [Key Mapping (Commands)](<https://wiki.cavesofqud.com/wiki/Modding:Key_Mapping_(Commands)>) | Custom entries in the Key Mapping menu |
| [Sounds](https://wiki.cavesofqud.com/wiki/Modding:Sounds) | The `/sounds` folder, supported types, the recognised tag names |
| [Harmony](https://wiki.cavesofqud.com/wiki/Modding:Harmony) | Runtime patching. **Charter rule 5 forbids this here.** Read the page for other people's mods. |

## Resources

| Page | What it settles |
|---|---|
| [Mod Configuration](https://wiki.cavesofqud.com/wiki/Modding:Mod_Configuration) | `manifest.json`, `workshop.json`, `modconfig.json`, and `config.json`. The page covers structure and version ranges. |
| [Creating a Workshop Mod](https://wiki.cavesofqud.com/wiki/Modding:Creating_a_Workshop_Mod) | Publishing, and the `workshop.json` fields |
| [Compatibility](https://wiki.cavesofqud.com/wiki/Modding:Compatibility) | Prefixing, merging, named arguments, and save migration. These practices support this fork. |
| [Installing a mod](https://wiki.cavesofqud.com/wiki/Modding:Installing_a_mod) | Every install route, for writing release instructions |
| [Colors & Object Rendering](https://wiki.cavesofqud.com/wiki/Modding:Colors_%26_Object_Rendering) | The colour letters, the markup language, colour templates, custom colours |
| [Code page 437](https://wiki.cavesofqud.com/wiki/Modding:Code_page_437) | The escape table and rendering behavior. XML is safe because the reader reverses the map. `docs/LESSONS.md` records the asymmetry. |
| [Visual Style](https://wiki.cavesofqud.com/wiki/Visual_Style) | The palette itself, in several formats, plus the font and graphics conventions |
| [Tutorial - Snapjaw Mages](https://wiki.cavesofqud.com/wiki/Modding:Tutorial_-_Snapjaw_Mages) | A worked tutorial for creatures, tiles, inventory, skills, and stats |
| [Histographicnomicon](https://wiki.cavesofqud.com/wiki/Modding:Histographicnomicon) | The sultan-history generator in the mod toolkit |
| [Tutorial - Custom Player Tiles](https://wiki.cavesofqud.com/wiki/Modding:Tutorial_-_Custom_Player_Tiles) | Player tile presets, build codes |

## Where the wiki and the assembly disagree

The wiki contains older pages.
The assembly takes precedence when a page disagrees with current game behavior.
This section records checks against the decompiled assembly.
It prevents repeated investigation.

**`<tag Value="*delete">` is not broken, in either of the two ways the wiki says it is.**
[Objects](https://wiki.cavesofqud.com/wiki/Modding:Objects) says it "appears to currently be broken
because it does not work in combination with `Load="Merge"` or on inherited tags". Both halves fail
against the assembly:

- **On inherited tags.** `GameObjectFactory.Bake` skips any tag whose `Value` contains `*delete`
  while baking a blueprint's flattened node tree, so an inherited tag does not survive. This fork
  relies on that in seven blueprints, and #171 confirmed it by measuring pool membership before and
  after.
- **With `Load="Merge"`.** `ObjectBlueprintXMLChildNode.Merge` copies incoming attributes over existing
  attributes with `Attributes[attribute.Key] = attribute.Value`.
  Merging `<tag Name="X" Value="*delete" />` therefore sets `Value` on the target node.
  `Bake` then skips the tag.
  This repository has no `*delete` merge to demonstrate.
  A `population:generate` check can support a future upstream correction (#504).

**`<stag>` provides more than grammar terms.**
The wiki describes it as a dynamic semantic table.
`docs/STYLEGUIDE.md` §4.0b describes it as the semantic-term layer.
Both descriptions are incomplete.
`Bake` stores `<stag Name="X">` as `SemanticX`.
`XRL.Language.Semantics` reads that key for grammar.
`FabricateDynamicSemanticTable` also reads it and builds a population table.
An `<stag>` can therefore place an object in a spawn pool.
Vanilla names 24 semantic categories in population tables.
Six more sites build names at runtime from village and dungeon data.
The consumed set has no fixed size.
None of the five categories declared by this fork matches those sets.

**Dynamic tables come in six kinds, not three.**
[Populations](https://wiki.cavesofqud.com/wiki/Modding:Populations) documents `DynamicObjectsTable`,
`DynamicInheritsTable` and `DynamicSemanticTable`. `PopulationManager.RequireTable` also dispatches
`StaticObjectsTable:`, `DynamicArtifactsTable:` and `DynamicHasPartTable:`, the last of which takes a
`:Tier` slice the same way the documented ones do.

**A parasang's X coordinate increases from the left.**
[Intro - Zones and Worlds](https://wiki.cavesofqud.com/wiki/Modding:Intro_-_Zones_and_Worlds) sets
the top-left parasang to (0, 0) and the bottom-right parasang to (79, 24).
The page later describes `JoppaWorld.53.3.1.1.10` as the 53rd tile from the right.
Those statements conflict.

The assembly uses the left-origin interpretation.
`WorldFactory.BuildZoneNameMap` walks parasang X from 0 to 79 and Y from 0 to 24.
`Zone` converts back with
`Location2D.Get(ParasangX * 3 + ZoneX, ParasangY * 3 + ZoneY)`.
Map X grows rightward from the top-left origin.

The example is `79 - 53 = 26` parasangs from the intended position.
A `goto:` wish or landing zone based on it lands 26 parasangs away on an 80-parasang map.
The remaining page content is sound.
The coordinate definition, `World.wX.wY.X.Y.Z` format, 0–2 zone coordinates, and `Z = 10` surface stratum remain useful.

**This contradiction exists within the page.**
It does not depend on a Qud version.
Offer the one-word correction upstream.

## Refreshing this index

The navbox is category-driven.
A page joins it when the page receives a category.
List the five categories to find additions:

```bash
for c in "Modding - Core Concepts" "Modding - Creatures and Objects" "Zones and Worlds" "Modding - Miscellanea" "Modding Resources"; do echo "== $c"; curl -s -A "Mozilla/5.0" --get --data-urlencode "cmtitle=Category:$c" --data "action=query&list=categorymembers&cmlimit=500&format=json" https://wiki.cavesofqud.com/api.php | python3 -c 'import json,sys;[print("  ",m["title"]) for m in json.load(sys.stdin)["query"]["categorymembers"]]'; done
```

This command has two traps.
The wiki returns **403 for an unrecognized user agent**.
The browser user agent is required.
The rendered navbox filters to the `Modding:` namespace.
It therefore hides `Visual Style` and `Wishes`.
The API returns both pages.
The sidebar does not.
Do not treat the sidebar as the complete list.
