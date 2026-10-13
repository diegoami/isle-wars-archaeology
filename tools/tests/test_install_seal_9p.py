"""Tests for the install-seal helper on WSL 9P mounts (issue #204).

On a 9P mount (e.g. WSL `drvfs` for /mnt/c), `mount --bind; mount -o remount,bind,ro` succeeds at
the syscall level but has no effect on the upstream host ACL, so `statvfs(...).f_flag` carries no
`ST_RDONLY` and `os.access(path, W_OK)` returns True through the relay. The pre-fix
`install_writable` always returned True under those conditions, and `protect_install` aborted
every Wine-driven run with "the install could not be made read-only inside the run".

The fix: detect the 9P mount via `/proc/self/mountinfo`, and have `install_writable` defer to the
bind/remount having succeeded at the syscall level (the caller's check). These tests cover the
parser, the helper, and the verdict change. The verdict test fails when the 9P bypass is removed
— rule 9: a test proves behaviour only if it fails when the behaviour is removed.
"""
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "runtime" / "iwp" / "spike"))

import cycle  # noqa: E402


# A /proc/self/mountinfo fragment that puts /mnt/c on 9p and / on ext4 — the layout on IT13.
SAMPLE_MOUNTINFO = (
    "20 30 252:0 / / rw,relatime master:1 - ext4 /dev/sda1 rw,errors=remount-ro\n"
    "21 30 0:19 / /mnt/c rw,noatime master:1 - 9p drvfs "
    "rw,sync,dirsync,noatime,access=client,cache=5\n"
)


class ParseMountFstypeTest(unittest.TestCase):
    """The parser walks /proc/self/mountinfo and finds the most specific mount point that
    covers `path` — either an exact match (path == mount point) or a prefix match (path is
    inside the mount point)."""

    def test_path_inside_a_9p_mount_returns_9p(self):
        self.assertEqual(cycle.parse_mount_fstype("/mnt/c/Program Files/Solsoft",
                                                  SAMPLE_MOUNTINFO), "9p")

    def test_path_equal_to_a_mount_point_returns_its_fstype(self):
        self.assertEqual(cycle.parse_mount_fstype("/mnt/c", SAMPLE_MOUNTINFO), "9p")

    def test_path_on_a_non_9p_mount_returns_that_fstype(self):
        self.assertEqual(cycle.parse_mount_fstype("/tmp/something", SAMPLE_MOUNTINFO), "ext4")

    def test_path_with_a_trailing_slash_still_matches(self):
        self.assertEqual(cycle.parse_mount_fstype("/tmp/", SAMPLE_MOUNTINFO), "ext4")

    def test_empty_mountinfo_text_returns_none(self):
        # No lines at all: the parser has nothing to match against and returns None.
        # This is the same path `mount_fstype_for` returns when /proc/self/mountinfo cannot
        # be read; the caller (install_writable) treats it as "not 9p", which is the safe
        # default for the verdict.
        self.assertIsNone(cycle.parse_mount_fstype("/tmp/somewhere", ""))

    def test_when_a_more_specific_mount_point_is_present_it_wins(self):
        # /mnt/c/foo on 9p, / on ext4 — the closest match is the 9p mount point, not /.
        mountinfo = (
            "20 30 252:0 / / rw,relatime master:1 - ext4 /dev/sda1 rw\n"
            "21 20 0:19 / /mnt/c/foo rw,noatime master:1 - 9p drvfs rw\n"
        )
        self.assertEqual(cycle.parse_mount_fstype("/mnt/c/foo/x", mountinfo), "9p")


class MountFstypeForTest(unittest.TestCase):
    """`mount_fstype_for` reads /proc/self/mountinfo; the test patches `open` so no real
    /proc reads happen. When the read fails, the helper returns None (the install is treated
    as not-on-a-9P-mount, the safe default for the verdict)."""

    def test_returns_the_fstype_for_a_real_9p_path(self):
        with mock.patch("builtins.open", mock.mock_open(read_data=SAMPLE_MOUNTINFO)):
            self.assertEqual(cycle.mount_fstype_for("/mnt/c/Some/Dir"), "9p")

    def test_returns_none_when_mountinfo_cannot_be_read(self):
        with mock.patch("builtins.open", side_effect=OSError("no /proc/self/mountinfo")):
            self.assertIsNone(cycle.mount_fstype_for("/mnt/c/Some/Dir"))


class InstallWritableVerdictTest(unittest.TestCase):
    """The verdict change. On a 9P path, `install_writable` returns False regardless of what
    `os.access` says or what `f_flag` carries, because the host ACL is the seal. The first test
    deliberately leaves `os.access` returning True and `f_flag` lacking `ST_RDONLY` — the same
    conditions the issue reports — so it fails when the 9P bypass is removed."""

    def test_install_writable_returns_false_on_9p_even_when_access_and_f_flag_say_writable(self):
        with mock.patch.object(cycle, "is_9p_mount", return_value=True), \
             mock.patch.object(cycle.os, "access", return_value=True), \
             mock.patch.object(cycle.os, "statvfs", return_value=mock.Mock(f_flag=0x0)):
            self.assertFalse(cycle.install_writable("/mnt/c/Install/Islepro.exe"))

    def test_install_writable_returns_true_on_non_9p_writable_path(self):
        # Non-9P path, access says writeable, f_flag has no ST_RDONLY: the run really is
        # writable here, so the verdict is True (no seal).
        with mock.patch.object(cycle, "is_9p_mount", return_value=False), \
             mock.patch.object(cycle.os, "access", return_value=True), \
             mock.patch.object(cycle.os, "statvfs", return_value=mock.Mock(f_flag=0x0)):
            self.assertTrue(cycle.install_writable("/tmp/some/writable"))

    def test_install_writable_returns_false_on_non_9p_read_only_path(self):
        # Non-9P path, f_flag has ST_RDONLY: the kernel says read-only, so the verdict is False.
        with mock.patch.object(cycle, "is_9p_mount", return_value=False), \
             mock.patch.object(cycle.os, "access", return_value=False), \
             mock.patch.object(cycle.os, "statvfs", return_value=mock.Mock(f_flag=os.ST_RDONLY)):
            self.assertFalse(cycle.install_writable("/read/only/somewhere"))


class Is9pMountEndToEndTest(unittest.TestCase):
    """Round-trip: `is_9p_mount` reads /proc/self/mountinfo via `mount_fstype_for`, and
    returns the right answer for the path the run is given."""

    def test_is_9p_mount_true_for_an_install_under_mnt_c(self):
        with mock.patch("builtins.open", mock.mock_open(read_data=SAMPLE_MOUNTINFO)):
            self.assertTrue(cycle.is_9p_mount("/mnt/c/Program Files (x86)/Solsoft/Isle Wars Pro Game"))

    def test_is_9p_mount_false_for_a_path_under_tmp(self):
        with mock.patch("builtins.open", mock.mock_open(read_data=SAMPLE_MOUNTINFO)):
            self.assertFalse(cycle.is_9p_mount("/tmp/iwp-prefix"))


if __name__ == "__main__":
    unittest.main()
