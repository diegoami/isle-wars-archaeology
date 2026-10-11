"""T45: the Session A case table and its pure picker (experiments/E021-pro-session-a/cases.py).

Each test's board is synthetic (tools/tests/e021_fixtures.py): 46 country readings, a small
adjacency, no pixels and no original bytes (rule 18). They pin the task file's Done-when 1: the
picker returns a valid (attacker, defender) pair for each case when one exists on a board, and
none when none does; and it never picks a non-adjacent or an own-country target.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "tests"))
import e021_fixtures as fx  # noqa: E402  (puts experiments/E021-pro-session-a on sys.path)
import cases  # noqa: E402
import points as points_module  # noqa: E402

ALL = {(case, cell) for case in cases.CASES for cell in cases.cells(case)}


class TableTest(unittest.TestCase):
    def test_the_table_is_the_task_files_forty_cells(self):
        self.assertEqual(cases.CASES, ("even", "underdog", "tiny", "quit", "lost", "busy"))
        self.assertEqual(cases.TOTALS, {"even": 16, "underdog": 4, "tiny": 3, "quit": 2, "lost": 5,
                                        "busy": 10})
        self.assertEqual(cases.TOTAL, 40)
        self.assertEqual(sum(cases.TOTALS.values()), cases.TOTAL)
        self.assertEqual(len(cases.needed_cells(())), 40)
        self.assertEqual(cases.needed_cells(ALL), [])

    def test_the_cells_of_a_row_run_from_1_to_its_total(self):
        for case, total in cases.TOTALS.items():
            self.assertEqual(cases.cells(case), tuple(range(1, total + 1)), case)
        with self.assertRaises(KeyError):
            cases.cells("no-such-case")

    def test_a_sizes_cells_spec_is_its_attacker_size_and_its_defenders_range(self):
        # even: cell 1 is attacker 2 vs a defender of 1, cell 4 attacker 2 vs 4, cell 5 attacker 4 vs 3
        self.assertEqual(cases.spec("even", 1), {"size": 2, "defender": (1, 1)})
        self.assertEqual(cases.spec("even", 4), {"size": 2, "defender": (4, 4)})
        self.assertEqual(cases.spec("even", 5), {"size": 4, "defender": (3, 3)})
        self.assertEqual(cases.spec("even", 16), {"size": 12, "defender": (14, 14)})
        # underdog: attacker N vs a strictly stronger defender (unbounded above)
        self.assertEqual(cases.spec("underdog", 1), {"size": 4, "defender": (5, None)})
        self.assertEqual(cases.spec("underdog", 4), {"size": 20, "defender": (21, None)})
        # tiny: attacker 1, 2 or 3 vs a defender of 1
        self.assertEqual(cases.spec("tiny", 3), {"size": 3, "defender": (1, 1)})
        # the outcome rows take any legal pair
        self.assertEqual(cases.spec("quit", 2), {})
        self.assertEqual(cases.spec("lost", 5), {})
        self.assertEqual(cases.spec("busy", 10), {})
        with self.assertRaises(KeyError):
            cases.spec("even", 17)
        with self.assertRaises(KeyError):
            cases.spec("tiny", 0)


class PickTest(unittest.TestCase):
    """Done-when 1: a valid pair for each case when one exists, none when none does, and never a
    non-adjacent or own-country target."""

    def pick(self, board, needed, adj=fx.ADJ, **kwargs):
        return cases.pick(board, needed, adj, **kwargs)

    def assert_pair(self, board, answer, case, cell, adj=fx.ADJ):
        self.assertIsNotNone(answer, f"no pair for {case} {cell}")
        got_case, got_cell, attacker, defender = answer
        self.assertEqual((got_case, got_cell), (case, cell))
        self.assertTrue(cases.paired(board, attacker, defender, adj))
        self.assertTrue(cases.fits(board, case, cell, attacker, defender, adj))

    def test_even_cell_one_when_the_board_shows_2_against_1(self):
        board = fx.frontier_board()
        self.assert_pair(board, self.pick(board, {("even", 1)}), "even", 1)

    def test_even_cell_against_each_of_the_four_defender_counts(self):
        for offset, defender in enumerate((-1, 0, 1, 2)):
            board = fx.board({3: (fx.BLUE, 2), 4: (fx.RED, 2 + defender)})
            cell = 1 + offset
            self.assert_pair(board, self.pick(board, {("even", cell)}), "even", cell)

    def test_underdog_cell_is_a_stronger_defender(self):
        board = fx.board({3: (fx.BLUE, 4), 4: (fx.RED, 9)})
        self.assert_pair(board, self.pick(board, {("underdog", 1)}), "underdog", 1)
        # a defender of 4 against an attacker of 4 is not an underdog (equality is not "stronger")
        equal = fx.board({3: (fx.BLUE, 4), 4: (fx.RED, 4)})
        self.assertIsNone(self.pick(equal, {("underdog", 1)}))

    def test_tiny_cell_is_a_defender_of_one(self):
        board = fx.board({3: (fx.BLUE, 3), 4: (fx.RED, 1)})
        self.assert_pair(board, self.pick(board, {("tiny", 3)}), "tiny", 3)

    def test_the_outcome_rows_take_any_legal_pair(self):
        board = fx.board({3: (fx.BLUE, 7), 4: (fx.RED, 7)})
        for case in ("quit", "lost", "busy"):
            self.assert_pair(board, self.pick(board, {(case, 1)}), case, 1)

    def test_none_when_no_needed_cell_is_on_the_board(self):
        # a blue 2 against a red 5: too strong for even cell 1, and no other size cell fits
        board = fx.board({3: (fx.BLUE, 2), 4: (fx.RED, 5)})
        self.assertIsNone(self.pick(board, {("even", 1)}))
        self.assertIsNone(self.pick(board, {("tiny", 2)}))
        self.assertIsNone(self.pick(board, set()))

    def test_stronger_enemy_is_a_boundary_probe_not_an_outcome_pair(self):
        # The task explicitly probes 2 versus 3, even if the game refuses it.
        board = fx.board({3: (fx.BLUE, 2), 4: (fx.RED, 3)})
        self.assertEqual(self.pick(board, {("even", 3)}), ("even", 3, 3, 4))
        self.assertIsNone(self.pick(board, {("lost", 1)}))

    def test_never_a_non_adjacent_target(self):
        # country 5 is red but borders only 4: 3 may not name it, and the size cells do not fit 4
        board = fx.board({3: (fx.BLUE, 2), 4: (fx.RED, 2), 5: (fx.RED, 1)})
        self.assertIsNone(self.pick(board, {("even", 1)}))
        self.assertIsNone(self.pick(board, {("tiny", 2)}))
        # the pair the picker does return is the adjacent 4, never the nearer-looking 5
        answer = self.pick(board, {("lost", 1)})
        self.assertEqual(answer[2:], (3, 4))

    def test_never_an_own_country_target(self):
        # every neighbour of 3 is blue: no legal pair at all, for any row
        adjacency = {1: {2, 3}, 2: {1, 3}, 3: {1, 2}}
        board = fx.board({1: (fx.BLUE, 1), 2: (fx.BLUE, 1), 3: (fx.BLUE, 5), 4: (fx.RED, 1)})
        for needed in ({("even", 1)}, {("tiny", 3)}, {("quit", 1)}, {("lost", 1)}, {("busy", 1)}):
            self.assertIsNone(self.pick(board, needed, adjacency), needed)
        # the positive control: with 4 (red) on 3's border, the same rows have a pair
        adjacency[3] = {1, 2, 4}
        adjacency[4] = {3}
        for needed in ({("quit", 1)}, {("lost", 1)}, {("busy", 1)}):
            self.assertEqual(self.pick(board, needed, adjacency)[2:], (3, 4), needed)

    def test_never_a_country_the_driver_cannot_click(self):
        # countries 11 and 15 have no proven click point (#120): never an attacker or a target
        adjacency = {11: {12}, 12: {11}}
        board = fx.board({11: (fx.BLUE, 3), 12: (fx.RED, 1)})
        points = points_module.click_points()
        self.assertIsNone(cases.pick(board, {("tiny", 3)}, adjacency, points=points))
        self.assertIsNone(cases.pick(board, {("lost", 1)}, adjacency, points=points))
        # the same board with the points allowed is a pair (the click constraint is the points')
        self.assertIsNotNone(cases.pick(board, {("tiny", 3)}, adjacency, points=None))

    def test_the_first_pair_is_the_lowest_country_numbers(self):
        board = fx.board({1: (fx.BLUE, 2), 3: (fx.BLUE, 2), 2: (fx.RED, 1), 4: (fx.RED, 1)})
        adjacency = {1: {2}, 2: {1}, 3: {4}, 4: {3}}
        self.assertEqual(cases.pick(board, {("tiny", 2)}, adjacency), ("tiny", 2, 1, 2))

    def test_the_lost_row_takes_the_closest_fight_and_busy_the_safest(self):
        board = fx.board({3: (fx.BLUE, 6), 4: (fx.RED, 6), 5: (fx.RED, 1)})
        adjacency = {3: {4, 5}, 4: {3}, 5: {3}}
        self.assertEqual(cases.pick(board, {("lost", 1)}, adjacency)[2:], (3, 4))
        self.assertEqual(cases.pick(board, {("busy", 1)}, adjacency)[2:], (3, 5))
        self.assertEqual(cases.pick(board, {("quit", 1)}, adjacency)[2:], (3, 5))

    def test_excluded_pairs_are_never_returned(self):
        board = fx.board({3: (fx.BLUE, 5), 4: (fx.RED, 5), 5: (fx.RED, 5)})
        adjacency = {3: {4, 5}, 4: {3}, 5: {3}}
        self.assertEqual(cases.pick(board, {("lost", 1)}, adjacency)[2:], (3, 4))
        self.assertEqual(cases.pick(board, {("lost", 1)}, adjacency, exclude={(3, 4)})[2:], (3, 5))
        self.assertIsNone(cases.pick(board, {("lost", 1)}, adjacency, exclude={(3, 4), (3, 5)}))

    def test_an_unread_country_is_never_a_pick(self):
        board = fx.frontier_board()
        self.assertIsNotNone(self.pick(board, {("even", 1)}))        # the positive control
        board[4] = {"army": None, "owner": None}
        self.assertIsNone(self.pick(board, {("even", 1)}))
        self.assertIsNone(self.pick(board, {("lost", 1)}))


class FrontierTest(unittest.TestCase):
    def test_the_frontier_is_the_country_a_needed_size_is_reachable_from(self):
        board = fx.frontier_board()          # blue 3 at 2 next to red 4 at 1
        answer = cases.frontier(board, {("tiny", 3)}, fx.ADJ)
        self.assertEqual(answer, (3, 4, "tiny", 3, 1))

    def test_a_country_already_at_a_needed_size_is_never_the_growth_target_for_it(self):
        # ALL places every reinforcement: growing a stack that shows its size only overshoots it
        board = fx.frontier_board()          # blue 3 at 2 next to red 4 at 1: even cell 1 as it is
        answer = cases.frontier(board, {("even", 1)}, fx.ADJ)
        self.assertEqual(answer[2:4], (None, None))

    def test_avoided_countries_are_grown_only_when_nothing_else_has_an_enemy(self):
        adjacency = {1: {2}, 2: {1}, 3: {4}, 4: {3}}
        board = fx.board({1: (fx.BLUE, 5), 2: (fx.RED, 9), 3: (fx.BLUE, 2), 4: (fx.RED, 1)})
        self.assertEqual(cases.frontier(board, {("even", 5)}, adjacency, avoid={3})[0], 1)
        self.assertEqual(cases.frontier(board, set(), adjacency, avoid={1})[0], 3)
        self.assertEqual(cases.frontier(board, set(), adjacency, avoid={1, 3})[0], 1)

    def test_the_frontier_grows_the_smallest_gap_first(self):
        # even cell 5 is an attacker of 4 against a defender of 3: two reinforcements away from 2
        board = fx.board({3: (fx.BLUE, 2), 4: (fx.RED, 3)})
        answer = cases.frontier(board, {("even", 5)}, fx.ADJ)
        self.assertEqual(answer, (3, 4, "even", 5, 2))

    def test_the_frontier_prefers_the_pair_whose_cell_is_closest(self):
        # Country 1 is one reinforcement from cell 6 (4 vs 4); country 3 three from cell 11 (8 vs 9).
        adjacency = {1: {2}, 2: {1}, 3: {4}, 4: {3}}
        board = fx.board({1: (fx.BLUE, 3), 2: (fx.RED, 4), 3: (fx.BLUE, 5), 4: (fx.RED, 9)})
        needed = {("even", 6), ("even", 11)}
        self.assertEqual(cases.frontier(board, needed, adjacency), (1, 2, "even", 6, 1))
        self.assertEqual(cases.frontier(board, {("even", 11)}, adjacency), (3, 4, "even", 11, 3))

    def test_the_frontier_falls_back_to_the_strongest_country_with_an_enemy(self):
        # nothing size-shaped is reachable (no size cells are needed): grow the strongest anyway
        board = fx.board({1: (fx.BLUE, 2), 3: (fx.BLUE, 9), 4: (fx.RED, 12)})
        answer = cases.frontier(board, {("quit", 1)}, fx.ADJ)
        self.assertEqual(answer[:2], (3, 4))
        self.assertIsNone(answer[2])

    def test_the_frontier_is_none_without_a_country_of_the_seat_next_to_an_enemy(self):
        board = fx.board({1: (fx.BLUE, 4), 2: (fx.BLUE, 4)})
        self.assertIsNone(cases.frontier(board, ALL, fx.ADJ))

    def test_reachable_lists_the_cells_each_pair_could_attempt(self):
        board = fx.frontier_board()
        found = cases.reachable(board, {("even", 1), ("tiny", 3), ("quit", 1)}, fx.ADJ)
        self.assertEqual(found, {(3, 4): [("even", 1, 0), ("tiny", 3, 1)]})

    def test_defender_fits_reads_the_cells_range_only(self):
        board = fx.frontier_board()          # country 4 is a red 1
        self.assertTrue(cases.defender_fits(board, "even", 1, 4))
        self.assertFalse(cases.defender_fits(board, "even", 1, 5))
        self.assertFalse(cases.defender_fits(board, "underdog", 1, 4))    # the floor is 5
        board[4] = {"army": 5, "owner": fx.RED}
        self.assertTrue(cases.defender_fits(board, "underdog", 1, 4))
        self.assertFalse(cases.defender_fits(board, "tiny", 1, 4))

    def test_next_outcome_cell_is_the_lowest_unmet_one(self):
        needed = cases.needed_cells({("lost", 1), ("lost", 2)})
        self.assertEqual(cases.next_outcome_cell(needed, "lost"), 3)
        self.assertIsNone(cases.next_outcome_cell(cases.needed_cells(ALL), "lost"))
        self.assertIsNone(cases.next_outcome_cell(cases.needed_cells(ALL), "quit"))


class LegalTest(unittest.TestCase):
    def test_legal_needs_owners_adjacency_and_the_equality_gate(self):
        board = fx.frontier_board()
        self.assertTrue(cases.legal(board, 3, 4, fx.ADJ))
        self.assertFalse(cases.legal(board, 3, 5, fx.ADJ))        # not adjacent
        self.assertFalse(cases.legal(board, 3, 2, fx.ADJ))        # own country
        self.assertFalse(cases.legal(board, 4, 3, fx.ADJ))        # the wrong way round
        board[3]["army"] = 0
        self.assertFalse(cases.legal(board, 3, 4, fx.ADJ))        # 0 may not attack 1
        board[3]["army"] = 1
        self.assertTrue(cases.legal(board, 3, 4, fx.ADJ))         # equality is the gate

    def test_pairs_lists_every_legal_pair_in_country_order(self):
        board = fx.board({1: (fx.BLUE, 5), 2: (fx.RED, 1), 3: (fx.RED, 2)})
        adjacency = {1: {2, 3}, 2: {1}, 3: {1}}
        self.assertEqual(cases.pairs(board, adjacency), [(1, 2), (1, 3)])


if __name__ == "__main__":
    unittest.main()


class FrontierGrowTargetTest(unittest.TestCase):
    """Fix #178: with no needed cell reachable now, the strongest country is grown towards the
    smallest open even or underdog attacker size above its armies."""

    def board(self, armies, defender=1):
        # blue 3 holds `armies` next to red 4 holding `defender`: no size cell below fits a defender of 1
        return fx.board({3: (fx.BLUE, armies), 4: (fx.RED, defender)})

    def test_the_smallest_open_size_above_the_armies_is_the_target(self):
        needed = {("even", 13), ("even", 9), ("underdog", 3)}      # attackers 12, 8, 12
        self.assertEqual(cases.reachable(self.board(3), needed, fx.ADJ), {})
        self.assertEqual(cases.frontier(self.board(3), needed, fx.ADJ), (3, 4, "even", 9, 5))

    def test_the_target_moves_up_when_the_smaller_size_is_passed_or_met(self):
        needed = {("even", 13), ("even", 9), ("underdog", 3)}
        self.assertEqual(cases.frontier(self.board(9), needed, fx.ADJ), (3, 4, "even", 13, 3))
        self.assertEqual(cases.frontier(self.board(3), {("even", 13), ("underdog", 3)}, fx.ADJ),
                         (3, 4, "even", 13, 9))

    def test_an_underdog_size_is_a_target_too(self):
        self.assertEqual(cases.frontier(self.board(3), {("underdog", 1)}, fx.ADJ), (3, 4, "underdog", 1, 1))

    def test_a_tiny_or_outcome_cell_is_never_a_growth_target(self):
        # a defender of 2 fits no tiny cell (they ask a defender of 1), so nothing is reachable
        self.assertEqual(cases.frontier(self.board(1, defender=2), {("tiny", 3), ("busy", 1), ("lost", 1)},
                                        fx.ADJ)[2:],
                         (None, None, 0))

    def test_when_every_open_size_is_below_the_strongest_stack_the_fallback_is_as_before(self):
        needed = {("even", 9), ("even", 5)}                        # attackers 8 and 4
        self.assertEqual(cases.frontier(self.board(9), needed, fx.ADJ), (3, 4, None, None, 0))
        self.assertEqual(cases.frontier(self.board(8), needed, fx.ADJ), (3, 4, None, None, 0))

    def test_a_reachable_cell_still_beats_the_target(self):
        needed = {("even", 9), ("even", 5)}
        board = self.board(3, defender=3)                          # attacker 4 vs 3 is reachable: even cell 5
        self.assertEqual(cases.frontier(board, needed, fx.ADJ), (3, 4, "even", 5, 1))

