# Naming Derivation Specification

> Scope: relics and sultan-associated items. Sultan *personal* names are explicitly out of
> scope — that niche is already served by the Workshop mod *Sultan's Names of Qud*, and
> volume expansion is not this mod's proposition.

---

## 1. The thesis

A generated name reads as generated when it is **assembled** rather than **earned**.

Vanilla already derives the relic's *item type* from history: a weapon from a battle, a gift
from a wedding. The gap is that the **name** is produced by an independent process that
draws adjectives and nouns from wordlists. The name therefore references *who* — a sultan —
but never *what happened*. It is a label glued onto an object.

The fix is one sentence: **the name must reference a fact that exists elsewhere in the
record.** Not a fact-shaped word. An actual referent — a place, a person, a deed, a debt —
that the player can encounter again somewhere else and match.

This is why the naming work depends on the event model. Before `DESIGN_history_events.md`, there is
almost nothing in the record specific enough to name something after. After it, every relic
arrives carrying a ledger, a set of threads it participated in, and a list of stable
`PlaceRef` / `EntityRef` handles.

---

## 2. Input contract

At the moment of naming, the generator must have access to:

```
NamingContext {
  origin_event   : EventInstance     # the event that produced the object
  ledger_at_time : LedgerSnapshot    # state when the object entered the record
  threads_open   : List<Thread>      # what was unresolved at that moment
  threads_touched: List<Thread]      # what this object participated in later
  sultan         : SultanRef
  era            : Era               # cosmic / blended / earthen
  item_type      : ItemType          # already derived by vanilla
}
```

**Open question:** whether such a seam exists — whether the originating event is still in
scope when the name is produced, or whether naming happens later from a stripped record.
This is recon question #2 in `DESIGN_history_implementation.md` §2 and it gates the entire document. If
no seam exists, the fallback is §7.

---

## 3. Derivation patterns

Six patterns, in rough order of preference. Each draws its content from `NamingContext`; a
pattern is only eligible if its required referent is present.

### 3.1 Place-bound

`the <PlaceRef> <Noun>` · `the <Noun> of <PlaceRef>`

Requires a `PlaceRef` from `origin_event.introduces` or `ledger.location`.

> *the Cistern Oath* · *the Salt Road Knife* · *the Second Cup of Ubel*

The workhorse pattern, and the best one. Places recur in the record more than any other
referent type, so place-bound names have the highest chance of the player encountering the
referent again — which is the whole payoff (P6).

### 3.2 Thread-bound

`the <ThreadKind-derived Noun>` · `<Verb-agent> of the <Thread referent>`

Requires a thread in `threads_touched`.

> *the Ransom* · *the Oathkeeper* · *the Unpaid Half* · *Drowner of the Ninth Claim*

Names an object after the *obligation* it was entangled in rather than the physical
circumstance. Produces the most evocative results and the most opaque ones, so it should be
weighted below place-bound and gated on the thread being referenced elsewhere.

### 3.3 Deed-genitive

`<Agent-noun> of <Object/Place>`

Requires the origin event to be a `resolution` or `terminal` role — something was *done*.

> *Breaker of the Khan's Line* · *Keeper of the Free Water*

Strong, but it front-loads drama; over-use makes every relic sound like a legend. Cap at
roughly one per sultan.

### 3.4 Epithet-transfer

`the <Sultan epithet> <Noun>`

Requires a non-empty `ledger.epithets` — and critically, the epithet must have been *earned*
by a specific event, since epithets under this model carry their source event id.

> If a sultan earned "the Salt-Drinker" by surviving a poisoned well, a relic from that
> chain may be *the Salt-Drinker's Bowl*. The player who has read the well event recognises
> the bowl instantly.

### 3.5 Understatement

`the <Plain adjective> <Plain noun>` — *with a qualifier that is only meaningful in context*

> *the Long Knife* · *the Second Cup* · *the Quiet Treaty* · *the Third Well*

Deliberately unremarkable. This pattern exists to satisfy the plainness quota (§4) and to
create contrast. Ordinal qualifiers (*Second*, *Ninth*, *Third*) are especially valuable:
they imply a series the player has not seen, which reads as depth rather than as
decoration, and they cost nothing to generate.

### 3.6 Consequence

`the <Nominalised consequence>`

Requires the object to appear in an event that closed a thread badly.

> *the Peacebreaker* · *the Widowmaker of Ubel* · *the Unransomed*

---

## 4. The plainness quota

Per `DESIGN_history.md` §2.5, the register problem is that **every** token is exotic, so
obscurity becomes the baseline and stops signifying.

### 4.1 Two lexicons

Maintain **PLAIN** and **STRANGE** token sets, tagged by part of speech.

- **PLAIN** — iron, salt, long, quiet, water, road, cup, knife, well, stone, second, low,
  bright, hollow, red, ninth, cold, bridge, gate, thread
- **STRANGE** — the existing vanilla lexicon, essentially unchanged

The mod adds the PLAIN set. It does **not** need to add to STRANGE, and probably should not.

### 4.2 Composition rule

For every name of two or more lexical tokens:

| Mix | Target share |
|---|---|
| plain + plain | 55% |
| plain + strange | 35% |
| strange + strange | 10% |

**Hard constraint:** no name may be composed entirely of STRANGE tokens *unless* at least
one of them is a proper noun already present in the record. A referent earns its strangeness;
an adjective does not.

### 4.3 Why this works

At a 10% strange-strange rate, an unusual name arrives roughly once per ten relics and
reads as *significant*. At 100% — the current state — it reads as noise. The mod's most
noticeable single change may well be this ratio, and it is by far the cheapest thing in the
document to implement.

---

## 5. Cross-reference enforcement

The rule that makes the whole thing land, restated as an algorithm:

```
name ← derive(context)
refs ← extract_referents(name)

if refs is empty:
    reject; retry with a pattern requiring a referent

for r in refs:
    assert r ∈ world_record.referents      # P6 — must exist elsewhere
    assert render(r) == world_record.canonical_string(r)   # exact string match
```

The second assertion is not pedantry. If the record calls it "the Cistern of Ubel" and the
relic is named for "Ubel's Cistern," the player cannot match them and the cross-reference is
worthless. **Referent strings must be rendered once and reused**, never re-generated.

### 5.1 Minimum reference count per world

Target: **≥ 12 distinct proper nouns** appearing in both a relic name and at least one
historical account (`DESIGN_history.md` §6). Below roughly eight, the player never notices the
system exists; the effect is not linear in the count but has a threshold.

---

## 6. Uniqueness and anti-repetition

- **No epithet reused within a world.** Maintain a used-set; on collision, re-derive.
- **No pattern used more than twice consecutively.** Track the last three patterns.
- **Per-sultan pattern spread:** a sultan's relics should not all share a pattern. Penalise
  a pattern already used for that sultan.
- **Noun budget:** cap any PLAIN noun at 2 uses per world. *Knife* appearing five times is
  its own kind of formulaic — the failure this mod is meant to fix, reintroduced through a
  smaller vocabulary.

The last point is the real risk of the plainness quota, and it should be instrumented from
the start rather than discovered in Workshop comments.

---

## 7. Fallback ladder

Per P8, naming must never fail. In order:

1. **Full derivation** — a pattern from §3 with a verified cross-reference.
2. **Weak derivation** — a pattern using a referent from the record but not verified as
   appearing elsewhere. Acceptable; still better than vanilla.
3. **Site-bound** — vanilla's existing behaviour for lore-less relics: name from the
   historic site or floor. **Apply the plainness quota anyway** — this alone improves
   lore-less relics without touching history generation at all.
4. **Vanilla** — unchanged behaviour.

**Rung 3 is the v0.1 release.** It requires no access to history generation, no ledger, and
no event model — only the naming call site and two wordlists. It is the cheapest meaningful
improvement available and it is a complete, shippable mod on its own.

---

## 8. Anti-patterns

Explicit rejects. Any generated name matching these should be re-derived.

| Anti-pattern | Example shape | Why |
|---|---|---|
| Two exotic tokens, no referent | *the Gyrating Fulcrum* | The exact failure being fixed |
| Superlative without cause | *the Greatest Blade* | Nothing in the record earns it |
| Referent that appears nowhere else | *the Sword of Kh'ral* (Kh'ral unmentioned) | Breaks P6; worse than no reference |
| Sultan name alone | *Sultan X's Sword* | References *who*, not *what* — vanilla's flaw |
| Register mismatch with era | earthen noun in a cosmic-era name | Undermines an existing good system |
| Adjective uncorrelated with item type | *the Drowned Bow* | Reads as slot-filling |

That last one deserves emphasis: adjective–noun semantic agreement is a large share of why
current names read as random. *The Drowned Bow* is incoherent unless the record contains a
drowning **and** the bow was there. Under §5 it either has that grounding or it is rejected.

---

## 9. Worked examples

From the biography in `DESIGN_history_catalog.md` §7 — an item crafted from the remainder of a
ransom, later carried in a battle over the Cistern of Ubel.

| Pattern | Generated name | Referent verifiable at |
|---|---|---|
| Place-bound | *the Cistern Knife* | oath event, dispute event, battle event |
| Thread-bound | *the Unpaid Half* | ransom debt, never fully discharged |
| Understatement | *the Second Cup of Ubel* | Ubel appears three times |
| Epithet-transfer | *the Oathkeeper's Blade* | epithet earned at the cistern oath |
| Consequence | *Widowmaker of Ubel* | battle event, khan's line |

Each of the five is checkable by a player who reads the sultan's history. Compare the
vanilla-shaped alternative — a two-token exotic assembly with no referent — which is
checkable against nothing, and which is the reason the naming looks obvious.

---

*Next:* `DESIGN_history_sources.md` — making the accounts disagree on purpose.
