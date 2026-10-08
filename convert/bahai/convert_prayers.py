#!/usr/bin/env python3
"""Bahá'í Prayers (bahai.org official HTML, as kept in dra11y/writings writings/html/prayers.html) → works/bahai-prayers.

Usage (from the reader root):  python3 -I convert/bahai/convert_prayers.py

Units are the sections of the prayer book (Short/Medium/Long Obligatory Prayer, then the General Prayers by
topic, the Occasional Prayers and the Special Tablets); passages are the paragraphs of each prayer. The class
names of the source are the obfuscated ones of bahai.org; the mapping follows dra11y/writings' PrayersVisitor.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

WORK = 'bahai-prayers'
SECTION = {'ub', 'c', 'l'}
SUBSECTION = {'xc', 'jb', 'c', 'kf', 'z', 'nb', 'zd', 'ub'}
TEACHING = {'c', 'kf', 'z', 'nb', 'zd', 'ub'}
AUTHOR = {'hb', 'ac'}
AUTHORS = ['Bahá’u’lláh', 'The Báb', '‘Abdu’l‑Bahá', '‘Abdu’l-Bahá']


def main():
    path = os.path.join(C.WRITINGS, 'prayers.html')
    with open(path, encoding='utf-8') as f:
        h = f.read()
    body = h[h.find('<body'):]
    end = body.find('<div class="bf">')
    notes_html = body[end:]
    body = body[:end]
    # endnotes: <a class="sf" id="ID"></a>TEXT<a class="jc" …>
    endnotes = {}
    for m in re.finditer(r'<p>\s*<a class="sf" id="(\d+)"></a>(.*?)<a class="jc"', notes_html, re.S):
        endnotes[m.group(1)] = C.plain(m.group(2))
    body = re.sub(r'<nav\b.*?</nav>', '', body, flags=re.S)
    body = re.sub(r'<div class="e">.*?<h1[^>]*>.*?</h1>\s*<p[^>]*>.*?</p>', '', body, count=1, flags=re.S)

    # ---- walk the paragraphs in order
    kinds = []          # [{'label', 'slug', 'units': [unit]}]
    cur_kind = None
    unit = None         # {'slug','label','prayers':[...], 'kind'}
    prayer = None       # {'paras': [], 'author': None, 'titles': [...]}
    pending_titles = []
    prologue = {'slug': 'prologue', 'label': 'Opening passages', 'prayers': [], 'standalone': True}
    units_by_slug = {}

    def new_unit(label, kind):
        nonlocal unit
        slug = C.slug(label)
        assert slug not in units_by_slug, slug
        unit = {'slug': slug, 'label': label, 'prayers': [], 'kind': kind}
        units_by_slug[slug] = unit
        kind['units'].append(unit)

    def close_prayer(author):
        nonlocal prayer
        if prayer and prayer['paras']:
            prayer['author'] = author
            (unit or prologue)['prayers'].append(prayer)
        prayer = None

    for m in re.finditer(r'<(h2|p)\b([^>]*)>(.*?)</\1>', body, re.S):
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        cls = set((re.search(r'class="([^"]*)"', attrs) or [None, ''])[1].split())
        inner = re.sub(r'<sup class="ye"><a href="#(\d+)">\d+</a></sup>', r'<a data-fnid="\1"></a>', inner)
        text, anchors = C.finish(C.extract(inner))
        if tag == 'h2':
            if 'g' in cls and 'c' in cls:
                close_prayer(None)
                cur_kind = {'label': text, 'slug': C.slug(text), 'units': []}
                kinds.append(cur_kind)
                unit = None
                if text == 'Obligatory Prayers':
                    new_unit('About the Obligatory Prayers', cur_kind)
            continue
        if not text:
            continue
        if AUTHOR <= cls:
            author = next((a for a in AUTHORS if a in text), text.lstrip('—').strip())
            close_prayer(author.replace('‘Abdu’l-Bahá', '‘Abdu’l‑Bahá'))
            continue
        if SECTION <= cls:
            close_prayer(None)
            new_unit(text, cur_kind)
            pending_titles = []
            continue
        if SUBSECTION <= cls or (TEACHING <= cls and 'jb' not in cls and 'c' in cls):
            close_prayer(None)
            pending_titles.append(text)
            continue
        if 'ub' in cls:  # instruction title line ("To be recited once in twenty-four hours, at noon")
            pending_titles.append(text)
            continue
        if cur_kind is None and unit is None:
            pass  # prologue
        if prayer is None:
            prayer = {'paras': [], 'author': None, 'titles': pending_titles}
            pending_titles = []
        instruction = bool({'cb', 'z'} & cls) or text.startswith('(')
        attribution = 'ac' in cls and 'z' in cls
        if attribution and prayer['paras']:
            prayer['paras'][-1]['text'] += '\n' + text
            continue
        if instruction and not text.startswith('*'):
            text = f'*{text}*'
        p = {'text': text}
        ns = [{'at': off, 'text': endnotes[fid]} for fid, off in anchors if fid in endnotes]
        if ns:
            p['notes'] = ns
        prayer['paras'].append(p)
    close_prayer(None)

    # ---- write
    C.reset_work(WORK)
    toc, aliases, units, count = [], {}, 0, 0

    def write(u):
        nonlocal units, count
        ps = []
        multi = len(u['prayers']) > 1
        prev_titles = []
        for k, pr in enumerate(u['prayers'], 1):
            head = [t for t in pr['titles'] if t not in prev_titles]  # a group title repeated on every prayer
            prev_titles = list(pr['titles'])
            tail = (f'Prayer {k}' if multi else '')
            if pr['author']:
                tail = f'{tail} · {pr["author"]}' if tail else pr['author']
            if tail:
                head.append(tail)
            for j, para in enumerate(pr['paras']):
                q = {'ref': f'{u["slug"]}:{len(ps) + 1}', 'text': para['text']}
                if 'notes' in para:
                    q['notes'] = para['notes']
                if j == 0 and head:
                    q['heading'] = ' — '.join(head)
                ps.append(q)
        C.write_unit(WORK, 'en', u['slug'], ps)
        units += 1
        count += len(ps)
        return {'ref': u['slug'], 'label': {'en': u['label']}, 'count': len(ps)}

    toc.append(write(prologue))
    aliases['prologue'] = ['blessed is the spot', 'prologue', 'intone o my servant']
    for kind in kinds:
        children = []
        for u in kind['units']:
            children.append(write(u))
            aliases[u['slug']] = [u['label'].lower(), u['slug'].replace('-', ' ')]
        toc.append({'ref': kind['slug'], 'label': {'en': kind['label']}, 'children': children})
    aliases['short-obligatory-prayer'] += ['obligatory prayer', 'short obligatory', 'noon prayer', 'daily prayer']
    aliases['medium-obligatory-prayer'] += ['medium obligatory']
    aliases['long-obligatory-prayer'] += ['long obligatory']
    if 'the-departed' in units_by_slug:
        aliases['the-departed'] += ['prayer for the dead', 'departed', 'dead']
    aliases['tablet-of-ahmad'] += ['tablet of ahmad', 'ahmad']
    aliases['healing'] += ['long healing prayer', 'healing prayer']
    aliases['the-fast'] += ['fast', 'fasting']
    aliases['naw-ruz'] += ['naw ruz', 'nawruz', 'new year']

    ed = C.edition('en', 'English (bahai.org, 2023)', 'translation', f'{C.WRITINGS_REPO}/prayers.html',
                   notes='The text of Bahá’í Prayers as published on bahai.org (retrieved 2025); instructions are shown in italics and '
                         'the author of each prayer in its heading.')
    m = C.manifest(WORK, 'devotional', 'Bahá’í Prayers', 'A Selection of Prayers Revealed by Bahá’u’lláh, the Báb, and ‘Abdu’l‑Bahá',
                   [{'id': 'section', 'label': {'en': 'Section'}, 'isUnit': True}, {'id': 'paragraph', 'label': {'en': 'Paragraph'}}],
                   {'format': '{work} {section} ¶{paragraph}', 'rangeFormat': '{work} {section} ¶{paragraph}–{paragraph2}', 'workAbbrev': {'en': 'Bahá’í Prayers'}},
                   toc, [ed], ['en'], aliases=aliases,
                   notes='The Bahá’í prayer book: the three Obligatory Prayers, General Prayers by topic, Occasional Prayers and Special Tablets.')
    C.write_manifest(WORK, m)
    C.report(WORK, 'devotional', ['en'], units, count)
    bad = {k for k in aliases if k not in units_by_slug and k != 'prologue'}
    assert not bad, bad


if __name__ == '__main__':
    main()
