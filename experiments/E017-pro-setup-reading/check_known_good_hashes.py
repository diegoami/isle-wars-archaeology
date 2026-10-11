#!/usr/bin/env python3
"""Contract test for the "Known-good binary hashes" row of F019 (T35).

The row's contract is constraint F of the rule 18 carve-out (CLAUDE.md, 2026-10-08):
a run record (formats/run-1.schema.json) whose `runtime.platform` starts with
`wine-on-user-machine` is allowed only when its `start_state.sha256` is the row's
hash for the set+variant the record names. The gate itself is T36's, in
`tools/check_no_originals.py`; this test is the row-side half. It lives with F019's
experiment record — not in `tools/` (the gate's home), and not in `formats/`, whose
files are vendored upstream bytes pinned by `tests/test_formats.py`.

It fails when the section or any row is removed, when a hash is dropped or
transposed (checked against the static reading's Artifact line and
`artifacts/known.json`, two sources independent of this table), when a provenance
field is left a placeholder, when a row is missing for a set+variant the table
claims to cover, or when the accept/refuse decision stops matching the contract.
Exit status follows unittest: 0 when every check holds.
"""
import json
import re
import unittest
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FINDING = ROOT / "findings" / "F019-pro-setup-rules.md"
REGISTRY = ROOT / "artifacts" / "known.json"

# Every Pro set+variant the F019 Known-good table claims to cover, with the date
# the row was signed. The binary is the same for both rows today
# (artifacts/known.json: 7150739 bytes, sha256 c4d7a248…594e), because the
# successor set declares only xtras/Islepro.skr as a runtime write, not the
# binary (F003). A row whose set is not listed here is a row whose (set, variant)
# pair the table does not intend to cover; removing it would still leave the gate
# operational for the remaining rows, so the missing-row assertion is restricted
# to KNOWN_SETS.
KNOWN_SETS = (
    {"set": "iwp-2.0-996e86c5", "variant": "unregistered", "signed_on": datetime.date(2026, 10, 8)},
    {"set": "iwp-2.0-de5a82a2", "variant": "unregistered", "signed_on": datetime.date(2026, 10, 9)},
)
BINARY = "Islepro.exe"
# The brief's and the finding's pinned hash: one dropped or transposed character
# must fail this test, or the gate would refuse every legitimate run.
KNOWN_HASH = "c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e"
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
    """(set, file, sha256) as the finding's Artifact line pins them. There is one
    Artifact line per finding; with two rows today, both share its binary hash
    because the binary does not change between them (F003)."""
    m = ARTIFACT_LINE.search(FINDING.read_text(encoding="utf-8"))
    assert m, "F019's Artifact line is missing or reshaped"
    return m.group(1), m.group(2), m.group(3)


def registry_hash():
    """Islepro.exe's sha256 for any of the table's sets, as artifacts/known.json
    registers it. With multiple sets covered, the binary is the same, so any one
    suffices; the test asserts each row's hash agrees with this single value."""
    sets = json.loads(REGISTRY.read_text(encoding="utf-8"))["sets"]
    wanted = {s["set"] for s in KNOWN_SETS}
    for entry in sets:
        manifest = entry["manifest"]
        if manifest.get("id") in wanted:
            for f in manifest["files"]:
                if f["path"] == BINARY:
                    return f["sha256"]
    raise AssertionError(
        f"{REGISTRY.name} has no {BINARY} for any of {[s['set'] for s in KNOWN_SETS]}"
    )


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


def wine_record(sha256=KNOWN_HASH, set_id=None, variant=None, platform=WINE_PREFIX):
    """A minimal run-record shape with the fields the gate reads (run/1's paths).
    Defaults to the first known set so single-row calls stay readable."""
    if set_id is None:
        set_id = KNOWN_SETS[0]["set"]
    if variant is None:
        variant = KNOWN_SETS[0]["variant"]
    return {
        "runtime": {"platform": platform},
        "artifact": {"set": set_id, "variant": variant},
        "start_state": {"sha256": sha256},
    }


class RowContractTest(unittest.TestCase):
    def test_every_known_set_has_a_row_with_every_column(self):
        rows = known_good_rows()
        present = {(r["set"], r["variant"]) for r in rows}
        for entry in KNOWN_SETS:
            self.assertIn(
                (entry["set"], entry["variant"]), present,
                f"F019's Known-good table is missing the row for set={entry['set']!r}",
            )
        for row in rows:
            self.assertRegex(row["sha256"], HEX64)
            self.assertRegex(row["install_path"], r"^[A-Z]:\\", row["install_path"])
            self.assertTrue(row["install_path"].endswith("\\"), row["install_path"])
            self.assertNotIn("/", row["install_path"])
            self.assertGreaterEqual(row["install_path"].count("\\"), 4, row["install_path"])
            datetime.date.fromisoformat(row["signed_on"])  # raises when not a real date

    def test_every_row_hash_agrees_with_the_static_pin_and_the_registry(self):
        _, binary, pin = static_pin()
        self.assertEqual(binary, BINARY)
        self.assertEqual(pin, KNOWN_HASH, "Artifact line differs from the pinned hash")
        self.assertEqual(registry_hash(), KNOWN_HASH, "artifacts/known.json differs")
        rows = known_good_rows()
        for row in rows:
            with self.subTest(set=row["set"]):
                self.assertEqual(
                    row["sha256"], KNOWN_HASH,
                    f"row set={row['set']!r} hash differs from the pinned hash",
                )
                self.assertEqual(row["file"], BINARY)

    def test_every_row_provenance_is_real_not_placeholder(self):
        rows = known_good_rows()
        for row in rows:
            with self.subTest(set=row["set"]):
                self.assertEqual(
                    "C:\\Program Files (x86)\\Solsoft\\Isle Wars Pro Game\\", row["install_path"],
                    "install_path is not the install directory",
                )
                for field in row.values():
                    for token in PLACEHOLDER_TOKENS:
                        self.assertNotIn(token, field.lower())
        for entry in KNOWN_SETS:
            row = next(
                r for r in rows
                if r["set"] == entry["set"] and r["variant"] == entry["variant"]
            )
            self.assertEqual(
                datetime.date.fromisoformat(row["signed_on"]), entry["signed_on"],
                f"signed_on for set={entry['set']!r} is not {entry['signed_on']}",
            )

    def test_every_row_install_path_has_no_host_or_placeholder_path(self):
        for row in known_good_rows():
            with self.subTest(set=row["set"]):
                self.assertNotIn("/mnt/", row["install_path"])
                self.assertNotIn("Downloads", row["install_path"])
                self.assertNotIn("<owner>", row["install_path"])

    def test_every_row_hash_is_the_static_reading_pin(self):
        # Rule 17: each row's hash traces to the finding's own pinning, never a guess.
        _, _, pin = static_pin()
        rows = known_good_rows()
        self.assertTrue(
            all(r["sha256"] == pin for r in rows),
            "at least one row's hash differs from the static reading pin",
        )


class GateContractTest(unittest.TestCase):
    """A sample record whose start_state.sha256 matches a row is accepted for that
    set+variant; one whose hash does not match is refused. The test walks every
    known set so the gate's accept/refuse decision is pinned per row."""

    def test_a_matching_record_is_accepted_for_every_known_set(self):
        rows = known_good_rows()
        for entry in KNOWN_SETS:
            with self.subTest(set=entry["set"]):
                record = wine_record(set_id=entry["set"], variant=entry["variant"])
                self.assertTrue(gate_accepts(record, rows))

    def test_a_dropped_or_transposed_character_is_refused_for_every_known_set(self):
        mutated = KNOWN_HASH[:-1] + ("d" if KNOWN_HASH[-1] != "d" else "e")
        rows = known_good_rows()
        for entry in KNOWN_SETS:
            with self.subTest(set=entry["set"]):
                record = wine_record(
                    sha256=mutated, set_id=entry["set"], variant=entry["variant"]
                )
                self.assertFalse(gate_accepts(record, rows))

    def test_the_all_zero_placeholder_is_refused_for_every_known_set(self):
        rows = known_good_rows()
        for entry in KNOWN_SETS:
            with self.subTest(set=entry["set"]):
                record = wine_record(
                    sha256="0" * 64, set_id=entry["set"], variant=entry["variant"]
                )
                self.assertFalse(gate_accepts(record, rows))

    def test_a_hash_match_with_a_foreign_set_or_variant_is_refused(self):
        rows = known_good_rows()
        self.assertFalse(gate_accepts(
            wine_record(set_id="iw-dos-3.1-30121376"), rows,
        ))
        self.assertFalse(gate_accepts(
            wine_record(variant="registered"), rows,
        ))

    def test_the_gate_touches_only_wine_on_user_machine_records(self):
        rows = known_good_rows()
        other = wine_record(sha256="f" * 64, platform="dosbox-x-2024.03.01")
        self.assertTrue(gate_accepts(other, rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
