# Balance — design doc

**Status:** audit complete. 20 findings filed under [#315](https://github.com/vixygrey/qud-expanded-community-edition/issues/315). **All four questions are settled** — §3.9, §4, §5 and §6. What remains is implementation.
**Target:** Caves of Qud 2.0.211.x, Steam build 20250808.
**Premise:** nothing in this mod should be blatantly stronger than what vanilla prices the same effect at.

`docs/DESIGN_options.md` is the model for this document — the design work behind a decision, kept so
the reasoning does not have to be rebuilt from the diff. Where this and `docs/CHARTER.md` touch,
the charter wins.

---

## 0. Why this document exists

I compared every blueprint the mod ships or merges against the game's own data, and decompiled the
combat, armour, tinkering and levelling code so that no claim rests on memory. Twenty findings came
out of it, four of them blatant by the plainest test available: **vanilla already prices the same
effect, and prices it far higher.**

Most of what follows is not a list of numbers to change. It is the reasoning and the verified
mechanics behind them, because the numbers are the cheap part. Section 2 in particular is written to
be read before anyone proposes a value — I got two mechanics wrong on the first pass, and both
mistakes would have produced a confident, wrong fix.

**The audit's own conclusion is that the numbers are not the problem.** `docs/STYLEGUIDE.md` §3.2
states a tier→material table and a value curve, and both have held perfectly across four releases.
Every number that drifted is a number §3.2 does not mention. That is the finding under the findings.

---

## 1. Method

Vanilla read through `tools/check_vanilla_drift.py`'s `parse(path, lenient=True)` — **5,202
blueprints**. A strict parser silently loses `Items.xml` and most of the comparison with it, which
`docs/LESSONS.md` already warns about and which I nearly repeated. Mod merges were applied on top
with the same inheritance resolution Qud uses, then compared field by field.

Mechanics were not assumed. These types were decompiled from `Assembly-CSharp.dll`:

`Combat` · `MeleeWeapon` · `MissileWeapon` · `ThrownWeapon` · `Armor` · `BodyPart` · `Body` ·
`ModGigantic` · `ModEntry` · `ModificationFactory` · `TinkerData` · `ModImprovedMutationBase<T>` ·
`HeightenedSpeed` · `Regeneration` · `Precognition` · `TemporalFugue` · `Leveler` · `Stat` ·
`Stats` · `RuleSettings` · `GetToHitModifierEvent` · `GetMeleeAttackChanceEvent` ·
`Multiweapon_Proficiency` / `_Expertise` / `_Mastery` · `ShortBlades` · `Cudgel_Slam`

Reading the DLL rather than the XML docs is `docs/LESSONS.md`'s standing advice and it earned its
keep twice here — see §2.2 and §2.4, both of which contradict what the field names suggest.

---

## 2. Verified mechanics

Read this before proposing any number.

### 2.1 `MeleeWeapon.Stat` names the penetration stat, not a damage stat

`Combat.MeleeAttackWithWeaponInternal` sets `string text2 = "Strength"` and then immediately
overwrites it with `text2 = Part.Stat`. Strength is only the *default value of the attribute* — the
engine has no opinion about which stat a weapon uses. That value then feeds:

```csharp
int StatBonus = (Part == null || !Part.HasTag("WeaponIgnoreStrength"))
    ? Attacker.StatMod(text2) : 0;
...
Penetrations = Stat.RollDamagePenetrations(AV, StatBonus + PenBonus + …, num + …);
```

There is **no Strength term anywhere in the damage path**. Damage is
`Σ over Penetrations of roll(BaseDamage)`. But the stat still governs output, because penetration
decides how many times the die is rolled. A weapon's `Stat` is a multiplier on its whole damage, not
an addend to it.

`Stat` also accepts a comma list — `Combat` and `MeleeWeapon.GetNormalPenetration` both expand it
and take the best. **No vanilla blueprint and none of the 87 installed Workshop mods use that form**,
so it is an untrodden path; the tooltip would render it literally as `Strength,Agility Bonus Cap: 9`.

### 2.2 The penetration loop decays its own bonus

`Stat.RollDamagePenetrations(TargetInclusive, Bonus, MaxBonus)`:

- three dice per wave, each `Random(1,10) - 2`, exploding on 8
- each die adds `min(Bonus, MaxBonus)`; it hits if the total **exceeds** the defender's AV
- **at least one hit scores exactly one penetration** — `if (num2 >= 1) num++`, not one per die
- **all three hits rolls another wave**, and `Bonus -= 2` runs every wave, so the chain terminates
- `MaxBonus` is the weapon's `MaxStrengthBonus` plus its `PenBonus`

I modelled this wrong the first time by reading only the top half of the method — one penetration
per hitting die, unbounded waves — and got a curve roughly twice as steep as the real one. The two
guards are in the tail. See `docs/LESSONS.md`.

`Long Sword8th` (`2d12+1`, `PenBonus 1`, cap 9), average damage per connecting hit:

| Strength | mod | vs AV 6 | vs AV 10 | vs AV 14 |
|---|---|---|---|---|
| 16 | 0 | 9.3 | 2.7 | 1.2 |
| 20 | 2 | 13.4 | 3.5 | 2.0 |
| 24 | 4 | 18.2 | 9.3 | 2.7 |
| 28 | 6 | 27.3 | 13.4 | 3.5 |
| 32 | 8 | 41.3 | 18.2 | 9.3 |

Nothing changes but the score. That is why `Stat` is the highest-leverage attribute on any weapon
blueprint.

### 2.3 What each attribute actually does in combat

| | Strength | Agility |
|---|---|---|
| Melee penetration | `MeleeWeapon.Stat` on **4,351 of 4,354** vanilla weapons | **0** vanilla weapons |
| Thrown penetration | `ThrownWeapon.cs:107`, hardcoded `Stat("Strength")` | — |
| Missile penetration | `ProjectilePenetrationStat` on the Compound Bow and Turbow — the only two ranged weapons that scale at all | — |
| Melee to-hit | — | `GetToHitModifierEvent.GetFor` opens with `Bonus + Actor.StatMod("Agility")`, unconditional, **no exemption** |
| Missile / thrown accuracy | — | yes |
| DV | — | `Stats.GetCombatDV` = `6 + level + StatMod("Agility")` |
| Short Blades bleed | — | duration `20 + StatMod("Agility")`, stacks capped at `1 + StatMod("Agility")` |

The three vanilla melee weapons that are not Strength are all `Ego`: two lamprey bites and the Tau
Dagger.

> **Strength is the only stat in Caves of Qud that scales weapon damage, in any mode. Agility is
> deliberately an accuracy-and-defence stat.** That is held across 4,440 weapons with three named
> exceptions.

`WeaponIgnoreStrength` zeroes the *penetration* bonus only; it returns early in
`GetNormalPenetration` and never touches the to-hit line. There is no Agility equivalent.

`StatMod` is `floor((score - 16) / 2)` — `Stat.GetScoreModifier`.

Two skills read Strength directly regardless of the weapon's `Stat`: `Cudgel_Slam`
(`SlamPower = StatMod("Strength") * 5 * multiplier`) and `Shield_Slam`.

### 2.4 Every body part with a weapon gets its own attack

`BodyPart.ScanForWeapon` walks the whole body recursively. For each part, if `Equipped ??
DefaultBehavior` has a `MeleeWeapon` and `AttackFromPart(this)` passes, the part is appended to
`PartList` — and `Combat.PerformMeleeAttack` makes one attack attempt per part in that list.

`MeleeWeapon.AttackFromPart` is a *restriction*, not a grant:

```csharp
if (Part.PreferredPrimary) return true;
if (string.IsNullOrEmpty(Slot)) return true;
if (Part.Type == null) return true;
if (!(Slot == Part.Type)) return Slot == Part.VariantType;
return true;
```

So `Slot="Arm"` means the weapon attacks **only** from an Arm — it cannot be stacked into hands —
but an Arm holding one is a fourth limb alongside two hands and another arm.

Only the first part in the list is primary. The rest roll against
`RuleSettings.BASE_SECONDARY_ATTACK_CHANCE`, which is **15**, plus Multiweapon Proficiency +20,
Expertise +15 and Mastery +15 — 65% fully invested.

One `Equipped` per `BodyPart`, so a weapon in a slot excludes armour in that slot.

### 2.5 Armour

`Armor.AV` is additive per piece onto the AV stat — `who.GetStat("AV").Bonus += num`. `SpeedBonus`
is Quickness: `SetStatShift(who, "Speed", SpeedBonus - SpeedPenalty)`, and the description text
calls it Quickness in as many words. Real `Armor` fields include `MA`, `CarryBonus`, `ToHit`,
`SpeedPenalty` and the four resistances, so those are applied rather than ignored.

### 2.6 Chips stack on mutations the character already has

`ModImprovedMutationBase<T>.HandleEvent(GetShortDescriptionEvent)` states its own rule:

> Grants you *X* at level *N*. **If you already have *X*, its level is increased by *N*.**

Nothing caps the total. Level curves worth knowing: `HeightenedSpeed` gives `13 + 2 × Level`
Quickness, so even level 1 is +15; `TemporalFugue` gives `(Level - 1) / 2 + 1` copies;
`Precognition` gives `4 × Level + 12` rounds.

### 2.7 Item mods merge by `Part`, and `TinkerAllowed` is the whole gate

`ModificationFactory.LoadModNode` looks an entry up by `Part` and overwrites only the attributes
present, so `Load="Merge"` on a `<mod>` is inert — the merge behaves identically without it.
`TinkerData.TinkerRecipes` adds every entry with `TinkerAllowed` to the recipe list at its
`TinkerTier`, which **defaults to 1** when unstated.

### 2.8 Levelling

`Leveler.RollSP` is `Stat.RollLevelupChoice(BaseSPGain) + (BaseStat("Intelligence") - 10) * 4`. So
one point of Intelligence is 4 skill points per level, and −6 Intelligence is −24 per level.
`RollHP` adds the Toughness modifier and floors at 1.

---

## 3. Question one — where should Agility scaling sit?

**Settled. The outcome is in §3.9; §3.1–§3.8 are the reasoning that got there.**
Tracked in [#321](https://github.com/vixygrey/qud-expanded-community-edition/issues/321).

### 3.1 Provenance — the swaps are undocumented

`docs/mura-feature-notes-wip.txt` describes three skill changes, and all three are in `Skills.xml`
exactly as written:

> Axe and Cudgel skills can now use either Strength or Agility for minimum requirements. Mind you,
> this does not change the skills themselves […] but it does give you access to more skills.

> Reduces Strength/Agility requirements for Multiweapon Expertise and Mastery by 2 points.

> Removes secondary stat requirement from En Garde! (Long Blade).

**No writeup mentions weapon `Stat` anywhere** — not the WIP notes, not `docs/2.2-changelog.txt`,
not the pinned Workshop list. So the 20 vanilla-weapon swaps sit outside every document Mura left,
while the new families' Agility scaling is a stated theme in `docs/STYLEGUIDE.md` §3.2. Two changes
with two different amounts of intent behind them, read for years as one thing.

That matters for charter rule 2. The skill regating has a stated reason and clears the bar. The
weapon swaps have never had one written down.

### 3.2 Where the switch lands

45 vanilla weapons end up on Agility: 20 by their own merge, 25 by inheriting a switched base.
`BaseDagger` alone reaches 17 of those, including `ForceKnife`, `Difucila`, `AoygDagger`,
`BloodyDagger3` and `TutorialDagger` — the same blast-radius shape the charter flags for
`Chip Interface` into `Humanoid`.

| family | T0 | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 |
|---|---|---|---|---|---|---|---|---|---|
| Long blade 1H | str | str | str | str | str | str | str | str | str |
| Long blade 2H | str | str | str | str | str | str | str | str | str |
| Axe 1H | str | str | str | str | str | str | str | str | str |
| **Axe 2H** | str | str | str | str | str | str | **AGI** | **AGI** | **AGI** |
| **Cudgel 1H** | str | **AGI** | both | **AGI** | **AGI** | **AGI** | str | str | **AGI** |
| **Cudgel 2H** | str | str | **AGI** | **AGI** | **AGI** | str | **AGI** | **AGI** | **AGI** |
| **Short blade** | **AGI** | **AGI** | **AGI** | **AGI** | **AGI** | **AGI** | **AGI** | **AGI** | **AGI** |

Bold is a vanilla blueprint the mod switched.

**Long blades is the theme done correctly.** Vanilla stays Strength across all nine tiers, and the
rapier and katana lines are a complete Agility path beside it, stat line for stat line. Three
families deviate, each differently:

- **Cudgel — no rule produces this.** Every tier already has a matched Strength/Agility pair with
  identical damage. Which side the *vanilla* blueprint sits on simply flips. `Cudgel5th` is Strength
  while `Cudgel4th` and `Cudgel6th` are Agility. Reverting nine attributes builds nothing, because
  the Agility twin already exists at every tier.
- **Axe 2H — a gap-fill with a real cause.** `Battle Axe6th/7th/8th` were switched because the
  halberd line stops at tier 5. Those three cells are the only Agility two-handed axe in the late
  game. Three new blueprints close it properly.
- **Short blade — the one with a genuine cost.** Reverting `BaseDagger` leaves the wristblade as the
  only Agility short blade, and the wristblade trails the dagger at every tier. See §3.7, which
  argues that gap should *widen* rather than close.

### 3.3 What D&D 5e does — the finesse property

The mechanism is a weapon property: *you may use Strength or Dexterity for the attack **and** damage
rolls, but the same modifier for both.* Four things make it work:

- a **property on a published, closed list** — dagger, dart, rapier, scimitar, shortsword, whip —
  not a per-item stat override
- a **choice, not a swap**; a Strength fighter with a rapier still uses Strength
- **light one-handed piercing or slashing only**. Finesse never coexists with `heavy` or
  `two-handed`. There is no finesse greataxe, maul or halberd, by rule
- **paid for in the damage die.** Finesse tops out at d8; Strength-only martial weapons get d10,
  d12, 2d6, plus reach and versatile

And then the warning, which is the more useful half: 5e is the system where **Dexterity became the
god stat** — AC, initiative, the three saves that matter, Stealth, ranged attacks, *and* finesse
melee. That critique is as old as the edition and it was never fixed. Finesse is where it came from.

### 3.4 What Pathfinder does — the split

- **PF2e `finesse`**: use Dexterity instead of Strength **on attack rolls**. Damage still uses
  Strength. No exceptions.
- **PF2e `agile`**: lower multiple-attack penalty, paired with a smaller damage die.
- **PF1e**: Weapon Finesse is a **feat**, a build resource. Getting Dexterity onto *damage* needs a
  further class-locked feature — Slashing Grace, Dervish Dance, the Thief racket. Never free, never
  automatic.

> **Pathfinder's principle: accuracy may cross over freely; damage must be bought.**

### 3.5 Qud is already Pathfinder

Agility → to-hit, free, universal, every weapon. Strength → penetration, which is the damage
multiplier. That is PF2e's finesse rule *as the default state of the entire game* — every Qud weapon
is already a finesse weapon in PF2e's sense.

So the vanilla-weapon swaps do not *add* finesse. Qud already has it everywhere, for free. What they
do is the one thing both Pathfinder editions specifically refuse: hand the damage stat to the
accuracy stat at no cost.

### 3.6 The gun-build objection

Agility is the gun stat, and **guns have no penetration stat at all** — `ProjectilePenetrationStat`
is unset on 84 of vanilla's 86 ranged weapons, and the two that set it use Strength for draw weight.

So a rifle build maxes Agility purely for accuracy and gets **zero** damage scaling on its own
weapon. Under the current design that same build picks up an Agility cudgel and gets full damage
scaling on a weapon it never invested in — better stat-scaling in melee than in its specialty. That
asymmetry is the sharpest argument against the swap, and it is the test the candidate designs in
§3.8 are sorted by.

### 3.7 Wristblades make the short-blade answer the opposite of the obvious one

Wristblades are `Slot="Arm"`, so by §2.4 they attack from a limb that costs no hand. Two swords plus
two wristblades is four attack attempts a round.

**The mechanic is vanilla's.** `ArmDagger4` is a vanilla blueprint whose display name is literally
*folded carbide wristblade* — `Slot="Arm"`, tier 4, in `Melee Weapons 5` at weight 20. Freehold
shipped one, at one tier. This mod completed it into nine and merged the original down from `1d8` to
`2d3`.

**What the mod broke is the opportunity cost.** In vanilla the Arm slot is where the utility
artifacts live — Kindrish, Otherpearl, Transkinetic Cuffs, Kah's Loop, Slip Ring, Ontological
Anchor, the Displacer and Force bracelets. Nearly all are AV 0, and the best AV in vanilla's entire
Arm slot is **1**. The trade is "an extra attack, or a unique artifact effect", and it is
interesting. The mod added the vambrace line to that slot, which looks like it raises the cost and
instead adds a weak competitor: at tier 8, two zetachrome vambraces are +6 AV against a ceiling
already at 48, or two zetachrome wristblades are +50% melee damage.

Tier 8, attacking stat mod +6, target AV 10:

| Multiweapon investment | 2 swords | 2 swords + 2 wristblades | |
|---|---|---|---|
| none (15%) | 10.31 | 12.03 | +17% |
| Proficiency (35%) | 12.11 | 16.10 | +33% |
| Expertise (50%) | 13.45 | 19.16 | +42% |
| Mastery (65%) | 14.80 | 22.22 | **+50%** |

The mod also cut Multiweapon Expertise 23→21 and Mastery 27→25, so the 65% row is cheaper to reach
than vanilla intended.

**The consequence for §3.2:** bringing the wristblade line up to dagger parity — which was my first
instinct — is backwards. It buys a whole extra attack, so it should sit *well* behind the dagger,
and 0.5 damage is not nearly enough. Tracked in
[#324](https://github.com/vixygrey/qud-expanded-community-edition/issues/324).

### 3.8 Candidate designs

Sorted by the §3.6 test: does a pure gun build get melee damage scaling it did not pay for?

| | Model | Mechanism | Passes? |
|---|---|---|---|
| **A** | PF2e-pure | No melee weapon uses `Stat="Agility"`. The Agility identity lives entirely in the skill trees — exactly, and only, what Mura documented. | yes |
| **B** | 5e finesse | Agility families take `Stat="Strength,Agility"`, one-handed only, one damage step below the Strength twin. | no, unless the damage step is steep |
| **C** | PF1e feat | Agility penetration comes from a **skill power**, not from the weapon. `GetWeaponMeleePenetrationEvent.Process` is the hook `Combat` already fires, so it is a `MinEvent` handler — no Harmony, no reflection, inside charter rule 5. | yes — a rifle build must spend points in a melee tree |
| **D** | Genre realignment | Orthogonal to all three: fix *which* weapons qualify. | — |

**D is worth doing whichever mechanism wins, and it is what reads worst today.** The mod's Agility
line is the halberd, war hammer and greathammer — three of the most archetypally Strength weapons in
existence — while its greataxe and mace lines are Strength. The rapier and wristblade are correct.
It is inverted precisely where genre convention is strongest.

**C + D was the recommendation, and it is what was chosen** — see §3.9. Together they answer the
gun objection and keep Mura's actual documented intent, more skill access for Agility builds, as the
thing the mod is *for*.

### 3.9 Settled — finesse is a purchased power

**Design C, with the Finesse power sold by Short Blades and Long Blades only, and the dagger line
finesse-eligible.**

Three things follow, and the first is the one that makes the rest simple: **C subsumes B.** If the
crossover is bought, every blueprint goes back to `Stat="Strength"` and the question stops being
"which weapons scale off Agility" — it becomes "which weapons *may*, and what does the licence
cost". An earlier draft of this section listed the rule and the build cost as separable decisions.
They are not, and B on its own does not answer §3.6: under B a rifle build simply picks up a
`Raven_` weapon and gets the scaling free.

**The shape.**

| Layer | Mechanism | Borrowed from |
|---|---|---|
| Which weapons qualify | `<tag Name="Finesse" />` on the blueprint | 5e's closed property list |
| Whether *you* may use it | a purchased power, one per eligible tree | PF1e's Weapon Finesse feat |
| What it does | raises `StatBonus` to `StatMod("Agility")` when higher | PF2e's split, priced |

Every melee blueprint reverts to `Stat="Strength"` — all 61 declarations, the 20 vanilla merges and
the 41 new ones alike. Nothing scales off Agility by default any more.

**Which trees sell it: Short Blades and Long Blades.** That is where genre convention is
unambiguous — 5e's finesse list is entirely daggers, rapiers, scimitars and shortswords — and it is
also what the trees themselves already say. Every power in vanilla's Short Blade tree is
`Attribute="Agility"`, and the Long Blade tree is deliberately mixed (Lunge on Agility, Swipe on
Strength, Dueling Stance on Intelligence). Axe and Cudgel stay Strength-only, which **reverses the
two most genre-inverted assignments in the mod**: the halberd and the war hammer.

**Tagged weapons:** the dagger line, the wristblade line, the rapier line, the katana line.
Daggers are the most genre-canonical finesse weapon in any system, and tagging them means the
wristblade no longer has to carry the Agility short blade role alone — which frees
[#324](https://github.com/vixygrey/qud-expanded-community-edition/issues/324) to widen the
wristblade's damage deficit rather than close it.

**Settled pricing: `Cost="250" Minimum="19"`.** An earlier draft proposed 21 against a generic
ladder; the trees' actual costs are Short Blade 0 / 100 / 150 / 250 and Long Blade 0 / 100 / 200 /
300, with minimums 17 / 21 / 23 / 25 / 27 / 29.

```xml
<power Name="Finesse" Cost="250" Attribute="Agility" Minimum="19"
       Class="Vixy_ShortBladesFinesse" ... />
```

**250** sits level with Rejoinder and Shank, below En Garde!'s 300, and above the closest mechanical
analogue in the game. `SingleWeaponFighting_PenetratingStrikes` handles the same event, costs **200
at Minimum 23**, and grants `E.Penetrations++` — a guaranteed extra damage roll, which is *stronger*
than Finesse at every AV. It charges for it, though: while toggled, `GetMeleeAttackChanceEvent` sets
`E.Multiplier = 0.0` on every non-primary attack, so it costs the whole offhand. Finesse has no
loadout cost, and its real value is not the damage anyway — reaching StrMod 4 from base 16 takes
**8 attribute points**, more than the 6 discretionary points a whole run awards, out of a chargen
pool of 34–44. Finesse refunds those into Agility, which also buys DV and to-hit. Less damage than
Penetrating Strikes, more total value, so it prices above it and below a capstone.

**19, not 21.** The gate should sit where the *decision* is still live: at Agility 21 a character has
already committed, so a higher minimum makes the power arrive after the choice it exists to license.
19 is the first odd score — vanilla's convention, since `StatMod` only moves on even scores — where
the modifier is non-zero. The gate is nearly decorative regardless, because `if (agi > E.StatBonus)`
self-limits: a Strength build that happens to reach Agility 19 gains exactly nothing.

Expected penetrations by bonus, from `Stat.RollDamagePenetrations` (three dice per wave, at most one
penetration per wave, `Bonus` decaying by 2):

| bonus | AV 4 | AV 8 | AV 12 |
|---:|---:|---:|---:|
| 0 | 0.815 | 0.221 | 0.115 |
| 3 | 1.302 | 0.664 | 0.196 |
| 4 | 1.561 | 0.815 | 0.221 |
| 6 | 2.561 | 1.112 | 0.490 |

A realistic finesse build runs +3 to +6, since `AddAttributeBonus` lifts Strength and Agility alike
and only discretionary points widen the gap.

**The C#** is a nine-line variation on a class Freehold already ships,
`SingleWeaponFighting_PenetratingStrikes` — a `BaseSkill` on the attacker that handles
`GetAttackerMeleePenetrationEvent` and mutates it. No instance fields, so `serializable-shape`
passes; no reflection, no Harmony, public members only.

```csharp
public override bool HandleEvent(GetAttackerMeleePenetrationEvent E)
{
    if (E.Weapon != null && E.Weapon.HasTag("Finesse")
        && E.Weapon.GetWeaponSkill() == "LongBlades")
    {
        int agi = E.Attacker.StatMod("Agility");
        if (agi > E.StatBonus) E.StatBonus = agi;
    }
    return base.HandleEvent(E);
}
```

**One tiny class per tree, never one shared class.** `SkillFactory.PowersByClass` keeps only the
first entry for any `Class`, which is exactly how #11 broke Akimbo — the mod reused
`Class="Pistol_Akimbo"` across two trees and vanilla's entry was served in place of the mod's.

**Adding a power to a vanilla tree is additive and verified**, not inferred:
`SkillFactory.HandlePowerNode` looks the name up in the existing skill's `Powers` and calls
`NewSkill.Add(value)` when it is absent, so an unknown power name appends rather than replacing
anything.

### 3.10 Two consequences to carry forward

**The Axe and Cudgel Agility families lose their reason to exist.** With finesse confined to blades,
the vinereaper, halberd, war hammer and greathammer lines become near-duplicates of the battle axe,
greataxe, mace and maceth lines. Across all 33 pairs, **damage, penetration bonus and cap are already
identical** — 9 pairs match on every field, and the other 24 differ only by one pound of weight (plus
the two `Cudgel8`/`Cudgel8th` entries that sit at 1200 against the curve's 1280).

That one pound is consistent, and it used to be the *second* signal rather than the only one: the
Agility twin is a pound lighter in Axe 1H, Cudgel 1H and Cudgel 2H, and a pound heavier in Axe 2H.

Vanilla does ship flavour duplicates — `Steel Dagger`, `Steel Kukri`, `Steel Utility Knife`,
`Steel Butcher Knife` and `Steel Potter's Knife` are all `1d4` / cap 3 / 1 lb / 20 water. So this is
idiomatic rather than wrong. But vanilla's are five names for one weapon, not two parallel nine-tier
families with a systematic offset that used to mean something, and that difference deserves a
decision rather than a shrug.

**The Axe and Cudgel skill regating becomes vestigial.** Twelve powers were regated to
`Strength|Agility`, and it is the one change Mura documented. With Axe and Cudgel weapons
Strength-only, an Agility character can now take Cleave and Dismember and has nothing to swing them
with. The relaxation is inert rather than harmful, and it is documented intent — but charter rule 2
does not like inert, so it wants a sentence either way.

Both are tracked in [#342](https://github.com/vixygrey/qud-expanded-community-edition/issues/342).

## 4. Question two — are the weight cuts a feature or a defect?

**Settled: the method is a feature and belongs in `docs/STYLEGUIDE.md` §3.2; body armour and the
short blades are defects against it. The factors' magnitudes wait on
[#176](https://github.com/vixygrey/qud-expanded-community-edition/issues/176).**
Tracked in [#320](https://github.com/vixygrey/qud-expanded-community-edition/issues/320).

### 4.1 Weight has exactly one consequence

`GetMaxCarriedWeight()` returns `Stat("Strength") × RuleSettings.MAXIMUM_CARRIED_WEIGHT_PER_STRENGTH`,
and that constant is **15**. `Overburdened` is binary — it blocks `IsMobile` and
`CanChangeMovementModeEvent`, with no gradient. Equipped and carried both count toward the total.

Nothing else in the game reads weight. So it is a pure budget against Strength with a cliff at the
line, which is what makes the question answerable: the only thing a weight number does is decide how
much of that budget an item spends.

### 4.2 The compression is a real method, applied to most of the mod

Testing each slot against a single per-slot factor:

| slot | factor | mean deviation | items >2 lb off |
|---|---:|---:|---|
| Melee-1H *(excluding short blades)* | ×0.67 | **0.5 lb** | **0 / 31** |
| Melee-2H | ×0.62 | **0.6 lb** | **0 / 23** |
| Hands | ×0.47 | **1.0 lb** | **0 / 7** |
| Head | ×0.59 | 1.5 lb | 1 / 6 |
| Shield | ×0.51 | 1.9 lb | 1 / 7 |
| Feet | ×0.39 | 2.1 lb | 2 / 7 |
| **Body** | ×0.36 | **6.5 lb** | **6 / 8** |

**61 items follow a clean constant-factor compression of vanilla's own curve.** That is derived work
whether or not it was ever written down, and it is the same finding #248 reached about greathammers —
vanilla's own curve, compressed and carried across. It is not noise, and "restore vanilla" would be
throwing away a consistent pre-fork design choice.

### 4.3 Where it was not applied

**Body armour**, which is the one slot where it matters most. Six of eight sit more than 2 lb off the
slot's own factor, and the spread collapsed from vanilla's 4.6× to 2.4× because the heaviest item was
cut hardest.

| | vanilla | % of a Str-16 budget | mod today | at the slot's own ×0.36 |
|---|---:|---:|---:|---:|
| Fullerite Plate Mail | 160 lb | **67%** | 36 lb (15%) | 58 lb (24%) |
| full best-in-slot loadout | 99 lb | 41% | 50 lb | 21% |

Even vanilla's whole loadout is only 41% of a Strength-16 budget, so **worn gear was never the
binding constraint — single heavy items were.** Fullerite Plate Mail at two-thirds of a character's
entire carry budget is vanilla's one real weight decision, and 36 lb deletes it.

**Short blades**, which are not a compression at all. Five got *heavier*, and the resulting line is
non-monotonic: T3 2, T4 2, T5 3, T6 1, T7 1, T8 1. Vibro is inconsistent with itself — Blade 2→4 up,
Dagger 5→1 down. And the zetachrome set is treated three different ways: Apex ×0.88, Gloves and Pumps
×0.50, Lune ×0.43.

### 4.4 Settled

**The rule is a constant factor per slot**, written into `docs/STYLEGUIDE.md` §3.2 beside the value
curve, with every weight derived as `round(vanilla × factor)`. That ratifies what Mura already did in
61 of 109 items, makes the remainder derivable rather than remembered, and restores body armour's
lever without returning to vanilla's numbers.

**Scrap and the two foods take the slot factor too**, floored at 1. Nothing that exists weighs
nothing — weightless scrap means uncapped bit hauling, and #331 already makes Tinkering cheaper to
reach.

**The magnitudes wait on #176.** A gradient and a cliff want different numbers: under a cliff a heavy
item is free until it is catastrophic, so only the extremes matter; under a gradient every pound bites
continuously, and the same weights would bite considerably harder. Setting the factors before that is
decided means setting them against a penalty curve that is about to change.

### 4.5 What is not blocked

The dependency is narrower than it looks, and worth stating precisely so the sequence does not stall.

**#340 covers six curves and only one of them is weight.** AV/DV per slot, damage per tier per family,
the chip budget, the table-share ceiling and the `Stat` rule all proceed. In #337 the same applies:
`armor-curve`, `damage-parity`, `table-share` and `stat-discipline` are unaffected, and only
`weight-curve` waits.

**And every slot factor is below 1**, so any weight the mod *increased* contradicts the rule whatever
the final magnitudes turn out to be. Those seven are fixable now:

| item | vanilla | mod |
|---|---:|---:|
| `Dagger3` | 1 | 2 |
| `Dagger4` | 1 | 2 |
| `Dagger5` | 2 | 3 |
| `Obsidian Kris` | 1 | 2 |
| `ArmDagger4` | 1 | 2 |
| `Vibro Blade` | 2 | 4 |
| `CrysteelHandBones` | 9 | 10 |

## 5. Question three — what is a chip worth?

**Open. The catalogue is now fully costed (§5.5) and three structural findings are settled facts;
what the budget should *be* is still undecided.**
Tracked in [#338](https://github.com/vixygrey/qud-expanded-community-edition/issues/338).

### 5.1 The ladder split — settled, leave it alone

`docs/2.2-changelog.txt` justifies the 3/6/10 physical ladder as compensation:

> unlike mental mutations which scale with Ego even when obtained via a chip, physical mutations do
> not scale at all. To compensate for this, psionic chips that give physical mutations now give
> 3/6/10 levels

**The premise is true, the compensation is Mura's only decision in it, and the decision is to leave
both ladders as they are.**

> ⚠️ This section was wrong twice before reaching that, and the corrections are worth keeping
> because the shape repeats. First I reported the premise as false, having grepped each mutation
> *class* for `Stat("Ego")` and found seven of twenty-three — the scaling is not in the classes.
> Then I described the result as uncapped, which `GetMutationCap` contradicts. Both are instances of
> `docs/LESSONS.md`'s *"Search where the effect is applied, not where the part is used"*, and the
> second instance there records why a partial match is more dangerous than no match.

**The gradient is vanilla's, not this mod's.** `BaseMutation.CalcLevel` adds the governing stat's
modifier, `MutationEntry.GetStat()` falls through to the category, and `Mutations.xml` declares it
once:

```xml
<category Name="Mental"   … Stat="Ego" … >   <!-- all 23 mental mutations -->
<category Name="Physical" …            >     <!-- no Stat attribute at all -->
```

Every mental mutation in Caves of Qud scales with Ego, chip-granted or inherent. Nothing here was
chosen by the mod, so there is no mod decision to reverse — only the size of the compensation to
judge.

**It reaches chips through the tracker.** `ModImprovedMutationBase` calls
`AddMutationMod(typeof(T), null, Tier, SourceType.Equipment, …)`, which creates the mutation at level
**0** and records the grade as a tracker. `CalcLevel` then sums the stat modifier and every matching
tracker, and clamps the total to `GetMutationCapForLevel(level)`, which is `level / 2 + 1`.

    effective rank = min( chip grade + EgoMod , character level / 2 + 1 )

**Where the compensation lands.** Ego is not static: `Leveler.AddAttributeBonus` adds **+1 to every
attribute** at levels 6, 12, 18, 24, 30 and 36, so Ego climbs whether the player invests in it or
not. Vanilla's chargen maximum of 24 applies to every genotype, so it is a starting line rather than
a ceiling.

Mental rank minus physical rank, at the perfected grade:

| char level | caster, all points to Ego | maxed at chargen, ignored after | Guardian, Ego 16 |
|---:|---:|---:|---:|
| 6–12 | +0 | +0 | +0 |
| 18 | +0 | +0 | **−3** |
| 24 | **+3** | **+2** | −2 |
| 30 | **+5** | **+2** | −2 |

**The compensation is exact precisely where it does not matter and drifts where it does.** Below
character level 18 the rank cap flattens everything to equality regardless of Ego. Above it the two
ladders come apart in both directions at once.

**Settled: leave both ladders alone.** The gradient is vanilla behaviour reaching chips rather than
a mod choice, the divergence is two to five ranks and only past level 18, and it is the one thing
distinguishing a caster Adept's chips from a Guardian's. Suppressing it would mean overriding a
mechanic that applies to every mental mutation in the game, which is a larger intervention than
anything else in this sweep.

Two things follow rather than being closed by it:

- **The +2 column is drift, not reward.** A character who maxed Ego at chargen and never thought
  about it again gains two ranks from `AttributeBonus` alone. The caster's +5 is an investment
  reward; the +2 beneath it rewards nothing. Accepted as the price of not overriding vanilla.
- **The Guardian column is the finding worth carrying.** Low-Ego builds sit two to three ranks behind
  from level 18 on, and Guardians are the half of the genotype that uses *physical* chips — which are
  flat at rank 10 forever per §5.8. The plateau lands hardest on the subtypes with no way out of it,
  and [#350](https://github.com/vixygrey/qud-expanded-community-edition/issues/350)'s duplicate
  stacking is currently their only escape.

### 5.2 The ladder is keyed on the wrong property, and inverted

What decides whether a level is worth much is not the category. It is whether a cooldown caps the
effect.

| mutation | grants at perfected | duration | cooldown | uptime |
|---|---|---:|---:|---:|
| `HeightenedSpeed` | +33 Quickness | — | — | **100%** |
| `PhotosyntheticSkin` | +33 Quickness, +120% healing | 3,600 | per bask | **100%** |
| `Regeneration` | 100%/round limb regrow | — | — | **100%** |
| `ForceBubble` | invulnerability | 28 | 100 | 28% |
| `TemporalFugue` | 3 duplicates | 26 | 120 | 22% |
| `Phasing` | phase out | 16 | 73 | 22% |
| `AdrenalControl2` | +19 Quickness | 20 | 200 | 10% |

The five permanent passives get the **largest** levels, precisely because they are the ones that do
not scale off a stat — but not scaling off a stat is exactly what makes level the only dial, and a
permanent passive is where a level is worth most. `AdrenalControl2` grants Quickness like
`HeightenedSpeed` does, at a tenth of the uptime, and gets the same ladder.

**Settled: this is a real inversion and the mod is not going to fix it by changing ranks.** Two
principles collide here — the compensation logic from §5.1 says physical mutations get more ranks
because they cannot gain any from Ego, and the uptime logic says permanent passives are worth more
per rank. For the five physical permanent passives both apply at once and they point opposite ways.

What breaks the tie is the same argument that settled §5.1:

> **Every one of these is a vanilla mutation, balanced by Freehold.** A mutant with `Regeneration`
> at rank 10 gets exactly what a chip user does. If the Ego gradient is vanilla's call rather than
> the mod's, then so is what a rank of `Regeneration` is worth — and re-tuning it through the chip
> ladder would be second-guessing Qud's own mutation design by proxy.

Which gives §5 a principle it had been missing, and one that should go into
`docs/STYLEGUIDE.md` §3.2 with the budget:

> **The chip system controls access and price. Vanilla controls what a mutation is worth.**

So no `Tier` value changes on account of uptime, and **§5.3's question widens from the Quickness
pair to all seven permanent passives** — price and rarity become the whole answer rather than one
dial of three.

### 5.3 Price and rarity — settled

`GetSpeedBonus(Level)` is `13 + 2 × Level`, shared by `HeightenedSpeed` and `PhotosyntheticSkin`, so
**level 1 is +15** — already above The Kesil Face's +10 at 10,000 water, and above The Shemesh Face's
+10 at 8,000. No ladder reaches below that floor, which is why §5.2's decision left this as the whole
remaining question rather than one dial of three.

**Price cannot gate a chip.** They live in `Artifact 3`–`8`, consumed only by
`ChestBuilders.BuildSpecialChestInventory` at `1d2+1` items per special chest. Village tinkers stock
`Artifact NR`, which carries none. So price sets what an unwanted chip *sells* for and nothing else;
rarity is the access dial. Both are the mod's business under §5.2's rule, but they do different jobs.

#### Settled: a stated chip curve at a quarter of the item curve

`chip value = 1.25 × 2^tier`, written into `docs/STYLEGUIDE.md` §3.2 with its reason, in the style of
`CURVE_EXEMPT`'s vibro entry — **chips are not equipment, their slot competes with nothing, and they
cannot be bought.**

| tier | kind | count | now | item curve | chip curve |
|---:|---|---:|---:|---:|---:|
| 4 | chip | 36 | 20 | 80 | **20** — already on it |
| 6 | chipset | 12 | 20 | 320 | **80** |
| 6 | chip | 36 | 40 | 320 | **80** |
| 7 | chipset | 12 | 40 | 640 | **160** |
| 8 | chip | 36 | 60 | 1280 | **320** |
| 8 | chipset | 12 | 60 | 1280 | **320** |

108 of the 144 change; the basic single chips are already correct.
[#354](https://github.com/vixygrey/qud-expanded-community-edition/issues/354) checks against this
curve rather than the item one.

#### Settled: the four steep permanent passives become jackpots

`HeightenedSpeed`, `PhotosyntheticSkin`, `Regeneration` and `ElectricalGeneration` drop from weight 3
to weight 1 in all three `Raven_Chips Tier N` tables — the same weight as a chipset. The three utility
passives keep weight 3.

| | per artifact roll | 50% chance after |
|---|---:|---:|
| a steep chip, now | 0.227% | 305 rolls |
| a steep chip, at weight 1 | **0.081%** | **854 rolls** |
| an ordinary single chip | 0.227% → 0.244% | — |

The table total falls 120 → 112, so every other chip gets marginally commoner, which is the intended
trade rather than a side-effect.

#### Settled: the Quickness pair stays in the catalogue

Removal was the only dial reaching below the +15 floor, and it is not taken. Under §5.2's rule the mod
controls access and price rather than what a mutation is worth, and **a Mutated Human can take
`Heightened Quickness` at chargen for 4 of their 16 mutation points**. The chip is the non-mutant's
route to the same thing, and pricing that route is exactly what is in scope. The floor of +15 is
accepted as a consequence of the mutation's own vanilla design.

What that leaves is a perfected Heightened Quickness chip at **320 water, 0.081% per artifact roll** —
against 60 water and 0.227% today.

### 5.4 Six chips whose grades grant nothing — filed separately

`Kindle` and `FrostWebs` both override `CanLevel()` to return `false` and never read their level.
Kindle's `GetCooldown(int Level)` returns a literal `50` and `GetRange(int Level)` a literal `12`;
FrostWebs' `CollectStats` sets range 12 and area 3×3 as constants.

So all three Kindle chips are the same item, as are all three Frost Webs chips, and the Fire and Ice
chipsets each carry a dead third. That is wrong under any budget, so it is
[#347](https://github.com/vixygrey/qud-expanded-community-edition/issues/347) rather than part of
this question.

### 5.5 The complete costing

All 36 at each grade. **permanent** means every level applies on every turn; **gated** means a
cooldown caps it; **INERT** means the level is not read at all.

| mutation | family | shipped | kind | scales off | basic | upgraded | perfected |
|---|---|---|---|---|---|---|---|
| `HeightenedSpeed` | Neutral Body | physical | permanent | — | +19 Qk | +25 Qk | +33 Qk |
| `PhotosyntheticSkin` | Light | physical | permanent | — | +19 Qk, +50% | +25 Qk, +80% | +33 Qk, +120% |
| `Regeneration` | Blood | physical | permanent | — | 30% / 40% | 60% / 70% | 100% / 110% |
| `ElectricalGeneration` | Lightning | physical | permanent | Willpower | 8k, 300/t | 14k, 600/t | 22k, 1000/t |
| `HeightenedHearing` | Neutral Body | physical | permanent | — | 9 | 15 | 23 |
| `Clairvoyance` | Neutral Spirit | mental | permanent | — | 5 | 7 | 9 |
| `Psychometry` | Neutral Spirit | mental | permanent | — | 3 / 1.5 | 5 / 3 | 7 / 4.5 |
| `AdrenalControl2` | Blood | physical | gated 10% | — | +12 Qk | +15 Qk | +19 Qk |
| `Phasing` | Lightning | physical | gated ~20% | — | 9t / 94cd | 12t / 85cd | 16t / 73cd |
| `ElectromagneticPulse` | Lightning | physical | gated | — | r2 | r5 | r9 |
| `CorrosiveGasGeneration` | Acid | physical | gated | — | 5 | 8 | 12 |
| `FreezingRay` | Ice | physical | gated | — | -3d4 | -6d4 | -10d4 |
| `FlamingRay` | Fire | physical | gated | — | 385° | 460° | 560° |
| `AcidSlimeGlands` | Acid | physical | gated | — | — | — | — |
| `Cryokinesis` | Ice | mental | gated | — | ~8 | ~16 | ~24 |
| `Pyrokinesis` | Fire | mental | gated | — | ~8 | ~16 | ~24 |
| `TemporalFugue` | Temporal | mental | gated 22% | — | 1 copy | 2 copies | 3 copies |
| `ForceBubble` | Force | mental | gated 28% | — | 20t | 24t | 28t |
| `ForceWall` | Neutral Mind | mental | gated 26% | — | 18t | 22t | 26t |
| `LifeDrain` | Blood | mental | gated 10% | — | 12t | 16t | 20t |
| `Domination` | Mental | mental | gated | Ego | — | — | — |
| `SunderMind` | Mental | mental | gated | Ego, Wil | — | — | — |
| `MassMind` | Mental | mental | gated | Willpower | — | — | — |
| `Confusion` | Acid | mental | gated | Ego | — | — | — |
| `Disintegration` | Force | mental | gated | — | — | — | — |
| `StunningForce` | Force | mental | gated | — | — | — | — |
| `MentalMirror` | Neutral Mind | mental | gated | Willpower | +3 MA | +6 MA | +9 MA |
| `LightManipulation` | Light | mental | gated | Willpower | +2 / 12% | +4 / 20% | +6.5 / 28% |
| `Teleportation` | Light | mental | gated | — | r3 | r5 | r7 |
| `TeleportOther` | Neutral Mind | mental | gated | — | — | — | — |
| `SpacetimeVortex` | Temporal | mental | gated | — | — | — | — |
| `TimeDilation` | Temporal | mental | gated | — | — | — | — |
| `Precognition` | Neutral Spirit | mental | gated | — | 20t | 28t | 36t |
| `WillForce` | Neutral Body | mental | gated | Ego, Tou | 20-24t | 24-28t | 28-32t |
| `Kindle` | Fire | mental | **INERT** | — | range 12 | range 12 | range 12 |
| `FrostWebs` | Ice | physical | **INERT** | — | 3x3 | 3x3 | 3x3 |

### 5.6 The three dials

| dial | outcome |
|---|---|
| **Level** | **not used** — §5.2. Vanilla decides what a rank is worth. |
| **Price** | **used** — §5.3. A stated chip curve at a quarter of the item curve; 108 of 144 reprice. Sets sale value only, since chips cannot be bought. |
| **Supply** | **used** — §5.3. The four steep permanent passives drop to weight 1. Slots were settled separately: the mutant's goes (#353), True Kin keep 2, the Adept keeps 4. |

None of them reaches the starting chipset every Guardian holds, which is why that is its own decision.

### 5.7 The four decisions — all settled

All four are answered; each row links to the section carrying its reasoning. What remains is
implementation, and a stated budget in `docs/STYLEGUIDE.md` §3.2, which is
[#340](https://github.com/vixygrey/qud-expanded-community-edition/issues/340)'s job.

Originally four, and two of them turned out cheap. Everything else this question started with has either been answered
or split out — §5.1 (the ladder rationale is sound), §5.8 (the curve shape is coherent),
[#347](https://github.com/vixygrey/qud-expanded-community-edition/issues/347) (inert grades),
[#350](https://github.com/vixygrey/qud-expanded-community-edition/issues/350) (duplicate stacking),
[#353](https://github.com/vixygrey/qud-expanded-community-edition/issues/353) (the mutant's slot) and
[#354](https://github.com/vixygrey/qud-expanded-community-edition/issues/354) (the value curve).

1. ~~**Is the Ego gradient intended?**~~ **Settled — leave both ladders alone.** The gradient is
   vanilla's own mechanic reaching chips rather than a mod decision, and suppressing it would mean
   overriding behaviour that applies to every mental mutation in the game. See §5.1 for the reasoning
   and for the two things it leaves open rather than closes.
2. ~~**Which of the steep permanent passives get a cap?**~~ **Settled — none.** The uptime inversion
   is real, but every mutation involved is a vanilla one, and re-tuning what a rank of it is worth
   through the chip ladder second-guesses Freehold by proxy. §5.2 records the reasoning and the
   principle it establishes: **the chip system controls access and price; vanilla controls what a
   mutation is worth.**
3. ~~**Price and rarity for the seven permanent passives.**~~ **Settled — see §5.3.** A stated chip
   curve at a quarter of the item curve (108 of 144 chips reprice), the four steep permanent passives
   drop to weight 1 in their tier tables, and the Quickness pair stays in the catalogue.
4. ~~**Do the Guardians keep starting with a chipset?**~~ **Settled — see §5.9.** A subtype starts
   with its own affinity, whatever that contains, and not with a generic chipset carrying someone
   else's steep passive. Nine edits, all replacing the same blueprint.

**What closing this question requires** is a stated budget in `docs/STYLEGUIDE.md` §3.2, and writing
it there is [#340](https://github.com/vixygrey/qud-expanded-community-edition/issues/340)'s job. So
#338 closes when these four are decided; no code depends on it.

### 5.9 Starting chips — settled

**All eighteen subtypes start with three chips granting five mutations**, not just the Guardians as
§5.7 originally had it. Guardians take their affinity's single chip, the Neutral Body chipset and a
Mental Mirror chip; casters take their affinity chipset, a Mental Mirror chip and a Clairvoyance chip.

That collides with §5.3. The four steep permanent passives were just made three times rarer to find,
and starting gear hands one to **12 of the 18**:

| subtype | steep passive | via |
|---|---|---|
| all nine Guardians | `HeightenedSpeed` | Neutral Body chipset |
| Light Guardian | *also* `PhotosyntheticSkin` | its own affinity chip |
| Light Psionic | `PhotosyntheticSkin` | Light chipset |
| Blood Psionic | `Regeneration` | Blood chipset |
| Lightning Psionic | `ElectricalGeneration` | Lightning chipset |

For scale: **vanilla hands out zero cybernetic implants in starting gear**, across every caste and
calling. The mod's equivalent gives every Adept five mutations at character creation.

#### The rule

> **A subtype starts with its own affinity, whatever that affinity contains. It does not start with a
> *generic* chipset carrying someone else's steep passive.**

That line separates the thematic cases from the accidental one. A Light Psionic beginning with
`PhotosyntheticSkin` is its affinity expressing itself and stays; the Light Guardian's own affinity
chip likewise. What goes is the **Neutral Body chipset in all nine Guardian kits** — generic, shared,
and the only reason every martial subtype opens at +15 Quickness.

#### The replacement

`Raven_Simple Neutral Mind Chipset` — `MentalMirror(1)`, `TeleportOther(1)`, `ForceWall(1)`. No steep
passive, and reflect-block-displace is closer to what a Guardian is than Quickness and hearing were.

It duplicates the Mental Mirror chip already in the kit, and duplicates stack
([#350](https://github.com/vixygrey/qud-expanded-community-edition/issues/350)), which should not be
baked into starting gear. So that separate chip becomes a **Neutral Spirit single chip** —
`Raven_Simple Precognition Chip` is the thematic pick. Still three chips, still five mutations, no
duplicate and no steep passive.

`Raven_Simple Neutral Spirit Chipset` is the alternative if the caster flavour is acceptable: it
needs no second edit, because nothing in it duplicates anything the Guardians already carry.

#### Worth confirming in game

The **Light Guardian** starts with `PhotosyntheticSkin` *and* `HeightenedSpeed` — two independent
Quickness sources, one a stat shift and one a metabolizing effect. On the code they look like they
stack, which would open at +30 rather than +15. Removing the Neutral Body chipset resolves it either
way, but the stacking question is worth an in-game check because it bears on
[#350](https://github.com/vixygrey/qud-expanded-community-edition/issues/350) too.

### 5.8 Genotype power curves — the cap shapes everything

Effective rank is `min(sum of every source, GetMutationCapForLevel(level))`, and that second term is
`level / 2 + 1`. **It applies to every genotype identically**, which turns out to be the most
important fact about the chip system.

The other half of the economy: `1 MP = 1 rank` — `GameObject` spends a point and calls
`LevelMutation(m, m.BaseLevel + 1)`. A mod Mutated Human has 16 points at chargen and
`BaseMPGain="1-2"` thereafter, plus Rapid Advancement's +3 to one *physical* mutation at levels 5,
15, 25 and 35. True Kin and Psionic Adepts get none of that: `Leveler` awards mutation points only
`if (ParentObject.IsMutant())`.

| char level | rank cap | mutant, 4 mutations — typical / best | Adept, 4 chips | True Kin, 2 chips |
|---:|---:|---:|---:|---:|
| 5 | 3 | 2.5 / 3.0 | 3 | 3 |
| 10 | 6 | 4.4 / 6.0 | 6 | 6 |
| **18** | **10** | 7.4 / 10.0 | **10** | **10** |
| 25 | 13 | 10.0 / 13.0 | 10 | 10 |
| 30 | 16 | 11.9 / **16.0** | 10 | 10 |
| 35 | 18 | 13.8 / **18.0** | 10 | 10 |

Three phases, and the shape is not the one the audit assumed:

- **Below level 18 the cap binds everyone equally.** A perfected chip and a mutant's grown mutation
  are the *same rank*, because both clamp to `level/2+1`. The Adept's advantage in this window is
  **count, not rank** — four mutations against a mutant's four, but acquired from chests rather than
  paid for at chargen.
- **Level 18 is the Adept's peak.** The cap reaches 10, which is exactly the perfected chip's grade,
  so a perfected chip finally shows its full value at the same moment the mutant is still behind.
- **Above level 18 the Adept plateaus and the mutant keeps climbing.** Rank 10 is the ceiling of a
  single chip; mutation-point income has no ceiling below the cap. By level 30 a mutant's best
  mutation outranks any single chip by six.

**Unless duplicates are stacked**, which is [#350](https://github.com/vixygrey/qud-expanded-community-edition/issues/350).
Trackers sum before the cap, so two perfected chips of one mutation are tracker 20 and track the cap
indefinitely — at half the mutation count.

| char level | 4 distinct chips | 2 mutations, 2 chips each |
|---:|---:|---:|
| 24 | 4 at rank 10 | 2 at rank **13** |
| 30 | 4 at rank 10 | 2 at rank **16** |
| 36 | 4 at rank 10 | 2 at rank **19** |

**What this means for the genotype's niche.** The Psionic Adept is front-loaded breadth that
plateaus, with an undocumented depth mode. It is strongest relative to the others around level 18 and
weakest at level 30+, which is the opposite shape to a mutant — and a coherent design, if an
unstated one. Its ledger is a real trade rather than a free lunch: the **fewest stat points in the
game** at 34 against 38 and 44, **half the mod True Kin's cybernetics licence** at 2 against 4, the
lowest HP gain, and no mutation points — bought with +10 SP per level, two extra chip slots, and
three extra starting skills.

Two corrections to earlier sections follow from the cap, both recorded where they were wrong:

- **§5.1** claimed Ego scaling was uncapped. It is not.
- **[#316](https://github.com/vixygrey/qud-expanded-community-edition/issues/316)'s figures need a
  character level attached.** +33 Quickness needs level 18. A Guardian's starting chipset is +15 at
  level 1, not the +17 that issue states, because the cap is 1 there. The finding survives — a
  20-water chip is +19 from level 4 against an *uncapped* 10,000-water legendary at +10 — but every
  number in it wants "at level N" beside it.

**One thing the cap does not touch.** `Armor.SpeedBonus` is not a mutation, so the Kesil Face's +10
is uncapped and available the moment it is worn. The chips beat it anyway from character level 1,
where the floor of `13 + 2 × Level` is +15.

## 6. Question four — fix in place, or gate behind an option?

**Settled: fix in place, and add no new options.** Tracked in
[#339](https://github.com/vixygrey/qud-expanded-community-edition/issues/339), which this closes, and
it answers [#336](https://github.com/vixygrey/qud-expanded-community-edition/issues/336) as well.

### 6.1 An item-stats option is not really available

Every one of the eleven shipped options works by mutating a **small loaded record** —
`GenotypeEntry` fields, `PowerEntry.Minimum`, an `Anatomy`, `PopulationManager.Populations`. Item
stats are not that shape.

To offer "restore vanilla item stats" the mod would have to carry **183 blueprints and 386
individual values**, and it **cannot read them back**: once Qud merges the mod's XML the in-memory
blueprint holds the mod's value, and vanilla's exists only in the game's own files on disk — which
charter rule 5 bans reaching, in as many words:

> **Never — these do not move:** file I/O outside the mod's own directory

So the option means 386 hardcoded numbers in C#, duplicating a dataset that already exists, drifting
from it on every Qud patch, with nothing able to check the drift — `tools/check_vanilla_drift.py`
reads the game's files, and the mod cannot. That is a maintenance liability rather than a feature,
and it would be the largest C# addition the mod has ever made, against a rule that prefers XML.

### 6.2 What is gateable mostly already has an option

| finding | shape | gateable |
|---|---|---|
| weights, AV, Agility, cudgel damage, cybernetics, chip prices | blueprint values | **no** — §6.1 |
| table weights (#325, #326, #327) | `PopulationManager` | yes, and `OptionQudExpandedCEChipDrops` is already this shape |
| subtype grants (#330, #332) | `GenotypeEntry` | yes |
| the Tinkering gate (#331) | `PowerEntry` | **already gated** |
| the mutant's chip slot (#353) | `Anatomies` | **already gated** |

### 6.3 And the charter points the same way

Rule 6's exception is *"a change that **grants** power with no content attached"* — written for
opinions the mod adds. Every fix in this sweep **removes** power and moves toward vanilla, which is
the baseline a player already accepted by installing Caves of Qud. And the charter says of the six
rules that where existing content violates one, *"that's debt to pay down, not precedent."*

The circular catch this question was filed with is also gone. Questions one to three produced stated
conventions, and [#340](https://github.com/vixygrey/qud-expanded-community-edition/issues/340) writes
them into `docs/STYLEGUIDE.md` §3.2 — so most of the sweep becomes a **defect fix** under rule 2's
lower bar rather than a design change needing its higher one.

### 6.4 What this obliges instead

No option means the changelog carries the whole burden of telling players. Charter rule 2 puts
causality in the player-facing changelog precisely for this, and these are the largest player-visible
numbers the fork has moved. Two things follow:

- **Every fix states its before and after**, not just its reason. A player who liked a number should
  be able to find out what it became.
- **The sweep lands across a version boundary players can see**, rather than trickling into patch
  releases. `docs/RELEASING.md` already treats a release as two publications; this wants to be one of
  them, announced.

## 7. The findings

All twenty are filed and indexed under
[#315](https://github.com/vixygrey/qud-expanded-community-edition/issues/315), which carries the
severity ranking, the sequence, and the links. It is the live list; this document is the reasoning.

The sequence, in short:

**All four questions are settled**, so what is left is implementation:

The work splits in two, and the halves are not the same size. Four of the conventions were
*decided* by the questions above and cost a paragraph each; the rest have to be **derived** from
vanilla's own values before they can be written at all. Bundling them delayed the cheap half behind
the expensive one.

1. **Write the settled rules** — the `Stat` rule from §3.9, the chip value curve from §5.3, and the
   two principles the questions produced: *the chip system controls access and price, vanilla
   controls what a mutation is worth* (§5.2), and *a subtype starts with its own affinity, not a
   generic chipset carrying someone else's steep passive* (§5.9). **Done** — they are in
   `docs/STYLEGUIDE.md` §3.2, and they unblock #321, #338 and #354.
2. **Derive the remaining curves** (#340) — AV and DV per slot per tier, weight per slot per tier,
   damage per tier per family, and a ceiling on mod share of a vanilla table. Each needs vanilla's
   own values collated first. Nothing they cover can be called a defect until there is something it
   contradicts, which is what gates #318, #320, #322 and #325.
3. **The four critical findings** (#316, #317, #318, #319).
4. **The validator checks** (#337, #354) — what makes step 3 stick.
5. **The systemic three** (#320, #321, #322). #321 was unblocked by step 1; #320's magnitudes still
   wait on #176.
6. **The rarity pass** (#325, #326, #327).
7. Everything else. No option work — §6 settles that there will be none.

---

## 8. What holds up

An audit that lists only faults misrepresents the thing.

- **The new weapon families.** All 71 new melee blueprints mirror a vanilla twin's damage,
  penetration bonus and cap at the same tier, across nine tiers, without a single exception.
- **The value curve.** Followed everywhere it applies, because `item-curve` checks it. The
  tier→material table likewise. This is the proof that the checked conventions hold and the
  unchecked ones do not.
- **The revived ammunition.** The six arrows, four shells and the scour slug are the best-calibrated
  content in the mod — modest payloads, honest rules text, weight-2 entries at the top tiers. #146's
  decision to cut ten bullets on measurement rather than ship them shows in the result.
- **Psionic gun distribution.** Weight 1 each in `Missile 2` and `Missile 3` against vanilla
  neighbours at 5–15. Whatever their stat line, they are correctly rare.
- **Chip drop rate.** 9.09% per artifact roll, 48 entries per tier table, chipsets at a quarter the
  weight of single chips.
- **Subtype stat budgets.** Net +1 to +3 across all eighteen, against vanilla's +2 for callings and
  +3/+4 for castes. The comment at the top of `mod/Subtypes.xml` states the target and the file
  meets it.

---

## Sources

| What | Where |
|---|---|
| Vanilla data | `StreamingAssets/Base`, read through `tools/check_vanilla_drift.py` |
| Game code | `Assembly-CSharp.dll`, decompiled with `ilspycmd` — see §1 for the type list |
| Mura's stated intent | `docs/mura-feature-notes-wip.txt`, `docs/2.2-changelog.txt` |
| The conventions that held | `docs/STYLEGUIDE.md` §3.2, §3.3 |
| The rules this is judged against | `docs/CHARTER.md` rules 1, 2 and 6 |
