"""Weekly Torah portions → works/parashah.

From hebcal-leyning's src/aliyot.json (BSD-2-Clause): the 54 parashiyot plus the 7 doubled portions, in
Torah order (each doubled portion right after its second component). Levels parashah(unit) / aliyah; one
passage per aliyah whose text is the verse range as a readable string (the Torah text itself is in the
Tanakh work, not duplicated here): refs `bereshit:1`…`bereshit:7`, `bereshit:m` (maftir), `bereshit:h`
(haftarah, with the Sephardic variant where it differs), `bereshit:w1`…`w3` (Monday/Thursday reading).
Editions en and he (Hebrew book names and letter numerals). Hebrew parashah names from Sefaria's
schemas/<Book>.json alts.Parasha.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (EN_EDITION, HE_EDITION, HEBCAL_LEYNING, WORKS, edition, passage, report, reset_work,
                    sefaria_path, slugify, write_manifest, write_unit)

WORK = 'parashah'
TORAH = {1: ('gen', 'Genesis'), 2: ('exo', 'Exodus'), 3: ('lev', 'Leviticus'), 4: ('num', 'Numbers'), 5: ('deu', 'Deuteronomy')}
SEFARIA_BOOK = {1: 'Genesis', 2: 'Exodus', 3: 'Leviticus', 4: 'Numbers', 5: 'Deuteronomy'}
HEBCAL_TO_SEFARIA = {'Lech-Lecha': 'Lech Lecha', "Ha'azinu": "Ha'Azinu", 'Vezot Haberakhah': "V'Zot HaBerachah"}
HAFT_BOOKS = {'Joshua': 'jos', 'Judges': 'jdg', 'I Samuel': '1sa', 'II Samuel': '2sa', 'I Kings': '1ki', 'II Kings': '2ki',
              'Isaiah': 'isa', 'Jeremiah': 'jer', 'Ezekiel': 'ezk', 'Hosea': 'hos', 'Joel': 'jol', 'Amos': 'amo',
              'Obadiah': 'oba', 'Jonah': 'jon', 'Micah': 'mic', 'Nahum': 'nam', 'Habakkuk': 'hab', 'Zephaniah': 'zep',
              'Haggai': 'hag', 'Zechariah': 'zec', 'Malachi': 'mal'}
HE_ALIYAH = ['', 'כהן', 'לוי', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שביעי']

ONES = ['', 'א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט']
TENS = ['', 'י', 'כ', 'ל', 'מ', 'נ', 'ס', 'ע', 'פ', 'צ']
HUNDREDS = ['', 'ק', 'ר', 'ש', 'ת']


def gematria(n):
    n = int(n)
    s = ''
    while n >= 400:
        s += 'ת'
        n -= 400
    s += HUNDREDS[n // 100]
    n %= 100
    if n in (15, 16):
        s += 'טו' if n == 15 else 'טז'
    else:
        s += TENS[n // 10] + ONES[n % 10]
    return s


def he_cv(cv):
    c, v = cv.split(':')
    return f'{gematria(c)}:{gematria(v)}'


def rng(book_en, book_he, a, b, lang):
    if lang == 'en':
        return f'{book_en} {a} – {b}' if a != b else f'{book_en} {a}'
    return f'{book_he} {he_cv(a)}–{he_cv(b)}' if a != b else f'{book_he} {he_cv(a)}'


def haft_text(h, books_he, lang):
    parts = h if isinstance(h, list) else [h]
    out = []
    for p in parts:
        code = HAFT_BOOKS[p['k']]
        name = p['k'].replace('I Kings', '1 Kings').replace('II Kings', '2 Kings').replace('I Samuel', '1 Samuel').replace('II Samuel', '2 Samuel')
        out.append(rng(name, books_he[code], p['b'], p['e'], lang))
    return '; '.join(out)


def main():
    with open(os.path.join(HEBCAL_LEYNING, 'src', 'aliyot.json'), encoding='utf-8') as f:
        aliyot = json.load(f)
    with open(os.path.join(WORKS, 'tanakh', 'manifest.json'), encoding='utf-8') as f:
        books_he = {k: v['he'] for k, v in json.load(f)['books'].items()}
    he_names = {}
    for b in SEFARIA_BOOK.values():
        for n in sefaria_path(f'schemas/{b}.json')['alts']['Parasha']['nodes']:
            he_names[n['sharedTitle']] = n['heTitle']

    singles = sorted((k for k, v in aliyot.items() if not v.get('combined')), key=lambda k: aliyot[k]['num'])
    doubled = {v['p2']: k for k, v in aliyot.items() if v.get('combined')}
    order = []
    for k in singles:
        order.append(k)
        if k in doubled:
            order.append(doubled[k])

    reset_work(WORK)
    counts, toc, aliases = {'units': 0, 'passages': 0}, [], {}
    for name in order:
        raw = aliyot[name]
        slug = slugify(name)
        code, book_en = TORAH[raw['book']]
        book_he = books_he[code]
        if raw.get('combined'):
            he_name = he_names[HEBCAL_TO_SEFARIA.get(raw['p1'], raw['p1'])] + '־' + he_names[HEBCAL_TO_SEFARIA.get(raw['p2'], raw['p2'])]
            haft_src = aliyot[raw['p1'] if raw['p1'] == 'Nitzavim' else raw['p2']]
            num_label = f'{raw["num1"]}–{raw["num2"]}'
        else:
            he_name = he_names[HEBCAL_TO_SEFARIA.get(name, name)]
            haft_src = raw
            num_label = str(raw['num'])
        fk = raw['fullkriyah']
        whole = f'{fk["1"][0]} – {fk["7"][1]}'
        for lang in ('en', 'he'):
            ps = []
            for i in range(1, 8):
                a, b = fk[str(i)][0], fk[str(i)][1]
                note = fk[str(i)][2] if len(fk[str(i)]) > 2 else None
                t = rng(book_en, book_he, a, b, lang)
                if note:
                    t += f' ({note})' if lang == 'en' else f' ({note})'
                ps.append(passage(f'{slug}:{i}', t, f'Aliyah {i}' if lang == 'en' else HE_ALIYAH[i]))
            if 'M' in fk:
                ps.append(passage(f'{slug}:m', rng(book_en, book_he, fk['M'][0], fk['M'][1], lang), 'Maftir' if lang == 'en' else 'מפטיר'))
            if haft_src.get('haft'):
                t = haft_text(haft_src['haft'], books_he, lang)
                if haft_src.get('seph'):
                    t += ('\nSephardic custom: ' if lang == 'en' else '\nמנהג הספרדים: ') + haft_text(haft_src['seph'], books_he, lang)
                ps.append(passage(f'{slug}:h', t, 'Haftarah' if lang == 'en' else 'הפטרה'))
            wk = raw.get('weekday') or (aliyot[raw['p1']].get('weekday') if raw.get('combined') else None)
            if wk:
                for i in range(1, 4):
                    ps.append(passage(f'{slug}:w{i}', rng(book_en, book_he, wk[str(i)][0], wk[str(i)][1], lang),
                                      f'Weekday reading, aliyah {i}' if lang == 'en' else f'שני וחמישי: {HE_ALIYAH[i]}'))
            k = write_unit(WORK, lang, slug, ps)
            counts['units'] += 1
            counts['passages'] += k
        toc.append({'ref': slug, 'label': {'en': f'{num_label}. {name} ({book_en} {whole})', 'he': f'{he_name} ({book_he} {he_cv(fk["1"][0])}–{he_cv(fk["7"][1])})'},
                    'count': k})
        al = {name.lower(), f'parashat {name.lower()}', f'parshat {name.lower()}', name.lower().replace("'", ''), he_name}
        if raw.get('combined'):
            al.add(f'{raw["p1"].lower()} {raw["p2"].lower()}')
        aliases[slug] = sorted(al)
    manifest = {
        'schemaVersion': 1, 'workId': WORK, 'tradition': 'judaism', 'shelf': 'documents', 'families': [],
        'title': {'en': 'Weekly Torah Portions', 'he': 'פרשות השבוע'},
        'subtitle': {'en': 'The 54 parashiyot and 7 doubled portions, with aliyah divisions, maftir and haftarah'},
        'levels': [
            {'id': 'parashah', 'label': {'en': 'Parashah'}, 'isUnit': True},
            {'id': 'aliyah', 'label': {'en': 'Aliyah'}},
        ],
        'citation': {'format': '{work} {parashah} · {aliyah}', 'rangeFormat': '{work} {parashah} · {aliyah}–{aliyah2}',
                     'workAbbrev': {'en': 'Parashat'}},
        'toc': toc,
        'editions': [
            edition('en', EN_EDITION, 'English (reading table)', 'original', 'BSD-2-Clause (hebcal/leyning data); Hebrew parashah names from Sefaria schemas',
                    'https://github.com/hebcal/leyning (src/aliyot.json)',
                    notes='Each passage gives the verse range of one aliyah according to the full Shabbat reading; "m" is the maftir, "h" the haftarah (Ashkenazi, with the Sephardic variant where it differs), "w1–w3" the Monday/Thursday reading. Open the Tanakh work to read the text.'),
            edition('he', HE_EDITION, 'Hebrew (reading table)', 'original', 'BSD-2-Clause (hebcal/leyning data); Hebrew parashah names from Sefaria schemas',
                    'https://github.com/hebcal/leyning (src/aliyot.json)',
                    notes='Same reading table with Hebrew book names and letter numerals.'),
        ],
        'defaultEditions': ['en', 'he'],
        'aliases': aliases,
        'notes': {'en': 'Doubled portions are listed after their second half; for them the haftarah follows the second portion (Nitzavim for Nitzavim–Vayeilech), as in hebcal. Special-Shabbat haftarot are not shown.'},
    }
    write_manifest(WORK, manifest)
    report(WORK, counts)


if __name__ == '__main__':
    main()
