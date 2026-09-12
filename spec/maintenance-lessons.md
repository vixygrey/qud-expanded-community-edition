# Maintenance Lessons Specification

## Status

- Status: Active
- Source: [`docs/LESSONS.md`](../docs/LESSONS.md)

## Scope

This specification defines evidence and maintenance rules learned from prior failures.

## Observable Behavior

Investigations read the exception type before forming a crash hypothesis.

Investigations read the repository, installed Qud data, and assembly metadata before inventing behavior.

Investigations distinguish a mechanism from its consumers.

Investigations distinguish declared data from resolved inherited data.

Investigations treat missing search results as inconclusive until the search itself is confirmed.

Static checks and runtime launches are reported as separate evidence.

Capped listings report their cap and the omitted count.

## Prerequisites

Confirm that a tool ran successfully before using its output as evidence.

Read the full control flow around an API before treating a member as an extension point.

Resolve `Inherits=`, `*noinherit`, and `*delete` before counting tags or parts.

Check Qud behavior against installed files at the paths documented in [`docs/LESSONS.md`](../docs/LESSONS.md).

## Safety Rules

Do not use `rg -r` as a recursive search flag. Ripgrep already recurses by default.

Do not read or write the same generated file during a generator run.

Do not use `git checkout <file>` to undo a probe without confirming index state.

Do not treat a passing static check as proof that gameplay behavior occurs.

Do not infer player-facing behavior from a field name, method name, or comment alone.

## Failure Behavior

Report a failed, skipped, stale, or inconclusive check as unresolved evidence.

Stop and correct the measurement when a count conflicts with the resolved data.

Add a positive control when a test suite contains only failure cases.

Record a new operational trap in [`docs/LESSONS.md`](../docs/LESSONS.md) after a failure produces a durable rule.

## Related Files

- [`docs/LESSONS.md`](../docs/LESSONS.md)
- [`tools/validate_mod.py`](../tools/validate_mod.py)
- [`tools/check_build_log.py`](../tools/check_build_log.py)
- [`tools/snapshot_qud_api.py`](../tools/snapshot_qud_api.py)
