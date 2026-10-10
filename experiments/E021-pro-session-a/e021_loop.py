"""E021's Session A loop: the driver plays the human seat and attacks on purpose (T45).

It is E020's batch loop with the human's turn replaced (imported and subclassed, never edited:
`experiments/E020-wine-first-run/e020_loop.py` keeps the game structure -- New Game from the title
only (T41, F003), the computers' `quiet` waits, the elimination notice, the winner notice, the
Scoreboard, the shipped scoreboard restore (fix #152), the deadline at the door of every input,
and the clean end on a screen the loop does not recognise). What this module adds is the turn:

  read the board by pixels (boardview.FrameReader: one live capture through the session, decoded
  by E020's reader) -> choose the case still needed that this board can attempt (cases.py) ->
  grow the frontier country (all reinforcements on it, `place-commit`) -> attack: select the
  attacker, open the target phase, name the target, confirm the attacker (the battle is on when
  the quit-attack button shows), then one exchange click (F011 Q-CMB-08: one click is one
  exchange) -> read the board after every click -> leave with the quit-attack button (or DONE
  after a capture) -> attack again while a needed case has a pair the game has not refused ->
  PASS when nothing fits.

Every attempt is a line of `actions.jsonl` (`event: attack-attempt` with the aim, the counters
before and after, the frames and the outcome; `event: case-met` when a cell of the 40 is met --
the export turns both into the record's observations, and the progress counter reads those).
Structural values only (constraint D): case and cell words are ours, counters are numbers, frames
are sha256s; no text of the original is ever written.

Hazards the task file names, and how they are held here:
* New Game is sent only on the title: inherited from E020's `games()` (never written again here);
* a case that does not appear on the deal is left unmet and recorded as such (the picker answers
  None and the turn passes); a board is never forced;
* the game may refuse an attack (the target panel does not change, the quit-attack button never
  shows): the pair is cancelled for the rest of the turn (`refused`) and the attempt is logged
  `refused`, never retried blind;
* a failed attack ends the turn by itself (Q-CMB-09, about 90%): the forfeit is read from the
  board (the attacking country changes hands, or is left at 1 army), the `lost` row is marked and
  the loop sends nothing more that turn;
* a board read with any country unread ends the sitting cleanly (`board-unreadable`): the player
  never plans on a board it cannot see.
"""
import time

import e020_loop  # noqa: E402  (E020's loop, imported read-only)
import exchange_events  # noqa: E402  (E020's reader: the committed adjacency, T21's tabulation)
import cases  # noqa: E402
import points as points_module  # noqa: E402
from driver import clicks  # noqa: E402  (the click-driver; on sys.path as the launcher puts it)
import steps as stepslib  # noqa: E402  (the E002 step language, on sys.path via driver.clicks)

# The bottom-bar controls the attack flow uses (walkthroughs/coordinates.md, E002's tour.steps;
# the spike's own ATTACK_BUTTON and CANCEL_BUTTON are 303,530 and 405,530 for its hover-and-click
# helper -- the tour and E019's walks click 337,531 for one exchange, and that is the point here).
ATTACK_BUTTON = (337, 531)
CANCEL_BUTTON = (405, 530)
QUIT_ATTACK_STEP = "click-until? 0 192 64 16 600 456 531 495 540"   # QUIT ATTACK, then DONE (the tour)
CENTRE_WATCH = "watch 262 502 276 70"                               # the phase panel of the tour
RESULT_WATCH = "watch 545 502 250 70"                               # the battle result row of the tour
PLACE_WATCH = "watch 265 530 270 26"                               # the placement row (E020's place)
PLACE_SELECT = "click-until? 168 168 168 24 1000 {x} {y}"           # E020's own placement test
EXCHANGE_CLICK = "click {x} {y}".format(x=ATTACK_BUTTON[0], y=ATTACK_BUTTON[1])
BUSY_MINIMUM = 3                    # a `busy` turn: at least 3 attacks (Q-CMB-10)
MAX_ATTACKS_PER_TURN = 12           # a safety bound, never a rule of the game
READY_SECONDS = 3.0                 # bound on the battle-ready poll after the confirm click
CHANGE_SECONDS = 3.0                # bound on the board-change poll after an exchange click


class SessionALoop(e020_loop.BatchLoop):
    """One Session A sitting: E020's games and screens, this task's turns and attacks."""

    def __init__(self, driver, batch, clock=time.monotonic, sleep=time.sleep, restore=None,
                 shipped_skr=None, reader=None, adjacency=None, points=None, met=()):
        """`reader` is the live view (boardview.FrameReader or a test's stand-in) with `read()`,
        `wait_ready(seconds)` and `wait_change(board, countries, seconds)`; `adjacency` is
        {country: set of neighbours} (E015's tabulation when absent); `points` is the clickable
        countries (walkthroughs/coordinates.md); `met` is the cells already met, usually read from
        the latest measurements/progress-r<nn>.json so a resumed batch starts where it stopped."""
        super().__init__(driver, batch, clock=clock, sleep=sleep, restore=restore, shipped_skr=shipped_skr)
        if reader is None:
            raise ValueError("the Session A loop needs a live board reader")
        self.reader = reader
        self.adjacency = exchange_events.load_adjacency() if adjacency is None else adjacency
        self.points = points_module.click_points() if points is None else points
        self.met = {tuple(pair) for pair in met}
        self.refused = set()                # (attacker, defender) the game refused this turn
        self.summary.update(attack_attempts=0, attack_clicks=0, cases_met=len(self.met),
                            exchanges=0)

    # --- the case table -------------------------------------------------------------------------

    def needed(self):
        """The (case, cell) pairs this sitting still works on."""
        return cases.needed_cells(self.met)

    def note_case(self, case, cell, **fields):
        """Mark a cell met and log it: the export's source for the record's `case:kind` groups,
        and what keeps the picker off a cell the sitting already has. False when it was met."""
        if (case, cell) in self.met:
            return False
        self.met.add((case, cell))
        self.summary["cases_met"] = len(self.met)
        self.driver.note(event="case-met", case=case, cell=cell, **fields)
        return True

    # --- the door every input goes through ------------------------------------------------------

    def send_step(self, block, text):
        """One synthesised step of the attack flow, through the click-driver (so through the
        session's display and accounting, T38 round 2), behind the deadline like every other
        input (T41 round 1)."""
        self.check_time(block)
        step = stepslib.parse_line(text)
        if step is None:
            raise ValueError(f"an empty step in block {block!r}")
        if step.op not in clicks.ALLOWED:
            raise ValueError(f"{step.op} is not a click-driver step; the driver sends only "
                             f"{', '.join(sorted(clicks.ALLOWED))}")
        return self.driver.run_step(block, step)

    # --- the board ------------------------------------------------------------------------------

    def read_board(self, strict=True):
        """(board, png sha256) of one live capture. Strict (the turn's own reads): an unread
        country ends the sitting cleanly, `board-unreadable`, and the loop sends nothing more.
        Not strict (a read inside an attack flow): the reason is logged and the flow continues on
        the last board it had; the caller decides what an unread frame means."""
        try:
            board, digest, _rgb = self.reader.read()
        except Exception as exc:                       # no templates file, an undecodable capture
            return self.unreadable(f"{type(exc).__name__}: {exc}", strict=strict)
        if board is None:
            return self.unreadable("a country of the board was unread", strict=strict)
        return board, digest

    def unreadable(self, reason, strict=True):
        """(None, None), with the sitting ended when strict: a last frame and the reason, no
        click (the unknown-screen discipline of E020's loop)."""
        self.driver.note(event="board-unread", reason=reason[:120])
        if strict:
            self.unknown_screen(self.driver.read_screen(), ended=f"board-unreadable: {reason[:120]}")
        return None, None

    # --- one human turn -------------------------------------------------------------------------

    def turn(self):
        """One turn of placement and attacks; None when it was played, else why the game ended
        for the loop. Two placement attempts with a `dismiss` between them, as E020's turn does;
        then the attack phase, then PASS -- unless a failed attack ended the turn by itself
        (Q-CMB-09), when the loop sends nothing more and the computers' turns follow."""
        screen = self.driver.read_screen()
        if screen not in e020_loop.BOARD:
            return self.off_board(screen)
        board, _digest = self.read_board()
        if board is None:
            return "board-unreadable"
        self.refused = set()
        for attempt in (1, 2):
            placed = self.place_for(board)
            if placed is True:
                return self.after_placement()
            if placed is not False:                    # the game ended while the block ran
                return placed
            if attempt == 1:
                self.send("dismiss")
                if not self.wait_quiet():
                    return "unknown-screen"
                screen = self.driver.read_screen()
                if screen not in e020_loop.BOARD:
                    return self.off_board(screen)
                board, _digest = self.read_board()
                if board is None:
                    return "board-unreadable"
        screen = self.driver.read_screen()
        if screen == "board-menu":                     # a live game the human cannot place in
            self.unknown_screen(screen, ended="placement-refused")
            return "placement-refused"
        return self.off_board(screen)

    def after_placement(self):
        """The attack phase, then PASS; the reason the game ended when a failure ended the turn."""
        board, _digest = self.read_board()
        if board is None:
            return "board-unreadable"
        ended = self.attack_phase(board)
        if ended == "forfeit":
            return None
        if ended is not None:
            return ended
        self.send("pass")
        return None

    def place_for(self, board):
        """Grow the frontier country: pick it (cases.frontier), select it on the board (the
        placement row lights only for a country the human owns -- the tour's own test, one
        candidate), then `place-commit` (ALL, PLACE). True when it ran, False when no country
        could be selected, else why the game ended."""
        choice = cases.frontier(board, self.needed(), self.adjacency, points=self.points)
        if choice is None:
            return False
        attacker, _defender, case, cell, gap = choice
        fields = {"event": "place-target", "country:attacker": attacker, "counter:gap": gap}
        if case is not None:
            fields.update({"aim:case": case, "aim:cell": cell})
        self.driver.note(**fields)
        x, y = self.points[attacker]
        self.send_step("place-select", PLACE_WATCH)
        outcome = self.send_step("place-select", PLACE_SELECT.format(x=x, y=y))
        if not outcome.get("picked"):
            return False
        screen = self.driver.read_screen()
        if screen not in e020_loop.BOARD:              # fix #141 round 2, as E020's place()
            return self.off_board(screen)
        self.summary["placements"] += 1
        self.send("place-commit")
        self.summary["turns"] += 1
        return True

    # --- the attack phase -----------------------------------------------------------------------

    def attack_phase(self, board):
        """Attack while a still-needed cell has a pair the game has not refused this turn.
        "forfeit" when a failure ended the turn (the loop then sends nothing more), and
        "board-unreadable" when a read inside an attack was unusable; else None (PASS follows)."""
        attacks = 0
        attempts = 0
        while attempts < MAX_ATTACKS_PER_TURN:
            choice = cases.pick(board, self.needed(), self.adjacency, points=self.points,
                                exclude=self.refused)
            if choice is None:
                break
            case, cell, attacker, defender = choice
            outcome, board = self.attack_once(board, case, cell, attacker, defender)
            attempts += 1
            if outcome in ("quit", "capture", "exchange", "forfeit"):
                attacks += 1
            self.summary["attack_attempts"] += 1
            if outcome == "forfeit":
                self.note_turn(attacks, ended="forfeit")
                return "forfeit"
            if outcome == "unread":
                self.note_turn(attacks, ended="board-unreadable")
                return "board-unreadable"
            if board is None:
                break
        self.note_turn(attacks)
        return None

    def note_turn(self, attacks, **fields):
        """The turn's attack count, and the busy cell when the turn had enough attacks
        (Q-CMB-10: a turn with three or more attacks is one observation of the row)."""
        self.driver.note(event="turn-end", attacks=attacks, **fields)
        if attacks >= BUSY_MINIMUM:
            cell = cases.next_outcome_cell(self.needed(), "busy")
            if cell is not None:
                self.note_case("busy", cell, counter=attacks)

    def aim_met(self, case, outcome):
        """Whether a resolved attack meets the cell it was aimed at. Every resolution of a size
        case is its observation (the case was attempted at those sizes and the game's answer was
        read); the `lost` row counts only a failure (Q-CMB-09); the quit row is marked by the
        quit-attack press itself and the busy row by the turn's attack count."""
        if case in cases.SIZE_CASES:
            return True
        return case == "lost" and outcome == "forfeit"

    def attack_once(self, board, case, cell, attacker, defender):
        """One attack order at one cell: select the attacker, open the target phase, name the
        target, confirm the attacker, then quit it (the quit row) or fight one exchange and leave.
        (outcome word, board after) -- `unread` when a read inside the flow was unusable, and the
        second element is then None. Every click is followed by a board read (the task file), and
        the attempt is one `attack-attempt` line."""
        a_xy, d_xy = self.points[attacker], self.points[defender]
        before = (board[attacker], board[defender])
        self.driver.note(event="attack-open", **{"aim:case": case, "aim:cell": cell,
                                                 "country:attacker": attacker,
                                                 "country:defender": defender})
        for block, text in (("attack-select", f"click {a_xy[0]} {a_xy[1]}"),
                            ("attack-open", f"click {ATTACK_BUTTON[0]} {ATTACK_BUTTON[1]}"),
                            ("attack-target", f"click {d_xy[0]} {d_xy[1]}"),
                            ("attack-confirm", f"click {a_xy[0]} {a_xy[1]}")):
            self.send_step(block, text)
            board, _digest = self.read_board(strict=False)
            if board is None:
                self.note_attempt(case, cell, attacker, defender, before, before, "unread", None, None)
                return "unread", None
        ready, ready_sha = self.reader.wait_ready(READY_SECONDS)
        self.driver.note(event="battle-ready", ready=bool(ready))
        if not ready:
            self.send_step("attack-cancel", f"click {CANCEL_BUTTON[0]} {CANCEL_BUTTON[1]}")
            self.refused.add((attacker, defender))
            board, _digest = self.read_board(strict=False)
            self.note_attempt(case, cell, attacker, defender, before, before, "refused", None, ready_sha)
            if case in cases.SIZE_CASES and board is not None:
                self.note_case(case, cell, outcome="refused")
            return "refused", board
        if case == "quit":
            self.leave_battle()
            self.note_case("quit", cell, **{"country:attacker": attacker,
                                            "country:defender": defender})
            board, _digest = self.read_board(strict=False)
            self.note_attempt(case, cell, attacker, defender, before, before, "quit", None, ready_sha)
            return "quit", board
        return self.exchange(board, case, cell, attacker, defender, before, ready_sha)

    def exchange(self, board, case, cell, attacker, defender, before, ready_sha):
        """One exchange click on the ATTACK button (F011 Q-CMB-08: one click is one exchange,
        five when both stacks are big), the board read after it, and the battle's end: capture,
        forfeit (the turn ends), or neither (the battle is still on and the loop leaves it with
        the quit-attack button). (outcome word, board after)."""
        live = board
        self.send_step("attack-exchange", RESULT_WATCH)
        self.summary["attack_clicks"] += 1
        self.send_step("attack-exchange", EXCHANGE_CLICK)
        after, digest = self.reader.wait_change(live, (attacker, defender), CHANGE_SECONDS)
        if after is None:
            self.leave_battle()
            self.note_attempt(case, cell, attacker, defender, before, before, "unread", 0, digest)
            return "unread", None
        a_row, d_row = after[attacker], after[defender]
        lost = (live[attacker]["army"] - a_row["army"]) + (live[defender]["army"] - d_row["army"])
        self.summary["exchanges"] += max(lost, 0)
        if d_row["owner"] != live[defender]["owner"] or d_row["army"] == 0:
            outcome = "capture"
        elif a_row["owner"] != live[attacker]["owner"] or a_row["army"] <= 1:
            outcome = "forfeit"
        elif lost > 0:
            outcome = "exchange"
        else:
            outcome = "no-change"
        if outcome in ("capture", "exchange", "forfeit") and case in cases.SIZE_CASES:
            self.note_case(case, cell, **{"country:attacker": attacker, "country:defender": defender})
        else:
            # The attempt did not meet its cell (a `lost` aim whose attack did not fail, or a click
            # the game did not answer): the pair is done for this turn, so the loop moves on instead
            # of ordering the same attack again.
            self.refused.add((attacker, defender))
        if outcome == "forfeit":
            cell_lost = cases.next_outcome_cell(self.needed(), "lost")
            if cell_lost is not None:
                self.note_case("lost", cell_lost, **{"country:attacker": attacker,
                                                     "country:defender": defender})
            self.leave_battle()
            self.note_attempt(case, cell, attacker, defender, before, (a_row, d_row), outcome, 1, digest)
            return "forfeit", after
        self.leave_battle()
        self.note_attempt(case, cell, attacker, defender, before, (a_row, d_row), outcome, 1, digest)
        return outcome, after

    def leave_battle(self):
        """QUIT ATTACK, or DONE when the country was taken (the tour's own two candidates on the
        centre panel). True when one of the two buttons was there. A quit-attack press is one
        observation of the quit row (Q-CMB-08), so the next unmet cell of that row is marked."""
        self.send_step("leave-battle", CENTRE_WATCH)
        outcome = self.send_step("leave-battle", QUIT_ATTACK_STEP)
        picked = outcome.get("picked")
        self.driver.note(event="leave-battle", picked=int(picked or 0))
        if picked == 1:
            cell = cases.next_outcome_cell(self.needed(), "quit")
            if cell is not None:
                self.note_case("quit", cell)
        return picked is not None

    def note_attempt(self, case, cell, attacker, defender, before, after, outcome, clicks, digest):
        """One `attack-attempt` line: the aim, both countries' owners and counters before and
        after, how many exchange clicks were sent, the outcome word and the last frame."""
        (a_before, d_before), (a_after, d_after) = before, after
        fields = {"event": "attack-attempt", "aim:case": case, "aim:cell": cell,
                  "country:attacker": attacker, "country:defender": defender,
                  "owner:attacker": a_before["owner"], "owner:defender": d_before["owner"],
                  "counter:attacker-before": a_before["army"], "counter:defender-before": d_before["army"],
                  "counter:attacker-after": a_after["army"], "counter:defender-after": d_after["army"],
                  "counter:clicks": int(clicks or 0), "outcome": outcome}
        if digest:
            fields["frame:after"] = digest
        self.driver.note(**fields)
