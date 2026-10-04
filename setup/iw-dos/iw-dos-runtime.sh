#!/usr/bin/env bash
# iw-dos-runtime: the DOS Isle Wars runtime profile (W3b draft). Idempotent; installs nothing and
# uses no sudo.
#
#   IW_DOS_DIR    the copy of the game (the extracted archive); read and hashed only
#   IW_DOS_RUN    the run directory, outside every checkout and worktree; the run copy is
#                 <IW_DOS_RUN>/game, which DOSBox-X mounts as C: and nothing else
#
# Steps: check the system packages and say which is missing; make the run copy equal to the
# registered set (setup/iw-dos/rundir.py sync: plain files of its own, copied from IW_DOS_DIR,
# anything else removed); check it (rundir.py check, which runs register_artifact.py check
# --strict); then run the lane's token checks of capabilities.json (setup/iw-dos/tokens.py). It
# prints "ready" and exits 0 only when all of them pass, and names each one that fails otherwise.
#
# TODO(H3): when game-archaeologist's generic preflight exists (07 §2), the last step becomes
#   `preflight --tokens <the lane's tokens>`; the exit code is still never trusted on its own.
set -u
ROOT=$(cd "${BASH_SOURCE[0]%/*}/../.." && pwd)
cd "$ROOT" || exit 1

if [ -z "${IW_DOS_DIR:-}" ] || [ -z "${IW_DOS_RUN:-}" ]; then
  echo "not ready: set IW_DOS_DIR (the copy) and IW_DOS_RUN (the run directory)" >&2
  exit 1
fi

missing=()
need() { command -v "$1" >/dev/null 2>&1 || missing+=("$2 (for $1)"); }
need dosbox-x dosbox-x
need Xvfb xvfb
need xdotool xdotool
need import imagemagick
need convert imagemagick
need xdpyinfo x11-utils
need unshare util-linux
need mount mount
need python3 python3
need git git
if [ "${#missing[@]}" -gt 0 ]; then
  echo "not ready: missing system packages:" >&2
  printf '  %s\n' "${missing[@]}" >&2
  exit 1
fi

step() { python3 setup/iw-dos/rundir.py "$1" || { echo "not ready: run copy step '$1' failed" >&2; exit 1; }; }
step sync
step check

python3 setup/iw-dos/tokens.py
