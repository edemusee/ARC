"""Edition specs, book-code maps and canons for convert_extra.py.

Every edition added on top of convert_bible.py's ten is declared in EDITIONS below:
    id, lang, label, src=(kind, file/abbr), license, source, [script, direction, font, role, canon,
    families, notes, fix, vulgate_psalms, book_filter, repair]
`fix` names a cleanup function in convert_extra.FIXES. `vulgate_psalms` is 'title' (Septuagint/Vulgate psalm
numbers, superscription counted as verse 1) or 'notitle' (same numbering, superscription not a verse).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

OT39, NT27 = C.OT39, C.NT27

# ------------------------------------------------------------------ book-code maps

# thiagobodruk/bible: Portuguese abbreviations in all current files; English ones in the two legacy files
# (en_bbe, fr_apee). Collisions (jo, jd, jn, ez, ed, lm, …) resolve to the same code in both sets.
THIAGO_ABBREV = {
    'gn': 'gen', 'ex': 'exo', 'lv': 'lev', 'nm': 'num', 'dt': 'deu', 'js': 'jos', 'jz': 'jdg', 'jud': 'jdg', 'rt': 'rut',
    '1sm': '1sa', '2sm': '2sa', '1rs': '1ki', '2rs': '2ki', '1kgs': '1ki', '2kgs': '2ki', '1cr': '1ch', '2cr': '2ch',
    '1ch': '1ch', '2ch': '2ch', 'ed': 'ezr', 'ezr': 'ezr', 'ne': 'neh', 'et': 'est', 'jó': 'job', 'job': 'job',
    'sl': 'psa', 'ps': 'psa', 'pv': 'pro', 'prv': 'pro', 'ec': 'ecc', 'ct': 'sng', 'so': 'sng', 'is': 'isa', 'jr': 'jer',
    'lm': 'lam', 'ez': 'ezk', 'dn': 'dan', 'os': 'hos', 'ho': 'hos', 'jl': 'jol', 'am': 'amo', 'ob': 'oba', 'jn': 'jon',
    'mq': 'mic', 'mi': 'mic', 'na': 'nam', 'hc': 'hab', 'hk': 'hab', 'sf': 'zep', 'zp': 'zep', 'ag': 'hag', 'hg': 'hag',
    'zc': 'zec', 'ml': 'mal', 'mt': 'mat', 'mc': 'mrk', 'mk': 'mrk', 'lc': 'luk', 'lk': 'luk', 'jo': 'jhn', 'atos': 'act',
    'act': 'act', 'rm': 'rom', '1co': '1co', '2co': '2co', 'gl': 'gal', 'ef': 'eph', 'eph': 'eph', 'fp': 'php', 'ph': 'php',
    'cl': 'col', '1ts': '1th', '2ts': '2th', '1tm': '1ti', '2tm': '2ti', 'tt': 'tit', 'fm': 'phm', 'phm': 'phm', 'hb': 'heb',
    'tg': 'jas', 'jm': 'jas', '1pe': '1pe', '2pe': '2pe', '1jo': '1jn', '2jo': '2jn', '3jo': '3jn', 'jd': 'jud',
    'ap': 'rev', 're': 'rev',
}

SCROLLMAPPER_EXTRA_NAMES = dict(C.SCROLLMAPPER_NAMES)
SCROLLMAPPER_EXTRA_NAMES.update({
    'Additional Psalm': 'ps151', 'Epistle of Jeremiah': 'lje', 'Esther (Greek)': 'esg', 'III Maccabees': '3ma',
    'IV Maccabees': '4ma', 'Additions to Esther': 'esg',
    # not carried: no book code in the library
    'Laodiceans': None, 'Psalms of Solomon': None, 'I Enoch': None, 'Odes': None, 'Additions to Daniel': None,
})

MDBIBLE_FILES = {
    'Genesis': 'gen', 'Exodus': 'exo', 'Leviticus': 'lev', 'Numbers': 'num', 'Deuteronomy': 'deu', 'Joshua': 'jos',
    'Judges': 'jdg', 'Ruth': 'rut', 'I_Samuel': '1sa', 'II_Samuel': '2sa', 'I_Kings': '1ki', 'II_Kings': '2ki',
    'I_Chronicles': '1ch', 'II_Chronicles': '2ch', 'Ezra': 'ezr', 'Nehemiah': 'neh', 'Esther': 'est', 'Job': 'job',
    'Psalms': 'psa', 'Proverbs': 'pro', 'Ecclesiastes': 'ecc', 'Song_of_Solomon': 'sng', 'Isaiah': 'isa', 'Jeremiah': 'jer',
    'Lamentations': 'lam', 'Ezekiel': 'ezk', 'Daniel': 'dan', 'Hosea': 'hos', 'Joel': 'jol', 'Amos': 'amo', 'Obadiah': 'oba',
    'Jonah': 'jon', 'Micah': 'mic', 'Nahum': 'nam', 'Habakkuk': 'hab', 'Zephaniah': 'zep', 'Haggai': 'hag',
    'Zechariah': 'zec', 'Malachi': 'mal', 'Matthew': 'mat', 'Mark': 'mrk', 'Luke': 'luk', 'John': 'jhn', 'Acts': 'act',
    'Romans': 'rom', 'I_Corinthians': '1co', 'II_Corinthians': '2co', 'Galatians': 'gal', 'Ephesians': 'eph',
    'Philippians': 'php', 'Colossians': 'col', 'I_Thessalonians': '1th', 'II_Thessalonians': '2th', 'I_Timothy': '1ti',
    'II_Timothy': '2ti', 'Titus': 'tit', 'Philemon': 'phm', 'Hebrews': 'heb', 'James': 'jas', 'I_Peter': '1pe',
    'II_Peter': '2pe', 'I_John': '1jn', 'II_John': '2jn', 'III_John': '3jn', 'Jude': 'jud', 'Revelation_of_John': 'rev',
}

NABRE_NAMES = {
    'Genesis': 'gen', 'Exodus': 'exo', 'Leviticus': 'lev', 'Numbers': 'num', 'Deuteronomy': 'deu', 'Joshua': 'jos',
    'Judges': 'jdg', 'Ruth': 'rut', '1Samuel': '1sa', '2Samuel': '2sa', '1Kings': '1ki', '2Kings': '2ki',
    '1Chronicles': '1ch', '2Chronicles': '2ch', 'Ezra': 'ezr', 'Nehemiah': 'neh', 'Tobit': 'tob', 'Judith': 'jdt',
    'Esther': 'est', '1Maccabees': '1ma', '2Maccabees': '2ma', 'Job': 'job', 'Psalms': 'psa', 'Proverbs': 'pro',
    'Ecclesiastes': 'ecc', 'SongofSongs': 'sng', 'Wisdom': 'wis', 'Sirach': 'sir', 'Isaiah': 'isa', 'Jeremiah': 'jer',
    'Lamentations': 'lam', 'Baruch': 'bar', 'Ezekiel': 'ezk', 'Daniel': 'dan', 'Hosea': 'hos', 'Joel': 'jol', 'Amos': 'amo',
    'Obadiah': 'oba', 'Jonah': 'jon', 'Micah': 'mic', 'Nahum': 'nam', 'Habakkuk': 'hab', 'Zephaniah': 'zep',
    'Haggai': 'hag', 'Zechariah': 'zec', 'Malachi': 'mal', 'Matthew': 'mat', 'Mark': 'mrk', 'Luke': 'luk', 'John': 'jhn',
    'Acts': 'act', 'Romans': 'rom', '1Corinthians': '1co', '2Corinthians': '2co', 'Galatians': 'gal', 'Ephesians': 'eph',
    'Philippians': 'php', 'Colossians': 'col', '1Thessalonians': '1th', '2Thessalonians': '2th', '1Timothy': '1ti',
    '2Timothy': '2ti', 'Titus': 'tit', 'Philemon': 'phm', 'Hebrews': 'heb', 'James': 'jas', '1Peter': '1pe',
    '2Peter': '2pe', '1John': '1jn', '2John': '2jn', '3John': '3jn', 'Jude': 'jud', 'Revelation': 'rev',
}

# ------------------------------------------------------------------ canons

TANAKH = ['gen', 'exo', 'lev', 'num', 'deu', 'jos', 'jdg', '1sa', '2sa', '1ki', '2ki', 'isa', 'jer', 'ezk', 'hos', 'jol',
          'amo', 'oba', 'jon', 'mic', 'nam', 'hab', 'zep', 'hag', 'zec', 'mal', 'psa', 'pro', 'job', 'sng', 'rut', 'lam',
          'ecc', 'est', 'dan', 'ezr', 'neh', '1ch', '2ch']

EXTRA_CANONS = {
    'nt-27': list(NT27),
    'hebrew-ot-39': TANAKH,
    'pentateuch-5': OT39[:5],
    'psalms-nt-28': ['psa'] + list(NT27),
    # Russian Synodal / Church Slavonic order: 2 Esdras (1es) after Nehemiah, 3 Esdras (2es) after 3 Maccabees,
    # Prayer of Manasseh (part of 2 Chr 36 in print) kept as its own book after 2 Chronicles, Psalm 151 after Psalms.
    'orthodox-synodal-79': ['gen', 'exo', 'lev', 'num', 'deu', 'jos', 'jdg', 'rut', '1sa', '2sa', '1ki', '2ki', '1ch', '2ch',
                            'man', 'ezr', 'neh', '1es', 'tob', 'jdt', 'est', 'job', 'psa', 'ps151', 'pro', 'ecc', 'sng',
                            'wis', 'sir', 'isa', 'jer', 'lam', 'lje', 'bar', 'ezk', 'dan', 'hos', 'jol', 'amo', 'oba', 'jon',
                            'mic', 'nam', 'hab', 'zep', 'hag', 'zec', 'mal', '1ma', '2ma', '3ma', '2es'] + NT27,
    # Protestant Bibles with the Apocrypha but without 1-2 Esdras (Menge, Swedish 1917)
    'apocrypha-78': [c for c in C.CANONS['kjv-apocrypha-80'] if c not in ('1es', '2es')],
    # Vulgate with its appendix (Prayer of Manasseh, 3 and 4 Esdras after the New Testament)
    'vulgate-appendix-76': C.CANONS['catholic-73'] + ['man', '1es', '2es'],
}

# Every code the library knows, in a sensible global order (used to order books of editions without a named canon).
ALL_CODES = []
for _lst in [C.CANONS['kjv-apocrypha-80'], C.CANONS['orthodox-web-84'], C.CANONS['lxx-brenton'], EXTRA_CANONS['orthodox-synodal-79']]:
    for _c in _lst:
        if _c not in ALL_CODES:
            ALL_CODES.append(_c)
_nt = [c for c in ALL_CODES if c in NT27]
ALL_CODES = [c for c in ALL_CODES if c not in NT27] + _nt

# ------------------------------------------------------------------ language defaults

LANG = {   # lang -> (script, direction, font)
    'ar': ('Arab', 'rtl', 'arabic'), 'fa': ('Arab', 'rtl', 'arabic'), 'he': ('Hebr', 'rtl', 'hebrew'),
    'hbo': ('Hebr', 'rtl', 'hebrew'), 'syc': ('Syrc', 'rtl', None), 'el': ('Grek', 'ltr', None), 'grc': ('Grek', 'ltr', None),
    'ru': ('Cyrl', 'ltr', None), 'uk': ('Cyrl', 'ltr', None), 'bg': ('Cyrl', 'ltr', None), 'sr': ('Cyrl', 'ltr', None),
    'be': ('Cyrl', 'ltr', None), 'cu': ('Cyrs', 'ltr', None), 'zh': ('Hans', 'ltr', None), 'lzh': ('Hant', 'ltr', None),
    'ja': ('Jpan', 'ltr', None), 'ko': ('Kore', 'ltr', None), 'th': ('Thai', 'ltr', None), 'hi': ('Deva', 'ltr', 'devanagari'),
    'mr': ('Deva', 'ltr', 'devanagari'), 'bn': ('Beng', 'ltr', None), 'pa': ('Guru', 'ltr', 'gurmukhi'),
    'ta': ('Taml', 'ltr', None), 'te': ('Telu', 'ltr', None), 'my': ('Mymr', 'ltr', None), 'ml': ('Mlym', 'ltr', None),
    'chr': ('Cher', 'ltr', None),
}

# ------------------------------------------------------------------ license strings

PD = 'Public domain'
CLEARED = "included under the project's cleared-permission assumption — not public domain"


def thiago_lic(holder):
    return (f'© {holder} (from thiagobodruk/bible, which states versions are property of their owners); '
            f"included under the project's cleared-permission assumption")


def cleared(holder):
    return f'© {holder}; {CLEARED}'


IRV = 'CC BY-SA 4.0 (© Bridge Connectivity Solutions, Indian Revised Version)'
THIAGO_SRC = 'https://github.com/thiagobodruk/bible (json/%s.json)'
SM_SRC = 'https://github.com/scrollmapper/bible_databases (formats/json/%s.json)'
OB_SRC = 'https://github.com/seven1m/open-bibles (%s)'

EDITIONS = []


def _ed(id, lang, label, src, license, source, **kw):
    e = dict(id=id, lang=lang, label=label if isinstance(label, dict) else {'en': label}, src=src, license=license,
             source=source)
    base = kw.pop('base_lang', lang)
    script, direction, font = LANG.get(base, ('Latn', 'ltr', None))
    e['script'] = kw.pop('script', script)
    e['direction'] = kw.pop('direction', direction)
    f = kw.pop('font', font)
    if f:
        e['font'] = f
    e.update(kw)
    EDITIONS.append(e)
    return e


def T(id, file, lang, label, license, **kw):
    return _ed(id, lang, label, ('thiago', file), license, THIAGO_SRC % file, **kw)


def S(id, abbr, lang, label, license, kind='scrollmapper', **kw):
    return _ed(id, lang, label, (kind, abbr), license, SM_SRC % abbr, **kw)


def O(id, file, lang, label, license, kind, **kw):
    return _ed(id, lang, label, (kind, file), license, OB_SRC % file, **kw)


# ================================================================== 1. ESV, 2. NABRE

_ed('esv', 'en', 'English Standard Version', ('mdbible', 'by_book'),
    "© 2001 Crossway; included under the project's cleared-permission assumption — not public domain",
    'https://github.com/lguenth/mdbible (by_book/*.md; text from javascripture)', canon='protestant-66',
    notes='The Markdown source carries no section headings or footnotes.')
_ed('nabre', 'en', 'New American Bible, Revised Edition (NABRE)', ('nabre', 'nabre.json'),
    "© 2010 United States Conference of Catholic Bishops; included under the project's cleared-permission assumption",
    'https://github.com/nirmalben/bible-nabre-json-dataset (generated_data/nabre.json; scraped from BibleGateway)',
    canon='catholic-73', families=['catholic'],
    notes='Section headings scraped into the verse text have been separated out heuristically. Esther is given in '
          'ten chapters (the Greek additions A–F are not carried by the source); Daniel has fourteen; Joel has four '
          'and Malachi three, following the Hebrew chapter divisions.')

# ================================================================== 3. thiagobodruk/bible

T('ar-kehm', 'ar_kehm', 'ar', {'en': 'Ketab El Hayat / New Arabic Version (Arabic)', 'ar': 'كتاب الحياة'}, thiago_lic('Biblica (Ketab El Hayat)'))
T('be-semukha', 'be_bbl', 'be', {'en': 'Semukha Bible 2002 (Belarusian)', 'be': 'Біблія (пераклад Васіля Сёмухі)'},
  thiago_lic('the Semukha translation rights holders'), vulgate_psalms='title',
  notes='Psalms are shown under the Hebrew (KJV) psalm numbers; the edition follows the Septuagint numbering and counts the superscription as verse 1.')
T('bn-irv', 'bn_irvben', 'bn', {'en': 'Indian Revised Version (Bengali)'}, IRV)
T('el-fpb', 'el_fpb', 'el', {'en': 'Modern Greek (Demotic) Bible, FPB'}, thiago_lic('the FPB Modern Greek text rights holders'))
T('en-amp', 'en_amp', 'en', 'Amplified Bible (2015)', thiago_lic('2015 The Lockman Foundation'),
  notes='Bracketed amplifications are part of the translation and are kept as plain text.')
T('en-cev', 'en_cev', 'en', 'Contemporary English Version', thiago_lic('1995 American Bible Society'),
  notes='The CEV combines some verses; combined verses carry the first verse number only.')
T('en-csb', 'en_csb', 'en', 'Christian Standard Bible (2017)', thiago_lic('2017 Holman Bible Publishers'))
T('en-rv1885', 'en_engrv', 'en', 'English Revised Version (1885)', PD)
T('en-fbv', 'en_fbv', 'en', 'Free Bible Version', 'CC BY-SA 4.0 (© Jonathan Gallagher)')
T('en-gnt', 'en_gnt', 'en', 'Good News Translation', thiago_lic('1992 American Bible Society'),
  notes='The GNT combines some verses; combined verses carry the first verse number only.')
T('geneva1599', 'en_gnv', 'en', 'Geneva Bible (1599)', PD)
T('en-kjvcpb', 'en_kjvcpb', 'en', 'King James Version, Cambridge Paragraph Bible (1873)', PD)
T('en-leb', 'en_leb', 'en', 'Lexham English Bible', thiago_lic('2012 Logos Bible Software'))
T('en-lsv', 'en_lsv', 'en', 'Literal Standard Version (2020)', 'CC BY-SA 4.0 (© 2020 Covenant Press)', fix='lsv_fix',
  notes='Bracketed alternative readings are kept as notes; the || line markers are shown as line breaks.')
T('en-msb', 'en_mbsb', 'en', 'Majority Standard Bible', 'Public domain (Berean Bible texts released to the public domain)')
T('en-nasb2020', 'en_nasb', 'en', 'New American Standard Bible (2020)', thiago_lic('2020 The Lockman Foundation'))
T('en-niv', 'en_niv', 'en', 'New International Version (2011)', thiago_lic('2011 Biblica, Inc.'))
T('en-nkjv', 'en_nkjv', 'en', 'New King James Version', thiago_lic('1982 Thomas Nelson'))
T('en-nlt', 'en_nlt', 'en', 'New Living Translation', thiago_lic('2015 Tyndale House Foundation'))
T('en-nmv', 'en_nmv', 'en', 'New Messianic Version Bible', thiago_lic('Tov Rose (New Messianic Version)'), fix='nmv_fix')
T('en-t4t', 'en_t4t', 'en', 'A Translation for Translators', 'CC BY-SA 4.0 (© 2008–2017 Ellis W. Deibler)', fix='t4t_fix',
  notes='Figure-of-speech tags such as [MET] have been removed; alternative renderings are shown in parentheses.')
T('en-ojb', 'en_tojb2011', 'en', 'The Orthodox Jewish Bible (2011)', thiago_lic('2011 Artists for Israel International'),
  notes='Malachi has three chapters, following the Hebrew division.')
T('en-wycliffe-modern', 'en_wbms', 'en', "Wycliffe's Bible with Modern Spelling", thiago_lic('2001 Terence P. Noble (modern-spelling edition; free use)'),
  notes="Bracketed glosses are the editor's and are kept as plain text.")
T('en-wmb', 'en_wmb', 'en', 'World Messianic Bible', PD)
T('ylt', 'en_ylt98', 'en', "Young's Literal Translation (1898)", PD, fix='supplied')
T('eo-esp', 'eo_esp', 'eo', {'en': 'La Sankta Biblio 1926 (Esperanto)', 'eo': 'La Sankta Biblio'}, PD)
T('es-rvr1960', 'es_rvr1960', 'es', {'en': 'Reina-Valera 1960 (Spanish)', 'es': 'Reina-Valera 1960'},
  thiago_lic('1960 Sociedades Bíblicas en América Latina'))
T('fa-pcb', 'fa_opcb', 'fa', {'en': 'Persian Contemporary Bible (2022)'}, thiago_lic('Biblica, Inc. (Persian Contemporary Bible)'),
  notes='Some verses are combined; combined verses carry the first verse number only.')
T('fi-1938', 'fi_fb38', 'fi', {'en': 'Kirkkoraamattu 1933/1938 (Finnish)', 'fi': 'Pyhä Raamattu 1933/1938'}, PD)
T('fr-epee', 'fr_apee', 'fr', {'en': "Bible de l'Épée (French)", 'fr': "La Bible de l'Épée"}, thiago_lic("Jean leDuc (Bible de l'Épée)"))
T('hi-irv', 'hi_irvhin', 'hi', {'en': 'Indian Revised Version 2019 (Hindi)'}, IRV)
T('it-riveduta2020', 'it_irb20', 'it', {'en': 'Sacra Bibbia Versione Riveduta 2020 (Italian)', 'it': 'Versione Riveduta 2020'},
  thiago_lic('Società Biblica di Ginevra (Riveduta 2020)'))
T('mr-irv', 'mr_irvmar', 'mr', {'en': 'Indian Revised Version (Marathi)'}, IRV)
T('nb-2011', 'nb_bibel2011', 'nb', {'en': 'Bibel 2011 (Norwegian Bokmål)', 'nb': 'Bibel 2011'}, thiago_lic('2011 Det Norske Bibelselskap'),
  fix='dbl_brace_to_supplied')
T('pa-irv', 'pa_irvpun', 'pa', {'en': 'Indian Revised Version (Punjabi)'}, IRV)
T('pt-a21', 'pt_a21', 'pt', {'en': 'Almeida Século 21 (Portuguese)', 'pt': 'Almeida Século 21'}, thiago_lic('Edições Vida Nova (Almeida Século 21)'))
T('pt-aa', 'pt_aa', 'pt', {'en': 'Almeida Revisada Imprensa Bíblica (Portuguese)', 'pt': 'Almeida Revisada Imprensa Bíblica'},
  'Public domain (Almeida lineage; the 1967 Imprensa Bíblica revision is treated as public domain per the project assumption)', fix='brace_note')
T('pt-acf', 'pt_acf', 'pt', {'en': 'Almeida Corrigida Fiel (Portuguese)', 'pt': 'Almeida Corrigida e Revisada Fiel'},
  thiago_lic('Sociedade Bíblica Trinitariana do Brasil (Almeida Corrigida Fiel)'))
T('pt-ara', 'pt_ara', 'pt', {'en': 'Almeida Revista e Atualizada (Portuguese)', 'pt': 'Almeida Revista e Atualizada'},
  thiago_lic('1993 Sociedade Bíblica do Brasil'))
T('pt-arc', 'pt_arc', 'pt', {'en': 'Almeida Revista e Corrigida (Portuguese)', 'pt': 'Almeida Revista e Corrigida'},
  'Public domain (Almeida Revista e Corrigida, 1898 lineage; treated as public domain per the project assumption)')
T('pt-avm', 'pt_avm', 'pt', {'en': 'Bíblia Sagrada Ave-Maria (Portuguese)', 'pt': 'Bíblia Sagrada Ave-Maria'},
  thiago_lic('Editora Ave-Maria'), vulgate_psalms='title', families=['catholic'],
  notes='Psalms are shown under the Hebrew (KJV) psalm numbers; the edition follows the Vulgate numbering. Malachi has three chapters.')
T('pt-bkj', 'pt_bkj', 'pt', {'en': 'King James Fiel (Portuguese)', 'pt': 'Bíblia King James Fiel'}, thiago_lic('BV Books (King James Fiel)'))
T('pt-bpt09', 'pt_bpt09', 'pt', {'en': 'Bíblia para Todos 2009 (Portuguese)', 'pt': 'Bíblia para Todos'},
  thiago_lic('2009 Sociedade Bíblica de Portugal'), notes='Malachi has three chapters.')
T('pt-kja', 'pt_kja', 'pt', {'en': 'King James Atualizada (Portuguese)', 'pt': 'King James Atualizada'},
  thiago_lic('Sociedade Bíblica Ibero-Americana / Abba Press (King James Atualizada)'))
T('pt-matos', 'pt_matos', 'pt', {'en': 'Matos Soares (Portuguese)', 'pt': 'Tradução do Pe. Matos Soares'},
  thiago_lic('Edições Paulinas (Matos Soares)'), vulgate_psalms='title', families=['catholic'], fix='strip_markers',
  notes='Psalms are shown under the Hebrew (KJV) psalm numbers; the edition follows the Vulgate numbering. Malachi has three chapters.')
T('pt-naa', 'pt_naa', 'pt', {'en': 'Nova Almeida Atualizada (Portuguese)', 'pt': 'Nova Almeida Atualizada'},
  thiago_lic('2017 Sociedade Bíblica do Brasil'))
T('pt-nbv', 'pt_nbv', 'pt', {'en': 'Nova Bíblia Viva 2007 (Portuguese)', 'pt': 'Nova Bíblia Viva'}, thiago_lic('2007 Editora Mundo Cristão'))
T('pt-ntlh', 'pt_ntlh', 'pt', {'en': 'Nova Tradução na Linguagem de Hoje (Portuguese)', 'pt': 'Nova Tradução na Linguagem de Hoje'},
  thiago_lic('2000 Sociedade Bíblica do Brasil'), notes='Some verses are combined; combined verses carry the first verse number only.')
T('pt-nvi', 'pt_nvi', 'pt', {'en': 'Nova Versão Internacional (Portuguese)', 'pt': 'Nova Versão Internacional'}, thiago_lic('Biblica, Inc.'))
T('pt-nvi2011', 'pt_nvi2011', 'pt', {'en': 'Nova Versão Internacional 2011 (Portuguese)', 'pt': 'Nova Versão Internacional 2011'}, thiago_lic('2011 Biblica, Inc.'))
T('pt-nvt', 'pt_nvt', 'pt', {'en': 'Nova Versão Transformadora (Portuguese)', 'pt': 'Nova Versão Transformadora'}, thiago_lic('2016 Editora Mundo Cristão'))
T('pt-ol', 'pt_ol', 'pt', {'en': 'O Livro (Portuguese)', 'pt': 'O Livro'}, thiago_lic('Biblica, Inc. (O Livro)'),
  notes='Some verses are combined; combined verses carry the first verse number only.')
T('pt-pastoral', 'pt_pastoral', 'pt', {'en': 'Edição Pastoral (Portuguese)', 'pt': 'Bíblia Sagrada Edição Pastoral'},
  thiago_lic('Paulus Editora (Edição Pastoral)'), families=['catholic'], notes='Malachi has three chapters.')
T('pt-rc69', 'pt_rc69', 'pt', {'en': 'Almeida Revista e Corrigida 1969 (Portuguese)', 'pt': 'Almeida Revista e Corrigida 1969'},
  thiago_lic('1969 Sociedade Bíblica do Brasil'))
T('pt-tb', 'pt_tb', 'pt', {'en': 'Tradução Brasileira 1917 (Portuguese)', 'pt': 'Tradução Brasileira'}, PD)
T('pt-vfl', 'pt_vfl', 'pt', {'en': 'Versão Fácil de Ler (Portuguese)', 'pt': 'Bíblia Sagrada: Versão Fácil de Ler'},
  thiago_lic('Bible League International (Versão Fácil de Ler)'))
T('sr-dk', 'sr_dk', 'sr', {'en': 'Daničić-Karadžić (Serbian, Cyrillic)', 'sr': 'Свето писмо, Даничић–Караџић'}, PD)
T('sv-folkbibeln2015', 'sv_sfb15', 'sv', {'en': 'Svenska Folkbibeln 2015 (Swedish)', 'sv': 'Svenska Folkbibeln 2015'},
  thiago_lic('2015 Stiftelsen Svenska Folkbibeln'))
T('sw-sruv', 'sw_sruv', 'sw', {'en': 'Swahili Revised Union Version', 'sw': 'Biblia, Swahili Revised Union Version'},
  thiago_lic('Bible Society of Kenya / Bible Society of Tanzania (Swahili Revised Union Version)'))
T('ta-irv', 'ta_irvtam', 'ta', {'en': 'Indian Revised Version (Tamil)'}, IRV)
T('te-irv', 'te_irvtel', 'te', {'en': 'Indian Revised Version 2019 (Telugu)'}, IRV)
T('tr-ytc', 'tr_ytc', 'tr', {'en': 'Yorumsuz Türkçe Çeviri (Turkish)', 'tr': 'Yorumsuz Türkçe Çeviri'},
  thiago_lic('the Yorumsuz Türkçe Çeviri rights holders'))
T('ur-irv', 'ur_irvurd', 'ur', {'en': 'Indian Revised Version 2019 (Urdu, Devanagari script)'}, IRV, script='Deva', font='devanagari',
  notes='The source publishes this Urdu edition in Devanagari script.')
T('zh-cnv', 'zh_cnvs', 'zh', {'en': '新譯本 Chinese New Version (Simplified)', 'zh': '新译本'},
  thiago_lic('Worldwide Bible Society (Chinese New Version)'), script='Hans')

# ================================================================== 4. open-bibles

O('bbe', 'eng-bbe.usfx.xml', 'en', 'Bible in Basic English (1949/1964)', PD, 'usfx', repair=True)
O('bsb', 'eng-bsb.usfx.xml', 'en', 'Berean Standard Bible', 'Public domain (Berean Bible texts released to the public domain)', 'usfx')
O('oeb', 'eng-us-oeb.osis.xml', 'en', 'Open English Bible (US edition, partial)', 'Public domain (CC0)', 'osis',
  notes='The Open English Bible is a work in progress; only the books completed by the translators are present.')
O('sq-albanian', 'sqi-albanian.osis.xml', 'sq', {'en': 'Albanian Bible', 'sq': 'Bibla'}, 'Public domain (per open-bibles)', 'osis')
O('bg-veren', 'bul-bulgarian.osis.xml', 'bg', {'en': 'Bulgarian Bible (Veren revision of the 1871 text)', 'bg': 'Библия, ревизия Верен'},
  'Public domain (per open-bibles; the file header credits the revision to Veren LTD)', 'osis')
O('zh-cuv', 'chi-cuv.usfx.xml', 'zh', {'en': '和合本 Chinese Union Version (Traditional)', 'zh': '和合本（繁體）'}, PD, 'usfx', script='Hant')
O('zh-cuv-simp', 'chi-cuv-simp.usfx.xml', 'zh', {'en': '和合本 Chinese Union Version (Simplified)', 'zh': '和合本（简体）'}, PD, 'usfx', script='Hans')
O('chr-nt', 'chr-cherokee.usfx.xml', 'chr', {'en': 'Cherokee New Testament'}, PD, 'usfx', canon='nt-27')
O('cs-kralicka', 'cze-bkr.zefania.xml', 'cs', {'en': 'Bible kralická 1613 (Czech)', 'cs': 'Bible kralická'}, PD, 'zefania')
O('hu-karoli', 'hun-karoli.osis.xml', 'hu', {'en': 'Károli Bible 1908 (Hungarian)', 'hu': 'Károli-biblia'}, PD, 'osis')
O('it-riveduta', 'ita-riveduta.osis.xml', 'it', {'en': 'Riveduta 1927 (Italian)', 'it': 'La Sacra Bibbia, Versione Riveduta'},
  'Public domain per open-bibles; the file header carries a 1990 notice of the Società Biblica Britannica e Forestiera', 'osis')
O('ja-kougo', 'jpn-kougo.osis.xml', 'ja', {'en': '口語訳 Japanese Colloquial Bible (1954/1955)', 'ja': '口語訳聖書'}, PD, 'osis')
O('mi-maori', 'mri-maori.osis.xml', 'mi', {'en': 'Maori Bible', 'mi': 'Te Paipera Tapu'}, PD, 'osis')
O('pt-almeida', 'por-almeida.usfx.xml', 'pt', {'en': 'João Ferreira de Almeida (Portuguese, open-bibles edition)', 'pt': 'Almeida'}, PD, 'usfx')
O('ro-cornilescu', 'ron-rccv.usfx.xml', 'ro', {'en': 'Cornilescu, corrected edition (Romanian)', 'ro': 'Biblia Cornilescu'}, 'Public domain (per open-bibles)', 'usfx')
O('es-bes', 'spa-bes.usfx.xml', 'es', {'en': 'La Biblia en Español Sencillo (Spanish)', 'es': 'La Biblia en Español Sencillo'},
  'CC BY 4.0 (© 2018 AudioBiblia.org / Irma Flores)', 'usfx')
O('es-pdt', 'spa-pddpt.usfx.xml', 'es', {'en': 'Palabra de Dios para ti (Spanish)', 'es': 'Palabra de Dios para ti'},
  'CC BY-SA 4.0 (© 2017–2022 Asociación Bíblica Latinoamericana)', 'usfx')
O('es-vbl', 'spa-vbl.usfx.xml', 'es', {'en': 'Versión Biblia Libre (Spanish)', 'es': 'Versión Biblia Libre'},
  'CC BY-SA 4.0 (© 2018–2020 Jonathan Gallagher y Shelly Barrios de Avila)', 'usfx')
O('tl-ang-biblia', 'tgl-tagalog.osis.xml', 'tl', {'en': 'Ang Biblia 1905 (Tagalog)', 'tl': 'Ang Dating Biblia'}, PD, 'osis')
O('th-kjv', 'tha-thai.osis.xml', 'th', {'en': 'Thai King James Version', 'th': 'พระคัมภีร์ภาษาไทยฉบับ KJV'}, 'Public domain (per open-bibles)', 'osis')
O('vi-cadman', 'vie-cadman.osis.xml', 'vi', {'en': 'Kinh Thánh Tiếng Việt 1934 (Vietnamese)', 'vi': 'Kinh Thánh Tiếng Việt 1934'}, PD, 'osis')

# ================================================================== 5. scrollmapper/bible_databases

S('acv', 'ACV', 'en', 'A Conservative Version', 'Public domain (per scrollmapper)')
S('akjv', 'AKJV', 'en', 'American King James Version', PD)
S('my-judson', 'BurJudson', 'my', {'en': 'Judson Bible 1835 (Burmese)'}, PD)
S('grc-byz', 'Byz', 'grc', {'en': 'Byzantine Textform 2013 (Greek New Testament)', 'el': 'Η Καινή Διαθήκη, Βυζαντινό κείμενο'},
  'Public domain (Robinson–Pierpont)', role='original', canon='nt-27')
S('cpdv', 'CPDV', 'en', 'Catholic Public Domain Version', PD, canon='catholic-73', families=['catholic'],
  book_filter=C.CANONS['catholic-73'], vulgate_psalms='title',
  notes='Psalms are shown under the Hebrew (KJV) psalm numbers; the edition follows the Vulgate numbering and counts the '
        'superscription as verse 1. Esther has sixteen chapters and Daniel fourteen, as in the Vulgate.')
S('cu-elizabeth', 'CSlElizabeth', 'cu', {'en': 'Elizabeth Bible 1757 (Church Slavonic)', 'cu': 'Елисаветинская Библия'}, PD,
  canon='orthodox-synodal-79', families=['eastern-orthodox'], vulgate_psalms='title',
  notes='Psalms are shown under the Hebrew (KJV) psalm numbers; the edition follows the Septuagint numbering and counts the '
        'superscription as verse 1. Daniel has fourteen chapters.')
S('zh-sigao', 'ChiSB', 'zh', {'en': '思高本 Studium Biblicum Version (Chinese, Traditional)', 'zh': '思高聖經'},
  cleared('Studium Biblicum Franciscanum, Hong Kong (思高聖經)'), kind='scrollmapper-chisb', script='Hant',
  canon='catholic-73', families=['catholic'], notes='Daniel has fourteen chapters; Joel four and Malachi three.')
S('lzh-cuv', 'ChiUnL', 'lzh', {'en': '文理和合 Chinese Union Version, Wenli (Classical Chinese)', 'zh': '文理和合譯本'}, PD)
S('hr-saric', 'CroSaric', 'hr', {'en': 'Šarić Bible (Croatian)', 'hr': 'Biblija, prijevod Ivana Šarića'},
  cleared('Hrvatsko biblijsko društvo / Verbum (Šarić revision)'), fix='croatian_fix', families=['catholic'], canon='catholic-73',
  notes='Daniel has fourteen chapters; Joel four and Malachi three.')
S('cs-csp', 'CzeCSP', 'cs', {'en': 'Český studijní překlad (Czech)', 'cs': 'Český studijní překlad'},
  cleared('2009 Nadační fond překladu Bible / KMS'), notes='Joel has four chapters and Malachi three.')
S('da-1871', 'DaOT1871NT1907', 'da', {'en': 'Danish Bible, OT 1871 / NT 1907', 'da': 'Bibelen, GT 1871 / NT 1907'}, PD)
S('darby', 'Darby', 'en', 'Darby Translation (1890)', PD, fix='supplied')
S('nl-statenvertaling', 'DutSVVA', 'nl', {'en': 'Statenvertaling 1637 with Apocrypha (Dutch)', 'nl': 'Statenvertaling'}, PD,
  fix='bracket_number_markers')
S('fi-biblia1776', 'FinBiblia', 'fi', {'en': 'Biblia 1776 (Finnish)', 'fi': 'Biblia 1776'}, PD, fix='bracket_number_markers')
S('fi-stlk2017', 'FinSTLK2017', 'fi', {'en': 'Pyhä Raamattu, STLK 2017 (Finnish)', 'fi': 'Pyhä Raamattu (STLK 2017)'},
  cleared('2017 Suomen Tunnustuksellinen Luterilainen Kirkko'), notes='Joel has four chapters and Malachi three.')
S('fr-bbb', 'FreBBB', 'fr', {'en': 'Bible Bovet Bonnet 1900 (French)', 'fr': 'Bible Bovet Bonnet'}, PD, fix='supplied')
S('fr-martin1744', 'FreBDM1744', 'fr', {'en': 'Bible David Martin 1744 (French)', 'fr': 'Bible David Martin 1744'}, PD)
S('fr-darby', 'FreJND', 'fr', {'en': 'Bible J.N. Darby (French)', 'fr': 'Bible Darby'}, PD, fix='supplied',
  notes='Joel has four chapters and Malachi three.')
S('fr-pgr', 'FrePGR', 'fr', {'en': 'Bible Perret-Gentil et Rilliet (French)', 'fr': 'Bible Perret-Gentil et Rilliet'}, PD, fix='pgr_fix')
S('fr-synodale1921', 'FreSynodale1921', 'fr', {'en': 'Version Synodale 1921 (French, New Testament and Psalms)', 'fr': 'Version Synodale 1921'}, PD)
S('fr-oltramare1874', 'FreOltramare1874', 'fr', {'en': 'Oltramare 1874 (French New Testament)', 'fr': 'Nouveau Testament Oltramare 1874'}, PD, canon='nt-27')
S('fr-stapfer1889', 'FreStapfer1889', 'fr', {'en': 'Stapfer 1889 (French New Testament)', 'fr': 'Nouveau Testament Stapfer 1889'}, PD, canon='nt-27')
S('fr-lxx-giguet', 'FreLXXGiguet', 'fr', {'en': 'Giguet Septuagint 1872 (French Old Testament)', 'fr': 'La Septante, traduction Giguet'}, PD,
  vulgate_psalms='notitle', families=['eastern-orthodox'],
  notes='Psalms are shown under the Hebrew (KJV) psalm numbers; the edition follows the Septuagint numbering. Psalms of Solomon, '
        'Odes and 1 Enoch in the source are not carried.')
S('de-elberfelder1871', 'GerElb1871', 'de', {'en': 'Elberfelder Bibel 1871 (German)', 'de': 'Elberfelder Bibel 1871'}, PD)
S('de-elberfelder1905', 'GerElb1905', 'de', {'en': 'Elberfelder Bibel 1905 (German)', 'de': 'Unrevidierte Elberfelder 1905'}, PD)
S('de-menge', 'GerMenge', 'de', {'en': 'Menge-Bibel 1939 (German)', 'de': 'Menge-Bibel'}, 'Public domain (Hermann Menge, d. 1939)',
  kind='scrollmapper-menge', notes='Joel has four chapters and Malachi three. The additions to Daniel are shown as Susanna, '
  'Bel and the Dragon and the Prayer of Azariah; the additions to Esther as Esther (Greek).')
S('de-schlachter1951', 'GerSch', 'de', {'en': 'Schlachter 1951 (German)', 'de': 'Schlachter-Bibel 1951'},
  "© 1951 Genfer Bibelgesellschaft (the 1951 revision is not public domain); included under the project's cleared-permission assumption",
  notes='Joel has four chapters and Malachi three.')
S('de-textbibel', 'GerTextbibel', 'de', {'en': 'Textbibel 1906 (German)', 'de': 'Textbibel 1906'}, PD,
  notes='Joel has four chapters and Malachi three.')
S('de-luther1545', 'GerBoLut', 'de', {'en': 'Lutherbibel 1545, modern spelling (German)', 'de': 'Lutherbibel 1545 (moderne Rechtschreibung)'}, PD,
  families=['lutheran'], notes='Joel has four chapters and Malachi three.')
S('de-zuercher1931', 'GerZurcher', 'de', {'en': 'Zürcher Bibel 1931 (German)', 'de': 'Zürcher Bibel 1931'}, 'Public domain (per scrollmapper)')
S('de-gruenewald', 'GerGruenewald', 'de', {'en': 'Grünewaldbibel 1924 (German)', 'de': 'Grünewaldbibel 1924'}, PD, families=['catholic'])
S('de-albrecht', 'GerAlbrecht', 'de', {'en': 'Albrecht, New Testament and Psalms (German)', 'de': 'Albrecht Neues Testament und Psalmen'}, PD)
S('el-vamvas', 'GreVamvas', 'el', {'en': 'Vamvas 1850 (Modern Greek)', 'el': 'Μετάφραση Νεόφυτου Βάμβα'}, PD)
S('ht-haitian', 'Haitian', 'ht', {'en': 'Haitian Creole Bible', 'ht': 'Bib la'}, 'Public domain (per scrollmapper)')
S('he-modern', 'HebModern', 'he', {'en': 'Modern Hebrew Bible', 'he': 'תנ"ך וברית חדשה בעברית מודרנית'}, 'Public domain (per scrollmapper)', fix='hebmodern_fix')
S('jps1917', 'JPS', 'en', 'Jewish Publication Society Tanakh (1917)', PD, canon='hebrew-ot-39', families=[],
  notes='Old Testament only, in the order of the Hebrew Bible. Joel has four chapters and Malachi three, following the Hebrew division.')
S('ja-bungo', 'JapBungo', 'ja', {'en': '文語訳 Japanese Classical Bible (Meiji/Taisho)', 'ja': '文語訳聖書（明治元訳・大正改訳）'}, PD, fix='japbungo_fix')
S('jubilee2000', 'Jubilee2000', 'en', 'Jubilee Bible 2000', cleared('2000 Russell M. Stendal (Jubilee Bible)'), fix='supplied')
S('ko-hkjv', 'KorHKJV', 'ko', {'en': 'Hangul King James Version (Korean)', 'ko': '한글 킹제임스 성경'},
  cleared('Word of God Preservation Society (Hangul King James Version)'))
S('ko-krv', 'KorRV', 'ko', {'en': '개역성경 Korean Revised Version', 'ko': '개역성경'},
  cleared('Korean Bible Society (개역성경 1961)'))
S('litv', 'LITV', 'en', "Green's Literal Translation", cleared('Jay P. Green Sr. (Literal Translation of the Holy Bible)'))
S('lv-gluck', 'LvGluck8', 'lv', {'en': 'Glück Bible, 8th edition (Latvian)', 'lv': 'Glika Bībele'}, PD)
S('mkjv', 'MKJV', 'en', "Green's Modern King James Version", cleared('Jay P. Green Sr. (Modern King James Version)'), fix='brace_note')
S('ml-1910', 'Mal1910', 'ml', {'en': 'Sathyavedapusthakam 1910 (Malayalam)'}, PD)
S('hbo-mapm', 'MapM', 'hbo', {'en': 'מקרא על פי המסורה Miqra according to the Masorah (Hebrew)', 'he': 'מקרא על פי המסורה'},
  'CC BY-SA (Miqra according to the Masorah project)', role='original', canon='hebrew-ot-39', fix='strip_markers',
  notes='Hebrew Bible in Tanakh order. Joel has four chapters and Malachi three.')
S('mg-1865', 'Mg1865', 'mg', {'en': 'Baiboly Malagasy 1865 (Malagasy)', 'mg': 'Baiboly Malagasy 1865'}, PD,
  notes='Joel has four chapters and Malachi three.')
S('nheb', 'NHEB', 'en', 'New Heart English Bible', PD)
S('nl-canisius1939', 'NlCanisius1939', 'nl', {'en': 'Petrus Canisius Vertaling 1939 (Dutch)', 'nl': 'Petrus Canisiusvertaling'},
  cleared('Katholieke Bijbelstichting (Petrus Canisius vertaling 1939)'), canon='catholic-73', families=['catholic'],
  book_filter=C.CANONS['catholic-73'], vulgate_psalms='title',
  notes='Psalms are shown under the Hebrew (KJV) psalm numbers; the edition follows the Vulgate numbering and counts the '
        'superscription as verse 1. Esther has sixteen chapters and Daniel fourteen.')
S('nn-smb1921', 'NorSMB', 'nn', {'en': 'Studentmållagsbibelen 1921 (Norwegian Nynorsk)', 'nn': 'Studentmållagsbibelen'}, PD,
  fix='bracket_number_markers')
S('nb-1930', 'Norsk', 'nb', {'en': 'Bibelen 1930 (Norwegian Bokmål)', 'nb': 'Bibelen 1930'}, PD)
S('noyes', 'Noyes', 'en', 'Noyes Translation (1869; New Testament, Job to Isaiah)', PD)
S('syc-peshitta', 'Peshitta', 'syc', {'en': 'Peshitta (Syriac New Testament)'}, PD, role='original', canon='nt-27')
S('pt-blivre', 'PorBLivre', 'pt', {'en': 'Bíblia Livre (Portuguese)', 'pt': 'Bíblia Livre'}, 'Public domain / free licence (Bíblia Livre project)')
S('pt-nva', 'PorNVA', 'pt', {'en': 'Nova Versão de Acesso Livre (Portuguese)', 'pt': 'Bíblia Nova Versão de Acesso Livre'}, 'Free licence (Nova Versão de Acesso Livre project)')
S('rwebster', 'RWebster', 'en', 'Revised Webster Version (1833/1995)', PD)
S('rotherham', 'Rotherham', 'en', "Rotherham's Emphasised Bible (1902)", PD, fix='rotherham_fix')
S('ru-synodal', 'RusSynodal', 'ru', {'en': 'Синодальный перевод Russian Synodal Translation', 'ru': 'Синодальный перевод'}, PD,
  kind='scrollmapper-rus', canon='orthodox-synodal-79', families=['eastern-orthodox'], vulgate_psalms='title',
  notes='Psalms are shown under the Hebrew (KJV) psalm numbers; the edition follows the Septuagint numbering and counts the '
        'superscription as verse 1. Daniel has fourteen chapters. Bracketed words mark Septuagint readings, as in the printed edition.')
S('ru-makarij', 'RusMakarij', 'ru', {'en': 'Makarij Pentateuch (Russian)', 'ru': 'Пятикнижие Моисеево в переводе Макария'}, PD, canon='pentateuch-5')
S('hbo-samaritan', 'SP', 'hbo', {'en': 'Samaritan Pentateuch (Hebrew)', 'he': 'התורה השומרונית'}, 'Public domain (per scrollmapper)', role='original', canon='pentateuch-5')
S('sl-kjv', 'SloKJV', 'sl', {'en': 'Slovenian translation of the King James Version', 'sl': 'Sveto pismo, prevod KJV'}, 'Public domain (per scrollmapper)')
S('sl-stritar', 'SloStritar', 'sl', {'en': 'Stritar 1882, New Testament and Psalms (Slovenian)', 'sl': 'Novi testament in Psalmi, Josip Stritar'}, PD)
S('es-platense', 'SpaPlatense', 'es', {'en': 'Biblia Platense, Straubinger (Spanish)', 'es': 'Biblia Platense (Straubinger)'},
  cleared('Fundación Straubinger (Biblia Platense)'), canon='catholic-73', families=['catholic'], book_filter=C.CANONS['catholic-73'],
  vulgate_psalms='title', fix='strip_markers',
  notes='Psalms are shown under the Hebrew (KJV) psalm numbers; the edition follows the Vulgate numbering and counts the '
        'superscription as verse 1. Esther has sixteen chapters and Daniel fourteen.')
S('es-rv1865', 'SpaRV1865', 'es', {'en': 'Reina-Valera 1865 (Spanish)', 'es': 'Reina-Valera 1865'}, PD)
S('sv-1917', 'Swe1917', 'sv', {'en': 'Swedish Bible 1917 with Apocrypha', 'sv': '1917 års kyrkobibel'}, PD, fix='swe1917_notes')
S('sv-karlxii', 'SweKarlXII1873', 'sv', {'en': 'Karl XII Bible, 1873 edition (Swedish)', 'sv': 'Karl XII:s Bibel (1873)'}, PD)
S('grc-tr', 'TR', 'grc', {'en': 'Textus Receptus 1550/1894 (Greek New Testament)', 'el': 'Textus Receptus'}, PD, role='original', canon='nt-27', fix='tr_strongs')
S('twenty', 'Twenty', 'en', 'Twentieth Century New Testament (1904)', PD, canon='nt-27')
S('tyndale', 'Tyndale', 'en', 'Tyndale Bible (1525/1530, partial)', PD,
  notes='The source carries Genesis, the four Gospels, Acts, Romans, 1 Corinthians, Hebrews and Revelation only.')
S('uk-ogienko', 'UkrOgienko', 'uk', {'en': 'Ohienko Bible 1962 (Ukrainian)', 'uk': 'Біблія, переклад Івана Огієнка'},
  'Public domain (per scrollmapper)', vulgate_psalms='title',
  notes='Psalms are shown under the Hebrew (KJV) psalm numbers; the edition follows the Septuagint numbering and counts the superscription as verse 1.')
S('hbo-wlc', 'WLC', 'hbo', {'en': 'Westminster Leningrad Codex (Hebrew)', 'he': 'תנ"ך, נוסח לנינגרד'}, PD, role='original',
  canon='hebrew-ot-39', notes='Hebrew Bible in Tanakh order. Joel has four chapters and Malachi three.')
S('webster', 'Webster', 'en', 'Webster Bible (1833)', PD, fix='supplied')
S('wycliffe', 'Wycliffe', 'enm', 'Wycliffe Bible (c. 1395, Middle English)', PD, canon='vulgate-appendix-76', families=['catholic'],
  book_filter=EXTRA_CANONS['vulgate-appendix-76'], vulgate_psalms='title',
  notes='Psalms are shown under the Hebrew (KJV) psalm numbers; the edition follows the Vulgate numbering and counts the '
        'superscription as verse 1. Esther has sixteen chapters and Daniel fourteen; the Prayer of Manasseh and 3–4 Esdras follow the New Testament.')
S('ceb-pinadayag', 'CebPinadayag', 'ceb', {'en': 'Cebuano Pinadayag'}, 'Public domain (per scrollmapper)')
S('pl-gdanska', 'PolGdanska', 'pl', {'en': 'Biblia Gdańska 1881 (Polish)', 'pl': 'Biblia Gdańska'}, PD)
S('pl-ugdanska', 'PolUGdanska', 'pl', {'en': 'Uwspółcześniona Biblia Gdańska (Polish)', 'pl': 'Uwspółcześniona Biblia Gdańska'},
  'Free use (© Fundacja Wrota Nadziei; distributed without restriction)')
S('sr-dk-ijekavian', 'SrKDIjekav', 'sr', {'en': 'Daničić-Karadžić, Ijekavian (Serbian, Cyrillic)', 'sr': 'Свето писмо, Даничић–Караџић (ијекавски)'}, PD)
S('haweis', 'Haweis', 'en', 'Haweis New Testament (1795)', PD, canon='nt-27')
S('anderson', 'Anderson', 'en', 'Anderson New Testament (1864)', PD, canon='nt-27')

IDS = [e['id'] for e in EDITIONS]
assert len(IDS) == len(set(IDS)), 'duplicate edition id'
