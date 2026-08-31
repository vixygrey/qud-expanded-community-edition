# Compositional Event Model

> **Status:** design specification, not an implementation plan. Written against the
> generator's *published behaviour*, not its source. Every assumption about internals is
> marked **[ASSUMPTION]** and must be checked once the game is installed.

---

## 1. The core move

Today an event is a **template**: a bundle of text with slots, selected at random from a
pool of seventeen, rendered, and forgotten. Events neither require nor produce state, so
they are order-insensitive: shuffling a sultan's biography would lose no information.

Under this model an event becomes a **transformation on a ledger**. It declares what must
already be true for it to occur, and what becomes true afterward. Selection is then
constrained by what has happened, and order carries meaning.

The payoff is combinatorial. Seventeen independent templates produce seventeen recognisable
shapes. Seventeen templates that chain produce a space of *biographies* whose size grows
with chain length, because "captured by bandits" preceded by an exile and followed by a
ransom that bankrupts a province is a different narrative object from the same template
fired cold — even with byte-identical prose.

This is why **composition must precede expansion**. It is also why expansion is worth so
much more afterward: in a flat pool, adding thirteen templates takes you from 17 shapes to
30. In a composing system, each new template multiplies against every valid predecessor and
successor.

---

## 2. The ledger

The **ledger** is the accumulated state of one sultan's life, threaded through generation.
It is written by events and read by preconditions.

### 2.1 Fields

```
Ledger {
  # identity & standing
  titles          : Set<Title>          # heir, sultan, exile, general, apostate...
  epithets        : List<Epithet>       # earned, ordered, each tied to a source event
  temperament     : Temperament         # fixed at origin; biases selection (§5.3)
  piety           : Int  [-3..+3]       # drifts; read by religious events & sources
  legitimacy      : Int  [-3..+3]       # claim strength; gates succession events
  renown          : Int  [ 0..+5 ]      # scales magnitude of later events

  # relationships
  allies          : Set<EntityRef>      # factions, persons
  enemies         : Set<EntityRef>
  kin             : Set<EntityRef>      # spouses, heirs, siblings
  rival           : EntityRef?          # at most one *named* rival at a time

  # material
  holdings        : Set<PlaceRef>       # settlements, regions held
  possessions     : Set<ObjectRef>      # relics, artifacts — the naming substrate
  treasury        : Int  [-2..+3]       # debt through wealth

  # geography & time
  location        : PlaceRef            # where the sultan currently is
  regions_touched : Set<RegionRef>      # satisfies the coverage requirement
  age_band        : Enum{youth, prime, late}

  # the important one
  threads         : List<Thread>        # open narrative obligations — §3
  history         : List<EventInstance> # what has already happened
}
```

**[ASSUMPTION]** that a per-sultan mutable context can be threaded through generation at
all. If the vanilla generator is stateless by design, this is the single largest
implementation risk in the project, and `DESIGN_history_implementation.md` §2 treats it as the first
recon question.

### 2.2 Reference types

`EntityRef`, `PlaceRef`, `ObjectRef` and `RegionRef` are **stable handles**, not strings.
Each carries a canonical rendered name plus the id of the event that introduced it.

This matters more than it looks. Principle **P6** — every generated proper noun must be
cross-referenceable — is enforced here or nowhere. If a cistern is introduced by event 3
and referenced by a relic name in event 9, both must resolve to the same `PlaceRef` so the
strings agree exactly. Rendering the same referent through two independent name generators
is the current failure mode and must be structurally impossible under this model.

---

## 3. Threads — the load-bearing structure

A **thread** is an open narrative obligation: something that happened which the world has
not finished reacting to.

```
Thread {
  kind        : ThreadKind
  referent    : Ref            # who/what/where the obligation attaches to
  opened_by   : EventInstance
  urgency     : Int [0..3]     # rises with age; drives selection pressure
  tags        : Set<Tag>
}
```

### 3.1 Thread kinds

| Kind | Opened by | Discharged by |
|---|---|---|
| `debt` | ransom, levy, tribute, gift accepted | repayment, default, war of repudiation |
| `grudge` | betrayal, humiliation, defeat, kin harmed | revenge, reconciliation, the enemy's death |
| `oath` | vow, treaty, marriage compact, sacred pledge | fulfilment, breach, release |
| `prophecy` | omen, weird sky, ritual, dream | fulfilment, aversion, ironic inversion |
| `claim` | disputed succession, contested holding | coronation, cession, conquest |
| `absence` | exile, pilgrimage, capture, disappearance | return, death abroad, replacement |
| `wound` | injury, curse, mutation, contamination | healing, worsening, death by it |
| `heirless` | reign without succession | birth, adoption, naming a successor |
| `relic_lost` | object misplaced, stolen, buried, surrendered | recovery, destruction, discovery by another |
| `legacy` | *inherited from a previous sultan* — see §7 | veneration, iconoclasm, restoration |

Ten kinds is deliberate. Fewer and chains become repetitive in a new way; more and the
precondition matrix gets hard to author against.

### 3.2 Why threads rather than direct event-to-event links

A thread is an *indirection*. Direct links ("event B may follow event A") require an
O(n²) authoring matrix and break whenever the pool changes. Threads let each event declare
its requirements against a small vocabulary of obligation kinds, so a new event
automatically composes with every existing event that opens a compatible thread. **This is
what makes the expansion in `DESIGN_history_catalog.md` cheap.**

---

## 4. Event definition

```
EventType {
  id              : String              # prefixed, e.g. LX_OathSworn
  role            : Role                # §5.1
  weight          : Float               # base selection weight

  requires        : Predicate(Ledger)   # hard gate
  prefers         : List<(Predicate, Float)]   # soft bonuses
  forbids         : Predicate(Ledger)   # hard veto

  opens           : List<ThreadSpec>
  closes          : List<ThreadMatcher> # which open threads this discharges
  effects         : List<LedgerMutation>

  introduces      : List<RefSpec>       # new places/persons/objects entering the record
  region_relevant : Bool                # can satisfy coverage requirement
  age_bands       : Set<AgeBand>
  era_affinity    : Map<Era, Float>     # cosmic/blended/earthen weighting

  renderings      : Map<SourceType, Template>   # see DESIGN_history_sources.md
}
```

### 4.1 On `closes`

An event that closes a thread is the payoff of the whole design. `closes` is a *matcher*,
not a hard requirement — most events should be able to fire with or without discharging
something, but discharge should be heavily rewarded in selection (§5.2). This keeps the
system from deadlocking when no eligible closer exists.

### 4.2 On `introduces`

Every proper noun a rendering can mention must be declared here or already present in the
ledger. **A rendering may not invent a referent inline.** This is the enforcement point for
P6 and, downstream, for the naming spec — a relic can only be named after a cistern if some
event actually put a cistern in the record.

---

## 5. Selection

### 5.1 Roles and the arc

Each event type carries a **role** describing its function in a life:

| Role | Function | Typical share |
|---|---|---|
| `origin` | fixed opener | 1 per life |
| `inciting` | opens threads, introduces referents; cheap, low magnitude | ~25% |
| `escalation` | raises stakes on an existing thread without closing it | ~20% |
| `complication` | opens a second thread while an earlier one is still open | ~15% |
| `reversal` | inverts standing — fortune, allegiance, or legitimacy | ~10% |
| `resolution` | closes one or more threads | ~20% |
| `terminal` | death; closes or pointedly fails to close | 1 per life |

Vanilla's seventeen are overwhelmingly `escalation`-shaped set-pieces with no `inciting` or
`resolution` counterparts. That imbalance is the structural reading of "formulaic," and
`DESIGN_history_catalog.md` addresses it directly.

Selection targets a **role curve** across the biography rather than uniform sampling: more
`inciting` early, more `resolution` late, `reversal` weighted toward the middle third.

### 5.2 Scoring

For each candidate event type passing `requires` and not tripping `forbids`:

```
score = base_weight
      × role_fit(role, arc_position)          # from the role curve
      × era_affinity[current_era]
      × (1 + DISCHARGE_BONUS × closes_count × max_urgency)
      × repetition_penalty(type, world, life)
      × temperament_fit(ledger.temperament)
      × Π prefers_bonuses
```

`DISCHARGE_BONUS` is the single most important tuning constant in the system. Too low and
threads accumulate unresolved and the output reads as chaotic; too high and every biography
becomes a mechanical open-close-open-close metronome, which is a *new* kind of formulaic.
Suggested starting value ≈ 1.5, tuned against the "share of events in a chain" metric with
a target near 55–65% rather than 100%. **Some threads should stay open forever.** A life
with a loose end is more mythic than one that ties off neatly, and leaving roughly a third
unresolved is closer to how Qud's existing register actually reads.

### 5.3 Temperament

Assigned at origin, fixed for life, biases selection across the whole biography:

`zealot · pragmatist · conqueror · builder · recluse · trickster · martyr · dynast`

Eight temperaments over the same pool is the cheapest available source of structural
variation — two sultans drawing identical event types will chain them differently because
their preference weights differ. This is the intended replacement for era-vocabulary as the
primary differentiator, and it costs almost nothing to author.

### 5.4 Anti-repetition

Two independent mechanisms:

- **Per-world type budget.** Each event type carries a soft cap (default 2) on firings per
  *world*, not per sultan. Exceeding it applies a steep multiplicative penalty rather than a
  hard block, so the generator degrades gracefully when the eligible pool is thin.
- **Shape hashing.** Hash the last *k* events as a (role, thread-kind) tuple sequence and
  penalise candidates producing a shape seen recently in this world. This catches the case
  where different event *types* produce structurally identical passages — the failure mode
  that pure type-counting misses, and the one most responsible for "same pattern reused."

---

## 6. Generation algorithm

```
generate_biography(sultan_index, era, rng):
    ledger ← seed_origin(sultan_index, era, rng)
    target_length ← rng.range(11, 14)

    while len(ledger.history) < target_length - 1:
        arc_pos   ← len(ledger.history) / target_length
        candidates ← [e for e in POOL if e.requires(ledger) and not e.forbids(ledger)]
        candidates ← filter_age_band(candidates, ledger.age_band)

        if candidates is empty:
            candidates ← FALLBACK_POOL          # P8: fail toward vanilla

        chosen ← weighted_choice(candidates, score(·, ledger, arc_pos), rng)
        apply(chosen, ledger, rng)
        age_threads(ledger)                     # urgency += 1 on each open thread

    ensure_region_coverage(ledger, rng)         # vanilla requirement, preserved
    chosen_death ← select_terminal(ledger, rng) # prefers closing highest-urgency thread
    apply(chosen_death, ledger, rng)
    return ledger
```

### 6.1 Notes

- `ensure_region_coverage` runs late, as in vanilla. Coverage events should be drawn
  preferentially from types that can *also* close an open thread, so the coverage
  requirement stops producing the disconnected filler it currently does.
- `select_terminal` preferring the highest-urgency open thread is what makes deaths feel
  earned: a sultan who incurred a blood-debt in his youth should be able to die of it.
- All randomness flows through a **seeded** `rng` — required both for reproducibility during
  tuning and per the wiki's own compatibility guidance.

---

## 7. Cross-sultan causality

The sultanate is a **sequence of five**, and the largest coherence win available is treating
it as one. At present each biography is generated in isolation, so the dynasty is five
unrelated lives that happen to share a throne.

Proposal: a **dynastic ledger** persists across sultans, carrying a reduced subset —
`holdings`, `enemies`, surviving `kin`, unresolved `legacy` threads, and the `possessions`
that became entombed relics.

Each sultan after the first draws 1–2 events from a `legacy` role, reacting to a predecessor:

- venerating or canonising them
- iconoclasm — destroying their monuments, striking their name from inscriptions
- recovering, or losing, one of their relics
- honouring or repudiating one of their treaties
- avenging or completing an unresolved grudge

This is disproportionately valuable for three reasons. It converts the era-vocabulary drift
from a cosmetic gradient into a *narrative* one; it gives relics a second life in the record
(a relic mentioned twice, centuries apart, is worth more than two relics mentioned once);
and iconoclasm gives an in-fiction license for genuine contradiction between sources, which
`DESIGN_history_sources.md` then exploits directly.

**[ASSUMPTION]** that the five sultans are generated in chronological sequence within one
pass. If they are generated independently or in parallel, this section needs rework.

---

## 8. Retrofitting the vanilla seventeen

The seventeen existing types are retained and given model metadata rather than replaced.
Full table in `DESIGN_history_catalog.md` §2. The retrofit rules:

1. **Preserve all existing text.** Retrofit assigns preconditions, effects and threads; it
   does not rewrite prose. This keeps 0.2 shippable without a writing pass and keeps the
   diff reviewable.
2. **Assign the least restrictive `requires` that is still meaningful.** Over-constraining
   the vanilla pool starves the generator before any new events exist to fill the gap.
3. **Prefer `opens` over `closes` on retrofit.** The vanilla seventeen are set-pieces; most
   naturally *create* obligations. Discharge is what the new connective events are for.
4. **Any vanilla type that cannot be sensibly retrofitted keeps `requires: always`** and
   participates as an unconstrained filler. Graceful degradation over forced modelling.

---

## 9. Failure modes to watch

| Failure | Symptom | Mitigation |
|---|---|---|
| Thread starvation | Chains never close; output reads as chaotic | Raise `DISCHARGE_BONUS`; add resolution-role events |
| Metronome | Every life is open-close-open-close | Lower `DISCHARGE_BONUS`; allow permanent threads |
| Pool starvation | `requires` too strict, generator falls to fallback constantly | Loosen retrofit predicates; instrument fallback rate |
| Shape collapse | Different types, identical structure | Shape hashing (§5.4) |
| Referent explosion | Too many proper nouns; none recur | Cap `introduces`; prefer reusing existing refs |
| Determinism break | Same seed, different world | Route all randomness through seeded rng |

The instrumentation in `DESIGN_history_implementation.md` §5 exists to detect each of these before
release rather than from Workshop comments after it.

---

*Next:* `DESIGN_history_catalog.md` — the role grid, the retrofit table, and candidate new events.
