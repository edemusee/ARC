"""Psalm cycles → works/tehillim-daily (30-day cycle, keyed to the day of the Hebrew month) and
works/tehillim-weekly (7-day cycle, Sunday–Shabbat; not calendar keyed because the reader has no weekday key).

Text is copied from the already-converted works/tanakh editions he-nikud and en-jps1917. Unit = day; ref
`<day>:<psalm>-<verse>`; the first verse of each psalm carries the heading "Psalm n" / "תהלים n".
The 30-day division comes from Sefaria's schemas/Psalms.json (alts["30 Day Cycle"]).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (EN_EDITION, HE_EDITION, WORKS, edition, passage, report, reset_work, sefaria_path,
                    write_manifest, write_unit)

TANAKH = os.path.join(WORKS, 'tanakh')
HE_NUM = ['', 'א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט', 'י', 'יא', 'יב', 'יג', 'יד', 'טו', 'טז', 'יז', 'יח', 'יט',
          'כ', 'כא', 'כב', 'כג', 'כד', 'כה', 'כו', 'כז', 'כח', 'כט', 'ל']

WEEKLY = [(1, 'Sunday', 'יום ראשון', 1, 29), (2, 'Monday', 'יום שני', 30, 50), (3, 'Tuesday', 'יום שלישי', 51, 72),
          (4, 'Wednesday', 'יום רביעי', 73, 89), (5, 'Thursday', 'יום חמישי', 90, 106),
          (6, 'Friday', 'יום שישי', 107, 119), (7, 'Shabbat', 'שבת', 120, 150)]


def psalm(eid, n):
    with open(os.path.join(TANAKH, eid, f'psa-{n}.json'), encoding='utf-8') as f:
        return json.load(f)['passages']


def tanakh_edition(eid):
    with open(os.path.join(TANAKH, 'manifest.json'), encoding='utf-8') as f:
        m = json.load(f)
    return next(e for e in m['editions'] if e['id'] == eid)


def parse_ref(ref):
    """'Psalms 1' → (1, None, None); 'Psalms 119:1-96' → (119, 1, 96)."""
    m = re.fullmatch(r'Psalms? (\d+)(?::(\d+)-(\d+))?\s*', ref)
    return int(m.group(1)), (int(m.group(2)) if m.group(2) else None), (int(m.group(3)) if m.group(3) else None)


def build(work, title, subtitle, days, calendar):
    """days: list of (unitRef, labelEn, labelHe, [(psalm, fromVerse|None, toVerse|None)])."""
    reset_work(work)
    counts = {'units': 0, 'passages': 0}
    toc = []
    for ref, en, he, ranges in days:
        count = 0
        for eid, lang in (('he', 'he-nikud'), ('en', 'en-jps1917')):
            ps = []
            for n, v1, v2 in ranges:
                verses = psalm(lang, n)
                first = True
                for p in verses:
                    v = int(p['ref'].split(':')[2])
                    if (v1 and v < v1) or (v2 and v > v2):
                        continue
                    head = (f'Psalm {n}' if eid == 'en' else f'תהלים {n}') if first else None
                    if v1 and v1 > 1 and first:
                        head += f' (from verse {v1})' if eid == 'en' else f' (מפסוק {v1})'
                    ps.append(passage(f'{ref}:{n}-{v}', p['text'], head))
                    first = False
            k = write_unit(work, eid, ref, ps)
            counts['units'] += 1
            counts['passages'] += k
            count = max(count, k)
        toc.append({'ref': ref, 'label': {'en': en, 'he': he}, 'count': count})
    he_src, en_src = tanakh_edition('he-nikud'), tanakh_edition('en-jps1917')
    manifest = {
        'schemaVersion': 1, 'workId': work, 'tradition': 'judaism', 'shelf': 'devotional', 'families': [],
        'title': title, 'subtitle': {'en': subtitle},
        **({'calendar': 'hebrew', 'dateKey': '{D}'} if calendar else {}),
        'levels': [
            {'id': 'day', 'label': {'en': 'Day'}, 'isUnit': True},
            {'id': 'verse', 'label': {'en': 'Psalm–verse'}},
        ],
        'citation': {'format': '{work} {day} · {verse}', 'rangeFormat': '{work} {day} · {verse}–{verse2}',
                     'workAbbrev': {'en': 'Tehillim'}},
        'toc': toc,
        'editions': [
            edition('he', HE_EDITION, 'Hebrew — Tanach with Nikkud', 'original', he_src['license'], he_src['source'],
                    notes='Verses copied from the Tanakh work (edition he-nikud). Each passage ref is psalm-verse.'),
            edition('en', EN_EDITION, 'English — JPS 1917', 'translation', en_src['license'], en_src['source'],
                    notes='Verses copied from the Tanakh work (edition en-jps1917); Hebrew verse numbering, so superscriptions are verse 1.'),
        ],
        'defaultEditions': ['he', 'en'],
        'aliases': {d[0]: [d[1].lower(), f'day {d[0]}'] for d in days},
    }
    write_manifest(work, manifest)
    report(work, counts)


def main():
    schema = sefaria_path('schemas/Psalms.json')
    days = []
    for n in schema['alts']['30 Day Cycle']['nodes']:
        d = int(n['title'].split()[1])
        ranges = [parse_ref(r) for r in n['refs']]
        label = n['wholeRef'].replace('Psalms ', '').replace('Psalm ', '').strip().replace('-', '–')
        days.append((str(d), f'Day {d} (Psalms {label})', f'יום {HE_NUM[d]} (תהלים {label})', ranges))
    build('tehillim-daily', {'en': 'Tehillim — Monthly Cycle', 'he': 'תהלים לימי החודש'},
          'The Book of Psalms divided for reading over the 30 days of the Hebrew month', days, calendar=True)
    days = [(str(i), f'{en} (Psalms {a}–{b})', f'{he} (תהלים {a}–{b})', [(n, None, None) for n in range(a, b + 1)])
            for i, en, he, a, b in WEEKLY]
    build('tehillim-weekly', {'en': 'Tehillim — Weekly Cycle', 'he': 'תהלים לימי השבוע'},
          'The Book of Psalms divided for reading over the seven days of the week (Sunday–Shabbat)', days, calendar=False)


if __name__ == '__main__':
    main()
