# Craft, Carry & Settle — design doc

**Status:** spec only, no code written
**Target:** Caves of Qud, current build
**Scope:** one loop across seven issues; mostly data, a little C#, no Harmony

> **This document is the worked design behind the arc issue.** That issue is the index and the
> sequencing; this is the reasoning, the measurements and the decisions. Where the two disagree, this
> one is newer and wins.
>
> **Everything below was measured against the installed game**, not recalled. Where a claim rests on
> reading rather than on play, it says so — because the recurring failure in this repository is a
> mechanism read correctly and inferred from wrongly.

---

## 1. The design problem, stated honestly

Three holes, and they are the same hole seen from three sides.

**This fork already charges for carrying things, and gives nothing back.**
[`FEATURES.md`](FEATURES.md) §14 grades encumbrance into four bands, and §55 makes carrying a
fortune draw raiders. Both are costs. Nothing anywhere is a reason to carry something heavy on
purpose, so the optimal play with anything bulky is to leave it where it is.

**Qud has an economy of values and no economy of places.** `TradeUI.GetValue` is the item's own
`ValueEach` multiplied by the player's trade `Performance`, and `Performance` derives from Ego.
There is no zone term, no region term, no faction term and no supply term anywhere in that path. A
gold nugget fetches the same in Joppa as in Kyakukya, so no journey is ever a trade.

**The workshops are furniture.** Nine blueprints read as workstations — Kiln, Lathe, Glass Furnace,
Sewing Machine, Glass Printer, Fluxthing, Electrothing, Gas Burner, Unicomputer — and not one has an
interactive part anywhere in its resolved chain. They are placed by worldgen into rooms built to look
like somewhere things get made.

The loop that closes all three is **gather → refine → carry → sell**, with somewhere to do it from.

### 1.1 The gate this passed, and the one it did not

The arc issue asks whether this is the mod at all. `manifest.json` describes this fork as Psionic
Adepts, psionic chips, complete weapon and armour families, and a home base in Joppa — and a trade
economy is not in that sentence.

**The place half is continuation.** A home base already ships as `mod/Optional/JoppaBuilding/`, and
generalising it is not a new claim on what this mod is.

**The craft-and-trade half is a new claim, and it needs the §10.4 test on its own terms** — *serves a
feature this fork is already building*. Its answer is the first paragraph of this section: two shipped
systems make weight and carried value cost something, and neither has a reward. That is the argument.
If it fails, the arc fails with it.

---

## 2. What the base game already gives us

Measured rather than assumed. Each row is the thing a phase depends on.

| mechanism | what it does | how sure |
|---|---|---|
| `ItemConvertor` | one item in, N out, recipe read from a tag on the input | 3 machines ship: Rock Tumbler, Wire Extruder, Nacham's Loom |
| `ChargeUse="0"` | skips the charge path entirely, so a machine works off-grid | read in `IActivePart`; the whole test is wrapped in `if (activeChargeUse > 0)` |
| Rock Tumbler pricing | 1:1 refinement that creates value at **×1.2**, uniformly across all seven rough-to-polished gem pairs | measured from the blueprints |
| `AdjustValueEvent` | multiplicative adjustment to an item's value, dispatched to the object | 8 vanilla users, `Rusted` among them |
| `GetTradePerformanceEvent` | dispatched to the actor; a handler writes `LinearAdjustment` and `FactorAdjustment` | read; the result is clamped to 0.05–0.95 |
| `Zone.GetRegion()` | resolves a zone to a curated 20-value terrain vocabulary | counted from the `Terrain` tags |
| `Interior` + `Vehicle` | an interior zone attached to an object, declarable in pure XML | Freehold's own modding wiki says so outright |
| `Interior` weight | answers the carried-weight event by adding its contents' weight | read in the part |
| `InteriorRequired` | per-object property that exempts that object's weight | the wiki documents it as what the base game itself does |
| portable beds | three of them, and any one reaches the `Bed` rest tier | `Hammock`, `Bedroll`, `Folding Cot` |
| `Survival_Camp` | places a campfire and registers it as a point of interest | read in the skill |
| bulk consumables | priced in common bits and made in quantity — a lead slug is one common bit for fifty | read from the blueprints |

### 2.1 The constraint that shapes everything

**`ItemConvertor` is strictly one input to N outputs.** There is no way to require several
ingredients, and `Chance` does not help — a failed roll leaves the item and retries, so it is a rate
rather than a consumption.

So no station can ever *combine* materials. Every recipe is a 1:1 step, and a chain is a series of
them. This does not make refinement impossible — the Rock Tumbler is exactly that shape and Freehold
is content with it — but it does mean:

- a chain's total value multiplier is the product of its steps, so a four-step chain at ×1.2 each is
  ×2.07 overall, and that is the number to watch;
- "three fibre and a dye make a robe" is not expressible at all, in any station, ever;
- anything that genuinely needs several inputs has to happen somewhere other than a station.

### 2.2 What we are not competing with

**Tinkering is Qud's system for a player building their own equipment, and it is comprehensive.**
Nearly a thousand blueprints carry a `TinkerItem` part once inheritance is resolved, covering melee
weapons, missile weapons, armour, shields and grenades. Nothing in this arc duplicates it, and
nothing in this arc should ever look like a second way to make a sword.

The corollary is a hard line on bits, in §5.2.

---

## 3. The loop

### 3.1 Gather

Qud's entire raw-material vocabulary is two item categories once `Physics.Category` is resolved
through inheritance: **Trade Goods** — the three nuggets, the one ingot, seven rough gems and their
polished pairs, two ape pelts, and jewellery — and **Scrap**, which is the tinkering bit source.

There is no clay, no sand, no raw glass and no bolt of cloth anywhere in the game. That is why four
of the nine stations have nothing they could possibly convert, and it is why authored materials are
the precondition for most of this arc rather than an enhancement to it.

**Materials should be regional.** A material that grows or is dug somewhere has its scarcity decided
by geography rather than by a multiplier table I invented, which is what makes §3.4 honest. The
20-value terrain vocabulary is the natural key.

### 3.2 Refine

A station is `ItemConvertor` with a `ConversionTag`, and a recipe is a tag on the input naming its
own output. The whole recipe layer is data.

**`ChargeUse="0"` is the only usable setting**, because these machines spawn in ruins workshops and
Red Rock where there is no power grid. A powered station is scenery exactly where a player finds it.
That sounds like it makes conversion free and unbounded; it does not, because the *input* is finite —
cleared zones never repopulate, so ore and materials do not regrow.

**Start with a leaf blueprint.** Five of the nine have no descendants at all: Kiln, Lathe, Glass
Furnace, Glass Printer and Sewing Machine. The other four each have a `Powerless` or `Unpowered`
child that **inherits** from it, and those children strip specific parts with `removepart` — they
cannot know to strip an `ItemConvertor` merged onto their parent, so merging onto one of those four
hands a working converter to the blueprint whose entire identity is that it does not work. With
`ChargeUse="0"` it would work perfectly, because the parts they remove are the ones a zero-charge
part never consults.

### 3.3 Carry

Weight is the cost, and this fork already grades it. The arc adds two ways to move more than a
character can carry:

**A vehicle.** `Vehicle` and `Interior` are both parts named in XML, so a caravan is declarable
without a line of C#. `Interior` answers the carried-weight event by adding its contents' weight, so
a vehicle is *not* free storage by default.

**That default is the design.** The wiki documents three ways to stop interior contents weighing
something, and the choice between two of them is the whole feature:

- **`InteriorRequired`** on each object in the interior map exempts that object. This is what the base
  game itself does, and it makes the vehicle's *structure* free while leaving **cargo heavy**.
- **`IgnoreWeight="true"`** on the `Interior` part exempts everything, and the wiki notes it
  contradicts standard game behaviour.

`InteriorRequired` is the correct one here and it is not a detail. A caravan should be a bigger
container that still costs something to fill, not a way to teleport weight. Chosen the other way,
this arc deletes the constraint it exists to give a reward to.

### 3.4 Sell

Price is event-driven a level above the trade screen, which is what makes regional pricing reachable
at all:

- **`GetTradePerformanceEvent`** is dispatched to the actor, so **one part on the player** — attached
  through the hooks this fork already has, reaching every existing save — can vary the trade rate by
  region. No merges onto any vanilla blueprint. This says *trade is good here*.
- **`AdjustValueEvent`** is dispatched to the object, so per-commodity pricing wants a part on the
  goods. That costs nothing when the goods are our own blueprints. This says *copper is good here*.

The second is the interesting one and the more expensive.

**The faucet is the risk, and it is real.** Merchants restock on a timer, so buy-low-sell-high is a
loop rather than a one-off. A gradient with no brake is an unbounded economy, which this repository
has already had to reason about more than once. Candidate brakes, to be decided rather than assumed:
a cap per merchant, a spread that narrows with use, a cooldown, or a gradient that only ever applies
to goods this fork adds.

---

## 4. The place

### 4.1 A wreck before a working vehicle

An interior zone attached to an object is a building you can walk into; add a `Vehicle` part and it is
a building that moves. Those are genuinely different features and should not be blurred.

**A derelict is the cheap and strong version.** It is static, it needs no answer to world-map travel,
and Qud is a world of ruins — so *"what used to be a vehicle"* explains itself without the game
needing a concept of ownership it does not have.

**A working caravan is the expensive version**, and its risk is specific: `Vehicle` carries `OwnerID`,
`PilotID`, `BindBlueprint` and `IsOwnedBy`, and **nothing in vanilla exercises any of them as
ownership**. The fields are public, XML-declarable and exactly the right shape; they have simply never
been asked. That makes ownership a thing to test early rather than a thing to design around.

### 4.2 What a base is actually for

Storage is already free. Cleared zones never repopulate, so a chest dropped in an emptied lair is as
safe as a vault, and a base justified as somewhere to put things is answering a question the game does
not ask.

What is missing is **services and identity** — somewhere the stations live, that the world
acknowledges, that can be improved. That is also what makes the Joppa building valuable today: not its
chest, but a becoming nook and a cybernetics rack available from turn one.

**Interiors are authored maps, not runtime construction.** Nothing is built at play time; the furniture
is placed in an `.rpm` the way `mod/Optional/JoppaBuilding/Joppa.rpm` already is. That answers the one
unknown the base issue said had the least evidence behind it.

---

## 5. The decisions that come before code

### 5.1 The five gates

Each is recorded on its own issue; they are gathered because they interact and because answering one
of them differently changes what the others are.

1. **Does the arc ship at all** — §1.1.
2. **The bits ceiling** — §5.2.
3. **`InteriorRequired` or `IgnoreWeight`** — §3.3. These produce opposite features.
4. **Wreck or working vehicle** — §4.1.
5. **The trade-good curve exemption** — §5.3.

### 5.2 Bits, and where the line goes

A station could output a scrap item that the player disassembles for bits. This needs no new
mechanism, and at the low end it serves something Freehold already built: bulk consumables are priced
in common bits and made in quantity, with a lead slug costing one common bit for fifty of them.

**The obvious exploit is already shut, twice.** Bulk consumables are `CanDisassemble="false"`, and
independently the disassembly yield is gated on how many the recipe makes, so an item made fifty at a
time returns its bit about one time in fifty-one. There is no build-then-disassemble loop to design
against.

**The line is the high end.** Vanilla rations tiered scrap deliberately, and bits buy the whole
tinkering catalogue. [`STYLEGUIDE.md`](STYLEGUIDE.md) §3.2 already draws this line for mutations — the
chip system controls access and price, and vanilla controls what a mutation is worth. The same
argument holds here: **vanilla controls what a tinkering recipe costs, and minting high-tier bits
would re-price every recipe in the game at once.**

So: the common named scraps and the low digits, never the tiers Freehold withholds.

### 5.3 Pricing, and a curve that does not describe this

New refined goods are trade goods, and vanilla's own trade goods are not on a curve — a copper nugget
against a copper figurine is a very different ratio from the same pair in gold. So an output cannot
simply reuse a vanilla figurine's price; it wants its own blueprint at the Rock Tumbler's ×1.2.

That runs into `item-curve`, which holds every prefixed object to the doubling value curve and exempts
only by part composition. A trade good matches none of the exemptions. **The exemption has to be
declared up front**, the way food was — before the first item is priced, not after one fails CI.

---

## 6. What this deliberately does not do

Recorded so it cannot creep back in.

- **A second equipment-crafting system.** Tinkering owns that, across nearly a thousand blueprints.
- **Weapon-tier materials.** [`STYLEGUIDE.md`](STYLEGUIDE.md) §3.2's ladder runs bronze to zetachrome
  and only bronze exists as a raw item. Authoring eight tiers of ore is a different, larger project.
- **Minting high-tier tinkering bits**, per §5.2.
- **Runtime furniture placement.** Interiors are authored maps.
- **Recipes needing several inputs.** Not expressible in `ItemConvertor` at all, per §2.1.

---

## 7. Build order

**Phase 1 — the pilot, which needs no new materials.** New ingots carrying no wire output, one leaf
station, and the minimum regional price term. This is the whole loop end to end using inputs the game
already has, and it is the cheapest place to find out the arc is wrong.

> **Kill criterion.** If refining metal and carrying it somewhere is not interesting with the
> materials Qud already has, authored materials will not rescue it. Stopping here costs two small
> features that stand alone.

**Phase 2 — the place.** A derelict with an interior and an authored map.

**Phase 3 — materials**, now with three consumers that already exist.

**Phase 4 — the shop and the road.** The outfitter, camp gear, and the full commodity pricing model.

**The ordering rule underneath all of it: a layer must not land before its consumer.** This repository
has already paid for the alternative — a check merged with nothing written against it could not see
the first content that needed it, and was only corrected because content arrived within the hour.

---

## 8. What only play can answer

Listed because every one of these is currently a reading, and readings in this repository have a
consistent failure rate.

- Whether a station-made scrap item disassembles the way a found one does. Nothing in the disassembly
  path looks at provenance, but that is a reading.
- Whether a vehicle can be owned and kept rather than being quest scenery.
- Whether an interior zone and its contents survive a save and a zone freeze.
- Whether `AdjustValueEvent` reaches a merchant's buy price or only the player's sell price.
- Whether the loop is any fun. No amount of this document answers that, and Phase 1 exists to find out
  cheaply.

---

## Sources

Everything here was read from the installed game — the blueprint XML under `StreamingAssets/Base`, the
decompiled assembly, and Freehold's own modding wiki, which is indexed in
[`WIKI.md`](WIKI.md). The fork-side facts come from
[`FEATURES.md`](FEATURES.md) and [`STYLEGUIDE.md`](STYLEGUIDE.md).

The operational traps this document tries not to repeat are in
[`LESSONS.md`](LESSONS.md) — particularly that a mechanism existing is
not a mechanism working, that a declaration is not a consumer, and that a figure quoted in prose has
no test.
