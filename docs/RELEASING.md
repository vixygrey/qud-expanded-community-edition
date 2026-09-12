# Releasing

Every release must reach two places.
Steam serves subscribers.
GOG, itch, and Linux players install the GitHub release zip.
A Workshop upload alone is not a release for those players.
The tag connects the release note to the released files.

Follow this order.
Run each available check.
Document the remaining steps because the process must not depend on memory.

---

## 1. Decide the version

`docs/STYLEGUIDE.md` §7.2.1 defines the version rule:

- **Patch:** defect fixes that correct behavior without a broader player-facing change
- **Minor:** new content, new tables, or rebalancing
- **Major:** save-breaking changes or removed content

"Removes content" means that content goes away.
It does not include content that another feature replaces.
Version 2.4.0 disabled the quill arrow and shipped the hulk honey arrow in its place.
The release remained minor because saves load, the old blueprint remains commented, and the release adds content overall.

## 2. Roll the changelog

Change `## [Unreleased]` to `## [X.Y.Z] - YYYY-MM-DD`.
Open a new empty `[Unreleased]` section above it.

Keep entries marked **(internal)**.
The changelog serves contributors and subscribers.
The marker lets readers skip internal entries.

## 3. Bump `manifest.json`

Change `version` only.
**`validate_mod.py` fails when this value disagrees with the newest released changelog heading.**
Pass `--tag vX.Y.Z` to `sync_mod.py --zip` in step 7.
That command compares the tag with the manifest and completes the three-way version check (#314).

## 4. Update `workshop.json`

**The description carries the version in two places.**

1. Replace the **New in X.Y.Z** section with this release's summary.
   Delete the previous section.
2. Update the **Version and saves** block.
   Set `[b]X.Y.Z.[/b]`.
   State which saves load.
   Use the answer for this release.

`check_docs.py`'s `workshop-version` check compares the second value with `manifest.json`.
It caught a mismatch during the 2.10.0 release (#694).
The check is a backstop, not an instruction.

**Watch the byte budget.** Steam limits the description to 8,000 bytes.
Measure the budget before writing the summary:

```bash
python3 -c "import json;print(len(json.loads(open('mod/workshop.json',encoding='utf-8-sig').read())['Description'].encode('utf-8')),'bytes')"
```

**Count bytes, not characters.** `validate_mod.py` measures bytes.
`len()` on the string measures characters.
The description contains non-ASCII characters that occupy more than one byte.
An older check measured 7,969 characters and missed a total of 8,035 bytes in version 2.15.0.

`validate_mod.py` rejects a description above 8,000 bytes.
Trim the description while adding content.
The description has stayed within 100 bytes of the limit since version 2.10.0.

See [`docs/STYLEGUIDE.md`](STYLEGUIDE.md) §7.4 for description content rules.


## 5. Write the player-facing notes

Write one note for two destinations:
the GitHub release body and the change note in Qud's Workshop uploader.

Write for players.
State what changed, how it affects an existing character, and whether a new character is required.
Put reasoning in `CHANGELOG.md` and issue records.
Put player effects in the release notes.

Start with the save-compatibility line:

> **A 2.4.x character carries over.** No new character is needed.

### Use separate Markdown and BBCode

Use the same words in both destinations.
GitHub uses **Markdown**.
Steam uses **BBCode**, the format in `mod/workshop.json`.
Do not paste Markdown into Steam.
The asterisks render as literal text.

The repository checks `mod/workshop.json`.
It does not check the change note entered in Steam.
Write both forms before opening the uploader.

| Markdown | BBCode |
|---|---|
| `**bold**` | `[b]bold[/b]` |
| `*italic*` | `[i]italic[/i]` |
| `- item` | `[list]` / `[*]item` / `[/list]` |
| `[text](https://example.com)` | `[url=https://example.com]text[/url]` |
| `# Heading` | `[h1]Heading[/h1]` |

Do not add a heading to the Steam change note.
Steam prints the version above the field.
The 8,000-byte limit applies to the description, not the change note.

The 2.15.1 note is the worked example, trimmed:

```
[b]A 2.15.x character carries over[/b] - no new character needed, and the fix reaches a character you are already playing.

One fix.

[list]
[*][b]Tiredness now says what it costs you.[/b] Looking at yourself and choosing Show Effects showed a placeholder where the description should be.
[/list]
```

## 6. Publish to the Workshop

```bash
python3 tools/sync_mod.py --publish
```

`tools/sync_mod.py --publish` requires a clean `main` that matches `origin`.
It runs the validator first.
It installs the mod in the game's `Mods` directory as the published build.

Launch Caves of Qud.
Upload through the Workshop uploader.
Paste the notes from step 5 into the change note field.

**Do not edit the install directory after publication.**
`--dev` writes to the same directory.
It removes `WorkshopId` and adds a title suffix.
This prevents a development build from overwriting the published item.

## 7. Tag and release on GitHub

```bash
git tag -a vX.Y.Z -m "X.Y.Z - short title"
git push origin vX.Y.Z
gh release create vX.Y.Z --title "X.Y.Z - short title" --notes-file <notes>
```

**This step serves players who do not use Steam.**
The tag is the third version value.
No validator can check it before the tag exists.
The release commit contains the manifest and changelog values.
The tag command creates the third value afterward.

### Attach the zip, and do not skip this

```bash
python3 tools/sync_mod.py --zip --tag vX.Y.Z
gh release upload vX.Y.Z QudExpandedCommunityEdition-X.Y.Z.zip
```

The archive contains `mod/` under a folder named for the manifest ID.
Both names come from `manifest.json`.
The archive name uses `version`.
The folder name uses `id`.
The install directory is `qud-expanded-community-edition`.
Each published archive contains `QudExpandedCommunityEdition`.

The archive is gitignored.
It does not need removal before step 6.
`--publish` rejects a dirty tree.
An earlier release asset blocked publication for that reason.

**`--zip` builds from `mod/`, not the install directory.**
No intermediate copy can come from a development build or an older version.
The command uses the same guards as `--publish`.
It rejects a dirty tree and a branch that does not match `origin`.
It runs the validator first.
The `--tag` option requires agreement with the manifest version.

The command reproduces the manual recipe.
The `v2.5.1` tag rebuilds the shipped 2.5.1 asset **byte for byte, all 81 files** (#314).

**A release without the archive still offers a download.**
GitHub creates a source zip for every tag.
That archive contains the repository, including `tools/` and `docs/`.
A player who copies it into `Mods/` receives the repository instead of the mod.
Version 2.5.1 lacked the asset for 20 minutes for this reason (#312).

The two checks added for #312 are now removed.
`--zip` makes both failure modes unreachable.
The archive comes from `mod/` at the verified commit.
The command receives no manually typed source path.
Removing a check after removing its failure path is the intended result.

## 8. Move the board

Everything in **Staging** becomes **Done** after publication.
Per [`CONTRIBUTING.md`](../CONTRIBUTING.md), a merged pull request is not Done.
A Workshop upload alone is not Done.

Done also contains issues closed without shipping.
Those issues bypass Staging.
The close reason distinguishes `not planned` from `completed`.

---

## The checklist, without the reasoning

- [ ] Choose the version against §7.2.1
- [ ] Roll `CHANGELOG.md` and open a fresh `[Unreleased]`
- [ ] Bump the `manifest.json` version
- [ ] Replace **New in X.Y.Z** in `workshop.json` and update **Version and saves**
- [ ] Keep the description below 8,000 bytes
- [ ] Write player-facing notes in Markdown and BBCode
- [ ] Run `python3 tools/validate_mod.py`
- [ ] Run `python3 tools/sync_mod.py --publish`
- [ ] Upload through Caves of Qud's Workshop uploader
- [ ] Tag, push, and create the GitHub release with the same notes
- [ ] Build and attach `QudExpandedCommunityEdition-X.Y.Z.zip` with `sync_mod.py --zip --tag vX.Y.Z`
- [ ] Move the board item from Staging to Done
