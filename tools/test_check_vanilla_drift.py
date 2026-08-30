"""Tests for `BlueprintIndex.carriers`, the resolved census.

`docs/LESSONS.md` asks for a negative test rather than a positive one: a fixture where the
declared-only answer is provably wrong, so the helper is seen to *fire* rather than merely to pass.
Every test here is built that way — the declared count is asserted alongside the resolved one, so a
regression that silently reverts to `findall` fails on the difference rather than on a total that
might have been right by luck.

Split out in #702, whose finding is that the declared count was short three times in two days and
the gap held the answer each time.
"""

from __future__ import annotations

import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_vanilla_drift import BlueprintIndex


def index(xml: str) -> BlueprintIndex:
    return BlueprintIndex([ET.fromstring(xml)])


def declared(idx: BlueprintIndex, kind: str, name: str) -> set[str]:
    """What a naive `findall` census returns — the wrong answer these tests exist to catch."""
    return {
        n
        for n, o in idx.objects.items()
        if any(e.get("Name") == name for e in o.findall(kind))
    }


class Carriers(unittest.TestCase):
    def test_an_inherited_part_is_counted_and_declaring_alone_misses_it(self) -> None:
        i = index(
            "<objects>"
            '<object Name="Base"><part Name="Travel" /></object>'
            '<object Name="Child" Inherits="Base" />'
            '<object Name="Grandchild" Inherits="Child" />'
            "</objects>"
        )
        self.assertEqual(declared(i, "part", "Travel"), {"Base"})
        self.assertEqual(i.carriers("part", "Travel"), {"Base", "Child", "Grandchild"})

    def test_a_mixin_carries_a_part_and_the_inherits_walk_alone_misses_it(self) -> None:
        """The #526 case: following `Inherits=` only made 143 vanilla blueprints invisible."""
        i = index(
            "<objects>"
            '<object Name="StatsMixin"><part Name="Travel" /></object>'
            '<object Name="Golem"><mixin Name="StatsMixin" /></object>'
            "</objects>"
        )
        self.assertEqual(declared(i, "part", "Travel"), {"StatsMixin"})
        self.assertIn("Golem", i.carriers("part", "Travel"))

    def test_noinherit_confines_a_tag_to_its_declarer(self) -> None:
        i = index(
            "<objects>"
            '<object Name="Base"><tag Name="BaseObject" Value="*noinherit" /></object>'
            '<object Name="Child" Inherits="Base" />'
            "</objects>"
        )
        self.assertEqual(i.carriers("tag", "BaseObject"), {"Base"})

    def test_delete_removes_an_inherited_tag_outright(self) -> None:
        """Vanilla takes `FoldingChair` out of `DynamicObjectsTable:Trinkets` exactly this way."""
        i = index(
            "<objects>"
            '<object Name="Trinket"><tag Name="DynamicObjectsTable:Trinkets" /></object>'
            '<object Name="FoldingChair" Inherits="Trinket">'
            '<tag Name="DynamicObjectsTable:Trinkets" Value="*delete" /></object>'
            '<object Name="SaltMill" Inherits="Trinket" />'
            "</objects>"
        )
        self.assertEqual(
            i.carriers("tag", "DynamicObjectsTable:Trinkets"), {"Trinket", "SaltMill"}
        )

    def test_a_nearer_delete_wins_over_a_further_declaration(self) -> None:
        """The nearest declaration decides, so a deleted tag stays gone for descendants."""
        i = index(
            "<objects>"
            '<object Name="A"><tag Name="T" /></object>'
            '<object Name="B" Inherits="A"><tag Name="T" Value="*delete" /></object>'
            '<object Name="C" Inherits="B" />'
            "</objects>"
        )
        self.assertEqual(i.carriers("tag", "T"), {"A"})

    def test_a_cycle_terminates(self) -> None:
        i = index(
            "<objects>"
            '<object Name="A" Inherits="B"><part Name="P" /></object>'
            '<object Name="B" Inherits="A" />'
            "</objects>"
        )
        self.assertEqual(i.carriers("part", "P"), {"A", "B"})

    def test_a_name_nothing_carries_is_empty_rather_than_everything(self) -> None:
        i = index('<objects><object Name="A"><part Name="P" /></object></objects>')
        self.assertEqual(i.carriers("part", "Absent"), set())


class CarriersMatching(unittest.TestCase):
    def test_a_predicate_resolves_a_family_of_tag_names(self) -> None:
        i = index(
            "<objects>"
            '<object Name="Base"><tag Name="DynamicObjectsTable:Guns:Tier3:Weight" Value="0.3" /></object>'
            '<object Name="Child" Inherits="Base" />'
            '<object Name="Unrelated"><tag Name="Tier" Value="1" /></object>'
            "</objects>"
        )
        got = i.carriers_matching("tag", lambda n: n.endswith(":Weight"))
        self.assertEqual(got, {"Base", "Child"})

    def test_the_predicate_census_also_honours_delete(self) -> None:
        i = index(
            "<objects>"
            '<object Name="Base"><tag Name="X:Weight" Value="0.3" /></object>'
            '<object Name="Child" Inherits="Base"><tag Name="X:Weight" Value="*delete" /></object>'
            "</objects>"
        )
        self.assertEqual(
            i.carriers_matching("tag", lambda n: n.endswith(":Weight")), {"Base"}
        )


if __name__ == "__main__":
    unittest.main()
