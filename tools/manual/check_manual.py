#!/usr/bin/env python3
"""Check complete-manual accounting; independent review must judge rules and prose."""
import argparse
import copy
import json
from pathlib import Path
import tempfile
from check_atlas import ROOT, need, read_json, repo_file, substantive, unique

SECTIONS = {'objective','setup','board','income','turns','combat','capture','movement','cards','trades','bombs','centres','events','ai','endings','persistence','interface','history'}
AREAS = {'board','cards','combat','computer-opponent','hazards','island-bonuses','movement','ownership','production-centres','reinforcement','representation','runtime','seats','setup','starting-state','surrender','turn-sequence','user-interface','victory'}
SCREENS = {'title-options','board-panels','placement','attack-result','capture-dialog','movement-dialog','cards-dialog','turn-pass','events-screen','production-feedback','cancel-confirm','help-scores','concession-victory','save-load','registration','keyboard-disabled','audio-timing'}
UNSEEN = {'capture-dialog','movement-dialog','cards-dialog','events-screen','production-feedback','concession-victory','registration','keyboard-disabled','audio-timing'}
UNKNOWN_BLOCKS = {'board-4','capture-2','bombs-3','events-6','interface-3'}
CONFLICTS = {'mandatory-trade','event-cooldown','island-count','centre-colour'}
CHECKLIST = {'country-readability','topology','active-phase','allocation','combat-feedback','movement-boundary','cards-effects','centre-events','results-persistence','navigation','limits'}
BASES = {'static':'static-bounded','documented':'documented','observed':'observed-bounded','derived':'conditional','unknown':'unknown'}


def load(root=ROOT):
    return read_json(root/'manual/pro/manual.json'), read_json(root/'docs/prototypes/T63/visual-source-survey-r3.json')


def validate(data, survey, root=ROOT):
    need(data.get('schema') == 'pro-manual/1', 'manual schema')
    scope = data.get('scope','')
    need(all(t in scope for t in ('unregistered','#259','#278','DOS','#265')), 'manual scope boundaries')
    sources = unique(data.get('sources',[]),'manual sources')
    for sid, src in sources.items():
        path = repo_file(root,src.get('path'))
        need(src.get('kind') in {'static','documented','observed'}, f'{sid}: source kind')
        substantive(src.get('scope'), f'{sid}: source scope')
        if src.get('anchor'):
            import re
            slugs = [re.sub(r'[^\w\- ]','', h.lower()).replace(' ','-') for h in re.findall(r'^#+\s+(.+)$', path.read_text(), re.M)]
            need(src['anchor'] in slugs, f'{sid}: source anchor missing')
    docs = {name: repo_file(root, 'manual/pro/'+name+'.md').read_text() for name in ('reference','coverage','checklist')}
    sections = unique(data.get('sections',[]),'reference sections')
    need(set(sections) == SECTIONS, 'missing reference topics')
    def refs(values, label):
        need(isinstance(values,list) and values and all(v in sources for v in values), label+': absent sources')
    def section_refs(values):
        need(isinstance(values,list) and values and all(v in sections for v in values), 'broken section references')
    blocks = {}
    for sid, section in sections.items():
        substantive(section.get('title'),sid+' title')
        need('<a id="'+sid+'"></a>' in docs['reference'], 'reference section anchor missing')
        entries = unique(section.get('blocks',[]),sid+' paragraphs')
        need(len(entries)>=2 and sum(len(x.get('text','').split()) for x in entries.values())>=70, sid+': substantive reference missing')
        for bid, block in entries.items():
            need(bid not in blocks,'duplicate reference paragraph')
            blocks[bid] = block
            substantive(block.get('text'),bid)
            need(len(block['text'].split())>=25, bid+': thin reference paragraph')
            need(block['text'] in docs['reference'], bid+': reference prose mismatch')
            basis = block.get('basis')
            need(basis in BASES and block.get('confidence')==BASES[basis], bid+': evidence tier mismatch')
            if basis == 'unknown':
                need(not block.get('sources') and not block.get('frames') and not block.get('observations'), 'unknown promoted to evidence')
                refs(block.get('limitation_sources'),bid)
            else:
                refs(block.get('sources'),bid)
                if basis in {'static','documented','observed'}:
                    need(any(sources[s]['kind']==basis for s in block['sources']), bid+': mismatched source tier')
    unknowns = unique(data.get('unknowns',[]),'manual unknowns')
    actual = {bid for bid,b in blocks.items() if b['basis']=='unknown'}
    need(set(unknowns)==actual==UNKNOWN_BLOCKS, 'unknown promotion or missing gap registry')
    for u in unknowns.values():
        need(u.get('status')=='unresolved','unknown status promoted')
        refs(u.get('limitation_sources'),u['id'])
        section_refs(u.get('sections'))
    subjects = unique(data.get('subjects',[]),'manual subjects')
    expected = unique(survey.get('manual_source',{}).get('subjects',[]),'survey subjects')
    need(set(subjects)==set(expected)=={f'M{n:02}' for n in range(1,16)}, 'missing manual subject coverage')
    for sid,x in subjects.items():
        need(all(x.get(k)==expected[sid].get(k) for k in ('own_word_subject','line_start','line_end')), 'stale manual subject range')
        section_refs(x.get('sections')); refs([x.get('source')],sid)
        substantive(x.get('boundary'),sid+' boundary')
        need(sid in docs['coverage'] and x['own_word_subject'] in docs['coverage'], 'subject prose coverage missing')
    areas = unique(data.get('spec_areas',[]),'Pro spec areas')
    need(set(areas)==AREAS,'missing Pro spec coverage')
    for aid,x in areas.items():
        section_refs(x.get('sections')); refs([x.get('source')],aid)
        need(sources[x['source']]['path']=='spec/'+aid+'.md','spec area source mismatch')
        need('Pro' in x.get('scope','') and 'DOS' in x['scope'],'Pro/DOS area boundary missing')
        need(aid in docs['coverage'],'spec prose coverage missing')
    screens = unique(data.get('screens',[]),'major screens')
    need(set(screens)==SCREENS,'missing major screen coverage')
    for sid,x in screens.items():
        need(x.get('status') in {'recorded','partial','unobserved','unsupported'},'screen evidence state')
        if sid in UNSEEN:
            need(x['status']=='unobserved','unseen screen promoted')
        if sid=='save-load':
            need(x['status']=='unsupported','position save support invented')
        section_refs(x.get('sections')); refs(x.get('sources'),sid)
        substantive(x.get('boundary'),sid+' screen boundary')
        need(x['boundary'] in docs['coverage'],'screen prose coverage missing')
    conflicts = unique(data.get('conflicts',[]),'source discrepancies')
    need(set(conflicts)==CONFLICTS,'missing source conflict')
    for cid,x in conflicts.items():
        need(x.get('status')=='unresolved-source-discrepancy','source discrepancy silently resolved')
        substantive(x.get('statement'),cid)
        refs(x.get('sources'),cid);section_refs(x.get('sections'))
        need(len(x['sources'])>=2,'conflict lacks both sources')
        need(x['statement'] in docs['coverage'],'conflict prose missing')
    checklist = unique(data.get('checklist',[]),'planning checklist')
    need(set(checklist)==CHECKLIST,'missing UI/map checklist quality')
    for cid,x in checklist.items():
        for key in ('title','boundary'):
            substantive(x.get(key),f'{cid}: checklist {key}')
            need(x[key] in docs['checklist'], f'{cid}: checklist prose mismatch')
        for key, minimum in (('benefit',12),('scenario',20)):
            need(isinstance(x.get(key),str) and len(x[key].split())>=minimum, f'{cid}: checklist {key} missing/thin')
            need(x[key] in docs['checklist'], f'{cid}: checklist prose mismatch')
        section_refs(x.get('sections'));refs(x.get('sources'),cid)
        need(x.get('basis')=='derived' and all(t in x['boundary'].lower() for t in ('planning','#191','proposal','implementation')), 'handoff adoption boundary missing')
    return f'PASS: {len(sections)} substantive sections/{len(blocks)} qualified paragraphs; 15 manual subjects, 19 Pro areas, {len(screens)} screen classes, {len(checklist)} benefit/scenario checklist entries. Structural accounting only; independent semantic/visual review required.'


def synthetic_fixture(root):
    """Invent text/metadata only, with production coverage topology; no original assets."""
    data, survey = copy.deepcopy(load())
    for src in data['sources']:
        path = root/src['path'];path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text('# Synthetic source\nInvented test evidence; not a claim about the game.\n')
    # All paragraphs are invented while keeping lengths, evidence tiers and coverage structure.
    for s in data['sections']:
        for b in s['blocks']:
            b['text'] = ('Synthetic '+b['id']+' paragraph explains an invented rule and its bounded assumptions for a synthetic control only. ')*4
    write_docs(data,root)
    return data,survey


def write_docs(data,root):
    """Fixture-only text witness, deliberately separate from production document authoring."""
    path=root/'manual/pro';path.mkdir(parents=True,exist_ok=True)
    (path/'reference.md').write_text('\n'.join('<a id="'+s['id']+'"></a>\n'+'\n'.join(b['text'] for b in s['blocks']) for s in data['sections']))
    (path/'coverage.md').write_text('\n'.join([x['id']+' '+x['own_word_subject'] for x in data['subjects']]+[x['id'] for x in data['spec_areas']]+[x['boundary'] for x in data['screens']]+[x['statement'] for x in data['conflicts']]))
    (path/'checklist.md').write_text('\n'.join(x[k] for x in data['checklist'] for k in ('title','benefit','scenario','boundary')))


def self_test():
    with tempfile.TemporaryDirectory(prefix='T65-manual-controls-',dir='/tmp') as d:
        root=Path(d);data,survey=synthetic_fixture(root)
        validate(data,survey,root)
        controls=[
            ('missing reference topic','missing reference topics',lambda x:x['sections'].pop()),
            ('thin reference','substantive reference missing',lambda x:x['sections'][0].update(blocks=x['sections'][0]['blocks'][:1])),
            ('absent sources','absent sources',lambda x:x['sections'][0]['blocks'][0].update(sources=[])),
            ('unknown visual proof','unknown promoted',lambda x:next(b for s in x['sections'] for b in s['blocks'] if b['basis']=='unknown').update(sources=['V3'],frames=['V06'])),
            ('unknown tier promotion','unknown promotion',lambda x:next(b for s in x['sections'] for b in s['blocks'] if b['basis']=='unknown').update(basis='observed',confidence='observed-bounded',sources=['V3'])),
            ('missing manual subject','manual subject coverage',lambda x:x['subjects'].pop()),
            ('stale subject range','stale manual subject',lambda x:x['subjects'][0].update(line_end=999)),
            ('missing Pro area','Pro spec coverage',lambda x:x['spec_areas'].pop()),
            ('broken section reference','broken section references',lambda x:x['spec_areas'][0].update(sections=['missing-section'])),
            ('missing major screen','major screen coverage',lambda x:x['screens'].pop()),
            ('unseen screen promoted','unseen screen promoted',lambda x:next(v for v in x['screens'] if v['id']=='events-screen').update(status='recorded')),
            ('missing source conflict','source conflict',lambda x:x['conflicts'].pop()),
            ('silent conflict resolution','silently resolved',lambda x:x['conflicts'][0].update(status='resolved')),
            ('missing checklist benefit','checklist benefit',lambda x:x['checklist'][0].pop('benefit')),
            ('missing checklist scenario','checklist scenario',lambda x:x['checklist'][0].pop('scenario')),
            ('adoption asserted','handoff adoption boundary',lambda x:x['checklist'][0].update(basis='observed')),
            ('mismatched evidence tier','evidence tier mismatch',lambda x:x['sections'][0]['blocks'][0].update(confidence='observed-bounded')),
            ('untracked prose change','reference prose mismatch',lambda x:x['sections'][0]['blocks'][0].update(text='Synthetic changed paragraph absent from the witness document, long enough to be substantive and distinct, but never supported by the stored own-word reference paragraph in this fixture.')),
        ]
        for label,expected,mutate in controls:
            x=copy.deepcopy(data);mutate(x)
            try:validate(x,survey,root)
            except ValueError as error:
                need(expected in str(error),f'{label}: wrong refusal: {error}')
                print(f'PASS control: {label} rejected ({error})')
            else:raise ValueError('control escaped: '+label)
        print(f'PASS: synthetic baseline and {len(controls)} manual negative controls; no originals used.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true');a=p.parse_args()
    try:
        if a.self_test:self_test()
        else:print(validate(*load()))
    except (ValueError,KeyError,OSError,TypeError,json.JSONDecodeError) as e:p.exit(1,f'FAIL: {e}\n')

if __name__=='__main__':main()
