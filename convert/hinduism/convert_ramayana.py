"""Valmiki Ramayana (svenkatreddy/Ramayana_Book) → works/ramayana.

Levels kanda / sarga(unit) / shloka; ref `bala:1:1`, unit file `bala-1.json`; 645 sargas.
Editions: sa (Sanskrit Wikisource text as held by the repo), en (verse-aligned English from the Valmiki Ramayan
Dataset as bundled by the repo).
"""
import glob
import os
import re
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (DEVA_EDITION, EN_EDITION, RAMAYANA, edition, level, load_json, manifest, norm, passage, report,
                    reset_work, write_manifest, write_unit)

WORK = 'ramayana'
REPO = 'https://github.com/svenkatreddy/Ramayana_Book'

KANDAS = [
    ('bala', 'bala_kanda', 'Bala Kanda', 'बालकाण्डम्', ['bala', 'balakanda', 'bala kanda', 'book of childhood']),
    ('ayodhya', 'ayodhya_kanda', 'Ayodhya Kanda', 'अयोध्याकाण्डम्', ['ayodhya', 'ayodhyakanda', 'ayodhya kanda']),
    ('aranya', 'aranya_kanda', 'Aranya Kanda', 'अरण्यकाण्डम्', ['aranya', 'aranyakanda', 'aranya kanda', 'forest']),
    ('kishkindha', 'kishkindha_kanda', 'Kishkindha Kanda', 'किष्किन्धाकाण्डम्',
     ['kishkindha', 'kishkindhakanda', 'kishkindha kanda', 'kiskindha']),
    ('sundara', 'sundara_kanda', 'Sundara Kanda', 'सुन्दरकाण्डम्', ['sundara', 'sundarakanda', 'sundara kanda', 'sundar kand']),
    ('yuddha', 'yuddha_kanda', 'Yuddha Kanda', 'युद्धकाण्डम्', ['yuddha', 'yuddhakanda', 'yuddha kanda', 'lanka kanda', 'war']),
    ('uttara', 'uttara_kanda', 'Uttara Kanda', 'उत्तरकाण्डम्', ['uttara', 'uttarakanda', 'uttara kanda']),
]

EDITIONS = [
    edition('sa', 'Sanskrit (Devanagari)', 'original',
            'CC BY-SA (Sanskrit Wikisource contributors) as stated by the repository; three sargas (Kishkindha 11, Yuddha 25, '
            'Yuddha 31) restored from IIT Kanpur\'s Valmiki Ramayanam per the repository README',
            f'{REPO} (san/<kanda>/chapter<N>.json)', base=DEVA_EDITION,
            notes='Trailing ॥५-१-१॥ verse markers are removed and half-verses are shown on separate lines; occasional '
                  'transliteration artefacts of the Wikisource text (e.g. R^) are left as found.'),
    edition('en', 'English (Ramayana_Book dataset)', 'translation',
            'stated MIT by repo; translation provenance unverified',
            f'{REPO} (translations/en/<kanda>/chapter<N>.json; the repo credits the Valmiki Ramayan Dataset by Ashutosh Vijay, '
            'drawing on M. N. Dutt 1891–1894, IIT Kanpur and Gyaandweep)',
            notes='Verse-aligned prose; about 1% of verses (mostly colophons) have no translation and are absent.'),
]

TRAIL = re.compile(r'\s*[।॥]*\s*[०-९0-9]+(?:\s*[-.]\s*[०-९0-9]+){0,2}\s*[।॥]*\s*$')


def clean_sa(s):
    t = norm(re.sub(r'<br\s*/?>', '\n', s, flags=re.I))
    t = t.replace('R^', '')
    # strip (possibly repeated) trailing verse markers such as ॥१-१-१॥ / ।। ५.५८.११ ।।११७ ।।।।
    prev = None
    while prev != t:
        prev = t
        t = TRAIL.sub('', t)
    t = re.sub(r'\s*[।॥]+\s*$', '', t)
    # markers left in the middle of a merged verse: ॥ ६.९७.३० ॥
    t = re.sub(r'\s*[।॥]*\s*[०-९0-9]+(?:\s*[-.]\s*[०-९0-9]+){1,2}\s*[।॥]*', '॥', t)
    t = re.sub(r'^[।॥\s]+', '', t)
    t = t.replace('।।', '॥')
    t = re.sub(r'॥+', '॥', t)
    # half-verse breaks: a danda directly followed by text
    t = re.sub(r'([।॥])\s*(?=[ऀ-ॿ(])', r'\1\n', t)
    t = re.sub(r'\s+([।॥])', r'\1', t)
    lines = [l.strip() for l in t.split('\n') if l.strip()]
    if not lines:
        return ''
    lines[-1] = lines[-1] + '॥'
    return '\n'.join(lines)


def main():
    reset_work(WORK)
    units = passages = 0
    toc, aliases = [], {}
    for slug, folder, en_name, sa_name, al in KANDAS:
        files = glob.glob(os.path.join(RAMAYANA, 'san', folder, 'chapter*.json'))
        chapters = sorted(int(re.search(r'chapter(\d+)\.json$', f).group(1)) for f in files)
        assert chapters == list(range(1, len(chapters) + 1)), (slug, chapters[-3:])
        children = []
        for n in chapters:
            d = load_json(os.path.join(RAMAYANA, 'san', folder, f'chapter{n}.json'))
            ch = d[list(d.keys())[0]]['chapters'][0]
            assert ch['chapter_number'] == n
            unit = f'{slug}:{n}'
            sa = []
            for i, s in enumerate(ch['slokas'], 1):
                text = clean_sa(s)
                if text:
                    sa.append(passage(f'{unit}:{i}', text))
            e = load_json(os.path.join(RAMAYANA, 'translations', 'en', folder, f'chapter{n}.json'))
            en = []
            for k in sorted(e['verses'], key=int):
                t = norm(e['verses'][k])
                if t:
                    en.append(passage(f'{unit}:{k}', t))
            write_unit(WORK, 'sa', unit, sa)
            units += 1
            passages += len(sa)
            if en:
                write_unit(WORK, 'en', unit, en)
                units += 1
                passages += len(en)
            children.append({'ref': unit, 'label': {'en': f'Sarga {n}', 'sa': f'सर्गः {n}'}, 'count': len(sa)})
            aliases[unit] = [f'{slug} {n}', f'{en_name.lower()} {n}', f'{en_name.lower().replace(" kanda", "")} sarga {n}']
        toc.append({'ref': slug, 'label': {'en': en_name, 'sa': sa_name}, 'children': children})
        aliases[slug] = al

    m = manifest(
        WORK, 'scripture', ['vaishnava'],
        {'en': 'Ramayana', 'sa': 'श्रीमद्वाल्मीकीयरामायणम्'},
        [level('kanda', 'Kanda'), level('sarga', 'Sarga', True), level('shloka', 'Shloka')],
        {'format': '{work} {kanda} {sarga}.{shloka}', 'rangeFormat': '{work} {kanda} {sarga}.{shloka}–{shloka2}',
         'workAbbrev': {'en': 'Ramayana'}},
        toc, EDITIONS, ['sa', 'en'],
        subtitle={'en': 'The Valmiki Ramayana — 7 kandas, 645 sargas, about 24,000 shlokas'},
        aliases=aliases,
        notes='Each sarga (chapter) is one unit. Kanda names: Bala, Ayodhya, Aranya, Kishkindha, Sundara, Yuddha, Uttara.')
    write_manifest(WORK, m)
    report(WORK, 'scripture', ['vaishnava'], [e['id'] for e in EDITIONS], units, passages)


if __name__ == '__main__':
    main()
