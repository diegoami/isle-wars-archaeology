#!/usr/bin/env python3
"""Check complete-manual accounting; independent review must judge rules and prose."""
import argparse
import copy
import json
import re
from pathlib import Path
import tempfile
from check_atlas import ROOT, need, read_json, repo_file, substantive, unique
from manual_markdown import render_documents

SECTIONS = {'objective','setup','board','income','turns','combat','capture','movement','cards','trades','bombs','centres','events','ai','endings','persistence','interface','history'}
AREAS = {'board','cards','combat','computer-opponent','hazards','island-bonuses','movement','ownership','production-centres','reinforcement','representation','runtime','seats','setup','starting-state','surrender','turn-sequence','user-interface','victory'}
SCREENS = {'title-options','board-panels','placement','attack-result','capture-dialog','movement-dialog','cards-dialog','turn-pass','events-screen','production-feedback','cancel-confirm','help-scores','concession-victory','save-load','registration','keyboard-disabled','audio-timing'}
UNSEEN = {'capture-dialog','movement-dialog','cards-dialog','events-screen','production-feedback','concession-victory','registration','keyboard-disabled','audio-timing'}
UNKNOWN_BLOCKS = {'board-4','capture-2','bombs-3','events-6','interface-3'}
CONFLICTS = {'mandatory-trade','event-cooldown','island-count','centre-colour'}
CHECKLIST = {'country-readability','topology','active-phase','allocation','combat-feedback','movement-boundary','cards-effects','centre-events','results-persistence','navigation','limits'}
# Derived confidence is conditional on cited source bounds or stated calculation assumptions.
BASES = {'static':'static-bounded','documented':'documented','observed':'observed-bounded','derived':'conditional','unknown':'unknown'}


def load(root=ROOT):
    return read_json(root/'manual/pro/manual.json'), read_json(root/'docs/prototypes/T63/visual-source-survey-r3.json')


def validate(data, survey, root=ROOT):
    need(data.get('schema') == 'pro-manual/1', 'manual schema')
    scope = data.get('scope','')
    need(isinstance(scope,str) and all(t in scope for t in ('unregistered','#259','#278','DOS','#265')), 'manual scope boundaries')
    sources = unique(data.get('sources',[]),'manual sources')
    for sid, src in sources.items():
        path = repo_file(root,src.get('path'))
        need(src.get('kind') in {'static','documented','observed'}, f'{sid}: source kind')
        substantive(src.get('scope'), f'{sid}: source scope')
        if src.get('anchor'):
            slugs = [re.sub(r'[^\w\- ]','', h.lower()).replace(' ','-') for h in re.findall(r'^#+\s+(.+)$', path.read_text(), re.M)]
            need(src['anchor'] in slugs, f'{sid}: source anchor missing')
    sections = unique(data.get('sections',[]),'reference sections')
    need(set(sections) == SECTIONS, 'missing reference topics')
    def refs(values, label):
        need(isinstance(values,list) and values and all(isinstance(v,str) and v in sources for v in values), label+': absent sources')
    def section_refs(values, label):
        need(isinstance(values,list) and values and all(isinstance(v,str) and v in sections for v in values), label+': broken section references')
    blocks = {}
    for sid, section in sections.items():
        substantive(section.get('title'),sid+' title')
        entries = unique(section.get('blocks',[]),sid+' paragraphs')
        need(len(entries)>=2 and sum(len(x.get('text','').split()) for x in entries.values())>=70, sid+': substantive reference missing')
        for bid, block in entries.items():
            need(bid not in blocks,'duplicate reference paragraph')
            blocks[bid] = block
            substantive(block.get('text'),bid)
            need(len(block['text'].split())>=25, bid+': thin reference paragraph')
            basis = block.get('basis')
            need(basis in BASES and block.get('confidence')==BASES[basis], bid+': evidence tier mismatch')
            if basis == 'unknown':
                need(not block.get('sources') and not block.get('frames') and not block.get('observations'), 'unknown promoted to evidence')
                refs(block.get('limitation_sources'),bid+' limitation')
            else:
                refs(block.get('sources'),bid+' support')
                if basis in {'static','documented','observed'}:
                    need(any(sources.get(s,{}).get('kind')==basis for s in block['sources']), bid+': mismatched source tier')
    unknowns = unique(data.get('unknowns',[]),'manual unknowns')
    actual = {bid for bid,b in blocks.items() if b['basis']=='unknown'}
    need(set(unknowns)==actual==UNKNOWN_BLOCKS, 'unknown promotion or missing gap registry')
    for u in unknowns.values():
        need(u.get('status')=='unresolved','unknown status promoted')
        refs(u.get('limitation_sources'),u['id']+' registry limitation')
        section_refs(u.get('sections'),u['id']+' registry')
    subjects = unique(data.get('subjects',[]),'manual subjects')
    expected = unique(survey.get('manual_source',{}).get('subjects',[]),'survey subjects')
    need(set(subjects)==set(expected)=={f'M{n:02}' for n in range(1,16)}, 'missing manual subject coverage')
    for sid,x in subjects.items():
        need(all(x.get(k)==expected[sid].get(k) for k in ('own_word_subject','line_start','line_end')), 'stale manual subject range')
        section_refs(x.get('sections'),sid+' subject')
        refs([x.get('source')],sid+' subject')
        substantive(x.get('boundary'),sid+' boundary')
    areas = unique(data.get('spec_areas',[]),'Pro spec areas')
    need(set(areas)==AREAS,'missing Pro spec coverage')
    for aid,x in areas.items():
        section_refs(x.get('sections'),aid+' spec')
        # Correct path also requires a valid source ID; a separate refs call would
        # duplicate this constraint and mask an omitted call in mutation testing.
        source = sources.get(x.get('source'),{})
        need(source.get('path')=='spec/'+aid+'.md','spec area source mismatch')
        need('Pro' in x.get('scope','') and 'DOS' in x['scope'],'Pro/DOS area boundary missing')
    screens = unique(data.get('screens',[]),'major screens')
    need(set(screens)==SCREENS,'missing major screen coverage')
    for sid,x in screens.items():
        need(x.get('status') in {'recorded','partial','unobserved','unsupported'},'screen evidence state')
        if sid in UNSEEN:
            need(x['status']=='unobserved','unseen screen promoted')
        if sid=='save-load':
            need(x['status']=='unsupported','position save support invented')
        section_refs(x.get('sections'),sid+' screen')
        refs(x.get('sources'),sid+' screen')
        substantive(x.get('boundary'),sid+' screen boundary')
    conflicts = unique(data.get('conflicts',[]),'source discrepancies')
    need(set(conflicts)==CONFLICTS,'missing source conflict')
    for cid,x in conflicts.items():
        need(x.get('status')=='unresolved-source-discrepancy','source discrepancy silently resolved')
        substantive(x.get('statement'),cid)
        refs(x.get('sources'),cid+' conflict')
        section_refs(x.get('sections'),cid+' conflict')
        need(len(x['sources'])>=2,'conflict lacks both sources')
    checklist = unique(data.get('checklist',[]),'planning checklist')
    need(set(checklist)==CHECKLIST,'missing UI/map checklist quality')
    for cid,x in checklist.items():
        for key in ('title','boundary','benefit','scenario'):
            substantive(x.get(key),f'{cid}: checklist {key}')
        for key, minimum in (('benefit',12),('scenario',20)):
            need(len(x[key].split())>=minimum, f'{cid}: checklist {key} missing/thin')
        section_refs(x.get('sections'),cid+' checklist')
        refs(x.get('sources'),cid+' checklist')
        need(x.get('basis')=='derived' and all(t in x['boundary'].lower() for t in ('planning','#191','proposal','implementation')), 'handoff adoption boundary missing')
    # Exact documents supersede every prior substring/span/row presence check.
    # They bind ordering, headings and all content, including unexpected additions.
    for name, canonical in render_documents(data).items():
        document = repo_file(root, 'manual/pro/'+name+'.md').read_text()
        need(document == canonical, name+': complete Markdown mismatch')
    return f'PASS: {len(sections)} substantive sections/{len(blocks)} qualified paragraphs; 15 manual subjects, 19 Pro areas, {len(screens)} screen classes, {len(checklist)} benefit/scenario checklist entries. Structural accounting only; independent semantic/visual review required.'


def synthetic_fixture(root):
    """Invent text/metadata only, with production coverage topology; no original assets."""
    data, survey = copy.deepcopy(load())
    for src in data['sources']:
        path = root/src['path'];path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text('# Synthetic source\nInvented test evidence; not a claim about the game.\n')
        if src.get('anchor'):
            src['anchor'] = 'synthetic-source'
    data['sources'][0]['anchor'] = 'synthetic-source'
    # All paragraphs are invented while keeping lengths, evidence tiers and coverage structure.
    for s in data['sections']:
        for b in s['blocks']:
            b['text'] = ('Synthetic '+b['id']+' paragraph explains an invented rule and its bounded assumptions for a synthetic control only. ')*4
    write_docs(data,root)
    return data,survey


def write_docs(data,root):
    """Write invented fixture witnesses; invalid IDs are rendered, never validated here."""
    path=root/'manual/pro';path.mkdir(parents=True,exist_ok=True)
    for name, document in render_documents(data).items():
        (path/(name+'.md')).write_text(document)


def self_test():
    from manual_controls import run_self_test
    run_self_test(validate, synthetic_fixture, write_docs)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true');a=p.parse_args()
    try:
        if a.self_test:self_test()
        else:print(validate(*load()))
    except (ValueError,KeyError,OSError,TypeError,json.JSONDecodeError) as e:p.exit(1,f'FAIL: {e}\n')

if __name__=='__main__':main()
