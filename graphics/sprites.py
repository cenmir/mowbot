"""Mowbot sprites as character grids: one letter per pixel, a legend per sprite.

Every sprite is authored facing one way and rotated to its heading, which is lossless for
true top-down art. Rows shorter than the width are padded with transparent pixels, so trailing
dots are not needed; a row longer than the width is an error that names the row.
"""
from PIL import Image

TILE = 32


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def draw_grid(rows, legend, width=TILE, height=TILE):
    """Render rows of letters to an RGBA image; '.' is transparent.

    The image is always width x height, padded with transparent rows, so that a square sprite
    rotates in place without cropping."""
    if len(rows) > height:
        raise ValueError(f"{len(rows)} rows, max {height}")
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    px = img.load()
    for y, row in enumerate(rows):
        if len(row) > width:
            raise ValueError(f"row {y} is {len(row)} wide, max {width}: {row!r}")
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            if ch not in legend:
                raise ValueError(f"row {y} col {x}: no legend entry for {ch!r}")
            px[x, y] = hex_to_rgb(legend[ch]) + (255,)
    return img


# --- the mower, facing north -------------------------------------------------------------------
# A four-wheel robot mower from above: white hull, treaded wheels, orange front bumper,
# sensor tower at the nose with a blue lens, red stop button at the rear, yellow rear lights.
MOWER_LEGEND = {
    "o": "#3a3a40",  # hull outline
    "w": "#ffffff",  # hull light
    "W": "#f2f2f2",  # hull mid
    "g": "#c8c8cc",  # hull dark
    "K": "#2b2b2b",  # wheel
    "k": "#4a4a4a",  # tread
    "h": "#8a8f94",  # hub
    "O": "#e8632b",  # bumper
    "p": "#f08a50",  # bumper light
    "R": "#d33a3a",  # stop button
    "r": "#f06060",  # stop button light
    "b": "#4a4f55",  # sensor tower
    "B": "#3b6bc9",  # lens
    "Y": "#f3c84b",  # rear light
}
MOWER = [
    "..............oooo",
    "............ooOOOOoo",
    "...........oOOppppOOo",
    "..........oOOOppppOOOo",
    ".........oOOOOOOOOOOOOo",
    "........oYwwwwwwwwwwwwYo",
    ".......owwwwwwbbbbwwwwwgo",
    ".oKKKKoowWWWWWbBBbWWWWWgooKKKKo",
    ".okKKkoowWWWWWbBBbWWWWWgookKKko",
    ".oKKKKoowWWWWWbbbbWWWWWgooKKKKo",
    ".oKhhKoowWWWWWWWWWWWWWWgooKhhKo",
    ".oKhhKoowWWWWWWWWWWWWWWgooKhhKo",
    ".oKKKKoowWWWWWWWWWWWWWWgooKKKKo",
    ".okKKkoowWWWWWWWWWWWWWWgookKKko",
    ".oKKKKoowWWWWWWWWWWWWWWgooKKKKo",
    ".......owWWWWWWWWWWWWWWgo",
    ".......owWggggggggggggWgo",
    ".......owWWWWWWWWWWWWWWgo",
    ".......owWWWWoRrrRoWWWWgo",
    ".......owWWWWoRRRRoWWWWgo",
    ".oKKKKoowWWWWoRRRRoWWWWgooKKKKo",
    ".okKKkoowWWWWooooooWWWWgookKKko",
    ".oKKKKoowWWWWWWWWWWWWWWgooKKKKo",
    ".oKhhKoowWWWWWWWWWWWWWWgooKhhKo",
    ".oKhhKoowWWWWWWWWWWWWWWgooKhhKo",
    ".oKKKKoowWWWWWWWWWWWWWWgooKKKKo",
    ".okKKkoowWWWWWWWWWWWWWWgookKKko",
    ".oKKKKoogggggggggggggggggoKKKKo",
    ".......oYYoooooooooooYYo",
    "........oooooooooooooooo",
]
MOWER_ANGLE = {"N": 0, "W": 90, "S": 180, "E": 270}  # PIL rotates counter-clockwise

# --- the charging station -----------------------------------------------------------------------
# A flat black pad with a raised back (north end), grille mesh on both sides, a blue LED strip
# on the back and a green power symbol in the middle. The mower docks facing north.
STATION_LEGEND = {
    "o": "#15171a",  # outline
    "D": "#2e3136",  # dark
    "d": "#3c4046",  # mid
    "l": "#5a5f66",  # light
    "G": "#22252a",  # grille holes
    "B": "#3b6bc9",  # LED strip
    "Y": "#f3c84b",  # lightning bolt
    "y": "#b8901e",  # bolt shadow edge
}
STATION = [
    "",
    "..........oooooooooooo",
    ".........oddddddddddddo",
    ".........odlllllllllldo",
    ".........odlBBBBBBBBldo",
    ".........oddddddddddddo",
    ".........oDDDDDDDDDDDDo",
    ".........oDDDDDDDDDDDDo",
    ".....oooooDDDDDDDDDDDDooooo",
    ".....ollllllllllllllllllllo",
    ".....oGdGdGdGddddddGdGdGdGo",
    ".....odGdGdGddddddddGdGdGdo",
    ".....oGdGdGdGddddddGdGdGdGo",
    ".....odGdGdGddddddddGdGdGdo",
    ".....oddddddddddddddddddddo",
    ".....oddddddddddYYYyddddddo",
    ".....odddddddddYYYydddddddo",
    ".....oddddddddYYYyddddddddo",
    ".....odddddddYYYYYYYydddddo",
    ".....odddddddddYYYydddddddo",
    ".....odddddddYYYydddddddddo",
    ".....oddddddYYYyddddddddddo",
    ".....odddddYYYydddddddddddo",
    ".....oddddYYydddddddddddddo",
    ".....oddddddddddddddddddddo",
    ".....oGdGdGdGddddddGdGdGdGo",
    ".....odGdGdGddddddddGdGdGdo",
    ".....oGdGdGdGddddddGdGdGdGo",
    ".....odGdGdGddddddddGdGdGdo",
    ".....oDDDDDDDDDDDDDDDDDDDDo",
    ".....oooooooooooooooooooooo",
]

# --- the hedgehog, facing south (face at the bottom) ---------------------------------------------
HEDGEHOG_LEGEND = {
    "o": "#2a1c12",  # outline
    "S": "#4a3222",  # spine dark
    "s": "#6e4c33",  # spine mid
    "t": "#a07a52",  # spine tip
    "e": "#c49a6c",  # ear
    "F": "#d9b48a",  # face
    "f": "#eed6b6",  # face light
    "E": "#1a1410",  # eye
    "w": "#ffffff",  # eye glint
    "N": "#2b1f18",  # nose
}
HEDGEHOG = [
    "",
    "............oooooooo",
    "..........ooSsSssSsSoo",
    ".........oSstsSssStsSSo",
    "........oSsssSssSsssSsSo",
    ".......oSstssSsssStssSsSo",
    "......oSsssssSstsSssssStSo",
    "......oSstsSssSsssSstsSsSo",
    ".....oSssSssstSsssSsssStsSo",
    ".....oSstsSsssSsstSsssSsSSo",
    ".....oSsssSstsSsssSstsSsSso",
    ".....oSstSsssSssSsssSsssSSo",
    ".....oSsssSstsSsssStsSsssSo",
    ".....oSstsSsssSsssSsssSstSo",
    ".....oSsssSssSsssSstsSsssSo",
    ".....oSsSsssSsssSsssSssSsSo",
    ".....oSsssSssSsssSssSsssSSo",
    ".....oSsSsssSsSSsSsssSsSsSo",
    ".....oeSsSssSsSsSsSsssSsSeo",
    ".....oeeSSsSsSsSsSsSsSsSeeo",
    "......oeoFFFFFFFFFFFFFFoeo",
    "......ooFffFFFFFFFFFFffFoo",
    ".......oFFFFEwFFFFwEFFFFo",
    ".......oFFFFEEFFFFEEFFFFo",
    ".......oFFFFFFFFFFFFFFFFo",
    "........oFFFFFffFFFFFFFo",
    ".........oFFFFffFFFFo",
    "..........oFFfNNfFFo",
    "...........ooNNNNoo",
    ".............oooo",
]
HEDGEHOG_ANGLE = {"S": 0, "E": 90, "N": 180, "W": 270}

# --- the person, front view (the lab partner on the arrow keys) ----------------------------------
PERSON_LEGEND = {
    "o": "#2a2020",  # outline
    "H": "#3a2a1e",  # hair
    "h": "#5a4330",  # hair light
    "F": "#f0c9a0",  # skin
    "f": "#f8dcc0",  # skin light
    "E": "#1a1410",  # eye
    "S": "#3b6bc9",  # shirt
    "s": "#5a88e0",  # shirt light
    "d": "#2f55a0",  # shirt dark
    "T": "#3c4046",  # trousers
    "B": "#7a5230",  # shoe
    "b": "#9a6a3e",  # shoe light
}
PERSON = [
    "",
    "",
    "............oooooooo",
    "...........oHHHHHHHHo",
    "..........oHHhhHHHHHHo",
    "..........oHHhHHHHHHHo",
    "..........oHHHHHHHHHHo",
    "..........oHFFFFFFFFHo",
    ".........oHFFFFFFFFFFHo",
    "..........oFFFFFFFFFFo",
    "..........oFFEFFFFEFFo",
    "..........oFFEFFFFEFFo",
    "..........oFFFFFFFFFFo",
    "..........ofFFFFFFFFfo",
    "...........oFFFFFFFFo",
    "............oFFFFFFo",
    "..........ooosSSSSooo",
    ".........oFoSsSSSSSSoFo",
    ".........oFoSsSSSSSSoFo",
    ".........oFoSSSSSSSSoFo",
    ".........oFoSSSSSSSSoFo",
    ".........oFoSSSSSSSSoFo",
    ".........oFodSSSSSSdoFo",
    ".........oFoddddddddoFo",
    "..........ooTTTTTTTToo",
    "...........oTTTToTTTTo",
    "...........oTTTToTTTTo",
    "...........oTTTToTTTTo",
    "...........oTTTToTTTTo",
    "..........oBBBBBoBBBBBo",
    "..........oBbBBBoBbBBBo",
    "..........ooooooooooooo",
]

# --- a boulder, faceted with the light from the top-left -----------------------------------------
ROCK_LEGEND = {
    "o": "#3a3e42",
    "L": "#b0b4b8",
    "M": "#8a8f94",
    "D": "#5c6166",
}
ROCK = [
    "", "", "", "", "", "",
    "..........ooooo",
    "........ooLLLLLoo",
    ".......oLLLLLLLLLo",
    "......oLLLLMMLLLLMo",
    ".....oLLLMMMMMMMMMMo",
    ".....oLMMMMMMMMMMMMo",
    "....oLLMMMMMMMMMMDDMo",
    "....oLMMMMMMMMMMDDDMo",
    "...oLLMMMMMMMoMMDDDDMo",
    "...oLMMMMMMMMoMMDDDDDo",
    "..oLLMMMMMMMMMoMMDDDDDo",
    "..oLMMMMMMMMMMMoMDDDDDo",
    "..oMMMMMMMMMMMMMoDDDDDo",
    "..oMMMMMMMMMMMMMMDDDDDo",
    "..oDMMMMMMMMMMMMDDDDDDo",
    "..oDDMMMMMMMMMMDDDDDDDo",
    "...oDDDMMMMMMMDDDDDDDo",
    "....oDDDDDDDDDDDDDDDo",
    ".....ooooooooooooooo",
]

# --- a tree: one crown with highlight clusters top-left, dark underside, trunk with roots ----------
TREE_LEGEND = {
    "o": "#1e3a1a",  # crown outline
    "L": "#8fd14f",  # leaf light
    "M": "#5fae38",  # leaf mid
    "D": "#3a7a24",  # leaf dark
    "K": "#2c5c1c",  # leaf deepest
    "q": "#3a2414",  # trunk outline
    "t": "#9a6a3e",  # trunk light
    "T": "#7a5230",  # trunk
    "d": "#5a3a22",  # trunk dark
}
TREE = [
    ".............oooooo",
    "..........oooMMMMMMooo",
    "........ooMMLLMMMMMMMMoo",
    ".......oMMLLLLMMMMMMMMMMo",
    "......oMLLLLLLMMMMMMMMMMMo",
    ".....oMLLLLLLLMMMMMMMMMMMMo",
    "....oMMLLLLLLLMMMMMMMMMMMMMo",
    "...oMMMLLLLLLMMMMMMMMMMMMMMMo",
    "...oMMMMLLLLMMMMMLLMMMMMMMMMo",
    "..oMMMMMLLMMMMMMLLLLMMMMMMMMMo",
    "..oMMMMMMMMMMMMMLLLLMMMMMMMMDo",
    "..oMMMMMMMMMMMMMMLLMMMMMMMMDDo",
    ".oMMMMMMMMMMMMMMMMMMMMMMMMMDDDo",
    ".oMMMMMMMMMMMMMMMMMMMMMMMMMDDDo",
    ".oMMMMLLMMMMMMMMMMMMMMMMMMDDDDo",
    ".oMMMLLLLMMMMMMMMMMMMMMMMDDDDDo",
    ".oMMMMLLMMMMMMMMMMMMDMMMMDDDDDo",
    ".oMMMMMMMMMMMMMMMMMDDDMMMDDDDDo",
    ".oDMMMMMMMMMMMMMMMMDDDDMDDDDDDo",
    ".oDDMMMMMMMMMMMMMMMDDDDDDDDDDDo",
    "..oDDMMMMMMMMMMMMMDDDDDDDDDDDo",
    "..oDDDMMMMMMMMMMMDDDDDDDDDDDKo",
    "..oDDDDMMMMMMMMDDDDDDDDDDDDKKo",
    "...oDDDDDMMMMMDDDDDDDDDDDKKKo",
    "...oDDDDDDDDDDDDDDDDDDDDKKKKo",
    "....oDDDDDDDDDDDDDDDDDKKKKKo",
    ".....oDDDDDDDDDDDDDDDKKKKKo",
    "......oDDDDDDDDDDDDDKKKKKo",
    ".......oDDDDDDDDDDDKKKKKo",
    "........ooDDDDDDDDKKKKoo",
    "..........ooDqTTTTqDoo",
    "............qtTTTTdq",
    "............qtTTTTdq",
    "............qtTTTTdq",
    "............qtTTTTdq",
    "............qtTTTTdq",
    "............qtTTTTdq",
    "............qtTTTTdq",
    "............qtTTTTdq",
    "............qtTTTTdq",
    "............qtTTTTdq",
    "............qtTTTTdq",
    "............qtTTTTdq",
    "...........qtTTTTTTdq",
    "..........qttTTTTTTddq",
    ".........qtTTTqTTqTTTdq",
    "........qqqqqq.qq.qqqqqq",
]


def mower(heading="N"):
    return draw_grid(MOWER, MOWER_LEGEND).rotate(MOWER_ANGLE[heading], resample=Image.NEAREST)


def station():
    return draw_grid(STATION, STATION_LEGEND)


def hedgehog(heading="S"):
    return draw_grid(HEDGEHOG, HEDGEHOG_LEGEND).rotate(HEDGEHOG_ANGLE[heading], resample=Image.NEAREST)


def person():
    return draw_grid(PERSON, PERSON_LEGEND)


def rock():
    return draw_grid(ROCK, ROCK_LEGEND)


def tree():
    return draw_grid(TREE, TREE_LEGEND, height=48)
