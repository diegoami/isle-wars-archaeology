#!/usr/bin/env bash
# Copy the text outputs of --explore runs (run log, observations, changes log, DOSBox-X log and
# configuration) into measurements/, and list every capture and kept game-written file by sha256
# (the images and the files themselves stay on this machine: evidence bundles, never committed).
# Usage: keep-explore.sh ARM [ARM ...]      Never overwrites: an existing file is left as it is.
set -eu
ROOT=$(cd "${BASH_SOURCE[0]%/*}/../../.." && pwd)
SRC=${E005_EXPLORE:?E005_EXPLORE is not set}
DST=$ROOT/experiments/E005-iw-dos-state-inventory/measurements/explore
mkdir -p "$DST"
for arm in "$@"; do
  for f in run.log observations.json changes.log dosbox.conf.txt dosbox.log; do
    [ -f "$SRC/$arm.$f" ] && { [ -e "$DST/$arm.$f" ] || cp "$SRC/$arm.$f" "$DST/$arm.$f"; }
  done
  : > "$DST/$arm.captures.sha256.tsv.new"
  for f in "$SRC/$arm".*.png "$SRC/$arm".*ISLEWAR.*; do
    [ -f "$f" ] || continue
    printf '%s\t%s\t%s\n' "$(sha256sum "$f" | cut -d' ' -f1)" "$(stat -c %s "$f")" "${f#$SRC/$arm.}" >> "$DST/$arm.captures.sha256.tsv.new"
  done
  if [ -e "$DST/$arm.captures.sha256.tsv" ]; then rm "$DST/$arm.captures.sha256.tsv.new"; else mv "$DST/$arm.captures.sha256.tsv.new" "$DST/$arm.captures.sha256.tsv"; fi
done
