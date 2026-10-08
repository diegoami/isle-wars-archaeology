"""Tests for tools/check_counts.py (T38, Done-when 8; round 2, R6, R8, R9).

Synthetic records only. They pin what is counted: complete, uniquely identified events (one step,
every field once, valid values, two frames the record holds), identities by sitting, game and seq
(never by run id), real games, and per-arm targets per claim before `corroborated`.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e020_fixtures import BOMB, EXCHANGE, ROOT, record  # noqa: E402

import check_counts  # noqa: E402

SCENARIOS = ROOT / "experiments" / "E020-wine-first-run" / "scenarios.txt"
EXCHANGE_FIELDS = list(EXCHANGE)
BOMB_FIELDS = list(BOMB)


class CountsWorld(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.runs = self.root / "runs"
        self.scenarios = self.root / "scenarios.txt"
        self.scenarios.write_text(SCENARIOS.read_text())
        self.batches = check_counts.load_batches(self.scenarios)

    def write(self, batch, name, doc):
        folder = self.runs / batch
        folder.mkdir(parents=True, exist_ok=True)
        (folder / name).write_text(json.dumps(doc))

    def exchanges(self, n, game=1, start=1, **values):
        return [(game, start + i, dict(EXCHANGE, **values)) for i in range(n)]

    def check(self, name):
        outcomes, problems = check_counts.declared_outcomes(self.scenarios)
        batch_problems, lines = check_counts.check_batch(name, self.batches[name], outcomes, self.runs)
        return problems + batch_problems, lines

    def declare(self, **claims):
        (self.root / "outcomes.json").write_text(json.dumps(
            {"claims": {k.replace("_", "-"): {"outcome": v} for k, v in claims.items()}}))


class FloorTest(CountsWorld):
    def test_batch_1_at_the_floor_passes(self):
        self.write("cmb-accumulation", "E020-r0001.json",
                   record("cmb-accumulation", "E020-r0001", 1, self.exchanges(100), EXCHANGE_FIELDS))
        problems, lines = self.check("cmb-accumulation")
        self.assertEqual(problems, [])
        self.assertIn("observed 100", "\n".join(lines))

    def test_batch_1_one_under_the_floor_fails_and_names_the_shortfall(self):
        self.write("cmb-accumulation", "E020-r0001.json",
                   record("cmb-accumulation", "E020-r0001", 1, self.exchanges(99), EXCHANGE_FIELDS))
        problems, _ = self.check("cmb-accumulation")
        self.assertTrue(any("short of the floor of 100 by 1" in p for p in problems), problems)

    def test_an_exchange_missing_a_side_is_not_counted(self):
        doc = record("cmb-accumulation", "E020-r0001", 1, self.exchanges(100), EXCHANGE_FIELDS)
        doc["observations"] = [o for o in doc["observations"]
                               if not (o.get("step") == 1 and o.get("field") == "counter:defender-after")]
        self.write("cmb-accumulation", "E020-r0001.json", doc)
        problems, _ = self.check("cmb-accumulation")
        self.assertTrue(any("not one complete event" in p for p in problems), problems)
        self.assertTrue(any("99 exchanges" in p for p in problems), problems)

    def test_duplicated_quartets_at_one_step_are_not_a_hundred_events(self):
        """R8 (a): one hundred copies of an exchange's fields at one step."""
        doc = record("cmb-accumulation", "E020-r0001", 1, self.exchanges(1), EXCHANGE_FIELDS)
        one = [o for o in doc["observations"] if o.get("step") == 1]
        doc["observations"] = doc["observations"][:1] + one * 100
        self.write("cmb-accumulation", "E020-r0001.json", doc)
        problems, _ = self.check("cmb-accumulation")
        self.assertTrue(any("0 exchanges" in p for p in problems), problems)

    def test_the_same_event_twice_in_one_record_counts_once_and_is_a_problem(self):
        events = self.exchanges(100)
        events[1] = events[0]
        self.write("cmb-accumulation", "E020-r0001.json",
                   record("cmb-accumulation", "E020-r0001", 1, events, EXCHANGE_FIELDS))
        problems, _ = self.check("cmb-accumulation")
        self.assertTrue(any("appears twice" in p for p in problems), problems)

    def test_an_event_without_two_frames_the_record_holds_is_not_counted(self):
        doc = record("cmb-accumulation", "E020-r0001", 1, self.exchanges(100), EXCHANGE_FIELDS)
        doc["outputs"] = doc["outputs"][:1]
        self.write("cmb-accumulation", "E020-r0001.json", doc)
        problems, _ = self.check("cmb-accumulation")
        self.assertTrue(any("two distinct frames" in p for p in problems), problems)

    def test_text_in_a_value_is_refused(self):
        """R6 at the checker: a counter that is not an integer, an owner that is not a colour word."""
        for field, value in (("counter:attacker-before", "synthetic forbidden screen label"),
                             ("owner:defender", "synthetic forbidden screen label")):
            with self.subTest(field=field):
                doc = record("cmb-accumulation", "E020-r0001", 1, self.exchanges(100), EXCHANGE_FIELDS)
                for o in doc["observations"]:
                    if o.get("field") == field and o["step"] == 1:
                        o["value"] = value
                self.write("cmb-accumulation", "E020-r0001.json", doc)
                problems, _ = self.check("cmb-accumulation")
                self.assertTrue(any("forbidden screen label" in p for p in problems), problems)


class IdentityTest(CountsWorld):
    def test_owner_only_observations_over_three_run_ids_are_not_nine_bomb_plays(self):
        """R8 (b): nine `owner:victim` readings, no victim counters and no bomber hand, three records."""
        for i in range(3):
            doc = record("bomb-sampling", f"E020-r000{i + 1}", 100 + i,
                         [(1, s, dict(BOMB)) for s in range(1, 4)], ["owner:victim"])
            self.write("bomb-sampling", f"E020-r000{i + 1}.json", doc)
        problems, _ = self.check("bomb-sampling")
        self.assertTrue(any("0 bomb plays" in p for p in problems), problems)

    def test_nine_plays_across_three_games_of_one_sitting_pass(self):
        events = [(g, s, dict(BOMB)) for g in (1, 2, 3) for s in (1, 2, 3)]
        self.write("bomb-sampling", "E020-r0001.json", record("bomb-sampling", "E020-r0001", 7, events, BOMB_FIELDS))
        problems, lines = self.check("bomb-sampling")
        self.assertEqual(problems, [])
        self.assertIn("games (distinct sitting and game): target >= 3, observed 3", "\n".join(lines))

    def test_a_re_read_of_one_game_is_not_another_game(self):
        """R8: three records (three run ids) of the same sitting and game are one game, its events once."""
        events = [(1, s, dict(BOMB)) for s in range(1, 10)]
        for i in range(3):
            self.write("bomb-sampling", f"E020-r000{i + 1}.json",
                       record("bomb-sampling", f"E020-r000{i + 1}", 7, events, BOMB_FIELDS))
        problems, lines = self.check("bomb-sampling")
        self.assertIn("observed 9", lines[1])
        self.assertTrue(any("1 game(s), short of the floor of 3" in p for p in problems), problems)

    def test_two_re_reads_that_disagree_stop_the_count(self):
        a = self.exchanges(100)
        b = self.exchanges(100)
        b[0] = (1, 1, dict(EXCHANGE, **{"counter:attacker-after": "5", "counter:defender-after": "0"}))
        self.write("cmb-accumulation", "E020-r0001.json", record("cmb-accumulation", "E020-r0001", 1, a, EXCHANGE_FIELDS))
        self.write("cmb-accumulation", "E020-r0002.json", record("cmb-accumulation", "E020-r0002", 1, b, EXCHANGE_FIELDS))
        problems, _ = self.check("cmb-accumulation")
        self.assertTrue(any("disagrees" in p for p in problems), problems)

    def test_two_sittings_are_two_identities(self):
        self.write("cmb-accumulation", "E020-r0001.json",
                   record("cmb-accumulation", "E020-r0001", 1, self.exchanges(50), EXCHANGE_FIELDS))
        self.write("cmb-accumulation", "E020-r0002.json",
                   record("cmb-accumulation", "E020-r0002", 2, self.exchanges(50), EXCHANGE_FIELDS))
        problems, lines = self.check("cmb-accumulation")
        self.assertEqual(problems, [])
        self.assertIn("observed 100", lines[1])


class CorroborationTest(CountsWorld):
    def test_five_hundred_identical_readings_do_not_corroborate_the_per_arm_claims(self):
        """R9: all attacker and defender readings `3` cannot establish Q-CMB-04's or Q-CMB-05's arms."""
        events = self.exchanges(500, **{"counter:attacker-before": "3", "counter:attacker-after": "2",
                                        "counter:defender-before": "3", "counter:defender-after": "3"})
        self.write("cmb-accumulation", "E020-r0001.json", record("cmb-accumulation", "E020-r0001", 1, events, EXCHANGE_FIELDS))
        self.declare(Q_CMB_04="corroborated", Q_CMB_05="corroborated")
        problems, _ = self.check("cmb-accumulation")
        self.assertTrue(any("Q-CMB-04 is declared corroborated" in p for p in problems), problems)
        self.assertTrue(any("Q-CMB-05 is declared corroborated" in p for p in problems), problems)

    def test_q_cmb_04_corroborates_with_a_hundred_exchanges_per_attacker_size(self):
        events, seq = [], 1
        for size in (2, 3, 4, 5, 10):
            for _ in range(100):
                events.append((1, seq, dict(EXCHANGE, **{"counter:attacker-before": str(size),
                                                         "counter:attacker-after": str(size - 1)})))
                seq += 1
        self.write("cmb-accumulation", "E020-r0001.json", record("cmb-accumulation", "E020-r0001", 1, events, EXCHANGE_FIELDS))
        self.declare(Q_CMB_04="corroborated", Q_CMB_06="corroborated", Q_CMB_07="corroborated")
        problems, _ = self.check("cmb-accumulation")
        self.assertEqual(problems, [])

    def test_q_cmb_07_is_not_corroborated_by_an_exchange_with_another_outcome(self):
        events = self.exchanges(199) + [(1, 200, dict(EXCHANGE, **{"counter:attacker-after": "3"}))]
        self.write("cmb-accumulation", "E020-r0001.json", record("cmb-accumulation", "E020-r0001", 1, events, EXCHANGE_FIELDS))
        self.declare(Q_CMB_07="corroborated")
        problems, _ = self.check("cmb-accumulation")
        self.assertTrue(any("Q-CMB-07 is declared corroborated" in p for p in problems), problems)

    def split(self):
        return self.exchanges(250, **{"country:attacker": "1"}) + self.exchanges(250, start=251)

    def test_q_cmb_11_corroborates_with_500_exchanges_split_by_the_vipc_list(self):
        self.assertIn("1", self.batches["cmb-accumulation"]["vipc_countries"].split())
        self.assertNotIn("12", self.batches["cmb-accumulation"]["vipc_countries"].split())
        self.write("cmb-accumulation", "E020-r0001.json",
                   record("cmb-accumulation", "E020-r0001", 1, self.split(), EXCHANGE_FIELDS))
        self.declare(Q_CMB_11="corroborated")
        problems, lines = self.check("cmb-accumulation")
        self.assertEqual(problems, [])
        self.assertIn("attacker inside 250, outside 250", "\n".join(lines))

    def test_q_cmb_11_is_never_corroborated_without_the_vipc_list_or_one_side_of_it(self):
        self.write("cmb-accumulation", "E020-r0001.json",
                   record("cmb-accumulation", "E020-r0001", 1, self.exchanges(500), EXCHANGE_FIELDS))
        self.declare(Q_CMB_11="corroborated")
        problems, _ = self.check("cmb-accumulation")
        self.assertTrue(any("Q-CMB-11 is declared corroborated" in p for p in problems), problems)
        self.batches["cmb-accumulation"]["vipc_countries"] = ""
        (self.runs / "cmb-accumulation" / "E020-r0001.json").write_text(json.dumps(
            record("cmb-accumulation", "E020-r0001", 1, self.split(), EXCHANGE_FIELDS)))
        problems, _ = self.check("cmb-accumulation")
        self.assertTrue(any("Q-CMB-11 is declared corroborated" in p for p in problems), problems)

    def test_narrowed_below_the_target_is_allowed(self):
        self.write("cmb-accumulation", "E020-r0001.json",
                   record("cmb-accumulation", "E020-r0001", 1, self.exchanges(100), EXCHANGE_FIELDS))
        self.declare(Q_CMB_04="narrowed", Q_CMB_06="narrowed")
        problems, _ = self.check("cmb-accumulation")
        self.assertEqual(problems, [])

    def test_an_unknown_outcome_word_is_refused(self):
        self.declare(Q_CMB_04="proven")
        problems, _ = self.check("cmb-accumulation")
        self.assertTrue(any("the outcome is one of" in p for p in problems), problems)


class ValueRuleTest(unittest.TestCase):
    def test_role_values(self):
        ok = [("counter:attacker-before", "0"), ("counter:x", "999"), ("owner:victim", "blue"),
              ("country:victim", "46"), ("game:ordinal", "1"), ("sitting:epoch", "1791460800")]
        bad = [("counter:attacker-before", "-1"), ("counter:x", "3 armies"), ("counter:x", "03"),
               ("owner:victim", "Blue"), ("owner:victim", "7"), ("country:victim", "47"), ("country:victim", "0"),
               ("game:ordinal", "0"), ("label:screen", "1"), ("Counter:x", "1"), ("counter:x", 3)]
        for field, value in ok:
            self.assertEqual(check_counts.value_problem(field, value), "", (field, value))
        for field, value in bad:
            self.assertNotEqual(check_counts.value_problem(field, value), "", (field, value))


if __name__ == "__main__":
    unittest.main(verbosity=2)
