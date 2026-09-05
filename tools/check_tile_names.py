#!/usr/bin/env python3
"""Every `Tile=` this mod writes must name a texture the game actually has.

**A tile name is a string with no referent in the game's data**, so nothing else in this repo can
check one. Qud renders a missing tile as a solid coloured block — content that looks finished in the
diff, passes every static gate, and is only wrong to somebody standing in front of it. #865.

Three of these had shipped when this was written:

- `Terrain/sw_brush_2.bmp` and two siblings on `Vixy_Dunelace` (#858), invented rather than taken
  from the game, and caught only by walking the salt flats.
- `Items/sw_nanoinjector.bmp` on `Vixy_SleepSuppressor`, wrong from the day it shipped.
- `Items/sw_nightvcyber.bmp` on `Raven_SteelFist`, wrong since before this fork — unnoticed because
  it is the weapon steel hand bones grant and those cannot be taken at chargen, so almost nobody has
  held one.

**The texture list is exact, which took three attempts to establish.** A filesystem search finds
nothing: the textures are packed into Unity assets rather than sitting on disk, and I twice concluded
from that a name could only be checked heuristically — once against "does vanilla XML reference it",
which is a proxy that reports a real sprite as missing whenever no blueprint happens to use it, and
once against a sighting in the character-creation UI, which was not even looking at the sprite in
question.

Unity stores each asset's *name* as a plain string in `Data/resources.assets`, in the form
`Assets_Content_Textures_Terrain_sw_flowers_bunched_1.bmp`. So the real set is recoverable with a
regex over that one file — 27,461 of them — and this check is exact, with no allowlist and no
possible false positive.

**It reads the installed game and skips when there is none**, the same shape as `compile_scripting`
and the snapshot hooks. Embedding 27,461 names in `tools/qud-api.json` would have roughly doubled
that file, and CI has no game to compare against in any case. `--require` turns the skip into a
failure.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# The same roots `check_vanilla_drift` uses, but pointed one level up: the textures live in
# `Data/resources.assets`, beside `StreamingAssets` rather than inside it.
DEFAULT_GAME_PATHS = [
    "~/Library/Application Support/Steam/steamapps/common/Caves of Qud/CoQ.app/Contents/Resources/Data",
    "~/.steam/steam/steamapps/common/Caves of Qud/CoQ_Data",
    "C:/Program Files (x86)/Steam/steamapps/common/Caves of Qud/CoQ_Data",
]

MOD = Path(__file__).resolve().parent.parent / "mod"
TEXTURES = MOD / "Textures"

# `Assets_Content_Textures_<Category>_<name>.<ext>`, which is one token with the separators
# flattened to underscores. Anchored on the prefix so ordinary strings elsewhere in the file cannot
# match.
ASSET = re.compile(rb"Assets_Content_Textures_[A-Za-z0-9_\-]+\.[A-Za-z]{2,4}")

# Both spellings, because `Tiles=` on a RandomTile builder is comma-separated and holds the majority
# of the names in this mod. Reading only `Tile=` would have caught one of dunelace's three.
TILE_ATTR = re.compile(r'\bTiles?="([^"]+)"')
OBJECT = re.compile(r'<object Name="([^"]+)"(.*?)</object>', re.DOTALL)


def find_game(explicit: str | None) -> Path | None:
    """The game's `Data` directory, or None."""
    candidates = [explicit] if explicit else DEFAULT_GAME_PATHS
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if (path / "resources.assets").is_file():
            return path
    return None


def game_tiles(data: Path) -> set[str]:
    """Every texture the game ships, keyed the way mod XML spells one: `Category/name.ext`."""
    blob = (data / "resources.assets").read_bytes()
    found = set()
    for match in ASSET.findall(blob):
        name = match.decode("ascii", "replace")
        rest = name[len("Assets_Content_Textures_") :]
        # The category is the first segment; everything after it is the file name, which itself
        # contains underscores. Splitting once is the whole of it.
        category, _, stem = rest.partition("_")
        if stem:
            found.add(f"{category}/{stem}".lower())
    return found


def shipped_tiles() -> set[str]:
    """Textures this mod ships itself, keyed the same way and without the extension.

    Extension-insensitive on purpose: the XML says `.bmp` and every file in `mod/Textures` is a
    `.png`, which is the convention the existing sprites already use and which Qud resolves.
    """
    if not TEXTURES.is_dir():
        return set()
    out = set()
    for path in TEXTURES.rglob("*"):
        if path.is_file():
            rel = path.relative_to(TEXTURES).as_posix()
            out.add(rel.rsplit(".", 1)[0].lower())
    return out


def mod_tiles(root: Path) -> dict[str, set[tuple[str, str]]]:
    """Every tile the mod names, mapped to the (file, blueprint) pairs that name it."""
    used: dict[str, set[tuple[str, str]]] = {}
    for path in sorted(root.rglob("*.xml")):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for name, body in OBJECT.findall(text):
            for attr in TILE_ATTR.findall(body):
                for tile in (piece.strip() for piece in attr.split(",")):
                    if tile:
                        used.setdefault(tile, set()).add((path.name, name))
    return used


def broken(
    used: dict[str, set[tuple[str, str]]], have: set[str], ships: set[str]
) -> list[str]:
    out = []
    for tile in sorted(used):
        key = tile.lower()
        if key in have or key.rsplit(".", 1)[0] in ships:
            continue
        who = ", ".join(f"{obj} ({fn})" for fn, obj in sorted(used[tile]))
        out.append(f"{tile} - named by {who}, and the game has no such texture")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--game", help="path to the game's Data directory")
    ap.add_argument(
        "--require",
        action="store_true",
        help="fail instead of skipping when the game is missing",
    )
    args = ap.parse_args()

    data = find_game(args.game)
    if data is None:
        # Loud on purpose; a skip that reads like a pass is the failure mode this file exists for.
        print(
            f"{'ERROR' if args.require else 'SKIPPED'} - no Caves of Qud install found, so tile "
            f"names cannot be checked.\nPass --game <path to the game's Data directory> to point "
            f"at one.",
            file=sys.stderr if args.require else sys.stdout,
        )
        return 1 if args.require else 0

    have = game_tiles(data)
    if not have:
        print(
            f"ERROR - read no texture names from {data / 'resources.assets'}, which means the "
            f"format changed rather than that every tile is fine.",
            file=sys.stderr,
        )
        return 1

    used = mod_tiles(MOD)
    problems = broken(used, have, shipped_tiles())
    if problems:
        print(f"FAIL - {len(problems)} tile name(s) name nothing:")
        for line in problems:
            print(f"  {line}")
        print(
            "\nQud renders a missing tile as a solid coloured block. Take a name the game already "
            "uses, or ship the sprite under mod/Textures/."
        )
        return 1

    print(
        f"OK - {len(used)} tile name(s) across the mod all resolve, against "
        f"{len(have)} game textures and {len(shipped_tiles())} shipped with the mod"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
