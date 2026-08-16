#!/usr/bin/env python3
"""Validate the shipped mod. Python 3 standard library only — no build step, no dependencies.

Run from the repository root:

    python3 tools/validate_mod.py            # fail on new violations
    python3 tools/validate_mod.py --all      # also list known inherited debt
    python3 tools/validate_mod.py --baseline # rewrite the baseline (deliberate, reviewed)

Known defects inherited from upstream 2.2 are enumerated in tools/validation-baseline.json with
the issue that tracks each one. They are reported but do not fail the run, so CI is green on a
codebase whose debt is already catalogued — while any *new* violation fails immediately.

The baseline is a ledger, not an excuse: it only shrinks. See CLAUDE.md, charter rule 4.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MOD = Path("mod")
BASELINE_PATH = Path("tools/validation-baseline.json")

# Objects that exist to be inherited from, not to be spawned.
ABSTRACT_MARKERS = ("Base", "Projectile")

# New objects the mod declares WITHOUT the Raven_ prefix. Documented in docs/FEATURES.md as
# exceptions to the prefix rule; they are new declarations, not vanilla replacements, so
# merge-discipline does not apply. Anything not listed here and not Raven_-prefixed is treated
# as a vanilla record.
NEW_UNPREFIXED = {
    "SteelFist",
    "TrueKin",
    "Yttrian",
    "PsionicAdept",
}

# New population tables the mod declares. Same reasoning as NEW_UNPREFIXED.
NEW_TABLE_PREFIXES = ("StartingGear_",)

# Mura's original Workshop item. This fork publishes SEPARATELY and must never target it —
# uploading with this ID in workshop.json would publish over their page. See docs/PERMISSION.md §5.
UPSTREAM_WORKSHOP_ID = 1134036260


class Findings:
    def __init__(self) -> None:
        self.items: list[tuple[str, str]] = []

    def add(self, check: str, detail: str) -> None:
        self.items.append((check, detail))


def xml_files() -> list[Path]:
    return sorted([*MOD.rglob("*.xml"), *MOD.rglob("*.rpm")])


def parse(path: Path):
    """Parse, tolerating the UTF-8 BOM the mod's files carry."""
    return ET.fromstring(path.read_text(encoding="utf-8-sig"))


# --------------------------------------------------------------------------- checks


def check_wellformed(f: Findings) -> dict[Path, ET.Element]:
    """Every XML and map file must parse. This is the check that would have caught #5."""
    roots: dict[Path, ET.Element] = {}
    for path in xml_files():
        try:
            roots[path] = parse(path)
        except ET.ParseError as exc:
            f.add("wellformed", f"{path}: {exc}")
    return roots


def check_json(f: Findings) -> None:
    for path in sorted(MOD.rglob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            f.add("json", f"{path}: {exc}")


def check_workshop_target(f: Findings) -> None:
    """The uploader publishes to whatever WorkshopId names. It must never be Mura's.

    0 means "create a new item". Once this fork is published, Qud writes its own ID here, which
    is fine — the only forbidden value is the upstream one.
    """
    path = MOD / "workshop.json"
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return  # check_json reports this
    if data.get("WorkshopId") == UPSTREAM_WORKSHOP_ID:
        f.add(
            "workshop-target",
            f"workshop.json WorkshopId is {UPSTREAM_WORKSHOP_ID} — Mura's original item. "
            f"Uploading would publish over their page. This fork releases separately.",
        )


def check_manifest(f: Findings) -> None:
    """manifest.json carries mod identity, and two fields have consequences beyond display.

    `id` is what other mods name in LoadBefore / LoadAfter, so changing it breaks their ordering
    declarations. `author` is where charter rule 3's credit obligation lives in machine-readable
    form, and must name Mura.
    """
    path = MOD / "manifest.json"
    if not path.is_file():
        f.add("manifest", "mod/manifest.json is missing — no id, version, or author")
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return  # check_json reports this
    for key in ("id", "title", "version", "author", "description"):
        if not data.get(key):
            f.add("manifest", f"manifest.json is missing required key: {key}")
    if "loadorder" in {k.lower() for k in data}:
        f.add("manifest", "manifest.json uses loadorder, deprecated as of build 210 — "
                          "use LoadBefore / LoadAfter")
    author = str(data.get("author", ""))
    if "Mura" not in author:
        f.add("manifest", "manifest.json author does not credit Mura — charter rule 3")


def check_options(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """Guard the slider constraint that crashes Qud.

    A Type="Slider" option whose Min is above 1 sends Qud's options menu into unbounded
    recursion: opening Options -> Mods crashes the game with a stack overflow and no usable
    diagnostic. Verified by bisection (Min=6 crashes, Min=0 does not), and corroborated by every
    one of the 13 sliders across the 87 mods installed locally using 0 or 1. See issue #51.

    This is a bug in the game, not in the mod, which is exactly why it needs a guard here: the
    crash points nowhere near the change that caused it.
    """
    for path, root in all_roots.items():
        if "option" not in path.name.lower():
            continue
        for el in root.iter("option"):
            if el.get("Type") != "Slider":
                continue
            name = el.get("ID", "<no ID>")
            raw_min = el.get("Min")
            try:
                minimum = int(raw_min)
            except (TypeError, ValueError):
                f.add("option-slider", f"{name}: Slider has no numeric Min ({raw_min!r})")
                continue
            if minimum not in (0, 1):
                f.add(
                    "option-slider",
                    f'{name}: Slider Min="{minimum}" crashes Qud\'s options menu. '
                    f"Must be 0 or 1 — see issue #51",
                )
            # A Default outside the range is the other way a slider ends up in a state the UI
            # was never asked to render.
            try:
                default, maximum = int(el.get("Default")), int(el.get("Max"))
            except (TypeError, ValueError):
                f.add("option-slider", f"{name}: Slider needs numeric Default and Max")
                continue
            if not minimum <= default <= maximum:
                f.add(
                    "option-slider",
                    f'{name}: Default="{default}" is outside Min="{minimum}"..Max="{maximum}"',
                )


def check_filenames(f: Findings) -> None:
    """Spaces force quoting in every script, hook and CI step. STYLEGUIDE.md section 3."""
    for path in MOD.rglob("*"):
        if path.is_file() and " " in path.name:
            f.add("filename-space", str(path))


def blueprint_sources(roots: dict[Path, ET.Element]):
    """Only .xml declares blueprints. A .rpm places already-declared objects into map cells, so
    its <object Name="Bed"> is a reference, not a redeclaration."""
    return {p: r for p, r in roots.items() if p.suffix == ".xml"}


def check_merge_discipline(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """Charter rule 1, mechanically enforced.

    Any record whose name lacks the fork's Raven_ prefix is a vanilla record, so touching it
    without Load="Merge" replaces it outright — conflicting with other mods and silently
    discarding future vanilla additions. This is the check that would have caught #3 on the
    commit that introduced it.
    """
    roots = blueprint_sources(all_roots)
    for path, root in roots.items():
        for tag, kind in (("object", "object"), ("population", "table")):
            for el in root.iter(tag):
                name = el.get("Name")
                if not name or name.startswith("Raven_"):
                    continue
                if name in NEW_UNPREFIXED or name.startswith(ABSTRACT_MARKERS):
                    continue
                if tag == "population" and name.startswith(NEW_TABLE_PREFIXES):
                    continue
                if el.get("Load") != "Merge":
                    f.add(
                        "merge-discipline",
                        f'{path}: <{tag} Name="{name}"> replaces a vanilla {kind}',
                    )


def check_scripting_parts(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """Every Raven_Mod* part referenced by a blueprint needs a matching C# class."""
    roots = blueprint_sources(all_roots)
    defined = set()
    for cs in (MOD / "Scripting").glob("*.cs"):
        classes = re.findall(
            r"public\s+(?:static\s+|sealed\s+|abstract\s+|partial\s+)*class\s+(\w+)",
            cs.read_text(encoding="utf-8-sig"),
        )
        defined.update(classes)
        # STYLEGUIDE.md section 5: one public class per file, filename == class name.
        if classes and cs.stem not in classes:
            f.add("class-filename", f"{cs.name} declares {', '.join(classes)}, not {cs.stem}")
    for path, root in roots.items():
        for part in root.iter("part"):
            name = part.get("Name", "")
            if name.startswith("Raven_Mod") and name not in defined:
                f.add(
                    "missing-script",
                    f"{path}: part {name} has no class in mod/Scripting/",
                )


def check_reachability(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """Every new blueprint must be obtainable: in a population table, or tinkerable.

    This is the check that surfaces #6 (72 unreachable chips) and #7 (9 unreachable armor
    pieces).
    """
    roots = blueprint_sources(all_roots)
    defined: dict[str, Path] = {}
    tinkerable: set[str] = set()
    for path, root in roots.items():
        for obj in root.iter("object"):
            name = obj.get("Name")
            if not name or not name.startswith("Raven_") or obj.get("Load") == "Merge":
                continue
            if any(m in name for m in ABSTRACT_MARKERS):
                continue
            defined[name] = path
            if any(p.get("Name") == "TinkerItem" for p in obj.iter("part")):
                tinkerable.add(name)

    # An object is reachable if ANYTHING references it: a population table (Blueprint=), a map
    # file placing it into a cell, or another object pointing at it (e.g. a cybernetic's
    # FistObject=). Checking only Blueprint= reported Joppa's furniture and the cybernetic fist
    # replacements as unobtainable, which they are not.
    referenced: set[str] = set()
    for path, root in all_roots.items():
        for el in root.iter():
            declares = path.suffix == ".xml"  # in a .rpm, <object Name="X"> PLACES X, it does
            for key, value in el.attrib.items():  # not declare it
                if declares and key == "Name" and el.tag in ("object", "population"):
                    continue  # a declaration is not a reference to itself
                referenced.add(value)
    in_tables = referenced

    for name, path in sorted(defined.items()):
        if name not in in_tables and name not in tinkerable:
            f.add(
                "unreachable",
                f"{name} ({path.name}) is in no population table and has no TinkerItem",
            )


def check_table_targets(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """A table entry naming a Raven_ blueprint that doesn't exist can never spawn."""
    roots = blueprint_sources(all_roots)
    defined = set()
    for root in roots.values():
        for obj in root.iter("object"):
            if obj.get("Name"):
                defined.add(obj.get("Name"))
    for path, root in roots.items():
        for el in root.iter():
            bp = el.get("Blueprint")
            if bp and bp.startswith("Raven_") and bp not in defined:
                f.add("dangling-blueprint", f"{path}: table references undefined {bp}")


# --------------------------------------------------------------------------- runner

CHECKS = (
    ("json", check_json),
    ("filenames", check_filenames),
)


def run() -> Findings:
    f = Findings()
    roots = check_wellformed(f)
    check_json(f)
    check_workshop_target(f)
    check_manifest(f)
    check_options(f, roots)
    check_filenames(f)
    check_merge_discipline(f, roots)
    check_scripting_parts(f, roots)
    check_reachability(f, roots)
    check_table_targets(f, roots)
    return f


def load_baseline() -> set[str]:
    if not BASELINE_PATH.exists():
        return set()
    data = json.loads(BASELINE_PATH.read_text())
    return {
        f"{k}␟{item}" for k, entry in data["known"].items() for item in entry["items"]
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--all",
        action="store_true",
        help="list known inherited debt as well as new violations",
    )
    ap.add_argument(
        "--baseline",
        action="store_true",
        help="rewrite the baseline from the current tree",
    )
    args = ap.parse_args()

    if not MOD.is_dir():
        print("error: run from the repository root (mod/ not found)", file=sys.stderr)
        return 2

    findings = run()

    if args.baseline:
        grouped: dict[str, list[str]] = {}
        for check, detail in findings.items:
            grouped.setdefault(check, []).append(detail)
        payload = {
            "_comment": (
                "Known defects inherited from upstream 2.2. Reported but not failing, so new "
                "violations are visible. This ledger only shrinks - remove entries as the "
                "referenced issues are fixed. Regenerate deliberately, never to silence a new "
                "failure."
            ),
            "known": {
                k: {"issue": "", "items": sorted(v)} for k, v in sorted(grouped.items())
            },
        }
        BASELINE_PATH.write_text(json.dumps(payload, indent=2) + "\n")
        print(f"wrote {BASELINE_PATH} with {len(findings.items)} entries")
        return 0

    baseline = load_baseline()
    new = [(c, d) for c, d in findings.items if f"{c}␟{d}" not in baseline]
    known = [(c, d) for c, d in findings.items if f"{c}␟{d}" in baseline]

    if args.all and known:
        print(f"Known inherited debt ({len(known)}), tracked in {BASELINE_PATH}:")
        for check, detail in sorted(known):
            print(f"  [{check}] {detail}")
        print()

    if new:
        print(f"FAIL - {len(new)} new violation(s):", file=sys.stderr)
        for check, detail in sorted(new):
            print(f"  [{check}] {detail}", file=sys.stderr)
        print(
            "\nIf a violation is a deliberate, reviewed exception, fix the cause instead. "
            "The baseline is for inherited debt only.",
            file=sys.stderr,
        )
        return 1

    print(f"OK - no new violations ({len(known)} known inherited defect(s) tracked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
