T51 review (Sol)

You review PR #197 at 646cb32335148c8ac119fed5266c33b858743dd7. You did not write it; a Claude (Opus) subagent did. It is a design task:
malpaco's rules for cards, island bonuses, production centres and events, a decision for each of
the 23 spec claims, and the check script extended to a second design file. The task file follows in
full. T50 (merged, design/core-rules.md) holds the core rules and the owner's 12 decisions it must
fit. Your working directory is the review worktree: run commands there with no `workdir` argument,
and use relative paths.

0. Prove the tree: HEAD is 646cb32…, and the diff against origin/main is the PR's; findings name its files.
1. Re-run every Done-when line yourself, and account for each (L32). DW4 is a reading line: write
   `DW4: ran a read of the choices section → <result>`.
2. Every changed file is one the task owns (L44). The implementer changed one existing test assertion,
   because Done-when 1's new output format required it: confirm the assertion is no weaker. It also
   added a sentence to design/README.md allowing counts from the owner's recordings, with their source,
   as context: say whether that is acceptable under rule 18 (counts only, no quotes).
3. The extended check_design.py: mutation-prove each check for the second file. Delete each check, run
   the tests, see a test fail, and restore by writing back the saved contents in a `finally`.
4. Design quality, the task's purpose:
   - each decision has a real fun or balance reason;
   - the model numbers are right: re-run the pasted Python, and check the draw counts, trade-in value
     against income, and event frequency;
   - no card or event can decide a game on its own;
   - every rule binds human and computer alike, and every Pro asymmetry is dropped with its row;
   - nothing feel-changing is settled without being in Choices for the owner;
   - the rules fit T50's decisions: a generated board, decision 12's bonus rule, one attack rule,
     re-rolled ties, domination at 3/4;
   - a proposed amendment to core-rules.md is a choice, not a silent change;
   - it states requirements, not implementation algorithms with promised bounds;
   - no status snapshot appears in any document (rule 3);
   - the rules are complete enough to build: name any gap, such as an order of steps, an unstated
     number, or an edge case like a raid on a stack of 2, a shield against a shield, an empty deck, or
     events at the domination line.
5. Rule 18: no original card names, labels, screen text or title; no quote from findings/ or
   runs/E018/CORRECTIONS.md.

## Blocking means

Any one is enough; a blocking finding means rework, never approve.
1. A Done-when line fails, or cannot be run as written.
2. What this task protects can be got past: a spec claim with no row, or a wrong decision word, that
   check_design.py accepts for either design file; a feel-changing decision made without being listed
   for the owner; original game text in design/ (rule 18). A bypass you proved is blocking, even when
   it looks like an edge case. (L47)
3. Behaviour nobody asked for inside a file the task owns: the computer opponent's policy designed here
   instead of in T53; an edit outside Owns, such as to design/core-rules.md. (L44)
4. A test that passes with its check deleted; a wrong number that a balance argument rests on; a status
   written into a document; a weakened existing test.
Not blocking: wording, style, and defects in code the PR did not change: file those as follow-ups.
When unsure, say how likely the problem is. Rate it blocking only if it is likely and would get
past what the task protects; otherwise it is a follow-up. (L53)

## Report every blocking finding in this one review

This review is your only pass before the author fixes. Do not stop at the first blocking
finding: finish reading the whole diff and the PR body, check every Done-when line and
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

Your final message is the review: the header; the verdict (approve | approve after named fixes |
rework | user decision); per Done-when line `DW<k>: ran <command> → <result>` or
`DW<k>: not run — <reason>`; the findings R1..Rn (file:line, blocking or not); the verdict again
last. Never post it: the script posts it.

---
The task file, in full:

# T51 malpaco's design, variety: cards, island bonuses, production centres and events

- **Kind**: feature (design; no code in malpaco, no research run)
- **Issue**: #193 · **Branch**: `task/T51-design-variety` · **Merge after**: T50 (the core rules it
  builds on: the generated board, one attack rule, re-rolled ties, domination at 3/4)
- **Implementer**: the user's choice, asked before the run (CLAUDE.md rule 6), recorded here and on
  the issue.
- **Reviewer**: the user's choice at review: an external model, never the implementer's family.
- **Evidence**: the promoted spec only, at the commit the branch starts from: `spec/cards.md`,
  `spec/island-bonuses.md`, `spec/production-centres.md` and `spec/hazards.md` (23 claims: C-CRD-01
  to 07, C-BON-01 to 03, C-CEN-01 to 05, C-HAZ-01 to 08). Also these:
  - malpaco's core rules and the owner's decisions in `design/core-rules.md` (T50, merged);
  - the coverage of each question in play, in `runs/coverage.md`. All eight card kinds have been seen
    in the owner's sittings, trade-ins both accepted and declined, and the bomb's results; the
    per-sitting detail is in `runs/E018/CORRECTIONS.md`, as counts only, never quoted;
  - the direction in CLAUDE.md, "The goal is a fun game, not a copy": the cards add some unbalance and
    surprise (the owner, 2026-10-11).
- **Owns**: `design/variety.md`, `design/README.md` (one line for the new file), and
  `tools/check_design.py` with `tools/tests/test_check_design.py`, which are extended so the check
  covers a second design file and its spec files. Not `design/core-rules.md`: a change it needs is
  stated in `design/variety.md` as a proposed amendment, for the owner. Not `spec/**`, `findings/**`,
  `runs/**` or `questions/**`.
- **Why**: cards, island bonuses, centres and events are where a game differs from the last one. The
  owner wants them to bring surprise and some unbalance without deciding games by luck alone. Pro's
  versions are the starting point. Some of its quirks have no place in a fun game: a fixed,
  never-shuffled 34-card list; the bomb card emptying its drawer's whole hand; events the computer reads
  differently from the human; a centre-increase that doubles stacks up to 999.
- **Scope**:
  - **`design/variety.md`**: malpaco's rules for cards, island bonuses, production centres and
    events, written so that a TypeScript implementer can build them without reading the spec. Use our
    own words and our own names, with card names of our own (rule 18). Constants are given as numbers,
    or as `open` with the choices. The rules fit T50's core rules: a generated board, so island bonuses
    follow T50's generator rule; one attack rule for every seat; re-rolled ties; domination at three
    quarters.
  - **The decision table**: one row per in-scope spec claim, in the form
    `| C-<AREA>-<nn> | decision | malpaco's rule (§ link) | why |`, with exactly one of `keep`,
    `change`, `replace`, `drop` or `open`. The rules are the same as T50's: `change`, `replace` and
    `drop` say why the game is better; `open` goes into the owner's list.
  - **Surprise and balance, argued, with numbers**. A number from a model, not a measurement, says so.
    - *The deck:* its composition, whether it is shuffled and how, and how often each kind is drawn in
      a game of T50's typical length. Also the hand limit, and what happens on a draw into a full hand.
    - *Trade-ins:* what a set is, what each set gives, and how the value compares with a turn's income
      at each stage of a game, so that a trade-in is a swing, not a decider. Whether the value grows
      over a game, as in the classic escalating sets, and why or why not.
    - *The bomb and the shield* (Pro's bomb and anti-bomb): the bomb's effect, whom it may target, and
      the counter-play it allows.
    - *Comebacks and runaways:* whether cards help the trailing seat, the leader, or neither, and the
      rule that keeps a leader from snowballing on cards alone. Domination at three quarters ends the
      game, so a late card swing has limited room.
    - *Island bonuses* on a generated board: value against size and entrances, and how the generator
      keeps bonuses comparable.
    - *Production centres:* whether malpaco has them at all, and if so what they give, at what cost,
      and why their doubling is capped or replaced.
    - *Events:* which kinds exist, how often, who they can hit, and why no event decides a game. Pro's
      floor holds: no event wipes a stack or eliminates a seat. Events are seat-blind, the same for the
      human and the computer.
  - **Fairness between seats**: every card, bonus and event rule applies alike to human and computer
    seats. Each of Pro's asymmetries is listed as dropped, with its row: the computer's fixed trade
    priority and its uncapped wildcard removal, the human's protected-branch reordering, and events
    that pre-empt one seat's draw.
  - **The owner's choices**: a section `## Choices for the owner` that lists every `open` row and every
    `change` or `replace` that alters the feel of play, each with 2–3 options, a recommendation and its
    reason. The owner decides these; the implementer never does.
  - **`tools/check_design.py`** checks both design files: each against its own in-scope spec files,
    with the same five failures as before, so that a claim with no row in its design file fails.
    `python3 tools/check_design.py` with no argument checks every design file and prints one line each.
    The existing tests keep passing, and the new cases visit the second file. Each check has a test that
    fails when the check is removed (rule 9).
  - Out of scope:
    - the computer opponent's policy (T53, #196, planned): how it values cards, chooses trade-ins and
      targets. T51 states only the rules that bind every seat;
    - the UI of cards, the hand and events (T52);
    - edits to the malpaco repository;
    - new runs or recordings.
- **Done when**:
  1. `python3 tools/check_design.py` prints `design/core-rules.md ok: 59 claims, 59 rows` and
     `design/variety.md ok: 23 claims, 23 rows`, and exits 0. It exits 1 on `main` today, because
     there is no variety design.
  2. `python3 -m unittest tools.tests.test_check_design` passes, with at least one new test per
     failure for the second file, each with a fixture that trips that failure alone.
  3. `grep -c '^| C-' design/variety.md` prints 23.
  4. `## Choices for the owner` exists in `design/variety.md`, and every entry has options, a
     recommendation and a reason. The reviewer reads each one.
  5. `python3 tools/check_links.py` and `python3 tools/check_no_originals.py` pass, and the full test
     suite is green.
- **Hazards**:
  - **Copying the deck.** Pro's 34-entry list, its order and its card names stay out (rule 18).
    Design the deck from what makes play good; Pro's mix is evidence of one working choice, not a
    target.
  - **Luck deciding games.** A card or event that can turn a lost game into a win on its own is a
    balance bug unless it is rare and the owner chooses it. Show the size of each swing against a
    turn's income.
  - **Over-reach into T53.** The computer's card and event policy is T53's. Where a rule needs one,
    note the link instead of designing the policy.
  - **Deciding for the owner.** Every feel-changing call is listed as a choice with a recommendation.
