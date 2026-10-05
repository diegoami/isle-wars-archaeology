#!/usr/bin/env bash
# One recorded run that loads a crafted save. Usage: run-crafted.sh VARIANT [STEPS]
#   VARIANT  the name of crafted/<VARIANT>.position.json (the position the writer encodes: savefmt.py); the run's arm
#            is load-<VARIANT>
#   STEPS    the step script's name in steps/ (default load-crafted)
# The position is placed in the run copy by the script's put-save, after the launch checks (I3). Paths are relative to
# the repository root, like run-arms.sh (a machine-local path never goes into a record). Waits for any other task's
# DOSBox-X run to end, like run-arms.sh. Needs IW_DOS_DIR, IW_DOS_RUN, E007_BUNDLES in the environment.
set -u
ROOT=$(cd "${BASH_SOURCE[0]%/*}/../../.." && pwd)
cd "$ROOT" || exit 1
EXP=experiments/E007-iw-dos-save-format
variant=$1
steps=${2:-load-crafted}
[ -f "$EXP/crafted/$variant.position.json" ] || { echo "no $EXP/crafted/$variant.position.json" >&2; exit 1; }
for try in $(seq 1 40); do
  out=$("$EXP/scripts/cyc.sh" "load-$variant" "$EXP/steps/$steps.steps" --crafted "$EXP/crafted/$variant.position.json" 2>&1); code=$?
  if printf '%s' "$out" | grep -q "stale processes of an earlier run are alive"; then sleep 20; continue; fi
  break
done
echo "load-$variant: exit $code: $(printf '%s' "$out" | tail -1)"
