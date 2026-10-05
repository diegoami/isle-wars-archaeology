#!/usr/bin/env python3
"""Read an unpacked DOS executable for two things, in the static folder (T26, U32):

    IWA_STATIC=<folder outside every checkout> python3 tools/static/dos_probe.py
        --file <name in the static folder> --sha256 <hex> [--needle TEXT]... [--record NAME]

1. **Which compiler or runtime made it.** It looks for a fixed list of marker texts (`MARKERS`: the
   run-time error texts of a few DOS compilers' libraries, chosen here) and reports, for each, whether
   it occurs and where. The list and the reading of it are ours; the image's own text is not kept.
2. **Where a file name is used.** For each needle (a file name such as `ISLEWAR.SAV`) it finds the
   text and reads the four bytes before it as a string descriptor: a 16-bit length, then the 16-bit
   offset of the text in the data segment. This is how the image lays out its string constants, as
   read from it (`descriptor_layout_holds` says whether the length word equals the text's length,
   and the record gives the data segment's base each needle implies: the reading holds only when
   all agree). It then lists the places in the load module that load the descriptor's offset into
   AX and push it (`B8 lo hi 50`, how the image passes a string to a library routine), as Ghidra
   addresses of the load segment 1000 (`1000:9b89`). Those are the call sites `ghidra_import.py
   --range` disassembles, into the static folder, for a person to read.

It reads only a file of the static folder that has the given sha256 (`static_common.derived`); it
writes nothing there and copies nothing. `--record NAME` writes the numbers to
`experiments/E008-static-triage/measurements/NAME` as a new file: offsets, addresses, counts, and
which of our markers occur. No byte of code and no text of the image beyond the needles is recorded.
"""
import argparse
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import static_common as common  # noqa: E402

# Marker texts, by the toolchain whose run-time library prints them. A marker shows that the library
# is linked in; several from one family and none from the others is the identification.
MARKERS = {
    "microsoft-basic": ["RESUME without error", "Out of DATA", "FIELD overflow", "Bad record number",
                        "Advanced feature unavailable", "String space corrupt", "Error in EXE file",
                        "Error during run-time initialization"],
    "microsoft-c-library": ["run-time error R60", "- stack overflow", "- illegal far pointer use"],
    "borland-turbo-pascal": ["Runtime error ", "Portions Copyright (c) 1983", "Turbo Pascal"],
    "borland-c": ["Borland C++", "Turbo C", "Abnormal program termination"],
    "other-basic": ["PowerBASIC", "Turbo Basic", "QBX", "Visual Basic"],
}
LOAD_SEGMENT = 0x1000      # where Ghidra's old-style DOS loader puts the load module


def module_of(data):
    """(header bytes, load module) of an MZ image."""
    if len(data) < 0x1C or data[:2] != b"MZ":
        common.die("not a DOS executable (no MZ)")
    last, pages, _, header_paragraphs = struct.unpack_from("<4H", data, 2)
    image = (pages - 1) * 512 + (last or 512)
    header = header_paragraphs * 16
    return header, data[header:image]


def markers(data):
    """{family: {marker: offset or None}}: where each marker text first occurs in the file."""
    found = {}
    for family, texts in MARKERS.items():
        found[family] = {text: (data.find(text.encode("ascii")) if text.encode("ascii") in data else None)
                         for text in texts}
    return found


def ghidra_address(offset):
    """A load-module offset as Ghidra writes it, when it lies in the first 64 KiB of the load segment."""
    return f"{LOAD_SEGMENT:04x}:{offset:04x}" if offset < 0x10000 else f"linear 0x{offset:x}"


def references(module, value):
    """Load-module offsets of `mov ax, value` followed by `push ax`."""
    pattern = b"\xb8" + struct.pack("<H", value) + b"\x50"
    found, at = [], module.find(pattern)
    while at >= 0:
        found.append(at)
        at = module.find(pattern, at + 1)
    return found


def needle(module, text):
    """Every occurrence of `text` in the load module, read as a string constant with its descriptor."""
    raw = text.encode("ascii")
    hits, at = [], module.find(raw)
    while at >= 0:
        item = {"module_offset": at}
        if at >= 4:
            length, offset = struct.unpack_from("<HH", module, at - 4)
            item["descriptor_layout_holds"] = length == len(raw)
            if item["descriptor_layout_holds"]:
                descriptor = offset - 4
                item.update({"text_offset_in_data_segment": f"0x{offset:04x}",
                             "descriptor_offset_in_data_segment": f"0x{descriptor:04x}",
                             "data_segment_base": f"0x{at - offset:x}",
                             "pushed_at": [ghidra_address(r) for r in references(module, descriptor)]})
        hits.append(item)
        at = module.find(raw, at + 1)
    return {"text": text, "hits": hits}


def main(argv=None, env=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--file", required=True, help="a file inside the static folder (a relative name)")
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--needle", action="append", default=[])
    parser.add_argument("--record")
    args = parser.parse_args(argv)
    root = common.static_root(env)
    path, size = common.derived(root, args.file, args.sha256)
    with common.safeio.open_source(path) as fh:
        data = fh.read()
    if common.sha256_bytes(data) != args.sha256:
        common.die(f"{args.file} changed after it was checked; nothing was read from it")
    header, module = module_of(data)
    found = markers(data)
    needles = [needle(module, text) for text in args.needle]
    bases = sorted({h["data_segment_base"] for n in needles for h in n["hits"] if h.get("descriptor_layout_holds")})
    result = {"input": {"derived_file_sha256": args.sha256, "bytes": size}, "header_bytes": header,
              "load_module_bytes": len(module),
              "markers": found,
              "marker_counts": {family: sum(v is not None for v in texts.values()) for family, texts in found.items()},
              "needles": needles, "data_segment_bases": bases}
    if args.record:
        name = args.record if args.record.endswith(".json") else args.record + ".json"
        print(f"record: {common.write_record(name, result)}")
    print(json.dumps({"marker_counts": result["marker_counts"], "data_segment_bases": bases,
                      "pushed_at": {n["text"]: [a for h in n["hits"] for a in h.get("pushed_at", [])] for n in needles}},
                     indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
