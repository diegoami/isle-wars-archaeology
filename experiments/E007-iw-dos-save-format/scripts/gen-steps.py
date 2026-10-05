#!/usr/bin/env python3
"""Write the step scripts of the E007 arms into ../steps/ (never replacing one that exists with other bytes).

The pieces are those of E005's scripts (`experiments/E005-iw-dos-state-inventory/steps/turn.steps`,
`save-load.steps`, `save-normal-3.steps`), whose coordinates E005 found:
  level list: Easy 168, Normal 185, Hard 202, Hardest 219 (x 315); starting armies: 1 at 169, 3 at 186,
  6 at 203, 10 at 220; the board's buttons Scores 412, Sound 459, Speed 507, Save 554, Quit 602 (y 20);
  the Speed panel: Faster 459, Slower 575; the turn menu: ATTACK 272,323, PASS 338,325, CARD 369,325.
E007's own findings (explore x03, x06; measurements/explore/): a click away from the buttons (330,330) closes the
Speed panel (a click on its value box did not); the CARD button shows the hand or `YOU HAVE NO CARDS...` at the
turn menu and PASS still works after it.

Usage: gen-steps.py   (writes steps/<arm>.steps for every arm below)
"""
import sys
from pathlib import Path

STEPS = Path(__file__).resolve().parents[1] / "steps"
LEVEL_Y = {"easy": 168, "normal": 185, "hard": 202, "hardest": 219}
ARMIES_Y = {1: 169, 3: 186, 6: 203, 10: 220}
HUMAN = "until 390 10 230 20 170 170 170 800 150"      # the human turn's button panel (E005)


def head(level, armies, note):
    return f"""# {note}
click-change 60 32
until 272 138 80 18 170 85 0 800
wait-stable
shot select-level
click-change 315 {LEVEL_Y[level]}
shot starting-armies
click-change 315 {ARMIES_Y[armies]}
shot board-before-start
files
click-change 510 22
{HUMAN}
wait-stable
shot human-turn
files
"""


def save(tag):
    return f"click-change 554 20\nshot save-{tag}\nfiles\n"


def place_all():
    return "choose-attack\nclick-mine\nrclick-mine\nclick-change 284 331\n"


def pass_turn(tag):
    return f"click 338 325\nwait-change 10\nwait-stable\n{HUMAN}\nwait-stable\nshot human-turn-{tag}\n"


def cards(tag):
    return f"click-change 369 325\nshot cards-{tag}\n"


def attack_turn(tag):
    """E005's `turn` arm: place all, attack until the move-in panel, move in, PASS (Blue draws), the computer turns."""
    return f"""choose-attack
click-mine
rclick-mine
shot place-how-many-{tag}
click-change 284 331
shot place-turn-menu-{tag}
click-change 272 323
click-target
shot attack-from-where-{tag}
click-mine
shot attack-ready-{tag}
click-until 283 323 258 305 155 40 255 255 85 300
shot attack-result-{tag}
files
click-change 284 331
until 270 310 140 30 170 0 0 150 20
wait-stable
shot after-move-in-{tag}
click 338 325
wait-change 10
wait-stable
shot draws-card-{tag}
wait-change 10
wait-stable
shot click-to-continue-{tag}
click-change 335 323
shot ai-turn-first-{tag}
wait-change 10
shot ai-turn-second-{tag}
{HUMAN}
wait-stable
shot human-turn-{tag}
"""


ARMS = {}
for level, armies in (("easy", 1), ("normal", 1), ("hard", 1), ("hardest", 1), ("easy", 3), ("easy", 6), ("easy", 10),
                      ("hard", 6)):
    ARMS[f"sv-{level}-{armies}"] = (head(level, armies, f"arm sv-{level}-{armies}: {level}, {armies} starting armies, "
                                       "Save at the first human turn (T16)") + save("turn1"))
ARMS["sv-speed-faster"] = (head("easy", 1, "arm sv-speed-faster: Easy, 1; Speed Faster once, the panel closed, Save (T16)")
                           + "click-change 507 20\nshot speed-panel\nclick-change 459 20\nshot speed-faster\n"
                             "click 330 330\nwait-change 10\nwait-stable\nshot speed-closed\n" + save("turn1"))
ARMS["sv-speed-slower"] = (head("easy", 1, "arm sv-speed-slower: Easy, 1; Speed Slower once, the panel closed, Save (T16)")
                           + "click-change 507 20\nshot speed-panel\nclick-change 575 20\nshot speed-slower\n"
                             "click 330 330\nwait-change 10\nwait-stable\nshot speed-closed\n" + save("turn1"))
ARMS["sv-sound-off"] = (head("easy", 1, "arm sv-sound-off: Easy, 1; Sound clicked once, Save (T16)")
                        + "click-change 459 20\nshot sound-clicked\nwait-stable\n" + save("turn1"))
ARMS["pass-3"] = (head("easy", 1, "arm pass-3: Easy, 1; three human turns of place all and PASS (no attack), Save and the CARD "
                                  "button at each (T16)")
                  + save("turn1") + place_all() + cards("turn1") + pass_turn("2")
                  + save("turn2") + place_all() + cards("turn2") + pass_turn("3")
                  + save("turn3") + place_all() + cards("turn3") + pass_turn("4")
                  + save("turn4"))
ARMS["attack-pass"] = (head("easy", 1, "arm attack-pass: Easy, 1; turn 1 attack (as E005's turn arm), then two turns of place all and "
                                       "PASS; Save and the CARD button at each (T16)")
                       + save("turn1") + attack_turn("2")
                       + save("turn2") + place_all() + cards("turn2") + pass_turn("3")
                       + save("turn3") + place_all() + cards("turn3") + pass_turn("4")
                       + save("turn4"))
ARMS["attack-2"] = (head("easy", 1, "arm attack-2: Easy, 1; turn 1 attack (as E005's turn arm), Save and the CARD button at turn 2 (T16; "
                                    "attack-pass, which goes on to turn 3, aborted at the turn-3 Save in E007-r0013)")
                    + save("turn1") + attack_turn("2") + save("turn2") + place_all() + cards("turn2"))
ARMS["pass-6-normal"] = (head("normal", 3, "arm pass-6-normal: Normal, 3; six human turns of place all and PASS, Save at each (T16)")
                         + "".join(save(f"turn{k}") + place_all() + pass_turn(str(k + 1)) for k in range(1, 7))
                         + save("turn7"))

# The crafted arms (--crafted POSITION): the option box, the save placed, Load saved game, the loaded board, Save again.
LOAD = """put-save
files
click-change 60 58
shot after-load
until 390 10 230 20 170 170 170 800 150
wait-stable
shot loaded-human-turn
files
"""
ARMS["load-crafted"] = ("# arm load-crafted: the option box; the crafted save placed in the run copy (--crafted); Load saved game; "
                        "the loaded board; Save again (T16, I3)\n" + LOAD + save("resave"))
ARMS["load-crafted-cards"] = ("# arm load-crafted-cards: as load-crafted, then place all and the CARD button (the hand) (T16, I3)\n"
                              + LOAD + save("resave") + place_all() + cards("loaded"))
ARMS["load-crafted-speed"] = ("# arm load-crafted-speed: as load-crafted, then the Speed panel (its value) (T16, I3)\n" + LOAD
                              + "click-change 507 20\nshot speed-panel\nclick 330 330\nwait-change 10\nwait-stable\n" + save("resave"))

ARMS["load-crafted-sound"] = ("# arm load-crafted-sound: as load-crafted, then the Sound button once (its label shows the state it toggles to) "
                              "(T16, I3)\n" + LOAD + "click-change 459 20\nshot sound-clicked\nwait-stable\n" + save("resave"))

if __name__ == "__main__":
    for arm, text in ARMS.items():
        target = STEPS / f"{arm}.steps"
        if target.exists():
            if target.read_text() != text:
                sys.exit(f"{target.name} exists with other bytes; nothing replaced")
            continue
        target.write_text(text)
        print("wrote", target.name)
