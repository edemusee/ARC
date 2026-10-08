#!/usr/bin/env python3
"""Convert devotionals from open-christian-data into works/<workId>/ (shelf `devotional`).

  spurgeon-me   data/devotionals/spurgeons-morning-evening/morning-evening.json   (calendar-keyed, MM-DD:am/pm)
  daily-light   data/devotionals/daily-light/daily-light.json                     (calendar-keyed, MM-DD:am/pm)
  bcp-collects  data/prayers/bcp-1662/collects.json                              (collect (isUnit), paragraph)

Usage: python3 -I convert_devotionals.py [workId ...]
"""
import calendar
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import OCD, OCD_LICENSE, OCD_URL, edition, load_json, norm, reset_work, write_manifest, write_unit

TRAD = 'christianity'
DONE = []
DATE_LEVELS = [{'id': 'date', 'label': {'en': 'Date'}, 'isUnit': True},
               {'id': 'half', 'label': {'en': 'Reading'}}]


def date_toc(entries_by_date):
    toc = []
    for mm in range(1, 13):
        for dd in range(1, 32):
            key = f'{mm:02d}-{dd:02d}'
            if key in entries_by_date:
                toc.append({'ref': key, 'label': {'en': f'{calendar.month_name[mm]} {dd}'}, 'count': len(entries_by_date[key])})
    return toc


def calendar_manifest(work_id, title, subtitle, families, abbrev, toc, ed, notes=None):
    m = {'schemaVersion': 1, 'workId': work_id, 'tradition': TRAD, 'shelf': 'devotional', 'families': families,
         'title': {'en': title}, 'subtitle': {'en': subtitle}, 'calendar': 'gregory', 'dateKey': '{MM}-{DD}',
         'levels': DATE_LEVELS,
         'citation': {'format': '{work} {date} {half}', 'rangeFormat': '{work} {date} {half}', 'workAbbrev': {'en': abbrev}},
         'toc': toc, 'editions': [ed], 'defaultEditions': [ed['id']]}
    if notes:
        m['notes'] = {'en': notes}
    return m


# ---------------------------------------------------------------- Spurgeon
def convert_spurgeon():
    work_id = 'spurgeon-me'
    d = load_json(os.path.join(OCD, 'devotionals', 'spurgeons-morning-evening', 'morning-evening.json'))
    reset_work(work_id)
    by_date = {}
    for e in d['data']:
        key = f'{int(e["month"]):02d}-{int(e["day"]):02d}'
        half = 'am' if e['period'] == 'morning' else 'pm'
        ref_raw = norm((e.get('primary_reference') or {}).get('raw') or '')
        heading = ('Morning' if half == 'am' else 'Evening') + (f' — {ref_raw}' if ref_raw else '')
        blocks = [norm(b) for b in e['content_blocks'] if norm(b)]
        text = '\n\n'.join(blocks)
        by_date.setdefault(key, {})[half] = {'ref': f'{key}:{half}', 'heading': heading, 'text': text}
    for key, halves in by_date.items():
        write_unit(work_id, 'en', key, [halves[h] for h in ('am', 'pm') if h in halves])
    toc = date_toc(by_date)
    ed = edition('en', 'English (1865 text, CCEL)', 'original', OCD_LICENSE,
                 OCD_URL + '/blob/main/data/devotionals/spurgeons-morning-evening/morning-evening.json',
                 available=[t['ref'] for t in toc])
    write_manifest(work_id, calendar_manifest(work_id, 'Morning and Evening', 'C. H. Spurgeon, 1865', [], 'M&E', toc, ed))
    DONE.append((work_id, 'devotional', []))


# ---------------------------------------------------------------- Daily Light
REF_LINE = re.compile(r'^(?:[1-3]?\s?[A-Z][A-Za-z]{0,4}\.?\s+\d[\d:,\-; ]*\s*)+$')
TERMINAL = re.compile(r'[.!?][\'"’”)\]]*$')


def unwrap_daily_light(block):
    """The SWORD text is hard-wrapped at ~64 columns with a blank line after every line. Re-flow it:
    a line break is a paragraph break only when the line ends a sentence and is visibly short (unfilled),
    or when the next line starts a new quotation group ('--' joins verses inside a paragraph)."""
    lines = [l.strip() for l in block.split('\n') if l.strip()]
    ref_lines = []
    while len(lines) > 1 and REF_LINE.match(lines[-1]):
        ref_lines.insert(0, lines.pop())
    refs = ' '.join(ref_lines) if ref_lines else None
    paras, cur, last = [], '', ''
    for line in lines:
        if not cur:
            cur = last = line
            continue
        if TERMINAL.search(last) and len(last) <= 56 and not last.endswith('--') and not line.startswith('--'):
            paras.append(cur)
            cur = line
        elif last.endswith('-') and not last.endswith('--'):
            cur = cur + line          # hyphenated word split across lines
        else:
            cur = cur + ' ' + line
        last = line
    if cur:
        paras.append(cur)
    out = []
    for p in paras:
        p = re.sub(r'\s*--\s*', '—', p)
        p = re.sub(r'\[([^\[\]]+)\]', r'[[\1]]', p)       # KJV italics → translator-supplied words
        p = re.sub(r'\s+', ' ', p).strip()
        out.append(p)
    text = '\n\n'.join(out)
    if refs:
        text += '\n\n' + re.sub(r'\s+', ' ', refs)
    return norm(text)


def convert_daily_light():
    work_id = 'daily-light'
    d = load_json(os.path.join(OCD, 'devotionals', 'daily-light', 'daily-light.json'))
    reset_work(work_id)
    by_date = {}
    for e in d['data']:
        key = f'{int(e["month"]):02d}-{int(e["day"]):02d}'
        half = 'am' if e['period'] == 'morning' else 'pm'
        text = '\n\n'.join(unwrap_daily_light(b) for b in e['content_blocks'] if b.strip())
        heading = 'Morning' if half == 'am' else 'Evening'
        by_date.setdefault(key, {})[half] = {'ref': f'{key}:{half}', 'heading': heading, 'text': text}
    for key, halves in by_date.items():
        write_unit(work_id, 'en', key, [halves[h] for h in ('am', 'pm') if h in halves])
    toc = date_toc(by_date)
    ed = edition('en', 'English (KJV text, CrossWire SWORD module)', 'original', OCD_LICENSE,
                 OCD_URL + '/blob/main/data/devotionals/daily-light/daily-light.json', available=[t['ref'] for t in toc])
    write_manifest(work_id, calendar_manifest(work_id, 'Daily Light on the Daily Path', 'Samuel Bagster and Sons, 1875', [],
                                              'Daily Light', toc, ed,
                                              notes='Scripture only, arranged by theme; the references follow each reading. Words in double brackets are the KJV translators\' supplied words.'))
    DONE.append((work_id, 'devotional', []))


# ---------------------------------------------------------------- BCP collects
COLLECT_TITLE_FIX = {'sexagesima': 'The Sunday called Sexagesima, or the second Sunday before Lent'}


def fix_collect_text(t):
    t = norm(t)
    t = re.sub(r'^O([A-Z]{2,})\b', lambda m: 'O ' + m.group(1).capitalize(), t)     # drop-cap artifact 'OGOD'
    t = re.sub(r'^([A-Z]{2,})\b', lambda m: m.group(1).capitalize(), t)             # 'ALMIGHTY God' → 'Almighty God'
    return t


def convert_collects():
    work_id = 'bcp-collects'
    d = load_json(os.path.join(OCD, 'prayers', 'bcp-1662', 'collects.json'))
    reset_work(work_id)
    toc = []
    for p in d['data']:
        cid = p['prayer_id']
        assert re.fullmatch(r'[a-z0-9-]+', cid), cid
        title = COLLECT_TITLE_FIX.get(cid, norm(p['title']))
        paras = [fix_collect_text(b) for b in p['content_blocks'] if norm(b)]
        ps = [{'ref': f'{cid}:{j}', 'text': t} for j, t in enumerate(paras, 1)]
        ps[0]['heading'] = title
        write_unit(work_id, 'en', cid, ps)
        toc.append({'ref': cid, 'label': {'en': title}, 'count': len(ps)})
    ed = edition('en', 'English (1662)', 'original', OCD_LICENSE, OCD_URL + '/blob/main/data/prayers/bcp-1662/collects.json',
                 available=[t['ref'] for t in toc])
    m = {'schemaVersion': 1, 'workId': work_id, 'tradition': TRAD, 'shelf': 'devotional', 'families': ['anglican'],
         'title': {'en': 'The Collects'}, 'subtitle': {'en': 'Book of Common Prayer, 1662'},
         'levels': [{'id': 'collect', 'label': {'en': 'Collect'}, 'isUnit': True},
                    {'id': 'paragraph', 'label': {'en': 'Paragraph'}}],
         'citation': {'format': '{work} {collect}', 'rangeFormat': '{work} {collect}', 'workAbbrev': {'en': 'BCP Collects'}},
         'toc': toc, 'editions': [ed], 'defaultEditions': ['en'],
         'notes': {'en': 'The Collects for Sundays and Holy Days from the 1662 Book of Common Prayer, in the order of the church year.'}}
    write_manifest(work_id, m)
    DONE.append((work_id, 'devotional', ['anglican']))


JOBS = {'spurgeon-me': convert_spurgeon, 'daily-light': convert_daily_light, 'bcp-collects': convert_collects}


def main(argv):
    for wid in argv or list(JOBS):
        JOBS[wid]()
        print('ok', wid)
    print()
    for wid, shelf, fam in DONE:
        print(f'{wid}\t{shelf}\t{fam}')


if __name__ == '__main__':
    main(sys.argv[1:])
