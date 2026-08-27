#!/usr/bin/env python3
"""Report which blueprints a `DynamicObjectsTable:` tag actually distributes.

A tag is a distribution route that nothing in this repository records. `validate_mod.py` checks
that every `Blueprint="..."` in PopulationTables.xml resolves and that every new blueprint is
reachable; neither sees a tag. So an object can reach merchant stock, creature inventories or a
machine socket with no entry, no weight, and nothing in a diff to review.

Worse, the tag inherits, so the blueprint carrying it is usually not the blueprint being
distributed. `BaseArrow` carries `DynamicObjectsTable:Ammo` and puts six revived arrows in the
ammunition pool (#261). Two psionic *base* blueprints carry `DynamicObjectsTable:Guns` and put all
eighteen psionic firearms into legendary gunsmith stock (#262). Both were invisible for the same
reason, and #223 described the first while missing the second on the same page - which is the
argument for a tool rather than for paying closer attention.

This reports; it does not fail. #263 has yet to decide which tags should stay, and a check that
failed would be prejudging it.

Needs the game, because the tags that matter are not all in `mod/` - `BaseArrow` is vanilla. Skips
loudly without it, the way tools/compile_scripting.py does, so a contributor without Qud is not
blocked by a report they cannot produce. `--require` turns the skip into a failure.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_vanilla_drift import BlueprintIndex, find_game, load_all

MOD_DIR = Path("mod")
TAG_PREFIX = "DynamicObjectsTable:"
INHERITS_PREFIX = "DynamicInheritsTable:"

# docs/STYLEGUIDE.md 3.2.1. Half is the same chosen ceiling the other two share checks use; the
# floor is on VANILLA's count, because the ceiling protects vanilla's presence and there is nothing
# to protect where vanilla ships nothing. No cell currently sits between four and six, so the exact
# number is not load-bearing.
# Declared rather than only interpolated, so check_docs.py can find it: docs/STYLEGUIDE.md 10.1
# must list every check name a tool emits, and this tool reports without a Findings object.
CHECK_NAME = "inherits-share"

CEILING_PERCENT = 50
VANILLA_FLOOR = 5

# Cells already over the ceiling when this check was written, with the issue tracking each. A
# ledger like tools/validation-baseline.json: it only shrinks, and an entry is a decision deferred
# rather than a rule waived.
#
# None of these can be fixed mechanically. The lever is per-blueprint and binary - a blueprint is
# in every dynamic pool or none - so there is no weight to lower, and getting under half means
# choosing WHICH ten of nineteen ranged weapons stop appearing in generic pools. That is a content
# decision about individual items, and #481 does not answer it.
KNOWN_OVER: dict[tuple[str, str], int] = {
    ("BaseMissileWeapon", "3"): 481,
    ("MissileWeapon", "3"): 481,
    ("MeleeWeapon", "1"): 481,
    # These four also wait on #482: their vinereapers and vibro weapons have no explicit
    # population entry, so excluding them would delete them rather than reweight them.
    ("MeleeWeapon", "5"): 482,
    ("MeleeWeapon", "6"): 482,
    ("MeleeWeapon", "7"): 482,
    ("MeleeWeapon", "8"): 482,
}
SNAPSHOT_PATH = Path("tools/dynamic-pools.json")


def merged_objects(
    van_roots: list[ET.Element], mod_roots: list[ET.Element]
) -> list[ET.Element]:
    """Vanilla blueprints with the mod's `Load="Merge"` edits applied.

    215 of the mod's blueprints merge onto a vanilla one, and 15 of those touch a tag this report
    reads. Indexing them last-wins would discard the vanilla record entirely - `Obsidian Kris`
    would lose `Inherits="BaseDagger"`, two tags and four parts - and the resulting counts would be
    quietly wrong rather than visibly broken.
    """
    objects: dict[str, ET.Element] = {}
    for root in van_roots:
        for obj in root.iter("object"):
            if name := obj.get("Name"):
                objects[name] = obj

    for root in mod_roots:
        for obj in root.iter("object"):
            name = obj.get("Name")
            if not name:
                continue
            if name not in objects:
                objects[name] = obj
                continue
            # A merge edits the blueprint in place, so the mod's declaration of a given tag or
            # part replaces vanilla's rather than sitting alongside it.
            combined = copy.deepcopy(objects[name])
            for child in obj:
                if child.tag in ("tag", "part"):
                    for existing in combined.findall(child.tag):
                        if existing.get("Name") == child.get("Name"):
                            combined.remove(existing)
                combined.append(copy.deepcopy(child))
            objects[name] = combined

    wrapper = ET.Element("objects")
    wrapper.extend(objects.values())
    return [wrapper]


def eligible(index: BlueprintIndex, name: str) -> bool:
    """`EncountersAPI.IsEligibleForDynamicEncounters`, as the game computes it.

    Three conditions, all readable from XML. `ExcludeFromDynamicEncountersOption` is deliberately
    not evaluated - it depends on a runtime option - and is reported separately instead.
    """
    return (
        not index.has_tag(name, "BaseObject")
        and index.has_part(name, "Render")
        and not index.has_tag(name, "ExcludeFromDynamicEncounters")
    )


def declarer(index: BlueprintIndex, name: str, tag: str) -> str | None:
    """The nearest blueprint on `name`'s chain that declares `tag`, honouring `*noinherit`.

    "Inherited" is not one answer. `DynamicObjectsTable:Guns` reaches Raven_Compact Flamethrower
    through vanilla's Flamethrower and reaches eighteen psionic firearms through two bases this
    fork wrote. Only the second is a decision anyone here made, and a report that called both
    "inherited" would put a number on the wrong thing - which is how #262 came to say 22 where the
    true reach is 23.
    """
    for depth, obj in enumerate(index.chain(name)):
        for el in obj.findall("tag"):
            if el.get("Name") == tag:
                if depth > 0 and el.get("Value") == "*noinherit":
                    return None
                return obj.get("Name")
    return None


def consumed_inherits_pools(game: Path) -> set[str]:
    """The `DynamicInheritsTable:<Base>` pools vanilla actually draws from.

    Read out of the population tables with comments stripped, because vanilla keeps a commented-out
    `DynamicInheritsTable:BaseAnimal:Tier2` that would otherwise look live. A pool nothing draws
    from cannot put anything in front of a player, so measuring this fork's share of it would be
    arithmetic about nothing.
    """
    pools: set[str] = set()
    for f in sorted(game.glob("PopulationTables*.xml")):
        text = re.sub(
            r"<!--.*?-->",
            "",
            f.read_text(encoding="utf-8-sig", errors="replace"),
            flags=re.DOTALL,
        )
        pools.update(re.findall(rf"{INHERITS_PREFIX}([A-Za-z_]+)", text))
    return pools


def inherits_cells(
    index: BlueprintIndex, pools: set[str], new_names: set[str]
) -> dict[tuple[str, str], list[int]]:
    """This fork's and vanilla's eligible blueprint counts, per (pool, tier).

    Membership here is not declared anywhere: the game fabricates the pool from everything
    descending from a base, so a blueprint joins as a consequence of `Inherits=`. That is why this
    is counted rather than read - there is no tag to look up and nothing in a diff to review.

    Tier comes from the nearest `Tier` tag on the chain, the same resolution the game uses to build
    the `:Tier{n}` slices these pools are always consumed as. A blueprint with no resolvable tier
    reaches no slice and is skipped.
    """
    cells: dict[tuple[str, str], list[int]] = {}
    for name in sorted(index.objects):
        if not eligible(index, name):
            continue
        tier = index.tag_value(name, "Tier")
        if tier is None:
            continue
        ancestors = {obj.get("Name") for obj in index.chain(name)[1:]}
        for pool in ancestors & pools:
            cell = cells.setdefault((pool, tier), [0, 0])
            cell[0 if name in new_names else 1] += 1
    return cells


def inherits_violations(
    cells: dict[tuple[str, str], list[int]],
) -> tuple[list[str], list[str]]:
    """Cells over the ceiling, split into new ones and the ones KNOWN_OVER already tracks.

    Returns (new, known). Only the first fails a run - the second is reported under `--all`, the
    same bargain tools/validation-baseline.json makes: debt that is catalogued does not block, and
    debt that is not is a defect.
    """
    new: list[str] = []
    known: list[str] = []
    for (pool, tier), (mine, vanilla) in sorted(cells.items()):
        if vanilla < VANILLA_FLOOR:
            continue
        total = mine + vanilla
        if not total or mine / total * 100 <= CEILING_PERCENT:
            continue
        line = (
            f"[{CHECK_NAME}] {INHERITS_PREFIX}{pool}:Tier{tier} is "
            f"{mine / total * 100:.0f}% this fork's ({mine} against vanilla's {vanilla}) - "
            "the ceiling is half"
        )
        issue = KNOWN_OVER.get((pool, tier))
        if issue:
            known.append(f"{line} [#{issue}]")
        else:
            new.append(line)
    return new, known


def collect(
    index: BlueprintIndex, new_names: set[str], mod_declared: dict[str, set[str]]
) -> dict[str, dict]:
    """For each tag, the blueprints declaring it and the mod's own blueprints it reaches.

    Only blueprints this mod introduces count. 215 of its records are `Load="Merge"` edits to
    vanilla objects, and a vanilla dagger was in `DynamicObjectsTable:Daggers` long before this
    fork touched it - counting those would report vanilla's distribution back as though it were
    ours, and bury the handful of entries that actually are.
    """
    tables: dict[str, dict] = {}
    for name in sorted(index.objects):
        for el in index.objects[name].findall("tag"):
            tag = el.get("Name") or ""
            if tag.startswith(TAG_PREFIX):
                # A *delete is a declaration that the tag does NOT apply. Listing it as a route
                # would name Corpse as putting things in DynamicObjectsTable:Items when vanilla
                # explicitly takes it out (#261).
                if el.get("Value") == "*delete":
                    continue
                tables.setdefault(
                    tag,
                    {
                        "declared_on": [],
                        "declared_in_mod": [],
                        "reaches": [],
                        "conditional": [],
                        "via": {},
                    },
                )
                tables[tag]["declared_on"].append(name)
                if name in mod_declared.get(tag, ()):
                    tables[tag]["declared_in_mod"].append(name)

    for tag, data in tables.items():
        for name in sorted(new_names):
            if not index.has_tag(name, tag):
                continue
            if index.has_tag(name, "ExcludeFromDynamicEncountersOption"):
                data["conditional"].append(name)
            elif eligible(index, name):
                data["reaches"].append(name)
                data["via"][name] = declarer(index, name, tag)
    return tables


def report(tables: dict[str, dict]) -> None:
    """Two groups, because only one of them is a decision.

    A tag inherited from a vanilla base is vanilla's design. `DynamicObjectsTable:Items` reaches
    almost every item in the game, and this fork's items are in it for exactly the reason
    vanilla's are. Flagging that is noise, and noise is how a report gets ignored.

    What this fork chose is the tag it declares itself. When one of those sits on a blueprint
    others inherit from, a single line distributes a whole family and nothing at the descendants
    says so - which is #262, and is the case worth a person's attention.
    """
    reached = {t: d for t, d in tables.items() if d["reaches"] or d["conditional"]}
    if not reached:
        print("No DynamicObjectsTable tag reaches a blueprint this mod introduces.")
        return

    ours = {t: d for t, d in reached.items() if d["declared_in_mod"]}
    theirs = {t: d for t, d in reached.items() if not d["declared_in_mod"]}

    print(f"== Declared by this mod ({len(ours)}) ==\n")
    for tag in sorted(ours):
        data = ours[tag]
        direct = set(data["declared_in_mod"]) & set(data["reaches"])
        print(tag)
        print(
            f"  declared here on {len(data['declared_in_mod'])}: "
            f"{', '.join(sorted(data['declared_in_mod']))}"
        )
        print(f"  reaches {len(data['reaches'])} blueprint(s) this mod introduces")
        ours_inherit = sum(
            1
            for n in data["reaches"]
            if n not in direct and data["via"].get(n) in data["declared_in_mod"]
        )
        if ours_inherit:
            print(
                f"  ** {ours_inherit} of them inherit it from a base this mod wrote, and "
                f"nothing at the descendants says so **"
            )
        for n in data["reaches"]:
            src = data["via"].get(n)
            if n in direct:
                note = "  "
            elif src in data["declared_in_mod"]:
                note = f"^ (via {src}) "
            else:
                note = f"~ (via vanilla {src}) "
            print(f"      {note}{n}")
        if data["conditional"]:
            print(
                f"  option-dependent, not evaluated: {', '.join(data['conditional'])}"
            )
        print()

    print(
        f"== Inherited from vanilla ({len(theirs)}) - vanilla's design, not a choice here ==\n"
    )
    for tag in sorted(theirs, key=lambda t: -len(theirs[t]["reaches"])):
        data = theirs[tag]
        via = ", ".join(sorted(data["declared_on"])[:3])
        more = " ..." if len(data["declared_on"]) > 3 else ""
        print(f"  {tag:44s} {len(data['reaches']):>4} via {via}{more}")
    print()
    print("^ inherits the tag from a base this mod wrote; ~ inherits it from vanilla.")


def report_inherits(
    cells: dict[tuple[str, str], list[int]],
    breaches: list[str],
    known_over: list[str],
    show_known: bool,
) -> None:
    """The inherited-membership side, which no tag and no table entry records.

    Printed even when nothing is over the ceiling, because the interesting number here is usually
    the one just under it - and because a section that only appears on failure teaches nobody what
    it is measuring.
    """
    graded = [
        (mine / (mine + vanilla) * 100, pool, tier, mine, vanilla)
        for (pool, tier), (mine, vanilla) in cells.items()
        if mine and vanilla >= VANILLA_FLOOR
    ]
    print(
        f"\nInherited pool membership - {len(cells)} pool tier(s), "
        f"{len(graded)} with content from this fork and a vanilla presence to measure against"
    )
    if not graded:
        return
    for share, pool, tier, mine, vanilla in sorted(graded, reverse=True)[:12]:
        flag = "  OVER" if share > CEILING_PERCENT else ""
        print(
            f"  {pool + ':Tier' + tier:34} {mine:4} / {mine + vanilla:4} = {share:5.1f}%{flag}"
        )
    if breaches:
        print(f"\n  {len(breaches)} newly over the ceiling. docs/STYLEGUIDE.md 3.2.1.")
    if known_over:
        print(
            f"  {len(known_over)} tracked in KNOWN_OVER" + (":" if show_known else ".")
        )
        if show_known:
            for line in known_over:
                print(f"    {line}")


def snapshot_of(tables: dict[str, dict]) -> dict[str, dict[str, list[str]]]:
    """The comparable part of a report: which of this mod's blueprints each pool reaches.

    Deliberately not `declared_on`, which names vanilla blueprints like `Item` and `MeleeWeapon`
    and would turn any Qud update into a diff about vanilla's own structure. `reaches` already
    catches the case that matters - a vanilla base gaining a pooled tag shows up as this mod's
    blueprints arriving in a pool, which is the thing worth being told about.
    """
    return {
        tag: {
            "reaches": sorted(data["reaches"]),
            "conditional": sorted(data["conditional"]),
        }
        for tag, data in sorted(tables.items())
        if data["reaches"] or data["conditional"]
    }


def describe_drift(old: dict, new: dict) -> list[str]:
    """Every difference between two snapshots, as lines a person can act on."""
    out: list[str] = []
    for tag in sorted(set(old) | set(new)):
        if tag not in old:
            out.append(f"{tag}: pool is new to this mod")
        elif tag not in new:
            out.append(f"{tag}: this mod no longer reaches this pool")
        for field in ("reaches", "conditional"):
            was = set(old.get(tag, {}).get(field, ()))
            now = set(new.get(tag, {}).get(field, ()))
            for name in sorted(now - was):
                out.append(f"{tag}: {name} is now in this pool ({field})")
            for name in sorted(was - now):
                out.append(f"{tag}: {name} is no longer in this pool ({field})")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--game", help="path to StreamingAssets/Base")
    ap.add_argument(
        "--require",
        action="store_true",
        help="fail instead of skipping when the game is missing",
    )
    ap.add_argument(
        "--all",
        action="store_true",
        help="list the inherited pool tiers KNOWN_OVER already tracks",
    )
    ap.add_argument(
        "--snapshot",
        action="store_true",
        help=f"rewrite {SNAPSHOT_PATH} (deliberate, reviewed in the diff)",
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help=f"compare against {SNAPSHOT_PATH} and fail on any difference",
    )
    args = ap.parse_args()

    # find_game falls back to the default install when an explicit path does not validate, so a
    # mistyped --game would silently report on a different copy of the game. Refuse instead.
    if args.game and not (Path(args.game).expanduser() / "Bodies.xml").is_file():
        print(
            f"ERROR - {args.game} does not look like StreamingAssets/Base (no Bodies.xml).",
            file=sys.stderr,
        )
        return 1

    game = find_game(args.game)
    if game is None:
        # Loud on purpose. A skip that reads like a pass is its own defect.
        print(
            f"{'ERROR' if args.require else 'SKIPPED'} - Caves of Qud is not installed, and this "
            "report needs it: the tags that matter are not all in mod/ (BaseArrow is vanilla).\n"
            "Pass --game /path/to/StreamingAssets/Base if it lives somewhere unusual.",
            file=sys.stderr,
        )
        return 1 if args.require else 0

    mod_roots = load_all(MOD_DIR)
    van_roots = load_all(game, lenient=True)

    vanilla_names = {
        obj.get("Name")
        for root in van_roots
        for obj in root.iter("object")
        if obj.get("Name")
    }
    new_names = {
        obj.get("Name")
        for root in mod_roots
        for obj in root.iter("object")
        if obj.get("Name") and obj.get("Name") not in vanilla_names
    }

    mod_declared: dict[str, set[str]] = {}
    for root in mod_roots:
        for obj in root.iter("object"):
            for el in obj.findall("tag"):
                tag = el.get("Name") or ""
                if tag.startswith(TAG_PREFIX) and obj.get("Name"):
                    mod_declared.setdefault(tag, set()).add(obj.get("Name"))

    index = BlueprintIndex(merged_objects(van_roots, mod_roots))
    tables = collect(index, new_names, mod_declared)
    cells = inherits_cells(index, consumed_inherits_pools(game), new_names)
    breaches, known_over = inherits_violations(cells)

    if args.snapshot:
        SNAPSHOT_PATH.write_text(
            json.dumps(snapshot_of(tables), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {SNAPSHOT_PATH}. Review the diff before committing it.")
        return 0

    if args.check:
        if not SNAPSHOT_PATH.exists():
            print(
                f"ERROR - {SNAPSHOT_PATH} is missing. Create it with:\n"
                "  python3 tools/report_dynamic_tables.py --snapshot",
                file=sys.stderr,
            )
            return 1
        drift = describe_drift(
            json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8")), snapshot_of(tables)
        )
        if drift:
            print(
                f"FAIL - {len(drift)} change(s) to dynamic pool membership:",
                file=sys.stderr,
            )
            for line in drift:
                print(f"  {line}", file=sys.stderr)
            print(
                "\nA tag inherits, so this is usually not the blueprint you edited - "
                "run the report without --check to see the route.\nIf the change is intended:\n"
                "  python3 tools/report_dynamic_tables.py --snapshot",
                file=sys.stderr,
            )
            return 1
        if breaches:
            print(
                f"FAIL - {len(breaches)} inherited pool tier(s) newly over the ceiling:",
                file=sys.stderr,
            )
            for line in breaches:
                print(f"  {line}", file=sys.stderr)
            print(
                "\nNothing declares this membership - a blueprint joins by what it Inherits, so "
                "there is no entry to reweight.\nThe only lever is "
                '<tag Name="ExcludeFromDynamicEncounters" />, which removes a blueprint from every '
                "dynamic\npool at once - so it is usable only on content that already has an "
                "explicit population entry.\ndocs/STYLEGUIDE.md 3.2.1.",
                file=sys.stderr,
            )
            return 1
        pools = len(snapshot_of(tables))
        tracked = f", {len(known_over)} tracked in KNOWN_OVER" if known_over else ""
        print(
            f"OK - dynamic pool membership matches {SNAPSHOT_PATH} across {pools} pool(s); "
            f"no new inherited pool tier over the ceiling{tracked}"
        )
        return 0

    print(f"{len(new_names)} blueprint(s) introduced by this mod\n")
    report(tables)
    report_inherits(cells, breaches, known_over, args.all)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
