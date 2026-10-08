"""Mahāyāna sūtras → works/heart-sutra, works/diamond-sutra, works/lotus-sutra, works/sukhavativyuha.

Sources:
  84000 TEI (data-tei/keep): English translations, CC BY-NC-ND 3.0. Only the <div type="translation"> body is
    used (front matter, introduction, end notes, bibliography and glossary are dropped); end notes attached
    inline in the body are kept as passage `notes`.
  CBETA xml-p5 (Taishō): Chinese text of T 251 (Heart, Xuanzang), T 235 (Diamond, Kumārajīva) and T 366
    (Amitābha / shorter Sukhāvatīvyūha, Kumārajīva), CC BY-NC-SA. Because the Chinese and the Tibetan-based
    English are different recensions with different paragraphing, each Chinese text is its own unit
    (declared through the edition's `available` list) rather than being lined up passage by passage.
  Rushi (CC0 markdown): Goddard 1932 English Diamond Sutra (public domain).
Usage: python3 -I convert/buddhism/convert_mahayana.py
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (CBETA, EN_EDITION, LICENSE_84000, LICENSE_CBETA, RUSHI, TEI_84000, ZH_EDITION, edition, norm,
                    reset_work, write_manifest, write_unit)

TEI = '{http://www.tei-c.org/ns/1.0}'
XMLNS = '{http://www.w3.org/XML/1998/namespace}'
CB = '{http://www.cbeta.org/ns/1.0}'


# ---------------------------------------------------------------- 84000 TEI
class TextBuilder:
    """Accumulates whitespace-collapsed text and end notes anchored at character offsets."""

    def __init__(self):
        self.out = ''
        self.notes = []

    def add(self, s):
        if not s:
            return
        s = re.sub(r'\s+', ' ', s)
        if s == ' ' and (not self.out or self.out.endswith((' ', '\n'))):
            return
        if s.startswith(' ') and (not self.out or self.out.endswith((' ', '\n'))):
            s = s[1:]
        self.out += s

    def newline(self):
        self.out = self.out.rstrip(' ')
        if self.out and not self.out.endswith('\n'):
            self.out += '\n'

    def note(self, text):
        text = norm(text)
        if text:
            self.notes.append({'at': len(self.out.rstrip()), 'text': text})

    def result(self):
        return self.out.strip(), self.notes


EMPH = {'title', 'foreign', 'distinct', 'emph'}


def walk(el, tb, in_note=False):
    """Render an element's content into tb (TEI 84000 body markup)."""
    tag = el.tag.replace(TEI, '')
    if tag == 'note':
        if not in_note:
            nb = TextBuilder()
            nb.add(el.text)
            walk_children(el, nb, True)
            tb.note(nb.result()[0])
        return
    if tag in ('ref', 'ptr', 'milestone'):
        # folio/bampo refs carry no text; hyperlinks inside notes keep their text
        if in_note and el.text:
            tb.add(el.text)
            walk_children(el, tb, in_note)
        return
    if tag == 'lb':
        tb.add(' ')
        return
    if tag == 'l':
        tb.add(el.text)
        walk_children(el, tb, in_note)
        tb.newline()
        return
    wrap = tag in EMPH and not in_note and el.get('type') != 'ignore'
    if wrap:
        inner = TextBuilder()
        inner.add(el.text)
        walk_children(el, inner, in_note)
        txt, nts = inner.result()
        if txt:
            if tb.out and not tb.out.endswith((' ', '\n', '“', '‘', '"', '(', '[', '-', '‑')):
                tb.out += ' '
            base = len(tb.out) + 1
            tb.out += '*' + txt + '*'
            for n in nts:
                tb.notes.append({'at': base + n['at'], 'text': n['text']})
        return
    tb.add(el.text)
    walk_children(el, tb, in_note)


def walk_children(el, tb, in_note):
    for ch in el:
        walk(ch, tb, in_note)
        if ch.tail:
            tb.add(ch.tail)


def render(el):
    tb = TextBuilder()
    tb.add(el.text)
    walk_children(el, tb, False)
    text, notes = tb.result()
    text = re.sub(r'\s*\{\d+\}', '', text)          # verse numbers {1} at line ends
    text = re.sub(r' +\n', '\n', text)
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r'(?<=\S) +([,.;:!?)’”])', r'\1', text)
    return text.strip(), notes


def body_blocks(el):
    """Yield p / lg / trailer elements in document order, without descending into notes or into a block."""
    for ch in el:
        tag = ch.tag.replace(TEI, '')
        if tag == 'note':
            continue
        if tag in ('p', 'lg', 'trailer'):
            yield ch
            continue
        yield from body_blocks(ch)


def tei_units(path, chapter_mode):
    """Yield (unit_ref, label, passages) from an 84000 TEI file's translation body."""
    root = ET.parse(path).getroot()
    body = root.find(TEI + 'text').find(TEI + 'body')
    tr = body.find(TEI + 'div[@type="translation"]')
    title = next((t for t in root.iter(TEI + 'title')
                  if t.get('type') == 'mainTitle' and t.get(XMLNS + 'lang') == 'en'), None)
    title = norm(title.text) if title is not None else ''
    units = []
    if chapter_mode:
        containers = [d for d in tr if d.tag == TEI + 'div' and d.get('type') in ('chapter', 'section')]
    else:
        containers = [d for d in tr if d.tag == TEI + 'div' and d.get('type') in ('section',)]
    colophon = tr.find(TEI + 'div[@type="colophon"]')
    for i, div in enumerate(containers, 1):
        heads = [h for h in div.findall(TEI + 'head')]
        chap = next((norm(h.text or '') for h in heads if h.get('type') == 'chapter'), '')
        ctitle = next((render(h)[0] for h in heads if h.get('type') == 'chapterTitle'), '')
        label = (chap + ': ' if chap else '') + ctitle if (chap or ctitle) else title
        passages = []
        pending_heading = ctitle if chapter_mode else title
        n = 0
        for el in body_blocks(div):
            text, notes = render(el)
            if not text:
                continue
            n += 1
            p = {'ref': f'{i}:{n}', 'text': text, 'notes': notes}
            if pending_heading:
                p['heading'] = pending_heading
                pending_heading = None
            passages.append(p)
        if colophon is not None and i == len(containers):
            first = True
            for el in body_blocks(colophon):
                text, notes = render(el)
                if not text:
                    continue
                n += 1
                p = {'ref': f'{i}:{n}', 'text': text, 'notes': notes}
                if first:
                    p['heading'] = 'Colophon'
                    first = False
                passages.append(p)
        units.append((str(i), label, passages))
    return title, units


# ---------------------------------------------------------------- CBETA
def cbeta_gaiji(root):
    m = {}
    for ch in root.iter(TEI + 'char'):
        cid = ch.get(XMLNS + 'id')
        uni = None
        norm_form = None
        for mp in ch.findall(TEI + 'mapping'):
            if mp.get('type') == 'unicode' and mp.text:
                uni = mp.text.strip()
        for cp in ch.findall(TEI + 'charProp'):
            ln = cp.find(TEI + 'localName')
            v = cp.find(TEI + 'value')
            if ln is not None and v is not None and ln.text and 'normal' in ln.text:
                norm_form = (v.text or '').strip()
        if uni and uni.startswith('U+'):
            m[cid] = chr(int(uni[2:], 16))
        elif norm_form:
            m[cid] = norm_form
        else:
            m[cid] = '〇'
    return m


def cbeta_text(el, gaiji, tb, notes):
    """Flatten a CBETA element: drop lb/pb/anchor, map <g>, inline <note> → notes, <caesura> → space,
    <l> lines → newline."""
    tag = el.tag.replace(TEI, '').replace(CB, 'cb:')
    if tag in ('note',):
        nb = []
        cbeta_text_children(el, gaiji, nb, [], True)
        t = norm(''.join(nb))
        if t:
            notes.append({'at': len(''.join(tb)), 'text': t})
        return
    if tag in ('lb', 'pb', 'anchor', 'cb:mulu', 'cb:docNumber', 'cb:jhead'):
        return
    if tag == 'g':
        tb.append(gaiji.get(el.get('ref', '').lstrip('#'), '〇'))
        return
    if tag == 'caesura':
        tb.append('　')
        return
    if tag == 'space':
        tb.append('　')
        return
    if tag == 'app':
        lem = el.find(TEI + 'lem')
        if lem is not None:
            cbeta_text(lem, gaiji, tb, notes)
        return
    if el.text:
        tb.append(el.text.replace('\n', ''))
    cbeta_text_children(el, gaiji, tb, notes, False)
    if tag == 'l':
        tb.append('\n')


def cbeta_text_children(el, gaiji, tb, notes, in_note):
    for ch in el:
        cbeta_text(ch, gaiji, tb, notes)
        if ch.tail:
            tb.append(ch.tail.replace('\n', ''))


def cbeta_passages(path, unit):
    """Passages from the <cb:div type="jing"> (and following mantra divs) of a CBETA file, one per <p>/<lg>."""
    root = ET.parse(path).getroot()
    gaiji = cbeta_gaiji(root)
    body = root.find(TEI + 'text').find(TEI + 'body')
    title = root.find('.//' + TEI + 'titleStmt/' + TEI + 'title')
    title = norm(title.text or '') if title is not None else ''
    passages = []
    n = 0
    pending = None
    for div in body.iter(CB + 'div'):
        if div.get('type') not in ('jing', 'w'):
            continue
        if div.get('type') == 'w':
            pending = pending or '附錄 (appendix carried in the Taishō text)'
        for el in div.iter():
            tag = el.tag.replace(TEI, '').replace(CB, 'cb:')
            if tag == 'head':
                tb, nts = [], []
                cbeta_text(el, gaiji, tb, nts)
                pending = norm(''.join(tb)) or pending
                continue
            if tag not in ('p', 'lg'):
                continue
            if tag == 'p' and el.find('.//' + TEI + 'lg') is not None:
                continue
            tb, nts = [], []
            cbeta_text(el, gaiji, tb, nts)
            text = ''.join(tb)
            text = re.sub(r'[ \t]+', '', text) if tag == 'p' else text   # CJK: line breaks carry no space
            text = norm(text)
            if not text or re.fullmatch(r'[^，。]{0,12}卷第[一二三四五六七八九十]+', text):
                continue   # end-of-fascicle marker
            n += 1
            p = {'ref': f'{unit}:{n}', 'text': text, 'notes': nts}
            if pending:
                p['heading'] = pending
                pending = None
            passages.append(p)
    return title, passages


# ---------------------------------------------------------------- Goddard markdown
def goddard_units(path):
    """Split the Rushi markdown into (ref, label, paragraphs). PDF-wrapped lines are re-flowed: lines ≥ 73
    characters are wrapped mid-paragraph, shorter lines ending in sentence punctuation end a paragraph,
    shorter lines without it are verse lines; blank lines are page breaks and ignored."""
    raw = open(path, encoding='utf-8').read()
    body = raw.split('\n---\n', 1)[1] if raw.startswith('---') else raw   # drop the YAML front matter
    lines = body.split('\n')
    sections = []
    cur = None
    for ln in lines:
        s = ln.rstrip()
        if re.match(r'^-{10,}$', s):
            break
        if s.startswith('## ') or s.startswith('### '):
            cur = {'label': s.lstrip('# ').strip(), 'lines': []}
            sections.append(cur)
            continue
        if cur is None:
            continue
        cur['lines'].append(s)
    units = []
    for sec in sections:
        if sec['label'].startswith('The Diamond Sutra ('):
            continue   # work title + byline
        paras, buf = [], []
        prev_short_noend = False

        def flush():
            if buf:
                paras.append(norm('\n'.join(buf)))
                buf.clear()

        for s in sec['lines']:
            if not s.strip():
                continue   # page break
            if s.startswith('*') and s.endswith('*') and 'End of' in s:
                continue
            starts_new = bool(re.match(r'^(“|"|\(|Subhuti|The Lord Buddha|Then |At that time|Thereupon|Upon )', s))
            if buf and starts_new and re.search(r'[.?!”"\')]$', buf[-1]) and not prev_short_noend:
                flush()
            if buf and (prev_short_noend or len(buf[-1]) < 73 and not re.search(r'[.?!”"\')]$', buf[-1])):
                buf.append(s)           # verse line continues
            elif buf:
                buf[-1] = buf[-1] + ' ' + s   # wrapped line
            else:
                buf.append(s)
            short = len(s) < 73
            ends = bool(re.search(r'[.?!”"\')]$', s))
            if short and ends:
                flush()
                prev_short_noend = False
            else:
                prev_short_noend = short and not ends
        flush()
        units.append((sec['label'], paras))
    return units


# ---------------------------------------------------------------- works
def convert_heart():
    work = 'heart-sutra'
    reset_work(work)
    title, units = tei_units(os.path.join(TEI_84000, '034-009_toh21,531-the_heart_of_the_perfection_of_wisdom_the_blessed_mother.xml'), False)
    counts = {}
    toc = []
    for ref, label, passages in units:
        counts['en-84000'] = counts.get('en-84000', 0) + write_unit(work, 'en-84000', ref, passages)
        toc.append({'ref': ref, 'label': {'en': label}, 'count': len(passages)})
    zt, zp = cbeta_passages(os.path.join(CBETA, 'T08n0251.xml'), 'zh')
    counts['zh-xuanzang'] = write_unit(work, 'zh-xuanzang', 'zh', zp)
    toc.append({'ref': 'zh', 'label': {'en': 'Chinese text — Xuanzang (T 251)', 'zh': '般若波羅蜜多心經'}, 'count': len(zp)})
    write_manifest(work, {
        'workId': work, 'shelf': 'scripture', 'families': ['mahayana'],
        'title': {'en': 'The Heart Sūtra', 'sa': 'Prajñāpāramitāhṛdaya', 'zh': '般若波羅蜜多心經'},
        'subtitle': {'en': 'The Heart of the Perfection of Wisdom, the Blessed Mother (Toh 21 / Taishō 251)'},
        'levels': [{'id': 'section', 'label': {'en': 'Text'}, 'isUnit': True},
                   {'id': 'paragraph', 'label': {'en': 'Paragraph'}}],
        'citation': {'format': '{work} {section}:{paragraph}', 'rangeFormat': '{work} {section}:{paragraph}–{paragraph2}',
                     'workAbbrev': {'en': 'Heart Sūtra'}},
        'toc': toc,
        'editions': [
            edition('en-84000', EN_EDITION, 'English — 84000 (Dharmachakra Translation Committee)', 'translation',
                    LICENSE_84000, 'https://github.com/84000/data-tei (034-009, Toh 21 / Toh 531), https://read.84000.co/translation/toh21.html',
                    available=['1'], notes={'en': 'The long recension translated from the Tibetan Kangyur (Toh 21, Toh 531). 84000: Translating the Words of the Buddha, v 1.0.14 (2024). Translators\' end notes are kept as passage notes.'}),
            edition('zh-xuanzang', ZH_EDITION, 'Chinese — Xuanzang, 649 CE (Taishō 251)', 'translation', LICENSE_CBETA,
                    'https://github.com/cbeta-org/xml-p5/blob/master/T/T08/T08n0251.xml',
                    available=['zh'], notes={'en': 'The short recension in Xuanzang\'s translation, the text recited throughout East Asia. It is a different recension from the Tibetan long version, so it is given as its own section rather than lined up with the English.'}),
        ],
        'defaultEditions': ['en-84000'],
        'aliases': {'1': ['heart sutra', 'heart', 'prajnaparamita hrdaya', 'hridaya', 'english', '84000'],
                    'zh': ['chinese', 'xinjing', 'xin jing', 'xuanzang', 'taisho 251', 't251']},
        'notes': {'en': 'Two recensions: the Tibetan long version in English (84000) and the Chinese short version (Xuanzang) as a separate section.'},
    })
    print(work, counts)


def convert_diamond():
    work = 'diamond-sutra'
    reset_work(work)
    units = goddard_units(os.path.join(RUSHI, 'scriptures', 'jingang-jing', 'en.md'))
    counts = {'en-goddard': 0}
    toc, avail = [], []
    labels = {'Preface': 'Preface (Goddard, 1932)', 'The Diamond Scripture': 'The Diamond Scripture — opening'}
    for i, (label, paras) in enumerate(units, 1):
        ref = str(i)
        lab = labels.get(label, label.title().replace('Paramita', 'Pāramitā') if label.isupper() or '—' in label else label)
        passages = [{'ref': f'{ref}:{n}', 'text': t, 'heading': lab if n == 1 else None} for n, t in enumerate(paras, 1)]
        counts['en-goddard'] += write_unit(work, 'en-goddard', ref, passages)
        toc.append({'ref': ref, 'label': {'en': lab}, 'count': len(passages)})
        avail.append(ref)
    zt, zp = cbeta_passages(os.path.join(CBETA, 'T08n0235.xml'), 'zh')
    counts['zh-kumarajiva'] = write_unit(work, 'zh-kumarajiva', 'zh', zp)
    toc.append({'ref': 'zh', 'label': {'en': 'Chinese text — Kumārajīva (T 235)', 'zh': '金剛般若波羅蜜經'}, 'count': len(zp)})
    aliases = {'1': ['preface'], '2': ['opening', 'diamond scripture', 'thus have i heard'],
               '3': ['dana', 'charity', 'dana paramita'], '4': ['sila', 'behavior', 'sila paramita'],
               '5': ['kshanti', 'patience', 'kshanti paramita'], '6': ['virya', 'zeal', 'virya paramita'],
               '7': ['dhyana', 'tranquillity', 'dhyana paramita'], '8': ['prajna', 'wisdom', 'prajna paramita'],
               'zh': ['chinese', 'kumarajiva', 'jingang jing', 'jingangjing', 'taisho 235', 't235']}
    write_manifest(work, {
        'workId': work, 'shelf': 'scripture', 'families': ['mahayana'],
        'title': {'en': 'The Diamond Sūtra', 'sa': 'Vajracchedikā Prajñāpāramitā', 'zh': '金剛般若波羅蜜經'},
        'subtitle': {'en': 'Based on William Gemmell\'s translation, edited, rearranged and interpreted by Dwight Goddard, A Buddhist Bible (1932); Chinese text of Kumārajīva (Taishō 235)'},
        'levels': [{'id': 'section', 'label': {'en': 'Section'}, 'isUnit': True},
                   {'id': 'paragraph', 'label': {'en': 'Paragraph'}}],
        'citation': {'format': '{work} {section}:{paragraph}', 'rangeFormat': '{work} {section}:{paragraph}–{paragraph2}',
                     'workAbbrev': {'en': 'Diamond Sūtra'}},
        'toc': toc,
        'editions': [
            edition('en-goddard', EN_EDITION, 'English — Goddard after Gemmell (A Buddhist Bible, 1932)', 'translation',
                    'Public domain / CC0. Goddard 1932 was not renewed at the US Copyright Office (Stanford Copyright '
                    'Renewal Database; sacred-texts.com attribution); the underlying Gemmell 1912 translation is '
                    'pre-1928. The Rushi corpus releases its markdown files under CC0 1.0.',
                    'https://github.com/hooosberg/Rushi/blob/main/scriptures/jingang-jing/en.md',
                    available=avail, notes={'en': 'Goddard rearranged Gemmell\'s 1912 translation of Kumārajīva\'s Chinese into sections on the six pāramitās, with passages from the Awakening of Faith inserted in parentheses at the head of each section. Paragraphing was recovered from a PDF transcription and may differ slightly from the printed book.'}),
            edition('zh-kumarajiva', ZH_EDITION, 'Chinese — Kumārajīva, 401 CE (Taishō 235)', 'original', LICENSE_CBETA,
                    'https://github.com/cbeta-org/xml-p5/blob/master/T/T08/T08n0235.xml',
                    available=['zh'], notes={'en': 'Kumārajīva\'s translation, the text used in East Asian recitation, given as its own section because Goddard\'s English does not follow its order.'}),
        ],
        'defaultEditions': ['en-goddard'],
        'aliases': aliases,
    })
    print(work, counts)


def convert_lotus():
    work = 'lotus-sutra'
    reset_work(work)
    title, units = tei_units(os.path.join(TEI_84000, '051-001_toh113-sutra_of_the_white_lotus_of_true_dharma.xml'), True)
    counts = {'en-84000': 0}
    toc, aliases = [], {}
    for ref, label, passages in units:
        counts['en-84000'] += write_unit(work, 'en-84000', ref, passages)
        toc.append({'ref': ref, 'label': {'en': label}, 'count': len(passages)})
        t = label.split(': ', 1)[-1].lower()
        aliases[ref] = sorted({t, t.replace('the ', ''), f'chapter {ref}', f'ch {ref}'})
    write_manifest(work, {
        'workId': work, 'shelf': 'scripture', 'families': ['mahayana'],
        'title': {'en': 'The Lotus Sūtra', 'sa': 'Saddharmapuṇḍarīka'},
        'subtitle': {'en': 'The White Lotus of the Good Dharma (Toh 113), in 27 chapters'},
        'levels': [{'id': 'chapter', 'label': {'en': 'Chapter'}, 'isUnit': True},
                   {'id': 'paragraph', 'label': {'en': 'Paragraph'}}],
        'citation': {'format': '{work} {chapter}:{paragraph}', 'rangeFormat': '{work} {chapter}:{paragraph}–{paragraph2}',
                     'workAbbrev': {'en': 'Lotus'}},
        'toc': toc,
        'editions': [
            edition('en-84000', EN_EDITION, 'English — 84000 (Peter Alan Roberts)', 'translation', LICENSE_84000,
                    'https://github.com/84000/data-tei (051-001, Toh 113), https://read.84000.co/translation/toh113.html',
                    notes={'en': 'Translated from the Tibetan Kangyur by Peter Alan Roberts for 84000: Translating the Words of the Buddha. The Tibetan has 27 chapters (the Devadatta chapter of Kumārajīva\'s Chinese is part of chapter 11). Verses are one passage per stanza; translators\' end notes are kept as passage notes.'}),
        ],
        'defaultEditions': ['en-84000'],
        'aliases': aliases,
    })
    print(work, counts)


def convert_sukhavati():
    work = 'sukhavativyuha'
    reset_work(work)
    title, units = tei_units(os.path.join(TEI_84000, '051-003_toh115_display_of_pure_land_of_sukhavati.xml'), False)
    counts = {}
    toc = []
    for ref, label, passages in units:
        counts['en-84000'] = counts.get('en-84000', 0) + write_unit(work, 'en-84000', ref, passages)
        toc.append({'ref': ref, 'label': {'en': label}, 'count': len(passages)})
    zt, zp = cbeta_passages(os.path.join(CBETA, 'T12n0366.xml'), 'zh')
    counts['zh-kumarajiva'] = write_unit(work, 'zh-kumarajiva', 'zh', zp)
    toc.append({'ref': 'zh', 'label': {'en': 'Chinese text — Kumārajīva, Amitābha Sūtra (T 366)', 'zh': '佛說阿彌陀經'}, 'count': len(zp)})
    write_manifest(work, {
        'workId': work, 'shelf': 'scripture', 'families': ['mahayana'],
        'title': {'en': 'The Display of the Pure Land of Sukhāvatī', 'sa': 'Sukhāvatīvyūha', 'zh': '佛說阿彌陀經'},
        'subtitle': {'en': 'The shorter Sukhāvatīvyūha / Amitābha Sūtra (Toh 115 / Taishō 366)'},
        'levels': [{'id': 'section', 'label': {'en': 'Text'}, 'isUnit': True},
                   {'id': 'paragraph', 'label': {'en': 'Paragraph'}}],
        'citation': {'format': '{work} {section}:{paragraph}', 'rangeFormat': '{work} {section}:{paragraph}–{paragraph2}',
                     'workAbbrev': {'en': 'Sukhāvatīvyūha'}},
        'toc': toc,
        'editions': [
            edition('en-84000', EN_EDITION, 'English — 84000 (Sakya Pandita Translation Group)', 'translation', LICENSE_84000,
                    'https://github.com/84000/data-tei (051-003, Toh 115), https://read.84000.co/translation/toh115.html',
                    available=['1'], notes={'en': 'Translated from the Tibetan Kangyur for 84000: Translating the Words of the Buddha. Toh 115 is the shorter Sukhāvatīvyūha (the Amitābha Sūtra); the longer Sukhāvatīvyūha is Toh 49 and is not included.'}),
            edition('zh-kumarajiva', ZH_EDITION, 'Chinese — Kumārajīva, 402 CE (Taishō 366)', 'translation', LICENSE_CBETA,
                    'https://github.com/cbeta-org/xml-p5/blob/master/T/T12/T12n0366.xml',
                    available=['zh'], notes={'en': 'Kumārajīva\'s Amitābha Sūtra, the text recited in Pure Land practice, given as its own section.'}),
        ],
        'defaultEditions': ['en-84000'],
        'aliases': {'1': ['sukhavati', 'amitabha sutra', 'shorter sukhavativyuha', 'pure land', 'english'],
                    'zh': ['chinese', 'amituo jing', 'amituojing', 'kumarajiva', 'taisho 366', 't366']},
    })
    print(work, counts)


def main():
    convert_heart()
    convert_diamond()
    convert_lotus()
    convert_sukhavati()


if __name__ == '__main__':
    main()
