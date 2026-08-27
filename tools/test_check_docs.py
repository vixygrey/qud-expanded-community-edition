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
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

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


# Two blueprints under one display name, differing only by item tier - the #347 shape, where
# Kindle and Frost Webs each collapsed onto a single name because every grade grants the same thing.
CHIP_BLUEPRINT_SHARED_NAME = """<objects>
  <object Name="Raven_Test Chip">
    <part Name="Render" DisplayName="basic {{K|test}} chip" />
    <part Name="Commerce" Value="20" />
    <part Name="Raven_ModTesting" Tier="2" />
    <tag Name="Tier" Value="4" />
  </object>
  <object Name="Raven_Improved Test Chip">
    <part Name="Render" DisplayName="basic {{K|test}} chip" />
    <part Name="Commerce" Value="20" />
    <part Name="Raven_ModTesting" Tier="2" />
    <tag Name="Tier" Value="6" />
  </object>
</objects>
"""


def appendix_findings(
    row: str, blueprint: str = CHIP_BLUEPRINT
) -> list[tuple[str, str]]:
    """Run check_appendix_b over a chip fixture with the given table row."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "mod" / "ObjectBlueprints").mkdir(parents=True)
        (root / "mod" / "Scripting").mkdir(parents=True)
        (root / "docs").mkdir()
        (root / "mod" / "ObjectBlueprints" / "Chips.xml").write_text(
            blueprint, encoding="utf-8"
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
        """The tier is half the key now, so a wrong one reads as an unmatched row."""
        codes = appendix_findings("| basic test chip | 6 | 20 | Testing @ 2 |")
        self.assertTrue(codes, "a wrong item tier must be reported")
        self.assertIn("at item tier 6", codes[0][1])

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

    def test_two_blueprints_may_share_a_display_name(self) -> None:
        """#347. Keyed on the name alone, the second blueprint used to overwrite the first, and
        the appendix could describe only whichever parsed last."""
        rows = (
            "| basic test chip | 4 | 20 | Testing @ 2 |\n"
            "| basic test chip | 6 | 20 | Testing @ 2 |"
        )
        self.assertEqual(appendix_findings(rows, CHIP_BLUEPRINT_SHARED_NAME), [])

    def test_a_shared_name_still_needs_a_row_per_tier(self) -> None:
        codes = appendix_findings(
            "| basic test chip | 4 | 20 | Testing @ 2 |", CHIP_BLUEPRINT_SHARED_NAME
        )
        self.assertTrue(
            any("no row for" in d and "item tier 6" in d for _, d in codes),
            "the tier that has no row must be named",
        )

    def test_colour_markup_is_stripped_before_matching(self) -> None:
        """The document writes plain names; the blueprint writes {{K|markup}}."""
        self.assertEqual(check_docs._plain("basic {{K|test}} chip"), "basic test chip")


ITEM_BLUEPRINTS = """<objects>
  <object Name="Raven_Test Blade" Inherits="BaseDagger">
    <part Name="Render" DisplayName="{{y|test blade}}" />
    <part Name="Commerce" Value="40" />
    <part Name="Physics" Weight="3" />
    <tag Name="Tier" Value="3" />
  </object>
  <object Name="Vanillaish Blade" Load="Merge">
    <part Name="Commerce" Value="80" />
  </object>
</objects>
"""

ITEM_HEADER = (
    "| Blueprint | New? | Tier | Damage | Pen | Max STR | Stat | Value | Weight | 2-slot |\n"
    "|---|---|---|---|---|---|---|---|---|---|\n"
)


def item_findings(row: str) -> list[tuple[str, str]]:
    """Run check_item_tables over a one-blueprint fixture with the given table row."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "mod" / "ObjectBlueprints").mkdir(parents=True)
        (root / "docs").mkdir()
        (root / "mod" / "ObjectBlueprints" / "Items.xml").write_text(
            ITEM_BLUEPRINTS, encoding="utf-8"
        )
        (root / "docs" / "FEATURES.md").write_text(
            "### 6.1 Test\n\n" + ITEM_HEADER + row + "\n", encoding="utf-8"
        )
        with chdir(root):
            f = check_docs.Findings()
            check_docs.check_item_tables(f)
            return f.items


class ItemTables(unittest.TestCase):
    """#287. 254 rows of typed figures that nothing recomputed, and they were worse than stale.

    Nine cells disagreed with their blueprints when this first ran. Four were fixes from #86 that
    reached the blueprint and the §10 row recording them but never the table. The other five - the
    low-tier wristblades - had been wrong since the original import and had never once been right,
    which is not drift: drift implies a moment when the document was true (#299).
    """

    def test_a_matching_row_passes(self) -> None:
        row = "| Raven_Test Blade | new | 3 | 1d3 | +0 | 4 | (inh) | 40 | 3 |  |"
        self.assertEqual(item_findings(row), [])

    def test_a_wrong_value_is_reported(self) -> None:
        codes = item_findings(
            "| Test Blade | new | 3 | 1d3 | +0 | 4 | (inh) | 55 | 3 |  |"
        )
        self.assertTrue(codes, "a wrong value must be reported")
        self.assertIn("value", codes[0][1])

    def test_a_wrong_tier_is_reported(self) -> None:
        codes = item_findings(
            "| Test Blade | new | 7 | 1d3 | +0 | 4 | (inh) | 40 | 3 |  |"
        )
        self.assertTrue(codes)
        self.assertIn("tier", codes[0][1])

    def test_a_wrong_weight_is_reported(self) -> None:
        codes = item_findings(
            "| Test Blade | new | 3 | 1d3 | +0 | 4 | (inh) | 40 | 9 |  |"
        )
        self.assertTrue(codes)
        self.assertIn("weight", codes[0][1])

    def test_the_prefix_may_be_dropped(self) -> None:
        """`Fullerite Greathammer` in the table is `Raven_Fullerite Greathammer` in the XML.

        Written as a mismatch rather than a match: a match would also pass if the name failed to
        resolve, because an unresolved row yields no comparison either. Only a reported mismatch
        proves the prefix-dropped name actually reached the blueprint.
        """
        row = "| Test Blade | new | 3 | 1d3 | +0 | 4 | (inh) | 55 | 3 |  |"
        codes = item_findings(row)
        self.assertTrue(codes, "the prefix-dropped name must resolve")
        self.assertIn("Raven_Test Blade", codes[0][1])

    def test_colour_markup_is_stripped_before_matching(self) -> None:
        codes = item_findings(
            "| test blade | new | 3 | 1d3 | +0 | 4 | (inh) | 55 | 3 |  |"
        )
        self.assertTrue(codes, "the display name must resolve too")

    def test_a_row_naming_no_blueprint_is_reported(self) -> None:
        codes = item_findings(
            "| Nothing Here | new | 3 | 1d3 | +0 | 4 | (inh) | 40 | 3 |  |"
        )
        self.assertTrue(codes)
        self.assertIn("no blueprint resolves", codes[0][1])

    def test_a_figure_the_mod_never_declares_is_skipped(self) -> None:
        """Not silence about a mismatch - silence about a figure that lives in the game's files.

        `Flawless Crysteel Boots` is the real case: #86 corrected its tier by *removing* the mod's
        override so vanilla's would apply, which is exactly what puts it beyond a mod-only check.
        """
        row = "| Vanillaish Blade | merge | 6 | 1d3 | +0 | 4 | (inh) | 80 | 5 |  |"
        self.assertEqual(
            item_findings(row), [], "tier and weight are not in the mod's XML"
        )

    def test_a_merge_that_declares_a_figure_is_still_checked(self) -> None:
        """The assumption this check was not built on for months, and it was wrong."""
        row = "| Vanillaish Blade | merge | 6 | 1d3 | +0 | 4 | (inh) | 99 | 5 |  |"
        codes = item_findings(row)
        self.assertTrue(codes, "a merge declaring Value must still be compared")
        self.assertIn("value", codes[0][1])

    def test_an_em_dash_is_not_a_figure(self) -> None:
        row = "| Test Blade | new | 3 | 1d3 | +0 | 4 | (inh) | \u2014 | 3 |  |"
        self.assertEqual(item_findings(row), [])


class GitHubAnchors(unittest.TestCase):
    """The slug is a reimplementation of someone else's rule, so the awkward shapes are pinned.

    All five below are real headings this wiki links to. If GitHub ever changes how it derives an
    anchor, these are what should fail rather than the whole check going quietly wrong.
    """

    def test_a_numbered_heading_drops_its_dots(self) -> None:
        self.assertEqual(check_docs.github_anchor("## 6.3 Armor"), "63-armor")

    def test_an_em_dash_leaves_a_double_hyphen(self) -> None:
        """The two spaces around the dash survive as hyphens; the dash itself does not."""
        self.assertEqual(
            check_docs.github_anchor("## Appendix B \u2014 every psionic chip"),
            "appendix-b--every-psionic-chip",
        )

    def test_backticked_code_keeps_its_text(self) -> None:
        self.assertEqual(
            check_docs.github_anchor("## 7. Loot tables (`PopulationTables.xml`)"),
            "7-loot-tables-populationtablesxml",
        )

    def test_a_lettered_subsection(self) -> None:
        self.assertEqual(
            check_docs.github_anchor("### 1.0b `<removetable>` \u2014 the tool"),
            "10b-removetable--the-tool",
        )

    def test_duplicate_headings_are_suffixed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp, "D.md")
            doc.write_text("## Same\n\n## Same\n", encoding="utf-8")
            self.assertEqual(check_docs.anchors_of(doc), {"same", "same-1"})


class WikiLinks(unittest.TestCase):
    """#230. A renamed heading breaks every wiki link to it, silently from both sides."""

    def _findings(
        self, page: str, doc: str = "## 13.1 What each option does\n"
    ) -> list:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "FEATURES.md").write_text(doc, encoding="utf-8")
            wiki = root / "wiki"
            wiki.mkdir()
            (wiki / "Page.md").write_text(page, encoding="utf-8")
            with chdir(root):
                f = check_docs.Findings()
                check_docs.check_wiki_links(wiki, f)
                return f.items

    LINK = (
        "see [the options](https://github.com/vixygrey/qud-expanded-community-edition"
        "/blob/main/docs/FEATURES.md#131-what-each-option-does)"
    )

    def test_a_resolving_anchor_passes(self) -> None:
        self.assertEqual(self._findings(self.LINK), [])

    def test_a_renamed_heading_is_reported(self) -> None:
        found = self._findings(self.LINK, doc="## 13.1 What each option covers\n")
        self.assertTrue(found, "a renamed heading must break the link")
        self.assertIn("anchors there", found[0][1])

    def test_a_missing_target_file_is_reported(self) -> None:
        page = self.LINK.replace("docs/FEATURES.md", "docs/GONE.md")
        found = self._findings(page)
        self.assertTrue(found)
        self.assertIn("does not exist", found[0][1])

    def test_a_link_without_a_fragment_is_not_checked(self) -> None:
        page = (
            "[features](https://github.com/vixygrey/qud-expanded-community-edition"
            "/blob/main/docs/FEATURES.md)"
        )
        self.assertEqual(self._findings(page), [])


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


class CheckNameRegistry(unittest.TestCase):
    """#402. The reverse direction was never checked, so a new check could ship unlisted.

    That is the quieter half: a documented name that does not exist is loud the moment anyone
    follows it, but an emitted name nobody documented is silent — the registry simply reads as
    complete. Fifteen names had accumulated that way.
    """

    def test_the_registry_parses_and_is_not_empty(self) -> None:
        """Guards against the vacuous pass: if the section heading ever moves, an empty set would
        make every emitted name a finding, and a None would make none of them one."""
        names = check_docs.registered_check_names()
        self.assertIsNotNone(names, "docs/STYLEGUIDE.md §10.1 could not be parsed")
        self.assertGreater(len(names), 40)
        self.assertIn("item-curve", names)
        self.assertIn("appendix-b", names)

    def test_the_registry_does_not_swallow_the_table_above_it(self) -> None:
        """§10 maps rules to enforcers and names things that are not checks — `ruff`, `prettier`,
        `gitleaks`. Parsing from the heading rather than the whole section keeps them out."""
        names = check_docs.registered_check_names()
        for not_a_check in ("ruff", "prettier", "gitleaks", "typos"):
            self.assertNotIn(not_a_check, names)

    def test_the_repository_agrees_with_itself_today(self) -> None:
        f = check_docs.Findings()
        check_docs.check_check_names(f)
        self.assertEqual([i for i in f.items if i[0] == "check-names"], [])

    def _with_registry(self, names: list[str]) -> list[str]:
        """Run the check against a synthetic registry holding exactly `names`."""
        rows = "\n".join(f"| `{n}` | `validate_mod.py` | x |" for n in names)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "tools").mkdir()
            (root / "docs" / "STYLEGUIDE.md").write_text(
                "### 10.1 Every check name\n\n| Check | Emitted by | What |\n|---|---|---|\n"
                + rows
                + "\n\n### 10.2 After\n",
                encoding="utf-8",
            )
            for source in ("validate_mod.py", "check_build_log.py", "check_docs.py"):
                (root / "tools" / source).write_text(
                    'f.add("real-check", "x")\n', encoding="utf-8"
                )
            with chdir(root):
                f = check_docs.Findings()
                check_docs.check_check_names(f)
                return [d for _, d in f.items]

    def test_an_emitted_name_missing_from_the_registry_is_reported(self) -> None:
        found = self._with_registry(["something-else"])
        self.assertTrue(any("emits the check 'real-check'" in d for d in found))

    def test_a_registered_name_nothing_emits_is_reported(self) -> None:
        found = self._with_registry(["real-check", "imaginary-check"])
        self.assertTrue(any("'imaginary-check'" in d for d in found))

    def test_agreement_is_quiet(self) -> None:
        self.assertEqual(self._with_registry(["real-check"]), [])


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

    def test_every_counted_claim_pattern_is_wrapped_by_the_loop(self) -> None:
        """Wrapping is applied centrally, so a new pattern cannot be written unwrapped by
        accident. 19 of the 29 patterns were literal-space before #422, and one of them had
        already gone silent across a reflow."""
        source = Path("tools/check_docs.py").read_text()
        self.assertEqual(
            source.count("re.finditer(wrapped(pattern), text)"),
            4,
            "check_counts, check_vanilla_figures, check_wiki_counts and check_workshop_counts "
            "must all wrap the pattern - this count rising is a new loop that has to opt in "
            "deliberately",
        )


class ClaimCoverage(unittest.TestCase):
    """A pattern matching nothing passes silently, because `re.finditer` simply yields nothing.

    #422: that hid two live figures at once - README drifted to 348 new blueprints against 400,
    and to eleven options against twelve. `claim-coverage` is the reverse direction, the same
    argument #402 made for the check-name registry.
    """

    def _findings(self, claims, vanilla=(), idle=None):
        f = check_docs.Findings()
        with (
            mock.patch.object(check_docs, "CLAIMS", list(claims)),
            mock.patch.object(check_docs, "VANILLA_CLAIMS", list(vanilla)),
            mock.patch.object(
                check_docs, "IDLE_PHRASINGS", {} if idle is None else idle
            ),
        ):
            check_docs.check_claim_coverage(f)
        return f.items

    def test_a_pattern_matching_nothing_is_reported(self) -> None:
        items = self._findings([(r"no document says this at all", ["x"])])
        self.assertTrue(items, "a pattern matching nothing was not reported")
        self.assertIn("matches nothing", items[0][1])

    def test_a_pattern_that_matches_is_quiet(self) -> None:
        self.assertEqual(
            self._findings([(r"(\w+) options, all under", ["options"])]), []
        )

    def test_an_idle_pattern_is_excused(self) -> None:
        pattern = r"no document says this at all"
        self.assertEqual(
            self._findings(
                [(pattern, ["x"])], idle={pattern: "registered ahead of the prose"}
            ),
            [],
        )

    def test_an_exemption_for_a_pattern_nobody_registered_is_reported(self) -> None:
        """Otherwise IDLE_PHRASINGS becomes a place typos go to be ignored."""
        items = self._findings([], idle={r"a phrasing nobody registered": "typo"})
        self.assertTrue(items, "a stale exemption was not reported")
        self.assertIn("CLAIMS, VANILLA_CLAIMS or WIKI_CLAIMS", items[0][1])

    def test_the_repository_agrees_with_itself_today(self) -> None:
        """The control the guard needs: run it against the real tables, not synthetic ones."""
        f = check_docs.Findings()
        check_docs.check_claim_coverage(f)
        self.assertEqual([c for c, _ in f.items], [])

    def test_every_idle_phrasing_names_a_reason(self) -> None:
        for pattern, reason in check_docs.IDLE_PHRASINGS.items():
            with self.subTest(pattern=pattern):
                self.assertTrue(
                    reason.strip(), "an exemption with no reason is not an exemption"
                )

    def test_wiki_patterns_are_not_dead_on_an_ordinary_run(self) -> None:
        """#427's design question: WIKI_CLAIMS has no wiki to match against unless --wiki is used.

        Reporting all ten as dead on every normal run would be the false failure the issue flagged
        before any of this was written, and a check that cries wolf is one people learn to skip.
        """
        f = check_docs.Findings()
        check_docs.check_claim_coverage(f)
        dead = [d for c, d in f.items if "WIKI_CLAIMS" in d]
        self.assertEqual(
            dead, [], "wiki patterns were reported dead with no wiki to read"
        )

    def test_wiki_patterns_are_checked_when_a_wiki_is_given(self) -> None:
        """The other half: passing a wiki must actually hold them, or the exemption is total."""
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp)
            (wiki / "Page.md").write_text("nothing matches here", encoding="utf-8")
            f = check_docs.Findings()
            with mock.patch.object(
                check_docs, "WIKI_CLAIMS", [(r"no page says this", ["options"])]
            ):
                check_docs.check_claim_coverage(f, wiki)
            self.assertTrue(
                [d for c, d in f.items if "WIKI_CLAIMS" in d],
                "a wiki pattern matching nothing was not reported",
            )


class WikiFigures(unittest.TestCase):
    """#427. The wiki had nine wrong figures and nothing read a word of its content.

    It also has no version selector, so a wrong figure there is wrong for every player on every
    version at once — which is why these are checked against the mod rather than against a document.
    """

    def _findings(self, page: str, known: dict[str, int]) -> list:
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp)
            (wiki / "Page.md").write_text(page, encoding="utf-8")
            f = check_docs.Findings()
            check_docs.check_wiki_counts(wiki, f, known)
            return f.items

    def test_a_wrong_option_count_is_reported(self) -> None:
        items = self._findings(
            "Eleven options live in Qud's own options menu, under Mods.",
            {"options": 12},
        )
        self.assertTrue(items, "a wrong option count was not reported")
        self.assertIn("says options is 11", items[0][1])

    def test_a_right_option_count_is_quiet(self) -> None:
        self.assertEqual(
            self._findings(
                "Twelve options live in Qud's own options menu, under Mods.",
                {"options": 12},
            ),
            [],
        )

    def test_a_claim_survives_a_line_break(self) -> None:
        """Wiki prose wraps like any other. The patterns go through `wrapped` for the same reason."""
        self.assertEqual(
            self._findings(
                "Twelve options live in Qud's\nown options menu, under Mods.",
                {"options": 12},
            ),
            [],
        )

    def test_the_slot_table_is_read_row_by_row(self) -> None:
        page = (
            "| genotype | slots |\n|---|---|\n| True Kin | 1 |\n| Psionic Adept | 4 |\n"
        )
        items = self._findings(
            page, {"chip-slots-truekin": 2, "chip-slots-psionicadept": 4}
        )
        self.assertEqual(len(items), 1, "exactly the wrong row should report")
        self.assertIn("chip-slots-truekin", items[0][1])

    def test_a_word_the_script_cannot_resolve_is_reported(self) -> None:
        """Silently skipping an unresolvable word is how a claim goes unchecked."""
        items = self._findings(
            "Umpteen options live in Qud's own options menu.", {"options": 12}
        )
        self.assertTrue(items)
        self.assertIn("WORD_NUMBERS", items[0][1])

    def test_none_resolves_to_zero(self) -> None:
        """The slot table writes zero as a word, so the vocabulary has to carry it."""
        self.assertEqual(check_docs.WORD_NUMBERS["none"], 0)

    def test_the_mutant_row_has_no_fact_behind_it(self) -> None:
        """Stated as a test so the limit is recorded rather than remembered.

        A Mutated Human has no slot because `Raven_ChipSlotPlayerMutator` removes it, which is a
        rule in C# rather than a number in XML. Restating it in Python would be a second
        implementation of the same rule.
        """
        self.assertNotIn("chip-slots-mutatedhuman", check_docs.facts())
        self.assertNotIn("chip-slots-humanoid", check_docs.facts())


class ConflictMarkers(unittest.TestCase):
    """#446. The marker that reached main was the one nothing looked for.

    pre-commit's check-merge-conflict matches "<<<<<<< ", "======= " and ">>>>>>> " and not the
    diff3 base marker, so a resolution removing the other three passed every gate and merged. These
    tests watch each shape fire, and watch the Markdown lookalikes stay quiet -- "=======" is also a
    setext H1 underline, and LICENSE-CONTENT rules its sections off with 71 of them.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        subprocess.run(["git", "init", "-q"], cwd=self.tmp, check=True)

    def findings(self, body: str) -> list[str]:
        (self.tmp / "doc.md").write_text(body, encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.tmp, check=True)
        f = check_docs.Findings()
        cwd = os.getcwd()
        os.chdir(self.tmp)
        try:
            check_docs.check_conflict_markers(f)
        finally:
            os.chdir(cwd)
        return [d for _, d in f.items]

    def test_the_diff3_base_marker_fires(self):
        """The one that got through. pre-commit's own hook does not match this."""
        found = self.findings("a\n||||||| 0e0d9de\nb\n")
        self.assertTrue(any("|||||||" in d for d in found), found)

    def test_the_three_the_upstream_hook_catches_fire_too(self):
        for marker in ("<<<<<<< HEAD", "======= ", ">>>>>>> main"):
            with self.subTest(marker=marker):
                self.assertTrue(self.findings(f"a\n{marker}\nb\n"), marker)

    def test_a_bare_seven_equals_line_fires(self):
        self.assertTrue(self.findings("a\n=======\nb\n"))

    def test_a_long_rule_is_not_a_marker(self):
        """LICENSE-CONTENT rules its sections off with 71 equals signs."""
        self.assertEqual(self.findings("Attribution 4.0\n" + "=" * 71 + "\n"), [])

    def test_a_short_setext_underline_is_not_a_marker(self):
        self.assertEqual(self.findings("Heading\n===\n"), [])

    def test_a_marker_without_its_trailing_space_is_not_one(self):
        """git always writes a space after the name markers; requiring it is what keeps this from
        firing on prose that happens to start with angle brackets."""
        self.assertEqual(self.findings("a\n<<<<<<<not-a-marker\nb\n"), [])

    def test_a_clean_file_is_quiet(self):
        self.assertEqual(self.findings("# Title\n\nOrdinary prose.\n"), [])

    def test_the_line_number_is_reported(self):
        found = self.findings("one\ntwo\n||||||| base\n")
        self.assertTrue(any("doc.md:3:" in d for d in found), found)

    def test_a_binary_file_is_skipped_rather_than_crashing(self):
        (self.tmp / "blob.bin").write_bytes(b"\x00\xff\xfe<<<<<<< HEAD\n")
        self.assertEqual(self.findings("clean\n"), [])


@contextmanager
def workshop_mod(description: str, version: str = "2.6.0"):
    """A synthetic mod/ holding one Workshop description and one manifest version."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "mod").mkdir()
        (root / "mod" / "workshop.json").write_text(
            json.dumps({"WorkshopId": 1, "Description": description}), encoding="utf-8"
        )
        (root / "mod" / "manifest.json").write_text(
            json.dumps({"version": version}), encoding="utf-8"
        )
        with chdir(root):
            yield


def workshop_findings(description: str, known=None):
    """Only the figure check, so a fixture without version lines does not trip the other one."""
    with workshop_mod(description):
        f = check_docs.Findings()
        counted = check_docs.check_workshop_counts(
            f, known if known is not None else {"options": 18}
        )
        return counted, f.items


def workshop_version_findings(description: str, version: str):
    """Only the version check, for the same reason in reverse."""
    with workshop_mod(description, version):
        f = check_docs.Findings()
        check_docs.check_workshop_version(f)
        return f.items


OPTIONS_LINE = "[b]{} settings in Qud's own options menu, under Mods.[/b]"
VERSION_LINES = (
    "[h1]New in {v}[/h1]\n[h1]Version and saves[/h1]\n[b]{v}.[/b] Loads fine."
)


class WorkshopFigures(unittest.TestCase):
    """#459: the Workshop description ships with a release and nobody counted its figures.

    `check_workshop_description` in validate_mod.py measures the Description's length and nothing
    else, which is how "Twelve settings" survived six new options across two releases.
    """

    def test_a_matching_count_passes(self) -> None:
        counted, items = workshop_findings(OPTIONS_LINE.format("Eighteen"))
        self.assertEqual(items, [])
        self.assertEqual(counted, 1, "the claim must actually have been checked")

    def test_the_real_defect_is_reported(self) -> None:
        """Verbatim the sentence that shipped wrong."""
        _, items = workshop_findings(OPTIONS_LINE.format("Twelve"))
        self.assertTrue(items, "a stale option count was not reported")
        self.assertEqual(items[0][0], "workshop-figure")
        self.assertIn("says options is 12", items[0][1])
        self.assertIn("18", items[0][1])

    def test_a_digit_is_read_as_well_as_a_word(self) -> None:
        self.assertEqual(workshop_findings(OPTIONS_LINE.format("18"))[1], [])

    def test_a_description_reflowed_across_a_line_still_matches(self) -> None:
        """`wrapped()` exists because prose moves; assert it applies here too, or this check
        drifts silent the way README.md's did in #422."""
        line = OPTIONS_LINE.format("Eighteen").replace("in Qud's", "in\nQud's")
        counted, items = workshop_findings(line)
        self.assertEqual(counted, 1, "a reflowed claim stopped being checked")
        self.assertEqual(items, [])

    def test_a_pattern_naming_an_unknown_fact_is_reported(self) -> None:
        _, items = workshop_findings(OPTIONS_LINE.format("Eighteen"), known={})
        self.assertTrue(items)
        self.assertIn("unknown fact", items[0][1])

    def test_no_claim_at_all_checks_nothing_and_reports_nothing(self) -> None:
        """The vacuous case, stated rather than assumed: zero checked is not zero problems."""
        counted, items = workshop_findings("[h1]Nothing quantified here[/h1]")
        self.assertEqual(counted, 0)
        self.assertEqual([i for i in items if i[0] == "workshop-figure"], [])


class WorkshopVersion(unittest.TestCase):
    """The two places that go stale the moment manifest.json bumps."""

    def test_matching_versions_pass(self) -> None:
        items = workshop_version_findings(VERSION_LINES.format(v="2.6.0"), "2.6.0")
        self.assertEqual(items, [])

    def test_a_stale_version_is_reported(self) -> None:
        items = workshop_version_findings(VERSION_LINES.format(v="2.6.0"), "2.7.0")
        self.assertEqual(len(items), 2, "both sites must be reported")
        self.assertTrue(all(c == "workshop-version" for c, _ in items))
        self.assertTrue(any("New in" in d for _, d in items))
        self.assertTrue(any("Version and saves" in d for _, d in items))

    def test_an_older_release_cited_in_prose_is_not_dragged_forward(self) -> None:
        """The quill arrow line says it shipped in 2.3.0. That is history, not a claim about
        what ships now, and a bare version regex would rewrite the past."""
        text = (
            VERSION_LINES.format(v="2.7.0") + "\nIt shipped in 2.3.0 with a bad bleed."
        )
        items = workshop_version_findings(text, "2.7.0")
        self.assertEqual(items, [])

    def test_a_reworded_heading_is_reported_rather_than_passing_quietly(self) -> None:
        """A pattern that matches nothing is the silence this whole file exists to break."""
        items = workshop_version_findings(
            "[h1]What's new[/h1]\nno version here", "2.7.0"
        )
        self.assertTrue(items, "a missing version site was not reported")
        self.assertTrue(all(c == "workshop-version" for c, _ in items))
        self.assertIn("missing or reworded", items[0][1])


if __name__ == "__main__":
    unittest.main()


TABLE = """### 6.1 Counts by file

| File | New objects | Merged vanilla objects |
|---|---|---|
{rows}
| **Total** | **444 active** | **211** |

### 6.2 Melee weapons
"""


def row_findings(rows: str, known: dict | None = None):
    """Run check_file_rows against a synthetic §6.1 table."""
    if known is None:
        known = {
            "file:Armor.xml:new": 61,
            "file:Armor.xml:merged": 38,
            "file:Armor.xml:dormant": 0,
        }
    tmp = Path(tempfile.mkdtemp())
    (tmp / "docs").mkdir()
    (tmp / "docs" / "FEATURES.md").write_text(TABLE.format(rows=rows))
    f = check_docs.Findings()
    with chdir(tmp):
        counted = check_docs.check_file_rows(f, known)
    return counted, sorted(f.items)


class FileRows(unittest.TestCase):
    """#473: three of eleven rows had drifted and the Total row still matched.

    The per-file figures had been computed here since the table was written and no CLAIMS pattern
    ever quoted one, so nothing looked. Both directions, and both structural cases: a row for a
    file that is gone, and a file with no row.
    """

    def test_a_correct_row_passes_and_is_counted(self) -> None:
        counted, items = row_findings("| `Armor.xml` | 61 | 38 |")
        self.assertEqual(items, [])
        self.assertEqual(counted, 2, "the row must actually have been checked")

    def test_a_stale_new_count_is_reported(self) -> None:
        """Verbatim the shape that shipped wrong: Creatures.xml said 2 and held 46."""
        _, items = row_findings("| `Armor.xml` | 2 | 38 |")
        self.assertTrue(items, "a stale new count was not reported")
        self.assertEqual(items[0][0], "file-rows")
        self.assertIn("new says 2", items[0][1])
        self.assertIn("it is 61", items[0][1])

    def test_a_stale_merged_count_is_reported(self) -> None:
        _, items = row_findings("| `Armor.xml` | 61 | 79 |")
        self.assertTrue(items)
        self.assertIn("merged says 79", items[0][1])

    def test_a_row_for_a_file_that_does_not_exist_is_reported(self) -> None:
        _, items = row_findings("| `Armor.xml` | 61 | 38 |\n| `Gone.xml` | 1 | 1 |")
        self.assertTrue(items)
        self.assertIn("not in mod/ObjectBlueprints", items[0][1])

    def test_a_file_with_no_row_is_reported(self) -> None:
        """The direction that let Plants.xml arrive without anyone deciding it belonged."""
        _, items = row_findings("")
        self.assertTrue(items, "a file with no row was not reported")
        self.assertIn("has no row", items[0][1])

    def test_a_dormant_count_is_checked_when_written(self) -> None:
        known = {
            "file:Ammo.xml:new": 22,
            "file:Ammo.xml:merged": 1,
            "file:Ammo.xml:dormant": 22,
        }
        self.assertEqual(
            row_findings("| `Ammo.xml` | 22 (22 dormant) | 1 |", known)[1], []
        )
        _, items = row_findings("| `Ammo.xml` | 22 (20 dormant) | 1 |", known)
        self.assertTrue(items, "the stale parenthetical that shipped was not reported")
        self.assertIn("dormant says 20", items[0][1])

    def test_unwritten_dormant_objects_are_reported(self) -> None:
        """A file that holds commented-out objects must say so, or the figure hides."""
        known = {
            "file:Ammo.xml:new": 22,
            "file:Ammo.xml:merged": 1,
            "file:Ammo.xml:dormant": 22,
        }
        _, items = row_findings("| `Ammo.xml` | 22 | 1 |", known)
        self.assertTrue(items, "a hidden dormant count was not reported")
        self.assertIn("holds 22 commented-out object(s)", items[0][1])

    def test_a_renamed_heading_is_reported_rather_than_passing_quietly(self) -> None:
        """The vacuous case: a table this cannot find must fail, not check zero rows."""
        tmp = Path(tempfile.mkdtemp())
        (tmp / "docs").mkdir()
        (tmp / "docs" / "FEATURES.md").write_text("### 6.1b Counts\n\nnothing here\n")
        f = check_docs.Findings()
        with chdir(tmp):
            check_docs.check_file_rows(f, {})
        self.assertTrue(f.items)
        self.assertIn("heading not found", min(f.items)[1])
