#!/usr/bin/env python3
"""Convert the Shia collections from narmafraz/ThaqalaynData (CC0) into works/.

  al-kafi          books/al-kafi/<vol>/<book>/<chapter>/<n>.json (+ <n>.en.json for the translations)
                   levels volume / book / chapter (isUnit) / hadith; ref <vol>:<book>:<chapter>:<n>
                   editions ar, en-hubeali (HTML stripped), en-sarwar. The `ai` fields are ignored.
  nahj-al-balagha  books/nahj-al-balagha/<part>/<number>/<n>.json
                   levels part / number (isUnit) / paragraph; units sermons:1 …, letters:1 …, sayings:1 …
                   editions ar, en-reza (Sayed Ali Reza)

Usage: python3 -I convert_shia.py [al-kafi] [nahj-al-balagha]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (AR_EDITION, THAQALAYN, edition, load_json, manifest, norm, report, reset_work, strip_html,
                    write_manifest, write_unit)

REPO = 'https://github.com/narmafraz/ThaqalaynData'
LICENSE = 'CC0 1.0 (ThaqalaynData repository); texts as published on thaqalayn.net'
HONORIFIC = re.compile(r'(?<=[A-Za-z])(azwj|asws|saww|ajfj)\b')


def ar_text(verse):
    parts = []
    chain = (verse.get('narrator_chain') or {}).get('parts') or []
    if chain:
        parts.append(''.join(p.get('text', '') for p in chain))
    body = [strip_html(s) for s in (verse.get('text') or [])]
    body = [s for s in (norm(s) for s in body) if s and not re.fullmatch(r'[–—\-_.]+', s)]
    t = norm(' '.join(parts)) + ('\n' if parts and body else '') + '\n'.join(body)
    return norm(t)


def en_text(chunks):
    # tags can be split across chunks, so join first and strip afterwards
    t = norm(strip_html('\n'.join(str(c) for c in (chunks or []))))
    t = re.sub(r'\s?\[\d+\]', '', t)          # footnote markers whose text is not in the data
    t = HONORIFIC.sub('', t)                   # HubeAli honorifics typed as plain text ('Allahazwj')
    t = re.sub(r'[‘’]{2,}', '’', t)
    return norm(t)


def translations_for(base_verse, en_file):
    """{translation key: text} merging the base file's `translations` and <n>.en.json chunk_translations."""
    out = {}
    for k, chunks in (base_verse.get('translations') or {}).items():
        if k.endswith('.ai'):
            continue
        out[k] = chunks
    if os.path.exists(en_file):
        e = load_json(en_file)
        for k, chunks in (e.get('chunk_translations') or {}).items():
            if k.endswith('.ai'):
                continue
            out[k] = chunks
    return out


def chapter_label(titles, fallback):
    en = norm(HONORIFIC.sub('', strip_html(titles.get('en') or ''))) or fallback
    lab = {'en': en}
    ar = norm(titles.get('ar') or '')
    if ar:
        lab['ar'] = ar
    return lab


# ---------------------------------------------------------------- al-Kafi
def convert_kafi(volumes=range(1, 9)):
    work_id = 'al-kafi'
    root = os.path.join(THAQALAYN, 'al-kafi')
    reset_work(work_id)
    vols = {c['local_index']: c for c in load_json(os.path.join(root + '.json'))['data']['chapters']}
    toc = []
    units = passages = 0
    editions_seen = set()
    for vol in volumes:
        vinfo = vols[vol]
        vdata = load_json(os.path.join(root, f'{vol}.json'))['data']
        for book in vdata['chapters']:
            bi = book['local_index']
            bdata = load_json(os.path.join(root, str(vol), f'{bi}.json'))['data']
            children = []
            for ch in bdata['chapters']:
                ci = ch['local_index']
                unit = f'{vol}:{bi}:{ci}'
                cdata = load_json(os.path.join(root, str(vol), str(bi), f'{ci}.json'))['data']
                per_ed = {'ar': [], 'en-hubeali': [], 'en-sarwar': []}
                pending = {}   # inline headings waiting for the next hadith, per edition
                for ref in cdata.get('verse_refs', []):
                    if 'inline' in ref:
                        inl = ref['inline']
                        h_ar = norm(strip_html(' '.join(inl.get('text') or [])))
                        if h_ar:
                            pending['ar'] = (pending.get('ar', '') + '\n' + h_ar).strip()
                        for k, chunks in (inl.get('translations') or {}).items():
                            ed = {'en.hubeali': 'en-hubeali', 'en.sarwar': 'en-sarwar'}.get(k)
                            if ed:
                                h = en_text(chunks)
                                if h:
                                    pending[ed] = (pending.get(ed, '') + '\n' + h).strip()
                        continue
                    n = ref['local_index']
                    vfile = os.path.join(root, str(vol), str(bi), str(ci), f'{n}.json')
                    if not os.path.exists(vfile):
                        continue
                    verse = load_json(vfile)['data']['verse']
                    pref = f'{unit}:{n}'
                    t = ar_text(verse)
                    if t:
                        p = {'ref': pref, 'text': t}
                        if pending.get('ar'):
                            p['heading'] = pending.pop('ar')
                        per_ed['ar'].append(p)
                    trs = translations_for(verse, vfile[:-5] + '.en.json')
                    for k, ed in (('en.hubeali', 'en-hubeali'), ('en.sarwar', 'en-sarwar')):
                        t = en_text(trs.get(k))
                        if t:
                            p = {'ref': pref, 'text': t}
                            if pending.get(ed):
                                p['heading'] = pending.pop(ed)
                            per_ed[ed].append(p)
                count = 0
                for ed, ps in per_ed.items():
                    if ps:
                        write_unit(work_id, ed, unit, ps)
                        editions_seen.add(ed)
                        units += 1
                        passages += len(ps)
                        count = max(count, len(ps))
                if count:
                    children.append({'ref': unit, 'label': chapter_label(ch.get('titles') or {}, f'Chapter {ci}'),
                                     'count': count})
            if children:
                lab = chapter_label(book.get('titles') or {}, f'Book {bi}')
                lab['en'] = f"Vol. {vol} · {lab['en'].title() if lab['en'].isupper() else lab['en']}"
                toc.append({'ref': f'{vol}:{bi}', 'label': lab, 'children': children})

    editions = [
        edition('ar', 'Arabic', 'original', LICENSE, f'{REPO} (books/al-kafi)', base=AR_EDITION),
        edition('en-hubeali', 'English — Hubeali', 'translation', LICENSE, f'{REPO} (books/al-kafi, en.hubeali)',
                notes={'en': 'Hubeali.com translation; superscript honorifics (asws, saww, azwj) and footnote markers of the web edition are omitted.'}),
        edition('en-sarwar', 'English — Muhammad Sarwar', 'translation', LICENSE, f'{REPO} (books/al-kafi, en.sarwar)'),
    ]
    editions = [e for e in editions if e['id'] in editions_seen]
    m = manifest(
        work_id, 'documents', ['shia'], {'en': 'Al-Kafi', 'ar': 'الكافي'},
        [{'id': 'volume', 'label': {'en': 'Volume'}}, {'id': 'book', 'label': {'en': 'Book'}},
         {'id': 'chapter', 'label': {'en': 'Chapter'}, 'isUnit': True}, {'id': 'hadith', 'label': {'en': 'Hadith'}}],
        {'format': '{work} {volume}:{book}:{chapter}:{hadith}', 'rangeFormat': '{work} {volume}:{book}:{chapter}:{hadith}–{hadith2}',
         'workAbbrev': {'en': 'Kafi'}},
        toc, editions, ['ar', 'en-hubeali'],
        subtitle={'en': 'Muhammad ibn Ya\'qub al-Kulayni (d. 329 AH)'},
        notes='Reference: volume:book:chapter:hadith as numbered on thaqalayn.net. Hadith without an English rendering are shown in Arabic only.')
    write_manifest(work_id, m)
    report(work_id, 'documents', ['shia'], [e['id'] for e in editions], units, passages)


# ---------------------------------------------------------------- Nahj al-Balagha
PARTS = [('sermons', 1, 'Sermons', 'الخطب'), ('letters', 2, 'Letters', 'الكتب'), ('sayings', 3, 'Sayings', 'الحكم')]


def convert_nahj():
    work_id = 'nahj-al-balagha'
    root = os.path.join(THAQALAYN, 'nahj-al-balagha')
    reset_work(work_id)
    toc = []
    units = passages = 0
    for part, idx, en_name, ar_name in PARTS:
        pdata = load_json(os.path.join(root, f'{idx}.json'))['data']
        children = []
        for ch in pdata['chapters']:
            ci = ch['local_index']
            unit = f'{part}:{ci}'
            cdata = load_json(os.path.join(root, str(idx), f'{ci}.json'))['data']
            ps_ar, ps_en = [], []
            for ref in cdata.get('verse_refs', []):
                if 'inline' in ref:
                    continue
                n = ref['local_index']
                vfile = os.path.join(root, str(idx), str(ci), f'{n}.json')
                if not os.path.exists(vfile):
                    continue
                verse = load_json(vfile)['data']['verse']
                pref = f'{unit}:{n}'
                t = ar_text(verse)
                if t:
                    ps_ar.append({'ref': pref, 'text': t})
                trs = translations_for(verse, vfile[:-5] + '.en.json')
                t = en_text(trs.get('en.sayed-ali-raza'))
                if t:
                    ps_en.append({'ref': pref, 'text': t})
            count = 0
            if ps_ar:
                write_unit(work_id, 'ar', unit, ps_ar)
                units += 1
                passages += len(ps_ar)
                count = len(ps_ar)
            if ps_en:
                write_unit(work_id, 'en-reza', unit, ps_en)
                units += 1
                passages += len(ps_en)
                count = max(count, len(ps_en))
            if count:
                lab = chapter_label(ch.get('titles') or {}, f'{en_name[:-1]} {ci}')
                lab['en'] = f"{ci}. {lab['en']}"
                children.append({'ref': unit, 'label': lab, 'count': count})
        toc.append({'ref': part, 'label': {'en': en_name, 'ar': ar_name}, 'children': children})

    editions = [
        edition('ar', 'Arabic', 'original', LICENSE, f'{REPO} (books/nahj-al-balagha)', base=AR_EDITION),
        edition('en-reza', 'English — Sayed Ali Reza', 'translation', LICENSE,
                f'{REPO} (books/nahj-al-balagha, en.sayed-ali-raza)',
                notes={'en': 'Footnote markers of the source are omitted (the footnote text is not in the data).'}),
    ]
    aliases = {'sermons': ['sermon', 'khutba', 'khutbah', 'sermons'], 'letters': ['letter', 'kitab', 'letters'],
               'sayings': ['saying', 'hikma', 'hikmah', 'sayings', 'wisdom']}
    m = manifest(
        work_id, 'documents', ['shia'], {'en': 'Nahj al-Balagha', 'ar': 'نهج البلاغة'},
        [{'id': 'part', 'label': {'en': 'Part'}}, {'id': 'number', 'label': {'en': 'Number'}, 'isUnit': True},
         {'id': 'paragraph', 'label': {'en': 'Paragraph'}}],
        {'format': '{work} {part} {number}:{paragraph}', 'rangeFormat': '{work} {part} {number}:{paragraph}–{paragraph2}',
         'workAbbrev': {'en': 'Nahj'}},
        toc, editions, ['ar', 'en-reza'], aliases=aliases,
        subtitle={'en': 'Sermons, letters and sayings of Ali ibn Abi Talib, compiled by al-Sharif al-Radi'},
        notes="Numbering follows thaqalayn.net; for the sayings it differs from the printed editions' numbering, which is kept inside the text.")
    write_manifest(work_id, m)
    report(work_id, 'documents', ['shia'], ['ar', 'en-reza'], units, passages)


if __name__ == '__main__':
    want = sys.argv[1:] or ['al-kafi', 'nahj-al-balagha']
    if 'al-kafi' in want:
        convert_kafi()
    if 'nahj-al-balagha' in want:
        convert_nahj()
