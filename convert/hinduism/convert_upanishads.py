"""Principal Upanishads → works/isha, kena, katha, prashna, mundaka, mandukya, aitareya.

Sanskrit from hrgupta/indian-scriptures (IITK scrape; CSV "mantra" field carries `।। 1.1.4 ।।` markers, commas
mark line breaks, shanti mantras / section titles precede the first mantra of a section).
English (isha, katha, kena) from Swami Paramananda, The Upanishads (1919), Project Gutenberg #3283: the first
paragraph after each roman numeral is the verse; the commentary paragraphs that follow are omitted.
Taittiriya and the file labelled Brihadaranyaka are skipped: see notes in the final report.
"""
import os
import re
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (DEVA_EDITION, EN_EDITION, PARAMANANDA, UPANISHAD_CSV, edition, level, manifest, norm, passage,
                    read_csv, read_text, report, reset_work, write_manifest, write_unit)

REPO_SA = 'https://github.com/hrgupta/indian-scriptures'
LIC_SA = ('Sanskrit text is public domain; the dataset (scraped from upanishads.iitk.ac.in) is distributed under the '
          'MIT License by hrgupta/indian-scriptures')
REPO_EN = 'https://www.gutenberg.org/ebooks/3283'
LIC_EN = ('Public domain. Swami Paramananda, The Upanishads, Vedanta Centre, Boston, 1919 (Project Gutenberg EBook '
          '#3283; author died 1940)')

MARKER = re.compile(r'।।\s*(\d+(?:\.\d+){1,2})\s*।।?')
ROMAN = {'I': 1, 'V': 5, 'X': 10, 'L': 50}

# workId -> config. `src` maps the source's (a, b, c) numbering onto (unit segments..., mantra).
WORKS = OrderedDict([
    ('isha', dict(csv='isavasya_upanishad.csv', title='Isha Upanishad', sa='ईशावास्योपनिषद्',
                  alt=['isavasya', 'ishavasya', 'isa', 'isha upanishad', 'ishopanishad'],
                  levels=[level('section', 'Section', True), level('mantra', 'Mantra')],
                  cite='{work} {mantra}', unit=lambda a, b, c: ('1',), unit_label=lambda u: 'Isha Upanishad',
                  en='Isa-Upanishad', en_part=lambda part: ('1',),
                  desc='18 mantras; the Vajasaneyi Samhita (Shukla Yajur Veda) chapter 40')),
    ('kena', dict(csv='kena_upanishad.csv', title='Kena Upanishad', sa='केनोपनिषद्',
                  alt=['kena', 'kenopanishad', 'talavakara'],
                  levels=[level('khanda', 'Khanda', True), level('mantra', 'Mantra')],
                  cite='{work} {khanda}.{mantra}', unit=lambda a, b, c: (str(a),), unit_label=lambda u: f'Khanda {u[0]}',
                  en='KENA-UPANISHAD', en_part=lambda part: (str(part),),
                  desc='4 khandas; from the Talavakara Brahmana of the Sama Veda')),
    ('katha', dict(csv='katha_upanishad.csv', title='Katha Upanishad', sa='कठोपनिषद्',
                   alt=['katha', 'kathopanishad', 'kathaka', 'nachiketa'],
                   levels=[level('adhyaya', 'Adhyaya'), level('valli', 'Valli', True), level('mantra', 'Mantra')],
                   cite='{work} {adhyaya}.{valli}.{mantra}', unit=lambda a, b, c: (str(a), str(b)),
                   unit_label=lambda u: f'Valli {u[0]}.{u[1]}',
                   en='Katha-Upanishad', en_part=lambda part: (str((part - 1) // 3 + 1), str((part - 1) % 3 + 1)),
                   desc='2 adhyayas of 3 vallis each; the dialogue of Nachiketa and Yama (Krishna Yajur Veda)')),
    ('prashna', dict(csv='prasna_upanishad.csv', title='Prashna Upanishad', sa='प्रश्नोपनिषद्',
                     alt=['prasna', 'prashna', 'prashnopanishad', 'prasnopanishad'],
                     levels=[level('prashna', 'Prashna', True), level('mantra', 'Mantra')],
                     cite='{work} {prashna}.{mantra}', unit=lambda a, b, c: (str(a),),
                     unit_label=lambda u: f'Prashna {u[0]}',
                     desc='6 questions put to the sage Pippalada (Atharva Veda)')),
    ('mundaka', dict(csv='mundaka_upanishad.csv', title='Mundaka Upanishad', sa='मुण्डकोपनिषद्',
                     alt=['mundaka', 'mundakopanishad'],
                     levels=[level('mundaka', 'Mundaka'), level('khanda', 'Khanda', True), level('mantra', 'Mantra')],
                     cite='{work} {mundaka}.{khanda}.{mantra}', unit=lambda a, b, c: (str(a), str(b)),
                     unit_label=lambda u: f'Mundaka {u[0]}, Khanda {u[1]}',
                     desc='3 mundakas of 2 khandas each (Atharva Veda)')),
    ('mandukya', dict(csv='mandukya_upanishad.csv', title='Mandukya Upanishad', sa='माण्डूक्योपनिषद्',
                      alt=['mandukya', 'mandukyopanishad', 'mandukya upanishad'],
                      levels=[level('section', 'Section', True), level('mantra', 'Mantra')],
                      cite='{work} {mantra}', unit=lambda a, b, c: ('1',), unit_label=lambda u: 'Mandukya Upanishad',
                      desc='12 mantras on Om and the four states of consciousness (Atharva Veda)')),
    ('aitareya', dict(csv='aitereya_upanishad.csv', title='Aitareya Upanishad', sa='ऐतरेयोपनिषद्',
                      alt=['aitareya', 'aitereya', 'aitareyopanishad'],
                      levels=[level('adhyaya', 'Adhyaya'), level('khanda', 'Khanda', True), level('mantra', 'Mantra')],
                      cite='{work} {adhyaya}.{khanda}.{mantra}',
                      unit=lambda a, b, c: {1: ('1', '1'), 2: ('1', '2'), 3: ('1', '3'), 4: ('2', '1'), 5: ('3', '1')}[b],
                      unit_label=lambda u: f'Adhyaya {u[0]}, Khanda {u[1]}',
                      desc='3 adhyayas (Rig Veda, Aitareya Aranyaka)',
                      sa_note='The source numbers the five khandas 1.1–1.5 in sequence; they are mapped to the '
                              'traditional 1.1, 1.2, 1.3, 2.1, 3.1.')),
])

# Paramananda's Kena Part First has 8 verses: III renders mantras 3 and 4 together.
EN_REMAP = {('kena', 1): {1: 1, 2: 2, 3: 3, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9}}


# ---------- Sanskrit ----------
def clean_sa(t):
    t = t.replace(' , ', ' ').replace(' ', ' ')
    t = re.sub(r'\s*,\s*', '\n', t)
    t = t.replace('ँ्', 'ँ').replace('्ँ', 'ँ').replace('़', '')
    t = re.sub(r'(?<=[ऀ-ॿ]):', 'ः', t)
    t = t.replace('।।', '॥')
    t = re.sub(r'\s+([।॥])', r'\1', t)
    t = re.sub(r'^\s*0', '', t)
    lines = [l.strip() for l in t.split('\n')]
    return [l for l in lines if l and not re.fullmatch(r'[।॥\s-]+', l)]


def parse_csv(path):
    """→ OrderedDict (a, b, c) -> (text, heading). Headings = shanti mantras / section titles preceding a mantra."""
    rows = read_csv(path)[1:]
    out = OrderedDict()
    for row in rows:
        field = row[1]
        pos = 0
        for m in MARKER.finditer(field):
            parts = tuple(int(x) for x in m.group(1).split('.'))
            if len(parts) == 2:
                parts = (1,) + parts
            chunk = field[pos:m.start()]
            pos = m.end()
            lines = clean_sa(chunk)
            # a heading block is everything before the last shanti/title lines; detect by the first danda-ending line
            heading, body = [], []
            # The pre-text (shanti mantra, title) is only present in the first segment of a row; separate it by looking
            # for colophon-free lines that precede the mantra: we take everything up to the last title-like line.
            idx = 0
            for i, l in enumerate(lines):
                if re.search(r'(उपनिषद्|खण्डः?|वल्ली|प्रश्नः?|मुण्डके|शान्तिः)\s*[॥।]*$', l) or l.startswith('हरिः ॐ') \
                        or re.fullmatch(r'हरिः\s*[।॥]*', l):
                    idx = i + 1
            heading, body = lines[:idx], lines[idx:]
            heading = [h for h in heading if not re.match(r'^[।॥\s]*(इति|--)', h)]
            if body and re.match(r'^हरिः\s*[।॥]+\s*', body[0]):
                heading.append('हरिः ॥')
                body[0] = re.sub(r'^हरिः\s*[।॥]+\s*', '', body[0])
            # shanti mantra lines before a title are part of the heading too (they precede idx already)
            if not body:
                continue
            body[-1] = re.sub(r'[।॥]*$', '', body[-1]) + '॥'
            if parts in out:
                continue
            out[parts] = ('\n'.join(body), '\n'.join(heading) if heading else None)
    return out


# ---------- English (Paramananda) ----------
def roman(s):
    s = s.strip()
    if not re.fullmatch(r'[IVXL]+', s):
        return None
    total, prev = 0, 0
    for ch in reversed(s):
        v = ROMAN[ch]
        total += -v if v < prev else v
        prev = max(prev, v)
    return total


def parse_paramananda():
    raw = read_text(PARAMANANDA, encoding='latin-1')
    lines = raw.replace('\r\n', '\n').split('\n')
    # locate the three texts: title line (second occurrence for Isa/Katha), ends at "Here ends this Upanishad"
    starts = {}
    for i, l in enumerate(lines):
        s = l.strip()
        if s in ('Isa-Upanishad', 'Katha-Upanishad', 'KENA-UPANISHAD') and i > 300:
            starts.setdefault(s, i)
    result = {}
    for title, start in starts.items():
        end = next(i for i in range(start, len(lines)) if lines[i].strip().startswith('Here ends this Upanishad'))
        part, verse, peace, verses = 1, None, [], OrderedDict()
        i = start + 1
        while i < end:
            s = lines[i].strip()
            m = re.fullmatch(r'Part (First|Second|Third|Fourth|fourth|Fifth|Sixth)', s)
            if m:
                part = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth'].index(m.group(1).lower()) + 1
                verse = None
                i += 1
                continue
            if s == 'Peace Chant':
                j = i + 1
                para, chant = [], []
                while j < end and not roman(lines[j]) and not lines[j].strip().startswith('Part '):
                    t = lines[j].strip()
                    if t:
                        para.append(t)
                    elif para:
                        chant.append(' '.join(para))
                        para = []
                    j += 1
                if para:
                    chant.append(' '.join(para))
                # keep only the chant itself (first paragraph(s) up to the OM! PEACE line); drop commentary after it
                keep = []
                for p in chant:
                    keep.append(p)
                    if p.startswith('OM!') and 'PEACE' in p:
                        break
                peace = keep
                i = j
                continue
            n = roman(s)
            if n:
                j = i + 1
                while j < end and not lines[j].strip():
                    j += 1
                para = []
                while j < end and lines[j].strip():
                    para.append(lines[j].strip())
                    j += 1
                text = ' '.join(para)
                verses[(part, n)] = (text, '\n'.join(peace) if peace else None)
                peace = []
                i = j
                continue
            i += 1
        result[title] = verses
    return result


def main():
    en_all = parse_paramananda()
    for wid, cfg in WORKS.items():
        reset_work(wid)
        sa = parse_csv(os.path.join(UPANISHAD_CSV, cfg['csv']))
        units_sa = OrderedDict()
        for (a, b, c), (text, heading) in sa.items():
            u = cfg['unit'](a, b, c)
            units_sa.setdefault(u, []).append(passage(':'.join(u) + f':{c}', text, heading))
        editions = [edition('sa', 'Sanskrit (Devanagari)', 'original', LIC_SA,
                            f'{REPO_SA} (data/processed/upanishads/{cfg["csv"]})', base=DEVA_EDITION,
                            notes=(cfg.get('sa_note', '') + ' Shanti mantras and section titles of the source are shown '
                                   'as headings; the anunasika written as ँ् in the source is normalised to ँ; '
                                   'colophons are omitted.').strip())]
        units = passages = 0
        all_units = OrderedDict((u, None) for u in units_sa)
        for u, ps in units_sa.items():
            write_unit(wid, 'sa', ':'.join(u), ps)
            units += 1
            passages += len(ps)
        # English
        if cfg.get('en'):
            ev = en_all[cfg['en']]
            units_en = OrderedDict()
            for (part, n), (text, heading) in ev.items():
                u = cfg['en_part'](part)
                n2 = EN_REMAP.get((wid, part), {}).get(n, n)
                units_en.setdefault(u, []).append(passage(':'.join(u) + f':{n2}', text, heading))
            for u, ps in units_en.items():
                write_unit(wid, 'en-paramananda', ':'.join(u), ps)
                units += 1
                passages += len(ps)
                all_units.setdefault(u, None)
            note = ('Verse translations only; Swami Paramananda\'s commentary paragraphs are omitted. Peace chants are '
                    'shown as headings.')
            if wid == 'kena':
                note += ' Paramananda renders khanda 1 mantras 3 and 4 as one verse (shown at 1.3); 1.4 is therefore absent.'
            if wid == 'katha':
                note += ' Paramananda\'s Parts First–Sixth correspond to vallis 1.1–1.3 and 2.1–2.3.'
            editions.append(edition('en-paramananda', 'English — Swami Paramananda (1919)', 'translation', LIC_EN,
                                    f'{REPO_EN} (3283-8.txt)', notes=note))
        # toc
        depth = len(cfg['levels'])
        toc = []
        if depth == 2:
            for u in all_units:
                cnt = len(units_sa.get(u, [])) or None
                e = {'ref': u[0], 'label': {'en': cfg['unit_label'](u)}}
                if cnt:
                    e['count'] = cnt
                toc.append(e)
        else:
            tops = OrderedDict()
            top_label = cfg['levels'][0]['label']['en']
            for u in all_units:
                tops.setdefault(u[0], {'ref': u[0], 'label': {'en': f'{top_label} {u[0]}'}, 'children': []})
                e = {'ref': ':'.join(u), 'label': {'en': cfg['unit_label'](u)}}
                cnt = len(units_sa.get(u, []))
                if cnt:
                    e['count'] = cnt
                tops[u[0]]['children'].append(e)
            toc = list(tops.values())
        aliases = {toc[0]['ref']: sorted(set(cfg['alt'] + [cfg['title'].lower()]))} if toc else None
        notes = cfg['desc'] + '.'
        if wid == 'katha':
            notes += ' The Sanskrit source covers adhyaya 1 only (vallis 1.1–1.3); the English covers all six vallis.'
        defaults = ['sa', 'en-paramananda'] if cfg.get('en') else ['sa']
        m = manifest(wid, 'scripture', [], {'en': cfg['title'], 'sa': cfg['sa']}, cfg['levels'],
                     {'format': cfg['cite'], 'rangeFormat': cfg['cite'] + '–{mantra2}',
                      'workAbbrev': {'en': cfg['title'].replace(' Upanishad', '')}},
                     toc, editions, defaults, subtitle={'sa': cfg['sa'], 'en': cfg['desc']}, aliases=aliases,
                     notes=notes)
        write_manifest(wid, m)
        report(wid, 'scripture', [], [e['id'] for e in editions], units, passages)


if __name__ == '__main__':
    main()
