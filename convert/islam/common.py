"""Shared helpers for the Islamic text converters.

Run with `python3 -I` from outside the source clones. All source files are untrusted data: they are only
ever parsed with json.load or read as text.
"""
import html
import json
import os
import re
import shutil
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
READER = os.path.abspath(os.path.join(HERE, '..', '..'))
WORKS = os.path.join(READER, 'works')
SOURCES = os.environ.get(
    'ISLAM_SOURCES',
    '/tmp/claude-0/-home-claude/7a651a9d-c615-572e-93d2-9ae13aaa0c8d/scratchpad/sources/islam')

QURAN_JSON = os.path.join(SOURCES, 'quran-json', 'data')
QURAN_API = os.path.join(SOURCES, 'quran-api-curl')
HADITH_API = os.path.join(SOURCES, 'hadith-api-curl')
HADITH_JSON = os.path.join(SOURCES, 'hadith-json', 'db', 'by_book')
THAQALAYN = os.path.join(SOURCES, 'ThaqalaynData', 'books')
OPENITI = os.path.join(SOURCES, '0325AH', 'data', '0321Tahawi', '0321Tahawi.MatnCaqida',
                       '0321Tahawi.MatnCaqida.JK000126-ara1')
ASMA = os.path.join(SOURCES, 'asma-u-llahi-l-husna', 'BeautifulNamesOfAllah.json')

TRAD = 'islam'

AR_EDITION = {'lang': 'ar', 'script': 'Arab', 'direction': 'rtl', 'font': 'arabic'}
EN_EDITION = {'lang': 'en', 'script': 'Latn', 'direction': 'ltr'}

HTML_TAG = re.compile(r'</?[a-zA-Z][^>]*>')


def norm(text):
    """NFC, collapse whitespace runs to one space (line breaks kept), trim."""
    if text is None:
        return ''
    t = unicodedata.normalize('NFC', str(text))
    t = t.replace(' ', ' ').replace('\r\n', '\n').replace('\r', '\n')
    t = re.sub(r'[ \t​﻿]+', ' ', t)
    t = '\n'.join(line.strip() for line in t.split('\n'))
    t = re.sub(r'\n{2,}', '\n', t)
    t = re.sub(r' ([,.;:!?،؛؟])', r'\1', t)
    t = re.sub(r'\( +', '(', t)
    t = re.sub(r' +\)', ')', t)
    return t.strip()


def strip_html(text):
    """Remove tags and unescape entities. Superscript honorifics (HubeAli: <sup>asws</sup>) are dropped,
    footnote markers (<sup>[1]</sup>) are dropped, other tags are simply removed."""
    t = str(text)
    t = re.sub(r'<sup>\s*\[?\d+\]?\s*</sup>', '', t)
    t = re.sub(r'<sup>[^<]{0,12}</sup>', '', t)
    t = re.sub(r'<br\s*/?>', '\n', t, flags=re.I)
    t = re.sub(r'</p>\s*<p[^>]*>', '\n', t, flags=re.I)
    t = HTML_TAG.sub('', t)
    t = html.unescape(t)
    return t


def slug_ok(s):
    return re.fullmatch(r'[a-z0-9-]+', s) is not None


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


# ---------- output ----------
def reset_work(work_id):
    d = os.path.join(WORKS, work_id)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    return d


def write_unit(work_id, edition_id, unit, passages):
    assert passages, f'{work_id}/{edition_id}/{unit}: no passages'
    for seg in unit.split(':'):
        assert slug_ok(seg), (work_id, unit)
    for p in passages:
        assert p['text'], f'{work_id}/{edition_id}/{unit}: empty passage {p["ref"]}'
        assert p['ref'] == unit or p['ref'].startswith(unit + ':'), (work_id, unit, p['ref'])
        for seg in p['ref'].split(':'):
            assert slug_ok(seg), (work_id, p['ref'])
        assert not HTML_TAG.search(p['text']), (work_id, p['ref'], 'html')
        p['text'] = unicodedata.normalize('NFC', p['text'])
        if 'heading' in p:
            assert not HTML_TAG.search(p['heading']), (work_id, p['ref'], 'html in heading')
            p['heading'] = unicodedata.normalize('NFC', p['heading'])
        if 'notes' in p:
            for n in p['notes']:
                n['text'] = unicodedata.normalize('NFC', n['text'])
    d = os.path.join(WORKS, work_id, edition_id)
    os.makedirs(d, exist_ok=True)
    fn = os.path.join(d, unit.replace(':', '-') + '.json')
    with open(fn, 'w', encoding='utf-8') as f:
        json.dump({'workId': work_id, 'editionId': edition_id, 'unit': unit, 'passages': passages},
                  f, ensure_ascii=False, separators=(',', ':'))
        f.write('\n')


def write_manifest(work_id, manifest):
    assert manifest['workId'] == work_id
    for lvl in manifest['levels']:
        assert slug_ok(lvl['id'])
    assert any(l.get('isUnit') for l in manifest['levels'])
    for ed in manifest['editions']:
        assert slug_ok(ed['id']) and ed.get('license') and ed.get('source') and ed.get('direction'), (work_id, ed['id'])
    for t in manifest.get('toc', []):
        for seg in t['ref'].split(':'):
            assert slug_ok(seg), (work_id, t['ref'])
        for c in t.get('children', []):
            for seg in c['ref'].split(':'):
                assert slug_ok(seg), (work_id, c['ref'])
    with open(os.path.join(WORKS, work_id, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
        f.write('\n')


def edition(ed_id, label, role, license_, source, base=EN_EDITION, **extra):
    e = {'id': ed_id}
    e.update(base)
    e.update({'label': {'en': label}, 'role': role, 'license': license_, 'source': source})
    e.update(extra)
    return e


def manifest(work_id, shelf, families, title, levels, citation, toc, editions, default_editions,
             subtitle=None, aliases=None, notes=None, **extra):
    m = {'schemaVersion': 1, 'workId': work_id, 'tradition': TRAD, 'shelf': shelf, 'families': families,
         'title': title}
    if subtitle:
        m['subtitle'] = subtitle
    m.update(extra)
    m.update({'levels': levels, 'citation': citation, 'toc': toc, 'editions': editions,
              'defaultEditions': default_editions})
    if aliases:
        m['aliases'] = aliases
    if notes:
        m['notes'] = {'en': notes}
    return m


def report(work_id, shelf, families, editions, units, passages):
    print(f'{work_id}: shelf={shelf} families={families} editions={editions} units={units} passages={passages}')
