"""Dhammapada → works/dhammapada (vagga/verse).

Editions: pli (Mahāsaṅgīti root), en-sujato (bilara, CC0), en-buddharakkhita (sc-data legacy HTML, BPS).
Usage: python3 -I convert/buddhism/convert_dhammapada.py
"""
import html as htmllib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (BILARA, BILARA_URL, EN_EDITION, MS_LICENSE, PLI_EDITION, SC_DATA, SUJATO_LICENSE, edition,
                    load_json, norm, bilara_markup, reset_work, write_manifest, write_unit)

WORK = 'dhammapada'
DHP_ROOT = os.path.join(BILARA, 'root', 'pli', 'ms', 'sutta', 'kn', 'dhp')
DHP_EN = os.path.join(BILARA, 'translation', 'en', 'sujato', 'sutta', 'kn', 'dhp')
DHP_HTML = os.path.join(BILARA, 'html', 'pli', 'ms', 'sutta', 'kn', 'dhp')
DHP_BR = os.path.join(SC_DATA, 'html_text', 'en', 'pli', 'sutta', 'kn', 'dhp', 'buddharakkhita', 'dhp')

# English vagga names for the aliases (Sujato's titles are read from the data; these are common alternatives)
ALIASES = {
    1: ['pairs', 'twin verses', 'yamaka'], 2: ['heedfulness', 'diligence', 'appamada'], 3: ['mind', 'the mind', 'citta'],
    4: ['flowers', 'puppha'], 5: ['fool', 'the fool', 'fools', 'bala'], 6: ['wise', 'the wise', 'the sage', 'pandita'],
    7: ['arahant', 'the arahant', 'perfected', 'the perfected one'], 8: ['thousands', 'the thousands', 'sahassa'],
    9: ['evil', 'papa'], 10: ['violence', 'punishment', 'the rod', 'danda'], 11: ['old age', 'jara'],
    12: ['self', 'the self', 'atta'], 13: ['world', 'the world', 'loka'], 14: ['buddha', 'the buddha', 'the awakened'],
    15: ['happiness', 'sukha'], 16: ['affection', 'the dear', 'piya'], 17: ['anger', 'kodha'],
    18: ['impurity', 'stains', 'mala'], 19: ['just', 'the just', 'the righteous', 'dhammattha'],
    20: ['path', 'the path', 'magga'], 21: ['miscellaneous', 'pakinnaka'], 22: ['hell', 'niraya'],
    23: ['elephant', 'the elephant', 'naga'], 24: ['craving', 'tanha'], 25: ['monk', 'the monk', 'mendicant', 'bhikkhu'],
    26: ['holy man', 'the holy man', 'brahmin', 'the brahmin', 'brahmana'],
}


def file_range(fn):
    m = re.match(r'dhp(\d+)-(\d+)', fn)
    return int(m.group(1)), int(m.group(2))


def verses_from_bilara(data, tmpl):
    """Group bilara segments by verse uid number. Returns ordered list of (verse_no, heading, lines).
    Only segments the html template marks as verse lines are kept: end-of-chapter lines ("Yamakavaggo
    paṭhamo."), the closing uddāna of chapter names and the end-of-book line are dropped."""
    order, verses, headings = [], {}, {}
    for key, val in data.items():
        uid, rest = key.split(':', 1)
        vno = int(uid[3:])
        parts = rest.split('.')
        if vno not in verses:
            verses[vno] = []
            order.append(vno)
        if parts[0] == '0':
            # dhp1:0.1 division, 0.2 subdivision, 0.3 vagga title, 0.4 verse story title; dhpN:0 story title
            if rest in ('0', '0.4') and val.strip():
                headings[vno] = norm(bilara_markup(val))
            continue
        if 'verse-line' not in tmpl.get(key, ''):
            continue
        line = norm(bilara_markup(val, verse=True))
        if line:
            verses[vno].append(line)
    return [(v, headings.get(v), verses[v]) for v in order]


def vagga_title(data, key_suffix='0.3'):
    for k, v in data.items():
        if k.endswith(':' + key_suffix):
            return norm(re.sub(r'^\d+\.\s*', '', v))
    return ''


def parse_buddharakkhita(path):
    """sc-data legacy HTML: <p><a data-uid='dhpN'>SC N</a>text</p>; continuation <p> without anchor."""
    raw = open(path, encoding='utf-8').read()
    body = raw.split('<footer>')[0]
    title = re.search(r'<h1>(.*?)</h1>', body)
    title = norm(htmllib.unescape(re.sub(r'<[^>]+>', '', title.group(1)))) if title else ''
    verses, order = {}, []
    cur = None
    for m in re.finditer(r'<p>(.*?)</p>', body, re.S):
        p = m.group(1)
        anchors = re.findall(r"<a class='ref sc'[^>]*data-uid='dhp(\d+)'[^>]*>.*?</a>", p)
        if anchors:
            # a paragraph carrying several anchors renders two verses as one; keep it under the first number
            cur = int(anchors[0])
            p = re.sub(r"<a class='ref sc'[^>]*>.*?</a>", '', p)
            if cur not in verses:
                verses[cur] = []
                order.append(cur)
            if len(anchors) > 1:
                verses[cur].append('*(verses %s–%s)*' % (anchors[0], anchors[-1]))
        if cur is None:
            continue
        t = re.sub(r'<i>(.*?)</i>', r'*\1*', p)
        t = re.sub(r'<[^>]+>', '', t)
        t = norm(htmllib.unescape(t))
        if t:
            verses[cur].append(t)
    return title, [(v, verses[v]) for v in order]


def main():
    reset_work(WORK)
    files = sorted(os.listdir(DHP_EN), key=lambda f: file_range(f)[0])
    assert len(files) == 26, len(files)
    toc, aliases = [], {}
    counts = {'pli': 0, 'en-sujato': 0, 'en-buddharakkhita': 0}
    for i, fn in enumerate(files, 1):
        unit = str(i)
        base = fn.replace('_translation-en-sujato.json', '')
        en = load_json(os.path.join(DHP_EN, fn))
        pli = load_json(os.path.join(DHP_ROOT, base + '_root-pli-ms.json'))
        tmpl = load_json(os.path.join(DHP_HTML, base + '_html.json'))
        title_en, title_pli = vagga_title(en), vagga_title(pli)
        # Pali root
        passages = []
        for n, (vno, heading, lines) in enumerate(verses_from_bilara(pli, tmpl)):
            passages.append({'ref': f'{unit}:{vno}', 'text': '\n'.join(lines), 'heading': heading})
        counts['pli'] += write_unit(WORK, 'pli', unit, passages)
        # Sujato
        passages = []
        for n, (vno, heading, lines) in enumerate(verses_from_bilara(en, tmpl)):
            h = heading or (title_en if n == 0 else None)
            passages.append({'ref': f'{unit}:{vno}', 'text': '\n'.join(lines), 'heading': h})
        counts['en-sujato'] += write_unit(WORK, 'en-sujato', unit, passages)
        nverses = len(passages)
        # Buddharakkhita
        br_path = os.path.join(DHP_BR, base + '.html')
        br_title, br_verses = parse_buddharakkhita(br_path)
        passages = []
        for n, (vno, paras) in enumerate(br_verses):
            passages.append({'ref': f'{unit}:{vno}', 'text': '\n'.join(paras), 'heading': br_title if n == 0 else None})
        counts['en-buddharakkhita'] += write_unit(WORK, 'en-buddharakkhita', unit, passages)
        lo, hi = file_range(fn)
        toc.append({'ref': unit, 'label': {'en': f'{title_en} ({lo}–{hi})', 'pi': title_pli}, 'count': nverses})
        al = set(ALIASES.get(i, []))
        al.add(title_en.lower())
        al.add(title_pli.lower())
        al.add(title_pli.lower().replace('vagga', '').strip())
        aliases[unit] = sorted(a for a in al if a)
    manifest = {
        'workId': WORK, 'shelf': 'scripture', 'families': ['theravada'],
        'title': {'en': 'The Dhammapada', 'pi': 'Dhammapada'},
        'subtitle': {'en': 'Sayings of the Dhamma — Khuddaka Nikāya (423 verses in 26 chapters)'},
        'levels': [{'id': 'vagga', 'label': {'en': 'Chapter (vagga)'}, 'isUnit': True},
                   {'id': 'verse', 'label': {'en': 'Verse'}}],
        'citation': {'format': '{work} {verse}', 'rangeFormat': '{work} {verse}–{verse2}',
                     'workAbbrev': {'en': 'Dhp'}},
        'toc': toc,
        'editions': [
            edition('pli', PLI_EDITION, 'Pali (Mahāsaṅgīti)', 'original', MS_LICENSE,
                    BILARA_URL + 'root/pli/ms/sutta/kn/dhp',
                    notes={'en': 'Verse headings are the names of the background stories (vatthu) carried in the Mahāsaṅgīti edition.'}),
            edition('en-sujato', EN_EDITION, 'English — Bhikkhu Sujato (2021)', 'translation', SUJATO_LICENSE,
                    BILARA_URL + 'translation/en/sujato/sutta/kn/dhp',
                    notes={'en': 'Sayings of the Dhamma: a meaningful translation of the Dhammapada, SuttaCentral 2021.'}),
            edition('en-buddharakkhita', EN_EDITION, 'English — Ācāriya Buddharakkhita (BPS 1985)', 'translation',
                    'Buddhist Publication Society, free distribution. Terms of use as carried in the source file: '
                    '"You may copy, reformat, reprint, republish, and redistribute this work in any medium whatsoever, '
                    'provided that: (1) you only make such copies, etc. available free of charge and, in the case of '
                    'reprinting, only in quantities of no more than 50 copies; (2) you clearly indicate that any '
                    'derivatives of this work (including translations) are derived from this source document; and (3) '
                    'you include the full text of this license in any copies or derivatives of this work. Otherwise, '
                    'all rights reserved." Sourced via Access to Insight / SuttaCentral.',
                    'https://github.com/suttacentral/sc-data/tree/master/html_text/en/pli/sutta/kn/dhp/buddharakkhita',
                    notes={'en': 'The Dhammapada: The Buddha\'s Path of Wisdom, translated by Ācāriya Buddharakkhita, Buddhist Publication Society, Kandy, 1985 (revised 1996). Prose rendering, one paragraph per verse; where the translator renders two verses as one paragraph it is placed under the first verse number and marked.'}),
        ],
        'defaultEditions': ['pli', 'en-sujato'],
        'aliases': aliases,
        'notes': {'en': 'Verses are numbered continuously 1–423 across the 26 chapters, as in all editions.'},
    }
    write_manifest(WORK, manifest)
    print(WORK, counts)


if __name__ == '__main__':
    main()
