"""Tests for tools/check_design.py (T50, Done-when 2).

Each failure the task's Scope lists has one fixture that trips that failure alone: the clean
fixture passes, and each test changes exactly one thing in it and expects exactly one problem.
"""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_design  # noqa: E402

SPEC_HEAD = "| ID | Claim | Status | Scope | Basis | Findings |\n| --- | --- | --- | --- | --- | --- |\n"
# Two claims in board.md and one in combat.md; the other in-scope files exist with empty tables.
SPEC = {
    "board": ["C-BRD-01", "C-BRD-02"],
    "combat": ["C-CMB-05"],
}
ROWS = {
    "C-BRD-01": "| C-BRD-01 | keep | [The board](#the-board) | It serves variety. |",
    "C-BRD-02": "| C-BRD-02 | change | [The board](#the-board) | Fewer countries, shorter games. |",
    "C-CMB-05": "| C-CMB-05 | open | [Combat](#combat) | The owner chooses. |",
}
CHOICES = "## Choices for the owner\n\n1. **Ties** (C-CMB-05; `open`). (a) one; (b) two. Recommendation: (b).\n"


class DesignWorld(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "spec").mkdir()
        (self.root / "design").mkdir()
        for name in check_design.SPEC_FILES:
            body = "".join(f"| {cid} | a claim | supported | s | b | f |\n" for cid in SPEC.get(name, []))
            (self.root / "spec" / f"{name}.md").write_text(f"# {name}\n\n## Claims\n\n{SPEC_HEAD}{body}")
        self.rows = dict(ROWS)
        self.extra_rows = []
        self.choices = CHOICES

    def write_design(self):
        table = "| Claim | Decision | malpaco's rule | Why |\n| --- | --- | --- | --- |\n"
        table += "\n".join(list(self.rows.values()) + self.extra_rows) + "\n"
        text = "# Rules\n\n## The board\n\nText.\n\n" + self.choices + "\n## Decisions, claim by claim\n\n" + table
        (self.root / "design" / "core-rules.md").write_text(text)

    def problems(self):
        self.write_design()
        problems, _, _ = check_design.check(self.root)
        return problems

    def assert_one(self, fragment):
        problems = self.problems()
        self.assertEqual(len(problems), 1, problems)
        self.assertIn(fragment, problems[0])


class CleanTest(DesignWorld):
    def test_clean_fixture_passes_and_counts(self):
        self.write_design()
        self.assertEqual(check_design.check(self.root), ([], 3, 3))

    def test_main_prints_ok_and_exits_0(self):
        self.write_design()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_design.main(["--root", str(self.root)])
        self.assertEqual((code, out.getvalue().strip()), (0, "design ok: 3 claims, 3 rows"))

    def test_main_exits_1_without_a_design(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_design.main(["--root", str(self.root)])
        self.assertEqual(code, 1)
        self.assertIn("design/core-rules.md: missing", out.getvalue())


class FailureTest(DesignWorld):
    def test_claim_with_no_row(self):
        del self.rows["C-BRD-02"]
        self.assert_one("C-BRD-02: no row")

    def test_claim_with_two_rows(self):
        self.extra_rows.append("| C-BRD-01 | keep | [The board](#the-board) | Again. |")
        self.assert_one("C-BRD-01: 2 rows")

    def test_row_naming_an_id_not_in_the_spec(self):
        self.extra_rows.append("| C-BRD-09 | keep | [The board](#the-board) | Invented. |")
        self.assert_one("C-BRD-09 is not an in-scope spec claim")

    def test_decision_not_one_of_the_five_words(self):
        self.rows["C-BRD-01"] = "| C-BRD-01 | tweak | [The board](#the-board) | It serves variety. |"
        self.assert_one("decision 'tweak'")

    def test_change_replace_drop_with_empty_why(self):
        for decision in ("change", "replace", "drop"):
            with self.subTest(decision=decision):
                self.rows["C-BRD-02"] = f"| C-BRD-02 | {decision} | [The board](#the-board) |  |"
                self.assert_one(f"C-BRD-02 is {decision} with an empty why")

    def test_keep_with_empty_why_is_allowed(self):
        self.rows["C-BRD-01"] = "| C-BRD-01 | keep | [The board](#the-board) |  |"
        self.assertEqual(self.problems(), [])

    def test_open_row_missing_from_choices(self):
        self.choices = "## Choices for the owner\n\n1. **Boards** (C-BRD-01). Recommendation: (a).\n"
        self.assert_one("C-CMB-05 is open but not in")

    def test_open_row_named_only_outside_choices_still_fails(self):
        self.choices = "## Choices for the owner\n\nNone yet.\n\n## Notes\n\nC-CMB-05 is discussed here.\n"
        self.assert_one("C-CMB-05 is open but not in")


class RepositoryTest(unittest.TestCase):
    def test_the_repository_design_is_complete(self):
        root = Path(check_design.__file__).resolve().parents[1]
        self.assertEqual(check_design.check(root), ([], 59, 59))


if __name__ == "__main__":
    unittest.main()
