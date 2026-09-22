# Record-Only Event Eligibility Catalog

> **Status:** #731 uses this document as a safety boundary, not as an authoring catalog. The
> speculative role-grid and `LX_` event proposals below are archived design material. Any future
> shipped code uses the repository's `Vixy_` prefix and is selected only after #979 reviews #731 play
> evidence.

## 1. Footprint classification

An earlier event is eligible for a record-only response only when the response does not claim to
change a thing that the earlier event created or moved into the world.

| Classification | Vanilla event types | #731 disposition |
|---|---|---|
| Creates a findable entity | `BattleItem`, `ForgeItem`, `FoundGuild`, `LoseItemAtTavern`, `Marry`, `MeetFaction` | Blocked. A truthful consequence requires matching worldgen work in #815. |
| Reveals a place or faction only | `BloodyBattle`, `CapturedByBandits`, `ChallengeSultan`, `ChariotDrivesOffCliff`, `CorruptAdministrator`, `InspiringExperience`, `LiberateCity`, `RampageRegion`, `SecretRitual`, `UnderWeirdSky` | Potentially safe for a later prose-only response. Each proposed consequence needs its own footprint review. |
| Closed beat | `Abdicate` | No answerable open thread in the current slice. |

## 2. First response

`CapturedByBandits` is eligible only when its generated `tombInscriptionCategory` is
`EnduresHardship`. That branch records an escape and leaves the bandits at large; it creates no
entity. The `Slays` branch is a resolved murder and is excluded.

The response is a later, same-sultan gospel reflection. It must not change the source event's
location, revealed region, or any other existing property. It must stand alone because the journal
reveals sultan notes independently.

## 3. Deferred catalog

The remaining sections preserve the original proposed role grid and expansion ideas. They are not
safe to implement from this document: several imply a new entity, a relocated relic, or a changed
faction. #979 decides whether a later record-only candidate is worth a dedicated issue; #815 owns
world-facing consequences.

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
cheapest naming substrate in the system — see `DESIGN_history_naming.md` §3.2.

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
eight events away. Worth building the chain-viewer tooling (`DESIGN_history_implementation.md` §5) just
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

`LX_DeathUnresolved` is deliberate: per `DESIGN_history_events.md` §5.2, roughly a third of lives
should end with threads still open. It is the mythic register's natural ending and a
guardrail against the metronome failure mode.

---

## 5. Legacy events — cross-sultan

Per `DESIGN_history_events.md` §7. Each fires for sultans 2–5, reading the dynastic ledger. These
are disproportionately valuable per unit of writing because they make the *sultanate* a
coherent object rather than five unrelated lives.

| Id | Reads | Effect |
|---|---|---|
| `LX_Canonization` | predecessor's `epithets` | Predecessor venerated; `piety +1`; predecessor's relic gains a cult |
| `LX_Iconoclasm` | predecessor's monuments | Monuments destroyed, name struck from inscriptions; **licenses source contradiction** (see `DESIGN_history_sources.md` §5) |
| `LX_TombDesecrated` | predecessor's `possessions` | A relic leaves the tomb; opens `relic_lost` for a *later* sultan to close |
| `LX_TreatyInherited` | predecessor's open `oath` | Honoured or repudiated; if repudiated, opens `grudge` with a faction that remembers |
| `LX_OldGrudgeAvenged` | predecessor's open `grudge` | Closes a thread opened generations earlier |

`LX_TombDesecrated` → `LX_RelicRecovered` across two different sultans is the flagship
chain of this mod. A relic that is buried, stolen, and recovered a century later — under a
name that references all three events — is the most concrete possible answer to "the names
are obvious mashups."

---

## 6. Authoring cost

Per `DESIGN_history.md` §2.2, every event needs a gospel rendering and a tomb-inscription
rendering, and each must work in cosmic and earthen vocabulary registers.

| Set | Types | Renderings each | Fragments |
|---|---|---|---|
| Core twelve (v0.3) | 12 | 2 sources × 2 registers = 4 | **48** |
| Extended (v0.4+) | 15 | 4 | 60 |
| Legacy (v0.5+) | 5 | 4 | 20 |
| **Total if all built** | **32** | | **128** |

**The prose is the project.** The model in `DESIGN_history_events.md` is a few hundred lines of
code; 128 fragments in Qud's voice is months of intermittent writing. This is the argument
for shipping v0.2 (retrofit, zero new writing) first and letting its reception fund the
enthusiasm for v0.3.

> **Open question 4** in `DESIGN_history.md` §7 matters enormously here. If the era vocabulary
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

*Next:* `DESIGN_history_naming.md` — deriving names from this record.
