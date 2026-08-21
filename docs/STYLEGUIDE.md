# Style Guide

How this repository is organised, named, and formatted.

`CHARTER.md` holds the **charter** — the six rules I maintain this fork under, and why. This
document is the mechanical layer beneath it: given those rules, what does a file get called, how
is it indented, and what is safe to change. Where the two touch, the charter wins.

Everything here is either an industry-standard convention, a Steam Workshop requirement, or a
constraint imposed by Qud's own loader. Where a rule exists only because Qud forces it, that is
stated — those are the ones that look arbitrary and are not.

---

## 1. The rule that comes before all the others

> **Some names are identifiers, not labels. Renaming them orphans data, breaks other mods, or
> breaks the mod itself — silently, with no error.**

Sort them into three groups before touching any of them: permanently frozen (§1.1), frozen since
this fork released (§1.1b), and free (§1.3). Conflating the first two is how a fork either
paralyses itself or breaks its own merges.

Qud resolves modded XML by **root element, not by filename**. Verified across the 87 mods
installed locally: `ObjectBlueprints.xml`, `Objectblueprints.xml`, and
`ShadowsOfTheSultans_PopulationTables.xml` all load correctly, because the loader reads the root
element (`<objects>`, `<populations>`) and ignores what the file is called.

That makes **filenames free** and makes several other things **frozen**. Know which is which
before renaming anything.

### 1.0b `<removetable>` — the tool this mod deliberately does not use

Qud can remove a table reference from a population group:

```xml
<group Name="Items" Load="Merge">
  <removetable Name="Armor 6C" />
</group>
```

The syntax is **Arendeth's**, worked out for this mod when an earlier attempt was malformed. It is
recorded here because it is genuinely hard to find, and because the code it was written for is
gone.

**Do not reach for it.** Charter rule 1 makes edits additive, and removing a vanilla table
reference is destructive twice over: it discards whatever a future Qud patch adds behind that
reference, and it makes any other mod's additions invisible too. It was used on
`Armor 7C/7R/8C/8R` to sever the tier cascade, and the effect was far larger than intended — a
tier-8 armor roll went from vanilla's 8.6% chance of a zetachrome piece to 100%, and vanilla items
reachable only through the cascade stopped dropping at all. Removed in #4.

**What to do instead: weight your own entries.** Weight is entirely within your own records, needs
no merge trickery, survives vanilla patches, and coexists with other mods. If your new items are
not showing up often enough, they are underweighted — the vanilla cascade is not the problem.

### 1.0c Skills merge per power, by name

`mod/Skills.xml` touches six vanilla skills — Axe, Cooking and Gathering, Cudgel, Long Blade,
Multiweapon Fighting, Tinkering — and edits individual powers inside them without restating the
rest.

**The loader merges at the level of the individual power, keyed by its `Name`, and keeps every
attribute the mod does not restate.** That is why an entry like

```xml
<power Name="Multiweapon Expertise" Minimum="21|21" Tile="..." Foreground="y" Detail="M" />
```

works despite carrying no `Class=` and no `Cost=`: it is editing vanilla's entry, not replacing it.
Here that single change is the whole point — the mod's contribution to that tree is a requirement
cut, `23|23` down to `21|21`.

The evidence is the mod itself. All **23** powers it declares omit `Class=`. If redeclaring a skill
replaced it, all 23 would be left with no implementation — Cleave, Berserk!, Tinker I/II/III,
Disassemble and the rest — and the mod would be obviously broken rather than subtly wrong. It has
played correctly for years. Replacement would also have silently deleted **18** vanilla powers,
including Tinkering's Repair and Scavenger and Long Blade's Lunge and Swipe.

**Write `Load="Merge"` on the skill anyway** (#87). The mod did not, for years, and was saved by the
loader's default rather than by intent — which is precisely the arrangement charter rule 1 exists to
prevent. Explicit is also durable: it states what is meant, survives a change to the loader's
default, and matches every other merge in the mod.

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

### 1.1b Frozen since first release

These are frozen by **save compatibility**, and that freeze is now in force.

**The window closed on 2026-08-17, when `v2.3.0` shipped** as this fork's first release. Until
then these were genuinely free — the fork publishes as a new Workshop item and its notes require a
new character, so nothing carried over from Mura's original and there were no saves of its own to
protect. That is no longer true. There are players with saves now, and #24, which tracked the
window, is closed.

| Thing | Note |
|---|---|
| **Body part type strings** (`Chip Interface`) | Written into save state on every character that has one. Settled in #13: `Chipset Interface` → **`Chip Interface`**. |
| **Anatomy and body-object names** (`PsionicAdept`) | Settled in #13: `Yttrian` → **`PsionicAdept`**, matching the `TrueKin` convention. |
| **CoQE-original blueprint names** (`Raven_Iron Maceth`) | Was *"verified free"* before release, on the evidence that no installed mod references a `Raven_` blueprint — true, and no longer the point. Saves reference them now. The `Raven_` prefix itself stays regardless — see §1.1. |

**What breaking this actually does, which is the reason it reads as a rule rather than a
preference.** Renaming or removing a blueprint that shipped does not crash and does not error where
anyone will see it. `GameObject.GetBlueprint` looks the name up, misses, logs through
`MetricsManager` and returns the generic `Object` blueprint:

```csharp
if (_BlueprintCache != null || GameObjectFactory.Factory.Blueprints.TryGetValue(Blueprint, out _BlueprintCache))
    return _BlueprintCache;
...
MetricsManager.LogError(new Exception("GameObject::GetBlueprint() Unknown Blueprint " + Blueprint));
return GameObjectFactory.Factory.Blueprints["Object"];
```

The player's object survives — its parts are serialised on the object itself, so a weapon still
swings and an arrow still fires — but every blueprint-level lookup (`GetTag`, `HasTagOrProperty`,
`IsWall`) silently answers as `Object` instead. Degraded, not broken, and invisible to whoever
caused it. The same silent-failure family as an orphaned `Load="Merge"`.

**If a shipped name genuinely has to go**, do what #201 did rather than renaming in place: comment
the old blueprint out with a note saying why and what would restore it, and give the replacement a
**new** name. Existing copies degrade rather than vanish, nothing new spawns, and the old
definition stays in the file for whoever revives it. Weigh that degradation against how long the
name has been out and how common the object is — #201 judged one day of exposure on a weight-2 drop
acceptable, which is not a general licence.

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

### 1.4 Settled naming decisions

The slot is **"Chip Interface"** and the anatomy and body object are **`PsionicAdept`** (#13). Both
were decided rather than inherited, so here is the reasoning.

The original shipped a slot called `Chipset Interface` while all of Mura's player-facing
documentation called it the "Psionic Interface". Neither was accurate: the slot takes 108 chips
against 36 chipsets, and 13 of the 36 mutations the chips grant are *physical* rather than mental.
"Chip Interface" is true of the whole catalogue, it matches the technological fiction in the chips'
own description, and it doesn't imply the slot belongs to the Psionic Adept genotype — it's merged
into base `Humanoid`, so every humanoid has one.

`PsionicAdept` follows the convention `Genotypes.xml` already sets: the True Kin genotype
("True Kin") points at a body object and anatomy named `TrueKin`, the display name with spaces
removed.

**Use these names in all new player-facing text.** Mura's original documents in `docs/` predate the
decision and I leave them as a historical record.

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
├── docs/                         # CHARTER, FEATURES, LESSONS, PERMISSION, STYLEGUIDE, upstream notes
├── tools/                        # validation script, helpers
├── .github/workflows/            # CI
├── .pre-commit-config.yaml
├── README.md
├── CONTRIBUTING.md
└── CLAUDE.md                     # my local working notes; untracked
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

- **A prefix on every new object**, and which one is a question of credit rather than of
  namespacing — see §6. `Raven_` is Mura's, and stays on everything inherited from CoQE; content
  added to this fork takes **`Vixy_`**. Never re-prefix an existing `Raven_` object: that would
  both break the attribution and spend the identifier-rename window described in §1.1b.
- `tools/validate_mod.py` enforces both through `MOD_PREFIXES`, and treats any other name as a
  vanilla record. A third prefix means updating that constant, or four of its six checks stop
  guarding in silence (#224).
- Vanilla merges use the **vanilla name** with `Load="Merge"` and **no prefix**.
- Display names are lowercase (`basic kindle chip`), matching Qud's convention.
- Tier suffixes follow vanilla's pattern where extending a vanilla family (`Battle Axe3th`), and
  read naturally where creating a new one (`Raven_Folded Carbide Halberd`).

### 3.2 Content conventions

Mura was consistent, and these tables are what make charter rule 2's "derived, not invented"
possible in practice. Match them when adding anything.

- **Blueprint prefix `Raven_` or `Vixy_`** on every new object, per §3.1 — `Raven_` on Mura's,
  `Vixy_` on this fork's. Merges into vanilla objects use the vanilla
  name with `Load="Merge"` and no prefix. **No exceptions remain:** `SteelFist` and the 18
  `Projectile*` objects were the last, renamed in #66 before the save window closed; the
  Recoilers turned out to be vanilla objects the mod was replacing, fixed in #29. The only
  unprefixed new objects left are `TrueKin` and `PsionicAdept`, which are body objects following
  vanilla's own `BodyObject` convention (#13).
- **Tier → material:** 0 bronze · 1 iron · 2 steel · 3 carbide · 4 folded carbide · 5 fullerite ·
  6 crysteel · 7 flawless crysteel · 8 zetachrome.
- **Value curve doubles per tier:** 5 · 10 · 20 · 40 · 80 · 160 · 320 · 640 · 1280. Body armor
  runs 8→2048; vambraces run 4→1024 (half curve, partial slot).
- **Two-handed variants** get `PenBonus="1"` and a damage bump over the one-handed version, plus
  `UsesTwoSlots="true"`.
- **Two-handed hammer `Physics` weight is the one-handed weight plus 3** — inventory pounds, not a
  population table's draw weight — and the one-handed line sits below vanilla's throughout. Every
  war hammer follows it: bronze 4→7, iron 3→6, steel 3→6, carbide 5→8, folded carbide 4→7,
  fullerite 6→9, crysteel 3→6, flawless crysteel 3→6, zetachrome 3→6.
  Read the greathammers on their own and the curve looks like it wobbles: it climbs to fullerite,
  then falls to the lightest weapon in the family at the top tier. That shape is vanilla's own
  one-handed curve, compressed and carried across with a constant added, so the wobble is
  inherited rather than introduced and there is no monotonic curve here to restore. Nothing checks
  this, so check it by hand when you add a tier — #248 read the two-handed half in isolation and
  proposed bringing fullerite down from 9, which was the one value the rule required.
- **Agility-scaling martials** are a deliberate theme: vinereapers, halberds, rapiers, katanas and
  war hammers all use `Stat="Agility"` while keeping their tree's skill.
- **Vibro weapons:** tier 5, value 300, `ChargeUse="100"`, bits `0015`,
  `Mods="AxeMods,BladeMods,WeaponMods,CommonMods,ElectronicsMods"`.
- **Prefer `Load="Merge"`** over redeclaring a vanilla object. The Artifact tables were the one
  place this was violated; they became merges in #34, and `tools/validate_mod.py`'s
  `merge-discipline` check holds the line now. Don't add new violations for it to catch.

The tier and value curves are checked by `item-curve` in `tools/validate_mod.py`, so a mispriced or
mistagged item fails CI rather than sitting in the loot pool at the wrong rarity.

### 3.3 Two ways to distribute an item, and which to reach for

A new item can reach the world by an explicit entry in `mod/PopulationTables.xml`, or by carrying a
`DynamicObjectsTable:X` tag. They do different jobs and this fork uses both.

**Reach for an explicit entry when you want a chosen weight in a named table.** That is what the
other 56 merged tables are, it is reviewable as a number in a diff, and `validate_mod.py` checks the
blueprint resolves. **Every new item should have one** — the tags below are additions on top, not
substitutes, and today every tagged blueprint in this fork also has an explicit entry.

**Reach for a tag when you want the item in vanilla's specialist pool for its category** — the hatter
stocking your helmets, the legendary gunsmith stocking your guns. Only nineteen of vanilla's
seventy-nine declared tables are consumed anywhere, and only a handful of those correspond to gear
this fork adds: `Ammo`, `Guns`, `Headwear`, `EnergyCells`, `Daggers`, `Trinkets`. There is no vanilla
pool for boots, gloves, body armour, shields, cloaks or most melee families, so for those an explicit
entry is the only route and no decision arises.

**A tag cannot be replaced by an explicit entry where the consumer is tiered.** Every one of these
pools is consumed in the `:Tier{n}` form — `DynamicObjectsTable:Guns:Tier{zonetier+1}` and the like —
and `PopulationManager.RequireTable` returns early when a table of that name already exists, so
declaring one replaces vanilla's whole fabricated pool instead of joining it. The tag is the only
additive way into tier-appropriate distribution.

`EnergyCells` is the one that is genuinely load-bearing rather than flavour: `EnergyCellSocket`
reads that pool, so it is what lets a cell this fork adds be found already installed in a machine.
Nothing written in `PopulationTables.xml` can express that. **Do not tidy it away.**

**Whichever you use, run `tools/report_dynamic_tables.py`.** A tag inherits, so the blueprint
carrying it is usually not the blueprint being distributed: `BaseArrow` is vanilla and puts six of
this fork's arrows in the ammunition pool, and two psionic *base* blueprints put all eighteen psionic
firearms into legendary gunsmith stock. Both were invisible until that tool existed, and #223
described the first while missing the second on the same page.

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
| `WorkshopId` | The published item ID. **Omit the key entirely until Steam has assigned one** — see below. A value targets *that* item, which is how a fork can accidentally publish over the original (#2). |
| `Title` | Item title |
| `Description` | **Steam BBCode**, not Markdown — `[h1]`, `[i]`, `[b]`, `[url]`, `[list]` |
| `Tags` | Comma-separated, from Qud's published tag set |
| `Visibility` | `0` public · `1` friends · `2` private |
| `ImagePath` | Relative path to the preview, normally `preview.png` |

**Before the first upload, `workshop.json` should not exist at all.** The uploader writes it: you
select the mod in *Modding Utilities → Steam Workshop Uploader*, click **Create Workshop Id for
Mod…**, and it creates the item and writes the file, containing nothing but the new id. Only then
does **Upload Content…** have somewhere to publish to.

**Never write `"WorkshopId": 0` as a placeholder.** `0` is not "no item" to the uploader — it is a
lookup for item zero, which fails as *Item not found*, with the path and id fields blank and no
offer to create anything. That cost this fork its first upload attempt (#163). Two of the installed
mods ship a `workshop.json` with **no `WorkshopId` key at all**, which is what an unpublished file
actually looks like; none of the 72 carries a zero. `workshop-target` in `tools/validate_mod.py`
rejects a placeholder now, so the trap cannot be laid again.

Once Steam has assigned an id, keep it. It is how every later upload finds the same item, and
`Title`, `Description`, `Tags`, `Visibility` and `ImagePath` are merged back in beside it.

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

"Removes content" means content that *goes away*, not content that is **replaced in function**.
Settled by 2.4.0, which disabled the quill arrow and shipped the hulk honey arrow in its place:
saves still load, the shipped blueprint is commented out rather than deleted so existing copies
keep working (§1.1b), and the release adds four shells besides — so content net-grows and nothing
a player owns stops functioning. That is **minor**. Reserve major for a release that genuinely
takes something away and leaves a hole, or that breaks saves outright.

Note that "requires a new character" applies to the **first** release regardless, because
save-baked identifiers changed during the fork.

### 7.3 `preview.png`

- PNG, **under 1 MB** (Steam limit). The current file is 504×382 and 71 KB.
- Must be readable as a thumbnail — it is displayed small.
- Path declared in `workshop.json` `ImagePath`.
- **Mura's original lettering stays untouched and stays dominant.** The fork's own marks — the
  green `- CE` and `& VixyGrey` — are additions layered on top of it, deliberately in a different
  face so they read as tacked on rather than as part of the original logo. Charter rule 3: the
  maintainer credit sits *under* Mura's, it does not replace or restyle it.

### 7.4 Description content

- Lead with what the mod does, not with history.
- Carry the `PERMISSION.md` §4 credit list, Noble Lark named explicitly.
- State clearly that this is a **community fork** and link the original item (`1134036260`).
- Never carry text written by the original author as though it were the fork's own — the current
  description is Mura's pre-handoff notice asking that the mod *not* be forked (#2).
- **8000 characters, hard.** That is Steam's own limit on a published item's description, and the
  installed mods confirm where the wall is: of the 72 shipping a `workshop.json`, the longest is
  Caves of Qud Expanded's own at 7943. Nothing local complains — the JSON stays valid, Qud still
  loads the mod, and the overflow is cut on Steam's side at upload — so `workshop-description` in
  `tools/validate_mod.py` fails the build instead.
- **Leave headroom.** The description grows with every release, and BBCode markup costs characters
  a reader never sees. Keep it summary-shaped and let `CHANGELOG.md` carry the reasoning: the page
  says what changed, the repository says why.

---

## 8. Documentation

- **Markdown, LF line endings**, one sentence per line not required but lines wrapped at ~100.
- `README.md` is the entry point: what it is, credits, install, contributing.
- `FEATURES.md` is the feature reference and is expected to stay exhaustive.
- `PERMISSION.md` is a provenance record — **append, never rewrite**.
- Reference issues as `#N`, files as clickable relative paths.
- `2.2-changelog.txt` and `mura-feature-notes-wip.txt` are Mura's, kept byte-for-byte as a
  provenance record — **never edited**, not even for typos or line endings.

> **On the first person.** The documents here are written in my voice, so they say "I decided" and
> "I checked" rather than reporting decisions as though they made themselves. That is a description
> of how *I* write, not a rule for you. **Write your issues, pull requests and comments however
> comes naturally** — in your own voice, in whatever person you like. I'd rather have your
> contribution than a stylistic match, and I'll keep the docs consistent myself.

---

## 9. Commits, branches, and PRs

Defined in `CONTRIBUTING.md` — trunk-based, issue-first, atomic commits, conventional commit
messages with repo-specific scopes (`tables`, `chips`, `armor`, `melee`, `ranged`, `skills`,
`genotypes`, `bodies`, `workshop`, `scripting`, `docs`). Not duplicated here.

The one point worth repeating, because it is the most commonly skipped: **the commit body carries
the causality.** Charter rule 2 lives or dies in commit messages.

---

## 10. What enforces what

A style rule nobody checks is a preference. Everything below is enforced today — **ten checks are
required on every pull request**, and `pre-commit` runs the same ones locally so they fail in
seconds rather than after a round trip.

| Rule | Enforced by |
|---|---|
| XML and map-file well-formedness | `wellformed` in `tools/validate_mod.py` |
| `manifest.json` / `workshop.json` validity, and the upload target | `json`, `manifest`, `workshop-target` |
| The Workshop description fitting inside Steam's 8000-character limit | `workshop-description` |
| **`Load="Merge"` on vanilla records** | `merge-discipline` |
| Blueprint reachability, and table entries resolving | `unreachable`, `dangling-blueprint` |
| Part names resolving to a real class in `XRL.World.Parts` | `unknown-part`, against `tools/qud-api.json` |
| Blueprint-valued part attributes naming a blueprint that exists | `dangling-blueprint-ref`, same snapshot |
| Part attributes naming a settable member of the part class | `part-attribute`, against the snapshot's `members` map |
| `<part Builder="…">` naming a class in `XRL.World.PartBuilders` | `part-builder`, against the snapshot's `part_builders` list |
| Figures the documents quote **from vanilla** | `vanilla-figure` in `tools/check_docs.py`, against the snapshot's `figures` map |
| Tier and value curve consistency | `item-curve` |
| Subtype tiles existing and named for their affinity | `subtype-tile` |
| C# parts referenced by XML having a class | `missing-script`, `class-filename` |
| Charter rule 5's banned APIs in `mod/Scripting/` | `scripting-policy` |
| Instance fields on `[Serializable]` types, which enter every save | `serializable-shape` |
| Option wiring — declared but unread, or read but undeclared | `option-wiring` |
| Slider `Min` above 1, which crashes Qud's options menu (#51) | `option-slider` |
| Filenames without spaces | `filename-space` |
| The Joppa removal system matching the map patch | `joppa-sync` |
| Line endings | `.gitattributes` |
| XML formatting | `prettier` with `@prettier/plugin-xml`, checked in CI |
| Python lint and format for `tools/` | `ruff`, pinned to the same version `pre-commit` runs |
| Spelling | `typos`, with a Qud vocabulary allowlist |
| No committed secrets | `gitleaks` over full history, plus GitHub push protection |
| Conventional PR title, and a changelog entry | The `conventions` job in `.github/workflows/ci.yml` |
| No direct commits to `main`, linear history, squash-only merges | GitHub ruleset, plus a local `pre-commit` hook that fails first |
| Every CI job being required or deliberately not, and this section's count | `required-checks` in `tools/check_docs.py`, against `tools/required-checks.json` |

The `merge-discipline` check is the important one: it turns this fork's headline compatibility rule
into something mechanically enforced rather than remembered, and it would have caught #3 on the
commit that introduced it.

**What none of them do is read a sentence and ask whether it's still true.** Every check above
inspects a machine-readable property, which is why the documentation here has gone quietly stale
three times (#93, #96, #106) with everything green. See `docs/LESSONS.md`.

The count in this section is itself the fourth instance, and the one that shows the shape most
clearly. It said **ten** while **nine** were enforced — `Tests` ran and passed on every pull
request and was simply not in the ruleset, so a failing test suite could have merged. Six
documents carried the number and nothing counted it, because a number in prose is prose. It is
checked now (#152), and the fix has a sting worth remembering: when `Tests` was made required, the
obvious next move was to update the documented count — which would have turned a correct ten into
an incorrect eleven. The documents were only right again *because* of the fix.

### 10.1 Where checking stops

Worth stating, so the boundary is not rediscovered by someone building the wrong tool.

**Checkable, and now checked:** figures quoted from the game. A number copied out of Freehold's
data is mechanical, and `vanilla-figure` holds every one of them to its source (#159).

**Not checkable:** claims about how the game *behaves*. "Resistance does not apply on this branch."
"Only `TurretTinker` and `PlaceTurretGoal` raise that event." Both were wrong in #147, both were
about control flow, and both were caught by deploying a turret and looking. Grepping decompiled
source for a pattern would produce a check harder to trust than the sentence it guards. **Do not
build that.**

**Should not be checked:** design rationale. "Cold has no gradient, so halving moderates nothing"
is a judgment, not a fact. Mechanising it would pad the check until it stops meaning anything —
the failure `.typos.toml`'s own policy warns about.

What actually catches the second and third kinds is an acceptance criterion that requires
**running the game**. #144 carried one and it earned its place twice: once finding the cryo arrow
too weak, once finding that turrets deploy empty. That habit is the lever. The tooling above is
worth having because quoted numbers are genuinely mechanical — not because it closes the gap.
