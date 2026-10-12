#!/usr/bin/env python3
"""Write runs/coverage.md: every research question the recorded play has touched, its outcome per source, and what is still open.

    python3 tools/coverage.py            # rewrite runs/coverage.md
    python3 tools/coverage.py --check    # exit 1 when runs/coverage.md is not what the records give

Sources, read only (CLAUDE.md "The goal is a fun game", the owner, 2026-10-11):
- `runs/E018/CORRECTIONS.md`: the per-question index of the owner's recordings. Each sitting is a
  top-level `# ` section (the first, before any `# IP1 …` heading, is IP1 025); each question is a
  `##` or `###` heading naming one or more ids (`Q-CMB-01`, `C-AI-05`, …) followed by a
  `- **Status:** <outcome>` line.
- `experiments/E021-pro-session-a/measurements/progress-rNN.json` (the newest): the model sittings'
  Session A cells, mapped to the questions they serve (CELL_QUESTIONS).

Outcome words follow `walkthroughs/f011-questions.md`: corroborated > narrowed > unestablished.
A question is "covered" when some source corroborates it, and open otherwise. The page is derived:
records stay the source, and nothing here is a claim of its own (rule 20).
"""
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
INDEX = ROOT / "runs/E018/CORRECTIONS.md"
PROGRESS = ROOT / "experiments/E021-pro-session-a/measurements"
OUT = ROOT / "runs/coverage.md"
PLAN = ROOT / "walkthroughs/f011-questions.md"   # the planned questions, with their count targets

RANK = {"corroborated": 3, "narrowed": 2, "unestablished": 1}
ID = re.compile(r"\b(?:Q|C)-[A-Z]{2,3}-\d{2}\b")
# Session A's rows (experiments/E021-pro-session-a/cases.py) and the questions each serves
CELL_QUESTIONS = {"even": "Q-CMB-01", "underdog": "Q-CMB-02", "tiny": "Q-CMB-03",
                  "quit": "Q-CMB-08", "lost": "Q-CMB-09", "busy": "Q-CMB-10"}


def outcome(text):
    """The outcome word a status line starts with, or None."""
    m = re.match(r"\s*(corroborated|narrowed|unestablished)", text, re.I)
    return m.group(1).lower() if m else None


def read_index(text):
    """{question id: {"title": str, "sources": {sitting: outcome}}} from the per-question index."""
    questions = {}
    sitting, ids, title, family = "IP1 025", [], None, False
    for line in text.splitlines():
        if line.startswith("# "):
            m = re.match(r"# (IP1 \d+)", line)
            if m:
                sitting = m.group(1)
            ids = []
            continue
        if line.startswith("## ") or line.startswith("### "):
            found = ID.findall(line)
            # a heading names its Q ids, with the claim ids in brackets; a C id stands alone only
            # when the heading names no Q id (e.g. "C-AI-05 (Q-AI-04's move half)" names both)
            ids = [i for i in found if i.startswith("Q-")] or found
            title = re.split(r"\s+[—-]\s+", line.lstrip("#").strip(), maxsplit=1)
            title = title[1] if len(title) > 1 else title[0]
            family = ".." in line           # "Q-CMB-01..11": one heading for a whole family
            continue
        m = re.match(r"- \*\*Status:\*\*(.*)", line)
        if m and ids:
            word = outcome(m.group(1))
            if word is None:
                continue
            for qid in ids:
                q = questions.setdefault(qid, {"title": title, "sources": {}})
                if not family and (q.get("family", True) or not q["title"]):
                    q["title"], q["family"] = title, False   # a question's own heading names it
                elif "family" not in q:
                    q["family"] = family
                prev = q["sources"].get(sitting)
                if prev is None or RANK[word] > RANK[prev]:
                    q["sources"][sitting] = word
            ids = []
    return questions


def read_plan(text):
    """{question id: what to record} from the plan's table rows (`| Q-… | C-… | target | what |`)."""
    plan = {}
    for line in text.splitlines():
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) >= 4 and re.fullmatch(r"Q-[A-Z]{2,3}-\d{2}", cols[0]):
            plan[cols[0]] = cols[3]
    return plan


def newest_progress(folder):
    """(file name, parsed JSON) of the highest-numbered progress-rNN.json, or (None, None)."""
    files = sorted(folder.glob("progress-r*.json"), key=lambda p: int(re.sub(r"\D", "", p.stem) or 0))
    if not files:
        return None, None
    return files[-1].name, json.loads(files[-1].read_text(encoding="utf-8"))


def render(questions, progress_name, progress, plan=None):
    """The page, as a string. A planned question no source has touched yet gets a row too."""
    for qid, what in (plan or {}).items():
        questions.setdefault(qid, {"title": what, "sources": {}})
    cells = {}
    if progress:
        for row, q in CELL_QUESTIONS.items():
            r = progress.get("rows", {}).get(row)
            if r is not None:
                cells[q] = f"{r['met']}/{r['total']} cells ({row})"
                questions.setdefault(q, {"title": "", "sources": {}})
    lines = [
        "# Coverage of the research questions by recorded play",
        "",
        "Generated by `python3 tools/coverage.py` from `runs/E018/CORRECTIONS.md` (the owner's recordings)",
        f"and `experiments/E021-pro-session-a/measurements/{progress_name or '—'}` (the model sittings' Session A).",
        "Do not edit by hand: regenerate after a recording or a sitting is added. The records are the source;",
        "this page claims nothing of its own. Outcome words: corroborated > narrowed > unestablished",
        "(`walkthroughs/f011-questions.md`, which also lists the planned questions; \"—\" = not yet touched). Counts are nice to have (CLAUDE.md, \"The goal is a fun game\"):",
        "an open row is worth playing only when a session covers it naturally.",
        "",
    ]
    sittings = sorted({s for q in questions.values() for s in q["sources"]})
    head = ["Question", "What", "Best"] + sittings + ["Model sittings"]
    lines.append("| " + " | ".join(head) + " |")
    lines.append("| " + " | ".join("---" for _ in head) + " |")

    def best(q):
        ranks = [RANK[w] for w in q["sources"].values()]
        return {3: "corroborated", 2: "narrowed", 1: "unestablished"}[max(ranks)] if ranks else "—"

    def order(qid):
        area, num = qid.split("-")[1], int(qid.split("-")[2])
        return (qid[0] != "Q", area, num)

    counts = {}
    for qid in sorted(questions, key=order):
        q = questions[qid]
        b = best(q)
        counts[b] = counts.get(b, 0) + 1
        row = [qid, q["title"].replace("|", "/"), f"**{b}**" if b == "corroborated" else b]
        row += [q["sources"].get(s, "") for s in sittings]
        row.append(cells.get(qid, ""))
        lines.append("| " + " | ".join(row) + " |")
    lines += ["", "Totals by best outcome: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) + "."]
    return "\n".join(lines) + "\n"


def build():
    name, progress = newest_progress(PROGRESS)
    plan = read_plan(PLAN.read_text(encoding="utf-8")) if PLAN.exists() else {}
    return render(read_index(INDEX.read_text(encoding="utf-8")), name, progress, plan)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail when runs/coverage.md is stale")
    a = parser.parse_args(argv)
    page = build()
    if a.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != page:
            print("runs/coverage.md is stale: run python3 tools/coverage.py", file=sys.stderr)
            return 1
        print("runs/coverage.md is current")
        return 0
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
