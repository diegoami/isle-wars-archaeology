#!/usr/bin/env python3
"""Unpack a DOS Isle Wars executable with Deark, into the static folder only (T26, U32).

    IWA_STATIC=<folder outside every checkout> IW_DOS_DIR=<the copy> python3 tools/static/dos_unpack.py
        [--original iw-dos | iw-dos-ov6] [--deark PATH] [--run ID] [--record NAME]

`ISLEWAR.EXE` (and `ISLEWAR.OV6`, the second executable of the set) is packed twice: PKLITE outside
(`dos_identify.py` reads its header) and, inside it, Microsoft LINK's EXEPACK (found on the first
unpack: the PKLITE layer returns an image whose entry point is EXEPACK's decoder, with no DOS
relocation of its own). So the unpack is two Deark runs, each with its module named:

1. `deark -m pklite` on the original, read in place after its sha256 matched the registered one
   (`static_common.original`), and hashed again afterwards;
2. `deark -m exepack` on the first stage's output.

Each stage writes one new file into the new directory `<IWA_STATIC>/deark-<run>/`, and its messages
into two log files beside it. The script then checks that the last image is a plausible DOS
executable (`mz_facts`: a valid MZ header, the relocation table inside the header, every relocation
and the entry point inside the load module, no PKLITE text and no EXEPACK decoder left). It prints,
and `--record NAME` writes to `experiments/E008-static-triage/measurements/NAME` as a new file, only
numbers: each file's sha256 and size, the header fields, the counts, Deark's version and sha256.
Nothing derived from the original is printed or written anywhere else.
"""
import argparse
import json
import os
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import static_common as common  # noqa: E402

MZ_FIELDS = ("signature", "bytes_in_last_page", "pages", "relocations", "header_paragraphs", "min_extra_paragraphs",
             "max_extra_paragraphs", "initial_ss", "initial_sp", "checksum", "initial_ip", "initial_cs",
             "relocation_table_offset", "overlay_number")
EXEPACK_TEXT = b"Packed file is corrupt"
PKLITE_TEXT = b"PKLITE Copr."
# (stage name, Deark module): the order the layers come off
STAGES = (("stage1-pklite", "pklite"), ("stage2-exepack", "exepack"))


def mz_facts(data):
    """Numbers about a DOS executable, and whether it is a plausible unpacked image (`plausible`, with
    the reasons it is not in `problems`). It reads the header and the relocation table, and the words
    the relocations point at (to count the segments they name); it returns no byte of code."""
    if len(data) < 0x1C or data[:2] != b"MZ":
        return {"plausible": False, "problems": ["no MZ header"]}
    fields = dict(zip(MZ_FIELDS, struct.unpack_from("<14H", data, 0)))
    problems = []
    image = (fields["pages"] - 1) * 512 + (fields["bytes_in_last_page"] or 512)
    header = fields["header_paragraphs"] * 16
    module = image - header
    table_end = fields["relocation_table_offset"] + 4 * fields["relocations"]
    if image > len(data):
        problems.append("the header says the image is longer than the file")
    if header < 0x1C or header > image:
        problems.append("the header size is outside the image")
    if fields["relocations"] and table_end > header:
        problems.append("the relocation table runs past the header")
    outside, segments = 0, set()
    if table_end <= len(data):
        for i in range(fields["relocations"]):
            off, seg = struct.unpack_from("<HH", data, fields["relocation_table_offset"] + 4 * i)
            at = seg * 16 + off
            if at + 2 > module:
                outside += 1
            else:
                segments.add(struct.unpack_from("<H", data, header + at)[0])
    if outside:
        problems.append(f"{outside} relocations point outside the load module")
    entry = fields["initial_cs"] * 16 + fields["initial_ip"]
    if entry >= module:
        problems.append("the entry point is outside the load module")
    if data.find(PKLITE_TEXT) == 30:
        problems.append("the PKLITE text is still at offset 30 (still packed)")
    if EXEPACK_TEXT in data:
        problems.append("EXEPACK's decoder text is still in the image (still packed)")
    return {"mz_header": {k: v for k, v in fields.items() if k != "signature"},
            "file_bytes": len(data), "image_bytes_by_header": image, "header_bytes": header,
            "load_module_bytes": module, "entry_point": f"{fields['initial_cs']:04x}:{fields['initial_ip']:04x}",
            "entry_offset_in_module": entry, "relocations_outside_module": outside,
            "segments_named_by_relocations": len(segments),
            "pklite_text_at_30": data.find(PKLITE_TEXT) == 30, "exepack_decoder_text": EXEPACK_TEXT in data,
            "plausible": not problems, "problems": problems}


def deark_identity(deark):
    """Deark's version line and its binary's sha256 (the tools manifest records the expected one)."""
    sha, size = common.sha256_path(deark)
    return {"path": common.anonymise(deark), "sha256": sha, "bytes": size}


def stage(deark, module, source, run_dir, name, env):
    """Run one Deark module on `source`; the one file it wrote into the run directory (its Path)."""
    before = set(os.listdir(run_dir))
    command = [deark, "-m", module, "-d", "-od", run_dir, "-o", name, source]
    code, seconds = common.run(command, run_dir, run_dir, f"deark-{name}", env=env, timeout=600)
    made = sorted(set(os.listdir(run_dir)) - before - {f"deark-{name}.out", f"deark-{name}.err"})
    if code != 0:
        common.die(f"Deark's {module} stage exited {code}; its messages are in the run directory")
    if len(made) != 1:
        common.die(f"Deark's {module} stage wrote {len(made)} files, not one; nothing is recorded")
    return run_dir / made[0], code, seconds


def main(argv=None, env=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--original", default="iw-dos", choices=("iw-dos", "iw-dos-ov6"))
    parser.add_argument("--deark", help="the Deark binary (default: $IWA_DEARK, else the tools folder's build)")
    parser.add_argument("--run")
    parser.add_argument("--record")
    args = parser.parse_args(argv)
    root = common.static_root(env, originals=(args.original,))
    original = common.original(args.original, env)
    deark = Path(args.deark) if args.deark else common.tool_home("IWA_DEARK", ["src", "deark-1.7.3", "deark"])
    if not deark.is_file() or not os.access(deark, os.X_OK):
        common.die("Deark is not installed (docs/environment.md, \"Static analysis tools\"): a missing tool is a "
                   "step to finish, never a reason to fall back to runs (U32)")
    run_dir = common.new_run_dir(root, "deark", args.run)
    child_env = dict(os.environ if env is None else env)
    result = {"artifact": original.set_id,
              "original": {"file": original.rel, "sha256": original.sha256, "bytes": original.size},
              "tool": dict(deark_identity(deark), name="deark"), "stages": []}
    source = original.path
    try:
        for name, module in STAGES:
            out, code, seconds = stage(deark, module, source, run_dir, name, child_env)
            sha, size = common.sha256_path(out)
            result["stages"].append({"stage": name, "deark_module": module, "exit": code, "seconds": seconds,
                                     "output": {"name": out.name, "sha256": sha, "bytes": size}})
            source = out
    finally:
        original.recheck()
    with common.safeio.open_source(source) as fh:
        final = fh.read()
    result["unpacked"] = dict(mz_facts(final), name=source.name, sha256=common.sha256_bytes(final),
                              run_directory=run_dir.name)
    if args.record:
        name = args.record if args.record.endswith(".json") else args.record + ".json"
        print(f"record: {common.write_record(name, result)}")
    print(json.dumps({"run_directory": run_dir.name,
                      "stages": [(s["stage"], s["output"]["sha256"], s["output"]["bytes"]) for s in result["stages"]],
                      "plausible": result["unpacked"]["plausible"], "problems": result["unpacked"]["problems"],
                      "relocations": result["unpacked"].get("mz_header", {}).get("relocations")}, indent=2))
    return 0 if result["unpacked"]["plausible"] else 1


if __name__ == "__main__":
    sys.exit(main())
