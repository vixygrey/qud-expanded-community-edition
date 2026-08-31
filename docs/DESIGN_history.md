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

## 4. Scope

### In scope

- A compositional event model with preconditions, effects and open threads
  (`DESIGN_history_events.md`)
- Retrofit of the existing seventeen event types into that model (`DESIGN_history_catalog.md`)
- An expansion of the event pool with **connective** event types (`DESIGN_history_catalog.md`)
- Derivation-based naming for relics and sultan items (`DESIGN_history_naming.md`)
- A source/divergence model for gospel, mural and tomb inscription (`DESIGN_history_sources.md`)
- Cross-sultan causality: later sultans reacting to earlier sultans' legacies

### Out of scope (for now)

- Village history generation — related, larger, and worth a separate mod
- Faction relation overhaul beyond what history already sets
- New historic site types or map generation changes
- Dialogue and gossip systems consuming history (desirable; deferred to a later release)
- Any change to Resheph, the fixed sixth sultan

### Explicit non-goals

- **Not** a wordlist expansion mod
- **Not** a tonal rewrite toward mundane realism
- **Not** a total-conversion of worldgen

---

## 5. Release staging

Sequencing chosen to put something shippable on the Workshop early, and to avoid
authoring content that later needs retrofitting.

| Version | Contents | Depends on |
|---|---|---|
| **0.1** | Naming derivation + plainness quota. Self-contained, high visibility per unit of work. Proves the approach and the mod's identity. | Access to naming call site |
| **0.2** | Compositional event model; vanilla 17 retrofitted; no new events yet. Output should already feel different. | History generation hook |
| **0.3** | Event pool expansion — connective tissue events. | 0.2 |
| **0.4** | Source divergence model. | 0.2 |
| **0.5+** | Cross-sultan legacy events; consumers (gossip, murals) reading the record. | 0.3 |

Each version is independently shippable. If the project stalls after 0.1, 0.1 is still a
good mod.

---

## 6. Success metrics

Design intent should be measurable, otherwise "feels less formulaic" is unfalsifiable.
Proposed instrumentation (see `DESIGN_history_implementation.md` §5 for how to collect it):

| Metric | Vanilla baseline (est.) | Target |
|---|---|---|
| Distinct event types seen per world | ~16 / 17 | ≥ 22 / 35 |
| Mean repeats per event type per world | ~2.4 | ≤ 1.3 |
| Share of events participating in a causal chain (≥2 linked) | ~0 | ≥ 55% |
| Distinct cross-referenced proper nouns per world | low | ≥ 12 |
| Names containing ≥1 plain-register token | low | ≥ 85% |
| Names referencing a record fact | ~0 | ≥ 70% |

Baselines marked "est." are inferred from published descriptions of the generator and must
be measured directly once the game is installed.

---

## 7. Open questions

Carried into `DESIGN_history_implementation.md`; listed here so the design record is self-contained.

1. How much of the event text lives in shipped XML versus compiled into the assembly?
2. Is there a seam at which a relic is named where the originating event is still in scope?
3. Can the event pool be extended by registration, or does it require replacing
   `QudHistoryFactory` wholesale?
4. Does the era vocabulary system operate on tokens or on whole strings? This determines
   how much authoring each new event actually costs.
5. Are sultan biographies generated before or after the map, and can events therefore place
   sites rather than merely reference them?

---

*Companion documents:*
`DESIGN_history_events.md` · `DESIGN_history_catalog.md` · `DESIGN_history_naming.md` · `DESIGN_history_sources.md` · `DESIGN_history_implementation.md`
