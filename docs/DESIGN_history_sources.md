# Source and Divergence Model

> The counter-intuitive document. Everywhere else this mod removes incoherence; here it
> **adds** it — deliberately, and under strict rules.

---

## 1. Why add contradiction to a coherence mod

The complaint that started this project was that the lore felt "not weird, but actually
stupid and incoherent." That distinction is the whole design.

Weirdness that a player can attribute to a *speaker* is interesting. Weirdness with no
attributable source is noise. Three accounts of a battle that disagree randomly read as a
bug. Three accounts that disagree because a priest wrote one, a victor carved another, and a
village remembers the third read as **history** — and the player's act of reconciling them
is the most engaging thing lore can do.

So the goal is not to make the record consistent. It is to make it **motivatedly**
inconsistent. Principle P5.

The architecture for this already exists in vanilla and is underused: every event already
has a *gospel* version and a *tomb inscription* version, with the inscription written in an
elevated register that sometimes omits the morally inconvenient parts. That is a source
model in embryo. This document proposes extending it from two sources to four, giving each
an explicit bias, and — critically — making the distortions **recoverable**.

---

## 2. The sources

| Source | Voice | Encountered as | Bias |
|---|---|---|---|
| **Gospel** | Chronicle, moderate register | Sultan history text, books | Closest to ground truth; mild pro-sultan drift |
| **Tomb inscription** | Elevated, formal, carved | Tomb of the Eaters | Strong valorisation; omits moral complication |
| **Mural** | Compressed, pictorial, captioned | Historic sites, ruins | Extreme compression; conflates and mislabels |
| **Oral tradition** | Vernacular, local | Village gossip, NPC dialogue | Localised; inflates local relevance; temporally vague |

Ground truth is the ledger produced by `DESIGN_history_events.md`. **No source renders ground truth
directly.** The gospel is closest but is still a rendering — which is a meaningful design
statement in itself, and matches how Qud already treats its own lore.

> **Scope note:** murals and oral tradition are consumed by systems outside history
> generation. Whether this mod can reach them is recon question #6
> (`DESIGN_history_implementation.md` §2). If it cannot, the model degrades cleanly to gospel + tomb —
> still worth building, since that pair alone supports §3's operators.

---

## 3. Distortion operators

Each source applies operators to a ground-truth event according to its bias vector. Seven
operators, each cheap to implement and each producing a recognisable *kind* of unreliability.

| Operator | Effect | Typical source |
|---|---|---|
| **Omit** | Drop a clause — usually the morally inconvenient one | Tomb |
| **Euphemise** | Substitute a softer predicate ("subdued" for "slaughtered") | Tomb, Gospel |
| **Transfer agency** | Reassign who acted — sultan credited for a subordinate's deed | Tomb, Oral |
| **Inflate magnitude** | Scale numbers, duration, or scope upward | Oral, Tomb |
| **Conflate** | Merge two events sharing a referent into one | Mural, Oral |
| **Displace** | Move the event in time, or attribute to the wrong sultan | Mural, Oral |
| **Localise** | Relocate the event to the speaker's own region | Oral |

### 3.1 Bias vectors

Each source carries per-operator probabilities. Illustrative starting values:

| | Omit | Euphem. | Transfer | Inflate | Conflate | Displace | Localise |
|---|---|---|---|---|---|---|---|
| Gospel | 0.05 | 0.10 | 0.05 | 0.05 | 0.00 | 0.00 | 0.00 |
| Tomb | 0.35 | 0.40 | 0.30 | 0.30 | 0.05 | 0.05 | 0.00 |
| Mural | 0.30 | 0.10 | 0.20 | 0.20 | 0.35 | 0.30 | 0.05 |
| Oral | 0.20 | 0.15 | 0.25 | 0.45 | 0.25 | 0.35 | 0.40 |

Tuning target: a player comparing two accounts of the same event should notice a difference
roughly **one time in three**. More often and the world reads as unreliable everywhere,
which is exhausting; less often and nobody ever notices the system exists.

---

## 4. The recoverability constraint

This is the rule that separates designed unreliability from randomness, and it is the most
important paragraph in the document.

> **A distortion must be recoverable.** A player comparing two sources must be able to infer
> what actually happened, or at minimum infer *that* something was altered and in which
> direction.

Three enforcement rules follow:

**R1 — Never distort referent identity.**
Proper nouns are inviolable. A source may lie about what happened at the Cistern of Ubel; it
may not rename the cistern. If referents drift, cross-referencing collapses and the player
is back to reading noise — undoing `DESIGN_history_naming.md` §5 entirely. **Distort predicates, never
handles.**

**R2 — Distortions must be directional and consistent with bias.**
A tomb inscription always flatters. It never randomly disparages. Once the player learns
"tombs exaggerate," every tomb inscription becomes readable — the bias itself is
information. Randomising the direction destroys this.

**R3 — At most two operators per event per source.**
Three or more compounding distortions produce an account no longer recognisable as the same
event, and the player perceives an unrelated event rather than a distorted one.

---

## 5. Iconoclasm — the diegetic license

`LX_Iconoclasm` (`DESIGN_history_catalog.md` §5) is where the source model earns its place.

When a later sultan strikes a predecessor's name from inscriptions, the mod gains explicit
in-fiction permission for the *most aggressive* distortion in the system: an inscription
where the agent has been erased and replaced, or effaced entirely.

The result is a record with a **hole in a specific shape** — a monument whose subject has
been scratched out, a gospel naming someone a tomb refuses to name. That is not incoherence.
That is the most coherent thing a generated history can produce, because the absence is
itself caused, and a player who finds both accounts can reconstruct not only what happened
but *who wanted it forgotten*.

This is the single strongest argument for cross-sultan causality (`DESIGN_history_events.md` §7),
and it is why the legacy events are worth their authoring cost despite being only five
types.

---

## 6. Player-facing payoff

The mod should not explain any of this. No tooltips, no "unreliable narrator" indicator, no
journal entry announcing a contradiction. The system works precisely to the extent that the
player discovers it.

What it produces, in ascending order of how long it takes a player to notice:

1. Accounts that differ, noticed on a second reading of a familiar event
2. A dawning sense that tomb inscriptions flatter and villages exaggerate
3. Using that knowledge to *correct* an account — inferring ground truth from bias
4. Noticing an erasure, and inferring the erasing sultan's motive from their own history

Stage 4 is the ceiling and few players will reach it. That is fine. A generated history
whose depth exceeds what most players will excavate is the correct shape for this game —
Qud's existing lore already works this way.

---

## 7. Risks

| Risk | Mitigation |
|---|---|
| Reads as bugs, gets reported as bugs | Keep distortion rate near 1-in-3; never distort referents (R1) |
| Wiki data-mining flattens it | Unavoidable and acceptable — vanilla has the same property |
| Interacts badly with mods that surface raw history | Expose a config toggle for source divergence |
| Players cannot tell distorted from vanilla weirdness | Acceptable. If it reads as vanilla weirdness, it has matched the register — which is P4 |
| Compounding with era vocabulary produces mush | Cap operators (R3); test cosmic-era tomb inscriptions specifically, as they stack two elevating systems |

That last risk is the most concrete: an early-era tomb inscription is already the most
elevated text in the game, and adding valorising distortion on top may push it past
comprehensibility. Test that combination first.

---

*Next:* `DESIGN_history_implementation.md` — tiers, recon, and instrumentation.
