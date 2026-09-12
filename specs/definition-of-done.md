# Definition of Done

A feature is done only when its behavior, records, checks, and project state agree.

## Required checks

- [ ] Every acceptance criterion passes.
- [ ] Every mapped automated test passes.
- [ ] Every mapped manual check passes.
- [ ] Red evidence exists for every automated test that required a red phase.
- [ ] `python3 tools/validate_mod.py --all` passes for changes that affect `mod/`.
- [ ] `python3 tools/check_docs.py` passes for changes that affect documented project behavior.
- [ ] Python unit tests, Ruff, basedpyright, and Prettier pass when their paths change.
- [ ] Applicable pre-commit hooks pass.
- [ ] Runtime checks pass when C# scripts, textures, or game behavior change.
- [ ] Documentation and the changelog are current.
- [ ] `VERSION` contains a valid Semantic Version.
- [ ] The validator passes in normal and strict modes.
- [ ] The changed files and known limitations are recorded.
- [ ] The feature is archived before another feature starts.

## Sign-off

Set `verification.status` to `passed` only after the required checks pass.

Set the feature status to `complete` only after the strict validator passes.
