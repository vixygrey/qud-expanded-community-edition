#!/usr/bin/env python3
"""Validate the shipped mod. Python 3 standard library only — no build step, no dependencies.

Run from the repository root:

    python3 tools/validate_mod.py            # fail on new violations
    python3 tools/validate_mod.py --all      # also list known inherited debt
    python3 tools/validate_mod.py --baseline # rewrite the baseline (deliberate, reviewed)

Known defects inherited from upstream 2.2 are enumerated in tools/validation-baseline.json with
the issue that tracks each one. They are reported but do not fail the run, so CI is green on a
codebase whose debt is already catalogued — while any *new* violation fails immediately.

The baseline is a ledger, not an excuse: it only shrinks. See docs/CHARTER.md, rule 4.
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
QUD_API_PATH = Path("tools/qud-api.json")

# Objects that exist to be inherited from, not to be spawned.
ABSTRACT_MARKERS = ("Base", "Projectile")

# New objects the mod declares WITHOUT the Raven_ prefix. They are new declarations, not vanilla
# replacements, so merge-discipline does not apply. Anything not listed here and not
# Raven_-prefixed is treated as a vanilla record.
#
# Keep this list minimal: an entry here is a hole in merge-discipline, so a stale name silently
# exempts anything later declared under it. Both remaining entries are body objects, unprefixed
# because vanilla's own BodyObject convention is the display name with spaces removed - the
# convention `TrueKin` itself sets (#13).
NEW_UNPREFIXED = {
    "TrueKin",
    "PsionicAdept",
}

# New population tables the mod declares. Same reasoning as NEW_UNPREFIXED.
NEW_TABLE_PREFIXES = ("StartingGear_",)

# Tier -> material, from docs/STYLEGUIDE.md 3.2. Longest first so "flawless crysteel"
# wins over "crysteel" and "folded carbide" over "carbide".
TIER_MATERIALS = [
    (7, "flawless crysteel"),
    (4, "folded carbide"),
    (8, "zetachrome"),
    (5, "fullerite"),
    (6, "crysteel"),
    (3, "carbide"),
    (0, "bronze"),
    (2, "steel"),
    (1, "iron"),
]

# Value doubles per tier. The base differs by slot: body armour runs 8 -> 2048 and vambraces
# 4 -> 1024 (half curve, partial slot); everything else 5 -> 1280.
VALUE_BASE_DEFAULT = 5
VALUE_BASE_BODY = 8
VALUE_BASE_VAMBRACE = 4

# Objects the curves genuinely do not describe. Each needs a reason, not just a name.
CURVE_EXEMPT = {
    # Vibro weapons are tier 5 at value 300 by their own convention, whatever the material.
    "vibro": "vibro weapons are tier 5 / value 300 by convention",
    # Cybernetic fists are granted by an implant and are not sold. Vanilla's own do not follow
    # the material table either - CarbideFist 3, FulleriteFist 4, CrysteelFist 7 - so they
    # track the implant rather than the metal.
    "fist": "cybernetic fists track the implant, not the material curve",
}

# Mura's original Workshop item. This fork publishes SEPARATELY and must never target it —
# uploading with this ID in workshop.json would publish over their page. See docs/PERMISSION.md §5.
UPSTREAM_WORKSHOP_ID = 1134036260

# Steam's own ceiling on a published item's description. Steamworks caps it at 8000 characters,
# and the installed mods agree: of the 72 that ship a workshop.json, the longest description is
# Caves of Qud Expanded's own at 7943 — right against the wall. Qud's uploader does not warn, so
# an over-long description is the kind of failure that only shows up on the published page.
STEAM_DESCRIPTION_MAX = 8000


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
    """The uploader publishes to whatever WorkshopId names. Two ways that goes wrong.

    It must never be Mura's item, which would publish over their page.

    And it must never be a placeholder. `0` is not "create a new item" — the uploader reads it as
    a lookup for item zero, fails with "Item not found", and offers no way forward (#163). An
    unpublished mod has **no WorkshopId key at all**: the uploader writes the file itself, via
    "Create Workshop Id for Mod...". Two of the installed mods ship one with the key absent; none
    ships a zero. Once published, Qud writes the real id here and it stays.
    """
    path = MOD / "workshop.json"
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return  # check_json reports this
    if "WorkshopId" not in data:
        return  # unpublished, and correctly so — the uploader writes the key
    workshop_id = data["WorkshopId"]
    if workshop_id == UPSTREAM_WORKSHOP_ID:
        f.add(
            "workshop-target",
            f"workshop.json WorkshopId is {UPSTREAM_WORKSHOP_ID} — Mura's original item. "
            f"Uploading would publish over their page. This fork releases separately.",
        )
    elif (
        not isinstance(workshop_id, int)
        or isinstance(workshop_id, bool)
        or workshop_id <= 0
    ):
        f.add(
            "workshop-target",
            f"workshop.json WorkshopId is {workshop_id!r}, which is not a Workshop item. "
            f'A placeholder does not mean "create a new item" — the uploader looks it up and '
            f"reports Item not found. Omit the key entirely until Steam assigns one.",
        )


def check_workshop_description(f: Findings) -> None:
    """The description must fit inside Steam's limit, with room to grow.

    Nothing local complains about an over-long one: the JSON stays valid, the mod still loads,
    and the truncation happens on Steam's side at upload. See docs/STYLEGUIDE.md §7.4.
    """
    path = MOD / "workshop.json"
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return  # check_json reports this
    length = len(data.get("Description", ""))
    if length > STEAM_DESCRIPTION_MAX:
        f.add(
            "workshop-description",
            f"workshop.json Description is {length} characters against Steam's "
            f"{STEAM_DESCRIPTION_MAX} limit. Steam truncates the overflow at upload without "
            f"reporting it. Cut it, or move the detail to CHANGELOG.md and link it.",
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
        f.add(
            "manifest",
            "manifest.json uses loadorder, deprecated as of build 210 — "
            "use LoadBefore / LoadAfter",
        )
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
                f.add(
                    "option-slider", f"{name}: Slider has no numeric Min ({raw_min!r})"
                )
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


def check_option_wiring(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """Every declared option must be read, and every option read must be declared.

    Both directions fail silently in game. A declared option appears in the menu and does nothing
    when changed; an option read but never declared makes Options.GetOption always return its
    fallback, so the feature is permanently stuck at its default. Neither produces an error.
    """
    declared: set[str] = set()
    for path, root in all_roots.items():
        if "option" in path.name.lower():
            declared |= {el.get("ID") for el in root.iter("option") if el.get("ID")}
    if not declared:
        return

    read: set[str] = set()
    for cs in (MOD / "Scripting").glob("*.cs"):
        read |= set(
            re.findall(r'"(Option[A-Za-z0-9_]+)"', cs.read_text(encoding="utf-8-sig"))
        )

    for missing in sorted(declared - read):
        f.add(
            "option-wiring",
            f"{missing} is declared but never read — the option will do nothing",
        )
    for undeclared in sorted(read - declared):
        f.add(
            "option-wiring",
            f"{undeclared} is read but never declared — GetOption will always return the fallback",
        )


JOPPA_SYSTEM = MOD / "Scripting" / "Raven_JoppaBuildingSystem.cs"


def check_joppa_sync(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """The Joppa removal system embeds the map patch's contents; keep them in step.

    Raven_JoppaBuildingSystem removes the building by exact (cell, blueprint) match, using a list
    generated from mod/Joppa.rpm. If the map is edited and that list is not regenerated, the
    option silently leaves the new objects behind — no error, just a half-removed building.
    """
    if not JOPPA_SYSTEM.is_file():
        return
    rpm = MOD / "Joppa.rpm"
    if not rpm.is_file():
        return

    try:
        root = parse(rpm)
    except ET.ParseError:
        return  # check_wellformed reports this
    in_map = {
        (int(c.get("X")), int(c.get("Y")), o.get("Name"))
        for c in root.iter("cell")
        for o in c.findall("object")
    }

    text = JOPPA_SYSTEM.read_text(encoding="utf-8-sig")
    block = re.search(r"PlacedObjects\s*=\s*\{(.*?)\};", text, re.DOTALL)
    if not block:
        f.add(
            "joppa-sync",
            "Raven_JoppaBuildingSystem has no PlacedObjects array to check",
        )
        return
    in_code = {
        (int(x), int(y), name)
        for x, y, name in re.findall(
            r'new Cel\((\d+),\s*(\d+),\s*"([^"]+)"\)', block.group(1)
        )
    }

    for missing in sorted(in_map - in_code):
        f.add(
            "joppa-sync",
            f"Joppa.rpm places {missing[2]} at {missing[0]},{missing[1]} but the removal system does not know about it",
        )
    for extra in sorted(in_code - in_map):
        f.add(
            "joppa-sync",
            f"the removal system expects {extra[2]} at {extra[0]},{extra[1]} but Joppa.rpm does not place it",
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
            f.add(
                "class-filename",
                f"{cs.name} declares {', '.join(classes)}, not {cs.stem}",
            )
    for path, root in roots.items():
        for part in root.iter("part"):
            name = part.get("Name", "")
            if name.startswith("Raven_Mod") and name not in defined:
                f.add(
                    "missing-script",
                    f"{path}: part {name} has no class in mod/Scripting/",
                )


def strip_cs_comments(src: str) -> list[str]:
    """Blank out C# comments, preserving line numbering.

    Required, not cosmetic: the scripts *document* the banned APIs — Raven_Options.cs says
    "no file I/O, no network, no reflection, no Harmony" — so scanning raw text reports the
    charter rule as a violation of itself.

    String literals are tracked so a `//` inside one is not mistaken for a comment. This is a
    drift detector for code the maintainer writes, not a defence against someone hiding an API
    call from it, so approximation is acceptable where malice is not the threat.
    """
    out: list[str] = []
    in_block = False
    for line in src.splitlines():
        buf, i, in_str, in_char, verbatim = [], 0, False, False, False
        while i < len(line):
            two = line[i : i + 2]
            if in_block:
                if two == "*/":
                    in_block, i = False, i + 2
                    buf.append("  ")
                    continue
                buf.append(" ")
                i += 1
                continue
            if in_str:
                if verbatim and two == '""':
                    buf.append(two)
                    i += 2
                    continue
                if not verbatim and line[i] == "\\":
                    buf.append(line[i : i + 2])
                    i += 2
                    continue
                if line[i] == '"':
                    in_str, verbatim = False, False
                buf.append(line[i])
                i += 1
                continue
            if in_char:
                if line[i] == "\\":
                    buf.append(line[i : i + 2])
                    i += 2
                    continue
                if line[i] == "'":
                    in_char = False
                buf.append(line[i])
                i += 1
                continue
            if two == "//":
                buf.append(" " * (len(line) - i))
                break
            if two == "/*":
                in_block, i = True, i + 2
                buf.append("  ")
                continue
            if line[i] == '"':
                in_str = True
                verbatim = i > 0 and line[i - 1] == "@"
                buf.append(line[i])
                i += 1
                continue
            if line[i] == "'":
                in_char = True
                buf.append(line[i])
                i += 1
                continue
            buf.append(line[i])
            i += 1
        out.append("".join(buf))
    return out


# Charter rule 5's hard limits, as patterns. Each entry cites the clause it enforces, because a
# banned-list without reasons is the kind of thing a future contributor deletes to make CI pass.
#
# These are NOT a security boundary - the maintainer writes this code, and anything here could be
# evaded trivially by someone trying. They catch drift: the accidental `File.ReadAllText` added
# while debugging, or a dependency that quietly pulls Harmony in.
#
# Comments are stripped before scanning, because the scripts legitimately *document* these APIs.
# String literals deliberately are NOT: `Type.GetType("System.IO.File")` is precisely how a token
# scan gets sidestepped, so a banned name in a string is worth a look. No current file trips it.
BANNED_CS = [
    (
        r"\bSystem\.IO\b|\bFile\.[A-Z]|\bDirectory\.[A-Z]|\b(?:File|Stream)(?:Reader|Writer|Stream)\b",
        "file I/O — rule 5: no file I/O outside the mod's own directory",
    ),
    (
        r"\bSystem\.Net\b|\bHttpClient\b|\bWebClient\b|\bWebRequest\b|\b(?:Tcp|Udp)Client\b|\bSocket\b",
        "network access — rule 5: no network access of any kind, or telemetry",
    ),
    (
        r"\bEnvironment\.GetEnvironmentVariable\b|\bEnvironment\.GetFolderPath\b|\bSpecialFolder\b|\bRegistry\b",
        "environment/player files — rule 5: no reading player files or the environment",
    ),
    (
        r"\bProcess\.Start\b|\bProcessStartInfo\b|\bSystem\.Diagnostics\.Process\b",
        "shelling out — rule 5: no shelling out, or loading external assemblies",
    ),
    (
        r"\bAssembly\.Load\w*\b|\bAppDomain\b",
        "external assemblies — rule 5: no shelling out, or loading external assemblies",
    ),
    (
        r"\bHarmony\w*\b",
        "Harmony — rule 5: breaks on arm64 macOS; every hook needed exists as a MinEvent",
    ),
    (
        r"\bSystem\.Reflection\b|\bBindingFlags\b|\.GetField\(|\.GetMethod\(|\.GetProperty\(|\.InvokeMember\(",
        "reflection — rule 5: public members and documented extension points only",
    ),
]


def check_scripting_policy(f: Findings) -> None:
    """Charter rule 5's hard limits, enforced instead of merely documented.

    Qud mods run with full process privileges and mod/Scripting/ triggers an approval prompt for
    every subscriber. Rule 5 calls that a trust relationship. Until this check existed the only
    thing holding the line was code review.
    """
    for cs in sorted((MOD / "Scripting").glob("*.cs")):
        lines = strip_cs_comments(cs.read_text(encoding="utf-8-sig"))
        for lineno, line in enumerate(lines, start=1):
            for pattern, why in BANNED_CS:
                hit = re.search(pattern, line)
                if hit:
                    f.add(
                        "scripting-policy",
                        f"{cs}:{lineno}: {hit.group(0)!r} — {why}",
                    )


def check_serializable_shape(f: Findings) -> None:
    """A [Serializable] type's instance fields are written into every player save.

    docs/CHARTER.md rule 5: "Anything [Serializable] is written into player saves. Its field layout is
    an identifier ... renaming or removing a field can break saves that already exist."

    Today every such type holds zero instance state - the 36 mutation stubs are empty and
    Raven_JoppaBuildingSystem is all static readonly - so save shape is trivially stable. This
    fires the moment that stops being true, which is the moment the obligation starts applying,
    rather than after a player's save has already broken.

    Adding state is allowed; rule 5 was widened deliberately in #46. This is not a veto, it asks
    that the layout be a considered, reviewed decision.

    Works on the brace-matched class body rather than line-by-line, so a field sharing a line with
    the class declaration is still seen. A miss here is a silent false negative, which is the
    expensive direction.
    """
    for cs in sorted((MOD / "Scripting").glob("*.cs")):
        text = "\n".join(strip_cs_comments(cs.read_text(encoding="utf-8-sig")))
        for m in re.finditer(
            r"\[\s*Serializable\s*\][\s\S]{0,400}?\b(?:class|struct)\s+([A-Za-z0-9_]+)",
            text,
        ):
            cls = m.group(1)
            brace = text.find("{", m.end())
            if brace < 0:
                continue
            depth, i = 0, brace
            while i < len(text):
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            body = text[brace + 1 : i]

            # Walk the body, collecting statements that sit directly in the class (depth 0).
            depth, stmt, start_off = 0, [], brace + 1
            for off in range(len(body)):
                ch = body[off]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                elif ch == ";" and depth == 0:
                    _report_field(f, cs, text, start_off, "".join(stmt), cls)
                    stmt, start_off = [], brace + 1 + off + 1
                    continue
                if depth == 0:
                    stmt.append(ch)
                else:
                    stmt.append(" ")


def _report_field(
    f: Findings, cs: Path, text: str, offset: int, stmt: str, cls: str
) -> None:
    """Flag one class-level statement if it declares a serialized instance field."""
    stmt = stmt.strip()
    if not stmt or stmt.startswith("["):
        return
    head = stmt.split("=", 1)[0]
    # A "(" before any "=" means a method or expression, not a field declaration.
    if "(" in head:
        return
    if re.search(r"\b(static|const)\b", head):
        return
    if not re.match(r"^(public|private|protected|internal|readonly|volatile)\b", stmt):
        return
    name = head.strip().split()[-1]
    lineno = text.count("\n", 0, offset) + 1
    f.add(
        "serializable-shape",
        f"{cs}:{lineno}: [Serializable] {cls} declares instance field {name!r} - its layout "
        f"is written into every save. See docs/CHARTER.md rule 5.",
    )


def check_subtype_tiles(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """Subtype tiles must exist on disk and be named for their affinity.

    Two failures, both silent in game rather than loud:

    A Tile pointing at a file that is not there renders as nothing, with no load error - the
    same class of silent breakage as an orphaned Load="Merge".

    And docs/STYLEGUIDE.md sets the texture convention `<affinity><Role>`, which 16 of the 18
    subtype tiles follow. The two that did not were named `corrosion*` for a subtype called
    "Corrosive" (#24), which is how a set of files stops being predictable from the thing it
    illustrates.

    Note the extension: Qud resolves a `.bmp` tile path against a `.png` asset. That mismatch
    is normal convention, not a bug - see docs/STYLEGUIDE.md 1.2.
    """
    for path, root in all_roots.items():
        for st in root.iter("subtype"):
            tile = st.get("Tile")
            name = st.get("Name") or "<unnamed>"
            if not tile:
                continue
            asset = MOD / "Textures" / Path(tile).with_suffix(".png")
            if not asset.is_file():
                f.add(
                    "subtype-tile", f"{path}: {name} tile {tile} has no file at {asset}"
                )
            affinity = name.split(",")[0].strip().lower()
            stem = Path(tile).stem
            match = re.match(r"([a-z]+)([A-Z]\w*)", stem)
            if match and affinity and match.group(1) != affinity:
                f.add(
                    "subtype-tile",
                    f"{path}: {name} uses tile {stem!r}, but the convention is "
                    f"<affinity><Role> - expected {affinity + match.group(2)!r}",
                )


def check_item_curves(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """Tier tags and prices must match the curves docs/STYLEGUIDE.md 3.2 states.

    Both curves are mechanical, which is exactly why drift goes unnoticed: a tier tag that is
    wrong puts an item in the wrong loot pool AND gives it the wrong mod capacity, and neither
    shows up as an error. This found two mispriced zetachrome weapons that the hand-written
    defect list in #9 had missed.

    Only the mod's own objects are priced, since vanilla sets its own values. Tier tags are
    checked on merges too, because the mod overriding a correct vanilla tier with a wrong one
    is the defect that started #9 (Flawless Crysteel Boots, tagged 3 against vanilla's 7).
    """
    for path, root in all_roots.items():
        for obj in root.iter("object"):
            name = obj.get("Name") or ""
            low = name.lower()
            if not name:
                continue
            exempt = next(
                (why for word, why in CURVE_EXEMPT.items() if word in low), None
            )
            if exempt:
                continue
            tier = next((t for t, mat in TIER_MATERIALS if mat in low), None)
            if tier is None:
                continue

            tag = next(
                (e.get("Value") for e in obj.iter("tag") if e.get("Name") == "Tier"),
                None,
            )
            if tag is not None and tag != str(tier):
                f.add(
                    "item-curve",
                    f"{path}: {name} is tier {tier} by material, but tagged Tier {tag}",
                )

            if not name.startswith("Raven_"):
                continue  # vanilla sets its own prices
            commerce = next(
                (e for e in obj.iter("part") if e.get("Name") == "Commerce"), None
            )
            if commerce is None or commerce.get("Value") is None:
                continue
            worn = next(
                (e.get("WornOn") for e in obj.iter("part") if e.get("Name") == "Armor"),
                None,
            )
            base = VALUE_BASE_DEFAULT
            if "vambrace" in low:
                base = VALUE_BASE_VAMBRACE
            elif worn == "Body":
                base = VALUE_BASE_BODY
            expected = base * (2**tier)
            actual = int(commerce.get("Value"))
            if actual != expected:
                f.add(
                    "item-curve",
                    f"{path}: {name} is tier {tier}, so the value curve gives "
                    f"{expected}, not {actual}",
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
            declares = (
                path.suffix == ".xml"
            )  # in a .rpm, <object Name="X"> PLACES X, it does
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


def load_qud_api() -> dict | None:
    """The committed snapshot of names Qud exposes. See tools/snapshot_qud_api.py."""
    if not QUD_API_PATH.exists():
        return None
    try:
        return json.loads(QUD_API_PATH.read_text())
    except json.JSONDecodeError:
        return None


def object_parts(root: ET.Element):
    """Only `<part>` elements belonging to an object blueprint.

    Conversations use `<part Name="…">` for a different system in a different namespace — vanilla
    has 55 of them, AskName and EndGame and the KithAndKin handlers. Scoping to objects is what
    keeps this check honest; an allowlist would rot.
    """
    for obj in root.iter("object"):
        yield from obj.iter("part")


def check_part_names(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """Every `<part Name="…">` must resolve to a real class.

    Qud silently ignores a part it cannot resolve: the object still loads, still validates, and
    simply does not do the thing you wrote. The mod's own Raven_Mod* parts are check_scripting_parts'
    job; this covers the vanilla ones.
    """
    api = load_qud_api()
    if api is None:
        f.add(
            "qud-api-snapshot",
            f"{QUD_API_PATH} is missing or unreadable - regenerate with "
            "tools/snapshot_qud_api.py (part and blueprint checks are skipped without it)",
        )
        return
    known = set(api["parts"])
    source = api.get("part_source", "unknown")
    for path, root in blueprint_sources(all_roots).items():
        for obj in root.iter("object"):
            owner = obj.get("Name") or "<unnamed>"
            for part in obj.iter("part"):
                name = part.get("Name")
                if not name or name.startswith("Raven_"):
                    continue
                if name not in known:
                    f.add(
                        "unknown-part",
                        f'{path}: {owner} uses <part Name="{name}">, which is not a part Qud '
                        f"provides - it will be ignored silently (snapshot source: {source}; "
                        f"if the part is real but unused by vanilla, regenerate with --assembly)",
                    )


def check_blueprint_refs(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """Blueprint-valued attributes must name a blueprint that exists.

    This is the check that would have caught #144's `GasObject="GasPoison"`: GasPoison is a *part*
    on the blueprint named PoisonGas, so the arrow fired and released nothing. Nothing errors, and
    nothing in the XML looks wrong.

    Only the attributes and contexts listed in the snapshot are checked, and each was included
    because it resolves for 100% of its values in vanilla's own data - a property the snapshot
    generator re-establishes every time it runs.
    """
    api = load_qud_api()
    if api is None:
        return  # already reported by check_part_names
    known = set(api["blueprints"])
    attrs = tuple(api["blueprint_attributes"])
    contexts = set(api["blueprint_contexts"])
    roots = blueprint_sources(all_roots)
    for root in roots.values():
        for obj in root.iter("object"):
            if obj.get("Name"):
                known.add(obj.get("Name"))
    for path, root in roots.items():
        for el in root.iter():
            if el.tag not in contexts:
                continue
            for attr in attrs:
                value = el.get(attr)
                if value and value not in known:
                    f.add(
                        "dangling-blueprint-ref",
                        f'{path}: <{el.tag} {attr}="{value}"> names no blueprint '
                        f"in vanilla or this mod",
                    )


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
    check_workshop_description(f)
    check_manifest(f)
    check_options(f, roots)
    check_option_wiring(f, roots)
    check_joppa_sync(f, roots)
    check_filenames(f)
    check_merge_discipline(f, roots)
    check_scripting_parts(f, roots)
    check_scripting_policy(f)
    check_subtype_tiles(f, roots)
    check_item_curves(f, roots)
    check_serializable_shape(f)
    check_reachability(f, roots)
    check_table_targets(f, roots)
    check_part_names(f, roots)
    check_blueprint_refs(f, roots)
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
