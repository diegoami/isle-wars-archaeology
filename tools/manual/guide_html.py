"""Reader-first guide HTML. Images are supplied by the guarded local renderer."""
from html import escape


def html_guide(guide, survey, names, svg):
    frames = {f["id"]: f for f in survey["frames"]}
    images = {v["id"]: v for v in guide["images"]}
    notes = {n["id"]: n for n in guide["visual_notes"]}
    walk = guide["walkthrough"]
    labels = {"visible": "What you can see", "actions": "What to do", "feedback": "What changes", "cancel": "Back out and confirm"}
    out = ['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
           '<title>Pro player guide and worked turn — local illustrated edition</title>',
           '<style>body{font:18px/1.6 system-ui,sans-serif;margin:auto;max-width:1100px;padding:24px;background:#f5f5f1;color:#202522}h1,h2,h3{line-height:1.2}a{color:#145778}nav{display:flex;gap:8px 18px;flex-wrap:wrap;padding:18px;background:#e7ece9}section{margin-top:42px;scroll-margin-top:16px}svg{display:block;width:100%;height:auto;background:#111}.callout{fill:none;stroke:#ffb600;stroke-width:2;vector-effect:non-scaling-stroke}.number{fill:#fff;stroke:#111;stroke-width:3;paint-order:stroke;font:bold 12px sans-serif}.detail-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px}.detail-grid svg{height:180px}figure{margin:16px 0}figcaption,small,details{font-size:14px}details{padding:10px;background:#e9ede9}summary{cursor:pointer}code{overflow-wrap:anywhere}.boundary{border-left:5px solid #aa6800;padding:12px;background:#fff0ce}.step{border-top:2px solid #becbc4;padding-top:16px}</style>',
           '<h1>Pro player guide and worked turn</h1>', f'<p class="boundary">{escape(guide["scope"])}</p>', '<nav aria-label="Chapters">']
    for topic in guide["topics"]:
        out.append(f'<a href="#topic-{escape(topic["id"])}">{escape(topic["title"])}</a>')
    out += ['<a href="#screens">Screen references</a><a href="#walkthrough">Worked turn</a><a href="atlas.html">Map and UI atlas</a></nav>']
    for topic in guide["topics"]:
        out.append(f'<section id="topic-{escape(topic["id"])}"><h2>{escape(topic["title"])}</h2>')
        for aspect, label in labels.items():
            field = topic[aspect]
            refs = field.get("sources", []) or field.get("limitation_sources", [])
            links = ', '.join(f'<a href="#source-{escape(s)}">{escape(s)}</a>' for s in refs)
            out.append(f'<p><strong>{label}.</strong> {escape(field["text"])}</p><details><summary>Evidence: {escape(field["basis"])} · {escape(field["confidence"])}</summary><p>{links}</p></details>')
        relevant = [v["id"] for v in guide["images"] if topic["id"] in v["topics"]]
        if relevant:
            out.append('<p>Illustrations: ' + ' · '.join(f'<a href="#{fid}">{fid}</a>' for fid in relevant) + '</p>')
        out.append('<p><a href="#">Back to chapters</a></p></section>')

    def illustration(fid):
        frame, image = frames[fid], images[fid]
        annotations = [a for a in guide["annotations"] if a["frame"] == fid]
        result = [f'<h3>{escape(fid)} · {escape(frame["state"])}</h3><p>{escape(image["caption"])}</p><figure>', svg(names[fid], frame, annotations),
                  f'<figcaption>Unchanged native {frame["width"]} × {frame["height"]} source. SHA-256 <code>{frame["sha256"]}</code>.</figcaption></figure><details><summary>Observed regions and limits</summary><ol>']
        for a in annotations:
            note = notes[a["observation"]]
            result.append(f'<li><strong>{escape(a["label"])}</strong> {escape(note["text"])}</li>')
        result.append('</ol></details><div class="detail-grid">')
        for a in annotations:
            result += ['<figure>', svg(names[fid], frame, [], a["rect"]), f'<figcaption>{escape(a["label"])}; native rectangle {escape(str(a["rect"]))}, explicitly clipped. Approximate observation region, never a hitbox.</figcaption></figure>']
        result.append('</div><p><a href="#">Back to chapters</a> · <a href="#walkthrough">Worked turn</a> · <a href="atlas.html">Atlas</a></p>')
        return result

    out.append('<h2 id="screens">Screen references</h2><p>Setup/navigation pictures come from another record than the worked turn; they are not the setup of that deal. No missing screen is reconstructed.</p>')
    for fid in images:
        if fid not in walk["frames"]:
            out.append(f'<section id="{escape(fid)}">')
            out += illustration(fid)
            out.append('</section>')
    out += ['<section id="walkthrough"><h2>A sampled placement-to-pass turn</h2>', f'<p>{escape(walk["introduction"])}</p><nav aria-label="Worked turn steps">']
    out += [f'<a href="#{escape(fid)}">Step {i}</a>' for i, fid in enumerate(walk["frames"], 1)]
    out.append('</nav>')
    for i, step in enumerate(walk["steps"], 1):
        out.append(f'<section id="{escape(step["frame"])}" class="step"><h3>Step {i}</h3><p>{escape(step["text"])}</p>')
        out += illustration(step["frame"])
        out.append('</section>')
    out.append('</section><section id="provenance"><h2>Source directory and limits</h2><ul>')
    for source in guide["sources"]:
        out.append(f'<li id="source-{escape(source["id"])}"><strong>{escape(source["id"])}</strong> <code>{escape(source["path"])}{escape("#"+source["anchor"] if source.get("anchor") else "")}</code> — {escape(source["scope"])}</li>')
    out.append('</ul>')
    for limitation in survey.get("limitations", []) + walk.get("limitations", []):
        out.append(f'<p>{escape(limitation)}</p>')
    out.append('</section></html>')
    return '\n'.join(out)
