# Releasing

Every release has to reach two places and neither one implies the other. Steam is where the
subscribers are, so it is easy to think of the Workshop upload as *the* release — but GOG, itch and
Linux players install from the GitHub release zip, and for all of them a Workshop upload is not a
release at all. Miss the tag and those players get nothing, silently.

This is the order I do it in. The steps that can be checked are checked; the rest are here because
four releases in, the process lived only in my head.

---

## 1. Decide the version

`docs/STYLEGUIDE.md` §7.2.1 has the rule, and it is worth reading rather than deciding by feel:

- **Patch** — defect fixes that change no player-facing behaviour beyond correcting it
- **Minor** — new content, new tables, rebalancing
- **Major** — reserved for a change that breaks saves or removes content

"Removes content" means content that *goes away*, not content replaced in function. 2.4.0
disabled
the quill arrow and shipped the hulk honey arrow in its place and was still minor, because saves
load, the old blueprint is commented rather than deleted, and the release net-grows.

## 2. Roll the changelog

Turn `## [Unreleased]` into `## [X.Y.Z] - YYYY-MM-DD` and open a fresh empty `[Unreleased]`
above it.

Entries marked **(internal)** stay — the changelog serves contributors as well as subscribers, and
the marking is what lets a reader skip them.

## 3. Bump `manifest.json`

`version` only. **`validate_mod.py` now fails if this and the changelog's newest released heading
disagree**, so these two cannot drift apart — but they can only be checked against each other, not
against the tag — so pass `--tag vX.Y.Z` to `sync_mod.py --zip` in step 7 and the third side of
that triangle is checked too (#314).

## 4. Update `workshop.json`

**The version lives in two places in the description, and it is easy to update one.**

1. The **New in X.Y.Z** heading. Replace the section with this release's summary and delete the
   previous one rather than letting them stack.
2. The **Version and saves** block, which opens `[b]X.Y.Z.[/b]` and then says which saves load. Both
   the number and the sentence need this release's answer — 2.10.0 loads on 2.9.x, and which of its
   features reach a character already running is not the same answer 2.9.0 gave.

`check_docs.py`'s `workshop-version` compares the second one against `manifest.json` and fails the
commit if they disagree, so this cannot ship wrong. It caught exactly this during the 2.10.0 release,
which is why it is written down here now: a check is the backstop, not the instruction (#694).

**Watch the budget.** Steam's limit is 8,000 characters, hard. Check the headroom before you start
rather than after you have written the summary:

```bash
python3 -c "import json;print(len(json.loads(open('mod/workshop.json',encoding='utf-8-sig').read())['Description']))"
```

`validate_mod.py` fails the build past 8,000, so this cannot ship broken — but it can block a release
at the worst possible moment. **Trim as you add.** The description has been within a hundred
characters of the limit since 2.10.0, so for now that is not advice, it is the step.

`docs/STYLEGUIDE.md` §7.4 has the rules for what belongs there at all.

## 5. Write the player-facing notes

One piece of prose, used twice: the GitHub release body, and the change note pasted into Caves of
Qud's uploader.

Write it for a player. What changed, what it means for a character they are already running,
and
whether they need a new one. The reasoning belongs in `CHANGELOG.md` and the issues — the release
notes say what they get.

Open with the save-compatibility line, because it is the first thing anyone wants:

> **A 2.4.x character carries over** — no new character needed.

## 6. Publish to the Workshop

```bash
python3 tools/sync_mod.py --publish
```

This refuses anything but a clean `main` level with `origin`, and runs the validator first. It
installs the mod into the game's `Mods` directory exactly as it will ship.

Then launch Caves of Qud and upload through its own Workshop uploader, pasting the notes from step 5
into the change note field.

**Do not hand-edit the install directory afterwards.** It is the same directory `--dev` writes to,
which is why `--dev` strips the `WorkshopId` and suffixes the title — so a dev build cannot
overwrite the published item.

## 7. Tag and release on GitHub

```bash
git tag -a vX.Y.Z -m "X.Y.Z — short title"
git push origin vX.Y.Z
gh release create vX.Y.Z --title "X.Y.Z — short title" --notes-file <notes>
```

**This is the step that serves everyone not on Steam.** The tag is also the third place the
version lives, and the one nothing can check: on the release commit the manifest and changelog
already say `X.Y.Z` while the tag does not exist yet, so a validator including it would fail the
very commit that creates a release.

### Attach the zip, and do not skip this

```bash
python3 tools/sync_mod.py --zip --tag vX.Y.Z
gh release upload vX.Y.Z QudExpandedCommunityEdition-X.Y.Z.zip
```

The contents of `mod/`, under a folder named for the manifest id. Both names come from
`manifest.json` — the archive from its `version`, the folder inside from its `id` — so the rename
that used to hide inside a `cp -R` cannot go wrong: the install directory is
`qud-expanded-community-edition` and every published zip contains `QudExpandedCommunityEdition`, and
that difference used to be a step you had to remember rather than something the tool knew.

The archive is gitignored, so it does not have to be moved or deleted before step 6 — which matters
because `--publish` refuses a dirty tree too, and for one release the asset from this step blocked the
publish build of the same release.

**`--zip` builds from `mod/`, not from the install directory**, which closes the other hole: there is
no copy in between that could belong to a `--dev` run or to a version before the bump. It applies the
same guards `--publish` does — refuses a dirty tree, refuses a branch that is not `main` level with
origin, and runs the validator first — and `--tag` refuses to build at all unless the tag agrees with
the manifest version. That is the check step 3 says it cannot make.

It reproduces what the manual recipe produced: run against the `v2.5.1` tag it rebuilds the shipped
2.5.1 asset **byte for byte, all 81 files** (#314).

**A release without it is not empty, which is the trap.** GitHub generates a source zip for any tag,
so the page still offers a download — of the whole repository, `tools/` and `docs/` and all. A
player who takes that and drops it in `Mods/` gets the repo rather than the mod. The failure is not
a missing file, it is a plausible wrong one, offered to exactly the players this step exists for.
2.5.1 went out without the asset for twenty minutes for this reason (#312).

The two checks #312 added here are gone, because `--zip` makes both impossible rather than
detectable. A stale build cannot happen when the archive is assembled from `mod/` at the commit the
guards just verified, and zipping the source tree by mistake cannot happen when no path is typed. A
check you can delete because the failure is now unreachable is the best outcome a check can have.

## 8. Move the board

Everything in **Staging** becomes **Done**. Per `CONTRIBUTING.md`, Done means released — a merged
pull request is not Done, and neither is a Workshop upload on its own.

Done also holds issues closed *without* shipping, which arrive there directly rather than through
Staging. Those are not part of a release and nothing here moves them; the close reason tells them
apart (`not planned` against `completed`).

---

## The checklist, without the reasoning

- [ ] Version chosen against §7.2.1
- [ ] `CHANGELOG.md` rolled, fresh `[Unreleased]` opened
- [ ] `manifest.json` version bumped
- [ ] `workshop.json` — **New in X.Y.Z** replaced and the previous one removed, **and** the
      **Version and saves** block's version and save answer updated. Under 8,000 characters
- [ ] Player-facing notes written, opening with save compatibility
- [ ] `python3 tools/validate_mod.py` passes
- [ ] `python3 tools/sync_mod.py --publish`
- [ ] Uploaded through Caves of Qud's uploader, notes pasted into the change note
- [ ] Tagged, pushed, and a GitHub release created with the same notes
- [ ] `QudExpandedCommunityEdition-X.Y.Z.zip` built with `sync_mod.py --zip --tag vX.Y.Z` and
      attached — **this is what non-Steam players install**, and GitHub's auto source zip is not a
      substitute
- [ ] Board: Staging → Done
