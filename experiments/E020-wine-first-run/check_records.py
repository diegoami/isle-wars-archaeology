#!/usr/bin/env python3
"""The E020 batch checker of Done-when 3, 4 and 6 (T38).

It checks the committed records (`runs/E020/**/*.json`) and manifests
(`evidence/E020/*.manifest.json`) the way the Done-when commands do, in one run:

  * every record is a valid `run/1` document (formats/run-1.schema.json);
  * every record's `runtime.platform` is exactly `wine-on-user-machine-iwp-2.0` (constraint C);
  * every record passes constraint F's gate against the F019 known-good table
    (tools/check_no_originals.check_wine_gate);
  * every observation `field` is a structural `kind:role` name of lowercase letters and hyphens
    (Done-when 4), and every observation carries `step` and `source` and then a `field`+`value`,
    `addr`+`value` or `ref` (formats/run-1.schema.json's anyOf);
  * every manifest is valid and every `files[].class` is `recording` (Done-when 3).

Usage: `python3 experiments/E020-wine-first-run/check_records.py [runs-dir] [evidence-dir]`,
defaulting to runs/E020 and evidence/E020. Exit 0 when every check holds.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_no_originals  # noqa: E402
import validate_records  # noqa: E402
import validate_wine_manifests  # noqa: E402

PLATFORM = "wine-on-user-machine-iwp-2.0"
FIELD = re.compile(r"^[a-z][a-z-]*:[a-z][a-z-]*$")


def check_record(path, table):
    """The check lines for one record file; [] when it passes every rule."""
    problems = []
    try:
        doc = validate_records.load_file(path)
    except (OSError, ValueError) as exc:
        return [f"{path}: {exc}"]
    if not isinstance(doc, dict):
        return [f"{path}: the document is not a JSON object"]
    for error in validate_records.validate_document(doc):
        problems.append(f"{path}: {error}")
    if doc.get("runtime", {}).get("platform") != PLATFORM:
        problems.append(f"{path}: runtime.platform is {doc.get('runtime', {}).get('platform')!r}, "
                        f"not {PLATFORM!r} (constraint C)")
    for i, obs in enumerate(doc.get("observations", [])):
        field = obs.get("field") if isinstance(obs, dict) else None
        if field is not None and not FIELD.fullmatch(str(field)):
            problems.append(f"{path}: observations[{i}].field {field!r} is not a structural kind:role name")
    problem, _warning = check_no_originals.check_wine_gate(doc, table)
    if problem:
        problems.append(f"{path}: {problem}")
    return problems


def check_manifest(path):
    try:
        doc = validate_records.load_file(path)
    except (OSError, ValueError) as exc:
        return [f"{path}: {exc}"]
    return [f"{path}: {error}" for error in validate_wine_manifests.errors_for(doc)]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    runs = Path(argv[0]) if argv else ROOT / "runs" / "E020"
    evidence = Path(argv[1]) if len(argv) > 1 else ROOT / "evidence" / "E020"
    table = check_no_originals.load_f019_table(ROOT)
    problems = []
    records = sorted(p for p in runs.rglob("*.json") if p.is_file())
    manifests = sorted(evidence.glob("*.manifest.json")) if evidence.is_dir() else []
    for path in records:
        if path.name == "outcome.json":
            continue
        problems += check_record(path, table)
    for path in manifests:
        problems += check_manifest(path)
    print(f"checked {len(records)} record(s), {len(manifests)} manifest(s)")
    for problem in problems:
        print(f"FAIL {problem}")
    if problems:
        return 1
    print("records and manifests ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
