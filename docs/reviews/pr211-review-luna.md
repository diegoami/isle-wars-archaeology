# PR #211 review (Luna) — hand-posted (harness exited 3, bug #203)

This is the review record for `fix #204: trust the 9P host ACL instead of mount flags in
install_writable` (PR #211). It is hand-posted because `tools/harness/review.mjs` ran Luna
correctly and got a clean approve, but its output parser did not extract the verdict from the
OpenCode output file (the bug filed as #203: "review.mjs exits 3 on a well-formed review when the
OpenCode log mixes color codes and markdown"). The session record
`ses_ecc149317ffeVgZSd12ICcAyKN` does contain the review exactly as Luna returned it; per rule
25, the run's final message is read before acting on it.

## Reviewer

GPT-5.6 Luna (openai family, not the session's minimax family) — cross-family ✓.
Worktree: `/home/diego/projects/isle-wars-archaeology-work/211-review-8aefebac` at
`5840e659da8cd290a2bdecdf3a3ed3ff3e848d8a`.

## Verdict

approve

## Done-when

| # | Done-when | Result |
|---|-----------|--------|
| 1 | `python3 -m unittest tools.tests.test_install_seal_9p` exits 0 | 13 tests passed |
| 2 | 9P path → False even with `os.access(W_OK)=True` and `f_flag` lacking `ST_RDONLY`; rule-9 mutation removes the 9P branch and the test fails; restored | expected failure; restored |
| 3 | Non-9P read-only path → False (kernel says read-only) | passed |
| 4 | Non-9P writable path → True (no seal) | passed |
| 5 | `mount_fstype_for` matches: exact, inner, trailing-slash, more-specific-wins | passed |
| 6 | `mount_fstype_for` returns None when `/proc/self/mountinfo` cannot be read | passed |
| 7 | Live readout on this machine: `/mnt/c/.../Isle Wars Pro Game` → False; `/tmp` → True; `/` → True | matches |

## Findings

None.

## Final pass done

approve
