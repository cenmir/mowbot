"""The level ladder: which rules are on, what is unlocked, what the next step costs.

Each level adds one rule and one concept (DESIGN.qmd section 7). Unlocks are cumulative:
a level's `unlocked` holds every function unlocked so far, `syntax` every language feature.
"""
from dataclasses import dataclass, field

from .lawn import Lawn, K_DEFAULT


@dataclass(frozen=True)
class Rules:
    battery: bool = False      # level 4
    blade: bool = False        # level 5
    station: bool = False      # level 6
    growth_map: bool = False   # level 7
    ground: bool = False       # level 9
    tall_grass: bool = False   # level 11
    obstacles: bool = False    # level 12
    stripes: bool = False      # level 13


@dataclass
class Level:
    number: int
    name: str
    width: int
    height: int
    rules: Rules
    functions: tuple = ()          # functions this level adds
    syntax: tuple = ()             # language features this level adds
    price: int = 0                 # tokens to unlock this level
    start_height: float = 45.0     # ripe: the first lap pays in full
    start: tuple = (0, 0)
    start_heading: str = "North"
    station: tuple | None = None
    rows: tuple | None = None      # map, north row first; None = all grass
    growth: dict = field(default_factory=dict)   # (x, y) -> k, overrides the default
    obstacles: tuple = ()          # (kind, x, y)
    unlocked: frozenset = frozenset()
    allowed_syntax: frozenset = frozenset()

    def make_lawn(self):
        return Lawn(self.width, self.height, self.start_height, K_DEFAULT,
                    rows=self.rows, growth=self.growth)


def _sun_and_shade(width, height):
    """Sunny south-east corner grows fast, shaded north-west slowly."""
    k = {}
    for x in range(width):
        for y in range(height):
            sunny = (x + (height - 1 - y)) / (width + height - 2)   # 0 at NW, 1 at SE
            k[(x, y)] = K_DEFAULT * (0.5 + 1.5 * sunny)
    return k


_R = Rules
LEVELS = [
    Level(0, "Sequence", 3, 3, _R(),
          functions=("forward", "backward", "turn_left", "turn_right")),
    Level(1, "Repetition", 3, 3, _R(), syntax=("for",), price=200),
    Level(2, "State", 5, 5, _R(),
          functions=("get_x", "get_y", "get_heading", "get_lawn_size"), syntax=("while",),
          price=400),
    Level(3, "Decisions", 5, 5, _R(),
          functions=("grass_height", "blade_on", "blade_off"), syntax=("if",), price=800),
    Level(4, "Battery", 5, 5, _R(battery=True),
          functions=("get_battery", "manual_recharge"), price=1200),
    Level(5, "Blade", 5, 5, _R(battery=True, blade=True),
          functions=("get_blade", "manual_sharpen"), price=1500),
    Level(6, "Functions", 6, 6, _R(battery=True, blade=True, station=True),
          functions=("get_station", "charge", "sharpen"), syntax=("def",), price=1800,
          station=(0, 0)),
    Level(7, "Lists", 6, 6, _R(battery=True, blade=True, station=True, growth_map=True),
          functions=("scan", "get_growth"), syntax=("list",), price=2500,
          station=(0, 0), growth=_sun_and_shade(6, 6)),
    Level(8, "Modules", 6, 6, _R(battery=True, blade=True, station=True, growth_map=True),
          syntax=("import",), price=3000, station=(0, 0), growth=_sun_and_shade(6, 6)),
    Level(9, "Flower beds", 6, 6,
          _R(battery=True, blade=True, station=True, growth_map=True, ground=True),
          functions=("get_ground",), syntax=("bool",), price=6000, station=(0, 0),
          growth=_sun_and_shade(6, 6),
          rows=("....FF",
                "....FF",
                "......",
                "......",
                "PP....",
                "......")),
    Level(10, "Lawn shapes", 8, 8,
          _R(battery=True, blade=True, station=True, growth_map=True, ground=True),
          functions=("is_clear",), price=8000, station=(0, 0), growth=_sun_and_shade(8, 8),
          rows=("....####",
                "....####",
                "....####",
                "........",
                "...##...",
                "...##...",
                "........",
                "........")),
    Level(11, "Cutting height", 8, 8,
          _R(battery=True, blade=True, station=True, growth_map=True, ground=True, tall_grass=True),
          functions=("set_cut_height",), price=12000, station=(0, 0), growth=_sun_and_shade(8, 8),
          start_height=80.0),
    Level(12, "Moving obstacles", 8, 8,
          _R(battery=True, blade=True, station=True, growth_map=True, ground=True,
             tall_grass=True, obstacles=True),
          price=16000, station=(0, 0), growth=_sun_and_shade(8, 8),
          obstacles=(("hedgehog", 6, 6), ("person", 3, 7))),
    Level(13, "Contracts", 8, 8,
          _R(battery=True, blade=True, station=True, growth_map=True, ground=True,
             tall_grass=True, obstacles=True, stripes=True),
          syntax=("dict",), price=20000, station=(0, 0), growth=_sun_and_shade(8, 8),
          obstacles=(("hedgehog", 6, 6), ("person", 3, 7))),
]

# make the unlocks cumulative
_functions, _syntax = set(), set()
for _lvl in LEVELS:
    _functions |= set(_lvl.functions)
    _syntax |= set(_lvl.syntax)
    _lvl.unlocked = frozenset(_functions)
    _lvl.allowed_syntax = frozenset(_syntax)


class Progress:
    """What the student has earned and unlocked across runs."""

    def __init__(self, tokens=0.0, level=0):
        self.tokens = tokens
        self.level = level

    @property
    def current(self):
        return LEVELS[self.level]

    @property
    def next_price(self):
        return LEVELS[self.level + 1].price if self.level + 1 < len(LEVELS) else None

    def bank(self, game):
        """Add a finished run's tokens to the account."""
        self.tokens += game.tokens

    def can_unlock(self):
        return self.next_price is not None and self.tokens >= self.next_price

    def unlock(self):
        if not self.can_unlock():
            return False
        self.tokens -= self.next_price
        self.level += 1
        return True
