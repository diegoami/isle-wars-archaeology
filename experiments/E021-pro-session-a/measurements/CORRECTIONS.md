# Corrections to E021's progress files

Measured outputs are never edited (rule 20). This file says which counts are wrong, and why.

## progress-r01.json: busy 10/10 was not met; the honest total is 13 of 40, not 23

`progress-r01.json` counts the first Session A sitting, 20261011T070437Z (record
`runs/E021/session-a/E021-r0001.json`, from commit `ed26e0c`). It gives 23 of 40 cells, ten of
them in the busy row (Q-CMB-10, turns with 3 or more attacks).

None of the ten busy cells is met.

- **What went wrong.** The loop counted every battle it opened toward a busy turn. In that sitting
  279 battles were opened by attacks aimed at the quit row and left at once, with no exchange
  click. The loop misread its own quit-attack press (below), so the quit row stayed unmet and the
  loop chose it again on every attack for the whole sitting. Each turn then counted 11 or 12
  "battles", and busy was met in ten turns where no attack fought.
- **Why it is not an observation.** Q-CMB-10 asks how many attacks a turn can make and what ends
  the turn. A battle that is opened and left before any exchange is not an attack that fought.
- **The other 13 cells stand:**
  - even 7 and underdog 2: the game's answer to each order, a battle or an answered refusal;
  - tiny 3: the same;
  - lost 1: a country handed over after a failed attack.

**The misread press.** The quit-attack click at 456,531 did close each battle: in all 178 leave
steps with a watcher frame taken before the second candidate was clicked, the battle panel was
already gone. The tour's test then looked for the turn menu's green, but the pointer had been left
over the CARD button, whose hover colour is outside the test's tolerance. So the second candidate
(495,540) was clicked and reported as the one that worked, and the press was never read as a quit.
The point and the frames are cited in `../session-a.steps`, block `quit-attack`.

## What the count does from now on

`e021_progress.py` reads the evidence each met group carries in the record itself:
- a busy cell counts only when its turn had at least 3 fights (`counter:fights`: battles with an
  exchange the board showed);
- a quit cell counts only when its battle fought before the press (`counter:fought` = 1).

E021-r0001's groups carry neither field, so it counts 13. `progress-r02.json` is that count, made
beside r01, with r01 left as it was.

I chose this rule over a hand-kept list of excluded cells for two reasons. Every record keeps
deciding for itself, and nothing outside the committed records can drift from them. A later
record's busy and quit groups carry the fields because the loop now writes them
(`e021_loop.py`, round 2).
