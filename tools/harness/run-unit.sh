#!/usr/bin/env bash
# Start a long job as its own transient systemd unit (CLAUDE.md rule 6.7; goal2-archaeology L103):
#
#   tools/harness/run-unit.sh NAME LOG [--mem 6G] -- COMMAND [ARGS]...
#
# The unit is iwa-NAME. It runs in the current directory with this shell's environment (so a
# sourced /tmp/iwp-env.sh reaches it), under the memory cap (MemoryMax, no swap), with stdin from
# /dev/null (`opencode run` waits for stdin's end otherwise), and stdout and stderr to LOG. It
# outlives a Claude Code restart, `--collect` removes it when it exits, and its life is tested
# with `systemctl --user is-active iwa-NAME` (watch.sh --unit), never with `pgrep -f`.
set -eu
name=$1 log=$2; shift 2
mem=6G
[ "${1:-}" = --mem ] && { mem=$2; shift 2; }
[ "${1:-}" = -- ] && shift
[ $# -gt 0 ] || { echo "run-unit.sh: no command" >&2; exit 2; }
envargs=()
while IFS= read -r -d '' kv; do
  case "$kv" in BASH_FUNC_*|_=*|PWD=*|SHLVL=*|OLDPWD=*) continue ;; esac
  envargs+=(-E "$kv")
done < <(env -0)
printf -v cmd '%q ' "$@"
printf -v qlog '%q' "$log"
systemd-run --user --unit="iwa-$name" --collect -q -p MemoryMax="$mem" -p MemorySwapMax=0 \
  -p WorkingDirectory="$PWD" "${envargs[@]}" \
  /bin/bash -c "exec $cmd < /dev/null > $qlog 2>&1"
echo "started unit iwa-$name; log $log"
