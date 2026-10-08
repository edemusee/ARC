"""Devotional works → works/hanuman-chalisa (one unit "1": 2 opening dohas, 40 chaupais, closing doha) and
works/vishnu-sahasranama (units = the 107 shlokas of the swami-krishnananda grouping used by the dataset; ref
`<shloka>:<name number 1–1000>`).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (CHALISA, DEVA_EDITION, EN_EDITION, HI_EDITION, IAST_EDITION, SAHASRANAMA, edition, level,
                    load_json, manifest, norm, passage, read_csv, report, reset_work, write_manifest, write_unit)

CH_REPO = 'https://github.com/gurbaxani/hanuman-chalisa'
VS_REPO = 'https://github.com/swathi/vishnu-sahasranama (sahasranama.github.io)'


def chalisa():
    work = 'hanuman-chalisa'
    reset_work(work)
    hi = load_json(os.path.join(CHALISA, 'hi.json'))
    en = load_json(os.path.join(CHALISA, 'en.json'))
    # (ref number, verse-line keys, meaning key, heading)
    items = []
    items.append((1, ['opening_doha_1', 'opening_doha_2', 'opening_doha_3', 'opening_doha_4'], 'learn_o1_m', 'doha'))
    items.append((2, ['opening_doha_5', 'opening_doha_6', 'opening_doha_7', 'opening_doha_8'], 'learn_o2_m', None))
    for v in range(1, 41):
        items.append((v + 2, [f'verse_{v}_1', f'verse_{v}_2'], f'learn_v{v}_m', 'chaupai' if v == 1 else None))
    items.append((43, ['concluding_doha_1', 'concluding_doha_2', 'concluding_doha_3', 'concluding_doha_4'],
                  'learn_c1_m', 'doha'))
    heads = {'hi': {'doha': 'दोहा', 'chaupai': 'चौपाई'}, 'translit': {'doha': 'Doha', 'chaupai': 'Chaupai'},
             'en': {'doha': 'Doha', 'chaupai': 'Chaupai'}}
    out = {'hi': [], 'translit': [], 'en': []}
    for n, keys, mkey, head in items:
        ref = f'1:{n}'
        hi_lines = [norm(hi[k]) for k in keys]
        tl_lines = [norm(en[k]) for k in keys]
        # dohas are written as two half-lines each; join the pairs
        if len(keys) == 4:
            hi_lines = [hi_lines[0] + ' ' + hi_lines[1], hi_lines[2] + ' ' + hi_lines[3]]
            tl_lines = [tl_lines[0] + ' ' + tl_lines[1], tl_lines[2] + ' ' + tl_lines[3]]
        out['hi'].append(passage(ref, '\n'.join(hi_lines), heads['hi'].get(head)))
        out['translit'].append(passage(ref, '\n'.join(tl_lines), heads['translit'].get(head)))
        out['en'].append(passage(ref, en[mkey], heads['en'].get(head)))
    lic = 'MIT License (KH Systems Private Limited / gurbaxani); the Chalisa text itself is public domain (Tulsidas, 16th c.)'
    editions = [
        edition('hi', 'Awadhi/Hindi (Devanagari)', 'original', lic, f'{CH_REPO} (messages/hi.json)', base=HI_EDITION),
        edition('translit', 'Transliteration (popular scheme)', 'transliteration', lic, f'{CH_REPO} (messages/en.json)',
                base={'lang': 'hi', 'script': 'Latn', 'direction': 'ltr'}, notes='The repository\'s informal roman spelling, not IAST.'),
        edition('en', 'English — meaning', 'translation', lic, f'{CH_REPO} (messages/en.json, learn_*_m keys)',
                notes='Verse-by-verse meanings as given in the app.'),
    ]
    for eid, ps in out.items():
        write_unit(work, eid, '1', ps)
    m = manifest(
        work, 'devotional', ['vaishnava'],
        {'en': 'Hanuman Chalisa', 'hi': 'हनुमान चालीसा'},
        [level('text', 'Text', True), level('verse', 'Verse')],
        {'format': '{work} {verse}', 'rangeFormat': '{work} {verse}–{verse2}', 'workAbbrev': {'en': 'Chalisa'}},
        [{'ref': '1', 'label': {'en': 'Hanuman Chalisa', 'hi': 'हनुमान चालीसा'}, 'count': len(out['hi'])}],
        editions, ['hi', 'en'],
        subtitle={'en': 'Tulsidas\'s forty verses in praise of Hanuman'},
        aliases={'1': ['hanuman chalisa', 'chalisa', 'hanuman']},
        notes='Verses 1–2 are the opening dohas, 3–42 the forty chaupais, 43 the closing doha.')
    write_manifest(work, m)
    report(work, 'devotional', ['vaishnava'], [e['id'] for e in editions], 3, 3 * len(out['hi']))


def sahasranama():
    work = 'vishnu-sahasranama'
    reset_work(work)
    names = load_json(os.path.join(SAHASRANAMA, 'names_1000.json'))
    atlas = load_json(os.path.join(SAHASRANAMA, 'atlas.json'))
    dev = {int(r[0]): norm(r[1]) for r in read_csv(os.path.join(SAHASRANAMA, 'build', 'dev_all.tsv'), '\t') if r and r[0].strip().isdigit()}
    nodes = {n['n']: n for n in atlas['nodes']}
    slokas = atlas['meta']['slokas']
    assert sum(s['count'] for s in slokas) == 1000 and len(names) == 1000
    by_n = {x['n']: x for x in names}
    units = passages = 0
    toc = []
    for s in slokas:
        unit = str(s['s'])
        nm, tl, en = [], [], []
        for n in range(s['first'], s['last'] + 1):
            ref = f'{unit}:{n}'
            d = nodes.get(n, {}).get('dev') or dev.get(n)
            nm.append(passage(ref, d if d else by_n[n]['name']))
            iast = nodes.get(n, {}).get('iast')
            tl.append(passage(ref, iast if iast else by_n[n]['name']))
            en.append(passage(ref, by_n[n]['meaning']))
        for eid, ps in (('name', nm), ('translit', tl), ('en', en)):
            write_unit(work, eid, unit, ps)
            units += 1
            passages += len(ps)
        toc.append({'ref': unit, 'label': {'en': f'Shloka {unit} (names {s["first"]}–{s["last"]})'}, 'count': s['count']})
    lic_en = 'meanings as published by sahasranama.github.io, rights of respective authors'
    editions = [
        edition('name', 'Names (Devanagari)', 'original',
                'The names are traditional public-domain text; Devanagari forms assembled by the project from the '
                'drikpanchang.com namavali and other namavalis (repository code MIT; data: "rights of respective authors")',
                f'{VS_REPO} (data/atlas.json nodes[].dev, falling back to data/build/dev_all.tsv)', base=DEVA_EDITION,
                notes='Names in nominative form as reconciled in the project\'s atlas; the project warns that the Devanagari was machine-matched and '
                      'should be verified against a trusted edition before liturgical use.'),
        edition('translit', 'Names (IAST)', 'transliteration',
                'Generated deterministically from the Devanagari by the project (repository code MIT)',
                f'{VS_REPO} (data/atlas.json, field "iast")', base=IAST_EDITION),
        edition('en', 'English — meaning', 'translation', lic_en, f'{VS_REPO} (data/names_1000.json)',
                notes='Short English glosses following the Sri Ramakrishna Math rendering, as given by the project.'),
    ]
    m = manifest(
        work, 'devotional', ['vaishnava'],
        {'en': 'Vishnu Sahasranama', 'sa': 'विष्णुसहस्रनाम'},
        [level('shloka', 'Shloka', True), level('name', 'Name')],
        {'format': '{work} {name}', 'rangeFormat': '{work} {name}–{name2}', 'workAbbrev': {'en': 'VS'}},
        toc, editions, ['name', 'en'],
        subtitle={'en': 'The thousand names of Vishnu, grouped into 107 shlokas'},
        aliases={'1': ['vishnu sahasranama', 'sahasranama', 'sahasranamam', 'thousand names', '1000 names']},
        notes='Each unit is one shloka of the stotra; a name is cited by its running number 1–1000. The shloka '
              'grouping follows swami-krishnananda.org as used by the dataset (107 shlokas).')
    write_manifest(work, m)
    report(work, 'devotional', ['vaishnava'], [e['id'] for e in editions], units, passages)


if __name__ == '__main__':
    chalisa()
    sahasranama()
