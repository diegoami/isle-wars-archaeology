#!/usr/bin/env python3
"""Remove each guarantee of the static tools in turn and show that its tests then fail (T26
Done-when 3, CLAUDE.md rule 9). Usage: python3 tests/mutants_static.py

Each mutant replaces one exact piece of source (it must occur exactly once), runs the named tests,
and restores the file whatever happens. A mutant is killed when the tests fail. The script exits 0
only when every mutant is killed and the unmutated tests pass; it exits 2 when any target test
skips (a skip shows nothing). It edits tracked files while it runs: run it in a clean worktree,
with TMPDIR set to a directory outside every checkout.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
T = "tests.test_static."
CO = T + "CheckoutRefusalTest"
OR = T + "OriginalRefusalTest"
SC = "tools/static/static_common.py"
DU = "tools/static/dos_unpack.py"
DP = "tools/static/dos_probe.py"
IV = "tools/static/inventory_derived.py"
IN = T + "InventoryTest"
MUTANTS = [
    # ---- the output never lands in a checkout; IWA_STATIC must be set and confined
    ("IWA_STATIC is not confined (unset, relative, in a checkout, over the repository)", SC,
     'return locations.confine("IWA_STATIC", env.get("IWA_STATIC"), others)',
     'return locations.real(env.get("IWA_STATIC") or "/nonexistent")',
     [CO + ".test_every_script_refuses_an_unset_static_folder_and_creates_nothing",
      CO + ".test_every_script_refuses_a_relative_static_folder",
      CO + ".test_every_script_refuses_a_static_folder_inside_a_checkout_and_writes_nothing",
      CO + ".test_every_script_refuses_a_static_folder_that_is_a_link_into_a_checkout"]),
    ("the static folder may overlap the original's folder", SC,
     "others = [(ORIGINALS[key][1], original_dir(key, env)) for key in originals]", "others = []",
     [CO + ".test_every_script_refuses_a_static_folder_that_overlaps_the_original"]),
    ("a run may reuse a run directory", SC,
     'except FileExistsError:\n        die(f"{name} already exists in the static root; a run never reuses a directory")',
     "except FileExistsError:\n        pass",
     [CO + ".test_a_run_never_reuses_a_directory"]),
    ("a link in the original's own name is read through", SC,
     "    with safeio.open_source(path) as fh:\n        for chunk in iter(lambda: fh.read(1 << 20), b\"\"):\n            digest.update(chunk)\n            size += len(chunk)",
     "    with open(path, \"rb\") as fh:\n        for chunk in iter(lambda: fh.read(1 << 20), b\"\"):\n            digest.update(chunk)\n            size += len(chunk)",
     [OR + ".test_an_original_that_is_a_link_is_not_read_through"]),
    # ---- an original that does not match its registered sha256 is not read
    ("an original is read without comparing it with its registered sha256", SC,
     "    if (observed_sha, observed_size) != (sha256, size):\n        die(f\"{rel} is not the registered file",
     "    if False:\n        die(f\"{rel} is not the registered file",
     [OR + ".test_a_changed_original_is_refused_by_every_script_and_nothing_is_made",
      OR + ".test_a_truncated_original_is_refused"]),
    ("the bytes a script uses are not checked again against the registered hash", SC,
     "if sha256_bytes(data) != self.sha256 or len(data) != self.size:", "if False:",
     [OR + ".test_the_bytes_a_script_uses_are_the_registered_ones_even_if_the_file_changes_after_the_check"]),
    ("the original is not hashed again after a tool read it by its path", SC,
     "        if (sha, size) != (self.sha256, self.size):\n            die(f\"{self.rel} is not the registered file after the tool ran\")",
     "        if False:\n            die(f\"{self.rel} is not the registered file after the tool ran\")",
     [OR + ".test_the_bytes_a_script_uses_are_the_registered_ones_even_if_the_file_changes_after_the_check"]),
    ("a derived file given to ghidra_import or dos_probe is not compared with its sha256", SC,
     "    if sha != sha256:\n        die(f\"{name} is not the file", "    if False:\n        die(f\"{name} is not the file",
     [OR + ".test_a_ghidra_file_input_must_match_the_given_sha256",
      T + "DosProbeTest.test_a_file_with_another_sha256_or_outside_the_static_folder_is_refused"]),
    ("a derived-file name may climb out of the static folder", SC,
     '    if rel.is_absolute() or ".." in rel.parts:', "    if False:",
     [OR + ".test_a_ghidra_file_input_must_match_the_given_sha256",
      T + "DosProbeTest.test_a_file_with_another_sha256_or_outside_the_static_folder_is_refused"]),
    ("dos_probe reads bytes other than the ones whose hash was checked", DP,
     "    if common.sha256_bytes(data) != args.sha256:", "    if False:",
     [T + "DosProbeTest.test_the_bytes_read_are_the_ones_whose_hash_was_checked"]),
    ("dos_probe takes IWA_STATIC without confining it", DP,
     "    root = common.static_root(env)",
     '    root = Path(env["IWA_STATIC"]) if env and env.get("IWA_STATIC") else Path("/nonexistent")',
     [T + "DosProbeTest.test_an_unset_or_in_checkout_static_folder_is_refused"]),
    ("dos_probe reads any four bytes before a text as its descriptor", DP,
     'item["descriptor_layout_holds"] = length == len(raw)', 'item["descriptor_layout_holds"] = True',
     [T + "DosProbeTest.test_a_text_without_a_descriptor_before_it_is_not_read_as_one"]),
    # ---- dos_unpack: Deark writes only into the run directory; the original is checked before and after
    ("dos_unpack lets the static folder overlap the original's folder", DU,
     "    root = common.static_root(env, originals=(args.original,))", "    root = common.static_root(env)",
     [CO + ".test_every_script_refuses_a_static_folder_that_overlaps_the_original"]),
    ("dos_unpack has Deark write next to its input", DU,
     '"-od", run_dir, "-o", name, source]', '"-od", Path(source).parent, "-o", name, source]',
     [T + "DosUnpackTest.test_two_stages_write_into_the_static_folder_and_a_record_holds_numbers_only"]),
    ("dos_unpack does not hash the original again after Deark read it", DU,
     "    finally:\n        original.recheck()", "    finally:\n        pass",
     [T + "DosUnpackTest.test_an_original_that_changes_while_deark_reads_it_is_caught"]),
    ("dos_unpack accepts a stage that failed", DU,
     "    if code != 0:\n        common.die(f\"Deark's", "    if False:\n        common.die(f\"Deark's",
     [T + "DosUnpackTest.test_a_stage_that_fails_or_writes_more_than_one_file_stops_the_run"]),
    ("dos_unpack accepts a stage that wrote several files", DU,
     "    if len(made) != 1:", "    if False:",
     [T + "DosUnpackTest.test_a_stage_that_fails_or_writes_more_than_one_file_stops_the_run"]),
    ("dos_unpack exits 0 for an image that is not plausible", DU,
     '    return 0 if result["unpacked"]["plausible"] else 1', "    return 0",
     [T + "DosUnpackTest.test_an_image_still_packed_is_not_plausible"]),
    ("a relocation outside the load module passes", DU,
     "            if at + 2 > module:", "            if False:",
     [T + "DosUnpackTest.test_the_plausibility_checks_each_fail_on_their_own_defect"]),
    ("an entry point outside the load module passes", DU,
     "    if entry >= module:", "    if False:",
     [T + "DosUnpackTest.test_the_plausibility_checks_each_fail_on_their_own_defect"]),
    ("an image still holding EXEPACK's decoder passes", DU,
     "    if EXEPACK_TEXT in data:", "    if False:",
     [T + "DosUnpackTest.test_the_plausibility_checks_each_fail_on_their_own_defect",
      T + "DosUnpackTest.test_an_image_still_packed_is_not_plausible"]),
    ("an image still holding the PKLITE text passes", DU,
     "    if data.find(PKLITE_TEXT) == 30:", "    if False:",
     [T + "DosUnpackTest.test_the_plausibility_checks_each_fail_on_their_own_defect"]),
    ("ghidra_import passes a malformed range to the post-script", "tools/static/ghidra_import.py",
     "        if not RANGE.fullmatch(item):", "        if False:",
     [T + "GhidraRangeTest.test_a_malformed_range_is_refused_before_anything_runs"]),
    ("ghidra_import does not give Ghidra a dot-free project path", "tools/static/ghidra_import.py",
     '    if not any(part.startswith(".") for part in Path(project).parts):', "    if True:",
     [CO + ".test_a_dot_folder_in_the_static_path_is_handled_for_ghidra"]),
    # ---- what reaches a tracked path
    ("a record with a machine path is written", SC,
     "    if found:\n        die(f\"the record", "    if False:\n        die(f\"the record",
     [T + "RecordTest.test_a_record_with_a_machine_path_is_refused_and_nothing_is_written"]),
    ("a record replaces an earlier one", SC,
     'data=text.encode("ascii"), exist="new",', 'data=text.encode("ascii"), exist="replace",',
     [T + "RecordTest.test_a_record_is_never_overwritten"]),
    ("a tracked file with a listed hash passes", "tools/static/check_derived_hashes.py",
     "        elif sha256_file(path) in listed:", "        elif False:",
     [T + "DerivedHashesTest.test_a_tracked_file_with_a_listed_hash_fails"]),
    # round 2, R3: the empty-file exemption of the amended Done-when 4, no wider and no narrower
    ("an empty tracked file is compared like any other", "tools/static/check_derived_hashes.py",
     "        elif path.stat().st_size == 0:", "        elif False:",
     [IN + ".test_an_empty_tracked_file_is_exempt_even_when_a_run_left_an_empty_file"]),
    ("a one-byte tracked file is exempt as well", "tools/static/check_derived_hashes.py",
     "        elif path.stat().st_size == 0:", "        elif path.stat().st_size <= 1:",
     [IN + ".test_an_empty_tracked_file_is_exempt_even_when_a_run_left_an_empty_file"]),
    ("a tracked file named like a derived output passes", "tools/static/check_derived_hashes.py",
     "        if DERIVED_NAME.search(Path(name).name):", "        if False:",
     [T + "DerivedHashesTest.test_a_tracked_file_named_like_a_derived_output_fails_whatever_its_bytes"]),
    # ---- the tools check
    ("a tool whose file has another sha256 is ready", "setup/static/check_tools.py",
     "            elif sha256_file(path) != expected:", "            elif False:",
     [T + "ToolsCheckTest.test_a_changed_file_is_not_ready"]),
    ("the PKLITE extra flag is read from the large flag's bit", "tools/static/dos_identify.py",
     '"extra_compression_flag": bool(major_flags & 0x10)', '"extra_compression_flag": bool(major_flags & 0x20)',
     [T + "DosIdentifyTest.test_each_flag_is_read_from_its_own_bit"]),
    ("an executable without the PKLITE text is called PKLITE", "tools/static/dos_identify.py",
     "    if at == 30:", "    if True:",
     [T + "DosIdentifyTest.test_an_executable_without_the_pklite_text_is_not_called_pklite"]),
    # ---- round 1, R1: dos_identify refuses as every script does
    ("dos_identify reads the original without confining IWA_STATIC", "tools/static/dos_identify.py",
     '    common.static_root(env, originals=("iw-dos",))\n', "",
     [CO + ".test_every_script_refuses_an_unset_static_folder_and_creates_nothing",
      CO + ".test_every_script_refuses_a_static_folder_inside_a_checkout_and_writes_nothing"]),
    ("dos_identify lets the static folder overlap the original's folder", "tools/static/dos_identify.py",
     '    common.static_root(env, originals=("iw-dos",))', "    common.static_root(env)",
     [CO + ".test_every_script_refuses_a_static_folder_that_overlaps_the_original"]),
    ("inventory_derived takes IWA_STATIC without confining it", IV,
     "    root = common.static_root(env)\n",
     '    root = Path(env.get("IWA_STATIC") or "/nonexistent")\n',
     [CO + ".test_every_script_refuses_an_unset_static_folder_and_creates_nothing",
      CO + ".test_every_script_refuses_a_static_folder_inside_a_checkout_and_writes_nothing"]),
    # ---- round 1, R2: every file a run leaves is inventoried, and the checker knows it by its bytes
    ("the inventory lists only the top of a run directory", SC,
     "    for folder, dirs, files in os.walk(base, followlinks=False, onerror=unlistable):",
     "    for folder, dirs, files in [next(os.walk(base))]:",
     [IN + ".test_each_run_records_every_file_of_its_directory",
      IN + ".test_a_tracked_copy_of_a_listing_a_ghidra_database_or_a_dumped_chunk_fails_under_any_name"]),
    # round 2, R1: a folder that cannot be listed stops the inventory
    ("the inventory skips a folder it cannot list", SC,
     "os.walk(base, followlinks=False, onerror=unlistable)", "os.walk(base, followlinks=False)",
     [IN + ".test_a_subtree_that_cannot_be_listed_stops_the_inventory",
      IN + ".test_a_run_directory_that_cannot_be_listed_stops_the_inventory",
      IN + ".test_a_subtree_whose_mode_denies_listing_stops_the_inventory"]),
    ("the inventory does not list a link as a link", SC,
     '            if path.is_symlink():\n                found.append({"path": rel, "link": True})\n                continue\n',
     "",
     [IN + ".test_a_link_in_a_run_directory_is_listed_and_not_followed"]),
    ("ghidra_import does not inventory its run directory", "tools/static/ghidra_import.py",
     '    result["derived_files"] = common.inventory(run_dir)', "    pass",
     [IN + ".test_each_run_records_every_file_of_its_directory",
      IN + ".test_a_tracked_copy_of_a_listing_a_ghidra_database_or_a_dumped_chunk_fails_under_any_name"]),
    ("iwp_extract does not inventory its run directory", "tools/static/iwp_extract.py",
     '    result["derived_files"] = common.inventory(run_dir)', "    pass",
     [IN + ".test_each_run_records_every_file_of_its_directory",
      IN + ".test_a_tracked_copy_of_a_listing_a_ghidra_database_or_a_dumped_chunk_fails_under_any_name"]),
    ("dos_unpack does not inventory its run directory", DU,
     '    result["derived_files"] = common.inventory(run_dir)', "    pass",
     [IN + ".test_each_run_records_every_file_of_its_directory"]),
    ("check_derived_hashes ignores the inventoried derived files", "tools/static/check_derived_hashes.py",
     "            for item in inventoried(doc):", "            for item in ():",
     [IN + ".test_a_tracked_copy_of_a_listing_a_ghidra_database_or_a_dumped_chunk_fails_under_any_name",
      IN + ".test_the_checker_counts_the_inventoried_files"]),
    # ---- round 1, R5: the error-marker count
    ("iwp_markers counts a marker inside a longer word", "tools/static/iwp_markers.py",
     'ERROR_WORD = re.compile(r"\\bERROR\\b")', 'ERROR_WORD = re.compile(r"ERROR")',
     [T + "MarkersTest.test_each_marker_is_counted_as_a_whole_word"]),
    # round 2, R2: each recorded script by its identity and its own hash, not as a set of hashes
    ("iwp_markers finds a recorded script by its hash, not its identity", "tools/static/iwp_markers.py",
     "        ls_path = found.get(key)\n",
     '        ls_path = next((p for p in found.values() if checked_text(p, script["ls_sha256"]) is not None), None)\n',
     [T + "MarkersTest.test_a_changed_member_of_a_duplicate_hash_group_stops_the_count",
      T + "MarkersTest.test_a_missing_member_of_a_duplicate_hash_group_stops_the_count",
      T + "MarkersTest.test_a_script_under_another_identity_does_not_stand_for_a_listed_one"]),
    ("iwp_markers takes any listing with the recorded hash for a script's own", "tools/static/iwp_markers.py",
     "            lasm_text = checked_text(lasm_path, want_lasm) if lasm_path else None\n",
     "            lasm_text = next((t for t in (checked_text(p.with_suffix('.lasm'), want_lasm) "
     "for p in found.values()) if t is not None), None)\n",
     [T + "MarkersTest.test_a_changed_listing_of_a_duplicate_hash_group_stops_the_count",
      T + "MarkersTest.test_a_missing_member_of_a_duplicate_hash_group_stops_the_count"]),
    ("iwp_markers accepts a record that lists one script twice", "tools/static/iwp_markers.py",
     "        if key in listed:\n", "        if False:\n",
     [T + "MarkersTest.test_a_record_listing_one_identity_twice_is_refused"]),
    ("iwp_markers accepts a record whose scripts are short of its script_count", "tools/static/iwp_markers.py",
     '        if counts["ls_files"] != movie.get("script_count"):', "        if False:",
     [T + "MarkersTest.test_a_record_whose_scripts_are_short_of_its_script_count_is_refused"]),
    ("iwp_markers takes IWA_STATIC without confining it", "tools/static/iwp_markers.py",
     "    root = common.static_root(env)\n", '    root = Path(env.get("IWA_STATIC") or "/nonexistent")\n',
     [T + "MarkersTest.test_an_unset_or_in_checkout_static_folder_is_refused"]),
    # ---- the extractor's reading of a projector
    ("a projector without its PJ00 header is accepted", "tools/static/iwp_extract.py",
     '    if data[image_end:image_end + 4] != b"00JP":', "    if False:",
     [T + "ProjectorTest.test_a_file_that_is_not_a_projector_is_refused_with_the_reason"]),
    ("the work copy does not keep the movie header at offset 0", "tools/static/iwp_extract.py",
     "    out[0:0x2C] = data[offset:offset + 0x2C]\n", "",
     [T + "ProjectorTest.test_the_work_copy_keeps_the_movie_at_its_offset_and_its_header_at_zero"]),
    ("an embedded file past the end of the file is accepted", "tools/static/iwp_extract.py",
     "        if offset + size > len(data):", "        if False:",
     [T + "ProjectorTest.test_an_embedded_file_that_runs_past_the_end_is_refused"]),
]


def tests_pass(ids):
    """True when the tests pass. A skipped target test proves nothing either way, so any skip
    stops the script loudly instead of reading as a pass or a kill."""
    done = subprocess.run([sys.executable, "-m", "unittest", "-v"] + ids, cwd=ROOT, capture_output=True, text=True)
    skipped = [line for line in done.stderr.splitlines() if " ... skipped" in line]
    if skipped:
        print("STOPPED: target tests skipped, so no mutant can be shown killed:")
        print("\n".join("  " + line[:300] for line in skipped[:5]))
        print("Run with TMPDIR set to a directory outside every checkout.")
        sys.exit(2)
    return done.returncode == 0


def main():
    ids = sorted({i for *_, group in MUTANTS for i in group})
    if not tests_pass(ids):
        print("the unmutated tests fail; nothing to show")
        return 1
    survived = 0
    for what, rel, old, new, group in MUTANTS:
        path = ROOT / rel
        original = path.read_text()
        if original.count(old) != 1:
            print(f"BAD MUTANT ({original.count(old)} matches): {what}")
            survived += 1
            continue
        try:
            path.write_text(original.replace(old, new))
            killed = not tests_pass(group)
        finally:
            path.write_text(original)
        print(f"{'killed  ' if killed else 'SURVIVED'} {what} ({rel}; {len(group)} test id(s))")
        survived += not killed
    print(f"{len(MUTANTS) - survived} of {len(MUTANTS)} mutants killed")
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
