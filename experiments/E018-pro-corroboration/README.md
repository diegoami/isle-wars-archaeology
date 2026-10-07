# E018 pro-corroboration

Corroboration of the Pro static rule readings (F011–F016, F018, F019) by recorded
ordinary play on the unregistered Pro build (`iwp-2.0-996e86c5`), and the three
measured questions (Q-TRN-05, Q-REI-05, Q-AI-07).

- **Task**: T28 (#80)
- **Finding**: F020 (`findings/F020-pro-corroboration.md`)
- **Batches**: F011 (combat), F013 (reinforcement), F012 (turn/victory), F014 (cards),
  F015 (centres/hazards), F016 (AI), F018 (deal), F019 (setup), then Q-TRN-05,
  Q-REI-05, Q-AI-07.
- **Artifact**: set `iwp-2.0-996e86c5`, unregistered build.
- **Runtime**: the T13 driver Session API (`runtime/iwp/driver/session.py`), on
  Linux (WSL2) with Wine/Xvfb/xfwm4.

## Structure

```
experiments/E018-pro-corroboration/
  record_f011.py          # F011 (combat) recorder; run by main session via C3
  check_recorded_plays.py # validates records; exits 0 when all checks pass
  README.md               # this file

runs/E018/
  combat/                 # Q-CMB-* and Q-MOV-* and Q-OWN-* and Q-SET-04 records
  reinforcement/          # F013 records (future)
  turn-victory/           # F012 records (future)
  cards/                  # F014 records (future)
  centres-hazards/        # F015 records (future)
  ai/                     # F016 records (future)
  deal/                   # F018 records (future)
  setup/                  # F019 records (future)
  measured/               # Q-TRN-05, Q-REI-05, Q-AI-07 records (future)

evidence/E018/
  combat/                 # screenshots from combat runs, by hash
  ...                     # by batch

findings/F020-pro-corroboration.md  # the corroboration finding
```

## Recorder

`record_f011.py` drives one question's worth of play via the Session API:

```bash
# Example: Q-CMB-04 (dice counts at attacker sizes 2,3,4,5,10)
python3 experiments/E018-pro-corroboration/record_f011.py Q-CMB-04 \
    --count-target 500 --attacker-sizes 2 3 4 5 10 --defender-size 1
```

Each run writes one JSON record to `runs/E018/<batch>/` with:
`run_id`, `question_id`, `claim_id`, `per_arm_counts`, `screenshot_path`,
`screenshot_sha256`, `seal_ok`, `elapsed_seconds`, `outcome`, `status`.

## Check

```bash
python3 experiments/E018-pro-corroboration/check_recorded_plays.py
```

Exits 0 when:
1. Every recorded file has a `run_id`.
2. Every `claim_id` in F020 has at least one record.
3. No record's `outcome` is `corroborated` without meeting the per-arm count target.

## C3 split

The recorder is written by the implementer (this experiment). The actual game runs
are performed by the main session on the install (the C3 lines). The implementer
processes the records into the F020 per-claim outcome table.

## Per-batch push order

1. F011 (combat) — this push
2. F013 (reinforcement)
3. F012 (turn/victory)
4. F014 (cards)
5. F015 (centres/hazards)
6. F016 (AI)
7. F018 (deal)
8. F019 (setup)
9. Q-TRN-05, Q-REI-05, Q-AI-07
