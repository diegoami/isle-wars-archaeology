"""tools/coverage.py: the coverage page follows the records, and stays current."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import coverage  # noqa: E402

INDEX = """# E018 per-question outcomes

## Q-CMB-01..11 — combat corroboration (whole family)

- **Status:** unestablished

## Q-MOV-01 — moves per turn

- **Status:** narrowed (one move only)

# IP1 026 sitting

### Q-CMB-01 (C-CMB-01) — who may attack

- **Status:** narrowed

### Q-CMB-07 (C-CMB-06) — exactly one army lost per exchange

- **Status:** corroborated

### C-AI-05 (Q-AI-04's move half) — the computer's end-of-turn move

- **Status:** narrowed

# IP1 027 sitting

### Q-MOV-01 (C-MOV-01) — moves per turn

- **Status:** corroborated
"""


class CoverageTest(unittest.TestCase):
    def setUp(self):
        self.q = coverage.read_index(INDEX)

    def test_each_sitting_is_a_source(self):
        self.assertEqual(self.q["Q-MOV-01"]["sources"], {"IP1 025": "narrowed", "IP1 027": "corroborated"})

    def test_a_claim_id_in_brackets_is_not_a_question_of_its_own(self):
        self.assertNotIn("C-CMB-01", self.q)
        self.assertNotIn("C-AI-05", self.q)
        self.assertIn("Q-AI-04", self.q)

    def test_a_question_takes_its_own_heading_over_a_family_heading(self):
        self.assertEqual(self.q["Q-CMB-01"]["title"], "who may attack")

    def test_best_outcome_and_model_cells_reach_the_page(self):
        page = coverage.render(self.q, "progress-r09.json",
                               {"rows": {"even": {"met": 8, "total": 16}, "busy": {"met": 10, "total": 10}}},
                               {"Q-TRN-05": "game length"})
        self.assertIn("| Q-MOV-01 | moves per turn | **corroborated** |", page)
        self.assertIn("8/16 cells (even)", page)
        self.assertIn("| Q-CMB-10 |", page)              # a model-only question still gets a row
        self.assertIn("| Q-TRN-05 | game length | — |", page)   # planned, not yet touched
        self.assertIn("progress-r09.json", page)

    def test_the_plan_table_is_read(self):
        plan = coverage.read_plan("| Q-id | C-id | t | w |\n| --- | --- | --- | --- |\n"
                                  "| Q-MOV-02 | C-MOV-02 | 2 + 2 | Stacks 2, 3, 10 |\n")
        self.assertEqual(plan, {"Q-MOV-02": "Stacks 2, 3, 10"})

    def test_the_committed_page_is_current(self):
        """A recording or sitting that changes the records must regenerate runs/coverage.md."""
        self.assertEqual(coverage.OUT.read_text(encoding="utf-8"), coverage.build(),
                         "runs/coverage.md is stale: run python3 tools/coverage.py")


if __name__ == "__main__":
    unittest.main()
