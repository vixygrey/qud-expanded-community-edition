# API verification — corrections to the four design docs

**Date:** 2026-08-15
**Source:** metadata pass over `Assembly-CSharp.dll` (see
`lore-expansion/docs/recon-addendum-metadata.md` and `lore-expansion/tools/metadata/`)

Every identifier the design docs flagged as unverified is now confirmed or corrected.
**This file supersedes the "unverified / verify before coding" caveats in all four.**

---

## 1. The headline: none of these mods need Harmony

Every hook the docs hypothesised exists as a real `MinEvent`. That was the single largest
open risk across the whole set, and it lands well.

| Doc | Needed hook | Actual type | Harmony? |
|---|---|---|---|
| Sleep | the `Asleep` effect | `XRL.World.Effects.Asleep` : `XRL.World.Effect` | no |
| Sleep | `Wakeful` | `XRL.World.Effects.Wakeful` | no |
| Burden | carry capacity | `XRL.World.GetMaxCarriedWeightEvent` : `IWeightEvent` : `MinEvent` | no |
| Burden | current load | `XRL.World.GetCarriedWeightEvent` : `IWeightEvent` | no |
| Burden | the vanilla cliff | `XRL.World.Effects.Overburdened` | no |
| Faction rivalry | reputation change | `XRL.World.ReputationChangeEvent` **and** `XRL.World.AfterReputationChangeEvent` | no |
| Legacy | death | `XRL.World.BeforeDieEvent` / `AfterDieEvent` / `BeforeDeathRemovalEvent`, all : `IDeathEvent` | no |
| Legacy | cross-run persistence | `XRL.IScribedSystem` (`Write`/`Read`) | no |
| Water covenant | ritual start | `XRL.World.WaterRitualStartEvent` | no |

**This retires the biggest caveat in `DESIGN_difficulty_systems.md`.** That doc rated faction
rivalry "Low effort — probably no Harmony, *if a reputation hook exists*," and I later
told you that ten minutes with the assembly should decide it. It does: **two** hooks exist,
before and after. Faction rivalry stays the recommended first build with the qualifier
removed.

### The macOS constraint you already found

`lore-expansion/docs/recon-findings.md` §Q0 establishes that this Mac build is a universal
binary with a **native arm64 slice** — the failing configuration for Harmony
(`mprotect EACCES` in MonoMod's POSIX detour layer), not the Rosetta case.

Combined with the table above, the practical conclusion is stronger than "prefer to avoid
Harmony": **every mod in these docs is fully developable and testable on your Mac**, and none
of them put the Windows machine on the critical path.

---

## 2. Burden — the exact API

```
XRL.World.GetMaxCarriedWeightEvent : IWeightEvent : MinEvent
    static ... GetFor(...)
    ... AdjustWeight(...)
    pooled: List<GetMaxCarriedWeightEvent> Pool, FromPool(), ResetPool()
XRL.World.GetCarriedWeightEvent : IWeightEvent
XRL.World.CheckOverburdenedOnStrengthUpdateEvent
XRL.World.Effects.Overburdened
```

`AdjustWeight` on the max-carried event is exactly the seam the graded-bands design needs —
you adjust rather than replace, so you compose with cybernetics, mutations and other mods
instead of fighting them.

Note the events are **pooled** (`FromPool` / `ResetPool` / `PoolCounter`). Do not cache
instances or hold references past the handler.

`CheckOverburdenedOnStrengthUpdateEvent` also tells you the vanilla threshold is re-evaluated
on Strength change — your band recalculation should hook the same moments, not only inventory
changes.

---

## 3. Legacy — the design changes materially

### The player already has a `HistoricEntity`

```
XRL.Annals.QudHistoryFactory
    public static string           PLAYER_ENTITY_ID
    static HistoricEntity          RequirePlayerEntity()
    static HistoricEntitySnapshot  RequirePlayerEntitySnapshot()
```

**The player is already an entity in the same historic ledger as the sultans**, with a
reserved id and require-or-create accessors.

`DESIGN_water_and_legacy.md` §3.2 says: *"do not try to add the player as a sixth sultan …
generate a parallel record instead."* That advice was aimed at the **sultan generator**, and
for that it still stands — `QudHistoryFactory` shows no registry field, so the event pool
leans hardcoded and injecting a sixth sultan means fighting it.

But the premise underneath it — that the player has no place in the record — is **wrong**.
The correct design is neither "sixth sultan" nor "parallel record":

> **Write the legacy onto the player's existing `HistoricEntity`, and read it back next world.**

That uses the engine's own ledger rather than shadowing it. Concretely:

```
HistoricEntity
    SetEntityPropertyAtCurrentYear(...)
    MutateListPropertyAtCurrentYear(...)
    AddEvent(...) / ApplyEvent(...)
    GetCurrentSnapshot()
    List<string> ListProperties
HistoricEvent
    Dictionary<string,string> eventProperties / entityProperties
    Dictionary<string,List<string>> addedListProperties / removedListProperties
    Dictionary<string,HistoricPerspective> perspectives
```

Deeds become entity properties and list properties on the player entity; the gospel is
generated from those the same way sultan gospels are.

### Gospel text is spice + perspective, not a text field

```
HistoryKit.HistoricPerspective
    string entityId · long eventId · int feeling
    string mainColor · string supportColor
```

There are **no `gospelText`/`tombText` fields** — a perspective is *whose view, of which
event, how they feel, what colours render it*, held per-event in
`HistoricEvent.perspectives`. The differing text is selected from `HistorySpice.json` using
that attitude.

So "wanderer gospels" is: **a perspective key + spice branches keyed on feeling.** That is
Tier 2-light — the same `[HasModSensitiveStaticCache]` / `[ModSensitiveCacheInit]` path the
lore-expansion v0.1 spike uses. Cheaper than §2.3 assumed, and it composes with that project
rather than duplicating it.

### Persistence

`XRL.IScribedSystem` (with `Write`/`Read`) is the vehicle for anything that must survive
inside a save. For state that must survive *across* saves — which is what legacy needs — a
scribed system still won't cross character boundaries; that part remains a file written
beside the save, as §3.1 assumed.

### The exclusion filter has an obvious implementation

Your painted/engraved rule needs to identify authored objects. Relevant surface exists —
`XRL.World.Parts.WaterRitualRecord` shows this codebase tracks provenance on parts, and the
paint/engrave/name features are all parts or properties on the object. Enumerate and exclude
by part presence rather than by string-matching display names.

---

## 4. Water covenant — a record already exists

```
XRL.World.Parts.WaterRitualRecord
XRL.World.Parts.WaterRitualDiscount
XRL.World.WaterRitualStartEvent
XRL.World.GetWaterRitualCostEvent
XRL.World.GetWaterRitualLiquidEvent
XRL.World.GetWaterRitualReputationAmountEvent
XRL.World.GetWaterRitualSecretWeightEvent
XRL.World.GetWaterRitualSellSecretBehaviorEvent
XRL.World.Conversations.Parts.IWaterRitualPart          ← extension point
XRL.World.Conversations.Parts.IWaterRitualSecretPart    ← extension point
  + WaterRitualBegin / BuyItem / BuySecret / SellSecret / LearnSkill /
    CookingRecipe / TinkeringRecipe / GainMutation / RandomMutation /
    JoinParty / SkillPoint / HermitOath / FungusColonize / NephilimPacify
```

Three things follow.

**`WaterRitualRecord` is a part**, so the game already records who you have shared water
with, per creature. The covenant design does not need to build a kinship registry — it needs
to read and extend one.

**`IWaterRitualPart` / `IWaterRitualSecretPart` are interfaces**, and every vanilla ritual
option is implemented as a conversation part against them. That is a designed extension
point: new covenant options ("ask for sanctuary", "call for aid") are **new conversation
parts**, not a menu rewrite. This is the cleanest integration surface in any of these docs.

**`GetWaterRitualReputationAmountEvent` exists**, so the reputation yield of a ritual is
already interceptable — relevant if bond depth should modulate it.

---

## 5. Sleep — confirmed as written

`XRL.World.Effects.Asleep` extends `XRL.World.Effect`; `Wakeful` exists as its own effect.
`EndTurnEvent` was already documented. The design in `DESIGN_sleep.md` needs no structural
change — only the §7 caveat removed.

The gas-sleep exclusion the doc calls the most important interaction is straightforward:
`XRL.World.Parts.GasSleep` and the `CookingDomainBreathers_UnitBreatheSleepGas*` effects are
distinct types from voluntary sleep, so "did this sleep come from gas?" is answerable by
source rather than by guesswork.

---

## 6. What is still unknown

Metadata gives structure, not behaviour. Genuinely open:

- Whether `QudHistoryFactory` builds its event pool by reflection or a hardcoded list
  (no registry field — leans hardcoded)
- Whether the relic-naming call site populates the variable bag with anything event-derived
- Whether history generation can be driven headlessly without a loaded world
- Whether Harmony works on this Mac under Rosetta (needs a live launch, not static analysis)

All four need IL. `ilspycmd` on a machine with the .NET SDK, or ILSpy on the Windows box.
