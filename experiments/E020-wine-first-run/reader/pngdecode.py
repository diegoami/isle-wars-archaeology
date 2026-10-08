"""A small PNG decoder for the sitting frames (T40): 8-bit RGB or RGBA, not interlaced, every
filter type, standard library plus numpy. It exists so that the reader needs no imaging library and
no OCR engine; a frame comes back as an (height, width, 3) uint8 array.

The decoder refuses what it does not understand (palette or 16-bit images, interlacing, a bad CRC,
a short IDAT) rather than guessing: an unreadable frame is unread, never a wrong one.
"""
import struct
import zlib

import numpy as np

SIGNATURE = b"\x89PNG\r\n\x1a\n"


class PngError(ValueError):
    """The bytes are not a PNG this decoder reads."""


def chunks(data):
    """(type, body) of every chunk, each CRC checked."""
    if data[:8] != SIGNATURE:
        raise PngError("not a PNG: bad signature")
    pos, out = 8, []
    while pos + 8 <= len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        crc = data[pos + 8 + length:pos + 12 + length]
        if len(body) != length or len(crc) != 4 or struct.unpack(">I", crc)[0] != zlib.crc32(kind + body):
            raise PngError(f"bad chunk {kind!r}")
        out.append((kind, body))
        pos += 12 + length
        if kind == b"IEND":
            return out
    raise PngError("no IEND chunk")


def _paeth_row(line, up, bpp):
    row = list(line)
    for i in range(len(row)):
        a = row[i - bpp] if i >= bpp else 0
        b = up[i]
        c = up[i - bpp] if i >= bpp else 0
        p = a + b - c
        pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
        pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
        row[i] = (row[i] + pred) & 0xFF
    return row


def _average_row(line, up, bpp):
    row = list(line)
    for i in range(len(row)):
        left = row[i - bpp] if i >= bpp else 0
        row[i] = (row[i] + ((left + up[i]) >> 1)) & 0xFF
    return row


def unfilter(raw, width, height, bpp):
    """The scanlines of `raw` (a filter byte then width*bpp bytes per row) without their filters,
    as a (height, width*bpp) uint8 array."""
    stride = width * bpp
    if len(raw) != height * (stride + 1):
        raise PngError("the image data is not height x (1 + stride) bytes")
    out = np.zeros((height, stride), dtype=np.uint8)
    previous = [0] * stride
    for y in range(height):
        base = y * (stride + 1)
        kind = raw[base]
        line = raw[base + 1:base + 1 + stride]
        if kind == 0:
            row = list(line)
        elif kind == 1:       # Sub: a running sum of each channel along the row
            arr = np.frombuffer(line, dtype=np.uint8).astype(np.int64).reshape(width, bpp)
            row = (arr.cumsum(axis=0) & 0xFF).reshape(stride).tolist()
        elif kind == 2:       # Up
            row = [(v + u) & 0xFF for v, u in zip(line, previous)]
        elif kind == 3:
            row = _average_row(line, previous, bpp)
        elif kind == 4:
            row = _paeth_row(line, previous, bpp)
        else:
            raise PngError(f"unknown filter type {kind}")
        out[y] = row
        previous = row
    return out


def decode(data):
    """(height, width, 3) uint8 RGB array of the PNG `data` (an alpha channel is dropped)."""
    parts = chunks(data)
    if not parts or parts[0][0] != b"IHDR" or len(parts[0][1]) != 13:
        raise PngError("no IHDR first")
    width, height, depth, colour, _compression, _filter, interlace = struct.unpack(">IIBBBBB", parts[0][1])
    if depth != 8 or colour not in (2, 6) or interlace != 0:
        raise PngError(f"only 8-bit RGB or RGBA, not interlaced (depth {depth}, colour type {colour}, "
                       f"interlace {interlace})")
    bpp = 3 if colour == 2 else 4
    try:
        raw = zlib.decompress(b"".join(body for kind, body in parts if kind == b"IDAT"))
    except zlib.error as exc:
        raise PngError(f"the image data does not inflate: {exc}") from None
    pixels = unfilter(raw, width, height, bpp).reshape(height, width, bpp)
    return np.ascontiguousarray(pixels[:, :, :3])


def decode_file(path):
    with open(path, "rb") as handle:
        return decode(handle.read())


def encode(rgb, filters=None):
    """A PNG of the (height, width, 3) uint8 array `rgb`, for tests. `filters` is a list of filter
    types cycled over the rows (default 0); each is applied properly, so a decoder that skips one
    returns different pixels."""
    height, width, _ = rgb.shape
    stride = width * 3
    flat = rgb.reshape(height, stride).astype(np.int64)
    rows, previous = [], [0] * stride
    for y in range(height):
        kind = 0 if filters is None else filters[y % len(filters)]
        cur = flat[y].tolist()
        line = list(cur)
        for i in range(stride):
            a = cur[i - 3] if i >= 3 else 0
            b = previous[i]
            c = previous[i - 3] if i >= 3 else 0
            if kind == 0:
                pred = 0
            elif kind == 1:
                pred = a
            elif kind == 2:
                pred = b
            elif kind == 3:
                pred = (a + b) >> 1
            elif kind == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
            else:
                raise ValueError(kind)
            line[i] = (cur[i] - pred) & 0xFF
        rows.append(bytes([kind]) + bytes(line))
        previous = cur

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))

    return (SIGNATURE + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"".join(rows), 6)) + chunk(b"IEND", b""))
