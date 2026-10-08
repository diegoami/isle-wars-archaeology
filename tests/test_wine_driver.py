"""Load T38's wine-driver tool tests so CI's `unittest discover -s tests` runs them.

The tests live beside the tools they cover (tools/tests/, the path docs/tasks/T38.md names); this
module loads them unchanged, exactly as tests/test_check_no_originals.py loads T36's.
"""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

for _name in ("test_watcher", "test_clicks", "test_check_counts", "test_wine_tools"):
    _spec = importlib.util.spec_from_file_location(f"t38_{_name}", ROOT / "tools" / "tests" / f"{_name}.py")
    _module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_module)
    globals().update({k: v for k, v in vars(_module).items()
                      if isinstance(v, type) and issubclass(v, unittest.TestCase)})


if __name__ == "__main__":
    unittest.main()
