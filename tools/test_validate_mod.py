#!/usr/bin/env python3
"""Tests for tools/validate_mod.py.

This script gates every commit, and until #224 it was the only tool in tools/ without tests. The
reason it needed them is the shape of its failures rather than their likelihood: four of the six
places that recognise a mod-owned blueprint fail by **skipping** the object, so a prefix the script
does not know about produces a clean green run over content nobody checked. That is
indistinguishable from a run that found nothing wrong, which is the trap docs/LESSONS.md keeps
returning to.

So every test here is a positive control in one direction or the other. A check is only proven by
watching it fire on something broken AND stay quiet on something sound, and the tests assert both
for each prefix. Synthetic mod directories only: no game, no network, no dependencies.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from pathlib import Path
from typing import ClassVar

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_mod


@contextmanager
def chdir(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


# The real API snapshot, read once. check_part_names returns early without it — so a fixture
# lacking it makes that test pass while the check never runs at all, which is the vacuous-pass
# this file exists to avoid. Written into each fixture rather than mocked, so the test exercises
# the same 1605-name set the validator uses in anger.
API_SNAPSHOT = Path(__file__).resolve().parent / "qud-api.json"


def write_mod(tmp: Path, blueprints: str = "", tables: str = "") -> Path:
    """A minimal mod/ tree containing only what a check needs to read."""
    tools = tmp / "tools"
    tools.mkdir(exist_ok=True)
    (tools / "qud-api.json").write_bytes(API_SNAPSHOT.read_bytes())
    mod = tmp / "mod"
    (mod / "ObjectBlueprints").mkdir(parents=True)
    (mod / "ObjectBlueprints" / "Test.xml").write_text(
        f'<?xml version="1.0" encoding="utf-8" ?>\n<objects>\n{blueprints}\n</objects>\n',
        encoding="utf-8",
    )
    if tables:
        (mod / "Core").mkdir(exist_ok=True)
        (mod / "Core" / "PopulationTables.xml").write_text(
            f'<?xml version="1.0" encoding="utf-8" ?>\n<population>\n{tables}\n</population>\n',
            encoding="utf-8",
        )
    return mod


# Vanilla's Tinker III, as tools/qud-api.json records it. The skill-option-coverage tests read
# this rather than the real snapshot so they state the vanilla side they are asserting against.
_VANILLA_TINKER3 = {
    "Tinkering/Tinker III": {
        "Cost": "300",
        "Minimum": "29",
        "Attribute": "Intelligence",
    }
}


def findings_for(check, tmp: Path) -> list[tuple[str, str]]:
    """Run one check against the synthetic mod and return what it reported."""
    with chdir(tmp):
        f = validate_mod.Findings()
        roots = validate_mod.check_wellformed(f)
        check(f, roots)
        return f.items


# The prefixes these tests cover, written out deliberately rather than read from
# validate_mod.MOD_PREFIXES. A test that derives its inputs from the value under test stops
# testing anything the moment that value shrinks: drop "Vixy_" from the constant and every
# subTest loop below would quietly iterate one prefix and still pass. That is the vacuous-loop
# failure docs/LESSONS.md records for unquoted shell variables, in Python. Constants.test_covers
# is what ties this list back to the real one.
COVERED_PREFIXES = ("Raven_", "Vixy_")


class PrefixRecognition(unittest.TestCase):
    """Both mod prefixes must be recognised at every site, and neither may swallow vanilla."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    # ---------------------------------------------------------------- merge discipline

    def test_mod_prefixed_objects_need_no_merge(self) -> None:
        """A new mod object is a declaration, not an edit of a vanilla record.

        Before #224 the Vixy_ half of this failed: the object read as vanilla, so declaring it
        without Load="Merge" was reported as a charter rule 1 violation — a false positive that
        would have blocked the first new blueprint.
        """
        for prefix in COVERED_PREFIXES:
            with self.subTest(prefix=prefix):
                tmp = Path(tempfile.mkdtemp(dir=self.tmp))
                write_mod(tmp, f'  <object Name="{prefix}Widget" />')
                self.assertEqual(
                    findings_for(validate_mod.check_merge_discipline, tmp),
                    [],
                    f"{prefix} object was treated as a vanilla record",
                )

    def test_vanilla_object_without_merge_is_still_reported(self) -> None:
        """The control. If this ever passes silently the check has stopped working entirely."""
        tmp = Path(tempfile.mkdtemp(dir=self.tmp))
        write_mod(tmp, '  <object Name="Lead Slug" />')
        items = findings_for(validate_mod.check_merge_discipline, tmp)
        self.assertTrue(
            items, "vanilla record edited without Load=Merge was not reported"
        )
        self.assertEqual(items[0][0], "merge-discipline")

    # ------------------------------------------------------------------- reachability

    def test_unreachable_mod_object_is_reported(self) -> None:
        """Before #224 a Vixy_ object was skipped here, so #6 and #7's defect class could recur
        silently under the new prefix."""
        for prefix in COVERED_PREFIXES:
            with self.subTest(prefix=prefix):
                tmp = Path(tempfile.mkdtemp(dir=self.tmp))
                write_mod(tmp, f'  <object Name="{prefix}Orphan" />')
                items = findings_for(validate_mod.check_reachability, tmp)
                self.assertTrue(
                    any("Orphan" in detail for _, detail in items),
                    f"unreachable {prefix} object was not reported",
                )

    def test_reachable_mod_object_is_not_reported(self) -> None:
        """The other direction: a tinkerable object is obtainable and must stay quiet."""
        for prefix in COVERED_PREFIXES:
            with self.subTest(prefix=prefix):
                tmp = Path(tempfile.mkdtemp(dir=self.tmp))
                write_mod(
                    tmp,
                    f'  <object Name="{prefix}Craftable">\n'
                    '    <part Name="TinkerItem" Bits="C" CanBuild="true" />\n'
                    "  </object>",
                )
                self.assertEqual(findings_for(validate_mod.check_reachability, tmp), [])

    def test_dynamic_table_tag_counts_as_reachable(self) -> None:
        """#171: creature variants self-register with a tag and sit in no population table.

        Checking only `Blueprint=` called all 32 unobtainable while they spawned perfectly well.
        """
        for prefix in COVERED_PREFIXES:
            with self.subTest(prefix=prefix):
                tmp = Path(tempfile.mkdtemp(dir=self.tmp))
                write_mod(
                    tmp,
                    f'  <object Name="{prefix}BrindleDog" Inherits="Dog">\n'
                    '    <tag Name="DynamicObjectsTable:Hills_Creatures" />\n'
                    "  </object>",
                )
                self.assertEqual(findings_for(validate_mod.check_reachability, tmp), [])

    def test_dynamic_table_tag_that_only_removes_is_not_reachable(self) -> None:
        """The direction that would have made the fix vacuous.

        A variant carries `*delete` tags to stay OUT of the tables it inherits. Counting those as
        distribution would pass every blueprint that names a table for any reason at all, and the
        check would go quiet on exactly the defect it exists for. Same for the `:Weight` modifier,
        which tunes an entry rather than creating one.
        """
        for prefix in COVERED_PREFIXES:
            for tag in (
                '<tag Name="DynamicObjectsTable:Hills_Creatures" Value="*delete" />',
                '<tag Name="DynamicObjectsTable:Hills_Creatures" Value="{{{remove}}}" />',
                '<tag Name="DynamicObjectsTable:Hills_Creatures:Weight" Value="3" />',
            ):
                with self.subTest(prefix=prefix, tag=tag):
                    tmp = Path(tempfile.mkdtemp(dir=self.tmp))
                    write_mod(
                        tmp,
                        f'  <object Name="{prefix}Orphan" Inherits="Dog">\n'
                        f"    {tag}\n"
                        "  </object>",
                    )
                    items = findings_for(validate_mod.check_reachability, tmp)
                    self.assertTrue(
                        any("Orphan" in detail for _, detail in items),
                        f"{tag} is not a distribution route but was treated as one",
                    )

    # ------------------------------------------------------------------- option wiring

    def _option_mod(self, blueprints: str) -> Path:
        """A mod declaring one option, plus whatever blueprints the case needs."""
        tmp = Path(tempfile.mkdtemp(dir=self.tmp))
        mod = write_mod(tmp, blueprints)
        (mod / "Core").mkdir(exist_ok=True)
        (mod / "Core" / "Options.xml").write_text(
            '<?xml version="1.0" encoding="utf-8" ?>\n<options>\n'
            '  <option ID="OptionTestGate" DisplayText="t" Category="Mods" '
            'Type="Checkbox" Default="Yes">\n    <helptext>t</helptext>\n  </option>\n'
            "</options>\n",
            encoding="utf-8",
        )
        return tmp

    def test_option_read_only_by_blueprint_tag_is_wired(self) -> None:
        """#171: an option can be read entirely in data, with no C# anywhere.

        `ExcludeFromDynamicEncountersOption` names an option ID that the game resolves itself.
        Scanning only mod/Scripting/*.cs called that option dead while it was doing its job.
        """
        for value in ("OptionTestGate", "!OptionTestGate"):
            with self.subTest(value=value):
                tmp = self._option_mod(
                    '  <object Name="Vixy_Gated">\n'
                    f'    <tag Name="ExcludeFromDynamicEncountersOption" Value="{value}" />\n'
                    "  </object>"
                )
                self.assertEqual(
                    findings_for(validate_mod.check_option_wiring, tmp), []
                )

    def test_option_with_no_reader_at_all_is_still_reported(self) -> None:
        """The positive control. Widening what counts as a read must not make the check vacuous -
        an option nothing reads is still the silent failure this check exists for."""
        tmp = self._option_mod('  <object Name="Vixy_Ungated" />')
        items = findings_for(validate_mod.check_option_wiring, tmp)
        self.assertTrue(
            any("OptionTestGate" in detail for _, detail in items),
            "an option read by nothing was not reported",
        )

    # ------------------------------------------------------------------ table targets

    def test_dangling_mod_blueprint_reference_is_reported(self) -> None:
        for prefix in COVERED_PREFIXES:
            with self.subTest(prefix=prefix):
                tmp = Path(tempfile.mkdtemp(dir=self.tmp))
                write_mod(
                    tmp,
                    "",
                    f'  <object Blueprint="{prefix}DoesNotExist" />',
                )
                items = findings_for(validate_mod.check_table_targets, tmp)
                self.assertTrue(
                    any("DoesNotExist" in detail for _, detail in items),
                    f"dangling {prefix} table reference was not followed",
                )

    def test_defined_mod_blueprint_reference_is_not_reported(self) -> None:
        for prefix in COVERED_PREFIXES:
            with self.subTest(prefix=prefix):
                tmp = Path(tempfile.mkdtemp(dir=self.tmp))
                write_mod(
                    tmp,
                    f'  <object Name="{prefix}Real" />',
                    f'  <object Blueprint="{prefix}Real" />',
                )
                self.assertEqual(
                    findings_for(validate_mod.check_table_targets, tmp), []
                )

    # --------------------------------------------------------------------- part names

    def test_mod_part_name_is_not_reported_as_unknown(self) -> None:
        """Mod-owned parts are check_scripting_parts' business, not check_part_names'.

        Without the prefix the part reads as a class that does not exist — the second false
        positive that would have blocked new content.
        """
        for prefix in COVERED_PREFIXES:
            with self.subTest(prefix=prefix):
                tmp = Path(tempfile.mkdtemp(dir=self.tmp))
                write_mod(
                    tmp,
                    f'  <object Name="{prefix}Thing">\n'
                    f'    <part Name="{prefix}SomePart" />\n'
                    "  </object>",
                )
                items = findings_for(validate_mod.check_part_names, tmp)
                self.assertFalse(
                    any(check == "qud-api-snapshot" for check, _ in items),
                    "the API snapshot was missing, so the check never ran",
                )
                self.assertFalse(
                    any("SomePart" in detail for _, detail in items),
                    f"{prefix} part name was reported as unknown",
                )

    def test_unknown_vanilla_part_name_is_reported(self) -> None:
        """Proves check_part_names actually fires inside the fixture, rather than passing
        because it bailed on a missing snapshot."""
        tmp = Path(tempfile.mkdtemp(dir=self.tmp))
        write_mod(
            tmp,
            '  <object Name="Raven_Thing">\n'
            '    <part Name="NoSuchPartClass" />\n'
            "  </object>",
        )
        items = findings_for(validate_mod.check_part_names, tmp)
        self.assertTrue(
            any("NoSuchPartClass" in detail for _, detail in items),
            "an unknown part name was not reported — the check is not running",
        )


class ScriptingParts(unittest.TestCase):
    """Widened in #146 from Mod* to the whole prefix.

    Until the scour slug there was no non-mutation part in mod/Scripting/, so Mod* covered every
    case. A part named Vixy_AmmoPayload fell between this check and check_part_names, which skips
    mod-prefixed names precisely because this one is supposed to cover them — so a typo in the part
    name would have loaded as nothing at all.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _mod_with(self, part: str, cs: str | None) -> Path:
        tmp = Path(tempfile.mkdtemp(dir=self.tmp))
        write_mod(
            tmp,
            f'  <object Name="Vixy_Thing">\n    <part Name="{part}" />\n  </object>',
        )
        scripting = tmp / "mod" / "Scripting"
        scripting.mkdir(parents=True, exist_ok=True)
        if cs:
            (scripting / f"{cs}.cs").write_text(
                f"namespace XRL.World.Parts {{ public class {cs} {{ }} }}",
                encoding="utf-8",
            )
        return tmp

    def test_non_mutation_part_without_a_class_is_reported(self) -> None:
        for part in ("Vixy_AmmoPayload", "Raven_SomeCombatPart"):
            with self.subTest(part=part):
                items = findings_for(
                    validate_mod.check_scripting_parts, self._mod_with(part, None)
                )
                self.assertTrue(
                    any(part in detail for _, detail in items),
                    f"{part} has no class and was not reported",
                )

    def test_part_with_a_matching_class_is_not_reported(self) -> None:
        items = findings_for(
            validate_mod.check_scripting_parts,
            self._mod_with("Vixy_AmmoPayload", "Vixy_AmmoPayload"),
        )
        self.assertEqual(items, [])

    def test_vanilla_part_name_is_not_required_to_have_a_class(self) -> None:
        """The boundary: this check owns mod parts only. RustOnHit is the game's."""
        items = findings_for(
            validate_mod.check_scripting_parts, self._mod_with("RustOnHit", None)
        )
        self.assertEqual(items, [])


class MutationTypeArguments(unittest.TestCase):
    """#256. Compiling proves the class exists; it does not prove the game will grant it.

    `GasGeneration` compiled cleanly and passed `unknown-part` for two years while six chips ran at
    roughly half their intended duration, because nothing looked inside the generic (#226).
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _findings(self, source: str) -> list[str]:
        tmp = Path(tempfile.mkdtemp(dir=self.tmp))
        write_mod(tmp)
        scripting = tmp / "mod" / "Scripting"
        scripting.mkdir(parents=True, exist_ok=True)
        (scripting / "Raven_ModThing.cs").write_text(source, encoding="utf-8")
        with chdir(tmp):
            f = validate_mod.Findings()
            validate_mod.check_mutation_type_arguments(f)
        return [c for c, _ in f.items]

    def test_a_catalogued_mutation_passes(self) -> None:
        codes = self._findings(
            "public class Raven_ModThing : ModImprovedMutationBase<CorrosiveGasGeneration> { }"
        )
        self.assertNotIn("unknown-mutation", codes)

    def test_a_class_with_no_catalogue_entry_is_reported(self) -> None:
        codes = self._findings(
            "public class Raven_ModThing : ModImprovedMutationBase<GasGeneration> { }"
        )
        self.assertIn(
            "unknown-mutation",
            codes,
            "GasGeneration has no <mutation Class=...> and must be reported - this is #226",
        )

    def test_an_invented_class_is_reported(self) -> None:
        codes = self._findings(
            "public class Raven_ModThing : ModImprovedMutationBase<NotAMutationAtAll> { }"
        )
        self.assertIn("unknown-mutation", codes)

    def test_a_commented_out_declaration_is_ignored(self) -> None:
        """The mod keeps dormant scripts and blueprints commented out, so this is not academic."""
        for source in (
            "// public class X : ModImprovedMutationBase<GasGeneration> { }",
            "/* public class X : ModImprovedMutationBase<GasGeneration> { } */",
        ):
            with self.subTest(source=source):
                self.assertNotIn("unknown-mutation", self._findings(source))

    def test_whitespace_inside_the_generic_is_tolerated(self) -> None:
        codes = self._findings(
            "public class Raven_ModThing : ModImprovedMutationBase< GasGeneration > { }"
        )
        self.assertIn("unknown-mutation", codes)


class GradedUnlevellableChips(unittest.TestCase):
    """#347. Kindle and Frost Webs shipped three grades each, and all six were one item.

    Nothing existing could see it. `unknown-mutation` passes because both are genuinely
    catalogued, and `item-curve` passes because each price sat exactly on the chip curve for its
    tier. Only the mutation's own method body knows, which is what `non_leveling_mutations` in the
    snapshot carries.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _findings(
        self, blueprints: str, mutation: str = "Kindle", api: dict | None = None
    ) -> list[tuple[str, str]]:
        tmp = Path(tempfile.mkdtemp(dir=self.tmp))
        write_mod(tmp, blueprints=blueprints)
        if api is not None:
            (tmp / "tools" / "qud-api.json").write_text(json.dumps(api))
        scripting = tmp / "mod" / "Scripting"
        scripting.mkdir(parents=True, exist_ok=True)
        (scripting / "Raven_ModDead.cs").write_text(
            f"public class Raven_ModDead : ModImprovedMutationBase<{mutation}> {{ }}",
            encoding="utf-8",
        )
        (scripting / "Raven_ModLive.cs").write_text(
            "public class Raven_ModLive : ModImprovedMutationBase<Teleportation> { }",
            encoding="utf-8",
        )
        return findings_for(validate_mod.check_graded_unlevellable_chips, tmp)

    @staticmethod
    def _chip(name: str, part_tier: str, extra: str = "") -> str:
        return (
            f'  <object Name="{name}" Inherits="Raven_Base Psionic Chip">\n'
            f'    <part Name="Raven_ModDead" Tier="{part_tier}" />\n'
            f"{extra}"
            f"  </object>"
        )

    def test_the_real_snapshot_knows_kindle_cannot_level(self) -> None:
        """Guards the whole class against a vacuous pass: if the snapshot ever loses the list,
        every test below would pass while the check returned early."""
        api = json.loads(API_SNAPSHOT.read_text())
        self.assertIn("Kindle", api["non_leveling_mutations"])
        self.assertIn("FrostWebs", api["non_leveling_mutations"])
        self.assertNotIn("Teleportation", api["non_leveling_mutations"])

    def test_one_level_across_the_line_passes(self) -> None:
        items = self._findings(
            "\n".join(
                self._chip(f"Raven_{grade} Dead Chip", "2")
                for grade in ("Simple", "Improved", "Advanced")
            )
        )
        self.assertEqual(items, [])

    def test_a_varying_level_is_reported(self) -> None:
        items = self._findings(
            "\n".join(
                self._chip(f"Raven_{grade} Dead Chip", tier)
                for grade, tier in (
                    ("Simple", "2"),
                    ("Improved", "4"),
                    ("Advanced", "6"),
                )
            )
        )
        self.assertEqual([c for c, _ in items], ["dead-chip-grade"])
        self.assertIn("Raven_Improved Dead Chip", items[0][1])

    def test_a_mutation_that_levels_is_left_alone(self) -> None:
        """The ladder is the point everywhere else in the catalogue - 34 of the 36 chip lines."""
        items = self._findings(
            "\n".join(
                self._chip(f"Raven_{grade} Live Chip", tier)
                for grade, tier in (
                    ("Simple", "2"),
                    ("Improved", "4"),
                    ("Advanced", "6"),
                )
            ),
            mutation="Teleportation",
        )
        self.assertEqual(items, [])

    def test_a_chipset_forms_its_own_line(self) -> None:
        """A chipset grants a lower level than the single chip on purpose, so comparing every
        blueprint at once would refuse the correct arrangement."""
        chips = "\n".join(
            self._chip(f"Raven_{grade} Dead Chip", "2")
            for grade in ("Simple", "Improved", "Advanced")
        )
        sets = "\n".join(
            self._chip(
                f"Raven_{grade} Dead Chipset",
                "1",
                extra='    <part Name="Raven_ModLive" Tier="3" />\n',
            )
            for grade in ("Simple", "Improved", "Advanced")
        )
        self.assertEqual(self._findings(chips + "\n" + sets), [])

    def test_a_chipset_line_is_checked_on_its_own(self) -> None:
        sets = "\n".join(
            self._chip(
                f"Raven_{grade} Dead Chipset",
                tier,
                extra='    <part Name="Raven_ModLive" Tier="3" />\n',
            )
            for grade, tier in (("Simple", "1"), ("Improved", "2"), ("Advanced", "3"))
        )
        self.assertEqual([c for c, _ in self._findings(sets)], ["dead-chip-grade"])

    def test_a_snapshot_without_the_list_is_reported(self) -> None:
        """A missing list must be loud. Returning quietly would make every check above vacuous."""
        api = json.loads(API_SNAPSHOT.read_text())
        del api["non_leveling_mutations"]
        items = self._findings(self._chip("Raven_Simple Dead Chip", "2"), api=api)
        self.assertEqual([c for c, _ in items], ["qud-api-snapshot"])


class CSharpShapesAddedIn411(unittest.TestCase):
    """#411 introduced two C# shapes neither check had seen, and both misread them.

    Reported as findings on correct code, which is the failure mode that trains people to ignore a
    check. Both fixes narrow the check rather than widening what it accepts.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _scripting(self, name: str, source: str) -> Path:
        tmp = Path(tempfile.mkdtemp(dir=self.tmp))
        write_mod(tmp)
        scripting = tmp / "mod" / "Scripting"
        scripting.mkdir(parents=True, exist_ok=True)
        (scripting / name).write_text(source, encoding="utf-8")
        return tmp

    def _shape(self, source: str) -> list[str]:
        tmp = self._scripting("Raven_Thing.cs", source)
        with chdir(tmp):
            f = validate_mod.Findings()
            validate_mod.check_serializable_shape(f)
        return [c for c, _ in f.items]

    def test_an_expression_bodied_property_is_not_a_field(self) -> None:
        """It compiles to a get-only property with no backing storage, so nothing reaches a save."""
        self.assertEqual(
            self._shape(
                "[Serializable]\npublic class Raven_Thing {\n"
                '    protected override string VariantBlueprint => "Icy Vapor";\n}'
            ),
            [],
        )

    def test_a_real_instance_field_is_still_reported(self) -> None:
        """The boundary. Narrowing the check must not stop it doing its job."""
        self.assertEqual(
            self._shape(
                "[Serializable]\npublic class Raven_Thing {\n"
                '    public string VariantBlueprint = "Icy Vapor";\n}'
            ),
            ["serializable-shape"],
        )

    def test_a_static_field_is_still_ignored(self) -> None:
        self.assertEqual(
            self._shape(
                "[Serializable]\npublic class Raven_Thing {\n"
                '    public static string Shared = "x";\n}'
            ),
            [],
        )

    def _mutation(self, source: str) -> list[str]:
        tmp = self._scripting("Raven_ModThing.cs", source)
        with chdir(tmp):
            f = validate_mod.Findings()
            validate_mod.check_mutation_type_arguments(f)
        return [c for c, _ in f.items]

    def test_a_type_parameter_is_not_a_mutation_name(self) -> None:
        """A generic base passes T straight through, and a literal read reports 'T' as unknown."""
        self.assertEqual(
            self._mutation(
                "public abstract class Raven_Base<T> : ModImprovedMutationBase<T> "
                "where T : BaseMutation, new() { }"
            ),
            [],
        )

    def test_a_real_mutation_name_is_still_checked(self) -> None:
        """The boundary again: the #226 defect must still be caught through a generic file."""
        self.assertIn(
            "unknown-mutation",
            self._mutation(
                "public abstract class Raven_Base<T> : ModImprovedMutationBase<T> { }\n"
                "public class Raven_ModThing : ModImprovedMutationBase<GasGeneration> { }"
            ),
        )


class VersionAgreesWithChangelog(unittest.TestCase):
    """#309. The version lives in three places by hand and nothing held any two together.

    The git tag is deliberately outside this. On the commit that creates a release the manifest
    and the changelog both say the new version and the tag does not exist yet, so a check
    including it would fail the release commit itself.
    """

    def findings(self, version: str, changelog: str) -> list[tuple[str, str]]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
            with chdir(root):
                f = validate_mod.Findings()
                validate_mod.check_version_matches_changelog(f, version)
                return f.items

    def test_agreement_passes(self) -> None:
        self.assertEqual(
            self.findings("2.5.0", "## [Unreleased]\n\n## [2.5.0] - 2026-08-19\n"), []
        )

    def test_a_manifest_bumped_alone_is_reported(self) -> None:
        """The ordinary mistake: bump the manifest, forget to roll the changelog."""
        items = self.findings("2.6.0", "## [Unreleased]\n\n## [2.5.0] - 2026-08-19\n")
        self.assertTrue(items)
        self.assertIn("2.6.0", items[0][1])
        self.assertIn("2.5.0", items[0][1])

    def test_unreleased_is_not_mistaken_for_a_release(self) -> None:
        """`[Unreleased]` is always the first heading, and is never the answer."""
        items = self.findings("2.5.0", "## [Unreleased]\n\n## [2.4.0] - 2026-08-18\n")
        self.assertTrue(items, "the newest *released* heading is 2.4.0, not Unreleased")

    def test_a_changelog_with_no_release_is_reported(self) -> None:
        items = self.findings("2.5.0", "## [Unreleased]\n")
        self.assertTrue(items)
        self.assertIn("no released version heading", items[0][1])

    def test_a_missing_changelog_is_not_this_check_s_business(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, chdir(Path(tmp)):
            f = validate_mod.Findings()
            validate_mod.check_version_matches_changelog(f, "2.5.0")
            self.assertEqual(f.items, [])


class Constants(unittest.TestCase):
    def test_covers_every_prefix_the_validator_claims(self) -> None:
        """The tie between the tests' own list and the real constant.

        If a prefix is added to the validator and not to COVERED_PREFIXES, the tests above would
        never exercise it and would still pass. This is the one assertion that notices.
        """
        self.assertEqual(set(validate_mod.MOD_PREFIXES), set(COVERED_PREFIXES))


class NamingChecksTest(unittest.TestCase):
    """`<naming>` is outside check_merge_discipline's reach, and its failures are silent.

    Every test is a positive control in both directions: the check fires on a fragment that earns
    it and stays quiet on one that does not. These checks take all_roots directly, so no mod tree
    is needed — the roots dict is the whole input.
    """

    def roots(self, body: str) -> dict[Path, ET.Element]:
        return {Path("mod/Naming.xml"): ET.fromstring(body)}

    def findings(self, check, body: str) -> list[str]:
        f = validate_mod.Findings()
        check(f, self.roots(body))
        return [d for _, d in f.items]

    # -- merge discipline ----------------------------------------------------------------------

    def test_vanilla_namestyle_without_merge_is_a_finding(self):
        found = self.findings(
            validate_mod.check_naming_discipline,
            """
            <naming><namestyles><namestyle Name="Qudish">
              <prefixes><prefix Name="ze" /></prefixes>
            </namestyle></namestyles></naming>""",
        )
        self.assertTrue(any("removes a vanilla namestyle" in d for d in found), found)

    def test_merge_on_the_root_cascades_and_is_quiet(self):
        self.assertEqual(
            self.findings(
                validate_mod.check_naming_discipline,
                """
            <naming Load="Merge"><namestyles><namestyle Name="Qudish">
              <prefixes><prefix Name="ze" /></prefixes>
            </namestyle></namestyles></naming>""",
            ),
            [],
        )

    def test_a_child_overriding_merge_back_off_is_a_finding(self):
        """The cascade is `GetAttribute("Load") ?? LoadMode`, so a child can undo the root's."""
        found = self.findings(
            validate_mod.check_naming_discipline,
            """
            <naming Load="Merge"><namestyles><namestyle Name="Qudish">
              <prefixes Load="Replace"><prefix Name="ze" /></prefixes>
            </namestyle></namestyles></naming>""",
        )
        self.assertTrue(any("discards vanilla" in d for d in found), found)

    def test_a_new_namestyle_needs_no_merge(self):
        self.assertEqual(
            self.findings(
                validate_mod.check_naming_discipline,
                """
            <naming><namestyles><namestyle Name="Vixy_Qudish Feminine" Format="TitleCase">
              <prefixes Amount="1"><prefix Name="ze" /></prefixes>
            </namestyle></namestyles></naming>""",
            ),
            [],
        )

    def test_an_unprefixed_scope_on_a_vanilla_namestyle_is_a_finding(self):
        """Scopes merge by Name, so <scope Name="General"> rewrites vanilla's rather than adding."""
        found = self.findings(
            validate_mod.check_naming_discipline,
            """
            <naming Load="Merge"><namestyles><namestyle Name="Qudish">
              <scopes><scope Name="General" Priority="50" Combine="true" /></scopes>
            </namestyle></namestyles></naming>""",
        )
        self.assertTrue(any("rewrites vanilla's scope" in d for d in found), found)

    def test_a_prefixed_scope_on_a_vanilla_namestyle_is_quiet(self):
        self.assertEqual(
            self.findings(
                validate_mod.check_naming_discipline,
                """
            <naming Load="Merge"><namestyles><namestyle Name="Qudish">
              <scopes><scope Name="Vixy_Masc" Tag="Vixy_Masc" Priority="200" Combine="false" /></scopes>
            </namestyle></namestyles></naming>""",
            ),
            [],
        )

    # -- syllables -----------------------------------------------------------------------------

    def test_non_ascii_syllable_is_a_finding(self):
        found = self.findings(
            validate_mod.check_naming_syllables,
            """
            <naming Load="Merge"><namestyles><namestyle Name="Qudish">
              <prefixes><prefix Name="n\u00e9e" /></prefixes>
            </namestyle></namestyles></naming>""",
        )
        self.assertTrue(any("non-ASCII" in d for d in found), found)

    def test_ascii_syllables_are_quiet(self):
        self.assertEqual(
            self.findings(
                validate_mod.check_naming_syllables,
                """
            <naming Load="Merge"><namestyles><namestyle Name="Qudish">
              <prefixes><prefix Name="ze" /></prefixes>
            </namestyle></namestyles></naming>""",
            ),
            [],
        )

    def test_a_new_pool_without_amount_is_a_finding(self):
        found = self.findings(
            validate_mod.check_naming_syllables,
            """
            <naming><namestyles><namestyle Name="Vixy_New" Format="TitleCase">
              <prefixes><prefix Name="ze" /></prefixes>
            </namestyle></namestyles></naming>""",
        )
        self.assertTrue(any("defaults to" in d and "0" in d for d in found), found)

    def test_a_merge_omitting_amount_is_quiet(self):
        """A merge omits Amount deliberately: the loader keeps vanilla's when it is absent."""
        self.assertEqual(
            self.findings(
                validate_mod.check_naming_syllables,
                """
            <naming Load="Merge"><namestyles><namestyle Name="Qudish">
              <prefixes><prefix Name="ze" /></prefixes>
            </namestyle></namestyles></naming>""",
            ),
            [],
        )

    def test_a_new_namestyle_without_format_is_a_finding(self):
        found = self.findings(
            validate_mod.check_naming_syllables,
            """
            <naming><namestyles><namestyle Name="Vixy_New">
              <prefixes Amount="1"><prefix Name="ze" /></prefixes>
            </namestyle></namestyles></naming>""",
        )
        self.assertTrue(any("AsIs" in d for d in found), found)

    # -- priority ------------------------------------------------------------------------------

    def test_a_combining_scope_at_priority_zero_is_a_finding(self):
        found = self.findings(
            validate_mod.check_naming_priority,
            """
            <naming><namestyles><namestyle Name="Vixy_New" Format="TitleCase">
              <scopes><scope Name="General" Priority="0" Combine="true" /></scopes>
              <prefixes Amount="1"><prefix Name="ze" /></prefixes>
            </namestyle></namestyles></naming>""",
        )
        self.assertTrue(any("NameGenFail" in d for d in found), found)

    def test_a_combining_scope_at_100_is_a_finding(self):
        found = self.findings(
            validate_mod.check_naming_priority,
            """
            <naming><namestyles><namestyle Name="Vixy_New" Format="TitleCase">
              <scopes><scope Name="G" Gender="female" Priority="100" Combine="true" /></scopes>
              <prefixes Amount="1"><prefix Name="ze" /></prefixes>
            </namestyle></namestyles></naming>""",
        )
        self.assertTrue(any("displacing the faction" in d for d in found), found)

    def test_a_combining_scope_at_50_is_quiet(self):
        self.assertEqual(
            self.findings(
                validate_mod.check_naming_priority,
                """
            <naming><namestyles><namestyle Name="Vixy_New" Format="TitleCase">
              <scopes><scope Name="G" Gender="female" Priority="50" Combine="true" /></scopes>
              <prefixes Amount="1"><prefix Name="ze" /></prefixes>
            </namestyle></namestyles></naming>""",
            ),
            [],
        )

    def test_an_exclusive_scope_above_100_is_quiet(self):
        """Combine="false" takes over by design; the ceiling only binds combining scopes."""
        self.assertEqual(
            self.findings(
                validate_mod.check_naming_priority,
                """
            <naming><namestyles><namestyle Name="Vixy_New" Format="TitleCase">
              <scopes><scope Name="T" Tag="Vixy_Femme" Priority="200" Combine="false" /></scopes>
              <prefixes Amount="1"><prefix Name="ze" /></prefixes>
            </namestyle></namestyles></naming>""",
            ),
            [],
        )

    def test_a_vanilla_namestyle_is_not_held_to_the_priority_rules(self):
        """Vanilla's own Qudish sits at General/0 and must not be reported as a mod defect."""
        self.assertEqual(
            self.findings(
                validate_mod.check_naming_priority,
                """
            <naming Load="Merge"><namestyles><namestyle Name="Qudish">
              <scopes><scope Name="General" Priority="0" Combine="true" /></scopes>
            </namestyle></namestyles></naming>""",
            ),
            [],
        )

    # -- option coverage -----------------------------------------------------------------------

    def coverage(self, xml: str, cs: str) -> list[str]:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))
        (tmp / "mod" / "Scripting").mkdir(parents=True)
        (tmp / "mod" / "Scripting" / "Vixy_NameSyllables.cs").write_text(
            cs, encoding="utf-8"
        )
        f = validate_mod.Findings()
        with chdir(tmp):
            validate_mod.check_naming_option_coverage(f, self.roots(xml))
        return [d for _, d in f.items]

    CS = """
        private static readonly string[] AddedPrefixes = { %s };
        private static readonly string[] AddedInfixes = { };
        private static readonly string[] AddedPostfixes = { };
    """

    XML = """
        <naming Load="Merge"><namestyles><namestyle Name="Qudish">
          <prefixes>%s</prefixes>
        </namestyle></namestyles></naming>"""

    def test_matching_lists_are_quiet(self):
        self.assertEqual(
            self.coverage(self.XML % '<prefix Name="ze" />', self.CS % '"ze"'), []
        )

    def test_a_syllable_the_option_cannot_switch_off_is_a_finding(self):
        found = self.coverage(
            self.XML % '<prefix Name="ze" /><prefix Name="za" />', self.CS % '"ze"'
        )
        self.assertTrue(any("cannot switch it off" in d for d in found), found)

    def test_a_syllable_the_option_does_not_own_is_a_finding(self):
        """The dangerous direction: zeroing the weight on a vanilla syllable silences it."""
        found = self.coverage(self.XML % '<prefix Name="ze" />', self.CS % '"ze", "fa"')
        self.assertTrue(any("does not add" in d for d in found), found)


class OptionDefaultTest(unittest.TestCase):
    """#443. Nothing here is broken today, which is exactly why it needs a check: the one wrong
    value in the file worked by accident, so copying it was a coin flip."""

    def findings(self, body: str) -> list[str]:
        f = validate_mod.Findings()
        roots = {Path("mod/Options.xml"): ET.fromstring(f"<options>{body}</options>")}
        validate_mod.check_option_defaults(f, roots)
        return [d for _, d in f.items]

    def test_yes_and_no_are_quiet(self):
        self.assertEqual(
            self.findings(
                '<option ID="A" Type="Checkbox" Default="Yes" />'
                '<option ID="B" Type="Checkbox" Default="No" />'
            ),
            [],
        )

    def test_true_is_a_finding(self):
        """The dangerous one: "true" is not "Yes", so an option meant to default on ships off."""
        found = self.findings('<option ID="A" Type="Checkbox" Default="true" />')
        self.assertTrue(any("reads as off" in d for d in found), found)

    def test_false_is_a_finding_even_though_it_behaves(self):
        """It reads as off, which is usually what was meant -- but only by accident."""
        found = self.findings('<option ID="A" Type="Checkbox" Default="false" />')
        self.assertEqual(len(found), 1, found)

    def test_a_combo_default_outside_its_values_is_a_finding(self):
        found = self.findings(
            '<option ID="A" Type="Combo" Values="1,2,3" Default="9" />'
        )
        self.assertTrue(any("not one of its" in d for d in found), found)

    def test_a_combo_default_inside_its_values_is_quiet(self):
        self.assertEqual(
            self.findings('<option ID="A" Type="Combo" Values="1,2,3" Default="2" />'),
            [],
        )

    def test_a_slider_is_not_held_to_either_rule(self):
        """option-slider covers sliders, and a numeric Default is correct for one."""
        self.assertEqual(
            self.findings(
                '<option ID="A" Type="Slider" Min="0" Max="24" Default="16" />'
            ),
            [],
        )

    def test_a_file_that_is_not_an_options_file_is_skipped(self):
        f = validate_mod.Findings()
        roots = {
            Path("mod/Naming.xml"): ET.fromstring(
                '<naming><option ID="A" Type="Checkbox" Default="true" /></naming>'
            )
        }
        validate_mod.check_option_defaults(f, roots)
        self.assertEqual([d for _, d in f.items], [])


class AggregateSweep(unittest.TestCase):
    """#171: an AggregateWith merged onto a vanilla parent reaches vanilla's descendants too.

    This shipped. Hulking Baboon, Shrewd Baboon and Baboon Hero 1 folded into Baboon's single
    spawn slot, taking baboons in the hills from four slots to one, and a playtest found it rather
    than any check. Nothing errors: the tag parses, the table builds, the creatures just get
    rarer.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _mod(self, blueprints: str, descendants: dict) -> Path:
        tmp = Path(tempfile.mkdtemp(dir=self.tmp))
        mod = write_mod(tmp, blueprints)
        del mod
        snapshot = json.loads((tmp / "tools" / "qud-api.json").read_text())
        snapshot["aggregate_descendants"] = descendants
        (tmp / "tools" / "qud-api.json").write_text(
            json.dumps(snapshot), encoding="utf-8"
        )
        return tmp

    def test_an_unexempted_vanilla_descendant_is_reported(self) -> None:
        tmp = self._mod(
            '  <object Name="Baboon" Load="Merge">\n'
            '    <tag Name="AggregateWith" Value="Baboon" />\n'
            "  </object>",
            {"Baboon": ["Hulking Baboon"]},
        )
        items = findings_for(validate_mod.check_aggregate_sweep, tmp)
        self.assertTrue(items, "a swept-in vanilla descendant was not reported")
        self.assertEqual(items[0][0], "aggregate-sweep")
        self.assertIn("Hulking Baboon", items[0][1])
        self.assertIn("Baboon", items[0][1])

    def test_an_exempted_descendant_passes(self) -> None:
        tmp = self._mod(
            '  <object Name="Baboon" Load="Merge">\n'
            '    <tag Name="AggregateWith" Value="Baboon" />\n'
            "  </object>\n"
            '  <object Name="Hulking Baboon" Load="Merge">\n'
            '    <tag Name="AggregateWith" Value="*delete" />\n'
            "  </object>",
            {"Baboon": ["Hulking Baboon"]},
        )
        self.assertEqual(findings_for(validate_mod.check_aggregate_sweep, tmp), [])

    def test_every_descendant_is_reported_not_just_the_first(self) -> None:
        """Three baboons shipped swept-in. A check that stopped at one would have hidden two."""
        tmp = self._mod(
            '  <object Name="Baboon" Load="Merge">\n'
            '    <tag Name="AggregateWith" Value="Baboon" />\n'
            "  </object>",
            {"Baboon": ["Hulking Baboon", "Shrewd Baboon", "Baboon Hero 1"]},
        )
        items = findings_for(validate_mod.check_aggregate_sweep, tmp)
        self.assertEqual(len(items), 3)

    def test_a_head_with_no_descendants_reports_nothing(self) -> None:
        """Seven of the thirteen families are genuinely safe; they must stay quiet."""
        tmp = self._mod(
            '  <object Name="Dog" Load="Merge">\n'
            '    <tag Name="AggregateWith" Value="Dog" />\n'
            "  </object>",
            {"Dog": []},
        )
        self.assertEqual(findings_for(validate_mod.check_aggregate_sweep, tmp), [])

    def test_a_snapshot_without_the_key_does_not_pass_vacuously(self) -> None:
        """An older snapshot cannot tell "no descendants" from "never recorded". It returns early
        rather than reporting clean - but assert that explicitly, because a silent early return is
        the failure this file exists to catch, and the value is that it CANNOT be mistaken for a
        pass elsewhere: snapshot-check fails on a stale file first."""
        tmp = Path(tempfile.mkdtemp(dir=self.tmp))
        write_mod(
            tmp,
            '  <object Name="Baboon" Load="Merge">\n'
            '    <tag Name="AggregateWith" Value="Baboon" />\n'
            "  </object>",
        )
        snapshot = json.loads((tmp / "tools" / "qud-api.json").read_text())
        snapshot.pop("aggregate_descendants", None)
        (tmp / "tools" / "qud-api.json").write_text(
            json.dumps(snapshot), encoding="utf-8"
        )
        self.assertEqual(findings_for(validate_mod.check_aggregate_sweep, tmp), [])


class WorkshopDescriptionLength(unittest.TestCase):
    """Steam's limit is bytes. Measuring characters shipped a false pass (#171).

    A 7,963-character description was 8,019 bytes, because it carried 28 em dashes at three bytes
    each. The check said fine, Steam said k_EResultInvalidParam, and the upload failed - a check
    being wrong in the one direction that matters, at the one moment it was for.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _findings(self, description: str):
        tmp = Path(tempfile.mkdtemp(dir=self.tmp))
        (tmp / "mod").mkdir()
        (tmp / "mod" / "workshop.json").write_text(
            json.dumps({"WorkshopId": 1, "Description": description}), encoding="utf-8"
        )
        with chdir(tmp):
            f = validate_mod.Findings()
            validate_mod.check_workshop_description(f)
            return f.items

    def test_ascii_under_the_limit_passes(self) -> None:
        self.assertEqual(self._findings("a" * 7999), [])

    def test_ascii_over_the_limit_is_reported(self) -> None:
        self.assertTrue(self._findings("a" * 8001))

    def test_multibyte_over_the_limit_is_reported(self) -> None:
        """The real case: comfortably under the limit in characters, over it in bytes."""
        text = "\u2014" * 2700  # 2,700 em dashes = 2,700 chars but 8,100 bytes
        self.assertLess(
            len(text), 8000, "the fixture must be under the limit in CHARACTERS"
        )
        self.assertGreater(len(text.encode("utf-8")), 8000)
        items = self._findings(text)
        self.assertTrue(items, "a description over the byte limit was not reported")
        self.assertIn("8100 bytes", items[0][1])

    def test_multibyte_under_the_limit_passes(self) -> None:
        """The other direction, so the fix cannot be a blanket rejection of non-ASCII."""
        text = "\u2014" * 2600  # 7,800 bytes
        self.assertLessEqual(len(text.encode("utf-8")), 8000)
        self.assertEqual(self._findings(text), [])


class SnapshotCoverage(unittest.TestCase):
    """#507: the snapshot's mod-scoped sections take their keys from the mod, so a mod change can
    outrun them. The digest that noticed needs Caves of Qud installed, so CI skipped it and a stale
    snapshot merged green - twice in one day, each time surfacing as a failure that blocked a
    commit which had not caused it. This check needs no game: both sides are in the repository."""

    def coverage(self, blueprints: str = "", tables: str = "") -> list[tuple[str, str]]:
        tmp = Path(tempfile.mkdtemp())
        write_mod(tmp, blueprints=blueprints, tables=tables)
        return findings_for(validate_mod.check_snapshot_coverage, tmp)

    def test_a_tag_name_the_snapshot_records_is_accepted(self) -> None:
        """BaseObject is in tag_forms, so it is covered and says nothing."""
        self.assertEqual(
            self.coverage('<object Name="T"><tag Name="BaseObject" /></object>'), []
        )

    def test_a_cited_absence_is_accepted(self) -> None:
        """Vixy_CreatureVariant is in tag_forms_absent because vanilla never writes it. A cited
        absence is an answer, which is the whole point of recording one."""
        self.assertEqual(
            self.coverage(
                '<object Name="T"><tag Name="Vixy_CreatureVariant" /></object>'
            ),
            [],
        )

    def test_a_name_in_neither_is_reported(self) -> None:
        """The #486 and #489 case: a tag the snapshot predates, which nothing without the game
        could previously notice."""
        found = self.coverage(
            '<object Name="T"><tag Name="Vixy_BrandNewTag" /></object>'
        )
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][0], "snapshot-coverage")
        self.assertIn("Vixy_BrandNewTag", found[0][1])
        self.assertIn("snapshot_qud_api.py", found[0][1])

    def test_an_stag_is_covered_too(self) -> None:
        """Both elements land in the same dictionary, so both must be checked."""
        found = self.coverage(
            '<object Name="T"><stag Name="Vixy_BrandNewTag" /></object>'
        )
        self.assertEqual(len(found), 1)

    def test_a_repeated_name_is_reported_once(self) -> None:
        """One missing name is one thing to fix, however many blueprints carry it - and this fork
        puts the same tag on dozens."""
        found = self.coverage(
            '<object Name="A"><tag Name="Vixy_BrandNewTag" /></object>'
            '<object Name="B"><tag Name="Vixy_BrandNewTag" /></object>'
        )
        self.assertEqual(len(found), 1)

    def test_a_merged_table_the_snapshot_records_is_accepted(self) -> None:
        """`Ammo 2` is one of the 72 tables this fork merges into, so the snapshot holds vanilla's
        side of it. Note the snapshot's table sections are themselves mod-scoped - a table this
        fork does not merge into has no entry, which is exactly the gap this check closes."""
        found = self.coverage(
            tables='<population Name="Ammo 2" Load="Merge">'
            '<object Blueprint="X" Weight="1" /></population>'
        )
        self.assertEqual(found, [])

    def test_a_merged_table_in_neither_is_reported(self) -> None:
        found = self.coverage(
            tables='<population Name="Vixy_UnknownTable" Load="Merge">'
            '<object Blueprint="X" Weight="1" /></population>'
        )
        self.assertEqual(len(found), 1)
        self.assertIn("Vixy_UnknownTable", found[0][1])

    def test_a_table_this_fork_defines_is_not_a_merge(self) -> None:
        """A table with no Load="Merge" is this fork's own and vanilla has nothing to say about it,
        so demanding a snapshot record would fail every new table."""
        found = self.coverage(
            tables='<population Name="Vixy_MyOwnTable">'
            '<object Blueprint="X" Weight="1" /></population>'
        )
        self.assertEqual(found, [])

    def test_it_says_nothing_without_a_snapshot(self) -> None:
        """A contributor without the snapshot gets silence rather than a wall of false findings -
        the same bargain every other snapshot-backed check makes."""
        tmp = Path(tempfile.mkdtemp())
        mod = write_mod(
            tmp, '<object Name="T"><tag Name="Vixy_BrandNewTag" /></object>'
        )
        (tmp / "tools" / "qud-api.json").unlink()
        self.assertEqual(
            findings_for(validate_mod.check_snapshot_coverage, mod.parent), []
        )


class DirectoryCoverage(unittest.TestCase):
    """#498. Declaring `Directories` changes loading from "everything under mod/" to "these paths
    only", and a path that does not match loads nothing with no error. Both sides are in the
    repository, so this needs no game."""

    def coverage(self, tree: dict, directories) -> list[str]:
        tmp = Path(tempfile.mkdtemp())
        mod = tmp / "mod"
        for rel, body in tree.items():
            target = mod / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
        manifest = {
            "id": "T",
            "title": "T",
            "version": "1.0.0",
            "author": "Mura",
            "description": "d",
        }
        if directories is not None:
            manifest["Directories"] = directories
        (mod / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        with chdir(tmp):
            f = validate_mod.Findings()
            validate_mod.check_directory_coverage(f)
            return [detail for _, detail in f.items]

    TREE: ClassVar = {"Core/A.xml": "<x/>", "Optional/Gated/B.rpm": "<x/>"}
    GOOD: ClassVar = [
        {"Paths": ["Core"]},
        {"Path": "Optional/Gated", "Options": "OptionX==Yes"},
    ]

    def test_a_correct_declaration_is_silent(self) -> None:
        self.assertEqual(self.coverage(self.TREE, self.GOOD), [])

    def test_no_directories_array_is_silent(self) -> None:
        """Without one the game loads the root, so everything is reachable by definition. Silent
        rather than vacuous: this check ships before the restructure it guards."""
        self.assertEqual(self.coverage(self.TREE, None), [])

    def test_a_path_wrong_only_in_case_is_reported(self) -> None:
        """macOS accepts it and Linux does not, so `Path.exists()` cannot be the test - the
        comparison has to be against real directory entries."""
        found = self.coverage(self.TREE, [{"Paths": ["core"]}, self.GOOD[1]])
        self.assertEqual(len(found), 1)
        self.assertIn("exactly that spelling", found[0])

    def test_a_broken_path_does_not_cascade(self) -> None:
        """Every file under a path that does not resolve is unreachable, so sweeping would bury
        the one finding that matters under its own consequences."""
        found = self.coverage(
            {"Core/A.xml": "<x/>", "Core/B.xml": "<x/>", "Core/C.xml": "<x/>"},
            [{"Paths": ["core"]}],
        )
        self.assertEqual(len(found), 1)

    def test_an_entry_containing_another_is_reported(self) -> None:
        """The trap that decides whether gating works at all: the game keeps one of two overlapping
        entries, and the loser's conditions go with it - so a root entry ungates everything."""
        found = self.coverage(
            self.TREE,
            [{"Path": "."}, {"Path": "Optional/Gated", "Options": "OptionX==Yes"}],
        )
        self.assertEqual(len(found), 1)
        self.assertIn("conditions are discarded", found[0])

    def test_an_unreachable_file_is_reported(self) -> None:
        found = self.coverage(self.TREE, [{"Paths": ["Core"]}])
        self.assertEqual(len(found), 1)
        self.assertIn("B.rpm", found[0])

    def test_manifest_files_are_not_content(self) -> None:
        """workshop.json and the preview are read by the mod manager, not loaded as content, so
        they sit outside every declared path by design."""
        tree = dict(self.TREE, **{"workshop.json": "{}", "preview.png": "x"})
        self.assertEqual(self.coverage(tree, self.GOOD), [])

    def test_the_shorthand_and_the_array_are_both_accepted(self) -> None:
        """`Path` and `Paths` are mutually exclusive in a manifest but both are legal, and reading
        only one would pass a manifest this check never looked at."""
        self.assertEqual(
            self.coverage(self.TREE, [{"Path": "Core"}, {"Path": "Optional/Gated"}]), []
        )


class MapId(unittest.TestCase):
    """#498. A map with no ID is keyed by its path, so moving the file silently stops it patching
    anything - no error, every check green, and content simply absent from the world."""

    def maps(self, body: str) -> list[str]:
        tmp = Path(tempfile.mkdtemp())
        target = tmp / "mod" / "Optional" / "Thing" / "Joppa.rpm"
        target.parent.mkdir(parents=True)
        target.write_text(body, encoding="utf-8")
        with chdir(tmp):
            f = validate_mod.Findings()
            validate_mod.check_map_id(f)
            return [detail for _, detail in f.items]

    def test_a_map_with_an_id_is_accepted(self) -> None:
        self.assertEqual(
            self.maps('<Map ID="Joppa.rpm" Load="Merge"><cell /></Map>'), []
        )

    def test_a_map_without_one_is_reported(self) -> None:
        found = self.maps('<Map Load="Merge"><cell /></Map>')
        self.assertEqual(len(found), 1)
        self.assertIn("keys it by its path", found[0])

    def test_an_empty_id_does_not_count(self) -> None:
        """An attribute present but blank falls back to the path exactly as an absent one does."""
        self.assertEqual(len(self.maps('<Map ID="" Load="Merge"><cell /></Map>')), 1)


if __name__ == "__main__":
    unittest.main()


class TierResolution(unittest.TestCase):
    """`item-curve` must find a tier from the Tier tag, not only from a material word.

    Every test here is a positive control in one direction or the other, for the reason this
    file's docstring gives: the failure mode being fixed is a **skip**, and a check that skips
    an object is indistinguishable from a check that approved it. #354 is 144 chips that sat
    twenty times under the curve for exactly that reason.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _curve(self, blueprints: str) -> list[tuple[str, str]]:
        tmp = Path(tempfile.mkdtemp(dir=self.tmp))
        write_mod(tmp, blueprints)
        return findings_for(validate_mod.check_item_curves, tmp)

    def test_tier_tag_alone_is_enough_to_price_an_object(self) -> None:
        """The defect #354 reports. No material word, an explicit tier, a wrong price."""
        items = self._curve(
            '  <object Name="Vixy_Widget">\n'
            '    <part Name="Commerce" Value="7" />\n'
            '    <tag Name="Tier" Value="3" />\n'
            "  </object>"
        )
        self.assertTrue(
            items, "an object with a Tier tag and no material was not priced"
        )
        self.assertIn("40", items[0][1], "tier 3 should price at 5 * 2^3")

    def test_tier_tag_alone_stays_quiet_when_the_price_is_right(self) -> None:
        """The other half of the control. Without this the test above passes on a check that
        reports everything."""
        self.assertEqual(
            self._curve(
                '  <object Name="Vixy_Widget">\n'
                '    <part Name="Commerce" Value="40" />\n'
                '    <tag Name="Tier" Value="3" />\n'
                "  </object>"
            ),
            [],
        )

    def test_material_word_still_works_without_a_tag(self) -> None:
        """The fallback has to survive. Objects that predate the Tier tag rely on it."""
        items = self._curve(
            '  <object Name="Vixy_Carbide Widget">\n'
            '    <part Name="Commerce" Value="7" />\n'
            "  </object>"
        )
        self.assertTrue(
            items, "a material-named object lost its tier when the tag was preferred"
        )

    def test_a_name_disagreeing_with_its_tag_is_reported(self) -> None:
        """The Flawless Crysteel Boots defect from #9, which must survive the reordering."""
        items = self._curve(
            '  <object Name="Vixy_Carbide Widget">\n'
            '    <part Name="Commerce" Value="1280" />\n'
            '    <tag Name="Tier" Value="8" />\n'
            "  </object>"
        )
        self.assertTrue(any("by material" in d for _, d in items))

    def test_chips_are_priced_on_the_chip_curve(self) -> None:
        """A chip at the item curve's price is wrong; §3.2.1 puts them at a quarter of it."""
        chip = (
            '  <object Name="Vixy_Test Chip" Inherits="Raven_Base Psionic Chip">\n'
            '    <part Name="Commerce" Value="{}" />\n'
            '    <tag Name="Tier" Value="8" />\n'
            "  </object>"
        )
        self.assertEqual(
            self._curve(chip.format(320)), [], "320 is the tier-8 chip curve"
        )
        items = self._curve(chip.format(1280))
        self.assertTrue(items, "a chip priced on the item curve was not reported")
        self.assertIn("chip curve", items[0][1])

    def test_base_objects_are_not_priced(self) -> None:
        """A base is a template. Nothing spawns one, so its price means nothing.

        Only reachable once tier stopped depending on a material word: Raven_Base Psionic Pistol
        carries Tier 3 and names no metal, so it was invisible here by accident rather than by
        rule.
        """
        self.assertEqual(
            self._curve(
                '  <object Name="Vixy_Base Widget">\n'
                '    <part Name="Commerce" Value="7" />\n'
                '    <tag Name="Tier" Value="3" />\n'
                '    <tag Name="BaseObject" Value="*noinherit" />\n'
                "  </object>"
            ),
            [],
        )


class CurveChecks(unittest.TestCase):
    """The checks #337 asked for, each proven in both directions.

    A check is only proven by watching it fire on something broken AND stay quiet on something
    sound. That is this file's house rule and it earns its keep here: every one of these guards a
    rule that had no enforcement while twenty findings accumulated behind it.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _run(self, check, blueprints: str) -> list[tuple[str, str]]:
        tmp = Path(tempfile.mkdtemp(dir=self.tmp))
        write_mod(tmp, blueprints)
        return findings_for(check, tmp)

    # ----------------------------------------------------------------- stat-discipline

    def test_new_weapon_on_agility_is_reported(self) -> None:
        items = self._run(
            validate_mod.check_stat_discipline,
            '  <object Name="Vixy_Blade">\n'
            '    <part Name="MeleeWeapon" Stat="Agility" />\n'
            "  </object>",
        )
        self.assertTrue(items, "a new weapon on Agility was not reported")
        self.assertEqual(items[0][0], "stat-discipline")

    def test_new_weapon_may_leave_stat_unset(self) -> None:
        """MeleeWeapon.Stat is initialised to "Strength" and vanilla omits it on 208 of 402
        declarations. Requiring it would report 28 correct weapons."""
        self.assertEqual(
            self._run(
                validate_mod.check_stat_discipline,
                '  <object Name="Vixy_Blade">\n'
                '    <part Name="MeleeWeapon" BaseDamage="1d4" />\n'
                "  </object>",
            ),
            [],
        )

    def test_merge_stating_any_stat_is_reported(self) -> None:
        """Stricter than the new-weapon half on purpose: CI has no game, so it cannot tell a merge
        that restates vanilla's value from one that changes it, and the second is the defect."""
        items = self._run(
            validate_mod.check_stat_discipline,
            '  <object Name="Dagger3" Load="Merge">\n'
            '    <part Name="MeleeWeapon" Stat="Strength" />\n'
            "  </object>",
        )
        self.assertTrue(items, "a merge asserting a Stat was not reported")

    def test_merge_without_a_stat_is_not_reported(self) -> None:
        self.assertEqual(
            self._run(
                validate_mod.check_stat_discipline,
                '  <object Name="Dagger3" Load="Merge">\n'
                '    <part Name="MeleeWeapon" BaseDamage="1d6" />\n'
                "  </object>",
            ),
            [],
        )

    # --------------------------------------------------------------------- armor-curve

    def test_armor_over_its_slot_ceiling_is_reported(self) -> None:
        items = self._run(
            validate_mod.check_armor_curve,
            '  <object Name="Vixy_Bracer">\n'
            '    <part Name="Armor" WornOn="Arm" AV="3" />\n'
            "  </object>",
        )
        self.assertTrue(
            items, "AV 3 in the Arm slot was not reported against a ceiling of 1"
        )

    def test_armor_at_its_slot_ceiling_is_not_reported(self) -> None:
        """The boundary. A ceiling is a maximum, not a limit to stay under."""
        self.assertEqual(
            self._run(
                validate_mod.check_armor_curve,
                '  <object Name="Vixy_Plate">\n'
                '    <part Name="Armor" WornOn="Body" AV="8" />\n'
                "  </object>",
            ),
            [],
        )

    def test_shield_av_is_checked_against_the_shield_ceiling(self) -> None:
        """Shields carry AV on a Shield part, not an Armor one. A survey filtered on Armor misses
        all fourteen of vanilla's, which is how 3.2.1 first shipped without a Shield column."""
        items = self._run(
            validate_mod.check_armor_curve,
            '  <object Name="Vixy_Aegis">\n'
            '    <part Name="Shield" AV="10" />\n'
            '    <tag Name="Tier" Value="8" />\n'
            "  </object>",
        )
        self.assertTrue(items, "a Shield part's AV was not checked")
        self.assertIn("Shield (tier 8)", items[0][1])

    def test_the_shield_ceiling_is_per_tier(self) -> None:
        """A single per-slot number would let a low-tier greatshield pass at the tier-8 ceiling.

        AV 9 is exactly right at tier 8 and three over at tier 2, and the check has to tell those
        apart - vanilla's shield line is AV = tier + 1 up to tier 3 and AV = tier from tier 5, so
        there is no one number for the slot.
        """
        shield = (
            '  <object Name="Vixy_Aegis">\n'
            '    <part Name="Shield" AV="9" />\n'
            '    <tag Name="Tier" Value="{}" />\n'
            "  </object>"
        )
        self.assertEqual(
            self._run(validate_mod.check_armor_curve, shield.format(8)), []
        )
        self.assertTrue(
            self._run(validate_mod.check_armor_curve, shield.format(2)),
            "AV 9 at tier 2 passed a ceiling meant for tier 8",
        )

    def test_base_objects_are_not_held_to_the_ceiling(self) -> None:
        self.assertEqual(
            self._run(
                validate_mod.check_armor_curve,
                '  <object Name="Vixy_Base Plate">\n'
                '    <part Name="Armor" WornOn="Arm" AV="3" />\n'
                '    <tag Name="BaseObject" Value="*noinherit" />\n'
                "  </object>",
            ),
            [],
        )

    # ---------------------------------------------------------------- finesse-visible

    def test_finesse_tag_without_the_text_is_reported(self) -> None:
        """How #366 was found: the tag has no player-facing surface, so a silent feature and a
        broken one look identical from the item screen."""
        items = self._run(
            validate_mod.check_finesse_visible,
            '  <object Name="Vixy_Rapier">\n    <tag Name="Finesse" />\n  </object>',
        )
        self.assertTrue(items, "a Finesse tag with no rules text was not reported")

    def test_finesse_text_without_the_tag_is_reported(self) -> None:
        """The other direction, which is a different mistake: a promise the game does not keep."""
        items = self._run(
            validate_mod.check_finesse_visible,
            '  <object Name="Vixy_Rapier">\n'
            '    <part Name="RulesDescription" Text="Finesse: uses Agility." />\n'
            "  </object>",
        )
        self.assertTrue(items, "finesse rules text with no tag was not reported")

    def test_finesse_tag_with_the_text_is_not_reported(self) -> None:
        self.assertEqual(
            self._run(
                validate_mod.check_finesse_visible,
                '  <object Name="Vixy_Rapier">\n'
                '    <tag Name="Finesse" />\n'
                '    <part Name="RulesDescription" Text="Finesse: uses Agility." />\n'
                "  </object>",
            ),
            [],
        )

    def test_a_deleted_finesse_tag_needs_no_text(self) -> None:
        """`Value="*delete"` removes an inherited tag. The vibro wristblade uses it, because
        MaxStrengthBonus 0 makes finesse unreachable there."""
        self.assertEqual(
            self._run(
                validate_mod.check_finesse_visible,
                '  <object Name="Vixy_Vibro Blade">\n'
                '    <tag Name="Finesse" Value="*delete" />\n'
                "  </object>",
            ),
            [],
        )


class SnapshotBackedChecks(unittest.TestCase):
    """The three checks that need vanilla's side, which CI does not have.

    Each reads `merged_records` or `table_weights` from tools/qud-api.json. The fixtures write
    their own snapshot rather than leaning on the committed one, so a test cannot start passing
    because vanilla changed.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _mod(
        self, blueprints: str = "", tables: str = "", snapshot: dict | None = None
    ) -> Path:
        tmp = Path(tempfile.mkdtemp(dir=self.tmp))
        write_mod(tmp, blueprints, tables)
        api = json.loads((tmp / "tools" / "qud-api.json").read_text())
        api.update(snapshot or {})
        (tmp / "tools" / "qud-api.json").write_text(json.dumps(api))
        return tmp

    # ---------------------------------------------------------------------- merge-value

    RECORD: ClassVar[dict] = {
        "tier": "8",
        "value": "6000",
        "resistances": {"Heat": "11"},
    }

    def _merge_value(self, blueprints: str, record: dict | None = None):
        tmp = self._mod(
            blueprints,
            snapshot={"merged_records": {"Zetachrome Lune": record or self.RECORD}},
        )
        return findings_for(validate_mod.check_merged_value, tmp)

    def test_a_merge_repricing_vanilla_is_reported(self) -> None:
        """#380. 142 of the 213 merges carried a price this fork had rewritten, and item-curve
        could not see one of them - it prices only the mod's own objects."""
        items = self._merge_value(
            '  <object Name="Zetachrome Lune" Load="Merge">\n'
            '    <part Name="Commerce" Value="2048" />\n'
            '    <tag Name="Tier" Value="8" />\n'
            "  </object>"
        )
        self.assertEqual([c for c, _ in items], ["merge-value"])
        self.assertIn("vanilla prices it 6000", items[0][1])

    def test_a_merge_restating_vanillas_price_passes(self) -> None:
        """Restating a value changes nothing by definition, so it is not the defect."""
        self.assertEqual(
            self._merge_value(
                '  <object Name="Zetachrome Lune" Load="Merge">\n'
                '    <part Name="Commerce" Value="6000" />\n'
                "  </object>"
            ),
            [],
        )

    def test_a_merge_that_re_tiers_may_reprice(self) -> None:
        """The exception, and the reason the check is not simply 'never'. Carbide Boots is tier 3
        at 40 against vanilla's tier 4 at 150 - the curve doing its job on a tier this fork chose."""
        self.assertEqual(
            self._merge_value(
                '  <object Name="Zetachrome Lune" Load="Merge">\n'
                '    <part Name="Commerce" Value="2048" />\n'
                '    <tag Name="Tier" Value="6" />\n'
                "  </object>"
            ),
            [],
        )

    def test_a_new_object_is_not_touched(self) -> None:
        """The curve still governs everything this fork adds; only merges are held to vanilla."""
        self.assertEqual(
            self._merge_value(
                '  <object Name="Zetachrome Lune">\n'
                '    <part Name="Commerce" Value="2048" />\n'
                "  </object>"
            ),
            [],
        )

    def test_a_merge_changing_a_resistance_is_reported(self) -> None:
        items = self._merge_value(
            '  <object Name="Zetachrome Lune" Load="Merge">\n'
            '    <part Name="Armor" Heat="10" />\n'
            "  </object>"
        )
        self.assertEqual([c for c, _ in items], ["merge-value"])
        self.assertIn("vanilla says 11", items[0][1])

    def test_a_merge_inventing_a_resistance_is_reported(self) -> None:
        """Vanilla states none, so there is nothing to restate - and no curve to derive it from."""
        items = self._merge_value(
            '  <object Name="Zetachrome Lune" Load="Merge">\n'
            '    <part Name="Armor" Cold="5" />\n'
            "  </object>"
        )
        self.assertEqual([c for c, _ in items], ["merge-value"])
        self.assertIn("vanilla says nothing", items[0][1])

    def test_a_merge_restating_a_resistance_passes(self) -> None:
        self.assertEqual(
            self._merge_value(
                '  <object Name="Zetachrome Lune" Load="Merge">\n'
                '    <part Name="Armor" Heat="11" />\n'
                "  </object>"
            ),
            [],
        )

    def test_a_re_tier_does_not_licence_a_resistance(self) -> None:
        """The exception is for price only. Re-tiering derives a new price; it derives nothing
        about a resistance, because no curve describes one."""
        items = self._merge_value(
            '  <object Name="Zetachrome Lune" Load="Merge">\n'
            '    <part Name="Armor" Heat="10" />\n'
            '    <tag Name="Tier" Value="6" />\n'
            "  </object>"
        )
        self.assertEqual([c for c, _ in items], ["merge-value"])

    def test_a_merge_vanilla_never_priced_is_left_alone(self) -> None:
        """`None` means vanilla states no value, so there is nothing to contradict."""
        self.assertEqual(
            self._merge_value(
                '  <object Name="Zetachrome Lune" Load="Merge">\n'
                '    <part Name="Commerce" Value="2048" />\n'
                "  </object>",
                record={"tier": "8", "value": None, "resistances": None},
            ),
            [],
        )

    def test_the_committed_snapshot_carries_vanillas_prices(self) -> None:
        """Guards against a vacuous pass: without `value` on the records the check returns nothing
        to compare and every test above would still pass."""
        api = json.loads(API_SNAPSHOT.read_text())
        records = api["merged_records"]
        self.assertEqual(records["Zetachrome Lune"]["value"], "6000")
        self.assertEqual(records["Zetachrome Lune"]["resistances"]["Heat"], "11")
        self.assertTrue(
            all(r.get("value") for r in records.values()),
            "every merged record should carry vanilla's price",
        )

    # ------------------------------------------------------------------ damage-ceiling

    def test_a_merge_over_its_family_ceiling_is_reported(self) -> None:
        """The #322 defect. A merge names no Skill, so only the snapshot can say it is a cudgel."""
        tmp = self._mod(
            '  <object Name="Cudgel8th" Load="Merge">\n'
            '    <part Name="MeleeWeapon" BaseDamage="5d6+2" />\n'
            "  </object>",
            snapshot={
                "merged_records": {
                    "Cudgel8th": {"skill": "Cudgel", "two_handed": True, "tier": "8"}
                }
            },
        )
        items = findings_for(validate_mod.check_damage_ceiling, tmp)
        self.assertTrue(items, "a merge over the damage ceiling was not reported")
        self.assertIn("19.5", items[0][1])

    def test_a_merge_on_its_family_ceiling_is_not_reported(self) -> None:
        tmp = self._mod(
            '  <object Name="Cudgel8th" Load="Merge">\n'
            '    <part Name="MeleeWeapon" BaseDamage="4d6" />\n'
            "  </object>",
            snapshot={
                "merged_records": {
                    "Cudgel8th": {"skill": "Cudgel", "two_handed": True, "tier": "8"}
                }
            },
        )
        self.assertEqual(findings_for(validate_mod.check_damage_ceiling, tmp), [])

    def test_damage_is_not_checked_without_a_snapshot(self) -> None:
        """The one silence worth naming. A snapshot predating these keys cannot tell "nothing
        wrong" from "nothing checked", which is why the tool says to regenerate after an update."""
        tmp = self._mod(
            '  <object Name="Cudgel8th" Load="Merge">\n'
            '    <part Name="MeleeWeapon" BaseDamage="99d99" />\n'
            "  </object>",
            snapshot={"merged_records": {}},
        )
        self.assertEqual(findings_for(validate_mod.check_damage_ceiling, tmp), [])

    def test_a_merge_that_states_no_damage_is_not_checked(self) -> None:
        """Changing an item's weight is not a claim about its damage."""
        tmp = self._mod(
            '  <object Name="Cudgel8th" Load="Merge">\n'
            '    <part Name="Physics" Weight="6" />\n'
            "  </object>",
            snapshot={
                "merged_records": {
                    "Cudgel8th": {"skill": "Cudgel", "two_handed": True, "tier": "8"}
                }
            },
        )
        self.assertEqual(findings_for(validate_mod.check_damage_ceiling, tmp), [])

    # -------------------------------------------------------------------- weight-curve

    def test_a_merge_made_heavier_is_reported(self) -> None:
        tmp = self._mod(
            '  <object Name="Dagger3" Load="Merge">\n'
            '    <part Name="Physics" Weight="2" />\n'
            "  </object>",
            snapshot={"merged_records": {"Dagger3": {"weight": "1"}}},
        )
        items = findings_for(validate_mod.check_weight_curve, tmp)
        self.assertTrue(items, "an item made heavier than vanilla was not reported")

    def test_a_merge_made_lighter_is_not_reported(self) -> None:
        """Lighter is the whole point of the compression. Only the direction is checked."""
        tmp = self._mod(
            '  <object Name="Dagger3" Load="Merge">\n'
            '    <part Name="Physics" Weight="1" />\n'
            "  </object>",
            snapshot={"merged_records": {"Dagger3": {"weight": "3"}}},
        )
        self.assertEqual(findings_for(validate_mod.check_weight_curve, tmp), [])

    # --------------------------------------------------------------------- table-share

    def test_a_table_over_half_is_reported(self) -> None:
        tmp = self._mod(
            "",
            tables='  <population Name="Armor 4C" Load="Merge">\n'
            '    <object Blueprint="Vixy_Thing" Weight="200" />\n'
            "  </population>",
            snapshot={"table_weights": {"Armor 4C": 100}},
        )
        items = findings_for(validate_mod.check_table_share, tmp)
        self.assertTrue(items, "a table past half was not reported")
        self.assertIn("66.7%", items[0][1])

    def test_a_table_at_half_is_not_reported(self) -> None:
        tmp = self._mod(
            "",
            tables='  <population Name="Armor 4C" Load="Merge">\n'
            '    <object Blueprint="Vixy_Thing" Weight="100" />\n'
            "  </population>",
            snapshot={"table_weights": {"Armor 4C": 100}},
        )
        self.assertEqual(findings_for(validate_mod.check_table_share, tmp), [])

    def test_this_forks_own_table_is_not_checked(self) -> None:
        """A table with no vanilla entry has nothing to be half of."""
        tmp = self._mod(
            "",
            tables='  <population Name="Raven_Chips Tier 1">\n'
            '    <object Blueprint="Vixy_Chip" Weight="999" />\n'
            "  </population>",
            snapshot={"table_weights": {"Armor 4C": 100}},
        )
        self.assertEqual(findings_for(validate_mod.check_table_share, tmp), [])

    # ----------------------------------------------------------------------- tag-form

    FORMS: ClassVar[dict] = {"tag_forms": {"Floating": "stag", "Tier": "tag"}}

    def _tag_form(self, blueprints: str, forms: dict | None = None):
        tmp = self._mod(blueprints, snapshot=forms if forms is not None else self.FORMS)
        return findings_for(validate_mod.check_tag_form, tmp)

    def test_a_stag_written_as_a_tag_is_reported(self) -> None:
        """#478, verbatim: the shape #50 introduced believing it was removing one."""
        items = self._tag_form(
            '  <object Name="Vixy_Sled">\n    <tag Name="Floating" />\n  </object>'
        )
        self.assertTrue(items, "a tag on the wrong key was not reported")
        self.assertEqual(items[0][0], "tag-form")
        self.assertIn("'Floating'", items[0][1])
        self.assertIn("'SemanticFloating'", items[0][1])

    def test_a_tag_written_as_a_stag_is_reported(self) -> None:
        """The other direction, which is the likelier mistake now that stag is understood."""
        items = self._tag_form(
            '  <object Name="Vixy_Thing">\n    <stag Name="Tier" Value="4" />\n  </object>'
        )
        self.assertTrue(items)
        self.assertIn("'SemanticTier'", items[0][1])

    def test_matching_vanillas_form_is_quiet(self) -> None:
        self.assertEqual(
            self._tag_form(
                '  <object Name="Vixy_Sled">\n    <stag Name="Floating" />\n  </object>'
            ),
            [],
        )
        self.assertEqual(
            self._tag_form(
                '  <object Name="Vixy_Thing">\n    <tag Name="Tier" Value="4" />\n  </object>'
            ),
            [],
        )

    def test_a_name_vanilla_never_writes_carries_no_opinion(self) -> None:
        """Vixy_CreatureVariant is read only by this mod's own C#, so nothing can judge it."""
        self.assertEqual(
            self._tag_form(
                '  <object Name="Vixy_Goat">\n'
                '    <stag Name="Vixy_CreatureVariant" />\n'
                "  </object>"
            ),
            [],
        )

    def test_a_name_vanilla_writes_both_ways_carries_no_opinion(self) -> None:
        """Four of them, Fiber among them. The snapshot omits an ambiguous name entirely."""
        self.assertEqual(
            self._tag_form(
                '  <object Name="Vixy_Reed">\n    <tag Name="Fiber" Value="rope" />\n  </object>'
            ),
            [],
        )

    def test_a_snapshot_without_the_key_checks_nothing(self) -> None:
        """The vacuous case: silence here must mean "no opinion", not "nothing looked"."""
        self.assertEqual(
            self._tag_form(
                '  <object Name="Vixy_Sled">\n    <tag Name="Floating" />\n  </object>',
                forms={"tag_forms": {}},
            ),
            [],
        )

    # ------------------------------------------------------------------- scatter-share

    def _scatter(self, entries: str, name: str = "SaltMarshZoneGlobals", snapshot=None):
        if snapshot is None:
            snapshot = {"scatter_quantities": {"SaltMarshZoneGlobals": 10.0}}
        tmp = self._mod(
            "",
            tables=f'  <population Name="{name}" Load="Merge">\n{entries}  </population>',
            snapshot=snapshot,
        )
        return findings_for(validate_mod.check_scatter_share, tmp)

    def test_a_chance_number_entry_is_counted_at_all(self) -> None:
        """The regression #474 exists for.

        Every biome-globals table scatters by Chance and Number and carries no Weight, so
        table-share's summed weight read this fork's side as 0 and could not fail however much was
        added. Six merge blocks sat in that hole, the creature variants among them.
        """
        items = self._scatter(
            '    <object Blueprint="Vixy_Thing" Chance="50" Number="60" />\n'
        )
        self.assertTrue(items, "a Chance/Number entry still counts for nothing")
        self.assertEqual(items[0][0], "scatter-share")
        self.assertIn("30.0 expected", items[0][1])

    def test_under_half_is_quiet(self) -> None:
        self.assertEqual(
            self._scatter(
                '    <object Blueprint="Vixy_Thing" Chance="50" Number="10" />\n'
            ),
            [],
        )

    def test_chance_scales_the_quantity(self) -> None:
        """25% of 40 is 10, which ties vanilla's 10 and must not fire."""
        self.assertEqual(
            self._scatter(
                '    <object Blueprint="Vixy_Thing" Chance="25" Number="40" />\n'
            ),
            [],
        )

    def test_a_weighted_entry_is_left_to_table_share(self) -> None:
        """The half this check must not touch, or #474's fix regresses 13 working tables.

        A merge block carries no Style, so a weighted entry cannot be told from its group here -
        but it does not have to be. Vanilla's pickone children all carry Weight and its pickeach
        children never do, so 'has a Weight' identifies the other check's business exactly.
        """
        self.assertEqual(
            self._scatter('    <object Blueprint="Vixy_Thing" Weight="9999" />\n'), []
        )

    def test_a_table_vanilla_does_not_define_is_named_as_such(self) -> None:
        """#476. Distinct from a stale snapshot, and wanting the opposite response."""
        items = self._scatter(
            '    <object Blueprint="Vixy_Thing" Chance="100" Number="2" />\n',
            name="GoneTable",
            snapshot={
                "scatter_quantities": {"SaltMarshZoneGlobals": 10.0},
                "absent_tables": ["GoneTable"],
            },
        )
        self.assertTrue(items)
        self.assertIn("vanilla does not define GoneTable", items[0][1])

    def test_a_table_the_snapshot_has_never_seen_is_reported_not_skipped(self) -> None:
        """table-share skips these in silence, which is how #476 stayed invisible."""
        items = self._scatter(
            '    <object Blueprint="Vixy_Thing" Chance="100" Number="2" />\n',
            name="BrandNewTable",
        )
        self.assertTrue(items, "an unseen table was skipped rather than reported")
        self.assertIn("not in the snapshot", items[0][1])

    def test_a_snapshot_without_the_key_checks_nothing_and_says_nothing(self) -> None:
        """The vacuous case, stated rather than assumed: zero checked is not zero problems.

        A snapshot predating this key cannot tell "nothing wrong" from "nothing checked", so the
        check returns early rather than guessing - and this pins that it stays silent even with
        999 objects in front of it.
        """
        self.assertEqual(
            self._scatter(
                '    <object Blueprint="Vixy_Thing" Chance="100" Number="999" />\n',
                snapshot={"scatter_quantities": {}, "absent_tables": []},
            ),
            [],
        )

    def test_number_midpoint_reads_every_form_vanilla_writes(self) -> None:
        for raw, expected in {
            None: 1.0,
            "": 1.0,
            "3": 3.0,
            "2-8": 5.0,
            "2d6": 7.0,
            "1d4+15": 17.5,
        }.items():
            self.assertEqual(
                validate_mod.number_midpoint(raw), expected, f"Number={raw!r}"
            )

    def test_an_unrecognised_number_understates_rather_than_erases(self) -> None:
        """1, not 0 - a form nobody anticipated must not delete the entry from the ratio."""
        self.assertEqual(validate_mod.number_midpoint("2d6-1d3"), 1.0)

    # -------------------------------------------------------------- implant-table-cost

    def _implant(self, cost: str, table: str) -> Path:
        return self._mod(
            f'  <object Name="Raven_Plating" Inherits="BaseCyberneticsEquipment_1point">\n'
            f'    <part Name="CyberneticsBaseItem" Slots="Body" Cost="{cost}" />\n'
            "  </object>",
            tables=f'  <population Name="{table}" Load="Merge">\n'
            '    <object Blueprint="Raven_Plating" Number="1" Weight="1" />\n'
            "  </population>",
        )

    def test_an_implant_above_its_brackets_ceiling_is_reported(self) -> None:
        """#418: crysteel plating went 3 points to 6 and stayed in the 3-point table."""
        items = findings_for(
            validate_mod.check_implant_table_cost,
            self._implant("6", "Implants_3Pointers"),
        )
        self.assertTrue(items, "an implant priced above its table was not reported")
        self.assertIn("Raven_Plating", items[0][1])

    def test_an_implant_below_its_brackets_floor_is_reported(self) -> None:
        items = findings_for(
            validate_mod.check_implant_table_cost,
            self._implant("2", "Implants_4PlusPointers"),
        )
        self.assertTrue(items, "an implant priced below its table was not reported")

    def test_an_implant_inside_its_bracket_is_not_reported(self) -> None:
        for cost, table in (
            ("1", "Implants_1and2Pointers"),
            ("2", "Implants_1and2Pointers"),
            ("3", "Implants_3Pointers"),
            ("9", "Implants_4PlusPointers"),
        ):
            with self.subTest(cost=cost, table=table):
                self.assertEqual(
                    findings_for(
                        validate_mod.check_implant_table_cost,
                        self._implant(cost, table),
                    ),
                    [],
                )

    def test_a_blueprint_this_fork_does_not_define_is_not_checked(self) -> None:
        """Vanilla's own placements are vanilla's to be wrong about."""
        tmp = self._mod(
            "",
            tables='  <population Name="Implants_3Pointers" Load="Merge">\n'
            '    <object Blueprint="OpticalMultiscanner" Number="1" Weight="1" />\n'
            "  </population>",
        )
        self.assertEqual(findings_for(validate_mod.check_implant_table_cost, tmp), [])

    def test_a_table_outside_the_three_brackets_is_not_checked(self) -> None:
        items = findings_for(
            validate_mod.check_implant_table_cost,
            self._implant("6", "Raven_Chips Tier 1"),
        )
        self.assertEqual(items, [])

    # ---------------------------------------------------------- skill-option-coverage

    def _coverage(
        self, power: str, options: str = "", snapshot: dict | None = None
    ) -> list[tuple[str, str]]:
        tmp = self._mod(
            "",
            snapshot={
                "skill_powers": _VANILLA_TINKER3 if snapshot is None else snapshot
            },
        )
        (tmp / "mod" / "Core").mkdir(parents=True, exist_ok=True)
        (tmp / "mod" / "Core" / "Skills.xml").write_text(
            '<?xml version="1.0" encoding="utf-8" ?>\n<skills>\n'
            '  <skill Name="Tinkering" Load="Merge">\n'
            f"    {power}\n"
            "  </skill>\n</skills>\n",
            encoding="utf-8",
        )
        scripting = tmp / "mod" / "Scripting"
        scripting.mkdir(parents=True, exist_ok=True)
        (scripting / "Raven_Options.cs").write_text(options, encoding="utf-8")
        with chdir(tmp):
            f = validate_mod.Findings()
            validate_mod.check_skill_option_coverage(f)
        return f.items

    def test_a_changed_power_no_option_restores_is_reported(self) -> None:
        """#421: the cut stayed in Skills.xml after the option governing it was removed."""
        items = self._coverage('<power Name="Tinker III" Minimum="25" />')
        self.assertTrue(items, "a change no option restores was not reported")
        self.assertIn("Minimum", items[0][1])

    def test_a_changed_power_an_option_restores_is_not_reported(self) -> None:
        self.assertEqual(
            self._coverage(
                '<power Name="Tinker III" Minimum="25" />',
                options='new PowerRequirement("Tinkering", "Tinker III", A, B),',
            ),
            [],
        )

    def test_an_option_entry_restoring_nothing_is_reported(self) -> None:
        """The other direction: a table entry whose value already matches vanilla."""
        items = self._coverage(
            '<power Name="Tinker III" Minimum="29" />',
            options='new PowerCost("Tinkering", "Tinker III", new Tuning<int>(1, 1)),',
        )
        self.assertTrue(items, "an option restoring nothing was not reported")
        self.assertIn("restores nothing", items[0][1])

    def test_a_power_matching_vanilla_is_not_reported(self) -> None:
        self.assertEqual(
            self._coverage('<power Name="Tinker III" Minimum="29" Tile="x.png" />'), []
        )

    def test_a_power_vanilla_does_not_have_is_not_checked(self) -> None:
        """This fork's own additions - the four Finesse powers - merge nothing."""
        self.assertEqual(
            self._coverage('<power Name="Finesse" Cost="100" Minimum="1" />'), []
        )

    def test_without_the_snapshot_key_the_check_stays_quiet(self) -> None:
        """A snapshot predating skill_powers cannot tell 'nothing wrong' from 'nothing checked'."""
        self.assertEqual(
            self._coverage('<power Name="Tinker III" Minimum="25" />', snapshot={}), []
        )


class CurveExemptions(unittest.TestCase):
    """The categories the value curve does not describe, and the ones it does.

    Each exemption is a hole in `item-curve`, so each needs a control proving the hole is the
    shape it claims: the exempt category stays quiet, and an ordinary item in the same tier still
    fires. Without the second half an exemption that matched everything would look like a pass.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _curve(self, body: str) -> list[tuple[str, str]]:
        tmp = Path(tempfile.mkdtemp(dir=self.tmp))
        write_mod(tmp, body)
        return findings_for(validate_mod.check_item_curves, tmp)

    def _obj(self, extra: str, value: int = 7, tier: int = 3) -> str:
        return (
            '  <object Name="Vixy_Thing">\n'
            f'    <part Name="Commerce" Value="{value}" />\n'
            f"{extra}"
            f'    <tag Name="Tier" Value="{tier}" />\n'
            "  </object>"
        )

    def test_an_ordinary_item_off_the_curve_still_fires(self) -> None:
        """The control every case below is measured against."""
        self.assertTrue(
            self._curve(self._obj("")), "a mispriced ordinary item was not reported"
        )

    def test_ranged_weapons_are_exempt(self) -> None:
        """0 of 5 in this mod have ever been on the curve, and 0 of vanilla's 64."""
        self.assertEqual(
            self._curve(self._obj('    <part Name="MissileWeapon" />\n')), []
        )

    def test_energy_cells_are_exempt(self) -> None:
        self.assertEqual(self._curve(self._obj('    <part Name="EnergyCell" />\n')), [])

    def test_containers_are_exempt(self) -> None:
        self.assertEqual(self._curve(self._obj('    <part Name="Backpack" />\n')), [])

    def test_food_is_exempt(self) -> None:
        """0 of vanilla's 32 tiered, priced edibles sit on the curve (#177)."""
        self.assertEqual(self._curve(self._obj('    <part Name="Food" />\n')), [])

    def test_prepared_cooking_ingredients_are_exempt(self) -> None:
        """A preserved ingredient carries no Food part, only the cooking one."""
        self.assertEqual(
            self._curve(self._obj('    <part Name="PreparedCookingIngredient" />\n')),
            [],
        )

    def test_trinkets_are_exempt(self) -> None:
        self.assertEqual(
            self._curve(
                '  <object Name="Vixy_Thing">\n'
                '    <part Name="Commerce" Value="7" />\n'
                '    <tag Name="Trinket" />\n'
                '    <tag Name="Tier" Value="3" />\n'
                "  </object>"
            ),
            [],
        )

    def test_a_trinket_marked_the_way_vanilla_marks_one_is_exempt(self) -> None:
        """#478. Vanilla writes Trinket as <stag>, and reverting #50 made this fork's sphere of
        negative weight match. A reader knowing only <tag> would have stopped exempting it in
        the same commit that corrected the blueprint - turning a fix into a false price of 100
        against a curve of 1280, reported as a defect in the item rather than in the check."""
        self.assertEqual(
            self._curve(
                '  <object Name="Vixy_Thing">\n'
                '    <part Name="Commerce" Value="7" />\n'
                '    <stag Name="Trinket" />\n'
                '    <tag Name="Tier" Value="3" />\n'
                "  </object>"
            ),
            [],
        )

    def test_armour_granting_no_av_is_exempt(self) -> None:
        """A slot occupier rather than armour — the curve prices protection."""
        self.assertEqual(
            self._curve(self._obj('    <part Name="Armor" AV="0" WornOn="Face" />\n')),
            [],
        )

    def test_armour_that_does_grant_av_is_not_exempt(self) -> None:
        """The other half. Without this the AV rule could exempt every armour piece and pass."""
        self.assertTrue(
            self._curve(self._obj('    <part Name="Armor" AV="2" WornOn="Face" />\n')),
            "real armour was swept up by the no-AV exemption",
        )
