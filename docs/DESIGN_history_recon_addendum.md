# Recon Addendum — full metadata pass

**Date:** 2026-08-15
**Build inspected:** `Assembly-CSharp.dll`, 11,806,208 bytes, from the local macOS install
**Method:** hand-rolled ECMA-335 reader — PE → CLI header → `#~` tables + `#Strings`/`#Blob`
heaps. Parses TypeDef / Field / MethodDef / Param / TypeRef and decodes field and method
signature blobs.

> **How this differs from the previous pass.** `DESIGN_history_recon.md` read the flat `#Strings`
> heap, which lists every string in the assembly but cannot say *which field belongs to which
> type*, *what type a field is*, or *what a method's signature looks like*. This pass parses
> the metadata tables properly, so member structure and signatures are now direct observation.
>
> **Still no method bodies.** No .NET SDK and no package index in this container, so IL was
> not decompiled. Questions needing control flow are still open and are marked as such below.
> Tooling to reproduce this is committed alongside (`tools/metadata/`).

Assembly totals: **7,837 typedefs · 30,396 fields · 63,452 methods.**

---

## Q9 — the `HistoricSpice` root accessor · **ANSWERED**

This was the blocker on the v0.1 spike.

```
HistoryKit.HistoricSpice  (extends System.Object)
  private static Newtonsoft.Json.Linq.JObject                      _root
  public  static Dictionary<string, Newtonsoft.Json.Linq.JContainer> _roots
  public  static JObject  get_root()          // i.e. a public static property `root`
  public  static void     CheckInit()
  private static void     Init()
  private static void     ResolveRelativeLinks(RingDeque<string> Stack, JContainer Container)
```

**Use `HistoricSpice.root`** (public static property, returns `JObject`). `_roots` is also
public if you need the per-file containers. Delete the reflection resolver in
`LX_SpiceInit.cs`.

`CheckInit()` being public and separate from the private `Init()` is worth noting — it is
presumably the idempotent "ensure loaded" entry point, which matters for a
`[ModSensitiveCacheInit]` method that may run before or after the tree is built.

### ⚠ Correction: the tree is **Newtonsoft**, not SimpleJSON

`DESIGN_history_recon.md` §Q8 states the tree is a `SimpleJSON.JSONNode` structure. **It is not.**

| Check | Result |
|---|---|
| `SimpleJSON` namespace present in assembly | **yes** (types are defined in it) |
| `SimpleJSON` appears in TypeRefs | no |
| `Newtonsoft` appears in TypeRefs | **yes** |
| `HistoricSpice._root` declared type | **`Newtonsoft.Json.Linq.JObject`** |

Both libraries ship, but the spice tree is Newtonsoft `JObject`/`JToken`. Any code written
against `SimpleJSON.JSONNode` — which is what the current scaffold assumes, following the
*WM Extended Mutations* precedent — **will not compile against this build.** That precedent
may predate a migration, or may touch a different structure.

Build nodes with `JObject` / `JArray` / `JValue`, and index with `JToken`.

---

## Q2 — the variable bag, and what's in scope · **ANSWERED**

```
HistoryKit.HistoricStringExpander  (static)
  public static string ExpandQuery(
      string query,
      HistoricEntitySnapshot entity,
      History history,
      Dictionary<string,string> vars,
      Dictionary<string,JToken>  nodeVars,
      System.Random R)

  public static string ExpandString(string input, System.Random Random)
  public static string ExpandString(
      string input, HistoricEntitySnapshot entity, History history,
      Dictionary<string,string> vars, System.Random Random)

  public static Dictionary<string,string> GetVariableCache()
  public static History nullHistory          // sentinel for the no-history overload
```

**There are two binding channels, and the richer one was not previously known:**

1. `Dictionary<string,string> vars` — the `*variable*` mechanism seen in the grammar
   (`*itemType*`, `*element*`, `*creatureName*`, `*personNoun*`). Open-ended: any key you put
   in is bindable.
2. `Dictionary<string,JToken> nodeVars` — binds a **subtree**, not a string. This means a
   caller can hand the grammar a whole JSON node to select from. That is a materially more
   powerful seam than `DESIGN_history_naming.md` assumed.

**Scope:** the full `History` and a `HistoricEntitySnapshot` are passed to every meaningful
overload. So at expansion time the entire record is reachable — entity properties, the event
list, other entities.

**The originating event is _not_ a parameter.** There is no `HistoricEvent` in any signature.
So derivation-based naming does **not** get the event handed to it; it gets the entity and the
history and must locate the event itself. `HistoricEntity` exposes `GetEvent`,
`GetEventWithEventProperty`, `GetEventWithEntityProperty` and
`GetRandomEventWhereDelegate`, so this is a lookup, not a blocker — but it is a lookup, and
whoever binds the variables has to do it.

**Verdict: derivation-based naming is viable without Harmony.** The gate is not the expander;
it is whether the *call site* that names a relic populates `vars`/`nodeVars` with what you
want. That specific call site still needs a body read.

---

## Q7 — headless generation · **ANSWERED: PLAUSIBLE**

```
HistoryKit.History            extends HistoryKit.HistoricEntityList
XRL.Annals.QudHistoryFactory  extends System.Object
```

Neither is a `MonoBehaviour` or any Unity type. `History` carries its own `System.Random`
(`_r`, with a public `get_r()`), holds `events`, `EntityByID`, `startingYear`, `currentYear`,
and has `Load`/`Save` against `XRL.World.SerializationReader/Writer`.

`QudHistoryFactory.GenerateNewSultanHistory()` is `static` and returns a `History`.

So a metrics harness can plausibly call `GenerateNewSultanHistory()` directly. The residual
risk is what `InitializeHistory` touches — it may reach into game statics that assume a loaded
world. **Bodies needed to be certain**, but nothing in the shape of these types blocks it.

---

## Q5 — sultans in sequence · **STRONGLY IMPLIED, NOT PROVEN**

```
static void GenerateNewSultan(History history, int period)
static void GenerateNewRegions(History history, int numRegions, int period)
static void AddResheph(History history)
static History GenerateNewSultanHistory()
static int numSultans          // static field
```

`period` as an explicit `int` parameter on both sultan and region generation, alongside a
`numSultans` field, is the signature of a `for (period = 0; period < numSultans; period++)`
loop inside `GenerateNewSultanHistory`. Cross-sultan legacy events would therefore have
earlier sultans available when later ones generate.

**Still needs the body** to confirm ordering and whether state is carried between iterations.

---

## Q3 — event pool extensibility · **STILL NEEDS BODIES, but better characterised**

```
XRL.Annals types: 67
  65 extend HistoryKit.HistoricEvent
   2 extend System.Object   (QudHistoryFactory + one other)
```

Every event is a subclass of a single base, and `HistoricEvent` exposes a **`Generate`**
method — so the factory constructs an event and calls `Generate` polymorphically. That is the
shape reflection-based discovery would take.

But **no registry field exists on `QudHistoryFactory`** — its fields are entirely worldgen
tuning constants (`numSultans`, `avgYearsInSultanate`, `percentOfWorldmap_*`,
`villageModifier_*`). If a type list exists it is a local inside a method body, which leans
**hardcoded**, not reflected.

Plan for hardcoded until a body says otherwise.

---

## N2 revisited — the ledger is real and first-class

```
HistoryKit.HistoricEvent
  long id · long year · long duration
  History history · HistoricEntity entity
  Dictionary<string,string>             eventProperties
  Dictionary<string,string>             entityProperties
  Dictionary<string,List<string>>       addedListProperties
  Dictionary<string,List<string>>       removedListProperties
  Dictionary<string,HistoricPerspective> perspectives
  → Generate, ApplyEvent-adjacent helpers, SetEventProperty, ExpandString, ...

HistoryKit.HistoricEntity
  string id · List<HistoricEvent> events · List<string> ListProperties
  → ApplyEvent · AddEvent · GetCurrentSnapshot
  → SetEntityPropertyAtCurrentYear · MutateListPropertyAtCurrentYear
  → GetEvent · GetEventWithEventProperty · GetEventWithEntityProperty
  → GetRandomEventWhereDelegate
```

`DESIGN_history_events.md`'s ledger is **already the engine's data model**, including the
add/remove-list-property distinction. Build threads as entity list properties. The
"generator may be stateless" risk is definitively dead.

---

## N3 corrected — `HistoricPerspective` is *feeling*, not text

```
HistoryKit.HistoricPerspective
  string entityId · long eventId · int feeling
  string mainColor · string supportColor
  → randomizeFeeling(), Load, Save
```

There are **no `gospelText` / `tombText` fields.** Those strings, seen in the `#Strings` heap,
are spice keys or property names, not members of this type.

So a perspective is `(whose view, of which event, how they feel, what colours render it)` —
an *attitude*, held per-event in `HistoricEvent.perspectives` keyed by string. The differing
**text** is then selected from spice using that attitude.

`DESIGN_history_sources.md` should be reframed accordingly: adding a mural or oral-tradition source means
adding a **perspective key plus spice branches keyed on feeling**, not adding text fields to a
type. That is cheaper than the doc assumed, and it is still Tier 2-light.

---

## N6 — NEW: the player already exists in the historic record

```
XRL.Annals.QudHistoryFactory
  public static string PLAYER_ENTITY_ID
  static HistoricEntity         RequirePlayerEntity()
  static HistoricEntitySnapshot RequirePlayerEntitySnapshot()
```

**The player has a `HistoricEntity` in the same ledger the sultans live in**, with a reserved
id and require-or-create accessors.

Not needed for lore-expansion's current roadmap, but it is the single most important fact in
this pass for anything involving the player and history — see the reconciliation note in
`../design-docs/` regarding the legacy mod, which had assumed a parallel record was necessary.

---

## Reproducing this

`tools/metadata/cli_meta.py` — the reader. `tools/metadata/query.py` — the queries above.
No dependencies beyond the standard library.

```
python3 tools/metadata/query.py
```

Point `DLL` at the installed `Assembly-CSharp.dll`. Re-run after a game update to diff the
surface you depend on.

---

## Revisions this pass requires

| Doc | Change |
|---|---|
| `DESIGN_history_recon.md` §Q8 | **SimpleJSON → Newtonsoft `JObject`.** Correct before the spike is compiled. |
| `DESIGN_history_recon.md` §Q2 | Answered: two binding channels, event not in scope, entity+history are |
| `DESIGN_history_recon.md` §Q7 | Answered: plain classes, harness plausible |
| `DESIGN_history_recon.md` §Q5 | Upgrade to strongly-implied |
| `DESIGN_history_recon.md` §Q3 | Leans hardcoded — no registry field |
| `DESIGN_history_recon.md` N3 | Perspective is feeling+colour, not text |
| `DESIGN_history_handoff.md` §1 | Q9 answered — `HistoricSpice.root`; **and the SimpleJSON assumption is wrong** |
| `DESIGN_history_sources.md` | Reframe onto perspective-key + feeling-keyed spice |
