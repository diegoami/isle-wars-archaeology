"""E019 (T24): the UI-walk recorder's spec, its records, and the catalogue check.

Tests here need no game, no display and no Wine: the walk table, the pixel helpers and
check_ui_catalogue are exercised against fixtures, the questions map and the E008 inventory.
The recorder command itself (run_walk.py) needs the install; the main session runs it ([C3]).
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "experiments" / "E019-pro-ui"))

import walks  # noqa: E402
import pixels  # noqa: E402
import records as e019_records  # noqa: E402
import check_ui_catalogue  # noqa: E402
import run_walk  # noqa: E402
import test_runs  # noqa: E402  (the amended record-layout rule)

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
PROXIED = {"Q-UI-07"}   # its row target is proxied by a measured field, so F020 is narrowed


def catalogue_ids():
    rows = walks.question_rows(QUESTIONS)
    return [qid for qid in rows if qid.startswith("Q-UI-")] + ["Q-PLY-04"]


def obs(step, field, value, source="screen"):
    return {"step": step, "source": source, "field": field, "value": str(value)}


def synthetic_record(run_id, qid, batch, status="completed", counts=True, timing=True,
                     observation=True, count_value=None, extra_observations=(), outputs=()):
    """One E019 record as the recorder writes it, for one question, with the observations its
    spec's check reads."""
    spec = walks.WALKS[qid]
    observations = [obs(0, "walk question", qid, "static"),
                    obs(0, "walk batch", batch, "static"),
                    obs(0, "speed setting", "normal (the unlocked default; timings normalised to it)", "static")]
    if observation:
        observations.append(obs(99, "observation", f"the {qid} walk recorded its screens and reads", "screen"))
    if counts and spec.get("count"):
        declared = spec["count"]
        field = declared.get("measured", declared["word"])
        value = count_value if count_value is not None else declared["at_least"]
        observations.append(obs(98, f"count: {field}", value))
        if field != declared["word"]:
            observations.append(obs(98, f"count note: {declared['word']}",
                                    f"the walk measures {field!r}, not {declared['word']!r}", "static"))
    if timing and spec.get("timing"):
        observations.append(obs(97, "timing: walk watch", "12.34 s between changes"))
    for kind, minimum in spec.get("reads", {}).items():
        for i in range(minimum):
            observations.append(obs(90 + i, f"read: {kind}", "0123456789abcdef" * 4))
    if spec.get("hit_areas"):
        observations.append(obs(89, "hit-area: bottom-bar labels", "41 of 70 points reacted"))
    observations.extend(extra_observations)
    if not outputs:
        outputs = [{"name": "before.png", "sha256": "ab" * 32, "store": "release:E019"},
                   {"name": "after.png", "sha256": "cd" * 32, "store": "release:E019"}]
        for i, state in enumerate(spec.get("states", [])):
            outputs.append({"name": f"state-{state}.png", "sha256": f"{i:02x}" * 32,
                            "store": "release:E019"})
    return {
        "schema": "run/1",
        "run_id": run_id,
        "experiment": "E019",
        "arm": e019_records.arm_of_question(qid),
        "rep": 1,
        "code_commit": "0" * 12,
        "machine": "local",
        "artifact": {"set": e019_records.artifact_set_for(spec), "variant": None},
        "runtime": {"driver": "experiments/E019-pro-ui/run_walk.py@000000000000", "platform": "test",
                    "fingerprint": {"wine": "test"}},
        "interventions": [{"level": "I1", "what": "screenshots of the display and read-only reads"}],
        "start_state": {"id": "S-cold-prefix-title", "sha256": "0" * 64, "restore": "test"},
        "seed": None,
        "actions": {"script": "experiments/E019-pro-ui/run_walk.py", "sha256": "0" * 64, "args": []},
        "observations": observations,
        "outputs": outputs,
        "started": "2026-10-07T00:00:00Z",
        "ended": "2026-10-07T00:01:00Z",
        "status": status,
    }


def synthetic_manifest(run_id, outputs, set_id):
    return {"schema": "evidence-manifest/1", "run_id": run_id, "experiment": "E019",
            "store": "release:E019", "artifact": {"set": set_id, "variant": None},
            "files": [{"name": o["name"], "bytes": 1, "sha256": o["sha256"],
                       "asset": f"{o['sha256'][:16]}-{o['name']}", "class": "screenshot"}
                      for o in outputs]}


def write_f020(root, observed=(), status_of=None):
    """A minimal F020 with one section per catalogue question; `observed` lists the ids whose
    Observation line carries a real status, the rest stay pending."""
    lines = ["# F020 UI observations catalogue (structure)", "", "## Observations", ""]
    for qid in catalogue_ids():
        lines.append(f"#### {qid} question text")
        if status_of and qid in status_of:
            status = status_of[qid]
        elif qid in PROXIED:
            status = "narrowed"
        elif qid in observed:
            status = "observed"
        elif qid in STATIC_ONLY:
            status = "static-only"
        else:
            status = "pending the [C3] walk"
        lines.append(f"- **Observation**: {status}: described from the recorded files.")
        lines.append("")
    path = Path(root) / "findings" / "F020-pro-ui-observations.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def build_tmp_tree(tmp, missing=(), aborted=(), low_count=False, no_observation=(),
                   drop_manifest=(), status_of=None):
    """A runs/evidence/findings tree with one synthetic record per catalogue question."""
    tmp = Path(tmp)
    for number, qid in enumerate(catalogue_ids(), start=1):
        if qid in missing:
            continue
        batch = walks.WALKS[qid]["batch"]
        run_id = f"E019-r{number:04d}"
        record = synthetic_record(run_id, qid, batch,
                                  status="aborted: game-died: test" if qid in aborted else "completed",
                                  observation=qid not in no_observation,
                                  count_value=(0 if low_count and walks.WALKS[qid].get("count") else None))
        folder = tmp / "runs" / "E019" / batch
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{run_id}.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
        if qid not in drop_manifest:
            evidence = tmp / "evidence" / "E019" / batch
            evidence.mkdir(parents=True, exist_ok=True)
            (evidence / f"{run_id}.manifest.json").write_text(
                json.dumps(synthetic_manifest(run_id, record["outputs"],
                                              e019_records.artifact_set_for(walks.WALKS[qid])), indent=1),
                encoding="utf-8")
    return write_f020(tmp, observed=set(catalogue_ids()) - set(missing) - set(aborted), status_of=status_of)


class WalkTableTest(unittest.TestCase):
    def test_every_catalogue_question_has_a_walk_spec_in_the_batches_of_the_task(self):
        ids = catalogue_ids()
        self.assertEqual(len(ids), 23)
        self.assertEqual([name for name, _ in walks.BATCHES], [name for name, _ in BRIEF_BATCHES])
        for (name, qids), (want_name, want_qids) in zip(walks.BATCHES, BRIEF_BATCHES):
            self.assertEqual(qids, want_qids, name)
        self.assertEqual(set(walks.WALKS), set(ids))

    def test_every_spec_belongs_to_the_batch_that_names_it(self):
        for qid, spec in walks.WALKS.items():
            batch = dict(walks.BATCHES)[spec["batch"]]
            self.assertIn(qid, batch, qid)

    def test_targets_come_from_the_question_rows(self):
        rows = walks.question_rows(QUESTIONS)
        for qid, spec in walks.WALKS.items():
            cell = rows[qid]["corroboration"]
            if spec.get("count"):
                if "at least" in cell:
                    # the row's own "at least N <word>" is the target, in the row's words
                    import re
                    m = re.search(r"at least (\d+) ([a-z ]+)", cell)
                    self.assertEqual(spec["count"]["word"], m.group(2).strip(), qid)
                    self.assertEqual(spec["count"]["at_least"], int(m.group(1)), qid)
            self.assertEqual(spec.get("timing") == "frame-timed", qid in FRAME_TIMED, qid)
            self.assertEqual(bool(spec.get("hit_areas")), qid in HIT_AREAS, qid)

    def test_the_frame_timed_and_hit_area_questions_are_exactly_the_task_names(self):
        timed = {qid for qid, spec in walks.WALKS.items() if spec.get("timing") == "frame-timed"}
        areas = {qid for qid, spec in walks.WALKS.items() if spec.get("hit_areas")}
        self.assertEqual(timed, FRAME_TIMED)
        self.assertEqual(areas, HIT_AREAS)

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
            lines = walks.step_lines(spec)
            has_plan = lines or spec.get("sizes") or any(a[0] == "composite" for a in spec["actions"])
            self.assertTrue(has_plan, f"{qid}: a walk with neither steps, sizes nor a composite")
            for line in lines:
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
        # a 10x8 field, background 200, with a 3-row band of dark "text" and a 1-row band below
        def px(x, y):
            if 2 <= y <= 4 and 1 <= x <= 8:
                return (30, 30, 30)
            if y == 6 and 1 <= x <= 8:
                return (30, 30, 30)
            return (200, 200, 200)
        data = self.rgb(10, 8, px)
        result = pixels.text_rows(data, 10, tol=40)
        self.assertEqual(result["boxes"], 2)
        self.assertEqual(result["heights"], [3, 1])

    def test_hover_points_steps_a_grid_inside_the_rectangle(self):
        points = pixels.hover_points((470, 515, 40, 20), step=10, ys=(525, 535))
        self.assertEqual(points, [(470, 525), (480, 525), (490, 525), (500, 525),
                                  (470, 535), (480, 535), (490, 535), (500, 535)])


class RecordLayoutTest(unittest.TestCase):
    def test_a_batch_folder_record_sits_at_its_batch_and_is_valid(self):
        # the amendment under test: runs/E019/<batch>/E019-r0001.json
        path = ROOT / "runs" / "E019" / "title-options" / "E019-r9999.json"
        self.assertEqual(test_runs.record_experiment(path), "E019")

    def test_a_record_still_must_sit_under_its_own_experiment(self):
        doc_text = (ROOT / "runs" / "E004" / "E004-r0062.json").read_text(encoding="utf-8")
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "runs" / "E019" / "title-options"
            folder.mkdir(parents=True)
            path = folder / "E002-r0001.json"
            path.write_text(doc_text, encoding="utf-8")
            errors = test_runs.run_record_errors(path, None)
        self.assertTrue(any("experiment" in e and "E004" in e for e in errors), errors)
        self.assertEqual(json.loads(doc_text)["experiment"], "E004")

    def test_deeper_nesting_is_refused(self):
        path = ROOT / "runs" / "E019" / "a" / "b" / "E019-r0001.json"
        self.assertIsNone(test_runs.record_experiment(path))

    def test_paths_of_a_record_and_its_manifest(self):
        self.assertEqual(e019_records.record_paths("play", "E019-r0007"),
                         {"run": "runs/E019/play/E019-r0007.json",
                          "manifest": "evidence/E019/play/E019-r0007.manifest.json"})

    def test_arm_and_question_round_trip(self):
        self.assertEqual(e019_records.arm_of_question("Q-UI-04"), "q-ui-04")
        self.assertEqual(e019_records.question_of_arm("q-ui-04"), "Q-UI-04")
        self.assertEqual(e019_records.question_of_arm("q-ply-04"), "Q-PLY-04")


class CheckCatalogueTest(unittest.TestCase):
    def run_check(self, tmp):
        return check_ui_catalogue.run_checks(Path(tmp), questions_path=QUESTIONS, inventory_path=INVENTORY)

    def test_a_complete_tree_passes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            build_tmp_tree(tmp)
            self.assertEqual(self.run_check(tmp), [])

    def test_a_missing_question_fails_by_id(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            build_tmp_tree(tmp, missing=["Q-UI-06"])
            errors = self.run_check(tmp)
            self.assertTrue(any("Q-UI-06" in e for e in errors), errors)

    def test_an_aborted_record_does_not_count_as_coverage(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            build_tmp_tree(tmp, aborted=["Q-UI-13"])
            errors = self.run_check(tmp)
            self.assertTrue(any("Q-UI-13" in e for e in errors), errors)

    def test_a_count_below_the_target_fails(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            build_tmp_tree(tmp, low_count=True)
            errors = self.run_check(tmp)
            self.assertTrue(any("count" in e for e in errors), errors)

    def test_a_record_without_an_observation_fails(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            build_tmp_tree(tmp, no_observation=["Q-UI-10"])
            errors = self.run_check(tmp)
            self.assertTrue(any("Q-UI-10" in e and "observation" in e for e in errors), errors)

    def test_a_record_without_its_manifest_fails(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            build_tmp_tree(tmp, drop_manifest=["Q-UI-04"])
            errors = self.run_check(tmp)
            self.assertTrue(any("manifest" in e for e in errors), errors)

    def test_a_pending_f020_section_fails(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            build_tmp_tree(tmp, status_of={"Q-UI-04": "pending the [C3] walk"})
            errors = self.run_check(tmp)
            self.assertTrue(any("Q-UI-04" in e and "F020" in e for e in errors), errors)

    def test_a_citation_outside_the_e008_inventory_fails(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            build_tmp_tree(tmp, status_of={})
            # a record that cites a script the inventory does not have
            record_path = next((Path(tmp) / "runs" / "E019" / "play").glob("*.json"))
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["observations"].append(obs(5, "static sources cited", "BehaviorScript 999 / `nope()`", "static"))
            record_path.write_text(json.dumps(record), encoding="utf-8")
            errors = self.run_check(tmp)
            self.assertTrue(any("BehaviorScript 999" in e for e in errors), errors)

    def test_the_real_tree_fails_while_the_walks_have_not_run(self):
        """The honest state of this round: no E019 records exist, so the check must fail,
        naming the questions still missing."""
        errors = check_ui_catalogue.run_checks(ROOT, questions_path=QUESTIONS, inventory_path=INVENTORY)
        self.assertTrue(errors)
        self.assertTrue(any("Q-UI-01" in e for e in errors), errors)

    # --- R1: a record of the wrong artifact set is never this walk's ---------------------------

    def _one_record(self, tmp):
        return next((Path(tmp) / "runs" / "E019" / "play").glob("*.json"))

    def test_a_record_of_the_wrong_artifact_set_is_refused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            build_tmp_tree(tmp)
            path = self._one_record(tmp)
            record = json.loads(path.read_text(encoding="utf-8"))
            record["artifact"]["set"] = "iw-dos-3.1-30121376"          # the known DOS set
            path.write_text(json.dumps(record), encoding="utf-8")
            errors = self.run_check(tmp)
            self.assertTrue(any("artifact set" in e and "iw-dos" in e for e in errors), errors)

    def test_the_successor_set_is_the_one_the_loss_walks_must_use(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            build_tmp_tree(tmp)
            # Q-UI-04 may write xtras/Islepro.skr (may_write_saved_files): its base set must fail
            path = next((Path(tmp) / "runs" / "E019" / "title-options").glob("E019-*.json"))
            record = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(record["artifact"]["set"], e019_records.ARTIFACT_SET_SAVED_FILES)
            record["artifact"]["set"] = e019_records.ARTIFACT_SET
            path.write_text(json.dumps(record), encoding="utf-8")
            errors = self.run_check(tmp)
            self.assertTrue(any("artifact set" in e for e in errors), errors)

    def test_a_record_with_the_wrong_variant_is_refused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            build_tmp_tree(tmp)
            path = self._one_record(tmp)
            record = json.loads(path.read_text(encoding="utf-8"))
            record["artifact"]["variant"] = "registered"
            path.write_text(json.dumps(record), encoding="utf-8")
            errors = self.run_check(tmp)
            self.assertTrue(any("variant" in e for e in errors), errors)

    def test_a_manifest_of_the_wrong_artifact_set_is_refused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            build_tmp_tree(tmp)
            manifest = next((Path(tmp) / "evidence" / "E019" / "play").glob("*.manifest.json"))
            doc = json.loads(manifest.read_text(encoding="utf-8"))
            doc["artifact"]["set"] = "iw-dos-3.1-30121376"
            manifest.write_text(json.dumps(doc), encoding="utf-8")
            errors = self.run_check(tmp)
            self.assertTrue(any("artifact set" in e and "iw-dos" in e for e in errors), errors)

    def test_a_record_without_the_seal_is_refused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            build_tmp_tree(tmp)
            path = self._one_record(tmp)
            record = json.loads(path.read_text(encoding="utf-8"))
            record["start_state"].pop("sha256")
            path.write_text(json.dumps(record), encoding="utf-8")
            errors = self.run_check(tmp)
            self.assertTrue(any("start_state" in e for e in errors), errors)

    def test_a_record_without_the_cycle_screenshots_is_refused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            build_tmp_tree(tmp)
            path = self._one_record(tmp)
            record = json.loads(path.read_text(encoding="utf-8"))
            record["outputs"] = [o for o in record["outputs"] if o["name"] != "before.png"]
            path.write_text(json.dumps(record), encoding="utf-8")
            errors = self.run_check(tmp)
            self.assertTrue(any("before.png" in e for e in errors), errors)

    # --- R2: an aborted record never covers a question -----------------------------------------

    def test_an_aborted_no_count_question_does_not_cover(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            # Q-UI-05 declares no count, so only coverage decides it; its F020 line is observed
            build_tmp_tree(tmp, aborted=["Q-UI-05"], status_of={"Q-UI-05": "observed"})
            errors = self.run_check(tmp)
            self.assertTrue(any("Q-UI-05" in e and "completed" in e for e in errors), errors)

    # --- R4: a proxied count uses its measured field and says so --------------------------------

    def _q_ui_07_record(self, tmp):
        for path in sorted((Path(tmp) / "runs" / "E019" / "events-end").glob("E019-*.json")):
            if json.loads(path.read_text(encoding="utf-8")).get("arm") == "q-ui-07":
                return path
        raise AssertionError("no Q-UI-07 record in the fixture")

    def test_a_proxied_count_must_use_its_measured_field(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            build_tmp_tree(tmp)
            path = self._q_ui_07_record(tmp)
            record = json.loads(path.read_text(encoding="utf-8"))
            for o in record["observations"]:
                if o["field"] == "count: centre-flash candidates":
                    o["field"] = "count: centre moves"       # the old, unsupported claim
            path.write_text(json.dumps(record), encoding="utf-8")
            errors = self.run_check(tmp)
            self.assertTrue(any("Q-UI-07" in e and "centre-flash candidates" in e for e in errors),
                            errors)

    def test_a_proxied_count_without_a_note_is_refused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            build_tmp_tree(tmp)
            path = self._q_ui_07_record(tmp)
            record = json.loads(path.read_text(encoding="utf-8"))
            record["observations"] = [o for o in record["observations"]
                                      if not o["field"].startswith("count note:")]
            path.write_text(json.dumps(record), encoding="utf-8")
            errors = self.run_check(tmp)
            self.assertTrue(any("count note" in e for e in errors), errors)

    def test_an_observed_proxied_section_is_refused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            build_tmp_tree(tmp, status_of={"Q-UI-07": "observed"})
            errors = self.run_check(tmp)
            self.assertTrue(any("Q-UI-07" in e and "proxy" in e for e in errors), errors)


class RecorderCountsTest(unittest.TestCase):
    """The recorder emits a `count:` for every declared target, and never claims an identification
    its pixels cannot make (the classes of R3 and R4)."""

    class FakeSession:
        def __init__(self):
            self.observed = []

        def observe(self, step, source, field, value):
            self.observed.append({"field": field, "value": str(value)})

        def perform(self, line):
            pass

    def stamp(self, qid):
        spec = dict(walks.WALKS[qid], qid=qid)
        ctx = run_walk.Ctx(spec)
        declared = spec.get("count") or {}
        target = declared.get("at_least", 0)
        measure = declared.get("measure")
        if measure == "shots":
            ctx.shots = target
        elif measure == "attempts":
            ctx.attempts = target
        elif measure == "labels":
            ctx.labels = {f"label-{i}" for i in range(target)}
        elif measure:
            ctx.counts[measure] = target
        session = self.FakeSession()
        run_walk.stamp_walk_summaries(session, ctx)
        return session.observed

    def test_every_declared_count_target_is_emitted(self):
        for qid, spec in walks.WALKS.items():
            declared = spec.get("count")
            if not declared:
                continue
            with self.subTest(qid=qid):
                field = declared.get("measured", declared["word"])
                fields = [o["field"] for o in self.stamp(qid)]
                self.assertIn(f"count: {field}", fields, qid)

    def test_a_proxied_count_uses_the_measured_word_and_carries_a_note(self):
        fields = [o["field"] for o in self.stamp("Q-UI-07")]
        self.assertIn("count: centre-flash candidates", fields)
        self.assertIn("count note: centre moves", fields)
        self.assertNotIn("count: centre moves", fields)

    def test_the_declared_shots_target_is_reachable_by_the_walks_own_shots(self):
        """A `shots` target must not exceed the shots the walk's actions actually take (the R3
        class: a target the recorder cannot produce). Runtime shot counts (Q-UI-15's awards) are
        the walk's own report and are not previewed here."""
        def planned_shots(spec):
            shots = sum(1 for kind, *rest in spec["actions"]
                        if kind == "step" and rest[0].startswith("shot "))
            for kind, *rest in spec["actions"]:
                if kind == "composite" and rest[0] == "computer_turns" and rest[1].get("shots", True):
                    shots += rest[1].get("passes", 1)
            return shots

        for qid, spec in walks.WALKS.items():
            declared = spec.get("count") or {}
            if declared.get("measure") != "shots":
                continue
            composites = {a[1] for a in spec["actions"] if a[0] == "composite"}
            if "card_turns" in composites:
                continue                      # award shots depend on the deal, reported at run time
            with self.subTest(qid=qid):
                self.assertGreaterEqual(planned_shots(spec), declared["at_least"], qid)

    def test_a_shot_step_increments_the_live_screenshot_count(self):
        ctx = run_walk.Ctx(dict(walks.WALKS["Q-UI-14"], qid="Q-UI-14"))
        run_walk.perform(self.FakeSession(), ctx, "shot something")
        self.assertEqual(ctx.shots, 1)

    def test_a_click_any_group_increments_the_attempt_count(self):
        ctx = run_walk.Ctx(dict(walks.WALKS["Q-UI-09"], qid="Q-UI-09"))
        run_walk.perform(self.FakeSession(), ctx, "click-any? 400 300 100 100 700 200")
        self.assertEqual(ctx.attempts, 1)

    def test_the_recorder_and_the_driver_agree_on_the_artifact_sets(self):
        sys.path.insert(0, str(ROOT / "runtime" / "iwp" / "spike"))
        import cycle as spike  # noqa: E402
        self.assertEqual(e019_records.ARTIFACT_SET, spike.SET_ID)
        self.assertEqual(e019_records.ARTIFACT_SET_SAVED_FILES, spike.SUCCESSOR2_ID)


if __name__ == "__main__":
    unittest.main()
