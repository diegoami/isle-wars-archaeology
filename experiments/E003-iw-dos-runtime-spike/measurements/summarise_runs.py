#!/usr/bin/env python3
"""summarise_runs.py [first] [last]: print the observations of runs/E003 records as one block per
run (field: value), read from the records only. Its output is records-runs-<range>.txt here."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
first = int(sys.argv[1]) if len(sys.argv) > 1 else 1
last = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 6
for path in sorted((ROOT / "runs" / "E003").glob("E003-r*.json")):
    number = int(path.stem.split("-r")[1])
    if not first <= number <= last:
        continue
    record = json.loads(path.read_text())
    print(f"== {record['run_id']} arm={record['arm']} rep={record['rep']} status={record['status']}")
    print(f"   commit {record['code_commit']}; args {record['actions']['args']}; "
          f"interventions {[i['level'] + ': ' + i['what'] for i in record['interventions']]}")
    print(f"   start_state {record['start_state']['id']} {record['start_state']['sha256']}")
    print(f"   started {record['started']} ended {record['ended']}")
    for obs in record["observations"]:
        print(f"   [{obs['step']}] {obs['source']}: {obs.get('field', obs.get('addr', ''))}: {obs.get('value', obs.get('ref'))}")
    for out in record["outputs"]:
        print(f"   output {out['name']} {out['sha256']}")
