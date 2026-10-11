"""E021's Session A loop: the driver plays the human seat and attacks on purpose (T45).

It is E020's batch loop with the human's turn replaced (imported and subclassed, never edited:
`experiments/E020-wine-first-run/e020_loop.py` keeps the game structure -- New Game from the title
only (T41, F003), the computers' `quiet` waits, the elimination notice, the winner notice, the
Scoreboard, the shipped scoreboard restore (fix #152), the deadline at the door of every input, and
the clean end on a screen the loop does not recognise). `games()`, `play_game()` and every notice
handler are E020's; this module overrides `turn()` only, and adds what a turn does:

1. read the board (boardview.FrameReader: one capture, read by E020's reader);
2. grow a stack: ALL reinforcements on one frontier country (cases.frontier), chosen towards the
   nearest still-needed attacker size, and never on a country that already shows one; when that
   country cannot be selected, a `dismiss` and a second try, then E020's own placement (`place-any`)
   so the turn is still played;
3. attack while a needed cell has a pair on the board (cases.pick) that this turn has not tried:
   `attack-open`, the target's click (the game took it when the target panel changed), the
   attacker's click, then captures polled for the quit-attack button (the battle is on). No battle:
   `attack-cancel`, and the attempt is a refusal. A battle:
   * a size cell (`even`, `underdog`, `tiny`) is met by the game's answer to the order, a battle or
     a refusal (an attacker of 1 refused is the observation, the task file); the battle gets one
     exchange click, then the quit-attack button;
   * a `quit` aim presses the quit-attack button at once;
   * a `lost` or `busy` aim fights: exchange clicks until a capture, a failure or a bound;
   after every exchange click the board is read until the two countries' counts have changed and
   settled (`wait_settled`), and the click's line records both countries before and after;
4. PASS, unless a failed attack ended the turn (F011 Q-CMB-09: the attacking country changes hands
   and the turn passes; the loop then sends nothing more).

Which cell an attempt meets is said by what the game did, never by the aim alone, and each event
meets at most one cell of a row: a quit-attack press in a battle meets the next `quit` cell; a
failed attack (the attacker's country changed hands) the next `lost` cell; a turn with three or
more battles the next `busy` cell, with what ended it (Q-CMB-10).

Exchanges are counted from the conserved total (DW3): the two countries' armies before a click
minus their armies after it. A capture moves armies between the same two countries (the move-in,
F011 Q-OWN-01: the total is conserved), and a failure gives the attacker's last army to the
defender's owner and leaves the defender as it was (Q-CMB-09), so the total holds across both,
and the count after a capture is read after DONE. One army lost is one exchange (Q-CMB-07); a
click whose total fell by more is logged with the number, and the summary counts both.

Lines of `actions.jsonl` (structural values only, constraint D: our own words, numbers, colour
words and sha256s; no text of the original): `board` (each reading: its frame, the seat, how many
countries were unread), `place-target`, `attack-open`, `exchange-click`, `leave-battle`,
`attack-attempt` (the aim, both countries before and after, the battle, the clicks, the armies
lost, the outcome, the frames), `case-met`, `turn-end`. The export (e021_export.py) turns
`exchange-click`, `attack-attempt`, `case-met` and `turn-end` into the record's observations.

Hazards the task file names, and how they are held here:
* New Game is sent only on the title: inherited from E020's `games()`, never written again here;
* the deal is random (F018): a cell the board cannot show is left unmet, and the turn passes; a
  board is never forced;
* one click, several exchanges: logged per click with its number; the loop never works around it
  (the main session decides);
* a reading with more than boardview.UNREAD_LIMIT unread countries at a turn's start ends the
  sitting cleanly (`board-unreadable`), with a last frame and no click: the player never plans on a
  board it cannot see. Inside an attack the flow leaves the battle instead.
"""
import time

import e020_loop  # noqa: E402  (E020's loop, imported read-only)
import exchange_events  # noqa: E402  (E020's reader: the committed adjacency, T21's tabulation)
import boardview  # noqa: E402
import cases  # noqa: E402
import points as points_module  # noqa: E402
from driver import clicks  # noqa: E402  (the click-driver; on sys.path as the launcher puts it)
import steps as stepslib  # noqa: E402  (the E002 step language, on sys.path via driver.clicks)

PLACE_WATCH = "watch 265 530 270 26"                 # the placement row (E020's `place`)
PLACE_SELECT = "click-until? 168 168 168 24 1000 {x} {y}"    # E020's own placement-row test, one point
TARGET_WATCH = "watch 10 502 250 70"                 # the spike's TARGET_PANEL
BAR_WATCH = "watch 0 495 800 105"                    # the bottom bar (the board's own blink is outside it):
                                                     # a refusal must change it to count as one
BUSY_MINIMUM = 3                     # a `busy` turn: at least 3 battles (Q-CMB-10)
MAX_ATTEMPTS_PER_TURN = 12           # a bound of the player's, never a rule of the game
MAX_FIGHT_CLICKS = 60                # likewise, for one fight (the bound is also the two stacks + 5)
BATTLE_SECONDS = 3.0                 # the poll for the quit-attack button after the attacker's click
                                     # (the spike polls 1.5 s)
SETTLE_SECONDS = 4.0                 # the poll for the counts to change and settle after a click
BATTLE_OUTCOMES = ("quit", "capture", "forfeit", "held")
SEAT = cases.HUMAN_SEAT


class SessionALoop(e020_loop.BatchLoop):
    """One Session A sitting: E020's games and screens, this task's turns and attacks."""

    def __init__(self, driver, batch, clock=time.monotonic, sleep=time.sleep, restore=None,
                 shipped_skr=None, reader=None, adjacency=None, points=None, met=()):
        """`reader` is the live view (boardview.FrameReader, or a test's stand-in with `read()`,
        `wait_battle(s)` and `wait_settled(board, countries, s)`); `adjacency` is {country: set of
        neighbours} (E015's tabulation when absent); `points` the clickable countries
        (walkthroughs/coordinates.md); `met` the cells already met, read by the launcher from the
        latest measurements/progress-r<nn>.json, so a resumed batch starts where it stopped."""
        super().__init__(driver, batch, clock=clock, sleep=sleep, restore=restore, shipped_skr=shipped_skr)
        if reader is None:
            raise ValueError("the Session A loop needs a live board reader")
        self.reader = reader
        self.adjacency = exchange_events.load_adjacency() if adjacency is None else adjacency
        self.points = points_module.click_points() if points is None else points
        self.met = {tuple(pair) for pair in met}
        self.attempt = 0
        self.summary.update(cases_met_before=len(self.met), cases_met=len(self.met), attack_attempts=0,
                            refusals=0, battles=0, exchange_clicks=0, clicks_one_army=0,
                            clicks_several_armies=0, clicks_no_change=0, clicks_unread=0, clicks_unisolated=0,
                            captures=0,
                            forfeits=0, quits=0)

    # --- the case table -------------------------------------------------------------------------

    def needed(self):
        return cases.needed_cells(self.met)

    def meet(self, case, cell=None, **fields):
        """Mark a cell met and log it (`case-met`, the export's source for the record's case
        groups). `cell` None takes the row's lowest unmet cell (the outcome rows). False when the
        cell was met already, or the row is complete."""
        if cell is None:
            cell = cases.next_outcome_cell(self.needed(), case)
            if cell is None:
                return False
        if (case, cell) in self.met:
            return False
        self.met.add((case, cell))
        self.summary["cases_met"] = len(self.met)
        self.driver.note(event="case-met", case=case, cell=cell, **fields)
        return True

    # --- inputs, through the click-driver -------------------------------------------------------

    def send_step(self, block, text):
        """One synthesised step (a country's click), through the click-driver, behind the deadline
        like every other input (T41 round 1)."""
        self.check_time(block)
        step = stepslib.parse_line(text)
        if step is None or step.op not in clicks.ALLOWED:
            raise ValueError(f"{text!r} is not a click-driver step")
        return self.driver.run_step(block, step)

    def click_country(self, block, country, watch=None):
        """A plain click on a country's proven point, after `watch` when one is given."""
        x, y = self.points[country]
        if watch:
            self.send_step(block, watch)
        return self.send_step(block, f"click {x} {y}")

    # --- the board ------------------------------------------------------------------------------

    def look(self, strict=True):
        """One reading, or None. Strict (a turn's own reads): a reading that cannot be used ends the
        sitting cleanly, `board-unreadable` (a last frame, no click). Not strict (inside an attack):
        the reason is logged and the caller leaves the battle."""
        try:
            reading = self.reader.read()
        except Exception as exc:                   # no templates file, an undecodable capture
            reason = f"{type(exc).__name__}: {exc}"[:120]
            reading = None
        else:
            reason = None
            if reading.unread > boardview.UNREAD_LIMIT:
                reason = f"{reading.unread} countries unread"
        if reading is not None:
            self.driver.note(event="board", sha256=reading.sha256, seat=reading.seat,
                             unread=reading.unread, battle=bool(reading.battle))
        if reason is None:
            return reading
        self.driver.note(event="board-unread", reason=reason)
        if strict:
            self.unknown_screen(self.driver.read_screen(), ended=f"board-unreadable: {reason}")
        return None

    # --- one human turn -------------------------------------------------------------------------

    def turn(self):
        """One turn: the placement (two tries with a `dismiss` between them, as E020's), then the
        attacks, then PASS. None when the turn was played, else why the game ended for the loop."""
        screen = self.driver.read_screen()
        if screen not in e020_loop.BOARD:
            return self.off_board(screen)
        reading = self.look()
        if reading is None:
            return "board-unreadable"
        placed = self.place_for(reading.board, fallback=False)
        if placed is False:
            self.send("dismiss")
            if not self.wait_quiet():
                return "unknown-screen"
            screen = self.driver.read_screen()
            if screen not in e020_loop.BOARD:
                return self.off_board(screen)
            reading = self.look()
            if reading is None:
                return "board-unreadable"
            placed = self.place_for(reading.board, fallback=True)
        if placed is False:
            screen = self.driver.read_screen()
            if screen == "board-menu":                 # a live game the human cannot place in
                self.unknown_screen(screen, ended="placement-refused")
                return "placement-refused"
            return self.off_board(screen)
        if placed is not True:                         # the game ended while the block ran
            return placed
        return self.attack_phase()

    def place_for(self, board, fallback):
        """Select the frontier country (the placement row lights only for a country the human
        owns) and commit ALL on it (`place-commit`). With `fallback`, E020's own `place-any` when
        that country could not be selected. True when placed, False when nothing was selected,
        else why the game ended (the screen read again before the commit, fix #141 round 2)."""
        ready = cases.pick(board, self.needed(), self.adjacency, points=self.points)
        avoid = {ready[2]} if ready and ready[0] in cases.SIZE_CASES else set()
        choice = cases.frontier(board, self.needed(), self.adjacency, points=self.points, avoid=avoid)
        picked = None
        if choice is not None:
            country, _defender, case, cell, gap = choice
            fields = {"country": country, "gap": gap}
            if case is not None:
                fields.update(case=case, cell=cell)
            self.driver.note(event="place-target", **fields)
            x, y = self.points[country]
            self.send_step("place-select", PLACE_WATCH)
            picked = self.send_step("place-select", PLACE_SELECT.format(x=x, y=y)).get("picked")
        if not picked and fallback:
            picked = self.send("place-any").get("picked")
            self.driver.note(event="place-any", picked=int(picked or 0))
        if not picked:
            return False
        screen = self.driver.read_screen()
        if screen not in e020_loop.BOARD:
            return self.off_board(screen)
        self.summary["placements"] += 1
        self.send("place-commit")
        self.summary["turns"] += 1
        return True

    def attack_phase(self):
        """Attack while a needed cell has an untried pair; then PASS, unless a failure passed the
        turn. None, or why the game ended for the loop."""
        tried, battles, ended = set(), 0, "pass"
        for _ in range(MAX_ATTEMPTS_PER_TURN):
            reading = self.look()
            if reading is None:
                self.driver.note(event="turn-end", battles=battles, end="board-unreadable")
                return "board-unreadable"
            choice = cases.pick(reading.board, self.needed(), self.adjacency, points=self.points,
                                exclude=tried)
            if choice is None:
                break
            tried.add(choice[2:])
            outcome, game_end = self.attack(reading, *choice)
            if outcome in BATTLE_OUTCOMES:
                battles += 1
            if game_end is not None:
                self.driver.note(event="turn-end", battles=battles, end="game-end")
                return game_end
            if outcome == "forfeit":
                ended = "forfeit"
                break
            if outcome == "no-menu":
                ended = "no-menu"
                break
        if ended != "forfeit":
            self.send("pass")
        self.driver.note(event="turn-end", battles=battles, end=ended)
        if battles >= BUSY_MINIMUM:
            self.meet("busy", battles=battles, end=ended)
        return None

    # --- one attack -----------------------------------------------------------------------------

    def attack(self, reading, case, cell, attacker, defender):
        """One attack order aimed at (case, cell): (outcome word, why the game ended or None).
        Outcomes: `no-menu` (the attack button did not answer), `target-refused`,
        `attacker-refused`, `quit`, `held` (left by a press that was not the quit-attack button's),
        `capture`, `forfeit`, `unread`."""
        self.attempt += 1
        self.summary["attack_attempts"] += 1
        seq, board = self.attempt, reading.board
        attempt = {"attempt": seq, "case": case, "cell": cell, "attacker": attacker, "defender": defender,
                   "before": self.counts(board, attacker, defender), "frames": [reading.sha256],
                   "battle": False, "clicks": 0, "lost": 0, "unknown": 0}
        self.driver.note(event="attack-open", attempt=seq, case=case, cell=cell, attacker=attacker,
                         defender=defender)
        if not self.send("attack-open").get("changed"):
            # The turn menu's attack button did not answer: whatever is up is cleared like a prompt
            # (E020's `dismiss`), and the attack phase ends there.
            self.send("dismiss")
            return self.finish(attempt, "no-menu", board)
        if not self.click_country("attack-target", defender, watch=TARGET_WATCH).get("changed"):
            self.send("attack-cancel")
            return self.finish(attempt, "target-not-taken", self.board_after(board, attempt))
        answered = bool(self.click_country("attack-attacker", attacker, watch=BAR_WATCH).get("changed"))
        attempt["answered"] = answered
        battle = self.reader.wait_battle(BATTLE_SECONDS)
        attempt["frames"].append(battle.sha256)
        if not battle.battle:
            self.send("attack-cancel")
            after = self.look(strict=False)
            if after is not None:
                attempt["frames"].append(after.sha256)
                if after.battle:
                    # the battle came up after the probe gave up: neither a refusal nor a battle the
                    # loop can account for; the sitting ends cleanly, the cell stays unmet
                    self.unknown_screen(self.driver.read_screen(), ended="battle-stuck")
                    return self.finish(attempt, "unresolved", after.board, check=False)[0], "battle-stuck"
            board_after = after.board if after is not None else board
            if not answered or after is None:
                # no affirmative answer to the order (the bottom bar did not change, or no reading
                # after the cancel): an unresolved attempt, never a refusal, and no cell is met
                return self.finish(attempt, "unresolved", board_after)
            self.summary["refusals"] += 1
            if case in cases.SIZE_CASES:
                self.meet(case, cell, attempt=seq, battle=0)
            return self.finish(attempt, "attacker-refused", board_after)
        attempt["battle"] = True
        self.summary["battles"] += 1
        if case in cases.SIZE_CASES:
            self.meet(case, cell, attempt=seq, battle=1)
        start = battle.board if self.counts_known(battle.board, attacker, defender) else board
        if case == "quit":
            return self.leave(attempt, start)
        if case in cases.SIZE_CASES:
            limit = 1
        else:
            limit = min(MAX_FIGHT_CLICKS, sum(c or 0 for c in attempt["before"][0::2]) + 5)
        return self.fight(attempt, start, limit)

    def fight(self, attempt, board, limit):
        """Exchange clicks, at most `limit`, each followed by the board read until it settled, until
        a capture, a failure or the limit; then the battle is left (DONE after a capture, the
        quit-attack button otherwise; nothing after a failure, which passed the turn)."""
        attacker, defender = attempt["attacker"], attempt["defender"]
        for _ in range(limit):
            self.send("exchange")
            attempt["clicks"] += 1
            self.summary["exchange_clicks"] += 1
            seen = self.reader.wait_settled(board, (attacker, defender), SETTLE_SECONDS)
            attempt["frames"] += [r.sha256 for r in seen]
            after = seen[-1].board
            state = self.state(board, after, attacker, defender)
            if state == "pending":                      # the attacker at 1, still the human's: the
                more = self.reader.wait_settled(after, (attacker, defender), SETTLE_SECONDS)
                attempt["frames"] += [r.sha256 for r in more]       # forfeit has not shown yet
                seen = seen + more
                after = seen[-1].board
                state = self.state(board, after, attacker, defender)
            if state == "forfeit":
                # A failure passes the turn by itself (Q-CMB-09), and the next seat plays without
                # waiting for any input, so a later reading can hold that seat's moves too. The
                # click's count is taken from the first reading that shows the hand-over, and only
                # when the score panel still boxes the human's seat there (no other turn has begun);
                # otherwise the count is unknown (R2 of the round-1 review).
                first = next(r for r in seen if self.state(board, r.board, attacker, defender) == "forfeit")
                self.note_click(attempt, board, first.board, [r.sha256 for r in seen],
                                isolated=first.seat == SEAT)
                self.summary["forfeits"] += 1
                self.meet("lost", attempt=attempt["attempt"])
                return self.finish(attempt, "forfeit", first.board, seat=seen[-1].seat)
            if state == "capture":
                picked = self.leave_battle(attempt)
                final = self.look(strict=False)
                final_board = final.board if final is not None else after
                if final is not None:
                    attempt["frames"].append(final.sha256)
                self.note_click(attempt, board, final_board, [r.sha256 for r in seen], moved_in=picked == 2)
                self.summary["captures"] += 1
                return self.finish(attempt, "capture", final_board, after_leave=True)
            if state in ("unread", "no-change"):
                self.note_click(attempt, board, after, [r.sha256 for r in seen])
                return self.leave(attempt, after, battle_seen=seen[-1].battle)
            self.note_click(attempt, board, after, [r.sha256 for r in seen])
            board = after
        return self.leave(attempt, board)

    def leave(self, attempt, board, battle_seen=True):
        """Leave a battle that is still on: the quit-attack button (candidate 1 of `leave-battle`),
        which meets the next `quit` cell when the battle panel was up before the press."""
        picked = self.leave_battle(attempt)
        after = self.board_after(board, attempt)
        if picked == 1:
            self.summary["quits"] += 1
            if battle_seen:
                self.meet("quit", attempt=attempt["attempt"])
            return self.finish(attempt, "quit", after, after_leave=True)
        return self.finish(attempt, "held", after, after_leave=True)

    def leave_battle(self, attempt):
        outcome = self.send("leave-battle")
        picked = outcome.get("picked")
        self.driver.note(event="leave-battle", attempt=attempt["attempt"], picked=int(picked or 0))
        return picked

    def board_after(self, board, attempt):
        """A reading after an attempt's last input: its board (the frame cited), else `board`."""
        reading = self.look(strict=False)
        if reading is None:
            return board
        attempt["frames"].append(reading.sha256)
        return reading.board

    def finish(self, attempt, outcome, board, seat=None, after_leave=False, check=True):
        """The attempt's line, then the screen: (outcome, why the game ended or None). After a
        failure the turn has passed and the screen is the computers'; anything but the board after
        any other attempt is answered by E020's `off_board`. A battle panel still up after the loop
        left it ends the sitting cleanly (`battle-stuck`): the next order would go into it."""
        a, d = attempt["attacker"], attempt["defender"]
        fields = dict(attempt, event="attack-attempt", outcome=outcome, after=self.counts(board, a, d))
        if attempt.get("unknown"):
            fields["lost"] = None            # a click of it has no count: the total is not known
        if seat is not None:
            fields["seat_after"] = seat
        self.driver.note(**fields)
        if outcome == "forfeit" or not check:
            return outcome, None
        screen = self.driver.read_screen()
        if screen not in e020_loop.BOARD:
            return outcome, self.off_board(screen)
        if after_leave or outcome in ("target-not-taken", "attacker-refused", "unresolved"):
            check = self.look(strict=False)
            if check is not None and check.battle:
                self.unknown_screen(screen, ended="battle-stuck")
                return outcome, "battle-stuck"
        return outcome, None

    # --- reading a click ------------------------------------------------------------------------

    @staticmethod
    def counts(board, attacker, defender):
        """[attacker army, attacker owner, defender army, defender owner] (None where unread)."""
        a, d = board.get(attacker) or {}, board.get(defender) or {}
        return [a.get("army"), a.get("owner"), d.get("army"), d.get("owner")]

    @staticmethod
    def counts_known(board, attacker, defender):
        return None not in SessionALoop.counts(board, attacker, defender)

    @staticmethod
    def state(before, after, attacker, defender):
        """What a click did, from two readings of the two countries: `forfeit` (the attacker's
        country is another seat's: Q-CMB-09), `capture` (the defender's is the human's, or holds
        0), `unread`, `pending` (the attacker at 1 and still the human's: the failure has not shown
        yet), `no-change`, or `on` (the battle goes on)."""
        a_army, a_owner, d_army, d_owner = SessionALoop.counts(after, attacker, defender)
        if a_owner is not None and a_owner != SEAT:
            return "forfeit"
        if d_owner == SEAT or d_army == 0:
            return "capture"
        if None in (a_army, a_owner, d_army, d_owner):
            return "unread"
        if a_army <= 1:
            return "pending"
        if SessionALoop.counts(before, attacker, defender) == [a_army, a_owner, d_army, d_owner]:
            return "no-change"
        return "on"

    def note_click(self, attempt, before, after, frames, moved_in=None, isolated=True):
        """One `exchange-click` line: both countries before and after the click, and the armies
        the two lost together (the conserved total, module text): None when a count is unread, or
        when the reading after the click cannot be shown to hold the human's battle alone
        (`isolated` False: another seat's turn may have begun)."""
        a, d = attempt["attacker"], attempt["defender"]
        b, f = self.counts(before, a, d), self.counts(after, a, d)
        lost = None
        if isolated and None not in (b[0], b[2], f[0], f[2]):
            lost = (b[0] + b[2]) - (f[0] + f[2])
        if lost is None:
            attempt["unknown"] = attempt.get("unknown", 0) + 1
        if not isolated:
            self.summary["clicks_unisolated"] += 1
        elif lost is None:
            self.summary["clicks_unread"] += 1
        elif lost == 1:
            self.summary["clicks_one_army"] += 1
        elif lost > 1:
            self.summary["clicks_several_armies"] += 1
        else:
            self.summary["clicks_no_change"] += 1
        if lost is not None and lost > 0:
            attempt["lost"] += lost
        fields = {"event": "exchange-click", "attempt": attempt["attempt"], "click": attempt["clicks"],
                  "before": b, "after": f, "lost": lost, "isolated": bool(isolated), "frames": list(frames)}
        if moved_in is not None:
            fields["moved_in"] = bool(moved_in)
        self.driver.note(**fields)
