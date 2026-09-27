# Record-Only History Implementation

> **Status:** implementation specification for the record-only responses shipped through #731,
> #1008, and #1012. It supersedes this document's former pre-recon plan, which assumed an unavailable
> registry and retained a Harmony route that `docs/CHARTER.md` rule 5 forbids.

---

## 1. Boundary

Vanilla generates sultan history before it builds worlds. A history event can therefore name or move
an entity that later becomes a relic, site, faction, or other world-facing fact. The record-only pass
adds later event records without changing an existing event or any world-facing state.

Three source branches are implemented:

```csharp
event is CapturedByBandits
    && event.GetEventProperty("tombInscriptionCategory") == "EnduresHardship"

event is InspiringExperience
    && event.GetEventProperty("tombInscriptionCategory") == "HasInspiringExperience"
    && event.GetListProperties("elements") contains exactly one nonempty element

event is SecretRitual
    && event.GetEventProperty("tombInscriptionCategory") == "LearnsSecret"
    && event.GetListProperties("likedFactions") contains exactly one retained faction
```

The bandit murder branch (`Slays`) and the ritual rejection branch (`hatedFactions`) are not eligible.
The accepted sources may reveal regions and add an element or faction relationship, but create no
entity. A later reflection can therefore remain truthful without matching worldgen work.

The vanilla branches that create or relocate findable entities remain excluded. A response that
changes one of those entities belongs in #815, where the history and constructed world can change
together.

## 2. Extension point

`QudSpecificBootHandlersModule` generates and normalizes history, then dispatches both
`BOOTEVENT_INITIALIZESULTANHISTORY` and `BOOTEVENT_AFTERINITIALIZESULTANHISTORY` before world
construction. #731 uses the latter. It is a public, purpose-built pass-through hook; no Harmony,
reflection, type override, file I/O, or network access is involved.

Register a separate `QudExpandedCE.Vixy_HistoryModule` in `mod/Core/EmbarkModules.xml`. Do not add
it early to `EmbarkInfo.modules`: `Vixy_NameFlavourModule` deliberately does that for character-name
rerolls and is consequently dispatched twice. A history module must remain normally registered and
also carry an exactly-once guard.

## 3. Option and idempotence

Add `OptionQudExpandedCEHistoryEvents` as a checkbox. It defaults to `No` and its help text must say
that it affects only worlds created after enabling it. The module reads the option while handling the
history boot event.

Use a private, namespaced `The.Game` integer state key. The handler must:

1. return the incoming element unless it is a `History`;
2. return it when the option is off or the state key is already set;
3. prepare valid responses without mutating history;
4. append the responses only after preparation succeeds;
5. set the state key after every response has been appended.

An exception or an invalid candidate skips the response and leaves vanilla history usable. The pass
must not leave a partial record for a sultan.

## 4. Response construction

For every generated sultan, select at most one source of each eligible type deterministically.
Inspiration and ritual selection use the earliest event by `(year, id)`; ritual additionally requires
the faction relationship to survive in the final snapshot. A response is valid only if it can be
assigned a year after its source event and before that sultan's terminal event.

Create a plain `HistoricEvent` with only event-local properties:

- `gospel`: a complete line that names the sultan and restates enough of the source experience to
  make its later consequence intelligible alone;
- a private `Vixy_` marker property identifying the source and preventing duplicate responses.

Do not write entity properties, entity list properties, `revealsRegion`, `revealsItem`, factions,
locations, tomb categories, or world-generation data. Do not add subclass fields. `HistoricEvent.Load`
restores a plain event plus its persisted property dictionaries, which is the save-safe shape.

`GenerateVillageEraHistory` has already converted calendar years and `a`/`an` forms before this hook
runs. The authored gospel must therefore avoid absolute years and article-sensitive unresolved nouns.
Use fully rendered source data rather than relying on that post-processing.

## 5. Journal and legibility

Every event with a `gospel` becomes its own `JournalSultanNote`. Sultan notes enter the random secret
pool independently, so a player can discover a response before discovering the source it answers.
Each response must be legible in that order. It cannot depend on a preceding note, tomb inscription,
or map discovery for its subject.

## 6. Verification

1. Compile `mod/Scripting/` with `python3 tools/compile_scripting.py` against the installed game.
2. Run `python3 tools/validate_mod.py`.
3. Create new worlds with the option disabled and enabled. Use recorded seeds containing each
   eligible source branch.
4. Verify one response of each qualifying type per eligible sultan, valid chronology, deterministic
   inspiration and ritual selection, and no duplicate after repeated dispatch.
5. Inspect each source and the world output to confirm no entity, location, element, faction
   relationship, region, or relic contradiction.
6. Save and reload the generated world, then verify each response remains an ordinary history record.
7. Reveal each response through the Sultan journal flow and review it without its antecedent.

No permanent test harness is required unless an uncertain edge case survives this smoke test. Remove
any temporary diagnostic code before release.

## 7. Deferred work

- Further safe record-only chains are selected one source and branch at a time under #979.
- Entity-creating event responses and any consequence players can walk to are #815.
- Replacing, pruning, or reweighting `QudHistoryFactory` is out of scope.
- The original ledger, source-divergence, and cross-sultan proposals remain design material only.
