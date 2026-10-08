T36 review (Sol) (rework)

Re-review PR #111 against the rework's new commits.
PR: https://github.com/diegoami/isle-wars-archaeology/pull/111
Branch: task/T36-check-no-originals-wine-gate
Head: f14cf9c9ed31099c51b843df12774ec325b10a5f
Base: main
Issue: #108

## What changed since the original review

The original review (Sol, `gpt-6.1-sol`, effort `low`, posted
2026-10-08T14:04:33Z) returned R1 blocking: the gate's
`platform.startswith(WINE_PLATFORM_PREFIX)` was not protected by a
mutation test. Sol proved the bypass by replacing `startswith` with
`==` and showing all 13 tool tests and all 622 CI unittest tests
still passed, while a record with `runtime.platform =
"wine-on-user-machine-evil-suffix"` slipped through.

Two new commits on the branch fix R1:

- `673b95e` — `T36 rework: pin the recognised wine platform suffix
  (Sol R1)`. Adds `RECOGNISED_WINE_SUFFIXES` as a named constant in
  `tools/check_no_originals.py`, refactors the platform check to
  require the platform to be either `wine-on-user-machine` (no
  suffix) or one of the recognised suffixes, and adds two unit tests
  (`test_an_unrecognised_platform_suffix_is_refused` and
  `test_a_recognised_platform_suffix_is_accepted`).
- `f14cf9c` — `T36 rework: pin the recognised wine suffix at the
  CLI level too`. Adds the same two contract cases at the CLI level
  (per Sol's R1: "preferably at both unit and CLI levels").

## What I want from the re-review

Apply the **same mutation you applied last round** —
`platform.startswith(WINE_PLATFORM_PREFIX)` →
`platform == WINE_PLATFORM_PREFIX` — and verify:

1. The unit test
   `test_an_unrecognised_platform_suffix_is_refused` **fails** under
   the mutation (the mutation returns `("", "")` before reaching the
   suffix check).
2. The unit test
   `test_a_recognised_platform_suffix_is_accepted` **passes** under
   the mutation (the mutation returns `("", "")` before the hash
   check, which is exactly the pass the legitimate-suffix case
   expects).
3. The CLI tests for the same two cases (added in `f14cf9c`) fail
   and pass respectively under the mutation.
4. The recognised-suffix list is a named constant
   `RECOGNISED_WINE_SUFFIXES` in `tools/check_no_originals.py`,
   not a magic value buried in the check.
5. The full tool test suite (`python3 -m unittest discover -s
   tools/tests`) and the full CI unittest suite (`python3 -m
   unittest discover -s tests`) both pass under the original
   implementation.

If all five hold, R1 is fixed and the gate is dispatchable. If any
fails, REQUEST CHANGES with the specific test name and the mutation
that escaped it.

## What to keep verifying

The other mutation categories from your original review
(DW2): removing the F019-row match, the empty F019 table, removing
set+variant matching, removing the placeholder branch, and
case-insensitive platform matching — those all passed your mutations
last round and the rework did not touch that logic. The fix is
*additive* (the recognised-suffix list and the two contract cases).
A quick sanity check on those existing mutations is welcome but
should not need rework.

## Effort and chain

- Effort: `low` (Sol, sparingly, per the owner note).
- Chain: `[gpt-6.1-sol, zai-glm-5.3, ali-glm, ali-qwen-max,
  deepseek-pro, luna]` via `--hard --sol`.
- Family check: DeepSeek (Go) implemented, OpenAI (Sol) reviews.
  Different families.

Final pass done.
