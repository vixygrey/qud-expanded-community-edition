#!/usr/bin/env python3
"""Install `mod/` into the game's Mods directory, as a dev build or a publish build.

The directory Qud loads a mod from is the same directory the Workshop uploader publishes from,
which puts two needs in direct conflict. Testing a branch means putting unreleased content there.
Publishing means putting exactly `main` there. Doing both by hand, in one directory, means the
difference is something you remember rather than something you can see — and #145 spent twenty
minutes on a wish command that was correct all along, because the install still held `main` while
the shells lived on a branch. A blueprint that does not exist does not fail: `WishSearcher` hands
back the nearest one that does.

Symlinking the directory to `mod/` fixes the testing half and makes the publishing half far worse,
because then `git checkout` decides what ships to subscribers.

So the two builds are made *distinguishable* instead:

    --dev       whatever branch is checked out, with WorkshopId REMOVED and the title suffixed
    --publish   main only, clean, level with origin, validated first, and left exactly as-is

`WorkshopId` is the whole trick. It is the only thing binding an upload to the published item, and
`validate_mod.py`'s `check_workshop_target` documents the semantics this relies on: with the key
absent the uploader treats the mod as unpublished and offers "Create Workshop Id for Mod...", so a
dev build **cannot overwrite the live page**. The safe state becomes a property of the artifact
rather than a thing to remember, and the suffixed title means the in-game mod list says which build
is loaded.

One directory, deliberately. Two would risk both loading at once and declaring every `Raven_`
blueprint twice.

Usage:
    python3 tools/sync_mod.py --dev
    python3 tools/sync_mod.py --publish
    python3 tools/sync_mod.py --dev --dest PATH     # explicit destination
    python3 tools/sync_mod.py --publish --no-fetch  # skip the network, trust the local ref

Nothing here ships: `tools/` is outside `mod/`, which is the only directory the uploader reads.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

MOD = Path("mod")
MANIFEST_ID = "QudExpandedCommunityEdition"
DEV_SUFFIX = " (dev)"

# The mod folder Qud reads, per platform. The install directory is <Mods>/<DEST_NAME>.
DEFAULT_MODS_DIRS = [
    "~/Library/Application Support/com.FreeholdGames.CavesOfQud/Mods",
    "~/.config/unity3d/Freehold Games/CavesOfQud/Mods",
    "~/AppData/LocalLow/Freehold Games/CavesOfQud/Mods",
]
DEST_NAME = "qud-expanded-community-edition"

# Never copied into the install. Finder litter, not mod content.
SKIP_NAMES = {".DS_Store"}


class Problem(Exception):
    """A refusal. The message is written for the person who has to act on it."""


def git(*args: str) -> str:
    """Run git and return stdout, stripped. Raises Problem when git itself fails."""
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise Problem(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def find_mods_dir(explicit: str | None) -> Path:
    """Locate the Mods directory. An explicit path is taken as the destination itself."""
    if explicit:
        return Path(os.path.expanduser(explicit))
    for candidate in DEFAULT_MODS_DIRS:
        p = Path(os.path.expanduser(candidate))
        if p.is_dir():
            return p / DEST_NAME
    raise Problem(
        "Could not find the Caves of Qud Mods directory. Looked in:\n  "
        + "\n  ".join(DEFAULT_MODS_DIRS)
        + "\nPass --dest with the install path if it lives somewhere else."
    )


def check_publish_state(fetch: bool) -> None:
    """Refuse anything that is not exactly the published branch.

    Three separate ways to ship something unintended, and being on the wrong branch is only the
    first. A dirty tree publishes edits nobody has reviewed, and a local `main` behind its remote
    publishes a state that no longer exists — the one that bites when a pull request merged from
    the web and the machine never pulled.
    """
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if branch != "main":
        raise Problem(
            f"On branch {branch!r}, not 'main'. A publish build is main and nothing else.\n"
            f"Use --dev to test this branch instead."
        )

    dirty = git("status", "--porcelain")
    if dirty:
        raise Problem(
            "Working tree is not clean, so the build would carry edits that are in no commit:\n"
            + "\n".join(f"  {line}" for line in dirty.splitlines()[:10])
        )

    if fetch:
        try:
            git("fetch", "--quiet", "origin", "main")
        except Problem as exc:
            raise Problem(
                f"{exc}\nPass --no-fetch to skip this and trust the local ref, but then the "
                f"'level with origin' check below is only as fresh as your last fetch."
            ) from exc

    local = git("rev-parse", "main")
    try:
        remote = git("rev-parse", "origin/main")
    except Problem as exc:
        raise Problem(f"No origin/main to compare against: {exc}") from exc

    if local != remote:
        ahead = git("rev-list", "--count", "origin/main..main")
        behind = git("rev-list", "--count", "main..origin/main")
        raise Problem(
            f"Local main is {ahead} ahead and {behind} behind origin/main.\n"
            f"Publishing an unpulled main ships a state you have not seen; publishing an "
            f"unpushed one ships a state nobody else has.\nPull, push, then try again."
        )


def run_validator() -> None:
    """A publish build runs the gate first. A dev build deliberately does not — it is meant to
    carry work in progress, and a validator failure there is information, not a blocker."""
    result = subprocess.run(
        [sys.executable, "tools/validate_mod.py"],
        capture_output=True,
        text=True,
        check=False,
    )
    sys.stdout.write(result.stdout)
    sys.stdout.write(result.stderr)
    if result.returncode != 0:
        raise Problem("validate_mod.py failed. Nothing was copied.")


def guard_destination(dest: Path) -> None:
    """The destination is deleted and replaced, so refuse anything that is not ours.

    Empty or absent is fine. Otherwise it must carry this mod's own manifest id — which is what
    stops a mistyped --dest from taking out an unrelated mod, or a home directory.
    """
    if not dest.exists():
        return
    if not dest.is_dir():
        raise Problem(f"{dest} exists and is not a directory.")
    contents = [p for p in dest.iterdir() if p.name not in SKIP_NAMES]
    if not contents:
        return
    manifest = dest / "manifest.json"
    if not manifest.is_file():
        raise Problem(
            f"{dest} is not empty and has no manifest.json, so it is not an install of this "
            f"mod. Refusing to delete it. Check --dest."
        )
    try:
        found = json.loads(manifest.read_text(encoding="utf-8-sig")).get("id")
    except json.JSONDecodeError as exc:
        raise Problem(f"{manifest} is not valid JSON: {exc}") from exc
    if found != MANIFEST_ID:
        raise Problem(
            f"{dest} holds a mod with id {found!r}, not {MANIFEST_ID!r}. Refusing to delete "
            f"somebody else's mod. Check --dest."
        )


def copy_tree(src: Path, dest: Path) -> int:
    """Replace dest with src. Returns the number of files written."""
    if dest.exists():
        shutil.rmtree(dest)
    written = 0
    for path in sorted(src.rglob("*")):
        if any(part in SKIP_NAMES for part in path.parts):
            continue
        target = dest / path.relative_to(src)
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            written += 1
    return written


def manifest_field(name: str) -> str:
    """Read one field out of mod/manifest.json, or refuse.

    The zip's two names both come from here rather than from a constant, which is the whole point of
    #314: the install directory is `qud-expanded-community-edition` and every published zip contains
    `QudExpandedCommunityEdition`, so the `cp -R` in the manual recipe was a *rename* that read as
    ceremony. Naming the folder from the id removes that hazard by construction.
    """
    path = MOD / "manifest.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Problem(f"cannot read {path}: {exc}") from exc
    value = data.get(name)
    if not isinstance(value, str) or not value.strip():
        raise Problem(f"{path} has no usable {name!r}")
    return value.strip()


def check_tag_matches(tag: str, version: str) -> None:
    """A named tag must agree with the manifest version.

    `validate_mod.py` ties the manifest to the changelog; this ties it to the tag the asset is being
    uploaded against. The gap between them is exactly where 2.6.0 became 2.5.1 across three files.
    """
    wanted = tag.removeprefix("v")
    if wanted != version:
        raise Problem(
            f"Tag {tag!r} is version {wanted!r}, but mod/manifest.json says {version!r}.\n"
            f"One of them is wrong, and the zip would be named after the manifest either way."
        )


def build_zip(out_dir: Path, tag: str | None) -> tuple[Path, int]:
    """Assemble the release asset, and return where it landed and how many files it holds.

    Reuses copy_tree rather than reimplementing the file set, so the zip holds exactly what a
    --publish install holds - SKIP_NAMES honoured, nothing else consulted. Building from mod/ rather
    than from the install directory is what closes the stale-build hole: there is no longer a copy
    in between that could belong to a --dev run or to a version before the bump.
    """
    identifier = manifest_field("id")
    version = manifest_field("version")
    if tag:
        check_tag_matches(tag, version)

    archive = out_dir / f"{identifier}-{version}.zip"
    with tempfile.TemporaryDirectory() as staging:
        root = Path(staging) / identifier
        written = copy_tree(MOD, root)
        if archive.exists():
            archive.unlink()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(root.parent))
    return archive, written


def mark_as_dev(dest: Path) -> list[str]:
    """Strip the Workshop binding and label the build. Returns what changed, for the report."""
    notes = []

    workshop = dest / "workshop.json"
    if workshop.is_file():
        data = json.loads(workshop.read_text(encoding="utf-8-sig"))
        removed = data.pop("WorkshopId", None)
        if "Title" in data and not data["Title"].endswith(DEV_SUFFIX):
            data["Title"] += DEV_SUFFIX
        workshop.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        notes.append(
            f"workshop.json: WorkshopId {removed} removed — this build cannot publish over the "
            f"live item"
            if removed is not None
            else "workshop.json: no WorkshopId to remove"
        )

    manifest = dest / "manifest.json"
    if manifest.is_file():
        data = json.loads(manifest.read_text(encoding="utf-8-sig"))
        if "title" in data and not data["title"].endswith(DEV_SUFFIX):
            data["title"] += DEV_SUFFIX
            notes.append(f"manifest.json: title is now {data['title']!r}")
        manifest.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    return notes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install mod/ into the game's Mods directory.",
        epilog="A dev build has no WorkshopId and so cannot overwrite the published item.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--dev",
        action="store_true",
        help="install the current branch, unpublishable and labelled",
    )
    mode.add_argument(
        "--publish",
        action="store_true",
        help="install main verbatim, after the guards and the validator",
    )
    mode.add_argument(
        "--zip",
        action="store_true",
        help="build the release asset from mod/, after the same guards",
    )
    parser.add_argument(
        "--out",
        help="directory to write the zip into (default: the repository root)",
    )
    parser.add_argument(
        "--tag",
        help="the release tag this asset is for; refused unless it matches the manifest version",
    )
    parser.add_argument(
        "--dest", help="install path (default: the game's Mods directory)"
    )
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="skip 'git fetch' during --publish and trust the local ref",
    )
    args = parser.parse_args()

    if not MOD.is_dir():
        print(
            "Run this from the repository root — no mod/ directory here.",
            file=sys.stderr,
        )
        return 2

    try:
        if args.zip:
            check_publish_state(fetch=not args.no_fetch)
            run_validator()
            out_dir = Path(args.out).expanduser() if args.out else Path.cwd()
            if not out_dir.is_dir():
                raise Problem(f"--out {out_dir} is not a directory")
            archive, written = build_zip(out_dir, args.tag)
            print(f"\nRELEASE asset built: {written} files -> {archive}")
            print(f"  from branch main at {git('rev-parse', '--short', 'HEAD')}")
            print(f"  top-level folder: {manifest_field('id')}")
            print(
                f"\n  Upload it with:\n"
                f"    gh release upload v{manifest_field('version')} {archive.name}"
            )
            return 0

        dest = find_mods_dir(args.dest)
        if args.publish:
            check_publish_state(fetch=not args.no_fetch)
            run_validator()
        guard_destination(dest)
        written = copy_tree(MOD, dest)
        notes = mark_as_dev(dest) if args.dev else []
    except Problem as exc:
        print(f"\nRefused: {exc}", file=sys.stderr)
        return 1

    kind = "DEV" if args.dev else "PUBLISH"
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    print(f"\n{kind} build installed: {written} files -> {dest}")
    print(f"  from branch {branch} at {git('rev-parse', '--short', 'HEAD')}")
    for note in notes:
        print(f"  {note}")
    if args.dev:
        print(
            "\n  The in-game mod list will show the (dev) suffix. Restart Qud: it reads the XML "
            "at load,\n  so a running session still holds the previous blueprints."
        )
    else:
        print("\n  Safe to point the Workshop uploader at this directory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
