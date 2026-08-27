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
        """The blueprint and its `Inherits=` ancestors, nearest first. Cycles terminate.

        LINEAGE, not lookup. This is what `GameObjectBlueprint.DescendsFrom` models - it walks
        `ShallowParent`, which is the `Inherits` parent and nothing else - so this is the right
        chain for asking what pools a blueprint belongs to. **A `<mixin>` does not confer
        membership**, and following one here would put 66 golems in the `Creature` pool.

        For asking what value reaches a blueprint, use `lookup_chain`: mixins do carry tags, parts
        and stats, and reading them through this method missed 143 vanilla blueprints that are
        excluded from dynamic encounters by a mixin (#526).
        """
        seen: set[str] = set()
        out: list[ET.Element] = []
        while name and name in self.objects and name not in seen:
            seen.add(name)
            out.append(self.objects[name])
            name = self.objects[name].get("Inherits")
        return out

    def lookup_chain(self, name: str, kind: str) -> list[ET.Element]:
        """Every blueprint that can supply a `<kind>` child to `name`, highest precedence first.

        `<mixin Name="X" />` is a second inheritance mechanism and the loader applies it with the
        same `Inherit()` call as `Inherits=`, so a mixin's tags, parts and stats reach the
        blueprint exactly as an ancestor's do. Following only `Inherits=` made `BaseVehicleGolem`
        and `BaseChiliadCreatureStats` invisible, and with them the `ExcludeFromDynamicEncounters`
        that keeps 143 vanilla blueprints out of every dynamic pool (#526).

        Precedence is the loader's, which applies Fill mixins first, then `Inherits`, then ordinary
        mixins, then the blueprint's own children - each overwriting what came before. Reversed
        into nearest-first that is: own, ordinary mixins, the `Inherits` chain, Fill mixins.

        `Include` / `Exclude` on a mixin filter by child-node kind, comma-delimited, and propagate
        to everything that mixin brings with it - vanilla uses this once, as
        `<mixin Name="Creature" Exclude="part" />`. `Priority` orders them, lower first.

        All four attributes are documented on the wiki's Modding:Objects page, which
        `docs/WIKI.md` has indexed since #509. I did not read it, and derived this from the loader
        instead - see docs/LESSONS.md.

        `*noinherit` needs no special handling here: the loader strips such a tag after each merge,
        so it confines the tag to its declarer whichever mechanism carried it, and the existing
        depth check in `has_tag` still expresses that.
        """
        out: list[ET.Element] = []
        seen: set[str] = set()

        def walk(name: str | None) -> None:
            if not name or name in seen or name not in self.objects:
                return
            seen.add(name)
            obj = self.objects[name]
            out.append(obj)
            # Priority orders the mixins, lower first - `Mixin.CompareTo` is
            # `Priority.CompareTo(Other.Priority)` and the loader sorts before applying. No
            # vanilla blueprint sets it, so every mixin is priority 0 today and this is stable
            # sorting on equal keys; modelled anyway because the wiki documents the attribute.
            mixins = sorted(
                (m for m in obj.findall("mixin") if self._mixin_supplies(m, kind)),
                key=lambda m: int(m.get("Priority") or 0),
            )
            for m in mixins:
                if m.get("Load") != "Fill":
                    walk(m.get("Name"))
            walk(obj.get("Inherits"))
            for m in mixins:
                if m.get("Load") == "Fill":
                    walk(m.get("Name"))

        walk(name)
        return out

    @staticmethod
    def _mixin_supplies(mixin: ET.Element, kind: str) -> bool:
        """Whether `mixin` may contribute a `<kind>` child, per its Include/Exclude filters."""
        include = mixin.get("Include")
        exclude = mixin.get("Exclude")
        if include and kind not in [p.strip() for p in include.split(",")]:
            return False
        return not (exclude and kind in [p.strip() for p in exclude.split(",")])

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
        for depth, obj in enumerate(self.lookup_chain(name, "tag")):
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
        for depth, obj in enumerate(self.lookup_chain(name, "tag")):
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
        for obj in self.lookup_chain(name, "part"):
            for el in obj.findall("part"):
                if el.get("Name") == part and el.get(attr) is not None:
                    return el.get(attr)
        return None

    def has_part(self, name: str, part: str) -> bool:
        """True when `part` is declared anywhere on the chain. Parts have no `*noinherit`."""
        return any(
            el.get("Name") == part
            for obj in self.lookup_chain(name, "part")
            for el in obj.findall("part")
        )

    def prop_value(self, name: str, key: str) -> str | None:
        """The value `<property Name="key">` resolves to on `name`, or None.

        Properties are the other half of a lookup the game treats as one. `GameObjectFactory`
        reads `<property>` into `GameObjectBlueprint.Props`, and every consumer that matters here
        checks both stores - the population weighting asks
        `Tags.TryGetValue("Role", ...) || Props.TryGetValue("Role", ...)`. Reading only tags means
        a value declared the other way is invisible, which is how thirteen of this fork's items
        came to be weighted a hundred times too heavily (#520).

        `{{{remove}}}` and `*delete` are the loader's two erasures, checked as substrings because
        that is how it checks them. Properties have no `*noinherit`.
        """
        for obj in self.lookup_chain(name, "property"):
            for el in obj.findall("property"):
                if el.get("Name") == key:
                    value = el.get("Value")
                    if value is not None and (
                        "{{{remove}}}" in value or "*delete" in value
                    ):
                        return None
                    return value
        return None

    def has_stat(self, name: str, stat: str) -> bool:
        """True when `stat` is declared anywhere on the chain, whatever it carries.

        The game's `HasStat`, and separate from `stat_attr` because the difference between them is
        load-bearing. `<stat Name="Level" sValue="18-20" />` declares Level with no numeric
        `Value`: `HasStat` is true, `BaseValue` is left at zero, and the blueprint lands in tier 1
        rather than having no tier at all. Thirty-two vanilla villagers are shaped that way.
        """
        return any(
            el.get("Name") == stat
            for obj in self.lookup_chain(name, "stat")
            for el in obj.findall("stat")
        )

    def stat_attr(self, name: str, stat: str, attr: str) -> str | None:
        """The nearest declaration of `stat`'s `attr` on the chain, or None.

        The stat-shaped twin of `part_attr`, and it exists for `Level`: a blueprint with no `Tier`
        tag takes its tier from `Level`, which is how every creature in the game is tiered.

        Nearest-per-attribute rather than nearest-whole-node, because that is what the loader does
        - `ObjectBlueprintXMLChildNode.Merge` copies attributes one key at a time, so a child
        adding `sValue` to an inherited `Value` keeps both.
        """
        for obj in self.lookup_chain(name, "stat"):
            for el in obj.findall("stat"):
                if el.get("Name") == stat and el.get(attr) is not None:
                    return el.get(attr)
        return None


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
