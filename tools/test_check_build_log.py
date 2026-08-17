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
would satisfy every other test here.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "check_build_log.py"
SCRIPTING = REPO / "mod" / "Scripting"

MOD_ID = "QudExpandedCommunityEdition"
TITLE_CAPS = "QUD EXPANDED COMMUNITY EDITION"
STAMP = "[2026-08-16T18:11:02] "
ANCIENT = "[2020-01-01T00:00:00] "

# What a successful build looks like, in the game's words.
BUILT = [
    "Loading path: /",
    "Compiling 40 files...",
    "Success :)",
    f"Location: /x/{MOD_ID}.dll",
    f"Defined symbol: MOD_{MOD_ID.upper()}",
]


def build_log(
    body: list[str],
    *,
    stamp: str = STAMP,
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
        log: str | None,
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

            if deploy:
                # A folder name deliberately unlike the manifest id: the script must find the mod
                # by reading manifests, since the installed folder is named however it arrived.
                deployed = mods / "some-installed-folder"
                (deployed / "Scripting").mkdir(parents=True)
                for cs in SCRIPTING.glob("*.cs"):
                    shutil.copy2(cs, deployed / "Scripting" / cs.name)
                (deployed / "manifest.json").write_text(json.dumps({"id": MOD_ID}))

                if edit:
                    target = deployed / "Scripting" / edit
                    target.write_text(target.read_text() + "\n// drifted\n")
                if remove:
                    (deployed / "Scripting" / remove).unlink()
                if touch_future:
                    victim = next(iter(sorted((deployed / "Scripting").glob("*.cs"))))
                    os.utime(victim, (2_000_000_000, 2_000_000_000))  # 2033

            if log is not None:
                (save / "build_log.txt").write_text(log)

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
        code, out = self.run_check(log=build_log(BUILT))
        self.assertEqual(code, 0, out)
        self.assertIn("OK -", out)

    # -- refusing to answer without evidence ------------------------------------------

    def test_missing_log_is_an_error_not_a_pass(self):
        code, out = self.run_check(log=None)
        self.assertEqual(code, 2, out)
        self.assertIn("no build log at", out)

    def test_mod_not_deployed(self):
        code, out = self.run_check(log=build_log(BUILT), deploy=False)
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "deployed")

    # -- the verdict must be about *this* source --------------------------------------

    def test_deployed_source_differs(self):
        code, out = self.run_check(log=build_log(BUILT), edit="Raven_Options.cs")
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "identical")

    def test_deployed_source_missing_a_file(self):
        code, out = self.run_check(log=build_log(BUILT), remove="Raven_Options.cs")
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "identical")

    def test_log_older_than_deployed_source(self):
        code, out = self.run_check(log=build_log(BUILT), touch_future=True)
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "fresh")

    def test_log_from_long_before_the_source(self):
        code, out = self.run_check(log=build_log(BUILT, stamp=ANCIENT))
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "fresh")

    # -- reading the compile verdict --------------------------------------------------

    def test_mod_disabled_is_not_a_pass(self):
        """The failure this script exists to prevent: nothing compiled, nothing complained."""
        code, out = self.run_check(
            log=build_log(["Loading path: /", "Skipping, state: Disabled"])
        )
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "built")
        self.assertIn("Options -> Mods", out)

    def test_compile_failure(self):
        code, out = self.run_check(
            log=build_log(
                [
                    "Loading path: /",
                    "Compiling 40 files...",
                    "Failure :(",
                    "== COMPILER ERRORS ==",
                    "Raven_Options.cs(12,5): error CS0103: no such name",
                ]
            )
        )
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "built")
        self.assertIn("CS0103", out, "the diagnostics must reach the reader")

    def test_compiler_threw(self):
        code, out = self.run_check(
            log=build_log(
                [
                    "Loading path: /",
                    "Compiling 40 files...",
                    "Exception compiling mod assembly: boom",
                ]
            )
        )
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "built")

    def test_no_verdict_either_way(self):
        code, out = self.run_check(
            log=build_log(["Loading path: /", "Compiling 40 files..."])
        )
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "built")

    def test_section_absent(self):
        code, out = self.run_check(log=build_log(BUILT, title="A DIFFERENT MOD"))
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "built")

    def test_file_count_disagrees(self):
        code, out = self.run_check(
            log=build_log([ln.replace("40 files", "39 files") for ln in BUILT])
        )
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "count")

    # -- built is not the same as loaded ----------------------------------------------

    def test_absent_from_load_order(self):
        code, out = self.run_check(log=build_log(BUILT, load_order=("SomeOtherMod",)))
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "loaded")

    def test_empty_load_order(self):
        code, out = self.run_check(log=build_log(BUILT, load_order=()))
        self.assertEqual(code, 1, out)
        self.assertFinding(out, "loaded")


if __name__ == "__main__":
    unittest.main()
