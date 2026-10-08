T36 rework (DeepSeek V4.1 Flash on Go)

Re-dispatch after Sol's R1 blocking finding on PR #111.
PR: https://github.com/diegoami/isle-wars-archaeology/pull/111
Branch: task/T36-check-no-originals-wine-gate
Head: cb34a06115f94d4a662815bf5cc70a5c081cb65a
Base: main
Issue: #108

## What Sol found

Sol's R1 is a **proven bypass of the gate's prefix-matching**, found
by mutation testing:

- Sol replaced `platform.startswith(WINE_PLATFORM_PREFIX)` with
  `platform == WINE_PLATFORM_PREFIX` in
  `tools/check_no_originals.py`.
- Under that mutation, all 13 tool tests passed and all 622 CI
  unittest tests passed.
- A record with `runtime.platform = "wine-on-user-machine-iwp-2.0-evil-suffix"`
  and a fake 64-hex hash was returned `("", "")` (gate passes) — when
  it should be **refused** (the platform prefix matches but the
  suffix is unexpected; the only legitimate suffixed platforms are
  those the task file names).
- The original implementation correctly refuses it.

The mutation tests the implementer wrote covered:
- removing the F019-row match (caught)
- empty F019 table (caught)
- removing set+variant matching (caught)
- removing the placeholder branch (caught)
- case-insensitive platform matching (caught)

The mutation tests did **not** cover:
- replacing `startswith` with `==` (NOT caught — this is Sol's R1).

The brief's Hazards section listed "A check that does more than it
says" as blocking. A platform whose suffix is not on the legitimate
list is exactly that: an unexpected suffix means the platform is
not a recognised wine-on-user-machine variant, and the gate's
contract is "platform starts with `wine-on-user-machine` AND the
suffix is one of the recognised variants" (constraint C of the
carve-out: "or a more specific token the task file names, e.g.
`wine-on-user-machine-iwp-2.0`").

## What to fix

Two new test cases in `tools/tests/test_check_no_originals.py`:

1. **Refusal case (catches R1):** a record whose
   `runtime.platform` starts with `wine-on-user-machine` but whose
   suffix is NOT one of the recognised variants
   (`wine-on-user-machine-iwp-2.0` is the only one the brief names;
   any other suffix is unexpected). The record's other fields match
   the F019 row (hash, set, variant). The gate must refuse it with a
   message that names the unexpected suffix. This test must fail
   when `startswith` is replaced with `==` (R1's mutation) — that
   is the proof the test catches the bypass.

2. **Acceptance case (pins the legitimate-suffix contract):** a
   record whose `runtime.platform = "wine-on-user-machine-iwp-2.0"`
   (the brief's example) and whose other fields match the F019 row
   must be accepted. This test must pass under both the original
   implementation and the `==` mutation, because the legitimate
   suffixed platform is exactly the case the carve-out's constraint
   C permits.

The two cases together pin the contract: the gate accepts
`wine-on-user-machine[-<recognised-suffix>]` and refuses anything
else starting with `wine-on-user-machine`.

## How the recognised-suffix list is defined

The brief's only named suffix is `wine-on-user-machine-iwp-2.0`. The
carve-out's constraint C says "or a more specific token the task file
names" — so the recognised-suffix list is whatever the task file
names. For T36 the only entry is the iwp-2.0 variant. Future T37
dispatch (the wine-driver task file) may add to the list; if it does,
the test cases update to match.

**The recognised-suffix list lives in `tools/check_no_originals.py` as
a constant** (e.g. `RECOGNISED_WINE_SUFFIXES = ("-iwp-2.0",)`), and the
gate's check is "platform starts with `wine-on-user-machine` AND
(platform == `wine-on-user-machine` OR
`platform.startswith("wine-on-user-machine" + recognised_suffix)` for
each recognised suffix)". The constant is the right shape because it
makes the list explicit, testable, and updateable from one place.

## Why the gate's *code* is correct, only the tests are wrong

The implementer wrote `platform.startswith(WINE_PLATFORM_PREFIX)`
which is the right contract. Sol's R1 mutation (`==` instead of
`startswith`) is what proves the existing tests don't pin the suffix
contract. The fix is **add tests, do not change the gate's logic**,
unless the implementer finds a cleaner way to express the
"starts-with-or-recognised-suffix" contract that makes the test
naming obvious.

If the implementer does change the logic, the change must:
- keep `wine-on-user-machine` (no suffix) accepted when the F019 row
  matches,
- keep `wine-on-user-machine-iwp-2.0` (recognised suffix) accepted
  when the F019 row matches,
- refuse `wine-on-user-machine-evil-suffix` (unrecognised suffix)
  even when the F019 row matches.

## Done when

1. Two new test cases land in
   `tools/tests/test_check_no_originals.py`: the unrecognised-suffix
   refusal case and the recognised-suffix acceptance case.
2. Both tests pass under the original implementation.
3. The unrecognised-suffix test fails when `startswith` is replaced
   with `==` in `tools/check_no_originals.py` (R1's mutation).
4. The recognised-suffix test passes under the `==` mutation.
5. The recognised-suffix list is a named constant in
   `tools/check_no_originals.py` (e.g. `RECOGNISED_WINE_SUFFIXES`),
   not a magic value buried in the check.
6. `python3 tools/check_no_originals.py` and
   `python3 -m unittest discover -s tools/tests` both exit 0.
7. CI is green; the PR has Sol's re-review (the same Sol, effort
   `low`).

## What NOT to change

- The gate's `startswith` logic, unless the test naming makes the
  logic clearer (in which case the new logic must keep the same
  observed behaviour for the three contract cases above).
- The F019 row, the placeholder check, the set+variant check, the
  case-sensitivity contract — these all passed Sol's mutations.
- The recognised-suffix list does not need to grow for this rework;
  the iwp-2.0 entry is the only one the brief names.

## Effort and chain

- Implementer: DeepSeek V4.1 Flash on Go, effort `high` (the same
  model that did the original work; the rework is small and the
  implementer has the context).
- Reviewer: Sol again, effort `low`. The chain with `--hard --sol`
  stays the same: `[gpt-6.1-sol, zai-glm-5.3, ali-glm, ali-qwen-max,
  deepseek-pro, luna]`.
- Family check: DeepSeek (Go) implemented, OpenAI (Sol) reviews.
  Different families. No family conflict.

Final pass done.
