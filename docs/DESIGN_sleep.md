# Sleep & Fatigue — design doc

**Status:** spec only, no code written
**Target:** Caves of Qud, build 210+ (MinEvent era)
**Scope:** one mod, mostly C#, no Harmony required

> **Revised against the assembly, and the revisions were large.** This document was written from the
> wiki before anything was checked, and five passes of recon on #179 found its two central sections
> resting on mechanisms that do something else. §1's premise, §2's dream row, §3.2's threshold table
> and §4's reward tier have all been rewritten; the sections that survive are §3.1, §3.3, §5 and §6.
>
> The pattern in every case was the same, and it is the useful thing to carry forward: **the document
> reached for generation where the game offers authored text, and for stat penalties where the game
> refuses an action.** Qud consistently shipped more than this document assumed, and the shipped
> mechanism was consistently smaller and better than the proposed one.
>
> Two design decisions were settled in the rewrite rather than derived: dreams **quote**
> `JournalAPI.Accomplishments` rather than generating, and Weary borrows the **`Confused` model** —
> unreliability — rather than an attribute ladder.

---

## 1. The design problem, stated honestly

Qud has both hunger and thirst attrition. Thirst is the faster and the only one that can
kill: `Stomach` spends `Speed / 5` water per action, so from its starting 30,000 —
`WATER_QUENCHED`, against a ceiling of 50,000 — a character who drinks nothing is Thirsty
at ~500 actions and **empty at ~1,500**, which is where the attrition begins rather than
where the run ends. Reaching zero locks out natural healing outright and then rolls
`1d(Toughness)` against 2 on each heal tick that comes due, taking 2 hit points only on a
natural 1 — on the order of 2 HP per hundred actions at Toughness 20, not per action.
The lockout is the real teeth. (`docs/DESIGN_difficulty_systems.md` §B3 has the code and
the arithmetic; this paragraph and that section were both wrong the same way, from the
same source, and were corrected together in #705.) Hunger is
slower and non-fatal but real: `COOKING_INCREMENT` is 1,200, so Hungry at 1,200 actions
and **Famished at 2,400**, and `Famished` is −10 Quickness until you eat.

What Freehold actually did is tune both so they almost never fire. One dram restores
10,000 water — 500 actions — and a waterskin holds 64 of them, 32,000 actions in one
container; `Options.AutoSip` drinks at the Thirsty line so the gauge never visibly moves.

**So the design position is not "no survival timers". It is "survival timers that almost
never fire".** That is a better opening for this document than the one it had, because it
makes the case stronger rather than weaker: a sleep timer would not be importing an alien
system into a game that rejected the idea — it would be a third timer in a game that
already runs two, and the only question is what rate it fires at next to theirs. Any
sleep-necessity mod is therefore swimming against the grain of the game's own *tuning*,
and the forums have a recurring thread of players saying so.

So the mod only justifies itself if sleep is **a gateway to content, not a meter you
top up**. If the player's summary of the mod is "I have to press `,` every 800 turns,"
it has failed regardless of how well it's coded.

Two rules follow, and every number below serves them:

- **Fatigue must never be merely punishing.** Exhaustion should make the world
  *stranger*, not the character weaker. Qud already has the vocabulary for this.
- **Sleeping must be a decision, not a chore.** Where you sleep, and what finds you
  while you're under, is the interesting part.

---

## 2. What the base game already gives us

Verified against the wiki; **confirm exact type names against the decompiled assembly
before writing code** (see §7 — I could not verify every identifier from documentation
alone).

| System | Behaviour | How we use it |
|---|---|---|
| `Asleep` effect | Unconscious; **−12 DV**; attackers get **+4 penetration**; damage wakes you and applies Dazed | Reuse wholesale. Do not reimplement — the vulnerability math is already tuned and other mods/creatures interact with it. |
| `Wakeful` | Granted 3–5 rounds after waking from *involuntary* sleep; blocks re-sleep | **Already true in vanilla — nothing to build.** `Wakeful` registers for and refuses only `CanApplyInvoluntarySleep` and `ApplyInvoluntarySleep`. `GasSleep` fires the check; `Bed` never goes near it. |
| Telepathic dream text | **Not a dream system.** `Asleep.GetSleepMessage` returns cyan Markov text only under `Mental && !Physical` — what a *psychically perceiving observer* sees when looking at a sleeping creature. The ordinary branches are *"utterly unresponsive"* and *"snores loudly"*. Nothing routes any of it to the sleeper. | Not the hook. The register it promised is real and reachable elsewhere — see the `=WEIRDMARKOVSENTENCE=` row below. |
| `=WEIRDMARKOVSENTENCE=` | A registered variable replacer (`VariableReplacers.cs`) running a Markov sentence through `Grammar.Weirdify`. Five siblings exist: `=MARKOVSENTENCE=`, `=MARKOVPARAGRAPH=`, and the corvid, waterbird and fish variants. | **This is §1's "make the world stranger" register, and it needs no C# at all.** Anything passing through `GameText.VariableReplace` can carry it, so a fatigue message can be authored data. |
| `JournalAPI.Accomplishments` | Public static serialised `List<JournalAccomplishment>`. Every entry carries `Time`, `Category`, `MuralText`, `GospelText`, `MuralCategory`, `MuralWeight` — timestamped deeds with **pre-authored prose in two registers**. | The store §4's dreams actually want. A list read, not a corpus project. |
| `Narcolepsy` mutation | Forces involuntary sleep | Must not stack pathologically with fatigue. See §6. |
| Sleep gas / Sleep Breath | Involuntary `Asleep` | Should **not** count as restful. **Already distinguishable — read `Asleep.Voluntary`.** Vanilla sets it correctly at every call site: `Bed`, `Slumberling` and the two lair sleepers pass `Voluntary: true`; `GasSleep`, `Narcolepsy`, `CrungleGaze`, `ModFatecaller`, `PaxKlanqMadness` and `Flagging` all leave it false. One field, nothing to thread. |

That last row is the single most important interaction in the mod. If sleep gas cures
exhaustion, the player carries gas grenades and the system is dead.

---

## 3. Core loop

### 3.1 The Fatigue stat

A single integer on the player, 0–1000, rising each turn.

```
FatiguePerTurn = 1.0
  × (Awake ? 1 : 0)
  × StrainMultiplier      // see below
```

**`Calendar.TurnsPerDay` is 1200**, which is the number this section needed and did not have. At 1
point per action, 1000 actions is **0.83 of one day** — not the "roughly two in-game days" claimed
here. The target was three days unhurried, so the baseline was `1000 / 3600` = **0.28 per action**,
carried in hundredths so the multipliers stay exact integers.

> **Amended by #821.** Play found the step from Tired to Weary arriving too soon, and measuring it
> showed the cause: the Rested band is **400 wide and every band after it is 200 or less**, so the
> second rung lands at half the pace the first one teaches. The ladder's shape is deliberate and
> stays; the rate moved instead, to **0.22** and a target of **3.79 days**. Widening the early bands
> could only have come out of the later ones, and `Exhausted` is where the mechanics live.

What that produces:

| activity | per action | actions to full | in-game days |
|---|---:|---:|---:|
| unhurried | 0.22 | 4,545 | **3.79** |
| overland travel, or bleeding | 0.33 | 3,030 | 2.53 |
| in combat throughout | 0.44 | 2,273 | 1.89 |

**Three days is the unhurried figure and a character who fights for it arrives in half that**, which
is the lever this section is actually about: fatigue is a consequence of what you did, not of elapsed
time.

`StrainMultiplier` makes fatigue a consequence of *what you did*, not just elapsed time:

| Condition | Multiplier |
|---|---|
| Resting / waiting | 0.5 |
| Normal activity | 1.0 |
| Overland travel | 1.5 |
| In combat this turn | 2.0 |
| Overburdened (see burden doc) | +0.5 |
| Bleeding / poisoned / on fire | +0.5 |

This is the design's main lever: a careful player who avoids fights sleeps less often,
which rewards exactly the play Qud already rewards.

### 3.2 Thresholds

**Rewritten against what vanilla's own timers actually cost.** The original table was a four-tier
ladder across three attributes — −1 Agility, then −2 Agility and −2 Intelligence, then −4/−4/−2
Willpower. It was written with no benchmark available. There is one now, and it is damning:

| vanilla timer | what it costs when it fires |
|---|---|
| **Thirst** at empty | natural healing stops; on a failed Toughness roll, ~2 HP per hundred actions. **No attribute penalty at all.** |
| **Hunger** at Famished | `Famished` — **−10 Quickness**, one stat, non-fatal. And `Stomach.HandleEvent(CanTravelEvent)` refuses world-map travel: *"You're too famished to travel long distances."* |

Between them, Qud's two survival timers use **one stat penalty on one effect**, and otherwise express
themselves as *capability* consequences — you cannot heal, and you cannot travel. The old §3.2 was
several times heavier than either, which would have made this the most punishing of three timers in a
game that tunes the other two almost out of existence.

It also contradicted §1. *"Fatigue must never be merely punishing"* and *"exhaustion should make the
world stranger, not the character weaker"* are the rules this document is built on, and a stat ladder
is exactly a character being made weaker. §3.2 even conceded it — *"the stat penalties are there so
the numbers-focused player also feels it"* — which is a reason to have one, not four.

**So: no attribute ladder. Capability consequences, following the idiom vanilla already uses.**

| Fatigue | State | Effect |
|---|---|---|
| 0–399 | Rested | none |
| 400–599 | Tired | occasional flavour message, carrying `=WEIRDMARKOVSENTENCE=` |
| 600–799 | Weary | the message grows frequent and stranger. **`Confused`-modelled unreliability begins** (§3.2.1) |
| 800–949 | Exhausted | unreliability frequent. **World-map travel refused**, following `Famished` |
| 950–1000 | Collapsing | all the above, plus a rising per-turn chance of forced `Asleep`, 1% climbing to 25% at 1000 |

Exactly one number is borrowed from vanilla and one mechanism: the travel refusal is `Famished`'s,
via `CanTravelEvent`. That event carries a single field and fires *before* a destination exists, so
the only thing it can express is an outright refusal — which is precisely what this wants. See
`docs/LESSONS.md`, *"The world-map movement gate is `ObjectLeavingCellEvent`"*, for why anything
conditioned on **where** you are going has to use a different hook.

### 3.2.1 Weary borrows `Confused` rather than inventing a hallucination

**There is no hallucination effect in the game to inherit.** The neighbours are `Confused`,
`FuriouslyConfused` and `Dazed`. `Confused` is the idiomatic shape and the right one here: it makes
the character *unreliable* rather than *weaker*, which is §1's rule stated as a mechanism.

Two things to know before building on it. `Confused` expresses itself largely through
`GetLostChanceEvent` — so it is a **movement** effect, and borrowing it wholesale would make fatigue
mean "you wander", not "you misperceive". And it is a larger behavioural change than −2 Agility, not
a smaller one; it is chosen because it is *better*, not because it is cheaper.

The recommendation is to borrow the **model**, not the class: a fatigue effect that introduces
unreliability at the point of action, in the way `Confused` does, rather than subclassing it and
inheriting its lost-chance behaviour by accident.

### 3.3 Sleeping

Sleep is entered voluntarily via a new "Sleep" option (interaction menu or a keybind).
It applies the vanilla `Asleep` effect and runs until fatigue reaches 0 or the player is
woken.

```
FatigueRecoveredPerTurn = 4  × RestQualityMultiplier
```

So a full 1000 → 0 sleep takes ~250 turns at quality 1.0.

**This table was written per turn and nobody multiplied it out.** A full sleep is 167–250 actions, so
a rate that reads harmless per turn compounds into something else entirely: the 0.5% for open
wilderness is a **71% chance of being ambushed over one sleep**. That is not "location is a decision",
it is "beds or nothing", and it fails §1's acceptance test — the player's summary becomes *"I get
jumped every time I sleep."*

**So the rates are derived from per-sleep odds now, not chosen per turn.** Pick what fraction of
sleeps should be interrupted, then solve `1 − (1 − p)ⁿ` backwards for the per-turn rate:

| Where the player sleeps | Rest quality | P(ambushed) per sleep | per turn |
|---|---|---:|---:|
| **In a settlement** | 1.5 | **0%** | 0 |
| On a bed / bedroll | 1.5 | 5% | 0.03% |
| Indoors, no hostiles in zone | 1.2 | 14% | 0.06% |
| Open wilderness | 1.0 | 30% | 0.14% |
| Hostile-occupied zone | 1.0 | 80% | 0.64% |
| While heavily burdened | ×0.75 | — | — |

**A settlement is genuinely safe, at 0 rather than the 0.1% first written here.** A tier list with no
top end gives the player nowhere to aim, and *"walk to a town and you can rest"* is a decision worth
making. The signal is `Zone.IsCheckpoint()` — the game's own notion of a safe hub, testing for a
`CheckpointWidget` in cell (0,0) — so the safe list is Freehold's rather than one this fork invented
and would have to maintain. It covers Joppa, the Stilt, Grit Gate, Kyakukya, Yd Freehold, Ezra and the
Arrivarium. Hostiles in the zone still override it: a settlement under attack is not a safe place to
lie down.

**Both tables must key on one tier function.** The first implementation had rest quality
distinguishing a sheltered spot from open ground while ambush chance did not, so the two disagreed
silently about how many tiers existed.

Ambush rolls each turn asleep, **and only when something hostile is already in the zone**. That
precondition is not a detail: without it the roll fires in empty zones, where there is nothing to do
the ambushing, and the hard-stop message asserts something untrue. No culprit means no roll and an
undisturbed sleep.

On a hit: **wake the culprit** if it is asleep, aim it at the player with `Brain.Target` and a `Kill`
goal, wake the player with `Dazed`, and name what found them. Nothing is spawned — *"spawn or wake"*
above offers both and waking what is already there is the less arbitrary half, but it only works if
the roll checks that there is something to wake.

Because the roll is conditional, **hostility is a precondition rather than a tier**. Making it a tier
breaks the table: a "hostile-occupied zone" row means the other rows only apply when nothing hostile
is present, which is exactly when no ambush can happen. Where you are is the tier; what is in the zone
decides whether the dice come out.

**This is what makes location a real decision** and gives bedrolls a reason to exist.

Involuntary sleep (gas, narcolepsy, conk) recovers fatigue at **0.5/turn** — better
than nothing, never a substitute.

---

## 4. The part that makes it worth playing

§3.2 no longer taxes attributes, so this section is not the interesting half beside a boring one — it
is the whole of what fatigue *is*. From Weary upward the player perceives Qud less reliably, and that
unreliability is the mechanic.

Escalating with fatigue tier, roll occasionally on:

1. **Phantom tiles.** A creature tile drawn in a nearby empty cell for a few turns. Purely visual, no
   entity. The player wastes a turn attacking nothing.
2. **Misread labels.** Item names swap with plausible neighbours for a few turns —
   `flawless chef's knife` reads as `flawed chef's knife`.
3. **False sounds.** *"You hear something breathing behind you."* No source.
4. **Mutation misfire.** A small failure chance on mental mutations that spends the cooldown and
   prints something unsettling.
5. **Strange narration.** Fatigue messages carry `=WEIRDMARKOVSENTENCE=`, so the prose itself decays
   as the character does.

**Number 5 replaces what used to be here, and the original was built on a misreading.** The old text
proposed that *"the cyan Markov dream text that normally only appears when telepathically reading a
sleeper starts appearing while the player is awake."* That text is `Asleep.GetSleepMessage` under
`Mental && !Physical` — it is what a psychic observer sees looking **at** a sleeper, it never reaches
the sleeper, and there is no path by which it reaches a waking player at all.

The register it wanted is real and easier to get: `=WEIRDMARKOVSENTENCE=` is a registered variable
replacer that runs a Markov sentence through `Grammar.Weirdify`. Anything going through
`GameText.VariableReplace` can carry it, so **this costs no C# whatever** — a fatigue message is
authored data with a token in it.

### 4.1 Dreams as reward — quoting, not generating

On a **full, uninterrupted** sleep (fatigue reaches 0 without being woken), roll for a dream.

> **Amended by #818.** As written this fires on *every* qualifying sleep, and shipped that way. But
> sleeping is refused only at fatigue zero, so lying down at 1 and waking at 0 qualifies — about 24
> turns for a dream, against one per 1,500 in ordinary play, and free of risk in a settlement. A
> dream now also requires having been at least **Tired** when you lay down, and then rolls at
> **50%**. The tier split below is unchanged apart from the portent, now 25%.
>
> **The gate is fatigue rather than odds, and that distinction is the lesson.** A rarer roll only
> lengthens a cheap loop; it does not close one. See `docs/FEATURES.md` §51.5a.

- **Common (~60%):** the dream quotes something the character actually did, drawn from
  `JournalAPI.Accomplishments`.
- **Uncommon (~30%):** a *portent* — reveals a nearby zone's contents, or marks an unexplored
  location on the world map.
- **Rare (~10%):** a **psychic echo** tying into Qud's Sultan and dream lore. A small temporary buff,
  a lore fragment, or +1 to a random mental mutation for a few hundred turns.

**The common tier was impossible as originally written.** It asked for text *"Markov-generated from
the player's recent history — creatures killed, zones visited, items carried."* Both generators load
a fixed shipped corpus:

```csharp
string text = "LibraryCorpus.json";
MarkovBook.EnsureCorpusLoaded(text);
return MarkovChain.GenerateParagraph(MarkovBook.CorpusData[text]);
```

`LibraryCorpus.json` is built offline by `MarkovCorpusGenerator` from books, conversations and
downloaded texts. It is **static game lore and contains nothing about the player**. No parameter
threads history into it.

**The store that does exist is better than the one that did not.** `JournalAPI.Accomplishments` is a
public static, serialised `List<JournalAccomplishment>`, and every entry carries `Time`, `Category`,
`MuralText`, `GospelText`, `MuralCategory` and `MuralWeight` — timestamped deeds with **pre-authored
prose in two registers**. The Cyclopean Prism shows the shape: a text reading *"You clutched the black
glass of the =this.refname= in your hands"* beside a hagiograph in the gospel voice.

So the common tier is **a list read**, not a corpus project. A dream that quotes what the character
did, in prose Freehold already wrote, in the gospel register when it wants to sound like myth — that
is a better version of the original idea, and it is the cheapest thing in this section rather than the
most expensive.

> **The pattern worth carrying out of this section.** Twice, the document reached for *generation*
> where the game offers *authored text plus a capability consequence*. §3.2 wanted a stat ladder where
> vanilla refuses an action; §4 wanted generated history where vanilla ships a journal. Both times the
> shipped mechanism is smaller, more idiomatic, and better.

This flips the mod's valence either way. Sleep stops being a tax and becomes something the player
*wants* to do properly, in a safe place, uninterrupted. **Design the reward before the punishment.**

---

## 5. File layout

```
SleepAndFatigue/
├── manifest.json
├── Options.xml                      # must contain "Option" in the filename
└── Scripts/
    ├── FatiguePart.cs               # IPart on the player: accrual, thresholds
    ├── FatigueEffects.cs            # Tired / Weary / Exhausted effect classes
    ├── SleepAction.cs               # the Sleep command, rest-quality calc, ambush roll
    ├── Hallucination.cs             # the §4 perception layer
    ├── DreamSystem.cs               # dream rolls and payloads
    └── ModOptions.cs                # [OptionFlag] fields
```

`manifest.json` — `ID`, `Title`, `Version`, `Description`. Note `LoadOrder` is
deprecated as of build 210; use `LoadBefore` / `LoadAfter` if ordering ever matters.
This mod shouldn't need either.

Qud compiles loose `.cs` at runtime and checks the mod assembly **before** the game
assembly, so no build pipeline is needed. Compile errors go to `build-log.txt`.

---

## 6. Edge cases

The core loop is a weekend. **This list is the actual schedule.** Every one of these
is a way the mod breaks or becomes exploitable.

**Must handle before release**

- [x] **Sleep gas must not clear fatigue.** **Settled by vanilla.** `Asleep.Voluntary` is false at
      every involuntary call site and true at every voluntary one, so a fatigue system clears fatigue
      only when it reads true. One field, no plumbing.
- [x] **Rest-until-healed** — **there is no fast-forward to plug.** `BeginTakeActionEvent.Check` has
      exactly two call sites in the game: `ActionManager` line 743, the per-actor scheduler, and
      `TerrainTravel` line 233. Resting is ordinary turns through the scheduler, so it already
      accrues. It accrues at the *base* rate rather than a reduced resting one, and `Stomach` does not
      slow hunger while resting either. The consequence is a good one: rest long enough to heal and
      you eventually collapse into real sleep.
- [x] **Overland travel** — **done, and the first attempt created exactly this hole.** The turn is
      stamped on entry and the debt paid on return, `Stomach`'s own pattern. But the catch-up was
      first capped at 1,200 turns, which is one parasang of North Sheva — so a twenty-parasang haul
      cost the same as one bad crossing, and the map was nearly free after all. The cap is now a
      sanity bound only; `Set` clamping at `Max` does the game-facing work. One parasang is 300 ticks
      across ordinary ground and 1,200 across North Sheva, per `docs/STYLEGUIDE.md` §3.2.1.
- [x] **Narcolepsy** — **narrowed, and no longer an exploit.** `Narcolepsy.cs` constructs
      `new Asleep(Stat.Random(20, 29), forced: true)` with `Voluntary` defaulting false, so narcoleptic
      sleep would not clear fatigue either. What remains is a tuning question — whether involuntary
      sleep should rest the character *at all*, or whether narcolepsy plus fatigue means being knocked
      down repeatedly and never rested. Tracked separately.
- [x] **Wakeful** — **already vanilla behaviour, nothing to build.** `Wakeful` registers for and
      refuses only `CanApplyInvoluntarySleep` and `ApplyInvoluntarySleep`. `GasSleep` fires the check;
      `Bed` never goes near it.
- [x] **Unbreathing / robotic True Kin and cybernetics** — **decided: no exemptions.** No build
      skips the timer; a body that does not breathe still gets tired. The "Sleep Suppressor"
      cybernetic that halves accrual is new content rather than an edge case, and is tracked
      separately.
- [x] **Per-turn state on the player** — **the precedent is `Stomach`.** Vanilla's own survival timer
      is a plain `IPart` with public int fields (`Water`, `HungerLevel`, `CookingCounter`,
      `RegenCounter`, `HitCounter`), no custom serialisation, declared as `<part Name="Stomach" />`.
      This fork already ships 59 parts of that shape and `serializable-shape` covers them.
- [x] **Saving mid-sleep** — **nothing to build.** `GameObject.IntProperty` is written and read by
      the save serialiser (`GameObject.cs` lines 1929 and 2069), so all four fatigue keys round-trip
      on their own. `Asleep` is vanilla's own serialised effect and `Vixy_Gutter` holds no state.
- [x] **Death while asleep** — **nothing to clean up.** Every piece of fatigue state is a property
      on the body that died, so it goes with the body. A replacement body starts at zero, which is
      the right answer.
- [x] **Companions and followers** — **already exempt.** `Vixy_Fatigue` is declared in no blueprint
      and is attached only through `Vixy_PlayerParts.Attach(The.Player)`.
- [x] **Dominated / possessed bodies** — **this was the one real hole, and it was wide.**
      `Domination.Dominate` assigns `The.Game.Player.Body = defender`, so the puppet becomes the
      player and the true body stops answering `IsPlayer()`. The puppet never carries the part, and
      the true body's `Dominating` effect returns false from its own `BeginTakeActionEvent` handler,
      which zeroes that body's energy and halts the dispatch chain — so whether the part is even
      reached is part-versus-effect ordering rather than anything to rely on. Duration is
      `100 * (Level + 1)` rounds against a 75-round cooldown: about 1,100 free rounds at rank 10,
      recastable before it lapses.

      Fixed by generalising the world-map catch-up rather than adding a second mechanism beside it.
      The turn fatigue was last charged is stamped on every action, and a gap wider than
      `GapThreshold` is billed at the base rate on return. The map was the first gap of this shape
      and domination the second; any future one is billed with nothing new written.

**Should handle**

- [x] Amnesia / madness effects interacting with the hallucination layer — **moot.** There is no
      hallucination layer. False sounds were investigated and dropped, because Qud has eight distinct
      "You hear" strings in the whole assembly and every one names its own cause, so a phantom noise
      would have had no true counterpart to be mistaken for. See `docs/LESSONS.md`.
- [x] Zone regeneration while asleep for 250 turns — **cannot happen.** The player's own zone is
      never suspended or frozen; `ZoneManager` line 897 logs an error if anything tries.
- [x] Very high Quickness — **the concern is inverted, and the answer is precedent.** This assumed
      `EndTurnEvent`. Accrual is on `BeginTakeActionEvent`, which `ActionManager` fires per action
      opportunity, so fatigue tracks exertion rather than the clock — a quick character covers more
      ground for the same fatigue, and pays the same per action. `Stomach` uses the same event, so
      whatever bias this carries, hunger and thirst carry it identically.

---

## 7. API notes and verification

Confirmed from documentation:

- Custom parts inherit `IPart` and want `[Serializable]`.
- `WantEvent(int ID, int cascade)` to register; `HandleEvent(SpecificEvent E)` to
  handle. Keep `WantEvent` lean — it runs on every event fired.
- `EndTurnEvent` fires once per standard turn — **this is the accrual hook**.
  `EndActionEvent` fires per player action; `EndSegmentEvent` fires 10× per turn.
- Mod options: an XML file with `Option` in its name, root `<options>`, types
  `Checkbox` / `Combo` / `BigCombo` / `Slider` / `Button`. Read them with the
  `[OptionFlag]` attribute on fields in a `[HasOptionFlagUpdate]` class — preferred
  over the legacy `Options.GetOption(ID)` string call.

**Everything on this list has now been checked.** The last item was *"the API for the telepathy dream
text generator"*, and checking it found there is no such thing: `Asleep.GetSleepMessage` is a display
for a psychic **observer**, not a dream system, and it never reaches the sleeper. §2 and §4 are
rewritten accordingly. The register that section wanted is `=WEIRDMARKOVSENTENCE=`, a registered
variable replacer reachable from data with no C#.

`Asleep` and `Wakeful` were on this list and have been checked (#687). Both resolved as
**already satisfied** rather than as requirements — see the two rows in §2, which name the
mechanism in each case. That is the pattern `docs/LESSONS.md` records: this document
assumed less of Qud than Qud ships. Generate `Mods.csproj` from the in-game Modding Utilities (needs Mouse
Overlay UI enabled) to get IntelliSense over the real namespaces, or decompile
`Assembly-CSharp.dll` with ILSpy.

**No Harmony needed.** Everything here is a part, an effect, or a command. That's a
significant maintenance advantage — Harmony patches break on game updates and Freehold
explicitly recommends treating them as a last resort.

---

## 8. Build order

1. `FatiguePart` + `EndTurnEvent` accrual + a debug readout. Verify the number moves.
2. Voluntary sleep command, reusing vanilla `Asleep`. Verify fatigue drains and the
   player wakes.
3. Threshold effects with stat penalties only. Playable, boring, correct.
4. **Edge-case pass** (§6). Do this before content, not after — it will change numbers.
5. Hallucination layer. This is where the mod becomes worth playing.
6. Dream rewards.
7. Mod options for every number in §3.

Steps 1–3 are a weekend. Step 4 is the real work. Steps 5–6 are why you'd bother.

---

## Sources

- [Modding:C Sharp Scripting](https://wiki.cavesofqud.com/wiki/Modding:C_Sharp_Scripting)
- [Modding:Parts](https://wiki.cavesofqud.com/wiki/Modding:Parts)
- [Modding:Turns, Segments, and Actions](https://wiki.cavesofqud.com/wiki/Modding:Turns,_Segments,_and_Actions)
- [Modding:Events](https://wiki.cavesofqud.com/wiki/Modding:Events)
- [Modding:Options](https://wiki.cavesofqud.com/wiki/Modding:Options)
- [Modding:Harmony](https://wiki.cavesofqud.com/wiki/Modding:Harmony)
- [Asleep](https://wiki.cavesofqud.com/wiki/Asleep)
