# F020 Corroboration of Pro static rule readings by recorded play

- **Status**: proposed
- **Question**: For each rule claim in F011–F016, F018, F019 and the three measured
  questions (Q-TRN-05, Q-REI-05, Q-AI-07), does recorded ordinary play on the
  unregistered Pro build corroborate, narrow, or fail to establish the static reading?
  What do the recorded counts show?
- **Experiment**: E018 (this file's `Owns`). Records: `runs/E018/**`; screenshots:
  `evidence/E018/**`. The recorder: `experiments/E018-pro-corroboration/record_f011.py`
  and per-question scripts; the check: `check_recorded_plays.py`.
- **Artifact**: set `iwp-2.0-996e86c5`, unregistered build, sha256
  `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`. Rule 19:
  Pro only; nothing here is claimed for DOS Isle Wars.
- **Confidence**: each outcome carries its own confidence (rule 22); the summary
  describes only `corroborated` and `narrowed` outcomes.
- **What would change it**: a different result from recorded play — the per-claim
  "what would change it" says what.

## Summary

*(filled after C3 runs — initially empty; only `corroborated` and `narrowed` are
described here)*

## F011 combat — per-claim outcomes

| Claim | Question | Outcome | Recorded counts | Confidence | What would change it |
| --- | --- | --- | --- | --- | --- |
| C-CMB-01 | Q-CMB-01 | pending | — | — | — |
| C-CMB-02 | Q-CMB-02 | pending | — | — | — |
| C-CMB-03 | Q-CMB-03 | pending | — | — | — |
| C-CMB-04 | Q-CMB-04 | pending | — | — | — |
| C-CMB-05 | Q-CMB-05 | pending | — | — | — |
| C-CMB-06 | Q-CMB-06 | pending | — | — | — |
| C-CMB-07 | Q-CMB-07 | pending | — | — | — |
| C-CMB-08 | Q-CMB-08 | pending | — | — | — |
| C-CMB-09 | Q-CMB-09 | pending | — | — | — |
| C-CMB-10 | Q-CMB-10 | pending | — | — | — |
| C-CMB-11 | Q-CMB-11 | pending | — | — | — |
| C-CMB-12 | Q-CMB-12 | pending | — | — | — |

### F011 Q-CMB-01 detail

*(filled after C3 runs — attack from N = 2, 4, 8, 12 against N-1, N, N+1, N+2)*

**T28 target**: 16 cases, deterministic, once each (human); 100+ observed attack starts (computer).

**Recorded counts** (from `runs/E018/combat/`):

```
pending
```

**Outcome**: `pending` — awaiting C3 runs.

### F011 Q-CMB-02 detail

*(filled after C3 runs — boundary at N = 4, 8, 12, 20)*

**T28 target**: 4 boundary cases once each (human); 100+ starts (computer).

**Recorded counts**:

```
pending
```

**Outcome**: `pending`.

### F011 Q-CMB-03 detail

*(filled after C3 runs — attack from 1, 2, 3 armies against 1-army neighbour)*

**T28 target**: 3 cases (human).

**Recorded counts**:

```
pending
```

**Outcome**: `pending`.

### F011 Q-CMB-04 detail

*(filled after C3 runs — exchanges and losses at attacker sizes 2,3,4,5,10)*

**T28 target**: at least 100 exchanges per attacker size (500 total).

**Recorded counts**:

```
pending
```

**Outcome**: `pending`.

### F011 Q-CMB-05 detail

*(filled after C3 runs — defender at 1,2,3,4,10)*

**T28 target**: at least 100 exchanges per defender size (500 total).

**Recorded counts**:

```
pending
```

**Outcome**: `pending`.

### F011 Q-CMB-06 detail

*(filled after C3 runs — equal results, attacker-loss share)*

**T28 target**: at least 500 exchanges; expect 58% attacker-loss share.

**Recorded counts**:

```
pending
```

**Outcome**: `pending`.

### F011 Q-CMB-07 detail

*(filled after C3 runs — one army lost per exchange)*

**T28 target**: at least 200 exchanges at several sizes; each is (attacker -1, defender 0) or (0, defender -1).

**Recorded counts**:

```
pending
```

**Outcome**: `pending`.

### F011 Q-CMB-08 detail

*(filled after C3 runs — single vs multiple exchanges, quit button)*

**T28 target**: at least 10 human attacks.

**Recorded counts**:

```
pending
```

**Outcome**: `pending`.

### F011 Q-CMB-09 detail

*(filled after C3 runs — failed attack consequences)*

**T28 target**: at least 5 failed human attacks.

**Recorded counts**:

```
pending
```

**Outcome**: `pending`.

### F011 Q-CMB-10 detail

*(filled after C3 runs — attacks per turn)*

**T28 target**: at least 10 turns with 3+ attacks.

**Recorded counts**:

```
pending
```

**Outcome**: `pending`.

### F011 Q-CMB-11 detail

*(filled after C3 runs — VIPC-list effect)*

**T28 target**: at least 500 exchanges split by VIPC membership.

**Recorded counts**:

```
pending
```

**Outcome**: `pending`.

### F011 Q-CMB-12 detail

*(filled after C3 runs — does attacking pay?)*

**T28 target**: at least 100 attacks per ratio band; 20+ games where one seat never attacks.

**Recorded counts**:

```
pending
```

**Outcome**: `pending`.

## F012 turn / victory — per-claim outcomes

*(batch F012 — filled in the next push after F011)*

| Claim | Question | Outcome | Recorded counts | Confidence | What would change it |
| --- | --- | --- | --- | --- | --- |

## F013 reinforcement — per-claim outcomes

*(batch F013 — filled after F012)*

## F014 cards — per-claim outcomes

*(batch F014 — filled after F013)*

## F015 centres / hazards — per-claim outcomes

*(batch F015 — filled after F014)*

## F016 AI — per-claim outcomes

*(batch F016 — filled after F015)*

## F018 deal — per-claim outcomes

*(batch F018 — filled after F016)*

## F019 setup — per-claim outcomes

*(batch F019 — filled after F018)*

## Measured questions

*(Q-TRN-05, Q-REI-05, Q-AI-07 — filled after F019)*

| Question | Outcome | Recorded counts | Confidence | What would change it |
| --- | --- | --- | --- | --- |
| Q-TRN-05 | pending | — | — | — |
| Q-REI-05 | pending | — | — | — |
| Q-AI-07 | pending | — | — | — |

## Method

- **Static first (rule 24).** F011–F016, F018, F019 are static readings;
  T28 corroborates from recorded play.
- **Recorder.** `experiments/E018-pro-corroboration/record_f011.py` drives the game
  via the T13 Session API and writes one JSON record per question per run.
- **C3 runs.** The main session runs the game cycles on the install; the
  implementer processes the records into per-claim outcomes.
- **Check.** `check_recorded_plays.py` validates the records: every claim has at
  least one record, and no record is marked `corroborated` without meeting the
  per-arm count target.

## Sources

- F011 (`findings/F011-pro-combat-rules.md`), claims C-CMB-01 through C-CMB-12
- F012–F016, F018, F019: respective finding files
- Q-TRN-05, Q-REI-05, Q-AI-07: `questions/pro-static.md`
- E018 records: `runs/E018/**/*.json`
- E018 screenshots: `evidence/E018/**/*.png` (by hash; originals not in repo)

## Reproduction

```bash
# Run the check
python3 experiments/E018-pro-corroboration/check_recorded_plays.py

# Run one question's recorder (the main session's C3 command)
python3 experiments/E018-pro-corroboration/record_f011.py Q-CMB-04 \
    --count-target 500 --attacker-sizes 2 3 4 5 10 --defender-size 1
```
