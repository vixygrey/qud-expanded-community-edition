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
import zipfile
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


class BuildZip(unittest.TestCase):
    """#314. The release asset was the only unchecked step left in the whole release.

    Everything around it has a guard - --publish refuses a dirty tree or a branch, validate_mod ties
    the manifest to the changelog, check_docs and the pool snapshot run on every commit. The one step
    where a person assembled a file by hand is the one that ships to players.
    """

    @contextmanager
    def _mod(self, manifest: dict | None = None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mod = root / "mod"
            (mod / "ObjectBlueprints").mkdir(parents=True)
            (mod / "ObjectBlueprints" / "Ammo.xml").write_text(
                "<objects />", encoding="utf-8"
            )
            (mod / "Bodies.xml").write_text("<bodies />", encoding="utf-8")
            (mod / ".DS_Store").write_text("junk", encoding="utf-8")
            (mod / "manifest.json").write_text(
                json.dumps(manifest or {"id": "TestModId", "version": "9.9.9"}),
                encoding="utf-8",
            )
            previous = sync_mod.MOD
            sync_mod.MOD = mod
            try:
                yield root
            finally:
                sync_mod.MOD = previous

    def test_the_asset_is_named_from_the_manifest(self) -> None:
        with self._mod() as root:
            archive, written = sync_mod.build_zip(root, None)
            self.assertEqual(archive.name, "TestModId-9.9.9.zip")
            self.assertEqual(
                written, 3, "manifest, Bodies.xml and Ammo.xml, but not .DS_Store"
            )

    def test_the_top_level_folder_is_the_id_not_the_install_directory(self) -> None:
        """The hazard #314 exists for. The install directory is `qud-expanded-community-edition`
        and every published zip contains `QudExpandedCommunityEdition`, so the manual `cp -R` was a
        rename that read as ceremony - and getting it wrong still produced a plausible file."""
        with self._mod() as root:
            archive, _ = sync_mod.build_zip(root, None)
            with zipfile.ZipFile(archive) as zf:
                tops = {name.split("/")[0] for name in zf.namelist()}
            self.assertEqual(tops, {"TestModId"})
            self.assertNotIn(sync_mod.DEST_NAME, tops)

    def test_it_holds_exactly_what_copy_tree_produces(self) -> None:
        with self._mod() as root:
            archive, _ = sync_mod.build_zip(root, None)
            with zipfile.ZipFile(archive) as zf:
                names = sorted(zf.namelist())
            self.assertEqual(
                names,
                [
                    "TestModId/Bodies.xml",
                    "TestModId/ObjectBlueprints/Ammo.xml",
                    "TestModId/manifest.json",
                ],
            )
            self.assertNotIn("TestModId/.DS_Store", names)

    def test_rebuilding_replaces_rather_than_appends(self) -> None:
        """A zipfile opened for append would keep the old members, so a rebuild after deleting a
        file would ship both versions and look fine."""
        with self._mod() as root:
            sync_mod.build_zip(root, None)
            (sync_mod.MOD / "Bodies.xml").unlink()
            archive, _ = sync_mod.build_zip(root, None)
            with zipfile.ZipFile(archive) as zf:
                self.assertNotIn("TestModId/Bodies.xml", zf.namelist())

    def test_a_matching_tag_is_accepted_with_or_without_the_v(self) -> None:
        with self._mod() as root:
            for tag in ("v9.9.9", "9.9.9"):
                with self.subTest(tag=tag):
                    archive, _ = sync_mod.build_zip(root, tag)
                    self.assertEqual(archive.name, "TestModId-9.9.9.zip")

    def test_a_mismatched_tag_is_refused(self) -> None:
        """The check that would have caught a release changing from 2.6.0 to 2.5.1 across three
        files - validate_mod ties the manifest to the changelog, this ties it to the tag."""
        with self._mod() as root:
            with self.assertRaises(sync_mod.Problem) as caught:
                sync_mod.build_zip(root, "v9.9.8")
            self.assertIn("9.9.8", str(caught.exception))
            self.assertIn("9.9.9", str(caught.exception))

    def test_a_manifest_without_a_version_is_refused(self) -> None:
        with (
            self._mod({"id": "TestModId"}) as root,
            self.assertRaises(sync_mod.Problem),
        ):
            sync_mod.build_zip(root, None)

    def test_a_manifest_with_a_blank_id_is_refused(self) -> None:
        """Blank rather than missing, because "" would name the archive "-9.9.9.zip" and put every
        file at the archive root - plausible, and wrong."""
        with (
            self._mod({"id": "   ", "version": "9.9.9"}) as root,
            self.assertRaises(sync_mod.Problem),
        ):
            sync_mod.build_zip(root, None)

    def test_an_unreadable_manifest_is_refused(self) -> None:
        with self._mod() as root:
            (sync_mod.MOD / "manifest.json").write_text("{not json", encoding="utf-8")
            with self.assertRaises(sync_mod.Problem):
                sync_mod.build_zip(root, None)


if __name__ == "__main__":
    unittest.main()
