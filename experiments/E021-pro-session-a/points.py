"""The 44 proven country click points of the driver's seat (walkthroughs/coordinates.md, "The 46
country positions"; the E002 tour's measured points, experiments/E002-iwp-state-inventory/scripts/
tour.steps).

The file lists the points in the board's country order and the tour used them as the placement
`click-until` candidates and as `attack-picked` targets (E020's play.steps carries the same 44 in
its `place` block). Countries 11 and 15 have no point there (#120: they were never measured on the
tour, and anchors.json holds their numeral centres from the sittings' frames instead), so the
driver never clicks those two: they can be read on the board, but never chosen as an attacker or
named as a target.

`points` is {country: (x, y)} for the 44 clickable countries; `COUNTRY_ORDER` is the mapping from
the list's position (1-based) to the country number it belongs to. tools/tests/test_e021_points.py
pins both against the committed list in coordinates.md and against E020's `place` block, so a
change on either side is a failing test rather than a silent drift.
"""
COUNTRY_ORDER = tuple(list(range(1, 11)) + [12, 13, 14] + list(range(16, 47)))   # 44 countries

LIST = ((55, 193), (49, 261), (42, 330), (105, 441), (142, 385), (153, 433), (188, 399), (235, 441),
        (239, 282), (178, 283), (132, 238), (139, 166), (277, 177), (358, 60), (344, 110), (307, 160),
        (390, 163), (393, 98), (473, 139), (440, 190), (509, 223), (566, 143), (525, 89), (593, 86),
        (682, 99), (760, 129), (685, 153), (746, 196), (668, 211), (748, 264), (655, 282), (750, 411),
        (698, 436), (639, 446), (515, 404), (521, 343), (454, 363), (448, 444), (372, 453), (377, 410),
        (308, 425), (333, 305), (412, 294), (321, 262))

NO_POINT = (11, 15)                 # #120: no proven click point on the tour

POINTS = {country: point for country, point in zip(COUNTRY_ORDER, LIST)}


def click_points():
    """{country: (x, y)} of the clickable countries, in country order."""
    return dict(POINTS)


def as_steps_list():
    """The list as the E002 step language's `X Y X Y ...` tail (the placement `click-until`)."""
    return " ".join(f"{x} {y}" for x, y in LIST)
