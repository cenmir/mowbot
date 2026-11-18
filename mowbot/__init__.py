"""Mowbot rules engine: the lawn, the mower and the rules of the game, in plain Python.

The same code runs under Pyodide in the browser and under pytest here. Nothing in it knows
about screens or editors; it only keeps state and enforces the rules in DESIGN.qmd.
"""
from .lawn import Lawn, Tile, H_MAX, GRASS, FLOWERBED, PATH, STONE
from .game import Game, Costs, GameOver, OutOfBattery, Collision, NotAtStation, NotUnlocked
from .levels import Level, Rules, LEVELS, Progress
from .gate import check_syntax

__all__ = [
    "Lawn", "Tile", "H_MAX", "GRASS", "FLOWERBED", "PATH", "STONE",
    "Game", "Costs", "GameOver", "OutOfBattery", "Collision", "NotAtStation", "NotUnlocked",
    "Level", "Rules", "LEVELS", "Progress", "check_syntax",
]
