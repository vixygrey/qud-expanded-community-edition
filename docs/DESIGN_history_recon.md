# Recon Findings

**Date:** 2026-08-14
**Build inspected:** local macOS install, `CoQ.app` (Steam)
**Method:** shipped data files read directly; assembly metadata read from the `#Strings` heap
of `Assembly-CSharp.dll`.

> **Method caveat.** No decompiler was available in the analysis sandbox — PyPI, the Ubuntu
> archive, and the .NET SDK are all unreachable from it, so ILSpy / `monodis` / `dnfile`
> could not be installed. Everything below about **data** is direct observation and is
> reliable. Everything about **code** is inferred from type and method names in assembly
> metadata, which tells us what exists but not what it does. Questions needing method bodies
> are marked **NEEDS DECOMPILE** and should be finished with ILSpy on the Windows machine.
>
> **UPDATE 2026-08-15 — a full metadata-table pass has since been done.** See
> `DESIGN_history_recon_addendum.md`. It answers **Q9, Q2, Q7**, upgrades **Q5**, sharpens **Q3**,
> and **corrects the SimpleJSON claim in §Q8 below** (the tree is Newtonsoft, not SimpleJSON)
> and the perspective claim in **N3**. Sections superseded by it are flagged inline.

---

## Headline

Three findings change the plan materially:

1. **The prose is data, not code.** All history and naming text lives in a shipped
   183 KB JSON grammar. This was the largest open risk in the project and it has landed on
   the good side.
2. **The era vocabulary is token substitution.** Q4 resolved favourably — **authoring cost
   for the whole project halves.**
3. **The vocabulary is not small — it's ~280 adjectives and ~488 nouns.** "Add more words"
   is now definitively refuted as a fix, and the derivation thesis is correspondingly
   strengthened.

Plus one unwelcome one: **the Mac build is a universal binary with a native arm64 slice**,
which is the bad case for Harmony rather than the Rosetta case the docs hoped for.

---

## Q0 — Harmony viability · **PARTIALLY ANSWERED, LEANS BAD**

```
CoQ.app/Contents/MacOS/CoQ: Mach-O universal binary with 2 architectures:
  [x86_64] [arm64]
```

`0Harmony.dll` **is** bundled in `Data/Managed/`, confirming Harmony ships with the game.
`MonoBleedingEdge` is present, so this is a Mono runtime — not IL2CPP — and runtime patching
is architecturally possible.

But the binary is **universal with a native arm64 slice**, so on Apple Silicon it launches
natively as arm64 by default. That is exactly the configuration in Harmony issue #424
(`mprotect returned EACCES` in MonoMod's POSIX detour layer), not the Rosetta configuration
AppleGamingWiki described. **Treat the AppleGamingWiki note as wrong or outdated for this
build.**

**Actionable:** this is forceable. Get Info on `CoQ.app` → *Open using Rosetta*, or a Steam
launch option, will run the x86_64 slice — where Harmony uses its well-trodden x64 detour
path. If that works, the Mac becomes a viable Harmony test environment and the two-machine
workflow (`DESIGN_history_implementation.md` §8.7) becomes optional.

**Still needs the live test:** launch with a known Harmony-using Workshop mod, native and
under Rosetta, and check the log for patch application. That is the one thing here I cannot
do from the sandbox.

---

## Q1 — Where does the text live? · **ANSWERED: DATA**

`StreamingAssets/Base/HistorySpice.json` — 183,051 bytes, 51 top-level categories.

It is a **recursive substitution grammar**. Terminals are plain strings; non-terminals are
dot-path references with a selection operator:

```
<spice.itemTypes.*itemType*.!random>
<spice.elements.*element*.adjectives.!random>
<^.materials.!random>                      # ^ = relative to current node
*personNounPossessive*                     # * * = variable bound by the caller
```

So there are three distinct mechanisms: **path references**, **relative references**, and
**caller-bound variables**. That last one is the seam the naming design needs (see Q2).

Adjacent data files, all shipped and readable: `Naming.xml` (169 KB — the prefix/infix/suffix
person-name system that *Sultan's Names of Qud* extends), `Relics.xml` (3.9 KB — relic type
taxonomy and noun→type mappings), `PopulationTables.xml`, `Conversations.xml`, `Books.xml`,
`Worlds.xml`.

**The event *logic* is C#.** Assembly metadata shows two namespaces:

- `HistoryKit` — the generic engine: `History`, `HistoricEntity`, `HistoricEntityList`,
  `HistoricEntitySnapshot`, `HistoricEvent`, `CreatedHistoricEvent`, `HistoricPerspective`,
  `HistoricSpice`, `HistoricStringExpander`, plus `FuzzyFunctions`, `If`, `Switch`.
- `XRL.Annals` — Qud's concrete events and `QudHistoryFactory`.

> Note: `DESIGN_history_implementation.md` earlier "corrected" HistoryKit to `XRL.Annals`. Both exist —
> HistoryKit is the engine, XRL.Annals is the Qud content layer. The original guess was
> right and the correction was wrong.

### The actual event pool

From assembly metadata, `XRL.Annals` event classes:

**Sultan life (~24):** `BornAsHeir` · `FoundAsBabe` · `Adopted` · `InitializeSultan` ·
`Abdicate` · `BattleItem` · `BloodyBattle` · `CapturedByBandits` · `ChallengeSultan` ·
`ChariotDrivesOffCliff` · `CorruptAdministrator` · `FakedDeath` · `ForgeItem` · `FoundGuild` ·
`GenericDeath` · `InspiringExperience` · `LiberateCity` · `DiscoveredLocation` ·
`LoseItemAtTavern` · `Marry` · `MeetFaction` · `RampageRegion` · `SecretRitual` ·
`UnderWeirdSky` · `LocationConstructed`

**Village (12):** `InitializeVillage` · `Abandoned` · `BecomesKnownFor` · `Despises` ·
`Worships` · `CodaDespises` · `CodaWorships` · `ImportedFoodorDrink` · `NewGovernment` ·
`PopulationInflux` · `SharedMutation` · `VillageProverb`

**Resheph (16, fixed):** the scripted sixth-sultan sequence.

This corroborates the wiki's "17 core types" and the diagnosis in `DESIGN_history.md` §2.1.

---

## Q2 — Is there a naming seam? · **ANSWERED** (addendum §Q2)

`spice.history.relics.names` — the **entire relic naming grammar**, eight forms:

| # | Form | Grounded? |
|---|---|---|
| 1 | `the <itemTypes.*itemType*> of the <adjectives.!random> <elements.*element*.nouns>` | partial |
| 2 | `the <itemTypes.*itemType*> of the <elements.*element*.adjectives> <nouns.!random>` | partial |
| 3 | `the <itemTypes.*itemType*> of the <adjectives.!random> <elements.*element*.professions>` | partial |
| 4 | `*personNounPossessive* <elements.*element*.adjectives> <itemTypes.*itemType*>` | partial |
| 5 | `*creatureNamePossessive* <elements.*element*.adjectives> <itemTypes.*itemType*>` | partial |
| 6 | `*creatureNamePossessive* <itemTypes.*itemType*>` | partial |
| 7 | `<nouns.!random>-<nouns.!random>` | **none** |
| 8 | `<adjectives.!random> <nouns.!random>` | **none** |

**This is the complaint, located exactly.** Forms 7 and 8 are pure random assembly with no
connection to anything — two random nouns hyphenated, or a random adjective plus a random
noun. One in four relics gets a name generated this way.

The other six ground on `*itemType*`, `*element*`, and the owner's name — **but never on an
event.** That is the precise gap `DESIGN_history_naming.md` predicted: the name references *what kind of
thing it is* and *whose thematic domain it belongs to*, never *what happened*.

**The good news is the `*variable*` mechanism.** The caller already binds `*itemType*`,
`*element*`, `*creatureName*`, `*personNoun*` at expansion time — so a binding channel from
generator to grammar demonstrably exists. The remaining question is what else can be pushed
through it.

**ANSWERED 2026-08-15.** `ExpandQuery(string, HistoricEntitySnapshot, History,
Dictionary<string,string> vars, Dictionary<string,JToken> nodeVars, System.Random)` — **two**
binding channels, the second binding a whole subtree rather than a string. The full `History`
and an entity snapshot are in scope. The originating `HistoricEvent` is **not** a parameter,
so event-derived naming must locate the event via `HistoricEntity.GetEventWithEventProperty` /
`GetRandomEventWhereDelegate`. Viable without Harmony. See `DESIGN_history_recon_addendum.md` §Q2.

---

## Q3 — Is the event pool extensible? · **ANSWERED: NO. HARDCODED.** (corrected 2026-08-30)

**Metadata left this open and the decompile closed it.** `QudHistoryFactory.GenerateNewSultan`
holds seventeen literal branches and constructs each event inline:

```csharp
for (int i = 0; i < 8; i++) {
    int num = Stat.Random(0, 16);
    if (num == 0)  historicEntity.ApplyEvent(new CorruptAdministrator(), …);
    if (num == 1)  historicEntity.ApplyEvent(new CapturedByBandits(), …);
    …
    if (num == 16) historicEntity.ApplyEvent(new Marry(), …);
}
```

No reflection, no registry, no data. The reflection-based registry this section called
plausible does not exist, and the instruction not to plan on it was right.

Two consequences. **Adding a single event type means replacing a static method on a static
class** — which is the cost `DESIGN_history_implementation.md`'s tier table has to carry. And
`DESIGN_history.md` §2.1's arithmetic — 17 types, 8 draws, 5 sultans, ~40 instances per world
— is not an estimate from the wiki. It is this loop.

---

## Q4 — Era vocabulary: token or string? · **ANSWERED: TOKEN. COST HALVES.**

```json
"gospels": {
  "EarlySultanate": {
    "adjective": ["star","space","time","temporal","spatial","cosmic","empyrean",
                  "ether","algebraic","astral","luminous","stellary","high"],
    "location":  ["<spice.3Dshapes.!random>", "<spice.2Dshapes.!random>", …],
    "vehicle":   ["star blimp", "star <spice.3Dshapes.!random>", …],
    "worshipObject": …, "objectNoun": …
  },
  "LateSultanate": { … same five keys, earthen vocabulary … }
}
```

Both eras expose the **same five keys**, and templates reference
`<spice.history.gospels.EarlySultanate.adjective.!random>`. Era variation is therefore
**token substitution inside a shared template**, exactly as hoped.

**Consequence:** each new event type needs **one template per source**, not one per source
per register. The estimate in `DESIGN_history_catalog.md` §6 drops from **128 fragments to ~64**.
This is the single largest cost reduction available to the project, and it lands on the item
identified as the project's main bulk.

Thirteen other gospel categories use the same two-era structure: `VehicularSabotage`,
`CrashedVehicle`, `MarriageAllianceResult`, `CommittedWrongAgainstSultan`, `EnemyHostName`,
`LostItem`, `ImmoralPractice`, `HumblePractice`, `RitualName`, `ObjectFoundBy`, `Celebration`,
`CivilizationActivity`, `VehicularSabotageResult`.

---

## Q5 — Sultans generated in sequence? · **ANSWERED: YES** (corrected 2026-08-30)

One pass, chronological, over a single shared mutable `History`:

```csharp
for (int i = 1; i <= 5; i++) {
    GenerateNewRegions(history, Stat.Random(2, 3), i);
    GenerateNewSultan(history, i);
    history.currentYear += spreadOfSultanYears[i - 1];
}
```

Each sultan is generated after everything written before it and can see all of it, so
**cross-sultan legacy events are feasible.** This section previously read *"strongly implied"*
on the strength of `InitializeSultan` existing as a distinct class; the loop settles it.

---

## Q6 — Do other systems read the record? · **PARTIAL, ENCOURAGING**

Village history is generated by **the same machinery** — `InitializeVillage`, `Worships`,
`Despises`, `VillageProverb` and friends are `XRL.Annals` event classes alongside the sultan
events, and `HistorySpice.json` carries `villages` (15 keys) and `tombstones` (15 keys)
categories.

So villages are not a parallel generator; they are the same generator pointed at a different
entity type. That is materially better news than `DESIGN_history.md` assumed when it scoped
village history out — the compositional model could extend there later at much lower cost
than a separate project.

**NEEDS DECOMPILE:** whether murals and NPC gossip read the record or generate independently.

---

## Q7 — Headless generation? · **ANSWERED: PLAUSIBLE** (addendum §Q7)

`HistoryKit.History` and `QudHistoryFactory` look like plain classes rather than Unity
components, which is encouraging for driving them from a test harness — but unconfirmed.

---

## New findings not on the question list

### N1 — The element system (a pre-existing coherence axis)

`spice.elements` defines **11 thematic domains**: glass · jewels · stars · time · salt · ice ·
scholarship · might · chance · circuitry · travel.

Each carries `professions`, `materials`, `adjectives`, `nouns`, `nounsPlural`, `practices`,
`murdermethods`, `inspirationsVerbPhrase`, `quality`, `babeTrait` and more. A sultan is
associated with an element, and it threads through their events, their relics, even how they
kill people.

**This changes the diagnosis, and the design docs need updating.** Qud already has a
coherence mechanism — it is *thematic*, not *causal*. A sultan's life hangs together by motif
rather than by consequence. That is a deliberate and rather elegant choice, and it explains
why the histories feel *stylistically* unified but *narratively* arbitrary.

The mod should therefore **add a causal axis alongside the thematic one, not replace it** —
and element affinity is an obvious input to the temperament system proposed in
`DESIGN_history_events.md` §5.3, which may already be half-built here.

### N2 — A ledger already exists in embryo

`XRL.Annals` exposes helpers: `SetEntityProperty` · `SetEntityProperties` ·
`MutateListProperty` · `AddEntityListItem` · `RemoveEntityListItem` ·
`RemoveEntityListProperties` · `AddLocationToRegion` · `Regionalize`.

Together with `HistoricEntity` / `HistoricEntitySnapshot`, this is **exactly the shape of the
ledger** proposed in `DESIGN_history_events.md` §2 — mutable typed properties on a historic entity,
snapshotted over time.

The `[ASSUMPTION]` flagged there as "the single largest implementation risk in the project"
is looking considerably safer. The threads model may be implementable **as entity list
properties** rather than as a parallel structure — which would be far more compatible with
the existing engine than the design assumed.

### N3 — A perspective model already exists in embryo · **PARTLY CORRECTED**

> **Corrected 2026-08-15.** `HistoricPerspective` has **no** `gospelText`/`tombText` fields —
> it is `entityId · eventId · int feeling · mainColor · supportColor`, held per-event in
> `HistoricEvent.perspectives`. It models an *attitude*, not text variants; the differing text
> is selected from spice using that attitude. A new source is therefore a **perspective key +
> feeling-keyed spice branches**, not new text fields. Cheaper than assumed, still Tier 2-light.
> `DESIGN_history_sources.md` should be reframed accordingly. See `DESIGN_history_recon_addendum.md` N3.


`HistoryKit.HistoricPerspective`, plus string constants `gospelText`, `tombText`,
`GospelText`, `perspectives`, `perspective`, and an `XRL.Annals.GospelEvent` class.

The source model in `DESIGN_history_sources.md` is therefore **extending an existing abstraction rather
than inventing one**. If `HistoricPerspective` is genuinely a first-class type, adding mural
and oral-tradition perspectives may be a Tier 2 addition rather than an overhaul.

### N4 — Vocabulary size, measured

Expanding the grammar to terminal strings (1–2 word terminals, depth ≤ 5):

| Pool | Forms in data | Distinct terminals reachable |
|---|---|---|
| `spice.adjectives` | 30 | **~280** |
| `spice.nouns` | 40 | **~488** |
| `spice.objectNouns` | 16 | **~342** |
| element adjectives (all 11) | — | 61 |

**"Add more words" is refuted.** With ~280 adjectives and ~488 nouns, form 8
(`<adjective> <noun>`) alone can produce well over 100,000 distinct names — and it still
reads as obviously generated. That is the clearest possible evidence for the thesis in
`DESIGN_history_naming.md` §1: the problem is not vocabulary size, it is that the name references
nothing. A player does not perceive a name as repetitive; they perceive it as *arbitrary*.

This also means the **plainness quota (`DESIGN_history_naming.md` §4) is now the cheapest high-impact
change in the entire project** — it is a data edit to a shipped JSON file, and the register
problem is entirely a property of which terminals those ~280 adjectives draw from.

### N5 — The Latin-suffix generator

`spice.items.suffixes`: `icus · ica · acus · ucus · ocus · ecus · aca · eca · oca · uca ·
yca · ycus`, alongside `items.blessing` (51 entries) and per-slot `weapons` / `armor` /
`misc` lists. Worth tracing — it is a plausible contributor to the "obscure mashup" texture
and it is pure data.

---

## Q8 — Can mods modify `HistorySpice.json`? · **ANSWERED: YES, BY SHIPPING THE FILE** (corrected 2026-08-29)

This was the question gating every Tier 1 claim. The answer is nuanced but good.

### There is no *generic* JSON merge, but `HistorySpice.json` is special-cased

> ### CORRECTED 2026-08-29 — shipping the file **is** the mechanism
>
> The paragraph below was wrong in its conclusion, and the correction matters because it
> changes what v0.1 is: a data file rather than a C# spike.
>
> `HistoryKit.HistoricSpice.Init()` merges mod JSON by hand:
>
> ```csharp
> JObject jObject = JObject.Parse(File.ReadAllText(DataManager.FilePath("HistorySpice.json")));
> JsonMergeSettings settings = new JsonMergeSettings {
>     MergeArrayHandling      = MergeArrayHandling.Union,
>     MergeNullValueHandling  = MergeNullValueHandling.Ignore,
>     PropertyNameComparison  = StringComparison.Ordinal
> };
> foreach (ModInfo activeMod in ModManager.ActiveMods)
>     foreach (ModFile file in activeMod.Files)
>         if (file.Type == ModFileType.JSON && file.Name == "historyspice.json")
>             jObject.Merge(JObject.Parse(File.ReadAllText(file.OriginalName)), settings);
> ```
>
> No C#, no reflection resolver, no `[ModSensitiveCacheInit]`, and no `TODO(Q9)`.
>
> **Two details that constrain what this can do:**
>
> - **The filename match is case-insensitive in effect.** `ModFile` sets
>   `FullName = OriginalName.ToLowerInvariant()` and `Name = Path.GetFileName(FullName)`, so a
>   mod may ship `HistorySpice.json` in any casing and still match `"historyspice.json"`.
> - **The merge is additive only.** `MergeArrayHandling.Union` adds new forms and vocabulary and
>   **cannot remove vanilla's**. Forms 7 and 8 of `spice.history.relics.names` — the specific
>   complaint that started this project, per *Facts worth not rediscovering* below — **cannot be
>   suppressed by a merge.**
>   Diluting them is possible; removing them still needs code.
>
> **Why the recon missed it, which is the transferable part.** The search was the right one and
> its finding was true: there is no generic JSON counterpart to `GetXMLFilesWithRoot`. What it
> could not see is that `HistoricSpice` special-cases one filename by hand. `HistoricSpice.cs:65`
> is the **only** consumer of `ModFileType.JSON` in the entire assembly, so no amount of searching
> `DataManager` would have found it, and metadata alone could not have shown it.
>
> > **A general claim can be true while the specific conclusion drawn from it is false.** *"There
> > is no JSON merge pipeline"* is correct. *"Therefore shipping a JSON file does nothing"* is not,
> > because one class implements the merge itself.

Qud's *generic* data merge pipeline is XML-only. The assembly exposes
`DataManager.GetXMLFilesWithRoot` and `DataManager.YieldXMLStreamsWithRoot` — the mechanism
that aggregates base-game and mod XML by root element — and there is no JSON counterpart.
`GetStreamingAssetsXMLStream` is likewise XML-specific.

That much stands. What does **not** follow is the conclusion this section used to draw, that a mod
cannot ship a `HistorySpice.json` which merges into the base file. It can, by the special case
above.

### But there is a supported runtime hook, with precedent

> ### CORRECTED 2026-08-15 — the tree is **Newtonsoft**, not SimpleJSON
>
> ```
> HistoryKit.HistoricSpice
>   private static Newtonsoft.Json.Linq.JObject                        _root
>   public  static Dictionary<string, Newtonsoft.Json.Linq.JContainer> _roots
>   public  static JObject get_root()      // public static property `root`  <- Q9 ANSWER
>   public  static void    CheckInit()
> ```
>
> `SimpleJSON` types do ship in the assembly, but never appear in TypeRefs and are not what
> `HistoricSpice` holds. Code written against `SimpleJSON.JSONNode` **will not compile.**
> Use `JObject` / `JArray` / `JValue`. The *WM Extended Mutations* precedent below presumably
> predates a migration. See `DESIGN_history_recon_addendum.md` §Q9.
>
> Also note: `HistorySpice.json` wraps all 51 categories in a single top-level `"spice"`
> object, so paths the grammar addresses as `spice.foo` are `root["spice"]["foo"]` unless
> `HistoricSpice` unwraps on load — which metadata cannot determine. Detect at runtime.

The spice tree is held by `HistoryKit.HistoricSpice`, and mods mutate it in place during
cache initialisation. The game provides first-class attributes for exactly this:

- `XRL.HasModSensitiveStaticCacheAttribute` — marks the class
- `XRL.ModSensitiveCacheInitAttribute` — marks the method run at (re)initialisation

**Working precedent in the wild** (but see the correction above — that mod's JSON library
usage may predate a migration and should not be copied verbatim)**:** the *WM Extended
Mutations* Workshop mod ships
`HistorySpiceUpdateonGameLoad.cs`, which is exactly this pattern — a
`[HasModSensitiveStaticCache]` class with a `[ModSensitiveCacheInit]` method that builds
`SimpleJSON` nodes and inserts them at paths like `spice.extradimensional` and
`spice.cooking.recipeNames.ingredients`.

```csharp
[HasModSensitiveStaticCache]
public static class LX_SpiceInit
{
    [ModSensitiveCacheInit]
    public static void Init()
    {
        // build Newtonsoft JObject/JArray/JValue nodes, insert at a spice path,
        // or replace an existing array outright
    }
}
```

### Why this is a good outcome

This is Tier 2, but the **cheapest and safest form of Tier 2 available**: no Harmony, no type
override, no reflection into private state. A documented attribute and direct manipulation of
a public data structure, with a shipped Workshop mod proving the path works.

Costs: the scripting-mod approval prompt applies (it is C#), and the mod must tolerate
re-initialisation, since mod-sensitive caches can reset during a session.

### What this unlocks immediately

`spice.history.relics.names` is a plain array in that tree. A mod can **replace it wholesale**
— which means:

- **Deleting the two ungrounded forms** (§Q2 forms 7 and 8) is a few lines of code.
- **Adding a plain-register lexicon** and new name forms that draw on it is a data edit
  expressed in C#.

Those two changes alone are a coherent, shippable **v0.1** that directly addresses the
original complaint, require no history-generation access, and carry near-zero update
fragility. This is the fastest meaningful result available and it should be built first.

The one thing still gated: name forms referencing **new** `*variables*` need the expander to
bind them, which is the outstanding Q2 decompile question. Forms built only from existing
bindings (`*itemType*`, `*element*`, `*creatureName*`, `*personNoun*`) and existing spice
paths work today.

---

## Facts worth not rediscovering

Moved here from `DESIGN_history_handoff.md` when that document was retired — it was a quick-reference
list for a separate project's next session, and these are the parts that outlive it.

- **The relic grammar is `spice.history.relics.names`** — 8 forms. Forms 7
  (`<noun>-<noun>`) and 8 (`<adjective> <noun>`) are pure random assembly with no grounding.
  **They are the specific cause of the complaint that started this project.**
- **Vocabulary is large:** ~280 adjective terminals, ~488 noun terminals. Form 8 alone can
  produce >100,000 distinct names and still reads as generated. Adding words will not help.
- **Existing plain-ish pools you can use immediately:** `spice.basicColors` (13),
  `spice.metals` (23). Both are already plain register.
- **`spice.ordinal` is numeric** (`1st`, `2nd`) — word ordinals need adding separately.
- **Event classes:** ~24 sultan, 12 village, 16 Resheph-specific, all in `XRL.Annals`.
- **Village history uses the same machinery** as sultan history — extending there later is
  much cheaper than the docs assumed.
- **Build target:** `netstandard2.0`, C# 9, per the game's own `Mods.csproj.template.txt`.
- **`manifest.json` uses lowercase keys** in the shipped DLC (`id`, `title`, `version`,
  `author`, `tags`, `loadOrder`, `previewImage`); community mods use PascalCase and also
  work, so it appears case-insensitive.

---

## Revised tier assignment

| Component | Prior | **Revised** | Basis |
|---|---|---|---|
| Plainness quota / PLAIN lexicon | 1 or 2 | **Tier 2-light** — spice mutation | No JSON merge, but `[ModSensitiveCacheInit]` works (Q8) |
| Remove ungrounded relic forms | — | **Tier 2-light** — replace the array | `spice.history.relics.names` is mutable (Q8) |
| New name forms, existing bindings | 2, maybe 3 | **Tier 2-light** | Uses `*itemType*` / `*element*` already bound (Q2) |
| Naming derivation, new bindings | 2 or 3 | **Tier 2** | Needs new `*variables*` at the call site — blocked on Q2 decompile |
| Ledger + threads | 2 | **Tier 2, lower risk** | Entity property helpers already exist (N2) |
| Event pool extension | 2 or 3 | **Unknown** | Blocked on Q3 |
| Source divergence | 2 | **Tier 2, lower risk** | `HistoricPerspective` exists (N3) |
| Cross-sultan legacy | 2–3 | **Unknown** | Blocked on Q5 |

"Tier 2-light" means: compiled C#, so the approval prompt applies, but no Harmony, no type
override, and no reflection into private state — only documented attributes and a public data
structure. It is the lowest-risk way to ship code in this game, and **it is enough for v0.1.**

Note the consequence for the macOS constraint: everything in v0.1 and most of v0.2 needs no
Harmony at all, so it is fully developable and testable on the Mac. The Windows machine is
not on the critical path until Q3 or Q5 forces it.

---

## Revised next actions

1. **Build the v0.1 spike.** A `[HasModSensitiveStaticCache]` class that replaces
   `spice.history.relics.names` — drop the two ungrounded forms, add a plain-register
   lexicon, add forms drawing on it. No Harmony, no decompile needed, testable on the Mac.
   This validates the whole delivery path and is a real mod on its own.
2. **Run Q0 live** — native and forced-Rosetta, with a Harmony-using mod installed. Now
   lower priority: nothing on the near-term path needs Harmony.
3. **Decompile** (ILSpy on the Windows machine, or any machine with the .NET SDK) and answer
   Q3, Q5, Q7, plus the `HistoricStringExpander` variable-bag question from Q2 — that last
   one is the gate on real derivation-based naming.
4. **Measure the baseline.** With the spice tree reachable in code, dumping generated relic
   names for corpus analysis is now straightforward.
5. **Revise the design docs** for the element system (N1), the existing ledger primitives
   (N2), and the existing perspective type (N3).

---

## Document revisions required

| Doc | Change |
|---|---|
| `DESIGN_history.md` | Add the element system to the diagnosis; note thematic-vs-causal coherence; correct HistoryKit/XRL.Annals |
| `DESIGN_history_events.md` | Rework §2 ledger onto `HistoricEntity` properties; downgrade the stateless-generator risk; add element affinity to temperament (§5.3) |
| `DESIGN_history_catalog.md` | Update the retrofit table to real class names; **halve** the §6 authoring estimate to ~64 fragments |
| `DESIGN_history_naming.md` | Add the eight measured forms; promote plainness quota to Tier 1; add the ~280/~488 vocabulary measurement |
| `DESIGN_history_sources.md` | Reframe as extending `HistoricPerspective` rather than inventing a model |
| `DESIGN_history_implementation.md` | Revised tier table; Q0 finding (arm64 slice, Rosetta workaround); add the JSON-merge question |
| **all of the above** | **Cross-check against `DESIGN_history_recon_addendum.md` (2026-08-15) first — it corrects §Q8 and N3, and answers Q2/Q7/Q9** |


---

# Addendum, 2026-08-29 — the five NEEDS DECOMPILE questions are answered

The recon that produced this document had no decompiler; these were read from the decompiled
assembly of the installed build. Source and full working:
[vixygrey/qud-expanded-community-edition#178](https://github.com/vixygrey/qud-expanded-community-edition/issues/178#issuecomment-5466193621),
tracked as #689. Two of them change the shape of the project.

**Q9 — the accessor exists, and the spike does not need it.** `HistoryKit.HistoricSpice` exposes
`public static JObject root` (with `CheckInit()` in the getter) and
`public static Dictionary<string, JContainer> roots`, keyed by top-level spice key. Newtonsoft,
confirming `DESIGN_history_recon_addendum.md` over this document's original SimpleJSON claim. But §Q8 above
supersedes the whole question: shipping the file is the mechanism, so there is nothing to reach into.

**Q2 — the gate on derivation-based naming is shut.** `ExpandQuery` is richer than expected —
`entity$…` and `entity.<prop>` reach a snapshot's properties and lists, and `entity[<id>]` reaches any
other entity in the history at the current year. **None of it is available where relics are named.**
All four call sites — `RelicGenerator:140`, `ItemNaming:387`, `RandomAltarBaetyl:615`, `Faction:1405`
— pass `entity` null and `history` null, and `RelicNameContext` is a `private static
Dictionary<string,string>` holding exactly two keys, set immediately before the call:

```csharp
RelicNameContext["*element*"]  = Element;
RelicNameContext["*itemType*"] = Type;
```

> **It is not a bag someone forgot to fill. It is a two-variable context by construction.** So the
> question this project called *"the gate on the core of the mod"* answers **no**: derivation-based
> naming cannot be reached by grammar alone.

There is a way through, and it already ships. `GenerateRelicNameByRegion` is taken whenever
`SnapRegion != null`, passes `sultanHistory`, and builds on the region's `newName`. A grounded naming
path exists and the ungrounded one is the fallback — so **widening which relics take the grounded path
may be a smaller change than replacing the flat one.**

**Q3 — hardcoded, with no extension point.** Seventeen literal branches, eight draws, `new` inline, no
reflection and no registry:

```csharp
for (int i = 0; i < 8; i++) {
    int num = Stat.Random(0, 16);
    if (num == 0)  historicEntity.ApplyEvent(new CorruptAdministrator(), …);
    …
    if (num == 16) historicEntity.ApplyEvent(new Marry(), …);
}
```

So `DESIGN_history.md`'s arithmetic — 17 types, 8 draws, 5 sultans, ~40 instances per world — is not an
estimate from the wiki, it is the loop. **Adding one event type means replacing a static method on a
static class**, which prices the events half of this project well above the naming half.

**Q5 — yes, one pass, chronological.** Upgrades this document's guess to a fact:

```csharp
for (int i = 1; i <= 5; i++) {
    GenerateNewRegions(history, Stat.Random(2, 3), i);
    GenerateNewSultan(history, i);
    history.currentYear += spreadOfSultanYears[i - 1];
}
```

One shared mutable `History`, sultans in order, each seeing everything written before it.
**Cross-sultan legacy events are feasible.**

**Q7 — a working precedent already ships.** `HistoryTestView` calls
`QudHistoryFactory.GenerateNewSultanHistory()`, renders `history.Dump(bVerbose: false)` and writes
`history_log.txt`. It is a `UIView`, so it needs the game running rather than being headless in the
strict sense — but generation touches no world and no zone, and the dump format already exists. The
metrics harness is cheap.

## What the five answers do to the project's shape

| half | what it costs | scripting tier |
|---|---|---|
| **Naming** — vocabulary, new forms, plainness quota | a `historyspice.json` merge. **No C# at all** | none |
| **Events** — new event types, causal derivation | replacing `GenerateNewSultan`, a static method | the expensive one |

The cheap half is the half with nothing to do with psionics; the psionics-in-history idea needs new
event types and lands squarely on the expensive side. **v0.1 can be a data-only mod that ships on its
own**, which is a better first release than a spike blocked on a symbol.

> **One claim here is still unproven and should be tested before anything is built on it:** that a
> `historyspice.json` merge actually reaches the grammar in a running game. Everything above is read
> from the assembly and is code-structural; a one-line test file settles it in a minute.
