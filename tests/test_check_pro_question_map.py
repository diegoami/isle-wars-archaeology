"""Tests for the row validation in tools/check_pro_question_map.py.

Every fixture is synthetic text: the question tables and the script inventory are
invented here, and no line of questions/pro-static.md is quoted (the file stays
outside the tests). The module-level MAP/QUESTIONS/INVENTORY paths are replaced
for the duration of each main() call, so the checker reads the synthetic rows.
"""
import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import check_pro_question_map as checker  # noqa: E402

# main() reads the inventory unconditionally, but the rows below cite
# "none found: ...", which skips the script-citation checks, so an empty
# script list is enough.
INVENTORY = '{"movies": [{"scripts": []}]}'

# One Pro-scope question: the scope cell (5th) does not start with DOS, so the
# id is expected rather than dropped, and the last cell is its priority.
MALPACO = "\n".join(
    [
        "# Questions",
        "",
        "| id | question | area | scope | dos | priority |",
        "|---|---|---|---|---|---|",
        "| Q-PRO-1 | When does the synthetic thing happen? | rules | Pro | no | P1 |",
    ]
)


def map_text(task):
    """A pro-static.md-shaped text whose one row has the given Task cell."""
    return "\n".join(
        [
            "# Pro static map",
            "",
            "| id | sources | task | corroboration | confidence |",
            "|---|---|---|---|---|",
            "| Q-PRO-1 | none found: searched the scripts | %s "
            "| play: owner video | high: direct |" % task,
        ]
    )


class _FakeFile:
    """read_text() stand-in so main() reads a synthetic string, not a repo file."""

    def __init__(self, text):
        self._text = text

    def read_text(self):
        return self._text


def run_checker(task):
    """Run main() on one synthetic map row; return (code, stdout, stderr)."""
    saved = (checker.MAP, checker.QUESTIONS, checker.INVENTORY)
    checker.MAP = _FakeFile(map_text(task))
    checker.QUESTIONS = _FakeFile(MALPACO)
    checker.INVENTORY = _FakeFile(INVENTORY)
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            code = checker.main()
    finally:
        checker.MAP, checker.QUESTIONS, checker.INVENTORY = saved
    return code, out.getvalue(), err.getvalue()


class TaskCell(unittest.TestCase):
    def test_t30_with_reason_is_accepted(self):
        # The cell this fix exists for: T30's rows in pro-static.md begin
        # "T30: ...", and T30 must be in the checker's TASKS set for the row
        # to pass.
        code, out, err = run_checker("T30: merged, F012 is the answer")
        self.assertEqual(code, 0, out + err)
        self.assertIn("ok: 1 rows match malpaco.md", out)

    def test_known_task_with_reason_is_accepted(self):
        # A pre-existing task id still passes: the fix widens the set,
        # it does not change what a task cell looks like.
        code, out, err = run_checker("T20: F011 ownership chain")
        self.assertEqual(code, 0, out + err)

    def test_unknown_task_number_is_refused(self):
        # T99 has the T<nn> shape but is in no task the checker knows; the
        # shape check alone must not admit it.
        code, out, _ = run_checker("T99: not a real task")
        self.assertEqual(code, 1)
        self.assertIn("task 'T99: not a real task'", out)

    def test_garbage_task_is_refused(self):
        code, out, _ = run_checker("garbage")
        self.assertEqual(code, 1)
        self.assertIn("task 'garbage'", out)

    def test_none_without_reason_is_refused(self):
        # A bare `none` says nothing; the checker demands a reason after a
        # colon, so the cell without one is refused.
        code, out, _ = run_checker("none")
        self.assertEqual(code, 1)
        self.assertIn("task none without a reason", out)

    def test_none_with_reason_is_accepted(self):
        # The contrast for the refusal above: a reason after the colon is
        # enough for `none`.
        code, out, err = run_checker("none: answered by F011")
        self.assertEqual(code, 0, out + err)
        self.assertIn("ok: 1 rows match malpaco.md", out)


if __name__ == "__main__":
    unittest.main()
