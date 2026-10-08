"""Tests for tools/check_counts.py (T38, Done-when 8).

The count checker reads the batch list's targets and the committed records' structural `field`
values. These tests use synthetic records only; they pin the Scope Counts line: batch 1 at least
100 exchanges with before/after counters for both sides, batch 2 at least 9 computer bomb plays
across at least 3 games, and no `corroborated` outcome below the f011 target.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_counts  # noqa: E402

BATCHES = check_counts.load_batches(check_counts.SCENARIOS)
EXCHANGE_FIELDS = ("counter:attacker-before", "counter:attacker-after",
                   "counter:defender-before", "counter:defender-after")


def write_batch(root, batch, records):
    folder = Path(root) / batch
    folder.mkdir(parents=True, exist_ok=True)
    for i, doc in enumerate(records, 1):
        (folder / f"E020-r{i:04d}.json").write_text(json.dumps(doc), encoding="utf-8")


def exchange_record(run_id, exchanges=1):
    observations = []
    for i in range(exchanges):
        for field in EXCHANGE_FIELDS:
            observations.append({"step": i, "source": "screen", "field": field, "value": "3"})
    return {"schema": "run/1", "run_id": run_id, "arm": "cmb-accumulation", "observations": observations}


def bomb_record(run_id, plays=1):
    observations = []
    for i in range(plays):
        for field, value in (("owner:victim", "red"), ("counter:victim-before", "4"),
                             ("counter:victim-after", "3"), ("hand:bomber", "6")):
            observations.append({"step": i, "source": "screen", "field": field, "value": value})
    return {"schema": "run/1", "run_id": run_id, "arm": "bomb-sampling", "observations": observations}


class CheckCountsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def check(self, batch):
        return check_counts.check_batch(batch, BATCHES[batch], self.root)

    def test_batch_1_at_the_floor_passes(self):
        write_batch(self.root, "cmb-accumulation", [exchange_record("E020-r0001", 100)])
        problems, lines = self.check("cmb-accumulation")
        self.assertEqual(problems, [], lines)

    def test_batch_1_one_under_the_floor_fails(self):
        write_batch(self.root, "cmb-accumulation", [exchange_record("E020-r0001", 99)])
        problems, _ = self.check("cmb-accumulation")
        self.assertTrue(any("100" in p for p in problems), problems)

    def test_an_incomplete_exchange_fails(self):
        record = exchange_record("E020-r0001", 100)
        record["observations"] = [o for o in record["observations"]
                                  if o["field"] != "counter:defender-after"]
        write_batch(self.root, "cmb-accumulation", [record])
        problems, _ = self.check("cmb-accumulation")
        self.assertTrue(any("defender-after" in p or "both sides" in p for p in problems), problems)

    def test_corroborated_below_the_f011_target_fails(self):
        write_batch(self.root, "cmb-accumulation", [exchange_record("E020-r0001", 100)])
        (self.root / "cmb-accumulation" / "outcome.json").write_text(
            json.dumps({"outcome": "corroborated"}), encoding="utf-8")
        problems, _ = self.check("cmb-accumulation")
        self.assertTrue(any("corroborated" in p for p in problems), problems)

    def test_corroborated_at_the_f011_target_passes(self):
        write_batch(self.root, "cmb-accumulation", [exchange_record("E020-r0001", 500)])
        (self.root / "cmb-accumulation" / "outcome.json").write_text(
            json.dumps({"outcome": "corroborated"}), encoding="utf-8")
        problems, lines = self.check("cmb-accumulation")
        self.assertEqual(problems, [], lines)

    def test_batch_2_nine_plays_across_three_games_passes(self):
        write_batch(self.root, "bomb-sampling",
                    [bomb_record("E020-r0001", 3), bomb_record("E020-r0002", 3), bomb_record("E020-r0003", 3)])
        problems, lines = self.check("bomb-sampling")
        self.assertEqual(problems, [], lines)

    def test_batch_2_nine_plays_in_two_games_fails(self):
        write_batch(self.root, "bomb-sampling",
                    [bomb_record("E020-r0001", 5), bomb_record("E020-r0002", 4)])
        problems, _ = self.check("bomb-sampling")
        self.assertTrue(any("games" in p for p in problems), problems)

    def test_batch_2_under_the_play_floor_fails(self):
        write_batch(self.root, "bomb-sampling",
                    [bomb_record("E020-r0001", 3), bomb_record("E020-r0002", 3), bomb_record("E020-r0003", 2)])
        problems, _ = self.check("bomb-sampling")
        self.assertTrue(any("bomb plays" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main(verbosity=2)
