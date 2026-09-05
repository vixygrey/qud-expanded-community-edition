#!/usr/bin/env python3
"""Tests for `make_tile`.

The refusals matter more than the output here. Every one of them is a mistake the game accepts
silently and renders wrong — a fourth colour is simply not tinted, a short row shifts every pixel
after it — so a version of this that wrote the file anyway would be worse than no tool at all.
"""

from __future__ import annotations

import struct
import sys
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import make_tile

BLANK = "\n".join(["." * 16] * 24)


def decode(data: bytes) -> tuple[int, int, list[tuple[int, int, int, int]]]:
    """Width, height and pixels, read back from a PNG this module wrote."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos, width, height, raw = 8, 0, 0, b""
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        kind = data[pos + 4 : pos + 8]
        payload = data[pos + 8 : pos + 8 + length]
        if kind == b"IHDR":
            width, height, depth, colour = struct.unpack(">IIBB", payload[:10])
            assert (depth, colour) == (8, 6), "must be 8-bit RGBA"
        elif kind == b"IDAT":
            raw += payload
        pos += 12 + length
    flat = zlib.decompress(raw)
    stride = width * 4 + 1
    pixels = []
    for y in range(height):
        row = flat[y * stride : (y + 1) * stride]
        assert row[0] == 0, "filter must be 0"
        pixels.extend(tuple(row[1 + x * 4 : 5 + x * 4]) for x in range(width))
    return width, height, pixels


class Refusals(unittest.TestCase):
    def test_too_few_rows(self) -> None:
        with self.assertRaises(make_tile.MapError) as caught:
            make_tile.parse("\n".join(["." * 16] * 23))
        self.assertIn("24 rows", str(caught.exception))

    def test_too_many_rows(self) -> None:
        with self.assertRaises(make_tile.MapError):
            make_tile.parse("\n".join(["." * 16] * 25))

    def test_a_short_row_is_named(self) -> None:
        """Off-by-one in one row shifts every pixel after it, and the tile still 'works'."""
        rows = ["." * 16] * 24
        rows[7] = "." * 15
        with self.assertRaises(make_tile.MapError) as caught:
            make_tile.parse("\n".join(rows))
        self.assertIn("row 7", str(caught.exception))

    def test_a_fourth_colour_is_refused(self) -> None:
        """The renderer tints white and black. Anything else is a pixel it will not touch."""
        rows = ["." * 16] * 24
        rows[3] = "#" * 15 + "X"
        with self.assertRaises(make_tile.MapError) as caught:
            make_tile.parse("\n".join(rows))
        self.assertIn("'X'", str(caught.exception))

    def test_a_valid_map_is_accepted(self) -> None:
        """The direction that would make every refusal above vacuous."""
        self.assertEqual(len(make_tile.parse(BLANK)), 24)


class Output(unittest.TestCase):
    def test_the_png_is_16x24_rgba(self) -> None:
        width, height, pixels = decode(make_tile.png(make_tile.parse(BLANK)))
        self.assertEqual((width, height), (16, 24))
        self.assertEqual(len(pixels), 16 * 24)

    def test_each_character_maps_to_its_documented_value(self) -> None:
        rows = ["." * 16] * 24
        rows[0] = "#*" + "." * 14
        _, _, pixels = decode(make_tile.png(make_tile.parse("\n".join(rows))))
        self.assertEqual(
            pixels[0], (255, 255, 255, 255), "'#' must be the ColorString pixel"
        )
        self.assertEqual(pixels[1], (0, 0, 0, 255), "'*' must be the DetailColor pixel")
        self.assertEqual(pixels[2], (0, 0, 0, 0), "'.' must be transparent")

    def test_only_the_three_values_ever_appear(self) -> None:
        rows = ["#*.." * 4] * 24
        _, _, pixels = decode(make_tile.png(make_tile.parse("\n".join(rows))))
        self.assertEqual(set(pixels), set(make_tile.PIXELS.values()))

    def test_comments_are_stripped(self) -> None:
        make_tile.parse("// a note about the shape\n" + BLANK)


class Preview(unittest.TestCase):
    def test_scaling_is_nearest_neighbour_and_square(self) -> None:
        width, height, _ = decode(make_tile.preview(make_tile.parse(BLANK), scale=4))
        self.assertEqual((width, height), (64, 96))

    def test_the_ground_is_flattened_rather_than_left_transparent(self) -> None:
        """A preview is for looking at, so transparency would just show whatever is behind it."""
        _, _, pixels = decode(make_tile.preview(make_tile.parse(BLANK), scale=1))
        self.assertTrue(all(px[3] == 255 for px in pixels))


class ShippedSprite(unittest.TestCase):
    def test_the_suppressor_map_still_builds_the_sprite_that_ships(self) -> None:
        """The map in tools/tiles is the source, so it has to stay in step with mod/Textures.

        Editing one without the other is the failure this catches: nothing else in the repo relates
        a sprite to the map it came from.
        """
        here = Path(__file__).resolve().parent
        source = here / "tiles" / "Vixy_SleepSuppressor.map"
        shipped = (
            here.parent / "mod" / "Textures" / "items" / "Vixy_SleepSuppressor.png"
        )
        if not source.is_file() or not shipped.is_file():
            self.skipTest("sprite or its map is absent")
        built = make_tile.png(make_tile.parse(source.read_text(encoding="utf-8")))
        self.assertEqual(
            decode(built)[2],
            decode(shipped.read_bytes())[2],
            "tools/tiles/Vixy_SleepSuppressor.map no longer builds the sprite that ships",
        )


if __name__ == "__main__":
    unittest.main()
