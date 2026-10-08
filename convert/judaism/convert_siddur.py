"""Siddurim → works/siddur-edot-hamizrach and works/siddur-ashkenaz.

Sefaria stores a siddur as a schema tree (nodes with enTitle/heTitle); `text` is a dict mirroring it, each
leaf holding a list of paragraphs. Each leaf becomes a unit whose ref is the slugified node path
(`weekday-shacharit-amidah-patriarchs`); toc entries are the leaf's parent path (joined with " · ") with the
leaves as children, so the reader's two-level navigation shows service → prayer.

Paragraph markup: <b>/<strong> → **bold** (opening words), <small> (rubrics/instructions) → *emphasis*,
<big> is dropped. A paragraph that is only a <big><b>title</b></big> becomes the heading of the next one.
Only named versions are read (never merged.json).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (EN_EDITION, HE_EDITION, clean, edition, license_text, passage, report, reset_work,
                    sefaria_path, slugify, source_url, write_manifest, write_unit)

TITLE_ONLY = re.compile(r'^\s*<big>\s*<b>(.*?)</b>\s*</big>\s*$', re.S | re.I)


def leaves(schema):
    """Yield (path list of enTitles, path list of heTitles) for every leaf node in schema order."""
    def walk(node, en, he):
        if 'nodes' in node:
            for n in node['nodes']:
                k = n.get('enTitle') or n.get('key') or n.get('sharedTitle') or ''
                yield from walk(n, en + [k], he + [n.get('heTitle') or k])
        else:
            yield en, he
    yield from walk(schema, [], [])


def leaf_text(text, path):
    t = text
    for k in path:
        if not isinstance(t, dict):
            return None
        t = t.get(k)
    return t


def flatten(t):
    out = []
    def rec(x):
        if isinstance(x, list):
            for y in x:
                rec(y)
        elif isinstance(x, str):
            out.append(x)
    rec(t)
    return out


def paragraphs(unit, raw_list):
    """Turn the leaf's paragraphs into passages, folding title-only paragraphs into headings."""
    ps, pending = [], None
    for i, raw in enumerate(raw_list, 1):
        m = TITLE_ONLY.match(raw or '')
        if m:
            h = clean(m.group(1), bold=False)
            if h:
                pending = (pending + ' — ' + h) if pending else h
            continue
        t = re.sub(r'<small(?:\s[^>]*)?>(.*?)</small>', r'<i>\1</i>', raw or '', flags=re.S | re.I)
        t = clean(t)
        if not t:
            continue
        ps.append(passage(f'{unit}:{i}', t, pending))
        pending = None
    return ps


def convert(work, title, subtitle, cat, versions, notes_work, aliases_extra=None):
    """versions: list of (editionId, langDir, versionTitle, base, label, role, notes)."""
    reset_work(work)
    counts, toc_entries, toc_index, units, seen_slugs = {'units': 0, 'passages': 0}, [], {}, [], set()
    available, licenses = {v[0]: [] for v in versions}, {}
    datasets = []
    for eid, lang_dir, vt, base, label, role, notes in versions:
        d = sefaria_path(f'json/{cat}/{lang_dir}/{vt}.json')
        licenses[eid] = license_text(d)
        datasets.append((eid, d))
    schema = datasets[0][1]['schema']
    for en_path, he_path in leaves(schema):
        slug = slugify('-'.join(en_path))
        if slug in seen_slugs:
            n = 2
            while f'{slug}-{n}' in seen_slugs:
                n += 1
            slug = f'{slug}-{n}'
        seen_slugs.add(slug)
        wrote_any = False
        for eid, d in datasets:
            raw = flatten(leaf_text(d['text'], en_path))
            ps = paragraphs(slug, raw)
            k = write_unit(work, eid, slug, ps)
            if k:
                counts['units'] += 1
                counts['passages'] += k
                available[eid].append(slug)
                wrote_any = True
        if not wrote_any:
            continue
        leaf = {'ref': slug, 'label': {'en': en_path[-1], 'he': he_path[-1]}}
        parent = tuple(en_path[:-1])
        if not parent:
            toc_entries.append(leaf)
            continue
        if parent not in toc_index:
            entry = {'ref': slugify('-'.join(parent)) + '-group', 'label': {'en': ' · '.join(parent), 'he': ' · '.join(he_path[:-1])}, 'children': []}
            toc_index[parent] = entry
            toc_entries.append(entry)
        toc_index[parent]['children'].append(leaf)
    editions = []
    for eid, lang_dir, vt, base, label, role, notes in versions:
        e = edition(eid, base, label, role, licenses[eid], source_url(cat, lang_dir, vt), notes=notes)
        e['available'] = available[eid]
        editions.append(e)
    aliases = {}
    for t in toc_entries:
        for c in t.get('children', [t]):
            al = {c['label']['en'].lower()}
            aliases.setdefault(c['ref'], sorted(al))
    if aliases_extra:
        for k, v in aliases_extra.items():
            if k in aliases:
                aliases[k] = sorted(set(aliases[k]) | set(v))
    manifest = {
        'schemaVersion': 1, 'workId': work, 'tradition': 'judaism', 'shelf': 'devotional', 'families': [],
        'title': title, 'subtitle': {'en': subtitle},
        'levels': [
            {'id': 'prayer', 'label': {'en': 'Prayer'}, 'isUnit': True},
            {'id': 'paragraph', 'label': {'en': 'Paragraph'}},
        ],
        'citation': {'format': '{work} {prayer} ¶{paragraph}', 'rangeFormat': '{work} {prayer} ¶{paragraph}–{paragraph2}',
                     'workAbbrev': {'en': 'Siddur'}},
        'toc': toc_entries,
        'editions': editions,
        'defaultEditions': [versions[0][0], next((v[0] for v in versions if v[3] is EN_EDITION), versions[0][0])],
        'aliases': aliases,
        'notes': {'en': notes_work},
    }
    write_manifest(work, manifest)
    report(work, {**counts, **{f'available[{k}]': len(v) for k, v in available.items()}, 'toc': len(toc_entries)})


def main():
    convert(
        'siddur-edot-hamizrach',
        {'en': 'Siddur Edot HaMizrach', 'he': 'סידור נוסח עדות המזרח'},
        'The daily, Shabbat and festival prayer book in the Sephardic / Mizrahi rite',
        'Liturgy/Siddur/Siddur Edot HaMizrach',
        [
            ('he', 'Hebrew', 'Torat Emet 357', HE_EDITION, 'Hebrew — Torat Emet (vocalized)', 'original',
             'Complete vocalized text of the Edot HaMizrach rite from the Torat Emet freeware edition (version 357), via Sefaria. Rubrics (instructions) are shown in emphasis; section titles become headings.'),
            ('en', 'English', 'Sefaria Community Translation', EN_EDITION, 'English — Sefaria Community Translation (partial)', 'translation',
             'Sefaria Community Translation, CC0. Partial: only the prayers listed in this edition have an English text; the others are shown in Hebrew only.'),
        ],
        'Follows the Sefaria arrangement of the Edot HaMizrach siddur: weekday services first, then Shabbat, Rosh Chodesh, festivals and occasional blessings.',
    )
    convert(
        'siddur-ashkenaz',
        {'en': 'Siddur Ashkenaz', 'he': 'סידור אשכנז'},
        'The daily, Shabbat and festival prayer book in the Ashkenazi rite',
        'Liturgy/Siddur/Siddur Ashkenaz',
        [
            ('he', 'Hebrew', 'Daat Siddur Ashkenaz', HE_EDITION, 'Hebrew — Daat (vocalized)', 'original',
             'Public-domain vocalized text from the Daat (Bar-Ilan) siddur, via Sefaria. Covers the weekday services and part of Shabbat; prayers without a Daat text are shown from the Metsudah edition if that is selected.'),
            ('he-metsudah', 'Hebrew', 'The Metsudah siddur, 1981', HE_EDITION, 'Hebrew — Metsudah Siddur (1981, vocalized)', 'original',
             'Hebrew text of the Metsudah linear siddur (Avrohom Davis, 1981), released by Sefaria under CC-BY. Covers weekday and Shabbat prayers; complements the Daat edition.'),
            ('en', 'English', 'Sefaria Community Translation', EN_EDITION, 'English — Sefaria Community Translation (partial)', 'translation',
             'Sefaria Community Translation, CC0. Partial: only the prayers listed in this edition have an English text; the others are shown in Hebrew only.'),
        ],
        'Follows the Sefaria arrangement of the Ashkenaz siddur (Weekday, Shabbat, Festivals, Berachot, Kaddish). No single public-domain Hebrew version covers every prayer, so two Hebrew editions are offered; prayers with no text in any edition are omitted from the contents.',
    )


if __name__ == '__main__':
    main()
