"""Tests for the WINEARCH eviction of issue #212 / PR #213 round 2 (Sol's R2).

fix #212 moved the Wine launch from i386 wine + WINEARCH=win32 to wine64 + wow64. Both
`prefix.wine_env()` and `spike.cycle.Cycle.__init__` copy `os.environ`, so a parent environment
carrying `WINEARCH=win32` would leak it into the wow64 launch unless it is evicted explicitly.
These tests set WINEARCH in the environment (patched, restored afterwards — the real env is
never mutated permanently) and assert neither env carries it. Rule 9: each test fails when the
`pop("WINEARCH", None)` line it guards is removed (checked via a saved-copy mutation).
"""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "setup" / "iwp"))
sys.path.insert(0, str(ROOT / "runtime" / "iwp" / "spike"))

import cycle  # noqa: E402
import prefix as prefixlib  # noqa: E402


def _env_without_winearch():
    """A patch.dict context whose environment simply lacks WINEARCH (the no-leak control)."""
    return mock.patch.dict(
        os.environ,
        {k: v for k, v in os.environ.items() if k != "WINEARCH"},
        clear=True,
    )


class WineEnvWinearchTest(unittest.TestCase):
    """`prefix.wine_env` builds its env from os.environ; an inherited WINEARCH must be evicted."""

    def test_wine_env_evicts_an_inherited_winearch(self):
        with mock.patch.dict(os.environ, {"WINEARCH": "win32"}):
            env = prefixlib.wine_env(Path("/tmp/iwp-prefix-test"))
        self.assertNotIn("WINEARCH", env)

    def test_wine_env_without_winearch_in_parent_stays_without_it(self):
        with _env_without_winearch():
            env = prefixlib.wine_env(Path("/tmp/iwp-prefix-test"))
        self.assertNotIn("WINEARCH", env)


class CycleEnvWinearchTest(unittest.TestCase):
    """`Cycle.__init__` builds self.env from os.environ; an inherited WINEARCH must be evicted
    there too — this is the env the game's wine process is launched with."""

    def _make_cycle(self):
        args = SimpleNamespace(size="800x600x32", audio="on")
        cyc = cycle.Cycle(args, "test-winearch", Path(tempfile.mkdtemp(prefix="iwp-prefix-test-")), [])
        self.addCleanup(shutil.rmtree, cyc.workdir, True)
        return cyc

    def test_cycle_env_evicts_an_inherited_winearch(self):
        with mock.patch.dict(os.environ, {"WINEARCH": "win32"}):
            cyc = self._make_cycle()
        self.assertNotIn("WINEARCH", cyc.env)

    def test_cycle_env_without_winearch_in_parent_stays_without_it(self):
        with _env_without_winearch():
            cyc = self._make_cycle()
        self.assertNotIn("WINEARCH", cyc.env)


if __name__ == "__main__":
    unittest.main()
