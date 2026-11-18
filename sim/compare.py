"""Naive sweep against a careful program on each core level, to tune k and the prices.

Two programs that a student could write with the concepts unlocked at that level:

- naive: serpentine over the lawn with the blade always on, recharge when the battery is low.
- careful: the same route, but the blade only on when the tile ahead is ripe (pays in full),
  and (from level 6) home to the station to charge and sharpen instead of the slow manual way.

Both run for a fixed number of ticks; the table shows tokens per 1000 ticks and how many ticks
each needs to earn the next level's price. Run: .venv/bin/python sim/compare.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mowbot import Game, LEVELS, GameOver  # noqa: E402
from mowbot.game import HEADINGS, DELTA  # noqa: E402

RUN_TICKS = 20000


def face(g, heading):
    while g.heading != heading:
        if (HEADINGS.index(heading) - HEADINGS.index(g.heading)) % 4 == 3:
            g.turn_left()
        else:
            g.turn_right()


def go_to(g, tx, ty):
    """Manhattan route, x first then y, with the blade off."""
    g.blade = False
    face(g, "East" if tx > g.x else "West")
    while g.x != tx:
        g.forward()
    face(g, "North" if ty > g.y else "South")
    while g.y != ty:
        g.forward()


def recharge(g, careful):
    if not g.rules.battery:
        return
    if careful and g.rules.station:
        x, y = g.x, g.y
        go_to(g, *g.level.station)
        g.charge()
        if g.rules.blade:
            g.sharpen()
        go_to(g, x, y)
    else:
        g.manual_recharge()
        if g.rules.blade and careful:
            g.manual_sharpen()


def sweep_step(g, careful):
    """One serpentine lap over a rectangular lawn: along x, step in y, back."""
    w, h = g.lawn.width, g.lawn.height
    for y in range(h):
        heading = "East" if y % 2 == 0 else "West"
        face(g, heading)
        for _ in range(w - 1):
            maybe_cut(g, careful)
            if g.rules.battery and g.battery < 25:   # enough to reach the station from anywhere
                recharge(g, careful)
            g.forward()
        if y < h - 1:
            face(g, "North")
            maybe_cut(g, careful)
            g.forward()
    # back to the start corner
    go_to(g, 0, 0)
    face(g, "East")


def maybe_cut(g, careful):
    if not careful:
        g.blade = True
        return
    nx, ny = g.x + DELTA[g.heading][0], g.y + DELTA[g.heading][1]
    if (nx, ny) not in g.lawn:
        g.blade = False
        return
    tile = g.lawn[(nx, ny)]
    g.blade = tile.height >= g.costs.ripe_low     # cut only what pays in full


def run(level, careful, ticks=RUN_TICKS):
    g = Game(level)
    g.unlocked = frozenset(LEVELS[-1].unlocked)   # the program is ours, not the student's
    ticks_to_price = None
    try:
        while g.ticks < ticks:
            sweep_step(g, careful)
            if ticks_to_price is None and level.number + 1 < len(LEVELS) \
                    and g.tokens >= LEVELS[level.number + 1].price:
                ticks_to_price = g.ticks
    except GameOver as e:
        return g, f"stopped: {e}"
    return g, ticks_to_price


def main():
    print(f"{'lvl':>3} {'lawn':>5} {'price':>7} | {'naive /1000':>11} {'ticks':>8} | "
          f"{'careful /1000':>13} {'ticks':>8}")
    for level in LEVELS[:8]:
        row = [f"{level.number:>3}", f"{level.width}x{level.height:<3}",
               f"{LEVELS[level.number + 1].price:>7}" if level.number + 1 < len(LEVELS) else "      -"]
        for careful in (False, True):
            g, t = run(level, careful)
            row.append(f"{g.score():>11.1f}" if not careful else f"{g.score():>13.1f}")
            row.append(f"{t:>8}" if isinstance(t, int) else f"{str(t):>8}")
        print(" ".join(row[:3]) + " | " + " ".join(row[3:5]) + " | " + " ".join(row[5:]))


if __name__ == "__main__":
    main()
