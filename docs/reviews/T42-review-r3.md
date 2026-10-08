T42 review (sol)
You review PR #129 at 28d2bb41f647d51fccea905edef5b5c685d555d6. You did not write it. This is a narrow re-review (round 3, granted by the main session under rule 7's exception).
0. Prove the tree: HEAD is 28d2bb41f647d51fccea905edef5b5c685d555d6; round 3 is `git diff 513a71e575e24b7ddfdb4b85cbf251d7b46f3da0 HEAD`. Findings name files in that diff.
1. Scope: your round-2 R1 and R2 only (pasted below), plus anything round 3 broke. Raise no other finding unless it is blocking and introduced by round 3.
2. For each, remove the fix or guard (in place, then restore) and name the test that fails. Re-run your own round-2 probes.
3. Re-run `python3 -m unittest discover -s tests`, and account for DW1–DW3 (DW2 is machine-local: the main session runs it at this head and posts its output on the PR).
Prove each finding or label it unverified. Your final message is the review: the header; the verdict (approve | approve after named fixes | rework | user decision); the DW lines; the findings R1..Rn (file:line, blocking or not); the verdict again last. Never post it.

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

T42 review (gpt-6.1-sol)
rework

DW1: ran `python3 -m unittest discover -s tests` → 871 tests passed.
DW2: not run — machine-local; main session's output on the PR at this head reports 8.000 fps and exit 0.
DW3: ran `python3 tools/check_no_originals.py` and `python3 tools/check_links.py` → both exited 0; GitHub reports CI and GitGuardian successful.

Verified the supplied detached worktree, HEAD `513a71e575e24b7ddfdb4b85cbf251d7b46f3da0`, and the nonempty diff against origin/main. Reviewed all changed code, tests, documentation and measurement records. All five measurements’ index/log hashes match their summaries, and every log entry matches its indexed name and hash. Synthetic measurement PNGs were deliberately deleted, so their hashes cannot be independently checked against retained images.

Round-1 R1–R3 are fixed with mutation-sensitive regression tests:
- Removing capture-overrun time fails `test_r1_the_interval_reaches_the_end_of_a_capture_past_the_deadline` and the command-level boundary test.
- Rounding before acceptance fails `test_r2_just_below_the_threshold_fails` and `test_sols_r2_case_fails_the_command_and_reports_the_unrounded_rate`.
- Removing socket ownership fails both adversarial ownership/retry tests.

R1 — **blocking** — `runtime/iwp/driver/watcher.py:209–212`: The duplicate branch trusts the cached `(name, sha256)` without checking the retained file, allowing a newly appended index line to name a file with a different hash. Reproduced with the real `Watcher.capture_once`, synthetic captures and an explicitly supplied staging directory: capture bytes `A`, change the retained file to bytes `B`, then capture `A` again. The second call succeeds with `duplicate=true`, records SHA256 `559aead0…` for `A`, but its named file hashes to `df7e70e5…` for `B`. This requires the retained file to change between captures; nevertheless, it demonstrably violates the index/file invariant the brief explicitly asks to protect. Before discarding a duplicate, verify that its retained target exists and matches the digest; reject an invalid target without appending another invalid index line. Add changed-file and missing-file regression tests.

R2 — **blocking test gap** — `tools/tests/test_watcher.py:164–170`, guarding `runtime/iwp/driver/watcher.py:223–225`: The destination-hash guard can be deleted without any test failing. I replaced `if sha256_file(path) != digest:` with `if False:`. All 40 watcher tests passed; independently repeating the mutation against the entire discovery suite also passed all 871 tests. The existing index/hash test exercises successful moves only, not the corruption this new guard rejects. Add a test whose move helper changes the destination bytes after moving, and require a `WatcherError`, removal of the invalid destination, and no index entry. That test must fail when destination verification is removed. This and R1 protect the same invariant, but concern separate branches.

Every mutation was restored using `git checkout -- runtime/iwp/driver/watcher.py`. The restored watcher’s 40 tests passed. No tracked changes remain; the brief was untouched and the scratch TMPDIR was removed.

Final pass done

rework

— gpt-6.1-sol, via tools/harness/review.mjs (openai/gpt-6.1-sol)
