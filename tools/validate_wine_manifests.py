#!/usr/bin/env python3
"""Validate model-driven evidence manifests (constraint C of the rule 18 carve-out, T38).

Each file is validated against formats/evidence-manifest-1.schema.json, and then every
`files[].class` must be `recording` and never `screenshot` of a human session. That distinction is
constraint C: per-frame evidence from a model-driven sitting under Wine is a `recording` (T38's
Done-when 3), while `screenshot` is what the owner's own captures are. Without this check a
manifest could pass as the owner's, which is the bypass the guard exists to stop.

This is the wine-manifest sibling of tools/validate_records.py; it imports that module's validator,
so the schema rules and the format lookup are the same one place.

Usage: `python3 tools/validate_wine_manifests.py <file.json>...`, usually fed by
`find evidence/E020 -name '*.manifest.json' -print0 | xargs -0 -r ...`. Prints `ok: <path>` per
valid file and one line per error otherwise. Exit 0 when every file is valid, 1 otherwise, 2 on a
usage error.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_records import load_file, validate_document  # noqa: E402

WINE_CLASS = "recording"
MANIFEST_SCHEMA = "evidence-manifest/1"


def errors_for(doc):
    """Errors for one parsed manifest; [] when it is a valid wine manifest (constraint C).

    The manifest schema is required explicitly (T38 round 2, R5): `validate_document` validates a
    document against the schema the document itself declares, so a valid `run/1` (or any other
    format) under a `*.manifest.json` name would pass it. A document that does not declare
    `evidence-manifest/1` is refused before anything else, and `files` must be present."""
    if not isinstance(doc, dict) or doc.get("schema") != MANIFEST_SCHEMA:
        declared = doc.get("schema") if isinstance(doc, dict) else type(doc).__name__
        return [f"$.schema: {declared!r} is not {MANIFEST_SCHEMA!r}; only an evidence manifest is a wine manifest"]
    errors = validate_document(doc)
    if errors:
        return errors
    if not isinstance(doc.get("files"), list) or not doc["files"]:
        return ["$.files: an evidence manifest lists at least one file"]
    out = []
    for i, entry in enumerate(doc["files"]):
        if entry.get("class") != WINE_CLASS:
            out.append(f"$.files[{i}].class: {entry.get('class')!r} is not {WINE_CLASS!r}; a "
                       f"model-driven frame is a recording, never a screenshot of a human session "
                       f"(constraint C)")
    return out


def validate_file(path):
    """Print the result for one file; True when it is a valid wine manifest. Never raises."""
    try:
        doc = load_file(path)
    except (OSError, ValueError) as exc:
        print(f"{path}: {exc}")
        return False
    errors = errors_for(doc)
    if errors:
        for error in errors:
            print(f"{path}: {error}")
        return False
    print(f"ok: {path}")
    return True


def main(argv=None):
    paths = sys.argv[1:] if argv is None else list(argv)
    if not paths:
        print("usage: validate_wine_manifests.py <file.json>...")
        return 2
    valid = True
    for path in paths:
        try:
            ok = validate_file(path)
        except Exception as exc:  # noqa: BLE001 - one file never stops the batch
            print(f"{path}: internal error on malformed input: {type(exc).__name__}: {exc}")
            ok = False
        if not ok:
            valid = False
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
