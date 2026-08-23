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
            "  </object>",
        )
        self.assertTrue(items, "a Shield part's AV was not checked")
        self.assertIn("Shield slot", items[0][1])

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
