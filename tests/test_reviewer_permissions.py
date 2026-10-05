"""The OpenCode reviewer's permissions outside its worktree (T29).

The reviewer may read the static folder (~/.local/share/isle-wars-archaeology/static/) and use one
scratch TMPDIR under /tmp/iwa-review-*; every other path outside its worktree stays rejected, and
the edit tool and the plain shell writes into the static folder are denied.

The rules are read from .opencode/agents/reviewer.md and evaluated the way OpenCode 1.18.34 does,
from its own source (the bundled JavaScript of ~/.opencode/bin/opencode):
- Permission.fromConfig turns each `permission: pattern: action` into a rule, expanding a leading
  `~/` or `$HOME/` to the home directory, and no other variable;
- Wildcard.match turns `*` into `.*` (it crosses `/` and spaces) and `?` into `.`, makes a trailing
  ` *` optional, and matches the whole string;
- Permission.evaluate takes the last matching rule, else `ask`, which a non-interactive run
  auto-rejects;
- a file tool or a path-taking shell command (cd, rm, cp, mv, mkdir, touch, chmod, chown, cat) asks
  `external_directory` for `<directory>/*`: the file's directory, or the directory itself.
The last test checks this reading against `opencode debug agent reviewer` where OpenCode is installed.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / ".opencode" / "agents" / "reviewer.md"
REVIEW = ROOT / "tools" / "harness" / "review.mjs"
HOME = "/home/someone"  # a synthetic home: no machine path is assumed
STATIC = f"{HOME}/.local/share/isle-wars-archaeology/static"

EXPECTED_EXTERNAL = {
    "/tmp/opencode/*": "deny",
    "~/.local/share/isle-wars-archaeology/static/*": "allow",
    "/tmp/iwa-review-*": "allow",
}
# What OpenCode puts before an agent's own rules (as `opencode debug agent` lists them): allow all,
# ask for any outside directory, and its own /tmp/opencode allowance, which the agent denies (L43).
DEFAULTS = [("*", "*", "allow"), ("external_directory", "*", "ask"),
            ("external_directory", "/tmp/opencode/*", "allow")]


def frontmatter_rules(text):
    """The agent's permission rules, in order, as (permission, pattern, action), unexpanded."""
    head = text.split("---", 2)[1]
    rules, inside, current = [], False, None
    unq = lambda s: s.strip().strip('"')  # noqa: E731
    for line in head.splitlines():
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0:
            inside = line.strip() == "permission:"
            continue
        if not inside:
            continue
        key, _, value = line.strip().rpartition(":") if indent == 4 else line.strip().partition(":")
        if indent == 2:
            current = unq(key)
            if value.strip():
                rules.append((current, "*", value.strip()))
        elif indent == 4:
            rules.append((current, unq(key), value.strip()))
        else:
            raise ValueError(f"unexpected indentation: {line!r}")
    return rules


def expand(pattern, home=HOME):
    """Permission.fromConfig's expansion of a pattern (OpenCode 1.18.34)."""
    if pattern.startswith("~/"):
        return home + pattern[1:]
    if pattern == "~":
        return home
    if pattern.startswith("$HOME"):
        return home + pattern[5:]
    return pattern


def match(text, pattern):
    """Wildcard.match (OpenCode 1.18.34)."""
    text, pattern = text.replace("\\", "/"), pattern.replace("\\", "/")
    rx = re.sub(r"[.+^${}()|\[\]\\]", lambda m: "\\" + m.group(0), pattern)
    rx = rx.replace("*", ".*").replace("?", ".")
    if rx.endswith(" .*"):
        rx = rx[:-3] + "( .*)?"
    return re.fullmatch(rx, text, re.S) is not None


def evaluate(permission, pattern, rules):
    """Permission.evaluate: the last matching rule wins; none means ask (auto-rejected)."""
    for perm, pat, action in reversed(rules):
        if match(permission, perm) and match(pattern, pat):
            return action
    return "ask"


def agent_rules(home=HOME):
    rules = frontmatter_rules(AGENT.read_text(encoding="utf-8"))
    return DEFAULTS + [(p, expand(pat, home), a) for p, pat, a in rules]


class ReviewerPermissions(unittest.TestCase):
    def setUp(self):
        self.text = AGENT.read_text(encoding="utf-8")
        self.rules = agent_rules()

    def outside(self, directory):
        return evaluate("external_directory", f"{directory}/*", self.rules)

    def shell(self, command):
        return evaluate("bash", command, self.rules)

    def test_grants_exactly_the_two_places(self):
        got = {pat: a for p, pat, a in frontmatter_rules(self.text) if p == "external_directory"}
        self.assertEqual(got, EXPECTED_EXTERNAL)

    def test_static_folder_is_readable(self):
        for d in (STATIC, f"{STATIC}/deark-exe-r1", f"{STATIC}/ghidra-dos-exe-r1/sub"):
            self.assertEqual(self.outside(d), "allow", d)

    def test_scratch_tmpdir_is_usable(self):
        for d in ("/tmp/iwa-review-a1B2c3", "/tmp/iwa-review-a1B2c3/sub"):
            self.assertEqual(self.outside(d), "allow", d)

    def test_every_other_outside_path_is_rejected(self):
        for d in (f"{HOME}/.local/share/isle-wars-archaeology/E007-bundles",
                  f"{HOME}/.local/share/isle-wars-archaeology",
                  f"{HOME}/.local/share/isle-wars-archaeology/static-other",
                  f"{HOME}/.local/share/isle-wars-archaeology/iwp.wineprefix/drive_c",
                  f"{HOME}/.local/share", HOME, f"{HOME}/.ssh", f"{HOME}/projects/isle-wars-archaeology",
                  "/tmp", "/tmp/iwa-other", "/tmp/opencode", "/tmp/harness-opencode", "/mnt/c/Users", "/"):
            self.assertNotEqual(self.outside(d), "allow", d)

    def test_edit_tool_is_denied_everywhere(self):
        edits = [(pat, a) for p, pat, a in frontmatter_rules(self.text) if p == "edit"]
        self.assertEqual(edits, [("*", "deny")])
        for f in (f"{STATIC}/a.ls", "/tmp/iwa-review-a1B2c3/x", "docs/models.md"):
            self.assertEqual(evaluate("edit", f, self.rules), "deny", f)

    def test_shell_writes_into_static_folder_are_denied(self):
        for path in ("~/.local/share/isle-wars-archaeology/static", STATIC, "$IWA_STATIC", "${IWA_STATIC}"):
            for cmd in (f"rm -rf {path}/x", f"rm {path}/a.ls", f"rmdir {path}/d", f"unlink {path}/a",
                        f"mv {path}/a {path}/b", f"mv x {path}/", f"cp x {path}/y", f"cp {path}/a.ls x",
                        f"touch {path}/new", f"mkdir -p {path}/d", f"chmod 000 {path}/a",
                        f"chown u {path}/a", f"truncate -s 0 {path}/a", f"tee {path}/f",
                        f"sed -i s/a/b/ {path}/a.ls", f"sed -i.bak s/a/b/ {path}/a.ls",
                        f"echo x > {path}/f", f"echo x >> {path}/f", f'printf x >"{path}/f"'):
                self.assertEqual(self.shell(cmd), "deny", cmd)

    def test_shell_reads_of_static_folder_and_tmpdir_work_are_allowed(self):
        s = "~/.local/share/isle-wars-archaeology/static"
        for cmd in (f"sha256sum {s}/deark-exe-r1/a.ls", f"cat {s}/a.ls", f"grep -rn handler {s}",
                    f"ls {s}", f"head -n 20 {s}/a.ls", f"sed -n 1,5p {s}/a.ls",
                    f"sha256sum {s}/a.ls 2>review-err.txt", f"sha256sum {s}/a.ls > /tmp/iwa-review-a1/h",
                    "mktemp -d /tmp/iwa-review-XXXXXX", "rm -rf /tmp/iwa-review-a1B2c3",
                    "TMPDIR=/tmp/iwa-review-a1B2c3 python3 -m unittest discover -s tests",
                    "git checkout -- tools/a.py", "rm review-err.txt"):
            self.assertEqual(self.shell(cmd), "allow", cmd)

    def test_earlier_denies_are_kept(self):
        for cmd in ("git push origin x", "git -C . push origin x", "git commit -m x", "gh pr merge 1",
                    "gh pr comment 1 -b x", "gh pr review 1", "gh pr edit 1", "gh issue edit 1",
                    "gh issue comment 1 -b x"):
            self.assertEqual(self.shell(cmd), "deny", cmd)
        self.assertEqual(evaluate("task", "general", self.rules), "deny")

    def test_no_machine_path_in_the_agent_file(self):
        self.assertIsNone(re.search(r"/home/|/mnt/|/Users/", self.text))

    def test_rules_text_says_what_is_allowed(self):
        prose = self.text.split("---", 2)[2]
        rules = REVIEW.read_text(encoding="utf-8")
        rules = rules[rules.index("OUTPUT RULES"):rules.index("The task has")]
        for text in (prose, rules):
            self.assertIn("~/.local/share/isle-wars-archaeology/static/", text)
            self.assertIn("mktemp -d /tmp/iwa-review-XXXXXX", text)
            self.assertIn("git checkout -- <file>", text)
        self.assertNotIn("no temp directory", prose)
        self.assertNotIn("never `/tmp`.", prose)

    @unittest.skipUnless(shutil.which("opencode"), "OpenCode is not installed here (CI); the mirror above still runs")
    def test_opencode_resolves_the_same_rules(self):
        """OpenCode's own reading of the agent file: `~/` expanded, and the same verdicts."""
        with tempfile.TemporaryDirectory(prefix="iwa-t29-") as tmp:
            env = {k: v for k, v in os.environ.items() if not k.startswith("OPENCODE_")}
            env.update(OPENCODE_CONFIG_DIR=str(ROOT / ".opencode"), OPENCODE_DISABLE_PROJECT_CONFIG="1",
                       XDG_DATA_HOME=f"{tmp}/data", XDG_CACHE_HOME=f"{tmp}/cache", XDG_STATE_HOME=f"{tmp}/state")
            out = subprocess.run(["opencode", "debug", "agent", "reviewer"], cwd=tmp, env=env,
                                 capture_output=True, text=True, timeout=180)
        self.assertEqual(out.returncode, 0, out.stderr[-500:])
        agent = json.loads(out.stdout[out.stdout.index("{"):])
        resolved = [(r["permission"], r["pattern"], r["action"]) for r in agent["permission"]]
        home = str(Path.home())
        static = f"{home}/.local/share/isle-wars-archaeology/static"
        self.assertIn(("external_directory", f"{static}/*", "allow"), resolved)
        self.assertIn(("external_directory", "/tmp/iwa-review-*", "allow"), resolved)
        mine = agent_rules(home)
        for d in (static, f"{static}/x", "/tmp/iwa-review-a1", f"{home}/.local/share/isle-wars-archaeology/E007-bundles",
                  "/tmp", "/tmp/opencode", home):
            self.assertEqual(evaluate("external_directory", f"{d}/*", resolved),
                             evaluate("external_directory", f"{d}/*", mine), d)
        for cmd in (f"rm -rf {static}/x", f"sha256sum {static}/a.ls", "git push origin x"):
            self.assertEqual(evaluate("bash", cmd, resolved), evaluate("bash", cmd, mine), cmd)


if __name__ == "__main__":
    unittest.main()
