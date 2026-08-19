#!/usr/bin/env python3
"""Tests for tools/snapshot_qud_api.py.

Only `guard_part_source`, because it is the part that can be tested without a copy of the game:
it reads the committed snapshot and the run's own arguments, and nothing else.

It is also the part worth testing. #244 found that mixing the two part sources breaks both paths -
a plain write over an assembly-built snapshot silently drops 656 part names, and `--check` across
the same mismatch calls a current file STALE and then advises the command that performs the drop.
Both directions are covered here, along with the two cases that must stay quiet: a first
generation with no snapshot to compare against, and a snapshot too broken to read.

No game, no network, no dependencies.
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

import snapshot_qud_api

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


if __name__ == "__main__":
    unittest.main()
