"""Rambam's Thirteen Principles → works/rambam-13-principles.

Source: Rambam on Mishnah Sanhedrin 10:1 (the introduction to Perek Chelek), Sefaria text[9][0]: the
whole commentary as one unit "1" with one passage per paragraph. The thirteen principle paragraphs get a
heading ("First principle" …) taken from their opening bold phrase.
Editions: he (Vilna edition, public domain) and en (Sefaria Community Translation, CC0).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (EN_EDITION, HE_EDITION, clean, edition, license_text, passage, report, reset_work,
                    sefaria_version, source_url, write_manifest, write_unit)

WORK = 'rambam-13-principles'
CAT = 'Mishnah/Rishonim on Mishnah/Rambam/Seder Nezikin/Rambam on Mishnah Sanhedrin'
HE_VT, EN_VT = 'Vilna edition', 'Sefaria Community Translation'

ORDINALS = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth',
            'eleventh', 'twelfth', 'thirteenth']
HE_ORD = ['הראשון', 'השני', 'השלישי', 'הרביעי', 'החמישי', 'הששי', 'השביעי', 'השמיני', 'התשיעי', 'העשירי',
          'אחד עשר', 'שנים עשר', 'שלשה עשר']
EN_HEAD = re.compile(r'^<b>\s*The (\w+) principle\s*</b>\s*', re.I)
HE_HEAD = re.compile(r'^<b>\s*היסוד ([^<]+?)\s*</b>\s*(?:<br\s*/?>)?\s*')


def split_heading(raw, lang):
    """Return (heading, remaining raw html) when the paragraph opens a principle, else (None, raw)."""
    if lang == 'en':
        m = EN_HEAD.match(raw)
        if m and m.group(1).lower() in ORDINALS:
            n = ORDINALS.index(m.group(1).lower()) + 1
            return f'{m.group(1).capitalize()} principle', raw[m.end():], n
    else:
        m = HE_HEAD.match(raw)
        if m and m.group(1).strip() in HE_ORD:
            n = HE_ORD.index(m.group(1).strip()) + 1
            return f'היסוד {m.group(1).strip()}', raw[m.end():], n
    return None, raw, None


def main():
    reset_work(WORK)
    counts, licenses, found = {'units': 0, 'passages': 0}, {}, {}
    for eid, lang_dir, vt, lang in (('he', 'Hebrew', HE_VT, 'he'), ('en', 'English', EN_VT, 'en')):
        d = sefaria_version(CAT, lang_dir, vt)
        licenses[eid] = license_text(d)
        segs = d['text'][9][0]
        ps, seen = [], []
        for i, raw in enumerate(segs, 1):
            heading, rest, n = split_heading(raw, lang)
            t = clean(rest)
            if not t:
                continue
            if heading:
                seen.append(n)
            ps.append(passage(f'1:{i}', t, heading))
        found[eid] = seen
        k = write_unit(WORK, eid, '1', ps)
        counts['units'] += 1
        counts['passages'] += k
    for eid, seen in found.items():
        assert seen == list(range(1, 14)), (eid, seen)
    manifest = {
        'schemaVersion': 1, 'workId': WORK, 'tradition': 'judaism', 'shelf': 'documents', 'families': [],
        'title': {'en': 'Rambam\'s Thirteen Principles of Faith', 'he': 'שלושה עשר עיקרים לרמב״ם'},
        'subtitle': {'en': 'Maimonides\' introduction to Perek Chelek (Commentary on Mishnah Sanhedrin 10:1), c. 1168'},
        'levels': [
            {'id': 'section', 'label': {'en': 'Section'}, 'isUnit': True},
            {'id': 'paragraph', 'label': {'en': 'Paragraph'}},
        ],
        'citation': {'format': '{work} {paragraph}', 'rangeFormat': '{work} {paragraph}–{paragraph2}',
                     'workAbbrev': {'en': '13 Principles'}},
        'toc': [{'ref': '1', 'label': {'en': 'Introduction to Perek Chelek and the Thirteen Principles', 'he': 'הקדמה לפרק חלק'},
                 'count': len(segs)}],
        'editions': [
            edition('he', HE_EDITION, 'Hebrew — Vilna edition (Ibn Tibbon translation)', 'original', licenses['he'],
                    source_url(CAT, 'Hebrew', HE_VT),
                    notes='Shmuel ibn Tibbon\'s medieval Hebrew translation of the Judeo-Arabic original, from the Vilna Mishnah. Paragraphs 16–30 contain the thirteen principles.'),
            edition('en', EN_EDITION, 'English — Sefaria Community Translation', 'translation', licenses['en'],
                    source_url(CAT, 'English', EN_VT),
                    notes='Sefaria Community Translation (CC0). Paragraphs 16–30 contain the thirteen principles.'),
        ],
        'defaultEditions': ['he', 'en'],
        'aliases': {'1': ['principles', 'thirteen principles', '13 principles', 'ikkarim', 'yesodot', 'perek chelek', 'chelek']},
        'notes': {'en': 'The thirteen principles are the climax of Maimonides\' essay on the World to Come that opens his commentary on the tenth chapter of Sanhedrin.'},
    }
    write_manifest(WORK, manifest)
    report(WORK, counts)


if __name__ == '__main__':
    main()
