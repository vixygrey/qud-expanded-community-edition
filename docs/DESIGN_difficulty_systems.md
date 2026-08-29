# Difficulty as Consequence — options scoped

**Status:** discussion doc, basic level. No numbers here are final.
**Premise:** difficulty that the world explains, and that creates decisions.

---

## 0. The framing that governs everything

### Qud's difficulty curve is inverted

Early game is genuinely lethal — level 1 characters die to snapjaws. Late game is
trivial for a player who knows the systems. This is the single most important fact
about designing difficulty for Qud, because it rules out the obvious approach:

> **Uniform scaling makes an already-brutal early game unplayable while barely
> touching the part that's actually too easy.**

Everything below therefore scales with **player power**, not with depth, tier, or
elapsed time.

### The two-question test

For any proposed system:

1. **Does the world explain it?** If the only answer is "because difficulty," it's
   arbitrary.
2. **Does it create a decision?** If the player's behaviour doesn't change — they just
   hold the attack key longer — it's a tax, not difficulty.

"Enemies have 2× HP" fails both. Every option below is here because it passes both.

### Why dynamic beats static

Qud is easy because it is *known*. Static difficulty is memorised once and then gone
forever. A system that reacts to **your specific build** cannot be pre-solved from a
wiki. This is an argument for the whole Part A approach over any numerical tuning.

---

## 1. The template: glimmer already does this

Qud solved this problem once, elegantly, and the solution is sitting in the game.

**Glimmer** = the sum of your mental mutation levels. As it rises:

| Glimmer | What happens |
|---|---|
| 20 | Seekers of the Sightless Way begin hunting you |
| 20–49 | `0.2 × (glimmer − 5)%` chance of a hunter per new zone |
| 34+ | Additional hunters roll separately |
| 40 | Extradimensional hunters appear — 40% chance per new zone |
| 50+ | Spawn chance becomes `0.0666 × (glimmer + 65)%` |
| Rising | Hunter rank escalates: osprey → harrier → owl → condor → strix → eagle → rukh |

And the detail that makes it excellent: **hunters level to match the player and randomly
acquire the player's own mental mutations.**

Decomposed, the pattern is:

1. A **measurable axis** of player power
2. A **faction with in-world motive** to object to it
3. Opposition scaling in **frequency** *and* **quality**
4. Opposition that **mirrors the player's build**
5. Real **counterplay** available

**Every system in Part A is this pattern applied to an axis of power that currently
generates no opposition whatsoever.**

---

## PART A — Notoriety systems

### A1. Faction rivalry *(highest value)*

**The gap.** Verified: faction reputation in Qud is tracked **entirely independently**.
Helping one faction does not anger its rivals. The only cross-faction penalty is
breaking a water ritual, which hits everyone at once. So reputation is pure
accumulation — water-ritual your way to friendly with everything and entire factions
stop being content.

**In-world basis.** The enmities are already canon. Putus Templar start at −700 and
despise mutants and technology. Barathrumites are explicitly interested in "templar
lairs." Seekers of the Sightless Way start at −500. Nothing needs inventing; the
politics exist, they're just not modelled.

**Mechanic.** An opposition matrix: gaining reputation with faction X applies a smaller
negative to X's rivals.

```
RepGain(X) = +100        ->  RepChange(rival of X) = −25 to −40
```

Ally-of-ally relationships can apply a small positive. Optionally, crossing a hostility
threshold with a faction you've wronged starts sending **retaliation parties** — the
glimmer pattern, scaled to how much they hate you.

**Decision created.** The water ritual stops being a universal off-switch and becomes a
choice about who you're willing to make enemies of.

**Implementation.** Data + events. A rivalry table in XML, a handler on the reputation
change event. **No Harmony.** This is the cleanest build in the document.

**Risk.** Tuning. Too steep and the player is locked out of content permanently; the
penalty must stay well below the gain so a deliberate player can still befriend most of
the world — just not *everyone*.

---

### A2. Hoard notoriety

**The gap.** Carrying a fortune in legendary artifacts attracts nobody.

**In-world basis.** Qud is a scavenger economy built on ancient tech. Mechanimists
venerate it, Barathrumites study it, Putus Templar want it destroyed, and everyone else
would like to sell it.

**Mechanic.** A hidden "notoriety" stat derived from the tier and count of artifacts
carried. Above a threshold, zone entry can roll for interested parties — scavenger
bands, a Mechanimist "tithe" demand, Templar purges.

**Decision created.** Whether to carry the hoard or cache it. Qud has containers and
homesteads; this gives them a purpose beyond tidiness.

**Implementation.** Inventory-scan on a timer, spawn on zone entry. No Harmony.

**Risk.** Can feel like punishment for playing well. Mitigate by making some
encounters **non-combat** — a trader who found you because of your reputation is the
same system producing an opportunity instead of a threat. Do this or the system reads
as pure tax.

---

### A3. Kill notoriety / champions

**The gap.** A vast kill count generates no reaction from anyone.

**In-world basis.** Qud's cultures are tribal and honour-driven. Someone who has
slaughtered hundreds of their kin is a known figure.

**Mechanic.** Track kills per faction. Past thresholds, that faction dispatches a
**named champion** — levelled to the player, equipped from that faction's gear pool,
and carrying a grudge line referencing what you did.

**Decision created.** Mostly pacing and dread rather than tactics, but it converts
grinding from a pure-upside activity into one with a bill attached.

**Implementation.** Kill counters plus a generator. Moderate work — the champion
generator is where the effort lives, and it's also where the *fun* lives, so don't
cheap out on it.

**Risk.** Champions that are just stat-inflated mooks are exactly the arbitrary
difficulty this doc exists to avoid. They need distinct kit and a reason.

---

### A4. Cybernetic attention *(smallest, True Kin only)*

**The gap.** Deep cybernetic investment draws no objection from anyone.

**In-world basis.** Putus Templar ideology. Their whole thing is purity.

**Mechanic.** A glimmer analogue driven by installed cybernetic tier — call it
*profane index* — that raises Templar hunter frequency.

**Value.** Gives True Kin a downside axis parallel to the one mutants already have in
glimmer. Currently glimmer punishes mental-mutation builds and nothing punishes True
Kin at all, which is an asymmetry worth closing.

**Implementation.** Nearly a copy of the glimmer system. Small.

---

## PART B — Resource systems

Part A adds opposition. Part B removes the free resources that make late Qud easy. **It
adds zero enemy HP.**

### B1. Wound system *(most directly attacks why the late game is easy)*

**The gap.** Natural regeneration is `[20 + 2 × (Willpower mod + Toughness mod)] / 100`
HP per turn, interrupted for 5 turns by damage. That's roughly 0.2 HP/turn baseline —
slow, but **turns are free**. HP is therefore a fully renewable resource whose only
cost is pressing a key. Nothing in the game charges you for time.

**In-world basis.** Qud is a world of radiation, infection, and rot. It already has a
Medicine skill, bandages, salve and ubernostrum injectors, witchwood bark, urberries,
and regeneration tanks. **The entire treatment economy exists and is currently
optional.**

**Mechanic.** Damage above a threshold in one blow, or dropping below ~25% HP, applies
a persistent **Wound** that does not heal by regeneration. Wounds cap maximum HP or
apply a stat penalty until treated. Treatment requires the existing consumables, the
Medicine skill, or a regeneration tank.

**Decision created.** This is the big one. It makes consumables matter, makes Medicine
a real skill choice, makes retreating-to-town a genuine cost, and gives damage
**memory** — you can no longer walk out of every fight as though it never happened.

**Implementation.** An effect plus a handler on damage. Interacts with the Regeneration
mutation (which should reduce wound severity or duration, not bypass it entirely).

**Risk.** The most likely of everything here to feel bad. Wounds must be *treatable
with what's already in the world*, never permanent, and the thresholds must be
generous enough that ordinary fights don't accumulate them. Get this wrong and it's a
misery generator rather than a difficulty system.

---

### B2. Pursuit across zones

**The gap.** Changing zones almost always breaks pursuit. Disengaging is close to free.

**In-world basis.** Intelligent creatures would follow you. They currently don't.

**Mechanic.** Intelligent hostiles that were actively engaged have a chance to follow
you through a zone transition, arriving a few turns behind.

**Decision created.** Fleeing becomes a real tactical choice with a cost, rather than
the universal escape hatch.

**Implementation.** Moderate. Zone-transition handling and off-screen entity persistence
are fiddly, and this is the option most likely to have nasty edge cases.

**Risk.** Could make the early game harder, which violates §0. **Gate it to intelligent
factions and higher-tier creatures only** so it bites in the back half of the curve.

---

### B3. Regional scarcity *(not a global thirst meter)*

**The gap.** Water is currency but rarely actually scarce mid-game.

**In-world basis.** Qud is a desert. The salt wastes are canonically hostile. The water
ritual is the central social mechanic *because* water is precious — and mechanically it
stops being precious quite early.

**Mechanic.** Water consumption applies **only in specific hostile biomes** — salt
desert, salt marsh. Entering them without provisioning is a real expedition problem.

**Why this shape.** A global hunger/thirst clock fights the game's stated design;
Freehold cut survival attrition deliberately. **Regional** scarcity gets the tension
without the busywork, and it makes a specific region feel like what the lore says it
is.

**Decision created.** Provisioning before crossing the salt. Actual expedition
planning.

**Implementation.** Zone-type check plus a consumption tick. Small.

---

### B4. Artifact instability

**The gap.** Gear doesn't degrade, so the tinkering economy is optional.

**In-world basis.** These are thousand-year-old machines dug out of the ground.

**Mechanic.** High-tier artifacts have a small per-use chance to **jam** — disabled
until repaired, never destroyed. Repair uses the existing Tinkering skill and scrap
economy.

**Decision created.** Makes Tinkering matter, makes redundancy worth carrying, makes
the scrap economy live.

**Risk.** Durability systems are widely hated, and usually because loss is
**permanent**. Jamming is reversible and skill-gated, which is a different feel
entirely. Keep it that way — never destroy an item.

---

## PART C — Rejected, and why

| Proposal | Why not |
|---|---|
| Flat enemy HP/damage multipliers | Fails both tests. No world explanation, no decision change. |
| Global hunger/thirst clock | Fights the game's deliberate design. Busywork. Use B3 instead. |
| Making the early game harder | The early game is already the hard part. Worsens the inverted curve. |
| Permanent item destruction | Loss-aversion misery. Use B4's jamming instead. |
| Reducing XP gain | Slower is not harder. Just extends time-to-power. |
| Randomising content per run | Breaks build planning, and Part A already solves the knowledge problem better. |

---

## Ranking

| System | Value | Effort | Harmony? | Verdict |
|---|---|---|---|---|
| **A1 Faction rivalry** | High | Low | No | **Build first** |
| **B1 Wound system** | High | Medium | Probably not | **Build second** |
| B3 Regional scarcity | Medium | Low | No | Good third |
| A4 Cybernetic attention | Medium | Low | No | Cheap, closes an asymmetry |
| A2 Hoard notoriety | Medium | Medium | No | Needs the non-combat valve |
| B4 Artifact instability | Medium | Medium | Maybe | Only as jamming |
| A3 Kill champions | Medium | High | No | Best content, most work |
| B2 Pursuit | Medium | High | Likely | Most edge cases. Last. |

**Suggested first release:** A1 alone. It's the clearest genuine gap, it's data and
events with no Harmony, it changes how the whole social layer plays, and it ships
small enough to actually finish.

---

## Technical notes

- Everything in Part A is reputation/spawn logic — parts, events, and XML tables.
- B1 needs a damage-event handler and an effect. B2 is the only one likely to need
  Harmony, which is a further argument for doing it last.
- Every system behind a **mod option, defaulted off**. These are opinionated changes and
  players should opt into each one independently.
- Freehold recommend treating Harmony as a last resort — postfix and non-blocking
  prefix patches only, never transpilers.

---

## Sources

- [Glimmer](https://wiki.cavesofqud.com/wiki/Glimmer)
- [Dealing With Esper Hunters](https://wiki.cavesofqud.com/wiki/Dealing_With_Esper_Hunters)
- [Reputation](https://wiki.cavesofqud.com/wiki/Reputation)
- [Factions](https://wiki.cavesofqud.com/wiki/Factions)
- [Putus Templar](https://wiki.cavesofqud.com/wiki/Putus_Templar)
- [Barathrumites](https://wiki.cavesofqud.com/wiki/Barathrumites)
- [Hitpoints (HP)](https://wiki.cavesofqud.com/wiki/Hitpoints_(HP))
- [Modding:Harmony](https://wiki.cavesofqud.com/wiki/Modding:Harmony)
