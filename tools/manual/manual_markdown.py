"""Canonical evidence spans and coverage rows for the GitHub-readable manual."""

def source_links(refs, sources):
    return ', '.join('['+sid+'](../../'+sources[sid]['path']+('#'+sources[sid]['anchor'] if sources[sid].get('anchor') else '')+')' for sid in refs)


def evidence_line(block, sources):
    unknown = block['basis'] == 'unknown'
    label = 'Limitation sources' if unknown else 'Evidence'
    return label+': '+block['basis']+' · '+block['confidence']+'; '+source_links(block.get('limitation_sources' if unknown else 'sources',[]),sources)+'.'


def evidence_span(block, sources):
    return block['text']+'\n\n'+evidence_line(block,sources)


def section_links(ids):
    return ', '.join('['+sid+'](reference.md#'+sid+')' for sid in ids)


def subject_row(subject):
    return '| '+subject['id']+' | '+subject['own_word_subject']+' ('+str(subject['line_start'])+'–'+str(subject['line_end'])+') | '+section_links(subject['sections'])+' |'


def screen_row(screen):
    return '| '+screen['title']+' | '+screen['status']+' | '+screen['boundary']+' | '+section_links(screen['sections'])+' |'


def conflict_bullet(conflict, sources):
    return '- '+conflict['statement']+' '+source_links(conflict['sources'],sources)+'.'
