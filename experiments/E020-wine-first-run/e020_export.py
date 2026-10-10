"""E020's export: one sitting directory to one run record and one evidence manifest (T38; rule 20,
raw and immutable; T38 round 2, R3, R6, R7).

`export(sitting_dir, batch_name, ...)` writes `runs/E020/<batch>/<run-id>.json` and
`evidence/E020/<run-id>.manifest.json`, or nothing at all. What it requires, and never supplies:

* the sitting directory is a direct child of the one sitting root (e020_sitting.confine_root) and is
  named by a sitting id;
* `sitting.json` is the proof of the sitting: its batch, the session's own status (an aborted
  sitting is exported `aborted: ...`, never `completed`), the session's start and end times, the
  versions, the commit that ran, the block file's sha256 and the measured binary identity, which
  becomes `start_state.sha256` only when it is the F019 row's (the export re-reads the table);
* every frame of `frames-index.jsonl` exists and has the sha256 the index says;
* `readings.jsonl` (the reading pass's output, optional: a sitting with no reading yet is exported
  with no event) holds one event per line, `{"kind": k, "game": n, "seq": n, "frames": [sha256, ...],
  "values": {field: value}}`, whose kind is the batch's event (`exchange`, `bomb`: one event,
  written with `event:seq`) or `net` (T40 round 2, R1: the net of one or more of them between two
  frames, written with `net:seq`, which tools/check_counts.py never counts as an event), whose game is one the click-driver started (`actions.jsonl`), whose
  (game, seq) is unique, whose frames (at least two, distinct) are frames of the index, and whose
  values are exactly the batch's event fields, each valid for its role (tools/check_counts.py
  value_problem: integers and colour words only, so no text of the original reaches a record).

A sitting whose log has a `loss-credited` line followed by a `game-start` is refused (T41): the game
wrote the scoreboard file, so the games after it ran on the successor set, which F019 has no row for.
The one exception (fix #152, the owner, 2026-10-09): the driver puts the shipped `xtras/Islepro.skr`
back into the run copy before that game's New Game, so a game after a credit is exported on the
shipped set only when an `skr-restored` line naming that same game, carrying the shipped file's
sha256 (read from `artifacts/known.json`, never a constant), comes after the credit and before the
`game-start`. Anything else is refused, as it was. A record never names the shipped set for a game
played after a scoreboard write without that proof. A sitting whose credit came last (no game started
after it) names the shipped set, which every game of it ran on.

Run ids are experiment-wide (R7): the next one is one more than every `E020-rNNNN` under
`runs/E020/` (all batches) and `evidence/E020/`, and neither file is ever written over.
"""
import calendar
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _sub in ("setup/iwp", "tools"):
    if str(ROOT / _sub) not in sys.path:
        sys.path.insert(0, str(ROOT / _sub))
import check_counts  # noqa: E402
import check_no_originals  # noqa: E402
import safeio  # noqa: E402

import e020_sitting as sitting  # noqa: E402

EXPERIMENT = sitting.EXPERIMENT
RUN_ID = re.compile(rf"^{EXPERIMENT}-r(\d{{4,}})(?:\.manifest)?\.json$")
SHA = re.compile(r"^[0-9a-f]{64}$")
RESTORE = "fresh prefix sync from the F019 install, no save"
# vocabulary/interventions.md: screenshots are passive instrumentation, I1 (T40 round 2, R4). A
# sitting's frames are the watcher's screenshots of the display, so every record declares them.
INTERVENTIONS = [{"level": "I1", "what": "screenshots of the display (the watcher's frames of the Xvfb screen); "
                  "no memory read, no modified file"}]
SUCCESSOR_SET = "iwp-2.0-de5a82a2"    # artifacts/known.json: the shipped set with xtras/Islepro.skr declared a runtime write


class ExportRefused(SystemExit):
    """Nothing was written: the sitting directory is not what the export needs."""


def next_run_id(root=ROOT):
    """One more than every E020 run id under runs/E020 (every batch) and evidence/E020."""
    numbers = [0]
    for folder in (Path(root) / "runs" / EXPERIMENT, Path(root) / "evidence" / EXPERIMENT):
        if folder.is_dir():
            numbers += [int(m.group(1)) for p in folder.rglob(f"{EXPERIMENT}-r*.json")
                        if (m := RUN_ID.match(p.name))]
    return f"{EXPERIMENT}-r{max(numbers) + 1:04d}"


def jsonl(path):
    """The objects of a JSON-lines file; ExportRefused on a line that is not an object."""
    out = []
    if not Path(path).is_file():
        return out
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            doc = json.loads(line)
        except ValueError:
            doc = None
        if not isinstance(doc, dict):
            raise ExportRefused(f"{Path(path).name} line {number} is not a JSON object; nothing was written")
        out.append(doc)
    return out


def read_frames(paths):
    """{sha256: frame path} of the index, each frame checked against its sha256."""
    frames = {}
    for line in jsonl(paths["index"]):
        name, digest = line.get("name"), line.get("sha256")
        path = paths["frames"] / str(name)
        if not isinstance(name, str) or "/" in name or not SHA.fullmatch(str(digest)) or not path.is_file():
            raise ExportRefused(f"frames-index names a frame that is not there: {name!r}; nothing was written")
        if sitting.sha256_of(path) != digest:
            raise ExportRefused(f"the frame {name} does not have the sha256 its index line says; nothing was written")
        frames[digest] = path
    return frames


def games_started(paths):
    """The game ordinals the click-driver started (its `game-start` lines)."""
    return {line.get("game") for line in jsonl(paths["actions"]) if line.get("event") == "game-start"}


def games_after_loss(paths, shipped_skr):
    """The game ordinals started after a credit with no shipped restore of their own (T41; fix #152):
    a `loss-credited` line sets the credit and clears any earlier restore, an `skr-restored` line
    after it records one, and a `game-start` line after it is a game of the successor set unless the
    latest restore names that same game with `shipped_skr`'s sha256. A game-start with no ordinal of
    its own is never named by a restore either, so a line that carries no game proves nothing. The
    credit wrote the scoreboard file (xtras/Islepro.skr, F003), so without the restore those games
    ran on the successor set."""
    credited, restored, after = False, None, []
    for line in jsonl(paths["actions"]):
        event = line.get("event")
        if event == "loss-credited":
            credited, restored = True, None
        elif event == "skr-restored":
            restored = line
        elif credited and event == "game-start":
            game = line.get("game")
            proved = isinstance(game, int) and not isinstance(game, bool) and restored is not None \
                and restored.get("game") == game and restored.get("sha256") == shipped_skr
            if not proved:
                after.append(game)
    return after


def shipped_skr_sha256():
    """The shipped `xtras/Islepro.skr` sha256, read from this checkout's `artifacts/known.json`
    (rule 17: read, never re-typed); ExportRefused when the file does not say what it is."""
    try:
        return sitting.shipped_skr_sha256()
    except SystemExit as exc:
        raise ExportRefused(f"{exc}; nothing was written") from None


def events(paths, batch, frames, games):
    """The run/1 observations of the readings, one step per event; ExportRefused on any bad event."""
    fields = check_counts.event_fields(batch)
    observations, seen = [], set()
    for number, event in enumerate(jsonl(paths["readings"]), start=1):
        where = f"readings.jsonl line {number}"
        game, seq = event.get("game"), event.get("seq")
        if not isinstance(game, int) or isinstance(game, bool) or game not in games:
            raise ExportRefused(f"{where}: game {game!r} is not a game the click-driver started; nothing was written")
        if not isinstance(seq, int) or isinstance(seq, bool) or seq < 1 or (game, seq) in seen:
            raise ExportRefused(f"{where}: seq {seq!r} is not a new event ordinal of game {game}; nothing was written")
        kind = event.get("kind")
        if not isinstance(kind, str) or kind not in (batch.get("event"), "net"):
            raise ExportRefused(f"{where}: kind {kind!r} is neither the batch's event {batch.get('event')!r} nor "
                                "'net'; a reading says which it is; nothing was written")
        seen.add((game, seq))
        cited = event.get("frames")
        if not isinstance(cited, list) or len(set(map(str, cited))) < 2 or any(c not in frames for c in cited):
            raise ExportRefused(f"{where}: an event cites at least two distinct frames of the index; nothing was written")
        values = event.get("values")
        if not isinstance(values, dict) or sorted(values) != sorted(fields):
            raise ExportRefused(f"{where}: the values are exactly the batch's event fields {fields}; nothing was written")
        seq_field = check_counts.NET_SEQ if kind == "net" else "event:seq"
        rows = [("game:ordinal", str(game)), (seq_field, str(seq))] + [(f, values[f]) for f in fields]
        for field, value in rows:
            problem = check_counts.value_problem(field, value)
            if problem:
                raise ExportRefused(f"{where}: {problem}; nothing was written")
        step = number
        observations += [{"step": step, "source": "screen", "field": f, "value": v} for f, v in rows]
        observations += [{"step": step, "source": "screen", "ref": f"sha256:{c}"} for c in cited]
    return observations


def bundle_files(paths, frames):
    """The files of the sitting that go to the bundle, all model-driven evidence: sitting.json, the
    action, frame and reading lines, the watcher's log, the session's own screenshots (before.png,
    after.png; the session's logs stay in the sitting directory) and every indexed frame."""
    files = [paths[k] for k in ("sitting_json", "actions", "index", "log", "readings") if paths[k].is_file()]
    if paths["session"].is_dir():
        files += sorted(p for p in paths["session"].iterdir() if p.is_file() and p.suffix == ".png")
    return files + [frames[d] for d in sorted(frames, key=lambda d: frames[d].name)]


def build(paths, name, batch, doc, run_id, rep, table):
    """(record, manifest) for one sitting."""
    row = next((r for r in table if r.get("set") == sitting.SET_ID and r.get("variant") == sitting.VARIANT), None)
    if row is None or doc["binary"]["sha256"] != row.get("sha256") or doc["binary"]["file"] != row.get("file"):
        raise ExportRefused("the sitting's measured binary is not the F019 row's; nothing was written")
    after_loss = games_after_loss(paths, shipped_skr_sha256())
    if after_loss:
        raise ExportRefused(
            f"the game credited a loss (a `loss-credited` line, F003) and the click-driver started game(s) "
            f"{after_loss} after it with no shipped restore of its own between the credit and that start (an "
            f"`skr-restored` line naming that game with the shipped {sitting.SKR} sha256, fix #152), so they "
            f"ran on the successor artifact set {SUCCESSOR_SET}, not the "
            f"shipped {sitting.SET_ID}; the F019 table has no row for the successor, so a record can name "
            "neither (never the shipped set for a game played after a scoreboard write); nothing was written")
    frames = read_frames(paths)
    epoch = int(calendar.timegm(time.strptime(doc["sitting_id"], "%Y%m%dT%H%M%SZ")))
    observations = [{"step": 0, "source": "process", "field": "sitting:epoch", "value": str(epoch)}]
    observations += events(paths, batch, frames, games_started(paths))
    files = bundle_files(paths, frames)
    # `store: release:E020` and `asset` are the evidence-manifest/1 schema's required fields: they name
    # the experiment and the file. The bundle stays on the user's machine; nothing is uploaded, and no
    # release asset is made (constraint A; T38 round 3, R3).
    listed = []
    for path in files:
        digest = sitting.sha256_of(path)
        listed.append({"name": path.name, "bytes": path.stat().st_size, "sha256": digest,
                       "asset": f"{digest[:16]}-{path.name}", "class": "recording"})
    fingerprint = {str(k): str(v) for k, v in doc["versions"].items()}
    bad = [k for k, v in fingerprint.items() if "/" in v or "\\" in v]
    if bad:
        raise ExportRefused(f"sitting.json versions hold a path ({', '.join(bad)}); nothing was written")
    record = {
        "schema": "run/1", "run_id": run_id, "experiment": EXPERIMENT, "arm": name, "rep": rep,
        "code_commit": doc["driver_commit"], "machine": doc["machine"],
        "artifact": {"set": sitting.SET_ID, "variant": sitting.VARIANT},
        "runtime": {"driver": f"experiments/{EXPERIMENT}-wine-first-run/launcher.py@{doc['driver_commit']}",
                    "platform": sitting.PLATFORM, "fingerprint": fingerprint},
        "interventions": [dict(i) for i in INTERVENTIONS],
        "start_state": {"id": "S-iwp-prefix-sync", "sha256": doc["binary"]["sha256"], "restore": RESTORE},
        "seed": None,
        "actions": {"script": f"experiments/{EXPERIMENT}-wine-first-run/play.steps",
                    "sha256": doc["blocks_sha256"], "args": list(doc["argv"])},
        "observations": observations,
        "outputs": [{"name": f["name"], "sha256": f["sha256"], "store": f"release:{EXPERIMENT}"} for f in listed],
        "started": doc["started"], "ended": doc["ended"], "status": doc["status"],
    }
    manifest = {"schema": "evidence-manifest/1", "run_id": run_id, "experiment": EXPERIMENT,
                "store": f"release:{EXPERIMENT}", "artifact": {"set": sitting.SET_ID, "variant": sitting.VARIANT},
                "files": listed}
    return record, manifest


def export(sitting_dir, name, batch, root=ROOT, sitting_root=sitting.SITTING_ROOT,
           prescribed=sitting.SITTING_ROOT, table=None):
    """Write the record and the manifest of one sitting; their repository paths."""
    confined = sitting.confine_root(sitting_root, prescribed)
    given = Path(sitting_dir)
    if not given.is_absolute() or given.parent != confined or not sitting.SITTING_ID.fullmatch(given.name) \
            or Path(os.path.realpath(given)) != given or not given.is_dir():
        raise ExportRefused(f"{given} is not a sitting directory of {confined}; nothing was written")
    paths = sitting.sitting_paths(confined, given.name)
    try:
        doc = json.loads(paths["sitting_json"].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ExportRefused("the directory has no readable sitting.json, so no proof of a sitting; "
                            "nothing was written") from None
    problems = sitting.sitting_problems(doc, given.name, name)
    if problems:
        raise ExportRefused("; ".join(problems) + "; nothing was written")
    table = check_no_originals.load_f019_table(Path(root)) if table is None else table
    run_id = next_run_id(root)
    runs_dir = Path(root) / "runs" / EXPERIMENT / name
    rep = 1 + (sum(1 for _ in runs_dir.glob(f"{EXPERIMENT}-r*.json")) if runs_dir.is_dir() else 0)
    record, manifest = build(paths, name, batch, doc, run_id, rep, table)
    targets = [(Path(root) / "evidence" / EXPERIMENT, f"{run_id}.manifest.json", manifest),
               (runs_dir, f"{run_id}.json", record)]
    for folder, filename, _ in targets:
        if (folder / filename).exists():
            raise ExportRefused(f"{filename} exists; records are never written over; nothing was written")
    written = []
    for folder, filename, data in targets:
        safeio.write_file(folder, filename, data=(json.dumps(data, indent=2) + "\n").encode(), exist="new",
                          create_below=Path(root))
        written.append((folder / filename).relative_to(root).as_posix())
    return written
