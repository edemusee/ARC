#!/usr/bin/env python3
"""Add further Bible editions to works/bible/ (on top of convert_bible.py's ten).

Usage (from the reader root):
    python3 -I convert/bible/convert_extra.py [--only id1,id2] [--probe id1,id2] [--list]

Sources (all under the scratchpad; see DEFAULT_* below):
    mdbible/            lguenth/mdbible            ESV in Markdown (by_book/NN_Book.md)
    nabre/              nirmalben/bible-nabre-json-dataset   NABRE scraped from BibleGateway (generated_data/nabre.json)
    thiagobodruk/json/  thiagobodruk/bible         ~90 versions, positional JSON arrays
    open-bibles/        seven1m/open-bibles        USFX / Zefania / OSIS XML
    fetch/<ABBR>.json   scrollmapper/bible_databases formats/json/<ABBR>.json

The edition table (EDITIONS) is the single place that says what is converted, from where, with which
cleanup, and what goes into the manifest. The manifest is rewritten by merging the new editions into the
existing works/bible/manifest.json (existing edition entries, canons and aliases are kept).
"""
import argparse
import html
import json
import os
import re
import shutil
import sys
import unicodedata
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C          # noqa: E402
import convert_bible as CB  # noqa: E402
import extra_tables as T    # noqa: E402
import extra_names as N     # noqa: E402

SCRATCH = '/tmp/claude-0/-home-claude/7a651a9d-c615-572e-93d2-9ae13aaa0c8d/scratchpad'
SRC = os.path.join(SCRATCH, 'sources', 'christianity')
FETCH = os.path.join(SCRATCH, 'fetch')
WORK = 'bible'

THIAGO = os.path.join(SRC, 'thiagobodruk', 'json')
OPENB = os.path.join(SRC, 'open-bibles')
MDBIBLE = os.path.join(SRC, 'mdbible', 'by_book')
NABRE = os.path.join(SRC, 'nabre', 'generated_data', 'nabre.json')

report = {}         # edition id -> dict(units, passages, bytes, books, skipped, notes)

# ====================================================================== text cleanup helpers

SUPPLIED_RE = re.compile(r'(?<!\[)\[([^\[\]\n]+)\](?!\])')


def supplied(text):
    """[word] -> [[word]] (translator-supplied words), leaving existing [[...]] alone."""
    return SUPPLIED_RE.sub(r'[[\1]]', text)


def strip_chars(chars):
    tbl = {ord(c): None for c in chars}
    return lambda t: t.translate(tbl)


def chain(*fns):
    def run(text, notes):
        for fn in fns:
            r = fn(text) if fn.__code__.co_argcount == 1 else fn(text, notes)
            if isinstance(r, tuple):
                text, extra = r
                if extra:
                    notes.extend(extra)
            else:
                text = r
        return text, notes
    return run


def hash_note(text):
    """'... She#1:2 The translators ...' (Song of Songs speaker notes scraped with a footnote) -> note."""
    m = re.search(r'\s*#\s?\d+[:.]\d+\s+(.*)$', text)
    if not m:
        return text
    return text[:m.start()].rstrip(), [{'at': len(text[:m.start()].rstrip()), 'text': m.group(1).strip()}]


def brace_note(text):
    """'{Heb. ransom}' glosses -> notes anchored where they stood."""
    notes = []
    out = []
    pos = 0
    for m in re.finditer(r'\s*\{([^{}]+)\}', text):
        out.append(text[pos:m.start()])
        notes.append({'at': len(''.join(out).rstrip()), 'text': m.group(1).strip()})
        pos = m.end()
    out.append(text[pos:])
    t = re.sub(r' +', ' ', ''.join(out)).strip()
    return (t, notes) if notes else text


def lsv_fix(text):
    """LSV: '[[ or x ]]' alternates -> notes; '||' poetry breaks -> newline; [x] -> [[x]]."""
    notes = []
    out = []
    pos = 0
    for m in re.finditer(r'\s*\[\[\s*(.*?)\s*\]\]\s*', text):
        out.append(text[pos:m.start()])
        notes.append({'at': len(''.join(out).rstrip()), 'text': m.group(1)})
        pos = m.end()
        if pos < len(text) and text[pos] not in ',.;:!?)':
            out.append(' ')
    out.append(text[pos:])
    t = ''.join(out)
    t = re.sub(r'\s*\|\|\s*', '\n', t)
    t = supplied(t)
    return t, notes


def t4t_fix(text):
    t = re.sub(r'\s?\[[A-Z]{2,5}(?:/[A-Z]{2,5})*\]', '', text)       # [MET] [RHQ] figure-of-speech tags
    t = t.replace('<', '(').replace('>', ')')
    t = re.sub(r'\{([^{}]*)\}', r'(\1)', t)
    return t


def angle_to_paren(text):
    return text.replace('<', '(').replace('>', ')')


def dbl_brace_to_supplied(text):
    return re.sub(r'\{\{([^{}]*)\}\}', r'[[\1]]', text)


def tr_strongs(text):
    """TR.json leaks Strong's numbers and morphology codes into a few verses."""
    t = re.sub(r'\s*\{[A-Z0-9-]+\}', '', text)
    t = re.sub(r'\s*\b\d{1,5}\b', '', t)
    return t


def croatian_fix(text):
    t = re.sub(r'#.*$', '', text)                       # '#THE UNBOUND BIBLE ...' trailer / lone '#'
    t = re.sub(r'\[\d+(?::\d+)?[a-z]?\]\s*', '', t)     # [5a] [4:1] alt-versification markers
    return t


def bracket_number_markers(text):
    """Strip {12:50} / [5:15] alternate versification markers (FinPR, DutSVVA) and [2-3] / [-] (NorSMB)."""
    t = re.sub(r'\s*\{\d+:\d+\}\s*', ' ', text)
    t = re.sub(r'\s*\[\d+:\s?\d+\]\s*', ' ', t)
    t = re.sub(r'\s*\[\d+-\d+\]\s*', ' ', t)
    t = re.sub(r'^\[-\]$', '', t.strip())
    return t


def strip_markers(text):
    """{1:x} / {} / [x. 12,1] cross-reference leftovers (pt_matos, SpaPlatense, MapM ketiv/qere brackets kept)."""
    t = re.sub(r'\s*\{[^{}]*\}\s*', ' ', text)
    t = re.sub(r'\s*\[[A-Za-z]{1,4}\. \d+,\d+\]\s*', ' ', t)
    return t


def pgr_fix(text):
    t = text.replace('{[}', '').replace('{]}', '')
    return supplied(t)


def rotherham_fix(text):
    """Rotherham: [****] section markers and [="word"] glosses leaked into the text."""
    t = re.sub(r'\s*\[\*+\]\s*', ' ', text)
    t = re.sub(r'\[=\s*[“"]([^”"\]]*)[”"]\s*\]', r'(= \1)', t)
    return t


def ascii_bracket_empty(text):
    """Drop empty or quote-only brackets left by scrapers: [] [ ] [’’] {}."""
    return re.sub(r'\s*(\[[\s’\'"]*\]|\{\s*\})', '', text)


def hebmodern_fix(text):
    return re.sub(r'\]\d+-\d+\[', '', text)


def swe1917_notes(text):
    """'människan[1] av stoft ... [1] Hebr adám [2] Hebr. adamá' -> notes anchored at the markers."""
    if '[' not in text:
        return text
    markers = list(re.finditer(r'(?<=\S)\[(\d+)\]', text))
    if not markers:
        return re.sub(r'\s*\[\d+\]\s*', ' ', text).strip()
    # footnote bodies start at the first ' [n] ' that is preceded by whitespace
    m = re.search(r'\s\[(\d+)\]\s', text)
    body = ''
    if m:
        body, text = text[m.start():], text[:m.start()]
    notes_by_n = {}
    for part in re.split(r'\s\[(\d+)\]\s', body):
        pass
    parts = re.split(r'\s\[(\d+)\]\s?', ' ' + body) if body else []
    for i in range(1, len(parts) - 1, 2):
        notes_by_n[parts[i]] = parts[i + 1].strip()
    notes = []
    out = []
    pos = 0
    for mk in re.finditer(r'\[(\d+)\]', text):
        out.append(text[pos:mk.start()])
        n = mk.group(1)
        if n in notes_by_n and notes_by_n[n]:
            notes.append({'at': len(''.join(out)), 'text': notes_by_n[n]})
        pos = mk.end()
    out.append(text[pos:])
    return ''.join(out), notes


def japbungo_fix(text):
    return '' if text.strip() in ('[なし]', 'なし') else text


def nmv_fix(text):
    t = angle_to_paren(text)
    return supplied(t)


FIXES = {
    'supplied': supplied, 'brace_note': brace_note, 'lsv_fix': lsv_fix, 't4t_fix': t4t_fix, 'nmv_fix': nmv_fix,
    'dbl_brace_to_supplied': dbl_brace_to_supplied, 'tr_strongs': tr_strongs, 'croatian_fix': croatian_fix,
    'bracket_number_markers': bracket_number_markers, 'hebmodern_fix': hebmodern_fix, 'swe1917_notes': swe1917_notes,
    'japbungo_fix': japbungo_fix, 'strip_markers': strip_markers, 'pgr_fix': pgr_fix, 'rotherham_fix': rotherham_fix,
}


def vulgate_psalm_notitle(ch, verse):
    """Septuagint psalm numbering where the superscription is NOT counted as a verse (Giguet)."""
    if ch == 9:
        return (9, verse) if verse <= 20 else (10, verse - 20)
    return C.vulgate_psalm_to_hebrew(ch, verse)


# Standard chapter counts of the 66 Protestant books (Hebrew-division Joel 4 / Malachi 3 are accepted too).
STD_CHAPTERS = dict(zip(C.CANONS['protestant-66'],
                        [50, 40, 27, 36, 34, 24, 21, 4, 31, 24, 22, 25, 29, 36, 10, 13, 10, 42, 150, 31, 12, 8, 66, 52, 5, 48,
                         12, 14, 3, 9, 1, 4, 7, 3, 3, 3, 2, 14, 4, 28, 16, 24, 21, 28, 16, 16, 13, 6, 6, 4, 4, 5, 3, 6, 4, 3, 1,
                         13, 5, 5, 3, 5, 1, 1, 1, 22]))

TAG_TITLE = re.compile(r'<title[^>]*>(.*?)</title>', re.S)
TAG_NOTE = re.compile(r'<note[^>]*>(.*?)</note>', re.S)
TAG_ANY = re.compile(r'</?[A-Za-z][^<>]*>')


# ====================================================================== generic emitter

class Emitter:
    """Collects (code, chapter, verse, text, heading, notes) records into works/bible/<ed>/."""

    def __init__(self, ed, fix=None, vulgate_psalms=False, book_filter=None):
        self.ed = ed
        self.w = C.Writer(WORK, ed)
        fn = FIXES[fix] if isinstance(fix, str) else fix
        self.fix = chain(fn) if fn else None
        self.vulgate_psalms = vulgate_psalms      # False | 'title' | 'notitle'
        self.book_filter = set(book_filter) if book_filter else None
        self.skipped = []
        self.books = []          # codes in source order with at least one passage
        self.pending_heading = {}  # code -> heading to attach to the next verse
        self.chapters = {}       # code -> set of chapter numbers written
        self.cleaned = 0         # verses where generic tag/marker cleanup changed something

    def generic_clean(self, code, text, notes):
        """Source-independent residue: stray <title>/<note>/other tags, ** markers, empty brackets."""
        orig = text
        if '&' in text:
            text = html.unescape(text)
        for m in TAG_TITLE.finditer(text):
            t = re.sub(r'\s+', ' ', TAG_ANY.sub('', m.group(1))).strip()
            if t:
                self.pending_heading[code] = (self.pending_heading.get(code, '') + ' ' + t).strip()
        text = TAG_TITLE.sub(' ', text)
        out, pos = [], 0
        for m in TAG_NOTE.finditer(text):
            out.append(text[pos:m.start()])
            nt = re.sub(r'\s+', ' ', TAG_ANY.sub('', m.group(1))).strip()
            if nt:
                notes.append({'at': len(re.sub(r'\s+', ' ', ''.join(out)).rstrip()), 'text': nt})
            pos = m.end()
        out.append(text[pos:])
        text = ''.join(out)
        text = TAG_ANY.sub(' ', text)
        text = text.replace('**', '').replace('__', '')
        # backtick used as a quotation mark (Wycliffe, Thai KJV, Cebuano, JPS): opening before a letter, else closing
        text = re.sub(r'`(?=\w)', '\u2018', text).replace('`', '\u2019')
        # footnote markers '#1:2 text' -> note; any other '#' is a scraper leftover
        if '#' in text:
            r = hash_note(text)
            if isinstance(r, tuple):
                text, extra = r
                notes.extend(extra)
            text = re.sub(r'#\s?\d*', '', text)
        text = re.sub(r'^>\s*', '', text)                       # blockquote-style verse prefix (Jubilee 2000)
        text = text.replace('<<', '\u00ab').replace('>>', '\u00bb')
        text = re.sub(r'\(\d+>', '', text)                        # '(3>' footnote marks (Luther 1545)
        text = re.sub(r'[<>\\]', '', text)                        # stray angle brackets and backslashes
        text = re.sub(r'[{}]', '', text)                           # unmatched braces (brace_note ran before this)
        text = ascii_bracket_empty(text)
        if text != orig:
            self.cleaned += 1
        return text, notes

    def add(self, code, ch, vs, text, heading=None, notes=None):
        if code is None:
            return False
        if self.book_filter and code not in self.book_filter:
            return False
        notes = list(notes or [])
        if self.fix:
            text, notes = self.fix(text, notes)
        text, notes = self.generic_clean(code, text, notes)
        if code == 'psa' and int(ch) == 151:          # Septuagint Psalm 151 as chapter 151 of the Psalms
            code, ch = 'ps151', 1
        if self.vulgate_psalms and code == 'psa' and isinstance(vs, int):
            if self.vulgate_psalms == 'notitle':
                ch, vs = vulgate_psalm_notitle(int(ch), vs)
            else:
                ch, vs = C.vulgate_psalm_to_hebrew(int(ch), vs)
        if isinstance(vs, int):
            vs = str(vs)
        vs = re.sub(r'[^0-9a-z-]', '', str(vs).lower())
        if not vs:
            self.skipped.append(f'{code} {ch}:? bad verse id')
            return False
        unit = f'{code}:{ch}'
        ph = self.pending_heading.pop(code, None)
        if ph:
            heading = (ph + (' — ' + heading if heading else ''))
        ok = self.w.add(unit, f'{unit}:{vs}', text, heading=heading, notes=[n for n in notes if n.get('text')] or None)
        if not ok:
            self.skipped.append(f'{unit}:{vs} empty')
            return False
        CB.note_chapter(code, int(ch))
        if code not in self.books:
            self.books.append(code)
        self.chapters.setdefault(code, set()).add(int(ch))
        return True

    def gaps(self):
        """(missing, short): chapters absent inside a book's range; books shorter than the standard count."""
        missing, short = [], []
        for code, chs in self.chapters.items():
            top = max(chs)
            holes = [c for c in range(1, top + 1) if c not in chs]
            if holes:
                missing.append(f'{code}:{",".join(map(str, holes))}')
            std = STD_CHAPTERS.get(code)
            if std and top < std and not (code == 'mal' and top == 3):
                short.append(f'{code}:{top}/{std}')
        return missing, short

    def finish(self, extra_notes=None):
        units, passages, nbytes = self.w.flush()
        missing, short = self.gaps()
        report[self.ed] = dict(units=units, passages=passages, bytes=nbytes, books=self.books,
                               skipped=self.skipped, notes=extra_notes or [], missing=missing, short=short,
                               cleaned=self.cleaned)
        return report[self.ed]


# ====================================================================== parsers (yield records)

def iter_thiago(path):
    with open(path, encoding='utf-8-sig') as f:
        data = json.load(f)
    for b in data:
        code = T.THIAGO_ABBREV.get(unicodedata.normalize('NFC', b['abbrev']).strip().lower())
        if code is None:
            raise ValueError(f'unknown thiago abbrev {b["abbrev"]!r} in {path}')
        for ci, chapter in enumerate(b['chapters']):
            for vi, text in enumerate(chapter):
                yield code, ci + 1, vi + 1, text, None, None


def iter_scrollmapper(path, names=None):
    names = names or T.SCROLLMAPPER_EXTRA_NAMES
    with open(path, encoding='utf-8-sig') as f:
        data = json.load(f)
    for b in data['books']:
        code = names.get(b['name'])
        for c in b['chapters']:
            for v in c['verses']:
                yield code, int(c['chapter']), int(v['verse']), v['text'], None, None


def iter_mdbible(folder):
    for fn in sorted(os.listdir(folder)):
        m = re.match(r'(\d\d)_(.+)\.md$', fn)
        if not m:
            continue
        code = T.MDBIBLE_FILES.get(m.group(2))
        ch = None
        with open(os.path.join(folder, fn), encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n')
                if not line.strip() or line.startswith('# '):
                    continue
                mh = re.match(r'## Chapter (\d+)\s*$', line)
                if mh:
                    ch = int(mh.group(1))
                    continue
                mv = re.match(r'(\d+)\. (.*)$', line)
                if mv and ch:
                    yield code, ch, int(mv.group(1)), mv.group(2), None, None
                else:
                    raise ValueError(f'unexpected line in {fn}: {line[:80]!r}')


# ---- NABRE: headings are scraped into the verse text; peel them off heuristically.

ROMAN = r'(?:I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII)'
NAB_PART = re.compile(r'^((?:%s\.|[A-E]\.|First Book|Second Book|Third Book|Fourth Book|Fifth Book|Preamble\.|Foreword)[^\n]*?)\s+(?=Chapter [A-Z0-9]+\b|Psalm \d+\b)' % ROMAN)
NAB_CHAPTER = re.compile(r'\(?Chapter ([A-Z0-9]+)\)?\s*(?:-\s*)?')
NAB_PSALM = re.compile(r'^Psalm (\d+)\s+(.*?)\s+-\s+')
NAB_STROPHE = re.compile(r'^%s(?:\s+-\s+|\.\s+)(?=[A-Z“"\(\[])' % ROMAN)
SMALL = {'a', 'an', 'the', 'of', 'and', 'to', 'in', 'on', 'for', 'with', 'at', 'by', 'from', 'or', 'as', 'is', 'his',
         'her', 'its', 'their', 'over', 'against', 'into', 'before', 'after', 'under', 'between', 'upon', 'be'}


def titleish(s):
    """NABRE section headings are Title Case, short, and never contain commas; genealogy verses do."""
    if ',' in s or ';' in s:
        return False
    words = re.findall(r"[A-Za-z’'][A-Za-z’'\-]*", s)
    if not (1 <= len(words) <= 9):
        return False
    if re.fullmatch(ROMAN, s.strip()):
        return False
    big = [w for w in words if w.lower() not in SMALL]
    if not big:
        return False
    if any(not w[0].isupper() for w in big):
        return False
    first = words[0].lower()
    if first in ('then', 'and', 'now', 'so', 'but', 'when', 'thus', 'these', 'this', 'he', 'she', 'they', 'i', 'you', 'we', 'it'):
        return False
    return not s.rstrip('.').endswith((',', ';', ':'))


def nabre_split(text, first_verse):
    """Return (headings list, text) for a scraped NABRE verse."""
    heads = []
    t = text.strip()
    m = NAB_PART.match(t)
    if m:
        heads.append(m.group(1).strip())
        t = t[m.end():]
    m = NAB_PSALM.match(t)
    if m:
        heads.append(m.group(2).strip())
        t = t[m.end():]
    m = NAB_CHAPTER.search(t)
    if m and m.start() <= 2 and first_verse:
        t = t[m.end():]
    elif m and first_verse is False and m.start() == 0:
        t = t[m.end():]
    t = NAB_STROPHE.sub('', t)
    # 'Title. Rest...' or 'Title - Rest...' section heading glued to the verse start
    m = re.match(r'^([A-Z][^.!?“"\(\[]{2,70}?)(\. | - )(?=[A-Z“"\(\[])', t)
    if m and titleish(m.group(1)) and len(t) > m.end() + 10:
        heads.append(m.group(1).strip())
        t = t[m.end():]
    return heads, t.strip()


def iter_nabre(path):
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    for b in data:
        code = T.NABRE_NAMES[b['book']]
        for c in b['chapters']:
            ch = int(c['chapter'])
            for v in c['verses']:
                vs = int(v['verse'])
                heads, text = nabre_split(v['text'], vs == 1)
                # a following 'Chapter X - ...' glued to the END of a verse (Esther additions in the scrape)
                m = re.search(r'\s(?:\(Chapter [A-Z0-9]+\)|Chapter [A-F]) - ', text)
                if m and m.start() > 20:
                    text = text[:m.start()].rstrip()
                yield code, ch, vs, text, (' — '.join(heads) if heads else None), None


# ---- OSIS, milestone-aware, with titles as headings and notes kept

OSIS_NS = '{http://www.bibletechnologies.net/2003/OSIS/namespace}'
OSIS_EXTRA = {'Tob': 'tob', 'Jdt': 'jdt', 'Wis': 'wis', 'Sir': 'sir', 'Bar': 'bar', '1Macc': '1ma', '2Macc': '2ma',
              '3Macc': '3ma', '4Macc': '4ma', '1Esd': '1es', '2Esd': '2es', 'PrMan': 'man', 'AddEsth': 'esg',
              'EsthGr': 'esg', 'PrAzar': 'pra', 'Sus': 'sus', 'Bel': 'bel', 'EpJer': 'lje', 'AddPs': 'ps151',
              'AddDan': None}


def osis_code(osis_id):
    if osis_id in C.OSIS_IDS:
        return C.OSIS_IDS[osis_id]
    return OSIS_EXTRA.get(osis_id)


def iter_osis(path):
    """Yield records from an OSIS file; handles container verses and sID/eID milestones."""
    tree = ET.parse(path)
    root = tree.getroot()
    ns = OSIS_NS if root.tag.startswith(OSIS_NS) else ''
    for div in root.iter(ns + 'div'):
        if div.get('type') != 'book':
            continue
        code = osis_code(div.get('osisID', ''))
        if code is None:
            continue
        # linearise the book: walk, emitting (kind, payload)
        cur = None            # (ch, vs)
        buf = []
        notes = []
        pending_title = []
        out = []              # records

        def flush():
            nonlocal buf, notes, cur
            if cur is None:
                return
            text = ''.join(buf)
            text = re.sub(r'\s+', ' ', text).strip()
            ch, vs = cur
            heading = ' '.join(pending_title).strip() or None
            pending_title.clear()
            out.append((code, ch, vs, text, heading, notes or None))
            buf, notes, cur = [], [], None

        def walk(el, in_verse):
            nonlocal cur
            tag = el.tag[len(ns):] if el.tag.startswith(ns) else el.tag
            if tag == 'verse':
                osis = el.get('osisID')
                if el.get('eID'):
                    flush()
                    return
                if osis:
                    flush()
                    parts = osis.split()[0].split('.')
                    if len(parts) >= 3 and re.fullmatch(r'\d+', parts[1]):
                        cur = (int(parts[1]), parts[2])
                    if el.get('sID'):
                        return             # milestone: text follows as siblings
                    # container verse
                    if el.text:
                        buf.append(el.text)
                    for ch in el:
                        walk(ch, True)
                        if ch.tail:
                            buf.append(ch.tail)
                    flush()
                return
            if tag == 'note':
                if cur is not None:
                    ntext = re.sub(r'\s+', ' ', ''.join(el.itertext())).strip()
                    if ntext:
                        notes.append({'at': len(re.sub(r'\s+', ' ', ''.join(buf)).rstrip()), 'text': ntext})
                return
            if tag == 'title':
                ttype = el.get('type', '')
                text = re.sub(r'\s+', ' ', ''.join(el.itertext())).strip()
                if ttype in ('main', 'runningHead', 'x-book', 'book') or el.get('canonical') == 'false' and ttype == 'main':
                    return
                if cur is not None and in_verse:
                    buf.append(' ' + text + ' ')      # canonical psalm title inside a verse
                elif text and ttype not in ('chapter',) and not re.fullmatch(r'(Chapter|Psalm|Kapitel)?\s*\d+\.?', text):
                    pending_title.append(text)
                return
            if tag in ('reference', 'w', 'seg', 'q', 'hi', 'transChange', 'divineName', 'foreign', 'name', 'p', 'lg',
                       'l', 'lb', 'div', 'chapter', 'milestone', 'list', 'item', 'inscription', 'abbr', 'speech', 'speaker'):
                if tag == 'transChange' and el.get('type') == 'added' and cur is not None:
                    buf.append('[[')
                    if el.text:
                        buf.append(el.text)
                    for ch in el:
                        walk(ch, in_verse)
                        if ch.tail:
                            buf.append(ch.tail)
                    buf.append(']]')
                    return
                if tag == 'l' and cur is not None and buf:
                    buf.append('\n')
                if el.text and cur is not None:
                    buf.append(el.text)
                for ch in el:
                    walk(ch, in_verse)
                    if ch.tail and cur is not None:
                        buf.append(ch.tail)
                if tag in ('l', 'lb') and cur is not None:
                    buf.append('\n')
                return
            if tag in ('header', 'work', 'teiHeader', 'figure', 'index'):
                return
            # unknown: treat as inline container
            if el.text and cur is not None:
                buf.append(el.text)
            for ch in el:
                walk(ch, in_verse)
                if ch.tail and cur is not None:
                    buf.append(ch.tail)

        if div.text:
            pass
        for ch in div:
            walk(ch, False)
            if ch.tail and cur is not None:
                buf.append(ch.tail)
        flush()
        for rec in out:
            yield rec


# ---- Zefania with bnumber -> code mapping that tolerates deuterocanon numbering

ZEF_NUMBERS = {i + 1: code for i, code in enumerate(C.CANONS['protestant-66'])}
ZEF_NUMBERS.update({67: 'tob', 68: 'jdt', 69: 'esg', 70: 'wis', 71: 'sir', 72: 'bar', 73: 'lje', 74: 'pra',
                    75: 'sus', 76: 'bel', 77: 'man', 78: '1ma', 79: '2ma', 80: '3ma', 81: '4ma', 82: '1es', 83: '2es'})


def iter_zefania(path):
    tree = ET.parse(path)
    for bb in tree.getroot().iter('BIBLEBOOK'):
        code = ZEF_NUMBERS.get(int(bb.get('bnumber')))
        for ch in bb.iter('CHAPTER'):
            cn = int(ch.get('cnumber'))
            for v in ch.iter('VERS'):
                notes = []
                parts = [v.text or '']
                for el in v:
                    if el.tag in ('NOTE', 'XREF'):
                        if el.tag == 'NOTE':
                            nt = re.sub(r'\s+', ' ', ''.join(el.itertext())).strip()
                            if nt:
                                notes.append({'at': len(''.join(parts).rstrip()), 'text': nt})
                    else:
                        parts.append(''.join(el.itertext()))
                    parts.append(el.tail or '')
                yield code, cn, int(v.get('vnumber')), ''.join(parts), None, notes or None


# ---- USFX via the existing converter (writes directly); repairs a truncated file on the way

def run_usfx(ed, path, keep_notes=True, repair=False):
    if repair:
        with open(path, encoding='utf-8') as f:
            txt = f.read()
        if '</usfx>' not in txt[-200:]:
            # eng-bbe.usfx.xml never closes its <book> elements and is cut off after the last verse
            if '</book>' not in txt:
                parts = txt.split('<book ')
                txt = parts[0] + '<book ' + '</book>\n<book '.join(parts[1:])
            txt = txt.rstrip() + '\n</book>\n</usfx>\n'
        # psalm superscriptions written as <A Psalm. Of David.> -> USFX <d> (becomes the verse heading)
        txt = re.sub(r'&lt;([A-Z][^&<>]*?)&gt;', r'<d>\1</d>', txt)
        txt = txt.replace('**', '')
        tmp = os.path.join(SCRATCH, 'repaired-' + os.path.basename(path))
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(txt)
        path = tmp
    CB.convert_usfx(ed, path, keep_notes=keep_notes)
    r = CB.report[ed]
    # gap check from the files written
    chapters = {}
    for fn in os.listdir(os.path.join(C.WORKS, WORK, ed)):
        m = re.match(r'([0-9a-z]+)-(\d+)\.json$', fn)
        if m:
            chapters.setdefault(m.group(1), set()).add(int(m.group(2)))
    em = Emitter.__new__(Emitter)
    em.chapters = chapters
    missing, short = Emitter.gaps(em)
    report[ed] = dict(units=r['units'], passages=r['passages'], bytes=r['bytes'], books=r['books'],
                      skipped=r['skipped'], notes=[], missing=missing, short=short, cleaned=0)
    return report[ed]


# ---- ChiSB (思高本): '[section title]' trails the verse before the section; '【psalm title】' leads it.

def chisb_records(path):
    carry = {}
    for code, ch, vs, text, heading, notes in iter_scrollmapper(path):
        heads = []
        m = re.match(r'^【([^】]+)】\s*', text)
        if m:
            heads.append(m.group(1).strip())
            text = text[m.end():]
        if code in carry:
            heads.insert(0, carry.pop(code))
        trail = re.findall(r'\[([^\[\]]+)\]', text)
        text = re.sub(r'\s*\[[^\[\]]+\]\s*', ' ', text).strip()
        if trail:
            carry[code] = ' — '.join(x.strip() for x in trail)
        yield code, ch, vs, text, (' — '.join(heads) if heads else None), notes


# ---- RusSynodal: a few <note>/<title> tags inside verse text

def rus_synodal_records(path):
    carry = {}
    for code, ch, vs, text, heading, notes in iter_scrollmapper(path):
        notes = list(notes or [])
        heads = []
        if code in carry:
            heads.append(carry.pop(code))
        for m in re.finditer(r'<title[^>]*>(.*?)</title>', text):
            carry[code] = m.group(1).strip()
        text = re.sub(r'\s*<title[^>]*>.*?</title>\s*', ' ', text)
        out, pos = [], 0
        for m in re.finditer(r'<note[^>]*>(.*?)</note>', text):
            out.append(text[pos:m.start()])
            notes.append({'at': len(''.join(out).rstrip()), 'text': m.group(1).strip()})
            pos = m.end()
        out.append(text[pos:])
        text = ''.join(out)
        text = re.sub(r'<[^>]+>', '', text)
        yield code, ch, vs, text, (' — '.join(heads) if heads else None), notes or None


# ---- GerMenge: 'Additions to Daniel' is one book of three chapters -> sus / bel / pra

def germenge_records(path):
    with open(path, encoding='utf-8-sig') as f:
        data = json.load(f)
    for b in data['books']:
        name = b['name']
        if name == 'Additions to Daniel':
            for c in b['chapters']:
                code = {1: 'sus', 2: 'bel', 3: 'pra'}.get(int(c['chapter']))
                for v in c['verses']:
                    yield code, 1, int(v['verse']), v['text'], None, None
            continue
        code = T.SCROLLMAPPER_EXTRA_NAMES.get(name)
        for c in b['chapters']:
            for v in c['verses']:
                yield code, int(c['chapter']), int(v['verse']), v['text'], None, None


# ====================================================================== edition table

def thiago(file):
    return os.path.join(THIAGO, file + '.json')


def sm(abbr):
    for d in (FETCH, os.path.join(FETCH, 'scrollmapper')):
        p = os.path.join(d, abbr + '.json')
        if os.path.exists(p):
            return p
    return os.path.join(FETCH, abbr + '.json')


def ob(file):
    return os.path.join(OPENB, file)


EDITIONS = T.EDITIONS   # list of dicts; see extra_tables.py


def records_for(ed):
    """Return an iterator of records for an edition spec, or None when the spec writes directly (USFX)."""
    kind, path = ed['src']
    if kind == 'thiago':
        return iter_thiago(thiago(path))
    if kind == 'scrollmapper':
        return iter_scrollmapper(sm(path))
    if kind == 'scrollmapper-chisb':
        return chisb_records(sm(path))
    if kind == 'scrollmapper-rus':
        return rus_synodal_records(sm(path))
    if kind == 'scrollmapper-menge':
        return germenge_records(sm(path))
    if kind == 'osis':
        return iter_osis(ob(path))
    if kind == 'zefania':
        return iter_zefania(ob(path))
    if kind == 'mdbible':
        return iter_mdbible(MDBIBLE)
    if kind == 'nabre':
        return iter_nabre(NABRE)
    if kind == 'usfx':
        return None
    raise ValueError(kind)


def convert(ed):
    kind, path = ed['src']
    if kind == 'usfx':
        return run_usfx(ed['id'], ob(path), keep_notes=True, repair=ed.get('repair', False))
    em = Emitter(ed['id'], fix=ed.get('fix'), vulgate_psalms=ed.get('vulgate_psalms', False),
                 book_filter=ed.get('book_filter'))
    for code, ch, vs, text, heading, notes in records_for(ed):
        if code is None:
            continue
        em.add(code, ch, vs, text, heading=heading, notes=notes)
    return em.finish()


# ====================================================================== manifest

def canon_for(ed, books):
    """Pick an existing canon when the edition's books equal it exactly; otherwise register one named after the
    edition (so the reader never lists a book the edition lacks). `canon` on the spec only fixes the ORDER."""
    canons = dict(C.CANONS)
    canons.update(T.EXTRA_CANONS)
    want = ed.get('canon')
    if want and canons.get(want) == books:
        return want
    for name, lst in canons.items():
        if lst == books:
            return name
    T.EXTRA_CANONS[ed['id']] = list(books)
    return ed['id']


# ---- book names from the sources themselves (for aliases)

def collect_sourced_names():
    """{code: [names]} read from the source files: Zefania bname, USFX <h>, OSIS main titles, thiago names."""
    out = {}

    def put(code, name):
        name = re.sub(r'\s+', ' ', unicodedata.normalize('NFC', name)).strip()
        if code and name and len(name) <= 60:
            out.setdefault(code, []).append(name)

    try:
        for fn in ('cze-bkr.zefania.xml', 'dut-statenvertaling.zefania.xml', 'rus-synodal.zefania.xml', 'eng-darby.zefania.xml'):
            for bb in ET.parse(ob(fn)).getroot().iter('BIBLEBOOK'):
                put(ZEF_NUMBERS.get(int(bb.get('bnumber'))), bb.get('bname') or '')
        for fn in ('chi-cuv.usfx.xml', 'chi-cuv-simp.usfx.xml', 'por-almeida.usfx.xml', 'ron-rccv.usfx.xml', 'lat-clementine.usfx.xml',
                   'spa-rv1909.usfx.xml', 'eng-web.usfx.xml'):
            with open(ob(fn), encoding='utf-8', errors='replace') as f:
                txt = f.read()
            for m in re.finditer(r'<book id="([A-Z0-9]+)">(.*?)</book>', txt, re.S):
                code = C.usfx_code(m.group(1))
                head = m.group(2)[:4000]
                h = re.search(r'<h>([^<]*)</h>', head)
                if h:
                    put(code, h.group(1))
                for t in re.findall(r'<toc level="[12]">([^<]*)</toc>', head):
                    put(code, t)
        for fn in ('jpn-kougo.osis.xml',):
            root = ET.parse(ob(fn)).getroot()
            for div in root.iter(OSIS_NS + 'div'):
                if div.get('type') != 'book':
                    continue
                code = osis_code(div.get('osisID', ''))
                for el in div.iter(OSIS_NS + 'title'):
                    if el.get('type') == 'main':
                        put(code, ''.join(el.itertext()))
                        break
        for fn in ('pt_nvi', 'en_bbe', 'pt_avm'):
            with open(thiago(fn), encoding='utf-8-sig') as f:
                for b in json.load(f):
                    put(T.THIAGO_ABBREV.get(unicodedata.normalize('NFC', b['abbrev']).lower()), b.get('name', ''))
        for abbr in ('FreCrampon',):
            if os.path.exists(sm(abbr)):
                with open(sm(abbr), encoding='utf-8-sig') as f:
                    for b in json.load(f)['books']:
                        put(T.SCROLLMAPPER_EXTRA_NAMES.get(b['name']), b['name'])
    except Exception as e:  # sources are optional for the manifest step
        print('   (sourced names incomplete:', str(e)[:80], ')')
    return out


def edition_entry(ed, books):
    e = {'id': ed['id'], 'lang': ed['lang'], 'script': ed.get('script', 'Latn'), 'direction': ed.get('direction', 'ltr'),
         'label': ed['label'], 'role': ed.get('role', 'translation')}
    if ed.get('font'):
        e['font'] = ed['font']
    e['canon'] = canon_for(ed, books)
    e['families'] = ed.get('families', [])
    e['license'] = ed['license']
    e['source'] = ed['source']
    notes = ed.get('notes')
    if notes:
        e['notes'] = {'en': notes}
    return e


def present_books(ed_id):
    """Codes with unit files in works/bible/<ed>/, ordered by their first appearance in any canon list."""
    edir = os.path.join(C.WORKS, WORK, ed_id)
    codes = set()
    for fn in os.listdir(edir):
        m = re.match(r'([0-9a-z]+)-(\d+)\.json$', fn)
        if m:
            codes.add(m.group(1))
            CB.note_chapter(m.group(1), int(m.group(2)))
    return codes


def write_manifest(new_entries):
    mp = os.path.join(C.WORKS, WORK, 'manifest.json')
    with open(mp, encoding='utf-8') as f:
        m = json.load(f)
    canons = dict(m.get('canons', {}))
    canons.update(T.EXTRA_CANONS)
    m['canons'] = canons
    # books: add any code we now carry that the manifest lacks
    for code in sorted(set(c for lst in canons.values() for c in lst)):
        m['books'].setdefault(code, {'en': C.BOOK_NAMES[code]})
    # chapters: max over every edition folder
    for e in m['editions'] + new_entries:
        present_books(e['id'])
    for code in m['books']:
        m['chapters'][code] = max(m['chapters'].get(code, 1), CB.chapters_seen.get(code, 1))
    # editions: existing kept verbatim, new ones replace same-id entries
    by_id = {e['id']: e for e in m['editions']}
    for e in new_entries:
        by_id[e['id']] = e
    order = [e['id'] for e in m['editions'] if e['id'] in by_id]
    for e in new_entries:
        if e['id'] not in order:
            order.append(e['id'])
    m['editions'] = [by_id[i] for i in order]
    m['defaultEditions'] = ['kjv']
    # drop canons registered by earlier runs that no edition uses any more (the base canons always stay)
    used = set(e['canon'] for e in m['editions']) | set(C.CANONS)
    m['canons'] = {k: v for k, v in m['canons'].items() if k in used}
    # title in a few more languages
    for k, v in N.TITLES.items():
        m['title'].setdefault(k, v)
    # aliases: existing + curated + sourced (lower-cased, NFC, de-duplicated)
    aliases = {k: list(v) for k, v in m.get('aliases', {}).items()}
    extra = N.curated()
    for code, names in collect_sourced_names().items():
        extra.setdefault(code, []).extend(names)
    added = 0
    for code, names in extra.items():
        if code not in m['books']:
            continue
        lst = aliases.setdefault(code, [])
        for a in names:
            a = unicodedata.normalize('NFC', a).lower().strip()
            a = re.sub(r'\s+', ' ', a)
            if a and a != code and a not in lst:
                lst.append(a)
                added += 1
    m['aliases'] = aliases
    print(f'   aliases: {added} added, {sum(len(v) for v in aliases.values())} total')
    return C.write_manifest(WORK, m)


# ====================================================================== main

def probe(ids):
    for ed in EDITIONS:
        if ed['id'] not in ids:
            continue
        kind, path = ed['src']
        if kind == 'usfx':
            print(f'== {ed["id"]}: usfx {path} (not probed)')
            continue
        want = {('jhn', 3, '16'), ('gen', 1, '1'), ('psa', 23, '1')}
        got = {}
        for code, ch, vs, text, heading, notes in records_for(ed):
            key = (code, ch, str(vs))
            if key in want:
                got[key] = text[:110]
            if len(got) == 3:
                break
        print(f'== {ed["id"]}')
        for k in sorted(got):
            print('   ', k, repr(got[k]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    ap.add_argument('--probe', default='')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--no-manifest', action='store_true')
    args = ap.parse_args()
    if args.list:
        for ed in EDITIONS:
            print(ed['id'], ed['lang'], ed['src'])
        return
    if args.probe:
        probe(set(args.probe.split(',')))
        return
    only = set(x for x in args.only.split(',') if x)
    entries = []
    dropped = {}
    for ed in EDITIONS:
        if only and ed['id'] not in only:
            if os.path.isdir(os.path.join(C.WORKS, WORK, ed['id'])):
                entries.append(edition_entry(ed, order_books(ed, present_books(ed['id']))))
            continue
        print(f'== {ed["id"]}', flush=True)
        try:
            r = convert(ed)
        except Exception as e:
            msg = re.sub(r'[^\W\d_]', 'x', str(e)[:160])   # never echo source text
            print(f'   FAILED: {type(e).__name__}: {msg}')
            dropped[ed['id']] = f'conversion failed: {type(e).__name__}: {msg[:120]}'
            shutil.rmtree(os.path.join(C.WORKS, WORK, ed['id']), ignore_errors=True)
            continue
        books = order_books(ed, set(r['books']))
        # thiagobodruk versions: drop any with chapters missing inside a book (the task's rule)
        if ed['src'][0] == 'thiago' and (r['missing'] or r['short']):
            why = f'missing chapters {r["missing"]} short books {r["short"]}'
            print('   DROPPED (incomplete):', why)
            dropped[ed['id']] = why
            shutil.rmtree(os.path.join(C.WORKS, WORK, ed['id']), ignore_errors=True)
            report.pop(ed['id'], None)
            continue
        entries.append(edition_entry(ed, books))
        print(f'   {len(books)} books, {r["units"]} units, {r["passages"]} passages, {r["bytes"]/1048576:.2f} MB; '
              f'{len(r["skipped"])} skipped, {r.get("cleaned", 0)} tag-cleaned; canon={entries[-1]["canon"]}')
        if r['missing']:
            print('   missing chapters:', ' '.join(r['missing'])[:300])
        if r['short']:
            print('   short books:', ' '.join(r['short'])[:300])
        shown = [s for s in r['skipped'] if not s.endswith(' empty')][:6]
        for s in shown:
            print('     -', s)
    if not args.no_manifest:
        mbytes = write_manifest(entries)
        print(f'manifest: {mbytes/1024:.1f} KB')
    out = {k: {kk: vv for kk, vv in v.items() if kk != 'skipped'} | {'skipped': len(v['skipped'])} for k, v in report.items()}
    for e in entries:
        if e['id'] in out:
            out[e['id']].update(lang=e['lang'], canon=e['canon'], license=e['license'])
    with open(os.path.join(SCRATCH, 'extra-report.json'), 'w', encoding='utf-8') as f:
        json.dump({'editions': out, 'dropped': dropped}, f, ensure_ascii=False, indent=1)
    if dropped:
        print('dropped:', json.dumps(dropped, ensure_ascii=False)[:2000])


def order_books(ed, codes):
    """Order present codes: by the requested canon when given, else by the source order recorded in T."""
    base = ed.get('order') or C.CANONS.get(ed.get('canon'), None) or T.EXTRA_CANONS.get(ed.get('canon'), None)
    if base is None:
        base = T.ALL_CODES
    return [c for c in base if c in codes] + sorted(c for c in codes if c not in base)


if __name__ == '__main__':
    main()
