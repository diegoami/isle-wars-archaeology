#!/usr/bin/env bash
# One E007 cycle run. Usage: cyc.sh ARM STEPS-FILE [--explore | other cycle.py args]
# The machine-local locations come from the environment (never from this file):
#   IW_DOS_DIR  IW_DOS_RUN  E007_BUNDLES  and, for --explore, E007_EXPLORE
set -eu
ROOT=$(cd "${BASH_SOURCE[0]%/*}/../../.." && pwd)
: "${IW_DOS_DIR:?}" "${IW_DOS_RUN:?}" "${E007_BUNDLES:?}"
exec python3 "$ROOT/runtime/iw-dos/spike/cycle.py" --experiment E007 --arm "$1" --steps "$2" "${@:3}"
