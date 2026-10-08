#!/usr/bin/env bash
# E020's batch dispatcher (T38). The contract path Done-when 2 names:
#
#   bash tools/wine-driver.sh --batch cmb-accumulation --help   # prints batch 1's targets, exit 0
#   bash tools/wine-driver.sh --batch bomb-sampling --help      # prints batch 2's targets, exit 0
#   bash tools/wine-driver.sh --batch unknown-x --help          # refuses it by name, non-zero
#   bash tools/wine-driver.sh --batch <name>                    # one sitting (user's machine, owner's go-ahead)
#   bash tools/wine-driver.sh --records --sitting <dir> --batch <name>
#
# `--batch NAME --help` never starts wine: the launcher prints the batch's targets from
# experiments/E020-wine-first-run/scenarios.txt. A batch outside "Why a run is made" is refused by
# name before wine starts (constraint B of the rule 18 carve-out).
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
exec python3 "$ROOT/experiments/E020-wine-first-run/launcher.py" "$@"
