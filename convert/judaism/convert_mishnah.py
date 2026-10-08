"""Mishnah (63 tractates) → works/mishnah, and Pirkei Avot → works/pirkei-avot.

Editions: he (Torat Emet 357, vocalized, public domain) and en-kulp (Mishnah Yomit by Dr. Joshua Kulp,
CC-BY). Sefaria `text` is chapter → mishnah.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (EN_EDITION, HE_EDITION, clean, edition, license_text, passage, report, reset_work,
                    sefaria_version, slugify, source_url, write_manifest, write_unit)

SEDARIM = [
    ('Zeraim', 'זרעים', ['Berakhot', 'Peah', 'Demai', 'Kilayim', 'Sheviit', 'Terumot', 'Maasrot', 'Maaser Sheni',
                         'Challah', 'Orlah', 'Bikkurim']),
    ('Moed', 'מועד', ['Shabbat', 'Eruvin', 'Pesachim', 'Shekalim', 'Yoma', 'Sukkah', 'Beitzah', 'Rosh Hashanah',
                      "Ta'anit", 'Megillah', 'Moed Katan', 'Chagigah']),
    ('Nashim', 'נשים', ['Yevamot', 'Ketubot', 'Nedarim', 'Nazir', 'Sotah', 'Gittin', 'Kiddushin']),
    ('Nezikin', 'נזיקין', ['Bava Kamma', 'Bava Metzia', 'Bava Batra', 'Sanhedrin', 'Makkot', 'Shevuot', 'Eduyot',
                           'Avodah Zarah', 'Pirkei Avot', 'Horayot']),
    ('Kodashim', 'קדשים', ['Zevachim', 'Menachot', 'Chullin', 'Bekhorot', 'Arakhin', 'Temurah', 'Keritot',
                           'Meilah', 'Tamid', 'Middot', 'Kinnim']),
    ('Tahorot', 'טהרות', ['Kelim', 'Oholot', 'Negaim', 'Parah', 'Tahorot', 'Mikvaot', 'Niddah', 'Makhshirin',
                          'Zavim', 'Tevul Yom', 'Yadayim', 'Oktzin']),
]

EXTRA_ALIASES = {
    'berakhot': ['brachot', 'berachot', 'berakhoth', 'brakhot'],
    'peah': ['pe\'ah'],
    'sheviit': ['shevi\'it', 'shviit'],
    'maasrot': ['maaserot', 'ma\'asrot'],
    'maaser-sheni': ['ma\'aser sheni'],
    'challah': ['hallah'],
    'bikkurim': ['bikurim'],
    'shabbat': ['shabbos', 'shabat'],
    'eruvin': ['eiruvin'],
    'pesachim': ['pesahim'],
    'rosh-hashanah': ['rosh hashana', 'rosh ha-shanah'],
    'taanit': ['ta\'anit', 'taanis'],
    'megillah': ['megilla'],
    'moed-katan': ['mo\'ed katan'],
    'chagigah': ['hagigah'],
    'ketubot': ['ketuvot', 'kesubos'],
    'kiddushin': ['kidushin'],
    'bava-kamma': ['baba kamma', 'bava kama', 'baba kama'],
    'bava-metzia': ['baba metzia', 'bava metsia', 'baba metsia'],
    'bava-batra': ['baba batra', 'bava basra'],
    'makkot': ['makot', 'makkos'],
    'shevuot': ['shevu\'ot', 'shevuos'],
    'eduyot': ['eduyyot', 'eduyos'],
    'avodah-zarah': ['avoda zara', 'avodah zara'],
    'pirkei-avot': ['avot', 'avos', 'pirkei avos', 'ethics of the fathers', 'pirke avot'],
    'zevachim': ['zevahim'],
    'menachot': ['menahot'],
    'chullin': ['hullin'],
    'arakhin': ['arachin'],
    'keritot': ['kritot', 'kerisos'],
    'meilah': ['me\'ilah'],
    'middot': ['midot'],
    'kinnim': ['kinim'],
    'oholot': ['ohalot', 'ahilot'],
    'negaim': ['nega\'im'],
    'mikvaot': ['mikva\'ot', 'mikvaos'],
    'niddah': ['nidah'],
    'makhshirin': ['machshirin'],
    'oktzin': ['uktzin', 'oktsin', 'uktsin'],
}

HE_NUM = ['', 'א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט', 'י', 'יא', 'יב', 'יג', 'יד', 'טו', 'טז', 'יז', 'יח', 'יט',
          'כ', 'כא', 'כב', 'כג', 'כד', 'כה', 'כו', 'כז', 'כח', 'כט', 'ל', 'לא', 'לב', 'לג', 'לד', 'לה', 'לו']


def he_num(n):
    return HE_NUM[n] if n < len(HE_NUM) else str(n)


HE_VT, EN_VT = 'Torat Emet 357', 'Mishnah Yomit by Dr. Joshua Kulp'


def folder(seder, name):
    return f'Mishnah/Seder {seder}/' + ('Pirkei Avot' if name == 'Pirkei Avot' else f'Mishnah {name}')


def convert_tractate(work, prefix, cat, counts, licenses, written):
    """Write both editions for one tractate; returns (chapter count per edition max, Hebrew title).
    `written[editionId]` collects the unit refs that got a file."""
    he_title, n_ch = None, 0
    for eid, lang_dir, vt in (('he', 'Hebrew', HE_VT), ('en-kulp', 'English', EN_VT)):
        d = sefaria_version(cat, lang_dir, vt)
        licenses.setdefault(eid, license_text(d))
        if d.get('heTitle') and lang_dir == 'Hebrew':
            he_title = d['heTitle']
        text = d['text']
        n_ch = max(n_ch, len(text))
        for ci, mishnayot in enumerate(text, 1):
            ps = []
            for mi, m in enumerate(mishnayot or [], 1):
                t = clean(m)
                if t:
                    ps.append(passage(f'{prefix}{ci}:{mi}' if prefix else f'{ci}:{mi}', t))
            unit = f'{prefix}{ci}' if prefix else f'{ci}'
            n = write_unit(work, eid, unit, ps)
            if n:
                counts['units'] += 1
                counts['passages'] += n
                written.setdefault(eid, []).append(unit)
    return n_ch, he_title


def editions(licenses, cat_hint):
    return [
        edition('he', HE_EDITION, 'Hebrew — Torat Emet (vocalized)', 'original', licenses['he'],
                source_url(cat_hint, 'Hebrew', HE_VT),
                notes='Vocalized Mishnah text from the Torat Emet freeware edition (version 357) as distributed by Sefaria. Bikkurim chapter 4 (a later addition found in some printings) is not in this edition.'),
        edition('en-kulp', EN_EDITION, 'English — Mishnah Yomit (Dr. Joshua Kulp)', 'translation', licenses['en-kulp'],
                source_url(cat_hint, 'English', EN_VT),
                notes='Translation by Dr. Joshua Kulp for the Conservative Yeshiva\'s Mishnah Yomit programme, licensed CC-BY; explanatory commentary is not included.'),
    ]


def main():
    # ---- mishnah ----
    reset_work('mishnah')
    counts, licenses, toc, aliases, written = {'units': 0, 'passages': 0}, {}, [], {}, {}
    for seder, seder_he, tractates in SEDARIM:
        for name in tractates:
            slug = slugify(name)
            n_ch, he_title = convert_tractate('mishnah', f'{slug}:', folder(seder, name), counts, licenses, written)
            he_short = (he_title or '').replace('משנה ', '', 1)
            toc.append({
                'ref': slug,
                'label': {'en': f'{seder} · {name}', 'he': f'{seder_he} · {he_short}' if he_short else seder_he},
                'children': [{'ref': f'{slug}:{c}', 'label': {'en': f'Chapter {c}', 'he': f'פרק {he_num(c)}'}}
                             for c in range(1, n_ch + 1)],
            })
            al = [name.lower(), f'mishnah {name.lower()}', f'tractate {name.lower()}'] + EXTRA_ALIASES.get(slug, [])
            if he_short:
                al.append(he_short)
            aliases[slug] = sorted(set(al))
    manifest = {
        'schemaVersion': 1, 'workId': 'mishnah', 'tradition': 'judaism', 'shelf': 'documents', 'families': [],
        'title': {'en': 'The Mishnah', 'he': 'משנה'},
        'subtitle': {'en': 'The six orders (sedarim) and 63 tractates of the Oral Torah, redacted c. 200 CE'},
        'levels': [
            {'id': 'tractate', 'label': {'en': 'Tractate'}},
            {'id': 'chapter', 'label': {'en': 'Chapter'}, 'isUnit': True},
            {'id': 'mishnah', 'label': {'en': 'Mishnah'}},
        ],
        'citation': {'format': '{tractate} {chapter}:{mishnah}', 'rangeFormat': '{tractate} {chapter}:{mishnah}–{mishnah2}',
                     'workAbbrev': {'en': 'Mishnah'}},
        'toc': toc,
        'editions': editions(licenses, 'Mishnah/Seder <seder>/Mishnah <tractate>'),
        'defaultEditions': ['he', 'en-kulp'],
        'aliases': aliases,
        'notes': {'en': 'Tractates are listed in the traditional order of the six sedarim; Pirkei Avot is also available as its own work.'},
    }
    all_units = [c['ref'] for t in toc for c in t['children']]
    for e in manifest['editions']:
        if len(written.get(e['id'], [])) < len(all_units):
            e['available'] = written[e['id']]
    write_manifest('mishnah', manifest)
    report('mishnah', counts)

    # ---- pirkei-avot ----
    reset_work('pirkei-avot')
    counts, licenses = {'units': 0, 'passages': 0}, {}
    n_ch, he_title = convert_tractate('pirkei-avot', '', folder('Nezikin', 'Pirkei Avot'), counts, licenses, {})
    manifest = {
        'schemaVersion': 1, 'workId': 'pirkei-avot', 'tradition': 'judaism', 'shelf': 'documents', 'families': [],
        'title': {'en': 'Pirkei Avot', 'he': 'פרקי אבות'},
        'subtitle': {'en': 'Ethics of the Fathers — Mishnah tractate Avot, with the sixth chapter (Kinyan Torah)'},
        'levels': [
            {'id': 'chapter', 'label': {'en': 'Chapter'}, 'isUnit': True},
            {'id': 'mishnah', 'label': {'en': 'Mishnah'}},
        ],
        'citation': {'format': '{work} {chapter}:{mishnah}', 'rangeFormat': '{work} {chapter}:{mishnah}–{mishnah2}',
                     'workAbbrev': {'en': 'Avot'}},
        'toc': [{'ref': str(c), 'label': {'en': f'Chapter {c}', 'he': f'פרק {he_num(c)}'}} for c in range(1, n_ch + 1)],
        'editions': editions(licenses, 'Mishnah/Seder Nezikin/Pirkei Avot'),
        'defaultEditions': ['he', 'en-kulp'],
        'aliases': {str(c): [f'chapter {c}', f'perek {c}'] for c in range(1, n_ch + 1)},
        'notes': {'en': 'Chapter 6, Kinyan Torah, is a later baraita appended for the custom of studying one chapter each Shabbat between Pesach and Shavuot.'},
    }
    write_manifest('pirkei-avot', manifest)
    report('pirkei-avot', counts)


if __name__ == '__main__':
    main()
