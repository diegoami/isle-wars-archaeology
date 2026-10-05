#!/usr/bin/env bash
# One arm of E006 (README "Design"); the command's output goes to measurements/command-output/, never over a file.
#   IW_DOS_DIR, IW_DOS_RUN, E006_BUNDLES: as for runtime/iw-dos/driver/repeat.py
set -u
ROOT=$(cd "${BASH_SOURCE[0]%/*}/../../.." && pwd)
cd "$ROOT" || exit 1
case "${1:-}" in
  control)           args=(--arm control --repeats 10) ;;
  sigkill-mid-cycle) args=(--arm sigkill-mid-cycle --repeats 3 --fault sigkill --fault-at after-before --fault-repeat 2) ;;
  close-mid-cycle)   args=(--arm close-mid-cycle --repeats 3 --fault close --fault-at after-input --fault-repeat 2) ;;
  *) echo "usage: run-arm.sh control|sigkill-mid-cycle|close-mid-cycle" >&2; exit 2 ;;
esac
out="experiments/E006-iw-dos-driver/measurements/command-output/$(date -u +%Y%m%dT%H%M%SZ)-$(git rev-parse --short=12 HEAD)-$1.out.txt"
set -C
{ echo "\$ python3 runtime/iw-dos/driver/repeat.py ${args[*]}"; } > "$out" || exit 1
python3 runtime/iw-dos/driver/repeat.py "${args[@]}" >> "$out" 2>&1
code=$?
echo "exit $code" >> "$out"
cat "$out"
exit $code
