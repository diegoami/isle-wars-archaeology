"""E020's batch loop: games and turns of place-all and pass, composed from the blocks of
play.steps and sent through the click-driver (runtime/iwp/driver/clicks.py), so through the session
(T38 round 2, R10, R11, R13, R14).

A game is: `new-game` (New Game, EASY, Play Game; sent from the title only, T41),
the computers' turns (`quiet`, repeated until the board is quiet), then turns of `place` (the human
selects a country it owns, read from the screen: the placement row only lights for one) and
`commit` (ALL, PLACE, PASS, CONTINUE), each followed by the computers' turns again. When no
country can be selected, `dismiss` clears a prompt and the placement is tried once more; when it
still fails on the board with its menu row lit, the loop stops the sitting cleanly (below). The loop
stops at the batch's `games_max`, or its `sitting_seconds`; a step that fails (a `click!` the screen
did not answer, a dead game) ends the sitting through the session's error, after its line is logged.

A sitting never quits a live game (T41, the owner, 2026-10-08): there is no turn limit. A game runs
until the human is eliminated (KEEP PLAYING, then the winner notice) or a computer wins, and when
`sitting_seconds` runs out in the middle of one the sitting ends through the session with no click.
The deadline is rechecked at the one door every input goes through (`send`, T41 round 1): the loop
sleeps or waits in several places (the play-out poll, the `quiet` waits, a screen read), and the time
may run out in any of them, so no block that sends input starts after the deadline, whatever
came before it. `quiet` sends nothing and is the only block not sent through `send`.
T38's third sitting (20261008T204817Z) sent New Game from the board of a live game at its 30-turn
cap with the human holding fewer than 10 countries: the game credited a loss, wrote its scoreboard
file (F003) and showed the Scoreboard, and the blind setup clicks after it missed. So New Game is
sent only on the title screen, never on a board.

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
* after a placement block reports `picked`, before its commit (fix #141, round 2): the winner
  notice may have come up under the block -- its CONTINUE blinks between a green and a grey phase,
  and the block's own grey test can fire on the phase the reader's grey test misses -- then no
  commit is sent, and `off_board` answers the screen;
* the winner notice (`game-over`, T38 round 6, measured from sitting 20261008T195537Z; its CONTINUE
  blinks green and grey, and either phase names it, fix #141 round 2), read in the play-out or at a
  turn's start, ends the game: its `game-end` line says `ended: game-over` and
  names the winner's colour when the score panel shows it by pixels (`winner`, a colour word or
  null; never OCR). The loop then clicks CONTINUE once (block `game-over-continue`) and reads the
  screen: the next game starts only on the title or the board with its menu row (the screens New
  Game is proven on); anything else ends the sitting as an unknown screen. What follows CONTINUE is
  not assumed;
* the Scoreboard (`scoreboard`, T41, measured from sitting 20261008T204817Z): the game shows it after
  it credits a loss. Wherever the loop reads it (after the winner notice's CONTINUE, at a turn's start,
  in the play-out) it logs `event: loss-credited` (the scoreboard file is written, so the artifact set
  is the successor from then on, and the export refuses a record that names the shipped set for a game
  after it), clicks its CONTINUE once (block `scoreboard-continue`) and reads the screen: the next game
  starts only on the title; anything else ends the sitting cleanly;
* New Game is sent only on a screen read as the title, never on a board;
* any screen the loop does not recognise where it would act (not the board at a turn's start, not
  the title before New Game, not the board or the winner notice while the computers play out), and a
  placement that failed on the board with its menu row lit, end the sitting cleanly: a last
  screenshot through the session, an `ended: unknown-screen` (or `placement-refused`) line with its
  sha256, no click, and the session's own finish.

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
NEW_GAME_ON = ("title",)  # New Game is sent here only (T41): from a board it quits a live game and credits a loss (F003)
WAIT_ON = BOARD + ("eliminated", "game-over", "scoreboard")   # screens a readiness wait keeps waiting on
                                                # (round 5, R1; the winner notice, round 6, and the
                                                # Scoreboard, T41: answered at the turn's start)
PLAYOUT_POLL = 5          # s between screen readings while the computers play out; no input is sent
FINAL_FRAME = "unknown-screen.png"


class TimeUp(Exception):
    """`sitting_seconds` ran out before an input block: caught by `run`, which ends the sitting cleanly."""


class BatchLoop:
    def __init__(self, driver, batch, clock=time.monotonic, sleep=time.sleep):
        self.driver = driver
        self.games_max = int(batch["games_max"])
        self.seconds = float(batch["sitting_seconds"])
        self.clock = clock
        self.sleep = sleep
        self.summary = {"games": 0, "turns": 0, "placements": 0, "ended": None}
        self.game_over_seen = None           # {"ended": "game-over", "winner": ...} once the winner notice is read
        self.scoreboard_seen = False         # the Scoreboard was read in the game's own turns or play-out
        self.game_open = False               # a game-start line was written and its game-end line was not

    def out_of_time(self):
        return self.clock() >= self.deadline

    def send(self, name):
        """Run one block that sends input, unless the time ran out first (T41 round 1): the deadline is
        rechecked here, at the door of every input, so a sleep or a wait before it cannot let a click
        through. TimeUp ends the sitting in `run`, with no click."""
        self.check_time(name)
        return self.driver.run_block(name)

    def check_time(self, what):
        if self.out_of_time():
            raise TimeUp(what)

    def end_game(self, reason, **fields):
        self.driver.note(event="game-end", reason=reason, **fields)
        self.game_open = False

    def run(self):
        """Play games until the bounds; the summary (games, turns, placements, why it ended). The time
        running out before an input ends the sitting there, unclicked, and says so (`sitting-seconds`)."""
        self.deadline = self.clock() + self.seconds
        try:
            return self.games()
        except TimeUp:
            if self.game_open:
                self.end_game("sitting-seconds")
            self.summary["ended"] = "sitting-seconds"
            return self.summary

    def games(self):
        after_notice = None                          # the screen read after a notice's CONTINUE (the title)
        for game in range(1, self.games_max + 1):
            if self.out_of_time():
                self.summary["ended"] = "sitting-seconds"
                return self.summary
            self.driver.context = {"game": game, "turn": 0}
            screen = after_notice if after_notice is not None else self.driver.read_screen()
            after_notice = None
            if screen not in NEW_GAME_ON:            # New Game only on the title, never on a board
                self.unknown_screen(screen)
                return self.summary
            self.check_time("game-start")           # no game is logged as started that New Game cannot start
            self.driver.note(event="game-start")
            self.game_open = True
            self.summary["games"] = game
            self.send("new-game")
            self.game_over_seen, self.scoreboard_seen = None, False
            reason = self.play_game()
            if self.game_over_seen is not None:     # the winner notice (round 6)
                self.end_game(reason, **self.game_over_seen)
                after_notice = self.continue_after_game_over()
            elif self.scoreboard_seen:              # the game credited a loss (T41)
                self.end_game(reason)
                after_notice = self.leave_scoreboard()
            else:
                self.end_game(reason)
                if self.summary["ended"] is None:   # never a next game from a game that is not over
                    self.summary["ended"] = reason
                return self.summary
            if after_notice is None:
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
        on it (the title); the Scoreboard is left as `leave_scoreboard` does; otherwise the sitting ends
        as an unknown screen, unclicked, and None."""
        self.send("game-over-continue")
        screen = self.driver.read_screen()
        if screen == "scoreboard":
            return self.leave_scoreboard()
        if screen in NEW_GAME_ON:
            return screen
        self.unknown_screen(screen)
        return None

    def leave_scoreboard(self):
        """The Scoreboard is up: the game credited a loss and wrote its scoreboard file. The line
        `loss-credited` first (the artifact set is the successor from here on), then CONTINUE once
        (block `scoreboard-continue`), then the screen: returned when it is the title; anything else
        ends the sitting as an unknown screen, unclicked, and None."""
        self.summary["loss_credited"] = self.summary.get("loss_credited", 0) + 1
        self.driver.note(event="loss-credited")
        self.send("scoreboard-continue")
        screen = self.driver.read_screen()
        if screen in NEW_GAME_ON:
            return screen
        self.unknown_screen(screen)
        return None

    def play_game(self):
        """Turns, with no limit (T41), until the human cannot place (the sitting stops, unclicked), the
        time runs out (the sitting stops, unclicked, with the game still live), the elimination notice
        (then the play-out), the winner notice, the Scoreboard or a screen the loop does not recognise.
        The reason the game ended for the loop."""
        if not self.wait_quiet():
            return "unknown-screen"
        turn = 0
        while True:
            if self.out_of_time():
                self.summary["ended"] = "sitting-seconds"
                return "sitting-seconds"
            turn += 1
            self.driver.context = dict(self.driver.context, turn=turn)
            ended = self.turn()
            if ended:
                return ended
            if not self.wait_quiet():
                return "unknown-screen"

    def turn(self):
        """One human turn, the screen read before each placement attempt; None when the turn was
        played, else why the game ended for the loop. A placement whose re-read (fix #141 round 2)
        found the board gone returns the reason `off_board` answered with, and the game ends there."""
        screen = self.driver.read_screen()
        if screen not in BOARD:
            return self.off_board(screen)
        placed = self.place()
        if placed is True:
            return None
        if placed is not False:         # the game ended while the placement block ran (fix #141 r2)
            return placed
        self.send("dismiss")
        if not self.wait_quiet():
            return "unknown-screen"
        screen = self.driver.read_screen()
        if screen not in BOARD:
            return self.off_board(screen)
        placed = self.place()
        if placed is True:
            return None
        if placed is not False:         # as above, at the second attempt
            return placed
        screen = self.driver.read_screen()
        if screen == "board-menu":                  # a live game the human cannot place in: stop, never New Game
            self.unknown_screen(screen, ended="placement-refused")
            return "placement-refused"
        return self.off_board(screen)

    def place(self):
        """The human selects a country it owns (the placement row lit) and commits; True when one
        was, False when the block picked nothing, else the reason the game ended: after the block
        reports `picked` the screen is read again before the commit (fix #141, round 2, defence in
        depth): sitting 20261009T160556Z (E020-r0008) had the winner notice up while the block ran
        -- its green phase read as the board, its grey phase lit the block's own test -- and the ALL
        click changed nothing, aborting the sitting. A screen that is not the board here is answered
        by `off_board` instead: no commit is sent, and its reason goes back to `turn`."""
        if not self.send("place").get("picked"):
            return False
        screen = self.driver.read_screen()
        if screen not in BOARD:
            return self.off_board(screen)
        self.summary["placements"] += 1
        self.send("commit")
        self.summary["turns"] += 1
        return True

    def off_board(self, screen):
        """Not the screen the turn needs: the elimination notice is answered (keep playing); anything
        else ends the sitting, unclicked. The winner notice ends the game (round 6), and so does the
        Scoreboard (T41): `run` leaves it."""
        if screen == "eliminated":
            return self.keep_playing()
        if screen == "game-over":
            return self.game_over()
        if screen == "scoreboard":
            return self.scoreboard()
        self.unknown_screen(screen)
        return "unknown-screen"

    def scoreboard(self):
        """The Scoreboard ended the game (the game credited a loss); `run` logs the end and leaves it."""
        self.scoreboard_seen = True
        return "scoreboard"

    def keep_playing(self):
        """KEEP PLAYING once; then no input, only screen readings while the board stays up, in the time.
        The winner notice ends the game (round 6), and so does the Scoreboard (T41); any other screen
        ends the sitting, unclicked."""
        self.send("eliminated-keep-playing")
        self.summary["eliminated"] = True
        while True:
            if self.out_of_time():
                self.summary["ended"] = "sitting-seconds"
                return "played-out: sitting-seconds"
            self.sleep(PLAYOUT_POLL)
            screen = self.driver.read_screen()
            if screen == "game-over":
                return "played-out: " + self.game_over()
            if screen == "scoreboard":
                return "played-out: " + self.scoreboard()
            if screen not in BOARD:
                self.unknown_screen(screen)
                return "played-out: unknown-screen"

    def unknown_screen(self, screen, ended="unknown-screen"):
        """End the sitting cleanly: a last screenshot, its sha256 logged, no click."""
        digest = self.driver.final_frame(FINAL_FRAME)
        self.summary.update(ended=ended, screen=screen, final_frame=digest)
        self.driver.note(event="ended", ended=ended, screen=screen, sha256=digest)

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
