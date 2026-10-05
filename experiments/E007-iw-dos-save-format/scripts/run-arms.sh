#!/usr/bin/env bash
# Run the named arms one after another (steps/<arm>.steps), each as one recorded cycle run. Usage: run-arms.sh ARM [ARM ...]
# The cycle refuses to start while any other run's DOSBox-X process (another task's, on this machine) is alive
# ("stale processes of an earlier run are alive", issue #32): this waits 20 s and tries again, up to 40 times, and
# touches no process but its own. A run that aborts keeps its record (never deleted); the arm is then not retried.
# Needs IW_DOS_DIR, IW_DOS_RUN, E007_BUNDLES in the environment.
# Paths are given to the cycle relative to the repository root: the record keeps the cycle's arguments, and a
# machine-local path never goes into a record (E007-r0001 to r0005 were made with an absolute path:
# runs/E007/CORRECTIONS.md).
set -u
ROOT=$(cd "${BASH_SOURCE[0]%/*}/../../.." && pwd)
cd "$ROOT" || exit 1
EXP=experiments/E007-iw-dos-save-format
for arm in "$@"; do
  for try in $(seq 1 40); do
    out=$("$EXP/scripts/cyc.sh" "$arm" "$EXP/steps/$arm.steps" 2>&1); code=$?
    if printf '%s' "$out" | grep -q "stale processes of an earlier run are alive"; then sleep 20; continue; fi
    break
  done
  echo "$arm: exit $code: $(printf '%s' "$out" | tail -1)"
done
