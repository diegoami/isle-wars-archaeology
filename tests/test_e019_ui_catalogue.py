"""E019 (T24): the UI-walk recorder, its records, and the catalogue check.

Tests here need no game, no display and no Wine. The walk table and the pixel helpers are tested
directly. The recorder is tested end to end: every walk of walks.py is driven through
run_walk.run_walk() with a fake session (FakeSession below: a fake screen and a fake clock, no
game), the records and manifests are the ones run_walk writes, with nothing added by hand, and
check_ui_catalogue's checks are run on them. The checker's refusals are tested by mutating that
recorder-written tree, never a hand-made record (round 2, R2).
"""
import contextlib
import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "experiments" / "E019-pro-ui"))

import walks  # noqa: E402
import pixels  # noqa: E402
import records as e019_records  # noqa: E402
import check_ui_catalogue  # noqa: E402
import run_walk  # noqa: E402
import test_runs  # noqa: E402  (the amended record-layout rule, and the pinned run/1 validator)

QUESTIONS = ROOT / "questions" / "pro-static.md"
INVENTORY = ROOT / "experiments" / "E008-static-triage" / "measurements" / "iwp-extract-pro-r1.json"

# The five per-screen batches of T24, in the order the task file fixes them.
BRIEF_BATCHES = [
    ("title-options", ["Q-UI-04", "Q-UI-10", "Q-UI-19", "Q-UI-22"]),
    ("board-pieces", ["Q-UI-01", "Q-UI-02", "Q-UI-03", "Q-UI-05", "Q-UI-20", "Q-PLY-04"]),
    ("play", ["Q-UI-08", "Q-UI-12", "Q-UI-13", "Q-UI-15", "Q-UI-16"]),
    ("events-end", ["Q-UI-06", "Q-UI-07", "Q-UI-11", "Q-UI-14", "Q-UI-21"]),
    ("inputs-sounds", ["Q-UI-09", "Q-UI-17", "Q-UI-18"]),
]
FRAME_TIMED = {"Q-UI-06", "Q-UI-13", "Q-UI-16"}
HIT_AREAS = {"Q-UI-18"}
STATIC_ONLY = {"Q-UI-14", "Q-UI-21"}
# the rows whose target needs an identification the pixels cannot make: proxied, F020 narrowed
PROXIED = {"Q-UI-06", "Q-UI-07", "Q-UI-13"}


def catalogue_ids():
    rows = walks.question_rows(QUESTIONS)
    return [qid for qid in rows if qid.startswith("Q-UI-")] + ["Q-PLY-04"]


def walk_order():
    """(qid, size) of every walk, in the batches' order: one per question, one per size for Q-UI-19."""
    return [(qid, size) for _, qids in walks.BATCHES for qid in qids
            for size in (walks.WALKS[qid].get("sizes") or [None])]


# --- the fake session: a screen and a clock, no game --------------------------------------------

class FakeClock:
    def __init__(self):
        self.now = 0.0

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.now += max(0.0, float(seconds))


class FakeScreen:
    """Region reads that change when an input or a pointer move is sent, and every two fake seconds
    (so the timed watches see changes); a whole-display read is the size the session was made at."""

    def __init__(self, fake):
        self.fake = fake

    def state(self):
        return (self.fake.events, int(self.fake.clock.now // 2))

    def raw(self, rect):
        if rect is None:
            w, h = (int(v) for v in self.fake.size.split("x")[:2])
            return bytes(w * h * 3)
        return hashlib.sha256(repr((self.state(), tuple(rect))).encode()).digest()[:12]   # 4 pixels


class FakeEngine:
    def __init__(self, fake):
        self.screen = FakeScreen(fake)
        self.obs = []
        self.outputs = []
        self.started = self.ended = None
        self.status = "running"
        self._error = None
        self.faults = []

    def abort_later(self, reason):
        self.faults.append(reason)
        self.status = f"aborted: fake: {reason}"


class FakeSession:
    """The driver Session's surface that run_walk uses, over a fake screen and clock. It makes no
    observation the recorder does not ask for, except the ones the driver itself makes (the title
    time and each screenshot's pixel hash); `drop` removes recorder observations (field, match) and
    `drop_outputs` screenshots, to show the check refuses a record without them."""

    def __init__(self, run_id, prefix, bundles, install, display, arm, size, *, clock, workdir,
                 drop=(), drop_outputs=(), snapshot=True):
        self.run_id, self.size, self.clock = run_id, size, clock
        self.workdir = Path(workdir) / run_id
        self.workdir.mkdir(parents=True)
        self.events = 0
        self.drop, self.drop_outputs = list(drop), set(drop_outputs)
        self._engine = FakeEngine(self)
        self.snap_before = ("fake", {"drive_c": ("dir",)}) if snapshot else None
        self.recovered = False
        self.elapsed = None

    @property
    def status(self):
        return self._engine.status

    @property
    def obs(self):
        return list(self._engine.obs)

    def execute(self, body):
        self._engine.started = "2026-10-08T00:00:00Z"
        try:
            body(self)
            self._engine.status = "completed"
        except Exception as exc:          # what the driver records as an aborted session
            self._engine.status = f"aborted: fake: {type(exc).__name__}: {exc}"
        self.recovered = True
        self.elapsed = round(self.clock.now, 2)
        self._engine.ended = "2026-10-08T00:01:00Z"
        return self._engine.status

    def expect(self, *names):
        pass

    def known_screen(self):
        self.observe(2, "screen", "title screen reached and stable, seconds after launch", 6.6)

    def wait_for_screen(self, name, timeout=None, stable=True):
        return 0.0

    def game_alive(self):
        return True

    def perform(self, text):
        words = text.split()
        if words[0] == "shot":
            self._shot(f"{words[1]}.png")
        elif words[0] in run_walk.sessionlib.INPUT_OPS or words[0] == "move":
            self.events += 1

    def observe_screenshot(self, name, step=None):
        self._shot(name)

    def _shot(self, name):
        pixels_sha = hashlib.sha256(repr(self.screen_state()).encode()).hexdigest()
        self._engine.obs.append({"step": 1, "source": "screen", "field": f"{name} raw RGB8 pixels sha256",
                                 "value": pixels_sha})
        if name in self.drop_outputs:
            return
        path = self.workdir / name
        path.write_bytes(f"{self.run_id} {name} {pixels_sha}".encode())
        self._engine.outputs.append((name, path, "screenshot"))

    def screen_state(self):
        return self._engine.screen.state()

    def observe(self, step, source, field, value):
        for dropped, match in self.drop:
            if (field == dropped) if match == "exact" else field.startswith(dropped):
                return
        self._engine.obs.append({"step": step, "source": source, "field": field, "value": str(value)})


def drive(root, qids=None, **fake_options):
    """Run the recorder (run_walk.run_walk) for the walks named (every walk by default) into `root`,
    with a fake session; returns [(qid, size, status, recovered)]."""
    root = Path(root).resolve()
    locs = {"IWP_PREFIX": root / "prefix", "IWP_DIR": root / "install", "E019_BUNDLES": root / "bundles"}
    for path in locs.values():
        path.mkdir(exist_ok=True)
    clock = FakeClock()

    def factory(*args):
        return FakeSession(*args, clock=clock, workdir=root / "work", **fake_options)

    results = []
    with mock.patch.object(run_walk, "CLOCK", clock.clock), mock.patch.object(run_walk, "SLEEP", clock.sleep), \
            contextlib.redirect_stdout(io.StringIO()):
        for qid, size in walk_order():
            if qids is not None and qid not in qids:
                continue
            status, recovered = run_walk.run_walk(qid, size, locs, ":99", "0123456789ab", "local", ["--test"],
                                                  {"wine": "fake"}, root=root, session_factory=factory)
            results.append((qid, size, status, recovered))
    return results


def write_f020(root, status_of=None):
    """A minimal F020 (the catalogue is T39's; this is the shape check_ui_catalogue reads): one
    section per question, the proxied ones narrowed, the none-found ones static-only."""
    lines = ["# F020 UI observations catalogue (structure)", "", "## Observations", ""]
    for qid in catalogue_ids():
        if status_of and qid in status_of:
            status = status_of[qid]
        elif qid in PROXIED:
            status = "narrowed"
        elif qid in STATIC_ONLY:
            status = "static-only"
        else:
            status = "observed"
        lines += [f"#### {qid} question text", f"- **Observation**: {status}: described from the records.", ""]
    path = Path(root) / "findings" / "F020-pro-ui-observations.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def records_of(root, qid):
    """[(path, record)] of one question's records under root, in run-id order."""
    found = []
    for path in sorted((Path(root) / "runs" / "E019").glob("*/E019-r*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record["arm"] == e019_records.arm_of_question(qid):
            found.append((path, record))
    return found


def check(root, f020=False):
    return check_ui_catalogue.run_checks(Path(root), questions_path=QUESTIONS, inventory_path=INVENTORY,
                                         f020=f020)


_BASE = {}


def recorded_tree():
    """The tree every walk's recorder run wrote (built once per test run, copied by each test)."""
    if "dir" not in _BASE:
        tmp = tempfile.mkdtemp(prefix="e019-e2e-")
        _BASE["dir"] = tmp
        _BASE["results"] = drive(tmp)
    return Path(_BASE["dir"])


def tearDownModule():
    if "dir" in _BASE:
        shutil.rmtree(_BASE["dir"], ignore_errors=True)


class Copy:
    """A private copy of the recorder-written tree, to mutate."""

    def __enter__(self):
        self.tmp = tempfile.mkdtemp(prefix="e019-copy-")
        for part in ("runs", "evidence"):
            shutil.copytree(recorded_tree() / part, Path(self.tmp) / part)
        return Path(self.tmp)

    def __exit__(self, *exc):
        shutil.rmtree(self.tmp, ignore_errors=True)


def rewrite(path, change):
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    change(record)
    Path(path).write_text(json.dumps(record), encoding="utf-8")


# --- the walk table ------------------------------------------------------------------------------

class WalkTableTest(unittest.TestCase):
    def test_every_catalogue_question_has_a_walk_spec_in_the_batches_of_the_task(self):
        ids = catalogue_ids()
        self.assertEqual(len(ids), 23)
        self.assertEqual([name for name, _ in walks.BATCHES], [name for name, _ in BRIEF_BATCHES])
        for (name, qids), (_, want_qids) in zip(walks.BATCHES, BRIEF_BATCHES):
            self.assertEqual(qids, want_qids, name)
        self.assertEqual(set(walks.WALKS), set(ids))

    def test_every_spec_belongs_to_the_batch_that_names_it(self):
        for qid, spec in walks.WALKS.items():
            self.assertIn(qid, dict(walks.BATCHES)[spec["batch"]], qid)

    def test_targets_come_from_the_question_rows(self):
        import re
        rows = walks.question_rows(QUESTIONS)
        for qid, spec in walks.WALKS.items():
            cell = rows[qid]["corroboration"]
            m = re.search(r"at least (\d+) ([a-z ]+)", cell)
            if m:
                # the row's own "at least N <word>" is the target, in the row's words
                self.assertEqual(spec["count"]["word"], m.group(2).strip(), qid)
                self.assertEqual(spec["count"]["at_least"], int(m.group(1)), qid)
            self.assertEqual(spec.get("timing") == "frame-timed", qid in FRAME_TIMED, qid)
            self.assertEqual(bool(spec.get("hit_areas")), qid in HIT_AREAS, qid)

    def test_the_proxied_targets_are_exactly_the_rows_that_need_an_identification(self):
        proxied = {qid for qid, spec in walks.WALKS.items() if check_ui_catalogue.is_proxy(spec)}
        self.assertEqual(proxied, PROXIED)

    def test_the_two_none_found_rows_are_the_static_only_walks(self):
        for qid in STATIC_ONLY:
            spec = walks.WALKS[qid]
            self.assertTrue(spec.get("absence") or spec.get("states"), qid)

    def test_q_ui_21_names_the_four_reference_states(self):
        self.assertEqual(walks.WALKS["Q-UI-21"]["states"], ["setup", "mid-game", "battle", "end"])

    def test_every_step_line_parses_in_the_e002_step_language(self):
        sys.path.insert(0, str(ROOT / "runtime" / "iwp" / "spike"))
        import steps as stepslib
        for qid, spec in walks.WALKS.items():
            for line in walks.step_lines(spec):
                try:
                    stepslib.parse_line(line)
                except stepslib.StepError as exc:
                    self.fail(f"{qid}: step {line!r} refused: {exc}")

    def test_every_region_is_inside_the_stage_and_says_where_it_came_from(self):
        for label, region in walks.REGIONS.items():
            x, y, w, h = region["rect"]
            self.assertTrue(0 <= x and 0 <= y and x + w <= 800 and y + h <= 600, label)
            self.assertTrue(region.get("source"), label)

    def test_every_spec_region_is_defined(self):
        for qid, spec in walks.WALKS.items():
            for label in spec.get("regions", []):
                self.assertIn(label, walks.REGIONS, f"{qid}: region {label}")
            for item in spec["actions"]:
                if item[0] == "timed_watch":
                    for label in ([item[1]] if isinstance(item[1], str) else item[1]):
                        self.assertIn(label, walks.REGIONS, f"{qid}: watched region {label}")


class PixelsTest(unittest.TestCase):
    def rgb(self, w, h, fn):
        return bytes(v for y in range(h) for x in range(w) for v in fn(x, y))

    def test_census_counts_distinct_quantised_colours(self):
        data = self.rgb(4, 1, lambda x, y: (10, 10, 250) if x < 2 else (250, 10, 10))
        result = pixels.census(data, quantise=16)
        self.assertEqual(result["distinct"], 2)
        self.assertEqual(result["total"], 4)
        self.assertEqual({tuple(c) for c, _ in result["top"]}, {(0, 0, 240), (240, 0, 0)})

    def test_greyscale_census_collapses_to_luminance(self):
        data = self.rgb(2, 1, lambda x, y: (10, 10, 10) if x == 0 else (250, 250, 250))
        result = pixels.greyscale_census(data, quantise=16)
        self.assertEqual(result["distinct"], 2)
        self.assertEqual(sorted(g for g, _ in result["top"]), [0, 240])

    def test_text_rows_finds_the_height_of_ink_bands(self):
        def px(x, y):
            if 2 <= y <= 4 and 1 <= x <= 8:
                return (30, 30, 30)
            if y == 6 and 1 <= x <= 8:
                return (30, 30, 30)
            return (200, 200, 200)
        result = pixels.text_rows(self.rgb(10, 8, px), 10, tol=40)
        self.assertEqual(result["boxes"], 2)
        self.assertEqual(result["heights"], [3, 1])

    def test_hover_points_steps_a_grid_inside_the_rectangle(self):
        points = pixels.hover_points((470, 515, 40, 20), step=10, ys=(525, 535))
        self.assertEqual(points, [(470, 525), (480, 525), (490, 525), (500, 525),
                                  (470, 535), (480, 535), (490, 535), (500, 535)])


class RecordLayoutTest(unittest.TestCase):
    def test_a_batch_folder_record_sits_at_its_batch_and_is_valid(self):
        path = ROOT / "runs" / "E019" / "title-options" / "E019-r9999.json"
        self.assertEqual(test_runs.record_experiment(path), "E019")

    def test_a_record_still_must_sit_under_its_own_experiment(self):
        doc_text = (ROOT / "runs" / "E004" / "E004-r0062.json").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "runs" / "E019" / "title-options"
            folder.mkdir(parents=True)
            path = folder / "E002-r0001.json"
            path.write_text(doc_text, encoding="utf-8")
            errors = test_runs.run_record_errors(path, None)
        self.assertTrue(any("experiment" in e and "E004" in e for e in errors), errors)

    def test_deeper_nesting_is_refused(self):
        self.assertIsNone(test_runs.record_experiment(ROOT / "runs" / "E019" / "a" / "b" / "E019-r0001.json"))

    def test_paths_of_a_record_and_its_manifest(self):
        self.assertEqual(e019_records.record_paths("play", "E019-r0007"),
                         {"run": "runs/E019/play/E019-r0007.json",
                          "manifest": "evidence/E019/play/E019-r0007.manifest.json"})

    def test_arm_and_question_round_trip(self):
        self.assertEqual(e019_records.arm_of_question("Q-UI-04"), "q-ui-04")
        self.assertEqual(e019_records.question_of_arm("q-ply-04"), "Q-PLY-04")

    def test_the_recorder_and_the_driver_agree_on_the_artifact_sets(self):
        sys.path.insert(0, str(ROOT / "runtime" / "iwp" / "spike"))
        import cycle as spike  # noqa: E402
        self.assertEqual(e019_records.ARTIFACT_SET, spike.SET_ID)
        self.assertEqual(e019_records.ARTIFACT_SET_SAVED_FILES, spike.SUCCESSOR2_ID)


# --- DW2: the recorder end to end -----------------------------------------------------------------

class RecorderEndToEndTest(unittest.TestCase):
    """Every walk of walks.py through run_walk.run_walk with a fake session; the check runs on the
    records the recorder wrote, with nothing added by hand."""

    def test_every_walk_is_recorded_completed_and_recovered(self):
        recorded_tree()
        self.assertEqual([(q, s) for q, s, _, _ in _BASE["results"]], walk_order())
        for qid, size, status, recovered in _BASE["results"]:
            self.assertEqual((status, recovered), ("completed", True), f"{qid} {size}")

    def test_the_recorders_own_records_pass_every_record_check(self):
        self.assertEqual(check(recorded_tree()), [])

    def test_the_recorders_own_records_with_a_catalogue_pass_the_whole_check(self):
        with Copy() as tmp:
            write_f020(tmp)
            self.assertEqual(check(tmp, f020=True), [])

    def test_the_recorders_records_and_manifests_are_valid_run_1_and_evidence_manifest_1(self):
        root = recorded_tree()
        known = {e019_records.ARTIFACT_SET, e019_records.ARTIFACT_SET_SAVED_FILES}
        for path in sorted((root / "runs" / "E019").glob("*/E019-r*.json")):
            self.assertEqual(test_runs.run_record_errors(path, known), [], path.name)
        for path in sorted((root / "evidence" / "E019").glob("*/*.manifest.json")):
            errors, _ = test_runs.schema_errors(path, test_runs.MANIFEST_SCHEMA)
            self.assertEqual(errors, [], path.name)

    def test_removing_any_required_field_the_recorder_writes_fails_the_check(self):
        """For every walk and every observation field the check requires of it, a recorder run that
        does not write that field gives a record the check refuses, naming the question."""
        for qid in catalogue_ids():
            spec = walks.WALKS[qid]
            # the task's own list (the run id, screenshots and seal are tested apart), so that a
            # field dropped from the checker's list is still tested here
            task_fields = [("walk question", "exact"), ("speed setting", "exact"), ("display size", "exact"),
                           ("observation", "exact")]
            if spec.get("count"):
                task_fields.append((f"count: {spec['count'].get('measured', spec['count']['word'])}", "exact"))
            if qid in PROXIED:
                task_fields.append((f"count note: {spec['count']['word']}", "exact"))
            if qid in FRAME_TIMED:
                task_fields.append(("timing:", "prefix"))
            if qid in HIT_AREAS:
                task_fields.append(("hit-area:", "prefix"))
            task_fields += [(f"read: {kind}", "exact") for kind in spec.get("reads", {})]
            fields = list(dict.fromkeys(task_fields + check_ui_catalogue.required_fields(spec)))
            for field, match in fields:
                with self.subTest(qid=qid, field=field), tempfile.TemporaryDirectory() as tmp:
                    drive_one(tmp, qid, walk_order_first(qid), drop=[(field, match)])
                    errors = [e for e in check(tmp) if f"({qid})" in e]
                    self.assertTrue(any(field.rstrip(":") in e for e in errors), (field, errors))

    def test_removing_a_required_output_fails_the_check(self):
        for qid in catalogue_ids():
            for name in check_ui_catalogue.required_outputs(walks.WALKS[qid]):
                with self.subTest(qid=qid, output=name), tempfile.TemporaryDirectory() as tmp:
                    drive_one(tmp, qid, walk_order_first(qid), drop_outputs={name})
                    errors = [e for e in check(tmp) if f"({qid})" in e]
                    self.assertTrue(any(name in e for e in errors), errors)

    def test_a_record_without_the_seal_fails_the_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            drive_one(tmp, "Q-UI-01", None, snapshot=False)
            errors = check(tmp)
            self.assertTrue(any("(Q-UI-01)" in e and "start_state" in e for e in errors), errors)

    def test_the_real_tree_fails_while_the_walks_have_not_run(self):
        """The honest state of this PR: no E019 records exist (the walks are T39's), so the
        repository's own check fails, naming the questions still missing."""
        errors = check_ui_catalogue.run_checks(ROOT, questions_path=QUESTIONS, inventory_path=INVENTORY)
        self.assertTrue(any("Q-UI-01" in e and "has not run" in e for e in errors), errors)


def walk_order_first(qid):
    """The first size a question's walk runs at (None: the default size)."""
    return (walks.WALKS[qid].get("sizes") or [None])[0]


def drive_one(root, qid, size, **fake_options):
    """One walk, at one size, through run_walk into root."""
    root = Path(root).resolve()
    locs = {"IWP_PREFIX": root / "prefix", "IWP_DIR": root / "install", "E019_BUNDLES": root / "bundles"}
    for path in locs.values():
        path.mkdir(exist_ok=True)
    clock = FakeClock()

    def factory(*args):
        return FakeSession(*args, clock=clock, workdir=root / "work", **fake_options)

    with mock.patch.object(run_walk, "CLOCK", clock.clock), mock.patch.object(run_walk, "SLEEP", clock.sleep), \
            contextlib.redirect_stdout(io.StringIO()):
        return run_walk.run_walk(qid, size, locs, ":99", "0123456789ab", "local", ["--test"], {"wine": "fake"},
                                 root=root, session_factory=factory)


# --- DW3: one regression per round-2 finding -------------------------------------------------------

class RoundTwoRegressionTest(unittest.TestCase):

    # R2: the recorder writes the per-question observation itself
    def test_r2_the_recorder_writes_the_per_question_observation(self):
        for qid in catalogue_ids():
            with self.subTest(qid=qid):
                (path, record), *_ = records_of(recorded_tree(), qid)
                values = [o["value"] for o in record["observations"] if o["field"] == "observation"]
                self.assertEqual(len(values), 1)
                summary = json.loads(values[0])
                self.assertEqual(summary["question"], qid)
                names = {o["name"] for o in record["outputs"]}
                self.assertTrue(set(summary["screenshots"]) <= names)

    # R3: Q-UI-06's flash candidates are never counted as events
    def test_r3_q_ui_06_never_emits_an_events_count(self):
        (path, record), = records_of(recorded_tree(), "Q-UI-06")
        fields = [o["field"] for o in record["observations"]]
        self.assertNotIn("count: events", fields)
        self.assertIn("count: flash candidates", fields)
        self.assertIn("count note: events", fields)

    def test_r3_the_check_refuses_an_events_count_and_an_observed_q_ui_06(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-06")[0]

            def rename(record):
                for o in record["observations"]:
                    if o["field"] == "count: flash candidates":
                        o["field"] = "count: events"
            rewrite(path, rename)
            write_f020(tmp, status_of={"Q-UI-06": "observed"})
            errors = check(tmp, f020=True)
            self.assertTrue(any("(Q-UI-06)" in e and "count: flash candidates" in e for e in errors), errors)
            self.assertTrue(any(e.startswith("Q-UI-06: F020 is observed") for e in errors), errors)

    def test_r3_one_tick_with_two_regions_changing_is_one_candidate(self):
        """Two countable regions changing in the same poll are one candidate, not two (a flash drawn
        over both is not two events)."""
        clock = FakeClock()
        session = FakeSession("E019-r0001", None, None, None, ":99", "q-ui-06", "800x600x24",
                              clock=clock, workdir=tempfile.mkdtemp(prefix="e019-r3-"))
        ctx = run_walk.Ctx(dict(walks.WALKS["Q-UI-06"], qid="Q-UI-06"))
        with mock.patch.object(run_walk, "CLOCK", clock.clock), mock.patch.object(run_walk, "SLEEP", clock.sleep):
            counted = run_walk.watch_regions(session, ctx, ["message-strip", "board-area"], 4.0, 1.0,
                                             flashes=True)
        shutil.rmtree(session.workdir.parent, ignore_errors=True)
        per_region = [json.loads(o["value"])["region"] for o in session.obs if o["field"] == "flash candidate"]
        self.assertEqual(per_region.count("message-strip"), per_region.count("board-area"))
        self.assertEqual(counted, per_region.count("board-area"))     # one per tick, not one per region
        self.assertGreater(counted, 0)

    # R4: the regions are polled together in one timed loop
    def test_r4_every_watched_region_is_polled_on_every_tick(self):
        clock = FakeClock()
        session = FakeSession("E019-r0001", None, None, None, ":99", "q-ui-13", "800x600x24",
                              clock=clock, workdir=tempfile.mkdtemp(prefix="e019-r4-"))
        reads = []
        raw = session._engine.screen.raw

        def counting(rect):
            reads.append(rect)
            return raw(rect)
        session._engine.screen.raw = counting
        ctx = run_walk.Ctx(dict(walks.WALKS["Q-UI-13"], qid="Q-UI-13"))
        labels = ["message-strip", "phase-panel", "board-area"]
        with mock.patch.object(run_walk, "CLOCK", clock.clock), mock.patch.object(run_walk, "SLEEP", clock.sleep):
            run_walk.watch_regions(session, ctx, labels, 25, 0.25, field="timing: computer turn change")
        shutil.rmtree(session.workdir.parent, ignore_errors=True)
        rects = [walks.REGIONS[label]["rect"] for label in labels]
        counts = [reads.count(rect) for rect in rects]
        self.assertEqual(counts[0], counts[1])
        self.assertEqual(counts[1], counts[2])
        self.assertGreater(counts[0], 90)                 # 25 s at 0.25 s: every region, every tick
        changed = {json.loads(o["value"])["region"] for o in session.obs
                   if o["field"] == "timing: computer turn change"}
        self.assertEqual(changed, set(labels))

    def test_r4_q_ui_13s_record_times_every_watched_region(self):
        (path, record), = records_of(recorded_tree(), "Q-UI-13")
        regions = {json.loads(o["value"])["region"] for o in record["observations"]
                   if o["field"] == "timing: computer turn change"}
        self.assertEqual(regions, {"message-strip", "phase-panel", "board-area"})

    # R5: the display sizes are measured, and distinct sizes are required
    def test_r5_q_ui_19s_records_carry_each_measured_display_size(self):
        shown = set()
        for _, record in records_of(recorded_tree(), "Q-UI-19"):
            size = json.loads(next(o["value"] for o in record["observations"] if o["field"] == "display size"))
            w, h = (int(v) for v in size["requested"].split("x")[:2])
            self.assertEqual(size["display pixels"], w * h)
            shown.add(size["requested"])
        self.assertEqual(shown, set(walks.WALKS["Q-UI-19"]["sizes"]))

    def test_r5_four_records_at_one_size_do_not_cover_four_sizes(self):
        with Copy() as tmp:
            for path, _ in records_of(tmp, "Q-UI-19"):
                def one_size(record):
                    for o in record["observations"]:
                        if o["field"] == "display size":
                            o["value"] = json.dumps({"requested": "800x600x24", "display pixels": 480000})
                rewrite(path, one_size)
            errors = check(tmp)
            self.assertTrue(any(e.startswith("Q-UI-19: no completed record shows the display size 640x480x24")
                                for e in errors), errors)

    def test_r5_a_size_not_measured_as_asked_is_refused(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-19")[0]

            def wrong(record):
                for o in record["observations"]:
                    if o["field"] == "display size":
                        o["value"] = json.dumps({"requested": "640x480x24", "display pixels": 480000})
            rewrite(path, wrong)
            errors = check(tmp)
            self.assertTrue(any("(Q-UI-19)" in e and "measured 480000" in e for e in errors), errors)

    def test_r5_a_count_is_met_by_one_record_never_by_adding_records(self):
        with Copy() as tmp:
            path, record = records_of(tmp, "Q-UI-16")[0]
            half = dict(record)

            def low(r):
                for o in r["observations"]:
                    if o["field"] == "count: attacks":
                        o["value"] = "10"
            rewrite(path, low)
            # a second, otherwise identical record with 10 more: 10 + 10 must not make 20
            second = path.with_name("E019-r9999.json")
            half = json.loads(path.read_text(encoding="utf-8"))
            half["run_id"] = "E019-r9999"
            second.write_text(json.dumps(half), encoding="utf-8")
            manifest = Path(tmp) / "evidence" / "E019" / "play"
            shutil.copy(manifest / f"{path.stem}.manifest.json", manifest / "E019-r9999.manifest.json")
            errors = check(tmp)
            self.assertTrue(any(e.startswith("Q-UI-16: count attacks reached 10") for e in errors), errors)

    # R6: citations are checked on every record, aborted ones included
    def test_r6_an_aborted_record_citing_a_script_outside_the_inventory_is_refused(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-05")[0]

            def abort_and_cite(record):
                record["status"] = "aborted: game-died: test"
                record["observations"].append({"step": 5, "source": "static", "field": "static sources cited",
                                               "value": "BehaviorScript 999 / nope()"})
            rewrite(path, abort_and_cite)
            errors = check(tmp)
            self.assertTrue(any("(Q-UI-05)" in e and "BehaviorScript 999" in e for e in errors), errors)
            self.assertTrue(any(e.startswith("Q-UI-05: no completed record") for e in errors), errors)

    def test_r6_an_aborted_record_of_the_wrong_set_or_without_a_manifest_is_refused(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-05")[0]
            rewrite(path, lambda r: r.update(status="aborted: game-died: test",
                                             artifact={"set": "iw-dos-3.1-30121376", "variant": None}))
            (Path(tmp) / "evidence" / "E019" / "board-pieces" / f"{path.stem}.manifest.json").unlink()
            errors = [e for e in check(tmp) if "(Q-UI-05)" in e]
            self.assertTrue(any("artifact set" in e for e in errors), errors)
            self.assertTrue(any("manifest" in e for e in errors), errors)

    # R7: the recorder writes no absence statement
    def test_r7_the_absence_tour_read_is_the_screenshots_and_nothing_more(self):
        (path, record), = records_of(recorded_tree(), "Q-UI-14")
        values = [o["value"] for o in record["observations"] if o["field"] == "read: absence-tour"]
        self.assertEqual(len(values), 1)
        tour = json.loads(values[0])
        self.assertEqual(set(tour), {"screenshots", "count"})
        self.assertEqual(tour["count"], len(tour["screenshots"]))
        self.assertGreaterEqual(tour["count"], 9)

    def test_r7_no_recorder_value_asserts_an_absence_or_an_identification(self):
        """The class: across every walk's record, no value the recorder wrote states that something
        was seen, confirmed or identified."""
        words = ("confirmed", " seen", "no list-of-events", "award notice", "centre moves =", "events =")
        for path in sorted((recorded_tree() / "runs" / "E019").glob("*/E019-r*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            for o in record["observations"]:
                for word in words:
                    self.assertNotIn(word, o["value"], f"{path.name} {o['field']}")


# --- the checker's other refusals (round 1's classes), on the recorder's own tree -----------------

class CheckCatalogueTest(unittest.TestCase):

    def test_a_missing_question_fails_by_id(self):
        with Copy() as tmp:
            for path, _ in records_of(tmp, "Q-UI-06"):
                path.unlink()
            self.assertTrue(any(e.startswith("Q-UI-06: no completed record") for e in check(tmp)))

    def test_an_aborted_record_does_not_count_as_coverage(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-13")[0]
            rewrite(path, lambda r: r.update(status="aborted: game-died: test"))
            errors = check(tmp)
            self.assertTrue(any(e.startswith("Q-UI-13: no completed record") and "aborted" in e for e in errors))

    def test_a_count_below_the_target_fails(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-04")[0]

            def low(record):
                for o in record["observations"]:
                    if o["field"] == "count: distinct screenshots":
                        o["value"] = "2"
            rewrite(path, low)
            self.assertTrue(any(e.startswith("Q-UI-04: count distinct screenshots reached 2") for e in check(tmp)))

    def test_a_count_that_is_not_a_number_or_is_given_twice_fails(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-16")[0]
            rewrite(path, lambda r: r["observations"].append(
                {"step": 999, "source": "screen", "field": "count: attacks", "value": "5"}))
            self.assertTrue(any("(Q-UI-16)" in e and "one wanted" in e for e in check(tmp)))

    def test_an_observation_that_is_not_the_recorders_summary_fails(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-10")[0]

            def hand_written(record):
                for o in record["observations"]:
                    if o["field"] == "observation":
                        o["value"] = "the walk looked fine"
            rewrite(path, hand_written)
            self.assertTrue(any("(Q-UI-10)" in e and "summary" in e for e in check(tmp)))

    def test_an_observation_naming_a_screenshot_the_record_lacks_fails(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-01")[0]

            def extra(record):
                for o in record["observations"]:
                    if o["field"] == "observation":
                        summary = json.loads(o["value"])
                        summary["screenshots"].append("invented.png")
                        o["value"] = json.dumps(summary)
            rewrite(path, extra)
            self.assertTrue(any("(Q-UI-01)" in e and "invented.png" in e for e in check(tmp)))

    def test_a_record_without_its_manifest_fails(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-04")[0]
            (Path(tmp) / "evidence" / "E019" / "title-options" / f"{path.stem}.manifest.json").unlink()
            self.assertTrue(any("(Q-UI-04)" in e and "manifest" in e for e in check(tmp)))

    def test_an_output_missing_from_its_manifest_fails(self):
        with Copy() as tmp:
            path, record = records_of(tmp, "Q-UI-04")[0]
            manifest = Path(tmp) / "evidence" / "E019" / "title-options" / f"{path.stem}.manifest.json"
            doc = json.loads(manifest.read_text(encoding="utf-8"))
            doc["files"] = [f for f in doc["files"] if f["name"] != "before.png"]
            manifest.write_text(json.dumps(doc), encoding="utf-8")
            self.assertTrue(any("(Q-UI-04)" in e and "before.png" in e and "manifest" in e for e in check(tmp)))

    def test_a_pending_f020_section_fails(self):
        with Copy() as tmp:
            write_f020(tmp, status_of={"Q-UI-04": "pending the walk"})
            self.assertTrue(any(e.startswith("Q-UI-04: F020") for e in check(tmp, f020=True)))

    def test_an_observed_proxied_section_is_refused(self):
        for qid in sorted(PROXIED):
            with self.subTest(qid=qid), Copy() as tmp:
                write_f020(tmp, status_of={qid: "observed"})
                self.assertTrue(any(e.startswith(f"{qid}: F020 is observed") for e in check(tmp, f020=True)))

    def test_a_record_of_the_wrong_artifact_set_is_refused(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-08")[0]
            rewrite(path, lambda r: r["artifact"].update(set="iw-dos-3.1-30121376"))
            self.assertTrue(any("artifact set" in e and "iw-dos" in e for e in check(tmp)))

    def test_the_successor_set_is_the_one_the_loss_walks_must_use(self):
        with Copy() as tmp:
            path, record = records_of(tmp, "Q-UI-04")[0]
            self.assertEqual(record["artifact"]["set"], e019_records.ARTIFACT_SET_SAVED_FILES)
            rewrite(path, lambda r: r["artifact"].update(set=e019_records.ARTIFACT_SET))
            self.assertTrue(any("(Q-UI-04)" in e and "artifact set" in e for e in check(tmp)))

    def test_a_record_with_the_wrong_variant_is_refused(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-08")[0]
            rewrite(path, lambda r: r["artifact"].update(variant="registered"))
            self.assertTrue(any("variant" in e for e in check(tmp)))

    def test_a_manifest_of_the_wrong_artifact_set_is_refused(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-08")[0]
            manifest = Path(tmp) / "evidence" / "E019" / "play" / f"{path.stem}.manifest.json"
            doc = json.loads(manifest.read_text(encoding="utf-8"))
            doc["artifact"]["set"] = "iw-dos-3.1-30121376"
            manifest.write_text(json.dumps(doc), encoding="utf-8")
            self.assertTrue(any("artifact set" in e and "iw-dos" in e for e in check(tmp)))

    def test_a_record_in_the_wrong_batch_folder_is_refused(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-08")[0]
            other = Path(tmp) / "runs" / "E019" / "events-end"
            shutil.move(str(path), str(other / path.name))
            self.assertTrue(any("sits in events-end" in e for e in check(tmp)))


class RecorderUnitTest(unittest.TestCase):
    def test_a_shot_step_increments_the_live_screenshot_count(self):
        ctx = run_walk.Ctx(dict(walks.WALKS["Q-UI-14"], qid="Q-UI-14"))
        session = mock.Mock()
        run_walk.perform(session, ctx, "shot something")
        self.assertEqual((ctx.shots, ctx.shot_names), (1, ["something.png"]))

    def test_a_click_any_group_increments_the_attempt_count(self):
        ctx = run_walk.Ctx(dict(walks.WALKS["Q-UI-09"], qid="Q-UI-09"))
        run_walk.perform(mock.Mock(), ctx, "click-any? 400 300 100 100 700 200")
        self.assertEqual(ctx.attempts, 1)

    def test_distinct_shots_counts_distinct_pixels_not_shots(self):
        ctx = run_walk.Ctx(dict(walks.WALKS["Q-UI-04"], qid="Q-UI-04"))
        ctx.shot_names = ["a.png", "b.png", "c.png"]
        session = mock.Mock()
        session.obs = [{"field": "a.png raw RGB8 pixels sha256", "value": "1" * 64},
                       {"field": "b.png raw RGB8 pixels sha256", "value": "1" * 64},
                       {"field": "c.png raw RGB8 pixels sha256", "value": "2" * 64}]
        self.assertEqual(run_walk.measured_count(session, ctx), 2)


if __name__ == "__main__":
    unittest.main()
