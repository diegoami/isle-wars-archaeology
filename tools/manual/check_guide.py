#!/usr/bin/env python3
"""Check guide coverage/provenance, not semantic truth or screenshot appearance."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import tempfile

from check_atlas import HEX, ROOT, need, read_json, region_ok, repo_file, substantive, unique

TOPICS = {"setup-options", "board-panels", "placement", "attack-capture", "movement", "cards-trade", "end-turn", "cancel-confirm", "help-navigation", "save-load", "concession-results", "registration"}
ASPECTS = ("visible", "actions", "feedback", "cancel")
BASES = {"local-visual", "static", "documented", "unobserved", "unsupported"}
STAGES = ["placement-selection", "allocation-chosen", "placement-committed", "attack-ready", "attack-result", "turn-menu-return", "after-pass"]


def validate(guide, survey, root=ROOT):
    need(guide.get("schema") == "pro-guide/1", "guide schema")
    sources = unique(guide.get("sources", []), "guide sources")
    for sid, source in sources.items():
        path = repo_file(root, source.get("path"))
        need(source.get("kind") in {"local-visual", "static", "documented", "limitation"}, f"{sid}: source kind")
        substantive(source.get("scope"), f"{sid} scope")
        if source.get("anchor"):
            import re
            headings = re.findall(r"^#+\s+(.+)$", path.read_text(), re.M)
            slugs = [re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in headings]
            need(source["anchor"] in slugs, f"{sid}: missing source anchor")
    topics = unique(guide.get("topics", []), "guide topics")
    need(set(topics) == TOPICS, "missing or unexpected required topics")
    frames = unique(survey.get("frames", []), "guide survey frames")
    images = unique(guide.get("images", []), "guide images")
    need(set(images) == set(frames), "guide images do not reconcile survey")
    need(len(frames) >= 10, "at least ten distinct guide images required")
    hashes, observations, output_orders = set(), {}, {}
    for fid, frame in frames.items():
        width, height = frame.get("width"), frame.get("height")
        need(type(width) is int and type(height) is int and width > 0 and height > 0, f"{fid}: dimensions")
        digest = frame.get("sha256", "")
        need(isinstance(digest, str) and HEX.fullmatch(digest), f"{fid}: image hash absent")
        record = read_json(repo_file(root, frame.get("record")))
        manifest = read_json(repo_file(root, frame.get("manifest")))
        matches = [e for e in manifest.get("files", []) if e.get("asset") == frame.get("asset")]
        need(len(matches) == 1 and matches[0].get("sha256") == digest and matches[0].get("class") in {"screenshot", "recording"}, f"{fid}: image/manifest mismatch")
        order = [i for i, e in enumerate(record.get("outputs", [])) if e.get("name") == matches[0]["name"] and e.get("sha256") == digest]
        need(len(order) == 1 and record.get("status") == "completed", f"{fid}: image/record mismatch")
        output_orders[fid] = order[0]
        for key in ("record", "manifest"):
            if key + "_sha256" in frame:
                need(hashlib.sha256(repo_file(root, frame[key]).read_bytes()).hexdigest() == frame[key + "_sha256"], f"{fid}: {key} digest mismatch")
        need(digest not in hashes, "duplicate guide image bytes with valid provenance")
        hashes.add(digest)
        substantive(images[fid].get("caption"), f"{fid} caption")
        need(images[fid].get("topics") and all(t in topics for t in images[fid]["topics"]), f"{fid}: image topic")
        for oid, observation in unique(frame.get("observations", []), f"{fid} observations").items():
            need(oid not in observations, "duplicate guide observation")
            substantive(observation.get("text"), oid)
            substantive(observation.get("basis"), f"{oid} basis")
            need(isinstance(observation.get("confidence"), str) and len(observation["confidence"]) >= 3, f"{oid}: confidence")
            region_ok(observation.get("region"), width, height, oid)
            observations[oid] = (fid, observation)
    notes = unique(guide.get("visual_notes", []), "guide visual notes")
    need(set(notes) == set(observations), "guide observations not reconciled")
    for oid, note in notes.items():
        fid, observation = observations[oid]
        need(note.get("frame") == fid and note.get("text") == observation["text"], "stale guide observation")
        need(note.get("source") in sources and sources[note["source"]]["kind"] == "local-visual", "visual note source missing")
    annotations = unique(guide.get("annotations", []), "guide annotations")
    need(set(a.get("observation") for a in annotations.values()) == set(observations), "guide annotations missing observations")
    for aid, annotation in annotations.items():
        oid = annotation.get("observation")
        fid, observation = observations[oid]
        need(annotation.get("frame") == fid, f"{aid}: frame mismatch")
        region_ok(annotation.get("rect"), frames[fid]["width"], frames[fid]["height"], aid)
        need(annotation["rect"] == observation["region"], f"{aid}: stale annotation region")
        need(isinstance(annotation.get("label"), str) and len(annotation["label"]) >= 3, f"{aid}: label missing")
    text = repo_file(root, guide.get("text_path")).read_text()
    for tid, topic in topics.items():
        substantive(topic.get("title"), f"{tid} title")
        for aspect in ASPECTS:
            field = topic.get(aspect, {})
            substantive(field.get("text"), f"{tid}/{aspect}")
            need(field["text"] in text, f"{tid}/{aspect}: prose mismatch")
            basis = field.get("basis")
            need(basis in BASES, f"{tid}/{aspect}: evidence basis")
            refs, limits = field.get("sources", []), field.get("limitation_sources", [])
            need(all(s in sources for s in refs + limits), f"{tid}/{aspect}: missing sources")
            image_refs, obs_refs = field.get("frames", []), field.get("observations", [])
            if basis == "unobserved":
                need(field.get("confidence") == "unknown" and not refs and limits and not image_refs and not obs_refs, "fabricated visual proof for unknown")
            else:
                need(refs, f"{tid}/{aspect}: missing sources")
                if basis == "local-visual":
                    need(field.get("confidence") == "observed-bounded", "visual confidence")
                    need(image_refs and obs_refs and all(f in frames for f in image_refs) and all(o in notes and notes[o]["frame"] in image_refs for o in obs_refs), "visual field lacks observed image evidence")
                    need(any(sources[s]["kind"] == "local-visual" for s in refs), "visual field source missing")
                else:
                    need(not image_refs and not obs_refs, "nonvisual field claims visual proof")
                    need(field.get("confidence") == {"static": "static-bounded", "documented": "documented", "unsupported": "unsupported"}[basis], "nonvisual confidence")
                    need(any(sources[s]["kind"] == ("static" if basis == "unsupported" else basis) for s in refs), "nonvisual source kind mismatch")
    walk = guide.get("walkthrough", {})
    expected = survey.get("walkthrough", {})
    need(walk.get("frames") == expected.get("frames") and walk.get("stages") == expected.get("stages"), "walkthrough differs from surveyed order")
    need(walk.get("stages") == STAGES, "walkthrough lacks placement-to-pass stages")
    need(walk.get("record") == expected.get("record"), "walkthrough record differs from survey")
    ids = walk.get("frames", [])
    need(len(ids) == len(STAGES) and len(set(ids)) == len(ids) and all(f in frames for f in ids), "walkthrough frame references")
    need(all(frames[f]["record"] == walk["record"] for f in ids), "walkthrough provenance mixes records")
    orders = [output_orders[f] for f in ids]
    need(all(a < b for a, b in zip(orders, orders[1:])), "walkthrough provenance order is incoherent")
    need(len({frames[f].get("record_sha256") for f in ids}) == 1, "walkthrough record hash disagreement")
    substantive(walk.get("introduction"), "walkthrough introduction")
    need(walk["introduction"] in text, "walkthrough prose missing")
    steps = walk.get("steps", [])
    need([s.get("frame") for s in steps] == ids, "walkthrough steps do not match frames")
    for step in steps:
        substantive(step.get("text"), "walkthrough step")
        need(step["text"] in text, "walkthrough step prose missing")
    substantive(guide.get("scope"), "guide scope")
    need("unregistered" in guide["scope"] and "#259" in guide["scope"] and "#278" in guide["scope"], "guide build/unknown boundaries missing")
    return f"PASS: {len(topics)} topics × 4 evidence-qualified aspects; {len(images)} distinct images, {len(notes)} observations/annotations; {len(ids)} same-record placement-to-pass steps. Prose/appearance require independent review."


def load(root=ROOT):
    return read_json(root / "manual/pro/guide.json"), read_json(root / "docs/prototypes/T64/visual-source-survey-r1.json")


def synthetic_fixture(root):
    (root / "source.md").write_text("# Synthetic source\nInvented evidence, no original images.\n")
    entries = [{"name": f"{n}.png", "asset": f"{n}.png", "sha256": f"{n:064x}", "class": "recording"} for n in range(1, 12)]
    (root / "record.json").write_text(json.dumps({"status": "completed", "outputs": entries}))
    (root / "manifest.json").write_text(json.dumps({"files": entries}))
    # A second, valid record permits a provenance mutation to reach the same-record rule.
    (root / "other-record.json").write_text(json.dumps({"status": "completed", "outputs": entries}))
    survey = {"frames": [], "walkthrough": {"record": "record.json", "frames": [f"G{n:02}" for n in range(1, 8)], "stages": list(STAGES)}}
    guide = {"schema": "pro-guide/1", "text_path": "guide.md", "scope": "Synthetic unregistered scope only; #259 and #278 remain boundaries.", "sources": [{"id": "S", "path": "source.md", "kind": "static", "scope": "Synthetic static source description."}, {"id": "V", "path": "source.md", "kind": "local-visual", "scope": "Synthetic observation source description."}], "topics": [], "images": [], "visual_notes": [], "annotations": []}
    for n in range(1, 12):
        fid, oid = f"G{n:02}", f"GO{n:02}"
        observation = {"id": oid, "text": "Synthetic own-word visual observation.", "basis": "Synthetic observation, no original scene.", "confidence": "synthetic", "region": [1, 1, 10, 5]}
        survey["frames"].append({"id": fid, "record": "record.json", "manifest": "manifest.json", "asset": f"{n}.png", "sha256": f"{n:064x}", "width": 80, "height": 60, "state": f"Synthetic state {n}", "observations": [observation]})
        guide["images"].append({"id": fid, "caption": "Synthetic image, unrelated to any original game.", "topics": ["placement"]})
        guide["visual_notes"].append({"id": oid, "frame": fid, "text": observation["text"], "source": "V"})
        guide["annotations"].append({"id": f"GA{n}", "frame": fid, "observation": oid, "rect": observation["region"], "label": "Synthetic observed region"})
    for tid in sorted(TOPICS):
        topic = {"id": tid, "title": f"Synthetic topic {tid}"}
        for aspect in ASPECTS:
            topic[aspect] = {"text": f"Synthetic static description of {tid} {aspect}.", "basis": "static", "confidence": "static-bounded", "sources": ["S"]}
        guide["topics"].append(topic)
    guide["topics"][0]["cancel"] = {"text": "Synthetic unobserved cancellation boundary.", "basis": "unobserved", "confidence": "unknown", "sources": [], "limitation_sources": ["S"]}
    guide["walkthrough"] = dict(copy.deepcopy(survey["walkthrough"]), introduction="Synthetic ordered sequence, no original gameplay.", steps=[{"frame": f, "text": f"Synthetic walkthrough step for {f}."} for f in survey["walkthrough"]["frames"]])
    prose = [f["text"] for t in guide["topics"] for f in [t[a] for a in ASPECTS]]
    prose += [guide["walkthrough"]["introduction"]] + [s["text"] for s in guide["walkthrough"]["steps"]]
    (root / "guide.md").write_text("\n".join(prose))
    return guide, survey


def self_test():
    with tempfile.TemporaryDirectory(prefix="T64-guide-controls-", dir="/tmp") as directory:
        root = Path(directory)
        guide, survey = synthetic_fixture(root)
        validate(guide, survey, root)
        controls = [
            ("missing topic", "required topics", lambda g, s: g["topics"].pop()),
            ("missing source", "missing sources", lambda g, s: g["topics"][0]["actions"].update(sources=[])),
            ("stale observation", "stale guide observation", lambda g, s: g["visual_notes"][0].update(text="A stale synthetic visual description.")),
            ("fabricated visual proof for unknown", "fabricated visual proof for unknown", lambda g, s: g["topics"][0]["cancel"].update(frames=["G01"], observations=["GO01"])),
            ("duplicated image with valid provenance", "duplicate guide image", lambda g, s: s["frames"][9].update(asset=s["frames"][10]["asset"], sha256=s["frames"][10]["sha256"])),
            ("mixed valid walkthrough record", "mixes records", lambda g, s: s["frames"][2].update(record="other-record.json")),
            ("changed walkthrough order", "surveyed order", lambda g, s: g["walkthrough"]["frames"].reverse()),
            ("jointly reversed walkthrough provenance", "order is incoherent", lambda g, s: (g["walkthrough"]["frames"].reverse(), s["walkthrough"]["frames"].reverse())),
            ("missing image hash", "image hash absent", lambda g, s: s["frames"][0].pop("sha256")),
            ("out-of-bounds annotation", "invalid annotation bounds", lambda g, s: g["annotations"][0].update(rect=[79, 1, 2, 2])),
        ]
        for label, expected, mutate in controls:
            g, s = copy.deepcopy((guide, survey))
            mutate(g, s)
            try:
                validate(g, s, root)
            except ValueError as error:
                need(expected in str(error), f"{label}: failed for wrong reason: {error}")
                print(f"PASS control: {label} rejected ({error})")
            else:
                raise ValueError(f"control escaped: {label}")
        print(f"PASS: synthetic baseline and {len(controls)} guide negative controls; no originals used.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
        else:
            print(validate(*load()))
    except (ValueError, KeyError, OSError, TypeError, json.JSONDecodeError) as error:
        parser.exit(1, f"FAIL: {error}\n")


if __name__ == "__main__":
    main()
