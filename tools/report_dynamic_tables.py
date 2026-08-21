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
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_vanilla_drift import BlueprintIndex, find_game, load_all

MOD_DIR = Path("mod")
TAG_PREFIX = "DynamicObjectsTable:"


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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--game", help="path to StreamingAssets/Base")
    ap.add_argument(
        "--require",
        action="store_true",
        help="fail instead of skipping when the game is missing",
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
    print(f"{len(new_names)} blueprint(s) introduced by this mod\n")
    report(collect(index, new_names, mod_declared))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
