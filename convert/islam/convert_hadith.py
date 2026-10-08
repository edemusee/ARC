#!/usr/bin/env python3
"""Convert the Sunni hadith collections from fawazahmed0/hadith-api into works/<collection>/.

  bukhari muslim abudawud tirmidhi nasai ibnmajah malik nawawi40
  source files: hadith-api editions/ara-<coll>.json and eng-<coll>.json (curl'd copies under HADITH_API)

Levels: book (the collection's section/"book" number, isUnit) / hadith (sunnah.com hadith number).
Section assignment walks the hadiths in order and advances to section k+1 when a hadith's
`reference.book` says k+1; the `section_details` ranges in the metadata overlap in Muslim/Tirmidhi/Ibn
Majah and are only used as a cross-check. Arabic section names come from AhmedBaset/hadith-json when its
chapter list has the same length.

Usage: python3 -I convert_hadith.py [workId ...]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (AR_EDITION, HADITH_API, HADITH_JSON, HTML_TAG, edition, load_json, manifest, norm, report,
                    reset_work, write_manifest, write_unit)

HADITH_API_REPO = 'https://github.com/fawazahmed0/hadith-api'
HADITH_JSON_REPO = 'https://github.com/AhmedBaset/hadith-json'
LICENSE = ('Repository released under the Unlicense (public domain dedication by fawazahmed0/hadith-api); '
           'the copyright status of the English translation is not stated by the source')

# workId: (api name, hadith-json file, title en, title ar, abbrev, english translator (as stated by the source),
#          notes)
COLLECTIONS = {
    'bukhari': ('bukhari', 'the_9_books/bukhari.json', 'Sahih al-Bukhari', 'صحيح البخاري', 'Bukhari',
                'Muhsin Khan', 'Imam Muhammad ibn Ismail al-Bukhari (d. 256 AH).'),
    'muslim': ('muslim', 'the_9_books/muslim.json', 'Sahih Muslim', 'صحيح مسلم', 'Muslim',
               'Abdul Hamid Siddiqui', 'Imam Muslim ibn al-Hajjaj (d. 261 AH).'),
    'abudawud': ('abudawud', 'the_9_books/abudawud.json', 'Sunan Abi Dawud', 'سنن أبي داود', 'Abu Dawud',
                 None, 'Imam Abu Dawud as-Sijistani (d. 275 AH).'),
    'tirmidhi': ('tirmidhi', 'the_9_books/tirmidhi.json', 'Jami` at-Tirmidhi', 'جامع الترمذي', 'Tirmidhi',
                 None, 'Imam Abu Isa at-Tirmidhi (d. 279 AH).'),
    'nasai': ('nasai', 'the_9_books/nasai.json', "Sunan an-Nasa'i", 'سنن النسائي', "Nasa'i",
              None, "Imam Ahmad an-Nasa'i (d. 303 AH)."),
    'ibnmajah': ('ibnmajah', 'the_9_books/ibnmajah.json', 'Sunan Ibn Majah', 'سنن ابن ماجه', 'Ibn Majah',
                 None, 'Imam Ibn Majah al-Qazwini (d. 273 AH).'),
    'malik': ('malik', 'the_9_books/malik.json', 'Muwatta Malik', 'موطأ مالك', 'Muwatta',
              None, 'Imam Malik ibn Anas (d. 179 AH).'),
    'nawawi40': ('nawawi', 'forties/nawawi40.json', "An-Nawawi's Forty Hadith", 'الأربعون النووية', 'Nawawi',
                 None, "Imam Yahya ibn Sharaf an-Nawawi (d. 676 AH); forty-two hadith."),
}


def clean(text):
    t = re.sub(r'<br\s*/?>', '\n', text, flags=re.I)
    if HTML_TAG.search(t):
        # stray angle brackets used as quotation marks (Nasa'i 4513), not markup
        t = t.replace('<', '').replace('>', '')
    return norm(t)


def hadith_ref(n):
    """402 → '402'; 402.2 → '402-2'."""
    if isinstance(n, float) and n.is_integer():
        n = int(n)
    return str(n).replace('.', '-')


def assign_sections(eng):
    """hadithnumber → section number, by walking in order (see module docstring)."""
    secs = eng['metadata']['sections']
    nsec = max(int(k) for k in secs)
    cur = 0 if secs.get('0') else 1
    out = {}
    for h in eng['hadiths']:
        rb = (h.get('reference') or {}).get('book') or 0
        if rb == cur + 1 and rb <= nsec:
            cur = rb
        out[h['hadithnumber']] = cur
    return out


def arabic_section_names(hj_file, secs):
    """Arabic chapter titles from hadith-json when its chapter list lines up with hadith-api's sections."""
    p = os.path.join(HADITH_JSON, hj_file)
    if not os.path.exists(p):
        return {}
    d = load_json(p)
    by_id = {int(c['id']): c for c in (d.get('chapters') or [])}
    named = [k for k in secs if secs[k]]
    if len(by_id) == 1 and len(named) == 1:
        by_id = {int(named[0]): next(iter(by_id.values()))}
    if len(by_id) != len(named) or any(int(k) not in by_id for k in named):
        return {}
    out = {}
    for k in named:
        ch = by_id[int(k)]
        ar = norm(ch.get('arabic') or '')
        # only trust the pairing when the English titles agree (loosely)
        en_a, en_b = norm(ch.get('english') or '').lower(), norm(secs[k]).lower()
        if ar and (en_a == en_b or en_a in en_b or en_b in en_a or k == '0' or len(named) == 1):
            out[k] = ar
    return out


def convert(work_id):
    api, hj_file, title_en, title_ar, abbrev, translator, note = COLLECTIONS[work_id]
    ara = load_json(os.path.join(HADITH_API, f'ara-{api}.json'))
    eng = load_json(os.path.join(HADITH_API, f'eng-{api}.json'))
    secs = eng['metadata']['sections']
    section_of = assign_sections(eng)
    ar_names = arabic_section_names(hj_file, secs)

    reset_work(work_id)
    units = passages = 0
    counts = {}
    for ed_id, src in (('ar', ara), ('en', eng)):
        by_sec = {}
        for h in src['hadiths']:
            text = clean(h.get('text') or '')
            if not text:
                continue
            n = h['hadithnumber']
            sec = section_of.get(n)
            if sec is None:
                continue
            by_sec.setdefault(sec, []).append({'ref': f'{sec}:{hadith_ref(n)}', 'text': text})
        for sec in sorted(by_sec):
            write_unit(work_id, ed_id, str(sec), by_sec[sec])
            units += 1
            passages += len(by_sec[sec])
            counts.setdefault(str(sec), 0)
            counts[str(sec)] = max(counts[str(sec)], len(by_sec[sec]))

    toc = []
    for k in sorted(secs, key=int):
        if k not in counts:
            continue
        label = {'en': norm(secs[k]) or f'Book {k}'}
        if k in ar_names:
            label['ar'] = ar_names[k]
        toc.append({'ref': k, 'label': label, 'count': counts[k]})

    en_label = f'English — {translator}' if translator else 'English (sunnah.com translation; translator not named by the source)'
    editions = [
        edition('ar', 'Arabic', 'original', LICENSE, f'{HADITH_API_REPO} (editions/ara-{api}.json)', base=AR_EDITION),
        edition('en', en_label, 'translation', LICENSE, f'{HADITH_API_REPO} (editions/eng-{api}.json)'),
    ]
    m = manifest(
        work_id, 'documents', ['sunni'], {'en': title_en, 'ar': title_ar},
        [{'id': 'book', 'label': {'en': 'Book'}, 'isUnit': True}, {'id': 'hadith', 'label': {'en': 'Hadith'}}],
        {'format': '{work} {hadith}', 'rangeFormat': '{work} {hadith}–{hadith2}', 'workAbbrev': {'en': abbrev}},
        toc, editions, ['ar', 'en'],
        subtitle={'en': note},
        notes='Hadith numbers follow sunnah.com; books are the collection\'s own sections.' +
              (' Arabic section titles from AhmedBaset/hadith-json.' if ar_names else ''))
    write_manifest(work_id, m)
    report(work_id, 'documents', ['sunni'], ['ar', 'en'], units, passages)


if __name__ == '__main__':
    for w in (sys.argv[1:] or list(COLLECTIONS)):
        convert(w)
