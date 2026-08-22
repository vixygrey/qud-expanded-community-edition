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
against the tag, so step 7 is still on you.

## 4. Update `workshop.json`

Replace the **New in X.Y.Z** section with this release's summary, and delete the previous one rather
than letting them stack.

**Watch the budget.** Steam's limit is 8,000 characters, hard, and the description is already over
6,000. `validate_mod.py` fails the build past 8,000 so this cannot ship broken — but it can block a
release at the worst possible moment. Trim as you add.

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
version
lives, and the one nothing can check: on the release commit the manifest and changelog already say
`X.Y.Z` while the tag does not exist yet, so a validator including it would fail the very commit
that creates a release.

## 8. Move the board

Everything in **Staging** becomes **Done**. Per `CONTRIBUTING.md`, Done means released — a merged
pull request is not Done, and neither is a Workshop upload on its own.

---

## The checklist, without the reasoning

- [ ] Version chosen against §7.2.1
- [ ] `CHANGELOG.md` rolled, fresh `[Unreleased]` opened
- [ ] `manifest.json` version bumped
- [ ] `workshop.json` **New in X.Y.Z** replaced, previous one removed, under 8,000 characters
- [ ] Player-facing notes written, opening with save compatibility
- [ ] `python3 tools/validate_mod.py` passes
- [ ] `python3 tools/sync_mod.py --publish`
- [ ] Uploaded through Caves of Qud's uploader, notes pasted into the change note
- [ ] Tagged, pushed, and a GitHub release created with the same notes
- [ ] Board: Staging → Done
