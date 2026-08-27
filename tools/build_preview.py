#!/usr/bin/env python3
"""Regenerate mod/preview.png — the mod manager and Steam Workshop image.

    python3 tools/build_preview.py            # write mod/preview.png
    python3 tools/build_preview.py out.png    # write elsewhere, to eyeball first

Needs Pillow, so it stays outside the validation gate the way its shell predecessor did -
tools/validate_mod.py is Python-stdlib-only precisely so every contributor can run it. Change
the design, run this, commit the result.

Stratigraphic Terminal — the design, whose reasoning is in docs/PREVIEW_DESIGN.md.

A cross-section. Strata stack downward like sediment, thick quiet layers separated by thin events;
one vertical intrusion pierces the whole column and is the only vertical permitted. Below it, a
plinth carries the label. Every band is an integer number of Qud's own 16x24 character cells, so
the forms are quantised even where they read as deposited.

Seen through an instrument rather than directly: scan lines at a fixed interval, a vignette closing
the corners. Both are meant to be discovered on a second look, not noticed on the first.

Designed for the small view first. At 128px the strata, the intrusion and the title still resolve,
and the annotation is built to dissolve gracefully rather than smear.
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 512
CELL_W, CELL_H = 16, 24  # Qud's own character cell
COLS = W // CELL_W  # 32
ROWS = 21  # 21 * 24 = 504, leaving a 4px margin top and bottom
Y0 = (H - ROWS * CELL_H) // 2

# The plinth is reserved before anything is drawn. The label must never depend on how tall the
# field happens to be - that is how text walks off a canvas.
FIELD_ROWS = 14
PLINTH_ROWS = ROWS - FIELD_ROWS

# GeistMono, SIL Open Font License. Point FONTS at any directory holding GeistMono-Bold.ttf and
# GeistMono-Regular.ttf, or set QUD_PREVIEW_FONTS. The generated PNG is committed, so nothing
# needs this script to build or play the mod - charter rule 4's "no build step" is untouched.
FONTS = Path(
    os.environ.get(
        "QUD_PREVIEW_FONTS",
        Path.home()
        / "Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin"
        / "e9775754-2cca-4f67-904a-fe8a1bd1a07f/704e84b0-0b0d-4b63-be0f-d61606a61517"
        / "skills/canvas-design/canvas-fonts",
    )
)

# Caves of Qud's fixed 18, named for what each does here rather than for what it is.
GROUND = (15, 59, 58)  # #0f3b3a  the dark room
GROUND_2 = (21, 83, 82)  # #155352
BONE = (177, 201, 195)  # #b1c9c3
TAN = (152, 135, 95)  # #98875f
GOLD = (207, 192, 65)  # #cfc041
RUST = (215, 66, 0)  # #d74200
AMBER = (233, 159, 16)  # #e99f10
MOSS = (0, 148, 3)  # #009403
GREEN = (0, 196, 32)  # #00c420
EMBER = (241, 95, 34)  # #f15f22
OXIDE = (166, 74, 46)  # #a64a2e
ICE = (119, 191, 207)  # #77bfcf
WHITE = (255, 255, 255)

# Read downward. The warm register takes the field - salt glare and canopy, the surface world as
# it actually looks - and the cool is the minority that separates. Loud is not noisy: few masses,
# large, saturated, each earning its thickness.
STRATA = [
    (2, MOSS),  # the canopy, given the mass it needs to hold against the warm field
    (1, GREEN),
    (1, GROUND),  # the cut: the only cool below the canopy, and the eye's rest
    (3, AMBER),  # the glare
    (2, GOLD),
    (1, EMBER),
    (3, RUST),
    (1, OXIDE),  # the floor
]
assert sum(r for r, _ in STRATA) == FIELD_ROWS

INTRUSION_COL = 21  # off-centre: the spine sits near a third, not on the half


def cell(x: int, y: int) -> tuple[int, int, int, int]:
    return (x * CELL_W, Y0 + y * CELL_H, (x + 1) * CELL_W, Y0 + (y + 1) * CELL_H)


def build() -> Image.Image:
    img = Image.new("RGB", (W, H), GROUND)
    d = ImageDraw.Draw(img)

    top = 0
    bands: list[tuple[int, int, tuple[int, int, int]]] = []
    for rows, colour in STRATA:
        d.rectangle((0, Y0 + top * CELL_H, W, Y0 + (top + rows) * CELL_H), fill=colour)
        bands.append((top, rows, colour))
        top += rows

    # Inclusions: single cells one step lighter than the band holding them, placed by a fixed rule
    # rather than by chance. Accumulation, not noise - and only in the quiet layers, since a thin
    # event is already saying something. The contrast sits deliberately near the threshold of
    # sight: it should reward a close look and vanish at a glance.
    for band_top, rows, colour in bands:
        if rows < 2:
            continue
        lighter = tuple(min(255, v + 9) for v in colour)
        for r in range(rows):
            for c in range(COLS):
                if (c * 5 + (band_top + r) * 7) % 13 == 0:
                    d.rectangle(cell(c, band_top + r), fill=lighter)

    # The intrusion. Half a cell wide, piercing every stratum, the brightest value in the piece and
    # spent only here.
    x0 = INTRUSION_COL * CELL_W + 4
    d.rectangle((x0 - 2, Y0, x0 + 10, Y0 + FIELD_ROWS * CELL_H), fill=GROUND)
    d.rectangle((x0 + 2, Y0, x0 + 6, Y0 + FIELD_ROWS * CELL_H), fill=WHITE)

    # The plinth, drawn last so the intrusion terminates cleanly against it.
    plinth_y = Y0 + FIELD_ROWS * CELL_H
    d.rectangle((0, plinth_y, W, H), fill=GROUND)
    d.rectangle((0, plinth_y, W, plinth_y + 1), fill=GROUND_2)  # the cut face

    # Depth annotation at the left margin: a tick at each boundary, a figure at every second one.
    tick = ImageFont.truetype(str(FONTS / "GeistMono-Regular.ttf"), 9)
    for i, (band_top, _, _) in enumerate(bands):
        y = Y0 + band_top * CELL_H
        d.rectangle((0, y, 6, y), fill=GROUND)
        if i % 2 == 0 and band_top:
            d.text((10, y + 2), f"{band_top * 12:03d}", font=tick, fill=(70, 58, 30))
    return img


def label(img: Image.Image) -> Image.Image:
    """A specimen label, not a title. Monospaced and letterspaced wide, small enough to belong to
    the instrument rather than the author - except the name, which carries the weight."""
    d = ImageDraw.Draw(img)
    plinth_y = Y0 + FIELD_ROWS * CELL_H

    sub = ImageFont.truetype(str(FONTS / "GeistMono-Regular.ttf"), 16)
    fine = ImageFont.truetype(str(FONTS / "GeistMono-Regular.ttf"), 11)

    def width(text, font, track):
        return sum(d.textlength(c, font=font) for c in text) + track * (len(text) - 1)

    def spaced(text, font, fill, track, y):
        x = (W - width(text, font, track)) / 2
        for ch in text:
            d.text((x, y), ch, font=font, fill=fill)
            x += d.textlength(ch, font=font) + track

    # The name is one line and must sit inside a measured margin, so the size is solved for
    # rather than chosen: step down until it fits, then stop.
    name = "QUD EXPANDED"
    target = W - 2 * 34
    size, track = 56, 6
    while size > 20:
        title = ImageFont.truetype(str(FONTS / "GeistMono-Bold.ttf"), size)
        if width(name, title, track) <= target:
            break
        size -= 1

    # Coloured by position, not by membership: "QUD" is the first three characters, and testing
    # `ch in "QUD"` would gild the D and the E's neighbours inside EXPANDED too.
    y = plinth_y + 14
    x = (W - width(name, title, track)) / 2
    for i, ch in enumerate(name):
        d.text((x, y), ch, font=title, fill=GOLD if i < 3 else WHITE)
        x += d.textlength(ch, font=title) + track

    # Clear the descender rather than the em box: Q carries a tail, and a rule that touches it
    # reads as a mistake however small the overlap.
    rule = y + int(size * 1.28) + 10
    d.rectangle((W / 2 - 96, rule, W / 2 + 96, rule), fill=(58, 106, 104))

    spaced("COMMUNITY EDITION", sub, ICE, 5, rule + 13)
    credit_y = rule + 38
    spaced("MURA  ·  VIXYGREY", fine, (104, 144, 141), 3, credit_y)

    # Nothing falls off the page: assert it rather than trusting the eye.
    assert credit_y + 11 <= H - 20, (
        f"credit line reaches {credit_y + 11}, past the bottom margin"
    )
    return img


def scanlines(img: Image.Image) -> Image.Image:
    """Horizontal lines at a fixed interval, read as the tooth of the paper rather than an effect."""
    px = img.load()
    for y in range(0, H, 3):
        for x in range(W):
            r, g, b = px[x, y]
            px[x, y] = (int(r * 0.9), int(g * 0.9), int(b * 0.9))
    return img


def vignette(img: Image.Image) -> Image.Image:
    """The corners close: an admission that the view is instrumented rather than direct."""
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    c = W / 2
    maxd = math.hypot(c, c)
    for r in range(int(maxd), 0, -2):
        v = 255 - int(190 * max(0.0, (r / maxd - 0.66) / 0.34) ** 1.7)
        md.ellipse((c - r, c - r, c + r, c + r), fill=v)
    mask = mask.filter(ImageFilter.GaussianBlur(12))
    return Image.composite(img, Image.new("RGB", (W, H), (5, 20, 20)), mask)


def main() -> None:
    if not (FONTS / "GeistMono-Bold.ttf").is_file():
        raise SystemExit(
            f"GeistMono not found under {FONTS}.\n"
            "Set QUD_PREVIEW_FONTS to a directory holding GeistMono-Bold.ttf and "
            "GeistMono-Regular.ttf."
        )
    img = vignette(scanlines(label(build())))
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("mod/preview.png")
    img.save(out)
    proof = out.with_name(out.stem + "-128.png")
    img.resize((128, 128), Image.LANCZOS).save(proof)
    print(f"wrote {out} ({W}x{H}) and {proof}, the mod-manager proof")


if __name__ == "__main__":
    main()
