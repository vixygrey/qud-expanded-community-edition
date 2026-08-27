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
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_vanilla_drift import BlueprintIndex, find_game, load_all

MOD_DIR = Path("mod")
TAG_PREFIX = "DynamicObjectsTable:"
INHERITS_PREFIX = "DynamicInheritsTable:"

# docs/STYLEGUIDE.md 3.2.1. Half is the same ceiling the other two share checks use, but on this
# route it is REPORTED rather than enforced - see #494. Membership here is a consequence of
# `Inherits=`, and completing a weapon family across every tier, which is what this fork is for,
# necessarily takes most of the pool for that family. A rule that fails on the mod's own premise is
# the wrong rule. What fails here is drift against tools/inherited-pools.json instead.
# Declared rather than only interpolated, so check_docs.py can find it: docs/STYLEGUIDE.md 10.1
# must list every check name a tool emits, and this tool reports without a Findings object.
CHECK_NAME = "inherits-share"

CEILING_PERCENT = 50

# A pool where vanilla ships almost nothing is arithmetic about nothing. Counted across the whole
# pool rather than one slice of it, because every slice contains every member - only the weights
# differ - so a per-slice count was never the right floor.
VANILLA_FLOOR = 5

# XRL.World.GameObjectFactory.InitWeights, verbatim. A blueprint's weight in a tier slice comes from
# how far its own Tier sits from the tier requested: same tier weighs 10^8, and every step away
# divides by ten. Counting members instead of weighting them was the defect #494 fixed - at a factor
# of ten per step the nearest tier dominates completely, so a flat count answers a question the game
# never asks.
TIER_DELTA_WEIGHTS = {
    0: 10**8,
    1: 10**7,
    2: 10**6,
    3: 10**5,
    4: 10**4,
    5: 10**3,
    6: 10**2,
    7: 10,
}
DEFAULT_TIER_WEIGHT = 1

# Also InitWeights, applied after the tier weight as ceil(weight * multiplier). The game applies a
# third multiplier after this one, from a `<Table>:Weight` tag; no blueprint in any consumed pool
# carries one, in vanilla or here, so it is not modelled. Role is, because 108 of the 1330 members
# carry one.
ROLE_WEIGHT_MULTIPLIERS = {
    "Common": 4.0,
    "Minion": 4.0,
    "Skirmisher": 1.0,
    "Artillery": 0.25,
    "Uncommon": 0.25,
    "Brute": 0.25,
    "Tank": 0.25,
    "Specialist": 0.1,
    "Leader": 0.1,
    "Hero": 0.1,
    "Rare": 0.01,
    "Epic": 0.01,
}

SNAPSHOT_PATH = Path("tools/dynamic-pools.json")
INHERITS_SNAPSHOT_PATH = Path("tools/inherited-pools.json")


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


def requested_inherits_slices(game: Path) -> dict[str, set[tuple[int, int] | None]]:
    """The `DynamicInheritsTable:` slices vanilla actually asks for, per pool.

    Until #494 this returned bare pool names, and a pool is not the thing that gets rolled - a slice
    is. `DynamicInheritsTable:BaseShield:Tier0` and `:Tier8` are different tables built from the
    same members, and this fork's share of them differs by sixty points. Measuring the pool and not
    its slices is what hid forty cells that were over the ceiling.

    A `{zonetier}`-style spec is substituted at runtime and can land on any tier, so it contributes
    all nine. `Tier4-7` is a range, which the game weights differently from `Tier4`. A request with
    no tier at all is the untiered table, recorded as None.

    Comments are stripped, because vanilla keeps a commented-out
    `DynamicInheritsTable:BaseAnimal:Tier2` that would otherwise look live. A pool nothing draws
    from cannot put anything in front of a player, so measuring this fork's share of it would be
    arithmetic about nothing.
    """
    slices: dict[str, set[tuple[int, int] | None]] = {}
    pattern = rf'{INHERITS_PREFIX}([A-Za-z_]+)(:Tier([^"\s/>]*))?'
    for f in sorted(game.glob("PopulationTables*.xml")):
        text = re.sub(
            r"<!--.*?-->",
            "",
            f.read_text(encoding="utf-8-sig", errors="replace"),
            flags=re.DOTALL,
        )
        for pool, tiered, spec in re.findall(pattern, text):
            want = slices.setdefault(pool, set())
            if not tiered:
                want.add(None)
            elif "{" in spec:
                want.update((n, n) for n in range(9))
            elif "-" in spec:
                low, _, high = spec.partition("-")
                want.add((int(low), int(high)))
            elif spec.isdigit():
                want.add((int(spec), int(spec)))
    return slices


def slice_label(window: tuple[int, int] | None) -> str:
    """How a slice is named in a report and pinned in the snapshot."""
    if window is None:
        return "untiered"
    low, high = window
    return f"Tier{low}" if low == high else f"Tier{low}-{high}"


def slice_weight(tier: int, window: tuple[int, int] | None, role: str | None) -> int:
    """One blueprint's weight in one slice, as the game computes it.

    For the untiered table the game forces the tier delta to zero, so every member weighs the same
    and only Role separates them.

    For a blueprint outside the window, the distance is measured from the LOW end twice. Vanilla
    writes `Math.Min(Math.Abs(minTier - t), Math.Abs(minTier - t))` - the same expression on both
    sides, so `maxTier` never reaches the comparison. That is a bug in Caves of Qud rather than a
    typo here, and reproducing it is the only way this report agrees with what a player rolls. It is
    invisible on a single tier, where low and high are equal, and bites only on the three ranges
    vanilla asks for.
    """
    if window is None:
        delta = 0
    else:
        low, high = window
        delta = 0 if low <= tier <= high else abs(low - tier)
    weight = TIER_DELTA_WEIGHTS.get(delta, DEFAULT_TIER_WEIGHT)
    multiplier = ROLE_WEIGHT_MULTIPLIERS.get(role or "")
    if multiplier is not None:
        weight = math.ceil(weight * multiplier)
    return weight


def inherits_members(
    index: BlueprintIndex, pools: set[str]
) -> dict[str, list[tuple[str, int, str | None]]]:
    """Every eligible blueprint each pool reaches, with the Tier and Role its weight needs.

    Membership is not declared anywhere: the game fabricates the pool from everything descending
    from a base, so a blueprint joins as a consequence of `Inherits=`. That is why this is counted
    rather than read - there is no tag to look up and nothing in a diff to review.

    A blueprint with no resolvable tier reaches no slice and is skipped, the same as in the game,
    where `GameObjectBlueprint.Tier` would have nothing to compare.
    """
    members: dict[str, list[tuple[str, int, str | None]]] = {}
    for name in sorted(index.objects):
        if not eligible(index, name):
            continue
        tier = index.tag_value(name, "Tier")
        if tier is None:
            continue
        role = index.tag_value(name, "Role")
        ancestors = {obj.get("Name") for obj in index.chain(name)[1:]}
        for pool in ancestors & pools:
            members.setdefault(pool, []).append((name, int(tier), role))
    return members


def inherits_cells(
    members: dict[str, list[tuple[str, int, str | None]]],
    slices: dict[str, set[tuple[int, int] | None]],
    new_names: set[str],
) -> dict[tuple[str, str], tuple[int, int, int, int]]:
    """This fork's and vanilla's weight in each slice, plus the member counts behind them.

    The counts are carried alongside so a report can say "twenty-nine of fifty members" next to a
    share of ninety-three per cent, which is the pair that makes the number legible. Quoting either
    alone invites the mistake #494 was: reading a count as if it were a probability.
    """
    cells: dict[tuple[str, str], tuple[int, int, int, int]] = {}
    for pool, windows in sorted(slices.items()):
        pooled = members.get(pool, [])
        for window in sorted(windows, key=lambda w: (w is not None, w or ())):
            mine = vanilla = mine_count = vanilla_count = 0
            for name, tier, role in pooled:
                weight = slice_weight(tier, window, role)
                if name in new_names:
                    mine += weight
                    mine_count += 1
                else:
                    vanilla += weight
                    vanilla_count += 1
            if mine + vanilla:
                cells[(pool, slice_label(window))] = (
                    mine,
                    vanilla,
                    mine_count,
                    vanilla_count,
                )
    return cells


def share_of(cell: tuple[int, int, int, int]) -> float:
    """This fork's percentage of a slice, by weight."""
    mine, vanilla, _, _ = cell
    return mine / (mine + vanilla) * 100


def over_ceiling(
    cells: dict[tuple[str, str], tuple[int, int, int, int]],
) -> list[tuple[str, str]]:
    """Slices where this fork holds more than half the weight, most dominant first.

    Reported, never failed - see the note on CEILING_PERCENT. #481 decides what, if anything, to do
    about the level; this only makes it visible.
    """
    return sorted(
        (
            key
            for key, cell in cells.items()
            if cell[3] >= VANILLA_FLOOR and share_of(cell) > CEILING_PERCENT
        ),
        key=lambda key: -share_of(cells[key]),
    )


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
    cells: dict[tuple[str, str], tuple[int, int, int, int]],
    show_all: bool,
) -> None:
    """The inherited-membership side, which no tag and no table entry records.

    Printed even when nothing is remarkable, because the interesting number here is usually the one
    just under the line - and because a section that only appears on failure teaches nobody what it
    is measuring.
    """
    measurable = {k: v for k, v in cells.items() if v[3] >= VANILLA_FLOOR}
    breaches = over_ceiling(cells)
    # The floor binds on nothing today - every consumed pool carries far more than five vanilla
    # members - so saying "N measurable" every run would dress a no-op up as a filter. Mention it
    # only when it actually excludes something.
    skipped = len(cells) - len(measurable)
    unmeasured = f", {skipped} too thin on vanilla's side to measure" if skipped else ""
    print(
        f"\nInherited pool slices - {len(cells)} slice(s) across "
        f"{len({pool for pool, _ in cells})} pool(s){unmeasured}"
    )
    ranked = sorted(measurable, key=lambda key: -share_of(measurable[key]))
    for pool, label in ranked if show_all else ranked[:12]:
        mine, vanilla, mine_count, vanilla_count = measurable[(pool, label)]
        flag = "  OVER" if share_of((mine, vanilla, 0, 0)) > CEILING_PERCENT else ""
        print(
            f"  {pool + ':' + label:34} {share_of(measurable[(pool, label)]):5.1f}% by weight  "
            f"({mine_count} of {mine_count + vanilla_count} members){flag}"
        )
    if not show_all and len(ranked) > 12:
        print(f"  ... and {len(ranked) - 12} more (--all)")
    if breaches:
        print(
            f"\n  {len(breaches)} of {len(measurable)} slice(s) are over "
            f"{CEILING_PERCENT}% by weight. Reported, not enforced - completing a family across "
            "every\n  tier takes most of that family's pool, which is what this fork is for. "
            "#481 decides whether\n  any of it should change. docs/STYLEGUIDE.md 3.2.1."
        )


def inherits_snapshot_of(
    cells: dict[tuple[str, str], tuple[int, int, int, int]],
    members: dict[str, list[tuple[str, int, str | None]]],
    new_names: set[str],
) -> dict[str, dict]:
    """The comparable part of the inherited side: who this fork puts in each pool, and how far.

    Two different things drift and they want telling apart. Membership changes when a blueprint of
    mine starts or stops descending from a base - the thing no diff shows. The share changes when
    either side's content moves relative to a tier, including when a Qud patch adds items I have
    never seen. Pinning both means the failure message can say which happened.

    Membership is per pool rather than per slice because every slice of a pool holds every member;
    only the weights differ. Shares are rounded to whole percent so that ordinary content work does
    not churn the file for a tenth of a point.
    """
    snapshot: dict[str, dict] = {}
    for (pool, label), cell in sorted(cells.items()):
        mine = sorted(name for name, _, _ in members.get(pool, ()) if name in new_names)
        if not mine:
            continue
        entry = snapshot.setdefault(pool, {"mine": mine, "shares": {}})
        entry["shares"][label] = round(share_of(cell))
    return snapshot


def describe_inherits_drift(old: dict, new: dict) -> list[str]:
    """Every difference between two inherited-pool snapshots, as lines a person can act on."""
    out: list[str] = []
    for pool in sorted(set(old) | set(new)):
        if pool not in old:
            out.append(f"{pool}: this fork now reaches this inherited pool")
            continue
        if pool not in new:
            out.append(f"{pool}: this fork no longer reaches this inherited pool")
            continue
        was, now = set(old[pool]["mine"]), set(new[pool]["mine"])
        for name in sorted(now - was):
            out.append(f"{pool}: {name} now descends into this pool")
        for name in sorted(was - now):
            out.append(f"{pool}: {name} no longer descends into this pool")
        old_shares, new_shares = old[pool]["shares"], new[pool]["shares"]
        for label in sorted(set(old_shares) | set(new_shares)):
            before, after = old_shares.get(label), new_shares.get(label)
            if before is None:
                out.append(f"{pool}:{label}: slice is newly requested ({after}%)")
            elif after is None:
                out.append(
                    f"{pool}:{label}: slice is no longer requested (was {before}%)"
                )
            elif before != after:
                out.append(
                    f"{pool}:{label}: this fork's share moved {before}% -> {after}%"
                )
    return out


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
        help="list every inherited pool slice, not only the top of the ranking",
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
    slices = requested_inherits_slices(game)
    members = inherits_members(index, set(slices))
    cells = inherits_cells(members, slices, new_names)
    inherited = inherits_snapshot_of(cells, members, new_names)

    if args.snapshot:
        SNAPSHOT_PATH.write_text(
            json.dumps(snapshot_of(tables), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        INHERITS_SNAPSHOT_PATH.write_text(
            json.dumps(inherited, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(
            f"Wrote {SNAPSHOT_PATH} and {INHERITS_SNAPSHOT_PATH}. "
            "Review the diff before committing it."
        )
        return 0

    if args.check:
        for path in (SNAPSHOT_PATH, INHERITS_SNAPSHOT_PATH):
            if not path.exists():
                print(
                    f"ERROR - {path} is missing. Create it with:\n"
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
        inherited_drift = describe_inherits_drift(
            json.loads(INHERITS_SNAPSHOT_PATH.read_text(encoding="utf-8")), inherited
        )
        if inherited_drift:
            print(
                f"FAIL - {len(inherited_drift)} change(s) to inherited pool membership "
                "or share:",
                file=sys.stderr,
            )
            for line in inherited_drift:
                print(f"  {line}", file=sys.stderr)
            print(
                "\nNothing declares this membership - a blueprint joins by what it Inherits, so "
                "the cause is usually\nan Inherits= you changed, or a Qud update moving vanilla's "
                "own content. A share that moved on its\nown is the second. "
                f"[{CHECK_NAME}] docs/STYLEGUIDE.md 3.2.1.\nIf the change is intended:\n"
                "  python3 tools/report_dynamic_tables.py --snapshot",
                file=sys.stderr,
            )
            return 1
        pools = len(snapshot_of(tables))
        breaches = over_ceiling(cells)
        print(
            f"OK - dynamic pool membership matches {SNAPSHOT_PATH} across {pools} pool(s); "
            f"inherited membership and share match {INHERITS_SNAPSHOT_PATH} across "
            f"{len(cells)} slice(s), {len(breaches)} of them over {CEILING_PERCENT}% "
            "and reported only"
        )
        return 0

    print(f"{len(new_names)} blueprint(s) introduced by this mod\n")
    report(tables)
    report_inherits(cells, args.all)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
