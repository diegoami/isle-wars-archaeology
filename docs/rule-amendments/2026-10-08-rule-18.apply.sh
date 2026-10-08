#!/usr/bin/env bash
# Apply the rule 18 amendment patch and open the commit, with the owner
# as author and committer. The agent (this Claude Code session) is not
# involved in either `git apply` or `git commit`. Run this from the
# repository root in a shell where the owner is signed in to git.
#
#   cd /home/diego/projects/isle-wars-archaeology
#   bash docs/rule-18-amendment-2026-10-08.apply.sh
#
# The script is intentionally verbose so the owner sees every step.

set -euo pipefail

REPO="/home/diego/projects/isle-wars-archaeology"
PATCH="$REPO/docs/rule-amendments/2026-10-08-rule-18.patch"
MSGFILE="$REPO/docs/rule-amendments/2026-10-08-rule-18.commit-msg"

cd "$REPO"

echo "== sanity: working tree clean? =="
if ! git diff --quiet HEAD; then
  echo "working tree is dirty. Stash or commit first." >&2
  exit 1
fi

echo "== sanity: patch file present? =="
test -f "$PATCH" || { echo "missing $PATCH" >&2; exit 1; }
test -f "$MSGFILE" || { echo "missing $MSGFILE" >&2; exit 1; }

echo "== dry-run apply (no changes) =="
git apply --check "$PATCH"

echo "== apply =="
git apply "$PATCH"

echo "== diff (first 80 lines) =="
git diff -- CLAUDE.md | head -80

echo
echo "== the staged change =="
git add CLAUDE.md
git status --short

echo
echo "== open the commit, then EDIT and SAVE in the editor that opens =="
echo "   the commit message is in $MSGFILE; press ENTER to use it."
echo
read -r -p "press ENTER to open the editor and commit, or Ctrl-C to abort: " _

git -c user.name="Diego Amicabile" -c user.email="diego.amicabile@gmail.com" \
  commit -e -F "$MSGFILE"

echo
echo "== final state =="
git log -1 --stat
echo
echo "If the commit looks right, push with:"
echo "  git push origin main"
