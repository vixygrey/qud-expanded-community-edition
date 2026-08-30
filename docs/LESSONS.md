# Lessons learned

Operational traps I hit while maintaining this fork, written down so nobody pays for them twice.
I add to this whenever something bites — the reasoning is the durable artifact, not the fix.

Some are about Caves of Qud itself and should be useful to anyone modding it: where the game keeps its
own API documentation, which vanilla data files aren't valid XML, how an extension point fails when you
forget its marker attribute. Others are about git, GitHub and the tooling here — and a growing number
are about the same underlying problem, which is telling a real green result from one that means
nothing.

(That first sentence used to read "most of these", which stopped being true somewhere around the
thirteenth entry and was corrected in #137. A count in prose rots exactly as described in the last
section of this document, so there is deliberately no proportion quoted here now — nothing checks it.)

---

## Read the crash *type* before forming a hypothesis

A Qud crash report's exception type narrows the search enormously, and it's free:

- `EXC_BAD_ACCESS` in the **Stack Guard** region with `RECURSION LEVEL n` markers is a **stack
  overflow** — unbounded recursion inside the game, not an exception thrown by mod code. A
  handler that calls two functions and returns cannot produce it.
- A managed exception appears in `game_log.txt` with a stack trace instead, and names the type.

I chased the options-menu crash through two wrong hypotheses before reading the report properly.
The recursion markers pointed at the game's own UI, which immediately made "my C# threw something"
the wrong tree.

The crash report lives in macOS's crash reporter, **not** in Qud's own logs — `game_log.txt` had
four lines because the process died before logging started.

## Stacked PRs do not survive a squash merge of their base

Squash-merging PR A **and deleting its branch** does not retarget PR B stacked on it — GitHub
**auto-closes B**. Once B's branch is rebased, `gh pr reopen` fails outright
(*"Could not open the pull request"*) and `--base` cannot be changed on a closed PR. The only
recovery is a fresh PR.

The cause is that a squash merge creates a commit that is not an ancestor of B, so B's history no
longer descends from `main`.

**Do instead:** retarget the child to `main` *before* merging the base, or merge the base without
deleting its branch. Recover with
`git rebase --onto origin/main <old-base-tip> <child-branch>` — and capture `<old-base-tip>`
*before* merging, because it's painful to find afterwards. Better still, don't stack when the base
will merge soon.

## A closing keyword next to an issue number links it, whatever the sentence is doing

GitHub scans a pull request body for a closing keyword followed by an issue reference and matches it
as a **bare substring**. The surrounding grammar is not read — not the tense, not the subject, not
whether the sentence is about this pull request at all. There are **nine** keywords, and the
past-tense forms are the ones most likely to be written by accident:

```
close   closes   closed
fix     fixes    fixed
resolve resolves resolved
```

Two ways this has bitten, and they fail differently:

Real examples, with the issue numbers **masked** — see the warning below, because writing them
faithfully here would arm this document:

```
## Why this doesn't close #NNN     <- a denial.      registered it; a later PR closed it on merge
... and closed #NNN                <- narration.     the reference was to a different issue entirely
I would rather you close #NNN      <- delegation.    in a body that also said "No closing keyword"
> "...I would rather you close #NNN..."  <- quoting the above, in the PR that documented it
```

Those were #286 against #284, #292 against #10, #360 against #339, and #362 against #339 again.

> ⚠️ **Quoting an example arms it.** The fourth entry happened while writing the third: the pull
> request documenting the mistake quoted the offending sentence verbatim, in both its body and its
> commit message, and registered the same issue a second time. That is why the block above uses
> `#NNN`. **When you write up a closing-keyword mistake, mask the number** — a bug report about a
> live wire is still a live wire.

The first is the memorable one and the second is the ordinary one. #286 was written to advance #284
without finishing it, and nothing in it counted: not the paragraph listing which acceptance boxes
were still open, not the commit trailer saying the issue stays open, not a comment on the issue
saying the same. #292 was not arguing with the parser at all — it was a sentence about what an
earlier pull request had done, and the reference was not even to the issue the pull request was
about.

So the rule is adjacency, not intent. Denial, narration, quotation, questions and **delegation** all
buy exactly nothing, and an entry that lists the ways a sentence can be shaped will always miss one —
the first version of this entry omitted the three past-tense keywords, and `closed` caught me the
next day.

The third example is the one worth staring at. The sentence declared *"No closing keyword"* and then
contained one nine words later, in the clause asking a human to do the closing by hand. Asking for
something to be done manually is not a way of saying it should not happen automatically; the parser
reads a verb and a number, and there is no register of speech it declines to read.

**Do instead:** keep the keyword away from the reference in every form. **"Why #N stays open"**,
**"Part of #N"**, **"advances #N"**; and when narrating, name the issue without the keyword —
*"resolved issue 10"*, *"#50 fixed that"*. Before merging a pull request that only advances an
issue:

```bash
gh pr view <n> --json closingIssuesReferences
```

It should come back empty. It found both instances above, and would have found either at any point
before the merge.

Afterwards, the close event on the issue timeline carries `commit_id: null`. That distinguishes a
linked-reference close from a commit-message close, and it is the fastest way to find out why an
issue you did not mean to close is shut.

## `closingIssuesReferences` checks the link, not that the work matches the issue

The two entries above are both about a keyword closing an issue nobody meant to close. This is the
other failure at the same seam, and the check prescribed above does not catch it: **the link was
correct and the work was not complete.**

#673 asked for three lessons when I read it. It was edited before my pull request merged and asked for
**four** — a new entry, and a fourth row in an existing table. #675 closed it as completed with three.
`closingIssuesReferences` came back exactly right: `[667, 672, 673, 674]`. Every one of those was an
issue the PR meant to close. It has nothing to say about whether what merged still matches what the
issue says, and a closing keyword written on Monday closes an issue rewritten on Tuesday.

> **Re-read the issue body before merging, not only before starting.** For a bundle it matters more,
> because one stale reading is invisible among three correct ones — and the closing keyword makes the
> issue disappear from the backlog either way, so nothing surfaces the gap afterwards.

Cheapest form: `gh issue view <n> --json title,body` immediately before the merge, and compare against
what the branch actually contains. It costs one command per issue and would have caught this.

**And the link check lags an edit.** Writing this entry, its own pull request body said *"#675 closed
#673 …"*, so `closingIssuesReferences` returned `[673, 678]` — the *"writing about a closing keyword is
writing one"* trap, in the pull request about that trap. Rewording the sentence fixed the body
immediately and **the API kept reporting the stale pair for another minute or so**. Re-check after a
pause rather than concluding the link is stuck; and do not read a single clean result straight after an
edit as proof either, for the same reason.

## The check you drop is the one that was working

`gh pr view <n> --json closingIssuesReferences` is prescribed two sections above, by me, after it
caught two accidental issue closures. I then ran it on five consecutive pull requests, found nothing,
stopped running it, and the sixth closed an issue I had explicitly written that I did not want closed.

The five clean results were not evidence the check was unnecessary. They were the check working.

What made it stoppable was that the work had become routine — same shape of pull request, same
sections, same body template, six times in an afternoon. Routine is exactly when a verification step
feels redundant, and exactly when it is not, because it is also when nobody is reading their own
boilerplate closely. The sentence that closed the issue was in a paragraph I had written five times
before and skimmed on the sixth.

> **A check that has never failed for you is indistinguishable from a check that cannot fail.** The
> only difference is in the counterfactual, which you never see. Treat a run of clean results as the
> reason to keep running it, not as permission to stop.

Two things that would have caught it, in order of cost:

- **Run the check.** It is one command and it reports the answer as a list.
- **Put it where it cannot be skipped.** A check that lives in someone's habit is a check with an
  expiry date. The repository already prefers mechanical enforcement to prose for exactly this reason,
  and `docs/CHARTER.md` rule 4 says so: *"Keep new checks in the script rather than in prose."*

**That second one is done** — [`tools/check_pr_intent.py`](../tools/check_pr_intent.py) runs in the
**PR conventions** job and fails a pull request whose body names an issue after `Part of`, `Advances`
or `Why … stays open` while `closingIssuesReferences` says it would close that same issue (#361). It
catches all three instances above, including this one, and its tests carry them in their own words so
that a regular expression over prose cannot quietly stop matching.

**Keep running the manual check anyway.** The automated one needs a *stated* intent to contradict, so
it cannot see a pull request that carries a closing reference and says nothing either way — and that
body is the easier one to write by accident, not the harder one. What the check removes is the case
that has actually bitten, three times.

## A null in a sentence is a body part that was never chosen

A player reported that a chip-granted Ice Ray failed with *"Your is too damaged to do that"*. The
missing noun **was the whole diagnosis**: the game builds that sentence as
`"Your " + BodyPartType + " is too damaged to do that!"`, so an empty gap between two words is a null
field rendered, not a typo in the message.

What produced it: `FlamingRay` and `FreezingRay` are *variant* mutations, deriving their body part
from a chosen variant. `BaseMutation.Create` only calls `SetVariant` when the variant is non-empty,
and the chip base class passes `null` — so the derivation never ran. The mutation's own fallback
looked like it should save this, and does not: it assigns the `Variant` **field** directly rather
than going through `SetVariant`, so the body part stays unset even once a variant exists.

Three things worth keeping from it:

- **Read the message as a format string.** *"Your is"* has a hole in it, and the hole is the variable.
  That narrowed a whole-catalogue question to one field in one class before any code was opened.
- **A fallback that assigns a field is not the same as one that calls the setter**, and the
  difference only shows when the setter does more than assign. Both of these look correct in
  isolation.
- **The player's own theory was wrong and worth discarding early.** They were a True Kin and assumed
  the genotype mattered; it does not, and chasing that would have cost the afternoon.

Vanilla never reaches this defect, which is why it survived: its only three items using that base
class grant mutations that have no variants. A mod that grants a wider set of mutations through a
vanilla mechanism is exactly the thing that finds the corners vanilla's own content never turns.

## Writing *about* a closing keyword is writing one

The fourth instance is the pull request that added the check above, and it is the only one where the
check was present and still did not cover it.

#403's body explained the defect by quoting #360's sentence. The quotation contained the words
*close* and *#339* next to each other, so GitHub resolved it, and `closingIssuesReferences` came back
naming an issue the pull request had no business touching. **The new check passed, correctly** —
there was no `Part of #339` for the link to contradict, only a quotation. The manual look caught it,
about thirty seconds after I had written in that same body that the automated check cannot see this
case.

Two things worth having in writing:

- **The reference resolves from the commit messages too, not only the body.** I fixed the body first
  and `closingIssuesReferences` did not change, because the commit message carried the same
  quotation. Editing one and re-checking is what showed it; fixing the body alone would have looked
  like a fix and left the link in place.
- **A document describing this trap cannot quote the trap.** The way out is the one this entry
  already uses without ever having said so: *describe* the offending sentence rather than reproduce
  it. "A clause asking a human to do the closing by hand" carries the same meaning and resolves to
  nothing.

So the quarantine is wider than it looks. It is not only your own intent that has to keep the keyword
away from the number — an explanation, a quotation, a changelog entry and a commit message all parse
the same way, and none of them is a register the parser declines to read.

That second point generalises past this check. Several of the habits in this document are still
habits, and every one of them has the same failure mode.

## Squash merging invalidates blame-ignore SHAs

`.git-blame-ignore-revs` must list the **squash commit on `main`**, not the commit from the
feature branch — squash merging replaces the branch SHA, so an entry written before merge points
at a commit that doesn't exist in history and is silently ignored.

So **an entry can only be added after its PR merges**, in a follow-up. And because the squash
collapses a whole PR into one commit, a PR containing a mechanical change plus anything else
produces a squash commit that isn't purely mechanical. If I mean a change to be blame-ignored, it
gets its own PR.

Verify with `git merge-base --is-ancestor <sha> HEAD` — a listed SHA that fails this check is doing
nothing.

## Normalisation rules need explicit exemptions for preserved documents

`* text=auto eol=lf` in `.gitattributes` reaches Mura's original documents too, and those are a
provenance record meant to stay byte-for-byte. They need `-text` to opt out of EOL conversion
entirely. Check with `git ls-files --eol` and `git add --renormalize`, not by reading the
attribute file — `git check-attr` reports an inherited `eol` value even where it doesn't apply.

## The game ships its own API documentation

`CoQ.app/Contents/Resources/Data/Managed/Assembly-CSharp.xml` — **898 documented members** with
summaries, including the full `QudGameBootModule.BOOTEVENT_*` lifecycle and the
`AbstractEmbarkBuilderModule` chargen surface. It's better than metadata analysis and I wasn't
using it.

Equally useful is what it *omits*: `GenotypeFactory`, `SkillFactory` and `MutationPoints` are
absent, which is a real signal about what is and isn't a supported extension point.

## For "does this API exist", read the DLL metadata, not the XML docs

`Assembly-CSharp.xml` documents **some** members. `GenotypeFactory`, `SkillFactory` and
`MutationPoints` appear in none of it — and all three exist, public, in the assembly. I briefly
mistook absence from the documentation for absence from the API, which nearly redirected an entire
design toward sub-mod splits it didn't need.

Read the assembly instead. A metadata reader gives you 7,837 types with field and method names,
signatures and visibility flags; point its `DLL` constant at
`CoQ.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll`. Mine lives outside this repository,
so it isn't something a clone gets — any ECMA-335 metadata reader will do.

## The vanilla game data is readable — check it

`~/Library/Application Support/Steam/steamapps/common/Caves of Qud/CoQ.app/Contents/Resources/Data/StreamingAssets/Base`

30 XML files plus `ObjectBlueprints/`. **Not** `CoQ_Data/StreamingAssets`, which holds only DLC —
that wrong turn made me report several questions as unanswerable when they weren't.

Two gotchas when reading it:

- **Five vanilla files are not well-formed XML.** `Items.xml`, `Creatures.xml`, `Furniture.xml`,
  `Books.xml` and `Manual.xml` embed control characters as numeric references (`&#11;`, `&#15;`,
  `&#27;`, `&#x7;`) which Qud accepts and XML 1.0 forbids. A strict parser rejects them.
- **Never swallow those failures.** Skipping `Items.xml` silently makes every object it defines
  look absent — which surfaced as *208 phantom "orphaned merge" defects* before I surfaced the
  parse errors. `tools/check_vanilla_drift.py` strips the invalid refs and reports anything it
  still cannot read.
- **Reuse that parser rather than writing another.** `parse(path, lenient=True)` in
  `tools/check_vanilla_drift.py` is importable, and anything reading the game's blueprints should go
  through it:

  ```python
  import sys; sys.path.insert(0, "tools")
  from check_vanilla_drift import parse
  root = parse(path, lenient=True)
  ```

  Knowing the drift checker copes is not the same as knowing the fix is one import away. I read the
  warning above, wrote my own `ET.parse` inside a `try/except` anyway, and got two empty results that
  looked like findings — that vanilla has no shield above AV 2, and no items in the `Arm` slot at
  all. Both are false; the second is wrong by 46 items. Going through `parse` took the same scan
  from **1,913** blueprints to **5,202**, because everything `Items.xml` defines was missing.

## Verify Qud's behaviour against installed mods, not from memory

Several confident-sounding assumptions I held about Qud were wrong, and only checking the ~87 mods
installed under `~/Library/Application Support/Steam/steamapps/workshop/content/333640/` caught
them:

- Mod options **can** gate content. `PopulationManager.Populations` stays mutable at runtime, so
  drops and behaviour are option-gateable; only chargen- and save-baked definitions are not.
- The loader dispatches on **root element**, not filename — so XML filenames are free.
- Dev files **do** ship to subscribers.

That directory is the cheapest ground truth available. Use it before asserting how Qud behaves.

## Distinguish "frozen by saves" from "frozen by vanilla identity"

They look alike and behave completely differently. Renaming a vanilla blueprint or population
table doesn't break a save — it silently orphans the `Load="Merge"` so the edit stops applying,
with **no error anywhere**. See `docs/STYLEGUIDE.md` §1.

## A generator must never read the file it writes

I first wrote `tools/build_preview.sh` to read `mod/preview.png`, composite the fork's marks onto
it, and write back to the same path. That's correct exactly once. `mod/preview.png` is now the
*composited* result, so a second run would have layered `- CE` and `& VixyGrey` on top of marks
that were already there.

The fix: keep the pristine input as its own committed file — `tools/preview-base.png`, Mura's
original, verified byte-identical to `git show upstream-2.2:preview.png` — and generate from that.

Two things make this worth remembering rather than filing under "obvious":

- **It fails plausibly, not loudly.** A double-composited image isn't corrupt and doesn't error.
  It renders, and a binary diff tells you nothing. Same silent-failure class as an orphaned
  `Load="Merge"`.
- **The general form is broader than images.** Any generator whose output overwrites its own input
  has stopped being idempotent — it applies to anything that appends, wraps, or composites. It's
  the same reasoning that makes charter rule 5 require option handlers to make data *match* the
  option's value rather than performing a one-way edit.

Two habits catch it: make `regenerate → diff against the committed artefact` part of finishing the
work, and **guard the input's identity** rather than trusting it — that script refused to run unless
the base was 418×312, because every offset was measured against that logo and a swapped base would
have misplaced the marks instead of erroring.

> **The pipeline this describes no longer exists** (#500). `mod/preview.png` is now generated from
> nothing but code — `tools/build_preview.py` reads no image at all, so the failure mode it taught
> me is structurally impossible there now. The lesson keeps its place because the general form is
> what matters: *any* generator whose output overwrites its own input has stopped being idempotent,
> and the one here happened to be an image.

## Static checks answer "is it correct". Launching answers "does it happen"

Six pull requests of naming and gender work reached `main` fully green: `validate_mod.py`,
`check_docs.py`, 354 tests, a purpose-built harness reimplementing `XRL.Names`, and
`compile_scripting.py` building the C# against the game's own assemblies. Then I launched Qud and
found five defects in an hour, four of them in code I had written and argued for in detail.

None of the five was a correctness error in the sense any of those tools measure:

| what was wrong | what it actually was |
|---|---|
| The Pronoun Set row never appeared | `QudCustomizeCharacterModule.Init()` calls `PronounSet.Reinit()`, which re-reads `EnableSelection="false"` as the screen opens |
| The name-flavour re-roll ignored its option | `EmbarkInfo._modules` is not filled until character creation *ends*, so the re-roll consulted an empty list |
| Renaming in game ignored it too | `GiveProperName` passes the *object*, so `Generate` reads gender off it and an option is invisible |
| Four vibro weapons lost a rules description | two `<part Name="RulesDescription">` in one object; Qud merges them and the later `Text` wins |

Every one is a question about **when something happens** — when a list is populated, when a flag is
re-read, which object a call passes, what a loader does with a collision. The harness modelled how a
name *resolves*, which is a question about correctness, and it answered that question well. It could
not have answered any of these, because it does not model a lifecycle. Neither does a compiler.

> **A check proves the thing it models. Launch the game to find out what it does not.**

Two specifics worth keeping:

- **The game reports errors nothing here reads.** Qud writes `MODERROR` lines to
  `~/Library/Logs/Freehold Games/CavesOfQud/Player.log` on every launch. The four duplicate-part
  errors had been printed there since #390 and nobody had looked. `tools/check_build_log.py` already
  reads a *different* game-written file to prove the C# compiled — the same trick against `Player.log`
  is worth building, and #448 records the thought.
- **"It compiled and loaded" is not "it ran".** `check_build_log.py` reported that the game compiled
  all 51 files from source byte-identical to the tree and loaded the mod, on the same launch where
  the Pronoun Set row was silently missing. That verdict was true and said nothing about behaviour.

This is the same shape as *A gate is only evidence about the property it checks*, one level up: there
the question was which property a check inspects, here it is which *kind* of question a whole class
of tooling can be asked. Both end the same way — before trusting green, name the question it answers.

The practical rule: **anything that touches a screen, a lifecycle, or an event order gets a
`tools/sync_mod.py --dev` pass before it merges**, not after. Content and value changes can lean on
the checks; behaviour cannot.

## A gate is only evidence about the property it checks

Reformatting the XML in #78 produced output that `tools/validate_mod.py`,
`tools/check_vanilla_drift.py` **and** `npx prettier --check` all passed — while prettier had
reflowed the text inside `<helptext>` in `Options.xml`, inserting a newline mid-sentence into a
string Qud renders in its options menu.

None of those three gates was broken. None of them looks at whether text *content* survived, so all
three were honestly green and collectively meaningless for that question. Three passing checks felt
like three pieces of evidence and were zero.

It surfaced when I compared the **parsed element tree** of every file before and after — tags,
attributes, stripped text — which found 18 of 19 files identical and one not. That's exactly the
ratio that gets waved through on a 2,500-line diff.

This is the general form of two things recorded below in their specific cases: an orphaned
`Load="Merge"` applies nothing with no error, and a renamed vanilla blueprint breaks no save while
silently ceasing to merge. Stated generally:

> **Before trusting a green run, ask which property each check actually inspects.** A change that
> rewrites content wholesale needs a comparison of a *parsed* representation — the AST for Python,
> the element tree for XML — not a reading of the diff and not the checks that happen to exist.

The same trap catches *manual* verification, where there's no green run to be suspicious of. The
wiki here was disabled in #102 after confirming it had never been created — a true answer, correctly
obtained, to the wrong question. **"Never used" is evidence about the past, not about intent**, and
an unwanted feature and a not-yet-wanted one are identical from the API; I wanted the wiki, for
documenting the mod's mechanics, and it had to be turned back on (#106). Before acting on a check,
confirm it answers the question you're actually deciding — and where the real question is intent, no
command answers it. Ask.

It's also why `serializable-shape` and `subtype-tile` were written: each exists because nothing else
was looking at that property, and "nothing was looking" is not the same as "nothing is wrong".

## A guard that fires on a correct action teaches people to disable it

`no-commit-to-main` tests the branch you are standing on. At `pre-commit` that is exactly the right
question. `default_install_hook_types` also installs `pre-push`, and the hook set no `stages:`, so it
ran there too — where the same question is the wrong one. It refused
`git push origin refs/tags/v2.7.0` from `main`, which is precisely where a release tag belongs.

I got the tag up with `--no-verify`. That is the part worth recording: **the workaround for a guard
that is wrong once is the same keystroke as the workaround for a guard that is right**, and having
formed the reflex on a correct action I would reach for it again on a mistaken one.

A `pre-push` hook receives `<local ref> <local sha> <remote ref> <remote sha>` on stdin, so a correct
version could refuse only when a line's remote ref is `refs/heads/main` and ignore `refs/tags/`. I
did not write that, because the guard does not need to exist at that stage at all: the `main
protection` ruleset requires a pull request, forbids deletion and non-fast-forward, demands linear
history and passing checks, and lists **no bypass actors**. The server is the authority on pushes and
cannot be talked out of it.

> **Scope a hook to the stage where its question is the right question.** A check that is correct at
> one stage is not automatically harmless at another, and `stages:` is cheaper than teaching everyone
> a bypass.

One thing to know while checking the premise: **that ruleset does not appear under classic branch
protection.** `GET /repos/:owner/:repo/branches/main/protection` answers `404 Branch not protected`,
and I nearly wrote up "main is unprotected" as a finding on the strength of it. Rulesets live at
`GET /repos/:owner/:repo/rulesets`.

## A hook that was never installed protects nothing, and this one failed to install quietly

I committed straight to `main` in #119. The GitHub ruleset rejected the push so nothing was lost,
but `.pre-commit-config.yaml` carries a `no-commit-to-main` hook written for exactly that mistake,
and it never ran — because `pre-commit install` had never succeeded in that clone.

It hadn't succeeded because it can't, on my machine:

```
[ERROR] Cowardly refusing to install hooks with `core.hooksPath` set.
```

`core.hooksPath` points at a global hooks directory, and `pre-commit` won't write `.git/hooks/`
while it's set — reasonable in general, because git would normally ignore the file it just wrote.
My global hook *does* delegate to the per-repo one, so the arrangement works; `pre-commit` just
can't tell. Unset it for the length of the install and put it straight back:

```bash
saved=$(git config --global --get core.hooksPath)
git config --global --unset core.hooksPath
pre-commit install --install-hooks
git config --global core.hooksPath "$saved"
```

Two things make this worth writing down rather than filing under "install your tools":

- **The repository had no way to know.** A missing hook produces no output, no warning, and no
  difference in any check. It's the same shape as a missing `[PlayerMutator]` attribute — the
  feature simply doesn't happen. The only signal was the mistake it was meant to prevent.
- **`core.hooksPath` also silently disables per-repo hooks it has no delegator for.** Git consults
  *only* that directory, so a per-repo hook with no counterpart there is never read — and nothing
  says so.

  > **No longer true here, and worth recording as fixed rather than deleted** (#495). When this was
  > written my global directory held a single `pre-commit` file, so `.git/hooks/pre-push` was
  > unreachable and `default_install_hook_types: [pre-commit, pre-push]` was half inert. That
  > directory now holds a full delegator set whose helper documents its first step as running *"the
  > repository's own hook (`.git/hooks/<type>`)"*, so `pre-push` is reached. What remains is
  > harmless rather than inert: the config installs a `pre-push` hook that currently runs nothing,
  > because no hook in `.pre-commit-config.yaml` declares `stages: [pre-push]`.
  >
  > The mechanism is still real and still silent, which is why the entry stays. Only my machine
  > changed, and a contributor's `core.hooksPath` may well be the shape this describes.

> **After installing hooks, prove one fires.** Attempt the thing it forbids. `git commit` on `main`
> takes a second and is the only evidence that any of it is wired up.

## Searching for a keyword is not the same as reading the document

I described `docs/PERMISSION.md` as recording "permission to fork with a credit condition" that
"says nothing about copyright or licensing at all", and licensed this repository on that basis
(#101). I'd checked by grepping it for "licen" — zero hits — and read the section headings.

The body of §1 says:

> I've decided to make the mod open to the community to **update, fork, and generally do with as
> they please**, all I ask is that you **give credit where due, which includes Noble Lark for the
> subclass sprites**.

Which is, in plain language, an attribution grant — and it names Noble Lark's sprites *inside* the
grant, where I had written that they weren't covered at all. My search was for the wrong token: a
grant this broad simply doesn't need the word "licence" in it, and the absence of that word is what
I mistook for the absence of the thing.

This is *a gate is only evidence about the property it checks*, with me as the gate. `grep` answered
the question I asked — does this string appear — perfectly, and I treated that as settling a
question it could not reach. The same shape as disabling the wiki because it had never been created
(#106): a true answer, correctly obtained, to the wrong question.

> **Before summarising a document, read it.** A keyword search tells you a word is absent, which is
> almost never what you actually want to know. This is worth more care in short documents than long
> ones, because a short document has no excuse — `docs/PERMISSION.md` is under 100 lines and I had
> already opened it twice.

## `git checkout <file>` restores from the index, not from HEAD

While testing a new check in #80, `git checkout mod/Core/Subtypes.xml` — which I used to undo a
deliberately broken probe — also silently reverted the real fix in that file, because the fix had
never been staged. The validator caught it moments later, but the command itself gave no sign it had
discarded work.

Stage before using checkout to undo scratch edits in a file you're also legitimately changing, or
keep the probe in a different file entirely.

## Discovery attributes fail by doing nothing

`[PlayerMutator]` is the marker Qud scans for. A class implementing `IPlayerMutator` **without** it
compiles, ships, and is simply never called — no exception, no log line, just a feature that doesn't
happen. Measured: 11 of the installed mods implementing that interface carry the attribute.

This generalises to every attribute-driven extension point in the game, `[HasOptionFlagUpdate]` and
`[OptionFlagUpdate]` included. **The failure mode for a missing registration marker is silence**, so
check the marker against a working installed mod rather than assuming the interface is sufficient.

## A genotype `<stat>` merge carries three integers, and drops the description

`Load="Merge"` on a `<genotype>` does not merge a `<stat>` the way it merges everything around it.
`GenotypeEntry.MergeWith` finds the existing stat by name and hands it to `GenotypeStat.MergeWith`,
which is this in full:

```csharp
public void MergeWith(GenotypeStat newStat)
{
    if (newStat.Minimum != -999) { Minimum = newStat.Minimum; }
    if (newStat.Maximum != -999) { Maximum = newStat.Maximum; }
    if (newStat.Bonus   != -999) { Bonus   = newStat.Bonus;   }
}
```

Three integers. **`ChargenDescription` is never touched**, so a merge that sets one is a silent
no-op: well-formed XML, a clean diff, every gate green, and nothing different in game. The stat
descriptions a player reads while allocating points cannot be changed on a vanilla genotype by any
additive route.

Found while deciding #227, which wanted True Kin told that Ego drives the mental mutations chips
grant. It cannot be done that way. What *does* reach a vanilla genotype is **`<extrainfo>`**, which
`MergeWith` appends to with a duplicate check — the same list holding vanilla's *"Access to
cybernetics"* and *"May rebuke robots"*. That is the additive route into the chargen panel, and it
is what #227 used in the end.

> **A merge routine is not uniform across the elements it merges.** Before writing one, read the
> method for the specific element rather than the one above it — the failure here is silence, not an
> error, and the diff looks correct.

## A mutation's rank is capped by character level, and the game will show you the arithmetic

`BaseMutation.GetMutationCapForLevel(level)` is `level / 2 + 1`, and `CalcLevel` applies it to the
sum of every source — inherent rank, equipment, tonics, cooking, the lot. It is not something a mod
opts into.

So a chip granting rank 10 reads as **rank 1** on a level-1 character:

| Character level | 1 | 6 | 12 | 18+ |
|---|---|---|---|---|
| Rank cap | 1 | 4 | 7 | 10 |

I did not know this, and it cost more than knowing it would have. Testing #226 on a fresh character,
a `Tier="3"` chip and a `Tier="10"` chip both produced rank 1, and I read that as chip tier doing
nothing — filed an issue saying so, put a warning into `docs/FEATURES.md` calling 144 documented
levels aspirational, and rewrote a changelog entry that had been right. Before that I had gone the
other way, quoting the rank-10 figures as though every player saw them. Two opposite wrong claims,
each true for exactly one row of that table.

**The game was showing the answer the whole time.** `BaseMutation.GetLevelCalculations` builds a
plain-language breakdown per mutation and the character sheet displays it — *"rank is increased by 10
due to your equipped item"* beside *"rank is capped at 1 due to your level."* One screen, no
decompiling, and I read the assembly for an hour first.

> **When a number in game does not match the number in the data, look for what sits between them
> before concluding either is wrong.** A cap, a clamp or a scale is a likelier explanation than a
> broken mechanism, and Qud tends to expose its own arithmetic in the UI — check that before
> reasoning about the code, and certainly before filing.

## Being in step with a document is not the same as being right

The wiki is written from `docs/FEATURES.md`, so there are three ways a page goes wrong and only two
of them look like anything:

1. **A link rots.** GitHub derives an anchor from the heading text, so renaming a heading breaks
   every wiki link to it — and a bad fragment still returns HTTP 200, so neither repository reports
   it. Renaming one heading breaks five links. `tools/check_docs.py --wiki` catches this.
2. **The page goes stale.** The repository moved and the page did not. The scour slug landed while
   the ammunition page was being written, and a page pushed an hour earlier still said "arrows and
   shells". No check will catch this; the remedy is grepping the wiki when a change lands.
3. **The page faithfully repeats something false.** Nothing is stale, no anchor is broken, every
   figure matches its source — and the source is wrong.

The third is the dangerous one, because it is invisible from both sides. **This fork's documents were
about 5% verified when that was measured** — 74 checked claims against roughly 713 data rows and 583
numbers in `docs/FEATURES.md` — and a single session turned up nine claims that did not match the mod
or the game, three of them introduced while fixing the other six.

> **Do not treat a repository document as a source of truth for a figure you are about to publish.**
> Recompute it, or check it against the game. Where a table is data rather than prose, make something
> recompute it — `check_docs.py` does that for the 144 rows of Appendix B, and found three wrong ones
> on its first run that two careful reads that same day had missed.

## A public field is not a supported setter if something caches what it derives

`PowerEntry.Attribute` and `.Minimum` are public and writable, so I assumed retuning a skill
requirement at runtime would be trivial. It isn't. `MeetsAttributeMinimum` gates on a **cached**
`_requirements` list, `InitRequirements()` returns early when that cache already exists, and the
cache is private — reaching it would need reflection, which charter rule 5 rules out. Once anything
has rendered or checked that power, writing the field is **inert, with no error**.

What saved the feature is that `HandleXMLNode` never primes the cache. It's null after load, so the
value written at boot is the one the cache is eventually built from. That makes the `Restart="true"`
option in #91 correct and honest. It wouldn't have supported a live one, and shipping it as live
would have produced an option that silently did nothing for anyone who happened to open the skills
screen first.

> **Before designing an option around writing a public field, find who *reads* it.** If a cache sits
> between the field and the behaviour, the option's scope is set by the cache's lifetime, not by how
> live the field looks.

This is why #91 became two options rather than one. `Cost` is a plain int that `Render` and purchase
read directly, so costs are genuinely live; requirements are not, and one toggle covering both would
have had to describe itself dishonestly. **The scopes are a property of the game, not a design
choice** — `docs/FEATURES.md` §13.2 tabulates all three (live / restart / new character).

Same silent-failure family as an orphaned `Load="Merge"` and a missing `[PlayerMutator]`.

## Read the IL when the metadata and the XML docs run out

The two lessons above say to check `Assembly-CSharp.xml` for documentation and a metadata reader for
structure. Neither can answer *"does this method rebuild, append, or return early"* — and that
question decided the design above. Method bodies can answer it, and reading them needs **no
decompiler**, because the metadata reader already yields each method's RVA.

- Header: `b & 3 == 2` means tiny format, one byte, code length `b >> 2`. Otherwise fat — 12-byte
  header with the code size at offset 4.
- Then scan opcodes. Token-bearing ones (`ldfld` `0x7b`, `stfld` `0x7d`, `call` `0x28`,
  `newobj` `0x73`) carry a 4-byte metadata token whose high byte is the table and low three the RID,
  so a field or method name can be resolved straight out of the tables.

**Do not scan for tokens alone.** A token-only pass over `InitRequirements` showed `ldfld` → `newobj`
→ `stfld` and read as a clean rebuild — exactly backwards, because it had dropped the branch between
them. The opening bytes settled it: `02 7b … 3a d4 00 00 00` is `ldarg.0; ldfld _requirements;
brtrue → ret`, a guard rather than a rebuild.

Worth the twenty minutes, because the wrong answer ships a silently inert option and the alternative
was another round trip through the game.

## GitHub does not re-run pull request checks on a retitle

`on: pull_request` with no `types:` means `opened`, `synchronize`, `reopened`. A job reading
`github.event.pull_request.title` therefore **cannot be satisfied by retitling**: the edit doesn't
re-trigger it, and a manual re-run replays the *original* event payload, so it still sees the old
title. The check stays red until an unrelated commit is pushed.

`.github/workflows/ci.yml` now lists `edited` explicitly. The general form: **a check that reads the
event payload must listen for the event that changes that payload**, or it's unfixable by the very
action it demands — which teaches contributors that a red check can be ignored.

## Stale prose rots silently, and the emphatic passages rot worst

Every gate here inspects a *machine-readable* property. `validate_mod.py` checks XML and C#
structure, prettier checks formatting, `typos` checks spelling, CodeQL checks the Python. **Not one
of them reads a sentence and asks whether it's still true.** So documentation decays with no signal
at all — the same silent-failure shape as an orphaned `Load="Merge"`, but across every file a
contributor reads *first*.

Measured at the point the option toggles landed (#93): **all five** items in the *Release blockers*
list were closed while that section was still titled "Immediate priorities" and written as a queue,
`docs/FEATURES.md` §7.3 still called a defect fixed months earlier in #34 the "🔴 Biggest
compatibility hazard in the mod", and §3.4's drop-rate arithmetic still read `10 / 100`, which was
only correct under the table *replacement* that #34 had removed. That last one is a wrong number
anyone trusting the doc would have repeated as fact.

**The worst case is not a stale figure but a stale permission.** `docs/STYLEGUIDE.md` §1.1b spent a
day telling contributors that CoQE-original blueprint names were *"verified free"* to rename,
because it was written before `v2.3.0` and still opened with *"this fork has no saves yet"*. That
sentence stopped being true on 2026-08-17 and nothing anywhere noticed. #201 needed to replace a
shipped arrow, read §1.1b, and got the wrong answer from the one document whose job it is to give
the right one — the correct answer came from `git tag`.

A wrong number gets repeated. A wrong *permission* gets acted on, and this one authorises the
silent-failure class the same section exists to prevent: rename a shipped blueprint and
`GameObject.GetBlueprint` logs through `MetricsManager` and falls back to the generic `Object`, so
every player's copy degrades without crashing and without telling anyone. When a document grants
leave to do something dangerous **on the basis of a state of the world**, the grant needs the state
written next to it — a date, a version, a tag — so the reader can check the premise rather than
trusting the conclusion.

**The emphasis is the tell.** A 🔴 callout, a "highest-value fix in the codebase", a numbered
priority list — I write those when a defect is freshest and most irritating, and that same emphasis
is what stops me revisiting them. They read as settled background rather than as claims under
review, so the strongest statements here become the least trustworthy. Two harms, both
charter-relevant: they point the next contributor at work already done, and they advertise a
resolved hazard in the one dimension charter rule 1 makes this fork's headline claim.

Stale **cross-references** are the same class. The charter's own commit-message example read
`closes #4` for work that actually closed #3, and nothing checks issue numbers in prose either.

> **When a PR closes a defect, grep the docs for it in the same PR.** `rg -i 'artifact 3|removetable'`
> costs seconds. The fix and the prose describing the defect are one change, not two — and the
> second half is the one no gate will ever remind me about.

## "Could not determine" is not a pass

Both C# checks (#135, #136) can be unable to answer: no game installed, no .NET SDK, no build log, or
a mod the game skipped because it was disabled. Every one of those has to be loud, and a skip must
never print next to the word OK. `tools/compile_scripting.py` prints `SKIPPED` on its own line and has
a `--require` flag that turns a skip into a failure; `tools/check_build_log.py` treats a missing or
disabled entry as a failure outright, because it is only ever run deliberately.

The sharper form of the trap is that a **negative result can be ambiguous**. `find_compiler()` walks
up from `csc.dll` to the dotnet root, and the first version went up three directories instead of four.
That does not raise — it lands on a directory with no `dotnet` beside it, and reports *"no SDK
found"*, which is exactly what a machine with no SDK reports. On a laptop where `dotnet` is keg-only
and genuinely not on `PATH`, that read as correct behaviour. It survived to the first real run.

What caught it was a test with an **independent oracle**: glob the known install locations directly,
and if a `csc.dll` exists there, `find_compiler()` must not return `None`. A test that merely called
the function and checked for `None` would have shared its mental model and agreed with it.

> **When a check reports absence, ask whether it can tell "not there" from "I looked in the wrong
> place".** If it cannot, the reassuring answer and the broken one are the same string. Verify against
> a source derived differently from the code under test.

This is a specific case of *A gate is only evidence about the property it checks*, above — the check
was honestly green about a question it was not actually asking.

## A suite of failure cases needs a positive control

`tools/test_check_build_log.py` is fifteen cases and fourteen of them assert that something broken is
reported as broken. A script that failed unconditionally would satisfy all fourteen. The fifteenth,
`test_a_good_log_passes`, is the only one that can tell a working check from a broken one, and it is
worth writing even when it looks tautological.

It paid for itself on its first CI run, by failing — see the next lesson for what it found.

> **Any suite whose cases all assert failure is satisfied by a permanently broken subject.** Add the
> case that must pass, and treat it as the load-bearing one.

## A fixture that describes files must take its clock from those files

The build-log fixtures stamped every synthetic log `2026-08-16T18:11:02`, a real timestamp copied from
a real log. It passed locally and failed in CI, and the check was right both times: my working tree's
`.cs` files were older than that stamp, but a **fresh checkout writes every mtime at clone time**, so
on the runner the source was newer than the log that claimed to describe it. The staleness guard did
precisely its job and rejected the fixture.

Timestamps now derive from the files the fixture deploys, computed *before* the per-case mutations so
that a case which deliberately post-dates a file still post-dates the log.

> **Never bake a timestamp into a fixture that makes claims about files.** Nothing about mtimes is
> stable across machines or clones; derive the clock from the same files the assertion is about.

## zsh does not word-split an unquoted variable, so a scenario loop can test nothing

Checking that the compile gate degraded correctly on a machine with neither the game nor an SDK, I
looped over environment combinations:

```bash
for sim in "QUD_MANAGED_DIR=/nonexistent QUD_CSC=/nonexistent"; do env $sim python3 -m unittest ...; done
```

In bash that splits into two assignments. **zsh does not word-split unquoted parameter expansions**,
so `env` received one argument, `QUD_MANAGED_DIR` was set to the literal string
`/nonexistent QUD_CSC=/nonexistent`, and `QUD_CSC` was never set at all. The run reported OK. The
scenario I believed I had verified had not executed.

It surfaced only because the skip *count* was identical to the previous scenario, which it could not
have been if the second variable had taken effect. Put assignments directly on the command
(`A=1 B=2 cmd`), or use an array, which zsh does split.

> **After running a scenario, confirm it actually took effect** — assert on something that must differ
> between cases, such as a count, an exit code or a reason string. A green result from a check that
> never ran is worse than a red one, because it is filed as evidence.

## A placeholder is a value, and something will look it up

`mod/workshop.json` carried `"WorkshopId": 0` for months, meaning "no item yet, create one". Four
documents said so. Qud's uploader disagreed: it read the zero as an item id, looked up item zero,
and reported *Item not found* with every field blank and no offer to create anything. The first
upload of this fork failed on it (#163).

The correct state was not a different value but **no key at all**. The uploader writes
`workshop.json` itself — "Create Workshop Id for Mod…" creates the Steam item and writes a file
containing nothing but the new id — so a hand-authored file with a placeholder pre-empts the one
step that would have worked.

The evidence was sitting on disk the whole time. Of the 72 installed mods that ship a
`workshop.json`, two have no `WorkshopId` key and **none** has a zero. That is the same check
`docs/LESSONS.md` already recommends for Qud's behaviour generally, applied one file over.

**Before inventing a sentinel, find out whether the consumer distinguishes absent from empty.**
Zero, `""` and `null` are all real values to whatever parses them, and a field that means "none"
is only safe if something documents it as meaning that. `workshop-target` in
`tools/validate_mod.py` now rejects a non-positive id, so this particular placeholder cannot come
back.

## A search that finds nothing has two explanations, and one of them is the search

Three times now a check has reported nothing and I have read it as an answer. Twice in one day,
and once again much later — and the late one is the one that should worry me, because by then the
trap was already written down in this repository.

**`strings` on a .NET assembly.** Deciding whether `Builder` was dead data in vanilla, I searched
`Assembly-CSharp.dll` for the literal and got zero hits — for `Builder`, and for every other name I
tried, including ones that certainly exist. That last part was the tell and I nearly missed it.
macOS `strings` reads ASCII runs; .NET keeps user strings in the `#US` heap as **UTF-16**, so the
search could not have found anything. Had I trusted it, `Builder` would have gone into the
documents as a defect in Freehold's own data. It is a real mechanism: every value resolves to a
type in `XRL.World.PartBuilders`.

**A test edit that never applied.** Verifying that `snapshot_qud_api.py` refuses to write when a
cited figure cannot be found, I patched a line of `CITED_FIGURES` in a temporary copy, ran the
tool, and got exit 0. The conclusion — that the gate does not work — was wrong twice over: `ruff
format` had already split those tuples across several lines, so the single-line replacement target
matched nothing, the file was never modified, and the run I read was an ordinary clean one. The
gate works. The test did not run.

**`command -v` on an installed tool.** Investigating #226 I wanted to decompile
`Assembly-CSharp.dll`, ran `command -v ilspycmd`, got nothing, and filed the issue saying the tool
was not installed and the question therefore needed a play session. It was installed — version
11.0.0.9375, sitting in `~/.dotnet/tools`. The .NET installer writes the **literal** string
`~/.dotnet/tools` into `/etc/paths.d/dotnet-cli-tools`, and `path_helper` copies entries verbatim
without expanding `~`, so the entry resolves to a directory named `~` and matches nothing. The path
is visible in `$PATH` and every binary under it is unreachable. One `export
PATH="$HOME/.dotnet/tools:$PATH"` and the whole of #226 fell out statically, including the duration
formula that turned out to be the actual defect. `CONTRIBUTING.md` had explained this in full since
#252; I had not read it, because I was not working on the snapshot check it is filed under.

All three had the same shape. A check that reports **zero of something** is indistinguishable from a
check that did not execute, and the second is far more common than it feels. A check that reports
a *problem* at least proves it ran.

> **Before believing an empty result, prove the search can find anything at all.** Probe for
> something you know is present, or assert the edit landed before running the thing that reads it —
> `assert old in text` costs one line and converts a silent no-op into a loud failure.

This is the same principle as the positive control two lessons up, one level out: there it is a
test suite that needs a case which must pass, here it is any search, grep or patch whose silence
you are about to treat as evidence.

## I built the reference, then did not read it

`docs/WIKI.md` exists because I asked for it: an index of Freehold's fifty-three modding pages so
that the next question about engine behaviour would be answered from their documentation instead of
from my guess. I wrote it in #509.

`<mixin>` is a second inheritance mechanism. A blueprint can pull tags, parts and stats from another
blueprint without inheriting from it, and 143 vanilla blueprints are kept out of every dynamic pool
by an `ExcludeFromDynamicEncounters` that arrives that way. `BlueprintIndex.chain()` followed
`Inherits=` and nothing else, so every one of those looked like a live pool member, and this fork's
share of forty-three slices was understated - `BaseAnimal:Tier1` by thirteen points.

The wiki documents `<mixin>` **nine times on `Modding:Objects`**, with `Include`, `Exclude`,
`Priority` and the `Load="Fill"` before-or-after rule stated plainly. `Modding:Objects` is in my
index. My one-line summary of it said *"blueprint definitions, the component system, the supported
tag list, and the part catalogue by category"* and did not mention the mechanism.

Three chances, and I took none of them:

1. **The reference named the page.** I did not open it while building the index that models
   inheritance.
2. **My own probe printed the word.** Checking something else this session, I listed the element
   kinds the index does not handle and `mixin` was in the output. I read past it.
3. **I re-derived it from the decompiled loader instead** - the mixin ordering, `Include`/`Exclude`,
   `Load="Fill"` - twenty minutes of reading IL to recover what one wiki page states in five lines.

A playtest found it. Not a check, not a review, not the reference.

> **When modelling engine behaviour, read Freehold's page on it before reading the assembly.** The
> decompiler answers *what this build does*; the wiki answers *what the mechanism is*, including
> the parts of it nothing in the data happens to exercise. `Priority` is real, documented, and used
> by no vanilla blueprint - I would never have found it in the data.

The narrower trap, worth keeping separately: **a search for `mixin` in the wiki's own search index
returns nothing.** `insource:/mixin/` across all namespaces reports zero pages, while fetching
`Modding:Objects` directly and grepping finds nine. Another empty result that was not an answer -
see *A search that finds nothing has two explanations* above.

## Inheriting a blueprint inherits its Role, and Role is a x4 lever

Thirty-two creature variants, each three lines over a vanilla parent - a name, a colour, a marker
tag. Every one is distributed by an explicit entry I placed in the biome it belongs to. And every one
also joins `DynamicInheritsTable:BaseAnimal` or `:BaseReptile`, because `Inherits="Dog"` is
membership and nothing else is required.

That much I knew. What I had not looked at was where the *weight* went. `BaseAnimal:Tier1` totals
5.67 billion, and **seven of my blueprints hold 49.4% of it while the other eleven hold 2.9%**.

`Dog` and `Bat` carry `<tag Name="Role" Value="Minion" />`, and `Minion` is a **x4.0** multiplier -
the largest in `InitWeights`, tied with `Common`. `Goat` and `Boar` carry `Brute`, which is **x0.25**.
So `Vixy_MarshDog` weighs 400,000,000 and is 7.06% of the pool on its own, while `Vixy_DunGoat`
weighs 25,000,000 and is sixteen times lighter. I did not choose either number. I chose a parent.

The lesson is not "check the Role tag" - it is that **a one-line `Inherits=` carries a distribution
profile with it**, and the profile is built from values that live on the parent and are multiplied by
values that live in the engine. A cosmetic re-skin is cosmetic in the blueprint and not at all
cosmetic in the population tables.

> **When a new blueprint inherits from a vanilla one, ask what the parent is a member of and what
> multipliers it carries, before asking what the new one looks like.** `Role`, `Tier`, `Level` and
> every `DynamicObjectsTable:` tag come along, and none of them appear in the diff.

The fix is `:Weight`, which is worth knowing exists: `<tag Name="<resolved table name>:Weight">` is a
multiplier applied inside one pool after the tier delta and Role. **Vanilla ships 81 of them across
28 pools** at 0.05-0.3 - `Holographic Banana Tree` is 0.2 of `DynamicObjectsTable:BananaGrove_Plants`.
The key is the table name *as requested*, and `TryResolvePopulation` substitutes `{zonetier}` before
`RequireTable` sees it, so a tiered slice carries its tier in the key and each slice needs its own
tag. A value of zero is not a small weight but an exclusion - `if (value == 0) continue`.

## A change to a dynamic pool has one witness, and you have to go and find him

A `DynamicObjectsTable:X` change is observable only through whatever consumes that pool, and the
list is shorter than it looks. `DynamicObjectsTable:Guns` has **exactly one** consumer,
`GunsmithInventory_Legendary`. `DynamicObjectsTable:Ammo` has that and `RandomItem` at weight 5.

`Gunsmith` carries the legendary table as `HeroTable`, and `GenericInventoryRestocker` reaches for
it only when `ParentObject.GetIntProperty("Hero") > 0`. **An ordinary gunsmith never touches it**,
so wishing one and reading his stock tests nothing at all — which is the shape of mistake worth
avoiding here, because it looks exactly like a test that passed.

There is no shortcut to a hero. `HeroMaker.MakeHero` is a method with no wish exposing it, and no
wish rolls a population table. Both read out of the assembly rather than assumed, after looking for
one.

**And one sighting is not a test, because these changes are removals.** Verifying a removal means
confirming an absence, and a pool you took six arrows out of looks identical to one you did not in
any sample where the roll would not have picked them anyway. It takes several legendary gunsmiths
before an absence means anything, and they are not common.

So the honest cost of play-testing a pool change is: find a legendary merchant of the right kind,
repeatedly, and then reason carefully about what you did not see. That is why #303 exists — the
membership belongs in a snapshot that fails loudly, not in a habit of looking. #261 and #262 were
both verified from `tools/report_dynamic_tables.py` for this reason, and moved to Staging on it.

Worth pairing with *A search that finds nothing has two explanations* above: an empty merchant stock
and an empty search result fail the same way, by looking like an answer.

## A property the game *derives* is not the tag you can grep for

`tools/report_dynamic_tables.py` reads a blueprint's Tier and Role in order to weight it the way the
population code does. Both reads were wrong, in the same way, and neither had a symptom: the report
kept printing a plausible number.

**Tier is a fallback chain, not a tag.** `GameObjectBlueprint.Tier` returns the `Tier` tag when there
is one, and otherwise `GetStat("Level").BaseValue / 5 + 1` clamped to 1–8. **Vanilla creatures carry
`Level` and no `Tier` tag at all** — `Goat` is `<stat Name="Level" Value="1" />` and nothing else — so
a report keyed on the tag dropped 593 eligible blueprints, 46 of them this fork's own creature
variants. `BaseAnimal`, `BaseReptile` and `Humanoid` were reported as pools that did not exist, while
I held 52%, 57% and 5 members of them. And `_Tier`'s `-999` sentinel, for a blueprint with neither,
does not mean *excluded*: the delta simply misses `TierDeltaWeights` and it joins at weight 1.

**Role lives in two stores.** The weighting asks
`Tags.TryGetValue("Role", …) || Props.TryGetValue("Role", …)`, and `<property Name="Role">` lands in
`Props` while `<tag Name="Role">` lands in `Tags`. Vanilla declares it as a tag 349 times and as a
property never. This fork does the exact opposite, thirteen times, on the Zetachrome items — so
reading only tags weighted them ×100 too heavily and put `BaseShield` Tier8 at 97% when it is 69%.

Both are the *silent zero* two lessons up, one level in: not a search that could not match, but a
**read of the wrong field on a match that did happen**. The tag was really absent. The conclusion
drawn from its absence was not.

> **Before reading a blueprint field, find the property on `GameObjectBlueprint` that the consumer
> actually calls, and follow it to the end.** If it has a fallback, an alternative store, or a
> sentinel, the XML you can grep for is one branch of three.

The cost was not the wrong number so much as what rested on it. #481 is a design decision about pool
dominance, and it was being weighed against these figures — including three pools the report said
were empty. I found this only because #502 sent me back into `PopulationManager` for something else.

## Rescaling a per-action budget to per-hit has to clear whatever decays per turn

The cryo arrow puts −50 on a target per action. A shell spends one piece of ammunition per action
too, and fires eight pellets, so eight pellets at −6 looked like the same budget. It shipped, and
eight shells into a 500 HP target left it never getting cold.

The mechanism was fine — a probe build renamed the shell's projectile and confirmed the game was
firing *ours*, and that `TemperatureOnHit` applied from it. The number was the defect, and the
reason was quoted in my own design comment three paragraphs above the number:

> temperature returns to ambient by `Math.Max(5, |diff| * 0.02)` every turn — a flat 5 a turn at
> these magnitudes

**That is a floor, not a curve.** Divide a payload far enough and it lands under the rate at which
the game undoes it. At −6 a pellet with three of eight connecting, a turn spent moving hands back
+5 of the −18 just delivered; with one connecting, the net is −1 and the effect cannot accumulate
at all. The arrow never had the problem because −50 against −5 is decisive on any single hit.

> Before dividing an effect across hits, find what the game restores per turn and check the result
> against it. Below that line the part fires, the event reaches the target, and nothing observable
> happens — which is indistinguishable from being broken, and costs an evening to tell apart.

#146 will meet this directly: a chaingun divides by six.

## The divisor is the projectiles that land, not the projectiles fired

The same tuning pass got the divisor wrong twice. Eight pellets leave a Pump Shotgun, so ÷8 looks
right — but `MissileWeapon.Fire` rolls `Stat.Random(-WeaponAccuracy, WeaponAccuracy)` **per
projectile**, and at `WeaponAccuracy="45"` that scatters most of them whatever the range.

Measured across three play-tests, by working backwards from how many shots a freeze took and how
far past the brittle line it landed:

| Run | pellets that connected, of 8 |
|---|---|
| −12 a pellet, five shots to freeze | ~2.5 |
| −20 a pellet, four shots | ~1.8 |
| −25 a pellet, two shots at true point blank | ~4.4 |

So the real divisor is about **2**, with a spread of roughly 2 to 4. Accuracy varies the rate as
well as range does — the Pump Shotgun at 45 is the worst of the four shell weapons, the modified
handcannon at 30 the best — so tune against the loosest gun and the rest over-deliver slightly.

> A multi-projectile weapon delivers a *fraction* of its payload, and the fraction is both small
> and variable. Derive it from a measurement, not from the shot count in the blueprint.

**It applies to probabilities as much as magnitudes**, which I did not generalise the first time.
The takedown shell's `Chance="40"` per pellet started life as `12` — sized against eight pellets,
so a shell had a 22% chance of doing anything at all, and play-testing saw nothing fire. Same
arithmetic, third occurrence in one feature.

## A magnitude cap must sit past the threshold it is bounding

Duration and intensity are the same number for temperature: how far past the line you land, at 5 a
turn back. Two point-blank shells put a target near −185 and held it frozen about seventeen turns,
where the arrow sits at −115 for three. No `Amount` fixes that, because the overshoot scales with
however many pellets happen to connect — shaving it only moves which end of the variance is wrong.

`TemperatureOnHit` already has the tool. With `Max="true"` it applies only while the target is
short of `MaxTemp`, on whichever side `Amount` points:

```csharp
(Amount.RollMaxCached() >= 0) ? (Temperature < MaxTemp) : (Temperature > MaxTemp)
```

The trap is the value. `MaxTemp="-90"` reads like a reasonable cap and would stop the cold applying
around −95 — *above* the −100 brittle line — so the target would never freeze at all. The cap would
silently defeat the payload it exists to limit. At −110 the last applicable pellet lands between
−110 and −135: the freeze is guaranteed and the overshoot is bounded.

> A cap on an effect that crosses a threshold has to sit on the far side of that threshold, with
> room for one more application. Put it on the near side and you have not limited the effect, you
> have removed it.

Vanilla writes `Max="true" MaxTemp="400"` on four objects, all heat. The cold side has no
precedent, which is exactly why the value needed working out rather than copying.

## An effect that reports nothing is not an effect that did nothing

Three consecutive play-tests of the takedown shell's `GroundOnHit` read as total failures: no
message, no visible change, targets flying away unbothered. The part was working the entire time.

`Grounded.Apply` prints nothing itself. The *"falls to the ground"* line a player expects comes from
`Flight.Fall`, and that only fires when the target has a live `Flying` effect at the moment of
impact:

```csharp
foreach (Flying item in Object.YieldEffects<Flying>())
    if ((item as Flying)?.Source != null) FailFlying(flying.Source, Object);
```

A target that happened to be walking gets grounded — genuinely unable to fly for 20–30 turns — in
complete silence. It took *examining* a creature and finding the `Grounded` status sitting in its
effect list to establish that anything had happened at all.

> When an effect appears not to fire, check the target's state before concluding anything about the
> mechanism. A status list is evidence; an empty message log is not.

The cause turned out to be sharper still, and it is a trap for anyone testing a flight-related
effect: **a creature you wish into existence is not flying.** `Flight.StartFlying` is reached only
from the `Wings` mutation's `CommandEvent` handler — flight is an *activated ability*, not a state
things spawn in — so a freshly wished gamma moth stands on the ground until its AI decides to take
off. Ground it in that window and `Flight.Fall` has no live `Flying` effect to fail, so it applies
in silence.

Wait for it to fly and shoot it again and the message appears exactly as documented. The same test
also measured `Grounded`'s duration for free: the moth spent ~20 turns unable to take off, because
`Grounded` refuses `CanChangeMovementModeEvent` for `"Flying"` the whole time, against a configured
`Duration="20-30"`.

Two chased bugs came out of this session's testing that were never bugs — this one, and a wish
returning a `Raven_Cryo Arrow` because the shell it asked for was not loaded. Both looked exactly
like broken code and both were the observation being wrong. The cost of the wrong diagnosis is
worse than the cost of checking: the first thing I did on this one was start reading `IsReady` for
a fault that did not exist.

## Containment is not dispatch — check the cascade level before assuming a part is reached

`MissilePerformance` is a real vanilla part with exactly the dials an effect round wants —
`PenetrationModifier`, `DamageDieModifier`, `DamageModifier`, `AddAttributes` — and vanilla puts it on
the Turbow. Putting it on a *round* looked like a free way to let ammunition modify a shot without
touching a single vanilla weapon. It would have loaded, fired, and done nothing.

`GetMissileWeaponPerformanceEvent.GetFor` dispatches to three objects, and the round is not one:

```csharp
Launcher.HandleEvent(e)     // Subject = Launcher
Projectile.HandleEvent(e)   // Subject = Projectile
Actor.HandleEvent(e)        // Subject = Actor
```

The one plausible back door is `MagazineAmmoLoader` forwarding to what it is holding, and it is gated:

```csharp
private bool AmmoWantsEvent(int ID, int cascade) {
    …
    if (!MinEvent.CascadeTo(cascade, 4)) return false;
```
```csharp
if (E.CascadeTo(4) && GameObject.Validate(ref Ammo) && !E.Dispatch(Ammo))
```

`CascadeTo(Cascade, Level)` is `(Cascade & Level) != 0`, and this event declares `CascadeLevel = 1`.
`1 & 4 == 0`, so the loaded round never sees it. The chambered round is *inside* the weapon and is
still not part of the weapon's event surface.

> **Before putting a part on a contained object, find the event's `CascadeLevel` and the container's
> forwarding gate, and AND them together.** Being held by something is not the same as being
> dispatched to.

Same silent-failure family as `TurretStockWeight="0"` and the melee-only `BleedingOnHit`: nothing
errors, nothing logs, the item simply does less than it says.

## `Priority` can only move a part earlier, so design for the order you get

The obvious way to let ammunition carry a payload is a part on the weapon that reads `E.Projectile`
after `MagazineAmmoLoader` has set it during `LoadAmmoEvent`. That ordering is not available, and no
attribute buys it.

Part order *is* dispatch order — `GameObject.HandleEventInner` walks `PartsList.GetArray()` in index
order — and the list is built by `AddPartInternals`:

```csharp
int priority = P.Priority;                    // IPart.Priority => 45000 by default
if (priority == int.MinValue) PartsList.Add(P);
else {
    int num = PartsList.Count;
    while (num > 0 && PartsList[num - 1].Priority < priority) num--;
    PartsList.Insert(num, P);
}
```

Equal priorities append, so blueprint order survives — and a *higher* priority only walks the part
**backwards**, toward the front. Nothing can push a part later than what is already in the list.
Meanwhile `ObjectBlueprintLoader.Bake` calls `Inherit(obj.Inherits, …)` before overlaying the object's
own children, so parts declared on an abstract base are always added first. `MagazineAmmoLoader` is
declared on the concrete weapons, never on `BaseFirearm`, so a part merged onto the base runs *before*
the loader, permanently.

The fix is not a knob, it is a different shape: read what you need while you are early — the loader's
`Ammo` field still holds the round it is about to chamber, before `RemoveOne()` — and do the work at a
later event. `MissileWeapon.SetupProjectile` fires `ProjectileSetup` on the launcher once per
projectile, after the projectile exists, which is order-independent because it is a separate dispatch.

> **When a part must run "after" another, stop looking for a priority and find a second event.**
> Ordering within one dispatch is fixed by blueprint inheritance; ordering *between* dispatches is free.

## Search where the effect is applied, not where the part is used

I told the maintainer of this repo — myself — that bleeding is melee-only in Qud by design, and put it
in #210 as a charter rule 2 argument against ever projecting it. The evidence was that `BleedingOnHit`
appears on exactly two vanilla objects, both melee.

That is a fact about one part. The question was about a mechanic. Grepping every `new Bleeding(` call
site in the decompiled assembly takes one command and returns about twenty, including two that
demolish the claim:

- `XRL.World.Parts.Skill.ShortBlades.WeaponMadeCriticalHit` — the tree's **root** class, so every
  critical hit with any short blade bleeds, with no power purchased and, via
  `Skills.GetGenericSkill(Skill, Attacker)`'s reflection fallback, no requirement that the attacker
  have the skill at all.
- `MissileWeapon.cs:1862` — the Bow and Rifle tree's **Wounding Fire**, which is bleeding at range and
  has been all along.

Both were reachable from the start. Neither was reachable from the part.

> **For "does vanilla do X", search for the thing X *is* — the effect class, the constructor, the
> applied state — not the one part you happen to have found doing it.** A part census answers "how is
> this part used", which is a different and much narrower question than it looks.

The cost here was not a bug, it was a design argument built on a false premise and written into an
issue, where it sat looking authoritative until someone questioned it.

**It happened again, on the chip budget, in the opposite direction.** Costing the psionic chips
(#338) I checked whether Mura's stated reason for the 3/6/10 physical ladder was true — that mental
mutations keep scaling with Ego from a chip and physical ones do not — by grepping each of the 36
mutation *classes* for `Stat("Ego")`. Seven matched, so I reported the rationale as holding for 7 of
23, called the split broken in both directions, and shipped that into `docs/DESIGN_balance.md`, the
changelog and two issue comments before catching it.

The scaling is not in the classes. It is one line in a shared base:

```csharp
// BaseMutation.CalcLevel
Statistic value = ParentObject.Statistics[mutationEntry?.GetStat()];
num += value.Modifier;
```

and `GetStat()` falls through to the *category*, declared once in `Mutations.xml` as
`<category Name="Mental" … Stat="Ego">`. All 23 mental mutations scale; the seven that named Ego
themselves were doing something else with it. The rationale was correct, and the ladders turn out to
be calibrated to meet exactly at Ego 24.

Same shape as the bleeding case and the same fix — but note what made it *harder* to catch. The
bleeding grep returned too few results and the claim was that the mechanic did not exist. Here the
grep returned seven results, which looked like a finding rather than like a miss. **A partial match
is more dangerous than no match**, because it furnishes a number, and a number reads as evidence that
the search worked. When a categorical claim comes back "true for some", ask where the property is
declared before believing the split is real.

## A boolean's name is not its semantics, and neither is a skill's

`Bleeding.Stack` reads as "this bleed stacks". It means the opposite:

```csharp
if (Stack) {
    foreach (Effect effect in Object.Effects)
        if (effect is Bleeding bleeding && bleeding.GetType() == GetType() && bleeding.Stack) {
            // raise SaveTarget / Damage to the better of the two, clear Bandaged
            return false;              // …and add no new effect
        }
}
// otherwise: add an independent effect
```

`Stack = true` **merges** into an existing bleed. `Stack = false` piles a separate one on. And
`BleedingOnHit.Stack` is a bare `public bool Stack;` — default **false** — while both vanilla users
write `Stack="true"` explicitly. So an inherited XML payload that omits the attribute quietly gets the
compounding version, which on a six-round burst is six independent effects rather than one.

The same trap runs through the skill data, where one power carries three different names: the tree is
`Name="Bow and Rifle"` with `Class="Rifles"`, its entry is **Draw a Bead**, and the activated ability
it grants is displayed as **Mark Target** (`AddMyActivatedAbility("Mark Target", "CommandMarkTarget", …)`).
Prose that quotes any one of those and expects a reader to find it in the game is a coin flip.

> **Read the field, do not read the field name** — and when documenting a vanilla mechanic, write down
> which of its names the player actually sees.

## The issue gets checked against the game; the prose written afterwards does not

Two claims in the ammunition work turned out to be wrong, and both survived review and shipped.

**"Bleeding is melee-only in Qud by design."** Written into #210 as a charter rule 2 argument, and
from there into `docs/FEATURES.md`, an `Ammo.xml` comment and a released changelog entry. It came
from noting that `BleedingOnHit` sits on exactly two vanilla objects, both melee. Grepping every
`new Bleeding(` call site instead — one command — returns about twenty, including the Short Blades
critical-hit bleed on the tree's *root* class and `Rifle_WoundingFire`, which is bleeding at range and
always was. Corrected in #219.

**The effect shells costing `003`.** Decided while implementing #145, on the reasoning that two scrap
metal and one pure alloy "sits between vanilla's two anchors, a grenade mk I at two bits for one and
plain shot at one bit for five". Both anchors are real; neither is the right comparison. Vanilla
charges `001` for every gas, flashbang, thermal, freeze and high explosive grenade mk III — the exact
payloads those shells carry, dialled down — and reserves pure alloy for plasma, gravity and time
dilation. Corrected in #146.

The thing worth noticing is where they came from. **Neither was in the issue.** I re-read #145 end to
end afterwards and checked every claim in it: the weapon list, all ten shell configurations, the gas
densities, the stasis inconsistency, all twelve weapon stats, the resonance damage figures — including
the non-obvious one, that vanilla's mk I sets `Level="2"` so `2d10+4` really is its non-structural
damage — and the takedown shell's anatomy and save mechanics. Every one held.

What was wrong got written *later*, in the commit messages, XML comments, `FEATURES.md` sections and
changelog entries that explain the finished work. Those are written from what the author now believes,
after the investigation has ended and while attention has moved to whether the code runs. Nothing
checks them, and they read as more authoritative than the issue did, because they are specific,
detailed and sitting next to working code.

> **Prose that explains a decision needs the same evidence the decision did.** When writing up
> finished work, treat every factual sentence as a claim to verify, not a summary of one already
> verified — especially the ones that begin "vanilla does…" or "the game declines to…". The check is
> one grep. The failure ships, gets quoted forward into three more documents, and is corrected in
> public.

The general form: an investigation has a natural check — you are looking things up, so you look this
up too. A write-up has none, because by then you are describing rather than discovering.

## A creature's blueprint is where it starts, not what it is carrying

Proving the scour slug's second-rust branch needed one number held still: how many things the target
is carrying. `RustOnHit` draws one item at random from equipment and inventory together, so pool size
*is* the experiment — with the chance temporarily at `100`, rust-then-dust on a pool of one is exactly
two hits.

I picked the target by reading XML. `Wraith-Knight Templar` → `Templar` → `BaseTrueKin` →
`BaseHumanoid` declares exactly one `<inventoryobject>`, a `Long Sword7`. Nothing on that chain
declares a `<builder>`. Across the whole of `StreamingAssets/Base` the creature's name appears in two
files, `Creatures.xml` and `Naming.xml` — no population table, no outfitting. Every static source
agreed on one item.

It took five or six hits. I spent a decompiling session on the gap and disproved three hypotheses in a
row: that `Crysteel` vetoes rust (it has no `ApplyRusted` handler and nothing rust-related at all),
that natural weapons pad the selection pool (`BodyPart.GetEquippedObjectCount` counts only `Equipped`,
never `DefaultBehavior`), and that the roll scales with level (`GetSpecialEffectChanceEvent.GetFor` is
pure dispatch — no built-in scaling of any kind). All three were hypotheses about code, because the
prediction I was defending had come from code.

The answer came from looking at the creature. It had a second weapon equipped that its blueprint does
not mention anywhere. Pool of two — and both runs, five or six and then four, are ordinary variance
for a pool of two. Nothing was ever broken.

A knight wished onto a bare floor has one weapon equipped. The one that had two had *both* equipped.
So it armed itself after spawning, from whatever was lying around. No amount of blueprint reading was
going to show that, because it is not a fact about the blueprint.

> **When an experiment's arithmetic depends on the state of a live object, measure the live object
> first.** A prediction read out of the XML is a prediction about a blueprint. The thing standing in
> the zone has a history — it picks things up — and that history is the variable the experiment
> actually rests on.

Two costs, worth separating. The small one is a session spent debugging code that was working. The
larger one is that I nearly wrote the result up with a cause attached — first that this fork's own
population merges had armed it, then that a vanilla `<builder>` had. Both were checked and both were
false. The section above says prose explaining a decision needs the same evidence the decision did;
this is that rule applied to the explanation of a *test result*, which is just as tempting to write
from the first mechanism that fits and has exactly as little checking it.

One limitation to know before designing the next one: **examine shows only what a creature has
equipped**, never its inventory, and no wish dumps another creature's pack — I read the whole command
list looking for one. The only reliable census is killing it with an ordinary weapon and counting
what drops.

## `Stat=` on a weapon names the penetration stat, and penetration multiplies the damage

`MeleeWeapon.Stat` looks like it should name the stat that adds damage. It does not. Reading
`Combat.MeleeAttackWithWeaponInternal` end to end: `text2 = Part.Stat` feeds `Attacker.StatMod(text2)`
into `Stat.RollDamagePenetrations`, and there is **no Strength term anywhere in the damage path**.
Damage is `Σ over Penetrations of roll(BaseDamage)`.

So the field sets penetration — but penetration decides how many times the damage die is rolled, so
the stat is a **multiplier on the weapon's whole output** rather than a side statistic. On a
`Long Sword8th` against AV 10, Strength 16 → 28 takes the same swing from 2.7 to 13.4 average damage.
The damage line never changes.

Two consequences that are easy to get backwards:

- **"Strength does not set melee damage" and "a long sword is a Strength weapon" are both true.** I
  wrote the second as a table of stat "affinities" and it read as a contradiction of the first.
  Whatever you call the column, say penetration.
- **Strength is not wired into combat at all.** Line 899 sets `string text2 = "Strength"` and line
  907 overwrites it with the weapon's own value. Strength is the *default value of an attribute*, not
  an engine assumption — which is exactly why a mod can move it and why the move is so large.

Vanilla holds the line rigidly: `Stat` is Strength on 4,351 of 4,354 melee weapons, `ThrownWeapon`
hardcodes `Stat("Strength")`, and the only two ranged weapons with a `ProjectilePenetrationStat` use
Strength for draw weight. Agility never scales damage anywhere. Verify that before assuming any
stat's role, because the field names do not tell you.

## Read the whole loop before modelling it — this one decays its own bonus

I modelled `Stat.RollDamagePenetrations` from its first thirty lines: three dice per wave, each
penetrating die scoring a penetration, all three rolling another wave. That gives an unbounded chain
and a curve about twice as steep as the real one, and it produced a table with a cell reading
10<sup>40</sup> damage before I noticed.

Both guards are in the tail, after the dice loop:

```csharp
if (num2 >= 1) num++;   // a wave scores ONE penetration, however many dice hit
Bonus -= 2;             // the bonus decays every wave, so the chain terminates
```

Neither is visible from the part of the method that looks like the interesting part. The
generalisable form: **a loop's termination condition and its accumulator are often nowhere near the
arithmetic**, and a decompiled method is exactly where that is easiest to miss, because the shape
that draws the eye is the innermost block.

The tell was the absurd number, and only because the input happened to reach a degenerate case. Had
I sampled a narrower range of stats the wrong model would have produced plausible figures and gone
into a document. **A model of game arithmetic wants one deliberately extreme input** for that
reason — the ordinary range will not tell you the model is wrong.

**There was an earlier tell and I missed it, because it looked like nothing.** The first version of
this model was a Monte Carlo simulation, and without `Bonus -= 2` the loop cannot terminate at all
once the effective bonus clears the target's AV by two: the minimum die is −1, so every die
penetrates, `wave` is always 3, and `while (wave == 3)` runs forever. I had backgrounded it when it
passed its timeout. It was still running seventeen hours later, pinning a core, and I only found it
because the interface said a task was live.

So the bug's first symptom was a **hung process**, not a wrong number — and I went and rebuilt the
same wrong model analytically instead, where the same degenerate case finally surfaced as a
printable absurdity.

> **A background task producing no output is indistinguishable from one still working.** Both are
> silent, and silence reads as progress. If a job is expected to print only at the end, it has no
> liveness signal at all, and a runaway can sit there for as long as the session does.

Two habits come out of it. Give a long computation **incremental output** — a line per row, not one
table at the end — so that silence means something. And when a model of a loop is being ported,
**bound the port** even if the original looks unbounded: a `for _ in range(80)` where the real code
has a decay costs nothing and turns an infinite loop into a visibly wrong number, which is the
failure you want.

## A weapon slot is any body part, not just a hand

`BodyPart.ScanForWeapon` walks the **whole body** recursively, and any part whose equipped item has
a `MeleeWeapon` passing `AttackFromPart` is added to the attack list. `Combat.PerformMeleeAttack`
then makes one attack attempt per part in that list. Two hands and two arms is four attacks.

`MeleeWeapon.Slot` is a restriction rather than a grant: `Slot="Arm"` means the weapon attacks
*only* from an Arm, so it cannot be stacked into hands — but an Arm holding one is a genuine extra
limb. Only the first part in the list is primary; the rest roll against
`RuleSettings.BASE_SECONDARY_ATTACK_CHANCE`, which is 15, plus 20/15/15 from the three Multiweapon
Fighting powers.

The balance consequence is entirely about **what else wants that slot**, and that is not something
the weapon's own blueprint shows you. Vanilla's Arm slot holds Kindrish, Otherpearl, the Transkinetic
Cuffs and the rest of the utility artifacts, nearly all at AV 0 — so vanilla's one arm-mounted
weapon, `ArmDagger4`, is trading an extra attack against a unique effect. Add ordinary armour to the
slot and that trade quietly stops being a trade. Before pricing an item that occupies an unusual
slot, enumerate what already lives there.

## A number that agrees because both sides share the error is not a cross-check

Deriving the armour curves in #340 I surveyed every vanilla blueprint carrying an `Armor` part,
totalled the per-slot maxima, and got **32** — the exact figure #318 had already published for
best-in-slot AV. That looked like independent confirmation from a second method, so I stopped
checking and wrote the curve.

It was a coincidence. Shields carry their AV on a **`Shield` part, not an `Armor` one**, so the
survey never saw a single one of vanilla's fourteen. My 32 was #318's 32 with the shield's 7
missing and two named artefacts wrongly included, and those two errors happened to cancel. The
curve shipped with no Shield column at all — in a document whose whole job was to give #319, *a
finding about a shield*, something to be a defect against.

Two things to take from it.

**A matching number is only evidence if the two derivations are actually independent.** Mine shared
the assumption that "armour" means "has an `Armor` part", which is the assumption that was wrong.
When a recount lands on a figure you were hoping for, the question is not *does it match* but *could
both of these be wrong the same way*.

**When a survey defines a category by one part name, ask what else delivers the same effect.**
Grepping `GetStat("AV")` finds only `Armor` — which is exactly why the miss was invisible. `Shield`
never touches the AV stat at all: it sets `E.ShieldBlocked` on a `GetDefenderHitDiceEvent` and its
AV applies to that one attack. Two mechanisms, one player-facing effect, and no shared symbol to
grep for. The category to enumerate is *"what reduces incoming damage"*, not *"what writes to the AV
stat"*.

That difference matters beyond the miss, because **shield AV is conditional and armour AV is not.**
Block chance is `25 * (1 + ImprovedBlock)`, plus 25 for `Shield_Block` and 25 for
`Shield_DeftBlocking` — so 25% bare, 75% fully skilled, and 100% only under Shield Wall. Any
best-in-slot total that adds a shield's AV to a body armour's is an upper bound, not a figure.

The tell I ignored: **the category had no members where the finding said the worst case was.** #318
named a shield in its own table and my slot list had no shield row. A survey that cannot see the
thing the issue is about has answered a different question.

## A commented-out blueprint is invisible to every check, and to nothing else

`mod/ObjectBlueprints/MeleeWeapons.xml` holds four objects inside a `<!-- rework these or remove
them` block — `Raven_Vibro Mace`, `Raven_Two-Handed Vibro Mace`, `Raven_Vibro War Hammer` and
`Raven_Two-Handed Vibro War Hammer`. They are not blueprints. They are text.

I tagged one of them by accident. The mace-ladder change in #342 needed a `Finesse` tag on ten
blueprints, I matched objects with a regex over the raw file, and the regex found the commented one
because a comment is just characters. The tag went in, the object stayed dead, and **every check
passed** — `validate_mod.py` parses with ElementTree, which does not see inside a comment, so there
was nothing for it to report. The defect reached `main` and shipped a changelog line promising a
tagged vibro mace that does not exist.

**Edit this file by parse, not by pattern.** If a script must work on raw text to preserve
formatting, reconcile the result against the parsed document before committing:

```python
live = {o.get("Name") for o in ET.fromstring(raw).iter("object")}
raw_objs = set(re.findall(r'<object Name="([^"]*)"', raw))
assert not (raw_objs - live) & touched      # touched something that is not a blueprint
```

`stat-discipline` already knew this and says so in its own docstring — *"Parses rather than greps,
deliberately… ElementTree does not see inside a comment"* — written because a line-based check
reported those same two vibro war hammers as violations nobody could fix. **The knowledge existed in
a docstring in the validator and nowhere a person writing an edit script would look.** That is the
part worth fixing, and why this is here.

**And counting by pattern fails the same way as editing by pattern.** Establishing that vanilla
declares `Role` as a tag and never as a property, I ran `grep -c 'tag Name="Role"'` over
`ObjectBlueprints/` and got 352. The real figure is **349**: three of those lines sit inside
commented-out blueprints in `Creatures.xml`, one of them a robot called Graftek. I had the number
wrong in a changelog entry, a lesson on this very page, an issue and a pull request before parsing
the same files and getting a different answer. `requested_inherits_slices` strips comments before it
counts, for exactly this reason, and says so — I did not extend the courtesy to a one-line check of
my own. **A figure that is going into prose deserves the parse too**, because prose has no test.

The general shape: **a validator that ignores a region cannot protect that region.** Anything
deliberately excluded from checking is somewhere mistakes accumulate silently, so a change that
writes to the file rather than through the parser has to police itself.

## Nothing checks that `Inherits=` names a blueprint that exists

Writing the spear line for #342 I gave nine blueprints `Inherits="BaseShortBlade"`. There is no such
object. Qud's Short Blades base is **`BaseDagger`** — the bases are `BaseAxe`, `BaseCudgel`,
`BaseDagger`, `BaseLongBlade`, and a handful of ranged ones.

`validate_mod.py` reported nothing. The file parses, the objects are well-formed, `unreachable` fired
about population tables and said nothing about the parent. `dangling-blueprint-ref` checks table
references, not inheritance. So nine weapons would have shipped inheriting nothing, and by §1.1b's
own mechanism the failure is silent: `GetBlueprint` misses, logs through `MetricsManager`, and hands
back the generic `Object`. Degraded, not broken, and invisible.

I found it only because I stopped to ask what `BaseShortBlade` actually contained before relying on
it. **That question is the check.** Until something enforces it, confirm the parent exists before
writing a line of a new family:

```bash
grep -ho '<object Name="Base[A-Za-z]*"' "$BASE"/ObjectBlueprints/*.xml | sort -u
```

Two things worth carrying beyond the specific mistake.

**An invented name is more dangerous than a wrong one.** A typo of a real base — `BaseCudgle` — fails
the same way, silently, so neither spelling nor plausibility helps. Only existence does.

**Inheriting the nearest base is not automatically right either.** `BaseDagger` carries
`DynamicObjectsTable:Daggers`, so a spear inheriting it would appear anywhere the game asks for a
dagger specifically. The spears inherit `MeleeWeapon` and declare their skill, mods and sounds
explicitly instead. **Read what a base actually grants before adopting it** — the tags it carries
travel with every child.

## A scope that looks load-bearing may match nothing at all

The entry above says to confirm a parent blueprint exists before building on it. This is the same
question asked of a *relationship* rather than a reference, and the answer surprised me more.

`Naming.xml` scopes on `Culture` **50 times**, naming 36 distinct cultures — twice as often as it
scopes on `Species`, which it uses 25 times. Read the scope table and the design looks obvious:
culture is how a creature gets a culturally appropriate name, and species is the fallback for things
that have no culture. I was one step from building #436 on top of that.

It is the wrong way round. `Culture` is a blueprint tag with a species fallback:

```csharp
public string GetCulture()
{
    return GetPropertyOrTag("Culture") ?? GetSpecies();
}
```

And almost nothing carries the tag.

| | |
|---|---|
| `Culture` tags across every vanilla blueprint | **41 instances, 33 distinct values** |
| Runtime writes of `Culture` in the whole 12 MB assembly | **one** — `EndGame.cs`, `"Chiliad Qudish"` |
| Village generation touching `Culture` | **none** — `VillageBase`, `Village` and `VillageMaker` never mention it |
| Scoped cultures that can never match a creature | **7 of 36** |

The dead seven are `Qudish`, `Arcologian`, `Ekuemekiyyen`, `Ibulian`, `Yawningmoon`, `Chiliad
Qudish` and `Ape`. The first is the one that matters: **the Qudish namestyle's `Culture="Qudish"`
scope at Priority 100 has never fired, in any game anyone has ever played**, because no blueprint in
Caves of Qud is tagged with it. Qudish reaches creatures entirely through its Priority-0 `General`
scope and `Genotype="Mutated Human"`. The rest of the `Culture` scopes are duplicates of their own
style's `Species` scope, reachable only through that `?? GetSpecies()` fallback.

**`Ape` is dead for a second reason, and it is the more general one.** Apes carry no `Culture` tag,
so the fallback supplies their species — which is `ape`. The scope asks for `Ape`. `NameScope.ApplyTo`
compares with `Culture != this.Culture`, an ordinal `string` comparison, so the capital is fatal.
`Bear`, `Bird` and `Antelope` look identical and work, because a blueprint tags each of them with the
capitalised spelling. Nothing distinguishes the working ones from the broken one by reading.

**The check is counting the other end**, and everything above came out of two commands. A grep for
what actually carries the tag:

```bash
grep -rhoE '<tag Name="Culture" Value="[^"]*"' "$BASE"/ObjectBlueprints/ | sort | uniq -c
```

and a search of the assembly for anything that writes it at runtime. Ten seconds, and it settles a
design question that I had otherwise been arguing about on taste.

**Before building on a data relationship, count the things on the other end of it.** A scope, a tag,
a table reference and an `Inherits=` are all *assertions that something is there*, and each of them
parses, validates and ships whether or not it is. This is the same family as an orphaned
`Load="Merge"`, a missing `[PlayerMutator]` and a `Priority="0"` scope handing back `NameGenFail1`:
data that is well-formed, passes every check, and does nothing.

There is a second, less comfortable point. **`tools/naming_harness.py` could have answered this
before #436 was ever written.** It reimplements `XRL.Names` precisely so questions like this stop
being guesses, it was sitting in the repository the whole time, and I did not think to ask it — I
read the XML instead and drew a conclusion from how the file looked. A tool built to answer a class
of question only helps if the question gets asked of it.

## Putting a value back is a change, and needs the same neighbour check as moving it

#335 restored `DermalPlating` to vanilla's 3 licence points for +1 AV. That was the right call, made
for the right reason, and it verified correctly: the value matched vanilla, the stacked ceiling it
was aimed at came down from +12 to +6, and every check passed. The balance sweep closed.

It also made vanilla's only dermal plating **dead content**. This fork sells a steel rung at 1 point
for the same +1 AV, and a crysteel rung at 3 points for twice it. Neither moved in #335, so neither
appeared in the diff. Put back where it belonged, carbide landed strictly worse than two things
standing beside it, and there was no state of the game in which a player should install it.

**Reverting felt like the safe direction, and that is why I did not check.** A change that makes an
item stronger obviously needs weighing against its neighbours. A change that puts a number back to
vanilla's reads as a *removal* of an opinion — as returning to the state where, by definition,
nothing is out of place. But the neighbours were not vanilla's. They were mine, priced against the
buffed carbide, and restoring the anchor moved every one of them relative to it without touching a
line of their XML.

**The test is positional, not directional.** Before changing any value, list what a player is
choosing *between* and check the whole set afterwards — including the entries the diff does not
touch. A rung is dominated when something costs less for the same benefit, or the same for more, and
that is arithmetic over the set rather than a property of the item you edited.

**I caught it the same day, and that is the uncomfortable part.** #335 and the fix are hours apart in
`git log`. I was not returning to cold code — I had written the restore, argued for it in the issue,
and could still recite why. I found the domination anyway only because I went to look up the plating
costs for an unrelated in-game check and read all four rows at once. Familiarity with a change is not
coverage of it; the diff was the thing I knew, and the diff was where the defect was not.

There was a second layer under it, and it is the more general trap. `Implants_3Pointers` is a vanilla
population table, and its **name is a claim about its contents**. Re-pricing crysteel from 3 points
to 6 invalidated a placement in a *different file* that never mentioned the cost — so the loot table
went on saying *3 Pointers* while holding a 6-point implant, and nothing in the game or in `tools/`
had any opinion about it.

**When a name encodes a value, editing the value edits the name's truth.** Grep for the identifier
you are re-pricing before you finish, not just the file you are in. `implant-table-cost` in
`tools/validate_mod.py` now holds this particular coupling, per charter rule 4 — but the general
version has no check and probably cannot have one. Bracket names, tier names and table names are all
assertions, and the thing that makes them dangerous is that they are usually right.

## A knob that accepts your value and rounds it away is worse than no knob

`DynamicObjectsTable:<Table>:Weight` looks like a rarity dial. Vanilla sets it on ten blueprints —
`Astral Tabby` at 0.2, `Ixlthyxl` at 0.1, `Issachari Raider` at 3 — and I read that spread as
evidence the game tunes creature rarity with it deliberately. I then built a whole rarity curve on
top: 0.5 for common coats, 0.25 for uncommon, 0.08 for the albinos. It was internally consistent,
documented, and completely inert.

Three facts compose, and no one of them is visible from the XML:

1. **No creature table is ever requested in the `:Tier` form.** Zero occurrences across the whole of
   `StreamingAssets/Base`, so they are all built by `FabricateDynamicObjectsTable` rather than the
   multitier path — and the two methods weight entries completely differently.
2. **In that method the tier-delta bonus is unreachable.** `num` and `num2` initialise to `-1` and
   are never assigned, so the `TierDeltaWeights` lookup guarded by `num != -1` never runs.
3. **`:Weight` is a multiplier wrapped in `(uint)Math.Ceiling`.** On a base of 1, `ceil(1 × 0.25)`
   is 1, `ceil(1 × 0.08)` is 1, and so is every fraction below one.

The floor is 1 and there is nothing under it. Vanilla's own fractional weights do nothing either,
which is the detail that should have warned me and instead reassured me: I had counted them, made a
5%/95% argument out of the count, and never asked whether the 5% *worked*.

> **Corrected in #492, and the correction is where the interest is.** I wrote above that "the base
> weight is exactly `1u` for every entry". It is not. There is a **third** multiplier in the same
> loop, and unlike the tier delta it is reachable:
>
> ```csharp
> if ((list[i].Tags.TryGetValue("Role", out var value2) || list[i].Props.TryGetValue("Role", out value2))
>     && RoleWeightMultipliers.TryGetValue(value2, out var value3))
> {
>     num6 = (uint)Math.Ceiling((double)num6 * value3);
> }
> ```
>
> `InitWeights()` fills that table with `Common` and `Minion` at **4.0**, `Skirmisher` at 1.0,
> `Artillery`/`Uncommon`/`Brute`/`Tank` at 0.25, `Specialist`/`Leader`/`Hero` at 0.1, and
> `Rare`/`Epic` at 0.01. Every one of those below 1.0 still ceilings to 1 — but 4.0 does not. **On a
> `Common` or `Minion` blueprint the base weight is 4**, and there `:Weight` 0.5 gives 2 and 0.75
> gives 3. The dial works.
>
> The part that stings: `Dog` is `Role="Minion"`, and it is one of my own variant parents. The 0.5 I
> chose for common coats would have done something on the dog variants and nothing on the goat, boar,
> bear and equimax ones, whose parents are all `Brute`. **"Completely inert" was a tidier story than
> the truth, and I preferred it without checking.**
>
> Worth knowing while you are in there: `Controller`, `Lurker`, `NPC`, `Summoner`, `Breeder` and
> `Unspecified` are used on **63** vanilla blueprints and appear in no multiplier table at all, so
> they silently take the plain base weight.
>
> Nothing shipped depends on this — every `:Weight` tag was removed from `Creatures.xml`. It is the
> lesson that was wrong, and the lesson is what future me will trust. The other half, where the dial
> works in *every* `:Tier`-requested pool rather than only on two roles, is #493.

> **A setting the engine accepts, stores, and quietly discards is indistinguishable from one that
> works — from the outside, and from the diff.** Vanilla using a value is evidence that vanilla's
> authors believed in it, not evidence that it does anything.

This is the same family as the vacuous shell loop and the scope that matches nothing: **silence read
as success.** What makes this one nastier is that there is no silence to notice. The tag parses, the
table builds, the creature spawns. Everything works; only the number is a fiction.

**What to do instead.** When a value is meant to change a frequency, find the code that consumes it
before writing the curve, and check what the value is multiplied *by* rather than only what it is.
`ilspycmd -t <Type> Assembly-CSharp.dll` answers this in about a minute and would have saved the
entire weight design.

**The postscript is worse than the lesson.** All of the above is true, and none of it mattered:
`DynamicObjectsTable:<Biome>_Creatures` is not rolled by anything that populates a zone, so the
weights I was so carefully computing governed a pool no hillside consults. I audited the arithmetic
of a mechanism twice without once asking what called it. (It *is* called — by village generation.
See the entries below, including the correction.)

**The mechanism that did work was three lines further down the same method.** `AggregateWith` bundles
a family into one slot weighted by its max member, which is how vanilla stops the eight snapjaws from
owning their tables. I had read past it twice while looking for a weight to set.

## A tag you merge onto a parent lands on every child that parent ever had

`AggregateWith` bundles everything carrying the same value into one slot in a spawn table. I merged
it onto thirteen vanilla creatures so each of my variants would share its parent's slot instead of
taking a new one, and wrote in the feature reference that the tables therefore did not grow.

They shrank. The tag **inherits**, so merging it onto `Baboon` also reached `Hulking Baboon`,
`Shrewd Baboon` and `Baboon Hero 1` — three distinct creatures vanilla had given three separate
slots — and folded all four into one. Baboons in the hills became roughly four times rarer.
`ClockworkBeetle`, a machine, began competing for the giant beetle's slot. `Sultan Croc`, a named
legendary, shared the ordinary croc's. Hills lost five slots, DesertCanyon and Jungle four each.

> **Merging a tag onto a vanilla record is not an edit to that record. It is an edit to that record
> and to everything descended from it.** The blast radius is the subtree, and the subtree is not
> visible from the diff — which shows one `<object Name="Baboon" Load="Merge">` and three lines.

The charter already says to know the blast radius, and I had even applied it correctly elsewhere:
the `Chip Interface` merge into base `Humanoid` is documented as reaching every humanoid in the
game. I did not think of `Baboon` as a base. It has a display name, an icon and a description; it
reads as one animal rather than as the head of a family. **Anything with an `Inherits` pointing at
it is a base, whatever else it looks like.**

Two things made this survive review. Every static check passed, because nothing errors: the tag
parses, the table builds, the creatures simply get rarer. And my own arithmetic in the pull request
was right about the variants and never asked the second question — I counted what I was adding and
never counted what vanilla already had underneath.

**What found it was playing the game.** Grey walked a run of zones and reported seeing exactly one
named variant, plus goats called "goat" and baboons called "baboon". That is a symptom no check I
had written could produce, and the first honest read of it was that my design was wrong rather than
that the observation was.

**What to do.** Before merging a tag onto a vanilla record, list its descendants — one pass over
`Inherits` answers it — and decide for each whether the tag belongs there. Where it does not,
`*delete` is vanilla's own idiom for dropping an inherited tag. Then encode the answer: `tools/
qud-api.json` records the descendant list and `aggregate-sweep` in `tools/validate_mod.py` fails
until each is exempted, so a Qud patch adding a descendant becomes a red run instead of a slow
change in what the world spawns.

## A pool with no members can be live, and a pool with 191 can be dead

Four times I shipped something aimed at a declaration whose consumer I had not traced — #171, #177,
#476, #478 — and the rule that came out of it is above: *"Does anything read this?" is the wrong
question. "Does the thing that reads it run where I need my content to appear?" is the right one.*

Auditing against Freehold's own wiki I found the mirror image, and it matters because the obvious
defence against my usual mistake gets this one exactly backwards (#505).

`VillageCodaBase.cs:1694` picks a plant for a coda village in three steps:

```csharp
string populationName = ResolvePopulationTableName("Village_Plants");
if (PopulationManager.HasPopulation(populationName)) { text = ...RollOneFrom(populationName)...; }
if (text == null) { text = ...RollOneFrom("DynamicObjectsTable:Coda_" + region + "_Plants")...; }
if (text == null) { text = ...RollOneFrom("DynamicObjectsTable:" + region + "_Plants")...; }
```

`Coda_<region>_Plants` is rolled every time a coda village is built, and **no vanilla blueprint
declares membership in it.** I searched every XML file in the install. It is an extension point with
zero members and a documented fallback behind it.

Set that beside `<Biome>_Creatures`, which **123 vanilla blueprints** declare into and which does
not put a creature in a zone, and the pair says the thing plainly:

> **Membership count and liveness are independent, and neither implies the other.** A pool with no
> members can be rolled on every village. A pool with a hundred and twenty-three can be rolled by
> nobody. "Who declares this?" is not a proxy for "is this real?" — they are two questions and both
> have to be asked.

The cheerful consequence: my three plants reach coda villages through that third line for free,
without a `Coda_` tag, because the fallback catches them.

**What to do instead.** Ask the two questions separately and answer each at its own end. Membership
is answered in the data — grep the tag. Liveness is answered in the assembly, or with
`population:generate:<table>#<amount>`, which fabricates the table by name rather than waiting for
something to have rolled it.

This is also the first time in the audit that checking the far end came back *"no consumer, nothing
to worry about"* rather than *"you built the wrong thing"* — the `<stag>` categories in #501 were
the other. Worth saying, because four bad results in a row make the check feel like a formality
right up until it is not.

## Count the consumers before you count anything else

Everything above about creature spawn weights is accurate and was worth nothing, because
`DynamicObjectsTable:<Biome>_Creatures` **does not put a creature in a zone**. 123 vanilla creature
blueprints tag themselves into sixteen of those tables. No population table references one, and no
zone builder requires one.

> **Corrected later, and the correction is the more useful fact.** I originally wrote that these
> pools have *no consumer at all*, on the strength of finding nothing in `Assembly-CSharp.dll`. That
> search was wrong — see *"strings cannot see a .NET string literal"* below — and every biome-keyed
> pool does have a consumer: **procedural village generation**, in `VillageBase.cs:167`,
> `Village.cs:734` and `VillageCoda.cs:1369`. So the tag was not inert. It was for villagers, and I
> was expecting wilderness.

Biome creatures come from ordinary hand-written populations. `HillsZoneGlobals-Reachable` lists
`Goat`, `Dog`, `Boar` and `Salamander` as explicit `<object Blueprint=>` entries, which is exactly
what a player meets in the hills.

I built a whole feature on that tag: 32 blueprints, 72 `*delete` tags to control which pools they
joined, 13 merges and 10 exemptions to balance the slots. All of it aimed at tables nobody rolls.
Three rounds of decompiling, two shipped pull requests, and a validator check written to guard the
mechanism — none of which could fail, because everything I built was internally consistent.

> **A declaration is evidence that someone wrote it, not that anything reads it.** Before building
> on a mechanism, find the *other end*: grep for the name outside the files that declare it. If
> every hit is a declaration, there is no mechanism.

`docs/LESSONS.md` already carried this, from nine hours earlier: *a scope that looks load-bearing may
match nothing at all*, written after finding that `Culture="Qudish"` matches no blueprint in the
game. I wrote that entry, filed the issue, and then made the identical mistake inside the next
feature — because there I was counting *vanilla's* usage rather than my own, and 191 tags felt like
proof. It is proof that Freehold typed them.

**And what found it was the game, not the code.** Grey played, saw plain goats and boars where the
design predicted half variants, and reported it. Every static check passed throughout. The wish
`population:findblueprint <name>` enumerates every table in `PopulationManager.Populations` with the
odds of that blueprint appearing in each — it is the fastest way to answer "does my thing actually
spawn", and one run of it would have settled in seconds what I spent hours inferring.

> **Reach for `population:generate:<table>#<amount>` instead when the question is about a table
> rather than a blueprint.** It rolls a named table N times and breaks down what came out, and
> Freehold's [wish list](https://wiki.cavesofqud.com/wiki/Wishes) says it takes dynamic tables
> directly:
>
> ```
> population:generate:DynamicObjectsTable:BananaGrove_Ingredients#100
> ```
>
> The difference is not convenience, it is that **`findblueprint` cannot see a table that has not
> been built yet.** It enumerates `PopulationManager.Populations`, which holds what has already been
> fabricated — so a pool nothing has rolled in that session is simply absent, and absence reads
> exactly like "no consumer". That is the false negative below: I ran it after a session with no
> village in it, saw no `*_Creatures` table, and called the family decoration. Naming the table
> sends it through `RequireTable`, which fabricates it on demand, so the question gets answered
> instead of dodged.
>
> **It has a false negative of its own, though, and it looks identical to failure.** `RequireTable`
> fabricates a pool for *any* name carrying the prefix, so a misspelled one builds an empty table,
> caches it, and reports nothing — no error, no "unknown table". Grey typed
> `SaltMarshes_Ingredients` for `Saltmarsh_Ingredients` while checking #489 and got
> "did not generate any results", which reads exactly like a tag that did not take. Had that been
> the first pool tried rather than the third, I would have gone hunting a bug that was not there.
>
> **So an empty result is only evidence once the name is known to be right.** Confirm the spelling
> against the blueprint that declares it — `grep -o 'DynamicObjectsTable:[A-Za-z_]*'` over the file
> you just edited — before reading emptiness as anything at all.

I did not know that wish existed until I indexed the wiki (#506), which is its own small argument
for `docs/WIKI.md`: the tool that would have prevented this entry was documented the whole time.

**The rule generalises, and #177 is where I found out how far — then how far it does not.** Adding
harvestable plants, the obvious way to distribute a preserved cooking ingredient was
`DynamicObjectsTable:<Biome>_Ingredients`. No population table names one, so I wrote that the whole
biome-keyed family was decoration and that only flat pools — `Ammo`, `Chests`, `Corpses`,
`EnergyCells`, `Guns`, `Items` and the rest — are ever rolled.

**That was wrong, and it stayed wrong in three documents until a playtest question sent me back.**
Every biome-keyed pool is rolled, from C# rather than from data:

| pool | rolled by |
|---|---|
| `<Biome>_Creatures` | `VillageBase.cs:167`, `Village.cs:734`, `VillageCoda.cs:1369` |
| `<Biome>_Ingredients` | `VillageBase.cs:2586`, `VillageCodaBase.cs:2866` |
| `<Biome>_Plants` | `VillageBase.cs:1430`, `VillageCodaBase.cs:1705` |
| `<Biome>_FarmablePlants` | `VillageBase.cs:1412` |

They are all **procedural village generation** — who lives there, what they farm, what the walls are
made of. Not zone spawns. So the #171 tags were never inert; they were pointed at villages while I
was watching hillsides.

> **Two consumers, and only one of them was mine.** "Does anything read this?" is the wrong
> question. The right one is **"does the thing that reads it run where I need my content to
> appear?"** A pool with a real consumer can still be the wrong pool.

The grep shortcut I wrote here — enumerate `DynamicObjectsTable:` out of `PopulationTables.xml` and
treat anything absent as decoration — is **necessary but not sufficient**, and stating it as
sufficient is what produced the error. Pool names are built at runtime by string concatenation, so
they cannot be found by grepping data at all.

## `strings` cannot see a .NET string literal

Three of my findings rested on `strings Assembly-CSharp.dll | grep …` coming back empty, and all
three were wrong. .NET stores string literals in the metadata `#US` heap as **UTF-16**, and `strings`
reads ASCII by default — so it finds *identifiers* (method and type names, which are UTF-8) and
silently misses every literal. macOS `strings` has no `-e` flag to fix it either.

Recovering them takes four lines:

```python
import re
b = open(dll, 'rb').read()
literals = {m.decode('utf-16-le') for m in re.findall(rb'(?:[\x20-\x7e]\x00){3,}', b)}
```

That turns up 28,872 literals in this build, including the `_Ingredients`, `_Creatures` and `_Plants`
suffixes I had reported as absent.

> **An empty grep is only evidence if the grep could have found the thing.** The failure mode is
> especially nasty here because a *partial* result looks like a working method: identifier searches
> returned plausible hits all along, so nothing signalled that literal searches were returning
> nothing on principle.

The reliable answer is to decompile and grep the source: `ilspycmd -o <dir> -p Assembly-CSharp.dll`
writes 5,435 `.cs` files in a couple of minutes, and a grep over those finds the call site with its
containing method, which is what actually answers the question.

### The sharper version: a search that could not *run*

The entry above is about a search that could not match. This one is about a search that could not
execute, and it is worse, because the shell hands back a value rather than an error.

Assessing #638 I ran:

```bash
for f in Stealth.cs Hidden.cs HiddenRender.cs; do rg -c '…' "$SRC/$f" || echo 0; done
```

and reported **0, 0, 0** — written up as *"zero references in the stealth machinery."* `Stealth.cs`
does not exist. `rg` failed on it, `|| echo 0` swallowed the failure, and a missing file was reported
as a clean negative. The other two return **1**, not 0. So two of the three numbers were wrong and
the third was meaningless.

> **A shell fallback that turns an error into a value launders a failure into a finding.**
> `|| echo 0`, `2>/dev/null`, a bare `-f` guard: each converts *"I could not look"* into *"I looked
> and found nothing."* Before believing a zero, confirm the thing you searched exists.

The conclusion survived only because I re-derived it from the type list instead, and the one real
reference turned out to be benign. That is luck, not method.

## A version number cannot express a boundary inside a version

#497 converted three classes to the `IScribed` bases, which changed what they write: `IComponent`
writes each public instance field unnamed, so a class with none writes **nothing**, while
`WriteNamedFields` writes a count first, so the same class writes a zero. One byte, and a real format
change. `Vixy_SaveFormat` existed to tell one format from the other, by comparing the mod version
recorded in the save against the last version that wrote the old one.

**It could not work, and the reason is worth keeping.** `v2.7.0` was tagged at 04:23 and #497 landed
at 12:20 the same day, so a save recording `2.7.0` was written either by the release, which wrote
nothing, or by an unreleased build, which wrote a block. The version is identical in both cases.
`manifest.json` cannot move ahead to break the tie either — `check_version_matches_changelog` binds
it to the newest *released* changelog heading, so bumping it means cutting a release.

> **A version identifies a release, not a commit.** Any question of the form "did the code that wrote
> this have change X" is unanswerable by version whenever X landed between a tag and the next one —
> which is where every change spends most of its life.

**The failure was silent and unbounded, which is the other half.** `IPart.Load` reads a length
prefix, keeps `Position` and `Length` as locals, and repositions to the end of the block **only from
inside its `catch`**. So reading *too much* throws, gets caught, and `SkipBlock` puts the stream back
— the component is dropped from that object and nothing else suffers. Reading *too little* throws
nothing at all, and every object after it in the zone deserialises from bytes that are not its own.
The log said `Recovered from game object deserialization error` 48 times in one session, on
`Desert Rifle`, `Musket`, `Humanoid`, `Hypertractor` — none of which is the component that
under-read. The blast lands downstream of the fault.

> **Over-read is contained; under-read is not.** When a format guess can go either way, guess long.

**The fix was to delete the question.** All three classes hold no serialisable state, so the block
they wrote was a count of zero and nothing else. Suppressing both halves — `Write` writing nothing,
`Read` reading nothing — gives one shape in every version, and a boundary that does not exist cannot
be got wrong. The classes stay on the `IScribed` bases, which is the part that is expensive to do
later; when one gains a field, both overrides come out, and by then the version really will have
moved.

Nothing repairs the saves already written. The stray byte is indistinguishable from the next
component's data, which is the same reason the guard could not work. #554.

## A field declaration is three lines long, and I keep reading one of them

Converting three classes to `IScribedPart` (#497) turned on one question: do they hold any state
that a change of serialization format would lose? I answered it four times and got three different
answers, because I kept reading the declaration and not the attribute above it.

**First pass**, filing the issue: I grepped for field declarations, saw
`private string Pending;` on `Vixy_AmmoPayload`, and wrote that it "carries risk today — it holds an
instance field, which is precisely the case migration protects." The line directly above it is
`[NonSerialized]`, and the comment above *that* explains at length that the field is transient by
construction. I had read neither.

**Second pass**: I found that both writers default to `BindingFlags.Instance | BindingFlags.Public`,
so a private field is never serialized anyway. Right conclusion, and it made the first one wrong
twice over.

**Third pass**: `IPart` declares `public GameObject _ParentObject`, and `Effect` declares five more —
`ID`, `DisplayName`, `Duration`, `_Object`, `_StatShifter`. Inherited public fields *are* included by
`GetCachedFields()`, so I concluded all three classes did carry state after all, and that the whole
conversion was unsafe.

**Fourth pass**: every one of those six is `[NonSerialized]` too, and the mask in `WriteNamedFields`
excludes exactly that. `Effect.Load` reads `ID`, `DisplayName` and `Duration` explicitly before
calling `Read`, which is *why* they are marked — the container owns them, not field reflection.

The answer was the one I first assumed, arrived at only on the fourth try, and I would have shipped
a save-desynchronising change on the third if I had stopped there feeling vindicated.

> **In C# a field's serialization behaviour is not in its declaration.** It is in the attribute
> above it, the `BindingFlags` of whoever reflects over it, and the `FieldAttributes` mask that
> reflector applies. Reading the declaration alone answers a question nobody asked.

This is the same shape as the `<stag>` misread in #478 and the `*noinherit` inversion in #171: a
symbol whose meaning lives in a modifier I did not look at. The tell each time was that the finding
felt like it settled the matter after one grep.

**What to do instead.** When the question is "is this serialized", read the whole declaration
including attributes, then find the reflector and read its flags and mask, then check whether a
container reads the field explicitly. Three places, and any one of them can make the other two
irrelevant.

## A palette copied from another plant is not a palette chosen for this one

Cragwort took noisegrass's sprite and, without my thinking about it, noisegrass's colours: `&K` on a
`&K` tile, the darkest grey in the game. That is fine for noisegrass, which grows in fungal and
underground zones. Cragwort grows on open mountain surface, beside dogthorn at `&G` and witchwood at
`&W`, and it was invisible.

The playtest is what said so, and it said so indirectly: several parasangs of mountains produced **no
cragwort and several witchwood**, which roll from the same table at `Chance=40` and `Chance=25`. The
rarer plant turning up and the commoner one never is not a distribution result, it is a contrast
result.

> **A tile is legible against a background, not against the plant you borrowed it from.** Reusing
> vanilla art is cheap and right; reusing the colours it was given for a different biome is not.
> Check the palette against what the player will actually be looking at.

There is a second half. **Vanilla signals ripeness with a change of hue** — witchwood `&W` → `&r`,
starapple `&g` → `&R`, noisegrass `&K` → `&M` — and cragwort's ripe state changed one detail pixel
and left the tile black. Even a ripe one was indistinguishable at a glance, which defeats the point
of `StartRipeChance` entirely: the number decides how often a plant is worth harvesting, and the
colour is how a player finds out.

## Whether the game deduplicates a placement is a property of the biome, not of the entry

Six harvestable plants, written to one pattern, merged the same way into six biomes. Three of them
could put two of the same plant in one cell and three could not, and nothing in my XML said which
was which.

The switch is in `ZoneTemplates.xml`, a file this mod never touches:

```xml
<population Table="HillsZoneGlobals" Hint="Any"></population>   <!-- Hills, Mountains, DesertCanyon -->
<population Table="JungleZoneGlobals"></population>             <!-- Jungle, SaltMarsh, BananaGrove -->
```

`PlacePopulationInRegion` passes that value down as a default hint, and a hinted placement runs

```csharp
Points.RemoveAll(l => !Z.GetCell(l).IsEmpty() || Z.GetCell(l).HasObject(gameObject.Blueprint));
```

where the second clause is the only same-blueprint check in the path. With no hint, `Points` is never
built at all and placement falls through to a fallback filtered on `IsReachable() && IsEmpty()`.

**And `IsEmpty()` does not mean empty.** It returns false only for an object rendering above
`RenderLayer` 5. `Plant` ships at 3, every vanilla plant inherits it, so the fallback cannot see a
plant that is already standing there. The guard runs, passes, and places a second one.

> **A predicate named for the general case may be measuring something much narrower.** `IsEmpty()`
> is really `HasSomethingDrawnAboveLayer5()`, and it is used as an occupancy test in dozens of
> places. Read what a guard measures before trusting what it is called.

Two things made this hard to see from the mod side. The symptom is a **grammar** bug —
`You pass by a brinereed and a brinereed`, because `Physics.EnterCell` lists every object in the cell
and `Grammar.MakeAndList` neither deduplicates nor counts — so it reads as a text problem rather than
a placement one. And it is invisible in three of six biomes, which is exactly the pattern that makes
a bug look like something else. I first assumed the mod I saw it in was doing something exotic; it
was not, it was calling `IsEmpty()` in a loop on a `RenderLayer=1` object.

**What to do instead.** Write the hint on the entry even where the template already supplies it. Six
identical lines are cheaper than one invariant that holds in half the file for a reason living in
someone else's XML. The same goes for anything else the caller can default: if correctness depends on
it, say it locally.

Creatures looked exempt, and the reason looked good — `PlaceObjectInArea` carries a separate
`workingSet.RemoveAll(p => Z.GetCell(p).HasCombatObject())`, which is not blueprint-keyed and so is
stronger than the plant guard rather than weaker. **That sentence stood here until #613 and it was
wrong.** The entry below has what actually happens; the sweep for "what else does this affect" was
narrower than the truth, and I had checked, which is the part worth sitting with.

## A check that skips is louder than a check that fails, and quieter than both is one that skips silently

`check_placement_hint` shipped in #542 and could not see the first content that needed it. It looks
a merge target up in `template_hints`, and `collect_template_hints` recorded only tables a zone
template *names*. The ruins vegetation this fork merges into sits one level below the table the
template names, so the lookup missed, the check returned early, and validation passed.

The propagation is one line of the game's own code:

```csharp
Population.Generate(Result, Vars, Hint ?? DefaultHint);   // PopulationTable.Generate
```

A `<table>` reference hands its own hint down, or the one it was given. Nesting was never a barrier
to the hint — only to my model of it.

> **When a check keys on a name, ask what else can wear that name's clothes.** I had verified the
> hint reached six biome tables and generalised to "the table the template names". The thing being
> modelled was "the table a placement ends up in", and those differ the moment anything nests.

The tell was there and I nearly walked past it. Running the finished content, `template_hints` came
back `None` for both of my targets. My first reading was "these aren't template-referenced tables,
so the check correctly has no opinion" — which is exactly what a silent skip looks like from the
inside. What made me look again was that it *should* have had an opinion: the ruins templates
obviously place vegetation, so a vegetation table having no placement route was a contradiction, not
an exemption.

**What to do instead.** A check that returns early needs a case in its own tests where the early
return is wrong, not only cases where it is right. Every skip branch here has a test asserting the
skip; none of them asserted that the *set of things skipped* was correct. Widening the citation from
10 tables to 69 changed nothing about the check's logic and everything about what it sees.

There is a second, cheaper lesson. **The fix landed because content was written against it within
the hour.** Tooling merged with no consumer is tooling nobody has proven. If a check is built ahead
of the content it guards — which is the right order — the content is still the test.

## The same blind spot, in a second check that did not inherit the fix

#544 taught `scatter_quantity` to follow a `<table>` reference into a table this fork writes,
because vanilla's overgrowth idiom is a sub-table and a `Vixy_` copy of it would otherwise measure
as nothing. I wrote that resolution, tested it, documented it — and did not apply it to
`check_placement_hint`, which keys on the same merge blocks and had the same hole.

The result: **all three of this fork's patch tables were unguarded at once.** Stripping the hint from
every one of them produced zero findings. The hints were correct in the content, because I had put
them there deliberately; nothing was enforcing them.

> **A fix to one check is a question asked of every check that shares its shape.** Both of these
> read `Load="Merge"` blocks and stop at their direct children. The moment one of them learned that
> content can live one reference away, the other was already wrong.

This is the third instance of one pattern in two days, and the pattern is worth naming: a check keyed
on **where I write something** rather than on **where it ends up**.

- `check_placement_hint` looked up the table a template *names*, and missed everything nested under
  it (#173).
- `scatter_quantity` summed the merge block, and missed everything behind a reference (#544).
- `check_placement_hint` again, same reference, different check (#547).

**A second variant of the same disease, twice in one week.** Both of these checks named one
instance in a string literal and silently stopped covering the file when a second arrived.

- `check_docs.py`'s `WORD_NUMBERS` stopped at `twenty`, and the capture groups stopped at `\w`. The
  mod reached its twenty-first option, three documents spelled it *"Twenty-one"*, and the check
  failed pointing at `one` — the wrong figure, with a message about an unknown number rather than a
  stale count (#605).
- `naming-option-coverage` compared each namestyle against the literal `"Qudish"` and skipped
  everything else. It had been correct for as long as Qudish was the only namestyle this fork
  merged into; the moment the Issachari pools arrived it covered nothing while still passing, which
  is exactly the failure it was written to prevent (#632).

> **A check that names one instance is a check with an expiry date.** It passes hardest at the
> moment it stops being true, because nothing about a check that silently narrows its scope looks
> different from a check that found nothing wrong.

The tell is the same in both: a literal naming *the thing there is currently one of*. Keying on a
map, and reporting an entry the map has that the data does not, costs a few lines and removes the
expiry.

**What to do instead.** After fixing a resolution bug, grep for the other readers of the same
structure before closing it — here, everything that iterates `population` and filters
`Load == "Merge"`. And test the *negative*: a check that passes on correct content proves nothing
until it has been seen to fail on incorrect content. Stripping the attribute and re-running took ten
seconds and is the only reason this was found before release rather than after.

## A recipe's cost is not the string I wrote, and its tier is not the field that names it

Two numbers govern a tinkering recipe, they are only loosely coupled, and both of them lie about
where they come from. Found while pricing the effect shells in #145, written down properly in #558
after #202 turned out to have the mechanism half right and the interesting half missing.

**Tier derives from the bits. `BuildTier` is only an override.** `TinkerItem.LoadBlueprint`:

```csharp
tinkerData.Cost = GetBitCostFor(Blueprint.Name);
int num = 0;
for (int i = 0; i < tinkerData.Cost.Length; i++)
    if (BitType.BitMap[tinkerData.Cost[i]].Level > num)
        num = BitType.BitMap[tinkerData.Cost[i]].Level;
tinkerData.Tier = part.GetParameter("BuildTier", num);
```

That tier is the whole skill gate, in `DataDisk.GetRequiredSkill` — `Tinker1` at 3 or below,
`Tinker2` at 6 or below, `Tinker3` above — and it weights disk placement through
`DataDisk.GetDataScore`. `BuildTier` is a real public field (`public int BuildTier = 1;`) that
**vanilla writes nowhere: zero occurrences against 332 `TinkerItem` records.** It is the lever for
decoupling what a recipe costs from when it unlocks, and this fork's effect shells use it —
`Bits="001" BuildTier="4"` puts them behind Tinker 2 on materials that alone would score tier 1.

**The digits are not bits, and they are redrawn every world.** A digit is a *level*, and
`BitType.ToRealBits` resolves it against `Stat.GetSeededRandomGenerator(Blueprint)`, which seeds on
`GetWorldSeed() + Blueprint`. So `0` becomes one of the four level-0 scraps, differently per
playthrough and stably within one. There is also a ~1% chance per digit to trade one level for an
extra bit, looping with a 10% continuation:

```csharp
while ((num > 0) & flag) { num--; num2++; if (random.Next(0, 101) <= 90) flag = false; }
```

**That path only ever splits downward** — one level-2 bit becomes two level-1s, then three level-0s.
Nothing anywhere combines upward into a higher tier, whatever the Steam threads say. The official
wiki's *Bits* page has this exactly right ("replace one or more of their advanced bits with two bits
of previous tiers... remain the same for the entire game"); it was secondhand advice that had it
backwards.

**`Bits` is a property, not the attribute.** Its getter returns the *resolved* cost out of
`BitCostMap`; the setter files what XML wrote into `BitSpecMap`. So the field never holds the string
in the blueprint, and `TinkerItem.Initialize`'s unrecognised-bit warning never fires on a digit — by
the time it reads `Bits`, the digits are already letters.

**The letters in XML are not the letters the game shows you.** This is the one that will bite
somebody. `BitType.TranslateBit` remaps every scrap character on the way to the screen:

| XML character | What it is | Displayed as | Wiki calls it |
|---|---|---|---|
| `R` | scrap power systems | A | `<A>` |
| `G` | scrap crystal | B | `<B>` |
| `B` | **scrap metal** | C | `<C>` |
| `C` | **scrap electronics** | D | `<D>` |

`B` and `C` are valid in both alphabets and mean different things in each. Write `Bits="B"` after
reading the wiki's `<B>` and you have asked for scrap metal while intending scrap crystal — and
nothing warns, because `B` *is* a real bit. The ten `Bits="BC"` records in
`mod/ObjectBlueprints/Ammo.xml` are Mura's, and they are safely inside the commented-out block from
#146, but they are what this trap looks like in the wild. Use digits unless there is a reason not to.

**The wiki's modding page is stale on precisely this field.** `Modding:Adding Code at Startup`, last
edited July 2024, still shows an instance `LoadBlueprint()` doing `tinkerData.Cost = this.Bits;
tinkerData.Tier = this.BuildTier;`. Both assignments are now wrong, and the second one inverts the
design: on that version tier came straight from `BuildTier`, which defaults to 1, so a modder
following the page concludes `BuildTier` is the only way to set a tier. It is the exception, not the
rule. Read `LoadBlueprint` in the assembly before trusting any account of it, this one included.

One last distinction, because the wiki prints both in the same infobox and they routinely disagree:
**an item's `Tier` is not its recipe's tier.** A nuclear cell is item tier 7 with `<006>`, which is
recipe tier 6, which is Tinker II — not the Tinker III its item tier would suggest.

## Before writing a name register, find out who would ever call for a name

#454 asked me to write naming registers for five peoples that draw Qudish. I nearly wrote five
phonologies. The measurement said write nothing for four of them, and that the fifth already
existed.

**Two things get a creature named, and both are gates.**

`EncountersAPI.GetALegendaryEligibleCreatureBlueprint` is one: `Creature` tag, `Render`, `Body` and
`Combat` parts, no `GivesRep`, no `Uplift`, not `ExcludeFromDynamicEncounters`, name without `Hero`,
and its **own** `BaseObject` tag absent. `VillageBase.getBaseVillager` is the other, feeding
`NameMaker.MakeName`; its first and third tiers both require
`DynamicObjectsTable:<region>_Creatures`, so a species with no region table is reachable only
through the rare middle fallback.

Applied to the five, counting blueprints that *resolve* to a species through `Inherits=` rather than
those that declare it:

| species | legendary draws | region table | verdict |
|---|---:|---|---|
| woodsprog | 6–7 | `Jungle_Creatures` | the only one in both paths |
| cragmensch | 6 | none | no dialogue anywhere to derive from |
| urshiib | 2 | none | 18 of 20 are hand-named Barathrumites |
| slynth | 1 | none | the best anchor in the set, and almost nobody to use it |
| baetyl | 0 | none | `InorganicObject` — a stone idol, not a people |

**Slynth is the one to remember.** It has 235 conversation lines, a named leader, and a speech
register nobody would have to invent. Exactly one blueprint would ever draw from it. That is
`docs/LESSONS.md`'s own *"a pool with no members can be live"* arriving from the other direction: not
a pool that draws nothing, but a pool nothing draws from.

**Then check whether the register already exists under a scope that does not reach.** Vanilla has a
`Naphtaali` namestyle — 22 prefixes, 21 infixes, 15 postfixes of Semitic register. The Naphtaali
*are* woodsprogs; `BaseNaphtaali` inherits `BaseWoodsprog`. What vanilla never wrote is a `Species`
scope, so a woodsprog outside the tribe fell through to Qudish while one inside it was named
correctly. Vanilla's own shape for a people with a faction is all three scopes — Snapjaw carries
Faction 100, Species 50, Culture 50 — and Naphtaali stops at two.

So the fix was **one scope, and no syllables at all**:

```xml
<namestyle Name="Naphtaali">
  <scopes>
    <scope Name="Vixy_Woodsprog" Species="woodsprog" Priority="50" Combine="true" />
  </scopes>
</namestyle>
```

> **A gap in generated names is more often a scope that does not reach than a register that does not
> exist.** Read the namestyle list for the *people* before deciding nobody wrote them one. I had
> already measured that woodsprogs draw Qudish and concluded the register was missing; both halves
> were true and the conclusion still did not follow.

Two things that made the difference, both cheap:

- **`Base="…"` looks like the clean answer and cannot be proven here.** A `Vixy_Woodsprog` style with
  `Base="Naphtaali"` delegates through `NameStyle.Generate` and avoids merging onto a vanilla record
  entirely, which is charter rule 1's preference. But `tools/naming_harness.py` records `style.base`
  and never follows it, so the fragment generated empty strings. That is a limitation of the harness,
  not of the game — and an unprovable change is not a shippable one, so the scope merge won.
- **Byte-identical output is the rule 1 proof.** `Faction=Naphtaali` at a fixed seed generates the
  same names before and after, which says the pools were added to and not replaced. Cheaper and more
  convincing than reading the loader again.

## `public` is an access modifier, not an extension point

#589 was planned as `Vixy_Fangs : Horns`, and the reasoning was sound. `Horns.RegrowHorns` is
variant-general — it reads the variant blueprint's `MeleeWeapon Slot`, finds that body part, creates
the object and equips it — so a fangs mutation could inherit the whole anatomy and regrowth machinery
and override only the four values that differ. Ten lines instead of sixty.

`Horns` declares all four in members that cannot be overridden:

```csharp
public int GetAV(int Level)                                          // not virtual
public string GetBaseDamage(int Level)                               // not virtual
public void RegrowHorns(bool Force = false)                          // not virtual
public override bool ChangeLevel(int NewLevel)                       // virtual - calls RegrowHorns()
public override void SetVariant(string Variant)                      // virtual - calls RegrowHorns()
public override bool HandleEvent(RegenerateDefaultEquipmentEvent E)  // virtual - calls RegrowHorns()
```

The three virtual methods are all reachable, and every one of them calls the non-virtual
`RegrowHorns`, which sets `MaxStrengthBonus = 100`, `BaseDamage = GetBaseDamage(Level)`,
`AV = GetAV(Level)` and force-equips the result — which is every one of the four things the subclass
existed to change. A subclass can override `ChangeLevel`, but `base.ChangeLevel(...)` runs the
parent's version, and C# has no `base.base`. No arrangement of overrides gets past it.

> **Before planning a subclass of a game type, read the modifiers on the members you intend to
> change — and on the ones that call them.** A class is extensible where it is virtual, not where it
> is public, and the second list is usually much shorter than the first.

One command answers it:

```bash
ilspycmd -t XRL.World.Parts.Mutation.Horns "$QUD/Managed/Assembly-CSharp.dll" \
  | grep -n 'public\|virtual\|override'
```

Two things worth carrying past the specific class.

**The member that blocked it was the one I had no intention of touching.** I read `GetAV` and
`GetBaseDamage` closely, because those were the numbers I wanted to change, and skimmed `RegrowHorns`
because I wanted to *keep* it. `RegrowHorns` is the one that decides the question: a non-virtual
method called from every virtual entry point seals a class as effectively as `sealed` would. **Check
the modifier on what you plan to inherit, not only on what you plan to replace.**

**The same read named the right parent.** `Beak` derives from `BaseDefaultEquipmentMutation` and does
all its work in `OnRegenerateDefaultEquipment`, which is virtual and is the only place it writes
anything — Face slot, `Part.DefaultBehavior` instead of force-equip, its own damage. That is the
pattern #589 wanted in the first place, arrived at from the other direction. So *"which of these can
I extend"* produced a better design than *"which of these is nearest"*, and it is worth asking in
that order. The 36 `ModImprovedMutationBase<T>` stubs in this fork work precisely because that base
was written to be extended; a vanilla gameplay class carries no such promise.

## A virtual method that ends in `base` is not an extension point either

The entry above settles the easy half: a member that is not virtual cannot be overridden, and reading
the modifiers answers it in one command. #570 hit the half that survives that check.

`GiveArtifact.HandleEvent(EnterElementEvent)` **is** virtual. It is also unusable as a parent, and for
a reason the modifiers do not show — its last line:

```csharp
public override bool HandleEvent(EnterElementEvent E)
{
    // ... pick an artifact from the player's inventory, remove it ...
    return base.HandleEvent(E);   // IConversationPart's, which advances the conversation
}
```

A subclass wanting to filter that picker must override the method and do its own picking. Then it
needs the conversation advanced, which is what vanilla's final line does — but from the subclass,
`base.HandleEvent(E)` reaches `GiveArtifact`, not `IConversationPart`, and re-runs the entire picker a
second time. C# has no `base.base`, so the tail call vanilla makes is the one call the subclass cannot
make.

**The counter-example is what makes this a rule rather than a refusal.** #605 needed the same shape
from `Garbage`, whose two rifle entry points are also virtual and also end in `base`. That subclass
was safe, because the grandparent those calls reach is a default in `IGameSystem`:

```csharp
public virtual bool HandleEvent(InventoryActionEvent E)
{
    return true;
}
```

A no-op. The subclass can override, do its own work, `return true`, and lose nothing — it has
replicated the grandparent exactly.

> **After confirming a method is virtual, read what its own `base` call reaches.** If the grandparent
> does real work, the subclass cannot get to it and the class is closed in practice. If the
> grandparent is a no-op returning a constant, overriding without calling base is complete and the
> subclass is safe.

So the test is not *"is this virtual"* but *"can I replicate what this method's tail call does"*. Two
classes with identical modifiers answered oppositely, one issue apart.

The fallback when the answer is no: derive from the grandparent instead and reuse the parent's static
helpers. `Vixy_GiveArtifact` would extend `IConversationPart` directly while calling
`GiveArtifact.IsArtifact`, which is `public static` — so the definition of *artifact* still comes from
vanilla and cannot drift, even though none of vanilla's code is inherited.

## A guard that hands back the cell it was avoiding

`PlaceObjectInArea` will not put a creature on top of another one. It filters the candidate set with
`workingSet.RemoveAll(p => Z.GetCell(p).HasCombatObject())`, and then, in case the fallback path
picked an occupied cell anyway, it checks again on the way out:

```csharp
else if (gameObject.IsCombatObject() && Z.GetCell(location2D).HasCombatObject())
    Z.GetCell(location2D).getClosestPassableCell().AddObject(gameObject);
```

**The second guard does nothing at all.** `getClosestPassableCell()` collects every `IsPassable()`
cell in the zone and sorts them by distance *from the cell it was called on* — and a cell is at
distance 0 from itself. So it returns that same cell, unless the cell is impassable. Creatures are
`Physics Solid="false"`, so an occupied cell is passable, so the object is added exactly where the
branch exists to prevent. Two crocs, one tile, which is how #613 was reported.

> **A fallback that searches "the closest X" will find the thing it started from, whenever the thing
> it started from is an X.** The guard reads as *move it somewhere else*; it is written as *find the
> nearest passable cell*, and the current cell qualifies. This is the same failure as `IsEmpty()` in
> the entry above — a helper whose name describes the intent while its body describes something
> broader — and it is worth noting that the two are in the same method, forty lines apart.

**None of it is this fork's to fix.** Reaching that line means Harmony or a replacement zone
builder, and charter rule 5 refuses the first while the second is a large new capability for
somebody else's defect. What this fork controls is *how often placement gets there*, and that turned
out to be the whole of our half: 30 creature variants were adding a second independent `Chance` roll
beside the animal they were a coat of, so a salt marsh expected twice vanilla's crocs and the
contested aquatic cells ran out twice as fast. `variant-density` checks that now.

**The reason I believed creatures were exempt is the part to carry.** I had read the first guard,
found it stronger than the plant one, and wrote the exemption into the entry above as a finding. It
was a true fact about a real line of code, and the conclusion still did not hold, because I stopped
at the first guard in a method that has two. **Reading one guard tells you what one guard does.**

## Vanilla builds mechanisms it never wires up, and the unused half is usually complete

Before designing a system, check whether Freehold already shipped one and left the data end
unconnected. It is not an occasional windfall — it is a habit, and looking first is cheap enough to be
a first move rather than a lucky one. Four verified cases, each failing in a different place:

**Data written that nothing parses.** `MerchantPersonalItem` appears on two `<inventoryobject>` nodes
in vanilla's `Creatures.xml`. The string appears **nowhere in the assembly**, and
`ParseInventoryObjectNode` reads a closed list of ten attributes that does not include it — so the
attribute is set, saved in the file, and dropped on load.

**A flag set at one end and read at neither.** `ActivatedAbilityEntry.Visible` is a public property
over `Flags` bit 2. It is serialised, compared in `SameAs`, and `Phasing` actively sets it — and
nothing displays it. `Sidebar`, `AbilityManager`, `AbilityNode` and `ActivatedAbilities` contain no
reference. The mutation is wired to a switch connected to nothing.

**A whole feature built and hidden.** `HiddenMutations.xml`, a file sitting beside `Mutations.xml`,
declares **48 complete mutations** — real classes, real art, real costs — under
`<mutations Hidden="true" ExcludeFromPool="true">`. None reaches character creation or the random
mutation pool. `Heightened Smell` among them is a finished mutation with terrain-attenuated detection
that this fork wanted and was about to write from scratch (#593).

**A part finished down to its player-facing text, on no blueprint.** `TrashOracle` exists to adjust
Trash Divining's chance — it guards on `E.Skill is Customs_TrashDivining`, carries `Bonus` and
`Magnitude`, and handles `GetShortDescriptionEvent` to write *"Chance to reveal secrets via Trash
Divining increased by 5%"* onto whatever item bears it. **No blueprint in the game carries it**, and
nothing constructs one. This is the most finished of the four: somebody wrote the rules text a player
would read. It settled #605 by proving the rate was adjustable through an event rather than by
patching `Garbage`, and its guard clause was copied verbatim as the intended idiom.

> **Look for the unwired mechanism before building a new one.** A decade of accretion leaves a lot of
> complete machinery behind a feature that shipped narrower than planned, and finding it turns a
> design problem into a wiring problem.

**The counterweight matters more than the instruction, and the third case demonstrates it.**
`HiddenMutations.xml` is not an oversight — `Hidden="true"` is *typed out*. Somebody decided those
mutations should not be selectable. **Unused is evidence that something was considered, not that it
was forgotten**, and the audit-first caution in #172 and #154 applies before assuming otherwise.
Finding the mechanism tells you the thing is *possible*; it says nothing about whether it is *wanted*.
That is why exposing one now takes a two-part test rather than a shrug — `docs/DESIGN_balance.md`
§10.4.

**An empty grep is the weakest evidence in this file, and it is the evidence this pattern invites.**
Name-string lookup and `ComponentReflection` both reach code that no call site names, `strings` cannot
see a .NET literal at all (see the entry above), and `AITonicUse` reads as unused on creatures only
because it lives on the tonics. Prefer a *positive* finding: `MerchantPersonalItem` is settled not by
its absence from the assembly but by `ParseInventoryObjectNode`'s attribute list being **closed and
enumerable**. Checking who reads a thing beats failing to find who reads it.

Both halves of this bit while writing this entry. The `FLAG_VISIBLE` row above came in as *"0
readers"*, which a grep appeared to confirm and which was wrong — the constant is unreferenced because
the code uses the literal `2`, while the flag behind it is read, written and compared. The row is
stronger once corrected, and it would have shipped false.

## A chance the game constrains to whole percents cannot be halved

`GetSkillEffectChanceEvent.GetFor` takes `ConstrainToPercentage` and it defaults **true**, so the
number every consumer receives is a whole percent. `Garbage.AttemptRifle` calls it that way, which
means Trash Divining's chance is an integer from 0 to 100 and there is no fractional value to hand
back.

That is easy to know and easy to forget one step later, while designing the curve rather than the
call. "Halve it each time" is the obvious shape for diminishing returns and it is what #605 proposed
in writing. From a base of 5 it produces **5, 2, 1, 0** — integer division truncating twice and then
reaching zero, which does not taper a bought skill so much as switch it off in any zone dense enough
to matter. The intended 5, 2.5, 1.25 cannot be said at all.

The fix is to state the bands as integers instead of deriving them, and to give the last one a floor:
5, 3, 2, 1, and 1 thereafter. That is more literal than a formula, and honest about the resolution
the engine actually offers.

> **When a rate is an integer, design the curve in integers.** A ratio written as a formula will be
> truncated somewhere you did not choose, and the place it lands on zero is rarely the place you
> would have picked.

The general shape is worth carrying past this instance: a curve is a claim about resolution as well
as about shape, and the resolution belongs to the engine rather than to the design. Check what the
consumer can represent *before* choosing how the value falls off — `ConstrainToPermillage` exists on
the same call for exactly this reason, and a caller that used it would have had ten times the room.

## A mod's reach ends where nothing in XML names the object

Charter rule 5 rules out Harmony and reflection, which makes *"can a mod reach this at all"* a real
question with a mechanical answer: **something in `Base/` has to name the type.** A blueprint part, a
mutation `Class`, a conversation part, a zone builder — all substitutable, because XML names them and
the game resolves that name. Nothing else is.

Two issues hit the wall from opposite directions.

**#585** wanted to dim older log messages. The markup work was done, the crux was settled, and the
approach worked — on the classic sidebar and on the Modern full-log screen. The Modern UI's *live*
log converts each message to RTF once on arrival and keeps it in `protected List<T> _scrollListData`
on a Unity component, behind a singleton. No XML anywhere names it. The only way in is reflection.

**#570** wanted the player's *important* mark to exclude an item from what a merchant will buy.
`TradeScreen` is `SingletonWindowBase<TradeScreen>` and the legacy `TradeUI` is
`IWantsTextConsoleInit`. Neither appears in any `Base/` XML file.

In both cases the unreachable thing was the *widest* part of the issue — selling is where a marked
item is most at risk, and the live log is the log most players read.

> **Ask whether the call site is named in XML before designing anything that has to reach it.** The
> answer is one grep, and it decides whether the issue is buildable before any of the interesting
> work starts.

The order is the whole lesson. In #570 the question came first and cost nothing; in #585 the design
was nearly complete when the wall turned up. Both issues were worth filing and the findings were worth
keeping — but one of them spent its budget before learning the thing that decided it.

**A useful corollary: reachability is not all-or-nothing, and the split is the finding.** #570 came
back with `GiveArtifact` and `RandomAltarBaetyl` reachable and both trade paths not, which turned a
systemic proposal into a small one rather than into nothing. Reporting *which half is reachable* is
more useful than reporting that the issue is blocked.

## A claim about what a player experiences needs a source, and I am not one

#609 opened: *"Walk through a village with a container set to auto-collect and you fill up from their
cistern without a prompt, a message, or a consequence."* First person, present tense, and it reads as
something I watched happen.

It is not. It came from an anti-exploit mod's feature list I read weeks earlier and thought was a good
idea. By the time it reached the tracker it had become a description of my own game.

Vanilla already handles it. `LiquidVolume.HandleEvent(AutoexploreObjectEvent)` refuses on
`!ParentObject.IsOwned()`, so an owned container never receives the `CollectLiquid` command.
`Village.cs` sets `Physics.Owner` to the village faction on every object tagged `Furniture` or
`Vessel` — and the next three lines fill those same vessels with the village's signature liquids, so
the pass is aimed at exactly the object the issue was about. Preset settlements carry ownership
hand-authored; Joppa's map has 28 objects owned by Joppa and its one vase among them.

The issue also had the mechanism backwards, which is the second cost. It named
`AllowLiquidCollectionEvent` as *"vanilla's 'you may not take this liquid' veto"*. It is asked of the
container **being filled**, and every implementer answers *is this liquid compatible with what I am*.
A destination filter, which never sees the source and could not have expressed *this belongs to the
village* however it was extended.

> **When an issue's premise comes from somewhere other than play, say so in the issue.** A feature
> another mod advertises is evidence about the version *it* targeted, and a fix Freehold has since
> shipped leaves the advertisement standing.

**The tell was in the issue from the start.** A behaviour described in the first person that nobody
has actually seen reads exactly like one that was, and nothing in the text marks the difference. This
one survived to the point of an assembly investigation before *"wait, when did this happen to me"*
got asked — and the answer, once asked, took one sentence.

Worth separating from a related and healthier case: an issue can be *filed* from a third-party
observation deliberately and usefully — #613's croc stacking arrived as a bug report and was real. The
failure here is not the source, it is the source going unrecorded until the premise had already been
spent on.

### The same failure with no third party involved, hours later

This entry was written scoped to issues taken from somebody else's mod. That scope was too narrow,
and #632 proved it the same day.

The argument for widening the Issachari name pools ran: an `IssachariParty` is 2d4 raiders plus
riflers, #572 made every creature askable, so **ask four people in one war party and two will open on
the same verb**. It went into the issue, into the pull request, and into `docs/FEATURES.md` §15.7.

The Issachari will not talk to you. `Factions.xml` gives them `InitialPlayerReputation="-475"`,
`REPUTATION_DISLIKED` is `-250`, so `Reputation.GetFeeling` returns `-50`, and
`Brain.GetFeelingLevel` calls anything below `-10` hostile. They attack instead. A question that
lives inside a conversation is worth nothing where there is no conversation.

Nobody handed me that premise. I generated it while arguing for work I wanted to do, and it was wrong
in the direction that made the case look stronger — which is the direction a premise of one's own
invention tends to fail in.

**What makes it worth adding rather than filing under the same heading.** The surrounding
investigation was careful: spawn tables measured, `Village.cs` read closely enough to correct an
earlier overreach about villages naming their inhabitants, `GivesRep` checked and found absent. Every
one of those was a question I thought to ask. *"Will they talk to me"* was not, and it was upstream of
all of them. One line in `Factions.xml`, in a file opened that same day for something else.

> **A statement about what a player will see is a claim, whoever made it.** It needs a source — a
> play session, or a line of data read for that purpose — and "it follows from the other things I
> just verified" is not one. Being the author of a premise is not evidence for it.

The practical form: when an argument for building something rests on a player doing X, find the thing
in the data that permits X before the argument is used. Reputation, hostility, gating flags and
prerequisites are all cheap to read and all sit upstream of the interesting mechanics — which is
exactly why they get skipped.

## Two liquid containers never stack, and no blueprint says so

`LiquidVolume.SameAs(IPart)` is `return false;`, unconditionally. `GameObject.SameAs` walks
`PartsList` and fails on the first part that says no, so **no two objects carrying a `LiquidVolume`
are ever `SameAs` each other** — two identical *empty* waterskins included. The only bypass is
`Stacker`'s `AlwaysStack` tag with a matching blueprint, and across the whole of `ObjectBlueprints/`
exactly five objects carry it: `Lead Slug`, `BaseArrow`, `HE Missile`, `Shotgun Shell`, `Bandage`.
No container. Belt and braces, `LiquidVolume.Attach()` sets
`FrameOffset = Stat.RandomCosmetic(0, 60)`, so every instance differs anyway.

I believed the opposite while writing #561, on the evidence that `PerformFill` wraps its work in
`RemoveOne()` and `CheckStack()`. That wrapper cannot fire on a container at all.

> **Stacking is decided by a `SameAs` override, which is a property of the part and not of the
> blueprint.** No amount of reading XML finds this. If a design rests on two things stacking, read
> `SameAs` on every part they carry before believing it.

## Before building something that gathers scattered resources, read the events that spend them

The premise of #561 was that water scattered across five waterskins is worth consolidating. It is
not, for currency: `GetFreeDramsEvent` sums `Volume` across every unsealed container holding the pure
liquid, `UseDramsEvent` drains them in sequence, and `TradeScreen`, `PlayerStatusBar` and
`WaterRitualBegin` all read `GetFreeDrams()`. **12 + 40 + 3 + 61 + 8 drams already spends exactly like
124.** `GiveDrams` is the same story from the other side — it requires `IsPureLiquid(Liquid) ||
IsEmpty()` before accepting a dram, so vanilla has never been able to contaminate a container by
paying you.

What survived was narrower and real: `GetStorableDramsEvent`, `GetAutoCollectDramsEvent` and
`GiveDrams` all gate on that same predicate, so a skin holding three drams of water cannot accept
honey at all. The feature is worth building for the container it frees, not the money it saves.

> **The scatter may already be cosmetic.** An aggregation feature is only worth its complexity if
> something downstream actually reads the pieces separately. Read the consumers first.

## A part on the actor can add an inventory action to somebody else's object

`GetInventoryActionsEvent` and `GetInventoryActionsAlwaysEvent` are both sent to the **object** only.
That makes a blueprint merge look like the only way to put an action on an item — and blueprint parts
are baked in at creation, so every object already in a save would silently never get it.

`OwnerGetInventoryActionsEvent` is the way past. `EquipmentAPI` fires it on the **actor**, alongside
the other two, for every item the actor looks at; `Telekinesis` and `Psychometry` both use it. Paired
with `AddAction(..., FireOnActor: true)` the same part handles the resulting command.

> **One part on the player, attached through the two `Vixy_PlayerParts` hooks, reaches every item in
> every existing save and needs no blueprint merges at all.** Reach for this before merging a part
> onto a family of blueprints.

## A part a blueprint inherits is not a part it declares

#640 was filed because three ways of counting the same thing disagreed: `Category="Meds"` held 3
blueprints, a `Medication` part filter found 2, and `Category="Tonics"` independently held 13. The
issue went up with a caveat saying nobody should act on it.

The filter was counting blueprints that write `<part Name="Medication" />` in their own record.
Tonics do not — they inherit it from a base. Resolving `Inherits=` first:

| Filter | Declared only | Resolved |
|---|---|---|
| `part Medication` | 2 | **13** |
| `part Tonic` | 3 | **13** |
| `Category="Tonics"` | 13 | **13** |

Category and part agree on all 13, in both directions. **The category was trustworthy the whole time
and the audit method was what was wrong** — worth separating from #172's `Clothes` false positive,
which really was a filing artefact.

> **A declared-part count is a lower bound**, and for anything with a `Base*` ancestor it can be off
> by most of the set. `parse → resolve Inherits → count` is the minimum before a number means
> anything.

## `*noinherit` and `*delete` are tag sentinels, not tag values

Writing the resolver for the entry above, every concrete item came back as an abstract base and every
count returned zero.

`PhysicalObject`, `InorganicObject` and `Item` each carry
`<tag Name="BaseObject" Value="*noinherit" />`. **`*noinherit` means the tag exists on the declaring
blueprint and does not pass to children** — so inheriting it naively marks all 4,642 concrete objects
as bases. **`*delete` means remove this inherited tag**; `Bandage` uses it to drop `Breakable`.
Across `ObjectBlueprints/` there are **957** `*noinherit` and **147** `*delete`.

- *"Is this a base object?"* is answered by whether the blueprint **declares** `BaseObject` in its own
  record, never by the resolved tag set.
- A resolved tag set that honours neither sentinel is wrong in both directions: it invents tags that
  were never inherited and keeps tags that were explicitly deleted.

> The failure is loud if you are lucky — every count is zero — and silent if you are not, as a tag
> filter quietly over-matches. Together with the two entries above and the `parse(lenient=True)` note,
> this is one sequence: **parse, resolve `Inherits`, honour the sentinels, then count.**

## Qud has no stealth system, so nothing can interact with one

Worth knowing before a design proposes light and shadow, or sneaking, and assumes there is something
to hook into. **There is no `Stealth` type anywhere in the assembly** — not a part, not a skill, not
an effect. Across all 7,073 types nothing matches.

Concealment is two unrelated things:

- **`Hidden`** — hidden *objects*: traps, secret doors, stashes. Detection is
  `Bonus + Random(1, Searcher.Intelligence) >= Difficulty`, fired from `Physics` as a `"Searched"`
  event. **Intelligence and nothing else** — the same roll #621 records upstream, where a default
  `Difficulty` of 15 means Intelligence 14 or below can never find a default hidden object.
- **Camouflage** — `FoliageCamouflage` and `UrbanCamouflage` behind `ICamouflage`, plus
  `ConcealedHologramMaterial`, which conceals but is *not* an `ICamouflage`. **None of the three
  contains a single light reference.**

The only light term anywhere in concealment is one line, identical in `Hidden`, `HiddenRender` and
`EelSpawn`:

```csharp
if (!Found && E.GetParameter("RenderEvent") is RenderEvent renderEvent
    && (renderEvent.Lit == LightLevel.Radar || renderEvent.Lit == LightLevel.LitRadar))
{
    Found = true;
}
```

That is penetrating radar **defeating** concealment — a vision mode revealing what is hidden. It runs
in the opposite direction from *"darkness helps you hide"*, and ambient light never enters it.

> **Ambient light has no bearing on being seen or hiding, in either direction.** Darkness does not
> conceal you and light does not expose you. Anything proposing a light-and-shadow interaction is
> building the stealth system *and* the coupling from nothing, not extending either.

What light does gate is targeting and information: `PickTarget` refuses unlit cells, `MissileWeapon`
will not fire at one, and the sense effects render only cells that are `IsLit() && IsExplored()`. No
combat penalty, no AI penalty.

## The `Tier` tag is what an item costs to make, not when a player meets it

A third trap in the same family as *"a part a blueprint inherits is not a part it declares"* and the
tag sentinels. The tag is present, numeric, and read correctly — and the conclusion is still wrong,
because the **population tables** decide when an item is encountered and they are an independent fact.

#578 was filed on *"the face slot is dead until tier 3"*, measured off the `Tier` tag. The tables
disagree:

| item | `Tier` tag | drops from | draw chance |
|---|---|---|---|
| Vinewood Sap Mask | 3 | `Armor 1C` — tier-1 **common** | 3.5% |
| Goggles | 2 | `Armor 1R` — tier-1 **rare** | 10.0% |
| Issachari Sun Veil | 1 | `Armor 2C`, `Armor 3C` — **no** tier-1 table | 9.1% |

Both of the slot's signature utilities are already in the tier-1 tables, and the item *tagged* tier 1
is the one that never appears there. The gap the issue was named for was substantially not real.

**It is not a one-off, and the shape differs by table kind.** Across every
`Armor|Melee Weapon|Missile Weapon <N><C|R>` table, 238 entries carry a numeric `Tier` tag and **85 of
them — 36% — disagree with their table's tier**:

| table kind | n | agrees with table tier | spread |
|---|---|---|---|
| `NC` (common) | 81 | **86%** | −2 … +2 |
| `NR` (rare) | 157 | **53%** | −3 … +2 |

> **`Armor NC` is a fair proxy for tier N. `Armor NR` is not** — a rare table agrees with its own
> number barely half the time and stocks items up to two tiers above it. `Strength Exo`, `Thermo Cask`
> and `Gas Tumbler` are all `Tier` 6 in `Armor 4R`; five `Tier` 7 items sit in `Armor 5R`.

**Not the same as the `Tier`-fallback entry above.** That one — *"a property the game derives is not
the tag you can grep for"* — is about reading the field *correctly*, since `Tier` falls back to
`Level / 5 + 1` when absent. Here the field is read correctly and the inference from it is what
fails. The two are easy to conflate and only one is about grepping the right thing.

## A mechanism existing is not a mechanism working — check the values moving through it

I made this mistake four times in one session, in four disguises. The fourth is last because
it got furthest — it survived into a recommendation, and Grey disproved it herself:

| where | what I confirmed | what I skipped | what it cost |
|---|---|---|---|
| #591 | `Quadruped` has no `Hand` or `Body` slot, so a saltback cannot use tier-1 gear | what is actually *in* `Armor 1C` — about 28% of it (caps, moccasins, masks, shawls) equips fine on a quadruped | called a harmless quirk "clearly wrong" and nearly filed an upstream report |
| #635 | `IBaseJournalEntry.Attributes` exists, all three note kinds populate it, `TryGetAttribute` reads it | what the *values* are — `SecretAttributes` is on 7 blueprints, and the fallback yields 197 near-unique strings | recommended attribute-scoping in a posted comment, then had to withdraw it |
| #568 | `Temporary.CarryOver` exists, with twelve precedents and exactly the right semantics | the *ordering* in `PerformPreserve` — `go.Obliterate()` runs before the product is created, so there is nothing to carry over from | nearly published "propagation, not refusal" as settled, when propagation is unreachable from a mod |
| #591 *(again)* | the arrow ladder runs `StrengthPenetration` 2 → 9, Wooden to Zetachrome | that `Stat.RollDamagePenetrations` takes it as **`MaxBonus`**, not a bonus — and the bonus itself exists only when the *bow* declares `ProjectilePenetrationStat`, which `Short Bow` does not | recommended "Short Bow + Steel Arrows", a kit whose penetration is **0** with every arrow in the game |

> **The shape is always the same:** find the mechanism, confirm it is real, and infer from its
> existence that it does the job. What gets skipped is the data or the ordering flowing through it,
> which is where the answer actually lives.

This is a sibling of *"count the consumers before you count anything else"* and *"an empty grep is
only evidence if the grep could have found the thing"*. Those say **check the far end of a
reference**. This one says **check the values moving through it** — and knowing the first two did not
stop me doing this, which is why it is written separately.

## Check what this fork already did before investigating what vanilla does

Four separate investigations ended with *the answer is already in the repository*, and in each one I
went to the decompiled assembly first and found the repo's own answer last:

| where | what I did | where the answer already was |
|---|---|---|
| #636 | audited vanilla's shield tiers and derived a −1 offset correcting at fullerite | `docs/STYLEGUIDE.md` §3.2 states the tier→material scale, `mod/ObjectBlueprints/Armor.xml` merges vanilla's steel and carbide armour onto it, and §3.2.1 already describes the same seam as an AV rule. `item-curve` fails CI if it drifts |
| #605 | recommended the density fix four times, twice in posted comments | `mod/Scripting/Vixy_TrashMemory.cs`, wired in `Vixy_PlayerParts`, documented as `docs/FEATURES.md` §25, in `CHANGELOG.md`, and the issue closed as completed. It shipped in 2.9.0 |
| #630 | traced turret ammunition through `MagazineAmmoLoader` and got it wrong | the comment at `mod/ObjectBlueprints/Ammo.xml:34` had the answer, ending *"Confirmed in game, not just read."* |
| #690 | decompiled `RTF.FormatToRTF` to work out why option help text runs off the screen, and drew the wrong conclusion | `CHANGELOG.md` records #271 fixing the identical symptom — *"squashed into a thin box running off the bottom of the screen"* — and already states the number that settles it: vanilla's longest help text is 352 characters |

> **The fork has already thought about more of vanilla than its own issues assume.** `AGENTS.md` says
> to verify claims about Qud against the game's own files. That is right, and it is not the first step.
> The first step is `docs/STYLEGUIDE.md`, `docs/FEATURES.md`, `CHANGELOG.md` and `mod/` — because a
> question worth filing an issue about is one I have often already answered, and the answer there is
> both cheaper to find and more likely to be current than anything re-derived from the assembly.

The sharpest version: **`grep mod/` before `ilspycmd`.** Three of eight investigations in one session
would have started in the right place, and two public comments would not have recommended work that
had already shipped.

The fourth row is the one that should sting, because the repository was not merely *consistent* with
the answer — it had **fixed this exact bug before**, described the symptom in the words the report
would later use, and written down the measurement that decides it. A `git log -S` or a `grep -i
"help text" CHANGELOG.md` costs seconds. I spent an afternoon and shipped a regression instead.
A bug that recurs has a changelog entry; that entry is the cheapest source there is.

This is distinct from the entry above. That one is about not trusting a mechanism you have only
half-read; this one is about not opening it until you have checked whether the question is still live.

## When a measurement says it cannot be done, check it measured the field the feature would use

The near-inverse of the entry above, and it cost a feature that was buildable.

#635 asked whether a secret could be scoped to the region a player is standing in. I measured the
zone's `SecretAttributes` tag and its fallback, found **197 near-unique identifiers** like
`lakehinnom c`, and concluded that nothing describes a zone in a vocabulary the notes could share. The
measurement was correct. The field was wrong.

`Zone.GetRegion()` → `ZoneManager.GetRegionForZone` reads the **`Terrain` tag** on the same blueprint —
a curated **20-value** vocabulary covering **299 of 318** world-map terrains. Two fields describe the
same zone; one is an identifier with the serial number filed off, the other is the category. I measured
the identifier and wrote "Qud's data cannot express this" on the strength of it.

> **A negative result is a claim about the thing you measured, not about the thing you wanted.** Before
> recording *"the data does not support this"*, name the field the feature would actually read and
> check you measured that one.

(The conclusion survived on a different objection — two of the three note kinds carry no location at
all — but the reasoning in the thread was wrong for two rounds before anyone noticed.)

## A destructive-looking branch may be unreachable, and the reason can be an argument three frames up

`IntegratedWeaponHosts.GenerateTurret` reads as a two-way split, with `weapon.Obliterate()` on one
side. #630 was filed on that reading: *deploying a turret destroys your weapon for seven weapon types.*

It is not a split. The eighth argument to `GameObject.Create` is `ProvideInventory`, and
`ProcessSpecification` matches a supplied object by blueprint, uses it instead of creating a fresh one,
and **removes it from the list**. So the list is empty by the time the branch is tested, and the
`Obliterate` never runs. What guarantees it is `RemoveOne()` in `Tinkering_DeployTurret` — a different
file, three frames up, making `Count == 1` and therefore making consumption certain.

> **Reading the method was not enough.** The answer was in what the caller passed. A branch that looks
> destructive is worth tracing from its callers before it is worth filing.

Sibling of the values-versus-mechanism entry rather than a copy: there the trap is not reading far
enough *into* a mechanism, here it is not reading far enough *out* of one.

## A memoised name that is never invalidated, and is not serialised either

`CookingRecipe.GetDisplayName()` builds its string once and caches it in `CachedDisplayName`. Nothing
in the class ever resets that field, it is **private**, and `Write`/`Read` do not serialise it — they
cover `Hidden`, `Favorite`, `DisplayName`, `ChefName`, `Components`, `Effects` and `Tile`.

So changing a recipe's `DisplayName` in place **shows the old name for the rest of the session and then
silently starts working after a save and reload.** That is close to the worst shape a bug can have: it
looks fixed the next time you sit down, so the report gets closed as unreproducible.

`DeepCopy()` is the legitimate way around it — `Activator.CreateInstance` plus a field-by-field copy
that omits the cache, so the copy renders from scratch. Reaching the private field instead would be
reflection, which charter rule 5 refuses.

> **Before writing to a field that feeds a cached getter, check whether the cache has an invalidator
> and whether it survives a save.** If it is private and unserialised, the bug you ship is one that
> disappears when anyone tries to reproduce it.

## `KnowsRecipe` compares by display name, not by identity

```csharp
knownRecipies.Any(i => newRecipe != null && i != null && newRecipe.GetDisplayName() == i.GetDisplayName())
```

Two recipes that read alike **are one recipe** as far as the game is concerned. Anything that lets a
player name or rename a recipe has to refuse a collision, or it silently merges two dishes. Worth
knowing before designing naming for anything that is identified by its own display string.

## Qud has a temporariness convention, and two designed escape hatches

Before claiming a hole where a temporary item might yield permanent value, look for the convention.
It is applied at fourteen sites and has two opt-outs: `CanCookTemporary` on cooking ingredients and
`AllowTemporary` on conversation item checks.

The inventory, from the #597 audit: `Nectar_Tonic_Applicator:41`,
`Campfire.IsValidCookingIngredient:572`, `Campfire` preserve lists (`:232`, `:233`, `:627`, `:659`,
`:665`), `Butcherable:132`, `Harvestable:277`, `CyberneticsButcherableCybernetic:146`,
`Disassembly:244`/`:269`/`:580`, `HaveItem`/`TakeItem`, `CyberneticsScreenInstall:59`,
`ItemNaming:60`, `MapReveal:46`, `FactionDeed:81`, `LiquidCloning.SmearOn:92`, `ModQuantumReverb:98`,
`Stacker:340`.

Three supporting facts, each of which cost a decompiling pass:

- `MakeTemporaryEvent` is `[GameEvent(Cascade = 271)]` — `CASCADE_ALL` (15) plus
  `CASCADE_DESIRED_OBJECT` (256) — so a clone's whole pack really is marked.
- Non-root objects get `Duration = -1` plus `ExistenceSupport.SupportedBy`, so pack items have no
  clock of their own and expire with their supporter *wherever they have got to*.
- `Temporary.Duration` is the live counter, decremented in place, so `CarryOver` passes on the
  remaining time and never a fresh allotment.

There are three distinct refusal wordings, chosen by context, and it is worth not inventing a fourth:
*"The experience is fleeting."*, *"The parts crumble into dust."*, and *"…behaving as nothing more
than an ordinary piece of paper."*

## `Load="Merge"` against a DLC blueprint fails for players without the DLC

`ObjectBlueprintLoader.cs:797`: a `Load="Merge"` naming a blueprint that is not loaded calls
`handleError` and discards the node. **`Load="MergeIfExists"` skips silently instead**, and is the
correct form for anything under `CoQ_Data/StreamingAssets/DLC/`.

> **But `check_merge_discipline` tests `el.get("Load") != "Merge"` exactly**, so `MergeIfExists` fails
> this repository's own validator today. Anything touching DLC content has to teach the check about
> it first. Worth knowing before discovering it mid-pull-request.

## Two manifest features can be mutually exclusive, and the failure is silence

`GeneralAskName` gates a complete conversation feature, appears nowhere in the game's data, and
`GetBoolSetting` returns false for a key it cannot find — so a mod is the only thing that could ever
switch it on. `LoadGlobalConfig` ends with the call that would let one:

```csharp
ModManager.ForEachFile("GlobalConfig.json", delegate(string fileName) { ... });
```

That call takes `Recursive`, defaulted to **false**, which matches on `ModFile.RelativeName` — the
path relative to the mod root. So the file has to sit at the mod root to be found.

**And this mod has no reachable root.** `ModInfo.InitializeFiles` walks the whole mod only when
`manifest.json` declares no `Directories`; otherwise it enumerates the declared paths and nothing
else, so a root file is never registered at all. Declaring the root as a path does not rescue it,
because the rack de-duplicates by containment — the root contains every other entry, so adding it
removes them all and enumerates everything underneath, including the directory gated behind
`"Options": "OptionQudExpandedCEJoppaBuilding==Yes"`. Reaching the setting would have cost a shipped
option its meaning.

Both features are documented. Neither mentions the other. The interaction is visible only by reading
`ModInfo`, and #651 asks upstream for the one-argument fix.

> **A mod's own manifest can put a game feature out of reach, and nothing reports it.** Before
> designing against a mechanism that reads from a mod, check that this mod's file layout is one the
> mechanism can see.

**What actually caught it was a check written for something else.** I had already designed the
feature, written `mod/GlobalConfig.json`, and was on my way to the docs when `validate_mod.py`'s
`directory-coverage` refused the commit: *"under mod/ but no declared path reaches it — it ships to
subscribers and is never loaded."* That check exists to stop dead weight shipping to subscribers, not
to catch this; it happened to state the exact fact that mattered.

Which is the counterweight to the two entries above about checks with blind spots. **A check aimed
at one thing will occasionally catch another**, and the reason it can is that it asserts something
true about the world rather than something true about the change. `directory-coverage` does not know
what `GlobalConfig.json` is for. It knows which files the game will read, and that was enough.

The workaround, recorded because the shape recurs: when the switch is unreachable, look at whether
the thing behind it can be declared directly. `AskName`'s choice, response node and part are all
public and mergeable, so #572 shipped its own choice targeting vanilla's own `TellName` node — more
code than setting a flag, and it left the Joppa option alone.

## A decompiled call site tells you what that frame does not do, never what happens instead

Option help text was rendering squashed into a narrow box with the ends of the lines off the side of
the screen. I traced it and found what looked like a clean answer:

- `XmlDataHelper.GetTextNode` normalises with `TrimSpacePerLine` and `TrimNewlineRegex`, so per-line
  indentation and surrounding blank lines go and **internal newlines survive**.
- `Qud.UI.OptionsRow` calls `RTF.FormatToRTF(data.HelpText)`, and `blockWrap` defaults to `-1`, so
  **`BlockWrap` never runs**.

Both of those are true, and I checked both. Then I concluded *therefore the container wraps instead*
and unwrapped all twenty-one help texts onto one line per paragraph — which is the one shape that
guarantees the symptom, because a 400-character line has nothing left to break it.

Nothing I read said the container wraps. I had established that one specific function declines to
wrap, and filled the hole where the actual layout lives with the most convenient possibility. The
evidence was entirely negative and I spent it as though it were positive.

> **Verifying that a function is not responsible is not the same as finding what is.** A call site
> that hands off to Unity, to a coroutine, to a layout pass, or to anything else outside the assembly
> ends the trace — it does not continue it. When the next frame is somewhere the decompiler cannot
> follow, say *"I do not know what wraps this"* and go measure, because the alternative is an
> assumption wearing a citation's clothes.

**The measurement was one command.** Vanilla ships four options with help text: 157 to 352
characters, longest source line 162, shortest 80. Parsing its `Options.xml` answers *what fits* in a
way no amount of reading `OptionsRow` can, because it is the game's own working example rather than a
derivation from it. `helptext-shape` now enforces those two numbers.

Related: [`Vanilla builds mechanisms it never wires up`](#vanilla-builds-mechanisms-it-never-wires-up-and-the-unused-half-is-usually-complete)
is the same organ read the other way round — there, code that looks dead is live; here, a conclusion
that looks derived is guessed. And this is the third mechanism in one session that I read out of the
assembly and had contradicted by a `tools/sync_mod.py --dev` pass, which is the whole argument of
[`A claim about what a player experiences needs a source, and I am not one`](#a-claim-about-what-a-player-experiences-needs-a-source-and-i-am-not-one).
The dev pass is not a formality before merge. It is the only step in the process that can tell me my
reading was wrong.

## My design docs assume Qud has less than it does, and the error is always optimistic

Seven claims across four design documents have now failed against the assembly, and they fail in the
same direction every time:

| document | claim | what ships |
|---|---|---|
| `DESIGN_difficulty_systems.md` §B1 | nothing in the game charges you for time | it does, and the currency is water — `RegenCounter` spends it while you wait (#674) |
| `DESIGN_difficulty_systems.md` §B3 | Freehold cut survival attrition deliberately | `Stomach` runs a complete water system. `WATER_MINIMUM` is 0, so reaching zero locks out natural healing and then takes 2 hit points on a natural 1 of `1d(Toughness)` per heal tick — on the order of 2 HP per hundred actions, not per action (#705) |
| `DESIGN_difficulty_systems.md` §B4 | medium effort, Harmony maybe | `Broken`, `Tinkering_Repair` and per-use breakage in `ChargeUsedEvent` all ship. The mechanic is a new *trigger*, not a new system |
| `DESIGN_sleep.md` §1 | Qud has no hunger and no thirst attrition | both exist and thirst kills. `Famished` is −10 Quickness at 2,400 actions |
| `DESIGN_sleep.md` §7 | `Asleep` and `Wakeful` need verifying before coding | both resolve as *already satisfied*: `Wakeful` refuses only the involuntary events, and `Asleep.Voluntary` is set correctly at all ten call sites |
| `API_VERIFICATION.md` | a kinship registry exists to read | three markers, all on the NPC, none enumerable (#182) |
| `recon-findings.md` | the spice tree needs a code hook to mutate | `HistoricSpice.Init` merges a mod's `historyspice.json` already (#178, #689) |

> **Every error is optimistic in the same direction: a mechanism read as absent when it ships, or a
> cost priced as new work when the state and the hook already exist.** That is the opposite of the
> traps elsewhere in this file, which are all about misreading *the game*. This is about misreading
> *my own scoping* — and it is the more expensive kind, because it decides whether a thing gets built
> at all rather than how.

**One of the rows above broke that rule, and it was the correction rather than the claim** (#705).
The §B3 row originally ended *"and adds 2 hit points of penalty every action"* — a figure written
into this table *while recording the correction*, carried from there into `DESIGN_sleep.md` §1 and
`DESIGN_difficulty_systems.md` §B3, and wrong by about ninetyfold. It **overstates** what Qud does,
which is the one direction this entry says the errors never run.

Two things follow, and the second is the one worth keeping:

- A directional bias is a thing to notice, never a thing to lean on. The moment "my errors all run
  one way" becomes a reason not to check the other way, it has stopped being an observation.
- **The correction is not safer than the claim.** Both are prose about the assembly and neither has
  a test; a figure written in the confident afterglow of having just been right is if anything the
  more dangerous of the two, because nobody re-reads it. This row was copied into two more documents
  before anyone did.

**A design document's cost estimate is a claim about the assembly, and it ages exactly as badly as
any other claim about the assembly.** It looks like a judgement, which is why it never gets checked;
it is actually an assertion that a hook does not exist, and that is falsifiable in one grep. §B4 was
priced at *medium effort, Harmony maybe* on the strength of nobody having looked for `Broken`.

**The correction usually strengthens the argument rather than weakening it**, which is the part I did
not expect. `DESIGN_sleep.md` opened by conceding that Qud rejects survival timers and that the mod
therefore swims against the design. It does not — Qud runs two, tuned so they almost never fire, and
a sleep timer is a third one in that company rather than a foreign body. The honest premise was the
better premise, and the document had been arguing uphill against a fact that was not true.

Related: [`Check what this fork already did before investigating what vanilla does`](#check-what-this-fork-already-did-before-investigating-what-vanilla-does)
is the same failure aimed at the repository instead of at the assembly, and
[`A decompiled call site tells you what that frame does not do, never what happens instead`](#a-decompiled-call-site-tells-you-what-that-frame-does-not-do-never-what-happens-instead)
is what happens when the check is run but the conclusion overreaches. All three are cheaper to catch
before the design than after.

## A capped listing answers a smaller question, and nothing in the output says so

`gh project item-list 1 --owner "@me" --limit N` returns the first N items and stops. There is no
truncation marker, no warning on stderr, and the exit status is 0. The board crossed 200 items during
August 2026 and held **247** on the 30th, so a `--limit 200` dump I was reading columns out of had
already run off the end before it reached Todo.

Todo came back as 13 rows. It has 22. **#193, #580, #583, #588, #595, #596, #633, #634 and #691 were
simply not in the output**, and I went on to recommend two promotions from what was left — while #595,
which on a full read is one of the two strongest candidates in the whole column, sat in the nine that
had been cut.

The tell was there and I walked past it: an On Deck column of ten against a Todo of thirteen is not a
plausible backlog for this fork, and I had just spent an hour establishing how much work is queued.
A number that disagrees with what you already know is worth more than a number that merely looks
tidy.

> **This is the [empty-search trap](#a-search-that-finds-nothing-has-two-explanations-and-one-of-them-is-the-search)
> one step further on, and it hides better.** Zero results feel like something went wrong, so they at
> least invite a second look. Thirteen plausible rows feel like an answer. A capped listing does not
> report a partial world; it reports a smaller one, in the same shape a complete answer would take.

The general form: **a limit is a silent filter, and every listing command has one whether you passed
it or not.** `gh` defaults to 30 items on most subcommands, and the flag that raises it does not
announce when it is still binding.

**What actually catches it.** Not raising the limit — I raised it from 100 to 200 and was still
wrong. Cross-check the listing against a source that counts differently:

```bash
comm -23 <(gh issue list --state open --limit 200 --json number --jq '.[].number' | sort -n) \
         <(gh project item-list 1 --owner "@me" --format json --limit 300 \
           | jq -r '.items[].content.number' | sort -n)
```

Empty output means every open issue is on the board. It also fails loudly the moment the board dump
is short, because the missing rows show up as differences. That one line is what I should have run
before reading any column, and it is now how I check the board is fully loaded before trusting a
count off it. Dump once to a file and query the file repeatedly, rather than re-running the command
at different limits and comparing impressions.

Related: [`A search that finds nothing has two explanations, and one of them is the search`](#a-search-that-finds-nothing-has-two-explanations-and-one-of-them-is-the-search)
is the zero-result version of the same failure, and
[`"Could not determine" is not a pass`](#could-not-determine-is-not-a-pass) is the third member of the
family — in all three a tool declines to answer the question and the silence gets read as the answer.

## A guard on a collection nothing fills is not a budget

`Zone.GetSuspendability` tests `The.ZoneManager.PinnedZones.Count > 3`, logs an exception and clears
the list. I read that as an engine cap of three concurrently pinned zones, wrote it into a comment on
#583 as *"the constraint that should replace the one in the body"*, and built a scheduling argument on
top of it.

`PinnedZones` has **exactly one writer in the whole assembly** — `ZoneManager.cs:647`, inside the save
loader, reading back what `:483` wrote. Nothing at runtime ever adds to it. The list is empty in every
session, the `> 3` guard cannot fire, and the `Suspendability.Pinned` return behind it is unreachable.
The pin vanilla actually uses is `GetZoneSuspendabilityEvent`, which has no cap at all.

> **A limit is only a limit if something can reach it.** Before quoting a guard as a constraint, count
> the writers of the thing it guards. `Count > N` is evidence about what the author considered
> reasonable; it is never evidence that anything is bounded.

The nearest neighbours here are [`a scope that looks load-bearing may match nothing at all`](#a-scope-that-looks-load-bearing-may-match-nothing-at-all)
and [`a knob that accepts your value and rounds it away is worse than no knob`](#a-knob-that-accepts-your-value-and-rounds-it-away-is-worse-than-no-knob),
both of which are a declaration with nothing on the other end. This is the same disease in a **guard**,
which is worse, because a guard reads as enforcement rather than as data — I would have checked a tag's
consumers and did not think to check a bounds check's.

Worth keeping the useful half: the dead guard is still real evidence about intent. Three is what
Freehold thought reasonable. That is a design opinion to adopt, not a limit to rely on.

## A dead store looks exactly like a cache

`AIWorldMapTravel.GetTravelSegments()` does the terrain lookup, caches the result in `TravelSegments`
— and then `return 1000;`. The field is `[NonSerialized] private` and is read nowhere in the class.
Travel is therefore a flat 100 turns per parasang, terrain-blind, where the discarded value would have
been 300 to 1,200.

What makes this an entry rather than a shrug is **where the eye stops**. The body is four lines of
correct, plausible caching, so reading the top of the method confirms the behaviour you expected and
the tail is one word you have already stopped looking at.

> **When a method computes a value you are about to rely on, check that the value reaches the return.**
> A private field written and never read means the computation is decoration.

Every other habit in this file points at reading *more* of a method — [`read the whole loop before modelling it`](#read-the-whole-loop-before-modelling-it-this-one-decays-its-own-bonus)
among them. This is the case where the interesting line is the last one. It is a sibling of
[`an effect that reports nothing is not an effect that did nothing`](#an-effect-that-reports-nothing-is-not-an-effect-that-did-nothing)
rather than a duplicate: there the mechanism ran on wrong data; here it computes the right answer and
throws it away.

## You can keep an actor running off-screen, and you cannot start one there

Two registrations decide whether something acts while the player is elsewhere. They have different
gates, and the difference decides what an off-screen event can be:

| | gate to join | gate to stay |
|---|---|---|
| **Acting** — a `Brain`, goals, `AIBoredEvent` | `AddActiveObject` (`ActionManager.cs:317`) refuses unless the zone is cached, null, or the active one | `ValidateActor` (`:689`) evicts only when the zone is **not cached**, not when it is merely inactive |
| **Ticking** — `WantTurnTick` / `TurnTick` | `MakeLive()`, called by `ActivateObjects` on activation and by `Cell.AddObject` only when the zone `IsActive()` — **but the method is public and ungated** | `ShouldRemove` (`:430`) drops the object when its zone is `Suspended` |

`AllowCachedTurns` has one writer in the assembly, `ReclamationSystem`, and is false otherwise. So an
actor enqueued while its zone was active keeps taking full turns indefinitely — which is how
`OthoWander1` walks to Omonporch, by pinning its zone so it is never dropped — while an actor created
in a zone the player has never entered **cannot join the queue at all**.

> **An event whose actor must be created off-screen has to be `TurnTick`-driven, and its spawner has
> to call `MakeLive()` by hand.** Only an event that continues an *existing* actor can use a brain.

That is what `AIWorldMapTravel`'s docstring — *"Ideally this would be possible with a separate action
queue/non-zone world map"* — is apologising for, and why that part does its work in `TurnTick` rather
than through the `Brain` it sits beside.

## When a count supports a claim, resolve it — and read the difference before the total

This file already says a declared-part count is a lower bound. I wrote that entry. Then, across three
investigations in two days:

| where | declared | resolved | what was in the gap |
|---|---:|---:|---|
| `DromadCaravan` (#583) | 9 | **11** | **`Tam`** — Joppa's merchant. *"Add the travel part to the carrier"* would have walked him out of the starting village |
| `AddsRep` (#596) | 37 | **48** | the five fungal infections, which turned *"the only two-sided trade"* into a whole item family — the strongest precedent that issue has |
| `GivesRep` (#188) | 44 | **57** | the blueprints carrying the part whose generated relations were the finding |

> **In every case the gap was not noise, it was the answer.** The inherited members are not a rounding
> error on a count; they are systematically the interesting ones, because a part worth putting on a
> base is a part that governs a family.

A third instance in two days is where *"be more careful"* has demonstrably stopped working, which is
why #702 exists: `tools/validate_mod.py` walks `Inherits` by hand in five places and imports the
tested `BlueprintIndex` in none of them.

## A mod's faction data is live when it adds and permanent when it removes

**Factions are save state.** `XRLGame.cs:2318` calls `Factions.Save`, which writes the whole
`FactionTable` as composites, `Faction.Write` included. `Factions.Load` clears the table and rebuilds
every faction from the save — **and then re-reads the XML**, which is the part that inverts the obvious
conclusion:

```csharp
public static void Load(SerializationReader Reader)
{
    FactionTable.Clear();
    // ... rebuild every faction from the save ...
    Loading.LoadTask("Loading Factions.xml", LoadXml, showToUser: false);
    InitAttitudes();
}
```

`LoadFactionNode` then treats vanilla and mods differently on that pass: an existing **vanilla** entry
is skipped, a **mod's** is merged, and a faction only a mod declares is created. Feelings land through
`TryAddFactionFeeling` → `FactionFeeling.TryAdd`, which is add-if-absent.

> **The asymmetry is the lesson.** Mod faction data is **live in the additive direction** — new
> factions and new feelings reach a character created before the mod was installed, on the next load.
> It is **permanent in the subtractive direction**: once an edge exists and the game has saved, it is
> in the save's own copy, and deleting it from the XML does nothing. Turning the option off leaves
> every edge it ever created.

That is a **one-way edit**, and a fourth off-switch scope — neither live, nor restart-scoped, nor
new-character-scoped, but *additive-live and subtractive-never*. Any feature built on faction edges
has to say so in its `<helptext>` the way the Chip Interface option does.

This is [`read the whole loop before modelling it`](#read-the-whole-loop-before-modelling-it-this-one-decays-its-own-bonus)
applied to a method rather than a loop, and the tell was available: a `Load` that only restored would
have no reason to exist separately from `Init`.

## `CanChangeMovementModeEvent.To` is a message name, not a mode

The natural way to stop a burdened character running is to refuse `CanChangeMovementModeEvent`, the way
vanilla's `Overburdened` refuses flight. **It does not work, and it fails silently.**

`To` carries the movement **message name** rather than a mode identifier, and `Run` passes its own
`ActiveEffectMessageName` — a field set from `EffectMessageName`, configurable per `Run` part. So a
handler matching `"Running"` never fires, and the restriction ships inert with nothing to notice it.
`Vixy_Burdened` vetoes the `ApplyRunning` string event instead, and records the rejected route in its
docstring.

> **Before matching on an event's string field, find where the string is set.** A field named for what
> it selects is not necessarily populated with an identifier — this one carries display text, and
> display text is configurable.

The general form is [`a boolean's name is not its semantics, and neither is a skill's`](#a-booleans-name-is-not-its-semantics-and-neither-is-a-skills).
`docs/STYLEGUIDE.md` §3.4 has the refusal idiom that this is the trap in.

## A dispatch list is a snapshot, so *when* a call runs decides who is in it

`Hidden` resolves a search as `Bonus + Stat.Random(1, Searcher.Intelligence) >= Difficulty`, and
**nothing in the assembly writes `Bonus`**. #221 read that as an extension point left open. I built a
skill to supply it, verified every link in the chain, shipped it in #717 — and it does nothing.

The chain really is as I read it. `Physics.Search()` fires `Event.New("Searched", "Searcher", …)` at
the current cell and its eight neighbours, passing one Event object by `ref` so a value set on the
first pass survives into the rest. `Cell.FireEvent` iterates `Objects` and calls `FireEvent` on each.
`AddSkill` does `AddPart` with `DoRegistration: true`, `ApplyRegistrar` calls `Register`, and
`GameObject.FireEvent` dispatches from `RegisteredPartEvents[E.ID]`. Every one of those is true, and
in the game the handler never ran once.

The reason is four lines of `Cell.AddObject`:

```csharp
XRL.World.Parts.Physics physics = Object.Physics;
if (physics != null && !physics.EnterCell(this))   // Search() runs in here
{
    return Object;
}
Objects.Add(Object);                                // the mover is added AFTER
```

`EnterCell` calls `Search()` **before** the mover is added to the cell's `Objects`. So on the movement
path the searcher is in the dispatch set of neither their new cell nor its neighbours, and a part on
the searcher cannot see the event at all. The `CmdWait` path calls `Search()` from `XRLCore` while the
player is already standing in the cell, so that one works — which is why the feature was not uniformly
dead, only dead in the case that matters.

> **Membership in a dispatch list is evaluated at call time, and a call inside an "entering" method
> runs before the entering has finished.** Verifying that A dispatches to B is not the same as
> verifying that B is in A's list *at the moment A runs*. The second question decides whether a
> handler fires, and it is invisible from the dispatch code.

Two things this cost that are worth naming:

- **Every static check passed.** It compiled, it validated, and the part was provably attached and
  registered — a heartbeat printed in-game confirmed `HasRegisteredEvent("Searched") == true` on the
  player while the handler never ran once. No check could have caught this, which is the whole
  argument for `tools/sync_mod.py --dev` *before* merge rather than after.
- **The trigger was published wrong as well.** I wrote that searching happens "every player turn" in
  the issue, the pull request, `FEATURES.md` and the docstring. It happens on entering a cell and on
  the wait command, and nowhere else. That figure came from an investigation comment I inherited and
  never checked.

Related: [`Containment is not dispatch — check the cascade level before assuming a part is reached`](#containment-is-not-dispatch-check-the-cascade-level-before-assuming-a-part-is-reached)
is the same family — there the part was in the object and outside the cascade, here it was registered
for the event and outside the list. Both are *reachability at the moment of the call*, and neither is
visible from the handler's side.
