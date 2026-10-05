"""The layout of DOS Isle Wars' ISLEWAR.SAV (T16, F009): decode the bytes the game wrote into a position, and encode a
position back into the same bytes. Pure functions; nothing here reads or writes a file.

The file is text with CRLF line ends and no other control byte. Its lines, in order (F009 says what shows each):

    N                       the number of production centres
    N lines                 the production centres' country numbers
    2 lines                 the DFT pair (the level and the starting armies of the game)
    2 lines                 the two settings (Speed and Sound)
    46 lines                the owner code of countries 1 to 46
    46 lines                the army count of countries 1 to 46
    a , b , c , d           the number of cards held by Blue, Red, Green, Brown
    w,x,y,z                 the cards held, as one digit per card, in the order Blue, Green, Red, Brown

A one-value line is ` v ` (a space on each side), the card-count line is ` a , b , c , d `, and the last line has
no spaces. Every line, the last included, ends in CRLF.

A position is a plain dict (JSON-able), the only thing the writer accepts:
    {"centres": [country numbers], "dft": [d1, d2], "settings": [s1, s2],
     "owners": [46 colour names], "armies": [46 integers],
     "cards": {"blue": [card digits], "red": [...], "green": [...], "brown": [...]}}
"""
import re

FILE_NAME = "ISLEWAR.SAV"
COUNTRIES = 46
COLOURS = ("blue", "red", "green", "brown")
# owner codes (F007 D10; blue by the conquest in three runs, the others by the screen in 12 saves)
OWNER_CODE = {"blue": 9, "red": 4, "green": 2, "brown": 8}
CODE_OWNER = {v: k for k, v in OWNER_CODE.items()}
# order of the colours in the card-count line and in the last line
COUNT_ORDER = ("blue", "red", "green", "brown")
HAND_ORDER = ("blue", "green", "red", "brown")
CARD_DIGITS = range(1, 10)          # a card is one digit (1 to 9) in the last line
MAX_CARDS = 9                       # what a hand line can hold unambiguously is bounded by the encoding only
MAX_ARMIES = 99                     # two digits: the largest value the encoder writes (larger is refused)
MAX_CENTRES = COUNTRIES


class SaveError(ValueError):
    """Bytes that are not a save in the layout above."""


class Refused(ValueError):
    """A position that cannot be encoded."""


_VALUE = re.compile(rb" (\d{1,3}) ")
_COUNTS = re.compile(rb" (\d) , (\d) , (\d) , (\d) ")
_HAND = re.compile(rb"([1-9]*),([1-9]*),([1-9]*),([1-9]*)")


def _lines(data):
    if not isinstance(data, (bytes, bytearray)):
        raise SaveError("a save is bytes")
    if not data.endswith(b"\r\n"):
        raise SaveError("the file does not end with CRLF")
    lines = bytes(data).split(b"\r\n")[:-1]
    if any(b"\r" in line or b"\n" in line for line in lines):
        raise SaveError("a line end other than CRLF")
    return lines


def _value(line, what):
    match = _VALUE.fullmatch(line)
    if not match:
        raise SaveError(f"{what} is not ` v `: {line[:20]!r}")
    return int(match.group(1))


def decode(data):
    """The position in the bytes of a save; SaveError when the bytes are not exactly the layout above."""
    lines = _lines(data)
    if not lines:
        raise SaveError("empty file")
    n = _value(lines[0], "the number of centres")
    if len(lines) != 1 + n + 4 + 2 * COUNTRIES + 2:
        raise SaveError(f"{len(lines)} lines for {n} centres")
    at = 1
    centres = [_value(line, "a centre") for line in lines[at:at + n]]
    at += n
    dft = [_value(line, "a DFT value") for line in lines[at:at + 2]]
    at += 2
    settings = [_value(line, "a setting") for line in lines[at:at + 2]]
    at += 2
    codes = [_value(line, "an owner") for line in lines[at:at + COUNTRIES]]
    at += COUNTRIES
    armies = [_value(line, "an army count") for line in lines[at:at + COUNTRIES]]
    at += COUNTRIES
    counts = _COUNTS.fullmatch(lines[at])
    hands = _HAND.fullmatch(lines[at + 1])
    if not counts or not hands:
        raise SaveError("the card lines are not in the layout")
    if any(code not in CODE_OWNER for code in codes):
        raise SaveError("an owner code that is no colour's")
    cards = {}
    for i, colour in enumerate(COUNT_ORDER):
        count = int(counts.group(1 + i))
        hand = [int(ch) for ch in hands.group(1 + HAND_ORDER.index(colour)).decode()]
        if len(hand) != count:
            raise SaveError(f"{colour} holds {count} cards by the count and {len(hand)} in the hands")
        cards[colour] = hand
    return {"centres": centres, "dft": dft, "settings": settings, "owners": [CODE_OWNER[c] for c in codes],
            "armies": armies, "cards": cards}


def check(position):
    """Raise Refused unless the position is one the format can carry without losing or changing a field."""
    if not isinstance(position, dict) or set(position) != {"centres", "dft", "settings", "owners", "armies", "cards"}:
        raise Refused("a position has exactly: centres, dft, settings, owners, armies, cards")

    def ints(values, what, low, high, length=None):
        if not isinstance(values, list) or (length is not None and len(values) != length):
            raise Refused(f"{what}: a list of {length if length is not None else 'integers'} expected")
        for v in values:
            if type(v) is not int or not low <= v <= high:
                raise Refused(f"{what}: {v!r} is not an integer from {low} to {high}")
        return values

    centres = ints(position["centres"], "centres", 1, COUNTRIES)
    if len(centres) > MAX_CENTRES or len(set(centres)) != len(centres):
        raise Refused("centres: each country at most once")
    ints(position["dft"], "dft", 0, 99, 2)
    ints(position["settings"], "settings", 0, 99, 2)
    ints(position["armies"], "armies", 0, MAX_ARMIES, COUNTRIES)
    owners = position["owners"]
    if not isinstance(owners, list) or len(owners) != COUNTRIES or any(o not in OWNER_CODE for o in owners):
        raise Refused(f"owners: {COUNTRIES} colour names ({', '.join(COLOURS)})")
    cards = position["cards"]
    if not isinstance(cards, dict) or set(cards) != set(COLOURS):
        raise Refused("cards: a hand for each colour")
    for colour in COLOURS:
        hand = cards[colour]
        ints(hand, f"cards of {colour}", CARD_DIGITS.start, CARD_DIGITS.stop - 1)
        if len(hand) > MAX_CARDS:
            raise Refused(f"cards of {colour}: at most {MAX_CARDS}")


def _put(value):
    return f" {value} \r\n".encode()


def encode(position):
    """The bytes of the save for a position; Refused when it cannot be encoded, and also when the bytes would not
    decode back to the same position (the round-trip check)."""
    check(position)
    out = [_put(len(position["centres"]))]
    out += [_put(c) for c in position["centres"]]
    out += [_put(v) for v in position["dft"]] + [_put(v) for v in position["settings"]]
    out += [_put(OWNER_CODE[o]) for o in position["owners"]]
    out += [_put(a) for a in position["armies"]]
    cards = position["cards"]
    out.append((" " + " , ".join(str(len(cards[c])) for c in COUNT_ORDER) + " \r\n").encode())
    out.append((",".join("".join(map(str, cards[c])) for c in HAND_ORDER) + "\r\n").encode())
    data = b"".join(out)
    try:
        back = decode(data)
    except SaveError as exc:
        raise Refused(f"the bytes do not decode: {exc}") from None
    if back != position:
        raise Refused("the bytes decode to another position")
    return data


def roundtrip(data):
    """True when decoding these bytes and encoding the position gives the same bytes; SaveError when they do not
    decode, False when they decode and encode differently."""
    return encode(decode(data)) == bytes(data)
