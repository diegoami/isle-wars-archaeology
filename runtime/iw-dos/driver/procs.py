"""Commands and processes of the DOS Isle Wars driver: the one helper every command goes through, and the one
place a signal is sent from (T15; T13's review, PR #54, classes A and B).

- `must(cmd)` runs every command the driver relies on, with a bound, and raises CommandFailed unless it exited 0.
  `xdotool search` that finds nothing exits 1 with nothing on stdout or stderr: `must(..., miss_ok=True)` returns
  None for exactly that, and raises for any other non-zero exit.
- `kill_marked(pid, items, sig)` sends a signal only to a process that still carries every one of `items` in its
  environment, checked again through a pidfd, so a pid reused by another process is never signalled.
- Every process of a driver command carries `IW_DOS_DRIVER_INVOCATION=<token>` (one token per command,
  repeat.outer); every process of a repeat also `IW_DOS_DRIVER_RUN=<run id>` and a side (`game`, `display`).
  Another session's processes (#32: other projects run DOSBox-X and Xvfb here, and T11's spike marks its own with
  IW_DOS_CYCLE_RUN) carry none of these exact entries and are never signalled.
"""
import os
import re
import secrets
import signal
import subprocess
from pathlib import Path

from driver.errors import CommandFailed

INVOCATION = "IW_DOS_DRIVER_INVOCATION"
MARK = "IW_DOS_DRIVER_RUN"
SIDE = "IW_DOS_DRIVER_SIDE"
SIDES = ("game", "display")
COMMAND = "IW_DOS_DRIVER_COMMAND"   # one token per helper command (must)
REAP_S = 5                  # s, for a command killed at its bound to be reaped
COMMAND_BOUND = 30          # s, any one helper command (a capture takes about 0.05 s; `git` and `mount` less than 1 s)


def must(cmd, env=None, cwd=None, timeout=COMMAND_BOUND, miss_ok=False):
    """The CompletedProcess of `cmd` (stdout and stderr as bytes), which must exit 0 within `timeout` s;
    CommandFailed otherwise. With miss_ok, exit 1 with empty stdout and stderr returns None (a search that
    found nothing).

    The command carries a marker of its own, IW_DOS_DRIVER_COMMAND=<token>; past its bound it is sent SIGKILL
    through kill_marked with that marker, never by subprocess's own kill (T15 round 1, R4)."""
    marker = secrets.token_hex(8)
    full = dict(os.environ if env is None else env, **{COMMAND: marker})
    try:
        proc = subprocess.Popen(cmd, env=full, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as exc:
        raise CommandFailed(f"{cmd[0]} could not be started: {type(exc).__name__}") from None
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        kill_marked(proc.pid, [item(COMMAND, marker)], signal.SIGKILL)
        try:
            proc.communicate(timeout=REAP_S)
        except subprocess.TimeoutExpired:
            raise CommandFailed(f"{cmd[0]} ran past its bound of {timeout} s and survived SIGKILL") from None
        raise CommandFailed(f"{cmd[0]} ran past its bound of {timeout} s") from None
    done = subprocess.CompletedProcess(cmd, proc.returncode, out, err)
    if miss_ok and done.returncode == 1 and not done.stdout.strip() and not done.stderr.strip():
        return None
    if done.returncode != 0:
        tail = (done.stderr or done.stdout).decode(errors="replace").strip().splitlines()[-1:] or [""]
        raise CommandFailed(f"{' '.join(map(str, cmd[:2]))} exited {done.returncode}: {tail[0][:200]}")
    return done


def start(cmd, env, **kw):
    """Every long-lived child (Xvfb, DOSBox-X) starts here; `env` must carry the invocation and run markers."""
    if not all(env.get(name) for name in (INVOCATION, MARK, SIDE)):
        raise ValueError("a child of the driver must carry the invocation marker, the run marker and a side")
    return subprocess.Popen(cmd, env=env, **kw)


def environ_has(pid, items):
    """True when every one of `items` (b"NAME=value") is a whole entry of the environment of pid. A zombie (its
    memory gone) has an empty environment, so it never has them."""
    try:
        env = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
    except OSError:
        return False
    return bool(items) and all(item in env for item in items)


def kill_marked(pid, items, sig=signal.SIGKILL):
    """Send `sig` to pid only if it still carries every one of `items`, checked through a pidfd that is opened first:
    a pid that ended and was reused between the check and the signal is not the process the pidfd refers to, and
    the signal fails rather than reach it. True when sent. Every signal the driver sends goes through here."""
    if not items:
        raise ValueError("kill_marked needs the markers the process must carry")
    try:
        fd = os.pidfd_open(pid)
    except OSError:
        return False
    try:
        if not environ_has(pid, items):
            return False
        signal.pidfd_send_signal(fd, sig)
        return True
    except OSError:
        return False
    finally:
        os.close(fd)


def marked_pids(items):
    """pids (not this process) whose environment holds every one of `items`, read from /proc."""
    if not items:
        raise ValueError("marked_pids needs the markers; it never lists every process")
    return sorted(int(e.name) for e in Path("/proc").iterdir()
                  if e.name.isdigit() and int(e.name) != os.getpid() and environ_has(e.name, items))


def pids_carrying(name):
    """pids (not this process) whose environment has an entry `name=<anything>`: any driver command's, for the
    check that refuses to start while one is alive (it never signals them)."""
    prefix = f"{name}=".encode()
    found = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            env = (entry / "environ").read_bytes().split(b"\0")
        except OSError:
            continue
        if any(e.startswith(prefix) for e in env):
            found.append(int(entry.name))
    return sorted(found)


def item(name, value):
    return f"{name}={value}".encode()


def listening_socket_inodes(path):
    """Inodes of the listening unix sockets bound to `path` ("@..." for an abstract one), from /proc/net/unix,
    which shows the sockets of this process's network namespace only."""
    found = set()
    for line in Path("/proc/net/unix").read_text(errors="replace").splitlines()[1:]:
        fields = line.split()
        if len(fields) >= 8 and fields[7] == path and int(fields[3], 16) & 0x10000:   # __SO_ACCEPTCON: listening
            found.add(int(fields[6]))
    return found


def socket_inodes_of(pid):
    """Inodes of the sockets process pid holds open, from /proc/<pid>/fd."""
    found = set()
    try:
        entries = list(Path(f"/proc/{pid}/fd").iterdir())
    except OSError:
        return found
    for entry in entries:
        try:
            match = re.fullmatch(r"socket:\[(\d+)\]", os.readlink(entry))
        except OSError:
            continue
        if match:
            found.add(int(match.group(1)))
    return found


def program_pids(name):
    """pids whose command name (/proc/<pid>/comm) is `name`: inside the command's PID namespace, only its own."""
    found = []
    for entry in Path("/proc").iterdir():
        if entry.name.isdigit():
            try:
                if (entry / "comm").read_text().strip() == name:
                    found.append(int(entry.name))
            except OSError:
                continue
    return sorted(found)
