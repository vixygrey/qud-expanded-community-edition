#!/usr/bin/env python3
"""Tests for tools/report_dynamic_tables.py.

The cases here are the ones that would produce a wrong *number* rather than a crash, because a
report is believed on sight and a wrong count is indistinguishable from a right one.
"""

from __future__ import annotations

import contextlib
import io
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from unittest import mock

import report_dynamic_tables
from check_vanilla_drift import BlueprintIndex
from report_dynamic_tables import collect, declarer, eligible, merged_objects


def roots(*xml: str) -> list[ET.Element]:
    return [ET.fromstring(x) for x in xml]


class MergePreservesVanilla(unittest.TestCase):
    """215 of the mod's blueprints are Load="Merge" edits to vanilla objects.

    Indexing them last-wins discards the vanilla record - Obsidian Kris would lose
    Inherits="BaseDagger", two tags and four parts - and every count drawn from it would be
    quietly wrong.
    """

    def test_a_merge_keeps_inherits_tags_and_parts(self) -> None:
        index = BlueprintIndex(
            merged_objects(
                roots(
                    '<objects><object Name="Kris" Inherits="BaseDagger">'
                    '<tag Name="Keep" /><part Name="Render" />'
                    "</object></objects>"
                ),
                roots(
                    '<objects><object Name="Kris" Load="Merge">'
                    '<part Name="Commerce" Value="9" />'
                    "</object></objects>"
                ),
            )
        )
        self.assertEqual(index.objects["Kris"].get("Inherits"), "BaseDagger")
        self.assertTrue(index.has_tag("Kris", "Keep"))
        self.assertTrue(index.has_part("Kris", "Render"))
        self.assertTrue(index.has_part("Kris", "Commerce"))

    def test_a_merge_overrides_rather_than_duplicating(self) -> None:
        index = BlueprintIndex(
            merged_objects(
                roots(
                    '<objects><object Name="X"><tag Name="T" Value="old" /></object></objects>'
                ),
                roots(
                    '<objects><object Name="X" Load="Merge">'
                    '<tag Name="T" Value="new" />'
                    "</object></objects>"
                ),
            )
        )
        tags = [
            t.get("Value")
            for t in index.objects["X"].findall("tag")
            if t.get("Name") == "T"
        ]
        self.assertEqual(tags, ["new"])


class Eligibility(unittest.TestCase):
    """EncountersAPI.IsEligibleForDynamicEncounters, as the game computes it."""

    def index(self, xml: str) -> BlueprintIndex:
        return BlueprintIndex(roots(xml))

    def test_a_base_object_is_not_eligible(self) -> None:
        i = self.index(
            '<objects><object Name="B"><part Name="Render" />'
            '<tag Name="BaseObject" Value="*noinherit" /></object></objects>'
        )
        self.assertFalse(eligible(i, "B"))

    def test_a_descendant_of_a_base_is_eligible(self) -> None:
        i = self.index(
            "<objects>"
            '<object Name="B"><part Name="Render" />'
            '<tag Name="BaseObject" Value="*noinherit" /></object>'
            '<object Name="C" Inherits="B" />'
            "</objects>"
        )
        self.assertTrue(eligible(i, "C"))

    def test_no_render_is_not_eligible(self) -> None:
        i = self.index('<objects><object Name="X" /></objects>')
        self.assertFalse(eligible(i, "X"))

    def test_an_explicit_exclusion_is_not_eligible(self) -> None:
        i = self.index(
            '<objects><object Name="X"><part Name="Render" />'
            '<tag Name="ExcludeFromDynamicEncounters" /></object></objects>'
        )
        self.assertFalse(eligible(i, "X"))


class Declarer(unittest.TestCase):
    """ "Inherited" is not one answer - it matters whose base it came from."""

    def test_it_names_the_nearest_declaring_blueprint(self) -> None:
        i = BlueprintIndex(
            roots(
                "<objects>"
                '<object Name="Base"><tag Name="DynamicObjectsTable:Guns" /></object>'
                '<object Name="Child" Inherits="Base" />'
                "</objects>"
            )
        )
        self.assertEqual(declarer(i, "Child", "DynamicObjectsTable:Guns"), "Base")

    def test_a_noinherit_declaration_does_not_reach_a_descendant(self) -> None:
        i = BlueprintIndex(
            roots(
                "<objects>"
                '<object Name="Base"><tag Name="T" Value="*noinherit" /></object>'
                '<object Name="Child" Inherits="Base" />'
                "</objects>"
            )
        )
        self.assertIsNone(declarer(i, "Child", "T"))
        self.assertEqual(declarer(i, "Base", "T"), "Base")


class Collect(unittest.TestCase):
    def test_it_separates_what_the_mod_declares_from_what_it_inherits(self) -> None:
        index = BlueprintIndex(
            roots(
                "<objects>"
                '<object Name="VanillaBase"><tag Name="DynamicObjectsTable:Items" />'
                '<part Name="Render" /></object>'
                '<object Name="ModBase"><part Name="Render" />'
                '<tag Name="DynamicObjectsTable:Guns" />'
                '<tag Name="BaseObject" Value="*noinherit" /></object>'
                '<object Name="ModGun" Inherits="ModBase" />'
                '<object Name="ModItem" Inherits="VanillaBase" />'
                "</objects>"
            )
        )
        tables = collect(
            index,
            {"ModBase", "ModGun", "ModItem"},
            {"DynamicObjectsTable:Guns": {"ModBase"}},
        )
        guns = tables["DynamicObjectsTable:Guns"]
        self.assertEqual(guns["declared_in_mod"], ["ModBase"])
        self.assertEqual(guns["reaches"], ["ModGun"])
        self.assertEqual(guns["via"]["ModGun"], "ModBase")

        items = tables["DynamicObjectsTable:Items"]
        self.assertEqual(items["declared_in_mod"], [])
        self.assertIn("ModItem", items["reaches"])

    def test_an_option_dependent_exclusion_is_reported_not_guessed(self) -> None:
        index = BlueprintIndex(
            roots(
                '<objects><object Name="X"><part Name="Render" />'
                '<tag Name="DynamicObjectsTable:Guns" />'
                '<tag Name="ExcludeFromDynamicEncountersOption" Value="SomeOption" />'
                "</object></objects>"
            )
        )
        tables = collect(index, {"X"}, {"DynamicObjectsTable:Guns": {"X"}})
        data = tables["DynamicObjectsTable:Guns"]
        self.assertEqual(data["conditional"], ["X"])
        self.assertEqual(data["reaches"], [])


class WithoutTheGame(unittest.TestCase):
    """A skip that reads like a pass is its own defect - tools/compile_scripting.py's lesson."""

    def run_with(self, argv: list[str]) -> tuple[int, str]:
        err = io.StringIO()
        with (
            mock.patch.object(sys, "argv", ["report_dynamic_tables.py", *argv]),
            contextlib.redirect_stderr(err),
        ):
            code = report_dynamic_tables.main()
        return code, err.getvalue()

    def test_it_skips_loudly_and_passes(self) -> None:
        with mock.patch.object(report_dynamic_tables, "find_game", return_value=None):
            code, err = self.run_with([])
        self.assertEqual(code, 0)
        self.assertIn("SKIPPED", err)
        self.assertIn("BaseArrow is vanilla", err)

    def test_require_turns_the_skip_into_a_failure(self) -> None:
        with mock.patch.object(report_dynamic_tables, "find_game", return_value=None):
            code, err = self.run_with(["--require"])
        self.assertEqual(code, 1)
        self.assertIn("ERROR", err)

    def test_a_game_path_that_does_not_validate_is_refused(self) -> None:
        code, err = self.run_with(["--game", "/nonexistent"])
        self.assertEqual(code, 1)
        self.assertIn("Bodies.xml", err)


if __name__ == "__main__":
    unittest.main()
