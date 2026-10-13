"""A single computer-vs-computer exchange from two close board readings (T44).

One die resolves one exchange: exactly one of the attacker's or the defender's counters drops by
one, the other side is unchanged, and no owner changes. So between two frame readings taken close
enough that at most one die resolved, exactly one country's counter reads one lower. The E020 reader
(`experiments/E020-wine-first-run/reader/exchange_events.py`) could only ever call such a pair a
`net`, because at the E020 capture rate (~1.4 s) several dice resolved between frames; T42 made the
watcher fast (8 fps), and this module is the reader half that turns one die into a counted exchange.

The other country of the pair is named by adjacency: the changed country is either the defender (its
owner is another seat; the attacker is the one seat-owned neighbour) or the attacker (its owner is
the seat in turn; the defender is the one neighbour of another seat). When more than one neighbour
fits, the pair is ambiguous and no exchange is claimed — a later task reads the attack panel to name
it. This module is pure: board readings are `{country: {"army": int, "owner": str}}`, adjacency is
`{country: set(country)}`; no pixels, no I/O, no clock.

A single exchange is exported as `event:seq` (never `net:seq`) and carries the `single:rank` marker
that `tools/check_counts.py --accept-single` reads (T44 Done-when 2).
"""

REASONS = ("single", "no-change", "many-changes", "unread", "ownership-change", "counter-rise",
           "not-one-army", "no-attacker", "many-attackers")


def _row(board, country):
    row = board.get(country)
    if not isinstance(row, dict):
        return None
    return (row.get("army"), row.get("owner"))


def single_exchange(before, after, seat, adjacency):
    """(values, reason). `values` is the exchange's field dict when `reason` is "single", else None.

    Fires when exactly one country changed, its owner is unchanged, its army dropped by exactly one,
    and the other country of the pair is the *unique* neighbour of the right side. Every other case
    returns a reason word and no values, so a caller never mistakes a placement, a move, a capture,
    a counter rise or an ambiguous pair for one exchange."""
    if seat not in ("blue", "yellow", "red", "green"):
        return None, "unread"
    changed = [c for c in sorted(set(before) | set(after)) if _row(before, c) != _row(after, c)]
    if not changed:
        return None, "no-change"
    if len(changed) != 1:
        return None, "many-changes"
    country = changed[0]
    was, now = _row(before, country), _row(after, country)
    if was is None or now is None or None in was or None in now:
        return None, "unread"
    if was[1] != now[1]:
        return None, "ownership-change"
    if now[0] > was[0]:
        return None, "counter-rise"
    if now[0] != was[0] - 1:
        return None, "not-one-army"
    if was[1] == seat:
        other = [n for n in adjacency.get(country, ()) if (_row(before, n) or (None, None))[1] != seat
                 and _row(before, n) is not None]
        attacker, defender = country, None
    else:
        other = [n for n in adjacency.get(country, ()) if (_row(before, n) or (None, None))[1] == seat]
        attacker, defender = None, country
    other = [n for n in other if _row(before, n) is not None]
    if not other:
        return None, "no-attacker"
    if len(other) > 1:
        return None, "many-attackers"
    if defender is None:
        defender = other[0]
    else:
        attacker = other[0]
    return {
        "counter:attacker-before": str(_row(before, attacker)[0]),
        "counter:attacker-after": str(_row(after, attacker)[0]),
        "counter:defender-before": str(_row(before, defender)[0]),
        "counter:defender-after": str(_row(after, defender)[0]),
        "country:attacker": str(attacker),
        "country:defender": str(defender),
        "owner:attacker": seat,
        "owner:defender": _row(before, defender)[1],
        "single:rank": "1",
    }, "single"


def observation(values, game, seq, refs):
    """The run/1 observations of one single exchange: `game:ordinal`, `event:seq`, every field once,
    and two frame refs (the pair the exchange was read from). `refs` are `sha256:<hex>` strings."""
    out = [{"step": seq, "source": "screen", "field": "game:ordinal", "value": str(game)},
           {"step": seq, "source": "screen", "field": "event:seq", "value": str(seq)}]
    out += [{"step": seq, "source": "screen", "field": f, "value": values[f]} for f in sorted(values)]
    out += [{"step": seq, "source": "screen", "ref": r} for r in refs]
    return out
