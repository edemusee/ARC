"""Ramcharitmanas (WirelessAlien/Ramcharitmanas, IITK text) → works/ramcharitmanas.

The source holds one entry per doha-block: the chaupai lines leading up to a doha/soratha (plus occasional chhand
and shloka lines), labelled with चौपाई / दोहा/सोरठा / छंद / श्लोक lines. Levels kand / doha(unit) / line; unit
`bal:1` = Bal Kand block ending in doha 1; each verse line is one passage, with the block label as heading on
the first line of each block. The source's float "verse-number" loses trailing zeros (1.10 → 1.1), so the doha
number is the entry's position within the kand.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (AWADHI_EDITION, RAMCHARITMANAS, edition, level, load_json, manifest, norm, passage, report,
                    reset_work, write_manifest, write_unit)

WORK = 'ramcharitmanas'
REPO = 'https://github.com/WirelessAlien/Ramcharitmanas'

KANDS = [
    ('bal', 'balkanda.json', 'Bal Kand', 'बालकाण्ड', ['bal', 'balkand', 'bal kand', 'balkanda']),
    ('ayodhya', 'ayodhyakanda.json', 'Ayodhya Kand', 'अयोध्याकाण्ड', ['ayodhya', 'ayodhya kand', 'ayodhyakanda']),
    ('aranya', 'aranyakanda.json', 'Aranya Kand', 'अरण्यकाण्ड', ['aranya', 'aranya kand', 'aranyakanda']),
    ('kishkindha', 'kishkindhakanda.json', 'Kishkindha Kand', 'किष्किन्धाकाण्ड',
     ['kishkindha', 'kishkindha kand', 'kishkindhakanda']),
    ('sundar', 'sundarkanda.json', 'Sundar Kand', 'सुन्दरकाण्ड', ['sundar', 'sundar kand', 'sundarkanda', 'sundara kanda']),
    ('lanka', 'lankakanda.json', 'Lanka Kand', 'लंकाकाण्ड', ['lanka', 'lanka kand', 'lankakanda', 'yuddha kand']),
    ('uttar', 'uttarakanda.json', 'Uttar Kand', 'उत्तरकाण्ड', ['uttar', 'uttar kand', 'uttarakanda', 'uttara kand']),
]
LABELS = {'चौपाई': 'चौपाई', 'दोहा/सोरठा': 'दोहा / सोरठा', 'दोहा': 'दोहा', 'सोरठा': 'सोरठा', 'छंद': 'छंद', 'श्लोक': 'श्लोक'}

EDITIONS = [
    edition('aw', 'Awadhi (Devanagari)', 'original',
            'Unlicense (public domain dedication) per the repository; text sourced from ramcharitmanas.iitk.ac.in (IIT Kanpur)',
            f'{REPO} (main/data/verses/<kand>.json)', base=AWADHI_EDITION,
            notes='Each unit is the group of chaupais (and any chhand/shloka) that leads up to one doha or soratha; '
                  'the block labels of the source (चौपाई, दोहा/सोरठा, छंद, श्लोक) are shown as headings. The source '
                  'does not distinguish doha from soratha. Trailing doha numbers are removed.'),
]


def clean_line(l):
    t = norm(l)
    t = re.sub(r'\s*[।॥]+\s*\d+\s*(?:\(+\s*[क-ह]\s*\)*|[क-ह])?\s*[।॥]*\s*$', '॥', t)   # ।।1।। / ॥21(क)॥ doha markers
    t = t.replace('।।', '॥')
    t = re.sub(r'\s+([।॥])', r'\1', t)
    return t


def main():
    reset_work(WORK)
    units = passages = 0
    toc, aliases = [], {}
    for slug, fn, en_name, hi_name, al in KANDS:
        entries = load_json(os.path.join(RAMCHARITMANAS, fn))
        children = []
        for n, e in enumerate(entries, 1):
            unit = f'{slug}:{n}'
            ps, heading, i = [], None, 0
            for raw in e['content'].split('\n'):
                line = raw.strip()
                if not line:
                    continue
                if line in LABELS:
                    heading = LABELS[line]
                    continue
                text = clean_line(line)
                if not text or re.fullmatch(r'[।॥\s]+', text):
                    continue
                i += 1
                ps.append(passage(f'{unit}:{i}', text, heading))
                heading = None
            assert ps, (slug, n)
            write_unit(WORK, 'aw', unit, ps)
            units += 1
            passages += len(ps)
            children.append({'ref': unit, 'label': {'en': f'Doha {n}', 'hi': f'दोहा {n}'}, 'count': len(ps)})
            aliases[unit] = [f'{slug} {n}', f'{en_name.lower()} {n}', f'{en_name.lower()} doha {n}']
        toc.append({'ref': slug, 'label': {'en': en_name, 'hi': hi_name}, 'children': children})
        aliases[slug] = al

    m = manifest(
        WORK, 'scripture', ['vaishnava'],
        {'en': 'Ramcharitmanas', 'hi': 'श्रीरामचरितमानस'},
        [level('kand', 'Kand'), level('doha', 'Doha', True), level('line', 'Line')],
        {'format': '{work} {kand} {doha}.{line}', 'rangeFormat': '{work} {kand} {doha}.{line}–{line2}',
         'workAbbrev': {'en': 'Manas'}},
        toc, EDITIONS, ['aw'],
        subtitle={'en': 'Tulsidas\'s Awadhi retelling of the Ramayana — 7 kands, 1,074 doha blocks'},
        aliases=aliases,
        notes='Awadhi text only; no English translation is included. Units are numbered by the doha that closes each '
              'block of chaupais (Bal Kand 1–361, Ayodhya 1–326, Aranya 1–46, Kishkindha 1–30, Sundar 1–60, Lanka 1–121, '
              'Uttar 1–130).')
    write_manifest(WORK, m)
    report(WORK, 'scripture', ['vaishnava'], [e['id'] for e in EDITIONS], units, passages)


if __name__ == '__main__':
    main()
