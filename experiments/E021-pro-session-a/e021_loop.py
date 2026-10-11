"""E021's Session A loop: the driver plays the human seat and attacks on purpose (T45).

It is E020's batch loop with the human's turn replaced (imported and subclassed, never edited:
`experiments/E020-wine-first-run/e020_loop.py` keeps the game structure -- New Game from the title
only (T41, F003), the computers' `quiet` waits, the elimination notice, the winner notice, the
Scoreboard, the shipped scoreboard restore (fix #152), the deadline at the door of every input, and
the clean end on a screen the loop does not recognise). `play_game()` and every notice
handler are E020's; this module overrides `turn()` and, for one case (the Game Options screen after an
abandon, fix #171), `games()`, and adds what a turn does:

1. read the board (boardview.FrameReader: one capture, read by E020's reader);
2. grow a stack: ALL reinforcements on one frontier country (cases.frontier), chosen towards the
   nearest still-needed attacker size, and never on a country that already shows one; when that
   country cannot be selected, a `dismiss` and a second try, then E020's own placement (`place-any`)
   so the turn is still played;
3. attack while a needed cell has a pair on the board (cases.pick) that this turn has not tried:
   `attack-open`, the target's click (the game took it when the target panel changed), the
   attacker's click (the bottom bar watched), then captures polled for the quit-attack button (the
   battle is on). No battle: `attack-cancel`, and the attempt is a refusal only when the game
   answered the click (the bottom bar changed: its not-enough-armies message, F011 Q-CMB-01) and
   no battle is up after the cancel; otherwise it is `unresolved` and meets no cell. A battle:
   * a size cell (`even`, `underdog`, `tiny`) is met by the game's answer to the order, a battle or
     a refusal (an attacker of 1 refused is the observation, the task file); the battle gets one
     exchange click, then the quit-attack button (block `quit-attack`, confirmed by a reading:
     the battle panel gone and the counts unchanged; never by a colour under the pointer);
   * a `quit` aim does the same: one exchange, then the press, so the quit is mid-battle;
   * after a capture, DONE (block `move-in-done`), then the counts;
   * a `lost` or `busy` aim fights: exchange clicks until a capture, a failure or a bound;
   after every exchange click the board is read until the two countries' counts have changed and
   settled (`wait_settled`), and the click's line records both countries before and after;
4. PASS, unless a failed attack ended the turn (F011 Q-CMB-09: the attacking country changes hands
   and the turn passes; the loop then sends nothing more).

Which cell an attempt meets is said by what the game did, never by the aim alone, and each event
meets at most one cell of a row: a confirmed quit-attack press after an exchange the board showed
meets the next `quit` cell; a failed attack (the attacker's country changed hands) the next `lost`
cell; a turn with three or more fights (battles with an exchange the board showed; an opened and
left battle is not one, round 2) the next `busy` cell, with what ended it (Q-CMB-10).

A case whose own action fails DROP_AFTER times in a row (the attempt met no cell and did not end
by the dice: a target not taken, an unresolved order, a press not confirmed, a quit with no fight)
is dropped for the sitting, with a `case-dropped` line: sitting 20261011T070437Z aimed at quit 299
times while its press was misread.

After NO_FIT_TURNS turns in a row of one game with no needed cell on the board and no attack opened,
the game is abandoned (a `game-abandoned` line, then New Game from the `board-menu`, the one New
Game sent from a board: T45 Done-when 1 as amended 2026-10-11), and E020's Scoreboard path starts
the next game. A turn whose placement grew a stack towards a needed attacker size (`place-target`
with a `gap` above 0, cases.frontier: the reinforcements the stack is short of the nearest needed size)
is not such a turn while that gap keeps shrinking (fix #171): it starts the count again, and a
`growing` field on the turn's `turn-end` line says so; a stack whose gap has not got smaller than
its smallest earlier one in the game counts like any other turn, so a stack that never reaches its
size cannot keep a game alive. When no needed cell is reachable on the board, cases.frontier still
names a target (fix #178; sitting 20261011T163105Z read `case None, gap 0` on every placement, so no
game counted as growing and games 2 to 6 were abandoned at turn 3 with no fights): the smallest
attacker size an unmet even or underdog cell still asks for above the grown country's armies. The gap
is then counted against that size, so a stack that passes one size and heads for the next (3, 6, 9
towards 8 and then 12) is still growing, while a stack that stops growing is abandoned as before.
Busy's drop count is per game (same fix): at each game start busy's failures are cleared and busy leaves
`dropped`, since what fails it (the game ended before three fights) belongs to the game; the other cases
keep the sitting-wide count, since their failures are about the press or the target (sitting
20261011T163105Z dropped busy at game 1 turn 6 and never aimed at it again).

With 10 or more human countries the game credits no loss, and the abandon's New Game goes straight to
the Game Options screen with no Scoreboard (F003; sitting 20261011T142906Z, game 2 turn 3, which ended
the sitting 55 minutes early as an unknown screen). The screen reader names that screen `unknown`, so
after the click the loop asks the reader's capture whether it shows it (boardview.options_up, a pixel
check traced to frames by name and sha256). It then writes `game-end` with the reason
`abandoned-no-scoreboard` and no `loss-credited` line, restores the shipped scoreboard file as for
any game after the first (`skr-restored`, naming the next game, #152), writes `game-start`, and sends
block `options-play` -- the clicks of `new-game` after its own first -- instead of `new-game`; the
game then goes on as after `new-game` (`quiet`). `games()` is overridden here for that case only.
New Game is still sent only from the title (`new-game`) or by the abandon (`abandon-game`).

A turn can start with the card trade-in offer instead of the placement row (fix #175; sitting
20261011T154319Z, game 1 turn 10, which ended the sitting 50 minutes early as an unknown screen): the
game shows two buttons in the middle panel when the human's hand holds a valid match, after income and
before placement. F014 (Q-BON-07, C-CRD-05) reads it as the human's choice, never forced: a second
button skips it, and the only forced card step is the discard of a full hand's draw (C-CRD-04). Every
reading says whether the offer is up (boardview.offer_up, a pixel check of the two buttons, traced to
frames by name and sha256); at a turn's start, and once more after a placement that picked nothing
(the offer can come up a second after the income message), the loop sends block `card-decline` (one
plain click on the red decline button, never a card pick, no card matching), waits a bounded poll of readings
for the offer to go, and places as usual with the reading that shows it gone. It logs a `card-offer`
line (`declined` 1, the frame). An offer that is still up after the poll is treated as forced: a
second `card-offer` line (`forced` 1, the frame) and the sitting ends cleanly as `card-trade-forced`
with no further click; a trade path is a follow-up. Block `card-decline` is not a New Game: the
no-New-Game guard (NewGameTest) covers it.

Exact stack sizes (fix #180; the owner, 2026-10-11): ALL puts the whole pool on one country, so a stack jumped
past 8 and 12 (sitting 20261011T170700Z grew one to 27). The placement panel also has a + and a - button (F013
Q-REI-03, CastScript 85 `plus2`: adds one to the counter, capped at the pool; 87 `min2`: takes one off; 83 `Pall2`:
the whole pool; 89 `place2`: moves the counter into the selected country), so when `place_for` has a target with a
`gap` above 0 and a named size case it selects the country as before, sends block `place-plus` once per army (the
counter then holds min(gap, pool)), then block `place-only` (PLACE), and reads the screen: the turn menu means the pool
is spent, the placement row still up means armies are left, which go with `place-commit` (ALL, PLACE) on a second
country (cases.rest_choices: never the target, an interior country first, then a frontier country showing no needed
size, a needed attacker's own stack only last; the phase ends only at pool zero, so the rest must go somewhere). It
logs `place-exact` (`country`, `gap`, `plus`, `rest_to`, and `rest_any` when E020's `place-any` took the rest). The
first reading after the placement is checked (`check_landing`): `place-landed` says whether the stack holds its
armies plus min(gap, pool), the pool being what the human's countries gained in all (`landed` 0 or 1). Intent never
credits a cell; only the board does. With gap 0, or no named case, the placement is `place-commit` as before, and
fix #178's bounds (a gap that stops shrinking stops counting as growing; the abandon) are untouched. None of the new
blocks is a New Game.

Exchanges are counted from the conserved total (DW3): the two countries' armies before a click
minus their armies after it, and only from a reading whose score panel boxes the human's seat: once
another seat's turn has begun (a failure passes the turn by itself) the reading may hold that seat's
moves too, and the click's count is unknown (`isolated` false). A failure's click is counted from
the first reading that shows the hand-over. A capture moves armies between the same two countries (the move-in,
F011 Q-OWN-01: the total is conserved), and a failure gives the attacker's last army to the
defender's owner and leaves the defender as it was (Q-CMB-09), so the total holds across both,
and the count after a capture is read after DONE. One army lost is one exchange (Q-CMB-07); a
click whose total fell by more is logged with the number, and the summary counts both.

Lines of `actions.jsonl` (structural values only, constraint D: our own words, numbers, colour
words and sha256s; no text of the original): `board` (each reading: its frame, the seat, how many
countries were unread), `card-offer`, `place-target`, `place-exact`, `place-landed`, `attack-open`, `exchange-click`, `quit-attack`, `move-in-done`, `case-dropped`,
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
DROP_AFTER = 5                       # consecutive failures of one case's own action before the
                                     # sitting stops aiming at it: sitting 20261011T070437Z's ordinary
                                     # failure rate was about 4% (12 targets not taken in 312 orders),
                                     # so five in a row by chance is about 1 in 10^7, and five cost
                                     # under a minute (about 8 s an order); that sitting aimed at quit
                                     # 299 times while its press was misread
NO_FIT_TURNS = 3                     # turns in a row of one game with no needed cell on the board and
                                     # no attack opened before the game is abandoned (the owner,
                                     # 2026-10-11, T45 Done-when 1 as amended in 50b6f35): sitting
                                     # 20261011T091212Z passed turns 7 to 13 on one blue country that
                                     # no needed cell fitted
NO_CELL_FAILURES = ("capture", "forfeit")    # an attempt that met no cell but ended by the dice is
                                             # not a failure of the case's own action
SEAT = cases.HUMAN_SEAT
REST_TRIES = 3                       # second-country candidates tried (fix #180) before E020's `place-any`
OFFER_POLLS = 5                      # readings after `card-decline` before the offer counts as still up
OFFER_POLL_SECONDS = 0.5             # between them (a guess: the game answers the click at once as far
                                     # as any frame shows; no sitting has declined yet, so this is the
                                     # first measurement's to confirm)
OPTIONS = "game-options"             # the screen after an abandon's New Game that is neither the Scoreboard
                                     # nor the board: the setup screen (boardview.options_up); the screen
                                     # reader names it `unknown`, so the loop asks the reader's capture
                                     # (fix #171). Never a name the click-driver's reader gives.


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
        self.failures, self.dropped = {}, set()
        self.no_fit = (None, 0)              # (game, no-fit turns in a row in it)
        self.options_seen = False            # the abandon's New Game went to the Game Options screen
        self.grow = (None, {})               # (game, {country: smallest gap seen on a turn it was grown})
        self.offers = 0                      # the card trade-in offers declined in this turn (fix #175)
        self.turn_growing = False            # this turn's placement grew a stack towards a needed size
        self.landing = None                  # an exact placement the next reading checks (fix #180)
        self.summary.update(cases_met_before=len(self.met), cases_met=len(self.met), attack_attempts=0,
                            refusals=0, battles=0, exchange_clicks=0, clicks_one_army=0,
                            clicks_several_armies=0, clicks_no_change=0, clicks_unread=0, clicks_unisolated=0,
                            captures=0,
                            forfeits=0, quits=0, fights=0)

    # --- the games ------------------------------------------------------------------------------

    def games(self):
        """E020's `games()` with one addition (fix #171): a game abandoned with no Scoreboard after it
        (the abandon's New Game went to the Game Options screen, F003's case of 10 or more human
        countries) ends as `abandoned-no-scoreboard`, with no `loss-credited` line, and the next game
        starts from that screen -- the skr restore (#152) and `game-start` as for any game after the
        first, then block `options-play` in place of `new-game` (its clicks after New Game's own, which
        was sent already). Everything else is E020's, line for line: New Game from the title only, the
        winner notice, the Scoreboard, an unknown screen ending the sitting."""
        after_notice = None                          # the screen read after a notice's CONTINUE (the title)
        for game in range(1, self.games_max + 1):
            if self.out_of_time():
                self.summary["ended"] = "sitting-seconds"
                return self.summary
            self.driver.context = {"game": game, "turn": 0}
            screen = after_notice if after_notice is not None else self.driver.read_screen()
            after_notice = None
            if screen not in e020_loop.NEW_GAME_ON and screen != OPTIONS:
                self.unknown_screen(screen)
                return self.summary
            self.check_time("game-start")
            if self.restore is not None and game > 1:
                if not self.restore_shipped_skr(screen):
                    return self.summary
            self.driver.note(event="game-start")
            self.new_game_state()
            self.game_open = True
            self.summary["games"] = game
            block = "options-play" if screen == OPTIONS else "new-game"
            self.send(block)
            self.game_over_seen, self.scoreboard_seen, self.options_seen = None, False, False
            reason = self.play_game()
            if self.game_over_seen is not None:
                self.end_game(reason, **self.game_over_seen)
                after_notice = self.continue_after_game_over()
            elif self.scoreboard_seen:
                self.end_game(reason)
                after_notice = self.leave_scoreboard()
            elif self.options_seen:
                self.end_game(reason)
                after_notice = OPTIONS
            else:
                self.end_game(reason)
                if self.summary["ended"] is None:
                    self.summary["ended"] = reason
                return self.summary
            if after_notice is None:
                return self.summary
        self.summary["ended"] = "games-max"
        return self.summary

    def new_game_state(self):
        """What belongs to one game: busy's failure count and its drop (fix #178). The other cases'
        failures stay sitting-wide."""
        self.failures.pop("busy", None)
        if "busy" in self.dropped:
            self.dropped.discard("busy")
            self.summary["dropped"] = sorted(self.dropped)

    # --- the case table -------------------------------------------------------------------------

    def needed(self):
        """The cells the picker still aims at: unmet, and not of a case dropped for this sitting."""
        return [pair for pair in cases.needed_cells(self.met) if pair[0] not in self.dropped]

    def track(self, case, met_before, outcome):
        """Count a failure of `case`'s own action (the attempt met no cell and did not end by the
        dice), reset on any other attempt; at DROP_AFTER in a row the case is dropped for the
        sitting, with a `case-dropped` line (round 2, point 3)."""
        if len(self.met) > met_before or outcome in NO_CELL_FAILURES:
            self.failures[case] = 0
            return
        self.failures[case] = self.failures.get(case, 0) + 1
        if self.failures[case] >= DROP_AFTER and case not in self.dropped:
            self.dropped.add(case)
            self.summary["dropped"] = sorted(self.dropped)
            self.driver.note(event="case-dropped", case=case, failures=self.failures[case], outcome=outcome)

    def meet(self, case, cell=None, **fields):
        """Mark a cell met and log it (`case-met`, the export's source for the record's case
        groups). `cell` None takes the row's lowest unmet cell (the outcome rows). False when the
        cell was met already, or the row is complete."""
        if cell is None:
            cell = cases.next_outcome_cell(cases.needed_cells(self.met), case)
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
        self.turn_growing = False
        self.landing = None
        self.offers = 0
        screen = self.driver.read_screen()
        if screen not in e020_loop.BOARD:
            return self.off_board(screen)
        reading = self.look()
        if reading is None:
            return "board-unreadable"
        reading, ended = self.answer_offer(reading)
        if ended is not None:
            return ended
        placed = self.place_for(reading.board, fallback=False)
        if placed is False:
            # the offer can come up a second after the income message (fix #175): look once more
            reading = self.look()
            if reading is None:
                return "board-unreadable"
            answered = self.offers
            reading, ended = self.answer_offer(reading)
            if ended is not None:
                return ended
            if self.offers > answered:                 # declined just now: the row can light, try again
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
            reading, ended = self.answer_offer(reading)
            if ended is not None:
                return ended
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

    def answer_offer(self, reading):
        """(reading, None) when no offer is up on `reading`, or when it was declined and a reading shows it
        gone (that reading: the placement goes on from it); (None, why) when the sitting ends: an offer that
        is still up after the poll is treated as forced (`card-offer` with `forced` 1, ended
        `card-trade-forced`, no further click), and a reading that cannot be used ends it as any
        unreadable board does. The loop never picks or trades cards (F014 Q-BON-07: the human may skip
        the offer; a trade path is a follow-up). `self.offers` counts the ones declined this turn."""
        if not reading.offer:
            return reading, None
        self.offers += 1
        self.driver.note(event="card-offer", declined=1, sha256=reading.sha256)
        self.send("card-decline")
        after = None
        for poll in range(OFFER_POLLS):
            after = self.look(strict=False)
            if after is not None and not after.offer:
                return after, None
            if poll + 1 < OFFER_POLLS:
                self.sleep(OFFER_POLL_SECONDS)
        if after is None:
            self.unknown_screen(self.driver.read_screen(), ended="board-unreadable: after card-decline")
            return None, "board-unreadable"
        self.driver.note(event="card-offer", forced=1, sha256=after.sha256)
        self.unknown_screen(self.driver.read_screen(), ended="card-trade-forced")
        return None, "card-trade-forced"

    def place_for(self, board, fallback):
        """Select the frontier country (the placement row lights only for a country the human
        owns) and commit ALL on it (`place-commit`). With `fallback`, E020's own `place-any` when
        that country could not be selected. True when placed, False when nothing was selected,
        else why the game ended (the screen read again before the commit, fix #141 round 2)."""
        ready = cases.pick(board, self.needed(), self.adjacency, points=self.points)
        avoid = {ready[2]} if ready and ready[0] in cases.SIZE_CASES else set()
        choice = cases.frontier(board, self.needed(), self.adjacency, points=self.points, avoid=avoid)
        picked, target = None, None
        if choice is not None:
            country, _defender, case, cell, gap = choice
            target = (country, gap, board[country]["army"] + gap)
            fields = {"country": country, "gap": gap}
            if case is not None:
                fields.update(case=case, cell=cell)
            self.driver.note(event="place-target", **fields)
            x, y = self.points[country]
            self.send_step("place-select", PLACE_WATCH)
            picked = self.send_step("place-select", PLACE_SELECT.format(x=x, y=y)).get("picked")
        chosen = bool(picked)                  # the stack the loop chose, not E020's own `place-any`
        if not picked and fallback:
            picked = self.send("place-any").get("picked")
            self.driver.note(event="place-any", picked=int(picked or 0))
        if not picked:
            return False
        screen = self.driver.read_screen()
        if screen not in e020_loop.BOARD:
            return self.off_board(screen)
        self.summary["placements"] += 1
        self.landing = None
        exact = chosen and choice is not None and choice[2] is not None and choice[4] > 0
        if exact:
            ended = self.place_exact(board, target[0], target[1])
            if ended is not True:
                return ended
        else:
            self.send("place-commit")
        self.summary["turns"] += 1
        self.turn_growing = chosen and self.growing(*target)
        return True

    def place_exact(self, board, country, gap):
        """The chosen stack gets exactly `gap` armies (fix #180; the owner, 2026-10-11): `place-plus`
        once per army (the counter holds min(gap, pool): + is capped at the pool, F013 Q-REI-03), then
        `place-only` (PLACE). The pool is read from the screen: the turn menu means it is zero (the
        phase ends only then), the placement row still up means armies are left, and they go with
        `place-commit` (ALL, PLACE) on a second country, chosen by the rule of cases.rest_choices: never
        `country`, an interior country first (never an attacker), then a frontier country that shows no
        needed size, and a needed attacker's own stack only when nothing else is left. If none of
        the three first choices can be selected, E020's `place-any` takes it. Logs one `place-exact`
        line (`country`, `gap`, `plus` clicks, `rest_to` the second country, or None when the pool
        was zero; `rest_any` 1 when E020's `place-any` took the rest) and keeps what the landing check
        (`check_landing`) needs. True when the pool is spent, else why the game ended."""
        for _ in range(gap):
            self.send("place-plus")
        self.send("place-only")
        screen = self.driver.read_screen()
        if screen not in e020_loop.BOARD:
            return self.off_board(screen)
        rest, rest_any = None, 0
        if screen != "board-menu":                       # the row is still up: the pool holds armies
            for candidate in cases.rest_choices(board, self.needed(), self.adjacency, country,
                                                points=self.points)[:REST_TRIES]:
                x, y = self.points[candidate]
                self.send_step("place-select", PLACE_WATCH)
                if self.send_step("place-select", PLACE_SELECT.format(x=x, y=y)).get("picked"):
                    rest = candidate
                    break
            if rest is None:
                rest_any = int(bool(self.send("place-any").get("picked")))
            screen = self.driver.read_screen()
            if screen not in e020_loop.BOARD:
                return self.off_board(screen)
            self.send("place-commit")
        fields = {"rest_any": 1} if rest_any else {}
        self.driver.note(event="place-exact", country=country, gap=gap, plus=gap, rest_to=rest, **fields)
        self.landing = {"country": country, "gap": gap, "board": board}
        return True

    def check_landing(self, reading):
        """The landing check of an exact placement (fix #180), on the first reading after the pool is
        spent: the pool is what the human's countries gained in all (armies of the countries the
        seat owned and both readings read, after minus before), and the stack should hold its armies
        before plus min(gap, pool). One `place-landed` line says what the board shows (`landed` 1 when
        it holds that, else 0, with `armies` the reading, or None when the country was unread). It
        credits no cell: the attack that follows is picked from the board alone, as always."""
        landing, self.landing = self.landing, None
        if landing is None:
            return
        before, country, gap = landing["board"], landing["country"], landing["gap"]
        pool = 0
        for number, row in before.items():
            now = cases.readable(reading.board, number)
            was = cases.readable(before, number)
            if was is not None and now is not None and was["owner"] == SEAT and now["owner"] == SEAT:
                pool += now["army"] - was["army"]
        now = cases.readable(reading.board, country)
        armies = None if now is None else now["army"]
        expected = before[country]["army"] + min(gap, pool)
        self.driver.note(event="place-landed", country=country, gap=gap, pool=pool, expected=expected,
                         armies=armies, landed=int(armies == expected))

    def growing(self, country, gap, size=None):
        """True when this turn's placement grew a stack towards a needed size: `country` was chosen
        with a `gap` (reinforcements short of the nearest needed attacker size, cases.frontier) above
        0, and that gap is smaller than any earlier gap of this country in this game, or the country is
        new to the game's list (fix #171). A stack that stays as short as it was, or a country that
        turns up again with a gap it already had, does not count as growing, so a stack that never
        reaches its size cannot keep the game alive: the turn then counts towards NO_FIT_TURNS. The
        smallest gap seen is kept per country, so a few countries taking turns cannot avoid the count
        either (a gap is a whole number, so a country shrinks at most as many times as its first gap).
        `size` is the attacker size the gap is counted towards (the country's armies plus the gap): the
        smallest gap is kept per (country, size), so a stack that has passed one size and heads for
        the next one (fix #178) is growing, and the bound holds still, as there are only so many sizes."""
        game = self.driver.context.get("game")
        previous, best = self.grow
        if previous != game:
            best = {}
        if gap <= 0:
            self.grow = (game, best)
            return False
        key = (country, size)
        shrank = key not in best or gap < best[key]
        best[key] = min(gap, best.get(key, gap))
        self.grow = (game, best)
        return shrank

    def attack_phase(self):
        """Attack while a needed cell has an untried pair; then PASS, unless a failure passed the
        turn. None, or why the game ended for the loop."""
        tried, battles, fights, ended = set(), 0, 0, "pass"
        opened = False
        for _ in range(MAX_ATTEMPTS_PER_TURN):
            reading = self.look()
            if reading is None:
                self.driver.note(event="turn-end", battles=battles, fights=fights, end="board-unreadable",
                                 growing=int(self.turn_growing))
                return "board-unreadable"
            self.check_landing(reading)
            choice = cases.pick(reading.board, self.needed(), self.adjacency, points=self.points,
                                exclude=tried)
            if choice is None:
                break
            tried.add(choice[2:])
            opened = True
            met_before = len(self.met)
            outcome, game_end = self.attack(reading, *choice)
            self.track(choice[0], met_before, outcome)
            battles += int(self.last["battle"])
            fights += int(self.last["fought"])
            if game_end is not None:
                self.driver.note(event="turn-end", battles=battles, fights=fights, end="game-end",
                                 growing=int(self.turn_growing))
                return game_end
            if outcome == "forfeit":
                ended = "forfeit"
                break
            if outcome == "no-menu":
                ended = "no-menu"
                break
        if opened or self.turn_growing:
            # an attack, or a stack still growing towards a needed size: the run of no-fit turns
            # starts again (fix #171); a stack that stopped growing counts like any other turn
            self.no_fit = (None, 0)
        if not opened and not self.turn_growing and self.abandon_due():
            self.driver.note(event="turn-end", battles=0, fights=0, end="abandoned", growing=0)
            return self.abandon()
        if ended != "forfeit":
            self.send("pass")
        self.driver.note(event="turn-end", battles=battles, fights=fights, end=ended,
                         growing=int(self.turn_growing))
        # Q-CMB-10 asks about attacks that fought: a battle opened and left with no exchange the
        # board showed is not one (round 2, point 2: sitting 20261011T070437Z met busy 10/10 so)
        if fights >= BUSY_MINIMUM:
            self.meet("busy", battles=battles, fights=fights, end=ended)
        return None

    # --- the no-fit abandon ---------------------------------------------------------------------

    def abandon_due(self):
        """Count one more turn of this game in which no needed cell fitted and no attack was opened
        (any other turn resets the count, in `attack_phase`'s caller below); True on the
        NO_FIT_TURNS-th in a row."""
        game = self.driver.context.get("game")
        previous, count = self.no_fit
        count = count + 1 if previous == game else 1
        self.no_fit = (game, count)
        return count >= NO_FIT_TURNS

    def abandon(self):
        """End a game no needed cell fits (T45 Done-when 1, amended 2026-10-11): a `game-abandoned`
        line, then E020's New Game click from the `board-menu` (block `abandon-game`). The game
        credits a loss and shows the Scoreboard (F003; sitting 20261008T204817Z), and E020's own
        path takes over: `loss-credited`, `scoreboard-continue`, the title, the skr restore (#152),
        `new-game`. Any other screen after the click ends the sitting cleanly (`off_board`). On a
        board without its menu row New Game is not on the screen: the turn passes instead."""
        game, count = self.no_fit
        screen = self.driver.read_screen()
        if screen != "board-menu":
            self.send("pass")
            return None
        self.driver.note(event="game-abandoned", reason="no-fit", turns=count)
        self.summary["abandoned"] = self.summary.get("abandoned", 0) + 1
        self.no_fit = (None, 0)
        self.send("abandon-game")
        screen = self.driver.read_screen()
        if screen == "unknown" and self.options_up():
            # no Scoreboard, no loss: the game went straight to its setup screen (fix #171; sitting
            # 20261011T142906Z, game 2 turn 3); `games()` starts the next game from it
            self.options_seen = True
            return "abandoned-no-scoreboard"
        return self.off_board(screen)

    def options_up(self):
        """True when one capture through the reader shows the Game Options screen (boardview.options_up).
        A capture that cannot be read is no: the sitting then ends as it does on any unknown screen."""
        try:
            up, digest = self.reader.options_screen()
        except Exception as exc:                   # an undecodable capture, a stand-in without the probe
            self.driver.note(event="options-unread", reason=f"{type(exc).__name__}: {exc}"[:120])
            return False
        self.driver.note(event="options-screen", sha256=digest, up=int(up))
        return up

    # --- one attack -----------------------------------------------------------------------------

    def attack(self, reading, case, cell, attacker, defender):
        """One attack order aimed at (case, cell): (outcome word, why the game ended or None).
        Outcomes: `no-menu` (the attack button did not answer), `target-not-taken`,
        `attacker-refused`, `unresolved`, `quit` (the press confirmed by a reading),
        `quit-unconfirmed`, `capture`, `forfeit`."""
        self.attempt += 1
        self.summary["attack_attempts"] += 1
        seq, board = self.attempt, reading.board
        attempt = {"attempt": seq, "case": case, "cell": cell, "attacker": attacker, "defender": defender,
                   "before": self.counts(board, attacker, defender), "frames": [reading.sha256],
                   "battle": False, "fought": False, "clicks": 0, "lost": 0, "unknown": 0}
        self.last = attempt
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
        if case in cases.SIZE_CASES or case == "quit":
            limit = 1                      # one exchange, then the quit-attack button: mid-battle
        else:
            limit = min(MAX_FIGHT_CLICKS, sum(c or 0 for c in attempt["before"][0::2]) + 5)
        return self.fight(attempt, start, limit)

    def fight(self, attempt, board, limit):
        """Exchange clicks, at most `limit`, each followed by the board read until it settled, until
        a capture, a failure or the limit; then the battle is left (`move-in-done` after a capture, the
        quit-attack button otherwise; nothing after a failure, which passed the turn)."""
        attacker, defender = attempt["attacker"], attempt["defender"]
        battle_seen = True                       # the battle panel was up when the fight began
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
            if state in ("on", "capture", "forfeit"):
                self.summary["fights"] += int(not attempt["fought"])
                attempt["fought"] = True           # the board showed this exchange
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
                done = bool(self.send("move-in-done").get("changed"))
                self.driver.note(event="move-in-done", attempt=attempt["attempt"], changed=int(done))
                final = self.look(strict=False)
                final_board = final.board if final is not None else after
                if final is not None:
                    attempt["frames"].append(final.sha256)
                # counted only from a reading after DONE that still boxes the human's seat: the
                # move-in screen's counts are not final, and no other seat may have played
                self.note_click(attempt, board, final_board, [r.sha256 for r in seen], moved_in=done,
                                isolated=final is not None and final.seat == SEAT)
                self.summary["captures"] += 1
                return self.finish(attempt, "capture", final_board, after_leave=True)
            isolated = seen[-1].seat == SEAT
            if state in ("unread", "no-change"):
                self.note_click(attempt, board, after, [r.sha256 for r in seen], isolated=isolated)
                return self.leave(attempt, after, battle_seen=seen[-1].battle)
            self.note_click(attempt, board, after, [r.sha256 for r in seen], isolated=isolated)
            board, battle_seen = after, seen[-1].battle
        # the quit-attack press meets a quit cell only when the last reading showed the battle up
        return self.leave(attempt, board, battle_seen=battle_seen)

    def leave(self, attempt, board, battle_seen=True):
        """Leave a battle that is still on with the quit-attack button (block `quit-attack`), and
        confirm it from a reading, never from a colour under the pointer (round 2, point 1): the
        battle panel gone and the two countries as they were before the press. A confirmed press
        meets the next `quit` cell only after an exchange the board showed and with the battle up
        on the last reading (Q-CMB-08 asks about leaving mid-battle). A press the reading does not
        confirm is `quit-unconfirmed`, meets nothing, and a battle panel still up ends the sitting
        cleanly (finish)."""
        self.send("quit-attack")
        reading = self.look(strict=False)
        if reading is not None:
            attempt["frames"].append(reading.sha256)
        a, d = attempt["attacker"], attempt["defender"]
        confirmed = (reading is not None and not reading.battle
                     and self.counts(reading.board, a, d) == self.counts(board, a, d))
        self.driver.note(event="quit-attack", attempt=attempt["attempt"], confirmed=int(confirmed))
        after = reading.board if reading is not None else board
        if not confirmed:
            return self.finish(attempt, "quit-unconfirmed", after, after_leave=True)
        self.summary["quits"] += 1
        if battle_seen and attempt["fought"]:
            self.meet("quit", attempt=attempt["attempt"], fought=1)
        return self.finish(attempt, "quit", after, after_leave=True)

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
