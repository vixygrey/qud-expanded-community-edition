<!--
Thanks for this. Everything below is what CI already checks, gathered here so you meet it before
the red X rather than after. Delete anything that doesn't apply.

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

<!--
Two things worth knowing:

- The C# is compiled by a local hook, not by CI. tools/compile_scripting.py builds mod/Scripting/
  against the game's own assemblies, but it needs Caves of Qud installed and skips without it, and
  CodeQL can't cover the C# either. So nothing here compiles it. If you changed C# and couldn't run
  the hook, say so and I'll run it — and say whether you tested in game, which is a separate question
  a compiler can't answer.

- Ten checks run here and all ten must pass. None of them reads prose, so if you changed
  documentation, the accuracy is on us rather than on CI.
-->
