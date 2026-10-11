#!/usr/bin/env bash
# Watch one background job (CLAUDE.md rule 6.7, L48): report its exit, a stall, and problem lines.
#
#   tools/harness/watch.sh --label NAME (--unit UNIT | --pid PID | --pid-of PATTERN) [--file F]... \
#       [--opencode-log LOG] [--problem REGEX] [--idle-min 10] [--every 60]
#
# --unit (preferred: a job started with tools/harness/run-unit.sh): alive while
# `systemctl --user is-active` says so, and the exit line gives the unit's result. Otherwise the
# job is alive while `kill -0 PID` succeeds. Never `pgrep -f PATTERN` in a loop: the pattern is in
# the watching shell's own command line, so it always matches itself and the exit is never seen
# (2026-10-04, L48; again 2026-10-11, where a review's exit went unseen for 1.5 h).
# --pid-of resolves PATTERN once, at start, leaving out this script and its own ancestors, and
# refuses when it finds no process or more than one.
# Progress: --file (repeatable) counts the files' total size. --opencode-log is an OpenCode run's
# log: its "session ses_… started" line names the session, whose newest update in the harness
# database (read-only) is then the signal, since `opencode run` writes its output file only at
# the end and a size watch flags a healthy run as stuck (goal2-archaeology, 2026-10-11).
# No progress for --idle-min minutes prints "possibly stuck" (once per stall). --problem: a new
# line in the first --file matching REGEX is printed. The script ends when the job exits.
set -u
label=job pid= unit= pattern= idle_min=10 every=60 problem= oclog=
files=()
while [ $# -gt 0 ]; do
  case "$1" in
    --label) label=$2; shift 2 ;;
    --unit) unit=$2; shift 2 ;;
    --pid) pid=$2; shift 2 ;;
    --pid-of) pattern=$2; shift 2 ;;
    --file) files+=("$2"); shift 2 ;;
    --opencode-log) oclog=$2; shift 2 ;;
    --problem) problem=$2; shift 2 ;;
    --idle-min) idle_min=$2; shift 2 ;;
    --every) every=$2; shift 2 ;;
    *) echo "watch.sh: unknown argument $1" >&2; exit 2 ;;
  esac
done

ancestors() {  # this shell and every process above it
  local p=$$
  while [ -n "$p" ] && [ "$p" != 0 ]; do
    echo "$p"
    p=$(awk '{print $4}' "/proc/$p/stat" 2>/dev/null)
  done
}

if [ -z "$pid" ] && [ -z "$unit" ] && [ -n "$pattern" ]; then
  mine=$(ancestors)
  found=()
  for p in $(pgrep -f -- "$pattern"); do
    grep -qx "$p" <<<"$mine" && continue
    tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null | grep -q 'watch\.sh' && continue
    found+=("$p")
  done
  # a wrapper and the command it runs both match: keep the outermost one
  if [ ${#found[@]} -gt 1 ]; then
    outer=()
    for p in "${found[@]}"; do
      parent=$(awk '{print $4}' "/proc/$p/stat" 2>/dev/null)
      printf '%s\n' "${found[@]}" | grep -qx "$parent" || outer+=("$p")
    done
    found=("${outer[@]}")
  fi
  if [ ${#found[@]} -ne 1 ]; then
    echo "$label: --pid-of '$pattern' found ${#found[@]} processes (${found[*]:-none}); pass --pid" >&2
    exit 2
  fi
  pid=${found[0]}
fi
[ -n "$pid" ] || [ -n "$unit" ] || { echo "watch.sh: --unit, --pid or --pid-of is required" >&2; exit 2; }

alive() {
  if [ -n "$unit" ]; then systemctl --user is-active -q "$unit"; else kill -0 "$pid" 2>/dev/null; fi
}
alive || { echo "$label: ${unit:-pid $pid} is not running"; exit 1; }
echo "$label: watching ${unit:-pid $pid}"

session_updated() {  # newest update (ms) of the OpenCode session the log names, or nothing
  local sid
  sid=$(grep -o 'session ses_[A-Za-z0-9]* started' "$oclog" 2>/dev/null | tail -1 | cut -d' ' -f2)
  [ -n "$sid" ] || return 0
  python3 -I -c '
import os, sqlite3, sys
db = os.path.expanduser("~/.local/share/harness-opencode/data/opencode/opencode.db")
c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
a = c.execute("select time_updated from session where id=?", (sys.argv[1],)).fetchone()
b = c.execute("select max(time_updated) from part where session_id=?", (sys.argv[1],)).fetchone()
print(max((a or [0])[0] or 0, (b or [0])[0] or 0))
' "$sid" 2>/dev/null
}

progress() {
  local t=0 s
  for f in "${files[@]}"; do s=$(stat -c %s "$f" 2>/dev/null || echo 0); t=$((t + s)); done
  [ -n "$oclog" ] && t="$t:$(stat -c %s "$oclog" 2>/dev/null):$(session_updated)"
  echo "$t"
}

tracked=0
{ [ ${#files[@]} -gt 0 ] || [ -n "$oclog" ]; } && tracked=1
prev=$(progress) still=0 flagged=0 seen=0
[ -n "$problem" ] && [ ${#files[@]} -gt 0 ] && seen=$(grep -cE -- "$problem" "${files[0]}" 2>/dev/null)
while alive; do
  sleep "$every"
  now=$(progress)
  if [ "$now" = "$prev" ]; then still=$((still + every)); else still=0 flagged=0 prev=$now; fi
  if [ $tracked = 1 ] && [ $still -ge $((idle_min * 60)) ] && [ $flagged = 0 ]; then
    echo "$label: possibly stuck: no progress for $idle_min min"; flagged=1
  fi
  if [ -n "$problem" ] && [ ${#files[@]} -gt 0 ]; then
    n=$(grep -cE -- "$problem" "${files[0]}" 2>/dev/null)
    if [ "${n:-0}" -gt "$seen" ]; then
      echo "$label: problem: $(grep -E -- "$problem" "${files[0]}" | tail -1 | cut -c1-200)"; seen=$n
    fi
  fi
done
last=""
[ ${#files[@]} -gt 0 ] && last=$(tail -1 "${files[0]}" 2>/dev/null | cut -c1-300)
[ -z "$last" ] && [ -n "$oclog" ] && last=$(tail -1 "$oclog" 2>/dev/null | cut -c1-300)
echo "$label: exited${last:+: $last}"
