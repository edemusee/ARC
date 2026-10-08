#!/usr/bin/env python3
"""Convert the Latter-day Saint standard works (except the KJV, already in the library as `bible`) from the
python-scripture-scraper sample JSON (2013 edition text, copyrighted study helps excluded by the scraper).

Usage (from the reader root):  python3 -I convert/lds/convert_lds.py [--only id1,id2]

Works written: book-of-mormon, doctrine-and-covenants, pearl-of-great-price, articles-of-faith, jst-appendix.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

SRC = lambda sub: f'{C.REPO} (sample/en-json/{sub})'  # noqa: E731
PD_2013 = ('Verse text public domain; 2013 edition typographic corrections; '
           'chapter/section headings and summaries excluded as copyrighted')

# ----------------------------------------------------------------- Bible-like helpers


def bible_like(work_id, shelf, title, subtitle, books, canon_id, edition, aliases, notes, sub_root, extra_heading=None,
               skip_file=None, verse_notes=None):
    """books: [(code, dirname, display name)] in canonical order."""
    C.reset_work(work_id)
    chapters, units, passages = {}, 0, 0
    for code, dirname, name in books:
        files = C.chapter_files(f'{sub_root}/{dirname}')
        if skip_file:
            files = [(n, p) for n, p in files if not skip_file(p)]
        chapters[code] = max(n for n, _ in files)
        for n, path in files:
            doc = C.load_chapter(path)
            out = []
            for vnum, text, pending in C.verses(doc):
                p = {'ref': f'{code}:{n}:{vnum}', 'text': text}
                head = heading_from(pending)
                if head:
                    p['heading'] = head
                if verse_notes:
                    vn = verse_notes(doc, code, n, vnum, text)
                    if vn:
                        p['notes'] = vn
                out.append(p)
            C.write_unit(work_id, edition['id'], f'{code}:{n}', out)
            units += 1
            passages += len(out)
    manifest = {
        'schemaVersion': 1, 'workId': work_id, 'tradition': C.TRAD, 'shelf': shelf, 'families': [],
        'title': {'en': title},
    }
    if subtitle:
        manifest['subtitle'] = {'en': subtitle}
    manifest.update({
        'levels': [{'id': 'book', 'label': {'en': 'Book'}}, {'id': 'chapter', 'label': {'en': 'Chapter'}, 'isUnit': True},
                   {'id': 'verse', 'label': {'en': 'Verse'}}],
        'citation': {'format': '{book} {chapter}:{verse}', 'rangeFormat': '{book} {chapter}:{verse}–{verse2}',
                     'workAbbrev': {'en': ''}},
        'canons': {canon_id: [c for c, _, _ in books]},
        'books': {c: {'en': name} for c, _, name in books},
        'chapters': chapters,
        'editions': [dict(edition, canon=canon_id)],
        'defaultEditions': [edition['id']],
        'aliases': aliases,
    })
    if notes:
        manifest['notes'] = {'en': notes}
    C.write_manifest(work_id, manifest)
    C.report(work_id, shelf, [], [edition['id']], units, passages)


def heading_from(pending):
    """Fold the title/subtitle/intro paragraphs that precede a verse into one heading string."""
    parts = []
    title = None
    for kind, text, _cid in pending:
        if not text or set(text) <= set('· .'):
            continue
        if kind == 'book-title':
            title = text
        elif kind in ('book-subtitle', 'chapter-subtitle'):
            if title and kind == 'book-subtitle':
                title = f'{title} · {text}'
            else:
                parts.append(text)
        else:  # paragraph (1830 book heading), section-title (JST excerpt title)
            parts.append(text)
    if title:
        parts.insert(0, title)
    return ' — '.join(parts) if parts else None


# ----------------------------------------------------------------- Book of Mormon

BOFM = [
    ('1ne', '1-nephi', '1 Nephi'), ('2ne', '2-nephi', '2 Nephi'), ('jac', 'jacob', 'Jacob'), ('enos', 'enos', 'Enos'),
    ('jar', 'jarom', 'Jarom'), ('omni', 'omni', 'Omni'), ('wom', 'words-of-mormon', 'Words of Mormon'),
    ('mos', 'mosiah', 'Mosiah'), ('alma', 'alma', 'Alma'), ('hel', 'helaman', 'Helaman'), ('3ne', '3-nephi', '3 Nephi'),
    ('4ne', '4-nephi', '4 Nephi'), ('morm', 'mormon', 'Mormon'), ('eth', 'ether', 'Ether'), ('moro', 'moroni', 'Moroni'),
]
BOFM_ALIASES = {
    '1ne': ['1 nephi', '1 ne', '1nephi', 'first nephi', 'i nephi'], '2ne': ['2 nephi', '2 ne', '2nephi', 'second nephi', 'ii nephi'],
    'jac': ['jacob', 'jcb'], 'enos': ['enos'], 'jar': ['jarom'], 'omni': ['omni'], 'wom': ['words of mormon', 'w of m', 'wofm'],
    'mos': ['mosiah'], 'alma': ['alma'], 'hel': ['helaman'], '3ne': ['3 nephi', '3 ne', '3nephi', 'third nephi', 'iii nephi'],
    '4ne': ['4 nephi', '4 ne', '4nephi', 'fourth nephi', 'iv nephi'], 'morm': ['mormon', 'morm.'], 'eth': ['ether'],
    'moro': ['moroni'],
}


def convert_bofm():
    ed = C.edition('en-2013', 'English (2013 edition)',
                   'Verse text public domain (1830/1920 text); 2013 edition typographic corrections; '
                   'chapter summaries excluded as copyrighted', SRC('book-of-mormon'),
                   notes='Book titles and the original 1830 book headings (e.g. "An account of Lehi…") are shown as headings on '
                         'the first verse of the chapters that carry them; the modern chapter summaries are not included.')
    bible_like('book-of-mormon', 'scripture', 'The Book of Mormon', 'Another Testament of Jesus Christ', BOFM, 'bofm-15', ed,
               BOFM_ALIASES, 'The Book of Mormon in the 2013 edition text (title page, witness testimonies and chapter summaries not included).',
               'book-of-mormon')


# ----------------------------------------------------------------- Pearl of Great Price

PGP = [
    ('moses', 'moses', 'Moses'), ('abr', 'abraham', 'Abraham'), ('jsm', 'joseph-smith-matthew', 'Joseph Smith—Matthew'),
    ('jsh', 'joseph-smith-history', 'Joseph Smith—History'), ('aof', 'articles-of-faith', 'Articles of Faith'),
]
PGP_ALIASES = {
    'moses': ['moses', 'book of moses'], 'abr': ['abraham', 'abr', 'book of abraham'],
    'jsm': ['joseph smith matthew', 'joseph smith—matthew', 'js-m', 'jsm', 'js matthew', 'js—m'],
    'jsh': ['joseph smith history', 'joseph smith—history', 'js-h', 'jsh', 'js history', 'js—h'],
    'aof': ['articles of faith', 'a of f', 'aof', 'a-of-f'],
}


def jsh_notes(doc, code, n, vnum, text):
    """The Oliver Cowdery excerpt printed after JS—H 1:75 (footnote to v. 71) becomes a note on verse 71."""
    if code != 'jsh' or vnum != 71:
        return None
    paras = [C.from_html(p['contentHtml']) for p in doc['paragraphs']
             if p['type'] == 'paragraph' and re.fullmatch(r'p\d+', p.get('churchId') or '')]
    paras = [t for t in paras if t and not set(t) <= set('· ')]
    if not paras:
        return None
    return [{'at': len(text), 'text': 'Footnote (printed after verse 75): ' + '\n'.join(paras)}]


def convert_pgp():
    ed = C.edition('en-2013', 'English (2013 edition)', PD_2013, SRC('pearl-of-great-price'),
                   notes='The three Facsimiles from the Book of Abraham are not included. Dates of the Moses chapters are shown as headings.')
    bible_like('pearl-of-great-price', 'scripture', 'The Pearl of Great Price',
               'Selections from the revelations, translations and narrations of Joseph Smith', PGP, 'pgp-5', ed, PGP_ALIASES,
               'The Pearl of Great Price in the 2013 edition text; facsimiles not included.', 'pearl-of-great-price',
               skip_file=lambda p: '-fac-' in p, verse_notes=jsh_notes)


# ----------------------------------------------------------------- Doctrine and Covenants

def convert_dc():
    work = 'doctrine-and-covenants'
    C.reset_work(work)
    toc, aliases, units, passages = [], {}, 0, 0
    for n, path in C.chapter_files('doctrine-and-covenants/sections'):
        doc = C.load_chapter(path)
        out = []
        for vnum, text, pending in C.verses(doc):
            p = {'ref': f'{n}:{vnum}', 'text': text}
            head = heading_from([x for x in pending if x[0] != 'book-title'])
            if head:
                p['heading'] = head
            out.append(p)
        C.write_unit(work, 'en-2013', str(n), out)
        toc.append({'ref': str(n), 'label': {'en': f'Section {n}'}, 'count': len(out)})
        aliases[str(n)] = [f'section {n}', f'sec {n}', f'd&c {n}', f'dc {n}']
        units += 1
        passages += len(out)
    # Official Declaration 1 (1890): paragraphs, not verses. OD 2 (1978) is excluded by the scraper as copyrighted.
    doc = C.load_chapter(os.path.join(C.SOURCES, 'doctrine-and-covenants/official-declarations/official-declaration-1.json'))
    out, k, pending = [], 0, None
    for p in doc['paragraphs']:
        text = C.from_html(p['contentHtml'])
        if p['type'] == 'section-title':
            pending = text
            continue
        if p['type'] != 'paragraph' or not text:
            continue
        k += 1
        q = {'ref': f'od1:{k}', 'text': text}
        if pending:
            q['heading'] = pending
            pending = None
        out.append(q)
    C.write_unit(work, 'en-2013', 'od1', out)
    toc.append({'ref': 'od1', 'label': {'en': 'Official Declaration 1 (1890)'}, 'count': len(out)})
    aliases['od1'] = ['official declaration 1', 'od 1', 'od1', 'manifesto']
    units += 1
    passages += len(out)
    ed = C.edition('en-2013', 'English (2013 edition)', PD_2013, SRC('doctrine-and-covenants'),
                   notes='The section headings (with dates and historical introductions) are not included; Official Declaration 2 (1978) '
                         'is excluded as copyrighted. Official Declaration 1 is shown by paragraph.')
    manifest = {
        'schemaVersion': 1, 'workId': work, 'tradition': C.TRAD, 'shelf': 'scripture', 'families': [],
        'title': {'en': 'The Doctrine and Covenants'},
        'subtitle': {'en': 'Revelations given to Joseph Smith and his successors, with Official Declaration 1'},
        'levels': [{'id': 'section', 'label': {'en': 'Section'}, 'isUnit': True}, {'id': 'verse', 'label': {'en': 'Verse'}}],
        'citation': {'format': '{work} {section}:{verse}', 'rangeFormat': '{work} {section}:{verse}–{verse2}', 'workAbbrev': {'en': 'D&C'}},
        'toc': toc, 'editions': [ed], 'defaultEditions': ['en-2013'], 'aliases': aliases,
        'notes': {'en': 'The Doctrine and Covenants in the 2013 edition text, 138 sections and Official Declaration 1.'},
    }
    C.write_manifest(work, manifest)
    C.report(work, 'scripture', [], ['en-2013'], units, passages)


# ----------------------------------------------------------------- Articles of Faith

def convert_aof():
    work = 'articles-of-faith'
    C.reset_work(work)
    doc = C.load_chapter(os.path.join(C.SOURCES, 'pearl-of-great-price/articles-of-faith/articles-of-faith-1.json'))
    out = [{'ref': f'1:{v}', 'text': t} for v, t, _ in C.verses(doc)]
    out[0]['heading'] = 'The Articles of Faith of The Church of Jesus Christ of Latter-day Saints'
    C.write_unit(work, 'en', '1', out)
    ed = C.edition('en', 'English', 'Public domain (Wentworth Letter, 1842); text as in the 2013 edition', SRC('pearl-of-great-price/articles-of-faith'))
    manifest = {
        'schemaVersion': 1, 'workId': work, 'tradition': C.TRAD, 'shelf': 'documents', 'families': [],
        'title': {'en': 'The Articles of Faith'}, 'subtitle': {'en': 'Joseph Smith, 1842'},
        'levels': [{'id': 'section', 'label': {'en': 'Section'}, 'isUnit': True}, {'id': 'article', 'label': {'en': 'Article'}}],
        'citation': {'format': '{work} {article}', 'rangeFormat': '{work} {article}–{article2}', 'workAbbrev': {'en': 'A of F'}},
        'toc': [{'ref': '1', 'label': {'en': 'The Articles of Faith'}, 'count': len(out)}],
        'editions': [ed], 'defaultEditions': ['en'],
        'aliases': {'1': ['articles of faith', 'a of f', 'aof', 'article']},
        'notes': {'en': 'The thirteen Articles of Faith, from the Wentworth Letter of 1842, as printed in the Pearl of Great Price.'},
    }
    C.write_manifest(work, manifest)
    C.report(work, 'documents', [], ['en'], 1, len(out))


# ----------------------------------------------------------------- JST appendix

JST_BOOKS = [  # (jst dirname, code, name) in biblical order
    ('jst-genesis', 'gen', 'Genesis'), ('jst-exodus', 'exo', 'Exodus'), ('jst-deuteronomy', 'deu', 'Deuteronomy'),
    ('jst-1-samuel', '1sa', '1 Samuel'), ('jst-2-samuel', '2sa', '2 Samuel'), ('jst-1-chronicles', '1ch', '1 Chronicles'),
    ('jst-2-chronicles', '2ch', '2 Chronicles'), ('jst-psalms', 'psa', 'Psalms'), ('jst-isaiah', 'isa', 'Isaiah'),
    ('jst-jeremiah', 'jer', 'Jeremiah'), ('jst-amos', 'amo', 'Amos'), ('jst-matthew', 'mat', 'Matthew'), ('jst-mark', 'mrk', 'Mark'),
    ('jst-luke', 'luk', 'Luke'), ('jst-john', 'jhn', 'John'), ('jst-acts', 'act', 'Acts'), ('jst-romans', 'rom', 'Romans'),
    ('jst-1-corinthians', '1co', '1 Corinthians'), ('jst-2-corinthians', '2co', '2 Corinthians'), ('jst-galatians', 'gal', 'Galatians'),
    ('jst-ephesians', 'eph', 'Ephesians'), ('jst-colossians', 'col', 'Colossians'), ('jst-1-thessalonians', '1th', '1 Thessalonians'),
    ('jst-2-thessalonians', '2th', '2 Thessalonians'), ('jst-1-timothy', '1ti', '1 Timothy'), ('jst-hebrews', 'heb', 'Hebrews'),
    ('jst-james', 'jas', 'James'), ('jst-1-peter', '1pe', '1 Peter'), ('jst-2-peter', '2pe', '2 Peter'), ('jst-1-john', '1jn', '1 John'),
    ('jst-revelation', 'rev', 'Revelation'),
]


def convert_jst():
    work = 'jst-appendix'
    root = os.path.join(C.SOURCES, 'jst-appendix')
    if not os.path.isdir(root):
        print('jst-appendix: source not present; skipped')
        return
    C.reset_work(work)
    present = set(os.listdir(root))
    missing = present - {d for d, _, _ in JST_BOOKS}
    assert not missing, f'unmapped JST folders: {missing}'
    toc, aliases, units, passages = [], {}, 0, 0
    for dirname, code, name in JST_BOOKS:
        if dirname not in present:
            continue
        children = []
        for n, path in C.chapter_files(f'jst-appendix/{dirname}'):
            doc = C.load_chapter(path)
            unit = f'{code}-{n}'
            out = []
            for vnum, text, pending in C.verses(doc):
                p = {'ref': f'{unit}:{vnum}', 'text': text}
                head = heading_from(pending)
                if head:
                    p['heading'] = head
                out.append(p)
            if not out:  # jst-genesis-1-8.json is only a pointer ("JST, Genesis 1:1–8:18" = Moses 1–8)
                continue
            C.write_unit(work, 'en', unit, out)
            children.append({'ref': unit, 'label': {'en': f'{name} {n}'}, 'count': len(out)})
            aliases[unit] = [f'jst {name.lower()} {n}', f'jst, {name.lower()} {n}', f'{name.lower()} {n}', f'{code} {n}', f'jst {code} {n}']
            units += 1
            passages += len(out)
        toc.append({'ref': code, 'label': {'en': f'JST, {name}'}, 'children': children})
    ed = C.edition('en', 'English (Joseph Smith Translation excerpts)',
                   'JST text public domain (1867 Inspired Version); excerpt selection and titles as in the 2013 edition appendix',
                   SRC('jst-appendix'),
                   notes='Italics mark the words that differ from the King James text, as in the printed appendix. Verse numbers are the '
                         'JST verse numbers; each excerpt title names the KJV passage to compare.')
    manifest = {
        'schemaVersion': 1, 'workId': work, 'tradition': C.TRAD, 'shelf': 'documents', 'families': [],
        'title': {'en': 'Joseph Smith Translation — Appendix Excerpts'},
        'subtitle': {'en': 'Selections from the Joseph Smith Translation of the Bible, as printed in the LDS edition appendix'},
        'levels': [{'id': 'chapter', 'label': {'en': 'Chapter'}, 'isUnit': True}, {'id': 'verse', 'label': {'en': 'Verse'}}],
        'citation': {'format': '{work} {chapter}:{verse}', 'rangeFormat': '{work} {chapter}:{verse}–{verse2}', 'workAbbrev': {'en': 'JST'}},
        'toc': toc, 'editions': [ed], 'defaultEditions': ['en'], 'aliases': aliases,
        'notes': {'en': 'Excerpts too long for the Bible footnotes, printed as an appendix in the LDS edition of the King James Bible; JST Genesis 1:1–8:18 is not repeated here: it is the Book of Moses in the Pearl of Great Price.'},
    }
    C.write_manifest(work, manifest)
    C.report(work, 'documents', [], ['en'], units, passages)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    a = ap.parse_args()
    only = set(a.only.split(',')) if a.only else None
    jobs = {'book-of-mormon': convert_bofm, 'doctrine-and-covenants': convert_dc, 'pearl-of-great-price': convert_pgp,
            'articles-of-faith': convert_aof, 'jst-appendix': convert_jst}
    for k, fn in jobs.items():
        if not only or k in only:
            fn()


if __name__ == '__main__':
    main()
