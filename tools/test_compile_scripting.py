#!/usr/bin/env python3
"""Tests for tools/compile_scripting.py. Python 3 standard library only.

    python3 -m unittest discover -s tools

Two halves, and the split is inherent rather than a shortcut.

The compiling half needs the game's `Assembly-CSharp.dll`, which is proprietary and cannot reach a
runner, so those cases are skipped where it is absent - reported as skips, never as passes. They are
the ones that matter most on a developer's machine: that a broken file actually fails, that the C# 9
pin actually bites, that nothing lands in `mod/`.

The other half needs nothing but the filesystem and runs everywhere: SDK discovery, and the
skip-versus-fail contract. Discovery is worth covering because getting its path arithmetic wrong is
*silent* - a bad root finds no `dotnet` beside it and reports "no SDK found", which is
indistinguishable from a machine that genuinely has none. That bug was written, and shipped as far as
the first run.

Cases build a throwaway source tree (a `mod/manifest.json` and a `mod/Scripting/`) and run the script
with that as its working directory, so a deliberately broken file never goes near the real one.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import compile_scripting as target

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "compile_scripting.py"
REAL_SCRIPTING = REPO / "mod" / "Scripting"
MANIFEST = REPO / "mod" / "manifest.json"

MANAGED = target.managed_dir(None)
HAVE_GAME = all((MANAGED / name).is_file() for name in target.REFERENCES)
HAVE_SDK = target.find_compiler(None) is not None

needs_game = unittest.skipUnless(HAVE_GAME, f"game assemblies not at {MANAGED}")
needs_sdk = unittest.skipUnless(HAVE_SDK, "no .NET SDK on this machine")


class Discovery(unittest.TestCase):
    """No game and no SDK needed: this is pure path arithmetic."""

    def test_an_sdk_on_disk_is_found(self):
        """Independent oracle. A wrong root makes find_compiler silently return None."""
        if os.environ.get(target.CSC_ENV):
            # An explicit override bypasses discovery by design, so there is nothing to assert.
            self.skipTest(f"${target.CSC_ENV} is set, so discovery is not in use")
        on_disk = [
            csc
            for pattern in target.SDK_ROOTS
            for root in sorted(
                Path("/").glob(str(Path(pattern).expanduser()).lstrip("/"))
            )
            for csc in root.glob("sdk/*/Roslyn/bincore/csc.dll")
        ]
        if not on_disk:
            self.skipTest("no SDK installed in any known location")
        self.assertIsNotNone(
            target.find_compiler(None),
            f"csc.dll exists at {on_disk[0]} but discovery found nothing",
        )

    @needs_sdk
    def test_the_discovered_host_actually_runs_the_compiler(self):
        """Catches a host paired with the wrong root, which a None check would not."""
        host, csc = target.find_compiler(None)
        result = subprocess.run(
            [str(host), str(csc), "-version"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_version_key_reads_the_sdk_version(self):
        csc = Path("/x/libexec/sdk/10.0.100/Roslyn/bincore/csc.dll")
        self.assertEqual(target.sdk_version_key(csc), (10, 0, 100))

    def test_newer_sdk_sorts_first(self):
        older = Path("/x/libexec/sdk/9.0.120/Roslyn/bincore/csc.dll")
        newer = Path("/x/libexec/sdk/10.0.100/Roslyn/bincore/csc.dll")
        self.assertGreater(target.sdk_version_key(newer), target.sdk_version_key(older))

    def test_mod_symbol_is_derived_from_the_manifest(self):
        self.assertEqual(target.mod_symbol(), "MOD_QUDEXPANDEDCOMMUNITYEDITION")


class Run(unittest.TestCase):
    def source_tree(self, tmp: str, extra: dict[str, str] | None = None) -> Path:
        """A minimal repo: the manifest and the real .cs files, plus any extra file."""
        root = Path(tmp)
        (root / "mod" / "Scripting").mkdir(parents=True)
        shutil.copy2(MANIFEST, root / "mod" / "manifest.json")
        for cs in REAL_SCRIPTING.glob("*.cs"):
            shutil.copy2(cs, root / "mod" / "Scripting" / cs.name)
        for name, text in (extra or {}).items():
            (root / "mod" / "Scripting" / name).write_text(text)
        return root

    def run_in(self, root: Path, *args: str, env: dict[str, str] | None = None):
        environment = {**os.environ, **(env or {})}
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )

    # -- the skip-versus-fail contract, which needs neither game nor SDK ---------------

    def test_missing_game_skips_but_says_so(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.source_tree(tmp)
            r = self.run_in(root, "--managed-dir", str(root / "nowhere"))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("SKIPPED", r.stdout)
            self.assertNotIn("OK -", r.stdout, "a skip must never read as a pass")

    def test_missing_game_with_require_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.source_tree(tmp)
            r = self.run_in(root, "--require", "--managed-dir", str(root / "nowhere"))
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertIn("ERROR", r.stderr)

    @needs_game
    def test_missing_sdk_skips_but_says_so(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.source_tree(tmp)
            r = self.run_in(root, "--csc", str(root / "no-such-csc.dll"))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("SKIPPED", r.stdout)
            self.assertIn("no .NET SDK found", r.stdout)

    @needs_game
    def test_missing_sdk_with_require_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.source_tree(tmp)
            r = self.run_in(root, "--require", "--csc", str(root / "no-such-csc.dll"))
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_outside_a_repo_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = self.run_in(Path(tmp))
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertIn("repository root", r.stderr)

    # -- the compiling half -----------------------------------------------------------

    @needs_game
    @needs_sdk
    def test_the_real_scripts_compile(self):
        """The control. Without it, a script that always failed would satisfy the rest."""
        with tempfile.TemporaryDirectory() as tmp:
            r = self.run_in(self.source_tree(tmp))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("OK -", r.stdout)

    @needs_game
    @needs_sdk
    def test_a_broken_file_fails_with_its_diagnostic(self):
        broken = (
            "using XRL.UI;\npublic class Raven_Broken { void F() { NoSuchType x; } }\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = self.source_tree(tmp, {"Raven_Broken.cs": broken})
            r = self.run_in(root)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("FAIL", r.stderr)
            self.assertIn(
                "CS0246", r.stderr, "the compiler's diagnostic must reach the reader"
            )

    @needs_game
    @needs_sdk
    def test_a_missing_xrl_member_fails(self):
        """The failure this gate exists for: an XRL API that is not there."""
        bad = "using XRL.UI;\npublic class Raven_Gone { void F() { Options.NoSuchMember(); } }\n"
        with tempfile.TemporaryDirectory() as tmp:
            r = self.run_in(self.source_tree(tmp, {"Raven_Gone.cs": bad}))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertRegex(r.stderr, r"CS\d+")

    @needs_game
    @needs_sdk
    def test_the_language_version_pin_bites(self):
        """C# 10 syntax must be rejected, since Unity's Roslyn is older than this SDK's."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self.source_tree(
                tmp, {"Raven_Modern.cs": "namespace Probe;\nclass X { }\n"}
            )
            r = self.run_in(root)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("CS8773", r.stderr)

    @needs_game
    @needs_sdk
    def test_preprocessor_use_is_warned_about(self):
        """This gate's define set can diverge from the game's; the blind spot stays visible."""
        conditional = (
            "#if MOD_QUDEXPANDEDCOMMUNITYEDITION\npublic class Raven_Cond { }\n#endif\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            r = self.run_in(self.source_tree(tmp, {"Raven_Cond.cs": conditional}))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("preprocessor directives", r.stderr)

    @needs_game
    @needs_sdk
    def test_nothing_is_written_into_mod(self):
        """A prebuilt DLL in mod/ would ship, and would change how the mod loads."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self.source_tree(tmp)
            before = {p.name for p in (root / "mod" / "Scripting").iterdir()}
            self.run_in(root)
            after = {p.name for p in (root / "mod" / "Scripting").iterdir()}
            self.assertEqual(before, after)
            self.assertEqual(list((root / "mod").rglob("*.dll")), [])
            self.assertEqual(list((root / "mod").rglob("*.pdb")), [])


if __name__ == "__main__":
    unittest.main()
