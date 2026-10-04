#!/usr/bin/env python3
"""Run the iw-dos lane's token checks of capabilities.json; print `ready` and exit 0 only if all
of them pass.

Usage: tokens.py [capabilities.json]

The lane's tokens are those whose check lives in setup/iw-dos/ (the iw-dos tokens), and the shared
tokens the lane needs (SHARED: T11's "Runs on"). The Wine lane's tokens (wine, xfwm4, the prefix,
its set) are not run here: they need IWP_DIR and IWP_PREFIX, which this lane does not set. The
running and the verdict are setup/iwp/tokens.py's `run_tokens`, imported as it is: one line per
token, then `ready` or `not ready: <the failing tokens>`. No selected token is not ready.
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHARED = ("tool:python@>=3.11", "tool:xvfb", "tool:xdotool", "facility:display")
OWN = "setup/iw-dos/"


def shared_tokens():
    spec = importlib.util.spec_from_file_location("iwp_tokens_shared", ROOT / "setup" / "iwp" / "tokens.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lane(capabilities):
    """The lane's tokens of a {token: {"check": command}} mapping, in their order there."""
    if not isinstance(capabilities, dict):
        return {}
    return {token: entry for token, entry in capabilities.items()
            if token in SHARED or (isinstance(entry, dict) and OWN in str(entry.get("check", "")))}


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else ROOT / "capabilities.json"
    try:
        capabilities = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print(f"not ready: {path.name} cannot be read")
        return 1
    selected = lane(capabilities)
    missing = [token for token in SHARED if token not in selected]
    if not any(OWN in str(entry.get("check", "")) for entry in selected.values() if isinstance(entry, dict)):
        missing.append("(no iw-dos token)")
    lines, failed = shared_tokens().run_tokens(selected)
    print("\n".join(lines))
    failed += missing
    if failed:
        print("not ready: " + " ".join(failed))
        return 1
    print("ready")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
