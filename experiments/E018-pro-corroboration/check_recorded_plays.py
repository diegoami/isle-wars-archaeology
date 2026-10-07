#!/usr/bin/env python3
"""check_recorded_plays.py: validate E018 records for F011.

Exit 0 when:
1. Every recorded file in runs/E018/*/ has a run_id.
2. Every claim_id in findings/F020-pro-corroboration.md has at least one record.
3. No record's outcome is 'corroborated' without meeting the per-arm count target.

Run from the repository root::

    python3 experiments/E018-pro-corroboration/check_recorded_plays.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs" / "E018"
FINDING = ROOT / "findings" / "F020-pro-corroboration.md"

# Per-question count targets from F011's T28 plan
COUNT_TARGETS = {
    "Q-CMB-01": 16,    # 16 attacker/target combos, deterministic, once each
    "Q-CMB-02": 4,     # 4 boundary cases (N=4,8,12,20), once each
    "Q-CMB-03": 3,     # 3 cases (attacker 1,2,3 vs defender 1)
    "Q-CMB-04": 500,   # 100 per attacker size x 5 sizes
    "Q-CMB-05": 500,   # 100 per defender size x 5 sizes
    "Q-CMB-06": 500,   # 500 exchanges total
    "Q-CMB-07": 200,   # 200 exchanges
    "Q-CMB-08": 10,    # 10 human attacks
    "Q-CMB-09": 5,     # 5 failed attacks
    "Q-CMB-10": 10,    # 10 turns with 3+ attacks
    "Q-CMB-11": 500,   # 500 exchanges split by condition
    "Q-CMB-12": 100,   # 100 attacks per ratio band + 20 games
    "Q-MOV-01": 10,    # 10 human turns with move
    "Q-MOV-02": 6,     # stacks 2,3,10 x 2 tries each
    "Q-MOV-03": 10,    # 10 turns with second move/attack
    "Q-OWN-01": 12,    # 4 stack sizes x 3+ each
    "Q-SET-04": 1,     # one visit
}


def load_records():
    """Load all E018 records from runs/E018/*/. Returns dict claim_id -> list of records."""
    records = {}
    if not RUNS.is_dir():
        print(f"ERROR: runs/E018/ not found", file=sys.stderr)
        return records
    for batch_dir in RUNS.iterdir():
        if not batch_dir.is_dir():
            continue
        for record_file in batch_dir.glob("*.json"):
            try:
                with open(record_file) as f:
                    rec = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"ERROR: could not read {record_file}: {e}", file=sys.stderr)
                continue
            run_id = rec.get("run_id")
            if not run_id:
                print(f"ERROR: {record_file} has no run_id", file=sys.stderr)
                continue
            claim_id = rec.get("claim_id")
            if not claim_id:
                print(f"ERROR: {record_file} has no claim_id", file=sys.stderr)
                continue
            records.setdefault(claim_id, []).append(rec)
    return records


def get_claim_ids_from_finding():
    """Extract claim_ids from F020-pro-corroboration.md."""
    claim_ids = set()
    if not FINDING.is_file():
        print(f"WARNING: {FINDING} not found; cannot check claim coverage", file=sys.stderr)
        return claim_ids
    text = FINDING.read_text()
    # Match C-CMB-*, C-MOV-*, C-OWN-*, C-SET-* patterns
    for m in re.finditer(r'\b(C-[A-Z]+-\d+)\b', text):
        claim_ids.add(m.group(1))
    return claim_ids


def check_record_coverage(records):
    """Check 1: every record has a run_id (already done in load_records)."""
    errors = []
    total = sum(len(recs) for recs in records.values())
    print(f"CHECK 1: records loaded: {total} records across {len(records)} claim_ids")
    if total == 0:
        errors.append("No records found in runs/E018/")
    return errors


def check_claim_coverage(records):
    """Check 2: every claim_id in F020 has at least one record."""
    errors = []
    claim_ids = get_claim_ids_from_finding()
    print(f"CHECK 2: claim_ids in F020: {sorted(claim_ids)}")
    for cid in sorted(claim_ids):
        if cid not in records:
            errors.append(f"ERROR: {cid} has no record in runs/E018/")
        else:
            print(f"  {cid}: {len(records[cid])} record(s)")
    return errors


def check_corroborated_outcomes(records):
    """Check 3: no 'corroborated' without meeting the per-arm count target."""
    errors = []
    for claim_id, recs in sorted(records.items()):
        # Extract question id from claim_id (e.g. C-CMB-04 -> Q-CMB-04)
        parts = claim_id.split("-")
        if len(parts) >= 2:
            qid = parts[0] + "-" + parts[1]  # e.g. "C-CMB"
            qid = qid.replace("C-", "Q-")
        else:
            qid = claim_id
        target = COUNT_TARGETS.get(qid, 0)
        for rec in recs:
            outcome = rec.get("outcome")
            if outcome == "corroborated":
                per_arm = rec.get("per_arm_counts", {})
                total = sum(v for v in per_arm.values() if isinstance(v, (int, float)))
                if total < target:
                    errors.append(
                        f"ERROR: {claim_id} record {rec.get('run_id')} is 'corroborated' "
                        f"but total {total} < target {target}"
                    )
    if not errors:
        print(f"CHECK 3: no 'corroborated' without per-arm count target violations")
    return errors


def main():
    print("=== E018 F011 record validation ===\n")
    records = load_records()
    all_errors = []
    all_errors.extend(check_record_coverage(records))
    all_errors.extend(check_claim_coverage(records))
    all_errors.extend(check_corroborated_outcomes(records))

    if all_errors:
        print("\nERRORS:")
        for e in all_errors:
            print(f"  {e}")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
