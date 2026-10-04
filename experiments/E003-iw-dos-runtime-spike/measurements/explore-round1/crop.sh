#!/bin/bash
# crop.sh TAG X Y NAME...: crop the 640x350 window out of each shot into the scratchpad
EX=<EXPLORE>
SP=<SCRATCHPAD>
TAG=$1 X=$2 Y=$3; shift 3
for n in "$@"; do convert "$EX/out/$TAG/$n.png" -crop 640x350+$X+$Y +repage "$SP/${TAG}_$n.png"; done
