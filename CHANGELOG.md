# Changelog

<!-- check-docs: not-a-file CLAUDE.md - the maintainer's private working notes, untracked by .gitignore since #115. Present on her machine, absent from a clean checkout, so it must never be treated as resolvable. -->

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

- **Kill enough of one people and they send someone** (#190). Off by default.

  Kill five hundred of one faction and, rarely, somebody arrives about it: a named champion of
  theirs, near my level, who says on arrival what he has come for. Five hundred is a lot of one
  kind, so expect this a handful of times in a run rather than often — fifty snapjaws in one cave
  is ordinary play, and that is a tenth of it.

  Both rolls happen the first time I walk into a given zone, never on the kill itself, so a threshold
  crossed mid-fight cannot put somebody into that fight. A zone is retired on arrival whether or not
  anything comes of it, so walking back through somewhere I have already been is completely inert —
  the kill count caps how many can ever come, and this caps how fast. The count is spent rather than
  cleared, so carrying on earns the next one instead of starting over.

  Past a threshold, then, somebody arrives only somewhere I have not been. Crossing five hundred
  kills in territory I have already cleared stays quiet until I move on.

  **Far more rarely it goes the other way** and an envoy arrives from their enemies, pleased and
  interested in me. Who is glad comes from Qud's own faction feelings rather than a table of my
  own, and anybody who would not talk to me is dropped before the choice is made rather than after
  — which narrows it, honestly, to Barathrum's quarrel with the Templar and the Mechanimists. The
  three factions who dislike everyone are the same three who already hate me, and the rest of Qud
  genuinely does not care who I have been killing. I would rather it stay silent than invent
  rivalries the game does not have.

  **Only peoples who could hear about it**, which is fifteen factions, listed and argued with in
  `docs/FEATURES.md` §54.2 rather than derived. Qud has no flag for sentience and the obvious
  proxies are wrong — it names bears and crabs and oozes too. A baboon troop sends no avenger.

- **The Six Day Stilt is more of a market** (#174). Off by default.

  Two more traders — a smithy and a water merchant — a pedlar in the tents that would otherwise stand
  empty, and about a third more stock on every merchant, reaching a tier or two above what they
  usually carry. Tier 6 at best, and rarely; nothing there sells zetachrome.

  **The idea and the two merchants are Mura's**, from the Grand Bazaar sub-mod, absorbed with his
  permission. **The numbers are mine.** His version raises merchant stock about 1.68× and reaches
  tier 8; this is held to 1.3× per merchant and stops at tier 6, so about three quarters of what he
  added is not here. It would be inaccurate to call this a port, and the credit is his either way.

  **His tent layout did not come across, and could not have.** That part is C# declaring vanilla's
  own type name, so it has never run for anybody who installed it — and the only way to point the
  game at a replacement would be to redeclare vanilla's entire Six Day Stilt map cell, which this
  fork does not do. Both of his earlier attempts are shut to me as well: one is a Harmony patch and
  the other shadows a second vanilla type.

  The pedlar is mine. Vanilla's empty tent holds a table; the Grand Bazaar filled it with bedrolls.
  A person with almost nothing to sell is the only version that explains why the tent was standing.

- **(internal)** The API snapshot could not see `mod/Optional/` (#174).

  Three of its collectors globbed `mod/ObjectBlueprints/*.xml` while `validate_mod.py` walks the whole
  tree, so a blueprint in a gated directory produced tag names the snapshot could never learn and
  `snapshot-coverage` reported them for ever. `check_docs.py` had the mirror image: its per-file
  counts were keyed on the bare filename, so a second `Creatures.xml` overwrote the first and
  `FEATURES.md` §6.1 reported one optional feature's three creatures as the mod's forty-six.

  Nobody had hit either, because the Stilt market is the first optional directory to contain
  blueprints at all — `HistoryNames` is a `.json` and `JoppaBuilding` is an `.rpm`. `variant_parents`
  stays scoped to the top level on purpose and now says why: a variant is identified by inheriting a
  blueprint this fork does not own, and an ordinary new creature does that too, so widening it would
  file a merchant as a coat of `BaseMerchant`.

- **(internal)** `scatter-share` can see a merge built from table references (#798).

  A `<table>` reference into a pool this fork does not define scored **zero**, so a merge made
  entirely of them measured as adding nothing at all — in both share checks, silently, with a clean
  run. Not following the reference was right and still is: a shared pool's *contents* belong to
  whoever wrote it. The draw is a different thing, and the draw is mine —
  `<table Name="DynamicInheritsTable:BaseArmor:Tier4" Number="1-2" />` merged into a vanilla merchant
  puts one or two more items in that merchant's stock.

  **It was hiding something the size of a feature.** #174's Grand Bazaar is exactly that shape: it
  takes twenty vanilla merchant tables from 311 to 524 expected items, and three of them —
  `HatterInventory`, `GloverInventory` and `ChefInventory` — measured *exactly zero* added. The tell
  was an impossibility rather than care: `ArmorerInventory` read 0.00 while visibly gaining five tier
  rows.

  **Vanilla's side of every ratio moved with it**, which is the part that needed checking rather than
  assuming. Twenty-four of the snapshot's 121 tables gained quantity, all upward, so shares relaxed
  and nothing already shipped newly breaches. No documented figure moved.

  **And the suite caught a real bug in the first version.** It treated a reference into a *cycle* the
  same as one it could not resolve, so a table naming itself charged a phantom draw;
  `test_a_reference_cycle_terminates` failed and its docstring said why. Five other tests then needed
  updating because they asserted the rule being changed — each rewritten to state the new one rather
  than to go quiet, and one of them had a justification that was already wrong: it claimed
  `snapshot_qud_api` runs the unresolved path, which it does not.

- **Experience follows the gap in tiers** (#792).

  Off by default. What a kill pays now depends on how far above or below me it was: something a tier
  over me pays a tenth more and three tiers over pays half again, while punching down tapers more
  gently than vanilla — two tiers under me pays a third rather than a tenth. **Three tiers under still
  pays nothing**, because that floor is what stops me farming trivia at level thirty, and it is
  vanilla's on purpose.

  The design is Mura's, from the Experience Curve sub-mod. **The implementation could not be**, and
  that is the part worth saying: that mod declares a class with vanilla's own name and relies on type
  resolution preferring its copy. It does not, and never has — so its C# has never run for anybody who
  installed it. The measurement is in #775.

  What replaces it is smaller than what it replaces. `IXPEvent.TierScaling` is a flag vanilla's own
  experience part reads and **nothing in the game ever sets false**, so one part switches it off,
  writes the amount, and leaves vanilla to do the clamping, the multiplier, the award and the party
  pass-down. Only the curve is mine. The sub-mod's whole-file copy had already drifted two behaviours
  behind vanilla with nothing able to show it, which is the cost this shape does not pay.

  One correction carried across deliberately: Mura's comment says three tiers up pays ×1.3 and his
  arithmetic says ×1.6. The code is what shipped and what he tuned against, so ×1.6 is what I built —
  written down in three places, because the comment is the more persuasive of the two.

- **(internal)** `pin-parity` fails a build where a tool's two pins disagree (#787).

  `ruff` and `typos` are each pinned twice — once in `ci.yml`, once in `.pre-commit-config.yaml` —
  and Dependabot tracks the halves in separate ecosystems, so it raises one without the other and
  nothing ever raises both. While they disagree, CI runs a different version of a checker than the
  hook a contributor just ran.

  Both pairs drifted the day before this landed, and nothing mechanical noticed either. The typos
  pair is what decided it was worth building: that one had drifted with no comment and nothing
  watching, and what surfaced it was luck — v1.49.1 stopped correcting one brand name, a changelog
  entry happened to need that word, and the older hook rejected the sentence the newer action
  accepted. Any other word in that release and both pull requests would have merged green.

  **The map of pairs is explicit, and `gitleaks` is why.** The hook is `gitleaks/gitleaks` at
  v8.30.1 while the workflow uses `gitleaks/gitleaks-action` at v3.0.0 — different repositories on
  independent version lines. Any rule pairing them by owner or by prefix reports drift that is not
  there, permanently, and a guard that fires on a correct state is one people learn to bypass.

  It reports three things rather than one, because the quiet failures are the ones worth having: a
  mapped pair whose versions differ; a pinned hook in neither table, so a third tool cannot go
  silently uncovered the way `naming-option-coverage` did the moment a second namestyle arrived; and
  a CI pin it can no longer read, which is a **finding rather than a skip**, since a skip here is
  indistinguishable from a pass.

  Thirteen tests, and I broke the check three ways to confirm they catch it rather than trusting a
  green run — dropping the comparison fails two of them, dropping the `v`-prefix normalisation fails
  eleven, and making the coverage guard vacuous fails one. Scope is the two config files and stays
  there: a version written in a tool's own config or in prose is out of reach, and a check that
  sweeps wider than it can parse is how a skip starts reading as a pass.

- **(internal)** `ruff` v0.16.4 → v0.16.5 and `typos` v1.49.1 → v1.50.0, each in both places it is
  pinned.

  **ruff** is a patch release with three rule fixes — `ASYNC210`, `DTZ007` and `SIM401` — and
  everything else in it gated behind preview, which is disabled here. All three are in ruff's default
  set, so they are live for `tools/` rather than academic: `tools/` contains no `async def`, no
  `await` and no `asyncio` import anywhere, so `ASYNC210` has nothing to fire on, and `ruff check`
  and `ruff format --check` are both clean on the new version.

  **typos is the one that needed testing.** v1.50.0 is a dictionary release — 315 words added to
  `words.csv` — which is the direction that can turn a green tree red without a line of mine
  changing, and the opposite of the v1.49.1 bump below, where the only change removed a correction.
  Reasoning from the release notes would not have settled it. Running it does: clean over the whole
  tree, this file included.

  **The comment added an hour earlier earned itself.** #715 put a note on both typos pins saying
  they have to move together, because Dependabot cannot see one from the other. Its very next act
  was to raise the hook to v1.50.0 and leave the action at v1.49.1 — exactly the drift the note
  describes, in the same file, directly beneath it. Both pins move here.

  That note also made a claim this pull request disproves. It said Dependabot "has never raised the
  hook", which was true when I wrote it and false forty minutes later. The two are tracked in
  separate ecosystems — the action under `github-actions`, the hook under `pre-commit` — so they move
  at different times and in either order, and nothing raises both together. Corrected to say that
  instead, since a pin comment that is confidently wrong is worse than no pin comment.

  Verified the way #110 established: all 17 default-stage hooks against the whole tree on the new
  versions. Every one passes, **nothing was modified**, and the byte-order-mark count is unchanged at
  20. `pre-commit` built fresh environments for both revs, holding ruff 0.16.5 and typos 1.50.0
  beside the older ones earlier revs left behind, so the sweep ran the versions being bumped rather
  than anything cached.

  **And a comment went back where it belongs.** The paragraph describing the Python hooks was written
  directly above them in #75; #79 inserted the prettier block between the two later the same day, and
  it has been stranded ever since — two stacked paragraphs above `- repo: local`, the first of them
  explaining why Python linting is scoped away from `mod/`, which has nothing to do with an XML
  formatter, while its actual subject sat fourteen lines further down.

- **(internal)** `typos` v1.49.0 → v1.49.1, in both places it is pinned.

  A one-word patch release: it stops correcting the brand name `HashiCorp`. That is strictly *fewer*
  corrections, so it cannot turn the spelling gate red — which is the thing worth establishing,
  because a dictionary bump is the one dependency update that can fail a tree nobody has touched.
  The rest of the range is a Rust toolchain bump, an internal refactor and README links.

  **The second file is the find.** `typos` is pinned twice — the action `ci.yml` runs, and the hook
  in `.pre-commit-config.yaml` — and Dependabot raises only the first. Across every pull request it
  has opened on this repository, this is the only one that mentions typos at all, so the bump as
  filed would have left the two dictionaries a version apart. That is the same defect the `ruff`
  pin already carries a comment about, in a tool where nobody had noticed it. Both typos pins carry
  one now, and the fuller note sits beside the action, where the bump lands.

  It is not theoretical, and it caught me writing this entry: naming `HashiCorp` above failed the
  v1.49.0 hook while passing the v1.49.1 action. One brand name is a small consequence. A gate that
  disagrees with the hook a contributor just ran is not, and that is what I would have shipped.

  Verified the way #110 established: all 17 hooks that run by default, against the whole tree, on
  the new versions. Every one passes, **nothing was modified**, and the byte-order-mark count is
  unchanged at 20 — which matters because the mod's XML depends on those marks and a hook that
  stripped them would break the mod quietly. I checked the pin as well as the version: `v1.49.1` is
  an annotated tag, so it dereferences twice before reaching a commit, and the commit it reaches is
  the SHA now in the workflow. The `# v1.49.1` comment beside it proves nothing on its own.

## [2.12.0] - 2026-09-01

### Fixed

- **Sleeping in my armour rests me worse** (#780).

  It was always meant to and never once did — the check read a value nothing in the mod ever wrote, so
  a full pack cost me nothing at all. It costs me now, on a slope rather than a cliff: a little over
  half loaded and I lose a twentieth of my rest, near capacity and I lose a quarter. The game says so
  when I lie down, because a penalty that size ought to be something I notice rather than something I
  work out.

  And it costs twice over, because the longer I lie there the more chances something has to find me.
  Heavily burdened on open ground, that is the difference between three sleeps in five going wrong and
  five in seven.

- **Sleeping somewhere sheltered finally means something** (#777).

  Finding a doorway was supposed to rest me half again as fast as lying in the open. It never did —
  the arithmetic rounded the difference away, so a sheltered spot rested me at exactly the rate of bare
  ground and, because I lay there longer for it, was found more often too. It now rests me the 20%
  faster it always claimed, and carries the same risk it always claimed, rather than one of those being
  a rounding error and the other an accident.

- **My parts stay on my own body** (#769).

  Two of Qud's own mechanisms were putting this mod's eleven player parts onto creatures that are not
  me. Saving while dominating something and reloading bolted all eleven onto the puppet, permanently —
  they outlive the domination. And copying me copies my parts wholesale, so a temporal fugue duplicate
  or a clone carried them with no save or load involved at all.

  Most of them noticed and went quiet on their own. Two did not: worn weapons wore for whoever was
  holding them, and a copy rifling through trash in my zone spent down my own odds of finding anything
  there. Fatigue was the odd one — its check was right for every other purpose and wrong for this one,
  because a body I am dominating counts as me, so it tired out a borrowed body and then charged me for
  the same stretch of time twice.

### Added

- **A sleep suppressor** (#771).

  A two-point implant for the body, turning up wherever the other one- and two-point implants do.
  Nothing can put me to sleep against my will — not sleep gas, not a cudgel to the back of the head,
  not a crungle's stare — and if I am running the fatigue system, I tire half as quickly on top of
  that.

  Two things it deliberately will not do. It does not stop narcolepsy, so it cannot cancel a defect
  somebody took points for at character creation. And it does not stop me collapsing from exhaustion:
  it slows the clock, it does not buy me out of the end of it.

- **(internal)** `wish vixyfatigue` reports the fatigue meter, its stamps and every rate derived from
  where you are standing; `wish vixyfatigue:600` sets it. Invisible unless typed (#782).

- **I choose how long I sleep** (#776).

  The same question a bedroll asks — until this hour or that one — with one more on top: until
  rested. Each says how many rounds it is, which a bedroll does not; "until Harvest Dawn" only tells
  you how long if you already know what time it is. Pick a time and you wake at it or sooner,
  whichever comes first, because being rested always ends a sleep early. Wake on the clock with the
  meter still up and you get no dream — waking early is waking early.

- **You can be made to sleep** (#179).

  Go about three unhurried days without sleeping and you tire; fight for those days and you get
  there in half of them. Long enough after that and you fall down where you stand.

  Crossing the world map costs what it takes. A parasang of ordinary ground is a quarter of a day
  and North Sheva is a whole one, so a long haul arrives tired and a very long one arrives ready to
  drop. Survival skills cut the fatigue as well as the time.

  What tiredness costs you is not your attributes. At exhaustion you cannot cross the world map, the
  way being famished already stops you, and from weariness onward the writing itself goes strange.
  Qud runs two survival timers already and neither of them makes you weaker — thirst stops you
  healing and hunger stops you travelling — so this one follows suit.

  {{y|What it costs you instead is reliability.}} Once you are exhausted, your concentration starts
  slipping: a mental mutation you were counting on gutters out mid-thought and stays down for twenty
  rounds. About five times across the stretch between exhausted and collapsing, and more often the
  closer you get to falling over. It takes a capability away at a moment you did not choose, which is
  a sharper thing than shaving a point off an attribute.

  Time I did not spend in my own body is still time. Dominating a creature used to stop the clock
  entirely — my real body is no longer the player while it is happening, so nothing was accruing on
  either end, and at a high enough rank the window is wide enough to live in. Now any stretch where
  the timer could not see me is billed when I come back, the same way a world-map crossing already
  was.

  {{y|Where you sleep is the point.}} In Joppa, the Stilt, Grit Gate or any settlement you are
  simply safe. A bed is nearly so. Sleep on open ground with something hostile in the zone and it
  finds you more often than not - it wakes, it comes for you, and you get told what it is. Sleep
  somewhere empty and nothing happens, because there is nothing there to happen.

  Sleep gas will not do instead of sleep, and neither will narcolepsy: only lying down on purpose
  rests you.

  Tiredness only speaks up when it is getting worse. Being woken part-way through a sleep used to
  greet you with "your eyes are heavy" — a warning delivered at the moment the rest had helped.

  {{y|You can see how tired you are.}} Tired, weary, exhausted, collapsing — one word on the active
  effects line, next to burdened, in colours that climb the way hunger's do. Until now the only thing
  that ever told you was a message as you crossed each threshold, and messages scroll away.

  {{y|Sleep the whole way through and you dream.}} Mostly of something you actually did, told back
  to you in the voice the sultan histories use - grander than it was, and not always accurate.
  Sometimes of a place you have not been, and you wake knowing where it is. Being woken costs you
  the dream as well as the rest.

  {{y|Off by default}}, and it is the only thing in this mod that adds a system Caves of Qud does
  not have. Turn it on from {{C|you have to sleep}} in the options.

- **Companions use what you give them** (#588).

  Hand a follower a better axe and they work out that it is better, instead of carrying it around
  and going on swinging. Qud has the machinery to re-equip a creature and never once calls it after
  an item changes hands, so until now a companion you armed stayed armed with whatever it started
  with.

  What a creature works out depends on what it could plausibly understand. A tinker reconsiders
  anything, artifacts included — and the reason tinkers are the line is that Qud already drew it: of
  the three creatures vanilla lets scavenge, two are tinkers. Everyone else reconsiders a stick with
  an edge and leaves the guns alone.

  {{y|This is mostly a companion feature.}} Creatures in Qud do not pick things up off the floor —
  a bare handful scavenge at all — so a snapjaw will still walk past a dropped axe. Making them
  notice is a separate question and a bigger one.

  Loadouts creatures already had are untouched. Off by the {{C|creatures use what they gain}}
  option, which takes effect from the next pickup rather than the next restart.

- **Thirteen books** (#741).

  Two of them continue series the game already has. {{y|Frivolous Lives, Vol. II}} carries on the
  Baccata Yewtarch's catalogue of humanoid kings, still dating everything by its own publication and
  still faintly sorry for everyone in it. {{y|Eta and the Earthling, Canto II}} is five more
  questions and five more answers that decline to be answers. Both sit in the general book pool
  beside the volumes they continue.

  The other eleven are stocked by booksellers — not on shelves, not in trinket piles, not in a
  starting pack, though a hamilcrab may turn one up the way it turns up anything. Ten of them take the manner of a writer I love and ask what that
  manner would have produced if it had grown up here instead: a stalker's survey of a ruin that will
  not make sense, a treatise on what a dram of water actually costs and a furious reply to it, an
  antiquarian who should have turned back, a week in the salt pans written by somebody having a bad
  one. No real writer is named or quoted anywhere in them. The prose is mine; only the angle is
  borrowed.

  The eleventh is a list of things a village can no longer remember, including one it is right to
  have lost.

- **Plainer names for legendary relics** (#730).

  A relic's name is built from a grammar of exotic words, and almost every one of them is strange.
  Strangeness only means something when there is something ordinary beside it, so at that density
  it stops reading as significant and starts reading as noise. The vocabulary was never the
  problem — there are hundreds of words, and more would not have helped.

  Twelve name forms built from plain words instead: {{y|the Iron Hood}}, {{y|the Mace of Water}},
  {{y|the Wanderer's Still Mask}}, {{y|Stone-ford}}, beside the sagittal quincunxes. Two of them
  are mixed, pairing a plain word with the relic's own element — {{y|the Bright Brand of the
  Desiccated Spice Root}}.

  Vanilla's own forms are never removed, so a plain name becomes likelier rather than a strange one
  impossible. Twelve is the number that makes it work: it puts the all-strange share at one in ten,
  which is where an odd name reads as odd again.

  Off by the {{C|plainer relic names}} option, which takes effect on restart. Relics that already
  have names keep them.

- **(internal)** `scatter-share` weighs a merge block by the group it merges into (#748).

  `PopulationGroup.MergeFrom` copies a group's `Chance` and `Number` only when the incoming group
  sets them, so a merge writing `<group Name="Creatures">` with neither keeps the target's — and at
  load that multiplier gates this fork's entries exactly as it gates vanilla's. The measure walked
  this fork's XML alone, saw no attributes, and counted the multiplier as one.

  Six merges here inherit one. The largest is `DesertCanyonZoneGlobals-Reachable`, whose group is
  worth 2.375 rolls of its contents: this fork's share there reads 34% rather than 18%. Nothing
  crosses the half ceiling, and two tables move down.

  Vanilla's per-group values are a new `group_multipliers` section in `tools/qud-api.json` — 17
  entries — held as raw strings rather than a computed number, because inheritance is per
  attribute and a group may inherit one while overriding the other.

- **(internal)** `scatter-share` measures a table by tree, so a group's `Chance` gates what is
  inside it (#746).

  The measure swept every `<object>` under a table and discarded the group structure, so a group's
  own `Chance` and `Number` were never applied. `DesertCanyonZoneGlobals-Reachable` shows the error
  running both ways at once: a `Chance="4"` group holding a snapjaw war party was counted as though
  it always fired, while a `Chance="95" Number="1-4"` group worth 2.375 rolls was counted as one.
  The table measured 28.47 objects where it scatters 7.56.

  Over-crediting vanilla is the quiet direction — it shrinks this fork's share of a table, hiding a
  ceiling breach rather than inventing one — which is why it wanted fixing although nothing was
  failing. Eight of the 118 recorded tables move and none crosses the ceiling. `GritGateBookshelf`
  now reads the 50% it always was, rather than 9%.

  A merge block inheriting the multiplier of the group it merges into is still not modelled; that
  needs vanilla's group structure in the snapshot, and is #748.

- **(internal)** `validate_mod.py` guards `<book>`, which no check could reach (#745).

  A book is keyed by `ID` rather than `Name` and takes no `Load` attribute at all, so
  `merge-discipline` — which walks `<object>` and `<population>` and keys on `Name` — never saw
  one. A `<book>` reusing a vanilla ID replaces that text outright, in a file that is valid XML
  and reports nothing anywhere. That went unguarded from the moment this fork shipped its first
  book.

  Three rules now: `book-merge-discipline` for the ID being the fork's own, `book-duplicate-id`
  for a repeat clearing the first book's pages, and `book-reference` for a
  `<part Name="Book" ID>` naming a book that does not exist — which is worse than silent, since
  `BookUI` indexes the dictionary raw and throws when the book is read.


- **Four bookshelves that are about the place they stand in** (#740).

  Only one bookshelf in Qud is about where you are standing. Joppa's holds the two volumes of its
  own history, and they appear nowhere else in the game. Every other named shelf — Grit Gate, the
  hydropon, Yd Freehold, Red Rock — is dressed for its location and stocked from the same general
  pool, so a book you pull off a shelf at Grit Gate is a book you could have found anywhere.

  Each of those four now has one local history of its own, sitting alongside the general pool
  rather than replacing it. Why the Barathrumites planted an orchard under a sealed ruin. What
  happened to the recoming nook the hydropon was built around, and what came up instead. Why the
  Yd Freehold lives in its reef without harvesting it. Who has used the outcrop at Red Rock, and
  why they kept coming back.

  One page each, in the register of the place rather than of a village — Grit Gate is an
  institution, not a farming hamlet, and the four do not sound alike. They are worth nothing, like
  Joppa's, so the Stilt librarian pays for scholarship and not for handing a place its own past
  back.

  How often you find one is sized to how many shelves each location has, so no place hands you the
  same book twice. Generic village shelves are deliberately untouched: villages already write their
  own histories as the world is made.


## [2.11.0] - 2026-08-31

### Added

- **Wary, a Tactics power for spotting hidden threats** (#722).

  Qud already searches for you every time you move, but the roll is your Intelligence against the
  thing's difficulty with no bonus at all — so below a certain Intelligence you **cannot** find a
  mine, ever, no matter how many times you walk past it.

  Wary gives you a second look. Enter a cell and you search again, this time with a +6 bonus,
  covering that cell and the eight around it. It costs 100 in the Tactics tree and wants Agility 15,
  so the melee and missile builds who carry low Intelligence can actually reach it.

  It finds what the game already hides: laid mines, lurking beths, lagroots, young ivory, yonderbrush
  and eels waiting in the water.

  **This shipped once before and did nothing.** The first version listened for the search event
  instead of causing one, and never received it — you could buy the skill and be no better off. That
  version was pulled in 2.10.0. This one adds a search of its own, and says so behind Debug Internals
  so it can never again look like it is working when it is not.

- **(internal)** `check_docs.py` validates file paths written as prose, not only markdown links
  (#735).

  Most paths in the documents are written in backticks rather than as markdown links, and nothing
  looked at them — a reference could rot indefinitely and the gate stayed green. Two had.

  The same change widened both link checks to every document in `docs/`. Eighteen of the
  twenty-seven were invisible to `check_links` as well, including the one holding a rotted
  reference.

- **What lies past sharp** (#723).

  Caves of Qud contains six finished item modifications that nothing in the game can ever apply. Each
  is the second rung of a ladder whose first rung you can already build: sharp has **keen** past it,
  masterwork has **legendary**, serrated has **microserrated**, overloaded has **massively
  overloaded**. They have effects, they have descriptions, and the base mod already knows to call
  itself "keen" instead of "sharp keen" when you get there. Nobody could reach any of it.

  Those four are now buildable — and they cannot be found. No loot carries them, no data disk holds
  them, and you cannot take one apart to learn it, because none exists to take apart. **The first keen
  blade in the world is the one you make.**

  So the knowledge comes from people. Four tinkers each teach one, once you already know the rung
  below it and have reached Tinker II:

  - **Yla Haj** — keen
  - **Barathrum the Old** — legendary
  - **Bep** — microserrated
  - **Q Girl** — massively overloaded

  They will only bring it up if you can actually use it, and each is the only source for theirs.

  The other two finished mods, *overbuilt* and *smart*, are deliberately still unreachable. Neither is
  an upgrade: overbuilt buys +2 AV with −2 DV, a movement penalty and double weight, and smart turns a
  scoped gun into a powered artifact that needs an energy cell, a boot sequence and a HUD before it
  does anything. The tinkering screen has no way to warn you about either, and presenting them beside
  the real upgrades would be a lie.

- **Wounds that rest will not close** (#192). *Off by default.*

  Late Qud is easy partly because damage has no memory — hit points come back for free if you wait,
  so you walk out of every fight as though it never happened.

  With this on, a single blow that takes half your hit points leaves a **wound**, and natural healing
  then stops a quarter short of full until you treat it.

  **Any treatment clears it** — a bandage, salve, an injector, the Physic skills, a regeneration tank
  or a healing meal. Qud already has a whole treatment economy and never makes you use it; this is
  what makes it matter. Untreated, a wound fades on its own, so you are never stranded.

  Damage over time never wounds — poison, bleeding, burning and gas are all exempt — and the
  Regeneration mutation shrinks the wound as it ranks up, gone entirely at rank 10.

  **It adds no enemy hit points.** Nothing hits harder; what changed is that a hard hit stays with
  you.

- **Diseases tell you what is happening while you can still do something** (#581).

  Catching glotrot, ironshank or monochrome vision starts a five-day fight you can win — a Toughness
  save every 1200 turns, two good rolls clear it, and Yuckwheat or honey improve your odds. The game
  never told you any of that was underway.

  Now an onset says when it takes hold, warns you on the fourth of its five days, and tells you when
  you have shaken it off.

  **The fourth-day warning is the point.** The deadline does not care how well you are doing — win
  three saves in a row and the disease still lands on day five, and the last thing vanilla says to
  you is *"You feel a bit better."* One day's warning is enough to go eat yuckwheat.

  And if your first two saves both passed, vanilla said **nothing at all** — not that you had caught
  anything, not that you had fought it off. The good-news messages only unlock once you have already
  failed a roll, so doing well was what made it silent.

  There is a checkbox for it under the mod options.

- **Know the people who follow you** (#592).

  Companions now have a **Look Over** action, next to *Attack Target* and *Come*. It shows their
  level, hit points, AV/DV/MA, attributes, mutations and skills — the numbers the game has always
  had and never showed you. It costs no time, and it works for anyone who follows you, whether they
  shared water, were beguiled, proselytised or tamed.

  And the water ritual now tells you who you are recruiting **before** you pay: the join line reads
  `[250 reputation] [level 14]`.

  That second half matters more than it looks. The price is built from their level minus yours — but
  it bottoms out at 50, so once you are thirteen levels ahead, **every recruit costs the same and
  the price tells you nothing**. Which is most of the late game.

- **Weapons wear out, the way armour already does** (#195).

  Your armour has always worn from use — being hit damages it, and at a quarter of its hitpoints it
  breaks. Your sword never did. Swing it ten thousand times and it is identical to the day you found
  it. This makes both halves of a loadout follow the same rule.

  A weapon spends one point of wear every so many uses — per hit for melee, per shot for missile —
  and breaks after nineteen of them, exactly as armour does. It is **repaired the same ways**: the
  Repair skill, fix-it spray foam, or paying a village tinker in water. It tells you where it is
  along the way — **[worn]** a third of the way through, **[battered]** two thirds — so nothing ever
  breaks without warning.

  **Low-tier weapons wear far faster.** A bronze axe spends wear every 10 hits and breaks after 190,
  a zetachrome one every 50 and breaks after 950 — because a bronze axe is a thing you replace and a
  zetachrome one is a thing you keep. Both are numbers you will actually reach.

  There is a slider for it under the mod options: off, light, normal or heavy.

- **Show someone their own work** (#595).

  Carry something a merchant or artisan made back to the person who made it, and you can now say so.
  They will know their own hand.

  Qud already stamps a maker's mark onto everything a hero merchant stocks, already records whose it
  is, and already prints it in the item's description — *"this dagger bears the mark of Argyve."* What
  nobody ever did was **react** to being shown it. That is the only part I built; everything else was
  already there and I had the issue wrong about it.

  It appears only when you are actually carrying that person's work, and only notable items get
  marked in the first place, so it stays a small moment rather than a fixture.

- **Two more ways to carry things, and one of them helps weak characters most** (#584).

  An **arm satchel**, worn on either forearm — so you can wear two — and a **shoulder bag**, slung
  from one shoulder and steadied with a hand.

  Qud's entire carry-capacity category was three items, and two of the three were back-slot, which is
  why it read as backpacks and nothing else. The mechanism was never restricted to the back; nobody
  had used it anywhere else.

  The shoulder bag is the interesting one. Every existing capacity item gives a **percentage**, which
  scales with Strength and so is worth most to someone already strong. The bag gives a flat 25 pounds
  — about a tenth of an average character's capacity and about a twentieth of a very strong one's, so
  it is the first carry item in the game that helps a weak character more than a strong one. It costs
  a hand to carry, which is a hand not holding a weapon.

  Both have new tile art.

- **(internal)** A resolved carriers helper, and one documented figure that had drifted (#702).

  `BlueprintIndex` gains `carriers` and `carriers_matching`, which answer *which blueprints does this
  reach* through the inheritance chain and through `<mixin>`, rather than by counting declarations.
  Counting declarations was short three times in two days, and the gap held the finding each time.

  It immediately caught a live one. `docs/STYLEGUIDE.md` said 200 blueprints carry a `:Weight` tag;
  the real figure was 189 when that was written, and my own trinket work moved it to 207 without
  anything noticing. The combined number needs the game loaded to recompute, so CI never could — it
  is gone now, and the vanilla half is a snapshot figure checked on every run.

- **Twelve more trinkets, and half of them can't be taken apart** (#704).

  A tuning fork, a horseshoe magnet, a key that opens nothing, a stopped pocket watch, a metronome
  and a pair of spectacles. Then a sprig of dried lavender, a feather, a paper fan, a paper boat, a
  cloth doll and a spool of thread.

  Which of those you can scrap for bits is decided by what it is made of, not by a rule I imposed
  item by item: the machines come apart, and the soft things don't. Metal and glass survive out here
  to be broken down for parts. Paper, cloth, plant and feather only ever survive as themselves.

  That takes the category to twenty-four, and I have made each one rarer to pay for it. Vanilla's
  original six now turn up about three times as often as any single one of mine, so most of what you
  find is still the game you bought and any particular curiosity of mine is a genuine find.

- **Six more trinkets, and each of them does one small useless thing** (#603).

  An hourglass you turn over, a hand mirror you look in, a snow globe you shake, a kaleidoscope you
  look through, a spinning top you spin, and a hand bell you ring. Nobody comes.

  Qud's whole category of ordinary objects from before was six items, and the same six turned up in
  a tier-eight ruin as in a hut outside Joppa. That sameness is right and I have not touched it — a
  folding chair is a folding chair, and grading trinkets by tier would make a joke of the one thing
  that makes them affecting. What was missing is breadth, so these six join all eight trinket tables
  in every tier band, rarer per item than vanilla's own six so that most of what you turn up is
  still the game you bought.

  They are held to the register the existing ones set: one small, ordinary, human thing each, and no
  mechanical payoff whatsoever. Nothing here is secretly useful, nothing is a joke, and all six can
  be taken apart for bits like the five vanilla trinkets that can. New tile art for each, in the
  game's three-colour style.

## [2.10.0] - 2026-08-29

### Fixed

- **Option help text fits the menu again** (#690).

  If an option's description showed up squashed into a narrow box with the ends of the lines off the
  side of the screen, that is because it was written at a scale the menu was never given. Vanilla
  ships four options with help text, 157 to 352 characters each; eleven of the twenty-one here were
  longer, the worst of them over a thousand.

  They are all inside vanilla's range now, wrapped at 76 columns so no line can run off. What went is
  the explaining — why the option exists, what vanilla does instead, the reasoning behind a number.
  Every *"applies to a new character"* and *"takes effect when you restart"* warning survives word for
  word, because those are the sentences that stop a run being wasted. The rest is in the feature
  reference and on the wiki, in more room than a tooltip has.

  This is the second time. [#271](https://github.com/vixygrey/qud-expanded-community-edition/issues/271)
  fixed the same thing when there were eleven options, and it came back as there got to be
  twenty-six — which is why there is now a check instead of an intention.

- **(internal)** `helptext-shape` refuses an option help text that will not fit (#690).

  A source line over 80 characters, or a total over 550. Both numbers are vanilla's: its shortest
  longest-line is 80, its longest text 352.

  I had this backwards first. `Qud.UI.OptionsRow` calls `RTF.FormatToRTF` with `blockWrap` at `-1`,
  so `BlockWrap` never runs — from which I concluded the container wrapped instead, and unwrapped
  every help text onto one line per paragraph. It renders worse, which a `--dev` pass caught before
  the merge and would have caught before the writing. The assembly says what does *not* wrap; it does
  not say what does.

  The convention was never written down and it drifted: ten of twenty-six were hard-wrapped, six of
  them recent. The length cap is a ratchet set just above the longest survivor, so nothing today fails
  and nothing new may be worse.


- **(internal)** `check_docs.py` could not read a hyphenated word number in a wiki claim (#674).

  `WORD_NUMBERS` has held `twenty-one` through `ninety-nine` since the options count crossed twenty,
  but the capture patterns were written `(\w+)` — and `\w` excludes the hyphen. So a page reading
  *"Twenty-four options live in Qud's own options menu"* captured `twenty`, left `four` dangling, and
  reported *"'four' is not a number this script knows"*.

  Three patterns were widened to `([\w-]+)` when the repository's own documents crossed twenty. **The
  wiki patterns did not inherit the fix** — the same shape as the *"second check that did not inherit
  the fix"* entry in `docs/LESSONS.md`. All sixteen are widened now, and the reasoning sits next to the
  compound-number table so the next person writing a claim pattern finds it.


### Removed

- **Five options taken out of the menu** (#690).

  Bearings, creature colour variants, silent trade offers, wider name pools and gendered name
  endings. **All five features stay exactly as they are — only the switches are gone**, so if you
  never touched them nothing about your game changes.

  Every option in this mod is meant to answer one question: would anybody actually turn this off?
  These five could not. None of them changes a number, a difficulty, a drop or anything you choose at
  character creation, and none takes anything away that you might want back — they are flavour, and
  the menu was charging you a line to read past for each of them.

  > **If you had one of the five switched off, it is on again.** There is nowhere left to store that
  > preference. Coloured animals will reappear, your generated names will use the wider syllable
  > pools, and creatures with nothing to trade will stop offering. Nothing is broken by this and
  > nothing needs a new character — but it is a change you did not ask for, and I would rather say so
  > here than let you find it.

  Twenty-one options remain, and every one of them changes something you would notice.


### Added

- **Fired arrows can be picked back up** (#643).

  An arrow you shoot sometimes survives and lands where it hit, so you can pick it up again. Archery
  stops being pure consumption without anyone having to build a crafting system for it.

  Caves of Qud already knows how to leave a projectile on the floor — it does it for anything else
  that lands. Arrows were the exception, and only because they are built as unreal objects that are
  deleted the instant they arrive. Nothing about the world says an arrow you shot into a wall stops
  being an arrow.

  **Not all of them come back**, and how often depends on what the arrow is made of. That is the
  game's own material ladder rather than a number I picked: a wooden arrow survives about a fifth of
  the time, a zetachrome one about nine times in ten. So the arrows worth keeping are the ones you
  keep, and ammunition stays a resource.

  **Arrows that carry something never come back** — explosive, cryo, gas, honey, flare. The payload is
  spent, and what is left is not an arrow any more. That is decided by what the arrow *is* rather than
  by a list, so anything added later is covered without anybody remembering it.

  If you have Caves of Qud's own *autoget primitive ammo* switched on, exploring collects them for
  you. That half already existed; there was simply never anything on the floor to find.

  New option, **on by default**, read live: turning it off makes fired arrows vanish again, from the
  next shot.

- **Charmed merchants still expect paying** (#563).

  Beguile, proselytize or mask a shopkeep and their whole shop became free. Caves of Qud treats
  anyone following you as a companion, and a companion's things are shared — which is right for
  someone who joined you over a long game and wrong for a trader you enchanted forty seconds ago.
  Nothing in any of the charms ever asked whether the person now following you keeps a shop.

  A charmed merchant still likes you, still shows you everything they have, and now still charges for
  it. **The charm is not weakened anywhere else**: they follow you, they fight for you, and the things
  they would never normally sell are still on the shelf — you just buy them. A merchant who genuinely
  joined you is unaffected, because the test is the charm rather than the following.

  This is not a rule about who owns the stock, which is what I originally wanted. Caves of Qud does
  mark each item as shop stock or personal effects, but it clears the mark the instant anything
  changes hands — including for free — so there is nothing left to read by the time it would matter.
  What is left is the simpler statement: charm buys goodwill, not goods.

  New option, **on by default**, read live: turning it off gives you the free shop back, from the next
  merchant you talk to.

- **Caravan guards carry a bow** (#591).

  A flying character could strip a dromad caravan at no risk. Not because caravans are undefended —
  they are guarded, by two to four level-30 escorts with 165 hit points each — but because **nothing
  in one could reach the sky.** Both of the game's equipment builders draw only from melee weapons,
  armour and junk, at every tier, so a caravan guard could not be armed against a flyer under any
  roll.

  Guards now carry a compound bow and fifteen to twenty-five steel arrows. **Flight is untouched.**
  It is a real mutation with real costs and it should stay strong; the problem was never that flying
  works, it was that a caravan crossing the salt dunes for a living had no answer to something in the
  air, which the world would not permit. Qud's skies contain things that eat camelfolk.

  A compound bow rather than a short bow, and the reason is worth stating because it is the whole
  difference between a fix and a gesture: **a short bow fires every arrow in the game at the same
  penetration, which is none.** Only the compound bow lets an archer's Strength count, and a guard's
  Strength is where the force actually comes from. Steel arrows because that is exactly as much as a
  guard of this strength can put behind a shot; a better arrowhead would be weight it cannot use.

  The trader still runs. Only the escort fights, which is what an escort is for.

  **This does not reach caravans that already exist in your save** — a caravan is built once, and the
  guards it was built with are the guards it keeps. New ones carry bows.

  Killing a caravan now yields the bows and arrows as well, which is a little more income from an
  encounter this change makes harder rather than easier. That is how Caves of Qud's own armed escorts
  work — a hindren scout and a snapjaw hunter both drop what they carry — and it seemed wrong to
  invent an exception here.


- **Name an item after a pride flag** (#577).

  When you name an item — after a kill, a level, a quest, a water ritual — the colour picker now
  offers **24 LGBTQIA+ flags** alongside Caves of Qud's own patterns. Fourteen orientation flags and
  ten gender ones, each drawn as stripes across the name.

  Pure data: one new file, no code. It also means removing the mod is harmless — an item named this
  way keeps its name and simply loses the colour.

  **Some black stripes do not appear, and that is deliberate rather than an oversight.** Caves of Qud
  draws on a very dark ground, and its darkest ink is barely lighter than that ground, so a black band
  has almost nothing to show against. Ten of these flags have one. The alternative was swapping in a
  visible brown or grey, which makes a *wrong* flag rather than an incomplete one — an asexual flag
  reading grey-white-purple is still recognisably itself, and one with a brown stripe is not. Every
  other stripe on every flag renders.

  No plain rainbow, because Caves of Qud already has one and it is already in this picker. Adding
  mine would have quietly repainted rainboweave, flash of neon and a few passages of writing that use
  the game's version.

  No transfeminine or transmasculine either. In seventeen colours both come out identical to the
  transgender flag, and three names for one swatch helps nobody. I would rather leave them out than
  ship them wrong.

  Recipes cannot be coloured yet — the game gives a recipe no colour to hold, and no name of your own
  to put one on.

- **(internal)** `shader-collision` refuses a colour name that vanilla already owns, or that this mod
  declares twice (#577).

  `Colors.xml` has no `Load` attribute and no concept of one — the loader updates a name it knows and
  registers one it does not, so merge is the only behaviour there is. That makes declaring a vanilla
  name a silent redefinition of it, reaching every place the game already used it, and
  `merge-discipline` cannot see it because there is no `Load` to look for. #577 was filed proposing
  exactly that row for `rainbow`; this check fails on it at commit time.

  `tools/qud-api.json` gains a `shader_names` section so the check runs in CI, which has no game.


- **Gather a liquid into one container** (#561).

  A `gather liquid` action on any container holding a liquid, which pulls every dram of exactly that
  liquid out of the rest of your inventory and into that one, least full first. Two waterskins with a
  few drams of honey each become one skin of honey and one skin free for something else.

  **It only ever pours a liquid into a container already holding the same liquid**, so it cannot turn
  fresh water into salty. That is not a safeguard bolted on: the test compares the mixtures and
  ignores how much is in each, and merging two identical mixtures is arithmetically incapable of
  changing either. Nothing else is offered, and no compatible-mixture merging is either.

  **What it buys you is an empty container, and I want to be honest that it is not more than that.**
  It does not make you richer — Caves of Qud already adds up every dram of water you carry when you
  pay for something, whichever skin it is in — and it does not shorten your inventory, because liquid
  containers have never stacked. What a partly full skin does cost you is the skin: three drams of
  water in it and it cannot pick up honey, cider or convalessence at all. Emptying it is what unlocks
  it.

  **`fill` could already do the transfer.** What it will not do is check. It offers every container
  you own, and picking one holding something else asks whether to empty it first and then mixes the
  two. This offers only exact matches, never asks for a dram count, and does all of them in one press.

  Costs **one turn**, however many containers it drains — deliberately stricter than `fill`, `pour`
  and `drain`, which are all free. Draining four containers at once is doing more than one fill, and a
  turn is the cheapest price the game has.

  Containers belonging to somebody else ask once for the whole sweep rather than once each. Sealed
  containers, containers in stasis, anything set to auto-collect something else and anything that
  refills itself are all left alone — a self-filling jug is a tap, not a stash. Acid still eats its
  container and neutron flux still detonates, exactly as they do on an ordinary fill, and either one
  ends the sweep rather than being carried through.

  **No option**, deliberately. It changes no number and no loot table, it takes nothing away — `fill`
  still does everything it did — and it reaches nothing `fill` could not. There is nothing to refuse
  but a menu entry that does the same job with fewer keystrokes.


## [2.9.0] - 2026-08-29

### Fixed

- **Creature variants doubled how many animals a zone had** (#613).

  Reported in play: a croc and a silt croc standing on the same tile in a salt marsh. Every coat was
  rolling *beside* the ordinary animal instead of taking part of its chance, so a salt marsh expected
  two crocs where Caves of Qud expects one, and a quarter of them got both. **30 animals were
  affected** — dogs, goats, boars, baboons, beetles, dragonflies and the rest — at a middling 1.6x
  and a worst of 2.11x.

  Every coat now splits its parent's share. A salt marsh gets one croc's worth of croc and a coin
  decides which croc it is, which is what these were always meant to be: a change of colour, not more
  animals. Twenty-seven of the thirty land on vanilla's figure exactly; the other three are within
  4.4%, because a chance has to be a whole number.

  **Turning creature variants off now leaves the ordinary animal in place** rather than removing the
  entry, so the world holds the same number of animals either way. Before this, switching them off
  would have taken those animals out of the world instead of repainting them.

  The stacking itself is Caves of Qud's, not this mod's — a guard against placing two creatures in
  one cell hands back the cell it was avoiding. It is recorded in `docs/LESSONS.md` and left alone;
  what this mod controls is how often placement reaches it.

- **(internal)** `variant-density` checks that a coat splits its parent's share of a table rather
  than adding a second roll (#613).

  `scatter-share` could not have caught this and never could: it measures this fork's share of a
  whole table against a ceiling of half, and the salt marsh is about a tenth mine while holding twice
  vanilla's crocs, because 260 watervine and brinestalk drown one reptile. Share is a property of a
  table; density is a property of a blueprint, and they want different checks.

### Added

- **Issachari names stop running out** (#632).

  An Issachari is one hyphenated phrase - {{Flays-upon-the-Sun}}, {{Chokes-in-Quicksalt}} - drawn
  from 7 verbs, 5 prepositions and 8 nouns. That is 280 names: the whole name repeats at around
  twenty people, and every individual slot at three or four. All three pools now widen together, to
  10, 10 and 12, which is 1,200 names and a repeat at about forty.

  Three of the four new nouns come from the Issachari themselves rather than from me. **Brine** and
  **the-Red-and-White** are things they say - *"the brine air will cure your lungs to jerky"* and
  *"Be respectful of the red-and-white and we will get along"* - and **Mirage** is from their banner,
  platinum stitch on a field of salt white, read by mirage-trained eyes.

  This is the opposite conclusion to the one the Qudish pools got, from the same arithmetic. Qudish
  has ~93,500 names, so exact repeats are not what you notice and the middle pool was deliberately
  left alone; Issachari has 280, so the whole name repeats and every slot with it. Both files say so.

  Covered by the same **wider name pools** option that governs Qudish.

- **(internal)** `naming-option-coverage` is keyed by namestyle, and the naming harness watches
  Issachari (#632).

  The check compared the namestyle's name against the literal `"Qudish"`, so the moment a second
  namestyle arrived it would have stopped covering the file while still passing - which is the exact
  failure it exists to prevent, aimed at itself. It now holds every namestyle in both directions, and
  reports an array that has entries no namestyle adds. The harness's watch list gained Issachari for
  the same reason: a fragment that cleared those pools rather than adding to them would have shown
  nothing at all.

- **Everyday objects vary in colour** (#608).

  Clay pots, baskets, benches, bedrolls, robes, sandals, spectacles and ten other ordinary things
  each get a colour of their own, instead of every one being identical to every other.

  Caves of Qud already does this and simply stops early - it ships the machinery and uses it on
  vases, pitchers, jugs and 23 pieces of furniture, so a vase is never quite the same vase twice.

  Each palette is read from the object's own description rather than chosen freehand. A clay pot is
  *Svy mud fired in a marsh oven*, so it comes out in fired reds and ochres; a bedroll is *goat wool
  fastened with canvas ties*, so it stays in undyed naturals. Only the chiliad basket gets the full
  range, because its description is the only one that says *dyed*.

  **Nothing whose colour tells you something is touched.** Weapons and armour keep their material
  colours, because that is how you read a tier at a glance. Neither does anything whose colour comes
  from the liquid inside it - a gourd's body varies, and the part of it that shows what it holds
  does not.

  Idea prompted by [Colors of Qud [Fork]](https://steamcommunity.com/sharedfiles/filedetails/?id=3287770072)
  on the Steam Workshop, which fills exactly this gap. Every palette here is my own, written from
  the descriptions; none of that mod's files were read.

- **Gates swing shut behind you** (#631).

  Caves of Qud never closes anything behind you, so a village gate you walk through stays swinging
  for the rest of the run. A brinestalk gate is described as set across an *iron-latched rail*, and a
  latch is a thing that catches - so now it does.

  **Gates only.** Interior doors are left alone, because leaving one open to shoot through is a real
  tactical choice. A gate costs you nothing when shut: you can already see through it, shoot through
  it and fly over it, which is exactly why it is the right place to draw the line.

  This keeps nothing in and nothing out. Anything that can walk opens a door by walking into it,
  livestock included - and that is also why your followers can never be stranded behind one. What
  changes is that a village looks like somebody lives in it.

- **Creatures with nothing to trade no longer offer to trade** (#571).

  Asking a giant dragonfly to trade was a valid choice right up until you made it, at which point the
  game told you it had nothing to trade. The information existed before you asked.

  An animal's bite is natural equipment and cannot be traded, so its side of the screen is empty even
  though it technically carries something - which is why "does it have an inventory" was never the
  right question. The check is Caves of Qud's own: if nothing they carry would appear on the trade
  screen, the option is not offered.

  **Companions are unaffected.** Trading with someone who follows you is free and opens even when
  they carry nothing, because that is how you hand them things.

- **An artifact you marked important is not offered to Argyve** (#570).

  Marking something important is supposed to mean *don't let me lose this*. When Argyve asks for a
  knickknack, Caves of Qud offers you every artifact you are carrying - your marked, one-of-a-kind
  relic sitting in the picker next to a bit of scrap - and there is no warning at all. Not a weak
  confirmation: none. I followed the whole chain to be sure.

  Now the ones you marked are simply not listed. If they are all you have, you are told why and told
  how to undo it, rather than handed an empty menu.

  Things the **game** marked important - quest items, storied relics - are still offered, and now ask
  you to confirm first, which Caves of Qud does not do here at all. That is what keeps the quest
  unblockable: nothing of yours is ever withheld without saying so.

  Selling is untouched and cannot be reached - the trade screens are UI singletons that no XML names,
  so no mod can change what they list. That is the wider half of the problem and it stays open.

- **You can ask a creature its name** (#572).

  Most of the people in Qud already have names. There was never a way to ask. Now conversations with
  a creature that has no name yet carry the question, and they answer — a snapjaw with a snapjaw
  name, an Issachari raider with an Issachari one, drawn from their own culture, faction and region
  the way a village elder's is.

  The question comes out differently each time, from a pool of eleven. Six are Caves of Qud's own
  wording and five are mine. What they say back is entirely the game's.

  **Caves of Qud wrote this and left it switched off.** The choice, the reply, the naming, and an
  opt-out for authors who want a particular creature to stay silent are all finished and shipped;
  one line hides the lot, and it tests a setting that appears nowhere in the game's data. This adds
  its own question rather than flipping that setting, because reaching it would have cost the Joppa
  home base its option — the two mechanisms turn out to be mutually exclusive, and `docs/FEATURES.md`
  §26.2 records why.

  **You cannot ask a dragonfly.** The question only appears where somebody is actually speaking -
  worked out from the conversation itself rather than from a list, by checking whether anything is
  left once the emotes are taken out. So animals, insects and plants are silent, and so are the
  people who deliberately do not speak: Sparafucile, Oboroqoru, Warden 1-FF, the apple farmer's
  daughter. Birds can be asked, because Caves of Qud gives them sentences.

  **Asking means you can no longer rename them.** The game refuses to rename anyone who already has
  a name, so a creature that has told you who it is cannot be given one by you afterwards. That is
  deliberate: asking who someone is and deciding who they are are different acts, and now you choose
  which one you are doing. Turn the option off if you would rather keep naming your companions.

- **Data disks now come on a curve instead of at random** (#582).

  Every data disk in Caves of Qud is a uniform draw from the whole recipe list — a tier-8 blueprint is
  exactly as likely from the first merchant in Joppa as from anything in the deep ruins. Now an early
  table leans early-tier and a late one leans late.

  **A powerful disk early is still possible, and now it is a story.** Roughly one disk in seventy from
  an early table is top-tier, rather than one in eight.

  **The curve is Freehold's, not mine.** Caves of Qud already contains 33 targeted disk blueprints —
  one per tinker tier, plus build, mod and category variants — and not one of them is used by
  anything in the game. This spends what was already built. Disks already in a save keep whatever
  recipe they rolled.

  **Disk specialists are the exception, and stay broad.** A disk merchant stocks every tier, because
  that is the reason to walk to one; the legendary version leans to the top of the ladder, as do the
  Barathrumites, who are the tinkers. All 34 tables are covered.

- **Tail**, a 1-point physical mutation, on by default (#590).

  A tail. It gives you 1 DV, and when something would knock you down — a shield slam, a rocket jump,
  slipping on slime — you get an Agility save to keep your feet. So it helps more the nimbler you
  are, which is the only way a one-point mutation can grow, since none of them gain ranks.

  **It does not attack and it holds nothing.** There is no tail weapon and no tail slot to fill; it
  is a defensive mutation and a cosmetic one. An axe can cut it off, and losing it takes the dodge
  with it until it grows back.

  **Choose which tail at character creation** — fox, wolf, cat, rat or lizard. That is pure
  flavour: they behave identically, and the choice is there because deciding what you are is worth
  something on its own.

- **Keen Smell**, a 3-point physical mutation, on by default (#593).

  You detect creatures around you by scent, at roughly twice the range of Heightened Hearing — but a
  wall stops a smell dead, and a closed door, deep water or anything blocking your view cuts it down.
  Better in open country than in a ruin, which is the opposite of how hearing behaves.

  **This is Caves of Qud's own mutation, not mine.** Freehold built Heightened Smell completely — the
  effect, the art, the terrain rules — gave it to a few animals, and never added it to the list you
  pick from. This adds it. What is mine is the price: vanilla's own figure is 2, but nothing in the
  game has ever been able to select it, so that number was never tested against a player. Twice the
  range of a 2-point mutation is worth 3.

  It stays out of the pool of mutations that random creatures roll, exactly as vanilla has it — the
  mutation only does anything for the player, so a creature holding one gains nothing.

- **Fangs**, a new 3-point physical mutation, on by default (#589).

  Long teeth on your face that bite alongside whatever you are wielding — about one round in five,
  which means they never compete with a better weapon — and draw blood when they land. They do not
  take your face slot, so a gas mask or night-vision goggles still fit. Damage is a flat `1d6`,
  which is vanilla's own figure for fangs; what grows with rank is the bleeding.

  Bleeding is normally bought. Bloodletter costs 150 skill points and needs Agility 17, and short
  blades otherwise only bleed on a critical hit. Fangs give a smaller share of that for a mutation
  point instead, and the two stack if you have both.

  Fangs or a beak, not both — they would grow on the same place. Fangs and horns is fine. They turn
  up on randomly generated creatures too, so expect the occasional fanged snapjaw.

  This is the first mutation this fork has ever declared, and the first of an animal-traits set
  (#471). Turning the new **anthro mutations** option off hides it at character creation and keeps
  it off creatures; mutations are read while a character is being made, so that applies to a **new**
  character.

- Woodsprogs outside the Naphtaali tribe are named like woodsprogs (#454).

  A woodsprog in the tribe was always named correctly. A woodsprog anywhere else — a Kyakukya
  villager, a jungle forager — drew a Qudish human name instead. The register was never missing:
  vanilla's `Naphtaali` namestyle already holds it, and the Naphtaali *are* woodsprogs. What was
  missing is the scope that reaches a woodsprog outside the faction, which is the third scope
  vanilla's own snapjaws carry and its Naphtaali do not.

  So this adds one scope and no syllables of mine. Tribe members are named exactly as they were —
  the faction scope still wins outright for them — and nothing else in the game moves.

- **(internal)** `bit-letters` reports a letter in a `TinkerItem Bits` cost (#560).

  A digit names a *level* and the game draws which bit of that level per world; a letter pins one
  specific bit. Both are legal and they mean different things, and a letter goes wrong two ways that
  nothing announces. `BitType.TranslateBit` remaps the scrap characters on the way to the screen, so
  XML `B` is scrap metal but displays as `<C>` while the wiki's `<B>` is scrap crystal — a blueprint
  written from the wiki's alphabet asks for the wrong material in silence. And case is three levels
  of cost: `b` is pure alloy, `B` is scrap metal.

  Letters are not forbidden, because pinning one bit is a real requirement that vanilla has of its
  own — `Shotgun Shell` is `Bits="C"` deliberately. It costs an entry in `BIT_LETTER_EXEMPT` with
  the reason. That map ships empty; every live record here already uses digits. An unrecognised
  character is reported separately, and an exemption does not silence that one.

### Changed

- **Trash Divining thins out as a zone is picked over** (#605).

  The skill says a 5% chance per pile and that reads as a trickle. Pile density made it a salary:
  the catacombs lay down 80 to 100 piles in one zone, so rifling a single catacombs zone handed you
  **four or five secrets** — and a secret sells for 50 reputation at a water ritual, so it was a
  reputation faucet as much as a knowledge one.

  **The 5% is untouched and the first twenty piles in a zone still pay it in full.** After that the
  same zone drops to 3%, then 2%, then 1%, and never lower. A catacombs zone now pays around two
  secrets instead of four or five. Thin zones are left alone — a rustwell has too few piles to reach
  the second band and pays exactly what it always did.

  This was never an exploit and is not treated as one. A player who spent 150 points and reached
  Intelligence 21 bought this skill, so the headline number does not move and the skill never stops
  working; what falls away is the fiftieth pile in a room that has already told you everything.

  The count is kept on the zone, so walking out and back does not reset it, and it keeps counting
  while the option is off — turning the option off in a rich zone and on again will not hand back a
  fresh 5%.

  Rifling still tells you about anywhere in the world rather than about where you are standing.
  That is a wider problem with four separate sources and is tracked in #635.

- **(internal)** `check_docs.py` understands hyphenated word numbers (#605).

  The mod crossed twenty options, and three claims are written out in prose — "Twenty-one options,
  in Qud's own options menu". The table stopped at twenty and the capture groups stopped at `\w`, so
  "Twenty-one" resolved to `one` and the check failed pointing at the wrong thing. The compounds are
  generated from tens and units rather than listed; the bare units stay out deliberately, because a
  group that resolved "one" would turn ordinary prose into a claim.

## [2.8.0] - 2026-08-28

### Added

- **Mind's Compass tells you where in the parasang you are standing** (#470).

  A parasang is a 3×3 block of zones and the game never says which of the nine you are in. You work
  it out by walking to an edge and watching which way the world map scrolls, which is navigation by
  trial and error rather than by skill. Now it is said on arrival, under the line where the game
  already tells you the zone and the time: *The northeast of this parasang.*

  It comes with **Mind's Compass**, which is free with **Wayfaring** rather than bought separately —
  the same idea as regaining your bearings when lost, one scale down, and it costs nothing a
  wayfarer has not already paid for. The information was always there: every zone ID carries its own
  position inside its parasang, and vanilla does the identical lookup itself to label the choices
  when you descend from the world map. Nothing surfaced it while you were standing in the zone.

  **Nothing is said while you are lost**, which is the one time you should not know — and the time
  vanilla drops you at a random one of the nine. Nothing on the world map, or in a world that has
  none, or inside a vehicle. Stairs are silent too: a staircase does not move you within the
  parasang, so it has nothing new to say.

  On by default. It grants no power, only a number the game had already written down.

  Played and confirmed on 2026-08-28, and the message's placement was what the playtest sent back —
  see below.

- **(internal)** Three figures in `docs/STYLEGUIDE.md` §1.0c recounted (#470).

  The section says `Skills.xml` touches **six** vanilla skills and quotes two counts as evidence for
  how the loader merges. All three were exact when written against six skills (#87). Adding Short
  Blade for its Finesse power (#146) made it seven and left `23 powers omit Class=` correct only by
  coincidence — a power carrying `Class=` does not count toward it — while quietly taking the
  deletion count from 18 to 25, since the mod names one of Short Blade's seven.

  Wayfaring makes it eight and moves both again: **24** and **34**, each recounted against vanilla's
  own `Skills.xml`. `check_docs.py` recounts neither, which is why these drifted where the option
  and blueprint counts beside them could not.

- **Caves grow bruisemoss** (#547).

  It never sees light and has no use for the green that would gather it, so it comes up the colour
  of a week-old bruise. Press a thumb into a patch and the damp stands in the print for a while
  afterward.

  It appears in caves under any parasang that is not a named biome, at every depth from 11 down to
  49 — which is most of the caves you will ever dig into. Like the ruins pair it gives you nothing
  and is only there to be looked at.

  It shares the ruins moss's tile at a different colour, which is what the game does with its own
  plants: one tile carries witchwood, the n-Ary tree, glitchwood and the icosahedar, and another
  carries four aloes. Magenta because a cave already grows dreadroot, young ivory and brightshroom,
  and the moss had to be none of them.

- **Ruins and baroque ruins have something growing in them** (#173).

  Two new plants, and neither gives you anything: **slabmoss**, a blue-green crust that takes the
  damp out of a floor slab and stops at the rain line where a roof has gone, and **pallvine**, which
  roots where a wall meets its floor and hangs from there in long dry ropes. No yield, no
  ingredient, no stat — a ruin should simply look like a thousand years have passed in it.

  They arrive in clumps rather than scattered evenly, because that is how the game already does
  this. Vanilla's brightshroom and grave moss patches are built from a common arm and a rare dense
  one, and every entry grows outward from wherever its first tile landed; these follow the same
  shape. Five ruins in six now carry one plant or the other, and about one in thirty has gone
  properly under — the frequency is taken from the crypts, where grave moss is that common because
  being mossy is part of what a crypt is.

  Slabmoss is teal on purpose. Everything already growing in a ruin is green — swarmshade, ziv
  bough, star palm, starapple — and a fourth green would have read as more canopy instead of
  something on the floor.

  No new art: slabmoss borrows grave moss's tiles and pallvine borrows yuckwheat's. The atlas holds
  better vines and roots than either, but they belong to North Sheva's sacred plants and are set by
  hand in the Star Orchid Temple, so using them would have made a named thing into wallpaper.

- **Three more harvestable plants — rimeburr, shadetooth and broadglove** (#177, #540).

  Counting distinct species rather than blueprints, `Hills`, `DesertCanyon` and `Jungle` each offered
  the same three things: starapple, its Barathrumite variant, and witchwood. **Two species, and the
  same two, across the biomes a player crosses most.** Wave one gave Mountains, Saltmarsh and
  BananaGrove something of their own; these three had nothing distinctive at all.

  | | Hills | DesertCanyon | Jungle |
  |---|---|---|---|
  | plant | rimeburr | shadetooth | broadglove |
  | yield | head | pad | cap |
  | preserve | pickled | cured | pressed |
  | cooking effect | `tastyMinor` | `thirst` | `medicinal` |

  Each effect is one vanilla already ships and uses once or twice, so none adds to the vocabulary —
  the charter rule 2 line wave one held. Everything is data, so no rule 5 budget either.

  The shadetooth is a water-holding succulent that grows only in the canyon wall's shade, and it
  ripens ochre to cyan — the ripe colour is the ingredient's own argument, since the preserve is what
  carries `thirst`. The broadglove is a shelf fungus rather than the broadleaf first drafted: its
  tile is Brightshroom's, and a plant should match the tile it borrows rather than the other way
  round.

  Ripeness is derived, not chosen. `Chance × Number ÷ StartRipeChance` puts them at **0.73, 0.63 and
  0.92** ripe plants per zone, inside vanilla's dense band of 0.6–1.0 — `docs/FEATURES.md` §18.3 has
  the full table. Scatter shares stay well under half: `JungleZoneGlobals` 4.5%,
  `DesertCanyonZoneGlobals` 10.8%, `HillsZoneGlobals` 17.3%.

  Each carries its biome's `_Plants` tag so a village can be built and described with it, and each
  preserve carries `_Ingredients` so it can be a village's signature dish. The fibre stags take a
  named vanilla neighbour rather than a guess, and only where the inherited default is wrong: Primal
  Grass's set for the burr, Fracti's for the succulent, and Fungus's single `Plank="mass"` for the
  shelf fungus.

  **No mod option**, which #177 left undecided. Wave one shipped without one and nothing asked; and
  unlike the creature variants these are not cosmetic — they feed cooking, village dishes and village
  descriptions, so an option that removed them would remove content other systems reference.

- **A village's signature dish can now be made with the local preserved plant** (#489).

  Qud gives each village a signature dish built from one to three ingredients, 80% of them drawn
  from its region's ingredient pool. Dried cragwort, salted brinereed and candied sweetfrond were
  not in those pools, so a mountain village could describe a dish of bear, boar and goat jerky and
  never the plant growing outside it.

  24 of vanilla's 40 preserved cooking ingredients are in one of these pools, and the split is the
  argument for joining: every regional plant preserve is in — starapple preserves, fermented
  yondercane, dried lah petals — while what stays out is mostly manufactured or placeless, like the
  food cube and the crusty loaf. Raw snacks stay out on both sides; only what has been put up for
  keeping is a village's stock.

  The banana grove is the one worth naming. Its ingredient pool held **exactly one** thing, and a
  dish that wants two distinct ingredients retries 25 times before giving up and repeating itself.
  Adding candied sweetfrond makes this fork half of that pool, which is more than I would normally
  take — but a pool of one cannot serve a mechanic that asks for two, so this is closer to repairing
  it than to crowding it.

  §18.7 had recorded the opposite decision, on the reasoning that an ingredient placed *only* in
  that pool would turn up in villages rather than in the wild. That is still true of the plants, and
  they still reach the world by explicit entry. It was never true of their preserves, which have no
  population entry at all and are made rather than found — so the tag adds a route instead of
  replacing one.

- **Villages in the mountains, saltmarsh and banana grove can now be built and described with the
  local plant** (#177).

  Qud names a village's walls after a plant of its region — *"thatch of cragwort, bound together
  with tar and twine of cragwort thatch"* — choosing from a per-biome pool. The three harvestable
  plants were not in that pool, so they could only ever be picked by already standing in the zone
  the village was built in.

  They carry the tag now, following brinestalk: wild flora joins the plant pool and not the
  farmable one, which is for crops villagers actually grow.

- **Three harvestable plants**, one each for the mountains, the saltmarsh and the banana grove
  (#177) — cragwort, brinereed and sweetfrond. Each can be harvested for a snack, and each snack
  preserves into a cooking ingredient.

  Vanilla is thinner here than it looks: no biome in the game reaches more than three harvestable
  plants, most reach one or two, and the starapple tree is in nearly all of them. These three go to
  the biomes whose cooking-ingredient pools are emptiest — the banana grove had exactly one.

  Their fiber, thatch and plank yields are set rather than inherited. Every plant inherits
  vanilla's `Plant` defaults — strip, bark, plank — and left alone that means bark off a reed and
  planks off mountain scrub. Vanilla overrides them on 17 of its own plants, so these three take a
  named neighbour each: the brinereed takes brinestalk's, its own marsh's own reed.

  They introduce no new cooking effects. `regenLowtier`, `plantMinor` and `starch` are all effects
  vanilla plants already carry, so what the kitchen gains is ingredients rather than behaviour. How
  often a plant is ripe is derived from vanilla's own band rather than picked: all three sit between
  0.7 and 1.5 ripe plants a zone, beside dreadroot at 0.8 and urberry at 1.0.

### Changed

- **(internal)** `placement-hint` now sees entries inside a patch table this fork writes (#547).

  It read a merge block's direct children only, and a block that pulls a patch table has none — so
  all three of this fork's patch tables were unguarded at once. The same gap `scatter-share` had
  before #544, in a second check that did not inherit the fix.

- **(internal)** `placement-hint` now sees tables reached through a `<table>` reference (#173).

  The check shipped in #544 read only the tables a zone template names directly, so the ruins
  vegetation this fork merges into — one level below the table the template names — was skipped in
  silence. The game passes a placement hint down through nesting; the citation now does too, and
  covers 69 tables where it covered 10.

- **(internal)** Two checks added ahead of the overgrowth work in #173 (#544).

  `scatter-share` now follows a `<table>` reference into a table this fork defines, so a sub-table
  written in vanilla's own patch idiom is measured rather than scoring zero. It still refuses to
  follow one into vanilla's tables, and resolution is opt-in so the other side of every ratio is
  unchanged.

  `name-collision` reports two scattered blueprints that read as the same thing. Colour markup is
  stripped before comparing, so `{{g|ivy}}` and `{{y|ivy}}` count as the collision they are.

- **Creature variants are a fifth of two generic creature pools instead of two thirds** (#524).

  The 26 animal and reptile variants each reach the world by an explicit entry I placed in the biome
  they belong to. They *also* join `DynamicInheritsTable:BaseAnimal` and `:BaseReptile` simply by
  inheriting from a vanilla parent, and those pools are biome-blind — a marsh dog could walk out in a
  flower field, and so could a jungle boar.

  It showed most in `FlowerFieldsPopulation`, whose creature group is `pickone` where
  `PopulationItem.Weight` defaults to 1. The fourteen named creatures there specify `Chance`, not
  `Weight`, so they weigh 1 apiece against that pool's 25 — **half of every creature pick went to a
  pool I held two thirds of**, in the low-tier zones where a new character spends its first hours.

  The weight was not spread across 26 animals. Seven held most of it, because `Dog` and `Bat` carry
  `Role="Minion"` — a ×4.0 multiplier, the largest there is — while `Goat` and `Boar` carry `Brute`
  at ×0.25. I chose a parent, not a number.

  | | before | after |
  |---|---:|---:|
  | `BaseAnimal` Tier0/1 | 69.6% | **18.6%** |
  | `BaseAnimal` Tier2 | 55.7% | **11.2%** |
  | `BaseReptile` Tier0/1 | 66.6% | **16.6%** |
  | `BaseReptile` Tier2 | 65.1% | **15.7%** |

  Done with vanilla's own `:Weight` tag — 78 of them, `Value="0.1"`, tiers 0–2 of the two pools. It
  is a multiplier applied inside one pool, so the deliberate entries and the inherited
  `DynamicObjectsTable:<Biome>_Creatures` village route are both untouched; membership does not
  change and no variant is harder to find where I put it. Vanilla uses the same tag 81 times across
  28 pools — `Holographic Banana Tree` is 0.2 of `DynamicObjectsTable:BananaGrove_Plants`. 0.1 lands
  each pool just under its own headcount share, so the variants stop being over-represented rather
  than being suppressed.

- **A new preview image, and it is my own work rather than Mura's logo** (#500).

  The old one was Mura's Caves of Qud Expanded logo with two marks composited on top — a green
  `- CE` after "Expanded" and `& VixyGrey` under "by TLR". It was also 504×382, where Freehold
  recommend a square 512×512, so the mod manager was letterboxing it.

  The new image is original: a stratigraphic cross-section built entirely from Caves of Qud's own
  eighteen fixed colours, laid out on the game's own 16×24 character cell, with scan lines and a
  vignette pitched to be noticed on a second look rather than a first. Both names sit in it, in the
  same face and weight. **Charter rule 3 obliges credit, not the reuse of someone else's artwork**,
  and a fork wearing its own identity while naming its origin honours that better than a borrowed
  logo with a suffix bolted on.

  `tools/preview-base.png` — Mura's logo — is deleted, since nothing composites onto it any more,
  and `COPYING.md` no longer lists the preview under Mura's grant. `tools/build_preview.sh` becomes
  `tools/build_preview.py`, which reads no image at all and so cannot repeat the double-composite
  trap `docs/LESSONS.md` records. It writes a 128px proof beside the output, because 128 is the size
  the mod manager actually displays and the design has to survive it.

  The reasoning behind the design is kept in `docs/PREVIEW_DESIGN.md` rather than discarded, on the
  same argument the old script made for itself: the alternative is that the next person to change it
  guesses at the intent.

- **The Joppa home base option now takes effect on restart, and applies to Joppa as it is first
  generated** (#498).

  It used to be lopsided: turning it off removed the building the next time you entered Joppa, and
  turning it back on never rebuilt it — a limitation the helptext had to spell out. It is
  symmetrical now. Joppa is built once from whatever loaded, and a save keeps what it was built
  with, in both directions. The option carries `Restart="true"`, so the options screen says so
  itself.

  A character who already has the building keeps it, and one made without it will not gain it later.

### Fixed

- **Saves written by unreleased builds shed objects out of thawed zones** (#554).

  Found while playtesting #470, and not caused by it. The game reported two errors loading a zone;
  the previous session's log had 48, on `Desert Rifle`, `Musket`, `Humanoid` and `Hypertractor`, all
  of them `Recovered from game object deserialization error` — vanilla catching a misaligned read
  and dropping the object.

  #497 moved three classes onto the `IScribed` bases, which changed what they write: a class with no
  serialisable fields wrote nothing before and writes a field count of zero now. `Vixy_SaveFormat`
  told the two apart by comparing the mod version in the save against the last version that wrote the
  old format — and could not, because `v2.7.0` was tagged eight hours before #497 landed. A save
  recording `2.7.0` was written either by the release, which wrote nothing, or by an unreleased build,
  which wrote a block. So the reader left a byte unconsumed, and an under-read is not contained:
  `IPart.Load` repositions to the end of the block only from inside its `catch`, so reading too little
  throws nothing and desynchronises every object after it.

  **Fixed by deleting the question rather than answering it.** All three classes hold no serialisable
  state, so both halves are now suppressed — `Write` writes nothing, `Read` reads nothing — giving one
  on-disk shape in every version. A boundary that does not exist cannot be got wrong, and
  `Vixy_SaveFormat` goes with it. #497 is not undone: the classes stay on the `IScribed` bases, which
  is the part that is expensive to do later, and when one gains a field both overrides come out.

  **Subscribers were never affected.** Released 2.7.0 predates #497 and its saves genuinely wrote
  nothing. Saves already written by unreleased builds cannot be repaired — the stray byte is
  indistinguishable from the next component's data, which is the same reason the guard could not
  work.

- **(internal)** The wiki reads a parasang's X from the wrong side, and `WIKI.md` now says so
  (#550).

  [Intro - Zones and Worlds](https://wiki.cavesofqud.com/wiki/Modding:Intro_-_Zones_and_Worlds) puts
  the top-left parasang at (0, 0) and the bottom-right at (79, 24), then two sentences later reads
  `JoppaWorld.53.3.1.1.10` as "the 53rd tile from the right". `WorldFactory.BuildZoneNameMap` walks
  parasang X from 0 to 79 in map order, so it is counted from the left and the example is off by
  `79 - 53 = 26` parasangs on a map eighty wide.

  Found while investigating #470, which leaned on that page for everything else it says — the
  parasang definition, the `World.wX.wY.X.Y.Z` format, zone coordinates running 0–2, `Z = 10` as the
  surface. All of that is correct.

  Unlike the three rows already in that section, this is the page contradicting itself rather than
  the game moving on, so the section's opening line now allows for both. It also means the
  correction needs no version note and is a one-word fix upstream.

- **(internal)** Two documents still described the Joppa removal system that #498 deleted (#549).

  `docs/DESIGN_options.md` recorded the removal correctly and the other two did not follow.
  `docs/FEATURES.md` §13 still routed the Joppa option through `Raven_JoppaBuildingSystem`, giving
  as the reason the very thing #498 disproved — that a map patch cannot be gated on an option. And
  `docs/CHARTER.md` rule 5 still listed a `[Serializable]` `IGameSystem` among the things this mod's
  C# does, in the paragraph where the rule states its own ceiling. That one mattered more: a ceiling
  is meant to be an exact description of what the C# may do, and one naming a capability the mod no
  longer has is a ceiling nobody can check a diff against.

  Three further spots had drifted the same way and are fixed with them. Both documents still
  carried the **old, lopsided contract** — the Joppa building "cannot be rebuilt once removed" —
  which #498 replaced with a symmetrical one; `mod/Core/Options.xml`'s helptext had already been
  updated and the prose had not. Rule 5's example of an irreversible edit is now the Chip Interface
  slot, which a body built without one never gains. And rule 6 flatly asserted that **reading an
  option requires C#**, which is the claim #498 disproved; it now says *acting on* one usually does,
  and names the directory gate as the exception.

  Rule 5 also now records that the ceiling **came down**, which had not happened before and is worth
  a sentence: the replacement for that system was not a smaller version of it but the discovery that
  `manifest.json` already gated directories on an option, which is what "prefer XML to C#" is for.

- **Two of the same plant could grow in one tile in three biomes** (#542).

  Brinereed in the saltmarsh, broadglove in the jungle and sweetfrond in the banana grove could each
  be placed twice in the same cell. The event log said so out loud — *"You pass by a brinereed and a
  brinereed"* — which reads as a wording bug and is really a placement one.

  Whether the game refuses to stack a scattered object is decided **per biome**, in a vanilla file
  this fork does not edit. `ZoneTemplates.xml` may carry a placement hint alongside the table it
  names, and only a hinted placement runs the check that a cell does not already hold that
  blueprint. Hills, Mountains and DesertCanyon carry one; Jungle, SaltMarsh and BananaGrove do not.
  So three of the six harvestable plants were protected and three were not, and nothing in this
  fork's own files said which.

  All six entries now carry the hint themselves. Three needed it; on the other three it changes
  nothing, and it puts the reason where the entry is instead of in someone else's file. A new
  `placement-hint` check fails the build if a scattered plant is ever written without one again.

- **18 items now have a drop rate somebody chose** (#482, #527).

  The six extended vinereapers, the eleven vibro weapons and the bio-scanner mask had no entry in
  any population table.
  They reached a player only through the generic dynamic pools, which means their rarity was whatever
  fell out of being one blueprint among hundreds in a tier slice. Vanilla places every one of its own
  weapons in these families explicitly, and this fork agreed with that exactly once —
  `Raven_Bronze Vinereaper` — while the other seventeen were added to complete the tier ladders and
  never got one.

  Vanilla files them by kind rather than by family, and so does this now:

  | | goes to | weight | matching |
  |---|---|---:|---|
  | 11 vibro weapons, all tier 5 | `Artifact 5R` | 10 | `Vibro Blade`, exactly |
  | 6 vinereapers, tiers 3–8 | `Melee Weapons 3C`–`8C` | 10 | `Steel Vinereaper` in `Melee Weapons 2C` |

  **The weight is vanilla's and 20 would have been wrong.** `Melee Weapons 2C` grades its entries
  20 / 10 / 5 — main weapons at 20, the vinereaper and the dagger at 10, kukri and utility knife at
  5. A vinereaper is a niche harvesting weapon that vanilla prices at half a main weapon, and copying
  20 from this fork's other entries would have doubled a rarity Freehold chose. It also keeps the
  enforced ceiling honest: at 20 the first three tables land at exactly 50.0%, legal but with no
  headroom ever after. At 10 the worst is 46.7%, and `docs/STYLEGUIDE.md` §3.2.1 already says which
  way to resolve that — *the fix is a lower per-item weight, never less content*.

  Putting the vibro line in `Artifact 5R` also makes it village tinker stock rather than a generic
  pool roll (`docs/DESIGN_balance.md` §5.3).

  `Raven_Bio Scanner Mask` joins them in `Artifact 5R` at Weight 10. It wears on the Face but is
  `AV="0" DV="0"` — a gadget rather than armour — and `VISAGE` is vanilla's precedent for a face
  artifact living in the Artifact tables. `Armor 5R` was the other candidate and is the wrong one
  twice over: the item is not armour, and at Weight 20 that table would have gone to 52.9%, past the
  ceiling.

  `Raven_Bronze Vinereaper` stays at Weight 13, matching the bronze block it sits in rather than
  vanilla's ratio — it is shipped and internally consistent, and only the newly priced six follow
  Freehold's number.

  The new `tinker-only` check keeps it that way. `check_reachability` accepts three routes and all
  eighteen passed on the third: they carry `TinkerItem`, so they were obtainable and the check was
  satisfied. But tinkering is a thing a player *does*, not a rate at which a thing *appears*, and
  nothing was asking the difference.

- **Two energy cells are as rare in the world as their price says they are** (#493, #535).

  `Raven_Dark Matter Cell` is Weight **1** in `Artifact 8R` where vanilla's `Antimatter Cell` is
  **5** — five times rarer, deliberately, because it holds 500,000 charge at 70 lb against
  antimatter's 200,000 and is valued 1200 against 125. `Raven_Solar Cell Nexus` sits at Weight 1 in
  `Ammo 7` and `8` beside the nuclear cell's 5.

  In `DynamicObjectsTable:EnergyCells` both were at **exact parity** with those peers, because
  nothing had ever set a weight there. And that pool is not a loot table — it is how artifacts get
  loaded:

  ```xml
  <part Name="EnergyCellSocket" SlottedType="#Solar Cell,@DynamicObjectsTable:EnergyCells:Tier{zonetier}" />
  ```

  So in late-game zones roughly half the cells that came pre-slotted in an artifact were the rarest
  artifact I ship.

  | slice | cell | before | after | its peer, after |
  |---|---|---:|---:|---:|
  | `Tier8` | Dark Matter | 45.2% | **15.0%** | Antimatter 75.1% |
  | `Tier7` | Solar Nexus | 43.0% | **13.9%** | Nuclear 69.3% |
  | `Tier6-8` | both | 19.1% | **5.5%** | peer 27.5% |

  Twelve `:Weight="0.2"` tags, on every tiered slice where a cell holds at least 1% of the weight.
  The untiered slice is left alone and cannot be otherwise: it takes the flat fabricator at base 1,
  where `ceil(1 × 0.2)` is 1 — and it needs nothing, because all thirteen cells sit at 7.7% there by
  design.

  Writing the first `:Weight` tag on a *tagged* pool also exposed a gap in the report: `collect`
  matched every tag starting with `DynamicObjectsTable:` and so filed seven modifier tags as pools
  of their own. `check_reachability` has skipped `:Weight`, `:Number` and `:Builder` since #171 —
  the knowledge existed in one tool and not in the other.

- **(internal)** `no-commit-to-main` runs at commit time only, so a release tag can be pushed (#469).

  The hook tests the branch you are standing on. At `pre-commit` that is the right question — it is
  the one check CI cannot run, because it refuses the commit before it exists. But
  `default_install_hook_types` installs `pre-push` as well and the hook set no `stages:`, so it ran
  there too, where the same question is wrong: it refused `git push origin refs/tags/v2.7.0` from
  `main`, which is exactly where a release tag belongs.

  Tagging 2.7.0 needed `--no-verify` to get through, and that is the real cost — the workaround for a
  guard that is wrong once is the same keystroke as the workaround for a guard that is right.

  Pushes are the server's business. The `main protection` ruleset requires a pull request, forbids
  deletion and non-fast-forward, demands linear history and passing checks, and lists **no bypass
  actors**. Worth knowing while checking that: it is a *ruleset*, so
  `GET /branches/main/protection` answers `404 Branch not protected` and the repo looks unguarded if
  you ask the classic way.

- **(internal)** A zone is never tier 0, so `{zonetier}` cannot ask for a Tier0 slice (#537).

  #533 fixed the offset forms and deliberately kept a bare `{zonetier}` at tiers 0–8, on the grounds
  that `ResolveTier` returns `zoneGenerationContextTier` unconstrained. That is true of `ResolveTier`
  and false of the value it reads: `Zone.NewTier` ends `if (_NewTier < 1) _NewTier = 1`, the static
  default is 1, `GetZoneTier` returns 1 on every early exit, and no zone template or `Worlds.xml`
  entry declares `Tier="0"`.

  Fifteen more phantom slices leave the ledger, including the largest figure in the whole report:

  | slice | reported |
  |---|---:|
  | `BaseShield:Tier0` | **93.3%** |
  | `BaseAxe:Tier0` | 65.7% |
  | `BaseLongBlade:Tier0` | 50.0% |
  | `Item:Tier0` | 40.2% |

  **`{ownertier}` is the one form that keeps tier 0**, because it is a *blueprint's* tier rather than
  a zone's, and blueprint tiers really are 0 — this fork's whole bronze line is. The game uses it
  three times, on `Armor`, `MeleeWeapon` and `EnergyCells`, and those are exactly the pools that keep
  a Tier0 slice. The inherited count moves 201 → 185.

  Found by Grey asking whether vanilla shipping no tier-0 armour might be deliberate. It is not —
  bronze is tier 0 on this fork's own documented ladder, the twelve bronze weapons match vanilla's
  twelve tier-0 weapons exactly, and per item the bronze armour sits at the same weight as vanilla's
  `Clay Pot`. Chasing the question is what turned up the zone floor.

  Third correction to the same expander in one day. Each of #520, #533 and this one was only findable
  once the one before it was fixed, and a test asserting the wrong range had to be corrected each
  time.

- **(internal)** Six reported slices were ones the game never rolls (#533).

  `ResolveTier` handles the `{zonetier}` forms itself rather than leaving them to
  `ReplaceVariables`, and every **offset** goes through `Tier.Constrain`, which is
  `Math.Min(Math.Max(Tier, 1), 8)` — floor 1, not 0. So `Tier{zonetier+1}` can never resolve to
  `Tier0`, and neither can `Tier{zonetier-2}`; the game ships test cases saying exactly that. Both
  slice expanders here treated any `{...}` as tiers 0–8.

  That put six phantom slices in the reports, four of them in *each pool at its worst slice*:

  | slice | reported | actually |
  |---|---:|---|
  | `BaseGlove:Tier0` | 84.3% | never rolled |
  | `BaseBoot:Tier0` | 75.7% | never rolled |
  | `Headwear:Tier0` | 71.5% | never rolled |
  | `BaseCloak:Tier0` | 70.0% | never rolled |
  | `BaseArmor:Tier0` | 44.6% | never rolled |
  | `Guns:Tier0` | 1% | never rolled |

  `BaseGlove` drops from 84.3% to **48.9%** at its real worst slice, and the inherited count moves
  205 → 201. A bare `{zonetier}` and `{ownertier}` keep tier 0, because neither is constrained.

  Found by Grey asking whether vanilla shipping no tier-0 headwear might be deliberate. It is —
  vanilla ships 19 tier-0 items and **not one is armour** — but the answer that mattered was that
  nothing asks for `Headwear:Tier0` in the first place.

- **(internal)** The tagged-pool route is measured, not just listed (#531).

  `tools/dynamic-pools.json` pinned which of my blueprints each `DynamicObjectsTable:` pool reaches
  and nothing else, so **how much of what comes out of one is mine had never been computed** — on
  the route `docs/STYLEGUIDE.md` §3.3 actively recommends. `inherits-share` has done this for the
  inherited route since #494; the tagged route had no equivalent.

  It needed one. `DynamicObjectsTable:Mountains_Creatures` is **79.3%** mine, `Flowerfields_Creatures`
  66.7%, `Headwear:Tier0` 71.5% and `Items:Tier0` 51.3% — none of it visible before.

  The check has to know which of two fabricators built the pool, because they weigh differently. A
  `:TierN` request goes through `FabricateMultitierDynamicPopulationTable` at base 10⁸; a tierless
  one through `FabricateDynamicObjectsTable` at base **1**, with the tier deltas never applying at
  all. Seven of the pools this fork is in are tiered and the rest flat, and **every biome pool is
  built at runtime** as `"DynamicObjectsTable:" + region + "_Creatures"` in `VillageBase` and its
  siblings — so those requests cannot be found by reading the data and are listed instead.

  Two traps went into the scan. A `<tag>` declares membership while a `<table>` consumes, so
  counting tags reported every pool as live — including `MeleeWeapons`, which **nothing in the game
  draws from**, and which holds 112 of my blueprints through a tag vanilla puts on `MeleeWeapon`
  itself. And the daggers pool's only consumer is
  `<inventoryobject Blueprint="@DynamicObjectsTable:Daggers:Tier2" />`, which a scan reading `Name=`
  alone never sees.

  §3.2.1 gains what I had wrong: `:Weight` works on **both** fabricators. On the flat path only one
  case rounds away — a no-Role blueprint given a fraction — while a value above 1 raises it, a
  fraction cuts a Role-boosted one, and **`Value="0"` excludes it from that pool alone**, which is
  the only per-pool exclusion there is.

- **(internal)** The inherited-pool report ranks slices instead of judging them against a line
  (#481, #529).

  The 50% ceiling on that route was reported and never enforced, and it does not survive looking at
  the distribution it was drawn across: 201 slices running smoothly from 0% to 93% with no break
  anywhere. `BaseLongBlade` is **21 of 42 members** — headcount parity to the blueprint — so where
  its members weigh alike the share is exactly **50.00000%**, with four sibling slices inside a
  fiftieth of a point. Whether those were in breach came down to the fourth decimal.

  A pool's share is not one number either. `BaseGlove` runs 2.9% to 84.3% across its own nine slices,
  `BaseShield` 30.7% to 93.4% — so "N of 205 over half" counted tier requests while reading as a
  count of breaches.

  What prints now is the ten most dominated slices and **every pool at its own worst slice**, so no
  pool hides behind its good tiers. Nothing becomes less strict: drift against
  `tools/inherited-pools.json` is what fails a commit, and it is untouched.

  §3.2.1's third-route section is rewritten with it. Six of its claims had gone stale and two were
  wrong mechanically rather than numerically — it said a `:Weight` tag would apply *"if any
  existed"* (200 blueprints carry one), and that `ExcludeFromDynamicEncounters` was the only lever
  and offered no partial exclusion (`:Weight` is exactly that, and `Value="0"` excludes from one
  slice). `check_docs` could not see any of it, because they were claims rather than registered
  figures.

- **(internal)** The pool report follows `<mixin>`, which is a second inheritance mechanism (#526).

  `BlueprintIndex.chain()` walked `Inherits=` and nothing else. A blueprint can also pull tags,
  parts and stats from another blueprint with `<mixin Name="…" />`, and **143 vanilla blueprints are
  kept out of every dynamic pool by an `ExcludeFromDynamicEncounters` that arrives that way** — 66
  golems through `BaseVehicleGolem`, 60 Chiliad creatures through `BaseChiliadCreatureStats`, plus
  `BaseHindrenClue` and `BaseAnimatedObject`.

  Counting all 143 as live pool members inflated vanilla's side everywhere, so this fork's share was
  understated across **43 of 201 slices**: `BaseAnimal` Tier0/1 by 13 points, `Creature` Tier0/1 from
  21.4% to **38.1%**. The fork writes no mixins, so the error ran in one direction only.

  `chain()` keeps its `Inherits=`-only meaning, because that is what `GameObjectBlueprint.DescendsFrom`
  walks and **a mixin does not confer pool membership** — following one there would have put 66
  golems in the `Creature` pool. The new `lookup_chain(name, kind)` is what every tag, part, stat and
  property lookup uses, in the loader's precedence order: own, ordinary mixins, the `Inherits` chain,
  then `Load="Fill"` mixins. `Include`, `Exclude` and `Priority` are all honoured.

  It also corrects the creature census, which is quoted in `docs/FEATURES.md` and in `Ammo.xml`:
  **897 creature blueprints becomes 904**. The seven are the furniture golems — `Bed Golem`,
  `Chair Golem`, `Door Golem`, `Infrastructure Golem`, `Iron Maiden Golem`, `Table Golem`,
  `Wall Golem` — which are creatures by way of `<mixin Name="Creature" Exclude="part" />` on
  `BaseAnimatedObject`, vanilla's only use of that filter. `creature-rust-dead` moves 721 → 728 with
  it; the shares those sentences turn on do not change.

  Found by a playtest, not by a check: the reported figure was 18% and the game rolled 33%.

- **(internal)** `Role` is declared as a tag, the way vanilla declares it (#522).

  Thirteen blueprints — the twelve Zetachrome items and the reinforced suspension — carried
  `<property Name="Role" Value="Rare" />`. Vanilla declares Role as a `<tag>` 349 times and as a
  property never, and its own tier-8 weapons are the exact precedent: `Long Sword8` is
  `<tag Name="Tier" Value="8" />` followed by `<tag Name="Role" Value="Rare" />`, which is now
  character-for-character what these thirteen are.

  Behaviour is identical and I checked rather than assumed it. `Property.Rebase(Blueprint.Props)`
  puts a blueprint property onto the live object, and both `GetPropertyOrTag` and
  `GetTagOrStringProperty` fall through to the blueprint's tags when no property is there — so
  every consumer returns `Rare` before and after. No ancestor of the thirteen declares a competing
  Role, so the two lookup orders never disagreed. The proof is that
  `report_dynamic_tables.py --check` passes against an unchanged `tools/inherited-pools.json`: not
  one weight moved.

  The new `role-form` check keeps it that way. Nothing depends on it — the report reads both stores
  since #520 — but the divergence is what made that report wrong, and a convention worth having is
  worth enforcing. `tools/qud-api.json` gains `"Role": "tag"`, read out of the game's own data,
  which `snapshot-coverage` demanded the moment the tag appeared.

  Also corrects 349 from 352 in the #520 entry, `docs/LESSONS.md` and the report's own docstring. I
  had counted with `grep -c`, and three of vanilla's Role tags sit inside commented-out blueprints.

- **(internal)** The inherited-pool report reads Tier and Role the way the game does (#520).

  `report_dynamic_tables.py` weights every member of a `DynamicInheritsTable:` pool by its tier
  distance and its role. It read both from tags, and the game reads neither from a tag alone.

  `GameObjectBlueprint.Tier` uses the `Tier` tag when there is one and otherwise
  `GetStat("Level").BaseValue / 5 + 1`, clamped to 1–8. **Vanilla creatures carry `Level` and no
  `Tier` tag**, so 593 eligible blueprints were dropped — 46 of them my own creature variants — and
  `BaseAnimal`, `BaseReptile` and `Humanoid` were reported as pools that did not exist. I hold 52%
  of `BaseAnimal` Tier1 and 57% of `BaseReptile` Tier2. A blueprint with neither tag nor `Level` is
  not excluded either: its delta misses `TierDeltaWeights` and it joins at weight 1, or at full
  weight in the untiered table, which 731 blueprints do.

  The weighting also asks `Tags.TryGetValue("Role", …) || Props.TryGetValue("Role", …)`. Vanilla
  declares Role as a tag 349 times and as a property never; this fork does the exact opposite,
  thirteen times, on the Zetachrome items. Reading only tags weighted those thirteen ×100 too
  heavily and put `BaseShield` Tier8 at 96.7% when it is 69.5%.

  169 slices across 16 pools becomes **205 across 22**. The count over the reported 50% ceiling
  barely moves, 50 to 49, but the list is materially different — which matters, because #481 is
  being decided on it. `BlueprintIndex` gains `prop_value`, `has_stat` and `stat_attr` to make the
  three-way resolution readable, and `tools/inherited-pools.json` is re-pinned.

- **(internal)** The 18 subtype gear tables carry this fork's prefix (#499).

  `StartingGear_Force Psionic` and its seventeen siblings sat in vanilla's namespace. A population
  table name is a lookup key, and the Compatibility page lists it among the identifiers a mod must
  prefix — vanilla ships 25 `StartingGear_*` tables of its own, and following that naming meant
  sitting inside it.

  Safe to rename, which was the open question when this was filed. `QudSubtypeModule` reads a
  subtype's `Gear` once, on `BOOTEVENT_BOOTPLAYEROBJECT`, rolls the table and adds the resulting
  blueprints to the new character. **The table name is never written to a save**, and `SubtypeEntry`
  is rebuilt from XML every boot, so §1.1's frozen-identifier rule does not reach it.

  Two things follow from the prefix. `validate_mod.py` loses its `NEW_TABLE_PREFIXES` exemption,
  which existed only so these unprefixed tables would not read as replacing vanilla records — with
  the prefix, a bare `StartingGear_*` in this mod is now correctly a `merge-discipline` finding.
  And the new `subtype-gear` check verifies each subtype's `Gear` names a table this fork defines,
  which nothing did before: a typo would have surfaced as `Unknown gear population table` at
  someone else's character creation, from two files eighteen names apart.

  `StartingGear_Common` stays bare throughout. It is vanilla's, every subtype here draws from it,
  and the check leaves unprefixed names alone because nothing in the repository lists vanilla's
  tables — verifying one would need the game.

- **(internal)** `mod/` is laid out for conditional loading, and the Joppa removal system is gone
  (#498).

  `manifest.json` now declares a `Directories` array: `Core`, `ObjectBlueprints`, `Scripting` and
  `Textures` always load, and `Optional/JoppaBuilding` loads only while its option is `Yes`. The ten
  loose XML files moved into `Core/`, because **no entry may name `mod/` itself** — the loader keeps
  only one of two overlapping paths, so a root entry would load the gated directory unconditionally.

  That deletes `Raven_JoppaBuildingSystem` and its mutator, 253 lines that removed 89 objects from
  76 cells after the fact, plus the hand-maintained table of those objects and the
  validator check that existed only to keep the table in step with the map. Data describing other data, and a
  check guarding the copy, both stop existing rather than being maintained.

  The premise they rested on was false. `docs/DESIGN_options.md` §4.5 said a map merge "cannot be
  gated on an option — it happens as data loads, long before any option is read". Option defaults are
  populated *before* directory initialisation, which is why the file declaring an option must have
  `Option` in its name; `ModInfo.InitializeFiles` loads only the directories that passed their
  conditions, and `MapFile.Reset` takes maps from that file list rather than scanning. A `.rpm` gates
  like anything else.

  **The restructure was done for what comes next rather than for this one feature.** A second
  presence-shaped option now costs a directory instead of a system, and `Directories` entries also
  carry `Dependencies`, `Exclusions`, `Version` and `Build` — so version-conditional content, or a
  shim for another mod, no longer needs a sub-mod or any C# at all.

  **The move also broke the map patch, and nothing static caught it.** `MapFile.CacheFile` keys a
  map by its `ID` attribute, or — when there is none — by its path relative to the mod root, which
  `MapFile.GetKey` truncates at the first dot. So `mod/Joppa.rpm` keyed as `joppa` and patched
  vanilla's Joppa; from `Optional/JoppaBuilding/` it keyed as `optional_joppabuilding_joppa` and
  patched nothing. The file loaded, the game logged the directory, every check passed, and Joppa
  simply had no building in it — in *both* option states. A playtest found it. `<Map ID="Joppa.rpm">`
  makes the key independent of the path, and the new `map-id` check requires an `ID` on every `.rpm`
  so the next move cannot repeat it.

  `Naming.xml`'s typo allowance had to move with the file — in **both** places that hold it,
  `.typos.toml` and the pre-commit hook's own `exclude`, because pre-commit passes changed files as
  explicit arguments and an explicitly named file overrides the config. The hook's comment already
  warned that anything skipped has to be skipped in both places or it is skipped in neither, and I
  updated one of them and was caught by the other.

  Moving the files also caught something the move itself was not looking for: `table-share`,
  `scatter-share`, `implant-table-cost` and `snapshot-coverage` each read `PopulationTables.xml`
  through `if not path.is_file(): return`, so all four went quiet while `validate_mod.py` still
  reported OK. The paths are constants now, and the new `layout` check says once and loudly when a
  file the checks read is not where they expect it.

- **(internal)** A check that the mod's declared load paths reach every file it ships (#498).

  Groundwork, landing before the restructure it exists to guard. Declaring a `Directories` array in
  `manifest.json` changes loading from "everything under `mod/`" to "these paths only", and **a path
  that does not match loads nothing, with no error** — the same silence as an unread tag, in the one
  place where it costs a whole feature rather than one blueprint.

  `directory-coverage` asks three things, all without the game because both sides are in the
  repository. That every declared path exists **matching case exactly**, since macOS accepts a
  wrong-case path and Linux does not, so `Path.exists()` cannot be the test. That no declared path
  contains another, because the game keeps only one of two overlapping entries and the loser's
  conditions go with it — which is what would make a gated subdirectory load unconditionally. And
  that every content file is reachable, since one that is not still ships to subscribers.

  Proved against a working prototype of the intended layout rather than only against synthetic
  fixtures: the layout comes back clean, a path misspelled in case gives exactly one finding, a root
  entry is caught as swallowing its sibling, and a forgotten directory reports each orphaned file.

- **(internal)** Three drifted section numbers fixed, and a check so they cannot drift again
  (#496, #503).

  `docs/DESIGN_balance.md` carried **two section 4.5s**, so `§4.5` had no correct reading, and its
  §5.9 sat above §5.8. `docs/FEATURES.md` had §15.5 above §15.4, so following the numbering led to
  the wrong section. None changes a claim; all three make a cross-reference ambiguous, and
  `check_sections` could not see it because the number a citation names still resolved to *a*
  heading.

  Fixed the way that keeps every citation valid: DESIGN_balance's two are a **reorder** (its seven
  references to §5.8 and §5.9 are untouched) and a renumber of the duplicate to §4.6 (nothing cites
  it). FEATURES' pair is a **renumber**, because "What this does not touch" is a closing section and
  belongs last — its three references to §15.5 now name §15.4.

  The new `heading-order` check holds it. It deliberately does not flag the letter suffix these
  documents already use for a section inserted later — §17.3a, §18.4b — since that convention is
  what makes renumbering unnecessary in the first place.

  Also the one non-ASCII character in the mod's shipped XML, a `÷` in an `Ammo.xml` comment. Qud
  reads XML as code page 437 regardless of the declaration, and there is no way to say otherwise
  outside the `lang-experimental` branch, so mod XML stays ASCII.

- **(internal)** Five findings from the wiki audit moved out of the issue tracker and into the
  documents (#492, #495, #501, #504, #505).

  **`:Weight` is not universally inert** (#492). `LESSONS` said the base weight in
  `FabricateDynamicObjectsTable` is "exactly `1u` for every entry". There is a third multiplier in
  the same loop that I never traced, and unlike the tier delta it is reachable: `Role`. `Common` and
  `Minion` multiply the base to **4**, where a `:Weight` of 0.5 gives 2 rather than 1. `Dog` is
  `Role="Minion"` and is one of my own variant parents, so the curve I called inert would have
  worked on exactly the coats I was writing it for. 63 vanilla blueprints carry a `Role` the
  multiplier table has never heard of.

  **`<stag>` reaches two consumers, and §4.0b named only one** (#501). The section knew about
  `DynamicSemanticTable`; it did not say that the same key is what `XRL.Language.Semantics` reads for
  grammar, nor — the part that matters to a contributor — that an `<stag>` added for a wall
  description can enrol the object in a spawn pool five zone builders draw from. It also said this
  fork writes 29 tag names; it writes **41**. Checking a category against a list is the wrong
  instinct anyway: 24 are named in vanilla's XML, six more sites build the name at runtime, and the
  live set has no fixed size.

  **A pool with no members can still be live** (#505), which is the mirror of the trap this fork
  keeps hitting. `Coda_<region>_Plants` is rolled on every coda village and **no vanilla blueprint
  declares into it** — an extension point with zero members and a fallback behind it. Set beside
  `<Biome>_Creatures`, which 123 blueprints declare into and nothing rolls for zones, the pair says
  membership count and liveness are independent and both have to be asked.

  **The `*delete` correction is now complete** (#504). Freehold's wiki says the tag is broken both
  with `Load="Merge"` and on inherited tags. Neither holds: `Bake` skips a `*delete` tag while
  flattening, and `ObjectBlueprintXMLChildNode.Merge` copies the incoming `Value` over the target's
  own, so the merged tag is skipped like any other.

  **And one entry is stale rather than wrong** (#495). The warning that `core.hooksPath` silently
  disables per-repo hooks stands — but my own global directory gained a full delegator set, so
  `pre-push` is reached here now. Recorded as fixed rather than deleted, because the mechanism is
  real and a contributor's setup may still be the shape it describes.

- **(internal)** A stale API snapshot now fails where it is noticed, instead of blocking whoever
  commits next (#507).

  `tools/qud-api.json`'s mod-scoped sections take their **keys** from this mod and their **values**
  from the game: `tag_forms` records how vanilla writes each tag name *this fork uses*,
  `table_weights` and `scatter_quantities` cover the tables *this fork merges into*. So adding a tag
  or merging into a new table leaves the snapshot incomplete — and the only thing that noticed was a
  digest comparison that needs Caves of Qud installed.

  CI has no game, so it skipped, and a stale snapshot merged green. It surfaced later on whichever
  machine had the install, as a failure blocking a commit that had not caused it. That happened
  twice in one day: #486 left it stale for the next person, and #489 was blocked by its own change
  with a message reading `installed game gives <digest>` when the game had not moved at all.

  The new `snapshot-coverage` check needs no game, because both sides are already in the
  repository — the mod's XML and the committed snapshot. It asks only whether the snapshot has an
  *opinion* about each tag name and merged table, never what the opinion is; deciding that still
  needs the install, and `tag-form` still does it.

  That required recording absences as well as values, since "not in `tag_forms`" meant both "vanilla
  has nothing to say about this name" and "the snapshot has never seen it". `tag_forms_absent` now
  separates the two: `both` where vanilla writes a name two ways and so has no opinion — `Fiber`,
  `Furniture`, `LightSource`, `Scrap` — and `absent` where vanilla never writes it, which is
  `Finesse` and `Vixy_CreatureVariant`. `absent_tables` had already made the same bargain for
  tables, and its own note says why: an absence is a citation worth as much as a figure.

- **(internal)** `docs/STYLEGUIDE.md` §3.3 stopped saying that Qud's biome pools have no consumer,
  and stopped miscounting how many pools do (#490, #491).

  #485 corrected the claim that `DynamicObjectsTable:<Biome>_Creatures` is read by nothing. It
  reached LESSONS, FEATURES twice and two mod files, and missed the styleguide — which is the
  normative document, and which FEATURES §17.2 cites as its authority. So the correction pointed at
  the page still carrying the error.

  Three figures in the same two paragraphs were wrong, all of them counted the same way:

  | claim | actually |
  |---|---|
  | "nothing consumes them" | rolled by village generation, `VillageBase.cs:167` |
  | "only nineteen of seventy-nine are consumed anywhere" | **seventy-six of seventy-nine** — nineteen is how many appear in the game's *XML* |
  | "191 vanilla creature blueprints" | **123**, across sixteen pools (201 tag instances) |

  §3.3 now also records the two searches that made the wrong answer look proven, because both are
  the normal way to check and neither was careless. Grepping the data cannot find a consumer that
  builds its table name by string concatenation. And `population:findblueprint` enumerates tables
  *already fabricated*, so running it in a session with no village in it showed no `*_Creatures`
  table and absence read as proof — where `population:generate` names the table and fabricates it on
  demand.

  Three pools genuinely are rolled by nothing: `HumanoidCorpses`, `MeleeWeapons` and `Mushrooms`.
  The `MeleeWeapons` one matters, because §3.3 told contributors there is no vanilla pool for melee
  families. There is one; it is simply dormant, and might not stay that way.

- **(internal)** Three script classes moved onto the `IScribed*` bases, while it was still free
  (#497).

  Freehold's [serialization page](https://wiki.cavesofqud.com/wiki/Modding:Serialization_(Saving/Loading))
  recommends `IScribedPart`, `IScribedEffect` and `IScribedSystem` strongly for new code: they write
  a component's fields by name, which is what lets a field be added or removed later without
  breaking saves that already exist. It also warns that converting a class afterwards is "possible,
  but nontrivial". `Vixy_AmmoPayload`, `Vixy_Burden` and `Vixy_Burdened` had no fields yet, so
  converting them now cost nothing and the next field is free.

  It is not quite a one-line change. `IComponent.Write` writes each serializable field unnamed, so a
  component with none writes **nothing**; `WriteNamedFields` writes a count first, so the same
  component writes a **zero**. One byte, but a real format change — and `IPart.Load` only
  repositions the stream inside its error handler, so a reader expecting a count where none was
  written would desynchronise the save rather than merely lose a field. Each of the three now reads
  nothing from a save written by 2.7.0 or earlier, which is exactly what the old format meant.

  `Raven_JoppaBuildingSystem` is deliberately left alone: #498 may remove it outright, and migrating
  something that might not exist is wasted work.

  The issue as I filed it said `Vixy_AmmoPayload` "carries risk today" because of an instance field.
  That was wrong — the field is `[NonSerialized]` and documented as transient — and the four passes
  it took me to settle what these classes actually serialize are written up in `docs/LESSONS.md`.

- **(internal)** An index of the official modding wiki, so I stop re-deriving what Freehold already
  documents (#506).

  Most of what this fork has learned the hard way has a page on
  [the official wiki](https://wiki.cavesofqud.com/wiki/Modding:Overview), and I did not know those
  pages existed. `<stag>`, load strategies, the random functions a mod is supposed to call, save
  migration, how an option can gate whole directories of XML — all documented, and all of it found
  by me only after the mistake.

  `docs/WIKI.md` indexes all 53 pages the modding navbox carries, grouped as the wiki groups them,
  with a line on what each settles and a table of *the question I keep asking → the page that
  answers it*. Nothing from the wiki is copied: it is CC BY-NC-SA, and a non-commercial clause does
  not sit comfortably beside this repository's own licences, so the file holds links, titles,
  section names and my own descriptions.

  It also records where the wiki and the assembly **disagree**, because the assembly wins and nobody
  should have to re-derive the same correction twice. Three so far: `*delete` is not broken on
  inherited tags, `<stag>` is a distribution route and not only a grammar one, and dynamic tables
  come in six kinds rather than three.

  Two traps are written down with it, both of which cost me a detour. The wiki returns 403 to an
  unrecognised user agent, so the obvious fetch fails. And the rendered navbox filters to the
  `Modding:` namespace, which hides two pages the categories genuinely contain — reading the sidebar
  and calling it the whole list is the same mistake as reading the XML and calling it the whole
  game.

- **(internal)** The one distribution route with no check now has one: `inherits-share` (#481,
  #494).

  Three ways content reaches a player were guarded — weighted entries, scatter entries, and
  `DynamicObjectsTable:` tags. The fourth was not, and it is the one nobody writes: the game builds
  `DynamicInheritsTable:<Base>` from everything descending from a base, so a blueprint joins as a
  consequence of `Inherits=`. No tag, no entry, nothing in a diff to review.

  `report_dynamic_tables.py` already had the inheritance index and the eligibility predicate, so the
  check lives there rather than in the validator — it needs the game for the same reason the rest of
  that tool does.

  **Its first cut measured the wrong thing, and the correction is the more useful half of this**
  (#494). It counted blueprints whose own tier matched the one requested. The game does not: a
  `:Tier{n}` slice holds *every* member of its pool, weighted by distance from that tier — 10⁸ at
  the tier itself, divided by ten per step away. Counting instead of weighing reported two slices as
  clean that were over half, and building cells only from tiers blueprints happen to carry meant
  most slices were never looked at. Fifty-five became a hundred and sixty-nine.

  So the ceiling is **reported here, not enforced**. Fifty of those slices sit above half, and that
  is not drift: completing a weapon or armour family across every tier is what this fork is for, and
  it necessarily takes most of that family's pool. A rule that fails the build on the mod's own
  premise is the wrong rule, and a ledger of fifty permanent exemptions is what the validation
  baseline exists to avoid. What fails instead is drift against `tools/inherited-pools.json`, which
  pins membership per pool and share per slice — they move independently, and a share can shift on
  its own when a Qud update moves vanilla's content relative to a tier.

  Ranges and the untiered table are modelled too, including vanilla's own bug of measuring a range's
  distance from `minTier` twice, so `maxTier` never reaches the comparison. Reproducing it is the
  only way the report agrees with what a player actually rolls.

- **(internal)** `docs/STYLEGUIDE.md` §3.2.1 now covers the third way content reaches a player, and
  how to measure it (#481, #494).

  `table-share` and `scatter-share` both govern entries someone typed. `DynamicInheritsTable:` pools
  are built from whatever descends from a base — joining is a consequence of `Inherits=`, with no
  tag and nothing in the diff.

  The section now says to measure a **slice** rather than a pool, and to **weigh** it rather than
  count it, which is the #494 correction. It also records that two earlier attempts to justify a
  floor are void: one rested on a gap between 9 and 16 in the pool-size distribution that does not
  exist, the other on "no cell has vanilla holding four to six" across 34 cells. Both counted
  members. Weighed properly there are 169 slices, not 34, and neither derivation survives the real
  numbers.

  The section also records that the dial here is coarser: no per-item weight to lower, only
  `ExcludeFromDynamicEncounters`, which removes a blueprint from every dynamic pool at once. So it
  is usable only on content that already has a home someone chose — which is why the chips could be
  excluded outright and the melee weapons cannot until #482.

- **(internal)** I documented, in five places, that Qud's biome-keyed dynamic pools have no consumer.
  They all do (#177, #171).

  `DynamicObjectsTable:<Biome>_Creatures`, `_Ingredients`, `_Plants` and `_FarmablePlants` are every
  one of them rolled — by **procedural village generation**, which decides who lives in a village,
  what they farm, and what the walls are made of. `VillageBase.cs` alone rolls all four.

  The original finding still holds where it matters: those pools do not put anything in a *zone*, so
  the 32 creature variants distributed by tag in #171 really never spawned. But "no consumer" and
  "a consumer that runs somewhere else" are different facts, and only the second one is true.

  **Why the search failed is worth more than the correction.** I checked the assembly with `strings`,
  which reads ASCII — and .NET keeps string literals in the metadata `#US` heap as UTF-16. So it
  found method and type names all along while silently finding no literals at all, which looks
  exactly like a working search. `docs/LESSONS.md` now carries both the corrected rule and the four
  lines of Python that read the literals properly.

- **Cragwort was almost invisible**, which is why a playtest crossing several parasangs of mountains
  never found one.

  It shipped in the darkest grey Qud has, on an equally dark tile — both inherited from noisegrass
  along with its sprite. Noisegrass grows in fungal and underground zones where that reads fine;
  cragwort grows on open mountain surface, next to dogthorn and witchwood, which are bright green
  and white.

  The tell was in the playtest rather than any check: witchwood turned up and cragwort did not,
  from the same table, where cragwort is the **commoner** of the two. Cragwort is now brown-olive,
  which keeps the ochre-on-rock look and is actually visible on rock.

  Ripe cragwort now changes colour properly too. It used to shift a single detail pixel and leave
  the tile black, so a ripe plant looked like an unripe one from more than a step away — vanilla
  always moves the whole hue when a plant ripens.

- **Psionic chips could turn up as ordinary loot, which was never the intention** (#481).

  `Raven_Base Psionic Chip` inherits `BaseArmor`, so all 144 chips descended from it — and the
  game builds loot pools from a base's descendants automatically. That put every chip in
  `DynamicInheritsTable:BaseArmor`, where this fork ran **80% to 96% of the pool at tiers 4 and
  above**, and in `DynamicObjectsTable:Items` alongside it.

  Nobody chose that. Membership follows from what a blueprint inherits, so it never appeared in a
  diff — and it worked against the chip design, which sets rarity through the Artifact tables on
  purpose and prices a chip only for what an unwanted one sells for.

  Chips now come from where the documentation always said they come from: `Raven_Chips Tier 1`–`3`
  through `Artifact 3`–`8`, at the hand-written rates in FEATURES §3.4, plus the starting kits.
  **No chip became harder to find** — all 144 are placed by hand and always were. What went away is
  a second, unchosen route around the rates.

- **The chalk centipede, hoary bat and black bear lived in a table Caves of Qud has switched off**,
  and now live somewhere you will actually meet them (#476).

  They were merged into `LowerTremblingDunesZoneGlobals`, whose contents Freehold commented out
  along with the rest of the Trembling Dunes globals. The zone is still built and its template still
  asks for that table, so the merge *created* it — which made these three **100% of that zone's
  global population**, and re-enabled something the game had deliberately emptied.

  The first fix moved them to Redrock, which holds all three parents and reads as the right kind of
  country. Measured afterwards, Redrock is **one world-map cell**, reached by 1 of the game's 87
  zone templates — exactly as narrow as the place they came from. It would have fixed the share and
  left the animals just as hard to meet. Every named landmark is that shape, the Rustwells included.

  So they went to the broadest table holding each parent instead: the hoary bat and black bear to
  `Tier3CavePopulation` (14 of 87 templates), the chalk centipede to `Shale Cave Critters 2` (8).
  Not `Tier2CaveCreatures`, which is also 14 but already carries the slate centipede — two variants
  of one parent in one table is not what the frequency curve describes. Weights follow it as usual:
  the parent's weight halved where its `Number` is already 1.

  `tools/validation-baseline.json` is empty again.

- **(internal)** `<stag>` is not a typo for `<tag>`, and the document that said so was wrong (#478).

  `XRL.World.GameObjectFactory` reads both, into the same dictionary — but it renames one:
  `<stag Name="Floating" />` produces the tag **`SemanticFloating`**, not `Floating`. They are two
  different keys, and whatever reads the tag looks for exactly one of them. Getting it wrong leaves
  the tag on a key nothing reads, which is the quietest failure in this codebase: the object loads,
  the tag exists, nothing happens.

  `docs/FEATURES.md` §10 row 6 stated the opposite — that `<stag>` is not an element Qud reads —
  and #50 changed two of them to `<tag>` on that reading. Vanilla writes `Floating` and `Trinket`
  **only** as `<stag>`, so that change made the advanced hoversled and the sphere of negative weight
  the only objects in the game carrying the unprefixed names. **Both are reverted**, and
  `curve_exempt` learned both forms in the same commit — it recognised a trinket only by `<tag>`, so
  correcting the blueprint on its own would have quietly dropped the sphere's exemption and priced
  it at 100 against a curve of 1280, reported as a defect in the item rather than in the check.

  With those two gone, `tools/validation-baseline.json` is **empty again**.

  A new `tag-form` check compares every tag this mod writes against vanilla's usage of that name,
  from a new `tag_forms` citation in the snapshot. It cannot judge a name vanilla never writes, or
  one vanilla writes both ways — `Fiber`, `Furniture`, `LightSource` and `Scrap` — and says so.
  `docs/STYLEGUIDE.md` §4.0b carries the mechanism.

- **(internal)** Three rows of `docs/FEATURES.md` §6.1 were wrong, and the total was right only
  because two of the errors cancelled (#473).

  `MeleeWeapons.xml` said 71 new / 79 merged and holds 101 / 77. `RangedWeapons.xml` said 9 merged
  and holds 11. `Creatures.xml` said 2 new and holds 46, having gone stale the moment the creature
  variants landed. The merged column drifted by −2 and +2, which sum to zero, so the Total row's
  **211** still matched — and the new column's Total matched too, because it is recounted from
  `mod/` rather than added up from the rows. The rows have never summed to the total.

  `check_docs.py` had computed the per-file figures since the table was written and published them
  as `file:<name>:new` and `file:<name>:merged`, and **no claim pattern had ever quoted one**. They
  are checked now, in both directions: a row naming a file that is gone fails, and so does a file
  with no row. Commented-out objects are counted too, which caught a fourth stale figure — the
  parenthetical on the `Ammo.xml` row said 20 dormant where the file holds 22, a number §10 already
  states correctly two thousand lines further down.
- **(internal)** The loot-table share ceiling silently governed nothing for half the tables it was
  meant to cover (#474).

  `table-share` caps this fork's share of a vanilla table at half by summing `Weight`. Vanilla's
  biome globals scatter with `Chance` and `Number` and carry no `Weight` at all, and neither does
  anything this fork merges into them — so both sides summed to zero and the check could not fail
  however much was added. Six merge blocks sat in that hole, every creature variant among them.
  `HillsZoneGlobals-Reachable` computed 0 against 100 and would have gone on passing at fifty more
  entries.

  A second check, `scatter-share`, measures those entries as expected quantity —
  `Chance ÷ 100 × Number` — which is what a scatter entry expresses. Twelve tables are guarded that
  were not, at real shares from 39% down — including all three the harvestable plants merge into.
  The weighted tables are untouched.

  Unifying the two into one measure does not work, and the attempt is worth recording: a
  `Load="Merge"` block carries no `Style`, because the group it merges into already has one, so a
  merged entry cannot be resolved to its parent's style from this fork's XML. Reading every merged
  entry as a scatter entry put `Melee Weapons 5C` at 75.2% against a true 42.6%, and twelve more
  with it. Splitting on "does this entry carry a `Weight`" needs no resolution, because vanilla is
  strictly disjoint there: all 4,860 of its `pickone` children carry `Weight` and none carries
  `Chance`.

  On its first run against real content it found #476 — a merge into a table Freehold has commented
  out — which is now the one entry in `tools/validation-baseline.json`.

- **(internal)** The Workshop description length check measured characters, not bytes (#171).

  Steam rejected the 2.7.0 upload with `k_EResultInvalidParam`. The description was 7,963
  characters and **8,019 bytes**: it carries 28 em dashes, and an em dash is three bytes in UTF-8.
  `check_workshop_description` measured `len(str)`, so it passed a description Steam would not take.

  A check that is wrong in the direction of saying "fine" is worse than no check, and this one was
  wrong at the single moment it existed for — the release it was written to protect. It now measures
  `len(str.encode("utf-8"))`, and the tests cover both directions of the multibyte case so the fix
  cannot degrade into rejecting non-ASCII outright.

  The description is trimmed to 7,951 bytes.

## [2.7.0] - 2026-08-27

### Added

- **44 creature colour variants**, on by default and toggleable in the mod options (#171).

  Thirteen common creatures pick up regional coats: brindle, rangy, pied, ash-coated and marsh dogs,
  dun and cragged and black goats, bristleback and russet and pale boars, mangy and silverback and
  rust-furred baboons, silt and pale crocs, copper and ember and glass dragonflies, verdigris and
  pale glowfish, marbled and ashen salamanders, mottled and sand horned chameleons, mossbacked and
  scarred tortoises, a banded honey skunk, an ashwing glowmoth, and midden, rust and salt beetles.

  **Purely cosmetic.** A variant differs in name, colour and description and in nothing else, so a
  pied dog fights exactly as a feral dog does.

  **The ordinary animal stays the common one.** Each variant sits one step below its vanilla parent
  on the game's own chance ladder in the same table, so a variant is the occasional find rather than
  the rule. Half the goats on a mountainside are not black; the black goat is two steps down and
  meant to be a surprise.

  **Baboons now reach the desert canyon**, which vanilla's own data always said they should — the
  mechanism that would have delivered them was never wired up. Two placements are genuinely new: a
  marsh dog in the saltmarsh and a salt beetle out on the dunes, neither of which vanilla has an
  animal for.

  A variant takes its parent's chance in the same table and about half its number, so you meet one
  roughly as often as the animal it varies while the plain animal stays the more numerous. An
  earlier curve put each variant a step below its parent, which made thirteen of them need about
  58 zones apiece to turn up — invisible in play, and found by walking the biomes rather than by
  any check.

  `docs/FEATURES.md` §17 is the full reference, including the catalogue and the derivation.

  A second wave adds six more families, chosen by the two rules the first wave arrived at the hard
  way — the animal must have a live population entry, and its colour must not already mean something.
  Sorrel and piebald equimaxes on the canyon floor and in the flowerfields, cinder and lantern
  glowcrows, ochre and meadow salthoppers, slate and chalk centipedes, rufous and hoary bats, and
  cinnamon and black bears through the caves and the Trembling Dunes. Birds were thin on the ground
  in Qud, so the glowcrows are the ones I most wanted.

  The svardym are deliberately left alone: their green, red, blue and bright green are rank markers
  rather than coats, and a variant there would read as a different tier of enemy.

- **(internal)** One creature variant, to prove the distribution route (#171).

  A single `dun goat` — a cosmetic colour variant of vanilla's goat — reaches the hills through an
  explicit merged entry in `mod/PopulationTables.xml`, which is how every other piece of this fork's
  content is distributed.

  It is deliberately alone. The previous attempt built 32 variants on a
  `DynamicObjectsTable:<Biome>_Creatures` tag that reaches no consumer, and none of them ever
  spawned; the defect was found by playing rather than by any check. So this one goes in first and
  gets walked in a running game before the other 31 follow.

  Both ends are verified this time. `ZoneTemplates.xml`'s `Hills` zonetemplate reads
  `HillsZoneGlobals-Reachable` in its `<global>` block, and that table is where vanilla lists `Goat`,
  `Dog` and `Boar` as explicit entries. `Chance` and `Number` are set high on purpose so the proof
  is observable in a handful of zones; they come down before the rest land.

  **Not releasable as it stands** — charter rule 6's option arrives with the full set, since the
  option mechanism the first attempt used is gated on the same dead tag and needs replacing too.

- **(internal)** The Workshop description's figures are checked, not only its length (#459).

  `check_docs.py` recounts 51 figures from `mod/` across the README, the charter and the feature
  reference — and read `mod/workshop.json` not at all. `validate_mod.py`'s `check_workshop_description`
  has only ever measured the Description against Steam's 8000-character limit. So the one piece of
  text every Workshop visitor reads was the only one whose figures nobody counted, and **"Twelve
  settings in Qud's own options menu" survived six new options across two releases**. Corrected to
  eighteen here.

  `WORKSHOP_CLAIMS` now holds four of them — options, subtypes, psionic chips and subtype sprites —
  read through the same recount machinery as everything else, and `workshop-version` holds the two
  places that go stale the moment `manifest.json` bumps: the `New in X.Y.Z` heading and the version
  under *Version and saves*. Both are anchored on their surrounding markup rather than on a bare
  version number, because the description legitimately cites older releases and the quill arrow
  really did ship in 2.3.0.

  What it deliberately does not check is whether the options *list* is complete. Six options are
  missing from those bullets, and they are prose rather than IDs, so no honest pattern reaches them.
  The count is what makes me reread the list — which is exactly how I found the six.

- **(internal)** The creature-variant work is reverted, and `docs/LESSONS.md` records why (#171).

  Thirty-two cosmetic creature variants were built on `DynamicObjectsTable:<Biome>_Creatures`, on
  the reading that a creature self-registers into a spawn table with a tag. **Nothing consumes
  those tables.** `Hills_Creatures` appears in exactly one file in the whole game — the one where
  creatures declare membership — and no population table references it, no zone builder requires
  it. Biome creatures come from ordinary hand-written populations: `HillsZoneGlobals-Reachable`
  lists `Goat`, `Dog`, `Boar` and `Salamander` as explicit entries.

  So the blueprints, their `*delete` tags, the `AggregateWith` merges and the option that gated
  them all governed a pool the game never rolls. None of it reached a release, and none of it is in
  this changelog as a player-facing change, because from a player's side nothing ever happened.

  Two lessons survive it, and both are recorded. `:Weight` on those tables is a multiplier wrapped
  in `(uint)Math.Ceiling`, so every fraction below one is inert — vanilla's own `Astral Tabby` at
  0.2 does nothing either. And `AggregateWith` inherits, so merging it onto a vanilla parent folds
  every vanilla descendant into one slot. Both are true, both were carefully verified, and neither
  mattered, which is the third and largest lesson: **count the consumers before you count anything
  else.**

  The blueprints are kept in history rather than in `mod/`, to be reintroduced through explicit
  `mod/PopulationTables.xml` entries once one variant is proven to spawn in a running game.

- **(internal)** Recorded that adding genders widened what the world generates, not just the chargen list (#435).

  `Gender.CheckSpecial` resolves keywords a blueprint can use in place of a gender name —
  `genericpersonalsingular`, `personalsingular`, `any` — through the same
  `GetAllGenericPersonalSingular()` the character-creation row uses, and that list went from **4 to
  13**. Nine vanilla blueprints use one of those keywords, so those creatures now generate as `fae`,
  `xe`, `spivak` and the rest.

  `male` and `female` pass through untouched, so `RandomGender="male,female"` — which 117 of the 126
  human blueprints inherit — is the same coin flip it always was.

  I think the behaviour is right: a blueprint asking for any generic gender should get any generic
  gender. But it changes what the world generates rather than what a player can pick, it was not
  argued for in #442, and I found it only because a village came up all-female and I went looking for
  a cause rather than assuming coincidence. §16.7 records it as a decision rather than leaving it a
  surprise.

- **A follower can wear a psionic chip, and the documentation now says so** (#417).

  Confirmed in game: a humanoid companion equipped a `Raven_Simple Disintegration Chip` unprompted,
  gained Disintegration, and killed a snapjaw with it. #434 corrected §13.1's claim that the slot was
  unreachable, but that correction was a code reading — this is the result, and §3 had never
  mentioned followers at all.

  §3.5 describes the capability, including the part that will otherwise waste someone's afternoon:
  the option adds the slot to the `Humanoid` **anatomy**, which is the template a body is built from,
  so **a follower you already have will never gain the slot** — only humanoids generated after the
  option is on. Testing it on an existing companion produces a false negative and the wrong
  conclusion.

  Nothing in this mod ever puts a chip on an NPC. Chips reach the world through the artifact tables
  that fill containers (#410), never through creature inventories, so this only happens because a
  player chose to hand one over — which is the sense in which the original line was half right.

- **(internal)** `docs/LESSONS.md` records what launching the game found that no check could.

  Six pull requests of naming and gender work reached `main` fully green — validator, docs checks,
  354 tests, a purpose-built harness reimplementing `XRL.Names`, and the C# compiled against the
  game's own assemblies. Launching Qud then found five defects in an hour, four of them mine.

  None was a correctness error in the sense any of those tools measure. Every one was a question
  about **when something happens**: when a list is populated, when a flag is re-read, which object a
  call passes, what a loader does with a collision. The harness modelled how a name *resolves* and
  answered that well; it does not model a lifecycle, and neither does a compiler.

  The entry keeps two specifics — that Qud writes `MODERROR` to its own log on every launch and
  nothing here reads it, and that `check_build_log.py` reported the mod compiled and loaded on the
  same launch where a character-creation row was silently missing. Both verdicts were true and
  neither was about behaviour.

- **Your chosen name flavour follows you, and Neutral is gone** (#184).

  Two things the first in-game test turned up.

  **Renaming yourself in game ignored the option.** That path is `GameObject.GiveProperName`, which
  calls `NameMaker.MakeName(this, …)` — a valid `For`, so `Generate` reads `Gender`, `Species` and
  `Tag` off the object and an option is invisible to it. Character creation followed your choice and
  every rename afterwards followed your gender. The module now writes the chosen tag onto the player
  as a `NamingTag` property, and `Raven_Options` rewrites it whenever the option changes, so it stays
  reversible rather than baked in — change your mind mid-run and the next rename uses the new choice.

  **`Neutral` is cut.** It drew from the mixed pool every time, which for a single name is
  indistinguishable from `Random` drawing that pool one time in three — both mean *"I am not
  specifying"*, and two ways to say it is a wart rather than a capability. `Random` still reaches
  that pool, so nothing is lost.

  **And the re-roll button in character creation now follows it**, which took working out.
  `EmbarkBuilder` fills `EmbarkInfo._modules` at the very *end* of character creation, so until then
  the list is empty and the Name row's re-roll consulted nobody — a setting whose re-roll ignores it
  is worse than no setting. The module now adds itself to that list in `Init()`. `EmbarkInfo.modules`
  is a public property, so this is a public member rather than a Harmony patch, and if Freehold
  changes it the mod stops compiling and CI says so on the next Qud update rather than the behaviour
  quietly rotting.

- **Four vibro weapons stopped losing their charge description** (#448).

  `Raven_Vibro Vinereaper`, `Vixy_Vibro Glaive`, `Vixy_Vibro Spear` and `Vixy_Vibro Quarterstaff`
  each carried **two** `<part Name="RulesDescription">` elements. Qud does not keep both:
  `ObjectBlueprintXMLChildNodeCollection.Add` reports the duplicate and then merges the second into
  the first, so the later `Text` overwrote the earlier. A player examining a Vibro Spear was told
  about Finesse and never told what charging it does, which is the entire point of a vibro weapon.

  The two texts are now one, keeping both facts.

  **`finesse-visible` caused it.** That check requires a `Finesse` tag and its rules text to imply
  each other, so satisfying it meant adding a `RulesDescription` — and on these four, one already
  existed. A check demanding text is what deleted other text. It arrived across #390 and #391, both
  of which passed all ten required checks, and has been shipping since.

  `duplicate-child` now holds every `<object>` against naming two children the same, across `part`,
  `tag`, `stat`, `mutation`, `skill`, `intproperty` and `property`.

  **Only the game ever noticed.** It writes `MODERROR` to its log on every launch and nothing reads
  that; the XML is well-formed, so neither `prettier` nor anything in `tools/` had an opinion. Found
  by launching Qud to test something unrelated.

- **(internal)** `ruff` v0.16.3 → v0.16.4, in both places it is pinned.

  A patch release, and the interesting part is the second file. `.pre-commit-config.yaml` is what
  Dependabot can see; `ci.yml` installs ruff by an explicit `pipx install ruff==` pin that it cannot,
  so a bump of the hook alone leaves CI's formatter a version behind the one contributors run — and
  `ruff format --check` disagreeing with the hook that just formatted your code is worse than having
  neither. The pin carries a comment saying it must move in step, and this is the first bump since
  that comment was written to actually test whether anyone reads it.

  Verified the way #110 established: every one of the 17 hooks run against the whole tree on the new
  version. All pass, **nothing was modified**, and the byte-order-mark count is unchanged at 19 —
  which matters because the mod's XML depends on those marks and a hook that stripped them would
  break the mod quietly.

- **(internal)** `conflict-markers` looks for the marker nothing else did (#446).

  I left a stray `||||||| 0e0d9de` in `CHANGELOG.md` resolving a merge. It was committed, it passed
  every gate, it merged, and it sat on `main` in a player-facing document until I happened to trip
  over it resolving the next one.

  **Nothing could have caught it.** `pre-commit`'s `check-merge-conflict` matches `<<<<<<< `,
  `======= ` and `>>>>>>> ` — and **not `||||||| `**, the diff3 base marker git writes as the third
  section of a conflict. `check_docs.py` reads figures and links and has no opinion about stray
  lines; `validate_mod.py` does not read the changelog at all; and it renders as ordinary text in
  GitHub Markdown, so it did not even look broken.

  It is also the marker most likely to survive a resolution, because the other three arrive as a
  matched set that is obvious when one is left behind, while the base marker is optional and easy to
  forget a file ever had.

  The check reads **every tracked file**, not the document list — the file a bad resolution lands in
  is the file nobody is reading. It is wired as its own **unscoped** pre-commit hook rather than
  folded into `check-docs`, which only runs on `mod/`, `docs/` and top-level Markdown; a marker in a
  workflow or a tool would not have been looked at either. It costs 0.1s over 140 files.

  Precision is deliberate: `=======` is also a Markdown setext underline for an H1, and
  `LICENSE-CONTENT` rules its sections off with 71 of them. Matching the upstream hook's exact
  shapes — a trailing space, or exactly seven characters then end of line — tells a conflict marker
  from a horizontal rule. Nine tests, both directions, including the lookalikes.

- **Your own random name can sound how you want it to** (#184).

  Everything in the naming change scopes on a creature's gender and species, and **none of it could
  reach the player**. `GenerateRandomPlayerName` calls `NameMaker.MakeName(null, null, Type)` with no
  GameObject — the name is generated before the player object exists — so `Generate` never populates
  `Gender`, `Species` or `Tag`, and your name came out gender-blind however the namestyles were
  scoped. There was nothing to hang a property on.

  A new option picks the pool instead: **Random** (the default, an even three-way split), **Masc**,
  **Femme** or **Neutral**. Typing a name in bypasses it, which is still the surest way to get the
  one you want, and it does not touch anyone else in the world.

  **This is the first time this mod's C# runs during character creation**, and it raises charter
  rule 5's ceiling for the second time since the fork. `mod/Scripting/Vixy_NameFlavourModule.cs` is
  an `AbstractEmbarkBuilderModule` that handles one boot event. None of rule 5's hard limits moves:
  the base class declares **no abstract members**, so it overrides one public virtual method; the
  game instantiates it from a class name in `mod/EmbarkModules.xml` exactly as it instantiates a part
  from a blueprint, so the reflection is the game's rather than the mod's; and it declares no module
  data, because `AbstractEmbarkBuilderModuleData` is `[Serializable]` and travels in build codes — a
  module holding state would put this mod's shape into other people's saved characters. The
  alternative was Harmony, which rule 5 refuses and which breaks on arm64 macOS anyway.

  It is a module rather than an `EmbarkEvent` handler because `fireBootEvent` iterates
  `enabledModules` regardless of `game`, while `EmbarkEvent.Send` goes through `Game?.HandleEvent` —
  and character creation's own *"roll me another name"* passes `game: null`. An event handler would
  have changed the name you started with and not the one you were shown while choosing it.

- **You can choose your gender and pronouns, and there are thirteen of them** (#435).

  Qud has a complete gender and pronoun system — 13 genders with full grammar tables, a separate
  pronoun-set system, replication between the two, and a selection UI rendered down to its screen
  coordinates. **It ships every part of it switched off.** Both data files carry
  `EnableSelection="false"`, and character creation yields the Gender and Pronoun Set rows only when
  those are true, so neither row is ever emitted and the game picks a gender for you at random.

  Character creation now offers both rows. The gender list goes from **4 to 13**: `elverson` (ey/em)
  unhidden, `xe`, `ze` and `sie` promoted from pronoun sets to genders, and `fae`, `spivak` (e/em),
  `ve`, `per` and `ne` added. The pronoun list goes from **8 to 14**.

  Every addition uses vanilla's own person terms for a generic non-binary gender, taken from
  `elverson` — `person / child / friend / child / sibling / parent`. The game had already answered
  that question, so this derives rather than invents.

  **`hartind` stays hidden, deliberately.** It is the other gender behind `Generic="false"`, its
  person terms are `hartind` / `faun`, and its pronouns duplicate `nonspecific` exactly — it is the
  hindren third gender rather than a general one, and offering it would change nothing about the
  grammar while putting a hindren cultural gender in everyone's list.

  **Turning it on is C# rather than the one-attribute XML version, and that is the whole point.** A
  `mod/Genders.xml` carrying `EnableSelection="true"` would work — but XML loads unconditionally and
  could never be switched off. Two options set the fields instead, so charter rule 6 holds.

  `DoNotReplicateAsPronounSet="true"` on the three promoted genders prevents a duplicate that would
  otherwise have shipped: a replicated pronoun set is named by all eleven of its forms, **person
  terms included**, so a promoted gender whose terms differ from vanilla's defaults does not collide
  with the hand-written set it was promoted from — it appears twice, identical pronouns, differing
  only in whether a stranger calls you `person` or `human`.

- **(internal)** `option-default` holds a Checkbox default to the two values a Checkbox stores (#443).

  Thirteen of the fourteen options used `Default="Yes"` or `Default="No"`. Graded burden used
  `Default="false"` — and it worked, which is the part worth fixing.

  A Checkbox stores exactly `"Yes"` or `"No"`
  (`SetOption(ID, GetOption(ID) == "Yes" ? "No" : "Yes")`), and `GetOption` returns the XML `Default`
  before any C# fallback, so the XML value is what `Enabled` compares against until the player
  touches the option. `"false"` is simply not `"Yes"`, so it read as off, which is what graded burden
  wanted. **`Default="true"` would not have been so lucky**: an option meant to default on would have
  shipped off, the checkbox would have rendered unchecked, and nothing would have errored — leaving a
  player looking at an option that appears not to work, and a one-character cause in a file nobody
  would suspect.

  The one wrong value in the file being a *working* example is what made it worth a check rather than
  a correction: the next person adding an option had a coin flip on which line to copy.

  The Combo half is preventative and I would rather say so than imply it caught something — every
  Combo in the file is correct. A `Default` outside the option's own `Values` fails the same silent
  way. `Default="false"` is now `Default="No"`, which changes no behaviour at all.

- **(internal)** The harness predicts the character-creation gender and pronoun lists (#435).

  Qud ships a complete gender and pronoun system switched off, and #435 is about turning it on. Both
  of the failure modes there are silent: a gender that never reaches the list, and two entries a
  player cannot tell apart. Neither errors, and neither is visible without starting a new game.

  `--genders` resolves both lists the way the game does — `Generic && !UseBareIndicative && !Plural`
  for the Gender row, hand-written sets plus one replica per eligible gender for the Pronoun Set row
  — and reports what a candidate fragment changes.

  It found the trap immediately. A replicated pronoun set is **named by all eleven of its forms,
  person terms included**, and replication is skipped only when a set of that exact name already
  exists. So promoting `xe` to a gender with sensible person terms does *not* collide with the
  hand-written `xe/xem/xyr/xyrs/xemself` set vanilla already ships — it appears **twice**, identical
  pronouns, differing only in whether a stranger calls you `person` or `human`. Three of the nine
  planned additions would have done this. `DoNotReplicateAsPronounSet="true"` avoids it, and the
  harness confirms both the duplicate and the fix rather than my having reasoned about it.

  Verified against the installed game: vanilla is 4 genders and 8 pronoun sets, which is what the
  simulation reproduces from the same files.

- **Both halves of the name change are options** (#184).

  `wider name pools` and `gendered name endings`, separate on purpose: wanting more variety and
  wanting names to signal gender are different opinions, and rule 6 says nobody should have to take
  one to get the other. Both default **on** — they are cosmetic and grant no power, so rule 6's
  default-off exception does not apply.

  Both are reversible rather than undoable, which is what rule 5 asks of anything that mutates
  loaded game data. The widening sets `Weight` to 0 on the syllables this mod added, which
  `GetRandomNameElement` skips while leaving the element in place; the gendered endings set `Chance`
  to 0 on the two new namestyles' scopes, which `ApplyTo` evaluates last, so the scope stops matching
  and naming falls back to Qudish exactly as vanilla does it. Off is vanilla, exactly.

  **The syllable list is restated in C# and a check holds the two halves together.** Nothing at
  runtime can tell a merged-in syllable from a vanilla one — the loader appends both into the same
  `List` and neither carries a marker — and reading the XML back would be file I/O, which rule 5
  forbids. It lives in its own `Vixy_NameSyllables.cs` so the spell checker can skip it — these are
  invented fragments, and `Raven_Options.cs` is 700 lines of real prose that should stay checked.
  `naming-option-coverage` holds the two files against `mod/Naming.xml` in both
  directions: a syllable in the XML the option cannot reach, and a syllable in the C# the XML does
  not add. The second is the dangerous one, because zeroing a weight on something this mod does not
  own means silencing vanilla's.

  `tools/naming_harness.py` covers the case CI cannot see: a syllable that shares a name with a
  vanilla one **merges into a single element**, so it does not lengthen the pool and there is no tail
  to inspect. The harness reads the fragment's own declarations against the installed game instead.
  None of the 59 collide today.

- **Names stopped repeating, and half the people in Qud stopped sounding like men** (#184).

  Vanilla's Qudish namestyle has 29 prefixes, 20 infixes and 24 postfixes — about 93,500 distinct
  names, so exact repeats were never what anyone was noticing (0.2% across 20 rolls). **Syllable**
  repeats were: a 50% chance of a repeated *opening* after 6.3 draws. So this widens openings and
  endings and deliberately leaves the infix pool alone, because the infix is not where the collision
  is. Prefixes 29 → 68, postfixes 24 → 36, which moves a repeated opening from 7 draws to 11 and
  halves how often you see one across 20 names.

  The second half is the one I did not expect. Qud's name generation is very nearly gender-blind —
  exactly **one** namestyle in the whole vanilla file uses a `Gender` attribute, and it is a Warden
  honorific. What reads as male-coded is a phonetic property of the pool: **23 of vanilla's 24
  endings are hard stops**, `la` being the only open one. And the game already knows: **117 of the
  126 blueprints that resolve to Qudish inherit `RandomGender="male,female"` from `BaseHuman`**, a
  coin flip rolled before the name is generated and handed to the generator. Half of every generated
  human in Qud already was female, drawing from a pool of hard stops.

  `Vixy_Qudish Feminine` and `Vixy_Qudish Neutral` use the gender the game had all along. The
  feminine pool keeps five hard endings on purpose — it is a lean, not a rule, so a name never states
  the gender outright. The neutral pool is an even mix, scoped one gender at a time because
  `NameScope.Gender` is a single exact-match string. `hartind` is deliberately excluded: its person
  terms are `hartind` / `faun`, which makes it the hindren third gender rather than a general one.

  **What this does not touch**, which turned out to be most of the game: hand-authored NPCs carry
  their names on the blueprint and never call the generator; snapjaws, robots, animals, plants,
  Templars and Mechanimists have their own pools; and village and site names come from `Qudish Site`,
  a separate namestyle whose scopes gate on `Type` and can never be reached by a person-name call.
  The player's own random name is untouched too — `GenerateRandomPlayerName` passes no `GameObject`,
  so it is generated gender-blind no matter what these namestyles say.

- **(internal)** Four checks hold `<naming>`, which merge discipline never reached (#184).

  `check_merge_discipline` walks `<object>` and `<population>`. A `<namestyle Name="Qudish">` without
  `Load="Merge"` passed CI, and the cost of that is not the one the existing check guards against:
  `LoadNameStyleNode`'s replacement branch removes the style from `_NameStyleList`, builds a fresh
  one, writes it to `_NameStyleTable` and **never adds it back to the list**. `Generate` iterates the
  list. The namestyle does not lose its pools — it leaves name generation entirely, and every
  procedurally named human comes back as the literal string `NameGenFail1`, `NameGenFail2`.

  `naming-merge-discipline` holds the attribute and its cascade, and holds one thing the object-side
  check has no analogue for: **scopes merge by `Name`**, so `<scope Name="General">` on a vanilla
  namestyle rewrites vanilla's scope in place rather than adding one. A new scope needs a mod prefix.

  `naming-priority` holds a combining scope above 0 and below 100. Both ends are silent failures that
  look like sensible defaults. At 0 the weighted draw skips the entry, so two such scopes send the
  total to zero and return `NameGenFail<n>` as a creature's name — vanilla's own `Qudish` sits at 0
  and survives only by being the single `General`-scope namestyle in the file. At 100 the exclusion
  test `other.priority > scope.priority` stops holding, so the scope displaces the faction namestyles
  instead of losing to them, and female Templars stop being named like Templars.

  `naming-amounts` holds `Format` and every pool's `Amount` on a **new** namestyle, because
  `NameStyle` defaults them to `"AsIs"` and `"0"` — omit them and the style generates the empty
  string rather than erroring. A merge omits `Amount` deliberately, and the check knows the
  difference. `naming-ascii` holds the line the prior-art builder already held: vanilla is 3,074
  syllables for 3,074 ASCII, with no exceptions.

- **(internal)** `tools/naming_harness.py` resolves name generation without launching the game (#184).

  Everything this repository knows about `Naming.xml` was read out of `Assembly-CSharp.dll`, and
  reading control flow is not the same as watching it run. The harness reimplements the three pieces
  of `XRL.Names` that decide what a creature is called — the loader's `Load="Merge"` cascade,
  `NameScope.ApplyTo`, and `NameStyles.Generate`'s Priority-weighted draw — so a candidate fragment
  can be checked against vanilla before it reaches `mod/`.

  It earned itself immediately. I had been describing a missing `Load="Merge"` as *"clears the
  pool"*, and it is worse than that: `LoadNameStyleNode`'s replacement branch calls
  `_NameStyleList.Remove(value)`, builds a fresh style, writes it to `_NameStyleTable` and **never
  adds it back to the list**. `Generate` iterates the list. So a redeclaration without the attribute
  does not empty a vanilla namestyle, it removes it from name generation altogether — surviving only
  for `Base=` lookups. Doing that to `Qudish` takes every procedurally named human in the game with
  it, and each one comes back as the literal string `NameGenFail1`, `NameGenFail2`, and so on.

  Two more traps are now executable rather than remembered. A `General` scope at `Priority="0"` is
  **skipped entirely** by the weighted draw, so a second one alongside vanilla's sends the total to
  zero and returns `NameGenFail<n>` as a creature's name; vanilla survives only because `Qudish` is
  the sole `General`-scope namestyle in the file, which takes a different branch. And the exclusion
  test is `other.priority > scope.priority`, so a new combining scope at 100 does not lose to the
  faction styles — it **displaces** them, and female Templars and Barathrumites stop being named
  like Templars and Barathrumites.

  `--check` runs a scenario battery and exits non-zero; `--sample` draws names for a context. 22
  tests in `tools/test_naming_harness.py`, synthetic XML only, so CI runs them without a game.

### Fixed

- **The Pronoun Set row never appeared, because character creation switched it back off** (#435).

  Both chargen options defaulted on and both set their flag, but only the Gender row showed up.
  `QudCustomizeCharacterModule.Init()` calls `PronounSet.Reinit()`, which clears every pronoun set
  and re-reads `PronounSets.xml` — whose root carries `EnableSelection="false"`. So character
  creation undid the pronoun half **as it opened**. `Gender` has no equivalent `Reinit` and
  survived, which is exactly why the symptom was one row present and one missing rather than both
  gone.

  `Vixy_NameFlavourModule.Init()` now reapplies both. `EmbarkBuilder` calls `Init()` on every module
  in load order, and `DataFile.CompareTo` sorts base files before mod files unconditionally, so a mod
  module's `Init` always runs after a base module's.

  **Found by launching the game**, on the first character created with the mod installed. Nothing
  else could have: the harness models how a name resolves, not the lifecycle of a character-creation
  module, and the C# compiled and loaded without complaint. It is the exact shape of defect
  `docs/LESSONS.md` keeps returning to — every check green over something nobody had looked at.

- **The documentation said an NPC's Chip Interface slot could never be filled, and it can** (#417).

  `docs/FEATURES.md` §13.1 read *"nothing here ever fills those slots, so the reason to turn it off is
  to stop another mod — or a later version of this one — being able to."* The first half is true of
  the mod: no creature is generated carrying a chip. The conclusion is not, **because a player is not
  another mod.**

  Chips are worn armour rather than implants — `BaseArmor` with `WornOn="Chip Interface"` — which puts
  them on the ordinary AI equip path, and every gate on that path is open. `Body.GetParts()` returns
  the abstract slot with no filter; `Armor`'s equippable-list handler adds the chip on a `WornOn`
  match and never reads `RequireDesirable`, so 0 AV / 0 DV does not disqualify it; no chip carries
  `NoAIEquip`; `CompareGear(chip, null)` returns `-1`, so anything beats an empty slot; and the grant
  fires on `EquippedEvent` against `E.Actor`, which is whoever wore it.

  So handing a chip to a humanoid follower should give **the follower** the mutation. The option is
  the switch for that, and nothing said so.

  **This is a code reading, not a result** — nobody has watched a follower do it, and the callout says
  so rather than implying otherwise. #417 stays open for the in-game test. What changed here is that
  the document no longer makes a claim its own code contradicts.

### Changed

- **(internal)** `aggregate-sweep` holds a blast radius that nothing could see (#171).

  Merging a tag onto a vanilla record edits that record *and everything descended from it*, and the
  subtree is not visible from a diff showing one `<object Load="Merge">` and three lines. Every
  static check passed while baboons quietly got four times rarer; what found it was playing the
  game.

  `tools/qud-api.json` now records every vanilla descendant of a parent this fork aggregates, and
  `validate_mod.py` fails until each is deliberately exempted. Because the list comes from the
  snapshot, a Qud patch adding a descendant to one of those families makes `snapshot-check` report
  stale, and regenerating turns the new name into a red run rather than a slow change in what the
  world spawns. `docs/LESSONS.md` records the reasoning.

- **(internal)** `tools/validate_mod.py` learned the two routes it was blind to (#171).

  `check_reachability` now counts a `DynamicObjectsTable:` tag as a distribution route — it had
  reported all 32 creature variants as unobtainable while they spawned perfectly well, because they
  sit in no `PopulationTables.xml` entry. `*delete`, `{{{remove}}}` and the `:Weight` / `:Number` /
  `:Builder` modifiers deliberately do not count, since a removal is the opposite of a route.

  `check_option_wiring` now also counts an option read by an `ExcludeFromDynamicEncountersOption`
  tag, having called the creature-variants option dead while it was doing its job. Both directions
  are covered by tests, including the positive controls that keep the widened checks from going
  vacuous.

  `docs/STYLEGUIDE.md` §3.3 gains the creature carve-out: its "every new item also gets an explicit
  population entry" rule cannot apply to a creature, because `PopulationManager.RequireTable` returns
  early on an existing name — declaring a `<Biome>_Creatures` table would replace vanilla's fabricated
  pool rather than join it, and silently stop every vanilla creature in that biome from spawning.

- **(internal)** `docs/LESSONS.md` records that a scope which looks load-bearing may match nothing (#456).

  `Naming.xml` scopes on `Culture` 50 times, naming 36 cultures — twice as often as it scopes on
  `Species`. Seven of those 36 can never match a creature, and one of them is `Qudish`: **no
  blueprint in Caves of Qud carries `Culture="Qudish"`**, so that scope has never fired in any game
  anyone has played. `GetCulture()` is `GetPropertyOrTag("Culture") ?? GetSpecies()`, the tag appears
  41 times in the whole game, and exactly one line in the 12 MB assembly writes it at runtime.

  `Ape` is dead for a second reason worth its own paragraph: apes carry no tag, so the fallback
  supplies `ape`, and the scope asks for `Ape`. `NameScope.ApplyTo` compares with `!=`. `Bear` and
  `Bird` look identical and work, because a blueprint tags each with the capitalised spelling.

  The rule the entry lands on is that a scope, a tag, a table reference and an `Inherits=` are all
  assertions that something is there, and every one of them parses, validates and ships whether or
  not it is. Counting the other end took two commands and settled a design question I had been
  arguing on taste. `AGENTS.md` gets the short version.

  The uncomfortable half is that `tools/naming_harness.py` could have answered this before #436 was
  written. It was built for exactly this and I read the XML instead.

- **(internal)** The wiki's figures are checked, not only its links (#427).

  `check_docs.py --wiki` cloned the wiki and verified its anchor links, and **read nothing else**.
  The sweep before 2.6.0 found nine wrong figures on five pages — eleven options where twelve ship,
  an extra cybernetics licence point no caste grants any more, eight vibro weapons where eleven
  exist. Not one was catchable, because nothing read the content. The wiki also has **no version
  selector**, so a wrong figure there is wrong for every player on every version at once.

  `wiki-figure` now holds eleven figures across the pages, against the same `facts()` the repository's
  own documents are checked against. Two facts are new and both come out of `mod/`:
  `chip-slots-truekin` / `chip-slots-psionicadept` counted from `Bodies.xml`, and `vibro-weapons`
  counted from a real parse of `MeleeWeapons.xml` — that file holds four vibro objects inside a
  comment block, and a regex over the raw text counts them, which is the defect `docs/LESSONS.md`
  records against that exact file.

  **`WIKI_CLAIMS` is a separate table from `CLAIMS`**, which was the design question #427 raised
  before any of this was written. The wiki is cloned only under `--wiki`, so its patterns match
  nothing on an ordinary run — and `claim-coverage` from #422 would have called all ten dead. One
  table would have meant a scope marker on every entry; two carry it in the name, and the coverage
  guard only reads the wiki table when there is a wiki to read it against. Both halves are tested.

  It runs weekly rather than on pull requests, in its own workflow. The wiki is a separate
  repository, so nothing here changes when it does and a push-triggered run would never see a wiki
  edit; and cloning needs the network, which `ci.yml` deliberately does not.

  **It catches four of the seven, and #427 claimed seven of nine before it was built.** I measured it
  by restoring all seven wrong claims to a copy of the wiki and running the check: the option count on
  three pages and the vibro count fire; the other three do not, because they are prose with no figure
  in them.

  The three it misses are the ones worth naming. *"Every humanoid has at least one Chip Interface
  slot, so a Mutated Human can wear one"* — the worst error of the sweep — has no number in it, and a
  Mutated Human's count is zero because a C# player mutator removes the slot rather than because any
  XML says so. Restating that rule in Python to check it would be a second implementation of the same
  rule, which is `docs/LESSONS.md`'s "a number that agrees because both sides share the error".
  Likewise *"every Lore Seeker comes with an extra licence point"* and the list of which weapons scale
  off Agility: both are sentences about which things belong to a set, not about how many.

  So this is a real floor under the wiki rather than a solution to it. The limit is recorded as a test
  so it is rediscovered by a failing assertion rather than by a player.

## [2.6.0] - 2026-08-24

### Changed
- **(internal)** Claim patterns are wrapped centrally, and `claim-coverage` fails any that matches
  nothing (#422).

  `check_docs.py` verifies a figure by finding the sentence that quotes it. `re.finditer` yields
  nothing for a pattern that matches nothing, so **a pattern which stops describing its sentence
  reports no failure** — it just quietly checks less. The only symptom is that the "N documented
  figure(s)" line goes down, and nothing knew what N should be.

  Six of forty-seven patterns were in that state, from two different causes:

  **Reflowed prose.** `wrapped()` has existed since #242 to turn every literal space into `\s+`,
  with a docstring saying a pattern with a literal space *"stops matching the moment a sentence
  moves across a line … which is the same silence this whole check exists to break, arriving
  through the check itself."* It was opt-in, and **19 of 29 `CLAIMS` patterns did not use it.** One
  had already gone silent, which is how the README's blueprint count drifted by 52 unnoticed. It is
  now applied by the loops, so a new pattern cannot be written unwrapped.

  **Reworded documents.** One pattern read
  `r"Eleven options" if False else r"\*\*(\d+)\*\* options, all under"` — a dead conditional
  leaving a live-looking disabled branch, where the disabled half matched the defect and the active
  half matched nothing at all.

  `claim-coverage` closes it in both directions, the same argument #402 made for the check-name
  registry: a pattern that matches nothing fails, and an `IDLE_PHRASINGS` exemption naming no
  registered pattern fails too, so the exemption list cannot become where typos go to be ignored.

  **Five patterns are legitimately idle** and say so. Four are the census matrix from #242, which
  registers nine ways to state one survey so whichever phrasing a document reaches for is checked;
  the fifth appears only inside a changelog entry quoting an old bug report. Each carries a reason,
  and a test asserts every reason is non-empty.

  The option's requirement count is a computed fact now — `optioned-requirements`, read out of
  `Raven_Options.cs`'s `Requirements[]` — rather than a number in prose with nobody to disagree
  with it.

- **(internal)** `skill-option-coverage` holds `mod/Skills.xml` against the option tables, in both
  directions (#421).

  The two halves of an optional skill change live in different files and neither names the other, so
  nothing could see that #331 had edited one and not the other. This fails the build when they
  disagree:

  | | means |
  |---|---|
  | a value differs from vanilla and no table restores it | a change nothing can undo |
  | a table entry whose value already matches vanilla | an option that restores nothing |

  Both directions were verified by reintroducing the real defect and watching each fire, rather than
  by trusting a pass. Powers with no vanilla counterpart — the four `Finesse` ones — are additions
  rather than merges and belong to neither direction.

  It needs vanilla's side to compare against, so `tools/qud-api.json` gains **`skill_powers`**: the
  `Cost`, `Minimum` and `Attribute` vanilla states for each of the 23 powers this fork merges. Same
  bargain as `merged_records` — a citation exists because a check depends on it, and CI has no game.

- **The dermal plating line is priced on vanilla's own rate, so vanilla's own plating is worth
  installing again** (#418).

  #335 restored `DermalPlating` to vanilla's 3 licence points for +1 AV, which was right. What it did
  not do is look at what that landed next to. **Vanilla's only plating came out dominated by two of
  this fork's rungs**: steel gave the same +1 AV for a third of the licence cost and a third of the
  water, and crysteel gave twice the AV for the same 3 points. There was no state of the game in
  which a player should install carbide dermal plating.

  Vanilla ships exactly one plating, so there is exactly one data point for what armour costs a True
  Kin: **3 licence points per +1 AV**. The fork's three rungs now sit on that rate.

  | plating | source | licence | water | AV | across 3 slots |
  |---|---|---:|---:|---:|---:|
  | steel | fork | 1 | 60 | +1 | **+1** — Body only |
  | carbide | **vanilla** | 3 | 180 | +1 | +3 |
  | crysteel | fork | **6** | **360** | +2 | +6 |
  | zetachrome | fork | **9** | **800** | +3 | +9 |

  **So the fork's platings buy slot density rather than power.** One zetachrome is +3 AV for 9 points
  in one slot; three carbides are +3 AV for 9 points in three. You pay vanilla's price for the armour
  and buy back two slots for something else — which is a reason to want the expensive one that
  survives being read carefully, and is the first one this line has had.

  Steel keeps its cheap entry price and is now **Body only**, so it cannot ladder to +3 the way it
  could while it undercut carbide in every slot. `Slots` governs installation rather than what is
  already installed, so **a save with steel plating in a Head or Back slot keeps it**.

  Crysteel moves from `Implants_3Pointers` to `Implants_4PlusPointers`, because those table names are
  literal about licence cost rather than decorative.

  **Carbide itself does not move.** Charter rule 2 sets a high bar for changing vanilla's values and
  #335 had just finished putting this one back; the fork's own rungs are the fork's to price. Nothing
  is deleted either — `Raven_DermalPlatingSteel` has shipped, and a save with one installed would be
  orphaned by removing it.

- **(internal)** `implant-table-cost` holds an implant's loot table against the licence points it
  actually costs (#418).

  The three vanilla implant tables are named after a cost bracket, so each name is a claim about what
  is inside it — and nothing in the game checks that. This is exactly how the crysteel placement
  above survived a re-price: the table went on saying *3 Pointers* while holding a 6-point implant.
  Charter rule 4 wants that in the script rather than in prose, so it is.

  Only this fork's blueprints are checked. Vanilla's placements are vanilla's to be wrong about.

- **The Psionic Adept has a stated reason to exist** (#410). It is the flagship genotype and nothing
  player-facing ever said what it was *for* — the README, the Workshop page and `docs/FEATURES.md`
  §1.4 all described its *contents*, which is not a reason to choose it over a True Kin.

  **A True Kin plans; an Adept adapts.** A True Kin's power is a shopping list: credits cost 150 water
  each, implants are chosen, and you install exactly what you saved for. An Adept's power is whatever
  the world hands it — psionic chips **cannot be bought and cannot be built**. They carry no
  `TinkerItem` and no `DynamicObjectsTable` tag, and the only tables naming them are `Artifact 3`
  through `8`, which is what fills a chest. Chargen gives you three, filling three of your four slots
  from your affinity's own kit, and everything after that is a find.

  So it is the one genotype whose build you cannot decide in advance — which is what its fiction
  already said, since a chip is *"knowledge lost eons ago"* that integrates with your flesh. **You
  become what you find**, and the 95 skill points a level, the most in the game, are the counterweight
  for having no innate power at all.

  **Why it mattered now.** The balance sweep touched this genotype five times — #338, #332, #330,
  #350 and #353 — and not one of those changes could be weighed against a niche, because there was
  none written. Charter rule 2 asks *"does the world explain it, and does it change a decision the
  player makes?"*, and that question had no answer here.

  Re-read against the niche now that it exists, four of the five hold up and one is in tension:
  **#338's rarity pass** is right on its own terms and lands on the only genotype whose core resource
  has a drop rate at all. A mutant spends points and a True Kin spends water; only an Adept can have a
  run simply not deliver. The starting kit is what stops that being a cliff. Recorded in
  `docs/DESIGN_balance.md` §5.8 rather than acted on.

  **Its power curve is the opposite shape to a mutant's, and that is the arc rather than a defect.**
  A chip's rank is capped at its grade, so an Adept peaks around character level 18 and falls behind
  after 30. Front-loaded breadth that plateaus, with #350's duplicate stacking as the one route past
  it. That was always the design; it had just never been said out loud.

- **The mace ladder is the Cudgel tree's finesse pick, and now weighs a pound less than the war
  hammers** (#342).

  **What it is.** Pathfinder's finesse bludgeon is a mace-family weapon — the light mace carries
  agile, finesse and shove, while the warhammer never does. So the **nine one-handed maces** take the
  `Finesse` tag: with the Cudgel tree's Finesse power bought, penetration rolls
  use your Agility modifier whenever it beats Strength. **The war hammers stay Strength**, which is
  what they should always have been — #321 called the war hammer one of the two most genre-inverted
  assignments in the mod, and this does not undo that, it puts the finesse on the weapon that
  deserved it instead.

  **The pound changes sides.** The war hammer used to be the lighter twin at six of nine tiers.
  That is backwards for a finesse weapon, so the mace line now sits **one pound below** the war
  hammer line at every tier, and the mauls one below the greathammers. Maces run 3·2·2·4·3·5·2·2·2
  against war hammers at 4·3·3·5·4·6·3·3·3.

  #342 called that one pound the last vestigial signal in these families. It is now the load-bearing
  one — it tells you which line is the finesse line.

  **It also repairs a rule.** `docs/STYLEGUIDE.md` §3.2 says a two-handed hammer weighs its
  one-handed twin plus 3. The mace family broke that at two tiers — fullerite was +4, zetachrome +2.
  Flipping the offset put every tier at exactly +3. Two-handed cudgels stay Strength-only either way;
  the mauls moved to keep the relationship true, not to become finesse weapons.

- **The vinereaper is a sickle** — it takes the `Finesse` tag, and stops being found as loot above
  steel (#342).

  **What it is.** Vanilla describes it as *"wrought iron was moulded to a **crescent** for **scything
  the rough hides of watervine**"* — a crescent blade named for the crop it harvests. That is a
  sickle, and Pathfinder's sickle carries agile, finesse and trip. So the whole line is now a finesse
  weapon: with the Axe tree's Finesse power bought, penetration rolls use your Agility modifier
  whenever it beats your Strength modifier.

  **Where you find it.** Vanilla ships a vinereaper at **iron and steel only** — the line stops at
  steel, because a farming implement is not something anyone forges out of crysteel. Mura extended it
  to nine tiers. Tiers 0–2 stay in the loot tables; **tiers 3–8 come out of them and become
  tinkerable instead.** A carbide vinereaper is no longer something you loot, it is something a
  tinker decides to make, and the recipe turns up on data disks gated by Tinkering rank like any
  other build.

  Nothing is removed. The blueprints all still exist and any save holding one is untouched — §1.1b
  freezes shipped names precisely because deleting one degrades it to a generic object with no error.
  The vibro vinereaper stays findable and tagged; it is a powered device that happens to be
  sickle-shaped, not a farm tool in exotic metal.

  This also trims six entries from vanilla's loot tables, which is the direction #386 wanted.

- **The value curve now says which categories it describes** (#373), and the validator baseline is
  **empty for the first time** — from 191 findings this morning to **zero**.

  #373 read as 22 mispriced items. Sixteen of them are not mispriced; they are categories the curve
  has never covered. The test that settles it is not whether *vanilla* follows the curve — vanilla is
  nowhere near one — but whether **this fork** ever has, since the curve is its own convention and
  `item-curve` prices only its own objects. Measured across everything priced:

  | category | on the curve |
  | -------------- | -----------: |
  | melee weapons | 63 of 73 |
  | armour | 50 of 62 |
  | **ranged weapons** | **0 of 5** |
  | **energy cells** | **0 of 4** |
  | **trinkets** | **0 of 1** |

  A rule nothing has ever followed is not a rule being broken. Ranged weapons, energy cells,
  containers and trinkets are now exempt with reasons — and vanilla agrees on the first: **none of
  its 64 missile weapons** sits on the curve, at a median of 2.5× and a range of 0 to 25.

  Two more exemptions came out of reading the items rather than their names. **An `Armor` part
  granting no AV is a slot occupier**, not armour — that is `Raven_Bio Scanner Mask` and
  `Raven_Reinforced Suspension`, both AV 0, one a face-slot scanner and the other a tread container.
  And the **nanoweave set at 300 against 320, with the mutating mask at 1000 against 1280**, are kept
  as chosen round numbers rather than flattened to satisfy a rule.

  **Exemptions are matched on part composition, not on a word in the blueprint name** — a name match
  is exactly the failure #354 removed from tier detection, and there was no reason to reintroduce it.

  Six items were genuinely mispriced and are repriced: the four `Flexi` pieces onto the curve at 160,
  after the rest of the category was accounted for.

- **This fork's share of a vanilla loot table now stops at half** (#325). Ninety-four drop weights
  across nine tables.

  | table | was | now | | table | was | now |
  | ------------------ | ----: | ----: | --- | ---------- | ----: | ----: |
  | `Armor 4C` | 65.9% | 49.1% | | `Armor 2C` | 59.3% | 50.0% |
  | `Melee Weapons 1R` | 62.5% | 50.0% | | `Armor 2R` | 57.7% | 48.8% |
  | `Armor 5C` | 61.1% | 50.0% | | `Armor 8R` | 55.8% | 49.8% |
  | `Armor 6C` | 60.0% | 49.4% | | `Melee Weapons 1C` | 55.4% | 49.9% |
  | `Armor 8C` | 54.1% | 50.0% | | | | |

  **The weights were rescaled, not flattened.** Each table is multiplied by vanilla's total over this
  fork's, so the shape inside it survives — `Armor 4C` keeps its 2:1 split between the carbide set at
  20 and the folded carbide set at 10, now 10 and 5. Flattening every entry to one number would have
  hit the ceiling just as well and thrown away a deliberate distinction.

  Worth restating, because it is the opposite of what the issue assumed: **the per-item weights were
  never the defect.** They matched vanilla's almost exactly, and in `Armor 1R` were deliberately
  lighter. Share drifted on **count** — completing every family and both handednesses puts more
  entries in a tier band than vanilla stocks, so `Melee Weapons 1R` held 6 vanilla entries against
  10 of this fork's. Capping share and keeping completeness are the same lever pulled in opposite
  directions, which is why the fix lowers per-item weight rather than dropping content.

  Half is the one number in §3.2.1 that is **chosen rather than derived** — vanilla has no opinion on
  how much of its loot pool may belong to a mod — and the section says so.

  `table-share` reports nothing and leaves the baseline, which falls to **22**: only #373's mispriced
  items remain, from a starting 191.

- **Weight is fixed where weight is the balance** (#320). Twelve items, and the per-slot factors are
  now written into `docs/STYLEGUIDE.md` §3.2.1.

  **Body armour is held to ×0.44**, its own slot median. `Fullerite Plate Mail` goes **36 → 70 lb**:
  vanilla puts it at 160 against a Strength-16 carry budget of 240 — two thirds of everything a
  character can lift, and precisely what its AV 6 is priced against. Cut to 36 it was a factor of
  **0.23**, which made that AV free. `Steel Plate Mail` 21 → 26, `Carbide Plate Armor` 27 → 20,
  `Fullerite Flake Armor` 30 → 40, `Chain Mail` 18 → 15.

  **Seven items the mod made *heavier* than vanilla go back.** That one needs no judgement: every
  slot factor is below 1, so an item gaining weight contradicts the rule whatever the magnitudes turn
  out to be. Five were short blades, leaving a line that ran **1, 1, 2, 2, 3, 1, 1, 1** by tier
  against vanilla's 1, 1, 1, 1, 1, 2, 2, 2 — noise rather than a compression.

  **The other hundred are left alone**, deliberately. #320's magnitudes waited on #176, and what
  #176 settled is that the **cliff is still the default** — graded burden ships opt-in, so the
  experience these factors are tuned against is unchanged, and under a binary threshold only the
  extremes count. The remaining items sit close enough to their slot medians that re-deriving each
  would be churn against a convention the content already follows.

  Measured factors, across the 119 merged items carrying a weight on both sides: **Body 0.44, Feet
  0.47, Hands 0.50, Head 0.57**, melee 0.60–0.75 one-handed and 0.62–0.67 two. `weight-curve` reports
  nothing and leaves the baseline, which falls to **31**.

- **Tinkering Gigantic now costs a tier that matches what it grants** (#317). `TinkerTier="7"`,
  alongside `ModNanon` and `ModSuspensor` — the top of what vanilla lets anyone build.

  Until now the merge set no tier at all, so `ModEntry` defaulted it to **1**. Nothing vanilla allows
  at tier 1 is in the same company: `ModGigantic.ApplyModification` calls `AdjustDamage(3)` on a
  melee weapon and damage is rolled **once per penetration**, so it is +3 *per penetration* rather
  than +3 flat, and it doubles energy cell capacity, grenade radius and tonic dosage besides. Every
  tinkerable vanilla mod at tier 6 or 7 carries a value multiplier of 1.3–1.5 and grants far less.

  **The capability is kept rather than reverted, because reading the code changed what the defect
  was.** #317 said Gigantic costs nothing: it costs a great deal, just not a mod slot.
  `GetSlotsRequiredEvent` does `E.Increases++`, so a gigantic item takes **one more equipment slot**
  unless the wielder is a gigantic creature — a gigantic one-handed sword needs both hands. And
  `GetAddedWeight()` is the blueprint's weight **× 4**, floored at 4, so a 6 lb greataxe becomes
  30 lb. Under graded burden that is now a cost paid every turn.

  Also corrected: the `× 3.333` value multiplier is gated on `GetIntProperty("Currency") > 0`, so it
  multiplies gigantic *currency*, not gigantic weapons. There is no money press. An ordinary item
  gets the entry's `Value="1.5"`, in line with every tinkerable vanilla mod.

  Verified rather than assumed: `ModificationFactory.LoadModNode` reads `TinkerTier` from the XML,
  and `ModEntry.TinkerTier` is `= 1` by default — so this would otherwise have shipped inert.

- **Melee damage comes back to vanilla's ceiling across all four families** (#322). Fifty weapons —
  the largest single change in the sweep, and considerably wider than the issue described.

  #322 reported the cudgel line as *"the exception"* to a mod whose new weapons are *"careful
  mirrors of their vanilla twins"*. Neither half holds. **Every family sits over its own vanilla
  ceiling**, and the mirrors were built at the raised values rather than the originals:

  | family | cells | median over | worst |
  | ------------- | ----: | ----------: | ----: |
  | Cudgel 1H | 14 | 25% | **47%** |
  | Cudgel 2H | 12 | 35% | 39% |
  | Long blade 2H | 10 | 14% | 25% |
  | Long blade 1H | 6 | 22% | 25% |
  | Axe 2H | 6 | 10% | 12% |
  | Short blade 1H | 2 | 7% | 7% |

  **Twenty-six are vanilla merges and twenty-four are this fork's own blueprints, and they pair
  up** — `Raven_Zetachrome Maceth` was 19.5 mean damage, exactly matching the raised `Cudgel8th`. One
  change expressed twice: the family was lifted, and its mirror built at the lifted value.

  The merges **drop their `BaseDamage` attribute entirely** so vanilla's own value stands, the same
  discipline `stat-discipline` enforces. The new blueprints take their vanilla twin's string —
  derived from the game rather than invented, and cross-checked by confirming the derived table
  reproduces §3.2.1's published ceiling on all 59 entries before a single edit.

  **Half of this was invisible until the check was fixed.** `damage-ceiling` resolved a weapon's
  family from the snapshot, which only covers merges — so a *new* blueprint like `Raven_Iron Mace`,
  which states no `Skill` and inherits `BaseCudgel`, resolved to nothing, found no ceiling, and was
  skipped in silence while sitting over one. It now walks `Inherits` through the mod's own files.
  That took the count from 26 to **50**.

  `damage-ceiling` now reports nothing and leaves the baseline, which falls to **38**.

- **(internal)** `Damage` and `AV` join `check_docs`' verified item-table columns, taking the count
  from 741 figures to **956**. Fifty damage cells and fifteen AV cells had to be corrected by hand
  when their blueprints moved — the third time in this sweep that a typed figure drifted because
  nothing was watching it, after `Stat` in #375.

- **The greatshield line comes down, and the tier-8 drop weights come back to vanilla's** (#319).

  The zetachrome greatshield had the **identical stat line to `Gear from the Great Machine`**, the
  best shield in Caves of Qud, at a seventh of the weight and a fifth of the price, out of a normal
  drop table. It is now AV **9** — one below the legendary.

  **The rule that settles it, now in `docs/STYLEGUIDE.md` §3.2.1: a greatshield sits one above the
  shield at its tier.** The shield line itself was already right — it matches vanilla exactly where
  vanilla ships one (3 at tier 2, 4 at 3, 5 at 5, 6 at 6, 7 at 7) and its tier-8 at 8 continues that
  into the one tier vanilla leaves empty. So only four greatshields move: **7→6, 8→7, 9→8, 10→9**.

  The issue said greatshields were *"strictly better than their own shield line — nothing is paid for
  the word great"*. Half right: they carry about **3 lb more and a flat −3 DV**. What they do not do
  is use two slots, and that turns out not to be available — a shield is `WornOn="Hand"` and a
  humanoid has two, so a two-slot greatshield means no weapon at all.

  **Shields need a ceiling per tier, not one number.** Vanilla's line is AV = tier + 1 up to tier 3
  and AV = tier from tier 5, so there is no single formula — and a flat per-slot number would let a
  tier-2 greatshield pass at the tier-8 ceiling. `armor-curve` now reads a per-tier table, with a
  test for exactly that case.

  **And the tier-8 drop weights come back to vanilla's 20**, from 43. Vanilla's four zetachrome
  pieces sit at 20 each in `Armor 8C`; this fork's five sat at 43, so the AV-10 shield was 2.15× as
  likely to appear as the `Zetachrome Lune` in vanilla's own table. That takes `Armor 8C` from
  **71.7% to 54.1%** mod content — still over half, which is #325's remaining work.

  `armor-curve` now reports **nothing at all**, and leaves the baseline entirely.

- **Best-in-slot AV comes back to vanilla's ceiling** (#318). Fifteen pieces, in three groups.

  **Four vanilla merges stop raising vanilla's own armour.** `Zetachrome Apex`, `Gloves` and `Pumps`
  go 6 → **4**, and `Zetachrome Lune` goes 10 → **8**. For Apex and Pumps the AV was the *only* thing
  the merge changed about the armour, so the whole `Armor` part is deleted and vanilla's stands —
  the discipline `stat-discipline` already enforces for `MeleeWeapon.Stat`.

  **Seven vambraces drop to AV 1** and **four cloaks to AV 2**, per `docs/DESIGN_balance.md` §9.3.
  Vanilla makes Back and Arm non-armour slots — ordinary cloaks are AV 1, and no vanilla Arm item
  exceeds 1 at any tier — and this fork had turned both into nine-tier armour lines reaching 3. The
  cloaks keep a deliberate **+1 over vanilla** so the weave line has somewhere to go; the vambraces
  do not, because the Arm slot is **worn twice** and the same courtesy there would cost four.

  Best-in-slot AV is now vanilla's in every slot but two: Back by the one point above, and Shield,
  which is #319's remaining work. `armor-curve`'s baseline goes from 19 entries to **4**.

  `docs/FEATURES.md`'s armour tables are brought back in step — **15 AV cells** were quoting the old
  values, and **nothing checks that column**, which is the same silent-drift shape as `Stat` before
  #375.

  Two things found while reading vanilla's records and filed rather than folded in: the mod also
  **rewrites vanilla's prices** through merges, unchecked, by up to −66% (#380); and the vambrace
  line is now **nine near-identical items**, which is a content question rather than a defect (#381).

### Added
- **Glaives** — a new nine-tier family, and the Axe tree's two-handed finesse weapon. **This
  completes #342**: every melee tree now offers finesse at one hand and at two (#342).

  **Why a glaive and not a halberd.** Of Pathfinder's three polearms, the glaive is the one whose
  identity survives translation to Qud. A halberd's traits are **reach** and **versatile** — Qud has
  no melee reach at all, and no per-swing damage-type toggle — so a Qud halberd is a halberd with
  both its defining properties removed. The glaive's are flavour rather than mechanism, so nothing is
  lost making one.

  **What it costs.** The greataxe's die one tier behind, the same way the quarterstaff pays the maul.
  That gives it a shape worth remembering: **a glaive hits exactly as hard as a one-handed battle axe
  one tier above it.** It is also the lightest two-handed axe at every tier.

  I should say plainly that neither the glaive nor the spear carries `finesse` in Pathfinder — the
  two-handed finesse weapons there are both elven. Tagging these two is my call, resting on the rule
  that a finesse weapon is light for its class, not on an imported trait.

  **The art is mine** — `mod/Textures/items/Vixy_Glaive.png`, a broad single-edged blade with a
  back-spur at the socket, so it reads as a chopping weapon beside the spear's thrusting point.

  **One knock-on, and it is the third time.** The tier 0–1 melee tables were full again — `Melee
  Weapons 1C` at 197 of 197 and `1R` at 120 of 120 after the spear. Fitting the bronze and iron
  glaives in meant scaling this fork's own entries down a third time, so tier-0 weapons now sit at 12
  where Mura left them at 16. Vanilla's entries are untouched throughout and every table stays under
  the cap #386 set, but the low-tier melee pool is now demonstrably saturated: three families in a
  row have had to buy their way in.

- **Spears** — a new nine-tier family, and **the first two-handed weapon the Short Blades tree has
  ever had** (#342).

  **Why it exists.** Short Blades was the only melee tree in the game with no two-handed weapon at
  all — Cudgel has 17, Long Blades 10, Axe 10, Short Blades none. That matters because Single Weapon
  Fighting's cost is your offhand: it zeroes every non-primary attack while toggled. A two-handed
  weapon has already given the offhand up, so the cost is largely pre-paid — and a short-blade
  specialist was the one build that could never take the skill cheaply. Now it can.

  A spear read as a short blade on a long pole is a stretch by weapon group and sound by shape, and
  Pathfinder's elven branched spear — two-handed, finesse — is the precedent for the combination.

  **What it does.** It carries the `Finesse` tag, so with the Short Blade tree's Finesse power bought
  its penetration rolls use your Agility modifier whenever that beats Strength. Damage sits at the
  midpoint between the dagger line and the two-handed long sword line at each tier: better than a
  dagger, never as good as a greatsword. It is the lightest two-handed blade at every tier.

  It is **not** throwable, although Pathfinder's spear is and Qud's whole dagger line carries
  `ThrownWeapon`. The two-handed spear exists to fill a build gap, not to do a second job as well.

  **The art is mine** — `mod/Textures/items/Vixy_Spear.png`, the first item tile this fork has drawn.
  One 16×24 sprite recoloured across all nine tiers: the head and the butt-ferrule take the tier's
  colour, the haft stays wood.

- **Quarterstaves** — a new nine-tier family, and the Cudgel tree's two-handed finesse weapon
  (#342).

  **Why a staff.** Pathfinder files both the staff and the bo staff in the **club** group, which is
  where the Cudgel tree's weapons come from, and tags each one `monk` — and monk is the trait that
  has always meant Dexterity. 5e says it outright: Martial Arts lets a monk use Dexterity instead of
  Strength for attack *and* damage with monk weapons, and the quarterstaff qualifies. So the staff is
  the two-handed cudgel a precise fighter was always supposed to use.

  **What it costs.** It deals **the maul's die one tier behind** — a bronze quarterstaff hits for
  1d3 where a bronze maul hits 2d2, and a zetachrome one for 3d6 against 4d6. That is what the
  finesse buys, and it is how both tabletop systems price a staff against a maul. It is also the
  lightest two-handed cudgel at every tier, which is the rule §3.2 now states: a finesse weapon is
  light for its class.

  Wood rather than metal, so a "carbide quarterstaff" is a heartwood shaft with carbide ferrules,
  which is what a shod quarterstaff has always been. It ships on the game's own staff tile and wood
  swing sound.

  **One knock-on worth stating.** The tier 0–1 melee loot tables were already at this fork's share
  cap — 196 of a permitted 197 in `Melee Weapons 1C`, and 120 of 120 in `1R`. Fitting the bronze and
  iron quarterstaves in meant scaling this fork's own existing entries there down by 10–15%, so a
  handful of other low-tier mod weapons are now marginally rarer. Vanilla's entries are untouched;
  the cap is what #386 set, and it is not being bent.

- **Finesse is now sold by all four melee trees** — Axe and Cudgel join Short Blade and Long Blade
  (#342).

  **What you buy.** `Finesse`, 250 skill points at Agility 19, on the same terms as the two trees
  that already sold it: penetration rolls use your Agility modifier whenever it beats your Strength
  modifier, for a weapon carrying the `Finesse` tag. The weapons those two powers apply to arrive in
  later changes — the vinereaper and glaive on the axe side, the mace line and quarterstaff on the
  cudgel side — so buying it today does nothing yet.

  **Why the reversal.** #321 left Axe and Cudgel Strength-only and called the halberd and war hammer
  the two most genre-inverted assignments in the mod. That still holds for those two weapons, and
  neither gets the tag. What changed is the reading of the trees themselves: vanilla describes the
  vinereaper as *"moulded to a crescent for scything the rough hides of watervine"* — a sickle, and
  Pathfinder's sickle carries finesse. Pathfinder's finesse bludgeon is likewise a mace-family
  weapon; the warhammer never carries it. So both trees do have a genre-legitimate finesse weapon.
  It was simply not the one the mod had picked.

  **This also settles the skill regating**, which had been deferred. Twelve Axe and Cudgel powers were
  relaxed to `Strength|Agility` by Mura, and with those trees Strength-only the relaxation was close
  to inert — an Agility character could buy Cleave or Slam but had nothing in the tree that rewarded
  the investment. Now they do. The regating stays, and it means something.

  `docs/DESIGN_balance.md` §3.3 records the correction that made this possible: *"finesse never
  coexists with two-handed"* is **5e's rule, not the genre's**, and this document had mistaken one
  for the other. Pathfinder's elven branched spear and elven curve blade are both two-handed and
  both finesse. The replacement rule is that **a finesse weapon is light for its class** — which is
  the same principle that sets the mace line a pound below the war hammers.

- **The psionic chips are repriced, the four steep passives made rare, and the Guardian starting
- **(internal)** `docs/DESIGN_balance.md` §3.10 records the direction on #342: **the Axe and Cudgel
  duplicate families get real differentiators**, and the skill-regating question **waits on that
  design** rather than being answered first. Deferred deliberately — it is a project across four
  nine-tier families, not a tidy-up.

  The premise strengthened while the issue sat open. Re-derived after #321 and #322 landed, **7 of 21
  pairs are byte-identical** on damage, penetration bonus, cap, weight and value, and 12 more differ
  by a single pound. #322 equalised the damage that used to sit alongside the weight offset, so the
  only signal left is the one §3.10 already called the weakest.

  Two things recorded so they are not rediscovered. **Retiring the duplicates was never an option** —
  §1.1 freezes blueprint names, and any save holding one would break on load. And **the regating is
  not inert**, contrary to how #342 framed it: it lowers the attribute minimum to *buy* a power, and
  Cleave's effect does not depend on the penetration stat, so an Agility build can buy Cleave and
  swing an axe — just badly. A reduced benefit rather than a dead one.

  kits fixed** (#338, and it closes #316). The largest content change of the balance sweep, and a
  player-facing one.

  **108 of the 144 chips move onto the chip curve**, `1.25 × 2^tier` — a quarter of the item curve,
  because chips are not equipment: their slot competes with nothing and **they cannot be bought**,
  living in `Artifact 3`–`8` while village tinkers stock `Artifact NR`. Tier 6 goes 20 and 40 → 80,
  tier 7 goes 40 → 160, and **a perfected chip goes 60 → 320**. The 36 basic chips at 20 were
  already on it.

  **`HeightenedSpeed`, `PhotosyntheticSkin`, `Regeneration` and `ElectricalGeneration` drop from
  weight 3 to weight 1** in all three chip tables — 0.227% to **0.081%** per artifact roll, or 305
  rolls to 854 for a coin flip. Each table total falls 120 → 112, so every other chip gets
  marginally commoner, which is the intended trade.

  **All nine Guardians lose the basic neutral body chipset**, replaced by neutral mind. That chipset
  carries `HeightenedSpeed`, so every martial subtype opened the game at +15 Quickness from a
  *generic* chipset that is nobody's affinity — against `docs/DESIGN_balance.md` §5.9's rule that **a
  subtype starts with its own affinity, not a generic chipset carrying someone else's steep
  passive.** Their mental mirror chip becomes precognition, because neutral mind already grants
  `MentalMirror` and duplicates stack (#350). Still three chips and five mutations.

  **What this does not do.** The Quickness chips stay in the catalogue: removal was the only dial
  reaching below their `13 + 2 × Level` floor of +15, and a Mutated Human can take Heightened
  Quickness at chargen for 4 of 16 mutation points, so the chip is the non-mutant's route to the same
  thing. The affinity cases stay too — a Light Psionic opening with `PhotosyntheticSkin` is its
  affinity expressing itself.

  `item-curve`'s baseline shrinks from 130 entries to **22**, which are the non-chip items #373
  carries.


- **(internal)** `docs/PERMISSION.md` §9 records **Mura's approval to absorb the Grand Bazaar and
  the Experience Curve**, given on Discord on 18 August 2026. That answers the question §8.4 left
  open, and unblocks #174 and #175 on permission — everything else those issues list still stands.

  Two details worth more than the yes itself. **The option-gated shape was part of the question**, so
  it is the form the permission was given in rather than something added afterwards. And **Mura kept
  the mods separate for want of capability, not preference** — *"I didn't have the knowledge to set
  everything up that way in a single mod"* — which is the exact thing twelve working options and a
  validator that checks their wiring now supply.

  §9.1 closes a second question: **there are no Noble Lark sprites in the Grand Bazaar**, *"just the
  base mod"*. §8.2 records those sprites as the one item still needing chirps' own confirmation, and
  it does not reach the Bazaar. I have not asked the same of the Experience Curve, and §9 says so
  rather than assuming.

- **(internal)** The last three of #337's checks — `damage-ceiling`, `weight-curve` and
  `table-share` — and the snapshot that makes them possible in CI.

  All three compare against **vanilla**, which CI does not have. A merge is opaque without it: it
  carries no `Inherits` and usually no `Skill`, so `Cudgel8th` cannot be recognised as a cudgel from
  this mod's own XML at all. Since **25 of the 26 damage violations are merges**, a check without
  vanilla's side would have caught 1 of 26 while appearing to cover damage — worse than no check.

  So `tools/qud-api.json` gains **`merged_records`** (213 entries) and **`table_weights`** (56),
  holding vanilla's answer for exactly the records this fork edits. Scope is the point: `CITED_FIGURES`
  already stated the rule that file is kept to — *"a list of citations, not a dump of the game"* —
  and every entry here exists because this mod merges that record. Its `_comment` claimed **"names
  only"** while already holding 28 figures; it now states the citation rule instead, which is the
  principle actually being followed.

  A consequence worth knowing: **adding a new merge means regenerating the snapshot**, which needs
  the game. That is the intended shape — a new merge is a new citation, and a record the snapshot has
  never seen makes its check fail loudly rather than skip in silence.

  What they find: **26** damage cells over §3.2.1's per-family ceiling, worst the cudgel line at 47%
  (#322); **7** merges that made a vanilla item heavier, five of them short blades (#320); and **9**
  vanilla tables past half, worst `Armor 8C` at 71.7% (#325). Each figure matches what the #340
  derivation found independently.

  `CURVE_EXEMPT` now covers damage as well as price, so cybernetic fists and vibro weapons are
  exempt from both for the reasons already recorded there.

  Nine more tests, each proving its check in both directions, with fixtures that write their own
  snapshot so a test cannot start passing because vanilla changed. All 191 findings are baselined
  against their governing issues.

- **(internal)** Three of the checks #337 asked for, plus a fourth column in `check_docs`. The
  balance sweep's twenty findings all accumulated without failing anything; these are the durable
  half of fixing that.

  **`armor-curve`** holds AV against §3.2.1's per-slot ceiling, shields included on their own
  `Shield` part. It reports **19** — the four vanilla merges from #318 (`Zetachrome Apex`, `Gloves`,
  `Pumps` and `Lune`), the four shields from #319, the eight vambraces, and the four cloaks the
  cloaks-stay decision caps at 2.

  **`stat-discipline`** holds `MeleeWeapon.Stat`, and the two halves are different rules. A new
  weapon may state Strength or leave it unset — the field is initialised to `"Strength"` and vanilla
  omits it on 208 of its 402 declarations, so requiring it would report 28 correct weapons; what is
  refused is any other value, which is the entire defect class. A **merge states nothing at all**,
  which is stricter on purpose: CI has no game, so it cannot tell a merge restating vanilla's value
  from one changing it, and the second is the defect. It reports **0** — one redundant
  `Stat="Strength"` on the `Chute Crab Claw` merge was removed rather than baselined, since a merge
  restating vanilla changes nothing by definition.

  **`finesse-visible`** holds a `Finesse` tag and its rules text to implying each other, in both
  directions. A tag with no text is a feature the player cannot discover — which is exactly how #366
  was found, from a play session whose only symptom was a dagger that said nothing. Text with no tag
  is a promise the game does not keep. It reports **0**.

  And **`Stat` joins `ITEM_COLUMNS`** in `check_docs`, taking the verified item-table figures from
  739 to 741. When #365 reverted 61 `Stat="Agility"` declarations, 65 table cells still said Agility
  and nothing failed.

  Twelve tests, each proving its check in both directions. The 19 `armor-curve` findings go into
  `tools/validation-baseline.json` against #318 and #319 — reported, tracked, and not failing the
  build, so every fix from here has a check to satisfy rather than a prose rule to remember.

- **(internal)** Graded burden is played and confirmed, so `docs/FEATURES.md` §13 and §14 say so
  rather than saying it is untested. All five behaviours the pull request left open check out —
  including the one with no compile-time proof, that **an existing save picks the part up on load**.
  That case is the entire reason `Vixy_BurdenAttach` carries two hooks: `[PlayerMutator]` fires only
  at character creation, and `CallAfterGameLoaded` only inside `XRLGame.LoadGame`.

- **Graded burden** — carrying weight becomes a gradient instead of a cliff (#176). **Off by
  default**, per charter rule 6: it is a genuinely new opinion this fork introduces rather than
  anything the mod already was.

  Vanilla has one threshold and nothing underneath it. Capacity is `15 × Strength`; exceed it and
  `Overburdened` makes you unable to move, and below it nothing happens at all — so the best play is
  to sit at 99% forever and never think about weight again. Four bands now fill that space: **−1 DV**
  at half capacity, **−2 DV** at three quarters, and **−4 DV, −10 Quickness and no running** at nine
  tenths. Vanilla's cliff is untouched and still stops you dead at full.

  **The cliff stays where it is on purpose.** Moving it to 125%, as the original spec proposed, is
  only possible by inflating `GetMaxCarriedWeightEvent` — and that figure is read by seven UI
  surfaces and by **Pack Rat**, which forces a character to stay above 90% of whatever capacity
  reports. Inflating it would pin a Pack Rat character permanently in the worst band. Leaving the
  cliff alone costs one band and has no blast radius.

  **Player only**, matching vanilla, where `IsOverburdened()` returns false for every non-player at
  any load. **Safe to toggle mid-run**: the band is derived from carried weight each turn and the
  effect stores nothing, so it adds nothing to the save.

  Two items from the spec could not be built, and neither was a shortcut. There is **no stealth
  system in Caves of Qud** — the word appears nowhere in the assembly — and there is no movement-cost
  hook, so *"movement costs double"* would have to be spent through Quickness, which is the penalty
  the band already applies. A fatigue rider waits on #179.

  Worth keeping for whoever touches this next: the run block vetoes **`ApplyRunning`**, not
  `CanChangeMovementModeEvent`. Refusing the latter is how vanilla's `Overburdened` blocks flight, so
  it looks like the model — but that event's `To` carries the movement *message name*, `"sprinting"`
  by default and configurable per `Run` part. Matching on `"Running"` would never have fired, and the
  restriction would have shipped silently inert.

- **(internal)** `docs/STYLEGUIDE.md` §3.2.1 carries the four curves the balance sweep was missing —
  AV, damage, weight and mod share of a loot table — derived from the installed game rather than
  chosen (#340). `docs/DESIGN_balance.md` §9 records what the derivation turned up, which is more
  interesting than the rules.

  **Vanilla has ceilings, not curves.** The premise was "AV per slot, per tier"; across 224 armour
  pieces the values overlap so heavily that there is nothing to match — tier-4 body armour runs AV 0
  to 5. What vanilla has is a clean ceiling per slot, and that is what the findings turn on anyway.
  Two tighter rules were tested against the data and **rejected**: `AV + DV` capped per tier is not
  monotone, and `AV + DV >= 0` is broken by 14 vanilla pieces. Either would have failed real items.

  **A humanoid has two Arm slots**, so Arm armour is worn twice and its AV counts twice. Nothing had
  accounted for that. It makes the vambrace line worth 6 AV — more than head, hands or feet — and it
  restates best-in-slot as 26 → 40 for ordinary items, or 33 → 43 counting named artefacts. #316's
  "32 → 48" is neither, because that issue never said which basis it used.

  **Settled: cloaks stay at AV 2, vambraces go back to flavour at AV 1.** Vanilla makes Back and Arm
  non-armour slots; this fork had turned both into nine-tier armour lines, which is most of why
  best-in-slot climbed. Keeping the cloaks costs exactly +1 AV against vanilla's best loadout.
  Extending it to vambraces would cost 4 more, and unlike cloaks there is no vanilla Arm item above
  AV 1 to point at.

  **And the drift is one defect wearing three hats.** Of the 26 damage cells over vanilla's ceiling,
  25 are vanilla blueprints the mod merged into — `Cudgel3`–`8th`, `Long Sword6`–`8th`,
  `Battle Axe6th`–`8th`, `Dagger7` — and only `Raven_Iron Mace` is this fork's own. The AV ceiling
  rises the same way, on `Crysteel Shardmail`, `Zetachrome Lune` and the zetachrome set. §3.2's rule
  that *a merge never changes vanilla's* was written for `Stat`; it turns out to describe nearly
  everything the sweep found, and #337's checks should be built around that shape.

  Table share is the one number that is chosen rather than derived — vanilla has no opinion on how
  much of its loot pool may be a mod's — and §3.2.1 says so. It also found **#325's list is
  incomplete**: nine tables sit above half, not six, and the worst is one it misses at 71.7%.

- **Finesse** — a purchased power that lets an Agility character get damage out of a blade (#321).

  **Before:** 61 melee blueprints declared `Stat="Agility"`, so rapiers, katanas, daggers,
  vinereapers, halberds and war hammers rolled penetration against Agility with nothing bought and
  nothing given up. **After:** every one of them rolls against Strength, as all 402 of vanilla's own
  `MeleeWeapon` declarations do, and the crossover is a power you buy.

  `MeleeWeapon.Stat` is not a damage stat — it names the stat penetration rolls against, and the
  damage die is rolled **once per penetration**, so it multiplies a weapon's whole output. Agility
  already supplies melee to-hit on every weapon with no exemption, and DV. Scaling penetration off it
  too made one attribute do three of melee's four jobs — and Agility is the gun stat, so a rifle
  build was getting better stat-scaling in melee than in its own specialty, having paid nothing.

  **What you buy.** `Finesse`, 250 skill points at Agility 19, sold once each by **Short Blade** and
  **Long Blade**. It rolls penetration against your Agility modifier whenever that beats your
  Strength modifier. **Tagged weapons:** daggers, knives and wristblades on the short blade side;
  rapiers and katanas on the long. Axe and Cudgel stay Strength-only, which reverses the two most
  genre-inverted assignments in the mod — the halberd and the war hammer.

  **What it costs you.** 250 sits level with Rejoinder and Shank and below En Garde!'s 300. For
  comparison, vanilla's `Penetrating Strikes` handles the same event for 200 and grants a whole extra
  penetration — stronger than Finesse at every armour value — but it switches off your entire
  offhand. Finesse has no loadout cost, and it refunds the 8 attribute points that reaching a +4
  Strength modifier would take, into a stat that also buys DV and to-hit.

  Two implementation notes worth keeping. One class per tree, never a shared one — `PowersByClass`
  keeps only the first entry for a given `Class`, which is how #11 broke Akimbo. And the `Finesse`
  tag on `BaseDagger` inherits to **51 melee blueprints**, 24 of them vanilla daggers and knives;
  that reach is deliberate — 5e gives the dagger `finesse` too — but it is one line changing a lot of
  vanilla, and worth seeing as such.

  `docs/STYLEGUIDE.md` §3.2 carries the rule, and `docs/DESIGN_balance.md` §3 the reasoning,
  including the D&D 5e and Pathfinder comparison.

- **(internal)** `docs/STYLEGUIDE.md` §3.2 gains the four conventions the balance sweep settled but
  had not written down. This is #340 split in half: these four were *decided* by questions one and
  three and cost a paragraph each, while the AV, weight, damage and table-share curves have to be
  **derived** from vanilla's values first. Bundling them held the cheap half behind the expensive
  one, and it was blocking #321, #338 and #354.

  **`MeleeWeapon.Stat` is `Strength` on every new weapon, and a merge never changes vanilla's.** A
  weapon meant to reward Agility carries a `Finesse` tag instead, and the crossover is bought as a
  power in the Short Blades or Long Blades tree. Counted while writing it: vanilla declares
  `MeleeWeapon` 402 times — 191 `Strength`, 208 unset, 3 `Ego`, and **`Agility` never**. This bullet
  **replaces one that said the opposite** —
  §3.2 described Agility-scaling vinereapers, halberds, rapiers, katanas and war hammers as a
  deliberate theme, which is exactly what §3.9 decided to revert. Until now the styleguide endorsed
  the behaviour the sweep's largest fix removes.

  **Chips run a quarter of the item curve at `1.25 × 2^tier`** — 20 · 40 · 80 · 160 · 320 across
  tiers 4–8 — because their slot competes with nothing and they cannot be bought, so rarity is the
  access dial and price only sets what an unwanted chip sells for.

  And the two principles: **the chip system controls access and price, vanilla controls what a
  mutation is worth**; and **a subtype starts with its own affinity**, never a generic chipset
  carrying someone else's steep passive.

  `docs/DESIGN_balance.md` §7 is re-sequenced around the split.

- **(internal)** Two additions to `docs/LESSONS.md`, both from closing an issue by accident in #360.

  The **closing-keyword** entry gains a third and fourth shape. Its examples were a denial and a narration; this
  one is **delegation** — *"No closing keyword — … I would rather you close #339 than have a merge do
  it."* The sentence declares the absence of a keyword and then contains one nine words later, in the
  clause asking a human to do the closing by hand. Asking for something to be done manually is not a
  way of telling the parser not to do it automatically.

  The fourth arrived while writing the third: **quoting an example arms it.** The pull request
  documenting the mistake reproduced the offending sentence verbatim, in its body and its commit
  message, and registered the same issue again. The entry's examples now mask their issue numbers,
  because a bug report about a live wire is still a live wire.

  And a new entry, **"The check you drop is the one that was working."** The command that would have
  caught this is prescribed two sections above, by me, after it caught two earlier closures. I ran it
  on five consecutive pull requests, found nothing, stopped, and the sixth closed an issue I had
  explicitly written that I did not want closed. Five clean results were the check working, not
  evidence it was unnecessary — and what made it stoppable was the work becoming routine, which is
  also when nobody reads their own boilerplate.

  #361 follows from it: charter rule 4 says to keep checks in the script rather than in prose, and
  this one is still a habit.


- **(internal)** The balance sweep's fourth and last question is settled: **fix in place, add no new
  options** (#339, and it answers #336). `docs/DESIGN_balance.md` §6 records it, and **all four
  questions are now closed** — what remains is implementation.

  The decision is mostly forced by a constraint rather than chosen. All eleven shipped options work
  by mutating a small loaded record — a `GenotypeEntry` field, a `PowerEntry`, an anatomy, a
  population table. Item stats are not that shape: an option would have to carry **183 blueprints and
  386 individual values**, and it **cannot read vanilla's back**, because once Qud merges the mod's
  XML the in-memory blueprint holds the mod's value and vanilla's exists only in the game's own files
  — which charter rule 5 bans reaching. So the switch means 386 hardcoded numbers duplicating a
  dataset that drifts on every Qud patch, with nothing able to check it.

  What *is* gateable mostly already has an option: skill requirements, chip slots and chip drops all
  ship with one today.

  The charter points the same way. Rule 6's exception is for a change that *grants* power with no
  content attached, and every fix here **removes** power and moves toward vanilla. The circular catch
  #339 was filed with is also gone: questions one to three produced stated conventions, so once #340
  writes them into §3.2, most of the sweep becomes a defect fix under rule 2's lower bar.

  **What it obliges instead** is on the changelog. With no switch to fall back on, every fix has to
  state its before and after rather than just its reason, and the sweep wants landing across a
  version boundary players can see rather than trickling into patch releases.


- **(internal)** Question three of the balance sweep is **fully settled** — its fourth and last
  decision covers starting chips (#338), recorded in `docs/DESIGN_balance.md` §5.9.

  Two corrections to how it had been framed. **All eighteen subtypes start with three chips granting
  five mutations**, not just the Guardians; and for scale, **vanilla hands out zero cybernetic
  implants in starting gear**, across every caste and calling.

  It collided with the decision before it: §5.3 made the four steep permanent passives three times
  rarer to find, and starting gear hands one to **12 of the 18 subtypes**. The rule that separates
  the deliberate cases from the accidental one:

  > A subtype starts with its own affinity, whatever that affinity contains. It does not start with
  > a *generic* chipset carrying someone else's steep passive.

  So a Light Psionic keeps `PhotosyntheticSkin` — that is its affinity — and what goes is the
  **Neutral Body chipset in all nine Guardian kits**, the only reason every martial subtype opens at
  +15 Quickness. It is replaced by the Neutral Mind chipset, whose reflect-block-displace is closer
  to what a Guardian is; the Mental Mirror chip already in the kit becomes a Precognition chip so the
  duplicate does not stack.

  Flagged for an in-game check: the **Light Guardian** starts with `PhotosyntheticSkin` *and*
  `HeightenedSpeed`, two independent Quickness sources that look on the code like they stack.


- **(internal)** Question three's third decision is settled — **price and rarity, not rank** (#338).
  `docs/DESIGN_balance.md` §5.3 records it.

  First, a fact that changes what price can do: **chips cannot be bought.** They live in
  `Artifact 3`–`8`, consumed only by `ChestBuilders.BuildSpecialChestInventory`, while village
  tinkers stock `Artifact NR`, which carries none. So price sets what an unwanted chip *sells* for
  and rarity is the access dial. Both are in scope, but they do different jobs.

  **A stated chip curve** goes into `docs/STYLEGUIDE.md` §3.2 at a quarter of the item curve —
  `1.25 × 2^tier` — with its reason written down, in the style of `CURVE_EXEMPT`'s vibro entry: chips
  are not equipment, their slot competes with nothing, and they cannot be bought. That reprices 108
  of the 144; the basic single chips at 20 are already on it. A perfected chip goes 60 → **320**.

  **The four steep permanent passives become jackpots.** `HeightenedSpeed`, `PhotosyntheticSkin`,
  `Regeneration` and `ElectricalGeneration` drop from weight 3 to weight 1 in all three chip tables —
  0.227% to **0.081%** per artifact roll, or 305 rolls to 854 for a coin flip. The other chips get
  marginally commoner as the table total falls from 120 to 112, which is the intended trade.

  **And the Quickness pair stays.** Removal was the only dial reaching below their +15 floor and it
  is not taken: a Mutated Human can take `Heightened Quickness` at chargen for 4 of 16 mutation
  points, so the chip is the non-mutant's route to the same thing and pricing that route is what is
  in scope. The floor is accepted as a consequence of the mutation's own vanilla design.


- **(internal)** Question three's second decision is settled, and it gives the chip system the
  principle it was missing (#338):

  > **The chip system controls access and price. Vanilla controls what a mutation is worth.**

  The question was which of the five 100%-uptime physical passives should have their granted rank
  capped, since a level of `HeightenedSpeed` — always on — is worth far more than a level of
  `AdrenalControl2`, which grants the same Quickness at a tenth of the uptime on the same ladder.

  The answer is **none of them**. Two principles collide: §5.1's compensation says physical
  mutations get more ranks because they cannot gain any from Ego, and uptime says permanent passives
  are worth more per rank. What breaks the tie is that **every one of them is a vanilla mutation** —
  a mutant with `Regeneration` at rank 10 gets exactly what a chip user does, so re-tuning it through
  the chip ladder would be second-guessing Qud's own mutation design by proxy. That is the same
  argument that settled decision one.

  So no `Tier` value changes, and the remaining question widens from "the Quickness pair" to **all
  seven permanent passives**, with price and rarity as the whole answer rather than one dial of
  three. Worth noting for that: `Regeneration` at rank 10 is +110% healing against `NocturnalApex`'s
  +10% for two licence points, and `ElectricalGeneration` at rank 10 is 1,000 charge per turn against
  the mod's own Solar Cell Nexus at 50.


- **(internal)** The first of question three's four decisions is settled: **the chip ladders stay as
  they are** (#338). `docs/DESIGN_balance.md` §5.1 is rewritten around it.

  The reason is that the Ego gradient is **vanilla's mechanic, not this mod's**. `Mutations.xml`
  declares `Stat="Ego"` once on the Mental category and `BaseMutation.CalcLevel` applies it to every
  mental mutation in the game, chip-granted or inherent. Mura's only decision was the size of the
  3/6/10 compensation, and overriding the gradient would mean suppressing behaviour far wider than
  the chips.

  Worth recording that the compensation is **exact precisely where it does not matter**. Below
  character level 18 the rank cap flattens every ladder to equality; above it they come apart, by +5
  ranks for a dedicated caster and **−2 to −3 for a low-Ego Guardian**. And two of those ranks are
  drift rather than reward: `AddAttributeBonus` raises every attribute at levels 6, 12, 18, 24, 30
  and 36, so Ego climbs whether a player invests in it or not. Vanilla's chargen maximum of 24 is a
  starting line, not a ceiling, and it applies to every genotype rather than being anything the
  Psionic Adept has.

  The finding carried forward is the Guardian column: they use *physical* chips, which are flat at
  rank 10 forever, so §5.8's plateau lands hardest on the subtypes with no way out of it and #350's
  duplicate stacking is currently their only escape.


- **(internal)** #354 records that **all 144 psionic chips are off `docs/STYLEGUIDE.md` §3.2's value
  curve** — a perfected chip is a tier-8 item priced at 60 water where the curve says 1,280 — and
  that `item-curve` cannot see them. The check finds an object's tier by matching a **material word**
  in its blueprint name, so anything not named after a metal is skipped before its price is compared,
  even when it carries an explicit `Tier` tag. That is the more general defect, and the chips are 144
  instances of it.


- **(internal)** `docs/DESIGN_balance.md` §5.8 models the three genotypes' **mutation power across a
  whole run**, which turns out to be shaped almost entirely by a cap nobody had accounted for.
  `GetMutationCapForLevel(level)` is `level / 2 + 1` and clamps the sum of every source, identically
  for every genotype.

  Three phases follow. **Below character level 18 the cap binds everyone equally** — a perfected chip
  and a mutant's grown mutation are the same rank — so the Psionic Adept's advantage there is *count,
  not rank*. **Level 18 is its peak**, because the cap reaches 10, which is exactly a perfected
  chip's grade. **Above 18 it plateaus while a mutant keeps climbing**, since `1 MP = 1 rank` has no
  ceiling below the cap and a single chip's grade is its ceiling.

  So the Adept is front-loaded breadth that plateaus, against a mutant that starts level and ends
  deeper — a coherent shape, and one no document stated. Its ledger is a real trade too: the fewest
  stat points in the game (34 against 38 and 44), half the True Kin's cybernetics licence, the lowest
  HP gain and no mutation points, bought with +10 skill points per level and two extra chip slots.

  #350 is filed for the exception: chip levels **sum** before the cap, so two perfected chips of one
  mutation track the cap indefinitely. That is the only way a chip build scales past level 18, and
  nothing documents it.

- **(internal)** `docs/DESIGN_balance.md` §5 now carries the **complete costing of all 36 mutations
  the psionic chips grant**, at every grade, read from the decompiled classes rather than from the
  documentation (#338). The question itself is still open; three structural findings are not.

  **The stated rationale is correct, and calibrated.** The 3/6/10 physical ladder compensates for
  mental mutations continuing to scale with Ego from a chip, and they do — the scaling lives in
  `BaseMutation.CalcLevel`, applied per *category* from `Mutations.xml`, where `Mental` carries
  `Stat="Ego"` and `Physical` carries nothing. A chip-granted mental mutation's effective level is
  `chip grade + EgoMod`, so **the two ladders converge exactly at Ego 24** — the Adept's stat
  maximum — and diverge either side of it.

  **The ladder is keyed on the wrong property.** What decides a level's worth is whether a cooldown
  caps it, and the five permanent passives — the ones that receive the largest levels — have 100%
  uptime. `AdrenalControl2` grants Quickness like `HeightenedSpeed` does, at 10% uptime, on the same
  ladder.

  **And no ladder reaches the Quickness pair.** `GetSpeedBonus` is `13 + 2 × Level`, so level 1 is
  already +15 against vanilla's best item at +10 for 10,000 water. The floor is the problem.

- **(internal)** `docs/LESSONS.md`'s entry on reading a decompiled loop's tail now records the tell I
  missed. The wrong model's *first* symptom was not the absurd number in the output table — it was a
  Monte Carlo run that could not terminate, sat backgrounded for seventeen hours pinning a core, and
  looked exactly like a job still working. A background task producing no output is indistinguishable
  from one making progress, and a job that prints only at the end has no liveness signal at all.

- **(internal)** Question two of the balance sweep is settled: **the weight compression is a method,
  not noise, and it belongs in `docs/STYLEGUIDE.md` §3.2** (#320). `docs/DESIGN_balance.md` §4
  records it.

  Testing each slot against a single factor found that **61 of the 109 re-weighted items already
  follow one cleanly** — melee one-handed at ×0.67, two-handed at ×0.62 and hands at ×0.47 have a
  mean deviation under 1 lb and not a single item more than 2 lb off. That is the same shape #248
  found in the greathammers: vanilla's own curve, compressed and carried across.

  Two places it was not applied. **Body armour**, where six of eight sit off the slot's factor and
  the spread collapsed from vanilla's 4.6× to 2.4× because the heaviest item was cut hardest — which
  matters because Fullerite Plate Mail at 160 lb is **two-thirds of a Strength-16 character's entire
  carry budget**, and that is vanilla's one real weight decision. And the **short blades**, which are
  not a compression at all: five got heavier, leaving a line that runs 2, 2, 3, 1, 1, 1 by tier.

  The magnitudes wait on #176, because a gradient and a cliff want different numbers — under today's
  binary `Overburdened` a heavy item is free until it is catastrophic, so only the extremes matter.
  That dependency is narrower than it sounds: #340 covers six curves and only weight is affected,
  and every slot factor is below 1, so the seven items the mod made *heavier* contradict the rule
  whatever the magnitudes turn out to be.

- **(internal)** Question one of the balance sweep is settled: **Agility scaling becomes a purchased
  power rather than a property baked into blueprints** (#321). Every melee blueprint reverts to
  `Stat="Strength"`; a `Finesse` tag marks which weapons may cross over, and a power sold by Short
  Blades and Long Blades decides whether you may. `docs/DESIGN_balance.md` §3.9 records the design
  and §3.1–§3.8 the reasoning.

  Three things decided it. Mura's notes describe **three skill changes and no weapon changes**, so
  the 20 vanilla-weapon `Stat` swaps sit outside every document they left. Vanilla is rigid here —
  Strength is the only stat in Qud that scales weapon damage, on 4,351 of 4,354 melee weapons, on
  thrown, and on the only two bows that scale at all. And Agility is the gun stat while guns have no
  penetration stat of their own, so the swaps gave a rifle build better stat-scaling in melee than
  in its own specialty.

  Splitting the licence from the weapon is Pathfinder's answer rather than D&D's, and it fits
  because **Qud already works that way** — accuracy crosses over free on every weapon, damage does
  not. It also reverses the two most genre-inverted assignments in the mod, since the halberd and
  the war hammer go back to Strength.

  The C# is a nine-line variation on a class Freehold already ships,
  `SingleWeaponFighting_PenetratingStrikes`. One class per tree rather than one shared class,
  because `SkillFactory.PowersByClass` keeps only the first entry for a given `Class` — which is
  exactly how #11 broke Akimbo.

- **(internal)** `docs/DESIGN_balance.md` — a balance audit of the whole mod against vanilla, and
  the reasoning behind it. Twenty findings are filed and indexed under
  [#315](https://github.com/vixygrey/qud-expanded-community-edition/issues/315); nothing is changed
  yet, and four questions are open.

  Four of the findings are blatant by the plainest test there is: **vanilla already prices the same
  effect, and prices it far higher.** A perfected Heightened Quickness chip grants +33 Quickness for
  60 water, where vanilla's only two Quickness items are legendaries at +10 for 8,000 and 10,000.
  Best-in-slot AV rises 32 → 48 while the loadout's weight halves. The zetachrome greatshield has
  the same stat line as the Gear from the Great Machine at a seventh of the weight.

  The document's §2 is the part worth keeping regardless of what gets changed: the combat, armour,
  chip and tinkering mechanics **verified against the decompiled game** rather than inferred from
  field names. `MeleeWeapon.Stat` names the penetration stat rather than a damage stat, and
  penetration multiplies damage; Agility supplies melee to-hit on every weapon with no exemption;
  every body part holding a weapon generates its own attack. Each of those changes what a
  reasonable fix looks like, and none of them is what the field names suggest.

  **The finding under the findings is that the checked conventions held and the unchecked ones did
  not.** `docs/STYLEGUIDE.md` §3.2's value curve and tier→material table are followed everywhere,
  because `item-curve` fails CI when they are not. Every number that drifted — AV, weight, damage,
  drop weight — is a number §3.2 does not mention. So the sequence starts by writing those curves
  down (#340) rather than by changing values, and the validator checks that would hold them (#337)
  are the durable half of the work.

### Fixed
- **`docs/FEATURES.md` §4 still described Finesse as a two-tree power** (#423).

  #342 sold Finesse in all four melee trees, added the `Finesse` tag to vinereapers, glaives, maces
  and quarterstaves, and wrote all of it into the changelog and into each family's own §6.2 heading.
  The §4 callout that *explains* Finesse was not touched, so the document said **"added to the two
  blade trees"** and **"Axe and Cudgel stay Strength-only"** while its own weapon headings said
  `(Axe, two-handed, Finesse)` two hundred lines below.

  It now carries the table of which weapons actually take the tag, and says why the halberd and the
  war hammer deliberately do not — that was never a claim about the trees, and #321's reading of
  those two weapons still stands.

  **Nothing checked it, and nothing easily could.** `check_docs.py` holds figures against the mod; a
  sentence naming which trees sell a power is prose. It was found by reading FEATURES to write the
  wiki page that cites it.

- **The README's own figures were wrong, and the check that should have caught them had gone
  silent** (#422).

  It advertised **348 new blueprints** against a real 400, and **eleven options** against twelve.
  `docs/FEATURES.md` §13.1 described the *eased skill requirements* option as covering "the twenty
  retuned attribute requirements" when it restores fifteen — #421 moved four powers out of that
  table and the sentence stayed.

  All three are figures `check_docs.py` was written to hold, and all three drifted anyway. Why is
  the interesting part, and it is below.

- **(internal)** `check-names` checks both directions, and `docs/STYLEGUIDE.md` gains **§10.1, a
  registry of every check name** any script in `tools/` can report (#402).

  It only ever verified that a name a document *calls a check* exists — the mistake #100 made,
  writing `reachability` where the validator emits `unreachable`. The reverse went unchecked, and it
  is the quieter half. **A documented name that does not exist is loud** the moment anyone follows
  it: they run the validator, grep the output, find nothing. **An emitted name nobody documented is
  silent** — the inventory simply reads as complete when it is not.

  `dead-chip-grade` shipped unlisted in #347 and I caught it by hand while adding a neighbouring row.
  Measuring properly found **fifteen** names in that state, most of `check_docs.py`'s own and all six
  of `check_build_log.py`'s.

  **§10 was the wrong place to enforce it.** That table maps *rules to enforcers*, so a check guarding
  something other than a style rule legitimately has no row — and it names things that are not checks
  at all, like `ruff` and `prettier`. Demanding a row there for all 49 would have invented a rule the
  document never claimed, which is the reasoning `check_item_tables` already uses about its own scope.
  So §10.1 is a separate, explicitly complete registry, and the check reads that section by its
  heading rather than the whole page.

  Both failures are covered by tests that build a synthetic registry, and one more guards the
  vacuous pass: if the heading ever moves, a section it cannot parse would otherwise make every emitted
  name a finding or none of them one.

  `qud-api-snapshot` is listed with a note. Several checks emit it when the API snapshot is missing or
  has lost a list they need, so it is a shared failure mode rather than a check of its own — and a
  contributor who meets it still needs somewhere to look it up.

- **The last four outliers of the balance sweep** (#334, #333, #328, #329) — and with them, the
  inherited-defect ledger is **empty for the first time**.

  **All 51 grenades carry vanilla's prices again** (#334). The fork had flattened every one to
  10/20/30, which erased **three** distinct ladders vanilla uses: 20/30/40 for the twelve common
  lines, 20/20/20 for the four that deliberately do not scale by grade, and **30/40/50** for fire
  support and time dilation. That is two separate signals — which throwables are premium, and which
  gain nothing from a higher grade — and it is most of how a player learns them. The merged grenade
  economy goes back from 1,020 to **1,470**.

  **`Rhinox-Skull Maul` gives back its extra penetration point** (#333). The issue said nothing else
  in the mod touches penetration; in fact **84** blueprints do, and every one of them is 1 — as is
  every one of the **28** weapons vanilla ships that a player can equip and that carry a `PenBonus`,
  including `Gimeleth` at 12,000 water and `Fist of the Ape God`. The high numbers in the game's data
  are on cherubic claws and astral tabby bites, not equipment. At 2 it was the only exception in
  either catalogue.

  Its weight stays at 10 against vanilla's 25: `weight-curve` permits a merge to lighten, and §3.2.1
  holds the non-body slots to the rule rather than the number. And the **Ironweave Cloak keeps its
  demotion** from tier 4 to 1 — iron is tier 1 in this fork's material table, and #380's value rule
  was already written around exactly this case: a merge keeps vanilla's value *unless it also
  re-tiers*.

  **`Raven_Drum Shotgun` fires 10 rather than 24** (#328). Vanilla's ceiling across 65 missile
  weapons is the `Swarm Rack` at 10, and its two shotguns fire 8 — so 24 was three times the best
  shotgun in the game, at the same tier, for less money. It is **10 shots for 2 ammo** now, which
  keeps the drum's real trade (five shots a shell against vanilla's eight) under a ceiling vanilla
  sets, and **125 water** rather than 75, above the Combat Shotgun it out-bursts.

  **`Raven_Fine-Tuned Handgun` costs 750 rather than 600** (#329), matching `LightLock`, the cheapest
  vanilla pistol at its tier — the others are 1,050 and 1,200. Its accuracy of 1 is **left alone**: it
  sits inside vanilla's tier-6 range rather than beyond it, since `Nullray Pistol` is 0. Its drop
  weight of 2 in `Missile 4` is untouched, as #284 and #286 set it deliberately.

- **(internal)** `tools/validation-baseline.json` is **empty**. It has tracked inherited debt since it
  was written; the 22 `item-curve` rows were cleared by #373 and the 47 `merge-value` rows by #334,
  and verified stale by running the validator with the ledger removed entirely — it still reports
  nothing. An empty ledger means every violation the validator can report is a new one, which is the
  state it was always meant to reach. The file and its comment stay, because the next inherited defect
  will want somewhere to go.

- **A solar cell no longer pays for a psionic shot every turn, the dark matter cell weighs what its
  capacity is worth, and the cell rarity ladder runs the right way up** (#323, #326).

  **The loop.** `SolarArray` produces its rate in charge every turn while you are outdoors in
  daylight. The solar cell nexus produced **50**, and a psionic pistol costs **50 a shot** — so
  daylight paid for one shot per turn, indefinitely. Vanilla's own ratio is a laser pistol at 100
  against a solar cell making 10: **ten turns of sun per shot**.

  Vanilla ships exactly one solar cell and its rate is **10**, so 25 and 50 were invented figures.
  Both fork cells are 10 now, which leaves **capacity** as the thing that separates them — as it
  separates every cell vanilla ships.

  | | charge per shot | solar per turn | turns of sun per shot |
  |---|---:|---:|---:|
  | vanilla: laser pistol + solar cell | 100 | 10 | 10 |
  | **was**: psionic pistol + nexus | 50 | 50 | **1** |
  | **now**: psionic pistol + nexus | 50 | 10 | 5 |

  **The dark matter cell held the mech power core's charge in a pocket.** Vanilla's portable ceiling
  is the antimatter cell at 200,000; the only 500,000 cell in the game is the mech power core, at
  **70 lb**. It keeps the 500,000 and now carries the 70 — a power source you install somewhere
  rather than one you pocket, which is the trade vanilla already priced.

  **And the rarity ladder was upside down.** Vanilla's rule shows up as soon as entry tier is read
  against capacity — more charge is rarer *and* later:

  | cell | charge | enters | drop weight |
  |---|---:|---|---:|
  | chem (vanilla) | 10,000 | Ammo 4 | 25 |
  | **advanced chem** | 50,000 | Ammo 5 | 20 → **10** |
  | nuclear (vanilla) | 100,000 | Ammo 6 | 5 |
  | antimatter (vanilla) | 200,000 | Ammo 7 | 1 |

  The advanced chem cell was **four times commoner than a nuclear cell holding twice as much**, and
  twenty times commoner than antimatter. The recharging cells run their own ladder beside that one,
  and were inverted the same way: the solar array goes 10 → **5** against vanilla's solar cell at 10,
  and the nexus 5 → **1**, sharing Ammo 7 with antimatter. Both ladders are monotone now.

  **What did not change**: the psionic guns' prices. `item-curve` records that ranged weapons follow
  no value curve in this fork *or* in vanilla — 0 of 5 here, and vanilla's own 64 missile weapons
  miss it too — so there is nothing to reprice against, and inventing an anchor is what #380 settled
  against.

- **(internal)** `docs/FEATURES.md`'s energy-cell table is checked against its blueprints. It gained
  Weight and Drop weight columns, and naming the first column `Blueprint` brings it under
  `check_item_tables` — which immediately caught a figure that had been wrong for some time: the dark
  matter cell was documented at value 300 against a blueprint saying **1200**. Checked item-table
  figures go from 1,136 to 1,145.

- **Chip-granted flaming ray and freezing ray could not be used at all** (#411). Reported by a
  player, and it is the first defect in this fork found by someone playing rather than by an audit.

  The symptom was *"Your is too damaged to do that"* — and the missing word is the whole diagnosis.
  The game builds that sentence as `"Your " + BodyPartType + " is too damaged to do that!"`, so the
  gap is a **null body part rendered into the message**.

  Both mutations derive the body part they fire from out of a chosen *variant*.
  `BaseMutation.Create` calls `SetVariant` **only when a variant is supplied**, and the stock chip
  base class passes `null` — so the derivation never ran. The mutation's own fallback looks like it
  should cover this and does not: it assigns the `Variant` field directly rather than going through
  `SetVariant`, so the body part stays unset even once a variant exists.

  **12 blueprints were affected** — three flaming ray chips, three freezing ray chips, and the three
  grades of each of the Fire and Ice chipsets. Every other chip in the catalogue is fine: 34 of the
  36 mutations this mod grants have no variants at all.

  Both parts now pass their variant — `Ghostly Flames` and `Icy Vapor`, each the only one its
  mutation has, both worn on the hands — and then rebuild the body's default equipment, which is what
  registers the slot and creates the object. Setting the body part without that would have moved the
  failure rather than fixed it.

  **Vanilla never reaches this**, which is why it survived: its only three items using that base
  class are the Enigma Cone, the Enigma Cap and the Leyline Puppeteers, granting Confusion and
  Temporal Fugue — neither has variants.

  Worth noting where this leaves the two families: with #347, Fire and Ice each had **two of their
  three mutations defective**. Kindle and Frost Webs ignored their grades; these two did not work at
  all.

- **(internal)** Three checks learned C# shapes they had never seen, all introduced by #411's fix and
  all reported against correct code:

  - `serializable-shape` read an **expression-bodied property** as an instance field. `=>` members
    have no backing storage and reach no save, so they are now skipped — while a real field, and a
    static one, still behave exactly as before.
  - `unknown-mutation` read the **type parameter** `T` in a generic base as a mutation name and
    reported that nothing declares it. Type parameters declared on the enclosing class are now
    excluded, and #226's actual defect is still caught through the same file.
  - `check_docs`'s Appendix B matched only the stock base class name, so both ray chip lines
    **silently stopped resolving** to a blueprint. That is the quieter failure of the two: a row that
    matches nothing rather than a figure that disagrees.

  A finding reported against correct code is how a check trains people to ignore it, so each fix
  narrows the check rather than widening what it tolerates.

- **The Support Battalion's skill grant is the trade it always claimed to be, and three
  undocumented skill cuts go back to vanilla** (#330, #331).

  **`Temporal, Support Battalion` granted 22 skills and 2,075 skill points.** Vanilla's most generous
  caste is `Priest of All Suns` at 7 and 700; the median is 5 and 450. It also opened *every* base
  weapon tree, which is why it had no weapon identity of its own.

  Its `extrainfo` states a trade — *"Starts with massively lowered Intelligence in exchange for so
  many skills"* — so the fix is to make that arithmetic rather than a claim. `Leveler.RollSP` is
  `(Intelligence − 10) × 4` per level, so **−6 Intelligence costs 24 a level, about 720 across a
  run**. Vanilla's ceiling of 700 plus the 720 it pays is ≈1,400, and that is what it grants now:
  **15 skills, 1,400 points** — still the most in the game, and paid for exactly.

  What went is the specialist weapon trees: Multiweapon Fighting, Heavy Weapon, Long Blade, Pistol,
  Shield, Short Blade and Acrobatics. What stayed is the whole support kit — the Tinkering line,
  Scavenger, Cooking, Physic, Persuasion, Customs, Wayfaring, Endurance, Self-discipline, Tactics —
  plus a sidearm and a long arm. A support unit is not master of every weapon in the battalion.

  **`Mental, Guides of the Lost` came down with it**, 12 skills / 825 SP to **10 / 700**, which is
  vanilla's ceiling exactly. It loses the firearm tree, which a guide has no call for, and the one
  terrain lore vanilla itself prices below the rest.

- **(internal)** Three skill changes nothing documented now track vanilla whichever way the
  *eased skill requirements* option is set (#331).

  That option carried six changes. Three are **documented intent** in Mura's notes and stay optional:
  the Axe and Cudgel powers accepting Strength *or* Agility, `En Garde!` needing 29 in either rather
  than 29 and 23 in both, and Multiweapon Expertise and Mastery at 21 and 25.

  Three had **no record anywhere**: Tinker I / II / III cut from Int 19 / 23 / 29 to 17 / 21 / 25,
  `Disassemble` made free against vanilla's 100, and — which #331 did not itself catch — `Long Blade`'s
  `Dueling Stance` cut from Int 17 to 15. Tinkering is the tree that converts into every other kind
  of power, and Tinker III at four attribute points cheaper is most of a build's investment.

  **An option offers a choice between two things somebody meant.** Drift is a defect, and a defect
  does not get a switch, so these are simply vanilla's now — the option no longer mentions them, and
  neither does its helptext.

  **That took two goes** (#421). #331 removed the three from `Raven_Options.cs`'s tables and stopped
  there, leaving `mod/Skills.xml` still declaring the cut values — so they went on shipping, and
  because the option no longer named them they could no longer be switched off either. The sentence
  above was true of the option and false of the mod for as long as both were in `[Unreleased]`.
  `mod/Skills.xml` now leaves all five attributes unset, so vanilla's own numbers stand.

- **Cybernetic implants are vanilla's again, elemental resistance can no longer reach total
  immunity, and the credit pass grants what vanilla's best wedge grants** (#335, #327, #332).

  Three issues, one resource, and they had to be settled together — because the way they combined
  was worse than any of them alone.

  **The thing that made it serious is that implants stack.** `CyberneticsOneOnly` is the only gate
  on duplicates and it is per-blueprint; vanilla tags 17 items with it and the dermal platings and
  insulations are not among them. `Slots="Body,Head,Back"` is **three distinct body parts**, and
  each implant adds its stat again with no cap. So every printed number here was really three times
  itself.

  | | vanilla | was | now |
  |---|---:|---:|---:|
  | best plating, three slots | +3 AV | **+12 AV** | +6 AV |
  | high-grade insulation, three slots | +27 | **+60** | +27 |
  | elemental resistance, caste + implants | 42 | **100** | 47 |

  **100 is not a large number, it is the end of the scale.** Resistance applies as
  `(100 - resistance) / 100`, so a Full Psionic caster's +40 on top of three insulations at +20
  multiplied those paths to zero — and the caste's own −20 drawback was repaid three times over by
  the same implants. That combination needed two of these issues to exist and neither one to be
  wrong on its own.

  **What changed.** Eight merged implants go back to vanilla's costs and effects: `DermalPlating`
  (3 points, +1 AV), both insulations, both ankle tendons, `CherubicVisage`, `OpticalMultiscanner`
  and `CrysteelHandBones`. Two of those merges are **deleted outright** — once the numbers are
  vanilla's, the merge changes nothing by definition.

  The fork's own plating line is re-scaled to **+1 / +2 / +3**, so the best three slots give +6
  rather than +12 — twice vanilla's ceiling instead of four times it. It is priced on the stacked
  total now, which is the number that was never being read.

  The nine Full Psionic casters drop to **20 / −10**, which is the scale their own Guardian half has
  always used, and **no longer grant a licence point** — vanilla's genotype is the only source of
  those in the whole game.

  The **cybernetics credit pass** grants **3** credits at **450** water, which is vanilla's
  `CyberneticsCreditWedge3` exactly. It granted 10, and a credit is a licence tier: one drop was five
  times a starting True Kin's entire licence, repeatable from a tier-8 table.

  **What did not change**: the True Kin licence stays at 4 against vanilla's 2, deliberately — it is
  chargen power rather than a ceiling, and the ceiling was the problem. Implant costs are untouched.

- **(internal)** `sync_mod.py --zip` builds the release asset, so the last unguarded step in the
  release stops being assembled by hand (#314).

  Everything else in a release has a guard: `--publish` refuses a dirty tree or a branch,
  `validate_mod.py` ties the manifest to the changelog, `check_docs.py` and the pool snapshot run on
  every commit. **The one step where a person assembled a file by hand was the one that ships to
  players** — and non-Steam players install nothing else.

  Three ways it went wrong, two of them silent:

  - **A stale build.** The zip was built from the *install directory*, which may hold a `--dev` build
    from testing, or a `--publish` from before the version bump. Nothing about the file looks wrong.
  - **The source tree.** Zipping the repository produces something plausible and much larger, which
    is #312 in a different form.
  - **The folder name.** The install directory is `qud-expanded-community-edition`; every published
    zip contains `QudExpandedCommunityEdition`. So the `cp -R` was not a copy, it was a **rename**,
    and it read as ceremony.

  `--zip` removes all three by construction. It builds from `mod/` rather than the install directory,
  so there is no copy in between to go stale. It reuses `copy_tree`, so the archive holds exactly what
  a `--publish` install holds and no path is ever typed. And both names come from `manifest.json` —
  the archive from `version`, the folder inside from `id` — so the rename is something the tool knows
  rather than something you remember.

  It applies the `--publish` guards and runs the validator first, and **`--tag vX.Y.Z` refuses to
  build unless the tag agrees with the manifest version** — the third side of a triangle
  `docs/RELEASING.md` step 3 explicitly said it could not check.

  **Verified against the real thing**: run against the `v2.5.1` tag it rebuilds the shipped 2.5.1
  asset **byte for byte, all 81 files, identical file list**.

  `docs/RELEASING.md` and the release issue template now point at it, and the two verification
  commands #312 added are **deleted rather than kept** — a stale build cannot happen when the archive
  is assembled from `mod/` at the commit the guards just verified, and zipping the source tree cannot
  happen when no path is typed. A check you can delete because its failure became unreachable is the
  best outcome a check can have.

- **The Arm slot goes back to being the Arm slot: vambraces stop costing dodge, and wristblades pay
  for the extra attack they buy** (#381, #324).

  **What the slot is.** Vanilla puts 28 armour items on the Arm, and they are Kindrish, the
  Transkinetic Cuffs, Kah's Loop, the scanning bracelets — utility artifacts. None grants more than
  **AV 1**, and **not one of the 28 carries a negative DV**; the values are 0, 1 and 2, and the
  median weight is a pound.

  **The vambraces broke both.** Seven of the nine imposed a dodge penalty the slot has never had —
  the column ran −1, 0, −2, −1, 0, −3, −2, −1, 0, which is noise rather than a progression — and they
  weighed 2 to 6 lb. Both were chosen per item, which `docs/STYLEGUIDE.md` §3.2.1 already forbids.
  All nine are now **AV 1, DV 0, 1 lb**.

  That leaves nine items separated only by price, and **that is the intended answer rather than a
  loose end**. The Arm slot is for utility artifacts; a vambrace is what you wear until you find one.
  Giving the line a stat ladder would invent a category vanilla does not have in that slot.

  **The wristblades are the other half.** They attack from the Arm slot, and the game walks every
  body part looking for a weapon, so two arms plus two hands is **four attack attempts a round**.
  That mechanic is vanilla's. What this fork changed is availability: vanilla ships exactly one
  wristblade, at one tier, which is a find rather than a build — and prices it at **full parity with
  the dagger of its tier**, because it never had to price a build. Nine of them is a build.

  So the line now runs at about **60% of the dagger's damage**, a deficit of a third to a half:

  | tier | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
  |---|---|---|---|---|---|---|---|---|---|
  | dagger | 1d2 | 1d3 | 1d4 | 1d6 | 1d8 | 1d10 | 1d12 | 1d12+1 | 1d12+2 |
  | **was** | 1 | 1d2 | 1d3 | 2d2 | 2d3 | 2d3+1 | 2d4 | 2d4+1 | 2d6 |
  | **now** | 1 | 1d2 | 1d2 | 1d3 | 1d4 | 1d6 | 2d3 | 1d8 | 2d4 |

  The zetachrome wristblade goes from a mean of 7.0 to **5.0**. Tiers 0 and 1 keep a smaller deficit
  because 40% off `1d2` has nowhere to go.

  `ArmDagger4` moves with them, to `1d4`. It is the one place this fork overrides a vanilla weapon's
  damage, and leaving it at vanilla's `1d8` would have made the merged item **80% better than its own
  tier-mates**. Worth being plain that #380's "a merge keeps vanilla's value" covers price and
  resistances, where the snapshot can prove what vanilla said; damage is held to a per-family ceiling
  instead, so this is allowed by the rules as they stand rather than in tension with them.

  **And a warning the family badly needed.** `docs/FEATURES.md` now says that **Single Weapon
  Fighting turns wristblades off, and it defaults to on** — while that ability is toggled on, every
  non-primary body part's attack chance is multiplied by zero, so the wristblades make no attacks at
  all. That is vanilla's behaviour and it applies to an off-hand weapon just the same, but a
  character who buys the skill and then straps on wristblades sees nothing happen and has no obvious
  reason why.

- **(internal)** `check_docs.py` checks the **DV** column of the item tables (#381). It covered tier,
  value, weight, stat, damage and AV — #337 named those — and DV was simply never on the list, so
  flattening the vambrace line left nine stale cells that nothing reported. The checked figure count
  goes from 1,068 to 1,136.

- **A Mutated Human no longer gets a Chip Interface slot** (#353, deciding #352).

  **Why it was there.** Nobody chose it. Vanilla's Mutated Human is `BodyObject="Humanoid"`, so the
  merge that gives every humanoid *NPC* a slot handed the mutant player one as a side-effect.

  **Why it goes.** Three reasons, each enough on its own. It contradicts what this system is for —
  `docs/FEATURES.md` §3 says chips grant mutations *"to genotypes that cannot mutate"*, and a mutant
  can. It was never a decision. And it inverts the power curve: a chip's level is a tracker that sums
  with a mutation's inherent `BaseLevel` before the rank cap, so the mutant's base keeps climbing
  while a chip alone stops at its grade.

  | character level | mutant, inherent + 1 chip | Adept, best single chip |
  |---:|---:|---:|
  | 25 | rank 13 — **+39 Quickness** | rank 10 — +33 |
  | 30 | rank 16 — **+45** | rank 10 — +33 |

  One slot on the genotype that already mutates beat four on the genotype the chips were built for.

  **What else changes.** The chargen panel no longer promises the mutant a slot, which would
  otherwise be #275's defect arriving from the other direction. The option
  *"your own Chip Interface slots"* is now **"True Kin Chip Interface slots"**, because that is all
  it governs; it still defaults on and still gives a True Kin two.

  **Existing characters keep theirs.** A body is built once, at character creation, so a Mutated
  Human already in a save keeps the slot and anything worn in it. Nothing is orphaned — the
  `Chip Interface` type string stays declared for the other two anatomies, and `Bodies.xml` is
  untouched, so every humanoid NPC still has one.

  **This is a straight fix rather than a new option**, following #339: item-shaped opinions get
  options, defects that contradict a stated convention do not, and what is gateable here already had
  its option. `docs/FEATURES.md` §13 flags that option as due a re-check in game, since the
  2026-08-16 pass no longer covers what it does.

- **(internal)** `docs/LESSONS.md` records the fourth instance of the closing-keyword trap, and it is
  the only one where the check from #361 was present and still did not cover it.

  #403's body explained the defect by quoting #360's sentence, and the quotation put a closing verb
  next to an issue number — so GitHub resolved it, and that pull request carried a link to an issue
  it had no business touching. The check passed correctly: there was no stated intent for the link to
  contradict, only a quotation. The manual look caught it, about thirty seconds after I had written
  in the same body that the check cannot see this case.

  Two facts the entry did not have before. **The reference resolves from commit messages as well as
  the body** — fixing the body alone changed nothing, because the commit carried the same quotation,
  and only re-checking showed it. And **a document describing the trap cannot quote the trap**: the
  way out is to describe the offending sentence rather than reproduce it, which is what the entry had
  been doing all along without saying so.

- **(internal)** CI fails a pull request that says it only *advances* an issue while carrying a
  closing link to it (#361).

  `docs/LESSONS.md` has prescribed `gh pr view --json closingIssuesReferences` since #292, and a
  habit is a check with an expiry date: I ran it on five consecutive pull requests, found nothing,
  stopped, and the sixth closed #339 with a sentence that read *"No closing keyword — … I would
  rather you close #339 than have a merge do it."* Charter rule 4 is explicit about where that
  belongs — **"Keep new checks in the script rather than in prose."**

  [`tools/check_pr_intent.py`](tools/check_pr_intent.py) compares the two machine-readable halves:
  an issue named after `Part of`, `Advances` or `Why … stays open` — the three forms `LESSONS.md`
  prescribes — must not also appear in `closingIssuesReferences`. It runs in the **PR conventions**
  job, so no new required check and no new job.

  **It catches all three instances this repository has recorded** — the denial in #286, the
  narration in #292 and the delegation in #360 — and its tests hold those three bodies in their own
  words, because a regular expression over prose that quietly stops matching would be worse than no
  check at all: it would retire the manual habit too.

  It is a script rather than a step body for the same reason. `LESSONS.md` now says both that the
  check exists and that the manual look still matters, since a body carrying a closing reference and
  saying nothing either way states no intent to contradict.

- **(internal)** `skip-changelog` works whenever it is applied (#346). The changelog gate reads
  `github.event.pull_request.labels`, and `labeled` was not in the workflow's trigger list — so
  applying the label after the run fired could never satisfy it: no new run, and a manual re-run
  replays the original payload, which was captured before the label existed. The check stayed red
  with the label visibly applied, which is what `CONTRIBUTING.md` promises it will not do.

  The workflow already documented this exact trap for the title check, which is why `edited` is
  there. Labels have the same problem and did not get the same fix. `unlabeled` is in the list too,
  so removing the label re-runs the gate rather than leaving a stale exemption.

- **(internal)** `validate_mod.py` holds a merge to vanilla's value and resistances (#380). This is
  the check the revert in the same issue argued for, and it is the second half of the blind spot
  #354 fixed for tier detection — **both halves of `item-curve` skipped vanilla-named objects, and
  only one of them should have.**

  `merged_records` in `tools/qud-api.json` gains **`value`** and **`resistances`**, so CI can tell a
  merge that restates vanilla's price from one that changes it. Without the snapshot a merge is
  opaque: it carries no `Inherits`, and CI has no game to look the record up in.

  The exception is stated rather than assumed: **where the merge also re-tiers the item the reprice
  stands**, because there the price follows a derived tier rather than replacing a decision vanilla
  made. Re-tiering licenses a price and nothing else — a resistance has no curve to derive from, so
  it is refused either way.

  Run against the tree as it stood before the revert, it reports **88** — the 80 prices and the 8
  resistance fields, exactly what was reverted.

  **The 47 grenades and 3 cybernetic implants go into `tools/validation-baseline.json`**, tagged to
  #334 and #335. Listed as known debt rather than exempted in the check, deliberately: an exemption
  would have made them invisible, and closing either issue now means clearing its rows.

- **(internal)** `docs/STYLEGUIDE.md`'s check inventory gains rows for `merge-value` and for
  `dead-chip-grade`, which shipped undocumented in #347. `check-names` verifies that a documented
  name *exists*; nothing verifies that an emitted check is documented, so a new check can ship
  unlisted in silence. Caught by hand this time.

- **Vanilla's own prices are vanilla's again on 80 merged items, and two zetachrome pieces get
  their resistances back** (#380).

  **What was wrong.** This fork applied its value curve to vanilla blueprints through merges. I
  found four by hand; the audit found **142 of the 213 merges**, moving the merged economy from
  44,476 to 33,459 — about **25% cheaper**, 124 items down and 18 up. `item-curve` could not see any
  of it, because it prices only `Raven_` and `Vixy_` objects on the rule that vanilla sets its own
  values. That rule is right for a new item and exactly wrong for a merge that rewrites vanilla's.

  **The measurement that settled which way to go.** The case for keeping them was that vanilla is
  inconsistent with its own economy — `Zetachrome Lune` at 6,000 against a tier-8 curve of 2,048.
  It is not. Hold the slot fixed and vanilla's body armour runs a 1.1x price spread at tier 5, 1.5x
  at tiers 6 and 7, and 1.1x at tier 8, where the Lune's only peer is the Flange from the Great
  Machine at 6,666. Vanilla is coherent at the top. This fork's curve is a different slope — above
  vanilla at tier 1, a third of it at tier 8 — so it was competing with vanilla's ladder rather than
  repairing it.

  **What changed.** 80 merges give their price back, including the four ranged weapons, which the
  curve should never have reached at all — `item-curve` already exempts ranged weapons on the
  grounds that neither this mod nor vanilla has ever priced them by tier. Highlights:

  | blueprint | was | now |
  |---|---:|---:|
  | `Zetachrome Lune` | 2,048 | **6,000** |
  | `Flawless Crysteel Shardmail` | 1,024 | **1,900** |
  | `Crysteel Shardmail` | 512 | **1,200** |
  | `Laser Rifle` | 550 | **750** |
  | `Battle Axe8` | 1,280 | **1,500** |
  | `Vibro Dagger` | 300 | **120** |

  And `Zetachrome Gloves` goes back to 6/6/6/6 elemental resistance from 5, `Zetachrome Lune` to
  11/11/11/11 from 10. Both were undocumented nerfs, and no curve claims resistances.

  **What did not change.** The 12 merges where this fork also re-tiers the item keep their new
  price, because there it follows a derived tier rather than replacing a decision vanilla made —
  `Carbide Boots` stays tier 3 at 40 against vanilla's tier 4 at 150. The grenades stay as they are
  under #334 and the cybernetics under #335, which own those two economies. And every item this
  fork adds is still priced by the curve, unchanged.

  **What it costs, since it is visible in play.** A family holding both new and merged items no
  longer steps evenly. Four pairs now run a higher tier at no more money, and ten tiers hold a fork
  item and a vanilla one at different prices — tier-5 boots are 160 new and 195 merged. Two of those
  four pairs are vanilla's own flat step, reproduced faithfully. `docs/STYLEGUIDE.md` §3.2 states the
  rule and accepts the unevenness.

- **(internal)** `validate_mod.py` refuses a chip line that grades a mutation which cannot level
  (#347). This is the guard the fix in the same issue argued for.

  **Why nothing caught it the first time.** `unknown-mutation` passed, because `Kindle` and
  `FrostWebs` are genuinely declared in the catalogue. `item-curve` passed, because every price sat
  exactly on the chip curve for its tier. The defect was only visible inside the mutation's own
  method body, and no check could reach one.

  So `tools/qud-api.json` gains **`non_leveling_mutations`** — 44 of the game's 130 mutation classes
  return a constant `false` from `CanLevel()`. Neither `Mutations.xml` nor `HiddenMutations.xml`
  carries an attribute for it, so it comes out of `Assembly-CSharp.dll` through
  `tools/dump_part_members.cs`, which already reads that file's metadata for part members. Reading a
  method body is still metadata rather than decompilation: `return false` compiles to two IL bytes,
  `ldc.i4.0` then `ret`, so the test is a two-byte comparison. I checked it against a full ilspycmd
  decompile of the same assembly — **44 out of 44, no drift in either direction**.

  The check groups blueprints by the set of mutation-granting parts they carry, which is what makes
  a line a line: the three Kindle chips must agree with each other, and the three Fire chipsets form
  their own group, because a chipset grants a lower level than the single chip on purpose. Run
  against the tree as it stood before the fix it reports all four lines and names the blueprints;
  against the tree after, nothing.

  **What it does not do** is find more of them today. Cross-referenced against all 36
  `ModImprovedMutationBase<T>` subclasses in `Scripting/`, exactly two match, and both are now
  fixed. This is a guard against the next one — a chip added for a mutation that turns out not to
  level, or a Qud patch that stops one levelling.

  It needs the snapshot regenerating with `--assembly` after a Qud update, like everything else in
  that file, and a snapshot that has lost the list fails loudly rather than passing quietly.

- **The kindle and frost webs chips had three grades that all granted the same thing, and the top
  one cost sixteen times the bottom one** (#347).

  **What was wrong.** `Kindle` and `FrostWebs` are the only two of the 36 mutations the chips grant
  that override `CanLevel()` to `false` — Kindle's cooldown and range are constants, Frost Webs sets
  its range and area as literals. Neither reads its level anywhere. So a perfected frost webs chip
  granted exactly what the basic one did, and after #338 repriced the catalogue it asked **320 water
  for what 20 buys**. Nothing in the item said so, because the description line is written by
  vanilla's `ModImprovedMutationBase` from whatever level the chip claims to give.

  **Before → after.** All six chips now say the same true thing:

  | | before | after |
  |---|---|---|
  | basic / upgraded / perfected kindle chip | 20 / 80 / 320 water · Kindle 2 / 4 / 6 | **20 / 20 / 20 · Kindle 2** |
  | basic / upgraded / perfected frost webs chip | 20 / 80 / 320 water · Frost Webs 3 / 6 / 10 | **20 / 20 / 20 · Frost Webs 3** |
  | all three display names, each line | basic / upgraded / perfected | **one name — "kindle chip", "frost webs chip"** |
  | fire chipset's Kindle component | 1 / 2 / 3 | **1 at every grade** |
  | ice chipset's Frost Webs component | 2 / 4 / 6 | **2 at every grade** |

  The chipsets keep their prices. Two of their three mutations still scale, so the price is still
  earned; only the dead component's stated level changes.

  **The blueprints all stay.** `docs/STYLEGUIDE.md` §1.1b freezes a shipped blueprint name, and
  removing one degrades any copy already in a save to the generic `Object`, silently. Three
  blueprints under one display name is the honest description of three identical items, and their
  item tiers still differ, which is what keeps each in its own loot pool.

  **What did not change**: the tooltip's phrasing, which is vanilla's; the drop tables; and the
  other 34 chip lines, which all grant mutations that do scale. I checked — those two are the only
  ones, against 44 non-levelling mutations in the game's catalogue.

- **(internal)** `docs/FEATURES.md` §3.3's chip price table still said 20 / 40 / 60 (#347). #338
  moved the catalogue onto the chip curve and the table was not updated with it; the figures are now
  20 / 80 / 320 for single chips and 80 / 160 / 320 for chipsets. Nothing checks that table —
  `check_docs.py` verifies Appendix B's 144 rows, not the summary above them.

- **(internal)** `check_docs.py`'s Appendix B check keys on **(display name, item tier)** rather
  than the display name alone (#347). A display name is not unique — #347 made three blueprints
  share one — and the old key let them overwrite each other, so the appendix could describe only
  whichever parsed last. No row changed meaning; six now exist that could not before.

- **(internal)** `docs/FEATURES.md` §3.2 records that **chip levels sum** on a mutation the
  character already has, and why that is left alone (#350). It is vanilla's own behaviour: the
  Enigma Cone and Enigma Cap both carry `ModImprovedConfusion` at Tier 3 on different slots, so the
  base game ships a deliberate stacking pair. The rank cap `level / 2 + 1` then holds this mod to
  the same ceiling of two useful sources — a third chip is worth nothing below character level 38.
  Working in `docs/DESIGN_balance.md` §5.8.
- **(internal)** `CONTRIBUTING.md` and `docs/RELEASING.md` say where an issue closed *without*
  shipping goes on the board: **straight to Done**.

  The columns were documented for work that ships — QA, then Staging, then Done once a release is
  cut. Nothing covered a report whose premise turns out not to hold. #364 was the first, and it had
  nowhere correct to sit: it cannot wait in Staging, because nothing about it will ever appear in a
  release, and leaving it in On Deck counts dead work as upcoming.

  So Done means *out of the pipeline* — released for anything that was built, immediate for anything
  that will not be — and the close reason (`not planned` against `completed`) is what tells the two
  apart. `RELEASING.md` says so too, since its "everything in Staging becomes Done" step would
  otherwise read as the only way in.


- **(internal)** `item-curve` now finds an item's tier from its **`Tier` tag**, falling back to the
  material word in its name only for the objects that predate the tag (#354). The order used to be
  the other way round, so anything not named after a metal was skipped before its price was ever
  compared — a clean green run over content nobody had checked.

  It was reported as 144 invisible psionic chips. It is **130 violations across 166 objects**: 108
  chips off the chip curve, and **22 other items nobody had filed**, from
  `Raven_Large Sphere of Negative Weight` at a twelfth of curve to `Raven_Cryocannon` at nearly five
  times it. #354 predicted exactly this — *"the chips are 144 of them; there may be others"* — and
  #373 now carries the 22, including the three groups where the honest answer may be an exemption
  rather than a reprice.

  Two smaller corrections came with it. Chips are priced on **§3.2.1's chip curve** at `1.25 × 2^tier`
  rather than the item curve, so the check now measures them against the right rule instead of
  skipping them. And **base objects are no longer priced** — `Raven_Base Psionic Pistol` carries
  `Tier` 3 and names no metal, so it was invisible here by accident rather than by rule, and nothing
  spawns a template.

  All 130 ship in `tools/validation-baseline.json`, reported but not failing, with the governing
  issues named. The ledger only shrinks.

  Six tests cover the new behaviour, and three of them were **checked against the old code first**
  to confirm they fail there. A test that passes before and after proves nothing, which matters
  especially here: the defect being fixed is a *skip*, and a check that skips is indistinguishable
  from a check that approved.

- **(internal)** `docs/STYLEGUIDE.md` §3.2.1's AV ceiling was missing shields, and
  `docs/DESIGN_balance.md` §9.2 was wrong about #318 as a result.

  **Shields carry AV on a `Shield` part, not an `Armor` one**, so the survey behind the curves never
  saw one — all 14 of vanilla's, and 20 of this fork's. The table shipped with no Shield column at
  all, in a document whose job was to give #319, *a finding about a shield*, something to be a defect
  against. §3.2.1 now has a Shield row at **7** (`Flawless Crysteel Shield`, the largest single AV of
  any ordinary item), and vanilla ships no ordinary tier-8 shield — only the artefact at 10, which is
  what #319 reports the zetachrome greatshield matching.

  §9.2 had claimed #318's "32 → 48" never stated its basis, and attributed it to #316. Both halves
  were wrong: it states the basis in its opening sentence, and with the shield restored it
  reconciles exactly — 8+4+4+4+2+(1×2)+1+**7** = 32, and 10+6+6+6+3+(3×2)+1+**10** = 48.

  Also recorded, because it changes what a fix should aim at: **shield AV is conditional and armour
  AV is not.** Block chance is `25 * (1 + ImprovedBlock)`, plus 25 each for `Shield_Block` and
  `Shield_DeftBlocking` — 25% bare, 75% fully skilled, 100% under Shield Wall — so a best-in-slot
  total that adds a shield to armour is an upper bound rather than a figure.

  `docs/LESSONS.md` gains the trap: **a number that agrees because both sides share the error is not
  a cross-check.** §9.1's per-slot maxima summed to 32, matching #318 exactly, which read as
  independent confirmation from a second method. It was a coincidence — the missing shield's 7 and
  two wrongly-included artefacts happened to cancel. The tell I ignored was that the survey had no
  member in the slot the finding was about.

- **Finesse no longer overrides a weapon's own penetration stat** (#366). Three vanilla melee
  weapons roll against something other than Strength, and one of them — `TauDagger`, the crystalline
  jile, at `Stat="Ego"` — inherits `BaseDagger` and so carried the Finesse tag. The handler compared
  Agility against the running `StatBonus`, which for that weapon held the *Ego* modifier, so any
  character with the higher Agility silently turned a psionic artefact into an Agility weapon. That
  is the same override #321 removed from the blueprints, arriving through a different door.

  It now reads the weapon's own stat and applies only at `Stat == "Strength"`. Safe for the 20
  vanilla merges that state no `Stat` at all, because `MeleeWeapon.Stat` is a field initialised to
  `"Strength"` — so an omitted attribute matches, and anything Qud adds later is excluded without a
  code change, which naming `TauDagger` would not have managed.

  Two things found alongside it. The **three vibro blades were tagged but inert** — `MaxStrengthBonus`
  is 0 and penetration adds `Math.Min(Bonus, MaxBonus)`, so Finesse could never contribute anything;
  the tag is gone from all three, via `Value="*delete"` on the wristblade, which inherits rather than
  declares it. And **nothing told the player a weapon was finesse-eligible** — the tag had no
  player-facing surface, which is how this was found, since a silent feature and a broken one look
  identical. Every finesse weapon now carries a `RulesDescription` saying so.

- **(internal)** `docs/DESIGN_balance.md` §5.7 was carrying two claims corrected elsewhere: that the
  Ego gradient diverges "without limit" above Ego 24, which the rank cap bounds, and that the
  Guardians' starting chipset is +17 Quickness at character creation, which is +15 because the cap
  at level 1 is 1. Both are now right in the one section that still had them wrong, and the list is
  scoped down to the four decisions that actually remain.

- **(internal)** Two corrections to §5.1, both from the same cause — modelling a layered system from
  a partial read. It claimed Ego scaling was uncapped; `GetMutationCap()` clamps it. And #316's
  figures now need a character level attached: **+33 Quickness requires level 18**, and a Guardian's
  starting chipset is +15 at level 1 rather than +17, because the cap is 1 there. The finding
  survives — a 20-water chip is +19 from level 4 against an *uncapped* 10,000-water legendary at +10.

- Nothing yet — but #347 records six chips whose grades grant nothing at all. `Kindle` and
  `FrostWebs` both return `false` from `CanLevel()` and never read their level, so basic, upgraded
  and perfected are the same item in each case, and the Fire and Ice chipsets each carry a dead
  third.

## [2.5.1] - 2026-08-21

### Added

- **(internal)** `docs/RELEASING.md` writes down what a release takes, and a `Release` issue
  template tracks each one on the board. Four releases in, the process lived only in my head, and
  two of its seven steps are invisible until somebody complains.

  The one worth stating plainly is that **a release is two publications and neither implies the
  other**. Steam is where the subscribers are, so it is easy to treat the Workshop upload as the
  release — but GOG, itch and Linux players install from the GitHub release zip, and for them a
  Workshop upload is not a release at all.

  The template asks for save compatibility as a required field, because it is the first thing any
  player wants and the easiest to leave until last.
- **(internal)** `validate_mod.py` fails when `manifest.json`'s version and `CHANGELOG.md`'s newest
  released heading disagree. The version is kept in three places by hand and nothing held any two
  of them together.

  The git tag is deliberately outside the check, and that is the interesting part: on the commit
  that creates a release the manifest and changelog already say the new version while the tag does
  not exist yet, so including it would fail the very commit that makes a release. Two of the three
  is what can be held honestly, and `docs/RELEASING.md` carries the third.
  ([#309](https://github.com/vixygrey/qud-expanded-community-edition/issues/309))
- **(internal)** Dynamic pool membership is pinned in `tools/dynamic-pools.json`, and
  `tools/report_dynamic_tables.py --check` fails on any change to it. A `pre-commit` hook runs it on
  every commit in ~0.2s; `--snapshot` rewrites the file when a change is intended, so the diff is
  the review.

  Verified by reproducing the real defect: deleting one of the six `Value="*delete"` tags that
  fixed #261 puts `Raven_Blaze Arrow` back in the ammunition pool, and the check names both the
  blueprint and the newly-appearing pool.

  **It cannot run in CI, and that is not an oversight.** The tags that decide membership sit on
  *vanilla* blueprints — `BaseArrow` carries `DynamicObjectsTable:Ammo` — so no runner can see them.
  A mod-only version would report the arrows out of the pool today and be right by luck, while
  missing a new blueprint that inherits `BaseArrow` and forgets the `*delete`, which is the entire
  regression. So it joins `compile_scripting.py` and the API snapshot as a local check that skips
  loudly without the game.
  ([#303](https://github.com/vixygrey/qud-expanded-community-edition/issues/303))
- **(internal)** `docs/LESSONS.md` records what it actually costs to play-test a change to a
  `DynamicObjectsTable` pool. `DynamicObjectsTable:Guns` has exactly one consumer,
  `GunsmithInventory_Legendary`, which `Gunsmith` carries as a `HeroTable` — so an ordinary gunsmith
  never touches the pool, and reading his stock tests nothing while looking exactly like a test that
  passed. There is no wish that makes a hero and none that rolls a population table; both were read
  out of the assembly after going to look for them.

  The other half is that these changes are removals, so a single sighting proves almost nothing: a
  pool six arrows were taken out of looks the same as one they were left in, in any sample where the
  roll would not have picked them. It takes several legendary merchants before an absence means
  anything.

  #261 and #262 sat in QA on the assumption they were ordinary gameplay changes awaiting a play
  test. They were verified from `tools/report_dynamic_tables.py` instead and moved to Staging.
  ([#304](https://github.com/vixygrey/qud-expanded-community-edition/issues/304))
- **(internal)** `tools/check_docs.py` recomputes `docs/FEATURES.md`'s item tables instead of
  trusting them. The new `item-tables` check compares every Tier, Value and Weight across all 254
  rows — **739 figures** — against the blueprint each row describes, and fails CI on a mismatch.
  It found nine on its first run, fixed separately in #299.

  **It runs in CI with no game installed, which is not what I expected.** `chips_from_blueprints`
  had said for months that these tables would need one, because 43 of their rows are `merge` edits
  to vanilla blueprints. Measuring rather than reasoning turned that around: a merge that changes a
  figure *declares* it, so of the 121 cells on those 43 rows exactly **one** is not in the mod's own
  XML — `Flawless Crysteel Boots`, whose tier #86 corrected by *removing* the override so vanilla's
  would apply. The fix that made it right is what puts it out of reach, and 739 of 740 is a good
  trade for that.

  Rows are matched three ways, which is what takes it from partial to every row: the blueprint name,
  the name with its `Raven_`/`Vixy_` prefix dropped, and the rendered display name.

  Mismatch-only, unlike the chip appendix, which also reports blueprints with no row. That appendix
  means to be complete; these tables are curated selections, and demanding a row per blueprint would
  invent a rule the document never made.

  `BlueprintIndex` gains `tag_value` and `part_attr` beside the existing `has_tag` and `has_part`,
  honouring the same `*noinherit` and `*delete` rules. Ten tests cover the check, including that a
  figure the mod never declares is skipped rather than reported.
  ([#287](https://github.com/vixygrey/qud-expanded-community-edition/issues/287))
- **(internal)** `docs/STYLEGUIDE.md` §3.3 states the rule this fork's spanning drop entries follow:
  an item entered in more than one tier of a table family is anchored at its own tier at one end of
  the run, and its weight moves toward that anchor. Two shapes — a consumable anchors at the bottom
  and tails upward at flat weight (`Raven_Solar Cell Array`, `Raven_Advanced Chem Cell`), an
  artifact ramps upward toward its tier (`Raven_Advanced Hoversled`, `Raven_Large Sphere of Negative
  Weight`).

  #284 read the four as two deliberate spans and two benign ones and asked that the deliberate pair
  be recorded so a later audit would not re-open them. Laying out the full runs rather than only the
  entries furthest from their table showed all four are one rule, which records them better than a
  list of exceptions would: the anchor is the entry that looks unremarkable, so an audit reading
  only outliers will always miss it.

  A single entry off its own tier is noted as vanilla's idiom rather than this fork's, needing
  vanilla's rarity with it — which is what `Raven_Fine-Tuned Handgun` now does.
  ([#284](https://github.com/vixygrey/qud-expanded-community-edition/issues/284))
- **(internal)** `docs/LESSONS.md` records that a closing keyword next to an issue number closes it
  even inside a denial. `## Why this doesn't close #284` registered a closing reference and shut
  #284 on the #286 merge, against a paragraph, a commit trailer and an issue comment all saying it
  should stay open. GitHub matches `close #N` as a substring and does not read the negation.

  The entry names the safe phrasings, the pre-merge check
  (`gh pr view <n> --json closingIssuesReferences`, which should be empty for a partial fix) and the
  tell afterwards (`commit_id: null` on the close event, which means a linked reference closed it
  rather than a commit message).

  It sits next to the stacked-PR entry, since both are a squash merge closing something it
  shouldn't and both are invisible until after the fact.
  ([#288](https://github.com/vixygrey/qud-expanded-community-edition/issues/288))
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

- **The fine-tuned handgun is a rarer find in `Missile 4`**, at draw weight 2 instead of 5. This is
  its odds of being picked from that table, not its physical weight, which is unchanged.

  It declares `Tier="6"` and drops from a tier-4 table, which #284 flagged as an unexplained
  two-tier span. Checking vanilla settles it: vanilla's own `Missile 4` carries the `Hypertractor`
  at tier 6, the identical span, so a tier-6 gun appearing there is vanilla's idiom rather than a
  defect — and the handgun's tier is right as it stands.

  What vanilla also does is make that item the rarest thing in the table. The `Hypertractor` sits
  at weight 2 against neighbours at 5 and 10; *allowed but rare* is the whole shape of the idiom,
  and the handgun was following only half of it. It is the most valuable of the four conventional
  guns this fork puts in that table at 600, so being the least likely of them to turn up is the
  right way round.
  ([#284](https://github.com/vixygrey/qud-expanded-community-edition/issues/284))
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
- **(internal)** `check_build_log.py` reads its log section title from the **deployed** manifest
  rather than the repository's, so it can pass against a dev build.

  The log names its section after the title the game saw, and `sync_mod.py --dev` deliberately
  suffixes that with `(dev)` so the in-game mod list says which build is loaded. The check looked up
  the repository's title instead, so **it could never pass against a dev build** — the only build
  worth checking, since a publish build is `main` and `main` is validated before it is installed.

  Found by using it: verifying #342 in-game, the game had compiled all 48 files and written
  `Success :)`, and the check called it a failure. `find_deployed` already looks the install up by
  manifest id "since the folder is named however it was installed" — this is that same thought,
  finished.

  Worth recording why sixteen tests missed it: the harness wrote the deployed manifest with **no
  title at all**, so every test took the fallback path and matched the repository's title. The defect
  lived in a code path the suite could not reach. Fixed the harness, then added three tests, and
  checked the new one fails with the fix reverted.


- **(internal)** `docs/RELEASING.md` and the release issue template now cover the release zip.
  Step 7 said to tag and run `gh release create` and stopped, but every release also attaches
  `QudExpandedCommunityEdition-X.Y.Z.zip` — the contents of `mod/` under a folder named for the
  manifest id, and the thing players outside Steam actually install.

  The omission is worse than a missing step. GitHub generates a source zip for any tag, so the
  release page is never empty — it offers the whole repository, `tools/` and `docs/` included. A
  player who takes that and drops it in `Mods/` gets the repo rather than the mod. The failure is a
  plausible wrong file, not an absent one, aimed at exactly the players the GitHub release exists
  for.

  Found by following the document on 2.5.1, which is the first release cut against it, and noticed
  only because 2.5.0 and 2.4.0 each show one asset where mine showed none.
  ([#312](https://github.com/vixygrey/qud-expanded-community-edition/issues/312))
- **(internal)** `CONTRIBUTING.md`'s .NET SDK and `ilspycmd` instructions sat under
  *Seeing what a `DynamicObjectsTable:` tag distributes*, a section about a tool that needs neither
  — `report_dynamic_tables.py` parses XML and runs fine under `PATH=/usr/bin:/bin`. They belong to
  `snapshot_qud_api.py`, two sections up, and have moved there.

  Both halves of that were doing harm. Someone reading about dynamic tables was told to install a
  decompiler they do not need, and might reasonably conclude the tool was out of reach. And the
  `path_helper` explanation — the reason `command -v` finding nothing does not mean a tool is
  missing — was orphaned from the hook it explains, which is the one place the person who needs it
  would look.

  The block's own last line gave it away: *"Until you do, the hook skips on every commit"*,
  singular, describing the `snapshot-check` hook. The dynamic-tables section had no hook at all
  when that was written.
  ([#307](https://github.com/vixygrey/qud-expanded-community-edition/issues/307))
- **The scour slug now tells you it is a 5% chance.** Its rules text read *"Rusts a piece of what
  the target is carrying"*, which reads as something that happens when you hit. It happens about one
  hit in twenty — roughly two dozen slugs per rusted item, which is the tuning #146 chose
  deliberately. A player loading them to strip a target's gear had no way to know that from the item.

  It now opens *"Has a 5% chance on hit to rust a piece of what the target is carrying."* The rest
  of the text is unchanged.

  Vanilla settles this rather than my preference: `Rank Fangs` carries the same `RustOnHit` part at
  the same `Chance="5"` and states the percentage outright, as does every other vanilla object with
  a chance-based on-hit effect. It also matters more here than it looks, because
  `Precision Nanon Fingers` multiplies percentage-based effects — a player with those installed was
  tripling a number the item never showed them.

  **No precedent for the other rounds.** The arrows and shells describe their effects without
  figures and are accurate as written; this one was not.
  ([#295](https://github.com/vixygrey/qud-expanded-community-edition/issues/295))
- **(internal)** Nine figures in `docs/FEATURES.md`'s item tables disagreed with the blueprints they
  describe, and the document was wrong in all nine. Four were stale — #86 corrected the zetachrome
  greataxe and wristblade to 1280, removed the `Flawless Crysteel Boots` tier override, and put the
  carbideweave cloak at 40, and the fix reached the blueprint and the §10 row but never the stat
  table.

  The other five had never been right. The low-tier wristblades were documented at 15, 25, 35, 55
  and 105 against blueprints of 5, 10, 20, 40 and 160 — §3.2's stated curve, which the same table
  already gets right from crysteel upward. `git log -S` puts both the values and the rows in the
  original import with no edit since, so those cells were wrong for the whole life of the fork.

  §10's below-curve note is corrected with them: it named four items and only `Cudgel8` and
  `Cudgel8th` are still below curve.

  No blueprint changed. Where the two disagreed the blueprint was both what ships and the one
  following a stated convention.
  ([#299](https://github.com/vixygrey/qud-expanded-community-edition/issues/299))
- **(internal)** `docs/FEATURES.md` §6.7's heading said *"arrows and shells live, bullets still
  disabled"*, wrong on both halves — the scour slug shipped in v2.5.0, and #146 cut the bullets
  rather than pausing them. It now reads *"arrows, shells and one slug live, bullets cut"*.

  The paragraph under it was worse than the heading: it said the bullets *"remain commented for
  #146"*, contradicting *The scour slug* subsection four hundred lines below it in the same section,
  which describes the cut and the measurement behind it. A section disagreeing with itself is harder
  to catch than a stale sentence, because both halves look authored.

  Renaming the heading moved its anchor, and the wiki linked to it three times across two pages —
  so those were updated in the same sitting rather than left to rot, which is the whole shape of
  #230. `check_docs.py --wiki` passes against a fresh clone.
  ([#297](https://github.com/vixygrey/qud-expanded-community-edition/issues/297))
- **(internal)** `docs/FEATURES.md` §10 rows 3 and 12 are marked fixed, finishing the sweep #291
  opened. Row 3 said the bullets were *"pending #146"*; #146 is closed and did not defer them, it
  **cut** them — it measured what rate of fire does to area and status effects and kept one slug
  with a payload that survives being fired in volume. Row 12 quoted chargen text that #276 replaced
  more than a week ago.

  The 22 objects those decisions covered stay commented in `Ammo.xml` rather than being deleted,
  per the note above that table: a closed row beats someone rediscovering the problem, and the same
  reasoning applies to the blueprints the row is about.
  ([#291](https://github.com/vixygrey/qud-expanded-community-edition/issues/291))
- **(internal)** The closing-keyword entry in `docs/LESSONS.md` listed six of GitHub's nine keywords,
  omitting the past-tense `closed`, `fixed` and `resolved` as a set — and one of the three caught me
  the next day, in the pull request for #291. It now lists all nine and is rewritten around
  adjacency rather than around denial.

  The original was built on the case that produced it: a heading arguing that a pull request did
  *not* close an issue. That framing asks the reader whether they are arguing with the parser, and
  the second instance was not arguing with anything — it was a sentence narrating what an earlier
  pull request had done, referring to an issue the pull request was not even about.

  Both examples are kept, because they fail differently and the ordinary one is the second.
  ([#293](https://github.com/vixygrey/qud-expanded-community-edition/issues/293))
- **(internal)** `docs/FEATURES.md` §10 row 6 is marked fixed, which it has been since #50. It
  described the `<stag>` typo on the advanced hoversled's `Floating` tag and the sphere of negative
  weight's `Trinket` tag as live at 🟠 Med, and carried line references two hundred lines out of
  date. `AGENTS.md` points contributors at §10 as the place to seed work from, so a row describing a
  fixed defect sends someone to fix it a second time.
  ([#291](https://github.com/vixygrey/qud-expanded-community-edition/issues/291))
- The zetachrome greathammer weighed 5 lbs where the family's rule puts it at 6. Every other war
  hammer in this fork weighs its one-handed counterpart plus 3 — bronze 4→7 through flawless
  crysteel 3→6 — and zetachrome was the only one off it, by one.

  Worth saying what this is *not*, because #248 asked whether the whole family was mistuned. It
  is not. The greathammer curve looks like it wobbles only when read on its own; that shape is
  vanilla's one-handed curve carried across with a constant added, and fullerite at 9 — the value
  the issue proposed lowering — is the rule being followed, not broken. One weight was wrong and
  the other eight were right.

  The rule is now written down in `docs/STYLEGUIDE.md` §3.2, since nothing enforces it and the
  only previous record of it was the numbers themselves.
  ([#248](https://github.com/vixygrey/qud-expanded-community-edition/issues/248))
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

[Unreleased]: https://github.com/vixygrey/qud-expanded-community-edition/compare/v2.10.0...main
[2.7.0]: https://github.com/vixygrey/qud-expanded-community-edition/releases/tag/v2.7.0
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
