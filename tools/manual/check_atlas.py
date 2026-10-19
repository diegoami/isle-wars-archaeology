#!/usr/bin/env python3
"""Check T63's text/provenance accounting; this does not prove prose or appearance."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parents[2]
HEX = re.compile(r"[0-9a-f]{64}")
LAYERS = {"appearance", "topology", "hit-area", "rendering", "interaction", "scope"}
UNKNOWN_IDS = {"U-hit", "U-mechanism", "U-neighbours", "U-events", "U-registration", "U-islands"}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def substantive(value, label):
    need(isinstance(value, str) and len(value.strip()) >= 16, f"{label}: absent prose")
    need(not re.search(r"\b(TODO|TBD|placeholder|lorem ipsum)\b", value, re.I), f"{label}: placeholder")


def unique(items, label):
    result = {}
    for item in items:
        key = item.get("id")
        need(isinstance(key, str) and key and key not in result, f"{label}: missing/duplicate ID")
        result[key] = item
    need(result, f"{label}: empty")
    return result


def repo_file(root, name):
    need(isinstance(name, str) and not Path(name).is_absolute(), "source must be repository-relative")
    path = (root / name).resolve()
    need(path.is_relative_to(root.resolve()) and path.is_file(), f"missing repository source: {name}")
    return path


def region_ok(rect, width, height, label):
    need(isinstance(rect, list) and len(rect) == 4, f"{label}: invalid annotation bounds")
    need(all(type(v) in (int, float) and math.isfinite(v) for v in rect), f"{label}: invalid annotation bounds")
    x, y, w, h = rect
    need(x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= width and y + h <= height,
         f"{label}: invalid annotation bounds")


def validate(atlas, inventory, survey, root=ROOT):
    need(atlas.get("schema") == "pro-atlas/1", "atlas schema")
    need(inventory.get("schema") == "pro-manual-inventory/1", "inventory schema")
    substantive(survey.get("method", survey.get("scope")), "survey method/scope")
    need(survey.get("limitations"), "survey limitations missing")
    sources = unique(atlas.get("sources", []), "sources")
    for sid, source in sources.items():
        path = repo_file(root, source.get("path"))
        need(source.get("kind") in {"documented", "static", "reported-visual", "local-visual", "limitation", "implementation"}, f"{sid}: source kind")
        substantive(source.get("scope"), f"{sid} scope")
        anchor = source.get("anchor")
        if anchor:
            headings = re.findall(r"^#+\s+(.+)$", path.read_text(), re.M)
            slugs = [re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in headings]
            need(anchor in slugs, f"{sid}: citation anchor absent")
    claims = unique(atlas.get("claims", []), "claims")
    for cid, claim in claims.items():
        substantive(claim.get("text"), cid)
        need(claim.get("layer") in LAYERS, f"{cid}: layer")
        need(claim.get("confidence") in {"documented", "high-bounded", "moderate-bounded", "static-high", "unknown"}, f"{cid}: confidence")
        refs = claim.get("sources", [])
        limits = claim.get("limitation_sources", [])
        need(all(s in sources for s in refs + limits), f"{cid}: missing sources")
        if cid in UNKNOWN_IDS or claim["confidence"] == "unknown":
            need(claim["confidence"] == "unknown" and not refs and limits, f"{cid}: claimed evidence for unknown")
        else:
            need(refs, f"{cid}: missing sources")
        need(claim.get("section") in {"Map", "Reading the board", "Interaction states", "Evidence boundaries"}, f"{cid}: section")
    need(UNKNOWN_IDS <= claims.keys(), "required unknowns missing")
    need("#259" in claims["U-islands"]["text"], "#259 unknown missing")
    for layer in LAYERS:
        need(any(c["layer"] == layer for c in claims.values()), f"missing layer: {layer}")
    frames = unique(survey.get("frames", []), "survey frames")
    frame_refs = unique(atlas.get("views", []), "views")
    need(set(frames) == set(frame_refs), "image references do not cover survey")
    need(any(v.get("role") == "full-board" for v in frame_refs.values()), "full board missing")
    states, hashes, observations = set(), set(), {}
    for fid, frame in frames.items():
        width, height = frame.get("width"), frame.get("height")
        need(type(width) is int and type(height) is int and width > 0 and height > 0, f"{fid}: dimensions absent")
        digest = frame.get("sha256")
        need(isinstance(digest, str) and HEX.fullmatch(digest), f"{fid}: bad/missing hash")
        record = read_json(repo_file(root, frame.get("record")))
        manifest = read_json(repo_file(root, frame.get("manifest")))
        entries = [e for e in manifest.get("files", []) if e.get("asset") == frame.get("asset")]
        need(len(entries) == 1 and entries[0].get("sha256") == digest and entries[0].get("class") in {"recording", "screenshot"}, f"{fid}: image/manifest mismatch")
        need(any(e.get("name") == entries[0]["name"] and e.get("sha256") == digest for e in record.get("outputs", [])), f"{fid}: image/record mismatch")
        need(record.get("status") == "completed", f"{fid}: incomplete record")
        for key in ("record", "manifest"):
            if key + "_sha256" in frame:
                need(hashlib.sha256(repo_file(root, frame[key]).read_bytes()).hexdigest() == frame[key + "_sha256"], f"{fid}: {key} hash mismatch")
        view = frame_refs[fid]
        substantive(view.get("caption"), f"{fid} caption")
        need(view.get("claims") and all(c in claims and claims[c]["confidence"] != "unknown" for c in view["claims"]), f"{fid}: view claims")
        if view.get("role") == "interaction-state":
            need(isinstance(frame.get("state"), str) and len(frame["state"]) >= 3, f"{fid}: state absent")
            need(frame["state"] not in states and digest not in hashes, "states must use distinct states and image bytes")
            states.add(frame["state"])
            hashes.add(digest)
        else:
            need(view.get("role") in {"full-board", "detail-reference"}, f"{fid}: view role")
        obs = unique(frame.get("observations", []), f"{fid} observations")
        for oid, observation in obs.items():
            need(oid not in observations, "observation IDs must be globally unique")
            substantive(observation.get("text"), oid)
            need(isinstance(observation.get("confidence"), str) and len(observation["confidence"]) >= 3, f"{oid}: confidence absent")
            substantive(observation.get("basis"), f"{oid} basis")
            region_ok(observation.get("region"), width, height, oid)
            observations[oid] = (fid, observation)
    need(len(states) >= 3, "at least three evidenced interaction states required")
    features = unique(inventory.get("visual_features", []), "visual features")
    accounted = []
    for feature in features.values():
        substantive(feature.get("description"), "feature description")
        need(feature.get("claims") and all(c in claims and claims[c]["confidence"] != "unknown" for c in feature["claims"]), "feature claim/source missing")
        need(feature.get("observations"), "missing visual features: evidence absent")
        for oid in feature["observations"]:
            need(oid in observations, "feature observation absent")
            accounted.append(oid)
    need(set(accounted) == set(observations), "missing visual features: survey observations unaccounted")
    annotations = unique(atlas.get("annotations", []), "annotations")
    need(set(a.get("observation") for a in annotations.values()) == set(observations), "annotation references do not cover observations")
    for aid, annotation in annotations.items():
        oid = annotation.get("observation")
        fid, observation = observations[oid]
        need(annotation.get("frame") == fid, f"{aid}: annotation frame mismatch")
        region_ok(annotation.get("rect"), frames[fid]["width"], frames[fid]["height"], aid)
        need(annotation["rect"] == observation["region"], f"{aid}: annotation not main's observed region")
        need(isinstance(annotation.get("label"), str) and len(annotation["label"]) >= 3, f"{aid}: label absent")
    subjects = unique(inventory.get("subjects", []), "manual subjects")
    documented = unique(survey.get("manual_source", {}).get("subjects", []), "survey manual subjects")
    need(set(subjects) == set(documented), "manual subject inventory incomplete")
    need(HEX.fullmatch(survey.get("manual_source", {}).get("sha256", "")), "manual source hash missing")
    for sid, subject in subjects.items():
        substantive(subject.get("description"), f"{sid} description")
        need(subject.get("milestone") in {"T63", "T64", "T65"}, f"{sid}: milestone")
        need(subject.get("coverage") in {"atlas", "later-part", "explicit-unknown"}, f"{sid}: coverage")
        need(subject.get("sources") and all(s in sources for s in subject["sources"]), f"{sid}: missing sources")
        need(subject.get("claims") and all(c in claims for c in subject["claims"]) if subject["coverage"] == "atlas" else bool(subject.get("boundary")), f"{sid}: coverage boundary absent")
        raw = documented[sid]
        need(type(raw.get("line_start")) is int and type(raw.get("line_end")) is int and 1 <= raw["line_start"] <= raw["line_end"] <= survey["manual_source"]["line_count"], f"{sid}: manual source range")
    text = repo_file(root, atlas.get("text_path")).read_text()
    for cid, claim in claims.items():
        need(claim["text"] in text and f"**{cid}**" in text, f"{cid}: manual prose/claim mismatch")
    return f"PASS: {len(claims)} claims, {len(subjects)} manual subjects, {len(features)} visual features, {len(frames)} images, {len(annotations)} annotations; {len(states)} distinct interaction states. Semantic prose and alignment require independent/local review."


def load(root=ROOT):
    return (read_json(root / "manual/pro/atlas.json"), read_json(root / "manual/pro/inventory.json"),
            read_json(root / "docs/prototypes/T63/visual-source-survey-r1.json"))


def self_test():
    """All inputs are invented metadata and tiny text files, never original images."""
    with tempfile.TemporaryDirectory(prefix="T63-atlas-controls-") as name:
        root = Path(name)
        (root / "source.md").write_text("# Synthetic source\nInvented metadata for validation.\n")
        digest = "a" * 64
        (root / "record.json").write_text(json.dumps({"status": "completed", "outputs": [{"name": f"{i}.png", "sha256": str(i) * 64} for i in range(1, 5)]}))
        (root / "manifest.json").write_text(json.dumps({"files": [{"name": f"{i}.png", "asset": f"{i}.png", "sha256": str(i) * 64, "class": "recording"} for i in range(1, 5)]}))
        claims = [{"id": f"C-{layer}", "text": f"Synthetic bounded description of {layer}.", "layer": layer, "confidence": "high-bounded", "sources": ["S"], "section": "Map"} for layer in sorted(LAYERS)]
        claims += [{"id": uid, "text": f"Unknown synthetic boundary for {uid}, including #259 where relevant.", "layer": "scope", "confidence": "unknown", "sources": [], "limitation_sources": ["S"], "section": "Evidence boundaries"} for uid in sorted(UNKNOWN_IDS)]
        (root / "atlas.md").write_text("\n".join(f"**{c['id']}** {c['text']}" for c in claims))
        atlas = {"schema": "pro-atlas/1", "text_path": "atlas.md", "sources": [{"id": "S", "path": "source.md", "kind": "local-visual", "scope": "Synthetic source, no game material."}], "claims": claims, "views": [], "annotations": []}
        survey = {"method": "Synthetic metadata only, no image reads.", "limitations": ["Invented."], "frames": [], "manual_source": {"sha256": digest, "line_count": 10, "subjects": [{"id": "M", "line_start": 1, "line_end": 10}]}}
        inventory = {"schema": "pro-manual-inventory/1", "visual_features": [], "subjects": [{"id": "M", "description": "Synthetic subject inventory description.", "milestone": "T63", "coverage": "atlas", "sources": ["S"], "claims": ["C-appearance"]}]}
        for i in range(1, 5):
            fid, oid = f"V{i}", f"O{i}"
            survey["frames"].append({"id": fid, "record": "record.json", "manifest": "manifest.json", "asset": f"{i}.png", "sha256": str(i) * 64, "width": 80, "height": 60, "state": f"Distinct synthetic state {i}", "observations": [{"id": oid, "text": "Invented visible feature description.", "basis": "Synthetic observation basis only.", "confidence": "Synthetic bounded confidence.", "region": [1, 2, 20, 10]}]})
            atlas["views"].append({"id": fid, "role": "full-board" if i == 1 else "interaction-state", "caption": "Synthetic frame caption with bounded scope.", "claims": ["C-appearance"]})
            atlas["annotations"].append({"id": f"A{i}", "frame": fid, "observation": oid, "rect": [1, 2, 20, 10], "label": "Synthetic visible region callout."})
            inventory["visual_features"].append({"id": f"F{i}", "description": "Synthetic visible feature description.", "observations": [oid], "claims": ["C-appearance"]})
        validate(atlas, inventory, survey, root)
        controls = [
            ("missing visual feature", "missing visual features", lambda a, i, s: i["visual_features"].pop()),
            ("missing source", "missing sources", lambda a, i, s: a["claims"][0].update(sources=[])),
            ("invalid annotation bounds", "invalid annotation bounds", lambda a, i, s: a["annotations"][0].update(rect=[79, 0, 2, 2])),
            ("claimed evidence for unknown", "claimed evidence for unknown", lambda a, i, s: next(c for c in a["claims"] if c["id"] == "U-mechanism").update(sources=["S"])),
            ("promoted unknown", "claimed evidence for unknown", lambda a, i, s: next(c for c in a["claims"] if c["id"] == "U-mechanism").update(confidence="high-bounded", sources=["S"])),
            ("missing image hash", "bad/missing hash", lambda a, i, s: s["frames"][0].pop("sha256")),
            ("reused image state", "image/manifest mismatch", lambda a, i, s: s["frames"][2].update(sha256=s["frames"][1]["sha256"])),
            ("absent manual subject", "inventory incomplete", lambda a, i, s: i["subjects"].append(dict(i["subjects"][0], id="extra"))),
            ("placeholder prose", "placeholder", lambda a, i, s: a["claims"][0].update(text="TODO placeholder missing a substantive description.")),
        ]
        for name, expected, mutate in controls:
            a, i, s = copy.deepcopy((atlas, inventory, survey))
            mutate(a, i, s)
            try:
                validate(a, i, s, root)
            except ValueError as error:
                need(expected in str(error), f"control {name} failed for wrong reason: {error}")
                print(f"PASS control: {name} rejected ({error})")
            else:
                raise ValueError(f"control escaped: {name}")
        print(f"PASS: synthetic baseline and {len(controls)} atlas negative controls; no originals used.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
        else:
            print(validate(*load()))
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as error:
        parser.exit(1, f"FAIL: {error}\n")


if __name__ == "__main__":
    main()
