"""Complete canonical Markdown editions. Formatting never establishes semantic truth.

Missing reference identifiers get a visible marker so synthetic invalid metadata can
reach its validation guard, rather than being masked by a renderer KeyError.
Production validation rejects those identifiers before rendering these documents.
"""

def text(value):
    return value if isinstance(value, str) else '' if value is None else str(value)


def items(value):
    return value if isinstance(value, list) else []


def source_links(refs, sources):
    links = []
    for sid in items(refs):
        source = sources.get(sid, {}) if isinstance(sid, str) else {}
        path = text(source.get('path', 'missing-source/'+text(sid)))
        anchor = '#'+text(source['anchor']) if source.get('anchor') else ''
        links.append('['+text(sid)+'](../../'+path+anchor+')')
    return ', '.join(links)


def evidence_line(block, sources):
    unknown = block.get('basis') == 'unknown'
    label = 'Limitation sources' if unknown else 'Evidence'
    return label+': '+text(block.get('basis'))+' · '+text(block.get('confidence'))+'; '+source_links(block.get('limitation_sources' if unknown else 'sources'),sources)+'.'


def evidence_span(block, sources):
    return text(block.get('text'))+'\n\n'+evidence_line(block,sources)


def section_links(ids):
    return ', '.join('['+text(sid)+'](reference.md#'+text(sid)+')' for sid in items(ids))


def subject_row(subject):
    return '| '+text(subject.get('id'))+' | '+text(subject.get('own_word_subject'))+' ('+text(subject.get('line_start'))+'–'+text(subject.get('line_end'))+') | '+section_links(subject.get('sections'))+' |'


def spec_row(area, sources):
    return '| '+text(area.get('id'))+' | '+section_links(area.get('sections'))+' | '+source_links([area.get('source')],sources)+' |'


def screen_row(screen):
    return '| '+text(screen.get('title'))+' | '+text(screen.get('status'))+' | '+text(screen.get('boundary'))+' | '+section_links(screen.get('sections'))+' |'


def conflict_bullet(conflict, sources):
    return '- '+text(conflict.get('statement'))+' '+source_links(conflict.get('sources'),sources)+'.'


def render_reference(data):
    sources = {s.get('id'):s for s in data.get('sources',[])}
    out = ['# Isle Wars Pro rules and reference', '', data.get('scope',''), '', 'Read the [player guide](guide.md), [worked turn](guide.md#a-sampled-placement-to-pass-turn), [atlas](atlas.md), [coverage register](coverage.md) and [planning checklist](checklist.md).', '']
    for section in data.get('sections',[]):
        out += ['<a id="'+text(section.get('id'))+'"></a>', '## '+text(section.get('title')), '']
        for block in section.get('blocks',[]):
            out += [text(block.get('text')), '', evidence_line(block,sources), '']
    return '\n'.join(out).rstrip()+'\n'


def render_coverage(data):
    sources = {s.get('id'):s for s in data.get('sources',[])}
    out = ['# Coverage and evidence boundaries', '', 'Coverage means a subject has an explanation or an explicit gap. It does not mean every screen was observed, every static path exercised, or an unknown resolved. Source ranges are paraphrased structure from main’s survey; no original text is reproduced.', '', '## Original-manual subjects', '', '| ID | Subject and source lines | Reference sections |', '| --- | --- | --- |']
    out += [subject_row(x) for x in data.get('subjects',[])]
    out += ['', '## Nineteen Pro spec areas', '', 'Shared files can include DOS rows; those do not support Pro rules. Representation and runtime are covered with their experimental boundaries.', '', '| Area | Reference sections | Source |', '| --- | --- | --- |']
    out += [spec_row(x,sources) for x in data.get('spec_areas',[])]
    out += ['', '## Major screens and feedback', '', '| Area | Evidence state | Boundary | Reference |', '| --- | --- | --- | --- |']
    out += [screen_row(x) for x in data.get('screens',[])]
    out += ['', '## Source discrepancies', '', 'These entries preserve conflicts rather than silently choosing a universal rule. #259 and #278 remain open research; event and trade wording is source-qualified.', '']
    out += [conflict_bullet(x,sources) for x in data.get('conflicts',[])]
    out += ['', 'The machine-readable [manual data](manual.json) holds all section, source, gap, screen and checklist references. Structural checks cannot certify semantic truth; independent review and local visual verification remain required.']
    return '\n'.join(out).rstrip()+'\n'


def render_checklist(data):
    sources = {s.get('id'):s for s in data.get('sources',[])}
    out = ['# UI and map planning checklist', '', 'Research handoff for [malpaco issue #191](https://github.com/diegoami/malpaco/issues/191), planning only after 0.1.x. These are qualities to assess and scenarios to discuss, not a proposed design or authorization to implement. The owner selects and approves a concrete design proposal, then separately authorizes and prioritizes implementation. Original pixels, branding, art and exact presentation remain outside Git and are not transferred.', '']
    for entry in data.get('checklist',[]):
        out += ['<a id="'+text(entry.get('id'))+'"></a>', '## '+text(entry.get('title')), '', 'Player benefit: '+text(entry.get('benefit')), '', 'Observable scenario: '+text(entry.get('scenario')), '', 'Evidence: '+text(entry.get('basis'))+' planning consideration; '+source_links(entry.get('sources'),sources)+'. Reference: '+section_links(entry.get('sections'))+'.', '', text(entry.get('boundary')), '']
    return '\n'.join(out).rstrip()+'\n'


def render_documents(data):
    return {'reference':render_reference(data), 'coverage':render_coverage(data), 'checklist':render_checklist(data)}
