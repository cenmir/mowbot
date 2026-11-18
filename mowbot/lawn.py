"""The lawn: a grid of tiles with grass height in mm that grows every tick.

Coordinates are (x, y) in the first quadrant: (0, 0) is the south-west corner, East increases
x, North increases y. A tile is 1 m x 1 m. Tiles that are not part of the lawn (a house, the
world outside an L shape) simply do not exist in the grid; driving into them is driving into a
wall.
"""
import os
from dataclasses import dataclass

H_MAX = 100.0          # mm: grass stops growing here
# Growth rate per tick, tuned with sim/compare.py. At the 20 mm cutting height this is about
# 0.013 mm per tick, so a cut tile takes some 1500 ticks (three laps of a 5x5 lawn) to ripen
# again. Faster and the lawn is always ripe, so a blind sweep is the best program and timing
# teaches nothing; slower and the early levels starve. The environment variable exists for the
# tuning simulation only.
K_DEFAULT = float(os.environ.get("MOWBOT_K", 1 / 6000))

GRASS, FLOWERBED, PATH, STONE = "Grass", "Flowerbed", "Path", "Stone"

# One letter per tile in a level map. Rows are written north first, as on the screen.
MAP_LETTERS = {".": GRASS, "F": FLOWERBED, "P": PATH, "S": STONE}
WALL = "#"


@dataclass
class Tile:
    height: float          # mm of grass; 0 on anything that is not grass
    k: float               # growth rate per tick
    ground: str = GRASS
    stripe: str | None = None   # heading of the last cut, for the stripes


class Lawn:
    def __init__(self, width, height, start_height=30.0, k=K_DEFAULT, rows=None, growth=None):
        """A width x height lawn. `rows` is an optional map (north row first) of the letters
        in MAP_LETTERS, '#' for no tile; `growth` an optional dict (x, y) -> k."""
        self.width, self.height = width, height
        self.tiles: dict[tuple[int, int], Tile] = {}
        for x in range(width):
            for y in range(height):
                letter = rows[height - 1 - y][x] if rows else "."
                if letter == WALL:
                    continue
                ground = MAP_LETTERS[letter]
                tile_k = (growth or {}).get((x, y), k)
                self.tiles[(x, y)] = Tile(start_height if ground == GRASS else 0.0, tile_k, ground)

    def __contains__(self, xy):
        return xy in self.tiles

    def __getitem__(self, xy):
        return self.tiles[xy]

    def grow(self, ticks):
        """Explicit Euler on dh/dt = k (H_MAX - h), one step per tick, dt = 1.

        This is the line the students rewrite as `predict` at level 7, so it stays a loop."""
        for tile in self.tiles.values():
            if tile.ground != GRASS:
                continue
            h = tile.height
            for _ in range(ticks):
                h = h + tile.k * (H_MAX - h)
            tile.height = h

    def heights(self):
        """heights[x][y] in mm, 0 where there is no grass, as `scan()` returns it."""
        return [[self.tiles[(x, y)].height if (x, y) in self.tiles else 0.0
                 for y in range(self.height)] for x in range(self.width)]
