"""The failures of the DOS Isle Wars driver, each with a name (T15, W5b).

Every way a repeat can fail raises one of these, and a repeat that hits one is recorded
`aborted: <kind>: <reason>`. A failure that has no class here is a bug of the driver: it is still
recorded `aborted`, as `driver-bug`, never `completed`.

Each class is also the spike's `Abort` (runtime/iw-dos/spike/cycle.py), so a step verb of the spike that
stops with `fail()` stops the driver's step the same way.
"""
import importlib.util
import sys
from pathlib import Path

_SPIKE = Path(__file__).resolve().parents[1] / "spike" / "cycle.py"


def _spike():
    """The DOS spike, loaded once under a name of its own (`iw_dos_spike_cycle`): the Pro spike is also a module
    called `cycle`, and a plain `import cycle` could find that one."""
    name = "iw_dos_spike_cycle"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, _SPIKE)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


spike = _spike()


class DriverError(spike.Abort):
    """Base of every failure the driver reports. `kind` is the word the record carries."""
    kind = "driver-bug"


class SealError(DriverError):
    """A check of the seal failed (IW_DOS_DIR not read-only, the run copy not safe or not at its baseline, the
    configuration, the network namespace, a DOSBox-X already running). Nothing is launched after it."""
    kind = "seal"


class CommandFailed(DriverError):
    """A command the driver relies on exited non-zero, did not start, or ran past its bound (procs.must)."""
    kind = "command-failed"


class DisplayError(DriverError):
    """This run's Xvfb did not come up, or the display is not held by it."""
    kind = "display"


class DisplayDied(DriverError):
    """This run's Xvfb was gone, or no longer held its display, while the session still needed it."""
    kind = "display-died"


class LaunchError(DriverError):
    """DOSBox-X did not start, showed no window, or its network isolation could not be verified."""
    kind = "launch"


class ScreenNotReached(DriverError):
    """A named screen did not appear (by its pixels) within its bound, or did not become still."""
    kind = "screen-not-reached"


class GameDied(DriverError):
    """DOSBox-X was gone while the session still needed it (killed, closed, crashed), or it ended otherwise than
    by the driver's own SIGTERM."""
    kind = "game-died"


class StepFailed(DriverError):
    """A step did not do what it must: refused by the grammar, no change on the screen, the wrong screen; or the
    session did not show what `completed` needs."""
    kind = "step-failed"


class TerminateError(DriverError):
    """DOSBox-X or Xvfb did not stop within its bound, or a process of the run survived."""
    kind = "terminate"


class ResetError(DriverError):
    """The reset did not put the run copy back to its baseline."""
    kind = "reset"


class RecordError(DriverError):
    """An output or the record could not be stored; the record never names what the store lacks."""
    kind = "record"


class FaultNotInjected(DriverError):
    """A fault the command was asked to inject (--fault) did not end DOSBox-X: the repeat is not the fault it should
    be, and the command fails."""
    kind = "fault-not-injected"
