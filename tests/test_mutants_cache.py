"""The bytecode-cache edge of tests/mutants_iwp_driver.py (T13 round 6, a flaky-SURVIVED diagnosis).

Python accepts a __pycache__ entry when the source's size and mtime (in whole seconds) match what
the entry records, so a file rewritten with the same size within the same mtime second keeps the
old entry valid and an importing subprocess runs the previous content. The mutants script rewrites
one source file per mutant, and two mutants of a file often have the same resulting size (the
round-5 `must(` -> `run(` groups differ by nothing else), so a kill-test subprocess could silently
test the previous mutant's code and report SURVIVED at random. mutants_iwp_driver.fresh_cache_python
gives every subprocess a throwaway cache (`-X pycache_prefix`); the test here visits the edge.
"""
import os
import sys
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mutants_iwp_driver  # noqa: E402


class FreshCacheTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="iwp-mutants-cache-test-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(self.dir, ignore_errors=True))
        self.module = self.dir / "m_cache_edge.py"

    def write(self, value):
        """(Re)write the module with `value` in CONSTANT, always the same file size."""
        text = f'CONSTANT = "{value}"\n'
        self.module.write_text(text)

    def test_a_same_size_rewrite_in_the_same_mtime_second_runs_the_old_code_by_default(self):
        self.write("A" * 8)
        now = int(time.time())
        os.utime(self.module, (now, now))
        plain = subprocess.run([sys.executable, "-c", "import m_cache_edge; print(m_cache_edge.CONSTANT)"],
                               cwd=self.dir, capture_output=True, text=True)
        self.assertEqual(plain.stdout.strip(), "A" * 8)
        self.write("B" * 8)                       # same size, other content
        os.utime(self.module, (now, now))         # and the same mtime second as the compiled entry
        plain = subprocess.run([sys.executable, "-c", "import m_cache_edge; print(m_cache_edge.CONSTANT)"],
                               cwd=self.dir, capture_output=True, text=True)
        self.assertEqual(plain.stdout.strip(), "A" * 8, "the stale __pycache__ entry wins: the edge exists")

    def test_the_mutants_runner_compiles_the_source_it_is_given_even_at_that_edge(self):
        self.write("A" * 8)
        now = int(time.time())
        os.utime(self.module, (now, now))
        plain = subprocess.run([sys.executable, "-c", "import m_cache_edge; print(m_cache_edge.CONSTANT)"],
                               cwd=self.dir, capture_output=True, text=True)   # primes the default __pycache__
        self.assertEqual(plain.stdout.strip(), "A" * 8)
        self.write("B" * 8)                       # same size, other content
        os.utime(self.module, (now, now))         # the same mtime second as the entry just compiled
        fresh = mutants_iwp_driver.fresh_cache_python(["-c", "import m_cache_edge; print(m_cache_edge.CONSTANT)"],
                                                      cwd=self.dir)
        self.assertEqual(fresh.stdout.strip(), "B" * 8,
                         "a throwaway cache: the subprocess must run the source it was given, not the"
                         " previous mutant's bytecode")


if __name__ == "__main__":
    unittest.main()
