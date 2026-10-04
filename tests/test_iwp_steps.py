"""The W4a extension of the cycle (E002), tested without the game or a display:

- steps.py: what a step script may say, and the click areas it can never touch;
- the step runner of Cycle (candidate search, the notice-screen rule, reading a game file);
- the exploration session's step files, and the choice of artifact set and intervention level of a record;
- snapshot_tree refusing a fifo, a socket or any non-regular entry instead of hanging on it (#27).

Nothing here starts the game, Xvfb or Wine, and nothing reads or writes the real install or prefix: the
fixtures in iwp_fixtures.py build their own.
"""
import glob
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import textwrap
import threading
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from iwp_fixtures import World, cycle, locations, ROOT, safeio

sys.path.insert(0, str(ROOT / "runtime" / "iwp" / "spike"))
import steps  # noqa: E402

sys.path.insert(0, str(ROOT / "tests"))
import test_runs  # noqa: E402


def parse_one(text):
    return steps.parse_line(text)


class StepsParseTest(unittest.TestCase):
    def test_every_committed_script_parses_and_clicks_nowhere_forbidden(self):
        scripts = sorted(glob.glob(str(ROOT / "experiments" / "E002-iwp-state-inventory" / "scripts" / "*.steps")))
        self.assertGreaterEqual(len(scripts), 9)
        for path in scripts:
            with self.subTest(script=Path(path).name):
                parsed = steps.parse(Path(path).read_text())
                self.assertTrue(parsed)
                for step in parsed:
                    points = step.args[5:] if step.op.startswith("click-until") else (
                        step.args[1:] if step.op == "clicks" else
                        step.args if step.op.startswith("click") or step.op == "move" else ())
                    for i in range(0, len(points) - 1, 2):
                        self.assertIsNone(steps.forbidden(points[i], points[i + 1]), (step, points[i:i + 2]))

    def test_the_soleau_games_label_cannot_be_clicked_at_parse_time(self):
        x, y, w, h = steps.FORBIDDEN["Soleau Games label on the title screen"]
        for point in ((x, y), (x + w - 1, y + h - 1), (470, 585)):
            for op in ("click", "click!", "move"):
                with self.subTest(op=op, point=point), self.assertRaises(steps.StepError):
                    parse_one(f"{op} {point[0]} {point[1]}")
            with self.assertRaises(steps.StepError):
                parse_one(f"click-any 10 10 {point[0]} {point[1]}")
            with self.assertRaises(steps.StepError):
                parse_one(f"click-until 1 2 3 4 5 {point[0]} {point[1]}")
            with self.assertRaises(steps.StepError):
                parse_one(f"clicks 3 {point[0]} {point[1]}")
        # the neighbours of the label are other controls: Options and Scores stay clickable
        for point in ((x - 1, y), (x + w, y), (x, y - 1), (320, 585), (620, 585)):
            self.assertIsNotNone(parse_one(f"click {point[0]} {point[1]}"), point)

    def test_steps_that_are_not_allowed_are_refused(self):
        bad = ["jump 1 2", "click 800 10", "click 10 600", "click -1 5", "click 5", "key dollar", "key $", "key ctrl+q",
               "key a b", "shot Title", "shot a/b", "shot", "file /etc/passwd", "file ../x", "file a//b", "file a b",
               "settle 0", "settle 61", "settle x", "watch 0 0 801 5", "watch 1 2 3", "watch 0 0 0 5",
               "click-any 1", "click-until 1 2 3 4 5", "click-until 300 0 0 0 1 5 5", "click-until 0 0 0 0 0 5 5",
               "clicks 1 5 5", "clicks 61 5 5", "title now", "proc x", "changes x"]
        for line in bad:
            with self.subTest(line=line), self.assertRaises(steps.StepError):
                parse_one(line)

    def test_allowed_steps_and_the_comment_and_blank_lines(self):
        good = {"settle": (), "settle 4": (4,), "move 5 6": (5, 6), "click 5 6": (5, 6), "click! 5 6": (5, 6),
                "key Return": ("Return",), "key Next": ("Next",), "key a": ("a",), "shot a-b1": ("a-b1",),
                "file xtras/Isledft.dat": ("xtras/Isledft.dat",), "watch 1 2 3 4": (1, 2, 3, 4), "watch all": (),
                "clicks 20 744 481": (20, 744, 481), "click-any 1 2 3 4": (1, 2, 3, 4),
                "click-any? 1 2": (1, 2), "click-until 168 168 168 24 1000 5 6": (168, 168, 168, 24, 1000, 5, 6),
                "click-until? 0 0 0 0 1 5 6 7 8": (0, 0, 0, 0, 1, 5, 6, 7, 8), "title": (), "proc": (), "changes": ()}
        for line, args in good.items():
            self.assertEqual(parse_one(line + "   # a comment").args, args, line)
        self.assertEqual([s.op for s in steps.parse("\n# only a comment\n\nsettle\n  \nshot a\n")], ["settle", "shot"])
        with self.assertRaises(steps.StepError) as caught:
            steps.parse("settle\nshot a\nbogus\n")
        self.assertIn("line 3", str(caught.exception))


class FakeWorld(World):
    """A cycle whose screen and mouse are replaced by a tiny model: a click at one of `works` changes
    the watched area, a click anywhere else does nothing."""

    def setUp(self):
        super().setUp()
        self.game = self.game_copy({"a.txt": b"alpha"})
        self.clicks, self.pos, self.changed = [], (0, 0), False
        self.works, self.paint = set(), (b"\x00\x00\x00", b"\xa0\xa0\xa0")
        self.notice = False

    def make(self, argv=("--experiment", "E002")):
        args = cycle.parser().parse_args(list(argv))
        made = cycle.Cycle(args, "E002-test", self.prefix, self.tmp / "b2", self.install)
        self.addCleanup(shutil.rmtree, made.workdir, True)
        made.screen.raw = self.raw
        made.screen.notice_up = lambda: self.notice
        made.screen.capture = lambda directory, name, exist="new", create_below=None: ("p" * 64, "f" * 64)
        return made

    def raw(self, crop=None):
        size = (crop[2] * crop[3]) if crop else 100
        return self.paint[1 if self.changed else 0] * size

    def fake_run(self, cmd, **kw):
        if cmd[:2] == ["xdotool", "mousemove"]:
            self.pos = (int(cmd[2]), int(cmd[3]))
        elif cmd[:2] == ["xdotool", "click"]:
            self.clicks.append(self.pos)
            self.changed = self.changed or self.pos in self.works
        return mock.MagicMock(returncode=0, stdout=b"", stderr=b"")

    def run_in(self, made, line):
        quick = lambda condition, timeout, interval=0.1: 0.0 if condition() else None  # noqa: E731
        with mock.patch.object(cycle, "run", self.fake_run), mock.patch.object(cycle, "poll", quick), \
                redirect_stdout(io.StringIO()):
            made.run_step(steps.parse_line(line))


class CandidateSearchTest(FakeWorld):
    def test_click_any_stops_at_the_first_candidate_that_changed_the_watched_area(self):
        made = self.make()
        self.works = {(20, 20), (30, 30)}
        self.run_in(made, "watch 0 0 4 4")
        self.run_in(made, "click-any 10 10 20 20 30 30")
        self.assertEqual(self.clicks, [(10, 10), (20, 20)])      # (30, 30) would have worked, and was never clicked
        self.assertIn("20,20 (number 2 of 3)", made.obs[-1]["value"])

    def test_a_search_records_the_point_it_stopped_at(self):
        made = self.make()
        self.works = {(20, 20)}
        self.run_in(made, "watch 0 0 4 4")
        self.assertIsNone(made.picked)
        self.run_in(made, "click-any 10 10 20 20")
        self.assertEqual(made.picked, (20, 20))

    def test_click_any_aborts_the_run_when_no_candidate_works(self):
        made = self.make()
        self.run_in(made, "watch 0 0 4 4")
        with self.assertRaises(cycle.Abort):
            self.run_in(made, "click-any 10 10 20 20")
        self.assertEqual(self.clicks, [(10, 10), (20, 20)])
        self.assertTrue(made.status.startswith("aborted: click-any: none of the 2 candidates worked"), made.status)

    def test_the_question_mark_form_only_notes_a_failure(self):
        made = self.make()
        self.run_in(made, "click-any? 10 10")
        self.assertEqual(made.status, "running")
        self.assertIn("none of the 1", made.obs[-1]["value"])
        self.run_in(made, "watch 0 0 4 4")
        self.run_in(made, "click-until? 160 160 160 8 1 10 10")
        self.assertEqual(made.status, "running")

    def test_click_until_needs_enough_pixels_of_the_colour(self):
        made = self.make()
        self.works = {(5, 5)}
        self.run_in(made, "watch 0 0 4 4")                          # 16 pixels
        with self.assertRaises(cycle.Abort):                        # 17 are asked for: one more than there are
            self.run_in(made, "click-until 160 160 160 0 17 5 5")
        made = self.make()
        self.changed = False
        self.run_in(made, "watch 0 0 4 4")
        self.run_in(made, "click-until 160 160 160 0 16 1 1 5 5")   # exactly 16 pixels of the colour
        self.assertEqual(self.clicks[-2:], [(1, 1), (5, 5)])

    def test_click_until_checks_the_colour_within_the_tolerance_only(self):
        made = self.make()
        self.works = {(5, 5)}
        self.run_in(made, "watch 0 0 4 4")
        with self.assertRaises(cycle.Abort):                        # the pixels are 160; 150 +- 9 does not reach them
            self.run_in(made, "click-until 150 150 150 9 1 5 5")
        made = self.make()
        self.changed = False
        self.run_in(made, "watch 0 0 4 4")
        self.run_in(made, "click-until 150 150 150 10 1 5 5")       # 150 +- 10 does
        self.assertIn("5,5", made.obs[-1]["value"])

    def test_click_until_without_a_watched_area_aborts(self):
        made = self.make()
        with self.assertRaises(cycle.Abort):
            self.run_in(made, "click-until 1 2 3 4 5 10 10")
        self.assertEqual(self.clicks, [])


class AttackPickedTest(FakeWorld):
    """attack-picked against a small model of the turn: the menu, "Select Country To Attack", "Attack From
    Where?" and the QUIT ATTACK panel. The model takes a target only if it is in `targets`, and an attacker
    only if the pair is in `pairs`; anything else changes nothing, as the game does."""

    def setUp(self):
        super().setUp()
        self.state, self.target, self.targets, self.pairs, self.log = "menu", None, set(), set(), []
        self.picked = (42, 330)

    def raw(self, crop=None):
        if crop is None:
            return b"\x00" * 30
        size = crop[2] * crop[3]
        if tuple(crop) == cycle.TARGET_PANEL:
            return {"menu": b"\x00", "select": b"\x01", "fromwhere": b"\x02", "ready": b"\x02"}[self.state] * (size * 3)
        if tuple(crop) == cycle.CENTRE_PANEL and self.state == "ready":
            return bytes(cycle.QUIT_ATTACK[0]) * size
        return b"\x00" * (size * 3)

    def fake_run(self, cmd, **kw):
        if cmd[:2] == ["xdotool", "mousemove"]:
            self.pos = (int(cmd[2]), int(cmd[3]))
        elif cmd[:2] == ["xdotool", "click"]:
            self.log.append((self.state, self.pos))
            if self.pos == cycle.CANCEL_BUTTON and self.state in ("select", "fromwhere"):
                self.state = "menu"
            elif self.pos == cycle.ATTACK_BUTTON and self.state == "menu":
                self.state = "select"
            elif self.state == "select" and self.pos in self.targets:
                self.state, self.target = "fromwhere", self.pos
            elif self.state == "fromwhere" and (self.target, self.pos) in self.pairs:
                self.state = "ready"
        return mock.MagicMock(returncode=0, stdout=b"", stderr=b"")

    def attack(self, made, line):
        made.picked = self.picked
        self.run_in(made, line)

    def test_the_first_target_that_the_game_takes_with_the_picked_attacker_is_attacked(self):
        made = self.make()
        self.targets = {(10, 10), (20, 20), (30, 30)}
        self.pairs = {((20, 20), self.picked)}
        self.attack(made, "attack-picked 5 5 10 10 20 20 30 30")
        self.assertEqual(self.state, "ready")
        # 5,5 is not taken as a target; 10,10 is, but the picked point cannot attack it: Cancel; 20,20 works
        states = [(st, pos) for st, pos in self.log]
        self.assertIn(("fromwhere", self.picked), states)
        self.assertIn(("fromwhere", cycle.CANCEL_BUTTON), states)
        self.assertNotIn((30, 30), [pos for _, pos in states])        # never reached: (20, 20) worked
        self.assertIn("20,20 from 42,330 (number 3 of 4)", made.obs[-1]["value"])

    def test_a_target_that_the_game_refuses_is_followed_by_cancel_and_the_next_one(self):
        made = self.make()
        self.targets, self.pairs = {(20, 20)}, {((20, 20), self.picked)}
        self.attack(made, "attack-picked 5 5 20 20")
        self.assertEqual(self.state, "ready")
        self.assertEqual(self.log[:2], [("menu", cycle.ATTACK_BUTTON), ("select", (5, 5))])
        self.assertEqual(self.log[2], ("select", cycle.CANCEL_BUTTON))

    def test_the_run_aborts_when_no_target_fits(self):
        made = self.make()
        self.targets, self.pairs = {(10, 10)}, set()
        with self.assertRaises(cycle.Abort):
            self.attack(made, "attack-picked 5 5 10 10")
        self.assertEqual(self.state, "menu")                          # left where it started
        self.assertIn("none of the 2 targets was accepted", made.status)

    def test_it_needs_a_picked_point(self):
        made = self.make()
        with self.assertRaises(cycle.Abort):
            self.run_in(made, "attack-picked 5 5")
        self.assertEqual(self.log, [])


class ClickGuardTest(FakeWorld):
    def test_a_click_in_a_forbidden_area_is_refused_when_it_is_sent_too(self):
        made = self.make()
        x, y, w, h = steps.FORBIDDEN["Soleau Games label on the title screen"]
        with mock.patch.object(cycle, "run", self.fake_run), self.assertRaises(steps.StepError):
            made.click_at(x + 1, y + 1)
        self.assertEqual(self.clicks, [])

    def test_with_the_notice_screen_up_only_exit_game_may_be_clicked(self):
        made = self.make()
        self.notice = True
        ex, ey, ew, eh = cycle.EXIT_GAME
        quick = lambda condition, timeout, interval=0.1: 0.0 if condition() else None  # noqa: E731
        with mock.patch.object(cycle, "run", self.fake_run), mock.patch.object(cycle, "poll", quick), \
                redirect_stdout(io.StringIO()):
            for point in ((408, 527), (115, 586), (413, 586), (ex - 1, ey), (ex, ey - 1), (ex + ew, ey), (ex, ey + eh)):
                with self.subTest(point=point), self.assertRaises(steps.StepError):
                    made.click_at(*point)
            self.assertEqual(self.clicks, [])
            made.click_at(ex + ew // 2, ey + eh // 2)
            made.click_at(ex, ey)
            made.click_at(ex + ew - 1, ey + eh - 1)
        self.assertEqual(len(self.clicks), 3)
        self.notice = False
        with mock.patch.object(cycle, "run", self.fake_run), mock.patch.object(cycle, "poll", quick), \
                redirect_stdout(io.StringIO()):
            made.click_at(408, 527)                                  # the same place on another screen is fine
        self.assertEqual(len(self.clicks), 4)


class ReadGameFileTest(FakeWorld):
    def read(self, made, rel):
        before = len(made.obs)
        with redirect_stdout(io.StringIO()):
            made.read_game_file(rel)
        return {o["field"]: o["value"] for o in made.obs[before:]}

    def test_a_file_the_game_left_alone_is_never_dumped(self):
        made = self.make()
        self.write(self.install / "xtras" / "keep.dat", b"shipped bytes")
        self.write(self.game / "xtras" / "keep.dat", b"shipped bytes")
        seen = self.read(made, "xtras/keep.dat")
        self.assertEqual(seen["xtras/keep.dat: equals the install's file"], "yes")
        self.assertFalse(any("raw:bytes" in k or "changed byte offsets" in k for k in seen), seen)
        self.assertNotIn(b"shipped bytes".hex(), json.dumps(made.obs))

    def test_a_small_file_the_game_wrote_is_dumped_and_its_changed_offsets_named(self):
        made = self.make()
        self.write(self.install / "xtras" / "w.dat", b"1,0,0,2,")
        self.write(self.game / "xtras" / "w.dat", b"1,0,0,3,9")
        seen = self.read(made, "xtras/w.dat")
        self.assertEqual(seen["xtras/w.dat: changed byte offsets, install>game copy"], "0x6 32>33; appended at 0x8: 39")
        self.assertEqual(seen["raw:bytes[0x0:0x9] of xtras/w.dat as written by the game"], b"1,0,0,3,9".hex())

    def test_bytes_appended_or_cut_off_are_named(self):
        made = self.make()
        self.write(self.install / "xtras" / "grow.dat", b"1,0,2")
        self.write(self.game / "xtras" / "grow.dat", b"1,0,2,")
        self.assertEqual(self.read(made, "xtras/grow.dat")["xtras/grow.dat: changed byte offsets, install>game copy"],
                         "appended at 0x5: 2c")
        self.write(self.install / "xtras" / "cut.dat", b"1,0,2,")
        self.write(self.game / "xtras" / "cut.dat", b"1,0")
        self.assertEqual(self.read(made, "xtras/cut.dat")["xtras/cut.dat: changed byte offsets, install>game copy"],
                         "ends at 0x3, where the install's file goes on")

    def test_a_large_changed_file_gets_its_offsets_but_no_dump(self):
        made = self.make()
        old = bytes(range(100))
        self.write(self.install / "xtras" / "big.dat", old)
        self.write(self.game / "xtras" / "big.dat", old[:10] + b"\xff" + old[11:])
        seen = self.read(made, "xtras/big.dat")
        self.assertEqual(seen["xtras/big.dat: changed byte offsets, install>game copy"], "0xa 0a>ff")
        self.assertFalse(any("raw:bytes" in k for k in seen), seen)

    def test_a_new_small_file_is_dumped_and_a_missing_one_is_said_to_be_absent(self):
        made = self.make()
        self.write(self.game / "new.sav", b"abc")
        seen = self.read(made, "new.sav")
        self.assertTrue(seen["new.sav: equals the install's file"].startswith("no: the install has no such file"))
        self.assertEqual(seen["raw:bytes[0x0:0x3] of new.sav as written by the game"], b"abc".hex())
        self.assertIn("absent", self.read(made, "nothing.dat")["nothing.dat"])

    def test_a_link_is_not_read_through(self):
        made = self.make()
        self.write(self.tmp / "secret", b"x")
        os.symlink(self.tmp / "secret", self.game / "link.dat")
        self.assertIn("absent or not a plain file", self.read(made, "link.dat")["link.dat"])


class ScriptLoadTest(FakeWorld):
    def load(self, text, argv_extra=()):
        script = Path(tempfile.mkdtemp(dir=ROOT / "tests", prefix=".steps-")) / "t.steps"
        self.addCleanup(shutil.rmtree, script.parent, True)
        script.write_text(text)
        made = self.make(["--experiment", "E002", "--script", str(script), *argv_extra])
        with redirect_stdout(io.StringIO()):
            try:
                made.load_script()
            except cycle.Abort:
                pass
        return made

    def test_a_valid_script_is_parsed_and_its_hash_recorded(self):
        made = self.load("settle\nshot a\n")
        self.assertEqual(made.status, "running")
        self.assertEqual([s.op for s in made.steps], ["settle", "shot"])
        self.assertEqual(made.obs[0]["field"], "step script sha256")
        self.assertEqual(len(made.obs[0]["value"]), 64)

    def test_a_bad_or_empty_script_aborts_before_anything_starts(self):
        for text, why in (("settle\nbogus\n", "line 2"), ("# nothing\n", "no steps"), ("click 470 585\n", "forbidden")):
            with self.subTest(text=text):
                made = self.load(text)
                self.assertTrue(made.status.startswith("aborted: "), made.status)
                self.assertIn(why, made.status)
                self.assertFalse(made.steps)

    def test_a_script_outside_this_repository_is_refused(self):
        outside = self.tmp / "evil.steps"
        outside.write_text("settle\nshot a\n")
        made = self.make(["--experiment", "E002", "--script", str(outside)])
        with redirect_stdout(io.StringIO()), self.assertRaises(cycle.Abort):
            made.load_script()
        self.assertIn("outside this repository", made.status)


class SessionTest(FakeWorld):
    def start(self, made, folder):
        made.session_dir = folder
        outcome = {}

        real_sleep = cycle.time.sleep

        def go():
            with mock.patch.object(cycle.time, "sleep", lambda s: real_sleep(0.01)), \
                    redirect_stdout(io.StringIO()):
                made.session()
            outcome["done"] = True

        thread = threading.Thread(target=go, daemon=True)
        thread.start()
        return thread, outcome

    def test_step_files_are_run_in_order_results_are_written_and_quit_ends_the_session(self):
        made = self.make(["--experiment", "E002", "--explore", "--session", "--arm", "t"])
        folder = self.tmp / "explore"
        folder.mkdir()
        made.screen.capture = lambda directory, name, exist="new", create_below=None: ("p" * 64, "f" * 64)
        (folder / "t.cmd-0001.txt").write_text("watch 1 2 3 4\nshot one\n")
        (folder / "t.cmd-0002.txt").write_text("settle\nbogus\n")
        (folder / "t.cmd-0003.txt").write_text("quit\n")
        with mock.patch.object(cycle, "run", self.fake_run):
            thread, outcome = self.start(made, folder)
            thread.join(10)
        self.assertTrue(outcome.get("done"), "the session did not end on `quit`")
        first = (folder / "t.out-0001.txt").read_text()
        self.assertIn("watched area: x,y,w,h 1,2,3,4", first)
        self.assertTrue(first.rstrip().endswith("ok"), first)
        second = (folder / "t.out-0002.txt").read_text()
        self.assertIn("error: line 2: unknown step 'bogus'", second)
        self.assertNotIn("settle:", second)              # a script with a bad line runs none of its steps
        self.assertFalse((folder / "t.out-0003.txt").exists())

    def test_a_step_file_that_is_still_empty_is_waited_for_not_run(self):
        made = self.make(["--experiment", "E002", "--explore", "--session", "--arm", "t"])
        folder = self.tmp / "explore2"
        folder.mkdir()
        (folder / "t.cmd-0001.txt").write_text("")       # created, not yet written
        with mock.patch.object(cycle, "run", self.fake_run):
            thread, outcome = self.start(made, folder)
            thread.join(0.5)
            self.assertFalse((folder / "t.out-0001.txt").exists(), "an empty step file was taken for a finished one")
            (folder / "t.cmd-0001.txt").write_text("quit\n")
            thread.join(10)
        self.assertTrue(outcome.get("done"))

    def test_a_failed_click_bang_in_a_session_is_reported_and_the_session_goes_on(self):
        made = self.make(["--experiment", "E002", "--explore", "--session", "--arm", "t"])
        folder = self.tmp / "explore3"
        folder.mkdir()
        (folder / "t.cmd-0001.txt").write_text("click! 10 10\n")
        (folder / "t.cmd-0002.txt").write_text("quit\n")
        with mock.patch.object(cycle, "run", self.fake_run), \
                mock.patch.object(cycle, "poll", lambda c, t, i=0.1: 0.0 if c() else None):
            thread, outcome = self.start(made, folder)
            thread.join(10)
        self.assertTrue(outcome.get("done"))
        self.assertIn("error:", (folder / "t.out-0001.txt").read_text())
        self.assertEqual(made.status, "running")


class RecordTest(FakeWorld):
    def args(self, *argv):
        return cycle.parser().parse_args(list(argv))

    def test_the_set_a_run_is_recorded_under(self):
        self.assertEqual(cycle.record_set(self.args()), cycle.SET_ID)
        self.assertEqual(cycle.record_set(self.args("--input", "save-default")), cycle.SUCCESSOR_ID)
        self.assertEqual(cycle.record_set(self.args("--experiment", "E002", "--may-write-saved-files")), cycle.SUCCESSOR2_ID)
        self.assertEqual(cycle.record_set(self.args("--experiment", "E002")), cycle.SET_ID)

    def test_the_successor_sets_are_registered_with_the_files_they_declare(self):
        known = json.loads((ROOT / "artifacts" / "known.json").read_text())["sets"]
        by_id = {e["manifest"]["id"]: e["manifest"] for e in known}
        self.assertEqual(by_id[cycle.SUCCESSOR_ID]["runtime_writes"], ["xtras/Isledft.dat"])
        self.assertEqual(sorted(by_id[cycle.SUCCESSOR2_ID]["runtime_writes"]), ["xtras/Isledft.dat", "xtras/Islepro.skr"])
        for name in ("xtras/Isledft.dat", "xtras/Islepro.skr"):
            self.assertNotIn(name, [f["path"] for f in by_id[cycle.SUCCESSOR2_ID]["files"]])

    def test_an_e002_record_is_valid_run_1_with_the_screenshot_level(self):
        made = self.make(["--experiment", "E002", "--script", "experiments/E002-iwp-state-inventory/scripts/tour.steps",
                          "--may-write-saved-files", "--terminate", "kill"])
        made.fingerprint, made.restore_text, made.argv = {"wine": "wine-9.0"}, "restored", ["--experiment", "E002"]
        made.started = made.ended = "2026-10-04T10:00:00Z"
        made.status = "completed"
        shot = made.workdir / "before.png"
        shot.write_bytes(b"png")
        made.outputs = [("before.png", shot, "screenshot")]
        made.observe(4, "file", "xtras/Isledft.dat: size in bytes and sha256", "16 " + "a" * 64)
        with mock.patch.dict(os.environ, {"IWP_CYCLE_REP": "1"}):
            record = cycle.build_record(made, "abcdef123456", "local", "0" * 64)
            manifest = cycle.build_manifest(made)
        self.assertEqual(record["experiment"], "E002")
        self.assertEqual(record["artifact"]["set"], cycle.SUCCESSOR2_ID)
        self.assertEqual([i["level"] for i in record["interventions"]], ["I1"])
        self.assertEqual(manifest["experiment"], "E002")
        self.assertEqual(manifest["store"], "release:E002")
        folder = self.tmp / "runs" / "E002"
        folder.mkdir(parents=True)
        record["run_id"] = "E002-r0001"
        path = folder / "E002-r0001.json"
        path.write_text(json.dumps(record))
        self.assertEqual(test_runs.run_record_errors(path), [])
        record["interventions"] = []
        path.write_text(json.dumps(record))
        self.assertTrue(test_runs.run_record_errors(path))      # the check itself can fail

    def test_an_e001_record_keeps_its_i0_level(self):
        made = self.make(["--experiment", "E001"])
        made.fingerprint, made.restore_text, made.argv = {}, "r", []
        made.started = made.ended = "2026-10-04T10:00:00Z"
        made.status = "completed"
        with mock.patch.dict(os.environ, {"IWP_CYCLE_REP": "1"}):
            record = cycle.build_record(made, "abcdef123456", "local", "0" * 64)
        self.assertEqual(record["interventions"], [{"level": "I0", "what": "none"}])


class LocationsTest(World):
    def test_each_experiment_has_its_own_bundle_and_exploration_variable(self):
        env = {"IWP_PREFIX": str(self.prefix), "IWP_DIR": str(self.install), "E002_BUNDLES": str(self.tmp / "b2"),
               "E002_EXPLORE": str(self.tmp / "x2"), "E001_BUNDLES": str(self.tmp / "b1")}
        found = locations.locations(env, need_prefix=True, need_bundles=True, explore=True, experiment="E002")
        self.assertEqual(found["E002_BUNDLES"], self.tmp / "b2")
        self.assertEqual(found["E002_EXPLORE"], self.tmp / "x2")
        self.assertNotIn("E001_BUNDLES", found)
        with self.assertRaises(SystemExit):
            locations.locations({k: v for k, v in env.items() if k != "E002_BUNDLES"}, need_prefix=True,
                                need_bundles=True, experiment="E002")

    def test_the_confinement_applies_to_the_new_variables(self):
        env = {"IWP_PREFIX": str(self.prefix), "IWP_DIR": str(self.install),
               "E002_BUNDLES": str(self.checkout / "bundles")}
        with self.assertRaises(SystemExit):
            locations.locations(env, need_prefix=True, need_bundles=True, experiment="E002")
        env["E002_BUNDLES"] = str(self.install / "b")
        with self.assertRaises(SystemExit):
            locations.locations(env, need_prefix=True, need_bundles=True, experiment="E002")

    def test_an_experiment_id_is_checked_before_it_becomes_a_variable_name(self):
        for bad in ("E1", "e002", "E002; rm", "X002", ""):
            with self.subTest(bad=bad), self.assertRaises(SystemExit):
                locations.locations({"IWP_DIR": str(self.install)}, experiment=bad)

    def test_the_parser_takes_only_known_experiments(self):
        self.assertEqual(cycle.parser().parse_args([]).experiment, "E001")
        self.assertEqual(cycle.parser().parse_args(["--experiment", "E002"]).experiment, "E002")
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=io.StringIO()):
            cycle.parser().parse_args(["--experiment", "E003"])


class SnapshotRefusesNonRegularEntriesTest(unittest.TestCase):
    """#27: a fifo in the prefix made the after-launch snapshot block for ever."""

    CHILD = textwrap.dedent("""
        import importlib.util, os, stat, sys
        spec = importlib.util.spec_from_file_location("cycle", sys.argv[1])
        cycle = importlib.util.module_from_spec(spec)
        sys.modules["cycle"] = cycle
        spec.loader.exec_module(cycle)
        base = sys.argv[2]
        if sys.argv[3] == "swapped":
            # the entry is a regular file when listed and a fifo when read: lstat is made to say regular
            real = os.lstat
            def lstat(path, *a, **k):
                info = real(path, *a, **k)
                if str(path).endswith("pipe"):
                    return os.stat_result((stat.S_IFREG | 0o644,) + tuple(info)[1:])
                return info
            os.lstat = lstat
        try:
            if sys.argv[3] == "hash":
                cycle.file_size_and_sha256(os.path.join(base, "p"), "p")
            else:
                cycle.snapshot_tree(base)
        except cycle.UnsupportedEntry as exc:
            print("refused:", exc)
            sys.exit(0)
        print("read it")
        sys.exit(3)
    """)

    def child(self, base, mode):
        return subprocess.run([sys.executable, "-c", self.CHILD, str(ROOT / "runtime/iwp/spike/cycle.py"), str(base), mode],
                              capture_output=True, text=True, timeout=20)

    def test_a_fifo_makes_snapshot_tree_refuse_not_hang(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "ok.txt").write_text("fine")
            os.mkfifo(Path(tmp) / "pipe")
            done = self.child(tmp, "listed")          # a hang is a TimeoutExpired: the test fails
        self.assertEqual((done.returncode, done.stdout.split()[:1]), (0, ["refused:"]), done.stderr)
        self.assertIn("pipe", done.stdout)

    def test_a_fifo_swapped_in_after_the_listing_is_not_read_either(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.mkfifo(Path(tmp) / "pipe")
            done = self.child(tmp, "swapped")
        self.assertEqual((done.returncode, done.stdout.split()[:1]), (0, ["refused:"]), done.stderr)

    def test_a_socket_and_a_fifo_in_a_subdirectory_are_refused_and_a_plain_tree_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "d").mkdir()
            (base / "d" / "f").write_bytes(b"x")
            os.symlink("/dev/null", base / "l")
            snap = cycle.snapshot_tree(base)                 # plain files, directories and links are read as before
            self.assertEqual(sorted(snap), ["d", "d/f", "l"])
            self.assertEqual(snap["d/f"][:2], ("f", 1))
            sock = socket.socket(socket.AF_UNIX)
            self.addCleanup(sock.close)
            sock.bind(str(base / "d" / "s"))
            with self.assertRaises(cycle.UnsupportedEntry) as caught:
                cycle.snapshot_tree(base)
            self.assertIn("d/s", str(caught.exception))
            (base / "d" / "s").unlink()
            os.mkfifo(base / "d" / "q")
            self.assertTrue(os.path.exists(base / "d" / "q"))
            done = self.child(base, "listed")
            self.assertEqual(done.returncode, 0, done.stderr)

    def test_the_hash_of_a_regular_file_is_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "f").write_bytes(b"hello")
            size, digest = cycle.file_size_and_sha256(Path(tmp) / "f", "f")
        self.assertEqual((size, digest), (5, "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"))
        with tempfile.TemporaryDirectory() as tmp:
            os.mkfifo(Path(tmp) / "p")
            done = self.child(tmp, "hash")            # in a child under a timeout: a hang fails the test, it does not stop the run
        self.assertEqual((done.returncode, done.stdout.split()[:1]), (0, ["refused:"]), done.stderr)


if __name__ == "__main__":
    unittest.main()
