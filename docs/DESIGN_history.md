# World history and relic naming — design overview

**Scope:** Qud's sultan history and relic naming systems.
**Where it ships:** this mod. Settled in #178 under the charter's *One mod, not a constellation*;
these documents were written for a separate Workshop item called `lore-expansion` and predate that
decision, so the framing elsewhere in the set has not caught up yet.
**Status:** design done, recon done, no implementation. The work is #730 (naming) and #731 (events).

---

## 1. The complaint, stated precisely

Two observations motivate this mod:

1. **Sultan histories feel formulaic.** The same structural patterns recur within a
   single playthrough, and are exhausted within two or three.
2. **Generated names read as generated.** Relic and sultan item names are
   recognisable as adjective-plus-noun assemblies drawn from wordlists, with no
   apparent connection to anything else in the world.

These are usually treated as separate complaints. They are the same complaint. In both
cases the system is **sampling from a flat pool** rather than **deriving from a record**,
and players detect flat sampling very quickly.

## 2. Diagnosis

### 2.1 The pool is too small for the number of draws

Per the wiki's description of the generator, each sultan's biography is assembled as:

| Stage | Count |
|---|---|
| Origin event | 1 |
| Core life events, drawn from **17 types** | 8 |
| Ascension event (if not yet ruler) | 0–1 |
| Regional coverage events | variable |
| Death event | 1 |

Total per sultan: 10–22 events, typically 11–14. **Five sultans per world.**

That yields roughly **40 core event instances per world drawn from a pool of 17 types**.
Under uniform sampling the expected number of *distinct* types seen in a world is about
16 of 17 — that is, a single playthrough shows you effectively the entire pool, and shows
most types two or three times.

This is the whole problem in one line. No amount of prose polish conceals a 17-item pool
sampled 40 times. Pattern recognition is not a failure of the player's charity; it is the
correct inference from the evidence available.

### 2.2 Variation is lexical, not structural

The generator's principal axis of differentiation between sultans is **vocabulary register
by era** — early sultans draw on cosmic language (star, temple, empyrean), late sultans on
earthen language (sand, salt, trash sea), with the middle sultan blending both.

This is a genuinely elegant touch, and it is doing work it cannot sustain. Two sultans can
have biographies of *identical shape* that differ mainly in word choice. The result is the
specific sensation described in the complaint: the same pattern, reused, with different
obscure words in the slots. Lexical variation is being asked to substitute for structural
variation, and it cannot.

### 2.3 Events do not compose

The seventeen core types are, with few exceptions, **self-contained set-pieces**: a battle,
a rampage, a marriage, a coronation challenge. Nothing about a rampage requires a prior
cause, and nothing about it demands a subsequent consequence. Events are therefore
interchangeable and order-insensitive — which is precisely why order conveys no meaning and
every biography reads as a shuffled list rather than a life.

### 2.4 Names reference the wrong thing

Relic naming already has a partial link to history: when a relic derives from sultan lore,
the *item type* is chosen to fit the narrative (a weapon from a battle, a gift from a
wedding). Relics without lore fall back to being named after the historic site or floor
where they are found.

So the object is derived from the event, but the **name** is not. The name references
*who* (a sultan) but never *what happened*. It is a label applied to an object rather than
a residue left by an event — and a label assembled from a wordlist is exactly as arbitrary
as it looks.

### 2.5 Register uniformity

Every component of a generated name is drawn from the same exotic lexical bucket, so
nothing in the name is plain. Real onomastic corpora are overwhelmingly mundane with
occasional strangeness — *the Iron Bridge*, *the Long Peace*, *the Salt Road* — and the
strangeness registers **because it is surrounded by plainness**. When every adjective is
obscure, obscurity becomes the baseline and reads as noise rather than as strangeness.

Widening the wordlist does not fix this. Adding a plain register does.

> **Note on prior art:** the Workshop mod *Sultan's Names of Qud* already expands sultan
> name combinations from 2,184 to 19,680 by adding prefixes, infixes and suffixes drawn
> from Egyptian and Persian royal names. That niche is occupied, and it is the shallow fix
> regardless. This mod's proposition is **derivation, not volume**.

---

## 3. Design principles

These are the constraints every downstream decision should be checked against.

**P1 — Derive, don't sample.**
Wherever a fact already exists in the record, use it instead of drawing from a wordlist.
Names, murals, gossip and site descriptions should be *functions of history*, not
independent generators that happen to run nearby.

**P2 — Meaning lives in position, not text.**
What makes an event feel distinct is its place in a causal chain, not its prose. An event
that discharges a debt incurred four events earlier is a different event from the same
template fired cold, even with identical wording. This is why composition beats expansion.

**P3 — Expand only after composing.**
New templates authored in a flat format must be retrofitted later. Build the compositional
framework against the existing seventeen first. See §4.

**P4 — Preserve the register; fix the grounding.**
The goal is not to make Qud's history sober or realistic in a mundane sense. Qud's
surrealism is load-bearing and deliberate — the designers have written about choosing
evocative non-causality on purpose. The goal is that strangeness read as **motivated**
rather than **arbitrary**. Same tone, different provenance.

**P5 — Contradiction is a feature if it is sourced.**
Three accounts that differ randomly read as a bug. Three accounts that differ in ways
traceable to who was speaking and what they wanted read as history. Do not eliminate
inconsistency; attribute it. See `DESIGN_history_sources.md`.

**P6 — Every generated proper noun must be cross-referenceable.**
If a relic is named for a cistern, that cistern must appear elsewhere in the record under
the same name. This single rule converts more perceived incoherence than any prose change,
because it lets the player *verify* that the world hangs together.

**P7 — Plainness quota.**
No name may be assembled entirely from the exotic lexicon. See `DESIGN_history_naming.md` §4.

**P8 — Fail toward vanilla.**
Any generation step that cannot satisfy its constraints falls back to current behaviour
rather than erroring. A Workshop mod that breaks worldgen breaks it at the least
recoverable moment in the game.

---

## 4. Current scope

### #730 — shipped

Plain-register relic-name forms are an optional, restart-scoped JSON merge. They are documented in
`docs/FEATURES.md` §48.

### #731 — record-only causal responses

The first history slice is deliberately smaller than the original compositional proposal:

- A separate embark module receives the completed history at
  `BOOTEVENT_AFTERINITIALIZESULTANHISTORY`.
- It may append a later **record-only** response to a safe vanilla event. It never changes a
  generated event, the generator's draw pool, or a world-facing entity.
- Its first candidate is `CapturedByBandits`' escape branch
  (`tombInscriptionCategory = EnduresHardship`). The response is a self-contained gospel about the
  later consequence of that escape.
- The option is new-world-scoped. Existing worlds and histories never change.

The module runs before world construction, so history is an input to worldgen rather than merely a
description of it. A response must not reclaim, relocate, create, or alter an entity, site, relic,
faction, region, or map state. The six vanilla event types that create a findable entity are outside
this slice. See #815 for the worldgen route.

### Deferred work

- Additional safe, place-revealing record-only responses depend on observed play of #731 and are
  tracked by #979.
- World-facing consequences, including any response to an entity-creating event, belong to #815.
- Generator replacement, draw-pool reweighting, and pruning vanilla events are not proposed by this
  feature.
- Source divergence, murals, gossip, relic derivation, and cross-sultan legacy remain design work,
  not part of #731.

---

## 5. Evidence and success criteria

The installed assembly establishes that vanilla draws eight events from seventeen hardcoded branches
for each of five generated sultans, then adds Resheph. A post-pass cannot change those draw
statistics, so the former distinct-type, repeat-rate, and 55% causal-chain targets do not measure
this feature.

| Criterion | Required result |
|---|---|
| Eligible coverage | Every eligible sultan gets exactly one response. |
| Ordering | The response is after its escape and before its terminal event. |
| Idempotence | Repeated boot dispatch adds no duplicate response. |
| Record-only boundary | The pass writes no world-facing state. |
| Legibility | The gospel makes sense when revealed before its antecedent. |
| Save safety | A generated response reloads as ordinary `HistoricEvent` data. |

Sultan gospels become independent journal notes revealed one random secret at a time. The response
therefore repeats enough of the earlier captivity or escape to be meaningful alone.

---

## 6. Settled questions

1. The hardcoded event pool cannot be extended by registration. Replacing it is out of scope.
2. `BOOTEVENT_AFTERINITIALIZESULTANHISTORY` is an unused, documented pass-through extension point.
3. Five generated sultans share one mutable `History`, and Resheph is added separately.
4. History generation precedes world construction. Record-only additions are safe only when they do
   not contradict a world footprint.
5. `HistoricEvent.Load` flattens subclasses to ordinary events while retaining event properties, so
   fieldless generated events are save-safe.

*Companion documents:*
`DESIGN_history_events.md` · `DESIGN_history_catalog.md` · `DESIGN_history_naming.md` · `DESIGN_history_sources.md` · `DESIGN_history_implementation.md`
