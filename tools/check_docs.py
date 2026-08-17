#!/usr/bin/env python3
"""Check the documentation against the mod. Python 3 standard library only.

    python3 tools/check_docs.py

`tools/validate_mod.py` checks the mod. This checks the documents that describe it, because
nothing else did — three separate sweeps (#93, #96, #130) found documentation asserting things
that had stopped being true, every time by someone reading rather than by anything checking.

It cannot read a sentence and ask whether it is still true; nothing can. What it can do is check
the parts of a document that are *not* prose:

  counts        a figure quoted in the docs, against the same figure recomputed from mod/
  links         every relative link resolves to a file that exists
  sections      every "FILE.md §N" cross-reference names a section that exists there
  checks        every validator check name quoted in the docs is one the validator emits
  preserved     Mura's two documents are still byte-identical to the upstream import

The counts check is the one that matters most and the one with a real limitation: it can only
verify a figure it knows how to find. CLAIMS below pairs a regular expression with the facts its
capture groups hold. A figure written in a phrasing no pattern matches is simply not checked, so
adding a new claim to the docs means adding its phrasing here. That is the cost of checking prose
at all, and it is cheaper than the alternative, which is three sweeps and counting.
"""

from __future__ import annotations

import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MOD = Path("mod")
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
    }
    for name, (n, m) in per_file.items():
        out[f"file:{name}:new"] = n
        out[f"file:{name}:merged"] = m
    return out


# Each pattern's capture groups map, in order, to the facts they must equal.
CLAIMS: list[tuple[str, list[str]]] = [
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
                    claimed = int(m.group(group))
                    if name not in known:
                        f.add("counts", f"{doc}: pattern names unknown fact {name!r}")
                    elif claimed != known[name]:
                        f.add(
                            "counts",
                            f"{doc} says {name} is {claimed}; recounted from mod/ it is "
                            f"{known[name]} — {m.group(0)[:60]!r}",
                        )
    return checked


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
    """A doc naming a validator check that does not exist teaches a contributor a false name."""
    emitted = set(
        re.findall(
            r'f\.add\(\s*"([a-z-]+)"', (Path("tools") / "validate_mod.py").read_text()
        )
    )
    if not emitted:
        f.add(
            "check-names", "could not read any check names out of tools/validate_mod.py"
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
                    f"{doc}: calls `{name}` a check, but tools/validate_mod.py emits no such name",
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


def main() -> int:
    if not MOD.is_dir():
        print("error: run from the repository root (mod/ not found)", file=sys.stderr)
        return 2

    f = Findings()
    known = facts()
    checked = check_counts(f, known)
    check_links(f)
    check_sections(f)
    check_check_names(f)
    check_preserved(f)

    if f.items:
        print(f"FAIL - {len(f.items)} problem(s):", file=sys.stderr)
        for check, detail in sorted(f.items):
            print(f"  [{check}] {detail}", file=sys.stderr)
        print(
            "\nIf a figure changed legitimately, update the document. If a claim is written in a "
            "phrasing this script cannot find, add it to CLAIMS.",
            file=sys.stderr,
        )
        return 1

    print(
        f"OK - {checked} documented figure(s) match the mod; links, sections, check names and "
        f"preserved documents all clean"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
