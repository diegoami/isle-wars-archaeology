"""The E022 single-exchange mechanism and its checker flag (T44 Done-when 2).

Fails on `main` (the mechanism and `--accept-single` are absent) and passes on the branch. Synthetic
board readings only: no game, no wine, no original pixels (rule 18).

It pins: one die's single-counter drop becomes one single exchange naming the attacker and defender
(both directions), while a two-change pair, a capture, a counter rise and an ambiguous pair are never
one; the committed synthetic record is exactly the mechanism's output; and
`tools/check_counts.py --accept-single` counts that record as an exchange while the same command
without the flag refuses it.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _sub in ("tools", "experiments/E022-pro-fast-capture"):
    if str(ROOT / _sub) not in sys.path:
        sys.path.insert(0, str(ROOT / _sub))

import check_counts  # noqa: E402
import single_exchange  # noqa: E402
import build_record  # noqa: E402

SCENARIOS = ROOT / "experiments" / "E022-pro-fast-capture" / "scenarios.txt"
RECORD = ROOT / "runs" / "E022" / "synthetic" / "E022-r0001.json"


def board(**countries):
    return {int(k[1:]): v for k, v in countries.items()}


class MechanismTest(unittest.TestCase):
    def test_a_defender_losing_one_army_is_a_single_exchange(self):
        before = {1: {"army": 9, "owner": "red"}, 2: {"army": 4, "owner": "blue"}}
        after = {1: {"army": 9, "owner": "red"}, 2: {"army": 3, "owner": "blue"}}
        values, reason = single_exchange.single_exchange(before, after, "red", {1: {2}, 2: {1}})
        self.assertEqual(reason, "single")
        self.assertEqual(values, {"counter:attacker-before": "9", "counter:attacker-after": "9",
                                  "counter:defender-before": "4", "counter:defender-after": "3",
                                  "country:attacker": "1", "country:defender": "2",
                                  "owner:attacker": "red", "owner:defender": "blue", "single:rank": "1"})

    def test_an_attacker_losing_one_army_is_a_single_exchange(self):
        before = {1: {"army": 4, "owner": "red"}, 2: {"army": 9, "owner": "blue"}}
        after = {1: {"army": 3, "owner": "red"}, 2: {"army": 9, "owner": "blue"}}
        values, reason = single_exchange.single_exchange(before, after, "red", {1: {2}, 2: {1}})
        self.assertEqual(reason, "single")
        self.assertEqual((values["country:attacker"], values["country:defender"]), ("1", "2"))
        self.assertEqual((values["counter:attacker-before"], values["counter:attacker-after"]), ("4", "3"))

    def test_a_two_change_pair_is_never_one(self):
        before = {1: {"army": 9, "owner": "red"}, 2: {"army": 4, "owner": "blue"}}
        after = {1: {"army": 8, "owner": "red"}, 2: {"army": 3, "owner": "blue"}}
        self.assertEqual(single_exchange.single_exchange(before, after, "red", {1: {2}, 2: {1}})[1],
                         "many-changes")

    def test_a_capture_a_rise_and_an_ambiguous_pair_are_never_one(self):
        capture = ({1: {"army": 9, "owner": "red"}, 2: {"army": 1, "owner": "blue"}},
                   {1: {"army": 9, "owner": "red"}, 2: {"army": 0, "owner": "red"}})
        rise = ({1: {"army": 9, "owner": "red"}, 2: {"army": 4, "owner": "blue"}},
                {1: {"army": 9, "owner": "red"}, 2: {"army": 5, "owner": "blue"}})
        adj = {1: {2}, 2: {1}}
        self.assertEqual(single_exchange.single_exchange(*capture, "red", adj)[1], "ownership-change")
        self.assertEqual(single_exchange.single_exchange(*rise, "red", adj)[1], "counter-rise")
        # the defender 3 borders two seat-owned countries (1 and 4): the pair is ambiguous
        before = {1: {"army": 9, "owner": "red"}, 3: {"army": 4, "owner": "blue"},
                  4: {"army": 6, "owner": "red"}}
        after = {1: {"army": 9, "owner": "red"}, 3: {"army": 3, "owner": "blue"},
                 4: {"army": 6, "owner": "red"}}
        self.assertEqual(single_exchange.single_exchange(before, after, "red", {1: {3}, 3: {1, 4}, 4: {3}})[1],
                         "many-attackers")


class RecordAndCheckerTest(unittest.TestCase):
    def test_the_committed_record_is_the_mechanism_output(self):
        values, reason = single_exchange.single_exchange(build_record.BEFORE, build_record.AFTER,
                                                         build_record.SEAT, build_record.ADJACENCY)
        self.assertEqual(reason, "single")
        doc = json.loads(RECORD.read_text(encoding="utf-8"))
        read = {o["field"]: o["value"] for o in doc["observations"] if "field" in o and o["step"] == 1}
        self.assertEqual({f: read[f] for f in values}, values)

    def run_check(self, *extra):
        return subprocess.run([sys.executable, str(ROOT / "tools" / "check_counts.py"),
                               "--experiment", "E022", *extra, str(SCENARIOS)],
                              cwd=ROOT, capture_output=True, text=True)

    def test_accept_single_counts_the_single_exchange(self):
        done = self.run_check("--accept-single")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("observed 1", done.stdout)

    def test_without_the_flag_the_single_exchange_is_refused(self):
        done = self.run_check()
        self.assertNotEqual(done.returncode, 0, done.stdout)
        self.assertIn("pass --accept-single", done.stdout)
        self.assertIn("observed 0", done.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
