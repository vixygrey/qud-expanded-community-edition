# Style Guide

How this repository is organised, named, and formatted.

`CLAUDE.md` holds the **charter** — the six rules the fork is maintained under, and why. This
document is the mechanical layer beneath it: given those rules, what does a file get called, how
is it indented, and what is safe to change. Where the two touch, the charter wins.

Everything here is either an industry-standard convention, a Steam Workshop requirement, or a
constraint imposed by Qud's own loader. Where a rule exists only because Qud forces it, that is
stated — those are the ones that look arbitrary and are not.

---

## 1. The rule that comes before all the others

> **Some names are identifiers, not labels. Renaming them orphans data, breaks other mods, or
> breaks the mod itself — silently, with no error.**

Sort them into three groups before touching any of them: permanently frozen (§1.1), frozen only
once this fork has released (§1.1b), and free (§1.3). Conflating the first two is how a fork
either paralyses itself or breaks its own merges.

Qud resolves modded XML by **root element, not by filename**. Verified across the 87 mods
installed locally: `ObjectBlueprints.xml`, `Objectblueprints.xml`, and
`ShadowsOfTheSultans_PopulationTables.xml` all load correctly, because the loader reads the root
element (`<objects>`, `<populations>`) and ignores what the file is called.

That makes **filenames free** and makes several other things **frozen**. Know which is which
before renaming anything.

### 1.1 Permanently frozen — never rename

These are frozen by vanilla identity or engine requirement. **No release schedule or save policy
changes them.**

| Thing | Why |
|---|---|
| **Vanilla blueprint names** (`Cudgel3`, `Battle Axe3th`, `Iron Vinereaper`) | Vanilla identity. Renaming doesn't break a save — it silently orphans the `Load="Merge"`, and the edit simply stops applying. No error. |
| **Population table names** (`Artifact 6R`, `Melee Weapons 3C`) | Same: the merge target must match vanilla exactly. |
| **`.rpm` map basenames** (`Joppa.rpm`) | The basename *is* the zone the patch applies to. |
| **`workshop.json`, `manifest.json`, `preview.png`** | Required names — the Workshop uploader and Qud's mod loader look for exactly these. |
| **Options filename pattern** | Qud only treats a file as mod options if the filename **contains `Option`**. `ModOptions.xml` and `Options.xml` both work; `Settings.xml` does not. |
| **The `Raven_` prefix** | Charter rule 3 — policy, not technology. Mura's signature in the namespace, and the attribution future contributors actually read. |

### 1.1b Frozen after first release — free until then

These are frozen only by **save compatibility**, and this fork has no saves yet.

It publishes as a **new Workshop item** and its release notes state that a new character is
required, so nothing carries over from the original. That makes the following free to change
today — and expensive the moment this fork ships its own v1, because at that point it has players
with saves of its own.

> **This is a closing window, not a standing freedom.** If a rename is wanted, it happens before
> first release. See #24.

| Thing | Note |
|---|---|
| **Body part type strings** (`Chip Interface`) | Written into save state on every character that has one. Settled in #13: `Chipset Interface` → **`Chip Interface`**. |
| **Anatomy and body-object names** (`PsionicAdept`) | Settled in #13: `Yttrian` → **`PsionicAdept`**, matching the `TrueKin` convention. |
| **CoQE-original blueprint names** (`Raven_Iron Maceth`) | **Verified free:** no installed mod references a `Raven_` blueprint. The 11 names the Grand Bazaar sub-mod shares with CoQE are all *vanilla* blueprints CoQE merges, not CoQE originals. The `Raven_` prefix itself still stays — see above. |

### 1.2 Coupled — renameable, but only in lockstep

Independent of release state: these travel in pairs, always.

| Thing | Update alongside |
|---|---|
| **C# class names** (`Raven_ModKindle`) | Referenced by `Name=` on `<part>` elements in the XML. Rename both or neither. |
| **Texture files** (`Textures/Subtypes/forcePsionic.png`) | Referenced from `Subtypes.xml` as `Tile="Subtypes/forcePsionic.bmp"` — note the **`.bmp` extension in XML against a `.png` on disk**. That mismatch is normal Qud convention, not a bug: the engine resolves `.bmp` tile paths against `.png` assets. |
| **C# filenames** | Keep filename == class name (standard .NET). Renaming the file means renaming the class, which means updating every `<part Name="…">` that references it. |

### 1.3 Free — rename freely

- XML filenames (`Melee Weapons.xml` → `melee-weapons.xml`)
- Directory names, except as constrained above
- Documentation filenames
- Tooling and CI filenames

---

## 2. Repository layout

The mod folder is **uploaded verbatim** to the Workshop, so anything sitting beside the mod
content reaches every subscriber. This is not theoretical — of the mods installed locally, 8 ship
a `README.md`, 5 a `LICENSE`, 4 a `.csproj`, and 2 a `.gitignore`. Nobody meant to.

Development tooling therefore lives **outside** the uploaded directory:

```
qud-expanded-community-edition/
├── mod/                          # the ONLY thing uploaded to the Workshop
│   ├── ObjectBlueprints/
│   ├── Scripting/
│   ├── Textures/Subtypes/
│   ├── *.xml
│   ├── Joppa.rpm
│   ├── manifest.json
│   ├── workshop.json
│   └── preview.png
├── docs/                         # FEATURES.md, PERMISSION.md, STYLEGUIDE.md, upstream notes
├── tools/                        # validation script, helpers
├── .github/workflows/            # CI
├── .pre-commit-config.yaml
├── README.md
└── CLAUDE.md
```

This matches the layout already used by the sibling Qud projects in this workspace
(`qud-creature-variants`, `lore-expansion`), so the whole set stays consistent.

**Rule:** if a file exists to help develop the mod rather than to run it, it does not belong in
`mod/`.

---

## 3. Naming conventions

Qud's own data files are `PascalCase.xml` (`PopulationTables.xml`, `ObjectBlueprints.xml`), and
matching vanilla makes modded files instantly legible to anyone who knows the game. **Inside
`mod/`, match vanilla. Outside `mod/`, use standard open-source conventions.**

| Artifact | Convention | Example |
|---|---|---|
| Mod XML files | `PascalCase.xml`, matching the vanilla file they correspond to | `PopulationTables.xml`, `Bodies.xml` |
| Mod XML files with no vanilla counterpart | `PascalCase.xml`, no spaces | `MeleeWeapons.xml`, `PsionicChips.xml` |
| Mod directories | `PascalCase` | `ObjectBlueprints/`, `Textures/` |
| C# files | `PascalCase.cs`, one public class per file, filename == class name | `Raven_ModKindle.cs` |
| C# classes for this fork | `Raven_` prefix retained — see §6 | `Raven_ModFrostWebs` |
| Textures | `camelCase.png`, `<affinity><Role>` | `forcePsionic.png`, `lightGuardian.png` |
| Repo-root docs | `SCREAMING_CASE.md` for top-level standards, `Title-Case.md` otherwise | `README.md`, `STYLEGUIDE.md` |
| Tooling scripts | `kebab-case` or `snake_case.py`, matching the language's norm | `validate-mod.py` |
| Branches | `type/kebab-case-description` | `fix/artifact-table-merge` |

**No filename contains a space.** The four that did — `Melee Weapons.xml`, `Other Equipment.xml`,
`Psionic Chips.xml`, `Ranged Weapons.xml` — were renamed in #23, because spaces require quoting in
every script, hook and CI step that touches them. Do not reintroduce any.

### 3.1 Blueprint naming (for new content)

New blueprints follow Mura's existing scheme, which the charter requires preserving:

- **`Raven_` prefix** on every new object. This is attribution, not decoration — see §6.
- Vanilla merges use the **vanilla name** with `Load="Merge"` and **no prefix**.
- Display names are lowercase (`basic kindle chip`), matching Qud's convention.
- Tier suffixes follow vanilla's pattern where extending a vanilla family (`Battle Axe3th`), and
  read naturally where creating a new one (`Raven_Folded Carbide Halberd`).

---

## 4. XML conventions

### 4.1 Line endings — LF

**LF everywhere**, enforced by `.gitattributes` (`* text=auto eol=lf`) so contributor platform
cannot reintroduce CRLF.

Upstream 2.2 was uniformly CRLF because Mura worked on Windows. This fork normalised it: LF is
what Qud mods actually use — a sample of the installed Workshop mods turned up no CRLF at all —
and .NET's XML parser is indifferent either way.

The obvious objection is that normalising rewrites every line and ruins the diff against the
`upstream-2.2` baseline. It doesn't, because git can suppress the noise:

```bash
git diff --ignore-cr-at-eol upstream-2.2
```

The conversion also landed as a single mechanical commit listed in `.git-blame-ignore-revs`, so
`git blame` skips it. Enable that once per clone:

```bash
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

GitHub applies the file automatically in its own blame view.

### 4.2 Formatting

| Rule | Value |
|---|---|
| Indentation | 2 spaces, **never tabs** — `Skills.xml` (4 lines) and `Throwables.xml` (12 lines) currently violate this |
| Declaration | `<?xml version="1.0" encoding="utf-8" ?>` on line 1 |
| Encoding | UTF-8 |
| Attribute quoting | Double quotes, always |
| Self-closing | Elements with no children close inline: `<part Name="Render" … />` |
| Blank lines | One blank line between logical groups of objects; none within an object |
| Line length | No hard limit — attribute-dense blueprint lines are normal and wrapping them hurts readability |

### 4.3 Attribute order

Consistent ordering makes diffs readable and scanning fast. On `<object>`:

1. `Name`
2. `Inherits`
3. `Load`

On `<part>`: `Name` first, then the rest in the order vanilla uses for that part type.

### 4.4 Escaped entities — do not touch

Qud colour codes appear as XML entities: `ColorString="&amp;y"`, `DisplayName="&amp;cvibro &amp;ybullet"`.
These must survive formatting unaltered. Any formatter or bulk edit is verified against this
before adoption.

### 4.5 Comments

- Section comments mark groups within a file: `<!-- Feet -->`
- Commented-out content **states why and when**. `ObjectBlueprints/Ammo.xml` is a ~500-line
  comment reading only "removed temporarily", with no date and no reason — see #14. Do not add
  more of these.

---

## 5. C# conventions

The `Scripting/` directory currently holds 36 one-line classes and nothing else. Standard .NET
conventions apply, plus two constraints from the charter:

- **PascalCase** types and members, `_camelCase` private fields, 4-space indent, one public class
  per file, filename == class name.
- **Parts inherit `IPart` and carry `[Serializable]`.** Keep `WantEvent` lean — it runs on every
  event fired.
- **Charter rule 5 (safety) is a hard boundary.** No file I/O outside the mod directory, no
  network, no reflection into game internals, no Harmony, no loading external assemblies. Qud mods
  run with full process privileges and `Scripting/` triggers an approval prompt for every
  subscriber — that is a trust relationship, and the current 36 inert classes are the ceiling.
- **Prefer XML.** Anything achievable in data should be data: less code is both safer and more
  durable across game patches.

---

## 6. Attribution in the source

Charter rule 3 makes credit the one non-negotiable condition of the fork. Two mechanical
consequences:

- **The `Raven_` blueprint and class prefix stays.** It is Mura's signature in the namespace, and
  it is the attribution that every future contributor actually reads. Renaming it to something
  fork-specific would erase authorship from the code itself.
- **`manifest.json` `author` and the Workshop description both carry the full credit list** from
  `PERMISSION.md` §4, with **Noble Lark named explicitly** for the subtype sprites, as Mura asked.

---

## 7. Steam Workshop requirements

### 7.1 `workshop.json`

Uploader metadata. Observed schema across all 40 installed mods that ship one — every field below
appears in all of them:

| Field | Notes |
|---|---|
| `WorkshopId` | The published item ID. **Empty on first upload** — Qud fills it in. A non-empty value targets *that* item, which is how a fork can accidentally publish over the original (#2). |
| `Title` | Item title |
| `Description` | **Steam BBCode**, not Markdown — `[h1]`, `[i]`, `[b]`, `[url]`, `[list]` |
| `Tags` | Comma-separated, from Qud's published tag set |
| `Visibility` | `0` public · `1` friends · `2` private |
| `ImagePath` | Relative path to the preview, normally `preview.png` |

### 7.2 `manifest.json`

Mod identity and load behaviour — present in 64 of 87 installed mods, and currently **missing
here** (#21). Lowercase keys:

```json
{
  "id": "…",
  "title": "…",
  "version": "…",
  "author": "…",
  "description": "…",
  "tags": "…",
  "previewImage": "preview.png"
}
```

`loadorder` is **deprecated as of build 210**. Use `LoadBefore` / `LoadAfter` when ordering
against another mod is genuinely required.

**`id` is effectively permanent.** It is what other mods name in their `LoadBefore` / `LoadAfter`
declarations, so changing it breaks their ordering against this mod. It is
`QudExpandedCommunityEdition` and should stay that way.

**`author` must name Mura.** Charter rule 3 in machine-readable form; the validator enforces it.

### 7.2.1 Versioning

Semantic versioning, **continuing Mura's lineage rather than resetting**. Upstream's last release
was 2.2, so this fork's first release is **2.3.0**. Restarting at 1.0.0 would present the fork as a
new mod rather than a continuation, which is both less accurate and a quieter form of taking
credit for the eleven releases that came before.

- **Patch** — defect fixes that change no player-facing behaviour beyond correcting it
- **Minor** — new content, new tables, rebalancing
- **Major** — reserved for a change that breaks saves or removes content

Note that "requires a new character" applies to the **first** release regardless, because
save-baked identifiers changed during the fork.

### 7.3 `preview.png`

- PNG, **under 1 MB** (Steam limit). The current file is 418×312 and 60 KB.
- Must be readable as a thumbnail — it is displayed small.
- Path declared in `workshop.json` `ImagePath`.

### 7.4 Description content

- Lead with what the mod does, not with history.
- Carry the `PERMISSION.md` §4 credit list, Noble Lark named explicitly.
- State clearly that this is a **community fork** and link the original item (`1134036260`).
- Never carry text written by the original author as though it were the fork's own — the current
  description is Mura's pre-handoff notice asking that the mod *not* be forked (#2).

---

## 8. Documentation

- **Markdown, LF line endings**, one sentence per line not required but lines wrapped at ~100.
- `README.md` is the entry point: what it is, credits, install, contributing.
- `FEATURES.md` is the feature reference and is expected to stay exhaustive.
- `PERMISSION.md` is a provenance record — **append, never rewrite**.
- Reference issues as `#N`, files as clickable relative paths.

---

## 9. Commits, branches, and PRs

Defined in `CLAUDE.md` § Workflow — trunk-based, issue-first, atomic commits, conventional commit
messages with repo-specific scopes (`tables`, `chips`, `armor`, `melee`, `ranged`, `skills`,
`genotypes`, `bodies`, `workshop`, `scripting`, `docs`). Not duplicated here.

The one point worth repeating, because it is the most commonly skipped: **the commit body carries
the causality.** Charter rule 2 lives or dies in commit messages.

---

## 10. What enforces what

A style rule nobody checks is a preference. Current and planned coverage:

| Rule | Enforced by | Status |
|---|---|---|
| XML well-formedness | `check-xml` pre-commit hook + CI | #18, #19 |
| Indentation, trailing whitespace, EOF newline | pre-commit hooks | #18 |
| Line endings | `.gitattributes` | #17 |
| XML formatting | Formatter, one isolated baseline commit | #17 |
| Spelling in player-facing strings | `typos`, with a Qud vocabulary allowlist | #18 |
| No committed secrets | `gitleaks`, `detect-secrets` | #18 |
| Blueprint reachability | Custom validation script | #8 |
| **`Load="Merge"` on vanilla records** | Custom validation script | #8 |
| Tier/value curve consistency | Custom validation script | #8 |
| Conventional commit format | `commitlint` in CI | #19 |
| No direct commits to `main` | Local hook; GitHub protection unavailable on private free tier | #20 |

The `Load="Merge"` check is the important one: it turns the fork's headline compatibility rule
into something mechanically enforced rather than remembered, and it would have caught #3 on the
commit that introduced it.
