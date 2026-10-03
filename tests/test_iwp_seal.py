"""The seal around the originals, at the point of use, on synthetic fixtures only (iwp_fixtures.py).

- HardLinkTest, MountTest: the game copy and the prefix hold no second name of another file and
  nothing mounted; synchronising never writes or re-permissions the install (round 1, R1).
- WriterTest: the one confined writer (setup/iwp/safeio.py) refuses links, second names, bad names
  and swapped directories, and leaves nothing behind (R2).
- OutputTest: inner() writes bundles, exploration output and records only through that writer (R2).
- GateTest: the real inner() and Cycle.execute() refuse an unsafe prefix before anything starts and
  again immediately before the launch (R3), never record a run "completed" unless it completed
  (R4), and turn a failed cold-state check or reset into an aborted record and a nonzero exit (R5).
"""
import os
import stat
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from iwp_fixtures import InnerHarness, World, cycle, inodes, prefix, safeio, sha, tree  # noqa: E402


def nlink(path):
    return os.lstat(path).st_nlink


class HardLinkTest(World):
    def test_a_mismatching_hard_link_to_an_unlisted_install_file_is_detached_not_written(self):
        game = self.game_copy({"xtras/b.dat": b"beta"})
        os.link(self.install / "unlisted.bin", game / "a.txt")
        self.assertTrue(any("a.txt has 2 names" in p for p in prefix.verify_game_copy(game)))
        self.assertEqual(self.call(prefix.sync_game)[0], 0)
        self.assertEqual((self.install / "unlisted.bin").read_bytes(), b"keep me")
        self.assertEqual(nlink(self.install / "unlisted.bin"), 1)
        self.assertEqual(((game / "a.txt").read_bytes(), nlink(game / "a.txt")), (b"alpha", 1))
        self.assertEqual(prefix.prefix_problems(self.prefix), [])

    def test_an_already_matching_hard_link_to_the_install_is_found_and_detached(self):
        game = self.game_copy()
        (game / "a.txt").unlink()
        os.link(self.install / "a.txt", game / "a.txt")
        self.assertTrue(any("another is the install's" in p for p in prefix.verify_game_copy(game)))
        self.assertTrue(any("a.txt has 2 names" in p for p in prefix.prefix_problems(self.prefix)))
        self.assertEqual(self.call(prefix.check)[0], 1)
        self.call(prefix.sync_game)
        self.assertEqual(prefix.prefix_problems(self.prefix), [])
        self.assertEqual(nlink(self.install / "a.txt"), 1)
        (game / "a.txt").write_bytes(b"the game wrote here")
        self.assertEqual((self.install / "a.txt").read_bytes(), b"alpha")

    def test_a_matching_hard_link_to_any_other_file_is_detached_too(self):
        game = self.game_copy()
        other = self.tmp / "elsewhere.txt"
        other.write_bytes(b"alpha")
        (game / "a.txt").unlink()
        os.link(other, game / "a.txt")
        self.call(prefix.sync_game)
        self.assertEqual((nlink(other), nlink(game / "a.txt")), (1, 1))

    def test_the_installs_mode_is_not_changed_through_a_hard_link(self):
        game = self.game_copy({"xtras/b.dat": b"beta"})
        os.chmod(self.install / "a.txt", 0o444)
        self.addCleanup(os.chmod, self.install / "a.txt", 0o644)
        os.link(self.install / "a.txt", game / "a.txt")
        before = inodes(self.install)
        self.call(prefix.sync_game)
        self.assertEqual(inodes(self.install)["a.txt"], (1, before["a.txt"][1]))
        self.assertEqual(stat.S_IMODE(os.stat(self.install / "a.txt").st_mode), 0o444)

    def test_pruning_an_unlisted_hard_link_removes_the_name_only(self):
        game = self.game_copy()
        os.link(self.install / "unins000.exe", game / "extra.exe")
        before = tree(self.install)
        self.call(prefix.sync_game)
        self.assertFalse((game / "extra.exe").exists())
        self.assertEqual(tree(self.install), before)

    def test_a_hard_link_elsewhere_in_the_prefix_is_found_and_given_a_file_of_its_own(self):
        self.game_copy()
        shared = self.prefix / "drive_c" / "users" / "u" / "notes.txt"
        os.link(self.install / "unlisted.bin", shared)
        self.assertTrue(any("notes.txt has 2 names (a hard link; another is the install's)" in p
                            for p in prefix.prefix_problems(self.prefix)))
        self.call(prefix.strip_links)
        self.assertEqual(prefix.prefix_problems(self.prefix), [])
        self.assertEqual((nlink(self.install / "unlisted.bin"), shared.read_bytes()), (1, b"keep me"))
        shared.write_bytes(b"changed")
        self.assertEqual((self.install / "unlisted.bin").read_bytes(), b"keep me")

    def test_a_directory_where_a_listed_file_belongs_is_removed_without_following_its_links(self):
        game = self.game_copy({"xtras/b.dat": b"beta"})
        (game / "a.txt").mkdir()
        os.symlink(self.install, game / "a.txt" / "to-install")
        os.link(self.install / "unlisted.bin", game / "a.txt" / "hard")
        before = tree(self.install)
        self.assertEqual(self.call(prefix.sync_game)[0], 0)
        self.assertEqual(tree(self.install), before)
        self.assertEqual(nlink(self.install / "unlisted.bin"), 1)        # the copy's name went, the file stayed
        self.assertEqual(prefix.verify_game_copy(game), [])

    def test_a_fifo_in_the_game_copy_is_found_and_removed(self):
        game = self.game_copy()
        os.mkfifo(game / "pipe")
        self.assertTrue(any("pipe is a device" in p for p in prefix.verify_game_copy(game)))
        self.call(prefix.sync_game)
        self.assertEqual(prefix.verify_game_copy(game), [])


class MountTest(World):
    """A mount inside the prefix (a bind mount of the install, say) is another place: it is reported,
    and nothing under it is changed or removed."""

    def mounted(self, path):
        return mock.patch.object(prefix, "mount_points", return_value=[Path("/"), path])

    def test_a_mount_point_in_the_game_copy_is_reported_and_sync_changes_nothing(self):
        game = self.game_copy({"a.txt": b"stale", "extra.txt": b"x"})
        with self.mounted(game / "xtras"):
            self.assertTrue(any("xtras is a mount point" in p for p in prefix.verify_game_copy(game)))
            self.assertTrue(any("mount point" in p for p in prefix.prefix_problems(self.prefix)))
            before = tree(self.prefix)
            reason, _ = self.refused(prefix.sync_game)
            self.assertEqual(tree(self.prefix), before)
            self.assertIn("another place", reason)

    def test_the_game_copy_itself_mounted_is_refused(self):
        game = self.game_copy()
        with self.mounted(game):
            self.assertTrue(any(". is a mount point" in p for p in prefix.verify_game_copy(game)))
            self.refused(prefix.sync_game)

    def test_strip_links_changes_nothing_in_a_prefix_with_a_mount(self):
        self.game_copy()
        os.symlink("/", self.prefix / "dosdevices" / "z:")
        with self.mounted(self.prefix / "drive_c" / "users"):
            before = tree(self.prefix)
            self.refused(prefix.strip_links)
            self.assertEqual(tree(self.prefix), before)

    def test_mount_points_are_read_from_mountinfo_with_escapes_decoded(self):
        self.assertIn(Path("/"), prefix.mount_points())
        text = "36 35 98:0 / /tmp/a\\040b rw - ext4 /dev/x rw\n"
        with mock.patch.object(prefix.Path, "read_text", return_value=text):
            self.assertEqual(prefix.mount_points(), [Path("/tmp/a b")])


class WriterTest(World):
    def setUp(self):
        super().setUp()
        self.out = self.tmp / "out"
        self.out.mkdir()
        self.precious = self.checkout / "precious.txt"
        self.write(self.precious, b"original")

    def leftovers(self):
        return sorted(p.name for p in self.out.iterdir() if p.name.startswith("."))

    def test_names_and_identifiers(self):
        for good in ("control", "size-1024x768x24", "a.b_c-1", "E001-r0001.json", ".update-timestamp"):
            self.assertEqual(safeio.safe_name(good), good)
        for bad in ("", ".", "..", "/tmp/x", "../x", "a/b", "a b", "x\n", "a" * 101, None):
            with self.subTest(bad=bad), self.assertRaises(safeio.Refused):
                safeio.safe_name(bad)
        for bad in (".hidden", "-lead", "../x", "/abs"):
            with self.subTest(bad=bad), self.assertRaises(safeio.Refused):
                safeio.identifier(bad)

    def test_the_cli_refuses_an_arm_that_is_not_a_plain_identifier(self):
        for bad in ("/tmp/x", "../x", "a/b", "", ".x"):
            with self.subTest(bad=bad), mock.patch("sys.stderr"), self.assertRaises(SystemExit):
                cycle.parser().parse_args(["--arm", bad])
        self.assertEqual(cycle.parser().parse_args(["--arm", "size-1024x768x24"]).arm, "size-1024x768x24")

    def test_new_writes_once_and_refuses_any_existing_name(self):
        self.assertEqual(safeio.write_file(self.out, "r.json", data=b"one"), "written")
        os.symlink(self.precious, self.out / "link.json")
        os.link(self.precious, self.out / "hard.json")
        (self.out / "dir.json").mkdir()
        for name in ("r.json", "link.json", "hard.json", "dir.json"):
            with self.subTest(name=name), self.assertRaises(safeio.Refused):
                safeio.write_file(self.out, name, data=b"two")
        self.assertEqual(((self.out / "r.json").read_bytes(), self.precious.read_bytes()), (b"one", b"original"))
        self.assertEqual(nlink(self.precious), 2)
        self.assertEqual(self.leftovers(), [])

    def test_replace_renames_over_a_plain_file_and_refuses_aliases(self):
        (self.out / "f").write_bytes(b"old")
        safeio.write_file(self.out, "f", data=b"new", exist="replace")
        self.assertEqual(((self.out / "f").read_bytes(), nlink(self.out / "f")), (b"new", 1))
        os.symlink(self.precious, self.out / "link")
        os.link(self.precious, self.out / "hard")
        for name in ("link", "hard"):
            with self.subTest(name=name), self.assertRaises(safeio.Refused):
                safeio.write_file(self.out, name, data=b"through?", exist="replace")
        self.assertEqual(self.precious.read_bytes(), b"original")
        safeio.write_file(self.out, "hard", data=b"own", exist="replace", replace_shared=True)
        self.assertEqual((self.precious.read_bytes(), nlink(self.precious)), (b"original", 1))
        with self.assertRaises(safeio.Refused):
            safeio.write_file(self.out, "link", data=b"x", exist="replace", replace_shared=True)
        self.assertEqual(self.leftovers(), [])

    def test_same_keeps_identical_bytes_and_refuses_others(self):
        safeio.write_file(self.out, "a", data=b"x", exist="same")
        self.assertEqual(safeio.write_file(self.out, "a", data=b"x", exist="same"), "kept")
        with self.assertRaises(safeio.Refused):
            safeio.write_file(self.out, "a", data=b"y", exist="same")
        self.assertEqual(((self.out / "a").read_bytes(), self.leftovers()), (b"x", []))

    def test_a_copy_whose_bytes_are_not_the_expected_ones_leaves_nothing(self):
        source = self.tmp / "src"
        source.write_bytes(b"tampered")
        with self.assertRaises(safeio.Refused):
            safeio.write_file(self.out, "copy", source=source, expect_sha256=sha(b"registered"))
        self.assertEqual(list(self.out.iterdir()), [])

    def test_a_source_that_is_a_link_is_not_read_through(self):
        os.symlink(self.precious, self.tmp / "src")
        with self.assertRaises(safeio.Refused):
            safeio.write_file(self.out, "copy", source=self.tmp / "src")
        self.assertEqual(list(self.out.iterdir()), [])

    def test_a_directory_behind_a_link_is_refused_even_after_the_path_was_checked(self):
        swapped = self.tmp / "swapped"
        os.symlink(self.checkout, swapped)       # a directory replaced by a link after confinement
        for directory in (swapped, swapped / "sub"):
            with self.subTest(directory=directory.name), self.assertRaises(safeio.Refused):
                safeio.write_file(directory, "x", data=b"x", create_below=self.tmp)
        for bad in (self.out / ".." / "out", Path("relative")):
            with self.subTest(bad=str(bad)), self.assertRaises(safeio.Refused):
                safeio.write_file(bad, "x", data=b"x")
        self.assertEqual(sorted(p.name for p in self.checkout.iterdir()), [".git", "precious.txt"])

    def test_directories_are_created_only_below_the_given_place(self):
        safeio.write_file(self.out / "a" / "b", "x", data=b"x", create_below=self.out)
        self.assertEqual((self.out / "a" / "b" / "x").read_bytes(), b"x")
        with self.assertRaises(safeio.Refused):
            safeio.write_file(self.tmp / "new" / "c", "x", data=b"x", create_below=self.tmp / "new")
        with self.assertRaises(safeio.Refused):
            safeio.write_file(self.tmp / "elsewhere", "x", data=b"x", create_below=self.out)
        self.assertFalse((self.tmp / "new").exists() or (self.tmp / "elsewhere").exists())

    def test_remove_takes_names_only_and_never_follows_a_link_on_the_way(self):
        os.symlink(self.install, self.out / "to-install")
        os.link(self.install / "unlisted.bin", self.out / "hard")
        (self.out / "dir").mkdir()
        os.symlink(self.install / "xtras", self.out / "dir" / "inner")
        before = tree(self.install)
        with self.assertRaises(safeio.Refused):
            safeio.remove(self.out, "to-install/a.txt")          # through the link: refused
        for rel in ("to-install", "hard", "dir"):
            self.assertTrue(safeio.remove(self.out, rel))
        self.assertFalse(safeio.remove(self.out, "dir"))
        for bad in ("../out", "/abs", ""):
            with self.subTest(bad=bad), self.assertRaises(safeio.Refused):
                safeio.remove(self.out, bad)
        self.assertEqual(tree(self.install), before)
        self.assertEqual(nlink(self.install / "unlisted.bin"), 1)

    def test_set_mode_never_acts_through_a_link_or_on_a_second_name(self):
        os.chmod(self.precious, 0o600)
        os.symlink(self.precious, self.out / "link")
        os.link(self.precious, self.out / "hard")
        for rel in ("link", "hard"):
            with self.subTest(rel=rel), self.assertRaises(safeio.Refused):
                safeio.set_mode(self.out, rel, 0o777)
        self.assertEqual(stat.S_IMODE(os.stat(self.precious).st_mode), 0o600)
        (self.out / "own").write_bytes(b"x")
        safeio.set_mode(self.out, "own", 0o640)
        self.assertEqual(stat.S_IMODE(os.stat(self.out / "own").st_mode), 0o640)

    def test_a_stream_is_a_new_file_never_an_existing_name(self):
        os.symlink(self.precious, self.out / "wine.log")
        with self.assertRaises(safeio.Refused):
            safeio.create_stream(self.out, "wine.log")
        with safeio.create_stream(self.out, "other.log") as fh:
            fh.write(b"log")
        self.assertEqual(self.precious.read_bytes(), b"original")


class OutputTest(InnerHarness):
    def setUp(self):
        super().setUp()
        self.game_copy()
        self.precious = self.checkout / "precious.txt"
        self.write(self.precious, b"original")

    def checkout_untouched(self):
        self.assertEqual(sorted(p.name for p in self.checkout.iterdir()), [".git", "precious.txt"])
        self.assertEqual((self.precious.read_bytes(), nlink(self.precious)), (b"original", 1))

    def asset(self, name="before.png"):
        """The bundle name a screenshot of the harness gets (the harness's capture is fixed)."""
        png = cycle.png_bytes(800, 600, b"\x10" * (800 * 600 * 3))
        return f"{sha(png)[:16]}-{name}"

    def test_an_arm_that_is_not_a_plain_identifier_starts_nothing_even_without_the_parser(self):
        for arm in (str(self.checkout / "evil"), "../../checkout/evil", ".hidden"):
            with self.subTest(arm=arm):
                args = cycle.parser().parse_args(["--explore"])
                args.arm = arm
                with mock.patch.dict(os.environ, {"IWP_CYCLE_ID": "E001-x1"}), \
                        mock.patch.object(cycle, "run", side_effect=AssertionError("nothing may run")), \
                        self.assertRaises(SystemExit):
                    cycle.inner(args)
        self.checkout_untouched()

    def test_a_good_run_stores_every_output_and_a_repeated_asset_is_kept(self):
        code, record = self.run_cycle()
        self.assertEqual((code, record["status"]), (0, "completed"))
        names = {o["name"] for o in record["outputs"]}
        self.assertTrue({"before.png", "after.png", "run.log", "changes.log"} <= names, names)
        code, record = self.run_cycle()                  # the same before.png asset is already there
        self.assertEqual((code, record["status"]), (0, "completed"))

    def test_a_bundle_asset_that_is_a_link_or_a_second_name_is_not_written_through(self):
        self.bundles.mkdir()
        for label, make in (("symbolic", os.symlink), ("hard", os.link)):
            with self.subTest(label):
                target = self.bundles / self.asset()
                if os.path.lexists(target):
                    target.unlink()
                make(self.precious, target)
                code, record = self.run_cycle()
                self.assertEqual(code, 1)
                self.assertTrue(record["status"].startswith("aborted: before.png was not stored"), record["status"])
                self.assertNotIn("before.png", {o["name"] for o in record["outputs"]})
                self.assertEqual(self.precious.read_bytes(), b"original")
        self.assertEqual(nlink(self.precious), 2)          # the fixture's hard link, untouched

    def test_an_exploration_file_that_is_a_link_is_not_written_through(self):
        explore = self.tmp / "explore"
        explore.mkdir()
        os.symlink(self.precious, explore / "control.before.png")
        code, record = self.run_cycle(["--explore"])
        self.assertEqual((code, record), (1, None))
        self.checkout_untouched()
        self.assertTrue((explore / "control.after.png").is_file())

    def test_a_bundle_directory_swapped_for_a_link_after_confinement_receives_nothing(self):
        swapped = self.tmp / "bundles-link"
        os.symlink(self.checkout, swapped)
        real = cycle.confined_locations

        def swapped_after_check(args):
            found = real(args)
            found["E001_BUNDLES"] = swapped
            return found

        with mock.patch.object(cycle, "confined_locations", swapped_after_check):
            code, record = self.run_cycle()
        self.assertEqual(code, 1)
        self.assertTrue(record["status"].startswith("aborted: "), record["status"])
        self.assertEqual(record["outputs"], [])
        self.checkout_untouched()

    def test_a_record_name_that_exists_in_any_form_is_never_written(self):
        (self.repo / "runs" / "E001").mkdir(parents=True)
        os.symlink(self.precious, self.repo / "runs" / "E001" / "E001-r9001.json")
        code, record = self.run_cycle()
        self.assertEqual((code, record), (1, None))
        self.checkout_untouched()
        self.assertFalse((self.repo / "evidence" / "E001" / "E001-r9001.manifest.json").exists())

    def test_a_records_folder_that_is_a_link_receives_nothing(self):
        (self.repo / "runs").rmdir()
        os.symlink(self.checkout, self.repo / "runs")
        code, _ = self.run_cycle()
        self.assertEqual(code, 1)
        self.checkout_untouched()

    def test_the_run_id_and_the_machine_id_must_be_plain(self):
        for key, value in (("IWP_CYCLE_ID", "../../x"), ("IWP_CYCLE_ID", "E002-r0001"), ("E001_MACHINE", "Bad/Name")):
            with self.subTest(key=key, value=value):
                code, record = self.run_cycle(env={key: value})
                self.assertIsInstance(code, SystemExit)
                self.assertIsNone(record)
        self.assertNotIn("start_x", self.calls)


class GateTest(InnerHarness):
    def setUp(self):
        super().setUp()
        self.game = self.game_copy()
        self.baseline = Path(str(self.prefix) + ".baseline")

    def values(self, record, field):
        return [o["value"] for o in record["observations"] if o["field"] == field]

    def started(self):
        """The stages that start something (stopping the display always runs, as clean-up)."""
        return [c for c in self.calls if c in ("start_x", "start_wm", "launch", "known_screen", "input")]

    def unsafe(self):
        users = self.prefix / "drive_c" / "users" / "u"
        mounted = mock.patch.object(prefix, "mount_points", return_value=[users])
        return {
            "absolute z:": lambda: os.symlink("/", self.prefix / "dosdevices" / "z:"),
            "relative escape": lambda: os.symlink("../../../../install", users / "Desktop"),
            "c: maps elsewhere": lambda: ((self.prefix / "dosdevices" / "c:").unlink(),
                                          os.symlink("..", self.prefix / "dosdevices" / "c:")),
            "another drive, inside": lambda: os.symlink("../drive_c", self.prefix / "dosdevices" / "d:"),
            "a hard link to the install": lambda: os.link(self.install / "unlisted.bin", users / "notes.txt"),
            "a mount": lambda: (mounted.start(), self.addCleanup(mounted.stop)),
        }

    # positive control

    def test_a_safe_prefix_completes_with_both_screenshots_and_exit_0(self):
        code, record = self.run_cycle()
        self.assertEqual((code, record["status"]), (0, "completed"))
        self.assertEqual(self.calls[:3], ["start_x", "start_wm", "launch"])
        self.assertEqual(self.values(record, "prefix seal before anything starts: problems found"), ["0"])
        self.assertEqual(self.values(record, "prefix seal immediately before launch: problems found"), ["0"])
        self.assertEqual(self.values(record, "install bound read-only in the run's mount namespace"), ["yes"])

    # R3: an unsafe prefix is never launched from, even when the registered-game check passes

    def test_each_unsafe_prefix_prevents_everything_with_an_aborted_record_and_exit_1(self):
        for label in list(self.unsafe()):
            with self.subTest(label):
                self.setUp()
                self.assertEqual(prefix.verify_game_copy(self.game), [], "the registered-game check passes")
                self.unsafe()[label]()
                code, record = self.run_cycle()
                self.assertEqual(code, 1)
                self.assertTrue(record["status"].startswith(
                    "aborted: the prefix is not safe to launch from (before anything starts)"), record["status"])
                self.assertEqual(self.started(), [])
                self.assertFalse({"before.png", "after.png"} & {o["name"] for o in record["outputs"]})

    def test_outer_starts_no_namespace_for_an_unsafe_prefix_and_one_for_a_safe_one(self):
        dispatched = []

        def fake_run(cmd, **kw):
            dispatched.append(cmd[0])
            return mock.MagicMock(returncode=0, stdout=b"abc123\n", stderr=b"")

        args = cycle.parser().parse_args(["--explore"])
        with mock.patch.object(cycle.subprocess, "run", fake_run):
            self.assertEqual(cycle.outer(args), 0)
        self.assertEqual(dispatched.count("unshare"), 1)
        for label in list(self.unsafe()):
            with self.subTest(label):
                self.setUp()
                self.unsafe()[label]()
                dispatched.clear()
                with mock.patch.object(cycle.subprocess, "run", fake_run), self.assertRaises(SystemExit) as caught:
                    cycle.outer(args)
                self.assertIn("not safe to launch from; nothing was started", str(caught.exception))
                self.assertNotIn("unshare", dispatched)

    def test_a_prefix_made_unsafe_after_the_first_seal_is_refused_immediately_before_launch(self):
        def spoil(self_):
            os.symlink("/", self.prefix / "dosdevices" / "z:")

        code, record = self.run_cycle(stages={"start_wm": spoil})
        self.assertEqual(code, 1)
        self.assertTrue(record["status"].startswith(
            "aborted: the prefix is not safe to launch from (immediately before launch)"), record["status"])
        self.assertNotIn("launch", self.calls)

    def test_the_real_launch_seals_the_prefix_before_it_starts_the_game(self):
        os.symlink("../../../../install", self.prefix / "drive_c" / "users" / "u" / "Desktop")
        made = cycle.Cycle(cycle.parser().parse_args([]), "E001-test", self.prefix, self.bundles, self.install)
        with mock.patch.object(cycle.subprocess, "Popen", side_effect=AssertionError("the game must not start")), \
                mock.patch("sys.stdout"), self.assertRaises(cycle.Abort):
            made.launch()
        self.assertTrue(made.status.startswith("aborted: the prefix is not safe"), made.status)

    def test_an_install_that_stays_writable_inside_the_run_starts_nothing(self):
        code, record = self.run_cycle(install_writable=True)
        self.assertEqual((code, record["status"]), (1, "aborted: the install could not be made read-only inside the run"))
        self.assertEqual(self.started(), [])

    # R5: the cold-state gate, each fault alone

    def test_a_changed_missing_or_stray_game_file_alone_prevents_everything(self):
        cases = {"changed": lambda: (self.game / "a.txt").write_bytes(b"ALPHA"),
                 "missing": lambda: (self.game / "xtras" / "b.dat").unlink(),
                 "stray": lambda: self.write(self.game / "stray.bin", b"x")}
        for label, make in cases.items():
            with self.subTest(label):
                self.setUp()
                make()
                code, record = self.run_cycle()
                self.assertEqual(code, 1)
                self.assertTrue(record["status"].startswith("aborted: the prefix is not safe"), record["status"])
                self.assertEqual(self.started(), [])

    # R4: nothing but a full cycle is completed

    def test_a_failed_capture_is_an_aborted_record_with_exit_1(self):
        code, record = self.run_cycle(raw=b"too short")
        self.assertEqual(code, 1)
        self.assertTrue(record["status"].startswith("aborted: RuntimeError: capture is"), record["status"])
        self.assertFalse({"before.png", "after.png"} & {o["name"] for o in record["outputs"]})

    def test_a_cycle_without_its_screenshots_or_its_options_screen_is_never_completed(self):
        code, record = self.run_cycle(shot=lambda self_, name, step: None)
        self.assertEqual((code, record["status"]), (1, "aborted: the cycle ended without before.png and after.png"))
        code, record = self.run_cycle(options_up=False)
        self.assertEqual((code, record["status"]), (1, "aborted: the click did not bring up the Options screen"))

    def test_a_crash_or_an_interruption_is_aborted_and_cleaned_up(self):
        def interrupt(self_):
            raise KeyboardInterrupt

        for label, stages, launch in (("crash", {}, lambda self_: {}["boom"]),
                                      ("interruption", {"known_screen": interrupt}, None)):
            with self.subTest(label):
                self.calls.clear()
                code, record = self.run_cycle(launch=launch, stages=stages)
                self.assertEqual(code, 1)
                self.assertRegex(record["status"], r"^aborted: (KeyError|KeyboardInterrupt)")
                self.assertIn("stop_x", self.calls)
                self.assertEqual(self.values(record, "prefix after reset equals prefix before launch"), ["yes"])

    def test_a_failing_clean_up_stage_aborts_a_completed_cycle_and_the_rest_still_runs(self):
        def broken(self_):
            raise OSError("display would not stop")

        code, record = self.run_cycle(stages={"stop_x": broken})
        self.assertEqual(code, 1)
        self.assertTrue(record["status"].startswith("aborted: stopping the display failed"), record["status"])
        self.assertEqual(self.values(record, "prefix after reset equals prefix before launch"), ["yes"])

    # R5: the reset gate

    def test_reset_removes_what_the_run_added_and_restores_registry_and_game_files(self):
        self.baseline.mkdir()
        (self.baseline / "system.reg").write_text("reg")

        def run_writes(self_):
            self.write(self.prefix / "drive_c" / "Temp" / "x.dll", b"extra")
            os.symlink("/dev/ttyS0", self.prefix / "dosdevices" / "com1")
            (self.prefix / "system.reg").write_text("rewritten by wine")
            (self.game / "a.txt").write_bytes(b"the game wrote here")

        code, record = self.run_cycle(launch=run_writes)
        self.assertEqual((code, record["status"]), (0, "completed"))
        self.assertFalse((self.prefix / "drive_c" / "Temp").exists() or os.path.lexists(self.prefix / "dosdevices" / "com1"))
        self.assertEqual(((self.prefix / "system.reg").read_text(), (self.game / "a.txt").read_bytes()), ("reg", b"alpha"))
        self.assertEqual(self.values(record, "prefix after reset equals prefix before launch"), ["yes"])

    def test_a_reset_that_does_not_restore_the_prefix_aborts_the_record_and_exits_1(self):
        notes = self.prefix / "drive_c" / "users" / "u" / "notes.txt"
        self.write(notes, b"before")
        code, record = self.run_cycle(launch=lambda self_: notes.write_bytes(b"after"))
        self.assertEqual((code, record["status"]), (1, "aborted: reset did not restore the prefix"))
        self.assertTrue(self.values(record, "prefix after reset equals prefix before launch")[0].startswith("no"))

    def test_a_reset_that_cannot_synchronise_the_game_copy_aborts(self):
        self.addCleanup((self.install / "a.txt").write_bytes, b"alpha")
        code, record = self.run_cycle(launch=lambda self_: (self.install / "a.txt").write_bytes(b"tampered"))
        self.assertEqual(code, 1)
        self.assertTrue(record["status"].startswith("aborted: reset could not synchronise the game copy"), record["status"])

    def test_reset_never_follows_what_the_run_planted(self):
        self.baseline.mkdir()
        (self.baseline / "system.reg").write_text("reg")
        users = self.prefix / "drive_c" / "users" / "u"

        def plant(self_):
            os.symlink(self.install, self.prefix / "drive_c" / "to-install")   # an added link
            (self.prefix / "system.reg").unlink()
            os.symlink(self.install / "unlisted.bin", self.prefix / "system.reg")   # a link where a file was
            users.rmdir()
            os.symlink(self.install / "xtras", users)                      # a directory swapped for a link

        before = tree(self.install), inodes(self.install)
        code, record = self.run_cycle(launch=plant)
        self.assertEqual(code, 1)
        self.assertTrue(record["status"].startswith("aborted: reset"), record["status"])
        self.assertEqual((tree(self.install), inodes(self.install)), before)

    def test_reset_refuses_a_drive_c_the_run_swapped_for_a_link_to_the_install(self):
        def swap(self_):
            os.rename(self.prefix / "drive_c", self.tmp / "old-drive_c")
            os.symlink(self.install, self.prefix / "drive_c")

        before = tree(self.install), inodes(self.install)
        code, record = self.run_cycle(launch=swap)
        self.assertEqual(code, 1)
        self.assertTrue(record["status"].startswith("aborted: reset could not synchronise"), record["status"])
        self.assertEqual((tree(self.install), inodes(self.install)), before)


if __name__ == "__main__":
    unittest.main()
