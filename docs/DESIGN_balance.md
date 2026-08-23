# Balance — design doc

**Status:** audit complete. 20 findings filed under [#315](https://github.com/vixygrey/qud-expanded-community-edition/issues/315); four questions open, one partly settled here.
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

**Partly settled. The rule is agreed in shape; three things are still open, at the end of §3.9.**
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

**My recommendation is C + D.** Together they answer the gun objection and keep Mura's actual
documented intent — more skill access for Agility builds — as the thing the mod is *for*. **A** is
the safe fallback if the C# is unwanted.

### 3.9 Left to decide

1. **The rule.** Recommended: match long blades everywhere. A vanilla blueprint keeps Strength; the
   mod's parallel family is the Agility path. One stated exception — a vanilla blueprint may sit on
   the Agility side when it is a low-tier member of a family this mod *completes* as the Agility
   line (`Iron`/`Steel Vinereaper`, `Warhammer2`, `Steel War Hammer`, `Steel War Hammerth`), because
   vanilla ships those families only partially.
2. **Whether the crossover costs a build resource** — design C, and the only thing that answers §3.6.
3. **Short blades**, given §3.7 argues the wristblade should fall further behind rather than catch up.

**Keep regardless:** the `Skills.xml` regating of 12 Axe and Cudgel powers to `Strength|Agility`. It
is required for the theme to function at all — without it an Agility halberd user cannot take
Cleave — and it is the only part Mura documented.

---

## 4. Question two — are the weight cuts a feature or a defect?

**Open.** [#320](https://github.com/vixygrey/qud-expanded-community-edition/issues/320).

109 vanilla items re-weighted; **1,423 lb → 699 lb, a 51% cut**, and the heaviest were cut hardest.
Heavy armour's cost in Qud *is* its weight, so cutting it makes the AV free — which is how this
compounds with the AV ceiling rather than sitting beside it.

#248 asked exactly this question about greathammer weights, settled it as deliberate, and recorded
the rule in `docs/STYLEGUIDE.md` §3.2. That is both the precedent and the template: decide, then
write the curve down. #176 is the other half — burden is a cliff rather than a gradient, so weight
only matters at the moment you cross the line.

---

## 5. Question three — what is a chip worth?

**Open.** [#338](https://github.com/vixygrey/qud-expanded-community-edition/issues/338).

There is no stated budget. The 3/6/10 physical ladder has a documented reason in
`docs/2.2-changelog.txt` — mental mutations keep scaling with Ego when granted by a chip, physical
ones do not — and that reasoning is sound. What it did not account for is that some physical
mutations have steep per-level curves and others do not, so a perfected Heightened Quickness chip is
worth 3.3× a legendary while a perfected Temporal Fugue chip is worth three copies for 24 rounds.

The output should be a budget in `docs/STYLEGUIDE.md` §3.2, so the next chip is derivable rather
than judged.

---

## 6. Question four — fix in place, or gate behind an option?

**Open.** [#339](https://github.com/vixygrey/qud-expanded-community-edition/issues/339).

The shape I think is right: **fix in place** anything that fails a *stated* convention, because
charter rule 2's lower bar covers it — "this contradicts the mod's own stated convention". **Option**
anything that is taste rather than contradiction.

The catch is circular, and it is why the conventions come first: most of these findings do not
currently *have* a convention to contradict, so until §7's first step lands they are design changes
needing rule 2's higher bar rather than defect fixes needing its lower one.

Worth knowing before designing the option: item stats are read at load and baked into each object
when it spawns, so an option here changes what spawns *next*, not what is already in a save.

---

## 7. The findings

All twenty are filed and indexed under
[#315](https://github.com/vixygrey/qud-expanded-community-edition/issues/315), which carries the
severity ranking, the sequence, and the links. It is the live list; this document is the reasoning.

The sequence, in short:

1. **Write the curves** (#340) — AV, weight, damage, chip budget, table share, and when a vanilla
   blueprint may change its `Stat`. Nothing above can be called a defect until there is something it
   contradicts.
2. **The four critical findings** (#316, #317, #318, #319).
3. **The validator checks** (#337) — what makes step 2 stick.
4. **The systemic three** (#320, #321, #322), once their questions are answered.
5. **The rarity pass** (#325, #326, #327).
6. Everything else, plus whatever option #339 settles.

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
