#!/usr/bin/env python3
"""Identify the packer of the DOS Isle Wars executable from its header, in place (T26, U32).

    IW_DOS_DIR=<the copy> python3 tools/static/dos_identify.py [--record NAME]

It hashes `ISLEWAR.EXE` where it is (it must be the registered file of `iw-dos-3.1-30121376`,
`static_common.original`), reads the MZ header, finds the PKLITE signature and decodes its version
word, and prints numbers: the header fields, the version, the two flags, the copyright text's
position. It writes nothing derived from the file and copies nothing. `--record NAME` writes the
numbers to `experiments/E008-static-triage/measurements/NAME`, as a new file.

The version word is read as the PKLITE format notes describe it (Entropymine, "Notes on PKLITE
format, part 1"): byte 28 is the minor version, the low four bits of byte 29 the major version, and
the high bits of byte 29 flags (0x10 "extra" compression, 0x20 the "large" codebook set). This is a
reading of a published description, not a result of this repository's own runs.
"""
import argparse
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import static_common as common  # noqa: E402

MZ_FIELDS = ("signature", "bytes_in_last_page", "pages", "relocations", "header_paragraphs", "min_extra_paragraphs",
             "max_extra_paragraphs", "initial_ss", "initial_sp", "checksum", "initial_ip", "initial_cs",
             "relocation_table_offset", "overlay_number")


def identify(data):
    """The header facts of a DOS executable that may be PKLITE-packed (a dict of numbers and names)."""
    if len(data) < 0x40 or data[:2] != b"MZ":
        common.die("not a DOS executable (no MZ)")
    fields = dict(zip(MZ_FIELDS, struct.unpack_from("<14H", data, 0)))
    image = (fields["pages"] - 1) * 512 + (fields["bytes_in_last_page"] or 512)
    result = {"mz_header": {k: v for k, v in fields.items() if k != "signature"},
              "image_bytes_by_header": image, "file_bytes": len(data), "bytes_after_image": len(data) - image,
              "header_bytes": fields["header_paragraphs"] * 16}
    text = b"PKLITE Copr."
    at = data.find(text)
    result["pklite_signature_offset"] = at if at >= 0 else None
    if at == 30:
        minor, major_flags = data[28], data[29]
        result["pklite"] = {"minor_version": minor, "major_version": major_flags & 0x0F,
                            "version": f"{major_flags & 0x0F}.{minor}",
                            "extra_compression_flag": bool(major_flags & 0x10),
                            "large_codebook_flag": bool(major_flags & 0x20),
                            "version_word": f"0x{major_flags:02x}{minor:02x}",
                            "copyright_years": data[at + 13:at + 20].decode("ascii", "replace")}
    else:
        result["pklite"] = None
    return result


def main(argv=None, env=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--record")
    args = parser.parse_args(argv)
    original = common.original("iw-dos", env)
    data = original.read()
    result = {"artifact": original.set_id, "original": {"file": original.rel, "sha256": original.sha256,
                                                        "bytes": original.size}}
    result.update(identify(data))
    if args.record:
        name = args.record if args.record.endswith(".json") else args.record + ".json"
        print(f"record: {common.write_record(name, result)}")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
