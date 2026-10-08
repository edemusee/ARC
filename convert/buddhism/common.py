"""Shared helpers for the Buddhist text converters.

Run with `python3 -I` from outside the source clones. All source files are untrusted data: they are only
ever parsed with json.load, xml.etree or read as text; nothing is executed.
"""
import json
import os
import re
import shutil
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
READER = os.path.abspath(os.path.join(HERE, '..', '..'))
WORKS = os.path.join(READER, 'works')
SOURCES = os.environ.get(
    'BUDDHISM_SOURCES',
    '/tmp/claude-0/-home-claude/7a651a9d-c615-572e-93d2-9ae13aaa0c8d/scratchpad/sources/buddhism')

BILARA = os.path.join(SOURCES, 'bilara-data')
SC_DATA = os.path.join(SOURCES, 'sc-data')
RUSHI = os.path.join(SOURCES, 'Rushi')
TEI_84000 = os.path.join(SOURCES, 'data-tei', 'keep')
CBETA = os.path.join(SOURCES, 'xml-p5', 'keep')
CSCD = os.path.join(SOURCES, 'tipitaka-xml', 'cscd')

TRAD = 'buddhism'

PLI_EDITION = {'lang': 'pi', 'script': 'Latn', 'direction': 'ltr'}
EN_EDITION = {'lang': 'en', 'script': 'Latn', 'direction': 'ltr'}
ZH_EDITION = {'lang': 'zh', 'script': 'Hant', 'direction': 'ltr'}

# Licence / source strings shared by several works
MS_LICENSE = ('Mahāsaṅgīti Tipiṭaka Buddhavasse 2500 (World Tipiṭaka Edition, Dhamma Society), the Pali root '
              'text distributed by SuttaCentral; SuttaCentral states the root texts are in the public domain '
              '(https://suttacentral.net/licensing).')
SUJATO_LICENSE = ('Creative Commons Zero (CC0 1.0) — "This translation is an expression of an ancient spiritual '
                  'text ... dedicated to the public domain via Creative Commons Zero (CC0)." (bilara-data '
                  '_publication.json; LICENSE.md). The translator requests that any use be in accordance with the '
                  'values and principles of the Buddhist community.')
BILARA_URL = 'https://github.com/suttacentral/bilara-data/tree/published/'
LICENSE_84000 = ('Creative Commons CC BY-NC-ND 3.0 (Attribution - Non-commercial - No-derivatives). '
                 'Attribution: 84000: Translating the Words of the Buddha. "They may be copied or printed for fair '
                 'use, but only with full attribution, and not for commercial advantage or personal compensation." '
                 '(https://github.com/84000/data-tei README; Terms of Use: '
                 'https://github.com/84000/all-data/blob/master/Terms_of_Use.md)')
LICENSE_CBETA = ('CBETA Chinese Electronic Tripitaka, Creative Commons BY-NC-SA 3.0 (Taiwan) '
                 '(https://www.cbeta.org/copyright.php); Taishō Tripiṭaka base text (public domain).')

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
    return t.strip()


def bilara_markup(text, verse=False):
    """Convert the small bilara markup subset to the reader's inline markup.
    <j> (soft break in long verse lines) → newline inside verses, space in prose; <em> → *…*;
    _pali_ (quoted root word) → *pali*; #123 section counters are dropped."""
    t = str(text)
    t = t.replace('<j>', '\n' if verse else ' ')
    t = re.sub(r'<em>(.*?)</em>', r'*\1*', t)
    t = re.sub(r'(^|[\s(“‘"])_([^_\n]+?)_(?=[\s.,;:!?)”’"]|$)', r'\1*\2*', t)
    t = re.sub(r'#\d+\s*', '', t)
    t = HTML_TAG.sub('', t)
    return t


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def seg_parts(key):
    """'mn10:4.0.1' → ['4', '0', '1']; 'dhp1:1' → ['1']."""
    return key.split(':', 1)[1].split('.')


# ---------- output ----------
def reset_work(work_id):
    d = os.path.join(WORKS, work_id)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    return d


def write_unit(work_id, edition_id, unit, passages):
    """Write one unit file. Drops empty passages; asserts refs are inside the unit."""
    clean = []
    for p in passages:
        text = norm(p.get('text'))
        if not text:
            continue
        assert p['ref'].startswith(unit + ':'), (work_id, edition_id, unit, p['ref'])
        q = {'ref': p['ref'], 'text': text}
        if p.get('heading'):
            q['heading'] = norm(p['heading'])
        if p.get('notes'):
            notes = [{'at': min(max(0, int(n['at'])), len(text)), 'text': norm(n['text'])}
                     for n in p['notes'] if norm(n.get('text'))]
            if notes:
                q['notes'] = notes
        clean.append(q)
    if not clean:
        return 0
    d = os.path.join(WORKS, work_id, edition_id)
    os.makedirs(d, exist_ok=True)
    fn = os.path.join(d, unit.replace(':', '-') + '.json')
    with open(fn, 'w', encoding='utf-8') as f:
        json.dump({'workId': work_id, 'editionId': edition_id, 'unit': unit, 'passages': clean},
                  f, ensure_ascii=False, indent=1)
    return len(clean)


def write_manifest(work_id, manifest):
    manifest = dict(manifest)
    manifest.setdefault('schemaVersion', 1)
    manifest['workId'] = work_id
    manifest.setdefault('tradition', TRAD)
    for ed in manifest['editions']:
        assert ed.get('license') and ed.get('source'), (work_id, ed['id'])
        assert re.fullmatch(r'[a-z0-9-]+', ed['id'])
    with open(os.path.join(WORKS, work_id, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)


def edition(id_, base, label, role, license_, source, **extra):
    ed = {'id': id_}
    ed.update(base)
    ed['label'] = {'en': label}
    ed['role'] = role
    ed['license'] = license_
    ed['source'] = source
    ed.update(extra)
    return ed
