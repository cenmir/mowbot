"""The functions the student calls. They are plain module-level names bound to one Game.

In the browser this module is what `from mowbot.api import *` gives the student's code; the
constants North, East, South, West are strings, so printing a heading shows the word.
"""
from . import game as _game_module

North, East, South, West = "North", "East", "South", "West"

_game: _game_module.Game | None = None


def bind(game):
    """Point every function at this run."""
    global _game
    _game = game


def _g():
    if _game is None:
        raise RuntimeError("No game is running.")
    return _game


def forward():            return _g().forward()
def backward():           return _g().backward()
def turn_left():          return _g().turn_left()
def turn_right():         return _g().turn_right()
def blade_on():           return _g().blade_on()
def blade_off():          return _g().blade_off()
def set_cut_height(mm):   return _g().set_cut_height(mm)
def manual_recharge():    return _g().manual_recharge()
def manual_sharpen():     return _g().manual_sharpen()
def charge():             return _g().charge()
def sharpen():            return _g().sharpen()
def get_x():              return _g().get_x()
def get_y():              return _g().get_y()
def get_heading():        return _g().get_heading()
def get_lawn_size():      return _g().get_lawn_size()
def grass_height(direction=None): return _g().grass_height(direction)
def get_battery():        return _g().get_battery()
def get_blade():          return _g().get_blade()
def get_station():        return _g().get_station()
def get_ground(direction=None):   return _g().get_ground(direction)
def is_clear(direction=None):     return _g().is_clear(direction)
def scan():               return _g().scan()
def get_growth(x, y):     return _g().get_growth(x, y)


__all__ = [
    "North", "East", "South", "West",
    "forward", "backward", "turn_left", "turn_right", "blade_on", "blade_off",
    "set_cut_height", "manual_recharge", "manual_sharpen", "charge", "sharpen",
    "get_x", "get_y", "get_heading", "get_lawn_size", "grass_height", "get_battery",
    "get_blade", "get_station", "get_ground", "is_clear", "scan", "get_growth",
]
