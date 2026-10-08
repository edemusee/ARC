#!/usr/bin/env python3
"""Convert 1 Enoch and Jubilees (R. H. Charles, 1917) from The-Book's docs/data/works/*.json into
works/enoch/ and works/jubilees/ (one edition each: en-charles).

Usage (from the reader root):
    python3 -I convert/bible/convert_enoch_jubilees.py [--sources DIR]

Cleanup done on the way (the source is an OCR-derived transcription of Charles):
  - "[[[[" / "]]]]" residue collapsed; Charles's double brackets (interpolations) are then rendered as
    ⟦ ⟧ so they do not collide with the reader's own [[supplied word]] markup; "+word+" (the source's
    stand-in for Charles's daggers) becomes †word†; "[*1]" footnote callouts are dropped.
  - Footnote-number residue (stray 1–2 digit numbers in the text) is stripped unless the number is a
    count ("in 5 years 6 days", "2 palms") or part of a range or a date.
  - Marginal Anno Mundi dates in Jubilees ("2122 A.M.") were inlined mid-sentence by the source; they are
    moved to the end of their verse in parentheses.
  - Charles's section headings ("XXII. Sheol, or the Underworld.") that were glued onto the end of the
    preceding verse become the `heading` of the next passage.
  - Several source "verses" hold a run of verses ("Gg 5. I saw ... 6. And I asked ..."): they are split
    at the inline verse numbers when the numbers run in sequence.
  - Prose-only chapters ("paras") are split at inline verse numbers when present, otherwise each
    paragraph becomes a sequentially numbered passage.
  - Known structural slips of the source: Enoch's "chapter 77" is Charles's chapter 78 (77 is absent);
    chapter 102 is recovered from the tail of chapter 101; Jubilees' "Prologue" (verses 1–26) and prose
    "chapter 1" (verses 27–29) are Jubilees 1.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

DEFAULT_SOURCES = '/tmp/claude-0/-home-claude/7a651a9d-c615-572e-93d2-9ae13aaa0c8d/scratchpad/sources/christianity'

ROMAN = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}


def roman_to_int(s):
    total, prev = 0, 0
    for ch in reversed(s):
        v = ROMAN[ch]
        total = total - v if v < prev else total + v
        prev = max(prev, v)
    return total


UNIT_WORDS = r'(?:days?|years?|months?|weeks?|cubits?|palms?|bricks?|parts?|portals?|times|windows?|gates?|hours?|stars?|leaders?)'
# A stray footnote number: 1–2 digits standing alone.
FOOTNOTE_NUM = re.compile(
    r'(?<![\w.\-–(/])(\d{1,2})(?![\w.\-–)/%]|,\d)'
    r'(?!\s' + UNIT_WORDS + r'\b)'
)
COUNT_CONTEXT = re.compile(r'(?:\b(?:in|to|are|than|about|amounts? to|number of)\s)$')
HEADING_TAIL = re.compile(
    r"(?<=[.!?'\"’”\]\)])\s+("                                       # after sentence end
    r"(?:[A-Z][A-Z' \-]{3,}\.?\s?\((?:[IVXLC]+[-–]?)+\.?\)(?:\s.*)?"   # uppercase title "(LXXXIII-XC.)" ...
    r"|(?:[IVXLC]{2,}|[VXLC])[\.\-–](?:\s?[IVXLC]+[\.\-–])*\s?.*))$")  # ... or roman numeral(s) then title
HEADING_START = re.compile(r"^(?:[A-Z][A-Z' \-]{3,}\.?\s?\((?:[IVXLC]+[-–]?)+\.?\)\s?)?(?:[IVXLC]{2,}|[VXLC])[\.\-–]")
VERSE_MARK = re.compile(r'(?:(?<=^)|(?<=\s)|(?<=\[)|(?<=\⟦))(\d{1,3})([a-d]?)\s?[.,]?\s')
AM_DATE = re.compile(r'\s*\b(\d{2,4}(?:-\d{2,4})?(?:\s\(\?\d{3,4}\))?)\s?A\.M\.\s*')


LITERAL_FIXES = [
    ('for sinners E been made for sinners', 'for sinners'),      # Enoch 22:10: two MS readings run together
]


def base_clean(t):
    for a, b in LITERAL_FIXES:
        t = t.replace(a, b)
    t = t.replace('[[[[', '[[').replace(']]]]', ']]')
    t = t.replace('[[', '⟦').replace(']]', '⟧')
    t = re.sub(r'\[\*\d+\]', '', t)
    t = re.sub(r'<([^<>]{1,120})>', '⟨\\1⟩', t)            # Charles's angle brackets (words from the Greek)
    t = re.sub(r'\+([^+]{1,120}?)\+', r'†\1†', t)
    t = t.replace('+', '†')                              # an unpaired dagger
    t = re.sub(r'\[Editorial note:[^\]]*\]', '', t)
    t = t.replace('(A.M. = Anno Mundi)', '')
    t = t.replace('195 I A.M.', '1951 A.M.')
    t = re.sub(r'\bA\s?M\.(?=\s)', 'A.M.', t)          # "A M." / "AM." -> "A.M."
    t = re.sub(r'\s(?:Gg|E)\s(?=\d{1,3}\s?[.,]?\s)', ' ', t)   # manuscript sigla before verse numbers
    return t


NUMBER_WORD = re.compile(
    r'(?:[a-z]+-)?(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|'
    r'(?:thir|four|fif|six|seven|eigh|nine)teenth|(?:twen|thir|for|fif|six|seven|eigh|nine)tieth|'
    r'one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|(?:thir|four|fif|six|seven|eigh|nine)teen|'
    r'(?:twen|thir|for|fif|six|seven|eigh|nine)ty|hundred|thousand)†?\s$')
# the same number standing alone, whatever follows ("the sixth 4 day")
BARE_NUM = re.compile(r'(?<![\w.\-–(/])(\d{1,2})(?![\w.\-–)/%]|,\d)')


def strip_footnote_numbers(t):
    out, pos = [], 0
    for m in BARE_NUM.finditer(t):
        before = t[:m.start()]
        if NUMBER_WORD.search(before):
            pass                                   # "the sixth 4 day": footnote after a number word
        elif not FOOTNOTE_NUM.match(t, m.start()):
            continue                               # a count followed by a unit word
        elif COUNT_CONTEXT.search(before):
            continue
        out.append(t[pos:m.start()])
        pos = m.end()
    out.append(t[pos:])
    t = ''.join(out)
    t = re.sub(r'(?<=\w)\s+([.,;:!?])(?=\s(?![.])|$)', r'\1', t)   # "them. 6" -> "them."; keep ". . ."
    t = re.sub(r'\s{2,}', ' ', t)
    return t.strip()


def move_am_dates(t):
    dates = []

    def grab(m):
        dates.append(m.group(1))
        return ' '
    t = AM_DATE.sub(grab, t)
    t = re.sub(r'\s{2,}', ' ', t).strip()
    if dates:
        t = t + ' (' + '; '.join(d + ' A.M.' for d in dates) + ')'
    return t


def split_heading_tail(t):
    """Return (text, heading) where heading is a Charles section title glued to the end of the text."""
    m = HEADING_TAIL.search(t)
    if not m:
        return t, None
    head = m.group(1).strip()
    if len(head) < 6:
        return t, None
    return t[:m.start()].rstrip(), head


def heading_chapter(head):
    """The chapter a heading names, when it names exactly one ("XXII. Sheol" -> 22), else None."""
    m = re.match(r'^(?:[A-Z][A-Z\' \-]{3,}\.?\s?\([^)]*\)\s?)?([IVXLC]+)\.\s', head)
    if not m:
        return None
    return roman_to_int(m.group(1))


class Chapter:
    def __init__(self, n):
        self.n = n
        self.passages = []       # dicts: v, text, heading


class WorkBuilder:
    def __init__(self, work_id, is_jubilees=False):
        self.work_id = work_id
        self.is_jubilees = is_jubilees
        self.chapters = {}       # n -> Chapter
        self.pending_heading = None
        self.cur = None

    def chapter(self, n):
        if n not in self.chapters:
            self.chapters[n] = Chapter(n)
        self.cur = self.chapters[n]
        return self.cur

    def push(self, v, text, heading=None):
        text = text.strip()
        if not text:
            return
        if self.pending_heading:
            # a heading that names one chapter is dropped when it would open a different chapter
            hc = heading_chapter(self.pending_heading)
            if hc is None or hc == self.cur.n or self.cur.passages:
                heading = (self.pending_heading + (' ' + heading if heading else ''))
            self.pending_heading = None
        ch = self.cur
        # continuation of the previous verse (same number) -> join with a line break
        if ch.passages and ch.passages[-1]['v'] == v:
            prev = ch.passages[-1]['text']
            sep = '\n' if prev[-1] in '.!?\'"’”)]⟧:;' else ' '   # mid-sentence page break -> space
            ch.passages[-1]['text'] += sep + text
            return
        ch.passages.append({'v': v, 'text': text, 'heading': heading})

    def finish_text(self, t):
        t = strip_footnote_numbers(t)
        if self.is_jubilees:
            t = move_am_dates(t)
        return t

    # -- feed a stream of (v, raw text) items that belong to chapter n; items may contain further verses
    def feed_verses(self, n, items):
        self.chapter(n)
        expected = 1
        for v, raw in items:
            t = base_clean(raw)
            # chapter switch inside a verse ("Chapter CII. 1. In those days ...")
            m = re.search(r'\s*Chapter ([IVXLC]+)\.\s(?=1\.)', t)
            if m:
                head_part, rest = t[:m.start()], t[m.end():]
                self._feed_one(v, head_part, expected)
                expected = max(expected, v + 1)
                newn = roman_to_int(m.group(1))
                self.chapter(newn)
                expected = 1
                v = 0
                t = rest
            expected = self._feed_one(v, t, expected)

    def _feed_one(self, v, t, expected):
        """Push one source verse; split at inline verse numbers that run in sequence. Returns next expected.

        A number splits the text only when it is the next expected verse number, stands at a sentence
        boundary, and is followed by its own period/comma or a capitalised word. Footnote residue
        ("thy beloved 3 son") fails those tests and is stripped later.
        """
        t, head = split_heading_tail(t)
        pieces = []
        cur_v = v if v else None
        pos = 0
        exp = max(expected, v + 1) if v else expected
        saw_lower = False
        for m in VERSE_MARK.finditer(t):
            num, suffix = int(m.group(1)), m.group(2)
            prev = t[:m.start()].rstrip()
            at_start = prev == ''
            own_punct = m.group(0).rstrip().endswith(('.', ','))
            nxt = t[m.end():m.end() + 1]
            next_ok = own_punct or (nxt != '' and (nxt.isupper() or nxt in '"\'“‘[(⟦⟨'))
            boundary = not at_start and prev[-1] in ".!?'\"’”)]⟧[⟦:;" and next_ok and not suffix
            if boundary and v and num < v:
                saw_lower = True
            if boundary and v and num == v and saw_lower and not pieces and cur_v == v:
                # the source repeated earlier verses (a second manuscript reading) before this verse's
                # own number: keep only what follows the verse's own number
                pos = m.end()
                continue
            if at_start:
                if cur_v is None and num == expected and not suffix:
                    cur_v, pos, exp = num, m.end(), num + 1
                elif num == v and not suffix:
                    pos = m.end()
                continue
            if suffix or m.start() < pos:
                continue
            if num == exp and prev[-1] in ".!?'\"’”)]⟧[⟦:;" and next_ok:
                pieces.append((cur_v if cur_v is not None else (v or expected), t[pos:m.start()]))
                cur_v, pos, exp = num, m.end(), num + 1
        pieces.append((cur_v if cur_v is not None else (v or expected), t[pos:]))
        for pv, ptxt in pieces:
            ptxt = self.finish_text(ptxt)
            if ptxt:
                self.push(pv, ptxt)
        if head:
            self.pending_heading = head
        return max(exp, (pieces[-1][0] + 1) if pieces else exp)

    def feed_paras(self, n, paras, start_v=1):
        """Prose-only chapter: split at inline verse numbers if they exist, else number paragraphs."""
        self.chapter(n)
        numbered = any(re.match(r'^\s*\d{1,3}[a-d]?\s?[.,]?\s', p) for p in paras)
        expected = start_v
        seq = start_v
        prev_was_heading = False
        for p in paras:
            p = base_clean(p).strip()
            if not p:
                continue
            is_heading = bool(HEADING_START.match(p)) or (prev_was_heading and len(p) < 100 and p[0].isupper()
                                                           and not re.match(r'^\d', p) and p.endswith('.')
                                                           and not p.startswith('And '))
            if p in ('Close of the Third Parable.',):
                is_heading = True
            if is_heading:
                self.pending_heading = ((self.pending_heading + ' ') if self.pending_heading else '') + p
                prev_was_heading = True
                continue
            prev_was_heading = False
            if numbered:
                m = re.match(r'^(\d{1,3})[a-d]?\s?[.,]?\s', p)
                if m:
                    v = int(m.group(1))
                    p = p[m.end():]
                    if v < expected:            # out-of-order residue: treat as continuation
                        v = max(expected - 1, start_v)
                    expected = self._feed_one(v, p, v + 1)
                    expected = max(expected, v + 1)
                else:
                    # unnumbered paragraph inside a numbered chapter: continuation of the last verse
                    last = self.cur.passages[-1]['v'] if self.cur.passages else max(expected - 1, start_v)
                    self._feed_one(last, p, expected)
            else:
                seq = self._feed_one(seq, p, seq + 1)

    # -- output
    def write(self, edition_id, label, notes, families, toc_label):
        w = C.Writer(self.work_id, edition_id)
        toc = []
        gaps = []
        for n in sorted(self.chapters):
            ch = self.chapters[n]
            unit = str(n)
            count = 0
            seen = set()
            for p in ch.passages:
                ref = f'{unit}:{p["v"]}'
                if p['v'] in seen:
                    gaps.append(f'duplicate {ref} merged')
                    continue
                seen.add(p['v'])
                if w.add(unit, ref, p['text'], heading=p['heading']):
                    count += 1
            if count:
                toc.append({'ref': unit, 'label': {'en': f'{toc_label} {n}'}, 'count': count})
        units, passages, nbytes = w.flush()
        return toc, units, passages, nbytes, gaps


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def build_enoch(S):
    base = os.path.join(S, 'The-Book/docs/data/works')
    files = ['1-enoch-the-book-of-the-watchers-chapters-1-36.json',
             '1-enoch-the-book-of-parables-chapters-37-71.json',
             '1-enoch-the-astronomical-book-chapters-72-82.json',
             '1-enoch-dream-visions-and-the-epistle-of-enoch-chapters-83-108.json']
    b = WorkBuilder('enoch')
    for fn in files:
        d = load(os.path.join(base, fn))
        for c in d['chapters']:
            n = c['n']
            if fn.startswith('1-enoch-the-astronomical') and n == 77:
                n = 78            # the source's "77" is Charles's chapter 78 (see module docstring)
                b.pending_heading = None
            if c.get('verses'):
                b.feed_verses(n, [(v['v'], v['t']) for v in c['verses']])
            else:
                b.feed_paras(n, c.get('paras') or [])
    return b


def build_jubilees(S):
    d = load(os.path.join(S, 'The-Book/docs/data/works/jubilees.json'))
    b = WorkBuilder('jubilees', is_jubilees=True)
    for c in d['chapters']:
        n = c['n']
        if n == 0:
            n = 1                 # "Prologue" holds Jubilees 1:1-26
        if c.get('verses'):
            items = []
            for v in c['verses']:
                t = v['t']
                if v['v'] == 1:
                    # drop the roman chapter numeral that opens some chapters ("1317 A.M. VII. And ...")
                    t = re.sub(r'^(\d{1,2}\s)?((?:\d{3,4}(?:-\d{3,4})?(?:\s\(\?\d+\))?\s?A\.?\s?M\.\s)?)[IVXLC]+\.\s', r'\2', t)
                items.append((v['v'], t))
            b.feed_verses(n, items)
        else:
            start = 27 if n == 1 else 1
            b.feed_paras(n, c.get('paras') or [], start_v=start)
    return b


def manifest(work_id, title, abbrev, toc, edition, notes):
    return {
        'schemaVersion': 1,
        'workId': work_id,
        'tradition': 'christianity',
        'shelf': 'scripture',
        'families': ['oriental-orthodox'],
        'title': {'en': title},
        'levels': [
            {'id': 'chapter', 'label': {'en': 'Chapter'}, 'isUnit': True},
            {'id': 'verse', 'label': {'en': 'Verse'}},
        ],
        'citation': {'format': '{work} {chapter}:{verse}', 'rangeFormat': '{work} {chapter}:{verse}–{verse2}',
                     'workAbbrev': {'en': abbrev}},
        'toc': toc,
        'editions': [edition],
        'defaultEditions': ['en-charles'],
        'aliases': {},
        'notes': {'en': notes},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sources', default=DEFAULT_SOURCES)
    args = ap.parse_args()
    S = args.sources
    total = 0
    for work_id, builder, title, abbrev, toc_label, notes in [
        ('enoch', build_enoch, '1 Enoch', '1 Enoch', 'Chapter',
         'R. H. Charles’s 1917 translation from the Ethiopic. ⟦ ⟧ mark material Charles judged interpolated, [ ] his restorations, ⟨ ⟩ words supplied from the Greek, ( ) words supplied for sense, † † corrupt text. Chapters 77 and 91:1–11 are missing from the source transcription.'),
        ('jubilees', build_jubilees, 'Jubilees', 'Jubilees', 'Chapter',
         'R. H. Charles’s 1917 translation from the Ethiopic. [ ] mark his restorations, ( ) words supplied for sense, † † corrupt text; marginal Anno Mundi dates are given in parentheses at the end of the verse. The prologue and 18:17–19 are missing from the source transcription.'),
    ]:
        edir = os.path.join(C.WORKS, work_id)
        if os.path.isdir(edir):
            import shutil
            shutil.rmtree(edir)
        b = builder(S)
        edition = dict(id='en-charles', lang='en', script='Latn', direction='ltr',
                       label={'en': 'R. H. Charles (1917)'}, role='translation', families=[],
                       license='Public domain (Charles 1917; The-Book LICENSE-DATA.md)',
                       source='https://github.com/TheoryofShadows/The-Book (docs/data/works/*.json)')
        toc, units, passages, nbytes, gaps = b.write('en-charles', edition['label'], notes, [], toc_label)
        m = manifest(work_id, title, abbrev, toc, edition, notes)
        mb = C.write_manifest(work_id, m)
        total += nbytes + mb
        print(f'== {work_id}: {units} units, {passages} passages, {(nbytes + mb)/1048576:.2f} MB; chapters '
              f'{min(b.chapters)}–{max(b.chapters)} ({len(toc)} present)')
        for g in gaps:
            print('   -', g)
    print(f'total written: {total/1048576:.2f} MB')


if __name__ == '__main__':
    main()
