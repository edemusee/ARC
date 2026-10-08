#!/usr/bin/env python3
"""Convert two short Islamic texts into works/.

  tahawiyyah     al-Aqidah al-Tahawiyyah, Arabic only, from the OpenITI 0325AH corpus
                 (0321Tahawi.MatnCaqida.JK000126-ara1). The `# n` numbered articles become passages;
                 levels section (isUnit, groups of 25 articles) / article. The preamble is the heading of 1:1.
  asma-ul-husna  the 99 Names of Allah from MZDN/asma-u-llahi-l-husna; levels list (isUnit) / name, one unit;
                 editions ar, translit, en (meaning). The "00" entry is dropped.

Usage: python3 -I convert_docs.py [tahawiyyah] [asma-ul-husna]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (AR_EDITION, ASMA, OPENITI, edition, load_json, manifest, norm, report, reset_work,
                    write_manifest, write_unit)

# ---------------------------------------------------------------- Tahawiyyah
OPENITI_REPO = 'https://github.com/OpenITI/0325AH'
OPENITI_LICENSE = ('OpenITI corpus text (CC BY-NC-SA 4.0 for the OpenITI markup/digitisation); the 10th-century '
                   'creed itself is public domain. Printed source per the file header: ed. al-Albani, '
                   'al-Maktab al-Islami, Beirut 1398/1978.')
GROUP = 25


def openiti_body(path):
    """Return the text after the #META# header with ~~ continuation lines joined and page markers removed."""
    with open(path, encoding='utf-8') as f:
        raw = f.read()
    body = raw.split('#META#Header#End#', 1)[1]
    lines = []
    for line in body.split('\n'):
        if line.startswith('~~'):
            lines[-1] += ' ' + line[2:]
        elif line.strip():
            lines.append(line)
    out = []
    for line in lines:
        line = re.sub(r'PageV\d+P\d+', ' ', line)
        line = re.sub(r'\bms\d+\b', ' ', line)
        line = line.replace('@QB@', '﴿').replace('@QE@', '﴾')
        line = re.sub(r'﴿\s+', '﴿', line)
        line = re.sub(r'\s+﴾', '﴾', line)
        out.append(line)
    return out


def convert_tahawiyyah():
    work_id = 'tahawiyyah'
    lines = openiti_body(OPENITI)
    preamble = None
    articles = []
    for line in lines:
        m = re.match(r'^#\s*\$\s*(.*)$', line)
        if m:
            preamble = norm(m.group(1))
            continue
        m = re.match(r'^#\s*(\d+)\s+(.*)$', line)
        if m:
            articles.append((int(m.group(1)), norm(m.group(2))))
            continue
        if line.startswith('#'):
            continue
        if articles:
            articles[-1] = (articles[-1][0], norm(articles[-1][1] + ' ' + line))
    nums = [n for n, _ in articles]
    assert nums == list(range(1, len(nums) + 1)), nums[:10]

    reset_work(work_id)
    toc = []
    units = passages = 0
    sections = {}
    for n, text in articles:
        sec = min((n - 1) // GROUP + 1, 4)   # 1–25, 26–50, 51–75, 76–105
        sections.setdefault(sec, []).append({'ref': f'{sec}:{n}', 'text': text})
    for sec, ps in sections.items():
        if sec == 1 and preamble:
            ps[0]['heading'] = preamble
        write_unit(work_id, 'ar', str(sec), ps)
        units += 1
        passages += len(ps)
        first, last = ps[0]['ref'].split(':')[1], ps[-1]['ref'].split(':')[1]
        toc.append({'ref': str(sec), 'label': {'en': f'Articles {first}–{last}', 'ar': f'المواد {first}–{last}'},
                    'count': len(ps)})

    ed = edition('ar', 'Arabic', 'original', OPENITI_LICENSE,
                 f'{OPENITI_REPO} (data/0321Tahawi/0321Tahawi.MatnCaqida/0321Tahawi.MatnCaqida.JK000126-ara1)',
                 base=AR_EDITION)
    m = manifest(
        work_id, 'documents', ['sunni'], {'en': 'Al-Aqidah al-Tahawiyyah', 'ar': 'العقيدة الطحاوية'},
        [{'id': 'section', 'label': {'en': 'Section'}, 'isUnit': True}, {'id': 'article', 'label': {'en': 'Article'}}],
        {'format': '{work} §{article}', 'rangeFormat': '{work} §{article}–{article2}', 'workAbbrev': {'en': 'Tahawiyyah'}},
        toc, [ed], ['ar'],
        subtitle={'en': 'Abu Ja\'far al-Tahawi (d. 321 AH) — the creed of Ahl al-Sunnah according to the Hanafi imams'},
        aliases={'1': ['tahawi', 'tahawiyyah', 'aqidah']},
        notes='Arabic text only; article numbering follows the OpenITI edition (105 articles). No English translation is included.')
    write_manifest(work_id, m)
    report(work_id, 'documents', ['sunni'], ['ar'], units, passages)


# ---------------------------------------------------------------- 99 Names
ASMA_REPO = 'https://github.com/MZDN/asma-u-llahi-l-husna'
ASMA_LICENSE = ('No licence file in the repository; the Names themselves are traditional text (public domain), '
                'the transliteration and glosses are by the repository author (MZDN), licence unstated')


def clean_meaning(s):
    parts = [norm(p) for p in str(s).split('/')]
    parts = [p for p in parts if p]
    return ' / '.join(parts)


def convert_asma():
    work_id = 'asma-ul-husna'
    d = load_json(ASMA)
    names = d['AsmaHusna'] if isinstance(d, dict) else d
    reset_work(work_id)
    ps = {'ar': [], 'translit': [], 'en': []}
    for e in names:
        n = int(e['number'])
        if n == 0:
            continue
        ref = f'1:{n}'
        ps['ar'].append({'ref': ref, 'text': norm(e['arabic'])})
        tl = re.sub(r'(?<=[A-ZḌṢṬẒ])([A-Z])(?=[a-z])', lambda m: m.group(1).lower(), norm(e['transliteration']))  # 'Aṣ-ṢAbūr'
        ps['translit'].append({'ref': ref, 'text': tl})
        ps['en'].append({'ref': ref, 'text': clean_meaning(e['meaning']['en'])})
    assert len(ps['ar']) == 99, len(ps['ar'])
    for ed_id, p in ps.items():
        write_unit(work_id, ed_id, '1', p)
    editions = [
        edition('ar', 'Arabic', 'original', ASMA_LICENSE, f'{ASMA_REPO} (BeautifulNamesOfAllah.json)', base=AR_EDITION),
        edition('translit', 'Transliteration', 'transliteration', ASMA_LICENSE, f'{ASMA_REPO} (BeautifulNamesOfAllah.json)'),
        edition('en', 'English — meaning', 'gloss', ASMA_LICENSE, f'{ASMA_REPO} (BeautifulNamesOfAllah.json)'),
    ]
    m = manifest(
        work_id, 'devotional', [], {'en': 'The 99 Names of Allah', 'ar': 'أسماء الله الحسنى'},
        [{'id': 'list', 'label': {'en': 'List'}, 'isUnit': True}, {'id': 'name', 'label': {'en': 'Name'}}],
        {'format': '{work} {name}', 'rangeFormat': '{work} {name}–{name2}', 'workAbbrev': {'en': 'Names'}},
        [{'ref': '1', 'label': {'en': 'Al-Asma ul-Husna', 'ar': 'الأسماء الحسنى'}, 'count': 99}],
        editions, ['ar', 'en'],
        subtitle={'en': 'Al-Asma ul-Husna, the Most Beautiful Names'},
        aliases={'1': ['names', 'asma', 'asma ul husna', 'al-asma ul-husna', '99 names']},
        notes='Compare the Arabic with the transliteration or the English meaning. Meanings are short glosses, not a translation.')
    write_manifest(work_id, m)
    report(work_id, 'devotional', [], [e['id'] for e in editions], 3, 297)


if __name__ == '__main__':
    want = sys.argv[1:] or ['tahawiyyah', 'asma-ul-husna']
    if 'tahawiyyah' in want:
        convert_tahawiyyah()
    if 'asma-ul-husna' in want:
        convert_asma()
