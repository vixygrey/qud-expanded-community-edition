#!/usr/bin/env python3
"""Check the documentation against the mod. Python 3 standard library only.

    python3 tools/check_docs.py

`tools/validate_mod.py` checks the mod. This checks the documents that describe it, because
nothing else did — three separate sweeps (#93, #96, #130) found documentation asserting things
that had stopped being true, every time by someone reading rather than by anything checking.

It cannot read a sentence and ask whether it is still true; nothing can. What it can do is check
the parts of a document that are *not* prose:

  counts          a figure quoted in the docs, against the same figure recomputed from mod/
  vanilla-figure  a figure quoted about the game, against qud-api.json's snapshot of it. These
                  are read from the mod's XML comments as well as from the documents, because
                  that is where the reasoning behind a value is written down.
  links           every relative link resolves to a file that exists
  sections        every "FILE.md §N" cross-reference names a section that exists there
  appendix-b      every row of FEATURES' chip appendix, against the blueprint it describes
  item-tables     every Tier, Value and Weight in FEATURES' item tables, against the same
  checks          every check name quoted in the docs is one a script in tools/ actually emits
  required-checks every CI job is required or deliberately not, and the documented count agrees
  preserved       Mura's two documents are still byte-identical to the upstream import

The required-checks pair is the newest and came from a near-miss. Six documents claimed ten
required checks while nine were enforced: Tests ran and passed on every pull request and was not
in the ruleset, so a failing test suite could have merged. When that was corrected the obvious
next move was to update the documented count - which would have changed a correct ten into an
incorrect eleven. The documents were only right again *because* of the fix. See #152.

`--ruleset` compares tools/required-checks.json against what GitHub actually enforces. It is not
part of the normal run: it needs gh and a network, and a check that quietly passes when it could
not reach anything is worse than no check at all.

The counts check is the one that matters most and the one with a real limitation: it can only
verify a figure it knows how to find. CLAIMS below pairs a regular expression with the facts its
capture groups hold. A figure written in a phrasing no pattern matches is simply not checked, so
adding a new claim to the docs means adding its phrasing here. That is the cost of checking prose
at all, and it is cheaper than the alternative, which is three sweeps and counting.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from check_vanilla_drift import BlueprintIndex

MOD = Path("mod")
REQUIRED_CHECKS_PATH = Path("tools/required-checks.json")
CI_WORKFLOWS = (
    Path(".github/workflows/ci.yml"),
    Path(".github/workflows/assign.yml"),
    Path(".github/workflows/wiki.yml"),
)

# The documents write these as words, which is their voice and not something to rewrite for a
# regex's convenience. Only the values actually used are listed; an unknown word is reported
# rather than guessed at, so a count nobody anticipated fails loudly instead of being skipped.
WORD_NUMBERS = {
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    # The wiki's genotype/slot table writes zero as a word, because "| Mutated Human | 0 |" reads
    # like a typo where "none" reads like a decision.
    "none": 0,
}
# The mod crossed twenty options in #605, and these claims are written out in prose - "Twenty-one
# options, in Qud's own options menu". The compounds are generated rather than listed because they
# are unambiguous in a way the bare units are not, which is why "one" through "seven" are still
# deliberately absent above: a capture group that resolved "one" would turn ordinary prose into a
# claim. A hyphenated compound can only ever be a number.
#
# The capture patterns below therefore use `([\w-]+)` and not `(\w+)`: `\w` excludes the hyphen, so
# a pattern written the obvious way captures "twenty" out of "twenty-four" and then reports
# "'four' is not a number this script knows". The dictionary held the compound the whole time; the
# pattern could not reach it. Three of these were widened when the repository's own documents
# crossed twenty options, and the wiki patterns did not inherit the fix - the same shape as the
# "second check that did not inherit the fix" entry in docs/LESSONS.md. They are all widened now.
_TENS = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}
_UNITS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
}
WORD_NUMBERS.update(_TENS)
WORD_NUMBERS.update(
    {
        f"{tens}-{unit}": tv + uv
        for tens, tv in _TENS.items()
        for unit, uv in _UNITS.items()
    }
)
DOCS = [
    Path(p)
    for p in (
        "README.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
        "COPYING.md",
        "NOTICE",
        "CHANGELOG.md",
        "AGENTS.md",
        "docs/CHARTER.md",
        "docs/FEATURES.md",
        "docs/LESSONS.md",
        "docs/STYLEGUIDE.md",
        "docs/PERMISSION.md",
        "docs/DESIGN_options.md",
        "docs/DESIGN_balance.md",
        ".github/PULL_REQUEST_TEMPLATE.md",
    )
]


# Every document that can hold a reference, which is a wider set than DOCS. DOCS drives the figure,
# section and heading checks and is curated; the link checks want everything, because a rotted
# pointer is a defect wherever it sits. Eighteen of the 27 documents in docs/ were invisible to
# check_links until #735 - including DESIGN_overgrowth.md, which held one of the rotted references
# that motivated it.
def linked_docs() -> list[Path]:
    """Resolved when called, not at import.

    A module-level constant would be computed against whatever directory the interpreter started
    in, which makes the check untestable against a synthetic tree and would quietly miss a document
    added during the run.
    """
    return sorted(set(DOCS) | set(Path("docs").glob("*.md")))


# Mura's documents, preserved byte-for-byte. They were renamed in #23, so comparing against the
# upstream import needs the ORIGINAL paths — using the current ones reports both as modified when
# they are untouched, which is how the first version of this check cried wolf.
PRESERVED = {
    "docs/2.2-changelog.txt": "2.2 changelog.txt",
    "docs/mura-feature-notes-wip.txt": "What Does the Mod Do (WIP).txt",
}

# A figure gets quoted where the reasoning for it lives, and for this mod that is often a comment
# in the XML rather than a document. Nothing read those until #242, where "282 of 908 creature
# blueprints" sat in `mod/ObjectBlueprints/Ammo.xml` through review and a release with a
# denominator that cannot be reproduced under any filter. Only the vanilla-figure check reads
# these: the link and section checks stay pointed at the documents, where those ideas mean
# something.


def figure_sources() -> list[Path]:
    """Everything a vanilla figure may be quoted in. Globbed per call, not at import, so the
    answer follows the working directory rather than whatever it was when this module loaded."""
    return DOCS + sorted(Path("mod").rglob("*.xml"))


# Documents whose figures describe a *past* state on purpose. The changelog records what was true
# when each entry was written, so recomputing its numbers would be wrong.
COUNT_EXEMPT = {Path("CHANGELOG.md"), Path("docs/DESIGN_options.md")}


def parse(path: Path):
    return ET.fromstring(path.read_text(encoding="utf-8-sig"))


# --------------------------------------------------------------------------- facts


def vibro_weapons() -> int:
    """Melee vibro weapons this fork owns.

    "New" rather than merged, which is the same test `facts()` uses everywhere else: vanilla's own
    `Vibro Blade` and `Vibro Dagger` are merges and are not part of the count the wiki quotes.

    Parsed rather than grepped. `mod/ObjectBlueprints/MeleeWeapons.xml` holds four vibro objects
    inside a comment block, and a regex over the raw text counts them - which is the defect
    docs/LESSONS.md records against that exact file.
    """
    path = MOD / "ObjectBlueprints" / "MeleeWeapons.xml"
    if not path.is_file():
        return 0
    return sum(
        1
        for obj in parse(path).iter("object")
        if "Vibro" in (obj.get("Name") or "") and obj.get("Load") != "Merge"
    )


def chip_slots() -> dict[str, int]:
    """Chip Interface slots per anatomy, for the two genotypes whose count is in the XML.

    `mod/Bodies.xml` is the single source: `TrueKin` and `PsionicAdept` are this fork's own
    anatomies and declare their slots literally, so counting the parts is the whole derivation.

    **The Mutated Human is deliberately absent.** Its count is zero because
    `Raven_ChipSlotPlayerMutator` removes the slot the shared `Humanoid` anatomy gives it, and that
    is a rule in C# rather than a number in XML. Restating it here would be a second implementation
    of the same rule, which is the "number that agrees because both sides share the error" trap in
    docs/LESSONS.md. So the wiki's mutant row is checked by nobody, and #427 says so rather than
    pretending otherwise.
    """
    path = MOD / "Core" / "Bodies.xml"
    if not path.is_file():
        return {}
    root = parse(path)
    out: dict[str, int] = {}
    for anatomy in root.iter("anatomy"):
        name = anatomy.get("Name")
        if name not in ("TrueKin", "PsionicAdept"):
            continue
        out[f"chip-slots-{name.lower()}"] = sum(
            1 for part in anatomy.iter("part") if part.get("Type") == "Chip Interface"
        )
    return out


def facts() -> dict[str, int]:
    """Recompute every figure the documents are allowed to quote."""
    new = merged = 0
    per_file: dict[str, tuple[int, int]] = {}
    dormant: dict[str, int] = {}
    for f in sorted(MOD.rglob("*.xml")):
        try:
            root = parse(f)
        except ET.ParseError:
            continue  # validate_mod.py owns well-formedness
        fn = fm = 0
        for obj in root.iter("object"):
            if not obj.get("Name"):
                continue
            if obj.get("Load") == "Merge":
                fm += 1
            else:
                fn += 1
        if f.parent == MOD / "ObjectBlueprints":
            # The top level only, and keyed on the bare filename because that is how FEATURES 6.1
            # names its rows. `mod/Optional/<feature>/ObjectBlueprints/` can hold a Creatures.xml
            # too - the Stilt market does - and matching on `f.parent.name` let it overwrite the
            # main file's counts, so 6.1 reported the optional feature's three creatures as the
            # whole mod's forty-six. The totals above still count every blueprint under mod/,
            # which is why they are recounted rather than summed from these rows.
            per_file[f.name] = (fn, fm)
            dormant[f.name] = dormant_objects(f)
        new += fn
        merged += fm

    pops = list(parse(MOD / "Core" / "PopulationTables.xml").iter("population"))
    chips = [
        o
        for o in parse(MOD / "ObjectBlueprints" / "PsionicChips.xml").iter("object")
        if o.get("Name")
    ]

    out = {
        "new-blueprints": new,
        "vanilla-merges": merged,
        "populations": len(pops),
        "populations-merged": sum(1 for p in pops if p.get("Load") == "Merge"),
        "populations-fresh": sum(1 for p in pops if p.get("Load") != "Merge"),
        "options": len(list(parse(MOD / "Core" / "Options.xml").iter("option"))),
        "subtypes": len(list(parse(MOD / "Core" / "Subtypes.xml").iter("subtype"))),
        "subtype-sprites": len(list((MOD / "Textures" / "Subtypes").glob("*.png"))),
        "chips": len(chips) - sum(1 for c in chips if "Base" in (c.get("Name") or "")),
        "chip-objects": len(chips),
        "vibro-weapons": vibro_weapons(),
        "scripting-files": len(list((MOD / "Scripting").glob("*.cs"))),
        "mutation-stubs": len(list((MOD / "Scripting").glob("Raven_Mod*.cs"))),
        "required-checks": len(required_checks()["required"]),
        **chip_slots(),
        "optioned-requirements": len(optioned_requirements()),
    }
    for name, (n, m) in per_file.items():
        out[f"file:{name}:new"] = n
        out[f"file:{name}:merged"] = m
        out[f"file:{name}:dormant"] = dormant[name]
    return out


def dormant_objects(path: Path) -> int:
    """Objects commented out inside an XML file rather than deleted.

    `Ammo.xml` keeps the ten cut bullets and the quill arrow commented as a record of what was
    tried (#146, #210), and docs/FEATURES.md 6.1 quotes that number beside the live one. An
    element inside a comment is invisible to the parser, so it has to be counted from the text.
    """
    text = path.read_text(encoding="utf-8-sig")
    return sum(
        len(re.findall(r"<object\s", block))
        for block in re.findall(r"<!--(.*?)-->", text, re.DOTALL)
    )


def optioned_requirements() -> set[tuple[str, str]]:
    """Every power whose attribute requirement the *eased skill requirements* option restores.

    Read out of `Raven_Options.cs`'s `Requirements[]` rather than counted by hand. #421 moved four
    powers out of that table and `docs/FEATURES.md` went on saying twenty, because a number in
    prose has nobody to disagree with it.

    `PowerCost` entries are deliberately not counted: those belong to the *retuned skill point
    costs* option, which is a separate switch with a separate scope.
    """
    source = MOD / "Scripting" / "Raven_Options.cs"
    if not source.is_file():
        return set()
    return {
        (m.group(1), m.group(2))
        for m in re.finditer(
            r'new PowerRequirement\(\s*"([^"]+)",\s*"([^"]+)"',
            source.read_text(encoding="utf-8-sig"),
        )
    }


QUD_API_PATH = Path("tools/qud-api.json")


# Figures the documents quote *from vanilla*, paired with the phrasing each is written in. The
# values come from tools/qud-api.json's `figures` map, which snapshot_qud_api.py reads out of the
# installed game - so this checks a citation against its source rather than against another
# document.
#
# Same limitation as CLAIMS, and the same bargain: a figure written in a phrasing no pattern
# matches is not checked. Numbers are compared with thousands separators stripped, because the
# prose writes 1,200 where the XML says 1200 and the comma is the document's to keep.
def wrapped(phrase: str) -> str:
    """A claim pattern that survives being reflowed.

    Prose wraps, by prettier and by hand, and a pattern with a literal space stops matching the
    moment a sentence moves across a line. It then reports nothing - which is the same silence
    this whole check exists to break, arriving through the check itself. Every space becomes
    `\\s+` so where the line happens to break stops mattering.
    """
    return r"\s+".join(phrase.split(" "))


VANILLA_CLAIMS: list[tuple[str, list[str]]] = [
    # The `:Weight` carrier census (#702). Quoted in STYLEGUIDE 3.2.1 and FEATURES 37.2 to
    # establish that the dial is vanilla's own idiom. It is a *resolved* count -- the tag sits on
    # bases and reaches descendants, so declaring alone gives 41 against 167 -- which is why it
    # comes from `BlueprintIndex.carriers_matching` in the snapshot rather than from a grep.
    (r"(\d+) vanilla blueprints carry a `:Weight` tag", ["weight-tag-carriers"]),
    # The creature census (#242). Each phrasing carries its own denominator so a sentence cannot
    # quote a share of one total against a count from another - which is the shape of the defect
    # these replace, where 813 and 282 were correct against two different populations.
    (
        r"(\d+) of (\d+) creature blueprints bleed",
        ["creature-blueprints-bleeding", "creature-blueprints"],
    ),
    (
        r"(\d+) of (\d+) creature blueprints carry nothing at all",
        ["creature-inventory-none", "creature-blueprints"],
    ),
    (
        r"(\d+) of (\d+) creature blueprints carry only natural gear",
        ["creature-inventory-natural", "creature-blueprints"],
    ),
    (
        r"(\d+) of (\d+) creature blueprints are dead to `RustOnHit`",
        ["creature-rust-dead", "creature-blueprints"],
    ),
    (
        r"(\d+) of (\d+) creature blueprints have a rustable item",
        ["creature-rustable", "creature-blueprints"],
    ),
    # The humanoid subset. "humanoid creature blueprints" cannot collide with the patterns above:
    # those require the digits to sit immediately before " creature", and here "humanoid" is in
    # the way. Kept explicit rather than made optional so a sentence cannot quote a humanoid count
    # against the whole-bestiary denominator.
    (
        r"(\d+) of (\d+) humanoid creature blueprints have a rustable item",
        ["humanoid-rustable", "humanoid-blueprints"],
    ),
    (
        r"(\d+) of (\d+) humanoid creature blueprints are dead to `RustOnHit`",
        ["humanoid-rust-dead", "humanoid-blueprints"],
    ),
    (
        r"(\d+) of (\d+) humanoid creature blueprints carry nothing at all",
        ["humanoid-inventory-none", "humanoid-blueprints"],
    ),
    (r"thermal mk I is `ThermalGrenade (-?\d+)`", ["heat-grenade-delta"]),
    (r"freeze mk I is `ThermalGrenade (-?\d+)`", ["cold-grenade-delta"]),
    (r"`HeatGrenade1` at `TemperatureDelta=\"(-?\d+)\"`", ["heat-grenade-delta"]),
    (r"`ColdGrenade1` at `(-?\d+)`", ["cold-grenade-delta"]),
    (r"poison gas mk I is (\d+)", ["poison-gas-density"]),
    (r"sleep gas mk I is (\d+)", ["sleep-gas-density"]),
    (
        r"flashbang mk I is R(\d+), (\d+d\d+\+\d+)",
        ["flashbang-radius", "flashbang-duration"],
    ),
    (
        r"force ([\d,]+) against ([\d,]+); (\d+d\d+) against (\d+d\d+)",
        ["boomrose-force", "he-grenade-force", "boomrose-damage", "he-grenade-damage"],
    ),
    # Anchored on "All are", not on the attribute alone: the bare phrasing also matches
    # §6.3's note about this mod's carbideweave cloak, which has nothing to do with Boomrose.
    (r"All are `Commerce Value=\"([\d.]+)\"`", ["boomrose-value"]),
    (
        r"`StrengthPenetration=\"(\d+)\"` over `(\d+d\d+)` damage",
        ["boomrose-penetration", "boomrose-base-damage"],
    ),
]


# What the wiki quotes, kept apart from CLAIMS because the two are read against different files and
# in different runs. The wiki is a separate repository, cloned only under --wiki, so a pattern here
# has nothing to match during an ordinary run - and `claim-coverage` must not call that dead. Keeping
# them in one table would mean every entry carrying a scope marker; two tables carry it in the name.
#
# The phrasings differ from the repository's on purpose. The wiki is written for a player and
# docs/FEATURES.md for a contributor, so "Twelve options live in Qud's own options menu" is a wiki
# sentence and will never appear in docs/. That is the cost of checking prose, and #422 already
# settled that it is cheaper than the alternative.
WIKI_CLAIMS: list[tuple[str, list[str]]] = [
    (r"([\w-]+) options live in Qud's own options menu", ["options"]),
    (r"([\w-]+) options sit in Qud's own options menu", ["options"]),
    (r"which of the ([\w-]+) to set", ["options"]),
    (r"one of ([\w-]+) affinities", ["subtypes"]),
    (r"The ([\w-]+) split into two groups", ["subtypes"]),
    (r"the ([\w-]+) affinities", ["subtypes"]),
    (r"which of the ([\w-]+) Psionic Adept affinities", ["subtypes"]),
    (r"([\w-]+) affinities to pick from", ["subtypes"]),
    # The genotype/slot table on Common-questions.md. Anchored on the row rather than on the number
    # so it cannot match a sentence that happens to say "True Kin" near a 2.
    (r"\| True Kin \| ([\w-]+) \|", ["chip-slots-truekin"]),
    (r"\| Psionic Adept \| ([\w-]+) \|", ["chip-slots-psionicadept"]),
    (r"([\w-]+) of them — battle axe", ["vibro-weapons"]),
]


# Patterns deliberately kept live while nothing matches them. `claim-coverage` fails any other
# pattern that matches nothing, so this is the line between "idle on purpose" and "went dead when
# somebody reworded a sentence" - which is the defect #422 was filed for, twice over.
#
# Keep this list short. An entry here is a check that is not running.
IDLE_PHRASINGS: dict[str, str] = {
    # The census matrix (#242) registers nine ways to state one survey so that whichever phrasing
    # a document reaches for is the one checked. Four have no home today. Deleting them would mean
    # a sentence could appear later with nothing watching it, which is how the census went wrong
    # the first time.
    r"(\d+) of (\d+) creature blueprints carry nothing at all": "census matrix (#242)",
    r"(\d+) of (\d+) creature blueprints have a rustable item": "census matrix (#242)",
    r"(\d+) of (\d+) humanoid creature blueprints are dead to `RustOnHit`": "census matrix (#242)",
    r"(\d+) of (\d+) humanoid creature blueprints carry nothing at all": "census matrix (#242)",
    # Its only home is a changelog entry quoting a historical bug report, and CHANGELOG.md is
    # COUNT_EXEMPT because its figures describe a past state on purpose.
    r"(\d+) referenced, (\d+) defined": "quoted only inside CHANGELOG.md",
}


# Each pattern's capture groups map, in order, to the facts they must equal.
# What the Steam Workshop description claims, kept apart from CLAIMS for the same reason
# WIKI_CLAIMS is: it is read against a different file. This one is not Markdown either - the text
# lives inside a JSON string, so it is decoded before matching rather than pattern-matched against
# the escaped source.
#
# It is the least defended text in the project and among the most read (#459).
# `check_workshop_description` in validate_mod.py has always measured the Description's *length*
# against Steam's limit and never its contents, so "Twelve settings in Qud's own options menu"
# survived six new options across two releases. A wrong figure here reaches someone deciding whether
# to subscribe, and it cannot be quietly corrected afterwards - it ships with a release.
#
# Deliberately absent: whether the options *list* is complete. The bullets are prose rather than IDs
# and no honest pattern matches them. The count is what prompts a human to reread the list, which is
# exactly how the six missing ones were found.
WORKSHOP_CLAIMS: list[tuple[str, list[str]]] = [
    (r"\[b\]([\w-]+) settings in Qud's own options menu", ["options"]),
    (r"(\d+) subtypes, sprites by Noble Lark", ["subtypes"]),
    (r"\[b\](\d+) psionic chips\[/b\]", ["chips"]),
    (r"(\d+) psionic subtype sprites", ["subtype-sprites"]),
]


WORKSHOP = MOD / "workshop.json"


def workshop_description() -> str:
    """The Steam description as a player reads it, decoded out of the JSON string.

    Empty when the file is missing or malformed: `check_json` in the pre-commit hook owns the
    malformed case, and reporting it twice in different words helps nobody.
    """
    if not WORKSHOP.is_file():
        return ""
    try:
        data = json.loads(WORKSHOP.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return ""
    return data.get("Description", "")


def claim_text(doc: Path) -> str:
    """The text a claim pattern is matched against.

    Every source is read through here so `check_workshop_counts` and `check_claim_coverage` see the
    *same* string. Matching the raw JSON in one and the decoded description in the other would work
    today and rot the first time a claim landed either side of a newline - `\n` in the source, a
    real break in the description.
    """
    if doc == WORKSHOP:
        return workshop_description()
    return doc.read_text(encoding="utf-8")


CLAIMS: list[tuple[str, list[str]]] = [
    # Required checks. Written as words in every document that carries them, so the patterns
    # capture \w+ and WORD_NUMBERS resolves it. This claim was wrong for an unknown length of
    # time - six copies said ten while nine were enforced - which is why it is checked now.
    (
        r"([\w-]+) checks run on every pull request and all ([\w-]+) must pass",
        ["required-checks", "required-checks"],
    ),
    (
        r"([\w-]+) checks run here and all ([\w-]+) must pass",
        ["required-checks", "required-checks"],
    ),
    (
        r"\*\*([\w-]+) checks are required on every pull request\*\*",
        ["required-checks"],
    ),
    (r"not one of the ([\w-]+) checks", ["required-checks"]),
    (
        r"(\d+) new blueprints and (\d+) vanilla merges",
        ["new-blueprints", "vanilla-merges"],
    ),
    (r"\*\*(\d+)\*\* brand-new objects", ["new-blueprints"]),
    (r'\*\*(\d+)\*\* `Load="Merge"` edits', ["vanilla-merges"]),
    (
        r"\|\s*\*\*Total\*\*\s*\|\s*\*\*(\d+) active\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|",
        ["new-blueprints", "vanilla-merges"],
    ),
    (
        r"(\d+) table definitions: \*\*(\d+) merged\*\* into vanilla, \*\*(\d+) declared fresh\*\*",
        ["populations", "populations-merged", "populations-fresh"],
    ),
    (
        r"PopulationTables\.xml\s+# (\d+) tables \((\d+) merge / (\d+) new\)",
        ["populations", "populations-merged", "populations-fresh"],
    ),
    (r"\*\*(\d+)\*\* vanilla tables merged", ["populations-merged"]),
    (r"(\d+) chips\. `Mut\. level`", ["chips"]),
    (r"(\d+) psionic chips/chipsets granting", ["chips"]),
    (r"\*\*(\d+) psionic chips\*\*", ["chips"]),
    (
        r"PsionicChips\.xml\s+# (\d+) new \(1 base \+ (\d+) chips\)",
        ["chip-objects", "chips"],
    ),
    (r"(\d+) subtypes in one class", ["subtypes"]),
    (r"Psionic Adept, with (\d+) subtypes", ["subtypes"]),
    (r"All (\d+) psionic subtype sprites", ["subtype-sprites"]),
    (r"the (\d+) subtype sprites", ["subtype-sprites"]),
    (r"Textures/Subtypes/\s+# (\d+) sprites", ["subtype-sprites"]),
    (r"([\w-]+) options, all under", ["options"]),
    (r"The ([\w-]+) retuned attribute requirements", ["optioned-requirements"]),
    (r"([\w-]+) options, in Qud's own options menu", ["options"]),
    (r"Options\.xml\s+# (\d+) options", ["options"]),
    (r"Scripting/\s+# (\d+) files", ["scripting-files"]),
    (r"(\d+) referenced, (\d+) defined", ["mutation-stubs", "mutation-stubs"]),
    (
        r"MeleeWeapons\.xml\s+# (\d+) new / (\d+) merged",
        ["file:MeleeWeapons.xml:new", "file:MeleeWeapons.xml:merged"],
    ),
    (
        r"RangedWeapons\.xml\s+# (\d+) new / (\d+) merged",
        ["file:RangedWeapons.xml:new", "file:RangedWeapons.xml:merged"],
    ),
    (
        r"OtherEquipment\.xml\s+# (\d+) new / (\d+) merged",
        ["file:OtherEquipment.xml:new", "file:OtherEquipment.xml:merged"],
    ),
    (
        r"Armor\.xml\s+# (\d+) new / (\d+) merged",
        ["file:Armor.xml:new", "file:Armor.xml:merged"],
    ),
    (
        r"Cybernetics\.xml\s+# (\d+) new / (\d+) merged",
        ["file:Cybernetics.xml:new", "file:Cybernetics.xml:merged"],
    ),
]


# -------------------------------------------------------------------------- checks


class Findings:
    def __init__(self) -> None:
        self.items: list[tuple[str, str]] = []

    def add(self, check: str, detail: str) -> None:
        self.items.append((check, detail))


def vanilla_figures() -> dict[str, str]:
    """The figures snapshot_qud_api.py read out of the game. Absent snapshot, absent check."""
    if not QUD_API_PATH.is_file():
        return {}
    try:
        return json.loads(QUD_API_PATH.read_text()).get("figures") or {}
    except json.JSONDecodeError:
        return {}


# Every marker git writes into a conflicted file. `|||||||` is the diff3 base marker -- the third
# section, showing the common ancestor -- and it is the one pre-commit's check-merge-conflict hook
# does NOT match. #446: a resolution that removed the other three and left this one passed that
# hook, passed every check here, passed CI, and merged.
#
# The three with a trailing space, and the bare "=======" line, are matched exactly as the upstream
# hook matches them. That precision is the point: "=======" is also a Markdown setext underline for
# an H1, and LICENSE-CONTENT rules its sections off with 71 of them. A startswith on seven-then-
# newline distinguishes a conflict marker from both.
CONFLICT_MARKERS = ("<<<<<<< ", "||||||| ", "======= ", ">>>>>>> ")
CONFLICT_BARE = "======="


def tracked_files() -> list[Path]:
    """Every file git tracks. Binary ones are skipped when they fail to decode."""
    out = subprocess.run(
        ["git", "ls-files", "-z"], capture_output=True, text=True, check=True
    ).stdout
    return [Path(p) for p in out.split("\0") if p]


def check_conflict_markers(f: Findings) -> int:
    """No tracked file carries a leftover conflict marker.

    Scans everything git tracks rather than the document list, because the marker that got through
    was in CHANGELOG.md but nothing about the failure was specific to a document -- a resolution
    can leave one anywhere, and the file it lands in is the file nobody was reading.

    Returns the number of files scanned, so a run that silently scanned nothing is visible.
    """
    scanned = 0
    for path in tracked_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue  # binary, or a submodule pointer
        scanned += 1
        for number, line in enumerate(text.split("\n"), start=1):
            hit = next((m for m in CONFLICT_MARKERS if line.startswith(m)), None)
            if hit is None and line == CONFLICT_BARE:
                hit = CONFLICT_BARE
            if hit is not None:
                f.add(
                    "conflict-markers",
                    f"{path}:{number}: leftover conflict marker {hit.strip()!r}",
                )
    return scanned


def check_vanilla_figures(f: Findings) -> int:
    """Hold every quoted vanilla figure to what the game actually says."""
    figures = vanilla_figures()
    if not figures:
        return 0
    checked = 0
    for doc in figure_sources():
        if not doc.is_file():
            continue
        text = doc.read_text()
        for pattern, names in VANILLA_CLAIMS:
            for m in re.finditer(wrapped(pattern), text):
                for group, name in enumerate(names, start=1):
                    expected = figures.get(name)
                    if expected is None:
                        f.add(
                            "vanilla-figure",
                            f"{doc}: no figure called {name} in {QUD_API_PATH} - "
                            f"add it to CITED_FIGURES and regenerate",
                        )
                        continue
                    checked += 1
                    written = m.group(group).replace(",", "")
                    if written != expected.replace(",", ""):
                        f.add(
                            "vanilla-figure",
                            f"{doc}: quotes {name} as {m.group(group)}, but the game says "
                            f"{expected}. Either Qud changed it or the sentence is wrong.",
                        )
    return checked


def check_wiki_counts(wiki: Path, f: Findings, known: dict[str, int]) -> int:
    """Every figure the wiki quotes, against the mod it describes.

    Until #427 the wiki was checked for broken links and nothing else, and a sweep found **nine wrong
    figures** across five pages: eleven options where twelve ship, an extra cybernetics licence point
    no caste grants any more, eight vibro weapons where eleven exist. None of it was catchable,
    because nothing read the content. The wiki also has no version selector, so whatever it says is
    what every player sees on every version - which makes it the least defended documentation in the
    project and the most read.

    This reaches seven of those nine. The two it cannot are prose with no figure in them, and the
    worse of those - *"a Mutated Human can wear one"* - is the one that actually shipped. See
    `chip_slots` for why that row has no fact behind it.
    """
    checked = 0
    for page in sorted(wiki.glob("*.md")):
        text = page.read_text(encoding="utf-8")
        for pattern, names in WIKI_CLAIMS:
            for m in re.finditer(wrapped(pattern), text):
                for group, name in enumerate(names, start=1):
                    raw = m.group(group)
                    if raw.isdigit():
                        claimed = int(raw)
                    elif raw.lower() in WORD_NUMBERS:
                        claimed = WORD_NUMBERS[raw.lower()]
                    else:
                        f.add(
                            "wiki-figure",
                            f"{page.name}: {raw!r} is not a number this script knows - add it to "
                            f"WORD_NUMBERS rather than leaving the claim unchecked",
                        )
                        continue
                    checked += 1
                    if name not in known:
                        f.add(
                            "wiki-figure",
                            f"{page.name}: pattern names unknown fact {name!r}",
                        )
                    elif claimed != known[name]:
                        f.add(
                            "wiki-figure",
                            f"{page.name}: says {name} is {claimed}; the mod says {known[name]} "
                            f"- the wiki has no version selector, so this is what every player "
                            f"reads",
                        )
    return checked


def check_workshop_counts(f: Findings, known: dict[str, int]) -> int:
    """Recount the Workshop description's figures from `mod/`.

    Same machinery as `check_counts`, pointed at the one file it never read. Returns how many
    figures were verified, so a silently-dead pattern shows up as a falling total rather than as
    nothing at all.
    """
    text = claim_text(WORKSHOP)
    if not text:
        return 0
    checked = 0
    for pattern, names in WORKSHOP_CLAIMS:
        for m in re.finditer(wrapped(pattern), text):
            for group, name in enumerate(names, start=1):
                raw = m.group(group)
                if raw.isdigit():
                    claimed = int(raw)
                elif raw.lower() in WORD_NUMBERS:
                    claimed = WORD_NUMBERS[raw.lower()]
                else:
                    f.add(
                        "workshop-figure",
                        f"workshop.json: {raw!r} is not a number this script knows - add it to "
                        f"WORD_NUMBERS rather than leaving the claim unchecked",
                    )
                    continue
                checked += 1
                if name not in known:
                    f.add(
                        "workshop-figure",
                        f"workshop.json: pattern names unknown fact {name!r}",
                    )
                elif claimed != known[name]:
                    f.add(
                        "workshop-figure",
                        f"workshop.json says {name} is {claimed}; the mod says {known[name]} "
                        f"- this is the text on the Workshop page, so it ships with the release "
                        f"and cannot be corrected quietly afterwards",
                    )
    return checked


def check_workshop_version(f: Findings) -> None:
    """The description's version must be the version being shipped.

    Two places go stale at the same moment `manifest.json` bumps, and neither is a figure any
    recount reaches: the `New in X.Y.Z` heading and the version under `Version and saves`. This is
    the coupling `check_version_matches_changelog` already holds for the changelog, one file
    further out.

    Both patterns are anchored on their surrounding markup rather than matching a bare version
    number, because the description legitimately cites *older* releases - "It shipped in 2.3.0 with
    a bleed that could never fire" is history and must not be dragged forward.
    """
    text = claim_text(WORKSHOP)
    manifest = MOD / "manifest.json"
    if not text or not manifest.is_file():
        return
    try:
        version = json.loads(manifest.read_text(encoding="utf-8-sig")).get("version")
    except json.JSONDecodeError:
        return  # check_json owns this
    if not version:
        return

    sites = [
        (r"\[h1\]New in (\d+\.\d+\.\d+)\[/h1\]", "the 'New in' heading"),
        (
            r"\[h1\]Version and saves\[/h1\]\s*\[b\](\d+\.\d+\.\d+)\.\[/b\]",
            "the version under 'Version and saves'",
        ),
    ]
    for pattern, where in sites:
        found = re.findall(pattern, text)
        if not found:
            f.add(
                "workshop-version",
                f"workshop.json: {where} is missing or reworded, so nothing checks it against "
                f"manifest.json - restore the phrasing or update the pattern",
            )
            continue
        for claimed in found:
            if claimed != version:
                f.add(
                    "workshop-version",
                    f"workshop.json: {where} says {claimed}; manifest.json ships {version}",
                )


def check_claim_coverage(f: Findings, wiki: Path | None = None) -> None:
    """Every claim pattern must match something, or say why it does not.

    `check_counts` and `check_vanilla_figures` both walk `re.finditer`, so a pattern that matches
    nothing contributes nothing and the run still passes. The only visible effect is that the
    "N documented figure(s)" total is quietly lower than it should be, and nothing knows what N is
    supposed to be.

    #422 found that costing two live figures at once. `README.md` had drifted to **348** new
    blueprints against 400, and to eleven options against twelve, and both patterns had gone silent
    - one because the sentence was reflowed across a line, one because it was reworded. The check
    written to catch drifting counts had itself drifted, in the direction that reports nothing.

    So this is the same argument #402 made for `check-names`: a registry is worth having only if it
    is read in both directions. `IDLE_PHRASINGS` carries the exceptions, and being on it is a claim
    that wants justifying rather than a place to put an inconvenient failure.
    """
    counted = [d for d in DOCS if d.is_file() and d not in COUNT_EXEMPT]
    everywhere = [d for d in figure_sources() if d.is_file()]

    tables = [
        ("CLAIMS", CLAIMS, counted),
        ("VANILLA_CLAIMS", VANILLA_CLAIMS, everywhere),
        ("WORKSHOP_CLAIMS", WORKSHOP_CLAIMS, [WORKSHOP] if WORKSHOP.is_file() else []),
    ]
    # WIKI_CLAIMS is only checkable when there is a wiki to check it against. Including it on an
    # ordinary run would report all ten as dead - the false failure #427 flagged before any of this
    # was written, and a check that cries wolf every run is one people learn to skip.
    if wiki is not None:
        tables.append(("WIKI_CLAIMS", WIKI_CLAIMS, sorted(wiki.glob("*.md"))))

    for label, patterns, sources in tables:
        for pattern, _ in patterns:
            if any(re.search(wrapped(pattern), claim_text(doc)) for doc in sources):
                continue
            reason = IDLE_PHRASINGS.get(pattern)
            if reason:
                continue
            f.add(
                "claim-coverage",
                f"tools/check_docs.py: the {label} pattern {pattern!r} matches nothing - "
                f"either the sentence it describes was reworded or removed, or the pattern "
                f"belongs in IDLE_PHRASINGS with a reason",
            )

    for pattern in sorted(IDLE_PHRASINGS):
        registered = (
            {p for p, _ in CLAIMS}
            | {p for p, _ in VANILLA_CLAIMS}
            | {p for p, _ in WIKI_CLAIMS}
            | {p for p, _ in WORKSHOP_CLAIMS}
        )
        if pattern in registered:
            continue
        f.add(
            "claim-coverage",
            f"tools/check_docs.py: IDLE_PHRASINGS lists {pattern!r}, which is in none of "
            f"CLAIMS, VANILLA_CLAIMS or WIKI_CLAIMS - an exemption for a pattern that does "
            f"not exist",
        )


def check_counts(f: Findings, known: dict[str, int]) -> int:
    checked = 0
    for doc in DOCS:
        if not doc.is_file() or doc in COUNT_EXEMPT:
            continue
        text = doc.read_text()
        for pattern, names in CLAIMS:
            for m in re.finditer(wrapped(pattern), text):
                for group, name in enumerate(names, start=1):
                    checked += 1
                    raw = m.group(group)
                    if raw.isdigit():
                        claimed = int(raw)
                    elif raw.lower() in WORD_NUMBERS:
                        claimed = WORD_NUMBERS[raw.lower()]
                    else:
                        f.add(
                            "counts",
                            f"{doc}: {raw!r} is not a number this script knows - add it to "
                            f"WORD_NUMBERS rather than leaving the claim unchecked",
                        )
                        continue
                    if name not in known:
                        f.add("counts", f"{doc}: pattern names unknown fact {name!r}")
                    elif claimed != known[name]:
                        f.add(
                            "counts",
                            f"{doc} says {name} is {claimed}; recounted from mod/ it is "
                            f"{known[name]} — {m.group(0)[:60]!r}",
                        )
    return checked


def required_checks() -> dict:
    """The intended required-check list, committed so it is reviewable in a pull request."""
    return json.loads(REQUIRED_CHECKS_PATH.read_text())


def workflow_jobs() -> dict[str, str]:
    """Map "file:jobkey" -> the check name GitHub will report for it.

    A job's check name is its `name:` if it has one, and its key otherwise. Parsed with regexes
    rather than a YAML library because this script is standard-library only, which is the same
    constraint tools/validate_mod.py works under.
    """
    jobs: dict[str, str] = {}
    for wf in CI_WORKFLOWS:
        if not wf.is_file():
            continue
        body = wf.read_text()
        body = body.split("\njobs:\n", 1)[-1]
        for key, block in re.findall(
            r"^  ([a-z][\w-]*):\n((?:    .*\n|\n)*)", body, re.MULTILINE
        ):
            name = re.search(r"^    name:\s*(.+?)\s*$", block, re.MULTILINE)
            jobs[f"{wf.name}:{key}"] = name.group(1) if name else key
    return jobs


def check_required_checks(f: Findings) -> None:
    """Every CI job is required, or is deliberately not. Neither by accident.

    This is the check that would have caught #152's defect: Tests existed as a job, passed on
    every pull request, and was not in the ruleset, so a failing test suite could have merged.
    Nothing compared the two lists because one of them lived only in GitHub's settings.
    """
    data = required_checks()
    required = {e["context"]: e["source"] for e in data["required"]}
    exempt = {e["context"]: e for e in data.get("not_required", [])}
    jobs = workflow_jobs()

    for context, source in required.items():
        if source.startswith("github:"):
            continue  # external to the repository; --ruleset is the only way to see these
        if source not in jobs:
            f.add(
                "required-checks",
                f"{REQUIRED_CHECKS_PATH} requires {context!r} from {source}, which is not a job "
                f"in any workflow - a required check that never reports blocks every merge",
            )
        elif jobs[source] != context:
            f.add(
                "required-checks",
                f"{REQUIRED_CHECKS_PATH} calls {source} {context!r} but the workflow names it "
                f"{jobs[source]!r} - GitHub matches on the reported name",
            )

    for source, name in sorted(jobs.items()):
        if name in required or name in exempt:
            continue
        f.add(
            "required-checks",
            f"workflow job {source} reports {name!r}, which is neither required nor listed under "
            f"not_required - decide which and record it in {REQUIRED_CHECKS_PATH}",
        )

    for context, entry in exempt.items():
        if not entry.get("reason"):
            f.add(
                "required-checks",
                f"{context!r} is exempt from being required with no reason given",
            )


PRECOMMIT_CONFIG = Path(".pre-commit-config.yaml")

# A tool pinned in both places, and how to read the CI side of it.
#
# The map is explicit rather than derived, and the reason is `gitleaks`: the hook is
# gitleaks/gitleaks at v8.30.1 and the workflow uses gitleaks/gitleaks-action at v3.0.0. Those are
# different repositories on independent version lines, so any rule that pairs them by owner or by
# prefix reports drift that is not there - and docs/LESSONS.md is clear that a guard firing on a
# correct action teaches people to reach for the bypass.
PIN_PAIRS = {
    "ruff": (
        "https://github.com/astral-sh/ruff-pre-commit",
        r"pipx install ruff==([0-9][\w.]*)",
    ),
    "typos": (
        "https://github.com/crate-ci/typos",
        r"uses:\s*crate-ci/typos@[0-9a-f]{40}\s*#\s*v?([0-9][\w.]*)",
    ),
}

# Pinned hooks with no CI counterpart to compare against. Each carries its reason, the way
# required-checks makes an exemption a sentence somebody had to write rather than a silent omission.
PIN_UNPAIRED = {
    "https://github.com/pre-commit/pre-commit-hooks": (
        "no CI counterpart - these hooks run only locally"
    ),
    "https://github.com/gitleaks/gitleaks": (
        "ci.yml uses gitleaks/gitleaks-action, a different repository on its own version line - "
        "v3 against the scanner's v8"
    ),
}


def precommit_pins() -> dict[str, str]:
    """Map each pinned pre-commit repo URL to its rev.

    Regexes rather than a YAML library, for the same standard-library-only reason
    workflow_jobs() gives. A `rev:` is matched against the most recent `- repo:` above it, so
    comment lines between the two - which both pinned tools now carry - are stepped over rather
    than breaking the pairing. `- repo: local` declares no rev and so never enters the map.
    """
    if not PRECOMMIT_CONFIG.is_file():
        return {}
    pins: dict[str, str] = {}
    repo: str | None = None
    for line in PRECOMMIT_CONFIG.read_text().splitlines():
        m = re.match(r"\s*-\s*repo:\s*(\S+)", line)
        if m:
            repo = m.group(1)
            continue
        m = re.match(r"\s*rev:\s*(\S+)", line)
        if m and repo is not None:
            pins[repo] = m.group(1)
            repo = None
    return pins


def check_pin_parity(f: Findings) -> int:
    """A tool pinned twice must carry the same version in both places.

    `ruff` and `typos` are each pinned in .github/workflows/ci.yml and in
    .pre-commit-config.yaml, and Dependabot tracks the halves in separate ecosystems - the action
    under `github-actions`, the hook under `pre-commit`. It raises one without the other, in either
    order, and nothing ever raises both. While they disagree CI runs a different version of a
    checker than the hook a contributor just ran.

    Both pairs drifted the day this was written and neither was caught by anything mechanical.
    The typos pair is the one that matters: it drifted with no comment and nothing watching, and
    what surfaced it was luck - v1.49.1 stopped correcting one brand name, a changelog entry
    happened to need that word, and the older hook rejected the sentence the newer action accepted.
    Any other word in that release and both pull requests would have merged green. #787.

    Scope is deliberately the two config files. A version written anywhere else - a tool's own
    config, or prose - is out of reach here and stays that way, because a check that sweeps wider
    than it can parse is how a skip starts reading as a pass.
    """
    hooks = precommit_pins()
    if not hooks:
        f.add(
            "pin-parity",
            f"{PRECOMMIT_CONFIG} declares no pinned repo - either it is missing or the format "
            f"moved, and either way nothing below this line is being checked",
        )
        return 0

    ci = "\n".join(w.read_text() for w in CI_WORKFLOWS if w.is_file())

    checked = 0
    for tool, (repo, pattern) in sorted(PIN_PAIRS.items()):
        if repo not in hooks:
            f.add(
                "pin-parity",
                f"{PRECOMMIT_CONFIG} no longer pins {repo} - {tool} is mapped as a two-place pin "
                f"and one of the places has gone",
            )
            continue
        found = sorted(set(re.findall(pattern, ci)))
        if not found:
            # A skip here would be indistinguishable from a pass, which is the failure this whole
            # file keeps recording. A reworded comment or a replaced install line is a finding.
            f.add(
                "pin-parity",
                f"could not read the {tool} version out of the CI workflows - the pin was "
                f"reworded or removed, so this pair is no longer being compared",
            )
            continue
        if len(found) > 1:
            f.add(
                "pin-parity",
                f"the CI workflows pin {tool} at more than one version ({', '.join(found)}) - "
                f"they disagree with each other before anything compares them to the hook",
            )
            continue
        hook_version = hooks[repo].lstrip("v")
        if found[0] != hook_version:
            f.add(
                "pin-parity",
                f"{tool} is pinned at {found[0]} in the CI workflows and {hooks[repo]} in "
                f"{PRECOMMIT_CONFIG} - CI runs a different version than the hook a contributor "
                f"just ran",
            )
            continue
        checked += 1

    # The anti-expiry half. A check that names only the tools there are currently two of stops
    # covering the file the moment a third arrives, and says nothing while it happens - which is
    # exactly how naming-option-coverage went quiet when a second namestyle landed.
    mapped = {repo for repo, _ in PIN_PAIRS.values()}
    for repo in sorted(hooks):
        if repo in mapped or repo in PIN_UNPAIRED:
            continue
        f.add(
            "pin-parity",
            f"{PRECOMMIT_CONFIG} pins {repo}, which is in neither PIN_PAIRS nor PIN_UNPAIRED - "
            f"add it to whichever applies, with a reason if it has no CI counterpart",
        )

    for repo, reason in sorted(PIN_UNPAIRED.items()):
        if not reason:
            f.add(
                "pin-parity", f"{repo} is exempt from pin parity with no reason given"
            )

    return checked


# The mutation a chip part grants, read off whichever base it inherits. #411 added
# Raven_ModVariantMutationBase for the two mutations that need a variant, and matching only the
# stock name silently dropped both from Appendix B - the rows stopped resolving to a blueprint
# rather than reporting a wrong figure, which is the quieter of the two failures.
MUTATION_PART = re.compile(
    r"(?:ModImprovedMutationBase|Raven_ModVariantMutationBase)<(\w+)>"
)
COLOUR_MARKUP = re.compile(r"\{\{[^|}]*\|([^}]*)\}\}")


def _plain(text: str) -> str:
    """A display name with Qud's colour markup taken off."""
    return COLOUR_MARKUP.sub(r"\1", text or "").replace("{{", "").replace("}}", "")


def chips_from_blueprints() -> dict[tuple[str, str], tuple[str, list[str]]]:
    """Recompute Appendix B from the blueprints: (name, item tier) -> (value, grants).

    Keyed on the pair rather than the display name alone, because a display name is not unique.
    #347 flattened the three Kindle chips and the three Frost Webs chips onto one name each - they
    grant the same thing, so they now say the same thing - and three blueprints sharing a name used
    to overwrite each other here, leaving the appendix able to describe only whichever parsed last.
    The item tier still separates them, because it is what puts each one in its own loot pool.

    Every column is data that was typed into the document by hand, and typed data drifts. Three
    rows still named `GasGeneration` months after #258 renamed it, and I corrected the three
    single-chip rows earlier the same day while missing the three chipsets - which is how well
    re-reading a 144-row table works.

    Mod-only, so this runs in CI where there is no game. The armour and weapon tables in 6 and 7
    were the obvious next targets, and this used to say they needed an installed game because 43 of
    their rows are `merge` edits to vanilla blueprints. That was the wrong way round, and measuring
    rather than reasoning is what showed it: a merge that changes a figure *declares* it, so of the
    121 cells on those 43 rows exactly one is not in the mod's own XML. `check_item_tables` does
    them on the same bargain as this, not a different one (#287).
    """
    granted: dict[str, str] = {}
    for cs in sorted((MOD / "Scripting").glob("Raven_Mod*.cs")):
        found = MUTATION_PART.search(cs.read_text(encoding="utf-8-sig"))
        if found:
            granted[cs.stem] = found.group(1)

    chips: dict[tuple[str, str], tuple[str, list[str]]] = {}
    for path in sorted((MOD / "ObjectBlueprints").glob("*.xml")):
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue  # check_wellformed in validate_mod.py owns this failure
        for obj in root.iter("object"):
            name = value = tier = None
            grants: list[str] = []
            for part in obj.iter("part"):
                which = part.get("Name", "")
                if which == "Render" and part.get("DisplayName"):
                    name = _plain(part.get("DisplayName"))
                elif which == "Commerce":
                    value = part.get("Value")
                elif which in granted:
                    grants.append(f"{granted[which]} @ {part.get('Tier')}")
            for tag in obj.iter("tag"):
                if tag.get("Name") == "Tier":
                    tier = tag.get("Value")
            if grants and name:
                chips[(name, tier)] = (value, sorted(grants))
    return chips


def check_appendix_b(f: Findings) -> int:
    """Every row of FEATURES.md's chip appendix must match the blueprint it describes."""
    doc = Path("docs/FEATURES.md")
    if not doc.is_file():
        return 0

    chips = chips_from_blueprints()
    lines = doc.read_text().splitlines()
    start = next(
        (i for i, line in enumerate(lines) if line.startswith("## Appendix B")), None
    )
    if start is None:
        f.add("appendix-b", "docs/FEATURES.md has no '## Appendix B' heading to check")
        return 0

    seen, rows = set(), 0
    for offset, line in enumerate(lines[start:], start=start):
        if line.startswith("## ") and not line.startswith("## Appendix B"):
            break
        if not line.startswith("|") or "---" in line or "Item tier" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 4:
            continue
        rows += 1
        name, tier, value, grants = cells
        seen.add((name, tier))
        if (name, tier) not in chips:
            f.add(
                "appendix-b",
                f"docs/FEATURES.md:{offset + 1}: no blueprint renders as {name!r} "
                f"at item tier {tier}",
            )
            continue
        want_value, want_grants = chips[(name, tier)]
        # Order-insensitive: a chipset grants three mutations and the document's order is its own.
        have_grants = sorted(g.strip() for g in grants.split(","))
        for label, have, want in (
            ("value", value, want_value),
            ("grants", ", ".join(have_grants), ", ".join(want_grants)),
        ):
            if have != want:
                f.add(
                    "appendix-b",
                    f"docs/FEATURES.md:{offset + 1}: {name} {label} is {have!r}, "
                    f"blueprints say {want!r}",
                )

    for missing_name, missing_tier in sorted(set(chips) - seen):
        f.add(
            "appendix-b",
            f"docs/FEATURES.md Appendix B has no row for {missing_name!r} "
            f"at item tier {missing_tier}",
        )
    return rows


ITEM_COLUMNS = (
    ("Tier", "tag", "Tier"),
    ("Value", "part", "Commerce"),
    ("Weight", "part", "Physics"),
    # Added after #367. When #365 reverted 61 `Stat="Agility"` declarations, 65 table cells still
    # said Agility and nothing failed - the two `item-tables` findings that did fire were about
    # deleted blueprints, not wrong values. Sixty-five stale cells is a larger drift than any
    # checked column has ever carried.
    ("Stat", "part", "MeleeWeapon"),
    # Damage and AV, added after #322 and #318 respectively. Both are typed figures the documents
    # quote and nothing verified: 50 damage cells and 15 AV cells had to be corrected by hand when
    # their blueprints moved, which is a larger drift than any checked column has carried. The
    # fourth element is the attribute name where it differs from the column heading.
    ("Damage", "part", "MeleeWeapon", "BaseDamage"),
    ("AV", "part", "Armor", "AV"),
    ("AV", "part", "Shield", "AV"),
    # DV, added after #381. The vambrace line's DV column had been noise for nine items - it ran
    # -1, 0, -2, -1, 0, -3, -2, -1, 0 - and flattening it to 0 left nine stale cells that nothing
    # reported, because this tuple listed every other armour figure and not this one. #337 named
    # "AV, weight, damage or drop weight"; DV was simply never on the list.
    ("DV", "part", "Armor", "DV"),
)
# A cell holding one of these is documenting an absence, not a figure, and has nothing to compare.
NOT_A_FIGURE = {"", "-", "\u2014", "(inh)"}


def item_table_index() -> tuple[BlueprintIndex, dict[str, str]]:
    """The mod's blueprints, plus a map from how a table writes a name to the blueprint's own.

    The tables name things three different ways and all three are in use: the blueprint itself
    (`Cudgel8th`), the blueprint with its prefix dropped (`Fullerite Greathammer` for
    `Raven_Fullerite Greathammer`), and the rendered display name. Resolving all three is what
    takes this from partial to every row - 254 of 254.
    """
    roots = []
    for path in sorted((MOD / "ObjectBlueprints").glob("*.xml")):
        try:
            roots.append(ET.parse(path).getroot())
        except ET.ParseError:
            continue
    index = BlueprintIndex(roots)
    names: dict[str, str] = {}

    def key(text: str) -> str:
        return re.sub(r"[^a-z0-9]", "", text.lower())

    for name in index.objects:
        names.setdefault(key(name), name)
        names.setdefault(key(re.sub(r"^(?:Raven_|Vixy_)", "", name)), name)
        shown = index.part_attr(name, "Render", "DisplayName")
        if shown:
            names.setdefault(key(re.sub(r"\{\{[^|]*\|([^}]*)\}\}", r"\1", shown)), name)
    return index, names


def check_file_rows(f: Findings, known: dict[str, int]) -> int:
    """Every row of docs/FEATURES.md 6.1 against a recount of the file it names.

    The per-file figures have been computed here since the table was written and nothing ever
    quoted them, so three of eleven rows drifted unnoticed (#473). The Total row did not, because
    it is recounted from mod/ rather than added up from the rows - and two of the errors happened
    to cancel in the merged column, so even a reader adding it up by hand would have seen 211.

    A CLAIMS pattern cannot do this: a claim pairs one regex with a fixed list of fact names by
    capture group, and this needs the filename out of the row to pick the fact.

    Both directions are checked. A row naming a file that does not exist is as much a defect as a
    file with no row - the second is what let Plants.xml arrive without anyone deciding whether it
    belonged in the table.
    """
    text = Path("docs/FEATURES.md").read_text()
    heading = re.search(r"^### 6\.1 .*$", text, re.MULTILINE)
    if not heading:
        f.add(
            "file-rows",
            "docs/FEATURES.md: 6.1 heading not found - has it been renamed?",
        )
        return 0

    table = text[heading.end() :].split("\n###", 1)[0]
    row = re.compile(
        r"^\|\s*`(?P<file>[^`]+\.xml)`\s*\|"
        r"\s*(?P<new>\d+)(?:\s*\((?P<dormant>\d+) dormant\))?\s*\|"
        r"\s*(?P<merged>\d+)\s*\|",
        re.MULTILINE,
    )

    checked = 0
    seen: set[str] = set()
    for m in row.finditer(table):
        name = m.group("file")
        seen.add(name)
        if f"file:{name}:new" not in known:
            f.add(
                "file-rows",
                f"docs/FEATURES.md 6.1: row names {name}, which is not in mod/ObjectBlueprints",
            )
            continue
        for column in ("new", "merged", "dormant"):
            raw = m.group(column)
            if raw is None:
                continue
            checked += 1
            actual = known[f"file:{name}:{column}"]
            if int(raw) != actual:
                f.add(
                    "file-rows",
                    f"docs/FEATURES.md 6.1: {name} {column} says {raw}, "
                    f"recounted from mod/ it is {actual}",
                )
        if m.group("dormant") is None and known[f"file:{name}:dormant"]:
            f.add(
                "file-rows",
                f"docs/FEATURES.md 6.1: {name} holds "
                f"{known[f'file:{name}:dormant']} commented-out object(s) and the row does not "
                f"say so - write it as 'N (M dormant)'",
            )

    for key in known:
        parts = key.split(":")
        if (
            len(parts) == 3
            and parts[0] == "file"
            and parts[2] == "new"
            and parts[1] not in seen
        ):
            f.add(
                "file-rows",
                f"docs/FEATURES.md 6.1: mod/ObjectBlueprints/{parts[1]} has no row",
            )
    return checked


def check_item_tables(f: Findings) -> int:
    """Every Tier, Value and Weight in FEATURES' item tables, against the blueprint it describes.

    The same argument as Appendix B one section up: 254 rows of typed figures, and typed figures
    drift. These had done worse than drift. Nine cells disagreed with their blueprints when this
    was first run, four of them fixes from #86 that reached the blueprint and the §10 row but never
    the table, and five - the low-tier wristblades - that had never been right at all, wrong since
    the original import because nothing had ever looked (#299).

    Mod-only, so it runs in CI where there is no game. `chips_from_blueprints` predicted this would
    need one, on the reasoning that 43 of these rows are `merge` edits to vanilla blueprints. That
    turned out to be the wrong way round: a merge that changes a figure *declares* it, so the mod's
    own XML holds it. Of the 121 cells on those 43 rows, exactly one needs the game -
    `Flawless Crysteel Boots`, whose tier #86 corrected by *removing* the mod's override so
    vanilla's would apply. The fix that made it right is what makes it unverifiable here, which is
    a fair trade for 739 of 740 cells.

    Mismatch-only, deliberately. Appendix B also reports blueprints with no row, because it is an
    appendix and means to be complete. These tables are curated selections, so demanding a row for
    every blueprint would be inventing a rule the document never claimed.
    """
    doc = Path("docs/FEATURES.md")
    if not doc.is_file():
        return 0

    index, names = item_table_index()
    lines = doc.read_text().splitlines()
    header: list[str] | None = None
    compared = 0

    for offset, line in enumerate(lines):
        if line.startswith("|") and all(c in line for c in ("Tier", "Value", "Weight")):
            header = [c.strip() for c in line.strip("|").split("|")]
            continue
        if header is None:
            continue
        if not line.startswith("|"):
            header = None
            continue
        if re.fullmatch(r"\|[\s\-|]+\|", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != len(header):
            continue

        row = dict(zip(header, cells))
        shown = row.get("Blueprint", "").strip("*").strip()
        blueprint = names.get(re.sub(r"[^a-z0-9]", "", shown.lower()))
        if not blueprint:
            f.add(
                "item-tables",
                f"docs/FEATURES.md:{offset + 1}: no blueprint resolves from {shown!r}",
            )
            continue

        for spec in ITEM_COLUMNS:
            column, kind, source = spec[0], spec[1], spec[2]
            attribute = spec[3] if len(spec) > 3 else column
            documented = row.get(column, "").strip()
            if documented in NOT_A_FIGURE:
                continue
            if kind == "tag":
                actual = index.tag_value(blueprint, source)
            else:
                actual = index.part_attr(blueprint, source, attribute)
            # None means the mod never declares it, so the figure lives in the game's own files
            # and this check cannot see it. Silence is right: reporting it would be reporting
            # the absence of a game install, which is not what this checks.
            if actual is None:
                continue
            compared += 1
            if documented != actual:
                f.add(
                    "item-tables",
                    f"docs/FEATURES.md:{offset + 1}: {shown} {column.lower()} is "
                    f"{documented!r}, {blueprint} says {actual!r}",
                )
    return compared


def check_links(f: Findings) -> None:
    for doc in linked_docs():
        if not doc.is_file():
            continue
        for target in re.findall(
            r"\[[^\]]*\]\(([^)#]+?)(?:#[^)]*)?\)", doc.read_text()
        ):
            # Markdown allows <angle brackets> around a target, which is how a URL containing
            # parentheses is written - docs/WIKI.md has three. The capture keeps the leading "<",
            # so stripping it is what lets the scheme test see a scheme.
            target = target.strip("<>")
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (doc.parent / target).resolve().exists():
                f.add("links", f"{doc}: dead relative link to {target}")


def sections_of(path: Path) -> set[str]:
    return {
        m.group(1)
        for line in path.read_text().splitlines()
        if (m := re.match(r"^#+\s+(?:§\s*)?([0-9]+(?:\.[0-9a-z]+)*)\.?\s", line))
    }


def heading_numbers(path: Path) -> list[tuple[int, str]]:
    """Every numbered heading in a document, as (line number, number), in file order."""
    return [
        (i, m.group(1))
        for i, line in enumerate(path.read_text().splitlines(), 1)
        if (m := re.match(r"^#+\s+(?:§\s*)?([0-9]+(?:\.[0-9a-z]+)*)\.?\s", line))
    ]


def sort_key(number: str) -> tuple:
    """Order a section number so `17.3` < `17.3a` < `17.4`, the convention these documents use.

    A letter suffix means "inserted after", so it sorts between its parent and the next whole
    number. Each component becomes (digits, letters) - absent letters sort first, which is what
    puts the unsuffixed heading ahead of its own insertions.
    """
    parts = []
    for piece in number.split("."):
        m = re.match(r"^(\d+)([a-z]*)$", piece)
        parts.append((int(m.group(1)), m.group(2)) if m else (0, piece))
    return tuple(parts)


# A path written as prose rather than as a markdown link. `check_links` sees only
# `[text](target)`, and most of the paths in `docs/` are prose in backticks - 194 of them, against
# roughly 60 markdown links. See #735.
PROSE_DOC_PATH = re.compile(r"`([A-Za-z0-9_./-]+\.md)`")

# The marker that exempts a path the prose names deliberately. Document-scoped and it must name the
# paths, so a marker cannot silently cover a *different* rotted path that appears later on the same
# line or in the same file.
#
# The body is captured whole and the reason split off afterwards rather than excluded by the
# pattern: the first version ended the path list at any "-", which cannot express `Title-Case.md`
# or `docs/patched-surface.md`. Hyphens are ordinary in a filename and the separator is " - ".
NOT_A_FILE = re.compile(r"<!--\s*check-docs:\s*not-a-file\s+(.*?)\s*-->", re.DOTALL)

REASON_SEPARATOR = re.compile(r"\s+[-—]\s+")


def exempt_paths(text: str) -> set[str]:
    """Paths this document declares are deliberately not files here."""
    found: set[str] = set()
    for body in NOT_A_FILE.findall(text):
        names = REASON_SEPARATOR.split(body, maxsplit=1)[0]
        found.update(n.strip() for n in names.split(",") if n.strip())
    return found


def check_prose_doc_links(f: Findings) -> int:
    """Markdown paths written as prose must resolve, or say why they do not.

    `check_links` validates `[text](target)` and nothing else, so a reference written as
    `` `DESIGN_history_recon.md` `` rots silently. #647 imported a document and left
    `DESIGN_options.md` pointing at its old home; the reference was wrong from the moment of the
    import and stayed green through every run until it was found by hand.

    Scoped to `.md` deliberately. Of 194 backticked paths across these documents 93 resolve to
    nothing, and nearly all of them legitimately: vanilla game data (`Bodies.xml`), decompiled
    source (`Village.cs`), naming-convention illustrations (`snake_case.py`), and other projects'
    files. Those are `.xml`, `.cs` and `.py`. **This repository's own documents are the `.md`
    ones**, which cuts the population to six and the false positives to three - each of which now
    carries a marker naming itself.

    A whitelist in this file was the other option and is the wrong shape: it inverts to "everything
    is fine unless listed", which is how the first rotted reference got through. The marker sits
    next to the prose it excuses and has to name the path.
    """
    checked = 0
    for doc in linked_docs():
        if not doc.is_file():
            continue
        text = doc.read_text()
        exempt = exempt_paths(text)
        for i, line in enumerate(text.splitlines(), 1):
            for target in PROSE_DOC_PATH.findall(line):
                if target in exempt:
                    continue
                checked += 1
                # Prose legitimately writes a bare `LESSONS.md`, so try the places a document of
                # ours could be before calling it dead.
                if any(
                    (base / target).exists()
                    for base in (Path("."), Path("docs"), doc.parent)
                ):
                    continue
                f.add(
                    "prose-links",
                    f"{doc}:{i}: prose names {target}, which is not a file here - fix the "
                    f"reference, or mark it with "
                    f"<!-- check-docs: not-a-file {target} - why -->",
                )
    return checked


def check_heading_order(f: Findings) -> None:
    """A numbered heading that repeats one above it, or goes backwards.

    Neither changes a claim, and both make a cross-reference ambiguous - `§4.5` naming two different
    sections has no correct reading, and §15.5 sitting above §15.4 sends anyone following the
    numbering to the wrong place. `check_sections` already verifies that a cited number *exists*;
    it cannot tell that two headings answer to it, or that the order is a lie.

    This is drift rather than error: every one of the three found in #496 was a section inserted
    later without renumbering its neighbours. The documents already have a convention for that -
    a letter suffix, as in §17.3a and §18.4b - which sorts between its parent and the next number
    and needs nothing renumbered at all.
    """
    for doc in DOCS:
        if not doc.is_file():
            continue
        seen: dict[str, int] = {}
        previous: tuple | None = None
        previous_number = ""
        for line_no, number in heading_numbers(doc):
            if number in seen:
                f.add(
                    "heading-order",
                    f"{doc}:{line_no}: section {number} repeats the one at line {seen[number]} - "
                    "a cross-reference to it has no correct reading",
                )
            else:
                seen[number] = line_no
            key = sort_key(number)
            if previous is not None and key < previous:
                f.add(
                    "heading-order",
                    f"{doc}:{line_no}: section {number} comes after {previous_number}, so the "
                    "numbering and the reading order disagree",
                )
            previous, previous_number = key, number


def check_sections(f: Findings) -> None:
    known = {d.name: sections_of(d) for d in DOCS if d.is_file()}
    for doc in DOCS:
        if not doc.is_file():
            continue
        # Matches `docs/FILE.md` §N and the markdown-link form [`docs/FILE.md`](path) §N, which
        # is what README actually uses — the first version of this regex missed it entirely.
        for target, ref in re.findall(
            r"(?:docs/)?([A-Z][A-Za-z_]*\.md)`?(?:\]\([^)]*\))?\s+§\s*([0-9]+(?:\.[0-9a-z]+)*)",
            doc.read_text(),
        ):
            if target in known and known[target] and ref not in known[target]:
                f.add(
                    "sections",
                    f"{doc}: cites {target} §{ref}, which has no such section",
                )


# Keep a Changelog's section set, in its order. A heading outside this set, or a repeat of one
# inside a release, is a structural defect rather than a style preference: entries under the second
# copy read as a separate group, so a reader scanning for what changed can stop at the first and
# miss half of it.
CHANGELOG_SECTIONS = ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security")


def check_changelog_sections(f: Findings) -> None:
    """One `###` section of each kind per release block.

    This has now happened twice — two `### Fixed` blocks corrected by hand before 2.4.0, and two
    `### Added` blocks introduced in #236 — because inserting an entry means anchoring on
    `## [Unreleased]` and it is easy not to look for the section already below it. The hand-fix did
    not stop the second one; this does.
    """
    path = Path("CHANGELOG.md")
    if not path.is_file():
        return
    release = None
    seen: dict[str, int] = {}
    for lineno, line in enumerate(path.read_text().splitlines(), 1):
        if m := re.match(r"^##\s+\[([^\]]+)\]", line):
            release, seen = m.group(1), {}
            continue
        if not (m := re.match(r"^###\s+(.+?)\s*$", line)) or release is None:
            continue
        name = m.group(1)
        if name not in CHANGELOG_SECTIONS:
            f.add(
                "changelog-sections",
                f"CHANGELOG.md:{lineno}: [{release}] has a '### {name}' section, which is not one "
                f"of Keep a Changelog's: {', '.join(CHANGELOG_SECTIONS)}",
            )
        elif name in seen:
            f.add(
                "changelog-sections",
                f"CHANGELOG.md:{lineno}: [{release}] has a second '### {name}' section - the first "
                f"is at line {seen[name]}. Entries under the second read as a separate group.",
            )
        else:
            seen[name] = lineno


# The registry in docs/STYLEGUIDE.md §10.1, which lists every name a script in tools/ can report.
# Delimited by its own heading so the parse cannot drift onto the rule-to-enforcer table above it,
# which is a different thing and deliberately incomplete.
CHECK_REGISTRY = ("docs/STYLEGUIDE.md", "### 10.1 Every check name")


def registered_check_names() -> set[str] | None:
    """Every check name §10.1 lists, or None when the section cannot be found."""
    doc = Path(CHECK_REGISTRY[0])
    if not doc.is_file():
        return None
    text = doc.read_text()
    start = text.find(CHECK_REGISTRY[1])
    if start < 0:
        return None
    end = text.find("\n### ", start + len(CHECK_REGISTRY[1]))
    section = text[start : end if end > 0 else len(text)]
    return {
        m.group(1)
        for line in section.splitlines()
        if line.startswith("| `")
        for m in [re.match(r"\|\s*`([a-z]+(?:-[a-z]+)*)`", line)]
        if m
    }


CHECK_SOURCES = (
    "validate_mod.py",
    "check_build_log.py",
    "check_docs.py",
    "report_dynamic_tables.py",
)


def check_check_names(f: Findings) -> None:
    """Check names and the documents must agree, in both directions.

    A document naming a check that does not exist teaches a contributor a false name — that is the
    mistake #100 made, writing `reachability` where the validator emits `unreachable`.

    The reverse went unchecked until #402, and it is the quieter half: a check the tools emit that no
    document lists is **silent**. The registry simply reads as complete when it is not, and whoever
    trusts it never learns the check is there. Fifteen names had accumulated that way, including
    `dead-chip-grade`, which shipped unlisted in #347 and was caught by hand.
    """
    # Every script that emits named checks, not just the validator: the moment one of them is
    # left out, documenting its checks correctly reports as an error. That is a worse failure
    # than the one this guards against, because it punishes the person doing the right thing.
    # This script included: it emits named checks too, and leaving itself out is the very trap
    # the paragraph above describes. #242 walked into it - documenting `vanilla-figure`, a name
    # this file has emitted since it was written, failed here.
    sources = CHECK_SOURCES
    emitted: set[str] = set()
    for name in sources:
        text = (Path("tools") / name).read_text()
        emitted |= set(re.findall(r'f\.add\(\s*"([a-z-]+)"', text))
        # Not every tool collects findings in a Findings object. report_dynamic_tables.py prints
        # its own, so it declares the name as a constant rather than only interpolating it - a
        # bare bracketed literal would match hook ids and YAML keys just as happily.
        emitted |= set(re.findall(r'^CHECK_NAME = "([a-z-]+)"', text, re.MULTILINE))
    if not emitted:
        f.add(
            "check-names",
            f"could not read any check names out of {' or '.join(sources)}",
        )
        return
    # Only consider names that look like a check and are claimed as one.
    for doc in DOCS:
        if not doc.is_file():
            continue
        text = doc.read_text()
        # Target the actual failure mode: calling something "the `x` check" when no such check
        # exists. That is the mistake I made in #100, writing `reachability` where the validator
        # emits `unreachable`. Looser heuristics catch pre-commit hook ids, Dependabot ecosystems
        # and YAML keys, all legitimately hyphenated and none of them checks.
        for m in re.finditer(r"`([a-z]+(?:-[a-z]+)*)`\s+check\b", text):
            name = m.group(1)
            # Skip placeholders. Prose that describes this check necessarily writes something like
            # "the `x` check" as an example, and the shortest real check name is four characters
            # (`json`), so anything shorter is standing in for a name rather than being one.
            if len(name) < 4:
                continue
            if name not in emitted:
                f.add(
                    "check-names",
                    f"{doc}: calls `{name}` a check, but no script in tools/ emits that name",
                )

    # The other direction: every emitted name must be in the registry.
    registered = registered_check_names()
    if registered is None:
        f.add(
            "check-names",
            f"{CHECK_REGISTRY[0]} has no '{CHECK_REGISTRY[1]}' section to check names against",
        )
        return
    for name in sorted(emitted - registered):
        f.add(
            "check-names",
            f"tools/ emits the check {name!r}, but {CHECK_REGISTRY[0]} §10.1 does not list it - "
            f"a check no document names is one nobody can look up",
        )
    for name in sorted(registered - emitted):
        f.add(
            "check-names",
            f"{CHECK_REGISTRY[0]} §10.1 lists {name!r}, but no script in tools/ emits it",
        )


def check_preserved(f: Findings) -> None:
    for current, original in PRESERVED.items():
        p = Path(current)
        if not p.is_file():
            f.add("preserved", f"{current} is missing")
            continue
        got = subprocess.run(
            ["git", "show", f"upstream-2.2:{original}"],
            capture_output=True,
            check=False,
        )
        if got.returncode != 0:
            f.add("preserved", f"could not read upstream-2.2:{original}")
            continue
        if got.stdout != p.read_bytes():
            f.add(
                "preserved",
                f"{current} differs from upstream-2.2:{original} — it must stay byte-identical",
            )


WIKI_URL = "https://github.com/vixygrey/qud-expanded-community-edition.wiki.git"

# Every wiki link into this repository, as GitHub writes them: blob/<ref>/<path>#<anchor>.
WIKI_LINK = re.compile(r"blob/[^/]+/([^)#\s]+)(?:#([A-Za-z0-9\-_]+))?")


def github_anchor(heading: str) -> str:
    """Derive a heading's anchor the way GitHub does.

    Lowercase, markdown stripped, anything but letters, digits, spaces, hyphens and underscores
    dropped, spaces to hyphens. An em dash therefore leaves the two spaces around it as a double
    hyphen, which is why `## Appendix B - every psionic chip` anchors as
    `appendix-b--every-psionic-chip` rather than the single hyphen it looks like.

    This is a reimplementation of someone else's rule and can drift from it. It agrees with all 23
    anchors the wiki uses today, and the awkward shapes are pinned in tools/test_check_docs.py.
    """
    text = re.sub(r"^#+\s*", "", heading.strip())
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\*\*?([^*]*)\*\*?", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.lower()
    text = "".join(c for c in text if c.isalnum() or c in " -_")
    return text.strip().replace(" ", "-")


def anchors_of(path: Path) -> set[str]:
    """Every anchor a markdown file offers, duplicates suffixed the way GitHub suffixes them."""
    found: set[str] = set()
    seen: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#"):
            continue
        base = github_anchor(line)
        n = seen.get(base, 0)
        seen[base] = n + 1
        found.add(base if n == 0 else f"{base}-{n}")
    return found


def check_wiki_links(wiki: Path, f: Findings) -> int:
    """Every anchor the wiki links to must still exist in the file it names."""
    cache: dict[Path, set[str] | None] = {}
    checked = 0
    for page in sorted(wiki.glob("*.md")):
        for target, anchor in WIKI_LINK.findall(page.read_text(encoding="utf-8")):
            path = Path(target)
            if path not in cache:
                cache[path] = anchors_of(path) if path.is_file() else None
            if cache[path] is None:
                f.add(
                    "wiki-link", f"{page.name}: links to {target}, which does not exist"
                )
                continue
            if not anchor:
                continue  # a link to the file with no fragment cannot rot this way
            checked += 1
            if anchor not in cache[path]:
                f.add(
                    "wiki-link",
                    f"{page.name}: {target}#{anchor} - no heading in {target} anchors there",
                )
    return checked


def check_wiki(explicit: str | None) -> int:
    """Clone the wiki and verify its links into this repository still resolve.

    Kept out of the normal run for the same reason as --ruleset: it needs a second repository and a
    network, and a check that passes quietly when it could not reach anything is worse than none.

    It catches the failure that is silent and mechanical. GitHub derives an anchor from the heading
    text, so renaming a heading breaks every wiki link to it - a bad fragment still returns HTTP 200
    and neither repository reports a thing. Renaming one heading in FEATURES.md broke five links
    across two pages when this was written. It cannot tell whether a page is still *true*; that is
    #230's other half and no check will ever answer it.
    """
    if explicit:
        wiki = Path(explicit)
        if not wiki.is_dir():
            print(f"error: {wiki} is not a directory", file=sys.stderr)
            return 2
    else:
        tmp = tempfile.mkdtemp(prefix="qud-wiki-")
        wiki = Path(tmp) / "wiki"
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", "--quiet", WIKI_URL, str(wiki)],
                check=True,
                capture_output=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            print(f"could not clone the wiki: {exc}", file=sys.stderr)
            return 2

    pages = sorted(wiki.glob("*.md"))
    if not pages:
        print(f"error: no markdown pages found in {wiki}", file=sys.stderr)
        return 2

    f = Findings()
    links = check_wiki_links(wiki, f)
    figures = check_wiki_counts(wiki, f, facts())
    check_claim_coverage(f, wiki)
    if f.items:
        print(f"FAIL - {len(f.items)} problem(s) in the wiki:", file=sys.stderr)
        for check, detail in sorted(f.items):
            print(f"  [{check}] {detail}", file=sys.stderr)
        print(
            "\nThe wiki is a separate repository and does not know this one changed. Either "
            "correct the page or, for a link, put the heading back - it clones from\n  "
            + WIKI_URL,
            file=sys.stderr,
        )
        return 1
    print(
        f"OK - {links} wiki anchor link(s) and {figures} figure(s) across "
        f"{len(pages)} page(s) still hold"
    )
    return 0


def compare_ruleset() -> int:
    """Compare the committed list against GitHub's live ruleset. Needs gh and network.

    This is the one thing the committed file cannot check about itself: whether it still describes
    what GitHub actually enforces. Kept out of the normal run deliberately - a check that needs a
    token and a network would either fail for contributors who have neither, or be made to pass
    quietly when it cannot reach anything, and a check that passes when it did not run is worse
    than no check.
    """
    data = required_checks()
    want = sorted(e["context"] for e in data["required"])
    try:
        out = subprocess.run(
            ["gh", "api", "repos/{owner}/{repo}/rulesets", "--jq", ".[].id"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"could not reach the GitHub API: {exc}", file=sys.stderr)
        return 2
    live: list[str] = []
    for rid in out.stdout.split():
        detail = subprocess.run(
            [
                "gh",
                "api",
                f"repos/{{owner}}/{{repo}}/rulesets/{rid}",
                "--jq",
                (
                    '[.rules[] | select(.type=="required_status_checks") '
                    "| .parameters.required_status_checks[].context] | .[]"
                ),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        live += detail.stdout.split("\n")
    have = sorted(c for c in live if c)
    if have == want:
        print(f"Ruleset matches {REQUIRED_CHECKS_PATH}: {len(want)} required check(s).")
        return 0
    print(
        f"MISMATCH between {REQUIRED_CHECKS_PATH} and the live ruleset:",
        file=sys.stderr,
    )
    for c in sorted(set(want) - set(have)):
        print(f"  committed but NOT enforced: {c}", file=sys.stderr)
    for c in sorted(set(have) - set(want)):
        print(f"  enforced but NOT committed: {c}", file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--wiki",
        action="store_true",
        help="clone the wiki and verify its links into this repository still resolve",
    )
    ap.add_argument(
        "--wiki-path",
        help="check an existing wiki clone instead of cloning one (implies --wiki)",
    )
    ap.add_argument(
        "--conflict-markers",
        action="store_true",
        help="scan tracked files for leftover conflict markers and nothing else (fast; for the "
        "pre-commit hook, which must run on every file rather than this script's usual subset)",
    )
    ap.add_argument(
        "--ruleset",
        action="store_true",
        help="compare tools/required-checks.json against GitHub's live ruleset (needs gh)",
    )
    args = ap.parse_args()
    if args.wiki or args.wiki_path:
        return check_wiki(args.wiki_path)
    if args.ruleset:
        return compare_ruleset()
    if args.conflict_markers:
        f = Findings()
        scanned = check_conflict_markers(f)
        for check, detail in sorted(f.items):
            print(f"  [{check}] {detail}", file=sys.stderr)
        if f.items:
            return 1
        print(f"OK - {scanned} tracked file(s) carry no leftover conflict markers")
        return 0

    if not MOD.is_dir():
        print("error: run from the repository root (mod/ not found)", file=sys.stderr)
        return 2

    f = Findings()
    known = facts()
    checked = check_counts(f, known)
    workshop = check_workshop_counts(f, known)
    check_workshop_version(f)
    from_game = check_vanilla_figures(f)
    check_claim_coverage(f)
    appendix = check_appendix_b(f)
    items = check_item_tables(f)
    file_rows = check_file_rows(f, known)
    check_links(f)
    prose_links = check_prose_doc_links(f)
    check_sections(f)
    check_heading_order(f)
    check_changelog_sections(f)
    check_check_names(f)
    check_required_checks(f)
    pins = check_pin_parity(f)
    check_preserved(f)
    markers = check_conflict_markers(f)

    if f.items:
        print(f"FAIL - {len(f.items)} problem(s):", file=sys.stderr)
        for check, detail in sorted(f.items):
            print(f"  [{check}] {detail}", file=sys.stderr)
        print(
            "\nIf a figure changed legitimately, update the document. If a claim is written in a "
            "phrasing this script cannot find, add it to CLAIMS - or to VANILLA_CLAIMS when the "
            "figure is quoted from the game.",
            file=sys.stderr,
        )
        return 1

    print(
        f"OK - {checked} documented figure(s) match the mod, {from_game} match the game, "
        f"{workshop} Workshop description figure(s) match the mod, "
        f"{appendix} chip row(s), {items} item-table figure(s) and {file_rows} per-file "
        f"row figure(s) match their blueprints; "
        f"links, sections, check names and preserved documents all clean; "
        f"{pins} pinned tool(s) in step; "
        f"{prose_links} prose path(s) resolve; "
        f"{markers} tracked file(s) carry no conflict markers"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
