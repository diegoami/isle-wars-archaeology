"""The parts of the W3a spike that run without the game: PNG bytes, registry and tree diffs, process
markers, and the prefix helper's link removal and check. The game itself is exercised by the cycle
(experiments/E001-iwp-runtime-spike), not here.
"""
import importlib.util
import os
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


cycle = load("iwp_cycle", "runtime/iwp/spike/cycle.py")
prefix = load("iwp_prefix", "setup/iwp/prefix.py")


class PngTest(unittest.TestCase):
    def test_png_is_deterministic_and_decodes_to_the_pixels(self):
        pixels = bytes((x * 7 + y * 3) % 256 for y in range(4) for x in range(5) for _ in range(3))
        first = cycle.png_bytes(5, 4, pixels)
        self.assertEqual(first, cycle.png_bytes(5, 4, pixels))
        self.assertEqual(first[:8], b"\x89PNG\r\n\x1a\n")
        # walk the chunks: only IHDR, IDAT, IEND (no date or time chunk), every CRC right
        kinds, offset, idat = [], 8, b""
        while offset < len(first):
            (length,) = struct.unpack(">I", first[offset:offset + 4])
            kind, body = first[offset + 4:offset + 8], first[offset + 8:offset + 8 + length]
            (crc,) = struct.unpack(">I", first[offset + 8 + length:offset + 12 + length])
            self.assertEqual(crc, zlib.crc32(kind + body))
            kinds.append(kind)
            if kind == b"IDAT":
                idat += body
            offset += 12 + length
        self.assertEqual(kinds, [b"IHDR", b"IDAT", b"IEND"])
        rows = zlib.decompress(idat)
        self.assertEqual(b"".join(rows[1 + y * 16:1 + y * 16 + 15] for y in range(4)), pixels)

    def test_different_pixels_give_different_files(self):
        self.assertNotEqual(cycle.png_bytes(1, 1, b"\0\0\0"), cycle.png_bytes(1, 1, b"\0\0\1"))


class DiffTest(unittest.TestCase):
    def test_tree_snapshot_and_diff_see_added_removed_changed_and_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "keep").write_text("a")
            (base / "gone").write_text("b")
            (base / "edit").write_text("c")
            os.symlink("/dev/null", base / "link")
            before = cycle.snapshot_tree(base)
            (base / "gone").unlink()
            (base / "edit").write_text("changed")
            (base / "new").write_text("n")
            os.unlink(base / "link")
            os.symlink("/dev/zero", base / "link")
            after = cycle.snapshot_tree(base)
        added, removed, changed = cycle.diff_tree(before, after)
        self.assertEqual((added, removed, changed), (["new"], ["gone"], ["edit", "link"]))

    def test_same_content_in_a_new_mtime_is_not_a_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "f"
            path.write_text("same")
            before = cycle.snapshot_tree(tmp)
            os.utime(path, (1, 1))
            self.assertEqual(cycle.diff_tree(before, cycle.snapshot_tree(tmp)), ([], [], []))


class RegistryTest(unittest.TestCase):
    def reg(self, tmp, stamp, value):
        Path(tmp, "user.reg").write_text(
            f"WINE REGISTRY Version 2\n;; All keys relative to \\\\User\\\\S-1\n\n#arch=win32\n\n"
            f"[Software\\\\Wine\\\\A] {stamp}\n#time=1d{stamp}\n\"v\"=\"{value}\"\n\n"
            f"[Software\\\\Wine\\\\B] {stamp}\n#time=1d{stamp}\n\"w\"=\"1\"\n")

    def test_timestamps_are_ignored_and_values_are_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.reg(tmp, 1000, "x")
            first = cycle.registry_keys(tmp)
            self.reg(tmp, 2000, "x")
            same = cycle.registry_keys(tmp)
            self.reg(tmp, 3000, "y")
            changed = cycle.registry_keys(tmp)
        self.assertEqual(sorted(first), ["user.reg: Software\\\\Wine\\\\A", "user.reg: Software\\\\Wine\\\\B"])
        self.assertEqual(first, same)
        self.assertNotEqual(first["user.reg: Software\\\\Wine\\\\A"], changed["user.reg: Software\\\\Wine\\\\A"])
        self.assertEqual(first["user.reg: Software\\\\Wine\\\\B"], changed["user.reg: Software\\\\Wine\\\\B"])


class MarkerTest(unittest.TestCase):
    def test_a_child_carrying_the_marker_is_found_and_one_without_is_not(self):
        env = dict(os.environ, **{cycle.MARK: "E001-test-marker"})
        child = subprocess.Popen(["sleep", "30"], env=env)
        plain = subprocess.Popen(["sleep", "30"], env={k: v for k, v in os.environ.items() if k != cycle.MARK})
        try:
            self.assertIn(child.pid, cycle.marked_processes("E001-test-marker"))
            self.assertNotIn(plain.pid, cycle.marked_processes("E001-test-marker"))
            self.assertNotIn(child.pid, cycle.marked_processes("E001-other"))
        finally:
            child.kill()
            plain.kill()
            child.wait()
            plain.wait()


class PrefixTest(unittest.TestCase):
    def make_prefix(self, tmp):
        pfx = Path(tmp) / "p"
        (pfx / "dosdevices").mkdir(parents=True)
        (pfx / "drive_c" / "users" / "u").mkdir(parents=True)
        (pfx / "system.reg").write_text("x")
        os.symlink("../drive_c", pfx / "dosdevices" / "c:")
        os.symlink("/", pfx / "dosdevices" / "z:")
        os.symlink("/dev/ttyS0", pfx / "dosdevices" / "com1")
        os.symlink("/home", pfx / "drive_c" / "users" / "u" / "Desktop")
        return pfx

    def test_strip_links_removes_z_com_and_absolute_profile_links_but_keeps_c(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfx = self.make_prefix(tmp)
            os.environ["IWP_PREFIX"] = str(pfx)
            try:
                self.assertEqual(len(prefix.absolute_links(pfx)), 3)
                with redirect_stdout(StringIO()):
                    prefix.strip_links()
                self.assertEqual(sorted(p.name for p in (pfx / "dosdevices").iterdir()), ["c:"])
                desktop = pfx / "drive_c" / "users" / "u" / "Desktop"
                self.assertTrue(desktop.is_dir() and not desktop.is_symlink())
                self.assertEqual(prefix.absolute_links(pfx), [])
            finally:
                del os.environ["IWP_PREFIX"]

    def test_check_fails_while_z_exists_and_names_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfx = self.make_prefix(tmp)
            os.environ["IWP_PREFIX"] = str(pfx)
            try:
                out = StringIO()
                with redirect_stdout(out):
                    code = prefix.check()
                self.assertEqual(code, 1)
                self.assertIn("dosdevices/z: exists", out.getvalue())
                self.assertIn("absolute link: dosdevices/com1", out.getvalue())
            finally:
                del os.environ["IWP_PREFIX"]


if __name__ == "__main__":
    unittest.main()
