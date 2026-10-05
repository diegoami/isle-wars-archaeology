"""Tests of T16's save layout and writer (runtime/iw-dos/save/): the decoder and encoder (savefmt.py), the round-trip
check, and the crafted-save writer (writer.py) with its three refusals: a name other than ISLEWAR.SAV, a directory that
is not a run copy of this install, and a position the format cannot carry.

The writer tests use test_iw_dos_seal's synthetic world (a copy, a run directory and a throwaway registered set in a
temporary directory outside every checkout); none touches the real install or run directory. tests/mutants_iw_dos.py
removes each refusal and the round-trip check in turn and shows the named tests failing.
"""
import contextlib
import copy
import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import test_iw_dos_seal as seal  # noqa: E402  (the synthetic world; sets sys.path for the modules below)
import test_iw_dos_steps as steps  # noqa: E402  (the step-script world: a cycle with a fake screen)

sys.path.insert(0, str(ROOT / "runtime" / "iw-dos" / "save"))
import savefmt  # noqa: E402
import writer  # noqa: E402
import rundir  # noqa: E402
import navsteps  # noqa: E402

cycle = seal.cycle


def position():
    """A position that is not any real game's: every field has its own value, so a swapped field shows."""
    owners = [("blue", "red", "green", "brown")[i % 4] for i in range(46)]
    return {"centres": [4, 44, 43], "dft": [1, 3], "settings": [2, 0], "owners": owners,
            "armies": [(i % 9) + 1 for i in range(46)],
            "cards": {"blue": [3], "red": [], "green": [3, 7], "brown": [1, 2, 9]}}


def natural_bytes(pos=None):
    """The bytes the game's layout gives, written here line by line from the layout in savefmt's docstring and not by
    savefmt.encode: a ` v ` line for each value, the count line and the last line."""
    pos = pos or position()
    code = {"blue": 9, "red": 4, "green": 2, "brown": 8}
    lines = [f" {len(pos['centres'])} "] + [f" {c} " for c in pos["centres"]] + [f" {v} " for v in pos["dft"]]
    lines += [f" {v} " for v in pos["settings"]] + [f" {code[o]} " for o in pos["owners"]]
    lines += [f" {a} " for a in pos["armies"]]
    cards = pos["cards"]
    lines.append(" " + " , ".join(str(len(cards[c])) for c in ("blue", "red", "green", "brown")) + " ")
    lines.append(",".join("".join(map(str, cards[c])) for c in ("blue", "green", "red", "brown")))
    return "".join(line + "\r\n" for line in lines).encode()


class LayoutTest(unittest.TestCase):
    def test_encode_gives_the_layout_byte_for_byte(self):
        self.assertEqual(savefmt.encode(position()), natural_bytes())

    def test_decode_gives_the_position_back(self):
        self.assertEqual(savefmt.decode(natural_bytes()), position())

    def test_the_known_corner_of_a_real_save_layout(self):
        # ` 0 , 0 , 1 , 0 ` and `,3,,` are lines the game wrote (E005, F007 D14): Green held one card, a 3
        pos = position()
        pos["cards"] = {"blue": [], "red": [], "green": [3], "brown": []}
        data = savefmt.encode(pos)
        self.assertTrue(data.endswith(b" 0 , 0 , 1 , 0 \r\n,3,,\r\n"), data[-30:])
        self.assertEqual(savefmt.decode(data)["cards"], pos["cards"])

    def test_a_save_with_no_centre_and_one_with_many_round_trip(self):
        for centres in ([], [1], list(range(1, 47))):
            with self.subTest(len(centres)):
                pos = dict(position(), centres=centres)
                self.assertEqual(savefmt.decode(savefmt.encode(pos)), pos)
                self.assertTrue(savefmt.roundtrip(savefmt.encode(pos)))

    def test_decode_refuses_bytes_that_are_not_the_layout(self):
        good = natural_bytes()
        lines = good.split(b"\r\n")
        damaged = {
            "no final CRLF": good[:-2],
            "LF line ends": good.replace(b"\r\n", b"\n"),
            "empty": b"",
            "a line short": b"\r\n".join(lines[:-2]) + b"\r\n",
            "a line more": good + b" 1 \r\n",
            "an owner code that is no colour's": good.replace(b" 9 \r\n", b" 5 \r\n", 1),
            "a value without its spaces": good.replace(b" 44 \r\n", b"44\r\n", 1),
            "a count that is not the hand": good.replace(b" 1 , 0 , 2 , 3 ", b" 1 , 0 , 2 , 2 "),
            "a hand with a 0": good.replace(b"3,37,,129", b"3,37,,120"),
            "not bytes": "text",
        }
        for what, data in damaged.items():
            with self.subTest(what):
                if what == "a count that is not the hand":
                    self.assertIn(b" 1 , 0 , 2 , 3 ", good)
                with self.assertRaises(savefmt.SaveError):
                    savefmt.decode(data)

    def test_roundtrip_is_true_for_what_the_game_wrote_and_false_when_the_bytes_differ(self):
        data = natural_bytes()
        self.assertTrue(savefmt.roundtrip(data))
        with mock.patch.object(savefmt, "encode", return_value=data + b"x"):
            self.assertFalse(savefmt.roundtrip(data))


class EncodeRefusalTest(unittest.TestCase):
    def refused(self, mutate):
        pos = position()
        mutate(pos)
        with self.assertRaises(savefmt.Refused):
            savefmt.encode(pos)

    def test_a_position_the_format_cannot_carry_is_refused(self):
        cases = {
            "an unknown colour": lambda p: p["owners"].__setitem__(0, "purple"),
            "45 owners": lambda p: p["owners"].pop(),
            "47 armies": lambda p: p["armies"].append(1),
            "100 armies": lambda p: p["armies"].__setitem__(0, 100),
            "negative armies": lambda p: p["armies"].__setitem__(0, -1),
            "armies as text": lambda p: p["armies"].__setitem__(0, "5"),
            "armies as a bool": lambda p: p["armies"].__setitem__(0, True),
            "a centre 0": lambda p: p.__setitem__("centres", [0]),
            "a centre 47": lambda p: p.__setitem__("centres", [47]),
            "a centre twice": lambda p: p.__setitem__("centres", [4, 4]),
            "a card 0": lambda p: p["cards"].__setitem__("blue", [0]),
            "a card 10": lambda p: p["cards"].__setitem__("blue", [10]),
            "ten cards": lambda p: p["cards"].__setitem__("blue", [1] * 10),
            "a missing hand": lambda p: p["cards"].pop("red"),
            "an extra colour": lambda p: p["cards"].__setitem__("white", []),
            "an extra key": lambda p: p.__setitem__("level", 1),
            "a missing key": lambda p: p.pop("settings"),
            "a dft of three": lambda p: p.__setitem__("dft", [1, 1, 1]),
            "a dft of 100": lambda p: p.__setitem__("dft", [100, 1]),
            "settings as a string": lambda p: p.__setitem__("settings", "20"),
            "not a dict": lambda p: None,
        }
        for what, mutate in cases.items():
            with self.subTest(what):
                if what == "not a dict":
                    with self.assertRaises(savefmt.Refused):
                        savefmt.encode([])
                else:
                    self.refused(mutate)

    def test_the_round_trip_check_refuses_bytes_that_decode_to_another_position(self):
        real = savefmt.decode
        other = position()
        other["armies"][0] += 1
        with mock.patch.object(savefmt, "decode", return_value=other):
            with self.assertRaises(savefmt.Refused) as caught:
                savefmt.encode(position())
        self.assertIn("another position", str(caught.exception))
        self.assertIs(savefmt.decode, real)

    def test_the_round_trip_check_refuses_bytes_that_do_not_decode(self):
        with mock.patch.object(savefmt, "decode", side_effect=savefmt.SaveError("x")):
            with self.assertRaises(savefmt.Refused):
                savefmt.encode(position())

    def test_the_extremes_that_are_accepted_round_trip(self):
        pos = position()
        pos["armies"] = [99] * 23 + [0] * 23
        pos["cards"]["blue"] = [9, 8, 7, 6, 5, 4, 3, 2, 1]
        self.assertEqual(savefmt.decode(savefmt.encode(pos)), pos)


class WriterTest(seal.World):
    def setUp(self):
        super().setUp()
        self.game = self.sync()

    def listing(self, path):
        return sorted(os.listdir(path))

    def test_the_save_is_written_into_the_run_copy_as_islewar_sav(self):
        before = self.listing(self.game)
        data, digest = writer.place(self.run_dir, self.install, position())
        self.assertEqual(data, natural_bytes())
        self.assertEqual((self.game / "ISLEWAR.SAV").read_bytes(), data)
        self.assertEqual(digest, seal.sha(data))
        self.assertEqual(self.listing(self.game), sorted(before + ["ISLEWAR.SAV"]))
        self.assertEqual(self.listing(self.install), sorted(seal.FILES))          # the install is untouched

    def test_an_existing_save_is_never_replaced(self):
        (self.game / "ISLEWAR.SAV").write_bytes(b"the game's")
        with self.assertRaises(savefmt.Refused):
            writer.place(self.run_dir, self.install, position())
        self.assertEqual((self.game / "ISLEWAR.SAV").read_bytes(), b"the game's")

    def test_any_name_but_islewar_sav_is_refused_and_nothing_is_written(self):
        for name in ("ISLEWAR.DFT", "ISLEWAR.SCR", "ISLEWAR.DAT", "ISLEWAR.EXE", "islewar.sav", "ISLEWAR.SAV ",
                     "../ISLEWAR.SAV", "/ISLEWAR.SAV", "X.SAV", ""):
            with self.subTest(name):
                before = self.listing(self.game)
                with self.assertRaises(savefmt.Refused):
                    writer.place(self.run_dir, self.install, position(), name=name)
                self.assertEqual(self.listing(self.game), before)
        self.assertEqual(self.listing(self.install), sorted(seal.FILES))

    def test_the_install_itself_is_never_written_into(self):
        (self.install / "game").mkdir()                    # even with a `game` folder in it
        for run_dir in (self.install, self.install / "game", self.install.parent):
            with self.subTest(str(run_dir)):
                with self.assertRaises(savefmt.Refused):
                    writer.place(run_dir, self.install, position())
        self.assertEqual(self.listing(self.install), sorted(list(seal.FILES) + ["game"]))
        self.assertEqual(self.listing(self.install / "game"), [])
        self.assertEqual(self.listing(self.game), sorted(seal.FILES))

    def test_a_directory_that_is_not_a_run_copy_is_refused(self):
        other = self.tmp / "other"
        (other / "game").mkdir(parents=True)
        (other / "game" / "NOTES.TXT").write_bytes(b"not the set")
        for run_dir in (other, self.tmp / "missing"):
            with self.subTest(str(run_dir)):
                with self.assertRaises(savefmt.Refused):
                    writer.place(run_dir, self.install, position())
        self.assertEqual(self.listing(other / "game"), ["NOTES.TXT"])

    def test_a_run_copy_with_a_changed_or_missing_registered_file_is_refused(self):
        (self.game / "ISLEWAR.EXE").write_bytes(b"MZ changed")
        with self.assertRaises(savefmt.Refused) as caught:
            writer.place(self.run_dir, self.install, position())
        self.assertIn("is not the registered file", str(caught.exception))
        (self.game / "ISLEWAR.EXE").unlink()
        with self.assertRaises(savefmt.Refused):
            writer.place(self.run_dir, self.install, position())
        self.assertFalse((self.game / "ISLEWAR.SAV").exists())

    def test_a_stray_file_is_refused_but_the_files_the_game_writes_itself_are_not(self):
        (self.game / "ISLEWAR.SCR").write_bytes(b"0,0\r\n")
        (self.game / "ISLEWAR.DFT").write_bytes(b" 1 , 1 , 2 \r\n")
        writer.place(self.run_dir, self.install, position())              # the game's own files are there at a Load
        (self.game / "ISLEWAR.SAV").unlink()
        (self.game / "EXTRA.TXT").write_bytes(b"stray")
        with self.assertRaises(savefmt.Refused) as caught:
            writer.place(self.run_dir, self.install, position())
        self.assertIn("not part of the registered set", str(caught.exception))
        self.assertFalse((self.game / "ISLEWAR.SAV").exists())

    def test_a_run_directory_inside_a_checkout_is_refused(self):
        checkout = self.tmp / "checkout"
        (checkout / ".git").mkdir(parents=True)
        run_dir = checkout / "run"
        (run_dir / "game").mkdir(parents=True)
        for name, data in seal.FILES.items():
            (run_dir / "game" / name).write_bytes(data)
        with self.assertRaises(savefmt.Refused):
            writer.place(run_dir, self.install, position())
        self.assertFalse((run_dir / "game" / "ISLEWAR.SAV").exists())

    def test_a_position_that_cannot_be_encoded_writes_nothing(self):
        pos = position()
        pos["armies"][3] = 100
        with self.assertRaises(savefmt.Refused):
            writer.place(self.run_dir, self.install, pos)
        self.assertFalse((self.game / "ISLEWAR.SAV").exists())

    def test_a_position_whose_bytes_decode_to_another_is_not_written(self):
        other = position()
        other["owners"][0] = "red"
        with mock.patch.object(savefmt, "decode", return_value=other):
            with self.assertRaises(savefmt.Refused):
                writer.place(self.run_dir, self.install, position())
        self.assertFalse((self.game / "ISLEWAR.SAV").exists())

    def test_a_symbolic_link_at_the_name_is_not_written_through(self):
        victim = self.tmp / "victim"
        victim.write_bytes(b"keep")
        os.symlink(victim, self.game / "ISLEWAR.SAV")
        with self.assertRaises(savefmt.Refused):
            writer.place(self.run_dir, self.install, position())
        self.assertEqual(victim.read_bytes(), b"keep")


class CommandLineTest(seal.World):
    def setUp(self):
        super().setUp()
        self.game = self.sync()

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = writer.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_craft_changes_one_field_and_write_places_it(self):
        base = self.tmp / "base.sav"
        base.write_bytes(natural_bytes())
        code, out, _ = self.run_main("craft", str(base), "owner:1=red", "armies:2=9", "cards:blue=7")
        self.assertEqual(code, 0)
        crafted = json.loads(out)
        want = position()
        want["owners"][0], want["armies"][1], want["cards"]["blue"] = "red", 9, [7]
        self.assertEqual(crafted, want)
        pos = self.tmp / "pos.json"
        pos.write_text(out)
        code, said, _ = self.run_main("write", str(pos), "--run-dir", str(self.run_dir), "--install", str(self.install))
        self.assertEqual(code, 0, said)
        self.assertEqual(savefmt.decode((self.game / "ISLEWAR.SAV").read_bytes()), want)

    def test_craft_and_write_refuse_what_cannot_be_encoded_or_placed(self):
        base = self.tmp / "base.sav"
        base.write_bytes(natural_bytes())
        self.assertEqual(self.run_main("craft", str(base), "armies:1=100")[0], 1)
        self.assertEqual(self.run_main("craft", str(base), "owner:1=purple")[0], 1)
        pos = self.tmp / "pos.json"
        pos.write_text(json.dumps(position()))
        code, _, err = self.run_main("write", str(pos), "--run-dir", str(self.install), "--install", str(self.install))
        self.assertEqual(code, 1)
        self.assertIn("refused", err)
        self.assertEqual(sorted(os.listdir(self.install)), sorted(seal.FILES))

    def test_roundtrip_exits_1_for_a_file_that_does_not_round_trip(self):
        good = self.tmp / "good.sav"
        good.write_bytes(natural_bytes())
        self.assertEqual(self.run_main("roundtrip", str(good))[0], 0)
        with mock.patch.object(savefmt, "encode", return_value=b"other"):
            self.assertEqual(self.run_main("roundtrip", str(good))[0], 1)
        bad = self.tmp / "bad.sav"
        bad.write_bytes(b"not a save")
        self.assertEqual(self.run_main("roundtrip", str(bad))[0], 1)


class PutSaveStepTest(steps.StepsWorld):
    """The cycle's `put-save` step and `--crafted`: an I3 intervention that the cycle declares, places only through
    the writer, and never takes without a position or without the step."""

    def crafted_file(self, pos=None):
        path = self.tmp / "crafted.position.json"
        path.write_text(json.dumps(pos or position()))
        return str(path)

    def started(self, text="put-save\nshot placed\n", pos=None):
        made = self.make_steps(text, extra=("--crafted", self.crafted_file(pos)))
        return made

    def load(self, made):
        with contextlib.redirect_stdout(io.StringIO()):
            made.load_script()

    def go(self, made):
        with mock.patch.object(cycle, "run", self.fake_run(made)), mock.patch.object(cycle, "poll", self.poll_once), \
                contextlib.redirect_stdout(io.StringIO()):
            made.load_script()
            made.navigate()

    def test_put_save_places_the_crafted_save_in_the_run_copy_and_records_it(self):
        made = self.started()
        self.go(made)
        placed = (made.game / "ISLEWAR.SAV").read_bytes()
        self.assertEqual(placed, natural_bytes())
        obs = {o["field"]: o["value"] for o in made.obs}
        self.assertEqual(obs["crafted save placed in the run copy as ISLEWAR.SAV: bytes, sha256"],
                         f"{len(placed)} {seal.sha(placed)}")
        self.assertEqual(obs["crafted position sha256"], seal.sha(Path(made.args.crafted).read_bytes()))
        self.assertEqual(made.crafted, (obs["crafted position sha256"], seal.sha(placed)))
        self.assertTrue(made.after_screen_ok)

    def test_a_run_that_placed_a_crafted_save_declares_I3_and_one_that_did_not_does_not(self):
        made = self.started()
        self.go(made)
        declared = cycle.interventions(made.args, made.used_savestate, made.crafted)
        self.assertEqual([d["level"] for d in declared], ["I1", "I3"])
        self.assertIn(made.crafted[0], declared[1]["what"])
        self.assertIn(made.crafted[1], declared[1]["what"])
        self.assertEqual([d["level"] for d in cycle.interventions(made.args, False, None)], ["I1"])

    def test_the_reset_removes_the_crafted_save_and_the_run_copy_equals_its_start(self):
        made = self.started()
        self.go(made)
        self.assertTrue((made.game / "ISLEWAR.SAV").is_file())
        with contextlib.redirect_stdout(io.StringIO()):
            made.reset()
        self.assertFalse((made.game / "ISLEWAR.SAV").exists())
        self.assertFalse(made.status.startswith("aborted"), made.status)

    def test_put_save_without_a_crafted_position_aborts_before_anything_is_launched(self):
        made = self.make_steps("put-save\n")
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(cycle.Abort):
            made.load_script()
        self.assertIn("put-save", made.status)
        self.assertFalse((made.game / "ISLEWAR.SAV").exists())

    def test_a_crafted_position_without_a_put_save_step_aborts(self):
        made = self.make_steps("shot a\n", extra=("--crafted", self.crafted_file()))
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(cycle.Abort):
            made.load_script()
        self.assertIn("no put-save", made.status)

    def test_a_position_that_cannot_be_encoded_aborts_at_the_load_of_the_script(self):
        bad = position()
        bad["armies"][0] = 100
        made = self.started(pos=bad)
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(cycle.Abort):
            made.load_script()
        self.assertIn("the --crafted position is refused", made.status)

    def test_a_crafted_file_that_is_not_json_aborts(self):
        made = self.started()
        Path(made.args.crafted).write_text("not json")
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(cycle.Abort):
            made.load_script()
        self.assertIn("the --crafted position is refused", made.status)

    def test_a_run_copy_with_a_stray_file_is_refused_at_the_step_and_nothing_is_written(self):
        made = self.started()
        (made.game / "EXTRA.TXT").write_bytes(b"stray")
        with mock.patch.object(cycle, "run", self.fake_run(made)), mock.patch.object(cycle, "poll", self.poll_once), \
                contextlib.redirect_stdout(io.StringIO()), self.assertRaises(cycle.Abort):
            made.load_script()
            made.navigate()
        self.assertIn("the crafted save was refused", made.status)
        self.assertFalse((made.game / "ISLEWAR.SAV").exists())
        self.assertFalse(made.after_screen_ok)

    def test_the_writer_is_the_only_writer_of_the_save(self):
        made = self.started()
        with mock.patch.object(cycle.writer, "place", side_effect=savefmt.Refused("no")) as place:
            with mock.patch.object(cycle, "run", self.fake_run(made)), mock.patch.object(cycle, "poll", self.poll_once), \
                    contextlib.redirect_stdout(io.StringIO()), self.assertRaises(cycle.Abort):
                made.load_script()
                made.navigate()
        place.assert_called_once()
        self.assertFalse((made.game / "ISLEWAR.SAV").exists())

    def test_put_save_is_allowed_once_and_crafted_needs_steps(self):
        with self.assertRaises(navsteps.Refused):
            navsteps.parse("put-save\nput-save\n")
        self.assertEqual(navsteps.parse("put-save\n"), [("put-save", ())])
        args = cycle.parser().parse_args(["--crafted", "x.json"])
        self.assertIn("--crafted needs --steps", cycle.refused_args(args))
        args = cycle.parser().parse_args(["--crafted", "x.json", "--steps", "s"])
        self.assertIsNone(cycle.refused_args(args))


if __name__ == "__main__":
    unittest.main()
