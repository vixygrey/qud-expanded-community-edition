#!/usr/bin/env python3
"""Tests for tools/check_docs.py.

`check_changelog_sections`, because it is the check with a history: the same defect
has reached `main` twice — two `### Fixed` blocks corrected by hand before 2.4.0, then two
`### Added` blocks in #236 — and the hand-fix is precisely what failed to prevent the second. A
guard against a recurring defect is worth a test that watches it fire.

And `check_vanilla_figures`, because #242 widened it to read the mod's own XML comments. That
widening is the entire fix - the figure that drifted was in `Ammo.xml`, which nothing had ever
read - so a test that proves an XML comment is actually reached is the test that proves the fix.

Both directions, per docs/LESSONS.md: a check is only proven by seeing it report something broken
AND stay quiet on something sound. Synthetic files in a temp directory; no network, no
dependencies.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_docs


@contextmanager
def chdir(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def findings_for(changelog: str) -> list[tuple[str, str]]:
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "CHANGELOG.md").write_text(changelog, encoding="utf-8")
        with chdir(Path(tmp)):
            f = check_docs.Findings()
            check_docs.check_changelog_sections(f)
            return f.items


CLEAN = """# Changelog

## [Unreleased]

### Added

- something

### Fixed

- something else

## [1.0.0] - 2026-01-01

### Added

- the first thing
"""


CHIP_BLUEPRINT = """<objects>
  <object Name="Raven_Test Chip">
    <part Name="Render" DisplayName="basic {{K|test}} chip" />
    <part Name="Commerce" Value="20" />
    <part Name="Raven_ModTesting" Tier="2" />
    <tag Name="Tier" Value="4" />
  </object>
</objects>
"""

CHIP_SCRIPT = "public class Raven_ModTesting : ModImprovedMutationBase<Testing> { }"


def appendix_findings(row: str) -> list[tuple[str, str]]:
    """Run check_appendix_b over a one-chip fixture with the given table row."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "mod" / "ObjectBlueprints").mkdir(parents=True)
        (root / "mod" / "Scripting").mkdir(parents=True)
        (root / "docs").mkdir()
        (root / "mod" / "ObjectBlueprints" / "Chips.xml").write_text(
            CHIP_BLUEPRINT, encoding="utf-8"
        )
        (root / "mod" / "Scripting" / "Raven_ModTesting.cs").write_text(
            CHIP_SCRIPT, encoding="utf-8"
        )
        (root / "docs" / "FEATURES.md").write_text(
            "## Appendix B\n\n"
            "| Chip | Item tier | Value | Grants (mutation @ level) |\n"
            "|---|---|---|---|\n" + row + "\n",
            encoding="utf-8",
        )
        with chdir(root):
            f = check_docs.Findings()
            check_docs.check_appendix_b(f)
            return f.items


class AppendixB(unittest.TestCase):
    """#230. The document asserts 144 rows of data nobody recomputes.

    Three of them still named GasGeneration months after #258 renamed it, and I corrected the
    three single-chip rows while missing the three chipsets on the same pass - which is the
    argument for a check rather than another careful read.
    """

    def test_a_matching_row_passes(self) -> None:
        self.assertEqual(
            appendix_findings("| basic test chip | 4 | 20 | Testing @ 2 |"), []
        )

    def test_a_wrong_item_tier_is_reported(self) -> None:
        codes = appendix_findings("| basic test chip | 6 | 20 | Testing @ 2 |")
        self.assertTrue(codes, "a wrong item tier must be reported")
        self.assertIn("item tier", codes[0][1])

    def test_a_wrong_value_is_reported(self) -> None:
        codes = appendix_findings("| basic test chip | 4 | 40 | Testing @ 2 |")
        self.assertTrue(codes)
        self.assertIn("value", codes[0][1])

    def test_a_stale_mutation_name_is_reported(self) -> None:
        """The real defect: a class renamed in the code, not in the table."""
        codes = appendix_findings("| basic test chip | 4 | 20 | Tested @ 2 |")
        self.assertTrue(codes)
        self.assertIn("grants", codes[0][1])

    def test_a_wrong_mutation_level_is_reported(self) -> None:
        codes = appendix_findings("| basic test chip | 4 | 20 | Testing @ 9 |")
        self.assertTrue(codes)

    def test_a_row_naming_no_blueprint_is_reported(self) -> None:
        codes = appendix_findings("| basic ghost chip | 4 | 20 | Testing @ 2 |")
        self.assertTrue(codes)
        self.assertIn("no blueprint renders as", codes[0][1])

    def test_a_chip_with_no_row_is_reported(self) -> None:
        codes = appendix_findings("| unrelated | 1 | 1 | x |")
        self.assertTrue(any("no row for" in d for _, d in codes))

    def test_colour_markup_is_stripped_before_matching(self) -> None:
        """The document writes plain names; the blueprint writes {{K|markup}}."""
        self.assertEqual(check_docs._plain("basic {{K|test}} chip"), "basic test chip")


class ChangelogSections(unittest.TestCase):
    def test_a_well_formed_changelog_is_quiet(self) -> None:
        self.assertEqual(findings_for(CLEAN), [])

    def test_a_repeated_section_in_one_release_is_reported(self) -> None:
        """The exact shape that reached main twice."""
        broken = CLEAN.replace(
            "### Fixed\n\n- something else",
            "### Added\n\n- a second Added block",
        )
        items = findings_for(broken)
        self.assertTrue(items, "a duplicate section was not reported")
        self.assertEqual(items[0][0], "changelog-sections")
        self.assertIn("second '### Added'", items[0][1])

    def test_the_same_section_in_different_releases_is_fine(self) -> None:
        """The boundary. Every release has its own Added; only repeats *within* one are wrong."""
        self.assertEqual(
            [i for i in findings_for(CLEAN) if "second" in i[1]],
            [],
            "sections were compared across releases rather than within one",
        )

    def test_a_non_keep_a_changelog_section_is_reported(self) -> None:
        broken = CLEAN.replace("### Fixed", "### Internal — tooling", 1)
        items = findings_for(broken)
        self.assertTrue(items, "a non-standard section name was not reported")
        self.assertIn("Internal", items[0][1])

    def test_every_keep_a_changelog_name_is_accepted(self) -> None:
        """A false positive here would block a legitimate entry, so prove all six pass."""
        body = "# Changelog\n\n## [1.0.0] - 2026-01-01\n\n" + "\n".join(
            f"### {name}\n\n- entry\n" for name in check_docs.CHANGELOG_SECTIONS
        )
        self.assertEqual(findings_for(body), [])

    def test_headings_before_any_release_are_ignored(self) -> None:
        """The document's own preamble has prose headings that are not release sections."""
        body = "# Changelog\n\n### Notes\n\nSome preamble.\n\n## [1.0.0] - 2026-01-01\n\n### Added\n\n- entry\n"
        self.assertEqual(findings_for(body), [])

    def test_a_missing_changelog_is_not_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, chdir(Path(tmp)):
            f = check_docs.Findings()
            check_docs.check_changelog_sections(f)
            self.assertEqual(f.items, [])


SNAPSHOT = {
    "figures": {
        "creature-blueprints": "897",
        "creature-blueprints-bleeding": "813",
        "creature-rustable": "169",
        "humanoid-blueprints": "340",
        "humanoid-rustable": "134",
        "humanoid-rust-dead": "202",
    }
}


def figure_findings(files: dict[str, str]) -> list[tuple[str, str]]:
    """Run check_vanilla_figures over a synthetic tree. Keys are repo-relative paths."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        Path(root, "tools").mkdir()
        Path(root, "tools", "qud-api.json").write_text(
            json.dumps(SNAPSHOT), encoding="utf-8"
        )
        for name, body in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        with chdir(root):
            f = check_docs.Findings()
            check_docs.check_vanilla_figures(f)
            return f.items


class VanillaFiguresInModXml(unittest.TestCase):
    """The #242 widening: figures quoted in the mod's XML comments are read too."""

    XML = "<objects>\n  <!-- {} -->\n</objects>\n"

    def test_a_correct_figure_in_an_xml_comment_is_quiet(self) -> None:
        body = self.XML.format("813 of 897 creature blueprints bleed, robots included.")
        self.assertEqual(figure_findings({"mod/ObjectBlueprints/Ammo.xml": body}), [])

    def test_a_wrong_figure_in_an_xml_comment_is_reported(self) -> None:
        """The exact shape that shipped: a denominator nothing could recompute."""
        body = self.XML.format("813 of 908 creature blueprints bleed, robots included.")
        items = figure_findings({"mod/ObjectBlueprints/Ammo.xml": body})
        self.assertTrue(items, "a wrong figure in an XML comment was not reported")
        self.assertEqual(items[0][0], "vanilla-figure")
        self.assertIn("908", items[0][1])
        self.assertIn("897", items[0][1])

    def test_mod_xml_is_reached_at_any_depth(self) -> None:
        body = self.XML.format("169 of 908 creature blueprints have a rustable item")
        self.assertTrue(
            figure_findings({"mod/deeply/nested/Thing.xml": body}),
            "rglob did not reach a nested mod file",
        )

    def test_documents_are_still_checked(self) -> None:
        """Widening the set must not have replaced it."""
        self.assertTrue(
            figure_findings(
                {"docs/FEATURES.md": "813 of 908 creature blueprints bleed"}
            ),
            "a document stopped being read when mod XML started being read",
        )

    def test_figure_sources_follow_the_working_directory(self) -> None:
        """Globbed per call, not at import - otherwise the list is whatever cwd was on load."""
        with tempfile.TemporaryDirectory() as tmp, chdir(Path(tmp)):
            self.assertEqual(
                [p for p in check_docs.figure_sources() if p.suffix == ".xml"], []
            )
            Path("mod").mkdir()
            Path("mod", "Later.xml").write_text("<objects />", encoding="utf-8")
            self.assertIn(
                Path("mod/Later.xml"),
                check_docs.figure_sources(),
                "a file created after import was not picked up",
            )

    def test_a_claim_naming_an_unknown_figure_is_reported(self) -> None:
        """A claim whose figure is missing from the snapshot must fail loudly, not skip."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Path(root, "tools").mkdir()
            Path(root, "tools", "qud-api.json").write_text(
                json.dumps({"figures": {"creature-blueprints": "897"}}),
                encoding="utf-8",
            )
            Path(root, "docs").mkdir()
            Path(root, "docs", "FEATURES.md").write_text(
                "813 of 897 creature blueprints bleed", encoding="utf-8"
            )
            with chdir(root):
                f = check_docs.Findings()
                check_docs.check_vanilla_figures(f)
            self.assertTrue(f.items, "a missing figure was silently skipped")
            self.assertIn("creature-blueprints-bleeding", f.items[0][1])


class CheckNameSources(unittest.TestCase):
    """check_docs.py emits named checks; leaving itself out of its own sources is the trap its
    comment warns about, and #242 walked into it."""

    def test_this_scripts_own_check_names_are_known(self) -> None:
        import re

        emitted = set(
            re.findall(
                r'f\.add\(\s*"([a-z-]+)"',
                Path(check_docs.__file__).read_text(encoding="utf-8"),
            )
        )
        self.assertIn(
            "vanilla-figure", emitted, "the fixture no longer matches the source"
        )
        f = check_docs.Findings()
        check_docs.check_check_names(f)
        self.assertEqual(
            [i for i in f.items if "vanilla-figure" in i[1]],
            [],
            "check_docs.py cannot see the check names it emits itself",
        )


class HumanoidCensusClaims(unittest.TestCase):
    """The humanoid subset shares a denominator-shaped phrasing with the whole-bestiary claims,
    which is exactly how a figure gets quoted against the wrong population."""

    def test_a_correct_humanoid_figure_is_quiet(self) -> None:
        self.assertEqual(
            figure_findings(
                {
                    "docs/FEATURES.md": "134 of 340 humanoid creature blueprints have a "
                    "rustable item"
                }
            ),
            [],
        )

    def test_a_humanoid_count_against_the_bestiary_denominator_is_reported(
        self,
    ) -> None:
        """The failure this pattern pair exists to catch."""
        items = figure_findings(
            {
                "docs/FEATURES.md": "134 of 897 humanoid creature blueprints have a "
                "rustable item"
            }
        )
        self.assertTrue(items, "a humanoid count against the wrong denominator passed")
        self.assertIn("340", items[0][1])

    def test_the_creature_pattern_does_not_swallow_a_humanoid_sentence(self) -> None:
        """`(\\d+) creature blueprints` requires the digits adjacent to `creature`, so the word
        `humanoid` in between keeps the two claims apart. If that ever stops holding, 134 would be
        compared against creature-rustable (169) and this goes red."""
        self.assertEqual(
            figure_findings(
                {
                    "mod/ObjectBlueprints/Ammo.xml": "<objects><!-- 134 of 340 humanoid "
                    "creature blueprints have a rustable item --></objects>"
                }
            ),
            [],
            "a humanoid sentence was matched by the whole-bestiary pattern",
        )

    def test_both_populations_can_be_quoted_in_one_document(self) -> None:
        self.assertEqual(
            figure_findings(
                {
                    "docs/FEATURES.md": "169 of 897 creature blueprints have a rustable item, "
                    "but 134 of 340 humanoid creature blueprints have a rustable item"
                }
            ),
            [],
        )


class WrappedClaims(unittest.TestCase):
    """A pattern with a literal space stops matching when prose reflows, and reports nothing while
    doing it - the check failing in exactly the way it exists to prevent. Every census claim was
    unbound in `docs/FEATURES.md` for this reason before `wrapped` existed."""

    def test_a_claim_survives_a_line_break(self) -> None:
        wrapped_text = "**134 of 340 humanoid creature blueprints have\na rustable item**, against 202 that do not."
        self.assertEqual(figure_findings({"docs/FEATURES.md": wrapped_text}), [])

    def test_a_wrong_figure_is_still_caught_across_a_line_break(self) -> None:
        """Tolerating the wrap must not have turned the check into one that always passes."""
        items = figure_findings(
            {
                "docs/FEATURES.md": "134 of 897 humanoid creature blueprints have\na rustable item"
            }
        )
        self.assertTrue(items, "a wrong figure survived because the sentence wrapped")
        self.assertIn("340", items[0][1])

    def test_wrapped_joins_on_whitespace(self) -> None:
        self.assertEqual(check_docs.wrapped("a b c"), r"a\s+b\s+c")


if __name__ == "__main__":
    unittest.main()
