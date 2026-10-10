"""Safety of the iwp-runtime profile and the E001 cycle, on synthetic fixtures only (iwp_fixtures.py).

Every test builds its own install, prefix and checkout in a temporary directory outside any
checkout. None reads or writes the real install (IWP_DIR) or the real prefix. A rejection test also
proves the "source" it protects is byte-for-byte unchanged. The writer, the seal and the cycle's
gates are in test_iwp_seal.py.
"""
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from iwp_fixtures import (MANIFEST, ROOT, registered, World, cycle, locations, prefix, sha, token_check,  # noqa: E402,F401
                          tokens, tree)


class LocationsTest(World):
    """R1: machine-local locations are confined before anything is mutated or launched."""

    def env(self, **values):
        base = {"IWP_PREFIX": str(self.prefix), "IWP_DIR": str(self.install), "E001_BUNDLES": str(self.bundles)}
        return {**base, **values}

    def test_a_good_layout_is_accepted(self):
        found = locations.locations(self.env(), need_prefix=True, need_bundles=True)
        self.assertEqual(found["IWP_PREFIX"], self.prefix)
        self.assertEqual(found["E001_BUNDLES"], self.bundles)
        self.assertEqual(found["IWP_PREFIX.baseline"], Path(str(self.prefix) + ".baseline"))

    def test_each_location_inside_a_checkout_is_refused(self):
        for name in ("IWP_PREFIX", "E001_BUNDLES"):
            with self.subTest(name=name), self.assertRaises(SystemExit) as caught:
                locations.locations(self.env(**{name: str(self.checkout / "sub" / "x")}),
                                    need_prefix=True, need_bundles=True)
            self.assertIn("inside a checkout", str(caught.exception))
        with self.assertRaises(SystemExit):
            locations.locations(self.env(E001_EXPLORE=str(self.checkout / "out")),
                                need_prefix=True, need_bundles=True, explore=True)

    def test_a_worktree_marker_that_is_a_file_counts_as_a_checkout(self):
        worktree = self.tmp / "worktree"
        worktree.mkdir()
        (worktree / ".git").write_text("gitdir: elsewhere")
        with self.assertRaises(SystemExit):
            locations.locations(self.env(IWP_PREFIX=str(worktree / "p")), need_prefix=True, need_bundles=True)

    def test_a_git_marker_that_is_a_dangling_link_counts_as_a_checkout(self):
        worktree = self.tmp / "worktree"
        worktree.mkdir()
        os.symlink(self.tmp / "gone", worktree / ".git")
        with self.assertRaises(SystemExit):
            locations.locations(self.env(IWP_PREFIX=str(worktree / "p")), need_prefix=True, need_bundles=True)

    def test_this_repository_and_its_parents_are_refused(self):
        for bad in (ROOT / "no-such-prefix", ROOT.parent, ROOT):
            with self.subTest(bad=str(bad.name)), self.assertRaises(SystemExit):
                locations.locations(self.env(IWP_PREFIX=str(bad)), need_prefix=True, need_bundles=True)

    def test_this_repository_is_refused_even_without_a_git_entry(self):
        with tempfile.TemporaryDirectory() as other:
            other = Path(os.path.realpath(other))
            plain = other / "plain-repo"
            plain.mkdir()
            with mock.patch.object(locations, "ROOT", plain):
                for label, bad in {"inside it": plain / "prefix", "its parent": other}.items():
                    with self.subTest(label), self.assertRaises(SystemExit):
                        locations.locations(self.env(IWP_PREFIX=str(bad)), need_prefix=True, need_bundles=True)

    def test_a_link_into_a_checkout_is_followed_and_refused(self):
        (self.checkout / "p").mkdir()
        link = self.tmp / "innocent"
        os.symlink(self.checkout / "p", link)
        with self.assertRaises(SystemExit):
            locations.locations(self.env(IWP_PREFIX=str(link)), need_prefix=True, need_bundles=True)

    def test_relative_empty_and_root_locations_are_refused(self):
        for bad in ("relative/prefix", "", "/"):
            with self.subTest(bad=bad), self.assertRaises(SystemExit):
                locations.locations(self.env(IWP_PREFIX=bad), need_prefix=True, need_bundles=True)

    def test_overlaps_with_the_install_and_each_other_are_refused(self):
        cases = {
            "prefix inside the install": {"IWP_PREFIX": str(self.install / "prefix")},
            "install inside the prefix": {"IWP_DIR": str(self.prefix / "install")},
            "prefix is the install": {"IWP_PREFIX": str(self.install)},
            "bundles inside the install": {"E001_BUNDLES": str(self.install / "b")},
            "bundles inside the prefix": {"E001_BUNDLES": str(self.prefix / "b")},
            "bundles are the prefix": {"E001_BUNDLES": str(self.prefix)},
        }
        for label, values in cases.items():
            with self.subTest(label), self.assertRaises(SystemExit) as caught:
                locations.locations(self.env(**values), need_prefix=True, need_bundles=True)
            self.assertIn("overlaps", str(caught.exception))

    def test_every_prefix_command_refuses_a_prefix_in_a_checkout_and_creates_nothing(self):
        bad = self.checkout / "prefix"
        os.environ["IWP_PREFIX"] = str(bad)
        with mock.patch.object(prefix, "start_xvfb", side_effect=AssertionError("Xvfb must not start")):
            for name, function in prefix.COMMANDS.items():
                with self.subTest(command=name):
                    self.refused(function)
        self.assertFalse(bad.exists())
        self.assertFalse(Path(str(bad) + ".baseline").exists())
        self.assertEqual(sorted(p.name for p in self.checkout.iterdir()), [".git"])

    def test_sync_into_a_prefix_in_a_checkout_copies_nothing(self):
        bad = self.checkout / "prefix"
        (bad / "drive_c").mkdir(parents=True)
        os.environ["IWP_PREFIX"] = str(bad)
        before = tree(self.checkout)
        self.refused(prefix.sync_game)
        self.assertEqual(tree(self.checkout), before)

    def test_the_cycle_refuses_bad_locations_before_it_mounts_or_launches_anything(self):
        for name in ("E001_BUNDLES", "IWP_PREFIX", "E001_EXPLORE"):
            os.environ["E001_BUNDLES"] = str(self.bundles)
            os.environ["IWP_PREFIX"] = str(self.prefix)
            os.environ["E001_EXPLORE"] = str(self.tmp / "explore")
            os.environ[name] = str(self.checkout / "x")
            args = cycle.parser().parse_args(["--explore"])
            # outer() reads the process lookups right after confined_locations(), so they are
            # stubbed: the refusals below must come from the location gate, never from a stray of
            # another session on this machine (fix #32). inner() reads neither lookup - its
            # refusal precedes them - but the stubs are inert there and kept for symmetry.
            with self.subTest(name=name), mock.patch.object(cycle, "run", side_effect=AssertionError("must not run")), \
                    mock.patch.dict(os.environ, {"IWP_CYCLE_ID": "E001-x1", "IWP_CYCLE_INNER": "1"}), \
                    mock.patch.object(cycle, "marked_processes", return_value=[]), \
                    mock.patch.object(cycle, "prefix_processes", return_value=[]):
                with self.assertRaises(SystemExit) as inner_exit:
                    cycle.inner(args)
                self.assertIn("inside a checkout or worktree", str(inner_exit.exception))
                with self.assertRaises(SystemExit) as outer_exit:
                    cycle.outer(args)
                self.assertIn("inside a checkout or worktree", str(outer_exit.exception))
        self.assertEqual(sorted(p.name for p in self.checkout.iterdir()), [".git"])

    def test_inner_writes_bundles_only_to_a_confined_directory(self):
        record_root = self.tmp / "repo"
        (record_root / "runs").mkdir(parents=True)

        def fake_execute(self_):
            png = self_.workdir / "before.png"
            png.write_bytes(b"synthetic png")
            self_.outputs.append(("before.png", png, "screenshot"))
            self_.status, self_.started, self_.ended = "completed", "2026-10-03T00:00:00Z", "2026-10-03T00:00:01Z"
            self_.snap_before = ({}, {}, {})

        args = cycle.parser().parse_args([])
        env = {"IWP_CYCLE_ID": "E001-r9999", "IWP_CYCLE_REP": "1", "IWP_CYCLE_COMMIT": "abcdef123456"}
        with mock.patch.dict(os.environ, env), mock.patch.object(cycle, "run"), \
                mock.patch.object(cycle, "ROOT", record_root), mock.patch.object(cycle, "versions", return_value={}), \
                mock.patch.object(cycle.Cycle, "execute", fake_execute), redirect_stdout(io.StringIO()):
            cycle.inner(args)
            self.assertTrue(any(p.name.endswith("-before.png") for p in self.bundles.iterdir()))
            os.environ["E001_BUNDLES"] = str(self.checkout / "bundles")
            with self.assertRaises(SystemExit):
                cycle.inner(args)
        self.assertEqual(sorted(p.name for p in self.checkout.iterdir()), [".git"])


class SyncTest(World):
    """R2: the game copy is a separate real directory; synchronisation never touches the install."""

    def assert_refused_and_install_intact(self, why):
        before = tree(self.install)
        self.refused(prefix.sync_game)
        self.assertEqual(tree(self.install), before, why)

    def test_a_normal_sync_copies_prunes_and_is_idempotent(self):
        game = self.game_copy({"a.txt": b"stale", "extra.txt": b"x"})
        (game / "empty").mkdir()
        self.call(prefix.sync_game)
        self.assertEqual(tree(game), {"a.txt": ("f", 5, sha(b"alpha")), "xtras": ("d", "", ""),
                                      "xtras/b.dat": ("f", 4, sha(b"beta"))})
        self.assertEqual(prefix.verify_game_copy(game), [])
        before = tree(game)
        _, out = self.call(prefix.sync_game)
        self.assertIn("copied 0, removed 0", out)
        self.assertEqual(tree(game), before)
        self.assertTrue(os.access(game / "a.txt", os.W_OK), "the copy must be writable")

    def test_a_game_directory_that_is_a_link_to_the_install_is_refused(self):
        os.symlink(self.install, self.prefix / "drive_c" / "iwp")
        self.assert_refused_and_install_intact("an unlisted file of the install was deleted")
        self.assertTrue((self.install / "unlisted.bin").exists())
        self.assertTrue((self.install / "unins000.exe").exists())

    def test_a_drive_c_that_is_a_link_is_refused(self):
        outside = self.tmp / "outside"
        self.write(outside / "iwp" / "a.txt", b"alpha")
        self.write(outside / "iwp" / "junk.txt", b"junk")
        (self.prefix / "drive_c" / "users" / "u").rmdir()
        (self.prefix / "drive_c" / "users").rmdir()
        (self.prefix / "drive_c").rmdir()
        os.symlink(outside, self.prefix / "drive_c")
        before = tree(outside)
        self.refused(prefix.sync_game)
        self.assertEqual(tree(outside), before)

    def test_a_directory_inside_the_copy_that_links_into_the_install_is_replaced_not_followed(self):
        game = self.game_copy({"a.txt": b"alpha"})
        os.symlink(self.install / "xtras", game / "xtras")
        before = tree(self.install)
        self.call(prefix.sync_game)
        self.assertEqual(tree(self.install), before)
        self.assertFalse((game / "xtras").is_symlink())
        self.assertEqual((game / "xtras" / "b.dat").read_bytes(), b"beta")

    def test_a_file_that_links_to_the_install_is_replaced_not_written_through(self):
        game = self.game_copy({})
        game.mkdir(parents=True, exist_ok=True)
        os.symlink(self.install / "a.txt", game / "a.txt")
        os.symlink(self.install / "unlisted.bin", game / "link-to-unlisted")
        before = tree(self.install)
        self.call(prefix.sync_game)
        self.assertEqual(tree(self.install), before)
        self.assertFalse((game / "a.txt").is_symlink())
        self.assertFalse((game / "link-to-unlisted").exists() or (game / "link-to-unlisted").is_symlink())

    def test_an_install_file_that_is_not_the_registered_one_copies_nothing(self):
        self.write(self.install / "xtras" / "b.dat", b"tampered")
        game = self.game_copy({})
        before = tree(self.prefix)
        self.refused(prefix.sync_game)
        self.assertEqual(tree(self.prefix), before)
        self.assertEqual(tree(game), {})

    def test_a_game_directory_that_links_to_another_place_inside_the_prefix_is_refused_too(self):
        other = self.prefix / "drive_c" / "other"
        self.write(other / "a.txt", b"alpha")
        self.write(other / "junk.txt", b"junk")
        os.symlink(other, self.prefix / "drive_c" / "iwp")
        before = tree(self.prefix)
        self.refused(prefix.sync_game)
        self.assertEqual(tree(self.prefix), before)

    def test_game_destination_refuses_any_overlap_with_the_install_on_its_own(self):
        game = self.prefix / "drive_c" / "iwp"
        game.mkdir()
        for label, install in {"install is the copy": game, "install contains the copy": game.parent}.items():
            with self.subTest(label), self.assertRaises(SystemExit):
                prefix.game_destination(self.prefix, install)
        self.assertEqual(prefix.game_destination(self.prefix, self.install), game)

    def test_a_manifest_path_that_leaves_the_set_is_refused(self):
        self.write(self.tmp / "escape.txt", b"x")          # a real, matching file one level above the install
        bad = dict(MANIFEST, files=[{"path": "../escape.txt", "bytes": 1, "sha256": sha(b"x")}])
        with mock.patch.object(prefix, "manifest", return_value=bad):
            before = tree(self.install)
            reason, _ = self.refused(prefix.sync_game)
            self.assertEqual(tree(self.install), before)
        self.assertIn("not a path inside the set", reason)     # refused for its form, before any later check
        self.assertFalse((self.prefix / "drive_c" / "escape.txt").exists())

    def test_the_game_copy_overlapping_the_install_is_refused_by_location_not_by_luck(self):
        os.environ["IWP_DIR"] = str(self.prefix / "drive_c" / "iwp")
        self.game_copy()
        before = tree(self.prefix)
        self.refused(prefix.sync_game)
        self.assertEqual(tree(self.prefix), before)


class LinksTest(World):
    """R3: a link that leaves the prefix is found by where it ends up, not by how it is written."""

    def good_prefix(self):
        self.game_copy()

    def test_a_good_prefix_checks_ok(self):
        self.good_prefix()
        self.assertEqual(prefix.prefix_problems(self.prefix), [])
        code, out = self.call(prefix.check)
        self.assertEqual((code, out.strip()), (0, "prefix ok"))

    def test_a_relative_link_that_escapes_is_found_removed_and_leaves_its_target_alone(self):
        self.good_prefix()
        desktop = self.prefix / "drive_c" / "users" / "u" / "Desktop"
        os.symlink("../../../../install", desktop)             # relative, resolves to the sibling install
        self.assertEqual((desktop / "a.txt").read_bytes(), b"alpha", "the fixture reads through the link")
        self.assertTrue(any("Desktop" in p for p in prefix.prefix_problems(self.prefix)))
        self.assertEqual(self.call(prefix.check)[0], 1)
        before = tree(self.install)
        self.call(prefix.strip_links)
        self.assertEqual(tree(self.install), before)
        self.assertTrue(desktop.is_dir() and not desktop.is_symlink())
        self.assertEqual(prefix.prefix_problems(self.prefix), [])

    def test_a_chain_of_links_that_ends_outside_is_found(self):
        self.good_prefix()
        os.symlink("hop", self.prefix / "drive_c" / "users" / "u" / "first")
        os.symlink("../../../../install", self.prefix / "drive_c" / "users" / "u" / "hop")
        found = [p for p in prefix.prefix_problems(self.prefix) if "link leaves" in p]
        self.assertEqual(len(found), 2)

    def test_a_link_that_stays_inside_the_prefix_is_not_an_escape(self):
        self.good_prefix()
        os.symlink("../../windows", self.prefix / "drive_c" / "users" / "u" / "inside")
        (self.prefix / "drive_c" / "windows").mkdir()
        self.assertEqual(prefix.prefix_problems(self.prefix), [])
        self.call(prefix.strip_links)
        self.assertTrue((self.prefix / "drive_c" / "users" / "u" / "inside").is_symlink())

    def test_an_escaping_link_outside_the_users_folder_is_removed_without_a_folder(self):
        self.good_prefix()
        link = self.prefix / "drive_c" / "windows"
        os.symlink("../../install", link)
        self.call(prefix.strip_links)
        self.assertFalse(link.exists() or link.is_symlink())

    def test_c_must_map_to_drive_c(self):
        self.good_prefix()
        c = self.prefix / "dosdevices" / "c:"
        for target in ("..", "../../install", "../drive_c/users", "../nothing"):
            with self.subTest(target=target):
                c.unlink()
                os.symlink(target, c)
                self.assertTrue(any("does not map to drive_c" in p or "leaves the prefix" in p
                                    for p in prefix.prefix_problems(self.prefix)))
                self.assertEqual(self.call(prefix.check)[0], 1)
                self.call(prefix.strip_links)
                self.assertEqual(prefix.prefix_problems(self.prefix), [])
                self.assertEqual(locations.real(c), locations.real(self.prefix / "drive_c"))

    def test_a_missing_c_mapping_is_found_and_repaired(self):
        self.good_prefix()
        (self.prefix / "dosdevices" / "c:").unlink()
        self.assertTrue(any("c: is not a link" in p for p in prefix.prefix_problems(self.prefix)))
        self.call(prefix.strip_links)
        self.assertEqual(prefix.prefix_problems(self.prefix), [])

    def test_any_other_drive_is_refused_even_when_it_points_inside(self):
        self.good_prefix()
        os.symlink("../drive_c", self.prefix / "dosdevices" / "d:")
        self.assertTrue(any("dosdevices/d: is mapped" in p for p in prefix.prefix_problems(self.prefix)))
        self.call(prefix.strip_links)
        self.assertEqual(sorted(p.name for p in (self.prefix / "dosdevices").iterdir()), ["c:"])

    def test_z_com_ports_and_absolute_links_are_all_removed(self):
        self.good_prefix()
        os.symlink("/", self.prefix / "dosdevices" / "z:")
        os.symlink("/dev/ttyS0", self.prefix / "dosdevices" / "com1")
        os.symlink("/", self.prefix / "drive_c" / "users" / "u" / "Documents")
        self.call(prefix.strip_links)
        self.assertEqual(prefix.prefix_problems(self.prefix), [])
        self.assertEqual(sorted(p.name for p in (self.prefix / "dosdevices").iterdir()), ["c:"])


class CheckIsolationTest(World):
    """R6: each fault alone makes `check` fail, and removing the artifact verification is noticed."""

    def setUp(self):
        super().setUp()
        self.game = self.game_copy()

    def only(self, fragment):
        problems = prefix.prefix_problems(self.prefix)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn(fragment, problems[0])
        code, out = self.call(prefix.check)
        self.assertEqual(code, 1)
        self.assertIn(fragment, out)

    def test_nothing_wrong_passes(self):
        self.assertEqual(self.call(prefix.check)[0], 0)

    def test_a_changed_game_file_alone_fails_the_check(self):
        (self.game / "a.txt").write_bytes(b"ALPHA")
        self.only("game copy")

    def test_a_missing_game_file_alone_fails_the_check(self):
        (self.game / "xtras" / "b.dat").unlink()
        self.only("missing")

    def test_a_file_outside_the_set_alone_fails_the_check(self):
        self.write(self.game / "stray.bin", b"x")
        self.only("unlisted")

    def test_a_game_directory_that_is_a_link_alone_fails_the_check(self):
        real_copy = self.tmp / "elsewhere"
        self.game.rename(real_copy)
        os.symlink(real_copy, self.game)
        problems = prefix.prefix_problems(self.prefix)
        self.assertTrue(any("leaves the prefix" in p for p in problems))
        self.assertTrue(any("not a real directory" in p for p in problems))

    def test_a_runtime_write_of_the_set_is_allowed(self):
        manifest = registered(dict(MANIFEST, files=MANIFEST["files"][:1], runtime_writes=["xtras/b.dat"]))
        (self.game / "xtras" / "b.dat").write_bytes(b"grown by the game")
        with mock.patch.object(prefix, "manifest", return_value=manifest):
            self.assertEqual(prefix.verify_game_copy(self.game), [])

    def test_verification_reports_each_kind_of_difference(self):
        self.assertEqual(prefix.verify_game_copy(self.game), [])
        (self.game / "a.txt").write_bytes(b"x")
        self.assertTrue(any("a.txt" in p for p in prefix.verify_game_copy(self.game)))
        self.assertTrue(prefix.verify_game_copy(self.tmp / "no-such-dir"))


class TokenChecksTest(World):
    """R6: the Wine, tool and artifact tokens reject what they should."""

    def fake(self, name, body, directory=None):
        directory = directory or self.tmp / "bin"
        directory.mkdir(exist_ok=True)
        path = directory / name
        path.write_text("#!/bin/sh\n" + body + "\n")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
        return path

    def fake_display(self, directory):
        """A fake Xvfb (records its display argument, then waits) and a fake xdpyinfo (answers once the
        Xvfb has recorded it), so start_xvfb works here without a real X server."""
        log = self.tmp / "xvfb-display"
        self.fake("Xvfb", f'echo "$1" > "{log}"; exec sleep 30', directory)
        self.fake("xdpyinfo", f'[ -s "{log}" ]', directory)

    def test_wine_accepts_exactly_a_9_0_build(self):
        good = self.fake("wine-good", 'echo "wine-9.0 (Ubuntu 9.0~repack-4build3)"')
        with mock.patch.object(token_check, "WINE", str(good)):
            self.assertIsNone(token_check.wine())

    def test_wine_rejects_another_version_a_failing_binary_and_a_missing_one(self):
        cases = {
            "older": self.fake("wine-old", 'echo "wine-8.0"'),
            "newer": self.fake("wine-new", 'echo "wine-10.1"'),
            "fails": self.fake("wine-fails", 'echo "wine-9.0"; exit 1'),
            "silent": self.fake("wine-silent", "exit 0"),
            "missing": self.tmp / "bin" / "absent",
        }
        for label, path in cases.items():
            with self.subTest(label), mock.patch.object(token_check, "WINE", str(path)):
                self.assertIsNotNone(token_check.wine())

    def test_tool_tokens_need_their_binaries_and_a_working_version_call(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        with mock.patch.dict(os.environ, {"PATH": str(empty)}):
            for check in (token_check.xvfb, token_check.xfwm4, token_check.xdotool, token_check.display):
                with self.subTest(check=check.__name__):
                    self.assertIsNotNone(check())
        bin_ok = self.tmp / "ok"
        self.fake("xfwm4", "exit 0", bin_ok)
        self.fake("xdotool", "exit 0", bin_ok)
        self.fake_display(bin_ok)
        bin_bad = self.tmp / "bad"
        self.fake("xfwm4", "exit 1", bin_bad)
        self.fake("xdotool", "exit 1", bin_bad)
        self.fake_display(bin_bad)
        with mock.patch.dict(os.environ, {"PATH": f"{bin_ok}{os.pathsep}/usr/bin{os.pathsep}/bin"}):
            self.assertIsNone(token_check.xfwm4())
            self.assertIsNone(token_check.xdotool())
        with mock.patch.dict(os.environ, {"PATH": f"{bin_bad}{os.pathsep}/usr/bin{os.pathsep}/bin"}):
            self.assertIsNotNone(token_check.xfwm4())
            self.assertIsNotNone(token_check.xdotool())

    def test_the_artifact_token_rejects_a_place_that_is_not_the_registered_set(self):
        self.assertIn("does not match", token_check.artifact())
        with mock.patch.dict(os.environ, {"IWP_PREFIX": "", "IWP_DIR": ""}):
            self.assertIn("neither", token_check.artifact())

    def test_the_prefix_token_needs_a_prefix_and_a_checked_one(self):
        with mock.patch.dict(os.environ, {"IWP_PREFIX": ""}):
            self.assertIn("not set", token_check.prefix())
        self.assertIsNotNone(token_check.prefix())     # the synthetic prefix has no registered game copy

    def test_python_must_be_3_11_or_newer(self):
        with mock.patch.object(token_check.sys, "version_info", (3, 10, 0)):
            self.assertIsNotNone(token_check.python())
        with mock.patch.object(token_check.sys, "version_info", (3, 11, 0)):
            self.assertIsNone(token_check.python())

    def test_the_main_entry_prints_unavailable_and_exits_1(self):
        script = ROOT / "setup" / "iwp" / "token_check.py"
        done = subprocess.run([sys.executable, str(script), "prefix"], capture_output=True, text=True,
                              env={**os.environ, "IWP_PREFIX": ""})
        self.assertEqual(done.returncode, 1)
        self.assertIn("unavailable", done.stdout)


class ReadyGatingTest(World):
    """R6: `ready` is printed, and 0 returned, only when every token passes."""

    # the Pro lane's tokens, the ones T09's "Runs on" names (facility:iwp-prefix included)
    PRO_TOKENS = ["tool:python@>=3.11", "tool:wine@10.0", "tool:xvfb", "tool:xfwm4", "tool:xdotool",
                  "facility:display", "artifact:iwp-2.0-996e86c5", "facility:iwp-prefix"]

    def test_all_tokens_passing_is_ready(self):
        lines, failed = tokens.run_tokens({"a": {"check": "echo verified"}, "b": {"check": "true"}})
        self.assertEqual(failed, [])

    def test_one_failing_token_is_named_and_blocks_ready(self):
        lines, failed = tokens.run_tokens({"a": {"check": "true"}, "b": {"check": "echo no >&2; exit 3"}})
        self.assertEqual(failed, ["b"])
        self.assertTrue(any(line.startswith("b: no") for line in lines))

    def test_an_empty_unreadable_or_commandless_capabilities_is_never_ready(self):
        self.assertTrue(tokens.run_tokens({})[1])
        self.assertTrue(tokens.run_tokens({"a": {}})[1])
        self.assertTrue(tokens.run_tokens({"a": {"check": "  "}})[1])
        self.assertTrue(tokens.run_tokens({"a": "true"})[1])

    def run_main(self, capabilities, extra=()):
        path = self.tmp / "capabilities.json"
        path.write_text(capabilities)
        out = io.StringIO()
        with redirect_stdout(out):
            code = tokens.main(["tokens.py", str(path), *extra])
        return code, out.getvalue().splitlines()

    def test_main_prints_ready_only_when_every_token_passes(self):
        code, lines = self.run_main(json.dumps({"a": {"check": "true"}, "b": {"check": "true"}}))
        self.assertEqual((code, lines[-1]), (0, "ready"))
        code, lines = self.run_main(json.dumps({"a": {"check": "true"}, "b": {"check": "false"}}))
        self.assertEqual(code, 1)
        self.assertNotIn("ready", lines)
        self.assertEqual(lines[-1], "not ready: b")
        code, lines = self.run_main("not json")
        self.assertEqual(code, 1)
        self.assertNotIn("ready", lines)

    def test_a_token_that_is_not_named_is_not_run_and_does_not_fail_the_verdict(self):
        code, lines = self.run_main(json.dumps({"pro": {"check": "true"},
                                                "iw-dos": {"check": "echo dos-ran >&2; exit 1"}}),
                                    extra=["--tokens", "pro"])
        self.assertEqual((code, lines[-1]), (0, "ready"))
        self.assertEqual(lines, ["pro: ", "ready"])

    def test_the_named_tokens_run_in_the_order_given(self):
        _, lines = self.run_main(json.dumps({"b": {"check": "true"}, "a": {"check": "true"}}),
                                 extra=["--tokens", "a,b"])
        self.assertEqual(lines, ["a: ", "b: ", "ready"])

    def test_a_named_token_that_capabilities_lacks_fails_and_is_never_skipped(self):
        code, lines = self.run_main(json.dumps({"pro": {"check": "true"}}), extra=["--tokens", "no:such"])
        self.assertEqual(code, 1)
        self.assertIn("no:such: not in capabilities.json", lines)
        self.assertEqual(lines[-1], "not ready: no:such")

    def test_an_empty_token_list_is_never_ready(self):
        code, lines = self.run_main(json.dumps({"pro": {"check": "true"}}), extra=["--tokens", ""])
        self.assertEqual(code, 1)
        self.assertNotIn("ready", lines)

    def test_a_repeated_tokens_option_is_refused(self):
        # R1: a second --tokens used to overwrite the first list, so `--tokens "" --tokens pro`
        # turned a not-ready empty list into a passing run.
        code, lines = self.run_main(json.dumps({"pro": {"check": "true"}}),
                                    extra=["--tokens", "", "--tokens", "pro"])
        self.assertEqual((code, lines), (1, ["not ready: --tokens given more than once"]))

    def test_a_second_positional_path_is_refused(self):
        # R1 for the path: the second positional used to overwrite the first silently, so the
        # verdict could come from a file that was not the one asked for first.
        other = self.tmp / "other-capabilities.json"
        other.write_text(json.dumps({"pro": {"check": "true"}}))
        code, lines = self.run_main(json.dumps({"pro": {"check": "false"}}), extra=[str(other)])
        self.assertEqual((code, lines), (1, ["not ready: capabilities path given more than once"]))

    def test_without_tokens_every_token_still_runs(self):
        code, lines = self.run_main(json.dumps({"a": {"check": "true"}, "b": {"check": "true"}}))
        self.assertEqual((code, lines[-1]), (0, "ready"))
        self.assertEqual(lines[:-1], ["a: ", "b: "])

    def test_the_profile_passes_exactly_the_pro_lanes_tokens(self):
        script = (ROOT / "setup" / "iwp" / "iwp-runtime.sh").read_text(encoding="utf-8")
        passed = re.search(r"--tokens\s+'([^']*)'", script)
        self.assertIsNotNone(passed, "iwp-runtime.sh must pass --tokens to tokens.py")
        self.assertEqual(passed.group(1).split(","), self.PRO_TOKENS)

    def test_the_profile_script_is_not_ready_without_its_locations_or_packages(self):
        script = ROOT / "setup" / "iwp" / "iwp-runtime.sh"
        bash = subprocess.run(["bash", "-c", "command -v bash"], capture_output=True, text=True).stdout.strip()
        empty = self.tmp / "empty-path"
        empty.mkdir()
        cases = {
            "no locations": {"PATH": os.environ["PATH"], "IWP_PREFIX": "", "IWP_DIR": ""},
            "no packages": {"PATH": str(empty), "IWP_PREFIX": str(self.prefix), "IWP_DIR": str(self.install)},
            "prefix in a checkout": {"PATH": os.environ["PATH"], "IWP_PREFIX": str(self.checkout / "prefix"),
                                     "IWP_DIR": str(self.install)},
        }
        for label, env in cases.items():
            with self.subTest(label):
                done = subprocess.run([bash, str(script)], capture_output=True, text=True, env=env, timeout=120)
                self.assertNotEqual(done.returncode, 0)
                self.assertNotIn("ready", done.stdout.splitlines())
                self.assertFalse((self.checkout / "prefix").exists())


class ProfileWiringTest(World):
    """R6: the profile script runs its steps in order, stops at the first failure, and is ready only
    when the token run says so. It is copied into a synthetic tree whose steps are stubs."""

    def setUp(self):
        super().setUp()
        self.fake_root = self.tmp / "fake-root"
        (self.fake_root / "setup" / "iwp").mkdir(parents=True)
        shutil.copy(ROOT / "setup" / "iwp" / "iwp-runtime.sh", self.fake_root / "setup" / "iwp" / "iwp-runtime.sh")
        self.log = self.tmp / "steps.log"
        self.bin = self.tmp / "stubs"
        self.bin.mkdir()
        for name in ("Xvfb", "xfwm4", "xdotool", "import", "xdpyinfo", "xprop", "unshare", "mount", "git"):
            self.stub(self.bin / name, "exit 0")
        os.symlink(sys.executable, self.bin / "python3")
        self.stub(self.tmp / "wine", "exit 0")

    @staticmethod
    def stub(path, body):
        path.write_text("#!/bin/sh\n" + body + "\n")
        path.chmod(0o755)

    def python_stub(self, name, code):
        (self.fake_root / "setup" / "iwp" / name).write_text(code)

    def steps(self, failing=None, tokens_exit=0):
        self.python_stub("prefix.py", "import sys\nopen(%r, 'a').write(sys.argv[1] + '\\n')\nsys.exit(%s)\n"
                         % (str(self.log), "1 if sys.argv[1] == %r else 0" % failing))
        self.python_stub("tokens.py", "import sys\nopen(%r, 'a').write('tokens\\n')\n"
                         "print('token lines')\nprint('ready' if %d == 0 else 'not ready: x')\nsys.exit(%d)\n"
                         % (str(self.log), tokens_exit, tokens_exit))

    def run_profile(self, **extra):
        env = {"PATH": str(self.bin), "IWP_PREFIX": str(self.prefix), "IWP_DIR": str(self.install),
               "IWP_WINE": str(self.tmp / "wine"), **extra}
        bash = subprocess.run(["bash", "-c", "command -v bash"], capture_output=True, text=True).stdout.strip()
        done = subprocess.run([bash, str(self.fake_root / "setup" / "iwp" / "iwp-runtime.sh")],
                              capture_output=True, text=True, env=env, timeout=60)
        logged = self.log.read_text().split() if self.log.exists() else []
        return done, logged

    def test_every_step_in_order_then_the_token_run_then_ready(self):
        self.steps()
        done, logged = self.run_profile()
        self.assertEqual(logged, ["build", "strip-links", "sync-game", "baseline", "tokens"])
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout.splitlines()[-1], "ready")

    def test_a_failing_step_stops_the_profile_before_the_tokens_and_is_not_ready(self):
        for failing in ("build", "strip-links", "sync-game", "baseline"):
            with self.subTest(failing=failing):
                if self.log.exists():
                    self.log.unlink()
                self.steps(failing=failing)
                done, logged = self.run_profile()
                self.assertNotEqual(done.returncode, 0)
                self.assertNotIn("tokens", logged)
                self.assertNotIn("ready", done.stdout.splitlines())
                self.assertIn(failing, done.stderr)

    def test_a_failing_token_run_is_not_ready_and_the_exit_code_is_not_zero(self):
        self.steps(tokens_exit=1)
        done, logged = self.run_profile()
        self.assertEqual(logged[-1], "tokens")
        self.assertEqual(done.returncode, 1)
        self.assertNotIn("ready", done.stdout.splitlines())

    def test_a_missing_package_names_it_and_runs_no_step(self):
        self.steps()
        (self.bin / "xfwm4").unlink()
        done, logged = self.run_profile()
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("xfwm4", done.stderr)
        self.assertEqual(logged, [])
        done, logged = self.run_profile(IWP_WINE=str(self.tmp / "no-wine"))
        self.assertIn("wine", done.stderr)
        self.assertEqual(logged, [])


class NetworkContractTest(World):
    """R4: the game runs only under N0, and a run says so only after looking."""

    def make_cycle(self):
        args = cycle.parser().parse_args([])
        made = cycle.Cycle(args, "E001-test", self.prefix, self.bundles)
        self.addCleanup(shutil.rmtree, made.workdir, True)
        return made

    def test_there_is_no_option_to_run_the_game_on_the_host_network(self):
        parsed = cycle.parser().parse_args([])
        self.assertFalse(hasattr(parsed, "net"))
        for argv in (["--net", "host"], ["--net=host"], ["--net", "n0"]):
            with self.subTest(argv=argv), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                cycle.parser().parse_args(argv)

    def test_the_game_is_always_started_under_unshare_n(self):
        self.assertEqual(cycle.game_command()[:2], ["unshare", "-n"])
        self.assertEqual(cycle.game_command()[-1], "Islepro.exe")
        seen = []

        class Stop(Exception):
            pass

        def fake_popen(cmd, **kw):
            seen.append(cmd)
            raise Stop

        run_cycle = self.make_cycle()
        self.game_copy()                       # a valid copy: launch seals the prefix before it starts the game
        with mock.patch.object(cycle.subprocess, "Popen", fake_popen), self.assertRaises(Stop), \
                redirect_stdout(io.StringIO()):
            run_cycle.launch()
        self.assertEqual(seen[0][:2], ["unshare", "-n"])

    def test_launch_verifies_isolation_right_after_starting_the_game(self):
        class Stop(Exception):
            pass

        run_cycle = self.make_cycle()
        self.game_copy()
        with mock.patch.object(cycle.subprocess, "Popen", return_value=mock.MagicMock()), \
                mock.patch.object(cycle, "poll", lambda *a, **k: None), \
                mock.patch.object(run_cycle, "verify_isolation", side_effect=Stop), redirect_stdout(io.StringIO()):
            with self.assertRaises(Stop):
                run_cycle.launch()

    def verify(self, pid, mine, theirs, interfaces):
        run_cycle = self.make_cycle()
        with mock.patch.object(run_cycle, "find_game_pid", return_value=pid), \
                mock.patch.object(cycle, "poll", lambda cond, timeout, interval=0.1: 0.0 if cond() else None), \
                mock.patch.object(cycle, "netns_of", lambda p: mine if p == "self" else theirs), \
                mock.patch.object(cycle, "interfaces_of", return_value=interfaces), \
                redirect_stdout(io.StringIO()):
            try:
                run_cycle.verify_isolation()
            except RuntimeError:
                pass
        return run_cycle

    def yes_observed(self, run_cycle):
        return any(o["field"] == "game in its own network namespace" and o["value"] == "yes" for o in run_cycle.obs)

    def test_isolation_is_recorded_only_when_it_was_seen(self):
        ok = self.verify(123, "net:[1]", "net:[2]", ["lo"])
        self.assertTrue(self.yes_observed(ok))
        self.assertEqual(ok.status, "running")    # not aborted; only complete() makes a run "completed"

    def test_no_game_process_found_aborts_and_records_no_isolation(self):
        bad = self.verify(None, "net:[1]", "net:[2]", ["lo"])
        self.assertFalse(self.yes_observed(bad))
        self.assertTrue(bad.status.startswith("aborted"))

    def test_the_same_namespace_aborts(self):
        bad = self.verify(123, "net:[1]", "net:[1]", ["lo"])
        self.assertFalse(self.yes_observed(bad))
        self.assertTrue(bad.status.startswith("aborted"))

    def test_an_interface_besides_lo_aborts(self):
        bad = self.verify(123, "net:[1]", "net:[2]", ["eth0", "lo"])
        self.assertFalse(self.yes_observed(bad))
        self.assertTrue(bad.status.startswith("aborted"))

    def test_an_unreadable_namespace_aborts(self):
        run_cycle = self.make_cycle()
        with mock.patch.object(run_cycle, "find_game_pid", return_value=123), \
                mock.patch.object(cycle, "poll", lambda cond, timeout, interval=0.1: 0.0 if cond() else None), \
                mock.patch.object(cycle, "netns_of", side_effect=OSError("gone")), redirect_stdout(io.StringIO()):
            with self.assertRaises(RuntimeError):
                run_cycle.verify_isolation()
        self.assertFalse(self.yes_observed(run_cycle))

    def test_interfaces_and_namespace_readers_read_proc(self):
        self.assertTrue(cycle.netns_of("self").startswith("net:["))
        self.assertIn("lo", cycle.interfaces_of("self"))


class StartStateTest(World):
    """R5: the start-state hash identifies the whole prefix, registry values included."""

    def base(self):
        return {"system.reg": ("f", 10, "aa" * 32), "user.reg": ("f", 20, "bb" * 32),
                "drive_c": ("d",), "drive_c/iwp/a.txt": ("f", 5, sha(b"alpha")), "dosdevices/c:": ("l", "../drive_c")}

    def test_equal_prefixes_give_equal_hashes(self):
        self.assertEqual(cycle.start_state_sha(self.base()), cycle.start_state_sha(dict(self.base())))
        self.assertRegex(cycle.start_state_sha(self.base()), r"^[0-9a-f]{64}$")

    def test_a_change_of_registry_values_with_the_same_key_names_changes_the_hash(self):
        changed = self.base()
        changed["user.reg"] = ("f", 20, "cc" * 32)
        self.assertNotEqual(cycle.start_state_sha(self.base()), cycle.start_state_sha(changed))

    def test_any_other_difference_in_the_prefix_changes_the_hash(self):
        for label, edit in {
            "game file": lambda t: t.update({"drive_c/iwp/a.txt": ("f", 5, sha(b"ALPHA"))}),
            "extra file": lambda t: t.update({"drive_c/new": ("f", 1, sha(b"x"))}),
            "link target": lambda t: t.update({"dosdevices/c:": ("l", "../elsewhere")}),
            "removed entry": lambda t: t.pop("drive_c"),
        }.items():
            with self.subTest(label):
                changed = self.base()
                edit(changed)
                self.assertNotEqual(cycle.start_state_sha(self.base()), cycle.start_state_sha(changed))

    def inner_hash(self, before_tree):
        record_root = self.tmp / "repo"
        (record_root / "runs").mkdir(parents=True, exist_ok=True)

        def fake_execute(self_):
            self_.status, self_.started, self_.ended = "completed", "2026-10-03T00:00:00Z", "2026-10-03T00:00:01Z"
            self_.snap_before = ({}, before_tree, {"user.reg: Software\\Wine\\A": "same-key-name-hash"})

        self.runs = getattr(self, "runs", 0) + 1         # records are never overwritten: one id per call
        run_id = f"E001-r{9900 + self.runs}"
        env = {"IWP_CYCLE_ID": run_id, "IWP_CYCLE_REP": "1", "IWP_CYCLE_COMMIT": "abcdef123456"}
        with mock.patch.dict(os.environ, env), mock.patch.object(cycle, "run"), \
                mock.patch.object(cycle, "ROOT", record_root), mock.patch.object(cycle, "versions", return_value={}), \
                mock.patch.object(cycle.Cycle, "execute", fake_execute), redirect_stdout(io.StringIO()):
            self.assertEqual(cycle.inner(cycle.parser().parse_args([])), 0)
        return json.loads((record_root / "runs" / "E001" / f"{run_id}.json").read_text())["start_state"]["sha256"]

    def test_inner_writes_a_hash_that_depends_on_the_registry_values(self):
        first = self.inner_hash(self.base())
        changed = self.base()
        changed["system.reg"] = ("f", 10, "dd" * 32)
        second = self.inner_hash(changed)
        self.assertNotEqual(first, second)
        self.assertEqual(first, self.inner_hash(self.base()))


if __name__ == "__main__":
    unittest.main()
