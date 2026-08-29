# Burden & Difficulty — design doc

**Status:** spec only, no code written
**Target:** Caves of Qud, build 210+
**Scope:** recommend shipping as **two or three separate mods**, not one. See §1.

---

## 1. Split it up

Burden rework, XP curve, and exploit patching have different audiences, different
failure modes, and very different maintenance costs. Bundled, anyone who wants the
burden system has to swallow your opinion about XP too, and a game update that breaks
one exploit patch takes the whole mod down with it.

**Recommendation:** `QudBurden` ships standalone. XP curve ships standalone. Exploit
patching either doesn't ship or ships last, separately, with eyes open.

If you insist on one package, put **every** component behind a mod option defaulted to
**off** and treat the mod as a menu rather than a stance.

There is also a framing question worth settling before writing anything:

> **"Harder" and "less exploitable" are different goals.**
> Qud's difficulty is mostly a knowledge check. Closing an exploit doesn't make the
> game harder for a new player — it lowers the ceiling for a veteran. Decide which
> player you're designing for, because the two rarely want the same patch.

---

## 2. Burden — the strongest of the three ideas

### 2.1 Why it's undercooked in vanilla

Verified: carry capacity is **15 × Strength**. Exceeding it applies **Overburdened**,
which makes you **unable to move**, full stop, until you drop something.

That's a **binary cliff**. You are either completely unaffected or completely immobile.
There is no gradient, so there is no interesting decision — the optimal play is to sit
at 99% capacity forever, and the system never once makes you think.

This is a genuine design gap, it's self-contained, and it doesn't require Harmony.
It's the best thing in this document.

### 2.2 Proposed graded bands

Let `L = CarriedWeight / CarryCapacity`.

| Band | Load | Effect |
|---|---|---|
| Unburdened | ≤ 50% | none |
| Light | 50–75% | −1 DV |
| Encumbered | 75–90% | −2 DV, −1 Quickness per 10% over 75 |
| Heavy | 90–100% | −4 DV, −10 Quickness, stealth penalty, **+50% fatigue accrual** (if the sleep mod is installed) |
| Overburdened | 100–125% | −6 DV, −25 Quickness, cannot run, movement costs double |
| Immobile | > 125% | unable to move — vanilla behaviour, but now it takes real commitment to reach |

The important change is that **vanilla's cliff moves from 100% to 125%**, and the space
underneath it fills with graded consequence. The player now feels the weight before it
stops them, which is the entire point.

### 2.3 Second-order effects worth adding

These are what turn a penalty table into a system:

- **Swimming / deep water.** Heavy or worse should risk dropping items, or forbid entry
  outright. Qud has water; nothing currently makes you respect it.
- **Falling damage** scales with load.
- **Noise.** Encumbered upward increases the radius at which sleeping creatures wake.
  Pairs directly with the sleep mod's ambush rolls.
- **Container weight.** Consider whether packs should reduce carried weight rather than
  just organise it — vanilla already has suspensor mods and negative-weight spheres, so
  there's precedent and a tuning baseline.

### 2.4 Implementation

The clean hook is the event that computes carry capacity / carried weight. **Verify the
exact event class name against the game assembly** — the community has discussed
modifying carry capacity via cybernetics, so the hook exists, but I could not confirm
the identifier from documentation alone.

Apply the band as an **effect** that the part refreshes on `EndTurnEvent` (or on
inventory-change events, which is cheaper — prefer those if they exist and fall back to
per-turn). Effects are the right vehicle because they display in the UI, serialise
with the save, and stack predictably with other sources.

**No Harmony required** if the capacity event is exposed. That keeps this mod
maintainable across updates, which is the main reason to build this one first.

---

## 3. XP curve — proceed carefully

### 3.1 What vanilla does

Total XP to reach level *x* is **15x³ + 100**. Cubic.

Kill XP scales by tier difference, where tier = `Floor(Level / 5)`:

| Tier difference | XP awarded |
|---|---|
| ≤ 0 | 100% |
| 1 | 50% |
| 2 | 10% |
| 3+ | 0% |

Only the killer (and their followers/party leader) receives XP.

### 3.2 What "smoother" actually means

The cubic curve is already steep — each level costs disproportionately more than the
last. Before touching it, be precise about the complaint:

- **"Early levels fly by"** → the problem is the *low* end of the cubic, where 15x³ is
  tiny. Fix by adding a constant or raising the early exponent, not by flattening the
  whole curve.
- **"Late levels take forever"** → that's the cubic working as intended. Flattening it
  makes the game *easier*, the opposite of this mod's stated goal.
- **"Levelling is lumpy"** → that's the tier-difference cliff, not the curve. A single
  kill going from 50% to 10% to 0% as you level is a much sharper discontinuity than
  anything in 15x³. **Smoothing the tier falloff into a continuous function is probably
  the change you actually want**, and it's a smaller, safer edit than rewriting the
  curve.

Recommendation: **change the tier falloff, leave 15x³ + 100 alone.** Replace the step
table with something like a geometric decay so a tier-2 kill is worth ~25% rather than
snapping to 10%.

### 3.3 Knock-ons to check

XP is entangled with more than combat:

- Quest rewards are flat XP grants — a curve change shifts their relative value
  silently.
- Water-ritual reputation and non-combat XP sources exist and are documented as
  incomplete on the wiki; test them explicitly.
- Skill points per level are `70 (True Kin) or 50 (Mutant) + 4 × (Int − 10)` — changing
  levelling *pace* changes skill-point income, which is a bigger balance lever than the
  levels themselves.
- Mutation points: 1/level for mutants. Same issue.

**A flat multiplier on the XP curve is not a small change.** It silently rebalances
skills, mutations, and quest value all at once.

---

## 4. Exploit patching — read this before committing

This is the highest ongoing-maintenance thing in the entire project.

Harmony **is bundled** with the base game, so there's no dependency problem. But
Freehold's own guidance is explicit: patches are "more prone to incompatibility with
other mods and future updates," and they recommend treating Harmony as a **last
resort**, preferring data-driven solutions and asking for better hooks instead.

Their compatibility ranking:

- **Safest:** postfix patches, and prefixes that don't block execution
- **Avoid:** prefixes that block, and transpilers that rewrite IL — these conflict with
  other mods frequently

Practical consequences:

1. Every patch targets an internal method that can be renamed or restructured in any
   update. You are signing up for maintenance **forever**, not once.
2. Patching an exploit that another popular mod depends on will break that mod, and
   your users will report it to you.
3. Prefer XML/data edits and public events over patches wherever the same outcome is
   reachable. A slightly worse fix that survives updates beats a perfect fix that
   breaks monthly.

**Recommendation:** don't ship this in the first release. Build burden, see how
maintenance feels across one or two game updates, then decide whether you want this
commitment.

---

## 5. Mod options

Every number in this document should be player-configurable. An XML file with `Option`
in its filename, root `<options>` element, using:

- `Checkbox` — enable/disable each subsystem (**default off** for anything opinionated)
- `Slider` — band thresholds, penalty magnitudes, XP multipliers (`Min`, `Max`,
  `Increment`)
- `Combo` / `BigCombo` — preset difficulty profiles

Read values via the `[OptionFlag]` attribute on fields in a `[HasOptionFlagUpdate]`
class rather than the legacy `Options.GetOption(ID)` string lookup.

Mod options are what let one package serve players who want only one piece of it. If
you do ship this bundled, this section is not optional.

---

## 6. File layout

```
QudBurden/                          # ship this one first, standalone
├── manifest.json
├── BurdenOptions.xml
└── Scripts/
    ├── BurdenPart.cs               # band calculation, refresh on inventory change
    ├── BurdenEffects.cs            # Light / Encumbered / Heavy / Overburdened
    └── BurdenOptions.cs            # [OptionFlag] fields

QudXPCurve/                         # separate mod
├── manifest.json
├── XPOptions.xml
└── Scripts/
    └── TierFalloff.cs              # smooth the tier-difference step function
```

---

## 7. Build order

1. **`QudBurden` alone.** Graded bands, effects, mod options. No Harmony. Ship it.
2. Live with it for a game update. Learn what maintenance actually costs you.
3. **Tier-falloff smoothing** as a second small mod, if you still want it after §3.2.
4. Exploit patching only if steps 1–3 left you wanting it, and only with §4 understood.

Burden is the one with a clear design gap, a clean implementation path, no Harmony
dependency, and an audience that doesn't need to agree with you about anything else.
Start there.

---

## Sources

- [Carry capacity](https://wiki.cavesofqud.com/wiki/Carry_capacity)
- [Overburdened](https://wiki.cavesofqud.com/wiki/Overburdened)
- [Experience](https://wiki.cavesofqud.com/wiki/Experience)
- [Modding:Harmony](https://wiki.cavesofqud.com/wiki/Modding:Harmony)
- [Modding:Options](https://wiki.cavesofqud.com/wiki/Modding:Options)
- [Modding:Events](https://wiki.cavesofqud.com/wiki/Modding:Events)
- [Modding:C Sharp Scripting](https://wiki.cavesofqud.com/wiki/Modding:C_Sharp_Scripting)
