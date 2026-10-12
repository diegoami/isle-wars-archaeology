"""Tests for tools/check_design.py (T50 Done-when 2; T51 Done-when 2; T53 Done-when 2; T52 Done-when 2).

Each failure the tasks' Scope lists has one fixture that trips that failure alone: the clean
fixture passes, and each test changes exactly one thing in it and expects exactly one problem.
`DesignWorld` tests `design/core-rules.md`; `VarietyWorld`, `ComputerWorld` and `UiWorld` run the same
failures against `design/variety.md`, `design/computer.md` and `design/ui.md`, each with its own spec
files; `design/ui.md` is also checked against the `Q-UI-*` rows of `questions/malpaco.md`. Every world writes
every design file clean, so `main()` sees a whole tree and only the file under test changes.
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
TABLE_HEAD = "| Claim | Decision | malpaco's rule | Why |\n| --- | --- | --- | --- |\n"

# core-rules.md: two claims in board.md and one in combat.md; the other in-scope files are empty.
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

# variety.md: two claims in cards.md and one in hazards.md; the other in-scope files are empty.
V_SPEC = {
    "cards": ["C-CRD-01", "C-CRD-02"],
    "hazards": ["C-HAZ-03"],
}
V_ROWS = {
    "C-CRD-01": "| C-CRD-01 | keep | [Cards](#cards) | It serves surprise. |",
    "C-CRD-02": "| C-CRD-02 | replace | [The deck](#the-deck) | A shuffled deck. |",
    "C-HAZ-03": "| C-HAZ-03 | open | [Events](#events) | The owner chooses. |",
}
V_CHOICES = "## Choices for the owner\n\n1. **Rate** (C-HAZ-03; `open`). (a) one; (b) two. Recommendation: (b).\n"

# computer.md: three claims in computer-opponent.md, its only in-scope spec file.
C_SPEC = {
    "computer-opponent": ["C-AI-01", "C-AI-02", "C-AI-08"],
}
C_ROWS = {
    "C-AI-01": "| C-AI-01 | keep | [Placement](#placement) | It serves play. |",
    "C-AI-02": "| C-AI-02 | replace | [Attacks](#attacks) | A readable rule. |",
    "C-AI-08": "| C-AI-08 | open | [Levels](#levels) | The owner chooses. |",
}
C_CHOICES = "## Choices for the owner\n\n1. **Levels** (C-AI-08; `open`). (a) one; (b) two. Recommendation: (b).\n"

# ui.md: two claims in user-interface.md, its only in-scope spec file, and two UI questions.
U_SPEC = {
    "user-interface": ["C-UI-01", "C-UI-02"],
}
U_ROWS = {
    "C-UI-01": "| C-UI-01 | keep | [Screens](#screens) | It serves play. |",
    "C-UI-02": "| C-UI-02 | change | [The board](#the-board) | Ownership needs a second cue. |",
    "Q-UI-01": "| Q-UI-01 | keep | [The board](#the-board) | Counts read well. |",
    "Q-UI-03": "| Q-UI-03 | open | [Sound](#sound) | The owner chooses. |",
}
U_CHOICES = "## Choices for the owner\n\n1. **Sound** (Q-UI-03; `open`). (a) one; (b) two. Recommendation: (b).\n"
# questions/malpaco.md: the in-scope rows are the Q-UI ones only. A rules question (Q-CMB-01) and the
# weakness table, which names Q-UI-05 in a later cell, are out of scope and must not count.
QUESTIONS_TEXT = ("# Questions\n\n## Rules\n\n| Id | q |\n| --- | --- |\n| Q-CMB-01 | a rules question |\n\n"
                  "## User interface\n\n| Id | What | Questions |\n| --- | --- | --- |\n"
                  "| UW-1 | a weakness | Q-UI-01, Q-UI-05 |\n\n"
                  "| Id | q |\n| --- | --- |\n| Q-UI-01 | a UI question |\n| Q-UI-03 | another |\n")

WORLDS = {
    "core-rules.md": (SPEC, ROWS, CHOICES),
    "variety.md": (V_SPEC, V_ROWS, V_CHOICES),
    "computer.md": (C_SPEC, C_ROWS, C_CHOICES),
    "ui.md": (U_SPEC, U_ROWS, U_CHOICES),
}
# What main() prints for each clean design file of the fixture tree, in check order.
OK = ["design/core-rules.md ok: 3 claims, 3 rows",
      "design/variety.md ok: 3 claims, 3 rows",
      "design/computer.md ok: 3 claims, 3 rows",
      "design/ui.md ok: 4 claims, 4 rows"]


def design_text(rows, choices):
    table = TABLE_HEAD + "\n".join(rows) + "\n"
    return "# Rules\n\n## The board\n\nText.\n\n" + choices + "\n## Decisions, claim by claim\n\n" + table


# Disguised rows for fix #202. Each is a line that bypasses the row parser without bypassing a
# permissive Markdown renderer. The four mutation tests below pin one row per disguise class.
DISGUISED_ROWS = {
    "blockquote":  "> | C-BRD-09 | nope    | text | |",                # R1 (rest): blockquote
    "list_dash":   "- | C-BRD-09 | nope    | text | |",               # R1 (rest): list bullet, dash
    "list_star":   "* | C-BRD-09 | nope    | text | |",               # R1 (rest): list bullet, star
    "entity_num":  "| Q&#45;UI&#45;99 | nope | text | |",               # R4: HTML entity, numeric
    "entity_name": "| Q&ndash;UI&ndash;99 | nope | text | |",         # R4: HTML entity, named (–)
    "lookalike":   "| Q‐UI‐99 | nope    | text | |",         # R4: look-alike U+2010
}


class DesignWorld(unittest.TestCase):
    design = "core-rules.md"
    # The ids used by the shared failure cases, per world.
    keep_id, change_id, open_id, alien_id = "C-BRD-01", "C-BRD-02", "C-CMB-05", "C-BRD-09"

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "spec").mkdir()
        (self.root / "design").mkdir()
        (self.root / "questions").mkdir()
        (self.root / "questions" / "malpaco.md").write_text(QUESTIONS_TEXT)
        for name, (spec, rows, choices) in WORLDS.items():
            for spec_file in check_design.DESIGNS[name]:
                body = "".join(f"| {cid} | a claim | supported | s | b | f |\n" for cid in spec.get(spec_file, []))
                (self.root / "spec" / f"{spec_file}.md").write_text(f"# {spec_file}\n\n## Claims\n\n{SPEC_HEAD}{body}")
            if name != self.design:   # the other design files stay clean
                (self.root / "design" / name).write_text(design_text(rows.values(), choices))
        _, rows, choices = WORLDS[self.design]
        self.rows = dict(rows)
        self.extra_rows = []
        self.choices = choices

    def write_design(self):
        text = design_text(list(self.rows.values()) + self.extra_rows, self.choices)
        (self.root / "design" / self.design).write_text(text)

    def problems(self):
        self.write_design()
        problems, _, _ = check_design.check(self.root, self.design)
        return problems

    def assert_one(self, fragment):
        problems = self.problems()
        self.assertEqual(len(problems), 1, problems)
        self.assertIn(fragment, problems[0])
        self.assertIn(f"design/{self.design}", problems[0])


class CleanTest(DesignWorld):
    def test_clean_fixture_passes_and_counts(self):
        self.write_design()
        self.assertEqual(check_design.check(self.root), ([], 3, 3))

    def test_main_prints_ok_and_exits_0(self):
        self.write_design()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_design.main(["--root", str(self.root)])
        self.assertEqual((code, out.getvalue().strip().splitlines()), (0, OK))

    def test_main_exits_1_without_a_design(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_design.main(["--root", str(self.root)])
        self.assertEqual(code, 1)
        self.assertIn("design/core-rules.md: missing", out.getvalue())


class FailureTest(DesignWorld):
    def test_claim_with_no_row(self):
        del self.rows[self.change_id]
        self.assert_one(f"{self.change_id}: no row")

    def test_claim_with_two_rows(self):
        self.extra_rows.append(f"| {self.keep_id} | keep | [The board](#the-board) | Again. |")
        self.assert_one(f"{self.keep_id}: 2 rows")

    def test_row_naming_an_id_not_in_the_spec(self):
        self.extra_rows.append(f"| {self.alien_id} | keep | [The board](#the-board) | Invented. |")
        self.assert_one(f"{self.alien_id} is not an in-scope spec claim")

    def test_decision_not_one_of_the_five_words(self):
        self.rows[self.keep_id] = f"| {self.keep_id} | tweak | [The board](#the-board) | It serves variety. |"
        self.assert_one("decision 'tweak'")

    def test_change_replace_drop_with_empty_why(self):
        for decision in ("change", "replace", "drop"):
            with self.subTest(decision=decision):
                self.rows[self.change_id] = f"| {self.change_id} | {decision} | [The board](#the-board) |  |"
                self.assert_one(f"{self.change_id} is {decision} with an empty why")

    def test_keep_with_empty_why_is_allowed(self):
        self.rows[self.keep_id] = f"| {self.keep_id} | keep | [The board](#the-board) |  |"
        self.assertEqual(self.problems(), [])

    def test_open_row_missing_from_choices(self):
        self.choices = f"## Choices for the owner\n\n1. **Other** ({self.keep_id}). Recommendation: (a).\n"
        self.assert_one(f"{self.open_id} is open but not in")

    def test_row_with_an_extra_cell_fails(self):
        # Otherwise valid: a known id, a valid decision and a reason; only the cell count is wrong.
        self.rows[self.keep_id] = f"| {self.keep_id} | keep | [The board](#the-board) | A reason. | extra |"
        self.assert_one(f"{self.keep_id} has 5 cells, not 4")

    def test_row_with_too_few_cells_fails(self):
        self.rows[self.keep_id] = f"| {self.keep_id} | keep | [The board](#the-board) |"
        self.assert_one(f"{self.keep_id} has 3 cells, not 4")

    # Inactive Markdown fails closed. The injected text starts at line 7 of the fixture file.
    def assert_inactive(self, inject, lines, kind):
        self.choices = inject + "\n" + self.choices
        problems = self.problems()
        self.assertEqual(len(problems), len(lines), problems)
        for problem, n in zip(problems, lines):
            self.assertTrue(problem.startswith(f"design/{self.design}:{n}: {kind}"), problem)

    def test_a_backtick_fence_fails(self):
        self.assert_inactive("```python\nx = 1\n```", [7, 9], "a code fence")

    def test_a_tilde_fence_fails(self):
        self.assert_inactive("~~~\nx = 1\n~~~", [7, 9], "a code fence")

    def test_an_indented_fence_fails(self):
        self.assert_inactive("      ```text", [7], "a code fence")

    def test_an_inline_html_comment_fails(self):
        self.assert_inactive("Some text <!-- hidden --> more text.", [7], "an HTML comment")

    def test_a_multi_line_html_comment_fails(self):
        self.assert_inactive("<!--\nhidden\n-->", [7], "an HTML comment")

    def test_a_script_tag_fails(self):
        self.assert_inactive("<script>\nx = 1\n</script>", [7, 9], "a raw HTML tag")

    def test_a_hidden_div_around_a_row_fails(self):
        # Sol's round-3 bypass: a row inside <div hidden> renders as nothing but was counted.
        self.rows[self.change_id] = "<div hidden>\n\n" + self.rows[self.change_id] + "\n\n</div>"
        problems = self.problems()
        self.assertEqual(len(problems), 2, problems)
        self.assertTrue(all("a raw HTML tag" in p for p in problems), problems)

    def test_a_closing_tag_fails(self):
        self.assert_inactive("</details>", [7], "a raw HTML tag")

    def test_an_indented_tag_fails(self):
        self.assert_inactive("   <details open>", [7], "a raw HTML tag")

    def test_a_declaration_fails(self):
        self.assert_inactive("<!DOCTYPE html>", [7], "a raw HTML tag")

    def test_a_less_than_in_text_is_allowed(self):
        # A line may start with "<" when no tag follows: a comparison, not HTML.
        self.choices = "< 3 armies is too few.\n<= 2 as well.\n" + self.choices
        self.assertEqual(self.problems(), [])

    def test_a_row_hidden_in_a_fence_still_fails_the_file(self):
        # Sol's bypass of round 2: rows after a fence that never closes. The fence alone fails.
        self.rows[self.change_id] = "````\n```\n" + self.rows[self.change_id]
        problems = self.problems()
        self.assertTrue(problems)
        self.assertTrue(all("a code fence" in p for p in problems), problems)

    # Rows Markdown renders but a column-zero reader would skip (Sol's round-1 bypass of T52): each is
    # either read as a row (up to 3 spaces of indentation) or rejected, never skipped.
    def test_rows_indented_up_to_three_spaces_count(self):
        for i, cid in enumerate(self.rows):
            self.rows[cid] = " " * (i % 3 + 1) + self.rows[cid]
        self.write_design()
        problems, n_claims, n_rows = check_design.check(self.root, self.design)
        self.assertEqual((problems, n_claims, n_rows), ([], len(self.rows), len(self.rows)))

    def test_an_indented_unknown_id_fails(self):
        self.extra_rows.append(f" | {self.alien_id} | keep | [The board](#the-board) | Invented. |")
        self.assert_one(f"{self.alien_id} is not an in-scope spec claim")

    def test_an_indented_duplicate_fails(self):
        self.extra_rows.append(f"   | {self.keep_id} | keep | [The board](#the-board) | Again. |")
        self.assert_one(f"{self.keep_id}: 2 rows")

    def test_a_malformed_id_suffix_fails(self):
        self.extra_rows.append(f"| {self.keep_id}a | keep | [The board](#the-board) | A suffix. |")
        self.assert_one(f"'{self.keep_id}a' is not a well-formed claim or question id")

    def test_a_lower_case_id_fails(self):
        self.extra_rows.append(f"| {self.keep_id.lower()} | keep | [The board](#the-board) | Lower case. |")
        self.assert_one("is not a well-formed claim or question id")

    def test_a_row_indented_four_spaces_fails(self):
        self.extra_rows.append(f"    | {self.alien_id} | keep | [The board](#the-board) | Deep. |")
        self.assert_one("is indented 4 spaces")

    def test_a_row_indented_by_a_tab_fails(self):
        self.extra_rows.append(f"\t| {self.alien_id} | keep | [The board](#the-board) | Tab. |")
        self.assert_one("is indented 4 spaces")

    def test_a_row_without_a_leading_pipe_fails(self):
        self.extra_rows.append(f"{self.alien_id} | keep | [The board](#the-board) | No pipe. |")
        self.assert_one("has no leading pipe")

    def test_open_row_named_only_outside_choices_still_fails(self):
        self.choices = f"## Choices for the owner\n\nNone yet.\n\n## Notes\n\n{self.open_id} is discussed here.\n"
        self.assert_one(f"{self.open_id} is open but not in")


class DecisionsHeadingTest(DesignWorld):
    def test_open_row_under_the_decisions_heading_passes(self):
        self.choices = ("## The owner's decisions (2026-10-12)\n\n"
                        f"1. **Choice** ({self.open_id}). (a) one; (b) two. Decided: (b).\n")
        self.assertEqual(self.problems(), [])

    def test_open_row_missing_from_the_decisions_section_fails(self):
        self.choices = ("## The owner's decisions (2026-10-12)\n\n"
                        f"1. **Other** ({self.keep_id}). Decided: (c).\n")
        self.assert_one(f"{self.open_id} is open but not in")

    def test_no_open_row_needs_no_owner_section(self):
        self.rows[self.open_id] = f"| {self.open_id} | change | [Combat](#combat) | Ties re-rolled. |"
        self.choices = ""
        self.assertEqual(self.problems(), [])


class VarietyWorld(DesignWorld):
    design = "variety.md"
    keep_id, change_id, open_id, alien_id = "C-CRD-01", "C-CRD-02", "C-HAZ-03", "C-CRD-09"


class VarietyCleanTest(VarietyWorld):
    def test_clean_fixture_passes_and_counts(self):
        self.write_design()
        self.assertEqual(check_design.check(self.root, "variety.md"), ([], 3, 3))

    def test_main_exits_1_without_the_variety_design(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_design.main(["--root", str(self.root)])
        self.assertEqual(code, 1)
        lines = out.getvalue().strip().splitlines()
        self.assertEqual(lines, [OK[0], "design/variety.md: missing", OK[2], OK[3]])

    def test_main_names_one_design(self):
        self.write_design()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_design.main(["--root", str(self.root), "design/variety.md"])
        self.assertEqual((code, out.getvalue().strip()), (0, "design/variety.md ok: 3 claims, 3 rows"))

    def test_main_fails_on_a_problem_in_the_second_file_only(self):
        del self.rows["C-CRD-02"]
        self.write_design()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_design.main(["--root", str(self.root)])
        self.assertEqual((code, out.getvalue().strip().splitlines()),
                         (1, [OK[0], "C-CRD-02: no row in design/variety.md", OK[2], OK[3]]))

    def test_variety_spec_file_missing(self):
        (self.root / "spec" / "production-centres.md").unlink()
        self.assert_one_spec_missing()

    def assert_one_spec_missing(self):
        problems = self.problems()
        self.assertEqual(problems, ["spec/production-centres.md: missing"])


class VariantsBanTest(VarietyWorld):
    """design/variants.md has no decision table; only the fence and comment ban applies to it."""

    def run_main(self, variants):
        self.write_design()
        (self.root / "design" / "variants.md").write_text(variants)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_design.main(["--root", str(self.root)])
        return code, out.getvalue().strip().splitlines()

    def test_clean_variants_prints_nothing_extra(self):
        self.assertEqual(self.run_main("# Variants\n\nText.\n"), (0, OK))

    def test_a_fence_in_variants_fails(self):
        code, lines = self.run_main("# Variants\n\n~~~\nx\n~~~\n")
        self.assertEqual(code, 1)
        self.assertEqual(lines[:4], OK)
        self.assertEqual(lines[4:], [l for l in lines[4:] if l.startswith("design/variants.md:")])
        self.assertEqual([l.split(":")[1] for l in lines[4:]], ["3", "5"])

    def test_a_tag_in_variants_fails(self):
        code, lines = self.run_main("# Variants\n\n<div hidden>\n")
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 5, lines)
        self.assertTrue(lines[4].startswith("design/variants.md:3: a raw HTML tag"), lines)

    def test_a_comment_in_variants_fails(self):
        code, lines = self.run_main("# Variants\n\nText <!-- hidden -->.\n")
        self.assertEqual((code, lines[4:]), (1,["design/variants.md:3: an HTML comment; design files may not hold HTML comments"]))


class VarietyFailureTest(VarietyWorld, FailureTest):
    """The five failures, each tripped alone, in design/variety.md."""

    def test_a_core_claim_row_in_the_variety_file_fails(self):
        # Each file is checked against its own spec files: a core claim is foreign here.
        self.extra_rows.append("| C-BRD-01 | keep | [The board](#the-board) | Wrong file. |")
        self.assert_one("C-BRD-01 is not an in-scope spec claim")


class VarietyDecisionsHeadingTest(VarietyWorld, DecisionsHeadingTest):
    """The owner's section, both headings, in design/variety.md."""


class ComputerWorld(DesignWorld):
    design = "computer.md"
    keep_id, change_id, open_id, alien_id = "C-AI-01", "C-AI-02", "C-AI-08", "C-AI-99"


class ComputerCleanTest(ComputerWorld):
    def test_clean_fixture_passes_and_counts(self):
        self.write_design()
        self.assertEqual(check_design.check(self.root, "computer.md"), ([], 3, 3))

    def test_main_exits_1_without_the_computer_design(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_design.main(["--root", str(self.root)])
        self.assertEqual((code, out.getvalue().strip().splitlines()),
                         (1, [OK[0], OK[1], "design/computer.md: missing", OK[3]]))

    def test_main_names_one_design(self):
        self.write_design()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_design.main(["--root", str(self.root), "design/computer.md"])
        self.assertEqual((code, out.getvalue().strip()), (0, OK[2]))

    def test_main_fails_on_a_problem_in_the_third_file_only(self):
        del self.rows["C-AI-02"]
        self.write_design()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_design.main(["--root", str(self.root)])
        self.assertEqual((code, out.getvalue().strip().splitlines()),
                         (1, [OK[0], OK[1], "C-AI-02: no row in design/computer.md", OK[3]]))

    def test_computer_spec_file_missing(self):
        (self.root / "spec" / "computer-opponent.md").unlink()
        problems = self.problems()
        # Every claim then lacks a spec source: the missing file, and each row names an unknown id.
        self.assertEqual(problems[0], "spec/computer-opponent.md: missing")
        self.assertEqual(problems[1:], [f"design/computer.md:{n}: {cid} is not an in-scope spec claim"
                                        for n, cid in self.row_lines()])

    def row_lines(self):
        lines = (self.root / "design" / "computer.md").read_text().splitlines()
        return [(n, line.split("|")[1].strip()) for n, line in enumerate(lines, 1) if line.startswith("| C-")]


class ComputerFailureTest(ComputerWorld, FailureTest):
    """The failures, each tripped alone, in design/computer.md."""

    def test_a_variety_claim_row_in_the_computer_file_fails(self):
        # Each file is checked against its own spec files: a card claim is foreign here.
        self.extra_rows.append("| C-CRD-01 | keep | [Cards](#cards) | Wrong file. |")
        self.assert_one("C-CRD-01 is not an in-scope spec claim")


class ComputerDecisionsHeadingTest(ComputerWorld, DecisionsHeadingTest):
    """The owner's section, both headings, in design/computer.md."""


class UiWorld(DesignWorld):
    design = "ui.md"
    # keep_id and open_id are Q-UI questions, change_id a spec claim, alien_id an unknown question.
    keep_id, change_id, open_id, alien_id = "Q-UI-01", "C-UI-02", "Q-UI-03", "Q-UI-99"


class UiCleanTest(UiWorld):
    def test_clean_fixture_passes_and_counts(self):
        # 2 spec claims and 2 Q-UI questions; Q-CMB-01 and the weakness table's Q-UI-05 do not count.
        self.write_design()
        self.assertEqual(check_design.check(self.root, "ui.md"), ([], 4, 4))

    def test_an_indented_question_row_still_counts(self):
        path = self.root / "questions" / "malpaco.md"
        path.write_text(path.read_text().replace("| Q-UI-03 |", "   | Q-UI-03 |"))
        self.write_design()
        self.assertEqual(check_design.check(self.root, "ui.md"), ([], 4, 4))

    def test_main_exits_1_without_the_ui_design(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_design.main(["--root", str(self.root)])
        self.assertEqual((code, out.getvalue().strip().splitlines()),
                         (1, [OK[0], OK[1], OK[2], "design/ui.md: missing"]))

    def test_main_names_one_design(self):
        self.write_design()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_design.main(["--root", str(self.root), "design/ui.md"])
        self.assertEqual((code, out.getvalue().strip()), (0, OK[3]))

    def test_main_fails_on_a_problem_in_the_fourth_file_only(self):
        del self.rows["Q-UI-01"]
        self.write_design()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_design.main(["--root", str(self.root)])
        self.assertEqual((code, out.getvalue().strip().splitlines()),
                         (1, [OK[0], OK[1], OK[2], "Q-UI-01: no row in design/ui.md"]))

    def test_ui_spec_file_missing(self):
        (self.root / "spec" / "user-interface.md").unlink()
        problems = self.problems()
        # The missing file, and each C-UI row then names an unknown id.
        self.assertEqual(problems[0], "spec/user-interface.md: missing")
        self.assertEqual([p.split(": ", 1)[1] for p in problems[1:]],
                         ["C-UI-01 is not an in-scope spec claim or question",
                          "C-UI-02 is not an in-scope spec claim or question"])

    def test_questions_file_missing(self):
        (self.root / "questions" / "malpaco.md").unlink()
        problems = self.problems()
        # The missing file, and each Q-UI row then names an unknown id.
        self.assertEqual(problems[0], "questions/malpaco.md: missing")
        self.assertEqual([p.split(": ", 1)[1] for p in problems[1:]],
                         ["Q-UI-01 is not an in-scope spec claim or question",
                          "Q-UI-03 is not an in-scope spec claim or question"])


class UiFailureTest(UiWorld, FailureTest):
    """The failures, each tripped alone, in design/ui.md, plus the question-specific ones."""

    def test_a_missing_spec_claim_row(self):
        del self.rows["C-UI-01"]
        self.assert_one("C-UI-01: no row")

    def test_a_missing_question_row(self):
        del self.rows["Q-UI-01"]
        self.assert_one("Q-UI-01: no row")

    def test_an_unknown_question_id(self):
        self.extra_rows.append("| Q-UI-23 | keep | [Screens](#screens) | Invented. |")
        self.assert_one("Q-UI-23 is not an in-scope spec claim or question")

    def test_an_id_named_only_in_the_weakness_table_is_unknown(self):
        # Q-UI-05 is in the questions file, but only inside the weakness table's last cell, not as a row.
        self.extra_rows.append("| Q-UI-05 | keep | [Screens](#screens) | Not a question row. |")
        self.assert_one("Q-UI-05 is not an in-scope spec claim or question")

    def test_a_rules_question_row_is_unknown(self):
        # Q-CMB-01 is a row of the questions file, but not a Q-UI one.
        self.extra_rows.append("| Q-CMB-01 | keep | [Combat](#combat) | Wrong file. |")
        self.assert_one("Q-CMB-01 is not an in-scope spec claim or question")

    def test_a_core_claim_row_in_the_ui_file_fails(self):
        self.extra_rows.append("| C-BRD-01 | keep | [The board](#the-board) | Wrong file. |")
        self.assert_one("C-BRD-01 is not an in-scope spec claim or question")


class UiDecisionsHeadingTest(UiWorld, DecisionsHeadingTest):
    """The owner's section, both headings, in design/ui.md."""


class QuestionRowElsewhereTest(DesignWorld):
    def test_a_question_row_in_core_rules_fails(self):
        # Only ui.md answers questions: a Q-UI row in another design file names an unknown id.
        self.extra_rows.append("| Q-UI-01 | keep | [The board](#the-board) | Wrong file. |")
        self.assert_one("Q-UI-01 is not an in-scope spec claim")

    def test_an_indented_question_row_in_core_rules_fails(self):
        self.extra_rows.append("  | Q-UI-01 | keep | [The board](#the-board) | Wrong file. |")
        self.assert_one("Q-UI-01 is not an in-scope spec claim")

    def test_an_indented_spec_row_still_counts(self):
        # The spec side reads rows with up to 3 spaces too, so an indented claim keeps its coverage.
        path = self.root / "spec" / "board.md"
        path.write_text(path.read_text().replace("| C-BRD-02 |", "  | C-BRD-02 |"))
        self.write_design()
        self.assertEqual(check_design.check(self.root), ([], 3, 3))


class DisguisedRowTest(DesignWorld):
    """Mutation tests for fix #202: each disguise class must fail the check."""

    def setUp(self):
        super().setUp()
        self.ok_rows = list(self.rows.values())

    def _problems_with(self, disguised_line):
        # Replace the design file's decision table with: the OK rows + one disguised row.
        body = TABLE_HEAD + "\n".join(self.ok_rows) + "\n" + disguised_line + "\n"
        text = ("# Rules\n\n## The board\n\nText.\n\n" + self.choices
                + "\n## Decisions, claim by claim\n\n" + body)
        (self.root / "design" / self.design).write_text(text)
        problems, _, _ = check_design.check(self.root, self.design)
        return problems

    def assert_disguise_fails(self, disguise_key, expected_substring):
        problems = self._problems_with(DISGUISED_ROWS[disguise_key])
        disguise_problems = [p for p in problems if expected_substring in p]
        self.assertEqual(
            len(disguise_problems), 1,
            msg=f"{disguise_key!r}: expected one problem containing "
                f"{expected_substring!r}, got {problems!r}",
        )
        where = disguise_problems[0]
        self.assertIn(f"design/{self.design}", where)
        self.assertNotIn(
            "no row in", "".join(problems),
            msg=f"{disguise_key!r}: the disguised line should NOT be parsed as a "
                f"missing row (it should fail closed before that); got {problems!r}",
        )

    def test_blockquote_table_line_fails(self):
        self.assert_disguise_fails("blockquote", "blockquote or list prefix")

    def test_list_bullet_table_line_fails(self):
        self.assert_disguise_fails("list_dash", "blockquote or list prefix")
        self.assert_disguise_fails("list_star", "blockquote or list prefix")

    def test_html_entity_in_table_line_fails(self):
        self.assert_disguise_fails("entity_num", "HTML entity")
        self.assert_disguise_fails("entity_name", "HTML entity")

    def test_lookalike_unicode_hyphen_next_to_id_fails(self):
        self.assert_disguise_fails("lookalike", "look-alike Unicode hyphen")

    def test_clean_design_without_disguise_passes(self):
        # Sanity: the OK rows alone still pass (DesignWorld's setUp completes with a
        # clean design). Pinning keeps the disguise tests from inadvertently flipping
        # the rule on a clean baseline.
        self.write_design()
        problems, _, _ = check_design.check(self.root, self.design)
        self.assertEqual(problems, [])


class RepositoryTest(unittest.TestCase):
    def test_the_repository_design_is_complete(self):
        root = Path(check_design.__file__).resolve().parents[1]
        self.assertEqual(check_design.check(root), ([], 59, 59))

    def test_the_repository_variety_design_is_complete(self):
        root = Path(check_design.__file__).resolve().parents[1]
        self.assertEqual(check_design.check(root, "variety.md"), ([], 23, 23))

    def test_the_repository_computer_design_is_complete(self):
        root = Path(check_design.__file__).resolve().parents[1]
        self.assertEqual(check_design.check(root, "computer.md"), ([], 9, 9))

    def test_the_repository_ui_design_is_complete(self):
        root = Path(check_design.__file__).resolve().parents[1]
        self.assertEqual(check_design.check(root, "ui.md"), ([], 24, 24))


if __name__ == "__main__":
    unittest.main()
