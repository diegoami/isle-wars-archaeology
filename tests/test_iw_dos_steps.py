"""Tests of T14's additions to the DOS cycle: the step scripts (navsteps.py), `--steps`, the files the
game writes (record_written), the savestate step and `--experiment`.

The seal itself is tested in test_iw_dos_seal.py (T11); these tests use its synthetic world (a copy,
a run directory and bundles in a temporary directory outside every checkout) and replace the
display, xdotool and the game. tests/mutants_iw_dos.py removes each addition in turn and shows the
named tests failing.
"""
import contextlib
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import test_iw_dos_seal as seal  # noqa: E402  (the synthetic world; sets sys.path for the modules below)

import navsteps  # noqa: E402
import rundir  # noqa: E402
import safeio  # noqa: E402

cycle = seal.cycle


class ParseTest(unittest.TestCase):
    def test_every_verb_parses_to_its_arguments(self):
        text = """
        # a comment
        click 60 32            # trailing comment
        until 272 138 80 18 170 85 0 800
        until 0 0 10 10 1 2 3 5 7
        wait-stable
        wait-change
        wait-change 5
        shot level-dialog
        files
        key Return
        key c
        key e
        savestate
        rclick 1 2
        click-change 5 6
        click-change 5 6 9
        rclick-change 7 8
        wait-exit
        wait-exit 5
        click-until 283 323 258 305 155 40 255 255 85 300
        click-until 283 323 258 305 155 40 255 255 85 300 5
        choose-attack
        click-mine
        rclick-mine
        click-target
        rclick-target
        """
        self.assertEqual(navsteps.parse(text), [
            ("click", (60, 32)),
            ("until", ((272, 138, 80, 18), (170, 85, 0), 800, 20)),
            ("until", ((0, 0, 10, 10), (1, 2, 3), 5, 7)),
            ("wait-stable", ()), ("wait-change", (20,)), ("wait-change", (5,)),
            ("shot", ("level-dialog.png",)), ("files", ()), ("key", ("Return",)), ("key", ("c",)), ("key", ("e",)),
            ("savestate", ()), ("rclick", (1, 2)), ("click-change", (5, 6, 6)), ("click-change", (5, 6, 9)),
            ("rclick-change", (7, 8, 6)), ("wait-exit", (90,)), ("wait-exit", (5,)),
            ("click-until", (283, 323, (258, 305, 155, 40), (255, 255, 85), 300, 12)),
            ("click-until", (283, 323, (258, 305, 155, 40), (255, 255, 85), 300, 5)), ("choose-attack", ()),
            ("click-mine", ()), ("rclick-mine", ()), ("click-target", ()), ("rclick-target", ())])

    def test_anything_the_grammar_does_not_list_is_refused(self):
        for bad in ("click 640 10", "click 10 350", "click -1 5", "click 1", "click a b", "click 1 2 3",
                    "drag 1 2", "key Alt+x", "key F12", "key Return Return", "shot", "shot Before", "shot before",
                    "shot after", "shot ../x", "shot a b", "shot a.png",
                    "files now", "savestate x", "wait-stable 3", "wait-change 0", "wait-change x",
                    "until 1 2 3 4 256 0 0 1", "until 600 300 100 100 1 2 3 4", "until 1 2 0 4 1 2 3 4",
                    "until 1 2 3 4 1 2 3", "until 1 2 3 4 1 2 3 4 0", "run ls", "shell ls", "",
                    "key u", "key r", "key Upgrade", "click-change 1", "click-change 1 2 0", "click-change 700 2",
                    "rclick 640 0", "wait-exit 0", "click-mine", "rclick-target\nchoose-attack",
                    "choose-attack 1", "click-mine 1", "click-until 1 2 3 4 5 6 7 8 9",
                    "click-until 700 2 3 4 5 6 7 8 9 10", "click-until 1 2 3 4 5 6 7 8 300 1",
                    "click-until 1 2 3 4 5 6 7 8 9 1 0"):
            with self.subTest(bad):
                if bad == "":
                    self.assertEqual(navsteps.parse(bad), [])
                else:
                    with self.assertRaises(navsteps.Refused):
                        navsteps.parse(bad)

    def test_the_keys_that_would_order_or_register_are_not_in_the_grammar(self):
        self.assertEqual(set(navsteps.KEYS), {"Return", "space", "Escape", "c", "e"})

    def test_two_shots_of_one_name_are_refused(self):
        with self.assertRaises(navsteps.Refused):
            navsteps.parse("shot a\nshot a")


class FakeScreen:
    """A screen that changes when xdotool is told to move or click (see Steps.fake_run)."""

    ox, oy = 80, 100

    def __init__(self):
        self.current = b"menu"
        self.colour = 0

    def raw(self, crop=None):
        return self.current

    def count(self, rect, colour):
        return self.colour

    def stable(self):
        return True

    def capture(self, directory, name):
        safeio.write_file(directory, name, data=b"png-" + self.current, exist="new")
        return "a" * 64, "b" * 64, self.current


class StepsWorld(seal.CycleWorld):
    def make_steps(self, text, extra=()):
        script = self.tmp / "script.steps"
        script.write_text(text)
        made = self.make(["--steps", str(script), "--experiment", "E005", *extra])
        made.screen = FakeScreen()
        self.calls = []
        self.ignored_clicks = 0
        self.click_count = 0
        self.conquer_at = 10 ** 6
        made.snap_before = cycle.snapshot_tree(made.game)
        return made

    def fake_run(self, made):
        def run(cmd, **kw):
            self.calls.append(cmd)
            if cmd[:2] == ["xdotool", "mousemove"]:
                made.screen.current = b"pointer"
            elif cmd[:2] == ["xdotool", "click"]:
                self.click_count += 1
                if self.click_count >= self.conquer_at:
                    made.screen.colour = 999
                if self.ignored_clicks > 0:
                    self.ignored_clicks -= 1
                else:
                    made.screen.current = b"dialog"
            return mock.MagicMock(returncode=0, stdout=b"")
        return run

    def poll_once(self, condition, timeout, interval=0.1):
        return 0.0 if condition() else None


class LoadScriptTest(StepsWorld):
    def test_a_script_the_grammar_refuses_aborts_with_nothing_launched(self):
        made = self.make_steps("click 60 32\nkey Alt+x\n")
        with redirect_stdout(io.StringIO()), self.assertRaises(cycle.Abort):
            made.load_script()
        self.assertTrue(made.status.startswith("aborted: the steps script is refused"), made.status)

    def test_execute_stops_at_a_refused_script_before_it_binds_or_launches_anything(self):
        made = self.make_steps("click 700 700\n")
        with mock.patch.object(cycle, "run") as run, mock.patch.object(cycle, "popen") as popen, \
                redirect_stdout(io.StringIO()):
            made.execute()
        run.assert_not_called()
        popen.assert_not_called()
        self.assertTrue(made.status.startswith("aborted: the steps script is refused"), made.status)

    def test_the_script_is_recorded_by_its_hash(self):
        made = self.make_steps("click 60 32\nshot a\n")
        with redirect_stdout(io.StringIO()):
            made.load_script()
        wanted = cycle.sha256_bytes(b"click 60 32\nshot a\n")
        self.assertIn(("steps script sha256", wanted), [(o["field"], o["value"]) for o in made.obs])


class NavigateTest(StepsWorld):
    def navigate(self, made, **patches):
        with mock.patch.object(cycle, "run", self.fake_run(made)), mock.patch.object(cycle, "poll", self.poll_once), \
                redirect_stdout(io.StringIO()):
            made.load_script()
            made.navigate()

    def test_a_click_moves_the_pointer_inside_the_window_and_then_presses(self):
        made = self.make_steps("click 60 32\n")
        self.navigate(made)
        self.assertEqual(self.calls, [["xdotool", "mousemove", "140", "132"], ["xdotool", "click", "1"]])
        self.assertTrue(made.after_screen_ok)

    def test_wait_change_sees_the_screen_move_after_a_click(self):
        made = self.make_steps("click 60 32\nwait-change 5\n")
        self.navigate(made)
        waited = [o["value"] for o in made.obs if o["field"] == "screen changed after (s)"]
        self.assertEqual(waited, ["0.0"])

    def test_a_shot_is_kept_as_an_output_and_the_steps_run_in_order(self):
        made = self.make_steps("click 60 32\nshot one\nshot two\n")
        self.navigate(made)
        self.assertEqual([n for n, _, _ in made.outputs], ["one.png", "two.png"])
        self.assertEqual([o["step"] for o in made.obs if o["field"].endswith("raw RGB8 pixels sha256")], [102, 103])

    def test_an_until_that_never_comes_aborts_and_the_run_is_not_completed(self):
        made = self.make_steps("until 0 0 4 4 170 0 0 10 3\nshot after-it\n")
        made.screen.colour = 10                       # not more than 10
        with mock.patch.object(cycle, "run", self.fake_run(made)), mock.patch.object(cycle, "poll", self.poll_once), \
                redirect_stdout(io.StringIO()), self.assertRaises(cycle.Abort):
            made.load_script()
            made.navigate()
        self.assertTrue(made.status.startswith("aborted: step 1: the expected screen did not appear"), made.status)
        self.assertFalse(made.after_screen_ok)
        self.assertNotIn("after-it.png", [n for n, _, _ in made.outputs])
        self.assertIn("until-failed-101.png", [n for n, _, _ in made.outputs])

    def test_an_until_that_comes_lets_the_steps_go_on(self):
        made = self.make_steps("until 0 0 4 4 170 0 0 10 3\nshot after-it\n")
        made.screen.colour = 11
        self.navigate(made)
        self.assertIn("after-it.png", [n for n, _, _ in made.outputs])

    def test_a_key_is_sent_as_given(self):
        made = self.make_steps("key Return\n")
        self.navigate(made)
        self.assertEqual(self.calls, [["xdotool", "key", "Return"]])


class CompleteTest(StepsWorld):
    def test_a_script_run_needs_every_shot_the_script_names(self):
        made = self.make_steps("shot a\nshot b\n")
        with redirect_stdout(io.StringIO()):
            made.load_script()
        made.after_screen_ok = True
        made.outputs.append(("before.png", Path("x"), "screenshot"))
        made.outputs.append(("a.png", Path("x"), "screenshot"))
        with redirect_stdout(io.StringIO()), self.assertRaises(cycle.Abort):
            made.complete()
        self.assertIn("without b.png", made.status)

    def test_a_script_run_does_not_need_after_png_but_all_its_steps(self):
        made = self.make_steps("shot a\n")
        with redirect_stdout(io.StringIO()):
            made.load_script()
        made.outputs += [("before.png", Path("x"), "screenshot"), ("a.png", Path("x"), "screenshot")]
        with redirect_stdout(io.StringIO()), self.assertRaises(cycle.Abort):
            made.complete()
        self.assertIn("the steps did not all finish", made.status)
        made.status = "running"
        made.after_screen_ok = True
        with redirect_stdout(io.StringIO()):
            made.complete()
        self.assertEqual(made.status, "completed")

    def test_without_a_script_the_e003_rule_is_unchanged(self):
        made = self.make()
        made.after_screen_ok = True
        with redirect_stdout(io.StringIO()), self.assertRaises(cycle.Abort):
            made.complete()
        self.assertIn("without before.png and after.png", made.status)


class WrittenFilesTest(StepsWorld):
    def written(self, made, prefix="s01"):
        with redirect_stdout(io.StringIO()):
            made.record_written("step 1", 101, prefix)
        return {o["field"]: o["value"] for o in made.obs}

    def test_a_small_file_the_game_adds_is_observed_with_its_bytes_and_kept(self):
        made = self.make_steps("files\n")
        (made.game / "ISLEWAR.SCR").write_bytes(b"0,0\r\n0,0\r\n")
        obs = self.written(made)
        self.assertEqual(obs["run copy at step 1: added/removed/changed"], "1/0/0")
        self.assertEqual(obs["run copy at step 1: added ISLEWAR.SCR: hex"], b"0,0\r\n0,0\r\n".hex())
        self.assertEqual(obs["run copy at step 1: added ISLEWAR.SCR: bytes, sha256"],
                         "10 " + cycle.sha256_bytes(b"0,0\r\n0,0\r\n"))
        self.assertEqual([n for n, _, _ in made.outputs], ["s01-ISLEWAR.SCR"])
        self.assertEqual(made.outputs[0][2], "measurement")       # a class the manifest schema accepts
        (made.game / "ISLEWAR.SAV").write_bytes(b"3\r\n")
        with redirect_stdout(io.StringIO()):
            made.record_written("step 2", 102, "s02")
        self.assertEqual({n: k for n, _, k in made.outputs}["s02-ISLEWAR.SAV"], "save")
        self.assertEqual((made.workdir / "s01-ISLEWAR.SCR").read_bytes(), b"0,0\r\n0,0\r\n")

    def test_the_manifest_of_a_run_that_kept_game_files_is_valid(self):
        import validate_records
        made = self.make_steps("files\n")
        (made.game / "ISLEWAR.SCR").write_bytes(b"0,0\r\n")
        (made.game / "ISLEWAR.SAV").write_bytes(b"3\r\n")
        self.written(made)
        manifest = cycle.build_manifest(made)
        self.assertEqual(sorted(f["class"] for f in manifest["files"]), ["measurement", "save"])
        self.assertEqual(validate_records.validate_document(manifest), [])

    def test_a_changed_file_is_labelled_changed_and_a_large_one_has_no_hex(self):
        made = self.make_steps("files\n")
        (made.game / "ISLEWAR.DAT").write_bytes(b"x" * (cycle.HEX_LIMIT + 1))
        obs = self.written(made)
        self.assertEqual(obs["run copy at step 1: added/removed/changed"], "0/0/1")
        self.assertIn("run copy at step 1: changed ISLEWAR.DAT: bytes, sha256", obs)
        self.assertNotIn("run copy at step 1: changed ISLEWAR.DAT: hex", obs)
        (made.game / "ISLEWAR.DAT").write_bytes(b"x" * cycle.HEX_LIMIT)
        made.obs.clear()
        self.assertIn("run copy at step 1: changed ISLEWAR.DAT: hex", self.written(made, "s02"))

    def test_a_removed_file_and_a_subdirectory_are_observed_and_not_copied(self):
        made = self.make_steps("files\n")
        (made.game / "ISLEWAR.EXE").unlink()
        (made.game / "SAVES").mkdir()
        obs = self.written(made)
        self.assertEqual(obs["run copy at step 1: removed ISLEWAR.EXE"], "removed")
        self.assertTrue(obs["run copy at step 1: SAVES"].startswith("not a plain file"))
        self.assertEqual(made.outputs, [])

    def test_a_file_name_that_is_not_a_plain_dos_name_is_not_copied(self):
        made = self.make_steps("files\n")
        (made.game / "bad name.txt").write_bytes(b"x")
        obs = self.written(made)
        self.assertTrue(obs["run copy at step 1: bad name.txt"].startswith("not a plain file"))
        self.assertEqual(made.outputs, [])

    def test_the_files_step_and_the_end_of_the_run_both_record_when_a_script_runs(self):
        made = self.make_steps("files\n")
        with redirect_stdout(io.StringIO()):
            made.load_script()
        (made.game / "ISLEWAR.SCR").write_bytes(b"0,0\r\n")
        made.take_snapshot("after")
        with redirect_stdout(io.StringIO()):
            made.report_changes()
        self.assertEqual(sorted(n for n, _, _ in made.outputs), ["changes.log", "end-ISLEWAR.SCR"])

    def test_without_a_script_the_end_of_the_run_adds_no_file_output(self):
        made = self.make()
        made.snap_before = cycle.snapshot_tree(made.game)
        (made.game / "ISLEWAR.SCR").write_bytes(b"0,0\r\n")
        made.take_snapshot("after")
        with redirect_stdout(io.StringIO()):
            made.report_changes()
        self.assertEqual([n for n, _, _ in made.outputs], ["changes.log"])


class SavestateStepTest(StepsWorld):
    def test_an_older_savestate_is_removed_so_it_cannot_satisfy_the_wait(self):
        made = self.make_steps("savestate\n")
        safeio.make_directory(made.workdir, "save")
        safeio.write_file(made.workdir / "save", "state.sav", data=b"older", exist="new")
        seen = []

        def save_state(step):
            seen.append((made.workdir / "save" / "state.sav").exists())
            return None
        with mock.patch.object(made, "save_state", save_state), \
                mock.patch.object(cycle, "savestate_members", return_value=({"Memory": (9, "x")}, None)), \
                redirect_stdout(io.StringIO()):
            made.step_savestate(101)
        self.assertEqual(seen, [False])
        self.assertTrue(made.used_savestate)
        self.assertIn(("savestate members (name: bytes)", "Memory: 9"), [(o["field"], o["value"]) for o in made.obs])

    def test_a_run_with_a_savestate_step_is_recorded_as_i2_and_one_without_as_i0(self):
        made = self.make_steps("savestate\n")
        self.assertEqual(cycle.interventions(made.args, False), [{"level": "I0", "what": "none"}])
        self.assertEqual(cycle.interventions(made.args, True)[0]["level"], "I2")


class ExperimentTest(seal.World):
    def test_the_bundles_of_e005_come_from_e005_bundles_and_are_confined(self):
        env = dict(self.env)
        env.pop("E003_BUNDLES")
        self.assertIn("E005_BUNDLES is not set", self.refused(
            lambda: rundir.run_locations(env, need_bundles=True, experiment="E005")))
        env["E005_BUNDLES"] = str(seal.ROOT / "bundles")
        self.assertIn("checkout", self.refused(lambda: rundir.run_locations(env, need_bundles=True, experiment="E005")))
        env["E005_BUNDLES"] = str(self.tmp / "bundles5")
        found = rundir.run_locations(env, need_bundles=True, experiment="E005")
        self.assertEqual(found["E005_BUNDLES"], self.tmp / "bundles5")
        self.assertNotIn("E003_BUNDLES", found)

    def test_the_default_experiment_is_still_e003(self):
        self.assertEqual(cycle.parser().parse_args([]).experiment, "E003")
        self.assertIn("E003_BUNDLES", rundir.run_locations(self.env, need_bundles=True))

    def test_an_experiment_other_than_the_two_is_refused(self):
        with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()), mock.patch("sys.stderr", io.StringIO()):
            cycle.parser().parse_args(["--experiment", "E004"])


class InnerE005Test(seal.CycleWorld):
    """The real inner() with --experiment E005 and a script: the record and its manifest land under E005."""

    def run_inner_e005(self, capture):
        repo = self.tmp / "repo"
        (repo / "runs").mkdir(parents=True, exist_ok=True)
        os.environ["E005_BUNDLES"] = str(self.tmp / "bundles5")
        env = {"IW_DOS_CYCLE_ID": "E005-r9001", "IW_DOS_CYCLE_REP": "1", "IW_DOS_CYCLE_COMMIT": "abcdef123456"}

        def launch(self_):
            self_.check_launch("immediately before launch", 1)
            self_.procs["game"] = seal.FakeGame()
            self_.t_launch = 0
        script = self.tmp / "s.steps"
        script.write_text("shot a\n")
        with contextlib.ExitStack() as stack:
            for name, value in (("start_x", lambda self_: None), ("known_screen", lambda self_: None),
                                ("launch", launch)):
                stack.enter_context(mock.patch.object(cycle.Cycle, name, value))
            stack.enter_context(mock.patch.object(cycle.Screen, "capture", capture))
            stack.enter_context(mock.patch.object(cycle.Screen, "raw", lambda *a, **k: b"x"))
            stack.enter_context(mock.patch.object(cycle, "run", return_value=mock.MagicMock(returncode=0)))
            stack.enter_context(mock.patch.object(cycle, "install_writable", return_value=False))
            stack.enter_context(mock.patch.object(cycle, "ROOT", repo))
            stack.enter_context(mock.patch.object(cycle, "WORK", self.work))
            stack.enter_context(mock.patch.object(cycle, "versions", return_value={}))
            stack.enter_context(mock.patch.dict(os.environ, env))
            stack.enter_context(mock.patch.object(cycle, "EXPERIMENT", "E003"))
            stack.enter_context(redirect_stdout(io.StringIO()))
            stack.enter_context(seal.redirect_stderr(io.StringIO()))
            code = cycle.inner(cycle.parser().parse_args(["--experiment", "E005", "--steps", str(script)]))
        return code, repo

    def test_an_e005_run_with_steps_writes_its_record_under_e005(self):
        def capture(self_, directory, name):
            seal.safeio.write_file(directory, name, data=b"png", exist="new")
            return "a" * 64, "b" * 64, b""
        code, repo = self.run_inner_e005(capture)
        self.assertEqual(code, 0)
        record = json.loads((repo / "runs" / "E005" / "E005-r9001.json").read_text())
        self.assertEqual((record["experiment"], record["status"]), ("E005", "completed"))
        self.assertEqual(sorted(o["name"] for o in record["outputs"] if o["name"].endswith(".png")),
                         ["a.png", "before.png"])
        self.assertTrue(all(o["store"] == "release:E005" for o in record["outputs"]))
        manifest = json.loads((repo / "evidence" / "E005" / "E005-r9001.manifest.json").read_text())
        self.assertEqual(manifest["experiment"], "E005")
        self.assertFalse((repo / "runs" / "E003").exists())
        self.assertEqual(len(list((self.tmp / "bundles5").iterdir())), len(manifest["files"]))
        self.assertIn("steps script sha256", [o["field"] for o in record["observations"]])

    def test_a_run_id_of_another_experiment_is_refused(self):
        with mock.patch.dict(os.environ, {"IW_DOS_CYCLE_ID": "E003-r9001"}), self.assertRaises(SystemExit):
            os.environ["E005_BUNDLES"] = str(self.tmp / "bundles5")
            cycle.inner(cycle.parser().parse_args(["--experiment", "E005"]))

class MoreNavigateTest(StepsWorld):
    def navigate(self, made):
        with mock.patch.object(cycle, "run", self.fake_run(made)), mock.patch.object(cycle, "poll", self.poll_once), \
                redirect_stdout(io.StringIO()):
            made.load_script()
            made.navigate()

    def test_a_right_click_presses_button_3(self):
        made = self.make_steps("rclick 60 32\n")
        self.navigate(made)
        self.assertEqual(self.calls[-1], ["xdotool", "click", "3"])

    def test_a_second_click_at_the_same_place_does_not_move_the_pointer_again(self):
        made = self.make_steps("click 5 5\nclick 5 5\nclick 6 5\n")
        self.navigate(made)
        self.assertEqual([c[1] for c in self.calls], ["mousemove", "click", "click", "mousemove", "click"])

    def test_click_change_clicks_again_when_the_game_ignored_the_click(self):
        made = self.make_steps("click-change 60 32\n")
        self.ignored_clicks = 1
        self.navigate(made)
        # the second click is preceded by a step off by one pixel and the move back: a real motion
        self.assertEqual(self.calls, [["xdotool", "mousemove", "140", "132"], ["xdotool", "click", "1"],
                                      ["xdotool", "mousemove", "141", "132"], ["xdotool", "mousemove", "140", "132"],
                                      ["xdotool", "click", "1"]])
        self.assertTrue(made.after_screen_ok)

    def test_click_change_gives_up_after_three_clicks_and_aborts(self):
        made = self.make_steps("click-change 60 32\nshot never\n")
        self.ignored_clicks = 99
        with mock.patch.object(cycle, "run", self.fake_run(made)), mock.patch.object(cycle, "poll", self.poll_once), \
                redirect_stdout(io.StringIO()), self.assertRaises(cycle.Abort):
            made.load_script()
            made.navigate()
        self.assertEqual([c[1] for c in self.calls].count("click"), 3)
        self.assertIn("never changed after three clicks", made.status)
        self.assertFalse(made.after_screen_ok)
        self.assertNotIn("never.png", [n for n, _, _ in made.outputs])
        self.assertIn("no-change-101.png", [n for n, _, _ in made.outputs])

    def test_click_until_clicks_one_roll_at_a_time_until_the_screen_shows_the_move_panel(self):
        made = self.make_steps("click-until 283 323 258 305 155 40 255 255 85 300\nshot done\n")
        self.conquer_at = 3
        self.navigate(made)
        self.assertEqual([c[1] for c in self.calls], ["mousemove", "click", "click", "click"])
        self.assertIn("done.png", [n for n, _, _ in made.outputs])

    def test_click_until_gives_up_after_its_clicks_and_aborts(self):
        made = self.make_steps("click-until 283 323 258 305 155 40 255 255 85 300 4\nshot done\n")
        with mock.patch.object(cycle, "run", self.fake_run(made)), mock.patch.object(cycle, "poll", self.poll_once), \
                redirect_stdout(io.StringIO()), self.assertRaises(cycle.Abort):
            made.load_script()
            made.navigate()
        self.assertEqual([c[1] for c in self.calls].count("click"), 4)
        self.assertIn("did not appear after 4 clicks", made.status)
        self.assertNotIn("done.png", [n for n, _, _ in made.outputs])
        self.assertIn("until-failed-101.png", [n for n, _, _ in made.outputs])

    def test_wait_exit_records_whether_the_game_ended_by_itself(self):
        made = self.make_steps("wait-exit 5\n")
        made.procs["game"] = seal.FakeGame()
        self.navigate(made)
        self.assertEqual([o["value"] for o in made.obs if o["field"] == "DOSBox-X ended by itself after (s)"],
                         ["still running after 5 s"])
        made.procs["game"].returncode = 0
        made.obs.clear()
        self.navigate(made)
        self.assertEqual([o["value"] for o in made.obs if o["field"] == "DOSBox-X ended by itself after (s)"], ["0.0"])


def painted(owners, half_height=19, half_width=14):
    """A 640x350 sea (0,0,170) with a block of army colour around the number box of each country in
    `owners` ({n: colour name}), each block half_height rows above and below the box's centre."""
    import board
    data = bytearray(bytes((0, 0, 170)) * (board.WIDTH * board.HEIGHT))
    for n, name in owners.items():
        cx, cy = board.BOXES[n]
        up = half_height[n] if isinstance(half_height, dict) else half_height
        for y in range(cy - up, cy + up + 1):
            for x in range(cx - half_width, cx + half_width + 1):
                data[(y * board.WIDTH + x) * 3:(y * board.WIDTH + x) * 3 + 3] = bytes(board.COLOURS[name])
        for y in range(cy - 4, cy + 4):                     # the black number box itself
            for x in range(cx - 6, cx + 6):
                data[(y * board.WIDTH + x) * 3:(y * board.WIDTH + x) * 3 + 3] = bytes((0, 0, 0))
    return bytes(data)


class BoardTest(unittest.TestCase):
    def test_owner_is_the_army_colour_beside_the_number_box(self):
        import board
        raw = painted({1: "blue", 2: "red", 3: "green", 4: "brown"})
        self.assertEqual([board.owner(raw, n) for n in (1, 2, 3, 4, 5)], ["blue", "red", "green", "brown", None])
        self.assertEqual(board.totals(raw), {"blue": 1, "red": 1, "green": 1, "brown": 1})

    def test_countries_whose_fills_nearly_meet_touch_and_distant_ones_do_not(self):
        import board
        raw = painted({1: "blue", 2: "red", 3: "blue"})      # 1 and 2 are 40 px apart in y, 2 and 3 are 34
        touch = board.neighbours(raw)
        self.assertEqual(touch[1], [2])
        self.assertEqual(touch[2], [1, 3])
        self.assertEqual(touch[3], [2])
        self.assertEqual(board.neighbours(painted({1: "blue", 12: "red"}))[1], [])

    def test_a_gap_wider_than_the_border_is_not_touching(self):
        import board
        raw = painted({1: "blue", 2: "red"}, half_height=15)  # fills 10 px apart
        self.assertEqual(board.neighbours(raw)[1], [])

    def test_the_number_boxes_are_found_as_black_rectangles_8_or_9_high(self):
        import board
        raw = painted({1: "blue", 2: "red"})
        found = board.derive_boxes(raw)
        self.assertEqual(len(found), 2)
        self.assertEqual(sorted((x + w // 2, y + h // 2) for x, y, w, h in found),
                         sorted([board.BOXES[1], board.BOXES[2]]))

    def test_there_are_46_distinct_boxes_inside_the_window(self):
        import board
        self.assertEqual(sorted(board.BOXES), list(range(1, 47)))
        self.assertEqual(len(set(board.BOXES.values())), 46)
        self.assertTrue(all(8 <= x < 632 and 20 <= y < 280 for x, y in board.BOXES.values()))


class ChooseAttackTest(StepsWorld):
    def navigate(self, made, owners):
        made.screen.current = painted(owners)
        with mock.patch.object(cycle, "run", self.fake_run(made)), mock.patch.object(cycle, "poll", self.poll_once), \
                redirect_stdout(io.StringIO()):
            made.load_script()
            made.navigate()

    def test_it_picks_a_blue_country_and_its_nearest_enemy_neighbour(self):
        import board
        made = self.make_steps("choose-attack\nclick-mine\nrclick-target\n")
        self.navigate(made, {1: "blue", 2: "red", 3: "brown"})
        self.assertEqual((made.mine, made.target), (1, 2))
        x, y = board.BOXES[1]
        self.assertEqual(self.calls[0], ["xdotool", "mousemove", str(x + 80), str(y + 100)])
        x, y = board.BOXES[2]
        self.assertEqual(self.calls[-2:], [["xdotool", "mousemove", str(x + 80), str(y + 100)], ["xdotool", "click", "3"]])
        chosen = [o["value"] for o in made.obs if o["field"].startswith("chosen")]
        self.assertEqual(chosen, ["1 2"])

    def test_a_country_of_the_same_army_is_never_the_target(self):
        made = self.make_steps("choose-attack\n")
        # 2 and 3 touch across one row of sea (not one region), and 2 is nearer to 3 than to the red 1
        made.screen.current = painted({1: "red", 2: "blue", 3: "blue"}, {1: 24, 2: 16, 3: 16})
        with mock.patch.object(cycle, "run", self.fake_run(made)), mock.patch.object(cycle, "poll", self.poll_once), \
                redirect_stdout(io.StringIO()):
            made.load_script()
            made.navigate()
        self.assertEqual((made.mine, made.target), (2, 1))

    def test_with_no_blue_country_touching_an_enemy_the_run_aborts(self):
        made = self.make_steps("choose-attack\nshot next\n")
        with self.assertRaises(cycle.Abort):
            self.navigate(made, {1: "blue", 12: "red"})
        self.assertIn("Blue has no country that touches an enemy", made.status)
        self.assertNotIn("next.png", [n for n, _, _ in made.outputs])


if __name__ == "__main__":
    unittest.main()
