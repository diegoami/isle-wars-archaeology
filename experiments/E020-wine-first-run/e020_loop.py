"""E020's batch loop: games and turns of place-all and pass, composed from the blocks of
play.steps and sent through the click-driver (runtime/iwp/driver/clicks.py), so through the session
(T38 round 2, R10, R11, R13, R14).

A game is: `new-game` (New Game, EASY, Play Game; from the title or mid-game at EASY, E002-r0018),
the computers' turns (`quiet`, repeated until the board is quiet), then turns of `place` (the human
selects a country it owns, read from the screen: the placement row only lights for one) and
`commit` (ALL, PLACE, PASS, CONTINUE), each followed by the computers' turns again. When no
country can be selected, `dismiss` clears a prompt and the placement is tried once more; when it
still fails, the game is over for the human, and the next game starts. The loop stops at the
batch's `games_max`, or its `sitting_seconds`; a step that fails (a `click!` the screen did not
answer, a dead game) ends the sitting through the session's error, after its line is logged.

Every game start and end is a line of `actions.jsonl` (`event: game-start` / `game-end`, with
the game ordinal and the reason), which is how the export knows the sitting's real games.

The events (exchanges, bomb plays) are read from the frames after the sitting, so the loop cannot
stop on a live count: a sitting that ends short is recorded as it is, and tools/check_counts.py
prints the shortfall.
"""
import time

QUIET_ATTEMPTS = 6        # `quiet` blocks before a turn is given up: 6 x (4 s + the spike's bound of 38 s);
                          # F003 measured 15 to 33 s for the computers' turns


class BatchLoop:
    def __init__(self, driver, batch, clock=time.monotonic):
        self.driver = driver
        self.games_max = int(batch["games_max"])
        self.turns_max = int(batch["turns_max"])
        self.seconds = float(batch["sitting_seconds"])
        self.clock = clock
        self.summary = {"games": 0, "turns": 0, "placements": 0, "ended": None}

    def out_of_time(self):
        return self.clock() >= self.deadline

    def run(self):
        """Play games until the bounds; the summary (games, turns, placements, why it ended)."""
        self.deadline = self.clock() + self.seconds
        for game in range(1, self.games_max + 1):
            if self.out_of_time():
                self.summary["ended"] = "sitting-seconds"
                return self.summary
            self.driver.context = {"game": game, "turn": 0}
            self.driver.note(event="game-start")
            self.summary["games"] = game
            self.driver.run_block("new-game")
            reason = self.play_game()
            self.driver.note(event="game-end", reason=reason)
            if reason == "sitting-seconds":
                self.summary["ended"] = reason
                return self.summary
        self.summary["ended"] = "games-max"
        return self.summary

    def play_game(self):
        """Turns until the human cannot place, `turns_max`, or the time. The reason it ended."""
        self.wait_quiet()
        for turn in range(1, self.turns_max + 1):
            if self.out_of_time():
                return "sitting-seconds"
            self.driver.context = dict(self.driver.context, turn=turn)
            if not self.place():
                return "placement-refused"
            self.driver.run_block("commit")
            self.summary["turns"] += 1
            self.wait_quiet()
        return "turns-max"

    def place(self):
        """The human selects a country it owns (the placement row lit); True when one was."""
        if self.driver.run_block("place").get("picked"):
            self.summary["placements"] += 1
            return True
        self.driver.run_block("dismiss")
        self.wait_quiet()
        if self.driver.run_block("place").get("picked"):
            self.summary["placements"] += 1
            return True
        return False

    def wait_quiet(self):
        """`quiet` until the board was unchanged for its time, at most QUIET_ATTEMPTS times."""
        for _ in range(QUIET_ATTEMPTS):
            if self.driver.run_block("quiet").get("quiet"):
                return True
        return False
