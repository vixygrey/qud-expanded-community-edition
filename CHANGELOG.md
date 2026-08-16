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

### Added

- **(internal)** `docs/STYLEGUIDE.md` — naming, layout, XML and C# formatting, and Steam Workshop
  requirements. §1 records which identifiers are safe to rename and which are load-bearing.
  ([#16](https://github.com/vixygrey/qud-expanded-community-edition/issues/16))
- **(internal)** `CLAUDE.md` — the fork charter: compatibility, causality, credit, DX, safety, and
  configurability, plus the contribution workflow.
- **(internal)** `docs/FEATURES.md` — complete feature reference reconstructed from source: 350
  new blueprints, 209 vanilla merges, and a severity-ranked defect checklist.
- **(internal)** `docs/PERMISSION.md` — fork permission, provenance, and credit obligations.
- **(internal)** This changelog.

### Fixed

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
- **Pre-commit hooks** running the same gates locally, plus a guard against committing to `main`.
  ([#18](https://github.com/vixygrey/qud-expanded-community-edition/issues/18))
- Repository placed under version control with the pristine upstream 2.2 import tagged
  `upstream-2.2`, so `git diff upstream-2.2` always shows exactly what the fork changed.

## Credits

Every release carries the credit list in [`docs/PERMISSION.md`](docs/PERMISSION.md) §4 —
**Mura** (`@mura_raven`) for the original mod, and **Noble Lark** for the psionic subtype sprites,
named explicitly as the one condition of the fork permission.

[Unreleased]: https://github.com/vixygrey/qud-expanded-community-edition/commits/main
