#!/bin/bash
# Render DESIGN.qmd to PDF on Euler and put the PDF in the course folder in Dropbox.
#
# The render runs on Euler (quarto + typst there), never locally, because a quarto render on
# this machine kills the running book preview. The PDF lands in
#   D:\Dropbox\Work\Kurser\CompScience\Mowbot_DESIGN.pdf   on Euler (Dropbox syncs it on)
# and a copy comes back here as DESIGN.pdf for viewing.
set -euo pipefail
cd "$(dirname "$0")"

REMOTE=euler
WORK='C:/Users/mirza/AppData/Local/Temp/mowbot'
DEST='D:\Dropbox\Work\Kurser\CompScience\Mowbot_DESIGN.pdf'

# the figures first, so the swatch script and the doc never disagree
.venv/bin/python graphics/swatch.py

ssh "$REMOTE" 'if not exist "%TEMP%\mowbot\graphics" mkdir "%TEMP%\mowbot\graphics"'
scp -q DESIGN.qmd "$REMOTE:$WORK/DESIGN.qmd"
scp -q graphics/sprites.png graphics/mock_lawn.png graphics/palette.png "$REMOTE:$WORK/graphics/"
ssh "$REMOTE" 'cd /d "%TEMP%\mowbot" && quarto render DESIGN.qmd --to typst --quiet'
ssh "$REMOTE" "copy /y \"%TEMP%\\mowbot\\DESIGN.pdf\" \"$DEST\" >nul && echo copied to $DEST"
scp -q "$REMOTE:$WORK/DESIGN.pdf" DESIGN.pdf
echo "local copy: $(pwd)/DESIGN.pdf"
