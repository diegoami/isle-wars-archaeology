#!/usr/bin/env bash
# Kept for the name the exploration of round 0 used: the work is keep-explore.py, which never replaces or deletes a
# kept file (PR #58 R3). Usage: keep-explore.sh KEY [KEY ...]
set -eu
exec python3 "${BASH_SOURCE[0]%/*}/keep-explore.py" "$@"
