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

### Notoriety must sometimes be an opportunity

Part A is entirely opposition. A1 makes factions hate you, A2 sends scavengers and
purges, A3 sends champions, A4 raises hunter frequency. Every one of the four produces
something that comes to fight you.

If becoming known only ever arrives as a threat, Part A is a difficulty tax with a
story attached — which is exactly what the second question exists to prevent. "The
player fights a harder thing" is not a decision; it is the same fight with larger
numbers.

> **Every system that generates notoriety must sometimes produce an opportunity rather
> than a threat.**

A trader who sought you out because of your reputation is the same system, the same
trigger, and the opposite valence. So is someone who wants to hire you, to warn you, or
to ask for help. Without that, notoriety reads as the game punishing you rather than as
the world noticing you.

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

**Risk.** Can feel like punishment for playing well — the sharpest case of the
opportunity rule in §0, since a hoard is the most visible thing a player earns.

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

**The gap.** Natural regeneration is `[20 + 2 × (Toughness mod + Willpower mod)] / 100`
HP per turn, interrupted for **10 turns** by damage (`HandleEvent(TookDamageEvent)` sets
`HitCounter = 10`). That's roughly 0.2 HP/turn baseline — slow, but repeatable, so HP is
a renewable resource.

**Turns are not free, and this is the correction that changes what B1 is.** The section
used to say *"nothing in the game charges you for time."* It does. The currency is water:

```csharp
RegenCounter += value;
if (RegenCounter > 100)
{
    int num = (int)Math.Floor((double)RegenCounter / 100.0);
    RegenCounter %= 100;
    if (Water > 0) { ParentObject.GetStat("Hitpoints").Penalty -= num; }
    else { if (IsPlayer()) return false; ... }
}
```

The counter is reset by `%= 100` **before** the water check, so at zero water the accrued
heal is discarded outright rather than banked. Resting to full already costs drams.

**And that `return false` is the whole of dehydration's teeth**, which this section quoted
without following. Its one caller is `Stomach`'s own action tick, where it gates the
thirst damage — so at zero water a character is locked out of natural healing entirely,
and *separately* takes 2 hit points on a natural 1 of `1d(Toughness)` per heal tick that
comes due. §B3 has the arithmetic. The two sections were describing the same six lines to
different conclusions until #705; they agree now.

> **So a wound system would be a *second* time-tax stacked on an existing one**, and this
> fork has its own positions on water in `docs/DESIGN_water_and_legacy.md`. B1's own risk
> note calls this the most likely of the eight to feel bad; stacking it on the water
> economy without saying so is exactly how that happens. **That interaction is an open
> question, not a resolved one** — it needs settling against the water document before B1
> is costed, and this section deliberately does not settle it.

**In-world basis.** Qud is a world of radiation, infection, and rot. It already has the
**`Physic`** skill tree (Staunch Wounds, Nostrums, Amputate Limb, Apothecary), bandages,
salve and ubernostrum injectors, witchwood bark, urberries, and regeneration tanks.
**The entire treatment economy exists and is currently optional.** #640 confirms the
inventory: 11 blueprints that restore HP or staunch bleeding, four cooking domains,
Convalessence, the `Physic` tree and the Regeneration mutation.

**Mechanic.** Damage above a threshold in one blow, or dropping below ~25% HP, applies
a persistent **Wound** that does not heal by regeneration. Wounds cap maximum HP or
apply a stat penalty until treated. Treatment requires the existing consumables, the
`Physic` skill, or a regeneration tank.

**Decision created.** This is the big one. It makes consumables matter, makes `Physic`
a real skill choice, makes retreating-to-town a genuine cost, and gives damage
**memory** — you can no longer walk out of every fight as though it never happened.

**Implementation.** An effect plus a handler on damage.

**The Regeneration mutation already bypasses the interrupt**, so the note that it *"should
reduce wound severity or duration, not bypass it entirely"* is aiming at a lever that
already exists. It does two separate things today: it multiplies the regen amount on the
`Regenerating` event by `0.1 + 0.1 × Level`, and it regenerates **through** the damage
interrupt at half rate —

```csharp
if ((HitCounter <= 0) | ParentObject.HasPart<Regeneration>()) { ... }
if (HitCounter > 0) { value /= 2; }
```

Blunting that existing behaviour is a cleaner lever than adding a wound-specific
exemption on top of it.

**Treatment items need no C#, so the "probably not" on Harmony can be a firm no.**
`HealMedication`, `RegenMedication` and `StatBoostMedication` are real classes in
`XRL.World.Parts` that **no vanilla blueprint declares** — fully XML-drivable, genotype
splits included. Vanilla built the mechanism and never wired it up, which is a shape
`docs/LESSONS.md` already records.

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

**Mechanic.** **Refuse the crossing, do not tax it.** A character who reaches the world
map without enough water for the terrain ahead is told so and stopped, the way
`Stomach` already stops a famished one. Consumption is untouched.

**Why this shape.** A global thirst clock is not missing from Qud — it is present and
lethal, and **capacity swamps it**. `Stomach` starts `Water` at 30,000 and spends
`Speed / 5` per action, so 20 a turn at Speed 100: **1,500 actions to empty**, not to
dead. `RuleSettings.WATER_MINIMUM` is 0, so nothing clamps it out of reach, and 30,000
is the *starting* value — `WATER_QUENCHED` — against a ceiling of
`WATER_MAXIMUM` **50,000**, with `WATER_TUMESCENT` at 40,000 between them. But one dram
restores 10,000 — 500 actions — and a waterskin holds 64 of them, which is **32,000
actions** in a single container. `Options.AutoSip` drinks at the Thirsty line, so the
gauge never visibly moves.

**What reaching zero actually does, because this document had it wrong by about
ninetyfold.** It is not two hit points per action. The damage is gated twice:

```csharp
bool flag3 = ProcessNaturalHealing();
if (!flag3 && Stat.RollPenetratingSuccesses("1d" + ParentObject.Stat("Toughness"), 2) <= 0)
{ … Popup.Show("You are dying of thirst!"); … Penalty += 2; }
```

`ProcessNaturalHealing` returns `false` only when `Water <= 0` *and* an accrued heal has
just come due — roughly every fifth action at baseline, since it banks
`20 + 2·ToughnessMod + 2·WillpowerMod` against a threshold of 100. And
`RollPenetratingSuccesses("1d" + Toughness, 2)` returns 0 **only on a natural 1**: any
face of 2 or more clears the target and breaks out as a success.

> So dehydration is **a natural-healing lockout plus a 1-in-Toughness chance of 2 HP per
> heal tick** — on the order of 2 HP per hundred actions at Toughness 20. **The lockout
> is the real teeth and the damage is the rounding.** §B1 quotes this same method ninety
> lines earlier and stops at its `return false`; the two sections now agree.

So the design position to argue with is not *"Qud rejects survival attrition"*. It is
*"Qud runs survival attrition at a rate that almost never fires."*

**And regional scarcity is not a mechanic to add — most of it already ships.**
`TerrainTravel.HandleLeavingCell` fires a full action tick every tenth travel segment,
and terrain blueprints override `Segments` from 1,000 to 4,000, so water is already
priced per distance *and* already terrain-aware:

| terrain | `Segments` | thirst ticks | water | drams |
|---|---:|---:|---:|---:|
| `TerrainSaltdunes2` | 3,000 | 900 | 18,000 | 1.80 |
| **`TerrainSaltdunes`** | **2,500** | **750** | **15,000** | **1.50** |
| `TerrainSaltmarsh` | 1,250 | 375 | 7,500 | 0.75 |
| road / asphalt | 1,000 | 300 | 6,000 | 0.60 |

**Vanilla already charges 2.5× to cross salt rather than a road.** The question is not
whether to build per-region cost but whether to scale one that exists — and against
64 drams in a one-pound skin, no plausible multiplier bites. That is why the mechanic
above is a refusal rather than a tick.

**Decision created.** Provisioning before crossing the salt. Actual expedition
planning.

**Implementation.** `CanTravelEvent`, which `Stomach` already uses for exactly this
shape — *"You're too famished to travel long distances."* It dispatches to the player
**and** to `The.Game`, the only `Can*Event` that does, so it can be vetoed centrally.
No Harmony, no vanilla record, no save state.

**Its real limit, stated so nobody scopes past it:** `CanTravelEvent` gates *entering*
the world map, not each parasang crossed. It can refuse an unprovisioned departure; it
cannot turn someone back halfway. A per-parasang check needs a different seam.

---

### B4. Artifact instability

**The gap.** Gear doesn't degrade, so the tinkering economy is optional.

**In-world basis.** These are thousand-year-old machines dug out of the ground.

**Mechanic.** High-tier artifacts have a small per-use chance to **jam** — disabled
until repaired, never destroyed. Repair uses the existing Tinkering skill and scrap
economy.

**This is a new trigger for an existing state, not a new system.** `Broken` is a
shipped effect applied at roughly twenty-five sites, `Tinkering_Repair` already clears
it for bits, and vanilla already does per-use breakage in `ChargeUsedEvent` — it is
simply gated to overloaded items:

```csharp
if (PowerLoadLevel <= 100) return;
int num = GetOverloadChargeEvent.GetFor(Object, Amount);
if ((1 + num / 10).in10000() && Object.ApplyEffect(new Broken(FromOverload: true)))
```

The state, the hook and the repair economy all exist. What is new is the condition.

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
| Global hunger/thirst clock | **Not** because Qud rejects one — it runs two. Because a global clock is busywork whatever its rate, and because capacity already swamps the one that ships. Use B3 instead. |
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
| B3 Provisioning refusal | Medium | Low | No | Good third — a `CanTravelEvent` refusal. Not the tick, and not AutoSip either: that is a bare global read with no dispatch, so suppressing it needs Harmony |
| A4 Cybernetic attention | Medium | Low | No | Cheap, closes an asymmetry |
| A2 Hoard notoriety | Medium | Medium | No | Needs the non-combat valve |
| B4 Artifact instability | Medium | **Low** | No | Only as jamming. `ChargeUsedEvent` is the hook; `Broken` already exists |
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
