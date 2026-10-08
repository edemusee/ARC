"""Rig Veda (VedaWeb data) → works/rig-veda.

Levels mandala / sukta(unit) / verse; ref `10:90:1`, unit file `10-90.json`. 1028 suktas.
Editions: sa (Eichler Devanagari, padas joined with newlines), translit (Lubotsky metrical IAST),
en-griffith (Griffith 1896). Sukta labels from VedaWeb's addressees.json (Geldner's addressees).
"""
import os
import re
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (DEVA_EDITION, EN_EDITION, IAST_EDITION, VEDAWEB, edition, level, load_json, manifest, norm,
                    passage, read_csv, report, reset_work, write_manifest, write_unit)

WORK = 'rig-veda'
REPO = 'https://github.com/VedaWebProject/vedaweb-data'
TEI = ('licence as stated in the VedaWeb corpus TEI header (rigveda/TEI/vedaweb_corpus.tei, checked 2026-10-08)')

EDITIONS = [
    edition('sa', 'Sanskrit (Devanagari, Eichler)', 'original',
            'CC BY-NC-SA 4.0 — Ṛgveda-Saṁhitā ed. Detlef Eichler (detlef108.de), as distributed by VedaWeb (Cologne Center '
            f'for e-Humanities); {TEI}. The Rig Veda text itself is public domain.',
            f'{REPO} (rigveda/versions/eichler.csv)', base=DEVA_EDITION,
            notes='Accented Devanagari text; the padas (half-verses) of each stanza are shown on separate lines, with dandas added.'),
    edition('translit', 'Transliteration (IAST, Lubotsky metrical text)', 'transliteration',
            'CC BY-NC-SA 4.0 — Alexander Lubotsky, A Rgvedic word concordance, metrically restored text as modified by '
            f'Dieter Gunkel and Kevin M. Ryan, distributed by VedaWeb; {TEI}',
            f'{REPO} (rigveda/versions/lubotsky.csv)', base=IAST_EDITION,
            notes='Metrically restored text in IAST with accents; one pada per line.'),
    edition('en-griffith', 'English — Ralph T. H. Griffith (1896)', 'translation',
            'Public domain translation (Ralph T. H. Griffith, The Hymns of the Rigveda, 2nd ed. 1896; translator died 1906). '
            f'The corrected digital file compiled by Mārcis Gasūns and distributed by VedaWeb is marked CC BY-NC-SA 4.0; {TEI}',
            f'{REPO} (rigveda/translations/eng/griffith.csv)'),
]

MANDALA_SA = {1: 'प्रथमं मण्डलम्', 2: 'द्वितीयं मण्डलम्', 3: 'तृतीयं मण्डलम्', 4: 'चतुर्थं मण्डलम्', 5: 'पञ्चमं मण्डलम्',
              6: 'षष्ठं मण्डलम्', 7: 'सप्तमं मण्डलम्', 8: 'अष्टमं मण्डलम्', 9: 'नवमं मण्डलम्', 10: 'दशमं मण्डलम्'}

FAMOUS = {
    '10:90': ['purusha sukta', 'purusha', 'purusa sukta', 'purushasukta'],
    '10:129': ['nasadiya', 'nasadiya sukta', 'nasadiya suktam', 'creation hymn', 'hymn of creation'],
    '3:62': ['gayatri', 'gayatri mantra', 'savitri'],
    '10:121': ['hiranyagarbha', 'hiranyagarbha sukta'],
    '1:1': ['agni sukta'],
}


def key_parts(k):
    m = re.fullmatch(r'(\d\d)\.(\d{3})\.(\d\d)', k)
    assert m, k
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def by_stanza(rows, multi):
    """rows → OrderedDict key -> text (padas joined with newline when multi)."""
    out = OrderedDict()
    for r in rows:
        k = r[0].strip()
        if not re.fullmatch(r'\d\d\.\d{3}\.\d\d', k):
            continue
        text = norm(r[2] if multi else r[1])
        if not text:
            continue
        out.setdefault(k, []).append(text)
    return {k: '\n'.join(v) for k, v in out.items()}


def dandas(text):
    """Eichler's padas carry no punctuation; close each half-verse with । and the stanza with ॥."""
    lines = text.split('\n')
    return '\n'.join(l + (' ॥' if i == len(lines) - 1 else ' ।') for i, l in enumerate(lines))


def main():
    reset_work(WORK)
    eichler = by_stanza(read_csv(os.path.join(VEDAWEB, 'versions', 'eichler.csv'), '\t'), True)
    eichler = {k: dandas(v) for k, v in eichler.items()}
    lubotsky = by_stanza(read_csv(os.path.join(VEDAWEB, 'versions', 'lubotsky.csv'), '\t'), True)
    griffith = by_stanza(read_csv(os.path.join(VEDAWEB, 'translations', 'eng', 'griffith.csv'), '\t'), False)
    addressees = load_json(os.path.join(VEDAWEB, 'info', 'addressees.json'))

    suktas = OrderedDict()
    for k in sorted(set(eichler) | set(lubotsky) | set(griffith), key=key_parts):
        m, s, v = key_parts(k)
        suktas.setdefault((m, s), []).append((v, k))

    units = passages = 0
    toc = OrderedDict()
    aliases = {}
    for (m, s), verses in suktas.items():
        unit = f'{m}:{s}'
        for eid, src in (('sa', eichler), ('translit', lubotsky), ('en-griffith', griffith)):
            ps = [passage(f'{unit}:{v}', src[k]) for v, k in verses if k in src]
            if ps:
                write_unit(WORK, eid, unit, ps)
                units += 1
                passages += len(ps)
        addr = addressees.get(f'{m:02d}.{s:03d}')
        deity = norm(addr[0][1]) if addr and addr[0] and len(addr[0]) > 1 else ''
        label = f'{m}.{s} — {deity}' if deity else f'Hymn {m}.{s}'
        toc.setdefault(m, {'ref': str(m), 'label': {'en': f'Mandala {m}', 'sa': MANDALA_SA[m]}, 'children': []})
        toc[m]['children'].append({'ref': unit, 'label': {'en': label}, 'count': len(verses)})
        al = [f'rv {m}.{s}', f'rigveda {m}.{s}', f'{m}.{s}']
        if deity:
            al.append(f'{deity.lower()} {m}.{s}')
        al += FAMOUS.get(unit, [])
        aliases[unit] = al
    for m in toc:
        aliases[str(m)] = [f'mandala {m}', f'book {m}', f'rv {m}', f'rigveda {m}']

    mf = manifest(
        WORK, 'scripture', [],
        {'en': 'Rig Veda', 'sa': 'ऋग्वेदः'},
        [level('mandala', 'Mandala'), level('sukta', 'Sukta', True), level('verse', 'Verse')],
        {'format': '{work} {mandala}.{sukta}.{verse}', 'rangeFormat': '{work} {mandala}.{sukta}.{verse}–{verse2}',
         'workAbbrev': {'en': 'RV'}},
        list(toc.values()), EDITIONS, ['sa', 'en-griffith'],
        subtitle={'en': 'The Rig Veda Samhita — 10 mandalas, 1028 hymns, 10,552 stanzas'},
        aliases=aliases,
        notes='Each hymn (sukta) is one unit. Famous hymns: Purusha Sukta 10.90, Nasadiya Sukta 10.129, the Gayatri '
              'mantra is 3.62.10, Hiranyagarbha Sukta 10.121. Hymn titles give the deity addressed (after Geldner).')
    write_manifest(WORK, mf)
    report(WORK, 'scripture', [], [e['id'] for e in EDITIONS], units, passages)


if __name__ == '__main__':
    main()
