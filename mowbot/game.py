"""One run of the game: the mower on a lawn, the clock, the battery, the blade and the tokens.

Every action spends ticks; while ticks pass the grass grows and the obstacles move. The rules a
level has switched on (see levels.py) decide which costs apply.
"""
import random
from dataclasses import dataclass

from .lawn import Lawn, GRASS, FLOWERBED, STONE, H_MAX

HEADINGS = ["North", "East", "South", "West"]
DELTA = {"North": (0, 1), "East": (1, 0), "South": (0, -1), "West": (-1, 0)}


class GameOver(Exception):
    """The run stops; the message is shown to the student."""


class OutOfBattery(GameOver):
    pass


class Collision(GameOver):
    pass


class NotAtStation(GameOver):
    pass


class NotUnlocked(GameOver):
    pass


@dataclass
class Costs:
    forward: int = 10          # ticks
    backward: int = 20
    turn: int = 5
    cut: int = 10              # added to a move while the blade is on, cut or not
    manual_recharge: int = 500
    manual_sharpen: int = 500
    station: int = 50          # charge or sharpen on the station
    battery_move: float = 1.0  # % per move or turn
    battery_cut: float = 1.0   # % extra when the blade is on
    dull_per_mm: float = 0.05  # % sharpness lost per mm cut: an eighth of the blade per 5x5 lap
    min_sharpness: float = 10.0
    flowerbed_penalty: float = 200.0
    pass_mm: float = 10.0      # at most this much per pass
    ripe_low: float = 40.0     # mm: grass cut inside [ripe_low, ripe_high] pays in full
    ripe_high: float = 70.0
    unripe_factor: float = 0.5  # too short is mulch, too tall tears: half pay
    tall_mm: float = 70.0      # above this, tall grass cuts worse (level 11)
    tall_pass_mm: float = 5.0
    cut_height_min: float = 20.0
    cut_height_max: float = 60.0


@dataclass
class Obstacle:
    kind: str                  # "hedgehog" or "person"
    x: int
    y: int
    every: int = 30            # a hedgehog ambles one tile every so many ticks
    due: int = 30


class Game:
    def __init__(self, level, easy=False, seed=0, costs=None):
        self.level = level
        self.rules = level.rules
        self.costs = costs or Costs()
        self.easy = easy
        self.rng = random.Random(seed)
        self.lawn: Lawn = level.make_lawn()
        self.x, self.y = level.start
        self.heading = level.start_heading
        self.blade = True
        self.battery = 100.0
        self.sharpness = 100.0
        self.cut_height = self.costs.cut_height_min
        self.ticks = 0
        self.tokens = 0.0
        self.unlocked = level.unlocked
        self.obstacles = [Obstacle(kind, x, y) for kind, x, y in level.obstacles]

    # --- the clock -----------------------------------------------------------------------------

    def _spend(self, ticks):
        self.ticks += ticks
        self.lawn.grow(ticks)
        self._move_obstacles(ticks)

    def _drain(self, pct):
        if not self.rules.battery or self.easy:
            return
        self.battery = max(0.0, self.battery - pct)
        if self.battery <= 0:
            raise OutOfBattery("The battery is empty. The mower stops where it is.")

    def _require(self, name):
        if name not in self.unlocked:
            raise NotUnlocked(f"{name}() is not unlocked yet.")

    # --- driving -------------------------------------------------------------------------------

    def forward(self):
        return self._drive(+1, self.costs.forward)

    def backward(self):
        return self._drive(-1, self.costs.backward)

    def _drive(self, sign, ticks):
        dx, dy = DELTA[self.heading]
        nx, ny = self.x + sign * dx, self.y + sign * dy
        if (nx, ny) not in self.lawn or self.lawn[(nx, ny)].ground == STONE:
            return False
        for ob in self.obstacles:
            if (ob.x, ob.y) == (nx, ny):
                raise Collision(f"The mower hit the {ob.kind}. The run stops.")
        self.x, self.y = nx, ny
        self._drain(self.costs.battery_move)
        if self.blade:
            # the blade runs whether or not there is grass to cut, and a dull blade runs longer
            factor = self.sharpness / 100 if self.rules.blade else 1.0
            ticks += round(self.costs.cut / factor)
        # the move takes its time first, so the grass grows, then the cut lands on the tile
        self._spend(ticks)
        if self.blade:
            self._cut(self.lawn[(nx, ny)])
        return True

    def turn_left(self):
        self.heading = HEADINGS[(HEADINGS.index(self.heading) - 1) % 4]
        self._drain(self.costs.battery_move)
        self._spend(self.costs.turn)

    def turn_right(self):
        self.heading = HEADINGS[(HEADINGS.index(self.heading) + 1) % 4]
        self._drain(self.costs.battery_move)
        self._spend(self.costs.turn)

    # --- cutting -------------------------------------------------------------------------------

    def _cut(self, tile):
        """Cut the tile just driven into: at most one pass, never below the cutting height.

        A tile that is already short costs the full cutting time for nothing: that is what
        makes checking the height before driving pay."""
        factor = self.sharpness / 100 if self.rules.blade else 1.0
        self._drain(self.costs.battery_cut)
        if tile.ground == FLOWERBED and self.rules.ground:
            self.tokens -= self.costs.flowerbed_penalty
            return
        if tile.ground != GRASS:
            return
        per_pass = self.costs.pass_mm
        if self.rules.tall_grass and tile.height > self.costs.tall_mm:
            per_pass = self.costs.tall_pass_mm
        # timing pays: a tile cut while ripe gives a full token per mm, otherwise half
        ripe = self.costs.ripe_low <= tile.height <= self.costs.ripe_high
        removed = max(0.0, min(per_pass, tile.height - self.cut_height))
        tile.height -= removed
        tile.stripe = self.heading
        self.tokens += removed * factor * (1.0 if ripe else self.costs.unripe_factor)
        if self.rules.blade and not self.easy:
            self.sharpness = max(self.costs.min_sharpness,
                                 self.sharpness - self.costs.dull_per_mm * removed)

    def blade_on(self):
        self._require("blade_on")
        self.blade = True

    def blade_off(self):
        self._require("blade_off")
        self.blade = False

    def set_cut_height(self, mm):
        self._require("set_cut_height")
        self.cut_height = min(self.costs.cut_height_max, max(self.costs.cut_height_min, float(mm)))

    # --- battery and blade care ----------------------------------------------------------------

    def manual_recharge(self):
        self._require("manual_recharge")
        self._spend(self.costs.manual_recharge)
        self.battery = 100.0

    def manual_sharpen(self):
        self._require("manual_sharpen")
        self._spend(self.costs.manual_sharpen)
        self.sharpness = 100.0

    def _at_station(self, what):
        if (self.x, self.y) != self.level.station:
            raise NotAtStation(f"{what}() only works on the charging station at {self.level.station}.")

    def charge(self):
        self._require("charge")
        self._at_station("charge")
        self._spend(self.costs.station)
        self.battery = 100.0

    def sharpen(self):
        self._require("sharpen")
        self._at_station("sharpen")
        self._spend(self.costs.station)
        self.sharpness = 100.0

    # --- looking around ------------------------------------------------------------------------

    def _ahead(self, direction=None):
        dx, dy = DELTA[direction or self.heading]
        return self.x + dx, self.y + dy

    def get_x(self):
        self._require("get_x")
        return self.x

    def get_y(self):
        self._require("get_y")
        return self.y

    def get_heading(self):
        self._require("get_heading")
        return self.heading

    def get_lawn_size(self):
        self._require("get_lawn_size")
        return self.lawn.width, self.lawn.height

    def grass_height(self, direction=None):
        """Height in mm of the tile ahead (or in `direction`); 0 where there is no grass."""
        self._require("grass_height")
        xy = self._ahead(direction)
        return self.lawn[xy].height if xy in self.lawn else 0.0

    def get_battery(self):
        self._require("get_battery")
        return self.battery

    def get_blade(self):
        self._require("get_blade")
        return self.sharpness

    def get_station(self):
        self._require("get_station")
        return self.level.station

    def get_ground(self, direction=None):
        self._require("get_ground")
        xy = self._ahead(direction)
        return self.lawn[xy].ground if xy in self.lawn else "Wall"

    def is_clear(self, direction=None):
        """True when the mower can drive one tile that way: lawn, no stone, nobody there."""
        self._require("is_clear")
        xy = self._ahead(direction)
        if xy not in self.lawn or self.lawn[xy].ground == STONE:
            return False
        return all((ob.x, ob.y) != xy for ob in self.obstacles)

    def scan(self):
        self._require("scan")
        return self.lawn.heights()

    def get_growth(self, x, y):
        self._require("get_growth")
        return self.lawn[(x, y)].k if (x, y) in self.lawn else 0.0

    # --- obstacles -----------------------------------------------------------------------------

    def _move_obstacles(self, ticks):
        for ob in self.obstacles:
            if ob.kind != "hedgehog":
                continue
            ob.due -= ticks
            while ob.due <= 0:
                ob.due += ob.every
                dx, dy = DELTA[self.rng.choice(HEADINGS)]
                nx, ny = ob.x + dx, ob.y + dy
                if (nx, ny) in self.lawn and (nx, ny) != (self.x, self.y):
                    ob.x, ob.y = nx, ny

    def move_person(self, direction):
        """The lab partner on the arrow keys. Walking into the mower is a hit as well."""
        for ob in self.obstacles:
            if ob.kind == "person":
                dx, dy = DELTA[direction]
                nx, ny = ob.x + dx, ob.y + dy
                if (nx, ny) not in self.lawn:
                    return
                if (nx, ny) == (self.x, self.y):
                    raise Collision("The person walked into the mower. The run stops.")
                ob.x, ob.y = nx, ny

    # --- the score -----------------------------------------------------------------------------

    def score(self):
        """Tokens per 1000 ticks; the number students compare."""
        return 1000 * self.tokens / self.ticks if self.ticks else 0.0
