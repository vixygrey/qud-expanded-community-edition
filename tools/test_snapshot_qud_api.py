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


if __name__ == "__main__":
    unittest.main()
