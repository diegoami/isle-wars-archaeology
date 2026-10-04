#!/usr/bin/env bash
# One E005 cycle run. Usage: cyc.sh ARM STEPS-FILE [--explore | other cycle.py args]
# The machine-local locations default to this machine's profile; override them in the environment.
set -u
ROOT=$(cd "${BASH_SOURCE[0]%/*}/../../.." && pwd)
D=${E005_BASE:-$HOME/.local/share/isle-wars-archaeology}
IW_DOS_DIR=${IW_DOS_DIR:-$D/iw-dos/install} IW_DOS_RUN=${IW_DOS_RUN:-$D/iw-dos/run} \
E005_BUNDLES=${E005_BUNDLES:-$D/E005-bundles} E005_EXPLORE=${E005_EXPLORE:-$D/E005-explore} \
exec python3 "$ROOT/runtime/iw-dos/spike/cycle.py" --experiment E005 --arm "$1" --steps "$2" "${@:3}"
