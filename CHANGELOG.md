# Changelog

All notable changes to this fork are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This changelog begins at the fork. Upstream history through 2.2 is Mura's and is preserved
verbatim in [`docs/2.2-changelog.txt`](docs/2.2-changelog.txt) — it is a historical record and is
never edited.

Entries marked **(internal)** do not affect the shipped mod and are invisible to players. They are
recorded because contributors need them, not because subscribers do.

## [Unreleased]

### Added

- **(internal)** `python3 tools/check_docs.py --wiki` verifies that the wiki's links into this
  repository still resolve. The wiki cites `docs/FEATURES.md` and three other files 56 times, and
  GitHub derives an anchor from the heading text — so renaming a heading breaks every link to it
  while a bad fragment still returns HTTP 200 and neither repository says a word. Renaming one
  heading breaks five links across three pages; that is measured, not guessed.

  Outside the normal run, like `--ruleset` and for the same reason: it needs a second repository and
  a network, and a check that passes quietly when it could not reach anything is worse than none.
  It clones the wiki itself, or takes `--wiki-path` for a clone you already have.

  It closes the half of #230 that is silent *and* mechanical. For the other half, `CONTRIBUTING.md`
  now carries the wiki's clone URL and the rule that a change to what a player sees should be
  grepped there, and the pull request template asks for it — conditionally, because most changes
  cannot affect the wiki and a checklist line with a poor hit rate is just noise.

  `docs/LESSONS.md` records the three ways a wiki page goes wrong, and that only two of them look
  like anything.
  ([#230](https://github.com/vixygrey/qud-expanded-community-edition/issues/230))
- **(internal)** `check_docs.py` recomputes `docs/FEATURES.md`'s chip appendix from the blueprints
  rather than trusting it. All 144 rows — item tier, value, and which mutation at which level — are
  data somebody typed out, and typed data drifts.

  It found three stale rows the moment it ran: the acid *chipsets* still named `GasGeneration`
  months after #258 renamed it, and I had corrected the three single-chip rows earlier the same day
  while missing these on the same pass. That is how well re-reading a 144-row table works, and it is
  the whole argument for the check.

  This is the first of the document's tables to be checked rather than believed. Of roughly 713 data
  rows and 583 numbers in that file, 74 claims were verified before this — about one in twenty. The
  armour and weapon tables are the obvious next targets and are a different bargain: 43 of their rows
  are `merge` edits to vanilla blueprints, so recomputing those needs an installed game, where this
  one is mod-only and runs in CI.
  ([#230](https://github.com/vixygrey/qud-expanded-community-edition/issues/230))
- **(internal)** `validate_mod.py` refuses a `ModImprovedMutationBase<T>` naming a mutation the game
  will not grant. Existing as a class and being grantable are different things, and only the second
  matters: `GasGeneration` compiles, and `unknown-part` passes it because `Raven_ModGasGeneration`
  is a genuine part, but nothing declares `<mutation Class="GasGeneration">`, so the game logs
  `Mutation entry not found` and hands out a fallback. Six chips ran at roughly half their intended
  gas duration from Mura's 2.2 until #226, through every gate this repository had, because no gate
  looked *inside* the generic.

  The catalogue is the authority rather than the `XRL.World.Parts.Mutation` namespace — the
  namespace is what made the defect look fine. Its 130 classes join `tools/qud-api.json` (1.9 KB,
  and inside the digest, so a Qud update that renames a mutation reads as a stale snapshot rather
  than as a silent gap), which keeps the check running in CI where no game exists.

  It reports nothing on `main`. Reverting #226's one-word fix makes it fire and name the cause,
  which is the only test of a gate that means anything.
  ([#256](https://github.com/vixygrey/qud-expanded-community-edition/issues/256))
- **(internal)** `tools/report_dynamic_tables.py` says what a `DynamicObjectsTable:` tag actually
  distributes. A tag is a route into merchant stock, creature inventories or a machine socket with
  no weight, no entry and nothing in a diff to review — and it inherits, so the blueprint carrying
  it is usually not the blueprint being distributed. That is why #223 described `BaseArrow` putting
  six arrows in the ammunition pool and missed two psionic bases putting eighteen firearms into
  legendary gunsmith stock, on the same page.

  It separates what this fork declares from what it inherits, because only the first is a decision
  anyone made here: `DynamicObjectsTable:Items` reaches 325 of the fork's 370 new blueprints, and
  that is just how vanilla distributes items. Three tags are ours — `EnergyCells`, `Headwear` and
  `Guns` — and only `Guns` is flagged, because 18 of the 23 it reaches inherit it from a base rather
  than declaring it.

  Running it corrected #262, which said 22 from a hand count. The true reach is 23: the extra is
  `Raven_Compact Flamethrower`, which takes the tag from vanilla's `Flamethrower` rather than from
  anything this fork wrote. A number arrived at by grepping was wrong by one in the direction that
  hides content, which is the argument for the tool in a sentence.
  ([#264](https://github.com/vixygrey/qud-expanded-community-edition/issues/264))
- **(internal)** `docs/LESSONS.md` records a third way a search can find nothing, and
  `AGENTS.md` warns about it in the traps list. `command -v ilspycmd` returns nothing on a machine
  where `ilspycmd` is installed, because the .NET installer writes the literal `~/.dotnet/tools`
  into `/etc/paths.d/dotnet-cli-tools` and `path_helper` never expands the `~`. I filed #226 saying
  the tool was absent and that settling the question needed a play session; it did not, and one
  `export` produced the whole answer. `CONTRIBUTING.md` had explained this since #252 — filed under
  the snapshot check, which is not where I was standing. It goes in beside the two existing examples
  rather than becoming its own lesson, because the shape is identical and a third instance is what
  turns a coincidence into a pattern.
  ([#259](https://github.com/vixygrey/qud-expanded-community-edition/issues/259))
- **(internal)** A `balance` label, for a change that moves a number a player feels. `bug` says a
  value is wrong and `balance` says correcting it changes how the mod plays — #226 is both, and the
  second half is a decision against the curves in `docs/STYLEGUIDE.md` §3.2 rather than something
  that rides along with the fix. #248 was already waiting for the same distinction.
  `CONTRIBUTING.md` documents it beside the other three labels that need explaining.

### Changed

- **(internal)** Blueprint tag resolution honours `*delete`, and `tools/report_dynamic_tables.py`
  stops counting deletions as routes. `*noinherit` confines a tag to the blueprint declaring it;
  `*delete` removes an inherited one outright, and vanilla uses it 126 times — including to take
  `Corpse` out of `DynamicObjectsTable:Items` and `FoldingChair` out of `:Trinkets`. Implementing
  only the first meant the resolver reported blueprints as pool members that the game had explicitly
  removed, and the report named `Corpse` as a route into a table it opts out of.

  No published figure moves: the API snapshot's digest is unchanged, so the census and every cited
  number are unaffected. What was wrong was the reach the report printed, which is what two content
  decisions were about to be made from.

  Those two directives are the complete set. Across every vanilla blueprint, the only tag values
  beginning with `*` are `*noinherit` (951) and `*delete` (126), plus a bare `*` twice that is an
  ordinary wildcard on `PaintWith` and `Species`.
  ([#261](https://github.com/vixygrey/qud-expanded-community-edition/issues/261))
- **(internal)** `docs/STYLEGUIDE.md` §3.3 records how this fork distributes an item, which was the
  open question behind #223. Explicit `PopulationTables.xml` entries are for a chosen weight in a
  named table and every new item should have one; a `DynamicObjectsTable:` tag is an addition on top
  that puts the item in vanilla's specialist pool for its category — the hatter stocking helmets, the
  legendary gunsmith stocking guns.

  #223 argued the tags should all become explicit entries. They cannot: every consumer uses the
  `:Tier{n}` form, and declaring one of those replaces vanilla's fabricated pool rather than joining
  it, so the tag is the only additive route into tier-appropriate distribution. What #223 actually
  wanted — a distribution route that something records — came from `tools/report_dynamic_tables.py`
  instead, at the cost of one tool rather than reworking three families.
  ([#263](https://github.com/vixygrey/qud-expanded-community-edition/issues/263))
- **(internal)** Recorded Qud's mutation rank cap, and undid a wrong claim I had put in
  `docs/FEATURES.md` because of not knowing it. A mutation's effective rank is
  `min(what grants it, level / 2 + 1)` — `BaseMutation.GetMutationCapForLevel` — so a chip granting
  rank 10 shows rank 1 on a level-1 character and reaches 10 at level 18.

  Watching a level-1 character, I concluded chip tier did nothing and warned in Appendix B that its
  144 documented mutation levels were aspirational. They are not: they are what each chip grants,
  and the character level caps what you see of it. The warning is gone and the table says so
  instead. `docs/LESSONS.md` carries the cap, which cost a wrongly-filed issue and two wrong
  changelog entries before anyone looked at the rank breakdown the game was already showing.
  ([#272](https://github.com/vixygrey/qud-expanded-community-edition/issues/272))
- **(internal)** Blueprint tag resolution honours `*noinherit`, and lives in one place. A tag
  declared `Value="*noinherit"` applies to the blueprint declaring it and not to anything
  inheriting from it — the rule that lets `Raven_Base Psionic Pistol` mark itself a base without
  making its nine descendants bases. `snapshot_qud_api.py` matched on tag name alone, which
  inverts the answer for every descendant, and inverts it to *nothing found*: resolving dynamic-
  encounter eligibility over the mod's psionic firearms returns 0 of 20 without the rule and 18
  of 20 with it.

  **No figure moved.** The helper was only ever called with `Creature`, `Humanoid` and
  `NaturalGear`, and I checked all 13,105 vanilla objects — none of those three is ever declared
  `*noinherit`. Only six tag names are, `ExcludeFromDynamicEncounters` and `BaseObject` the
  common ones. So the census was right by coincidence rather than by construction, which is a
  poor thing for a general-looking helper to be. The snapshot's digest is unchanged, and since
  the 28 cited figures feed that digest, that is the proof rather than a hope.

  It is now `BlueprintIndex` in `check_vanilla_drift.py`, beside the parser everything already
  shares. It takes parsed roots rather than a game path, so `validate_mod.py` can use it in CI
  where there is no game — which is what #264 needs.
  ([#265](https://github.com/vixygrey/qud-expanded-community-edition/issues/265))

### Fixed

- **A legendary gunsmith no longer stocks twenty to thirty of this mod's arrows.** The six revived
  arrows are meant to be an occasional find — weight 2 apiece in `Ammo 2` and `Ammo 3`, one or `1d4`
  at a time, which is what #144 tuned. A second route was handing over twenty to thirty in a single
  shop, and putting them in `RandomItem` besides.

  Nobody chose it. Vanilla's `BaseArrow` carries `DynamicObjectsTable:Ammo` and tags inherit, so
  every arrow built on it was in that pool. The four shells never were — vanilla tags `Shotgun Shell`
  itself rather than `Projectile`, and the shells are built on `Projectile`. That asymmetry is
  vanilla's structure, not a decision anyone made here, and #145 tuned the shells against the arrows
  without either of us being able to see it.

  The arrows now match the shells. `Boomrose Arrow` is vanilla's and is untouched, still distributed
  vanilla's way. Nothing becomes harder to find: all six keep their three drop entries apiece.

  Nothing else changes. The tag is removed with `*delete`, which vanilla uses the same way to take
  `Corpse` out of `DynamicObjectsTable:Items` — so these six leave the ammunition pool and stay in
  every other one they were in.
  ([#261](https://github.com/vixygrey/qud-expanded-community-edition/issues/261))
- **A legendary gunsmith no longer stocks six to eight psionic firearms at once.** The eighteen
  psionic pistols and rifles are meant to be rare — one entry apiece at weight 1 in `Missile 2` and
  `Missile 3`, which against vanilla's own 29 and 125 makes any one of them a 2.6% find at tier 2 and
  0.7% at tier 3 — plus the one your subtype starts with. A second route was handing a single shop
  more of them than the whole world offers.

  That route was never chosen. Both psionic base blueprints carry `DynamicObjectsTable:Guns`, tags
  inherit, and so all eighteen descendants were in the pool a legendary gunsmith draws six to eight
  from. Inherited from Mura's 2.2 and invisible at the blueprints, because the tag is on something
  they inherit from rather than on them.

  The four conventional guns keep the tag; they were tagged directly and a legendary gunsmith
  stocking them is what it is for. Nothing becomes harder to find — every psionic firearm keeps its
  own drop entry at exactly the rarity it had.
  ([#262](https://github.com/vixygrey/qud-expanded-community-edition/issues/262))
- **The mod's options are readable in the settings menu again.** Every one of them showed its help
  text squashed into a thin box running off the bottom of the screen, because the text was written
  at a scale the menu was never given: vanilla's longest help text is 352 characters and ten of the
  eleven here were longer, the worst of them 953 across seven paragraphs.

  Most of that length was a reference table written as prose — the exact attribute requirement each
  skill changed, the vanilla number beside it — and all of it is already in the mod's documentation,
  in a real table. So the trim loses nothing: nine options are now within vanilla's range, and every
  *"set this before creating a character"* warning survives word for word, because those are the
  sentences that stop a run being wasted.

  *Eased skill requirements* was the one I meant to leave long, on the argument that its detail is
  what a player most wants while deciding. In game it was still unreadable, so it came down with the
  rest: it now names the five skills it touches and sends you to the documentation for the twenty
  powers. A help text nobody can read is not a kindness.
  ([#271](https://github.com/vixygrey/qud-expanded-community-edition/issues/271))
- **Character creation stops promising features you switched off.** Every line this mod adds to a
  genotype's panel was static text, while the options deciding whether those things happen are read
  at runtime — so a player who turned off starting skills was still told *"May use Menacing Stare"*,
  and one who turned off the reputation bonus was still told *"+300 reputation with Joppa"*. Four
  lines now appear only when the option that delivers them is on, and return to their original place
  in the list when it goes back on.

  Only lines this mod actually governs move. The Psionic Adept's four chip slots and its Mechanimist
  standing are its genotype rather than additions to one, and the hit-point and stat-point lines
  describe vanilla, so all of those stay put whatever the options say.

  The Adept's skill-point line now reads **95 skill points each level** rather than *30 bonus*. The
  30 was the difference against this fork's own Mutated Human, which is fair enough until you turn
  the skill-point option off and that baseline moves to 50, leaving the panel quoting a bonus that
  had become 45. An absolute figure is true under every setting.
  ([#275](https://github.com/vixygrey/qud-expanded-community-edition/issues/275))
- **True Kin are told about Ego on the attribute screen too, and only while they have chip slots.**
  The genotype panel gained a Chip Interface line in the same release, but Ego is spent one screen
  later — and there a True Kin still read vanilla's sentence saying Ego governs haggling and
  domination and nothing else. That is right for a genotype that cannot mutate and wrong for one
  wearing a psionic chip. Both screens should say it.

  It could not be done in the XML: a genotype `<stat>` merge carries three integers and silently
  discards the description, which is why the first attempt stopped at the panel. Setting the field
  the game has already loaded is the same thing the mod has done to `GenotypeEntry` since 2.3.0.

  Doing it that way turned out better than the static text. The description now **follows the
  option**: turn your own Chip Interface slots off and vanilla's sentence comes back, because
  without slots Ego really does not drive a mental mutation for you. Turn them on and it returns.
  Vanilla's wording is captured from the installed game rather than written into the mod, so what
  comes back is whatever Qud actually ships.
  ([#227](https://github.com/vixygrey/qud-expanded-community-edition/issues/227))
- **Character creation now tells you the chip system exists.** It never did — the word "chip"
  appeared nowhere in `Genotypes.xml`, for any genotype. The slots were there from the first turn
  and nothing in front of you at chargen said so.

  Each genotype's panel now names its slots and what raises them: one for a mutated human, **two for
  a True Kin**, **four for a Psionic Adept**, alongside the reputation and skill-point lines already
  there. And the Psionic Adept's **Ego** description no longer says Ego has nothing to do with
  mental mutations — it carried vanilla's True Kin sentence verbatim, which is right for a genotype
  that cannot mutate and wrong for one wearing a psionic chip. Twenty-three of the thirty-six
  mutations chips grant are Mental, and Qud scales that category with Ego.

  This matters at chargen and nowhere else: **Ego is allocated before you have ever seen a chip, and
  cannot be reallocated afterwards.** A player building toward chips could read that Ego was for
  haggling and domination, spend accordingly, and find out much later. The Adept has the most slots
  in the game and was told the least about them.

  True Kin get the same line by a different route, because vanilla's own stat descriptions cannot be
  changed additively — a `<stat>` merge carries three integers and silently discards the
  description. `docs/LESSONS.md` records that, since the diff for the attempt looks perfectly
  correct.
  ([#227](https://github.com/vixygrey/qud-expanded-community-edition/issues/227))
- **Corrosive gas chips release for roughly twice as long**, because they were granting the wrong
  mutation. Every chip in the acid family — the three corrosive gas chips and the three acid
  chipsets — named the base class `GasGeneration` rather than `CorrosiveGasGeneration`. The gas
  itself was always right: both resolve to `AcidGas`. But the base class releases for
  `1 + rank / 2` rounds where the real mutation gives `rank + 2`.

  How much you feel depends on where you are. A mutation's rank is capped at `level / 2 + 1` by your
  own character level, so a perfected chip's rank 10 is only fully yours at level 18:

  | Character level | Rank | Release, before → after |
  |---|---|---|
  | 1 | 1 | 1 → **3** rounds |
  | 6 | 4 | 3 → **6** rounds |
  | 12 | 7 | 4 → **9** rounds |
  | 18+ | 10 | 6 → **12** rounds |

  Release, not lingering: the cloud disperses on its own schedule afterwards, which this does not
  change.

  Three things came with it. The ability was called "Gas Generation" rather than "Release Corrosive
  Gas"; the mutation contributed no `salt` to your item elements, which it should; and because
  nothing in the game declares `Class="GasGeneration"`, Qud logged an error every time it tried to
  look the mutation up — naming the exact fix, in a log nobody reads.

  These were the only chips affected. Thirty-four of the thirty-five mutations the chips grant name a
  class the game actually catalogues, so the acid family was alone in handing out a quietly degraded
  copy of its mutation. Inherited unchanged from Mura's 2.2, and invisible to every gate: the part
  name is real, so `unknown-part` passes, and the class is real, so it compiles. Nothing looked
  inside the generic — #256 is about making something do so.

  Chips already worn in a save keep the old behaviour until you take one off and put it back on,
  which is enough to fix it. Nothing needs migrating.

  This entry has been wrong twice. It first quoted only the rank-10 figures, as though every player
  saw them; I then "corrected" it to only the rank-1 figures, having watched a level-1 character and
  concluded chip tier did nothing. Both were one row of the table above. The cap is
  `BaseMutation.GetMutationCapForLevel`, and it applies to every mutation from every source — not
  something this fork does.
  ([#226](https://github.com/vixygrey/qud-expanded-community-edition/issues/226))
- The help text for **Chip Interface slots on other humanoids** opened with `{{y;` where Qud's
  colour markup wants `{{y|`. It is the only semicolon form in the mod — against 46 pipe forms in
  `mod/Options.xml` alone, and none anywhere in the game's own data — and the sibling option
  directly above it writes the same sentence correctly, which is the signature of a slip rather than
  a decision. Whether a player saw raw markup in the settings menu or the parser quietly tolerated it,
  the line now matches its neighbours.
  ([#229](https://github.com/vixygrey/qud-expanded-community-edition/issues/229))
- **(internal)** `docs/FEATURES.md` §7.2 said nine new melee blueprints reach no table and named
  `Raven_Iron Maceth` as neither dropped nor tinkerable. The Maceth has been dropped since #38, at
  `PopulationTables.xml:431` — and §10 row 2b said so, in the same document. The count is eight, and
  the eight are the vibro weapons, which are tinkerable. This is the shape #93, #96, #106 and #139
  all had: the fix landed, the prose describing the defect stayed, and the document disagreed with
  itself. The row written *about* the fix knew; the section describing the tables did not.
  ([#231](https://github.com/vixygrey/qud-expanded-community-edition/issues/231))
- **(internal)** `docs/FEATURES.md` §6.3 got two of its six bullets wrong about what vanilla
  already has. Vanilla does not "only put bucklers" in the arm slot — 46 blueprints resolve to
  `Armor WornOn="Arm"`, and bucklers are not among them, carrying `Shield` rather than `Armor`. The
  true claim is stronger than the one I had: no arm item in the game grants more than a single point
  of AV and vanilla's tier ladder there climbs in DV, so vambraces are the first arm line that trades
  DV for AV. And nanoweave and flexi are not new concepts — vanilla ships `Nanoweave Vest` and
  `Flexivest`; what this mod adds is the rest of both sets. That bullet now sits under a second
  heading for families completed rather than concepts introduced, beside the weave cloaks, and the
  summary table at the top of the document no longer calls either one a new armor class.
  ([#232](https://github.com/vixygrey/qud-expanded-community-edition/issues/232))

## [2.5.0] - 2026-08-19

### Added

- **The scour slug** — a bullet that ruins what your target is carrying rather than the target. It takes one random thing out of their pack or off their body and rusts it: a rusted weapon swings far slower, rusted gear is worth almost nothing until repaired, and a rusted **artifact stops working entirely**, so this is how you take a laser rifle out of someone's hands without out-shooting them. It does not need to punch through armour to do it, which makes it an answer to the thing you cannot hurt.

  It asks for something back, and that is the point. Rust ruins the loot you were about to pick up — you can repair it, but rusted repair costs more than ordinary repair, and rusting an already-rusted item destroys it outright. And it is useless against most of the bestiary — far more of it than I first thought. Roughly four creatures in five have nothing it can touch: they carry nothing, or nothing metal, or their claws and cannons are natural weapons the rust cannot reach however armed they look. Against the things it is *for* — the armed and the armoured — about two in five are worth shooting with it. This is a round for the armed and the armoured, and dead weight against beasts.

  Craftable at Tinker II for two scrap metal and one phasic power systems per six rounds — the same materials vanilla charges for a grenade mk III — and found in the ammunition pools from tier 2 up.

  Mura's ten effect bullets are **cut** rather than revived. Six had already gone from the arrows and the shells for reasons that did not change, and the razor bullet failed the test the rest of this ammunition is built on: 813 of 908 creatures bleed, robots included, so it had no matchup it was wrong for — a straight upgrade over a plain slug rather than a trade. The old blueprints stay commented out as a naming reference.
  ([#146](https://github.com/vixygrey/qud-expanded-community-edition/issues/146))

- **(internal)** `Vixy_AmmoPayload`, the mod's first combat part, and the reason the slug is possible at all. All 19 slug consumers name their own projectile on `MagazineAmmoLoader`, which only reads the round's `ProjectileObject` when that field is blank — so every effect bullet Mura wrote was loaded, fired, and had its payload thrown away. Blanking the field the way #145 did for the four shotguns was not available: for shotguns both pellet projectiles are identical to the round's own, while for slugs that field is where the weapon's ballistics live, and flattening all 19 would take the Sniper Rifle from 1d8/pen 7 and the Linear Cannon from 2d12 `Vorpal` down to `ProjectileLeadSlug`'s 1d6/pen 3.

  So the part merges the round's payload *into* the weapon's projectile instead. One `Load="Merge"` on `BaseFirearm` reaches all 19 plus both Masterwork variants and anything a future Qud release adds, adding a part and replacing no attribute. It needs two events because one is not available: a part merged onto an abstract base is always dispatched *before* the concrete blueprint's own, and `IPart.Priority` can only move a part earlier — so it reads the round at `LoadAmmoEvent`, while the loader still holds the stack it is about to draw from, and applies the payload at `ProjectileSetup`, which is a separate dispatch where ordering stops mattering.
  ([#146](https://github.com/vixygrey/qud-expanded-community-edition/issues/146))

- **(internal)** `tools/check_docs.py` refuses a `CHANGELOG.md` release block that repeats a `###` section, or names one Keep a Changelog does not define. This has reached `main` twice — two `### Fixed` blocks corrected by hand before 2.4.0, then two `### Added` blocks I introduced in #236 by anchoring an insertion on `## [Unreleased]` without looking for the section already below it. The hand-fix is exactly what failed to prevent the second, which is why this is a check rather than a third correction. `tools/test_check_docs.py` is new alongside it, and was verified by stubbing the guard out and confirming the two reporting cases fail.
  ([#237](https://github.com/vixygrey/qud-expanded-community-edition/issues/237))
- **(internal)** `docs/LESSONS.md` records the asymmetry behind both wrong claims in the ammunition work: an issue gets checked against the game, and the prose written afterwards does not. Re-reading #145 end to end found every claim in it correct — the weapon list, all ten shell configurations, the gas densities, the resonance figures including the non-obvious one that vanilla's mk I sets `Level="2"`, and the takedown shell's anatomy and save mechanics. What was wrong had been written later, in the commit messages, XML comments and changelog entries explaining the finished work, where nothing checks a factual sentence and the result reads as more authoritative than the issue did.
  ([#235](https://github.com/vixygrey/qud-expanded-community-edition/issues/235))

- **(internal)** `docs/LESSONS.md` now says that the parser which copes with vanilla's malformed XML is **importable**, not just that the drift checker owns one. Five of the game's own files embed control characters as numeric references that XML 1.0 forbids, and the lesson has warned about them — and about never swallowing the failure — since the 208 phantom orphaned-merge defects that found them. It described what `tools/check_vanilla_drift.py` does, though, rather than what a new script should do, and I read it as a property of that tool.

  So I wrote my own `ET.parse` inside a `try/except` anyway, and got two empty results that read as discoveries: that vanilla has no shield with an armour value above 2, and that nothing at all occupies its `Arm` slot. Both false — the second by 46 items — and both were about to go onto the wiki as fact. Routing the same scan through `parse(path, lenient=True)` took it from 1,913 blueprints to 5,202, because everything `Items.xml` defines had been silently absent.

  Recorded as two sentences and a snippet on the existing bullet rather than as a new lesson. The rule already has an owner, and a second entry describing the same trap is the duplication this repository has corrected four times.
  ([#233](https://github.com/vixygrey/qud-expanded-community-edition/issues/233))
- **(internal)** `tools/validate_mod.py` recognises the `Vixy_` prefix as well as `Raven_`, and gains a test suite. The split is `docs/STYLEGUIDE.md` §3.1 — `Raven_` is Mura's attribution and stays on everything inherited from CoQE, while content added to this fork takes `Vixy_` — but the validator predated it and tested for `Raven_` literally, so a `Vixy_` object read as a *vanilla record*. Six sites, failing two different ways: `check_merge_discipline` and `check_part_names` would have reported new content as charter rule 1 violations and unknown classes, while `check_reachability`, `check_table_targets`, `check_scripting_parts` and the tier/value curve would simply have skipped it. Four of the six fail by staying silent, which is a clean green run over content nobody checked.

  Both prefixes now live in one `MOD_PREFIXES` constant, with `MOD_PART_PREFIXES` derived from it so a third prefix cannot update one and miss the other. New content is held to the tier and value curve like everything else — that check exists because #10 got prices wrong, and new content is where that recurs.

  `validate_mod.py` gates every commit and was the only tool in `tools/` without tests, which mattered more here than usual: "it still passes" proves nothing about a check that fails by skipping. `tools/test_validate_mod.py` therefore asserts both directions at every site, and was itself checked by reverting the constant to `Raven_` alone and confirming five tests fail. That exercise caught two flaws in the tests rather than the code — they had been reading `MOD_PREFIXES` to decide what to test, so removing a prefix would have silently narrowed the suite, and the part-name test had been passing without the check ever running, because `check_part_names` returns early when the API snapshot is absent from the fixture.
  ([#224](https://github.com/vixygrey/qud-expanded-community-edition/issues/224))

- **(internal)** `docs/LESSONS.md` records four traps from the investigation into reviving the effect slugs ([#146](https://github.com/vixygrey/qud-expanded-community-edition/issues/146), [#210](https://github.com/vixygrey/qud-expanded-community-edition/issues/210)). Each cost real time, and one of them put a false claim into an issue where it sat looking authoritative.

  **Containment is not dispatch.** Putting `MissilePerformance` on a round looked like a free way to let ammunition modify a shot without touching a single vanilla weapon. It would have loaded, fired and done nothing: `GetMissileWeaponPerformanceEvent` dispatches only to launcher, projectile and actor, and `MagazineAmmoLoader` forwards to the round it is holding only when `CascadeTo(cascade, 4)` — while the event declares `CascadeLevel = 1`. Being held by something is not the same as being dispatched to.

  **`Priority` can only move a part earlier.** `AddPartInternals` inserts by `IPart.Priority`, equal priorities append and a higher one walks backwards, so nothing can be placed *after* a part already in the list — and `ObjectBlueprintLoader.Bake` adds inherited parts before the blueprint's own. When a part must run after another, the answer is never a knob; it is a second event.

  **Search where the effect is applied, not where the part is used.** I argued on #210 that bleeding is melee-only in Qud by design, on the evidence that `BleedingOnHit` sits on two melee objects. Enumerating every `new Bleeding(` call site instead returns the Short Blades critical-hit bleed — from the tree's root class, no power purchased — and the Bow and Rifle tree's Wounding Fire, which is bleeding at range and always has been. A part census answers a much narrower question than it appears to.

  **A boolean's name is not its semantics.** `Bleeding.Stack = true` *merges* into an existing bleed and adds no new effect; `false` — the default on `BleedingOnHit` — piles independent ones on, so an XML payload that omits the attribute quietly gets the compounding version. The same trap runs through the skill data, where one power is the tree *Bow and Rifle*, the entry *Draw a Bead*, and the ability *Mark Target*.
  ([#217](https://github.com/vixygrey/qud-expanded-community-edition/issues/217))

- **(internal)** `docs/LESSONS.md` records why a playtest of the scour slug read as a broken effect for a session. `RustOnHit` picks one item at random from equipment and inventory together, so the target's pool size is the whole experiment — and I sized it by reading XML. `Wraith-Knight Templar` declares one `<inventoryobject>`, nothing on its chain declares a `<builder>`, and the creature appears in no population table, so a pool of one predicted rust-then-dust in two hits. It took five or six. Three hypotheses about code fell before the answer arrived from looking at the creature: it had armed itself after spawning with a second weapon its blueprint never mentions, and both runs are ordinary variance for a pool of two. Nothing was broken. The entry also notes that examine shows only equipped items and no wish dumps another creature's pack, so the only reliable census is killing it and counting what drops.
  ([#240](https://github.com/vixygrey/qud-expanded-community-edition/issues/240))

- **(internal)** The creature census the scour slug's design rests on is now **recomputed from the game rather than written down**. `tools/snapshot_qud_api.py` gains `collect_census`, which counts vanilla's creature blueprints by what an effect reaching for a target's belongings can actually touch, and `check_docs.py`'s `vanilla-figure` check now reads the mod's own **XML comments** as well as the documents.

  That second half is the fix. `282 of 908 creature blueprints` sat in an `Ammo.xml` comment through review and a release, and the denominator turns out to be unreproducible under any filter I can construct — while 813, the numerator beside it, comes out exactly. Nothing caught it because nothing had ever read an XML comment, and `CITED_FIGURES` could not express a census anyway: it reads one attribute off one blueprint. The definition now lives in a docstring beside the code implementing it, and the buckets are asserted to partition the set, so a category added without its arithmetic fails generation instead of quietly summing to the wrong thing.
  ([#242](https://github.com/vixygrey/qud-expanded-community-edition/issues/242))

- **(internal)** The creature census gains the **humanoid subset** — 340 blueprints, of which 134 have a rustable item against 202 that do not. Quoting only the whole-bestiary share reads as a round that does nothing; the pair is the honest claim, because "a round for the armed and the armoured, and dead weight against beasts" is a statement about two populations and needs both numbers to be checkable.

  Measuring it also killed my own assumption. I expected the blueprint census to *overstate* how dead the scour slug is, since it weights a unique legendary the same as a snapjaw. Restricting to creatures reachable from a vanilla population table moves the rustable share from 18.8% to 17.4%, and weighting by how many table entries name them takes it to 13.6%. The census was generous, not harsh — so `Chance="5"` stands, and what needed correcting was the description rather than the value.
  ([#242](https://github.com/vixygrey/qud-expanded-community-edition/issues/242))

- **(internal)** `check_docs.py`'s figure patterns now tolerate a line break. A pattern with a literal space stops matching the moment prose reflows — and reports nothing while doing it, which is the check failing in precisely the way it exists to prevent. Every census claim in `docs/FEATURES.md` was silently unbound for that reason before I noticed the checked-figure count had not risen as far as it should have.
  ([#242](https://github.com/vixygrey/qud-expanded-community-edition/issues/242))

- **(internal)** `tools/snapshot_qud_api.py` now **refuses to mix its two part sources**, in either direction. The committed snapshot is built with `--assembly` — 1605 part names against the 949 vanilla's own XML happens to use — and the digest covers that list, so a run using the other source is not comparable. Two failures came out of that, and the second is the one that matters: a plain regeneration over an assembly-built snapshot dropped 656 names in silence, surfacing much later as `validate_mod.py` rejecting a mod part that is perfectly real; and `--check` across the same mismatch reported a current file as **STALE**, exited 1, and advised *"Re-run without `--check` to update"* — the exact command that performs the drop. The tool handed you the wrong fix for a problem you did not have.

  Both paths now stop before doing any work and name the flag that reproduces the committed snapshot. `tools/test_snapshot_qud_api.py` is new and covers both directions plus the two cases that must stay quiet: a first generation with nothing to compare against, and a snapshot too broken to read.
  ([#244](https://github.com/vixygrey/qud-expanded-community-edition/issues/244))

- **(internal)** `tools/snapshot_qud_api.py --check` now runs as a pre-commit hook. Nothing ever ran it, so `tools/qud-api.json` going stale after a Qud update was invisible until it misfired — as `validate_mod.py` rejecting mod XML that is perfectly correct, or worse, quietly accepting a name the new build removed.

  `always_run` rather than a file pattern, deliberately: what it catches is a *Qud update*, which correlates with nothing in a diff, and the case that matters most is the one any pattern misses — Qud updated last night and today's commit is a docs change. About 1.5 seconds where the game is installed. Where the game, the .NET SDK or `ilspycmd` is absent it skips loudly and passes, in the same shape `compile-scripting` already uses, so a contributor without them is not blocked by a hook they cannot satisfy. `--require` turns that skip into a failure.

  The split is the whole point and is what the new tests hold: a missing dependency skips, a stale snapshot does not. Collapsing them either way breaks the check — one way it blocks everyone, the other way it never fires.

  `README.md` is corrected in the same pass. It still said `--assembly` was for "if you ever need a
  part vanilla declares but never uses — but the default does not", which #244 made false: the
  committed snapshot is built with that flag, so it is what reproduces it, and a plain run is now
  refused. I fixed that framing in the script's docstring and its `--help` when I wrote #244 and
  missed the third place it was written down.
  ([#246](https://github.com/vixygrey/qud-expanded-community-edition/issues/246))

### Changed

- **The four effect shells are cheaper to craft.** They cost two scrap metal and one **pure alloy** for three, and pure alloy is a bit the game hands out for plasma, gravity and time dilation grenades — not for a paper cartridge carrying a dialled-down payload. They now cost two scrap metal and one **phasic power systems**, which is exactly what vanilla charges for the gas, flashbang, thermal, freeze and high explosive grenades mk III whose effects they borrow.

  Nothing else about them moves. Incendiary, cryo and flechette still sit behind Tinker II and takedown still does not, because that gate was always `BuildTier` rather than the materials — which is clearer now that the bits no longer reach the third tier on their own. Decided while pricing the scour slug, which had inherited the same mistake before it shipped.
  ([#146](https://github.com/vixygrey/qud-expanded-community-edition/issues/146))

### Fixed

- **(internal)** `CHANGELOG.md` had **four** malformed release blocks, not the one that prompted the check. `[Unreleased]` and `[2.4.0]` each carried two `### Added` sections, `[2.4.0]` two `### Fixed`, and `[2.3.0]` two `### Changed` — so entries under the second copy read as a separate group, and anyone scrolling for what changed could stop at the first and miss half of it. Every duplicate is merged into its first section with entry order preserved.

  `[2.3.0]`'s `### Internal — tooling` section is also gone, its 29 entries redistributed into that release's existing **Added** (10), **Changed** (11) and **Fixed** (8). It predated the `**(internal)**` marker that now does the same job, and a section name Keep a Changelog does not define is one the new check cannot let past. All 137 entries in the file are unchanged in wording and none was lost — verified by diffing the entry set before and after.
  ([#237](https://github.com/vixygrey/qud-expanded-community-edition/issues/237))

- **(internal)** Three documents claimed that bleeding in Qud is melee-only *by design* and that putting it at range would invent a mechanic the game had declined to have. Both halves are false, and I had repeated them in `docs/FEATURES.md`, in the `Ammo.xml` comment above the reserved quill arrow, and in the released 2.4.0 entry below. `XRL.World.Parts.Skill.ShortBlades` — the tree's root class, no power purchased — bleeds on every critical hit, and `Rifle_WoundingFire` applies `Bleeding` at range from `MissileWeapon.cs`. `Sharpened Polyp`, cited as a natural weapon, is a wieldable `LongBlades` item.

  The claim came from surveying where `BleedingOnHit` is used rather than where the `Bleeding` effect is applied — a part census answering a much narrower question than it appeared to. What survives is the distinction the prose had collapsed: the **part** is melee-only, which is genuinely why the quill arrow was inert and why #201's fix was right; the **mechanic** is not. The 2.4.0 entry is corrected in place with a note saying so, rather than quietly rewritten.
  ([#219](https://github.com/vixygrey/qud-expanded-community-edition/issues/219))

- **The fullerite greathammer is two-handed now**, like every other greathammer. It was the only one in the family missing `UsesTwoSlots`, so it could be swung one-handed alongside a shield or a second weapon — a 3d6 weapon with a penetration bonus getting a slot it was never meant to have. If you are carrying one, expect it to need both hands from now on.

  Inherited from upstream 2.2 rather than introduced here. The reason it slipped is visible in the shape of the file: every other tier is a merge onto a vanilla two-handed blueprint that already carries the attribute, and fullerite is the one tier with no vanilla counterpart to merge onto, so it had to be written by hand. Found while playtesting the scour slug, when a Wraith-Knight Templar turned up holding a one-handed sword and a hammer at once.

- **The flawless crysteel greathammer drops "two-handed" from its name.** Every other greathammer in
  the family is just `<material> greathammer`, and this one alone kept vanilla's older phrasing — so
  it read as though it were a different kind of weapon when it is the same kind at a different tier.
  Nothing about it changes but the label; it was already two-handed, and the word was doing no work
  the family's naming does not already do.
  ([#239](https://github.com/vixygrey/qud-expanded-community-edition/issues/239))

- **(internal) The snapshot check's dependencies are documented, and the PATH export now explains itself.** `CONTRIBUTING.md` had nothing about `tools/snapshot_qud_api.py` at all — `compile_scripting.py` and `check_build_log.py` were both covered, but the one that runs on *every* commit was not, so a contributor's first encounter with it was a skip with no page to turn to. It now has a section: what the snapshot is for, that it is regenerated after every Qud update, that `--assembly` is how the committed one is built rather than an optional extra, and what it needs.

  The `ilspycmd` remedy also gained the reason it is necessary. Both messages already said `export PATH="$PATH:$HOME/.dotnet/tools"`, which is correct advice that reads as redundant to anyone who has already installed the tool — because the path *looks* configured. The .NET installer writes `/etc/paths.d/dotnet-cli-tools` containing the **literal** string `~/.dotnet/tools`, and `path_helper` copies entries from that directory verbatim without expanding `~`, so the entry resolves to a directory named `~` and matches nothing. `echo $PATH` shows it; `command -v ilspycmd` finds nothing. Saying so turns advice that looks already-done into advice that is obviously needed.

  Found because the hook had been skipping on every commit on the machine it was written for — loudly, so a visible no-op rather than a false pass, but a check that never ran (#251)

## [2.4.0] - 2026-08-18

### Fixed

- **(internal)** `docs/STYLEGUIDE.md` §1.1b no longer tells contributors that shipped identifiers are free to rename. It was written before the fork released and still opened *"this fork has no saves yet"*, with a table marking CoQE-original blueprint names *"verified free"*. That stopped being true on 2026-08-17 when `v2.3.0` shipped, and nothing mechanical noticed — `check_docs.py` verifies counts, links and section references, none of which is a sentence about the state of the world.

  It surfaced because #201 relied on it. Replacing the quill arrow needed to know whether its blueprint name could be renamed, §1.1b said yes, and `git tag` said the fork had released the day before. The section now states when the window closed, keeps the reasoning for why those names were once free, and records what breaking the rule actually does: `GameObject.GetBlueprint` logs through `MetricsManager` and falls back to the generic `Object` blueprint, so a player's object keeps working while every blueprint-level tag lookup silently answers as something else. It also documents the escape hatch #201 used — comment the shipped blueprint out and give the replacement a new name, rather than renaming in place.

  `docs/LESSONS.md` gains the general form, which is sharper than "documentation goes stale": the dangerous case is not a stale *figure* but a stale *permission*. A wrong number gets repeated; a wrong permission gets acted on. Where a document grants leave to do something risky on the basis of a state of the world, the state belongs next to the grant — a date, a version, a tag — so a reader can check the premise instead of trusting the conclusion.
  ([#211](https://github.com/vixygrey/qud-expanded-community-edition/issues/211))

- **The quill arrow did nothing, and now it is a hulk honey arrow.** It shipped in 2.3.0 with a bleed that could never fire: bleeding in Qud is a melee effect, and an arrow is not a melee weapon. It flew, hit, dealt its damage, and that was all — no error, no clue, which is how it got through a release.

  I found it while working on the shotgun shells, whose razor shell had exactly the same defect and was cut for it. The bleeding *part* only works in melee — it listens for events the melee path raises and a fired arrow never does — so the arrow got a payload that works at range instead. (This paragraph originally said bleeding at range was something Qud had declined to have. That was wrong, and it is corrected here rather than left standing: short blades bleed on a critical hit, and the Bow and Rifle tree's Wounding Fire bleeds at range. See [#219](https://github.com/vixygrey/qud-expanded-community-edition/issues/219).)

  It is now a **hulk honey arrow**: a waxed bulb of honey behind the head that bursts and sets, miring whatever it hits until the target pulls free. Hulk honey is already the game's own sticky substance, so the thing on the arrowhead explains what the arrow does. It is also the only arrow that works on everything — being stuck needs no legs, so it holds oozes and insects that nothing else in the family can touch, and it drags fliers down as well.

  The quill arrow is not gone, only set aside. Its barb was always the right image for bleeding, so the name is being kept for the day bleeding at range is possible ([#210](https://github.com/vixygrey/qud-expanded-community-edition/issues/210)) rather than spent on something else. If you are holding quill arrows from 2.3.0 they still fire; they simply stop appearing.
  ([#201](https://github.com/vixygrey/qud-expanded-community-edition/issues/201))

- **(internal)** `docs/FEATURES.md` §10 no longer files **Saving Joppa** alongside the two sub-mods that really are separate. Mura's standalone listing says the opposite outright — *"there's no point in installing both as it is already incorporated into the base mod"* — and the shared parts check out: `Raven_Empty Weapon Rack`, `Raven_Empty Gun Rack`, `Raven_Empty Armor Rack` and `Raven_Rusted Door` are declared in `Furniture.xml` identically to the standalone's own copies, attribute for attribute.

  The incorporation is partial, which is the part worth writing down rather than rounding off. `TerrainJoppaRuins` and the 96 KB `JoppaRuins.rpm` — the content the sub-mod is actually named for — are in the standalone and absent here. So "incorporated" describes the furniture, not the ruins.

  It matters beyond the correction: absorbing a sub-mod is something this mod's own author has already done, which makes it precedent for #174 and #175 rather than a departure. Recorded in `docs/PERMISSION.md` §8.4, which is append-only, together with the distinction that precedent is not permission — §8's licence grant is worded as *"their work in this mod"*, and the Bazaar and the Experience Curve are separate Workshop items.
  ([#198](https://github.com/vixygrey/qud-expanded-community-edition/issues/198))

- **(internal)** Four documents no longer say that `"WorkshopId": 0` makes Qud's uploader create a new Workshop item. It does not: the uploader reads a zero as an id, looks up item zero, and answers *Item not found* with every field blank and no way forward. That is what blocked this fork's first upload, and the guidance that caused it was in `docs/STYLEGUIDE.md` §7.1, `docs/FEATURES.md` §10 row 0b, `docs/CHARTER.md`'s release-blocker table, and `docs/PERMISSION.md` §7 — each of them confidently wrong, and one of them the file I would have checked first.

  The correct pre-publish state is **no `WorkshopId` key at all**. The uploader writes the file itself: "Create Workshop Id for Mod..." creates the item and writes a file containing nothing but the new id, after which the description and the rest are merged back in beside it. `docs/STYLEGUIDE.md` §7.1 now says that, with the recovery steps. `docs/PERMISSION.md` is append-only, so its correction is a note under the original text rather than a rewrite of it.

  The evidence was on disk the whole time: of the 72 installed mods that ship a `workshop.json`, two have no `WorkshopId` key and none carries a zero. Recorded in `docs/LESSONS.md` as the general form — before inventing a sentinel, find out whether the consumer distinguishes absent from empty.
  ([#165](https://github.com/vixygrey/qud-expanded-community-edition/issues/165))


### Added

- **(internal)** The Workshop description now states the version, says whether your save carries forward, and carries a **Known issues** section. It described 2.3.1 and listed a quill arrow that does nothing.

  Two caveats go on the page rather than being left for players to trip over. The quill arrow is disabled and the hulk honey arrow replaces it. And **effect shells will not work in a shotgun you already own** — `MagazineAmmoLoader.ProjectileObject` is serialised per object, so a gun created before the update keeps the hardcoded shot it was built with, and only one obtained afterwards defers to the shell. That cannot be fixed in data, and it would read as a bug to anyone who updates and tries the new ammunition with the shotgun already in their hands.

  Fitting four additions into a page with 994 characters of headroom meant cutting something, and `docs/STYLEGUIDE.md` §7.4 says which: the page says what changed, the repository says why. So two sentences of reasoning came out of **Compatibility**, and the standalone *Requires a new character* section merged into **Version and saves**, which now distinguishes updating from 2.3.x (no new character) from arriving from Mura's original (new character). Final length 7,837 with 163 spare.
  ([#214](https://github.com/vixygrey/qud-expanded-community-edition/issues/214))

- **Four effect shotgun shells** — an **incendiary shell**, a **cryo shell**, a **flechette shell** and a **takedown shell**, for the pump shotgun, the combat shotgun, the drum shotgun and the modified handcannon. They drop from `Ammo 2` upward and are craftable once you find the disk.

  These were the second block of `Ammo.xml` to come back, and unlike the arrows in #144 I found out *why* they had never worked. A shotgun never asked its ammunition what to fire: every shell-firing weapon in the game hardcodes its own pellet, and the game only consults the shell's projectile when the weapon leaves that field blank. So each of Mura's shells was loaded, fired, and had its payload thrown away. That is the "degraded to plain ammo" note in #14, and it was structural rather than a bug — which is why nobody could have fixed it by editing the shells.

  The fix is the game's own. An empty projectile field means "fire whatever is loaded", and it is how the grenade launcher and the dart gun already work. All four shotguns now defer to the shell. Ordinary shotgun shells behave exactly as before, because the three pellet blueprints involved are the same object three times over — and the gun's damage readout now reflects the shell you actually have loaded, which is a small gift from the same change.

  Six of Mura's ten did not survive it. A shell fires **eight** pellets and each one carries a full copy of the payload, so anything that bursts detonates eight times: a single gas shell would have blanketed up to 72 cells, and an explosive shell divided into eight pieces stops being an explosion at all. The razor shell could never have worked either — bleeding is a melee-only effect in Qud, which is also true of the quill arrow I shipped in 2.3.0 and did not catch. Vibro, sunder and stasis went for the reasons their arrows went, all three worse when multiplied by eight.

  What is left is what a shotgun already is: many small hits, each carrying something. Incendiary and cryo do per shot roughly what their arrows do per hit — three cryo shells freeze a target, which works on oozes and slugs and worms, none of which have legs for anything else in this list to grab. Getting there took three rounds of play-testing and two wrong answers: a shotgun only lands about two of its eight pellets, and the game warms things back up by a flat 5 a turn, so the first version divided the payload until the game undid it faster than the shell delivered it. The flechette shell is new: I wanted a slug round, the game does not let ammunition change how many projectiles a gun fires, and so the anti-armour shell became a bundle of steel darts instead — worse than buckshot against anything unarmoured, and about half again as effective against the heavily armoured. The takedown shell is the less-lethal round, knocking targets off their feet and dragging fliers down, and it is the only one of the four a character with basic tinkering can learn to build.
  ([#145](https://github.com/vixygrey/qud-expanded-community-edition/issues/145))

- **(internal)** `tools/sync_mod.py` installs `mod/` into the game, as either a dev build or a publish build. The directory Qud loads a mod from is the one the Workshop uploader publishes from, so testing a branch and shipping a release wanted opposite things from the same folder, and the difference was something to remember rather than something to see.

  A dev build has its **`WorkshopId` removed**, which is the only thing binding an upload to the published item — without it the uploader can only offer to create a *new* item, so experimental content cannot overwrite the live page no matter which branch it came from. The title gains a `(dev)` suffix so the mod list says which build is loaded. A publish build refuses unless the tree is clean, on `main`, and level with `origin/main`, and runs the validator before copying anything.

  It came out of #145: the install held `main` while the shells lived on a branch, and wishing for `Raven_Cryo Shell` returned a `Raven_Cryo Arrow` — a blueprint that does not exist does not fail, `WishSearcher` fuzzy-matches to the nearest one that does. Twenty minutes went into a wish command that had been correct all along. The obvious fix, symlinking the folder to `mod/`, would have made `git checkout` decide what ships to subscribers.
  ([#208](https://github.com/vixygrey/qud-expanded-community-edition/issues/208))


- **(internal)** A **Staging** column on the project board, between QA and Done, and a narrower **QA** to go with it. QA was doing two jobs — a change being tested, and a merged change waiting to ship — which meant the column could not answer the only question worth asking of it: is anyone still checking this? QA is now testing alone, Staging is everything merged since the last release, and Done still means live on the Workshop *and* released for players outside Steam.

  Staging is where most items will spend most of their time, because it collects changes that passed QA and changes that never needed it. `README.md`, `CONTRIBUTING.md` and the entry above were corrected to match, since nothing mechanical checks that the board and the documents describing it still agree.
  ([#206](https://github.com/vixygrey/qud-expanded-community-edition/issues/206))


- **A link to the project board**, in the README, in `CONTRIBUTING.md`, and in the Workshop description beside the repository link it already carried. The board is public and is the actual view of what is being worked on; nothing pointed at it, which left three different people short of the same thing — someone judging whether the fork is alive, a contributor looking for something to pick up, and a subscriber wondering whether the bug they hit is already known.

  All three also now carry the rule the board states in its own column descriptions: **nothing reaches Done until the change is live on the Workshop *and* a release has been cut for players outside Steam.** GOG, itch and Linux players install from the release zip, so a change sitting in `main` has reached nobody. Two new columns cover the gap: **QA** for a change being tested, and **Staging** for everything merged since the last release, whether it needed testing or never did. The validators can prove an object is well-formed and reachable; only playing can prove it does what it says, which is the gap that let the quill arrow ship inert in 2.3.0.
  ([#204](https://github.com/vixygrey/qud-expanded-community-edition/issues/204))


- **(internal)** `docs/LESSONS.md` records that an empty result has two explanations, and one of them is the search. It happened twice in one day while building the part-attribute checks. `strings` on `Assembly-CSharp.dll` returned nothing for `Builder` — and nothing for every other name tried, including ones that certainly exist, which was the tell — because macOS `strings` reads ASCII while .NET keeps user strings as UTF-16; trusting it would have put `Builder` into the documents as a defect in Freehold's own data when it is a real mechanism. And a test that was supposed to prove `snapshot_qud_api.py` refuses an unlocatable citation exited 0, because `ruff format` had split the tuple being patched across several lines, so the replacement matched nothing and the run was an ordinary clean one. The gate worked; the test had not run.

  Both have the same shape: a check reporting **zero** of something is indistinguishable from a check that did not execute, while a check reporting a problem at least proves it ran. It is the positive-control lesson one level out, applied to any search or patch whose silence is about to be read as evidence.
  ([#196](https://github.com/vixygrey/qud-expanded-community-edition/issues/196))

- **(internal)** A `<part Builder="…">` naming a class that does not exist now fails the build. `Builder` does not set a member — it names a class in `XRL.World.PartBuilders` that post-processes the part once it is built, which is how #151 came to treat it as an attribute of the element rather than of the part class. That settled the *attribute* and left the *value* unchecked, so a builder that does not exist failed the way this whole family fails: the part loads, the builder never runs, and nothing anywhere says so.

  `tools/dump_part_members.cs` already walked every type in the assembly, so emitting the 21 names in `XRL.World.PartBuilders` alongside the members map cost a few lines and no new tool. Vanilla is held to the rule at generation time, and passes. The mod sets `Builder` on no part today, so this finds nothing now — it is a guard against a future edit, which is the same reason `unknown-part` exists.
  ([#168](https://github.com/vixygrey/qud-expanded-community-edition/issues/168))

- **(internal)** `README.md` says where the mod is published and how to install it without Steam. It carried install paths but no link to the Workshop item, and no route at all for anyone on GOG, itch, or Linux outside Steam — for whom the Workshop is not an option and the release zip is the whole answer. The three routes are now named for who each is for, along with the detail that decides whether an install worked: the folder is right when `Mods/QudExpandedCommunityEdition/manifest.json` exists. Manual installs do not auto-update, so that route points at the releases page and the changelog rather than leaving people to notice on their own.
  ([#185](https://github.com/vixygrey/qud-expanded-community-edition/issues/185))

- **(internal)** Figures the documents quote *from vanilla* are now checked against vanilla. `tools/check_docs.py` already recomputed 45 figures from `mod/`, and `tools/qud-api.json` already checked names against the game, but a number copied out of Freehold's data was checked by nobody and goes stale on any update. `docs/FEATURES.md` §6.7 alone cites a dozen: the thermal and freeze grenade deltas, both gas densities, the flashbang's radius and duration, the high explosive grenade's force and damage, and five figures belonging to the boomrose arrow and its projectile. All fifteen citations across the documents now resolve against the game, and `snapshot_qud_api.py` refuses to write a snapshot if a cited figure cannot be located at all — a citation the game no longer supports should be loud when someone regenerates, not quietly absent from a check that then passes.

  This is the check that would have caught #144's worst claim. That work shipped saying the thermal and freeze grenades do not exist; they do, `HeatGrenade1` and `ColdGrenade1`, sitting in `Items.xml` the whole time, and the arrow payloads were scaled against the wrong anchors because of it.

  It found a real problem the first time it ran, though not the one it was aimed at: the pattern for the boomrose arrow's commerce value was written loosely enough to also match §6.3's note about this mod's carbideweave cloak, and reported the cloak's 5 against the arrow's 0.20. The pattern is anchored on its sentence now. A check that reads prose is only ever as good as the phrasing it looks for, which is the standing cost of `CLAIMS` and now `VANILLA_CLAIMS` too.
  ([#159](https://github.com/vixygrey/qud-expanded-community-edition/issues/159))

- **(internal)** `docs/STYLEGUIDE.md` §10.1 records where checking stops, so the boundary is not rediscovered by someone building the wrong tool. Quoted figures are mechanical and are checked. Claims about how the game *behaves* are not — both such claims in #147 were wrong, both were about control flow, and both were caught by deploying a turret rather than by any static check; grepping decompiled source would produce a check harder to trust than the sentence it guards. Design rationale should not be checked at all. What catches the last two is an acceptance criterion that requires running the game, which #144 carried and which earned its place twice.
  ([#159](https://github.com/vixygrey/qud-expanded-community-edition/issues/159))

- **(internal)** A `<part>` attribute that names nothing on the part class now fails the build. Qud applies attributes by name and discards the ones that match no member — the part loads, the object validates, and the setting you wrote does nothing. `<part Name="TemperatureOnHit" Amount="250" Radius="2" />` is a working part with a dead attribute on it, and nothing anywhere says so. It is the third of the three checks scoped while reviving the effect arrows, and the one that was deferred because a naive version produced 29 findings against a clean codebase, every one of them wrong.

  The three reasons it was hard are all in the member list, so the fix is to build that list properly. **Properties** — `Armor.AV`, `Description.Short` and `TinkerItem.Bits` have bodies rather than being fields. **Inheritance** — `ChargeUse` lives on `IPoweredPart`, not on the five parts the mod sets it on. **Generic bases** — `ModImprovedConfusion` extends a constructed generic, so its `Tier` is one blob-decode away rather than one handle away. `tools/dump_part_members.cs` handles all three and flattens the result at generation time, which keeps `part-attribute` in `tools/validate_mod.py` a plain lookup that needs no game and no SDK in CI.

  It reads the assembly's **metadata**, not its code: `System.Reflection.Metadata` is in-box in the .NET SDK, so there is no `ilspycmd`, no package restore, no network, and nothing executed. What comes back is member names.

  Vanilla is the gate, and it earned its keep on the first run. Four attribute names in Freehold's own data resolved to no member, and each one corrected the rule instead of being waved through: `ChanceOneIn` and `Builder` turned out to belong to the `<part>` **element** rather than the part class — `ChanceOneIn` is a public field of `XRL.World.GamePartBlueprint`, and every value vanilla gives `Builder` resolves to a type in `XRL.World.PartBuilders` — while the two `Tier` hits were the generic-base gap above. With those understood, vanilla passes on all **50,075** of its part attributes and the mod on all **5,371**, which is the evidence that the rule is safe to enforce rather than a hope that it is.

  One limit worth stating: the check is case-sensitive. Vanilla matches its members' casing exactly in all 50,075, so this costs nothing today, and if Qud does fold case then a mismatch is still worth fixing.
  ([#151](https://github.com/vixygrey/qud-expanded-community-edition/issues/151))

- **(internal)** `tools/qud-api.json` carries a `members` map — 21,957 settable names across 1,371 part classes — and the snapshot's digest covers it, so a stale members map is as loud as a stale part list. There is deliberately no flag to skip generating it: a snapshot quietly missing the map would disable the new check in CI and still look green, which is the failure mode this whole family of tools exists to prevent.
  ([#151](https://github.com/vixygrey/qud-expanded-community-edition/issues/151))

- **(internal)** `workshop-target` rejects a `WorkshopId` that is not a real item — a zero, a negative, a string, a boolean — alongside the existing guard against Mura's id. Verified in all five directions, including that an absent key passes, since that is the state an unpublished mod is supposed to be in. The check that already existed would have caught the catastrophic failure (publishing over the original) and said nothing about the merely wasted afternoon.
  ([#165](https://github.com/vixygrey/qud-expanded-community-edition/issues/165))


## [2.3.1] - 2026-08-17

### Fixed

- **Crow helped with bug fixes, and is credited for that rather than as a contributor.** Mura corrected the line after this fork's first release: *"Crow (in the credits) helped with bug fixes, they didn't contribute to the mod itself."* Every credit list here said "contributor to the original" — `README.md`, `NOTICE`, `docs/PERMISSION.md` §4, and `mod/workshop.json`, which ships to subscribers and was live on the Workshop when the correction came in. Mura writes *they* for Crow, so this project does too. The exchange is recorded in `docs/PERMISSION.md` §8.3, which is append-only.

  Crow was also missing from `docs/FEATURES.md` §12 entirely, which is how the wrong wording survived a check against that list. Added there too, so the six credit lists finally agree with each other. Credit is the one condition attached to this fork, so overstating what someone did is the same class of error as leaving them out.
  ([#163](https://github.com/vixygrey/qud-expanded-community-edition/issues/163))

- **The Workshop description's fixes list reads less like an audit.** Each entry now leads with what is true in the mod today and mentions the old behaviour second, where it needs mentioning at all: "all 144 psionic chips can be found now" rather than "72 of the 144 could not be found", "ten more items are findable" rather than "ten items had no route into the world". A few words doing more work than they earned are gone — tables "replaced vanilla's cascade rather than adding to it" instead of "severed" it, and the hit points line drops "as every writeup always said".

  Nothing about the facts changed and no item left the list. The page is read by people deciding whether to trust a fork of someone else's mod, and a list of corrections written in the register of a defect report says something about the original that I do not mean and that is not true. Mura maintained this for years across many Qud versions; I read the whole thing at once with no deadline and their own documentation to check it against, which is a far easier position to find these from than the one they were in.
  ([#163](https://github.com/vixygrey/qud-expanded-community-edition/issues/163))

- **(internal)** `mod/workshop.json` carries the fork's real Workshop item id, `3785441196`, in place of the placeholder `0`. The placeholder is what blocked the first upload: Qud's uploader writes this file itself, and a `0` reads as a lookup for item zero rather than as "no item yet", so it reported the item as not found and never offered to create one. The fix was to remove the file entirely and let the uploader's "Create Workshop Id for Mod..." button write it, then merge the description back in. Two published mods installed locally ship a `workshop.json` with no `WorkshopId` key at all, which is what an unpublished one actually looks like. `docs/STYLEGUIDE.md` §7.1 still says "empty on first upload" and the validator still accepts a zero; both are tracked separately.
  ([#163](https://github.com/vixygrey/qud-expanded-community-edition/issues/163))

- **(internal)** `docs/FEATURES.md` §12 no longer warns that `mod/workshop.json` "is stale: it still contains the older 'please don't fork this' description." That was fixed in #2, long before the first release, and §10 row 0b already records the history. The note sat directly under the credit list it contradicted.
  ([#163](https://github.com/vixygrey/qud-expanded-community-edition/issues/163))

## [2.3.0] - 2026-08-17

The fork's first release. Version numbering continues Mura's lineage rather than resetting —
upstream's last release was 2.2, and this is a continuation of it, not a new mod.

> ⚠️ **This release requires a new character.** Body-part and anatomy identifiers changed
> (see *Changed* below), and those are written into save state. This fork publishes as a separate
> Workshop item, so no existing save is affected — but a save started against a pre-release build
> of this fork will not carry forward.

### Changed

- **Turrets you find no longer come loaded with effect arrows, or boomrose arrows.** When the game stocks a turret itself — one generated out in the world, or one an NPC sets down — it takes any ammunition of the right kind unless that ammunition has been marked otherwise, and nothing had marked these. A bow turret was not merely *risking* a bad arrow either: the game fills a turret with a share of every eligible type, so one carried a dozen effect arrows and a boomrose as a matter of course. Anything that closes to point blank on a turret like that puts the cloud or the blast on the turret and on whatever is standing beside it, and nobody chose to load it that way. Vanilla's boomrose arrow has the same problem and is corrected the same way, by merge.

  This does not touch turrets **you** deploy. Those arrive empty and you load them from your own pack, so the ammunition is your choice — which is exactly why it needed saying about the ones that aren't.

  The other half of the reasoning covers the arrows that do not burst. These are hand-made things: a quill lashed to a shank with sinew, a hollowed stinger with the sac still in it, a scored gas bulb, a phial, a shell of thin wax. None of that survives being cycled through a magazine and a feed mechanism, which is a fair description of why vanilla's own arrows are a shaft and a metal head.

  Deliberately left alone: fullerite, crysteel, flawless crysteel and zetachrome arrows are also unmarked, and are also stocked. They are better sticks rather than hazards, and where Freehold draws the line on handing out end-game materials is their economy to set, not this fork's.
  ([#147](https://github.com/vixygrey/qud-expanded-community-edition/issues/147))

- **The cryo arrow chills harder, because play-testing said the first number was wrong.** It moves from −35 to −50 per hit, which freezes a target solid on the third consecutive hit instead of the fourth. Freezing itself is unconditional — there is no save and no roll, only whether temperature has reached the brittle line — so this is arithmetic, and the arithmetic had a term missing. Temperature crawls back toward ambient every single turn, by a flat five at the magnitudes involved, so each hit is worth less than it looks and every miss hands some of it back. In play that made the old number take four or five arrows rather than the three or four intended. One hit still leaves a target far above the freezing line, so this remains a tool you commit several arrows to rather than an opening move.

  Worth recording alongside it: both temperature arrows are subject to the target's cold and heat resistance. The glowpad used for testing resists heat by a quarter and cold not at all — so the blaze arrow igniting it in two hits is a figure measured against something that was actively resisting, while the cryo figures assume no resistance at all and will stretch against anything that has it.
  ([#144](https://github.com/vixygrey/qud-expanded-community-edition/issues/144))

- **The Workshop description now describes the mod as it currently stands.** It gained a **New features** section covering the eleven options and the six revived effect arrows, and a **Tweaks and fixes** section listing what this fork has corrected — the 72 unobtainable psionic chips, the ten items with no route into the world, the hit points per level, the severed armor cascade, the merges that stopped replacing vanilla records, and Jah-yee's tag fix. Neither existed before, so a subscriber had no way to learn from the page that the mod is now configurable at all.

  Three smaller changes came with it. **Development note** became **Development notes**, with the AI disclaimer joined by a line saying the mod is actively developed. The compatibility section now asks for reports through Steam or a GitHub issue rather than only stating the merge guarantee. And the fixes are listed plainly, with no commentary on how they came to be there — the reasoning belongs here, and the page is a summary that points at it rather than a second copy of it, which is now a constraint rather than a preference. See below.
  ([#160](https://github.com/vixygrey/qud-expanded-community-edition/issues/160))

- **Akimbo's removal is now a line in the fixes list rather than its own section.** The full account — the shared implementation, the Gunslinger calling, the skills screen that would not close — stays here in the changelog, which is where the reasoning belongs. What a subscriber needs from the page is that the power moved, not why it took three attempts to find out.
  ([#160](https://github.com/vixygrey/qud-expanded-community-edition/issues/160))

- **(internal)** The `pre-commit` hooks are current: `pre-commit-hooks` v5.0.0 → v6.0.0, `ruff` v0.16.2 → v0.16.3, `gitleaks` v8.23.1 → v8.30.1. `pre-commit-hooks` v6 is a major release that removes `check-byte-order-marker` and `fix-encoding-pragma` and requires Python 3.9, none of which this repository uses — but it was worth checking rather than assuming, because a hook that strips byte-order marks would quietly break the 13 BOMs the mod's XML depends on. Verified by running every hook against the whole tree on the new versions: all 13 pass, nothing was modified, and the BOM count is unchanged. The bump also needed a second file Dependabot cannot see: `ci.yml` installs ruff by an explicit `pipx install ruff==` pin, so bumping the hook alone would have left CI's formatter one version behind the one contributors run, and `ruff format --check` disagreeing with the hook that just formatted your code is worse than having neither. That pin now carries a comment saying it must move in step.
  ([#110](https://github.com/vixygrey/qud-expanded-community-edition/pull/110))

- **(internal)** The three GitHub Actions CI uses are on their Node 24 releases: `actions/checkout` v4.4.0 → v7.0.1, `actions/setup-node` v4.4.0 → v7.0.0, and `gitleaks/gitleaks-action` v2.3.9 → v3.0.0. Not optional maintenance — GitHub removes the Node 20 runtime from hosted runners on **16 September 2026**, at which point the old versions stop working regardless of any opt-out flag, and runs on the previous pins were already printing the deprecation warning. `gitleaks-action` v3 is a runtime change only, with no change to inputs, outputs or behaviour, so the secret scan still does exactly what it did. Each pin is a full commit SHA with the tag in a trailing comment, as `ci.yml` requires; all three SHAs were checked against the tags they claim to be, because a comment saying `# v7.0.1` is not evidence that the SHA beside it is that release.
  ([#111](https://github.com/vixygrey/qud-expanded-community-edition/pull/111))

- **The dark matter cell is priced for what it holds**, at 1200 rather than 300. It stores 500,000 charge against the advanced chem cell's 50,000 and cost exactly the same, so the ordering was simply wrong.
  ([#9](https://github.com/vixygrey/qud-expanded-community-edition/issues/9))

- **Wristblade prices follow the tier curve end to end.** Tiers 0–5 ran 15/25/35/55/105 while tiers 6–8 already sat exactly on the doubling curve at 320/640/1280 — two progressions in one family. The low tiers are now 5/10/20/40/160, which makes cheap wristblades cheaper. The vibro wristblade keeps its 300; vibro weapons price by their own convention.
  ([#9](https://github.com/vixygrey/qud-expanded-community-edition/issues/9))

- **The Psionic Adept genotype is now named `Psionic Adept` internally**, matching its display
  name. It was `Psionic`. Vanilla's convention is that a genotype's internal and display names
  agree — `Mutated Human`, `True Kin` — and this was the last identifier in the mod that didn't
  follow one of vanilla's own patterns.
  ([#24](https://github.com/vixygrey/qud-expanded-community-edition/issues/24))

- **Workshop metadata now describes this fork.** `WorkshopId` is cleared so the uploader creates
  a **new** item — it previously still pointed at Mura's original, which would have published
  over their page. The description was Mura's pre-handoff notice asking that the mod *not* be
  forked; it is replaced with one that credits everyone in `docs/PERMISSION.md` §4, names
  **Noble Lark** explicitly for the subtype sprites as Mura asked, links the original mod, and
  states plainly that a new character is required.
  ([#2](https://github.com/vixygrey/qud-expanded-community-edition/issues/2))

- **Nineteen blueprints gained the `Raven_` prefix they were missing** — `SteelFist` and the 18
  psionic-weapon projectiles are now `Raven_SteelFist` and `Raven_Projectile*`. They were the
  mod's own objects wearing vanilla-style names, which is a live risk rather than an untidiness:
  vanilla owns `CarbideFist`, `CrysteelFist` and `FulleriteFist`, and **steel is the obvious gap
  in that series**, so a future Qud patch filling it would have collided. The mod was also
  inconsistent with itself, since its other new fist was already `Raven_ZetachromeFist`. Landed
  now because blueprint names are written into saves, and this is the last release where changing
  them costs nothing.
  ([#66](https://github.com/vixygrey/qud-expanded-community-edition/issues/66))

- **The disintegration rifle's projectile is spelled correctly.** `ProjectileDisintegationRifle`
  was missing its second `r` while the pistol's was spelled correctly. It worked, because the
  misspelling was consistent — but it is a blueprint name, so it was fixed as part of the rename
  above rather than left to become a second save-breaking change later.
  ([#66](https://github.com/vixygrey/qud-expanded-community-edition/issues/66))

- **The Workshop preview image now marks this as the Community Edition.** It was Mura's original
  *CoQ / Expanded / by TLR* logo, which gave a subscriber no way to tell the fork from the
  original in a search listing. A green `- CE` now follows "Expanded", and `& VixyGrey` sits under
  "by TLR". Both are in a marker face deliberately unlike Mura's chrome lettering, so they read as
  additions rather than as part of the original logo — Mura's artwork is untouched and still the
  dominant element, per charter rule 3.
  ([#60](https://github.com/vixygrey/qud-expanded-community-edition/issues/60))

- **The chip slot is now `Chip Interface`** (was `Chipset Interface`). The slot holds 108 chips
  against 36 chipsets, so it was named after the minority item; a chipset is a set of chips, so
  the new name is accurate for the whole catalogue. `Psionic Interface` — the name Mura's
  documentation used — was rejected because 13 of the 36 mutations these chips grant are physical
  rather than mental, and because the slot exists on every humanoid rather than only on Psionic
  Adepts. ([#13](https://github.com/vixygrey/qud-expanded-community-edition/issues/13))
- **The Psionic Adept anatomy and body object are now `PsionicAdept`** (was `Yttrian`, a leftover
  from before the genotype was renamed). Follows the convention already set by True Kin →
  `TrueKin`: the display name with spaces removed.
  ([#13](https://github.com/vixygrey/qud-expanded-community-edition/issues/13))

- **(internal)** **Mura has licensed their work under the same terms as mine** — Apache-2.0 for code, CC BY 4.0 for content — so the licences now cover the inherited mod rather than stopping at my own contributions. Their earlier grant was broad in substance (*"generally do with as they please, all I ask is that you give credit"*) but named no licence, which left anyone downstream without defined terms. The exchange is recorded in `docs/PERMISSION.md` §8, which is append-only.

  **The 18 subtype sprites are still not covered.** Mura's advice was to ask Noble Lark directly rather than assume, which is right — Mura naming the sprites inside the original grant shows Mura believed they were theirs to open up, but Noble Lark has never said so himself. He's been asked; until he answers, the sprites are his, used with credit.
  ([#126](https://github.com/vixygrey/qud-expanded-community-edition/issues/126))

- **(internal)** The content conventions and the Chip Interface naming decision moved into `docs/STYLEGUIDE.md`, where naming and identifiers already lived, and its enforcement table was rewritten because it had drifted badly. That table claimed XML well-formedness came from a `check-xml` pre-commit hook that is deliberately absent, that `detect-secrets` runs when it doesn't, that `commitlint` checks commit format when it's a grep in CI, and that "GitHub protection [is] unavailable on private free tier" — this repository is public with nine required checks, linear history and squash-only merges. It's the one table someone would read to decide whether a rule is real, so being wrong there is worse than saying nothing. Every check name in the replacement was verified against `tools/validate_mod.py` rather than written from memory, which caught one I'd got wrong myself in #100.
  ([#115](https://github.com/vixygrey/qud-expanded-community-edition/issues/115))

- **(internal)** The charter now lives in `docs/CHARTER.md` — the six rules I maintain this fork under, the cleared release blockers, the things not to break, and the source-document index. `README.md` and `docs/STYLEGUIDE.md` point at it instead of at `CLAUDE.md`, which is where it had been sitting: a file named after one assistant, holding the rules of the project. Converted to my voice as it moved, and verified to lose nothing — all 15 issue references, both code blocks, the link and the URL are identical. Five references into checkouts only I have were dropped, along with the three section numbers that belonged to them; the reasoning each one carried is kept, since it was never the citation that mattered. Also corrected two stale claims found in passing: rule 4 still asked for the validation script to be written, years after `tools/validate_mod.py` existed, and `docs/FEATURES.md` and `docs/DESIGN_options.md` pointed at charter rules by the old filename.
  ([#115](https://github.com/vixygrey/qud-expanded-community-edition/issues/115))

- **(internal)** The lessons I've collected maintaining this fork now live in `docs/LESSONS.md`, out of `CLAUDE.md` and in a file that isn't named after one particular tool. Seventeen of them, most about Caves of Qud itself and useful to anyone modding it: where the game keeps its own API documentation, which five vanilla data files aren't valid XML, how `[PlayerMutator]` fails by doing nothing, why a public field isn't a supported setter when something caches what it derives, and how to read a method's IL without a decompiler. The rest cover git, GitHub and the tooling here. Two stay private because they're about my own setup rather than about Qud. Converted to my voice as they moved, and the move was verified to lose nothing: every number, identifier, path and issue reference is accounted for.
  ([#115](https://github.com/vixygrey/qud-expanded-community-edition/issues/115))

- **(internal)** The documentation is moving to my own voice — first person, warm, direct — instead of an impersonal register that reports decisions as though they made themselves. I decided these things, and charter rule 2 is about stating reasons, which "I decided X because Y" carries better than "X was decided". It also continues Mura's voice rather than replacing it: `docs/2.2-changelog.txt` is already written this way. `README.md` is the first file converted; the convention is recorded in `CLAUDE.md` § Voice, and `docs/STYLEGUIDE.md` §8 tells contributors plainly that it describes how *I* write and that they should write however comes naturally to them. The AI disclosure in `README.md` and the Workshop description stays, along with the `Co-Authored-By:` trailer — that disclosure is what makes writing in my voice honest rather than misleading. The rewrite was verified to change nothing but voice: every number, identifier, file path, link target and issue reference in `README.md` is identical before and after.
  ([#112](https://github.com/vixygrey/qud-expanded-community-edition/issues/112))

- **(internal)** **Every GitHub Action is pinned to a full commit SHA**, and Dependabot now keeps the pins current. A git tag is mutable: whoever controls an action's repository can repoint it, and the next CI run executes different code with this repository's token. `gitleaks/gitleaks-action@v2` was the sharpest case, a *major* tag that moves on every release. Charter rule 5 already takes that threat model seriously for the mod's own C#, where `validate_mod.py` enforces a banned-API list rather than trusting review — third-party CI actions had none of that scrutiny and run with more privilege than anything in `mod/Scripting/`. Each pin carries a `# vX.Y.Z` comment so it stays readable, and `.github/dependabot.yml` covers `github-actions`, `npm` and `pre-commit` on a weekly grouped schedule. Every job also gained `timeout-minutes`, replacing the 360-minute default. **Behaviour is unchanged**: each action is pinned to the SHA its *current* tag already resolved to, so no version moved — upstream majors (checkout and setup-node v7, gitleaks-action v3) are deliberately left for Dependabot to raise as reviewable PRs rather than smuggled in under a change described as pinning.
  ([#103](https://github.com/vixygrey/qud-expanded-community-edition/issues/103))

- **(internal)** **All nine CI checks are now required to merge**, and four repository settings changed. The branch ruleset required only four — `Validate mod`, `Spelling`, `Secret scan`, `PR conventions` — so a pull request with unformatted mod XML or a failing `ruff check` merged green. That made the two PRs whose whole purpose was enforcement, #75 (ruff) and #79 (XML formatting), add jobs that reported rather than gates that blocked. `XML format`, `Python lint`, `Analyze (actions)`, `Analyze (python)` and `CodeQL` are now required too; all five were first confirmed to report on every kind of PR, including `mod/`-only ones, since a required check that stays pending blocks a branch forever. Alongside: branches are deleted automatically on merge, secret scanning and push protection are enabled (gitleaks catches a secret after it is committed; push protection stops it landing), the repository has a description and topics, and the unused Projects tab is disabled. The wiki stays enabled — it holds nothing yet, but it is where the mod's mechanics will be documented in depth.
  ([#102](https://github.com/vixygrey/qud-expanded-community-edition/issues/102),
  [#106](https://github.com/vixygrey/qud-expanded-community-edition/issues/106))

- **(internal)** `.gitignore` now covers `.claude/worktrees/`. Claude Code agent worktrees are created inside the repository and each is a complete second copy of the working tree, so leaving them untracked meant one `git add -A` would stage the whole duplicate. Worse than ordinary untracked noise because it is intermittent: the worktree is removed when the agent finishes, so it exists only while someone is mid-task. Scoped to `worktrees/` rather than all of `.claude/`, so any agent or skill configuration this project checks in later stays visible. Same reasoning as #63 — a repo's `.gitignore` has to stand on its own.
  ([#98](https://github.com/vixygrey/qud-expanded-community-edition/issues/98))

- **All mod files normalised to LF line endings**, enforced by `.gitattributes`. Upstream was
  CRLF throughout. Diff against the pre-normalisation baseline with
  `git diff --ignore-cr-at-eol upstream-2.2`, and `git blame` skips the conversion via
  `.git-blame-ignore-revs`. Mura's original documents are exempted from normalisation and stay
  byte-for-byte.
  ([#17](https://github.com/vixygrey/qud-expanded-community-edition/issues/17))

- **Repository restructured** so the shipped mod is isolated in `mod/`, with documentation in
  `docs/` and tooling at the repo root. Development files were previously destined to ship to
  every subscriber — measured across 87 installed mods, 8 ship a `README.md`, 5 a `LICENSE` and 4
  a `.csproj` by accident. ([#15](https://github.com/vixygrey/qud-expanded-community-edition/issues/15))

- **Spaces removed from blueprint filenames** — `MeleeWeapons.xml`, `OtherEquipment.xml`,
  `PsionicChips.xml`, `RangedWeapons.xml`. Safe because Qud resolves modded XML by root element
  rather than by filename.


### Added

- **The validator refuses a Workshop description over 8000 characters.** **(internal)** That is Steam's own limit, and it is invisible from here: the JSON stays valid, Qud loads the mod, `prettier` and the spell check pass, and the overflow is cut on Steam's side at upload with nothing said. The first draft of the new description came in at 14,921 characters and would have published as an arbitrary two-thirds of itself.

  The number is not a guess. Of the 72 installed mods that ship a `workshop.json`, the longest description is Caves of Qud Expanded's own at 7943 — Mura evidently found this wall too, and stopped one paragraph short of it. `workshop-description` in `tools/validate_mod.py` now fails the build rather than letting anyone else find it by looking at a truncated page. `docs/STYLEGUIDE.md` §7.4 records the limit and the reason to leave headroom: BBCode markup costs characters a reader never sees, and the description grows with every release.
  ([#160](https://github.com/vixygrey/qud-expanded-community-edition/issues/160))

- **The number of checks required to merge is now counted rather than claimed.** **(internal)** Six documents said ten. Nine were enforced — the test suite ran and passed on every pull request and was not actually required, so a pull request with failing tests could have merged, and nothing said so because the number was written in prose. `tools/required-checks.json` now holds that list inside the repository, where a change to it is reviewable like any other, and `tools/check_docs.py` enforces three things against it: that the documented count agrees, that every required check names a job that exists, and that every job is either required or written down as deliberately not, with a reason. The last of those is what would have caught the original problem — a job can no longer quietly exist without someone having decided about it.

  The near-miss is worth recording next to the fix. Once the test suite was made required, the obvious next move was to update the count in the documents — which would have changed a correct ten into an incorrect eleven. They were only right again *because* of the fix, and the instinct to keep them in step would have broken them. What the repository still cannot check on its own is whether GitHub's own settings still match the file; `--ruleset` compares them, and is kept out of the automatic run on purpose, because a check that passes quietly when it could not reach anything is worse than no check at all.
  ([#152](https://github.com/vixygrey/qud-expanded-community-edition/issues/152))

- **Two new validator checks catch silently-ignored XML.** **(internal)** `unknown-part` verifies every `<part Name="…">` resolves to a real class in `XRL.World.Parts`; `dangling-blueprint-ref` verifies that blueprint-valued attributes name a blueprint that exists. Both failures are invisible today — Qud discards a part it cannot resolve and spawns nothing for a blueprint that isn't there, with no error, no log line, and an object that still loads and still validates. #144 shipped with exactly that defect in its history: `GasObject="GasPoison"` names a *part* on the blueprint called `PoisonGas`, and the arrow would have flown, hit, and released no gas.

  They run **in CI**, which is the part that took the work. Both need names that exist only inside a Caves of Qud install, and GitHub runners have no game. `tools/snapshot_qud_api.py` writes those names to `tools/qud-api.json` — 949 part names and 5,202 blueprints — and that file is committed, so the validator is a plain lookup that runs anywhere. Every name in it is read from the plain-text XML the game ships: no decompilation, and nothing but identifiers, which are the same identifiers this mod's own XML already references in every `Load="Merge"`. Regenerate it after a Qud update; it records the Steam build it came from, and `--check` compares it against your install without writing. A stale snapshot fails as a false positive on a newly added vanilla name, which is loud, and loud is the correct direction for a tool whose entire purpose is catching silence.

  The generator refuses to write a snapshot whose rules do not already hold for vanilla's own data. That gate earned itself immediately: the first version of the part-name rule flagged 55 of Freehold's own conversation parts, which resolve from a different namespace, and the fix was to scope the rule to parts inside `<object>` rather than to grow an allowlist.
  ([#144](https://github.com/vixygrey/qud-expanded-community-edition/issues/144))

- **Six effect arrows, brought back from a file that was entirely commented out.** `ObjectBlueprints/Ammo.xml` held 62 objects behind a comment reading only "removed temporarily": Mura pulled them when a Qud change broke their effects and they quietly degraded to plain ammo. The arrows come back first because they are the smallest claim — only three weapons fire them, and vanilla already ships an effect arrow. They are **blaze** (heat), **cryo** (cold), **dream dew** (sleeping gas), **quill** (bleeding), **starshell** (flashbang) and **stinger** (poison gas). Every figure is derived from `Boomrose Arrow`, the one effect arrow vanilla ships: `BaseArrow` and `BaseArrowProjectile` for the chassis, `StrengthPenetration` 1 over 1d2 damage, and a value of 0.20. None of Mura's arrows used those bases, which is why they had no arrow tile, no whistle, no impact sound and no arrow VFX — they inherited `Projectile` directly. Each payload is then scaled to its own grenade at the ratio Boomrose uses against a high explosive grenade mk I, which is a little over half: gas density is **20** against the mk I grenade's 40, and the flashbang was already weaker than its grenade so it is unchanged. Both gas arrows also named a *part* where a *blueprint* belongs — `GasPoison` instead of `PoisonGas` — so as written they would have fired and released nothing at all.

  Each arrow also carries a **rules description** saying what its payload does, which is the one thing the player could not otherwise find out: the payload parts live on the projectile rather than on the arrow you pick up, so nothing about them reaches the item you examine. That text names no figures. Mura's sunder arrow baked `2d100+20` into its flavour text and one of the two numbers was wrong, which is what hardcoding costs you — say what a thing does and retuning it later cannot make the description lie.

  **Blaze and cryo are deliberately asymmetric, because Qud implements heat and cold differently.** Their grenades sit at +500 and −400 and Mura's ±400 matched those almost exactly, but the same number means very different things in each direction. Burning is gated on a threshold *and* puts itself out the moment the target cools back under it, with damage keyed to how far above the line they are — so the size of the hit sets both how hard it burns and how long, and a hit that barely ignites is worth about two damage in total. Heat therefore takes the honest half, 250, at which two arrows burn a target for about as long as one thermal grenade would. Freezing has no such gradient: crossing the brittle line is simply an immobilise, so halving the grenade moderates nothing — anything past roughly a third of it is still a one-shot disable. Cold takes far less than half, and reaches the same effect over three or four arrows instead of one. Both stay single-target: fire already spreads on its own, so the blaze arrow reaches past what it hits without help, and the cryo arrow is meant to be a precise tool rather than a thrown one.

  **The names are Qud-era, not artifact-era**, which is why none of these is called an incendiary or a frozen arrow. Qud names grenades functionally — poison gas grenade mk I, flashbang grenade mk I — because grenades are recovered old-world tech that arrives labelled: the `Grenade` blueprint carries an `Examiner` part and reads as `UnknownGrenade` until identified. `BaseArrow` has no `Examiner` at all. Arrows are contemporary craft, and vanilla names them for the substance on the tip — boomrose, crysteel, fullerite — never for the effect they produce. Every name here is a noun the game already uses, and dream dew is the clearest case: vanilla's own sleep gas grenade is described as being damp with it.

  **Three of the nine were cut rather than retuned.** The vibro arrow carried `Vorpal`, an attribute vanilla grants to exactly one weapon — the tier-7 Linear Cannon — on ammo craftable six at a time from the two commonest scrap bits in the game. The sunder arrow had a flat `BasePenetration` of 10, higher than any arrow vanilla ships, on a payload meant for breaching walls. The stasis arrow dropped `IsRealityDistortionBased`, which vanilla's stasis grenade sets, so it would not have been suppressed by normality effects the way a real stasis field is. Cutting is not deletion: the bullets and shells stay disabled in the same file for [#145](https://github.com/vixygrey/qud-expanded-community-edition/issues/145) and [#146](https://github.com/vixygrey/qud-expanded-community-edition/issues/146) to work from, now with a comment that records why instead of leaving the next reader guessing.
  ([#144](https://github.com/vixygrey/qud-expanded-community-edition/issues/144))

- **The effect arrows are found and bought, never crafted** — which is the rule vanilla applies to every arrow it ships, and to a great deal else besides. Qud has exactly one crafting system, and tinkering is the *artifact* skill: it builds recovered old-world technology. No arrow is craftable, but neither is a dagger, a long sword, a battle axe, a steel suit, a short bow or a compound bow. The Turbow is the only bow you can build, and it is the only one the game treats as an artifact at all — servos, an air turbine, and an examine step before you know what it is. Slugs and shells are craftable because cartridges serve firearms, which are recovered technology in their own right. An arrow is a stick.

  So these six are reachable through the drop tables instead: weight 2 apiece in the tier 2 through 4 ammo pools, at the same quantities vanilla gives boomrose arrows, which also puts them in merchant stock rather than leaving them to floor luck. A pre-release revision had made them craftable and had merged a recipe onto vanilla's boomrose arrow as well; both are reverted. That would not have filled a gap the developers left — it would have put a stick into the artifact system, which vanilla declines to do for every wooden and forged object in the game. Whether this fork should add a crafting system for *mundane* goods is a separate question and is being tracked as one.
  ([#144](https://github.com/vixygrey/qud-expanded-community-edition/issues/144))

- **The skill tree retunes split into two toggles.** **Qud Expanded: eased skill requirements** governs the twenty attribute requirements the mod lowers or widens — Axe and Cudgel accepting Strength *or* Agility, Long Blade's Dueling Stance at 15 and En Garde! needing only one attribute at 29, Multiweapon Expertise at 21 and Mastery at 25, and Tinker I/II/III at 17/21/25. **Qud Expanded: retuned skill point costs** governs the four prices — free Disassemble, Reverse Engineer at 200, Butchery and Spicer at 100 each. Off restores vanilla exactly in both cases; no power is ever removed and nothing you already own is taken back.

  They are separate because their scopes genuinely differ. Costs apply immediately. Requirements apply **on restart**, and the option says so: Qud builds each power's requirement list once per session and offers no supported way to rebuild it. Splitting them also lets you keep the accessibility changes while paying vanilla prices, which matters if you have turned extra starting skills off — the Cooking price rise exists to offset the free Cooking and Gathering that option grants.
  ([#91](https://github.com/vixygrey/qud-expanded-community-edition/issues/91))

- **Psionic chips can be kept out of loot.** **Qud Expanded: psionic chips in loot** governs the six references that put chips into the artifact tables at tiers 3 through 8. Off means no chip or chipset is ever rolled — and since no chip is tinkerable, that closes the supply completely rather than leaving a back door. Fully live: it changes what is rolled from that point on, and chips already in the world or in your pack are untouched. Psionic Adepts keep their starting chips either way, since those are the genotype rather than an addition to it.
  ([#91](https://github.com/vixygrey/qud-expanded-community-edition/issues/91))

- **The extra skill points per level can be turned off.** **Qud Expanded: extra skill points per level** governs the mod's 65 for a Mutated Human (vanilla 50) and 85 for a True Kin (vanilla 70). Off restores vanilla's numbers exactly. Like hit points, skill points are rolled at each level-up, so this applies from your next level and never removes points already earned. The Psionic Adept's 95 is the genotype rather than an addition to a vanilla one, so it is unaffected.
  ([#91](https://github.com/vixygrey/qud-expanded-community-edition/issues/91))

- **Mutated Human hit points per level are selectable.** **Qud Expanded: Mutated Human hit points per level** offers `1-5` (this mod's documented range, the default), `2-3` (what 2.2 actually shipped), and `1-4` (vanilla). The range is rolled fresh at every level-up, so unlike the chargen options this one takes effect from your next level rather than needing a new character. True Kin and Psionic Adepts are unaffected.
  ([#90](https://github.com/vixygrey/qud-expanded-community-edition/issues/90))

- **The docs now say which mods this one can run beside.** `README.md` gains a compatibility section and the Workshop description states the same: **this fork and Mura's original *Caves of Qud Expanded* must not both be enabled.** They define 36 script types with the same names in the same namespace — one per psionic chip part — which Qud reports as a type conflict, and whichever loads first wins, so you could get either mod's version of any part. That is inherent to being a fork rather than a defect, but nothing said so. The three passages that came closest all made a different claim: "a separate mod… does not replace the original" is about *provenance*, the old compatibility section was entirely about merge discipline against *vanilla* records, and "saves from the original won't work" is about *save files*. A subscriber who already had the original was told three reassuring things and given no warning. The other two mods in the family are confirmed fine and are called out by name: **The Grand Bazaar** shares no object name, no script type and not one vanilla record merged by both — its only merge target is vanilla's `EmptyTent` table, which this fork does not touch — and all 79 of its blueprint references resolve; **Experience Curve Beta** ships no XML and hooks `AwardXPEvent`, which nothing in `mod/Scripting/` goes near. Neither declares a dependency on the original. Both claims come from comparing every declared record and type rather than from play-testing the combinations, and the docs say so rather than overstating it.
  ([#148](https://github.com/vixygrey/qud-expanded-community-edition/issues/148))

- **The wiki is live, and the repository points at it.** Its home page says what it is for and links to `docs/FEATURES.md` for every figure rather than repeating any of them, which is the boundary #108 settled. `README.md` now sends readers to the wiki for how the mod *plays* — builds, synergies, opening strategy — and to `docs/FEATURES.md` for the numbers; `docs/FEATURES.md` §0 states the same split from its end, so the boundary is visible whichever document you arrive at first. Both directions were verified by following the URLs rather than by assuming: the wiki page renders, `docs/FEATURES.md` resolves from the wiki, and the `CONTRIBUTING.md` anchor the wiki links to exists on `main`. That last one is worth checking by hand because GitHub derives heading anchors from heading text, so renaming that section breaks the wiki's link silently and nothing on either side would report it.
  ([#142](https://github.com/vixygrey/qud-expanded-community-edition/issues/142))

- **(internal)** `CONTRIBUTING.md` settles what the wiki is for before anything is written in it: **the wiki explains, `docs/FEATURES.md` specifies.** Build feel, chip-family synergies, opening strategy and what a system is for in the fiction belong there; every figure — tier, weight, price, drop rate, stat modifier, option default and scope — stays in `docs/FEATURES.md`, and wiki pages link to it rather than repeating it. The boundary is worth drawing before the first page rather than enforcing afterwards, because the wiki is a *separate git repository* that not one of the ten checks reaches: no `typos`, no prettier, no validator, no changelog requirement, no review, and nothing standing behind its numbers. That makes it prose with fewer guardrails than the documents that have gone quietly stale four times *with* guardrails, and so the highest-risk place in the project to write a number down. Also recorded: a wiki page cannot use a relative link into this repository, since it is a different one, and that friction is exactly what tempts a contributor to paste a figure instead of linking to it. One thing the issue proposed was already impossible — it offered `CLAUDE.md`'s source-documents table as a home for the rule, and `CLAUDE.md` was taken out of git in #119.
  ([#108](https://github.com/vixygrey/qud-expanded-community-edition/issues/108))

- **(internal)** `docs/LESSONS.md` records four verification traps from the two C# checks, all four about telling a real green result from one that means nothing. That *"could not determine" is not a pass* — and its sharper form, that a negative result can be ambiguous, since the SDK lookup in #136 had its root off by one directory and failed by reporting "no SDK found", indistinguishable from a machine that has none; what caught it was a test built on an independent oracle rather than one sharing the code's mental model. That a suite whose cases all assert failure is satisfied by a permanently broken subject, so the one case that must *pass* is the load-bearing one. That a fixture making claims about files has to derive its clock from those files, because a fresh checkout writes every mtime at clone time — which is how a hardcoded timestamp passed locally and failed in CI. And that zsh does not word-split unquoted parameter expansions, so `env $vars cmd` in a scenario loop silently sets one variable to the whole string and reports OK for a case that never ran. The document's own opening line was corrected in the same pass: it claimed most entries were about Qud itself, which stopped being true around the thirteenth, and it now quotes no proportion at all, since nothing checks one.
  ([#137](https://github.com/vixygrey/qud-expanded-community-edition/issues/137))

- **(internal)** `tools/compile_scripting.py` compiles the mod's C# on demand, closing the last gap no check covered. It runs Roslyn from an installed .NET SDK against four DLLs from the Qud install — `mscorlib`, `System`, `System.Core` and `Assembly-CSharp` — with `-nostdlib+ -noconfig`, so there is no reference-assembly package, no NuGet restore, no csproj and no network; referencing what the game actually loads also removes any question of version skew. All 40 files compile in under half a second, which is why this runs as an ordinary `pre-commit` hook rather than a manual one like the build-log check: it needs the game's assemblies but not a game *launch*. Nothing is written into `mod/` — the assembly goes to a temporary directory and is deleted, because the mod ships C# for Qud to compile at load time and a prebuilt DLL would change that. Two blind spots are stated rather than papered over: the language version is pinned to C# 9, since the SDK's compiler is newer than the Roslyn Unity embeds and would otherwise accept syntax the game rejects, and only the `MOD_*` preprocessor symbol is defined (derived from `manifest.json`) because `VERSION_*` and `BUILD_*` encode the installed game build and hardcoding them would rot silently — the check warns if any file starts using a directive. Both blind spots fail in the safe direction: a false failure that names itself, never a false pass.
  ([#134](https://github.com/vixygrey/qud-expanded-community-edition/issues/134))

- **(internal)** `tools/check_build_log.py` reads back the game's own verdict on whether the mod's C# compiles, and the repo has its first tests. Nothing here compiled `mod/Scripting/` — the validator lints it, but a linter is not a compiler, so the only evidence the 40 files build was that I clicked through the eleven options in game once. Qud compiles every enabled mod through Roslyn at launch and writes the result to `build_log.txt`, so the verdict already existed; this reads it, keyed off the vocabulary in `Assembly-CSharp.dll` rather than guessed strings. The two guards are the point: `identical` compares the working tree against the copy the game actually compiled (the game's `Mods/` entry is a copy, not a symlink, so a green log can otherwise belong to source that no longer exists here) and `fresh` rejects a verdict written before that copy. Without them this would be a green light wired to a log that may predate the code, which is worse than no check because it reads as evidence. It cannot run in CI — compiling needs Freehold's proprietary `Assembly-CSharp.dll`, the same wall that took C# out of CodeQL in #70 — so it is a manual `pre-commit` hook. Its 15 failure paths *are* covered in CI, though, through synthetic save directories that need no game: a guard that has quietly stopped firing is indistinguishable from one that passes.
  ([#134](https://github.com/vixygrey/qud-expanded-community-edition/issues/134))

- **(internal)** `CLAUDE.md` *Lessons learned* records two traps from the option toggles, and `docs/FEATURES.md` §13 records that all eleven options are verified in game. First: a public field is not a supported setter if something caches what it derives — `PowerEntry.Attribute` is writable, but the skill gate reads a cached requirement list whose rebuild is guarded, so the write goes inert once the cache is warm. That is what forced the requirements toggle to be restart-scoped and split from costs, and it generalises to any option built on writing a public field. Second: how to read a method's IL out of the DLL when the metadata and the XML docs cannot answer a question, including why a token-only scan of that method gave the answer backwards. Also records why a CI check reading the event payload must listen for `edited`, and — from the documentation audit in #93 — that stale prose rots with no gate watching, with the most emphatic passages rotting worst, because emphasis is written when a defect is freshest and is exactly what stops it being revisited.
  ([#94](https://github.com/vixygrey/qud-expanded-community-edition/issues/94))

- **(internal)** CI now re-runs on `edited` as well as the default pull request events. The **PR conventions** job reads the title from the event payload, so retitling a PR to fix a failing title neither re-triggered the job nor changed what a manual re-run saw — a re-run replays the original payload. The check stayed red until an unrelated commit was pushed, which is a poor reason to make someone write one.
  ([#91](https://github.com/vixygrey/qud-expanded-community-edition/issues/91))

- **(internal)** `CLAUDE.md` *Lessons learned* records three verification traps from this release's tooling work: that a green gate is only evidence about the property it inspects (three checks passed on XML whose player-facing text had been silently reflowed), that `git checkout <file>` restores from the index and can discard unstaged work without saying so, and that attribute-driven extension points like `[PlayerMutator]` fail by doing nothing at all rather than erroring.
  ([#83](https://github.com/vixygrey/qud-expanded-community-edition/issues/83))

- **Chip Interface slots are now optional, separately for you and for everyone else.** Two new options, both **on by default** so nothing changes unless you ask: *your own Chip Interface slots* (the 1 a Mutated Human gets, or the 2 a True Kin gets) and *Chip Interface slots on other humanoids* (the one merged into the base humanoid anatomy, which reaches every villager, merchant and snapjaw in the game). Psionic Adepts are unaffected by both — their 4 slots are the genotype rather than an addition to it. Nothing in the mod ever puts a chip in an NPC's slot, so the second option changes nothing you can see; it exists so the slot need not sit on every humanoid in the world, where another mod or a later version of this one could start filling them. Both are read at character creation, because a body is built once — set them before starting a character.
  ([#81](https://github.com/vixygrey/qud-expanded-community-edition/issues/81))

- **(internal)** `.gitignore` now covers Python build artefacts, Windows desktop files and `.env`.
  Running the validators writes `tools/__pycache__/`, which was ignored only by the maintainer's
  *global* gitignore — so it was invisible to them and untracked noise for every contributor, who
  could commit bytecode by accident. A repo's `.gitignore` has to stand on its own, because a
  global one is per-developer machine config and is not part of a clone.
  ([#63](https://github.com/vixygrey/qud-expanded-community-edition/issues/63))

- **(internal)** `CLAUDE.md` *Lessons learned* records why a generator must never read the file it
  writes. The preview-image generator was first written to read and write `mod/preview.png`, which
  would have composited the fork's marks on twice from the second run onward — a failure that
  renders fine and shows nothing useful in a diff. Kept because the general form covers anything
  that appends, wraps or composites, not just images.
  ([#62](https://github.com/vixygrey/qud-expanded-community-edition/issues/62))

- **(internal)** `tools/check_docs.py` checks the documentation against the mod, and runs in CI and `pre-commit`. Three staleness sweeps (#93, #96, #130) all found documents asserting things that had stopped being true, and every one was me reading rather than anything checking — the last found four documents claiming 350 new blueprints and 209 vanilla merges when #35 had made them 348 and 211 five months earlier. It can't read a sentence and ask whether it's still true, but it recounts **36 figures** quoted in prose against `mod/` itself, resolves every relative link, checks every `FILE.md §N` cross-reference against real headings, catches a document attributing a check name to the validator when it emits no such name, and confirms Mura's two preserved documents are still byte-identical to the upstream import — comparing against their pre-#23 filenames, since using the current ones reports both as modified when they're untouched.
  ([#131](https://github.com/vixygrey/qud-expanded-community-edition/issues/131))

- **(internal)** The repository has licences: **Apache-2.0** for code, **CC BY 4.0** for content and documentation, both covering my own contributions. `package.json` had claimed `"SEE LICENSE IN LICENSE"` since the fork began, pointing at a file that never existed, and a public repository with no licence is all-rights-reserved by default — which contradicted everything this project says about being a community fork. Apache rather than MIT deliberately: its `NOTICE` file is one downstream redistributors must reproduce, where MIT's attribution requirement only reaches the source, and credit surviving redistribution is the entire point here. What is **not** covered is stated just as plainly in `NOTICE` and `COPYING.md` — the inherited work is Mura's and the subtype sprites are Noble Lark's, and a permission to fork is not a copyright licence I can pass on. `CONTRIBUTING.md` now also says what terms a contribution arrives under, which it never did.
  ([#101](https://github.com/vixygrey/qud-expanded-community-edition/issues/101))

- **(internal)** `CODE_OF_CONDUCT.md` added — the Contributor Covenant 2.1, verbatim apart from the contact method it leaves blank. Reports go through the repository's private reporting form, which keeps them private without publishing a personal email address on a project that will get Workshop traffic; the file also points at GitHub's own abuse reporting, since the person someone needs to report might be me. Linked from `README.md` and `CONTRIBUTING.md`.
  ([#104](https://github.com/vixygrey/qud-expanded-community-edition/issues/104))

- **(internal)** `SECURITY.md`, issue forms and a pull request template added, finishing the contributor-facing documentation begun with `CONTRIBUTING.md`. The security policy is not boilerplate here: this mod ships C# that Qud runs with full process privileges, and any `mod/Scripting/` directory makes the game ask every subscriber to approve it. It states what's in scope, what `scripting-policy` and `serializable-shape` already enforce, and — plainly — that neither is a security boundary but a drift detector, that CodeQL cannot cover the C#, and that there's no compile gate either. Private vulnerability reporting is enabled, so reports have somewhere to go that isn't a public issue. The three issue forms route to the labels that exist and ask for the things I actually need: mod and Qud versions, the full mod list, and where the log lives on each platform. Compatibility gets its own form because charter rule 1 makes it the fork's headline claim rather than a flavour of "bug". Also indexed `docs/DESIGN_options.md`, which had been referenced only from a changelog entry.
  ([#104](https://github.com/vixygrey/qud-expanded-community-edition/issues/104))

- **(internal)** `CONTRIBUTING.md` and `AGENTS.md` added, and `CLAUDE.md` is no longer in version control — which completes the split begun in #115. The workflow rules now live in `CONTRIBUTING.md` where a contributor will actually find them, with the label list corrected to include `security`, `upstream-qud` and `dependencies`. `AGENTS.md` points any coding agent at the charter, styleguide, lessons and contributing guide, and carries none of my preferences. `CLAUDE.md` keeps only how I want prose written, which is exactly what shouldn't travel: it loads automatically for anyone working in this repository, so a contributor using Claude Code would have inherited my voice and ended up with their own pull requests written in it. The obsolete *Validating changes* section was dropped rather than moved — it presented a heredoc as the minimum bar and listed as "useful follow-up checks" things `tools/validate_mod.py` has enforced for months. Every reference to the old file was repointed, including one in `mod/Options.xml`, which ships.
  ([#115](https://github.com/vixygrey/qud-expanded-community-edition/issues/115), [#104](https://github.com/vixygrey/qud-expanded-community-edition/issues/104))

- **Validation script** (`tools/validate_mod.py`) — XML and JSON well-formedness, blueprint
  reachability, `Load="Merge"` discipline, C# part resolution, and filename rules. Python 3
  standard library only, so it adds no toolchain. Known inherited defects are enumerated in
  `tools/validation-baseline.json` against the issue tracking each, so new violations fail while
  catalogued debt does not.
  ([#8](https://github.com/vixygrey/qud-expanded-community-edition/issues/8))

- **CI on every pull request** — validation, spelling, secret scanning, conventional PR titles,
  and a changelog check.
  ([#19](https://github.com/vixygrey/qud-expanded-community-edition/issues/19))

- **Vanilla drift checker** (`tools/check_vanilla_drift.py`) — a maintainer tool, run after each
  Qud update, that verifies every `Load="Merge"` still has a vanilla target and that the copied
  anatomies still match vanilla's `Humanoid`. Both failure modes are otherwise completely silent.

- **Pre-commit hooks** running the same gates locally, plus a guard against committing to `main`.
  ([#18](https://github.com/vixygrey/qud-expanded-community-edition/issues/18))

- I put the repository under version control with the pristine upstream 2.2 import tagged
  `upstream-2.2`, so `git diff upstream-2.2` always shows exactly what the fork changed.

## Credits

Every release carries the credit list in [`docs/PERMISSION.md`](docs/PERMISSION.md) §4 —
**Mura** (`@mura_raven`) for the original mod, and **Noble Lark** for the psionic subtype sprites,
named explicitly as the one condition of the fork permission.

[Unreleased]: https://github.com/vixygrey/qud-expanded-community-edition/compare/v2.4.0...main
[2.4.0]: https://github.com/vixygrey/qud-expanded-community-edition/releases/tag/v2.4.0
[2.3.1]: https://github.com/vixygrey/qud-expanded-community-edition/releases/tag/v2.3.1
[2.3.0]: https://github.com/vixygrey/qud-expanded-community-edition/releases/tag/v2.3.0

### Removed

- **Multiweapon Fighting no longer offers Akimbo.** Akimbo is unchanged and still available in the Pistol tree, and Multiweapon Fighting keeps this mod's reduced stat requirements for Expertise and Mastery. The two powers shared one implementation, and Qud maps each implementation to exactly one power — so this mod's copy was served wherever the game asked for vanilla's, most visibly on the **Gunslinger** calling, which grants Akimbo by implementation name and therefore displayed the wrong power. It went unnoticed for years because both powers were named "Akimbo" and looked identical wherever they appeared; it surfaced only when this fork renamed one of them while working on something else. Giving the mod's version its own implementation fixed the Gunslinger, but a character who then bought both got the ability listed twice and a skills screen that would not close, so the power was removed rather than shipped with a known way to spoil a run.
  ([#11](https://github.com/vixygrey/qud-expanded-community-edition/issues/11))

### Fixed

- **(internal)** Six passages across five documents no longer say the C# has no compile gate, or that nine checks run on a pull request. Both stopped being true when #135 and #136 merged, and I caused it by not grepping the docs for the defect I had just closed — the rule written in the last section of `docs/LESSONS.md`, violated in the same day I added four lessons to that file. `AGENTS.md`, `.github/PULL_REQUEST_TEMPLATE.md` and `SECURITY.md` described a gate that now exists; `docs/FEATURES.md` §13 claimed there was no C# toolchain on the authoring machine; `AGENTS.md`, the pull request template and `docs/STYLEGUIDE.md` §10 all still counted nine checks. The template was the most harmful, since every contributor reads it and it told them the opposite of what the hooks do. Three neighbouring claims were left alone because they remain true: there is still no `.csproj` (the compile takes four DLLs from a Qud install and nothing else), CodeQL still cannot cover the C#, and you still need no toolchain to contribute — the hook skips where the game or an SDK is absent, which is the whole reason that last one survives. `docs/FEATURES.md` §13 keeps its point on a corrected premise: a compiler proves the code builds, not that an option does the right thing to a run, so the in-game verification of all eleven options is still the only evidence of behaviour. `CONTRIBUTING.md` now counts this as the fourth silent documentation rot rather than the third, because a count of past failures that omits the most recent one is the same class of error.
  ([#139](https://github.com/vixygrey/qud-expanded-community-edition/issues/139))

- **(internal)** `CLAUDE.md` and `docs/FEATURES.md` no longer describe already-fixed defects as open. Both still called the `Artifact 3`–`8` table replacements the mod's worst compatibility defect and the highest-value fix available — `docs/FEATURES.md` §7.3 was titled *"replaced, not merged"* under a 🔴 *"Biggest compatibility hazard in the mod"* callout — although all six were converted to merges in #34, and the `<removetable>` chain they were paired with went in #85. Verifying that turned up the same staleness across the whole of `CLAUDE.md`'s *Immediate priorities*: **all five** release blockers listed there are closed, not just the Artifact one. Two harms, both charter-relevant: the list pointed the next contributor at work already done, and it advertised a resolved compatibility hazard in the one dimension charter rule 1 makes the fork's headline claim. The `<removetable>` accounts in `docs/STYLEGUIDE.md` §1.0b and `docs/FEATURES.md` §7.2 were already correct and are unchanged. Also corrected: §0 counts the loot tables as **54** merged and none replaced, and §3.4's chip drop weight reads `10 / 110` rather than `10 / 100`, because merging *adds* the entry to vanilla's uniform 95/5 pool rather than carving it out.
  ([#93](https://github.com/vixygrey/qud-expanded-community-edition/issues/93))

- **Mutated Humans gain 1-5 hit points per level, as the mod always said they did.** The XML shipped `2-3`, against `1-5` in the 2.2 changelog, the WIP notes, and the pinned Workshop feature list. `2-3` is uniform over {2,3}, which is **vanilla's own 2.5 average** — so the mod's headline HP change moved nothing, and it left mutants strictly dominated by True Kin, whose 2-4 shares the same floor with a higher ceiling. That inverts the changelog's stated design, which gives mutants "variability but potential for greater numbers" and True Kin consistency "leaning the opposite from Mutants". Every other HP figure in the docs matches its XML, leaving this the single disagreement. Anyone who preferred 2-3 can select it, along with vanilla's 1-4, under **Qud Expanded: Mutated Human hit points per level**.
  ([#90](https://github.com/vixygrey/qud-expanded-community-edition/issues/90))

- **(internal)** The six vanilla skills `mod/Skills.xml` edits now carry `Load="Merge"` explicitly. They always merged — Qud keys the merge to each power's `Name` and keeps attributes the mod omits, which is why entries carrying only a `Minimum` work at all — but the mod was relying on the loader's default rather than stating intent, and charter rule 1 asks for every touch of a vanilla record to be explicit. Had the default been replacement instead, **18** vanilla powers would have been deleted, including Tinkering's Repair and Scavenger; all 23 powers the mod declares omit `Class=`, so they would also have lost their implementations. Behaviour is unchanged; the guarantee is now written down rather than inferred.
  ([#87](https://github.com/vixygrey/qud-expanded-community-edition/issues/87))

- **Nine item stats and prices corrected.** `Flawless Crysteel Boots` was tagged tier 3 by the mod, overriding vanilla's 7 — wrong loot pool and wrong mod capacity. `Cudgel6th` carried `MaxStrengthBonus="11"` where vanilla and all fourteen other tier-6 weapons use 7. The `Raven_Carbideweave Cloak` cost 5 instead of 40, the only member of a family that is otherwise exactly on the doubling curve. Two zetachrome weapons cost 1200 where every other tier-8 item costs 1280. Psionic pistols offered rifle mods rather than pistol mods, because their base inherits `BaseRifle`. And the fire rifle's projectile was missing its `Fire` attribute, so it most likely was not setting anything alight — its pistol counterpart has it.
  ([#9](https://github.com/vixygrey/qud-expanded-community-edition/issues/9))

- **High-tier armor drops cascade again.** `Armor 7C`, `7R`, `8C` and `8R` each carried a `<removetable>` that severed vanilla's tier cascade, so a tier-8 armor roll produced a zetachrome piece **100%** of the time instead of vanilla's 8.6% — and vanilla gear reachable only through the cascade, like anti-gravity boots and high-energy thermo casks, stopped dropping from those rolls entirely. The cascade is restored and this mod's own zetachrome pieces carry the weight instead, landing at **25%** top-tier: still a large boost over vanilla, but a tier-8 container is a jackpot again rather than a certainty. Tier 7 keeps its existing weights and simply cascades again (67% → 79%). Nothing is removed from any vanilla table any more, so future Qud additions and other mods' entries stay reachable.
  ([#4](https://github.com/vixygrey/qud-expanded-community-edition/issues/4))

- **The two Corrosive subtype sprites are named for their subtype.** `corrosionPsionic.png` and `corrosionGuardian.png` are now `corrosivePsionic.png` and `corrosiveGuardian.png`, matching the "Corrosive" subtypes they illustrate and the `<affinity><Role>` convention the other 16 of 18 tiles already followed. Noble Lark's artwork is untouched — only the filenames change. No player-visible effect; texture paths are not written into saves.
  ([#24](https://github.com/vixygrey/qud-expanded-community-edition/issues/24))

- **(internal)** `tools/validate_mod.py` now checks subtype tiles: every `Tile` must resolve to a real file, and its prefix must match the subtype's affinity. A tile pointing at a missing file renders as nothing with no load error, which is the same silent failure class as an orphaned `Load="Merge"`.
  ([#24](https://github.com/vixygrey/qud-expanded-community-edition/issues/24))

- **(internal)** I reformatted all of the mod's XML to a single consistent style, and that style is now enforced. Indentation is 2 spaces throughout with no tabs — `docs/STYLEGUIDE.md` has required that all along while 18 lines across `Skills.xml`, `Throwables.xml`, `Mods.xml` and `MeleeWeapons.xml` violated it — and long elements put one attribute per line. `prettier --check` runs in CI and formats on commit via `pre-commit`. The reformat was verified to change nothing but layout by comparing the parsed element tree of every file before and after: 19 of 19 identical in tags, attributes and text, BOMs preserved, and `Ammo.xml`'s commented-out 62 objects byte-identical. Mura's original files stay permanently retrievable through the immutable `upstream-2.2` tag, and the reformat commit is listed in `.git-blame-ignore-revs` so `git blame` skips it.
  ([#17](https://github.com/vixygrey/qud-expanded-community-edition/issues/17))

- **(internal)** The XML formatter is configured with `xmlWhitespaceSensitivity: "preserve"`, not `"ignore"`. Under `ignore`, prettier reflowed the *text content* of `<helptext>` in `mod/Options.xml` to satisfy the print width, inserting a newline mid-sentence in a string Qud renders in the options menu. Attribute formatting is unaffected, so the chosen style is unchanged; only text nodes are now protected.
  ([#17](https://github.com/vixygrey/qud-expanded-community-edition/issues/17))

- **(internal)** Prettier with `@prettier/plugin-xml` is declared as the mod's XML formatter, pinned in `package.json` and configured in `.prettierrc.json` (2-space indent, LF, `printWidth` 120). Tooling only, at the repo root — `mod/` is still loaded directly by Qud with no build step, and `node_modules/` is gitignored, so nothing here reaches subscribers. This commit adds the tooling; the reformat itself lands separately.
  ([#17](https://github.com/vixygrey/qud-expanded-community-edition/issues/17))

- **(internal)** Python linting and formatting are now an enforced gate rather than an undeclared habit. `ruff check` and `ruff format --check` run in CI and in `pre-commit`, both pinned to the same version, both scoped to `tools/` — `mod/` holds no Python and the scoping keeps the hook from ever touching shipped files. The gap this closes was not cosmetic: a formatter was already running as an editor hook on the maintainer's machine, so the repo received ruff-formatted output without having declared ruff, and that leaked incidental reformats into unrelated pull requests. `tools/` was reformatted once in #74, whose squash commit is listed in `.git-blame-ignore-revs`. Charter rule 4 is intact — `validate_mod.py` remains Python-stdlib-only at runtime, so no contributor needs ruff to run the validator.
  ([#72](https://github.com/vixygrey/qud-expanded-community-edition/issues/72))

- **(internal)** I fixed the three pre-existing `ruff check` failures in `tools/`: both validators are now executable, making their `#!/usr/bin/env python3` shebangs true rather than decorative (`tools/build_preview.sh` was already `100755`), and `re.S` is spelled `re.DOTALL`. Groundwork for making Python linting an actual gate.
  ([#72](https://github.com/vixygrey/qud-expanded-community-edition/issues/72))

- **(internal)** The validator now enforces charter rule 5's C# limits instead of only documenting them. `scripting-policy` flags file I/O, network access, environment reads, shelling out, external-assembly loading, Harmony and reflection in `mod/Scripting/`, each pattern citing the clause it enforces; `serializable-shape` flags any instance field on a `[Serializable]` type, because that layout is written into every player save and `CLAUDE.md` treats it as an identifier. Both are Python-stdlib-only and run under the existing one command. Prompted by removing C# from the repo's CodeQL languages: every non-`System` dependency is `XRL.*` from Freehold's proprietary game assembly, which is absent from CI, so call-target resolution was stuck at 82% against an 85% threshold with no way to raise it. CodeQL's generic queries could not have expressed these rules anyway.
  ([#70](https://github.com/vixygrey/qud-expanded-community-edition/issues/70))

- **(internal)** The validator no longer exempts two blueprints that no longer exist. `NEW_UNPREFIXED` in `tools/validate_mod.py` still listed `SteelFist` (renamed in #66) and `Yttrian` (renamed in #13). Both were inert, but that list is what makes the validator treat an unprefixed object as a *new declaration* rather than a *vanilla record* — so a stale name is a latent hole in merge-discipline, silently exempting anything later declared under it. The two real entries, `TrueKin` and `PsionicAdept`, now carry a comment saying why they are legitimately unprefixed.
  ([#68](https://github.com/vixygrey/qud-expanded-community-edition/issues/68))

- **(internal)** `tools/build_preview.sh` regenerates the Workshop preview image from
  `tools/preview-base.png` — Mura's original logo, kept unmodified. The sizes, angles and green
  used for the fork's marks now live in a script instead of in whoever last opened an image
  editor, so the next title or credits change does not start by guessing at them. It needs
  ImageMagick and a macOS font, so unlike the validators it is not part of the gate and does not
  run in CI; `mod/preview.png` stays committed and no contributor needs the script to build or
  play the mod.
  ([#60](https://github.com/vixygrey/qud-expanded-community-edition/issues/60))

- **(internal)** I amended charter rule 5: the mod's C# may now hold state and adjust already-loaded
  game data, which is past the "36 inert one-line classes" the rule previously named as its
  ceiling. The hard limits are unchanged — no file I/O, network, telemetry, reflection, Harmony or
  external assemblies. Two new obligations come with holding state: a `[Serializable]` system's
  field layout is written into saves and must be treated as an identifier, and anything mutating
  loaded data must be idempotent and reversible.
  ([#46](https://github.com/vixygrey/qud-expanded-community-edition/issues/46))

- **[@Jah-yee](https://github.com/Jah-yee) credited** in the README and the Workshop description
  as this project's first outside contributor.

- **(internal)** CI leaves an informational note when a pull request has maintainer edits
  disabled, explaining what enabling it would allow. It never fails the build — a contribution
  should not be rejected over a checkbox the contributor owns.

- **(internal)** Pull requests now automatically request my review via
  `.github/CODEOWNERS`, and PRs opened by anyone else are assigned to them by a workflow — so a
  contribution from outside can't sit unnoticed.

- Development note in the README and the Workshop description: VixyGrey uses AI to help with
  development and documentation tasks.

- **Validator now guards Qud's slider crash.** A `Type="Slider"` option with `Min` above 1 sends
  the game's options menu into unbounded recursion; the check refuses any such slider, and also
  catches a `Default` outside its own `Min`..`Max`.
  ([#51](https://github.com/vixygrey/qud-expanded-community-edition/issues/51))
- **The Joppa home base building is now optional** (**on** by default, as the mod has always
  behaved). Turning it off removes the building the next time you enter Joppa and puts the ground
  back beneath it. Nothing vanilla is removed either way. Set it before starting a new character —
  and note that turning it back on afterwards does not rebuild it, because the building is map
  data and once removed from a save it is gone.
  ([#44](https://github.com/vixygrey/qud-expanded-community-edition/issues/44))
- **Two more options: extra starting skills, and the starting reputation bonus.**
  *Extra starting skills* (**on** by default, as the mod has always behaved) gives Mutated Humans
  and True Kin Staunch Wounds, Cooking and Gathering and Meal Preparation, plus Menacing Stare for
  mutants. Turning it off restores exactly vanilla's starting skills — vanilla's own are never
  removed, and Psionic Adepts are unaffected, since their skills are not an addition to a vanilla
  genotype but the whole of what they start with.
  *Starting reputation bonus* (**off** by default) gives Mutated Humans +300 with Joppa. It is off
  because it grants power with nothing attached to use it — the exception written into charter
  rule 6. True Kin keep their vanilla Templar standing either way.
  ([#44](https://github.com/vixygrey/qud-expanded-community-edition/issues/44))
- **Mod options menu, first entry: a mutation-point slider.** Mutated Humans start with 16
  mutation points by default, as this mod has always given, and the slider covers 0–24 for
  players who want vanilla's 12 or something else. Set it before creating a character.
  ([#44](https://github.com/vixygrey/qud-expanded-community-edition/issues/44))
- **(internal)** I recorded the lessons from the options-menu crash (they live in `docs/LESSONS.md` now): read a crash's
  *type* before hypothesising (a stack overflow rules out mod code that cannot recurse), treat the
  sibling design docs as design thinking rather than as an API reference, and batch experiments
  when the only test environment is someone else's machine. Charter rule 6 corrected — it named
  `[OptionFlag]` as the way to read options, where 0 of 87 installed mods use it and 17 use
  `Options.GetOption`.
- **`manifest.json`** — the mod had none, where 64 of 87 installed mods do. Declares `id`,
  `title`, `version`, `author`, `description`, `tags` and `previewImage`, and makes ordering
  against other mods expressible via `LoadBefore` / `LoadAfter` when it is ever needed.
  Versioning continues Mura's lineage: upstream ended at 2.2, so this fork starts at **2.3.0**.
  ([#21](https://github.com/vixygrey/qud-expanded-community-edition/issues/21))

- **(internal)** `docs/STYLEGUIDE.md` — naming, layout, XML and C# formatting, and Steam Workshop
  requirements. §1 records which identifiers are safe to rename and which are load-bearing.
  ([#16](https://github.com/vixygrey/qud-expanded-community-edition/issues/16))
- **(internal)** `CLAUDE.md` — the fork charter: compatibility, causality, credit, DX, safety, and
  configurability, plus the contribution workflow.
- **(internal)** `docs/FEATURES.md` — complete feature reference reconstructed from source: 350
  new blueprints, 209 vanilla merges, and a severity-ranked defect checklist.
- **(internal)** `docs/PERMISSION.md` — fork permission, provenance, and credit obligations.
- **(internal)** Charter rule 6 now states the mod stays **self-contained** — one subscription,
  not a constellation of sub-mods — with options as the mechanism and splitting a last resort.
  Every new feature must ship with its option in the same PR.
- **(internal)** Charter rule 6 settled: mod options will default to reproducing the mod's
  established behaviour, so installing it gives you Caves of Qud Expanded and the options let you
  opt out of parts. ([#45](https://github.com/vixygrey/qud-expanded-community-edition/issues/45))
- **(internal)** `docs/DESIGN_options.md` — design for gating the mod's features behind in-game
  options, written before a first release.
- **(internal)** `README.md` — what the mod is, the credit list, install instructions, and the
  contributor workflow.
- **(internal)** This changelog.


- **The advanced hoversled floats and the sphere of negative weight is a trinket again.** Both
  carried `<stag>` where `<tag>` was meant, so neither tag was ever applied. Thanks to
  **[@Jah-yee](https://github.com/Jah-yee)**, this project's first outside contribution.
  ([#10](https://github.com/vixygrey/qud-expanded-community-edition/issues/10),
  [#50](https://github.com/vixygrey/qud-expanded-community-edition/pull/50))

- **The empty armor rack is now in the Joppa building.** It existed as a blueprint but had no
  route into the world at all — no drop table, no tinker recipe, and unlike its gun-rack and
  weapon-rack siblings it was never placed on the map. It now sits directly below them, completing
  the set along the building's east wall.
  ([#37](https://github.com/vixygrey/qud-expanded-community-edition/issues/37))

- `Raven_ModCorrosiveGasGeneration.cs` renamed to `Raven_ModGasGeneration.cs` to match the class
  it declares. Not a functional defect — the corrosive-gas chips always worked — but it was the
  one file of 36 breaking the filename-equals-class rule, and it is why `docs/FEATURES.md` once
  reported the scripts as "36 referenced, 36 defined" while comparing filenames rather than
  classes. ([#30](https://github.com/vixygrey/qud-expanded-community-edition/issues/30))

- **Ten items that existed but could never be found are now obtainable.** The four nanoweave
  pieces, the four flexi pieces, the mutating mask and `Raven_Iron Maceth` were in no population
  table and had no tinker recipe. I placed each in the table matching its own tier: nanoweave
  (tier 6) in Armor 6C, flexi (tier 5) in Armor 5C, the mutating mask (tier 8) in Armor 8R, and
  the two-handed iron maceth in Melee Weapons 1R alongside its peers.
  ([#7](https://github.com/vixygrey/qud-expanded-community-edition/issues/7))
- **All 144 psionic chips can now drop.** The three chip tables listed only the first chip of
  each of the 12 families plus its chipset — 24 entries where 48 were needed — so **72 of the
  144 chips existed but could never be obtained**, and had no tinker recipe either. Half the
  mod's flagship system was wish-only.
  ([#6](https://github.com/vixygrey/qud-expanded-community-edition/issues/6))

  How often a chip drops at all is unchanged, and each of the 12 families remains equally likely.
  What changes is the mix within a family: with all three chips present at their declared
  weights, chipsets are 10% of a family's results rather than 25%. The 25% was an artifact of
  two-thirds of the chips being absent — the weights themselves always specified 10%.
- **Artifact tables 3–8 no longer replace their vanilla counterparts.** The mod overwrote all six
  outright, which conflicted with any other mod touching them and silently discarded future
  vanilla additions. They now merge, contributing only the psionic-chip entry. Chip drop rate
  moves from 10% to 9.1% as a consequence of adding to the pool rather than carving space out of
  it; commons and rares return to vanilla's ratio.
  ([#3](https://github.com/vixygrey/qud-expanded-community-edition/issues/3))
- **The programmable and reprogrammable recoilers no longer replace their vanilla definitions.**
  The mod redeclared both, which discarded everything vanilla defines on them: their value
  (80 and 210), their tinker recipes, their `Tier` / `TechTier` / `Role` tags, their examiner
  complexity, their display names and their imprint sound. Both now merge, so they keep all of
  that and carry only the mod's intended changes — reduced charge use, and the cheaper recoiler
  becoming re-imprintable.
  ([#29](https://github.com/vixygrey/qud-expanded-community-edition/issues/29))
- **`Skills.xml` now parses.** Line 10 carried a duplicate `Tile` attribute on the Berserk!
  power — the only file in the mod that failed a strict XML parse. Confirmed in-game that Qud's
  loader tolerated it, so the six retuned skill trees have been working all along and no player
  was ever missing them; this is a correctness fix, not a behaviour change.
  ([#5](https://github.com/vixygrey/qud-expanded-community-edition/issues/5))
- Four spelling errors, two of them in text players actually see: "stitched" was misspelled in
  the bronze and iron scale armor descriptions, and the reprogrammable recoiler's description
  read "consider" where it meant "considerable". Two more in source comments.

  (The misspellings are described rather than quoted here on purpose — the spell check in CI
  reads this file too, and quoting them fails the build.)

- **Noble Lark and "chirps" are one person, and had been credited as two.** Mura pointed out that chirps is his Steam name. Every credit list here named both separately, following Mura's original Workshop page — `README.md`, `NOTICE`, `docs/PERMISSION.md` §4, and `mod/workshop.json`, which ships to subscribers. All corrected to **Noble Lark (a.k.a. chirps)**, with Crow listed on his own. Credit is the one condition attached to this fork, so getting a contributor's identity wrong is the worst kind of error this project can make.
  ([#126](https://github.com/vixygrey/qud-expanded-community-edition/issues/126))

- **(internal)** Audited every documentation file against the mod itself and fixed what had drifted. The headline counts — **350 new blueprints and 209 vanilla merges** — were wrong in four places, including `README.md` and `docs/CHARTER.md`. They're **348 and 211**: #35 converted two Recoilers from new declarations to merges, and no document was updated. `docs/FEATURES.md` §11's file map was the worst of it, still describing the mod as it stood at the fork — the pre-#23 filenames with spaces, the `Yttrian` anatomy renamed in #13, `48 merge / 28 new` tables, `Scripting/` as "36 one-line classes" when it's 40 and does far more, no `Options.xml` or `manifest.json`, and Mura's documents listed *inside* `mod/` when they live in `docs/`, which matters because `mod/` is what ships. Also corrected §6.1's per-file table, where `OtherEquipment.xml` read 9 new / 14 merged against an actual 7 and 16.
  ([#112](https://github.com/vixygrey/qud-expanded-community-edition/issues/112))

- **(internal)** `docs/FEATURES.md` §7 said the mod merges **48** vanilla loot tables and declares 28 fresh, while §0 of the same document said **54** merged — the file contradicting itself. 54 and 22 are correct, counted from `mod/PopulationTables.xml`. The 48/28 split predates #34, which converted `Artifact 3`–`8` from replacements to merges; #95 corrected §0 and missed this line. Its header also no longer describes itself as "generated" — I reconstructed that document by reading the whole mod source, because no complete list of what this mod does had ever existed, and it should say so.
  ([#112](https://github.com/vixygrey/qud-expanded-community-edition/issues/112))

- **(internal)** `NOTICE` and `COPYING.md` now describe Mura's grant as it actually reads. I had written that it was "permission to fork" which "says nothing about copyright or licensing", and that Noble Lark's sprites were not covered — having checked by grepping `docs/PERMISSION.md` for "licen" and finding nothing. The body of §1 says the mod is open "to update, fork, and generally do with as they please, all I ask is that you give credit where due, which includes Noble Lark for the subclass sprites", which is an attribution grant in everything but name and which names the sprites inside it. The licences still cover only my own contributions, for the narrower reason that an informal grant doesn't explicitly convey the right to sublicense — but that is now presented as a scoping decision rather than as a warning that the inherited work is off-limits, which it is not. Recorded in `docs/LESSONS.md`, since searching for a keyword instead of reading the document is the repo's own "a gate is only evidence about the property it checks" with me as the gate.
  ([#101](https://github.com/vixygrey/qud-expanded-community-edition/issues/101), [#126](https://github.com/vixygrey/qud-expanded-community-edition/issues/126))

- **(internal)** This changelog had two `### Fixed` sections and two internal ones under a single `## [Unreleased]`, so anyone scrolling for fixes would have found half of them and stopped. Merged, and put in the order [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) specifies — which this file's own header says it follows. Entries where I'm the one who did the work now say so rather than reporting it as though it happened by itself. The reorganisation was verified to move nothing: 367 numbers, 280 identifiers, 89 issue references, 79 links and 78 URLs identical before and after.
  ([#112](https://github.com/vixygrey/qud-expanded-community-edition/issues/112))

- **(internal)** `README.md` now says the mod is configurable. It listed the genotype, the chips and the item families without mentioning that eleven options exist, so the people most likely to want the mod — someone who wants the weapons but not the chip economy, or vanilla's skill requirements back — had no way to tell from the front page. Charter rule 6 exists so nobody has to swallow the whole mod to get one part of it, and the README gave no hint that was true. It also spells out the three scopes, since when a change takes effect is the part people get caught by.
  ([#113](https://github.com/vixygrey/qud-expanded-community-edition/issues/113))

- **(internal)** `README.md` stops calling the local hooks optional and explains how to install them when `core.hooksPath` is set. `pre-commit install` refuses outright in that case, which is the common arrangement for anyone whose dotfiles wire in global hooks — so the instruction as written didn't work on my own machine, and the `no-commit-to-main` hook had therefore never been installed. I found that out by committing to `main` in #119 and having the ruleset reject the push. Recorded in `docs/LESSONS.md`, along with the related trap that `core.hooksPath` silently disables any per-repo hook it has no delegator for.
  ([#120](https://github.com/vixygrey/qud-expanded-community-edition/issues/120))

- **(internal)** Three more clusters of stale documentation corrected, the second sweep after #93. `docs/FEATURES.md` §10 still listed five closed defects as open — two of them 🔴 Critical — and §3.3 and §7.2 still described the 72 chips and nine armor pieces as unobtainable, though both were fixed in #36 and #38. §0, §4 and the file tree still credited Akimbo to Multiweapon Fighting while §10 row 7 recorded its removal in #88, so the file contradicted itself; the class-collision account is kept as settled history rather than deleted, because it is the repo's clearest demonstration that `Class=` is an identifier. And `CLAUDE.md` still said there was no remote, no issue tracker, and that the validation script was "the only automated gate that exists" — all three untrue, and the middle one told contributors the repo's own stated workflow was not yet in force.
  ([#96](https://github.com/vixygrey/qud-expanded-community-edition/issues/96))
