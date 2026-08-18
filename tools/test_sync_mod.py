#!/usr/bin/env python3
"""Tests for tools/sync_mod.py.

The script's whole value is its refusals, and a guard that has quietly stopped firing is
indistinguishable from one that passes — the same reasoning that put tests on
`tools/check_build_log.py`. So these cover the three things that would be expensive to get wrong:

1. `--publish` refusing a state that is not exactly the published branch.
2. `--dev` actually removing the `WorkshopId`, which is the only thing standing between an
   experimental build and the live Workshop page.
3. The destination guard refusing to delete a directory that is not this mod.

They build synthetic git repositories and mod directories, so they need no game, no network and
no dependencies.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))

import sync_mod


@contextmanager
def chdir(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


def make_repo(tmp: Path) -> tuple[Path, Path]:
    """A local 'origin' and a clone of it, both with a main branch and one commit."""
    origin = tmp / "origin"
    origin.mkdir()
    run("git", "init", "--quiet", "--bare", "--initial-branch=main", ".", cwd=origin)

    work = tmp / "work"
    work.mkdir()
    run("git", "init", "--quiet", "--initial-branch=main", ".", cwd=work)
    run("git", "config", "user.email", "t@example.com", cwd=work)
    run("git", "config", "user.name", "Test", cwd=work)
    (work / "mod").mkdir()
    (work / "mod" / "manifest.json").write_text(
        json.dumps({"id": sync_mod.MANIFEST_ID, "title": "Test Mod"}), encoding="utf-8"
    )
    run("git", "add", "-A", cwd=work)
    run("git", "commit", "--quiet", "-m", "initial", cwd=work)
    run("git", "remote", "add", "origin", str(origin), cwd=work)
    run("git", "push", "--quiet", "-u", "origin", "main", cwd=work)
    return origin, work


class PublishGuards(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.origin, self.work = make_repo(Path(self.tmp.name))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_accepts_clean_main_level_with_origin(self) -> None:
        with chdir(self.work):
            sync_mod.check_publish_state(fetch=False)  # must not raise

    def test_refuses_a_feature_branch(self) -> None:
        run("git", "switch", "--quiet", "-c", "feature/x", cwd=self.work)
        with chdir(self.work), self.assertRaises(sync_mod.Problem) as cm:
            sync_mod.check_publish_state(fetch=False)
        self.assertIn("feature/x", str(cm.exception))

    def test_refuses_a_dirty_tree(self) -> None:
        (self.work / "mod" / "scratch.xml").write_text("<objects />", encoding="utf-8")
        with chdir(self.work), self.assertRaises(sync_mod.Problem) as cm:
            sync_mod.check_publish_state(fetch=False)
        self.assertIn("not clean", str(cm.exception))

    def test_refuses_when_local_is_ahead_of_origin(self) -> None:
        (self.work / "mod" / "extra.xml").write_text("<objects />", encoding="utf-8")
        run("git", "add", "-A", cwd=self.work)
        run("git", "commit", "--quiet", "-m", "unpushed", cwd=self.work)
        with chdir(self.work), self.assertRaises(sync_mod.Problem) as cm:
            sync_mod.check_publish_state(fetch=False)
        self.assertIn("origin/main", str(cm.exception))

    def test_refuses_when_local_is_behind_origin(self) -> None:
        # A second clone pushes, so origin moves on and this one is stale — the state that bites
        # after merging a pull request from the web without pulling.
        other = Path(self.tmp.name) / "other"
        run(
            "git",
            "clone",
            "--quiet",
            str(self.origin),
            str(other),
            cwd=Path(self.tmp.name),
        )
        run("git", "config", "user.email", "t@example.com", cwd=other)
        run("git", "config", "user.name", "Test", cwd=other)
        (other / "mod" / "later.xml").write_text("<objects />", encoding="utf-8")
        run("git", "add", "-A", cwd=other)
        run("git", "commit", "--quiet", "-m", "later", cwd=other)
        run("git", "push", "--quiet", cwd=other)

        with chdir(self.work), self.assertRaises(sync_mod.Problem) as cm:
            sync_mod.check_publish_state(fetch=True)
        self.assertIn("behind", str(cm.exception))


class DevBuild(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dest = Path(self.tmp.name) / "install"
        self.dest.mkdir()
        (self.dest / "workshop.json").write_text(
            json.dumps(
                {"WorkshopId": 3785441196, "Title": "Qud Expanded", "Description": "x"}
            ),
            encoding="utf-8",
        )
        (self.dest / "manifest.json").write_text(
            json.dumps({"id": sync_mod.MANIFEST_ID, "title": "Qud Expanded"}),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _workshop(self) -> dict:
        return json.loads((self.dest / "workshop.json").read_text(encoding="utf-8"))

    def _manifest(self) -> dict:
        return json.loads((self.dest / "manifest.json").read_text(encoding="utf-8"))

    def test_removes_the_workshop_id_entirely(self) -> None:
        sync_mod.mark_as_dev(self.dest)
        # Absent, not zero: check_workshop_target documents that 0 is a lookup for item zero,
        # not a blank, so leaving one behind would be its own defect.
        self.assertNotIn("WorkshopId", self._workshop())

    def test_labels_both_titles(self) -> None:
        sync_mod.mark_as_dev(self.dest)
        self.assertTrue(self._workshop()["Title"].endswith(sync_mod.DEV_SUFFIX))
        self.assertTrue(self._manifest()["title"].endswith(sync_mod.DEV_SUFFIX))

    def test_is_idempotent(self) -> None:
        sync_mod.mark_as_dev(self.dest)
        sync_mod.mark_as_dev(self.dest)
        self.assertEqual(self._manifest()["title"].count(sync_mod.DEV_SUFFIX), 1)

    def test_leaves_other_fields_alone(self) -> None:
        sync_mod.mark_as_dev(self.dest)
        self.assertEqual(self._workshop()["Description"], "x")
        self.assertEqual(self._manifest()["id"], sync_mod.MANIFEST_ID)


class DestinationGuard(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dest = Path(self.tmp.name) / "install"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_allows_a_missing_directory(self) -> None:
        sync_mod.guard_destination(self.dest)

    def test_allows_an_empty_directory(self) -> None:
        self.dest.mkdir()
        (self.dest / ".DS_Store").write_text("", encoding="utf-8")
        sync_mod.guard_destination(self.dest)

    def test_allows_our_own_install(self) -> None:
        self.dest.mkdir()
        (self.dest / "manifest.json").write_text(
            json.dumps({"id": sync_mod.MANIFEST_ID}), encoding="utf-8"
        )
        sync_mod.guard_destination(self.dest)

    def test_refuses_another_mod(self) -> None:
        self.dest.mkdir()
        (self.dest / "manifest.json").write_text(
            json.dumps({"id": "SomebodyElsesMod"}), encoding="utf-8"
        )
        with self.assertRaises(sync_mod.Problem) as cm:
            sync_mod.guard_destination(self.dest)
        self.assertIn("SomebodyElsesMod", str(cm.exception))

    def test_refuses_a_directory_that_is_not_a_mod(self) -> None:
        self.dest.mkdir()
        (self.dest / "taxes.pdf").write_text("", encoding="utf-8")
        with self.assertRaises(sync_mod.Problem) as cm:
            sync_mod.guard_destination(self.dest)
        self.assertIn("no manifest.json", str(cm.exception))


class CopyTree(unittest.TestCase):
    def test_skips_finder_litter_and_replaces_the_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src, dest = Path(tmp) / "mod", Path(tmp) / "install"
            (src / "ObjectBlueprints").mkdir(parents=True)
            (src / "ObjectBlueprints" / "Ammo.xml").write_text(
                "<objects />", encoding="utf-8"
            )
            (src / ".DS_Store").write_text("junk", encoding="utf-8")
            dest.mkdir()
            (dest / "stale.xml").write_text("old", encoding="utf-8")

            written = sync_mod.copy_tree(src, dest)

            self.assertEqual(written, 1)
            self.assertTrue((dest / "ObjectBlueprints" / "Ammo.xml").is_file())
            self.assertFalse((dest / ".DS_Store").exists())
            self.assertFalse((dest / "stale.xml").exists())


if __name__ == "__main__":
    unittest.main()
