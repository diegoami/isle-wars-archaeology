"""The failures of the Isle Wars Pro driver, each with a name.

Every way a repeat can fail raises one of these, and a repeat that hits one is recorded
`aborted: <kind>: <reason>`. A failure that has no class here is a bug in the driver: it is still
recorded `aborted`, as `driver-bug`, never `completed`.
"""


class DriverError(RuntimeError):
    """Base of every failure the driver reports. `kind` is the word the record carries."""
    kind = "driver-bug"


class SealError(DriverError):
    """The install is not read-only here, or the prefix is not safe to launch from (T08's seal), or it
    is not at its baseline. Nothing was started."""
    kind = "seal"


class DisplayError(DriverError):
    """Xvfb or the window manager did not come up."""
    kind = "display"


class LaunchError(DriverError):
    """The game did not start, showed no window, or its network isolation could not be verified."""
    kind = "launch"


class ScreenNotReached(DriverError):
    """A named screen did not appear (by its pixels) within its time."""
    kind = "screen-not-reached"


class GameDied(DriverError):
    """The game process was gone while the cycle still needed it (killed, crashed or quit)."""
    kind = "game-died"


class StepFailed(DriverError):
    """A step or the input did not do what it must: refused, no change on the screen, wrong screen."""
    kind = "step-failed"


class TerminateError(DriverError):
    """A process of the run survived terminate, even after the bounded wait and a kill."""
    kind = "terminate"


class ResetError(DriverError):
    """The reset did not put the prefix back to its state before the launch."""
    kind = "reset"


class RecordError(DriverError):
    """An output or the record could not be stored; the record never names what the store lacks."""
    kind = "record"
