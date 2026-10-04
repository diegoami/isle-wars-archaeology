#!/usr/bin/env python3
"""savestate_members.py OUTROOT TAG...: for each probe's DOSBox-X savestate (a zip), print every
member's size and sha256, then decompress the Memory member (a zlib stream) and count the bytes
in which each image differs from the first tag's, by 4 KiB page. Reads only; the savestates stay
machine-local (they hold the game's memory)."""
import hashlib
import sys
import zipfile
import zlib
from pathlib import Path

root, tags = Path(sys.argv[1]), sys.argv[2:]
members, images = {}, {}
for tag in tags:
    z = zipfile.ZipFile(root / tag / "save" / "state.sav")
    members[tag] = {i.filename: (i.file_size, hashlib.sha256(z.read(i)).hexdigest()) for i in z.infolist()}
    d = zlib.decompressobj()
    images[tag] = d.decompress(z.read("Memory"))
    print(f"{tag}: savestate sha256 {hashlib.sha256((root / tag / 'save' / 'state.sav').read_bytes()).hexdigest()}; "
          f"Memory member: zlib stream, {len(images[tag])} bytes inflated, {len(d.unused_data)} bytes after "
          f"the stream, inflated sha256 {hashlib.sha256(images[tag]).hexdigest()}")
print()
print("member\t" + "\t".join(tags))
for name in members[tags[0]]:
    values = [members[t].get(name) for t in tags]
    same = len({v for v in values}) == 1
    print(f"{name}\t" + ("same in all: %d bytes %s" % (values[0][0], values[0][1][:16]) if same else
                         "\t".join(f"{v[0]}:{v[1][:12]}" if v else "absent" for v in values)))
print()
first = images[tags[0]]
for tag in tags[1:]:
    other = images[tag]
    diff = [i for i in range(min(len(first), len(other))) if first[i] != other[i]]
    pages = {}
    for i in diff:
        pages[i >> 12] = pages.get(i >> 12, 0) + 1
    print(f"{tag} vs {tags[0]}: {len(diff)} bytes differ; by page (offset: count) " +
          ", ".join(f"0x{p << 12:x}: {n}" for p, n in sorted(pages.items())))
