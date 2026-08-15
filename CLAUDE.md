# Caves of Qud Expanded — fork working notes

## What this is

A community fork of **Caves of Qud Expanded** (Steam Workshop `1134036260`), originally by
**Mura** (`@mura_raven`). Fork permission is public and explicit — see `PERMISSION.md`.

This folder **is** the mod. There is no build step: Qud loads these XML files directly, and the
folder as-is is what gets packaged and uploaded to the Workshop. Anything you add here ships to
subscribers.

**Read `FEATURES.md` before touching anything.** It's the complete reference for what the mod
does — every system, every item, all 350 new blueprints and 209 vanilla merges, reconstructed
from the source because no complete list ever existed. Section 10 is the bug/fork checklist.

## Immediate priorities

These are the things blocking a first release, in order.

1. **`Skills.xml` does not parse.** Line 10 has a duplicate `Tile` attribute on the Berserk!
   power. It's the only file in the mod that fails XML validation. **Every skill change the mod
   documents may currently be silently not loading.** Fix, then verify in-game that the Axe /
   Cudgel Strength-or-Agility change actually applies before assuming anything else in §4 works.
2. **`workshop.json` still has `"WorkshopId": 1134036260`** — Mura's item. This fork releases
   *separately*, so that field must be cleared or the uploader targets their page. `Description`
   also holds Mura's pre-handoff text; `Title` and `ImagePath` need updating too.
3. **72 of 144 psionic chips can't drop.** `Raven_Chips Tier 1/2/3` only list the first chip of
   each family plus its chipset. Chips B and C of all 12 families are in no table and have no
   `TinkerItem`. See `FEATURES.md` §3.3.
4. **Nine armor pieces are unobtainable** — the four nanoweave, four flexi, and the mutating mask
   have no drop entry and no tinker recipe. Plus `Raven_Iron Maceth`. See §7.2.
5. **`Artifact 3`–`Artifact 8` are full table replacements, not merges.** Biggest compatibility
   hazard in the mod: conflicts with any other mod touching those tables, and silently discards
   future vanilla additions. Converting to `Load="Merge"` is the highest-value compat fix. See §7.3.

Lower-priority items (value typos, tier typos, the `<stag>` bug, the Akimbo class collision) are
in `FEATURES.md` §10, severity-ranked with file and line.

## Conventions to preserve

Mura was consistent. Match these when adding anything.

- **Blueprint prefix `Raven_`** on every new object. Merges into vanilla objects use the vanilla
  name with `Load="Merge"` and no prefix. (A handful of new objects break this — `SteelFist`,
  `Programmable Recoiler`, the `Projectile*` objects — but the prefix is the rule.)
- **Tier → material:** 0 bronze · 1 iron · 2 steel · 3 carbide · 4 folded carbide · 5 fullerite ·
  6 crysteel · 7 flawless crysteel · 8 zetachrome.
- **Value curve doubles per tier:** 5 · 10 · 20 · 40 · 80 · 160 · 320 · 640 · 1280. Body armor
  runs 8→2048; vambraces run 4→1024 (half curve, partial slot).
- **Two-handed variants** get `PenBonus="1"` and a damage bump over the one-handed version, plus
  `UsesTwoSlots="true"`.
- **Agility-scaling martials** are a deliberate theme: vinereapers, halberds, rapiers, katanas,
  war hammers all use `Stat="Agility"` while keeping their tree's skill.
- **Vibro weapons:** tier 5, value 300, `ChargeUse="100"`, bits `0015`,
  `Mods="AxeMods,BladeMods,WeaponMods,CommonMods,ElectronicsMods"`.
- **Prefer `Load="Merge"`** over redeclaring a vanilla object. The Artifact tables are the one
  place this was violated, and it's the mod's worst compatibility problem — don't add more.

## Naming decision still open

Mura's player-facing docs all say **"Psionic Interface"**; the XML defines the body part as
**"Chipset Interface"** and the items are chips/chipsets. The in-game string comes from
`Bodies.xml`, so players currently see "Chipset Interface". Pick one and make it consistent
before writing any new player-facing text.

## Validating changes

There is no test suite. The minimum bar before any commit — this would have caught the
`Skills.xml` bug:

```bash
python3 - <<'EOF'
import xml.etree.ElementTree as ET, glob, sys
bad = 0
for f in glob.glob('*.xml') + glob.glob('ObjectBlueprints/*.xml') + glob.glob('*.rpm'):
    try:
        ET.parse(f)
    except Exception as e:
        print(f'FAIL {f}: {e}'); bad = 1
print('all XML parses' if not bad else 'PARSE ERRORS ABOVE')
sys.exit(bad)
EOF
```

Useful follow-up checks, all scriptable against the XML:

- Every `Blueprint="..."` in `PopulationTables.xml` resolves to a real object.
- Every new blueprint is reachable — appears in a population table **or** has a `TinkerItem` part.
  (This is the check that surfaces the 72 chips and 9 armor pieces.)
- Every `Raven_Mod*` part referenced by a chip has a matching class in `Scripting/`.
  (Currently clean: 36 referenced, 36 defined.)
- Tier tags are internally consistent with the value curve.

In-game, `wish` is the fastest way to spawn a blueprint by name and eyeball it.

## Things not to break

- **Credit is the one condition of the fork permission.** Mura named **Noble Lark** explicitly for
  the subtype sprites. Keep the credits list in `PERMISSION.md` §4 intact in the Workshop
  description and any README.
- `Ammo.xml` is **entirely commented out** (62 objects, "removed temporarily"). Don't delete it —
  it's the largest block of ready-made content available, including vibro bullets/shells and a
  reworked shotgun shell. Reviving it is a good early win.
- Four vibro weapons are commented out in `Melee Weapons.xml` with "rework these or remove them".
- The `Chipset Interface` slot is merged into the base `Humanoid` anatomy, so **every humanoid NPC
  in the game has one**. Nothing populates it today. Be deliberate if you ever change that — it
  would affect the entire world at once.

## Repo state

⚠️ **This folder is not under version control.** No `.git` was found at this level. Before making
changes across 350 blueprints, `git init` and commit the pristine upstream 2.2 state first — you
will want a diff against Mura's original, both for your own sanity and to show what the fork
changed. (Checked from a sandbox that stops at the mount boundary, so a repo in a parent
directory wouldn't have been visible — verify with `git rev-parse --show-toplevel`.)

## Source documents

| File | What it is |
|---|---|
| `FEATURES.md` | Complete feature reference + bug checklist. Written for this fork; the authoritative doc. |
| `PERMISSION.md` | Fork permission, provenance, credit obligations, pre-upload actions. |
| `permission-mura-workshop-comment.png` | Screenshot evidence of the grant. |
| `What Does the Mod Do (WIP).txt` | Mura's oldest partial list. Joppa section is stale. |
| `2.2 changelog.txt` | The 2.1.1 → 2.2 delta. Only source for the physical-vs-mental chip scaling split. |

Mura also kept a pinned "Partial Feature List" discussion on the Workshop page — newest of the
three writeups, best source for the energy-cell mod formulas. Its content is folded into
`FEATURES.md` §6.6 and §10. Where any of Mura's docs disagree with the XML, **the XML is what
ships** — `FEATURES.md` §10 has a table of the known disagreements.
