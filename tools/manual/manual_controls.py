"""Synthetic semantic and whole-document controls, independent literal corruptions."""
import copy
from pathlib import Path
import tempfile
from check_atlas import need


def controls(data):
    cases = []
    def add(label, expected, change):
        cases.append((label, expected, lambda d,s,r: change(d)))
    def block(d): return d['sections'][0]['blocks'][0]
    def derived(d): return d['sections'][0]['blocks'][1]
    def unknown(d): return next(b for sec in d['sections'] for b in sec['blocks'] if b['basis']=='unknown')
    def screen(d, sid): return next(x for x in d['screens'] if x['id']==sid)
    add('wrong schema','manual schema',lambda d:d.update(schema='invented/0'))
    for token in ('unregistered','#259','#278','DOS','#265'):
        add('scope lacks '+token,'manual scope boundaries',lambda d,t=token:d.update(scope=d['scope'].replace(t,'')))
    add('invalid source kind','source kind',lambda d:next(s for s in d['sources'] if s['id']=='S-board').update(kind='invalid'))
    add('source scope absent','source scope',lambda d:d['sources'][0].update(scope=''))
    add('source scope filler','placeholder',lambda d:d['sources'][0].update(scope='TODO synthetic source scope description.'))
    add('invalid source anchor','source anchor missing',lambda d:d['sources'][0].update(anchor='missing-synthetic-heading'))
    add('source file missing','missing repository source',lambda d:next(s for s in d['sources'] if s['id']=='F020').update(path='missing-source.md'))
    add('source path escapes root','missing repository source',lambda d:next(s for s in d['sources'] if s['id']=='F020').update(path='../outside.md'))
    def missing_topic(d):
        d['sections']=[sec for sec in d['sections'] if sec['id']!='history']
        for key in ('unknowns','subjects','spec_areas','screens','conflicts','checklist'):
            for entry in d[key]:
                entry['sections']=['objective' if sid=='history' else sid for sid in entry['sections']]
    add('coherent missing reference topic','missing reference topics',missing_topic)
    add('section title absent','title: absent prose',lambda d:d['sections'][0].update(title=''))
    add('section title filler','placeholder',lambda d:d['sections'][0].update(title='TODO synthetic reference title.'))
    add('single paragraph section','substantive reference missing',lambda d:d['sections'][0].update(blocks=d['sections'][0]['blocks'][:1]))
    def short_section(d):
        d['sections'][0]['blocks']=d['sections'][0]['blocks'][:2]
        for b in d['sections'][0]['blocks']:
            b['text']=' '.join(['Synthetic']*30)
    add('section below seventy words','substantive reference missing',short_section)
    add('paragraph ID repeated across sections','duplicate reference paragraph',lambda d:d['sections'][1]['blocks'][0].update(id=d['sections'][0]['blocks'][0]['id']))
    add('paragraph filler with enough words','placeholder',lambda d:block(d).update(text='TODO '+' '.join(['synthetic']*30)))
    add('thin individual paragraph','thin reference paragraph',lambda d:block(d).update(text='This invented paragraph is substantive text but contains fewer than twenty five words, so the individual word minimum must reject it.'))
    add('invalid evidence basis','evidence tier mismatch',lambda d:block(d).update(basis='invented'))
    add('invalid evidence confidence','evidence tier mismatch',lambda d:block(d).update(confidence='observed-bounded'))
    for key,value in [('sources',['V3']),('frames',['V06']),('observations',['O17'])]:
        add('unknown claims '+key,'unknown promoted to evidence',lambda d,k=key,v=value:unknown(d).update({k:v}))
    for label,values in [('absent',[]),('invalid',['missing-source'])]:
        add('unknown block '+label+' limitation refs','limitation: absent sources',lambda d,v=values:unknown(d).update(limitation_sources=v))
        add('known block '+label+' support refs','support: absent sources',lambda d,v=values:derived(d).update(sources=v))
        add('unknown registry '+label+' limitation refs','registry limitation: absent sources',lambda d,v=values:d['unknowns'][0].update(limitation_sources=v))
    add('static source tier mismatch','mismatched source tier',lambda d:block(d).update(sources=['V3']))
    add('missing unknown registry entry','unknown promotion or missing gap registry',lambda d:d['unknowns'].pop())
    add('unknown registry resolved','unknown status promoted',lambda d:d['unknowns'][0].update(status='resolved'))
    add('unknown tier promotion','unknown promotion or missing gap registry',lambda d:unknown(d).update(basis='derived',confidence='conditional',sources=['V3']))
    add('missing manual subject','missing manual subject coverage',lambda d:d['subjects'].pop())
    add('stale subject range','stale manual subject range',lambda d:d['subjects'][0].update(line_end=999))
    add('subject boundary absent','boundary: absent prose',lambda d:d['subjects'][0].update(boundary=''))
    add('subject boundary filler','placeholder',lambda d:d['subjects'][0].update(boundary='TODO synthetic subject boundary.'))
    add('missing Pro area','missing Pro spec coverage',lambda d:d['spec_areas'].pop())
    add('wrong valid spec source','spec area source mismatch',lambda d:d['spec_areas'][0].update(source='S-cards'))
    add('absent spec source','spec area source mismatch',lambda d:d['spec_areas'][0].update(source=None))
    add('invalid spec source','spec area source mismatch',lambda d:d['spec_areas'][0].update(source='missing-source'))
    for token in ('Pro','DOS'):
        add('spec scope lacks '+token,'Pro/DOS area boundary missing',lambda d,t=token:d['spec_areas'][0].update(scope=d['spec_areas'][0]['scope'].replace(t,'')))
    add('missing major screen','missing major screen coverage',lambda d:d['screens'].pop())
    add('invalid screen evidence enum','screen evidence state',lambda d:d['screens'][0].update(status='invented'))
    add('unseen event recorded','unseen screen promoted',lambda d:screen(d,'events-screen').update(status='recorded'))
    add('position save invented','position save support invented',lambda d:screen(d,'save-load').update(status='recorded'))
    add('screen boundary absent','screen boundary: absent prose',lambda d:d['screens'][0].update(boundary=''))
    add('screen boundary filler','placeholder',lambda d:d['screens'][0].update(boundary='TODO synthetic screen boundary.'))
    add('missing conflict','missing source conflict',lambda d:d['conflicts'].pop())
    add('conflict status resolved','silently resolved',lambda d:d['conflicts'][0].update(status='resolved'))
    add('conflict statement absent','absent prose',lambda d:d['conflicts'][0].update(statement=''))
    add('conflict statement filler','placeholder',lambda d:d['conflicts'][0].update(statement='TODO synthetic conflict description.'))
    add('conflict has one source','conflict lacks both sources',lambda d:d['conflicts'][0].update(sources=['T04']))
    add('missing checklist quality','missing UI/map checklist quality',lambda d:d['checklist'].pop())
    for key in ('title','boundary','benefit','scenario'):
        add('checklist '+key+' absent','checklist '+key+': absent prose',lambda d,k=key:d['checklist'][0].update({k:''}))
        # Enough words and all adoption terms retain every other constraint.
        add('checklist '+key+' filler','placeholder',lambda d,k=key:d['checklist'][0].update({k:'TODO planning #191 proposal implementation '+' '.join(['synthetic']*30)}))
    for key in ('benefit','scenario'):
        add('checklist '+key+' thin','checklist '+key+' missing/thin',lambda d,k=key:d['checklist'][0].update({k:'Synthetic text with too few words for this field.'}))
    add('checklist adoption asserted','handoff adoption boundary missing',lambda d:d['checklist'][0].update(basis='observed'))
    for token in ('planning','#191','proposal','implementation'):
        add('checklist boundary lacks '+token,'handoff adoption boundary missing',lambda d,t=token:d['checklist'][0].update(boundary=d['checklist'][0]['boundary'].lower().replace(t,'')))
    # Every refs/section_refs call site gets independently synchronized bad metadata.
    domains=[('registry',lambda d:d['unknowns'][0]),('subject',lambda d:d['subjects'][0]),('spec',lambda d:d['spec_areas'][0]),('screen',lambda d:d['screens'][0]),('conflict',lambda d:d['conflicts'][0]),('checklist',lambda d:d['checklist'][0])]
    for name,pick in domains:
        for label,values in [('absent',[]),('invalid',['missing-section'])]:
            add(name+' '+label+' section refs',name+': broken section references',lambda d,p=pick,v=values:p(d).update(sections=v))
    for name,pick in [('subject',lambda d:d['subjects'][0]),('screen',lambda d:d['screens'][0]),('conflict',lambda d:d['conflicts'][0]),('checklist',lambda d:d['checklist'][0])]:
        for label,values in [('absent',[]),('invalid',['missing-source','GUIDE'])]:
            if name=='subject':
                add(name+' '+label+' source',name+': absent sources',lambda d,v=values: d['subjects'][0].update(source=v[0] if v else None))
            else:
                add(name+' '+label+' sources',name+': absent sources',lambda d,p=pick,v=values:p(d).update(sources=v))
    # Shared unique() protects every collection against duplicates, not just its set.
    for key in ('sources','sections','unknowns','subjects','spec_areas','screens','conflicts','checklist'):
        add('duplicate '+key,'missing/duplicate ID',lambda d,k=key:d[k].append(copy.deepcopy(d[k][0])))
    add('duplicate paragraph in section','missing/duplicate ID',lambda d:d['sections'][0]['blocks'].append(copy.deepcopy(d['sections'][0]['blocks'][0])))
    cases.append(('duplicate surveyed subject','missing/duplicate ID',lambda d,s,r:s['manual_source']['subjects'].append(copy.deepcopy(s['manual_source']['subjects'][0]))))
    return cases


def markdown_controls(data):
    cases=[]
    def edit(name, old, new):
        def mutate(d,s,root):
            p=root/'manual/pro'/(name+'.md');content=p.read_text()
            need(content.count(old)==1,'ambiguous literal Markdown mutation')
            p.write_text(content.replace(old,new))
        return mutate
    def add(label,name,old,new):cases.append((label,name+': complete Markdown mismatch',edit(name,old,new)))
    add('added unknown/conflict-resolving claim','reference','<a id="trades"></a>', 'The trade conflict is resolved and registered screens were observed.\n\nEvidence: observed · observed-bounded; [V3](../../docs/prototypes/T63/visual-source-survey-r3.json).\n\n<a id="trades"></a>')
    add('duplicate capture row recorded','coverage','| Capture and split dialogue | unobserved |', '| Capture and split dialogue | recorded | Added unsupported proof | [capture](reference.md#capture) |\n| Capture and split dialogue | unobserved |')
    for area in ('board','cards'):
        def remove(d,s,root,a=area):
            p=root/'manual/pro/coverage.md';lines=p.read_text().splitlines(True)
            matches=[line for line in lines if line.startswith('| '+a+' |')];need(len(matches)==1,'missing literal spec row')
            p.write_text(''.join(line for line in lines if line!=matches[0]))
        cases.append(('deleted '+area+' spec row','coverage: complete Markdown mismatch',remove))
    # Prefix only the first line, with an independent literal rather than a renderer helper.
    def prefix(d,s,root):
        p=root/'manual/pro/checklist.md';v=p.read_text();need('Player benefit: ' in v,'missing benefit literal');p.write_text(v.replace('Player benefit: ','Player benefit: DOS ONLY. ',1))
    cases.append(('checklist benefit prefix','checklist: complete Markdown mismatch',prefix))
    for key,literal in [('title','## Readable country identity and ownership'),('boundary','Planning input only for malpaco #191 after 0.1.x; owner approves proposal and separately authorizes implementation. No original assets or exact presentation transfer.'),('scenario','Observable scenario: ')]:
        def prefix_field(d,s,root,v=literal):
            p=root/'manual/pro/checklist.md';doc=p.read_text();need(v in doc,'missing checklist literal');p.write_text(doc.replace(v,'UNSUPPORTED. '+v,1))
        cases.append(('checklist '+key+' drift','checklist: complete Markdown mismatch',prefix_field))
    def moved(d,s,root):
        p=root/'manual/pro/reference.md';doc=p.read_text();start=doc.index('Synthetic objective-1 paragraph');end=doc.index('\n\n',doc.index('\n\n',start)+2)
        span=doc[start:end];doc=doc[:start]+doc[end:];needle='<a id="setup"></a>';need(doc.count(needle)==1,'missing setup literal');p.write_text(doc.replace(needle,needle+'\n\n'+span))
    cases.append(('paragraph moved to wrong section','reference: complete Markdown mismatch',moved))
    add('missing reference heading','reference','## Aim and how to read this book','## Unsupported replacement heading')
    add('missing reference anchor','reference','<a id="objective"></a>','')
    def unknown_line(d,s,root):
        p=root/'manual/pro/reference.md';doc=p.read_text();needle='Limitation sources: unknown · unknown;';need(needle in doc,'unknown literal missing');p.write_text(doc.replace(needle,'Evidence: observed · observed-bounded;',1))
    cases.append(('unknown evidence promotion','reference: complete Markdown mismatch',unknown_line))
    add('subject range drift','coverage','(51–92)','(51–60)')
    add('conflict resolved prefix','coverage','- T04 mandatory-trade wording differs','- RESOLVED: trades are optional. T04 mandatory-trade wording differs')
    def registration(d,s,root):
        p=root/'manual/pro/coverage.md';v=p.read_text();needle='| Registration and unlocked controls | unobserved |';need(v.count(needle)==1,'registration literal missing');p.write_text(v.replace(needle,needle.replace('unobserved','recorded')))
    cases.append(('registration status drift','coverage: complete Markdown mismatch',registration))
    return cases


def run_self_test(validate, fixture, write_docs):
    with tempfile.TemporaryDirectory(prefix='T65-manual-controls-',dir='/tmp') as directory:
        root=Path(directory);data,survey=fixture(root);validate(data,survey,root)
        cases=[(label,expected,change,True) for label,expected,change in controls(data)]+[(label,expected,change,False) for label,expected,change in markdown_controls(data)]
        failures=[];escaped=[]
        for label,expected,change,sync in cases:
            d,s=copy.deepcopy((data,survey));write_docs(data,root)
            try:
                change(d,s,root)
                if sync:write_docs(d,root)
                validate(d,s,root)
            except ValueError as error:
                if expected in str(error):print(f'PASS control: {label} rejected ({error})')
                else:failures.append(label+': wrong refusal: '+str(error))
            except (KeyError,TypeError,OSError) as error:
                failures.append(label+': masked by '+type(error).__name__+': '+str(error))
            else:escaped.append(label)
        for failure in failures:print('FAIL control: '+failure)
        for label in escaped:print('FAIL control escaped: '+label)
        need(not escaped,'control escaped: '+', '.join(escaped))
        need(not failures,'control masking/wrong refusal: '+'; '.join(failures))
        print(f'PASS: synthetic baseline and {len(cases)} manual negative controls; no originals used.')
