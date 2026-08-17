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
| **Noble Lark** | All 18 psionic subtype sprites. |
| **Scrolldier** (a.k.a. Parzival) | Taught Mura to mod Caves of Qud. |
| **Arendeth** | Population table fixes. |
| **Tyrir** | Bug reports, including the 2.2 typo batch. |
| **Crow**, **chirps** | Contributors to the original. |

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

[`docs/FEATURES.md`](docs/FEATURES.md) is the complete reference: every system, all 350 new
blueprints and 209 vanilla merges.

## Requires a new character

Some identifiers changed during the fork, and Qud writes those into save files, so **start a new
character with this mod enabled.** Saves from the original mod won't work.

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
merges it — you shouldn't have to ask.

The rules I maintain this fork under are in [`CLAUDE.md`](CLAUDE.md) — six of them, covering
compatibility, causality, credit, developer experience, safety, and configurability. I mean them as
constraints rather than aspirations, and most are mechanically enforced.

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

After a Caves of Qud update, run this one too:

```bash
python3 tools/check_vanilla_drift.py
```

It compares the mod against your installed copy of the game and catches the two failure modes that
are otherwise completely silent: a `Load="Merge"` whose vanilla target no longer exists, and the
custom anatomies drifting from vanilla's `Humanoid`.

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

### Optional local hooks

```bash
pre-commit install
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

### Workflow

Issue first, short-lived branch, small PR, squash merge. Every PR updates
[`CHANGELOG.md`](CHANGELOG.md) and states its compatibility impact. Commit bodies carry the
*reason* for a change, not just its content — that's charter rule 2, and it's the one I lose
soonest if I stop watching for it.

---

## Layout

```
mod/     the shipped mod — the only directory uploaded to the Workshop
docs/    FEATURES, LESSONS, PERMISSION, STYLEGUIDE, and Mura's original documents
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
