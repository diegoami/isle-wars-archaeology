#!/usr/bin/env python3
"""E020's sitting launcher and batch dispatcher (T38, rule 18 carve-out).

This is the one command T37's brief sketched: it resolves a batch from
`experiments/E020-wine-first-run/scenarios.txt`, refuses any batch that is not one the "Why a run
is made" section names (constraint B), and then — for a real dispatch — launches the session
through the E004 machinery (`runtime/iwp/driver/session.py`), attaches the watcher
(`runtime/iwp/driver/watcher.py`), drives the click-driver (`runtime/iwp/driver/clicks.py`), and
emits the per-sitting directory on the user's machine (constraint A):

    `<sitting-root>/<YYYYMMDDTHHMMSSZ>/{sitting.json, frames/, frames-index.jsonl,
      actions.jsonl, dumps/, watcher.log}`

Subcommands:
  `--batch NAME --help`       print NAME's targets and exit 0; never starts wine (Done-when 2)
  `--batch NAME`              run the sitting (the real dispatch; the main session runs it)
  `--records --sitting DIR --batch NAME`
                              turn a completed sitting's readings into the committed run record and
                              evidence manifest (rule 20; a re-read writes beside, never over)

It is reached through `tools/wine-driver.sh`, the path Done-when 2 names.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "runtime" / "iwp"))
sys.path.insert(0, str(ROOT / "setup" / "iwp"))

import check_no_originals  # noqa: E402
import check_counts  # noqa: E402

EXPERIMENT = "E020"
PLATFORM = "wine-on-user-machine-iwp-2.0"
SET_ID = "iwp-2.0-996e86c5"
VARIANT = "unregistered"
SITTING_ROOT = Path("/mnt/c/Temp/iwp-shots/wine")
SCENARIOS = Path(__file__).resolve().with_name("scenarios.txt")
USAGE = "usage: wine-driver.sh --batch <name> [--help] | --records --sitting <dir> --batch <name>"


def batches():
    return check_counts.load_batches(SCENARIOS)


def value_of(argv, flag):
    for i, item in enumerate(argv):
        if item == flag and i + 1 < len(argv):
            return argv[i + 1]
        if item.startswith(flag + "="):
            return item.split("=", 1)[1]
    return None


def f019_row():
    """The F019 known-good row this dispatch runs under (rule 17: read, never re-typed)."""
    for row in check_no_originals.load_f019_table(ROOT):
        if row.get("set") == SET_ID and row.get("variant") == VARIANT:
            return row
    raise SystemExit(f"the F019 known-good row for {SET_ID}/{VARIANT} is missing; nothing was started")


def batch_help(name, batch):
    """The batch's targets, printed by `--batch NAME --help`; never starts wine."""
    steps = Path(__file__).resolve().with_name(batch.get("steps", ""))
    lines = [
        f"batch {name} (platform {PLATFORM})",
        f"  questions: {batch.get('questions', '')}",
        f"  source: {batch.get('source', '')}",
    ]
    if "exchanges_field" in batch:
        lines.append(f"  target: at least {batch['exchanges_min']} exchanges in the first sitting "
                     f"(each exchange: {batch['exchanges_field']} with before/after counters for both sides)")
        lines.append(f"  corroboration: walkthroughs/f011-questions.md counts across sittings "
                     f"(at least {batch.get('corroborate_min', batch['exchanges_min'])} exchanges to claim corroborated)")
    if "bomb_plays_field" in batch:
        lines.append(f"  target: at least {batch['bomb_plays_min']} computer bomb plays across at "
                     f"least {batch['games_min']} games")
    lines += [
        f"  vocabulary: {batch.get('vocabulary', '')}",
        f"  note: {batch.get('note', '')}",
        f"  steps: {steps.relative_to(ROOT).as_posix() if steps.is_file() else batch.get('steps', '')}",
        f"  records land in runs/{EXPERIMENT}/{name}/; bundles are release {EXPERIMENT} assets",
    ]
    return "\n".join(lines)


# --- pure sitting layout helpers (tested without wine) ---------------------------------------

def sitting_id(epoch=None):
    """The sitting id: UTC `YYYYMMDDTHHMMSSZ` (the layout's wall-time name)."""
    import time
    epoch = time.time() if epoch is None else epoch
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(epoch))


def sitting_paths(root, sid):
    """Every path of one sitting directory (see the module text)."""
    sitting = Path(root) / sid
    return {
        "root": sitting,
        "frames": sitting / "frames",
        "dumps": sitting / "dumps",
        "index": sitting / "frames-index.jsonl",
        "actions": sitting / "actions.jsonl",
        "log": sitting / "watcher.log",
        "sitting_json": sitting / "sitting.json",
        "readings": sitting / "readings.jsonl",
    }


def prepare_sitting(paths):
    for key in ("root", "frames", "dumps"):
        paths[key].mkdir(parents=True, exist_ok=True)


def write_sitting_json(paths, batch, versions, commit, started, ended):
    import json
    doc = {
        "sitting_id": paths["root"].name,
        "batch": batch,
        "platform": PLATFORM,
        "wine": versions.get("wine", "unknown"),
        "xvfb": versions.get("xvfb", "unknown"),
        "xfwm4": versions.get("xfwm4", "unknown"),
        "driver_commit": commit,
        "started": started,
        "ended": ended,
    }
    paths["sitting_json"].write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc


# --- records and manifests (rule 20; tested with synthetic readings) -------------------------

def read_readings(path):
    """The sitting's structural readings: one JSON object per line (field, value, step, source)."""
    import json
    path = Path(path)
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        doc = json.loads(line)
        if isinstance(doc, dict):
            out.append(doc)
    return out


def record_observations(paths, vocabulary):
    """Frame refs and reading values as run/1 observations; refuse a field outside the vocabulary.

    Frames enter as `{step, source: screen, ref: sha256:<digest>}` (the bundle holds them by hash);
    a reading enters as `{step, source, field, value}` when its `field` is in the batch's documented
    vocabulary. The original's text never enters a reading: a value is a raw integer or a colour
    word, and a field is a structural `kind:role` name (constraint D, Done-when 4)."""
    import json
    observations = []
    index = Path(paths["index"])
    if index.is_file():
        for line in index.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            frame = json.loads(line)
            observations.append({"step": 0, "source": "screen", "ref": f"sha256:{frame['sha256']}"})
    known = set(vocabulary.split())
    for reading in read_readings(paths["readings"]):
        field = reading.get("field")
        if field not in known:
            raise SystemExit(f"reading field {field!r} is not in the batch vocabulary {sorted(known)}; "
                             "the record is not written")
        observations.append({"step": int(reading.get("step", 0)),
                             "source": reading.get("source", "screen"),
                             "field": field,
                             "value": str(reading.get("value", ""))})
    return observations


def build_record(run_id, batch, commit, machine, fingerprint, driver_sha, started, ended, status,
                 observations, args):
    return {
        "schema": "run/1",
        "run_id": run_id,
        "experiment": EXPERIMENT,
        "arm": batch,
        "rep": 1,
        "code_commit": commit,
        "machine": machine,
        "artifact": {"set": SET_ID, "variant": VARIANT},
        "runtime": {
            "driver": f"experiments/{EXPERIMENT}-wine-first-run/launcher.py@{commit}",
            "platform": PLATFORM,
            "fingerprint": {k: str(v) for k, v in fingerprint.items() if "/" not in str(v) and "\\" not in str(v)},
        },
        "interventions": [{"level": "I0", "what": "none"}],
        "start_state": {
            "id": "S-iwp-prefix-sync",
            "sha256": f019_row()["sha256"],
            "restore": "fresh prefix sync from the F019 install, no save",
        },
        "seed": None,
        "actions": {"script": f"experiments/{EXPERIMENT}-wine-first-run/launcher.py",
                    "sha256": driver_sha, "args": list(args)},
        "observations": observations,
        "outputs": [],
        "started": started,
        "ended": ended,
        "status": status,
    }


def build_manifest(run_id, files):
    """An evidence-manifest/1 whose every file is class `recording` (constraint C, Done-when 3)."""
    from driver.watcher import sha256_file
    out = []
    for path in files:
        path = Path(path)
        digest = sha256_file(path)
        out.append({"name": path.name, "bytes": path.stat().st_size, "sha256": digest,
                    "asset": f"{digest[:16]}-{path.name}", "class": "recording"})
    return {"schema": "evidence-manifest/1", "run_id": run_id, "experiment": EXPERIMENT,
            "store": f"release:{EXPERIMENT}", "artifact": {"set": SET_ID, "variant": VARIANT},
            "files": out}


# --- the dispatcher --------------------------------------------------------------------------

def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    name = value_of(argv, "--batch")
    if "--help" in argv or "-h" in argv:
        if name is None:
            print(USAGE)
            print("batches: " + ", ".join(sorted(batches())))
            return 0
        known = batches()
        if name not in known:
            print(f"unknown batch {name!r}: the batch list names {sorted(known)}; nothing was started",
                  file=sys.stderr)
            return 2
        print(batch_help(name, known[name]))
        return 0
    if "--records" in argv:
        return records_main(argv)
    if name is None:
        print(USAGE, file=sys.stderr)
        return 2
    known = batches()
    if name not in known:
        print(f"unknown batch {name!r}: the batch list names {sorted(known)}; nothing was started",
              file=sys.stderr)
        return 2
    return run_sitting(name, known[name], argv)


def run_sitting(name, batch, argv):
    """The real dispatch: launch through E004, attach the watcher and the click-driver.

    It is only run on the user's machine, after the owner's go-ahead, by the main session. It
    never runs in CI or in a worktree build."""
    import os
    import time
    from argparse import Namespace
    from driver import session as sessionlib
    from driver.clicks import ClickDriver
    from driver.watcher import Watcher, wall_time

    roots = {}
    for key in ("IWP_DIR", "IWP_PREFIX", f"{EXPERIMENT}_BUNDLES"):
        if not os.environ.get(key):
            raise SystemExit(f"{key} is not set; the sitting needs the confined locations "
                             "(setup/iwp/locations.py); nothing was started")
        roots[key] = os.environ[key]
    sessionlib.spike.confined_locations(Namespace(explore=False, experiment=EXPERIMENT))

    root = Path(value_of(argv, "--sitting-root") or SITTING_ROOT)
    sid = sitting_id()
    paths = sitting_paths(root, sid)
    prepare_sitting(paths)
    started = wall_time()
    commit = sessionlib.spike.must(["git", "rev-parse", "--short=12", "HEAD"], cwd=ROOT).stdout.decode().strip()
    machine = os.environ.get("IWP_MACHINE", "local")
    run_id = next_run_id(name)

    steps_text = Path(__file__).resolve().with_name(batch["steps"]).read_text(encoding="utf-8")
    last_step = {"step": 0}
    session = sessionlib.Session(run_id, roots["IWP_PREFIX"], roots[f"{EXPERIMENT}_BUNDLES"],
                                 roots["IWP_DIR"], sessionlib.free_display(), arm=name)

    def body(active):
        active.expect("title")
        active.known_screen()
        window = game_window_id(active.procs["game"].pid)
        watcher = Watcher(window, paths["frames"], paths["index"], paths["log"],
                          lambda: last_step["step"])
        thread, stop = watcher.start()
        active.observe_screenshot("before.png")
        try:
            driver = ClickDriver(actions_path=paths["actions"],
                                 on_action=lambda step: last_step.__setitem__("step", step.line))
            driver.execute(steps_text)
        finally:
            stop.set()
            thread.join(timeout=30)
        active.observe_screenshot("after.png")
        active.observe(active.step_no, "process", "record:role", "click-driver steps completed")

    try:
        session.execute(body)
    finally:
        write_sitting_json(paths, name, sessionlib.spike.versions(), commit, started, wall_time())
    print(f"sitting {sid} -> {paths['root']} ({session.status})")
    return 0 if session.status == "completed" else 1


def game_window_id(pid):
    """The game's own window on this run's display, by pid (never by the title's text)."""
    from driver.session import spike
    done = spike.must(["xdotool", "search", "--pid", str(pid)])
    ids = done.stdout.split()
    if not ids:
        raise SystemExit("the game window was not found by its pid; the sitting stops")
    return ids[-1].decode()


def next_run_id(batch, runs_root=None):
    """The next E020-rNNNN id in runs/E020/<batch>/: a re-read writes beside, never over (rule 20)."""
    import re
    folder = Path(runs_root) if runs_root else ROOT / "runs" / EXPERIMENT / batch
    numbers = [int(m.group(1)) for p in folder.glob(f"{EXPERIMENT}-r*.json")
               if (m := re.match(rf"{EXPERIMENT}-r(\d+)\.json$", p.name))]
    return f"{EXPERIMENT}-r{(max(numbers) if numbers else 0) + 1:04d}"


def records_main(argv):
    """Build the committed record and manifest from a completed sitting's readings (rule 20)."""
    import json
    from driver.session import spike
    from driver.watcher import sha256_file, wall_time

    sitting = value_of(argv, "--sitting")
    name = value_of(argv, "--batch")
    if not sitting or not name:
        print("--records needs --sitting and --batch", file=sys.stderr)
        return 2
    known = batches()
    if name not in known:
        print(f"unknown batch {name!r}; nothing was written", file=sys.stderr)
        return 2
    paths = sitting_paths(Path(sitting).parent, Path(sitting).name)
    if not paths["root"].is_dir():
        print(f"no sitting directory at {paths['root']}; nothing was written", file=sys.stderr)
        return 2
    commit = spike.must(["git", "rev-parse", "--short=12", "HEAD"], cwd=ROOT).stdout.decode().strip()
    run_id = next_run_id(name)
    observations = record_observations(paths, known[name].get("vocabulary", ""))
    frames = sorted(paths["frames"].glob("*.png"))
    record = build_record(run_id, name, commit, __import__("os").environ.get("IWP_MACHINE", "local"),
                          spike.versions(), sha256_file(Path(__file__)), wall_time(), wall_time(),
                          "completed", observations, [run_id])
    record["outputs"] = [{"name": p.name, "sha256": sha256_file(p), "store": f"release:{EXPERIMENT}"}
                         for p in frames]
    manifest = build_manifest(run_id, frames)
    runs_dir = ROOT / "runs" / EXPERIMENT / name
    evidence_dir = ROOT / "evidence" / EXPERIMENT
    runs_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    record_path = runs_dir / f"{run_id}.json"
    manifest_path = evidence_dir / f"{run_id}.manifest.json"
    for path in (record_path, manifest_path):
        if path.exists():
            print(f"no record written: {path} exists; records are never overwritten", file=sys.stderr)
            return 1
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {record_path.relative_to(ROOT).as_posix()} and "
          f"{manifest_path.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
