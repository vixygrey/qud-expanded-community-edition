#!/usr/bin/env python3
"""Tests for tools/check_docs.py.

Only `check_changelog_sections` for now, because it is the check with a history: the same defect
has reached `main` twice — two `### Fixed` blocks corrected by hand before 2.4.0, then two
`### Added` blocks in #236 — and the hand-fix is precisely what failed to prevent the second. A
guard against a recurring defect is worth a test that watches it fire.

Both directions, per docs/LESSONS.md: a check is only proven by seeing it report something broken
AND stay quiet on something sound. Synthetic changelogs in a temp directory; no network, no
dependencies.
"""

from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
