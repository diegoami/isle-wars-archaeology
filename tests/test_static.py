"""Tests of the static-analysis tools (T26), on synthetic originals: no original, no real tool.

Every test builds its own folders in a temporary directory outside every checkout: a throwaway
checkout whose `artifacts/known.json` registers a synthetic set (the registered hash the tools
compare an original with), a synthetic original, and a fake tool (a small script that stands in for
ProjectorRays or Ghidra's `analyzeHeadless` and writes a canned output). `static_common.ORIGINALS`
and `KNOWN_ROOT` are pointed at them. Nothing here reads an original game file.

The three refusals of T26 Done-when 3, each with the tests that fail when it is removed
(tests/mutants_static.py removes each and shows the tests failing), for every script that reads an
original or writes derived output (`iwp_extract`, `ghidra_import`):
- the output is never written inside a git checkout: CheckoutRefusalTest;
- the script refuses to run when `IWA_STATIC` is unset or inside a checkout: CheckoutRefusalTest;
- the script refuses to read an original that does not match its registered sha256:
  OriginalRefusalTest.

Also: the projector reader and the output counters (ProjectorTest, ExtractRunTest), the Ghidra
report (GhidraRunTest), the record writer (RecordTest), and the check that no tracked file is an
output derived from an original (DerivedHashesTest).

They need a temporary directory outside every checkout. Inside one, every test of a World skips
with SKIP_REASON, and the module warns on stderr when it is imported: a run that skipped them has
not verified the refusals, whatever its OK says.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "static"))
sys.path.insert(0, str(ROOT / "setup" / "iwp"))
sys.path.insert(0, str(ROOT / "setup" / "static"))

import locations  # noqa: E402
import safeio  # noqa: E402
import validate_records  # noqa: E402
import static_common  # noqa: E402
import iwp_extract  # noqa: E402
import ghidra_import  # noqa: E402
import check_derived_hashes  # noqa: E402
import check_tools  # noqa: E402
import dos_identify  # noqa: E402
import dos_unpack  # noqa: E402
import dos_probe  # noqa: E402
import inventory_derived  # noqa: E402
import iwp_markers  # noqa: E402


def sha(data):
    return hashlib.sha256(data).hexdigest()


# ---- a synthetic Director projector -------------------------------------------------------------

def tag(name):
    """A chunk tag as the little-endian files write it (reversed)."""
    return name.encode("ascii")[::-1]


def make_movie(size_after_header=0x60):
    """A synthetic MV93 movie: `XFIR`, its length, `MV93`, an initial map, then padding."""
    body = bytearray(size_after_header)
    body[0:4] = tag("MV93")
    return b"XFIR" + struct.pack("<I", len(body)) + bytes(body)


def make_projector(movie=None, extra_files=(b"MZ\x90\x00 a library", b"plain data"), pj="00JP"):
    """A projector for Windows: a tiny PE image, `PJ00`, a container with a chunk map, the embedded files."""
    movie = make_movie() if movie is None else movie
    out = bytearray(0x400)
    out[0:2] = b"MZ"
    struct.pack_into("<I", out, 0x3C, 0x80)
    out[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<H", out, 0x80 + 6, 1)             # one section
    struct.pack_into("<H", out, 0x80 + 20, 0)            # no optional header
    struct.pack_into("<II", out, 0x80 + 24 + 16, 0x200, 0x200)   # raw size, raw pointer: the image ends at 0x400
    appl = 0x400 + 8
    out += pj.encode("ascii") + struct.pack("<I", appl)
    files = list(extra_files) + [movie]
    entries = 3 + len(files)
    imap_at = appl + 12
    mmap_at = imap_at + 32
    mmap_len = 0x18 + 20 * entries
    files_at = mmap_at + 8 + mmap_len + 16
    placed, cursor = [], files_at
    for data in files:
        placed.append((cursor, data))
        cursor += len(data)

    def entry(name, length, offset):
        return tag(name) + struct.pack("<IIHHi", length, offset, 1, 0, -1)

    container = b"XFIR" + struct.pack("<I", 0) + tag("APPL")
    container += tag("imap") + struct.pack("<I", 0x18) + struct.pack("<III", 1, mmap_at, 1406) + b"\0" * 12
    container += tag("mmap") + struct.pack("<I", mmap_len) + struct.pack("<HHIIiii", 0x18, 20, entries, entries, -1, -1, -1)
    container += entry("RIFX", 0, appl) + entry("imap", 32, imap_at) + entry("mmap", 8 + mmap_len, mmap_at)
    for offset, data in placed:
        container += entry("File", len(data), offset)
    container += b"\0" * 16
    assert appl + len(container) == files_at, (appl + len(container), files_at)
    out += container
    for _, data in placed:
        out += data
    return bytes(out), placed


FAKE_PROJECTORRAYS = '''#!{python}
"""A stand-in for ProjectorRays: writes a canned output tree for a synthetic movie."""
import json, pathlib, sys
args = sys.argv[1:]
src, out = args[1], pathlib.Path(args[args.index("-o") + 1])
assert args[0] == "decompile"
if "--dump-scripts" in args:
    d = out / "movie" / "casts" / "Internal"
    d.mkdir(parents=True)
    (out / "movie.dir").write_bytes(b"rebuilt")
    (d / "MovieScript 7 - Saver.ls").write_text("on SaveThing\\n  openFile(f, \\"Thing.dat\\")\\n  writeString(f, x)\\nend\\n\\non Other\\nend\\n")
    (d / "MovieScript 7 - Saver.lasm").write_text("asm\\n")
    (d / "BehaviorScript 9.ls").write_text("on mouseDown\\nend\\n")
    (d / "BehaviorScript 9.lasm").write_text("asm\\n")
    (d / "CastScript 3 - Btn.ls").write_text("on mouseUp\\n  put readFile(f)\\n  openFile(g, \\"Thing.dat\\")\\nend\\n")
    print("Decompiled Macromedia Director 7.0 movie " + src)
    for i, t in enumerate(["CASt", "CASt", "Lscr", "Lscr", "Lscr", "BITD"], start=1):
        print("Found RIFX resource index %d: '%s', 20 bytes @ pos 0x%08x (%d)" % (i, t, 100 * i, 100 * i))
if "--dump-json" in args:
    d = out / "movie" / "chunks"
    d.mkdir(parents=True)
    (out / "movie.dir").write_bytes(b"rebuilt")
    for i, t in enumerate([1, 1, 11, 3, 99]):
        (d / ("CASt-%d.json" % i)).write_text(json.dumps({{"type": t}}))
    (d / "Lctx-9.json").write_text(json.dumps({{"entryCount": 5, "validCount": 4}}))
'''

FAKE_ANALYZE = '''#!/bin/sh
# A stand-in for Ghidra's analyzeHeadless: writes the report the post-script would write, a project
# database file, and a listing for each range.
report=""
ranges=""
project="$1"
case "$1" in */.*) echo "Path element starting with '.' is not permitted" >&2; exit 1;; esac
while [ $# -gt 0 ]; do
  if [ "$1" = "-postScript" ]; then report="$3"; fi
  case "$1" in range=*) ranges="$ranges ${1#range=}";; esac
  shift
done
mkdir -p "$project/t26.rep/idata/00"
printf 'a synthetic ghidra database' > "$project/t26.rep/idata/00/~00000000.db"
for r in $ranges; do
  printf 'a synthetic listing of %s\n' "$r" > "$(dirname "$report")/listing-$(echo "${r%%-*}" | tr : -).txt"
done
cat > "$report" <<EOF
language=x86:LE:16:Real Mode
compiler_spec=default
format=Old-style DOS Executable (MZ)
functions=42
instructions=900
memory_blocks=2
block CODE_0 1000:0000 4096
block DATA 2000:0000 512
needle FILE.SAV hits=1
  at 2000:0123 offset=0x123
    reference from 1000:0456 in FUN_1000_0400 at 1000:0400
    immediate in 1000:0460 in FUN_1000_0400 at 1000:0400
range 1000:0400 1000:0460 instructions=30 far_calls=4
EOF
echo "analysis done"
'''


FAKE_DEARK = '''#!{python}
"""A stand-in for Deark: one module per call, writes the canned image of that stage into -od."""
import pathlib, sys
args = sys.argv[1:]
module, od, base, source = args[args.index("-m") + 1], args[args.index("-od") + 1], args[args.index("-o") + 1], args[-1]
here = pathlib.Path(__file__).resolve().parent
data = pathlib.Path(source).read_bytes()
assert data[:2] == b"MZ", source
canned = {{"pklite": "stage1.bin", "exepack": "final.bin"}}[module]
pathlib.Path(od, base + ".000.exe").write_bytes((here / canned).read_bytes())
if module == "pklite":
    print("DEBUG: reported PKLITE version: 1.15/l/e")
    print("DEBUG:  extra cmpr: 1")
    print("DEBUG:  large cmpr: 1")
    print("DEBUG:  decompressed 10 bytes to 20")
else:
    print("DEBUG: variant: common290 (LINK 5.60/etc.)")
    print("DEBUG:  reloc count: 1")
print("Warning: (Standard warning about executable decompression)", file=sys.stderr)
'''


def make_mz(module, relocations=(), cs=0, ip=0):
    """A DOS executable around a load module: a header, its relocation table, the module."""
    paragraphs = max(2, (0x1C + 4 * len(relocations) + 15) // 16)
    header = bytearray(paragraphs * 16)
    total = len(header) + len(module)
    struct.pack_into("<14H", header, 0, 0x5A4D, total % 512, (total + 511) // 512, len(relocations), paragraphs,
                     0x10, 0xFFFF, 0, 0x100, 0, ip, cs, 0x1C, 0)
    for i, (offset, segment) in enumerate(relocations):
        struct.pack_into("<HH", header, 0x1C + 4 * i, offset, segment)
    return bytes(header) + module


def probe_module(text=b"FILE.SAV"):
    """A load module laid out as the unpacked ISLEWAR.EXE is read to be: code that loads a string
    descriptor's offset into AX and pushes it (at 0x10 and 0x40), and a data segment at 0x100 whose
    string constant is its descriptor (length, offset of the text) followed by the text (offset 0x20)."""
    module = bytearray(0x200)
    module[0x10:0x14] = b"\xb8" + struct.pack("<H", 0x1C) + b"\x50"
    module[0x40:0x44] = b"\xb8" + struct.pack("<H", 0x1C) + b"\x50"
    module[0x11C:0x120] = struct.pack("<HH", len(text), 0x20)
    module[0x120:0x120 + len(text)] = text
    module[0x180:0x194] = b"RESUME without error"
    return bytes(module)


FINAL_IMAGE = make_mz(probe_module(), relocations=[(0x0002, 0)], cs=0, ip=0x10)
STAGE1_IMAGE = make_mz(b"\x90" * 0x40 + b"Packed file is corrupt" + b"\0" * 0x20, cs=0, ip=0x10)


SKIP_REASON = ("SAFETY TEST NOT RUN: the temporary directory is inside a checkout (TMPDIR="
               f"{os.environ.get('TMPDIR', '')!r}), and the code under test refuses every location inside one; "
               "set TMPDIR to a directory outside every checkout, or this run verifies nothing")
if locations.checkout_of(Path(os.path.realpath(tempfile.gettempdir()))) is not None:
    sys.stderr.write(f"\nWARNING: tests/test_static.py: {SKIP_REASON}\n")

PROJECTOR, PLACED = make_projector()
DOS_BYTES = b"MZ synthetic packed executable" + bytes(48)        # 64 bytes or more: dos_identify reads a header


def registered(manifest, label):
    body = dict(manifest, acquired={"how": "generated", "when": "2026-10-05"})
    body["id"] = f"{label}-{validate_records.canonical_set_hash(body)[:8]}"
    return body


def manifest_for(title, files, label):
    return registered({"schema": "artifact-set/1", "title": title, "version": "1",
                       "files": [{"path": p, "bytes": len(d), "sha256": sha(d)} for p, d in sorted(files.items())],
                       "runtime_writes": []}, label)


MANIFEST_IWP = manifest_for("synthetic pro", {"Islepro.exe": PROJECTOR}, "iwp-synthetic")
MANIFEST_DOS = manifest_for("synthetic dos", {"ISLEWAR.EXE": DOS_BYTES}, "iw-dos-synthetic")


class World(unittest.TestCase):
    """A throwaway known.json checkout, an install of each synthetic original, a static folder."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(os.path.realpath(self._tmp.name))
        if locations.checkout_of(self.tmp) is not None:
            self.skipTest(SKIP_REASON)
        self.known = self.tmp / "known"
        (self.known / "artifacts").mkdir(parents=True)
        (self.known / "artifacts" / "known.json").write_text(
            json.dumps({"sets": [{"manifest": MANIFEST_IWP}, {"manifest": MANIFEST_DOS}]}))
        subprocess.run(["git", "init", "-q", str(self.known)], check=True)
        patch = mock.patch.object(static_common, "KNOWN_ROOT", self.known)
        patch.start()
        self.addCleanup(patch.stop)
        patch = mock.patch.dict(static_common.ORIGINALS, {
            "iwp": (MANIFEST_IWP["id"], "IWP_DIR", "Islepro.exe"),
            "iw-dos": (MANIFEST_DOS["id"], "IW_DOS_DIR", "ISLEWAR.EXE")})
        patch.start()
        self.addCleanup(patch.stop)
        self.iwp = self.tmp / "iwp"
        self.dos = self.tmp / "dos"
        for directory, name, data in ((self.iwp, "Islepro.exe", PROJECTOR), (self.dos, "ISLEWAR.EXE", DOS_BYTES)):
            directory.mkdir()
            (directory / name).write_bytes(data)
        self.static = self.tmp / "static"
        self.static.mkdir()
        self.env = {"IWA_STATIC": str(self.static), "IWP_DIR": str(self.iwp), "IW_DOS_DIR": str(self.dos),
                    "PATH": os.environ["PATH"]}
        self.tools = self.tmp / "tools"
        self.tools.mkdir()
        self.fake_projectorrays = self.tools / "projectorrays"
        self.fake_projectorrays.write_text(FAKE_PROJECTORRAYS.format(python=sys.executable))
        self.fake_projectorrays.chmod(0o755)
        self.ghidra = self.tools / "ghidra"
        (self.ghidra / "support").mkdir(parents=True)
        (self.ghidra / "Ghidra").mkdir()
        (self.ghidra / "support" / "analyzeHeadless").write_text(FAKE_ANALYZE)
        (self.ghidra / "support" / "analyzeHeadless").chmod(0o755)
        (self.ghidra / "Ghidra" / "application.properties").write_text(
            "application.version=12.1.4\napplication.revision.ghidra=abc\napplication.build.date.short=20260921\n")
        self.java = self.tools / "jdk"
        (self.java / "bin").mkdir(parents=True)
        (self.java / "lib").mkdir()
        (self.java / "bin" / "java").write_text("#!/bin/sh\n")
        (self.java / "release").write_text('JAVA_RUNTIME_VERSION="21.0.12.1+1-LTS"\nIMPLEMENTOR_VERSION="Temurin-21.0.12.1+1"\n')
        (self.java / "lib" / "modules").write_bytes(b"modules")
        self.fake_deark = self.tools / "deark"
        self.fake_deark.write_text(FAKE_DEARK.format(python=sys.executable))
        self.fake_deark.chmod(0o755)
        (self.tools / "stage1.bin").write_bytes(STAGE1_IMAGE)
        (self.tools / "final.bin").write_bytes(FINAL_IMAGE)
        patch = mock.patch.dict(os.environ, {"IWA_GHIDRA": str(self.ghidra), "IWA_JAVA_HOME": str(self.java),
                                             "IWA_DEARK": str(self.fake_deark)})
        patch.start()
        self.addCleanup(patch.stop)

    def static_entries(self):
        return sorted(p.name for p in self.static.iterdir())

    def call(self, module, argv, env=None):
        """(exit, text): the module's main with the world's environment, its printed text."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = module.main(argv, env=self.env if env is None else env)
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue() + err.getvalue()

    def extract(self, *extra, env=None):
        return self.call(iwp_extract, ["--projectorrays", str(self.fake_projectorrays), "--run", "t1", *extra], env)

    def ghidra_run(self, *extra, env=None):
        return self.call(ghidra_import, ["--original", "iw-dos", "--run", "t1", *extra], env)

    def unpack(self, *extra, env=None):
        return self.call(dos_unpack, ["--run", "t1", *extra], env)

    def inventory(self, *extra, env=None):
        with mock.patch.object(static_common, "ROOT", self.known):     # its records go to the test's checkout
            return self.call(inventory_derived, ["--all", "--prefix", "test-inv", *extra], env)


# the scripts that read an original or the static folder, and how each is called
SCRIPTS = {
    "iwp_extract": lambda world, env: world.extract(env=env),
    "ghidra_import": lambda world, env: world.ghidra_run(env=env),
    "dos_unpack": lambda world, env: world.unpack(env=env),
    "dos_identify": lambda world, env: world.call(dos_identify, [], env),           # writes nothing derived
    "inventory_derived": lambda world, env: world.inventory(env=env),              # reads no original
}
# the original each script reads (inventory_derived reads none, so it has no original to overlap)
READS = {"iwp_extract": "iwp", "ghidra_import": "dos", "dos_unpack": "dos", "dos_identify": "dos"}


class CheckoutRefusalTest(World):
    """T26 Done-when 3, first two bullets: never write inside a checkout; refuse an unset or in-checkout IWA_STATIC."""

    def test_the_good_layout_runs_every_script(self):
        for name, call in SCRIPTS.items():
            with self.subTest(script=name):
                code, text = call(self, None)
                self.assertEqual(code, 0, text)

    def test_every_script_refuses_an_unset_static_folder_and_creates_nothing(self):
        for name, call in SCRIPTS.items():
            with self.subTest(script=name):
                for env in (dict(self.env, IWA_STATIC=""), {k: v for k, v in self.env.items() if k != "IWA_STATIC"}):
                    code, text = call(self, env)
                    self.assertIn("IWA_STATIC is not set", str(code))
                self.assertEqual(self.static_entries(), [])

    def test_every_script_refuses_a_relative_static_folder(self):
        for name, call in SCRIPTS.items():
            with self.subTest(script=name):
                code, _ = call(self, dict(self.env, IWA_STATIC="relative/static"))
                self.assertIn("absolute", str(code))

    def test_every_script_refuses_a_static_folder_inside_a_checkout_and_writes_nothing(self):
        checkout = self.tmp / "checkout"
        (checkout / ".git").mkdir(parents=True)
        inside = checkout / "static"
        inside.mkdir()
        for name, call in SCRIPTS.items():
            with self.subTest(script=name):
                code, _ = call(self, dict(self.env, IWA_STATIC=str(inside)))
                self.assertIn("inside a checkout", str(code))
                self.assertEqual(list(inside.iterdir()), [])

    def test_every_script_refuses_a_static_folder_that_is_a_link_into_a_checkout(self):
        checkout = self.tmp / "checkout"
        (checkout / ".git").mkdir(parents=True)
        (checkout / "static").mkdir()
        link = self.tmp / "link"
        link.symlink_to(checkout / "static")
        for name, call in SCRIPTS.items():
            with self.subTest(script=name):
                code, _ = call(self, dict(self.env, IWA_STATIC=str(link)))
                self.assertIn("inside a checkout", str(code))
                self.assertEqual(list((checkout / "static").iterdir()), [])

    def test_every_script_refuses_a_static_folder_that_contains_this_repository(self):
        for name, call in SCRIPTS.items():
            with self.subTest(script=name):
                code, _ = call(self, dict(self.env, IWA_STATIC=str(ROOT.parent)))
                self.assertNotEqual(code, 0)
                self.assertTrue(isinstance(code, str) and "IWA_STATIC" in code, code)

    def test_every_script_refuses_a_static_folder_that_overlaps_the_original(self):
        for name, key in READS.items():
            with self.subTest(script=name):
                original = getattr(self, key)
                call = SCRIPTS[name]
                code, _ = call(self, dict(self.env, IWA_STATIC=str(original)))
                self.assertIn("overlaps", str(code))

    def test_a_run_never_reuses_a_directory(self):
        self.assertEqual(self.extract()[0], 0)
        code, text = self.extract()
        self.assertIn("a run never reuses a directory", str(code))
        self.assertEqual(self.ghidra_run()[0], 0)
        code, text = self.ghidra_run()
        self.assertIn("a run never reuses a directory", str(code))
        self.assertEqual(self.unpack()[0], 0)
        code, text = self.unpack()
        self.assertIn("a run never reuses a directory", str(code))

    def test_a_dot_folder_in_the_static_path_is_handled_for_ghidra(self):
        dotted = self.tmp / ".hidden" / "static"
        dotted.mkdir(parents=True)
        code, text = self.ghidra_run(env=dict(self.env, IWA_STATIC=str(dotted)))
        self.assertEqual(code, 0, text)
        self.assertTrue((dotted / "ghidra-t1" / "report.txt").is_file())


class OriginalRefusalTest(World):
    """T26 Done-when 3, third bullet: an original that does not match its registered sha256 is not read."""

    def corrupt(self, directory, name, data):
        (directory / name).write_bytes(data)

    def test_a_changed_original_is_refused_by_every_script_and_nothing_is_made(self):
        for script, directory, name in (("iwp_extract", self.iwp, "Islepro.exe"), ("ghidra_import", self.dos, "ISLEWAR.EXE"),
                                        ("dos_unpack", self.dos, "ISLEWAR.EXE"), ("dos_identify", self.dos, "ISLEWAR.EXE")):
            with self.subTest(script=script):
                good = (directory / name).read_bytes()
                self.corrupt(directory, name, good[:-1] + bytes([good[-1] ^ 1]))
                code, _ = SCRIPTS[script](self, None)
                self.assertIn("is not the registered file", str(code))
                self.assertEqual(self.static_entries(), [])
                self.corrupt(directory, name, good)

    def test_a_truncated_original_is_refused(self):
        self.corrupt(self.iwp, "Islepro.exe", PROJECTOR[:-10])
        code, _ = self.extract()
        self.assertIn("is not the registered file", str(code))

    def test_a_missing_original_is_refused(self):
        (self.iwp / "Islepro.exe").unlink()
        code, _ = self.extract()
        self.assertIn("cannot be read", str(code))
        self.assertEqual(self.static_entries(), [])

    def test_an_original_that_is_a_link_is_not_read_through(self):
        elsewhere = self.tmp / "elsewhere.exe"
        elsewhere.write_bytes(PROJECTOR)
        (self.iwp / "Islepro.exe").unlink()
        (self.iwp / "Islepro.exe").symlink_to(elsewhere)
        code, _ = self.extract()
        self.assertIn("is a link", str(code))

    def test_an_unset_or_relative_original_folder_is_refused(self):
        code, _ = self.extract(env={k: v for k, v in self.env.items() if k != "IWP_DIR"})
        self.assertIn("IWP_DIR is not set", str(code))
        code, _ = self.extract(env=dict(self.env, IWP_DIR="relative"))
        self.assertIn("absolute", str(code))

    def test_a_set_the_manifest_does_not_know_is_refused(self):
        with mock.patch.dict(static_common.ORIGINALS, {"iwp": ("iwp-nothing-00000000", "IWP_DIR", "Islepro.exe")}):
            code, _ = self.extract()
        self.assertIn("no known.json entry", str(code))

    def test_the_bytes_a_script_uses_are_the_registered_ones_even_if_the_file_changes_after_the_check(self):
        original = static_common.original("iwp", self.env)
        (self.iwp / "Islepro.exe").write_bytes(PROJECTOR[:-1] + b"X")
        with self.assertRaises(SystemExit) as caught:
            original.read()
        self.assertIn("changed after it was checked", str(caught.exception))
        with self.assertRaises(SystemExit):
            original.recheck()

    def test_a_ghidra_file_input_must_match_the_given_sha256(self):
        self.assertEqual(self.ghidra_run()[0], 0)
        unpacked = self.static / "unpacked.exe"
        unpacked.write_bytes(b"MZ unpacked")
        argv = ["--file", "unpacked.exe", "--run", "t2"]
        code, text = self.call(ghidra_import, argv + ["--sha256", sha(b"MZ unpacked")])
        self.assertEqual(code, 0, text)
        code, _ = self.call(ghidra_import, argv[:-1] + ["t3", "--sha256", sha(b"something else")])
        self.assertIn("is not the file with the given sha256", str(code))
        code, _ = self.call(ghidra_import, ["--file", "unpacked.exe", "--run", "t4"])
        self.assertIn("--sha256", str(code))
        code, _ = self.call(ghidra_import, ["--file", "../elsewhere", "--sha256", "0" * 64, "--run", "t5"])
        self.assertIn("relative and without ..", str(code))


class ProjectorTest(unittest.TestCase):
    def test_the_layout_of_a_projector_is_read(self):
        layout = iwp_extract.parse_projector(PROJECTOR)
        self.assertEqual(layout["image_end"], 0x400)
        self.assertEqual(layout["projector_signature"], "PJ00")
        self.assertEqual(layout["container_imap_version_field"], 1406)
        self.assertEqual(layout["container_chunks"], 3 + 3)
        kinds = [f["kind"] for f in layout["files"]]
        self.assertEqual(kinds, ["pe-or-dos-executable", "other", "director-movie"])
        movie = layout["files"][-1]
        self.assertEqual((movie["codec"], movie["length"]), ("MV93", len(make_movie())))
        self.assertEqual(movie["sha256"], sha(make_movie()))
        self.assertEqual(movie["offset"], PLACED[-1][0])

    def test_a_file_that_is_not_a_projector_is_refused_with_the_reason(self):
        for data, why in ((b"not an exe", "MZ"), (b"MZ" + b"\0" * 0x3E + struct.pack("<I", 0x80) + b"\0" * 0x80, "PE"),
                          (PROJECTOR[:0x400] + b"XXXX" + PROJECTOR[0x404:], "PJ00")):
            with self.subTest(why=why):
                with self.assertRaises(SystemExit) as caught:
                    iwp_extract.parse_projector(data)
                self.assertIn(why, str(caught.exception))

    def test_an_embedded_file_that_runs_past_the_end_is_refused(self):
        with self.assertRaises(SystemExit) as caught:
            iwp_extract.parse_projector(PROJECTOR[:-5])
        self.assertIn("runs past the end", str(caught.exception))

    def test_the_work_copy_keeps_the_movie_at_its_offset_and_its_header_at_zero(self):
        offset, movie = PLACED[-1]
        copy = iwp_extract.work_copy(PROJECTOR, offset, len(movie))
        self.assertEqual(copy[offset:], movie)
        self.assertEqual(copy[:0x2C], movie[:0x2C])
        self.assertEqual(len(copy), offset + len(movie))
        self.assertEqual(copy[0x2C:offset], b"\0" * (offset - 0x2C))


class ExtractRunTest(World):
    def run_it(self, *extra):
        code, text = self.extract("--probe", "Thing.dat", "--record", "test-iwp.json", *extra)
        return code, text

    def test_a_run_carves_decompiles_counts_and_records_without_a_line_of_code(self):
        with mock.patch.object(static_common, "ROOT", self.known):
            code, text = self.run_it()
        self.assertEqual(code, 0, text)
        run = self.static / "iwp-extract-t1"
        offset, movie = PLACED[-1]
        self.assertEqual((run / "movie-01.dxr").read_bytes(), movie)
        self.assertEqual((run / "movie-01.abs.dxr").read_bytes()[offset:], movie)
        record = json.loads((self.known / static_common.MEASUREMENTS / "test-iwp.json").read_text())
        movie_record = record["movies"][0]
        self.assertEqual(record["original"]["sha256"], sha(PROJECTOR))
        self.assertEqual(movie_record["carved_sha256"], sha(movie))
        self.assertEqual((movie_record["script_count"], movie_record["handler_count"]), (3, 4))
        self.assertEqual(movie_record["scripts_by_kind"], {"BehaviorScript": 1, "CastScript": 1, "MovieScript": 1})
        self.assertEqual(movie_record["chunks_by_kind"], {"BITD": 1, "CASt": 2, "Lscr": 3})
        self.assertEqual(movie_record["reported"], "Macromedia Director 7.0")
        self.assertEqual(movie_record["cast_member_types"], {"bitmap": 2, "script": 1, "text": 1,
                                                             "type 99 (not named by the tool)": 1})
        self.assertEqual(movie_record["scripts_without_a_cast_member"], 1)       # 4 valid, 3 written
        hits = movie_record["probes"]["Thing.dat"]
        self.assertEqual([(h["handler"], h["reads"], h["writes"]) for h in hits],
                         [("mouseUp", True, False), ("SaveThing", False, True)])
        text = json.dumps(record)
        for code_fragment in ("openFile(", "writeString(", "readFile(", "end\\n"):
            self.assertNotIn(code_fragment, text, "a record carries names and counts, never a line of code")
        self.assertEqual(static_common.leaks(text), [])

    def test_a_missing_tool_is_a_stop_not_a_fallback(self):
        code, _ = self.call(iwp_extract, ["--projectorrays", str(self.tools / "missing"), "--run", "t1"])
        self.assertIn("not installed", str(code))
        self.assertIn("never a reason to fall back to runs", str(code))
        self.assertEqual(self.static_entries(), [])

    def test_a_failing_tool_makes_the_run_fail_and_still_records(self):
        self.fake_projectorrays.write_text("#!/bin/sh\nexit 3\n")
        code, text = self.extract()
        self.assertEqual(code, 1, text)

    def test_a_projector_without_a_movie_is_refused(self):
        data, _ = make_projector(movie=b"XXXX" + b"\0" * 0x70)
        (self.iwp / "Islepro.exe").write_bytes(data)
        with mock.patch.dict(static_common.ORIGINALS, {"iwp": (
                manifest_for("x", {"Islepro.exe": data}, "iwp-other")["id"], "IWP_DIR", "Islepro.exe")}):
            (self.known / "artifacts" / "known.json").write_text(json.dumps(
                {"sets": [{"manifest": manifest_for("x", {"Islepro.exe": data}, "iwp-other")}]}))
            code, _ = self.extract()
        self.assertIn("no Director movie", str(code))


class GhidraRunTest(World):
    def test_the_report_is_parsed_into_counts_addresses_and_names(self):
        with mock.patch.object(static_common, "ROOT", self.known):
            code, text = self.ghidra_run("--needle", "FILE.SAV", "--record", "test-ghidra.json")
        self.assertEqual(code, 0, text)
        record = json.loads((self.known / static_common.MEASUREMENTS / "test-ghidra.json").read_text())
        report = record["report"]
        self.assertEqual((report["functions"], report["instructions"]), (42, 900))
        self.assertEqual(report["language"], "x86:LE:16:Real Mode")
        self.assertEqual(report["needles"][0]["occurrences"][0]["at"], "2000:0123")
        self.assertEqual(len(report["needles"][0]["occurrences"][0]["references"]), 2)
        self.assertEqual(record["tools"]["ghidra"]["version"], "12.1.4")
        self.assertEqual(record["tools"]["java"]["version"], "21.0.12.1+1-LTS")
        self.assertEqual(record["input"]["sha256"], sha(DOS_BYTES))
        self.assertEqual(static_common.leaks(json.dumps(record)), [])

    def test_a_missing_ghidra_is_a_stop_not_a_fallback(self):
        (self.ghidra / "support" / "analyzeHeadless").unlink()
        code, _ = self.ghidra_run()
        self.assertIn("never a reason to fall back to runs", str(code))
        self.assertEqual(self.static_entries(), [])

    def test_the_language_is_16_bit_real_mode_and_the_project_is_in_the_static_folder(self):
        args = self.tmp / "args.txt"
        (self.ghidra / "support" / "analyzeHeadless").write_text(
            '#!/bin/sh\necho "$@" > ' + str(args) + '\n' + FAKE_ANALYZE.split("\n", 1)[1])
        self.assertEqual(self.ghidra_run()[0], 0)
        text = args.read_text()
        self.assertIn("-processor x86:LE:16:Real Mode", text)
        self.assertIn(str(self.static / "ghidra-t1" / "project"), text)


class RecordTest(World):
    def test_a_record_with_a_machine_path_is_refused_and_nothing_is_written(self):
        for value in ("/home/someone/x", "C:\\Games\\x", "/mnt/c/x", "~/.local/share/x", "Program Files (x86)/x"):
            with self.subTest(value=value):
                with self.assertRaises(SystemExit) as caught:
                    static_common.write_record("bad.json", {"where": value}, root=self.known)
                self.assertIn("machine path", str(caught.exception))
        self.assertFalse((self.known / static_common.MEASUREMENTS).exists())

    def test_a_record_is_never_overwritten(self):
        static_common.write_record("one.json", {"n": 1}, root=self.known)
        with self.assertRaises(SystemExit) as caught:
            static_common.write_record("one.json", {"n": 2}, root=self.known)
        self.assertIn("never overwritten", str(caught.exception))
        self.assertEqual(json.loads((self.known / static_common.MEASUREMENTS / "one.json").read_text()), {"n": 1})

    def test_a_record_name_cannot_climb_out_of_the_measurements_folder(self):
        for name in ("../x.json", "/abs.json", "a/b.json"):
            with self.subTest(name=name):
                with self.assertRaises(SystemExit):
                    static_common.write_record(name, {"n": 1}, root=self.known)

    def test_anonymise_replaces_the_home_folder(self):
        home = str(Path.home())
        self.assertEqual(static_common.anonymise(home + "/tools/x"), "$HOME/tools/x")
        self.assertEqual(static_common.anonymise("/opt/x"), "/opt/x")


class DerivedHashesTest(World):
    """T26 Done-when 4: no tracked file is an output the measurements list by hash."""

    def repo(self, name="repo"):
        root = self.tmp / name
        (root / static_common.MEASUREMENTS).mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        return root

    def track(self, root, *names):
        subprocess.run(["git", "add", "-f", *names], cwd=root, check=True)

    def test_a_clean_checkout_passes_and_says_what_it_checked(self):
        root = self.repo()
        (root / "a.txt").write_text("harmless")
        (root / static_common.MEASUREMENTS / "m.json").write_text(json.dumps({"sha256": sha(b"the unpacked bytes")}))
        self.track(root, "a.txt", str(static_common.MEASUREMENTS / "m.json"))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_derived_hashes.main(["--root", str(root)])
        self.assertEqual(code, 0)
        self.assertIn("checked 2 tracked files against 1 hashes", out.getvalue())

    def test_a_tracked_file_with_a_listed_hash_fails(self):
        root = self.repo()
        (root / "sneaky.txt").write_bytes(b"the unpacked bytes")
        (root / static_common.MEASUREMENTS / "m.json").write_text(json.dumps({"sha256": sha(b"the unpacked bytes")}))
        self.track(root, "sneaky.txt", str(static_common.MEASUREMENTS / "m.json"))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_derived_hashes.main(["--root", str(root)])
        self.assertEqual(code, 1)
        self.assertIn("sneaky.txt", out.getvalue())

    def test_a_tracked_file_named_like_a_derived_output_fails_whatever_its_bytes(self):
        for name in ("movie-01.dxr", "x.lasm", "Script 1 - a.ls", "proj.gpr", "movie-01-out"):
            with self.subTest(name=name):
                root = self.repo("repo-" + hashlib.sha1(name.encode()).hexdigest()[:8])
                (root / name).write_text("anything")
                self.track(root, name)
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(check_derived_hashes.main(["--root", str(root)]), 1)

    def test_a_directory_that_is_not_a_checkout_is_a_usage_error(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check_derived_hashes.main(["--root", str(self.tmp)]), 2)

    def test_this_checkout_passes(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check_derived_hashes.main(["--root", str(ROOT)]), 0)


def pklite_header(minor=15, major_flags=0x31, years=b"1990-92"):
    """A synthetic packed DOS executable: an MZ header and the PKLITE version word and copyright."""
    header = struct.pack("<14H", 0x5A4D, 124, 164, 1, 6, 4364, 0xFFFF, 5224, 512, 0, 256, 0xFFF0, 82, 0)
    header += bytes([minor, major_flags]) + b"PKLITE Copr. " + years + b" PKWARE Inc."
    return header.ljust(164 * 512 - 388, b"\0")


class DosIdentifyTest(World):
    def test_the_header_and_the_pklite_version_word_are_read(self):
        result = dos_identify.identify(pklite_header())
        self.assertEqual(result["pklite"], {"minor_version": 15, "major_version": 1, "version": "1.15",
                                            "extra_compression_flag": True, "large_codebook_flag": True,
                                            "version_word": "0x310f", "copyright_years": "1990-92"})
        self.assertEqual(result["pklite_signature_offset"], 30)
        self.assertEqual(result["mz_header"]["pages"], 164)
        self.assertEqual(result["mz_header"]["initial_cs"], 0xFFF0)

    def test_each_flag_is_read_from_its_own_bit(self):
        for word, extra, large, version in ((0x01, False, False, "1.15"), (0x11, True, False, "1.15"),
                                            (0x21, False, True, "1.15"), (0x02, False, False, "2.15")):
            with self.subTest(word=word):
                pk = dos_identify.identify(pklite_header(major_flags=word))["pklite"]
                self.assertEqual((pk["extra_compression_flag"], pk["large_codebook_flag"], pk["version"]),
                                 (extra, large, version))

    def test_an_executable_without_the_pklite_text_is_not_called_pklite(self):
        data = bytearray(pklite_header())
        data[30:42] = b"SOMETHING ELS"[:12]
        self.assertIsNone(dos_identify.identify(bytes(data))["pklite"])
        with self.assertRaises(SystemExit):
            dos_identify.identify(b"not an exe" * 10)

    def test_the_registered_original_is_required_and_a_record_is_written(self):
        data = pklite_header()
        manifest = manifest_for("dos", {"ISLEWAR.EXE": data}, "iw-dos-id")
        (self.known / "artifacts" / "known.json").write_text(json.dumps({"sets": [{"manifest": manifest}]}))
        (self.dos / "ISLEWAR.EXE").write_bytes(data)
        with mock.patch.dict(static_common.ORIGINALS, {"iw-dos": (manifest["id"], "IW_DOS_DIR", "ISLEWAR.EXE")}), \
                mock.patch.object(static_common, "ROOT", self.known):
            code, text = self.call(dos_identify, ["--record", "test-identify.json"])
            self.assertEqual(code, 0, text)
            record = json.loads((self.known / static_common.MEASUREMENTS / "test-identify.json").read_text())
            self.assertEqual(record["original"]["sha256"], sha(data))
            (self.dos / "ISLEWAR.EXE").write_bytes(data[:-1] + b"X")
            code, _ = self.call(dos_identify, [])
            self.assertIn("is not the registered file", str(code))


class ToolsCheckTest(World):
    """setup/static/check_tools.py: an install is compared with the recorded hashes."""

    def manifest(self):
        folder = self.tmp / "toolsroot" / "thing-1"
        folder.mkdir(parents=True)
        (folder / "a.bin").write_bytes(b"aaa")
        return {"tools": [{"name": "thing", "version": "1", "dir": "thing-1", "files": {"a.bin": sha(b"aaa")}}]}

    def run_check(self, manifest, *extra):
        path = self.tmp / "tools.json"
        path.write_text(json.dumps(manifest))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_tools.main(["--root", str(self.tmp / "toolsroot"), "--manifest", str(path), *extra])
        return code, out.getvalue()

    def test_a_matching_tool_is_ready(self):
        code, text = self.run_check(self.manifest())
        self.assertEqual(code, 0)
        self.assertIn("thing 1: 1 files match", text)
        self.assertTrue(text.endswith("ready\n"))

    def test_a_changed_file_is_not_ready(self):
        manifest = self.manifest()
        (self.tmp / "toolsroot" / "thing-1" / "a.bin").write_bytes(b"changed")
        code, text = self.run_check(manifest)
        self.assertEqual(code, 1)
        self.assertIn("another sha256", text)

    def test_a_missing_file_a_missing_folder_and_an_unknown_name_are_not_ready(self):
        manifest = self.manifest()
        (self.tmp / "toolsroot" / "thing-1" / "a.bin").unlink()
        self.assertIn("a.bin is missing", self.run_check(manifest)[1])
        (self.tmp / "toolsroot" / "thing-1").rmdir()
        code, text = self.run_check(manifest)
        self.assertEqual(code, 1)
        self.assertIn("folder thing-1 is missing", text)
        code, text = self.run_check(manifest, "--only", "nothing")
        self.assertEqual(code, 1)
        self.assertIn("not in tools.json", text)

    def test_the_recorded_manifest_is_well_formed_and_names_no_machine_path(self):
        text = (ROOT / "setup" / "static" / "tools.json").read_text()
        self.assertEqual(static_common.leaks(text), [])
        manifest = json.loads(text)
        for tool in manifest["tools"]:
            self.assertTrue(tool["files"], tool["name"])
            for value in tool["files"].values():
                self.assertRegex(value, r"^[0-9a-f]{64}$")


class DosUnpackTest(World):
    """dos_unpack: two Deark stages into the static folder, and the check that the result is a plain image."""

    def test_two_stages_write_into_the_static_folder_and_a_record_holds_numbers_only(self):
        with mock.patch.object(static_common, "ROOT", self.known):
            code, text = self.unpack("--record", "test-unpack.json")
        self.assertEqual(code, 0, text)
        run = self.static / "deark-t1"
        self.assertEqual(sorted(p.name for p in run.iterdir() if p.suffix == ".exe"),
                         ["stage1-pklite.000.exe", "stage2-exepack.000.exe"])
        record = json.loads((self.known / static_common.MEASUREMENTS / "test-unpack.json").read_text())
        self.assertEqual([s["output"]["sha256"] for s in record["stages"]], [sha(STAGE1_IMAGE), sha(FINAL_IMAGE)])
        self.assertEqual(record["unpacked"]["sha256"], sha(FINAL_IMAGE))
        self.assertTrue(record["unpacked"]["plausible"])
        self.assertEqual(record["stages"][0]["deark_says"]["pklite_version"], "1.15/l/e")
        self.assertEqual(record["stages"][1]["deark_says"]["exepack_variant"], "common290 (LINK 5.60/etc.)")
        self.assertEqual(record["original"]["sha256"], sha(DOS_BYTES))
        self.assertEqual(static_common.leaks(json.dumps(record)), [])
        self.assertNotIn(b"RESUME", json.dumps(record).encode())
        self.assertEqual(sorted(p.name for p in self.dos.iterdir()), ["ISLEWAR.EXE"])

    def test_a_missing_deark_is_a_stop_not_a_fallback(self):
        code, _ = self.unpack("--deark", str(self.tools / "nothing"))
        self.assertIn("never a reason to fall back to runs", str(code))
        self.assertEqual(self.static_entries(), [])

    def test_a_stage_that_fails_or_writes_more_than_one_file_stops_the_run(self):
        self.fake_deark.write_text("#!/bin/sh\nexit 3\n")
        code, _ = self.unpack()
        self.assertIn("exited 3", str(code))
        self.fake_deark.write_text(FAKE_DEARK.format(python=sys.executable)
                                   + "pathlib.Path(od, 'second.bin').write_bytes(b'x')\n")
        code, _ = self.unpack("--run", "t2")
        self.assertIn("wrote 2 files, not one", str(code))

    def test_an_original_that_changes_while_deark_reads_it_is_caught(self):
        self.fake_deark.write_text(FAKE_DEARK.format(python=sys.executable)
                                   + "if module == 'pklite':\n    open(source, 'ab').write(b'!')\n")
        code, _ = self.unpack()
        self.assertIn("is not the registered file after the tool ran", str(code))

    def test_an_image_still_packed_is_not_plausible(self):
        (self.tools / "final.bin").write_bytes(STAGE1_IMAGE)
        code, text = self.unpack()
        self.assertEqual(code, 1, text)
        self.assertIn("EXEPACK", text)

    def test_the_plausibility_checks_each_fail_on_their_own_defect(self):
        self.assertTrue(dos_unpack.mz_facts(FINAL_IMAGE)["plausible"])
        cases = {
            "outside the load module": make_mz(probe_module(), relocations=[(0x1000, 0)], ip=0x10),
            "entry point": make_mz(probe_module(), cs=0x40, ip=0x10),
            "PKLITE": make_mz(b"\0" * 4 + b"PKLITE Copr." + b"\0" * 0x100)[:30] + b"PKLITE Copr." + b"\0" * 0x100,
            "EXEPACK": STAGE1_IMAGE,
            "longer than the file": FINAL_IMAGE[:-10],
            "no MZ": b"ZM" + FINAL_IMAGE[2:],
        }
        for needle, data in cases.items():
            with self.subTest(defect=needle):
                facts = dos_unpack.mz_facts(data)
                self.assertFalse(facts["plausible"])
                self.assertTrue(any(needle in p for p in facts["problems"]), facts["problems"])


class DosProbeTest(World):
    """dos_probe: reads only a static-folder file with the given sha256; finds descriptors and their pushes."""

    def setUp(self):
        super().setUp()
        (self.static / "img").mkdir()
        (self.static / "img" / "final.exe").write_bytes(FINAL_IMAGE)

    def probe(self, *extra, env=None, digest=None):
        return self.call(dos_probe, ["--file", "img/final.exe", "--sha256", digest or sha(FINAL_IMAGE),
                                     "--needle", "FILE.SAV", *extra], env)

    def test_the_descriptor_and_the_places_that_push_it_are_found(self):
        with mock.patch.object(static_common, "ROOT", self.known):
            code, text = self.probe("--record", "test-probe.json")
        self.assertEqual(code, 0, text)
        record = json.loads((self.known / static_common.MEASUREMENTS / "test-probe.json").read_text())
        hit = record["needles"][0]["hits"][0]
        self.assertTrue(hit["descriptor_layout_holds"])
        self.assertEqual(hit["descriptor_offset_in_data_segment"], "0x001c")
        self.assertEqual(hit["data_segment_base"], "0x100")
        self.assertEqual(hit["pushed_at"], ["1000:0010", "1000:0040"])
        self.assertEqual(record["marker_counts"]["microsoft-basic"], 1)
        self.assertEqual(record["marker_counts"]["borland-turbo-pascal"], 0)
        self.assertEqual(static_common.leaks(json.dumps(record)), [])

    def test_a_text_without_a_descriptor_before_it_is_not_read_as_one(self):
        module = bytearray(probe_module())
        module[0x11C:0x11E] = b"\x07\x00"
        hit = dos_probe.needle(bytes(module), "FILE.SAV")["hits"][0]
        self.assertFalse(hit["descriptor_layout_holds"])
        self.assertNotIn("pushed_at", hit)

    def test_a_file_with_another_sha256_or_outside_the_static_folder_is_refused(self):
        code, _ = self.probe(digest=sha(b"other"))
        self.assertIn("is not the file with the given sha256", str(code))
        code, _ = self.call(dos_probe, ["--file", "../dos/ISLEWAR.EXE", "--sha256", sha(DOS_BYTES)])
        self.assertIn("relative and without ..", str(code))

    def test_the_bytes_read_are_the_ones_whose_hash_was_checked(self):
        (self.static / "img" / "other.exe").write_bytes(FINAL_IMAGE + b"!")
        with mock.patch.object(static_common, "derived",
                               return_value=(self.static / "img" / "other.exe", len(FINAL_IMAGE) + 1)):
            code, _ = self.probe()
        self.assertIn("changed after it was checked", str(code))

    def test_an_unset_or_in_checkout_static_folder_is_refused(self):
        code, _ = self.probe(env={k: v for k, v in self.env.items() if k != "IWA_STATIC"})
        self.assertIn("IWA_STATIC is not set", str(code))
        checkout = self.tmp / "checkout"
        (checkout / ".git").mkdir(parents=True)
        (checkout / "static" / "img").mkdir(parents=True)
        (checkout / "static" / "img" / "final.exe").write_bytes(FINAL_IMAGE)
        code, _ = self.probe(env=dict(self.env, IWA_STATIC=str(checkout / "static")))
        self.assertIn("inside a checkout", str(code))


class GhidraRangeTest(World):
    def test_a_range_is_passed_to_the_post_script_and_its_counts_are_recorded(self):
        args = self.tmp / "args.txt"
        (self.ghidra / "support" / "analyzeHeadless").write_text(
            '#!/bin/sh\necho "$@" > ' + str(args) + '\n' + FAKE_ANALYZE.split("\n", 1)[1])
        with mock.patch.object(static_common, "ROOT", self.known):
            code, text = self.ghidra_run("--range", "1000:0400-1000:0460", "--record", "test-range.json")
        self.assertEqual(code, 0, text)
        self.assertIn("range=1000:0400-1000:0460", args.read_text())
        record = json.loads((self.known / static_common.MEASUREMENTS / "test-range.json").read_text())
        self.assertEqual(record["report"]["ranges"],
                         [{"start": "1000:0400", "end": "1000:0460", "instructions": 30, "far_calls": 4}])

    def test_a_malformed_range_is_refused_before_anything_runs(self):
        for bad in ("1000:0400", "1000:0400-x", "../x-1000:0000"):
            with self.subTest(bad=bad):
                code, _ = self.ghidra_run("--range", bad)
                self.assertIn("is not START-END", str(code))
        self.assertEqual(self.static_entries(), [])


def walk(directory):
    """{relative path: sha256} of every file under a directory, for comparing with an inventory."""
    return {path.relative_to(directory).as_posix(): sha(path.read_bytes())
            for path in Path(directory).rglob("*") if path.is_file() and not path.is_symlink()}


class InventoryTest(World):
    """T26 round 1, R2: every file a run leaves in the static folder is recorded by sha256 and size, and
    check_derived_hashes.py knows a tracked copy of any of them, whatever its name."""

    def record(self, name):
        return json.loads((self.known / static_common.MEASUREMENTS / name).read_text())

    def runs(self):
        with mock.patch.object(static_common, "ROOT", self.known):
            self.assertEqual(self.ghidra_run("--range", "1000:0400-1000:0460", "--record", "g.json")[0], 0)
            self.assertEqual(self.extract("--record", "p.json")[0], 0)
            self.assertEqual(self.unpack("--record", "d.json")[0], 0)

    def assert_inventory_is_the_folder(self, inventory, folder):
        self.assertEqual({item["path"]: item["sha256"] for item in inventory}, walk(folder))
        for item in inventory:
            self.assertEqual(item["bytes"], (folder / item["path"]).stat().st_size)

    def test_each_run_records_every_file_of_its_directory(self):
        self.runs()
        ghidra = self.record("g.json")["derived_files"]
        self.assert_inventory_is_the_folder(ghidra, self.static / "ghidra-t1")
        paths = [item["path"] for item in ghidra]
        for expected in ("listing-1000-0400.txt", "project/t26.rep/idata/00/~00000000.db", "report.txt",
                         "analyzeHeadless.out"):
            self.assertIn(expected, paths)
        extract = self.record("p.json")["derived_files"]
        self.assert_inventory_is_the_folder(extract, self.static / "iwp-extract-t1")
        paths = [item["path"] for item in extract]
        for expected in ("movie-01.dxr", "movie-01.abs.dxr", "movie-01-json/movie/chunks/CASt-0.json",
                         "movie-01-out/movie/casts/Internal/MovieScript 7 - Saver.ls", "movie-01-projectorrays.out"):
            self.assertIn(expected, paths)
        unpack = self.record("d.json")["derived_files"]
        self.assert_inventory_is_the_folder(unpack, self.static / "deark-t1")
        self.assertIn("deark-stage1-pklite.out", [item["path"] for item in unpack])
        for record in ("g.json", "p.json", "d.json"):
            self.assertEqual(static_common.leaks(json.dumps(self.record(record))), [])

    def test_a_link_in_a_run_directory_is_listed_and_not_followed(self):
        run = self.static / "by-hand"
        run.mkdir()
        (run / "file.bin").write_bytes(b"made by hand")
        (run / "to-original").symlink_to(self.dos / "ISLEWAR.EXE")
        self.assertEqual(static_common.inventory(run), [
            {"path": "file.bin", "sha256": sha(b"made by hand"), "bytes": 12},
            {"path": "to-original", "link": True}])

    def test_the_inventory_script_records_each_folder_once_and_never_rewrites(self):
        self.runs()
        code, text = self.inventory()
        self.assertEqual(code, 0, text)
        for folder in ("deark-t1", "ghidra-t1", "iwp-extract-t1"):
            record = self.record(f"test-inv-{folder}.json")
            self.assertEqual(record["run_directory"], folder)
            self.assert_inventory_is_the_folder(record["derived_files"], self.static / folder)
        before = self.record("test-inv-ghidra-t1.json")
        (self.static / "ghidra-t1" / "extra.txt").write_text("later")
        code, _ = self.inventory()
        self.assertIn("never overwritten", str(code))
        self.assertEqual(self.record("test-inv-ghidra-t1.json"), before)
        for bad in (["--dir", "../x", "--prefix", "p"], ["--dir", "x", "--prefix", "../p"]):
            with self.subTest(argv=bad), mock.patch.object(static_common, "ROOT", self.known):
                code, _ = self.call(inventory_derived, bad)
                self.assertIn("not a plain", str(code))

    def test_a_tracked_copy_of_a_listing_a_ghidra_database_or_a_dumped_chunk_fails_under_any_name(self):
        self.runs()
        sources = {"notes.txt": ("ghidra-t1", "listing-1000-0400.txt"),
                   "data.bin": ("ghidra-t1", "project/t26.rep/idata/00/~00000000.db"),
                   "config.json": ("iwp-extract-t1", "movie-01-json/movie/chunks/Lctx-9.json")}
        for name, (run, rel) in sources.items():
            with self.subTest(copy=name):
                root = self.tmp / ("repo-" + name.replace(".", "-"))
                (root / static_common.MEASUREMENTS).mkdir(parents=True)
                subprocess.run(["git", "init", "-q", str(root)], check=True)
                for record in ("g.json", "p.json"):
                    (root / static_common.MEASUREMENTS / record).write_bytes(
                        (self.known / static_common.MEASUREMENTS / record).read_bytes())
                (root / name).write_bytes((self.static / run / rel).read_bytes())
                subprocess.run(["git", "add", "-f", "."], cwd=root, check=True)
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    code = check_derived_hashes.main(["--root", str(root)])
                self.assertEqual(code, 1, out.getvalue())
                self.assertIn(f"{name}: its sha256 is listed in", out.getvalue())
                self.assertIn(f"(the run's file {rel})", out.getvalue())

    def test_the_checker_counts_the_inventoried_files(self):
        self.runs()
        root = self.tmp / "repo-count"
        (root / static_common.MEASUREMENTS).mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        (root / static_common.MEASUREMENTS / "g.json").write_bytes(
            (self.known / static_common.MEASUREMENTS / "g.json").read_bytes())
        subprocess.run(["git", "add", "-f", "."], cwd=root, check=True)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(check_derived_hashes.main(["--root", str(root)]), 0)
        count = len(self.record("g.json")["derived_files"])
        self.assertIn(f"({count} inventoried derived files among them)", out.getvalue())


class MarkersTest(World):
    """T26 round 1, R5: ProjectorRays' error markers are counted, in the scripts the record lists."""

    def extracted(self):
        with mock.patch.object(static_common, "ROOT", self.known):
            self.assertEqual(self.extract("--record", "p.json")[0], 0)
        return self.static / "iwp-extract-t1" / "movie-01-out" / "movie" / "casts" / "Internal"

    def count(self, *extra, env=None):
        with mock.patch.object(static_common, "ROOT", self.known):
            return self.call(iwp_markers, ["--dir", "iwp-extract-t1", "--against", "p.json", *extra], env)

    def test_a_clean_output_counts_zero_markers_over_every_listed_script(self):
        self.extracted()
        code, text = self.count("--record", "m.json")
        self.assertEqual(code, 0, text)
        movie = json.loads((self.known / static_common.MEASUREMENTS / "m.json").read_text())["movies"][0]
        self.assertEqual((movie["ls_files"], movie["lasm_files"], movie["scripts_in_record"]), (3, 2, 3))
        self.assertEqual((movie["error_words_in_ls"], movie["unknown_opcodes_in_lasm"]), (0, 0))

    def test_each_marker_is_counted_as_a_whole_word(self):
        folder = self.tmp / "out"
        folder.mkdir()
        texts = {"MovieScript 1.ls": "on a\n  ERROR\n  -- ERROR: Stray endrepeat\n  put ERRORS\nend\n",
                 "MovieScript 1.lasm": "  unk5F\n  unk5f\n  pushcons 1\n  xunk12\n",
                 "CastScript 2.ls": "on b\nend\n", "CastScript 2.lasm": "  ret\n"}
        for name, text in texts.items():
            (folder / name).write_text(text)
        scripts = [{"ls_sha256": sha(texts["MovieScript 1.ls"].encode()), "lasm_sha256": sha(texts["MovieScript 1.lasm"].encode())},
                   {"ls_sha256": sha(texts["CastScript 2.ls"].encode()), "lasm_sha256": sha(texts["CastScript 2.lasm"].encode())}]
        counts = iwp_markers.count_markers(folder, scripts)
        self.assertEqual((counts["error_words_in_ls"], counts["ls_files_with_an_error_word"]), (2, 1))
        self.assertEqual((counts["unknown_opcodes_in_lasm"], counts["lasm_files_with_an_unknown_opcode"]), (1, 1))

    def test_an_empty_script_and_an_empty_listing_are_both_counted(self):
        folder = self.tmp / "empty"
        folder.mkdir()
        (folder / "MovieScript 1.ls").write_text("")
        (folder / "MovieScript 1.lasm").write_text("  ret\n")
        (folder / "MovieScript 2.ls").write_text("on b\nend\n")
        (folder / "MovieScript 2.lasm").write_text("")
        scripts = [{"ls_sha256": sha(b""), "lasm_sha256": sha(b"  ret\n")},
                   {"ls_sha256": sha(b"on b\nend\n"), "lasm_sha256": sha(b"")}]
        counts = iwp_markers.count_markers(folder, scripts)
        self.assertEqual((counts["ls_files"], counts["lasm_files"]), (2, 2))

    def test_a_changed_or_missing_script_stops_the_count(self):
        folder = self.extracted()
        (folder / "BehaviorScript 9.ls").write_text("on mouseDown\n  ERROR\nend\n")
        code, _ = self.count()
        self.assertIn("not in movie-01-out with their recorded sha256", str(code))

    def test_a_script_the_record_does_not_list_is_not_counted(self):
        folder = self.extracted()
        (folder / "MovieScript 99.ls").write_text("on z\n  ERROR\nend\n")
        code, text = self.count("--record", "m.json")
        self.assertEqual(code, 0, text)
        movie = json.loads((self.known / static_common.MEASUREMENTS / "m.json").read_text())["movies"][0]
        self.assertEqual((movie["ls_files"], movie["error_words_in_ls"]), (3, 0))

    def test_an_unset_or_in_checkout_static_folder_is_refused(self):
        self.extracted()
        checkout = self.tmp / "checkout"
        (checkout / ".git").mkdir(parents=True)
        for env, says in ((dict(self.env, IWA_STATIC=""), "IWA_STATIC is not set"),
                          (dict(self.env, IWA_STATIC=str(checkout)), "inside a checkout")):
            with self.subTest(says=says):
                code, _ = self.count(env=env)
                self.assertIn(says, str(code))


if __name__ == "__main__":
    unittest.main()
