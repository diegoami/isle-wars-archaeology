#!/usr/bin/env python3
"""Exact outcome probabilities of one human attack, computed from the rule F011 reads (a model, not a measurement).

The rule as read (F011, Q-CMB-04 to Q-CMB-09): each exchange both sides draw one die, 1 to 6, assumed uniform
and independent (the generator is Director's own, T18; its distribution is not claimed). The attacker wins the
exchange only when its die is strictly higher (15 of 36); the defender wins it otherwise, ties included (21 of 36).
The loser of an exchange loses one army. The human attack ends in a capture when the defender reaches 0, or in a
failure when the attacker is down to 1 army (it then forfeits the country). The human may also stop earlier by
pressing the quit-attack button; that is not modelled. The five-exchange batch for big stacks does not change the
outcome of the sequence, only where the player can stop, so it is not modelled either.

Writes the table to measurements/win-probability-<run>.json (a new file; never overwrites). Needs no original.
Usage: win_probability.py [run-id]   (default r1)
"""
import json
import sys
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

P_ATT = Fraction(15, 36)  # attacker's die strictly higher
P_DEF = Fraction(21, 36)  # defender's die higher or equal

sys.setrecursionlimit(10000)


@lru_cache(maxsize=None)
def outcome(a, d):
    """(P capture, E attacker armies lost, E defender armies lost) from attacker a, defender d, human rule."""
    if d <= 0:
        return (Fraction(1), Fraction(0), Fraction(0))
    if a <= 1:
        return (Fraction(0), Fraction(0), Fraction(0))
    pw, la, ld = outcome(a, d - 1)  # attacker wins the exchange: defender loses one
    pl, lb, le = outcome(a - 1, d)  # defender wins the exchange: attacker loses one
    cap = P_ATT * pw + P_DEF * pl
    e_att = P_ATT * la + P_DEF * (1 + lb)
    e_def = P_ATT * (1 + ld) + P_DEF * le
    return (cap, e_att, e_def)


def main():
    run = sys.argv[1] if len(sys.argv) > 1 else "r1"
    out = Path(__file__).resolve().parent / "measurements" / ("win-probability-%s.json" % run)
    if out.exists():
        print("refusing to overwrite", out.name)
        return 1
    attackers = [2, 3, 4, 5, 6, 8, 10, 15, 20]
    defenders = [1, 2, 3, 4, 5, 8, 10, 15, 20]
    rows = []
    for a in attackers:
        for d in defenders:
            cap, ea, ed = outcome(a, d)
            rows.append({
                "attacker_armies": a, "defender_armies": d,
                "p_capture": round(float(cap), 6),
                "e_attacker_losses": round(float(ea), 4),
                "e_defender_losses": round(float(ed), 4),
                "allowed_by_human_check": a >= d and a >= 2,
            })
    rec = {
        "what": "model of one human attack from the rule read in F011, uniform independent dice assumed; not observed",
        "per_exchange": {"attacker_wins": "15/36", "defender_wins_including_ties": "21/36"},
        "end_of_attack": "capture when the defender reaches 0; failure when the attacker is down to 1 army",
        "rows": rows,
    }
    out.write_text(json.dumps(rec, indent=1) + "\n")
    print("wrote", out.name, len(rows), "rows")
    for r in rows:
        if r["attacker_armies"] == r["defender_armies"] or (r["attacker_armies"], r["defender_armies"]) in {(5, 2), (10, 5), (3, 1)}:
            print(r["attacker_armies"], r["defender_armies"], r["p_capture"],
                  r["e_attacker_losses"], r["e_defender_losses"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
