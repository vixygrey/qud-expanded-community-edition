#!/usr/bin/env python3
"""Tests for tools/check_build_log.py. Python 3 standard library only.

    python3 -m unittest discover -s tools

`check_build_log.py` reads a verdict the game wrote on a developer's machine, so the check itself
can never run in CI. Its *guards* can, and they are the part worth covering: the whole point of
that script is that it refuses a stale or unrelated verdict, and a guard that has quietly stopped
firing looks exactly like a guard that passes.

So every case here builds a synthetic save directory - a deployed copy of `mod/Scripting/` and a
`build_log.txt` written in the game's own vocabulary - and asserts the script reaches the intended
verdict. `test_a_good_log_passes` is the control: without it, a script that failed unconditionally
would satisfy every other test here. It has already earned that place, by catching a hardcoded
timestamp in these fixtures on its first CI run - see `stamp_after` below.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "check_build_log.py"
SCRIPTING = REPO / "mod" / "Scripting"

MOD_ID = "QudExpandedCommunityEdition"
TITLE_CAPS = "QUD EXPANDED COMMUNITY EDITION"
ANCIENT = "[2020-01-01T00:00:00] "

# What a successful build looks like, in the game's words.
BUILT = [
    "Loading path: /",
    "Compiling 40 files...",
    "Success :)",
    f"Location: /x/{MOD_ID}.dll",
    f"Defined symbol: MOD_{MOD_ID.upper()}",
]


def stamp_after(paths: list[Path]) -> str:
    """A log timestamp an hour after the newest of these files, in the game's format.

    Derived rather than hardcoded, and that is not fussiness. A fixed stamp passes locally, where
    the working tree was written whenever it was written, and fails on a fresh checkout, where
    every file's mtime is "now" and so newer than any date baked in here. The `fresh` guard then
    fires on the control case - which is what happened. A fixture that describes files has to take
    its clock from those files.
    """
    newest = max(p.stat().st_mtime for p in paths)
    # Local time, because that is what the game writes - naive stamps with no offset.
    local = datetime.fromtimestamp(newest, tz=timezone.utc).astimezone()
    return (local + timedelta(hours=1)).strftime("[%Y-%m-%dT%H:%M:%S] ")


def build_log(
    body: list[str],
    *,
    stamp: str,
    load_order: tuple[str, ...] = (MOD_ID,),
    title: str = TITLE_CAPS,
) -> str:
    """Assemble a build log around one mod section, mimicking the real file's shape."""
    lines = [
        "--log start--",
        stamp + "BuildLogger initialized...",
        stamp + "==== BUILDING MODS ====",
        # A neighbouring mod, so section parsing is exercised rather than assumed.
        stamp + "=== SOME OTHER MOD ===",
        stamp + "Loading path: /",
        stamp + "Skipping, state: Disabled",
        stamp + f"=== {title} ===",
    ]
    lines += [stamp + line for line in body]
    lines.append(stamp + "==== FINAL LOAD ORDER ====")
    lines += [stamp + f"{i}: {name}" for i, name in enumerate(load_order, 1)]
    return "\n".join(lines) + "\n"


class BuildLogCheck(unittest.TestCase):
    def run_check(
        self,
        *,
        body: list[str] | None = None,
        stamp: str | None = None,
        load_order: tuple[str, ...] = (MOD_ID,),
        title: str = TITLE_CAPS,
        write_log: bool = True,
        deploy: bool = True,
        edit: str | None = None,
        remove: str | None = None,
        touch_future: bool = False,
    ) -> tuple[int, str]:
        """Run the script against a synthetic save directory and return (exit code, output)."""
        with tempfile.TemporaryDirectory() as tmp:
            save = Path(tmp)
            mods = save / "Mods"
            mods.mkdir()
            deployed_cs: list[Path] = []

            if deploy:
                # A folder name deliberately unlike the manifest id: the script must find the mod
                # by reading manifests, since the installed folder is named however it arrived.
                deployed = mods / "some-installed-folder"
                (deployed / "Scripting").mkdir(parents=True)
                for cs in SCRIPTING.glob("*.cs"):
                    target = deployed / "Scripting" / cs.name
                    shutil.copy2(cs, target)
                    deployed_cs.append(target)
                (deployed / "manifest.json").write_text(json.dumps({"id": MOD_ID}))

            # Before the mutations below, so touch_future lands *after* the log rather than
            # dragging the derived timestamp along with it.
            if stamp is None:
                stamp = stamp_after(deployed_cs) if deployed_cs else ANCIENT

            if edit:
                drifted = deployed / "Scripting" / edit
                drifted.write_text(drifted.read_text() + "\n// drifted\n")
            if remove:
                (deployed / "Scripting" / remove).unlink()
            if touch_future:
                os.utime(min(deployed_cs), (2_000_000_000, 2_000_000_000))  # 2033

            if write_log:
                (save / "build_log.txt").write_text(
                    build_log(
                        BUILT if body is None else body,
                        stamp=stamp,
                        load_order=load_order,
                        title=title,
                    )
                )

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--save-dir", str(save)],
                cwd=REPO,
                capture_output=True,
                text=True,
                check=False,
            )
        return result.returncode, result.stdout + result.stderr

    def assertFinding(self, output: str, check: str) -> None:
        self.assertIn(f"[{check}]", output, f"expected a {check!r} finding:\n{output}")

    # -- the control ------------------------------------------------------------------

    def test_a_good_log_passes(self):
        """Without this, a script that always failed would pass every other test here."""
        code, out = self.run_check()
        self.assertEqual(code, 0, out)
        self.assertIn("OK -", out)

    # -- refusing to answer without evidence ------------------------------------------

    def test_missing_log_is_an_error_not_a_pass(self):
        code, out = self.run_check(write_log=False)
        self.assertEqual(code, 2, out)
        self.assertIn("no build log at", out)

    def test_mod_not_deployed(self):
        code, out = self.run_check(deploy=False)
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "deployed")

    # -- the verdict must be about *this* source --------------------------------------

    def test_deployed_source_differs(self):
        code, out = self.run_check(edit="Raven_Options.cs")
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "identical")

    def test_deployed_source_missing_a_file(self):
        code, out = self.run_check(remove="Raven_Options.cs")
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "identical")

    def test_log_older_than_deployed_source(self):
        code, out = self.run_check(touch_future=True)
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "fresh")

    def test_log_from_long_before_the_source(self):
        code, out = self.run_check(stamp=ANCIENT)
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "fresh")

    # -- reading the compile verdict --------------------------------------------------

    def test_mod_disabled_is_not_a_pass(self):
        """The failure this script exists to prevent: nothing compiled, nothing complained."""
        code, out = self.run_check(
            body=["Loading path: /", "Skipping, state: Disabled"]
        )
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "built")
        self.assertIn("Options -> Mods", out)

    def test_compile_failure(self):
        code, out = self.run_check(
            body=[
                "Loading path: /",
                "Compiling 40 files...",
                "Failure :(",
                "== COMPILER ERRORS ==",
                "Raven_Options.cs(12,5): error CS0103: no such name",
            ]
        )
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "built")
        self.assertIn("CS0103", out, "the diagnostics must reach the reader")

    def test_compiler_threw(self):
        code, out = self.run_check(
            body=[
                "Loading path: /",
                "Compiling 40 files...",
                "Exception compiling mod assembly: boom",
            ]
        )
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "built")

    def test_no_verdict_either_way(self):
        code, out = self.run_check(body=["Loading path: /", "Compiling 40 files..."])
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "built")

    def test_section_absent(self):
        code, out = self.run_check(title="A DIFFERENT MOD")
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "built")

    def test_file_count_disagrees(self):
        code, out = self.run_check(
            body=[ln.replace("40 files", "39 files") for ln in BUILT]
        )
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "count")

    # -- built is not the same as loaded ----------------------------------------------

    def test_absent_from_load_order(self):
        code, out = self.run_check(load_order=("SomeOtherMod",))
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "loaded")

    def test_empty_load_order(self):
        code, out = self.run_check(load_order=())
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "loaded")


if __name__ == "__main__":
    unittest.main()
