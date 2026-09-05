#!/usr/bin/env python3
"""Author a Qud tile from an ASCII map, and refuse anything the game would render wrong.

**Qud tiles are not free-form images.** A sprite is 16x24 RGBA with exactly three pixel values, and
the renderer assigns meaning to two of them: white takes the blueprint's `ColorString`, black takes
its `DetailColor`, and transparent is ground. All 41 sprites in `mod/Textures` follow that without
exception — a fourth colour, or a wrong size, is not a style choice but a sprite the game will not
tint. Nothing downstream says so, which is the reason this exists rather than a drawing program.

Written for #865, where `Vixy_SleepSuppressor` needed a sprite of its own because the tile it named
did not exist. The map format is the useful half: a tile small enough to write as text is a tile you
can review in a diff, iterate on in seconds, and see the shape of without opening anything.

    ................
    ....########....     '#'  white       -> the ColorString
    ..###*####*###..     '*'  black       -> the DetailColor
    ...##########...     '.'  transparent -> ground
    ....#*####*#....
    ...            (24 rows of 16, exactly)

**Pure Python on purpose.** Writing a PNG is a header, one zlib stream and a checksum, and the
alternative was making every contributor install ImageMagick to change a sprite. The preview does its
own nearest-neighbour scaling for the same reason.

Usage:

    python3 tools/make_tile.py sprite.map mod/Textures/items/Vixy_Thing.png
    python3 tools/make_tile.py sprite.map out.png --preview big.png --scale 12

Name the output the way its neighbours are named: `mod/Textures/items/` holds `Vixy_PascalCase.png`
and blueprints reference it with the same extension, while `mod/Textures/Subtypes/` writes `.bmp`
against a `.png`. Qud resolves either, so nothing tells you when you have picked the wrong one — see
`AGENTS.md`.
"""

from __future__ import annotations

import argparse
import struct
import sys
import zlib
from pathlib import Path

WIDTH = 16
HEIGHT = 24

# The three values, and the only three. Keyed by the map character that produces each.
PIXELS = {
    "#": (255, 255, 255, 255),  # ColorString
    "*": (0, 0, 0, 255),  # DetailColor
    ".": (0, 0, 0, 0),  # ground
}


class MapError(ValueError):
    """The map is not a shape the game can render."""


def parse(text: str) -> list[list[tuple[int, int, int, int]]]:
    """Turn an ASCII map into rows of RGBA, refusing anything off-spec.

    Every failure here is one the game would accept silently and render wrong, so each is an error
    rather than a warning: a short row shifts every pixel after it, and an unknown character has no
    defensible default.
    """
    rows = [line for line in text.strip("\n").split("\n") if not line.startswith("//")]
    if len(rows) != HEIGHT:
        raise MapError(f"need exactly {HEIGHT} rows, got {len(rows)}")
    out = []
    for y, row in enumerate(rows):
        if len(row) != WIDTH:
            raise MapError(f"row {y} is {len(row)} wide, need exactly {WIDTH}")
        bad = sorted(set(row) - set(PIXELS))
        if bad:
            raise MapError(
                f"row {y} uses {bad}, and only {sorted(PIXELS)} mean anything to the renderer"
            )
        out.append([PIXELS[char] for char in row])
    return out


def png(rows: list[list[tuple[int, int, int, int]]]) -> bytes:
    """An RGBA PNG. Colour type 6, filter 0 on every row — the shape ImageMagick writes too."""
    raw = b"".join(b"\x00" + b"".join(bytes(px) for px in row) for row in rows)

    def chunk(kind: bytes, payload: bytes) -> bytes:
        body = kind + payload
        return (
            struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))
        )

    header = struct.pack(">IIBBBBB", len(rows[0]), len(rows), 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def preview(
    rows: list[list[tuple[int, int, int, int]]],
    scale: int = 12,
    main: tuple[int, int, int] = (255, 255, 255),
    detail: tuple[int, int, int] = (48, 48, 48),
    ground: tuple[int, int, int] = (20, 20, 20),
) -> bytes:
    """The same tile tinted and scaled, so the shape can be judged before it is committed.

    Defaults approximate a white `ColorString` on Qud's dark ground, which is what the suppressor
    uses. Pass others to check a sprite against the colours its blueprint actually sets — a shape
    that reads in the abstract can still vanish into its biome, which is what §18.4b is about.
    """
    flat = []
    for row in rows:
        line = []
        for r, g, b, a in row:
            if a == 0:
                colour = ground
            elif (r, g, b) == (255, 255, 255):
                colour = main
            else:
                colour = detail
            line.extend([(*colour, 255)] * scale)
        flat.extend([line] * scale)
    return png(flat)


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a Qud tile from an ASCII map.")
    ap.add_argument("map", help="the ASCII map, 24 rows of 16 using # * .")
    ap.add_argument("out", help="where to write the 16x24 RGBA PNG")
    ap.add_argument("--preview", help="also write a scaled, tinted preview here")
    ap.add_argument("--scale", type=int, default=12, help="preview scale (default 12)")
    args = ap.parse_args()

    try:
        rows = parse(Path(args.map).read_text(encoding="utf-8"))
    except MapError as exc:
        print(f"FAIL - {args.map}: {exc}", file=sys.stderr)
        return 1

    Path(args.out).write_bytes(png(rows))
    print(f"wrote {args.out} ({WIDTH}x{HEIGHT} RGBA, 3 values)")
    if args.preview:
        Path(args.preview).write_bytes(preview(rows, args.scale))
        print(f"wrote {args.preview} (x{args.scale})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
