"""Draw the Mowbot palette as a swatch and a mock lawn, so the theme can be judged on screen.

Native tiles are 32 x 32 px; the output is scaled by an integer with nearest-neighbour sampling,
as the game will do, so the pixels stay crisp. Every object is drawn with three tones (light,
mid, dark) and a tinted outline, and casts a soft shadow. Grass varies per tile from a seeded
random generator, so the same lawn always looks the same. Run from anywhere:

    python graphics/swatch.py          # writes palette.png and mock_lawn.png next to this file
"""
import random
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import sprites  # noqa: E402  the hand-authored pixel grids
TILE = 32
SCALE = 3

# The palette from DESIGN.md section 12. Keys are roles, values are hex colours.
PALETTE = {
    "grass cut": "#8fd14f",
    "grass growing": "#6cb83a",
    "grass ripe": "#4f9a2e",
    "grass overgrown": "#3a7a24",
    "scalped": "#a8864a",
    "path (sand)": "#c9a46c",
    "stone": "#8a8f94",
    "outline": "#1e2a1a",
    "mower body": "#e8632b",
    "mower accent": "#f5f0e6",
    "wheels, shadow": "#2b2b2b",
    "station, shirt": "#3b6bc9",
    "flower red": "#e84c6a",
    "flower yellow": "#f3c84b",
    "flower bed soil": "#5a3e2b",
    "fence wood": "#7a5230",
    "hedgehog body": "#6b4a31",
    "hedgehog face": "#d9b48a",
    "skin": "#f0c9a0",
    "hair": "#3a2a1e",
}


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(rgb, factor):
    """Lighten (factor > 1) or darken (factor < 1) a colour, clamped to 0..255."""
    return tuple(max(0, min(255, round(c * factor))) for c in rgb[:3])


def outline_of(rgb):
    """A tinted outline: the colour itself, much darker, never plain black."""
    return shade(rgb, 0.35)


C = {k: hex_to_rgb(v) for k, v in PALETTE.items()}
GRASS_TIERS = [C["grass cut"], C["grass growing"], C["grass ripe"], C["grass overgrown"]]
SHADOW = (20, 30, 15, 90)


def palette_swatch():
    cols, cell, pad = 4, 120, 10
    rows = -(-len(PALETTE) // cols)
    img = Image.new("RGB", (cols * cell + pad, rows * (cell // 2 + 24) + pad), (30, 30, 30))
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    for i, (name, hexv) in enumerate(PALETTE.items()):
        x = pad + (i % cols) * cell
        y = pad + (i // cols) * (cell // 2 + 24)
        w3 = (cell - pad) // 3
        for k, f in enumerate((1.25, 1.0, 0.75)):  # light, mid, dark
            d.rectangle([x + k * w3, y, x + (k + 1) * w3, y + cell // 2], fill=shade(C[name], f))
        d.rectangle([x, y, x + cell - pad, y + cell // 2], outline=outline_of(C[name]))
        d.text((x, y + cell // 2 + 2), name, fill=(220, 220, 220), font=font)
        d.text((x, y + cell // 2 + 12), hexv, fill=(150, 150, 150), font=font)
    img.save(HERE / "palette.png")


# --- helpers -----------------------------------------------------------------------------------

class Canvas:
    """An RGBA image with a shadow layer composited below the sprites."""

    def __init__(self, w, h):
        self.img = Image.new("RGBA", (w, h), (30, 30, 30, 255))
        self.d = ImageDraw.Draw(self.img)

    def shadow(self, box):
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse(box, fill=SHADOW)
        self.img.alpha_composite(layer)
        self.d = ImageDraw.Draw(self.img)

    def paste(self, sprite, xy):
        self.img.alpha_composite(sprite, dest=xy)
        self.d = ImageDraw.Draw(self.img)


def sprite():
    s = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    return s, ImageDraw.Draw(s)


def shaded_ellipse(d, box, colour):
    """A ball: dark base, mid body, light cap, tinted outline."""
    x0, y0, x1, y1 = box
    d.ellipse(box, fill=shade(colour, 0.75), outline=outline_of(colour))
    d.ellipse([x0 + 1, y0 + 1, x1 - 1, y1 - 3], fill=colour)
    d.ellipse([x0 + 3, y0 + 2, x0 + (x1 - x0) // 2 + 1, y0 + (y1 - y0) // 2], fill=shade(colour, 1.25))


def shaded_box(d, box, colour, radius=3):
    """A block: dark bottom and right, mid face, light top-left edge, tinted outline."""
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius, fill=shade(colour, 0.75), outline=outline_of(colour))
    d.rounded_rectangle([x0 + 1, y0 + 1, x1 - 2, y1 - 3], radius, fill=colour)
    d.rounded_rectangle([x0 + 2, y0 + 2, x1 - 4, y0 + 4], radius // 2, fill=shade(colour, 1.2))


# --- tiles -------------------------------------------------------------------------------------

def grass_tile(cv, x, y, tier, stripe=0, seed=0):
    rng = random.Random(seed)
    base = GRASS_TIERS[tier]
    base = shade(base, 1.10) if stripe > 0 else shade(base, 0.90) if stripe < 0 else base
    d = cv.d
    d.rectangle([x, y, x + TILE - 1, y + TILE - 1], fill=base)
    light, dark = shade(base, 1.18), shade(base, 0.82)
    # short blades everywhere, more and taller the higher the tier
    for _ in range(8 + 4 * tier):
        bx, by = x + rng.randrange(2, TILE - 2), y + rng.randrange(3, TILE - 1)
        h = 2 + tier + rng.randrange(0, 2)
        col = dark if rng.random() < 0.6 else light
        d.line([bx, by, bx, by - h], fill=col)
        if tier >= 2:  # a second blade leaning off the first makes a tuft
            d.line([bx + 1, by, bx + 2, by - h + 1], fill=col)
    if tier >= 3:  # overgrown: dark clumps
        for _ in range(3):
            cx, cy = x + rng.randrange(4, TILE - 6), y + rng.randrange(6, TILE - 4)
            d.line([cx, cy, cx - 2, cy - 6], fill=outline_of(base))
            d.line([cx, cy, cx, cy - 7], fill=outline_of(base))
            d.line([cx, cy, cx + 2, cy - 6], fill=outline_of(base))
    if tier <= 1 and rng.random() < 0.45:  # a daisy or buttercup on short grass
        fx, fy = x + rng.randrange(4, TILE - 5), y + rng.randrange(4, TILE - 5)
        petal = C["mower accent"] if rng.random() < 0.6 else C["flower yellow"]
        for px, py in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            d.point((fx + px, fy + py), fill=petal)
        d.point((fx, fy), fill=C["flower yellow"] if petal == C["mower accent"] else C["flower red"])


def scalped_tile(cv, x, y, seed=0):
    rng = random.Random(seed)
    d = cv.d
    base = C["scalped"]
    d.rectangle([x, y, x + TILE - 1, y + TILE - 1], fill=base)
    for _ in range(14):  # dry stubble and bare patches
        px, py = x + rng.randrange(1, TILE - 1), y + rng.randrange(1, TILE - 1)
        d.point((px, py), fill=shade(base, 0.8) if rng.random() < 0.5 else shade(base, 1.15))
    for _ in range(3):
        px, py = x + rng.randrange(3, TILE - 6), y + rng.randrange(3, TILE - 6)
        d.ellipse([px, py, px + 4, py + 3], fill=shade(base, 0.88))


def path_tile(cv, x, y, seed=0):
    rng = random.Random(seed)
    d = cv.d
    base = C["path (sand)"]
    d.rectangle([x, y, x + TILE - 1, y + TILE - 1], fill=base)
    d.rectangle([x, y, x + TILE - 1, y + 1], fill=shade(base, 0.85))  # worn edge
    for _ in range(7):  # pebbles with a light side
        px, py = x + rng.randrange(2, TILE - 4), y + rng.randrange(3, TILE - 3)
        d.ellipse([px, py, px + 2, py + 2], fill=shade(base, 0.78))
        d.point((px, py), fill=shade(base, 1.15))


def flower_bed_tile(cv, x, y, seed=0):
    rng = random.Random(seed)
    d = cv.d
    soil = C["flower bed soil"]
    d.rectangle([x, y, x + TILE - 1, y + TILE - 1], fill=soil)
    for row in range(0, TILE, 4):  # tilled rows
        d.line([x, y + row, x + TILE - 1, y + row], fill=shade(soil, 0.8))
        d.line([x, y + row + 2, x + TILE - 1, y + row + 2], fill=shade(soil, 1.12))
    colours = [C["flower red"], C["flower yellow"], C["mower accent"]]
    for fx, fy in [(7, 9), (21, 7), (12, 21), (24, 22)]:
        px, py = x + fx, y + fy
        leaf = C["grass ripe"]
        d.line([px - 3, py + 3, px, py], fill=leaf)   # leaves
        d.line([px + 3, py + 3, px, py], fill=leaf)
        d.line([px, py + 4, px, py], fill=shade(leaf, 0.8))
        petal = rng.choice(colours)
        for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, -1), (-1, 1), (1, 1)]:
            d.point((px + ox, py + oy), fill=petal)
        d.point((px, py), fill=C["flower yellow"] if petal != C["flower yellow"] else C["flower red"])
        d.point((px - 2, py - 1), fill=shade(petal, 1.2))


def stone_on(cv, x, y):
    cv.shadow([x + 3, y + 20, x + 24, y + 27])
    cv.paste(sprites.rock(), (x, y))


def station_on(cv, x, y):
    cv.shadow([x + 4, y + 24, x + 28, y + 32])
    cv.paste(sprites.station(), (x, y))


def mower_on(cv, x, y, heading="N"):
    cv.shadow([x + 3, y + 22, x + 29, y + 32])
    cv.paste(sprites.mower(heading), (x, y))


def hedgehog_on(cv, x, y, heading="S"):
    cv.shadow([x + 5, y + 22, x + 27, y + 31])
    cv.paste(sprites.hedgehog(heading), (x, y))


def person_on(cv, x, y):
    cv.shadow([x + 9, y + 28, x + 24, y + 33])
    cv.paste(sprites.person(), (x, y))


def tree_on(cv, x, y):
    """Two tiles tall; (x, y) is the top-left of the crown, the trunk stands on the lower tile."""
    cv.shadow([x + 4, y + 42, x + 28, y + 50])
    cv.paste(sprites.tree(), (x, y))


def sprite_sheet():
    """Every sprite in every heading on growing grass, scaled x5, for review."""
    items = [("mower " + h, lambda h=h: sprites.mower(h)) for h in "NESW"]
    items += [("hedgehog " + h, lambda h=h: sprites.hedgehog(h)) for h in "SENW"]
    items += [("station", sprites.station), ("person", sprites.person), ("rock", sprites.rock)]
    cell, cols = 48, 4
    rows = -(-(len(items) + 1) // cols)
    cv = Canvas(cols * cell, rows * cell + 16)
    for i in range((cols * cell) // TILE + 1):
        for j in range((rows * cell + 16) // TILE + 1):
            grass_tile(cv, i * TILE, j * TILE, 1, seed=500 + 7 * i + j)
    for n, (name, make) in enumerate(items):
        x, y = (n % cols) * cell + 8, (n // cols) * cell + 8
        cv.shadow([x + 4, y + 22, x + 28, y + 32])
        cv.paste(make(), (x, y))
    x, y = (len(items) % cols) * cell + 8, (len(items) // cols) * cell + 4
    cv.shadow([x + 4, y + 42, x + 28, y + 50])
    cv.paste(sprites.tree(), (x, y))
    big = cv.img.convert("RGB").resize((cv.img.width * 5, cv.img.height * 5), Image.NEAREST)
    big.save(HERE / "sprites.png")


def fence_h(cv, x, y, post=True):
    """A horizontal fence section: two rails with shading, and a post with a cap."""
    d = cv.d
    wood = C["fence wood"]
    for ry in (11, 21):
        d.rectangle([x, ry + y, x + TILE - 1, ry + y + 3], fill=wood, outline=outline_of(wood))
        d.line([x, ry + y + 1, x + TILE - 1, ry + y + 1], fill=shade(wood, 1.2))
    if post:
        cv.shadow([x + 10, y + 26, x + 22, y + 31])
        d.rectangle([x + 12, y + 4, x + 19, y + 28], fill=wood, outline=outline_of(wood))
        d.line([x + 13, y + 5, x + 13, y + 27], fill=shade(wood, 1.25))
        d.line([x + 18, y + 5, x + 18, y + 27], fill=shade(wood, 0.8))
        d.rectangle([x + 11, y + 3, x + 20, y + 5], fill=shade(wood, 1.1), outline=outline_of(wood))


def fence_v(cv, x, y, post=True):
    d = cv.d
    wood = C["fence wood"]
    for rx in (11, 19):
        d.rectangle([x + rx, y, x + rx + 3, y + TILE - 1], fill=wood, outline=outline_of(wood))
        d.line([x + rx + 1, y, x + rx + 1, y + TILE - 1], fill=shade(wood, 1.2))
    if post:
        cv.shadow([x + 9, y + 24, x + 25, y + 31])
        d.rectangle([x + 12, y + 8, x + 21, y + 26], fill=wood, outline=outline_of(wood))
        d.line([x + 13, y + 9, x + 13, y + 25], fill=shade(wood, 1.25))
        d.rectangle([x + 11, y + 7, x + 22, y + 9], fill=shade(wood, 1.1), outline=outline_of(wood))


def mock_lawn():
    w = h = 6
    border = 2  # one tile of surroundings, one tile of fence
    W, H = (w + 2 * border) * TILE, (h + 2 * border) * TILE
    cv = Canvas(W, H)

    def at(gx, gy):
        """Pixel origin of lawn tile (gx, gy): inside the border, y = 0 at the bottom."""
        return (gx + border) * TILE, (h - 1 - gy + border) * TILE

    # surroundings: growing grass everywhere, then the fence ring on the inner border tile
    for i in range(w + 2 * border):
        for j in range(h + 2 * border):
            grass_tile(cv, i * TILE, j * TILE, 1, seed=1000 + 31 * i + j)
    for i in range(1, w + 3):
        fence_h(cv, i * TILE, 1 * TILE)
        fence_h(cv, i * TILE, (h + 2) * TILE)
    for j in range(2, h + 2):
        fence_v(cv, 1 * TILE, j * TILE)
        fence_v(cv, (w + 2) * TILE, j * TILE)

    heights = [  # tier per (x, y), y = 0 is south
        [0, 0, 0, 1, 2, 3],
        [0, 0, 1, 1, 2, 3],
        [0, 1, 1, 2, 3, 3],
        [1, 1, 2, 2, 3, 3],
        [1, 2, 2, 3, 3, 3],
        [2, 2, 3, 3, 3, 3],
    ]
    for gx in range(w):
        for gy in range(h):
            tier = heights[gx][gy]
            stripe = (1 if gy % 2 == 0 else -1) if tier <= 1 else 0  # alternating east-west passes
            grass_tile(cv, *at(gx, gy), tier, stripe, seed=17 * gx + gy)
    flower_bed_tile(cv, *at(4, 5), seed=3)
    flower_bed_tile(cv, *at(5, 5), seed=4)
    path_tile(cv, *at(0, 1), seed=5)
    path_tile(cv, *at(1, 1), seed=6)
    scalped_tile(cv, *at(3, 3), seed=7)
    stone_on(cv, *at(5, 2))
    station_on(cv, *at(0, 0))
    mower_on(cv, *at(2, 0), "E")
    hedgehog_on(cv, *at(4, 3), "W")
    person_on(cv, *at(1, 4))
    tree_on(cv, 0 * TILE, 0 * TILE)                      # outside the fence, top-left
    tree_on(cv, (w + 3) * TILE, (h + 2) * TILE)          # bottom-right
    stone_on(cv, (w + 3) * TILE, 3 * TILE)

    big = cv.img.convert("RGB").resize((W * SCALE, H * SCALE), Image.NEAREST)
    big.save(HERE / "mock_lawn.png")


if __name__ == "__main__":
    palette_swatch()
    sprite_sheet()
    mock_lawn()
