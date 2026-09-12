# Verification Protocol

Use this protocol for every feature that changes shipped mod behavior, tooling behavior,
validation behavior, or contributor workflow.

## 1. Specification gates

- [ ] Give every acceptance criterion a stable ID.
- [ ] Describe observable behavior for every acceptance criterion.
- [ ] Map every acceptance criterion to an automated test or manual check.

## 2. Design gates

- [ ] Record the design summary and constraints.
- [ ] Record affected repository paths, interfaces, identifiers, and data flow.
- [ ] Record rejected alternatives when the design has meaningful alternatives.

## 3. Test-driven design gates

- [ ] Run each new automated test before implementation.
- [ ] Record the failing result in the test `red_evidence` field.
- [ ] Record the executable command in each automated test record.
- [ ] Implement the smallest complete change that satisfies the specification.
- [ ] Run the mapped tests after implementation.
- [ ] Record test results and evidence.

## 4. Automated checks

- [ ] Run `python3 tools/validate_mod.py --all` for mod structure, references,
      merge discipline, and scripting policy.
- [ ] Run `python3 tools/check_docs.py` for documentation links, sections, claims,
      preserved files, counts, and CI metadata.
- [ ] Run `python3 -m unittest discover -s tools -v` for the Python tool tests.
- [ ] Run `ruff check tools/`.
- [ ] Run `ruff format --check tools/`.
- [ ] Run `basedpyright tools/`.
- [ ] Run `npx prettier --check "mod/**/*.xml" "mod/**/*.rpm"`.
- [ ] Run `pre-commit run --all-files`.

Run only the checks that cover the changed paths during development.
Run the complete applicable set before delivery.

## 5. Shipped-content and scripting checks

- [ ] Keep development files outside `mod/`.
- [ ] Preserve save-backed identifiers and resolved Qud references.
- [ ] Use `Load="Merge"` for changed vanilla records and tables.
- [ ] Keep C# scripts compatible with the installed game assemblies.
- [ ] Run `python3 tools/compile_scripting.py` when the required game files exist.
- [ ] Run the manual `check-build-log` hook after a game launch when C# changed.
- [ ] Confirm changed textures and `Tile` names against the installed game when available.
- [ ] Keep scripts free of external file I/O, network access, telemetry, shell execution,
      external assembly loading, Harmony, and reflection.

## 6. Manual checks

- [ ] Exercise the changed game flow when automation cannot observe the behavior.
- [ ] Review every acceptance criterion against its evidence.
- [ ] Review the changed files and known limitations.
- [ ] Review Workshop and manifest metadata when distribution behavior changed.

## 7. Post-flight sign-off

Record the changed files, checks, evidence references, known limitations, reviewer, and date.

- [ ] Run `specs/validate-context.sh` during development.
- [ ] Run `specs/validate-context.sh --strict` before archive.
- [ ] Run `specs/archive-feature.sh` before you start another feature.

Set `active-feature.yaml` field `verification.status` to `passed` only after the required checks pass.

## Definition of Ready

- [ ] Read `specs/definition-of-ready.md`.
- [ ] Complete the user story, acceptance criteria, impact analysis, design, test plan,
      dependencies, risks, and required ADRs.

## Definition of Done

- [ ] Read `specs/definition-of-done.md`.
- [ ] Pass every mapped automated test and manual check.
- [ ] Update the documentation and `CHANGELOG.md`.
- [ ] Confirm that `VERSION` contains a Semantic Version.
- [ ] Run the normal and strict validators.
