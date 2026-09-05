#!/usr/bin/env python3
"""Tests for `check_tile_names`.

Every case here has a negative twin, because a check that cannot fail is the trap
`docs/LESSONS.md` records under *the check you drop is the one that was working* — and this one
guards a class of defect that is invisible everywhere else, so a silently vacuous version of it
would be worse than none.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_tile_names


class GameTiles(unittest.TestCase):
    """Reading the texture names back out of a Unity assets blob."""

    def _fake(self, *names: str) -> Path:
        tmp = Path(tempfile.mkdtemp())
        blob = b"".join(b"\x00\x08\x00" + n.encode() for n in names)
        (tmp / "resources.assets").write_bytes(blob)
        return tmp

    def test_reads_a_name_in_the_packed_form(self) -> None:
        data = self._fake("Assets_Content_Textures_Terrain_sw_flowers_bunched_1.bmp")
        self.assertIn(
            "terrain/sw_flowers_bunched_1.bmp", check_tile_names.game_tiles(data)
        )

    def test_keeps_underscores_in_the_file_name(self) -> None:
        """Only the *first* segment is the category; the rest is the name and keeps its underscores.

        Splitting on every underscore would turn `sw_wheat_stem` into `sw`, which matches nothing
        and would report every tile in the mod as broken.
        """
        data = self._fake("Assets_Content_Textures_Items_sw_wheat_stem.bmp")
        self.assertEqual(check_tile_names.game_tiles(data), {"items/sw_wheat_stem.bmp"})

    def test_ignores_strings_that_are_not_texture_assets(self) -> None:
        data = self._fake("Assets_Content_Audio_Terrain_sw_not_a_texture.bmp")
        self.assertEqual(check_tile_names.game_tiles(data), set())


class Broken(unittest.TestCase):
    HAVE: ClassVar[set[str]] = {"items/sw_carbidehand.bmp", "terrain/sw_grass1.bmp"}

    def test_a_name_the_game_has_is_quiet(self) -> None:
        used = {"Items/sw_carbidehand.bmp": {("Cybernetics.xml", "Raven_SteelFist")}}
        self.assertEqual(check_tile_names.broken(used, self.HAVE, set()), [])

    def test_a_name_the_game_does_not_have_is_reported_with_its_blueprint(self) -> None:
        used = {
            "Items/sw_nanoinjector.bmp": {("Cybernetics.xml", "Vixy_SleepSuppressor")}
        }
        found = check_tile_names.broken(used, self.HAVE, set())
        self.assertEqual(len(found), 1)
        self.assertIn("sw_nanoinjector", found[0])
        self.assertIn("Vixy_SleepSuppressor", found[0])

    def test_case_does_not_matter(self) -> None:
        """Vanilla writes `items/` and `Items/` interchangeably and Qud resolves either.

        A case-sensitive compare reported seven perfectly good tiles as missing the first time I
        ran this by hand.
        """
        used = {"items/SW_CarbideHand.bmp": {("Armor.xml", "Whatever")}}
        self.assertEqual(check_tile_names.broken(used, self.HAVE, set()), [])

    def test_a_sprite_the_mod_ships_counts(self) -> None:
        used = {
            "Items/vixy_sleep_suppressor.bmp": {
                ("Cybernetics.xml", "Vixy_SleepSuppressor")
            }
        }
        ships = {"items/vixy_sleep_suppressor"}
        self.assertEqual(check_tile_names.broken(used, self.HAVE, ships), [])

    def test_a_shipped_sprite_matches_across_extensions(self) -> None:
        """The XML says `.bmp` and every file in `mod/Textures` is a `.png`."""
        used = {"Subtypes/icePsionic.bmp": {("Subtypes.xml", "Whatever")}}
        self.assertEqual(
            check_tile_names.broken(used, self.HAVE, {"subtypes/icepsionic"}), []
        )

    def test_a_shipped_sprite_that_is_not_there_still_reports(self) -> None:
        """The direction that would make the mod/Textures escape hatch vacuous."""
        used = {"Items/vixy_nothing.bmp": {("Cybernetics.xml", "Whatever")}}
        self.assertEqual(
            len(check_tile_names.broken(used, self.HAVE, {"items/vixy_other"})), 1
        )


class Parsing(unittest.TestCase):
    def _mod(self, body: str) -> Path:
        tmp = Path(tempfile.mkdtemp())
        (tmp / "Test.xml").write_text(
            f"<objects>\n{body}\n</objects>", encoding="utf-8"
        )
        return tmp

    def test_a_plain_tile_attribute_is_read(self) -> None:
        root = self._mod(
            '  <object Name="Thing"><part Name="Render" Tile="Items/a.bmp" /></object>'
        )
        self.assertIn("Items/a.bmp", check_tile_names.mod_tiles(root))

    def test_a_random_tile_builder_is_split_on_commas(self) -> None:
        """#858's defect was two-thirds inside a `Tiles=` list.

        A check reading only `Tile=` would have caught one name of the three and called the file
        clean.
        """
        root = self._mod(
            '  <object Name="Plant">'
            '<builder Name="RandomTile" Tiles="Terrain/a.bmp,Terrain/b.bmp,Terrain/c.bmp" />'
            "</object>"
        )
        found = check_tile_names.mod_tiles(root)
        self.assertEqual(
            set(found), {"Terrain/a.bmp", "Terrain/b.bmp", "Terrain/c.bmp"}
        )

    def test_the_blueprint_is_recorded_so_the_report_can_name_it(self) -> None:
        root = self._mod(
            '  <object Name="Thing"><part Name="Render" Tile="Items/a.bmp" /></object>'
        )
        self.assertEqual(
            check_tile_names.mod_tiles(root)["Items/a.bmp"], {("Test.xml", "Thing")}
        )


class MissingGame(unittest.TestCase):
    def test_find_game_wants_the_assets_file_not_just_the_directory(self) -> None:
        """A `Data` directory without `resources.assets` is not an install to read."""
        tmp = Path(tempfile.mkdtemp())
        self.assertIsNone(check_tile_names.find_game(str(tmp)))
        (tmp / "resources.assets").write_bytes(b"")
        self.assertEqual(check_tile_names.find_game(str(tmp)), tmp)


if __name__ == "__main__":
    unittest.main()
