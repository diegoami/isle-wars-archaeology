"""Safety tests of the iw-dos-runtime profile and the E003 cycle (T11), on synthetic fixtures.

Every test builds its own copy (IW_DOS_DIR), run directory, bundles and known.json in a temporary
directory outside any checkout. None reads or writes the real copy or the real run directory: the
environment is replaced for each test, and rundir.KNOWN_ROOT points at a throwaway git checkout
whose artifacts/known.json registers a synthetic set under the real set's id, so the real
`tools/register_artifact.py check --strict` runs against it.

The four guarantees of T11's Done-when 3, each with the tests that fail when it is removed
(tests/mutants_iw_dos.py removes each and shows the test failing):
- a run directory inside a checkout is refused: RunLocationsTest;
- a configuration that mounts anything but the run copy aborts the run before launch: ConfTest,
  LaunchGateTest;
- a run copy that fails `check --strict` aborts the run before launch: RunCopyTest, LaunchGateTest;
- a capture failure records `aborted`: InnerTest.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "setup" / "iwp"))
sys.path.insert(0, str(ROOT / "setup" / "iw-dos"))
sys.path.insert(0, str(ROOT / "runtime" / "iw-dos" / "spike"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


import locations  # noqa: E402
import safeio  # noqa: E402
import rundir  # noqa: E402
import dosconf  # noqa: E402

cycle = load("iw_dos_cycle", "runtime/iw-dos/spike/cycle.py")
token_check = load("iw_dos_token_check", "setup/iw-dos/token_check.py")
tokens = load("iw_dos_tokens", "setup/iw-dos/tokens.py")
assert cycle.rundir is rundir and cycle.dosconf is dosconf and cycle.safeio is safeio

FILES = {"ISLEWAR.EXE": b"MZ synthetic", "ISLEWAR.DAT": b"1,2,3"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


MANIFEST = {"schema": "artifact-set/1", "id": rundir.SET_ID, "title": "synthetic", "version": "3.1",
            "files": [{"path": p, "bytes": len(d), "sha256": sha(d)} for p, d in sorted(FILES.items())],
            "runtime_writes": []}


class World(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(os.path.realpath(self._tmp.name))
        if locations.checkout_of(self.tmp) is not None:
            self.skipTest("the temporary directory is inside a checkout; these tests need one outside every checkout")
        self.known = self.tmp / "known"
        (self.known / "artifacts").mkdir(parents=True)
        (self.known / "artifacts" / "known.json").write_text(json.dumps({"sets": [{"manifest": MANIFEST}]}))
        subprocess.run(["git", "init", "-q", str(self.known)], check=True)
        patcher = mock.patch.object(rundir, "KNOWN_ROOT", self.known)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.install = self.tmp / "install"
        self.install.mkdir()
        for name, data in FILES.items():
            (self.install / name).write_bytes(data)
        self.run_dir = self.tmp / "run"
        self.bundles = self.tmp / "bundles"
        self.env = {"IW_DOS_DIR": str(self.install), "IW_DOS_RUN": str(self.run_dir),
                    "E003_BUNDLES": str(self.bundles)}
        env = mock.patch.dict(os.environ, self.env)
        env.start()
        self.addCleanup(env.stop)
        for name in ("E003_EXPLORE", "E003_MACHINE"):
            os.environ.pop(name, None)

    def sync(self):
        with redirect_stdout(io.StringIO()):
            rundir.sync(self.env)
        return self.run_dir / rundir.GAME_DIR

    def refused(self, function):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            function()
        return str(caught.exception.code)


class RunLocationsTest(World):
    def test_a_good_layout_is_accepted(self):
        found = rundir.run_locations(self.env, need_bundles=True)
        self.assertEqual(found["IW_DOS_RUN"], self.run_dir)

    def test_a_run_directory_inside_a_checkout_is_refused_and_sync_creates_nothing(self):
        checkout = self.tmp / "checkout"
        (checkout / ".git").mkdir(parents=True)
        env = dict(self.env, IW_DOS_RUN=str(checkout / "run"))
        self.assertIn("checkout", self.refused(lambda: rundir.run_locations(env)))
        self.assertIn("checkout", self.refused(lambda: rundir.sync(env)))
        self.assertFalse((checkout / "run").exists())

    def test_this_repository_and_a_link_into_a_checkout_are_refused(self):
        self.assertIn("checkout", self.refused(lambda: rundir.run_locations(dict(self.env, IW_DOS_RUN=str(ROOT / "x")))))
        checkout = self.tmp / "checkout"
        (checkout / ".git").mkdir(parents=True)
        os.symlink(checkout, self.tmp / "alias")
        self.assertIn("checkout", self.refused(
            lambda: rundir.run_locations(dict(self.env, IW_DOS_RUN=str(self.tmp / "alias" / "run")))))

    def test_overlaps_with_the_copy_and_each_other_are_refused(self):
        for value in (str(self.install), str(self.install / "run"), str(self.tmp)):
            self.assertIn("overlaps", self.refused(lambda: rundir.run_locations(dict(self.env, IW_DOS_RUN=value))))
        env = dict(self.env, E003_BUNDLES=str(self.run_dir / "bundles"))
        self.assertIn("overlaps", self.refused(lambda: rundir.run_locations(env, need_bundles=True)))

    def test_the_cycle_refuses_a_run_directory_in_a_checkout_before_it_starts_anything(self):
        checkout = self.tmp / "checkout"
        (checkout / ".git").mkdir(parents=True)
        with mock.patch.dict(os.environ, {"IW_DOS_RUN": str(checkout / "run")}), \
                mock.patch.object(cycle, "run_namespace") as started, mock.patch.object(cycle, "run") as ran, \
                mock.patch.object(cycle, "popen") as spawned:
            self.assertIn("checkout", self.refused(lambda: cycle.outer(cycle.parser().parse_args([]))))
            self.assertIn("checkout", self.refused(lambda: cycle.inner(cycle.parser().parse_args([]))))
        started.assert_not_called()
        ran.assert_not_called()
        spawned.assert_not_called()


class RunCopyTest(World):
    def test_sync_makes_the_registered_set_and_is_idempotent(self):
        game = self.sync()
        self.assertEqual(rundir.run_problems(self.run_dir, self.install), [])
        (game / "ISLEWAR.SCR").write_bytes(b"written by the game")
        (game / "ISLEWAR.DAT").write_bytes(b"changed")
        with redirect_stdout(io.StringIO()) as out:
            rundir.sync(self.env)
        self.assertIn("copied 1, removed 1", out.getvalue())
        self.assertEqual(sorted(os.listdir(game)), sorted(FILES))
        with redirect_stdout(io.StringIO()) as out:
            rundir.sync(self.env)
        self.assertIn("copied 0, removed 0", out.getvalue())

    def test_a_copy_that_fails_check_strict_is_refused(self):
        game = self.sync()
        cases = {"unlisted": lambda: (game / "EXTRA.TXT").write_bytes(b"x"),
                 "ISLEWAR.DAT: sha256": lambda: (game / "ISLEWAR.DAT").write_bytes(b"9,9,9"),
                 "ISLEWAR.EXE: missing": lambda: (game / "ISLEWAR.EXE").unlink()}
        for words, damage in cases.items():
            with self.subTest(words):
                self.sync()
                damage()
                problems = rundir.run_problems(self.run_dir, self.install)
                self.assertTrue(any("check --strict" in p and words in p for p in problems), problems)

    def test_a_hard_link_to_the_copy_is_found_and_sync_gives_the_run_copy_a_file_of_its_own(self):
        game = self.sync()
        (game / "ISLEWAR.EXE").unlink()
        os.link(self.install / "ISLEWAR.EXE", game / "ISLEWAR.EXE")
        problems = rundir.run_problems(self.run_dir, self.install)
        self.assertTrue(any("ISLEWAR.EXE has 2 names" in p and "IW_DOS_DIR's" in p for p in problems), problems)
        self.sync()
        self.assertEqual(os.lstat(game / "ISLEWAR.EXE").st_nlink, 1)
        self.assertEqual(os.lstat(self.install / "ISLEWAR.EXE").st_nlink, 1)
        self.assertEqual((self.install / "ISLEWAR.EXE").read_bytes(), FILES["ISLEWAR.EXE"])
        self.assertEqual(rundir.run_problems(self.run_dir, self.install), [])

    def test_a_link_in_the_run_copy_is_found_and_replaced_without_writing_its_target(self):
        game = self.sync()
        (game / "ISLEWAR.DAT").unlink()
        os.symlink(self.install / "ISLEWAR.DAT", game / "ISLEWAR.DAT")
        self.assertTrue(any("is a link" in p for p in rundir.run_problems(self.run_dir, self.install)))
        self.sync()
        self.assertFalse((game / "ISLEWAR.DAT").is_symlink())
        self.assertEqual((self.install / "ISLEWAR.DAT").read_bytes(), FILES["ISLEWAR.DAT"])

    def test_a_run_copy_that_is_a_link_is_refused(self):
        self.run_dir.mkdir()
        os.symlink(self.install, self.run_dir / "game")
        self.assertIn("link", self.refused(lambda: rundir.sync(self.env)))
        self.assertEqual(rundir.run_problems(self.run_dir, self.install), ["the run copy is not a real directory"])

    def test_a_copy_whose_file_is_not_the_registered_one_copies_nothing(self):
        (self.install / "ISLEWAR.DAT").write_bytes(b"other")
        self.assertIn("nothing changed", self.refused(lambda: rundir.sync(self.env)))
        self.assertFalse(self.run_dir.exists())


class ConfTest(World):
    def setUp(self):
        super().setUp()
        self.game = self.sync()
        self.work = self.tmp / "work"
        self.text = dosconf.generate(self.game, self.work, "fixed 3000", ("01-01-1994", "12:00:00"))

    def problems(self, text, command=None):
        return dosconf.problems(text, self.game, self.work, command)

    def test_the_generated_configuration_passes(self):
        self.assertEqual(self.problems(self.text), [])
        self.assertEqual(self.problems(dosconf.generate(self.game, self.work)), [])

    def test_any_other_mount_is_refused(self):
        for line in ("mount d /", f'mount c "{self.install}"', 'mount d "/tmp"', "imgmount d /x.iso",
                     f"MOUNT D {self.tmp}", "subst d c:", "Z:", "c:mount d /"):
            with self.subTest(line):
                text = self.text.replace("@echo off\n", f"@echo off\n{line}\n")
                self.assertTrue(self.problems(text), line)
        replaced = self.text.replace(f'"{self.game}"', f'"{self.install}"')
        self.assertTrue(any("mount" in p for p in self.problems(replaced)))
        self.assertTrue(any("mount" in p for p in self.problems(self.text.replace(f'mount c "{self.game}"\n', ""))))

    def test_settings_that_mount_network_or_leave_the_work_directory_are_refused(self):
        for old, new in (("automountall=false", "automountall=true"), ("ne2000=false", "ne2000=true"),
                         ("ipx=false", "ipx=true"), ("serial1=disabled", "serial1=modem"),
                         ("nosound=true", "nosound=false"),
                         (f"captures={self.work}/cap", "captures=/tmp/elsewhere")):
            with self.subTest(new):
                self.assertTrue(self.problems(self.text.replace(old, new)), new)
        self.assertTrue(self.problems(self.text.replace("[cpu]", "[cpu]\nnew setting=1")))
        self.assertTrue(self.problems(self.text + "[dos]\nautomountall=true\n"))

    def test_the_command_line_may_name_only_its_configuration(self):
        good = ["dosbox-x", "-conf", str(self.work / "dosbox.conf"), "-nogui", "-nomenu", "-fastlaunch"]
        self.assertEqual(self.problems(self.text, good), [])
        for extra in (["-c", "mount d /"], ["-set", "dos automountall=true"], ["-conf", "/tmp/other.conf"],
                      [str(self.install)], ["-userconf"]):
            with self.subTest(extra):
                self.assertTrue(self.problems(self.text, good + extra))
        self.assertTrue(self.problems(self.text, ["sh", "-c", "dosbox-x"]))


class CycleWorld(World):
    def setUp(self):
        super().setUp()
        self.game = self.sync()
        self.work = self.tmp / "work"
        self.work.mkdir()

    def make(self, argv=()):
        args = cycle.parser().parse_args(list(argv))
        made = cycle.Cycle(args, "E003-r9001", self.run_dir, self.install, self.work, outer_netns="net:[1]")
        made.argv, made.fingerprint = list(argv), {}
        return made


class LaunchGateTest(CycleWorld):
    def launch(self, made):
        with mock.patch.object(cycle, "popen") as popen, redirect_stdout(io.StringIO()):
            with self.assertRaises(cycle.Abort):
                made.launch()
        return popen

    def test_a_good_run_copy_and_configuration_reach_the_launch(self):
        made = self.make()
        made.write_conf()
        with mock.patch.object(cycle, "popen", side_effect=RuntimeError("launched")) as popen, \
                redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
            made.launch()
        popen.assert_called_once()
        self.assertEqual(popen.call_args[0][0][:3], ["dosbox-x", "-conf", str(self.work / "dosbox.conf")])

    def test_a_configuration_that_mounts_anything_else_aborts_before_launch(self):
        for damage in (lambda t: t.replace("@echo off\n", "@echo off\nmount d /\n"),
                       lambda t: t.replace(f'"{self.game}"', f'"{self.install}"'),
                       lambda t: t.replace("automountall=false", "automountall=true")):
            with self.subTest():
                for name in os.listdir(self.work):
                    safeio.remove(self.work, name)
                made = self.make()
                made.write_conf()
                path = self.work / "dosbox.conf"
                text = damage(path.read_text())
                safeio.write_file(self.work, "dosbox.conf", data=text.encode(), exist="replace")
                popen = self.launch(made)
                popen.assert_not_called()
                self.assertTrue(made.status.startswith("aborted: the configuration may not be launched"), made.status)

    def test_a_run_copy_that_fails_check_strict_aborts_before_launch(self):
        made = self.make()
        made.write_conf()
        (self.game / "EXTRA.TXT").write_bytes(b"stray")
        popen = self.launch(made)
        popen.assert_not_called()
        self.assertIn("check --strict failed", made.status)
        self.assertTrue(made.status.startswith("aborted: the run copy is not safe to launch from"))

    def test_the_outer_process_starts_no_namespace_for_a_copy_that_fails(self):
        (self.game / "EXTRA.TXT").write_bytes(b"stray")
        with mock.patch.object(cycle, "run_namespace") as started:
            self.assertIn("nothing was started", self.refused(lambda: cycle.outer(cycle.parser().parse_args([]))))
        started.assert_not_called()
        self.game.joinpath("EXTRA.TXT").unlink()
        with mock.patch.object(cycle, "run_namespace", return_value=0) as started, \
                mock.patch.object(cycle, "run", return_value=mock.MagicMock(stdout=b"")):
            self.assertEqual(cycle.outer(cycle.parser().parse_args(["--explore"])), 0)
        started.assert_called_once()

    def test_dosbox_x_in_the_outer_network_namespace_aborts(self):
        made = self.make()
        made.outer_netns = cycle.netns_of("self")
        made.procs["game"] = mock.MagicMock(pid=os.getpid())
        with redirect_stdout(io.StringIO()), self.assertRaises(cycle.Abort):
            made.verify_isolation()
        self.assertIn("network namespace", made.status)

    def test_a_copy_that_stays_writable_aborts_before_anything(self):
        made = self.make()
        with mock.patch.object(cycle, "run", return_value=mock.MagicMock(returncode=0)), \
                mock.patch.object(cycle, "install_writable", return_value=True), \
                redirect_stdout(io.StringIO()), self.assertRaises(cycle.Abort):
            made.protect_install()
        self.assertIn("read-only", made.status)


class FakeGame:
    pid = 1

    def __init__(self):
        self.returncode = None

    def poll(self):
        return self.returncode

    def send_signal(self, _):
        self.returncode = 0

    def kill(self):
        self.returncode = -9

    def wait(self, *_):
        return self.returncode


class InnerTest(CycleWorld):
    """The real inner() and Cycle.execute(), with the display, the mounts and the game replaced."""

    def run_inner(self, capture):
        repo = self.tmp / "repo"
        (repo / "runs").mkdir(parents=True, exist_ok=True)

        def launch(self_):
            self_.check_launch("immediately before launch", 1)
            self_.procs["game"] = FakeGame()
            self_.t_launch = 0

        def input_stage(self_):
            self_.after_screen_ok = True

        env = {"IW_DOS_CYCLE_ID": "E003-r9001", "IW_DOS_CYCLE_REP": "1", "IW_DOS_CYCLE_COMMIT": "abcdef123456"}
        with contextlib.ExitStack() as stack:
            for name, value in (("start_x", lambda self_: None), ("known_screen", lambda self_: None),
                                ("launch", launch), ("input", input_stage)):
                stack.enter_context(mock.patch.object(cycle.Cycle, name, value))
            stack.enter_context(mock.patch.object(cycle.Screen, "capture", capture))
            stack.enter_context(mock.patch.object(cycle, "run", return_value=mock.MagicMock(returncode=0)))
            stack.enter_context(mock.patch.object(cycle, "install_writable", return_value=False))
            stack.enter_context(mock.patch.object(cycle, "ROOT", repo))
            stack.enter_context(mock.patch.object(cycle, "WORK", self.work))
            stack.enter_context(mock.patch.object(cycle, "versions", return_value={}))
            stack.enter_context(mock.patch.dict(os.environ, env))
            stack.enter_context(redirect_stdout(io.StringIO()))
            stack.enter_context(redirect_stderr(io.StringIO()))
            code = cycle.inner(cycle.parser().parse_args([]))
        record = json.loads((repo / "runs" / "E003" / "E003-r9001.json").read_text())
        return code, record

    def test_a_good_cycle_is_completed(self):
        def capture(self_, directory, name):
            safeio.write_file(directory, name, data=b"png", exist="new")
            return "a" * 64, "b" * 64, b""
        code, record = self.run_inner(capture)
        self.assertEqual((code, record["status"]), (0, "completed"))

    def test_a_capture_failure_records_aborted_and_exits_1(self):
        def capture(self_, directory, name):
            raise RuntimeError("capture is 0 bytes, not 640x350 RGB")
        code, record = self.run_inner(capture)
        self.assertEqual(code, 1)
        self.assertTrue(record["status"].startswith("aborted: RuntimeError: capture is 0 bytes"), record["status"])
        self.assertNotIn("before.png", [o["name"] for o in record["outputs"]])

    def test_a_cycle_without_its_screenshots_is_never_completed(self):
        made = self.make()
        made.after_screen_ok = True
        with redirect_stdout(io.StringIO()), self.assertRaises(cycle.Abort):
            made.complete()
        self.assertIn("without before.png and after.png", made.status)


class TokenTest(World):
    def test_the_lane_runs_its_own_and_the_shared_tokens_only(self):
        capabilities = json.loads((ROOT / "capabilities.json").read_text())
        selected = tokens.lane(capabilities)
        self.assertIn("artifact:iw-dos-3.1-30121376", selected)
        self.assertIn("tool:dosbox-x@2024.03.01", selected)
        self.assertIn("facility:iw-dos-run", selected)
        for token in ("tool:wine@9.0", "tool:xfwm4", "facility:iwp-prefix", "artifact:iwp-2.0-996e86c5"):
            self.assertNotIn(token, selected)

    def test_ready_only_when_every_lane_token_passes(self):
        path = self.tmp / "caps.json"
        good = {"tool:python@>=3.11": {"check": "true"}, "tool:xvfb": {"check": "true"},
                "tool:xdotool": {"check": "true"}, "facility:display": {"check": "true"},
                "facility:iw-dos-run": {"check": "true # setup/iw-dos/"}, "tool:wine@9.0": {"check": "false"}}
        path.write_text(json.dumps(good))
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(tokens.main(["tokens.py", str(path)]), 0)
        self.assertTrue(out.getvalue().strip().endswith("ready"))
        for change in ({"facility:iw-dos-run": {"check": "false # setup/iw-dos/"}},
                       {"facility:iw-dos-run": {"check": "true"}}, {"tool:xvfb": {"check": "false"}}):
            path.write_text(json.dumps({**good, **change}))
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(tokens.main(["tokens.py", str(path)]), 1)
            self.assertIn("not ready", out.getvalue())

    def test_the_run_token_needs_a_safe_run_copy(self):
        self.assertEqual(token_check.run_copy(), "the run directory is not a real directory")
        self.sync()
        self.assertIsNone(token_check.run_copy())
        (self.run_dir / "game" / "EXTRA.TXT").write_bytes(b"x")
        self.assertIn("check --strict", token_check.run_copy())

    def test_the_artifact_token_needs_the_registered_copy(self):
        self.assertIsNone(token_check.artifact())
        (self.install / "EXTRA.TXT").write_bytes(b"x")
        self.assertIn("does not match", token_check.artifact())

    def test_the_profile_is_not_ready_without_its_locations(self):
        env = {k: v for k, v in os.environ.items() if k not in ("IW_DOS_DIR", "IW_DOS_RUN")}
        done = subprocess.run(["bash", str(ROOT / "setup" / "iw-dos" / "iw-dos-runtime.sh")], env=env,
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(done.returncode, 1)
        self.assertNotIn("ready\n", done.stdout)
        self.assertIn("not ready", done.stderr)


if __name__ == "__main__":
    unittest.main()
