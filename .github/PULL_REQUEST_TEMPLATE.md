<!--
Thanks for this. Everything below gathers the required checks and evidence before review. Delete
anything that does not apply.

If this is your first contribution: I credit it by name in the README and the Workshop description,
in this pull request. You shouldn't have to ask, and I'd rather not miss it — tell me if I do.
-->

Closes #

## What this changes

<!-- What, and — more importantly — why. Charter rule 2: a reason grounded in the mod's own
     conventions for a fix, or in Qud's fiction and systems for a design change. -->

## Compatibility impact

<!-- Which vanilla records this touches, and whether the edit is additive.

     "None — nothing under mod/ changes" is a complete answer for docs and tooling.

     If it touches a population table or a record other mods commonly touch, say so. Charter rule 1
     makes this the fork's headline claim, so it's worth a sentence even when the answer is boring.
-->

## Checklist

- [ ] `python3 tools/validate_mod.py` passes
- [ ] `CHANGELOG.md` updated — or the `skip-changelog` label applied, if this genuinely records
      nothing for subscribers
- [ ] The PR title is a conventional commit (`fix(tables): …`) — it becomes the squash commit
- [ ] Nothing new was added under `mod/` that shouldn't ship to subscribers
- [ ] **If this touches a screen, a lifecycle, or an event order** — `python3 tools/sync_mod.py --dev`,
      then played. `docs/LESSONS.md` says before merge, not after: content and value changes can lean
      on the checks, behaviour cannot. Use `--dev` rather than copying `mod/` by hand — it strips
      `WorkshopId`, so a branch build cannot overwrite the live Workshop item
- [ ] **If this changes what a player sees or does** — the wiki has been grepped for what it
      describes. It's a separate repository and not one of these checks reaches it

## C# verification

<!-- Delete this section if mod/Scripting/ is unchanged. -->

- [ ] `python3 tools/compile_scripting.py` passed against the installed game's assemblies
- [ ] I launched Qud with this source deployed and `pre-commit run --hook-stage manual check-build-log` passed
- [ ] I could not run one or both checks: reason and maintainer follow-up are stated below

<!--
Two things worth knowing:

- The C# is compiled locally, not by CI. It needs Caves of Qud's proprietary assemblies, and
  CodeQL cannot cover it either. A compiler proves the source builds, not that it behaves correctly
  in a run.

- Eleven checks run here and all eleven must pass. None reads prose, so if you changed
  documentation, the accuracy is on us rather than on CI. The wiki is documentation that isn't even
  in this repository — CONTRIBUTING.md has the clone URL and `tools/check_docs.py --wiki` checks
  that its links still land, though not that its pages are still true.
-->
