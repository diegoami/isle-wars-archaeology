#!/usr/bin/env python3
"""Contract test for the "Known-good binary hashes" row of F019 (T35).

The row's contract is constraint F of the rule 18 carve-out (CLAUDE.md, 2026-10-08):
a run record (formats/run-1.schema.json) whose `runtime.platform` starts with
`wine-on-user-machine` is allowed only when its `start_state.sha256` is the row's
hash for the set+variant the record names. The gate itself is T36's, in
`tools/check_no_originals.py`; this test is the row-side half. It lives with F019's
experiment record — not in `tools/` (the gate's home), and not in `formats/`, whose
files are vendored upstream bytes pinned by `tests/test_formats.py`.

It fails when the section or the row is removed, when the hash is dropped or
transposed (checked against the static reading's Artifact line and
`artifacts/known.json`, two sources independent of this table), when a provenance
field is left a placeholder, or when the accept/refuse decision stops matching the
contract. Exit status follows unittest: 0 when every check holds.
"""
import json
import re
import unittest
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FINDING = ROOT / "findings" / "F019-pro-setup-rules.md"
REGISTRY = ROOT / "artifacts" / "known.json"

SET_ID = "iwp-2.0-996e86c5"
VARIANT = "unregistered"
BINARY = "Islepro.exe"
# The brief's and the finding's pinned hash: one dropped or transposed character
# must fail this test, or the gate would refuse every legitimate run.
KNOWN_HASH = "c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e"
SIGNED_ON = datetime.date(2026, 10, 8)
WINE_PREFIX = "wine-on-user-machine"  # exact lowercase; T36 owns the case contract
PLACEHOLDER_TOKENS = ("<date>", "<placeholder>", "tbd", "todo", "example.com")

HEX64 = re.compile(r"^[0-9a-f]{64}$")
ARTIFACT_LINE = re.compile(
    r"^- \*\*Artifact\*\*: set `([^`]+)`, `([^`]+)`, sha256 `([0-9a-f]{64})`", re.M
)
COLUMNS = ("set", "variant", "file", "sha256", "install_path", "signed_on")


def known_good_rows():
    """The rows of F019's "Known-good binary hashes" table, as dicts.

    Raises AssertionError when the section or any row's shape is missing, so a
    removed row is a failure here, not a silent empty gate."""
    text = FINDING.read_text(encoding="utf-8")
    m = re.search(r"^## Known-good binary hashes\s*$", text, re.M)
    assert m, "F019 has no '## Known-good binary hashes' section"
    section = text[m.end():]
    nxt = re.search(r"^## ", section, re.M)
    if nxt:
        section = section[:nxt.start()]
    rows = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cells):  # separator row
            continue
        if cells and cells[0].lower() == "set":  # header row
            continue
        assert len(cells) == len(COLUMNS), f"row has {len(cells)} cells, want {len(COLUMNS)}: {cells}"
        row = dict(zip(COLUMNS, (c.strip("`") for c in cells)))
        rows.append(row)
    assert rows, "the Known-good binary hashes table has no row"
    return rows


def static_pin():
    """(set, file, sha256) as the finding's Artifact line pins them."""
    m = ARTIFACT_LINE.search(FINDING.read_text(encoding="utf-8"))
    assert m, "F019's Artifact line is missing or reshaped"
    return m.group(1), m.group(2), m.group(3)


def registry_hash():
    """Islepro.exe's sha256 for the set, as artifacts/known.json registers it."""
    sets = json.loads(REGISTRY.read_text(encoding="utf-8"))["sets"]
    for entry in sets:
        manifest = entry["manifest"]
        if manifest.get("id") == SET_ID:
            for f in manifest["files"]:
                if f["path"] == BINARY:
                    return f["sha256"]
    raise AssertionError(f"{REGISTRY.name} has no {BINARY} for set {SET_ID}")


def gate_accepts(record, rows):
    """Constraint F, row-side: a wine-on-user-machine record is allowed only on an
    exact (set, variant, sha256) row; any other record passes this gate untouched
    (the existing no-originals checks do the rest). The platform test is case-
    sensitive startswith, the contract T36's mutation tests name."""
    if not record["runtime"]["platform"].startswith(WINE_PREFIX):
        return True
    return any(
        r["set"] == record["artifact"]["set"]
        and r["variant"] == record["artifact"]["variant"]
        and r["sha256"] == record["start_state"]["sha256"]
        for r in rows
    )


def wine_record(sha256=KNOWN_HASH, set_id=SET_ID, variant=VARIANT, platform=WINE_PREFIX):
    """A minimal run-record shape with the fields the gate reads (run/1's paths)."""
    return {
        "runtime": {"platform": platform},
        "artifact": {"set": set_id, "variant": variant},
        "start_state": {"sha256": sha256},
    }


class RowContractTest(unittest.TestCase):
    def test_the_row_exists_with_every_column(self):
        rows = known_good_rows()
        self.assertIn((SET_ID, VARIANT), [(r["set"], r["variant"]) for r in rows])
        for row in rows:
            self.assertRegex(row["sha256"], HEX64)
            self.assertTrue(row["install_path"].startswith("/"), row["install_path"])
            self.assertTrue(row["install_path"].endswith("/"), row["install_path"])
            self.assertGreaterEqual(row["install_path"].count("/"), 5, row["install_path"])
            datetime.date.fromisoformat(row["signed_on"])  # raises when not a real date

    def test_the_row_hash_agrees_with_both_independent_sources(self):
        set_id, binary, pin = static_pin()
        self.assertEqual((set_id, binary), (SET_ID, BINARY))
        self.assertEqual(pin, KNOWN_HASH, "Artifact line differs from the pinned hash")
        self.assertEqual(registry_hash(), KNOWN_HASH, "artifacts/known.json differs")
        row = next(r for r in known_good_rows() if r["set"] == SET_ID and r["variant"] == VARIANT)
        self.assertEqual(row["sha256"], KNOWN_HASH, "the table row is not the pinned hash")
        self.assertEqual(row["file"], BINARY)

    def test_the_row_provenance_is_real_not_placeholder(self):
        row = next(r for r in known_good_rows() if r["set"] == SET_ID and r["variant"] == VARIANT)
        self.assertIn("Downloads/Isle-Wars-Pro_Win_EN_v20-Shareware/", row["install_path"])
        for field in row.values():
            for token in PLACEHOLDER_TOKENS:
                self.assertNotIn(token, field.lower())
        self.assertEqual(datetime.date.fromisoformat(row["signed_on"]), SIGNED_ON)

    def test_the_row_hash_is_the_static_reading_pin(self):
        # Rule 17: the row's hash traces to the finding's own pinning, never a guess.
        _, _, pin = static_pin()
        rows = known_good_rows()
        self.assertTrue(any(r["sha256"] == pin for r in rows))


class GateContractTest(unittest.TestCase):
    """A sample record whose start_state.sha256 matches the row is accepted; one
    whose hash does not match is refused (the brief's contract, T36's gate)."""

    def test_a_matching_record_is_accepted(self):
        self.assertTrue(gate_accepts(wine_record(), known_good_rows()))

    def test_a_dropped_or_transposed_character_is_refused(self):
        mutated = KNOWN_HASH[:-1] + ("d" if KNOWN_HASH[-1] != "d" else "e")
        self.assertFalse(gate_accepts(wine_record(sha256=mutated), known_good_rows()))

    def test_the_all_zero_placeholder_is_refused(self):
        self.assertFalse(gate_accepts(wine_record(sha256="0" * 64), known_good_rows()))

    def test_a_hash_match_with_a_foreign_set_or_variant_is_refused(self):
        rows = known_good_rows()
        self.assertFalse(gate_accepts(wine_record(set_id="iw-dos-3.1-30121376"), rows))
        self.assertFalse(gate_accepts(wine_record(variant="registered"), rows))

    def test_the_gate_touches_only_wine_on_user_machine_records(self):
        other = wine_record(sha256="f" * 64, platform="dosbox-x-2024.03.01")
        self.assertTrue(gate_accepts(other, known_good_rows()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
