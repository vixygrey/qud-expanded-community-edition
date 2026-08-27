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

`--check` verifies the committed snapshot still matches the installed game and writes nothing. It
runs as a pre-commit hook (`snapshot-check`), with `always_run` rather than a file pattern: what it
catches is a *Qud update*, which correlates with nothing in a diff. Where the game, the .NET SDK or
ilspycmd is absent it skips loudly and passes, so a contributor without them is not blocked by a
hook they cannot satisfy; `--require` turns that skip into a failure. A genuinely stale snapshot
always fails, on every machine that could tell - the skip is for what this machine cannot reach, not
for what it found.

`--assembly` reads part *names* from `Assembly-CSharp.dll` instead of from vanilla's usage, which
is 1605 names against 949 — vanilla declares far more parts than it uses. **The committed snapshot
is built this way**, so `--assembly` is how you reproduce it, not an optional extra. That path wants
`ilspycmd` (`dotnet tool install -g ilspycmd`).

Mixing the two is refused outright, in both directions, because the digest covers the part list and
the two sources produce different ones. #244 found this the hard way twice over: a plain run over an
assembly-built snapshot drops 656 names in silence, and `--check` across the same mismatch calls a
current file STALE and then advises the very command that performs the drop.

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
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_vanilla_drift import BlueprintIndex, find_game, load_all, parse

SNAPSHOT_PATH = Path("tools/qud-api.json")

# Parts resolve from this namespace exactly. Not its children: XRL.World.Parts.Skill.Shield and
# XRL.World.Parts.Shield are different types with the same leaf name, and so are
# XRL.Collections.Container and XRL.World.Parts.Container. Widening the scope would let a typo
# land on an unrelated class and pass.
PART_NAMESPACE = "XRL.World.Parts"

# Where a `<part Builder="…">` value resolves. Exactly this namespace, not its children - the same
# rule PART_NAMESPACE follows and for the same reason.
BUILDER_NAMESPACE = "XRL.World.PartBuilders"

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

# Figures the documents quote *from vanilla*, and where each one lives. Every entry exists
# because a document depends on it - this is a list of citations, not a dump of the game.
#
# The gap it closes: check_docs.py recomputes 45 figures from `mod/`, and qud-api.json checks
# names against the game, but a number copied out of Freehold's data was checked by nobody and
# goes stale on any update. #144 shipped saying the thermal and freeze grenades do not exist.
# They do, in Items.xml, and the arrow payloads were scaled against the wrong anchors as a result.
#
# (key, blueprint, "part" or "tag", element name, attribute)
CITED_FIGURES = (
    (
        "heat-grenade-delta",
        "HeatGrenade1",
        "part",
        "ThermalGrenade",
        "TemperatureDelta",
    ),
    (
        "cold-grenade-delta",
        "ColdGrenade1",
        "part",
        "ThermalGrenade",
        "TemperatureDelta",
    ),
    ("poison-gas-density", "PoisonGasGrenade1", "part", "GasGrenade", "Density"),
    ("sleep-gas-density", "SleepGasGrenade1", "part", "GasGrenade", "Density"),
    ("flashbang-radius", "FlashbangGrenade1", "part", "FlashbangGrenade", "Radius"),
    ("flashbang-duration", "FlashbangGrenade1", "part", "FlashbangGrenade", "Duration"),
    ("he-grenade-force", "HEGrenade1", "part", "HEGrenade", "Force"),
    ("he-grenade-damage", "HEGrenade1", "part", "HEGrenade", "Damage"),
    ("boomrose-force", "ProjectileExplosiveArrow", "part", "HEGrenade", "Force"),
    ("boomrose-damage", "ProjectileExplosiveArrow", "part", "HEGrenade", "Damage"),
    ("boomrose-value", "Boomrose Arrow", "part", "Commerce", "Value"),
    (
        "boomrose-penetration",
        "ProjectileExplosiveArrow",
        "part",
        "Projectile",
        "StrengthPenetration",
    ),
    (
        "boomrose-base-damage",
        "ProjectileExplosiveArrow",
        "part",
        "Projectile",
        "BaseDamage",
    ),
)

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
            '  export PATH="$PATH:$HOME/.dotnet/tools"\n'
            "The export is needed even if you installed it: the .NET installer's own\n"
            "/etc/paths.d/dotnet-cli-tools holds the literal string `~/.dotnet/tools`,\n"
            "and path_helper never expands `~`, so that entry has never resolved."
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


MUTATION_NAMESPACE = "XRL.World.Parts.Mutation"


def collect_members(
    assembly: Path,
) -> tuple[dict[str, list[str]], list[str], list[str]]:
    """Every settable member of every part class, the part-builder type names, and the mutations
    that cannot level.

    Shells out to `tools/dump_part_members.cs` through a throwaway project, because the answer
    lives in the assembly's metadata and nothing in the shipped XML carries it. See that file for
    what counts as settable and why properties, inheritance and generic bases each need handling.

    The third list is the one #347 needed. A mutation whose `CanLevel()` returns a constant false
    reads its level nowhere, so every grade of a chip granting it is the same item - Kindle and
    Frost Webs shipped three grades each and all six were one item, at 20, 80 and 320 water.
    Neither `Mutations.xml` nor `HiddenMutations.xml` carries an attribute for it; only the method
    body knows, which is why this comes from the assembly rather than from the catalogue.
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
        payload_obj = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"error: the member dumper did not return JSON: {exc}"
        ) from exc
    if not payload_obj.get("members"):
        raise SystemExit(f"error: no members found in {PART_NAMESPACE}")
    if not payload_obj.get("part_builders"):
        raise SystemExit(f"error: no types found in {BUILDER_NAMESPACE}")
    if not payload_obj.get("non_leveling_mutations"):
        raise SystemExit(
            f"error: no CanLevel() overrides found in {MUTATION_NAMESPACE}.\n"
            "Every mutation in the game reports that it can level, which has never been true - "
            "the shape of the method or the namespace has changed."
        )
    members = {
        name: sorted(vals) for name, vals in sorted(payload_obj["members"].items())
    }
    return (
        members,
        sorted(payload_obj["part_builders"]),
        sorted(payload_obj["non_leveling_mutations"]),
    )


def collect_figures(game: Path) -> dict[str, str]:
    """Read every figure in CITED_FIGURES out of vanilla's own data.

    A figure that cannot be located fails generation rather than resolving to nothing. That is the
    whole point: a citation the game no longer supports should be loud at the moment someone
    regenerates, not silently absent from a check that then passes.

    Values are read where they are written, without following `Inherits`. Every citation so far
    sits on the blueprint that declares it, and resolving the chain would let a figure keep
    checking out after the specific object stopped saying it.
    """
    wanted: dict[str, dict[str, tuple[str, str, str]]] = {}
    for key, blueprint, kind, element, attr in CITED_FIGURES:
        wanted.setdefault(blueprint, {})
        wanted[blueprint][key] = (kind, element, attr)

    figures: dict[str, str] = {}
    for root in load_all(game, lenient=True):
        for obj in root.iter("object"):
            spec = wanted.get(obj.get("Name") or "")
            if not spec:
                continue
            for key, (kind, element, attr) in spec.items():
                for el in obj.iter(kind):
                    if el.get("Name") == element and el.get(attr) is not None:
                        figures[key] = el.get(attr)

    missing = [key for key, *_ in CITED_FIGURES if key not in figures]
    if missing:
        raise SystemExit(
            "error: these cited figures could not be found in the installed game:\n  "
            + "\n  ".join(missing)
            + "\n\nEither Qud moved them, or CITED_FIGURES is wrong. Fix the citation and the "
            "document that depends on it - do not drop the entry."
        )
    return figures


# The seven counts collect_census emits. Named here so a claim in check_docs.py can be read
# against the list without opening the function.
# The buckets every population is counted into. `creature-` covers all creature blueprints;
# `humanoid-` the subset carrying the `Humanoid` tag, which is the population the scour slug is
# actually aimed at - "a round for the armed and the armoured, and dead weight against beasts".
# Quoting only the overall share reads as "this round does nothing"; the pair is the honest claim.
BUCKETS = (
    "inventory-none",
    "inventory-natural",
    "inventory-nonmetal",
    "inventory-popref",
    "rust-dead",
    "rustable",
)
CENSUS_POPULATIONS = ("creature", "humanoid")
CENSUS_KEYS = (
    "creature-blueprints",
    "creature-blueprints-bleeding",
    "humanoid-blueprints",
) + tuple(f"{p}-{b}" for p in CENSUS_POPULATIONS for b in BUCKETS)


def collect_census(game: Path) -> dict[str, str]:
    """Count vanilla's creature blueprints by what an effect can actually reach.

    CITED_FIGURES cannot express this: it reads one attribute off one blueprint, and a census is
    an aggregate over all of them. That gap is what #242 cost. "282 of 908 creature blueprints"
    sat in an `Ammo.xml` comment through review and a release, and the denominator turned out to
    be unreproducible under any filter - while the numerator of the neighbouring claim, 813, came
    out exactly. Nothing could have caught it, because nothing could recompute it.

    The definition lives here, beside the code implementing it, so the two cannot drift:

      creature      the `Creature` tag resolved through `Inherits`, minus the blueprints the
                    `BaseObject` tag reaches. Those are the abstract bases - templates rather
                    than things that spawn. Both tags resolve through BlueprintIndex, which
                    honours `*noinherit` - and `BaseObject` is nearly always declared that way,
                    so a base is excluded while everything inheriting from it is not (#265).
      bleeds        `<intproperty Name="Bleeds" Value="1">`, nearest declaration winning.
      inventory     every `<inventoryobject>` on the chain. Entries opening with `@` or `*` are
                    population references and are counted apart: they are not empty, they draw
                    real items at runtime, and nothing static can say which.
      natural gear  `<intproperty Name="Natural" Value="1">` or the `NaturalGear` tag. An effect
                    reaching for a creature's belongings cannot see it - `BodyPart.DoEquip` sends
                    anything `IsNatural()` to `DefaultBehavior` rather than `Equipped`, and
                    `GetEquippedObjects` collects `Equipped` only. A creature whose gear is all
                    natural has an empty pool however armed it looks.
      metal         a `<part Name="Metal">`, which is what `Rusted.Apply` opens on.
      humanoid      the `Humanoid` tag, resolved the same way. Counted as its own population
                    because the overall share answers "what does this round do to the bestiary"
                    and the humanoid share answers "what does it do to the things it is for",
                    and only the pair is honest. Quoting the first alone reads as a round that
                    does nothing.

    This is a census of *blueprints*, which is a floor and not the number - docs/LESSONS.md
    records a wished creature arming itself after spawning with a weapon its blueprint never
    mentions. Anything quoting these figures should say so.
    """
    index = BlueprintIndex(load_all(game, lenient=True))
    objects = index.objects
    chain, has_tag, has_part = index.chain, index.has_tag, index.has_part

    def intprop(name: str, prop: str) -> str | None:
        for o in chain(name):
            for e in o.findall("intproperty"):
                if e.get("Name") == prop:
                    return e.get("Value")
        return None

    def is_natural(name: str) -> bool:
        return intprop(name, "Natural") == "1" or has_tag(name, "NaturalGear")

    creatures = [
        name
        for name in objects
        if has_tag(name, "Creature") and not has_tag(name, "BaseObject")
    ]
    if not creatures:
        raise SystemExit(
            "error: no creature blueprints found. Either the game moved its data or the "
            "definition in collect_census no longer matches it - fix the definition rather "
            "than dropping the census, or every figure that cites it stops being checked."
        )

    humanoids = [name for name in creatures if has_tag(name, "Humanoid")]

    def count_into(tally: dict, prefix: str, names: list) -> None:
        """Sort one population into the buckets and check the result partitions it."""
        for name in names:
            carried = [
                e.get("Blueprint")
                for o in chain(name)
                for e in o.findall("inventoryobject")
                if e.get("Blueprint")
            ]
            if not carried:
                tally[f"{prefix}-inventory-none"] += 1
            elif all(b[0] in "@*" for b in carried):
                tally[f"{prefix}-inventory-popref"] += 1
            else:
                real = [b for b in carried if b[0] not in "@*" and not is_natural(b)]
                if not real:
                    tally[f"{prefix}-inventory-natural"] += 1
                elif not any(has_part(b, "Metal") for b in real):
                    tally[f"{prefix}-inventory-nonmetal"] += 1
                else:
                    tally[f"{prefix}-rustable"] += 1
        tally[f"{prefix}-rust-dead"] = (
            tally[f"{prefix}-inventory-none"]
            + tally[f"{prefix}-inventory-natural"]
            + tally[f"{prefix}-inventory-nonmetal"]
        )
        # Every member lands in exactly one bucket. If it does not, a category was added without
        # its arithmetic and the totals would look plausible while summing to the wrong thing.
        partitioned = (
            tally[f"{prefix}-rust-dead"]
            + tally[f"{prefix}-inventory-popref"]
            + tally[f"{prefix}-rustable"]
        )
        if partitioned != len(names):
            raise SystemExit(
                f"error: the {prefix} census buckets sum to {partitioned}, not {len(names)}. "
                f"The categories no longer partition the set."
            )

    tally = dict.fromkeys(CENSUS_KEYS, 0)
    tally["creature-blueprints"] = len(creatures)
    tally["humanoid-blueprints"] = len(humanoids)
    tally["creature-blueprints-bleeding"] = sum(
        1 for name in creatures if intprop(name, "Bleeds") == "1"
    )
    count_into(tally, "creature", creatures)
    count_into(tally, "humanoid", humanoids)
    return {key: str(value) for key, value in tally.items()}


MOD = Path("mod")


def merged_record_names() -> tuple[list[str], list[str]]:
    """Every vanilla record this mod edits: blueprints by `Load="Merge"`, and population tables.

    The scope of the citation set, and the reason it is a citation set rather than a dump. Each
    entry exists because this fork edits that record, which is the same standard CITED_FIGURES
    holds itself to.

    A consequence worth knowing: adding a new merge means regenerating this snapshot, and that
    needs the game. That is the intended shape - a new merge is a new citation, and a record the
    snapshot has never seen makes its check fail loudly rather than skip in silence.
    """
    blueprints: set[str] = set()
    for f in sorted((MOD / "ObjectBlueprints").glob("*.xml")):
        for obj in parse(f, lenient=True).iter("object"):
            if obj.get("Load") == "Merge" and obj.get("Name"):
                blueprints.add(obj.get("Name"))
    tables: set[str] = set()
    pops = MOD / "PopulationTables.xml"
    if pops.is_file():
        for pop in parse(pops, lenient=True).iter("population"):
            if pop.get("Name"):
                tables.add(pop.get("Name"))
    return sorted(blueprints), sorted(tables)


def _chain_attr(chain, part: str, key: str) -> str | None:
    """The nearest ancestor's value for one part attribute. Takes the chain explicitly rather
    than closing over it - a nested function would capture the loop variable by reference, which
    is correct only for as long as every call stays inside the iteration that made it."""
    for ancestor in chain:
        for el in ancestor.findall("part"):
            if el.get("Name") == part and el.get(key) is not None:
                return el.get(key)
    return None


def _chain_tag(chain, key: str) -> str | None:
    """The nearest ancestor's value for one tag."""
    for ancestor in chain:
        for el in ancestor.findall("tag"):
            if el.get("Name") == key:
                return el.get("Value")
    return None


# The four elemental resistances an `Armor` part can state. No curve describes them, so a merge
# never states one - two zetachrome pieces did, both undocumented nerfs, and #380 reverted them.
RESISTANCES = ("Heat", "Cold", "Acid", "Elec")


def collect_aggregate_descendants(game: Path) -> dict[str, list[str]]:
    """Vanilla blueprints that would inherit an `AggregateWith` this mod merges onto a parent.

    `AggregateWith` bundles everything carrying the same value into ONE slot in a fabricated
    spawn table. The tag inherits, so merging it onto a vanilla parent reaches every vanilla
    *descendant* of that parent too - and collapses records vanilla deliberately kept apart.
    #171 shipped exactly that: `Hulking Baboon`, `Shrewd Baboon` and `Baboon Hero 1` joined
    `Baboon`'s slot, taking baboons in the hills from four slots to one, and `ClockworkBeetle` -
    a machine - began competing for the giant beetle's. Nothing errored.

    Vanilla builds aggregates the same way, by inheritance, so the mechanism is not the problem:
    `Snapjaw Scavanger` appears once in the whole game and Scavenger 0/1/2 inherit it. What
    matters is whether the chosen head has vanilla descendants vanilla wanted in their own slots.

    Recorded here rather than computed in validate_mod.py because that runs in CI without a game.
    The list changing on a Qud update is caught by --check, which is the point: a patch adding a
    descendant to one of these families is exactly the drift that would otherwise be invisible.
    """
    index = BlueprintIndex(load_all(game, lenient=True))
    heads = aggregate_heads()
    if not heads:
        return {}

    spawns: dict[str, bool] = {}
    for name, obj in index.objects.items():
        del obj
        spawns[name] = any(
            tag.get("Name", "").startswith("DynamicObjectsTable:")
            and not tag.get("Name", "").endswith((":Weight", ":Number", ":Builder"))
            and tag.get("Value") not in ("*delete", "{{{remove}}}")
            for record in index.chain(name)
            for tag in record.findall("tag")
        )

    out: dict[str, list[str]] = {}
    for head in sorted(heads):
        swept = [
            name
            for name in sorted(index.objects)
            if name != head
            and spawns.get(name)
            and any(r.get("Name") == head for r in index.chain(name))
        ]
        out[head] = swept
    return out


def aggregate_heads() -> set[str]:
    """Vanilla blueprints this mod merges an `AggregateWith` tag onto."""
    heads: set[str] = set()
    for path in sorted(MOD.rglob("*.xml")):
        try:
            root = parse(path)
        except (ET.ParseError, OSError):
            # validate_mod.py's check_wellformed owns a malformed mod file and says so in its own
            # words; failing the snapshot here as well would report one defect twice.
            continue
        for obj in root.iter("object"):
            name = obj.get("Name")
            if not name or obj.get("Load") != "Merge":
                continue
            if obj.find("tag[@Name='AggregateWith']") is not None:
                heads.add(name)
    return heads


def collect_merged_records(game: Path) -> dict[str, dict]:
    """What vanilla says about each record this mod merges into.

    The checks in validate_mod.py run in CI, where there is no game, so a merge is opaque to them:
    it carries no `Inherits` and usually no `Skill`, so `Cudgel8th` cannot be recognised as a
    cudgel from the mod's own XML at all. That is why damage could drift 40% across a whole family
    without failing anything.

    Only the fields a check actually compares against are recorded, and `None` where vanilla does
    not state one.
    """
    index = BlueprintIndex(load_all(game, lenient=True))
    names, _ = merged_record_names()
    out: dict[str, dict] = {}
    for name in names:
        chain = index.chain(name)
        if not chain:
            continue  # a merge whose target vanilla no longer has; check_vanilla_drift owns that

        record = {
            "skill": _chain_attr(chain, "MeleeWeapon", "Skill"),
            "two_handed": (_chain_attr(chain, "Physics", "UsesTwoSlots") or "").lower()
            == "true",
            "slot": _chain_attr(chain, "Armor", "WornOn"),
            "av": _chain_attr(chain, "Armor", "AV")
            or _chain_attr(chain, "Shield", "AV"),
            "weight": _chain_attr(chain, "Physics", "Weight"),
            "tier": _chain_tag(chain, "Tier"),
            # Added for #380. 142 of the 213 merges carried a price this fork had rewritten, and
            # nothing could see it: `item-curve` prices only the mod's own objects, on the rule
            # that vanilla sets its own values. Recording vanilla's side is what lets a check tell
            # a merge that restates a price from one that changes it.
            "value": _chain_attr(chain, "Commerce", "Value"),
            "resistances": {
                element: _chain_attr(chain, "Armor", element)
                for element in RESISTANCES
                if _chain_attr(chain, "Armor", element) is not None
            }
            or None,
        }
        if any(v not in (None, False) for v in record.values()):
            out[name] = record
    return out


SKILL_POWER_FIELDS = ("Cost", "Minimum", "Attribute")


def collect_skill_powers(game: Path) -> dict[str, dict]:
    """What vanilla says about each skill power this mod merges into.

    Same bargain as `collect_merged_records`, for the same reason: `mod/Skills.xml` is all
    `Load="Merge"`, so from the mod's own XML alone there is no way to tell a line that *changes*
    a power from one that merely restates vanilla's number. #421 is what that costs — three
    undocumented cuts stayed in this file after the option that governed them was removed, and
    nothing could see that the file and the option tables disagreed.

    Keyed `"<skill>/<power>"` so the JSON stays flat. Only the three fields a check compares are
    recorded, `None` where vanilla does not state one.
    """
    wanted: set[tuple[str, str]] = set()
    skills = MOD / "Skills.xml"
    if skills.is_file():
        for sk in parse(skills, lenient=True).iter("skill"):
            for pw in sk.iter("power"):
                if sk.get("Name") and pw.get("Name"):
                    wanted.add((sk.get("Name"), pw.get("Name")))

    out: dict[str, dict] = {}
    for f in sorted(game.glob("Skills*.xml")):
        for sk in parse(f, lenient=True).iter("skill"):
            for pw in sk.iter("power"):
                key = (sk.get("Name"), pw.get("Name"))
                if key not in wanted:
                    continue
                out[f"{key[0]}/{key[1]}"] = {
                    field: pw.get(field) for field in SKILL_POWER_FIELDS
                }
    return out


def collect_tag_forms(game: Path) -> dict[str, str]:
    """Which element vanilla writes each tag name with: `tag` or `stag`.

    They are not interchangeable, and the difference is invisible in the XML.
    `XRL.World.GameObjectFactory` loads both into the same dictionary, but renames one:

        if (item8.Value.NodeName == "stag") { text = "Semantic" + text; ... }
        gameObjectBlueprint.Tags.Add(text, value);

    So `<stag Name="Floating" />` produces the tag **`SemanticFloating`**, not `Floating`, and a
    consumer looking for one will not find the other. Writing a tag in the form vanilla does not
    use puts it on a key nothing reads - which fails the way an unread declaration always fails
    here, in silence.

    Scoped to the tag names this mod actually writes, so this stays a citation set rather than a
    dump of vanilla's 710. Names vanilla writes both ways carry no opinion and are omitted.
    """
    wanted: set[str] = set()
    for f in sorted((MOD / "ObjectBlueprints").glob("*.xml")):
        for obj in parse(f, lenient=True).iter("object"):
            for child in obj:
                if child.tag in ("tag", "stag") and child.get("Name"):
                    wanted.add(child.get("Name"))

    forms: dict[str, set[str]] = {}
    for f in sorted((game / "ObjectBlueprints").glob("*.xml")):
        for obj in parse(f, lenient=True).iter("object"):
            for child in obj:
                if child.tag in ("tag", "stag") and child.get("Name") in wanted:
                    forms.setdefault(child.get("Name"), set()).add(child.tag)
    return {name: next(iter(k)) for name, k in sorted(forms.items()) if len(k) == 1}


def collect_tag_forms_absent(game: Path) -> dict[str, str]:
    """Why a tag name this mod writes has no entry in `tag_forms`, for each name that has none.

    A citation of an absence, the same bargain `collect_absent_tables` makes and for the same
    reason: without it, "not in `tag_forms`" means either "vanilla has no opinion about this name"
    or "the snapshot predates this tag", and nothing can tell those apart. That ambiguity is #507 -
    a mod change that adds a tag name goes unnoticed until someone with the game installed happens
    to run the digest check, which twice in one day meant blocking a commit that had nothing to do
    with it.

    With both recorded, `validate_mod.py` can assert that every tag name this mod writes is
    accounted for one way or the other, from files that are all in the repository. That check needs
    no Caves of Qud install and so runs where it matters, which the digest never can.

    Two reasons, and they are not the same fact:

    - `both` - vanilla writes the name as `<tag>` somewhere and `<stag>` somewhere else, so it
      carries no opinion about which this mod should use. There are four: `Fiber`, `Furniture`,
      `LightSource` and `Scrap`.
    - `absent` - vanilla never writes the name at all, so there is nothing to copy. `Finesse` and
      `Vixy_CreatureVariant` are this mod's own, read only by its own C#.
    """
    wanted: set[str] = set()
    for f in sorted((MOD / "ObjectBlueprints").glob("*.xml")):
        for obj in parse(f, lenient=True).iter("object"):
            for child in obj:
                if child.tag in ("tag", "stag") and child.get("Name"):
                    wanted.add(child.get("Name"))

    forms: dict[str, set[str]] = {}
    for f in sorted((game / "ObjectBlueprints").glob("*.xml")):
        for obj in parse(f, lenient=True).iter("object"):
            for child in obj:
                if child.tag in ("tag", "stag") and child.get("Name") in wanted:
                    forms.setdefault(child.get("Name"), set()).add(child.tag)

    return {
        name: ("both" if len(forms.get(name, ())) > 1 else "absent")
        for name in sorted(wanted)
        if len(forms.get(name, ())) != 1
    }


def collect_scatter_quantities(game: Path) -> dict[str, float]:
    """Vanilla's expected scattered quantity for each population table this mod adds entries to.

    The companion to `collect_table_weights`, for the entries that carry no `Weight` and which
    summed weight therefore measured as nothing at all (#474). The arithmetic is imported from
    `validate_mod` rather than repeated here: two sides of a ratio computed by two copies of a
    formula is a defect waiting for one copy to be edited, which is exactly how the weight version
    came to measure zero on both sides without anyone noticing.
    """
    from validate_mod import scatter_quantity

    _, wanted = merged_record_names()
    totals: dict[str, float] = {}
    for f in sorted(game.glob("PopulationTables*.xml")):
        for pop in parse(f, lenient=True).iter("population"):
            name = pop.get("Name")
            if name not in wanted:
                continue
            totals[name] = round(totals.get(name, 0.0) + scatter_quantity(pop), 4)
    return totals


def collect_absent_tables(game: Path) -> list[str]:
    """Population tables this mod merges into that vanilla does not define.

    A citation of an absence, which is worth as much as a citation of a figure and is otherwise
    indistinguishable from "the snapshot is stale". `LowerTremblingDunesZoneGlobals` is the live
    case: Freehold **commented the whole table out**, while `ZoneTemplates.xml` still names it in
    the Trembling Dunes' `<population Table=…>` block. A `Load="Merge"` into it therefore has no
    vanilla content to join.
    """
    merged = {
        pop.get("Name")
        for pop in parse(MOD / "PopulationTables.xml", lenient=True).iter("population")
        if pop.get("Name") and pop.get("Load") == "Merge"
    }
    seen: set[str] = set()
    for f in sorted(game.glob("PopulationTables*.xml")):
        for pop in parse(f, lenient=True).iter("population"):
            if pop.get("Name"):
                seen.add(pop.get("Name"))
    return sorted(m for m in merged if m not in seen)


def collect_table_weights(game: Path) -> dict[str, int]:
    """Vanilla's total drop weight for each population table this mod adds entries to.

    docs/STYLEGUIDE.md 3.2.1 caps this fork's share of a vanilla table at half. Share is a ratio,
    so the check cannot compute it without vanilla's side, and CI has no game.
    """
    _, wanted = merged_record_names()
    totals: dict[str, int] = {}
    for f in sorted(game.glob("PopulationTables*.xml")):
        for pop in parse(f, lenient=True).iter("population"):
            name = pop.get("Name")
            if name not in wanted:
                continue
            total = 0
            for obj in pop.iter("object"):
                if obj.get("Blueprint"):
                    try:
                        total += int(obj.get("Weight") or 0)
                    except ValueError:
                        pass
            totals[name] = totals.get(name, 0) + total
    return totals


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


def collect_mutation_classes(game: Path) -> list[str]:
    """Every `Class` the game's mutation catalogue declares.

    This is the authority for whether a mutation can be *granted*, which is not the same question
    as whether its class exists. `GasGeneration` is a real, concrete, instantiable class with no
    catalogue entry, so `BaseMutation.GetMutationEntry()` logs an error and synthesises a fallback -
    which is #226, six shipped chips at roughly half their intended gas duration. A check against
    the `XRL.World.Parts.Mutation` namespace would have passed it.

    Both files matter: Mutations.xml carries the selectable ones and HiddenMutations.xml the rest,
    and a chip can name either.
    """
    classes = set()
    for name in ("Mutations.xml", "HiddenMutations.xml"):
        path = game / name
        if not path.is_file():
            raise SystemExit(
                f"error: {path} not found - the game moved its mutation catalogue"
            )
        for mutation in parse(path, lenient=True).iter("mutation"):
            if cls := mutation.get("Class"):
                classes.add(cls)
    if not classes:
        raise SystemExit(
            "error: no mutation classes found; the catalogue's shape has changed"
        )
    return sorted(classes)


def verify(
    game: Path,
    parts: set[str],
    blueprints: set[str],
    members: dict[str, list[str]],
    part_builders: set[str],
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
            builder = part.get("Builder")
            if builder and builder not in part_builders:
                problems.append(
                    f'vanilla sets <part Builder="{builder}">, which is not a type in '
                    f"{BUILDER_NAMESPACE}"
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


def unavailable(reason: str, remedy: str, require: bool) -> int:
    """Report a dependency this machine does not have, and say whether that is fatal.

    Same shape as `tools/compile_scripting.py`, deliberately: a contributor without Caves of Qud
    cannot act on a red hook, so the absence of the game is a skip rather than a failure. `--require`
    turns it into one, for when you mean to be sure the check actually ran.

    Loud on purpose, and it never prints beside the word OK. `docs/LESSONS.md` records that a check
    which quietly passes when it could not reach anything is worse than no check at all - and #244
    is a whole issue about this script answering confidently when it should not have answered.
    """
    stream = sys.stderr if require else sys.stdout
    print(f"{'ERROR' if require else 'SKIPPED'} - {reason}\n{remedy}", file=stream)
    return 2 if require else 0


def part_source_for(assembly: Path | None) -> str:
    """What `part_source` a run with these arguments produces. One definition, so the guard below
    and the snapshot itself cannot disagree about what kind of build this is."""
    return f"assembly:{PART_NAMESPACE}" if assembly is not None else "vanilla-xml"


def committed_part_source() -> str | None:
    """The `part_source` of the snapshot on disk, or None if there isn't one to compare against."""
    if not SNAPSHOT_PATH.exists():
        return None
    try:
        return json.loads(SNAPSHOT_PATH.read_text()).get("part_source")
    except (OSError, json.JSONDecodeError):
        return None


def guard_part_source(assembly: Path | None) -> str | None:
    """Refuse to write or check across a change of part source. Returns an error, or None to go on.

    The digest covers the part list, and the two sources produce different lists - 1605 names from
    the assembly against 949 from vanilla's own usage, because vanilla declares far more parts than
    it uses. So mixing them breaks both paths, and #244 caught both:

      writing   a plain run over an assembly-built snapshot drops 656 names. Nothing errors. The
                consequence surfaces later as validate_mod rejecting a mod part that is perfectly
                real, with nothing pointing back here.
      checking  worse, because it is confidently wrong. `--check` without `--assembly` compares an
                assembly-built snapshot to a vanilla-xml one, calls a current file STALE, exits 1,
                and advises "Re-run without --check to update" - which is the exact command that
                performs the corruption above. The tool hands you the wrong fix for a problem you
                do not have.

    Hence refusing in BOTH directions rather than only the narrowing one. A snapshot built one way
    and checked the other is not a check, whichever way round it is.
    """
    committed = committed_part_source()
    running = part_source_for(assembly)
    if committed is None or committed == running:
        return None
    remedy = (
        "add --assembly (it needs ilspycmd: dotnet tool install -g ilspycmd)"
        if committed.startswith("assembly:")
        else "drop --assembly"
    )
    return (
        f"{SNAPSHOT_PATH} was built with part_source {committed!r}, but this run would use "
        f"{running!r}.\nThe digest covers the part list and the two sources produce different "
        f"lists, so comparing or overwriting across them is meaningless.\n\nTo match the "
        f"committed snapshot, {remedy}."
    )


def build(game: Path, assembly: Path | None, member_assembly: Path) -> dict:
    part_source = part_source_for(assembly)
    parts = (
        collect_parts(assembly)
        if assembly is not None
        else collect_parts_from_xml(game)
    )
    blueprints = collect_blueprints(game)
    members, part_builders, non_leveling = collect_members(member_assembly)
    figures = collect_figures(game)
    mutation_classes = collect_mutation_classes(game)
    figures.update(collect_census(game))
    merged_records = collect_merged_records(game)
    aggregate_descendants = collect_aggregate_descendants(game)
    table_weights = collect_table_weights(game)
    tag_forms = collect_tag_forms(game)
    tag_forms_absent = collect_tag_forms_absent(game)
    scatter_quantities = collect_scatter_quantities(game)
    absent_tables = collect_absent_tables(game)
    skill_powers = collect_skill_powers(game)

    problems = verify(game, set(parts), set(blueprints), members, set(part_builders))
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
    figure_repr = "\n".join(f"{k}={v}" for k, v in sorted(figures.items()))
    builder_repr = "\n".join(part_builders)
    digest = hashlib.sha256(
        (
            "\n".join(parts)
            + "\0"
            + "\n".join(blueprints)
            + "\0"
            + member_repr
            + "\0"
            + figure_repr
            + "\0"
            + builder_repr
            + "\0"
            + "\n".join(mutation_classes)
            + "\0"
            + "\n".join(non_leveling)
            + "\0"
            + json.dumps(merged_records, sort_keys=True)
            + "\0"
            + json.dumps(table_weights, sort_keys=True)
            + "\0"
            + json.dumps(tag_forms, sort_keys=True)
            + "\0"
            + json.dumps(tag_forms_absent, sort_keys=True)
            + "\0"
            + json.dumps(scatter_quantities, sort_keys=True)
            + "\0"
            + json.dumps(absent_tables, sort_keys=True)
            + "\0"
            + json.dumps(skill_powers, sort_keys=True)
            + "\0"
            + json.dumps(aggregate_descendants, sort_keys=True)
        ).encode()
    ).hexdigest()[:16]
    return {
        "_comment": (
            "Generated by tools/snapshot_qud_api.py from an installed Caves of Qud. Two kinds "
            "of entry, and the distinction is the rule this file is kept to. Most of it is "
            "IDENTIFIERS - part, blueprint, member and builder names, the same ones this mod's "
            'own XML already writes in every Load="Merge". The rest is CITATIONS: figures, '
            "merged_records, table_weights and scatter_quantities hold values read out of "
            "Freehold's data, and each "
            "exists because something here depends on it - a document quotes it, or a check "
            "compares against a vanilla record this fork edits. No descriptions, text or art, and "
            "no value without a dependant: a list of citations, not a dump of the game. "
            "Regenerate after every Qud update; a stale snapshot shows up as a false positive on "
            "a newly added vanilla name, which is loud rather than silent."
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
            "figures": len(figures),
            "part_builders": len(part_builders),
            "mutation_classes": len(mutation_classes),
            "non_leveling_mutations": len(non_leveling),
            "merged_records": len(merged_records),
            "table_weights": len(table_weights),
            "tag_forms": len(tag_forms),
            "tag_forms_absent": len(tag_forms_absent),
            "scatter_quantities": len(scatter_quantities),
            "absent_tables": len(absent_tables),
            "skill_powers": len(skill_powers),
            "aggregate_descendants": len(aggregate_descendants),
        },
        "mutation_classes": mutation_classes,
        "non_leveling_mutations": non_leveling,
        "parts": parts,
        "blueprints": blueprints,
        "members": members,
        "part_builders": part_builders,
        "figures": dict(sorted(figures.items())),
        "merged_records": dict(sorted(merged_records.items())),
        "table_weights": dict(sorted(table_weights.items())),
        "tag_forms": tag_forms,
        "tag_forms_absent": tag_forms_absent,
        "scatter_quantities": dict(sorted(scatter_quantities.items())),
        "absent_tables": absent_tables,
        "skill_powers": dict(sorted(skill_powers.items())),
        "aggregate_descendants": dict(sorted(aggregate_descendants.items())),
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
        help="read the part list from Assembly-CSharp.dll instead of vanilla's XML usage. This "
        "is how the committed snapshot is built, so it is what reproduces it. Needs ilspycmd. "
        "Pass bare to auto-locate, or give a path.",
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="compare the committed snapshot against the install; write nothing",
    )
    ap.add_argument(
        "--require",
        action="store_true",
        help="fail instead of skipping when the game, the .NET SDK or ilspycmd is missing. The "
        "skip exists so the pre-commit hook is harmless on a machine without Caves of Qud; pass "
        "this when you mean to be sure the check ran.",
    )
    args = ap.parse_args()

    # Absences are skips rather than failures, so the hook is harmless without the game. Only
    # under --check: a WRITE with a missing dependency has to be an error, because silently
    # writing nothing and returning 0 is how a regeneration gets believed to have happened.
    def missing(what: str, remedy: str) -> int:
        """One dependency absent. A skip under --check, an error on the write path.

        Never a skip when writing: a regeneration that quietly does nothing and returns 0 is how
        a snapshot comes to be believed current when it was never rebuilt.
        """
        reason = (
            f"cannot {'check' if args.check else 'regenerate'} the snapshot: {what}"
        )
        if not args.check:
            print(f"{reason}\n{remedy}", file=sys.stderr)
            return 2
        return unavailable(reason, remedy, args.require)

    game = find_game(args.game)
    if game is None:
        return missing(
            "the installed game data was not found",
            "Pass --game PATH pointing at StreamingAssets/Base (on macOS this lives inside\n"
            "CoQ.app/Contents/Resources/Data). Nothing else verifies tools/qud-api.json.",
        )

    assembly = None
    if args.assembly:
        # Checked before find_assembly so the message names the thing that is actually absent:
        # most machines have the game and not the decompiler, not the other way round.
        if not shutil.which("ilspycmd"):
            return missing(
                "ilspycmd is not on PATH",
                "  dotnet tool install -g ilspycmd\n"
                '  export PATH="$PATH:$HOME/.dotnet/tools"\n'
                "The export is needed even if you installed it: the .NET installer's own\n"
                "/etc/paths.d/dotnet-cli-tools holds the literal string `~/.dotnet/tools`, and\n"
                "path_helper never expands `~`, so that entry has never resolved.\n"
                "ilspycmd is needed because the committed snapshot's part list comes from the\n"
                "assembly.",
            )
        assembly = find_assembly(None if args.assembly == "auto" else args.assembly)
        if assembly is None:
            return missing("Assembly-CSharp.dll was not found", "Pass --assembly PATH.")

    member_assembly = assembly or find_assembly(None)
    if member_assembly is None:
        return missing(
            "Assembly-CSharp.dll was not found, and it is where part members live",
            "Pass --assembly PATH.",
        )

    mismatch = guard_part_source(assembly)
    if mismatch:
        print(mismatch, file=sys.stderr)
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
        f"{fresh['counts']['part_builders']} part builders, "
        f"steam build {fresh['steam_build_id']}, digest {fresh['digest']}"
    )
    print(
        "Vanilla satisfies all three rules, so they are safe to enforce against the mod."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
