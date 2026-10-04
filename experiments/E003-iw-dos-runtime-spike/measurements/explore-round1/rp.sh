#!/bin/bash
# rp.sh TAG [VAR=value ...]: reset the explore copy, run probe2 in private namespaces, summarise
EX=<EXPLORE>
TAG=$1; shift
for f in "$EX"/game/*; do [ -e "$EX/../install/$(basename "$f")" ] || rm -f "$f"; done
env TAG="$TAG" "$@" timeout ${TMO:-120} unshare -rmpfn --mount-proc --kill-child "$EX/probe2.sh"
cd "$EX/out/$TAG" || exit 1
echo "== $TAG"
cat geom.txt 2>/dev/null
for f in *.rgb; do echo "$f $(sha256sum "$f" | cut -c1-16)"; done
echo "game files: $(ls "$EX/game" | wc -l) new: $(ls "$EX/game" | grep -v -x -F -f <(ls "$EX/../install") | tr '\n' ' ')"
