#!/usr/bin/env python3
"""One-off correction of the evidence manifests of E005-r0001 to r0026.

The cycle wrote `"class": "file"` for the game-written files it kept (`s<NN>-<NAME>`, `end-<NAME>`), a class
that evidence-manifest/1 does not allow (`save`, `screenshot`, `recording`, `memory-dump`, `trace`, `log`,
`measurement`). tests/test_runs.py (CI) rejects such a manifest. The cycle is fixed (a `.SAV` file is `save`,
any other game-written file is `measurement`, tests/test_iw_dos_steps.py). This script gives the 26 manifests
already written the class the fixed cycle gives, and changes nothing else: names, sizes, sha256 and assets are
untouched, and no run record changes (a record holds no class). Idempotent. Usage: fix-manifest-classes.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
changed = 0
for path in sorted((ROOT / "evidence" / "E005").glob("E005-r*.manifest.json")):
    doc = json.loads(path.read_text())
    edited = False
    for entry in doc["files"]:
        if entry["class"] == "file":
            entry["class"] = "save" if entry["name"].upper().endswith(".SAV") else "measurement"
            edited = True
    if edited:
        path.write_text(json.dumps(doc, indent=2) + "\n")
        changed += 1
print(f"{changed} manifest(s) corrected")
