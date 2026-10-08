"""Shared helpers for the Christian documents / devotionals converters.

Run with `python3 -I` from outside the source clones. All source files are treated as untrusted data:
they are only ever parsed with json.load / read as text.
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
    'CHRISTIAN_SOURCES',
    '/tmp/claude-0/-home-claude/7a651a9d-c615-572e-93d2-9ae13aaa0c8d/scratchpad/sources/christianity')

CREEDS_JSON = os.path.join(SOURCES, 'Creeds.json', 'creeds')
OCD = os.path.join(SOURCES, 'open-christian-data', 'data')
OPB = os.path.join(SOURCES, 'open-prayer-book', 'md')

CREEDS_JSON_URL = 'https://github.com/NonlinearFruit/Creeds.json'
CREEDS_JSON_LICENSE = 'Public domain text; repository under the Unlicense'
OCD_URL = 'https://github.com/OpenChristianData/open-christian-data'
OCD_LICENSE = 'Public domain text; Open Christian Data compilation CC BY-NC 4.0'
OPB_URL = 'https://github.com/dmtzs/open-prayer-book'
OPB_LICENSE = 'Public domain (CC0 1.0 release by the Open Prayer Book project)'

ROMAN = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}


def roman_to_int(s):
    s = s.upper()
    if not s or any(c not in ROMAN for c in s):
        return None
    total, prev = 0, 0
    for c in reversed(s):
        v = ROMAN[c]
        total += -v if v < prev else v
        prev = max(prev, v)
    return total


def norm(text):
    """NFC, collapse runs of spaces/tabs, trim each line, drop blank-line runs beyond a double newline."""
    if text is None:
        return ''
    t = unicodedata.normalize('NFC', str(text))
    t = t.replace(' ', ' ').replace('\r\n', '\n').replace('\r', '\n')
    t = re.sub(r'[ \t]+', ' ', t)
    t = '\n'.join(line.strip() for line in t.split('\n'))
    t = re.sub(r'\n{3,}', '\n\n', t)
    return t.strip()


def paragraphs(text):
    return [p for p in (norm(p) for p in norm(text).split('\n\n')) if p]


def split_sentences(text):
    """Split a creed paragraph into lines on sentence boundaries; fall back to semicolons."""
    text = norm(text).replace('\n', ' ')
    parts = [p.strip() for p in re.split(r'(?<=[.!?])\s+(?=["\'\[A-Z])', text) if p.strip()]
    if len(parts) < 3:
        parts = [p.strip() for p in re.split(r'(?<=;)\s+', text) if p.strip()]
    return parts


def slug_ok(s):
    return re.fullmatch(r'[a-z0-9-]+', s) is not None


# ---------- OSIS references → readable text (for proof-text notes) ----------
OSIS_BOOKS = {
    'Gen': 'Gen.', 'Exod': 'Exod.', 'Lev': 'Lev.', 'Num': 'Num.', 'Deut': 'Deut.', 'Josh': 'Josh.', 'Judg': 'Judg.',
    'Ruth': 'Ruth', '1Sam': '1 Sam.', '2Sam': '2 Sam.', '1Kgs': '1 Kings', '2Kgs': '2 Kings', '1Chr': '1 Chron.',
    '2Chr': '2 Chron.', 'Ezra': 'Ezra', 'Neh': 'Neh.', 'Esth': 'Esth.', 'Job': 'Job', 'Ps': 'Ps.', 'Prov': 'Prov.',
    'Eccl': 'Eccl.', 'Song': 'Song', 'Isa': 'Isa.', 'Jer': 'Jer.', 'Lam': 'Lam.', 'Ezek': 'Ezek.', 'Dan': 'Dan.',
    'Hos': 'Hos.', 'Joel': 'Joel', 'Amos': 'Amos', 'Obad': 'Obad.', 'Jonah': 'Jonah', 'Mic': 'Mic.', 'Nah': 'Nah.',
    'Hab': 'Hab.', 'Zeph': 'Zeph.', 'Hag': 'Hag.', 'Zech': 'Zech.', 'Mal': 'Mal.', 'Matt': 'Matt.', 'Mark': 'Mark',
    'Luke': 'Luke', 'John': 'John', 'Acts': 'Acts', 'Rom': 'Rom.', '1Cor': '1 Cor.', '2Cor': '2 Cor.', 'Gal': 'Gal.',
    'Eph': 'Eph.', 'Phil': 'Phil.', 'Col': 'Col.', '1Thess': '1 Thess.', '2Thess': '2 Thess.', '1Tim': '1 Tim.',
    '2Tim': '2 Tim.', 'Titus': 'Titus', 'Phlm': 'Philem.', 'Heb': 'Heb.', 'Jas': 'James', '1Pet': '1 Pet.',
    '2Pet': '2 Pet.', '1John': '1 John', '2John': '2 John', '3John': '3 John', 'Jude': 'Jude', 'Rev': 'Rev.',
    'Tob': 'Tobit', 'Jdt': 'Judith', 'Wis': 'Wisd.', 'Sir': 'Sirach', 'Bar': 'Baruch', '1Macc': '1 Macc.',
    '2Macc': '2 Macc.', 'EpJer': 'Ep. Jer.', 'PrMan': 'Pr. Man.', 'Sus': 'Susanna', 'Bel': 'Bel',
}


def _osis_one(ref):
    m = re.fullmatch(r'([1-4]?[A-Za-z]+)(?:\.(\d+)(?:\.(\d+))?)?', ref.strip())
    if not m:
        return ref.strip(), None, None, None
    book, ch, vs = m.group(1), m.group(2), m.group(3)
    return OSIS_BOOKS.get(book, book), book, ch, vs


def osis_to_text(refs):
    """['Rom.14.7-Rom.14.9', '1Cor.6.19'] → 'Rom. 14:7–9; 1 Cor. 6:19'."""
    out = []
    for r in refs:
        r = r.strip()
        if not r:
            continue
        pieces = [p for p in r.split(',') if p]   # some entries are 'a,b' in one string
        for p in pieces:
            if '-' in p:
                a, b = p.split('-', 1)
                an, ab, ac, av = _osis_one(a)
                bn, bb, bc, bv = _osis_one(b)
                if ab == bb and ac == bc and av and bv:
                    out.append(f'{an} {ac}:{av}–{bv}')
                elif ab == bb and ac and bc:
                    out.append(f'{an} {ac}:{av or 1}–{bc}:{bv or ""}'.rstrip(':'))
                else:
                    out.append(f'{an} {ac}:{av}–{bn} {bc}:{bv}')
            else:
                n, b, c, v = _osis_one(p)
                if c and v:
                    out.append(f'{n} {c}:{v}')
                elif c:
                    out.append(f'{n} {c}')
                else:
                    out.append(n)
    return '; '.join(out)


def proof_notes(text_with_markers, proofs):
    """Turn 'text,[1] more[2]' + [{Id, References}] into (clean_text, notes[]) with char offsets.
    Returns (None, None) when the marked text does not reduce to the plain text (caller keeps plain text)."""
    if not text_with_markers or not proofs:
        return None, None
    by_id = {}
    for p in proofs:
        refs = p.get('References') or []
        if isinstance(refs, str):
            refs = [refs]
        by_id[str(p.get('Id'))] = osis_to_text(refs)
    notes, clean, pos = [], '', 0
    src = norm(text_with_markers)

    def append(seg):
        nonlocal clean
        if clean.endswith(' ') and seg.startswith(' '):
            seg = seg[1:]
        clean += seg

    for m in re.finditer(r'\[(\d+)\]', src):
        append(src[pos:m.start()])
        t = by_id.get(m.group(1))
        if t:
            notes.append({'at': len(clean), 'text': t})
        pos = m.end()
    append(src[pos:])
    lead = len(clean) - len(clean.lstrip())
    clean = clean.strip()
    for n in notes:
        n['at'] = max(0, min(n['at'] - lead, len(clean)))
    return clean, notes


# ---------- output ----------
def reset_work(work_id):
    d = os.path.join(WORKS, work_id)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    return d


def write_unit(work_id, edition_id, unit, passages):
    assert passages, f'{work_id}/{edition_id}/{unit}: no passages'
    for p in passages:
        assert p['text'], f'{work_id}/{edition_id}/{unit}: empty passage {p["ref"]}'
        assert p['ref'] == unit or p['ref'].startswith(unit + ':'), (work_id, unit, p['ref'])
        assert not re.search(r'</?[a-z][^>]*>', p['text'], re.I), (work_id, p['ref'], 'html')
        p['text'] = unicodedata.normalize('NFC', p['text'])
        if 'heading' in p:
            p['heading'] = unicodedata.normalize('NFC', p['heading'])
    d = os.path.join(WORKS, work_id, edition_id)
    os.makedirs(d, exist_ok=True)
    fn = os.path.join(d, unit.replace(':', '-') + '.json')
    with open(fn, 'w', encoding='utf-8') as f:
        json.dump({'workId': work_id, 'editionId': edition_id, 'unit': unit, 'passages': passages},
                  f, ensure_ascii=False, indent=1)
        f.write('\n')


def write_manifest(work_id, manifest):
    assert manifest['workId'] == work_id
    for lvl in manifest['levels']:
        assert slug_ok(lvl['id'])
    for ed in manifest['editions']:
        assert slug_ok(ed['id']) and ed.get('license') and ed.get('source'), (work_id, ed['id'])
    for t in manifest.get('toc', []):
        for seg in t['ref'].split(':'):
            assert slug_ok(seg), (work_id, t['ref'])
    with open(os.path.join(WORKS, work_id, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write('\n')


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def edition(ed_id, label, role, license_, source, **extra):
    e = {'id': ed_id, 'lang': 'en', 'script': 'Latn', 'direction': 'ltr', 'label': {'en': label},
         'role': role, 'license': license_, 'source': source}
    e.update(extra)
    return e
