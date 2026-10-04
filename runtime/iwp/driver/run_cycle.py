#!/usr/bin/env python3
"""The E004 command: the 10-repeat cycle of the Isle Wars Pro driver. See runner.py for what it does."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from driver import runner  # noqa: E402

if __name__ == "__main__":
    sys.exit(runner.main())
