#!/usr/bin/env python3
"""Compile mod/Scripting/ against the installed game's assemblies. Python 3 standard library only.

    python3 tools/compile_scripting.py

`tools/check_build_log.py` reads back the verdict Qud recorded on its last launch. This is the other
half of #134: it compiles the C# here and now, without needing the game to have been run, so a
mistake is caught before it is deployed rather than after.

It shells out to Roslyn from an installed .NET SDK, with `-nostdlib+ -noconfig`, and references the
game's own DLLs rather than any reference-assembly package:

    mscorlib.dll  System.dll  System.Core.dll  Assembly-CSharp.dll

That is the entire reference set - no Unity assembly, no NuGet restore, no csproj, no network. It is
four DLLs because the 40 files between them use nine namespaces, all `XRL.*` or `System.*`.
Referencing what the game actually loads also removes any question of version skew: these are the
same binaries Qud compiles against.

## What this can and cannot tell you

It **cannot produce a false pass through a missing reference.** An unreferenced type is an error, not
a silent omission, so the narrow reference set can only ever be stricter than the game's. A file that
starts using, say, `UnityEngine` will fail here and compile in game - a false *failure*, which is
visible, named, and fixed by adding one reference.

Two real blind spots, both stated rather than papered over:

  language version   pinned to C# 9.0, because this SDK's compiler is newer than the Roslyn Unity
                     embeds and would otherwise accept syntax the game rejects. Pinned low on
                     purpose: wrong in this direction is a false failure, not a false pass.
  preprocessor       Qud defines VERSION_*, BUILD_* and MOD_* symbols when it compiles. Only MOD_* is
                     defined here, derived from manifest.json; the others encode the installed game
                     build, and hardcoding them would rot silently. Nothing in mod/Scripting/ uses a
                     preprocessor directive today, and this warns if that changes.

Nothing is written into `mod/`. The assembly goes to a temporary directory and is deleted - the mod
ships C# for Qud to compile at load time, and a prebuilt DLL in the shipped directory would change
that. There is deliberately no persistent build output to gitignore.

Unlike `check_build_log.py` this needs no game *launch*, so it runs as an ordinary pre-commit hook.
It skips, loudly, when the game or an SDK is absent, because a contributor without either cannot act
on a red hook. `--require` turns that skip into a failure, for when you mean to be sure it ran.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

MOD = Path("mod")
SCRIPTING = MOD / "Scripting"
MANIFEST = MOD / "manifest.json"

MANAGED_DIR_ENV = "QUD_MANAGED_DIR"
DEFAULT_MANAGED_DIR = (
    Path.home()
    / "Library/Application Support/Steam/steamapps/common/Caves of Qud"
    / "CoQ.app/Contents/Resources/Data/Managed"
)

CSC_ENV = "QUD_CSC"

# The whole reference set. Order is irrelevant; the comment is not.
REFERENCES = (
    "mscorlib.dll",  # the base library the game runs on, not this SDK's
    "System.dll",
    "System.Core.dll",  # HashSet<T> and LINQ live here on .NET Framework
    "Assembly-CSharp.dll",  # every XRL.* type the mod touches
)

# Newer than the Roslyn Unity embeds would accept syntax the game rejects. See the module docstring.
LANG_VERSION = "9.0"

# Where an SDK's Roslyn lives, relative to a dotnet root. Ordered by how likely each root is on a
# machine that has any SDK at all: Homebrew (both plain and versioned formulae), the official
# installer, then a dotnet-install.sh user install.
SDK_ROOTS = (
    "/opt/homebrew/opt/dotnet/libexec",
    "/opt/homebrew/opt/dotnet@*/libexec",
    "/opt/homebrew/Cellar/dotnet/*/libexec",
    "/opt/homebrew/Cellar/dotnet@*/*/libexec",
    "/usr/local/share/dotnet",
    "/usr/share/dotnet",  # Linux packages, and the GitHub Actions runner images
    "/usr/lib/dotnet",
    "~/.dotnet",
)


def sdk_version_key(path: Path) -> tuple[int, ...]:
    """Sort SDK directory names numerically, so 10.0.100 beats 9.0.120.

    Counting from csc.dll: parents[0] bincore, [1] Roslyn, [2] the SDK version, [3] sdk, [4] the
    dotnet root. Getting that arithmetic wrong is silent - it yields a root with no `dotnet` beside
    it, so discovery just reports no SDK found, which is why test_finds_this_machines_sdk exists.
    """
    return tuple(int(p) for p in re.findall(r"\d+", path.parents[2].name)) or (0,)


def find_compiler(override: str | None) -> tuple[Path, Path] | None:
    """Return (dotnet, csc.dll), or None if no SDK can be found.

    csc.dll is a managed assembly, so it needs the `dotnet` host that shipped with it - hence the
    pair. Both are derived from one path: <root>/sdk/<version>/Roslyn/bincore/csc.dll sits under the
    same <root> as the `dotnet` binary.
    """
    explicit = override or os.environ.get(CSC_ENV)
    candidates: list[Path] = []

    if explicit:
        candidates = [Path(explicit).expanduser()]
    else:
        # DOTNET_ROOT first: whoever set it meant that SDK, not whichever one a glob finds.
        roots_to_scan = list(SDK_ROOTS)
        if os.environ.get("DOTNET_ROOT"):
            roots_to_scan.insert(0, os.environ["DOTNET_ROOT"])
        for pattern in roots_to_scan:
            expanded = Path(pattern).expanduser()
            # Two globs to resolve: the root pattern, then the SDK version under it.
            roots = (
                sorted(Path("/").glob(str(expanded).lstrip("/")))
                if "*" in pattern
                else [expanded]
            )
            for root in roots:
                candidates += root.glob("sdk/*/Roslyn/bincore/csc.dll")
        candidates.sort(key=sdk_version_key, reverse=True)

    for csc in candidates:
        if not csc.is_file():
            continue
        root = csc.parents[4]  # see sdk_version_key for the arithmetic
        # Homebrew puts the host at <root>/dotnet and also links <cellar>/bin/dotnet; the official
        # installer only has the former.
        for host in (root / "dotnet", root.parent / "bin" / "dotnet"):
            if host.is_file() and os.access(host, os.X_OK):
                return host, csc
    return None


def managed_dir(override: str | None) -> Path:
    if override:
        return Path(override).expanduser()
    from_env = os.environ.get(MANAGED_DIR_ENV)
    if from_env:
        return Path(from_env).expanduser()
    return DEFAULT_MANAGED_DIR


def mod_symbol() -> str:
    """The MOD_* symbol Qud defines for this mod, derived rather than hardcoded."""
    mod_id = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))["id"]
    return "MOD_" + re.sub(r"[^A-Za-z0-9]", "", mod_id).upper()


def warn_about_preprocessor(sources: list[Path]) -> None:
    """The one place this gate's define set could diverge from the game's."""
    directives = re.compile(
        r"^\s*#\s*(if|elif|else|endif|define|undef)\b", re.MULTILINE
    )
    using_it = [
        p.name for p in sources if directives.search(p.read_text(encoding="utf-8-sig"))
    ]
    if using_it:
        print(
            f"warning: {', '.join(using_it)} use(s) preprocessor directives, and this check "
            f"defines only {mod_symbol()} - not the VERSION_* / BUILD_* symbols Qud defines from "
            "the installed game build. Conditional code may not be covered. See the module "
            "docstring.",
            file=sys.stderr,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--managed-dir",
        help=f"Qud's Managed directory (default: ${MANAGED_DIR_ENV}, else {DEFAULT_MANAGED_DIR})",
    )
    parser.add_argument(
        "--csc", help=f"path to csc.dll (default: ${CSC_ENV}, else autodetected)"
    )
    parser.add_argument(
        "--require",
        action="store_true",
        help="fail instead of skipping when the game or an SDK is missing",
    )
    parser.add_argument(
        "--out", help="keep the compiled assembly at this path instead of discarding it"
    )
    args = parser.parse_args()

    if not MOD.is_dir():
        print("error: run from the repository root (mod/ not found)", file=sys.stderr)
        return 2

    sources = sorted(SCRIPTING.glob("*.cs"))
    if not sources:
        print(f"error: no .cs files in {SCRIPTING}/", file=sys.stderr)
        return 2

    def unavailable(reason: str, remedy: str) -> int:
        # Loud on purpose. A skip that reads like a pass is the failure mode this whole issue is
        # about, so it never prints alongside the word OK.
        stream = sys.stderr if args.require else sys.stdout
        print(
            f"{'ERROR' if args.require else 'SKIPPED'} - {reason}\n{remedy}",
            file=stream,
        )
        return 2 if args.require else 0

    managed = managed_dir(args.managed_dir)
    missing = [name for name in REFERENCES if not (managed / name).is_file()]
    if missing:
        return unavailable(
            f"cannot compile: {managed} is missing {', '.join(missing)}",
            f"Install Caves of Qud, or point --managed-dir (or ${MANAGED_DIR_ENV}) at its "
            "Managed directory. The C# is not compiled by any other check.",
        )

    compiler = find_compiler(args.csc)
    if compiler is None:
        return unavailable(
            "cannot compile: no .NET SDK found",
            "Install one (`brew install dotnet`), or point --csc (or "
            f"${CSC_ENV}) at an SDK's Roslyn/bincore/csc.dll.",
        )
    host, csc = compiler

    warn_about_preprocessor(sources)

    with tempfile.TemporaryDirectory() as tmp:
        # Written to a temporary directory and discarded: the mod ships C# for Qud to compile at
        # load time, so a DLL must never land in mod/. Nothing persists, so there is nothing to
        # gitignore either.
        out = Path(args.out).expanduser() if args.out else Path(tmp) / "scripting.dll"
        command = [
            str(host),
            str(csc),
            "-nologo",
            "-target:library",
            "-nostdlib+",  # use the game's mscorlib, not this SDK's
            "-noconfig",  # and none of the SDK's default references
            f"-langversion:{LANG_VERSION}",
            f"-define:{mod_symbol()}",
            f"-out:{out}",
            *(f"-reference:{managed / name}" for name in REFERENCES),
            *(str(p) for p in sources),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)

    diagnostics = [
        ln for ln in (result.stdout + result.stderr).splitlines() if ln.strip()
    ]
    errors = [ln for ln in diagnostics if re.search(r": error [A-Z]+\d+:", ln)]
    warnings = [ln for ln in diagnostics if re.search(r": warning [A-Z]+\d+:", ln)]

    if errors or result.returncode != 0:
        print(f"FAIL - {len(errors) or 'unknown'} compile error(s):", file=sys.stderr)
        for line in diagnostics:
            print(f"  {line}", file=sys.stderr)
        if not diagnostics:
            print(
                f"  compiler exited {result.returncode} with no output", file=sys.stderr
            )
        return 1

    for line in warnings:
        print(f"  {line}")
    print(
        f"OK - {len(sources)} file(s) compile against {managed.name}/ "
        f"(C# {LANG_VERSION}, {len(warnings)} warning(s))"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
