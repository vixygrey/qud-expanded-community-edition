# Project Charter Specification

## Status

- Status: Active
- Source: [`docs/CHARTER.md`](../docs/CHARTER.md)

## Scope

This specification defines the non-negotiable rules for compatibility, causality, credit, developer experience, safety, and configuration.

## Observable Behavior

The mod remains compatible with vanilla, future Qud patches, and other mods where the engine permits.

Every change has a stated reason grounded in a defect, Qud behavior, existing data, or player choice.

New content is derived from established curves, tables, and conventions instead of arbitrary values.

The repository keeps Mura's credit and credits outside contributors in player-facing metadata.

The mod loads XML directly from `mod/` without a build step.

Players can choose configurable behavior through options with documented defaults.

## Prerequisites

Read [`docs/FEATURES.md`](../docs/FEATURES.md) and [`docs/STYLEGUIDE.md`](../docs/STYLEGUIDE.md) before changing shipped content.

Use `Load="Merge"` for every changed vanilla object or table.

Run `python3 tools/validate_mod.py` before delivery.

## Safety Rules

Never replace vanilla data when an additive merge is possible.

Never add file I/O outside the mod directory, network access, telemetry, shell execution, external assembly loading, Harmony, or reflection into game internals.

Treat all `mod/Scripting/` code as privileged code that requires subscriber trust.

Keep serializable field layouts stable unless the change explicitly accepts save incompatibility.

Make option handlers idempotent and reversible when runtime mutation is possible.

Keep new behavior behind an option when it changes the world or grants player power.

## Failure Behavior

Reject arbitrary changes that lack a causal explanation.

Reject compatibility changes that discard future vanilla additions or other mod contributions.

Reject a feature when an existing data or engine mechanism provides the correct solution and the proposed code bypasses it.

Report known inherited defects in the validation baseline rather than hiding them.

## Related Files

- [`docs/CHARTER.md`](../docs/CHARTER.md)
- [`docs/FEATURES.md`](../docs/FEATURES.md)
- [`docs/STYLEGUIDE.md`](../docs/STYLEGUIDE.md)
- [`tools/validate_mod.py`](../tools/validate_mod.py)
- [`mod/manifest.json`](../mod/manifest.json)
