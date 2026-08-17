# Lessons learned

Operational traps I hit while maintaining this fork, written down so nobody pays for them twice.
I add to this whenever something bites — the reasoning is the durable artifact, not the fix.

Most of these are about Caves of Qud itself and should be useful to anyone modding it: where the
game keeps its own API documentation, which vanilla data files aren't valid XML, how an extension
point fails when you forget its marker attribute. The rest are about git, GitHub, and the tooling
here.

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
work (`tools/build_preview.sh` reproduces `mod/preview.png` byte-for-byte, and a second run proves
it), and **guard the input's identity** rather than trusting it — the script refuses to run unless
the base is 418×312, because every offset is measured against that logo and a swapped base would
misplace the marks instead of erroring.

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
  *only* that directory. My global directory holds a single `pre-commit` file, so `.git/hooks/`
  `pre-push` is never read, and `default_install_hook_types: [pre-commit, pre-push]` is half inert.
  Harmless while no hook declares `stages: [pre-push]`, and a trap the moment one does.

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

While testing a new check in #80, `git checkout mod/Subtypes.xml` — which I used to undo a
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
