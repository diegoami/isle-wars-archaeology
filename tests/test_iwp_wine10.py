"""Fix #159: the runtime accepts Wine 10.0 (the new computer's only Wine), its tool checks run on a
display of their own and never on the inherited one, and every new record names the font set.

No real Wine or X server is needed: fake binaries and a fake probe stand in for them.
"""
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from iwp_fixtures import ROOT, token_check  # noqa: E402
from test_iwp_spike import cycle  # noqa: E402


class Fakes(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def fake(self, name, body, directory=None):
        directory = directory or self.tmp / "bin"
        directory.mkdir(exist_ok=True)
        path = directory / name
        path.write_text("#!/bin/sh\n" + body + "\n")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
        return path


class Wine10TokenTest(Fakes):
    def check(self, fn, body):
        with mock.patch.object(token_check, "WINE", str(self.fake("wine", body))):
            return fn()

    def test_10_0_is_accepted_by_the_10_0_check(self):
        self.assertIsNone(self.check(token_check.wine10, 'echo "wine-10.0 (Ubuntu 10.0~repack-12ubuntu1)"'))

    def test_the_10_0_check_refuses_every_other_answer_and_names_what_it_saw(self):
        cases = {"nine": 'echo "wine-9.0 (Ubuntu 9.0~repack-4build3)"', "ten-one": 'echo "wine-10.1"',
                 "empty": "exit 0", "fails": 'echo "wine-10.0"; exit 1', "garbage": 'echo "hello"'}
        for label, body in cases.items():
            with self.subTest(label):
                problem = self.check(token_check.wine10, body)
                self.assertIsNotNone(problem)
                self.assertIn("not 10.0", problem)
        self.assertIn("wine-9.0", self.check(token_check.wine10, cases["nine"]))
        with mock.patch.object(token_check, "WINE", str(self.tmp / "absent")):
            self.assertIn("not installed", token_check.wine10())

    def test_the_9_0_check_is_unchanged_and_refuses_10_0(self):
        self.assertIsNone(self.check(token_check.wine, 'echo "wine-9.0 (Ubuntu 9.0~repack-4build3)"'))
        self.assertIn("not 9.0", self.check(token_check.wine, 'echo "wine-10.0 (Ubuntu 10.0~repack-12ubuntu1)"'))

    def test_a_wine_probe_that_hangs_is_a_problem_string(self):
        with mock.patch.object(token_check, "PROBE_TIMEOUT", 1):
            problem = self.check(token_check.wine10, "exec sleep 30")
        self.assertIsInstance(problem, str)
        self.assertIn("did not answer", problem)

    def test_the_capabilities_name_both_pins_and_the_runtime_asks_for_10_0(self):
        capabilities = json.loads((ROOT / "capabilities.json").read_text(encoding="utf-8"))
        self.assertEqual(capabilities["tool:wine@10.0"]["check"], "python3 setup/iwp/token_check.py wine10")
        self.assertEqual(capabilities["tool:wine@9.0"]["check"], "python3 setup/iwp/token_check.py wine")
        self.assertIn("wine10", token_check.CHECKS)
        script = (ROOT / "setup" / "iwp" / "iwp-runtime.sh").read_text(encoding="utf-8")
        self.assertIn("tool:wine@10.0", script)
        self.assertNotIn("tool:wine@9.0", script)


class OwnDisplayTest(Fakes):
    """xfwm4 and xdotool are probed on a throwaway Xvfb, never on the inherited DISPLAY."""

    ON_OWN = '[ "$DISPLAY" = "$(cat LOG)" ]'

    def setup_bin(self, xfwm4_body, xdotool_body):
        """Fakes whose probes see the display the fake Xvfb was started with (LOG holds it)."""
        log = self.tmp / "xvfb-display"
        bin_dir = self.tmp / "bin"
        self.fake("Xvfb", f'echo "$1" > "{log}"; exec sleep 30', bin_dir)
        self.fake("xdpyinfo", f'[ -s "{log}" ]', bin_dir)
        self.fake("xfwm4", xfwm4_body.replace("LOG", str(log)), bin_dir)
        self.fake("xdotool", xdotool_body.replace("LOG", str(log)), bin_dir)
        return {"PATH": f"{bin_dir}{os.pathsep}/usr/bin{os.pathsep}/bin"}

    def test_the_probes_run_on_the_throwaway_display_whatever_is_inherited(self):
        env = self.setup_bin(self.ON_OWN, self.ON_OWN)
        for inherited in (":0", ":42", None):
            with self.subTest(inherited=inherited):
                with mock.patch.dict(os.environ, env):
                    if inherited is None:
                        os.environ.pop("DISPLAY", None)
                    else:
                        os.environ["DISPLAY"] = inherited
                    self.assertIsNone(token_check.xfwm4())
                    self.assertIsNone(token_check.xdotool())

    def test_a_probe_that_hangs_on_a_dead_display_passes_on_its_own(self):
        hang = '[ "$DISPLAY" = "$(cat LOG)" ] || exec sleep 30'
        env = self.setup_bin(hang, hang)
        with mock.patch.dict(os.environ, {**env, "DISPLAY": ":42"}), \
                mock.patch.object(token_check, "PROBE_TIMEOUT", 5):
            self.assertIsNone(token_check.xfwm4())
            self.assertIsNone(token_check.xdotool())

    def test_a_probe_that_never_answers_is_a_string_not_a_traceback(self):
        env = self.setup_bin("exec sleep 30", "exec sleep 30")
        with mock.patch.dict(os.environ, {**env, "DISPLAY": ":42"}), \
                mock.patch.object(token_check, "PROBE_TIMEOUT", 1):
            for check in (token_check.xfwm4, token_check.xdotool):
                with self.subTest(check=check.__name__):
                    problem = check()
                    self.assertIsInstance(problem, str)
                    self.assertIn("did not answer", problem)

    def test_a_failing_probe_is_refused(self):
        env = self.setup_bin("exit 1", "exit 1")
        with mock.patch.dict(os.environ, env):
            self.assertIsNotNone(token_check.xfwm4())
            self.assertIsNotNone(token_check.xdotool())

    def test_a_missing_binary_is_refused_without_starting_a_display(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        with mock.patch.dict(os.environ, {"PATH": str(empty)}):
            self.assertIn("not on PATH", token_check.xfwm4())
            self.assertIn("not on PATH", token_check.xdotool())

    def test_the_throwaway_xvfb_is_stopped_afterwards(self):
        env = self.setup_bin("exit 0", "exit 0")
        import prefix as prefix_helpers
        original = prefix_helpers.start_xvfb
        started = []

        def start(size):
            proc, display = original(size)
            started.append(proc)
            return proc, display

        with mock.patch.dict(os.environ, env), mock.patch.object(prefix_helpers, "start_xvfb", start):
            self.assertIsNone(token_check.xfwm4())
        self.assertEqual(len(started), 1)
        self.assertIsNotNone(started[0].poll())


class FontsTest(unittest.TestCase):
    def test_only_installed_packages_sorted(self):
        out = ("ii  fonts-wine=10.0~repack-12ubuntu1\nun  fonts-arphic-ukai=\n"
               "ii  fonts-dejavu-core=2.37-8build1\nrc  fonts-old=1.0\n")
        self.assertEqual(cycle.fonts_line(out), "fonts-dejavu-core=2.37-8build1, fonts-wine=10.0~repack-12ubuntu1")

    def test_no_installed_font_is_unknown(self):
        self.assertEqual(cycle.fonts_line("un  fonts-arphic-ukai=\n"), "unknown")

    def test_a_path_separator_never_reaches_a_record(self):
        value = cycle.fonts_line("ii  fonts-a=1/2\nii  fonts-b=3\\4\n")
        self.assertNotIn("/", value)
        self.assertNotIn("\\", value)

    def test_versions_carries_the_font_set(self):
        def fake_probe(cmd, **kw):
            if cmd[0] == "dpkg-query" and cmd[-1] == "fonts-*":
                return (True, b"ii  fonts-wine=10.0\nun  fonts-x=\nii  fonts-a=2\n", b"")
            return (False, b"", b"")
        with mock.patch.object(cycle, "probe", side_effect=fake_probe):
            self.assertEqual(cycle.versions()["fonts"], "fonts-a=2, fonts-wine=10.0")
        with mock.patch.object(cycle, "probe", return_value=(False, b"ii  fonts-wine=1\n", b"failed")):
            self.assertEqual(cycle.versions()["fonts"], "unknown")


if __name__ == "__main__":
    unittest.main()
