#!/usr/bin/env python3
"""Check the E020 sitting counts against the batch list's targets (T38, Done-when 8).

The batch list is `experiments/E020-wine-first-run/scenarios.txt`: one INI block per batch, with
the count targets Scope's Counts line names. This tool reads it, counts the observations of the
committed records under `runs/E020/<batch>/`, and prints, per batch, the target and the observed
count. It exits 0 only when every floor is met and when no outcome claims `corroborated` below the
walkthroughs/f011-questions.md target (the `corroborate_min` key).

Counting is by structural `field` values only, so it can never read an interpretation: a batch 1
exchange is four observations (`counter:attacker-before`, `counter:attacker-after`,
`counter:defender-before`, `counter:defender-after`), and a batch 2 bomb play is an `owner:victim`
observation. A record whose `schema` is not `run/1` is not counted (an `outcome.json` beside the
records is read separately, as the batch's declared outcome).

Usage: `python3 tools/check_counts.py experiments/E020-wine-first-run/scenarios.txt`.
"""
import configparser
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECORDS = ROOT / "runs" / "E020"
SCENARIOS = ROOT / "experiments" / "E020-wine-first-run" / "scenarios.txt"


def load_batches(path):
    """{batch name: {key: value}} from the `[batch <name>]` blocks of the scenarios file."""
    parser = configparser.ConfigParser(interpolation=None)
    if not parser.read(str(path)):
        raise SystemExit(f"cannot read the batch list: {path}")
    batches = {}
    for section in parser.sections():
        if not section.startswith("batch "):
            continue
        name = section.split(None, 1)[1].strip()
        batches[name] = dict(parser.items(section))
    return batches


def records_of(batch, records_root=RECORDS):
    """The parsed run/1 records under runs/E020/<batch>/, sorted by file name."""
    folder = Path(records_root) / batch
    if not folder.is_dir():
        return []
    out = []
    for path in sorted(folder.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(doc, dict) and doc.get("schema") == "run/1":
            out.append(doc)
    return out


def field_counts(records):
    """Counter of every observation `field` across the records."""
    counts = Counter()
    for doc in records:
        for obs in doc.get("observations", []):
            field = obs.get("field")
            if isinstance(field, str):
                counts[field] += 1
    return counts


def games_with_field(records, field):
    """How many distinct run ids carry at least one observation of `field`."""
    games = set()
    for doc in records:
        run_id = doc.get("run_id")
        for obs in doc.get("observations", []):
            if obs.get("field") == field:
                games.add(run_id if isinstance(run_id, str) else "<unknown>")
    return len(games), sorted(games)


def declared_outcome(batch, records_root=RECORDS):
    """The batch's declared outcome, or None when no outcome.json is committed yet."""
    path = Path(records_root) / batch / "outcome.json"
    if not path.is_file():
        return None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "malformed"
    return doc.get("outcome") if isinstance(doc, dict) else "malformed"


def check_batch(name, batch, records_root=RECORDS):
    """(problems, lines) for one batch: the printed lines and the failures that stop the tool."""
    records = records_of(name, records_root)
    counts = field_counts(records)
    lines = [f"batch {name}: {batch.get('questions', '')}"]
    problems = []

    if "exchanges_field" in batch:
        field = batch["exchanges_field"]
        observed = counts.get(field, 0)
        target = int(batch["exchanges_min"])
        sides = batch.get("exchanges_sides", "").split()
        lines.append(f"  exchanges ({field}): target >= {target}, observed {observed}")
        if observed < target:
            problems.append(f"{name}: {observed} exchanges, under the floor of {target}")
        for side in sides:
            if counts.get(side, 0) != observed:
                problems.append(f"{name}: {counts.get(side, 0)} {side} readings for {observed} exchanges; "
                                f"an exchange needs a before and an after for both sides")
        corroborate = int(batch.get("corroborate_min", target))
        outcome = declared_outcome(name, records_root)
        lines.append(f"  outcome: {outcome if outcome is not None else 'none declared'}; "
                     f"corroboration needs >= {corroborate}")
        if outcome == "corroborated" and observed < corroborate:
            problems.append(f"{name}: outcome corroborated at {observed} exchanges, below the "
                            f"walkthroughs/f011-questions.md target of {corroborate}")

    if "bomb_plays_field" in batch:
        field = batch["bomb_plays_field"]
        plays = counts.get(field, 0)
        target = int(batch["bomb_plays_min"])
        games, _ids = games_with_field(records, field)
        games_target = int(batch.get("games_min", 0))
        lines.append(f"  bomb plays ({field}): target >= {target}, observed {plays}")
        lines.append(f"  games: target >= {games_target}, observed {games}")
        if plays < target:
            problems.append(f"{name}: {plays} computer bomb plays, under the floor of {target}")
        if games < games_target:
            problems.append(f"{name}: {plays} bomb plays across {games} game(s), under the floor "
                            f"of {games_target} games")

    if "exchanges_field" not in batch and "bomb_plays_field" not in batch:
        problems.append(f"{name}: the batch names no count rule (exchanges_field or bomb_plays_field)")
    return problems, lines


def check(scenarios=SCENARIOS, records_root=RECORDS):
    """(problems, lines) for every batch of the scenarios file."""
    batches = load_batches(scenarios)
    if not batches:
        return [f"{scenarios}: no [batch ...] block found"], []
    problems, lines = [], []
    for name, batch in batches.items():
        batch_problems, batch_lines = check_batch(name, batch, records_root)
        problems += batch_problems
        lines += batch_lines
    return problems, lines


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if len(argv) != 1:
        print("usage: check_counts.py <scenarios.txt>")
        return 2
    problems, lines = check(Path(argv[0]))
    print("\n".join(lines))
    for problem in problems:
        print(f"FAIL {problem}")
    if problems:
        return 1
    print("counts ok: every batch meets its floor")
    return 0


if __name__ == "__main__":
    sys.exit(main())
