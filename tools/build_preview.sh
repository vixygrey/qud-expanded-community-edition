#!/usr/bin/env bash
#
# Regenerate mod/preview.png — the Workshop preview image.
#
#     tools/build_preview.sh              # write mod/preview.png
#     tools/build_preview.sh out.png      # write somewhere else, to eyeball first
#
# The image is Mura's original CoQ Expanded logo with two fork marks layered on top: a green
# "- CE" after "Expanded", and "& VixyGrey" under "by TLR".
#
# WHY THIS EXISTS
#
# The generated PNG is committed, so nothing needs this script to build or play the mod — charter
# rule 4's "no build step" is untouched. It exists because the alternative is that the next person
# to change the title or add a maintainer re-does the compositing by hand in an image editor and
# has to guess at the sizes, angles and green. Those are recorded below instead.
#
# NOT part of the validation gate and deliberately not run in CI: it needs ImageMagick and a font
# that only ships with macOS, and tools/validate_mod.py is Python-stdlib-only precisely so that
# every contributor can run it. Change the image, run this, commit the result.
#
# REQUIREMENTS
#
#   magick      ImageMagick 7
#   MarkerFelt  macOS system font. Override with PREVIEW_FONT=/path/to/font.ttf on other
#               platforms — the marks will not match the committed image, so check the result.
#   oxipng      optional; used to shrink the PNG if installed
#
# CREDIT (charter rule 3, non-negotiable)
#
# tools/preview-base.png is Mura's artwork, byte-identical to `git show upstream-2.2:preview.png`.
# It is composited in unmodified and stays the dominant element. The fork's marks are set in a
# deliberately different face so they read as tacked on rather than as part of the original logo.
# Do not "fix" that mismatch — it is the point. See docs/STYLEGUIDE.md §7.3.
#
# It lives in tools/ rather than mod/ because everything in mod/ ships to subscribers.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

BASE="tools/preview-base.png"
OUT="${1:-mod/preview.png}"
FONT="${PREVIEW_FONT:-/System/Library/Fonts/MarkerFelt.ttc}"

GREEN='#8CFF3B' # venomous green fill
DARK='#12380A'  # outline, so the glyphs keep their edge against the halo
GLOW='#5BFF00'  # halo

CW=504
CH=382 # output canvas
LX=6
LY=4 # where Mura's logo sits inside it

# Text sizes and angles. CE_PT was 48 until a thumbnail check: docs/STYLEGUIDE.md §7.3 requires
# the image to survive being displayed small, and "- CE" stopped being legible around 120px wide.
CE_PT=54
CE_ROT=9 # droops right, as if squeezed in after the fact
VG_PT=50
VG_ROT=-3

# --- guards ------------------------------------------------------------------------------------
command -v magick >/dev/null || {
    echo "error: ImageMagick 7 ('magick') not found." >&2
    exit 1
}
[ -f "$BASE" ] || {
    echo "error: missing $BASE" >&2
    exit 1
}
[ -f "$FONT" ] || {
    echo "error: font not found: $FONT" >&2
    echo "       On non-macOS, set PREVIEW_FONT to a marker/handwriting face." >&2
    exit 1
}

# Every offset below is measured against the 418x312 original. A different base would place the
# marks silently wrong rather than fail, so refuse instead.
base_size=$(magick identify -format '%wx%h' "$BASE")
[ "$base_size" = "418x312" ] || {
    echo "error: $BASE is $base_size, expected 418x312." >&2
    echo "       The mark positions are measured against the original logo. Re-measure the" >&2
    echo "       text bands (see below) before changing the base image." >&2
    exit 1
}

# --- composition -------------------------------------------------------------------------------
#
# Text bands in the base image, measured with:
#     magick tools/preview-base.png -crop <band> +repage -alpha off -colorspace gray \
#            -threshold 20% -format '%@' info:
#
#     "CoQ"       x 127..295  y  32..110
#     "Expanded"  x  26..395  y 110..190
#     "by TLR"    x  63..359  y 192..284

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# Render green marker text, rotate it, and wrap it in a toxic bloom.
# Echoes the halo's margin so the caller can position the *text* rather than the padded layer.
mktext() { # $1=text  $2=pointsize  $3=rotation  $4=outfile
    magick -background none -fill "$GREEN" -stroke "$DARK" -strokewidth 2 \
        -font "$FONT" -pointsize "$2" label:"$1" -trim +repage "$work/t.png"
    magick "$work/t.png" -background none -rotate "$3" +repage "$work/tr.png"
    magick "$work/tr.png" -bordercolor none -border 18 \
        \( +clone -background "$GLOW" -shadow 70x5+0+0 \) \
        \( +clone -background "$GLOW" -shadow 55x11+0+0 \) \
        -reverse -background none -layers merge +repage "$4"
    local rw gw
    rw=$(magick identify -format '%w' "$work/tr.png")
    gw=$(magick identify -format '%w' "$4")
    echo $(((gw - rw) / 2))
}

ce_pad=$(mktext '- CE' "$CE_PT" "$CE_ROT" "$work/ce.png")
vg_pad=$(mktext '& VixyGrey' "$VG_PT" "$VG_ROT" "$work/vg.png")

vg_w=$(magick identify -format '%w' "$work/vg.png")
vg_text_w=$((vg_w - 2 * vg_pad))

# "- CE" hangs off the tail of "Expanded" (which ends at x=395), sitting low against its baseline.
ce_x=$((LX + 393 - ce_pad))
ce_y=$((LY + 138 - ce_pad))

# "& VixyGrey" centred under "by TLR", whose centre is x=211 in the base image.
vg_x=$((LX + 211 - vg_text_w / 2 - vg_pad))
vg_y=$((LY + 292 - vg_pad))

magick -size "${CW}x${CH}" xc:black \
    "$BASE" -geometry "+${LX}+${LY}" -composite \
    "$work/ce.png" -geometry "+${ce_x}+${ce_y}" -composite \
    "$work/vg.png" -geometry "+${vg_x}+${vg_y}" -composite \
    -depth 8 "$OUT"

command -v oxipng >/dev/null && oxipng -o 4 --strip safe -q "$OUT"

echo "wrote $OUT — $(magick identify -format '%wx%h, %b' "$OUT")"

# Steam rejects previews over 1 MB (docs/STYLEGUIDE.md §7.3).
if [ "$(wc -c <"$OUT")" -gt 1000000 ]; then
    echo "error: over Steam's 1 MB preview limit." >&2
    exit 1
fi
