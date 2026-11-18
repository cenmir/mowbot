# Mowbot

A browser game for learning Python: you program a robotic lawnmower, starting on a 3×3 lawn,
and unlock the language one concept at a time, from calling functions to lists and dicts. Real
CPython runs in the browser; the code you write is the code you will write in Jupyter afterwards.

Built for the course *Vetenskaplig programmering* (TTPG15) at Jönköping University, where it
replaces a commercial game from 2027. It will be served at python.ju.se as part of the Python book.

## Status

Design phase. The game mechanics, economy, level ladder, course placement and art are settled in
[DESIGN.qmd](DESIGN.qmd) (rendered to PDF by `render_design.sh`). Nothing runs yet; the build
order is the rules engine in Python, then the browser spike, then the levels and the book chapters.

## Layout

| Path | What |
|---|---|
| `DESIGN.qmd` | the design document, with a decision log at the end |
| `render_design.sh` | renders the design to PDF with quarto on a remote machine and copies it to the course folder |
| `graphics/sprites.py` | every sprite as a hand-authored pixel grid, one letter per pixel |
| `graphics/swatch.py` | draws the palette, a sprite sheet and a mock lawn from the grids |
| `graphics/*.png` | the current renders of those |

## Running the graphics

```
uv venv .venv
uv pip install --python .venv/bin/python pillow pytest
.venv/bin/python graphics/swatch.py
```

![The mock lawn](graphics/mock_lawn.png)
