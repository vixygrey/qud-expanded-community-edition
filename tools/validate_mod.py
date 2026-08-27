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

# Prefixes the mod owns. Raven_ is Mura's attribution, carried by everything inherited from CoQE;
# Vixy_ marks content added to this fork. docs/STYLEGUIDE.md §3.1 has the reasoning - it is a credit
# line, not namespace hygiene. Every check below needs only one thing from a prefix: "ours, not
# vanilla's", so both belong in the same tuple.
#
# Adding a prefix here without adding it to every site is the failure this constant exists to
# prevent: four of the six sites fail SILENTLY when a prefix is missing, by skipping the object
# rather than reporting it (#224).
MOD_PREFIXES = ("Raven_", "Vixy_")

# The tag prefix that self-registers a blueprint into a spawn pool without any PopulationTables.xml
# entry. docs/STYLEGUIDE.md §3.3 covers when to reach for it over an explicit entry.
DYNAMIC_TABLE_PREFIX = "DynamicObjectsTable:"

# The tag that gates a blueprint's dynamic-encounter eligibility on a mod option, with no C#
# involved. Its value is an option ID, optionally prefixed with "!" to invert.
OPTION_GATE_TAG = "ExcludeFromDynamicEncountersOption"

# New objects the mod declares WITHOUT one of the MOD_PREFIXES. They are new declarations, not
# vanilla replacements, so merge-discipline does not apply. Anything not listed here and not
# mod-prefixed is treated as a vanilla record.
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
# 4 -> 1024 (half curve, partial slot); everything else 5 -> 1280. Chips run a quarter curve at
# 1.25 -> 320, per docs/STYLEGUIDE.md 3.2.1: they are not equipment, their slot competes with
# nothing, and they cannot be bought.
# The four elemental resistances an Armor part can state, matching RESISTANCES in
# tools/snapshot_qud_api.py. No curve describes them, so a merge never states one (#380).
RESISTANCES = ("Heat", "Cold", "Acid", "Elec")

VALUE_BASE_DEFAULT = 5
VALUE_BASE_BODY = 8
VALUE_BASE_VAMBRACE = 4
VALUE_BASE_CHIP = 1.25


def tier_of(obj: ET.Element, name: str) -> int | None:
    """An object's tier: its `Tier` tag first, the material word in its name only as a fallback.

    This order matters and it used to be the other way round. Matching a material word finds a
    tier for anything named after a metal and `None` for everything else, so an object with an
    explicit `<tag Name="Tier">` was skipped before its price was ever compared - which is how
    all 144 psionic chips sat twenty times under the curve without failing anything (#354). The
    tag is what the curve is actually about; the material word is a convenience for the objects
    that predate it.

    Returns None only when neither is present, which is the one case where there is genuinely no
    tier to check against.
    """
    tag = next(
        (e.get("Value") for e in obj.iter("tag") if e.get("Name") == "Tier"), None
    )
    if tag is not None:
        try:
            return int(tag)
        except ValueError:
            return None
    low = name.lower()
    return next((t for t, mat in TIER_MATERIALS if mat in low), None)


def is_base_object(obj: ET.Element) -> bool:
    """True for a template blueprint rather than a real item.

    Qud marks these with `<tag Name="BaseObject" Value="*noinherit" />` - the value confines the
    tag to the blueprint declaring it, so descendants are real objects. Nothing spawns a base, so
    pricing one against the curve is meaningless. This only started mattering when tier resolution
    stopped depending on a material word: `Raven_Base Psionic Pistol` carries `Tier` 3 and no
    metal in its name, so it was previously invisible to the price check by accident.
    """
    return any(
        e.get("Name") == "BaseObject" and e.get("Value") == "*noinherit"
        for e in obj.findall("tag")
    )


# Every psionic chip inherits this one blueprint - all 144 of them, with nothing else doing so.
CHIP_BASE = "Raven_Base Psionic Chip"


def is_chip(obj: ET.Element, name: str) -> bool:
    """True for a psionic chip, by inheritance rather than by name.

    Deliberately not a name match. Matching "chip" in the blueprint name is the same class of
    mistake as finding a tier by its material word, which is what #354 is about: it happens to
    work today and silently stops working the moment something is named differently. All 144
    chips declare `Inherits="Raven_Base Psionic Chip"` and nothing else does.
    """
    return obj.get("Inherits") == CHIP_BASE


def material_tier_of(name: str) -> int | None:
    """The tier a blueprint's own name claims, or None when it names no material."""
    low = name.lower()
    return next((t for t, mat in TIER_MATERIALS if mat in low), None)


# AV ceiling per slot, from docs/STYLEGUIDE.md 3.2.1. Vanilla's best ORDINARY item in each slot -
# named artefacts break vanilla's own ceiling on purpose and are not a benchmark this fork may
# match. Shields carry AV on a `Shield` part rather than an `Armor` one, which is why they need
# their own entry: a survey filtered on `Armor` misses all fourteen of vanilla's.
AV_CEILING = {
    "Body": 8,
    "Head": 4,
    "Hands": 4,
    "Feet": 4,
    "Back": 2,
    "Arm": 1,
    "Face": 2,
    "Floating Nearby": 1,
}
# Shields need a ceiling per TIER, not one number for the slot. Vanilla's shield line is
# AV = tier + 1 up to tier 3 and AV = tier from tier 5 - not one formula, so the ceiling is
# vanilla's own value where vanilla ships a shield, extended to 8 at tier 8 because vanilla ships
# none there. Greatshields sit one above the shield at their tier, paid for in weight and DV.
# A single per-slot number would let a tier-2 greatshield pass at the tier-8 ceiling.
AV_CEILING_SHIELD = {0: 3, 1: 3, 2: 4, 3: 5, 4: 6, 5: 6, 6: 7, 7: 8, 8: 9}

# Highest MEAN damage vanilla ships per family, tier and handedness, from docs/STYLEGUIDE.md
# 3.2.1. Keyed (skill, two_handed) -> tier -> mean. A tier absent from a family's row is one
# vanilla does not ship, and is not checked: there is no ceiling to be under.
DAMAGE_CEILING = {
    ("ShortBlades", False): {
        0: 1.5,
        1: 2.0,
        2: 3.5,
        3: 4.5,
        4: 4.5,
        5: 5.5,
        6: 6.5,
        7: 7.5,
        8: 8.5,
    },
    # Vanilla ships no two-handed short blade, so this row has no vanilla weapon to measure.
    # It is derived instead: the midpoint between the dagger line and the two-handed long sword
    # line at each tier - above its own tree's one-handed line, below the two-handed line of the tree
    # above. Added with the spear in #342, because a family the ceiling skips is a family
    # nothing protects.
    ("ShortBlades", True): {
        0: 2.5,
        1: 3.0,
        2: 4.0,
        3: 5.0,
        4: 6.0,
        5: 7.0,
        6: 8.0,
        7: 9.0,
        8: 11.0,
    },
    ("LongBlades", False): {
        0: 2.0,
        1: 2.5,
        2: 3.5,
        3: 4.5,
        4: 5.5,
        5: 6.5,
        6: 7.0,
        7: 8.0,
        8: 9.0,
    },
    ("LongBlades", True): {
        0: 3.5,
        1: 4.5,
        2: 5.5,
        3: 6.5,
        4: 7.0,
        5: 8.0,
        6: 9.0,
        7: 11.0,
        8: 13.0,
    },
    ("Axe", False): {
        0: 1.5,
        1: 2.0,
        2: 3.0,
        3: 3.5,
        4: 4.5,
        5: 5.5,
        6: 6.5,
        7: 7.5,
        8: 8.5,
    },
    ("Axe", True): {2: 4.5, 3: 5.5, 4: 6.5, 5: 7.5, 6: 8.5, 7: 9.5, 8: 10.5},
    ("Cudgel", False): {
        0: 2.0,
        1: 2.0,
        2: 3.0,
        3: 4.0,
        4: 5.0,
        5: 6.0,
        6: 7.0,
        7: 7.5,
        8: 8.5,
    },
    ("Cudgel", True): {2: 5.0, 3: 6.0, 4: 7.0, 5: 9.0, 6: 8.5, 7: 10.5, 8: 14.0},
}

# The blueprints a Finesse tag reaches that roll penetration against Strength must say so in a
# RulesDescription, and one that rolls against anything else must not - the tag is inert there.
FINESSE_TAG = "Finesse"
FINESSE_TEXT = "Finesse:"


def curve_exempt(obj: ET.Element, name: str) -> str | None:
    """Why the value curve does not describe this object, or None when it does.

    The curve is **this fork's** convention rather than vanilla's - `item-curve` prices only
    Raven_ and Vixy_ objects because "vanilla sets its own values". So the test for an exemption is
    not whether vanilla follows the curve; it is whether this mod ever has, in that category.

    Measured across every priced object this fork ships: melee weapons 63 of 73 on the curve and
    armour 50 of 62, against **0 of 5** ranged weapons, **0 of 4** energy cells and 0 of 1 trinket.
    A category the convention has never once described is not 22 defects; it is a category the
    convention does not cover. #373.

    Checked by part composition rather than by a word in the name, because a name match is the
    failure #354 removed from tier detection and there is no reason to reintroduce it here.
    """
    low = name.lower()
    for word, why in CURVE_EXEMPT.items():
        if word in low:
            return why

    parts = {e.get("Name") for e in obj.findall("part")}
    if "MissileWeapon" in parts:
        # Vanilla agrees, for whatever that is worth: none of its 64 missile weapons sits on the
        # curve either, at a median of 2.5x and a range of 0 to 25.
        return "ranged weapons have never followed the curve, in this mod or in vanilla"
    if "EnergyCell" in parts:
        return "cells are priced by charge, not by tier"
    if "Backpack" in parts:
        return "containers are priced by what they carry"
    if any(e.get("Name") == "Trinket" for e in obj.findall("tag")):
        return "a trinket is priced against its vanilla sibling, not the curve"

    armor = next((e for e in obj.findall("part") if e.get("Name") == "Armor"), None)
    if armor is not None and not (armor.get("AV") or "").strip("0 "):
        # An Armor part granting no AV is a slot occupier - a utility artifact wearing an armour
        # slot - and the curve prices protection.
        return "grants no AV, so it is a slot occupier rather than armour"
    return None


# Objects the curves genuinely do not describe. Each needs a reason, not just a name.
CURVE_EXEMPT = {
    # Vibro weapons are tier 5 at value 300 by their own convention, whatever the material.
    "vibro": "vibro weapons are tier 5 / value 300 by convention",
    # Cybernetic fists are granted by an implant and are not sold. Vanilla's own do not follow
    # the material table either - CarbideFist 3, FulleriteFist 4, CrysteelFist 7 - so they
    # track the implant rather than the metal.
    "fist": "cybernetic fists track the implant, not the material curve",
    # Deliberate round numbers rather than drift, kept as chosen (#373). The nanoweave set is 300
    # against a curve of 320 and the mutating mask 1000 against 1280 - close enough that flattening
    # them would be satisfying a rule at the cost of a number somebody picked.
    "nanoweave": "300 is a chosen round number, not drift from 320",
    "mutating mask": "1000 is a chosen round number, not drift from 1280",
    # Kindle and Frost Webs override CanLevel() to false and read their level nowhere, so a higher
    # grade of either chip grants exactly what the basic one does (#347). All three grades of each
    # are priced at the tier-4 floor of 20 rather than the 80 and 320 their own tiers would give,
    # because the chip curve prices what a chip grants and these grant the same thing. The tier
    # tags stay as they are - they place the chip in its loot pool, and the pools are correct.
    "kindle": "every grade grants the same thing, so all three are priced at the floor (#347)",
    "frost webs": "every grade grants the same thing, so all three are priced at the floor (#347)",
}

# Mura's original Workshop item. This fork publishes SEPARATELY and must never target it —
# uploading with this ID in workshop.json would publish over their page. See docs/PERMISSION.md §5.
UPSTREAM_WORKSHOP_ID = 1134036260

# Attributes that belong to the `<part>` element rather than to the part class, so they are valid
# on every part and resolve against no member. Read from the snapshot when it carries them; this
# is the fallback for an older snapshot. See ELEMENT_ATTRS in tools/snapshot_qud_api.py for the
# evidence behind each name.
ELEMENT_ATTRS = ("Name", "Namespace", "ChanceOneIn", "Reflector", "Builder")

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
    # Steam's limit is BYTES, not characters, and this description is full of em dashes at three
    # bytes each. Measuring characters passed a 7,963-character description that was 8,019 bytes,
    # and Steam rejected the upload with k_EResultInvalidParam - a check giving a false pass at
    # exactly the moment it was meant to be useful.
    length = len(data.get("Description", "").encode("utf-8"))
    if length > STEAM_DESCRIPTION_MAX:
        f.add(
            "workshop-description",
            f"workshop.json Description is {length} bytes against Steam's "
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

    check_version_matches_changelog(f, str(data.get("version", "")))


def check_version_matches_changelog(f: Findings, version: str) -> None:
    """manifest.json's version and CHANGELOG.md's newest released heading must agree.

    The version lives in three places by hand - here, the changelog, and the git tag - and nothing
    held any two of them together. Bumping one and forgetting another is an ordinary mistake that
    ships a stale version to every subscriber's mod list.

    The tag is deliberately not part of this. At the moment a release commit lands, the manifest
    and the changelog both say the new version and the tag does not exist yet, so including it
    would fail the very commit that creates a release. Two of the three is what can be held
    honestly; the third is a line on the release checklist (#309).
    """
    changelog = Path("CHANGELOG.md")
    if not version or not changelog.is_file():
        return
    released = [
        m.group(1)
        for m in re.finditer(
            r"^## \[([^\]]+)\]", changelog.read_text(encoding="utf-8"), re.MULTILINE
        )
        if m.group(1).lower() != "unreleased"
    ]
    if not released:
        f.add(
            "manifest", "CHANGELOG.md has no released version heading to check against"
        )
        return
    if released[0] != version:
        f.add(
            "manifest",
            f"manifest.json version is {version!r} but CHANGELOG.md's newest release is "
            f"{released[0]!r} - bump both together, or roll [Unreleased] into a new heading",
        )


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


def check_option_defaults(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """An option's Default is the value the game reads until the player touches it.

    Options.GetOption returns the stored value, then the XML Default, then the caller's fallback --
    so the C# fallback only ever applies to an option that is not declared at all. Whatever is in
    Default is what Raven_Options.Enabled compares against, and it compares against "Yes".

    A Checkbox stores exactly "Yes" or "No":

        Options.SetOption(option.ID, (Options.GetOption(option.ID) == "Yes") ? "No" : "Yes");

    Anything else is simply not "Yes" and reads as off. `Default="false"` therefore worked, and
    worked by accident (#443). `Default="true"` would not: an option meant to default on would ship
    off, the checkbox would render unchecked, and nothing would error.

    The Combo half is preventative -- every Combo in this file is correct today. A Default that is
    not one of the option's own Values leaves the option reading a value the menu cannot show, which
    fails the same silent way.
    """
    for path, root in all_roots.items():
        if "option" not in path.name.lower():
            continue
        for option in root.iter("option"):
            ident = option.get("ID", "?")
            kind = option.get("Type")
            default = option.get("Default")
            if kind == "Checkbox" and default not in ("Yes", "No"):
                f.add(
                    "option-default",
                    f'{path}: {ident} is a Checkbox with Default="{default}" — a Checkbox stores '
                    f'"Yes" or "No", so anything else reads as off however it was meant',
                )
            elif kind in ("Combo", "BigCombo"):
                values = (option.get("Values") or "").split(",")
                if default not in values:
                    f.add(
                        "option-default",
                        f'{path}: {ident} has Default="{default}", which is not one of its '
                        f"Values ({', '.join(values)})",
                    )


def check_option_wiring(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """Every declared option must be read, and every option read must be declared.

    Both directions fail silently in game. A declared option appears in the menu and does nothing
    when changed; an option read but never declared makes Options.GetOption always return its
    fallback, so the feature is permanently stuck at its default. Neither produces an error.

    There are two ways to read one, and only counting the first reported the creature-variants
    option as dead when it was wired the whole time (#171). C# calling `Options.GetOption` is the
    usual route. The other is data: a `<tag Name="ExcludeFromDynamicEncountersOption">` value names
    an option ID that `GameObjectBlueprint.IsExcludedFromDynamicEncounters` resolves itself, with a
    leading `!` inverting it. Vanilla ships that path unused, so it is easy to forget it exists -
    which is the argument for encoding it here rather than remembering it.
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
    for root in all_roots.values():
        for tag in root.iter("tag"):
            if tag.get("Name") != OPTION_GATE_TAG:
                continue
            value = (tag.get("Value") or "").lstrip("!")
            if value:
                read.add(value)

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

    Any record whose name lacks one of the fork's prefixes (MOD_PREFIXES) is a vanilla record, so touching it
    without Load="Merge" replaces it outright — conflicting with other mods and silently
    discarding future vanilla additions. This is the check that would have caught #3 on the
    commit that introduced it.
    """
    roots = blueprint_sources(all_roots)
    for path, root in roots.items():
        for tag, kind in (("object", "object"), ("population", "table")):
            for el in root.iter(tag):
                name = el.get("Name")
                if not name or name.startswith(MOD_PREFIXES):
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


def _naming_roots(all_roots: dict[Path, ET.Element]) -> dict[Path, ET.Element]:
    """Qud resolves modded XML by root element, not filename — so this is `<naming>`, not
    `Naming.xml`. STYLEGUIDE.md section 1."""
    return {p: r for p, r in all_roots.items() if r.tag == "naming"}


def _load_mode(node: ET.Element, inherited: str | None) -> str | None:
    """LoadNamingNode and every level below: `Reader.GetAttribute("Load") ?? LoadMode`."""
    return node.get("Load") or inherited


def check_naming_discipline(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """Charter rule 1 for `<naming>`, which check_merge_discipline does not reach.

    That check walks `<object>` and `<population>` only, so a `<namestyle Name="Qudish">` without
    Load="Merge" passes CI today. The consequence is worse than the one merge-discipline guards
    against. LoadNameStyleNode's replacement branch removes the style from _NameStyleList, builds
    a fresh one, writes it to _NameStyleTable and **never adds it back to the list** — and
    Generate iterates the list. So the namestyle does not lose its pools, it leaves name
    generation entirely, surviving only for `Base=` lookups. Doing that to Qudish takes every
    procedurally named human in the game with it, each one coming back as the literal string
    "NameGenFail1", "NameGenFail2", and so on.

    Scopes are matched by Name, so a merged `<scope Name="General">` rewrites vanilla's in place
    rather than adding one. A new scope on a vanilla namestyle needs a mod-prefixed Name.
    """
    for path, root in _naming_roots(all_roots).items():
        file_mode = _load_mode(root, None)
        for styles_node in root:
            if styles_node.tag != "namestyles":
                continue
            styles_mode = _load_mode(styles_node, file_mode)
            for style in styles_node:
                if style.tag != "namestyle":
                    continue
                name = style.get("Name", "")
                style_mode = _load_mode(style, styles_mode)
                vanilla = not name.startswith(MOD_PREFIXES)
                if vanilla and style_mode != "Merge":
                    f.add(
                        "naming-merge-discipline",
                        f'{path}: <namestyle Name="{name}"> removes a vanilla namestyle from '
                        f"name generation",
                    )
                    continue
                for child in style:
                    child_mode = _load_mode(child, style_mode)
                    if vanilla and child_mode != "Merge":
                        f.add(
                            "naming-merge-discipline",
                            f'{path}: <{child.tag}> under vanilla namestyle "{name}" '
                            f"discards vanilla's entries",
                        )
                    if child.tag != "scopes" or not vanilla:
                        continue
                    for scope in child:
                        sname = scope.get("Name", "")
                        if not sname.startswith(MOD_PREFIXES):
                            f.add(
                                "naming-merge-discipline",
                                f'{path}: <scope Name="{sname}"> on vanilla namestyle "{name}" '
                                f"rewrites vanilla's scope — scopes merge by Name, so a new one "
                                f"needs a mod prefix",
                            )


def check_naming_syllables(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """Two silent failures in a new namestyle, plus the ASCII line the builder already held.

    Amount defaults to "0" and Format to "AsIs" on a fresh NameStyle, so a new style that omits
    them generates the empty string rather than erroring. A merge omits Amount deliberately —
    the loader only assigns it when the attribute is non-empty, so vanilla's survives.

    ASCII is not a preference. Vanilla is 3,074 syllables for 3,074 across all 148 namestyles,
    with no exceptions, and diacritics are a font-rendering risk in Qud's tileset.
    """
    pools = ("prefixes", "infixes", "postfixes")
    for path, root in _naming_roots(all_roots).items():
        for style in root.iter("namestyle"):
            name = style.get("Name", "")
            new_style = name.startswith(MOD_PREFIXES)
            if new_style and not style.get("Base") and not style.get("Format"):
                f.add(
                    "naming-amounts",
                    f'{path}: new namestyle "{name}" states no Format, so it defaults to '
                    f'"AsIs" and its names arrive lowercase',
                )
            for child in style:
                if child.tag in pools and new_style and not child.get("Amount"):
                    f.add(
                        "naming-amounts",
                        f'{path}: <{child.tag}> on new namestyle "{name}" states no Amount, '
                        f'which defaults to "0" — the pool is never drawn from',
                    )
                for el in child:
                    syllable = el.get("Name", "")
                    if any(ord(c) > 127 for c in syllable):
                        f.add(
                            "naming-ascii",
                            f'{path}: non-ASCII syllable "{syllable}" in "{name}"',
                        )


def check_naming_priority(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """A combining scope at Priority 0 is a landmine, and it looks like vanilla's own default.

    Generate's weighted draw skips every entry at Priority <= 0. With one combining candidate the
    `case 1:` branch ignores Priority entirely, which is why vanilla's Qudish survives at 0 — it
    is the only General-scope namestyle in the file. Add a second and the total goes to zero, and
    a creature's name comes back as the literal string "NameGenFail<n>".

    The ceiling is the same test read the other way. Exclusion is `other.priority > scope.priority`,
    so a combining scope at 100 does not lose to the faction styles that sit at exactly 100 with
    Combine="false" — it displaces them, and female Templars stop being named like Templars.
    """
    for path, root in _naming_roots(all_roots).items():
        for style in root.iter("namestyle"):
            name = style.get("Name", "")
            if not name.startswith(MOD_PREFIXES):
                continue
            for scope in style.iter("scope"):
                if scope.get("Combine") != "true":
                    continue
                priority = int(scope.get("Priority", "0"))
                sname = scope.get("Name", "")
                if priority <= 0:
                    f.add(
                        "naming-priority",
                        f'{path}: <scope Name="{sname}"> on "{name}" combines at Priority '
                        f"{priority}, which the weighted draw skips — two such scopes return "
                        f'"NameGenFail<n>" as a creature\'s name',
                    )
                elif priority >= 100:
                    f.add(
                        "naming-priority",
                        f'{path}: <scope Name="{sname}"> on "{name}" combines at Priority '
                        f"{priority}, displacing the faction namestyles at 100",
                    )


def check_naming_option_coverage(
    f: Findings, all_roots: dict[Path, ET.Element]
) -> None:
    """The syllables the option can switch off must be exactly the syllables the XML adds.

    Nothing at runtime can tell a merged-in syllable from a vanilla one -- the loader appends both
    into the same List and neither carries a marker -- and reading the XML back would be file I/O,
    which charter rule 5 forbids. So `Raven_Options.cs` restates the list, and the two halves live
    in different files with neither naming the other. That is the shape #421 came from, and
    skill-option-coverage exists for the same reason.

    Held in both directions:

      a syllable in the XML but not the C#  -> a syllable the option cannot switch off
      a syllable in the C# but not the XML  -> the option zeroes a weight on something else,
                                               which for a vanilla syllable means silencing it
    """
    arrays = {
        "prefixes": "AddedPrefixes",
        "infixes": "AddedInfixes",
        "postfixes": "AddedPostfixes",
    }
    source = MOD / "Scripting" / "Vixy_NameSyllables.cs"
    if not source.is_file():
        return
    text = source.read_text(encoding="utf-8-sig")

    declared: dict[str, set[str]] = {}
    for pool, array in arrays.items():
        match = re.search(rf"string\[\]\s+{array}\s*=\s*\{{(.*?)\}};", text, re.DOTALL)
        declared[pool] = (
            set(re.findall(r'"([^"]+)"', match.group(1))) if match else set()
        )

    for path, root in _naming_roots(all_roots).items():
        for style in root.iter("namestyle"):
            if style.get("Name") != "Qudish":
                continue
            for pool, array in arrays.items():
                node = style.find(pool)
                in_xml = {el.get("Name") for el in node} if node is not None else set()
                for missing in sorted(in_xml - declared[pool]):
                    f.add(
                        "naming-option-coverage",
                        f"{path}: {pool[:-2]} {missing!r} is added to Qudish but absent from "
                        f"{array} — the option cannot switch it off",
                    )
                for extra in sorted(declared[pool] - in_xml):
                    f.add(
                        "naming-option-coverage",
                        f"{source}: {array} names {extra!r}, which Qudish does not add — "
                        f"the option would zero the weight on something it does not own",
                    )


def check_duplicate_children(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """Within one <object>, no two named children may share a Name.

    Qud does not keep both and does not drop the object. ObjectBlueprintXMLChildNodeCollection.Add
    reports the duplicate and then merges the second into the first, so a later attribute silently
    overwrites an earlier one -- which on four vibro weapons destroyed the charge description and
    left only the Finesse line (#448).

    The XML is well-formed either way, so nothing else here or in prettier had an opinion. The only
    thing that ever noticed was the game, which writes MODERROR to its log on every launch.

    Worth knowing how it arrived: `finesse-visible` requires a Finesse tag and its rules text to
    imply each other, so satisfying it meant adding a RulesDescription -- and on these four, one
    already existed. A check demanding text is what deleted other text.
    """
    named = ("part", "tag", "stat", "mutation", "skill", "intproperty", "property")
    for path, root in blueprint_sources(all_roots).items():
        for obj in root.iter("object"):
            for tag in named:
                seen: dict[str, int] = {}
                for child in obj.findall(tag):
                    name = child.get("Name")
                    if name:
                        seen[name] = seen.get(name, 0) + 1
                for name, count in sorted(seen.items()):
                    if count > 1:
                        f.add(
                            "duplicate-child",
                            f'{path}: <object Name="{obj.get("Name")}"> has {count} '
                            f'<{tag} Name="{name}"> - Qud merges them, so the later one\'s '
                            f"attributes overwrite the earlier one's",
                        )


def check_scripting_parts(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """Every mod-prefixed part referenced by a blueprint needs a matching C# class.

    Widened from Mod* to the whole prefix in #146. Until then every script here was a mutation
    stub, so Mod* covered them all — but a part named Vixy_AmmoPayload would have fallen between
    this check and check_part_names, which skips mod-prefixed names on the grounds that this one
    covers them. A part naming a class that does not exist loads as nothing at all.
    """
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
            if name.startswith(MOD_PREFIXES) and name not in defined:
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
    # An expression-bodied member declares no field at all - the compiler emits a method or a
    # get-only property with no backing storage, so nothing reaches the save. #411 added the first
    # of these: `protected override string VariantBlueprint => "Icy Vapor";`. Checked before the
    # "=" split, because "=>" would otherwise read as an assignment and the head as a field.
    if "=>" in stmt:
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
            if curve_exempt(obj, name):
                continue
            tier = tier_of(obj, name)
            if tier is None:
                continue

            # The tag wins for pricing, but a name that claims a different metal is still a
            # defect worth reporting - it is how Flawless Crysteel Boots came to be tagged 3.
            by_material = material_tier_of(name)
            if by_material is not None and by_material != tier:
                f.add(
                    "item-curve",
                    f"{path}: {name} is tier {by_material} by material, but tagged Tier {tier}",
                )

            if not name.startswith(MOD_PREFIXES):
                continue  # vanilla sets its own prices
            if is_base_object(obj):
                continue  # a base is a template, not an item anyone can hold
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
            curve = "value curve"
            if is_chip(obj, name):
                base = VALUE_BASE_CHIP
                curve = "chip curve"
            elif "vambrace" in low:
                base = VALUE_BASE_VAMBRACE
            elif worn == "Body":
                base = VALUE_BASE_BODY
            expected = int(base * (2**tier))
            actual = int(commerce.get("Value"))
            if actual != expected:
                f.add(
                    "item-curve",
                    f"{path}: {name} is tier {tier}, so the {curve} gives "
                    f"{expected}, not {actual}",
                )


def check_stat_discipline(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """`MeleeWeapon.Stat` is Strength on a new weapon, and a merge never states it at all.

    docs/STYLEGUIDE.md 3.2.1. `Stat=` names the stat penetration rolls against, and the damage
    die is rolled once per penetration, so it multiplies a weapon's whole output rather than
    adding to it. Vanilla declares `MeleeWeapon` 402 times: 191 Strength, 208 unset, 3 Ego, and
    Agility never. This fork had 61 on Agility before #321.

    The two halves are different rules. A new weapon may state Strength or leave it unset - the
    `MeleeWeapon.Stat` field is initialised to "Strength", and vanilla itself omits the attribute on
    208 of its 402 declarations, so requiring it would report 28 correct weapons. What is refused is
    any other value, which is the whole defect class: all 61 of #321's swaps were explicit.

    A merge states nothing at all, which is stricter, and deliberately. CI has no game, so the check
    cannot tell a merge that restates vanilla's value from one that changes it - and the second is
    the defect. Refusing the attribute outright is a line the check can actually hold, and it costs
    nothing, because a merge restating vanilla's own value changes nothing by definition. It also
    protects the three vanilla weapons that roll against Ego, which a flat "always Strength" rule
    would have quietly rewritten.

    Parses rather than greps, deliberately. mod/ObjectBlueprints/MeleeWeapons.xml carries a
    commented-out block holding two vibro war hammers that still declare Stat="Agility"; they are
    inert, and a line-based check would report two violations nobody can fix without touching code
    marked for rework. ElementTree does not see inside a comment.
    """
    for path, root in all_roots.items():
        for obj in root.iter("object"):
            name = obj.get("Name") or ""
            if not name:
                continue
            for part in obj.findall("part"):
                if part.get("Name") != "MeleeWeapon":
                    continue
                stat = part.get("Stat")
                if obj.get("Load") == "Merge":
                    if stat is not None:
                        f.add(
                            "stat-discipline",
                            f"{path}: {name} is a merge and states Stat={stat!r} - a merge never "
                            f"changes what vanilla decided the weapon rolls against",
                        )
                elif (
                    name.startswith(MOD_PREFIXES)
                    and stat is not None
                    and stat != "Strength"
                ):
                    f.add(
                        "stat-discipline",
                        f"{path}: {name} states Stat={stat!r}; a new weapon rolls penetration "
                        f"against Strength, and a Finesse tag is how one rewards Agility",
                    )


def check_armor_curve(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """No item may exceed vanilla's best ordinary item in its slot.

    docs/STYLEGUIDE.md 3.2.1. There is no AV *curve* to check against - vanilla's tier-4 body
    armour runs AV 0 to 5, so per-item values overlap far too heavily for a per-tier rule to
    exist. What vanilla has is a ceiling per slot, and that is what the findings turn on: #318
    and #319 are both ceiling violations.

    Merges are checked as well as new objects, because raising a vanilla piece's AV is how most of
    the drift happened - Crysteel Shardmail 6 -> 8, Zetachrome Lune 8 -> 10, and the whole
    Zetachrome Apex/Gloves/Pumps set 4 -> 6. A merge that states an AV is asserting that number
    whatever vanilla said.

    Shields are looked up separately because they carry AV on a `Shield` part rather than an
    `Armor` one - the omission that shipped the first version of 3.2.1 without a Shield column.
    """
    for path, root in all_roots.items():
        for obj in root.iter("object"):
            name = obj.get("Name") or ""
            if not name or is_base_object(obj):
                continue
            for part in obj.findall("part"):
                kind = part.get("Name")
                if kind not in ("Armor", "Shield"):
                    continue
                raw = part.get("AV")
                if raw is None:
                    continue
                try:
                    av = int(float(raw))
                except ValueError:
                    continue

                if kind == "Shield":
                    tier = tier_of(obj, name)
                    if tier not in AV_CEILING_SHIELD:
                        continue  # a tier the shield ceiling says nothing about
                    slot, ceiling = f"Shield (tier {tier})", AV_CEILING_SHIELD[tier]
                else:
                    slot = part.get("WornOn")
                    if slot not in AV_CEILING:
                        continue  # a slot vanilla states no ceiling for
                    ceiling = AV_CEILING[slot]

                if av > ceiling:
                    f.add(
                        "armor-curve",
                        f"{path}: {name} grants AV {av} in the {slot} slot, over vanilla's best "
                        f"ordinary item at {ceiling}",
                    )


def check_finesse_visible(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """A weapon tagged Finesse must say so, and a weapon that says so must be tagged.

    The Finesse tag has no player-facing surface of its own: nothing in the item screen mentions
    it, so a weapon carrying the tag and a weapon where the feature is silently broken look
    identical. That is not hypothetical - it is how #366 was found, after a play session where the
    only symptom was a dagger description that said nothing.

    Checked in both directions, because each catches a different mistake. A tag with no text is a
    feature the player cannot discover; text with no tag is a promise the game does not keep.

    Scope is what CI can actually resolve: blueprints that *declare* the tag in this mod's own
    files. The daggers reached through `BaseDagger`'s tag are vanilla blueprints whose inheritance
    needs the game, so they are covered transitively - `BaseDagger` carries both the tag and the
    text, and this check holds that pairing.
    """
    for path, root in all_roots.items():
        for obj in root.iter("object"):
            name = obj.get("Name") or ""
            if not name:
                continue
            tag = next(
                (e for e in obj.findall("tag") if e.get("Name") == FINESSE_TAG), None
            )
            tagged = tag is not None and tag.get("Value") != "*delete"
            described = any(
                e.get("Name") == "RulesDescription"
                and FINESSE_TEXT in (e.get("Text") or "")
                for e in obj.findall("part")
            )
            if tagged and not described:
                f.add(
                    "finesse-visible",
                    f"{path}: {name} carries the Finesse tag but no RulesDescription saying so - "
                    f"a silent feature and a broken one look the same from the item screen",
                )
            elif described and not tagged:
                f.add(
                    "finesse-visible",
                    f"{path}: {name} describes itself as a finesse weapon but carries no Finesse "
                    f"tag, so the power will never apply to it",
                )


def mean_damage(dice: str | None) -> float | None:
    """Mean of a Qud damage string like `2d6+1`, which is 8.0. None when it is not one."""
    if not dice:
        return None
    m = re.fullmatch(r"\s*(\d*)d(\d+)\s*([+-]\s*\d+)?\s*", dice)
    if m:
        count = int(m.group(1) or 1)
        faces = int(m.group(2))
        bonus = int(m.group(3).replace(" ", "")) if m.group(3) else 0
        return count * (faces + 1) / 2 + bonus
    try:
        return float(dice.strip())
    except ValueError:
        return None


def snapshot_records() -> tuple[dict, dict]:
    """Vanilla's side of the records this mod merges, from tools/qud-api.json.

    Empty when the snapshot predates these keys, in which case the checks that need it return
    early. That is the one silence here worth naming: a snapshot without them cannot distinguish
    "nothing wrong" from "nothing checked", so regenerate after every Qud update.
    """
    if not QUD_API_PATH.is_file():
        return {}, {}
    data = json.loads(QUD_API_PATH.read_text())
    return data.get("merged_records", {}), data.get("table_weights", {})


def snapshot_skill_powers() -> dict[str, dict]:
    """Vanilla's Cost, Minimum and Attribute for each skill power this mod merges into.

    Separate accessor rather than a third element on `snapshot_records`, because the callers do
    not overlap and a tuple that grows is a tuple every caller has to be edited for.
    """
    if not QUD_API_PATH.is_file():
        return {}
    return json.loads(QUD_API_PATH.read_text()).get("skill_powers", {})


def inherited_skill(obj: ET.Element, all_roots: dict[Path, ET.Element]) -> str | None:
    """A weapon's `Skill`, walked up `Inherits` through this mod's own files.

    The snapshot answers this for merges, and a merge is the case that motivated it - but a NEW
    blueprint has the same problem from the other direction: `Raven_Iron Mace` states no Skill and
    inherits `BaseCudgel`, which this mod merges with `Skill="Cudgel"`. Without this it resolved to
    None, found no ceiling, and was skipped in silence while sitting over one.

    Only walks what the mod ships. A chain leaving the mod's files ends here rather than guessing.
    """
    seen: set[str] = set()
    name = obj.get("Inherits")
    while name and name not in seen:
        seen.add(name)
        parent = None
        for root in all_roots.values():
            for candidate in root.iter("object"):
                if candidate.get("Name") == name:
                    parent = candidate
                    break
            if parent is not None:
                break
        if parent is None:
            return None
        for el in parent.findall("part"):
            if el.get("Name") == "MeleeWeapon" and el.get("Skill"):
                return el.get("Skill")
        name = parent.get("Inherits")
    return None


def check_damage_ceiling(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """No weapon may out-damage vanilla's best at its family, tier and handedness.

    docs/STYLEGUIDE.md 3.2.1. This is the check the cudgel line in #322 walked past: 26 family and
    tier cells over the ceiling, the worst by 47%.

    Twenty-five of those 26 are **merges**, which is why this needs the snapshot. A merge carries
    no `Inherits` and usually no `Skill`, so `Cudgel8th` cannot be recognised as a cudgel from this
    mod's own XML at all - a CI check without vanilla's side would have caught 1 of 26 while
    appearing to cover damage, which is worse than no check.

    Only fires where the mod actually states a damage. A merge that leaves `BaseDamage` alone is
    making no claim about damage, and armour that inherits a weapon's default `Skill` is not a
    weapon.
    """
    records, _ = snapshot_records()
    if not records:
        return

    for path, root in all_roots.items():
        for obj in root.iter("object"):
            name = obj.get("Name") or ""
            if not name or is_base_object(obj):
                continue
            if any(word in name.lower() for word in CURVE_EXEMPT):
                continue  # the same exemptions the value curve carries, for the same reasons
            part = next(
                (e for e in obj.findall("part") if e.get("Name") == "MeleeWeapon"), None
            )
            if part is None or part.get("BaseDamage") is None:
                continue
            mean = mean_damage(part.get("BaseDamage"))
            if mean is None:
                continue

            fact = records.get(name, {})
            skill = (
                part.get("Skill")
                or fact.get("skill")
                or inherited_skill(obj, all_roots)
            )
            tier = tier_of(obj, name)
            if tier is None and fact.get("tier") is not None:
                try:
                    tier = int(fact["tier"])
                except ValueError:
                    tier = None
            declared = next(
                (
                    e.get("UsesTwoSlots")
                    for e in obj.findall("part")
                    if e.get("Name") == "Physics" and e.get("UsesTwoSlots")
                ),
                None,
            )
            two = (declared or "").lower() == "true" or (
                declared is None and bool(fact.get("two_handed"))
            )

            ceiling = DAMAGE_CEILING.get((skill, two), {}).get(tier)
            if ceiling is None:
                continue  # a family, tier or handedness vanilla does not ship
            if mean > ceiling:
                hands = "two-handed" if two else "one-handed"
                f.add(
                    "damage-ceiling",
                    f"{path}: {name} deals {mean:g} mean damage, over vanilla's best "
                    f"{hands} {skill} at tier {tier}, which is {ceiling:g}",
                )


def check_weight_curve(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """A merge may make a vanilla item lighter, never heavier.

    docs/STYLEGUIDE.md 3.2.1. The per-slot magnitudes wait on the burden work in #320, but the
    direction does not: every factor this fork uses is below 1, so an item the mod made *heavier*
    contradicts the rule whatever the magnitudes turn out to be.
    """
    records, _ = snapshot_records()
    if not records:
        return

    for path, root in all_roots.items():
        for obj in root.iter("object"):
            name = obj.get("Name") or ""
            if obj.get("Load") != "Merge" or not name:
                continue
            part = next(
                (e for e in obj.findall("part") if e.get("Name") == "Physics"), None
            )
            if part is None or part.get("Weight") is None:
                continue
            was = records.get(name, {}).get("weight")
            if was is None:
                continue
            try:
                now_w, was_w = float(part.get("Weight")), float(was)
            except ValueError:
                continue
            if now_w > was_w:
                f.add(
                    "weight-curve",
                    f"{path}: {name} weighs {now_w:g} lb against vanilla's {was_w:g} - every "
                    f"per-slot factor is below 1, so nothing may get heavier",
                )


def check_table_share(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """This fork's share of a vanilla loot table stops at half.

    docs/STYLEGUIDE.md 3.2.1, and the one curve there that is a chosen number rather than a
    derived one - vanilla has no opinion on how much of its loot pool may belong to a mod.

    Share is a ratio, so vanilla's side has to come from the snapshot. Tables this fork defines
    itself have no vanilla entry to be half of, and are not checked.
    """
    _, vanilla_totals = snapshot_records()
    if not vanilla_totals:
        return

    pops = Path("mod/PopulationTables.xml")
    if not pops.is_file():
        return
    try:
        root = ET.fromstring(pops.read_text(encoding="utf-8-sig"))
    except ET.ParseError:
        return  # check_wellformed owns this

    for pop in root.iter("population"):
        name = pop.get("Name")
        vanilla = vanilla_totals.get(name)
        if not name or not vanilla:
            continue
        mine = 0
        for obj in pop.iter("object"):
            if obj.get("Blueprint"):
                try:
                    mine += int(obj.get("Weight") or 0)
                except ValueError:
                    pass
        if mine > vanilla:
            share = mine / (mine + vanilla) * 100
            f.add(
                "table-share",
                f"mod/PopulationTables.xml: {name} is {share:.1f}% this fork's content "
                f"({mine} against vanilla's {vanilla}) - the ceiling is half",
            )


IMPLANT_TABLE_COSTS = {
    "Implants_1and2Pointers": (1, 2),
    "Implants_3Pointers": (3, 3),
    "Implants_4PlusPointers": (4, 99),
}


def check_implant_table_cost(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """An implant's loot table has to match the licence points it actually costs.

    Vanilla's three implant tables are named after a cost bracket, so the name is a claim about
    the blueprints inside it rather than a label. Nothing in the game enforces that, which is how
    #418 happened: crysteel dermal plating was re-priced from 3 licence points to 6 and stayed in
    `Implants_3Pointers`, where its own name said it did not belong.

    Only this fork's blueprints are checked. Vanilla's placements are vanilla's to be wrong about,
    and the merges do not change `Cost`.
    """
    pops = Path("mod/PopulationTables.xml")
    if not pops.is_file():
        return
    try:
        root = ET.fromstring(pops.read_text(encoding="utf-8-sig"))
    except ET.ParseError:
        return  # check_wellformed owns this

    costs: dict[str, int] = {}
    for blueprint_root in blueprint_sources(all_roots).values():
        for obj in blueprint_root.iter("object"):
            name = obj.get("Name")
            if not name:
                continue
            for part in obj.iter("part"):
                if part.get("Name") == "CyberneticsBaseItem" and part.get("Cost"):
                    try:
                        costs[name] = int(part.get("Cost"))
                    except ValueError:
                        pass

    for pop in root.iter("population"):
        bracket = IMPLANT_TABLE_COSTS.get(pop.get("Name") or "")
        if not bracket:
            continue
        low, high = bracket
        for obj in pop.iter("object"):
            blueprint = obj.get("Blueprint")
            cost = costs.get(blueprint or "")
            if cost is None or not (low <= cost <= high):
                if cost is None:
                    continue
                f.add(
                    "implant-table-cost",
                    f"mod/PopulationTables.xml: {blueprint} costs {cost} licence point(s) "
                    f"but sits in {pop.get('Name')}, which is for {low}"
                    + (f"-{high}" if high != low else "")
                    + (" and up" if high == 99 else ""),
                )


SKILL_POWER_FIELDS = ("Cost", "Minimum", "Attribute")


def optioned_powers() -> set[tuple[str, str]]:
    """Every (skill, power) the eased-requirements and retuned-costs options restore.

    Read out of `Raven_Options.cs`'s two tables rather than duplicated here, so the check cannot
    drift from the thing it checks. Both entries start `new PowerRequirement("Skill", "Power"` or
    `new PowerCost("Skill", "Power"`, which is a shape the file's own formatting keeps stable.
    """
    source = Path("mod/Scripting/Raven_Options.cs")
    if not source.is_file():
        return set()
    text = source.read_text(encoding="utf-8-sig")
    return {
        (m.group(1), m.group(2))
        for m in re.finditer(
            r'new Power(?:Requirement|Cost)\(\s*"([^"]+)",\s*"([^"]+)"', text
        )
    }


def check_skill_option_coverage(f: Findings) -> None:
    """A skill power this fork changes must be a power its options can put back.

    #421: #331 decided three undocumented cuts were drift and removed them from the option tables
    -- but not from `mod/Skills.xml`, so they kept shipping and could no longer be switched off.
    Nothing could see it, because the two halves live in different files and neither names the
    other.

    So this holds them together, in both directions:

      a value that differs from vanilla and is in no table  -> a change nothing can undo
      a table entry whose value already matches vanilla     -> an option that restores nothing

    Powers with no vanilla counterpart are this fork's own additions rather than merges -- the
    four `Finesse` powers -- and belong to neither direction.
    """
    vanilla = snapshot_skill_powers()
    if not vanilla:
        return  # no snapshot, or one predating this key; regenerating is the fix

    skills = Path("mod/Skills.xml")
    if not skills.is_file():
        return
    try:
        root = ET.fromstring(skills.read_text(encoding="utf-8-sig"))
    except ET.ParseError:
        return  # check_wellformed owns this

    optioned = optioned_powers()
    changed: set[tuple[str, str]] = set()

    for skill in root.iter("skill"):
        for power in skill.iter("power"):
            name = (skill.get("Name"), power.get("Name"))
            if not all(name):
                continue
            stock = vanilla.get(f"{name[0]}/{name[1]}")
            if not stock:
                continue  # a power this fork adds, not one it merges

            differs = [
                field
                for field in SKILL_POWER_FIELDS
                if power.get(field) is not None and power.get(field) != stock.get(field)
            ]
            if not differs:
                continue
            changed.add(name)
            if name not in optioned:
                f.add(
                    "skill-option-coverage",
                    f"mod/Skills.xml: {name[0]} / {name[1]} changes "
                    f"{', '.join(differs)} against vanilla, but no option restores it - "
                    f"either put vanilla's value back or add it to Raven_Options.cs",
                )

    for name in sorted(optioned - changed):
        f.add(
            "skill-option-coverage",
            f"mod/Scripting/Raven_Options.cs: {name[0]} / {name[1]} is in an option table, "
            f"but mod/Skills.xml does not change it - the option restores nothing",
        )


def check_reachability(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """Every new blueprint must be obtainable: in a population table, tagged, or tinkerable.

    This is the check that surfaces #6 (72 unreachable chips) and #7 (9 unreachable armor
    pieces).

    A `DynamicObjectsTable:` tag is the third route, and it took #171 to notice: creature
    variants self-register into spawn tables with a tag and appear in no `PopulationTables.xml`
    entry at all, so checking only `Blueprint=` called all 32 of them unobtainable while they
    spawned perfectly well. For the tiered pools it is not merely *a* route but the only additive
    one - `PopulationManager.RequireTable` returns early when a table of that name already exists,
    so declaring one replaces vanilla's whole fabricated pool instead of joining it.

    What this deliberately does NOT check is whether the table name is one vanilla defines.
    Emitting `Baboons_Creatures` when the real table is `Baboons` fabricates a pool nothing draws
    from, and the variant never spawns with no error anywhere - but answering that needs the game,
    and this script runs in CI without it. `tools/report_dynamic_tables.py` owns that question: a
    bogus name shows up as a pool new to this mod in the snapshot diff, and the `dynamic-pools`
    pre-commit hook blocks on it.
    """
    roots = blueprint_sources(all_roots)
    defined: dict[str, Path] = {}
    tinkerable: set[str] = set()
    tagged: set[str] = set()
    for path, root in roots.items():
        for obj in root.iter("object"):
            name = obj.get("Name")
            if (
                not name
                or not name.startswith(MOD_PREFIXES)
                or obj.get("Load") == "Merge"
            ):
                continue
            if any(m in name for m in ABSTRACT_MARKERS):
                continue
            defined[name] = path
            if any(p.get("Name") == "TinkerItem" for p in obj.iter("part")):
                tinkerable.add(name)
            for tag in obj.iter("tag"):
                tag_name = tag.get("Name") or ""
                if not tag_name.startswith(DYNAMIC_TABLE_PREFIX):
                    continue
                # `:Weight`, `:Number` and `:Builder` modify an entry rather than creating one,
                # and a removal is the opposite of a route - 72 of the creature variants' tags
                # are `*delete` precisely to keep them OUT of a table.
                if tag_name.endswith((":Weight", ":Number", ":Builder")):
                    continue
                if tag.get("Value") in ("*delete", "{{{remove}}}"):
                    continue
                tagged.add(name)

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
        if name not in in_tables and name not in tinkerable and name not in tagged:
            f.add(
                "unreachable",
                f"{name} ({path.name}) is in no population table, carries no "
                f"{DYNAMIC_TABLE_PREFIX} tag, and has no TinkerItem",
            )


def check_aggregate_sweep(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """An `AggregateWith` merged onto a vanilla parent must not sweep in vanilla's descendants.

    `AggregateWith` bundles every blueprint carrying the same value into ONE slot in a fabricated
    spawn table, and the tag INHERITS. So merging it onto a vanilla parent reaches every vanilla
    descendant of that parent too, and collapses records vanilla deliberately kept apart.

    #171 shipped exactly that, and it took a playtest to find. `Hulking Baboon`, `Shrewd Baboon`
    and `Baboon Hero 1` joined `Baboon`'s slot, taking baboons in the hills from four slots to one
    and making the family roughly four times rarer; `ClockworkBeetle` - a machine - began
    competing for the giant beetle's slot, and `Sultan Croc` for the ordinary croc's. Nothing
    errored, nothing failed, and the mod's own documentation claimed the tables had not grown.
    They had shrunk.

    The mechanism is not the defect - vanilla builds aggregates by inheritance too, and
    `Snapjaw Scavanger` appears once in the whole game with Scavenger 0/1/2 inheriting it. The
    defect is choosing a head that has vanilla descendants of its own, so each one has to be
    exempted deliberately with `AggregateWith` set to `*delete`, which is vanilla's own idiom.

    The descendant list comes from the snapshot rather than from `mod/`, because the answer is in
    the game and this runs in CI without one. A Qud patch adding a descendant to one of these
    families changes the snapshot, `snapshot-check` reports it stale, and regenerating brings the
    new name here - which turns future drift from invisible into a red run.
    """
    if not QUD_API_PATH.is_file():
        return
    descendants = json.loads(QUD_API_PATH.read_text()).get("aggregate_descendants")
    if not descendants:
        return  # a snapshot predating this key cannot distinguish "none" from "not recorded"

    exempt: set[str] = set()
    for root in blueprint_sources(all_roots).values():
        for obj in root.iter("object"):
            name = obj.get("Name")
            if not name:
                continue
            for tag in obj.findall("tag"):
                if tag.get("Name") == "AggregateWith" and tag.get("Value") == "*delete":
                    exempt.add(name)

    for head, swept in sorted(descendants.items()):
        for name in swept:
            if name in exempt:
                continue
            f.add(
                "aggregate-sweep",
                f"{name} inherits AggregateWith from {head}, so vanilla's own entry is folded "
                f"into that one spawn slot - give {name} a merged AggregateWith of *delete, "
                f"or stop aggregating {head}",
            )


def check_table_targets(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """A table entry naming a mod blueprint that doesn't exist can never spawn."""
    roots = blueprint_sources(all_roots)
    defined = set()
    for root in roots.values():
        for obj in root.iter("object"):
            if obj.get("Name"):
                defined.add(obj.get("Name"))
    for path, root in roots.items():
        for el in root.iter():
            bp = el.get("Blueprint")
            if bp and bp.startswith(MOD_PREFIXES) and bp not in defined:
                f.add("dangling-blueprint", f"{path}: table references undefined {bp}")


def check_part_attributes(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """A `<part>` attribute must name something the part class can actually be set to.

    Qud applies attributes by name. One that matches no member is discarded in silence - the part
    loads, the object validates, and the setting does nothing:

        <part Name="TemperatureOnHit" Amount="250" Radius="2" />
                                                   ^^^^^^^^^^ ignored, no error anywhere

    Same failure shape as `unknown-part` and `dangling-blueprint-ref`, and the same class of defect
    that put all of Ammo.xml behind a comment for the whole of 2.2.

    The member list comes from tools/qud-api.json, so this runs in CI with no game and no SDK. A
    part missing from the snapshot is skipped rather than guessed at: `unknown-part` is what
    reports a name that resolves to nothing, and reporting it twice would only look like two
    problems. See issue #151.
    """
    api = load_qud_api()
    if not api or not api.get("members"):
        return
    members = api["members"]
    element_attrs = set(api.get("element_attributes") or ELEMENT_ATTRS)
    for path, root in all_roots.items():
        for part in object_parts(root):
            name = part.get("Name")
            if name not in members:
                continue
            allowed = set(members[name]) | element_attrs
            for attr in sorted(part.attrib):
                if attr not in allowed:
                    f.add(
                        "part-attribute",
                        f'{path}: <part Name="{name}" {attr}="…"> - {name} has no settable '
                        f"member called {attr}, so Qud discards it without an error",
                    )


def check_part_builders(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """A `<part Builder="…">` must name a class that exists in XRL.World.PartBuilders.

    `Builder` does not set a member - it names a class that post-processes the part once it is
    built, which is why #151 treats it as an attribute of the element rather than of the part.
    That established the attribute is legitimate and left the *value* unchecked, so a builder that
    does not exist fails the way everything in this family fails: the part loads, the builder
    never runs, and nothing anywhere says so.

    This mod sets `Builder` on no part today. The check is a guard against a future edit, which is
    the same reason `unknown-part` exists. See issue #168.
    """
    api = load_qud_api()
    if not api or not api.get("part_builders"):
        return
    builders = set(api["part_builders"])
    for path, root in all_roots.items():
        for part in object_parts(root):
            builder = part.get("Builder")
            if builder and builder not in builders:
                f.add(
                    "part-builder",
                    f'{path}: <part Name="{part.get("Name")}" Builder="{builder}"> - '
                    f"{builder} is not a class in XRL.World.PartBuilders, so nothing runs",
                )


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
    simply does not do the thing you wrote. The mod's own Mod* parts are check_scripting_parts'
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
                if not name or name.startswith(MOD_PREFIXES):
                    continue
                if name not in known:
                    f.add(
                        "unknown-part",
                        f'{path}: {owner} uses <part Name="{name}">, which is not a part Qud '
                        f"provides - it will be ignored silently (snapshot source: {source}; "
                        f"if the part is real but unused by vanilla, regenerate with --assembly)",
                    )


def check_mutation_type_arguments(f: Findings) -> None:
    """Every `ModImprovedMutationBase<T>` must name a `T` the game will actually grant.

    Existing in the assembly is not the same as being grantable. `GasGeneration` is a real,
    concrete, instantiable class — so it compiles, and `unknown-part` passes because
    `Raven_ModGasGeneration` is a genuine part — but nothing declares `Class="GasGeneration"` in
    either mutation catalogue. `BaseMutation.GetMutationEntry()` finds no entry, logs
    `Mutation entry not found`, and synthesises a fallback. Six chips ran at roughly half their
    intended gas duration from upstream 2.2 until #226, invisible to every gate we had, because no
    gate looked *inside* the generic.

    The catalogue is the authority rather than the `XRL.World.Parts.Mutation` namespace, because
    the namespace is what made the defect look fine.

    The mod declares no mutations of its own — there is no `<mutation>` element anywhere in `mod/`.
    Should that ever change, this must union the mod's own `Class` values with vanilla's, or it
    will report a mod-declared mutation as unknown.
    """
    api = load_qud_api()
    if api is None:
        return  # check_part_names already reported the missing snapshot
    known = api.get("mutation_classes")
    if not known:
        f.add(
            "qud-api-snapshot",
            f"{QUD_API_PATH} has no mutation_classes - regenerate with "
            "tools/snapshot_qud_api.py --assembly",
        )
        return
    known = set(known)
    for cs in sorted((MOD / "Scripting").glob("*.cs")):
        # Comments are stripped so a commented-out declaration cannot invent a violation; the
        # mod keeps blocks of dormant blueprints and scripts exactly like that.
        src = "\n".join(strip_cs_comments(cs.read_text(encoding="utf-8-sig")))
        # Type parameters are not mutation names. Raven_ModVariantMutationBase is generic over T
        # and passes it through to ModImprovedMutationBase<T>, so a literal read finds "T" and
        # reports a mutation nothing declares (#411).
        parameters = {
            name
            for decl in re.findall(r"\bclass\s+\w+\s*<([^>]*)>", src)
            for name in re.findall(r"\w+", decl)
        }
        for match in re.finditer(r"ModImprovedMutationBase<\s*(\w+)\s*>", src):
            arg = match.group(1)
            if arg in parameters:
                continue
            if arg not in known:
                f.add(
                    "unknown-mutation",
                    f"{cs.name}: ModImprovedMutationBase<{arg}> names a class no mutation "
                    f'declares - nothing has <mutation Class="{arg}">, so the game logs '
                    f"'Mutation entry not found' and grants a fallback (see #226)",
                )


def check_graded_unlevellable_chips(
    f: Findings, all_roots: dict[Path, ET.Element]
) -> None:
    """A chip granting a mutation that cannot level must not vary that level by grade.

    `Kindle` and `FrostWebs` override `CanLevel()` to return a constant false and read their level
    nowhere - Kindle's cooldown and range are literals, Frost Webs sets its range and area the same
    way. So a chip granting one of them is the same item whatever level it claims to give, and the
    fork shipped three grades of each at 20, 80 and 320 water: #347. A player paid sixteen times
    the price of the basic chip for the basic chip.

    Nothing could have caught it. `unknown-mutation` passes, because `Kindle` is genuinely
    declared in the catalogue; `item-curve` passes, because each price sat exactly on the chip
    curve for its tier. The defect is only visible inside the mutation's own method body, which is
    why `tools/qud-api.json` now carries `non_leveling_mutations` - see `tools/dump_part_members.cs`
    for how two IL bytes decide it.

    Grouped by the set of mutation-granting parts a blueprint carries, which is what makes a line a
    line. The three Kindle chips carry `{Raven_ModKindle}` and must agree with each other; the three
    Fire chipsets carry that part alongside two that do scale, so they form their own group and must
    agree among themselves. Comparing every blueprint at once would refuse the correct arrangement,
    where a chipset grants a lower level than the single chip on purpose.
    """
    api = load_qud_api()
    if api is None:
        return  # check_part_names already reported the missing snapshot
    unlevellable = api.get("non_leveling_mutations")
    if not unlevellable:
        f.add(
            "qud-api-snapshot",
            f"{QUD_API_PATH} has no non_leveling_mutations - regenerate with "
            "tools/snapshot_qud_api.py --assembly",
        )
        return
    unlevellable = set(unlevellable)

    # Every chip part, and which of them grant a mutation that cannot level. Comments are
    # stripped for the same reason check_mutation_type_arguments strips them: the mod keeps
    # dormant scripts commented out, and a dormant declaration is not a violation.
    granting: set[str] = set()
    dead: dict[str, str] = {}
    for cs in sorted((MOD / "Scripting").glob("*.cs")):
        src = "\n".join(strip_cs_comments(cs.read_text(encoding="utf-8-sig")))
        match = re.search(r"ModImprovedMutationBase<\s*(\w+)\s*>", src)
        if not match:
            continue
        granting.add(cs.stem)
        if match.group(1) in unlevellable:
            dead[cs.stem] = match.group(1)
    if not dead:
        return

    # group -> part -> {tier: [blueprint names]}
    groups: dict[tuple[str, ...], dict[str, dict[str, list[str]]]] = {}
    for root in all_roots.values():
        for obj in root.iter("object"):
            name = obj.get("Name") or ""
            carried = {
                e.get("Name"): e.get("Tier")
                for e in obj.findall("part")
                if e.get("Name") in granting
            }
            if not any(part in dead for part in carried):
                continue
            key = tuple(sorted(carried))
            for part, tier in carried.items():
                if part not in dead:
                    continue
                groups.setdefault(key, {}).setdefault(part, {}).setdefault(
                    tier or "unset", []
                ).append(name)

    for parts in (g for _, g in sorted(groups.items())):
        for part, by_tier in sorted(parts.items()):
            if len(by_tier) < 2:
                continue
            ladder = "; ".join(
                f"Tier {tier} on {', '.join(sorted(names))}"
                for tier, names in sorted(by_tier.items())
            )
            f.add(
                "dead-chip-grade",
                f"{part} grants {dead[part]}, which cannot level, so every grade of it "
                f"grants the same thing - but the level varies by grade ({ladder}). "
                f"Give the line one level, or the tooltip promises a ladder that is not "
                f"there (see #347)",
            )


def check_merged_value(f: Findings, all_roots: dict[Path, ET.Element]) -> None:
    """A merge keeps vanilla's value, unless it also changes the item's tier.

    docs/STYLEGUIDE.md 3.2. The value curve describes *this fork's* items; `item-curve` prices only
    `Raven_` and `Vixy_` objects, on the rule that vanilla sets its own values. That rule is right
    for a new item and exactly wrong for a merge that rewrites vanilla's, which is how 142 of the
    213 merges came to carry a price this fork had chosen - the merged economy 25% cheaper, and
    nothing able to see it (#380).

    The exception is real and small. Where the merge also re-tiers the item the new price follows a
    derived tier rather than replacing a decision vanilla made: `Carbide Boots` is tier 3 at 40
    against vanilla's tier 4 at 150, and that is the curve doing its job on a tier this fork chose.
    Twelve merges qualify.

    Resistances have no curve at all, so a merge never states one. Vanilla's side is recorded for
    the same reason as value: CI has no game, so without the snapshot a merge is opaque.

    This is the second half of the blind spot #354 fixed for tier detection. Both halves of
    `item-curve` skipped vanilla-named objects; only one of them should have.
    """
    api = load_qud_api()
    if api is None:
        return  # check_part_names already reported the missing snapshot
    records = api.get("merged_records")
    if not records:
        f.add(
            "qud-api-snapshot",
            f"{QUD_API_PATH} has no merged_records - regenerate with "
            "tools/snapshot_qud_api.py --assembly",
        )
        return

    for path, root in all_roots.items():
        for obj in root.iter("object"):
            name = obj.get("Name") or ""
            if obj.get("Load") != "Merge" or name not in records:
                continue
            vanilla = records[name]

            mine = next(
                (
                    e.get("Value")
                    for e in obj.findall("part")
                    if e.get("Name") == "Commerce" and e.get("Value") is not None
                ),
                None,
            )
            if mine is not None and vanilla.get("value") not in (None, mine):
                my_tier = next(
                    (
                        e.get("Value")
                        for e in obj.findall("tag")
                        if e.get("Name") == "Tier"
                    ),
                    None,
                )
                retiered = (
                    my_tier is not None
                    and vanilla.get("tier") is not None
                    and my_tier != vanilla["tier"]
                )
                if not retiered:
                    f.add(
                        "merge-value",
                        f"{path}: {name} is a merge priced at {mine}, but vanilla prices it "
                        f"{vanilla['value']} - a merge keeps vanilla's value unless it also "
                        f"re-tiers the item (STYLEGUIDE 3.2, #380)",
                    )

            armor = next(
                (e for e in obj.findall("part") if e.get("Name") == "Armor"), None
            )
            if armor is None:
                continue
            theirs = vanilla.get("resistances") or {}
            for element in RESISTANCES:
                stated = armor.get(element)
                if stated is None or stated == theirs.get(element):
                    continue
                f.add(
                    "merge-value",
                    f"{path}: {name} is a merge stating {element}={stated}, but vanilla "
                    f"says {theirs.get(element, 'nothing')} - no curve describes a resistance, "
                    f"so a merge never states one (STYLEGUIDE 3.2, #380)",
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
    check_option_defaults(f, roots)
    check_joppa_sync(f, roots)
    check_filenames(f)
    check_merge_discipline(f, roots)
    check_duplicate_children(f, roots)
    check_naming_discipline(f, roots)
    check_naming_syllables(f, roots)
    check_naming_priority(f, roots)
    check_naming_option_coverage(f, roots)
    check_scripting_parts(f, roots)
    check_scripting_policy(f)
    check_subtype_tiles(f, roots)
    check_item_curves(f, roots)
    check_stat_discipline(f, roots)
    check_armor_curve(f, roots)
    check_finesse_visible(f, roots)
    check_damage_ceiling(f, roots)
    check_weight_curve(f, roots)
    check_table_share(f, roots)
    check_implant_table_cost(f, roots)
    check_skill_option_coverage(f)
    check_serializable_shape(f)
    check_reachability(f, roots)
    check_aggregate_sweep(f, roots)
    check_table_targets(f, roots)
    check_part_names(f, roots)
    check_blueprint_refs(f, roots)
    check_part_attributes(f, roots)
    check_part_builders(f, roots)
    check_mutation_type_arguments(f)
    check_graded_unlevellable_chips(f, roots)
    check_merged_value(f, roots)
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
