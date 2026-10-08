"""Patanjali's Yoga Sutras (GRETIL e-text via OliverHellwig/sanskrit) → works/yoga-sutras.

The source file carries Bhoja's Rājamārtaṇḍa commentary; the sutras are the `||mula:` lines (or, where the
commentary splits a sutra, the text after `---` on the line that carries the `// 1.19 //` marker).
Levels pada(unit)/sutra; ref `1:2`; 4 units, 195 sutras. Edition sa-iast.
"""
import os
import re
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (IAST_EDITION, YOGASUTRA, edition, level, manifest, norm, passage, read_text, report, reset_work,
                    write_manifest, write_unit)

WORK = 'yoga-sutras'
REPO = 'https://github.com/OliverHellwig/sanskrit'
PADAS = {1: ('Samadhi Pada', 'समाधिपादः'), 2: ('Sadhana Pada', 'साधनपादः'), 3: ('Vibhuti Pada', 'विभूतिपादः'),
         4: ('Kaivalya Pada', 'कैवल्यपादः')}
MARK = re.compile(r'//\s*([1-4])\.(\d+)\s*//')

EDITIONS = [
    edition('sa-iast', 'Sanskrit (IAST)', 'original',
            'CC BY-SA 4.0 — GRETIL e-text (data entry Philipp A. Maas, ed. Āgāśe 1904, Ānandāśrama Sanskrit Series 47) '
            'as reformatted in the OliverHellwig/sanskrit repository (corpus/GRETIL); the repository\'s DCS data '
            'directory is marked CC BY 4.0. The sutra text itself is public domain.',
            f'{REPO} (corpus/GRETIL/sa_pataJjali-yogasUtra-with-bhASya.txt, ||mula: lines)', base=IAST_EDITION,
            notes='Sutra text only (the mula lines of the source); Bhoja\'s Rājamārtaṇḍa commentary is omitted. '
                  'Sandhi and avagraha are as in the GRETIL edition.'),
]


def main():
    reset_work(WORK)
    sutras = OrderedDict()
    for line in read_text(YOGASUTRA).split('\n'):
        m = MARK.search(line)
        if not m:
            continue
        pada, n = int(m.group(1)), int(m.group(2))
        before = line[:m.start()]
        if before.startswith('||mula:'):
            text = before[len('||mula:'):]
        else:
            # commentary line that ends with the second half of a split sutra: take what follows the last ' --- '
            text = before.rsplit('---', 1)[-1]
        text = norm(text).rstrip(' /').strip()
        assert text and (pada, n) not in sutras, (pada, n, line)
        sutras[(pada, n)] = text + ' ॥'
    units = passages = 0
    toc, aliases = [], {}
    for pada in range(1, 5):
        ps = [passage(f'{pada}:{n}', t) for (p, n), t in sutras.items() if p == pada]
        nums = [n for (p, n) in sutras if p == pada]
        assert nums == list(range(1, len(nums) + 1)), (pada, nums)
        write_unit(WORK, 'sa-iast', str(pada), ps)
        units += 1
        passages += len(ps)
        en, sa = PADAS[pada]
        toc.append({'ref': str(pada), 'label': {'en': f'{pada}. {en}', 'sa': sa}, 'count': len(ps)})
        aliases[str(pada)] = [en.lower(), en.lower().replace(' pada', ''), f'pada {pada}', f'ys {pada}', f'book {pada}']

    m = manifest(
        WORK, 'documents', [],
        {'en': 'Yoga Sutras of Patanjali', 'sa': 'पातञ्जलयोगसूत्राणि'},
        [level('pada', 'Pada', True), level('sutra', 'Sutra')],
        {'format': '{work} {pada}.{sutra}', 'rangeFormat': '{work} {pada}.{sutra}–{sutra2}', 'workAbbrev': {'en': 'YS'}},
        toc, EDITIONS, ['sa-iast'],
        subtitle={'en': '195 aphorisms on yoga in four padas'},
        aliases=aliases,
        notes='Sanskrit in Roman transliteration (IAST) only; no English translation is included in this snapshot.')
    write_manifest(WORK, m)
    report(WORK, 'documents', [], [e['id'] for e in EDITIONS], units, passages)


if __name__ == '__main__':
    main()
