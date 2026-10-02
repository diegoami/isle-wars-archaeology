#!/usr/bin/env python3
"""Check that `>` blockquote lines in a sources Markdown file quote an original text file.

Usage: check_quotes.py <original> <sources.md> [--encoding NAME]

Every line whose first non-space character is `>` is a blockquote line and must
occur in the original once whitespace is collapsed on both sides (runs of
whitespace become one space and the ends are stripped), so a quote may wrap
lines differently than the original. A blockquote line that is only a citation
(`Islepro.txt:12-14`) is not a quote. The quoted characters must not exceed 25%
of the original's characters; that 25% is a designed policy value (the user's
instruction of 2026-10-02), not a finding from the games. Both sides are
counted after the same collapse, and a quote repeated on several lines counts
once, so a copy-paste cannot inflate or dodge the share.

Blockquote lines are recognised with no fence tracking: fenced code is not
special-cased, so a `>` line inside a code fence is checked like any other, and
a stray `>` in a code block makes the checker reject the file — it fails
closed, the safe direction (the task never asked for code-fence handling, and
each fence rule tried so far was a way to hide a copy; reviews R1 and round 2).
Each failing quote is printed with its line number in the sources file, and
when the share cap is exceeded, every quote counted toward the cap is printed
with the sources-file line number of its first occurrence.

The original is decoded with --encoding (default cp1252, the usual encoding of Windows-era
plain text, so T04 can invoke the tool without a flag); the sources file is a repository
file and is always UTF-8. Tests use synthetic text only; no game text is embedded here.

Exit 0 when all quotes pass, 1 on any failed quote or an exceeded share, 2 on a usage
error (bad arguments, or a file that cannot be read or decoded).
"""
import re
import sys
from pathlib import Path

# Designed policy value (the user's instruction of 2026-10-02), not a finding: at most
# CAP_NUMERATOR/CAP_DENOMINATOR of an original's characters may be quoted. The comparison
# stays in integers, so a share of exactly 25% passes.
CAP_NUMERATOR = 1
CAP_DENOMINATOR = 4

# cp1252: the usual encoding of Windows-era plain text (the originals' encoding is not
# known, 07 §4 W2), and T04 invokes the tool without a flag
# (tests/test_check_quotes.py::test_cp1252_byte_decoded).
DEFAULT_ENCODING = "cp1252"

# A citation line such as `Islepro.txt:12-14` or `Order.txt:3` (T04 cites this way): a
# file-ish name, a dot extension, a colon, and a line number or range. Not a quote.
CITATION = re.compile(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+:[0-9]+(?:-[0-9]+)?$")

# Markdown blockquote markers: leading indentation, then one or more `>` (nesting), then
# the space that conventionally follows the marker.
MARKERS = re.compile(r"^(?:\s*>)+\s*")

USAGE = "check_quotes.py <original> <sources.md> [--encoding NAME]"


def collapse(text):
    """Collapse runs of whitespace to one space and strip the ends; the only normalisation."""
    return " ".join(text.split())


def blockquote_lines(lines):
    """Yield (line number, collapsed content) for each `>` blockquote line in the sources.

    Any line whose first non-space character is `>` counts, wherever it sits:
    there is no fence tracking, so a `>` line inside a fenced code block is
    checked like any other and rejects the file when it quotes nothing from
    the original — the fail-closed direction
    (tests/test_check_quotes.py::test_fence_content_quote_line_is_checked;
    the reviewer's round-2 phantom-fence inputs are covered by
    ::test_review_fence_inputs_then_whole_copy_exit_1).
    """
    for number, line in enumerate(lines, 1):
        if not line.lstrip().startswith(">"):
            continue
        content = collapse(MARKERS.sub("", line))
        if content:  # an empty blockquote line quotes nothing
            yield number, content


def check(original_text, sources_lines):
    """Return (failures, n_quotes, quoted_chars, original_chars); no failures means pass.

    n_quotes counts distinct quotes: a quote repeated on several lines counts once
    against the cap, and a cap failure reports each counted quote at the line of its
    first occurrence (review R2).
    """
    original = collapse(original_text)
    failures = []
    quotes = {}  # content -> first line number; a repeated quote counts once
    for number, content in blockquote_lines(sources_lines):
        if CITATION.match(content):
            # A line that is only a citation points at the original; it is not quoted text
            # (tests/test_check_quotes.py::test_citation_line_is_not_a_quote).
            continue
        if content not in original:
            failures.append(f"line {number}: quote not in original: {content}")
        quotes.setdefault(content, number)
    # Distinct quotes only: a quote repeated on several lines counts once against the cap
    # (tests/test_check_quotes.py::test_repeated_quote_counts_once).
    quoted_chars = sum(len(quote) for quote in quotes)
    if quoted_chars * CAP_DENOMINATOR > len(original) * CAP_NUMERATOR:
        # Integer comparison: exactly CAP_NUMERATOR/CAP_DENOMINATOR passes
        # (tests/test_check_quotes.py::test_share_exactly_25_percent_passes).
        # An empty original with a quote is over the cap by any measure
        # (tests/test_check_quotes.py::test_empty_original_with_quote_exits_1).
        # Each quote counted toward the cap is reported at its first line, so a cap
        # failure carries the sources-file line numbers the cap was computed from
        # (review R2; tests/test_check_quotes.py::
        # test_cap_failure_lists_line_of_each_counted_quote and
        # ::test_cap_failure_lists_repeated_quote_once_at_first_line).
        for quote, first_number in quotes.items():
            failures.append(f"line {first_number}: quote counts toward the cap: {quote}")
        share = f"{100 * quoted_chars / len(original):.1f}%" if original else "100.0%"
        failures.append(
            f"quoted {quoted_chars} of {len(original)} characters ({share}), over the "
            f"{100 * CAP_NUMERATOR // CAP_DENOMINATOR}% cap"
        )
    return failures, len(quotes), quoted_chars, len(original)


def usage_error(message):
    print(f"check_quotes.py: {message}\nusage: {USAGE}", file=sys.stderr)


def main(argv):
    encoding = DEFAULT_ENCODING
    positional = []
    arguments = list(argv)
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--encoding":
            index += 1
            if index == len(arguments):
                usage_error("--encoding needs a value")
                return 2
            encoding = arguments[index]
        elif argument.startswith("--encoding="):
            encoding = argument.split("=", 1)[1]
        elif argument in ("-h", "--help"):
            print(f"usage: {USAGE}")
            return 0
        else:
            positional.append(argument)
        index += 1
    if len(positional) != 2:
        usage_error(f"expected <original> <sources.md>, got {len(positional)} argument(s)")
        return 2
    original_path, sources_path = positional
    try:
        original_text = Path(original_path).read_bytes().decode(encoding)
    except (OSError, LookupError, UnicodeDecodeError) as error:
        usage_error(f"cannot read {original_path} as {encoding}: {error}")
        return 2
    try:
        sources_text = Path(sources_path).read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        usage_error(f"cannot read {sources_path} as utf-8: {error}")
        return 2
    failures, n_quotes, quoted_chars, original_chars = check(
        original_text, sources_text.splitlines()
    )
    if failures:
        for failure in failures:
            print(f"{sources_path}: {failure}")
        return 1
    share = f"{100 * quoted_chars / original_chars:.1f}%" if original_chars else "0.0%"
    print(
        f"quotes ok ({n_quotes} quotes, {quoted_chars} of {original_chars} characters, {share})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
