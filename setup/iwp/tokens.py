#!/usr/bin/env python3
"""Run the token checks of capabilities.json; print `ready` and exit 0 only if all of them pass.

Usage: tokens.py [--tokens <name>[,<name>...]] [capabilities.json]

Each token's `check` is a shell command (exit 0 = verified). One line per token is printed, then
either `ready` (exit 0) or `not ready: <the failing tokens>` (exit 1). A capabilities file with no
token, an unreadable one, or an entry without a check is not ready: silence is not success.

`--tokens` runs only the named tokens, in the order given (iwp-runtime.sh passes the Pro lane's).
A named token the file lacks is a failure (`<name>: not in capabilities.json`), never skipped, and
an empty list is not ready. With no `--tokens` every token of the file is run, as before.

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


def select(capabilities, names):
    """(mapping, lines, failed) restricted to names, in the order given. A name the file lacks is
    a failure (`<name>: not in capabilities.json`), never skipped."""
    lines, failed, selected = [], [], {}
    for name in names:
        if isinstance(capabilities, dict) and name in capabilities:
            selected[name] = capabilities[name]
        else:
            lines.append(f"{name}: not in capabilities.json")
            failed.append(name)
    return selected, lines, failed


def parse_argv(argv):
    """(path, names): `--tokens` takes a comma-separated list, any other argument is the
    capabilities path. names is None when `--tokens` is absent, so every token runs."""
    path, names = None, None
    i = 0
    while i < len(argv):
        if argv[i] == "--tokens":
            if i + 1 >= len(argv):
                raise ValueError("--tokens needs a comma-separated list of token names")
            names = [name for name in argv[i + 1].split(",") if name]
            i += 2
        else:
            path = Path(argv[i])
            i += 1
    return path, names


def main(argv):
    try:
        path, names = parse_argv(argv[1:])
    except ValueError as exc:
        print(f"not ready: {exc}")
        return 1
    path = path or ROOT / "capabilities.json"
    try:
        capabilities = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print(f"not ready: {path.name} cannot be read")
        return 1
    if names is None:
        lines, failed = run_tokens(capabilities)
    else:
        selected, sel_lines, sel_failed = select(capabilities, names)
        if selected:
            more_lines, more_failed = run_tokens(selected)
        elif sel_failed:                   # every named token was missing: they are named above
            more_lines, more_failed = [], []
        else:                              # nothing selected: an empty list is not ready
            more_lines, more_failed = ["no token to check"], ["no token was selected"]
        lines, failed = sel_lines + more_lines, sel_failed + more_failed
    print("\n".join(lines))
    if failed:
        print("not ready: " + " ".join(failed))
        return 1
    print("ready")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
