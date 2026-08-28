#!/usr/bin/env python3
"""Tests for tools/snapshot_qud_api.py.

`guard_part_source`, because it is the part that can be tested without a copy of the game: it
reads the committed snapshot and the run's own arguments, and nothing else.

And the skip/fail split added for #246, which is the invariant the pre-commit hook rests on. A
missing dependency must skip so a contributor without Caves of Qud is not blocked by a hook they
cannot satisfy; a genuinely stale snapshot must NOT, because that is a real finding. Collapsing the
two in either direction breaks the check - one way it blocks everyone, the other way it never fires.

It is also the part worth testing. #244 found that mixing the two part sources breaks both paths -
a plain write over an assembly-built snapshot silently drops 656 part names, and `--check` across
the same mismatch calls a current file STALE and then advises the command that performs the drop.
Both directions are covered here, along with the two cases that must stay quiet: a first
generation with no snapshot to compare against, and a snapshot too broken to read.

No game, no network, no dependencies.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import snapshot_qud_api
from check_vanilla_drift import BlueprintIndex

ASSEMBLY = Path(
    "/nonexistent/Assembly-CSharp.dll"
)  # never opened; only its presence matters


@contextmanager
def chdir(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


@contextmanager
def snapshot(part_source: str | None):
    """A temp tree holding a committed snapshot, or a raw string, or nothing."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        Path(root, "tools").mkdir()
        if part_source is not None:
            Path(root, "tools", "qud-api.json").write_text(
                json.dumps({"part_source": part_source, "digest": "abc"}),
                encoding="utf-8",
            )
        with chdir(root):
            yield


class NoInheritTagResolution(unittest.TestCase):
    """`*noinherit` confines a tag to the blueprint declaring it.

    Matching on tag name alone inverts the answer for every descendant, and inverts it to
    *nothing found* - the failure docs/LESSONS.md warns about under "A search that finds nothing
    has two explanations". See #265.
    """

    def index(self, xml: str) -> BlueprintIndex:
        return BlueprintIndex([ET.fromstring(xml)])

    def test_an_ordinary_tag_reaches_descendants(self) -> None:
        i = self.index(
            "<objects>"
            '  <object Name="Base"><tag Name="Guns" /></object>'
            '  <object Name="Child" Inherits="Base" />'
            "</objects>"
        )
        self.assertTrue(i.has_tag("Child", "Guns"))

    def test_noinherit_stops_at_the_declaring_blueprint(self) -> None:
        i = self.index(
            "<objects>"
            '  <object Name="Base"><tag Name="BaseObject" Value="*noinherit" /></object>'
            '  <object Name="Child" Inherits="Base" />'
            "</objects>"
        )
        self.assertTrue(i.has_tag("Base", "BaseObject"))
        self.assertFalse(i.has_tag("Child", "BaseObject"))

    def test_a_nearer_declaration_wins_over_a_noinherit_ancestor(self) -> None:
        i = self.index(
            "<objects>"
            '  <object Name="Base"><tag Name="X" Value="*noinherit" /></object>'
            '  <object Name="Mid" Inherits="Base"><tag Name="X" /></object>'
            '  <object Name="Child" Inherits="Mid" />'
            "</objects>"
        )
        self.assertTrue(i.has_tag("Child", "X"))

    def test_parts_have_no_noinherit_and_reach_descendants(self) -> None:
        i = self.index(
            "<objects>"
            '  <object Name="Base"><part Name="Render" /></object>'
            '  <object Name="Child" Inherits="Base" />'
            "</objects>"
        )
        self.assertTrue(i.has_part("Child", "Render"))

    def test_delete_removes_an_inherited_tag(self) -> None:
        """Vanilla takes Corpse out of DynamicObjectsTable:Items exactly this way."""
        i = self.index(
            "<objects>"
            '  <object Name="Item"><tag Name="T" /></object>'
            '  <object Name="Corpse" Inherits="Item"><tag Name="T" Value="*delete" /></object>'
            "</objects>"
        )
        self.assertTrue(i.has_tag("Item", "T"))
        self.assertFalse(i.has_tag("Corpse", "T"))

    def test_delete_also_stops_it_reaching_descendants(self) -> None:
        i = self.index(
            "<objects>"
            '  <object Name="Item"><tag Name="T" /></object>'
            '  <object Name="Corpse" Inherits="Item"><tag Name="T" Value="*delete" /></object>'
            '  <object Name="Robot Corpse" Inherits="Corpse" />'
            "</objects>"
        )
        self.assertFalse(i.has_tag("Robot Corpse", "T"))

    def test_a_nearer_plain_declaration_beats_a_deleted_ancestor(self) -> None:
        """*delete is not permanent - a descendant may declare the tag again."""
        i = self.index(
            "<objects>"
            '  <object Name="A"><tag Name="T" /></object>'
            '  <object Name="B" Inherits="A"><tag Name="T" Value="*delete" /></object>'
            '  <object Name="C" Inherits="B"><tag Name="T" /></object>'
            "</objects>"
        )
        self.assertTrue(i.has_tag("C", "T"))

    def test_a_cycle_terminates(self) -> None:
        i = self.index(
            "<objects>"
            '  <object Name="A" Inherits="B" />'
            '  <object Name="B" Inherits="A" />'
            "</objects>"
        )
        self.assertFalse(i.has_tag("A", "Anything"))


class PsionicFirearmRegression(unittest.TestCase):
    """The real case #265 was found through, reduced to its shape.

    `Raven_Base Psionic Pistol` declares both `BaseObject` (as `*noinherit`) and
    `DynamicObjectsTable:Guns` (inheritable). A resolver ignoring `*noinherit` reports every
    descendant as a base blueprint and therefore ineligible - 0 of 20 rather than 18.
    """

    def test_descendants_are_eligible_and_the_base_is_not(self) -> None:
        i = BlueprintIndex(
            [
                ET.fromstring(
                    "<objects>"
                    '  <object Name="Raven_Base Psionic Pistol" Inherits="BaseRifle">'
                    '    <part Name="Render" />'
                    '    <tag Name="DynamicObjectsTable:Guns" />'
                    '    <tag Name="BaseObject" Value="*noinherit" />'
                    "  </object>"
                    '  <object Name="Raven_Ice Psionic Pistol" Inherits="Raven_Base Psionic Pistol" />'
                    "</objects>"
                )
            ]
        )

        def eligible(name: str) -> bool:
            return (
                not i.has_tag(name, "BaseObject")
                and i.has_part(name, "Render")
                and not i.has_tag(name, "ExcludeFromDynamicEncounters")
            )

        self.assertFalse(eligible("Raven_Base Psionic Pistol"))
        self.assertTrue(eligible("Raven_Ice Psionic Pistol"))
        self.assertTrue(
            i.has_tag("Raven_Ice Psionic Pistol", "DynamicObjectsTable:Guns")
        )


class GuardPartSource(unittest.TestCase):
    def test_matching_assembly_source_proceeds(self) -> None:
        with snapshot("assembly:XRL.World.Parts"):
            self.assertIsNone(snapshot_qud_api.guard_part_source(ASSEMBLY))

    def test_matching_vanilla_source_proceeds(self) -> None:
        with snapshot("vanilla-xml"):
            self.assertIsNone(snapshot_qud_api.guard_part_source(None))

    def test_narrowing_is_refused_and_names_the_flag(self) -> None:
        """The write path in #244: 1605 part names down to 949, silently."""
        with snapshot("assembly:XRL.World.Parts"):
            message = snapshot_qud_api.guard_part_source(None)
        self.assertIsNotNone(message, "a narrowing run was allowed")
        self.assertIn("--assembly", message)
        self.assertIn("vanilla-xml", message)

    def test_widening_is_refused_too(self) -> None:
        """Refused in both directions: a snapshot built one way and checked the other is not a
        check, whichever way round it is."""
        with snapshot("vanilla-xml"):
            message = snapshot_qud_api.guard_part_source(ASSEMBLY)
        self.assertIsNotNone(message, "a widening run was allowed")
        self.assertIn("drop --assembly", message)

    def test_a_first_generation_has_nothing_to_disagree_with(self) -> None:
        """No snapshot on disk must not be an error, or the file could never be created."""
        with snapshot(None):
            self.assertIsNone(snapshot_qud_api.guard_part_source(None))
            self.assertIsNone(snapshot_qud_api.guard_part_source(ASSEMBLY))

    def test_an_unreadable_snapshot_does_not_block(self) -> None:
        """A broken snapshot is a reason to regenerate, not a reason to refuse to."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Path(root, "tools").mkdir()
            Path(root, "tools", "qud-api.json").write_text(
                "{ not json", encoding="utf-8"
            )
            with chdir(root):
                self.assertIsNone(snapshot_qud_api.guard_part_source(ASSEMBLY))

    def test_a_snapshot_without_the_key_does_not_block(self) -> None:
        with snapshot(None):
            Path("tools", "qud-api.json").write_text(
                json.dumps({"digest": "abc"}), encoding="utf-8"
            )
            self.assertIsNone(snapshot_qud_api.guard_part_source(ASSEMBLY))

    def test_the_guard_and_the_snapshot_agree_on_what_a_run_is(self) -> None:
        """part_source_for is the single definition build() uses, so the guard cannot compare
        against a label the file would never actually carry."""
        self.assertEqual(
            snapshot_qud_api.part_source_for(ASSEMBLY),
            f"assembly:{snapshot_qud_api.PART_NAMESPACE}",
        )
        self.assertEqual(snapshot_qud_api.part_source_for(None), "vanilla-xml")
        source = Path(snapshot_qud_api.__file__).read_text(encoding="utf-8")
        self.assertIn("part_source = part_source_for(assembly)", source)


@contextmanager
def stub(**attrs):
    """Replace module attributes for one test, restoring them afterwards."""
    previous = {k: getattr(snapshot_qud_api, k) for k in attrs}
    for k, v in attrs.items():
        setattr(snapshot_qud_api, k, v)
    try:
        yield
    finally:
        for k, v in previous.items():
            setattr(snapshot_qud_api, k, v)


def run_main(argv: list[str]) -> tuple[int, str]:
    out, err = io.StringIO(), io.StringIO()
    argv_previous = sys.argv
    sys.argv = ["snapshot_qud_api.py"] + argv
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = snapshot_qud_api.main()
    finally:
        sys.argv = argv_previous
    return code, out.getvalue() + err.getvalue()


class Unavailable(unittest.TestCase):
    def test_a_skip_passes_and_says_so(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = snapshot_qud_api.unavailable("no game", "install it", require=False)
        self.assertEqual(code, 0)
        self.assertIn("SKIPPED", out.getvalue())
        self.assertNotIn("OK", out.getvalue())

    def test_require_turns_the_skip_into_a_failure(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = snapshot_qud_api.unavailable("no game", "install it", require=True)
        self.assertEqual(code, 2)
        self.assertIn("ERROR", err.getvalue())


class NonLevelingMutations(unittest.TestCase):
    """#347. The list only exists inside the assembly, so its absence has to be loud.

    A mutation whose `CanLevel()` returns a constant false reads its level nowhere, which makes
    every grade of a chip granting it the same item. Neither `Mutations.xml` nor
    `HiddenMutations.xml` carries an attribute for it - `tools/dump_part_members.cs` decides it
    from two IL bytes - so the only protection against the list silently going missing is that
    `collect_members` refuses to return without it.
    """

    SNAPSHOT = Path(__file__).resolve().parent / "qud-api.json"

    def test_the_committed_snapshot_carries_it(self) -> None:
        api = json.loads(self.SNAPSHOT.read_text())
        listed = api["non_leveling_mutations"]
        self.assertEqual(api["counts"]["non_leveling_mutations"], len(listed))
        self.assertEqual(
            listed, sorted(listed), "the list must be sorted for a stable digest"
        )
        # The two the check exists for, and one that must not be caught by it.
        self.assertIn("Kindle", listed)
        self.assertIn("FrostWebs", listed)
        self.assertNotIn("Teleportation", listed)

    def test_every_name_is_a_real_mutation_class(self) -> None:
        api = json.loads(self.SNAPSHOT.read_text())
        catalogue = set(api["mutation_classes"])
        # The namespace holds classes the catalogue never declares, so this is a subset check
        # rather than equality - but a name in neither is a sign the dumper read the wrong thing.
        self.assertTrue(
            catalogue & set(api["non_leveling_mutations"]),
            "no non-levelling mutation is catalogued, which cannot be right",
        )

    def _collect(self, payload: dict) -> tuple:
        completed = mock.Mock(returncode=0, stdout=json.dumps(payload), stderr="")
        with (
            mock.patch.object(
                snapshot_qud_api.shutil, "which", return_value="/usr/bin/dotnet"
            ),
            mock.patch.object(snapshot_qud_api, "member_tfm", return_value="net8.0"),
            mock.patch.object(
                snapshot_qud_api.subprocess, "run", return_value=completed
            ),
        ):
            return snapshot_qud_api.collect_members(ASSEMBLY)

    def test_a_dumper_payload_without_the_list_fails(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            self._collect({"members": {"Armor": ["AV"]}, "part_builders": ["X"]})
        self.assertIn("CanLevel", str(caught.exception))

    def test_a_complete_payload_returns_all_three_lists(self) -> None:
        members, builders, unlevellable = self._collect(
            {
                "members": {"Armor": ["AV"]},
                "part_builders": ["X"],
                "non_leveling_mutations": ["Kindle", "Albino"],
            }
        )
        self.assertEqual(members, {"Armor": ["AV"]})
        self.assertEqual(builders, ["X"])
        self.assertEqual(unlevellable, ["Albino", "Kindle"], "returned unsorted")


class TemplateHints(unittest.TestCase):
    """#542. The citation that says which biomes deduplicate a scatter placement and which do not.

    `ZoneTemplates.xml` supplies a default `Hint` per population reference, and only a hinted
    placement runs `PlaceObjectInArea`'s same-blueprint check. The split is not something this fork
    can infer from its own XML, so `check_placement_hint` is only as good as this key.
    """

    SNAPSHOT = Path(__file__).resolve().parent / "qud-api.json"

    # The three that protect a scatter entry and the three that do not, verified by hand against
    # ZoneTemplates.xml. If a Qud update moves one of these, the check silently changes meaning.
    HINTED = ("HillsZoneGlobals", "MountainsZoneGlobals", "DesertCanyonZoneGlobals")
    UNHINTED = ("JungleZoneGlobals", "SaltMarshZoneGlobals", "BananaGroveZoneGlobals")

    def test_the_committed_snapshot_carries_it(self) -> None:
        api = json.loads(self.SNAPSHOT.read_text())
        hints = api["template_hints"]
        self.assertEqual(api["counts"]["template_hints"], len(hints))
        for table, supplied in hints.items():
            self.assertEqual(
                supplied,
                sorted(set(supplied)),
                f"{table} must be a sorted set for a stable digest",
            )

    def test_the_three_protected_biomes_supply_any(self) -> None:
        hints = json.loads(self.SNAPSHOT.read_text())["template_hints"]
        for table in self.HINTED:
            self.assertEqual(hints.get(table), ["Any"], table)

    def test_the_three_unprotected_biomes_supply_nothing(self) -> None:
        """The empty string is the citation. Omitting the table instead would be
        indistinguishable from a table no template names, which wants the opposite response."""
        hints = json.loads(self.SNAPSHOT.read_text())["template_hints"]
        for table in self.UNHINTED:
            self.assertEqual(hints.get(table), [""], table)

    def test_a_game_without_the_file_yields_nothing_rather_than_raising(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(snapshot_qud_api.collect_template_hints(Path(tmp)), {})

    def test_a_hint_reaches_a_table_nested_under_the_one_named(self) -> None:
        """The regression this key was rewritten for (#173).

        The four ruins templates name `RuinsZoneGlobals-Surface` with `Hint="Any"`, and the
        vegetation this fork merges into sits one level below that. Reading only what a template
        names directly recorded nothing for it, so `check_placement_hint` skipped the merge in
        silence - a check that cannot fire, found by the first content to rely on it.

        `PopulationTable.Generate` ends `Population.Generate(Result, Vars, Hint ?? DefaultHint)`,
        so the hint follows the reference down.
        """
        self.assertEqual(
            self._hints(
                templates='<population Table="Root" Hint="Any"></population>',
                tables=(
                    '<population Name="Root"><table Name="Nested" /></population>'
                    '<population Name="Nested"><object Blueprint="X" /></population>'
                ),
                wanted={"Nested"},
            ),
            {"Nested": ["Any"]},
        )

    def test_a_reference_carrying_its_own_hint_overrides_the_one_above(self) -> None:
        self.assertEqual(
            self._hints(
                templates='<population Table="Root" Hint="Any"></population>',
                tables=(
                    '<population Name="Root"><table Name="Nested" Hint="AlongWall" /></population>'
                    '<population Name="Nested"><object Blueprint="X" /></population>'
                ),
                wanted={"Nested"},
            ),
            {"Nested": ["AlongWall"]},
        )

    def test_two_routes_that_disagree_are_both_recorded(self) -> None:
        """A table is only safe if every way in carries a hint, so the unhinted route has to
        survive into the citation rather than being masked by the hinted one."""
        self.assertEqual(
            self._hints(
                templates=(
                    '<population Table="RootA" Hint="Any"></population>'
                    '<population Table="RootB"></population>'
                ),
                tables=(
                    '<population Name="RootA"><table Name="Nested" /></population>'
                    '<population Name="RootB"><table Name="Nested" /></population>'
                    '<population Name="Nested"><object Blueprint="X" /></population>'
                ),
                wanted={"Nested"},
            ),
            {"Nested": ["", "Any"]},
        )

    def test_a_reference_cycle_terminates(self) -> None:
        self.assertEqual(
            self._hints(
                templates='<population Table="Root" Hint="Any"></population>',
                tables=(
                    '<population Name="Root"><table Name="Nested" /></population>'
                    '<population Name="Nested"><table Name="Root" /></population>'
                ),
                wanted={"Nested"},
            ),
            {"Nested": ["Any"]},
        )

    @staticmethod
    def _hints(templates: str, tables: str, wanted: set[str]) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp)
            (game / "ZoneTemplates.xml").write_text(
                f"<zonetemplates><zonetemplate Name='T'>{templates}</zonetemplate></zonetemplates>"
            )
            (game / "PopulationTables.xml").write_text(
                f"<populations>{tables}</populations>"
            )
            with mock.patch.object(
                snapshot_qud_api, "merged_record_names", return_value=([], wanted)
            ):
                return snapshot_qud_api.collect_template_hints(game)


class MissingDependencies(unittest.TestCase):
    """The hook must be harmless on a machine without the game."""

    def test_check_skips_when_the_game_is_absent(self) -> None:
        with snapshot("assembly:XRL.World.Parts"), stub(find_game=lambda _: None):
            code, text = run_main(["--check", "--assembly"])
        self.assertEqual(code, 0, "an absent game blocked the hook")
        self.assertIn("SKIPPED", text)

    def test_check_require_fails_when_the_game_is_absent(self) -> None:
        with snapshot("assembly:XRL.World.Parts"), stub(find_game=lambda _: None):
            code, text = run_main(["--check", "--assembly", "--require"])
        self.assertEqual(code, 2)
        self.assertIn("ERROR", text)

    def test_a_write_never_skips(self) -> None:
        """A regeneration that quietly does nothing and returns 0 is how a snapshot comes to be
        believed current when it was never rebuilt."""
        with snapshot("assembly:XRL.World.Parts"), stub(find_game=lambda _: None):
            code, text = run_main(["--assembly"])
        self.assertEqual(code, 2, "a write skipped instead of failing")
        self.assertIn("regenerate", text)
        self.assertNotIn("SKIPPED", text)


class StaleIsNotASkip(unittest.TestCase):
    """The other half of the invariant: a stale snapshot is a finding, not an unavailability."""

    def test_a_stale_snapshot_blocks(self) -> None:
        fake = Path("/fake/Assembly-CSharp.dll")
        built = {
            "digest": "different-from-committed",
            "counts": {"parts": 1, "blueprints": 1, "members": 1},
        }
        with (
            snapshot("assembly:XRL.World.Parts"),
            stub(
                find_game=lambda _: Path("/fake/Base"),
                find_assembly=lambda _: fake,
                build=lambda *a, **k: built,
            ),
            mock.patch.object(
                snapshot_qud_api.shutil, "which", lambda _: "/fake/ilspycmd"
            ),
        ):
            code, text = run_main(["--check", "--assembly"])
        self.assertEqual(code, 1, "a stale snapshot did not block")
        self.assertIn("STALE", text)
        self.assertNotIn("SKIPPED", text)


class TagFormsAbsent(unittest.TestCase):
    """#507. `tag_forms` is keyed on the tag names this mod writes, so adding one leaves the
    snapshot incomplete - and "not in tag_forms" used to mean both "vanilla has no opinion" and
    "the snapshot has never seen this". Recording the reason is what lets validate_mod tell those
    apart without needing the game.
    """

    SNAPSHOT = Path(__file__).resolve().parent / "qud-api.json"

    def api(self) -> dict:
        return json.loads(self.SNAPSHOT.read_text())

    def test_the_committed_snapshot_carries_it(self) -> None:
        api = self.api()
        absent = api["tag_forms_absent"]
        self.assertEqual(api["counts"]["tag_forms_absent"], len(absent))
        self.assertEqual(set(absent.values()) - {"both", "absent"}, set())

    def test_the_two_reasons_are_recorded_separately(self) -> None:
        """They are not the same fact. `Fiber` has a vanilla usage that simply disagrees with
        itself; `Vixy_CreatureVariant` has none at all, and only this fork's C# reads it."""
        absent = self.api()["tag_forms_absent"]
        self.assertEqual(absent.get("Fiber"), "both")
        self.assertEqual(absent.get("Vixy_CreatureVariant"), "absent")

    def test_no_name_is_in_both_sections(self) -> None:
        """A name with a form has an opinion; one here has none. Both would make the coverage
        check pass for the wrong reason."""
        api = self.api()
        self.assertEqual(set(api["tag_forms"]) & set(api["tag_forms_absent"]), set())

    def test_together_they_cover_every_tag_name_this_mod_writes(self) -> None:
        """The invariant check_snapshot_coverage enforces, asserted here against the real mod so
        the two cannot drift apart silently."""
        mod = Path(__file__).resolve().parent.parent / "mod" / "ObjectBlueprints"
        written = {
            child.get("Name")
            for f in sorted(mod.glob("*.xml"))
            for obj in snapshot_qud_api.parse(f, lenient=True).iter("object")
            for child in obj
            if child.tag in ("tag", "stag") and child.get("Name")
        }
        api = self.api()
        self.assertEqual(
            written - set(api["tag_forms"]) - set(api["tag_forms_absent"]), set()
        )


if __name__ == "__main__":
    unittest.main()
