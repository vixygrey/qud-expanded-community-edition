#!/usr/bin/env python3
"""Check the documentation against the mod. Python 3 standard library only.

    python3 tools/check_docs.py

`tools/validate_mod.py` checks the mod. This checks the documents that describe it, because
nothing else did — three separate sweeps (#93, #96, #130) found documentation asserting things
that had stopped being true, every time by someone reading rather than by anything checking.

It cannot read a sentence and ask whether it is still true; nothing can. What it can do is check
the parts of a document that are *not* prose:

  counts          a figure quoted in the docs, against the same figure recomputed from mod/
  links           every relative link resolves to a file that exists
  sections        every "FILE.md §N" cross-reference names a section that exists there
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
import xml.etree.ElementTree as ET
from pathlib import Path

MOD = Path("mod")
REQUIRED_CHECKS_PATH = Path("tools/required-checks.json")
CI_WORKFLOWS = (Path(".github/workflows/ci.yml"), Path(".github/workflows/assign.yml"))

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
}
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
        ".github/PULL_REQUEST_TEMPLATE.md",
    )
]

# Mura's documents, preserved byte-for-byte. They were renamed in #23, so comparing against the
# upstream import needs the ORIGINAL paths — using the current ones reports both as modified when
# they are untouched, which is how the first version of this check cried wolf.
PRESERVED = {
    "docs/2.2-changelog.txt": "2.2 changelog.txt",
    "docs/mura-feature-notes-wip.txt": "What Does the Mod Do (WIP).txt",
}

# Documents whose figures describe a *past* state on purpose. The changelog records what was true
# when each entry was written, so recomputing its numbers would be wrong.
COUNT_EXEMPT = {Path("CHANGELOG.md"), Path("docs/DESIGN_options.md")}


def parse(path: Path):
    return ET.fromstring(path.read_text(encoding="utf-8-sig"))


# --------------------------------------------------------------------------- facts


def facts() -> dict[str, int]:
    """Recompute every figure the documents are allowed to quote."""
    new = merged = 0
    per_file: dict[str, tuple[int, int]] = {}
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
        if f.parent.name == "ObjectBlueprints":
            per_file[f.name] = (fn, fm)
        new += fn
        merged += fm

    pops = list(parse(MOD / "PopulationTables.xml").iter("population"))
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
        "options": len(list(parse(MOD / "Options.xml").iter("option"))),
        "subtypes": len(list(parse(MOD / "Subtypes.xml").iter("subtype"))),
        "subtype-sprites": len(list((MOD / "Textures" / "Subtypes").glob("*.png"))),
        "chips": len(chips) - sum(1 for c in chips if "Base" in (c.get("Name") or "")),
        "chip-objects": len(chips),
        "scripting-files": len(list((MOD / "Scripting").glob("*.cs"))),
        "mutation-stubs": len(list((MOD / "Scripting").glob("Raven_Mod*.cs"))),
        "required-checks": len(required_checks()["required"]),
    }
    for name, (n, m) in per_file.items():
        out[f"file:{name}:new"] = n
        out[f"file:{name}:merged"] = m
    return out


QUD_API_PATH = Path("tools/qud-api.json")

# Figures the documents quote *from vanilla*, paired with the phrasing each is written in. The
# values come from tools/qud-api.json's `figures` map, which snapshot_qud_api.py reads out of the
# installed game - so this checks a citation against its source rather than against another
# document.
#
# Same limitation as CLAIMS, and the same bargain: a figure written in a phrasing no pattern
# matches is not checked. Numbers are compared with thousands separators stripped, because the
# prose writes 1,200 where the XML says 1200 and the comma is the document's to keep.
VANILLA_CLAIMS: list[tuple[str, list[str]]] = [
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


# Each pattern's capture groups map, in order, to the facts they must equal.
CLAIMS: list[tuple[str, list[str]]] = [
    # Required checks. Written as words in every document that carries them, so the patterns
    # capture \w+ and WORD_NUMBERS resolves it. This claim was wrong for an unknown length of
    # time - six copies said ten while nine were enforced - which is why it is checked now.
    (
        r"(\w+) checks run on every pull request and all (\w+) must pass",
        ["required-checks", "required-checks"],
    ),
    (
        r"(\w+) checks run here and all (\w+) must pass",
        ["required-checks", "required-checks"],
    ),
    (r"\*\*(\w+) checks are required on every pull request\*\*", ["required-checks"]),
    (r"not one of the (\w+) checks", ["required-checks"]),
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
    (r"Eleven options" if False else r"\*\*(\d+)\*\* options, all under", ["options"]),
    (r"Options\.xml\s+# (\d+) options", ["options"]),
    (r"Scripting/\s+# (\d+) classes", ["scripting-files"]),
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


def check_vanilla_figures(f: Findings) -> int:
    """Hold every quoted vanilla figure to what the game actually says."""
    figures = vanilla_figures()
    if not figures:
        return 0
    checked = 0
    for doc in DOCS:
        if not doc.is_file():
            continue
        text = doc.read_text()
        for pattern, names in VANILLA_CLAIMS:
            for m in re.finditer(pattern, text):
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


def check_counts(f: Findings, known: dict[str, int]) -> int:
    checked = 0
    for doc in DOCS:
        if not doc.is_file() or doc in COUNT_EXEMPT:
            continue
        text = doc.read_text()
        for pattern, names in CLAIMS:
            for m in re.finditer(pattern, text):
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


def check_links(f: Findings) -> None:
    for doc in DOCS:
        if not doc.is_file():
            continue
        for target in re.findall(
            r"\[[^\]]*\]\(([^)#]+?)(?:#[^)]*)?\)", doc.read_text()
        ):
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


def check_check_names(f: Findings) -> None:
    """A doc naming a check that does not exist teaches a contributor a false name."""
    # Every script that emits named checks, not just the validator: the moment one of them is
    # left out, documenting its checks correctly reports as an error. That is a worse failure
    # than the one this guards against, because it punishes the person doing the right thing.
    sources = ("validate_mod.py", "check_build_log.py")
    emitted: set[str] = set()
    for name in sources:
        emitted |= set(
            re.findall(r'f\.add\(\s*"([a-z-]+)"', (Path("tools") / name).read_text())
        )
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
        "--ruleset",
        action="store_true",
        help="compare tools/required-checks.json against GitHub's live ruleset (needs gh)",
    )
    args = ap.parse_args()
    if args.ruleset:
        return compare_ruleset()

    if not MOD.is_dir():
        print("error: run from the repository root (mod/ not found)", file=sys.stderr)
        return 2

    f = Findings()
    known = facts()
    checked = check_counts(f, known)
    from_game = check_vanilla_figures(f)
    check_links(f)
    check_sections(f)
    check_check_names(f)
    check_required_checks(f)
    check_preserved(f)

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
        f"OK - {checked} documented figure(s) match the mod, {from_game} match the game; "
        f"links, sections, check names and preserved documents all clean"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
