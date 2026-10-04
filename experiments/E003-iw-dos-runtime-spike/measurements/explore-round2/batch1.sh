#!/bin/bash
# Round-2 batch 1: determinism (host clock, then a fixed clock), speed, debugger, secure mode.
# Usage: batch1.sh <IW_DOS_DIR> <OUTROOT>
H=$(cd "$(dirname "$0")" && pwd)
D=$1 O=$2
p() { bash "$H/probe.sh" "$@" IW_DOS_DIR="$D" OUTROOT="$O"; }
for i in 1 2 3; do p det-host-$i STEPS="$H/s_det.sh" SAVE=1; done
for i in 1 2 3; do p det-fixed-$i STEPS="$H/s_det.sh" SAVE=1 SYNC=false "PRE=date 01-01-1994
time 12:00:00"; done
for c in "fixed 10000" "fixed 30000" "max"; do p "speed-${c// /-}" STEPS="$H/s_det.sh" "CYCLES=$c"; done
p dbg-breakstart STEPS="$H/s_det.sh" ARGS=-break-start TMO=60
p dbg-debugbox STEPS="$H/s_det.sh" PRE=DEBUGBOX TMO=60
p secure STEPS="$H/s_det.sh" "PRE=config -securemode
mount d /tmp
echo after-mount" TMO=60
for t in "$O"/*/shots.txt; do echo "== $t"; cat "$t"; done
