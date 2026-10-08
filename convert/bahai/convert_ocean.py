#!/usr/bin/env python3
"""Convert the Bahá'í core works from chadananda/ocean-library (published/<id>/<id>-en.html) into works/.

Usage (from the reader root):  python3 -I convert/bahai/convert_ocean.py [--only id1,id2]

Works: kitab-i-aqdas, kitab-i-iqan, hidden-words, gleanings, prayers-and-meditations, some-answered-questions,
will-and-testament. Paragraph numbers are the `div.par id` numbers of the source, which follow the Bahá'í
Reference Library numbering.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

ITEM_RE = re.compile(r"""
  <section\ class='content'(?P<sattrs>[^>]*)>
| <div\ class='section_header(?P<hcls>[^']*)'[^>]*>(?P<hbody>.*?)</div>\s*<!--\ section_header
| <div\ id='(?P<pid>[^']*)'\ class='(?P<pcls>par[^']*)'>(?P<pbody>.*?)</div></div>\s*<!--\ end\ par
| <aside\ class='fn'\ id='(?P<fid>[^']*)'[^>]*>(?P<fbody>.*?)</aside>
""", re.S | re.X)

ROMAN = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
         (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]


def roman(n):
    s = ''
    for v, r in ROMAN:
        while n >= v:
            s += r
            n -= v
    return s


def load(book):
    path = os.path.join(C.OCEAN, book, f'{book}-en.html')
    with open(path, encoding='utf-8') as f:
        h = f.read()
    items, notes = [], {}
    for m in ITEM_RE.finditer(h):
        if m.group('sattrs') is not None:
            a = m.group('sattrs')
            sid = re.search(r"id='([^']*)'", a)
            st = re.search(r"data-sectiontype='([^']*)'", a)
            items.append(('section', sid.group(1) if sid else '', st.group(1) if st else ''))
        elif m.group('hbody') is not None:
            hs = re.findall(r"<h3 class='([^']*)'[^>]*>(.*?)</h3>", m.group('hbody'), re.S)
            items.append(('header', {c.split()[0]: C.plain(b) for c, b in hs}))
        elif m.group('pid') is not None:
            items.append(('par', m.group('pid'), m.group('pcls'), m.group('pbody')))
        else:
            fid = re.sub(r'^fn', '', m.group('fid'))
            t, _ = C.finish(C.extract(m.group('fbody')))
            if t:
                notes[fid] = t
    return items, notes, f'{C.OCEAN_REPO}/{book}/{book}-en.html'


def passage(ref, body, notes, orphan_sink=None):
    text, anchors = C.finish(C.extract(body))
    text = text.replace('\x07', '').replace('\x08', '')
    if not text:
        return None
    p = {'ref': ref, 'text': text}
    ns = [{'at': off, 'text': notes[fid]} for fid, off in anchors if fid in notes]
    if ns:
        p['notes'] = ns
    return p


def chunk(nums, size=20, min_tail=8):
    out, cur = [], []
    for n in nums:
        cur.append(n)
        if len(cur) == size:
            out.append(cur)
            cur = []
    if cur:
        if out and len(cur) < min_tail:
            out[-1].extend(cur)
        else:
            out.append(cur)
    return out


def rng_label(nums):
    return f'¶ {nums[0]}–{nums[-1]}' if len(nums) > 1 else f'¶ {nums[0]}'


# ----------------------------------------------------------------- Kitáb-i-Aqdas

def convert_aqdas():
    work = 'kitab-i-aqdas'
    items, notes, src = load('baha-ka')
    C.reset_work(work)
    body, qa = {}, {}
    for it in items:
        if it[0] != 'par':
            continue
        pid, _cls, pbody = it[1], it[2], it[3]
        if re.fullmatch(r'\d+', pid):
            body[int(pid)] = pbody
        elif re.fullmatch(r'qa\.\d+', pid):
            qa[int(pid[3:])] = pbody
        # '???' paragraphs duplicate the <aside> notes and are dropped
    toc, units, count = [], 0, 0
    for i, nums in enumerate(chunk(sorted(body)), 1):
        ps = [p for p in (passage(f'{i}:{n}', body[n], notes) for n in nums) if p]
        if i == 1:
            ps[0]['heading'] = 'The Kitáb-i-Aqdas — The Most Holy Book'
        C.write_unit(work, 'en', str(i), ps)
        toc.append({'ref': str(i), 'label': {'en': rng_label(nums)}, 'count': len(ps)})
        units += 1
        count += len(ps)
    ps = [p for p in (passage(f'qa:{n}', qa[n], notes) for n in sorted(qa)) if p]
    ps[0]['heading'] = 'Questions and Answers'
    C.write_unit(work, 'en', 'qa', ps)
    toc.append({'ref': 'qa', 'label': {'en': 'Questions and Answers'}, 'count': len(ps)})
    units += 1
    count += len(ps)
    ed = C.edition('en', 'English (Bahá’í World Centre, 1992)', 'translation', src,
                   notes='Paragraph numbers follow the 1992 edition and the Bahá’í Reference Library; the explanatory Notes of that '
                         'edition are attached as footnotes. The Synopsis and Codification is not included.')
    m = C.manifest(work, 'scripture', 'The Kitáb-i-Aqdas', 'The Most Holy Book — Bahá’u’lláh',
                   [{'id': 'part', 'label': {'en': 'Part'}, 'isUnit': True}, {'id': 'paragraph', 'label': {'en': 'Paragraph'}}],
                   {'format': '{work} ¶{paragraph}', 'rangeFormat': '{work} ¶{paragraph}–{paragraph2}', 'workAbbrev': {'en': 'Kitáb-i-Aqdas'}},
                   toc, [ed], ['en'],
                   aliases={'1': ['aqdas', 'kitab-i-aqdas', 'most holy book'], 'qa': ['questions and answers', 'q&a', 'q and a']},
                   notes='The Most Holy Book of Bahá’u’lláh (1873), with the Questions and Answers; shown in groups of twenty numbered paragraphs.')
    C.write_manifest(work, m)
    C.report(work, 'scripture', ['en'], units, count)


# ----------------------------------------------------------------- Kitáb-i-Íqán

def convert_iqan():
    work = 'kitab-i-iqan'
    items, notes, src = load('baha-ki')
    C.reset_work(work)
    body, part_of, part, part_names = {}, {}, 0, {}
    for it in items:
        if it[0] == 'header':
            t = it[1].get('title') or it[1].get('sectionnum') or ''
            if 'Part' in t:
                part += 1
                part_names[part] = t
        elif it[0] == 'par' and re.fullmatch(r'\d+', it[1]):
            body[int(it[1])] = it[3]
            part_of[int(it[1])] = part or 1
    toc, units, count = [], 0, 0
    for pt in sorted(part_names):
        nums = [n for n in sorted(body) if part_of[n] == pt]
        children = []
        for i, group in enumerate(chunk(nums), 1):
            unit = f'{pt}-{i}'
            ps = [p for p in (passage(f'{unit}:{n}', body[n], notes) for n in group) if p]
            if i == 1:
                ps[0]['heading'] = part_names[pt]
            C.write_unit(work, 'en', unit, ps)
            children.append({'ref': unit, 'label': {'en': rng_label(group)}, 'count': len(ps)})
            units += 1
            count += len(ps)
        toc.append({'ref': str(pt), 'label': {'en': part_names[pt].replace('The Kitáb-i-Íqán, ', '')}, 'children': children})
    ed = C.edition('en', 'English (Shoghi Effendi)', 'translation', src,
                   notes='Translated by Shoghi Effendi (1931). Paragraph numbers follow the Bahá’í Reference Library; the Qur’án '
                         'references of the printed edition are attached as footnotes.')
    m = C.manifest(work, 'scripture', 'The Kitáb-i-Íqán', 'The Book of Certitude — Bahá’u’lláh',
                   [{'id': 'section', 'label': {'en': 'Section'}, 'isUnit': True}, {'id': 'paragraph', 'label': {'en': 'Paragraph'}}],
                   {'format': '{work} ¶{paragraph}', 'rangeFormat': '{work} ¶{paragraph}–{paragraph2}', 'workAbbrev': {'en': 'Kitáb-i-Íqán'}},
                   toc, [ed], ['en'],
                   aliases={'1-1': ['iqan', 'kitab-i-iqan', 'book of certitude', 'part one'], '2-1': ['part two']},
                   notes='The Book of Certitude (1862), in two parts; shown in groups of twenty numbered paragraphs.')
    C.write_manifest(work, m)
    C.report(work, 'scripture', ['en'], units, count)


# ----------------------------------------------------------------- Hidden Words

def convert_hidden_words():
    work = 'hidden-words'
    items, notes, src = load('baha-hw')
    C.reset_work(work)
    # id → body for en (a0, a1…, p0, p1…, p19.1, ???) and originals (a1-ar, p1-pe…)
    en, orig, closing = {'arabic': {}, 'persian': {}}, {'arabic': {}, 'persian': {}}, {'en': None, 'fa': None}
    subhead = {'en': {'arabic': {}, 'persian': {}}, 'orig': {'arabic': {}, 'persian': {}}}
    part = None
    for it in items:
        if it[0] == 'section':
            part = 'arabic' if it[1] == 'hw_1' else 'persian'
            continue
        if it[0] != 'par':
            continue
        pid, pbody = it[1], it[3]
        m = re.fullmatch(r'(a|p|aa)(\d+)(?:\.(\d+))?(-ar|-pe)?', pid)
        if pid == '???':
            t = C.plain(pbody)
            if t:
                closing['fa' if re.search(r'[؀-ۿ]', t) else 'en'] = t
            continue
        if not m:
            continue
        n, sub, lang = int(m.group(2)), m.group(3), m.group(4)
        target = orig if lang else en
        if sub:  # p19.1: the line introducing the next Hidden Word
            subhead['orig' if lang else 'en'][part][n + 1] = C.plain(pbody)
            continue
        target[part][n] = pbody

    def build(ed_id, part, data, heads, closing_text):
        ps = []
        for n in sorted(data):
            ref = f'{part}:{"preamble" if n == 0 else n}'
            p = passage(ref, data[n], notes)
            if not p:
                continue
            p['text'] = re.sub(r'^\([۰-۹٠-٩0-9]+\)\s*', '', p['text'])
            if ed_id in ('ar', 'fa'):
                p['text'] = p['text'].replace('*', '٭')
            if n in heads:
                p['heading'] = heads[n]
            ps.append(p)
        if closing_text:
            ps.append({'ref': f'{part}:closing', 'text': closing_text.replace('*', '٭') if ed_id == 'fa' else closing_text})
        C.write_unit(work, ed_id, part, ps)
        return len(ps)

    count = 0
    count += build('en', 'arabic', en['arabic'], subhead['en']['arabic'], None)
    count += build('en', 'persian', en['persian'], subhead['en']['persian'], closing['en'])
    count += build('ar', 'arabic', orig['arabic'], subhead['orig']['arabic'], None)
    count += build('fa', 'persian', orig['persian'], subhead['orig']['persian'], closing['fa'])
    toc = [{'ref': 'arabic', 'label': {'en': 'Part One: From the Arabic', 'ar': 'من العربية'}, 'count': len(en['arabic'])},
           {'ref': 'persian', 'label': {'en': 'Part Two: From the Persian', 'fa': 'از فارسی'}, 'count': len(en['persian']) + 1}]
    eds = [
        C.edition('en', 'English (Shoghi Effendi)', 'translation', src,
                  notes='Translated by Shoghi Effendi. The Arabic part has 71 Hidden Words, the Persian part 82, each preceded by its preamble.'),
        C.edition('ar', 'Arabic (original)', 'original', src, base=C.AR_EDITION, available=['arabic']),
        C.edition('fa', 'Persian (original)', 'original', src, base=C.FA_EDITION, available=['persian']),
    ]
    m = C.manifest(work, 'scripture', 'The Hidden Words', 'Bahá’u’lláh',
                   [{'id': 'part', 'label': {'en': 'Part'}, 'isUnit': True}, {'id': 'number', 'label': {'en': 'Number'}}],
                   {'format': '{work} {part} {number}', 'rangeFormat': '{work} {part} {number}–{number2}', 'workAbbrev': {'en': 'Hidden Words'}},
                   toc, eds, ['en', 'ar'],
                   aliases={'arabic': ['arabic', 'arabic hidden words', 'from the arabic', 'ahw', 'hw arabic'],
                            'persian': ['persian', 'persian hidden words', 'from the persian', 'phw', 'hw persian']},
                   notes='The Hidden Words of Bahá’u’lláh (c. 1858): 71 from the Arabic and 82 from the Persian, with the original text alongside.')
    C.write_manifest(work, m)
    C.report(work, 'scripture', ['en', 'ar', 'fa'], 2, count)


# ----------------------------------------------------------------- numbered selections (Gleanings, P&M, SAQ)

def convert_selections(work, book, title, subtitle, abbrev, section_label, head_fn, label_fn, ed_label, ed_notes, shelf, aliases_fn, notes):
    items, notes_map, src = load(book)
    C.reset_work(work)
    sections = []  # [n, header, {par: body}]
    cur = None
    for it in items:
        if it[0] == 'section':
            cur = None
            continue
        if it[0] == 'header':
            num = it[1].get('sectionnum', '')
            cur = {'num': num, 'title': it[1].get('title', ''), 'pars': {}}
            sections.append(cur)
        elif it[0] == 'par' and cur is not None:
            m = re.fullmatch(r'(\d+)\.(\d+)', it[1])
            if m:
                cur['n'] = int(m.group(1))
                cur['pars'][int(m.group(2))] = it[3]
    toc, aliases, units, count = [], {}, 0, 0
    for s in sections:
        if 'n' not in s:
            continue  # foreword / preface (SAQ) carry no numbered paragraphs
        n = s['n']
        ps = [p for p in (passage(f'{n}:{k}', s['pars'][k], notes_map) for k in sorted(s['pars'])) if p]
        head = head_fn(n, s)
        if head:
            ps[0]['heading'] = head
        C.write_unit(work, 'en', str(n), ps)
        toc.append({'ref': str(n), 'label': {'en': label_fn(n, s)}, 'count': len(ps)})
        aliases[str(n)] = aliases_fn(n, s)
        units += 1
        count += len(ps)
    ed = C.edition('en', ed_label, 'translation', src, notes=ed_notes)
    m = C.manifest(work, shelf, title, subtitle,
                   [{'id': 'section', 'label': {'en': section_label}, 'isUnit': True}, {'id': 'paragraph', 'label': {'en': 'Paragraph'}}],
                   {'format': '{work} {section}:{paragraph}', 'rangeFormat': '{work} {section}:{paragraph}–{paragraph2}', 'workAbbrev': {'en': abbrev}},
                   toc, [ed], ['en'], aliases=aliases, notes=notes)
    C.write_manifest(work, m)
    C.report(work, shelf, ['en'], units, count)


def first_words(s, n=60):
    t = s['title'].rstrip('.… ')
    return (t[:n].rsplit(' ', 1)[0] + '…') if len(t) > n else t


def convert_gleanings():
    convert_selections('gleanings', 'baha-gwb', 'Gleanings from the Writings of Bahá’u’lláh', 'Translated by Shoghi Effendi',
                       'Gleanings', 'Section',
                       lambda n, s: roman(n), lambda n, s: f'{roman(n)}. {first_words(s)}',
                       'English (Shoghi Effendi)',
                       'Translated and compiled by Shoghi Effendi (1935). Sections I–CLXVI are numbered 1–166; paragraphs follow the Bahá’í Reference Library.',
                       'scripture', lambda n, s: [roman(n).lower(), f'section {n}', f'gleanings {n}'],
                       'One hundred sixty-six passages from the Writings of Bahá’u’lláh, selected and translated by Shoghi Effendi.')


def convert_pm():
    convert_selections('prayers-and-meditations', 'baha-pm', 'Prayers and Meditations by Bahá’u’lláh', 'Translated by Shoghi Effendi',
                       'P&M', 'Prayer',
                       lambda n, s: roman(n), lambda n, s: f'{roman(n)}. {first_words(s)}',
                       'English (Shoghi Effendi)',
                       'Translated and compiled by Shoghi Effendi (1938). Prayers I–CLXXXIV are numbered 1–184; paragraphs follow the Bahá’í Reference Library.',
                       'scripture', lambda n, s: [roman(n).lower(), f'prayer {n}', f'pm {n}'],
                       'One hundred eighty-four prayers and meditations of Bahá’u’lláh, selected and translated by Shoghi Effendi.')


def convert_saq():
    convert_selections('some-answered-questions', 'abd-saq', 'Some Answered Questions', '‘Abdu’l-Bahá, collected by Laura Clifford Barney',
                       'SAQ', 'Chapter',
                       lambda n, s: f'{n}. {s["title"]}', lambda n, s: f'{n}. {s["title"]}',
                       'English (2014 revised translation)',
                       'The 2014 revised translation published by the Bahá’í World Centre; chapter and paragraph numbers follow the Bahá’í Reference Library. '
                       'The foreword and Laura Clifford Barney’s preface are not included.',
                       'documents', lambda n, s: [f'chapter {n}', f'question {n}', f'saq {n}', C.slug(s['title']).replace('-', ' ')],
                       'Table talks of ‘Abdu’l-Bahá at ‘Akká (1904–1906), recorded by Laura Clifford Barney, in eighty-four chapters.')


# ----------------------------------------------------------------- Will and Testament

def convert_wt():
    work = 'will-and-testament'
    items, notes, src = load('abd-wt')
    C.reset_work(work)
    parts, cur = [], None
    for it in items:
        if it[0] == 'header':
            cur = {'name': it[1].get('sectionnum', ''), 'pars': {}}
            parts.append(cur)
        elif it[0] == 'par' and cur is not None and re.fullmatch(r'\d+', it[1]):
            cur['pars'][int(it[1])] = it[3]
    toc, units, count = [], 0, 0
    for i, pt in enumerate(parts, 1):
        ps = [p for p in (passage(f'{i}:{n}', pt['pars'][n], notes) for n in sorted(pt['pars'])) if p]
        ps[0]['heading'] = pt['name']
        C.write_unit(work, 'en', str(i), ps)
        toc.append({'ref': str(i), 'label': {'en': pt['name']}, 'count': len(ps)})
        units += 1
        count += len(ps)
    ed = C.edition('en', 'English', 'translation', src,
                   notes='Paragraph numbers run continuously through the three parts and follow the Bahá’í Reference Library.')
    m = C.manifest(work, 'documents', 'The Will and Testament of ‘Abdu’l-Bahá', 'In three parts',
                   [{'id': 'part', 'label': {'en': 'Part'}, 'isUnit': True}, {'id': 'paragraph', 'label': {'en': 'Paragraph'}}],
                   {'format': '{work} ¶{paragraph}', 'rangeFormat': '{work} ¶{paragraph}–{paragraph2}', 'workAbbrev': {'en': 'W&T'}},
                   toc, [ed], ['en'],
                   aliases={'1': ['part one', 'part 1', 'will and testament'], '2': ['part two', 'part 2'], '3': ['part three', 'part 3']},
                   notes='The Will and Testament of ‘Abdu’l-Bahá, the charter of the Bahá’í Administrative Order, in three parts.')
    C.write_manifest(work, m)
    C.report(work, 'documents', ['en'], units, count)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    a = ap.parse_args()
    only = set(a.only.split(',')) if a.only else None
    jobs = {'kitab-i-aqdas': convert_aqdas, 'kitab-i-iqan': convert_iqan, 'hidden-words': convert_hidden_words,
            'gleanings': convert_gleanings, 'prayers-and-meditations': convert_pm,
            'some-answered-questions': convert_saq, 'will-and-testament': convert_wt}
    for k, fn in jobs.items():
        if not only or k in only:
            fn()


if __name__ == '__main__':
    main()
