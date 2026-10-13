"""Issue #215: mocked wow64 boot must finish before links and registry are sealed."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import prefix


class BootBaselineTest(unittest.TestCase):
    def test_boot_complete_registry_and_links_for_new_and_existing_prefix(self):
        for existing in (False, True):
            with self.subTest(existing=existing), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                home, baseline = root / "prefix", root / "baseline"
                home.mkdir()
                (home / "drive_c").mkdir()
                (home / "dosdevices").mkdir()
                if existing:
                    (home / "system.reg").write_text("preboot")
                calls = []

                def run(command, **kwargs):
                    calls.append(command)
                    self.assertNotIn("WINEARCH", kwargs["env"])
                    if command == [prefix.WINE, "wineboot", "-u"]:
                        (home / "system.reg").write_text("preboot")
                    if command == [prefix.WINE, "wineboot", "-e"]:
                        (home / "dosdevices" / "com1").symlink_to("/dev/ttyS0")
                    if command == [prefix.WINESERVER, "-w"]:
                        if [prefix.WINE, "wineboot", "-e"] in calls:
                            (home / "system.reg").write_text("boot-complete")
                            (home / "user.reg").write_text("boot-complete-user")
                    return subprocess.CompletedProcess(command, 0)

                locs = {"IWP_PREFIX": home, "IWP_PREFIX.baseline": baseline}
                xvfb = mock.Mock()
                with mock.patch.object(prefix.locations, "locations", return_value=locs), \
                        mock.patch.object(prefix, "start_xvfb", return_value=(xvfb, ":123")), \
                        mock.patch.object(prefix.subprocess, "run", side_effect=run), \
                        mock.patch.dict(os.environ, {"WINEARCH": "win32"}):
                    prefix.build()
                    prefix.strip_links()
                    prefix.baseline()
                    self.assertEqual((baseline / "system.reg").read_text(), "boot-complete")
                    self.assertEqual((baseline / "user.reg").read_text(), "boot-complete-user")
                    self.assertFalse((home / "dosdevices" / "com1").is_symlink())
                    self.assertEqual([p.name for p in (home / "dosdevices").iterdir()], ["c:"])
                    self.assertIn([prefix.WINE, "wineboot", "-e"], calls)
                    calls.clear()
                    prefix.build()
                    prefix.baseline()
                    self.assertEqual(calls, [])
                xvfb.terminate.assert_called_once()
                xvfb.wait.assert_called_once_with(10)


if __name__ == "__main__":
    unittest.main()
