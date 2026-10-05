#!/usr/bin/env python3
"""Extract the Director movie from the Isle Wars Pro projector and decompile its Lingo (T26, U32).

    IWA_STATIC=<folder outside every checkout> IWP_DIR=<the install> python3 tools/static/iwp_extract.py
        [--run ID] [--projectorrays PATH] [--probe NAME]... [--record NAME]

What it does, in order (every step refuses first, `static_common.py`):
1. `IWA_STATIC` is confined (set, absolute, outside every checkout, not overlapping IWP_DIR).
2. `Islepro.exe` in IWP_DIR is hashed in place and must be the registered file of `iwp-2.0-996e86c5`.
3. The projector is read from those bytes: the end of the PE image, the `PJ00` header that follows
   it, the Director container (`APPL`) it points at, and the container's chunk map. Every `File`
   chunk of the map is listed by offset, length, kind and sha256; each embedded Director movie
   (an `XFIR` file, a little-endian RIFX) is carved into `<run>/`.
4. ProjectorRays reads a movie by the offsets inside it, and in a projector those offsets are the
   offsets in the executable. The work copy `movie-NN.abs.dxr` therefore keeps the movie at its
   original offset: the first 44 bytes at 0, and the movie again at its offset, zeros between.
   ProjectorRays then decompiles that copy with `--dump-scripts`.
5. The output is counted: chunks by kind, scripts by kind, handlers, and a sha256 for each script
   file. `--probe NAME` names a file whose handlers are searched for: the handlers that mention it
   are listed with whether they read or write a file.

Everything derived from the original (the carved movie, the work copy, the decompiled scripts, the
tool's logs) stays in `<IWA_STATIC>/iwp-extract-<run>/`. `--record NAME` writes the counts, hashes,
names and addresses, with the sha256 and size of every file of the run directory (`derived_files`), to `experiments/E008-static-triage/measurements/NAME`, as a new file, and never
a line of the scripts.
"""
import argparse
import json
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import static_common as common  # noqa: E402

SCRIPT_NAME = re.compile(r"^(MovieScript|CastScript|BehaviorScript|ParentScript) (\d+)(?: - (.*))?\.(ls|lasm)$")
HANDLER = re.compile(r"^on (\S+)", re.MULTILINE)
CHUNK_LINE = re.compile(r"^Found RIFX resource index (\d+): '(.{4})', (\d+) bytes @ pos 0x([0-9a-f]+)", re.MULTILINE)
VERSION_LINE = re.compile(r"Decompiled (Macromedia Director [0-9.]+) movie")
READ_CALLS = re.compile(r"\b(readFile|readLine|readChar|readWord|readToken)\b", re.IGNORECASE)
WRITE_CALLS = re.compile(r"\b(writeString|writeChar|writeLine|createFile)\b", re.IGNORECASE)


def parse_projector(data):
    """The layout of a Director projector for Windows, from its bytes: a dict, or SystemExit saying
    which expectation failed. Offsets are file offsets."""
    if data[:2] != b"MZ":
        common.die("the file is not a DOS/Windows executable (no MZ)")
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe:pe + 4] != b"PE\0\0":
        common.die("the file is not a PE executable")
    sections = struct.unpack_from("<H", data, pe + 6)[0]
    optional = struct.unpack_from("<H", data, pe + 20)[0]
    table = pe + 24 + optional
    image_end = 0
    for index in range(sections):
        raw_size, raw_ptr = struct.unpack_from("<II", data, table + 40 * index + 16)
        image_end = max(image_end, raw_ptr + raw_size)
    if data[image_end:image_end + 4] != b"00JP":
        common.die("no projector header (PJ00) at the end of the PE image")
    appl = struct.unpack_from("<I", data, image_end + 4)[0]
    if data[appl:appl + 4] != b"XFIR" or data[appl + 8:appl + 12] != b"LPPA":
        common.die("the projector header does not point at a Director container (APPL)")
    if data[appl + 12:appl + 16] != b"pami":
        common.die("the container has no initial map")
    mmap_offset = struct.unpack_from("<I", data, appl + 12 + 8 + 4)[0]
    imap_version = struct.unpack_from("<I", data, appl + 12 + 8 + 8)[0]
    if data[mmap_offset:mmap_offset + 4] != b"pamm":
        common.die("the container's initial map does not point at a memory map")
    header_length, entry_length, _max, used = struct.unpack_from("<HHII", data, mmap_offset + 8)[0:4]
    if entry_length != 20:
        common.die(f"unexpected memory map entry length {entry_length}")
    files = []
    chunk_kinds = {}
    for index in range(used):
        at = mmap_offset + 8 + header_length + index * entry_length
        tag = data[at:at + 4][::-1].decode("latin-1")
        length, offset = struct.unpack_from("<II", data, at + 4)
        chunk_kinds[tag] = chunk_kinds.get(tag, 0) + 1
        if tag != "File":
            continue
        head = data[offset:offset + 4]
        if head == b"XFIR":
            size = struct.unpack_from("<I", data, offset + 4)[0] + 8
            kind, codec = "director-movie", data[offset + 8:offset + 12][::-1].decode("latin-1")
        elif head[:2] == b"MZ":
            size, kind, codec = length, "pe-or-dos-executable", None
        else:
            size, kind, codec = length, "other", None
        if offset + size > len(data):
            common.die(f"embedded file {len(files)} runs past the end of the file")
        files.append({"index": len(files), "offset": offset, "chunk_length": length, "length": size,
                      "kind": kind, "codec": codec, "sha256": common.sha256_bytes(data[offset:offset + size])})
    return {"image_end": image_end, "projector_signature": "PJ00", "container_offset": appl,
            "container_imap_version_field": imap_version, "container_chunks": used,
            "container_chunk_kinds": dict(sorted(chunk_kinds.items())), "files": files}


def work_copy(data, offset, size):
    """The movie at its original offset, with its first 44 bytes (header and initial map) at 0."""
    out = bytearray(offset + size)
    out[0:0x2C] = data[offset:offset + 0x2C]
    out[offset:offset + size] = data[offset:offset + size]
    return bytes(out)


def inspect_output(out_dir, probes):
    """Counts, hashes and names from a ProjectorRays output folder (no script text)."""
    scripts, handlers_total = [], 0
    probe_hits = {name: [] for name in probes}
    for path in sorted(Path(out_dir).rglob("*")):
        match = SCRIPT_NAME.match(path.name) if path.is_file() else None
        if not match or match.group(4) != "ls":
            continue
        kind, number, name = match.group(1), int(match.group(2)), match.group(3) or ""
        text = path.read_text(encoding="utf-8", errors="replace")
        starts = [m for m in HANDLER.finditer(text)]
        handlers = []
        for position, found in enumerate(starts):
            end = starts[position + 1].start() if position + 1 < len(starts) else len(text)
            body = text[found.start():end]
            handlers.append(found.group(1))
            for probe in probes:
                if probe.lower() in body.lower():
                    probe_hits[probe].append({"script_kind": kind, "script_number": number, "script_name": name,
                                              "handler": found.group(1), "reads": bool(READ_CALLS.search(body)),
                                              "writes": bool(WRITE_CALLS.search(body))})
        lasm = path.with_suffix(".lasm")
        handlers_total += len(handlers)
        scripts.append({"kind": kind, "number": number, "name": name, "handlers": handlers,
                        "lines": text.count("\n"), "ls_sha256": common.sha256_path(path)[0],
                        "lasm_sha256": common.sha256_path(lasm)[0] if lasm.is_file() else None})
    by_kind = {}
    for script in scripts:
        by_kind[script["kind"]] = by_kind.get(script["kind"], 0) + 1
    return {"scripts": scripts, "script_count": len(scripts), "scripts_by_kind": dict(sorted(by_kind.items())),
            "handler_count": handlers_total, "probes": probe_hits}


MEMBER_TYPES = {0: "null", 1: "bitmap", 2: "film loop", 3: "text", 4: "palette", 5: "picture", 6: "sound",
                7: "button", 8: "shape", 9: "movie", 10: "digital video", 11: "script", 12: "rich text"}


def inspect_json(json_dir):
    """Cast member types and the script context from a `--dump-json` folder (counts only)."""
    types, context = {}, None
    for path in sorted(Path(json_dir).rglob("*.json")):
        if path.name.startswith("CASt-"):
            kind = json.loads(path.read_text(encoding="utf-8"))["type"]
            label = MEMBER_TYPES.get(kind, f"type {kind} (not named by the tool)")
            types[label] = types.get(label, 0) + 1
        elif path.name.startswith("Lctx-"):
            doc = json.loads(path.read_text(encoding="utf-8"))
            context = {"entries": doc["entryCount"], "valid": doc["validCount"]}
    return {"cast_member_count": sum(types.values()), "cast_member_types": dict(sorted(types.items())),
            "script_context": context}


def parse_log(text):
    kinds = {}
    for _, tag, _, _ in CHUNK_LINE.findall(text):
        kinds[tag] = kinds.get(tag, 0) + 1
    version = VERSION_LINE.search(text)
    return {"chunks_by_kind": dict(sorted(kinds.items())), "chunk_count": sum(kinds.values()),
            "reported": version.group(1) if version else None}


def tool_identity(binary):
    sha, size = common.sha256_path(binary)
    return {"name": "projectorrays", "path": common.anonymise(binary), "sha256": sha, "bytes": size}


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--run", help="run id (default: the UTC time)")
    parser.add_argument("--projectorrays", help="the ProjectorRays binary (default: $IWA_PROJECTORRAYS or "
                        "$HOME/tools/projectorrays-0.2.0/bin/projectorrays)")
    parser.add_argument("--probe", action="append", default=[], help="a file name whose handlers are listed")
    parser.add_argument("--record", help="write the measurement under experiments/E008-static-triage/measurements/")
    return parser


def main(argv=None, env=None):
    args = build_parser().parse_args(argv)
    root = common.static_root(env, originals=("iwp",))      # refuses first: nothing is read or made before
    original = common.original("iwp", env)
    data = original.read()
    layout = parse_projector(data)
    movies = [f for f in layout["files"] if f["kind"] == "director-movie"]
    if not movies:
        common.die("no Director movie in the projector")
    binary = Path(args.projectorrays) if args.projectorrays else common.tool_home(
        "IWA_PROJECTORRAYS", ["projectorrays-0.2.0", "bin", "projectorrays"])
    if not binary.is_file():
        common.die("ProjectorRays is not installed (setup/static/README.md): a missing tool is a step "
                   "to finish, never a reason to fall back to runs (U32)")
    run_dir = common.new_run_dir(root, "iwp-extract", args.run)
    result = {"artifact": original.set_id, "original": {"file": original.rel, "sha256": original.sha256,
                                                        "bytes": original.size},
              "layout": {k: v for k, v in layout.items() if k != "files"}, "embedded_files": layout["files"],
              "tool": tool_identity(binary), "movies": []}
    for number, movie in enumerate(movies, start=1):
        exact = data[movie["offset"]:movie["offset"] + movie["length"]]
        stem = f"movie-{number:02d}"
        common.write_new(run_dir, f"{stem}.dxr", exact)
        abs_copy = work_copy(data, movie["offset"], movie["length"])
        common.write_new(run_dir, f"{stem}.abs.dxr", abs_copy)
        out_dir = run_dir / f"{stem}-out"
        common.safeio.make_directory(run_dir, out_dir.name)
        code, seconds = common.run([binary, "decompile", run_dir / f"{stem}.abs.dxr", "-o", out_dir,
                                    "--dump-scripts", "-v"], run_dir, run_dir, f"{stem}-projectorrays")
        log = (run_dir / f"{stem}-projectorrays.out").read_text(errors="replace") + \
              (run_dir / f"{stem}-projectorrays.err").read_text(errors="replace")
        entry = {"movie": number, "offset": movie["offset"], "length": movie["length"], "codec": movie["codec"],
                 "carved_sha256": common.sha256_bytes(exact), "work_copy_sha256": common.sha256_bytes(abs_copy),
                 "work_copy_bytes": len(abs_copy), "projectorrays_exit": code, "seconds": seconds}
        entry.update(parse_log(log))
        if code == 0:
            entry.update(inspect_output(out_dir, args.probe))
            json_dir = run_dir / f"{stem}-json"
            common.safeio.make_directory(run_dir, json_dir.name)
            json_code, _ = common.run([binary, "decompile", run_dir / f"{stem}.abs.dxr", "-o", json_dir,
                                       "--dump-json"], run_dir, run_dir, f"{stem}-projectorrays-json")
            entry["projectorrays_json_exit"] = json_code
            if json_code == 0:
                entry.update(inspect_json(json_dir))
                if entry["script_context"]:
                    entry["scripts_without_a_cast_member"] = entry["script_context"]["valid"] - entry["script_count"]
            dirs = sorted(out_dir.glob("*.dir"))
            entry["rebuilt_movie"] = [{"bytes": common.sha256_path(d)[1], "sha256": common.sha256_path(d)[0]}
                                      for d in dirs]
        result["movies"].append(entry)
    original.recheck()
    result["original_unchanged_after_run"] = True
    result["derived_files"] = common.inventory(run_dir)       # every carved, decompiled and dumped file
    if args.record:
        name = args.record if args.record.endswith(".json") else args.record + ".json"
        print(f"record: {common.write_record(name, result)}")
    print(json.dumps({"run_directory": run_dir.name, "movies": [
        {k: m.get(k) for k in ("movie", "codec", "reported", "projectorrays_exit", "script_count",
                               "handler_count", "chunk_count")} for m in result["movies"]]}, indent=2))
    return 0 if all(m["projectorrays_exit"] == 0 for m in result["movies"]) else 1


if __name__ == "__main__":
    sys.exit(main())
