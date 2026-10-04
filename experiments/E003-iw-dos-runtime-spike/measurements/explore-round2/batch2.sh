#!/bin/bash
# Round-2 batch 2: SIGTERM and SIGKILL as ways to stop; DOSBox-X's own screenshot, twice.
# Usage: batch2.sh <IW_DOS_DIR> <OUTROOT>
H=$(cd "$(dirname "$0")" && pwd)
D=$1 O=$2
p() { bash "$H/probe.sh" "$@" IW_DOS_DIR="$D" OUTROOT="$O"; }
p term-sigterm STEPS="$H/s_full.sh" TERMS=term
p term-sigkill STEPS="$H/s_full.sh" TERMS=kill
p cap-1 STEPS="$H/s_full.sh" CAP=1 TERMS=windowkill
p cap-2 STEPS="$H/s_full.sh" CAP=1 TERMS=windowkill
for t in term-sigterm term-sigkill cap-1 cap-2; do echo "== $t"; cat "$O/$t/shots.txt"; ls "$O/$t/cap"; done
for f in "$O"/cap-*/cap/*.png "$O"/a1/cap/*.png; do echo "$f file $(sha256sum < "$f" | cut -c1-16) pixels $(convert "$f" -depth 8 rgb:- | sha256sum | cut -c1-16) $(identify "$f" | cut -d' ' -f3-5)"; done
