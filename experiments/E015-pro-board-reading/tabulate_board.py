#!/usr/bin/env python3
"""T32: tabulate the board tables of Isle Wars Pro from the decompiled start handler, in place, and check
the table properties F017 claims (rule 20: the output is the checked measurement the finding cites).

  IWA_STATIC=<folder> python3 experiments/E015-pro-board-reading/tabulate_board.py [--run r1] [--out r1]

Reads the decompiled text of `MovieScript 1 - Startmovie` IN PLACE in the static folder (never copied),
parses the board tables it builds (the per-country island numbers, the nine island member lists, the
per-island key-country lists, the 23-country key list, the five border tables and the two position
tables), and writes measurements/board-tabulation-<out>.json (default <out> = <run>; an existing file is
never overwritten). The output holds derived, tabulated data only: all 27 board tables as plain
number lists (the per-country island numbers, the member lists, the zero-padded per-island key lists,
the 23-country key list, the five border tables and the two coordinate tables), plus counts, member
lists with their zero padding dropped, adjacency in both directions, degrees, the island crossing
graph, and one boolean per check — never a line of the decompiled text and never a machine path.

Checks (a property a script checks is checked, not read):
  table lengths (46 entries each; entries in range); no self-neighbour (with the detector itself
  exercised against an injected self-edge, so a self-edge cannot pass unnoticed); no duplicate
  neighbour within a country; symmetry (every border entry listed on both sides); connectivity of the
  whole board from one country; the nine member lists forming a disjoint cover; the per-country island
  numbers agreeing with the member lists; the per-island key lists (zero-padded) concatenating to the
  23-country key list in order; every key country inside its own island; 46 distinct positions.
Exit 0 when every check holds.
"""
import json
import re
import sys
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INVENTORY = ROOT / "experiments" / "E008-static-triage" / "measurements" / "iwp-extract-pro-r1.json"
MOVIE_DIR = ("movie-01-out", "movie-01.abs", "casts", "Internal")
SOURCE = ("MovieScript", 1, "Startmovie")
N_COUNTRIES = 46
TABLE_RE = re.compile(r"^\s*(IslandNum|ISLAND[1-9]|IC[1-9]|VIPC|BR[1-5]|ARRX|ARRY) = \[([0-9, ]*)\]\s*$")
BOARD_TABLES = (["IslandNum", "VIPC", "ARRX", "ARRY"] + ["ISLAND%d" % i for i in range(1, 10)]
                + ["IC%d" % i for i in range(1, 10)] + ["BR%d" % k for k in range(1, 6)])
# the bytecode listing: a `setglobal` line names the global and renders the value it is given; the
# push instructions since the previous `setglobal` line carry that value's entries, in order
LASM_SETGLOBAL = re.compile(r"setglobal \d+ \.+ (\S+) = \[")
LASM_PUSH = re.compile(r"push(?:int\d+|zero)\b.*<(-?\d+)>\s*$")


def parse_tables(text):
    """The named number lists the start handler builds, in order of appearance; the first assignment wins."""
    tables = {}
    for line in text.splitlines():
        m = TABLE_RE.match(line)
        if not m:
            continue
        name = m.group(1)
        if name in tables:
            continue
        tables[name] = [int(x) for x in m.group(2).replace(" ", "").split(",") if x != ""]
    return tables


def bytecode_tables(lasm_text):
    """The same tables as the bytecode listing carries them: the push arguments since the previous
    setglobal line are the entries of the list the next setglobal stores, in order. Globals assigned a
    non-list value (a bare number or a constant) are skipped, and their pushes do not leak into the
    next table."""
    tables = {}
    pending = []
    for line in lasm_text.splitlines():
        if "setglobal" in line:
            m = LASM_SETGLOBAL.search(line)
            if m and pending and m.group(1) not in tables:
                tables[m.group(1)] = pending
            pending = []
            continue
        p = LASM_PUSH.search(line)
        if p:
            pending.append(int(p.group(1)))
    return tables


def file_name(kind, number, name):
    return "%s %d - %s.ls" % (kind, number, name)


def has_self_neighbour(adj):
    """True when any country lists itself among its neighbours. The keys of `adj` are country numbers
    as text; the neighbours are integers, so the key must be converted before the membership test."""
    return any(int(c) in ns for c, ns in adj.items())


def main():
    errors = []
    sys.path.insert(0, str(ROOT / "tools" / "static"))
    import static_common as sc  # noqa: E402

    run = sys.argv[sys.argv.index("--run") + 1] if "--run" in sys.argv else "r1"
    root = sc.static_root()
    folder = root.joinpath("iwp-extract-pro-" + run, *MOVIE_DIR)
    path = folder / file_name(SOURCE[0], SOURCE[1], SOURCE[2])
    text = path.read_text()
    digest, size = sc.sha256_path(path)

    inv = json.loads(INVENTORY.read_text())
    scripts = {(s["kind"], s["number"]): s for s in inv["movies"][0]["scripts"]}
    record = scripts[(SOURCE[0], SOURCE[1])]
    source_match = digest == record["ls_sha256"]
    if not source_match:
        errors.append("the start handler on disk does not match the record's ls_sha256")

    t = parse_tables(text)
    for name in BOARD_TABLES:
        if name not in t:
            errors.append("table %s not found in the decompiled text" % name)
    if errors:
        for e in errors:
            print("FAIL", e)
        return 1

    lasm = (folder / (file_name(SOURCE[0], SOURCE[1], SOURCE[2])[:-3] + ".lasm")).read_text()
    bt = bytecode_tables(lasm)

    checks = {}
    island_num = t["IslandNum"]
    checks["island_number_table_has_46_entries"] = len(island_num) == N_COUNTRIES
    checks["island_numbers_in_1_to_9"] = all(1 <= v <= 9 for v in island_num)
    for k in range(1, 6):
        br = t["BR%d" % k]
        checks["border_table_%d_has_46_entries" % k] = len(br) == N_COUNTRIES
        checks["border_table_%d_entries_in_0_to_46" % k] = all(0 <= v <= N_COUNTRIES for v in br)
    checks["position_tables_have_46_entries_each"] = len(t["ARRX"]) == N_COUNTRIES and len(t["ARRY"]) == N_COUNTRIES

    # Every board table entry confirmed in the bytecode listing: the pushed arguments before the
    # table's store carry the same numbers in the same order.
    missing = [name for name in BOARD_TABLES if name not in bt]
    checks["every_board_table_in_the_bytecode_listing"] = not missing
    checks["bytecode_entries_match_the_text_table_by_table"] = all(
        bt.get(name) == t[name] for name in BOARD_TABLES)

    # Adjacency: country n's neighbours are the non-zero entries of its five border slots, in slot order.
    adjacency = {}
    for c in range(1, N_COUNTRIES + 1):
        adjacency[str(c)] = [t["BR%d" % k][c - 1] for k in range(1, 6) if t["BR%d" % k][c - 1] != 0]
    checks["no_self_neighbour"] = not has_self_neighbour(adjacency)
    # The detector itself is exercised: a synthetic self-edge must be found, so a comparison bug that
    # silently passes every board (a text key against integer neighbours) cannot hide one again.
    checks["self_neighbour_detector_catches_an_injected_self_edge"] = has_self_neighbour({"1": [1, 2]})
    checks["no_duplicate_neighbour_within_a_country"] = all(len(set(ns)) == len(ns) for ns in adjacency.values())
    checks["adjacency_symmetric"] = all(
        sorted(adjacency[str(c)]) == sorted([d for d in range(1, N_COUNTRIES + 1)
                                             if c in adjacency[str(d)]])
        for c in range(1, N_COUNTRIES + 1))
    degrees = {c: len(adjacency[str(c)]) for c in range(1, N_COUNTRIES + 1)}
    checks["every_country_has_2_to_5_neighbours"] = all(2 <= d <= 5 for d in degrees.values())

    seen = {1}
    queue = deque([1])
    while queue:
        c = queue.popleft()
        for d in adjacency[str(c)]:
            if d not in seen:
                seen.add(d)
                queue.append(d)
    checks["board_connected_from_one_country"] = len(seen) == N_COUNTRIES

    islands = [{"island": i, "members": t["ISLAND%d" % i]} for i in range(1, 10)]
    flat = [c for isl in islands for c in isl["members"]]
    checks["island_member_lists_disjoint"] = len(flat) == len(set(flat))
    checks["island_member_lists_cover_all_46"] = sorted(flat) == list(range(1, N_COUNTRIES + 1))
    checks["island_numbers_match_member_lists"] = all(
        island_num[c - 1] == i for i in range(1, 10) for c in islands[i - 1]["members"])
    for isl in islands:
        isl["size"] = len(isl["members"])
        isl["key_countries"] = [v for v in t["IC%d" % isl["island"]] if v != 0]
    checks["key_lists_union_is_the_key_list_in_order"] = (
        [v for isl in islands for v in isl["key_countries"]] == t["VIPC"])
    checks["every_key_country_inside_its_island"] = all(
        v in isl["members"] for isl in islands for v in isl["key_countries"])
    checks["key_list_holds_23_countries"] = len(t["VIPC"]) == 23
    checks["key_list_complement_holds_23_countries"] = N_COUNTRIES - len(set(t["VIPC"])) == 23

    checks["positions_all_distinct"] = len(set(zip(t["ARRX"], t["ARRY"]))) == N_COUNTRIES

    directed = {}
    crossings = []
    for c in range(1, N_COUNTRIES + 1):
        for d in adjacency[str(c)]:
            if island_num[c - 1] != island_num[d - 1]:
                a, b = island_num[c - 1], island_num[d - 1]
                directed.setdefault(a, {})
                directed[a][b] = directed[a].get(b, 0) + 1
                if c < d:
                    crossings.append({"edge": [c, d], "between_islands": [a, b]})
    total_directed = sum(v for row in directed.values() for v in row.values())
    total_edges = sum(degrees.values()) // 2
    checks["crossing_entries_pair_up_both_ways"] = total_directed == 2 * len(crossings)
    checks["degree_sum_even"] = sum(degrees.values()) == 2 * total_edges

    out = {
        "what": "the board tables of Isle Wars Pro, tabulated from the decompiled start handler read in place "
                "(nothing copied; no code and no machine path kept), with the table properties checked",
        "binary_sha256": "c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e",
        "set": "iwp-2.0-996e86c5",
        "run": "pro-" + run,
        "record": "experiments/E008-static-triage/measurements/iwp-extract-pro-r1.json",
        "source_script": {"kind": SOURCE[0], "number": SOURCE[1], "name": SOURCE[2],
                          "file": file_name(SOURCE[0], SOURCE[1], SOURCE[2]), "bytes": size,
                          "sha256_on_disk": digest, "ls_sha256_in_record": record["ls_sha256"],
                          "match": source_match},
        "counts": {"countries": N_COUNTRIES, "islands": len(islands),
                   "island_sizes": [isl["size"] for isl in islands],
                   "key_countries": len(t["VIPC"]),
                   "undirected_edges": total_edges,
                   "directed_border_entries": sum(degrees.values()),
                   "island_crossing_edges": len(crossings),
                   "island_crossing_directed_entries": total_directed,
                   "degree_histogram": {str(d): sum(1 for v in degrees.values() if v == d)
                                        for d in sorted(set(degrees.values()))}},
        "tables": {name: t[name] for name in BOARD_TABLES},
        "islands": islands,
        "island_of_country": island_num,
        "adjacency": adjacency,
        "degrees": {str(c): degrees[c] for c in sorted(degrees)},
        "island_crossing_edges": crossings,
        "island_crossing_directed_entries": {str(a): {str(b): v for b, v in sorted(row.items())}
                                             for a, row in sorted(directed.items())},
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }
    for name, ok in checks.items():
        if not ok:
            errors.append("check failed: %s" % name)

    text_out = json.dumps(out, indent=1) + "\n"
    if sc.leaks(text_out):
        errors.append("the output would hold a machine path; not written")
    else:
        tag = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else run
        dest = HERE / "measurements" / ("board-tabulation-%s.json" % tag)
        if dest.exists():
            print("not overwriting", dest.name)
        else:
            dest.write_text(text_out)
            print("wrote", dest.name)

    print("countries %d, islands %d (sizes %s), edges %d directed %d, crossings %d directed %d"
          % (N_COUNTRIES, len(islands), [isl["size"] for isl in islands], total_edges, sum(degrees.values()),
             len(crossings), total_directed))
    print("bytecode listing: %d of %d board tables found and matched entry by entry"
          % (sum(1 for name in BOARD_TABLES if bt.get(name) == t[name]), len(BOARD_TABLES)))
    print("checks: %d of %d hold" % (sum(checks.values()), len(checks)))
    for e in errors:
        print("FAIL", e)
    if errors:
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
