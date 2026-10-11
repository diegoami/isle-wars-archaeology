#!/usr/bin/env bash
# What an OpenCode run is doing now: its latest steps, read-only from the harness's data directory.
#
#   tools/harness/peek.sh ses_XXXX [-n 20]
#   tools/harness/peek.sh <run log> [-n 20]     (the log's "session ses_… started" line names it)
#
# Prints the newest N steps: each tool call with its status (running, completed, error) and the
# start of its input, and the start of each message the model wrote. It reads the session through
# `opencode export` with the harness's XDG directories (implement.mjs and review.mjs run there),
# never auth.json. Works while the run is going and after it ends.
set -eu
target=${1:?usage: peek.sh ses_XXXX|<run log> [-n N]}; shift
n=20
[ "${1:-}" = -n ] && n=$2
sid=$target
if [ -f "$target" ]; then
  sid=$(grep -o 'session ses_[A-Za-z0-9]* started' "$target" | tail -1 | cut -d' ' -f2)
  [ -n "$sid" ] || sid=$(grep -o '"sessionID":"ses_[A-Za-z0-9]*"' "$target" | head -1 | cut -d'"' -f4)
  [ -n "$sid" ] || { echo "peek.sh: no session id in $target yet" >&2; exit 1; }
fi
case "$sid" in ses_*) ;; *) echo "peek.sh: not a session id or a run log: $target" >&2; exit 2 ;; esac
H=${HARNESS_OPENCODE_HOME:-$HOME/.local/share/harness-opencode}
out=$(mktemp)
trap 'rm -f -- "$out"' EXIT
# to a file: a large session read through a pipe came back cut short
(cd /tmp && XDG_DATA_HOME=$H/data XDG_CACHE_HOME=$H/cache XDG_STATE_HOME=$H/state \
  opencode export "$sid" > "$out" 2>/dev/null) || { echo "peek.sh: opencode export $sid failed" >&2; exit 1; }
jq -r --argjson n "$n" '
  "\(.info.title) · \(.info.model.providerID)/\(.info.model.id) · \(.info.directory)",
  ([.messages[].parts[]
    | if .type == "tool" then "  tool \(.tool) [\(.state.status)]: \(.state.input | tostring | gsub("\n"; " ") | .[0:140])"
      elif .type == "text" and (.text | length) > 0 then "  says: \(.text | gsub("\n"; " ") | .[0:200])"
      else empty end] | .[-$n:][])
' "$out"
