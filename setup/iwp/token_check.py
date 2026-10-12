#!/usr/bin/env python3
"""The checks behind the iwp tokens of capabilities.json: exit 0 = verified, 1 = unavailable.

Usage: token_check.py <python|wine|wine10|xvfb|xfwm4|xdotool|display|artifact|prefix>

These exist because the generic preflight (H3, game-archaeologist 07 §2) does not yet. When it
lands, the generic tokens (python, wine, xvfb, xfwm4, xdotool, display, artifact) move to it and
only `prefix` stays here. Nothing here prints an environment value or a local path.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SET_ID = "iwp-2.0-996e86c5"
WINE = "/usr/lib/wine/wine"
PROBE_TIMEOUT = 60


class ProbeTimeout(Exception):
    pass


def out(cmd, env=None):
    """(exit code, output) of a probe; a probe that outlives PROBE_TIMEOUT raises ProbeTimeout."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=PROBE_TIMEOUT, env=env)
    except subprocess.TimeoutExpired:
        raise ProbeTimeout(f"{Path(cmd[0]).name} did not answer within {PROBE_TIMEOUT} s") from None
    return result.returncode, (result.stdout + result.stderr).strip()


def need(binary):
    if shutil.which(binary) is None:
        return f"{binary} is not on PATH"
    return None


def python():
    return None if sys.version_info >= (3, 11) else f"python {sys.version_info[0]}.{sys.version_info[1]} is older than 3.11"


def wine_version(prefix_text):
    """None when `wine --version` at the packaged path starts with prefix_text, else a problem string."""
    if not Path(WINE).is_file():
        return "wine is not installed (apt: wine, wine32:i386)"
    try:
        code, text = out([WINE, "--version"])
    except ProbeTimeout as exc:
        return str(exc)
    if code != 0 or not text.startswith(prefix_text):
        return f"wine reports {text!r}, not {prefix_text[len('wine-'):]}"
    return None


def wine():
    return wine_version("wine-9.0")


def wine10():
    return wine_version("wine-10.0")


def xvfb():
    return need("Xvfb") or need("xdpyinfo") or need("import") or need("xprop")


def on_own_display(binary, args):
    """Run `binary args` against a throwaway Xvfb of its own, never the inherited DISPLAY (WSLg's :0
    accepts connections and never answers, so a probe on it hangs). None when it exits 0, else a
    problem string; a timeout is a problem string, never a traceback."""
    problem = need(binary) or need("Xvfb") or need("xdpyinfo")
    if problem:
        return problem
    sys.path.insert(0, str(ROOT / "setup" / "iwp"))
    import prefix as prefix_helpers
    try:
        proc, display = prefix_helpers.start_xvfb("64x64x16")
    except SystemExit as exc:
        return str(exc)
    try:
        try:
            code, _ = out([binary, *args], env={**os.environ, "DISPLAY": display})
        except ProbeTimeout as exc:
            return str(exc)
        return None if code == 0 else f"{binary} does not run"
    finally:
        proc.terminate()
        proc.wait(10)


def xfwm4():
    return on_own_display("xfwm4", ["--version"])


def xdotool():
    return on_own_display("xdotool", ["version"])


def display():
    """An X display can be served: a throwaway Xvfb answers xdpyinfo. The game never uses it."""
    problem = need("Xvfb") or need("xdpyinfo")
    if problem:
        return problem
    sys.path.insert(0, str(ROOT / "setup" / "iwp"))
    import prefix as prefix_helpers
    try:
        proc, _ = prefix_helpers.start_xvfb("64x64x16")
    except SystemExit as exc:
        return str(exc)
    proc.terminate()
    proc.wait(10)
    return None


def artifact():
    """The registered set is on this machine: the install (IWP_DIR) and/or the prefix's copy."""
    places = [p for p in (os.environ.get("IWP_DIR"),
                          os.environ.get("IWP_PREFIX") and str(Path(os.environ["IWP_PREFIX"]) / "drive_c" / "iwp")) if p]
    if not places:
        return "neither IWP_DIR nor IWP_PREFIX is set"
    for place in places:
        code, _ = out([sys.executable, str(ROOT / "tools" / "register_artifact.py"), "check", place, SET_ID,
                         "--known", str(ROOT / "artifacts" / "known.json")])
        if code != 0:
            return f"{SET_ID} does not match in one of the places given by the environment"
    return None


def prefix():
    if not os.environ.get("IWP_PREFIX"):
        return "IWP_PREFIX is not set"
    code, text = out([sys.executable, str(ROOT / "setup" / "iwp" / "prefix.py"), "check"])
    return None if code == 0 else text.replace("\n", "; ")


CHECKS = {"python": python, "wine": wine, "wine10": wine10, "xvfb": xvfb, "xfwm4": xfwm4, "xdotool": xdotool,
          "display": display, "artifact": artifact, "prefix": prefix}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in CHECKS:
        sys.exit(__doc__)
    problem = CHECKS[sys.argv[1]]()
    if problem:
        print(f"unavailable: {problem}")
        sys.exit(1)
    print("verified")
