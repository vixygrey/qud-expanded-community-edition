# Handoff — start here

**Date:** 2026-08-14
**Phase:** design complete, recon mostly complete, first code spike scaffolded but **never
compiled or run**.

---

## Where things stand

Research and design were done in a separate session that could read the game's data files but
**could not compile anything or run the game**. So everything in `mod/` is unverified — it is
a starting point written against observed data structures, not working code.

| Area | Status |
|---|---|
| Diagnosis of the problem | **Done** — `DESIGN_history.md`, confirmed by recon |
| Design: event model, catalog, naming, sources | **Done** — docs 01–04 |
| Recon of game internals | **Mostly done** — `DESIGN_history_recon.md` |
| Decompilation of `Assembly-CSharp` | **Not done** — no .NET SDK in the prior sandbox |
| v0.1 spike | **Scaffolded, never compiled** — `mod/` |
| Metrics harness | **Not started** |
| Prose authoring | **Not started** (handled outside implementation) |

---

## Do this first

### 1. v0.1 is a data file — delete the spike

**This step used to say "make the v0.1 spike actually run". It should not run at all.**
`DESIGN_history_recon.md` §Q8 said a mod could not ship a `HistorySpice.json` that merges, and
that was wrong: `HistoryKit.HistoricSpice.Init()` walks `ModManager.ActiveMods` and merges any
mod file named `historyspice.json` into the tree with Newtonsoft's `JObject.Merge`.

So v0.1 is:

```
mod/HistorySpice.json
```

and nothing else. No C#, no `[ModSensitiveCacheInit]`, no reflection resolver, and no `TODO(Q9)`
— the unresolved symbol that step 1 existed to resolve is not needed, because there is nothing to
reach into. `mod/Scripts/LX_SpiceInit.cs` should be **deleted rather than finished**, and the
*WM Extended Mutations* precedent it was modelled on is a harder route to the same place.

**What the merge cannot do, which shapes the whole roadmap.** `MergeArrayHandling.Union` is
additive: new forms and vocabulary go in, and **vanilla's cannot be taken out**. Forms 7 and 8 of
`spice.history.relics.names` — the specific complaint this project exists to answer — cannot be
suppressed by a data file. Diluting them by adding alternatives is possible and is what v0.1 can
achieve; removing them still needs code, and that is a different and later question.

The full correction, including why the original recon missed it, is in `DESIGN_history_recon.md`
§Q8. Tracked as vixygrey/qud-expanded-community-edition#689.

Then: build, load, generate a world, and look at relic names. Success is qualitative at this
stage — do names read as less arbitrary?

### 2. Answer the outstanding recon questions

All need method bodies. ILSpy or `ilspycmd` against
`../Caves of Qud/CoQ.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll`.

| Q | Question | Why it matters |
|---|---|---|
| **Q2** | What variable bag does `HistoricStringExpander` accept, and is the originating event in scope when a relic is named? | **The gate on real derivation-based naming** — the core of the mod |
| **Q3** | Does `QudHistoryFactory` enumerate event types by reflection, or is the pool hardcoded? | Tier 2 vs factory replacement for the whole expansion |
| **Q5** | Are the five sultans generated in chronological sequence in one pass? | Gates cross-sultan legacy events |
| **Q7** | Can biography generation be invoked headlessly? | Determines how painful the metrics harness is |
| **Q9** | The `HistoricSpice` root accessor | Blocks the v0.1 spike (see above) |

Write answers into `DESIGN_history_recon.md` — keep it the single source of truth.

### 3. Optional, low priority: Q0

Whether Harmony works on the Mac. Launch with a known Harmony-using Workshop mod, once
natively and once forced through Rosetta (Get Info → Open using Rosetta). Check the log for
patch application vs a memory-protection error.

Low priority **because nothing on the near-term path needs Harmony** — v0.1 and most of v0.2
are Tier 2-light. Worth knowing before v0.3 planning.

---

## What was learned in recon that contradicts the design docs

Docs 00–05 were written before the game was inspected. Four findings supersede them; the
revisions table at the end of `DESIGN_history_recon.md` lists the specific edits.

1. **The prose is data.** All history and naming text is in `HistorySpice.json`, a recursive
   substitution grammar. Event *logic* is C# (`XRL.Annals`); event *text* is not.
2. **Era vocabulary is token substitution**, not per-register strings. Authoring cost for the
   whole project **halves** — ~64 fragments, not ~128.
3. **Qud already has a coherence axis, and it's thematic.** The `elements` system (11 domains:
   glass, salt, stars, circuitry, chance…) threads motifs through a sultan's life. This mod
   should add a *causal* axis alongside it, **not replace it**.
4. **A ledger and a perspective model already exist in embryo.** `HistoricEntity` +
   `SetEntityProperty` / `MutateListProperty` / `AddEntityListItem` look like the ledger in
   `DESIGN_history_events.md` §2. `HistoricPerspective` + `gospelText` / `tombText` look like the
   source model in `DESIGN_history_sources.md`. **Extend these rather than building parallel structures.**

Point 4 in particular means `DESIGN_history_events.md`'s biggest flagged risk — "the generator may be
stateless" — is probably not real.

---

## Facts worth not rediscovering

- **The relic grammar is `spice.history.relics.names`** — 8 forms. Forms 7
  (`<noun>-<noun>`) and 8 (`<adjective> <noun>`) are pure random assembly with no grounding.
  **They are the specific cause of the complaint that started this project.**
- **Vocabulary is large:** ~280 adjective terminals, ~488 noun terminals. Form 8 alone can
  produce >100,000 distinct names and still reads as generated. Adding words will not help.
- **Existing plain-ish pools you can use immediately:** `spice.basicColors` (13),
  `spice.metals` (23). Both are already plain register.
- **`spice.ordinal` is numeric** (`1st`, `2nd`) — the spike adds word ordinals separately.
- **Event classes:** ~24 sultan, 12 village, 16 Resheph-specific, all in `XRL.Annals`.
- **Village history uses the same machinery** as sultan history — extending there later is
  much cheaper than the docs assumed.
- **Build target:** `netstandard2.0`, C# 9, per the game's own `Mods.csproj.template.txt`.
- **`manifest.json` uses lowercase keys** in the shipped DLC (`id`, `title`, `version`,
  `author`, `tags`, `loadOrder`, `previewImage`); community mods use PascalCase and also
  work, so it appears case-insensitive.

---

## Things deliberately not done

- **No prose written.** The ~64 event fragments are authored separately, in Qud's voice.
  Don't generate filler to make something compile — stub and flag.
- **No Harmony.** Nothing needed it yet. See the policy in `CLAUDE.md`.
- **No metrics harness.** Blocked on Q7, and not needed until v0.2.
- **Docs 00–05 not yet revised** against recon. Do this when touching the relevant subsystem,
  not as a batch.

---

## Definition of done for v0.1

- Mod loads without errors on a fresh world
- Relic names no longer use the two ungrounded forms
- A visible share of names use the plain register
- Nothing throws during worldgen under any seed tried
- `DESIGN_history_recon.md` updated with Q9's answer
