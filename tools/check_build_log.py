#!/usr/bin/env python3
"""Check that Caves of Qud compiled this mod's C#, using the game's own build log.

    python3 tools/check_build_log.py

Nothing in this repository compiles `mod/Scripting/`. `tools/validate_mod.py` lints it - banned
APIs, `[Serializable]` field layout, a class per part - but lint is not a compiler, and until #134
the only evidence the C# builds at all was that I clicked through the options in-game once.

The game already knows the answer. Qud compiles every enabled mod through Roslyn at launch and
writes the verdict to `build_log.txt` in the save directory, in these words - read out of
`Assembly-CSharp.dll`, not guessed:

    === <TITLE IN CAPS> ===         one section per mod
    Skipping, state: Disabled       not built at all
    Compiling 40 files...
    Success :)  /  Failure :(
    == COMPILER ERRORS ==           the diagnostics, when it failed

So this script compiles nothing. It reads that verdict back, and refuses to accept it unless the
verdict is demonstrably about the working tree:

  deployed    the game's `Mods/` copy of this mod exists, found by manifest id rather than by
              folder name, since the folder is named however it was installed
  identical   every `mod/Scripting/*.cs` is byte-identical to that copy. The game compiles the
              copy, and it is a copy rather than a symlink, so without this a green log can
              belong to source that no longer exists here
  fresh       the log is newer than that copy. A verdict recorded before the last deployment says
              nothing about what is deployed now
  built       the section exists, was not skipped, and reports success with no compiler errors
  count       the file count the game reports matches the number of `.cs` files here
  loaded      the mod reached `FINAL LOAD ORDER`, so it built *and* was accepted

`identical` and `fresh` are the point, not padding. Without them this is a green light wired to a
log that may predate the code - which is worse than having no check, because it reads as evidence.
Everything here fails loudly; nothing is treated as passing because it could not be determined.

This cannot run in CI: the log is written by a copy of the game on a developer's machine. The
compile gate in #134 has the same limit for the same reason. Python 3 standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

MOD = Path("mod")
SCRIPTING = MOD / "Scripting"
MANIFEST = MOD / "manifest.json"

# Overridable because only the macOS Steam layout is known here; GOG, itch and Linux all differ.
SAVE_DIR_ENV = "QUD_SAVE_DIR"
DEFAULT_SAVE_DIR = (
    Path.home() / "Library/Application Support/com.FreeholdGames.CavesOfQud"
)

TIMESTAMP = re.compile(r"^\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\] ?(.*)$")
# Three equals for a mod, four for a phase. The inner [^=] guards keep "==== BUILDING MODS ===="
# from parsing as a mod named "= BUILDING MODS =".
SECTION = re.compile(r"^=== ([^=].*[^=]) ===$")
PHASE = re.compile(r"^==== (.+) ====$")
LOAD_ORDER = re.compile(r"^(\d+): (.+)$")
COMPILING = re.compile(r"^Compiling (\d+) files?\.\.\.$")
SKIPPING = re.compile(r"^Skipping, state: (.+)$")

SUCCESS = "Success :)"
FAILURE = "Failure :("
COMPILER_ERRORS = "== COMPILER ERRORS =="
COMPILE_EXCEPTION = "Exception compiling mod assembly: "
LOAD_ORDER_PHASE = "FINAL LOAD ORDER"


class Findings:
    def __init__(self) -> None:
        self.items: list[tuple[str, str]] = []

    def add(self, check: str, detail: str) -> None:
        self.items.append((check, detail))


def save_dir(override: str | None) -> Path:
    if override:
        return Path(override).expanduser()
    from_env = os.environ.get(SAVE_DIR_ENV)
    if from_env:
        return Path(from_env).expanduser()
    return DEFAULT_SAVE_DIR


def parse_log(text: str) -> tuple[dict[str, list[str]], list[str], list[datetime]]:
    """Split the log into per-mod sections, the final load order, and every timestamp."""
    sections: dict[str, list[str]] = {}
    order: list[str] = []
    stamps: list[datetime] = []
    current: str | None = None
    phase: str | None = None

    for raw in text.splitlines():
        stamped = TIMESTAMP.match(raw)
        if stamped:
            stamps.append(datetime.fromisoformat(stamped.group(1)))
            line = stamped.group(2)
        else:
            line = raw

        as_phase = PHASE.match(line)
        if as_phase:
            phase, current = as_phase.group(1), None
            continue

        as_section = SECTION.match(line)
        if as_section:
            current = as_section.group(1)
            sections[current] = []
            continue

        if current is not None:
            sections[current].append(line)
        elif phase == LOAD_ORDER_PHASE:
            entry = LOAD_ORDER.match(line)
            if entry:
                order.append(entry.group(2))

    return sections, order, stamps


def find_deployed(f: Findings, mods_dir: Path, mod_id: str) -> Path | None:
    """Locate the game's copy of this mod by manifest id, not by folder name."""
    if not mods_dir.is_dir():
        f.add("deployed", f"{mods_dir} does not exist - is Caves of Qud installed?")
        return None

    for candidate in sorted(p for p in mods_dir.iterdir() if p.is_dir()):
        manifest = candidate / "manifest.json"
        if not manifest.is_file():
            continue
        try:
            found = json.loads(manifest.read_text(encoding="utf-8-sig")).get("id")
        except json.JSONDecodeError:
            continue
        if found == mod_id:
            return candidate

    f.add(
        "deployed",
        f"no mod with id {mod_id!r} under {mods_dir} - deploy this mod and launch the game",
    )
    return None


def deployed_title(deployed: Path, fallback: str) -> str:
    """The title the game saw, which is the deployed manifest's rather than the repository's."""
    manifest = deployed / "manifest.json"
    try:
        found = json.loads(manifest.read_text(encoding="utf-8-sig")).get("title")
    except (OSError, json.JSONDecodeError):
        return fallback
    return found or fallback


def check_identical(f: Findings, deployed: Path) -> Path | None:
    """The game compiles the deployed copy, so a verdict only counts if it matches ours."""
    deployed_scripting = deployed / "Scripting"
    if not deployed_scripting.is_dir():
        f.add("identical", f"{deployed_scripting} does not exist in the deployed copy")
        return None

    here = {p.name: p.read_bytes() for p in SCRIPTING.glob("*.cs")}
    there = {p.name: p.read_bytes() for p in deployed_scripting.glob("*.cs")}

    for name in sorted(set(here) - set(there)):
        f.add("identical", f"{name} is missing from the deployed copy")
    for name in sorted(set(there) - set(here)):
        f.add("identical", f"{name} is in the deployed copy but not in {SCRIPTING}/")
    for name in sorted(set(here) & set(there)):
        if here[name] != there[name]:
            f.add("identical", f"{name} differs from the deployed copy")

    return deployed_scripting


def check_fresh(f: Findings, deployed_scripting: Path, stamps: list[datetime]) -> None:
    """A green verdict recorded before the current source was deployed is not evidence."""
    if not stamps:
        f.add(
            "fresh", "the build log carries no timestamps, so its age cannot be checked"
        )
        return

    built = max(stamps)
    newest = max(
        ((p.stat().st_mtime, p.name) for p in deployed_scripting.glob("*.cs")),
        default=None,
    )
    if newest is None:
        f.add("fresh", f"no .cs files in {deployed_scripting}")
        return

    # The log writes local time with no offset, so its stamps are naive. Making both sides
    # local-aware compares the two instants rather than two wall clocks.
    changed = datetime.fromtimestamp(newest[0], tz=timezone.utc).astimezone()
    if built.astimezone() < changed:
        f.add(
            "fresh",
            f"the log was written {built:%Y-%m-%d %H:%M:%S} but the deployed "
            f"{newest[1]} changed {changed:%Y-%m-%d %H:%M:%S} - relaunch the game",
        )


def check_built(
    f: Findings, sections: dict[str, list[str]], title: str, expected: int
) -> None:
    """Read the compile verdict, and refuse anything that is not an explicit success."""
    header = title.upper()
    body = sections.get(header)
    if body is None:
        f.add(
            "built",
            f"no section {header!r} in the build log - the log records "
            f"{len(sections)} mod(s), and the section is titled after manifest.json's title",
        )
        return

    skipped = next(
        (SKIPPING.match(line) for line in body if SKIPPING.match(line)), None
    )
    if skipped:
        f.add(
            "built",
            f"the game skipped this mod (state: {skipped.group(1)}) so nothing was "
            "compiled - enable it in Options -> Mods and relaunch",
        )
        return

    if FAILURE in body or COMPILER_ERRORS in body:
        diagnostics = [line for line in body if line and line != FAILURE]
        f.add("built", "the mod failed to compile: " + " | ".join(diagnostics[:20]))
        return

    for line in body:
        if line.startswith(COMPILE_EXCEPTION):
            f.add("built", f"the compiler itself threw: {line}")
            return

    compiling = next(
        (COMPILING.match(line) for line in body if COMPILING.match(line)), None
    )
    if compiling is None:
        f.add("built", "the section reports no 'Compiling N files...' line")
        return

    if SUCCESS not in body:
        f.add("built", "the section reports neither success nor failure")
        return

    reported = int(compiling.group(1))
    if reported != expected:
        f.add(
            "count",
            f"the game compiled {reported} file(s) but {SCRIPTING}/ holds {expected} - "
            "the deployed copy is out of step",
        )


def check_loaded(f: Findings, order: list[str], mod_id: str) -> None:
    if not order:
        f.add("loaded", "the build log has no FINAL LOAD ORDER section")
    elif mod_id not in order:
        f.add(
            "loaded",
            f"{mod_id} compiled but is absent from FINAL LOAD ORDER ({len(order)} mod(s) loaded)",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--save-dir",
        help=f"Qud save directory (default: ${SAVE_DIR_ENV}, else {DEFAULT_SAVE_DIR})",
    )
    args = parser.parse_args()

    if not MOD.is_dir():
        print("error: run from the repository root (mod/ not found)", file=sys.stderr)
        return 2

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    mod_id, title = manifest["id"], manifest["title"]
    expected = len(list(SCRIPTING.glob("*.cs")))

    saves = save_dir(args.save_dir)
    log_path = saves / "build_log.txt"
    if not log_path.is_file():
        print(
            f"error: no build log at {log_path}\n"
            f"Launch Caves of Qud once with this mod enabled, or point --save-dir "
            f"(or ${SAVE_DIR_ENV}) at the right directory.",
            file=sys.stderr,
        )
        return 2

    f = Findings()
    sections, order, stamps = parse_log(log_path.read_text(encoding="utf-8-sig"))

    deployed = find_deployed(f, saves / "Mods", mod_id)
    if deployed is not None:
        deployed_scripting = check_identical(f, deployed)
        if deployed_scripting is not None:
            check_fresh(f, deployed_scripting, stamps)
        # The log names its section after the title the GAME saw, which is the deployed
        # manifest's - and `sync_mod.py --dev` deliberately suffixes that with " (dev)" so the
        # in-game mod list says which build is loaded. Reading the repository's title here made
        # this check impossible to pass against a dev build, which is the only build worth
        # checking: a publish build is `main`, verified before it is installed rather than after.
        # Same reasoning `find_deployed` already applies to the folder name. See #342.
        title = deployed_title(deployed, title)

    check_built(f, sections, title, expected)
    check_loaded(f, order, mod_id)

    if f.items:
        print(f"FAIL - {len(f.items)} problem(s):", file=sys.stderr)
        for check, detail in sorted(f.items):
            print(f"  [{check}] {detail}", file=sys.stderr)
        print(
            "\nThis check reports what the game did on its last launch. Fix the cause, "
            "redeploy, relaunch - do not reason around a stale verdict.",
            file=sys.stderr,
        )
        return 1

    built = max(stamps) if stamps else None
    when = f" at {built:%Y-%m-%d %H:%M:%S}" if built else ""
    print(
        f"OK - the game compiled all {expected} file(s) in {SCRIPTING}/ without errors"
        f"{when}, from source byte-identical to this tree, and loaded {mod_id}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
