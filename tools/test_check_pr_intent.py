#!/usr/bin/env python3
"""Tests for tools/check_pr_intent.py.

The interesting part is a regular expression over prose, which is the kind of thing that fails
quietly and reports a clean run. So the three pull requests that actually caused #361 are here as
fixtures, in their own words: a check for this defect that does not catch the recorded instances of
it would be worse than none, because it would retire the manual habit as well.

No network and no `gh` - the script takes the body and the resolved links as arguments precisely so
that it can be tested without either.
"""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_pr_intent

# The three instances docs/LESSONS.md records, quoted from the pull requests themselves.
DENIAL = "Part of #284 — deliberately does not close it, see the end.\n\n## Why #284 stays open\n"
NARRATION = (
    "Part of #291. Does not finish it — two of its three acceptance boxes need a decision.\n"
    "#50 corrected both to `<tag>` and resolved issue 10.\n"
)
DELEGATION = (
    "Part of #339 and #336, and completes the balance sweep's four questions. No closing keyword —\n"
    "implementation is still to come, and I would rather you close #339 than have a merge do it.\n"
)


def run(body: str, *args: str) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "body.md"
        path.write_text(body, encoding="utf-8")
        out = io.StringIO()
        with redirect_stdout(out):
            code = check_pr_intent.main(["--body-file", str(path), *args])
        return code, out.getvalue()


class RecordedInstances(unittest.TestCase):
    """#361. Each of these merged and closed an issue its own body said it did not close."""

    def test_the_denial_in_286(self) -> None:
        code, out = run(DENIAL, "--closes", "284")
        self.assertEqual(code, 1)
        self.assertIn("#284", out)

    def test_the_narration_in_292(self) -> None:
        code, _ = run(NARRATION, "--closes", "291")
        self.assertEqual(code, 1)

    def test_the_delegation_in_360(self) -> None:
        """The one worth staring at: it declares 'No closing keyword' and contains one nine words
        later, in the clause asking a human to do the closing by hand."""
        code, out = run(DELEGATION, "--closes", "339")
        self.assertEqual(code, 1)
        self.assertIn("would rather you close #339", out)

    def test_360_would_also_have_flagged_the_second_issue(self) -> None:
        """'Part of #339 and #336' names two, and a run of references must read as both."""
        code, out = run(DELEGATION, "--closes", "336")
        self.assertEqual(code, 1)
        self.assertIn("#336", out)


class Markers(unittest.TestCase):
    def test_part_of(self) -> None:
        self.assertEqual(run("Part of #12.", "--closes", "12")[0], 1)

    def test_advances(self) -> None:
        self.assertEqual(run("Advances #12 a little.", "--closes", "12")[0], 1)

    def test_why_it_stays_open(self) -> None:
        self.assertEqual(run("## Why #12 stays open", "--closes", "12")[0], 1)

    def test_markers_are_case_insensitive(self) -> None:
        for body in ("PART OF #12", "part of #12", "Part Of #12"):
            with self.subTest(body=body):
                self.assertEqual(run(body, "--closes", "12")[0], 1)

    def test_markdown_emphasis_around_the_marker(self) -> None:
        """Every pull request body in this repository writes it as **Part of #N**."""
        self.assertEqual(run("**Part of #12** — see below.", "--closes", "12")[0], 1)

    def test_a_comma_separated_run(self) -> None:
        code, out = run("Part of #12, #13 and #14.", "--closes", "14")
        self.assertEqual(code, 1)
        self.assertIn("#14", out)


class Passes(unittest.TestCase):
    def test_advancing_an_issue_it_does_not_close(self) -> None:
        """The ordinary case, and the one that must stay quiet - most pull requests look like this."""
        code, out = run("Part of #12.", "--closes", "99")
        self.assertEqual(code, 0)
        self.assertIn("none of them would be closed", out)

    def test_closing_an_issue_the_body_does_not_disclaim(self) -> None:
        """A pull request that means to close something is not this check's business."""
        code, _ = run("Closes #12.", "--closes", "12")
        self.assertEqual(code, 0)

    def test_a_passing_mention_is_not_a_stated_intent(self) -> None:
        """Deliberate. The check catches a stated intent contradicted by a link; a body that merely
        names an issue has stated nothing, and flagging it would invert the failure this prevents."""
        code, _ = run("This follows the reasoning in #12.", "--closes", "12")
        self.assertEqual(code, 0)

    def test_an_empty_body(self) -> None:
        code, out = run("", "--closes", "12")
        self.assertEqual(code, 0)
        self.assertIn("No 'Part of'", out)

    def test_a_marker_not_followed_by_a_reference(self) -> None:
        """'part of the sweep' is prose, not a reference."""
        code, _ = run("This is part of the balance sweep.", "--closes", "12")
        self.assertEqual(code, 0)


class ClosesJson(unittest.TestCase):
    """The workflow passes `gh pr view --json closingIssuesReferences` through unchanged."""

    PAYLOAD = '[{"number": 339, "url": "https://example.invalid/339"}]'

    def test_the_gh_payload_is_read(self) -> None:
        self.assertEqual(run("Part of #339.", "--closes-json", self.PAYLOAD)[0], 1)

    def test_an_empty_payload_passes(self) -> None:
        self.assertEqual(run("Part of #339.", "--closes-json", "[]")[0], 0)

    def test_malformed_json_is_a_usage_error_not_a_pass(self) -> None:
        """Exit 2, never 0. A parse failure that passed would be a check that stopped running
        without anyone noticing - which is the whole failure mode #361 is about."""
        code, _ = run("Part of #339.", "--closes-json", "{not json")
        self.assertEqual(code, 2)

    def test_a_payload_of_the_wrong_shape_is_a_usage_error(self) -> None:
        code, _ = run("Part of #339.", "--closes-json", '["339"]')
        self.assertEqual(code, 2)


class Api(unittest.TestCase):
    """The two functions, exercised directly - the ordering guarantee is not visible through main."""

    def test_advanced_issues_preserves_order_and_deduplicates(self) -> None:
        self.assertEqual(
            check_pr_intent.advanced_issues("Part of #9 and #3. Why #9 stays open."),
            [9, 3],
        )

    def test_contradictions_returns_only_the_overlap(self) -> None:
        self.assertEqual(
            check_pr_intent.contradictions("Part of #1, #2 and #3.", {2, 7}), [2]
        )


if __name__ == "__main__":
    unittest.main()
