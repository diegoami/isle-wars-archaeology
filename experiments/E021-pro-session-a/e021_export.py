"""E021's export: one Session A sitting directory to one run record and one evidence manifest (T45;
rule 20, raw and immutable).

    python3 experiments/E021-pro-session-a/launcher.py --records --sitting <dir> --batch session-a

It is E020's export (experiments/E020-wine-first-run/e020_export.py, imported, never edited) with
this experiment's records: what it requires and never supplies is E020's -- the sitting directory a
direct child of the one sitting root, `sitting.json` the proof of the sitting (the session's own
status, times, versions, commit, block-file sha256 and the measured binary, which becomes
`start_state.sha256` only when it is the F019 row's), every indexed frame present with its sha256,
and no game after a credited loss without the shipped scoreboard's restore (fix #152). Two more
checks are E021's: `sitting.json` names experiment E021 (an E020 sitting is never exported here),
and every frame a line cites is a file of the bundle.

The observations come from the loop's own lines of `actions.jsonl` (e021_loop.py), one step each:
`attack-attempt`, `exchange-click`, `case-met`, `turn-end`, `case-dropped` and `game-abandoned`. Values are structural only
(constraint D): E020's vocabulary (tools/check_counts.py: counters, countries, games, events,
colour words) and six kinds of this experiment's own words -- `case:`, `aim:` and `dropped:` (a row of
the case table), `cell:` (a cell number), `outcome:` and `end:` (the loop's outcome and turn-end words,
listed below). The progress counter (e021_progress.py) reads the `case:kind` / `cell:ordinal`
groups, which only `case-met` lines make.

Run ids are experiment-wide: one more than every `E021-rNNNN` under `runs/E021/` and
`evidence/E021/`; neither file is ever written over.
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
E020 = ROOT / "experiments" / "E020-wine-first-run"
for _path in (ROOT / "setup/iwp", ROOT / "tools", E020, HERE):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))
import check_counts  # noqa: E402
import check_no_originals  # noqa: E402
import safeio  # noqa: E402
import e020_export  # noqa: E402  (imported read-only)
import e020_sitting as sitting  # noqa: E402
import cases  # noqa: E402

EXPERIMENT = "E021"
FOLDER = "E021-pro-session-a"
RUN_ID = re.compile(rf"^{EXPERIMENT}-r(\d{{4,}})(?:\.manifest)?\.json$")
OUTCOMES = frozenset({"no-menu", "target-not-taken", "attacker-refused", "unresolved", "quit", "quit-unconfirmed",
                      "capture", "forfeit"})
ENDS = frozenset({"pass", "forfeit", "no-menu", "game-end", "board-unreadable", "abandoned", "no-fit"})
WORD_KINDS = {"case": frozenset(cases.CASES), "aim": frozenset(cases.CASES), "dropped": frozenset(cases.CASES),
              "outcome": OUTCOMES, "end": ENDS}
SUMMARY = ("exchange_clicks", "clicks_one_army", "clicks_several_armies", "clicks_no_change", "clicks_unread",
           "clicks_unisolated", "fights",
           "battles", "refusals", "captures", "forfeits", "quits", "attack_attempts")
ExportRefused = e020_export.ExportRefused


def value_problem(field, value):
    """Why `value` may not stand under `field`, or "" (E020's vocabulary, then this experiment's)."""
    kind = field.split(":", 1)[0] if isinstance(field, str) else None
    if kind == "cell":
        if not check_counts.FIELD.fullmatch(field):
            return f"field {field!r} is not a structural kind:role name"
        if not isinstance(value, str) or not re.fullmatch(r"[1-9][0-9]{0,2}", value):
            return f"{field}: {value!r} is not a cell number"
        return ""
    if kind in WORD_KINDS:
        if not check_counts.FIELD.fullmatch(field):
            return f"field {field!r} is not a structural kind:role name"
        if value not in WORD_KINDS[kind]:
            return f"{field}: {value!r} is not one of {sorted(WORD_KINDS[kind])}"
        return ""
    return check_counts.value_problem(field, value)


def next_run_id(root=ROOT):
    numbers = [0]
    for folder in (Path(root) / "runs" / EXPERIMENT, Path(root) / "evidence" / EXPERIMENT):
        if folder.is_dir():
            numbers += [int(m.group(1)) for p in folder.rglob(f"{EXPERIMENT}-r*.json") if (m := RUN_ID.match(p.name))]
    return f"{EXPERIMENT}-r{max(numbers) + 1:04d}"


def counts_rows(prefix, counts):
    """The rows of one [attacker army, attacker owner, defender army, defender owner] list."""
    a_army, a_owner, d_army, d_owner = counts
    rows = []
    for field, value in ((f"counter:attacker-{prefix}", a_army), (f"owner:attacker-{prefix}", a_owner),
                         (f"counter:defender-{prefix}", d_army), (f"owner:defender-{prefix}", d_owner)):
        if value is not None:                   # an unread count stays out, never guessed
            rows.append((field, str(value)))
    return rows


def flag(value):
    return "1" if value else "0"


def rows_of(line):
    """(rows, cited frames) for one of the loop's lines, or None for a line the record does not take."""
    event = line.get("event")
    game = [("game:ordinal", str(line.get("game")))]
    turn = [("counter:turn", str(line["turn"]))] if isinstance(line.get("turn"), int) else []
    if event == "attack-attempt":
        rows = game + turn + [("event:seq", str(line["attempt"])), ("aim:case", line["case"]), ("cell:aim", str(line["cell"])),
                       ("country:attacker", str(line["attacker"])), ("country:defender", str(line["defender"]))]
        rows += counts_rows("before", line["before"]) + counts_rows("after", line["after"])
        rows += [("counter:battle", flag(line["battle"])), ("counter:fought", flag(line.get("fought"))),
                 ("counter:clicks", str(line["clicks"])),
                 ("counter:clicks-unknown", str(line.get("unknown", 0))), ("outcome:attack", line["outcome"])]
        if line.get("lost") is not None:              # unknown when a click of it has no count
            rows.append(("counter:lost", str(line["lost"])))
        if "answered" in line:
            rows.append(("counter:attacker-answered", flag(line["answered"])))
        if line.get("seat_after") is not None:
            rows.append(("owner:seat-after", line["seat_after"]))
        return rows, line.get("frames") or []
    if event == "exchange-click":
        rows = game + [("event:attempt", str(line["attempt"])), ("counter:click", str(line["click"]))]
        rows += counts_rows("before", line["before"]) + counts_rows("after", line["after"])
        if line.get("lost") is not None:
            rows.append(("counter:lost", str(line["lost"])))
        if "isolated" in line:
            rows.append(("counter:isolated", flag(line["isolated"])))
        if "moved_in" in line:
            rows.append(("counter:moved-in", flag(line["moved_in"])))
        return rows, line.get("frames") or []
    if event == "case-met":
        rows = game + [("case:kind", line["case"]), ("cell:ordinal", str(line["cell"]))]
        if line.get("attempt") is not None:
            rows.append(("event:attempt", str(line["attempt"])))
        for key in ("battle", "battles", "fought", "fights"):
            if line.get(key) is not None:
                rows.append((f"counter:{key}", str(int(line[key]))))
        if line.get("end") is not None:
            rows.append(("end:turn", line["end"]))
        return rows, []
    if event == "turn-end":
        return game + turn + [("counter:battles", str(line["battles"])),
                              ("counter:fights", str(line.get("fights", 0))), ("end:turn", line["end"])], []
    if event == "game-abandoned":
        return game + turn + [("end:game", line["reason"]), ("counter:turns", str(line["turns"]))], []
    if event == "case-dropped":
        return game + turn + [("dropped:case", line["case"]), ("counter:failures", str(line["failures"])),
                              ("outcome:attack", line["outcome"])], []
    return None


def observations_of(paths, games, bundle):
    """The run/1 observations of the loop's lines; ExportRefused on any line that is not clean."""
    observations, step = [], 0
    for number, line in enumerate(e020_export.jsonl(paths["actions"]), start=1):
        where = f"actions.jsonl line {number}"
        try:
            found = rows_of(line)
        except (KeyError, TypeError, ValueError) as exc:
            raise ExportRefused(f"{where}: a {line.get('event')} line lacks {exc}; nothing was written") from None
        if found is None:
            continue
        rows, cited = found
        game = line.get("game")
        if not isinstance(game, int) or isinstance(game, bool) or game not in games:
            raise ExportRefused(f"{where}: game {game!r} is not a game the click-driver started; nothing was written")
        for field, value in rows:
            problem = value_problem(field, value)
            if problem:
                raise ExportRefused(f"{where}: {problem}; nothing was written")
        missing = [c for c in cited if c not in bundle]
        if missing:
            raise ExportRefused(f"{where}: cites a frame that is not a file of the bundle ({missing[0][:16]}); "
                                "nothing was written")
        step += 1
        observations += [{"step": step, "source": "screen", "field": f, "value": v} for f, v in rows]
        observations += [{"step": step, "source": "screen", "ref": f"sha256:{c}"} for c in dict.fromkeys(cited)]
    return observations


def build(paths, name, doc, run_id, rep, table):
    """(record, manifest) for one sitting."""
    row = next((r for r in table if r.get("set") == sitting.SET_ID and r.get("variant") == sitting.VARIANT), None)
    if row is None or doc["binary"]["sha256"] != row.get("sha256") or doc["binary"]["file"] != row.get("file"):
        raise ExportRefused("the sitting's measured binary is not the F019 row's; nothing was written")
    after_loss = e020_export.games_after_loss(paths, e020_export.shipped_skr_sha256())
    if after_loss:
        raise ExportRefused(f"the game credited a loss and the click-driver started game(s) {after_loss} after it "
                            f"with no shipped restore of its own (fix #152): they ran on the successor set "
                            f"{e020_export.SUCCESSOR_SET}, which F019 has no row for; nothing was written")
    frames = e020_export.read_frames(paths)
    files = e020_export.bundle_files(paths, frames)
    listed = []
    for path in files:
        digest = sitting.sha256_of(path)
        listed.append({"name": path.name, "bytes": path.stat().st_size, "sha256": digest,
                       "asset": f"{digest[:16]}-{path.name}", "class": "recording"})
    bundle = {f["sha256"] for f in listed}
    epoch = int(calendar.timegm(time.strptime(doc["sitting_id"], "%Y%m%dT%H%M%SZ")))
    observations = [{"step": 0, "source": "process", "field": "sitting:epoch", "value": str(epoch)}]
    loop = doc.get("loop") if isinstance(doc.get("loop"), dict) else {}
    for key in SUMMARY:
        value = loop.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            observations.append({"step": 0, "source": "process", "field": "counter:" + key.replace("_", "-"),
                                 "value": str(value)})
    observations += observations_of(paths, e020_export.games_started(paths), bundle)
    fingerprint = {str(k): str(v) for k, v in doc["versions"].items()}
    bad = [k for k, v in fingerprint.items() if "/" in v or "\\" in v]
    if bad:
        raise ExportRefused(f"sitting.json versions hold a path ({', '.join(bad)}); nothing was written")
    record = {
        "schema": "run/1", "run_id": run_id, "experiment": EXPERIMENT, "arm": name, "rep": rep,
        "code_commit": doc["driver_commit"], "machine": doc["machine"],
        "artifact": {"set": sitting.SET_ID, "variant": sitting.VARIANT},
        "runtime": {"driver": f"experiments/{FOLDER}/launcher.py@{doc['driver_commit']}",
                    "platform": sitting.PLATFORM, "fingerprint": fingerprint},
        "interventions": [dict(i) for i in e020_export.INTERVENTIONS],
        "start_state": {"id": "S-iwp-prefix-sync", "sha256": doc["binary"]["sha256"], "restore": e020_export.RESTORE},
        "seed": None,
        "actions": {"script": f"experiments/{FOLDER}/session-a.steps", "sha256": doc["blocks_sha256"],
                    "args": list(doc["argv"])},
        "observations": observations,
        "outputs": [{"name": f["name"], "sha256": f["sha256"], "store": f"release:{EXPERIMENT}"} for f in listed],
        "started": doc["started"], "ended": doc["ended"], "status": doc["status"],
    }
    manifest = {"schema": "evidence-manifest/1", "run_id": run_id, "experiment": EXPERIMENT,
                "store": f"release:{EXPERIMENT}", "artifact": {"set": sitting.SET_ID, "variant": sitting.VARIANT},
                "files": listed}
    return record, manifest


def export(sitting_dir, name, root=ROOT, sitting_root=sitting.SITTING_ROOT, prescribed=sitting.SITTING_ROOT,
           table=None):
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
        raise ExportRefused("the directory has no readable sitting.json; nothing was written") from None
    problems = sitting.sitting_problems(doc, given.name, name)
    if isinstance(doc, dict) and doc.get("experiment") != EXPERIMENT:
        problems.append(f"sitting.json experiment is {doc.get('experiment')!r}, not {EXPERIMENT!r}")
    if problems:
        raise ExportRefused("; ".join(problems) + "; nothing was written")
    table = check_no_originals.load_f019_table(Path(root)) if table is None else table
    run_id = next_run_id(root)
    runs_dir = Path(root) / "runs" / EXPERIMENT / name
    rep = 1 + (sum(1 for _ in runs_dir.glob(f"{EXPERIMENT}-r*.json")) if runs_dir.is_dir() else 0)
    record, manifest = build(paths, name, doc, run_id, rep, table)
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
