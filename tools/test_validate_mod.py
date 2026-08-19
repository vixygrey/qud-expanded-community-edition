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

import os
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

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
        (mod / "PopulationTables.xml").write_text(
            f'<?xml version="1.0" encoding="utf-8" ?>\n<population>\n{tables}\n</population>\n',
            encoding="utf-8",
        )
    return mod


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


class Constants(unittest.TestCase):
    def test_covers_every_prefix_the_validator_claims(self) -> None:
        """The tie between the tests' own list and the real constant.

        If a prefix is added to the validator and not to COVERED_PREFIXES, the tests above would
        never exercise it and would still pass. This is the one assertion that notices.
        """
        self.assertEqual(set(validate_mod.MOD_PREFIXES), set(COVERED_PREFIXES))


if __name__ == "__main__":
    unittest.main()
