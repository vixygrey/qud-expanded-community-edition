#!/usr/bin/env python3
"""Tests for tools/report_dynamic_tables.py.

The cases here are the ones that would produce a wrong *number* rather than a crash, because a
report is believed on sight and a wrong count is indistinguishable from a right one.
"""

from __future__ import annotations

import contextlib
import io
import math
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import ClassVar

sys.path.insert(0, str(Path(__file__).resolve().parent))

from unittest import mock

import report_dynamic_tables
from check_vanilla_drift import BlueprintIndex
from report_dynamic_tables import (
    TIER_DELTA_WEIGHTS,
    collect,
    declarer,
    describe_drift,
    describe_inherits_drift,
    eligible,
    inherits_cells,
    inherits_members,
    inherits_snapshot_of,
    merged_objects,
    over_ceiling,
    requested_inherits_slices,
    resolved_role,
    resolved_tier,
    resolved_weight_tags,
    slice_label,
    slice_weight,
    snapshot_of,
    weight_tag_key,
)


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


class Snapshot(unittest.TestCase):
    """#303. Nothing enforced pool membership, so #261 and #262 could come back in silence.

    The check has to see vanilla to work at all. `BaseArrow` carries `DynamicObjectsTable:Ammo`,
    so a mod-only index would report the arrows out of the pool and be right by luck, while
    missing a *new* blueprint inheriting `BaseArrow` - which is the whole regression. That is why
    this is a local hook and not CI.
    """

    def index(self, extra: str = "") -> BlueprintIndex:
        return BlueprintIndex(
            roots(
                "<objects>"
                '<object Name="BaseArrow"><tag Name="DynamicObjectsTable:Ammo" />'
                '<part Name="Render" /></object>'
                '<object Name="ModArrow" Inherits="BaseArrow">'
                '<tag Name="DynamicObjectsTable:Ammo" Value="*delete" /></object>'
                + extra
                + "</objects>"
            )
        )

    def snap(self, index: BlueprintIndex, names: set[str]) -> dict:
        return snapshot_of(collect(index, names, {}))

    def test_a_deleted_tag_keeps_the_pool_out_of_the_snapshot(self) -> None:
        self.assertEqual(self.snap(self.index(), {"ModArrow"}), {})

    def test_a_new_blueprint_inheriting_a_vanilla_pool_is_caught(self) -> None:
        """The #261 regression exactly: inherit `BaseArrow` and forget the `*delete`."""
        before = self.snap(self.index(), {"ModArrow"})
        after = self.snap(
            self.index('<object Name="NewArrow" Inherits="BaseArrow" />'),
            {"ModArrow", "NewArrow"},
        )
        drift = describe_drift(before, after)
        self.assertTrue(drift, "a blueprint joining a pool must be reported")
        self.assertIn("NewArrow", " ".join(drift))
        self.assertIn("pool is new to this mod", " ".join(drift))

    def test_a_removed_declaration_is_caught(self) -> None:
        drift = describe_drift({"P": {"reaches": ["A"], "conditional": []}}, {})
        self.assertIn("no longer reaches", " ".join(drift))

    def test_snapshot_omits_pools_it_reaches_nothing_in(self) -> None:
        """An empty pool is noise: vanilla declares many this mod never touches."""
        snap = snapshot_of(
            {"P": {"reaches": [], "conditional": [], "declared_on": ["X"], "via": {}}}
        )
        self.assertEqual(snap, {})

    def test_identical_snapshots_report_no_drift(self) -> None:
        one = {"P": {"reaches": ["A", "B"], "conditional": []}}
        self.assertEqual(describe_drift(one, dict(one)), [])


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


class InheritsPools(unittest.TestCase):
    """#481: membership nobody declares, so nothing recorded it.

    A blueprint joins `DynamicInheritsTable:<Base>` by descending from `<Base>` - there is no tag
    to grep and nothing in a diff to review, which is why this is counted rather than read.
    """

    BASE = (
        "<objects>"
        '<object Name="BaseSword"><part Name="Render" />'
        '<tag Name="BaseObject" Value="*noinherit" /><tag Name="Tier" Value="3" /></object>'
        '<object Name="VanillaSword" Inherits="BaseSword" />'
        '<object Name="Vixy_Sword" Inherits="BaseSword" />'
        "</objects>"
    )

    def cells(self, xml: str | None = None, new: set[str] | None = None, window=(3, 3)):
        index = BlueprintIndex(roots(xml or self.BASE))
        members = inherits_members(index, {"BaseSword"})
        return inherits_cells(
            members, {"BaseSword": {window}}, new if new is not None else {"Vixy_Sword"}
        )

    def test_a_descendant_is_counted_on_the_side_it_belongs_to(self) -> None:
        cell = self.cells()[("BaseSword", "Tier3")]
        self.assertEqual(cell[2:], (1, 1))
        self.assertEqual(cell[0], cell[1])

    def test_the_base_itself_is_not_counted(self) -> None:
        """It is not eligible, and counting it would inflate vanilla's side by one everywhere."""
        _, _, mine, vanilla = self.cells()[("BaseSword", "Tier3")]
        self.assertEqual(mine + vanilla, 2)

    def test_tier_is_inherited_from_the_nearest_declaration(self) -> None:
        cell = self.cells()[("BaseSword", "Tier3")]
        self.assertEqual(cell[0], TIER_DELTA_WEIGHTS[0])

    def test_a_blueprint_with_no_tier_at_all_is_still_a_member(self) -> None:
        """#520. The game does not skip it: `_Tier` keeps its -999 sentinel, the delta misses
        `TierDeltaWeights`, and it joins at weight 1. Dropping it understated every pool it is in,
        and 604 such blueprints sit under `PhysicalObject` alone."""
        cell = self.cells(
            "<objects>"
            '<object Name="BaseSword"><part Name="Render" />'
            '<tag Name="BaseObject" Value="*noinherit" /></object>'
            '<object Name="Vixy_Sword" Inherits="BaseSword" />'
            "</objects>"
        )[("BaseSword", "Tier3")]
        self.assertEqual(cell[0], 1)
        self.assertEqual(cell[2:], (1, 0))

    def test_an_excluded_blueprint_leaves_the_pool(self) -> None:
        """The one lever there is - and the reason the chip fix in #483 worked."""
        cell = self.cells(
            self.BASE.replace(
                '<object Name="Vixy_Sword" Inherits="BaseSword" />',
                '<object Name="Vixy_Sword" Inherits="BaseSword">'
                '<tag Name="ExcludeFromDynamicEncounters" /></object>',
            )
        )[("BaseSword", "Tier3")]
        self.assertEqual(cell[0], 0)
        self.assertEqual(cell[2:], (0, 1))

    def test_every_requested_slice_gets_a_cell_from_the_same_members(self) -> None:
        """#494: a slice holds every member of the pool, not only those at its own tier. Building
        cells from the tiers blueprints happen to carry hid forty slices that were over half."""
        index = BlueprintIndex(roots(self.BASE))
        members = inherits_members(index, {"BaseSword"})
        cells = inherits_cells(
            members, {"BaseSword": {(0, 0), (3, 3), (8, 8), None}}, {"Vixy_Sword"}
        )
        self.assertEqual(
            set(cells),
            {
                ("BaseSword", "Tier0"),
                ("BaseSword", "Tier3"),
                ("BaseSword", "Tier8"),
                ("BaseSword", "untiered"),
            },
        )
        for cell in cells.values():
            self.assertEqual(cell[2:], (1, 1))


class ResolvedTier(unittest.TestCase):
    """#520. `GameObjectBlueprint.Tier` is not the `Tier` tag: it falls back to Level, and vanilla
    creatures carry Level and no tag. Reading the tag alone dropped 593 eligible blueprints."""

    def index(self, body: str) -> BlueprintIndex:
        return BlueprintIndex(roots(f"<objects>{body}</objects>"))

    def test_the_tag_decides_when_it_is_there(self) -> None:
        index = self.index(
            '<object Name="Sword"><tag Name="Tier" Value="6" /></object>'
        )
        self.assertEqual(resolved_tier(index, "Sword"), 6)

    def test_level_supplies_the_tier_when_the_tag_does_not(self) -> None:
        """Every creature in the game takes this route - Goat is Level 1 and has no Tier tag."""
        index = self.index(
            '<object Name="Goat"><stat Name="Level" Value="1" /></object>'
        )
        self.assertEqual(resolved_tier(index, "Goat"), 1)

    def test_the_tag_wins_over_level(self) -> None:
        index = self.index(
            '<object Name="Thing"><tag Name="Tier" Value="2" />'
            '<stat Name="Level" Value="40" /></object>'
        )
        self.assertEqual(resolved_tier(index, "Thing"), 2)

    def test_level_is_clamped_to_the_ladder(self) -> None:
        for level, want in ((0, 1), (1, 1), (35, 8), (400, 8)):
            with self.subTest(level=level):
                index = self.index(
                    f'<object Name="X"><stat Name="Level" Value="{level}" /></object>'
                )
                self.assertEqual(resolved_tier(index, "X"), want)

    def test_a_level_the_loader_cannot_parse_is_tier_one_not_no_tier(self) -> None:
        """`Convert.ToInt32("18-20")` throws, the loader catches it, and BaseValue stays zero.
        Thirty-two vanilla villagers declare Level that way and the game tiers them at 1."""
        index = self.index(
            '<object Name="Apothecary"><stat Name="Level" sValue="18-20" /></object>'
        )
        self.assertEqual(resolved_tier(index, "Apothecary"), 1)

    def test_neither_tag_nor_level_is_no_tier(self) -> None:
        """None, not zero - the game's -999 sentinel. It still belongs to the pool; see
        SliceWeight."""
        index = self.index('<object Name="Rock"><part Name="Render" /></object>')
        self.assertIsNone(resolved_tier(index, "Rock"))

    def test_level_is_inherited(self) -> None:
        index = self.index(
            '<object Name="Goat"><stat Name="Level" Value="1" /></object>'
            '<object Name="Vixy_DunGoat" Inherits="Goat" />'
        )
        self.assertEqual(resolved_tier(index, "Vixy_DunGoat"), 1)


class ResolvedRole(unittest.TestCase):
    """#520. The weighting reads `Tags || Props`. Vanilla declares Role as a tag 352 times and as
    a property never; this fork does the opposite thirteen times, and reading only tags weighted
    those thirteen a hundred times too heavily."""

    def index(self, body: str) -> BlueprintIndex:
        return BlueprintIndex(roots(f"<objects>{body}</objects>"))

    def test_a_tag_is_read(self) -> None:
        index = self.index('<object Name="X"><tag Name="Role" Value="Hero" /></object>')
        self.assertEqual(resolved_role(index, "X"), "Hero")

    def test_a_property_is_read(self) -> None:
        index = self.index(
            '<object Name="Raven_Zetachrome Shield">'
            '<property Name="Role" Value="Rare" /></object>'
        )
        self.assertEqual(resolved_role(index, "Raven_Zetachrome Shield"), "Rare")

    def test_the_tag_is_consulted_first(self) -> None:
        index = self.index(
            '<object Name="X"><tag Name="Role" Value="Hero" />'
            '<property Name="Role" Value="Rare" /></object>'
        )
        self.assertEqual(resolved_role(index, "X"), "Hero")

    def test_an_erased_property_is_not_a_role(self) -> None:
        index = self.index(
            '<object Name="X"><property Name="Role" Value="*delete" /></object>'
        )
        self.assertIsNone(resolved_role(index, "X"))

    def test_a_property_role_reaches_the_weighting(self) -> None:
        """The whole point: BaseShield Tier8 read 96.67% until this landed, and is 69.45%."""
        index = self.index(
            '<object Name="X"><property Name="Role" Value="Rare" /></object>'
        )
        self.assertEqual(
            slice_weight(8, (8, 8), resolved_role(index, "X")),
            math.ceil(TIER_DELTA_WEIGHTS[0] * 0.01),
        )


class Mixins(unittest.TestCase):
    """#526. `<mixin>` is a second inheritance mechanism, documented on the wiki's Modding:Objects
    page, and the index followed only `Inherits=`. That hid the
    `ExcludeFromDynamicEncounters` on `BaseVehicleGolem` and `BaseChiliadCreatureStats`, and with
    it 143 vanilla blueprints that are in no dynamic pool - understating this fork's share of 43
    slices. Caught by a playtest, not by a check."""

    def index(self, body: str) -> BlueprintIndex:
        return BlueprintIndex(roots(f"<objects>{body}</objects>"))

    GOLEM = (
        '<object Name="BaseVehicleGolem"><tag Name="ExcludeFromDynamicEncounters" /></object>'
        '<object Name="BaseAntelope"><part Name="Render" /></object>'
        '<object Name="Antelope Golem" Inherits="BaseAntelope">'
        '<mixin Name="BaseVehicleGolem" /></object>'
    )

    def test_a_tag_arrives_through_a_mixin(self) -> None:
        index = self.index(self.GOLEM)
        self.assertTrue(index.has_tag("Antelope Golem", "ExcludeFromDynamicEncounters"))

    def test_that_tag_takes_the_blueprint_out_of_the_pool(self) -> None:
        """The whole consequence: `eligible` reads it, and 143 vanilla blueprints turn on this."""
        self.assertFalse(eligible(self.index(self.GOLEM), "Antelope Golem"))

    def test_a_mixin_does_not_confer_membership(self) -> None:
        """`DescendsFrom` walks `ShallowParent`, which is `Inherits=` and nothing else. Following
        a mixin here would have put 66 golems in the `Creature` pool."""
        index = self.index(self.GOLEM)
        self.assertEqual(
            [o.get("Name") for o in index.chain("Antelope Golem")],
            ["Antelope Golem", "BaseAntelope"],
        )

    def test_exclude_keeps_a_kind_out(self) -> None:
        """Vanilla's one use: `<mixin Name="Creature" Exclude="part" />`."""
        index = self.index(
            '<object Name="Creature"><part Name="Render" />'
            '<tag Name="Wanted" /></object>'
            '<object Name="Thing"><mixin Name="Creature" Exclude="part" /></object>'
        )
        self.assertTrue(index.has_tag("Thing", "Wanted"))
        self.assertFalse(index.has_part("Thing", "Render"))

    def test_include_admits_only_what_it_names(self) -> None:
        index = self.index(
            '<object Name="Src"><part Name="Render" /><tag Name="Wanted" /></object>'
            '<object Name="Thing"><mixin Name="Src" Include="part" /></object>'
        )
        self.assertTrue(index.has_part("Thing", "Render"))
        self.assertFalse(index.has_tag("Thing", "Wanted"))

    def test_an_ordinary_mixin_outranks_the_inherits_parent(self) -> None:
        """The loader applies `Inherits` and then ordinary mixins, each overwriting the last."""
        index = self.index(
            '<object Name="Parent"><tag Name="Colour" Value="parent" /></object>'
            '<object Name="Mix"><tag Name="Colour" Value="mixin" /></object>'
            '<object Name="Thing" Inherits="Parent"><mixin Name="Mix" /></object>'
        )
        self.assertEqual(index.tag_value("Thing", "Colour"), "mixin")

    def test_a_fill_mixin_is_outranked_by_the_inherits_parent(self) -> None:
        """`Load="Fill"` applies BEFORE normal inheritance, so the parent wins."""
        index = self.index(
            '<object Name="Parent"><tag Name="Colour" Value="parent" /></object>'
            '<object Name="Mix"><tag Name="Colour" Value="mixin" /></object>'
            '<object Name="Thing" Inherits="Parent">'
            '<mixin Name="Mix" Load="Fill" /></object>'
        )
        self.assertEqual(index.tag_value("Thing", "Colour"), "parent")

    def test_the_blueprints_own_declaration_still_wins(self) -> None:
        index = self.index(
            '<object Name="Mix"><tag Name="Colour" Value="mixin" /></object>'
            '<object Name="Thing"><mixin Name="Mix" />'
            '<tag Name="Colour" Value="own" /></object>'
        )
        self.assertEqual(index.tag_value("Thing", "Colour"), "own")

    def test_a_cycle_terminates(self) -> None:
        index = self.index(
            '<object Name="A"><mixin Name="B" /></object>'
            '<object Name="B"><mixin Name="A" /></object>'
        )
        self.assertEqual(
            {o.get("Name") for o in index.lookup_chain("A", "tag")}, {"A", "B"}
        )


class WeightTag(unittest.TestCase):
    """#524. The game's third multiplier, after the tier delta and Role. Vanilla uses it 81 times
    across 28 pools; this fork uses it to damp the creature variants inside two pools without
    touching the entries that distribute them deliberately."""

    def index(self, body: str) -> BlueprintIndex:
        return BlueprintIndex(roots(f"<objects>{body}</objects>"))

    def test_the_key_carries_the_tier(self) -> None:
        """`{zonetier}` is substituted before `RequireTable` sees the name, so the fabricator keys
        on the resolved name - which is why damping a pool costs a tag per tier."""
        self.assertEqual(
            weight_tag_key("BaseAnimal", (1, 1)),
            "DynamicInheritsTable:BaseAnimal:Tier1:Weight",
        )

    def test_the_key_keeps_a_range_intact(self) -> None:
        self.assertEqual(
            weight_tag_key("BaseShield", (3, 7)),
            "DynamicInheritsTable:BaseShield:Tier3-7:Weight",
        )

    def test_the_untiered_key_has_no_tier(self) -> None:
        self.assertEqual(
            weight_tag_key("PhysicalObject", None),
            "DynamicInheritsTable:PhysicalObject:Weight",
        )

    def test_it_multiplies_the_weight_the_other_two_produced(self) -> None:
        full = slice_weight(1, (1, 1), "Minion")
        self.assertEqual(slice_weight(1, (1, 1), "Minion", 0.2), math.ceil(full * 0.2))

    def test_zero_is_an_exclusion_not_a_weight(self) -> None:
        """`if (value == 0) continue` - the blueprint leaves the slice entirely."""
        self.assertEqual(slice_weight(1, (1, 1), "Minion", 0.0), 0)

    def test_a_tag_is_read_and_inherited(self) -> None:
        index = self.index(
            '<object Name="Dog">'
            '<tag Name="DynamicInheritsTable:BaseAnimal:Tier1:Weight" Value="0.2" /></object>'
            '<object Name="Vixy_MarshDog" Inherits="Dog" />'
        )
        self.assertEqual(
            resolved_weight_tags(index, "Vixy_MarshDog"),
            {"DynamicInheritsTable:BaseAnimal:Tier1:Weight": 0.2},
        )

    def test_a_value_the_game_cannot_parse_is_skipped_not_zeroed(self) -> None:
        """`Convert.ToDouble` throws, vanilla catches and logs it, and the weight is untouched.
        Reading it as zero would silently delete the blueprint from the slice instead."""
        index = self.index(
            '<object Name="X">'
            '<tag Name="DynamicInheritsTable:BaseAnimal:Tier1:Weight" Value="lots" /></object>'
        )
        self.assertEqual(resolved_weight_tags(index, "X"), {})

    def test_only_weight_tags_are_collected(self) -> None:
        index = self.index(
            '<object Name="X"><tag Name="Vixy_CreatureVariant" />'
            '<tag Name="DynamicObjectsTable:Hills_Creatures" /></object>'
        )
        self.assertEqual(resolved_weight_tags(index, "X"), {})


class WeightTagIsSliceScoped(unittest.TestCase):
    """The property the whole of #524 rests on: a tag damps ONE slice. If it leaked across tiers,
    78 tags would be doing the job of 6 and the numbers would be wrong everywhere."""

    XML = (
        "<objects>"
        '<object Name="BaseAnimal"><part Name="Render" />'
        '<tag Name="BaseObject" Value="*noinherit" /><tag Name="Tier" Value="1" /></object>'
        '<object Name="Vanilla Dog" Inherits="BaseAnimal" />'
        '<object Name="Vixy_MarshDog" Inherits="BaseAnimal">'
        '<tag Name="DynamicInheritsTable:BaseAnimal:Tier1:Weight" Value="0.2" /></object>'
        "</objects>"
    )

    def shares(self):
        index = BlueprintIndex(roots(self.XML))
        members = inherits_members(index, {"BaseAnimal"})
        cells = inherits_cells(
            members, {"BaseAnimal": {(1, 1), (2, 2)}}, {"Vixy_MarshDog"}
        )
        return {label: cells[("BaseAnimal", label)] for label in ("Tier1", "Tier2")}

    def test_the_tagged_slice_is_damped(self) -> None:
        mine, vanilla, _, _ = self.shares()["Tier1"]
        self.assertEqual(mine, math.ceil(vanilla * 0.2))

    def test_every_other_slice_is_untouched(self) -> None:
        mine, vanilla, _, _ = self.shares()["Tier2"]
        self.assertEqual(mine, vanilla)

    def test_the_member_is_still_in_the_pool(self) -> None:
        """Damped, not removed - the count must not move, or the ledger would report a departure
        that never happened."""
        for label in ("Tier1", "Tier2"):
            self.assertEqual(self.shares()[label][2:], (1, 1))


class SliceWeight(unittest.TestCase):
    """#494: the game weights a slice's members by tier distance, and a flat count is a different
    question. At a factor of ten per step the nearest tier dominates completely."""

    def test_the_requested_tier_weighs_most(self) -> None:
        self.assertEqual(slice_weight(3, (3, 3), None), 10**8)

    def test_each_step_away_divides_by_ten(self) -> None:
        self.assertEqual(slice_weight(4, (3, 3), None), 10**7)
        self.assertEqual(slice_weight(1, (3, 3), None), 10**6)

    def test_distance_is_symmetric(self) -> None:
        self.assertEqual(slice_weight(1, (3, 3), None), slice_weight(5, (3, 3), None))

    def test_beyond_the_table_falls_back_to_one(self) -> None:
        """TierDeltaWeights stops at seven steps; the game's own default is 1u, not zero, so a
        distant blueprint stays in the pool instead of dropping out of it."""
        self.assertEqual(slice_weight(1, (8, 8), None), 10)
        self.assertEqual(slice_weight(0, (8, 8), None), 1)

    def test_anything_inside_a_range_is_at_full_weight(self) -> None:
        for tier in (4, 5, 6, 7):
            self.assertEqual(slice_weight(tier, (4, 7), None), 10**8)

    def test_outside_a_range_the_distance_is_measured_from_the_low_end(self) -> None:
        """Vanilla writes Math.Min(Math.Abs(minTier - t), Math.Abs(minTier - t)) - the same
        expression twice, so maxTier never reaches the comparison. Reproducing that bug is the only
        way this report agrees with what a player rolls: tier 8 against Tier4-7 is four steps from
        the low end, not one from the high end."""
        self.assertEqual(slice_weight(8, (4, 7), None), 10**4)

    def test_a_tier_less_member_weighs_one_in_a_tiered_slice(self) -> None:
        """#520. The game computes a delta of about a thousand, misses TierDeltaWeights, and takes
        the 1u fallback - it does not drop the blueprint."""
        self.assertEqual(slice_weight(None, (4, 4), None), 1)

    def test_a_tier_less_member_weighs_full_in_the_untiered_table(self) -> None:
        """The forced-zero delta reaches it before its own tier is ever consulted."""
        self.assertEqual(slice_weight(None, None, None), TIER_DELTA_WEIGHTS[0])

    def test_the_untiered_table_weighs_every_member_alike(self) -> None:
        self.assertEqual(slice_weight(0, None, None), slice_weight(8, None, None))

    def test_role_multiplies_the_tier_weight(self) -> None:
        """Reachable, unlike the tier delta on the untiered path - which is the correction in
        #492. Common and Minion quadruple; the rest divide."""
        self.assertEqual(slice_weight(3, (3, 3), "Minion"), 4 * 10**8)
        self.assertEqual(slice_weight(3, (3, 3), "Rare"), 10**6)

    def test_an_unknown_role_is_left_alone(self) -> None:
        """Controller, Lurker, NPC, Summoner and Breeder are used on 63 vanilla blueprints and are
        in no multiplier table, so they must take the plain tier weight."""
        self.assertEqual(slice_weight(3, (3, 3), "Lurker"), 10**8)
        self.assertEqual(slice_weight(3, (3, 3), None), 10**8)


class InheritsCeiling(unittest.TestCase):
    """docs/STYLEGUIDE.md 3.2.1 - reported, not enforced, since #494."""

    def test_over_half_by_weight_is_reported(self) -> None:
        self.assertEqual(
            over_ceiling({("Pool", "Tier3"): (11, 9, 11, 9)}), [("Pool", "Tier3")]
        )

    def test_at_half_exactly_is_not_reported(self) -> None:
        self.assertEqual(over_ceiling({("Pool", "Tier3"): (9, 9, 9, 9)}), [])

    def test_a_thin_vanilla_presence_is_exempt(self) -> None:
        """1 of 1 does not mean this fork dominates the slice - it means vanilla ships none, and a
        percentage there reports only that vanilla left a gap."""
        self.assertEqual(over_ceiling({("Pool", "Tier0"): (1, 0, 1, 0)}), [])
        self.assertEqual(over_ceiling({("Pool", "Tier0"): (3, 3, 3, 3)}), [])

    def test_the_floor_is_on_vanillas_member_count_not_its_weight(self) -> None:
        """Weight and count answer different questions: five vanilla members can carry very little
        weight in a distant slice, and that slice is still worth measuring."""
        self.assertEqual(
            over_ceiling({("Pool", "Tier3"): (10**8, 10, 1, 5)}), [("Pool", "Tier3")]
        )
        self.assertEqual(over_ceiling({("Pool", "Tier3"): (10**8, 10, 1, 4)}), [])

    def test_the_ranking_puts_the_most_dominated_slice_first(self) -> None:
        self.assertEqual(
            over_ceiling(
                {
                    ("Pool", "Tier1"): (60, 40, 6, 40),
                    ("Pool", "Tier2"): (90, 10, 9, 10),
                }
            ),
            [("Pool", "Tier2"), ("Pool", "Tier1")],
        )


class InheritsSnapshot(unittest.TestCase):
    """#494 swapped a ceiling that fails for a snapshot that fails, so this is now the only thing
    guarding the inherited route. Membership and share drift separately and must be told apart."""

    MEMBERS: ClassVar = {"Pool": [("Vixy_Sword", 3, None), ("VanillaSword", 3, None)]}

    def snapshot(self, cells):
        return inherits_snapshot_of(cells, self.MEMBERS, {"Vixy_Sword"})

    def test_it_pins_membership_once_and_a_share_per_slice(self) -> None:
        snap = self.snapshot(
            {("Pool", "Tier3"): (75, 25, 1, 1), ("Pool", "Tier8"): (10, 90, 1, 1)}
        )
        self.assertEqual(snap["Pool"]["mine"], ["Vixy_Sword"])
        self.assertEqual(snap["Pool"]["shares"], {"Tier3": 75, "Tier8": 10})

    def test_a_pool_this_fork_is_not_in_is_omitted(self) -> None:
        """Pinning a share of zero for every pool would bury the ones that matter."""
        snap = inherits_snapshot_of(
            {("Pool", "Tier3"): (0, 100, 0, 2)}, self.MEMBERS, set()
        )
        self.assertEqual(snap, {})

    def test_identical_snapshots_report_no_drift(self) -> None:
        snap = self.snapshot({("Pool", "Tier3"): (75, 25, 1, 1)})
        self.assertEqual(describe_inherits_drift(snap, snap), [])

    def test_a_blueprint_joining_a_pool_is_caught(self) -> None:
        old = {"Pool": {"mine": [], "shares": {"Tier3": 50}}}
        new = {"Pool": {"mine": ["Vixy_Sword"], "shares": {"Tier3": 50}}}
        self.assertEqual(
            describe_inherits_drift(old, new),
            ["Pool: Vixy_Sword now descends into this pool"],
        )

    def test_a_share_moving_on_its_own_is_caught(self) -> None:
        """The case no diff shows: a Qud update adds tier-8 weapons and this fork's share of that
        slice falls without a line of mine changing."""
        old = {"Pool": {"mine": ["Vixy_Sword"], "shares": {"Tier8": 91}}}
        new = {"Pool": {"mine": ["Vixy_Sword"], "shares": {"Tier8": 74}}}
        self.assertEqual(
            describe_inherits_drift(old, new),
            ["Pool:Tier8: this fork's share moved 91% -> 74%"],
        )

    def test_a_newly_requested_slice_is_caught(self) -> None:
        old = {"Pool": {"mine": ["Vixy_Sword"], "shares": {}}}
        new = {"Pool": {"mine": ["Vixy_Sword"], "shares": {"Tier2": 60}}}
        self.assertIn("newly requested", describe_inherits_drift(old, new)[0])

    def test_a_pool_this_fork_stops_reaching_is_caught(self) -> None:
        old = {"Pool": {"mine": ["Vixy_Sword"], "shares": {"Tier3": 50}}}
        self.assertEqual(
            describe_inherits_drift(old, {}),
            ["Pool: this fork no longer reaches this inherited pool"],
        )


class RequestedInheritsSlices(unittest.TestCase):
    def slices(self, body: str):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "PopulationTables.xml").write_text(
            f"<populations>{body}</populations>", encoding="utf-8"
        )
        return requested_inherits_slices(tmp)

    def test_a_commented_out_reference_does_not_count(self) -> None:
        """Vanilla keeps a commented-out DynamicInheritsTable:BaseAnimal:Tier2. Counting it would
        measure this fork's share of a pool nothing rolls."""
        got = self.slices(
            '<table Name="DynamicInheritsTable:Live:Tier1" />'
            '<!-- <table Name="DynamicInheritsTable:Dead:Tier2" /> -->'
        )
        self.assertEqual(set(got), {"Live"})

    def test_a_plain_tier_is_a_single_slice(self) -> None:
        self.assertEqual(
            self.slices('<table Name="DynamicInheritsTable:P:Tier4" />')["P"], {(4, 4)}
        )

    def test_a_range_is_kept_as_a_range(self) -> None:
        """Tier4-7 is not Tier4: everything inside the window is at full weight."""
        self.assertEqual(
            self.slices('<table Name="DynamicInheritsTable:P:Tier4-7" />')["P"],
            {(4, 7)},
        )

    def test_a_substituted_spec_contributes_every_tier(self) -> None:
        """{zonetier} is resolved at runtime and can land anywhere, so all nine are reachable and
        pinning only the ones blueprints happen to carry is what #494 fixed."""
        self.assertEqual(
            self.slices('<table Name="DynamicInheritsTable:P:Tier{zonetier}" />')["P"],
            {(n, n) for n in range(9)},
        )

    def test_a_request_with_no_tier_is_the_untiered_table(self) -> None:
        self.assertEqual(
            self.slices('<table Name="DynamicInheritsTable:P" />')["P"], {None}
        )

    def test_slices_from_several_requests_accumulate(self) -> None:
        got = self.slices(
            '<table Name="DynamicInheritsTable:P:Tier1" />'
            '<table Name="DynamicInheritsTable:P:Tier4-7" />'
            '<table Name="DynamicInheritsTable:P" />'
        )
        self.assertEqual(got["P"], {(1, 1), (4, 7), None})


class SliceLabel(unittest.TestCase):
    def test_labels_are_stable_across_the_three_shapes(self) -> None:
        """These are snapshot keys, so a change of spelling reads as drift on every slice."""
        self.assertEqual(slice_label((3, 3)), "Tier3")
        self.assertEqual(slice_label((4, 7)), "Tier4-7")
        self.assertEqual(slice_label(None), "untiered")
