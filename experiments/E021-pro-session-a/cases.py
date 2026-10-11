"""T45's Session A case table and its pure case picker (walkthroughs/video-walkthrough.md,
"Session A — deliberate cases"; the owner's choices of 2026-10-07, carried in the T45 task file).

The 40 cells the sitting works through, one claim each (the task file's table):

  even     16   attacker N in {2, 4, 8, 12} vs a defender of N-1, N, N+1, N+2   Q-CMB-01
  underdog  4   attacker 4, 8, 12, 20 vs a strictly stronger defender            Q-CMB-02
  tiny      3   attacker 1, 2, 3 vs a defender of 1                              Q-CMB-03
  quit      2   the quit-attack button mid-battle                                Q-CMB-08
  lost      5   attacks that fail; what happens to the turn                      Q-CMB-09
  busy     10   turns with 3 or more attacks; what ends each                     Q-CMB-10

A board is the shape the reader gives (`boardreader.read_board`): {country: {"army": int|None,
"owner": colour word|None}} for countries 1 to 46 (F017). Everything here is a pure function of
such a board, the adjacency (E015's committed tabulation, via `exchange_events.load_adjacency`)
and the cells still needed: no pixels, no clicks, no game.

What an attack pair must satisfy before any case is considered (`paired`): the attacker belongs to
the seat that plays (the driver plays blue, F019 Q-SET-02), the defender is another seat's country
that borders it. Size cases probe both sides of the expected equality gate (F011 Q-CMB-02,
about 90%); that gate must not filter out a boundary probe. An
attacker of 1 may still be refused by the game (the task file): the refusal is the observation, so
the picker never filters it out.

Size cases (`even`, `underdog`, `tiny`) are picked only when the board already shows the case's
attacker size: the reinforcements of one turn cannot be counted on before they are placed (ALL
places every one of them), so the loop grows a stack first (`frontier`, which never grows a
country that already shows a needed size) and picks the attack after the placement.
`quit`, `lost` and `busy` are outcome cells: any pair past the gate can attempt them; which cell
an attempt meets is the loop's to say, from what the game did.
"""
CASES = ("even", "underdog", "tiny", "quit", "lost", "busy")
TOTALS = {"even": 16, "underdog": 4, "tiny": 3, "quit": 2, "lost": 5, "busy": 10}
TOTAL = 40                              # the cells of the task file's table, 16+4+3+2+5+10

EVEN_SIZES = (2, 4, 8, 12)
EVEN_OFFSETS = (-1, 0, 1, 2)            # the defender holds N-1, N, N+1 or N+2
UNDERDOG_SIZES = (4, 8, 12, 20)
TINY_SIZES = (1, 2, 3)

SIZE_CASES = ("even", "underdog", "tiny")
GROW_CASES = ("even", "underdog")       # the size rows whose attacker sizes (4 to 20) a stack is grown
                                        # towards when no cell is reachable now (fix #178)
OUTCOME_CASES = ("quit", "lost", "busy")
HUMAN_SEAT = "blue"                     # the driver's seat (F019 Q-SET-02; exchange_events.HUMAN_SEAT)
COUNTRIES = 46


def cells(case):
    """The 1-based cell numbers of `case`, in order."""
    if case not in TOTALS:
        raise KeyError(f"no case {case!r}; the table holds {CASES}")
    return tuple(range(1, TOTALS[case] + 1))


def needed_cells(met):
    """The (case, cell) pairs not yet met, in table order. `met` is any iterable of such pairs."""
    met = set(met)
    return [(case, cell) for case in CASES for cell in cells(case) if (case, cell) not in met]


def spec(case, cell):
    """What the pair must show for this cell: {"size": N, "defender": (lo, hi)} for a size case
    (the attacker holds exactly N armies, the defender lo to hi inclusive; `hi` None is unbounded),
    {} for an outcome cell (any legal pair). KeyError on a cell outside the table."""
    if case not in TOTALS or not 1 <= cell <= TOTALS[case]:
        raise KeyError(f"no cell {cell} of case {case!r}")
    if case == "even":
        size = EVEN_SIZES[(cell - 1) // len(EVEN_OFFSETS)]
        offset = EVEN_OFFSETS[(cell - 1) % len(EVEN_OFFSETS)]
        return {"size": size, "defender": (size + offset, size + offset)}
    if case == "underdog":
        size = UNDERDOG_SIZES[cell - 1]
        return {"size": size, "defender": (size + 1, None)}    # strictly stronger than the attacker
    if case == "tiny":
        size = TINY_SIZES[cell - 1]
        return {"size": size, "defender": (1, 1)}
    return {}


def readable(board, country):
    """The country's reading when the board has one with an army and an owner, else None."""
    row = board.get(country)
    if not isinstance(row, dict) or row.get("army") is None or row.get("owner") is None:
        return None
    return row


def paired(board, attacker, defender, adjacency, seat=HUMAN_SEAT, points=None):
    """True when (attacker, defender) is a pair the driver may name: a readable country of `seat`,
    a readable country of another seat that borders it, and -- when `points` is given -- both
    countries among the ones with a proven click point (walkthroughs/coordinates.md; countries 11
    and 15 have none, #120, and are never clicked). Nothing about the counts: the size rows are
    exactly the probes of the count gate below."""
    if points is not None and (attacker not in points or defender not in points):
        return False
    if defender == attacker or defender not in adjacency.get(attacker, ()):
        return False
    a, d = readable(board, attacker), readable(board, defender)
    if a is None or d is None or a["owner"] != seat or d["owner"] == seat:
        return False
    return True


def gate(board, attacker, defender):
    """The human's attack gate (F011 Q-CMB-02, about 90%): the attacker holds at least as many
    armies as the defender. The running game's answer to a pair past this gate is what the even
    (N vs N+1, N+2) and underdog cells record; the picker never filters those out."""
    return readable(board, attacker)["army"] >= readable(board, defender)["army"]


def legal(board, attacker, defender, adjacency, seat=HUMAN_SEAT, points=None):
    """True when (attacker, defender) is an attack the game is expected to fight: a pair, past the
    gate. The outcome rows (`quit`, `lost`, `busy`) take only such pairs."""
    return paired(board, attacker, defender, adjacency, seat=seat, points=points) \
        and gate(board, attacker, defender)


def defender_fits(board, case, cell, defender):
    """True when the defender's count fits the cell's range on this board."""
    row = readable(board, defender)
    if row is None:
        return False
    lo, hi = spec(case, cell)["defender"]
    return row["army"] >= lo and (hi is None or row["army"] <= hi)


def fits(board, case, cell, attacker, defender, adjacency, seat=HUMAN_SEAT, points=None):
    """True when (attacker, defender) attempts this cell. A size case asks the pair and the
    counts only -- the cells past the gate (even N vs N+1 or N+2, every underdog) are the probes
    of it, and the game's refusal is their observation; an outcome case asks a pair the game is
    expected to fight (`legal`)."""
    if not paired(board, attacker, defender, adjacency, seat=seat, points=points):
        return False
    wanted = spec(case, cell)
    if not wanted:
        return gate(board, attacker, defender)
    if readable(board, attacker)["army"] != wanted["size"]:
        return False
    return defender_fits(board, case, cell, defender)


def pairs(board, adjacency, seat=HUMAN_SEAT, points=None):
    """Every legal (attacker, defender) of the board, in country order."""
    out = []
    for attacker in sorted(board):
        for defender in sorted(adjacency.get(attacker, ())):
            if legal(board, attacker, defender, adjacency, seat=seat, points=points):
                out.append((attacker, defender))
    return out


def pick(board, needed, adjacency, seat=HUMAN_SEAT, points=None, exclude=()):
    """(case, cell, attacker, defender) for the first needed cell the board can attempt, in table
    order (the size rows first, then the outcome rows), or None when no needed cell fits.

    A size case is picked only where the board already shows its attacker size, and its first pair
    is the lowest country numbers, so the choice is a function of the board and never of a random
    draw. An outcome case takes any pair past the gate, ranked by the margin (attacker minus
    defender): the `lost` row takes the smallest margin first (the attack most likely to fail,
    F011's model: at equal armies about 4 in 5), the `quit` and `busy` rows the largest first (the
    attack most likely to keep the turn going); ties take the lowest country numbers. `exclude` is
    the (attacker, defender) pairs the caller already tried this turn: they are never returned."""
    wanted = set(needed)
    tried = set(map(tuple, exclude))
    candidates = [(attacker, defender) for attacker in sorted(board)
                  for defender in sorted(adjacency.get(attacker, ()))
                  if (attacker, defender) not in tried]
    for case in CASES:
        for cell in cells(case):
            if (case, cell) not in wanted:
                continue
            fitting = [(a, d) for a, d in candidates
                       if fits(board, case, cell, a, d, adjacency, seat=seat, points=points)]
            if not fitting:
                continue
            if case in OUTCOME_CASES:
                sign = 1 if case == "lost" else -1
                fitting.sort(key=lambda pair: (sign * (board[pair[0]]["army"] - board[pair[1]]["army"]),
                                               pair))
            attacker, defender = fitting[0]
            return case, cell, attacker, defender
    return None


def reachable(board, needed, adjacency, seat=HUMAN_SEAT, points=None):
    """{(attacker, defender): [(case, cell, gap), ...]}: the needed size cells each pair would
    attempt if the attacker were grown to the cell's size (the defender's count already fits, and
    will not change before this turn's attack: the game waits for the human). Pairs past the gate
    count here too -- growing towards a boundary cell is exactly what the even and underdog rows
    are for. The map is what `frontier` chooses among; empty when no needed size cell is
    reachable from any pair."""
    wanted = set(needed)
    out = {}
    for attacker in sorted(board):
        mine = readable(board, attacker)
        if mine is None or mine["owner"] != seat:
            continue
        for defender in sorted(adjacency.get(attacker, ())):
            if not paired(board, attacker, defender, adjacency, seat=seat, points=points):
                continue
            hit = []
            for case in SIZE_CASES:
                for cell in cells(case):
                    if (case, cell) not in wanted:
                        continue
                    size = spec(case, cell)["size"]
                    if size >= mine["army"] and defender_fits(board, case, cell, defender):
                        hit.append((case, cell, size - mine["army"]))
            if hit:
                out[(attacker, defender)] = hit
    return out


def frontier(board, needed, adjacency, seat=HUMAN_SEAT, points=None, avoid=()):
    """(attacker, defender, case, cell, gap) for the country this turn should grow, or None when
    the board has no country of `seat` with an adjacent enemy to click.

    The choice is the reachable pair (against `reachable`) whose cell size is the smallest number
    of reinforcements away (gap = size - the attacker's armies, never negative), so one turn's
    `ALL` placement moves the stack towards a cell that is still needed; ties take the pair whose
    attacker holds most, then the lowest country numbers. When no needed size cell is reachable,
    the strongest country of the seat with an adjacent enemy is grown anyway, and it now names a
    target (fix #178; sitting 20261011T163105Z, 26 of 40 met, where the open size rows needed stacks
    of 8, 12 or 20 that an early board lacks, so every `place-target` read case None, gap 0 and no
    game counted as growing): the smallest attacker size still needed by an unmet `even` or
    `underdog` cell (`GROW_CASES`) that is above the country's armies, with that cell's case and
    cell, and gap = that size minus the country's armies. The defender is not asked to fit (none
    does, or the pair would have been reachable). When no open size cell is above the country's
    armies, the answer is as before: case and cell None, gap 0, since the outcome rows take any
    legal pair and a bigger stack is never a waste.

    `avoid` is the countries whose count should not change this turn: an attacker that already
    shows a needed size (the placement would overshoot it, since ALL places every reinforcement).
    They are grown only when the seat has no other country with an adjacent enemy to click."""
    avoid = set(avoid)
    options = reachable(board, needed, adjacency, seat=seat, points=points)
    ranked = []
    for (attacker, defender), hit in options.items():
        if attacker in avoid:
            continue
        for case, cell, gap in hit:
            if gap == 0:
                continue                 # already the size: growing it would only overshoot
            ranked.append((gap, -readable(board, attacker)["army"], attacker, defender, case, cell))
    if ranked:
        best = min(ranked)
        return best[2], best[3], best[4], best[5], best[0]
    strongest = []
    for attacker in sorted(board):
        mine = readable(board, attacker)
        if mine is None or mine["owner"] != seat:
            continue
        if points is not None and attacker not in points:
            continue
        for defender in sorted(adjacency.get(attacker, ())):
            if points is not None and defender not in points:
                continue
            row = readable(board, defender)
            if row is not None and row["owner"] != seat:
                strongest.append((-mine["army"], attacker, defender))
    if not strongest:
        return None
    preferred = [row for row in strongest if row[1] not in avoid] or strongest
    _, attacker, defender = min(preferred)
    target = grow_target(board, needed, attacker)
    if target is None:
        return attacker, defender, None, None, 0
    return (attacker, defender) + target


def rest_choices(board, needed, adjacency, target, seat=HUMAN_SEAT, points=None):
    """The countries of `seat` that may take the rest of the pool after an exact placement (fix #180),
    best first. The pool ends only at exactly zero (F013 Q-REI-03), so what the exact stack did not
    take must go somewhere; the rule keeps it from spoiling a size the sitting still needs:

    * never `target`, the stack just sized, and never a country without a click point or a reading;
    * never a needed attacker showing its size (an attacker of a pair that fits an unmet size cell
      with gap 0 now: more armies would overshoot its cell). They are excluded, not ranked last
      (round 2): the list may be empty, and then the caller does not place exactly at all;
    * first the interior countries (every neighbour readable and the seat's own: never an attacker),
      then the frontier countries; within a tier the lowest country number, so the choice is a
      function of the board."""
    shown = {attacker for (attacker, _defender), hit in
             reachable(board, needed, adjacency, seat=seat, points=points).items()
             if any(gap == 0 for _case, _cell, gap in hit)}
    ranked = []
    for country in sorted(board):
        row = readable(board, country)
        if country == target or country in shown or row is None or row["owner"] != seat:
            continue
        if points is not None and country not in points:
            continue
        neighbours = [readable(board, n) for n in adjacency.get(country, ())]
        interior = all(n is not None and n["owner"] == seat for n in neighbours)
        ranked.append((0 if interior else 1, country))
    return [country for _tier, country in sorted(ranked)]


def grow_target(board, needed, country):
    """(case, cell, gap) for the smallest attacker size above `country`'s armies that an unmet
    `even` or `underdog` cell in `needed` still asks for (ties: the case order, then the lowest
    cell), or None when no such size is open. A pure function of the board and the cells."""
    wanted = set(needed)
    armies = readable(board, country)["army"]
    best = None
    for case in GROW_CASES:
        for cell in cells(case):
            if (case, cell) not in wanted:
                continue
            size = spec(case, cell)["size"]
            if size > armies and (best is None or size < best[0]):
                best = (size, case, cell)
    if best is None:
        return None
    return best[1], best[2], best[0] - armies


def next_outcome_cell(needed, case):
    """The lowest unmet cell of the outcome row `case`, or None when the row is complete."""
    wanted = [cell for c, cell in needed if c == case]
    return min(wanted) if wanted else None
