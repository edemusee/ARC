"""Talmud Bavli (37 tractates) → works/talmud-bavli.

Levels tractate / daf / side(unit) / segment; ref `berakhot:2:a:3`, unit file `berakhot-2-a.json`.
Sefaria `text[n]` is daf (n//2 + 1), side a when n is even, b when odd; text[0], text[1] (daf 1) are empty.
Editions: en-davidson (William Davidson Edition – English, CC-BY-NC) and ar-vocalized (William Davidson
Edition – Vocalized Aramaic, CC-BY-NC).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (EN_EDITION, HE_EDITION, clean, edition, license_text, passage, report, reset_work,
                    sefaria_version, slugify, source_url, write_manifest, write_unit)

WORK = 'talmud-bavli'

SEDARIM = [
    ('Zeraim', 'זרעים', ['Berakhot']),
    ('Moed', 'מועד', ['Shabbat', 'Eruvin', 'Pesachim', 'Rosh Hashanah', 'Yoma', 'Sukkah', 'Beitzah', 'Taanit',
                      'Megillah', 'Moed Katan', 'Chagigah']),
    ('Nashim', 'נשים', ['Yevamot', 'Ketubot', 'Nedarim', 'Nazir', 'Sotah', 'Gittin', 'Kiddushin']),
    ('Nezikin', 'נזיקין', ['Bava Kamma', 'Bava Metzia', 'Bava Batra', 'Sanhedrin', 'Makkot', 'Shevuot',
                           'Avodah Zarah', 'Horayot']),
    ('Kodashim', 'קדשים', ['Zevachim', 'Menachot', 'Chullin', 'Bekhorot', 'Arakhin', 'Temurah', 'Keritot',
                           'Meilah', 'Tamid']),
    ('Tahorot', 'טהרות', ['Niddah']),
]

EXTRA_ALIASES = {
    'berakhot': ['brachot', 'berachot', 'brakhot'], 'shabbat': ['shabbos', 'shabat'], 'eruvin': ['eiruvin'],
    'pesachim': ['pesahim'], 'rosh-hashanah': ['rosh hashana'], 'taanit': ["ta'anit", 'taanis'],
    'megillah': ['megilla'], 'moed-katan': ["mo'ed katan"], 'chagigah': ['hagigah'], 'ketubot': ['kesubos'],
    'kiddushin': ['kidushin'], 'bava-kamma': ['baba kamma', 'bava kama'], 'bava-metzia': ['baba metzia', 'bava metsia'],
    'bava-batra': ['baba batra', 'bava basra'], 'makkot': ['makot'], 'shevuot': ['shevuos'],
    'avodah-zarah': ['avoda zara'], 'zevachim': ['zevahim'], 'menachot': ['menahot'], 'chullin': ['hullin'],
    'arakhin': ['arachin'], 'keritot': ['kerisos'], 'meilah': ["me'ilah"], 'niddah': ['nidah'],
}

HE_NUM = {1: 'א', 2: 'ב', 3: 'ג', 4: 'ד', 5: 'ה', 6: 'ו', 7: 'ז', 8: 'ח', 9: 'ט', 10: 'י', 20: 'כ', 30: 'ל', 40: 'מ',
          50: 'נ', 60: 'ס', 70: 'ע', 80: 'פ', 90: 'צ', 100: 'ק'}


def he_num(n):
    if n in (15, 16):
        return 'טו' if n == 15 else 'טז'
    s = ''
    for v in (100, 90, 80, 70, 60, 50, 40, 30, 20, 10):
        while n >= v:
            s += HE_NUM[v]
            n -= v
    if n in (15, 16):
        s += 'טו' if n == 15 else 'טז'
    elif n:
        s += HE_NUM[n]
    return s


EN_VT, AR_VT = 'William Davidson Edition - English', 'William Davidson Edition - Vocalized Aramaic'
ATTRIBUTION = ('The William Davidson Talmud (Koren – Steinsaltz), © Koren Publishers Jerusalem and Sefaria, released under '
               'CC-BY-NC 4.0. Non-commercial use only; attribute "The William Davidson Talmud" and link to sefaria.org.')


def main():
    reset_work(WORK)
    counts, licenses, toc, aliases = {'units': 0, 'passages': 0}, {}, [], {}
    for seder, seder_he, tractates in SEDARIM:
        for name in tractates:
            slug = slugify(name)
            cat = f'Talmud/Bavli/Seder {seder}/{name}'
            he_title, sides = None, set()
            for eid, lang_dir, vt, bold in (('en-davidson', 'English', EN_VT, True), ('ar-vocalized', 'Hebrew', AR_VT, False)):
                d = sefaria_version(cat, lang_dir, vt)
                licenses.setdefault(eid, license_text(d))
                if lang_dir == 'Hebrew' and d.get('heTitle'):
                    he_title = d['heTitle']
                for n, segs in enumerate(d['text']):
                    daf, side = n // 2 + 1, 'a' if n % 2 == 0 else 'b'
                    unit = f'{slug}:{daf}:{side}'
                    ps = []
                    for si, s in enumerate(segs or [], 1):
                        t = clean(s, bold=bold, italic=bold)
                        if t:
                            ps.append(passage(f'{unit}:{si}', t))
                    k = write_unit(WORK, eid, unit, ps)
                    if k:
                        counts['units'] += 1
                        counts['passages'] += k
                        sides.add((daf, side))
            children = [{'ref': f'{slug}:{daf}:{side}', 'label': {'en': f'{daf}{side}', 'he': f'{he_num(daf)} {"ע״א" if side == "a" else "ע״ב"}'}}
                        for daf, side in sorted(sides)]
            toc.append({'ref': slug, 'label': {'en': f'{seder} · {name}', 'he': f'{seder_he} · {he_title}' if he_title else seder_he},
                        'children': children})
            al = [name.lower(), f'tractate {name.lower()}', f'masechet {name.lower()}'] + EXTRA_ALIASES.get(slug, [])
            if he_title:
                al.append(he_title)
            aliases[slug] = sorted(set(al))
            # The reader's reference parser knows book/chapter/verse shapes, not daf+side; an alias per
            # daf side ("berakhot 2a" → berakhot:2:a) lets a typed "Berakhot 2a" open the right page.
            for daf, side in sorted(sides):
                aliases[f'{slug}:{daf}:{side}'] = [f'{name.lower()} {daf}{side}']
    manifest = {
        'schemaVersion': 1, 'workId': WORK, 'tradition': 'judaism', 'shelf': 'documents', 'families': [],
        'title': {'en': 'Talmud Bavli', 'he': 'תלמוד בבלי'},
        'subtitle': {'en': 'The Babylonian Talmud — 37 tractates with Gemara, in the William Davidson Edition'},
        'levels': [
            {'id': 'tractate', 'label': {'en': 'Tractate'}},
            {'id': 'daf', 'label': {'en': 'Daf'}},
            {'id': 'side', 'label': {'en': 'Side'}, 'isUnit': True},
            {'id': 'segment', 'label': {'en': 'Segment'}},
        ],
        'citation': {'format': '{tractate} {daf}{side}:{segment}', 'rangeFormat': '{tractate} {daf}{side}:{segment}–{segment2}',
                     'workAbbrev': {'en': 'Bavli'}},
        'toc': toc,
        'editions': [
            edition('en-davidson', EN_EDITION, 'English — William Davidson Edition (Koren – Steinsaltz)', 'translation',
                    licenses['en-davidson'], source_url('Talmud/Bavli/Seder <seder>/<tractate>', 'English', EN_VT),
                    notes=ATTRIBUTION + ' Bold marks the translated Talmud text; plain text is Rabbi Adin Even-Israel Steinsaltz\'s elucidation.'),
            edition('ar-vocalized', HE_EDITION, 'Aramaic / Hebrew — William Davidson Edition (vocalized)', 'original',
                    licenses['ar-vocalized'], source_url('Talmud/Bavli/Seder <seder>/<tractate>', 'Hebrew', AR_VT),
                    notes=ATTRIBUTION + ' Vocalization (nikud) by Dicta – the Israel Center for Text Analysis. Enlarged first-word markers removed.',
                    lang='arc'),
        ],
        'defaultEditions': ['ar-vocalized', 'en-davidson'],
        'aliases': aliases,
        'notes': {'en': 'Each unit is one side of a folio (daf); segments follow the Davidson edition\'s division. Folio 2a is the first page of every tractate.'},
    }
    write_manifest(WORK, manifest)
    report(WORK, counts)


if __name__ == '__main__':
    main()
