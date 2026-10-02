"""Tests for tools/check_quotes.py. Every fixture is synthetic text; no game text (T06)."""
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import check_quotes  # noqa: E402

# Synthetic plain text (about 580 characters once collapsed): long enough that the
# short quotes used in the tests stay under the 25% cap.
SYNTHETIC = "\n".join(
    [
        "This synthetic text file exists only to test the quote",
        "checker; it is not a game file and copies nothing real.",
        "More filler sentences follow so the total is long enough",
        "that short quotes stay comfortably under the share cap.",
        "The quick brown fox jumps over the lazy dog once more.",
        "Pack my box with five dozen liquor jugs, then rest a while.",
        "How vexingly quick daft zebras jump when they are provoked.",
        "Sphinx of black quartz, judge my vow before the evening.",
        "The five boxing wizards jump quickly onward and upward.",
        "Bright vixens jump; dozy fowl quack quickly at each other.",
    ]
).encode("cp1252")


def run_checker(original_bytes, sources_text, args=()):
    """Write the two synthetic files to a temp dir, run main, return (code, stdout, stderr)."""
    with tempfile.TemporaryDirectory() as tmp:
        original = Path(tmp) / "Synthetic.txt"
        original.write_bytes(original_bytes)
        sources = Path(tmp) / "sources.md"
        sources.write_text(sources_text, encoding="utf-8")
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = check_quotes.main([str(original), str(sources), *args])
    return code, out.getvalue(), err.getvalue()


class ValidQuotes(unittest.TestCase):
    def test_valid_quotes_pass(self):
        sources = "\n".join(
            [
                "# Notes",
                "",
                "> test the quote checker; it is not a game file",
                ">",
                "> The quick brown fox jumps over the lazy dog once more.",
                "",
                "> Synthetic.txt:1-3",
                "> Synthetic.txt:5",
            ]
        )
        code, out, err = run_checker(SYNTHETIC, sources)
        self.assertEqual(code, 0, err)
        self.assertIn("quotes ok", out)

    def test_citation_line_is_not_a_quote(self):
        # `Synthetic.txt:1-3` and `Synthetic.txt:5` occur nowhere in the original: if
        # citation lines counted as quotes, they would fail the presence check.
        sources = "\n".join(
            [
                "> The quick brown fox jumps over the lazy dog once more.",
                "",
                "> Synthetic.txt:1-3",
                "> Synthetic.txt:5",
            ]
        )
        code, out, err = run_checker(SYNTHETIC, sources)
        self.assertEqual(code, 0, err)

    def test_fence_line_is_not_a_quote(self):
        # The fenced `>` line occurs nowhere in the original: if it counted as a
        # blockquote, the check would fail.
        sources = "\n".join(
            [
                "# Notes",
                "",
                "> The quick brown fox jumps over the lazy dog once more.",
                "",
                "```text",
                "> this fenced line is not a blockquote and is nowhere in the original",
                "```",
            ]
        )
        code, out, err = run_checker(SYNTHETIC, sources)
        self.assertEqual(code, 0, err)

    def test_indented_code_line_inside_fence_does_not_close_it(self):
        # A fence closes only with backticks within the first three columns of
        # the line (review R1): the four-space-indented (or tab-indented) ```
        # line below is fenced code, not the closing fence, so the `>` line
        # after it stays fenced and unchecked — it occurs nowhere in the
        # original, so an early close would fail the check.
        for closer in ("    ```", "\t```"):
            with self.subTest(closer=repr(closer)):
                sources = "\n".join(
                    [
                        "> The quick brown fox jumps over the lazy dog once more.",
                        "",
                        "```text",
                        closer,
                        "> this still fenced line occurs nowhere in the original",
                        "```",
                    ]
                )
                code, out, err = run_checker(SYNTHETIC, sources)
                self.assertEqual(code, 0, err)


class FailingQuotes(unittest.TestCase):
    def test_absent_quote_exits_1(self):
        sources = "\n".join(
            [
                "# Notes",
                "",
                "> This sentence appears nowhere in the synthetic original.",
            ]
        )
        code, out, _ = run_checker(SYNTHETIC, sources)
        self.assertEqual(code, 1)
        self.assertIn("line 3:", out)
        self.assertIn("quote not in original", out)
        self.assertIn("This sentence appears nowhere in the synthetic original.", out)

    def test_quote_after_indented_code_line_is_checked(self):
        # Backticks indented four spaces (or one tab) are an indented code
        # block, not a fence (review R1): the blockquote after them must still
        # be checked, and this one is absent from the original. Without the
        # fence fix the indented line opened a phantom fence, the blockquote
        # was swallowed, and the check exited 0.
        for opener in ("    ```text", "\t```text"):
            with self.subTest(opener=repr(opener)):
                sources = "\n".join(
                    [
                        opener,
                        "> This sentence appears nowhere in the synthetic original.",
                    ]
                )
                code, out, _ = run_checker(SYNTHETIC, sources)
                self.assertEqual(code, 1)
                self.assertIn("line 2:", out)
                self.assertIn("quote not in original", out)

    def test_whole_copy_after_indented_code_line_exits_1(self):
        # The reviewer's adversarial case (review R1): the whole original
        # quoted as one blockquote after a four-space-indented ``` line used to
        # exit 0 reporting zero quotes; it must exit 1 over the cap.
        whole = " ".join(SYNTHETIC.decode("cp1252").split())
        code, out, _ = run_checker(SYNTHETIC, "    ```text\n> " + whole + "\n")
        self.assertEqual(code, 1)
        self.assertIn("25% cap", out)

    def test_share_over_25_percent_exits_1(self):
        # 11 of 40 characters is 27.5%: over the cap, while the quote itself is present.
        code, out, _ = run_checker(b"a" * 40 + b"\n", "> " + "a" * 11 + "\n")
        self.assertEqual(code, 1)
        self.assertIn("25% cap", out)
        self.assertNotIn("not in original", out)

    def test_share_exactly_25_percent_passes(self):
        # 10 of 40 characters is exactly 25%: at the cap, not over it.
        code, out, err = run_checker(b"a" * 40 + b"\n", "> " + "a" * 10 + "\n")
        self.assertEqual(code, 0, err)
        self.assertIn("quotes ok", out)

    def test_repeated_quote_counts_once(self):
        # The same 10-character quote on two lines is still 10 of 40 characters,
        # exactly 25%: counted twice it would be 50% and fail.
        quote = "> " + "a" * 10
        code, out, err = run_checker(b"a" * 40 + b"\n", quote + "\n" + quote + "\n")
        self.assertEqual(code, 0, err)

    def test_cap_failure_lists_line_of_each_counted_quote(self):
        # Two distinct quotes, 22 of 80 characters (27.5%): over the cap, and
        # every quote counted toward the cap is printed with its sources-file
        # line number (review R2).
        sources = "> " + "b" * 11 + "\n\n> " + "c" * 11 + "\n"
        code, out, _ = run_checker(b"b" * 40 + b"c" * 40, sources)
        self.assertEqual(code, 1)
        self.assertIn("line 1:", out)
        self.assertIn("line 3:", out)
        self.assertIn("counts toward the cap", out)
        self.assertIn("25% cap", out)

    def test_cap_failure_lists_repeated_quote_once_at_first_line(self):
        # A quote repeated on several lines counts once against the cap, so a
        # cap failure reports it once, at the line of its first occurrence
        # (review R2); 21 of 40 characters is 52.5%.
        quote = "> " + "b" * 21
        code, out, _ = run_checker(b"b" * 40 + b"\n", quote + "\n" + quote + "\n")
        self.assertEqual(code, 1)
        self.assertIn("line 1:", out)
        self.assertNotIn("line 2:", out)
        self.assertIn("25% cap", out)

    def test_empty_original_with_quote_exits_1(self):
        # A quote of an empty original fails presence and the cap without a crash.
        code, out, _ = run_checker(b"", "> anything at all\n")
        self.assertEqual(code, 1)
        self.assertIn("quote not in original", out)
        self.assertIn("25% cap", out)


class Wrapping(unittest.TestCase):
    def test_match_across_differing_line_wrap(self):
        # The original wraps between "quote" and "checker;" (lines 1-2); the sources
        # quote that span on one line, and split line 6 at a point where the original
        # does not wrap. Collapsing whitespace must make both match.
        sources = "\n".join(
            [
                "> test the quote checker; it is not a game file",
                "> Pack my box with five dozen",
                "> liquor jugs, then rest a while.",
            ]
        )
        code, out, err = run_checker(SYNTHETIC, sources)
        self.assertEqual(code, 0, err)


class Encoding(unittest.TestCase):
    # Built from bytes: 0x92 is the cp1252 right single quote, not a UTF-8 byte.
    ORIGINAL = b"\n".join(
        [
            b"A synthetic file for the encoding check, nothing more.",
            b"The machine\x92s owner said it\x92s synthetic, not a game file.",
            b"More filler keeps the quoted share far below the cap.",
            b"Even more filler text keeps it under a quarter.",
            b"Filler continues here with plain ascii wording.",
            b"Another filler line pads the character count.",
        ]
    )

    def test_cp1252_byte_decoded(self):
        # 0x92 is the cp1252 right single quote; the sources file holds the same
        # character in UTF-8. The default encoding must decode it, and --encoding
        # must reach the decoder: utf-8 cannot decode this byte at all.
        sources = "> The machine\u2019s owner said it\u2019s synthetic, not a game file.\n"
        self.assertIn(b"\x92", self.ORIGINAL)
        code, out, err = run_checker(self.ORIGINAL, sources)
        self.assertEqual(code, 0, err)
        code, _, err = run_checker(self.ORIGINAL, sources, ["--encoding", "utf-8"])
        self.assertEqual(code, 2, err)
        self.assertIn("utf-8", err)


class Usage(unittest.TestCase):
    def test_no_arguments_exit_2(self):
        for argv in ([], ["only-one-argument"]):
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = check_quotes.main(argv)
            self.assertEqual(code, 2, argv)
            self.assertIn("usage:", err.getvalue())

    def test_no_arguments_exit_2_end_to_end(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "check_quotes.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("usage:", result.stderr)

    def test_unreadable_original_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources = Path(tmp) / "sources.md"
            sources.write_text("> anything\n", encoding="utf-8")
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = check_quotes.main([str(Path(tmp) / "missing.txt"), str(sources)])
        self.assertEqual(code, 2)
        self.assertIn("usage:", err.getvalue())


if __name__ == "__main__":
    unittest.main()
