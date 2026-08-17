# Qud Expanded Community Edition

A community-maintained fork of **[Caves of Qud Expanded](https://steamcommunity.com/sharedfiles/filedetails/?id=1134036260)** by **Mura**.

I publish this as a **separate mod**. It doesn't replace, modify, or take over the original, which
is still Mura's and still available.

> **Development note:** I, VixyGrey, do use AI to help me with development and documentation
> tasks.

---

## Credits

This mod exists because of other people's work, so I'd rather you saw that before anything else.

| Who | What |
|---|---|
| **Mura** (`@mura_raven`) | Created Caves of Qud Expanded and spent years on it. This fork is their mod, continued. |
| **Noble Lark** (a.k.a. **chirps**) | All 18 psionic subtype sprites. |
| **Scrolldier** (a.k.a. Parzival) | Taught Mura to mod Caves of Qud. |
| **Arendeth** | Population table fixes. |
| **Tyrir** | Bug reports, including the 2.2 typo batch. |
| **Crow** | Contributor to the original. |

### Contributors to this fork

| Who | What |
|---|---|
| **[Jah-yee](https://github.com/Jah-yee)** | Fixed the `<stag>` typos that stopped the advanced hoversled floating and the sphere of negative weight registering as a trinket. This project's first outside contribution. |

Mura opened the mod to the community with one condition — *give credit where due, which includes
Noble Lark for the subclass sprites*. I treat that as permanent, and the build fails if
`manifest.json` stops naming Mura. Provenance and the full grant are in
[`docs/PERMISSION.md`](docs/PERMISSION.md).

---

## What it does

- **Psionic Adept** — a third genotype with 18 subtypes, split between casters and martial
  guardians.
- **144 psionic chips** — implantable chips granting real, working mutations to genotypes that
  cannot mutate. Every one of them can be found.
- **Complete weapon and armor families** — bronze through zetachrome, one- and two-handed, with
  consistent stats, tiers and prices.
- **New weapon classes** — katanas, rapiers, halberds, greataxes, greatswords, war hammers,
  wristblades and more.
- **Skill and economy retuning**, and a home base building in Joppa.

**Two places to read more, and they don't overlap.** The
[wiki](https://github.com/vixygrey/qud-expanded-community-edition/wiki) covers how the mod *plays* —
builds, synergies, opening strategy, what each system is for. [`docs/FEATURES.md`](docs/FEATURES.md)
is the complete reference and the authoritative source for every figure: tiers, weights, prices, drop
rates, stat modifiers, option defaults.

### You can turn most of it off

Eleven options, in Qud's own options menu under **Mods**. If you want the weapons and armor but not
the chip economy, or vanilla's skill requirements back, or the Joppa building left alone, you can
have that — nobody should need to swallow the whole mod to get one part of it.

**When a change takes effect varies, and it's the part people get caught by:**

- **Immediately** — psionic chips in loot, skill point costs. Hit points and skill points per level
  apply from your next level.
- **On restart** — the eased skill requirements. Qud builds each power's requirement list once per
  session.
- **On a new character** — mutation points, starting skills, starting reputation, both Chip
  Interface options, the Joppa building. These are read at character creation or baked into the
  save.

[`docs/FEATURES.md`](docs/FEATURES.md) §13 lists every option, its default and its scope. That
document is also the complete reference for the mod itself: every system, all 348 new blueprints and
211 vanilla merges.

## Requires a new character

Some identifiers changed during the fork, and Qud writes those into save files, so **start a new
character with this mod enabled.** Saves from the original mod won't work.

---

## Compatibility with the other Expanded mods

> ⚠️ **Do not enable this and the original *Caves of Qud Expanded* at the same time.** Pick one.

This fork is a continuation of Mura's mod, so it defines the same things the original does — **36 C#
types with the same names in the same namespace**, one per psionic chip part. Qud reports that as
`==== TYPE CONFLICTS DETECTED ====` and the result is undefined: whichever loads first wins, and you
may get either mod's version of any given part. It isn't a bug in either mod, it's what a fork *is*.
Saves don't carry across either, as above.

The other two mods in the family are fine, and are unaffected by this fork:

| Mod | | |
|---|---|---|
| **Caves of Qud Expanded** (Mura's original) | ❌ | Same 36 types in `XRL.World.Parts` — enable one or the other |
| **Caves of Qud Expanded — The Grand Bazaar** | ✅ | No shared records or types with this fork |
| **Caves of Qud Expanded — Experience Curve Beta** | ✅ | Script-only, and this fork never touches experience |

Where those green ticks come from, so you can judge them: I compared every object, population table
and C# type the three mods declare. The Bazaar shares **no** object name, **no** C# type, and **not
one** vanilla record merged by both — its only merge target is vanilla's `EmptyTent` table, which this
fork doesn't touch — and all 79 of its blueprint references resolve. The Experience Curve ships no XML
at all, and its one class handles `AwardXPEvent`, which nothing in `mod/Scripting/` goes near. Neither
declares a dependency on the original, and Mura's own description of the Bazaar says it works with or
without it.

That is a record-level comparison rather than a play-test of every combination, which is the honest
limit of the claim. If you hit something anyway, please [file an
issue](https://github.com/vixygrey/qud-expanded-community-edition/issues) — that's the compatibility
promise this fork is built on, and I'd want to know.

---

## Installing

**From the Workshop** — subscribe, and enable the mod in Qud's mod menu.

**Manually** — copy the **`mod/` directory** into Qud's Mods folder:

| Platform | Path |
|---|---|
| macOS | `~/Library/Application Support/com.FreeholdGames.CavesOfQud/Mods/` |
| Windows | `%USERPROFILE%\AppData\LocalLow\Freehold Games\CavesOfQud\Mods\` |
| Linux | `~/.config/unity3d/Freehold Games/CavesOfQud/Mods/` |

Only `mod/` is the mod. Everything else in this repository is development tooling and never reaches
the Workshop.

---

## Contributing

I'd be glad of the help, and I credit every outside contribution by name in the pull request that
merges it — you shouldn't have to ask. [`CONTRIBUTING.md`](CONTRIBUTING.md) is the full guide, and
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) applies to me as much as to anyone.

The rules I maintain this fork under are in [`docs/CHARTER.md`](docs/CHARTER.md) — six of them,
covering compatibility, causality, credit, developer experience, safety, and configurability. I mean
them as constraints rather than aspirations, and most are mechanically enforced.

[`docs/LESSONS.md`](docs/LESSONS.md) collects the traps I've hit, mostly about Qud itself. Worth a
skim before a first change.

[`docs/STYLEGUIDE.md`](docs/STYLEGUIDE.md) covers naming, layout, and formatting. **Read §1 before
renaming anything** — several conventions look like mess and are load-bearing identifiers, and
breaking one fails silently with no error anywhere.

### There is no build step

Qud loads the XML in `mod/` directly. You need no toolchain to contribute.

### Validation

One command, and nothing to install beyond Python 3:

```bash
python3 tools/validate_mod.py
```

It checks XML and JSON well-formedness, blueprint reachability, `Load="Merge"` discipline on every
vanilla record, C# part resolution, the Workshop upload target, and the manifest's credit field.
It also enforces charter rule 5 against `mod/Scripting/` — no file I/O, network, reflection,
shelling out, external assemblies or Harmony — and flags any instance field on a `[Serializable]`
type, since that layout is written into every player save.
The same checks run in CI on every pull request.

After a Caves of Qud update, run these two as well:

```bash
python3 tools/check_vanilla_drift.py
```

It compares the mod against your installed copy of the game and catches the two failure modes that
are otherwise completely silent: a `Load="Merge"` whose vanilla target no longer exists, and the
custom anatomies drifting from vanilla's `Humanoid`.

```bash
python3 tools/snapshot_qud_api.py
```

It regenerates `tools/qud-api.json`, the committed list of every part class and blueprint name the
game exposes. That snapshot is what lets `validate_mod.py` check part names and blueprint
references **in CI**, where there is no game to read and no decompiler to run. Generating it needs
both — `ilspycmd` for the class names, your install for the blueprints — which is exactly why the
answer is committed rather than computed on demand.

The snapshot records the Steam build it came from, and `--check` compares it against what is
installed without writing anything. A stale snapshot fails as a false positive on a newly added
vanilla name, which is loud; that is the intended failure direction, since silence is the thing
these checks exist to catch.

### Regenerating the Workshop preview image

`mod/preview.png` is committed, so you only need this if you're changing it:

```bash
tools/build_preview.sh
```

It composites the fork's green `- CE` and `& VixyGrey` marks onto `tools/preview-base.png` —
Mura's original logo, kept unmodified and byte-identical to `git show upstream-2.2:preview.png`.
Unlike the validators it needs ImageMagick and a macOS system font, so I left it out of the
validation gate and it doesn't run in CI. Sizes, angles and colours live in the script rather than
in someone's image editor; see the header, and `docs/STYLEGUIDE.md` §7.3 for why the fork's marks
deliberately don't match Mura's lettering.

### Local hooks — worth installing

```bash
pre-commit install --install-hooks
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

The hooks run the same checks CI does, so they fail in seconds instead of after a round trip. One of
them CI **cannot** run: `no-commit-to-main` refuses a commit on `main` before it exists. By the time
CI sees such a commit it has already been made, and the server-side ruleset can only reject the
push afterwards.

I know that one matters because I skipped installing these and then committed to `main` (#120).

**If you get `Cowardly refusing to install hooks with core.hooksPath set`,** something in your git
config — usually a dotfile manager wiring in global hooks — has set `core.hooksPath`, and
`pre-commit` won't write `.git/hooks/` while it is. If your global hook delegates to the per-repo
one, which is the common arrangement, unset it for the length of the install:

```bash
saved=$(git config --global --get core.hooksPath)
git config --global --unset core.hooksPath
pre-commit install --install-hooks
git config --global core.hooksPath "$saved"
```

Then check it took, by trying to commit on `main` and being told no.

### Workflow

[`CONTRIBUTING.md`](CONTRIBUTING.md) has it in full — issue first, short-lived branch, small PR,
squash merge, and what each pull request needs before I can take it.

---

## Licence

My contributions are **Apache-2.0** for code ([`LICENSE`](LICENSE)) and **CC BY 4.0** for content
and documentation ([`LICENSE-CONTENT`](LICENSE-CONTENT)).

The inherited work is Mura's and the subtype sprites are Noble Lark's — neither is mine to license,
so neither is covered. [`COPYING.md`](COPYING.md) says exactly what you may reuse and from whom, and
[`NOTICE`](NOTICE) carries the credit that has to travel with any redistribution.

## Layout

```
mod/     the shipped mod — the only directory uploaded to the Workshop
docs/    CHARTER, FEATURES, LESSONS, PERMISSION, STYLEGUIDE, and Mura's original documents
tools/   validation, drift checking, and the preview-image generator
```

`git diff upstream-2.2` shows what I've changed since Mura's 2.2 release:

```bash
git diff -M --ignore-cr-at-eol upstream-2.2 HEAD
```

**Since #78 that diff is dominated by formatting**, because I reformatted the XML wholesale and long
elements now put one attribute per line. `-w` does *not* help: it ignores whitespace within a line,
and the reformat splits single lines into many, which git sees as genuinely different lines. Read
the raw diff as "what files changed", not "what changed in them".

Two things still work, and they're the ones that matter:

- **Retrieving Mura's originals.** `git show upstream-2.2:<path>` reproduces any file byte-for-byte
  exactly as they wrote it. The tag is immutable and I never move it, so that stays true permanently
  regardless of any future reformat.
- **`git blame`.** The reformat commit is listed in [`.git-blame-ignore-revs`](.git-blame-ignore-revs),
  so blame attributes lines to whoever actually wrote them. Enable it once per clone:
  `git config blame.ignoreRevsFile .git-blame-ignore-revs`.
