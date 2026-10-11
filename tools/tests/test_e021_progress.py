"""Synthetic record tests for T45's once-per-cell progress number."""
import tempfile
import unittest
from pathlib import Path

import e021_fixtures as fx
import e021_progress as progress


class ProgressTest(unittest.TestCase):
    def test_cells_are_deduplicated_within_and_across_records(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = [fx.write_record(directory, fx.record("E021-r0001", [
                (1, {"case:kind": "even", "cell:ordinal": "1"}, []),
                (2, {"case:kind": "even", "cell:ordinal": "1"}, []),
                (3, {"case:kind": "tiny", "cell:ordinal": "1"}, []),
            ])), fx.write_record(directory, fx.record("E021-r0002", [
                (1, {"case:kind": "even", "cell:ordinal": "1"}, []),
                (2, {"case:kind": "busy", "cell:ordinal": "2", "counter:fights": "3"}, []),
            ]))]
            result = progress.count(paths)
            self.assertEqual(result["met"], 3)
            self.assertEqual(result["total"], 40)
            self.assertEqual(result["rows"]["even"]["cells"], [1])
            self.assertEqual(result["rows"]["even"]["unmet"], list(range(2, 17)))
            self.assertEqual(result["rows"]["busy"]["unmet"], [1] + list(range(3, 11)))
            self.assertEqual(sum(row["met"] for row in result["rows"].values()), 3)

    def test_busy_and_quit_count_only_with_the_fights_their_group_carries(self):
        # round 2, point 4: E021-r0001's busy groups carry battles opened and left, no fights
        doc = fx.record("E021-r0001", [
            (1, {"case:kind": "busy", "cell:ordinal": "1", "counter:battles": "12", "end:turn": "pass"}, []),
            (2, {"case:kind": "busy", "cell:ordinal": "2", "counter:battles": "5", "counter:fights": "2"}, []),
            (3, {"case:kind": "busy", "cell:ordinal": "3", "counter:battles": "4", "counter:fights": "3"}, []),
            (4, {"case:kind": "quit", "cell:ordinal": "1"}, []),
            (5, {"case:kind": "quit", "cell:ordinal": "2", "counter:fought": "1"}, []),
            (6, {"case:kind": "even", "cell:ordinal": "1", "counter:battle": "0"}, []),
        ])
        self.assertEqual(progress.cells_of_record(doc), {("busy", 3), ("quit", 2), ("even", 1)})

    def test_the_committed_first_sitting_counts_13_not_23(self):
        # E021-r0001 as committed (rule 20: never edited): progress-r01 counted 23, the busy row
        # 10 of them; read with the rule above it is 13 (measurements/CORRECTIONS.md)
        path = fx.ROOT / "runs" / "E021" / "session-a" / "E021-r0001.json"
        result = progress.count([path])
        self.assertEqual(result["rows"]["busy"]["met"], 0)
        self.assertEqual(result["met"], 13)

    def test_other_experiments_cannot_credit_session_a(self):
        with tempfile.TemporaryDirectory() as directory:
            path = fx.write_record(directory, fx.record("E020-r0001", [
                (1, {"case:kind": "even", "cell:ordinal": "1"}, []),
            ], experiment="E020"))
            with self.assertRaises(progress.ProgressRefused):
                progress.count([path])

    def test_next_snapshot_preserves_previous_bytes_and_resumes_cells(self):
        with tempfile.TemporaryDirectory() as directory:
            doc = progress.count([])
            first = progress.write_next(doc, directory)
            before = first.read_bytes()
            second = progress.write_next(doc, directory)
            self.assertEqual(first.name, "progress-r01.json")
            self.assertEqual(second.name, "progress-r02.json")
            self.assertEqual(first.read_bytes(), before)
            self.assertEqual(progress.load_latest(directory), doc)
            self.assertEqual(len(progress.needed_from(doc)), 40)

    def test_invalid_or_incomplete_cells_are_refused(self):
        for fields in ({"case:kind": "even"},
                       {"case:kind": "even", "cell:ordinal": "17"},
                       {"case:kind": "other", "cell:ordinal": "1"}):
            with self.subTest(fields=fields):
                with self.assertRaises(progress.ProgressRefused):
                    progress.cells_of_record(fx.record("E021-r0001", [(1, fields, [])]))
