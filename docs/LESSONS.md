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
