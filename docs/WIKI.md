# The official modding wiki, indexed

Every question this fork keeps re-deriving from the game files has a page on the official wiki, and
I kept not knowing that. This is the index I wish I had had: the 53 pages the modding navbox carries,
what each one actually settles, and which of them answer questions this repo has already got wrong
once.

**Nothing from the wiki is reproduced here.** Its content is CC BY-NC-SA, and the non-commercial
clause does not sit comfortably beside this repository's own licences — see `COPYING.md`. So this
file holds links, page titles, section names and my own one-line descriptions, and stops there. Read
the page at the link.

The wiki is a secondary source. Where it disagrees with the decompiled assembly, the assembly wins
and `docs/LESSONS.md` records why — but the wiki is very often the faster way to find out *which*
type to go and read.

## Where I would look first

| The question I keep asking | Page |
|---|---|
| Why did my `Load="Merge"` not merge? | [XML](https://wiki.cavesofqud.com/wiki/Modding:XML) — load strategies |
| What puts an object into the world? | [Populations](https://wiki.cavesofqud.com/wiki/Modding:Populations) — and read *Dynamic Tables* twice |
| Does the engine read this tag? | [Objects](https://wiki.cavesofqud.com/wiki/Modding:Objects) — the supported-tag list |
| What is `<stag>` for? | [Grammar](https://wiki.cavesofqud.com/wiki/Modding:Grammar) — semantic terms |
| Which random function may I call? | [Randomness](https://wiki.cavesofqud.com/wiki/Modding:Randomness) — never `Random.Next()` |
| Will this option actually be read? | [Options](https://wiki.cavesofqud.com/wiki/Modding:Options) — both directions fail silently |
| Why did my save stop loading? | [Serialization](<https://wiki.cavesofqud.com/wiki/Modding:Serialization_(Saving/Loading)>) — and its migration section |
| How do I not break other mods? | [Compatibility](https://wiki.cavesofqud.com/wiki/Modding:Compatibility) — prefixing, merging, named arguments |
| Where does a zone's content come from? | [Zone Builders](https://wiki.cavesofqud.com/wiki/Modding:Zone_Builders) |
| What colour codes exist? | [Colors & Object Rendering](https://wiki.cavesofqud.com/wiki/Modding:Colors_%26_Object_Rendering) |
| How do I test this without playing to it? | [Wishes](https://wiki.cavesofqud.com/wiki/Wishes) — the full player-facing list |

## Core Concepts

| Page | What it settles |
|---|---|
| [Overview](https://wiki.cavesofqud.com/wiki/Modding:Overview) | File structure, what a mod may do, the incompatible-mod flag |
| [XML](https://wiki.cavesofqud.com/wiki/Modding:XML) | Syntax, how data loads, **load strategies**, debugging |
| [Objects](https://wiki.cavesofqud.com/wiki/Modding:Objects) | Blueprint definitions, the component system, the supported tag list, and the part catalogue by category |
| [Parts](https://wiki.cavesofqud.com/wiki/Modding:Parts) | What a part is and the kinds there are |
| [Active Parts](https://wiki.cavesofqud.com/wiki/Modding:Active_Parts) | `IActivePart` — statuses, `IsReady()`, `IPoweredPart`, and the configuration points that reconfigure all of it from XML |
| [Events](https://wiki.cavesofqud.com/wiki/Modding:Events) | String events and MinEvents — listening, firing, handling, cascading |
| [Effects](https://wiki.cavesofqud.com/wiki/Modding:Effects) | `GetEffectType()` as a bit vector, and the masking that follows from it |
| [Populations](https://wiki.cavesofqud.com/wiki/Modding:Populations) | Encounter vs population tables, **`DynamicObjectsTable` / `DynamicInheritsTable` / `DynamicSemanticTable`**, excluding objects, debugging |
| [Grammar](https://wiki.cavesofqud.com/wiki/Modding:Grammar) | Term format, pronouns, verbs — the semantic layer `<stag>` feeds |
| [Turns, Segments, and Actions](https://wiki.cavesofqud.com/wiki/Modding:Turns,_Segments,_and_Actions) | `ActionManager.RunSegment`, the action queue, action cost |
| [Scripting](https://wiki.cavesofqud.com/wiki/Modding:Scripting) | C# 9, runtime compilation, getting the source, dev environment |
| [Wishes](https://wiki.cavesofqud.com/wiki/Modding:Wishes) | Declaring your own — `[WishCommand]` and `[HasWishCommand]` |
| [Polish](https://wiki.cavesofqud.com/wiki/Modding:Polish) | The pre-publish checklist: articles, zoom levels, both UIs |

## Creatures and Objects

| Page | What it settles |
|---|---|
| [Creature AI](https://wiki.cavesofqud.com/wiki/Modding:Creature_AI) | What `Brain` exposes to XML alone, the AI part catalogue, goal handlers, opinions and allegiances |
| [Mutations](https://wiki.cavesofqud.com/wiki/Modding:Mutations) | `Mutations.xml` parameters — cost, `MaxSelected`, exclusions, `BearerDescription` |
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
| [Intro - Zones and Worlds](https://wiki.cavesofqud.com/wiki/Modding:Intro_-_Zones_and_Worlds) | The vocabulary — start here before the other four |
| [Zone Builders](https://wiki.cavesofqud.com/wiki/Modding:Zone_Builders) | The pre-existing builders, `ZoneBuilderSandbox`, `PlacePopulationInRegion`, pathfinding |
| [Zone Procedural Generation](https://wiki.cavesofqud.com/wiki/Modding:Zone_Procedural_Generation) | FastNoise, NoiseMap, wave function collapse |
| [Interior Zones](https://wiki.cavesofqud.com/wiki/Modding:Interior_Zones) | Zones attached to objects, vehicles, interior weights, and the limits |
| [Maps](https://wiki.cavesofqud.com/wiki/Modding:Maps) | `.rpm` format, patching a shipped map, the map editor — what `mod/Joppa.rpm` is |
| [Worlds](https://wiki.cavesofqud.com/wiki/Modding:Worlds) | `JoppaWorldBuilderExtension`, worldgen patterns, building a world of your own |

## Miscellanea

| Page | What it settles |
|---|---|
| [Options](https://wiki.cavesofqud.com/wiki/Modding:Options) | The XML structure, option types, `[OptionFlag]`, `Options.GetOption`, requirement specs, **enabling and disabling XML from an option** |
| [Randomness](https://wiki.cavesofqud.com/wiki/Modding:Randomness) | The `Stat.cs` generators and which to use — `Rnd`, `SeededRandom`, `GaussianRandom`, `RandomCosmetic` |
| [Serialization (Saving/Loading)](<https://wiki.cavesofqud.com/wiki/Modding:Serialization_(Saving/Loading)>) | How Qud saves, custom serialization, and **migrating between mod versions** |
| [Adding Code at Startup](https://wiki.cavesofqud.com/wiki/Modding:Adding_Code_at_Startup) | The four cache points and their timing |
| [Adding Code to the Player](https://wiki.cavesofqud.com/wiki/Modding:Adding_Code_to_the_Player) | `[PlayerMutator]` / `IPlayerMutator`, on new game and on load |
| [Genotypes and Subtypes](https://wiki.cavesofqud.com/wiki/Modding:Genotypes_and_Subtypes) | A whole genotype in XML — the worked snapjaw example covers all four files |
| [Quests](https://wiki.cavesofqud.com/wiki/Modding:Quests) | `Quests.xml`, `IQuestSystem`, giving and completing steps in XML or script |
| [Liquids](https://wiki.cavesofqud.com/wiki/Modding:Liquids) | `BaseLiquid` plus the `IsLiquid` attribute |
| [Key Mapping (Commands)](<https://wiki.cavesofqud.com/wiki/Modding:Key_Mapping_(Commands)>) | Custom entries in the Key Mapping menu |
| [Sounds](https://wiki.cavesofqud.com/wiki/Modding:Sounds) | The `/sounds` folder, supported types, the recognised tag names |
| [Harmony](https://wiki.cavesofqud.com/wiki/Modding:Harmony) | Runtime patching. **Charter rule 5 forbids this here** — the page is for reading other people's mods |

## Resources

| Page | What it settles |
|---|---|
| [Mod Configuration](https://wiki.cavesofqud.com/wiki/Modding:Mod_Configuration) | `manifest.json`, `workshop.json`, `modconfig.json`, `config.json` — structure and version ranges |
| [Creating a Workshop Mod](https://wiki.cavesofqud.com/wiki/Modding:Creating_a_Workshop_Mod) | Publishing, and the `workshop.json` fields |
| [Compatibility](https://wiki.cavesofqud.com/wiki/Modding:Compatibility) | Prefixing, merging, named arguments, save migration — the practices this fork is built on |
| [Installing a mod](https://wiki.cavesofqud.com/wiki/Modding:Installing_a_mod) | Every install route, for writing release instructions |
| [Colors & Object Rendering](https://wiki.cavesofqud.com/wiki/Modding:Colors_%26_Object_Rendering) | The colour letters, the markup language, colour templates, custom colours |
| [Code page 437](https://wiki.cavesofqud.com/wiki/Modding:Code_page_437) | The escape table and how it renders — what `RenderString` takes |
| [Visual Style](https://wiki.cavesofqud.com/wiki/Visual_Style) | The palette itself, in several formats, plus the font and graphics conventions |
| [Wishes](https://wiki.cavesofqud.com/wiki/Wishes) | The player-facing wish list — the testing tool, as opposed to the modding page above |
| [Histographicnomicon](https://wiki.cavesofqud.com/wiki/Modding:Histographicnomicon) | The sultan-history generator in the mod toolkit |
| [Tutorial - Snapjaw Mages](https://wiki.cavesofqud.com/wiki/Modding:Tutorial_-_Snapjaw_Mages) | The long worked tutorial — creature, tiles, inventory, skills, stats |
| [Tutorial - Custom Player Tiles](https://wiki.cavesofqud.com/wiki/Modding:Tutorial_-_Custom_Player_Tiles) | Player tile presets, build codes |

## Where the wiki and the assembly disagree

The wiki is written by people, some of it years ago, and I have found places where the game has
moved on. These are the ones I have checked against the decompiled assembly myself. The assembly
wins; the wiki entry is noted so nobody re-derives the same correction.

**`<tag Value="*delete">` is not broken.** [Objects](https://wiki.cavesofqud.com/wiki/Modding:Objects)
says it "appears to currently be broken because it does not work in combination with `Load="Merge"`
or on inherited tags". `GameObjectFactory.Bake` skips any tag whose `Value` contains `*delete` while
baking a blueprint's flattened node tree, so an inherited tag genuinely does not survive. This fork
relies on that in seven blueprints and it works. I have not tested the `Load="Merge"` half of the
claim, so treat that half as open.

**`<stag>` is not only a grammar mechanism.** The same page describes it as adding an object to a
dynamic semantic table; `docs/STYLEGUIDE.md` §4.0b describes it as the semantic-term layer. Both are
right and neither is complete: `Bake` stores `<stag Name="X">` as the single tag `SemanticX`, and
*two* different consumers read that key — `XRL.Language.Semantics` for grammar, and
`FabricateDynamicSemanticTable`, which prefixes each requested category with `Semantic` and builds a
population table from everything carrying it. So an `<stag>` can put an object into a spawn pool.
Twenty-four semantic categories are named in vanilla's population tables — `Furniture` and
`ElectricalPowerConsumer` among them — and six more sites build the name at runtime from village and
dungeon data, so the consumed set has no fixed size. None of the five this fork declares is among the
twenty-four, and none matches the runtime shapes either.

**Dynamic tables come in six kinds, not three.**
[Populations](https://wiki.cavesofqud.com/wiki/Modding:Populations) documents `DynamicObjectsTable`,
`DynamicInheritsTable` and `DynamicSemanticTable`. `PopulationManager.RequireTable` also dispatches
`StaticObjectsTable:`, `DynamicArtifactsTable:` and `DynamicHasPartTable:`, the last of which takes a
`:Tier` slice the same way the documented ones do.

## Refreshing this index

The navbox is category-driven rather than hand-written, so a page joins it the moment it is
categorised. To see what has been added since I wrote this, list the five categories:

```bash
for c in "Modding - Core Concepts" "Modding - Creatures and Objects" "Zones and Worlds" "Modding - Miscellanea" "Modding Resources"; do echo "== $c"; curl -s -A "Mozilla/5.0" --get --data-urlencode "cmtitle=Category:$c" --data "action=query&list=categorymembers&cmlimit=500&format=json" https://wiki.cavesofqud.com/api.php | python3 -c 'import json,sys;[print("  ",m["title"]) for m in json.load(sys.stdin)["query"]["categorymembers"]]'; done
```

Two traps in that command, both of which cost me a detour. The wiki returns **403 to an unrecognised
user agent**, so the browser UA is not decoration — `WebFetch` and a bare `curl` both bounce. And the
*rendered* navbox filters to the `Modding:` namespace, which hides two pages the categories really do
contain: `Visual Style` and `Wishes`. The API sees both; the sidebar does not. Reading the sidebar
and calling it the whole list is the same mistake as reading the XML and calling it the whole game.
