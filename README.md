# Qud Expanded Community Edition

A community-maintained fork of **[Caves of Qud Expanded](https://steamcommunity.com/sharedfiles/filedetails/?id=1134036260)** by **Mura**.

This is a **separate mod**. It does not replace, modify, or take over the original, which remains
Mura's.

> **Development note:** I, VixyGrey, do use AI to help me with development and documentation
> tasks.

---

## Credits

This mod exists because of other people's work.

| Who | What |
|---|---|
| **Mura** (`@mura_raven`) | Created Caves of Qud Expanded and spent years on it. This fork is their mod, continued. |
| **Noble Lark** | All 18 psionic subtype sprites. |
| **Scrolldier** (a.k.a. Parzival) | Taught Mura to mod Caves of Qud. |
| **Arendeth** | Population table fixes. |
| **Tyrir** | Bug reports, including the 2.2 typo batch. |
| **Crow**, **chirps** | Contributors to the original. |

Mura opened the mod to the community with one condition — *give credit where due, which includes
Noble Lark for the subclass sprites*. That condition is treated as permanent here, and the build
fails if `manifest.json` stops naming Mura. Provenance and the full grant are recorded in
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

Some identifiers changed during the fork, and Qud writes those into save files. **Start a new
character with this mod enabled.** Saves from the original mod are not compatible.

---

## Installing

**From the Workshop** — subscribe, and enable the mod in Qud's mod menu.

**Manually** — copy the **`mod/` directory** into Qud's Mods folder:

| Platform | Path |
|---|---|
| macOS | `~/Library/Application Support/com.FreeholdGames.CavesOfQud/Mods/` |
| Windows | `%USERPROFILE%\AppData\LocalLow\Freehold Games\CavesOfQud\Mods\` |
| Linux | `~/.config/unity3d/Freehold Games/CavesOfQud/Mods/` |

Only `mod/` is the mod. Everything else in this repository is development tooling and is not
uploaded to the Workshop.

---

## Contributing

The rules this fork is maintained under are in [`CLAUDE.md`](CLAUDE.md) — six of them, covering
compatibility, causality, credit, developer experience, safety, and configurability. They are
constraints rather than aspirations, and most of them are mechanically enforced.

[`docs/STYLEGUIDE.md`](docs/STYLEGUIDE.md) covers naming, layout, and formatting. **Read §1 before
renaming anything** — several conventions that look like mess are load-bearing identifiers, and
breaking them fails silently with no error anywhere.

### There is no build step

Qud loads the XML in `mod/` directly. You need no toolchain to contribute.

### Validation

One command, no dependencies beyond Python 3:

```bash
python3 tools/validate_mod.py
```

It checks XML and JSON well-formedness, blueprint reachability, `Load="Merge"` discipline on every
vanilla record, C# part resolution, the Workshop upload target, and the manifest's credit field.
The same checks run in CI on every pull request.

After a Caves of Qud update, also run:

```bash
python3 tools/check_vanilla_drift.py
```

That one compares the mod against your installed copy of the game and catches the two failure
modes that are otherwise completely silent: a `Load="Merge"` whose vanilla target no longer
exists, and the custom anatomies drifting from vanilla's `Humanoid`.

### Optional local hooks

```bash
pre-commit install
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

### Workflow

Issue first, short-lived branch, small PR, squash merge. Every PR updates
[`CHANGELOG.md`](CHANGELOG.md) and states its compatibility impact. Commit bodies carry the
*reason* for a change, not just its content — that is charter rule 2, and it is the rule most
easily lost.

---

## Layout

```
mod/     the shipped mod — the only directory uploaded to the Workshop
docs/    FEATURES, PERMISSION, STYLEGUIDE, and Mura's original documents
tools/   validation and drift checking
```

`git diff upstream-2.2` shows everything this fork has changed since Mura's 2.2 release. Add
`--ignore-cr-at-eol`, since the mod was normalised from CRLF to LF.
