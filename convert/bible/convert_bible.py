#!/usr/bin/env python3
"""Convert the Bible editions into works/bible/.

Usage (from the reader root):
    python3 -I convert/bible/convert_bible.py [--sources DIR] [--crampon FILE] [--only ed1,ed2]

Sources (defaults are the cloned repos under the scratchpad sources/christianity folder):
    scrollmapper/KJVA.json, scrollmapper/DRC.json          (scrollmapper/bible_databases JSON)
    open-bibles/*.usfx.xml, *.zefania.xml, *.osis.xml       (seven1m/open-bibles)
    freebiblos/lxx-en.json                                  (FreeBiblos / bluesboy13 KJV app data: Brenton LXX)
    FreCrampon.json (fetched from scrollmapper, formats/json/FreCrampon.json)
"""
import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

DEFAULT_SOURCES = '/tmp/claude-0/-home-claude/7a651a9d-c615-572e-93d2-9ae13aaa0c8d/scratchpad/sources/christianity'
DEFAULT_CRAMPON = '/tmp/claude-0/-home-claude/7a651a9d-c615-572e-93d2-9ae13aaa0c8d/scratchpad/fetch/FreCrampon.json'

WORK = 'bible'
report = {}            # edition -> dict(units, passages, bytes, books, skipped)
chapters_seen = {}     # code -> max chapter number across editions


def note_chapter(code, ch):
    if ch > chapters_seen.get(code, 0):
        chapters_seen[code] = ch


# ------------------------------------------------------------------ scrollmapper JSON

def convert_scrollmapper(ed, path, book_filter=None, vulgate_psalms=False, kjv_brackets=False):
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    w = C.Writer(WORK, ed)
    skipped = []
    books = []
    for b in data['books']:
        code = C.SCROLLMAPPER_NAMES.get(b['name'])
        if code is None or (book_filter and code not in book_filter):
            skipped.append(f"book {b['name']!r} dropped")
            continue
        n_before = w.passages
        for c in b['chapters']:
            for v in c['verses']:
                text = v['text']
                if text.strip() in ('', '…', '...'):
                    skipped.append(f"{code} {c['chapter']}:{v['verse']} empty")
                    continue
                ch, vs = c['chapter'], v['verse']
                if vulgate_psalms and code == 'psa':
                    ch, vs = C.vulgate_psalm_to_hebrew(ch, vs)
                if kjv_brackets:
                    text = re.sub(r'\[([^\]]+)\]', r'[[\1]]', text)
                text = re.sub(r'\s+_\s*$', '', text)          # DRC Joshua 6:24 trailing "_"
                text = re.sub(r'\s*<[^<>]*>\s*$', '', text)   # Crampon Sir 50:29 trailing "<DEUX APPENDICES >"
                unit = f'{code}:{ch}'
                w.add(unit, f'{unit}:{vs}', text)
                note_chapter(code, ch)
        if w.passages > n_before:
            books.append(code)
    units, passages, nbytes = w.flush()
    report[ed] = dict(units=units, passages=passages, bytes=nbytes, books=books, skipped=skipped)
    return w


# ------------------------------------------------------------------ USFX (eBible)

HEADING_SFMS = {'ms', 'mr', 's', 's1', 's2', 's3', 'sp', 'r', 'd', 'qa', 'ms1', 'ms2'}
SKIP_SFMS = {'mt', 'mt1', 'mt2', 'mt3', 'mte', 'is', 'ip', 'ili', 'ili1', 'ili2', 'imt', 'iot', 'io', 'io1', 'io2',
             'ie', 'ib', 'im', 'iq', 'rem', 'h', 'toc', 'toc1', 'toc2', 'toc3', 'cl', 'cp', 'periph'}
SKIP_TAGS = {'id', 'h', 'toc', 'ide', 'cl', 'cp', 'vp', 'x', 'rem', 'periph', 'fig', 'sts'}
LINE = '\x00'   # poetry line break sentinel
NOTE = '\x01'   # footnote anchor sentinel


class UsfxConverter:
    def __init__(self, ed, path, keep_notes=True):
        self.ed, self.path, self.keep_notes = ed, path, keep_notes
        self.w = C.Writer(WORK, ed)
        self.skipped = []
        self.books = []
        self.reset_book(None)

    def reset_book(self, code):
        self.code = code
        self.chapter = None
        self.verse = None
        self.buf = []
        self.notes = []
        self.pending_heading = []
        self.heading_buf = None

    def emit(self, s):
        if self.heading_buf is not None:
            self.heading_buf.append(s)
        elif self.verse is not None:
            self.buf.append(s)

    def flush_verse(self):
        if self.verse is None:
            return
        raw = ''.join(self.buf)
        # normalise: whitespace runs -> space, LINE sentinels -> newline, locate NOTE sentinels
        raw = re.sub(r'[ \t\r\n ]+', ' ', raw)
        raw = re.sub(r' ?%s ?' % LINE, '\n', raw)
        raw = re.sub(r'\n+', '\n', raw).strip()
        notes = []
        if self.keep_notes and self.notes:
            out = []
            i = 0
            for ch in raw:
                if ch == NOTE:
                    if i < len(self.notes):
                        notes.append({'at': len(''.join(out)), 'text': self.notes[i]})
                    i += 1
                else:
                    out.append(ch)
            raw = ''.join(out)
        else:
            raw = raw.replace(NOTE, '')
        raw = re.sub(r' +([,.;:!?])', r'\1', raw)       # space left before punctuation by a removed footnote
        raw = re.sub(r'\s+\n', '\n', raw).strip()
        vs = self.verse
        if re.fullmatch(r'\d+', vs):
            vs = str(int(vs))
        vs = re.sub(r'[^0-9a-z-]', '', vs.lower())
        unit = f'{self.code}:{self.chapter}'
        heading = ' '.join(self.pending_heading).strip() or None
        self.pending_heading = []
        ok = self.w.add(unit, f'{unit}:{vs}', raw, heading=heading, notes=[n for n in notes if n['text']] or None)
        if not ok:
            self.skipped.append(f'{unit}:{vs} empty')
        else:
            note_chapter(self.code, int(self.chapter))
        self.verse = None
        self.buf = []
        self.notes = []

    def note_text(self, el):
        parts = []
        if el.text:
            parts.append(el.text)
        for ch in el:
            tag = ch.tag
            if tag in ('fr', 'xo'):
                pass
            else:
                parts.append(self.note_text(ch))
            if ch.tail:
                parts.append(ch.tail)
        return re.sub(r'\s+', ' ', ''.join(parts)).strip()

    def walk(self, el):
        tag = el.tag
        if tag == 'book':
            code = C.usfx_code(el.get('id', ''))
            self.reset_book(code)
            if code is None:
                return
            n_before = self.w.passages
            for ch in el:
                self.walk(ch)
                if ch.tail:
                    self.emit(ch.tail)
            self.flush_verse()
            if self.w.passages > n_before:
                self.books.append(code)
            return
        if self.code is None:
            return
        if tag in SKIP_TAGS:
            return
        if tag == 'c':
            self.flush_verse()
            self.chapter = str(int(el.get('id')))
            if self.code == 'ps151':                       # WEB numbers Psalm 151 as chapter 151 of its own book
                self.chapter = '1'
            if self.code == 'lje' and self.chapter == '6': # WEB numbers the Letter of Jeremiah as Baruch 6
                self.chapter = '1'
            return
        if tag == 'v':
            self.flush_verse()
            self.verse = el.get('id', '').strip()
            return
        if tag == 've':
            self.flush_verse()
            return
        if tag == 'f':
            if self.verse is not None:
                self.notes.append(self.note_text(el))
                self.buf.append(NOTE)
            return
        if tag == 'd':
            # psalm superscription: heading on the next verse
            self.heading_buf = []
            self._walk_children(el)
            text = re.sub(r'\s+', ' ', ''.join(self.heading_buf)).strip()
            self.heading_buf = None
            if text:
                self.pending_heading.append(text)
            return
        if tag == 'p':
            sfm = el.get('sfm', 'p')
            if sfm in SKIP_SFMS:
                return
            if sfm in HEADING_SFMS:
                self.heading_buf = []
                self._walk_children(el)
                text = re.sub(r'\s+', ' ', ''.join(self.heading_buf)).strip()
                self.heading_buf = None
                if text:
                    self.pending_heading.append(text)
                return
            self._walk_children(el)
            return
        if tag == 's':
            self.heading_buf = []
            self._walk_children(el)
            text = re.sub(r'\s+', ' ', ''.join(self.heading_buf)).strip()
            self.heading_buf = None
            if text:
                self.pending_heading.append(text)
            return
        if tag == 'q':
            self._walk_children(el)
            self.emit(LINE)
            return
        if tag == 'add':
            self.emit('[[')
            self._walk_children(el)
            self.emit(']]')
            return
        if tag == 'b':
            return
        # generic inline container (w, wj, k, qs, nd, it, bk, tl, sc, ref, optionalLineBreak ...)
        self._walk_children(el)

    def _walk_children(self, el):
        if el.text:
            self.emit(el.text)
        for ch in el:
            self.walk(ch)
            if ch.tail:
                self.emit(ch.tail)

    def run(self):
        tree = ET.parse(self.path)
        root = tree.getroot()
        for book in root.iter('book'):
            self.walk(book)
        units, passages, nbytes = self.w.flush()
        report[self.ed] = dict(units=units, passages=passages, bytes=nbytes, books=self.books, skipped=self.skipped)


def convert_usfx(ed, path, keep_notes=True, vulgate_psalms=False):
    conv = UsfxConverter(ed, path, keep_notes=keep_notes)
    if vulgate_psalms:
        orig_add = conv.w.add

        def add(unit, ref, text, heading=None, notes=None):
            code, ch, vs = ref.split(':')
            if code == 'psa' and re.fullmatch(r'\d+', vs):
                ch2, vs2 = C.vulgate_psalm_to_hebrew(int(ch), int(vs))
                unit, ref = f'psa:{ch2}', f'psa:{ch2}:{vs2}'
                note_chapter('psa', ch2)
            return orig_add(unit, ref, text, heading=heading, notes=notes)
        conv.w.add = add
    conv.run()


# ------------------------------------------------------------------ Zefania

def convert_zefania(ed, path):
    w = C.Writer(WORK, ed)
    skipped, books = [], []
    tree = ET.parse(path)
    order = C.CANONS['protestant-66']
    for bb in tree.getroot().iter('BIBLEBOOK'):
        n = int(bb.get('bnumber'))
        code = order[n - 1]
        n_before = w.passages
        for ch in bb.iter('CHAPTER'):
            cn = int(ch.get('cnumber'))
            for v in ch.iter('VERS'):
                text = ''.join(v.itertext())
                unit = f'{code}:{cn}'
                if not w.add(unit, f'{unit}:{int(v.get("vnumber"))}', text):
                    skipped.append(f'{unit}:{v.get("vnumber")} empty')
                else:
                    note_chapter(code, cn)
        if w.passages > n_before:
            books.append(code)
    units, passages, nbytes = w.flush()
    report[ed] = dict(units=units, passages=passages, bytes=nbytes, books=books, skipped=skipped)


# ------------------------------------------------------------------ OSIS (container verses)

def convert_osis(ed, path):
    w = C.Writer(WORK, ed)
    skipped, books = [], []
    ns = '{http://www.bibletechnologies.net/2003/OSIS/namespace}'
    tree = ET.parse(path)
    for div in tree.getroot().iter(ns + 'div'):
        if div.get('type') != 'book':
            continue
        code = C.OSIS_IDS.get(div.get('osisID'))
        if code is None:
            skipped.append(f"book {div.get('osisID')} dropped")
            continue
        n_before = w.passages
        for v in div.iter(ns + 'verse'):
            osis = v.get('osisID')
            if not osis:
                continue
            _, cn, vn = osis.split('.')
            parts = [v.text or '']
            notes = []
            for ch in v:
                if ch.tag == ns + 'note':
                    ntext = re.sub(r'\s+', ' ', ''.join(ch.itertext())).strip()
                    if ntext:
                        notes.append({'at': len(re.sub(r'\s+', ' ', ''.join(parts)).rstrip()), 'text': ntext})
                else:
                    parts.append(''.join(ch.itertext()))
                parts.append(ch.tail or '')
            text = re.sub(r' +([,.;:!?])', r'\1', ''.join(parts))
            unit = f'{code}:{int(cn)}'
            if not w.add(unit, f'{unit}:{int(vn)}', text, notes=notes or None):
                skipped.append(f'{unit}:{vn} empty')
            else:
                note_chapter(code, int(cn))
        if w.passages > n_before:
            books.append(code)
    units, passages, nbytes = w.flush()
    report[ed] = dict(units=units, passages=passages, bytes=nbytes, books=books, skipped=skipped)


# ------------------------------------------------------------------ Brenton LXX (FreeBiblos JSON)

LXX_INDEX = {str(i): code for i, code in enumerate(C.OT39)}
LXX_INDEX.update({'66': '1es', '67': 'tob', '68': 'jdt', '69': '1ma', '70': '2ma', '71': '3ma', '72': '4ma',
                  '73': 'wis', '74': 'sir', '75': 'man', '76': 'bar', '77': 'lje', '78': 'sus', '79': 'bel'})


def convert_lxx(ed, path):
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    w = C.Writer(WORK, ed)
    skipped, books = [], []
    chapter_labels = d.get('chapters', {})
    verse_labels = d.get('labels', {})
    for key in sorted(d['books'], key=int):
        code = LXX_INDEX.get(key)
        if code is None:
            skipped.append(f'book index {key} ({d.get("names", {}).get(key)}) dropped')
            continue
        chaps = d['books'][key]
        clabels = chapter_labels.get(key) or [str(i + 1) for i in range(len(chaps))]
        assert len(clabels) == len(chaps), (key, len(clabels), len(chaps))
        n_before = w.passages
        for ci, verses in enumerate(chaps):
            clabel = clabels[ci]
            vlabels = (verse_labels.get(key) or {}).get(clabel) or [str(i + 1) for i in range(len(verses))]
            assert len(vlabels) == len(verses), (key, clabel, len(vlabels), len(verses))
            bcode, cn = code, clabel
            if code == 'psa' and clabel == '151':
                bcode, cn = 'ps151', '1'
            unit = f'{bcode}:{cn}'
            seen = set()
            for vi, text in enumerate(verses):
                vl = re.sub(r'[^0-9a-z]', '', vlabels[vi].lower())
                if vl in seen:
                    skipped.append(f'{unit}:{vl} duplicate label')
                    continue
                seen.add(vl)
                text = text.replace('¶', ' ')
                if not w.add(unit, f'{unit}:{vl}', text):
                    skipped.append(f'{unit}:{vl} empty')
                else:
                    note_chapter(bcode, int(cn))
        if w.passages > n_before:
            books.append(code)
    units, passages, nbytes = w.flush()
    report[ed] = dict(units=units, passages=passages, bytes=nbytes, books=books, skipped=skipped)


# ------------------------------------------------------------------ manifest

EDITIONS = [
    dict(id='kjv', lang='en', script='Latn', direction='ltr', label={'en': 'King James Version (with Apocrypha)'},
         role='translation', canon='kjv-apocrypha-80', families=[],
         license='Public domain', source='https://github.com/scrollmapper/bible_databases (formats/json/KJVA.json)',
         notes={'en': 'The 1769 text with the 1611 Apocrypha. The source carries no italics for translator-supplied words, so only 1 John 2:23 shows them.'}),
    dict(id='drb', lang='en', script='Latn', direction='ltr', label={'en': 'Douay-Rheims (Challoner)'},
         role='translation', canon='catholic-73', families=['catholic'],
         license='Public domain', source='https://github.com/scrollmapper/bible_databases (formats/json/DRC.json)',
         notes={'en': 'Psalms are shown under the Hebrew (KJV) psalm numbers; verse numbers within each psalm follow the Vulgate, which counts the title as verse 1. Daniel 13–14 and Esther 11–16 are the deuterocanonical additions.'}),
    dict(id='web', lang='en', script='Latn', direction='ltr', label={'en': 'World English Bible'},
         role='translation', canon='orthodox-web-84', families=[],
         license='Public domain', source='https://github.com/seven1m/open-bibles (eng-web.usfx.xml)',
         notes={'en': 'Translator footnotes are kept as notes. Esther (Greek) carries the Septuagint additions inside the Hebrew chapter numbering; the Letter of Jeremiah (Baruch 6 in the source) and Psalm 151 are shown as chapter 1.'}),
    dict(id='asv', lang='en', script='Latn', direction='ltr', label={'en': 'American Standard Version (1901)'},
         role='translation', canon='protestant-66', families=[],
         license='Public domain', source='https://github.com/seven1m/open-bibles (eng-asv.zefania.xml)'),
    dict(id='lxx-brenton', lang='en', script='Latn', direction='ltr', label={'en': "Brenton's Septuagint (1851)"},
         role='translation', canon='lxx-brenton', families=['eastern-orthodox', 'oriental-orthodox'],
         license='Public domain', source='https://github.com/bluesboy13/freebiblos (data/lxx-en.json; text from eBible.org eng-Brenton)',
         notes={'en': 'Sir Lancelot Brenton’s English translation of the Septuagint. Chapter and verse numbers follow the KJV scheme per the source; verses with no KJV counterpart carry a letter suffix (e.g. 50a).'}),
    dict(id='rvr1909', lang='es', script='Latn', direction='ltr', label={'en': 'Reina-Valera 1909', 'es': 'Reina-Valera 1909'},
         role='translation', canon='protestant-66', families=[],
         license='Public domain', source='https://github.com/seven1m/open-bibles (spa-rv1909.usfx.xml)'),
    dict(id='luther1912', lang='de', script='Latn', direction='ltr', label={'en': 'Luther Bible 1912', 'de': 'Lutherbibel 1912'},
         role='translation', canon='protestant-66', families=['lutheran'],
         license='Public domain', source='https://github.com/seven1m/open-bibles (deu-luther1912.osis.xml)'),
    dict(id='ostervald', lang='fr', script='Latn', direction='ltr', label={'en': 'Ostervald (1996 revision)', 'fr': 'Bible Ostervald (révision 1996)'},
         role='translation', canon='protestant-66', families=[],
         license='Public domain', source='https://github.com/seven1m/open-bibles (fra-ostervald.osis.xml)'),
    dict(id='vulgate', lang='la', script='Latn', direction='ltr', label={'en': 'Clementine Vulgate', 'la': 'Vulgata Clementina'},
         role='translation', canon='catholic-73', families=['catholic'],
         license='Public domain', source='https://github.com/seven1m/open-bibles (lat-clementine.usfx.xml)',
         notes={'en': 'Psalms are shown under the Hebrew (KJV) psalm numbers; verse numbers within each psalm follow the Vulgate, which counts the title as verse 1.'}),
    dict(id='crampon', lang='fr', script='Latn', direction='ltr', label={'en': 'Crampon (1923)', 'fr': 'Bible Crampon 1923'},
         role='translation', canon='catholic-73', families=['catholic'],
         license='Public domain', source='https://github.com/scrollmapper/bible_databases (formats/json/FreCrampon.json)',
         notes={'en': 'Joel has four chapters and Malachi three, following the Vulgate chapter divisions.'}),
]


def write_manifest(editions_done):
    codes_used = []
    for canon in C.CANONS.values():
        for c in canon:
            if c not in codes_used:
                codes_used.append(c)
    books = {c: {'en': C.BOOK_NAMES[c]} for c in codes_used}
    chapters = {}
    for c in codes_used:
        chapters[c] = chapters_seen.get(c, 1)
    manifest = {
        'schemaVersion': 1,
        'workId': WORK,
        'tradition': 'christianity',
        'shelf': 'scripture',
        'families': [],
        'title': {'en': 'The Bible', 'es': 'La Biblia', 'de': 'Die Bibel', 'fr': 'La Bible', 'la': 'Biblia Sacra'},
        'levels': [
            {'id': 'book', 'label': {'en': 'Book'}},
            {'id': 'chapter', 'label': {'en': 'Chapter'}, 'isUnit': True},
            {'id': 'verse', 'label': {'en': 'Verse'}},
        ],
        'citation': {'format': '{book} {chapter}:{verse}', 'rangeFormat': '{book} {chapter}:{verse}–{verse2}',
                     'workAbbrev': {'en': ''}},
        'canons': C.CANONS,
        'books': books,
        'chapters': chapters,
        'editions': [e for e in EDITIONS if e['id'] in editions_done],
        'defaultEditions': ['kjv'],
        'aliases': C.build_aliases(codes_used),
    }
    return C.write_manifest(WORK, manifest)


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sources', default=DEFAULT_SOURCES)
    ap.add_argument('--crampon', default=DEFAULT_CRAMPON)
    ap.add_argument('--only', default='')
    args = ap.parse_args()
    S = args.sources
    only = set(x for x in args.only.split(',') if x)

    jobs = [
        ('kjv', lambda: convert_scrollmapper('kjv', os.path.join(S, 'scrollmapper/KJVA.json'), kjv_brackets=True)),
        ('drb', lambda: convert_scrollmapper('drb', os.path.join(S, 'scrollmapper/DRC.json'),
                                             book_filter=set(C.CANONS['catholic-73']), vulgate_psalms=True)),
        ('web', lambda: convert_usfx('web', os.path.join(S, 'open-bibles/eng-web.usfx.xml'), keep_notes=True)),
        ('asv', lambda: convert_zefania('asv', os.path.join(S, 'open-bibles/eng-asv.zefania.xml'))),
        ('lxx-brenton', lambda: convert_lxx('lxx-brenton', os.path.join(S, 'freebiblos/lxx-en.json'))),
        ('rvr1909', lambda: convert_usfx('rvr1909', os.path.join(S, 'open-bibles/spa-rv1909.usfx.xml'))),
        ('luther1912', lambda: convert_osis('luther1912', os.path.join(S, 'open-bibles/deu-luther1912.osis.xml'))),
        ('ostervald', lambda: convert_osis('ostervald', os.path.join(S, 'open-bibles/fra-ostervald.osis.xml'))),
        ('vulgate', lambda: convert_usfx('vulgate', os.path.join(S, 'open-bibles/lat-clementine.usfx.xml'), vulgate_psalms=True)),
        ('crampon', lambda: convert_scrollmapper('crampon', args.crampon, book_filter=set(C.CANONS['catholic-73']))),
    ]
    done = []
    for ed, fn in jobs:
        if only and ed not in only:
            # keep an existing edition folder in the manifest if present
            if os.path.isdir(os.path.join(C.WORKS, WORK, ed)):
                done.append(ed)
            continue
        print(f'== {ed}', flush=True)
        fn()
        r = report[ed]
        done.append(ed)
        print(f'   {len(r["books"])} books, {r["units"]} units, {r["passages"]} passages, {r["bytes"]/1048576:.2f} MB; '
              f'{len(r["skipped"])} skipped')
        for s in r['skipped'][:12]:
            print('     -', s)
        if len(r['skipped']) > 12:
            print(f'     - ... {len(r["skipped"]) - 12} more')
    # chapters_seen only knows about editions converted in this run; when --only is used, recover the
    # rest by scanning the existing folders.
    for ed in done:
        edir = os.path.join(C.WORKS, WORK, ed)
        for fn in os.listdir(edir):
            m = re.match(r'([0-9a-z]+)-(\d+)\.json$', fn)
            if m:
                note_chapter(m.group(1), int(m.group(2)))
    mbytes = write_manifest(done)
    total = sum(report[e]['bytes'] for e in report) + mbytes
    print(f'manifest: {mbytes/1024:.1f} KB; total written this run: {total/1048576:.2f} MB')


if __name__ == '__main__':
    main()
