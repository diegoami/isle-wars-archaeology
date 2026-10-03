"""Synthetic fixtures for the safety tests of the iwp-runtime profile and the E001 cycle.

Every test builds its own install, prefix and checkout in a temporary directory outside any
checkout. None reads or writes the real install (IWP_DIR) or the real prefix: the environment
variables are replaced for the duration of each test and the registered manifest is replaced by a
synthetic one. `prefix` here is the very module the cycle imports, so that replacement holds for
the cycle's seal and reset too.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "setup" / "iwp"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


import locations  # noqa: E402
import prefix  # noqa: E402  (the module the cycle imports as prefixlib)
import safeio  # noqa: E402

token_check = load("iwp_token_check", "setup/iwp/token_check.py")
tokens = load("iwp_tokens", "setup/iwp/tokens.py")
cycle = load("iwp_cycle_safety", "runtime/iwp/spike/cycle.py")
assert cycle.prefixlib is prefix and cycle.safeio is safeio

FILES = {"a.txt": b"alpha", "xtras/b.dat": b"beta"}
UNLISTED = {"unlisted.bin": b"keep me", "unins000.exe": b"uninstaller"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


MANIFEST = {
    "schema": "artifact-set/1", "id": "synthetic-1.0-00000000", "title": "synthetic", "version": "1.0",
    "files": [{"path": p, "bytes": len(d), "sha256": sha(d)} for p, d in sorted(FILES.items())],
    "runtime_writes": [],
}


def tree(base):
    """{relative path: (kind, size or target, sha256)} of everything under base, links not followed."""
    out = {}
    for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
        for name in dirnames + filenames:
            path = Path(dirpath) / name
            rel = path.relative_to(base).as_posix()
            if path.is_symlink():
                out[rel] = ("l", os.readlink(path), "")
            elif path.is_dir():
                out[rel] = ("d", "", "")
            else:
                out[rel] = ("f", path.stat().st_size, sha(path.read_bytes()))
    return out


def inodes(base):
    """{relative path: (st_nlink, st_mode)} of every regular file under base."""
    out = {}
    for dirpath, _, filenames in os.walk(base, followlinks=False):
        for name in filenames:
            info = os.lstat(Path(dirpath) / name)
            out[(Path(dirpath) / name).relative_to(base).as_posix()] = (info.st_nlink, info.st_mode)
    return out


class World(unittest.TestCase):
    """A synthetic install, a synthetic prefix, and a synthetic checkout, all in one temp dir."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(os.path.realpath(self._tmp.name))
        if locations.checkout_of(self.tmp) is not None:
            self.skipTest("the temporary directory is inside a checkout (TMPDIR?); these safety tests need one "
                          "outside every checkout, because the code under test refuses locations inside one")
        self.install = self.tmp / "install"
        for rel, data in {**FILES, **UNLISTED}.items():
            self.write(self.install / rel, data)
        self.prefix = self.tmp / "prefix"
        (self.prefix / "drive_c" / "users" / "u").mkdir(parents=True)
        (self.prefix / "dosdevices").mkdir()
        (self.prefix / "system.reg").write_text("reg")
        os.symlink("../drive_c", self.prefix / "dosdevices" / "c:")
        self.checkout = self.tmp / "checkout"
        (self.checkout / ".git").mkdir(parents=True)
        self.bundles = self.tmp / "bundles"
        patcher = mock.patch.dict(os.environ, {"IWP_PREFIX": str(self.prefix), "IWP_DIR": str(self.install),
                                               "E001_BUNDLES": str(self.bundles)})
        patcher.start()
        self.addCleanup(patcher.stop)
        for name in ("E001_EXPLORE", "E001_MACHINE"):
            os.environ.pop(name, None)
        manifest = mock.patch.object(prefix, "manifest", return_value=MANIFEST)
        manifest.start()
        self.addCleanup(manifest.stop)

    @staticmethod
    def write(path, data):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def game_copy(self, files=None):
        game = self.prefix / "drive_c" / "iwp"
        game.mkdir(parents=True, exist_ok=True)
        for rel, data in (FILES if files is None else files).items():
            self.write(game / rel, data)
        return game

    def call(self, function):
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            return function(), out.getvalue()

    def refused(self, function):
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            function()
        return str(caught.exception.code), out.getvalue()


class InnerHarness(World):
    """The real inner() and Cycle.execute(): every gate, the status, the reset and the writes run.

    Only what needs a display or the game is replaced: Xvfb, xfwm4, the game process and its
    screens, terminate, the mounts (cycle.run), and the read-only check of the install."""

    def setUp(self):
        super().setUp()
        self.repo = self.tmp / "repo"
        (self.repo / "runs").mkdir(parents=True)
        self.calls = []
        self.counter = 0

    def run_cycle(self, argv=(), launch=None, shot=None, install_writable=False, env=None, stages=None,
                  raw=b"\x10" * (800 * 600 * 3), options_up=True):
        """(exit code, or the SystemExit raised; the record, or None).

        launch(cycle) runs where the game would start (after the real seal); shot replaces the
        screenshot stage; stages maps a stage name to a replacement; raw is what every screen
        capture returns, options_up whether the Options screen is seen."""
        self.counter += 1
        explore = "--explore" in argv
        run_id = f"E001-x{self.counter}" if explore else f"E001-r{9000 + self.counter}"
        calls = self.calls

        def noop(name):
            def stage(self_, *a, **k):
                calls.append(name)
            return stage

        def input_stage(self_):
            calls.append("input")
            self_.after_screen_ok = True

        def launch_stage(self_):
            self_.seal("immediately before launch", 1)       # the real seal, as in Cycle.launch
            calls.append("launch")
            if launch:
                launch(self_)

        def shot_stage(self_, name, step):
            self_.screen.capture(self_.workdir, name)
            self_.outputs.append((name, self_.workdir / name, "screenshot"))

        stage_map = {name: noop(name) for name in ("start_x", "start_wm", "known_screen", "terminate", "stop_x")}
        stage_map.update(launch=launch_stage, input=input_stage, shot=shot or shot_stage)
        stage_map.update(stages or {})
        values = {"IWP_CYCLE_ID": run_id, "IWP_CYCLE_REP": "1", "IWP_CYCLE_COMMIT": "abcdef123456",
                  "E001_EXPLORE": str(self.tmp / "explore"), **(env or {})}
        args = cycle.parser().parse_args(list(argv))
        with contextlib.ExitStack() as stack:
            for name, replacement in stage_map.items():
                stack.enter_context(mock.patch.object(cycle.Cycle, name, replacement))
            stack.enter_context(mock.patch.object(cycle.Screen, "options_up", return_value=options_up))
            stack.enter_context(mock.patch.object(cycle.Screen, "raw", return_value=raw))
            stack.enter_context(mock.patch.object(cycle, "install_writable", return_value=install_writable))
            stack.enter_context(mock.patch.dict(os.environ, values))
            stack.enter_context(mock.patch.object(cycle, "run", return_value=mock.MagicMock(returncode=0)))
            stack.enter_context(mock.patch.object(cycle, "ROOT", self.repo))
            stack.enter_context(mock.patch.object(cycle, "versions", return_value={}))
            stack.enter_context(redirect_stdout(io.StringIO()))
            stack.enter_context(redirect_stderr(io.StringIO()))
            try:
                code = cycle.inner(args)
            except SystemExit as exc:
                code = exc
            except BaseException as exc:        # an interruption that escaped inner() is a failure, not a stop
                self.fail(f"{type(exc).__name__} escaped inner(): the run would leave no record")
        path = self.repo / "runs" / "E001" / f"{run_id}.json"
        return code, (json.loads(path.read_text()) if path.exists() and not path.is_symlink() else None)
