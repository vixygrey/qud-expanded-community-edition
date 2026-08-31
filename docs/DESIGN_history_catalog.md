# Event Catalog — Role Grid, Retrofit, and Expansion

> Companion to `01-event-model.md`. All identifiers use the `LX_` prefix per the wiki's
> compatibility guidance on unique namespacing.

---

## 1. The role grid

The diagnosis in `00-overview.md` §2.3 says the vanilla pool is structurally lopsided. Here
is the shape of that lopsidedness, and what filling it requires.

| Role | Vanilla coverage | Needed | Gap |
|---|---|---|---|
| `origin` | 2 variants (heir / foundling) | 2–4 | small |
| `inciting` | ~2 of 17 | ~8 | **large** |
| `escalation` | ~9 of 17 | ~8 | none — oversupplied |
| `complication` | ~2 of 17 | ~5 | moderate |
| `reversal` | ~2 of 17 | ~5 | moderate |
| `resolution` | ~1 of 17 | ~8 | **large** |
| `terminal` | death variants | 4–6 | small |
| `legacy` | none | ~5 | **absent** |

The generator is almost entirely middle. It has spectacles but very few beginnings and
almost no endings-of-things — which is exactly why events feel interchangeable: with
nothing to open a thread and nothing to close one, every event is a middle with no
surrounding arc.

**The expansion should therefore be roughly 60% `inciting` and `resolution`.** Adding more
spectacles — more battles, more rampages — would make the problem *worse* by deepening an
already oversupplied role.

---

## 2. Retrofit table — the vanilla seventeen

Per `01-event-model.md` §8: assign metadata, preserve all existing text, prefer permissive
predicates. `requires` is written informally here; `∅` means unconditional.

| # | Vanilla event | Role | `requires` | `opens` | `closes` |
|---|---|---|---|---|---|
| 1 | Corrupt Minister | complication | has `holdings` | `grudge`(minister), `debt` | — |
| 2 | Captured by Bandits | reversal | `location` outside holdings | `absence`, `debt`(ransom) | — |
| 3 | Inspiring Experience | inciting | ∅ | `oath` \| `prophecy` | — |
| 4 | Meet Faction | inciting | ∅ | — (introduces `EntityRef`) | — |
| 5 | Secret Ritual | inciting | `piety` ≥ 0 | `prophecy`, `oath` | — |
| 6 | Challenge Sultan | escalation | not yet sultan | `claim`, `grudge` | — |
| 7 | Crafted Item | inciting | ∅ | — (introduces `ObjectRef`) | `prophecy` (if foretold) |
| 8 | Under Weird Sky | inciting | ∅ | `prophecy` | — |
| 9 | Army at the Gates | escalation | has `holdings` | `claim` \| `grudge` | — |
| 10 | Rampage Region | escalation | ∅ | `grudge`(region) | `grudge` (if vengeance) |
| 11 | Gathering Place | inciting | ∅ | — (introduces `PlaceRef`) | — |
| 12 | Faction Battle | escalation | has `enemies` | `grudge` | `grudge` (if decisive) |
| 13 | Tavern Misfortune | complication | ∅ | `grudge` \| `debt` | — |
| 14 | Bloody Battle | escalation | has `enemies` | `wound`, `grudge` | `claim` (if decisive) |
| 15 | Chariot Incident | complication | ∅ | `wound` \| `grudge` | — |
| 16 | Power Shift | reversal | is sultan | `claim` | `claim` |
| 17 | Marriage | resolution | no living spouse | `oath`, `heirless` | `grudge` (if political) |

### 2.1 What this table already buys

Even with **zero new events**, the retrofit alone should produce a visible change, because
selection stops being uniform. *Bloody Battle* now requires an enemy, so it can no longer
appear before anyone has been made an enemy. *Marriage* can close a political grudge, so it
lands as a settlement rather than as a non-sequitur. *Captured by Bandits* opens a ransom
debt that a later event can discharge.

**This is v0.2 and it should be shipped and evaluated before any writing begins.** If the
retrofit alone moves the "share of events in a chain" metric above ~35%, the expansion is
strongly justified. If it does not, something in the model is wrong and it is far better to
learn that before authoring fifty prose fragments.

### 2.2 Oversupply note

Items 6, 9, 10, 12, 14 are five distinct escalation-role combat set-pieces. Under the
per-world type budget (`01-event-model.md` §5.4) these will now compete with each other
rather than all firing, which by itself should reduce the "constant war" texture of vanilla
biographies.

---

## 3. Core expansion — the twelve

Priority set for v0.3. Chosen to fill the `inciting` and `resolution` gaps, and to be
maximally *connective* — each one composes with many existing types rather than standing
alone. Ordered by value-per-unit-of-writing.

### 3.1 Inciting

**`LX_OathSworn`** — the sultan swears a vow before witnesses at a named place.
`requires:` ∅ · `opens:` `oath` · `introduces:` `PlaceRef`, optional `EntityRef` (witness)
· `effects:` `piety +1`
The single highest-value addition. Oaths are the most versatile thread kind: they can be
fulfilled, broken, or transmuted, and every outcome is narratively legible. Also the
cheapest naming substrate in the system — see `03-naming.md` §3.2.

**`LX_DebtIncurred`** — a gift accepted, a loan taken, a levy raised against future spoils.
`requires:` ∅ · `opens:` `debt` · `effects:` `treasury +1`, creditor → `EntityRef`
Gives the treasury field meaning and sets up repudiation, the best `reversal` fuel.

**`LX_RivalNamed`** — a specific person is elevated from circumstance into an antagonist.
`requires:` `rival` is null · `opens:` `grudge` · `effects:` sets `ledger.rival`
Vanilla has factional enemies but essentially no *persons*. A named rival who recurs across
four events and finally kills or is killed by the sultan is the strongest single coherence
signal available, and it costs one event type.

**`LX_WaterRightsDispute`** — a claim over a cistern, well, or watering hole.
`requires:` has `holdings` · `opens:` `claim` or `grudge` · `introduces:` `PlaceRef` (water
source)
Deeply Qud-appropriate — water is the setting's currency and its sacrament. Also generates
the most naturally *plain-register* proper nouns in the system, which the naming spec needs
(P7).

### 3.2 Resolution

**`LX_BloodPricePaid`** — restitution rendered for a killing or a humiliation.
`requires:` open `grudge` · `closes:` `grudge` · `effects:` `treasury -1`, `legitimacy +1`
The general-purpose grudge closer. Without something like this, grudges accumulate and
never discharge.

**`LX_TreatySworn`** — enmity converted into obligation.
`requires:` open `grudge` with a faction · `closes:` `grudge` · `opens:` `oath` ·
`effects:` enemy → ally
A closer that opens a new thread is structurally the most valuable kind of event: it
sustains chains instead of terminating them. Pairs with `LX_TreatyBroken` (§4) for the
long-range payoff.

**`LX_RelicRecovered`** — a lost object returns.
`requires:` open `relic_lost` · `closes:` `relic_lost` · `effects:` `possessions +=` object
Essential for making relics feel like they have provenance rather than merely existing.
Directly feeds the naming derivation, and the recovered object can be recovered *again* by
a later sultan (§5).

**`LX_AmnestyGranted`** — the sultan pardons a faction, region, or the rival.
`requires:` open `grudge`, `renown ≥ 2` · `closes:` `grudge` · `effects:` `legitimacy +1`
A non-violent resolution. The pool badly needs endings that are not killings — currently
almost every discharge available is a battle, which is itself a source of sameness.

### 3.3 Complication and reversal

**`LX_HostageTaken`** — kin or an heir held by another party.
`requires:` non-empty `kin` · `opens:` `absence`, `debt` · `effects:` `legitimacy -1`
Opens two threads at once, which is what `complication` is for.

**`LX_Exile`** — the sultan is driven out.
`requires:` `legitimacy ≤ 0`, is or was sultan · `opens:` `absence`, `claim` ·
`effects:` `titles += exile`, `holdings` cleared, `location` → distant region
The strongest reversal available, and it naturally satisfies region-coverage by relocating
the sultan — which is exactly the fix for coverage events currently reading as filler.

**`LX_BetrayalRevealed`** — an ally is discovered to have been working against the sultan.
`requires:` non-empty `allies` · `opens:` `grudge` · `effects:` ally → enemy,
`legitimacy -1`
Retroactively recolours an earlier event, which is a very cheap way to make prior text feel
intentional.

### 3.4 Terminal

**`LX_DeathOfAnOldWound`** — the sultan dies of an injury sustained long before.
`requires:` open `wound` with `urgency ≥ 2` · `closes:` `wound` · role: `terminal`
The clearest possible demonstration that the system works: a consequence arriving from
eight events away. Worth building the chain-viewer tooling (`05-implementation.md` §5) just
to confirm this fires correctly.

---

## 4. Extended set — deferred to v0.4+

Same model, lower priority. Listed so the design space is recorded, not because all should
be built.

| Id | Role | Requires | Opens | Closes |
|---|---|---|---|---|
| `LX_OmenRead` | inciting | ∅ | `prophecy` | — |
| `LX_HeirBorn` | inciting | has spouse | `claim` | `heirless` |
| `LX_ApprenticeTaken` | inciting | `age_band` = youth | — | — |
| `LX_SaltBlight` | escalation | has `holdings` | `debt` | — |
| `LX_TributeDemanded` | escalation | open `debt` | — | — |
| `LX_RumorSpread` | escalation | open `grudge` | — | — |
| `LX_SiegeLaid` | escalation | open `claim` | `wound` | `claim` |
| `LX_AssassinationFailed` | complication | has `enemies` | `wound`, `grudge` | — |
| `LX_TreatyBroken` | reversal | open `oath` w/ treaty tag | `grudge` | `oath` |
| `LX_Apostasy` | reversal | \|`piety`\| ≥ 2 | `grudge` | `oath` |
| `LX_TrialHeld` | resolution | open `claim` | — | `claim` |
| `LX_PilgrimageCompleted` | resolution | open `oath` \| `prophecy` | — | `oath`, `prophecy` |
| `LX_ReturnFromExile` | resolution | open `absence` | `claim` | `absence` |
| `LX_DeathAtRivalsHand` | terminal | `rival` set | — | `grudge` |
| `LX_DeathUnresolved` | terminal | ∅ | — | *nothing, pointedly* |

`LX_DeathUnresolved` is deliberate: per `01-event-model.md` §5.2, roughly a third of lives
should end with threads still open. It is the mythic register's natural ending and a
guardrail against the metronome failure mode.

---

## 5. Legacy events — cross-sultan

Per `01-event-model.md` §7. Each fires for sultans 2–5, reading the dynastic ledger. These
are disproportionately valuable per unit of writing because they make the *sultanate* a
coherent object rather than five unrelated lives.

| Id | Reads | Effect |
|---|---|---|
| `LX_Canonization` | predecessor's `epithets` | Predecessor venerated; `piety +1`; predecessor's relic gains a cult |
| `LX_Iconoclasm` | predecessor's monuments | Monuments destroyed, name struck from inscriptions; **licenses source contradiction** (see `04-sources.md` §5) |
| `LX_TombDesecrated` | predecessor's `possessions` | A relic leaves the tomb; opens `relic_lost` for a *later* sultan to close |
| `LX_TreatyInherited` | predecessor's open `oath` | Honoured or repudiated; if repudiated, opens `grudge` with a faction that remembers |
| `LX_OldGrudgeAvenged` | predecessor's open `grudge` | Closes a thread opened generations earlier |

`LX_TombDesecrated` → `LX_RelicRecovered` across two different sultans is the flagship
chain of this mod. A relic that is buried, stolen, and recovered a century later — under a
name that references all three events — is the most concrete possible answer to "the names
are obvious mashups."

---

## 6. Authoring cost

Per `00-overview.md` §2.2, every event needs a gospel rendering and a tomb-inscription
rendering, and each must work in cosmic and earthen vocabulary registers.

| Set | Types | Renderings each | Fragments |
|---|---|---|---|
| Core twelve (v0.3) | 12 | 2 sources × 2 registers = 4 | **48** |
| Extended (v0.4+) | 15 | 4 | 60 |
| Legacy (v0.5+) | 5 | 4 | 20 |
| **Total if all built** | **32** | | **128** |

**The prose is the project.** The model in `01-event-model.md` is a few hundred lines of
code; 128 fragments in Qud's voice is months of intermittent writing. This is the argument
for shipping v0.2 (retrofit, zero new writing) first and letting its reception fund the
enthusiasm for v0.3.

> **Open question 4** in `00-overview.md` §7 matters enormously here. If the era vocabulary
> system substitutes *tokens* within a shared template, each event needs 2 fragments, not 4
> — halving the cost of the entire project. Check this early.

---

## 7. Worked example

Illustrative only — constructed to show output *shape*, not proposed final prose.

**Vanilla-shaped biography** (events independent, order arbitrary):

> …met the Barathrumites · crafted an item under a weird sky · rampaged through the
> Rainbow Wood · was captured by bandits · fought a bloody battle · married · died.

Seven events, no dependencies. Reorder them and nothing is lost. Every one is a middle.

**Same seven under the compositional model,** with four core additions:

> Born heir. Swore an **oath** at the Cistern of Ubel to keep its water free `[LX_OathSworn
> → opens oath]` · met the Barathrumites, who witnessed it `[Meet Faction]` · a
> **water-rights dispute** turned a neighbouring khan into a named **rival**
> `[LX_WaterRightsDispute + LX_RivalNamed → opens claim, grudge]` · was **captured by
> bandits** in the khan's pay; ransomed at ruinous cost `[Captured by Bandits → opens
> absence, debt]` · **crafted an item** from the ransom's remainder `[Crafted Item →
> introduces ObjectRef]` · fought a **bloody battle** over the cistern and took a wound
> `[Bloody Battle → closes claim, opens wound]` · **married** the khan's daughter, settling
> the grudge `[Marriage → closes grudge]` · died of the old wound, the cistern still free
> `[LX_DeathOfAnOldWound → closes wound, oath held]`.

Same seven vanilla events, same prose fragments, four new connective types. The difference
is entirely positional — and the biography now supports a relic name that means something:
the item crafted from a ransom, carried at the cistern, would be named for the cistern and
the debt, and the Cistern of Ubel appears three separate times in the record so a player can
verify the reference.

That last property — a name a player can *check* — is the thing the mod is actually for.

---

*Next:* `03-naming.md` — deriving names from this record.
