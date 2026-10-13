#!/usr/bin/env python3
"""Check the E020 sitting counts against the batch list's targets (T38, Done-when 8).

The batch list is `experiments/E020-wine-first-run/scenarios.txt`: one INI block per batch, with
the count targets Scope's Counts line names. This tool reads it, reads the committed records under
`runs/E020/<batch>/`, and prints, per batch, the target and the observed count. It exits 0 only
when every floor is met and no claim is declared `corroborated` without its own per-arm target.

What is counted (T38 round 2, R8 and R9: a count is of complete, uniquely identified events and
real games, never of field occurrences or export ids):

* An **event** is one exchange (batch 1) or one computer bomb play (batch 2). In a record it is the
  group of observations sharing one `step` > 0. The group carries `game:ordinal` and `event:seq`
  once each, every field the batch's `event_fields` names once each, every value valid for its
  field's role (`value_problem`), and at least two `ref` observations (the frames it was read
  from, before and after), each a file the record's `outputs` holds. A group that misses any of it
  is a problem, never a partial count.
* An event's identity is (sitting, game, seq): the sitting is the record's one `sitting:epoch`
  observation (the sitting directory's start time), the game is the game ordinal the sitting's
  click-driver logged when it started that game. Run ids are never identities: a re-read of one
  sitting writes a new record with a new run id and the same events, which are counted once (two
  re-reads that disagree on an event are a problem); two events with one identity in one record
  are a problem.
* A **game** is a distinct (sitting, game) pair among the counted events.
* A **net observation** (T40 round 2, R1) is a group that carries `net:seq` in place of
  `event:seq`: two frames between which two bordering countries changed, which is the net of one or
  more exchanges, never known to be one. It is checked like an event (every field once, valid
  values, two frames the record holds) and counted apart, as a descriptive measurement. It is never
  an event: no floor counts it and every claim rule refuses its input when one is among it
  (`exchanges_only`), whatever the floors. A group with both `event:seq` and `net:seq` is a
  problem.

Per-claim corroboration (R9): `experiments/E020-wine-first-run/outcomes.json`, when committed,
declares one outcome per claim id (`corroborated`, `narrowed`, `unestablished` or `pending`). A
claim may be `corroborated` only when its own rule in `CLAIM_RULES` holds over every committed
sitting: the walkthroughs/f011-questions.md arms for Q-CMB-04/05/06/07/11 (100 exchanges per
attacker size against a defender of 1; 100 per defender size against one attacker size; 500 in
all; 200 with every exchange losing exactly one army on one side; 500 with the attacker's country
known and split by the fixed VIPC list, which `vipc_countries` names), and the batch floors for
batch 2's claims. A claim with no rule is never corroborated. Shortfalls are printed per arm.

Usage: `python3 tools/check_counts.py experiments/E020-wine-first-run/scenarios.txt`.

T44 adds `--accept-single`, `--experiment` and `--records-root`: with `--accept-single` the checker
accepts the `single:rank` kind (a single die read from two close frames, T44) and counts the
observation as an exchange; without it the kind is unknown and the observation is refused, so it is
never counted. `--experiment`/`--records-root` point the checker at another experiment's batch list
and records (default E020/runs/E020), which keeps the E020 behaviour unchanged.
"""
import argparse
import configparser
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECORDS = ROOT / "runs" / "E020"
SCENARIOS = ROOT / "experiments" / "E020-wine-first-run" / "scenarios.txt"
EXPERIMENT = "E020"

# --- the field vocabulary and the value each role may carry (constraint D; R6) ----------------

FIELD = re.compile(r"^[a-z][a-z-]*:[a-z][a-z-]*$")      # Done-when 4's structural kind:role name
INTEGER_KINDS = frozenset({"counter", "hand", "game", "event", "net", "country", "sitting"})
COLOUR_KINDS = frozenset({"owner"})
COLOURS = frozenset({"blue", "green", "red", "yellow"})  # the four seat colours (F019 Q-SET-02: seat 1 blue)
COUNTRIES = 46                                           # F017: the board's countries are numbered 1 to 46
INTEGER = re.compile(r"^(0|[1-9][0-9]{0,9})$")
OUTCOMES = ("corroborated", "narrowed", "unestablished", "pending")
SHA = re.compile(r"^sha256:([0-9a-f]{64})$")


def value_problem(field, value, accept_single=False):
    """Why `value` may not stand under `field`, or "" when it may. A field is a structural
    `kind:role` name; a counter, hand, game, event, country or sitting value is a plain
    non-negative integer as read (a country is the board's country number, 1 to 46, F017; a game
    or an event ordinal starts at 1); an owner is one of the four seat colour words. A `single`
    kind (a single-die marker, T44) is in the vocabulary only with `accept_single`; any
    other kind, and any other value (text from the screen included), is refused."""
    if not isinstance(field, str) or not FIELD.fullmatch(field):
        return f"field {field!r} is not a structural kind:role name"
    kind = field.split(":", 1)[0]
    if not isinstance(value, str):
        return f"{field}: the value is not a string"
    if kind in INTEGER_KINDS or (accept_single and kind == "single"):
        if not INTEGER.fullmatch(value):
            return f"{field}: {value!r} is not a plain non-negative integer"
        number = int(value)
        if kind in ("game", "event", "net") and number < 1:
            return f"{field}: {value!r} is an ordinal, from 1"
        if kind == "country" and not 1 <= number <= COUNTRIES:
            return f"{field}: {value!r} is not a country index from 1 to {COUNTRIES}"
        return ""
    if kind in COLOUR_KINDS:
        if value not in COLOURS:
            return f"{field}: {value!r} is not a colour word ({', '.join(sorted(COLOURS))})"
        return ""
    hint = "; pass --accept-single for a single-die marker" if kind == "single" else ""
    return f"field {field!r}: the kind {kind!r} is not in the vocabulary " \
           f"({', '.join(sorted(INTEGER_KINDS | COLOUR_KINDS))}{hint})"


# --- the batch list -----------------------------------------------------------------------------

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


def event_fields(batch):
    """The fields every event of the batch carries, besides game:ordinal and event:seq."""
    return batch.get("event_fields", "").split()


def vocabulary(batch):
    """Every field a record of the batch may carry."""
    return ["sitting:epoch", "game:ordinal", "event:seq", NET_SEQ] + event_fields(batch)


NET_SEQ = "net:seq"       # the ordinal of a net observation, which is never an event (R1)


# --- records and events -------------------------------------------------------------------------

def records_of(batch, records_root=RECORDS):
    """[(path, parsed document)] of the files under runs/E020/<batch>/, sorted by name."""
    folder = Path(records_root) / batch
    if not folder.is_dir():
        return []
    out = []
    for path in sorted(folder.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            doc = exc
        out.append((path, doc))
    return out


def observations_of(doc, name, batch, experiment=EXPERIMENT, accept_single=False):
    """({identity: values} of events, {identity: values} of net observations, problems) for one
    record: its complete events and its complete net observations, each once. A net observation is
    never among the events (R1)."""
    problems = []
    if not isinstance(doc, dict) or doc.get("schema") != "run/1":
        return {}, {}, ["not a run/1 document"]
    if doc.get("experiment") != experiment or doc.get("arm") != name:
        problems.append(f"experiment {doc.get('experiment')!r} arm {doc.get('arm')!r} is not "
                        f"{experiment} {name!r}")
    held = {o.get("sha256") for o in doc.get("outputs", []) if isinstance(o, dict)}
    allowed = set(vocabulary(batch))
    sittings = []
    groups = defaultdict(list)
    for i, obs in enumerate(doc.get("observations", [])):
        if not isinstance(obs, dict):
            problems.append(f"observations[{i}] is not an object")
            continue
        if "field" in obs:
            if obs["field"] not in allowed:
                problems.append(f"observations[{i}]: field {obs['field']!r} is not in the batch vocabulary")
                continue
            problem = value_problem(obs["field"], obs.get("value"), accept_single)
            if problem:
                problems.append(f"observations[{i}]: {problem}")
                continue
        if obs.get("field") == "sitting:epoch":
            sittings.append(obs.get("value"))
            continue
        step = obs.get("step")
        if not isinstance(step, int) or step < 1:
            problems.append(f"observations[{i}]: an event observation needs a step from 1")
            continue
        groups[step].append(obs)
    if len(sittings) != 1:
        problems.append(f"{len(sittings)} sitting:epoch observations; a record names exactly one sitting")
        return {}, {}, problems
    sitting = sittings[0]
    events, nets = {}, {}
    for step, group in sorted(groups.items()):
        fields = Counter(o["field"] for o in group if "field" in o)
        if fields["event:seq"] and fields[NET_SEQ]:
            problems.append(f"step {step}: carries both event:seq and {NET_SEQ}; an exchange or a net, never both")
            continue
        net = bool(fields[NET_SEQ])
        seq_field = NET_SEQ if net else "event:seq"
        kind = "net observation" if net else "event"
        need = ["game:ordinal", seq_field] + event_fields(batch)
        refs = [o.get("ref", "") for o in group if "ref" in o]
        missing = [f for f in need if fields[f] == 0]
        doubled = sorted(f for f, n in fields.items() if n > 1)
        if missing or doubled:
            problems.append(f"step {step}: not one complete {kind} (missing {missing or 'none'}, "
                            f"repeated {doubled or 'none'})")
            continue
        shas = [m.group(1) for r in refs if (m := SHA.fullmatch(r))]
        if len(shas) < 2 or len(set(shas)) < 2 or any(s not in held for s in shas) or len(shas) != len(refs):
            problems.append(f"step {step}: an event cites at least two distinct frames the record's outputs hold")
            continue
        values = {o["field"]: o["value"] for o in group if "field" in o}
        key = (sitting, int(values["game:ordinal"]), int(values[seq_field]))
        into = nets if net else events
        if key in into:
            problems.append(f"step {step}: {kind} {key} appears twice in one record")
            continue
        into[key] = values
    return events, nets, problems


def events_of(doc, name, batch, experiment=EXPERIMENT, accept_single=False):
    """({identity: values}, problems) for one record: its complete events, each once (never its
    net observations)."""
    events, _nets, problems = observations_of(doc, name, batch, experiment, accept_single)
    return events, problems


def batch_observations(name, batch, records_root=RECORDS, experiment=EXPERIMENT, accept_single=False):
    """({identity: values} of events, {identity: values} of net observations, problems) over every
    record of the batch, each counted once."""
    merged = {"event": {}, "net observation": {}}
    problems = []
    for path, doc in records_of(name, records_root):
        if isinstance(doc, Exception):
            problems.append(f"{path.name}: not JSON ({doc})")
            continue
        events, nets, record_problems = observations_of(doc, name, batch, experiment, accept_single)
        problems += [f"{path.name}: {p}" for p in record_problems]
        for kind, found in (("event", events), ("net observation", nets)):
            for key, values in found.items():
                if key in merged[kind] and merged[kind][key] != values:
                    problems.append(f"{path.name}: {kind} {key} disagrees with an earlier record of the same "
                                    "sitting; a re-read that changes a reading names the record it supersedes "
                                    "in the finding, and the counts stop until it is resolved")
                    continue
                merged[kind][key] = values
    return merged["event"], merged["net observation"], problems


def batch_events(name, batch, records_root=RECORDS, experiment=EXPERIMENT, accept_single=False):
    """({identity: values}, problems) over every record of the batch, each event counted once
    (net observations are never among them)."""
    events, _nets, problems = batch_observations(name, batch, records_root, experiment, accept_single)
    return events, problems


# --- per-claim rules (R9) ------------------------------------------------------------------------

def _ints(events, *fields):
    return [tuple(int(v[f]) for f in fields) for v in events.values()]


def _arms(rows, target, label):
    lines, ok = [], True
    for arm, have in rows:
        lines.append(f"    {label} {arm}: {have} of {target}" + ("" if have >= target else f" (short {target - have})"))
        ok = ok and have >= target
    return ok, lines


def rule_cmb_04(events, batch):
    pairs = Counter(_ints(events, "counter:attacker-before", "counter:defender-before"))
    return _arms([(a, pairs[(a, 1)]) for a in (2, 3, 4, 5, 10)], 100, "attacker size vs defender 1:")


def rule_cmb_05(events, batch):
    """100+ exchanges per defender size in {1, 2, 3, 4, 10}, all against one fixed attacker size
    (walkthroughs/f011-questions.md). Every arm is counted for the same attacker size; the size
    reported is the one whose weakest arm is largest (T38 round 3, R2: never one size per arm)."""
    pairs = Counter(_ints(events, "counter:attacker-before", "counter:defender-before"))
    defenders = (1, 2, 3, 4, 10)
    attackers = sorted({a for a, _ in pairs})
    if not attackers:
        return _arms([(d, 0) for d in defenders], 100, "defender size (no attacker size observed):")
    fixed = max(attackers, key=lambda a: (min(pairs[(a, d)] for d in defenders),
                                          sum(pairs[(a, d)] for d in defenders), -a))
    return _arms([(d, pairs[(fixed, d)]) for d in defenders], 100, f"defender size (attacker size {fixed} fixed):")


def rule_cmb_06(events, batch):
    return _arms([("all", len(events))], 500, "exchanges")


def rule_cmb_07(events, batch):
    deltas = Counter()
    for a0, a1, d0, d1 in _ints(events, "counter:attacker-before", "counter:attacker-after",
                                "counter:defender-before", "counter:defender-after"):
        deltas[(a1 - a0, d1 - d0)] += 1
    other = sum(n for delta, n in deltas.items() if delta not in ((-1, 0), (0, -1)))
    ok, lines = _arms([("all", len(events))], 200, "exchanges")
    lines.append(f"    exchanges with another outcome than one army lost on one side: {other}")
    return ok and other == 0, lines


def rule_cmb_11(events, batch):
    vipc = {int(v) for v in batch.get("vipc_countries", "").split() if v.isdigit()}
    inside = sum(1 for (a,) in _ints(events, "country:attacker") if a in vipc)
    ok, lines = _arms([("all", len(events))], 500, "exchanges")
    lines.append(f"    VIPC list: {len(vipc)} countries named; attacker inside {inside}, outside {len(events) - inside}")
    if not vipc:
        lines.append("    the VIPC list is not named in scenarios.txt (vipc_countries): no split, no corroboration")
    return ok and bool(vipc) and 0 < inside < len(events), lines


def rule_batch_floor(events, batch):
    games = {(s, g) for s, g, _ in events}
    ok_e, lines = _arms([("all", len(events))], int(batch["events_min"]), "bomb plays")
    ok_g, more = _arms([("all", len(games))], int(batch["games_min"]), "games")
    return ok_e and ok_g, lines + more


def exchanges_only(rule):
    """The claim rule, refusing any input that holds a net observation (R1). Every claim of the
    batch list is about single events (one exchange, one bomb play): a net of several exchanges can
    never stand for one, so a rule given a value set with `net:seq`, or without `event:seq`, is not
    met, whatever its floors. Q-CMB-06's loss share is counted per exchange like the rest; nets are
    not summed into it (a net hides the exchanges inside it, and the captures are never nets)."""
    def guarded(events, batch):
        foreign = sum(1 for v in events.values() if NET_SEQ in v or "event:seq" not in v)
        met, lines = rule(events, batch)
        if foreign:
            return False, lines + [f"    {foreign} net observation(s) among the events: refused, a net is never "
                                   "an exchange or a play"]
        return met, lines
    guarded.__name__ = rule.__name__
    guarded.__doc__ = rule.__doc__
    return guarded


CLAIM_RULES = {claim: exchanges_only(rule) for claim, rule in {
    "Q-CMB-04": rule_cmb_04, "Q-CMB-05": rule_cmb_05, "Q-CMB-06": rule_cmb_06,
    "Q-CMB-07": rule_cmb_07, "Q-CMB-11": rule_cmb_11,
    "C-CRD-06": rule_batch_floor, "Q-BON-08": rule_batch_floor,
}.items()}


def declared_outcomes(scenarios):
    """({claim id: {outcome, note}}, problems) from outcomes.json beside the scenarios file."""
    path = Path(scenarios).with_name("outcomes.json")
    if not path.is_file():
        return {}, []
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {}, [f"{path.name}: not JSON ({exc})"]
    claims = doc.get("claims") if isinstance(doc, dict) else None
    if not isinstance(claims, dict):
        return {}, [f"{path.name}: no claims object"]
    problems = []
    for claim, entry in claims.items():
        if not isinstance(entry, dict) or entry.get("outcome") not in OUTCOMES:
            problems.append(f"{path.name}: {claim}: the outcome is one of {', '.join(OUTCOMES)}")
    return claims, problems


# --- the check ----------------------------------------------------------------------------------

def check_batch(name, batch, outcomes=None, records_root=RECORDS, experiment=EXPERIMENT, accept_single=False):
    """(problems, lines) for one batch."""
    outcomes = outcomes or {}
    events, nets, problems = batch_observations(name, batch, records_root, experiment, accept_single)
    noun = "exchanges" if batch.get("event") == "exchange" else f"{batch.get('event', 'event')} plays"
    games = {(s, g) for s, g, _ in events}
    floor, games_floor = int(batch.get("events_min", 0)), int(batch.get("games_min", 0))
    lines = [f"batch {name}: {batch.get('questions', '')}",
             f"  {noun} (complete, uniquely identified): target >= {floor}, observed {len(events)}",
             f"  games (distinct sitting and game): target >= {games_floor}, observed {len(games)}",
             f"  net observations (two frames' net of one or more {noun}; descriptive, never counted "
             f"as {noun}): {len(nets)}"]
    if not batch.get("event") or not event_fields(batch):
        problems.append(f"{name}: the batch names no event and no event fields")
    if len(events) < floor:
        problems.append(f"{name}: {len(events)} {noun}, short of the floor of {floor} by {floor - len(events)}")
    if len(games) < games_floor:
        problems.append(f"{name}: {len(games)} game(s), short of the floor of {games_floor}")
    for claim in batch.get("claims", "").split():
        declared = (outcomes.get(claim) or {}).get("outcome", "none declared")
        rule = CLAIM_RULES.get(claim)
        if rule is None:
            met, arm_lines = False, ["    no per-arm rule: never corroborated"]
        else:
            met, arm_lines = rule(events, batch)
        lines.append(f"  {claim}: declared {declared}; per-arm target {'met' if met else 'not met'}")
        lines += arm_lines
        if declared == "corroborated" and not met:
            problems.append(f"{name}: {claim} is declared corroborated, but its per-arm target is not met")
    return problems, lines


def check(scenarios=SCENARIOS, records_root=None, experiment=EXPERIMENT, accept_single=False):
    """(problems, lines) for every batch of the scenarios file. `records_root` defaults to
    `runs/<experiment>`."""
    scenarios = Path(scenarios)
    records_root = Path(records_root) if records_root else ROOT / "runs" / experiment
    batches = load_batches(scenarios)
    if not batches:
        return [f"{scenarios}: no [batch ...] block found"], []
    outcomes, problems = declared_outcomes(scenarios)
    known = {c for b in batches.values() for c in b.get("claims", "").split()}
    problems += [f"outcomes.json names {c}, which no batch carries" for c in outcomes if c not in known]
    lines = []
    for name, batch in batches.items():
        batch_problems, batch_lines = check_batch(name, batch, outcomes, records_root, experiment, accept_single)
        problems += batch_problems
        lines += batch_lines
    return problems, lines


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check an experiment's sitting counts against its batch list.")
    parser.add_argument("scenarios", nargs="?", default=str(SCENARIOS),
                        help="the batch list (default: E020's scenarios.txt)")
    parser.add_argument("--experiment", default=EXPERIMENT,
                        help="the experiment id the batch list belongs to (default: E020)")
    parser.add_argument("--records-root", default=None,
                        help="the records root (default: runs/<experiment>)")
    parser.add_argument("--accept-single", action="store_true",
                        help="accept the single:rank marker (a single die, T44) and count the observation "
                             "as an exchange; without it the marker is refused, so it is never counted")
    args = parser.parse_args(sys.argv[1:] if argv is None else list(argv))
    problems, lines = check(Path(args.scenarios), args.records_root, args.experiment, args.accept_single)
    print("\n".join(lines))
    for problem in problems:
        print(f"FAIL {problem}")
    if problems:
        return 1
    print("counts ok: every batch meets its floor, and no claim is corroborated below its arms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
