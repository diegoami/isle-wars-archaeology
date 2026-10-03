#!/usr/bin/env python3
"""Run every token check of capabilities.json; print `ready` and exit 0 only if all of them pass.

Usage: tokens.py [capabilities.json]

Each token's `check` is a shell command (exit 0 = verified). One line per token is printed, then
either `ready` (exit 0) or `not ready: <the failing tokens>` (exit 1). A capabilities file with no
token, an unreadable one, or an entry without a check is not ready: silence is not success.

TODO(H3): when game-archaeologist's generic preflight exists (07 §2) this becomes
`preflight --tokens <the tokens of capabilities.json>`; the exit code is still never trusted on its
own (ADR-004).
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_tokens(capabilities, cwd=ROOT):
    """(lines, failed) for a {token: {"check": command}} mapping; commands run with bash in cwd."""
    lines, failed = [], []
    if not isinstance(capabilities, dict) or not capabilities:
        return ["no token to check"], ["capabilities.json holds no token"]
    for token, entry in capabilities.items():
        check = entry.get("check") if isinstance(entry, dict) else None
        if not isinstance(check, str) or not check.strip():
            lines.append(f"{token}: no check command")
            failed.append(token)
            continue
        try:
            result = subprocess.run(["bash", "-c", check], cwd=cwd, capture_output=True, text=True, timeout=300)
            ok, text = result.returncode == 0, (result.stdout + result.stderr).strip()
        except (OSError, subprocess.TimeoutExpired) as exc:
            ok, text = False, f"check could not run: {type(exc).__name__}"
        lines.append(f"{token}: {text}")
        if not ok:
            failed.append(token)
    return lines, failed


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else ROOT / "capabilities.json"
    try:
        capabilities = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print(f"not ready: {path.name} cannot be read")
        return 1
    lines, failed = run_tokens(capabilities)
    print("\n".join(lines))
    if failed:
        print("not ready: " + " ".join(failed))
        return 1
    print("ready")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
