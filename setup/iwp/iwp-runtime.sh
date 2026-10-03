#!/usr/bin/env bash
# iwp-runtime: the Isle Wars Pro runtime profile (W3a draft). Idempotent; installs nothing and uses
# no sudo.
#
#   IWP_PREFIX   the Wine prefix, outside every checkout and worktree
#   IWP_DIR      the install; read and hashed only, to copy the registered files into the prefix
#   IWP_WINE     the Wine launcher to look for (default /usr/lib/wine/wine; the tests point it at a stub)
#
# Steps: check the system packages and say which is missing; build the prefix when it is absent;
# remove Z: and every link that leaves the prefix; make the game's copy in the prefix's C: drive
# equal to the registered set (artifacts/known.json); keep the registry files as the cycle's reset
# baseline; then run every token check of capabilities.json (tokens.py). It prints "ready" and
# exits 0 only when all of them pass, and names each one that fails otherwise. Every prefix step
# confines the locations first (locations.py) and refuses a prefix inside a checkout.
#
# TODO(H3): when game-archaeologist's generic preflight exists (07 §2), the last step becomes
#   `preflight --tokens <the tokens of capabilities.json>` (see tokens.py); the exit code is still
#   never trusted on its own (ADR-004).
set -u
ROOT=$(cd "${BASH_SOURCE[0]%/*}/../.." && pwd)
cd "$ROOT" || exit 1

if [ -z "${IWP_PREFIX:-}" ] || [ -z "${IWP_DIR:-}" ]; then
  echo "not ready: set IWP_PREFIX (the Wine prefix) and IWP_DIR (the install)" >&2
  exit 1
fi

missing=()
need() { command -v "$1" >/dev/null 2>&1 || missing+=("$2 (for $1)"); }
wine_bin=${IWP_WINE:-/usr/lib/wine/wine}
[ -x "$wine_bin" ] || missing+=("wine and wine32:i386 (for $wine_bin)")
need Xvfb xvfb
need xfwm4 xfwm4
need xdotool xdotool
need import imagemagick
need xdpyinfo x11-utils
need xprop x11-utils
need unshare util-linux
need mount mount
need python3 python3
need git git
if [ "${#missing[@]}" -gt 0 ]; then
  echo "not ready: missing system packages:" >&2
  printf '  %s\n' "${missing[@]}" >&2
  exit 1
fi

step() { python3 setup/iwp/prefix.py "$1" || { echo "not ready: prefix step '$1' failed" >&2; exit 1; }; }
step build
step strip-links
step sync-game
step baseline

python3 setup/iwp/tokens.py
