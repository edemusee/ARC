"""Bhagavad Gita (gita/gita repo) → works/bhagavad-gita.

Levels chapter(unit)/verse; ref `2:47`. Editions: sa (Devanagari), translit (repo's simplified scheme),
en-purohit (Shri Purohit Swami 1935), en-sivananda (Swami Sivananda), hi (Swami Tejomayananda).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (DEVA_EDITION, EN_EDITION, HI_EDITION, IAST_EDITION, GITA, edition, level, load_json, manifest, norm,
                    passage, report, reset_work, write_manifest, write_unit)

WORK = 'bhagavad-gita'
REPO = 'https://github.com/gita/gita'
SPEAKER = re.compile(r'^\s*(धृतराष्ट्र\s*उवाच|स(?:ञ्|ं)जय\s*उवाच|अर्जुन\s*उवाच|श्री\s*भगवानुवाच)')
SPEAKER_TL = re.compile(r'^\s*((?:dhṛitarāśhtra|sañjaya|arjuna|śhrī bhagavān)\s+uvācha)\s*$', re.I)
MARKER = re.compile(r'\s*।+\s*\d+\.\d+\s*।*\s*$')

EDITIONS = [
    edition('sa', 'Sanskrit (Devanagari)', 'original',
            'Repository released under the Unlicense (public domain dedication); the Sanskrit text is public domain',
            f'{REPO} (data/verse.json, field "text")', base=DEVA_EDITION,
            notes='Speaker lines (Dhritarashtra uvacha, Sanjaya uvacha, Arjuna uvacha, Shri Bhagavan uvacha) are shown '
                  'as headings; the trailing ।।1.1।। verse markers of the source are removed.'),
    edition('translit', 'Transliteration (simplified)', 'transliteration',
            'Repository released under the Unlicense (public domain dedication)',
            f'{REPO} (data/verse.json, field "transliteration")', base=IAST_EDITION,
            notes='The repository uses a simplified reading scheme (śh, ch, ṛi, …), not IAST.'),
    edition('en-purohit', 'English — Shri Purohit Swami (1935)', 'translation',
            'Public domain in India (Shri Purohit Swami, The Geeta, 1935; translator died 1941); reproduced from the '
            'gita/gita repository (Unlicense)',
            f'{REPO} (data/translation.json, author "Shri Purohit Swami")'),
    edition('en-sivananda', 'English — Swami Sivananda', 'translation',
            'Divine Life Society — reproduced from gita/gita repo (Unlicense); rights as stated by the Society',
            f'{REPO} (data/translation.json, author "Swami Sivananda")'),
    edition('hi', 'Hindi — Swami Tejomayananda', 'translation',
            'Chinmaya Mission (Swami Tejomayananda) — reproduced from the gita/gita repo (Unlicense); rights as held by '
            'the translator/publisher',
            f'{REPO} (data/translation.json, author "Swami Tejomayananda")', base=HI_EDITION,
            notes='Leading ।।1.1।। verse markers of the source are removed.'),
]


def clean_sanskrit(text):
    t = norm(text)
    t = MARKER.sub('', t.replace('\n', ' ') if '\n' not in t.strip() else t)
    heading = None
    m = SPEAKER.match(t)
    if m:
        heading = re.sub(r'\s+', ' ', m.group(1)).strip()
        heading = heading.replace('श्री भगवानुवाच', 'श्रीभगवानुवाच')
        t = t[m.end():].strip()
    t = MARKER.sub('', t)
    lines = [l.strip() for l in t.split('\n') if l.strip()]
    if len(lines) == 1:
        lines = [l.strip() for l in re.split(r'(?<=।)', lines[0]) if l.strip()]
    lines = [l for l in lines if l]
    lines[-1] = re.sub(r'\s*[।॥]+\s*$', '', lines[-1]) + '॥'
    return '\n'.join(lines), heading


def clean_translit(text):
    lines = [l.strip() for l in norm(text).split('\n') if l.strip()]
    heading = None
    if lines and SPEAKER_TL.match(lines[0]):
        heading = lines[0]
        lines = lines[1:]
    return '\n'.join(lines), heading


def clean_hindi(text):
    t = norm(text)
    t = re.sub(r'^\s*।+\s*\d+\.\d+\s*।+\s*', '', t)
    t = re.sub(r'\s*।।\s*$', '।', t)
    return t


def main():
    reset_work(WORK)
    verses = sorted(load_json(os.path.join(GITA, 'verse.json')), key=lambda v: (v['chapter_number'], v['verse_number']))
    chapters = sorted(load_json(os.path.join(GITA, 'chapters.json')), key=lambda c: c['chapter_number'])
    translations = load_json(os.path.join(GITA, 'translation.json'))
    by_verse_id = {v['id']: (v['chapter_number'], v['verse_number']) for v in verses}
    tr = {'en-purohit': {}, 'en-sivananda': {}, 'hi': {}}
    for t in translations:
        key = {'Shri Purohit Swami': 'en-purohit', 'Swami Sivananda': 'en-sivananda',
               'Swami Tejomayananda': 'hi'}.get(t['authorName'])
        if key:
            tr[key][by_verse_id[t['verse_id']]] = t['description']

    units = passages = 0
    toc, aliases = [], {}
    for ch in chapters:
        n = ch['chapter_number']
        cv = [v for v in verses if v['chapter_number'] == n]
        assert len(cv) == ch['verses_count'], (n, len(cv), ch['verses_count'])
        sa, tl, en1, en2, hi = [], [], [], [], []
        for v in cv:
            ref = f'{n}:{v["verse_number"]}'
            text, heading = clean_sanskrit(v['text'])
            sa.append(passage(ref, text, heading))
            text, heading = clean_translit(v['transliteration'])
            tl.append(passage(ref, text, heading))
            key = (n, v['verse_number'])
            for lst, eid in ((en1, 'en-purohit'), (en2, 'en-sivananda')):
                if norm(tr[eid].get(key, '')):
                    lst.append(passage(ref, tr[eid][key]))
            if norm(clean_hindi(tr['hi'].get(key, ''))):
                hi.append(passage(ref, clean_hindi(tr['hi'][key])))
        for eid, lst in (('sa', sa), ('translit', tl), ('en-purohit', en1), ('en-sivananda', en2), ('hi', hi)):
            write_unit(WORK, eid, str(n), lst)
            units += 1
            passages += len(lst)
        name = ch['name_translation'].strip()
        toc.append({'ref': str(n), 'label': {'en': f'{name} — {ch["name_meaning"].strip()}', 'sa': ch['name']},
                    'count': ch['verses_count']})
        al = {name.lower(), ch['name_transliterated'].lower(), f'gita {n}', f'chapter {n}', f'bg {n}',
              f'bhagavad gita {n}', ch['name_meaning'].lower()}
        base = re.sub(r'\s*yoga?$', '', name.lower())
        al.add(base)
        al.add(base + ' yoga')
        aliases[str(n)] = sorted(a for a in al if a)

    m = manifest(
        WORK, 'scripture', [],
        {'en': 'Bhagavad Gita', 'sa': 'श्रीमद्भगवद्गीता'},
        [level('chapter', 'Chapter', True), level('verse', 'Verse')],
        {'format': '{work} {chapter}.{verse}', 'rangeFormat': '{work} {chapter}.{verse}–{verse2}',
         'workAbbrev': {'en': 'Gita'}},
        toc, EDITIONS, ['sa', 'en-purohit'],
        subtitle={'en': 'The Song of the Lord — 18 chapters, 700 verses, from the Bhishma Parva of the Mahabharata'},
        aliases=aliases,
        notes='Each chapter is one unit; verse numbering follows the standard 700-verse text (chapter 1 has 47 verses).')
    write_manifest(WORK, m)
    report(WORK, 'scripture', [], [e['id'] for e in EDITIONS], units, passages)


if __name__ == '__main__':
    main()
