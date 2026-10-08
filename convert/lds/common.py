"""Shared helpers for the Latter-day Saint text converters (python-scripture-scraper sample JSON).

Run with `python3 -I` from outside the source clones. Source files are untrusted data: they are only ever
parsed with json.load.
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
    'LDS_SOURCES',
    '/tmp/claude-0/-home-claude/7a651a9d-c615-572e-93d2-9ae13aaa0c8d/scratchpad/sources/lds/python-scripture-scraper/sample/en-json')
REPO = 'https://github.com/samuelbradshaw/python-scripture-scraper'
TRAD = 'lds'
EN_EDITION = {'lang': 'en', 'script': 'Latn', 'direction': 'ltr'}
HTML_TAG = re.compile(r'</?[a-zA-Z][^>]*>')


def norm(text):
    t = unicodedata.normalize('NFC', str(text or ''))
    t = t.replace(' ', ' ').replace('\r\n', '\n').replace('\r', '\n')
    t = re.sub(r'[ \t​﻿]+', ' ', t)
    t = '\n'.join(line.strip() for line in t.split('\n'))
    t = re.sub(r'\n{2,}', '\n', t)
    return t.strip()


def from_html(h):
    """contentHtml → plain text with the reader's inline markup (*em*, **strong**, _smallcaps_)."""
    t = str(h or '')
    t = re.sub(r'<br\s*/?>\s*', '\n', t, flags=re.I)
    t = re.sub(r'<(em|i)>(.*?)</\1>', lambda m: '*' + m.group(2).strip() + '*' if m.group(2).strip() else '', t, flags=re.S)
    t = re.sub(r'<strong>(.*?)</strong>', lambda m: '**' + m.group(1).strip() + '**' if m.group(1).strip() else '', t, flags=re.S)
    t = re.sub(r'<span class="small-caps">(.*?)</span>', lambda m: '_' + m.group(1).strip() + '_', t, flags=re.S)
    t = HTML_TAG.sub('', t)
    t = html.unescape(t)
    t = re.sub(r'\*\*\s*\*\*', '', t)
    t = norm(t)
    if t.endswith('*') and t.count('*') % 2 == 1:  # footnote marker (JS—H 1:71)
        t = t[:-1].rstrip()
    return t


def load_chapter(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def chapter_files(subdir):
    """[(number, path)] of the chapter files in SOURCES/<subdir>, sorted numerically."""
    d = os.path.join(SOURCES, subdir)
    out = []
    for fn in os.listdir(d):
        m = re.fullmatch(r'(.+?)-(\d+)\.json', fn)
        if m:
            out.append((int(m.group(2)), os.path.join(d, fn)))
    return sorted(out)


def verses(doc):
    """Yield (verse_number:int, text, heading_before) for the verse paragraphs of a chapter document;
    title/subtitle/section-title/paragraph content that precedes a verse is folded into its heading."""
    pending = []
    for p in doc['paragraphs']:
        kind = p['type']
        if kind == 'verse':
            text = from_html(p['contentHtml'])
            if not text:
                continue
            yield int(p['number']), text, pending
            pending = []
        elif kind == 'image':
            continue
        elif kind == 'chapter-title':
            continue
        else:
            pending.append((kind, from_html(p['contentHtml']), p.get('churchId') or ''))


# ---------- output ----------
def reset_work(work_id):
    d = os.path.join(WORKS, work_id)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)


def write_unit(work_id, edition_id, unit, passages):
    assert passages, (work_id, edition_id, unit)
    for p in passages:
        assert p['text'], (work_id, unit, p['ref'])
        assert p['ref'] == unit or p['ref'].startswith(unit + ':'), (work_id, unit, p['ref'])
        assert re.fullmatch(r'[a-z0-9:-]+', p['ref']), p['ref']
        assert not HTML_TAG.search(p['text']), (work_id, p['ref'])
        p['text'] = unicodedata.normalize('NFC', p['text'])
        if 'heading' in p:
            assert not HTML_TAG.search(p['heading']), (work_id, p['ref'], 'heading')
            p['heading'] = unicodedata.normalize('NFC', p['heading'])
    d = os.path.join(WORKS, work_id, edition_id)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, unit.replace(':', '-') + '.json'), 'w', encoding='utf-8') as f:
        json.dump({'workId': work_id, 'editionId': edition_id, 'unit': unit, 'passages': passages},
                  f, ensure_ascii=False, separators=(',', ':'))
        f.write('\n')


def write_manifest(work_id, manifest):
    assert manifest['workId'] == work_id
    assert any(l.get('isUnit') for l in manifest['levels'])
    for ed in manifest['editions']:
        assert ed.get('license') and ed.get('source') and ed.get('direction'), ed['id']
    with open(os.path.join(WORKS, work_id, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
        f.write('\n')


def edition(ed_id, label, license_, source, role='original', notes=None, **extra):
    e = {'id': ed_id}
    e.update(EN_EDITION)
    e.update({'label': {'en': label}, 'role': role, 'license': license_, 'source': source})
    if notes:
        e['notes'] = {'en': notes}
    e.update(extra)
    return e


def report(work_id, shelf, families, editions, units, passages):
    print(f'{work_id}: shelf={shelf} families={families} editions={editions} units={units} passages={passages}')
