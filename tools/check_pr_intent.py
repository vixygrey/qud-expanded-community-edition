#!/usr/bin/env python3
"""Refuse a pull request that says it only advances an issue while carrying a closing link to it.

`docs/LESSONS.md` has prescribed `gh pr view <n> --json closingIssuesReferences` since #292, after
accidental closing keywords shut two issues. It is a habit, and habits expire: I ran it on five
consecutive pull requests, found nothing, stopped, and #360 closed #339 with a sentence that read
*"No closing keyword - ... I would rather you close #339 than have a merge do it."* Charter rule 4
says where that belongs - **"Keep new checks in the script rather than in prose."**

Both halves of the contradiction are machine-readable:

- the body's stated intent - `Part of #N`, `Advances #N`, `Why #N stays open`, the three forms
  `docs/LESSONS.md` prescribes for referring to an issue a pull request does *not* close;
- the actual link - `closingIssuesReferences`, which GitHub resolves from the body's keywords.

So the rule is: **an issue named after a non-closing marker must not also be closed by this pull
request.** That needs no judgement, and it catches every instance this repository has recorded - the
denial in #286, the narration in #292 and the delegation in #360.

It is deliberately not the whole of the habit. A pull request that carries a closing reference and
says nothing either way is still worth the manual look, because there is no stated intent to
contradict. What this removes is the case that has actually bitten, three times.

A separate script rather than a step body, because the interesting part is a regular expression over
prose and that is exactly the kind of thing that goes subtly wrong in silence. `tools/` is where this
repository keeps things it can test.

Usage:
    python3 tools/check_pr_intent.py --body-file body.md --closes 339 --closes 347
    python3 tools/check_pr_intent.py --body-file - --closes-json '[{"number": 339}]'

Exits 0 when the body and the links agree, 1 when they contradict, and 2 on a usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# The three forms docs/LESSONS.md prescribes for naming an issue a pull request does not close.
# Matched case-insensitively. `Advance` covers "advances" and the bare imperative; `Why` covers
# "Why #N stays open", where the marker precedes the number the same way.
#
# Deliberately narrow. A wider net - every "#N" not adjacent to a closing keyword - would invert the
# failure this exists to prevent: the point is to catch a *stated* intent contradicted by a link, and
# a pull request that merely mentions an issue in passing has stated nothing to contradict.
MARKERS = re.compile(r"\b(?:part of|advances?|why)\b[ \t]*(?=#\d)", re.IGNORECASE)

# A run of issue references, so "Part of #1 and #2" and "Part of #1, #2" both read as two.
RUN = re.compile(r"#(\d+)(?:[ \t]*(?:,|and)[ \t]*)?", re.IGNORECASE)


def advanced_issues(body: str) -> list[int]:
    """Every issue number the body names after a non-closing marker, in order of appearance."""
    found: list[int] = []
    for marker in MARKERS.finditer(body):
        position = marker.end()
        while match := RUN.match(body, position):
            number = int(match.group(1))
            if number not in found:
                found.append(number)
            position = match.end()
    return found


def contradictions(body: str, closes: set[int]) -> list[int]:
    """Issues the body says it only advances, which this pull request would nonetheless close."""
    return [number for number in advanced_issues(body) if number in closes]


def report(found: list[int], body: str) -> None:
    plural = "issue" if len(found) == 1 else "issues"
    numbers = ", ".join(f"#{n}" for n in found)
    print(
        f"::error::This pull request says it only advances {numbers}, but it also carries a "
        f"closing reference to {'that ' + plural if len(found) == 1 else 'those ' + plural}. "
        "GitHub would close it on merge. Closing keywords ignore negation, narration and "
        "delegation - see docs/LESSONS.md."
    )
    for number in found:
        for line in body.splitlines():
            if re.search(rf"#{number}\b", line):
                print(f"  #{number}: {line.strip()}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--body-file",
        required=True,
        help="file holding the pull request body, or - for standard input",
    )
    parser.add_argument(
        "--closes",
        type=int,
        action="append",
        default=[],
        help="an issue number this pull request closes; repeatable",
    )
    parser.add_argument(
        "--closes-json",
        help="closingIssuesReferences as gh returns it, e.g. '[{\"number\": 339}]'",
    )
    args = parser.parse_args(argv)

    body = (
        sys.stdin.read()
        if args.body_file == "-"
        else Path(args.body_file).read_text(encoding="utf-8")
    )

    closes = set(args.closes)
    if args.closes_json:
        try:
            payload = json.loads(args.closes_json)
        except json.JSONDecodeError as exc:
            print(f"::error::--closes-json is not JSON: {exc}", file=sys.stderr)
            return 2
        try:
            closes |= {int(entry["number"]) for entry in payload}
        except (TypeError, KeyError, ValueError) as exc:
            print(
                f"::error::--closes-json is not a list of objects with a number: {exc}",
                file=sys.stderr,
            )
            return 2

    found = contradictions(body, closes)
    if not found:
        advanced = advanced_issues(body)
        if advanced:
            named = ", ".join(f"#{n}" for n in advanced)
            print(f"Body says it advances {named}; none of them would be closed. Good.")
        else:
            print(
                "No 'Part of' / 'Advances' / 'Why ... stays open' reference to check."
            )
        return 0

    report(found, body)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
