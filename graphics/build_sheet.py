"""Build the sprite sheet the browser draws from: web/assets/sheet.png and sheet.json.

Every tile variant and every sprite is painted once here, with the same painters as the mock
lawn, so the game looks exactly like the mock. The JSON maps a name to [x, y, w, h] in the
sheet. Run after any change to swatch.py or sprites.py:

    .venv/bin/python graphics/build_sheet.py
"""
import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import swatch  # noqa: E402
import sprites  # noqa: E402

TILE = 32
CELL_W, CELL_H, COLS = 32, 48, 16        # every cell is tall enough for the tree
STRIPE = {"m": -1, "0": 0, "p": 1}


def entries():
    """(name, width, height, painter(cv, x, y)) for everything in the sheet."""
    out = []
    for tier in range(4):
        for code, stripe in STRIPE.items():
            for v in range(4):
                out.append((f"grass_{tier}_{code}_{v}", TILE, TILE,
                            lambda cv, x, y, t=tier, s=stripe, v=v:
                            swatch.grass_tile(cv, x, y, t, s, seed=100 * t + 10 * v + s + 1)))
    for v in range(2):
        out.append((f"path_{v}", TILE, TILE, lambda cv, x, y, v=v: swatch.path_tile(cv, x, y, seed=v)))
        out.append((f"flower_{v}", TILE, TILE, lambda cv, x, y, v=v: swatch.flower_bed_tile(cv, x, y, seed=v)))
        out.append((f"scalped_{v}", TILE, TILE, lambda cv, x, y, v=v: swatch.scalped_tile(cv, x, y, seed=v)))
    out.append(("fence_h", TILE, TILE, lambda cv, x, y: swatch.fence_h(cv, x, y)))
    out.append(("fence_v", TILE, TILE, lambda cv, x, y: swatch.fence_v(cv, x, y)))
    for h in "NESW":
        out.append((f"mower_{h}", TILE, TILE, lambda cv, x, y, h=h: swatch.mower_on(cv, x, y, h)))
        out.append((f"hedgehog_{h}", TILE, TILE, lambda cv, x, y, h=h: swatch.hedgehog_on(cv, x, y, h)))
    out.append(("station", TILE, TILE, swatch.station_on))
    out.append(("person", TILE, TILE, swatch.person_on))
    out.append(("rock", TILE, TILE, swatch.stone_on))
    out.append(("tree", TILE, 48, swatch.tree_on))
    return out


def main():
    items = entries()
    rows = -(-len(items) // COLS)
    cv = swatch.Canvas(COLS * CELL_W, rows * CELL_H, bg=(0, 0, 0, 0))
    index = {}
    for n, (name, w, h, paint) in enumerate(items):
        x, y = (n % COLS) * CELL_W, (n // COLS) * CELL_H
        paint(cv, x, y)
        index[name] = [x, y, w, h]
    out = HERE.parent / "web" / "assets"
    out.mkdir(parents=True, exist_ok=True)
    cv.img.save(out / "sheet.png")
    (out / "sheet.json").write_text(json.dumps(index, indent=0))
    return len(items)


if __name__ == "__main__":
    n = main()
    Image.open(HERE.parent / "web" / "assets" / "sheet.png")   # a sanity check that it reads back
    sys.stdout.write(f"{n} cells in web/assets/sheet.png\n")
