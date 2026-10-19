"""Own-word reference/coverage/checklist pages; no original assets or new artwork."""
from html import escape as e

NAV = '<nav aria-label="Book chapters"><a href="index.html">Contents</a><a href="guide.html">Player guide</a><a href="guide.html#walkthrough">Worked turn</a><a href="atlas.html">Map/UI atlas</a><a href="reference.html">Rules/reference</a><a href="coverage.html">Coverage and gaps</a><a href="checklist.html">Planning checklist</a></nav>'
STYLE = 'body{font:18px/1.65 system-ui,sans-serif;max-width:1050px;margin:auto;padding:24px;background:#f5f5f1;color:#202522}h1,h2,h3{line-height:1.2}a{color:#145778}nav{display:flex;flex-wrap:wrap;gap:8px 18px;background:#e7ece9;padding:16px}section{margin-top:40px;scroll-margin-top:16px}details,small{font-size:14px}details{padding:10px;background:#e9ede9}summary{cursor:pointer}code{overflow-wrap:anywhere}.boundary{border-left:5px solid #aa6800;padding:12px;background:#fff0ce}li{margin-bottom:12px}'


def page(title, body):
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+e(title)+'</title><style>'+STYLE+'</style>'+NAV+'<h1>'+e(title)+'</h1>'+body+'</html>'


def section_links(ids):
    return ' · '.join('<a href="reference.html#'+e(i)+'">'+e(i)+'</a>' for i in ids)


def evidence(refs):
    return ', '.join('<a href="#source-'+e(s)+'">'+e(s)+'</a>' for s in refs)


def sources(data):
    return '<section id="sources"><h2>Sources and scope</h2><p>Repository source paths are provenance identifiers, not links to local original files.</p><ul>'+''.join('<li id="source-'+e(s['id'])+'"><strong>'+e(s['id'])+'</strong> <code>'+e(s['path'])+'</code> — '+e(s['scope'])+'</li>' for s in data['sources'])+'</ul></section>'


def book_pages(data):
    toc='<p class="boundary">'+e(data['scope'])+'</p><p>Begin with the player guide for controls, follow the sampled turn for a recorded sequence, and use the reference for rules and exceptions. The atlas explains the visible map. Coverage lists evidence gaps; the checklist is planning input only.</p>'+NAV
    toc+='<h2>Rules at a glance</h2><ol>'+''.join('<li><a href="reference.html#'+e(s['id'])+'">'+e(s['title'])+'</a></li>' for s in data['sections'])+'</ol><p>No original images are embedded in repository files. This local edition reuses the unchanged, hash-verified images only outside every checkout.</p>'
    ref='<p class="boundary">'+e(data['scope'])+'</p><nav aria-label="Reference sections">'+''.join('<a href="#'+e(s['id'])+'">'+e(s['title'])+'</a>' for s in data['sections'])+'</nav>'
    for s in data['sections']:
        ref+='<section id="'+e(s['id'])+'"><h2>'+e(s['title'])+'</h2>'
        for b in s['blocks']:
            ref+='<p>'+e(b['text'])+'</p><details><summary>Evidence: '+e(b['basis'])+' · '+e(b['confidence'])+'</summary><p>'+evidence(b.get('sources',b.get('limitation_sources',[])))+'</p></details>'
        ref+='<p><a href="index.html">Contents</a> · <a href="#">Reference sections</a></p></section>'
    checklist='<p class="boundary">Planning only after 0.1.x for <a href="https://github.com/diegoami/malpaco/issues/191">malpaco #191</a>. Owner selection/approval of a concrete design proposal and separately authorized/prioritized implementation are required. No adoption or original asset transfer is implied.</p>'
    for x in data['checklist']:
        checklist+='<section id="'+e(x['id'])+'"><h2>'+e(x['title'])+'</h2><p><strong>Player benefit.</strong> '+e(x['benefit'])+'</p><p><strong>Observable scenario.</strong> '+e(x['scenario'])+'</p><p>'+section_links(x['sections'])+'</p><details><summary>Derived planning input and evidence</summary><p>'+evidence(x['sources'])+'</p><p>'+e(x['boundary'])+'</p></details></section>'
    coverage='<p>Coverage means a substantive explanation or an explicit gap, not that every path was observed or every unknown resolved.</p><h2 id="manual-subjects">Fifteen manual subjects</h2><ul>'
    for x in data['subjects']:
        coverage+='<li id="'+e(x['id'])+'"><strong>'+e(x['id'])+' · '+e(x['own_word_subject'])+'</strong> (source lines '+str(x['line_start'])+'–'+str(x['line_end'])+'). '+section_links(x['sections'])+'<p>'+e(x['boundary'])+'</p></li>'
    coverage+='</ul><h2 id="spec-areas">Nineteen Pro spec areas</h2><ul>'
    for x in data['spec_areas']:
        coverage+='<li id="area-'+e(x['id'])+'"><strong>'+e(x['id'])+'</strong> · '+section_links(x['sections'])+'<p>'+e(x['scope'])+' '+evidence([x['source']])+'</p></li>'
    coverage+='</ul><h2 id="screens">Major screens and feedback</h2><ul>'
    for x in data['screens']:
        coverage+='<li id="screen-'+e(x['id'])+'"><strong>'+e(x['title'])+' · '+e(x['status'])+'</strong><p>'+e(x['boundary'])+'</p>'+section_links(x['sections'])+'<p>'+evidence(x['sources'])+'</p></li>'
    coverage+='</ul><h2 id="conflicts">Source discrepancies</h2><ul>'
    for x in data['conflicts']:
        coverage+='<li id="conflict-'+e(x['id'])+'">'+e(x['statement'])+'<p>'+section_links(x['sections'])+' · '+evidence(x['sources'])+'</p></li>'
    coverage+='</ul>'
    return {'index.html':page('Isle Wars Pro — local illustrated manual',toc),'reference.html':page('Rules and reference',ref+sources(data)),'coverage.html':page('Coverage and evidence boundaries',coverage+sources(data)),'checklist.html':page('UI and map planning checklist',checklist+sources(data))}


def add_book_nav(document):
    # Preserve all illustrated sections byte-for-byte; only add book navigation.
    return document.replace('<h1>',NAV+'<h1>',1)
