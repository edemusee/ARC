"""Shared helpers for the Bahá'í text converters.

Run with `python3 -I` from outside the source clones. Source HTML is untrusted data: it is only ever parsed
with html.parser / regular expressions and never executed or imported.
"""
import html
import json
import os
import re
import shutil
import unicodedata
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
READER = os.path.abspath(os.path.join(HERE, '..', '..'))
WORKS = os.path.join(READER, 'works')
SOURCES = os.environ.get(
    'BAHAI_SOURCES', '/tmp/claude-0/-home-claude/7a651a9d-c615-572e-93d2-9ae13aaa0c8d/scratchpad/sources/bahai')
OCEAN = os.path.join(SOURCES, 'ocean-library', 'published')
WRITINGS = os.path.join(SOURCES, 'writings', 'writings', 'html')
OCEAN_REPO = 'https://github.com/chadananda/ocean-library/blob/master/published'
WRITINGS_REPO = 'https://github.com/dra11y/writings/blob/main/writings/html'
TRAD = 'bahai'
LICENSE = ("© Bahá'í International Community; reproduced under the Bahá'í International Community terms "
           "(attribution, non-commercial, unaltered)")
EN_EDITION = {'lang': 'en', 'script': 'Latn', 'direction': 'ltr'}
AR_EDITION = {'lang': 'ar', 'script': 'Arab', 'direction': 'rtl', 'font': 'arabic'}
FA_EDITION = {'lang': 'fa', 'script': 'Arab', 'direction': 'rtl', 'font': 'arabic'}
HTML_TAG = re.compile(r'</?[a-zA-Z][^>]*>')

FN_OPEN, FN_CLOSE = '\x01', '\x02'     # footnote anchor sentinel: \x01<id>\x02
EM_OPEN, EM_CLOSE = '\x03', '\x04'     # italics sentinels
ST_OPEN, ST_CLOSE = '\x05', '\x06'     # bold sentinels


class TextExtractor(HTMLParser):
    """HTML fragment → text with sentinels; block-ish elements become line breaks."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get('class', '') or ''
        self.stack.append((tag, cls))
        if tag in ('br', 'li', 'p', 'hr', 'div', 'h1', 'h2', 'h3', 'h4'):
            self.out.append('\n')
        elif tag == 'span' and ('block' in cls.split() or 'answer' in cls.split()):
            self.out.append('\n')
        elif tag in ('i', 'em'):
            self.out.append(EM_OPEN)
        elif tag in ('b', 'strong'):
            self.out.append(ST_OPEN)
        elif tag == 'a' and a.get('data-fnid'):
            self.out.append(FN_OPEN + a['data-fnid'] + FN_CLOSE)
        elif tag == 'sup':
            self.out.append('\x07')  # marks a superscript citation number (prayers.html); resolved by caller

    def handle_endtag(self, tag):
        cls = ''
        while self.stack:
            t, c = self.stack.pop()
            if t == tag:
                cls = c
                break
        if tag in ('i', 'em'):
            self.out.append(EM_CLOSE)
        elif tag in ('b', 'strong'):
            self.out.append(ST_CLOSE)
        elif tag == 'span' and ('question' in cls.split() or 'block' in cls.split() or 'preamble' in cls.split()):
            self.out.append('\n' if 'question' in cls.split() or 'block' in cls.split() else ' ')
        elif tag in ('li', 'p', 'div'):
            self.out.append('\n')
        elif tag == 'sup':
            self.out.append('\x08')

    def handle_data(self, data):
        # source line wrapping is not structure: tags add the line breaks
        data = re.sub(r'(?<=[\u0600-\u06FF])\n\s*(?=[\u0600-\u06FF])', '', data)   # one mid-word wrap in Arabic
        self.out.append(data.replace('\n', ' '))


def extract(fragment):
    p = TextExtractor()
    p.feed(fragment)
    p.close()
    return ''.join(p.out)


def finish(raw):
    """Resolve sentinels into the reader's inline markup and normalize whitespace.
    Returns (text, anchors) where anchors = [(fnid, offset)]."""
    t = raw.replace(' ', ' ')
    # italics / bold: trim inside, drop empties
    t = re.sub(EM_OPEN + r'\s*(.*?)\s*' + EM_CLOSE, lambda m: f'*{m.group(1)}*' if m.group(1).strip() else '', t, flags=re.S)
    t = re.sub(ST_OPEN + r'\s*(.*?)\s*' + ST_CLOSE, lambda m: f'**{m.group(1)}**' if m.group(1).strip() else '', t, flags=re.S)
    t = t.replace(EM_OPEN, '').replace(EM_CLOSE, '').replace(ST_OPEN, '').replace(ST_CLOSE, '')
    t = re.sub(r'[ \t\r\f\v​﻿]+', ' ', t)
    t = '\n'.join(line.strip() for line in t.split('\n'))
    t = re.sub(r'\n{2,}', '\n', t).strip()
    t = re.sub(r' ([,.;:!?’”)])', r'\1', t)
    t = re.sub(r'([(“‘]) ', r'\1', t)
    t = re.sub(r'\s+(' + FN_OPEN + r'[^\x02]*' + FN_CLOSE + r')', r'\1', t)   # anchor hugs the preceding word
    anchors, clean, pos = [], [], 0
    for m in re.finditer(FN_OPEN + r'([^\x02]*)' + FN_CLOSE, t):
        clean.append(t[pos:m.start()])
        anchors.append((m.group(1), len(''.join(clean))))
        pos = m.end()
    clean.append(t[pos:])
    t = ''.join(clean)
    t = unicodedata.normalize('NFC', t)
    return t.strip(), anchors


def plain(fragment):
    """Fragment → text, sentinels dropped (for headings/labels)."""
    t, _ = finish(extract(fragment))
    return t.replace('\x07', '').replace('\x08', '')


# ---------- output ----------
def reset_work(work_id):
    d = os.path.join(WORKS, work_id)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)


def write_unit(work_id, edition_id, unit, passages):
    assert passages, (work_id, edition_id, unit)
    assert re.fullmatch(r'[a-z0-9-]+', unit), unit
    for p in passages:
        assert p['text'], (work_id, unit, p['ref'])
        assert p['ref'].startswith(unit + ':'), (work_id, unit, p['ref'])
        assert re.fullmatch(r'[a-z0-9:-]+', p['ref']), p['ref']
        assert not HTML_TAG.search(p['text']), (work_id, p['ref'])
        assert '\x01' not in p['text'] and '\x07' not in p['text'], (work_id, p['ref'])
        p['text'] = unicodedata.normalize('NFC', p['text'])
        if 'heading' in p:
            assert p['heading'] and not HTML_TAG.search(p['heading']), (work_id, p['ref'], 'heading')
        if 'notes' in p:
            for n in p['notes']:
                assert 0 <= n['at'] <= len(p['text']) and n['text'], (work_id, p['ref'], 'note')
    d = os.path.join(WORKS, work_id, edition_id)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, unit + '.json'), 'w', encoding='utf-8') as f:
        json.dump({'workId': work_id, 'editionId': edition_id, 'unit': unit, 'passages': passages},
                  f, ensure_ascii=False, separators=(',', ':'))
        f.write('\n')


def write_manifest(work_id, manifest):
    assert manifest['workId'] == work_id
    assert any(l.get('isUnit') for l in manifest['levels'])
    for ed in manifest['editions']:
        assert ed.get('license') and ed.get('source') and ed.get('direction'), ed['id']
    for t in manifest.get('toc', []):
        assert re.fullmatch(r'[a-z0-9-]+', t['ref']), t['ref']
        for c in t.get('children', []):
            assert re.fullmatch(r'[a-z0-9-]+', c['ref']), c['ref']
    with open(os.path.join(WORKS, work_id, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
        f.write('\n')


def edition(ed_id, label, role, source, base=EN_EDITION, notes=None, **extra):
    e = {'id': ed_id}
    e.update(base)
    e.update({'label': {'en': label}, 'role': role, 'license': LICENSE, 'source': source})
    if notes:
        e['notes'] = {'en': notes}
    e.update(extra)
    return e


def manifest(work_id, shelf, title, subtitle, levels, citation, toc, editions, defaults, aliases=None, notes=None):
    m = {'schemaVersion': 1, 'workId': work_id, 'tradition': TRAD, 'shelf': shelf, 'families': [], 'title': {'en': title}}
    if subtitle:
        m['subtitle'] = {'en': subtitle}
    m.update({'levels': levels, 'citation': citation, 'toc': toc, 'editions': editions, 'defaultEditions': defaults})
    if aliases:
        m['aliases'] = aliases
    if notes:
        m['notes'] = {'en': notes}
    return m


def slug(s):
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r'[’‘\'`ʼ]', '', s.lower())
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s


def report(work_id, shelf, editions, units, passages):
    print(f'{work_id}: shelf={shelf} editions={editions} units={units} passages={passages}')
