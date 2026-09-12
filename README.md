# Qud Expanded Community Edition

A community-maintained fork of **[Caves of Qud Expanded](https://steamcommunity.com/sharedfiles/filedetails/?id=1134036260)** by **Mura**.

**On the Steam Workshop:** [Qud Expanded Community Edition](https://steamcommunity.com/sharedfiles/filedetails/?id=3785441196) ·
**Not on Steam?** [Download the latest release](https://github.com/vixygrey/qud-expanded-community-edition/releases/latest)

This fork is a **separate mod**. It does not replace, modify, or take over the original.
Mura's original remains available.

> **Development note:** VixyGrey uses AI to assist with development and documentation tasks.

---

## Credits

This mod exists because other people built important parts of it. Read their credits first.

| Who | What |
|---|---|
| **Mura** (`@mura_raven`) | Created Caves of Qud Expanded and spent years on it. This fork is their mod, continued. |
| **Noble Lark** (a.k.a. **chirps**) | All 18 psionic subtype sprites. |
| **Scrolldier** (a.k.a. Parzival) | Taught Mura to mod Caves of Qud. |
| **Arendeth** | Population table fixes. |
| **Tyrir** | Bug reports, including the 2.2 typo batch. |
| **Crow** | Helped with bug fixes on the original. |

### Contributors to this fork

| Who | What |
|---|---|
| **[Jah-yee](https://github.com/Jah-yee)** | Fixed the `<stag>` typos that stopped advanced hoversled floating and stopped the sphere of negative weight from registering as a trinket. This project received its first outside contribution. |

Mura opened the mod to the community with one condition: *give credit where due, including Noble
Lark for the subtype sprites*. I treat that condition as permanent.
The build fails when `manifest.json` stops naming Mura.
Provenance and the full grant appear in [`docs/PERMISSION.md`](docs/PERMISSION.md).

---

## What it does

- **Psionic Adept**, a third genotype for players who prefer to find a build instead of planning one.
  It has no mutations, the fewest stat points in the game, and the most skill points per level.
  Psionic chips provide its power.
  Chips cannot be bought or built, and they come only from chests.
  A True Kin saves for a chosen implant. An Adept wears what it finds.
  The 18 subtypes divide between casters and martial guardians.
- **144 psionic chips**, implantable chips granting real, working mutations to genotypes that
  cannot mutate. Every one of them can be found.
- **Complete weapon and armor families**, bronze through zetachrome, one- and two-handed, with
  consistent stats, tiers and prices.
- **New weapon classes**: katanas, rapiers, halberds, greataxes, greatswords, war hammers,
  wristblades, and the two-handed finesse lines: glaives, spears and quarterstaves.
- **Skill and economy retuning**, and a home base building in Joppa.

**Read these two sources for different information.** The
[wiki](https://github.com/vixygrey/qud-expanded-community-edition/wiki) covers how the mod *plays*:
builds, synergies, opening strategy, and each system's purpose.
[`docs/FEATURES.md`](docs/FEATURES.md) is the complete reference and the authoritative source for
tiers, weights, prices, drop rates, stat modifiers, and option defaults.

### You can turn most of it off

Thirty-six options, in Qud's own options menu, appear under **Mods**.
Keep the weapons and armor while disabling the chip economy, vanilla skill requirements, or the Joppa building.
The mod does not require every feature.

**The effect of a change depends on its scope:**

- **Immediately:** psionic chips in loot and skill point costs.
  Hit points and skill points per level apply at the next level.
- **On restart:** eased skill requirements.
  Qud builds each power's requirement list once per session.
- **On a new character:** mutation points, starting skills, starting reputation, both Chip Interface options,
  and the Joppa building.
  Qud reads these values at character creation or stores them in the save.

[`docs/FEATURES.md`](docs/FEATURES.md) §13 lists every option, its default, and its scope.
That document is also the complete reference for the mod.
It covers 527 new blueprints and 284 vanilla merges.

## Requires a new character

Some identifiers changed during the fork, and Qud writes them into save files.
**Start a new character with this mod enabled.** Saves from the original mod do not work.

---

## Compatibility with the other Expanded mods

> **Do not enable this fork and the original *Caves of Qud Expanded* at the same time.** Pick one.

This fork continues Mura's mod and defines the same records:
**36 C# types with the same names in the same namespace**, one for each psionic chip part.
Qud reports this state as `==== TYPE CONFLICTS DETECTED ====`.
Load order decides which version wins.
The result is undefined.
Saves do not transfer between the two mods.

The other two mods in the family:

| Mod | | |
|---|---|---|
| **Caves of Qud Expanded** (Mura's original) | ❌ | Same 36 types in `XRL.World.Parts`, so enable one or the other |
| **Caves of Qud Expanded — The Grand Bazaar** | ❌ | Its content is now in this fork, so enable one or the other |
| **Caves of Qud Expanded — Experience Curve Beta** | ✅ | No shared record or type, and its script cannot run |

**The Bazaar compatibility mark changed because this fork absorbed its content.**
The two merchants, their tents, and their merchant retuning are now part of this mod.
The *Six Day Stilt* option controls them.
Running both mods declares `Raven_Smithy` and `Raven_WaterMerchant` twice.
The mods also merge the same merchant tables twice.
Pick one.

The tent-layout script is a separate matter.
It never ran for players.
See [`docs/FEATURES.md` §53.1](docs/FEATURES.md#531).

**The Experience Curve needs a separate note.**
It ships no XML, and its one class is called `XRL.World.Parts.Experience`, vanilla's own name.
Type resolution reaches vanilla's type first, so the sub-mod's C# remains inert.
This fork has its own experience curve, off by default, in a separately named part.
The two mods share no type or record.
The compatibility mark remains valid.
Enabling the sub-mod adds nothing because the sub-mod adds nothing on its own.

This comparison covers records and types.
It does not cover every combination through a play test.
Report unexpected behavior by [filing an issue](https://github.com/vixygrey/qud-expanded-community-edition/issues).

---

## Installing

**On Steam.** [Subscribe on the Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3785441196)
and enable the mod in Qud's mod menu. Updates arrive automatically.

**On GOG, itch, or Linux without Steam.** The Workshop is not available.
Download the [latest release](https://github.com/vixygrey/qud-expanded-community-edition/releases/latest).
The archive contains only the mod.
It extracts to a single `QudExpandedCommunityEdition/` folder.
Copy that folder into Qud's Mods directory:

| Platform | Path |
|---|---|
| macOS | `~/Library/Application Support/com.FreeholdGames.CavesOfQud/Mods/` |
| Windows | `%USERPROFILE%\AppData\LocalLow\Freehold Games\CavesOfQud\Mods\` |
| Linux | `~/.config/unity3d/Freehold Games/CavesOfQud/Mods/` |

The installation is correct when `Mods/QudExpandedCommunityEdition/manifest.json` exists.
Enable the mod in Qud's mod menu.
Update the mod by replacing the folder.
Read the [changelog](CHANGELOG.md) for each change and its reason.

**From a clone.** Copy this repository's `mod/` directory as described above.
Only `mod/` is the mod.
All other files provide development tooling and never reach subscribers.

---

## Contributing

The README and Workshop description credit every outside contribution by name in the pull request
that merges it. You do not need to ask.
[`CONTRIBUTING.md`](CONTRIBUTING.md) is the full guide.
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) applies to every contributor, including the maintainer.

The rules for this fork appear in [`docs/CHARTER.md`](docs/CHARTER.md).
Six rules cover compatibility, causality, credit, developer experience, safety, and configuration.
They are constraints, and most are mechanically enforced.

[`docs/LESSONS.md`](docs/LESSONS.md) collects traps from Qud and prior maintenance work.
Read it before a first change.

[`docs/STYLEGUIDE.md`](docs/STYLEGUIDE.md) covers naming, layout, and formatting.
**Read §1 before renaming anything.** Several conventions are load-bearing identifiers.
Breaking one can fail without an error.

### There is no build step

Qud loads the XML in `mod/` directly. You need no toolchain to contribute.

### Validation

Run one command. Python 3 is the only required dependency:

```bash
python3 tools/validate_mod.py
```

The validator checks XML and JSON syntax, blueprint reachability, `Load="Merge"` discipline on
vanilla records, C# part resolution, part attributes, the Workshop target, and manifest credit.
It also enforces charter rule 5 against `mod/Scripting/`.
It rejects file I/O, network access, reflection, shell execution, external assemblies, and Harmony.
It flags instance fields on `[Serializable]` types because those fields enter player saves.
CI runs the same checks on every pull request.

After a Caves of Qud update, run both additional commands:

```bash
python3 tools/check_vanilla_drift.py
```

This command compares the mod with the installed game.
It catches a missing `Load="Merge"` target and custom anatomies that drift from vanilla's `Humanoid`.

```bash
python3 tools/snapshot_qud_api.py
```

This command regenerates `tools/qud-api.json`, the committed list of part and blueprint names that
the game uses.
The snapshot lets `validate_mod.py` check part names and blueprint references in **CI**.
CI has no game installation, so the snapshot supplies the reference data.

Most snapshot data comes from the game's plain-text XML.
The `members` map is the exception.
It lists the member names that each part class accepts, and it exists only inside `Assembly-CSharp.dll`.
`tools/dump_part_members.cs` reads assembly *metadata* with `System.Reflection.Metadata`.
The process does not decompile, execute, or restore a package.
The result contains identifiers.
The .NET SDK is required.
The part list also comes from that assembly through `--assembly`.
That option requires [`ilspycmd`](https://github.com/icsharpcode/ILSpy).
The snapshot contains 1605 names, while vanilla XML uses 949 names.
Vanilla declares more parts than its XML uses.
**The `--assembly` option is required.** The committed snapshot uses it.
The generator refuses a run without it instead of silently narrowing the file.

The snapshot records the Steam build that produced it.
The `--check` option compares the snapshot with the installed game without writing.
The pre-commit hook runs this check on every commit because a Qud update does not correlate with a file pattern.
The hook skips when the game, SDK, or `ilspycmd` is missing.
It passes for contributors who cannot run the check.
A stale snapshot fails.
That failure exposes a newly added vanilla name, which is the intended direction.

After changing which checks are required to merge, run:

```bash
python3 tools/check_docs.py --ruleset
```

This command compares `tools/required-checks.json` with the checks that GitHub enforces.
The file records the repository's intended ruleset.
`check_docs.py` verifies the documented count and the status of every CI job.
The command cannot confirm that GitHub still matches the file.
Run it with `gh` and network access after changing required checks.

### Installing it to play and publish

Qud loads the mod from the same directory that the Workshop uploader publishes.
`tools/sync_mod.py` creates separate development and publication builds:

```bash
python3 tools/sync_mod.py --dev       # any branch
python3 tools/sync_mod.py --publish   # main only, after validation
```

**A development build removes `WorkshopId`.** That key binds an upload to the published item.
Without the key, the uploader treats the mod as unpublished and offers *"Create
Workshop Id for Mod…"* instead of overwriting the published item.
Experimental content therefore cannot reach the live page.
The development `manifest.json` title also gains a `(dev)` suffix.

`--publish` requires `main`, a clean tree, and local `main` at `origin/main`.
Publishing an unpulled `main` ships a state that the maintainer has not reviewed.
The command runs `validate_mod.py` first and copies nothing after failure.
Both modes require an empty destination with this mod's own `manifest.json` ID.
This prevents a mistyped `--dest` from deleting another mod.

Restart Qud after either mode.
Qud reads XML at load, so a running session retains the previous blueprints.
A wish for an unloaded blueprint resolves to the nearest loaded blueprint.

### Regenerating the Workshop preview image

`mod/preview.png` is committed.
Run this command only when changing the image:

```bash
python3 tools/build_preview.py
```

The image is **original work**, a stratigraphic cross-section in Caves of Qud's 18 fixed colors.
It uses its own 16×24 character cell.
It is not derived from Mura's logo.
Mura receives credit in the image, `manifest.json`, and this README.
[`docs/PREVIEW_DESIGN.md`](docs/PREVIEW_DESIGN.md) records the design reasoning.

The script needs Pillow, so it is outside the validation gate and does not run in CI.
`tools/validate_mod.py` uses only the Python standard library.
Set `QUD_PREVIEW_FONTS` when the script cannot find GeistMono.
The script stores every size and interval and writes a 128px proof beside the output.
The mod manager displays the proof at that size.

### Local hooks, worth installing

```bash
pre-commit install --install-hooks
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

The hooks run the same checks as CI.
They fail within seconds instead of after a remote round trip.
CI cannot run `no-commit-to-main`.
That hook rejects a commit on `main` before it exists.
The server-side ruleset can reject such a push only afterward.
The hook runs at `pre-commit` because release tags belong on `main` (#469).

Install the hooks before making commits.
The maintainer learned this after committing to `main` without them (#120).

**If `pre-commit` reports `Cowardly refusing to install hooks with core.hooksPath set`,** a global
Git configuration sets `core.hooksPath`.
Unset it during installation when the global hook delegates to the repository hook:

```bash
saved=$(git config --global --get core.hooksPath)
git config --global --unset core.hooksPath
pre-commit install --install-hooks
git config --global core.hooksPath "$saved"
```

Confirm the installation by attempting a commit on `main`.
The hook must reject that commit.

### Workflow

[`CONTRIBUTING.md`](CONTRIBUTING.md) contains the full workflow:
issue first, short-lived branch, small PR, squash merge, and required pull request evidence.

The [**Qud Expanded CE project board**](https://github.com/users/vixygrey/projects/1) shows active work.
Issues use tracks for Ammo, Content, Systems, Sub-mod merges, Upstream, and Tooling & docs.
Work reaches **Done** after Workshop publication and a release for players without Steam.
**QA** identifies a change that requires play testing.
**Staging** identifies work merged since the last release.

---

## Licence

This project licenses maintainer contributions as **Apache-2.0** for code
([`LICENSE`](LICENSE)) and **CC BY 4.0** for content and documentation
([`LICENSE-CONTENT`](LICENSE-CONTENT)).

Mura owns the inherited work.
Noble Lark owns the subtype sprites.
Neither contribution is mine to license.
[`COPYING.md`](COPYING.md) states what you can reuse and from whom.
[`NOTICE`](NOTICE) carries the credit required for redistribution.

## Layout

```
mod/     the shipped mod, the only directory uploaded to the Workshop
docs/    CHARTER, FEATURES, LESSONS, PERMISSION, STYLEGUIDE, and Mura's original documents
tools/   validation, drift checking, and the preview-image generator
```

`git diff upstream-2.2` shows changes since Mura's 2.2 release:

```bash
git diff -M --ignore-cr-at-eol upstream-2.2 HEAD
```

**Since #78, this diff is dominated by formatting.**
The XML was reformatted wholesale, and long elements now place one attribute on each line.
`-w` does not help because it ignores whitespace within a line.
The reformat splits single lines into many lines, which Git treats as changed lines.
Read the raw diff as a file-change record, not a content-change record.

Two tools preserve the useful history:

- **Retrieve Mura's originals.** `git show upstream-2.2:<path>` reproduces each file byte-for-byte.
  The tag is immutable and remains unchanged through future reformats.
- **Use `git blame`.** The reformat commit appears in [`.git-blame-ignore-revs`](.git-blame-ignore-revs).
  Enable it once per clone:
  `git config blame.ignoreRevsFile .git-blame-ignore-revs`.
