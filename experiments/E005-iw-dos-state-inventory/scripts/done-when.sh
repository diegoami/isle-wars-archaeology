#!/usr/bin/env bash
# Run T14's Done-when commands and keep each output in measurements/done-when/ (rule 20).
# Needs IW_DOS_DIR and IW_DOS_RUN (and a TMPDIR outside every checkout) in the environment.
set -u
ROOT=$(cd "${BASH_SOURCE[0]%/*}/../../.." && pwd)
cd "$ROOT" || exit 1
OUT=experiments/E005-iw-dos-state-inventory/measurements/done-when
mkdir -p "$OUT"
TS=$(date -u +%Y%m%dT%H%M%SZ)
run() {  # run NAME COMMAND...
  local name=$1; shift
  { echo "\$ $*"; "$@" 2>&1; echo "exit=$?"; } > "$OUT/$name-$TS.txt"
  tail -n 3 "$OUT/$name-$TS.txt"
}
run unittest python3 -m unittest discover -s tests
run mutants python3 tests/mutants_iw_dos.py
run validate-records sh -c 'python3 tools/validate_records.py runs/E005/*.json evidence/E005/*.json | grep -vc "^ok"; python3 tools/validate_records.py runs/E005/*.json evidence/E005/*.json | grep -c "^ok"'
run runtime-profile setup/iw-dos/iw-dos-runtime.sh
run register-check python3 tools/register_artifact.py check "$IW_DOS_DIR" iw-dos-3.1-30121376 --strict
# Done-when 6's grep, with its pattern assembled from pieces: this very script and its output are inside the
# grep's own scope, so neither may contain the pattern's text. The pattern is the task file's, unchanged.
PAT='program fi''les|/m''nt/|[a-z]:\\\\|/ho''me/|\.local/sh''are'
{ echo "\$ git grep -n -i -E '<the pattern of Done-when 6>' -- runtime/iw-dos setup/iw-dos findings experiments/E005-iw-dos-state-inventory runs/E005 evidence/E005 knowledge-map.md"
  git grep -n -i -E "$PAT" -- runtime/iw-dos setup/iw-dos findings experiments/E005-iw-dos-state-inventory runs/E005 evidence/E005 knowledge-map.md
  echo "exit=$? (1 means no line matched)"; } > "$OUT/grep-paths-$TS.txt"
cat "$OUT/grep-paths-$TS.txt"
run check-no-originals python3 tools/check_no_originals.py
run check-links python3 tools/check_links.py
run files-over-1mb sh -c 'git ls-files | while read f; do [ -f "$f" ] && [ "$(stat -c %s "$f")" -gt 1000000 ] && echo "$f"; done; echo done'
run tracked-evidence sh -c 'git ls-files evidence/E005 | grep -vc "manifest.json$"; git ls-files evidence/E005 runs/E005 experiments/E005-iw-dos-state-inventory | grep -ci -E "\.(sav|exe|ov[0-9]|png|rgb|zip)$"'
run knowledge-map-diff git diff origin/main...HEAD -- knowledge-map.md
