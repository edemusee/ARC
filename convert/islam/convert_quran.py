#!/usr/bin/env python3
"""Convert the Qur'an (and the juz'-of-the-day devotional) into works/quran/ and works/juz-of-the-day/.

Sources (quran-json by risan, data/meta/sources.json holds the per-file licences):
  ar-hafs       data/quranpedia/qpc-hafs.json      KFGQPC Hafs text (Qur'anpedia dump), no basmala prefix
  ar-uthmani    data/tanzil/uthmani.json           Tanzil Uthmani (basmala prefixed to ayah 1 — moved to heading)
  ar-simple     data/tanzil/simple-clean.json      Tanzil simple-clean (no tashkeel)
  translit      quran-api editions/ara-quran-la.json (fawazahmed0/quran-api, fetched via raw.githubusercontent)
  en-saheeh     data/quranenc/english_saheeh.json  (verse-number prefix and [n] footnote markers removed,
                                                    footnotes → notes)
  en-pickthall, en-yusufali, en-rodwell, en-sale   data/extra/
  ur-junagarhi, es-garcia, fr-hameedullah, id-sabiq, tr-rwwad   data/quranenc/
  toc           data/tanzil/chapters.json (names + indexes.juzs)

Usage: python3 -I convert_quran.py [quran] [juz-of-the-day]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (AR_EDITION, EN_EDITION, QURAN_API, QURAN_JSON, WORKS, edition, load_json, manifest, norm,
                    report, reset_work, write_manifest, write_unit)

QURAN_JSON_REPO = 'https://github.com/risan/quran-json'
QURAN_API_REPO = 'https://github.com/fawazahmed0/quran-api'
SAHEEH_BASMALA = 'In the name of Allah, the Entirely Merciful, the Especially Merciful.'

# Arabic combining marks (harakat, Qur'anic annotation signs, U+08D3–U+08FF extended marks)
COMBINING = r'[ً-ٰٟۖ-ۜ۟-۪ۤۧۨ-ۭ࣓-ࣿ]'
SPACE_BEFORE_MARK = re.compile(r' (?=' + COMBINING + ')')


def fix_spacing(text):
    """Remove the known artefact of a space before a combining mark (seen around U+08F0 in some dumps)."""
    return SPACE_BEFORE_MARK.sub('', text)


# ---------------------------------------------------------------- sources
def sources_meta():
    by_path = {}
    for e in load_json(os.path.join(QURAN_JSON, 'meta', 'sources.json')):
        by_path[e['path']] = e
    return by_path


def licence(meta, rel):
    e = meta[rel]
    lic = e['license']
    if e.get('source_metadata', {}).get('version'):
        lic += f" (QuranEnc version {e['source_metadata']['version']})"
    src = f"{e['url']} (via {QURAN_JSON_REPO}, {rel})"
    return lic, src


def load_verses(rel):
    """quran-json verse-by-verse file → {surah: [ {verse, text, footnotes?} ]} with int keys."""
    d = load_json(os.path.join(QURAN_JSON, rel))
    return {int(k): v for k, v in d.items()}


def load_translit():
    p = os.path.join(QURAN_API, 'ara-quran-la.json')
    if not os.path.exists(p):
        return None
    d = load_json(p)
    out = {}
    for x in d['quran']:
        out.setdefault(int(x['chapter']), []).append({'verse': int(x['verse']), 'text': x['text']})
    return out


# ---------------------------------------------------------------- text cleaning
FOOTNOTE_LINE = re.compile(r'^\[(\d+)\]\s*[-.]?\s*(.*)$')


def parse_footnotes(s):
    """QuranEnc footnotes field: '[2]- text\\n[3]- text' → {2: text}."""
    out = {}
    cur = None
    for line in (s or '').split('\n'):
        m = FOOTNOTE_LINE.match(line.strip())
        if m:
            cur = int(m.group(1))
            out[cur] = m.group(2).strip()
        elif cur is not None and line.strip():
            out[cur] += ' ' + line.strip()
    return out


def clean_translation(text, verse, footnotes):
    """Strip a leading verse-number prefix '(n) ' or 'n. ' (only when n == verse), pull [n] markers out into
    notes with character offsets. Returns (text, notes)."""
    t = norm(text)
    m = re.match(r'^\(?(\d+)[\.\)]\s*', t)
    if m and int(m.group(1)) == verse:
        t = t[m.end():]
    fns = parse_footnotes(footnotes)
    notes = []
    clean = ''
    pos = 0
    for mk in re.finditer(r'\s?\[(\d+)\]', t):
        clean += t[pos:mk.start()]
        n = int(mk.group(1))
        if n in fns and fns[n]:
            notes.append({'at': len(clean), 'text': norm(fns[n])})
        pos = mk.end()
        # keep a space that preceded the marker if the next character is a word character
        if mk.group(0).startswith(' ') and pos < len(t) and not re.match(r'[\s,.;:!?)\]]', t[pos]):
            clean += ' '
    clean += t[pos:]
    clean = norm(clean)
    if not fns:
        # a translation with no footnote text: just drop the markers
        clean = norm(re.sub(r'\s?\[\d+\]', '', clean))
    return clean, notes


# ---------------------------------------------------------------- Qur'an
def convert_quran():
    work_id = 'quran'
    meta = sources_meta()
    chapters = load_json(os.path.join(QURAN_JSON, 'tanzil', 'chapters.json'))
    chap = {c['id']: c for c in chapters['chapters']}

    editions = []
    ed_data = {}  # edition id -> {surah: [passages]}

    def add(ed, data):
        editions.append(ed)
        ed_data[ed['id']] = data

    # ---- Arabic
    hafs = load_verses('quranpedia/qpc-hafs.json')
    hafs_basmala = norm(fix_spacing(hafs[1][0]['text']))
    lic, src = licence(meta, 'data/quranpedia/qpc-hafs.json')
    data = {}
    for s, verses in hafs.items():
        ps = []
        for v in verses:
            t = norm(fix_spacing(v['text']))
            p = {'ref': f"{s}:{v['verse']}", 'text': t}
            if v['verse'] == 1 and s not in (1, 9):
                p['heading'] = hafs_basmala
            ps.append(p)
        data[s] = ps
    add(edition('ar-hafs', 'Arabic — Hafs ʿan ʿAsim (KFGQPC text)', 'original', lic, src, base=AR_EDITION,
                notes={'en': "King Fahd Glorious Qur'an Printing Complex Hafs text as digitised by Qur'anpedia.net; "
                             "NFC-normalised for the reader."}), data)

    uth = load_verses('tanzil/uthmani.json')
    uth_basmala = norm(uth[1][0]['text'])
    basmala_prefix = re.compile(r'^' + re.escape(uth_basmala).replace(r'بِ', r'بِّ?', 1) + r'\s+')
    lic, src = licence(meta, 'data/tanzil/uthmani.json')
    data = {}
    for s, verses in uth.items():
        ps = []
        for v in verses:
            t = norm(v['text'])
            p = {'ref': f"{s}:{v['verse']}"}
            if v['verse'] == 1 and s not in (1, 9):
                t2 = basmala_prefix.sub('', t)
                assert t2 != t, (s, t[:40])
                t = t2
                p['heading'] = uth_basmala
            p['text'] = t
            ps.append(p)
        data[s] = ps
    add(edition('ar-uthmani', 'Arabic — Uthmani (Tanzil)', 'original', lic, src, base=AR_EDITION,
                notes={'en': 'Tanzil Uthmani text. The basmala Tanzil prefixes to the first ayah of each surah is '
                             'shown as a heading instead; NFC-normalised for the reader.'}), data)

    simple = load_verses('tanzil/simple-clean.json')
    simple_basmala = norm(simple[1][0]['text'])
    lic, src = licence(meta, 'data/tanzil/simple-clean.json')
    data = {}
    for s, verses in simple.items():
        ps = []
        for v in verses:
            t = norm(v['text'])
            p = {'ref': f"{s}:{v['verse']}"}
            if v['verse'] == 1 and s not in (1, 9):
                assert t.startswith(simple_basmala + ' '), (s, t)
                t = t[len(simple_basmala) + 1:]
                p['heading'] = simple_basmala
            p['text'] = t
            ps.append(p)
        data[s] = ps
    add(edition('ar-simple', 'Arabic — simple (no tashkeel)', 'original', lic, src, base=AR_EDITION,
                notes={'en': 'Tanzil simple-clean text without vowel marks, convenient for searching. The basmala '
                             'prefixed to the first ayah of each surah is shown as a heading instead.'}), data)

    # ---- transliteration
    tl = load_translit()
    if tl:
        tl_basmala = norm(tl[1][0]['text'])
        data = {}
        for s, verses in tl.items():
            ps = []
            for v in verses:
                t = norm(v['text'])
                if not t:
                    continue
                p = {'ref': f"{s}:{v['verse']}", 'text': t}
                if v['verse'] == 1 and s not in (1, 9):
                    p['heading'] = tl_basmala
                ps.append(p)
            data[s] = ps
        add(edition('translit', 'Transliteration (Latin)', 'transliteration',
                    'Repository released under the Unlicense (public domain dedication)',
                    f'{QURAN_API_REPO} (editions/ara-quran-la.json)'), data)
    else:
        print('translit: quran-api ara-quran-la.json not available, skipped')

    # ---- translations
    TRANSLATIONS = [
        ('en-saheeh', 'en', 'English — Saheeh International', 'quranenc/english_saheeh.json'),
        ('en-pickthall', 'en', 'English — Pickthall (1930)', 'extra/english_pickthall.json'),
        ('en-yusufali', 'en', 'English — Yusuf Ali (1934)', 'extra/english_yusuf_ali.json'),
        ('en-rodwell', 'en', 'English — Rodwell (1861)', 'extra/english_rodwell.json'),
        ('en-sale', 'en', 'English — Sale (1734)', 'extra/english_sale.json'),
        ('ur-junagarhi', 'ur', 'Urdu — Muhammad Junagarhi', 'quranenc/urdu_junagarhi.json'),
        ('es-garcia', 'es', 'Spanish — Isa García', 'quranenc/spanish_garcia.json'),
        ('fr-hameedullah', 'fr', 'French — Muhammad Hamidullah', 'quranenc/french_hameedullah.json'),
        ('id-sabiq', 'id', 'Indonesian — Sabiq', 'quranenc/indonesian_sabiq.json'),
        ('tr-rwwad', 'tr', 'Turkish — Rwwad Translation Center', 'quranenc/turkish_rwwad.json'),
    ]
    for ed_id, lang, label, rel in TRANSLATIONS:
        verses = load_verses(rel)
        lic, src = licence(meta, 'data/' + rel)
        # the translation's own basmala wording = its rendering of 1:1
        b_text, _ = clean_translation(verses[1][0]['text'], 1, verses[1][0].get('footnotes'))
        basmala = b_text if b_text else SAHEEH_BASMALA
        if not re.search(r'\bname\b|nom|nombre|nama|ad[ıi]|bismill|نام', basmala, re.I):
            basmala = SAHEEH_BASMALA
        if not basmala.endswith(('.', '۔', '…')):
            basmala += '.'
        data = {}
        for s, vs in verses.items():
            ps = []
            for v in vs:
                t, notes = clean_translation(v['text'], v['verse'], v.get('footnotes'))
                if not t:
                    continue
                p = {'ref': f"{s}:{v['verse']}", 'text': t}
                if v['verse'] == 1 and s not in (1, 9):
                    p['heading'] = basmala
                if notes:
                    p['notes'] = notes
                ps.append(p)
            data[s] = ps
        base = dict(EN_EDITION)
        base['lang'] = lang
        if lang == 'ur':
            base.update({'script': 'Arab', 'direction': 'rtl', 'font': 'arabic'})
        ed = edition(ed_id, label, 'translation', lic, src, base=base)
        if rel.startswith('quranenc/'):
            e = meta['data/' + rel]
            ed['notes'] = {'en': f"{e['source_metadata']['title']}, QuranEnc.com version "
                                 f"{e['source_metadata']['version']}. Verse-number prefixes removed; footnotes "
                                 f"attached as notes."}
        add(ed, data)

    # ---- write
    reset_work(work_id)
    units = passages = 0
    for ed in editions:
        data = ed_data[ed['id']]
        for s in range(1, 115):
            ps = data.get(s) or []
            if ps:
                write_unit(work_id, ed['id'], str(s), ps)
                units += 1
                passages += len(ps)

    toc = []
    aliases = {}
    for s in range(1, 115):
        c = chap[s]
        tr = c['transliteration']
        toc.append({'ref': str(s), 'label': {'en': f"{tr} ({c['translation']})", 'ar': c['name']},
                    'count': c['total_verses']})
        aliases[str(s)] = surah_aliases(tr, c['translation'])

    m = manifest(
        work_id, 'scripture', [], {'en': "The Qur'an", 'ar': 'القرآن الكريم'},
        [{'id': 'surah', 'label': {'en': 'Surah'}, 'isUnit': True}, {'id': 'ayah', 'label': {'en': 'Ayah'}}],
        {'format': '{work} {surah}:{ayah}', 'rangeFormat': '{work} {surah}:{ayah}–{ayah2}', 'workAbbrev': {'en': "Qur'an"}},
        toc, editions, ['ar-hafs', 'en-saheeh'], aliases=aliases,
        notes="Translations convey the meaning; the Arabic text is the Qur'an.")
    write_manifest(work_id, m)
    report(work_id, 'scripture', [], [e['id'] for e in editions], units, passages)
    return ed_data, chapters


def surah_aliases(translit, meaning):
    """'Al-Baqara' + 'The Cow' → baqara, al-baqara, albaqara, baqarah, cow, the cow …"""
    out = []

    def push(x):
        x = x.strip().lower()
        if x and x not in out:
            out.append(x)

    base = translit.lower()
    forms = {base}
    # spelling variants: doubled long vowels → single, drop apostrophes/diacritics
    for f in list(forms):
        forms.add(re.sub(r'aa', 'a', re.sub(r'ee', 'i', re.sub(r'oo', 'u', f))))
    for f in list(forms):
        forms.add(f.replace("'", '').replace('’', '').replace('ʿ', '').replace('ʾ', ''))
    for f in list(forms):
        forms.add(f.replace('-', ' '))
        forms.add(f.replace('-', ''))
    for f in list(forms):
        m = re.match(r'^(al|an|as|ad|ar|at|ash|az|ath|adh|aṭ|aḍ|aṣ|aẓ)[- ](.+)$', f)
        if m:
            forms.add(m.group(2))
            forms.add(m.group(2).replace('-', ' '))
            forms.add(m.group(2).replace('-', ''))
    for f in list(forms):
        if f.endswith('a') and not f.endswith('aa'):
            forms.add(f + 'h')
        if f.endswith('ah'):
            forms.add(f[:-1])
    for f in sorted(forms, key=len):
        push(f)
    mn = meaning.lower()
    push(mn)
    push(re.sub(r'^the ', '', mn))
    for extra in EXTRA_ALIASES.get(translit, []):
        push(extra)
    return out


# common spellings that the generated variants miss (Tanzil's transliterations are idiosyncratic)
EXTRA_ALIASES = {
    'Aal-i-Imraan': ['imran', 'al-imran', 'ali imran', 'aal imran', 'ale imran', 'al imran', 'family of imran'],
    'An-Nisaa': ['nisa', 'an-nisa', 'nisaa', 'women'],
    'Al-Maaida': ['maidah', 'al-maidah', 'maida', 'table spread'],
    'Al-An\'aam': ['anam', 'al-anam', 'anaam'],
    'Al-A\'raaf': ['araf', 'al-araf', 'aaraf'],
    'At-Tawba': ['tawbah', 'at-tawbah', 'tauba', 'taubah', 'repentance', 'baraah', 'baraa'],
    'Yunus': ['jonah'],
    'Hud': ['hood'],
    'Yusuf': ['joseph'],
    'Ar-Ra\'d': ['rad', 'ar-rad', 'raad', 'thunder'],
    'Ibrahim': ['abraham'],
    'Al-Israa': ['isra', 'al-isra', 'bani israil', 'bani israel', 'night journey'],
    'Al-Kahf': ['kahf', 'cave'],
    'Maryam': ['mary'],
    'Taa-Haa': ['taha', 'ta-ha', 'ta ha'],
    'Al-Anbiyaa': ['anbiya', 'al-anbiya', 'prophets'],
    'Al-Muminoon': ['muminun', 'al-muminun', 'mu\'minun', 'believers'],
    'An-Noor': ['nur', 'an-nur', 'noor', 'light'],
    'Ash-Shu\'araa': ['shuara', 'ash-shuara', 'poets'],
    'An-Naml': ['naml', 'ant', 'ants'],
    'Al-Qasas': ['qasas', 'stories'],
    'Al-Ankaboot': ['ankabut', 'al-ankabut', 'spider'],
    'Ar-Room': ['rum', 'ar-rum', 'romans'],
    'As-Sajda': ['sajdah', 'as-sajdah', 'prostration'],
    'Al-Ahzaab': ['ahzab', 'al-ahzab'],
    'Yaseen': ['yasin', 'ya-sin', 'ya sin', 'yaa seen'],
    'As-Saaffaat': ['saffat', 'as-saffat'],
    'Saad': ['sad', 'suad'],
    'Az-Zumar': ['zumar'],
    'Al-Ghaafir': ['mumin', 'al-mumin', 'forgiver'],
    'Fussilat': ['ha-mim sajdah', 'ha mim'],
    'Ash-Shura': ['shura', 'consultation'],
    'Az-Zukhruf': ['zukhruf'],
    'Ad-Dukhaan': ['dukhan', 'ad-dukhan', 'smoke'],
    'Al-Jaathiya': ['jathiyah', 'al-jathiyah', 'jathiya'],
    'Al-Ahqaf': ['ahqaf'],
    'Al-Fath': ['fath', 'victory'],
    'Al-Hujuraat': ['hujurat', 'al-hujurat'],
    'Qaaf': ['qaf'],
    'Adh-Dhaariyat': ['dhariyat', 'adh-dhariyat', 'zariyat'],
    'At-Tur': ['tur', 'mount'],
    'An-Najm': ['najm', 'star'],
    'Al-Qamar': ['qamar', 'moon'],
    'Ar-Rahmaan': ['rahman', 'ar-rahman', 'al-rahman'],
    'Al-Waaqia': ['waqiah', 'al-waqiah', 'waqia', 'inevitable'],
    'Al-Hadid': ['hadid', 'iron'],
    'Al-Mujaadila': ['mujadilah', 'al-mujadilah', 'mujadila'],
    'Al-Hashr': ['hashr', 'exile'],
    'Al-Mumtahana': ['mumtahanah', 'al-mumtahanah'],
    'As-Saff': ['saff', 'ranks'],
    'Al-Jumu\'a': ['jumuah', 'al-jumuah', 'jumah', 'friday'],
    'Al-Munaafiqoon': ['munafiqun', 'al-munafiqun', 'hypocrites'],
    'At-Taghaabun': ['taghabun', 'at-taghabun'],
    'At-Talaaq': ['talaq', 'at-talaq', 'divorce'],
    'At-Tahrim': ['tahrim'],
    'Al-Mulk': ['mulk', 'sovereignty', 'kingdom'],
    'Al-Qalam': ['qalam', 'pen', 'nun'],
    'Al-Haaqqa': ['haqqah', 'al-haqqah', 'haqqa'],
    'Al-Ma\'aarij': ['maarij', 'al-maarij'],
    'Nooh': ['nuh', 'noah'],
    'Al-Jinn': ['jinn'],
    'Al-Muzzammil': ['muzzammil', 'muzammil'],
    'Al-Muddaththir': ['muddathir', 'al-muddathir', 'mudathir'],
    'Al-Qiyaama': ['qiyamah', 'al-qiyamah', 'qiyama', 'resurrection'],
    'Al-Insaan': ['insan', 'al-insan', 'dahr', 'ad-dahr', 'man'],
    'Al-Mursalaat': ['mursalat', 'al-mursalat'],
    'An-Naba': ['naba', 'an-naba', 'tidings', 'news'],
    'An-Naazi\'aat': ['naziat', 'an-naziat', 'naziaat'],
    'Abasa': ['abasa'],
    'At-Takwir': ['takwir'],
    'Al-Infitaar': ['infitar', 'al-infitar'],
    'Al-Mutaffifin': ['mutaffifin', 'tatfif'],
    'Al-Inshiqaaq': ['inshiqaq', 'al-inshiqaq'],
    'Al-Burooj': ['buruj', 'al-buruj'],
    'At-Taariq': ['tariq', 'at-tariq'],
    'Al-A\'laa': ['ala', 'al-ala', 'alaa'],
    'Al-Ghaashiya': ['ghashiyah', 'al-ghashiyah', 'ghashiya'],
    'Al-Fajr': ['fajr', 'dawn'],
    'Al-Balad': ['balad', 'city'],
    'Ash-Shams': ['shams', 'sun'],
    'Al-Lail': ['layl', 'al-layl', 'lail', 'night'],
    'Ad-Dhuhaa': ['duha', 'ad-duha', 'dhuha', 'morning'],
    'Ash-Sharh': ['sharh', 'inshirah', 'al-inshirah', 'alam nashrah'],
    'At-Tin': ['tin', 'fig'],
    'Al-Alaq': ['alaq', 'iqra', 'clot'],
    'Al-Qadr': ['qadr', 'power', 'decree'],
    'Al-Bayyina': ['bayyinah', 'al-bayyinah'],
    'Az-Zalzala': ['zalzalah', 'az-zalzalah', 'zilzal', 'earthquake'],
    'Al-Aadiyaat': ['adiyat', 'al-adiyat'],
    'Al-Qaari\'a': ['qariah', 'al-qariah', 'qaria', 'calamity'],
    'At-Takaathur': ['takathur', 'at-takathur'],
    'Al-Asr': ['asr', 'time'],
    'Al-Humaza': ['humazah', 'al-humazah'],
    'Al-Fil': ['fil', 'elephant'],
    'Quraish': ['quraysh'],
    'Al-Maa\'un': ['maun', 'al-maun'],
    'Al-Kawthar': ['kawthar', 'kauthar', 'abundance'],
    'Al-Kaafiroon': ['kafirun', 'al-kafirun', 'kafiroon', 'disbelievers'],
    'An-Nasr': ['nasr', 'help'],
    'Al-Masad': ['masad', 'lahab', 'al-lahab', 'tabbat'],
    'Al-Ikhlaas': ['ikhlas', 'tawhid', 'sincerity'],
    'Al-Falaq': ['falaq', 'daybreak'],
    'An-Naas': ['nas', 'an-nas', 'mankind'],
    'Al-Faatiha': ['fatiha', 'al-fatiha', 'fatihah', 'opening'],
    'Al-Baqara': ['baqarah', 'al-baqarah', 'cow'],
}


# ---------------------------------------------------------------- juz' of the day
def convert_juz(ed_data, chapters):
    work_id = 'juz-of-the-day'
    chap = {c['id']: c for c in chapters['chapters']}
    juzs = sorted(chapters['indexes']['juzs'], key=lambda j: j['index'])
    assert len(juzs) == 30
    bounds = []
    for i, j in enumerate(juzs):
        start = (j['sura'], j['aya'])
        if i + 1 < len(juzs):
            n = juzs[i + 1]
            # end = the ayah before the next juz' start
            if n['aya'] > 1:
                end = (n['sura'], n['aya'] - 1)
            else:
                end = (n['sura'] - 1, chap[n['sura'] - 1]['total_verses'])
        else:
            end = (114, 6)
        bounds.append((j['index'], start, end))

    def ayat_in(start, end):
        s, a = start
        while (s, a) <= end:
            yield s, a
            a += 1
            if a > chap[s]['total_verses']:
                s += 1
                a = 1

    ar = ed_data['ar-hafs']
    en = ed_data['en-saheeh']
    ar_by = {p['ref']: p for s in ar for p in ar[s]}
    en_by = {p['ref']: p for s in en for p in en[s]}

    reset_work(work_id)
    toc = []
    units = passages = 0
    for idx, start, end in bounds:
        unit = str(idx)
        ps_ar, ps_en = [], []
        for s, a in ayat_in(start, end):
            ref = f'{unit}:{s}-{a}'
            src_ar, src_en = ar_by[f'{s}:{a}'], en_by.get(f'{s}:{a}')
            first = (s, a) == start or a == 1
            p = {'ref': ref, 'text': src_ar['text']}
            if first:
                h = f"سورة {chap[s]['name']}"
                if a == 1 and src_ar.get('heading'):
                    h += '\n' + src_ar['heading']
                p['heading'] = h
            ps_ar.append(p)
            if src_en:
                p = {'ref': ref, 'text': src_en['text']}
                if first:
                    h = f"Surah {s} — {chap[s]['transliteration']} ({chap[s]['translation']})"
                    if a == 1 and src_en.get('heading'):
                        h += '\n' + src_en['heading']
                    p['heading'] = h
                if src_en.get('notes'):
                    p['notes'] = src_en['notes']
                ps_en.append(p)
        write_unit(work_id, 'ar', unit, ps_ar)
        write_unit(work_id, 'en', unit, ps_en)
        units += 2
        passages += len(ps_ar) + len(ps_en)
        toc.append({'ref': unit, 'label': {'en': f"Juz' {idx} ({start[0]}:{start[1]} – {end[0]}:{end[1]})"},
                    'count': len(ps_ar)})

    qm = load_json(os.path.join(WORKS, 'quran', 'manifest.json'))
    q_eds = {e['id']: e for e in qm['editions']}
    ar_ed = edition('ar', q_eds['ar-hafs']['label']['en'], 'original', q_eds['ar-hafs']['license'],
                    q_eds['ar-hafs']['source'], base=AR_EDITION)
    en_ed = edition('en', q_eds['en-saheeh']['label']['en'], 'translation', q_eds['en-saheeh']['license'],
                    q_eds['en-saheeh']['source'])
    m = manifest(
        work_id, 'devotional', [], {'en': "Juz' of the Day", 'ar': 'جزء اليوم'},
        [{'id': 'juz', 'label': {'en': "Juz'"}, 'isUnit': True}, {'id': 'ayah', 'label': {'en': 'Ayah'}}],
        {'format': "{work} {juz} · {ayah}", 'rangeFormat': "{work} {juz} · {ayah}–{ayah2}", 'workAbbrev': {'en': "Juz'"}},
        toc, [ar_ed, en_ed], ['ar', 'en'],
        subtitle={'en': "One thirtieth of the Qur'an for each day of the Islamic month"},
        calendar='islamic-umalqura', dateKey='{D}',
        notes="The juz' for today's day of the Hijri month (Umm al-Qura). Day 30 has no juz' in a 29-day month; read juz' 30 on the 29th.")
    write_manifest(work_id, m)
    report(work_id, 'devotional', [], ['ar', 'en'], units, passages)


if __name__ == '__main__':
    want = sys.argv[1:] or ['quran', 'juz-of-the-day']
    ed_data = chapters = None
    if 'quran' in want or 'juz-of-the-day' in want:
        ed_data, chapters = convert_quran()
    if 'juz-of-the-day' in want:
        convert_juz(ed_data, chapters)
