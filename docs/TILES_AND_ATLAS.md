# Tiles and the sprite atlas — findings

**Status:** reference notes. Sprite work is parked; this is what was learned.
**Target:** Caves of Qud 2.0.211.x

---

## 1. Where the tiles live

Not on disk. They are packed into `Data/resources.assets` (291 MB) as Unity objects:

- **~27,500 MonoBehaviour objects** — one per tile, each an atlas *entry*: a name plus a rect
- **~20 Texture2D objects** named `Kobold_DynamicAtlas_<Category>_1` — the actual pixels

Categories and counts: Walls 8309, Walls2 5661, Tiles 5592, Tiles2 1961, Items 1373,
**Creatures 1364**, Terrain 1037, Liquids 678, UI 358, Water 272, Furniture 259, Text 257,
Abilities 236, Mutations 96, Deaths 5.

`Kobold_DynamicAtlas_Creatures_1` is 1024×1024 RGBA32.

### 1.1 The entry struct

Each tile's MonoBehaviour, after `m_GameObject` / `m_Enabled` / `m_Script` / name and two
GUID strings, carries 14 ints. The ones that matter:

```
[8]=width(16)  [9]=height(24)  [10]=x  [11]=y  [12]=width  [13]=height
```

`x` is always a multiple of **18**, `y` a multiple of **26** — so the atlas is a grid of
18×26 cells holding 16×24 tiles, with 2px of gutter. Unity's texture origin is bottom-left,
so the crop is `(x, 1024 - y - h, x + w, 1024 - y)`.

### 1.2 The trap that cost the most time

**Do not take the image as the last `w*h*4` bytes of the Texture2D object.** A Texture2D
ends with an `m_StreamData` record — 16 bytes for an inline (non-streamed) texture. Slicing
from the end therefore starts 16 bytes late, which is **4 pixels**, and every row of the
atlas comes out rolled sideways by 4.

The symptom is subtle and easy to rationalise: sprites still look like animals, but each one
is missing its leftmost 4 columns and has 4 columns of its neighbour welded onto the right.
Goats lose their horns, boars lose their snouts, and the debris on the right reads as
"Qud's stray-pixel style".

Correct approach — find the length-prefixed blob:

```python
NEED = w * h * 4
cands = [i for i in range(300)
         if i + 4 + NEED <= len(b) and struct.unpack('<i', b[i:i+4])[0] == NEED]
data = b[cands[-1] + 4 : cands[-1] + 4 + NEED]
```

For the Creatures atlas the prefix is at offset 124, data at 128, with 16 trailing bytes.

### 1.3 Tile paths in Creatures.xml are inconsistent

Four shapes appear, all referring to the same asset:

```
creatures/sw_dog.bmp
Creatures/sw_salamander.bmp
creatures\sw_glowfish.bmp          <- backslash
Assets_Content_Textures_Creatures_sw_goat.bmp
```

Reduce both the XML attribute and the atlas key to a bare basename and match **exactly**.
Substring matching resolves `sw_dog` to `sw_cherub_dog` and `sw_tortoise` to
`sw_cherub_tortoise`.

---

## 2. There are TWO creature tilesets

This matters more than it sounds.

| | `sw_*` | `Creatures-*` |
|---|---|---|
| count | ~1,141 | 223 |
| wired to blueprints | yes | mostly not — named by grid position (`Creatures-2-11`) |
| DetailColor use | ~20% of pixels | **0% — single colour** |
| edge/area | 0.66 | 0.63 |
| 4-connected pieces | 6 | 8 |
| run length | 2.93 | 2.88 |

The `sw_*` set is what the game actually renders for creatures. The `Creatures-*` set is
cleaner and more readable — `Creatures-Pig` has an obvious snout where `sw_boar` is close to
a featureless blob (109 solid pixels, 3 detail pixels).

A handful of `Creatures-*` tiles are named (`Ape`, `Baboon`, `Croc`, `Goat`, `Pig`, `Skunk`,
`Snail`, `Tortoise`); the rest are grid coordinates.

---

## 3. Style spec — measured on the *corrected* atlas

Animal subset of `Creatures-*`, 28–33 tiles:

| Metric | Median | p10 | p90 |
|---|---|---|---|
| body pixels | 93 | 56 | 122 |
| edge/area | 0.63 | 0.50 | 0.80 |
| 4-connected pieces | 8 | 2 | 20 |
| 8-connected pieces | **1** | 1 | 1.6 |
| run length | 2.88 | 1.9 | 4.8 |
| bbox fill | 43% | 34% | 55% |
| L/R asymmetry | 58% | 41% | 77% |

The two numbers that define the idiom:

- **4-connected ≈ 8, 8-connected ≈ 1.** Vanilla tiles break into many orthogonally-separate
  fragments that still touch **diagonally**. Negative space is load-bearing; detached pixels
  read as paws, hooves and limbs. Forcing a tile to be one orthogonally-connected blob is
  wrong.
- **Legs step.** A leg descends one column as it goes down, which is how a tile stays
  4-fragmented while remaining a single diagonal mass.

Also: `sw_dog` shows only **one or two** legs clearly. Drawing all four square-on reads as a
diagram, not a creature.

> **Numbers measured before 2025-08 in this project's notes were taken on the 4px-shifted
> atlas and are wrong.** The shifted figures said fill 37% and px 82; the truth is 43% and 93.

---

## 4. Tile format for new art

16×24 PNG. Black → `TileColor`, white → `DetailColor`, transparent → background.
`shadermode:1` in `modconfig.json` enables true colour.

Render previews against the camera background `0F252B`, not white.

---

## 5. Tooling

`tools/atlas_extract.py` — parses the Unity serialized file by hand (no UnityPy; it is not
available from the package index in the build environment), extracts any
`Kobold_DynamicAtlas_*` texture and dumps named tiles as PNGs.

Useful for: checking new art against real vanilla tiles, measuring style metrics, and
confirming which sprite a blueprint's `Tile` attribute actually resolves to.
