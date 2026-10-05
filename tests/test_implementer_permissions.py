"""The OpenCode implementer's permissions outside its worktree (T31).

The implementer may read the static folder (~/.local/share/isle-wars-archaeology/static/) and
nothing else outside its worktree. It still edits its worktree, but never the static folder, and the
plain shell writes into that folder are denied. /tmp stays rejected (the T13 lesson): no TMPDIR
outside the worktree is granted.

The rules are read from .opencode/agents/implementer.md and evaluated as in T29's test
(tests/test_reviewer_permissions.py, which holds OpenCode 1.18.34's rules as read from its source).
One more fact, from the same source: the edit, write and apply_patch tools all ask `edit` with the
file's path *relative to the worktree root* (path.relative(worktree, file)), so a file in the static
folder is, for example, `../../.local/share/isle-wars-archaeology/static/a.ls`; `edit` takes
per-path patterns (OpenCode's own config help says so: "Within an object, insertion order matters").
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_reviewer_permissions import DEFAULTS, HOME, STATIC, evaluate, expand, frontmatter_rules

ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / ".opencode" / "agents" / "implementer.md"

EXPECTED_EXTERNAL = {
    "/tmp/opencode/*": "deny",
    "~/.local/share/isle-wars-archaeology/static/*": "allow",
}
EXPECTED_EDIT = [("*", "allow"), ("*.local/share/isle-wars-archaeology/static/*", "deny")]
# Relative paths from a worktree root, at different depths, to a file in the static folder.
RELATIVE_STATIC = ("../../.local/share/isle-wars-archaeology/static/a.ls",
                   "../../../../../.local/share/isle-wars-archaeology/static/ghidra-x/sub/b.ls",
                   "../.local/share/isle-wars-archaeology/static/new.txt")


def agent_rules(home=HOME):
    rules = frontmatter_rules(AGENT.read_text(encoding="utf-8"))
    return DEFAULTS + [(p, expand(pat, home), a) for p, pat, a in rules]


class ImplementerPermissions(unittest.TestCase):
    def setUp(self):
        self.text = AGENT.read_text(encoding="utf-8")
        self.rules = agent_rules()

    def outside(self, directory):
        return evaluate("external_directory", f"{directory}/*", self.rules)

    def shell(self, command):
        return evaluate("bash", command, self.rules)

    def test_grants_exactly_the_static_folder(self):
        got = {pat: a for p, pat, a in frontmatter_rules(self.text) if p == "external_directory"}
        self.assertEqual(got, EXPECTED_EXTERNAL)

    def test_static_folder_is_readable(self):
        for d in (STATIC, f"{STATIC}/deark-exe-r1", f"{STATIC}/ghidra-dos-exe-r1/sub"):
            self.assertEqual(self.outside(d), "allow", d)

    def test_every_other_outside_path_is_rejected(self):
        for d in (f"{HOME}/.local/share/isle-wars-archaeology/E007-bundles",
                  f"{HOME}/.local/share/isle-wars-archaeology",
                  f"{HOME}/.local/share/isle-wars-archaeology/static-other",
                  f"{HOME}/.local/share/isle-wars-archaeology/iwp.wineprefix/drive_c",
                  f"{HOME}/.local/share", HOME, f"{HOME}/.ssh", f"{HOME}/projects/isle-wars-archaeology",
                  "/tmp", "/tmp/iwa-review-a1B2c3", "/tmp/iwa-other", "/tmp/opencode", "/tmp/harness-opencode",
                  "/mnt/c/Users", "/"):
            self.assertNotEqual(self.outside(d), "allow", d)

    def test_edit_rules_deny_the_static_folder_only(self):
        edits = [(pat, a) for p, pat, a in frontmatter_rules(self.text) if p == "edit"]
        self.assertEqual(edits, EXPECTED_EDIT)
        for f in ("docs/models.md", "tests/test_x.py", ".opencode/agents/implementer.md", "src/a/static/x.ts"):
            self.assertEqual(evaluate("edit", f, self.rules), "allow", f)
        for f in RELATIVE_STATIC:
            self.assertEqual(evaluate("edit", f, self.rules), "deny", f)
        # a sibling folder is not the static folder
        self.assertNotEqual(
            evaluate("edit", "../../.local/share/isle-wars-archaeology/static-other/x", self.rules), "deny")

    def test_shell_writes_into_static_folder_are_denied(self):
        for path in ("~/.local/share/isle-wars-archaeology/static", STATIC, "$IWA_STATIC", "${IWA_STATIC}"):
            for cmd in (f"rm -rf {path}/x", f"rm {path}/a.ls", f"rmdir {path}/d", f"unlink {path}/a",
                        f"mv {path}/a {path}/b", f"mv x {path}/", f"cp x {path}/y", f"cp {path}/a.ls x",
                        f"touch {path}/new", f"mkdir -p {path}/d", f"chmod 000 {path}/a",
                        f"chown u {path}/a", f"truncate -s 0 {path}/a", f"tee {path}/f",
                        f"sed -i s/a/b/ {path}/a.ls", f"sed -i.bak s/a/b/ {path}/a.ls",
                        f"echo x > {path}/f", f"echo x >> {path}/f", f'printf x >"{path}/f"'):
                self.assertEqual(self.shell(cmd), "deny", cmd)

    def test_shell_reads_of_static_folder_and_worktree_work_are_allowed(self):
        s = "~/.local/share/isle-wars-archaeology/static"
        for cmd in (f"sha256sum {s}/deark-exe-r1/a.ls", f"cat {s}/a.ls", f"grep -rn handler {s}",
                    f"ls {s}", f"head -n 20 {s}/a.ls", f"sed -n 1,5p {s}/a.ls",
                    f"sha256sum {s}/a.ls 2>err.txt", "git add -A", "git commit -m x", "git push origin x",
                    "git checkout -- tools/a.py", "rm err.txt", "gh pr create --title x --body y",
                    "python3 -m unittest discover -s tests", "sed -i s/a/b/ docs/models.md"):
            self.assertEqual(self.shell(cmd), "allow", cmd)

    def test_earlier_denies_are_kept(self):
        for cmd in ("git push --force origin x", "git push -f origin x", "git stash", "git worktree add x",
                    "git -C . push --force origin x", "git -C . stash", "git -C . worktree list",
                    "gh pr merge 1", "gh pr review 1", "gh issue edit 1"):
            self.assertEqual(self.shell(cmd), "deny", cmd)
        self.assertEqual(evaluate("task", "general", self.rules), "deny")

    def test_no_machine_path_in_the_agent_file(self):
        self.assertIsNone(re.search(r"/home/|/mnt/|/Users/", self.text))

    def test_prose_names_the_one_read_only_exception(self):
        prose = self.text.split("---", 2)[2]
        self.assertIn("~/.local/share/isle-wars-archaeology/static/", prose)
        self.assertIn("never write it", prose)
        self.assertIn("never copy a line of it into the", prose)
        self.assertIn("rule 18", prose)
        self.assertNotIn("no temp directory, home directory, main checkout or other worktree.", prose)
        self.assertNotIn("iwa-review", prose)  # no /tmp grant

    @unittest.skipUnless(shutil.which("opencode"), "OpenCode is not installed here (CI); the mirror above still runs")
    def test_opencode_resolves_the_same_rules(self):
        """OpenCode's own reading of the agent file: `~/` expanded, and the same verdicts."""
        with tempfile.TemporaryDirectory(prefix="iwa-t31-") as tmp:
            env = {k: v for k, v in os.environ.items() if not k.startswith("OPENCODE_")}
            env.update(OPENCODE_CONFIG_DIR=str(ROOT / ".opencode"), OPENCODE_DISABLE_PROJECT_CONFIG="1",
                       XDG_DATA_HOME=f"{tmp}/data", XDG_CACHE_HOME=f"{tmp}/cache", XDG_STATE_HOME=f"{tmp}/state")
            out = subprocess.run(["opencode", "debug", "agent", "implementer"], cwd=tmp, env=env,
                                 capture_output=True, text=True, timeout=180)
        self.assertEqual(out.returncode, 0, out.stderr[-500:])
        agent = json.loads(out.stdout[out.stdout.index("{"):])
        resolved = [(r["permission"], r["pattern"], r["action"]) for r in agent["permission"]]
        home = str(Path.home())
        static = f"{home}/.local/share/isle-wars-archaeology/static"
        self.assertIn(("external_directory", f"{static}/*", "allow"), resolved)
        self.assertNotIn("/tmp/iwa-review-*", [p for perm, p, a in resolved if perm == "external_directory"])
        mine = agent_rules(home)
        for d in (static, f"{static}/x", f"{home}/.local/share/isle-wars-archaeology/E007-bundles",
                  "/tmp", "/tmp/opencode", "/tmp/iwa-review-a1", home):
            self.assertEqual(evaluate("external_directory", f"{d}/*", resolved),
                             evaluate("external_directory", f"{d}/*", mine), d)
        for f in (*RELATIVE_STATIC, "docs/models.md"):
            self.assertEqual(evaluate("edit", f, resolved), evaluate("edit", f, mine), f)
        for cmd in (f"rm -rf {static}/x", f"sha256sum {static}/a.ls", "git push origin x", "git add -A",
                    f"echo x > {static}/f"):
            self.assertEqual(evaluate("bash", cmd, resolved), evaluate("bash", cmd, mine), cmd)


if __name__ == "__main__":
    unittest.main()
