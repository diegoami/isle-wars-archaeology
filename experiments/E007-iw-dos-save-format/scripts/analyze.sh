#!/usr/bin/env bash
# Build every table F009 cites, from the run records and the evidence bundles, into a new batch directory
# measurements/analysis-<UTC time>/ (never replacing an earlier one). Needs E005_BUNDLES and E007_BUNDLES.
set -eu
ROOT=$(cd "${BASH_SOURCE[0]%/*}/../../.." && pwd)
cd "$ROOT"
EXP=experiments/E007-iw-dos-save-format
B=$EXP/measurements/analysis-$(date -u +%Y%m%dT%H%M%SZ)
mkdir "$B"
python3 $EXP/scripts/save-tables.py "$B/saves" | tee -a "$B/summary.txt"
python3 $EXP/scripts/check-stars.py "$B/stars" | tee -a "$B/summary.txt"
python3 $EXP/scripts/check-cards.py "$B/cards" | tee -a "$B/summary.txt"
python3 $EXP/scripts/check-crafted.py "$B/crafted" | tee -a "$B/summary.txt"
python3 $EXP/scripts/pair-diffs.py $EXP/pairs.json "$B/pairs" | tee -a "$B/summary.txt"
echo "$B"
