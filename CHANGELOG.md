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

Nothing has been released yet. Everything below lands in the fork's first Workshop release.

> ⚠️ **The first release requires a new character.** Body-part and anatomy identifiers changed
> (see *Changed* below), and those are written into save state. This fork publishes as a separate
> Workshop item, so no existing save is affected — but a save started against a pre-release build
> of this fork will not carry forward.

### Changed

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

### Internal — tooling

- **(internal)** Three more clusters of stale documentation corrected, the second sweep after #93. `docs/FEATURES.md` §10 still listed five closed defects as open — two of them 🔴 Critical — and §3.3 and §7.2 still described the 72 chips and nine armor pieces as unobtainable, though both were fixed in #36 and #38. §0, §4 and the file tree still credited Akimbo to Multiweapon Fighting while §10 row 7 recorded its removal in #88, so the file contradicted itself; the class-collision account is kept as settled history rather than deleted, because it is the repo's clearest demonstration that `Class=` is an identifier. And `CLAUDE.md` still said there was no remote, no issue tracker, and that the validation script was "the only automated gate that exists" — all three untrue, and the middle one told contributors the repo's own stated workflow was not yet in force.
  ([#96](https://github.com/vixygrey/qud-expanded-community-edition/issues/96))

- **(internal)** `.gitignore` now covers `.claude/worktrees/`. Claude Code agent worktrees are created inside the repository and each is a complete second copy of the working tree, so leaving them untracked meant one `git add -A` would stage the whole duplicate. Worse than ordinary untracked noise because it is intermittent: the worktree is removed when the agent finishes, so it exists only while someone is mid-task. Scoped to `worktrees/` rather than all of `.claude/`, so any agent or skill configuration this project checks in later stays visible. Same reasoning as #63 — a repo's `.gitignore` has to stand on its own.
  ([#98](https://github.com/vixygrey/qud-expanded-community-edition/issues/98))

- **All mod files normalised to LF line endings**, enforced by `.gitattributes`. Upstream was
  CRLF throughout. Diff against the pre-normalisation baseline with
  `git diff --ignore-cr-at-eol upstream-2.2`, and `git blame` skips the conversion via
  `.git-blame-ignore-revs`. Mura's original documents are exempted from normalisation and stay
  byte-for-byte.
  ([#17](https://github.com/vixygrey/qud-expanded-community-edition/issues/17))

### Added

- **The skill tree retunes split into two toggles.** **Qud Expanded: eased skill requirements** governs the twenty attribute requirements the mod lowers or widens — Axe and Cudgel accepting Strength *or* Agility, Long Blade's Dueling Stance at 15 and En Garde! needing only one attribute at 29, Multiweapon Expertise at 21 and Mastery at 25, and Tinker I/II/III at 17/21/25. **Qud Expanded: retuned skill point costs** governs the four prices — free Disassemble, Reverse Engineer at 200, Butchery and Spicer at 100 each. Off restores vanilla exactly in both cases; no power is ever removed and nothing you already own is taken back.

  They are separate because their scopes genuinely differ. Costs apply immediately. Requirements apply **on restart**, and the option says so: Qud builds each power's requirement list once per session and offers no supported way to rebuild it. Splitting them also lets you keep the accessibility changes while paying vanilla prices, which matters if you have turned extra starting skills off — the Cooking price rise exists to offset the free Cooking and Gathering that option grants.
  ([#91](https://github.com/vixygrey/qud-expanded-community-edition/issues/91))

- **Psionic chips can be kept out of loot.** **Qud Expanded: psionic chips in loot** governs the six references that put chips into the artifact tables at tiers 3 through 8. Off means no chip or chipset is ever rolled — and since no chip is tinkerable, that closes the supply completely rather than leaving a back door. Fully live: it changes what is rolled from that point on, and chips already in the world or in your pack are untouched. Psionic Adepts keep their starting chips either way, since those are the genotype rather than an addition to it.
  ([#91](https://github.com/vixygrey/qud-expanded-community-edition/issues/91))

- **The extra skill points per level can be turned off.** **Qud Expanded: extra skill points per level** governs the mod's 65 for a Mutated Human (vanilla 50) and 85 for a True Kin (vanilla 70). Off restores vanilla's numbers exactly. Like hit points, skill points are rolled at each level-up, so this applies from your next level and never removes points already earned. The Psionic Adept's 95 is the genotype rather than an addition to a vanilla one, so it is unaffected.
  ([#91](https://github.com/vixygrey/qud-expanded-community-edition/issues/91))

- **Mutated Human hit points per level are selectable.** **Qud Expanded: Mutated Human hit points per level** offers `1-5` (this mod's documented range, the default), `2-3` (what 2.2 actually shipped), and `1-4` (vanilla). The range is rolled fresh at every level-up, so unlike the chargen options this one takes effect from your next level rather than needing a new character. True Kin and Psionic Adepts are unaffected.
  ([#90](https://github.com/vixygrey/qud-expanded-community-edition/issues/90))

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

### Removed

- **Multiweapon Fighting no longer offers Akimbo.** Akimbo is unchanged and still available in the Pistol tree, and Multiweapon Fighting keeps this mod's reduced stat requirements for Expertise and Mastery. The two powers shared one implementation, and Qud maps each implementation to exactly one power — so this mod's copy was served wherever the game asked for vanilla's, most visibly on the **Gunslinger** calling, which grants Akimbo by implementation name and therefore displayed the wrong power. It went unnoticed for years because both powers were named "Akimbo" and looked identical wherever they appeared; it surfaced only when this fork renamed one of them while working on something else. Giving the mod's version its own implementation fixed the Gunslinger, but a character who then bought both got the ability listed twice and a skills screen that would not close, so the power was removed rather than shipped with a known way to spoil a run.
  ([#11](https://github.com/vixygrey/qud-expanded-community-edition/issues/11))

### Fixed

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

- **(internal)** All of the mod's XML is reformatted to a single consistent style, and that style is now enforced. Indentation is 2 spaces throughout with no tabs — `docs/STYLEGUIDE.md` has required that all along while 18 lines across `Skills.xml`, `Throwables.xml`, `Mods.xml` and `MeleeWeapons.xml` violated it — and long elements put one attribute per line. `prettier --check` runs in CI and formats on commit via `pre-commit`. The reformat was verified to change nothing but layout by comparing the parsed element tree of every file before and after: 19 of 19 identical in tags, attributes and text, BOMs preserved, and `Ammo.xml`'s commented-out 62 objects byte-identical. Mura's original files stay permanently retrievable through the immutable `upstream-2.2` tag, and the reformat commit is listed in `.git-blame-ignore-revs` so `git blame` skips it.
  ([#17](https://github.com/vixygrey/qud-expanded-community-edition/issues/17))

- **(internal)** The XML formatter is configured with `xmlWhitespaceSensitivity: "preserve"`, not `"ignore"`. Under `ignore`, prettier reflowed the *text content* of `<helptext>` in `mod/Options.xml` to satisfy the print width, inserting a newline mid-sentence in a string Qud renders in the options menu. Attribute formatting is unaffected, so the chosen style is unchanged; only text nodes are now protected.
  ([#17](https://github.com/vixygrey/qud-expanded-community-edition/issues/17))

- **(internal)** Prettier with `@prettier/plugin-xml` is declared as the mod's XML formatter, pinned in `package.json` and configured in `.prettierrc.json` (2-space indent, LF, `printWidth` 120). Tooling only, at the repo root — `mod/` is still loaded directly by Qud with no build step, and `node_modules/` is gitignored, so nothing here reaches subscribers. This commit adds the tooling; the reformat itself lands separately.
  ([#17](https://github.com/vixygrey/qud-expanded-community-edition/issues/17))

- **(internal)** Python linting and formatting are now an enforced gate rather than an undeclared habit. `ruff check` and `ruff format --check` run in CI and in `pre-commit`, both pinned to the same version, both scoped to `tools/` — `mod/` holds no Python and the scoping keeps the hook from ever touching shipped files. The gap this closes was not cosmetic: a formatter was already running as an editor hook on the maintainer's machine, so the repo received ruff-formatted output without having declared ruff, and that leaked incidental reformats into unrelated pull requests. `tools/` was reformatted once in #74, whose squash commit is listed in `.git-blame-ignore-revs`. Charter rule 4 is intact — `validate_mod.py` remains Python-stdlib-only at runtime, so no contributor needs ruff to run the validator.
  ([#72](https://github.com/vixygrey/qud-expanded-community-edition/issues/72))

- **(internal)** The three pre-existing `ruff check` failures in `tools/` are fixed: both validators are now executable, making their `#!/usr/bin/env python3` shebangs true rather than decorative (`tools/build_preview.sh` was already `100755`), and `re.S` is spelled `re.DOTALL`. Groundwork for making Python linting an actual gate.
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

- **(internal)** Charter rule 5 amended: the mod's C# may now hold state and adjust already-loaded
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

- **(internal)** Pull requests now automatically request review from the maintainer via
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
- **(internal)** Lessons from the options-menu crash recorded in `CLAUDE.md`: read a crash's
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

### Fixed

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
  table and had no tinker recipe. Each is placed in the table matching its own tier: nanoweave
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

### Internal

- **Repository restructured** so the shipped mod is isolated in `mod/`, with documentation in
  `docs/` and tooling at the repo root. Development files were previously destined to ship to
  every subscriber — measured across 87 installed mods, 8 ship a `README.md`, 5 a `LICENSE` and 4
  a `.csproj` by accident. ([#15](https://github.com/vixygrey/qud-expanded-community-edition/issues/15))
- **Spaces removed from blueprint filenames** — `MeleeWeapons.xml`, `OtherEquipment.xml`,
  `PsionicChips.xml`, `RangedWeapons.xml`. Safe because Qud resolves modded XML by root element
  rather than by filename.
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
- Repository placed under version control with the pristine upstream 2.2 import tagged
  `upstream-2.2`, so `git diff upstream-2.2` always shows exactly what the fork changed.

## Credits

Every release carries the credit list in [`docs/PERMISSION.md`](docs/PERMISSION.md) §4 —
**Mura** (`@mura_raven`) for the original mod, and **Noble Lark** for the psionic subtype sprites,
named explicitly as the one condition of the fork permission.

[Unreleased]: https://github.com/vixygrey/qud-expanded-community-edition/commits/main
