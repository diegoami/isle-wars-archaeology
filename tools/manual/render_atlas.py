#!/usr/bin/env python3
"""Assemble an illustrated local edition using unchanged, verified E019 PNG files."""
import argparse
import hashlib
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import zlib
import xml.etree.ElementTree as ET
from unittest.mock import patch

from check_atlas import ROOT, load, need, validate


def checkout_roots(repo=ROOT):
    result = subprocess.run(["git", "-C", str(repo), "worktree", "list", "--porcelain"], check=True, text=True, capture_output=True)
    return [Path(line[len("worktree "):]).resolve() for line in result.stdout.splitlines() if line.startswith("worktree ")]


def outside_checkouts(path, roots):
    path = path.resolve()
    need(not any(path.is_relative_to(root.resolve()) for root in roots), f"path is inside a checkout: {path}")
    for parent in (path, *path.parents):
        marker = parent / ".git"
        need(not (marker.is_file() or (marker / "HEAD").is_file()), f"path is inside a checkout: {path}")
    return path


def png_size(path):
    with path.open("rb") as handle:
        header = handle.read(24)
    need(len(header) == 24 and header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR", "not a PNG with IHDR")
    return struct.unpack(">II", header[16:24])


def preflight(frames, mapping, output, roots):
    output = outside_checkouts(output, roots)
    need(not output.exists(), "output must not exist; choose a new edition directory")
    verified = {}
    for frame in frames:
        fid = frame["id"]
        need(fid in mapping, f"{fid}: missing bundle-map entry")
        need(isinstance(mapping[fid], str) and Path(mapping[fid]).is_absolute(), f"{fid}: bundle path must be absolute")
        path = outside_checkouts(Path(mapping[fid]), roots)
        need(path.is_file(), f"{fid}: missing local image")
        expected = frame.get("sha256", "")
        need(len(expected) == 64 and all(c in "0123456789abcdef" for c in expected), f"{fid}: bad/missing hash")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        need(actual == expected, f"{fid}: bad image hash")
        need(png_size(path) == (frame["width"], frame["height"]), f"{fid}: wrong image dimensions")
        verified[fid] = path
    return output, verified


def svg(image_name, frame, annotations, box=None):
    width, height = frame["width"], frame["height"]
    view = box or [0, 0, width, height]
    vb = " ".join(str(v) for v in view)
    result = [f'<svg role="img" aria-label="{escape(frame["state"], quote=True)}" viewBox="{vb}" xmlns="http://www.w3.org/2000/svg">']
    clip_attribute = ""
    if box is not None:
        # viewBox sets the transform, but letterboxing can expose pixels beyond it.
        # Clip the image itself in the same native source-coordinate space.
        clip_id = "detail-" + hashlib.sha256(f"{image_name}:{vb}".encode()).hexdigest()[:16]
        x, y, w, h = box
        result.append(f'<defs><clipPath id="{clip_id}" clipPathUnits="userSpaceOnUse"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath></defs>')
        clip_attribute = f' clip-path="url(#{clip_id})"'
    result.append(f'<image href="images/{image_name}" width="{width}" height="{height}"{clip_attribute}/>')
    if box is None:
        for index, annotation in enumerate(annotations, 1):
            x, y, w, h = annotation["rect"]
            result.append(f'<g><title>{escape(annotation["label"])}</title><rect x="{x}" y="{y}" width="{w}" height="{h}" class="callout"/><text x="{x+3}" y="{y+13}" class="number">{index}</text></g>')
    result.append("</svg>")
    return "".join(result)


def html_edition(atlas, inventory, survey, names):
    claims = {c["id"]: c for c in atlas["claims"]}
    frames = {f["id"]: f for f in survey["frames"]}
    out = ['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
           '<title>Pro map and UI atlas — local illustrated edition</title>',
           '<style>body{font:17px/1.55 system-ui,sans-serif;margin:auto;max-width:1100px;padding:24px;background:#f5f5f1;color:#202522}h1,h2,h3{line-height:1.2}a{color:#145778}svg{display:block;width:100%;height:auto;background:#111}.callout{fill:none;stroke:#ffb600;stroke-width:2;vector-effect:non-scaling-stroke}.number{fill:#fff;stroke:#111;stroke-width:3;paint-order:stroke;font:bold 12px sans-serif}.detail-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px}.detail-grid svg{height:180px}figure{margin:12px 0 24px}figcaption,small{font-size:14px}section{margin-top:48px}code{overflow-wrap:anywhere}.boundary{padding:16px;border-left:5px solid #aa6800;background:#fff0ce}li{margin:8px 0}nav a{margin-right:14px}</style>',
           '<h1>Pro map and UI atlas</h1><p>Own-word guide to preserved, unregistered Windows Pro observations. Original pixels remain local. These rectangles mark observed regions; they are not click targets.</p>',
           '<p class="boundary">The full-board overview is a different deal from the interaction sequence. Country ownership and army values are examples. Image hashes establish identity, not the meaning of the scene. Unknowns and later manual parts remain explicit below.</p><nav>']
    out += [f'<a href="#{escape(v["id"])}">{escape(v["id"])}</a>' for v in atlas["views"]]
    out.append('<a href="#prose">Evidence and prose</a></nav>')
    for view in atlas["views"]:
        fid = view["id"]
        frame = frames[fid]
        annotations = [a for a in atlas["annotations"] if a["frame"] == fid]
        observations = {o["id"]: o for o in frame["observations"]}
        out += [f'<section id="{escape(fid)}"><h2>{escape(fid)} · {escape(frame["state"])}</h2><p>{escape(view["caption"])}</p><figure>', svg(names[fid], frame, annotations), f'<figcaption>Native {frame["width"]} × {frame["height"]}; unchanged image. SHA-256 <code>{frame["sha256"]}</code>. {escape(frame["asset"])}</figcaption></figure><ol>']
        for annotation in annotations:
            obs = observations[annotation["observation"]]
            out.append(f'<li><strong>{escape(annotation["label"])}</strong> {escape(obs["text"])} <small>Confidence: {escape(obs["confidence"])}. Basis: {escape(obs["basis"])}</small></li>')
        out.append('</ol><h3>Bounded detail views</h3><div class="detail-grid">')
        for annotation in annotations:
            out += ['<figure>', svg(names[fid], frame, [], annotation["rect"]), f'<figcaption>{escape(annotation["label"])} · source region {escape(str(annotation["rect"]))}. Same unchanged source image, explicitly clipped in native coordinates.</figcaption></figure>']
        out.append('</div></section>')
    out.append('<section id="prose"><h2>Evidence and prose</h2>')
    for section in ("Map", "Reading the board", "Interaction states", "Evidence boundaries"):
        out.append(f'<h3>{section}</h3>')
        for claim in claims.values():
            if claim["section"] == section:
                refs = claim.get("sources", []) or claim.get("limitation_sources", [])
                out.append(f'<p id="{escape(claim["id"])}"><strong>{escape(claim["id"])}</strong> {escape(claim["text"])} <small>Layer: {claim["layer"]}; confidence: {claim["confidence"]}; sources: {escape(", ".join(refs))}.</small></p>')
    out.append('<h3>Source directory</h3><ul>')
    for source in atlas["sources"]:
        out.append(f'<li>{escape(source["id"])} — {escape(source["path"])}{escape("#"+source["anchor"] if source.get("anchor") else "")}: {escape(source["scope"])}</li>')
    out.append('</ul><h3>Manual subject inventory</h3><ul>')
    for subject in inventory["subjects"]:
        out.append(f'<li>{escape(subject["description"])} — {subject["milestone"]}, {subject["coverage"]}. {escape(subject.get("boundary", "Covered by atlas claims: " + ", ".join(subject.get("claims", []))))}</li>')
    out.append('</ul><h3>Survey limitations</h3><ul>')
    out += [f'<li>{escape(x)}</li>' for x in survey["limitations"]]
    out.append('</ul></section></html>')
    return "\n".join(out)


def render(atlas, inventory, survey, mapping, output, roots, guide_data=None):
    # Complete structural, location, hash and dimension checks before creating output.
    frames = survey["frames"] + (guide_data[1]["frames"] if guide_data else [])
    need(len({f["id"] for f in frames}) == len(frames), "guide/atlas image IDs collide")
    output, paths = preflight(frames, mapping, output, roots)
    names = {fid: f'{fid}-{hashlib.sha256(path.read_bytes()).hexdigest()[:16]}.png' for fid, path in paths.items()}
    atlas_document = html_edition(atlas, inventory, survey, names)
    document = atlas_document
    if guide_data:
        from guide_html import html_guide
        document = html_guide(*guide_data, names, svg)
        atlas_document = atlas_document.replace('<h1>Pro map and UI atlas</h1>', '<nav><a href="index.html">Player guide</a> · <a href="index.html#walkthrough">Worked turn</a></nav><h1>Pro map and UI atlas</h1>')
    output.mkdir(parents=True)
    (output / "images").mkdir()
    for fid, path in paths.items():
        shutil.copyfile(path, output / "images" / names[fid])
        # Detect bytes changing after preflight; abort before writing index.html.
        # Retain the partial output and copied bytes for diagnosis; this is not atomic publication.
        need(hashlib.sha256((output / "images" / names[fid]).read_bytes()).hexdigest() == next(f["sha256"] for f in frames if f["id"] == fid), f"{fid}: image changed during copy")
    if guide_data:
        (output / "atlas.html").write_text(atlas_document, encoding="utf-8")
    (output / "index.html").write_text(document, encoding="utf-8")
    receipt = {"schema": "pro-atlas-render/1", "images": [{"id": f["id"], "sha256": f["sha256"], "width": f["width"], "height": f["height"]} for f in frames], "html_sha256": hashlib.sha256(document.encode()).hexdigest(), "annotation_count": len(atlas["annotations"]), "boundary": "Local receipt only; no original bytes or paths belong in repository evidence."}
    if guide_data:
        receipt["atlas_html_sha256"] = hashlib.sha256(atlas_document.encode()).hexdigest()
        receipt["guide_annotation_count"] = len(guide_data[0]["annotations"])
        receipt["guide_image_count"] = len(guide_data[1]["frames"])
        receipt["walkthrough_frames"] = guide_data[0]["walkthrough"]["frames"]
    (output / "render-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return output / "index.html"


def assert_detail_clip(markup, expected):
    """Synthetic oracle: verify the image binding, units and exact clipping extent."""
    tree = ET.fromstring(markup)
    ns = {"s": "http://www.w3.org/2000/svg"}
    images = tree.findall("s:image", ns)
    need(len(images) == 1, "detail must contain one source image")
    reference = images[0].get("clip-path", "")
    need(reference.startswith("url(#") and reference.endswith(")"), "detail image is not bound to a clip")
    clip_id = reference[5:-1]
    clips = [node for node in tree.findall("s:defs/s:clipPath", ns) if node.get("id") == clip_id]
    need(len(clips) == 1 and clips[0].get("clipPathUnits") == "userSpaceOnUse", "detail clip is missing or not in native user space")
    rects = clips[0].findall("s:rect", ns)
    need(len(rects) == 1 and len(list(clips[0])) == 1, "detail clip must be a single rectangle")
    actual = [float(rects[0].get(key, "nan")) for key in ("x", "y", "width", "height")]
    need(actual == expected, "detail clip extent differs from observed region")


def clipping_controls():
    frame = {"width": 100, "height": 80, "state": "Synthetic clipping fixture"}
    for box in ([10, 20, 60, 5], [20, 10, 5, 60]):
        markup = svg("synthetic.png", frame, [], box)
        assert_detail_clip(markup, box)
        # Controls operate on generated markup: unused defs cannot satisfy the oracle.
        controls = [
            ("unbound image", markup.replace(' clip-path="url(', ' unused="url(')),
            ("missing definition", markup.replace('<clipPath ', '<unused ').replace('</clipPath>', '</unused>')),
            ("wrong coordinate space", markup.replace('userSpaceOnUse', 'objectBoundingBox')),
            ("exposed surrounding pixels", markup.replace(f'width="{box[2]}" height="{box[3]}"', f'width="{box[2]+1}" height="{box[3]}"')),
        ]
        for label, mutated in controls:
            try:
                assert_detail_clip(mutated, box)
            except ValueError:
                pass
            else:
                raise ValueError(f"detail clipping control escaped: {label}")
    print("PASS: wide/tall details bind source images to exact native-space clips; 8 clipping mutations rejected.")


def guide_render_controls(tmp, positive_frame, positive_atlas, original):
    """Exercise the complete companion edition using only invented PNG files."""
    from check_guide import synthetic_fixture, validate as validate_guide
    fixture = tmp / "guide-fixture"
    fixture.mkdir()
    guide, guide_survey = synthetic_fixture(fixture)
    mapping = {"V": str(original)}
    entries = []
    for n, frame in enumerate(guide_survey["frames"], 1):
        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
        pixels = (b"\x00" + bytes([n, 0, 0]) * 80) * 60
        data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 80, 60, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b"")
        path = fixture / frame["asset"]
        path.write_bytes(data)
        frame["sha256"] = hashlib.sha256(data).hexdigest()
        mapping[frame["id"]] = str(path)
        entries.append({"name": frame["asset"], "asset": frame["asset"], "sha256": frame["sha256"], "class": "recording"})
    for name in ("record.json", "other-record.json"):
        (fixture / name).write_text(json.dumps({"status": "completed", "outputs": entries}))
    (fixture / "manifest.json").write_text(json.dumps({"files": entries}))
    validate_guide(guide, guide_survey, fixture)
    atlas_survey = {"frames": [positive_frame], "limitations": ["Synthetic only."]}
    output = tmp / "combined-edition"
    render(positive_atlas, {"subjects": []}, atlas_survey, mapping, output, [], (guide, guide_survey))
    class Links(HTMLParser):
        def __init__(self):
            super().__init__()
            self.ids, self.hrefs = set(), []
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if "id" in attrs:
                need(attrs["id"] not in self.ids, "duplicate HTML chapter/frame ID")
                self.ids.add(attrs["id"])
            if tag == "a":
                self.hrefs.append(attrs.get("href", ""))
    documents = {}
    for name in ("index.html", "atlas.html"):
        parser = Links()
        parser.feed((output / name).read_text())
        documents[name] = parser
    for name, parser in documents.items():
        for href in parser.hrefs:
            target, _, fragment = href.partition("#")
            need((target or name) in documents, "broken local companion-page link")
            if fragment:
                need(fragment in documents[target or name].ids, "broken chapter/walkthrough link")
    need({"topic-" + t["id"] for t in guide["topics"]} <= documents["index.html"].ids and "walkthrough" in documents["index.html"].ids, "guide chapters/walkthrough missing")
    need(set(guide["walkthrough"]["frames"]) <= documents["index.html"].ids, "illustrated walkthrough missing")
    receipt = json.loads((output / "render-receipt.json").read_text())
    need(receipt["guide_image_count"] == 11 and len(receipt["images"]) == 12, "companion image set missing")
    guide_survey["frames"][-1]["sha256"] = "a" * 64
    rejected = tmp / "bad-companion-edition"
    try:
        render(positive_atlas, {"subjects": []}, atlas_survey, mapping, rejected, [], (guide, guide_survey))
    except ValueError as error:
        need("bad image hash" in str(error) and not rejected.exists(), "guide pre-copy refusal failed")
    else:
        raise ValueError("bad companion image hash escaped preflight")
    print("PASS: synthetic guide/atlas edition retains both pages, all chapter/step links and image references; bad guide hash refused before copying.")


def self_test():
    clipping_controls()
    with tempfile.TemporaryDirectory(prefix="T63-render-controls-", dir="/tmp") as name:
        tmp = Path(name)
        checkout = tmp / "checkout"
        checkout.mkdir()
        (checkout / ".git").mkdir()
        (checkout / ".git" / "HEAD").write_text("ref: refs/heads/synthetic\n")
        original = tmp / "synthetic.png"
        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
        original.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 1, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(b"\x00" + b"\x00\x00\x00" * 2)) + chunk(b"IEND", b""))
        frame = {"id": "V", "sha256": hashlib.sha256(original.read_bytes()).hexdigest(), "width": 2, "height": 1}
        output = tmp / "edition"
        preflight([frame], {"V": str(original)}, output, [checkout])
        controls = [
            ("bad hash", dict(frame, sha256="a" * 64), {"V": str(original)}, output, "bad image hash"),
            ("missing hash", dict(frame, sha256=""), {"V": str(original)}, output, "bad/missing hash"),
            ("wrong dimensions", dict(frame, width=3), {"V": str(original)}, output, "wrong image dimensions"),
            ("missing map entry", frame, {}, output, "missing bundle-map"),
            ("in-checkout output", frame, {"V": str(original)}, checkout / "edition", "inside a checkout"),
            ("unregistered checkout output", frame, {"V": str(original)}, checkout / "edition", "inside a checkout"),
        ]
        for label, test_frame, mapping, destination, expected in controls:
            try:
                preflight([test_frame], mapping, destination, [] if label.startswith("unregistered") else [checkout])
            except ValueError as error:
                need(expected in str(error), f"wrong failure for {label}: {error}")
                need(not destination.exists(), f"{label}: copied/created output before refusal")
                print(f"PASS control: {label} refused before copying")
            else:
                raise ValueError(f"control escaped: {label}")
        link = tmp / "alias"
        link.symlink_to(checkout, target_is_directory=True)
        try:
            preflight([frame], {"V": str(original)}, link / "edition", [checkout])
        except ValueError:
            print("PASS control: symlink into checkout refused before copying")
        else:
            raise ValueError("symlink control escaped")
        shutil.copyfile(original, checkout / "synthetic.png")
        try:
            preflight([frame], {"V": str(checkout / "synthetic.png")}, output, [checkout])
        except ValueError:
            print("PASS control: in-checkout image refused before copying")
        else:
            raise ValueError("in-checkout source control escaped")
        need(not output.exists(), "negative controls created output")
        positive_frame = dict(frame, state="Synthetic visible state", asset="synthetic.png", observations=[{"id": "O", "text": "Invented feature for rendering.", "confidence": "synthetic", "basis": "Synthetic input only."}])
        positive_atlas = {"claims": [], "sources": [], "views": [{"id": "V", "caption": "Synthetic render baseline."}], "annotations": [{"id": "A", "frame": "V", "observation": "O", "rect": [0, 0, 1, 1], "label": "Synthetic feature"}]}
        html_path = render(positive_atlas, {"subjects": []}, {"frames": [positive_frame], "limitations": ["Synthetic only."]}, {"V": str(original)}, output, [checkout])
        document = html_path.read_text()
        need(document.count("<svg ") == 2 and 'class="callout"' in document and 'viewBox="0 0 1 1"' in document, "rendered full image/annotation/detail missing")
        copied = list((output / "images").iterdir())
        need(len(copied) == 1 and copied[0].read_bytes() == original.read_bytes(), "render changed image bytes")
        need((output / "render-receipt.json").is_file(), "render receipt missing")
        interrupted = tmp / "interrupted-edition"
        def changed_copy(source, destination):
            Path(destination).write_bytes(b"synthetic copy-time change")
        with patch.object(shutil, "copyfile", side_effect=changed_copy):
            try:
                render(positive_atlas, {"subjects": []}, {"frames": [positive_frame], "limitations": ["Synthetic only."]}, {"V": str(original)}, interrupted, [checkout])
            except ValueError as error:
                need("image changed during copy" in str(error), "copy-time control failed for wrong reason")
            else:
                raise ValueError("copy-time changed image was accepted")
        need(not (interrupted / "index.html").exists(), "copy-time failure wrote an index")
        partial_images = list((interrupted / "images").iterdir())
        need(len(partial_images) == 1 and partial_images[0].read_bytes() == b"synthetic copy-time change", "copy-time failure discarded diagnostic bytes")
        print("PASS: synthetic copy-time hash failure preserves partial output and omits index.html.")
        print("PASS: synthetic positive edition has unchanged PNG, full view, callout, bounded detail and receipt.")
        guide_render_controls(tmp, positive_frame, positive_atlas, original)
        print("PASS: synthetic PNG baselines and 8 renderer negative controls; no originals used.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-map", type=Path, help="local JSON object mapping survey frame IDs to absolute PNG paths")
    parser.add_argument("--output", type=Path, help="new directory outside every checkout")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--include-guide", action="store_true", help="add the player guide and walkthrough as index.html; retain atlas.html")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
            return
        need(args.bundle_map is not None and args.output is not None, "--bundle-map and --output required")
        atlas, inventory, survey = load()
        print(validate(atlas, inventory, survey))
        guide_data = None
        if args.include_guide:
            from check_guide import load as load_guide, validate as validate_guide
            guide_data = load_guide()
            print(validate_guide(*guide_data))
        mapping = json.loads(args.bundle_map.read_text())
        print(f"Rendered verified local edition: {render(atlas, inventory, survey, mapping, args.output, checkout_roots(), guide_data)}")
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"FAIL: {error}\n")


if __name__ == "__main__":
    main()
