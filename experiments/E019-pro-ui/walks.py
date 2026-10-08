"""E019 (T24): the per-question walk table for the Isle Wars Pro UI catalogue.

One record per question: the recorder (run_walk.py) launches the game through T13's driver
(runtime/iwp/driver/session.py), performs this table's actions for the question, and writes a
run/1 record under runs/E019/<batch>/. The catalogue (findings/F020-pro-ui-observations.md)
turns the records into the per-question observations; nothing here states a rule.

Every coordinate and rectangle is measured, not guessed:
- points cited to `E002 tour.steps` or one of the `opt-*.steps` scripts are the click points of
  F003's recorded runs (findings/F003, Screens table);
- points cited to `spike` come from runtime/iwp/spike/cycle.py's constants, read off F002's
  exploration screenshots;
- points cited to `E002 explore s2` come from the committed exploration commands
  (experiments/E002-iwp-state-inventory/measurements/explore/), which F003 keeps machine-local
  and non-evidence; the walk verifies each of them at run time (a click that does nothing is
  recorded, and `click!` aborts);
- rectangles cited as `derived` are computed from measured points and say how.

Language notes. A `step` action is one line of the E002 step language (runtime/iwp/spike/steps.py),
performed through session.perform(); `wait` waits for a known screen by its pixels; the recorder's
own reads (`census`, `greyscale`, `text_rows`, `timed_watch`, `hover_map`) are pixels-read only —
no OCR pass anywhere (the task's Done-when 4). `composite` actions are the recorder's named
multi-turn plans; each says what it records.

What the walks cannot do is stated per question in `notes`, with what was searched. The unmeasured
points (the board's CARD and MOVE menu buttons, the plus/minus placement buttons) stay unmeasured:
a walk that needs one records the gap instead of guessing (CLAUDE.md rule 17).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "questions" / "pro-static.md"

# The five per-screen batches of T24, in the order the task file fixes them (one commit each).
BATCHES = [
    ("title-options", ["Q-UI-04", "Q-UI-10", "Q-UI-19", "Q-UI-22"]),
    ("board-pieces", ["Q-UI-01", "Q-UI-02", "Q-UI-03", "Q-UI-05", "Q-UI-20", "Q-PLY-04"]),
    ("play", ["Q-UI-08", "Q-UI-12", "Q-UI-13", "Q-UI-15", "Q-UI-16"]),
    ("events-end", ["Q-UI-06", "Q-UI-07", "Q-UI-11", "Q-UI-14", "Q-UI-21"]),
    ("inputs-sounds", ["Q-UI-09", "Q-UI-17", "Q-UI-18"]),
]

# Measured rectangles (x, y, w, h) of the 800x600 stage, each with where it came from.
REGIONS = {
    "board-area": {"rect": (0, 0, 800, 495),
                   "source": "E002 tour.steps watch (the board above the bottom panels)"},
    "message-strip": {"rect": (265, 530, 270, 26),
                      "source": "E002 tour.steps watch (the phase prompt line)"},
    "phase-panel": {"rect": (262, 502, 276, 70),
                    "source": "E002 tour.steps watch; the spike's CENTRE_PANEL"},
    "attack-panel": {"rect": (545, 502, 250, 70),
                     "source": "E002 tour.steps watch (the ATTACK / QUIT ATTACK panel)"},
    "turn-panel": {"rect": (10, 502, 250, 70),
                   "source": "the spike's TARGET_PANEL (Select Country To Attack)"},
    "bottom-bar": {"rect": (0, 560, 800, 40),
                   "source": "derived: the label row of the measured click points (y=585) and the "
                             "spike's OPTIONS_LABEL band (y 572..598)"},
    "return-button": {"rect": (470, 515, 185, 40),
                      "source": "the spike's RETURN_BUTTON (green, on the Options screen)"},
    "turn-menu-band": {"rect": (250, 502, 300, 70),
                       "source": "derived: the band around the measured PASS (417,530) and the "
                                 "spike's ATTACK (303,530) points"},
    "full-stage": {"rect": (0, 0, 800, 600),
                   "source": "the whole 800x600 stage"},
}

# Measured click points of the title screen's bottom bar and the screens they open (F003).
OPTIONS_CLICK = (320, 585)      # E002 tour.steps; the spike's OPTIONS_CLICK
HELP_CLICK = (215, 585)         # E002 tour.steps
SCORES_CLICK = (620, 585)       # E002 tour.steps
NEWGAME_CLICK = (100, 585)      # E002 tour.steps
QUIT_CLICK = (712, 585)         # the spike's QUIT_CLICK (F002's exploration screenshots)
RETURN_CLICK = (565, 532)       # the spike's RETURN_CLICK
PLAY_CLICK = (565, 532)         # E002 tour.steps (Play Game on the setup screen)
LOSS_CONTINUE_CLICK = (400, 526)  # E002 tour.steps (Continue on the loss notice)
HELP_RETURN_CLICK = (388, 536)  # E002 tour.steps
SCORES_RETURN_CLICK = (388, 516)  # E002 tour.steps
HELP_PAGE_CLICKS = (20, 744, 481)  # E002 tour.steps (20 clicks on the Help page-down arrow)
EAR_CLICK = (396, 533)          # E002 explore s2.cmd-0003 (the ear switch; verified at run time)

# The Options screen's controls, from the opt-*.steps scripts of F003's recorded runs.
FREQ_NEVER_CLICK = (571, 389)   # opt-freq-never.steps

# Back-to-title: the tour's Return click until the title subtitle band shows again.
BACK_TO_TITLE = ["watch 180 335 440 25",
                 "click-until 0 192 240 16 1500 565 532 565 532 565 532",
                 "watch all", "settle"]

# A Blue country to place on, and the attack candidate list: E002 tour.steps' measured points
# (the game ignores a point the board does not take; `click-until` stops at the first that reacts).
PLACE_COUNTRIES = ("55 193 49 261 42 330 105 441 142 385 153 433 188 399 235 441 239 282 178 283 "
                   "132 238 139 166 277 177 358 60 344 110 307 160 390 163 393 98 473 139 440 190 "
                   "509 223 566 143 525 89 593 86 682 99 760 129 685 153 746 196 668 211 748 264 "
                   "655 282 750 411 698 436 639 446 515 404 521 343 454 363 448 444 372 453 377 410 "
                   "308 425 333 305 412 294 321 262")
PLACE_WATCH = "watch 265 530 270 26"
PLACE_CLICK = "click-until 168 168 168 24 1000 " + PLACE_COUNTRIES
ALL_CLICK = (307, 543)          # E002 tour.steps (ALL, on the placement panel)
PLACE_DONE_CLICK = (497, 543)   # E002 tour.steps (PLACE)
ATTACK_PANEL_CLICK = (337, 531)  # E002 tour.steps (ATTACK, one exchange)
QUIT_ATTACK_CLICKS = "click-until 0 192 64 16 600 456 531 495 540"  # QUIT ATTACK, or DONE (tour)
PASS_CLICK = (417, 530)         # E002 tour.steps (PASS, on the turn menu)
CONTINUE_CLICK = (402, 531)     # E002 tour.steps (CONTINUE, when a card was awarded)

# The shared reach-the-board prefix (the deal is random, F018: every board read happens after it).
_REACH_BOARD = [
    ("step", f"click {NEWGAME_CLICK[0]} {NEWGAME_CLICK[1]}"),   # New Game
    ("step", "settle"),
    ("step", f"click! {PLAY_CLICK[0]} {PLAY_CLICK[1]}"),        # Play Game
    ("step", "watch 0 0 800 495"),
    ("step", "settle 4"),        # the computer players' opening turns; quiet when Blue's turn
]

# The shared one-human-turn prefix of the tour: place every army on one Blue country, then open
# the attack panel (E002 tour.steps, the runs F003 records).
_TURN_TO_ATTACK = _REACH_BOARD + [
    ("step", PLACE_WATCH),
    ("step", PLACE_CLICK),
    ("step", "shot place-selected"),
    ("step", "watch 262 502 276 70"),
    ("step", f"click! {ALL_CLICK[0]} {ALL_CLICK[1]}"),
    ("step", "shot place-all"),
    ("step", f"click! {PLACE_DONE_CLICK[0]} {PLACE_DONE_CLICK[1]}"),
    ("step", "settle"),
    ("step", "shot place-done"),
    ("step", f"attack-picked {PLACE_COUNTRIES}"),
    ("step", "shot attack-ready"),
]

WALKS = {
    # --- batch 1: title and options -----------------------------------------------------------
    "Q-UI-04": {
        "batch": "title-options",
        "title": "every screen reached by walking each menu path",
        "may_write_saved_files": True,   # the mid-game New Game credits a loss (F003)
        "count": {"word": "distinct screenshots", "at_least": 8, "measure": "distinct shots"},
        "actions": [
            ("step", "shot title"),
            ("step", f"click {OPTIONS_CLICK[0]} {OPTIONS_CLICK[1]}"),
            ("wait", "options"),
            ("step", "shot options"),
            * [("step", line) for line in BACK_TO_TITLE],
            ("step", f"click {HELP_CLICK[0]} {HELP_CLICK[1]}"),
            ("step", "settle"),
            ("step", "shot help-page-1"),
            ("step", "clicks {} {} {}".format(*HELP_PAGE_CLICKS)),
            ("step", "settle"),
            ("step", "shot help-page-2"),
            ("step", "clicks {} {} {}".format(*HELP_PAGE_CLICKS)),
            ("step", "settle"),
            ("step", "shot help-page-3"),
            ("step", f"click! {HELP_RETURN_CLICK[0]} {HELP_RETURN_CLICK[1]}"),
            ("step", "settle"),
            ("step", f"click {SCORES_CLICK[0]} {SCORES_CLICK[1]}"),
            ("step", "settle"),
            ("step", "shot scores"),
            ("step", f"click! {SCORES_RETURN_CLICK[0]} {SCORES_RETURN_CLICK[1]}"),
            ("step", "settle"),
            ("step", f"click {NEWGAME_CLICK[0]} {NEWGAME_CLICK[1]}"),
            ("step", "settle"),
            ("step", "shot newgame-setup"),
            ("step", f"click! {PLAY_CLICK[0]} {PLAY_CLICK[1]}"),
            ("step", "watch 0 0 800 495"),
            ("step", "settle 4"),
            ("step", "shot board"),
            ("step", f"click {NEWGAME_CLICK[0]} {NEWGAME_CLICK[1]}"),
            ("step", "settle"),
            ("step", "shot loss-notice"),
            ("step", f"click! {LOSS_CONTINUE_CLICK[0]} {LOSS_CONTINUE_CLICK[1]}"),
            ("step", "settle"),
            ("step", f"click! {PLAY_CLICK[0]} {PLAY_CLICK[1]}"),
            ("step", "watch 0 0 800 495"),
            ("step", "settle 4"),
            ("step", f"click {QUIT_CLICK[0]} {QUIT_CLICK[1]}"),
            ("wait", "notice"),
            ("step", "shot quit-notice"),
        ],
        "notes": [
            "the Soleau Games label is a refused rectangle (runtime/iwp/spike/steps.py); its "
            "screens are never walked, as in E002",
            "the Quit path stops at the notice: T13's driver terminates by kill, so Exit Game is "
            "never clicked inside a recorded walk (F003's tour reached it under the spike's "
            "ui-quit termination)",
        ],
    },
    "Q-UI-10": {
        "batch": "title-options",
        "title": "three timed walkthroughs with click counts",
        "may_write_saved_files": False,
        "count": {"word": "walkthroughs", "at_least": 3, "measure": "walkthroughs"},
        "actions": [("composite", "title_options_rounds", {"rounds": 3})],
        "notes": [
            "each round is title -> Options -> title, timed with the monotonic clock and counted "
            "in inputs; the launch-to-title time is the session's own measurement",
        ],
    },
    "Q-UI-19": {
        "batch": "title-options",
        "title": "screenshots at each supported resolution",
        "may_write_saved_files": False,
        "count": None,          # the sizes are checked as sizes: one completed record per size, each
                        # carrying its measured display size (check_ui_catalogue.py, R5)
        "sizes": ["640x480x24", "800x600x24", "1024x768x24", "1280x1024x24"],
        "actions": [
            ("step", "shot title-at-this-size"),
            ("step", f"click {OPTIONS_CLICK[0]} {OPTIONS_CLICK[1]}"),
            ("wait", "options"),
            ("step", "shot options-at-this-size"),
        ],
        "notes": [
            "one launch per size; the driver assumes the 800x600 stage is centred in the game "
            "window (the spike's stage origin), so a size where the title is not detected, or the "
            "Options click does nothing, is recorded as its own outcome",
            "the projector-level windowing is not established here: what the projector does with "
            "the desktop size is outside the Lingo and outside this walk",
        ],
    },
    "Q-UI-22": {
        "batch": "title-options",
        "title": "the event-frequency option, on and off",
        "may_write_saved_files": False,
        "count": {"word": "screenshots", "at_least": 2, "measure": "shots"},
        "actions": [
            ("step", f"click {OPTIONS_CLICK[0]} {OPTIONS_CLICK[1]}"),
            ("wait", "options"),
            ("step", "shot frequency-default"),
            ("step", f"click {FREQ_NEVER_CLICK[0]} {FREQ_NEVER_CLICK[1]}"),
            ("step", "settle"),
            ("step", "shot frequency-locked"),
        ],
        "notes": [
            "the frequency option is locked in the unregistered build (F003's locked-frequency "
            "screens; F019's registration gates): on and off is reachable only at the file-write "
            "path, not at the click, and the record notes the locked state",
        ],
    },

    # --- batch 2: board and pieces -------------------------------------------------------------
    "Q-UI-01": {
        "batch": "board-pieces",
        "title": "the board at the one player count the build allows, and in greyscale",
        "may_write_saved_files": False,
        "count": {"word": "screenshots", "at_least": 1, "measure": "shots"},
        "reads": {"colour-census": 1, "greyscale-census": 1},
        "regions": ["board-area"],
        "actions": [
            *_REACH_BOARD,
            ("step", "shot board-1"),
            ("census", "board-area", 16),
            ("greyscale", "board-area", 16),
        ],
        "notes": [
            "the screenshot is taken after the deal (the deal is random, F018): no two walks show "
            "the same board",
            "one human seat: the unregistered build locks the seat toggles (F003's locked-human "
            "screen)",
        ],
    },
    "Q-UI-02": {
        "batch": "board-pieces",
        "title": "boards with production centres at the default size, and the centre flash",
        "may_write_saved_files": False,
        "count": {"word": "screenshots", "at_least": 2, "measure": "shots"},
        "reads": {"timed-watch": 1},
        "regions": ["board-area", "message-strip"],
        "actions": [
            *_REACH_BOARD,
            ("step", "shot board-with-centres-1"),
            ("timed_watch", ["message-strip", "board-area"], 20, 0.25),   # one loop polls both
            ("step", "shot board-with-centres-2"),
        ],
        "notes": [
            "the centres' positions are random (F017's reading of the set-up handler); the shots "
            "show whatever marks the board carries at the default size",
            "the centre flash is recorded only if an event fires inside the watch window; the "
            "record reports what changed and when, and the catalogue says what the shots show",
        ],
    },
    "Q-UI-03": {
        "batch": "board-pieces",
        "title": "the army-count text, measured by pixel rows",
        "may_write_saved_files": False,
        "count": {"word": "screenshots", "at_least": 1, "measure": "shots"},
        "reads": {"text-rows": 1},
        "regions": ["board-area", "message-strip", "phase-panel"],
        "actions": [
            *_REACH_BOARD,
            ("step", "shot board-armies"),
            ("text_rows", "message-strip"),
            ("text_rows", "phase-panel"),
        ],
        "notes": [
            "the territory numbers' font and size are in the cast (not decoded); the measured "
            "text rows are the message strip's and the phase panel's, where the game writes at a "
            "known place; the catalogue describes the territory numbers from the annotated shot",
        ],
    },
    "Q-UI-05": {
        "batch": "board-pieces",
        "title": "sampled colours of the board and the options screen",
        "may_write_saved_files": False,
        "count": None,
        "reads": {"colour-census": 2},
        "regions": ["board-area", "full-stage"],
        "actions": [
            ("step", f"click {OPTIONS_CLICK[0]} {OPTIONS_CLICK[1]}"),
            ("wait", "options"),
            ("census", "full-stage", 16),
            * [("step", line) for line in BACK_TO_TITLE],
            *_REACH_BOARD,
            ("step", "shot board-colours"),
            ("census", "board-area", 16),
        ],
        "notes": [
            "the census is a quantised pixel count, not a colour claim: the catalogue reads the "
            "values, and the colour values themselves stay in the cast",
        ],
    },
    "Q-UI-20": {
        "batch": "board-pieces",
        "title": "the territory text's colour and contrast, measured",
        "may_write_saved_files": False,
        "count": None,
        "reads": {"colour-census": 1, "greyscale-census": 1, "text-rows": 1},
        "regions": ["board-area", "message-strip"],
        "actions": [
            *_REACH_BOARD,
            ("step", "shot board-contrast"),
            ("census", "board-area", 16),
            ("greyscale", "board-area", 16),
            ("text_rows", "message-strip"),
        ],
        "notes": [
            "contrast is derived by the catalogue from the recorded censuses; the walk records "
            "the raw colour and luminance distributions and the text-row heights",
        ],
    },
    "Q-PLY-04": {
        "batch": "board-pieces",
        "title": "counting the colours on the board and the options screen",
        "may_write_saved_files": False,
        "count": None,
        "reads": {"colour-census": 2},
        "regions": ["board-area", "full-stage"],
        "actions": [
            ("step", f"click {OPTIONS_CLICK[0]} {OPTIONS_CLICK[1]}"),
            ("wait", "options"),
            ("census", "full-stage", 16),
            * [("step", line) for line in BACK_TO_TITLE],
            *_REACH_BOARD,
            ("step", "shot board-for-colour-count"),
            ("census", "board-area", 16),
        ],
        "notes": [
            "the count is the recorded census; which colours are the players' is the catalogue's "
            "reading of it, never a rule claim",
        ],
    },

    # --- batch 3: play --------------------------------------------------------------------------
    "Q-UI-08": {
        "batch": "play",
        "title": "every panel with per-player figures, through one turn",
        "may_write_saved_files": False,
        "count": {"word": "screenshots", "at_least": 4, "measure": "shots"},
        "regions": ["board-area", "turn-panel", "phase-panel", "attack-panel"],
        "actions": [
            *_TURN_TO_ATTACK,
            ("step", "watch 545 502 250 70"),
            ("step", f"click! {ATTACK_PANEL_CLICK[0]} {ATTACK_PANEL_CLICK[1]}"),
            ("step", "shot panel-attack-result"),
            ("step", "watch 262 502 276 70"),
            ("step", QUIT_ATTACK_CLICKS),
            ("step", "shot panel-turn-menu"),
        ],
        "notes": [
            "the panels are shot at each phase of the tour's turn; the layout itself is in the "
            "score, which stays undecoded",
        ],
    },
    "Q-UI-12": {
        "batch": "play",
        "title": "the status texts and the button frames through one full turn",
        "may_write_saved_files": False,
        "count": {"word": "screenshots", "at_least": 4, "measure": "shots"},
        "reads": {"text-rows": 1},
        "regions": ["message-strip", "turn-panel", "phase-panel"],
        "actions": [
            *_TURN_TO_ATTACK,
            ("text_rows", "turn-panel"),
            ("step", "watch 545 502 250 70"),
            ("step", f"click! {ATTACK_PANEL_CLICK[0]} {ATTACK_PANEL_CLICK[1]}"),
            ("step", "shot status-attack-result"),
            ("step", "watch 262 502 276 70"),
            ("step", QUIT_ATTACK_CLICKS),
            ("step", "shot status-turn-menu"),
            ("step", f"click! {PASS_CLICK[0]} {PASS_CLICK[1]}"),
            ("step", "shot status-after-pass"),
        ],
        "notes": [
            "annotated screenshots: the shots carry the status texts of each phase; the strip and "
            "panel text rows are measured by pixels",
        ],
    },
    "Q-UI-13": {
        "batch": "play",
        "title": "the computer's turns, timed",
        "may_write_saved_files": False,
        # a proxy: the pixels do not identify a computer turn; the walk counts its own PASS clicks and
        # derives the turns from the default seats (three computer players, F003's options table)
        "count": {"word": "computer turns", "at_least": 20, "measured": "computer turns derived from passes",
                  "measure": "computer turns derived from passes"},
        "timing": "frame-timed",
        "regions": ["message-strip", "phase-panel", "board-area"],
        "actions": [
            *_REACH_BOARD,
            ("composite", "computer_turns", {"passes": 7, "watch": ["message-strip", "phase-panel",
                                                                    "board-area"],
                                             "seconds": 25, "interval": 0.25}),
        ],
        "notes": [
            "seven passes at the default seats are 21 computer turns (three between two human "
            "turns); the watch records every change of the watched regions with its timestamp, so "
            "the pauses show as the gaps between changes",
            "timings are wall-clock readings at speed = normal, the unlocked default (the record "
            "observes the options file equal to the shipped one, which is that default, F003)",
        ],
    },
    "Q-UI-15": {
        "batch": "play",
        "title": "holding, playing and discarding cards",
        "may_write_saved_files": False,
        "count": {"word": "screenshots", "at_least": 1, "measure": "shots"},
        "regions": ["message-strip"],
        "actions": [
            *_REACH_BOARD,
            ("composite", "card_turns", {"turns": 10}),
        ],
        "notes": [
            "the hand screen is not walked: the turn menu's CARD button has no measured point "
            "(E002's tour never used it; F003's Screens table says so), and it stays unmeasured "
            "rather than guessed",
            "the walk plays up to 10 aggressive turns, clicks CONTINUE after each pass and shots "
            "the message strip each time it changed; whether a shot shows a card award is the "
            "catalogue's reading of it, not the recorder's",
        ],
    },
    "Q-UI-16": {
        "batch": "play",
        "title": "the battle text updates and pauses, timed",
        "may_write_saved_files": False,
        "count": {"word": "attacks", "at_least": 20, "measure": "attacks"},
        "timing": "frame-timed",
        "regions": ["attack-panel", "message-strip"],
        "actions": [
            *_REACH_BOARD,
            ("composite", "attack_exchanges", {"turns": 8, "exchanges": 3, "need": 20,
                                               "watch": "attack-panel"}),
        ],
        "notes": [
            "one attack is one click on the ATTACK button (F011's reading); the watch records the "
            "battle panel's change with its timestamp around each click",
            "the exchanges a turn can give end when the target dies or the attacker is down to 1 "
            "(the game stops accepting); the walk continues over up to 8 turns until 20 are "
            "recorded",
            "timings are wall-clock readings at speed = normal (the unlocked default, F003)",
        ],
    },

    # --- batch 4: events and end ----------------------------------------------------------------
    "Q-UI-06": {
        "batch": "events-end",
        "title": "the event message, flash and sound, frame-timed",
        "may_write_saved_files": False,
        # a proxy: which event a large change is cannot be decided by pixels (R3, round 2)
        "count": {"word": "events", "at_least": 5, "measured": "flash candidates",
                  "measure": "flash candidates"},
        "timing": "frame-timed",
        "regions": ["message-strip", "board-area"],
        "actions": [
            *_REACH_BOARD,
            ("composite", "event_watch", {"turns": 30, "need": 5, "word": "flash candidates",
                                          "watch": ["message-strip", "board-area"]}),
        ],
        "notes": [
            "an event is not identified by pixels: the walk counts flash candidates (poll ticks in "
            "which a watched region changed over a large share of its pixels) and shots each one; a "
            "candidate may be an ordinary redraw or one of a flash's two transitions, so the row's "
            "'at least 5 events' is proxied, never claimed, and F020's entry is narrowed",
            "events are random at the one frequency the unregistered build allows (F019); a walk "
            "that sees fewer than the target records fewer and is re-run, never padded",
            "timings are wall-clock readings at speed = normal (the unlocked default, F003)",
        ],
    },
    "Q-UI-07": {
        "batch": "events-end",
        "title": "the centre event's message and flash",
        "may_write_saved_files": False,
        "count": {"word": "centre moves", "at_least": 5, "measured": "centre-flash candidates",
                  "measure": "centre-flash candidates"},
        "regions": ["message-strip", "board-area"],
        "actions": [
            *_REACH_BOARD,
            ("composite", "event_watch", {"turns": 30, "need": 5,
                                          "word": "centre-flash candidates",
                                          "count_regions": ["board-area"],
                                          "watch": ["message-strip", "board-area"]}),
        ],
        "notes": [
            "a centre move is not decidable by pixels: the walk counts the board-area flash "
            "candidates (the region the centre flash is drawn in) and the record says so; the row's "
            "'at least 5 centre moves' is proxied by 5 centre-flash candidates, never claimed as "
            "identified centre moves, and F020's entry is narrowed",
            "the catalogue describes what the recorded shots and timestamps show",
        ],
    },
    "Q-UI-11": {
        "batch": "events-end",
        "title": "the end screens after a win, a loss and a concession",
        "may_write_saved_files": True,   # the loss path credits a loss (F003)
        "count": {"word": "screenshots", "at_least": 1, "measure": "shots"},
        "actions": [
            *_REACH_BOARD,
            ("step", f"click {NEWGAME_CLICK[0]} {NEWGAME_CLICK[1]}"),
            ("step", "settle"),
            ("step", "shot end-loss-notice"),
        ],
        "notes": [
            "the loss notice is the end state this walk reaches; a win and a concession are not "
            "reached (no run in this repository has played to a win, F003; the surrender offer "
            "depends on a position the walk cannot craft), and the catalogue says so",
        ],
    },
    "Q-UI-14": {
        "batch": "events-end",
        "title": "looking for an event log over one long session",
        "may_write_saved_files": False,
        "absence": True,
        "count": {"word": "screenshots", "at_least": 9, "measure": "shots"},
        "reads": {"absence-tour": 1},
        "actions": [
            ("step", "shot title"),
            ("step", f"click {OPTIONS_CLICK[0]} {OPTIONS_CLICK[1]}"),
            ("wait", "options"),
            ("step", "shot options"),
            * [("step", line) for line in BACK_TO_TITLE],
            ("step", f"click {SCORES_CLICK[0]} {SCORES_CLICK[1]}"),
            ("step", "settle"),
            ("step", "shot scores"),
            ("step", f"click! {SCORES_RETURN_CLICK[0]} {SCORES_RETURN_CLICK[1]}"),
            ("step", "settle"),
            *_REACH_BOARD,
            ("composite", "computer_turns", {"passes": 5, "watch": ["message-strip", "phase-panel"],
                                             "seconds": 25, "interval": 0.25, "shots": True}),
            ("step", "shot board-long-session"),
        ],
        "notes": [
            "absence walk: the tour visits the title, options, scores, setup, board and the turn "
            "phases over a long session (five passes of computer turns), and shots each screen "
            "visited (nine: title, options, scores, one per pass, and the board); the record names "
            "the screenshots and nothing more: whether a list-of-events control is on any of them is "
            "the catalogue's reading, made by inspecting them (R7, round 2)",
        ],
    },
    "Q-UI-21": {
        "batch": "events-end",
        "title": "reference screenshots in setup, mid-game, battle and end states",
        "may_write_saved_files": True,   # the end state here is the loss notice (F003)
        "states": ["setup", "mid-game", "battle", "end"],
        "actions": [
            ("step", f"click {NEWGAME_CLICK[0]} {NEWGAME_CLICK[1]}"),
            ("step", "settle"),
            ("step", "shot state-setup"),
            ("step", f"click! {PLAY_CLICK[0]} {PLAY_CLICK[1]}"),
            ("step", "watch 0 0 800 495"),
            ("step", "settle 4"),
            ("step", "shot state-mid-game"),
            ("step", PLACE_WATCH),
            ("step", PLACE_CLICK),
            ("step", "watch 262 502 276 70"),
            ("step", f"click! {ALL_CLICK[0]} {ALL_CLICK[1]}"),
            ("step", f"click! {PLACE_DONE_CLICK[0]} {PLACE_DONE_CLICK[1]}"),
            ("step", "settle"),
            ("step", f"attack-picked {PLACE_COUNTRIES}"),
            ("step", "shot state-battle"),
            ("step", f"click {NEWGAME_CLICK[0]} {NEWGAME_CLICK[1]}"),
            ("step", "settle"),
            ("step", "shot state-end"),
        ],
        "notes": [
            "the board's look is bitmaps in the cast, which stays undecoded: the observation is "
            "the reference screenshots themselves",
            "the end state reached is the loss notice; a win screen is not reached by this walk",
        ],
    },

    # --- batch 5: inputs and sounds -------------------------------------------------------------
    "Q-UI-09": {
        "batch": "inputs-sounds",
        "title": "attempts at each illegal action, and their messages",
        "may_write_saved_files": False,
        "count": {"word": "attempts", "at_least": 3, "measure": "attempts"},
        "regions": ["message-strip", "board-area"],
        "actions": [
            *_TURN_TO_ATTACK,
            ("step", "watch 265 530 270 26"),
            ("step", "shot illegal-before"),
            ("step", "click-any? 400 300 100 100 700 200"),
            ("step", "shot illegal-attempt-1"),
            ("step", "click-any? 60 60 750 60 400 450"),
            ("step", "shot illegal-attempt-2"),
            ("step", "click-any? 200 300 600 300 300 200"),
            ("step", "shot illegal-attempt-3"),
            ("census", "message-strip", 16),
        ],
        "notes": [
            "the attempts are clicks the game may refuse or ignore: points over water and over "
            "the wrong side while the attack panel is up; `click-any?` only notes a group that "
            "changed nothing, so the walk never aborts on a refusal",
            "the error message of each attempt is in the recorded shots; the strip's census is "
            "recorded beside them",
        ],
    },
    "Q-UI-17": {
        "batch": "inputs-sounds",
        "title": "the sound switch, and the events sounds answer",
        "may_write_saved_files": False,
        "count": None,
        "reads": {"ear-toggle": 1},
        "actions": [
            ("step", f"click {OPTIONS_CLICK[0]} {OPTIONS_CLICK[1]}"),
            ("wait", "options"),
            ("step", "shot sound-before"),
            ("step", f"click {EAR_CLICK[0]} {EAR_CLICK[1]}"),
            ("step", "settle"),
            ("step", "shot sound-after"),
            ("step", f"click {EAR_CLICK[0]} {EAR_CLICK[1]}"),
            ("step", "settle"),
            ("step", "shot sound-restored"),
        ],
        "notes": [
            "the driver runs with audio off (no sound device in its display namespace), so the "
            "table of events against sounds is recorded as: the switch's reaction on the screen, "
            "and the note that sound capture needs a driver change; the record says audio was off",
            "the ear switch's point comes from the committed exploration commands (E002 explore "
            "s2.cmd-0003) and is verified at run time by the click's recorded reaction",
        ],
    },
    "Q-UI-18": {
        "batch": "inputs-sounds",
        "title": "inputs against actions, and measured hit areas",
        "may_write_saved_files": False,
        "count": {"word": "bands with a hover reaction", "at_least": 3, "measure": "labels"},
        "hit_areas": True,
        "regions": ["bottom-bar", "return-button", "turn-menu-band"],
        "actions": [
            ("hover_map", "bottom-bar", 12, (578, 590)),
            ("step", f"click {OPTIONS_CLICK[0]} {OPTIONS_CLICK[1]}"),
            ("wait", "options"),
            ("hover_map", "return-button", 12, (525, 535)),
            * [("step", line) for line in BACK_TO_TITLE],
            *_TURN_TO_ATTACK,
            ("step", "watch 545 502 250 70"),
            ("step", f"click! {ATTACK_PANEL_CLICK[0]} {ATTACK_PANEL_CLICK[1]}"),
            ("step", "watch 262 502 276 70"),
            ("step", QUIT_ATTACK_CLICKS),
            ("step", "shot turn-menu"),
            ("hover_map", "turn-menu-band", 12, (524, 536)),
            ("step", f"click! {PASS_CLICK[0]} {PASS_CLICK[1]}"),
        ],
        "notes": [
            "the hit areas are measured by hover: at each grid point the recorder moves the "
            "pointer and records whether the watched band reacted (the highlight the game draws "
            "under the pointer); no grid point is clicked, so the walk fires no action",
            "the Soleau label's area is refused by the step language and its points are skipped; "
            "the record counts the label bands (the measured click points +/- 40 px) in which a "
            "point reacted",
            "the click hit areas proper are in the score (not decoded); the hover-reactive area "
            "is what this walk measures",
        ],
    },
}

FRAME_TIMED = "frame-timed"


def question_rows(path=QUESTIONS):
    """{id: {sources, task, corroboration, confidence}} for every Q- row of pro-static.md."""
    rows = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| (Q-[A-Z]+-\d+) \|", line)
        if m:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows[m.group(1)] = {"sources": cells[1], "task": cells[2],
                                "corroboration": cells[3], "confidence": cells[4]}
    return rows


def batch_of(qid):
    return WALKS[qid]["batch"]


def step_lines(spec):
    """The step-language lines of one spec's actions, in order (the recorder's `step` items)."""
    return [text for kind, *rest in spec["actions"] if kind == "step" for text in [rest[0]]]


def expects_of(spec):
    """The known screens the walk waits for, complete() requires, title always included."""
    names = {"title"}
    for kind, *rest in spec["actions"]:
        if kind == "wait":
            names.add(rest[0])
    return sorted(names)
