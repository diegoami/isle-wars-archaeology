#!/bin/bash
# Done-when lines 4, 2 and 5 of T11, run from the worktree with the machine-local locations set.
cd <WORKTREE> || exit 1
export IW_DOS_DIR=<MACHINE-LOCAL>/install
export IW_DOS_RUN=<MACHINE-LOCAL>/run
export E003_BUNDLES=<MACHINE-LOCAL>/bundles-E003
M=experiments/E003-iw-dos-runtime-spike/measurements/done-when; mkdir -p "$M"
OUT="$M/$1-$(date -u +%Y%m%dT%H%M%SZ).txt"
exec > >(tee "$OUT") 2>&1
echo "+ dw.sh $* (at $(git rev-parse --short=12 HEAD), $(date -u +%FT%TZ))"
case "$1" in
  profile) setup/iw-dos/iw-dos-runtime.sh; echo "exit $?"; setup/iw-dos/iw-dos-runtime.sh; echo "exit $?";;
  control) for i in 1 2 3; do python3 runtime/iw-dos/spike/cycle.py || exit 1; done; echo "loop exit 0";;
  arm) shift; python3 runtime/iw-dos/spike/cycle.py "$@"; echo "exit $?";;
  check) python3 tools/register_artifact.py check "$IW_DOS_DIR" iw-dos-3.1-30121376 --strict; echo "exit $?";;
esac
