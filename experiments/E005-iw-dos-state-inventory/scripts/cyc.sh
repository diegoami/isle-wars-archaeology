#!/usr/bin/env bash
# One E005 cycle run. Usage: cyc.sh ARM STEPS-FILE [--explore | other cycle.py args]
# The machine-local locations come from the environment (never from this file):
#   IW_DOS_DIR  IW_DOS_RUN  E005_BUNDLES  and, for --explore, E005_EXPLORE
set -eu
ROOT=$(cd "${BASH_SOURCE[0]%/*}/../../.." && pwd)
: "${IW_DOS_DIR:?}" "${IW_DOS_RUN:?}" "${E005_BUNDLES:?}"
exec python3 "$ROOT/runtime/iw-dos/spike/cycle.py" --experiment E005 --arm "$1" --steps "$2" "${@:3}"
