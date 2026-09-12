<!--
Use this template to record the change, its reason, and the required evidence.
Delete sections that do not apply.

If this is your first contribution, the README and Workshop description credit you by name.
Tell the maintainer if the credit is missing.
-->

Closes #

## What this changes

<!-- State what changed and why.
     Ground a fix in project conventions or Qud behavior.
     Ground a design change in Qud's fiction and systems. -->

## Compatibility impact

<!-- List the vanilla records that this change touches.
     State whether the change is additive.

     Use "None. Nothing under mod/ changes." for documentation and tooling changes.

     Name any population table or commonly edited record that this change touches.
     Charter rule 1 requires this information. -->

## Checklist

- [ ] `python3 tools/validate_mod.py` passes
- [ ] `CHANGELOG.md` is updated, or the `skip-changelog` label is applied when no subscriber-facing record exists
- [ ] The PR title is a Conventional Commit, such as `fix(tables): merge Artifact 3-8 instead of replacing`
- [ ] No development-only file was added under `mod/`
- [ ] **If this touches a screen, lifecycle, or event order:** run `python3 tools/sync_mod.py --dev`, then play the changed path
- [ ] **If this changes player-facing behavior:** search the wiki for affected claims
- [ ] **If this changes documentation:** apply the house writing style and preserve protected text

<!--
The C# compiler runs through a local hook, not CI.
Run tools/compile_scripting.py when the game and its assemblies are available.
Report the result when a scripting change cannot be compiled locally.

The ten validation checks do not read prose.
Review documentation for accuracy in addition to running the checks.
The wiki is a separate repository.
Use tools/check_docs.py --wiki to confirm that repository links still resolve.
-->
