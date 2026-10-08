"""Visuddhimagga (Pali, VRI Chaṭṭha Saṅgāyana CD) → works/visuddhimagga (chapter/paragraph).

Source: tipitaka-xml/cscd/e0101n.mul*.xml and e0102n.mul*.xml (UTF-16 TEI.2). One file per chapter
(mul0 of the first part is the Nidānādikathā, unit "0"); CSCD paragraph numbers (<p n="N">, continuous
through the whole book) are the passage refs. Verse lines (rend gatha1/2/3/gathalast) are joined with
newlines; sub-headings (rend subhead/subsubhead) become the heading of the paragraph they introduce;
<hi rend="bold"> → **bold**; page breaks (<pb>) are dropped.
Usage: python3 -I convert/buddhism/convert_visuddhimagga.py
"""
import html as htmllib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CSCD, PLI_EDITION, edition, norm, reset_work, write_manifest, write_unit

WORK = 'visuddhimagga'

CHAPTERS_EN = {
    0: 'Introduction', 1: 'Virtue', 2: 'The Ascetic Practices', 3: 'Taking a Meditation Subject',
    4: 'The Earth Kasiṇa', 5: 'The Remaining Kasiṇas', 6: 'Foulness as a Meditation Subject',
    7: 'Six Recollections', 8: 'Other Recollections as Meditation Subjects', 9: 'The Divine Abidings',
    10: 'The Immaterial States', 11: 'Concentration', 12: 'The Supernormal Powers', 13: 'Other Direct-Knowledges',
    14: 'The Aggregates', 15: 'The Bases and Elements', 16: 'The Faculties and Truths',
    17: 'The Soil in Which Understanding Grows', 18: 'Purification of View',
    19: 'Purification by Overcoming Doubt',
    20: 'Purification by Knowledge and Vision of What Is and What Is Not the Path',
    21: 'Purification by Knowledge and Vision of the Way', 22: 'Purification by Knowledge and Vision',
    23: 'The Benefits in Developing Understanding',
}

VERSE = {'gatha1', 'gatha2', 'gatha3', 'gathalast'}
HEADINGS = {'subhead', 'subsubhead', 'title', 'chapter'}


def inline(s):
    s = re.sub(r'<pb [^>]*/>', ' ', s)
    s = re.sub(r'<hi rend="paranum">\d+</hi><hi rend="dot">\.</hi>\s*', '', s)
    s = re.sub(r'<hi rend="bold">(.*?)</hi>',
               lambda m: ('**' + m.group(1).strip() + '**') if m.group(1).strip() else ' ', s, flags=re.S)
    s = re.sub(r'<hi rend="[^"]*">(.*?)</hi>', r'\1', s, flags=re.S)
    s = re.sub(r'<[^>]+>', '', s)
    s = htmllib.unescape(s)
    s = re.sub(r'\*\*\s*\*\*', ' ', s)      # adjacent bold runs split by a page break
    return norm(s)


def chapter_passages(path, unit):
    f = open(path, encoding='utf-16').read()
    body = f[f.index('<body>') + 6:f.index('</body>')]
    paras = re.findall(r'<p rend="([^"]+)"(?: n="(\d+)")?>(.*?)</p>', body, re.S)
    passages = []
    cur = None          # current passage dict
    cur_lines = []      # chunks: (is_verse, text)
    heading = []
    chapter_title = ''

    def flush():
        nonlocal cur, cur_lines
        if cur is None:
            return
        out, prev_verse = '', False
        for is_verse, t in cur_lines:
            if not out:
                out = t
            else:
                out += '\n' + t
        cur['text'] = out
        passages.append(cur)
        cur, cur_lines = None, []

    for rend, n, raw in paras:
        text = inline(raw)
        if rend == 'chapter':
            chapter_title = text
            continue
        if rend == 'book':
            continue
        if n:
            flush()
            cur = {'ref': f'{unit}:{n}'}
            if heading:
                cur['heading'] = ' — '.join(heading)
                heading = []
            if text:
                cur_lines.append((False, text))
            continue
        if rend in HEADINGS or (rend == 'centre' and cur is None):
            if text:
                heading.append(text)
            continue
        if not text:
            continue
        if cur is None:
            # text before the first numbered paragraph (e.g. the opening homage): attach as heading
            heading.append(text)
            continue
        cur_lines.append((rend in VERSE, text))
    flush()
    return chapter_title, passages


def main():
    reset_work(WORK)
    files = [(0, os.path.join(CSCD, 'e0101n.mul0.xml'))]
    files += [(i, os.path.join(CSCD, f'e0101n.mul{i}.xml')) for i in range(1, 12)]
    files += [(i + 12, os.path.join(CSCD, f'e0102n.mul{i}.xml')) for i in range(0, 12)]
    toc, aliases = [], {}
    total = 0
    for ch, path in files:
        unit = str(ch)
        title, passages = chapter_passages(path, unit)
        if ch == 0:
            title = title or 'Nidānādikathā'
        n = write_unit(WORK, 'pli', unit, passages)
        total += n
        pli_title = re.sub(r'^\d+\.\s*', '', title)
        toc.append({'ref': unit, 'label': {'en': f'{ch}. {CHAPTERS_EN[ch]} ({pli_title})' if ch else f'{CHAPTERS_EN[ch]} ({pli_title})',
                                           'pi': title}, 'count': n})
        aliases[unit] = sorted({pli_title.lower(), pli_title.lower().replace('niddeso', '').strip(),
                                CHAPTERS_EN[ch].lower(), CHAPTERS_EN[ch].lower().replace('the ', ''),
                                f'chapter {ch}', f'ch {ch}'})
    write_manifest(WORK, {
        'workId': WORK, 'shelf': 'documents', 'families': ['theravada'],
        'title': {'en': 'Visuddhimagga — The Path of Purification', 'pi': 'Visuddhimagga'},
        'subtitle': {'en': 'Buddhaghosa (5th century), the classic Theravāda manual of meditation and doctrine — Pali text only'},
        'levels': [{'id': 'chapter', 'label': {'en': 'Chapter (pariccheda)'}, 'isUnit': True},
                   {'id': 'paragraph', 'label': {'en': 'Paragraph'}}],
        'citation': {'format': '{work} {chapter}.{paragraph}', 'rangeFormat': '{work} {chapter}.{paragraph}–{paragraph2}',
                     'workAbbrev': {'en': 'Vism'}},
        'toc': toc,
        'editions': [
            edition('pli', PLI_EDITION, 'Pali (VRI CSCD)', 'original',
                    'VRI tipitaka.org, free for non-commercial use (Vipassana Research Institute, Chaṭṭha Saṅgāyana CD '
                    'Roman-script edition; the tipitaka-xml repository packaging is MIT-licensed).',
                    'https://github.com/sarbanandabhikkhu/tipitaka-xml (cscd/e0101n.mul*.xml, e0102n.mul*.xml), from https://www.tipitaka.org/romn/',
                    notes={'en': 'Paragraph numbers are the VRI edition\'s continuous paragraph numbers (1–896), which Ñāṇamoli\'s English translation also prints in its margins.'}),
        ],
        'defaultEditions': ['pli'],
        'aliases': aliases,
        'notes': {'en': 'No English translation is included; Ñāṇamoli\'s Path of Purification (BPS) is not free for redistribution. English chapter names follow it.'},
    })
    print(WORK, {'pli': total})


if __name__ == '__main__':
    main()
