#!/usr/bin/env python3
"""Migrate E018's committed `e018-record/1` records into `run/1` documents (T28 R3, defect 1).

The R2 recorder wrote `e018-record/1` documents into runs/E018/combat/, and the
suite (tests/test_runs.py check_runs) requires every runs/**/*.json to validate
as schema `run/1` — CI on the branch was red exactly on that. This script
migrates the thirteen records in place, value-preserving (rule 20: measured
outputs are never silently altered):

* every original field's value survives verbatim — run_id, experiment, batch
  (as `arm`), question_id, claim_id, count_target, per_arm_counts,
  screenshot_path, screenshot_sha256, seal_ok, elapsed_seconds, outcome, status,
  extra — with the recorder's flat fields carried as observations through
  record_f011.e018_observation_fields() (the same mapping a fresh record uses;
  a non-string value is stringified, `null` as "null");
* the original bytes stay in git history, at the commit that added each record
  (named by runs/E018/CORRECTIONS.md); nothing is deleted, only rewritten in the
  working tree as the migrated document;
* the run/1 fields the original document never carried are pinned to their best
  evidence and say so: code_commit and started/ended name the commit that
  recorded the run (the original documents carried no timestamps; the commit is
  the only time evidence, and elapsed_seconds is preserved verbatim beside
  them); start_state.sha256 is the F019-pinned Islepro.exe hash of the artifact
  set the runs name — not a hash these runs measured, which the restore text
  and CORRECTIONS.md both state; the fingerprint is empty because the original
  documents recorded no versions.

Usage, from the repository root::

    python3 experiments/E018-pro-corroboration/migrate_to_run1.py           # write the migration
    python3 experiments/E018-pro-corroboration/migrate_to_run1.py --check   # re-derive and compare

`--check` re-derives every migrated document from git (the original bytes at
each record's adding commit) and exits 0 only when the committed files are
exactly that derivation — so the migration stays reproducible and any later
edit of a migrated record is caught.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "experiments" / "E018-pro-corroboration"))
import check_no_originals  # noqa: E402  (the F019 table reader, reused, not copied)
import record_f011        # noqa: E402  (e018_observation_fields, SCRIPT — the shared mapping)

COMBAT = ROOT / "runs" / "E018" / "combat"
MACHINE = "local"          # the original documents carried no machine id; the runs were the
                           # user's machine through the driver (IWP_MACHINE's default)


def git(args):
    done = subprocess.run(["git"] + args, cwd=ROOT, capture_output=True, check=True)
    return done.stdout.decode()


def adding_commit(path):
    """The newest commit that added `path` — where the original bytes of the record live."""
    return git(["log", "--diff-filter=A", "-n1", "--format=%H", "--", path]).strip()


def file_at(commit, path):
    return git(["show", f"{commit}:{path}"]).encode()


def pinned_binary_sha():
    """The F019-pinned Islepro.exe sha256 for the set+variant these records name.

    Read from the same table tools/check_no_originals.py's wine gate reads, so the
    migration can never pin a value the gate would refuse. SystemExit when the row
    is absent (fail closed, like the gate).
    """
    for row in check_no_originals.load_f019_table(ROOT):
        if (row["set"], row["variant"]) == (record_f011.driver_runner.spike.SET_ID,
                                            record_f011.driver_runner.VARIANT):
            return row["sha256"]
    raise SystemExit("the F019 known-good table has no row for the set+variant these "
                     "records name; nothing was migrated")


def migrated_document(path, binary_sha):
    """One run/1 document, derived from the original bytes at the record's adding commit."""
    rel = path.relative_to(ROOT).as_posix()
    commit = adding_commit(rel)
    original = json.loads(file_at(commit, rel))
    stamp = git(["show", "-s", "--format=%cI", commit]).strip()
    short = git(["show", "-s", "--format=%h", commit]).strip()
    script_sha = hashlib.sha256(file_at(commit, record_f011.SCRIPT)).hexdigest()
    return {
        "schema": "run/1",
        "run_id": original["run_id"],
        "experiment": original["experiment"],
        "arm": original["batch"],
        "rep": int(original["run_id"].split("-r")[1]),
        "code_commit": short,
        "machine": MACHINE,
        "artifact": {"set": record_f011.driver_runner.spike.SET_ID,
                     "variant": record_f011.driver_runner.VARIANT},
        "runtime": {
            "driver": f"{record_f011.SCRIPT}@{short}",
            "platform": record_f011.driver_runner.PLATFORM,
            "fingerprint": {},
        },
        "interventions": [{"level": "I1", "what":
                           "the driver's cycle seal (read-only install bind, prefix baseline "
                           "checks) and read-only /proc reads; no game input was sent and no "
                           "screenshot was kept in this attempt (the session aborted)"}],
        "start_state": {"id": "S-cold-prefix-title", "sha256": binary_sha,
                        "restore": "attempted launch from the sealed prefix through the T13 "
                                   "driver (the e018-record/1 document this migrates carried no "
                                   "start state); start_state.sha256 is the F019-pinned "
                                   "Islepro.exe hash of the artifact set named above, not a hash "
                                   "this run measured — see runs/E018/CORRECTIONS.md"},
        "seed": None,
        "actions": {"script": record_f011.SCRIPT, "sha256": script_sha,
                    "args": [original["question_id"]]},
        "observations": record_f011.e018_observation_fields(original),
        "outputs": [],
        "started": stamp,
        "ended": stamp,
        "status": original["status"],
    }


def records():
    return sorted(COMBAT.glob("E018-r*.json"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true",
                        help="re-derive every migrated document and compare with what is "
                             "committed; exit 1 on any difference")
    args = parser.parse_args(argv)
    binary_sha = pinned_binary_sha()
    differences = []
    for path in records():
        doc = migrated_document(path, binary_sha)
        text = json.dumps(doc, indent=2) + "\n"
        if args.check:
            if path.read_text(encoding="utf-8") != text:
                differences.append(path.name)
        else:
            path.write_text(text, encoding="utf-8")
            print(f"migrated {path.name} (original bytes at {adding_commit(path.relative_to(ROOT).as_posix())[:12]})")
    if args.check:
        if differences:
            print("NOT the derivation of the originals: " + ", ".join(differences), file=sys.stderr)
            return 1
        print(f"all {len(records())} combat records are exactly the migration of their originals")
    return 0


if __name__ == "__main__":
    sys.exit(main())
