"""Synthetic T45 fixtures: boards, adjacency, a fake click-driver, a fake live reader and shaped
records. No wine, no display, no original bytes, no PNG of the game (rule 18): every board here is
a dict of country readings, and every frame stand-in is bytes the test itself made.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _sub in ("tools", "runtime/iwp", "runtime/iwp/spike", "setup/iwp",
              "experiments/E020-wine-first-run", "experiments/E020-wine-first-run/reader",
              "experiments/E021-pro-session-a"):
    if str(ROOT / _sub) not in sys.path:
        sys.path.insert(0, str(ROOT / _sub))

import cases  # noqa: E402

COUNTRIES = 46
# A small synthetic island for the tests: 1-2-3 blue, 4-5 red, 3 next to 4 (the frontier).
ADJ = {1: {2, 3}, 2: {1, 3}, 3: {1, 2, 4}, 4: {3, 5}, 5: {4}}
BLUE = "blue"
RED = "red"


def board(cells=None, owner="blue", army=1):
    """A 46-country board of `owner`/`army`, with `cells` ({country: (owner, army)}) over it."""
    out = {c: {"army": army, "owner": owner} for c in range(1, COUNTRIES + 1)}
    for country, (own, count) in (cells or {}).items():
        out[country] = {"army": count, "owner": own}
    return out


def frontier_board():
    """Blue 3 with 2 armies next to red 4 with 1: the even cell 1 (attacker 2 vs defender 1)."""
    return board({1: (BLUE, 1), 2: (BLUE, 1), 3: (BLUE, 2), 4: (RED, 1), 5: (RED, 3)})


def all_met():
    """The whole table met: a sitting that needs nothing."""
    return {(case, cell) for case in cases.CASES for cell in cases.cells(case)}


POINTS = {c: (10 * c, 10 * c) for c in range(1, 11)}      # synthetic click points, one per country
AT = {xy: c for c, xy in POINTS.items()}


class FakeGame:
    """A synthetic game behind the click-driver: the board, the screen, the attack flow's state.

    It answers the blocks and the synthesised steps the way F011's reading says the human's attack
    goes (Q-CMB-01: the attacker needs at least the target's armies and more than 1; Q-CMB-08: an
    exchange click is `per_click` exchanges; Q-CMB-09: at 1 army the attacking country goes to the
    defender's owner and the turn passes; Q-OWN-01: a capture shows the move-in, DONE moves 1 in).
    `losers` scripts who loses each exchange ("a" or "d"), in order."""

    def __init__(self, board, screen="board", losers=(), per_click=1, reinforcements=3, adjacency=ADJ):
        self.board = board
        self.screen = screen
        self.losers = list(losers)
        self.per_click = per_click
        self.reinforcements = reinforcements
        self.adjacency = adjacency
        self.seat = BLUE
        self.selected = None          # the country the placement row lit for
        self.phase = "menu"           # menu, target, attacker, battle, move-in, passed
        self.target = self.attacker = None
        self.after_pass = None
        self.after_continue = "title"
        self.after_scoreboard = "title"
        self.attack_button_works = True
        self.board_screen = "board"        # the screen New Game's Play Game leaves up
        self.after_abandon = "scoreboard"  # the screen after New Game from the board
        self.games = self.passes = 0
        self.on_pass = None                # (game) -> None: the computers' turns, as a test scripts them
        self.quit_works = True             # False: the quit-attack press does not land
        self.quits = 0                     # battles the quit-attack button closed
        self.exchange_noop = False         # True: an exchange click changes nothing on the board
        self.attacker_unanswered = False   # the attacker's click reaches no handler: nothing changes
        self.refused = 0                   # orders the game's attacker check refused (its message)
        self.seat_lag = False              # the score panel still boxes blue on the first reading
                                           # after a failure
        self.computer_move = None          # (game) -> None: the next seat's play after a failure

    def click_country(self, block, country):
        if block == "attack-target":
            ok = (self.phase == "target" and self.board[country]["owner"] != BLUE
                  and any(self.board[n]["owner"] == BLUE for n in self.adjacency.get(country, ())))
            if ok:
                self.target, self.phase = country, "attacker"
            return {"changed": ok}
        if block == "attack-attacker":
            if self.attacker_unanswered:
                return {"changed": False}
            a, d = self.board[country], self.board.get(self.target)
            if (self.phase == "attacker" and a["owner"] == BLUE and self.target in self.adjacency.get(country, ())
                    and a["army"] > 1 and a["army"] >= d["army"]):
                self.attacker, self.phase = country, "battle"
            elif self.phase == "attacker":
                self.refused += 1          # the not-enough-armies message changes the bottom bar
            return {"changed": True}
        return {"changed": False}

    def block(self, name):
        if name == "new-game":
            self.screen = self.board_screen
            self.games += 1
        elif name == "options-play":
            # the clicks after New Game's own, on the Game Options screen (fix #171)
            if self.screen == "game-options":
                self.screen = self.board_screen
                self.games += 1
        elif name == "abandon-game":
            # New Game from the board: with fewer than 10 human countries the game credits a loss
            # and shows the Scoreboard (F003); elsewhere the click is not on the screen
            if self.screen == "board-menu":
                self.screen = self.after_abandon
                return {"changed": True}
            return {"changed": False}
        elif name == "place-commit" and self.selected is not None:
            self.board[self.selected]["army"] += self.reinforcements
            self.selected = None
        elif name == "pass":
            self.passes += 1
            if self.on_pass is not None:
                self.on_pass(self)
            if self.after_pass is not None:
                self.screen = self.after_pass
        elif name == "attack-open":
            if self.attack_button_works and self.phase == "menu":
                self.phase = "target"
                return {"changed": True}
            return {"changed": False}
        elif name == "attack-cancel":
            if self.phase in ("target", "attacker"):
                self.phase = "menu"
        elif name == "exchange":
            if self.phase == "battle" and not self.exchange_noop:
                for _ in range(self.per_click):
                    self.exchange()
                    if self.phase != "battle":
                        break
            return {"changed": True}
        elif name == "quit-attack":
            if self.phase == "battle" and self.quit_works:
                self.phase = "menu"
                self.quits += 1
                return {"changed": True}
            return {"changed": False}
        elif name == "move-in-done":
            if self.phase == "move-in":
                self.board[self.attacker]["army"] -= 1
                self.board[self.target] = {"army": 1, "owner": BLUE}
                self.phase = "menu"
                return {"changed": True}
            return {"changed": False}
        elif name == "game-over-continue":
            self.screen = self.after_continue
        elif name == "scoreboard-continue":
            self.screen = self.after_scoreboard
        elif name == "place-any":
            for country in sorted(self.board):
                if self.board[country]["owner"] == BLUE:
                    self.selected = country
                    return {"picked": 1}
            return {"picked": None}
        return {}

    def exchange(self):
        a, d = self.board[self.attacker], self.board[self.target]
        loser = self.losers.pop(0) if self.losers else "d"
        if loser == "a":
            a["army"] -= 1
        else:
            d["army"] -= 1
        if d["army"] == 0:
            d["owner"] = BLUE
            self.phase = "move-in"
        elif a["army"] == 1:
            self.board[self.attacker] = {"army": 1, "owner": d["owner"]}
            self.phase, self.seat = "passed", d["owner"]


class FakeDriver:
    """What the loop needs of the click-driver (runtime/iwp/driver/clicks.py): blocks, steps, note
    lines and the screen, over a FakeGame. Every block and step is logged for the tests."""

    def __init__(self, game):
        self.game = game
        self.blocks, self.steps, self.notes = [], [], []
        self.context = {}
        self.quiet = True
        self.pending_watch = None

    def run_block(self, name):
        self.blocks.append(name)
        if name == "quiet":
            return {"quiet": self.quiet}
        return self.game.block(name)

    def run_step(self, block, step):
        self.steps.append((block, step.op, tuple(step.args)))
        if step.op == "click-until?" and block == "place-select":
            country = AT.get(tuple(step.args[5:7]))
            if country is not None and self.game.board[country]["owner"] == BLUE:
                self.game.selected = country
                return {"picked": 1}
            return {"picked": None}
        if step.op == "click":
            return self.game.click_country(block, AT.get(tuple(step.args)))
        return {}

    def note(self, **fields):
        self.notes.append(dict(self.context, **fields))

    def read_screen(self):
        # the click-driver's pixel reader has no name for the Game Options screen: `unknown` (fix #171)
        return "unknown" if self.game.screen == "game-options" else self.game.screen

    def read_winner(self):
        return None

    def final_frame(self, name):
        return "f" * 64

    def events(self, name):
        return [note for note in self.notes if note.get("event") == name]

    def country_clicks(self):
        """The countries the loop clicked (synthesised steps), in order, with their block."""
        return [(block, AT.get(args)) for block, op, args in self.steps if op == "click"]


class FakeReader:
    """boardview.FrameReader's interface over a FakeGame: each read is a copy of the game's board,
    with a frame sha256 of its own. `unread` makes every reading that many countries short."""

    def __init__(self, game, unread=0, fail=None, battle_blind=0):
        self.game = game
        self.unread = unread
        self.fail = fail
        self.battle_blind = battle_blind   # this many battle probes miss a battle that is up
        self.seat_after_failure = None     # the seat the score panel boxes once the turn has passed
        self.reads = 0

    def read(self, seat=None):
        import boardview
        if self.fail is not None:
            raise self.fail
        self.reads += 1
        board = {c: dict(row) for c, row in self.game.board.items()}
        if seat is None:
            seat = self.game.seat
            if self.game.phase == "passed" and self.seat_after_failure is not None:
                seat = self.seat_after_failure
        return boardview.Reading(board, f"{self.reads:064x}", seat,
                                 self.game.phase in ("battle", "move-in"), self.unread)

    def options_screen(self):
        """boardview.FrameReader.options_screen: (the capture shows the Game Options screen, its sha256)."""
        self.reads += 1
        return self.game.screen == "game-options", f"{self.reads:064x}"

    def wait_battle(self, seconds):
        reading = self.read()
        if self.battle_blind:
            self.battle_blind -= 1
            return reading._replace(battle=False)
        return reading

    def wait_settled(self, before, countries, seconds):
        """One reading; after a failure, the next seat's move (when the test gives one) comes after
        it, and a second reading shows it (the interleaving of round 1's R2)."""
        game = self.game
        if game.phase == "passed" and game.computer_move is not None:
            first = self.read(seat=BLUE if game.seat_lag else None)
            game.computer_move(game)
            game.computer_move = None
            return [first, self.read()]
        return [self.read()]


def game_board(cells):
    """A 46-country board, all blue 1 (so no country but `cells` has an enemy to click: the
    synthetic adjacency only joins 1 to 10), with `cells` ({country: (owner, army)}) over it."""
    return board(cells)


def record(run_id, groups, experiment="E021", batch="session-a"):
    """A run/1-shaped record whose observations are `groups` ([(step, {field: value}, [refs])])."""
    observations = [{"step": 0, "source": "process", "field": "sitting:epoch", "value": "1790000000"}]
    outputs = []
    step_of = {}
    for step, fields, refs in groups:
        for field, value in fields.items():
            observations.append({"step": step, "source": "screen", "field": field, "value": str(value)})
        for ref in refs:
            observations.append({"step": step, "source": "screen", "ref": f"sha256:{ref}"})
            if ref not in step_of:
                outputs.append({"name": f"{len(outputs)}.png", "sha256": ref, "store": "release:E021"})
                step_of[ref] = step
    return {"schema": "run/1", "run_id": run_id, "experiment": experiment, "arm": batch, "rep": 1,
            "code_commit": "abcdef123456", "machine": "local",
            "artifact": {"set": "iwp-2.0-996e86c5", "variant": "unregistered"},
            "runtime": {"driver": f"experiments/E021-pro-session-a/launcher.py@abcdef123456",
                        "platform": "wine-on-user-machine-iwp-2.0", "fingerprint": {"wine": "wine-10.0"}},
            "interventions": [{"level": "I1", "what": "screenshots of the display"}],
            "start_state": {"id": "S-iwp-prefix-sync", "sha256": "c" * 64,
                            "restore": "fresh prefix sync from the F019 install, no save"},
            "seed": None,
            "actions": {"script": "experiments/E021-pro-session-a/session-a.steps", "sha256": "b" * 64,
                        "args": ["--batch", batch]},
            "observations": observations, "outputs": outputs,
            "started": "2026-10-10T12:00:00Z", "ended": "2026-10-10T13:00:00Z", "status": "completed"}


def write_record(root, doc):
    """The record at runs/E021/<batch>/<run_id>.json under `root`."""
    path = Path(root) / "runs" / doc["experiment"] / doc["arm"] / f"{doc['run_id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path
