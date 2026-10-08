T38 review (sol)
You review PR #118 at f19dab6c72d4aa15f546425e6a903453bcb1586c. You did not write it. This is a narrow re-review (round 3), granted by the owner after escalation (rule 7).
0. Prove the tree: HEAD is f19dab6c72d4aa15f546425e6a903453bcb1586c and `git diff 1afbb1bc5c0b003a24555e24ddc32461e365384c HEAD` is round 3's change; findings name its files.
1. Scope: your round-2 findings R1, R2 and R3 only (your previous review comment on PR #118, pasted below), plus the sweeps Opus reports in the PR body's "Round 3" section. Raise no other finding unless it is blocking and was introduced by round 3.
2. For R1 and R2, remove each fix (in place, then restore) and name the test that fails. Re-run your own R1 and R2 probes against the new code.
3. Re-run `python3 -m unittest discover -s tests` and Done-when lines 2, 6, 7 and 8, and account for DW1–DW8 (`DW<k>: ran <command> → <result>` or `DW<k>: not run — <reason>`; DW1's find and DW3's records need the sitting).
4. Display isolation must still hold after round 3's changes to `runtime/iwp/driver/session.py` and `clicks.py`. A path to the caller's DISPLAY is blocking.
Prove each finding (run it, or delete the behaviour and name the test that fails) or label it unverified. Your final message is the review: the header; the verdict (approve | approve after named fixes | rework | user decision); the DW lines; the findings R1..Rn (file:line, blocking or not); the verdict again last. Never post it: the script posts it and applies the label.

# The review brief's own sections

Every review brief carries these two sections, in full, after the numbered block of
`process.md` §5 (or, in the review profile, after the brief's numbered lines). The reviewer reads
the brief in another file, so paste them; never point to this one. Write "Blocking means" for the
task; paste the second section as it is. (L47, L49)

```text
## Blocking means

Any one is enough; a blocking finding means rework, never approve.
1. A Done-when line fails, or cannot be run as written.
2. What this task protects can be got past: <name it: the guard, check, permission, invariant,
   rule value or file this task exists to protect>. A bypass you proved is blocking, even when it
   looks like an edge case. Never "follow-up hardening" or "outside the threat model" unless the
   task says so; if it does, quote the line. (L47)
3. Behaviour the task forbids, or behaviour nobody asked for, inside a file the task requires. (L44)
4. <project-specific items: a constant with no evidence, a test that passes with the behaviour
   deleted, a status written into a document>
Not blocking: wording, style, and defects in code the PR did not change: file those as follow-ups.
When unsure, say how likely the problem is. Rate it blocking only if it is likely and would get
past what the task protects; otherwise it is a follow-up. (L53)

## Report every blocking finding in this one review

This review is your only pass before the author fixes. Do not stop at the first blocking
finding: finish reading the whole diff and the task file, check every Done-when line and
every item under "Blocking means", and report all blocking findings together.

- Before you write the verdict, make one last pass over the full diff for anything you have
  not yet rated, and say "Final pass done" as the last line before the verdict.
- Number the findings R1, R2, … in order of severity. A finding you held back because an
  earlier one was already blocking is a review defect: if two problems share a cause, list
  both and say so.
- Do not rely on a later round. The author fixes everything you list, and the next review
  checks those fixes and new code only, not anything you saw but did not report.
- If you ran out of time or context before covering the whole diff, say which files or
  sections you did not cover. Do not approve in that case.
```

## Your round-2 review, in full

T38 review (gpt-6.1-sol)
rework

DW1: not run — needs the sitting for the machine-local find assertion. Ran the prescribed user-path grep → pass; clean-status assertion fails only because the supplied harness brief is untracked.
DW2: ran `bash tools/wine-driver.sh --batch cmb-accumulation --help`, `bash tools/wine-driver.sh --batch bomb-sampling --help`, and `bash tools/wine-driver.sh --batch unknown-x --help` → correct targets; known batches exit 0, unknown batch exits 2 and names `unknown-x`.
DW3: not run — needs the sitting for the platform-token assertion and actual records. Ran both prescribed find/xargs validators → exit 0 with no inputs; `python3 tools/check_no_originals.py` → pass.
DW4: ran the prescribed structural-field grep and DW3 schema-validation command → pass with no records. Export/value rejection tests also pass.
DW5: ran the prescribed diff assertion over `runs/E018`, `runs/E019`, and `findings/F020-pro-corroboration.md` → pass; both batch notes identify owner-play evidence as primary.
DW6: ran `python3 tools/check_no_originals.py` and the verbatim five-case Python gate assertions → pass: F019 row accepted, all four mutations refused. Actual E020 records remain pending.
DW7: ran the prescribed `git diff`/`wc -l` assertion over `spec/` → pass.
DW8: ran `python3 tools/check_counts.py experiments/E020-wine-first-run/scenarios.txt` → exit 1, reporting zero observations and the expected shortfalls; no outcomes file exists. Ran `check_links.py`, `check_no_originals.py`, and `check_pro_question_map.py` → all pass. GitHub reports successful CI checks; this review is not approving.

HEAD verified: `1afbb1bc5c0b003a24555e24ddc32461e365384c`; supplied detached worktree verified; nonempty diff contains 24 files, all read.
Verification: `TMPDIR=<review scratch> python3 -m unittest discover -s tests` → 716 tests pass. An earlier invocation with `PYTHONDONTWRITEBYTECODE=1` invalidated the existing cache-edge test’s premise; rerunning without that override passed. `git diff --check origin/main...HEAD` passes. The batch record checker reports zero records and manifests.
Round-1 findings and their replacement tests were inspected and the tests rerun. I did not independently repeat the author’s 25 source-deletion mutations, so that mutation-coverage claim remains unverified.
Display isolation: no caller-DISPLAY fallback was found on the sitting’s window lookup, capture, or input paths. Inputs now pass through Session; watcher commands receive its environment and window. No Wine or game run occurred. Findings below were reproduced with synthetic inputs and fake dependencies. No source files were changed; scratch directory removed.

R1 — **blocking** — `experiments/E020-wine-first-run/e020_loop.py:60–69,78,84–89`: **Exhausting the readiness wait still permits game input.** `wait_quiet()` returns `False` after six unsuccessful polls, but all three callers ignore that result. I ran the real BatchLoop with the existing FakeDriver configured for 100 noisy polls and a successful placement: it executed six unsuccessful `quiet` blocks, then `place` and `commit`, and returned a normal `games-max` summary. Thus the state-aware readiness check can fail without stopping subsequent clicks—the wrong-state continuation class from round-1 R10 remains. An active computer turn or battle is a likely instance; actual battle input was not reproduced because the review does not run the game. Abort through Session, or stop with an explicit unsuccessful state, when readiness cannot be established. Add a test asserting that exhausted noisy-board waits send no placement or commit inputs; the current bounded-wait test permits this continuation.

R2 — **blocking** — `tools/check_counts.py:230–236`: **Q-CMB-05’s fixed-attacker requirement can still be bypassed.** The rule selects the largest count independently for each defender size, so different attacker sizes can satisfy different arms. I supplied 100 complete events for each pair `(attacker, defender) = (2,1), (3,2), (4,3), (5,4), (10,10)`. Event validation returned no problems and `rule_cmb_05()` returned `True`, although no attacker size occurs across all defender arms. `walkthroughs/f011-questions.md:21` requires “vs attacker fixed.” Consequently the changed corroboration guard can accept `corroborated` without its required controlled comparison; round-1 R9 is not fixed as a class. This does not demand hitting the deferred T40 targets now: it concerns the guard already implemented in this PR. Require one common attacker size with sufficient observations in every defender arm, and add both mixed-size rejection and common-size acceptance tests.

R3 — **not blocking; documentation correction** — `evidence/E020/README.md:9–10`: **The README still describes sitting bundles as release assets.** The amended contract explicitly keeps bundles on the user’s machine and makes no release asset; `store: release:E020` is only the schema-required experiment name. Update this wording so a later operator is not instructed toward the prohibited upload. No upload implementation was found.

Final pass done

rework

— gpt-6.1-sol, via tools/harness/review.mjs (openai/gpt-6.1-sol)
