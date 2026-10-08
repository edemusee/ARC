"""Individual Pali suttas from bilara-data → one work each (section/paragraph).

Editions: pli (Mahāsaṅgīti root), en-sujato (CC0). Paragraph = the first number of the bilara segment id
(mn10:4.2 → paragraph 4); sentences of a paragraph are joined with spaces, verse lines (html template
class 'verse-line') and successive <p> blocks with newlines. Section headings (segment ids ending in .0 or
.0.n) become the `heading` of the paragraph they introduce. DN 16 is split into its six recitation sections
(dn16:3.12.4 → unit 3, paragraph 12); every other sutta is one unit "1".
Usage: python3 -I convert/buddhism/convert_suttas.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (BILARA, BILARA_URL, EN_EDITION, MS_LICENSE, PLI_EDITION, SUJATO_LICENSE, edition, load_json,
                    norm, bilara_markup, reset_work, write_manifest, write_unit)

# workId, bilara uid, relative path, English title, Pali title, canonical reference, aliases, notes
SUTTAS = [
    ('dhammacakkappavattana', 'sn56.11', 'sn/sn56/sn56.11', 'Setting the Wheel of Dhamma in Motion',
     'Dhammacakkappavattanasutta', 'SN 56.11',
     ['dhammacakkappavattana sutta', 'dhammacakka', 'first sermon', 'turning of the wheel', 'sn 56.11'],
     'The Buddha\'s first discourse at Isipatana: the middle way, the four noble truths and the eightfold path.'),
    ('satipatthana', 'mn10', 'mn/mn10', 'Mindfulness Meditation', 'Satipaṭṭhānasutta', 'MN 10',
     ['satipatthana sutta', 'foundations of mindfulness', 'establishments of mindfulness', 'mn 10'],
     'The four establishments of mindfulness: body, feelings, mind and principles.'),
    ('anapanasati', 'mn118', 'mn/mn118', 'Mindfulness of Breathing', 'Ānāpānassatisutta', 'MN 118',
     ['anapanasati sutta', 'anapanassati', 'mindfulness of breathing', 'mn 118'],
     'Sixteen steps of mindfulness of breathing and how they fulfil the four establishments of mindfulness and the awakening factors.'),
    ('metta-sutta', 'snp1.8', 'kn/snp/vagga1/snp1.8', 'The Discourse on Love', 'Mettasutta', 'Snp 1.8',
     ['metta sutta', 'karaniya metta sutta', 'karaniyametta', 'loving-kindness', 'snp 1.8', 'kp 9'],
     'Sutta Nipāta 1.8. The same text is recited as Khuddakapāṭha 9 (Kp 9).'),
    ('mangala-sutta', 'snp2.4', 'kn/snp/vagga2/snp2.4', 'Blessings', 'Maṅgalasutta', 'Snp 2.4',
     ['mangala sutta', 'maha mangala sutta', 'mahamangala', 'blessings', 'snp 2.4', 'kp 5'],
     'Sutta Nipāta 2.4. The same text is recited as Khuddakapāṭha 5 (Kp 5).'),
    ('kalama-sutta', 'an3.65', 'an/an3/an3.65', 'With the Kālāmas of Kesamutta', 'Kesamuttisutta', 'AN 3.65',
     ['kalama sutta', 'kesamutti sutta', 'kesaputta', 'an 3.65'],
     'The discourse to the Kālāmas on not relying on tradition or logic alone but on what one knows for oneself to be wholesome.'),
    ('sigalovada', 'dn31', 'dn/dn31', 'Advice to Sigālaka', 'Siṅgālasutta', 'DN 31',
     ['sigalovada sutta', 'singalovada', 'singala sutta', 'sigala', 'advice to sigala', 'dn 31'],
     'The layperson\'s code of discipline: the six directions and the duties of family and social life.'),
    ('mahaparinibbana', 'dn16', 'dn/dn16', 'The Great Discourse on the Buddha\'s Extinguishment',
     'Mahāparinibbānasutta', 'DN 16',
     ['mahaparinibbana sutta', 'maha parinibbana', 'parinibbana', 'great passing', 'dn 16'],
     'The Buddha\'s last journey, final teachings and passing away, in six recitation sections (bhāṇavāra).'),
]

DN16_SECTIONS = ['Paṭhamabhāṇavāra', 'Dutiyabhāṇavāra', 'Tatiyabhāṇavāra', 'Catutthabhāṇavāra',
                 'Pañcamabhāṇavāra', 'Chaṭṭhabhāṇavāra']


def paths(rel, uid):
    return (os.path.join(BILARA, 'root', 'pli', 'ms', 'sutta', rel + '_root-pli-ms.json'),
            os.path.join(BILARA, 'translation', 'en', 'sujato', 'sutta', rel + '_translation-en-sujato.json'),
            os.path.join(BILARA, 'html', 'pli', 'ms', 'sutta', rel + '_html.json'))


def build_passages(data, tmpl, multi_unit, title):
    """Return {unit: [passages]} from a bilara segment dict + html template."""
    units = {}
    order = []
    paras = {}          # (unit, para) -> {'chunks': [(joiner, text)], 'heading': [..]}
    prev_tmpl_end_p = False
    first_key = None
    for key, val in data.items():
        parts = key.split(':', 1)[1].split('.')
        html = tmpl.get(key, '')
        if parts[0] == '0':
            continue
        if multi_unit:
            unit, para, rest = parts[0], parts[1], parts[2:]
        else:
            unit, para, rest = '1', parts[0], parts[1:]
        pk = (unit, para)
        if pk not in paras:
            paras[pk] = {'chunks': [], 'heading': []}
            order.append(pk)
            if unit not in units:
                units[unit] = []
        if rest and rest[0] == '0':
            h = norm(bilara_markup(val))
            if h:
                paras[pk]['heading'].append(h)
            prev_tmpl_end_p = False
            continue
        is_verse = 'verse-line' in html
        # closing/end-of-section markers that carry no text in translation are simply empty strings
        text = norm(bilara_markup(val, verse=is_verse))
        if text:
            joiner = '\n' if (is_verse or prev_tmpl_end_p) else ' '
            paras[pk]['chunks'].append((joiner, text))
        prev_tmpl_end_p = html.rstrip().endswith('</p>') or '</blockquote>' in html or 'endsection' in html
    first = True
    for pk in order:
        unit, para = pk
        p = paras[pk]
        text = ''
        for joiner, chunk in p['chunks']:
            text = chunk if not text else text + joiner + chunk
        text = norm(text)
        if not text:
            continue
        heading = ' — '.join(p['heading'])
        if first:
            heading = title + (' — ' + heading if heading else '')
            first = False
        units[unit].append({'ref': f'{unit}:{para}', 'text': text, 'heading': heading or None})
    return units


def convert(work, uid, rel, title_en, title_pli, canon, aliases, note):
    reset_work(work)
    root_p, en_p, html_p = paths(rel, uid)
    root, en, tmpl = load_json(root_p), load_json(en_p), load_json(html_p)
    multi = uid == 'dn16'
    counts = {}
    toc = []
    units_pli = build_passages(root, tmpl, multi, title_pli)
    units_en = build_passages(en, tmpl, multi, title_en)
    for unit in units_en:
        counts.setdefault('pli', 0)
        counts['pli'] += write_unit(work, 'pli', unit, units_pli.get(unit, []))
        counts.setdefault('en-sujato', 0)
        counts['en-sujato'] += write_unit(work, 'en-sujato', unit, units_en[unit])
        if multi:
            i = int(unit)
            label = {'en': f'Recitation section {i}', 'pi': DN16_SECTIONS[i - 1]}
        else:
            label = {'en': title_en, 'pi': title_pli}
        toc.append({'ref': unit, 'label': label, 'count': len(units_en[unit])})
    collection = {'sn': 'Saṁyutta Nikāya', 'mn': 'Majjhima Nikāya', 'an': 'Aṅguttara Nikāya', 'dn': 'Dīgha Nikāya',
                  'snp': 'Sutta Nipāta (Khuddaka Nikāya)', 'kp': 'Khuddakapāṭha'}[re.match(r'[a-z]+', uid).group(0)]
    manifest = {
        'workId': work, 'shelf': 'scripture', 'families': ['theravada'],
        'title': {'en': title_en, 'pi': title_pli},
        'subtitle': {'en': f'{canon} — {collection}'},
        'levels': [{'id': 'section', 'label': {'en': 'Recitation section' if multi else 'Sutta'}, 'isUnit': True},
                   {'id': 'paragraph', 'label': {'en': 'Paragraph'}}],
        'citation': {'format': '{work} {section}:{paragraph}' if multi else '{work} {paragraph}',
                     'rangeFormat': '{work} {section}:{paragraph}–{paragraph2}' if multi else '{work} {paragraph}–{paragraph2}',
                     'workAbbrev': {'en': canon}},
        'toc': toc,
        'editions': [
            edition('pli', PLI_EDITION, 'Pali (Mahāsaṅgīti)', 'original', MS_LICENSE,
                    BILARA_URL + 'root/pli/ms/sutta/' + os.path.dirname(rel)),
            edition('en-sujato', EN_EDITION, 'English — Bhikkhu Sujato', 'translation', SUJATO_LICENSE,
                    BILARA_URL + 'translation/en/sujato/sutta/' + os.path.dirname(rel)),
        ],
        'defaultEditions': ['pli', 'en-sujato'],
        'aliases': {toc[0]['ref']: sorted(set(a.lower() for a in aliases))} if not multi else
                   {str(i + 1): [f'section {i + 1}', f'bhanavara {i + 1}', DN16_SECTIONS[i].lower()] for i in range(6)},
        'notes': {'en': note + ' Paragraph numbers follow the SuttaCentral segment numbering.'},
    }
    write_manifest(work, manifest)
    print(work, counts)


def main():
    for row in SUTTAS:
        convert(*row)


if __name__ == '__main__':
    main()
