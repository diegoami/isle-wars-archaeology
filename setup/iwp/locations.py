"""Confinement of the machine-local locations of the iwp-runtime profile and the E001 cycle.

The prefix, its baseline, the evidence bundles and the exploration output are machine-local: CLAUDE.md
rule 18 and T08's hazards keep them out of every checkout and worktree, and the install (IWP_DIR) is
read only. Every entry point calls `confine` before it mutates or launches anything.

A location is accepted when its canonical path (symlinks resolved)
- is absolute,
- is not inside a checkout or worktree (an ancestor, the path included, holds a `.git` entry),
- does not contain this repository (so `$HOME` is not a prefix),
- does not overlap the install, nor any other location handed in (neither contains the other).
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def real(path):
    return Path(os.path.realpath(path))


def inside(child, parent):
    """True when child is parent or lies under it (both canonical)."""
    child, parent = Path(child), Path(parent)
    return child == parent or parent in child.parents


def checkout_of(path):
    """The nearest ancestor of a canonical path that holds a `.git` entry, or None."""
    path = Path(path)
    for candidate in (path, *path.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def confine(name, value, others=()):
    """The canonical Path of one machine-local location, or SystemExit saying why it is refused.

    `others` are (name, canonical path) pairs the location must not overlap.
    """
    if not value:
        raise SystemExit(f"{name} is not set")
    if not os.path.isabs(str(value)):
        raise SystemExit(f"{name} must be an absolute path")
    path = real(value)
    if path == Path(path.anchor):
        raise SystemExit(f"{name} must not be the filesystem root")
    checkout = checkout_of(path)
    if checkout is not None:
        raise SystemExit(f"{name} is inside a checkout or worktree; machine-local locations live outside every one")
    if inside(path, real(ROOT)):
        raise SystemExit(f"{name} is inside this repository; machine-local locations live outside every checkout")
    if inside(real(ROOT), path):
        raise SystemExit(f"{name} contains this repository; machine-local locations live outside every checkout")
    for other_name, other in others:
        if inside(path, other) or inside(other, path):
            raise SystemExit(f"{name} overlaps {other_name}")
    return path


def locations(env=None, need_prefix=False, need_bundles=False, explore=False):
    """Confine every machine-local location named in the environment; returns {name: Path}.

    IWP_DIR (the install) is confined for overlap only: it is not a checkout location, but no
    other location may contain it or lie inside it. Prefix, baseline, bundles and exploration
    output must not overlap one another either.
    """
    env = os.environ if env is None else env
    found = {}
    install = None
    if env.get("IWP_DIR"):
        if not os.path.isabs(env["IWP_DIR"]):
            raise SystemExit("IWP_DIR must be an absolute path")
        install = real(env["IWP_DIR"])
        found["IWP_DIR"] = install
    seen = [("IWP_DIR", install)] if install else []

    def add(name, value, required):
        if not value:
            if required:
                raise SystemExit(f"{name} is not set")
            return
        found[name] = confine(name, value, seen)
        seen.append((name, found[name]))

    add("IWP_PREFIX", env.get("IWP_PREFIX"), need_prefix)
    if "IWP_PREFIX" in found:
        add("IWP_PREFIX.baseline", str(found["IWP_PREFIX"]) + ".baseline", False)
    add("E001_BUNDLES", env.get("E001_BUNDLES"), need_bundles)
    if explore:
        add("E001_EXPLORE", env.get("E001_EXPLORE"), False)
    return found
