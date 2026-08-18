#!/usr/bin/env python3
"""Snapshot the names Qud exposes, so CI can check against them without the game.

`tools/validate_mod.py` needs to know two things that only exist inside a Caves of Qud install:

1. **Which `<part Name="…">` values are real classes.** Qud silently ignores a part it cannot
   resolve. A typo leaves the object valid, loadable, and missing the behaviour you wrote.
2. **Which blueprint names exist.** A part attribute naming a blueprint that isn't there fails the
   same way — #144 found `GasObject="GasPoison"` where the blueprint is `PoisonGas` (`GasPoison`
   is a *part* on it), which would have fired an arrow that released no gas at all.
3. **Which members a part attribute can land on.** `<part Name="TemperatureOnHit" Radius="2" />`
   is discarded whole: the part loads, the object is valid, and the setting does nothing. That
   list only exists in `Assembly-CSharp.dll`, so `tools/dump_part_members.cs` reads it out of the
   metadata — no decompiler, no packages, nothing executed.

GitHub runners have no copy of the game, so neither check can run in CI directly. This tool writes
the answers to `tools/qud-api.json`, which **is committed**. The validator reads that file and runs
everywhere, with no install of anything.

Everything comes from the plain-text XML the game ships, and the snapshot holds identifiers only —
no descriptions, stats, text or art. They are the same identifiers the mod's own XML already names
in every `Load="Merge"`.

**Run this after every Qud update**, alongside `tools/check_vanilla_drift.py`. A stale snapshot is
visible — it records the Steam build it came from — and its failure mode is a false positive on a
newly added vanilla name, which is loud. That is the right way round: silence is what this whole
tool exists to prevent.

Usage:
    python3 tools/snapshot_qud_api.py [--game PATH] [--check]
    python3 tools/snapshot_qud_api.py --assembly          # widen the part list; needs ilspycmd

`--check` verifies the committed snapshot still matches the installed game and writes nothing.

`--assembly` reads part *names* from `Assembly-CSharp.dll` instead of from vanilla's usage. Only
needed if the mod adopts a real part that vanilla declares and never uses — the default list covers
every part in use today. That path wants `ilspycmd` (`dotnet tool install -g ilspycmd`).

Part *members* always come from the assembly, which is located automatically, and need the .NET
SDK — the same one `tools/compile_scripting.py` uses. There is deliberately no flag to skip them:
a snapshot silently missing its `members` map would disable `part-attribute` in CI and look green.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_vanilla_drift import find_game, load_all

SNAPSHOT_PATH = Path("tools/qud-api.json")

# Parts resolve from this namespace exactly. Not its children: XRL.World.Parts.Skill.Shield and
# XRL.World.Parts.Shield are different types with the same leaf name, and so are
# XRL.Collections.Container and XRL.World.Parts.Container. Widening the scope would let a typo
# land on an unrelated class and pass.
PART_NAMESPACE = "XRL.World.Parts"

# The member dumper, and the throwaway project that builds it. System.Reflection.Metadata is
# in-box in the .NET SDK, so this needs no package, no network and no ilspycmd - and the SDK is
# already required by tools/compile_scripting.py, which the pre-commit hook runs.
MEMBER_DUMPER = Path(__file__).resolve().parent / "dump_part_members.cs"
MEMBER_PROJECT = """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>{tfm}</TargetFramework>
    <Nullable>disable</Nullable>
    <EnableDefaultCompileItems>false</EnableDefaultCompileItems>
    <AssemblyName>dump_part_members</AssemblyName>
  </PropertyGroup>
  <ItemGroup><Compile Include="{source}" /></ItemGroup>
</Project>
"""


def member_tfm() -> str:
    """Target whatever SDK is installed rather than pinning a version.

    A pinned `net8.0` fails on a machine that only has 10 - the SDK compiles it and then finds no
    matching runtime. The dumper uses nothing version-specific, so the installed major is always
    the right answer.
    """
    proc = subprocess.run(
        ["dotnet", "--version"], capture_output=True, text=True, check=False
    )
    major = proc.stdout.strip().split(".")[0] if proc.returncode == 0 else ""
    return f"net{major}.0" if major.isdigit() else "net8.0"


# Attributes that belong to the `<part>` element rather than to the part class, so they are valid
# on every part and resolve against no member at all. Not a guess: `Name`, `Namespace`,
# `ChanceOneIn` and `Reflector` are the public fields of `XRL.World.GamePartBlueprint`, which is
# the loader's own representation of the element. `Builder` is here on separate evidence - every
# value vanilla gives it (`InventoryChestJunk`, `InventoryChestJunk1R`, …) resolves to a type in
# `XRL.World.PartBuilders`, so it names a builder class rather than setting a member.
#
# Keep this list evidence-backed. Each entry is a hole in the check, and verify() is what proves
# the holes are the right shape - it re-establishes on every regeneration that vanilla passes.
ELEMENT_ATTRS = ("Name", "Namespace", "ChanceOneIn", "Reflector", "Builder")

DEFAULT_ASSEMBLIES = [
    "~/Library/Application Support/Steam/steamapps/common/Caves of Qud/CoQ.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll",
    "~/.steam/steam/steamapps/common/Caves of Qud/CoQ_Data/Managed/Assembly-CSharp.dll",
    "C:/Program Files (x86)/Steam/steamapps/common/Caves of Qud/CoQ_Data/Managed/Assembly-CSharp.dll",
]

STEAM_MANIFESTS = [
    "~/Library/Application Support/Steam/steamapps/appmanifest_333640.acf",
    "~/.steam/steam/steamapps/appmanifest_333640.acf",
    "C:/Program Files (x86)/Steam/steamapps/appmanifest_333640.acf",
]

# Attributes whose value is a blueprint name. Every one of these resolves for 100% of its distinct
# values across vanilla's own data, which is the evidence for including it — see verify() below,
# which re-establishes that on every regeneration rather than trusting this comment.
#
# `Blueprint` is deliberately absent. It is overloaded: in population tables it also holds skill
# names (`SingleWeaponFighting_ExpertStrikes`), templated table references
# (`@DynamicObjectsTable:EnergyCells:Tier{ownertier}`), and vanilla's own dead example entries
# (`Thing`, `BigThing`). Population-table targets are `check_table_targets`' job instead.
BLUEPRINT_ATTRS = (
    "ProjectileObject",
    "GasObject",
    "GasBlueprint",
    "CorpseBlueprint",
    "SubstituteBlueprint",
    "SpawnBlueprint",
    "SpawnCheckBlueprint",
    "FistObject",
    "Result",
    "GiveItem",
    "TakeItem",
)

# Elements whose attributes are checked. Every context here is 100% resolvable in vanilla.
# `<object Blueprint=…>` inside a population table is not, for the reasons above.
BLUEPRINT_CONTEXTS = ("part", "inventoryobject", "widget", "removeinventoryobject")


def object_parts(root):
    """Yield only `<part>` elements belonging to an object blueprint.

    Conversations use `<part Name="…">` too — AskName, EndGame, GiveArtifact, the KithAndKin
    handlers — and those resolve from a different namespace entirely. Checking every `<part>` in
    every file reports 55 of vanilla's own conversation parts as broken. Scope is the fix, not a
    longer allowlist.
    """
    for obj in root.iter("object"):
        yield from obj.iter("part")


def find_assembly(explicit: str | None) -> Path | None:
    for candidate in ([explicit] if explicit else []) + DEFAULT_ASSEMBLIES:
        if not candidate:
            continue
        p = Path(os.path.expanduser(candidate))
        if p.is_file():
            return p
    return None


def steam_build_id() -> str:
    """Best-effort. The snapshot is still valid without it; the digest is the real identity."""
    for candidate in STEAM_MANIFESTS:
        p = Path(os.path.expanduser(candidate))
        if p.is_file():
            m = re.search(r'"buildid"\s*"(\d+)"', p.read_text(errors="replace"))
            if m:
                return m.group(1)
    return "unknown"


def collect_parts(assembly: Path) -> list[str]:
    if not shutil.which("ilspycmd"):
        raise SystemExit(
            "error: ilspycmd not found on PATH.\n"
            "  dotnet tool install -g ilspycmd\n"
            '  export PATH="$PATH:$HOME/.dotnet/tools"'
        )
    proc = subprocess.run(
        ["ilspycmd", "-l", "c", str(assembly)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(f"error: ilspycmd failed:\n{proc.stderr.strip()}")
    prefix = PART_NAMESPACE + "."
    names = set()
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("Class "):
            continue
        fq = line[len("Class ") :].split("`")[0]
        if fq.startswith(prefix) and "." not in fq[len(prefix) :]:
            names.add(fq[len(prefix) :])
    if not names:
        raise SystemExit(
            f"error: no classes found in {PART_NAMESPACE}. Did the assembly layout change?"
        )
    return sorted(names)


def collect_members(assembly: Path) -> dict[str, list[str]]:
    """Every settable member of every part class, inherited members flattened in.

    Shells out to `tools/dump_part_members.cs` through a throwaway project, because the answer
    lives in the assembly's metadata and nothing in the shipped XML carries it. See that file for
    what counts as settable and why properties, inheritance and generic bases each need handling.
    """
    if not shutil.which("dotnet"):
        raise SystemExit(
            "error: the .NET SDK is needed to read part members from the assembly.\n"
            "  brew install dotnet          (or https://dotnet.microsoft.com/download)\n"
            "It is the same SDK tools/compile_scripting.py already uses."
        )
    if not MEMBER_DUMPER.is_file():
        raise SystemExit(f"error: {MEMBER_DUMPER} is missing")

    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "dump_part_members.csproj"
        project.write_text(
            MEMBER_PROJECT.format(tfm=member_tfm(), source=MEMBER_DUMPER)
        )
        proc = subprocess.run(
            ["dotnet", "run", "--project", str(project), "--", str(assembly)],
            capture_output=True,
            text=True,
            check=False,
            env={
                **os.environ,
                "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
                "DOTNET_NOLOGO": "1",
            },
        )
    if proc.returncode != 0:
        raise SystemExit(f"error: reading part members failed:\n{proc.stderr.strip()}")
    payload = proc.stdout[proc.stdout.index("{") :] if "{" in proc.stdout else ""
    try:
        members = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"error: the member dumper did not return JSON: {exc}"
        ) from exc
    if not members:
        raise SystemExit(f"error: no members found in {PART_NAMESPACE}")
    return {name: sorted(vals) for name, vals in sorted(members.items())}


def collect_blueprints(game: Path) -> list[str]:
    names = set()
    for root in load_all(game, lenient=True):
        for obj in root.iter("object"):
            name = obj.get("Name")
            if name:
                names.add(name)
    if not names:
        raise SystemExit(f"error: no object blueprints found under {game}")
    return sorted(names)


def verify(
    game: Path, parts: set[str], blueprints: set[str], members: dict[str, list[str]]
) -> list[str]:
    """Hold vanilla to the rules we are about to hold the mod to.

    If vanilla fails them, the rule is wrong and the snapshot must not ship — a rule that flags
    Freehold's own data would flag ours for the same non-reasons, and the noise would train us to
    ignore it. This is what caught the first part-name rule reporting 55 of vanilla's own
    conversation parts as broken.

    Note the part half is only a real test under `--assembly`. With the default XML-derived list
    the set *is* vanilla's usage, so vanilla cannot fail it — true by construction rather than by
    verification. The rule stays sound (a part vanilla uses is a part that exists) and the check
    against the mod stays meaningful; it is the self-test that goes trivial, and it is worth
    knowing that rather than reading a green line as more assurance than it carries. The blueprint
    and member halves are genuine tests either way.

    The member half earned its keep immediately. It found four attribute names vanilla sets that
    are not members of the part class, and each one taught the rule something rather than being
    waved through: `ChanceOneIn` and `Builder` belong to the element (see ELEMENT_ATTRS), and
    `Tier` on the ModImproved* parts is inherited through a *generic* base, which the dumper now
    decodes. Vanilla is clean on all 50,075 of its part attributes.
    """
    problems = []
    element_attrs = set(ELEMENT_ATTRS)
    for root in load_all(game, lenient=True):
        for part in object_parts(root):
            name = part.get("Name")
            if name and name not in parts:
                problems.append(
                    f'vanilla uses <part Name="{name}"> which is not a class'
                )
            if name in members:
                allowed = set(members[name]) | element_attrs
                for attr in part.attrib:
                    if attr not in allowed:
                        problems.append(
                            f'vanilla sets <part Name="{name}" {attr}="…">, '
                            f"which is not a settable member of {name}"
                        )
        for el in root.iter():
            if el.tag in BLUEPRINT_CONTEXTS:
                for attr in BLUEPRINT_ATTRS:
                    value = el.get(attr)
                    if value and value not in blueprints:
                        problems.append(
                            f"vanilla uses {el.tag}[{attr}]={value!r} which is not a blueprint"
                        )
    return sorted(set(problems))


def collect_parts_from_xml(game: Path) -> list[str]:
    """Every part name vanilla itself uses on an object blueprint.

    This is the default source, and it needs nothing but the plain-text XML the game ships. The
    assembly gives a wider set — 1,605 classes against 949 names in use — but the extra 656 are
    parts vanilla declares and never uses, and the mod touches none of them.

    The trade is a false positive if the mod ever adopts a real part vanilla happens not to use in
    its own data. That is loud, one line to diagnose, and fixable with `--assembly`. It is the same
    failure direction as a stale snapshot, and the right one for a tool that exists to catch
    silence.
    """
    names = set()
    for root in load_all(game, lenient=True):
        for part in object_parts(root):
            name = part.get("Name")
            if name:
                names.add(name)
    if not names:
        raise SystemExit(f"error: no part names found under {game}")
    return sorted(names)


def build(game: Path, assembly: Path | None, member_assembly: Path) -> dict:
    if assembly is not None:
        parts, part_source = collect_parts(assembly), f"assembly:{PART_NAMESPACE}"
    else:
        parts, part_source = collect_parts_from_xml(game), "vanilla-xml"
    blueprints = collect_blueprints(game)
    members = collect_members(member_assembly)

    problems = verify(game, set(parts), set(blueprints), members)
    if problems:
        print(
            f"REFUSING to write: the rules do not hold for vanilla itself "
            f"({len(problems)} problem(s)).",
            file=sys.stderr,
        )
        for p in problems[:20]:
            print(f"  {p}", file=sys.stderr)
        if len(problems) > 20:
            print(f"  … and {len(problems) - 20} more", file=sys.stderr)
        print(
            "\nNarrow BLUEPRINT_ATTRS, BLUEPRINT_CONTEXTS or ELEMENT_ATTRS until vanilla is "
            "clean, then regenerate.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    member_repr = "\n".join(f"{k}:{','.join(v)}" for k, v in members.items())
    digest = hashlib.sha256(
        ("\n".join(parts) + "\0" + "\n".join(blueprints) + "\0" + member_repr).encode()
    ).hexdigest()[:16]
    return {
        "_comment": (
            "Generated by tools/snapshot_qud_api.py from an installed Caves of Qud. Names only - "
            "no descriptions, stats, text or art. Regenerate after every Qud update; a stale "
            "snapshot shows up as a false positive on a newly added vanilla name, which is loud "
            "rather than silent."
        ),
        "steam_build_id": steam_build_id(),
        "digest": digest,
        "part_source": part_source,
        "blueprint_attributes": list(BLUEPRINT_ATTRS),
        "blueprint_contexts": list(BLUEPRINT_CONTEXTS),
        "element_attributes": list(ELEMENT_ATTRS),
        "counts": {
            "parts": len(parts),
            "blueprints": len(blueprints),
            "member_types": len(members),
            "members": sum(len(v) for v in members.values()),
        },
        "parts": parts,
        "blueprints": blueprints,
        "members": members,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--game", help="path to StreamingAssets/Base")
    ap.add_argument(
        "--assembly",
        nargs="?",
        const="auto",
        help="widen the part list from Assembly-CSharp.dll instead of vanilla's XML usage; "
        "needs ilspycmd. Pass bare to auto-locate, or give a path.",
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="compare the committed snapshot against the install; write nothing",
    )
    args = ap.parse_args()

    game = find_game(args.game)
    if game is None:
        print(
            "Could not find the installed game data. Pass --game PATH pointing at\n"
            "StreamingAssets/Base (on macOS this lives inside CoQ.app/Contents/Resources/Data).",
            file=sys.stderr,
        )
        return 2
    assembly = None
    if args.assembly:
        assembly = find_assembly(None if args.assembly == "auto" else args.assembly)
        if assembly is None:
            print(
                "Could not find Assembly-CSharp.dll. Pass --assembly PATH.",
                file=sys.stderr,
            )
            return 2

    member_assembly = assembly or find_assembly(None)
    if member_assembly is None:
        print(
            "Could not find Assembly-CSharp.dll, which is where part members live.\n"
            "Pass --assembly PATH.",
            file=sys.stderr,
        )
        return 2

    print(f"game:     {game}")
    print(f"parts:    {assembly if assembly else 'vanilla XML usage (no decompiler)'}")
    print(f"members:  {member_assembly}\n")
    fresh = build(game, assembly, member_assembly)

    if args.check:
        if not SNAPSHOT_PATH.exists():
            print(
                f"{SNAPSHOT_PATH} does not exist - run without --check", file=sys.stderr
            )
            return 1
        current = json.loads(SNAPSHOT_PATH.read_text())
        if current.get("digest") == fresh["digest"]:
            print(
                f"Snapshot is current ({fresh['counts']['parts']} parts, "
                f"{fresh['counts']['blueprints']} blueprints, "
                f"{fresh['counts']['members']} members, digest {fresh['digest']})."
            )
            return 0
        print(
            f"STALE - committed digest {current.get('digest')}, installed game gives "
            f"{fresh['digest']}.\nRe-run without --check to update.",
            file=sys.stderr,
        )
        return 1

    SNAPSHOT_PATH.write_text(json.dumps(fresh, indent=2) + "\n")
    print(
        f"wrote {SNAPSHOT_PATH}: {fresh['counts']['parts']} parts, "
        f"{fresh['counts']['blueprints']} blueprints, "
        f"{fresh['counts']['members']} members across "
        f"{fresh['counts']['member_types']} part classes, "
        f"steam build {fresh['steam_build_id']}, digest {fresh['digest']}"
    )
    print(
        "Vanilla satisfies all three rules, so they are safe to enforce against the mod."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
