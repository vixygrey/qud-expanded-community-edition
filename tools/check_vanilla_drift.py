#!/usr/bin/env python3
"""Compare the mod against the *installed* vanilla game data.

This cannot run in CI — GitHub runners have no copy of Caves of Qud — so it is a maintainer tool.
**Run it after every Qud update.** It catches the two failure modes that are otherwise invisible:

1. **Orphaned merges.** A `Load="Merge"` whose target no longer exists in vanilla does not error.
   It silently stops applying, and the mod quietly loses that edit. `docs/STYLEGUIDE.md` §1.
2. **Anatomy drift.** `TrueKin` and `PsionicAdept` are full copies of vanilla's `Humanoid`,
   because Qud anatomies cannot inherit — none of the 78 vanilla anatomies uses any inheritance
   mechanism. So when vanilla adds a body part to `Humanoid`, those two silently do not get it,
   and characters of those genotypes are missing a slot every other humanoid has.

Usage:
    python3 tools/check_vanilla_drift.py [--game PATH]
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MOD = Path("mod")

# Steam on macOS. The game data is under CoQ.app/Contents/Resources/Data — NOT under
# CoQ_Data/StreamingAssets, which contains only DLC and is an easy wrong turn.
DEFAULT_GAME_PATHS = [
    "~/Library/Application Support/Steam/steamapps/common/Caves of Qud/CoQ.app/Contents/Resources/Data/StreamingAssets/Base",
    "~/.steam/steam/steamapps/common/Caves of Qud/CoQ_Data/StreamingAssets/Base",
    "C:/Program Files (x86)/Steam/steamapps/common/Caves of Qud/CoQ_Data/StreamingAssets/Base",
]

# Anatomies the mod defines as copies of a vanilla anatomy, and the vanilla anatomy each copies.
# Values are the extra part types the copy is *supposed* to add.
ANATOMY_COPIES = {
    "TrueKin": ("Humanoid", {"Chip Interface"}),
    "PsionicAdept": ("Humanoid", {"Chip Interface"}),
}


def find_game(explicit: str | None) -> Path | None:
    for candidate in ([explicit] if explicit else []) + DEFAULT_GAME_PATHS:
        if not candidate:
            continue
        p = Path(os.path.expanduser(candidate))
        if (p / "Bodies.xml").is_file():
            return p
    return None


INVALID_REF = re.compile(r"&#x?[0-9A-Fa-f]+;")


def _valid_codepoint(n: int) -> bool:
    return n in (0x9, 0xA, 0xD) or 0x20 <= n <= 0xD7FF or 0xE000 <= n <= 0xFFFD


def parse(path: Path, lenient: bool = False) -> ET.Element:
    """Parse, optionally tolerating vanilla's non-conformant character references.

    Vanilla data embeds control characters as numeric refs (&#11;, &#15;, &#27;, &#x7;) which
    Qud's own parser accepts and XML 1.0 forbids. Five vanilla files use them, including
    Items.xml, which defines most of the objects the mod merges into. Stripping them is safe
    here: this tool only reads *names*, never text content.

    Applied to vanilla only. The mod's own files are held to the strict standard by
    tools/validate_mod.py.
    """
    text = path.read_text(encoding="utf-8-sig")
    if lenient:
        text = INVALID_REF.sub(
            lambda m: (
                ""
                if not _valid_codepoint(
                    int(m.group()[3:-1], 16)
                    if m.group()[2] in "xX"
                    else int(m.group()[2:-1])
                )
                else m.group()
            ),
            text,
        )
    return ET.fromstring(text)


def load_all(root_dir: Path, lenient: bool = False) -> list[ET.Element]:
    """Load every XML file. Unparsable files are reported, never silently skipped — swallowing
    them makes every record they define look absent, which reads as hundreds of false defects."""
    out, failed = [], []
    for p in sorted(root_dir.rglob("*.xml")):
        try:
            out.append(parse(p, lenient=lenient))
        except ET.ParseError as exc:
            failed.append(f"{p.name}: {exc}")
    if failed:
        print(
            f"WARNING: {len(failed)} file(s) could not be parsed; results are incomplete:",
            file=sys.stderr,
        )
        for f in failed:
            print(f"  {f}", file=sys.stderr)
        print(file=sys.stderr)
    return out


class BlueprintIndex:
    """Blueprint lookups resolved through `Inherits`, honouring `*noinherit`.

    Qud has two inheritance rules for tags and this resolves both. A tag declared on a blueprint
    applies to everything inheriting from it — *except* when its value is `*noinherit`, which
    confines it to the blueprint that declares it. That is how `Raven_Base Psionic Pistol` marks
    itself a base object without making its nine descendants base objects too.

    Matching on tag name alone gets those descendants exactly backwards. Resolving
    `IsEligibleForDynamicEncounters` over the mod's psionic firearms returns 0 of 20 without the
    rule and 18 of 20 with it — a silent zero, which is the failure `docs/LESSONS.md` describes
    under *A search that finds nothing has two explanations*. See #265.

    Takes parsed roots rather than a path, so it works over the mod's own XML with no game
    installed. `tools/validate_mod.py` runs in CI where there is none.
    """

    def __init__(self, roots: list[ET.Element]) -> None:
        self.objects: dict[str, ET.Element] = {}
        for root in roots:
            for obj in root.iter("object"):
                name = obj.get("Name")
                if name:
                    self.objects[name] = obj

    def chain(self, name: str) -> list[ET.Element]:
        """The blueprint and its ancestors, nearest first. Cycles terminate rather than hang."""
        seen: set[str] = set()
        out: list[ET.Element] = []
        while name and name in self.objects and name not in seen:
            seen.add(name)
            out.append(self.objects[name])
            name = self.objects[name].get("Inherits")
        return out

    def has_tag(self, name: str, tag: str) -> bool:
        """True when `tag` reaches `name`, whether declared on it or inherited.

        The nearest declaration decides, and two values are directives rather than data. They are
        the only two: across every vanilla blueprint, tag values beginning with `*` are
        `*noinherit` (951) and `*delete` (126), plus a bare `*` twice that is an ordinary wildcard
        value on `PaintWith` and `Species`.

        `*noinherit` confines the tag to the blueprint declaring it - found on an ancestor it means
        the tag stops there, found on `name` itself it still applies. That is how
        `Raven_Base Psionic Pistol` marks itself a base without making its descendants bases.

        `*delete` removes an inherited tag outright, so it is false wherever it is found. Vanilla
        uses it to take `Corpse` out of `DynamicObjectsTable:Items` and `FoldingChair` out of
        `:Trinkets`, among 126 others. Missing it made this over-report - counting blueprints as
        pool members that the game had explicitly removed (#261).
        """
        for depth, obj in enumerate(self.chain(name)):
            for el in obj.findall("tag"):
                if el.get("Name") == tag:
                    value = el.get("Value")
                    if value == "*delete":
                        return False
                    return not (depth > 0 and value == "*noinherit")
        return False

    def tag_value(self, name: str, tag: str) -> str | None:
        """The value `tag` resolves to on `name`, or None when it does not reach it.

        Same two directives as `has_tag`, and for the same reasons: `*delete` removes an inherited
        tag outright, `*noinherit` confines one to the blueprint declaring it. Returning None for
        both keeps this the value-shaped twin of that method rather than a second set of rules.
        """
        for depth, obj in enumerate(self.chain(name)):
            for el in obj.findall("tag"):
                if el.get("Name") == tag:
                    value = el.get("Value")
                    if value == "*delete" or (depth > 0 and value == "*noinherit"):
                        return None
                    return value
        return None

    def part_attr(self, name: str, part: str, attr: str) -> str | None:
        """The nearest declaration of `part`'s `attr` on the chain, or None.

        Nearest wins, which is what makes this work over a `Load="Merge"` blueprint: the merge
        declares only what it changes, so a value the mod overrides is found on the mod's own
        element and one it leaves alone falls through to the ancestor. Parts have no `*noinherit`.
        """
        for obj in self.chain(name):
            for el in obj.findall("part"):
                if el.get("Name") == part and el.get(attr) is not None:
                    return el.get(attr)
        return None

    def has_part(self, name: str, part: str) -> bool:
        """True when `part` is declared anywhere on the chain. Parts have no `*noinherit`."""
        return any(
            el.get("Name") == part
            for obj in self.chain(name)
            for el in obj.findall("part")
        )


def anatomy(roots: list[ET.Element], name: str) -> ET.Element | None:
    for r in roots:
        for a in r.iter("anatomy"):
            if a.get("Name") == name:
                return a
    return None


def signature(el: ET.Element, depth: int = 0) -> list[tuple]:
    out = []
    for p in el.findall("part"):
        out.append((depth, p.get("Type"), p.get("Laterality"), p.get("DependsOn")))
        out += signature(p, depth + 1)
    return out


def check_anatomy_drift(mod_roots, van_roots) -> list[str]:
    problems = []
    for copy_name, (vanilla_name, added) in ANATOMY_COPIES.items():
        mine = anatomy(mod_roots, copy_name)
        theirs = anatomy(van_roots, vanilla_name)
        if mine is None:
            problems.append(f"anatomy {copy_name} not found in the mod")
            continue
        if theirs is None:
            problems.append(
                f"vanilla anatomy {vanilla_name} not found — did Qud rename it?"
            )
            continue
        mine_sig = [p for p in signature(mine) if p[1] not in added]
        for part in signature(theirs):
            if part not in mine_sig:
                problems.append(
                    f"{copy_name} is missing a part vanilla {vanilla_name} has: "
                    f"{part[1]}{' (' + part[2] + ')' if part[2] else ''}"
                )
    return problems


def check_merge_targets(mod_roots, van_roots) -> list[str]:
    """Every Load=\"Merge\" must name a record vanilla still defines."""
    van_objects, van_tables, van_anatomies, van_genotypes = set(), set(), set(), set()
    for r in van_roots:
        for el in r.iter("object"):
            van_objects.add(el.get("Name"))
        for el in r.iter("population"):
            van_tables.add(el.get("Name"))
        for el in r.iter("anatomy"):
            van_anatomies.add(el.get("Name"))
        for el in r.iter("genotype"):
            van_genotypes.add(el.get("Name"))

    buckets = {
        "object": van_objects,
        "population": van_tables,
        "anatomy": van_anatomies,
        "genotype": van_genotypes,
    }
    problems = []
    for r in mod_roots:
        for tag, known in buckets.items():
            for el in r.iter(tag):
                if el.get("Load") != "Merge":
                    continue
                name = el.get("Name")
                if name and name not in known:
                    problems.append(
                        f'<{tag} Name="{name}" Load="Merge"> has no vanilla target — '
                        f"the edit is silently not applying"
                    )
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--game", help="path to StreamingAssets/Base")
    args = ap.parse_args()

    game = find_game(args.game)
    if game is None:
        print(
            "Could not find the installed game data. Pass --game PATH pointing at\n"
            "StreamingAssets/Base (on macOS this lives inside CoQ.app/Contents/Resources/Data,\n"
            "not under CoQ_Data/StreamingAssets, which holds only DLC).",
            file=sys.stderr,
        )
        return 2

    print(f"vanilla data: {game}\n")
    van_roots = load_all(game, lenient=True)
    mod_roots = load_all(MOD)

    problems = check_merge_targets(mod_roots, van_roots) + check_anatomy_drift(
        mod_roots, van_roots
    )
    if problems:
        print(f"DRIFT — {len(problems)} problem(s):", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1

    print(
        'No drift. Every Load="Merge" target exists in vanilla, and the copied anatomies'
    )
    print("match vanilla's apart from their added slots.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
