"""E020's batch loop: games and turns of place-all and pass, composed from the blocks of
play.steps and sent through the click-driver (runtime/iwp/driver/clicks.py), so through the session
(T38 round 2, R10, R11, R13, R14).

A game is: `new-game` (New Game, EASY, Play Game; from the title or mid-game at EASY, E002-r0018),
the computers' turns (`quiet`, repeated until the board is quiet), then turns of `place` (the human
selects a country it owns, read from the screen: the placement row only lights for one) and
`commit` (ALL, PLACE, PASS, CONTINUE), each followed by the computers' turns again. When no
country can be selected, `dismiss` clears a prompt and the placement is tried once more; when it
still fails on the board with its menu row lit, the game is over for the human, and the next game
starts. The loop stops at the batch's `games_max`, or its `sitting_seconds`; a step that fails (a
`click!` the screen did not answer, a dead game) ends the sitting through the session's error,
after its line is logged.

Readiness is never assumed (T38 round 3, R1): when `QUIET_ATTEMPTS` `quiet` blocks pass without a
quiet board, the loop sends nothing more. It marks its summary `ended: aborted: not-ready: ...` and
raises the click-driver's `NotReady`, which ends the session with the status `aborted: not-ready:
<reason>` (Session.execute keeps the reason); the summary is never a normal one. After each `quiet`
block that was not quiet, the screen is read before the next (T38 round 5, R1): only the board, with
or without its menu, or the elimination notice is waited on; any other screen ends the sitting as an
unknown screen (below), so a screen that never settles is not mistaken for a busy board.

The screen is read by pixels, never assumed (T38 round 4; runtime/iwp/driver/screens.py, measured
from the frames of sitting 20261008T184505Z):

* at the start of every human turn, before the placement (and again before the second placement
  attempt): on the elimination notice the loop sends the `eliminated-keep-playing` block once (the
  owner's decision: the computers play the game out), then sends nothing more. It reads the screen
  every `PLAYOUT_POLL` seconds while the board stays up, bounded by the batch's `sitting_seconds`;
* the winner notice (`game-over`, T38 round 6, measured from sitting 20261008T195537Z), read in the
  play-out or at a turn's start, ends the game: its `game-end` line says `ended: game-over` and
  names the winner's colour when the score panel shows it by pixels (`winner`, a colour word or
  null; never OCR). The loop then clicks CONTINUE once (block `game-over-continue`) and reads the
  screen: the next game starts only on the title or the board with its menu row (the screens New
  Game is proven on); anything else ends the sitting as an unknown screen. What follows CONTINUE is
  not assumed;
* New Game is sent only on a screen read as the title or as the board with its menu row lit;
* any screen the loop does not recognise where it would act (not the board at a turn's start, not
  the board with its menu after a placement failed, not the title or that board before New Game,
  not the board or the winner notice while the computers play out) ends the sitting cleanly: a last
  screenshot through the session, an `ended: unknown-screen` line with its sha256, no click, and the
  session's own finish.

Every game start and end is a line of `actions.jsonl` (`event: game-start` / `game-end`, with
the game ordinal and the reason), which is how the export knows the sitting's real games; every
screen reading is a line too (`event: screen`).

The events (exchanges, bomb plays) are read from the frames after the sitting, so the loop cannot
stop on a live count: a sitting that ends short is recorded as it is, and tools/check_counts.py
prints the shortfall.
"""
import time

from driver.clicks import NotReady

QUIET_ATTEMPTS = 6        # `quiet` blocks before a turn is given up: 6 x (4 s + the spike's bound of 38 s);
                          # F003 measured 15 to 33 s for the computers' turns
BOARD = ("board", "board-menu")
NEW_GAME_ON = ("title", "board-menu")   # New Game is on these screens (the menu row lit; E002-r0018/r0019)
WAIT_ON = BOARD + ("eliminated", "game-over")   # screens a readiness wait keeps waiting on (round 5, R1;
                                                # the winner notice, round 6: answered at the turn's start)
PLAYOUT_POLL = 5          # s between screen readings while the computers play out; no input is sent
FINAL_FRAME = "unknown-screen.png"


class BatchLoop:
    def __init__(self, driver, batch, clock=time.monotonic, sleep=time.sleep):
        self.driver = driver
        self.games_max = int(batch["games_max"])
        self.turns_max = int(batch["turns_max"])
        self.seconds = float(batch["sitting_seconds"])
        self.clock = clock
        self.sleep = sleep
        self.summary = {"games": 0, "turns": 0, "placements": 0, "ended": None}
        self.game_over_seen = None           # {"ended": "game-over", "winner": ...} once the winner notice is read

    def out_of_time(self):
        return self.clock() >= self.deadline

    def run(self):
        """Play games until the bounds; the summary (games, turns, placements, why it ended)."""
        self.deadline = self.clock() + self.seconds
        after_continue = None                        # the screen read after a winner notice's CONTINUE
        for game in range(1, self.games_max + 1):
            if self.out_of_time():
                self.summary["ended"] = "sitting-seconds"
                return self.summary
            self.driver.context = {"game": game, "turn": 0}
            screen = after_continue if after_continue is not None else self.driver.read_screen()
            after_continue = None
            if screen not in NEW_GAME_ON:            # New Game only where it is proven on the screen
                self.unknown_screen(screen)
                return self.summary
            self.driver.note(event="game-start")
            self.summary["games"] = game
            self.driver.run_block("new-game")
            self.game_over_seen = None
            reason = self.play_game()
            if self.game_over_seen is not None:     # the winner notice (round 6)
                self.driver.note(event="game-end", reason=reason, **self.game_over_seen)
                after_continue = self.continue_after_game_over()
                if after_continue is None:
                    return self.summary
                continue
            self.driver.note(event="game-end", reason=reason)
            if self.summary["ended"] is not None:    # the time, the play-out or an unknown screen
                return self.summary
        self.summary["ended"] = "games-max"
        return self.summary

    def game_over(self):
        """The winner notice is up: the game is over. Its winner is read by pixels (None when the
        score panel does not show one); the game-end line is written by `run`, then CONTINUE."""
        self.game_over_seen = {"ended": "game-over", "winner": self.driver.read_winner()}
        return "game-over"

    def continue_after_game_over(self):
        """CONTINUE once (block `game-over-continue`), then the screen: returned when New Game is proven
        on it (the title, or the board with its menu row); otherwise the sitting ends as an unknown
        screen, unclicked, and None."""
        self.driver.run_block("game-over-continue")
        screen = self.driver.read_screen()
        if screen in NEW_GAME_ON:
            return screen
        self.unknown_screen(screen)
        return None

    def play_game(self):
        """Turns until the human cannot place, `turns_max`, the time, the elimination notice (then the
        play-out) or a screen the loop does not recognise. The reason the game ended for the loop."""
        if not self.wait_quiet():
            return "unknown-screen"
        for turn in range(1, self.turns_max + 1):
            if self.out_of_time():
                self.summary["ended"] = "sitting-seconds"
                return "sitting-seconds"
            self.driver.context = dict(self.driver.context, turn=turn)
            ended = self.turn()
            if ended:
                return ended
            if not self.wait_quiet():
                return "unknown-screen"
        return "turns-max"

    def turn(self):
        """One human turn, the screen read before each placement attempt; None when the turn was
        played, else why the game ended for the loop."""
        screen = self.driver.read_screen()
        if screen not in BOARD:
            return self.off_board(screen)
        if self.place():
            return None
        self.driver.run_block("dismiss")
        if not self.wait_quiet():
            return "unknown-screen"
        screen = self.driver.read_screen()
        if screen not in BOARD:
            return self.off_board(screen)
        if self.place():
            return None
        screen = self.driver.read_screen()
        if screen == "board-menu":
            return "placement-refused"
        return self.off_board(screen)

    def place(self):
        """The human selects a country it owns (the placement row lit) and commits; True when one was."""
        if not self.driver.run_block("place").get("picked"):
            return False
        self.summary["placements"] += 1
        self.driver.run_block("commit")
        self.summary["turns"] += 1
        return True

    def off_board(self, screen):
        """Not the screen the turn needs: the elimination notice is answered (keep playing); anything
        else ends the sitting, unclicked. The winner notice ends the game (round 6)."""
        if screen == "eliminated":
            return self.keep_playing()
        if screen == "game-over":
            return self.game_over()
        self.unknown_screen(screen)
        return "unknown-screen"

    def keep_playing(self):
        """KEEP PLAYING once; then no input, only screen readings while the board stays up, in the time.
        The winner notice ends the game (round 6); any other screen ends the sitting, unclicked."""
        self.driver.run_block("eliminated-keep-playing")
        self.summary["eliminated"] = True
        while True:
            if self.out_of_time():
                self.summary["ended"] = "sitting-seconds"
                return "played-out: sitting-seconds"
            self.sleep(PLAYOUT_POLL)
            screen = self.driver.read_screen()
            if screen == "game-over":
                return "played-out: " + self.game_over()
            if screen not in BOARD:
                self.unknown_screen(screen)
                return "played-out: unknown-screen"

    def unknown_screen(self, screen):
        """End the sitting cleanly: a last screenshot, its sha256 logged, no click."""
        digest = self.driver.final_frame(FINAL_FRAME)
        self.summary.update(ended="unknown-screen", screen=screen, final_frame=digest)
        self.driver.note(event="ended", ended="unknown-screen", screen=screen, sha256=digest)

    def wait_quiet(self):
        """`quiet` until the board was unchanged for its time, at most QUIET_ATTEMPTS times; True when
        it was. A `quiet` block sends no input. After a block that was not quiet the screen is read
        before the next one (T38 round 5, R1): a screen that is neither the board nor the elimination
        notice ends the sitting as an unknown screen (its final frame, no click), and the wait is
        False. NotReady, after the summary says so, when a known screen never went quiet: no further
        input is sent (round 3, R1)."""
        for _ in range(QUIET_ATTEMPTS):
            try:
                if self.driver.run_block("quiet").get("quiet"):
                    return True
            except NotReady:
                pass
            screen = self.driver.read_screen()
            if screen not in WAIT_ON:
                self.unknown_screen(screen)
                return False
        where = ", ".join(f"{k} {v}" for k, v in sorted(self.driver.context.items()))
        reason = f"the board was not quiet after {QUIET_ATTEMPTS} quiet blocks ({where})"
        self.summary["ended"] = f"aborted: {NotReady.kind}: {reason}"
        raise NotReady(reason)
